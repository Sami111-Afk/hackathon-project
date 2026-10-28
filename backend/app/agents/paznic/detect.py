"""Găsește datele personale în text: regex + cifre de control, MRZ, ancore pe etichete.

Ieșirea sunt span-uri (offset-uri în text), ca să poată fi mapate înapoi la bbox-uri
(ARCHITECTURE.md §4, pașii 2–5). GLiNER (nume/adrese fără etichetă) se adaugă peste.
"""
import re
from dataclasses import dataclass

from app.agents.paznic import validators as v


@dataclass(frozen=True)
class Span:
    kind: str           # CNP, IBAN, CUI, TELEFON, EMAIL, SERIE, NR, MRZ, PERSOANA, ADRESA, FIRMA
    start: int
    end: int
    value: str
    valid: bool | None = None  # None = fără cifră de control (nume, adresă, telefon…)


# prioritate la suprapuneri: MRZ acoperă tot ce e pe liniile lui
PRIORITY = {"MRZ": 0, "IBAN": 1, "CNP": 2, "CUI": 3, "SERIE": 4, "NR": 4, "EMAIL": 5, "TELEFON": 6,
            "ADRESA": 7, "FIRMA": 8, "PERSOANA": 9, "CONT": 10}

CNP_RX = re.compile(r"(?<!\d)[1-9]\d{12}(?!\d)")
# CNP scris cu separatori („259 031 229 0006”) — acceptat doar dacă cifra de control e validă (altfel ar prinde sume)
CNP_SPACED_RX = re.compile(r"(?<![\d.])[1-9](?:[ .\-]?\d){12}(?!\d)")
IBAN_RX = re.compile(r"\bRO\d{2}\s?[A-Z]{4}(?:\s?[A-Z0-9]{4}){4}\b", re.I)
# tolerant la OCR („R0”, un caracter în plus/lipsă, grupuri rupte): tot ascuns, chiar fără checksum (§4)
# „ROO5” = RO05; „ROO09” = RO09 (un „O” în plus)
IBAN_LOOSE_RX = re.compile(r"\bR[O0]{1,2}\s?[0-9OILSBZG]{2}\s?[A-Z]{4}(?:\s?[A-Z0-9]){15,17}\b", re.I)  # „ROOS” = RO05
CUI_RX = re.compile(r"\b(?:CUI|CIF|C\.U\.I\.|cod fiscal|cod unic de [îi]nregistrare)\s*[:.]?\s*((?:RO)?\s?\d{2,10})\b",
                    re.I)
PHONE_RX = re.compile(r"(?<!\d)(?:\+40|0040|0)[ .\-]?7(?:[ .\-]?\d){8}(?!\d)")
EMAIL_RX = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# zgomot de OCR între serie și număr („SERIA BV _ NR 946988”) și spații în număr („NR 86524 7”) e tolerat
SERIE_NR_RX = re.compile(r"\bSERIA\s*[:._|-]*\s*([A-Z]{2})\s*[:._|-]*\s*(?:NR\.?|N[O°]\.?)?\s*[:._|-]*\s*"
                         r"(\d(?: ?\d){5})(?!\d)", re.I)
MRZ_RX = re.compile(r"^[A-Z0-9<]{28,46}$")  # pe linia compactată (fără spații, « → <)
# seria + numărul fără eticheta „SERIA” (doar pe buletin, altfel ar prinde orice cod)
BARE_SERIE_NR_RX = re.compile(r"\b([A-Z]{2})\s?(\d{6})\b")

