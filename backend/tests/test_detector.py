import asyncio
import io

import pytest
from cryptography.fernet import Fernet
from PIL import Image, ImageDraw

from app.agents.detector import ela, structure
from app.agents.detector.agent import Detector
from app.config import REPO_ROOT, settings
from app.core import files
from app.core.pipeline import PipelineContext
from app.models import Case, Document

MARIA = REPO_ROOT / "data" / "demo" / "maria"


@pytest.fixture
def secrets(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "vault_key", Fernet.generate_key().decode())
    monkeypatch.setattr(files, "UPLOAD_DIR", tmp_path)


def _jpeg(img: Image.Image, q: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=q)
    return buf.getvalue()


def _page() -> Image.Image:
    img = Image.new("RGB", (1240, 1754), "white")
    d = ImageDraw.Draw(img)
    for i in range(30):
        d.text((80, 80 + 50 * i), f"Linia {i}: Salariu brut 14.200,00 CAS 3.550,00 Sold 2.851,50", fill="black")
        d.text((1160, 80 + 50 * i), f"{1000 + 37 * i},00", fill="black", anchor="ra")
    return img


def _run(case: Case, data: dict[str, bytes]):
    return asyncio.run(Detector().run(case, PipelineContext(case=case, files=data)))


def test_clean_documents_have_no_ela_anomaly():
    page = _page()
    once = Image.open(io.BytesIO(_jpeg(page, 90)))
    twice = Image.open(io.BytesIO(_jpeg(Image.open(io.BytesIO(_jpeg(page, 75))), 92)))
    assert ela.analyze(once).regions == []      # o singură salvare: nimic de comparat
    assert ela.analyze(twice).first_quality == 75
    assert ela.analyze(twice).regions == []     # dublă compresie, dar uniformă


def test_maria_payslip_edit_is_found(secrets):
    case = Case(id="case_t", created_at="2026-10-28T12:00:00",
                documents=[Document(id="doc_2", filename="fluturas.jpg")])
    r = _run(case, {"doc_2": (MARIA / "fluturas.jpg").read_bytes()})
    net = [820, 895, 1165, 950]  # truth.json → net_bbox
    boxes = [f.evidence.bbox for f in r.findings if f.code == "ELA_ANOMALY"]
    assert any(ela_overlap(b, net) for b in boxes)
    assert files.load_derived("case_t", "doc_2", "ela", 1)
    assert r.artifacts["ela_image"].endswith("doc_2/image?view=ela")


def test_maria_statement_editor_producer(secrets):
    case = Case(id="case_t", created_at="2026-10-28T12:00:00",
                documents=[Document(id="doc_3", filename="extras.pdf")])
    r = _run(case, {"doc_3": (MARIA / "extras.pdf").read_bytes()})
    codes = {f.code for f in r.findings}
    assert "PDF_EDITOR_PRODUCER" in codes and "PDF_INCREMENTAL_UPDATE" not in codes
    assert "GIMP" in next(f.message for f in r.findings if f.code == "PDF_EDITOR_PRODUCER")


def test_incremental_update_counts_linearized():
    assert structure.incremental_updates(structure.PdfInfo(eof_count=2, linearized=True)) == 0
    assert structure.incremental_updates(structure.PdfInfo(eof_count=3, linearized=True)) == 1
    assert structure.incremental_updates(structure.PdfInfo(eof_count=2)) == 1


def ela_overlap(a, b) -> bool:
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])
