"""Seiful (vault.db): valorile reale din spatele etichetelor, criptate cu VAULT_KEY (Fernet).

Fără endpoint public. Doar Paznicul scrie; restul pipeline-ului vede etichete și amprente.
La pornire, valorile se reîncarcă în poarta anti-PII, ca dosarele vechi să rămână protejate.
"""
import json
import sqlite3
import threading

from cryptography.fernet import Fernet

from app.config import settings
from app.core import pii_gate


def _db_path() -> str:
    url = settings.vault_database_url
    return url.removeprefix("sqlite:///") if url.startswith("sqlite:///") else ":memory:"


class Vault:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            path = ":memory:" if settings.env == "test" else _db_path()
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS vault (case_id TEXT, label TEXT, value BLOB, PRIMARY KEY (case_id, label))"
            )
        return self._conn

    def _fernet(self) -> Fernet:
        return Fernet(settings.vault_key.encode())

    def put(self, case_id: str, values: dict[str, list[str]]) -> None:
        """Rulează într-un thread (asyncio.to_thread): criptare + scriere SQLite."""
        f = self._fernet()
        rows = [(case_id, label, f.encrypt(json.dumps(vals, ensure_ascii=False).encode()))
                for label, vals in values.items()]
        with self._lock:
            conn = self._connect()
            conn.executemany("INSERT OR REPLACE INTO vault VALUES (?, ?, ?)", rows)
            conn.commit()
        pii_gate.register_vault_values(case_id, [v for vals in values.values() for v in vals])

    def get(self, case_id: str) -> dict[str, list[str]]:
        f = self._fernet()
        with self._lock:
            rows = self._connect().execute("SELECT label, value FROM vault WHERE case_id = ?", (case_id,)).fetchall()
        return {label: json.loads(f.decrypt(blob)) for label, blob in rows}

    def load_into_gate(self) -> None:
        """La pornirea serverului: poarta anti-PII cunoaște din nou valorile tuturor dosarelor."""
        with self._lock:
            case_ids = [r[0] for r in self._connect().execute("SELECT DISTINCT case_id FROM vault")]
        for case_id in case_ids:
            pii_gate.register_vault_values(case_id, [v for vals in self.get(case_id).values() for v in vals])

    def forget(self, case_id: str) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM vault WHERE case_id = ?", (case_id,))
            conn.commit()
        pii_gate.forget_case(case_id)

    def reset(self) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM vault")
            conn.commit()


vault = Vault()
