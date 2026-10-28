# Video 3:00 — VARIANTA 4 (după 3 runde de jurați; runda 3 cu Fable, care au verificat și codul) — DE LUCRU

> Variantele 3, 2 și 1 sunt mai jos, doar ca istoric. **De confirmat după workshopul de la 20:00.**

## Runda 3 (4 jurați Fable: șef operațiuni credite, tehnic, coach de pitch, avocatul diavolului)
Pe varianta 3: 7 · 8 (tehnic) · 7 · 7 din 10, top 3 ~35–45%. Cu reparațiile lor: **8–8,5 din 10, ~55–65%**.
Juratul tehnic a verificat în cod fiecare afirmație din video: **toate sunt acoperite** de cod și de cifre, cu două formulări prea tari.
1. **Deschiderea e cea pe care o va avea orice echipă** („repetitive work, 20 minutes”) → începem cu dovada:
   „Fluturașul ăsta spune 8.500. Ar trebui 8.307.” — și ne întoarcem la el la Maria.
2. **Riscul cel mai mare:** juriul găsește în cod `manual_minutes_per_case = 20` și crede că cifra e inventată → o spunem
   de fiecare dată ca estimare, iar cronometrul din scena 3 e singura cifră de timp măsurată; pilotul măsoară restul.
3. **O contradicție:** „20 s + un minut de verificare” (scena 2) vs „sub un minut” (scena 3) → scena 3 spune timpul real de pe cronometru.
4. **Omisiunea din scena 8:** 3/12 cinstiți merg la om. Scrie în README, deci juriul o va vedea → o spunem în video.
5. **„Never leave the bank”** contrazice cloud-ul → „never go to the cloud” (doar buletinele și pozele neclare).
6. Ce face sistemul mai bine decât spunea videoul: **ce citește AI-ul trebuie găsit în document, altfel e aruncat**, iar
   **o a doua barieră re-scanează fiecare cerere** înainte să plece spre cloud. Le spunem.
7. **Scena 9:** pe ecran trebuie să apară un fals care TRECE (vocea spune „gets through”), nu unul prins.
8. Pentru banca reală (șeful de operațiuni): ofițerul de protecția datelor nu lasă date în afara UE → pilotul rulează **pe mașina băncii**,
   lângă sistemul actual, pe o copie a dosarului. O spunem la final.

