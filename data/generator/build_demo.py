"""Documentele Mariei — VERSIUNE BRUTĂ (Samuel), de rafinat de Lorena.

Rulare din rădăcina repo-ului:  python -m data.generator.build_demo
Produce în data/demo/maria/:
  buletin.jpg   — CI cu MRZ corect, poză „generată” (placeholder), CNP valid
  fluturas.jpg  — net 8.500 declarat (corect ar fi 8.307), angajator inactiv; zona netului editată (ELA)
  extras.pdf    — extras Raiffeisen cu soldul final editat; producer „GIMP” în metadate
  truth.json    — adevărul: ce e fals și TOATE valorile PII (pentru benchmark / rata de scurgere)
Toate datele sunt INVENTATE.
"""
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pypdf import PdfReader, PdfWriter

from data.generator.ro_ids import cnp, iban, mrz_td2

ROOT = Path(__file__).resolve().parents[2]
FONTS = ROOT / "backend" / "app" / "arena" / "fonts"
OUT = ROOT / "data" / "demo" / "maria"

MARIA = {
    "surname": "IONESCU", "given": "MARIA", "sex": "F", "birth": "1959-03-12", "county": "PH",
    "address": "Str. Florilor nr. 12, Ploiești, jud. Prahova", "phone": "0722 318 405",
    "series": "PH", "number": "481925", "issued": "2019-05-20", "expiry": "2029-03-12",
}
EMPLOYER = {"name": "Agro Prahova Distribuție SRL", "cui": "RO9402119372"}  # inactivă în registrul Arenei/ANAF simulat


def font(size, bold=False):
    return ImageFont.truetype(str(FONTS / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size)


def lei(x):
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def jpeg(img, q):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def edit_region(img, box, draw_fn, q_before=75, q_after=92):
    """Rețeta pentru ELA: original salvat la q75 → zona editată → salvat la q92."""
    base = jpeg(img, q_before)
    d = ImageDraw.Draw(base)
    d.rectangle(box, fill="white")
    draw_fn(d)
    return base, q_after


def id_card(cnp_value):
    w, h = 1600, 1010
    img = Image.new("RGB", (w, h), "#e9eef2")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 120), fill="#1d4f91")
    d.text((40, 30), "ROMÂNIA  ·  ROUMANIE  ·  ROMANIA", font=font(34, True), fill="white")
    d.text((40, 140), "CARTE DE IDENTITATE / IDENTITY CARD", font=font(30, True), fill="#1d4f91")
    d.text((900, 140), f"SERIA {MARIA['series']}  NR {MARIA['number']}", font=font(30, True), fill="#b3261e")
    d.text((900, 190), f"CNP {cnp_value}", font=font(30, True), fill="black")
    # poza: „față generată” (placeholder vizibil; Detectorul o semnalează)
    d.rectangle((40, 200, 400, 660), fill="#c9d3dc", outline="#7a8a99", width=3)
    face = Image.new("RGB", (360, 460), "#d8c2ad")
    fd = ImageDraw.Draw(face)
    fd.ellipse((90, 70, 270, 290), fill="#e8cdb4")
    fd.rectangle((60, 320, 300, 460), fill="#4a5a6a")
    img.paste(face.filter(ImageFilter.GaussianBlur(1.2)), (40, 200))
    rows = [("Nume/Nom/Last name", MARIA["surname"]), ("Prenume/Prénom/First name", MARIA["given"]),
            ("Cetățenie/Nationalité/Nationality", "Română / ROU"), ("Sex/Sexe/Sex", MARIA["sex"]),
            ("Loc naștere/Lieu de naissance/Place of birth", "Mun. Ploiești, Jud. PH"),
            ("Domiciliu/Adresse/Address", MARIA["address"]),
            ("Valabilitate/Validité/Validity", f"{MARIA['issued'][8:]}.{MARIA['issued'][5:7]}.{MARIA['issued'][2:4]}"
                                                f"-{MARIA['expiry'][8:]}.{MARIA['expiry'][5:7]}.{MARIA['expiry'][:4]}")]
    y = 250
    for label, value in rows:
        d.text((440, y), label, font=font(20), fill="#555")
        d.text((440, y + 26), value, font=font(30, True), fill="black")
        y += 72
    l1, l2 = mrz_td2(MARIA["surname"], MARIA["given"], MARIA["series"], MARIA["number"],
                     MARIA["birth"], MARIA["sex"], MARIA["expiry"], cnp_value)
    d.rectangle((0, 820, w, h), fill="white")
    mono = font(40)
    d.text((40, 840), l1, font=mono, fill="black")
    d.text((40, 910), l2, font=mono, fill="black")
    return jpeg(img, 90), (l1, l2)


