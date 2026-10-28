"""Poarta anti-scurgere: ultimul control înainte ca un payload să plece spre un LLM din cloud.

Blochează dacă găsește:
  1. un CNP / IBAN / telefon / email în clar (regex);
  2. orice valoare din seif pentru dosarul curent (nume, adresă, CNP...) — potrivire
     exactă după normalizare (fără diacritice, litere mici, spații comprimate).
Paznicul (Narcis) înregistrează valorile din seif cu `register_vault_values`.
"""
import re
import unicodedata
from collections import defaultdict

PATTERNS = {
    "CNP": re.compile(r"(?<!\d)[1-9]\d{12}(?!\d)"),
    "IBAN": re.compile(r"\bRO\d{2}\s?[A-Z]{4}(?:\s?[A-Z0-9]{4}){4}\b", re.I),
    "TELEFON": re.compile(r"(?<!\d)(?:\+40|0040|0)7\d{2}[\s.-]?\d{3}[\s.-]?\d{3}(?!\d)"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
}

MIN_VALUE_LEN = 4  # valori mai scurte (ex. „PH”) ar da prea multe alarme false

_vault: dict[str, set[str]] = defaultdict(set)


def normalize(text: str) -> str:
    text = text.replace("ş", "ș").replace("ţ", "ț").replace("Ş", "Ș").replace("Ţ", "Ț")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().lower()


def register_vault_values(case_id: str, values: list[str]) -> None:
    for v in values:
        n = normalize(v)
        if len(n) >= MIN_VALUE_LEN:
            _vault[case_id].add(n)


def known_values(case_id: str | None) -> int:
    """Câte valori personale ale dosarului caută poarta (pentru audit: arată că verificarea nu e goală)."""
    return len(_vault.get(case_id, ())) if case_id else 0


def forget_case(case_id: str) -> None:
    _vault.pop(case_id, None)


def scan(text: str, case_id: str | None) -> list[str]:
    """Întoarce tipurile de date găsite (fără valori!). Listă goală = sigur de trimis."""
    hits = [kind for kind, rx in PATTERNS.items() if rx.search(text)]
    if case_id and _vault.get(case_id):
        norm = normalize(text)
        if any(v in norm for v in _vault[case_id]):
            hits.append("VALOARE_DIN_SEIF")
    return hits


class PIIGateBlocked(Exception):
    def __init__(self, kinds: list[str]):
        super().__init__(f"apel blocat de poarta anti-PII: {', '.join(kinds)}")
        self.kinds = kinds
