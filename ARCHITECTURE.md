# ORB — Arhitectură tehnică

Documentul de referință pentru toată echipa. Dacă ceva din cod contrazice acest document, ori repari codul, ori actualizezi documentul și anunți pe grup.

## Cuprins
1. [Principii](#1-principii)
2. [Componente și flux](#2-componente-și-flux)
3. [Contractul comun (JSON)](#3-contractul-comun-json)
4. [Confidențialitate](#4-confidențialitate)
5. [Agenții, unul câte unul](#5-agenții-unul-câte-unul)
6. [Criptare homomorfică](#6-criptare-homomorfică)
7. [Dovezi zero-knowledge](#7-dovezi-zero-knowledge)
8. [Self-learning și motorul de reguli](#8-self-learning-și-motorul-de-reguli)
9. [Arena](#9-arena)
10. [Frontend](#10-frontend)
11. [Dashboard și metrici](#11-dashboard-și-metrici)
12. [API și autentificare](#12-api-și-autentificare)
13. [Clientul LLM: bedrock / cloud / local / mock](#13-clientul-llm-bedrock--cloud--local--mock)
14. [Concurență, GPU și performanță](#14-concurență-gpu-și-performanță)
15. [Deploy](#15-deploy)
16. [Securitate](#16-securitate)
17. [Reglementare — cum ne poziționăm](#17-reglementare--cum-ne-poziționăm)
18. [Date de test și benchmark](#18-date-de-test-și-benchmark)
19. [Testare și CI](#19-testare-și-ci)
20. [Structura repo-ului](#20-structura-repo-ului)

---

## 1. Principii

1. **Nicio dată personală identificabilă nu ajunge la un LLM din cloud.** Paznicul rulează primul, local. Ce iese e **pseudonimizat** (sume, date, tipuri de documente legate de etichete) — formulăm exact așa, nu „nicio dată”.
2. **Ce se poate face cu cod, se face cu cod.** Cifre de control, calcule, parsarea extraselor, reguli → Python determinist. LLM-ul doar unde chiar e nevoie de limbaj.
3. **LLM-ul nu decide.** Scorul vine din finding-uri; LLM-ul doar explică. Omul ia decizia finală.
4. **Totul e auditabil.** Fiecare pas, fiecare apel extern, fiecare regulă, fiecare decizie (cu `decided_by`).
5. **Fiecare componentă are fallback.** Demo-ul nu depinde de nimic care poate pica.
6. **Contractul JSON e sfânt.** Toți lucrează în paralel pe el, cu fixture-uri din prima oră.

## 2. Componente și flux

```
Upload (Dosar / Arena)
   │
   ▼
ORCHESTRATOR (backend/app/core/pipeline.py)
   │  stare + evenimente în memorie → SSE; DB scris la finalul fiecărui agent
   │
   ├─ 1. PAZNIC          PDF text-layer sau OCR → PII (regex+checksum, MRZ, GLiNER, zone de șablon)
   │                     → etichete + amprente HMAC + seif + imagine redactată + bbox-uri
   │                     + detectare locală de prompt injection
   │
   ├─ 2. FUNCȚIONAR      text redactat → JSON cu {value, source_text} → grounding pe OCR
   │                     (extrasele: parsare deterministă pe coloane, LLM doar pt. antet)
   │
   ├─ 3. VERIFICATOR ┐   taxe (TenSEAL), extras, ANAF, verificări românești, reguli
   ├─ 4. DETECTOR    ├─  ELA (z-score), metadate PDF/EXIF, C2PA, AI-detector (semnal slab)
   ├─ 5. DETECTIV    ┘   amprente → graf → clustere                       ← asyncio.gather
   │
   ├─ 6. COMPLIANCE      noisy-OR pe finding-uri + override-uri dure → verdict
   │                     LLM scrie rezumatul DOAR din finding-uri (nu vede textul documentului)
   ▼
Decizia omului (cu decided_by) ──► SELF-LEARNING (regulă propusă → validare → backtest → aprobare)
```

- Paznic → Funcționar: secvențial. Verificator, Detector, Detectiv: în paralel.
- Detectorul lucrează pe imaginea originală, **local**.
- Un agent cu eroare / timeout (30 s) → `status: "error"`; Compliance marchează dosarul **„incomplet”** (nu scade riscul și nu blochează pipeline-ul).
- Stări dosar: `received → processing → awaiting_review → cleared | rejected | escalated` (+ `error`).

## 3. Contractul comun (JSON)

**Sursa adevărului: `backend/app/models.py`.** Schemele din `shared/schemas/` se generează cu `python scripts/export_schemas.py` (excepție: `rule.schema.json`, scrisă de mână); fixture-urile din `shared/fixtures/` cu `python scripts/build_fixtures.py`. CI-ul pică dacă nu sunt la zi.

### Dosar (`Case`)
```json
{
  "id": "case_7f3a",
  "source": "bank",
  "status": "awaiting_review",
  "created_at": "2026-10-28T10:14:00Z",
  "requested_amount_ron": 45000,
  "applicant_token": "[PERSOANA_1]",
  "documents": [
    {
      "id": "doc_1",
      "type": "payslip",
      "filename": "fluturas.jpg",
      "pages": [{ "page": 1, "width": 1654, "height": 2339 }],
      "redacted_text": "Angajat: [PERSOANA_1], CNP [CNP_1] ...",
      "extracted": {
        "gross_salary": { "value": 14200, "source_text": "14.200,00" },
        "net_salary":   { "value": 8500,  "source_text": "8.500,00" }
      }
    }
  ],
  "fingerprints": { "phone": ["hm_9c1e"], "iban": ["hm_44ab"], "cnp": ["hm_0f2d"], "address": ["hm_aa71"] },
  "results": [],
  "verdict": { "risk": 0.96, "label": "identity_fraud", "summary": "...", "recommendation": "escalate", "incomplete": false },
  "decision": null
}
```

`pages[].width/height` sunt obligatorii — frontend-ul scalează `bbox`-urile pe imagine cu ele.

### Rezultatul unui agent (`AgentResult`)
```json
{
  "agent": "verificator",
  "status": "done",
  "risk": 0.82,
  "duration_ms": 1840,
  "error": null,
  "findings": [
    {
      "code": "NET_MISMATCH",
      "severity": "high",
      "message": "Netul calculat (8.307 lei) diferă de cel declarat (8.500 lei)",
      "evidence": { "doc_id": "doc_1", "page": 1, "bbox": [120, 340, 260, 360], "field": "net_salary" },
      "rule_id": null
    }
  ],
  "artifacts": { "ela_image": "/api/cases/case_7f3a/documents/doc_1/image?view=ela" },
  "llm_usage": { "provider": "featherless", "model": "deepseek-ai/DeepSeek-V4-Flash", "input_tokens": 1820, "output_tokens": 410, "cost_usd": 0.00037 }
}
```
- `bbox` = `[x0, y0, x1, y1]` în pixeli pe pagina indicată (origine stânga-sus).
- `error` = mesaj generic + ID de corelare, **niciodată** valori din document (vezi §16).
- Câmpurile opționale lipsă se serializează cu `exclude_none=True`.

### Eveniment SSE (`PipelineEvent`)
```json
{ "case_id": "case_7f3a", "seq": 12, "ts": "2026-10-28T10:14:08.120Z",
  "type": "agent_finished", "agent": "verificator",
  "message": "Calculul nu iese: diferență -193 lei", "data": { } }
```
Tipuri: `case_created, agent_started, agent_progress, agent_finished, agent_error, debate, verdict, decision, rule_proposed, rule_approved, arena_scored, ping`.
- `seq` crește per dosar; clientul reconectează cu `Last-Event-ID` și primește replay din memorie.
- Stream-ul global (`/api/events`) trimite **doar ID-uri și stări**, nu conținut.
- `debate` = mesaj între agenți (pentru animația din Birou).

## 4. Confidențialitate

### Ce înseamnă concret „protejat”
| Clasă | Exemple | Tratament |
|---|---|---|
| Identificatori | CNP, IBAN, CUI, serie/nr. buletin, telefon, email, **MRZ** | doar cod local → etichetă + amprentă HMAC |
| Date personale | nume, adresă, data nașterii, **poza, semnătura** | doar local → etichetă / zonă neagră |
| Date financiare | salariu, sold, sume | pseudonimizate (legate de etichete); Verificatorul le poate procesa criptat |
| Text non-personal | denumiri de câmpuri, structură | oriunde |

**Formulare corectă (și în pitch):** datele trimise în cloud sunt **pseudonimizate** — tot date personale în sensul GDPR (art. 4(5)), dar fără identificatori. **În producție: LLM local / on-prem; Featherless doar pe date sintetice** (secret bancar OUG 99/2006, DORA, EBA/GL/2019/02 → un LLM extern ar fi furnizor de outsourcing).

### Paznicul — pași
1. **Text:** PDF digital → stratul de text cu `pypdfium2` (text + bbox exacte). Imagine → Tesseract `ron` (`tessdata_best`), upscale ~300 DPI, `--psm 6`, `image_to_data` (cuvinte + bbox).
2. **Hartă offset → bbox:** la concatenarea cuvintelor în text se construiește maparea `char_offset → word_index`; orice span găsit (regex/GLiNER) se mapează înapoi la reuniunea bbox-urilor cuvintelor.
3. **Regex + validare** CNP, IBAN, CUI, telefon, email, serie buletin. Match fără checksum valid → tot ascuns, plus finding `*_CHECKSUM_INVALID`.
4. **MRZ** (buletin): linii `^[A-Z0-9<]{30,36}$` → redactate integral; validate local cu cifrele de control (ponderi 7-3-1) și comparate cu câmpurile tipărite și cu CNP-ul.
5. **GLiNER** (pe CPU, în bucăți cu overlap — trunchiază la ~384 tokeni) pentru nume/adrese; pe buletin (MAJUSCULE) folosim și ancore pe etichete („Nume/Nom”, „Domiciliu”). Dacă la ora 3 GLiNER e slab pe română → regex + listă de nume.
6. **Zone de șablon:** poza, semnătura, MRZ pe buletin sunt mascate pe regiuni fixe ale șablonului, indiferent de OCR.
7. **Normalizare** înainte de etichete și HMAC: majuscule/minuscule, fără diacritice, părțile numelui sortate, ş/ţ (sedilă) → ș/ț (virgulă). `IONESCU MARIA` și `Maria Ionescu` → același `[PERSOANA_1]`. Adresele: amprentă pe componente (localitate + stradă + număr).
8. **Amprentă HMAC-SHA256** cu `HMAC_SECRET` (Arena are cheie separată `ARENA_HMAC_SECRET`).
9. **Seif** (`vault.db`): valori criptate cu `VAULT_KEY` (Fernet). Fără endpoint public.
10. **Imagine redactată:** dreptunghiuri negre pe bbox-uri PII + zonele de șablon. **Imaginile de buletin nu pleacă niciodată în cloud**, nici redactate.
11. **Prompt injection:** detectat local aici (fraze tip „ignoră instrucțiunile”), finding `PROMPT_INJECTION_SUSPECTED`.

### Cifre de control (`paznic/validators.py`)
- **CNP:** 13 cifre `S AA LL ZZ JJ NNN C`. Constanta `279146358279`; Σ(cifră×pondere) mod 11; rest 10 → C=1. S: 1/2 → 1900–1999, 3/4 → 1800–1899, 5/6 → 2000–2099, 7/8 rezidenți străini, 9 cetățeni străini. JJ (județ): 01–46, 51–52, plus 47/48 (fostele sectoare 7–8). Data trebuie să fie validă.
- **IBAN:** primele 4 caractere la final, litere → numere (A=10…), mod 97 == 1. IBAN RO = 24 caractere; caracterele 5–8 = cod bancă (`RZBR` = Raiffeisen, `BTRL` = BT …).
- **CUI:** se elimină prefixul `RO`; 2–10 cifre. Cheia `753217532` aliniată la dreapta pe cifrele fără cifra de control; Σ×10 mod 11; 10 → 0.

### Amprentele — limita lor (spusă onest)
HMAC-ul protejează față de oricine **nu are cheia**. Cine are cheia poate încerca toate valorile posibile (telefoane RO ~10⁸ în secunde, CNP-uri structurate ~4·10⁹ în ore). În producție cheia stă într-un **HSM**, iar Detectivul nu are acces la ea.

### Poarta anti-scurgere (ultimul check înainte de cloud)
În `core/llm.py`, pentru `cloud`: payload-ul e verificat cu regex CNP/IBAN **și** cu potrivire exactă/fuzzy față de **toate valorile din seif pentru dosarul curent**. Orice match → apelul e blocat, finding `PII_GATE_BLOCKED`, intrare în audit.

### Jurnal de audit
`audit_log`: fiecare apel extern (`featherless`, `anaf`) cu `case_id`, destinație, hash payload, nr. etichete, rezultatul porții. Plus fiecare decizie umană (`decided_by`, timp).

### Mod 100% local
`LLM_MODE=local` → tot LLM-ul pe Ollama; ANAF din cache local. Contorul „apeluri externe” rămâne 0.

## 5. Agenții, unul câte unul

```python
class Agent(Protocol):
    name: str
    async def run(self, case: Case, ctx: PipelineContext) -> AgentResult: ...
```
`PipelineContext`: client LLM, `ctx.emit(...)`, acces DB, config, rezultatele anterioare. **Orice lucru CPU-intensiv (OCR, GLiNER, ELA, TenSEAL, randare PDF) se rulează cu `await asyncio.to_thread(...)`**, altfel îngheață SSE-ul și restul API-ului.

### 🛡️ Paznic — Narcis
Vezi §4. Ieșire: text redactat, imagine redactată, `pages` (cu dimensiuni), amprente, finding-uri (checksum, MRZ, injection).

### 📄 Funcționar — Stefan
- Clasifică documentul și extrage câmpurile per tip (`functionar/schemas.py`).
- Fiecare câmp: `{value, source_text}`. **Grounding:** `source_text` trebuie să existe (fuzzy) în textul OCR; altfel `value = null` + finding `EXTRACTION_UNGROUNDED`. Match-ul dă și bbox-ul pentru dovezi.
- LLM-ul întoarce string-uri brute; **Python** parsează sumele în format românesc (`14.200,00`) și datele.
- **Extrasele de cont nu trec rând cu rând prin LLM** (ar sări/inventa rânduri → fals pozitive la sold). Parsare deterministă pe coloane, după coordonatele x din OCR (layout-ul generatorului e cunoscut). LLM doar pentru antet.
- JSON invalid → 1 retry cu eroarea în prompt; apoi `error`.

### 🔍 Verificator — Stefan
**Fluturaș (definiția folosită în proiect, declarată ca simplificare):**
```
G = brut, D = deducere personală (calculată de bancă în clar, apoi criptată)
CAS  = 0,25·G      CASS = 0,10·G
impozit = 0,10·(G − CAS − CASS − D) = 0,10·(0,65·G − D)
net = 0,65·G − 0,10·(0,65·G − D) = 0,585·G + 0,1·D
toleranță: ±2 lei (rotunjiri pe fiecare componentă)
```
„Net” = net **înainte** de alte rețineri (tichete, avansuri, popriri). Generatorul nu emite tichete de masă și evită salariul minim (suma netaxabilă e altă regulă). Deducerea personală reală e pe tranșe (doar pentru brut ≤ salariul minim + 2.000 lei, în funcție de persoanele în întreținere) — pentru demo o tabelă simplificată, spusă deschis.

**Extras:** sold anterior + intrări − ieșiri = sold final, pe fiecare rând; netul de pe fluturaș apare ca intrare de la angajator.

**ANAF:** API-ul public pentru contribuabili (`PlatitorTvaRest` pe `webservicesp.anaf.ro` — **verificați versiunea curentă în documentația ANAF**). Cache local + limită de rată. Existență, activ/inactiv, data înregistrării, denumirea.

**Verificări românești ieftine (dar spectaculoase):**
- data nașterii și sexul din CNP vs câmpurile buletinului vs MRZ;
- vârsta vs angajarea (Maria, 67 de ani, „contabilă” activă?);
- prefixul seriei de buletin (ex. `PH` = Prahova) vs județul din adresă; valabilitatea buletinului vs vârstă;
- codul băncii din IBAN vs banca din antetul extrasului;
- brutul ≥ salariul minim configurat;
- document emis înainte de înființarea firmei.

**Reguli învățate:** motorul de reguli (§8). **HE:** §6.

### 🤖 Detector — Narcis
| Semnal | Implementare | Greutate |
|---|---|---|
| **ELA** | re-salvare JPEG ~q90, diferență, apoi **z-score pe blocuri față de statistica paginii** (altfel orice margine de literă „se aprinde”) | medie–mare pe JPEG; inutil pe poze de telefon și PDF digital |
| **Structură PDF** | update-uri incrementale (mai multe `%%EOF`), font diferit în câmpul sumei, producer, date creare vs modificare | mare |
| **Metadate imagine** | EXIF (Pillow), software de editare | medie |
| **C2PA** | `c2pa-python`, Content Credentials | mare dacă există |
| **AI-detector** | model HF pe crop-ul pozei (zonă de șablon), GPU | **maximum „medium”** — modelele sunt antrenate pe imagini naturale, nesigure pe crop-uri mici; validat pe ~30 de exemple/clasă înainte să-l folosim |

### 🕵️ Detectiv — Erin (P1, backend + graful din frontend)
- Graf `networkx`: noduri = dosare + amprente; muchii = „dosarul folosește amprenta”.
- Semnal: amprentă comună la ≥ N dosare cu **solicitanți diferiți**; IBAN de destinație comun; componente conexe mari.
- Ieșire: cluster-ul dosarului (pentru vizualizare) + `FRAUD_RING_SUSPECTED`.
- Doar amprente, fără acces la seif. Dosarele din Arena sunt excluse.
- `/api/graph?case_id=` întoarce noduri + muchii + clusterul marcat; frontend-ul (react-force-graph) adaugă nodurile live, din evenimentele SSE, și colorează clusterul suspect.
- Rulează pe CPU, fără torch → merge și pe Mac-ul lui Erin.

### ⚖️ Compliance — Samuel
- **Scor:** noisy-OR pe ponderile finding-urilor: `risk = 1 − Π(1 − wᵢ)`. Ponderi în config.
- **Override-uri dure:** CNP invalid, firmă inactivă, MRZ invalid → minim „escalate”.
- **Semnale slabe plafonate:** ELA și AI-detector nu pot depăși singure pragul de respingere.
- **Praguri** alese pe benchmark pentru **0 fals pozitive pe dosarele legitime**.
- „Risc 96%” e un **scor**, nu o probabilitate — așa îl numim în UI.
- **Recomandări:** `clear` (trimis la analiza normală de credit) / `review` / `escalate` (investigație fraudă). Nu există „approve” automat.
- **Rezumatul LLM** e generat **doar din finding-uri**, nu din textul documentului (anti prompt injection).
- **Dezbatere:** la conflict între agenți → evenimente `debate`.
- Raport de anchetă (P2): HTML → PDF.

## 6. Criptare homomorfică

**Model de amenințare (spus onest):** banca are deja datele în clar — HE nu ascunde nimic de bancă. HE permite ca **un verificator terț** (un motor de reguli externalizat, alt departament, o altă instituție) să ruleze verificări pe datele băncii **fără să le vadă**. Fraza de pitch: *„un motor de reguli terț rulează pe datele noastre fără să le vadă vreodată.”*

```
🏦 Banca (cheia secretă)                              🔍 Verificator terț
  ctx = ts.context(CKKS, poly_modulus_degree=8192,
                   coeff_mod_bit_sizes=[60,40,40,60])
  ctx.global_scale = 2**40
  # fără galois keys — nu facem rotații
  g = ts.ckks_vector(ctx, [G1, G2, ...])   # toți brutii din dosar (batch)
  n = ts.ckks_vector(ctx, [N1, N2, ...])
  d = ts.ckks_vector(ctx, [D1, D2, ...])
  trimite ctx.serialize(save_secret_key=False) + g,n,d serializați ──►
                                                     ctx = ts.context_from(bytes)
                                                     diff = g*0.585 + d*0.1 - n
                                              ◄────  diff.serialize()
  decriptează diff → |diffᵢ| > 2 lei → NET_MISMATCH
  rezultatul decriptat NU se trimite înapoi verificatorului
```
- Vectori separați pentru G, N, D → fără rotații, fără galois keys, context mult mai mic.
- CKKS e aproximativ (eroare ~1e-6 la acești parametri) — irelevant la toleranța de 2 lei.
- CKKS dă **confidențialitate, nu integritate**: un verificator rău-intenționat poate întoarce orice. Spunem asta.
- **Nu returnăm niciodată rezultatul decriptat verificatorului** (decriptările CKKS partajate pot scurge cheia — atacul Li–Micciancio).
- UI: dimensiunea contextului, câțiva bytes din ciphertext (ca **ilustrație**, nu dovadă), latența, plus fraza cu modelul de amenințare.
- În demo banca și verificatorul sunt module separate, cu serializare reală între ele.

**Calea minimă (~3h):** `tax.py` în clar + teste → `he_bank.py` (context, criptare batch) → `he_verifier.py` (încarcă contextul public, calculează) → banca decriptează și aplică pragul → UI.

## 7. Dovezi zero-knowledge

**Afirmația:** „Am un venit, semnat de angajatorul meu înregistrat, pentru **această cerere**, iar venitul ≥ pragul cerut.” Banca află doar `true`.

**Pragul** nu e arbitrar: banca îl calculează din rată și limita de grad de îndatorare (DSTI, Regulamentul BNR 17/2012: 40%) → `prag = rata / 0,40`. În pitch spunem deschis că, în realitate, BNR cere venitul exact pentru dosarul de credit — ZK e util pentru **pre-eligibilitate**, înainte ca clientul să-și dea datele.

### Actori
1. **Angajatorul** — **serviciu separat** (alt proces/port, cheia lui privată), nu backend-ul băncii. Pagina „angajator” din demo semnează `H(salariu_bani, case_nonce, perioadă)`. Salariul ajunge doar la angajator (care oricum îl știe) și la client.
2. **Registrul de angajatori** — banca are `CUI → cheie publică`. În realitate: atestare prin sisteme ANAF (REVISAL/D112); în demo: un fișier JSON.
3. **Clientul (browser)** — primește atestarea, generează dovada local (`noir_js` + `bb.js`). Salariul nu pleacă din browser către bancă.
4. **Banca** — emite `case_nonce` (random `Field`) per cerere; la verificare **reconstruiește singură inputurile publice** (prag, cheia angajatorului din registru pentru CUI-ul extras de Funcționar, perioada, nonce) și respinge orice nepotrivire. Nonce-ul se folosește o singură dată (anti-replay).

### Circuit (schiță — numele funcțiilor de verificat pe versiunea fixată de Noir)
```rust
fn main(
    salary_bani: u64,               // privat
    signature: [u8; 64],            // privat
    threshold_bani: pub u64,
    employer_pubkey_x: pub [u8; 32],
    employer_pubkey_y: pub [u8; 32],
    case_nonce: pub Field,
    period: pub u32,
) {
    let msg = hash_fixed_layout(salary_bani, case_nonce, period); // blake2s sau sha256
    assert(ecdsa_secp256k1_verify(employer_pubkey_x, employer_pubkey_y, signature, msg));
    assert(salary_bani >= threshold_bani);
}
```

### Hash identic în Python și Noir
Layout fix: `salary_bani` (8 bytes big-endian) ‖ `case_nonce` (32 bytes) ‖ `period` (4 bytes) → `blake2s` (sau sha256, ce oferă versiunea fixată). Python: `hashlib.blake2s` + `ecdsa` cu `sign_digest(..., sigencode=sigencode_string_canonize)` (low-S, semnătură `r‖s` de 64 bytes). **Vector de test scris în prima oră.**

### Browser și verificare
- Proving **single-threaded** (circuit mic) → nu avem nevoie de headerele COOP/COEP pe Vercel.
- Vite: `@noir-lang/*` și `@aztec/bb.js` excluse din `optimizeDeps`.
- `nargo`, `noir_js`, `bb.js` cu versiuni **compatibile, fixate** în `zk/README.md`.
- Verificarea: script **Node cu aceeași versiune de bb.js**, apelat din `/api/zk/verify` (nu CLI `bb` — poate avea alt format). Verificarea în browser-ul clientului nu înseamnă nimic pentru bancă.

### Fallback (dacă semnătura în circuit nu merge până la ora 3,5)
Angajatorul semnează ECDSA un commitment `C = H(salary, salt, nonce)`; **Python verifică semnătura normal**, în afara circuitului; circuitul dovedește doar că știi `salary, salt` pentru `C` și `salary ≥ threshold`. La fel de solid, mult mai simplu.

### Calea în 5h
1. Ora 1: versiuni fixate; circuit doar cu `salary >= threshold`, dovadă în browser, verificare în Node.
2. Ora 2–3: serviciul angajatorului (Python ECDSA + blake2s), registrul, vectorul de test.
3. Ora 3: `case_nonce` + verificarea semnăturii în circuit (sau fallback la 3,5).
4. Ora 4: `/api/zk/verify` — verificare Node + inputuri publice reconstruite + cheie din registru + nonce nefolosit + perioadă recentă.
5. Ora 5: demo — salariul nu pleacă din device; semnătură falsă și prag modificat → respinse.

## 8. Self-learning și motorul de reguli

**Proprietari:** Samuel (propunere, backtest, aprobare, legătura cu Arena) · Stefan (evaluarea regulilor aprobate în Verificator).

LLM-ul **nu scrie cod executabil** (ar fi injecție de cod într-un sistem bancar). Propune reguli într-un DSL limitat, evaluat de un motor cu operatori din whitelist.

```json
{
  "id": "rule_017",
  "status": "proposed",
  "description": "Data documentului trebuie să fie după data înregistrării firmei la ANAF",
  "applies_to": ["payslip", "employment_certificate"],
  "when": { "all": [ { "left": "doc.issue_date", "op": "lt", "right": "company.registration_date" } ] },
  "then": { "code": "DOC_BEFORE_COMPANY", "severity": "high", "message": "Document emis înainte de înființarea firmei" },
  "origin": { "type": "arena", "submission_id": "sub_88", "created_by": "llm" },
  "backtest": { "cases": 214, "true_positives": 9, "false_positives": 0, "fp_rate": 0.0 }
}
```
- Operatori: `eq, ne, lt, lte, gt, gte, between, in, not_in, exists, missing, abs_diff_gt, ratio_gt, regex`. Regex prin pachetul `regex` cu `timeout=` (modulul standard `re` nu are timeout).
- Câmpuri doar din catalogul schemei extrase (`doc.*`, `company.*`, `statement.*`, `case.*`).

**Bucla:**
1. Declanșator: omul corectează un verdict sau un fals din Arena trece.
2. LLM-ul primește **doar** datele extrase structurate + finding-urile + catalogul de câmpuri (nu text liber din document) → propune 1–3 reguli.
3. Validare de schemă și câmpuri.
4. Backtest pe setul **dev** (nu pe test!): respinsă automat dacă are FP pe dosare legitime sau nu prinde cazul declanșator.
5. Aprobare umană → `approved`.

## 9. Arena

### Mecanica — „Forge Studio” (nu editezi poze pe telefon)
- Jucătorul alege o misiune („fluturaș de minim 9.000 lei net care să treacă”).
- Pagina arată șablonul + **câmpuri editabile** (net, brut, angajator, dată) + **„trucuri”**: „recalculează taxele”, „schimbă poza cu una generată AI”, „ascunde un text de injection”, „schimbă firma”.
- **Backend-ul aplică modificările peste JPEG-ul original** cu generatorul Lorenei (re-compresie reală → ELA are semnal) și știe exact ce s-a modificat → feedback precis.
- Mod „pro” (laptop): upload de fișier.

### Scor
- Puncte doar dacă **ținta misiunii e atinsă** (ex. net ≥ 9.000) **și** documentul diferă de șablon.
- Deduplicare pe hash; plafon de puncte per pseudonim.
- Prins → jucătorul vede *de ce* (motivează să revină). Trecut → puncte mari + declanșează self-learning („acest fals a devenit regula #18”).
- **Feedback-ul „de ce” e un oracol pentru atacatori** → Arena e explicit un **sandbox de red-team**, separat de sistemul real.

### Debit și protecții
- Arena rulează cu **LLM cloud și `DETECTOR_GPU=off`** (GPU-ul rămâne pentru dosarele băncii). Telefonul arată poziția în coadă + pașii agenților live în timp ce așteaptă.
- Fișiere (mod pro): PNG/JPG/PDF, max 5 MB, max 3 pagini, magic bytes; parsarea în subproces cu timeout și limită de memorie.
- Rate limit 5/min/IP; ID-uri de trimitere neghicibile.
- SSE public pentru o trimitere = **proiecție whitelisted** (status, agent, cod finding, mesaj) — fără text redactat, amprente sau `data`.
- Pseudonime filtrate (lungime, caractere, cuvinte vulgare) înainte de ecranul mare.
- Fișierele din Arena se șterg după scorare (TTL 24h); nu intră în seif, în graful Detectivului sau în statisticile băncii.
- Mesaj vizibil: **„Nu încărcați documente reale.”**

### Ecranul de proiector (`/arena/live`)
QR mare + URL scurt, feed live, top 10, plus un grafic pe runde „AI atacator vs AI apărător”.

### Atacatorul (P2, Samuel)
Un **fuzzer** (fără LLM — Claude a refuzat rolul de falsificator, iar un algoritm e oricum repetabil și instant): alege câmpuri și trucuri din Forge Studio, citește codurile dovezilor care l-au prins și evită ce l-a dat de gol. Ce trece declanșează self-learning (Claude Opus) → apărătorul învață. Pe ecran: rata de falsuri care trec, pe runde. `POST /api/admin/attacker/start {rounds, auto_approve}`.

### Dacă nu joacă nimeni
**Dacă nu joacă nimeni:** clasamentul e populat cu rulările pregătite de echipă, Atacatorul poate fi pornit din admin, un coleg joacă live de pe un telefon proiectat.

## 10. Frontend

**Stack:** React + Vite + TypeScript + Tailwind + **shadcn/ui** (componente gata), **TanStack Query** (snapshot-uri), **Recharts** (dashboard), **react-force-graph** (graf), `@microsoft/fetch-event-source` (SSE cu headere).

**Ecrane obligatorii (P0/P1):**
1. **Dosar** — documentul cu 3 vederi (original / „ce a văzut AI-ul” / harta ELA), bbox-uri peste imagine, lista de finding-uri, verdictul, butoanele de decizie, **banda „biroului” cu agenții** live.
2. **Arena pe mobil** (Forge Studio) + **`/arena/live`** pe proiector.
3. **Dashboard** — 4 carduri de cifre + 1 grafic.

**Opționale (P2):** pagină separată de Birou animat, hartă, pagina de reguli. **Pagina ZK** o face Lorena.

**State:** un reducer per dosar, cheiat pe `seq` (ignoră duplicate), reconectare cu `Last-Event-ID`, snapshot din TanStack Query la încărcare.

**Mock / replay:** `shared/fixtures/maria_events.jsonl` — dosarul Mariei înregistrat ca evenimente cu timpii originali, redat cu aceleași întârzieri. Același fișier servește pentru dezvoltare, fallback offline și video de rezervă.

**URL-ul API-ului:** din `?api=` (salvat în localStorage), apoi `VITE_API_URL`. Așa schimbarea tunelului nu cere redeploy.

**Proiector și accesibilitate:** text ≥ 20–24 px, contrast mare, riscul cu iconiță + etichetă (nu doar roșu/verde), o singură limbă în UI și pitch. Pagina de mobil: fără hover, butoane mari, < 200 KB, QR testat din ultimul rând.

## 11. Dashboard și metrici

| Metrică | Formula | Sursă |
|---|---|---|
| Dosare procesate | count | DB |
| Timp economisit | dosare × (min_manual − min_review) | `MANUAL_MINUTES_PER_CASE` (**de confirmat cu mentorii Raiffeisen**), `REVIEW_MINUTES_PER_CASE` |
| Bani economisiți | ore × cost/oră | `COST_PER_HOUR_RON` |
| Fraude oprite / sumă oprită | dosare `escalated`/`rejected` cu motiv fraudă | DB |
| Date personale protejate | nr. etichete | Paznic |
| Apeluri externe cu PII | **0** (blocate de poartă) | audit_log |
| Rata de scurgere PII pe benchmark | valori PII cunoscute găsite în payload-uri / total | benchmark |
| Cost AI | Σ `llm_usage.cost_usd` | config prețuri |
| Reguli învățate | count `approved` | DB |
| Precizie / recall | pe setul **test** | `scripts/benchmark.py` |

Valorile presupuse se afișează ca **presupuneri configurabile**, nu ca fapte.

## 12. API și autentificare

### Autentificare
- UI-ul băncii: ecran de login unde se lipește `BANK_UI_TOKEN` → **sessionStorage**. Tokenul **nu** e în variabile `VITE_*` (ar ajunge în bundle-ul public).
- SSE prin `fetch-event-source` (trimite `Authorization`). Imaginile se iau cu `fetch` + blob (sau URL-uri semnate de 60 s). Fără tokeni în query string (ajung în loguri).
- Deciziile poartă `decided_by` (numele introdus la login) → atribuire + posibilitate de „4 ochi”.
- `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` când `ENV=demo`.

### Endpoint-uri (`/api`) — ✅ implementat · ⏳ de făcut
| Metodă | Endpoint | Descriere | Acces |
|---|---|---|---|
| ✅ GET | `/health` | stare | public |
| ✅ POST | `/api/cases` | upload multipart (1–5 fișiere) → `{case_id}`, pornește pipeline-ul | bancă |
| ✅ GET | `/api/cases` · `/api/cases/{id}` | listă / dosar complet | bancă |
| ✅ GET | `/api/cases/{id}/events` | SSE (replay de la `Last-Event-ID`) | bancă |
| ✅ GET | `/api/cases/{id}/documents/{doc_id}/image?view=original\|redacted\|ela&page=1` | imagini (PDF → PNG); `redacted`/`ela` după ce le salvează Paznic/Detector | bancă |
| ✅ POST | `/api/cases/{id}/decision` | `{action: clear\|reject\|escalate\|flag_network\|correct, decided_by, notes}` → Decision | bancă |
| ✅ GET | `/api/cases/{id}/report` | raport de anchetă HTML (printabil ca PDF) | bancă |
| ✅ GET | `/api/events` | SSE global (doar ID-uri + stări) | bancă |
| ✅ GET | `/api/dashboard/stats` · `/api/audit` | metrici / jurnal | bancă |
| ✅ GET/POST | `/api/settings` | `llm_mode`, `he_enabled` (butoanele din UI) | bancă |
| ✅ GET | `/api/rules` · POST `/api/rules/{id}/approve\|reject` · POST `/api/rules/learn/{submission_id}` | self-learning | bancă |
| ✅ GET | `/api/arena/missions` | misiuni + șabloane + câmpuri editabile | public |
| ✅ POST | `/api/arena/submissions` | `{nickname, mission_id, edits, tricks}` (JSON) | public, rate-limited |
| ✅ GET | `/api/arena/submissions/{id}` · `/image` | rezultat + „de ce” · falsul generat | public |
| ✅ GET | `/api/arena/leaderboard` · `/api/arena/live` (SSE) | clasament + feed | public |
| ✅ POST | `/api/admin/rerun-demo` · `seed-demo` · `seed-arena` · `reset` · `attacker/start` · GET `attacker/status` | demo | admin |
| ⏳ GET | `/api/graph?case_id=` | noduri + muchii (Erin, cu Detectivul) | bancă |
| ⏳ GET | `/api/cases/{id}/he-preview` | ciphertext ilustrativ (Stefan) | bancă |
| ⏳ POST | `/api/zk/nonce` · `/api/zk/verify` | ZK (Lorena) | public |

Serviciul angajatorului (`/employer/attest`) rulează **separat**, cu cheia lui.

## 13. Clientul LLM: bedrock / cloud / local / mock

### Cele patru moduri

| Mod | Ce | Client | Când |
|---|---|---|---|
| `bedrock` | **Claude pe AWS Bedrock** (Haiku 5.5 / Sonnet 5.5 / Opus 5.5) | SDK-ul Anthropic, `AsyncAnthropicBedrock` | principalul, cât timp e valabilă cheia (setați `LLM_MODE=bedrock`; implicitul din cod e `mock`) |
| `cloud` | Featherless (DeepSeek, Qwen) | SDK `openai` cu `base_url` | după ce expiră cheia Bedrock; teste ieftine |
| `local` | Ollama (Qwen ~4B) | SDK `openai` cu `base_url` local | butonul „mod 100% local” |
| `mock` | răspunsuri salvate | — | frontend, CI, demo fără internet |

**Bedrock — testat pe 2026-10-28:** cheia de la organizatori (`AWS_BEARER_TOKEN_BEDROCK`) merge în `us-west-2` cu profilurile `us.anthropic.claude-haiku-5-5`, `us.anthropic.claude-sonnet-5-5`, `us.anthropic.claude-opus-5-5` (apel Converse, `Authorization: Bearer <cheie>`, endpoint `https://bedrock-runtime.us-west-2.amazonaws.com/model/<id>/converse`). În cod: **SDK-ul oficial Anthropic, clientul `AsyncAnthropicBedrock(api_key=<cheia bearer>, aws_region="us-west-2")`**, cu ID-urile `us.anthropic.claude-*` — testat, merge. (`AnthropicBedrockMantle` dă 404 pe contul organizatorilor.) Implementare: `backend/app/core/llm.py`; ghid de folosire: `backend/README.md`.

**⚠️ Cheia expiră după 12h** (emisă 2026-10-28 09:21 UTC → expiră ~21:21 UTC, adică ~23:21 ora României). Hackathonul durează 24h → **cereți o cheie nouă organizatorilor înainte de demo**; altfel `LLM_MODE=cloud`. Clientul trece automat pe Featherless la eroare 403 de la Bedrock și scrie asta în audit.

**Ce model folosește fiecare agent (în modul `bedrock`):**

| Agent / sarcină | Model | De ce |
|---|---|---|
| Funcționar (extragere text + imagini) | Haiku 5.5 | rapid, ieftin, bun la extragere și imagini |
| Arena (volum mare) | Haiku 5.5 | multe cereri |
| Compliance (rezumat din dovezi) | Sonnet 5.5 | raționament bun, latență mică |
| Self-learning (propunere de reguli) | Opus 5.5 | puține apeluri, calitatea contează |

**Notă pentru pitch:** cheia de demo e în regiunea SUA (`us-west-2`). În producție: Bedrock într-o regiune UE (ex. Frankfurt) sau complet on-prem — spunem asta explicit.

```python

async def chat(messages, *, task: str, case_id: str, json_schema=None, images=None) -> LLMResponse:
    # 1. mode = settings.llm_mode (schimbabil live): bedrock | cloud | local | mock
    # 2. mock / DEMO_CACHE → cache cheiat pe (sha256 fișier + task), nu pe hash(messages)
    # 3. bedrock / cloud → poarta anti-PII (regex + valorile din seif pentru case_id); blochează la match
    # 4. semafor global, timeout, 2 retry cu backoff
    # 5. audit_log + cost
    # 6. modul "record" salvează în cache (și OCR + ieșirea Paznicului)
```
- Modele per task din config (`BEDROCK_MODEL_*`, `MODEL_EXTRACT`, `MODEL_REASON`, `MODEL_VISION`, `MODEL_LOCAL`). **Ora 1: confirmați numele exacte pe Featherless și că modelul vizual chiar acceptă imagini.**
- Claude (Haiku/Sonnet/Opus 5.5) are gândirea adaptivă pornită; efortul se setează per sarcină (`low` pentru extragere, `medium`/`high` pentru Compliance și self-learning). Nu folosiți `temperature`/prefill — modelele noi le resping.
- `LLM_MAX_CONCURRENCY` (implicit 2) — modelele mari Featherless costă 4 unități de concurență.
- Structured output: cerem JSON + validare Pydantic; fallback „răspunde DOAR cu JSON” + extragere robustă.
- **Ollama:** `num_ctx: 8192` (implicitul trunchiază silențios!), `temperature: 0`, `format` cu schema JSON, modul „thinking” al Qwen oprit. Prompturile se testează și pe `local`.
- Cache-ul (`data/llm_cache/`) conține prompturi → doar local, în `.gitignore`.

## 14. Concurență, GPU și performanță

- **Event loop:** tot ce e CPU-bound → `asyncio.to_thread`. Task-urile pornite cu `create_task` se țin într-un set (altfel pot fi colectate de GC).
- **SQLite:** mod WAL, `check_same_thread=False`. Starea pipeline-ului și evenimentele stau **în memorie**; dosarul se scrie în DB la finalul fiecărui agent, sub un lock async.
- **GPU (RTX 4060, 8 GB):**

| Ce | VRAM aprox. |
|---|---|
| Qwen ~4B cuantizat (Ollama, ctx 8k, cu KV cache) | ~3,5–4 GB |
| Context CUDA per proces + Windows/desktop | ~1–1,5 GB |
| AI-detector | ~0,5–1 GB |
| GLiNER | **pe CPU** (eliberează VRAM) |

  Încape, dar la limită. Fără modele de 8–9B în paralel. Semaforul din Python nu coordonează cu Ollama (alt proces) — de aceea Arena nu folosește GPU-ul.
- Modelele se încarcă **lazy** și se încălzesc cu `scripts/warmup.py`; `OLLAMA_KEEP_ALIVE=-1`.
- La demo: uvicorn **fără** `--reload`, un singur worker.
- Ținte: dosar < 15 s (`cloud`), < 40 s (`local`).

## 15. Deploy

```
Demo pe scenă:   frontend servit LOCAL pe laptopul lui Narcis (vite preview) → backend localhost
                 → butonul „mod local” + cablul scos funcționează (nu depinde de internet)
Arena publică:   Vercel (frontend) → tunel → backend pe laptopul lui Narcis
```
- **Tunel:** preferat **ngrok cu domeniul static gratuit** (URL fix). Cloudflare Quick Tunnel: URL-ul se schimbă la fiecare repornire și **probabil nu suportă SSE** — de verificat în prima oră de pe un telefon. Cu ngrok, frontend-ul trimite headerul `ngrok-skip-browser-warning`.
- **Fallback la SSE:** polling `GET /api/cases/{id}` la 1 s.
- **CORS:** `allow_origin_regex=r"https://.*\.vercel\.app"` + `localhost:5173/4173`.
- **Vite:** `envDir: '..'` sau `frontend/.env` separat (Vite nu citește `.env` din rădăcină).
- **Ollama:** pe același laptop cu backend-ul → ascultă pe `127.0.0.1` (nu `0.0.0.0` pe Wi-Fi-ul de la hackathon).
- **Windows (Narcis):** Tesseract (UB Mannheim) cu limba română bifată + `TESSERACT_CMD`; aplicația Ollama din tray ocupă deja portul 11434 → `OLLAMA_HOST`/`OLLAMA_KEEP_ALIVE` ca variabile de mediu ale utilizatorului + restart la tray + regulă de firewall; ngrok/cloudflared prin `winget`; `uvicorn --reload --reload-dir app` în dezvoltare.
- **Planul B:** al doilea laptop cu `requirements-core.txt`, `LLM_MODE=cloud`, `DETECTOR_GPU=off`. (Docker cu torch pe Wi-Fi-ul de la hackathon nu e realist.)
- Deploy-ul și tunelul sunt ale lui **Narcis** (e mașina lui).

## 16. Securitate

- **Secrete:** doar în `.env`; aplicația **refuză să pornească** dacă `HMAC_SECRET`, `VAULT_KEY` sau `BANK_UI_TOKEN` lipsesc sau încep cu `#`.
- **Originalele** se salvează criptate cu `VAULT_KEY`; servite doar prin ruta auditată.
- **Upload:** magic bytes, limită de dimensiune și de pagini, nume UUID, în afara folderului static; Pillow `MAX_IMAGE_PIXELS`; PDF doar randat (`pypdfium2`), fără JS; parsarea în subproces cu timeout/limită de memorie.
- **Erori:** mesaje generice + ID de corelare în `AgentResult.error` și SSE; detaliile doar în logul local.
- **Prompt injection:** detectat local în Paznic; Compliance și self-learning nu văd text liber din document; LLM-ul nu decide.
- **Arena:** proiecție whitelisted, cheie HMAC separată, rate limit, TTL.
- **Ollama** doar pe `127.0.0.1`. Docs FastAPI dezactivate în demo.

## 17. Reglementare — cum ne poziționăm

- **AI Act:** scoringul de credit e sistem cu risc ridicat (Anexa III 5(b)), dar **sistemele de detectare a fraudei financiare sunt excluse explicit**. ORB = **detectare de fraudă și verificare documente**, nu scoring de credit. Recomandarea e `clear / review / escalate`, nu „aprobă creditul”.
- **GDPR art. 22:** omul decide efectiv (vede dovezile, poate contrazice, decizia are `decided_by`); nu e „ștampilă”.
- **„Blochează rețeaua”** → în realitate **„marchează pentru investigație”**: ceilalți solicitanți din rețea pot fi și ei victime.
- **SMS-ul către Maria** se trimite pe datele de contact **din evidențele băncii**, nu pe telefonul din cerere (care e al escrocului).
- **Secret bancar / DORA / EBA outsourcing:** producție = LLM local/on-prem; Featherless doar pentru demo pe date sintetice.

## 18. Date de test și benchmark

Lorena, `data/`:
- **Generator:** Python + Pillow + fonturi; buletin, fluturaș, extras, adeverință, cu CNP/IBAN/CUI **valide matematic** dar inventate, MRZ corect. Salvate ca JPEG (și PDF digital pentru verificările structurale).
- **Rețeta de fals pentru ELA:** randare → JPEG q≈75 → editarea zonei sumei → JPEG q≈92. (O singură re-salvare a întregului document nu dă semnal.)
- **Etichete:** `.json` lângă fiecare document (legit / tip fals / câmp modificat / **toate valorile PII**).
- **Tipuri de falsuri:** (1) sumă modificată fără taxe refăcute; (2) sumă modificată cu taxe refăcute (prins de ELA/extras/ANAF); (3) firmă inexistentă/inactivă; (4) CNP cu checksum greșit; (5) sold care nu se adună; (6) poză înlocuită/generată AI; (7) date incoerente (doc înainte de firmă, vârstă vs angajare, serie buletin vs județ); (8) prompt injection — **vizibil cu contrast mic** (textul alb e invizibil pentru OCR) sau în stratul de text PDF; (9) rețea: aceleași telefon/IBAN/adresă pe identități diferite; (10) MRZ care nu se potrivește cu fața buletinului.
- **Copii degradate:** rotație, blur, JPEG, zgomot — ca să vedem cât rezistă.
- **Split dev/test:** self-learning și pragurile se aleg pe **dev**; cifrele din pitch vin de pe **test**.
- **Benchmark:** recall per tip de fals, fals pozitive pe legitime, timp, cost, **rata de scurgere PII** (generatorul știe toate valorile PII → le căutăm în textul redactat și în payload-uri). „0 scurgeri în N documente” e o cifră puternică pentru pitch.
- **Scenariul de demo** (`data/demo/`): Maria + rețeaua de 6 + 10 legitime + cazuri-limită.
- **Prima versiune brută a documentelor Mariei: până la ora 2** (toți depind de ea).

## 19. Testare și CI

- `backend/tests/test_smoke.py`: în `mock`, dosarul Mariei ajunge la `awaiting_review` cu `escalate`. Trebuie să treacă înainte de orice merge.
- Teste unitare: `validators.py` (CNP/IBAN/CUI/MRZ), `tax.py`, motorul de reguli, vectorul de test ZK.
- Test că `models.py` → JSON schema se potrivește cu `shared/schemas/`.
- GitHub Action: `requirements-core.txt` + `ruff` + `pytest` la fiecare push. `main` protejat.

## 20. Structura repo-ului

```
hackathon-project/
├── README.md · ARCHITECTURE.md · .env.example · .gitignore
├── .github/workflows/ci.yml
├── shared/
│   ├── schemas/                 contractul JSON
│   └── fixtures/                maria_case.json, maria_events.jsonl
├── backend/
│   ├── requirements-core.txt    pentru toată lumea (fără torch)
│   ├── requirements-ml.txt      doar pe laptopul cu GPU (torch, gliner, tenseal, c2pa)
│   ├── app/
│   │   ├── main.py · config.py · models.py
│   │   ├── api/                 rute                                   [Samuel]
│   │   ├── core/                pipeline, events, llm, db, audit        [Samuel]
│   │   ├── agents/
│   │   │   ├── base.py                                                  [Samuel]
│   │   │   ├── paznic/          ocr, validators, mrz, gliner, vault     [Narcis]
│   │   │   ├── detector/        ela, pdf_structure, metadata, c2pa, ai  [Narcis]
│   │   │   ├── functionar/      prompts, schemas, grounding, statement  [Stefan]
│   │   │   ├── verificator/     tax, statement, anaf, ro_checks, he     [Stefan]
│   │   │   ├── detectiv/        graph, clusters, scoring                [Erin]
│   │   │   └── compliance/      scoring, summary, report                [Samuel]
│   │   ├── learning/            engine (reguli JSON), proposer (LLM + backtest) [Samuel; în Verificator: Stefan]
│   │   ├── arena/               missions, forge, judge, service, attacker, ratelimit [Samuel]
│   │   └── zk/                  nonce, verify bridge                    [Lorena]
│   └── tests/
├── employer/                    serviciul separat al angajatorului (ZK)   [Lorena]
├── frontend/                    React + Vite + TS + Tailwind + shadcn    [Erin; pagina ZK: Lorena]
├── zk/                          circuite Noir, verificator Node, versiuni [Lorena]
├── data/
│   ├── generator/ [Lorena] · attacker/ [Samuel] · demo/
│   └── llm_cache/               local, ignorat de git
└── scripts/                     benchmark, seed, warmup
```