## Structura (180 s, ~400 de cuvinte, ~2,2–2,5 cuvinte/s)

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Text mare |
|---|---|---|---|---|---|
| 0 | 0:00–0:03 | 3 s | Titlul ORB | — (muzică) | — |
| 1 | 0:03–0:17 | 14 s | Zoom pe fluturașul Mariei, pe netul 8.500 → apoi buletinul și extrasul | "This payslip says 8,500 lei take-home. It should say 8,307. An analyst finds that by hand — by our own timing, about twenty minutes of reading, recalculating and cross-checking. Every file. Even the honest ones." | „~20 min per file (our timing)” |
| 2 | 0:17–0:29 | 12 s | Dashboard: bara cu orele | "ORB runs those checks in twenty seconds; the analyst reviews the evidence, not the paperwork. Our estimate for these twenty-one files: seven hours, down to about twenty minutes." | „7 h → ~20 min (estimate)” |
| 3 | 0:29–0:59 | 30 s | „New application” + cronometru → dosarul cinstit → agenții → nimic grav → click pe o valoare = sursa ei pe document → Approve → cronometrul se oprește | "Most applications are honest — that's where the hours go. So here's an honest one, with a real stopwatch. Six steps, one job each. Two use AI, to read and to summarise — and anything the AI reads must be found in the document, or it's discarded. The four that check and score are plain code: no hidden text can change the score. Every value linked to its source. The analyst approves. Upload to decision: **[timpul de pe cronometru]**." | cronometrul |
| 4 | 0:59–1:31 | 32 s | Maria → „Re-run live” (agenții la 2x) → dovezile → click = chenar pe fluturaș → zonele editate | "Now Maria — the payslip from the start. Someone applied in her name for forty-five thousand lei. Her bank statement shows a pension, but the payslip says she's employed. ORB recalculates it: 8,307, not 8,500. The employer comes back inactive in the registry. And pixel analysis shows where the payslip was edited — every finding drawn as a box on the document." | „20 s real time, shown at 2×” · „8,307 ≠ 8,500 lei” |
| 5 | 1:31–1:41 | 10 s | Graful: Maria + 5 cereri | "And what no one sees one file at a time: one bank account, six applications, six different names. ORB links them." | „1 account · 6 names” |
| 6 | 1:41–1:59 | 18 s | Risc „Very high” → „Why this score?” → Approve fără motiv → cere motiv | "Risk: very high. But the AI doesn't decide. The score is computed by code from the evidence, every line explained. The analyst decides — and approving a flagged file takes a written reason." | „The AI doesn't decide” |
| 7 | 1:59–2:17 | 18 s | Privacy: textul exact văzut de AI ([PERSOANA_1]) → butonul „100% local” | "Before any cloud AI sees a document, names and ID numbers become stand-ins like 'Person 1' — and a second gate re-scans every request before it leaves. ID cards and unclear photos never go to the cloud. Or, one switch, and it all runs in-house." | „0 names or ID numbers to the cloud” |
| 8 | 2:17–2:37 | 20 s | Cardul cu cifrele (nou) | "Sixty test applications, real cloud AI. Zero names or ID numbers reached the cloud. Twelve honest applicants: none flagged high-risk, three sent to a human for a second look. Thirty-six simple forgeries: all caught. Forgeries where every number is correct: three of twelve — that's why we want real files next." | (cardul plin) |
| 9 | 2:37–2:47 | 10 s | Proiectorul Arenei: un fals care **trece** → regula propusă → Approve | "And when a forgery does get through? Anyone can try in our public Arena. Each win becomes a proposed rule — and a human approves it." | — |
| 10 | 2:47–3:00 | 13 s | Cardul de final: cererea + link + Arena | "Our ask: a hundred real files, beside one of your analysts, on your own machine. Count the hours saved and the forgeries caught. ORB does the checking. Your people decide." | „Pilot: 100 real files · on your machine” |

### De făcut înainte de filmare
- **Cardurile** (`scripts/make_video_cards.py`):
  - titlul fără „without customer data leaving the bank”;
  - „~20 min per file (our timing)”, „7 h → ~20 min (estimate)”, „20 s real time, shown at 2×”, „1 account · 6 names”, „0 names or ID numbers to the cloud”;
  - cardul de cifre: 0 · 0/12 high-risk (3/12 la om) · 36/36 simple · 3/12 perfect;
  - cardul de final cu pilotul.
- **Scena 3:** filmăm dosarul cinstit cap-coadă în timp real, iar fraza finală spune timpul de pe cronometru.
- **Scena 9:** pornim Auto-Attacker până trece un fals, apoi filmăm regula propusă.
- Dashboard curat (fără Error/unknown), cu 21 de dosare procesate (sau schimbăm cifra din voce).
- Dovezile cu pensia și firma inactivă să se vadă în listă când le spunem.

## Întrebări grele la finală (de la juratul tehnic) — răspunsuri oneste
1. *Falsurile sunt făcute de voi; cât prindeți din cele reale?* — Nu știm încă. Arena aduce falsuri făcute de alții, iar pilotul pe 100 de dosare e răspunsul.
2. *Pseudonimizarea nu e anonimizare (GDPR).* — Corect: etichetele + salariul tot date personale sunt. De asta cheia seifului nu pleacă,
   folosim o regiune UE sau modul local, iar Bedrock e un împuternicit (persoană împuternicită) în analiza de impact (DPIA).
3. *De ce 3 cinstiți la om?* — Bariera a blocat 2 trimiteri, iar la 1 s-a citit greșit un rând din extras. E o verificare, nu o respingere: costă minute, nu o decizie greșită.
4. *Prompt injection?* — Detector pe textul OCR, extragerea trebuie găsită în document, rezumatul e verificat cifră cu cifră, scorul e cod.
   (Testul cu text slab vizibil: OCR-ul nu l-a citit deloc, deci nu a ajuns la AI.)
5. *AI Act: creditarea e risc ridicat.* — ORB produce dovezi, nu decizii. Scorul e determinist, cu detaliere completă, iar decizia omului e înregistrată cu motiv.

