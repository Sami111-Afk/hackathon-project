"""Găsește datele personale în text: regex + cifre de control, MRZ, ancore pe etichete.

Ieșirea sunt span-uri (offset-uri în text), ca să poată fi mapate înapoi la bbox-uri
(ARCHITECTURE.md §4, pașii 2–5). GLiNER (nume/adrese fără etichetă) se adaugă peste.
"""
import re
from dataclasses import dataclass

from app.agents.paznic import validators as v


@dataclass(frozen=True)
class Span:
    kind: str           # CNP, IBAN, CUI, TELEFON, EMAIL, SERIE, NR, MRZ, PERSOANA, ADRESA, FIRMA
    start: int
    end: int
    value: str
    valid: bool | None = None  # None = fără cifră de control (nume, adresă, telefon…)


# prioritate la suprapuneri: MRZ acoperă tot ce e pe liniile lui
PRIORITY = {"MRZ": 0, "IBAN": 1, "CNP": 2, "CUI": 3, "SERIE": 4, "NR": 4, "EMAIL": 5, "TELEFON": 6,
            "ADRESA": 7, "FIRMA": 8, "PERSOANA": 9}

CNP_RX = re.compile(r"(?<!\d)[1-9]\d{12}(?!\d)")
IBAN_RX = re.compile(r"\bRO\d{2}\s?[A-Z]{4}(?:\s?[A-Z0-9]{4}){4}\b", re.I)
CUI_RX = re.compile(r"\b(?:CUI|CIF|C\.U\.I\.|cod fiscal|cod unic de [îi]nregistrare)\s*[:.]?\s*((?:RO)?\s?\d{2,10})\b",
                    re.I)
PHONE_RX = re.compile(r"(?<!\d)(?:\+40|0040|0)7\d{2}[\s.-]?\d{3}[\s.-]?\d{3}(?!\d)")
EMAIL_RX = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
SERIE_NR_RX = re.compile(r"\bSERIA\s*[:.]?\s*([A-Z]{2})\s*(?:NR\.?|N[O°]\.?)?\s*[:.]?\s*(\d{6})\b", re.I)
MRZ_RX = re.compile(r"^[A-Z0-9<]{30,44}$", re.M)

# eticheta → ce urmează după ea; pe buletin etichetele sunt bilingve („Nume/Nom/Last name”)
ANCHORS = {
    "PERSOANA": ["nume si prenume", "nume", "prenume", "nom", "prenom", "titular", "angajat", "salariat",
                 "solicitant", "client"],
    "ADRESA": ["domiciliu", "domiciliul", "adresa", "adresse", "address"],
    "FIRMA": ["angajator", "angajatorul", "societatea", "employer"],
}
# etichete după care valoarea se termină (pe aceeași linie); „nr” lipsește intenționat (apare în adrese)
STOP_LABELS = ["cnp", "cui", "cif", "seria", "iban", "functia", "funcția", "brut", "net", "data", "sex",
               "cetatenie", "cetățenie", "nationalitate", "loc nastere", "emis", "valabilitate", "telefon",
               "email", "sold", "perioada", "cont"] + [a for labels in ANCHORS.values() for a in labels]
# traducerile de pe buletin: „Nume/Nom/Last name”, „Domiciliu/Adresse/Address”
_LABEL_TAIL = r"(?:\s*/\s*(?:nom|prenom|last\s+name|first\s+name|surname|given\s+names?|adresse|address))*"

INJECTION_RX = re.compile(
    r"ignor[aăe]\w*\s+(?:toate\s+)?(?:instruc\w+|regul\w+)|ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)"
    r"|uit[aă]\s+(?:toate\s+)?instruc\w+|forget\s+(?:all\s+)?(?:previous\s+)?instructions"
    r"|system\s+prompt|you\s+are\s+now|e[sș]ti\s+acum\s+un|aprob[aă]\s+(?:acest|imediat|automat)"
    r"|approve\s+(?:this|the)\s+(?:loan|application)|r[aă]spunde\s+doar\s+cu\s+[\"„]?(?:aprobat|clear)",
    re.I,
)


