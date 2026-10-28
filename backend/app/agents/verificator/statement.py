"""Extrasul de cont: soldurile trebuie să se adune, iar salariul să apară ca încasare.

Rândurile vin de la Funcționar (ctx.scratch["functionar"][doc_id]["statement"]):
    sold anterior + sumă = sold, pe fiecare rând; soldul final = soldul ultimului rând.
"""
import math
from collections.abc import Callable

from app.agents.functionar.classify import normalize
from app.agents.verificator.tax import format_ron
from app.models import Evidence, Finding

BALANCE_TOLERANCE_RON = 0.01
SALARY_TOLERANCE_RON = 2.0


Reread = Callable[[int | None, list[float] | None], float | None]  # (pagina, chenar) → suma recitită


def _uncertain(doc_id: str, page, bbox, field: str | None = None) -> Finding:
    return Finding(code="AMOUNT_UNCERTAIN", severity="low",
                   message="Soldul nu iese cu sumele citite, dar iese la recitirea zonei: "
                           "probabil eroare de citire, de verificat pe document",
                   evidence=Evidence(doc_id=doc_id, page=page, bbox=bbox, field=field))


def _again(reread: Reread | None, page, bbox, value: float) -> float:
    """Valoarea recitită de pe imagine, dacă se poate; altfel cea citită inițial."""
    if reread is None or bbox is None:
        return value
    again = reread(page, bbox)
    return value if again is None else math.copysign(again, value)  # recitirea dă mărimea; semnul e al coloanei


def check_balances(table: dict, doc_id: str, reread: Reread | None = None) -> list[Finding]:
    """Cu `reread`, o nepotrivire e recitită de pe imagine înainte de a acuza: dacă la recitire soldul iese,
    e o eroare de OCR → AMOUNT_UNCERTAIN (low), nu BALANCE_MISMATCH."""
    rows = table.get("rows") or []
    findings: list[Finding] = []
    for prev, row in zip(rows, rows[1:], strict=False):
        if row.get("amount") is None or prev.get("balance") is None or row.get("balance") is None:
            continue
        expected = round(prev["balance"] + row["amount"], 2)
        if abs(expected - row["balance"]) <= BALANCE_TOLERANCE_RON:
            continue
        page = row["page"]
        again = round(_again(reread, prev["page"], prev.get("balance_bbox"), prev["balance"])
                      + _again(reread, page, row.get("amount_bbox"), row["amount"]), 2)
        if abs(again - _again(reread, page, row.get("balance_bbox"), row["balance"])) <= BALANCE_TOLERANCE_RON:
            findings.append(_uncertain(doc_id, page, row["bbox"]))
            continue
        findings.append(Finding(
            code="BALANCE_MISMATCH", severity="high",
            message=f"Soldul de pe {row['date']} ({format_ron(row['balance'])} lei) nu iese din rândul "
                    f"anterior ({format_ron(expected)} lei)",
            evidence=Evidence(doc_id=doc_id, page=page, bbox=row["bbox"])))
    closing = table.get("closing_balance")
    if (rows and closing is not None and rows[-1].get("balance") is not None
            and abs(closing - rows[-1]["balance"]) > BALANCE_TOLERANCE_RON):
        ev = table.get("closing_evidence") or {}
        last = rows[-1]
        closing_again = _again(reread, ev.get("page"), ev.get("bbox"), closing)
        last_again = _again(reread, last["page"], last.get("balance_bbox"), last["balance"])
        if abs(closing_again - last_again) <= BALANCE_TOLERANCE_RON:
            findings.append(_uncertain(doc_id, ev.get("page"), ev.get("bbox"), "closing_balance"))
        else:
            findings.append(Finding(
                code="BALANCE_MISMATCH", severity="high",
                message=f"Soldul final ({format_ron(closing)} lei) nu iese din tranzacții "
                        f"({format_ron(last['balance'])} lei)",
                evidence=Evidence(doc_id=doc_id, page=ev.get("page"), bbox=ev.get("bbox"), field="closing_balance")))
    return findings


def check_income(table: dict, doc_id: str, payslip_net: float | None) -> list[Finding]:
    """Netul de pe fluturaș ar trebui să apară ca încasare; o pensie la un „angajat” e de văzut."""
    rows = table.get("rows") or []
    credits = [r for r in rows if r["amount"] is not None and r["amount"] > 0]
    findings: list[Finding] = []
    if payslip_net and credits and not any(abs(r["amount"] - payslip_net) <= SALARY_TOLERANCE_RON for r in credits):
        findings.append(Finding(
            code="SALARY_NOT_IN_STATEMENT", severity="medium",
            message=f"Netul de pe fluturaș ({format_ron(payslip_net)} lei) nu apare ca încasare în extras",
            evidence=Evidence(doc_id=doc_id)))
    pension = next((r for r in credits if "pensie" in normalize(r["description"])), None)
    if pension and payslip_net:
        findings.append(Finding(
            code="PENSION_INCOME", severity="low",
            message=f"Extrasul arată o încasare de pensie ({format_ron(pension['amount'])} lei), "
                    "deși solicitantul se declară angajat",
            evidence=Evidence(doc_id=doc_id, page=pension["page"], bbox=pension["bbox"])))
    return findings
