"""Parsarea citirilor OCR din recitire (fără Tesseract — rulează și în CI)."""
import pytest


@pytest.mark.parametrize(("text", "value"), [
    ("9.547,50", 9547.5), ("9,547.50", 9547.5), ("-1.240,50-", 1240.5), ("7952,52", 7952.52),
    ("1.234.567,89", 1234567.89), ("95252,", None), ("7.95252", None), ("", None), ("8.307", None),
])
def test_parse_ocr_amount(text, value):
    from app.agents.verificator.reread import parse_ocr_amount

    assert parse_ocr_amount(text) == value
