"""Tipul documentului după titlurile fixe din text; LLM-ul doar dacă nu se găsește nimic."""
import re
import unicodedata

from app.models import DocType

# ordinea contează: adeverința poate conține „salariu”, fluturașul poate conține „extras”
KEYWORDS: list[tuple[DocType, tuple[str, ...]]] = [
    ("id_card", ("carte de identitate", "identity card", "carte d'identite", "idrou")),
    ("employment_certificate", ("adeverinta de salariat", "adeverinta", "certificat de angajare")),
    ("payslip", ("fluturas de salariu", "fluturas", "stat de plata", "net de plata", "rest de plata")),
    ("bank_statement", ("extras de cont", "sold initial", "sold final", "sold anterior")),
]


def normalize(text: str) -> str:
    """Minuscule, fără diacritice, spații unice (pentru căutări tolerante)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_by_keywords(text: str | None) -> DocType | None:
    if not text:
        return None
    norm = normalize(text)
    for doc_type, words in KEYWORDS:
        if any(w in norm for w in words):
            return doc_type
    return None
