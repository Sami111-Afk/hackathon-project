from datetime import date

import pytest

from app.agents.paznic.validators import (
    iban_bank_code,
    mrz_check_digit,
    mrz_matches_cnp,
    parse_cnp,
    parse_mrz_td2_line2,
    valid_cnp,
    valid_cui,
    valid_iban,
)

MARIA_CNP = "2590314290011"  # F, 14.03.1959, Prahova (29)
ICAO_TD2_LINE2 = "D231458907UTO7408122F1204159<<<<<<<6"  # specimenul din ICAO 9303


def test_cnp_valid_and_decoded():
    info = parse_cnp(MARIA_CNP)
    assert info is not None
    assert info.birth_date == date(1959, 3, 14)
    assert info.sex == "F"
    assert info.county == "29"


@pytest.mark.parametrize("cnp", [
    "2590314290012",   # cifră de control greșită
    "2590314990012",   # județ inexistent (99)
    "2591314290011",   # luna 13
    "0590314290011",   # S = 0
    "259031429001",    # 12 cifre
    "25903142900AB",
])
def test_cnp_invalid(cnp):
    assert not valid_cnp(cnp)


def test_cnp_control_10_becomes_1():
    # căutăm un corp de CNP cu restul 10 și verificăm că cifra 1 e acceptată
    from app.agents.paznic.validators import CNP_WEIGHTS
    for nnn in range(1000):
        body = f"180010140{nnn:03d}"
        if sum(int(c) * int(w) for c, w in zip(body, CNP_WEIGHTS, strict=True)) % 11 == 10:
            assert valid_cnp(body + "1")
            assert not valid_cnp(body + "0")
            return
    pytest.fail("niciun corp cu restul 10")


def test_iban():
    assert valid_iban("RO49AAAA1B31007593840000")
    assert valid_iban("ro49 aaaa 1b31 0075 9384 0000")
    assert not valid_iban("RO48AAAA1B31007593840000")
    assert not valid_iban("RO49AAAA1B3100759384000")  # 23 de caractere
    assert iban_bank_code("RO49RZBR1B31007593840000") == "RZBR"


def test_cui():
    assert valid_cui("361820")      # Raiffeisen Bank
    assert valid_cui("RO361820")
    assert not valid_cui("361821")
    assert not valid_cui("1")
    assert not valid_cui("12345678901")


def test_mrz_icao_specimen():
    assert mrz_check_digit("D23145890") == 7
    mrz = parse_mrz_td2_line2(ICAO_TD2_LINE2)
    assert mrz is not None and mrz.valid
    assert (mrz.document_number, mrz.birth_date, mrz.sex) == ("D23145890", "740812", "F")


def test_mrz_tampered_birth_date_fails():
    tampered = ICAO_TD2_LINE2[:13] + "750812" + ICAO_TD2_LINE2[19:]
    mrz = parse_mrz_td2_line2(tampered)
    assert not mrz.checks_ok["birth_date"] and not mrz.valid


def test_mrz_vs_cnp():
    mrz = parse_mrz_td2_line2(ICAO_TD2_LINE2)
    assert not mrz_matches_cnp(mrz, MARIA_CNP)
    line = "AB1234567" + "<" + "ROU" + "590314"
    line += str(mrz_check_digit("590314")) + "F" + "300101" + str(mrz_check_digit("300101")) + "<" * 7
    line = line[:9] + str(mrz_check_digit(line[:9])) + line[10:]
    line += str(mrz_check_digit(line[0:10] + line[13:20] + line[21:35]))
    maria = parse_mrz_td2_line2(line)
    assert maria.valid and mrz_matches_cnp(maria, MARIA_CNP)
