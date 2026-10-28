# Note pentru Narcis

## 1. Paznicul e în `main`, cu modificări: dă `git pull`
PR #4 îmbinat. L-am testat pe pozele reale ale Mariei (cu Tesseract) și am reparat câteva scurgeri
(commit `52561b6`, fișierele `agents/paznic/detect.py`, `agent.py`, `vault.py`):
- **MRZ:** OCR-ul pune spații între `<<<`, iar rândul 2 TD2 are un singur `<` → acum potrivim pe linia
  compactată (fără spații, `«` → `<`), cu minimum un `<` și lungime ≥ 30.
- **Nume fără eticheta „Nume”** („Beneficiar: IONESCU MARIA” în extras) → două faze: întâi citim toate
  documentele și strângem numele, apoi le ascundem oriunde apar (`detect.find_known_names`).
- **CNP / telefon cu separatori** („259 031 229 0171”, „+40 722 318 405”) → prinse (CNP doar cu cifra de control validă).
- **Seria buletinului fără „SERIA”** → prinsă doar pe buletin (`looks_like_id_card`); „NR”/„RO” excluse.
- **Locul nașterii** → tratat ca adresă.
- Seiful se înregistrează în poarta anti-PII pe event loop, nu din thread (`vault.put(..., register=False)`).

Rezultat pe dosarul Mariei: 0 date personale în ieșirea API, 0 apeluri AI blocate. Teste noi în
`tests/test_paznic_agent.py::test_ocr_noise_and_names_outside_labels_are_redacted`.

Ce a mai notat review-ul și NU e reparat (de văzut când ai timp):
- zonele de mască de pe buletin (`images.py`) acoperă și text (numele de la x=440) → afectează grounding-ul;
  coordonatele reale sunt în `data/generator/build_demo.py` (`id_card`);
- adresa „Str. Florilor nr. 12, Ploiești, jud. Prahova” vs „Str. Florilor 12 Ploiesti” → amprente diferite
  (fără județ în normalizare ar merge);
- nu există amprentă pentru serie+număr buletin (buletin refolosit în mai multe dosare = semnal bun pentru Detectiv);
- fără Tesseract, registry-ul trece pe stub și dosarele reale ar primi datele Mariei → ok pentru demo, nu pentru „producție”.

## 2. Detectorul: singurul agent rămas de probă
De prins pe documentele Mariei (adevărul în `data/demo/maria/truth.json`):
- zona editată din `fluturas.jpg` (netul, `net_bbox`) și din `extras.pdf` (soldul final, `balance_bbox`);
  documentele sunt făcute cu rețeta ELA (JPEG q75 → zonă editată → JPEG q92);
- producer-ul `GIMP 2.10.38` din metadatele PDF-ului.
Imaginea ELA: `files.save_derived(case.id, doc.id, "ela", page, png)` → apare la `?view=ela`.
Cine scrie ce: `backend/README.md`. Semnalele slabe (ELA, AI-detector) sunt plafonate în Compliance.

## 3. Modul local (Ollama)
`.env`: `LLM_MODE=local`, `MODEL_LOCAL=<modelul Qwen ~4B>`, `OLLAMA_URL=http://127.0.0.1:11434`.
Apoi `POST /api/admin/rerun-demo` și notează cât durează + dacă rezumatul verdictului arată ok.
Pe Windows: `OLLAMA_KEEP_ALIVE=-1` ca variabilă de mediu, restart la Ollama din tray.

## 4. Deploy (laptopul tău = serverul băncii)
ngrok cu domeniu static gratuit → testat SSE de pe telefon (`/api/arena/live`). Până la integrarea #2 (~ora 16).

## 5. CORS pentru telefoane (din review-ul Arenei)
Implicit backend-ul acceptă doar `localhost:5173/4173` + `*.vercel.app` (`CORS_ORIGINS`, `CORS_ORIGIN_REGEX` în `.env`).
Dacă Arena se servește de pe alt domeniu (ngrok, IP din rețea), adaugă-l în `CORS_ORIGINS`, altfel telefoanele primesc eroare.
Testează la deploy: deschide Arena de pe un telefon pe date mobile (nu pe Wi-Fi-ul hackathonului).
