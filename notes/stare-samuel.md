# Stare proiect + context pentru continuare (Samuel)

Scris 2026-10-28 ~13:30, înainte de /compact. Hackathon Raiffeisen „Operational Efficiency”, 24h, început ~08:00.
Repo: https://github.com/Sami111-Afk/hackathon-project (privat). Local: `/home/sol/Projects/hackathon-project`.
Echipa: Samuel (eu, backend/orchestrare), Narcis (simighost: Paznic, Detector, deploy/ngrok, Ollama),
Stefan (Stefannasd: Funcționar, Verificator, ANAF, HE), Erin (erinlud: frontend, Detectiv), Lorena (Loricu: date, ZK).

## Reguli de lucru (de respectat)
- **Fără „Co-Authored-By: Claude” sau orice mențiune Claude în commit-uri/PR-uri** (cerința lui Samuel, și în memorie).
  10 commit-uri vechi ale colegilor au mențiunea → de curățat istoricul LA FINAL (după 18:00), cu acordul lui Samuel.
- **Doar date inventate**: CNP-uri cu număr de ordine `000`, IBAN `RO59RZBR9999000000000001` (sucursală 9999),
  CUI-uri verificate la ANAF că NU există: RO9185472906 (Tehnoserv), RO9341910290 (Bitwave), RO9402119372 (Agro Prahova = firma Mariei),
  RO9477321003 (Nordic). Maria: CNP 2590312290006, buletin PH 481925, adresă Str. Florilor nr. 12, Ploiești.
- Frontend-ul îl face Erin (nu-l atingem); colegii primesc observații în `notes/<nume>.md`.
- **Fiecare PR nou → agent de verificare automat** (Sonnet), apoi merge dacă e ok; observațiile mici merg în notes.
- Ascultător pe PR-uri: Monitor bash care rulează `gh pr list` + `git ls-remote` la 45s, expiră la 30 min → re-armat.
- Pe laptopul lui Samuel: Python 3.14 (CI e pe 3.11), Tesseract `ron` instalat, TenSEAL instalat în `backend/.venv`.
- Atenție: NU `pkill -f` (a omorât shell-ul); oprește serverele după PID (`ss -ltnp | grep :PORT`).
- Verificări live: `uvicorn app.main:app --port 80xx` din `backend/`, token: `grep ^BANK_UI_TOKEN ../.env | cut -d= -f2`,
  `POST /api/admin/seed-demo`, `POST /api/admin/rerun-demo`, apoi `GET /api/cases/{id}`.
- `.env` local are cheia Bedrock (expiră ~23:20, organizatorii dau alta la demo). Claude Code rulează pe abonament (nu pe cheie).

## Ce e gata pe `main` (189 teste, CI verde)
- **Pipeline** (Samuel): Paznic → Funcționar → [Verificator ∥ Detector ∥ Detectiv] → Compliance; SSE cu replay; timeout per agent;
  agenți „skipped” dacă dependența pică; dosarul Mariei (fișiere reale din `data/demo/maria/`) în ~22–24s.
- **Client LLM** `core/llm.py` (Samuel): bedrock (AsyncAnthropicBedrock, Haiku/Sonnet/Opus 5.5) / cloud (Featherless) / local (Ollama) / mock;
  poarta anti-PII (`core/pii_gate.py`) + audit (`core/audit.py`); cache `data/llm_cache` (LLM_RECORD / DEMO_CACHE).
