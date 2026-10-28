"""Zgomot de OCR văzut pe documentele reale ale Mariei: IBAN cu un caracter în plus, MRZ cu „/” în loc de „<”."""
import pytest

from app.agents.paznic import detect
from app.agents.paznic import validators as v
from app.agents.paznic.redact import fingerprint, normalize_value

TRUE_IBAN = "RO54RZBR0000060012345678"  # valid; așa l-a citit OCR-ul: RO54RZBR0O000060012345678


@pytest.mark.parametrize(
    ("ocr", "fixed"),
    [
        ("RO54RZBR0O000060012345678", TRUE_IBAN),        # un „O” în plus, lipit de zerouri (văzut pe extras)
        ("RO54RZBR0000O60012345678", TRUE_IBAN),         # „O” în loc de „0”
        ("R054RZBR0000060012345678", TRUE_IBAN),         # „R0” în loc de „RO”
        ("ROO5RZBR9999000000000003", "RO05RZBR9999000000000003"),  # „O” în cifrele de control (benchmark)
        ("RO54 RZBR 0000 06OO 1234 5678", TRUE_IBAN),    # grupuri cu spații + confuzii
        ("RO59RZBR9999000000000001", "RO59RZBR9999000000000001"),  # deja valid → neschimbat
        ("RO00RZBR9999000000000001", None),              # cifre de control greșite, nu e zgomot de OCR
        ("RO54RZBR00000600123456", None),                # prea scurt
    ],
)
def test_repair_iban(ocr, fixed):
    assert v.repair_iban(ocr) == fixed


def test_misread_iban_is_hidden_and_gets_the_true_fingerprint():
    text = "Titular: X\nIBAN: RO54RZBR0O000060012345678\nPerioada: 01.09.2026"
    spans = [s for s in detect.find_identifiers(text) if s.kind == "IBAN"]
    assert len(spans) == 1
    s = spans[0]
    assert text[s.start:s.end] == "RO54RZBR0O000060012345678"  # tot fragmentul citit e ascuns
    assert s.valid and s.value == TRUE_IBAN
    # aceeași amprentă ca IBAN-ul citit corect → Detectivul leagă dosarul de rețea
    assert fingerprint("k", "IBAN", normalize_value("IBAN", s.value)) == \
        fingerprint("k", "IBAN", normalize_value("IBAN", TRUE_IBAN))


def test_iban_with_letter_in_check_digits_is_hidden():
    text = "IBAN: ROO5RZBR9999000000000003"  # văzut în benchmark: „RO05” citit „ROO5”
    s = next(s for s in detect.find_identifiers(text) if s.kind == "IBAN")
    assert text[s.start:s.end] == "ROO5RZBR9999000000000003" and s.value == "RO05RZBR9999000000000003"


def test_unrepairable_iban_is_still_hidden():
    text = "IBAN: RO00RZBR99990000000000012"
    s = next(s for s in detect.find_identifiers(text) if s.kind == "IBAN")
    assert s.valid is False and text[s.start:s.end].startswith("RO00RZBR")


def test_normal_text_is_not_an_iban():
    text = "RO 2026 · Raiffeisen BANK · Sold final 26.480,00 · ROU5903128"
    assert not [s for s in detect.find_identifiers(text) if s.kind == "IBAN"]


MRZ_L1 = "IDROUIONESCU<<MARIA<<<<<<<<<<<<<<<<<"
MRZ_L2 = "PH481925<7ROU5903128F290312722900067"


def test_mrz_line2_with_slash_and_extra_char_is_hidden_and_validated():
    ocr_l1 = "IDROUIONESCU<<MARIA<< <<< <<< << << <<< <<"
    ocr_l2 = "PH481925<7/ROU5903128F290312722900067"  # exact cum a citit OCR-ul buletinul Mariei
    text = f"Valabilitate\n20.05.19-12.03.2029\n{ocr_l1}\n{ocr_l2}"
    spans = detect.find_mrz(text)
    assert [text[s.start:s.end] for s in spans] == [ocr_l1, ocr_l2]
    assert spans[1].valid is True  # „/” scos → cifrele de control ies → verificarea MRZ vs CNP merge


def test_mrz_spans_win_over_series_inside_the_line():
    text = f"{MRZ_L1}\nPH481925<7/ROU5903128F290312722900067"
    spans = detect.find_all(text)
    line2 = text.split("\n")[1]
    covering = [s for s in spans if s.kind == "MRZ" and text[s.start:s.end] == line2]
    assert covering and not [s for s in spans if s.kind in ("SERIE", "NR")]


def test_label_lines_with_slashes_are_not_mrz():
    text = "Nume/Nom/Last name\nCetățenie/Nationalité/Nationality\nLoc naștere/Lieu de naissance/Place of birth"
    assert detect.find_mrz(text) == []


def test_id_card_title_with_slash_is_not_mrz():
    text = "CARTE DE IDENTITATE / IDENTITY CARD SERIA PH NR 481925\nCNP 1234"
    assert detect.find_mrz(text) == []
    kinds = {s.kind for s in detect.find_identifiers(text)}
    assert {"SERIE", "NR"} <= kinds


def test_benchmark_ocr_cases_are_hidden():
    # văzute în scripts/benchmark_pipeline.py pe dosare generate curat
    s = next(s for s in detect.find_identifiers("IBAN: ROO09RZBR9999000000000028") if s.kind == "IBAN")
    assert s.valid and s.value == "RO09RZBR9999000000000028"
    text = "CARTE DE IDENTITATE / IDENTITY CARD SERIA BV _ NR 946988"
    spans = {s.kind: text[s.start:s.end] for s in detect.find_identifiers(text)}
    assert spans.get("SERIE") == "BV" and spans.get("NR") == "946988"


