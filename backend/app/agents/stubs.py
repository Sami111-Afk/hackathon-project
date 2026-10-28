"""Agenți de probă: redau rezultatele din shared/fixtures/maria_case.json.

Așa pipeline-ul, SSE-ul și frontend-ul merg cap-coadă înainte ca agenții
reali să fie gata. Un agent real îl înlocuiește în agents/registry.py.
"""
import asyncio
import json
from functools import lru_cache
from pathlib import Path

from app.config import REPO_ROOT, settings
from app.models import AgentResult, Case, ExtractedValue, PageInfo

FIXTURE = REPO_ROOT / "shared" / "fixtures" / "maria_case.json"


@lru_cache
def _fixture() -> dict:
    return json.loads(Path(FIXTURE).read_text(encoding="utf-8"))


class StubAgent:
    def __init__(self, name: str, start_message: str, delay: float = 1.0) -> None:
        self.name = name
        self.start_message = start_message
        self.delay = delay

    async def run(self, case: Case, ctx) -> AgentResult:
        await asyncio.sleep(0 if settings.env == "test" else self.delay)
        raw = next(r for r in _fixture()["results"] if r["agent"] == self.name)
        fixture_docs = _fixture()["documents"]
        for i, doc in enumerate(case.documents):  # pe poziție: doc_1 ↔ primul document din fixture
            src = fixture_docs[i % len(fixture_docs)]
            if self.name == "paznic":  # Paznicul scrie: pages, redacted_text, fingerprints
                doc.pages = doc.pages or [PageInfo(**pg) for pg in src.get("pages", [])]
                doc.redacted_text = doc.redacted_text or src.get("redacted_text")
            elif self.name == "functionar":  # Funcționarul scrie: type, extracted
                doc.type = src["type"] if doc.type == "unknown" else doc.type
                extracted = src.get("extracted") or {}
                doc.extracted = doc.extracted or {k: ExtractedValue(**v) for k, v in extracted.items()}
        if self.name == "paznic" and not case.fingerprints:
            case.fingerprints = _fixture()["fingerprints"]
        return AgentResult.model_validate(raw)
