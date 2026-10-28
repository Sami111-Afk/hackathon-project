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
