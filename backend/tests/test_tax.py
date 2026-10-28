import pytest

from app.agents.verificator.tax import (
    MIN_WAGE_RON,
    NET_TOLERANCE_RON,
    check_net,
    compute_payslip,
    expected_net,
    format_ron,
    min_wage_for,
    personal_deduction,
    untaxed_amount,
)
from app.models import Evidence


def test_maria_net_mismatch_matches_fixture():
    f = check_net(14200, 8500, evidence=Evidence(doc_id="doc_2", field="net_salary"))
    assert f is not None and f.code == "NET_MISMATCH" and f.severity == "high"
    assert f.message == "Netul calculat (8.307 lei) diferă de cel declarat (8.500 lei)"
    assert f.evidence.field == "net_salary"


def test_correct_payslip_has_no_finding():
    t = compute_payslip(14200)
    assert (t.cas, t.cass, t.deduction, t.income_tax, t.net) == (3550, 1420, 0, 923, 8307)
    assert check_net(14200, 8307) is None


def test_tolerance_is_two_lei():
    assert check_net(14200, 8307 + NET_TOLERANCE_RON) is None
    assert check_net(14200, 8307 - NET_TOLERANCE_RON) is None
    assert check_net(14200, 8307 + NET_TOLERANCE_RON + 1) is not None


def test_components_round_half_up():
    t = compute_payslip(4326)  # cu suma netaxabilă de 200: CAS = 0,25·4126 = 1031,5 → 1032
    assert (t.untaxed, t.cas, t.cass, t.deduction) == (200, 1032, 413, 843)


def test_minimum_wage_net_matches_published_value():
    # iulie 2026: brut 4.325, suma netaxabilă 200 → net 2.699 (valoarea publicată în presă)
    assert compute_payslip(4325, period="2026-09").net == 2699
    assert check_net(4325, 2699, period="2026-09") is None


def test_minimum_wage_depends_on_month():
    assert min_wage_for("2026-03") == 4050 and min_wage_for("2026-09") == 4325
    assert untaxed_amount(4050, "2026-03") == 300 and untaxed_amount(4400, "2026-03") == 0
    assert untaxed_amount(4600, "2026-09") == 200 and untaxed_amount(4601, "2026-09") == 0


@pytest.mark.parametrize(
    ("gross", "dependents", "deduction"),
    [
        (MIN_WAGE_RON, 0, 865),          # 20% din salariul minim
        (MIN_WAGE_RON, 2, 1298),         # 30%
        (MIN_WAGE_RON, 9, 1946),         # plafonat la 4+ persoane: 45%
        (MIN_WAGE_RON + 1, 0, 843),      # primul pas de 50 lei: 19,5%
        (MIN_WAGE_RON + 50, 0, 843),
        (MIN_WAGE_RON + 51, 0, 822),
        (MIN_WAGE_RON + 2000, 0, 0),     # capătul intervalului
        (MIN_WAGE_RON + 2001, 4, 0),     # peste interval nu mai există deducere
        (0, 0, 0),
    ],
)
def test_personal_deduction(gross, dependents, deduction):
    assert personal_deduction(gross, dependents) == deduction


def test_linear_formula_agrees_with_rounded_payslip():
    # varianta HE calculează forma liniară; trebuie să cadă în toleranță față de fluturaș
    for gross in range(MIN_WAGE_RON, 30000, 37):
        for dependents in range(5):
            t = compute_payslip(gross, dependents)
            assert abs(t.net - expected_net(gross, t.deduction, t.untaxed)) <= NET_TOLERANCE_RON, (gross, dependents)


@pytest.mark.parametrize(
    ("amount", "text"),
    [(8307, "8.307"), (8307.5, "8.307,50"), (14200, "14.200"), (950, "950"), (-12.3, "-12,30")],
)
def test_format_ron(amount, text):
    assert format_ron(amount) == text


def test_honest_payslips_with_dependents_are_not_flagged():
    # bug găsit de benchmark: 108/112 fluturași cinstiți cu persoane în întreținere erau marcați falși
    for gross in range(4325, 6400, 75):
        for dep in range(5):
            net = compute_payslip(gross, dep, period="2026-09").net
            assert check_net(gross, net, period="2026-09") is None, (gross, dep)
    assert check_net(14200, 8500, period="2026-09") is not None  # Maria rămâne prinsă
