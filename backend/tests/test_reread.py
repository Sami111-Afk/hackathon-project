"""Recitirea sumelor înainte de acuzație. Se sar dacă Tesseract `ron` lipsește (CI)."""
import asyncio
import io
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.agents.paznic.ocr import ocr_available

# OCR real pe imagini (~15 s): rulează doar cu `pytest -m slow` (vezi pytest.ini)
pytestmark = [pytest.mark.slow, pytest.mark.skipif(not ocr_available(), reason="Tesseract `ron` lipsește")]

from app.agents.functionar import agent as functionar_agent  # noqa: E402
from app.agents.functionar.agent import Functionar  # noqa: E402
from app.agents.functionar.layout import group_lines  # noqa: E402
from app.agents.functionar.statement import parse_statement  # noqa: E402
from app.agents.verificator import agent as verificator_agent  # noqa: E402
from app.agents.verificator.agent import Verificator  # noqa: E402
from app.agents.verificator.reread import Rereader, read_amount  # noqa: E402
from app.agents.verificator.statement import check_balances  # noqa: E402
from app.core.llm import LLMUnavailable  # noqa: E402
from app.models import Case, Document  # noqa: E402

FONTS = Path(__file__).resolve().parents[1] / "app" / "arena" / "fonts"
TODAY_ISO = "2026-10-28T10:00:00Z"


def render(lines: list[tuple[int, int, str, bool]], size=(1240, 1100), misread: dict[str, str] | None = None):
    """Desenează rândurile și întoarce (JPEG, cuvinte cu bbox) — cuvintele ca de la Paznic; `misread` simulează
    OCR-ul care a citit greșit un cuvânt (imaginea rămâne cea corectă)."""
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    words = []
    for x, y, text, right in lines:
        font = ImageFont.truetype(str(FONTS / "NotoSans-Bold.ttf"), 26)
        if right:  # aliniat la dreapta, ca sumele de pe documente
            x -= d.textlength(text, font=font)
        for token in text.split(" "):
            if token:
                box = d.textbbox((x, y), token, font=font)
                d.text((x, y), token, font=font, fill="black")
                words.append({"text": (misread or {}).get(token, token), "page": 1, "bbox": list(box)})
            x += d.textlength(token + " ", font=font)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue(), words


STATEMENT = [(80, 100, "EXTRAS DE CONT", False), (80, 160, "Raiffeisen BANK", False),
             (80, 260, "01.09 Sold inițial", False), (1160, 260, "1.240,50", True),
             (80, 310, "05.09 Încasare salariu", False), (850, 310, "8.307,00", True), (1160, 310, "9.547,50", True),
             (80, 360, "12.09 Cumpărături card", False), (850, 360, "-1.595,00", True), (1160, 360, "7.952,50", True),
             (80, 430, "Sold final", False), (1160, 430, "7.952,50", True)]


def test_read_amount_from_crop():
    data, words = render(STATEMENT)
    img = Image.open(io.BytesIO(data))
    w = next(w for w in words if w["text"] == "-1.595,00")
    assert read_amount(img, w["bbox"]) == 1595.0  # mărimea; semnul îl dă citirea inițială


def table_and_reader(misread_at: int | None = None, wrong: str = "", lines=STATEMENT):
    """`misread_at` = y-ul rândului pe care OCR-ul a citit greșit ultima sumă (imaginea rămâne corectă)."""
    data, words = render(lines)
    if misread_at is not None:
        last = max((w for w in words if abs(w["bbox"][1] - misread_at) < 15), key=lambda w: w["bbox"][0])
        last["text"] = wrong
    table = parse_statement(group_lines(words)).to_dict()
    rr = Rereader({"d": data})
    return table, (lambda page, bbox: rr.amount("d", page, bbox))


def test_ocr_digit_error_on_closing_balance_is_not_an_accusation():
    table, reread = table_and_reader(misread_at=430, wrong="1.952,50")  # exact cazul din benchmark
    assert table["closing_balance"] == 1952.5
    assert [f.code for f in check_balances(table, "d")] == ["BALANCE_MISMATCH"]
    assert [f.code for f in check_balances(table, "d", reread)] == ["AMOUNT_UNCERTAIN"]


def test_ocr_digit_error_inside_a_row_is_not_an_accusation():
    table, reread = table_and_reader(misread_at=310, wrong="9.541,50")
    assert [f.code for f in check_balances(table, "d")] == ["BALANCE_MISMATCH", "BALANCE_MISMATCH"]
    assert [f.code for f in check_balances(table, "d", reread)] == ["AMOUNT_UNCERTAIN", "AMOUNT_UNCERTAIN"]


def test_real_forgery_is_confirmed_by_rereading():
    forged = [line if line[2] != "7.952,50" or line[1] != 430 else (1160, 430, "26.480,00", True) for line in STATEMENT]
    table, reread = table_and_reader(lines=forged)
    f = check_balances(table, "d", reread)
    assert [x.code for x in f] == ["BALANCE_MISMATCH"] and "26.480" in f[0].message


PAYSLIP = [(80, 80, "Tehnoserv Construct SRL", False), (80, 230, "FLUTURAȘ DE SALARIU", False),
           (80, 290, "Luna: septembrie 2026 · Emis: 30.09.2026", False),
           (80, 380, "Salariu brut", False), (1160, 380, "14.200,00", True),
           (80, 450, "CAS 25%", False), (1160, 450, "-3.550,00", True),
           (80, 520, "NET DE PLATĂ", False), (1160, 520, "{net}", True)]


class Ctx:
    def __init__(self, scratch, files):
        self.scratch, self.files = scratch, files

    async def emit(self, *a, **k):
        pass


def run_payslip(monkeypatch, printed: str, ocr_read: str):
    async def unavailable(*a, **k):
        raise LLMUnavailable("mock")

    monkeypatch.setattr(functionar_agent, "chat", unavailable)
    monkeypatch.setattr(verificator_agent.local_values, "load", lambda case_id: {})
    lines = [(x, y, t.format(net=printed), r) for x, y, t, r in PAYSLIP]
    data, words = render(lines, misread={printed: ocr_read})
    case = Case(id="c", created_at=TODAY_ISO, documents=[Document(id="doc_1", filename="fluturas.jpg")])
    ctx = Ctx({"paznic": {"doc_1": {"words": words}}}, {"doc_1": data})

    async def go():
        await Functionar().run(case, ctx)
        return await Verificator().run(case, ctx)

    return asyncio.run(go())


def test_payslip_ocr_error_becomes_uncertain_not_mismatch(monkeypatch):
    result = run_payslip(monkeypatch, printed="8.307,00", ocr_read="8.387,00")  # netul corect, citit greșit
    codes = [f.code for f in result.findings]
    assert "NET_MISMATCH" not in codes and "AMOUNT_UNCERTAIN" in codes


def test_payslip_forgery_is_still_caught(monkeypatch):
    result = run_payslip(monkeypatch, printed="8.500,00", ocr_read="8.500,00")  # falsul Mariei, tipărit
    assert "NET_MISMATCH" in [f.code for f in result.findings]

