"""Angajatorul la ANAF: există, e activ, de când. Vezi ARCHITECTURE.md §5 (Verificator).

Ordinea:
  1. registrul simulat al demo-ului (aceleași firme inventate ca în Arena), după CUI sau nume;
  2. API-ul public ANAF (PlatitorTvaRest v9), după CUI — cache local 24 h, maximum 1 apel/s;
  3. fără rețea → ultimul răspuns din cache, chiar expirat; altfel „neverificat”.

COMPANY_NOT_FOUND e override dur în Compliance, deci îl emitem DOAR când ANAF-ul real spune
„notFound”. În modul local (LLM_MODE=local: zero apeluri externe) și în teste: doar cache.
CUI-ul unei firme nu e dată personală; apelul intră totuși în jurnalul de audit.
Rețea → se apelează cu asyncio.to_thread.
"""
import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Literal

import httpx

from app.agents.functionar.classify import normalize
from app.arena.missions import COMPANIES
from app.config import REPO_ROOT, settings
from app.core import audit
from app.models import Evidence, Finding

log = logging.getLogger("orb.anaf")

ANAF_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"
CACHE_DIR = REPO_ROOT / "data" / "anaf_cache"
CACHE_TTL = timedelta(hours=24)
MIN_INTERVAL_S = 1.0  # limita publică ANAF: 1 cerere pe secundă
TIMEOUT_S = 5.0

Source = Literal["demo", "anaf", "cache", "unavailable"]

_rate_lock = threading.Lock()
_last_call = 0.0


@dataclass(frozen=True)
class Company:
    name: str
    cui: str
    active: bool
    founded: date | None
    source: Source


def _cui_key(cui: str | None) -> str:
    return re.sub(r"\D", "", cui or "")


def _name_key(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize(name or ""))


def lookup(cui: str | None = None, name: str | None = None) -> Company | None:
    """Doar registrul simulat al demo-ului."""
    for company_name, c in COMPANIES.items():
        if (cui and _cui_key(cui) == _cui_key(c["cui"])) or (name and _name_key(name) == _name_key(company_name)):
            return Company(company_name, c["cui"], c["active"], c.get("founded"), source="demo")
    return None


# ── ANAF real ────────────────────────────────────────────────────────────────

def _date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def parse_record(record: dict) -> Company:
    general = record.get("date_generale") or {}
    inactive = record.get("stare_inactiv") or {}
    deregistered = bool(inactive.get("dataRadiere"))
    return Company(
        name=general.get("denumire") or "",
        cui=str(general.get("cui") or ""),
        active=not inactive.get("statusInactivi") and not deregistered,
        founded=_date(general.get("data_inregistrare")),
        source="anaf",
    )


def _cache_path(cui: str):
    return CACHE_DIR / f"{cui}.json"


