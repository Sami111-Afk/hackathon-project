# Video 3:00 — VARIANTA 7 (după juriul Opus + verificarea pe slide-urile organizatorilor) — DE FILMAT

> Variantele 6–1 sunt mai jos, ca istoric. Vocea: AI (Chatterbox, varianta expresivă aleasă de Samuel), generată din `notes/voce.md`.

## Ce s-a schimbat față de varianta 6
- **Limitele spuse în video** (scena 12) — slide-urile 41 și 50 le cer explicit; lipseau complet.
- **„Why this shape?”** spune și **uneltele** (tabele de taxe, registrul firmelor, analiza imaginii) — criteriul de 25%.
- **Decizia omului dusă până la capăt** (refuz → motiv → trimis la investigație → salvat în audit).
- **Modul local spus cinstit:** „tested on our laptop, ~9 s/file” + pe ecran „switch shown only”.
- **Etichete pe ecran de la început** (SYNTHETIC DATA, 2×, tăieturi între dosare, simulated phone photos, demo registry, AWS us-west-2).
- **Scoasă** fraza cu ANAF (nu o putem susține). „ORB” scris „Orb” în textul vocii (altfel AI-ul spune „or B”).
- Pe cardul final: „ORB checks documents, not creditworthiness · voice: AI-generated”.
- Juriu Opus pe v6: ~61/90, locul 2–6 din 28, ~45–50% top 3.

## Structura (180 s)

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Text pe ecran |
|---|---|---|---|---|---|
| 0 | 0:00–0:04 | 4 s | Intro animat ORB (text scurt: „Loan-document checks for credit analysts. A human always decides.”) | — (muzică) |  |
| 1 | 0:04–0:17 | 13 s | Zoom pe netul de pe fluturașul Mariei: 8.500 → „should be 8,307” cu roșu · insignă „SYNTHETIC DATA · DEMO” de aici până la 2:46 | "This payslip says 8,500 lei net. Romanian payroll rules say 8,307. Today a credit analyst catches that by hand: read, recalculate, cross-check. About twenty minutes a file, by our own timing." | „~20 min per file · our timing, not bank data” |
| 2 | 0:17–0:30 | 13 s | Ecranul „New application”, zoom lent · „User: credit analyst” | "We built Orb to help credit analysts check loan documents. Today that's slow: every payslip, statement and employer is checked by hand, and fraud rings hide across files. Orb flags exactly what's wrong." | „User: credit analyst” · „Screen recording · 2× while agents run · cuts between files” |
| 3 | 0:30–0:40 | 10 s | Documentele Mariei → zoom pe nume → [PERSOANA_1] în vederea „What the AI saw” | "Watch the names. Maria's application: three synthetic documents. Before any AI sees them, the Guard swaps every name and ID number for a label." |  |
| 4 | 0:40–1:06 | 26 s | Agenții live („2× SPEED”) → dovezile, zoom pe fiecare când e numită → click = chenar pe fluturaș | "Six agents, one job each, and only two of them use AI. The Clerk extracts the fields; any value it can't point to in the document is discarded. Watch the box. The Verifier recomputes the tax: net should be 8,307, not 8,500. The employer, in our demo registry: inactive. And the salary never arrives in her statement." | „2× SPEED” · „DEMO REGISTRY · real ANAF API for real companies” · „8,307 ≠ 8,500 lei” |
| 5 | 1:06–1:15 | 9 s | „Edit map” pe fluturaș → graful: contul → 6 cereri | "The Detector marks the edited pixels. The Detective finds the same bank account in six applications, under six names." | „1 account · 6 names” |
| 6 | 1:15–1:32 | 17 s | Risc „Very high” → „Why this score?” → Approve → refuzat (1 s, „ping”) → analistul scrie motivul → „Send for investigation” → salvat | "Watch the button. The risk comes from fixed rules, every finding listed; the AI only writes the summary, and a summary quoting an unverified number is rejected. Approve? Refused without a written reason. The analyst sends it for investigation, and the decision goes into the audit." | „summary with an unverified number = rejected” |
| 7 | 1:32–1:48 | 16 s | Card „SECOND FILE” → dosarul cu poze neclare: „not sent to the cloud AI”, recomandare „review”, risc mic | "Different file now: blurry phone photos. Orb can't guarantee it hid everything, so their text never goes to the cloud AI. A person gets the file, and nobody is accused on a photo we can't read." | „simulated phone photos” · „no cloud call” |
| 8 | 1:48–2:04 | 16 s | Schema celor 6 pași; cei doi cu AI evidențiați; uneltele lângă ceilalți | "Why this shape? Audits need identical steps, so the order is fixed in code. AI only reads and summarises; the rest is rules and tools: tax tables, the company registry, image forensics. If a step fails, the file is never shown as clean." | „AI: read · summarise — rules & tools: everything else” |
| 9 | 2:04–2:14 | 10 s | Dosarul cinstit: clear, click pe o valoare = sursa ei | "Most files are honest: clean in seconds, nothing to fix, approved in one click. Twenty minutes becomes about a minute of review, our estimate." | „~20 min → ~1 min review (estimate) · 1 in 4 honest files still goes to a human” |
| 10 | 2:14–2:26 | 12 s | Privacy: textul exact primit de AI → butonul „Local”, apoi înapoi | "Built for a bank: the cloud AI sees only labels, and a second gate blocks any request still carrying a name. Local mode, tested on our laptop: about nine seconds a file." | „switch shown only · local run tested on our demo laptop, ~9 s/file · demo cloud: AWS us-west-2” |
| 11 | 2:26–2:44 | 18 s | Cardul cu cifrele | "Sixty synthetic files, real cloud AI: no name or ID number left the bank. None of twelve honest applicants flagged high-risk; three went to a human. All thirty-six simple forgeries caught, and all twelve perfect ones sent to a human. The forgeries are ours." | (cardul plin) |
| 12 | 2:44–2:56 | 12 s | Terminal curat: `pytest -q` → 275 passed · README „Verify it in 5 minutes” | "Limits: synthetic data and our own forgeries, so real-fraud accuracy is untested; a forger who also fakes the statement would pass. Next: a pilot on a hundred real files, in-house." | „275 tests · one command · runs without an API key (rules-only fallback)” |
| 13 | 2:56–3:00 | 4 s | Outro animat ORB + rând mic: „ORB checks documents, not creditworthiness · voice: AI-generated” | "Orb does the checking. Your people decide." |  |

