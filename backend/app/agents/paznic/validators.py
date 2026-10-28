"""Cifre de control pentru identificatorii românești. Vezi ARCHITECTURE.md §4.

Toate funcțiile sunt pure și primesc șirul deja curățat de spații.
"""
import re
from dataclasses import dataclass
from datetime import date

CNP_WEIGHTS = "279146358279"
CUI_WEIGHTS = "753217532"
# JJ (județ): 01–46, 47/48 (fostele sectoare 7–8), 51–52 (Călărași, Giurgiu)
CNP_COUNTIES = {f"{i:02d}" for i in range(1, 49)} | {"51", "52"}
# S → secolul nașterii; 7/8/9 (rezidenți/cetățeni străini) nu codifică secolul
CNP_CENTURY = {"1": 1900, "2": 1900, "3": 1800, "4": 1800, "5": 2000, "6": 2000}


@dataclass(frozen=True)
class CnpInfo:
    birth_date: date
    sex: str  # "M" | "F"
    county: str


def _cnp_date(s: str, yy: int, mm: int, dd: int) -> date | None:
    centuries = [CNP_CENTURY[s]] if s in CNP_CENTURY else [2000, 1900]
    for century in centuries:
        try:
            d = date(century + yy, mm, dd)
        except ValueError:
            return None
        if d <= date.today():
            return d
    return None


def parse_cnp(cnp: str) -> CnpInfo | None:
    """CnpInfo dacă CNP-ul e valid (format, dată, județ, cifră de control), altfel None."""
    if len(cnp) != 13 or not cnp.isdigit() or cnp[0] == "0":
        return None
    total = sum(int(c) * int(w) for c, w in zip(cnp[:12], CNP_WEIGHTS, strict=True))
    control = total % 11
    if (1 if control == 10 else control) != int(cnp[12]):
        return None
    if cnp[7:9] not in CNP_COUNTIES:
        return None
    birth = _cnp_date(cnp[0], int(cnp[1:3]), int(cnp[3:5]), int(cnp[5:7]))
    if birth is None:
        return None
    sex = "M" if cnp[0] in "13579" else "F"
    return CnpInfo(birth_date=birth, sex=sex, county=cnp[7:9])


def valid_cnp(cnp: str) -> bool:
    return parse_cnp(cnp) is not None


def valid_iban(iban: str) -> bool:
    iban = iban.replace(" ", "").upper()
    if not iban.isalnum() or len(iban) < 15 or len(iban) > 34:
        return False
    if iban.startswith("RO") and len(iban) != 24:
        return False
    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(c, 36)) for c in rearranged)  # A=10 … Z=35
    return int(digits) % 97 == 1


# confuzii tipice de OCR: litere citite în loc de cifre
_OCR_DIGITS = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "S": "5", "B": "8", "Z": "2",
                             "G": "6"})


def repair_iban(raw: str) -> str | None:
    """IBAN RO citit greșit de OCR → varianta validă, sau None.

    Încearcă, în ordine: „R0” → „RO”; litere-confuzie → cifre în cele 16 caractere ale contului;
    un caracter în plus (OCR dublează des „0”/„O”). Checksum-ul mod 97 decide; fiecare încercare are
    ~1% șanse de potrivire întâmplătoare, deci rămân puține și în ordinea celor mai probabile.
    """
    iban = re.sub(r"\s", "", raw).upper()
    if iban.startswith("R0"):
        iban = "RO" + iban[2:]
    if not iban.startswith("RO") or len(iban) not in (23, 24, 25):
        return None
    head = iban[:8]  # RO + cifre de control + codul băncii (litere)
    head = head[:2] + head[2:4].translate(_OCR_DIGITS) + head[4:8]
    account = iban[8:]
    candidates = [head + account, head + account.translate(_OCR_DIGITS)]
    if len(account) == 17:
        for i in range(len(account)):
            if account[i] in "0O" and (i and account[i - 1] in "0O" or i + 1 < len(account) and account[i + 1] in "0O"):
                dropped = account[:i] + account[i + 1:]
                candidates += [head + dropped, head + dropped.translate(_OCR_DIGITS)]
    seen = set()
    for c in candidates:
        if c not in seen and len(c) == 24 and valid_iban(c):
            return c
        seen.add(c)
    return None


def iban_bank_code(iban: str) -> str | None:
    """Codul băncii din IBAN-ul RO (caracterele 5–8), ex. RZBR = Raiffeisen."""
    iban = iban.replace(" ", "").upper()
    return iban[4:8] if iban.startswith("RO") and len(iban) == 24 else None


def valid_cui(cui: str) -> bool:
    cui = cui.upper().removeprefix("RO").strip()
    if not cui.isdigit() or not 2 <= len(cui) <= 10:
        return False
    body, check = cui[:-1], int(cui[-1])
    weights = CUI_WEIGHTS[-len(body):]  # cheia se aliniază la dreapta
    control = sum(int(c) * int(w) for c, w in zip(body, weights, strict=True)) * 10 % 11
    return (0 if control == 10 else control) == check


# ── MRZ ──

def mrz_check_digit(field: str) -> int:
    """Cifra de control ICAO 9303: ponderi 7-3-1, cifre = valoarea, A=10…Z=35, '<'=0."""
    total = 0
    for i, c in enumerate(field):
        if c.isdigit():
            v = int(c)
        elif c.isalpha():
            v = ord(c.upper()) - 55
        else:
            v = 0
        total += v * (7, 3, 1)[i % 3]
    return total % 10


@dataclass(frozen=True)
class MrzLine2:
    """Linia 2 a unui MRZ TD2 (36 de caractere), formatul buletinului românesc."""
    document_number: str
    nationality: str
    birth_date: str   # YYMMDD
    sex: str          # M | F | <
    expiry_date: str  # YYMMDD
    optional: str
    checks_ok: dict[str, bool]

    @property
    def valid(self) -> bool:
        return all(self.checks_ok.values())


def parse_mrz_td2_line2(line: str) -> MrzLine2 | None:
    line = line.strip().upper()
    if len(line) != 36:
        return None

    def ok(field: str, digit: str) -> bool:
        return digit.isdigit() and mrz_check_digit(field) == int(digit)

    composite = line[0:10] + line[13:20] + line[21:35]
    return MrzLine2(
        document_number=line[0:9].rstrip("<"),
        nationality=line[10:13],
        birth_date=line[13:19],
        sex=line[20],
        expiry_date=line[21:27],
        optional=line[28:35].rstrip("<"),
        checks_ok={
            "document_number": ok(line[0:9], line[9]),
            "birth_date": ok(line[13:19], line[19]),
            "expiry_date": ok(line[21:27], line[27]),
            "composite": ok(composite, line[35]),
        },
    )


def mrz_matches_cnp(mrz: MrzLine2, cnp: str) -> bool:
    """Data nașterii și sexul din MRZ trebuie să fie aceleași ca în CNP."""
    info = parse_cnp(cnp)
    if info is None:
        return False
    return mrz.birth_date == info.birth_date.strftime("%y%m%d") and mrz.sex == info.sex
