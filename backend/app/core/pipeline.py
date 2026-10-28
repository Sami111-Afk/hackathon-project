"""Orchestratorul. Ordinea (ARCHITECTURE §2):

  paznic → functionar → [verificator ∥ detector ∥ detectiv] → compliance

Un agent care pică sau depășește timeout-ul nu oprește dosarul: primește
status "error" (mesaj generic + ID de corelare), iar Compliance marchează
verdictul ca "incomplet".
"""
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.events import bus
from app.core.files import render_pages, sniff
from app.core.llm import LLMUnavailable
from app.core.pii_gate import PIIGateBlocked
from app.core.store import store
from app.models import AgentResult, Case

log = logging.getLogger("orb.pipeline")

# secunde; OCR/GLiNER/LLM local pe CPU pot dura — ajustați dacă e nevoie
AGENT_TIMEOUT_S = {"paznic": 90, "functionar": 120, "verificator": 60, "detector": 60, "detectiv": 20,
                   "compliance": 60}
# dacă agentul din stânga pică, cei din dreapta nu au pe ce lucra → "skipped"
DEPENDS_ON = {"functionar": {"paznic"}, "verificator": {"functionar"}, "detectiv": {"paznic"}}
_running: set[asyncio.Task] = set()  # păstrăm referințe, altfel GC-ul poate opri task-urile


@dataclass
class PipelineContext:
    case: Case
    results: dict[str, AgentResult] = field(default_factory=dict)
    files: dict[str, bytes] = field(default_factory=dict)  # doc_id -> conținutul original (doar local)
    scratch: dict[str, Any] = field(default_factory=dict)   # date interne între agenți (nu ajung în API)
    _agent: str | None = None

    def mime(self, doc_id: str) -> str | None:
        """'image/jpeg' | 'image/png' | 'application/pdf' | None (fără fișier)."""
        data = self.files.get(doc_id)
        kind = sniff(data) if data else None
        return kind[1] if kind else None

    def pages(self, doc_id: str) -> list:
        """Paginile documentului ca imagini PIL (PDF randat o singură dată, apoi din cache)."""
        cache = self.scratch.setdefault("_pages", {})
        if doc_id not in cache:
            data = self.files.get(doc_id)
            cache[doc_id] = render_pages(data) if data else []
        return cache[doc_id]

    async def emit(self, type: str, message: str = "", data: dict | None = None, agent: str | None = None) -> None:
        bus.publish(self.case.id, type, agent=agent or self._agent, message=message, data=data)


async def _run_agent(name: str, ctx: PipelineContext) -> AgentResult:
    from app.agents.registry import AGENTS

    agent = AGENTS[name]
    failed = {d for d in DEPENDS_ON.get(name, set()) if ctx.results.get(d) and ctx.results[d].status != "done"}
    if failed:
        result = AgentResult(agent=name, status="skipped", error=f"sărit: {', '.join(sorted(failed))} nu a terminat")
        bus.publish(ctx.case.id, "agent_error", agent=name, message=result.error,
                    data=result.model_dump(exclude_none=True))
        ctx.results[name] = result
        ctx.case.results = [r for r in ctx.case.results if r.agent != name] + [result]
        await store.save(ctx.case)
        return result
    agent_ctx = PipelineContext(case=ctx.case, results=ctx.results, files=ctx.files, scratch=ctx.scratch, _agent=name)
    bus.publish(ctx.case.id, "agent_started", agent=name, message=getattr(agent, "start_message", ""))
    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(agent.run(ctx.case, agent_ctx), timeout=AGENT_TIMEOUT_S.get(name, 60))
        result.duration_ms = result.duration_ms or int((time.perf_counter() - t0) * 1000)
        ok = True
    except Exception as exc:
        corr = uuid.uuid4().hex[:8]
        log.exception("agent %s a picat (corelare %s)", name, corr)
        if isinstance(exc, asyncio.TimeoutError):
            kind = "timeout"
        elif isinstance(exc, PIIGateBlocked):
            kind = f"blocat de poarta anti-PII ({', '.join(exc.kinds)})"
        elif isinstance(exc, LLMUnavailable):
            kind = "AI indisponibil"
        else:
            kind = "eroare internă"
        result = AgentResult(agent=name, status="error", error=f"{kind} (ref {corr})",
                             duration_ms=int((time.perf_counter() - t0) * 1000))
        ok = False
    bus.publish(ctx.case.id, "agent_finished" if ok else "agent_error", agent=name,
                message=_summarize(result) if ok else result.error, data=result.model_dump(exclude_none=True))
    ctx.results[name] = result
    ctx.case.results = [r for r in ctx.case.results if r.agent != name] + [result]
    await store.save(ctx.case)
    return result


def _summarize(result: AgentResult) -> str:
    if not result.findings:
        return "Nicio problemă găsită"
    worst = max(result.findings, key=lambda f: ["info", "low", "medium", "high", "critical"].index(f.severity))
    return worst.message


MAX_CONCURRENT_CASES = 3
_case_sem: asyncio.Semaphore | None = None


async def run_pipeline(case: Case, files: dict[str, bytes] | None = None) -> Case:
    global _case_sem
    _case_sem = _case_sem or asyncio.Semaphore(MAX_CONCURRENT_CASES)
    async with _case_sem:
        return await _run(case, files)


async def _run(case: Case, files: dict[str, bytes] | None) -> Case:
    ctx = PipelineContext(case=case, files=files or {})
    case.status = "processing"
    await store.save(case)

    await _run_agent("paznic", ctx)
    await _run_agent("functionar", ctx)
    await asyncio.gather(*(_run_agent(n, ctx) for n in ("verificator", "detector", "detectiv")))
    await _run_agent("compliance", ctx)

    case.status = "awaiting_review"
    await store.save(case)
    if case.verdict:
        bus.publish(case.id, "verdict", agent="compliance", message=case.verdict.summary,
                    data=case.verdict.model_dump())
    return case


def start_pipeline(case: Case, files: dict[str, bytes] | None = None) -> asyncio.Task:
    task = asyncio.create_task(run_pipeline(case, files))
    _running.add(task)
    task.add_done_callback(_running.discard)
    return task
