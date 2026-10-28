# Pitch ORB — schiță pentru video (3:00), slide-uri și mentorat

Scris de Samuel pe 28.10, ~15:30, din feedback-ul a 8 „jurați” independenți (bancă, securitate, AI, avocatul diavolului — 2 runde).
Consens: **tehnic suntem peste medie; pierdem dacă povestea e „fraudă + multă tehnologie”**. Tema Raiffeisen e
*eficiență operațională: muncă repetitivă cu documente, date, verificare* → asta e povestea.

**Fraza de deschidere:** „ORB face verificarea repetitivă a dosarelor de credit în 20 de secunde în loc de X minute —
fără ca datele clienților să iasă din bancă. Fraudele prinse sunt bonusul.”

## Video — 3:00 (ce se vede · ce se spune)

| Timp | Pe ecran | Text (idee) |
|---|---|---|
| 0:00–0:20 | Un analist cu 3 documente (buletin, fluturaș, extras) + cronometru | „Azi, un analist citește actele, recalculează taxele, caută firma la ANAF, compară cu extrasul. **Am cronometrat: X minute pe dosar.**” |
| 0:20–0:40 | Dashboard → „Dosar nou” → încarcă un dosar **cinstit** → aprobat | „Un dosar normal: ORB verifică tot, analistul aprobă. 20 de secunde.” (eficiența = munca repetitivă scoasă) |
| 0:40–1:40 | Dosarul Mariei, „Analizează din nou, live”: cei 6 agenți pornesc; dovezile apar pe document („Arată pe document”) | „Același flux pe Maria, 67 de ani: netul nu iese din brut (8.307 vs 8.500), firma e inactivă, soldul nu se adună, zona netului a fost editată.” |
| 1:40–2:00 | Graful: Maria legată de alte 5 cereri prin același IBAN | „Ce nu vede un om dosar cu dosar: același cont în 6 cereri, pe 6 identități.” |
| 2:00–2:20 | Nivel de risc + „De ce acest scor?” + butonul de decizie (aprobarea cere motiv) | „AI-ul nu decide. Scorul e calculat din dovezi, fiecare explicată; omul decide și semnează.” |
| 2:20–2:40 | Panoul Confidențialitate: „Ce a văzut AI-ul” ([PERSOANA_1], [CNP_1]) + butonul Local (la Narcis, fără internet) | „AI-ul vede doar etichete. Poza neclară sau buletinul nu pleacă deloc în cloud. Sau totul rulează local, pe un laptop.” |
| 2:40–3:00 | Slide cu cifrele măsurate + „mod umbră → asistent → triaj” | „Am măsurat, nu am estimat. Propunem un pilot în mod umbră.” |

**Taiem din video** (rămân în repo + un slide „ce mai avem”): ZK, criptarea homomorfă, Arena, Atacatorul, self-learning.
Excepție posibilă: 5–10 s de Arena la final („oricine poate încerca să-l păcălească”) — doar dacă rămâne timp.
**Finala live** (dacă intrăm): acolo Arena cu QR pentru juriu e momentul de neuitat.

## Slide „Cifre măsurate” (doar ce am măsurat; fiecare cu sursa)

| Ce | Valoare | Sursă / cum |
|---|---|---|
| Timp manual pe dosar | **X min** (de cronometrat: un coleg, 3 dosare) | cronometru; + cifra de la mentorii Raiffeisen |
| Timp ORB pe dosar | **~13–20 s** cloud · **8–9 s** local (RTX 4060, Ollama — testat și pe linkul public) | dosarul Mariei; benchmark |
| Cost AI pe dosar | **~0,005 $** (Haiku extrage, Sonnet rezumă) | `llm_usage` pe dosarul Mariei |
| Date personale trimise la AI-ul din cloud | **0 din 40** (curat) · **0 din 20** (poze de telefon) | `scripts/benchmark_pipeline.py`, `data/benchmark/pipeline_results.json` |
| Oameni cinstiți acuzați | **0 din 8** (curat) · pe poze proaste: trimiși la om, nu acuzați | idem |
| Falsuri prinse (net umflat / sold / firmă inactivă) | 8/8 · 8/8 · 8/8 pe documente curate | idem |
| Cu AI-ul real (Haiku/Bedrock), 20 dosare | **0 valori inventate** (filtrul n-a avut ce opri) · **198/200 câmpuri corecte** · 0 cinstiți acuzați · 12/12 falsuri prinse · ~13 s/dosar | `--llm bedrock`, cheia `clean_bedrock` |

