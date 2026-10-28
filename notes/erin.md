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

## Arena pe mobil + proiector (PR #13, îmbinat) — din review
1. **QR (`ArenaLive.tsx` ~140) folosește `window.location.origin`** → dacă proiectorul e deschis pe `localhost`,
   telefoanele nu pot intra. Fă-l configurabil: `VITE_PUBLIC_URL` sau `?base=https://...` (adresa publică Vercel/ngrok).
2. Avertismentul „Nu încărcați documente reale” pe proiector e `text-lg` (`ArenaLive.tsx` ~185) → `text-xl`.
3. Ecranul live ignoră `rule_proposed` / `rule_approved` / `agent_progress` (Atacatorul). Momentul din pitch
   „acest fals a devenit regula #N” și runda atacatorului ar trebui să apară pe proiector. La reconectarea SSE,
   reîmprospătează și clasamentul (`onopen`).
4. `lib/arena.ts` ~57: dacă `detail` e obiect (eroare 422 FastAPI), apare „[object Object]” →
   `typeof d === 'string' ? d : mesaj generic`.
5. Previzualizarea din Forge arată netul vechi când e bifat „recalculează taxele”; motivele din rezultat sunt cheiate pe text (dubluri).

## Deploy: Vercel (tu) + ngrok (Narcis) — pașii
1. **Header obligatoriu pentru ngrok gratuit:** fiecare cerere către API trebuie să trimită `ngrok-skip-browser-warning: 1`
   (`lib/api.ts`, `lib/arena.ts`, `lib/events.ts`). Altfel ngrok răspunde cu o pagină HTML în loc de JSON.
   Dacă ecranul de proiector folosește `EventSource` simplu pentru `/api/arena/live`, mută-l pe `fetchEventSource`
   (ca în `events.ts`) — `EventSource` nu poate trimite headere.
2. Pe Vercel: `VITE_API_URL=https://<domeniul-ngrok-al-lui-Narcis>` și `VITE_PUBLIC_URL=https://<proiectul-tău>.vercel.app`
   (QR-ul de pe proiector trebuie să ducă la Vercel, nu la `localhost`). Fără `BANK_UI_TOKEN` în variabilele `VITE_*`.
3. Rewrites SPA (`vercel.json`) ca `/arena`, `/arena/live`, `/dashboard` să meargă la refresh.
4. Test cu Narcis de pe telefon pe **date mobile**.

## Review PR #18 (redesign) — după merge
Build OK (`npm ci`, `tsc -b && vite build` fără erori; dev server pornește și servește pe :5180 cu backend-ul pe :8028). Funcțiile sunt păstrate: bbox-uri, 3 vederi (original/redactat/ELA cu `view=ela`), banda de agenți SSE, graf, raport, butoane de decizie, grafice Dashboard, Arena mobil, comutator mod local, URL din `VITE_API_URL`, fără token hard-codat. `npm run lint`: doar 4 warning-uri (ui/badge.tsx:48, ui/button.tsx:66, ui/tabs.tsx:89, NetworkGraph.tsx:33 — ref citit în render), nu blochează.

Probleme rămase (nu vin din redesign, dar blochează deploy-ul pe ngrok gratuit):
1. **BLOCANT:** `ngrok-skip-browser-warning: 1` nu e trimis nicăieri (grep în `src/` = 0 rezultate). Adaugă-l în `lib/api.ts:15-18` (`headers.set('ngrok-skip-browser-warning', '1')`), `lib/arena.ts:45` (fetch-ul fără headere, plus `:67`) și `lib/events.ts:29` (`headers['ngrok-skip-browser-warning'] = '1'`). Fără el ngrok întoarce HTML în loc de JSON.
2. `pages/arena/ArenaLive.tsx:66` folosește `new EventSource(liveUrl())` — nu poate trimite headerul. Înlocuiește cu `fetchEventSource` (ca în `lib/events.ts`), cu headerul de mai sus și cu reconectare/`onopen`/`onerror` echivalente; altfel proiectorul nu primește evenimente prin ngrok. Imaginile (`lib/api.ts`, blob) trec prin `apiFetch`, deci se rezolvă cu punctul 1.
3. `npm audit` raportează vulnerabilități în dependențe (nu am rulat `audit fix`); neurgent.

Info: există acum API-ul ZK gata (`POST /api/zk/demo`, vezi `zk/README.md`). Lorena va construi pagina ZK și te poate întreba unde s-o pună în meniu (`components/AppNav.tsx`).

