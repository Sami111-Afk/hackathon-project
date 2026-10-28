import asyncio
from datetime import date

import pytest

from app.agents.compliance.scoring import score
from app.agents.functionar import agent as functionar_agent
from app.agents.functionar.agent import Functionar
from app.agents.verificator import agent as verificator_agent
from app.agents.verificator import anaf, ro_checks
from app.agents.verificator.agent import Verificator
from app.agents.verificator.statement import check_balances, check_income
from app.core.llm import LLMUnavailable
from tests.test_functionar_agent import PAYSLIP, STATEMENT, Ctx, maria_case, paznic_scratch

TODAY = date(2026, 10, 28)
MARIA_VAULT = {"[CNP_1]": ["2590312290006"], "[IBAN_1]": ["RO59RZBR9999000000000001"], "[CUI_1]": ["RO9402119372"],
               "[SERIE_1]": ["PH"], "[ADRESA_1]": ["Str. Florilor nr. 12, Ploiești, jud. Prahova"]}


@pytest.fixture
def no_llm(monkeypatch):
    async def unavailable(*a, **k):
        raise LLMUnavailable("mock")

    monkeypatch.setattr(functionar_agent, "chat", unavailable)


def run_both(case, scratch, monkeypatch, vault):
    monkeypatch.setattr(verificator_agent.local_values, "load", lambda case_id: vault)
    ctx = Ctx(scratch)

    async def go():
        await Functionar().run(case, ctx)
        return await Verificator(today=TODAY).run(case, ctx)

    return asyncio.run(go())


def by_code(result):
    return {f.code: f for f in result.findings}


def test_maria_is_caught_on_every_axis(no_llm, monkeypatch):
    result = run_both(maria_case(), paznic_scratch(), monkeypatch, MARIA_VAULT)
    f = by_code(result)

    assert f["NET_MISMATCH"].message == "Netul calculat (8.307 lei) diferă de cel declarat (8.500 lei)"
    assert f["NET_MISMATCH"].evidence.bbox[1] == 900 and f["NET_MISMATCH"].evidence.field == "net_salary"
    assert f["COMPANY_INACTIVE"].message == "Angajatorul [CUI_1] figurează inactiv la ANAF"
    assert f["BALANCE_MISMATCH"].message == "Soldul final (26.480 lei) nu iese din tranzacții (2.851,50 lei)"
    assert f["AGE_EMPLOYMENT_MISMATCH"].message == "Solicitant de 67 de ani declarat angajat activ"
    assert {"SALARY_NOT_IN_STATEMENT", "PENSION_INCOME"} <= set(f)
    assert not {"ID_EXPIRED", "CNP_SEX_MISMATCH", "SERIES_COUNTY_MISMATCH", "IBAN_BANK_MISMATCH"} & set(f)

    verdict, _ = score([result])
    assert verdict.recommendation == "escalate" and verdict.label == "forged"


def test_no_identifier_value_leaks_into_findings(no_llm, monkeypatch):
    result = run_both(maria_case(), paznic_scratch(), monkeypatch, MARIA_VAULT)
    text = " ".join(f.message for f in result.findings)
    for values in MARIA_VAULT.values():
        assert values[0] not in text


def honest_scratch():
    """Același dosar, dar cinstit: net corect, firmă activă, salariul intră în cont, solduri corecte."""
    def swap(words, mapping):
        return [dict(w, text=mapping.get(w["text"], w["text"])) for w in words]

    slip = swap(PAYSLIP, {"8.500,00": "8.307,00"})
    stmt = swap(STATEMENT, {"pensie": "salariu", "2.310,00": "8.307,00", "3.550,50": "9.547,50",
                            "3.138,20": "9.135,20", "2.851,50": "8.848,50", "26.480,00": "8.848,50"})
    scratch = paznic_scratch()
    scratch["paznic"]["doc_2"]["words"] = slip
    scratch["paznic"]["doc_3"]["words"] = stmt
    return scratch


def test_honest_case_is_cleared(no_llm, monkeypatch):
    # Bitwave, activă; 36 ani
    vault = dict(MARIA_VAULT, **{"[CUI_1]": ["RO9341910290"], "[CNP_1]": ["2900312290008"]})
    result = run_both(maria_case(), honest_scratch(), monkeypatch, vault)
    assert [f.code for f in result.findings if f.severity != "info"] == []
    verdict, _ = score([result])
    assert verdict.recommendation == "clear"


def test_without_vault_skips_vault_checks_but_still_checks_numbers(no_llm, monkeypatch):
    result = run_both(maria_case(), paznic_scratch(), monkeypatch, {})
    f = by_code(result)
    assert {"NET_MISMATCH", "BALANCE_MISMATCH"} <= set(f)
    assert "AGE_EMPLOYMENT_MISMATCH" not in f
    assert f["COMPANY_UNVERIFIED"].severity == "info"  # CUI-ul și numele firmei sunt doar etichete


