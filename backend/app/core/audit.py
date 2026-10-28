"""Jurnalul de audit: fiecare apel extern (LLM cloud, ANAF) și fiecare blocare a porții anti-PII.

Nu scriem conținutul trimis, doar hash-ul lui, destinația și rezultatul.
"""
import hashlib
import json
import threading
from collections import deque

from app.core.events import now_iso
from app.core.store import store

_lock = threading.Lock()
_recent: deque = deque(maxlen=2000)


def payload_hash(payload) -> str:
    raw = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def record(*, kind: str, destination: str, case_id: str | None, outcome: str, detail: dict | None = None) -> dict:
    entry = {"ts": now_iso(), "kind": kind, "destination": destination, "case_id": case_id,
             "outcome": outcome, **(detail or {})}
    with _lock:
        _recent.append(entry)
        conn = store._connect()
        conn.execute("CREATE TABLE IF NOT EXISTS audit_log (ts TEXT, json TEXT)")
        conn.execute("INSERT INTO audit_log VALUES (?, ?)", (entry["ts"], json.dumps(entry, ensure_ascii=False)))
        conn.commit()
    return entry


def recent(limit: int = 200) -> list[dict]:
    return list(_recent)[-limit:][::-1]


def external_calls_with_pii() -> int:
    """Pentru dashboard: câte apeluri au plecat cu date personale. Trebuie să fie 0."""
    return sum(1 for e in _recent if e["kind"] == "llm" and e["outcome"] == "sent" and e.get("pii_detected"))


def reset() -> None:
    _recent.clear()