## Reparație mică făcută de Samuel (28.10, ~13:45)
Linkul din meniu `/cases/case_maria` dădea „Dosarul nu s-a încărcat” — fiecare `rerun-demo` creează un id nou (`case_maria_xxxxxx`).
În `pages/CasePage.tsx` am pus un wrapper: `case_maria` (în afara modului mock) → caută cel mai recent `case_maria_*` din `/api/cases`
și redirecționează; restul paginii e neschimbat (acum e `CaseView`). Dacă refaci pagina, păstrează comportamentul.
- (13:55) Am adăugat în `CasePage` butonul **„Analizează din nou, live”** (doar pe dosarele Mariei, nu în mock): `POST /api/admin/rerun-demo`
  → navighează la dosarul nou, iar agenții apar live prin SSE. Funcția e `rerunDemo()` în `lib/api.ts`. Rămâne la tine: butonul **„Dosar nou”**
  cu încărcare de documente (`POST /api/cases`, multipart — vezi `backend/app/api/cases.py`).

## Design — ce nu se înțelege la prima vedere (Samuel, 28.10 ~14:00) — după deploy, în ordinea asta
1. **Panou „Dovezi de confidențialitate” în pagina Dosar** (cel mai important — e ce ne diferențiază și acum NU se vede nicăieri).
   Date gata: `GET /api/cases/{id}/privacy` (token de bancă). Întoarce:
   - `at_rest.documents[]` (`filename`, `encrypted_bytes`, `sample` = începutul fișierului criptat de pe disc, „gAAAAA…”) și
     `at_rest.vault` (`labels` = [CNP_1], [IBAN_1]…, `count`, `sample` criptat) → „Documentele și datele personale stau criptate (AES)”.
   - `ai_saw` (`llm_calls`, `with_pii` = 0, `blocked`, `models`, `redacted_sample`) → „AI-ul a primit 6 cereri, 0 cu date personale”
     + textul exact pe care l-a văzut AI-ul (cu [PERSOANA_1]).
   - `homomorphic` (`he_scheme`, `he_formula`, `he_ms`, `he_ciphertext_kb`, `he_ciphertext_sample`, `verifier_has_secret_key: false`)
     → „Taxele verificate pe date criptate: CKKS, 71 ms, 1,6 MB ciphertext; verificatorul n-a avut cheia”. Arată și câțiva octeți hex.
   - `zk` (null sau `answer`, `reason`, `threshold_ron`, `employer`) → „Venit dovedit fără să-l vedem: DA”. Buton „Cere dovadă de venit”
     care cheamă `POST /api/zk/demo` cu `{"case_id": id}` și apoi reîncarcă panoul (pagina Lorenei poate primi `?case_id=`).
   - `prompt_injection_detected` (bool).
   Ideal ca o bandă sus, sub banda agenților: 🔒 Criptat în repaus · 🙈 AI-ul n-a văzut date personale · 🧮 Calcul pe date criptate · 🔐 Venit dovedit ZK.
2. **Context**: cine folosește aplicația (analistul de credit) și ce câștigă (20 min → 1 min/dosar). Un text scurt pe Dashboard.
3. **„Solicitant [PERSOANA_1]”** pare bug → tooltip/notă: „numele e ascuns de Paznic, nici AI-ul nu-l vede”.
4. **Graful**: cutia neagră mare cu nodurile înghesuite într-un colț și etichete peste legendă. Centrează (zoomToFit după încărcare),
   fă-l mai mic și mută-l SUB documente + dovezi (documentele sunt partea principală).
5. **Dashboard**: `case_ok_30` nu spune nimic → „Credit nevoi personale · 60.000 lei” / solicitant anonimizat; buton **„Dosar nou”**
   (upload, `POST /api/cases` multipart, vezi `backend/app/api/cases.py`).
6. Mici: gol mare deasupra scorului de risc în coloana din dreapta; descrierile agenților tăiate („Ascunde datele perso…”);
   link spre Arena în meniu.

- (14:55) Am pus eu panoul „Confidențialitate” (punctul 1 de mai sus): `components/PrivacyPanel.tsx`, montat în `CasePage` sub banda agenților, doar în afara modului mock. Ajustează-l liber la stilul tău.

## Deploy fără blocaj (Samuel, ~15:00)
Vercel (plan gratuit, repo privat) blochează deploy-ul dacă ultimul commit nu e al tău. Folosește de acum:
```
git pull && scripts/deploy_frontend.sh
```
Copiază `frontend/` + `shared/` într-un folder temporar fără git și rulează `npx vercel --prod` de acolo. Caută singur
`.vercel` în rădăcina repo-ului sau în `frontend/`. Joi, după ce facem repo-ul public, merge și `npx vercel --prod` direct.