### Înainte de filmare (checklist din slide-ul 51)
- seed-demo + rerun-demo; toate ecranele deschise o dată înainte (cache cald);
- notificările oprite; în terminalul din scena 12: shell curat, fără `.env`, fără token-uri, fără istoric;
- Tesseract cu `ron` pe laptopul de filmare (altfel Paznicul ar rula pe varianta înregistrată);
- baza de date locală curată (dosarul cinstit încărcat o singură dată, altfel apar legături false între încărcările repetate).

---

# Varianta 6 (istoric)

> Variantele 5–1 sunt mai jos, ca istoric. Urmează structura recomandată de organizatori și criteriile Raiffeisen.

## Ce s-a schimbat față de varianta 5 (și de ce)
- **Cod:** semnalul „salariul de pe fluturaș nu apare în extras” trimite acum dosarul la om → **12/12 falsuri perfecte** ajung la om
  (înainte 3/12), 0/12 cinstiți afectați. Plus: semnalele care nu acuză pe nimeni (MRZ ilizibil, valori nelegate de document) nu mai pot
  escalada singure un dosar (pe poze, un cinstit era escaladat așa). Benchmark-urile reluate cu AI-ul real.
- **Domeniu (directorul de risc):**
  - **scos „pensie + salariu”**: cumulul e legal în România, nu e semnal de fraudă;
  - în loc: „salariul nu ajunge în extras”;
  - deschiderea spune că datele ANAF nu acoperă tot, deci ORB verifică documentele;
  - „ORB checks documents, not creditworthiness” (AI Act).
- **Un singur flux (design de servicii):** Maria merge până la decizie, **apoi** „second file” cu situațiile neprevăzute;
  indicii pentru juriu înainte de click („Watch the names”, „Watch the button”); etichete pe ecran de la început.
- **Designul agenților (șeful AI, 25%):** scenă nouă „Why this shape?”; **rezumatul AI respins** dacă citează o cifră fără dovadă
  (nimeni altcineva nu va arăta asta); scos „debate” și agentul „skipped” din voce (doar text pe ecran).