# eticheta → ce urmează după ea; pe buletin etichetele sunt bilingve („Nume/Nom/Last name”)
ANCHORS = {
    "PERSOANA": ["nume si prenume", "nume", "prenume", "nom", "prenom", "titular", "angajat", "salariat",
                 "solicitant", "client", "beneficiar", "platitor", "ordonator"],
    # locul nașterii e tot dată personală → îl tratăm ca adresă
    "ADRESA": ["domiciliu", "domiciliul", "adresa", "adresse", "address", "loc nastere", "loc nasterii"],
    "FIRMA": ["angajator", "angajatorul", "societatea", "employer"],
}
# etichete după care valoarea se termină (pe aceeași linie); „nr” lipsește intenționat (apare în adrese)
STOP_LABELS = ["cnp", "cui", "cif", "seria", "iban", "functia", "funcția", "brut", "net", "data", "sex",
               "cetatenie", "cetățenie", "nationalitate", "loc nastere", "emis", "valabilitate", "telefon",
               "email", "sold", "perioada", "cont"] + [a for labels in ANCHORS.values() for a in labels]
# traducerile de pe buletin: „Nume/Nom/Last name”, „Domiciliu/Adresse/Address”
_LABEL_TAIL = (r"(?:\s*/\s*(?:nom|prenom|last\s+name|first\s+name|surname|given\s+names?|adresse|address"
               r"|lieu\s+de\s+naissance|place\s+of\s+birth))*")

INJECTION_RX = re.compile(
    r"ignor[aăe]\w*\s+(?:toate\s+)?(?:instruc\w+|regul\w+)|ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)"
    r"|uit[aă]\s+(?:toate\s+)?instruc\w+|forget\s+(?:all\s+)?(?:previous\s+)?instructions"
    r"|system\s+prompt|you\s+are\s+now|e[sș]ti\s+acum\s+un|aprob[aă]\s+(?:acest|imediat|automat)"
    r"|approve\s+(?:this|the)\s+(?:loan|application)|r[aă]spunde\s+doar\s+cu\s+[\"„]?(?:aprobat|clear)"
    # mesaje adresate direct AI-ului / sistemului automat
    r"|\b(?:asistent(?:ul)?|assistant|llm|chatgpt|claude|gpt)\b(?:\s+ai)?\s*:"
    r"|(?:pentru|catre|to\s+the)\s+(?:sistemul|asistentul|modelul|automated\s+system|ai\b|llm\b)"
    r"|instruc\w+\s+(?:pentru|for)\s+(?:ai|llm|model|sistem|system|asistent|assistant)\b"
    # cereri de a schimba verdictul
    r"|marche\w*\s+(?:acest|aceasta|dosarul|clientul|cererea|documentul)\w*\s+(?:\w+\s+)?ca\s+"
    r"(?:sigur|valid|aprobat|legitim|curat|ok)"
    r"|(?:mark|classify|treat)\s+(?:this|the)\s+\w+\s+as\s+(?:safe|valid|approved|legit|clean|genuine)"
    r"|nu\s+(?:raporta|semnala|marca)\w*\s+(?:nicio|niciun|nimic)|(?:do\s+not|don'?t)\s+(?:flag|report)\b",
    re.I,
)


def _ascii_fold(text: str) -> str:
    table = str.maketrans("ăâîșşțţĂÂÎȘŞȚŢéèÉÈ", "aaissttAAISSTTeeEE")
    return text.translate(table)


# Plase de siguranță pentru OCR stricat (poze de telefon): IBAN-ul citit strâmb nu mai trece de regula strictă.
#  - tot ce urmează după eticheta „IBAN” pe același rând;
#  - orice șir de ≥10 cifre (cont, CNP rupt) — o sumă de bani nu are niciodată 10 cifre consecutive.
IBAN_LABEL_RX = re.compile(r"\bIBAN\b\s*[:.]?\s*([A-Z0-9][A-Z0-9 ]{12,40}[A-Z0-9])", re.I)
LONG_DIGITS_RX = re.compile(r"(?<![\d.,])\d(?: ?\d){9,}(?![\d,])")


