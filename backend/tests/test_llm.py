import asyncio
import json

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
    assert "sonnet" in llm.model_for("learn", "bedrock")


def test_extract_json_recovers_object_without_opening_brace():
    # așa răspunde Featherless (DeepSeek-V4-Flash): obiectul fără „{” de început
    raw = '  "gross": 14200,\n  "net": {"v": 8500}\n}'
    assert llm._extract_json(raw) == {"gross": 14200, "net": {"v": 8500}}
    assert llm._extract_json('```json\n{"gross": 1}\n```') == {"gross": 1}
    with pytest.raises(json.JSONDecodeError):
        llm._extract_json('"doar text, nu JSON"}')


def _capture_openai_kwargs(monkeypatch) -> dict:
    seen: dict = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            seen.update(kwargs)
            msg = type("M", (), {"content": '{"gross": 1, "net": 1}'})
            return type("R", (), {"choices": [type("C", (), {"message": msg})], "usage": None})

    fake = type("Client", (), {"chat": type("Chat", (), {"completions": FakeCompletions()})})
    monkeypatch.setattr(llm, "_openai", lambda mode: fake)
    return seen


def test_local_mode_sends_full_json_schema_to_ollama(monkeypatch):
    # fără schema completă, Qwen 4B răspunde {"properties": {...}} și validarea pică
    seen = _capture_openai_kwargs(monkeypatch)
    run(llm._call_openai("local", "qwen3:4b-instruct", "sys", "p", [], 100, Payslip))
    fmt = seen["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["name"] == "Payslip"
    assert set(fmt["json_schema"]["schema"]["properties"]) == {"gross", "net"}


def test_cloud_mode_keeps_json_object(monkeypatch):
    seen = _capture_openai_kwargs(monkeypatch)
    run(llm._call_openai("cloud", "deepseek", "sys", "p", [], 100, Payslip))
    assert seen["response_format"] == {"type": "json_object"}
    seen.clear()
    run(llm._call_openai("local", "qwen3:4b-instruct", "sys", "p", [], 100, None))
    assert "response_format" not in seen
