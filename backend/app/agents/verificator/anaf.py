"""Angajatorul la ANAF: există, e activ, de când.

Acum: registrul simulat al demo-ului (aceleași firme ca în Arena), căutat după CUI sau nume.
P1: API-ul public ANAF (PlatitorTvaRest), cu cache local + limită de rată.

Atenție: COMPANY_NOT_FOUND e override dur în Compliance, deci îl emitem doar când sursa
e autoritară (ANAF real). Pe registrul simulat, o firmă necunoscută e doar „neverificată”.
"""
import re
from dataclasses import dataclass
from datetime import date

from app.agents.functionar.classify import normalize
from app.arena.missions import COMPANIES
from app.models import Evidence, Finding


@dataclass(frozen=True)
class Company:
    name: str
    cui: str
    active: bool
    founded: date | None
    source: str  # "demo" | "anaf"


def _cui_key(cui: str) -> str:
    return re.sub(r"\D", "", cui or "")


def _name_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", normalize(name or ""))


def lookup(cui: str | None = None, name: str | None = None) -> Company | None:
    for company_name, c in COMPANIES.items():
        if (cui and _cui_key(cui) == _cui_key(c["cui"])) or (name and _name_key(name) == _name_key(company_name)):
            return Company(company_name, c["cui"], c["active"], c.get("founded"), source="demo")
    return None


def check_company(company: Company | None, doc_id: str, label: str) -> list[Finding]:
    ev = Evidence(doc_id=doc_id, field="employer_cui")
    if company is None:
        return [Finding(code="COMPANY_UNVERIFIED", severity="info",
                        message=f"Angajatorul {label} nu a putut fi verificat în registru", evidence=ev)]
    if not company.active:
        return [Finding(code="COMPANY_INACTIVE", severity="critical",
                        message=f"Angajatorul {label} figurează inactiv la ANAF", evidence=ev)]
    return []
