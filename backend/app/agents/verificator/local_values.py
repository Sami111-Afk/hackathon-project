"""Valorile în clar din seiful local al Paznicului (CNP, IBAN, CUI ...), doar pe serverul băncii.

Verificatorul are nevoie de ele pentru calcule (vârsta din CNP, codul băncii din IBAN),
dar nu le pune niciodată în finding-uri și nu le trimite la LLM.
"""
import logging

log = logging.getLogger("orb.verificator")


def load(case_id: str) -> dict[str, list[str]]:
    """etichetă („[CNP_1]”) → valori; {} dacă seiful lipsește sau nu poate fi citit."""
    try:
        from app.agents.paznic.vault import vault
    except ImportError:
        return {}
    try:
        values = vault.get(case_id)
    except Exception:  # seif indisponibil → verificările care depind de el se sar
        log.warning("seiful nu poate fi citit pentru %s", case_id)
        return {}
    return {(k if k.startswith("[") else f"[{k}]"): v for k, v in values.items()}


def resolve(values: dict[str, list[str]], label_or_value) -> str | None:
    """„[CNP_1]” → valoarea din seif; o valoare care nu e etichetă rămâne ca atare."""
    if not isinstance(label_or_value, str) or not label_or_value:
        return None
    if label_or_value.startswith("["):
        found = values.get(label_or_value.strip())
        return found[0] if found else None
    return label_or_value
