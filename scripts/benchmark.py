"""Benchmark ORB pe fluturași sintetici: câte falsuri prindem (pe tip) și câți oameni cinstiți lovim.

CE MĂSOARĂ ȘI CE NU (de spus la fel și în pitch):
  - Falsurile sunt generate de noi, pe tipuri pe care verificările le țintesc → 100% înseamnă că regulile
    sunt implementate corect, NU că prindem 100% din falsurile reale.
  - Fluturașii legitimi sunt tot sintetici (salarii plauzibile, inclusiv mici, cu 0–4 persoane în întreținere).
    0 fals pozitive aici = nu lovim oameni cinstiți pe CAZURILE PE CARE LE-AM GÂNDIT, nu o garanție.
  - Falsul „perfect” (taxe corecte, salariu plauzibil) NU poate fi prins doar din fluturaș: e nevoie de
    extrasul de cont / ANAF. Îl raportăm separat, ca limită cunoscută.

Rulare (din rădăcina repo-ului):  backend/.venv/bin/python scripts/benchmark.py [--n 40] [--seed 2026]
Ieșire: tabel în consolă + data/benchmark/results.json (cifrele pentru pitch).

Setul de TEST e generat cu alt seed decât setul legitim folosit de self-learning la backtest,
ca regulile învățate să nu fie evaluate pe datele pe care au fost verificate.
"""
import argparse
import json
import random
import statistics
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
import os  # noqa: E402

os.environ.setdefault("ENV", "test")

from app.agents.verificator.tax import compute_payslip  # noqa: E402
from app.arena.judge import judge  # noqa: E402
from app.arena.missions import COMPANIES  # noqa: E402
from app.learning import engine  # noqa: E402

# Regula învățată de Claude Opus în rularea live a Atacatorului (aprobată de om), păstrată ca exemplu.
LEARNED_RULE = {
    "id": "rule_live_1", "status": "approved",
    "description": "Brutul depășește de peste 1,55 ori medianul firmei pentru funcția declarată",
    "when": {"all": [{"left": "company.role_median", "op": "exists", "right": True},
                     {"left": "doc.gross_salary", "op": "ratio_gt", "right": ["company.role_median", 1.55]}]},
    "then": {"code": "GROSS_ABOVE_ROLE", "severity": "medium", "message": "Brut nejustificat față de funcție"},
}

ACTIVE = [n for n, c in COMPANIES.items() if c["active"]]


def payslip(rng, employer=None, role=None, factor=None, issued=None, dependents=0):
    employer = employer or rng.choice(ACTIVE)
    c = COMPANIES[employer]
    role = role or rng.choice(list(c["role_medians"]))
    factor = factor if factor is not None else rng.uniform(0.6, 1.45)
    gross = max(4325, round(c["role_medians"].get(role, c["median_gross"]) * factor / 50) * 50)
    if c["employees"] < 50:
        gross = min(gross, int(2.4 * c["median_gross"]))
    issued = issued or max(c["founded"], date(2026, 10, 1) - timedelta(days=rng.randint(1, 200)))
    period = issued.isoformat()[:7]
    return {"employee": "[PERSOANA_X]", "employer": employer, "job_title": role, "gross_salary": gross,
            "net_salary": int(compute_payslip(gross, dependents, period=period).net), "issue_date": issued.isoformat(),
            "tricks": []}


def renet(doc):
    doc["net_salary"] = int(compute_payslip(doc["gross_salary"], period=doc["issue_date"][:7]).net)
    return doc