**Spunem deschis:** date sintetice, falsuri create de noi → „test de corectitudine a lanțului, nu acuratețe pe fraude reale”.
Ce NU prindem: falsul „perfect” (taxe refăcute corect) nu se vede din fluturaș — doar din extras/ANAF.
Pe poze proaste de telefon, extragerea scade mult → ORB trimite dosarul la om în loc să ghicească.

## Mentorat (joi 12:00) — 3 criterii, 1–5

- **Problema și utilizatorul:** analistul de credit / back-office-ul de verificare. Durerea: munca repetitivă (citit, recalculat,
  căutat la ANAF, comparat documente) + fraudele de identitate care trec printre degete. *Întrebăm mentorii:* câte dosare pe zi,
  câte minute pe dosar, câți analiști, cât din timp e verificare de documente.
- **Valoarea:** minute → secunde pe dosar; fiecare dovadă arătată pe document (analistul verifică în 1 minut, nu refacere de la zero);
  rețele de fraudă văzute între dosare. Costul AI ~0,005 $/dosar.
- **Adopția:** mod umbră (ORB rulează lângă analist, nu decide) → asistent (pre-completează) → triaj (dosarele curate merg rapid).
  AI-ul nu ia decizii (AI Act: om în buclă, explicabil). Datele: pseudonimizate spre cloud, sau 100% local. Audit pe fiecare apel.
  *De spus deschis:* validarea modelului (MRM), integrarea cu sistemul de credite și sursa documentelor = pașii de pilot.

## Întrebări grele + răspunsuri oneste

- **„De ce 99,8?”** — Nu e o probabilitate. E un scor de gravitate: dovezile au ponderi după severitate, multe dovezi grave îl împing spre 100.
  De asta afișăm nivelul (foarte mare) și lista de dovezi, nu procentul.
- **„Cum știți că prindeți fraude reale?”** — Nu știm încă: am testat corectitudinea pe date sintetice. Pentru fraude reale ne trebuie
  dosare etichetate de la bancă — primul pas al pilotului.
- **„Ce garantează că AI-ul nu vede date personale?”** — Nimic absolut: sunt straturi (redactare, poartă la ieșire, refuz pe poze neclare, buletinul
  nu pleacă niciodată). Pe benchmark: 0 trimise în cloud. Garanția totală = modul local.
- **„Ce garantează că AI-ul nu halucinează?”** — Fiecare valoare extrasă trebuie să existe exact în document (altfel e aruncată), scorul nu depinde
  de AI, iar fiecare cifră din rezumat e verificată în dovezi (altfel rezumatul e înlocuit).
- **„De ce criptare homomorfă dacă banca are datele?”** — Pentru calcule externalizate: un verificator terț reface calculul pe salariul criptat
  fără să-l vadă. E un prototip; CKKS dă confidențialitate, nu corectitudine.
- **„ZK?”** — Clientul dovedește „venit ≥ prag” fără să arate salariul; încrederea e în angajatorul care semnează (simulat la noi; real: REVISAL/D112).
  Util pentru pre-eligibilitate, nu pentru dosarul final.
- **„Self-learning-ul nu poate strica sistemul?”** — Regulile sunt într-un format limitat (nu cod), testate pe istoric (respinse dacă acuză oameni cinstiți)
  și aprobate de un om. Recunoaștem: azi e testat pe date sintetice.
- **„Atacatorul e AI?”** — Nu, e un atacator automat (algoritm) care se adaptează la ce l-a prins. Claude a refuzat să joace rolul de falsificator.
- **„Agenți sau funcții?”** — 6 roluri specializate cu eșec izolat; AI-ul doar citește și explică. Nu vindem „agenți care raționează”.

## Înainte de înregistrare (checklist)
- [ ] Cineva cronometrează verificarea manuală a 3 dosare → cifra X
- [ ] Mentorii: dosare/zi, minute/dosar (dacă avem acces până la video)
- [ ] `git pull` + `scripts/start_bank.sh` la Narcis; `scripts/deploy_frontend.sh` la Erin
- [ ] Rerun Maria o dată înainte (cache cald); un dosar cinstit pregătit pentru „Dosar nou”
- [ ] Înregistrare de rezervă a demo-ului complet
