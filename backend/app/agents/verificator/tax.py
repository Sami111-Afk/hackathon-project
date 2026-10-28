"""Taxele de pe fluturaș, refăcute în clar. Vezi ARCHITECTURE.md §5 (Verificator).

Simplificare declarată:
    CAS = 0,25·G   CASS = 0,10·G   impozit = 0,10·(G − CAS − CASS − D)
    net = 0,585·G + 0,1·D          toleranță ±2 lei (rotunjiri pe componente)

„Net” = înainte de alte rețineri (tichete, avansuri, popriri).
Funcția liniară `expected_net` e cea pe care o calculează și varianta HE.
"""
import math
from dataclasses import dataclass

from app.models import Evidence, Finding

CAS_RATE = 0.25
CASS_RATE = 0.10
INCOME_TAX_RATE = 0.10
NET_TOLERANCE_RON = 2.0

# Salariul minim brut pe țară; de confirmat valoarea curentă înainte de demo.
MIN_WAGE_RON = 4050

# Deducerea personală (tabelă simplificată): procent din salariul minim, după
# numărul de persoane în întreținere, pentru brut ≤ salariul minim. Peste, scade
# cu 0,5 puncte procentuale la fiecare 50 lei, până la salariul minim + 2.000 lei.
DEDUCTION_BASE_PCT = {0: 20.0, 1: 25.0, 2: 30.0, 3: 35.0, 4: 45.0}
DEDUCTION_STEP_RON = 50
DEDUCTION_STEP_PCT = 0.5
DEDUCTION_RANGE_RON = 2000


def _lei(amount: float) -> int:
    """Rotunjire la leu cu .5 în sus (round() din Python rotunjește la par)."""
    return math.floor(amount + 0.5)


def personal_deduction(gross: float, dependents: int = 0, min_wage: float = MIN_WAGE_RON) -> float:
    if gross <= 0 or gross > min_wage + DEDUCTION_RANGE_RON:
        return 0.0
    pct = DEDUCTION_BASE_PCT[min(max(dependents, 0), 4)]
    if gross > min_wage:
        steps = -(-(gross - min_wage) // DEDUCTION_STEP_RON)  # plafon: orice leu peste pragul de 50 contează
        pct -= steps * DEDUCTION_STEP_PCT
    return _lei(max(pct, 0.0) / 100 * min_wage)


def expected_net(gross: float, deduction: float = 0.0) -> float:
    """Forma liniară (fără rotunjiri), aceeași ca pe datele criptate."""
    return 0.585 * gross + 0.1 * deduction


@dataclass(frozen=True)
class PayslipTaxes:
    gross: float
    deduction: float
    cas: float
    cass: float
    income_tax: float
    net: float


def compute_payslip(gross: float, dependents: int = 0, min_wage: float = MIN_WAGE_RON) -> PayslipTaxes:
    """Componentele rotunjite la leu, cum apar pe un fluturaș real."""
    deduction = personal_deduction(gross, dependents, min_wage)
    cas = _lei(CAS_RATE * gross)
    cass = _lei(CASS_RATE * gross)
    income_tax = _lei(INCOME_TAX_RATE * max(gross - cas - cass - deduction, 0))
    return PayslipTaxes(gross, deduction, cas, cass, income_tax, gross - cas - cass - income_tax)


def check_net(
    gross: float,
    declared_net: float,
    dependents: int = 0,
    evidence: Evidence | None = None,
    min_wage: float = MIN_WAGE_RON,
) -> Finding | None:
    """NET_MISMATCH dacă netul declarat nu iese din brut, altfel None."""
    taxes = compute_payslip(gross, dependents, min_wage)
    if abs(declared_net - taxes.net) <= NET_TOLERANCE_RON:
        return None
    return Finding(
        code="NET_MISMATCH",
        severity="high",
        message=f"Netul calculat ({format_ron(taxes.net)} lei) diferă de cel declarat ({format_ron(declared_net)} lei)",
        evidence=evidence,
    )


def format_ron(amount: float) -> str:
    """8307 → '8.307', 8307.5 → '8.307,50'."""
    whole, frac = divmod(_lei(abs(amount) * 100), 100)
    text = f"{whole:,}".replace(",", ".")
    if frac:
        text += f",{frac:02d}"
    return ("-" if amount < 0 else "") + text
