"""⚖️ Compliance — deterministic risk score + LLM summary (English summary below).

Deterministic risk level from the evidence (scoring.py). The LLM only writes the summary and receives ONLY
the findings, never the document text (prompt-injection safe). A summary quoting a number that is not in the
evidence is replaced by the template summary.
(RO: scor determinist; LLM-ul scrie doar rezumatul, din dovezi; un rezumat cu cifre nesusținute e înlocuit.)
"""
import logging

from pydantic import BaseModel, Field

from app.agents.compliance.scoring import score, unsupported_claims
from app.core.llm import chat
from app.models import AgentResult, Finding

log = logging.getLogger("orb.compliance")

SYSTEM = (
    "You are a bank's compliance officer. You receive ONLY the list of evidence found by the agents "
    "(code, severity, message), the risk score and the recommendation — already computed. You do NOT change them. "
    "Write, in ENGLISH, a summary of 2-3 sentences for the employee who decides: what was found, why it matters, "
    "what you recommend. No personal data, no speculation beyond the evidence, no scores or percentages. "
    "Labels like [X_1] stay labels. Do not mention technical details about the data source (e.g. \"demo registry\")."
)


class Summary(BaseModel):
    summary: str = Field(max_length=600)

LABEL_FINDING = {
    "identity_fraud": ("IDENTITY_FRAUD_LIKELY", "critical", "Likely identity theft, part of a ring"),
    "fraud_ring": ("FRAUD_RING_LINKED", "high", "The application is linked to a suspicious ring"),
    "forged": ("DOCUMENT_FORGERY_LIKELY", "high", "Documents likely forged"),
    "suspicious": ("NEEDS_REVIEW", "medium", "The application needs manual review"),
    "clean": ("NO_ISSUES", "info", "No issues found"),
}


def _band(risk: float) -> str:
    return "very high" if risk >= 0.85 else "high" if risk >= 0.70 else "medium" if risk >= 0.35 else "low"


AGENT_NAMES = {"paznic": "Guard", "functionar": "Clerk", "verificator": "Verifier", "detector": "Detector",
               "detectiv": "Detective", "compliance": "Compliance"}


class Compliance:
    name = "compliance"
    start_message = "Analyzing the evidence"

    async def run(self, case, ctx) -> AgentResult:
        results = list(ctx.results.values())
        await self._debate(results, ctx)
        verdict, top = score(results)
        usage = None
        try:
            evidence = "\n".join(f"- {f.code} [{f.severity}]: {f.message}" for f in top[:12]) or "- (no evidence)"
            r = await chat("summary", case_id=case.id, system=SYSTEM, json_schema=Summary, max_tokens=1500,
                           cache_key=f"summary|{case.id}" if case.id.startswith("case_maria") else None,
                           prompt=f"Risk level: {_band(verdict.risk)} (do not give percentages or scores). "
                                  f"Recommendation: {verdict.recommendation}. "
                                  f"Incomplete: {verdict.incomplete}.\nEvidence:\n{evidence}")
            usage = r.usage
            bad = unsupported_claims(r.data.summary, evidence, verdict.risk)
            if bad:  # rezumatul conține cifre/etichete care nu sunt în dovezi → nu-l arătăm
                log.warning("rezumat LLM respins: afirmații fără dovadă %s", bad)
                verdict.summary_source = "template_after_check"
                await ctx.emit("agent_progress",
                               "The AI summary contained a figure with no supporting evidence "
                               "— using the standard summary")
            else:
                verdict.summary, verdict.summary_source = r.data.summary, "llm"
        except Exception as exc:  # noqa: BLE001 — rezumatul din șablon rămâne
            log.info("rezumat din șablon (%s)", type(exc).__name__)
        case.verdict = verdict
        code, severity, message = LABEL_FINDING[verdict.label]
        return AgentResult(agent="compliance", status="done", risk=verdict.risk, llm_usage=usage,
                           findings=[Finding(code=code, severity=severity, message=message)])

    async def _debate(self, results, ctx) -> None:
        """Când agenții nu sunt de acord (unul vede risc mic, altul critic), o arătăm."""
        scored = [r for r in results if r.risk is not None and r.status == "done"]
        if len(scored) < 2:
            return
        low, high = min(scored, key=lambda r: r.risk), max(scored, key=lambda r: r.risk)
        if round(high.risk - low.risk, 6) >= 0.15:
            lo, hi = AGENT_NAMES.get(low.agent, low.agent), AGENT_NAMES.get(high.agent, high.agent)
            await ctx.emit("debate", f"{lo} sees {low.risk:.0%} risk, but {hi} has evidence at {high.risk:.0%} — "
                           "weighing both.",
                           data={"low": low.agent, "high": high.agent})
