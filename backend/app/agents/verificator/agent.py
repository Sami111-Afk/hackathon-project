"""🔍 Verificator — Stefan. Refacem calculele și verificăm coerența dosarului.

Totul determinist, fără LLM (ARCHITECTURE.md §5):
  fluturaș  → taxele refăcute (tax.py), NET_MISMATCH; cu HE_ENABLED pe date criptate (he_bank.py)
  extras    → soldurile rând cu rând + salariul ca încasare (statement.py)
  angajator → registrul demo, apoi ANAF real cu cache (anaf.py)
  dosar     → verificări românești pe valorile din seiful local (ro_checks.py)
  reguli    → regulile învățate și aprobate (learning/engine.py)

Citește doc.extracted + ctx.scratch["functionar"] (bbox-uri, rândurile extrasului).
"""
import asyncio
import logging
import math
from datetime import date

from app.agents.stubs import StubAgent
from app.agents.verificator import anaf, he_bank, local_values, ro_checks
from app.agents.verificator.reread import Rereader
from app.agents.verificator.ro_checks import parse_iso
from app.agents.verificator.statement import check_balances, check_income
from app.agents.verificator.tax import check_net, net_mismatch
from app.config import settings
from app.learning.engine import apply_rules
from app.models import AgentResult, Case, Document, Evidence, Finding

log = logging.getLogger("orb.verificator")

