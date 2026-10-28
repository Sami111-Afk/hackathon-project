"""Sumele și datele în format românesc, parsate în Python (nu de LLM).

    parse_amount("14.200,00") == 14200.0     parse_amount("-412,30 lei") == -412.3
    parse_date("30.09.2026") == "2026-09-30"  parse_month("septembrie 2026") == "2026-09"
"""
import re
from datetime import date

MONTHS = {
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5, "iunie": 6,
    "iulie": 7, "august": 8, "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
}
_MONTH_PREFIX = {name[:3]: n for name, n in MONTHS.items()}  # „sept.”, „ian” ...

_LABEL = re.compile(r"\[[A-Z_]+_\d+\]")  # etichetele Paznicului nu sunt valori
_MINUS = "-−–"
_AMOUNT = re.compile(r"([" + _MINUS + r"]?)\s*(\d[\d.\s ]*(?:,\d{1,2})?)")


def parse_amount(text: str | None) -> float | None:
    """„14.200,00” → 14200.0. Punctul e separator de mii, virgula de zecimale.

    Fără virgulă, un punct urmat de 1–2 cifre e luat drept zecimale („8.5”, „2310.00”).
    """
    if not text:
        return None
    m = _AMOUNT.search(_LABEL.sub(" ", text).replace("\u00a0", " "))
    if not m:
        return None
    sign, body = m.group(1), re.sub(r"\s", "", m.group(2)).rstrip(".")
    if "," in body:
        whole, frac = body.rsplit(",", 1)
        whole = whole.replace(".", "")
    else:
        parts = body.split(".")
        if len(parts) > 1 and len(parts[-1]) in (1, 2):
            whole, frac = "".join(parts[:-1]), parts[-1]
        else:
            whole, frac = "".join(parts), ""
    if not whole.isdigit():
        return None
    value = float(f"{whole}.{frac or 0}")
    return -value if sign else value


_DMY = re.compile(r"\b(\d{1,2})\s*[./-]\s*(\d{1,2})\s*[./-]\s*(\d{4}|\d{2})\b")
_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_WORD = re.compile(r"\b(\d{1,2})\s+([a-zăâîșşțţ]+)\.?\s+(\d{4})\b", re.I)


def _year(y: str) -> int:
    if len(y) == 4:
        return int(y)
    yy = int(y)  # „20.05.19” de pe buletin; buletinele expiră cel mult ~peste 10 ani
    return 2000 + yy if yy <= date.today().year % 100 + 10 else 1900 + yy


def _month_number(word: str) -> int | None:
    w = word.lower().replace("ş", "ș").replace("ţ", "ț")
    return MONTHS.get(w) or _MONTH_PREFIX.get(w[:3])


def _iso(y: int, m: int, d: int) -> str | None:
    try:
        return date(y, m, d).isoformat()
    except ValueError:
        return None


def parse_date(text: str | None) -> str | None:
    """„30.09.2026”, „30/09/2026”, „2026-09-30”, „30 septembrie 2026” → „2026-09-30”."""
    if not text:
        return None
    if m := _ISO.search(text):
        return _iso(int(m[1]), int(m[2]), int(m[3]))
    if m := _DMY.search(text):
        return _iso(_year(m[3]), int(m[2]), int(m[1]))
    if (m := _WORD.search(text)) and (month := _month_number(m[2])):
        return _iso(int(m[3]), month, int(m[1]))
    return None


_MONTH_YEAR = re.compile(r"\b([a-zăâîșşțţ]+)\.?\s+(\d{4})\b", re.I)
_NUM_MONTH = re.compile(r"\b(\d{1,2})\s*[./-]\s*(\d{4})\b")


def parse_month(text: str | None) -> str | None:
    """„septembrie 2026”, „09/2026”, „Luna: sept. 2026” → „2026-09”."""
    if not text:
        return None
    for m in _MONTH_YEAR.finditer(text):
        if month := _month_number(m[1]):
            return f"{m[2]}-{month:02d}"
    if (m := _NUM_MONTH.search(text)) and 1 <= int(m[1]) <= 12:
        return f"{m[2]}-{int(m[1]):02d}"
    return None
