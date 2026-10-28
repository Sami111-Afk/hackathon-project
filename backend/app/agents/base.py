"""Interfața comună pentru agenți. Vezi ARCHITECTURE.md §5.

Regulă: orice lucru CPU-intensiv (OCR, GLiNER, ELA, TenSEAL, randare PDF)
se rulează cu `await asyncio.to_thread(...)`, altfel îngheață SSE-ul.
"""
from typing import Protocol

from app.models import AgentResult, Case


class PipelineContext(Protocol):
    """Implementat de Samuel în core/pipeline.py: llm, emit(), db, settings, rezultate anterioare."""

    async def emit(self, type: str, message: str = "", data: dict | None = None) -> None: ...


class Agent(Protocol):
    name: str

    async def run(self, case: Case, ctx: PipelineContext) -> AgentResult: ...