def find_identifiers(text: str, id_card: bool = False) -> list[Span]:
    spans = _find_identifiers(text, id_card)
    # plasele de siguranță doar acolo unde regulile stricte n-au găsit nimic
    taken = [(s.start, s.end) for s in spans]
    free = lambda a, b: not any(a < e and s < b for s, e in taken)  # noqa: E731
    for m in IBAN_LABEL_RX.finditer(text):
        if free(m.start(1), m.end(1)):
            spans.append(Span("IBAN", m.start(1), m.end(1), m.group(1), None))
    for m in LONG_DIGITS_RX.finditer(text):
        if free(m.start(), m.end()):
            spans.append(Span("CONT", m.start(), m.end(), m.group(), None))
    return spans


def _find_identifiers(text: str, id_card: bool) -> list[Span]:
    spans = []
    for m in CNP_RX.finditer(text):
        spans.append(Span("CNP", m.start(), m.end(), m.group(), v.valid_cnp(m.group())))
    for m in CNP_SPACED_RX.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if m.group() != digits and v.valid_cnp(digits):
            spans.append(Span("CNP", m.start(), m.end(), m.group(), True))
    if id_card:
        for m in BARE_SERIE_NR_RX.finditer(text):
            if m.group(1).upper() in {"NR", "NO", "RO"}:
                continue
            spans.append(Span("SERIE", m.start(1), m.end(1), m.group(1)))
            spans.append(Span("NR", m.start(2), m.end(2), m.group(2)))
    for m in IBAN_LOOSE_RX.finditer(text):
        if v.valid_iban(m.group()):
            spans.append(Span("IBAN", m.start(), m.end(), m.group(), True))
        elif repaired := v.repair_iban(m.group()):
            # valoarea reparată intră în seif și în amprentă → aceeași amprentă ca IBAN-ul citit corect
            spans.append(Span("IBAN", m.start(), m.end(), repaired, True))
        else:
            spans.append(Span("IBAN", m.start(), m.end(), m.group(), False))
    for m in CUI_RX.finditer(text):
        val = m.group(1)
        spans.append(Span("CUI", m.start(1), m.end(1), val, v.valid_cui(val.replace(" ", ""))))
    for m in PHONE_RX.finditer(text):
        spans.append(Span("TELEFON", m.start(), m.end(), m.group()))
    for m in EMAIL_RX.finditer(text):
        spans.append(Span("EMAIL", m.start(), m.end(), m.group()))
    for m in SERIE_NR_RX.finditer(text):
        spans.append(Span("SERIE", m.start(1), m.end(1), m.group(1)))
        spans.append(Span("NR", m.start(2), m.end(2), m.group(2)))
    return spans


# ce citește OCR-ul des în locul lui „<” pe zona MRZ
_MRZ_FILLER_RX = re.compile(r"[«‹/\\|(\[{]")


def _compact_mrz(line: str) -> str:
    compact = re.sub(r"\s+", "", line).upper()
    # doar pe rânduri care au deja un „<” adevărat: altfel „IDENTITATE / IDENTITY CARD” ar deveni MRZ
    return _MRZ_FILLER_RX.sub("<", compact) if "<" in compact else compact


def _repair_mrz_line2(compact: str):
    """Rândul 2 TD2 are 36 de caractere; OCR-ul mai adaugă unul (ex. „<7/ROU” în loc de „<7ROU”).
    Scoatem câte un „<” până ies cifrele de control; altfel None (linia rămâne oricum ascunsă)."""
    parsed = v.parse_mrz_td2_line2(compact)
    if parsed or len(compact) != 37:
        return parsed
    for i, ch in enumerate(compact):
        if ch == "<" and (candidate := v.parse_mrz_td2_line2(compact[:i] + compact[i + 1:])) and candidate.valid:
            return candidate
    return None


