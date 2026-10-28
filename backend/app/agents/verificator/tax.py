"""Taxele de pe fluturaș, refăcute în clar. Vezi ARCHITECTURE.md §5 (Verificator).

Simplificare declarată:
    N = suma netaxabilă (salariul minim, OUG 89/2025: 300 lei ian–iun 2026, 200 lei iul–dec 2026)
    CAS = 0,25·(G − N)   CASS = 0,10·(G − N)   impozit = 0,10·(G − N − CAS − CASS − D)
    net = 0,585·G + 0,415·N + 0,1·D          toleranță ±2 lei (rotunjiri pe componente)

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

# Salariul minim brut, după luna fluturașului: (de la „YYYY-MM”, valoare). HG 146/2026: 4.325 de la 1 iulie 2026.
MIN_WAGE_HISTORY = [("2025-01", 4050), ("2026-07", 4325)]
MIN_WAGE_RON = MIN_WAGE_HISTORY[-1][1]

# Suma netaxabilă pentru salariul minim (OUG 89/2025): (de la, sumă, plafonul brutului până la care se aplică)
UNTAXED_HISTORY = [("2025-01", 300, 4300), ("2026-07", 200, 4600)]


def _pick(history: list, period: str | None):
    """Valoarea în vigoare pentru luna „YYYY-MM” (implicit: cea mai recentă)."""
    if not period:
        return history[-1]
    current = history[0]
    for row in history:
        if period[:7] >= row[0]:
            current = row
    return current


def min_wage_for(period: str | None = None) -> int:
    return _pick(MIN_WAGE_HISTORY, period)[1]


def untaxed_amount(gross: float, period: str | None = None) -> int:
    """Suma netaxabilă: doar pentru brut între salariul minim și plafon."""
    _, amount, ceiling = _pick(UNTAXED_HISTORY, period)
    return amount if min_wage_for(period) <= gross <= ceiling else 0

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
        return 0
    pct = DEDUCTION_BASE_PCT[min(max(dependents, 0), 4)]
    if gross > min_wage:
        steps = -(-(gross - min_wage) // DEDUCTION_STEP_RON)  # plafon: orice leu peste pragul de 50 contează
        pct -= steps * DEDUCTION_STEP_PCT
    return _lei(max(pct, 0.0) / 100 * min_wage)


def expected_net(gross: float, deduction: float = 0.0, untaxed: float = 0.0) -> float:
    """Forma liniară (fără rotunjiri), aceeași ca pe datele criptate: N și D le calculează banca în clar."""
    return 0.585 * gross + 0.415 * untaxed + 0.1 * deduction


@dataclass(frozen=True)
class PayslipTaxes:
    gross: float
    deduction: float
    untaxed: float
    cas: float
    cass: float
    income_tax: float
    net: float


def compute_payslip(gross: float, dependents: int = 0, min_wage: float | None = None,
                    period: str | None = None) -> PayslipTaxes:
    """Componentele rotunjite la leu, cum apar pe un fluturaș real. `period` = „YYYY-MM” (luna fluturașului)."""
    min_wage = min_wage or min_wage_for(period)
    deduction = personal_deduction(gross, dependents, min_wage)
    untaxed = untaxed_amount(gross, period) if min_wage == min_wage_for(period) else 0
    base = gross - untaxed
    cas = _lei(CAS_RATE * base)
    cass = _lei(CASS_RATE * base)
    income_tax = _lei(INCOME_TAX_RATE * max(base - cas - cass - deduction, 0))
    return PayslipTaxes(gross, deduction, untaxed, cas, cass, income_tax, gross - cas - cass - income_tax)


def check_net(
    gross: float,
    declared_net: float,
    dependents: int = 0,
    evidence: Evidence | None = None,
    min_wage: float | None = None,
    period: str | None = None,
) -> Finding | None:
    """NET_MISMATCH dacă netul declarat nu iese din brut, altfel None. `period` = luna fluturașului („YYYY-MM”)."""
    taxes = compute_payslip(gross, dependents, min_wage, period)
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
