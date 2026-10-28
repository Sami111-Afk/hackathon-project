"""Magistrala de evenimente: istoric în memorie per dosar + abonați live (SSE).

Fiecare dosar are propriul `seq` crescător. Un client care se reconectează cu
Last-Event-ID primește tot ce a ratat (replay), apoi evenimentele noi.
Stream-ul global trimite doar ID-uri și stări, fără conținut (vezi ARCHITECTURE §3).
"""
import asyncio
from collections import defaultdict
from datetime import UTC, datetime

from app.models import PipelineEvent

GLOBAL_TYPES = {"case_created", "agent_started", "agent_finished", "agent_error", "verdict", "decision"}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class EventBus:
    def __init__(self) -> None:
        self._history: dict[str, list[PipelineEvent]] = defaultdict(list)
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._global_subs: set[asyncio.Queue] = set()

    def publish(self, case_id: str, type: str, *, agent: str | None = None,
                message: str = "", data: dict | None = None) -> PipelineEvent:
        history = self._history[case_id]
        event = PipelineEvent(case_id=case_id, seq=len(history), ts=now_iso(),
                              type=type, agent=agent, message=message, data=data)
        history.append(event)
        for q in list(self._subs[case_id]):
            q.put_nowait(event)
        if type in GLOBAL_TYPES:
            slim = event.model_copy(update={"data": None, "message": ""})
            for q in list(self._global_subs):
                q.put_nowait(slim)
        return event

    def history(self, case_id: str, after_seq: int = -1) -> list[PipelineEvent]:
        return [e for e in self._history.get(case_id, []) if e.seq > after_seq]

    def subscribe(self, case_id: str | None = None) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        (self._global_subs if case_id is None else self._subs[case_id]).add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue, case_id: str | None = None) -> None:
        (self._global_subs if case_id is None else self._subs[case_id]).discard(q)

    def reset(self) -> None:
        self._history.clear()


bus = EventBus()
