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


def test_summary_check_flags_invented_numbers_and_labels():
    from app.agents.compliance.scoring import unsupported_claims
    ev = ("- NET_MISMATCH [high]: Netul calculat (8.307 lei) diferă de cel declarat (8.500 lei)\n"
          "- SHARED_IBAN [critical]: Contul [IBAN_1] apare în alte 5 cereri")
    assert unsupported_claims("Netul de 8.500 lei nu iese (8.307 lei); [IBAN_1] apare în 5 cereri. Risc 100%.",
                              ev, 0.998) == []
    assert set(unsupported_claims("Netul de 9.200 lei e fals; [CNP_1] e invalid.", ev, 0.998)) == {"9200", "[CNP_1]"}


def test_verdict_explains_its_score():
    from app.agents.compliance.scoring import score
    from app.models import AgentResult, Finding
    results = [AgentResult(agent="verificator", status="done", findings=[
        Finding(code="COMPANY_INACTIVE", severity="critical", message="firmă inactivă"),
        Finding(code="NET_MISMATCH", severity="high", message="net greșit"),
        Finding(code="ELA_ANOMALY", severity="high", message="zonă editată"),
        Finding(code="DOCS_CLASSIFIED", severity="info", message="clasificat")])]
    verdict, _ = score(results)
    assert [i.code for i in verdict.breakdown] == ["COMPANY_INACTIVE", "NET_MISMATCH", "ELA_ANOMALY"]
    assert verdict.breakdown[2].weight == 0.3  # semnal slab plafonat
    assert verdict.breakdown[0].hard_override
    keep = 1
    for i in verdict.breakdown:
        keep *= 1 - i.weight
    assert abs(verdict.risk - (1 - keep)) < 1e-3


def test_blurry_photo_caps_ocr_born_signals_at_review():
    # benchmark --phone: cinstit escaladat doar din semnale născute din OCR pe o poză neclară
    v, _ = score([res("paznic", ("OCR_LOW_QUALITY", "low"), ("MRZ_INVALID", "high"),
                      ("IBAN_CHECKSUM_INVALID", "medium"),
                      ("CNP_CHECKSUM_INVALID", "high")),
                  res("verificator", ("BALANCE_MISMATCH", "high"))])
    assert v.risk >= 0.7 and v.recommendation == "review"


def test_blurry_photo_still_escalates_on_signals_not_from_ocr():
    v, _ = score([res("paznic", ("OCR_LOW_QUALITY", "low")), res("verificator", ("COMPANY_INACTIVE", "critical"))])
    assert v.recommendation == "escalate"
    v, _ = score([res("paznic", ("OCR_LOW_QUALITY", "low")), res("detectiv", ("SHARED_IBAN", "high")),
                  res("verificator", ("NET_MISMATCH", "high"), ("BALANCE_MISMATCH", "high"))])
    assert v.recommendation == "escalate"


def test_clear_photo_unchanged():
    v, _ = score([res("verificator", ("NET_MISMATCH", "high"), ("BALANCE_MISMATCH", "high"))])
    assert v.recommendation == "escalate"


def test_signals_that_accuse_no_one_never_escalate():
    # poză de telefon: MRZ ilizibil + valori nelegate de document → la om, nu acuzat (benchmark --phone)
    v, _ = score([res("paznic", ("MRZ_INVALID", "high")),
                  res("functionar", *[("EXTRACTION_UNGROUNDED", "low")] * 4)])
    assert v.risk >= 0.70 and v.recommendation == "review"


def test_salary_missing_from_statement_goes_to_a_human():
    # singura urmă a falsului „perfect” (taxe refăcute corect): nu acuzăm, dar un om se uită
    v, _ = score([res("verificator", ("SALARY_NOT_IN_STATEMENT", "medium"))])
    assert v.recommendation == "review"


def test_real_evidence_still_escalates():
    v, _ = score([res("verificator", ("NET_MISMATCH", "high"), ("BALANCE_MISMATCH", "high"))])
    assert v.recommendation == "escalate"
