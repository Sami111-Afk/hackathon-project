# Note pentru Narcis

## 1. Paznicul e în `main`, cu modificări: dă `git pull`
PR #4 îmbinat. L-am testat pe pozele reale ale Mariei (cu Tesseract) și am reparat câteva scurgeri
(commit `52561b6`, fișierele `agents/paznic/detect.py`, `agent.py`, `vault.py`):
- **MRZ:** OCR-ul pune spații între `<<<`, iar rândul 2 TD2 are un singur `<` → acum potrivim pe linia
  compactată (fără spații, `«` → `<`), cu minimum un `<` și lungime ≥ 30.
- **Nume fără eticheta „Nume”** („Beneficiar: IONESCU MARIA” în extras) → două faze: întâi citim toate
  documentele și strângem numele, apoi le ascundem oriunde apar (`detect.find_known_names`).
- **CNP / telefon cu separatori** („259 031 229 0171”, „+40 700 000 001”) → prinse (CNP doar cu cifra de control validă).
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

## 6. Deploy: ngrok (tu) + Vercel (Erin) — pașii
1. Cont gratuit pe ngrok.com → ia **domeniul static gratuit** (URL fix, `ceva.ngrok-free.app`). Fix = Erin nu trebuie
   să refacă deploy-ul pe Vercel la fiecare repornire.
2. Pe laptopul tău: backend pornit (`ENV=demo`, fără `--reload`), apoi `ngrok http --url=<domeniul-tău> 8000`.
3. **Dă-i lui Erin URL-ul** (pune-l și pe grup). Ea îl setează pe Vercel ca `VITE_API_URL`.
4. `.env`: `CORS_ORIGINS` — domeniul Vercel e deja acoperit de `CORS_ORIGIN_REGEX=https://.*\.vercel\.app`;
   adaugă în `CORS_ORIGINS` doar alte adrese (ex. `http://localhost:4173` pentru demo local).
5. Test de pe telefon pe **date mobile**: pagina Arena de pe Vercel se încarcă, trimiterea merge, ecranul live primește evenimente.
6. Laptopul în priză, fără sleep, actualizări oprite.

## Review PR #19 (Detector) — 2026-10-28
Mergeuit. 206 teste trec, ruff curat, fără conflicte cu main. Observații minore (nu blochează):
- `artifacts.ela_image` nu are `page` (implicit 1; ok pentru JPEG, pentru PDF cu mai multe pagini arată doar pagina 1).
- Calea `page` la `/documents/{id}/image` e 1-based; `page=0` dă 404 (corect, doar de știut).
- `Image.open` + `getexif` pe JPEG rulează pe event loop (cost neglijabil, dar poate intra în `to_thread`).
- PNG-urile nu sunt analizate (fără compresie JPEG); o fotografie/scan salvat ca PNG scapă de ELA.
- Pe Maria, a doua zonă ELA (doc_2, bbox 832,1328-1136,1616) e `info` fără câmp asociat; probabil ștampila/semnătura, de verificat vizual.
- O singură salvare JPEG sau recompresii oneste (75→90, 60→85, 70→80→90) nu dau fals pozitive în testele mele.

## Review PR #30

`scripts/start_bank.sh` (Ollama + backend ENV=demo + ngrok + test Maria). Verdict: OK, mergeuit. `bash -n` curat, shellcheck doar SC2015 (info). Nu atinge `.env`, nu afișează secrete, nu șterge nimic, re-rulabil.

Minor:
- `NGROK_DOMAIN` nu e în `.env.example`; scriptul pică cu "NGROK_DOMAIN lipsește" dacă nu e setat. De adăugat.
- `--stop` folosește `pkill -f` pe `uvicorn app.main:app`, `ollama serve`, `ngrok http`: oprește și serverul de dev de pe 8000 sau un Ollama pornit ca serviciu. De știut înainte de demo.
- Pasul "Test: dosarul Mariei" apelează `rerun-demo`, care șterge dosarele Maria terminate (intenționat), și se sare silențios dacă `BANK_UI_TOKEN` e gol.
- Scriptul nu e menționat în README.

## Review PR #45 (navigare + proiector) — Samuel, ~20:30 — NU e pe main încă
Navigarea instant, bara de sus și QR-ul centrat pe proiector arată bine și merg (testat pe build de producție).
**Un bug, de reparat înainte de merge:** linkul „Maria Ionescu's application” din bara de sus duce acum direct la id-ul
dosarului Mariei luat dintr-o listă ținută în cache 5 s. După „Re-run live”, backend-ul șterge rularea veche, dar linkul
arată tot spre ea → click pe tab = „The application could not be loaded”.
Reparația simplă: linkul să rămână `/cases/case_maria` (alias-ul din `CasePage` redirecționează la cel mai recent dosar),
sau `qc.invalidateQueries({ queryKey: ['cases', false] })` după `rerunDemo()` în `CasePage`. Prima variantă e mai sigură.

## Review PR #46 (landing) — Samuel, ~21:00
Arată foarte bine. Am corectat pe ramura ta (2 commit-uri, `narcis/landing`) trei afirmații care nu erau exact adevărate:
titlul („20 seconds, not 20 minutes” → „seconds, not ~20 minutes”; 20 min e estimare), „Measured, not estimated” fără
„synthetic data” (am adăugat disclaimer-ul), Detectorul „AI-generated images” (nu face asta → urme de editare în poze/PDF),
plus registrul demo la ANAF. Fă `git pull` pe ramură înainte să mai lucrezi pe ea.

- (21:15) PR #45: am rezolvat eu conflictele cu landing-ul și am pus linkul Mariei înapoi pe `/cases/case_maria` (testat: după Re-run, tab-ul duce la dosarul nou). E pe main. Fă `git pull` înainte să mai lucrezi.

## Design pentru platformă — ce vrea Samuel (seara de 28.10)
**Pagina de prezentare e ascunsă** (`/about`, fără link; `/` duce iar la dashboard). Nu mai lucra pe ea. Juriul vede
**platforma** în video, deci acolo punem tot efortul. În ordinea în care apar în video:
1. **Pagina dosarului** (cea mai importantă, ~1 minut din video): banda celor 6 agenți când rulează live (să se vadă clar
   cine lucrează, cine a terminat, animație la pornire), documentul cu chenarele dovezilor (chenar mai vizibil, evidențiere
   când dai click pe o dovadă), cardul de risc („Very high” mare, clar).
2. **Lista de dovezi**: severitatea dintr-o privire (culoare/iconiță), mai aerisit, citibil pe proiector.
3. **Panoul Privacy**: cele 4 carduri să arate ca „dovezi”, nu ca text — mai vizual.
4. **Dashboard-ul**: primul cadru din video după titlu → să arate impresionant în 3 secunde.

Reguli: **doar aspect**, nu schimbi ce face aplicația și nici textele cu cifre/afirmații. PR-uri mici (câte o pagină),
ca să le verific și să le pun repede. **Termen: ~22:30** — după aia filmăm videoul și nu mai schimbăm interfața.
