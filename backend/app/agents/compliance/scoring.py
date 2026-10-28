"""Scorul de risc al Compliance — determinist, LLM-ul nu îl decide (ARCHITECTURE §5).

risk = 1 − Π(1 − wᵢ)   (noisy-OR pe ponderile finding-urilor)
- semnalele slabe (ELA, AI-detector) sunt plafonate
- override-urile dure împing recomandarea minim la "escalate"
"""
import re

from app.models import AgentResult, Finding, ScoreItem, Verdict

SEVERITY_WEIGHT = {"info": 0.0, "low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.85}

SOFT_SIGNALS = {"ELA_ANOMALY": 0.3, "AI_IMAGE_SUSPECTED": 0.3, "EXIF_EDITOR": 0.2}

# MRZ_INVALID nu e override: pe o poză de telefon, OCR-ul strică ușor cifrele de control din MRZ
# (benchmark: un buletin cinstit escaladat doar din asta). Rămâne dovadă „ridicată” → minim verificare umană.
HARD_OVERRIDES = {"CNP_CHECKSUM_INVALID", "COMPANY_INACTIVE", "COMPANY_NOT_FOUND",
                  "PROMPT_INJECTION_SUSPECTED"}

FORGERY_CODES = {"NET_MISMATCH", "ELA_ANOMALY", "PDF_EDITOR_PRODUCER", "PDF_INCREMENTAL_UPDATE",
                 "BALANCE_MISMATCH", "AI_IMAGE_SUSPECTED", "MRZ_INVALID", "CNP_CHECKSUM_INVALID"}
RING_CODES = {"FRAUD_RING_SUSPECTED", "SHARED_IBAN"}
# PII_GATE_BLOCKED: poarta și-a făcut treaba (n-a plecat nimic în cloud) — nu e o dovadă împotriva clientului,
# dar AI-ul n-a putut citi tot → un om verifică (benchmark cu Bedrock: 2/12 cinstiți escaladați doar din asta).
REVIEW_OVERRIDES = {"OCR_LOW_QUALITY", "MRZ_INVALID", "PII_GATE_BLOCKED"}  # nu acuză pe nimeni; un om se uită

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
    soft_strong = any(f.code in SOFT_SIGNALS and SEVERITY_WEIGHT[f.severity] >= 0.3 for f in findings)
    if risk >= ESCALATE_AT or hard:
        recommendation = "escalate"
    elif risk >= REVIEW_AT or incomplete or soft_strong or codes & REVIEW_OVERRIDES:
        recommendation = "review"
    else:
        recommendation = "clear"

    forged, ring = bool(codes & FORGERY_CODES), bool(codes & RING_CODES)
    if recommendation == "clear":
        label = "clean"
    elif recommendation == "review":
        label = "suspicious"
    elif ring and forged:
        label = "identity_fraud"
    elif ring:
        label = "fraud_ring"
    elif forged:
        label = "forged"
    else:
        label = "suspicious"

    top = sorted(findings, key=finding_weight, reverse=True)
    breakdown = [ScoreItem(code=f.code, severity=f.severity, weight=finding_weight(f), message=f.message,
                           hard_override=f.code in HARD_OVERRIDES) for f in top if finding_weight(f) > 0]
    return Verdict(risk=risk, label=label, recommendation=recommendation, incomplete=incomplete,
                   breakdown=breakdown, summary=template_summary(top, recommendation, incomplete)), top


def template_summary(top: list[Finding], recommendation: str, incomplete: bool) -> str:
    """Rezumat fără LLM — folosit în mock și ca fallback."""
    action = {"escalate": "Recommendation: reject and open a fraud investigation.",
              "review": "Recommendation: manual review.",
              "clear": "No issues: the application can proceed to normal credit analysis."}[recommendation]
    reasons = "; ".join(f.message for f in top[:3] if SEVERITY_WEIGHT[f.severity] > 0)
    note = " Warning: an agent did not finish, the verdict is incomplete." if incomplete else ""
    return f"{reasons + '. ' if reasons else ''}{action}{note}"


_NUM = re.compile(r"\d[\d.,]*\d|\d")
_LABEL = re.compile(r"\[[A-Z_]+_\d+\]")


def _digits(text: str) -> set[str]:
    return {re.sub(r"\D", "", m).lstrip("0") or "0" for m in _NUM.findall(text)}


def unsupported_claims(summary: str, evidence: str, risk: float) -> list[str]:
    """Cifrele și etichetele din rezumatul LLM care NU apar în dovezi = halucinații. Gol = rezumat fidel."""
    allowed = _digits(evidence) | {str(round(risk * 100)), str(round(risk * 1000)), str(round(risk * 100, 1)),
                                  str(round(risk, 2)).replace("0.", "").lstrip("0") or "0"}
    allowed |= {str(i) for i in range(0, 11)}  # „2–3 propoziții”, „5 cereri” — numere mici, inofensive
    bad = [n for n in _digits(summary) if n not in allowed]
    bad += [lab for lab in _LABEL.findall(summary) if lab not in evidence]
    return bad
