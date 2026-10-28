import asyncio
import io

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import AUTH

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def wait_for_review(client: TestClient, case_id: str) -> dict:
    for _ in range(100):
        case = client.get(f"/api/cases/{case_id}", headers=AUTH).json()
        if case["status"] != "processing" and case.get("verdict"):
            return case
        asyncio.run(asyncio.sleep(0.02))
    raise AssertionError("pipeline-ul nu a terminat")


def test_health():
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "ok"


def test_requires_token():
    with TestClient(app) as c:
        assert c.get("/api/cases").status_code == 401
        assert c.get("/api/cases", headers={"Authorization": "Bearer gresit"}).status_code == 401


def test_rejects_non_documents():
    with TestClient(app) as c:
        r = c.post("/api/cases", headers=AUTH, files=[("files", ("x.txt", io.BytesIO(b"salut"), "text/plain"))])
        assert r.status_code == 415


def test_maria_end_to_end():
    """Dosarul Mariei (agenți de probă) ajunge la awaiting_review cu recomandarea escalate."""
    with TestClient(app) as c:
        r = c.post("/api/cases", headers=AUTH, data={"requested_amount_ron": "45000"},
                   files=[("files", (f"d{i}.png", io.BytesIO(PNG), "image/png")) for i in range(3)])
        case_id = r.json()["case_id"]
        case = wait_for_review(c, case_id)

        assert case["status"] == "awaiting_review"
        assert case["verdict"]["recommendation"] == "escalate"
        assert case["verdict"]["label"] == "identity_fraud"
        agents = {r["agent"] for r in case["results"]}
        assert agents == {"paznic", "functionar", "verificator", "detector", "detectiv", "compliance"}

        img = c.get(f"/api/cases/{case_id}/documents/doc_1/image", headers=AUTH)
        assert img.status_code == 200 and img.content == PNG

        d = c.post(f"/api/cases/{case_id}/decision", headers=AUTH, json={"action": "reject", "decided_by": "Andrei"})
        assert d.json()["status"] == "rejected"
        assert d.json()["action"] == "reject" and d.json()["decided_by"] == "Andrei"

        stats = c.get("/api/dashboard/stats", headers=AUTH).json()
        assert stats["frauds_stopped"] >= 1


def test_agent_failure_marks_incomplete(monkeypatch):
    from app.agents import registry

    class Broken:
        name = "detector"

        async def run(self, case, ctx):
            raise RuntimeError("CNP 1590312... ar fi o scurgere")

    monkeypatch.setitem(registry.AGENTS, "detector", Broken())
    with TestClient(app) as c:
        case_id = c.post("/api/admin/rerun-demo", headers=AUTH).json()["case_id"]
        case = wait_for_review(c, case_id)
        det = next(r for r in case["results"] if r["agent"] == "detector")
        assert det["status"] == "error"
        assert "1590312" not in det["error"]  # nu scurgem date în mesajele de eroare
        assert case["verdict"]["incomplete"] is True


def test_seed_demo_fills_dashboard():
    with TestClient(app) as c:
        r = c.post("/api/admin/seed-demo", headers=AUTH).json()
        assert len(r["seeded"]) == 15
        stats = c.get("/api/dashboard/stats", headers=AUTH).json()
        assert stats["cases_processed"] >= 15 and stats["frauds_stopped"] >= 5
        ring = [x for x in c.get("/api/cases", headers=AUTH).json() if x["id"].startswith("case_ring")]
        assert len(ring) == 5


def test_report_lists_evidence_and_ring_without_pii():
    with TestClient(app) as c:
        c.post("/api/admin/seed-demo", headers=AUTH)
        case_id = c.post("/api/admin/rerun-demo", headers=AUTH).json()["case_id"]
        wait_for_review(c, case_id)
        html = c.get(f"/api/cases/{case_id}/report", headers=AUTH).text
        assert "NET_MISMATCH" in html and "case_ring_1" in html
        assert "2590312" not in html and "IONESCU" not in html


def test_rerun_demo_uses_real_maria_files_and_renders_pdf():
    with TestClient(app) as c:
        case_id = c.post("/api/admin/rerun-demo", headers=AUTH).json()["case_id"]
        case = wait_for_review(c, case_id)
        assert [d["type"] for d in case["documents"]] == ["id_card", "payslip", "bank_statement"]
        assert case["fingerprints"]  # scrise de Paznic (aici: stub)
        jpg = c.get(f"/api/cases/{case_id}/documents/doc_2/image", headers=AUTH)
        assert jpg.headers["content-type"] == "image/jpeg"
        pdf_page = c.get(f"/api/cases/{case_id}/documents/doc_3/image?page=1", headers=AUTH)
        assert pdf_page.headers["content-type"] == "image/png"
        assert c.get(f"/api/cases/{case_id}/documents/doc_1/image?view=ela", headers=AUTH).status_code == 404


def test_downstream_agents_skipped_when_paznic_fails(monkeypatch):
    from app.agents import registry

    class Broken:
        async def run(self, case, ctx):
            raise RuntimeError("x")

    monkeypatch.setitem(registry.AGENTS, "paznic", Broken())
    with TestClient(app) as c:
        case = wait_for_review(c, c.post("/api/admin/rerun-demo", headers=AUTH).json()["case_id"])
        status = {r["agent"]: r["status"] for r in case["results"]}
        assert status["paznic"] == "error"
        assert status["functionar"] == status["verificator"] == status["detectiv"] == "skipped"
        assert status["detector"] == "done" and case["verdict"]["incomplete"]