def find_mrz(text: str) -> list[Span]:
    """Liniile MRZ se ascund integral. OCR-ul pune des spații între „<” → comparăm pe linia compactată.
    Validarea (7-3-1) se face doar pe ultima linie a blocului (linia 2 TD2)."""
    lines = []
    pos = 0
    for raw in text.split("\n"):
        start, end = pos, pos + len(raw)
        pos = end + 1
        s, e = _trim_mrz_noise(raw)
        compact = _compact_mrz(raw[s:e])
        # rândul 2 TD2 poate avea un singur „<” (PH481925<7ROU…) → ajunge unul, dacă linia e lungă
        if MRZ_RX.match(compact) and "<" in compact and len(compact) >= 30:
            lines.append((start + s, start + e, compact))
        elif "<" in compact and "ROU" in compact and len(compact) >= 25:
            # poză de telefon: zgomot și în interiorul liniei → n-o putem valida, dar e clar MRZ → o ascundem
            lines.append((start + s, start + e, None))
    spans = []
    for i, (start, end, compact) in enumerate(lines):
        is_last = i + 1 == len(lines) or text[end:lines[i + 1][0]].strip()
        parsed = _repair_mrz_line2(compact) if compact and is_last and i > 0 else None
        spans.append(Span("MRZ", start, end, compact or text[start:end], parsed.valid if parsed else None))
    return spans


def _trim_mrz_noise(raw: str) -> tuple[int, int]:
    """Capetele rândului fără „gunoi” de OCR („__ 15750912<4ROU… E =”): bucăți scurte fără „<” de la margini."""
    tokens = [(m.start(), m.end()) for m in re.finditer(r"\S+", raw)]
    while tokens and "<" not in raw[tokens[0][0]:tokens[0][1]] and tokens[0][1] - tokens[0][0] <= 2:
        tokens.pop(0)
    while tokens and "<" not in raw[tokens[-1][0]:tokens[-1][1]] and tokens[-1][1] - tokens[-1][0] <= 2:
        tokens.pop()
    return (tokens[0][0], tokens[-1][1]) if tokens else (0, 0)


def find_known_names(text: str, tokens: set[str]) -> list[Span]:
    """A doua trecere: numele găsite lângă etichete („Nume: …”) le ascundem ORIUNDE apar în dosar
    („Beneficiar: … IONESCU MARIA”, „Plată către Maria Ionescu”). Tokeni vecini → un singur span."""
    toks = {t for t in tokens if len(t) >= 3}
    if not toks:
        return []
    folded = _ascii_fold(text).lower()
    rx = re.compile(r"(?<![\w\[])(?:" + "|".join(re.escape(_ascii_fold(t)) for t in sorted(toks, key=len, reverse=True))
                    + r")(?!\w)")
    hits = [(m.start(), m.end()) for m in rx.finditer(folded)]
    spans: list[Span] = []
    for start, end in hits:
        if spans and re.fullmatch(r"[\s,.\-]{1,3}", text[spans[-1].end:start]):
            prev = spans.pop()
            start = prev.start
        spans.append(Span("PERSOANA", start, end, text[start:end]))
    return spans


def find_anchored(text: str) -> list[Span]:
    """Valoarea de după o etichetă cunoscută: pe aceeași linie sau, dacă linia e goală, pe următoarea."""
    folded = _ascii_fold(text).lower()  # aceeași lungime ca textul → offset-urile rămân valabile
    stop_rx = re.compile(r"\b(?:" + "|".join(re.escape(_ascii_fold(s)) for s in STOP_LABELS) + r")\b\s*[:/]?")
    spans = []
    for kind, labels in ANCHORS.items():
        label_rx = re.compile(r"(?<![\w\[])(?:" + "|".join(re.escape(lbl) for lbl in labels) + r")\b" + _LABEL_TAIL
                              + r"\s*[:\-]?[ \t]*")
        for m in label_rx.finditer(folded):
            start = m.end()
            line_end = text.find("\n", start)
            line_end = len(text) if line_end == -1 else line_end
            rest = text[start:line_end].strip()
            # valoarea e pe linia următoare; „/…” = traducerea etichetei, citită greșit de OCR („/Prenoni/First nane”)
            if (not rest or rest.startswith("/")) and line_end < len(text):
                start = line_end + 1
                line_end = text.find("\n", start)
                line_end = len(text) if line_end == -1 else line_end
            stop = stop_rx.search(folded, start, line_end)
            end = stop.start() if stop else line_end
            raw = text[start:end]
            value = raw.strip(" \t:,;")
            if len(value) < 3 or not re.search(r"[A-Za-zÀ-ÿ]", value) or value.startswith("["):
                continue
            if kind == "PERSOANA" and (len(value.split()) > 5 or re.search(r"\d", value)):
                continue
            offset = start + raw.index(value)
            spans.append(Span(kind, offset, offset + len(value), value))
    return spans


