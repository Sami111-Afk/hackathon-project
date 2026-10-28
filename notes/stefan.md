# Stefan — Funcționar, Verificator, criptare homomorfică, ANAF (pentru pitch)

## Cele 30 de secunde

> „Eu am făcut cei doi agenți care **citesc și verifică** documentele.
> **Funcționarul** citește fluturașul, extrasul și buletinul. LLM-ul vede doar textul cu datele personale deja ascunse
> și **nu are voie să inventeze**: fiecare valoare trebuie să existe în document, altfel o aruncăm. Rândurile din extras
> le citim fără LLM, ca să nu sară sau să inventeze tranzacții.
> **Verificatorul** reface calculele: taxele de pe fluturaș — **pe date criptate homomorf**, de un verificator terț care
> nu vede salariul —, soldurile din extras rând cu rând, firma la **ANAF** și verificări românești: vârsta din CNP,
> seria buletinului, banca din IBAN.
> La Maria: netul nu iese din brut, soldul final e umflat de 9 ori, firma e inactivă, iar ea are 67 de ani și încasează pensie.
> Pe benchmark: **240 de documente, zero date personale scăpate, zero oameni cinstiți acuzați.**”

## Cifre pe care le putem spune (din `data/benchmark/pipeline_results.json`)

Benchmark pe **documente-imagine** prin agenții reali (OCR Tesseract → Paznic → Funcționar → Verificator):
80 de dosare = **240 de documente**, jumătate curate, jumătate scanate prost (rotite, blurate, JPEG slab).

| | |
|---|---|
| Date personale scăpate (text pentru LLM, câmpuri, mesaje) | **0 / 80 dosare** |
| Oameni cinstiți acuzați | **0 / 16** |
| Falsuri prinse: net umflat · sold falsificat · firmă inactivă | **16/16 · 16/16 · 16/16** |
| Extragere corectă, cel mai slab câmp | ≥ 92% (curat: ≥ 95%) |
| Timp pe dosar (3 documente, laptop, CPU) | 4–5 s (cu recitirea sumelor la nepotriviri) |
| Verificarea netului pe date criptate | ~0,3 s, context public ~1,8 MB |
| Cost LLM (Featherless) | ~0,0002 $ / document |

**Cum le spunem corect:** „pe documente sintetice generate de noi, cu layout cunoscut” — arată că lanțul e
implementat corect, nu că prindem orice fals real. Nu spunem „100% acuratețe”.

## Dosarul Mariei — ce găsește Verificatorul

| Severitate | Ce | Dovadă |
|---|---|---|
| high | Netul calculat (8.307 lei) diferă de cel declarat (8.500 lei) | chenar pe sumă, pe fluturaș |
| critical | Angajatorul figurează inactiv la ANAF | |
| high | Soldul final (26.480 lei) nu iese din tranzacții (2.851,50 lei) | chenar pe sold, pe extras |
| medium | Netul de pe fluturaș nu apare ca încasare în extras | |
| low | Extrasul arată o încasare de **pensie**, deși se declară angajată | chenar pe rând |
| medium | Solicitantă de 67 de ani declarată angajată activ | |

Netul e verificat **pe date criptate**; rezultatul e identic cu calculul în clar.

## Cum funcționează (pentru întrebări tehnice)

**Funcționar**
- Tipul documentului: după titluri („FLUTURAȘ DE SALARIU”, „EXTRAS DE CONT”); LLM doar dacă nu se recunoaște.
- LLM-ul primește textul redactat (`[PERSOANA_1]`, `[CNP_1]` …), întoarce valori brute + fragmentul citat.
  **Grounding:** fragmentul trebuie găsit în textul OCR, iar suma/data trebuie să fie exact cea din document.
  În teste, un LLM care „corecta” netul 8.500 → 8.307 e respins.
- Plasă de siguranță: extragere pe etichete, fără LLM — demo-ul merge și fără internet / cu cheia expirată.
- Identificatorii intră în câmpuri **doar ca etichete**; dacă Paznicul a ratat ceva, câmpul e aruncat.

**Verificator — taxe** (simplificare declarată)
- `net = 0,585·G + 0,415·N + 0,1·D`, toleranță ±2 lei. G = brut, N = suma netaxabilă la salariul minim
  (OUG 89/2025: 200 lei din iulie 2026, pentru brut între 4.325 și 4.600 lei), D = deducerea personală (tabel simplificat).
- Salariul minim după luna fluturașului (4.050 → 4.325 lei din iulie 2026). Persoanele în întreținere nu scriu pe
  fluturaș → acceptăm oricare variantă 0–4, ca să nu acuzăm oamenii cu copii.

**Criptare homomorfă (CKKS, TenSEAL)**
- Banca criptează brutul, N, D, netul declarat (și corecția de rotunjire). **Verificatorul terț primește doar contextul
  public** — nu poate decripta — și calculează diferența pe date criptate. Banca decriptează și aplică pragul.
- Rezultatul decriptat **nu se trimite înapoi** verificatorului (atacul Li–Micciancio pe decriptări CKKS partajate).

**ANAF**
- API-ul public PlatitorTvaRest v9, cu cache local 24 h, maximum 1 apel/s, fiecare apel în jurnalul de audit;
  în modul local, zero apeluri externe. Firmele din demo sunt inventate (CUI-uri verificate ca inexistente la ANAF).

**Extras:** sold anterior + sumă = sold, pe fiecare rând; soldul final = ultimul rând; netul de pe fluturaș trebuie
să apară ca încasare.

## Ce spunem onest (limite)

