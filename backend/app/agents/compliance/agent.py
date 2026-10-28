"""⚖️ Compliance — Samuel. Scor determinist + dezbatere + rezumat.

Rezumatul LLM (când îl adăugăm) primește DOAR finding-urile, niciodată textul
documentelor (anti prompt injection). Până atunci: rezumat din șablon.
"""
import logging

from pydantic import BaseModel, Field

from app.agents.compliance.scoring import score
from app.core.llm import chat
from app.models import AgentResult, Finding

log = logging.getLogger("orb.compliance")

SYSTEM = (
    "Ești ofițerul de conformitate al unei bănci. Primești DOAR lista de dovezi găsite de agenți "
    "(cod, gravitate, mesaj), scorul de risc și recomandarea — deja calculate. NU le schimbi. "
    "Scrii în română un rezumat de 2–3 propoziții pentru angajatul care decide: ce s-a găsit, de ce contează, "
    "ce recomanzi. Fără date personale, fără speculații dincolo de dovezi. Etichetele [X_1] rămân etichete."
)


class Summary(BaseModel):
    summary: str = Field(max_length=600)

LABEL_FINDING = {
    "identity_fraud": ("IDENTITY_FRAUD_LIKELY", "critical", "Furt de identitate probabil, parte dintr-o rețea"),
    "fraud_ring": ("FRAUD_RING_LINKED", "high", "Dosarul e legat de o rețea suspectă"),
    "forged": ("DOCUMENT_FORGERY_LIKELY", "high", "Documente probabil falsificate"),
    "suspicious": ("NEEDS_REVIEW", "medium", "Dosarul necesită verificare manuală"),
    "clean": ("NO_ISSUES", "info", "Nicio problemă găsită"),
}


class Compliance:
    name = "compliance"
    start_message = "Analizez dovezile"

    async def run(self, case, ctx) -> AgentResult:
        results = list(ctx.results.values())
        await self._debate(results, ctx)
        verdict, top = score(results)
        usage = None
        try:
            evidence = "\n".join(f"- {f.code} [{f.severity}]: {f.message}" for f in top[:12]) or "- (nicio dovadă)"
            r = await chat("summary", case_id=case.id, system=SYSTEM, json_schema=Summary, max_tokens=1500,
                           cache_key=f"summary|{case.id}" if case.id.startswith("case_maria") else None,
                           prompt=f"Scor de risc: {verdict.risk:.2f}. Recomandare: {verdict.recommendation}. "
                                  f"Incomplet: {verdict.incomplete}.\nDovezi:\n{evidence}")
            verdict.summary, usage = r.data.summary, r.usage
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
            await ctx.emit("debate", f"{low.agent.capitalize()} vede risc {low.risk:.0%}, dar "
                           f"{high.agent.capitalize()} are dovezi de {high.risk:.0%} — cântăresc ambele.",
                           data={"low": low.agent, "high": high.agent})
