"""Benchmark pe DOCUMENTE (imagini): Paznic (OCR real) → Funcționar → Verificator → scor, pe dosare sintetice.

Completează scripts/benchmark.py (care testează regulile pe date deja structurate): aici trec prin tot
lanțul pozele de buletin, fluturaș și extras, ca la un upload real.

CE MĂSOARĂ ȘI CE NU (de spus la fel și în pitch):
  - Scurgeri: orice valoare personală (nume, CNP, IBAN, serie/nr. buletin, MRZ, stradă) găsită în ce
    pleacă din seif (textul redactat = ce vede LLM-ul, câmpurile extrase, mesajele finding-urilor).
  - Extragere: câmpurile citite de Funcționar comparate cu adevărul de la generare.
  - Detecție: falsurile din dosar prinse; dosarele cinstite lovite (orice recomandare ≠ „clear”).
  - Documentele au layout-ul generatorului nostru (același ca la Maria) și sunt curate sau ușor degradate
    (--noisy). NU sunt documente reale de la bănci: cifrele arată că lanțul e implementat corect, nu că
    prindem orice fals real. Falsul „perfect” (taxe refăcute corect) e raportat separat, ca limită.
  - Detector și Detectiv nu intră în scor aici (Detectorul e încă varianta de probă).

Toate datele sunt INVENTATE: CNP cu număr de ordine 000 (nu se atribuie), IBAN cu sucursala 9999,
firmele din Arena (CUI-uri verificate ca inexistente la ANAF).

Rulare (din rădăcina repo-ului):
  backend/.venv/Scripts/python scripts/benchmark_pipeline.py [--n 20] [--seed 2026] [--noisy] [--llm cloud]
Ieșire: tabel în consolă + data/benchmark/pipeline_results.json
"""
import argparse
import asyncio
import io
import json
import os
import random
import re
import sys
import tempfile
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

_TMP = Path(tempfile.mkdtemp(prefix="orb_bench_"))
os.environ.update({
    "ENV": "test", "BANK_UI_TOKEN": "bench", "HMAC_SECRET": "bench-hmac", "ARENA_HMAC_SECRET": "bench-arena",
    "VAULT_DATABASE_URL": f"sqlite:///{(_TMP / 'vault.db').as_posix()}",
    "DATABASE_URL": f"sqlite:///{(_TMP / 'orb.db').as_posix()}",
})
os.environ.setdefault("LLM_MODE", "mock")
if "VAULT_KEY" not in os.environ:
    from cryptography.fernet import Fernet

    os.environ["VAULT_KEY"] = Fernet.generate_key().decode()

from data.generator.build_demo import font, jpeg, lei  # noqa: E402
from data.generator.ro_ids import cnp, iban, mrz_td2  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

from app.agents.compliance.scoring import score  # noqa: E402
from app.agents.functionar.agent import Functionar  # noqa: E402
from app.agents.paznic.agent import Paznic  # noqa: E402
from app.agents.paznic.ocr import ocr_available  # noqa: E402
from app.agents.verificator.agent import Verificator  # noqa: E402
from app.agents.verificator.tax import compute_payslip  # noqa: E402
from app.arena.missions import COMPANIES  # noqa: E402
from app.core.pipeline import PipelineContext  # noqa: E402
from app.models import Case, Document  # noqa: E402

OUT = ROOT / "data" / "benchmark" / "pipeline_results.json"
TODAY = date(2026, 10, 28)

SURNAMES = ["POPESCU", "IONESCU", "POPA", "DUMITRU", "STAN", "STOICA", "GHEORGHE", "MATEI", "CONSTANTIN",
            "MARIN", "TUDOR", "DOBRE", "BARBU", "NISTOR", "FLOREA", "ENACHE", "LUPU", "CRISTEA"]
GIVEN = {"F": ["ELENA", "IOANA", "ANDREEA", "CRISTINA", "MIHAELA", "DIANA", "LAURA", "ALINA", "OANA"],
         "M": ["ANDREI", "MIHAI", "ALEXANDRU", "BOGDAN", "STEFAN", "RADU", "COSMIN", "VLAD", "DANIEL"]}
# județ → (seria buletinului, oraș, prefixul de seif pentru CNP); toate în tabela Verificatorului
COUNTIES = {"PH": ("PH", "Ploiești", "Prahova"), "CJ": ("CJ", "Cluj-Napoca", "Cluj"),
            "IS": ("IS", "Iași", "Iași"), "TM": ("TM", "Timișoara", "Timiș"), "BV": ("BV", "Brașov", "Brașov")}
