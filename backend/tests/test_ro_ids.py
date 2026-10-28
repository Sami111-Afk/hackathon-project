import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data" / "generator"))

from ro_ids import cnp, cnp_valid, cui_valid, iban, iban_valid, mrz_td2  # noqa: E402

from app.arena.missions import COMPANIES  # noqa: E402


def test_generated_ids_are_valid():
    for seq in range(1, 50):
        assert cnp_valid(cnp("F", "1959-03-12", "PH", seq))
    assert iban_valid(iban("RZBR"))
    assert not cnp_valid("2590312290170")


def test_arena_companies_have_valid_cui():
    for c in COMPANIES.values():
        assert cui_valid(c["cui"]), c["cui"]


def test_mrz_lines_are_36_chars():
    l1, l2 = mrz_td2("IONESCU", "MARIA", "PH", "481925", "1959-03-12", "F", "2029-03-12", "2590312290171")
    assert len(l1) == len(l2) == 36 and l1.startswith("IDROUIONESCU<<MARIA")