SEVERITY_RISK = {"info": 0.0, "low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.85}


def _val(doc: Document | None, name: str):
    ev = (doc.extracted or {}).get(name) if doc else None
    return ev.value if ev else None


def _first(case: Case, doc_type: str) -> Document | None:
    return next((d for d in case.documents if d.type == doc_type and d.extracted), None)


def _evidence(scratch: dict, doc: Document, name: str) -> Evidence:
    box = ((scratch.get(doc.id) or {}).get("fields") or {}).get(name) or {}
    return Evidence(doc_id=doc.id, page=box.get("page"), bbox=box.get("bbox"), field=name)


def _vault_first(values: dict[str, list[str]], kind: str) -> str | None:
    return next((v[0] for k, v in sorted(values.items()) if k.startswith(f"[{kind}_") and v), None)


def _confirm_net(slip: Document, scratch: dict, rereader: Rereader, findings: list[Finding],
                 period: str | None) -> list[Finding]:
    """NET_MISMATCH → recitim brutul și netul de pe imagine. Dacă la recitire netul iese, e o eroare de OCR:
    AMOUNT_UNCERTAIN (low) în loc de acuzație. Dacă recitirea confirmă cifrele, acuzația rămâne."""
    fields = (scratch.get(slip.id) or {}).get("fields") or {}

    def again(name: str) -> float:
        box = fields.get(name) or {}
        value = rereader.amount(slip.id, box.get("page"), box.get("bbox"))
        return _val(slip, name) if value is None else math.copysign(value, _val(slip, name))

    gross, net = again("gross_salary"), again("net_salary")
    if (gross, net) == (_val(slip, "gross_salary"), _val(slip, "net_salary")) or check_net(gross, net, period=period):
        return findings
    uncertain = Finding(code="AMOUNT_UNCERTAIN", severity="low",
                        message="Netul nu iese din brut cu sumele citite, dar iese la recitirea zonei: "
                                "probabil eroare de citire, de verificat pe document",
                        evidence=_evidence(scratch, slip, "net_salary"))
    return [f for f in findings if f.code != "NET_MISMATCH"] + [uncertain]


class Verificator:
    name = "verificator"
    start_message = "Refac calculele"

    def __init__(self, today: date | None = None) -> None:
        self.today = today

    async def run(self, case, ctx) -> AgentResult:
        scratch = ctx.scratch.get("functionar")
        if scratch is None:
            # Funcționarul a redat rezultatul de probă (fără Paznic real) → la fel și noi
            return await StubAgent(self.name, self.start_message, delay=1.8).run(case, ctx)

        today = self.today or date.today()
        values = local_values.load(case.id)
        findings: list[Finding] = []
        # înainte de a acuza pe baza unei sume, o recitim de pe imagine (OCR-ul mai greșește câte o cifră)
        files = getattr(ctx, "files", None) or {}
        rereader = Rereader(files) if files and Rereader.available() else None
        slip, card = _first(case, "payslip"), _first(case, "id_card")
        stmt = _first(case, "bank_statement")
        cert = _first(case, "employment_certificate")
        employment = slip or cert
        net = _val(slip, "net_salary")

        artifacts: dict[str, str] = {}
        if slip:
            slip_findings, artifacts = await self._payslip(slip, scratch, ctx, rereader)
            findings += slip_findings
        company = None
        if employment:
            cui = _val(employment, "employer_cui")
            company, source = await asyncio.to_thread(
                anaf.resolve, local_values.resolve(values, cui),
                local_values.resolve(values, _val(employment, "employer_name")), case.id)
            declared = local_values.resolve(values, _val(employment, "employer_name"))
            findings += anaf.check_company(company, source, employment.id, cui if isinstance(cui, str) else "",
                                           declared_name=declared)
            findings += ro_checks.check_dates(_val(employment, "issue_date"), company.founded if company else None,
                                              today, employment.id)
        if stmt:
            table = (scratch.get(stmt.id) or {}).get("statement") or {}
            if rereader:
                findings += await asyncio.to_thread(check_balances, table, stmt.id,
                                                    lambda page, bbox: rereader.amount(stmt.id, page, bbox))
            else:
                findings += check_balances(table, stmt.id)
            findings += check_income(table, stmt.id, net)
            if f := ro_checks.check_iban_bank(local_values.resolve(values, _val(stmt, "iban")),
                                              _val(stmt, "bank_name"), stmt.id):
                findings.append(f)

        cnp = _vault_first(values, "CNP")
        on = parse_iso(_val(employment, "issue_date")) or today
        if employment and (f := ro_checks.check_age_employment(cnp, on, employment.id)):
            findings.append(f)
        if card:
            for f in (ro_checks.check_card_sex(cnp, _val(card, "sex"), card.id),
                      ro_checks.check_id_validity(_val(card, "expiry_date"), today, card.id),
                      ro_checks.check_series_county(local_values.resolve(values, _val(card, "series")),
                                                    local_values.resolve(values, _val(card, "address")), card.id)):
                if f:
                    findings.append(f)

        if slip:
            # firmă găsită la ANAF real (nu în registrul demo) → regulile compară cu datele ei reale
            real = ({"active": company.active, "founded": company.founded}
                    if company and company.source != "demo" else None)
            findings += apply_rules(self._rule_doc(slip, company), company=real)

        keep = 1.0
        for f in findings:
            keep *= 1 - SEVERITY_RISK[f.severity]
        await ctx.emit("agent_progress", f"{len(findings)} verificări cu probleme")
        return AgentResult(agent="verificator", status="done", risk=round(1 - keep, 4), findings=findings,
                           artifacts=artifacts)

    @staticmethod
    async def _payslip(slip: Document, scratch: dict, ctx,
                       rereader: Rereader | None = None) -> tuple[list[Finding], dict[str, str]]:
        gross, net = _val(slip, "gross_salary"), _val(slip, "net_salary")
        if not isinstance(gross, int | float) or not isinstance(net, int | float):
            return [], {}  # sumă lipsă sau neparsată → nu acuzăm pe baza ei
        evidence, period = _evidence(scratch, slip, "net_salary"), _val(slip, "period")
        if settings.he_enabled and he_bank.available():
            try:
                report = await asyncio.to_thread(he_bank.bank.verify_nets,
                                                 [he_bank.NetItem(slip.id, gross, net, period)])
            except Exception:  # HE picat nu are voie să oprească verificarea → calculăm în clar
                log.exception("verificarea pe date criptate a eșuat; trec pe calculul în clar")
            else:
                check = report.checks[0]
                await ctx.emit("agent_progress", f"Taxe verificate pe date criptate (CKKS, {report.ms} ms)")
                findings = [] if check.ok else [net_mismatch(check.computed_net, net, evidence)]
                if findings and rereader:
                    findings = await asyncio.to_thread(_confirm_net, slip, scratch, rereader, findings, period)
                return findings, report.artifacts()
        f = check_net(gross, net, evidence=evidence, period=period)
        findings = [f] if f else []
        if findings and rereader:
            findings = await asyncio.to_thread(_confirm_net, slip, scratch, rereader, findings, period)
        return findings, {}

    @staticmethod
    def _rule_doc(slip: Document, company) -> dict:
        """Același format ca documentele din Arena, ca regulile învățate acolo să se aplice și aici."""
        doc = {"gross_salary": _val(slip, "gross_salary"), "net_salary": _val(slip, "net_salary"),
               "job_title": _val(slip, "job_title"), "employer": company.name if company else None}
        if issue := _val(slip, "issue_date"):
            doc["issue_date"] = issue
        return {k: v for k, v in doc.items() if v is not None}