def test_garbled_bilingual_label_does_not_hide_the_label_instead_of_the_name():
    # benchmark, buletin degradat: traducerea etichetei citită greșit → numele de pe rândul următor rămânea vizibil
    text = "Prenume/Prenoni/First nane\nELENA\nCetățenie/Nationalité/Nationality\nRomână / ROU"
    names = [text[s.start:s.end] for s in detect.find_anchored(text) if s.kind == "PERSOANA"]
    assert names == ["ELENA"]


@pytest.mark.parametrize("line", [
    "IBAN: RO1 0RZBR9999000000000010",   # spațiu în locul greșit
    "IBAN: ROBORZBR9999000000000011",    # „0” citit „O”, cifra de control pierdută
    "IBAN RO58RZB R9999000000000019",
])
def test_garbled_iban_after_label_is_hidden(line):
    from app.agents.paznic.detect import find_all
    spans = find_all(line)
    assert spans and all(s.kind in ("IBAN", "CONT") for s in spans)
    assert "9999000000000" not in "".join(line[:s.start] + line[s.end:] for s in spans)


def test_long_digit_runs_hidden_but_amounts_and_phones_kept():
    from app.agents.paznic.detect import find_all
    kinds = {s.value: s.kind for s in find_all("Cont 9999 0000 0000 0001. Sold 26.480,00. Tel 0722 123 456")}
    assert kinds.get("9999 0000 0000 0001") == "CONT"
    assert "26.480,00" not in kinds and kinds.get("0722 123 456") == "TELEFON"


@pytest.mark.parametrize("line", [
    "Str. Mihai viteazu nr. 13, Ploiești, jud. Prahova",     # văzute în benchmark --phone, fără eticheta „Domiciliu”
    "PE Str. Republicii nr. 72. Timişoara, jud. Timiş",
    "+ Str. Victoriei nr. 28, Iași, jud. Iași",
    "m Mihai Viteazu nr. 14, Timişoara, jud. Timiș",          # OCR-ul a mâncat „Str.”
    "Bd. Unirii nr. 5A, bl. 3, București",
    "Mun. Ploiești, Jud. PH",                                 # locul nașterii
])
def test_addresses_hidden_by_shape_without_label(line):
    text = f"Valabilitate\n{line}\n20.05.19-12.03.2029"
    spans = [s for s in detect.find_all(text) if s.kind == "ADRESA"]
    hidden = "".join(text[s.start:s.end] for s in spans)
    street = line.split(" nr.")[0].split()[-1]
    assert spans and street in hidden


@pytest.mark.parametrize("line", [
    "CUI [CUI_1] · Ploiești, jud. Prahova",                   # firma de pe fluturaș: nu e adresă personală
    "Salariu brut 14.200,00", "NET DE PLATĂ 8.500,00", "Perioada: 01.09.2026 – 30.09.2026",
    "20.09 Factură utilități -286,70 2.851,50", "Funcția Contabil",
])
def test_ordinary_lines_are_not_addresses(line):
    assert [s for s in detect.find_addresses(line)] == []


def test_iban_with_s_for_5_is_hidden():
    s = next(s for s in detect.find_identifiers("IBAN: ROOSRZBR9999000000000003") if s.kind == "IBAN")
    assert s.valid and s.value == "RO05RZBR9999000000000003"  # benchmark --phone: „RO05” citit „ROOS”


ID_HEADER = "CARTE DE IDENTITATE / IDENTITY CARD\n"


@pytest.mark.parametrize("line", [
    "———————K | Victoriei pr. 96, Ploieşti, jud. Prahova",   # benchmark --phone: „nr.” citit „pr.”
    "Str. Florilor m 1 08, Brașov, jud. Brașov",
    "i ser. Zorilor nr Sa Cluj-Napoca, jud. Cluj",
])
def test_id_card_county_lines_are_addresses_whatever_ocr_read(line):
    text = ID_HEADER + line
    spans = [s for s in detect.find_all(text) if s.kind == "ADRESA"]
    street = next(w for w in ("Victoriei", "Florilor", "Zorilor") if w in line)
    assert any(street in text[s.start:s.end] for s in spans)


@pytest.mark.parametrize("line", [
    "__ 15750912<4ROU9705102M2911208000037 E =",           # benchmark --phone: zgomot la capete
    "1S166673<5ROU971 1220F3201146000097 —",              # zgomot și în interior
])
def test_noisy_mrz_line2_is_hidden_without_accusing(line):
    text = ID_HEADER + "IDROUPOPESCU<<ELENA<<<<<<<<<<<<<<<<<<<\n" + line
    spans = [s for s in detect.find_all(text) if s.kind == "MRZ"]
    hidden = "".join(text[s.start:s.end] for s in spans)
    assert "ROU" in hidden and ("15750912" in hidden or "166673" in hidden)
    assert all(s.valid is not False for s in spans)  # nevalidabil ≠ fals: fără MRZ_INVALID pe zgomot


def test_payslip_county_line_is_not_hidden():
    text = "FLUTURAȘ DE SALARIU\nCUI RO9402119372 · Ploiești, jud. Prahova"  # nu e buletin → firma rămâne
    assert not [s for s in detect.find_all(text) if s.kind == "ADRESA"]


def test_id_number_with_ocr_space_is_hidden():
    text = "CARTE DE IDENTITATE / IDENTITY CARD SERIA IS NR 86524 7"  # benchmark --phone
    spans = {s.kind: text[s.start:s.end] for s in detect.find_identifiers(text)}
    assert spans.get("SERIE") == "IS" and spans.get("NR") == "86524 7"
