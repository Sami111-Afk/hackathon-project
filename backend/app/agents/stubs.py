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
        if self.name == "functionar" and not any(d.extracted for d in case.documents):
            # dosarul primește documentele de probă, ca să aibă ce afișa
            fixture_docs = {d["type"]: d for d in _fixture()["documents"]}
            for doc in case.documents:
                src = fixture_docs.get(doc.type) or next(iter(fixture_docs.values()))
                doc.type = src["type"]
                doc.redacted_text = src.get("redacted_text")
                doc.extracted = {k: ExtractedValue(**v) for k, v in (src.get("extracted") or {}).items()}
                doc.pages = doc.pages or [PageInfo(**pg) for pg in src.get("pages", [])]
        return AgentResult.model_validate(raw)
