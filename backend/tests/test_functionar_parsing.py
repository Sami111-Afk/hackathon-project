import pytest

from app.agents.functionar.classify import classify_by_keywords
from app.agents.functionar.parsing import parse_amount, parse_date, parse_month
from app.agents.functionar.schemas import FIELD_KINDS, SCHEMAS, PayslipFields


@pytest.mark.parametrize(
    ("text", "value"),
    [
        ("14.200,00", 14200.0),
        ("8.500,00", 8500.0),
        ("-412,30", -412.3),
        ("−3.550,00 lei", -3550.0),
        ("1.240,50", 1240.5),
        ("RON 2.310,00", 2310.0),
        ("14 200,00", 14200.0),
        ("8.500", 8500.0),
        ("1.234.567,89", 1234567.89),
        ("2310.00", 2310.0),
        ("950", 950.0),
        ("0,5", 0.5),
        ("", None),
        (None, None),
        ("[SUMA_1]", None),
    ],
)
def test_parse_amount(text, value):
    assert parse_amount(text) == value


@pytest.mark.parametrize(
    ("text", "iso"),
    [
        ("30.09.2026", "2026-09-30"),
        ("Emis: 30.09.2026", "2026-09-30"),
        ("1/9/2026", "2026-09-01"),
        ("2026-09-30", "2026-09-30"),
        ("12 martie 1959", "1959-03-12"),
        ("20.05.19", "2019-05-20"),
        ("12.03.59", "1959-03-12"),
        ("31.02.2026", None),
        ("fără dată", None),
    ],
)
def test_parse_date(text, iso):
    assert parse_date(text) == iso


@pytest.mark.parametrize(
    ("text", "month"),
    [
        ("septembrie 2026", "2026-09"),
        ("Luna: septembrie 2026   ·   Emis: 30.09.2026", "2026-09"),
        ("Sept. 2026", "2026-09"),
        ("09/2026", "2026-09"),
        ("13/2026", None),
    ],
)
def test_parse_month(text, month):
    assert parse_month(text) == month


@pytest.mark.parametrize(
    ("text", "doc_type"),
    [
        ("ROMÂNIA · CARTE DE IDENTITATE / IDENTITY CARD", "id_card"),
        ("[CUI_1]\nFLUTURAȘ DE SALARIU\nLuna: septembrie 2026", "payslip"),
        ("Raiffeisen BANK\nEXTRAS DE CONT\nSold final", "bank_statement"),
        ("ADEVERINȚĂ\nPrin prezenta se adeverește că", "employment_certificate"),
        ("Factură fiscală nr. 12", None),
        (None, None),
    ],
)
def test_classify_by_keywords(text, doc_type):
    assert classify_by_keywords(text) == doc_type


def test_every_typed_field_exists_in_a_schema():
    fields = {name for schema in SCHEMAS.values() for name in schema.model_fields}
    assert set(FIELD_KINDS) <= fields


def test_schema_tolerates_partial_llm_output():
    out = PayslipFields.model_validate({"net_salary": {"value": "8.500,00", "source_text": "8.500,00"}, "x": 1})
    assert out.net_salary.value == "8.500,00" and out.gross_salary.value is None