def _ascii_fold(text: str) -> str:
    table = str.maketrans("ăâîșşțţĂÂÎȘŞȚŢéèÉÈ", "aaissttAAISSTTeeEE")
    return text.translate(table)


def find_identifiers(text: str) -> list[Span]:
    spans = []
    for m in CNP_RX.finditer(text):
        spans.append(Span("CNP", m.start(), m.end(), m.group(), v.valid_cnp(m.group())))
    for m in IBAN_RX.finditer(text):
        spans.append(Span("IBAN", m.start(), m.end(), m.group(), v.valid_iban(m.group())))
    for m in CUI_RX.finditer(text):
        val = m.group(1)
        spans.append(Span("CUI", m.start(1), m.end(1), val, v.valid_cui(val.replace(" ", ""))))
    for m in PHONE_RX.finditer(text):
        spans.append(Span("TELEFON", m.start(), m.end(), m.group()))
    for m in EMAIL_RX.finditer(text):
        spans.append(Span("EMAIL", m.start(), m.end(), m.group()))
    for m in SERIE_NR_RX.finditer(text):
        spans.append(Span("SERIE", m.start(1), m.end(1), m.group(1)))
        spans.append(Span("NR", m.start(2), m.end(2), m.group(2)))
    return spans


def find_mrz(text: str) -> list[Span]:
    """Liniile MRZ se ascund integral; validarea (7-3-1) se face doar pe ultima linie a blocului (linia 2 TD2)."""
    lines = [m for m in MRZ_RX.finditer(text) if "<" in m.group()]
    spans = []
    for i, m in enumerate(lines):
        line = m.group()
        is_last = i + 1 == len(lines) or text[m.end():lines[i + 1].start()].strip()
        parsed = v.parse_mrz_td2_line2(line) if is_last and i > 0 else None
        spans.append(Span("MRZ", m.start(), m.end(), line, parsed.valid if parsed else None))
    return spans


def find_anchored(text: str) -> list[Span]:
    """Valoarea de după o etichetă cunoscută: pe aceeași linie sau, dacă linia e goală, pe următoarea."""
    folded = _ascii_fold(text).lower()  # aceeași lungime ca textul → offset-urile rămân valabile
    stop_rx = re.compile(r"\b(?:" + "|".join(re.escape(_ascii_fold(s)) for s in STOP_LABELS) + r")\b\s*[:/]?")
    spans = []
    for kind, labels in ANCHORS.items():
        label_rx = re.compile(r"(?<![\w\[])(?:" + "|".join(re.escape(lbl) for lbl in labels) + r")\b" + _LABEL_TAIL
                              + r"\s*[:\-]?[ \t]*")
        for m in label_rx.finditer(folded):
            start = m.end()
            line_end = text.find("\n", start)
            line_end = len(text) if line_end == -1 else line_end
            if not text[start:line_end].strip() and line_end < len(text):  # valoarea e pe linia următoare
                start = line_end + 1
                line_end = text.find("\n", start)
                line_end = len(text) if line_end == -1 else line_end
            stop = stop_rx.search(folded, start, line_end)
            end = stop.start() if stop else line_end
            raw = text[start:end]
            value = raw.strip(" \t:,;")
            if len(value) < 3 or not re.search(r"[A-Za-zÀ-ÿ]", value) or value.startswith("["):
                continue
            if kind == "PERSOANA" and (len(value.split()) > 5 or re.search(r"\d", value)):
                continue
            offset = start + raw.index(value)
            spans.append(Span(kind, offset, offset + len(value), value))
    return spans


def find_prompt_injection(text: str) -> bool:
    return bool(INJECTION_RX.search(_ascii_fold(text)))


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Păstrează un singur span pe fiecare zonă: prioritatea tipului, apoi cel mai lung."""
    chosen: list[Span] = []
    for s in sorted(spans, key=lambda s: (PRIORITY.get(s.kind, 99), -(s.end - s.start), s.start)):
        if all(s.end <= c.start or s.start >= c.end for c in chosen):
            chosen.append(s)
    return sorted(chosen, key=lambda s: s.start)


def find_all(text: str) -> list[Span]:
    return resolve_overlaps(find_mrz(text) + find_identifiers(text) + find_anchored(text))
