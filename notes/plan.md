# Planul echipei — de acum până joi la 11:00

Actualizat: miercuri 28.10, ~15:50. **Citiți-l după fiecare `git pull`.**
Codul e gata și merge pe linkul public (https://orb-raiffeisen.vercel.app, backend la Narcis). De acum câștigăm
prin **cifre reale, video și pitch**, nu prin funcții noi. Detalii de pitch: `notes/pitch.md`.

## Reguli până la predare
- **Fără funcții noi.** Doar reparații. Orice schimbare → PR (se verifică automat) sau commit mic pe `main`.
- **Fără Claude în commit-uri** (nici `Co-Authored-By`, nici „Generated with Claude Code” în PR-uri).
- **Doar date inventate** (CNP cu `000`, IBAN sucursala 9999, CUI-urile din `app/arena/missions.py`).
- Token-ul de bancă și cheile nu se pun în git și nu pe grupul mare.

## Termene
| Când | Ce |
|---|---|
| miercuri până la 20:00 | cifrele reale (cronometrare + mentori), poze reale de telefon, prima versiune a videoului, testul Arenei |
| **miercuri 20:00** | **workshop de pitch — vin toți**, notăm ce vrea juriul de la video și cum e finala |
| miercuri seara | scenariul final al videoului + slide-urile |
| **joi 09:00** | **înghețăm codul**: Samuel curăță istoria git (rescrie istoria → toți clonează din nou) și face repo-ul public |
| joi 09:00–10:30 | înregistrăm videoul final (+ variantă de rezervă), redeploy final |
| **joi 11:00** | **predare**: video 3 min + link repo + link slide-uri — verificate dintr-o fereastră incognito |
| joi 12:00 | mentorat de business (2 sesiuni) |
| joi 17:00 | finala live, dacă intrăm în top 3 |

## Lorena
1. **Cronometrare manuală (cel mai important lucru de azi), cu Stefan.** Unul verifică de mână dosarul Mariei
   (`data/demo/maria/`: buletin, fluturaș, extras): citește actele, recalculează taxele, caută firma la ANAF, compară netul cu extrasul,
   caută dacă IBAN-ul/telefonul apare în alte dosare. Celălalt cronometrează. Repetați pe 2 dosare din benchmark
   (`backend/.venv/bin/python scripts/benchmark_pipeline.py --n 3 --save data/generated/bench --generate-only`).
   Notați minutele în `notes/pitch.md` → slide-ul „Cifre măsurate”, rândul „Timp manual pe dosar”.
2. **Slide-urile** (Google Slides, acces „oricine are linkul poate vedea”), 5–6 slide-uri: problema · soluția · cifre măsurate ·
   confidențialitate · adopție (mod umbră → asistent → triaj) · echipa. Textul e în `notes/pitch.md`. Stilul: cel al aplicației
   (gri, grafit, galben doar ca accent) — întreabă-o pe Erin.

## Stefan
1. **Cronometrarea, cu Lorena** (vezi mai sus).
2. **Vorbiți cu oamenii Raiffeisen** (mentori/organizatori), 5 minute: câte dosare pe zi, câte minute pe dosar, ce verifică un analist,
   câți analiști. O singură cifră de la ei → în `notes/pitch.md`.
3. **Q&A tehnic:** citește „Întrebări grele” din `notes/pitch.md` și partea ta din `notes/stefan.md`; tu răspunzi la taxe, ANAF, criptare.

## Narcis
1. **Poze reale de telefon:** tipărește sau afișează pe un ecran documentele Mariei (`data/demo/maria/`) și fotografiază-le cu 3–4
   telefoane diferite (lumină normală, ușor înclinat). Pune-le în `data/real_photos/<telefon>/` (sunt date inventate, pot intra în git)
   și spune-i lui Samuel — el le rulează prin ORB și măsoară. E testul pe care l-a cerut fiecare jurat.
2. **Laptopul băncii:** după orice `git pull`: `scripts/start_bank.sh --stop && scripts/start_bank.sh`. Ține-l pornit și pe priză.
   Modul rămâne `local` (Ollama) pentru demo; dacă se schimbă, spune pe grup.
3. **Joi dimineață:** primul care face `git pull` după curățarea istoriei (vezi termene) și repornește.

## Erin
1. **Arena pentru finala live** — lista completă în `notes/erin.md` („Arena pentru finala live”): QR spre linkul public,
   bug-urile de pe mobil/desktop, ecranul de start, „de ce te-am prins”, proiectorul ca spectacol.
2. **Prima versiune a videoului, cu Samuel:** înregistrare de ecran după scenariul din `notes/pitch.md`, fără montaj, ca să vedem
   dacă încape în 3 minute și ce nu se înțelege.
3. **Redeploy** după fiecare reparație de interfață: `scripts/deploy_frontend.sh` (sau commit gol + `npx vercel --prod`).
   Restul aplicației nu se mai schimbă până după video.

## Samuel
1. Verificarea automată a PR-urilor + reparații.
2. Rulează pozele reale de la Narcis și videoul de test prin „jurați” independenți; actualizează cifrele în `notes/pitch.md`.
3. Prima versiune a videoului, cu Erin; scenariul final după workshop.
4. **Joi 09:00:** curățarea istoriei git (scoate mențiunile Claude din commit-uri și din PR-uri), repo public, anunță pe grup
   „toată lumea: ștergeți clona și clonați din nou”.

## Toți
- **Testul Arenei, 15 minute, până la 20:00:** fiecare deschide https://orb-raiffeisen.vercel.app/arena de pe telefon,
  în același timp, cu `/arena/live` pe un ecran mare. Încercați să păcăliți sistemul. Ce se strică → pe grup, Erin repară.
- **Pitch:** fiecare știe în 30 de secunde ce a făcut el și răspunsul la o întrebare grea din `notes/pitch.md`.
