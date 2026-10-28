import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "data" / "generator"))

from ro_ids import SAFE_CUIS, cnp, cnp_valid, cui, cui_valid, iban, iban_valid, mrz_td2, mrz_td2_valid  # noqa: E402

from app.arena.missions import COMPANIES  # noqa: E402


def test_generated_ids_are_valid():
    for seq in range(1, 50):
        assert cnp_valid(cnp("F", "1959-03-12", "PH", seq))
    assert iban_valid(iban("RZBR"))
    assert not cnp_valid("2590312290170")


def test_arena_companies_have_valid_cui():
    for c in COMPANIES.values():
        assert cui_valid(c["cui"]), c["cui"]
        assert c["cui"].removeprefix("RO") in SAFE_CUIS


def test_generated_cui_uses_only_unallocated_values():
    assert all(cui_valid(value) for value in SAFE_CUIS)
    assert all(cui() in SAFE_CUIS for _ in range(20))


def test_mrz_lines_are_36_chars():
    lines = mrz_td2("IONESCU", "MARIA", "PH", "481925", "1959-03-12", "F", "2029-03-12", "2590312290171")
    assert len(lines[0]) == len(lines[1]) == 36
    assert lines[0].startswith("IDROUIONESCU<<MARIA")
    assert mrz_td2_valid(lines)

    tampered = (lines[0], lines[1][:19] + ("0" if lines[1][19] != "0" else "1") + lines[1][20:])
    assert not mrz_td2_valid(tampered)