def payslip(cnp_value):
    w, h = 1240, 1754
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    gross = 14200
    cas, cass = round(gross * 0.25), round(gross * 0.10)
    tax = round(0.10 * (gross - cas - cass))
    d.text((80, 80), EMPLOYER["name"], font=font(30), fill="black")
    d.text((80, 125), f"CUI {EMPLOYER['cui']}  ·  Ploiești, jud. Prahova", font=font(22), fill="#333")
    d.text((80, 230), "FLUTURAȘ DE SALARIU", font=font(44, True), fill="black")
    d.text((80, 290), "Luna: septembrie 2026   ·   Emis: 30.09.2026", font=font(22), fill="#333")
    d.line((80, 340, w - 80, 340), fill="black", width=2)
    rows = [("Angajat", f"{MARIA['surname']} {MARIA['given']}"), ("CNP", cnp_value), ("Funcția", "Contabil"),
            ("Salariu brut", lei(gross)), ("CAS 25%", "-" + lei(cas)), ("CASS 10%", "-" + lei(cass)),
            ("Impozit 10%", "-" + lei(tax))]
    y = 380
    for label, value in rows:
        d.text((80, y), label, font=font(22), fill="black")
        d.text((w - 80, y), value, font=font(22), fill="black", anchor="ra")
        y += 70
    y += 30
    d.text((80, y), "NET DE PLATĂ", font=font(32, True), fill="black")
    d.text((w - 80, y), lei(gross - cas - cass - tax), font=font(32, True), fill="black", anchor="ra")
    net_box = (w - 420, y - 5, w - 75, y + 50)
    # falsul: netul corect (8.307) e înlocuit cu 8.500, iar imaginea re-salvată → ELA vede zona
    forged, q = edit_region(img, net_box, lambda dd: dd.text((w - 80, y), lei(8500), font=font(32, True),
                                                            fill="black", anchor="ra"))
    sd = ImageDraw.Draw(forged)
    sd.ellipse((w - 400, h - 420, w - 120, h - 140), outline="#1f4fa8", width=6)
    sd.text((w - 260, h - 280), "AGRO PRAHOVA", font=font(22), fill="#1f4fa8", anchor="mm")
    return jpeg(forged, q), {"net_bbox": list(net_box), "net_true": gross - cas - cass - tax, "net_declared": 8500}


def statement(iban_value):
    w, h = 1240, 1754
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, 140), fill="#fee600")
    d.text((80, 45), "Raiffeisen BANK", font=font(44, True), fill="black")
    d.text((80, 200), "EXTRAS DE CONT", font=font(40, True), fill="black")
    d.text((80, 260), f"Titular: {MARIA['surname']} {MARIA['given']}", font=font(22), fill="black")
    d.text((80, 295), f"IBAN: {iban_value}", font=font(22), fill="black")
    d.text((80, 330), "Perioada: 01.09.2026 – 30.09.2026", font=font(22), fill="black")
    tx = [("01.09", "Sold inițial", None, 1240.50), ("05.09", "Plată pensie", 2310.00, None),
          ("12.09", "Cumpărături card", -412.30, None), ("20.09", "Factură utilități", -286.70, None)]
    y, bal = 420, 0.0
    d.text((80, y), "Data      Descriere                                Sumă            Sold", font=font(22, True), fill="black")
    y += 50
    for date_, desc, amount, opening in tx:
        bal = opening if opening is not None else round(bal + amount, 2)
        d.text((80, y), date_, font=font(22), fill="black")
        d.text((230, y), desc, font=font(22), fill="black")
        if amount is not None:
            d.text((850, y), lei(amount), font=font(22), fill="black", anchor="ra")
        d.text((w - 80, y), lei(bal), font=font(22), fill="black", anchor="ra")
        y += 45
    y += 30
    d.text((80, y), "Sold final", font=font(26, True), fill="black")
    d.text((w - 80, y), lei(bal), font=font(26, True), fill="black", anchor="ra")
    box = (w - 400, y - 5, w - 75, y + 45)
    forged, q = edit_region(img, box, lambda dd: dd.text((w - 80, y), lei(26480), font=font(26, True),
                                                        fill="black", anchor="ra"))
    pdf_buf = io.BytesIO()
    jpeg(forged, q).save(pdf_buf, "PDF", resolution=150)
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf_buf.getvalue())))
    writer.add_metadata({"/Producer": "GIMP 2.10.38", "/Creator": "GIMP"})
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue(), {"balance_bbox": list(box), "balance_true": bal, "balance_declared": 26480}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cnp_value = cnp(MARIA["sex"], MARIA["birth"], MARIA["county"], seq=17)
    iban_value = iban("RZBR", "0000060012345678")
    card, mrz = id_card(cnp_value)
    card.save(OUT / "buletin.jpg", "JPEG", quality=90)
    slip, slip_truth = payslip(cnp_value)
    slip.save(OUT / "fluturas.jpg", "JPEG", quality=92)
    pdf, st_truth = statement(iban_value)
    (OUT / "extras.pdf").write_bytes(pdf)
    truth = {
        "case": "maria", "label": "identity_fraud", "requested_amount_ron": 45000,
        "pii": {"name": f"{MARIA['given']} {MARIA['surname']}", "cnp": cnp_value, "iban": iban_value,
                "address": MARIA["address"], "phone": MARIA["phone"], "id_series": MARIA["series"],
                "id_number": MARIA["number"], "mrz": list(mrz)},
        "documents": {
            "buletin.jpg": {"type": "id_card", "forged": ["photo"], "note": "poză înlocuită (placeholder generat)"},
            "fluturas.jpg": {"type": "payslip", "forged": ["net_salary"], **slip_truth,
                             "employer": EMPLOYER, "employer_inactive": True},
            "extras.pdf": {"type": "bank_statement", "forged": ["closing_balance"], **st_truth,
                           "producer": "GIMP 2.10.38"},
        },
    }
    (OUT / "truth.json").write_text(json.dumps(truth, indent=2, ensure_ascii=False), encoding="utf-8")
    print("scris în", OUT.relative_to(ROOT), "→", sorted(p.name for p in OUT.iterdir()))


if __name__ == "__main__":
    main()
