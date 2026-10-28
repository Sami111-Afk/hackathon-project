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
import asyncio
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
   Dacă Paznicul pică, Funcționarul/Verificatorul/Detectivul sunt „skipped” (n-au pe ce lucra).

### Cine scrie ce (ca să nu vă călcați pe câmpuri)
| Agent | Scrie în `case` | Lasă în `ctx.scratch` |
|---|---|---|
| Paznic | `doc.pages` (cu width/height!), `doc.redacted_text`, `case.fingerprints` (`phone`/`iban`/`cnp`/`address` → `hm_...`); apelează `pii_gate.register_vault_values(case.id, [...])`; imaginea redactată cu `files.save_derived(case.id, doc.id, "redacted", page, png)` | `scratch["ocr"][doc_id]`, `scratch["bboxes"][doc_id]` |
| Funcționar | `doc.type`, `doc.extracted` | — |
| Verificator / Detector / Detectiv | nimic în `case` — doar `AgentResult` (rulează în paralel!) | Detector: `files.save_derived(..., "ela", ...)` |
| Compliance | `case.verdict` | — |

Scrieți în `case` doar din corutină, niciodată din `asyncio.to_thread`.

### Ce îți dă `ctx`
- `ctx.files[doc_id]` — bytes originale; `ctx.mime(doc_id)` — `image/jpeg|image/png|application/pdf`
- `ctx.pages(doc_id)` — paginile ca imagini PIL (PDF randat o dată, partajat între agenți)
- `ctx.results` — rezultatele agenților anteriori; `await ctx.emit("agent_progress", "mesaj")`
- Timeout per agent: `AGENT_TIMEOUT_S` în `core/pipeline.py` (Paznic 90 s, Funcționar 120 s …)

### Testare cu documentele Mariei
`POST /api/admin/rerun-demo` trimite prin pipeline **fișierele reale** din `data/demo/maria/` (ca un upload).
Agenții tăi primesc deci un JPEG de buletin, un JPEG de fluturaș și un PDF de extras. Adevărul e în `truth.json`.

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
- **Sarcini → modele** (`TASKS` în `core/llm.py`): `extract`/`arena` → Haiku 5.5, `summary` → Sonnet 5.5, `learn` → Sonnet 5.5 (pe Bedrock).
- **Moduri:** `LLM_MODE=bedrock|cloud|local|mock`, schimbabil live prin `POST /api/settings`. Bedrock picat (cheie expirată) → trece singur pe Featherless.
- **Poarta anti-PII:** în bedrock/cloud, orice CNP/IBAN/telefon/email sau valoare din seif în payload → `PIIGateBlocked`, nimic nu pleacă. Paznicul înregistrează valorile cu `pii_gate.register_vault_values(case_id, [...])`.
- **Imagini:** `images=[(bytes, "image/jpeg")]`; în cloud doar cu `images_redacted=True`. Buletine — niciodată.
- **Demo offline:** `LLM_RECORD=true` salvează răspunsurile în `data/llm_cache/`; `DEMO_CACHE=true` sau `LLM_MODE=mock` le redă.
- Fiecare apel extern intră în jurnalul de audit (`GET /api/audit`).

## API (rute „bancă” cer `Authorization: Bearer <BANK_UI_TOKEN>`)
`POST /api/admin/seed-demo` (rețeaua + 10 dosare legitime, pentru dashboard și graf) · `POST /api/admin/seed-arena` (clasament pre-populat) · `POST /api/cases` · `GET /api/cases` · `GET /api/cases/{id}` · `GET /api/cases/{id}/events` (SSE) · `GET /api/cases/{id}/report` (raport de anchetă HTML → „Salvează ca PDF”) · `GET /api/cases/{id}/documents/{doc}/image?view=original|redacted|ela&page=N` (PDF → PNG) · `POST /api/cases/{id}/decision` · `GET /api/events` · `GET|POST /api/settings` · `GET /api/dashboard/stats` · `GET /api/audit` · `POST /api/admin/rerun-demo` · `POST /api/admin/reset`

## Arena (PUBLICĂ, fără token) — pentru Erin
- `GET /api/arena/missions` — misiunile: `template` (fluturașul de pornire), `editable` (câmpurile de pus în formular: number/select/date), `tricks` (bife), `target`.
- `POST /api/arena/submissions` `{nickname, mission_id, edits: {câmp: valoare}, tricks: [..]}` → `{id, outcome: passed|caught|invalid, points, reasons[], caught_by[], duplicate}`. Limită: 5/minut/IP (429).
- `GET /api/arena/submissions/{id}/image` — falsul generat (JPEG), de arătat jucătorului.
- `GET /api/arena/leaderboard` — `{top, feed, stats}`; `GET /api/arena/live` — SSE pentru proiector (`arena_scored`, `rule_proposed`, `rule_approved`).

## Self-learning (rute „bancă”)
- Un fals care trece în Arena → Claude Sonnet propune reguli în fundal → backtest automat (respinsă dacă nu prinde falsul sau prinde fluturași legitimi).
- `GET /api/rules` · `POST /api/rules/{id}/approve|reject` `{decided_by}` · `POST /api/rules/learn/{submission_id}` (pornire manuală, util la demo).
- Regulile sunt JSON evaluat de `app/learning/engine.py` — LLM-ul nu scrie cod.
- Arena folosește deocamdată un arbitru provizoriu (`app/arena/judge.py`) cu aceleași verificări ca Verificatorul; trece pe pipeline-ul complet când agenții reali sunt gata.

## Atacatorul (fuzzer, fără LLM)
`POST /api/admin/attacker/start` `{rounds, mission_id, auto_approve}` · `GET /api/admin/attacker/status`.
Încearcă falsuri în Arena și se adaptează după motivele pentru care e prins; când trece, self-learning-ul propune reguli.
`auto_approve: true` doar pentru demo. (Un LLM a refuzat rolul de falsificator — de aceea e algoritmic.)

## Documentele Mariei (versiune brută — Lorena le rafinează)
`python -m data.generator.build_demo` (din rădăcina repo-ului) → `data/demo/maria/`: `buletin.jpg`, `fluturas.jpg`,
`extras.pdf`, `truth.json` (ce e fals + toate valorile PII, pentru benchmark). Identificatorii: `data/generator/ro_ids.py`.