---

# Varianta 3 (istoric)

> Varianta 2 și varianta 1 sunt mai jos, doar ca istoric. **De confirmat după workshopul de la 20:00.**

## Runda 2 de jurați (pe varianta 2): ce s-a schimbat
Note: 7 · 7 · 6 · 6 din 10. Toți: **încape în 3:00** (~330 de cuvinte), dar timpul e prost împărțit: scenele 3, 4 și 6 au liniște,
iar 1, 5 și 9 sunt înghesuite. Reparații în varianta 3:
1. **Eficiența e încă doar estimată.** → În scena 3 punem un **cronometru real pe ecran** (de la încărcare la aprobare) = singura
   cifră de eficiență *măsurată* chiar în video. La scena 2 spunem „our estimate”.
2. **„Toate falsurile prinse” e o omisiune.** Benchmark-ul are 60 de dosare: 12 cinstite, 36 de falsuri simple (toate prinse) și
   **12 falsuri „perfecte”** (taxe refăcute corect), din care semnalăm doar 3. → O spunem deschis în scena 8 și legăm Arena de asta.
3. **„Stolen identity”** nu putem dovedi → „someone applied in her name”. **„Retired, dar are fluturaș”** părea o greșeală de scenariu →
   e chiar o dovadă: extrasul arată pensie, fluturașul zice angajată.
4. **„0 personal data”** e prea larg (salariul e tot dată personală) → „0 names or ID numbers”. „none of twelve” în loc de „no honest”.
5. **„Two use AI, four are plain code”**, plus de ce contează: un document nu poate convinge scorul cu text ascuns (prompt injection).
6. Cifra de pe dashboard: 21 de dosare × 1 min de verificare = **~20 min** (0,4 h), corect. Mașina rulează separat, nu e timpul analistului.

## Structura — ce se vede și ce se aude (180 s, ~320 de cuvinte)

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Text mare pe ecran |
|---|---|---|---|---|---|
| 0 | 0:00–0:03 | 3 s | Titlul: ORB — „AI agents that do the repetitive checks on loan applications” | — (muzică) | — |
| 1 | 0:03–0:17 | 14 s | Buletinul, fluturașul și extrasul Mariei, zoom lent | "Every loan file means the same repetitive work: read the ID, the payslip, the bank statement. Recalculate the taxes, look up the employer, cross-check everything. By our own timing, about twenty minutes per file." | „~20 min per application” |
| 2 | 0:17–0:29 | 12 s | Dashboard-ul; zoom pe bara cu orele (manual vs ORB) | "ORB does that check in twenty seconds; the analyst reviews the evidence in a minute. On these twenty-one files, our estimate: seven hours, down to twenty minutes." | „7 h → 20 min (estimate)” |
| 3 | 0:29–0:59 | 30 s | „New application” + **cronometru pe ecran** → dosarul cinstit → agenții → nimic grav → valori legate de document → Approve → cronometrul se oprește | "Most real applications are honest — and that's where the hours go. Here's one, with a stopwatch running. Six steps, each with one job: two use AI to read and summarise; the four that check and score are plain code, so a document can't talk its way past them. Everything adds up — upload to approval in under a minute." | cronometrul (timpul real măsurat) |
| 4 | 0:59–1:33 | 34 s | Maria → „Re-run live”: agenții (2x) → dovezile → click = chenar pe fluturaș → harta editării | "Now Maria. Someone applied in her name for a forty-five-thousand-lei loan. Her bank statement shows a pension — yet the payslip says she's employed. ORB recalculates that payslip: the take-home pay should be 8,307 lei, not 8,500. The employer comes back inactive. And image forensics highlight where the payslip was edited — every finding marked on the document." | „real time: 20 s” · „8,307 ≠ 8,500 lei” |
| 5 | 1:33–1:43 | 10 s | Graful: Maria + 5 cereri, același cont | "And what no one sees one file at a time: one bank account, six applications, six different names." | „1 account · 6 names” |
| 6 | 1:43–2:01 | 18 s | Cardul de risc → „Why this score?” → Approve fără motiv → cere motiv | "The AI doesn't decide. The risk level is computed from the evidence, each piece explained. The analyst decides — and approving a flagged file takes a written reason." | „The AI doesn't decide” |
| 7 | 2:01–2:19 | 18 s | Privacy: ce a văzut AI-ul ([PERSOANA_1]) → butonul „100% local” | "Before any cloud AI sees a document, names and ID numbers are replaced with placeholders. ID cards and unclear photos never leave the bank. Or, with one switch, everything runs on the bank's own machine." | „0 names or ID numbers to the cloud” |
| 8 | 2:19–2:39 | 20 s | Cardul cu cifrele (nou: include și falsurile „perfecte”) | "We tested sixty synthetic applications with the real cloud AI: no names or ID numbers leaked, none of twelve honest applicants flagged high-risk, thirty-six of thirty-six simple forgeries caught. Perfect forgeries mostly get through — that's what a pilot on real files measures." | (cardul plin) |
| 9 | 2:39–2:49 | 10 s | Telefonul: Arena, fals prins → proiectorul: regula propusă → Approve | "Think you can do better? Try our Arena. When a forgery gets through, it becomes a proposed rule — and a human approves it." | — |
| 10 | 2:49–3:00 | 11 s | Cardul de final: propunerea + link + Arena | "Our proposal: run ORB next to your analysts on a hundred real files, and measure the hours saved. ORB does the checking. People decide." | „Pilot: 100 real files, next to your analysts” |