- **Arhitectura (inginerul AI, 15%):** pe ecran `pytest` → 275 passed + README cu o comandă; README-ul are acum Prerequisites,
  „Verify it in 5 minutes” și „Why a fixed pipeline”.

## Structura (180 s, 2,1–2,6 cuvinte/s pe fiecare scenă)

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Text pe ecran |
|---|---|---|---|---|---|
| 0 | 0:00–0:04 | 4 s | Intro animat ORB | — (muzică) |  |
| 1 | 0:04–0:17 | 13 s | Zoom pe netul de pe fluturașul Mariei: 8.500 → apare „should be 8,307” cu roșu | "This payslip says 8,500 lei net. Romanian payroll rules say 8,307. Today a credit analyst catches that by hand: read, recalculate, cross-check. About twenty minutes a file, by our own timing." | „~20 min per file · our timing, not bank data” |
| 2 | 0:17–0:32 | 15 s | Ecranul „New application” (fără mișcări de cursor) · text „User: credit analyst” | "We built ORB to help credit analysts check loan applications. Salary data from ANAF can't cover everything, so ORB checks the documents themselves against the bank's rules, and flags exactly what's wrong." | „User: credit analyst” |
| 3 | 0:32–0:42 | 10 s | Încărcăm cele 3 documente → zoom pe nume → [PERSOANA_1] · insignă în colț „SYNTHETIC DATA · DEMO” până la 2:15 | "Watch the names. Maria's application: three synthetic documents. Before any AI sees them, the Guard swaps every name and ID number for a label." | „SYNTHETIC DATA” |
| 4 | 0:42–1:08 | 26 s | Agenții live („2× SPEED” în colț) → dovezile, zoom pe fiecare când e numită → click = chenar pe fluturaș → zonele editate | "Six agents, at double speed. The Clerk extracts the fields; any value it can't point to in the document is discarded. Now the findings. The Verifier recomputes the tax: net should be 8,307, not 8,500. The employer, in our demo registry: inactive. The salary never arrives in her statement. One click, and the box lands on the exact spot." | „2× SPEED” · „DEMO REGISTRY” pe firmă · „8,307 ≠ 8,500 lei” |
| 5 | 1:08–1:15 | 7 s | Graful: nodul contului → cele 6 cereri | "The Detector marks the edited pixels. The Detective finds one bank account in six applications." | „1 account · 6 names” |
| 6 | 1:15–1:32 | 17 s | Risc „Very high” → „Why this score?” → click pe Approve → caseta goală de motiv (1 s pauză, singurul „ping” din video) | "Watch the button. The risk comes from fixed rules, every finding listed. The AI only writes the summary, and a summary quoting a number not in the evidence is thrown out. The analyst decides, with a written reason." | „The AI doesn't decide” |
| 7 | 1:32–1:50 | 18 s | Card „SECOND FILE” → dosarul cu poză neclară: OCR_LOW_QUALITY, „not sent to the cloud” în audit → la om · apoi o sumă „to check” | "Different file now: a blurry phone photo. ORB can't guarantee it hid everything, so its text never goes to the cloud AI; a person gets it. And a sum the OCR may have misread is re-read from the image: 'to check', not 'forged'." | „no cloud call” · „to check” |
| 8 | 1:50–2:06 | 16 s | Schema celor 6 pași, cu cele două locuri unde lucrează AI-ul evidențiate | "Why this shape? Fixed steps, because an audit needs the same steps every time. The AI only reads and summarises; every decision is a written rule. If an agent fails, the rest finish, and the file is never shown as clean." | „AI: read · summarise — rules: everything else” |
| 9 | 2:06–2:16 | 10 s | Dosarul cinstit: clear, click pe o valoare = sursa ei | "Most files are honest: clean in seconds, nothing to fix, approved in one click. Twenty minutes becomes about a minute of review, our estimate." | „~20 min → ~1 min review (estimate)” |
| 10 | 2:16–2:28 | 12 s | Privacy: textul exact primit de AI → butonul „100% local” · text mic „demo: AWS us-west-2 · pilot: EU or in-house” | "Built for a bank: the cloud AI sees only labels, and a second gate blocks any request still carrying a name. One switch runs it all in-house." | „0 names or ID numbers to the cloud” |
| 11 | 2:28–2:46 | 18 s | Cardul cu cifrele (nou) | "Sixty synthetic files, real cloud AI: no name or ID number left the bank. None of twelve honest applicants flagged high-risk; three went to a human. All thirty-six simple forgeries caught, and all twelve perfect ones sent to a human. The forgeries are ours." | (cardul plin) |
| 12 | 2:46–2:56 | 10 s | Terminal: `pytest` → 275 passed · README cu comanda · schema | "Six modules, one contract, 275 tests, one command. ORB checks documents, not creditworthiness. Our ask: a pilot on a hundred real files, in-house." | „275 tests · runs without an API key” |
| 13 | 2:56–3:00 | 4 s | Outro animat ORB | "ORB does the checking. Your people decide." |  |

