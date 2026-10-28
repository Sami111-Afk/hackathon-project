# 🔒 ORB — agenți AI care verifică documentele băncii fără să le citească

> **Echipa: planul de acum până la predare e în [`notes/plan.md`](notes/plan.md)** (cine ce face, termene). Pitch-ul: [`notes/pitch.md`](notes/pitch.md).


> Hackathon · Tema **Raiffeisen Bank: Operational Efficiency** — *„Explore how AI agents can reduce repetitive work involving documents, data, and verification.”*

**ORB** este un birou virtual de agenți AI pentru back-office-ul băncii. Agenții citesc documentele dintr-o cerere de credit (buletin, fluturaș, extras, adeverință), le verifică, prind falsurile — inclusiv cele făcute cu AI — și leagă dosarele între ele ca să descopere rețele de fraudă. Omul ia decizia, cu toate dovezile în față.

Fără ca datele clienților să iasă din bancă:
- AI-ul din cloud primește doar date **pseudonimizate** — `[PERSOANA_1]`, `[CNP_1]` — niciodată identificatori;
- un verificator terț poate verifica calculele **pe numere criptate**, fără să le vadă (criptare homomorfică);
- clientul își poate **dovedi venitul fără să-l arate** (dovezi zero-knowledge);
- un **buton de mod 100% local**: totul rulează pe serverul „băncii”, fără internet.

Iar ca sistemul să devină tot mai bun, oricine îl poate ataca în **Arena** — un joc în care încerci să păcălești agenții cu un document fals. Fiecare fals care trece devine o regulă nouă (self-learning).

📐 Detaliile tehnice: **[ARCHITECTURE.md](ARCHITECTURE.md)**

---

