"""Clientul LLM unic al proiectului. Toți agenții apelează DOAR `chat(...)`.

Moduri (settings.llm_mode, schimbabil live din UI):
  bedrock — Claude pe AWS Bedrock (SDK Anthropic, client AsyncAnthropicBedrock)
  cloud   — Featherless (SDK openai, base_url)
  local   — Ollama (SDK openai, base_url local)
  mock    — doar răspunsuri din cache (data/llm_cache); fără internet, fără cost

Pentru bedrock/cloud, fiecare payload trece prin poarta anti-PII (core/pii_gate.py).
Fiecare apel extern ajunge în jurnalul de audit. Bedrock picat (cheie expirată) →
trece automat pe Featherless, dacă există cheie.

Exemplu:
    from app.core.llm import chat
    r = await chat("extract", case_id=case.id,
                   system="Extragi date din fluturași de salariu.",
                   prompt=redacted_text, json_schema=MySchema)
    r.data  # instanță MySchema validată
"""
import asyncio
import base64
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ValidationError

from app.config import REPO_ROOT, settings
from app.core import audit
from app.core.pii_gate import PIIGateBlocked, known_values, scan
from app.models import LLMUsage

log = logging.getLogger("orb.llm")

CACHE_DIR = REPO_ROOT / "data" / "llm_cache"

# Ce model folosește fiecare tip de sarcină
TASKS = {
    "extract": "fast",   # Funcționar: extragere din documente
    "arena": "fast",     # volum mare
    "summary": "reason", # Compliance: rezumat din dovezi
    "attack": "reason",  # (rezervat; Atacatorul e acum un fuzzer, fără LLM)
    "learn": "deep",     # self-learning: propunere de reguli
}

# USD per milion de tokeni (intrare, ieșire). Prețuri estimative; Bedrock poate diferi.
PRICES = {
    "haiku-5-5": (0.10, 0.50), "sonnet-5-5": (2.0, 10.0), "opus-5-5": (4.0, 20.0),
    "DeepSeek-V4-Flash": (0.14, 0.28), "Qwen3.8-Flash-Next": (0.15, 0.50),
}

_sem: asyncio.Semaphore | None = None
_clients: dict[str, Any] = {}


class LLMUnavailable(Exception):
    pass


@dataclass
class LLMResponse:
    text: str
    data: Any = None                     # instanța Pydantic validată, dacă s-a cerut json_schema
    usage: LLMUsage | None = None
    cached: bool = False
    meta: dict = field(default_factory=dict)


def model_for(task: str, mode: str) -> str:
    tier = TASKS.get(task, "reason")
    if mode == "bedrock":
        return {"fast": settings.bedrock_model_extract, "reason": settings.bedrock_model_reason,
                "deep": settings.bedrock_model_deep}[tier]
    if mode == "cloud":
        return settings.model_extract if tier == "fast" else settings.model_reason
    return settings.model_local or "qwen3.5:4b"


def _price(model: str, tin: int, tout: int) -> float:
    for key, (pi, po) in PRICES.items():
        if key in model:
            return round((tin * pi + tout * po) / 1_000_000, 6)
    return 0.0


# ── cache (demo offline + mock) ───────────────────────────────────────────────

def _cache_key(task: str, cache_key: str | None, system: str, prompt: str) -> str:
    base = f"{task}|{cache_key}" if cache_key else f"{task}|{system}|{prompt}"
    return hashlib.sha256(base.encode()).hexdigest()[:24]


