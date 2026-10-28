from fastapi.testclient import TestClient

from app.main import app


def test_health():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# TODO (Samuel, ora 8): dosarul Mariei în modul mock trece cap-coadă
# și ajunge la awaiting_review cu recommendation == "escalate".
