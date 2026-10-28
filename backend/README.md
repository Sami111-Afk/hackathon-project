# Backend ORB — ghid rapid pentru colegi

## Pornire
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements-core.txt
uvicorn app.main:app --reload --reload-dir app --port 8000
pytest -q          # trebuie să treacă înainte de merge
```
Dosarul Mariei, oricând: `curl -X POST -H "Authorization: Bearer $BANK_UI_TOKEN" localhost:8000/api/admin/rerun-demo`

## Cum îți conectezi agentul
1. Scrii clasa în folderul tău (ex. `app/agents/paznic/agent.py`):
```python
from app.models import AgentResult, Finding, Evidence

class Paznic:
    name = "paznic"
    start_message = "Ascund datele personale"

    async def run(self, case, ctx) -> AgentResult:
        data = ctx.files.get("doc_1")                     # bytes originale (doar local)
        text = await asyncio.to_thread(ocr, data)         # tot ce e CPU-intensiv → to_thread!
        await ctx.emit("agent_progress", "OCR gata")      # opțional, apare live în UI
        ctx.scratch["ocr"] = ...                          # date pentru agenții următori (nu ajung în API)
        return AgentResult(agent="paznic", status="done", findings=[...])
```
2. În `app/agents/registry.py` înlocuiești `StubAgent(...)` de pe linia ta cu `Paznic()`.
3. Excepțiile nu blochează dosarul: agentul tău apare cu `status: "error"`, verdictul devine „incomplet”.

## Cum apelezi AI-ul — doar prin `chat()`
```python
from pydantic import BaseModel
from app.core.llm import chat, LLMUnavailable
from app.core.pii_gate import PIIGateBlocked

class Fluturas(BaseModel):
    gross_salary: str
    net_salary: str

r = await chat("extract", case_id=case.id, system="...", prompt=text_redactat, json_schema=Fluturas)
r.data.net_salary   # validat
```
- **Sarcini → modele** (`TASKS` în `core/llm.py`): `extract`/`arena` → Haiku 5.5, `summary`/`attack` → Sonnet 5.5, `learn` → Opus 5.5 (pe Bedrock).
- **Moduri:** `LLM_MODE=bedrock|cloud|local|mock`, schimbabil live prin `POST /api/settings`. Bedrock picat (cheie expirată) → trece singur pe Featherless.
- **Poarta anti-PII:** în bedrock/cloud, orice CNP/IBAN/telefon/email sau valoare din seif în payload → `PIIGateBlocked`, nimic nu pleacă. Paznicul înregistrează valorile cu `pii_gate.register_vault_values(case_id, [...])`.
- **Imagini:** `images=[(bytes, "image/jpeg")]`; în cloud doar cu `images_redacted=True`. Buletine — niciodată.
- **Demo offline:** `LLM_RECORD=true` salvează răspunsurile în `data/llm_cache/`; `DEMO_CACHE=true` sau `LLM_MODE=mock` le redă.
- Fiecare apel extern intră în jurnalul de audit (`GET /api/audit`).

## API (rute „bancă” cer `Authorization: Bearer <BANK_UI_TOKEN>`)
`POST /api/cases` · `GET /api/cases` · `GET /api/cases/{id}` · `GET /api/cases/{id}/events` (SSE) · `GET /api/cases/{id}/documents/{doc}/image` · `POST /api/cases/{id}/decision` · `GET /api/events` · `GET|POST /api/settings` · `GET /api/dashboard/stats` · `GET /api/audit` · `POST /api/admin/rerun-demo` · `POST /api/admin/reset`
