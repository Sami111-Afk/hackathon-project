"""Arbitrul provizoriu al Arenei: verificările reale pentru fluturaș, pe datele știute exact.

Când agenții reali sunt gata, ARENA_USE_PIPELINE=true trimite falsurile prin pipeline-ul
complet. Până atunci, aceleași verificări pe care le face Verificatorul + reguli învățate.
"""
from datetime import date

from app.agents.compliance.scoring import score
from app.agents.verificator.tax import check_net
from app.arena.missions import COMPANIES
from app.models import AgentResult, Finding

TODAY = date(2026, 10, 28)


def check(doc: dict) -> list[AgentResult]:
    verificator: list[Finding] = []
    detector: list[Finding] = []
    paznic: list[Finding] = []
    gross, net = doc["gross_salary"], doc["net_salary"]
    company = COMPANIES.get(doc["employer"])
    issued = date.fromisoformat(doc["issue_date"])

    if mismatch := check_net(gross, net):  # calculul real al Verificatorului (Stefan)
        verificator.append(mismatch)
    if company is None:
        verificator.append(Finding(code="COMPANY_NOT_FOUND", severity="critical", message="Angajatorul nu există"))
    else:
        if not company["active"]:
            verificator.append(Finding(code="COMPANY_INACTIVE", severity="critical",
                                       message="Angajatorul figurează inactiv la ANAF"))
        if issued < company["founded"]:
            verificator.append(Finding(code="DOC_BEFORE_COMPANY", severity="high",
                                       message="Documentul e emis înainte de înființarea firmei"))
        if company["median_gross"] and gross > 2.5 * company["median_gross"] and company["employees"] < 50:
            verificator.append(Finding(code="SALARY_IMPLAUSIBLE", severity="medium",
                                       message=f"Brut de {gross} lei la o firmă cu {company['employees']} angajați"))
    if issued > TODAY:
        verificator.append(Finding(code="DOC_FUTURE_DATE", severity="high", message="Data emiterii e în viitor"))
    if "hide_injection" in doc["tricks"]:
        paznic.append(Finding(code="PROMPT_INJECTION_SUSPECTED", severity="critical",
                              message="Text ascuns care încearcă să manipuleze AI-ul"))
    if "ai_photo" in doc["tricks"]:
        detector.append(Finding(code="AI_IMAGE_SUSPECTED", severity="medium",
                                message="Ștampila pare generată cu AI"))

    from app.learning.engine import apply_rules  # reguli învățate (self-learning)
    verificator += apply_rules(doc)

    return [AgentResult(agent="paznic", status="done", findings=paznic),
            AgentResult(agent="verificator", status="done", findings=verificator),
            AgentResult(agent="detector", status="done", findings=detector)]


def judge(doc: dict) -> dict:
    results = check(doc)
    verdict, top = score(results)
    # în joc: prins = orice dovadă de gravitate medie sau mai mare (sau o recomandare ≠ clear)
    caught = verdict.recommendation != "clear" or any(
        f.severity in ("medium", "high", "critical") for r in results for f in r.findings)
    return {"caught": caught, "verdict": verdict, "results": results,
            "caught_by": sorted({r.agent for r in results if r.findings}),
            "reasons": [f.message for f in top if f.severity != "info"][:4]}