### De făcut înainte de filmare
- **Cardurile** (`scripts/make_video_cards.py`):
  - titlul fără „without customer data leaving the bank”;
  - overlay nou „7 h → 20 min (estimate)”;
  - „1 account · 6 names”;
  - „0 names or ID numbers to the cloud”;
  - cardul de cifre: „0/12 honest flagged high-risk”, „36/36 simple forgeries”, plus „12 perfect forgeries: 3 flagged”;
  - cardul de final cu pilotul.
- **Cronometrul din scena 3:** îl adăugăm la montaj, după timpul real din înregistrare. Dacă iese peste un minut, schimbăm fraza.
- **Dashboard-ul:** seed curat, fără rânduri Error/unknown; vocea spune cifra care apare pe ecran (21 de dosare / 7 h / 0,4 h).
- Dovada cu pensia trebuie să se vadă în lista Mariei când o spunem.
- Designul nou al lui Narcis intră înainte de filmare.

---

# Varianta 2 (istoric)

> Asta e varianta de lucru. Varianta veche e mai jos, la „Varianta 1”, doar ca istoric.
> **De confirmat după workshopul de la 20:00.**

## Ce au zis jurații (business Raiffeisen, tehnic, om din afara domeniului, avocatul diavolului)
Note: 7 · 7 · 6,5 · 6,5 din 10. Șansă de top 3 doar din video: ~15–35% acum, ~40–45% cu schimbările de mai jos.
1. **Toți 4: povestea cu frauda acoperă eficiența**, adică tema concursului. Eficiența are ~25 s, frauda și confidențialitatea ~105 s.
   Dosarul cinstit e chiar locul unde se câștigă orele → îl lungim și spunem orele.
2. **Maria: prea lung și prea dens** (4 dovezi într-o frază) → 3 dovezi, spuse rar.
3. **Afirmații de reparat:**
   - „~20 min” → „după cronometrarea noastră”;
   - „20 s” → „ORB pregătește verificarea; analistul se uită la dovezi un minut”;
   - „customer data never leaves the bank” contrazice scena cu AI-ul din cloud → „datele personale sunt mascate înainte de AI, sau totul rămâne local”;
   - „six specialised agents” → „șase specialiști: doi folosesc AI, patru sunt cod simplu” (e adevărat: Funcționarul și rezumatul folosesc LLM);
   - „no honest applicant accused” → „niciun dosar cinstit marcat cu risc mare”, cu numărul de dosare.
4. **Jargon** pentru cine nu e bancher: „net/gross” → „take-home pay”, „IBAN” → „bank account”, „shadow-mode pilot” → „next to your analysts”.
5. **Finalul**: fraza tăiată în două la schimbarea de cadru, fără o cerere clară → o propunere concretă, într-o singură frază.
6. **Arena și regula în 9 s = prea mult.** Doi jurați zic s-o scoatem, unul zice că bucla de învățare e partea interesantă →
   o păstrăm, dar într-o singură propoziție.
