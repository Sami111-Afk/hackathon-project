# Lorena — schimbare de rol (28.10, ~14:00)

**ZK-ul l-am preluat noi (Samuel)** — ca să fie gata la timp. E deja pe `main` și merge cap-coadă:
circuit Noir, angajator care semnează (ECDSA), bancă cu nonce de unică folosință, verificare cu `bb`, 11 teste.
Detalii: `zk/README.md` și `ARCHITECTURE.md` §7. Nu mai trebuie să instalezi nargo/bb dacă nu vrei.

## Ce rămâne la tine
1. **Ramura `lorena/p0-generatoare-date`** (validatorul MRZ `mrz_td2_valid`) — e corectă, am testat-o. **Deschide PR** din ea.
2. **Set de benchmark cu degradări realiste** (`data/generator/`): copii ale documentelor ca „poze de telefon” —
   rotație mică (±3°), blur, JPEG q 60–80, umbră/gradient de lumină, zgomot. Plus tipurile de fals din `ARCHITECTURE.md` §18
   (sumă modificată cu/fără taxe refăcute, sold care nu se adună, CNP cu checksum greșit, date incoerente).
   Fiecare document cu `.json` de etichete lângă el (legit/fals, ce s-a modificat, valorile PII).
   `scripts/benchmark.py` le poate folosi ca să arătăm cât rezistă OCR-ul și regulile. **Doar date inventate** (CNP cu `000`, IBAN sucursala 9999, CUI-urile din `app/arena/missions.py`).
3. **Pagina ZK din frontend** (vorbește cu Erin unde o pune în meniu): un formular — salariu net, rată, angajator, atac —
   care cheamă `POST /api/zk/demo` și afișează `steps` ca o cronologie (bancă → angajator → client → bancă) + răspunsul mare DA/NU
   + „ce a văzut banca” (`bank_saw`: doar commitment și dimensiunea dovezii, fără salariu). Exemplu de cerere:
   ```json
   {"net_salary_ron": 8307, "installment_ron": 2500, "cui": "RO9341910290", "period": "2026-09", "attack": "none"}
   ```
   Atacuri de arătat: `lie_salary`, `lower_threshold`, `fake_signature`, `replay` — toate trebuie să dea NU.
   Ruta cere `Authorization: Bearer <BANK_UI_TOKEN>` (ca restul paginilor de bancă) + header-ul `ngrok-skip-browser-warning: 1`.
4. (după 18:00) slide-urile și scenariul de demo împreună cu noi.

## Review PR #29
PR-ul e îmbinat (233 teste trec, fără conflicte cu main, fără fișiere binare adăugate: doar `phone.py` și `benchmark_pipeline.py`). Observații minore:
- `--phone` (n=12, mock): scurgeri de PII în 4/12 dosare (NR_BULETIN, IBAN, STRADA, MRZ) față de 0/12 la clean. Redactarea ratează când OCR-ul citește prost. Cifra e reală și trebuie spusă onest în pitch, nu ascunsă.
- Degradarea pare cam agresivă: extragerea scade la brut 4/12, sold 4/12, expirare 5/12 (clean: 12/12). Merită testat cu blur și zgomot mai mici, ca să se vadă și un caz „poză decentă”.
- Falsuri prinse în phone: forged_net 1/3, forged_balance 1/2 (clean: 3/3 și 2/2); cinstiți loviți 1/3 (MRZ_INVALID din OCR).
- `prompt_injection` (text gri #b4b4b4) dă 0/1 și pe clean: ori OCR nu citește textul, ori Paznicul nu îl prinde. De verificat înainte să-l prezentăm ca tip de fals acoperit.
- `--extra-fakes` clean: bad_cnp, mrz_mismatch, doc_before_company prinse 1/1 fiecare.
- Ruff trece cu configul din `backend/`; rulat din rădăcină, `benchmark_pipeline.py` dă I001 (ordinea importurilor), nu blochează.
- Rezultatele nu sunt comise în PR; `data/benchmark/pipeline_results.json` trebuie regenerat dacă vrem cifrele phone în repo.

## Review PR #35 (slide-uri) — Samuel, ~16:30
Merge făcut. Varianta **EN** (cea pe care o predăm) e aliniată cu `notes/pitch.md` — bravo. Varianta lungă **RO** are câteva
lucruri vechi, de corectat doar dacă o folosim: „scor de risc 96” (acum arătăm *nivelul* de risc), „AI contra AI” (atacatorul e
un algoritm automat, nu AI), cost „~0,0006 $” (acum ~0,005 $/dosar cu Bedrock), „~15 secunde” / „240 de documente” (acum: ~12–20 s;
benchmark cu AI real pe 60 de dosare, vezi `notes/pitch.md`).