STREETS = ["Florilor", "Libertății", "Mihai Viteazu", "Republicii", "Teilor", "Zorilor", "Victoriei", "Morii"]
EXPENSES = ["Cumpărături card", "Factură utilități", "Chirie", "Abonament telefon", "Retragere ATM"]
ROLES = {"Tehnoserv Construct SRL": "Operator date", "Bitwave Software SRL": "Programator",
         "Nordic Consulting Grup SRL": "Consultant", "Agro Prahova Distribuție SRL": "Contabil"}
ACTIVE = [n for n, c in COMPANIES.items() if c["active"] and c["founded"] < date(2026, 1, 1)]
INACTIVE = [n for n, c in COMPANIES.items() if not c["active"]]

KINDS = ["honest", "forged_net", "forged_balance", "inactive_employer", "perfect_fake"]
EXPECTED = {  # ce trebuie să găsească Verificatorul pentru fiecare tip de fals
    "forged_net": "NET_MISMATCH", "forged_balance": "BALANCE_MISMATCH", "inactive_employer": "COMPANY_INACTIVE",
}


# ── generare ──────────────────────────────────────────────────────────────────

def person(rng: random.Random, i: int) -> dict:
    sex = rng.choice("FM")
    county = rng.choice(list(COUNTIES))
    series, city, county_name = COUNTIES[county]
    birth = date(rng.randint(1966, 2001), rng.randint(1, 12), rng.randint(1, 28))
    issued = date(rng.randint(2019, 2025), rng.randint(1, 12), rng.randint(1, 28))
    p = {"sex": sex, "surname": rng.choice(SURNAMES), "given": rng.choice(GIVEN[sex]), "county": county,
         "series": series, "number": f"{rng.randint(100000, 999999)}", "birth": birth.isoformat(),
         "issued": issued.isoformat(), "expiry": issued.replace(year=issued.year + 10).isoformat(),
         "address": f"Str. {rng.choice(STREETS)} nr. {rng.randint(1, 120)}, {city}, jud. {county_name}",
         "city": city}
    p["cnp"] = cnp(sex, p["birth"], county, seq=0)  # 000 = număr de ordine neatribuit niciodată
    p["iban"] = iban("RZBR", f"9999{i:012d}")        # sucursala 9999 nu există
    return p


def draw_id_card(p: dict) -> tuple[Image.Image, tuple[str, str]]:
    w, h = 1600, 1010
    img = Image.new("RGB", (w, h), "#e9eef2")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 120), fill="#1d4f91")
    d.text((40, 30), "ROMÂNIA  ·  ROUMANIE  ·  ROMANIA", font=font(34, True), fill="white")
    d.text((40, 140), "CARTE DE IDENTITATE / IDENTITY CARD", font=font(30, True), fill="#1d4f91")
    d.text((900, 140), f"SERIA {p['series']}  NR {p['number']}", font=font(30, True), fill="#b3261e")
    d.text((900, 190), f"CNP {p['cnp']}", font=font(30, True), fill="black")
    d.rectangle((40, 200, 400, 660), fill="#c9d3dc", outline="#7a8a99", width=3)
    iss, exp = p["issued"], p["expiry"]
    rows = [("Nume/Nom/Last name", p["surname"]), ("Prenume/Prénom/First name", p["given"]),
            ("Cetățenie/Nationalité/Nationality", "Română / ROU"), ("Sex/Sexe/Sex", p["sex"]),
            ("Loc naștere/Lieu de naissance/Place of birth", f"Mun. {p['city']}, Jud. {p['county']}"),
            ("Domiciliu/Adresse/Address", p["address"]),
            ("Valabilitate/Validité/Validity", f"{iss[8:]}.{iss[5:7]}.{iss[2:4]}-{exp[8:]}.{exp[5:7]}.{exp[:4]}")]
    y = 250
    for label, value in rows:
        d.text((440, y), label, font=font(20), fill="#555")
        d.text((440, y + 26), value, font=font(30, True), fill="black")
        y += 72
    l1, l2 = mrz_td2(p["surname"], p["given"], p["series"], p["number"], p["birth"], p["sex"], p["expiry"], p["cnp"])
    d.rectangle((0, 820, w, h), fill="white")
    d.text((40, 840), l1, font=font(40), fill="black")
    d.text((40, 910), l2, font=font(40), fill="black")
    return img, (l1, l2)