7. Dashboard-ul la filmare: **fără rânduri „Error”/„unknown”** (seed curat înainte).

## Structura nouă — ce se vede și ce se aude

Totalul e 180 s, cu ~300 de cuvinte de voce (rar, cu pauze).

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Text mare pe ecran |
|---|---|---|---|---|---|
| 0 | 0:00–0:03 | 3 s | Titlu: ORB — „AI agents that do the repetitive checks on loan applications” | — (muzică) | — |
| 1 | 0:03–0:17 | 14 s | Buletinul, fluturașul și extrasul Mariei, zoom lent pe fiecare | "Every loan application comes with the same repetitive work. Read the ID card, the payslip, the bank statement. Recalculate the taxes. Look up the employer. Cross-check everything. By our own timing — about twenty minutes per file." | „~20 min per application” |
| 2 | 0:17–0:29 | 12 s | Dashboard-ul băncii; zoom pe bara „ore de lucru: manual vs ORB” | "ORB prepares that check in about twenty seconds — the analyst just reviews the findings. Across these twenty-one files: seven hours of manual work, down to under half an hour." | „7 h → under 0.5 h” |
| 3 | 0:29–0:57 | 28 s | „New application” → încărcăm dosarul cinstit → cei 6 agenți rulează → nicio dovadă gravă → valorile sunt legate de document → analistul apasă Approve | "Most applications are honest — and that's where the hours go. Here's one. Six specialists, each with one job: two use AI, four are plain code. Every value is traced back to the document, nothing is flagged — so the analyst approves it in one click." | — |
| 4 | 0:57–1:37 | 40 s | Maria → „Re-run live”: agenții se aprind (2x) → dovezile apar → click pe dovadă = chenar pe fluturaș → harta editării | "Now Maria. She's sixty-seven and retired — and someone has applied for a forty-five-thousand-lei loan with her stolen identity. ORB recalculates the payslip: the take-home pay should be 8,307 lei, not 8,500. The employer is listed as inactive. And the Detector shows exactly where the payslip was edited — every finding marked on the document itself." | „real time: 20 s” (pe agenți) · „8,307 ≠ 8,500 lei” |
| 5 | 1:37–1:45 | 8 s | Graful: Maria + încă 5 cereri, același cont | "And what no analyst sees one file at a time: the same bank account in six applications, under six different names." | „1 account · 6 identities” |
| 6 | 1:45–2:06 | 21 s | Cardul de risc → „Why this score?” → Approve fără motiv → aplicația cere motivul | "The AI doesn't decide. The risk level is computed from the evidence, and each piece is explained. The analyst decides — and approving a flagged file takes a written reason." | „The AI doesn't decide” |
| 7 | 2:06–2:24 | 18 s | Privacy: ce a văzut AI-ul ([PERSOANA_1]) → butonul „100% local” | "Before any cloud AI sees a document, names and ID numbers are replaced with placeholders. ID cards and unclear photos never go to the cloud. Or, with one switch, everything runs on the bank's own machine." | „0 personal data to the cloud” |
| 8 | 2:24–2:40 | 16 s | Cardul cu cifrele măsurate | "We measured it on sixty synthetic applications, with the real AI: no personal data sent to the cloud, no honest applicant flagged as high risk, all thirty-six planted forgeries caught. A baseline — real accuracy is what a pilot measures." | (cardul plin) |
| 9 | 2:40–2:48 | 8 s | Telefonul: Arena, fals prins (4 s) → proiectorul: regula propusă → Approve (4 s) | "Think you can fool it? Try our Arena. Forgeries that slip through become new rules — approved by a human." | — |
| 10 | 2:48–3:00 | 12 s | Cardul de final: propunerea + linkul + Arena | "Our proposal: run ORB next to your analysts on a hundred real files, and measure the hours saved. ORB does the checking. People decide." | „Pilot: 100 real files, next to your analysts” |

