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