def draw_payslip(p: dict, employer: str, gross: int, net: float, taxes, month: str, issue: date) -> Image.Image:
    w, h = 1240, 1754
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    c = COMPANIES[employer]
    d.text((80, 80), employer, font=font(30), fill="black")
    d.text((80, 125), f"CUI {c['cui']}  ·  {p['city']}", font=font(22), fill="#333")
    d.text((80, 230), "FLUTURAȘ DE SALARIU", font=font(44, True), fill="black")
    d.text((80, 290), f"Luna: {month}   ·   Emis: {issue:%d.%m.%Y}", font=font(22), fill="#333")
    d.line((80, 340, w - 80, 340), fill="black", width=2)
    rows = [("Angajat", f"{p['surname']} {p['given']}"), ("CNP", p["cnp"]), ("Funcția", ROLES[employer]),
            ("Salariu brut", lei(gross)), ("CAS 25%", "-" + lei(taxes.cas)), ("CASS 10%", "-" + lei(taxes.cass)),
            ("Impozit 10%", "-" + lei(taxes.income_tax))]
    y = 380
    for label, value in rows:
        d.text((80, y), label, font=font(22), fill="black")
        d.text((w - 80, y), value, font=font(22), fill="black", anchor="ra")
        y += 70
    y += 30
    d.text((80, y), "NET DE PLATĂ", font=font(32, True), fill="black")
    d.text((w - 80, y), lei(net), font=font(32, True), fill="black", anchor="ra")
    return img


def draw_statement(p: dict, rows: list[tuple[str, str, float | None, float]], closing: float) -> Image.Image:
    w, h = 1240, 1754
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 140), fill="#fee600")
    d.text((80, 45), "Raiffeisen BANK", font=font(44, True), fill="black")
    d.text((80, 200), "EXTRAS DE CONT", font=font(40, True), fill="black")
    d.text((80, 260), f"Titular: {p['surname']} {p['given']}", font=font(22), fill="black")
    d.text((80, 295), f"IBAN: {p['iban']}", font=font(22), fill="black")
    d.text((80, 330), "Perioada: 01.09.2026 – 30.09.2026", font=font(22), fill="black")
    y = 420
    d.text((80, y), "Data      Descriere                                Sumă            Sold", font=font(22, True),
           fill="black")
    y += 50
    for day, desc, amount, bal in rows:
        d.text((80, y), day, font=font(22), fill="black")
        d.text((230, y), desc, font=font(22), fill="black")
        if amount is not None:
            d.text((850, y), lei(amount), font=font(22), fill="black", anchor="ra")
        d.text((w - 80, y), lei(bal), font=font(22), fill="black", anchor="ra")
        y += 45
    y += 30
    d.text((80, y), "Sold final", font=font(26, True), fill="black")
    d.text((w - 80, y), lei(closing), font=font(26, True), fill="black", anchor="ra")
    return img


def degrade(img: Image.Image, rng: random.Random) -> Image.Image:
    """Ușor: ca o scanare proastă (nu o poză de telefon — asta e P2 la Lorena)."""
    img = img.rotate(rng.uniform(-0.8, 0.8), expand=False, fillcolor="white", resample=Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(rng.uniform(0.3, 0.8)))
    return jpeg(img, rng.randint(55, 75))


def to_bytes(img: Image.Image, kind: str) -> bytes:
    buf = io.BytesIO()
    if kind == "pdf":
        img.save(buf, "PDF", resolution=150)
    else:
        img.save(buf, "JPEG", quality=88)
    return buf.getvalue()


def make_case(rng: random.Random, i: int, kind: str, noisy: bool) -> dict:
    p = person(rng, i)
    employer = rng.choice(INACTIVE if kind == "inactive_employer" else ACTIVE)
    gross = rng.choice([rng.randint(4400, 6500), rng.randint(6500, 16000)])
    dependents = rng.randint(0, 4)
    taxes = compute_payslip(gross, dependents, None, "2026-09")
    net = taxes.net
    if kind == "forged_net":
        net = round(net * rng.uniform(1.06, 1.3))
    if kind == "perfect_fake":  # brut umflat, taxele refăcute corect; salariul real intră în cont
        real_net = net
        gross = round(gross * rng.uniform(1.4, 1.9))
        taxes = compute_payslip(gross, dependents, None, "2026-09")
        net = taxes.net
    issue = date(2026, 9, 30)

    opening = round(rng.uniform(150, 6000), 2)
    credit = real_net if kind == "perfect_fake" else net
    tx = [("01.09", "Sold inițial", None), ("05.09", "Încasare salariu", float(credit))]
    for day in sorted(rng.sample(range(6, 29), 3)):
        tx.append((f"{day:02d}.09", rng.choice(EXPENSES), -round(rng.uniform(40, 900), 2)))
    rows, bal = [], opening
    for day, desc, amount in tx:
        bal = opening if amount is None else round(bal + amount, 2)
        rows.append((day, desc, amount, bal))
    closing = bal if kind != "forged_balance" else round(bal + rng.uniform(4000, 30000), 2)

    card, mrz = draw_id_card(p)
    slip = draw_payslip(p, employer, gross, net, taxes, "septembrie 2026", issue)
    stmt = draw_statement(p, rows, closing)
    if noisy:
        card, slip, stmt = (degrade(x, rng) for x in (card, slip, stmt))
    return {
        "id": f"bench_{i:03d}", "kind": kind, "person": p, "mrz": mrz,
        "files": {"buletin.jpg": to_bytes(card, "jpg"), "fluturas.jpg": to_bytes(slip, "jpg"),
                  "extras.pdf": to_bytes(stmt, "pdf")},
        "truth": {"gross_salary": gross, "net_salary": net, "period": "2026-09", "issue_date": issue.isoformat(),
                  "opening_balance": opening, "closing_balance": closing, "rows": len(rows),
                  "expiry_date": p["expiry"], "sex": p["sex"], "employer": employer},
    }