### Ce schimbăm față de varianta 1
- dosarul cinstit: 18 s → 28 s, plus o scenă nouă cu orele (dashboard) → eficiența ~55 s în loc de ~25 s;
- Maria: 48 s → 40 s, 3 dovezi în loc de 4 (scoatem soldul);
- confidențialitatea: 24 s → 18 s;
- finalul: o cerere concretă (100 de dosare reale, măsurăm orele), fără fraza tăiată în două.

### De făcut înainte de filmare
- **Cardurile** (`scripts/make_video_cards.py`):
  - titlul fără „without customer data leaving the bank”;
  - overlay nou „7 h → under 0.5 h”;
  - „1 IBAN” → „1 account”;
  - pe cardul de cifre, „honest applicants accused” → „honest applicants flagged high-risk”;
  - cardul de final cu propunerea de pilot.
- **Dashboard-ul:** seed curat (fără rânduri Error/unknown). Cifra „21 files / 7 h / 0.4 h” trebuie să fie cea de pe ecran la filmare;
  dacă se schimbă numărul de dosare, schimbăm și vocea.
- Designul nou al lui Narcis intră înainte de filmare (termen ~22:30).

---

# Varianta 1 (veche, doar ca istoric)

Format: înregistrare de ecran a aplicației (OBS, 1080p, zoom 125–150%) + voce înregistrată separat (telefon la 20 cm, cameră liniștită)
+ 4–5 texte mari pe ecran. Montaj: Kdenlive / Shotcut / CapCut. Secvența cu agenții (~20 s) accelerată 2x, cu „real time: 20 s”.
**Verificați la final: sub 3:00.** Faceți și o variantă de rezervă (demo brut) înainte de 11:00.

| Timp | Pe ecran | Vocea (engleză) | Text mare |
|---|---|---|---|
| 0:00–0:15 | 3 documente (buletin, fluturaș, extras — ale Mariei) | "Every loan application at a bank means the same repetitive work: read the ID, the payslip, the bank statement, recalculate the taxes, look up the employer, cross-check everything. About twenty minutes per file." | ~20 min / application |
| 0:15–0:25 | Logo ORB → Dashboard | "ORB does that work in twenty seconds — and customer data never leaves the bank." | 20 min → 20 s |
| 0:25–0:45 | „New application” → dosar cinstit → aprobat | "A normal application: six specialised agents read and check it, the analyst sees that everything adds up and approves it." | — |
| 0:45–1:35 | Maria, „Re-run live”: agenții pornesc; click pe dovezi → chenar pe document | "Now Maria, 67, retired. Someone applied for a 45,000 lei loan in her name. The Verifier recalculates the payslip: the net pay doesn't follow from the gross. The employer is listed as inactive. The balance in the statement doesn't add up, and the Detector shows exactly where the payslip was edited. Every finding is shown on the document itself." | 8,307 ≠ 8,500 lei |
| 1:35–1:45 | Graful: Maria + 5 cereri | "And something no human sees file by file: the same bank account in six applications, under six identities." | 1 IBAN · 6 identities |
| 1:45–2:10 | Cardul de risc → „Why this score?” → aprobare cere motiv | "The AI doesn't decide. The risk level is computed from the evidence, each piece explained. The analyst decides — and approving a flagged file requires a written reason." | The AI doesn't decide |
| 2:10–2:35 | Privacy → „What the AI saw” ([PERSOANA_1]) → butonul Local | "The cloud AI only ever sees labels like 'person one', never a name or an ID number. ID cards and unclear photos don't go to the cloud at all. Or, with one button, everything runs on the bank's own machine." | 0 personal data to the cloud |
| 2:35–2:50 | Slide cu cifrele | "We measured it with the real AI on sixty applications: no personal data sent to the cloud, no invented values, no honest applicant accused — every planted forgery caught. On synthetic data, and we say so." | 0 · 0 · 0 · 36/36 |
| 2:50–3:00 | QR Arena → „shadow mode → assistant → triage” | "Try to fool it yourself in our Arena. We propose a shadow-mode pilot: ORB works next to your analysts, never instead of them." | Shadow-mode pilot |

~330 de cuvinte ≈ 2:40 citit liniștit → rămâne loc de pauze.