def test_company_found_by_name_when_paznic_left_it_in_clear(no_llm, monkeypatch):
    scratch = paznic_scratch()  # pe fluturașul real, Paznicul lasă numele firmei în clar
    scratch["paznic"]["doc_2"]["words"] = [dict(w, text="Agro Prahova Distribuţie SRL") if w["text"] == "[FIRMA_1]"
                                           else w for w in PAYSLIP]
    assert "COMPANY_INACTIVE" in by_code(run_both(maria_case(), scratch, monkeypatch, {}))


def test_without_functionar_output_falls_back_to_fixture():
    result = asyncio.run(Verificator(today=TODAY).run(maria_case(), Ctx({})))
    assert result.agent == "verificator" and "NET_MISMATCH" in by_code(result)


def test_statement_row_chain_break_points_to_the_row():
    rows = [{"date": "01.09", "description": "Sold", "amount": None, "balance": 100.0, "page": 1, "bbox": [0] * 4},
            {"date": "02.09", "description": "x", "amount": 50.0, "balance": 150.0, "page": 1, "bbox": [0, 1, 2, 3]},
            {"date": "03.09", "description": "y", "amount": -20.0, "balance": 200.0, "page": 1, "bbox": [0, 9, 2, 9]}]
    f = check_balances({"rows": rows, "closing_balance": 200.0}, "d")
    assert len(f) == 1 and f[0].evidence.bbox == [0, 9, 2, 9] and "03.09" in f[0].message
    assert check_income({"rows": rows}, "d", None) == []


@pytest.mark.parametrize(
    ("cnp", "birth", "sex"),
    [("2590312290006", date(1959, 3, 12), "F"), ("1900101400000", date(1990, 1, 1), "M"),
     ("5010203400000", date(2001, 2, 3), "M"), ("6991302400000", None, "F"), ("123", None, None)],
)
def test_cnp_parsing(cnp, birth, sex):
    assert ro_checks.cnp_birth_date(cnp) == birth and ro_checks.cnp_sex(cnp) == sex


def test_romanian_checks():
    assert ro_checks.check_card_sex("2590312290006", "M", "d").code == "CNP_SEX_MISMATCH"
    assert ro_checks.check_card_sex("2590312290006", "F", "d") is None
    assert ro_checks.check_id_validity("2026-01-01", TODAY, "d").code == "ID_EXPIRED"
    assert ro_checks.check_series_county("CJ", "Str. X 1, Ploiești, jud. Prahova", "d").code == "SERIES_COUNTY_MISMATCH"
    assert ro_checks.check_series_county("PH", "Str. X 1, Ploiești, Județul Prahova", "d") is None
    assert ro_checks.check_series_county("ZZ", "jud. Prahova", "d") is None  # prefix necunoscut → nu ghicim
    assert ro_checks.check_iban_bank("RO49BTRL0000000000001234", "Raiffeisen BANK", "d").code == "IBAN_BANK_MISMATCH"
    assert ro_checks.check_iban_bank("RO59RZBR9999000000000001", "Raiffeisen BANK", "d") is None
    codes = [f.code for f in ro_checks.check_dates("2027-01-01", date(2027, 6, 1), TODAY, "d")]
    assert codes == ["DOC_FUTURE_DATE", "DOC_BEFORE_COMPANY"]


def test_anaf_lookup_and_unknown_company_is_not_a_hard_override():
    assert anaf.lookup(cui="9402119372").name == "Agro Prahova Distribuție SRL"
    assert anaf.lookup(name="AGRO PRAHOVA DISTRIBUTIE S.R.L").active is False
    f = anaf.check_company(None, "unavailable", "d", "[CUI_1]")
    assert f[0].code == "COMPANY_UNVERIFIED" and f[0].severity == "info"


def test_learned_rule_uses_real_anaf_company(no_llm, monkeypatch):
    # firmă care NU e în registrul demo, găsită la ANAF real; regula aprobată: document emis înainte de înființare
    from app.learning import engine

    rule = {"id": "rule_t", "status": "approved",
            "when": {"left": "doc.issue_date", "op": "lt", "right": "company.founded"},
            "then": {"code": "DOC_BEFORE_COMPANY_RULE", "severity": "high", "message": "Emis înainte de firmă"}}
    real = anaf.Company("FIRMA REALA SRL", "123456", True, date(2026, 10, 1), source="anaf")
    monkeypatch.setattr(verificator_agent.anaf, "resolve", lambda *a, **k: (real, "anaf"))
    monkeypatch.setattr(verificator_agent.anaf, "check_company", lambda *a, **k: [])
    engine.add_rule(rule)
    try:
        result = run_both(maria_case(), paznic_scratch(), monkeypatch, {})
    finally:
        engine.clear()
    f = next(f for f in result.findings if f.code == "DOC_BEFORE_COMPANY_RULE")
    assert f.rule_id == "rule_t"  # fluturașul e emis 30.09.2026, firma înființată 01.10.2026


def test_demo_registry_still_feeds_rules():
    from app.learning import engine

    rule = {"id": "r", "status": "approved", "when": {"left": "company.active", "op": "eq", "right": False},
            "then": {"code": "X", "severity": "low", "message": "inactivă"}}
    assert engine.apply_rules({"employer": "Agro Prahova Distribuție SRL"}, [rule])
    assert not engine.apply_rules({"employer": "Agro Prahova Distribuție SRL"}, [rule], company={"active": True})
