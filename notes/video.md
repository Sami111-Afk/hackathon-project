# Video 3:00 — scenariu + textul vocii (engleză)

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