# ── măsurare ──────────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    text = "".join(c for c in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9<]", " ", text.upper())


def pii_needles(c: dict) -> dict[str, str]:
    p = c["person"]
    street = p["address"].split(" nr.")[0].removeprefix("Str. ")
    return {"CNP": p["cnp"], "IBAN": p["iban"], "IBAN_CONT": p["iban"][8:], "NUME": p["surname"],
            "PRENUME": p["given"], "SERIE_NR": f"{p['series']}{p['number']}", "NR_BULETIN": p["number"],
            "STRADA": street, "MRZ_1": c["mrz"][0][5:20], "MRZ_2": c["mrz"][1][13:28]}


def find_leaks(c: dict, case: Case, results) -> list[str]:
    """Valorile personale care ies din seif: text redactat (→ LLM), câmpuri extrase, mesaje (→ API, UI)."""
    out = [d.redacted_text or "" for d in case.documents]
    out += [str(v.value) + " " + str(v.source_text) for d in case.documents for v in (d.extracted or {}).values()]
    out += [f.message for r in results for f in r.findings]
    hay = " " + _norm(" ".join(out)) + " "
    hay_compact = hay.replace(" ", "")
    leaks = []
    for kind, value in pii_needles(c).items():
        v = _norm(value).strip()
        if kind in ("NUME", "PRENUME", "STRADA"):
            hit = all(f" {tok} " in hay for tok in v.split())
        else:
            hit = v.replace(" ", "") in hay_compact
        if hit:
            leaks.append(kind)
    return leaks


def field_checks(c: dict, case: Case, scratch: dict) -> dict[str, bool]:
    t = c["truth"]
    by_type = {d.type: d for d in case.documents}

    def val(doc_type, name):
        doc = by_type.get(doc_type)
        ev = (doc.extracted or {}).get(name) if doc else None
        return ev.value if ev else None

    stmt = by_type.get("bank_statement")
    rows = ((scratch.get("functionar", {}).get(stmt.id) or {}).get("statement") or {}).get("rows", []) if stmt else []
    return {
        "tip documente": sorted(by_type) == ["bank_statement", "id_card", "payslip"],
        "brut": val("payslip", "gross_salary") == t["gross_salary"],
        "net": val("payslip", "net_salary") == t["net_salary"],
        "luna": val("payslip", "period") == t["period"],
        "data emiterii": val("payslip", "issue_date") == t["issue_date"],
        "sold inițial": val("bank_statement", "opening_balance") == t["opening_balance"],
        "sold final": val("bank_statement", "closing_balance") == t["closing_balance"],
        "rânduri extras": len(rows) == t["rows"],
        "expirare buletin": val("id_card", "expiry_date") == t["expiry_date"],
        "sex": val("id_card", "sex") == t["sex"],
    }


async def run_case(c: dict) -> dict:
    docs = [Document(id=f"doc_{i}", filename=name) for i, name in enumerate(c["files"], start=1)]
    case = Case(id=c["id"], created_at="2026-10-28T10:00:00Z", documents=docs)
    files = {d.id: c["files"][d.filename] for d in docs}
    scratch: dict = {}

    def ctx(name):
        return PipelineContext(case=case, files=files, scratch=scratch, _agent=name)

    t0 = time.perf_counter()
    results = []
    for agent in (Paznic(), Functionar(), Verificator(today=TODAY)):
        try:
            results.append(await agent.run(case, ctx(agent.name)))
        except Exception as exc:  # un agent picat = rezultat de raportat, nu oprim benchmark-ul
            results.append(None)
            print(f"   {c['id']}: {agent.name} a picat: {type(exc).__name__}")
    ok = [r for r in results if r is not None]
    verdict, _ = score(ok)
    ver = results[2]
    codes = {f.code for f in ver.findings} if ver else set()
    return {
        "id": c["id"], "kind": c["kind"], "ms": int((time.perf_counter() - t0) * 1000),
        "agents_ok": len(ok) == 3, "leaks": find_leaks(c, case, ok), "fields": field_checks(c, case, scratch),
        "codes": sorted(codes), "recommendation": verdict.recommendation, "risk": verdict.risk,
        "expected_caught": EXPECTED.get(c["kind"]) in codes if c["kind"] in EXPECTED else None,
    }


