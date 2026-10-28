"""Dosarele: în memorie (rapid, pentru pipeline) + SQLite (persistă la fiecare agent terminat).

SQLite în mod WAL; scrierile rulează într-un thread, sub un lock
ca să nu blocheze event loop-ul.
"""
import asyncio
import sqlite3
import threading

from app.config import settings
from app.core.events import bus
from app.models import Case


def _db_path() -> str:
    url = settings.database_url
    return url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else ":memory:"


class CaseStore:
    def __init__(self) -> None:
        self._cases: dict[str, Case] = {}
        self._lock = threading.Lock()  # scrierile rulează în thread-uri
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            path = ":memory:" if settings.env == "test" else _db_path()
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, created_at TEXT, json TEXT)")
            for (raw,) in self._conn.execute("SELECT json FROM cases"):
                case = Case.model_validate_json(raw)
                if case.status in ("received", "processing"):
                    case.status = "error"  # serverul a repornit în timpul procesării
                self._cases[case.id] = case
                bus.continue_after_restart(case.id)
        return self._conn

    def load(self) -> None:
        self._connect()

    def get(self, case_id: str) -> Case | None:
        return self._cases.get(case_id)

    def list(self) -> list[Case]:
        return sorted(self._cases.values(), key=lambda c: c.created_at, reverse=True)

    async def save(self, case: Case) -> None:
        self._cases[case.id] = case
        payload = case.model_dump_json(exclude_none=True)
        await asyncio.to_thread(self._write, case.id, case.created_at, payload)

    def _write(self, case_id: str, created_at: str, payload: str) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO cases VALUES (?, ?, ?)", (case_id, created_at, payload))
            conn.commit()

    def delete(self, case_id: str) -> None:
        self._cases.pop(case_id, None)
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
            conn.commit()

    def reset(self) -> None:
        self._cases.clear()
        self._connect().execute("DELETE FROM cases")
        self._connect().commit()


store = CaseStore()
