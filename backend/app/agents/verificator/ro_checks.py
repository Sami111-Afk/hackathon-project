"""Verificări românești ieftine (ARCHITECTURE.md §5). Funcții pure; agentul le dă valorile.

Valorile în clar (CNP, IBAN, serie, adresă) vin din seiful local al Paznicului și nu
apar niciodată în mesaje — doar concluzia („67 de ani”, „alt județ”).
"""
import re
from datetime import date

from app.agents.functionar.classify import normalize
from app.models import Evidence, Finding

RETIREMENT_AGE = 65

# Prefixe de serie CI → județ (tabelă parțială, doar ce știm sigur; prefix necunoscut → nu verificăm)
SERIES_COUNTY = {
    "PH": "prahova", "PX": "prahova", "CJ": "cluj", "KX": "cluj", "TM": "timis", "TZ": "timis",
    "IS": "iasi", "MX": "iasi", "MZ": "iasi", "CT": "constanta", "KZ": "constanta", "BV": "brasov",
    "AR": "arad", "IF": "ilfov",
    "RD": "bucuresti", "RR": "bucuresti", "RT": "bucuresti", "RX": "bucuresti",
    "DP": "bucuresti", "DR": "bucuresti", "DT": "bucuresti", "DX": "bucuresti",
}

# Codul băncii din IBAN (caracterele 5–8) → cuvânt din numele băncii
IBAN_BANKS = {
    "RZBR": "raiffeisen", "BTRL": "transilvania", "BRDE": "brd", "RNCB": "bcr", "INGB": "ing",
    "CECE": "cec", "BACX": "unicredit", "BPOS": "posta", "OTPV": "otp", "TREZ": "trezor",
}


def cnp_birth_date(cnp: str) -> date | None:
    """S AA LL ZZ ...: 1/2 → 1900, 3/4 → 1800, 5/6 → 2000; 7/8/9 (străini) → secolul plauzibil."""
    if not re.fullmatch(r"\d{13}", cnp or ""):
        return None
    s, yy, mm, dd = int(cnp[0]), int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7])
    century = {1: 1900, 2: 1900, 3: 1800, 4: 1800, 5: 2000, 6: 2000}.get(s)
    if century is None:
        century = 2000 if yy <= date.today().year % 100 else 1900
    try:
        return date(century + yy, mm, dd)
    except ValueError:
        return None


def cnp_sex(cnp: str) -> str | None:
    if not re.fullmatch(r"\d{13}", cnp or "") or cnp[0] == "9":
        return None
    return "M" if int(cnp[0]) % 2 else "F"


def age_on(birth: date, on: date) -> int:
    return on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))


def check_age_employment(cnp: str | None, on: date, doc_id: str) -> Finding | None:
    birth = cnp_birth_date(cnp) if cnp else None
    if not birth:
        return None
    age = age_on(birth, on)
    if age < RETIREMENT_AGE:
        return None
    return Finding(code="AGE_EMPLOYMENT_MISMATCH", severity="medium",
                   message=f"Solicitant de {age} de ani declarat angajat activ",
                   evidence=Evidence(doc_id=doc_id))


def check_card_sex(cnp: str | None, card_sex: str | None, doc_id: str) -> Finding | None:
    sex = cnp_sex(cnp) if cnp else None
    printed = (card_sex or "").strip().upper()[:1]
    if not sex or printed not in ("M", "F") or printed == sex:
        return None
    return Finding(code="CNP_SEX_MISMATCH", severity="high",
                   message="Sexul de pe buletin nu corespunde cu CNP-ul",
                   evidence=Evidence(doc_id=doc_id, field="sex"))


def parse_iso(value) -> date | None:
    """„2026-09-30” → date; orice altceva (format greșit, None, număr) → None, fără excepții."""
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def check_id_validity(expiry: str | None, on: date, doc_id: str) -> Finding | None:
    if parse_iso(expiry) is None or parse_iso(expiry) >= on:
        return None
    return Finding(code="ID_EXPIRED", severity="medium", message=f"Buletinul a expirat ({expiry})",
                   evidence=Evidence(doc_id=doc_id, field="expiry_date"))


def address_county(address: str | None) -> str | None:
    m = re.search(r"\bjud(?:etul|\.)?\s+([a-z\- ]+?)(?:[,.]|$)", normalize(address or ""))
    return m.group(1).strip().replace(" ", "-") if m else None


def check_series_county(series: str | None, address: str | None, doc_id: str) -> Finding | None:
    expected = SERIES_COUNTY.get((series or "").strip().upper()[:2])
    county = address_county(address)
    if not expected or not county or county.startswith(expected):
        return None
    return Finding(code="SERIES_COUNTY_MISMATCH", severity="low",
                   message="Seria buletinului e de alt județ decât domiciliul",
                   evidence=Evidence(doc_id=doc_id, field="series"))


def check_iban_bank(iban: str | None, bank_name: str | None, doc_id: str) -> Finding | None:
    code = re.sub(r"\s", "", iban or "").upper()[4:8]
    expected = IBAN_BANKS.get(code)
    if not expected or not bank_name or expected in normalize(bank_name):
        return None
    return Finding(code="IBAN_BANK_MISMATCH", severity="medium",
                   message="Codul băncii din IBAN nu corespunde cu banca din antetul extrasului",
                   evidence=Evidence(doc_id=doc_id, field="iban"))


def check_dates(issue_date: str | None, founded: date | None, today: date, doc_id: str) -> list[Finding]:
    if not issue_date:
        return []
    issued = parse_iso(issue_date)
    if issued is None:
        return []
    out = []
    if issued > today:
        out.append(Finding(code="DOC_FUTURE_DATE", severity="high", message="Data emiterii e în viitor",
                           evidence=Evidence(doc_id=doc_id, field="issue_date")))
    if founded and issued < founded:
        out.append(Finding(code="DOC_BEFORE_COMPANY", severity="high",
                           message="Documentul e emis înainte de înființarea firmei",
                           evidence=Evidence(doc_id=doc_id, field="issue_date")))
    return out