- **HE nu ascunde nimic de bancă** — banca are deja datele. Permite unui verificator *terț* să calculeze fără să le vadă.
  CKKS dă confidențialitate, nu integritate: un verificator rău-intenționat poate întoarce orice.
- **Fals „perfect”** (brut umflat, taxe refăcute corect): fluturașul singur nu-l poate prinde. Semnalul există
  (16/16: netul nu apare în extras), dar e sub pragul de review → nu e escaladat.
- **OCR-ul greșește cifre** (~2–3 din 40 de dosare, ex. 7.952 → 1.952). De aceea, **înainte de a acuza**, Verificatorul
  recitește de pe imagine doar zona sumei (6 citiri, vot). Dacă la recitire calculul iese → „probabil eroare de citire,
  de verificat” (`AMOUNT_UNCERTAIN`), nu acuzație; dacă recitirea confirmă cifra (falsul e tipărit) → acuzația rămâne.
  În benchmark: ambele solduri citite greșit au devenit „de verificat”, toate cele 16 extrase falsificate au rămas prinse.
  Tot omul decide.
- Taxele sunt o **simplificare declarată** (fără tichete, avansuri, popriri; deducerea pe tabel simplificat).
- Registrul ANAF al demo-ului e simulat pentru firmele inventate; pentru CUI-uri reale interogăm ANAF-ul real.

## Întrebări probabile

**„Ce vede LLM-ul?”** — Text cu identificatorii înlocuiți de etichete; o poartă blochează apelul dacă apare un CNP,
IBAN sau o valoare din seif. Pozele buletinului nu pleacă niciodată. În producție: LLM local / on-prem (avem modul local).

**„Și dacă LLM-ul halucinează?”** — Fiecare valoare trebuie să existe în textul documentului (grounding), iar sumele le
parsează Python, nu LLM-ul. Ce nu se regăsește e aruncat și raportat.

**„De ce criptare, dacă banca are datele?”** — Ca un motor de reguli externalizat, alt departament sau altă instituție
să poată rula verificarea fără să vadă salariul. Nu pretindem mai mult.

**„Ce faceți dacă OCR-ul greșește?”** — Paznicul repară confuziile tipice (O/0, caractere în plus) cu cifrele de control;
ce nu poate repara rămâne ascuns. Înainte de o acuzație pe o sumă, Verificatorul o recitește de pe imagine; dacă la
recitire calculul iese, marchează „de verificat”, nu „fals”. Și oricum doar recomandă — omul decide, cu chenarul pe document.

**„Cât costă / cât durează?”** — 4–5 secunde și ~0,0006 $ pe un dosar de 3 documente, pe un laptop.

**„Merge pe documente reale?”** — Am testat pe documente sintetice cu layout cunoscut; pentru alte layout-uri,
LLM-ul face extragerea, iar extrasele ar avea nevoie de parsarea pe coloane per bancă.

## Review PR #25
Nu l-am îmbinat încă. Ideea e bună (fluturașul Mariei e tot prins: NET_MISMATCH 8.307 vs 8.500, verdict escalate; HE rămâne în uz; nicio sumă recitită nu e logată sau trimisă la LLM; `ai_saw.with_pii == 0`; recitirea rulează în `asyncio.to_thread`), dar:
- **Teste picate (4)**: `recitire` apelează `pytesseract.image_to_string` fără `lang`, deci cere `eng`. README/ARCHITECTURE cer doar `ron` (la mine există doar `ron` + `osd`) → `TesseractError`, recitirea eșuează în tăcere (`except Exception` → rămâne citirea inițială) și testele din `tests/test_reread.py` pică (`test_read_amount_from_crop`, cele două cu AMOUNT_UNCERTAIN pe sold, cea pe fluturaș).
- Cu `lang="ron"` trec 3 din 4, dar `test_ocr_digit_error_inside_a_row_is_not_an_accusation` dă al doilea rând tot BALANCE_MISMATCH → votul cu `ron` e mai slab pe decupaje; de reglat (ori `eng` documentat ca cerință + `ocr_available()` să verifice și `eng`).
- Cerință: `Rereader.available()` să verifice limba pe care o folosește chiar recitirea, ca să nu pară activ când nu e.
- Testele din `test_reread.py` durează ~16 s (OCR real) — de marcat ca lente sau reduse.

### Răspuns (Stefan)
- **Limba:** recitirea folosește `eng` dacă e instalată (vine implicit cu Tesseract; citește cifrele mai bine — `ron` confundă des „7” cu „1” pe fontul nostru, chiar și la recitire), altfel `ron`. Reprodus mediul tău (doar `ron` + `osd`, cu `TESSDATA_PREFIX`): toate testele trec.
- **Votul:** 8 citiri (măriri ×2 și ×3 × 2 contraste × `--psm 7/13`), minimum 3 voturi și strict mai multe decât a doua valoare; citirile în format EN (`9,547.50`) sunt interpretate corect, cele incomplete nu votează.
- **`Rereader.available()`** verifică exact limba aleasă (`digit_lang()`).
- **Viteză:** testele cu OCR real sunt `@pytest.mark.slow`; `pytest.ini` le exclude implicit (`-m "not slow"`), rulează cu `pytest -m slow` (~15 s). Parsarea citirilor e în `test_reread_parse.py` și rulează și în CI.
- **Benchmark:** dacă un agent pică (am prins o dată un `OSError` trecător de la OCR-ul în paralel pe Windows), îl reîncercăm o dată; altfel dosarul e raportat ca eroare și nu mai intră în detecție (înainte Funcționarul trecea pe datele de probă ale Mariei și număra acuzațiile ei).

