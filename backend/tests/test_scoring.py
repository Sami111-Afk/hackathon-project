from app.agents.compliance.scoring import score
from app.models import AgentResult, Finding


def res(agent, *findings, status="done"):
    return AgentResult(agent=agent, status=status,
                       findings=[Finding(code=c, severity=s, message=c) for c, s in findings])


def test_no_findings_is_clean():
    v, _ = score([res("verificator")])
    assert (v.recommendation, v.label, v.risk) == ("clear", "clean", 0)


def test_label_never_contradicts_recommendation():
    v, _ = score([res("detectiv", ("FRAUD_RING_SUSPECTED", "info")), res("detector", ("ELA_ANOMALY", "low"))])
    assert v.recommendation == "clear" and v.label == "clean"


def test_strong_soft_signal_goes_to_review_not_reject():
    v, _ = score([res("detector", ("ELA_ANOMALY", "critical"))])
    assert v.recommendation == "review"


def test_hard_override_escalates():
    v, _ = score([res("verificator", ("COMPANY_INACTIVE", "low"))])
    assert v.recommendation == "escalate"


def test_agent_error_marks_incomplete():
    v, _ = score([res("detector", status="error")])
    assert v.incomplete and v.recommendation == "review"