async def main_async(args) -> dict:
    rng = random.Random(args.seed)
    kinds = [KINDS[i % len(KINDS)] for i in range(args.n)]
    print(f"Generez {args.n} dosare ({'degradate' if args.noisy else 'curate'}), LLM_MODE={os.environ['LLM_MODE']} …")
    cases = [make_case(rng, i, k, args.noisy) for i, k in enumerate(kinds)]
    sem = asyncio.Semaphore(args.jobs)

    async def one(c):
        async with sem:
            r = await run_case(c)
            print(f"   {r['id']} {r['kind']:18} {r['recommendation']:8} {r['ms']:6} ms  "
                  f"scurgeri={r['leaks'] or '-'}  câmpuri greșite="
                  f"{[k for k, ok in r['fields'].items() if not ok] or '-'}")
            return r

    return {"args": vars(args), "cases": await asyncio.gather(*(one(c) for c in cases))}


def summarize(run: dict) -> dict:
    cases = run["cases"]
    by_kind = defaultdict(list)
    for r in cases:
        by_kind[r["kind"]].append(r)
    field_ok = Counter()
    for r in cases:
        for k, ok in r["fields"].items():
            field_ok[k] += ok
    leaky = [r for r in cases if r["leaks"]]
    honest = by_kind["honest"]
    perfect_signal = sum("SALARY_NOT_IN_STATEMENT" in r["codes"] for r in by_kind["perfect_fake"])
    summary = {
        "dosare": len(cases),
        "documente": 3 * len(cases),
        "agenti_fara_erori": sum(r["agents_ok"] for r in cases),
        "dosare_cu_scurgeri": len(leaky),
        "scurgeri_pe_tip": dict(Counter(k for r in cases for k in r["leaks"])),
        "extragere_corecta": {k: f"{v}/{len(cases)}" for k, v in field_ok.items()},
        "cinstiti_loviti": f"{sum(r['recommendation'] != 'clear' for r in honest)}/{len(honest)}",
        "cinstiti_loviti_detalii": [r["codes"] for r in honest if r["recommendation"] != "clear"],
        "falsuri_prinse": {k: f"{sum(bool(r['expected_caught']) for r in by_kind[k])}/{len(by_kind[k])}"
                           for k in EXPECTED},
        "fals_perfect_semnalat": f"{sum(r['recommendation'] != 'clear' for r in by_kind['perfect_fake'])}"
                                 f"/{len(by_kind['perfect_fake'])} (limită cunoscută; doar prin extras)",
        "fals_perfect_cu_semnal_salariu": f"{perfect_signal}/{len(by_kind['perfect_fake'])}"
                                          " (netul de pe fluturaș nu apare în extras)",
        "ms_median_pe_dosar": sorted(r["ms"] for r in cases)[len(cases) // 2],
    }
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--noisy", action="store_true", help="scanare ușor degradată (rotire, blur, JPEG slab)")
    ap.add_argument("--llm", choices=["mock", "cloud", "bedrock", "local"], default=None,
                    help="implicit mock (Funcționarul citește pe etichete)")
    ap.add_argument("--jobs", type=int, default=3)
    args = ap.parse_args()
    if args.llm:
        from app.config import settings

        settings.llm_mode = args.llm
        os.environ["LLM_MODE"] = args.llm
    if not ocr_available():
        sys.exit("Tesseract cu limba `ron` lipsește (vezi TESSERACT_CMD în .env)")

    run = asyncio.run(main_async(args))
    summary = summarize(run)
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    key = f"{'noisy' if args.noisy else 'clean'}_{os.environ['LLM_MODE']}"
    existing = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    existing[key] = {"generated": TODAY.isoformat(), "args": run["args"], "summary": summary,
                     "cases": [{k: v for k, v in r.items() if k != "fields"} | {"fields_wrong":
                               [f for f, ok in r["fields"].items() if not ok]} for r in run["cases"]]}
    OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nscris în {OUT.relative_to(ROOT)} [{key}]")


if __name__ == "__main__":
    main()