- **Compliance** (Samuel): noisy-OR, override-uri, rezumat Sonnet doar din dovezi; raport HTML `GET /api/cases/{id}/report`.
- **Paznic** (Narcis, + reparațiile mele + Stefan #14 + Narcis #15): OCR, MRZ tolerant, nume peste tot, CNP/telefon cu spații,
  IBAN reparat din zgomot OCR, amprente HMAC (inclusiv `id_document`), seif criptat. 0 scurgeri pe Maria.
- **Funcționar** (Stefan): grounding cu bbox, extras pe rânduri, fallback fără LLM.
- **Verificator** (Stefan): taxe (`tax.py`, cu suma netaxabilă + salariu minim pe lună + 0–4 persoane în întreținere),
  extras (solduri, salariul în extras), ANAF real (cache 24h, 1/s, audit, comparație nume firmă), verificări RO,
  **criptare homomorfică** CKKS/TenSEAL (`he_bank.py`, `he_verifier.py`, ~50–70 ms).
- **Detectiv** (Erin): graf networkx pe amprente, `/api/graph`, rețeaua Mariei = 6 dosare (via IBAN, seed-demo leagă prin amprente reale).
- **Arena** (Samuel): Forge Studio, judge provizoriu (folosește tax.py), scor anti-trișat, rate limit, clasament, SSE `/api/arena/live`.
- **Self-learning** (Samuel): Opus propune reguli JSON → validare + backtest (respinge FP pe legitime și reguli prea specifice) → aprobare umană.
- **Atacator** (Samuel): fuzzer adaptiv (Claude a refuzat rolul de falsificator → algoritmic). `POST /api/admin/attacker/start`.
- **Benchmark** `scripts/benchmark.py` — ONEST: date sintetice, falsuri create de noi (100% = regulile merg pe cazurile gândite,
  nu acuratețe reală); 0 FP pe 240 legitime (incl. salarii mici cu persoane în întreținere); falsul „perfect” nu se prinde din fluturaș.
- **Frontend** (Erin): Login, Dosar (3 vederi + bbox + graf live + raport), Dashboard, Arena mobil, proiector `/arena/live`,
  buton „Mod 100% local”.
- `seed-demo`, `seed-arena`, `rerun-demo`, `reset` (interzis în ENV=demo).

## Ce lipsește / în lucru
| Ce | Cine | Stare |
|---|---|---|
| **Detector real** (ELA, metadate PDF; `files.save_derived(..., "ela", page, png)`) | Narcis | încă stub (`registry.py`) |
| **Header `ngrok-skip-browser-warning: 1`** în `lib/api.ts`, `lib/arena.ts`, `lib/events.ts` + proiectorul de pe `EventSource` pe `fetchEventSource` | Erin | lipsește — BLOCANT pentru deploy prin ngrok gratuit |
| Deploy: ngrok domeniu static (Narcis) + Vercel cu `VITE_API_URL`/`VITE_PUBLIC_URL` (Erin) | Narcis + Erin | neînceput; pașii în `notes/narcis.md` §6 și `notes/erin.md` |
| Mod local Ollama testat | Narcis | ? |
| **ZK** | **Samuel (acum)** — Lorena n-a început | vezi planul de mai jos |
| PR #17 (Stefan: `_extract_json` fără „{” pentru Featherless + bbox doar pe valoare) | agent de verificare pornit | de văzut rezultatul, atinge `core/llm.py` |
| Ramura `erin/review-fixes` ec07618 (proiector „+0”, graf aerisit) — după merge-ul #16 | Erin | fără PR încă; diff-ul vs main arată notele de deploy șterse doar pentru că ramura e veche (nu le șterge ea) — la merge atenție să nu dispară `notes/*` |
| Ramura `lorena/p0-generatoare-date` (validator MRZ `mrz_td2_valid`, corect — testat) | Lorena | fără PR; fără conflicte acum |
| După 18:00: `LLM_RECORD=true` + rerun pentru demo offline, video de rezervă, pitch, curățare istoric Claude | toți | — |

## PLAN ZK (varianta rapidă, ~1,5–2h) — de făcut acum
Din ARCHITECTURE §7 (fallback). Afirmația: „venitul meu, atestat de angajator pentru această cerere, e ≥ prag”; banca află doar DA.
1. **Unelte**: `nargo` (Noir) + `bb` (Barretenberg). Instalare: `noirup` / `bbup` (curl din repo noir-lang). Fixează versiunile
   compatibile între `nargo`, `@noir-lang/noir_js`, `@aztec/bb.js` → scrie-le în `zk/README.md`. Întâi „hello world” care dovedește/verifică din CLI.
2. **Circuit** `zk/circuits/income_threshold/src/main.nr` (fără semnătură în circuit):
   - privat: `salary_bani: u64`, `salt: Field`; public: `threshold_bani: u64`, `commitment: Field`, `case_nonce: Field`.
   - `assert(poseidon/pedersen_hash([salary_bani as Field, salt, case_nonce]) == commitment)`; `assert(salary_bani >= threshold_bani)`.
   - Funcția de hash: cea disponibilă în stdlib-ul versiunii fixate (pedersen_hash sau poseidon); ACEEAȘI trebuie calculată de „angajator”
     → cel mai simplu: angajatorul calculează commitment-ul tot cu Noir/`bb` sau cu `noir_js` (evită reimplementarea hash-ului în Python).
3. **Angajatorul** (serviciu separat, `employer/`): primește `salary`, `case_nonce`, generează `salt`, calculează `commitment`,
   **semnează ECDSA** `(commitment, case_nonce, period)` cu cheia lui (Python `ecdsa`), dă clientului `{salary, salt, commitment, sig}`.
   Registrul de angajatori: `CUI → cheie publică` (JSON). Semnătura se verifică ÎN PYTHON, în afara circuitului.
4. **Banca** (`backend/app/zk/`): `POST /api/zk/nonce` (nonce random, o singură folosire), `POST /api/zk/verify`:
   verifică semnătura angajatorului (registru), reconstruiește inputurile publice (prag = rata/0,40 DSTI, commitment, nonce),
   verifică dovada (script Node cu bb.js aceeași versiune, sau `bb verify` CLI ca prim pas), marchează nonce-ul folosit.
5. **Dovada**: întâi din CLI/backend pentru demo sigur; apoi, dacă e timp, în browser cu `noir_js` + `bb.js` (single-threaded, fără COOP/COEP;
   Vite: exclude `@noir-lang/*` și `@aztec/bb.js` din `optimizeDeps`) — pagina clientului o poate face Lorena/Erin.
6. **Demo**: dovadă validă → DA; prag modificat / semnătură falsă / nonce refolosit → respinse. Teste pentru toate.
7. Timebox: dacă nu merge până la ~17:00 → rămâne în pitch ca „următorul pas”.

## Comenzi utile
- Teste: `cd backend && .venv/bin/ruff check app tests -q && .venv/bin/python -m pytest -q`
- Documentele Mariei: `backend/.venv/bin/python -m data.generator.build_demo`
- Benchmark: `backend/.venv/bin/python scripts/benchmark.py`
- Review PR: `git fetch origin pull/N/head:review-prN` + worktree în scratchpad + symlink `.venv`, port separat per agent.
