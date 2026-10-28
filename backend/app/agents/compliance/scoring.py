"""Scorul de risc al Compliance — determinist, LLM-ul nu îl decide (ARCHITECTURE §5).

risk = 1 − Π(1 − wᵢ)   (noisy-OR pe ponderile finding-urilor)
- semnalele slabe (ELA, AI-detector) sunt plafonate
- override-urile dure împing recomandarea minim la "escalate"
"""
from app.models import AgentResult, Finding, Verdict

SEVERITY_WEIGHT = {"info": 0.0, "low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.85}

SOFT_SIGNALS = {"ELA_ANOMALY": 0.3, "AI_IMAGE_SUSPECTED": 0.3, "EXIF_EDITOR": 0.2}

HARD_OVERRIDES = {"CNP_CHECKSUM_INVALID", "COMPANY_INACTIVE", "MRZ_INVALID", "COMPANY_NOT_FOUND",
                  "PROMPT_INJECTION_SUSPECTED", "PII_GATE_BLOCKED"}

FORGERY_CODES = {"NET_MISMATCH", "ELA_ANOMALY", "PDF_EDITOR_PRODUCER", "PDF_INCREMENTAL_UPDATE",
                 "BALANCE_MISMATCH", "AI_IMAGE_SUSPECTED", "MRZ_INVALID", "CNP_CHECKSUM_INVALID"}
RING_CODES = {"FRAUD_RING_SUSPECTED"}

ESCALATE_AT = 0.70  # de recalibrat pe benchmark: 0 fals pozitive pe dosarele legitime
REVIEW_AT = 0.35


def finding_weight(f: Finding) -> float:
    w = SEVERITY_WEIGHT[f.severity]
    return min(w, SOFT_SIGNALS[f.code]) if f.code in SOFT_SIGNALS else w


def score(results: list[AgentResult]) -> tuple[Verdict, list[Finding]]:
    findings = [f for r in results if r.agent != "compliance" for f in r.findings]
    incomplete = any(r.status == "error" for r in results if r.agent != "compliance")

    keep = 1.0
    for f in findings:
        keep *= 1 - finding_weight(f)
    risk = round(1 - keep, 4)

    codes = {f.code for f in findings}
    hard = codes & HARD_OVERRIDES
    if risk >= ESCALATE_AT or hard:
        recommendation = "escalate"
    elif risk >= REVIEW_AT or incomplete:
        recommendation = "review"
    else:
        recommendation = "clear"

    forged, ring = bool(codes & FORGERY_CODES), bool(codes & RING_CODES)
    if ring and forged:
        label = "identity_fraud"
    elif ring:
        label = "fraud_ring"
    elif forged and recommendation == "escalate":
        label = "forged"
    elif recommendation == "clear":
        label = "clean"
    else:
        label = "suspicious"

    top = sorted(findings, key=finding_weight, reverse=True)
    return Verdict(risk=risk, label=label, recommendation=recommendation, incomplete=incomplete,
                   summary=template_summary(top, recommendation, incomplete)), top


def template_summary(top: list[Finding], recommendation: str, incomplete: bool) -> str:
    """Rezumat fără LLM — folosit în mock și ca fallback."""
    action = {"escalate": "Recomandare: respingere și investigație de fraudă.",
              "review": "Recomandare: verificare manuală.",
              "clear": "Nicio problemă: dosarul poate merge la analiza normală de credit."}[recommendation]
    reasons = "; ".join(f.message for f in top[:3] if SEVERITY_WEIGHT[f.severity] > 0)
    note = " Atenție: un agent nu a terminat, verdictul e incomplet." if incomplete else ""
    return f"{reasons + '. ' if reasons else ''}{action}{note}"