def _cache_read(cui: str) -> dict | None:
    try:
        return json.loads(_cache_path(cui).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _cache_write(cui: str, record: dict | None) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        entry = {"fetched": datetime.now(UTC).isoformat(timespec="seconds"), "record": record}
        _cache_path(cui).write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
    except OSError:
        log.warning("nu pot scrie cache-ul ANAF pentru %s", cui)


def _fresh(entry: dict) -> bool:
    try:
        return datetime.now(UTC) - datetime.fromisoformat(entry["fetched"]) < CACHE_TTL
    except (KeyError, ValueError):
        return False


def online_allowed() -> bool:
    return settings.env != "test" and settings.llm_mode != "local"


def _query(cui: str, on: date, case_id: str | None) -> dict | None:
    """Un apel ANAF. Întoarce {"found": record | None}; excepție dacă rețeaua/ANAF nu răspunde."""
    global _last_call
    with _rate_lock:
        wait = MIN_INTERVAL_S - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
    try:
        r = httpx.post(ANAF_URL, json=[{"cui": int(cui), "data": on.isoformat()}], timeout=TIMEOUT_S)
        if r.status_code != 404:  # ANAF răspunde 404 + {"found": [], "notFound": [cui]} pentru CUI inexistent
            r.raise_for_status()
        body = r.json()
        if r.status_code == 404 and "notFound" not in body:
            r.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        audit.record(kind="anaf", destination="anaf", case_id=case_id, outcome="error",
                     detail={"error": type(exc).__name__})
        raise
    audit.record(kind="anaf", destination="anaf", case_id=case_id, outcome="sent", detail={"cuis": 1})
    found = body.get("found") or []
    return {"found": found[0] if found else None}


def resolve(cui: str | None, name: str | None = None, case_id: str | None = None,
            on: date | None = None) -> tuple[Company | None, Source]:
    """(firma sau None, sursa). None + "anaf"/"cache" = ANAF spune că nu există."""
    if company := lookup(cui=cui, name=name):
        return company, "demo"
    key = _cui_key(cui)
    if not (2 <= len(key) <= 10):
        return None, "unavailable"

    cached = _cache_read(key)
    if cached and (_fresh(cached) or not online_allowed()):
        record = cached.get("record")
        return (parse_record(record) if record else None), "cache"
    if not online_allowed():
        return None, "unavailable"
    try:
        result = _query(key, on or date.today(), case_id)
    except (httpx.HTTPError, ValueError):
        log.warning("ANAF indisponibil pentru CUI-ul cerut")
        if cached:  # cache expirat e mai bun decât nimic
            record = cached.get("record")
            return (parse_record(record) if record else None), "cache"
        return None, "unavailable"
    _cache_write(key, result["found"])
    return (parse_record(result["found"]) if result["found"] else None), "anaf"


_LEGAL_FORMS = {"srl", "sa", "sca", "snc", "scs", "ii", "if", "pfa", "srl-d", "ong", "ra", "intreprindere",
                "individuala", "familiala", "societate", "comerciala", "sc", "si"}


def _name_tokens(name: str) -> set[str]:
    import re
    import unicodedata
    folded = "".join(c for c in unicodedata.normalize("NFKD", name or "") if not unicodedata.combining(c)).lower()
    return {t for t in re.split(r"[^a-z0-9]+", folded) if len(t) > 1 and t not in _LEGAL_FORMS}


def same_company(declared: str | None, registered: str | None) -> bool | None:
    """True/False dacă numele de pe document se potrivește cu cel de la ANAF; None dacă nu avem ce compara."""
    a, b = _name_tokens(declared or ""), _name_tokens(registered or "")
    if not a or not b:
        return None
    return len(a & b) / min(len(a), len(b)) >= 0.5


def check_company(company: Company | None, source: Source, doc_id: str, label: str,
                  declared_name: str | None = None) -> list[Finding]:
    ev = Evidence(doc_id=doc_id, field="employer_cui")
    if company is None and source in ("anaf", "cache"):
        return [Finding(code="COMPANY_NOT_FOUND", severity="critical",
                        message=f"Angajatorul {label} nu există în registrul ANAF", evidence=ev)]
    if company is None:
        return [Finding(code="COMPANY_UNVERIFIED", severity="info",
                        message=f"Angajatorul {label} nu a putut fi verificat la ANAF", evidence=ev)]
    # ANAF a răspuns cu firma de la acest CUI: e aceeași cu cea de pe document? Altfel NU-i folosim starea
    # (am atribui documentului situația unei firme străine — ex. un CUI inventat care există la altcineva).
    if source in ("anaf", "cache") and same_company(declared_name, company.name) is False:
        return [Finding(code="COMPANY_NAME_MISMATCH", severity="high",
                        message=f"CUI-ul {label} aparține la ANAF altei firme decât cea de pe document",
                        evidence=ev)]
    if not company.active:
        return [Finding(code="COMPANY_INACTIVE", severity="critical",
                        message=(f"Angajatorul {label} figurează inactiv la ANAF" if source in ("anaf", "cache")
                                 else f"Angajatorul {label} figurează inactiv (registru demo, nu ANAF real)"),
                        evidence=ev)]
    return []