# fiecare generator: (cum se numește, cum îl fabrică)
def fakes(rng):
    small = [n for n in ACTIVE if COMPANIES[n]["employees"] < 50]
    big = [n for n in ACTIVE if COMPANIES[n]["employees"] >= 50]
    return {
        "net umflat (fără taxe refăcute)": lambda: {**payslip(rng), "net_salary": rng.randint(9000, 15000)},
        "brut umflat la firmă mică": lambda: renet({**payslip(rng, rng.choice(small)), "gross_salary": rng.randint(16000, 25000)}),
        "firmă inactivă": lambda: renet({**payslip(rng), "employer": "Agro Prahova Distribuție SRL"}),
        "emis înainte de înființarea firmei": lambda: renet({**payslip(rng, "Nordic Consulting Grup SRL"), "issue_date": "2026-03-31"}),
        "dată în viitor": lambda: renet({**payslip(rng), "issue_date": "2027-01-31"}),
        "text ascuns pentru AI (prompt injection)": lambda: {**payslip(rng), "tricks": ["hide_injection"]},
        "ștampilă generată cu AI": lambda: {**payslip(rng), "tricks": ["ai_photo"]},
        "salariu umflat față de funcție (firmă mare)": lambda: payslip(rng, rng.choice(big), "Operator date", rng.uniform(2.2, 3.5)),
        "fals „perfect” (salariu plauzibil, taxe corecte)": lambda: payslip(rng, rng.choice(big), factor=rng.uniform(1.0, 1.4)),
    }


def caught(doc) -> tuple[bool, float]:
    t0 = time.perf_counter()
    r = judge(doc)
    return r["caught"], (time.perf_counter() - t0) * 1000


def evaluate(n: int, seed: int) -> dict:
    rng = random.Random(seed)
    legit = [payslip(rng) for _ in range(n * 4)]
    # oameni cinstiți cu salariu mic și persoane în întreținere (aici deducerea schimbă netul)
    legit += [payslip(rng, factor=rng.uniform(0.5, 0.9), dependents=rng.randint(1, 4)) for _ in range(n * 2)]
    fake_sets = {name: [make() for _ in range(n)] for name, make in fakes(rng).items()}
    out = {}
    for phase in ("înainte de self-learning", "după self-learning"):
        engine.clear()
        if phase.startswith("după"):
            engine.add_rule(LEARNED_RULE)
        times, row = [], {}
        fp = 0
        for d in legit:
            c, ms = caught(d)
            fp += c
            times.append(ms)
        for name, docs in fake_sets.items():
            hits = 0
            for d in docs:
                c, ms = caught(d)
                hits += c
                times.append(ms)
            row[name] = hits / len(docs)
        catchable = [v for k, v in row.items() if "perfect" not in k]
        out[phase] = {"recall_per_type": row, "recall_catchable": statistics.mean(catchable),
                      "false_positives": fp, "legit_total": len(legit),
                      "ms_per_doc": statistics.median(times)}
    engine.clear()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="falsuri per tip (legitime: 5×n)")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    res = evaluate(a.n, a.seed)
    names = list(next(iter(res.values()))["recall_per_type"])
    w = max(map(len, names)) + 2
    print(f"\n{'Tip de fals':<{w}}" + "".join(f"{p:>26}" for p in res))
    for name in names:
        print(f"{name:<{w}}" + "".join(f"{res[p]['recall_per_type'][name]:>25.0%} " for p in res))
    print("-" * (w + 52))
    for label, key, fmt in [("Prinse (fără falsul perfect)", "recall_catchable", "{:>25.0%} "),
                            ("Fals pozitive pe legitime", "false_positives", "{:>25} "),
                            ("ms per dosar (mediană)", "ms_per_doc", "{:>25.2f} ")]:
        print(f"{label:<{w}}" + "".join(fmt.format(res[p][key]) for p in res))
    legit_total = next(iter(res.values()))["legit_total"]
    print(f"\n{legit_total} fluturași legitimi (o parte cu salariu mic și persoane în întreținere), "
          f"{a.n} falsuri pe tip, seed {a.seed}.")
    print("ATENȚIE: date sintetice, falsuri create de noi — vezi docstring-ul pentru ce înseamnă cifrele.")
    out = ROOT / "data" / "benchmark"
    out.mkdir(parents=True, exist_ok=True)
    note = ("Date sintetice; falsurile sunt create de noi pe tipurile pe care verificările le țintesc. "
            "Arată că regulile funcționează corect pe aceste cazuri, nu acuratețea pe fraude reale. "
            "Falsul 'perfect' nu se poate prinde doar din fluturaș.")
    (out / "results.json").write_text(json.dumps({"n": a.n, "seed": a.seed, "note": note, **res}, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    print(f"scris: {(out / 'results.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
