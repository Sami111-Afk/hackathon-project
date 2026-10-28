import asyncio

import pytest
from pydantic import BaseModel

from app.config import settings
from app.core import llm
from app.core.pii_gate import PIIGateBlocked, register_vault_values, scan


class Payslip(BaseModel):
    gross: int
    net: int


def run(coro):
    return asyncio.run(coro)


def test_gate_finds_identifiers_without_returning_values():
    hits = scan("CNP 2590312400011, IBAN RO49 RZBR 0000 0600 0000 1234, tel 0722 123 456", None)
    assert set(hits) == {"CNP", "IBAN", "TELEFON"}


def test_gate_finds_vault_values_normalized():
    register_vault_values("case_t1", ["Maria Ionescu", "Str. Florilor 12, Ploiești"])
    assert scan("solicitant: MARIA  IONESCU", "case_t1") == ["VALOARE_DIN_SEIF"]
    assert scan("str. florilor 12, ploiesti", "case_t1") == ["VALOARE_DIN_SEIF"]
    assert scan("solicitant: [PERSOANA_1]", "case_t1") == []


def test_cloud_call_blocked_before_leaving(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "bedrock")

    async def boom(*a, **k):
        raise AssertionError("nu trebuia să plece nimic")

    monkeypatch.setattr(llm, "_dispatch", boom)
    with pytest.raises(PIIGateBlocked):
        run(llm.chat("extract", prompt="CNP 2590312400011", case_id="case_x"))
    with pytest.raises(PIIGateBlocked):  # imagine neredactată
        run(llm.chat("extract", prompt="ok", images=[(b"\xff\xd8\xff", "image/jpeg")]))


def test_mock_uses_cache_and_validates_json(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "llm_mode", "mock")
    with pytest.raises(llm.LLMUnavailable):
        run(llm.chat("extract", prompt="x", cache_key="k1", json_schema=Payslip))
    key = llm._cache_key("extract", "k1", "", "")
    llm._cache_put(key, '```json\n{"gross": 14200, "net": 8500}\n```')
    r = run(llm.chat("extract", prompt="x", cache_key="k1", json_schema=Payslip))
    assert r.cached and r.data == Payslip(gross=14200, net=8500)


def test_invalid_json_retried_once(monkeypatch):
    monkeypatch.setattr(settings, "llm_mode", "local")
    answers = iter(["nu e json", '{"gross": 1, "net": 2}'])

    async def fake(mode, task, system, prompt, images, max_tokens, *, json_mode, case_id):
        return next(answers), None

    monkeypatch.setattr(llm, "_dispatch", fake)
    r = run(llm.chat("extract", prompt="x", json_schema=Payslip))
    assert r.data.net == 2


def test_task_routing():
    assert "haiku" in llm.model_for("extract", "bedrock")
    assert "sonnet" in llm.model_for("summary", "bedrock")
    assert "opus" in llm.model_for("learn", "bedrock")
