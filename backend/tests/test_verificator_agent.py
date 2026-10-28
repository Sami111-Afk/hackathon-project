from datetime import date


def test_malformed_fields_do_not_crash():
    """Review PR #7: datele/sumele în format neașteptat nu trebuie să doboare agentul."""
    from app.agents.verificator.ro_checks import check_dates, check_id_validity, parse_iso
    from app.agents.verificator.statement import check_balances

    assert parse_iso("28.10.2026") is None and parse_iso(None) is None
    assert check_id_validity("12.2030", date(2026, 10, 28), "doc_1") is None
    assert check_dates("30/09/2026", None, date(2026, 10, 28), "doc_2") == []
    rows = [{"date": "01.09", "amount": None, "balance": 100.0, "page": 1, "bbox": None},
            {"date": "02.09", "amount": 5.0, "balance": None, "page": 1, "bbox": None}]
    assert check_balances({"rows": rows, "closing_balance": 50.0}, "doc_3") == []
