# Note pentru Erin

## Dashboard (PR #12, îmbinat) — din review
1. **Modul mock inventează două cifre** (`mockDashboard.ts` ~240): costul AI `0.00056 $/dosar` și `23` date personale/dosar,
   iar comentariul zice „aceleași formule ca backend”. `?mock=1` rămâne activ pe tab → la prezentare s-ar putea vedea
   cifre false din greșeală. Propunere: banner mare „DATE DE DEMO” când e mock, sau 0 la cost.
2. Mock-ul numără frauda după `recommendation === 'escalate'`; backend-ul după etichetă sau status `rejected/escalated`
   (`backend/app/api/system.py`). Pot da cifre diferite.
3. **Lizibilitate pe proiector:** nota cu presupuneri e `text-sm`, etichetele KPI și tabelul `text-base`, axele graficului 13px.
   Ținta din ARCHITECTURE §10 e ≥ 20–24px → `text-xl` la etichete, cel puțin `text-base` la notă.
4. `perDay` grupează pe dată UTC, tabelul pe dată locală → pot diferi noaptea.
5. Tabelul „dosare recente” ia `slice(0,10)` fără sortare (merge acum doar pentru că backend-ul le dă în ordine).

## Detectiv / graf (PR #10, îmbinat) — mărunțișuri
- `linked_cases` numără și legăturile doar prin CUI/nume → un coleg cinstit pornește animația grafului degeaba.
- Nodurile CUI/nume cu `shared_by ≥ 2` apar roșii (`in_cluster`) chiar dacă nu sunt rețea.
- `IDENTITY_KINDS` din `graph.py` nu e folosit.

## Ce mai trebuie pe frontend (backend-ul e gata, vezi `backend/README.md`)
- **Arena pe telefon** (Forge Studio): `GET /api/arena/missions`, `POST /api/arena/submissions`, `/submissions/{id}/image`.
- **Ecranul de proiector** `/arena/live`: QR + `GET /api/arena/leaderboard` + SSE `GET /api/arena/live`
  (evenimente `arena_scored`, `rule_proposed`, `rule_approved`, `agent_progress` de la Atacator).
- **Butonul „Mod 100% local”**: `POST /api/settings {"llm_mode": "local"}` (și înapoi `bedrock`).
- **Raportul de anchetă**: `GET /api/cases/{id}/report` (HTML printabil) — un buton pe pagina Dosar.
- Criptarea homomorfică: Verificatorul pune în `AgentResult.artifacts` câțiva bytes de ciphertext — dacă îi arăți,
  scrie că sunt **ilustrație**, nu dovadă.
