"""Magistrala de evenimente: istoric în memorie per dosar + abonați live (SSE).

Fiecare dosar are propriul `seq` crescător. Un client care se reconectează cu
Last-Event-ID primește tot ce a ratat (replay), apoi evenimentele noi.
Stream-ul global trimite doar ID-uri și stări, fără conținut (vezi ARCHITECTURE §3).
"""
import asyncio
import threading
from collections import defaultdict
from datetime import UTC, datetime

from app.models import PipelineEvent

QUEUE_MAX = 500           # client lent → pierde cele mai vechi evenimente, nu umple memoria
RESTART_SEQ_OFFSET = 100_000

GLOBAL_TYPES = {"case_created", "agent_started", "agent_finished", "agent_error", "verdict", "decision"}


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class EventBus:
    def __init__(self) -> None:
        self._history: dict[str, list[PipelineEvent]] = defaultdict(list)
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._global_subs: set[asyncio.Queue] = set()
        self._offset: dict[str, int] = {}
        self._lock = threading.RLock()

    def continue_after_restart(self, case_id: str) -> None:
        """Istoria nu supraviețuiește restartului; noile evenimente primesc seq mare,
        ca un client cu Last-Event-ID vechi să nu le ignore."""
        self._offset[case_id] = RESTART_SEQ_OFFSET

    def publish(self, case_id: str, type: str, *, agent: str | None = None,
                message: str = "", data: dict | None = None) -> PipelineEvent:
        with self._lock:
            return self._publish(case_id, type, agent, message, data)

    def _publish(self, case_id, type, agent, message, data) -> PipelineEvent:
        history = self._history[case_id]
        seq = self._offset.get(case_id, 0) + len(history)
        event = PipelineEvent(case_id=case_id, seq=seq, ts=now_iso(),
                              type=type, agent=agent, message=message, data=data)
        history.append(event)
        for q in list(self._subs[case_id]):
            _offer(q, event)
        if type in GLOBAL_TYPES:
            slim = event.model_copy(update={"data": None, "message": ""})
            for q in list(self._global_subs):
                _offer(q, slim)
        return event

    def history(self, case_id: str, after_seq: int = -1) -> list[PipelineEvent]:
        return [e for e in self._history.get(case_id, []) if e.seq > after_seq]

    def subscribe(self, case_id: str | None = None) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAX)
        q._orb_loop = asyncio.get_running_loop()  # type: ignore[attr-defined]
        (self._global_subs if case_id is None else self._subs[case_id]).add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue, case_id: str | None = None) -> None:
        if case_id is None:
            self._global_subs.discard(q)
        else:
            self._subs[case_id].discard(q)
            if not self._subs[case_id]:
                del self._subs[case_id]

    def trim(self, case_id: str, keep: int) -> None:
        h = self._history.get(case_id)
        if h and len(h) > keep:
            drop = len(h) - keep
            self._offset[case_id] = self._offset.get(case_id, 0) + drop
            del h[:drop]

    def reset(self) -> None:
        self._history.clear()
        self._offset.clear()


def _offer(q: asyncio.Queue, event: PipelineEvent) -> None:
    def put() -> None:
        if q.full():
            q.get_nowait()
        q.put_nowait(event)

    loop = getattr(q, "_orb_loop", None)
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    if loop is not None and loop is not running:
        loop.call_soon_threadsafe(put)  # publicat dintr-un thread → livrăm pe loop-ul abonatului
    else:
        put()


bus = EventBus()