def find_prompt_injection(text: str) -> bool:
    return bool(INJECTION_RX.search(_ascii_fold(text)))


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Păstrează un singur span pe fiecare zonă: prioritatea tipului, apoi cel mai lung."""
    chosen: list[Span] = []
    for s in sorted(spans, key=lambda s: (PRIORITY.get(s.kind, 99), -(s.end - s.start), s.start)):
        if all(s.end <= c.start or s.start >= c.end for c in chosen):
            chosen.append(s)
    return sorted(chosen, key=lambda s: s.start)


def looks_like_id_card(text: str) -> bool:
    folded = _ascii_fold(text).lower()
    return "carte de identitate" in folded or "identity card" in folded or "idrou" in folded.replace(" ", "")


# Adrese recunoscute după FORMĂ, nu după etichetă: pe pozele de telefon OCR-ul strică des „Domiciliu/Adresse”,
# iar adresa de pe rândul următor rămânea în clar (benchmark --phone). Restul rândului (oraș, județ) e ascuns și el.
_STREET = r"(?:str|strada|bd|b-dul|bulevardul|calea|aleea|sos|șos|soseaua|șoseaua|piata|piața|intrarea|splaiul)"
STREET_RX = re.compile(r"(?<![\w\[])" + _STREET + r"\b\.?\s+[^\n\[\]]{2,40}?\bnr\.?\s*\d+[^\n]*", re.I)
# „… nr. 14, Timișoara, jud. Timiș” — OCR-ul a mâncat chiar „Str.”: nr. + jud. pe același rând
NR_JUD_RX = re.compile(r"[^\n\[\]]{2,60}\bnr\.?\s*\d+[A-Za-z]?\b[^\n]*?\bjud(?:etul|ețul)?\b\.?\s*[^\n]*", re.I)
# locul nașterii: „Mun. Ploiești, Jud. PH”
BIRTHPLACE_RX = re.compile(r"\b(?:mun|municipiul|or|oras|oraș|com|comuna|sat)\.?\s+[^\n,\[\]]{2,30},"
                           r"\s*jud\.?\s*[^\n]{2,20}", re.I)


# pe buletin, singurele rânduri cu „jud.” sunt domiciliul și locul nașterii → oricum le-ar fi citit OCR-ul
# („Victoriei pr. 96, Ploiești, jud. Prahova”, „ser. Zorilor nr Sa Cluj-Napoca, jud. Cluj”)
ID_CARD_JUD_RX = re.compile(r"[^\n]*\bjud\b[^\n]*", re.I)


def find_addresses(text: str, id_card: bool = False) -> list[Span]:
    spans = []
    for rx in (STREET_RX, NR_JUD_RX, BIRTHPLACE_RX) + ((ID_CARD_JUD_RX,) if id_card else ()):
        for m in rx.finditer(text):
            value = m.group().strip(" \t,;")
            if not value:
                continue
            start = m.start() + m.group().index(value)
            spans.append(Span("ADRESA", start, start + len(value), value))
    return spans


def find_all(text: str, known_names: set[str] | None = None) -> list[Span]:
    spans = find_mrz(text) + find_identifiers(text, looks_like_id_card(text)) + find_anchored(text)
    spans += find_addresses(text, looks_like_id_card(text))
    if known_names:
        spans += find_known_names(text, known_names)
    return resolve_overlaps(spans)