## Înainte de filmare
- aplicația în engleză (traducerea e în lucru) + redeploy (`scripts/deploy_frontend.sh`);
- backend la Narcis: `git pull && scripts/start_bank.sh --stop && scripts/start_bank.sh`, apoi seed-demo;
- dosarul Mariei rulat o dată înainte; un dosar cinstit pregătit pentru „New application”
  (`backend/.venv/bin/python scripts/benchmark_pipeline.py --n 3 --save data/generated/bench --generate-only` → un „honest”).

## Varianta finală a vocii (de citit, ~320 cuvinte ≈ 2:30)
> **Corectură:** NU spunem „ANAF says the employer is inactive” — firma Mariei e inactivă în **registrul demo**, nu la ANAF real.

**[0:00]** Every loan application at a bank comes with the same repetitive work. Read the ID card, the payslip, the bank statement. Recalculate the taxes. Look up the employer. Cross-check everything. About twenty minutes — for every single file.

**[0:15]** ORB does that work in twenty seconds. And customer data never leaves the bank.

**[0:25]** Here's a normal application. Six specialised agents read it and check it. Everything adds up — the analyst approves it.

**[0:45]** Now Maria. She's sixty-seven and retired — and someone just applied for a forty-five-thousand-lei loan in her name. The Verifier recalculates the payslip: the net pay doesn't follow from the gross. The employer is listed as inactive. The balance on the statement doesn't add up — and the Detector shows exactly where the payslip was edited. Every finding is shown on the document itself.

**[1:35]** And something no analyst sees one file at a time: the same bank account, in six applications, under six different identities.

**[1:45]** The AI doesn't decide. The risk level is computed from the evidence, and every piece is explained. The analyst decides — and approving a flagged file takes a written reason.

**[2:10]** The cloud AI only ever sees labels — "person one", "ID number one" — never a real name. ID cards and unclear photos don't go to the cloud at all. And with one button, everything runs on the bank's own machine.

**[2:35]** We measured it with the real AI on sixty applications: no personal data sent to the cloud, no invented values, no honest applicant accused — and every planted forgery caught. On synthetic data, and we say so.

**[2:50]** Try to fool it yourself in our Arena. We propose a shadow-mode pilot: ORB works next to your analysts — never instead of them.

**Citit:** rar, pauze scurte între fraze; accent pe contraste („twenty minutes” → „twenty seconds”, „doesn't decide”, „never instead of them”);
Raiffeisen = „RAI-fai-zen”, lei = „lay”; fiecare paragraf într-un fișier separat.

## Cum îl facem (ordinea contează: vocea → imaginea → montajul)
1. **Pregătire (15 min):** redeploy Erin + `git pull` și repornire Narcis; seed-demo + rerun-demo o dată; browser curat, ecran complet,
   zoom 125%; dosarul cinstit din `data/demo/honest/` pregătit pentru „New application”; telefonul pentru Arena (înregistrare nativă).
2. **Vocea întâi (20 min):** Samuel citește textul de mai sus, **scenă cu scenă, fișiere separate**; telefon la 20 cm, cameră mică.
3. **Clipurile de ecran (Erin, Mac, Screen Studio sau Cap — zoom automat pe click):**
   A Dashboard → New application → aprobat · B Maria → Re-run live (lasă până la verdict) · C dovezi → chenar pe fluturaș → Edit map
   (2 s pe fiecare) · D graful · E Very high → Why this score? → Approve fără motiv (cere motiv) · F Privacy → What the AI saw → Local
   · G telefon: Arena, fals prins, „Math does not lie”.
4. **Montaj (CapCut desktop):** voce · clipuri pe voce (+ zoom keyframes) · 4–5 texte mari · sunete (click, whoosh la agenți, alertă
   la dovada roșie) · muzică −25 dB · subtitrări automate verificate (CNP, ANAF). Agenții accelerați 2x cu „real time: 20 s”.
   Nicio scenă statică > 4–5 s. Final 5 s: logo + link + „Shadow-mode pilot”.
5. **Export:** 1080p, 30 fps, MP4, **sub 3:00**. Vizionat o dată fără sunet și o dată pe telefon. YouTube „Unlisted” / Drive cu link
   public — verificat din incognito.
