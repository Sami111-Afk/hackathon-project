"""⚖️ Compliance — Samuel. Scor determinist + dezbatere + rezumat.

Rezumatul LLM (când îl adăugăm) primește DOAR finding-urile, niciodată textul
documentelor (anti prompt injection). Până atunci: rezumat din șablon.
"""
from app.agents.compliance.scoring import score
from app.models import AgentResult, Finding

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
        verdict, _ = score(results)
        case.verdict = verdict
        code, severity, message = LABEL_FINDING[verdict.label]
        return AgentResult(agent="compliance", status="done", risk=verdict.risk,
                           findings=[Finding(code=code, severity=severity, message=message)])

    async def _debate(self, results, ctx) -> None:
        """Când agenții nu sunt de acord (unul vede risc mic, altul critic), o arătăm."""
        scored = [r for r in results if r.risk is not None and r.status == "done"]
        if len(scored) < 2:
            return
        low, high = min(scored, key=lambda r: r.risk), max(scored, key=lambda r: r.risk)
        if high.risk - low.risk >= 0.15:
            await ctx.emit("debate", f"{low.agent.capitalize()} vede risc {low.risk:.0%}, dar "
                           f"{high.agent.capitalize()} are dovezi de {high.risk:.0%} — cântăresc ambele.",
                           data={"low": low.agent, "high": high.agent})
