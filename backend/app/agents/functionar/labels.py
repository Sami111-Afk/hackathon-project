"""Extragere pe etichete („Salariu brut … 14.200,00”), fără LLM.

Plasa de siguranță: când LLM-ul nu răspunde (mod mock fără cache, cheie expirată) sau
dă un câmp care nu se regăsește în document. Valoarea = exact textul din document,
deci e grounded prin construcție.
"""
import re

from app.agents.functionar.classify import normalize
from app.agents.functionar.layout import Line
from app.agents.functionar.schemas import RawField

AMT = r"([-−–]?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2})"
DATE = r"(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})"
LABEL = r"\[{kind}_\d+\]"

# câmp → regex pe textul unui rând; grupul 1 = valoarea. Primul rând care se potrivește câștigă.
SAME_LINE: dict[str, dict[str, str]] = {
    "payslip": {
        "employer_cui": rf"\bCUI\b:?\s*({LABEL.format(kind='CUI')}|(?:RO)?\d{{2,10}})",
        "employer_name": rf"^({LABEL.format(kind='FIRMA')}|.+\b(?:SRL|S\.R\.L\.|SA|S\.A\.))\s*$",
        "employee_name": r"^Angajat(?:ul)?:?\s+(.+)$",
        "job_title": r"^Func[tțţ]i[ae]:?\s+(.+)$",
        "period": r"\bLuna:?\s*([A-Za-zăâîșşțţ]+\.?\s+\d{4}|\d{1,2}[./]\d{4})",
        "issue_date": rf"\bEmis(?:\s+la)?:?\s*{DATE}",
        "gross_salary": rf"^Salariu(?:l)?\s+brut\b.*?{AMT}\s*$",
        "personal_deduction": rf"^Deducere\b.*?{AMT}\s*$",
        "cas": rf"^CAS\b.*?{AMT}\s*$",
        "cass": rf"^CASS\b.*?{AMT}\s*$",
        "income_tax": rf"^Impozit\b.*?{AMT}\s*$",
        "net_salary": rf"^(?:NET\s+DE\s+PLAT[AĂ]|REST\s+DE\s+PLAT[AĂ]|Salariu(?:l)?\s+net)\b.*?{AMT}\s*$",
    },
    "bank_statement": {
        "bank_name": r"^(.*\b(?:bank|banca)\b.*)$",
        "account_holder": r"^Titular:?\s+(.+)$",
        "iban": rf"\bIBAN:?\s*({LABEL.format(kind='IBAN')}|RO\d{{2}}[A-Z]{{4}}[A-Z0-9]{{16}})",
        "period_start": rf"Perioada:?\s*{DATE}",
        "period_end": rf"Perioada:?\s*\S+\s*[-–—]\s*{DATE}",
    },
    "id_card": {
        "series": rf"\bSERIA\s+({LABEL.format(kind='SERIE')}|[A-Z]{{2}})(?!\w)",
    },
    "employment_certificate": {
        "employer_cui": rf"\bCUI\b:?\s*({LABEL.format(kind='CUI')}|(?:RO)?\d{{2,10}})",
        "employment_start_date": rf"\bangajat\S*\s+(?:din|începând cu|incepand cu|de la)\s+(?:data\s+de\s+)?{DATE}",
        "gross_salary": rf"\bsalariu(?:l)?\s+(?:de\s+bază\s+)?brut\b.*?{AMT}",
        "net_salary": rf"\bsalariu(?:l)?\s+net\b.*?{AMT}",
    },
}

# buletinul: eticheta pe un rând, valoarea pe rândul următor (prefix normalizat → câmp)
NEXT_LINE = {
    "id_card": {
        "nume/": "last_name",
        "prenume/": "first_name",
        "cetatenie": "nationality",
        "sex/": "sex",
        "loc nastere": "birth_place",
        "domiciliu": "address",
        "valabilitate": "_validity",
    },
}
_VALIDITY = re.compile(rf"{DATE}\s*[-–—]\s*{DATE}")


def _raw(text: str) -> RawField:
    text = text.strip()
    return RawField(value=text, source_text=text)


def extract_by_labels(doc_type: str, lines: list[Line]) -> dict[str, RawField]:
    out: dict[str, RawField] = {}
    for name, pattern in SAME_LINE.get(doc_type, {}).items():
        rx = re.compile(pattern, re.I)
        for line in lines:
            if m := rx.search(line.text):
                out[name] = _raw(m.group(1))
                break
    labels = NEXT_LINE.get(doc_type, {})
    for line, nxt in zip(lines, lines[1:], strict=False):
        norm = normalize(line.text)
        name = next((f for prefix, f in labels.items() if norm.startswith(prefix)), None)
        if not name or name in out:
            continue
        if name == "_validity":
            if m := _VALIDITY.search(nxt.text):
                out["issue_date"], out["expiry_date"] = _raw(m.group(1)), _raw(m.group(2))
        else:
            out[name] = _raw(nxt.text)
    return out
