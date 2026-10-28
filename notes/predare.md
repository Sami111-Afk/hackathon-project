# Predare — joi 29.10, 11:00

## Ce predăm (formularul organizatorilor)
1. **Video 3:00** — `video/out/ORB_video_AI.mp4` sau `ORB_video_Samuel.mp4` (alegem pe grup). Urcat pe YouTube (Unlisted)
   sau Google Drive cu „oricine are linkul” → link verificat dintr-o fereastră incognito.
2. **Repo:** https://github.com/Sami111-Afk/hackathon-project (public, istoria curățată pe 28.10 seara).
3. **Slide-uri:** Google Slides, „oricine are linkul poate vedea” (Lorena, `scripts/make_presentation.py --lang en`).
4. Numele echipei, emailul liderului, titlul + descrierea proiectului.

## Dimineață, înainte de 11:00
- **Erin:** `git fetch origin && git reset --hard origin/main && scripts/deploy_frontend.sh` (designul nou + pagina de prezentare ascunsă).
- **Narcis:** `git fetch origin && git reset --hard origin/main && scripts/start_bank.sh --stop && scripts/start_bank.sh`.
  Laptopul pornit și în priză **11:00–15:30** (juriul verifică linkul public). Rămâne pe `LLM_MODE=local`.
- Token-ul de bancă pentru juriu se trimite separat (nu în formular public, nu pe grupul mare).
- Cheia Bedrock de pe laptopul lui Samuel expiră joi ~10:40 — cine are nevoie de cloud cere una nouă de la organizatori.

## După predare
- 12:00 mentorat de business (2 sesiuni): cine e utilizatorul, valoarea, barierele (date în UE / local, SSO, date reale etichetate).
- 15:30 checkpoint juriu — cineva disponibil pentru întrebări.
- 16:00 finaliștii · 16:30 deck-ul final · 17:00 finala (doar video, fără demo live).
- Întrebările grele + răspunsurile: `notes/video.md` („Întrebări grele la finală”).

## Repo-ul rescris (28.10 seara)
Toți: `git fetch origin && git reset --hard origin/main` în clona voastră (vă păstrează `.env`-ul). **Nu dați push din ramuri vechi.**
