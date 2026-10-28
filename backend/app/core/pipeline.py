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
from app.core.store import store
from app.models import AgentResult, Case

log = logging.getLogger("orb.pipeline")

AGENT_TIMEOUT_S = 30
_running: set[asyncio.Task] = set()  # păstrăm referințe, altfel GC-ul poate opri task-urile


@dataclass
class PipelineContext:
    case: Case
    results: dict[str, AgentResult] = field(default_factory=dict)
    files: dict[str, bytes] = field(default_factory=dict)  # doc_id -> conținutul original (doar local)
    scratch: dict[str, Any] = field(default_factory=dict)   # date interne între agenți (nu ajung în API)
    _agent: str | None = None

    async def emit(self, type: str, message: str = "", data: dict | None = None, agent: str | None = None) -> None:
        bus.publish(self.case.id, type, agent=agent or self._agent, message=message, data=data)


async def _run_agent(name: str, ctx: PipelineContext) -> AgentResult:
    from app.agents.registry import AGENTS

    agent = AGENTS[name]
    agent_ctx = PipelineContext(case=ctx.case, results=ctx.results, files=ctx.files, scratch=ctx.scratch, _agent=name)
    bus.publish(ctx.case.id, "agent_started", agent=name, message=getattr(agent, "start_message", ""))
    t0 = time.perf_counter()
    try:
        result = await asyncio.wait_for(agent.run(ctx.case, agent_ctx), timeout=AGENT_TIMEOUT_S)
        result.duration_ms = result.duration_ms or int((time.perf_counter() - t0) * 1000)
        bus.publish(ctx.case.id, "agent_finished", agent=name, message=_summarize(result),
                    data=result.model_dump(exclude_none=True))
    except Exception as exc:
        corr = uuid.uuid4().hex[:8]
        log.exception("agent %s a picat (corelare %s)", name, corr)
        kind = "timeout" if isinstance(exc, asyncio.TimeoutError) else "eroare internă"
        result = AgentResult(agent=name, status="error", error=f"{kind} (ref {corr})",
                             duration_ms=int((time.perf_counter() - t0) * 1000))
        bus.publish(ctx.case.id, "agent_error", agent=name, message=result.error,
                    data=result.model_dump(exclude_none=True))
    ctx.results[name] = result
    ctx.case.results = [r for r in ctx.case.results if r.agent != name] + [result]
    await store.save(ctx.case)
    return result


def _summarize(result: AgentResult) -> str:
    if not result.findings:
        return "Nicio problemă găsită"
    worst = max(result.findings, key=lambda f: ["info", "low", "medium", "high", "critical"].index(f.severity))
    return worst.message


async def run_pipeline(case: Case, files: dict[str, bytes] | None = None) -> Case:
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