### De filmat / pregătit
- dosarul cu **poză de telefon neclară** (`scripts/benchmark_pipeline.py --n 4 --phone --save data/generated/phone --generate-only`, un „honest”);
- momentul **rezumat respins**: dacă nu apare natural, îl arătăm din audit (linia „summary replaced: unsupported figure”) — de verificat;
- terminalul cu `pytest -q` și README-ul;
- cardurile noi (cifrele sunt deja refăcute în `video/cards/05_numbers.png`).

---

# Varianta 5 (istoric)

> Variantele 4–1 sunt mai jos, ca istoric. Varianta 5 urmează **structura recomandată de organizatori** și
> **criteriile juriului Raiffeisen**. Sursa: slide-urile workshopului (link în chat).

## Ce am aflat din prezentare (important)
- **3 finaliști pe challenge**, iar în challenge-ul nostru (Operational Efficiency) sunt **~28 de echipe**. Evaluarea companiei
  contează 90% la selecția finaliștilor, mentoratul 10%.
- **Criteriile Raiffeisen:**
  - originalitate 15%;
  - înțelegerea problemei și a domeniului 15% („procese, date, reguli, constrângeri, excepții”);
  - **designul agenților și orchestrarea 25%** („decizii, folosirea uneltelor, **situații neprevăzute**”);
  - funcționalitate și testabilitate 20%;
  - arhitectură și reproductibilitate 15% („componente + instrucțiuni de instalare”).
  - Plus: *„Mai mulți agenți nu înseamnă automat o soluție mai bună. Explicați de ce designul se potrivește sarcinii.”*
- **Structura recomandată (nu obligatorie):**
  - 0:00–0:30 utilizator, problemă, soluție;
  - **0:30–2:00 demonstrație: UN flux de la input la rezultat**;
  - 2:00–2:30 valoare și diferențiere;
  - 2:30–3:00 implementare, limite, pasul următor;
  - „Explicați deciziile tehnice în timpul demo-ului.”
- Deschiderea recomandată: *„We built [soluția] to help [utilizatorul] do [sarcina]. Today this is difficult because [problema].”*
  **Exemplul lor e chiar ideea noastră** („an agent that checks application documents and flags missing information”) →
  multe echipe vor face ceva asemănător, deci **diferențierea contează** (dovezile pe document, fără date personale în AI, situații neprevăzute).
- „A feature tour is less useful than a complete user journey.” → **scoatem Arena din video** (rămâne linkul pe cardul de final).
- „Spuneți clar ce e sintetic, ce integrare e simulată, ce nu e terminat.” + „Spuneți dacă ați accelerat sau tăiat așteptări.” (avem „shown at 2×”).
- **Finala (17:00): doar video, fără demo live pe platformă** („technical restrictions”). → **Arena cu telefoanele juriului nu se poate face
  în finală.** Pitch deck-ul final se predă până la 16:30. La 15:30 juriul poate pune întrebări.

## Structura (180 s) — mapată pe criterii