## Cuprins
1. [Povestea (scenariul de demo)](#1-povestea-scenariul-de-demo)
2. [Ce face, pe scurt](#2-ce-face-pe-scurt)
3. [Arhitectura într-o imagine](#3-arhitectura-într-o-imagine)
4. [Stack tehnic](#4-stack-tehnic)
5. [Cum pornești proiectul](#5-cum-pornești-proiectul)
6. [Moduri de rulare](#6-moduri-de-rulare)
7. [Cine ce face](#7-cine-ce-face)
8. [Primele 60 de minute](#8-primele-60-de-minute)
9. [Priorități](#9-priorități-p0--p1--p2)
10. [Timeline 24h](#10-timeline-24h)
11. [Reguli de lucru în echipă](#11-reguli-de-lucru-în-echipă)
12. [Confidențialitate — ce spunem și ce nu](#12-confidențialitate--ce-spunem-și-ce-nu)
13. [Pitch și demo](#13-pitch-și-demo)
14. [Întrebări probabile de la juriu](#14-întrebări-probabile-de-la-juriu)
15. [Riscuri și planuri B](#15-riscuri-și-planuri-b)

---

## 1. Povestea (scenariul de demo)

**Maria Ionescu**, 67 de ani, pensionară din Ploiești. Un escroc găsește o poză cu buletinul ei și cere online un credit de 45.000 lei pe numele ei, cu:
- buletinul Mariei cu poza înlocuită de un chip generat cu AI;
- un fluturaș de salariu făcut cu un LLM („contabilă, 8.500 lei net”);
- un extras de cont editat.

În ~15 secunde, ORB:
1. 🛡️ **Paznicul** ascunde local toate datele personale (inclusiv poza și zona MRZ a buletinului);
2. 📄 **Funcționarul** extrage datele din documente;
3. 🔍 **Verificatorul** reface calculul taxelor — netul nu iese; firma e inactivă la ANAF; o femeie de 67 de ani „angajată ca contabilă”;
4. 🤖 **Detectorul** arată zona editată din extras și urmele de editare din PDF;
5. 🕵️ **Detectivul** găsește că telefonul din cerere apare în alte 5 cereri, pe 5 nume diferite → rețea;
6. ⚖️ **Compliance** dă verdictul: *scor de risc 96 — furt de identitate, rețea suspectă → investigație* + dosar cu dovezi;
7. 👤 **Angajatul** respinge cererea și marchează rețeaua pentru investigație. Banca o anunță pe Maria **pe telefonul din evidențele băncii** (nu pe cel din cerere — acela e al escrocului).

Maria nu va afla niciodată de la un executor că are o datorie de 45.000 lei.

## 2. Ce face, pe scurt

| Componentă | Rol | Tehnologie |
|---|---|---|
| 🛡️ Paznic | OCR, găsește și ascunde datele personale, MRZ, amprente HMAC, seif local | Tesseract / strat text PDF, regex + cifre de control, GLiNER |
| 📄 Funcționar | Extrage date structurate, fiecare valoare legată de textul sursă | LLM + validare, parsare deterministă pentru extrase |
| 🔍 Verificator | Taxe, extras, ANAF, verificări românești (CNP vs buletin vs MRZ, vârstă, IBAN), reguli | Python, TenSEAL |
| 🤖 Detector | Editări și documente generate cu AI | ELA, structură PDF, metadate, C2PA, AI-detector (GPU) |
| 🕵️ Detectiv | Leagă dosarele prin amprente, găsește rețele | networkx |
| ⚖️ Compliance | Scor din dovezi + verdict + rezumat | noisy-OR + LLM (doar pentru explicație) |
| 🧠 Self-learning | Reguli noi din greșeli, testate, aprobate de om | LLM + motor de reguli JSON |
| 🎮 Arena | Joc: păcălește agenții din telefon („Forge Studio”), clasament live | același pipeline |
| 🔐 ZK | Clientul dovedește „venit ≥ prag” fără să-l arate | Noir + Barretenberg (UltraHonk) |
| 📊 Dashboard | Dosare, ore/bani economisiți, fraude, date protejate, cost AI | React + Recharts |

## 3. Arhitectura într-o imagine

```
   Demo pe scenă: frontend local ─┐        🏦 „BANCA” = laptopul lui Narcis (RTX 4060)
   Arena: ☁️ Vercel (telefoane) ──┤  ┌──────────────────────────────────────────────┐
                                  └─►│ FastAPI  (ngrok, domeniu static)             │
                                     │                                              │
                                     │ ORCHESTRATOR                                 │
                                     │  1 Paznic ─► 2 Funcționar ─┬─► 3 Verificator │
                                     │                            ├─► 4 Detector    │
                                     │                            └─► 5 Detectiv    │
                                     │                 ─► 6 Compliance ─► om        │
                                     │ SQLite · vault.db · Ollama (Qwen 4B, local)  │
                                     └───────────────┬──────────────────────────────┘
                                                     │ doar date pseudonimizate
                                                     ▼ (poarta anti-PII)
                                ☁️ AWS BEDROCK — Claude  (rezervă: Featherless)

   🏢 Serviciul „angajatorului” (separat) ─► semnează venitul ─► 📱 clientul face dovada ZK
```

## 4. Stack tehnic

| Parte | Alegere | Note |
|---|---|---|
| Backend | **Python 3.11** + FastAPI + SQLModel + SQLite (WAL) | 3.11 obligatoriu (TenSEAL, GLiNER, torch) |
| Live | SSE + `fetch-event-source` în browser | polling ca fallback |
| LLM cloud (principal) | **Claude pe AWS Bedrock** — Haiku 5.5 / Sonnet 5.5 / Opus 5.5 | testat, merge; cheia expiră după 12h → cereți una nouă |
| LLM cloud (rezervă) | Featherless, SDK `openai` | DeepSeek-V4-Flash, Qwen3.8-Flash-Next |
| LLM local | Ollama | Qwen ~4B, `num_ctx 8192`, `temperature 0` |
| OCR | Tesseract `ron` (`tessdata_best`) / stratul de text PDF | |
| Date personale | regex + cifre de control + MRZ + GLiNER (CPU) + zone de șablon | |
| Criptare homomorfică | TenSEAL (CKKS) | |
| Zero-knowledge | Noir (`nargo` 1.0.0-beta.13) + Barretenberg (`bb` 1.2.0, UltraHonk) | versiuni fixate în `zk/README.md` |
| Frontend | React + Vite + TS + Tailwind + shadcn/ui + TanStack Query + Recharts + react-force-graph | |
| Deploy | Vercel (Arena) + ngrok static (backend) + frontend local pentru demo | |

## 5. Cum pornești proiectul

### Cerințe
- Python **3.11**, Node 20+, Git
- Tesseract cu limba română (pe Windows: installer-ul UB Mannheim, **bifează Romanian**, apoi setează `TESSERACT_CMD`)
- Doar pe laptopul cu GPU: Ollama, torch cu CUDA
- Doar pentru ZK: `nargo` (versiunea din `zk/README.md`)

### Configurare
```bash
cp .env.example .env
# completează: HMAC_SECRET, ARENA_HMAC_SECRET, VAULT_KEY, BANK_UI_TOKEN (+ AWS_BEARER_TOKEN_BEDROCK sau FEATHERLESS_API_KEY)
# (comenzile de generare sunt în comentariile din .env.example)
```
Backend-ul **refuză să pornească** dacă secretele lipsesc.

### Backend — toată lumea
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements-core.txt
uvicorn app.main:app --reload --reload-dir app --port 8000
# test: http://localhost:8000/health
```

### Backend — în plus, pe laptopul lui Narcis (GPU)
```bash
# ÎNTÂI torch cu CUDA, abia apoi restul (altfel pip pune torch fără GPU)
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements-ml.txt
```

### Frontend — Erin (nu instalează nimic de Python)
```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
# fără backend: deschide cu ?mock=1 → redă shared/fixtures/maria_events.jsonl
# alt backend: ?api=https://<url-ngrok>
```

### Modul local (Narcis)
Ollama rulează pe același laptop cu backend-ul, pe `127.0.0.1`. Pe Windows, setează `OLLAMA_KEEP_ALIVE=-1` ca variabilă de mediu a utilizatorului și repornește aplicația Ollama din tray.

### Date de demo (din rădăcina repo-ului)
```bash
python -m data.generator.build_demo
export BANK_UI_TOKEN=$(grep ^BANK_UI_TOKEN .env | cut -d= -f2)
curl -X POST -H "Authorization: Bearer $BANK_UI_TOKEN" localhost:8000/api/admin/seed-demo
```

## 6. Moduri de rulare

| Variabilă | Valori | Ce face |
|---|---|---|
| `LLM_MODE` | `bedrock` / `cloud` / `local` / `mock` | Claude pe Bedrock / Featherless / Ollama / răspunsuri salvate |
| `DETECTOR_GPU` | `on` / `off` | AI-detector pe GPU sau doar ELA + PDF + metadate |
| `HE_ENABLED` | `true` / `false` | verificare pe date criptate sau în clar |
| `DEMO_CACHE` | `true` / `false` | redă răspunsurile LLM salvate (demo fără internet) |
| `ENV` | `dev` / `demo` | `demo` ascunde `/docs` și pornește fără reload |

## 7. Cine ce face

| Cine | Foldere | P0 (ora 0–8) | P1 (ora 8–16) | P2 |
|---|---|---|---|---|
| **Samuel** | `backend/app/core`, `api`, `models.py`, `agents/compliance`, `arena`, `learning`, `data/attacker`, **`zk/`, `backend/app/zk`** | modele + orchestrator + SSE + client LLM (cloud/local/mock + poarta anti-PII) + Compliance + fixture-uri | **bucla AI contra AI:** Arena (Forge Studio, scor, coadă) + **self-learning** (propunere → backtest → aprobare) + ecranul `/arena/live` | **Atacatorul** (falsuri tot mai bune pe runde) + raport PDF |
| **Narcis** | `agents/paznic`, `agents/detector`, deploy | Paznic (OCR, regex, MRZ, zone, normalizare, HMAC, seif) + Ollama + **tunel testat cu SSE** | Detector (ELA z-score, structură PDF, metadate, C2PA) | AI-detector pe GPU |
| **Stefan** | `agents/functionar`, `agents/verificator` | Funcționar (grounding, parsare extrase) + Verificator (taxe, extras, verificări românești) | criptare homomorfică + ANAF | motorul de reguli în Verificator (rulează regulile aprobate) |
| **Erin** | `frontend/`, `backend/app/agents/detectiv` | motorul de live (SSE, reconectare, replay după `seq`) + pagina Dosar (3 vederi + bbox + banda agenților) pe replay-ul Mariei, login | **Detectivul cap-coadă:** graf networkx pe amprente, detectarea rețelelor, scor de cluster, `/api/graph` + **graful live** (react-force-graph) · Dashboard + Arena pe mobil cu componente gata (shadcn, Recharts) | Birou animat, hartă |
| **Lorena** | `data/`, pagina ZK din `frontend/` | generator (CNP/IBAN/CUI/MRZ valide) + **documentele Mariei, brut, până la ora 2** | **set de benchmark cu degradări realiste** (poze de telefon: rotație, blur, JPEG, umbre) + tipurile de fals din ARCHITECTURE §18 · **pagina ZK** (UI peste `/api/zk/demo`, deja gata în backend) | prezentarea (slide-uri + scenariul demo) |

> **Schimbare 28.10, ~14:00:** ZK (circuit Noir, angajatorul care semnează, verificarea la bancă) l-a preluat **Samuel** — e gata în backend. Lorena rămâne pe date + benchmark + pagina ZK. Detalii: `notes/lorena.md`.

**Ora 18–24: toți** — bugfix, video de rezervă, pitch. Fiecare poate explica tehnic partea lui în 30 de secunde.

## 8. Primele 60 de minute

- **Samuel:** confirmă `models.py` (`Case`, `AgentResult`, `PipelineEvent`, `PipelineContext`) · `pipeline.py` care emite evenimente false prin SSE · `shared/fixtures/maria_case.json` + `maria_events.jsonl` complete · CI pe GitHub · protecție pe `main`.
- **Narcis:** Python 3.11 + torch CUDA + Tesseract `ron` + Ollama · pornește ngrok (domeniu static) și **testează SSE de pe un telefon** · GLiNER pe un text românesc · postează URL-ul pe grup.
- **Stefan:** schemele Funcționarului per tip de document · `tax.py` cu teste (net = 0,585·G + 0,1·D) · `import tenseal` funcționează · numele exacte ale modelelor pe Featherless + model vizual testat.
- **Erin:** `npm create vite@latest frontend -- --template react-ts` + Tailwind + shadcn · proiect Vercel · client SSE (`fetch-event-source`) + override `?api=` + replay din `maria_events.jsonl` · venv mic de Python cu `requirements-core.txt` (fără torch) pentru Detectiv.
- **Lorena:** generatoare CNP/IBAN/CUI/MRZ cu teste · prima versiune a documentelor Mariei (JPEG). (ZK: preluat de Samuel, vezi `zk/README.md`.)

## 9. Priorități (P0 / P1 / P2)

- **P0 — fără ele nu există demo:** Paznic, Funcționar, Verificator (în clar), Detector (ELA + PDF), Compliance, orchestrator + SSE, pagina Dosar, Dashboard simplu, documentele Mariei, butonul cloud/local, replay offline.
- **P1 — ce ne face să câștigăm:** criptare homomorfică, ZK, Arena + `/arena/live`, Detectiv + graf, ANAF, benchmark cu cifre.
- **P2 — bonus:** self-learning complet, AI-detector pe GPU, Atacator, Birou animat, hartă, raport PDF.

**Reguli:**
- Nu începi P1 până nu merge P0-ul tău cap-coadă.
- Dacă trebuie tăiat, ordinea e: hartă → Birou animat → Atacator → AI-detector pe GPU → self-learning. HE și ZK rămân.

## 10. Timeline 24h

| Ora | Ce |
|---|---|
| 0:00–1:00 | Checklist-ul din §8. Fixture-urile Mariei gata → toată lumea lucrează pe ele |
| 1:00–8:00 | P0 în paralel |
| **2:00** | Documentele Mariei (brut) disponibile pentru toți |
| **8:00** | **Integrare #1** — dosarul Mariei trece cap-coadă, real |
| 8:00–16:00 | P1 |
| **12:00** | Mini-check: ce nu va fi gata? Tăiem acum. Se întreabă mentorii Raiffeisen cifrele pentru business case |
| **16:00** | **Integrare #2** — Arena testată de pe 5 telefoane prin tunel |
| **18:00** | **STOP feature-uri.** Doar bugfix |
| 18:00–20:00 | Benchmark final, cache LLM pentru demo, video de rezervă |
| 20:00–23:00 | Pitch, repetiții (min. 5), răspunsuri la întrebări |
| 23:00–24:00 | Încălzire modele, check final, laptop în priză |

## 11. Reguli de lucru în echipă

- **Branch-uri scurte:** `nume/feature`, merge în `main` des.
- **`main` pornește mereu.** CI-ul (ruff + pytest) trebuie să fie verde.
- **Contractul** se schimbă doar în `backend/app/models.py`, cu anunț pe grup, apoi `python scripts/export_schemas.py` și `python scripts/build_fixtures.py`.
- **Cheile nu intră în git.** Fiecare are cheia lui Featherless. Comentariile din `.env` stau pe rând separat, niciodată după o valoare.
- **Doar date inventate.** Niciun document real, nicăieri.
- Blocat > 30 min? Spui pe grup.

## 12. Confidențialitate — ce spunem și ce nu

✅ Spunem:
- „Identificatorii (CNP, IBAN, nume, MRZ, poza) nu părăsesc niciodată serverul băncii.”
- „Ce ajunge la LLM e **pseudonimizat**; o poartă blochează orice payload în care apare o valoare din seif.”
- „Pe benchmark: 0 scurgeri de date personale în N documente.” (doar dacă așa iese)
- „**În demo:** Claude pe Bedrock, contul organizatorilor (regiunea us-west-2, date sintetice). **În producție:** Bedrock într-o regiune UE (eu-central-1, Frankfurt), sub contractul AWS al băncii, sau LLM complet on-prem — butonul de mod local arată că se poate.”
- „Criptarea homomorfică permite unui verificator **terț** să ruleze verificări fără să vadă datele.”

❌ Nu spunem:
- „AI-ul nu vede nicio dată” — vede sume și date, pseudonimizate.
- „Amprentele sunt anonime” — sunt pseudonime; cheia ar sta într-un HSM.
- „ORB aprobă credite” — ORB detectează fraude și pregătește dosarul; omul decide.

## 13. Pitch și demo

**Durata: ~4:30.** QR-ul Arenei apare de la început, ca juriul să joace cât vorbim.

| Timp | Ce |
|---|---|
| 0:00 | **Hook** — Maria. QR-ul Arenei pe ecran |
| 0:25 | **Dosarul live** — 3 momente: (a) „ce a văzut AI-ul” lângă original, (b) harta de editare se aprinde pe extras, (c) graful arată rețeaua |
| 1:50 | **Confidențialitate** — butonul de mod local, cablul scos, contorul „0 apeluri externe” |
| 2:30 | **ZK** — clientul cinstit își dovedește venitul fără să-l arate (20 s) |
| 2:50 | **Arena** — rezultatele juriului + „acest fals a devenit regula #18” |
| 3:30 | **Business case** — ore, bani, fraude, cu cifre de la mentori |
| 4:15 | **Închidere** + viziune: Radarul care găsește următorul proces de automatizat |

**Business case** (de completat cu mentorii Raiffeisen, cu surse):
- cât durează azi verificarea manuală a unui dosar și câte dosare pe zi;
- pierderile din fraudă de identitate în România;
- **calea de adoptare:** mod umbră (rulează lângă oameni, fără efect) → asistent → triaj automat al dosarelor cu risc mic; integrat ca API în spatele sistemului de credite existent;
- **reglementarea ca argument:** AI Act (detectarea fraudei e exclusă din „risc ridicat”, dar avem oricum om în buclă + audit), GDPR, DORA.

**De ce nu un furnizor existent** (Resistant AI, Inscribe, Onfido, Veriff, Klippa): sunt servicii cloud — datele pleacă din bancă. ORB rulează on-prem, leagă fraudele **între dosare** prin amprente care păstrează confidențialitatea și învață din corecturile băncii.

## 14. Întrebări probabile de la juriu

| Întrebare | Răspuns |
|---|---|
| Câte fals pozitive aveți pe dosare legitime? | Cifra de pe setul de test, pe slide |
| De ce criptare homomorfică dacă totul rulează la voi? | Pentru verificare de către un terț / alt departament / altă bancă, fără să vadă datele |
| Cine semnează venitul în realitate pentru ZK? | Angajatorul prin sistemele ANAF (REVISAL / D112); în demo, un serviciu simulat cu registru de chei |
| Merge pe poze de telefon? | Verificările de conținut da; ELA nu — de aceea e un semnal printre altele |
| Ce faceți cu prompt injection? | Detectat local, LLM-ul nu decide, rezumatul se face doar din dovezi — demonstrăm live |
| E risc ridicat după AI Act? | Detectarea fraudei financiare e exclusă explicit; oricum avem om în buclă și audit |
| Și dacă rețeaua conține victime? | De aceea nu blocăm automat — marcăm pentru investigație |

## 15. Riscuri și planuri B

| Risc | Plan B |
|---|---|
| Laptopul lui Narcis pică | Al doilea laptop cu `requirements-core.txt`, `LLM_MODE=cloud`, `DETECTOR_GPU=off` |
| Expiră cheia Bedrock (după 12h!) | cheie nouă de la organizatori; altfel `LLM_MODE=cloud` (Featherless) — clientul trece automat |
| Pică internetul / cloud-ul | `LLM_MODE=local` sau `DEMO_CACHE=true`; demo-ul rulează cu frontend local |
| Tunelul nu suportă SSE | ngrok static; frontend-ul trece pe polling |
| Wi-Fi-ul blochează conexiunile | hotspot de pe telefon |
| ZK / HE nu merg la timp | fallback-urile din ARCHITECTURE §6–7; P0 nu depinde de ele |
| Nu joacă nimeni în Arena | clasament pre-populat, Atacatorul pornit, un coleg joacă live |
| Juriul nu reușește să păcălească nimic / reușește prea ușor | falsuri pregătite de ambele tipuri |
| Totul pică | video de rezervă (ora 18) + replay din fixture-uri |
