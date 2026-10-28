"""Identificatori românești INVENTAȚI, dar valizi matematic (cifre de control corecte).

Algoritmii sunt cei descriși în ARCHITECTURE §4. Folosiți doar pentru date sintetice.
"""
import random
import string

CNP_KEY = "279146358279"
CUI_KEY = "753217532"
COUNTY_CODES = {"AB": "01", "B": "40", "CJ": "12", "IS": "22", "PH": "29", "TM": "35", "BV": "08"}


def cnp(sex: str, birth: str, county: str, seq: int | None = None) -> str:
    """sex 'F'/'M', birth 'YYYY-MM-DD', county ex. 'PH'."""
    y, m, d = birth.split("-")
    century = int(y[:2])
    s = {19: {"M": 1, "F": 2}, 18: {"M": 3, "F": 4}, 20: {"M": 5, "F": 6}}[century][sex]
    nnn = f"{seq if seq is not None else random.randint(1, 999):03d}"
    body = f"{s}{y[2:]}{m}{d}{COUNTY_CODES[county]}{nnn}"
    c = sum(int(a) * int(b) for a, b in zip(body, CNP_KEY)) % 11
    return body + ("1" if c == 10 else str(c))


def cnp_valid(value: str) -> bool:
    if len(value) != 13 or not value.isdigit():
        return False
    c = sum(int(a) * int(b) for a, b in zip(value[:12], CNP_KEY)) % 11
    return value[12] == ("1" if c == 10 else str(c))


def _iban_mod97(s: str) -> int:
    digits = "".join(str(int(ch, 36)) for ch in s)
    return int(digits) % 97


def iban(bank: str = "RZBR", account: str | None = None) -> str:
    account = account or "".join(random.choices(string.digits, k=16))
    check = 98 - _iban_mod97(f"{bank}{account}RO00")
    return f"RO{check:02d}{bank}{account}"


def iban_valid(value: str) -> bool:
    v = value.replace(" ", "").upper()
    return len(v) == 24 and v.startswith("RO") and _iban_mod97(v[4:] + v[:4]) == 1


def cui(base: str | None = None) -> str:
    base = base or str(random.randint(10**6, 10**8 - 1))
    padded = base.rjust(9, "0")
    c = sum(int(a) * int(b) for a, b in zip(padded, CUI_KEY)) * 10 % 11
    return base + ("0" if c == 10 else str(c))


def cui_valid(value: str) -> bool:
    v = value.upper().removeprefix("RO")
    if not v.isdigit() or not 2 <= len(v) <= 10:
        return False
    return cui(v[:-1]) == v


# ── MRZ pentru cartea de identitate românească (TD2: 2 rânduri × 36) ──

def _mrz_cd(s: str) -> str:
    vals = {**{str(i): i for i in range(10)}, **{ch: i + 10 for i, ch in enumerate(string.ascii_uppercase)}, "<": 0}
    return str(sum(vals[ch] * w for ch, w in zip(s, [7, 3, 1] * 20)) % 10)


def mrz_td2(surname: str, given: str, series: str, number: str, birth: str, sex: str,
            expiry: str, cnp_value: str) -> tuple[str, str]:
    name = f"{surname}<<{given}".upper().replace(" ", "<").replace("-", "<")
    line1 = f"IDROU{name}"[:36].ljust(36, "<")
    doc = f"{series}{number}"[:9].ljust(9, "<")
    b = birth[2:4] + birth[5:7] + birth[8:10]
    e = expiry[2:4] + expiry[5:7] + expiry[8:10]
    optional = (cnp_value[0] + cnp_value[7:13])[:7]
    core = f"{doc}{_mrz_cd(doc)}ROU{b}{_mrz_cd(b)}{sex}{e}{_mrz_cd(e)}{optional}"
    composite = _mrz_cd(f"{doc}{_mrz_cd(doc)}{b}{_mrz_cd(b)}{e}{_mrz_cd(e)}{optional}")
    return line1, (core + composite)[:36].ljust(36, "<")


def mrz_td2_valid(lines: tuple[str, str]) -> bool:
    line1, line2 = lines
    if len(line1) != 36 or len(line2) != 36:
        return False
    allowed = set(string.ascii_uppercase + string.digits + "<")
    if any(ch not in allowed for ch in line1 + line2):
        return False

    document = line2[:9]
    birth = line2[13:19]
    expiry = line2[21:27]
    optional = line2[28:35]
    document_check, birth_check, expiry_check = line2[9], line2[19], line2[27]
    if document_check != _mrz_cd(document):
        return False
    if birth_check != _mrz_cd(birth) or expiry_check != _mrz_cd(expiry):
        return False
    composite = document + document_check + birth + birth_check + expiry + expiry_check + optional
    return line2[35] == _mrz_cd(composite)