def _cache_get(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _cache_put(key: str, text: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")


# ── furnizori ─────────────────────────────────────────────────────────────────

def _bedrock():
    if "bedrock" not in _clients:
        from anthropic import AsyncAnthropicBedrock
        _clients["bedrock"] = AsyncAnthropicBedrock(api_key=settings.aws_bearer_token_bedrock,
                                                    aws_region=settings.aws_region,
                                                    timeout=settings.llm_timeout_s, max_retries=2)
    return _clients["bedrock"]


def _openai(mode: str):
    if mode not in _clients:
        from openai import AsyncOpenAI
        if mode == "cloud":
            _clients[mode] = AsyncOpenAI(base_url="https://api.featherless.ai/v1",
                                         api_key=settings.featherless_api_key,
                                         timeout=settings.llm_timeout_s, max_retries=2)
        else:
            _clients[mode] = AsyncOpenAI(base_url=f"{settings.ollama_url}/v1", api_key="ollama",
                                         timeout=max(settings.llm_timeout_s, 90), max_retries=1)
    return _clients[mode]


async def _call_bedrock(model, system, prompt, images, max_tokens):
    content: list[dict] = [{"type": "image", "source": {"type": "base64", "media_type": mt,
                                                         "data": base64.b64encode(b).decode()}}
                           for b, mt in images]
    content.append({"type": "text", "text": prompt})
    r = await _bedrock().messages.create(model=model, max_tokens=max_tokens, system=system or [],
                                         messages=[{"role": "user", "content": content}])
    if r.stop_reason == "refusal":
        raise LLMUnavailable("modelul a refuzat cererea")
    text = "".join(b.text for b in r.content if b.type == "text")
    return text, r.usage.input_tokens, r.usage.output_tokens


async def _call_openai(mode, model, system, prompt, images, max_tokens,
                       json_mode: type[BaseModel] | None):
    user: list[dict] = [{"type": "image_url",
                         "image_url": {"url": f"data:{mt};base64,{base64.b64encode(b).decode()}"}}
                        for b, mt in images]
    user.append({"type": "text", "text": prompt})
    kwargs: dict = {"model": model, "max_tokens": max_tokens, "temperature": 0,
                    "messages": ([{"role": "system", "content": system}] if system else [])
                    + [{"role": "user", "content": user if images else prompt}]}
    if json_mode:
        if mode == "local" and isinstance(json_mode, type):
            # Ollama primește schema completă → decodare constrânsă. Fără ea, Qwen 4B copiază forma schemei
            # din prompt ({"properties": {"summary": ...}}) și validarea pică de două ori.
            kwargs["response_format"] = {"type": "json_schema", "json_schema": {
                "name": json_mode.__name__, "schema": json_mode.model_json_schema()}}
        else:
            kwargs["response_format"] = {"type": "json_object"}
    if mode == "local":
        kwargs["extra_body"] = {"options": {"num_ctx": 8192}, "think": False}
    r = await _openai(mode).chat.completions.create(**kwargs)
    u = r.usage
    return r.choices[0].message.content or "", (u.prompt_tokens if u else 0), (u.completion_tokens if u else 0)


# ── JSON ──────────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Any:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Featherless (DeepSeek-V4-Flash) întoarce obiectul fără „{” de început: ‹"camp": {...}, ...}›
        if text.startswith('"') and text.endswith("}"):
            try:
                return json.loads("{" + text)
            except json.JSONDecodeError:
                pass
        m = re.search(r"[\{\[].*[\}\]]", text, flags=re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def _schema_instruction(schema: type[BaseModel]) -> str:
    return ("\n\nReply ONLY with a valid JSON object, no other text, matching this JSON schema:\n"
            + json.dumps(schema.model_json_schema(), ensure_ascii=False))


# ── API public ────────────────────────────────────────────────────────────────

async def chat(task: str, *, prompt: str, system: str = "", case_id: str | None = None,
               json_schema: type[BaseModel] | None = None, images: list[tuple[bytes, str]] | None = None,
               images_redacted: bool = False, cache_key: str | None = None,
               max_tokens: int = 4000) -> LLMResponse:
    """Un apel LLM. `images` = [(bytes, "image/jpeg")]; pentru cloud trebuie `images_redacted=True`
    (imaginea a trecut prin Paznic). Imaginile de buletin nu se trimit niciodată în cloud."""
    global _sem
    _sem = _sem or asyncio.Semaphore(settings.llm_max_concurrency)
    images = images or []
    full_system = system + (_schema_instruction(json_schema) if json_schema else "")
    key = _cache_key(task, cache_key, full_system, prompt)
    mode = settings.llm_mode

    if mode == "mock" or settings.demo_cache:
        hit = _cache_get(key)
        if hit:
            return _finish(hit["text"], json_schema, LLMUsage(provider="cache", model="cache"), cached=True)
        if mode == "mock":
            raise LLMUnavailable(f"mock mode: no saved response for task '{task}'")

    if mode in ("bedrock", "cloud"):
        _gate(prompt + "\n" + full_system, images, images_redacted, case_id, mode)

    last_error: Exception | None = None
    for _attempt in range(2):  # a doua încercare: JSON invalid → retrimitem cu eroarea
        try:
            text, usage = await _dispatch(mode, task, full_system, prompt, images, max_tokens,
                                          json_mode=json_schema, case_id=case_id)
        except Exception as exc:
            if mode == "bedrock" and _is_auth_error(exc) and settings.featherless_api_key:
                log.warning("Bedrock indisponibil (%s) → trec pe Featherless", type(exc).__name__)
                audit.record(kind="llm", destination="bedrock", case_id=case_id, outcome="fallback_cloud")
                _gate(prompt + "\n" + full_system, images, images_redacted, case_id, "cloud")
                mode = "cloud"
                text, usage = await _dispatch(mode, task, full_system, prompt, images, max_tokens,
                                              json_mode=json_schema, case_id=case_id)
            else:
                raise LLMUnavailable(f"{mode}: {type(exc).__name__}") from exc
        try:
            resp = _finish(text, json_schema, usage)
            if settings.llm_record:
                _cache_put(key, text)
            return resp
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            prompt = (f"{prompt}\n\nYour previous reply was not valid JSON for the schema "
                      f"({type(exc).__name__}). Try again, JSON ONLY.")
    raise LLMUnavailable(f"invalid JSON after 2 attempts: {type(last_error).__name__}")


def _gate(text, images, images_redacted, case_id, mode):
    kinds = scan(text, case_id)
    if images and not images_redacted:
        kinds.append("IMAGINE_NEREDACTATA")
    if kinds:
        audit.record(kind="llm", destination=mode, case_id=case_id, outcome="blocked", detail={"pii_kinds": kinds})
        raise PIIGateBlocked(kinds)


async def _dispatch(mode, task, system, prompt, images, max_tokens, *, json_mode, case_id):
    model = model_for(task, mode)
    t0 = time.perf_counter()
    async with _sem:
        if mode == "bedrock":
            text, tin, tout = await _call_bedrock(model, system, prompt, images, max_tokens)
            provider = "bedrock"
        else:
            text, tin, tout = await _call_openai(mode, model, system, prompt, images, max_tokens, json_mode)
            provider = "featherless" if mode == "cloud" else "ollama"
    usage = LLMUsage(provider=provider, model=model, input_tokens=tin, output_tokens=tout,
                     cost_usd=_price(model, tin, tout) if mode != "local" else 0.0)
    if mode == "local":  # nu pleacă nicăieri, dar îl trecem în audit (altfel panoul ar arăta „0 apeluri AI”)
        audit.record(kind="llm", destination="ollama", case_id=case_id, outcome="local",
                     detail={"task": task, "model": model, "ms": int((time.perf_counter() - t0) * 1000)})
    else:
        audit.record(kind="llm", destination=provider, case_id=case_id, outcome="sent",
                     detail={"task": task, "model": model, "payload_hash": audit.payload_hash(system + prompt),
                             "images": len(images), "ms": int((time.perf_counter() - t0) * 1000),
                             # re-scanăm payload-ul EXACT trimis (nu presupunem): dacă vreodată e True, e un bug
                             "pii_detected": bool(scan(system + "\n" + prompt, case_id)),
                             "pii_values_checked": known_values(case_id)})
    return text, usage


def _finish(text, schema, usage, cached=False) -> LLMResponse:
    data = schema.model_validate(_extract_json(text)) if schema else None
    return LLMResponse(text=text, data=data, usage=usage, cached=cached)


def _is_auth_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    return status in (401, 403) or "expired" in str(exc).lower()