| # | Timp | Durată | Pe ecran | Vocea (engleză) | Criteriu |
|---|---|---|---|---|---|
| 0 | 0:00–0:04 | 4 s | Intro animat ORB | — (muzică) | |
| 1 | 0:04–0:17 | 13 s | Zoom pe fluturașul Mariei (8.500), apoi buletinul și extrasul | "This payslip says 8,500 lei take-home. It should say 8,307. Catching that is a credit analyst's routine: read the documents, recalculate, cross-check. About twenty minutes a file, by our own timing." | problema |
| 2 | 0:17–0:33 | 16 s | Ecranul „New application” / dashboard | "We built ORB to help credit analysts check loan applications. It takes the ID card, the payslip and the bank statement, applies the bank's rules, and either clears the file or flags exactly what's wrong, for a human to decide." | utilizator + soluție |
| 3 | 0:33–0:46 | 13 s | **Input:** încărcăm cele 3 documente ale Mariei → vederea „redactat” (nume → [PERSOANA_1]) | "Here's Maria's application. First, the Guard reads the documents and replaces every name and ID number with a stand-in, before any AI sees them." | flux, decizii |
| 4 | 0:46–1:16 | 30 s | **Procesare:** agenții live (2×) → dovezile → click = chenar pe fluturaș → zonele editate | "The Clerk extracts the fields, and anything it reads must be found in the document, or it's discarded. The Verifier applies Romanian payroll tax rules: take-home should be 8,307, not 8,500. It looks up the employer: inactive. The statement shows a pension, though the payslip says employed. And the Detector finds where the image was edited." | unelte, domeniu |
| 5 | 1:16–1:25 | 9 s | Graful rețelei | "The Detective checks other applications: the same bank account, six applications, six different names." | |
| 6 | 1:25–1:45 | 20 s | **Situații neprevăzute:** un dosar cu poză neclară (OCR_LOW_QUALITY → la om, fără cloud) · o sumă „de verificat” · un agent „skipped” | "When something doesn't fit, ORB doesn't guess. A blurry photo never goes to the cloud; the file goes to a human. An amount the OCR may have misread is re-read before anyone is accused. If one agent fails, the others finish, and the gap is reported." | **agenți 25%** |
| 7 | 1:45–2:00 | 15 s | **Rezultat:** risc „Very high” → „Why this score?” → Approve cere motiv | "Compliance weighs the evidence with fixed rules, every line explained. The AI doesn't decide. The analyst does, and approving a flagged file takes a written reason." | excepție + om |
| 8 | 2:00–2:15 | 15 s | Dosarul cinstit: verde, valorile legate de sursă → dashboard cu orele | "Most files are honest. They come back clean in seconds, every value linked to its source. On twenty-one files: seven hours of checking, about twenty minutes of review, by our estimate." | valoare |
| 9 | 2:15–2:30 | 15 s | Privacy: ce a văzut AI-ul → butonul local | "And it's built for a bank: the cloud AI only sees stand-ins, a second gate checks every request before it leaves, and one switch runs everything in-house." | diferențiere |
| 10 | 2:30–2:46 | 16 s | Cardul cu cifrele (cu falsurile perfecte și „synthetic”) | "We tested sixty synthetic applications with the real AI: no names leaked, none of twelve honest applicants flagged high-risk, all thirty-six simple forgeries caught. Perfect forgeries mostly pass. The data and the forgeries are ours." | limite |
| 11 | 2:46–2:56 | 10 s | Schema arhitecturii (6 module) + README cu o comandă | "Six modules on one shared contract, tested, one command to run. Our ask: a pilot on a hundred real files, on the bank's own machine." | arhitectură 15% + pasul următor |
| 12 | 2:56–3:00 | 4 s | Outro animat ORB | "ORB does the checking. Your people decide." | |

### Ce se schimbă față de varianta 4
- **Maria devine fluxul principal** (input → procesare → rezultat → om), cum cer ei; dosarul cinstit trece la „valoare”.
- **Scenă nouă: situații neprevăzute** (25% din notă e pe asta și nu o arătam deloc).
- **Fiecare agent e numit când lucrează** (Guard, Clerk, Verifier, Detector, Detective, Compliance) → „agent design” vizibil.
  Am scos „four are plain code”: la criteriul lor ar suna ca „nu sunt agenți”. Spunem în schimb *de ce* (reguli fixe unde cifrele trebuie să fie exacte).
- **Arena scoasă** din video (linkul rămâne pe cardul de final). În finală nu se poate face live oricum.
- **Scenă nouă de arhitectură** (10 s): 6 module, contract comun, teste, o comandă.

### De filmat în plus
- un dosar cu **poză de telefon neclară** (din `scripts/benchmark_pipeline.py --phone --generate-only`) → OCR_LOW_QUALITY, fără cloud;
- o sumă „de verificat” (AMOUNT_UNCERTAIN) și un agent „skipped”, dacă le putem arăta pe un dosar real;
- schema arhitecturii (din `ARCHITECTURE.md`) ca imagine curată.

---

# Varianta 4 (istoric)

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
