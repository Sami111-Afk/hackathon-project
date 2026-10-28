import base64

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.zk import bank, employer, tools
from tests.conftest import AUTH

needs_tools = pytest.mark.skipif(not tools.available(), reason="nargo/bb lipsesc (vezi zk/README.md)")
client = TestClient(app)


def test_threshold_is_installment_over_dsti():
    assert bank.threshold_for(200_000) == 500_000  # rată 2.000 lei → prag 5.000 lei
    assert bank.threshold_for(100_001) == 250_003  # rotunjit în sus, în favoarea băncii


def test_public_inputs_layout():
    pub = tools.public_inputs(500_000, 0x1234, 7)
    assert len(pub) == 96 and int.from_bytes(pub[:32], "big") == 500_000 and pub[-1] == 7


def test_signature_is_bound_to_cui_period_and_nonce():
    sig = employer.sign_with_unregistered_key("RO9341910290", "2026-09", 5, 7)
    assert not employer.verify_signature("RO9341910290", "2026-09", 5, 7, sig)  # cheie necunoscută
    employer.registry()
    key = employer._keys["RO9341910290"]
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    good = base64.b64encode(key.sign(employer.message("RO9341910290", "2026-09", 5, 7),
                                     ec.ECDSA(hashes.SHA256()))).decode()
    assert employer.verify_signature("RO9341910290", "2026-09", 5, 7, good)
    assert not employer.verify_signature("RO9341910290", "2026-08", 5, 7, good)
    assert not employer.verify_signature("RO9341910290", "2026-09", 5, 8, good)
    assert not employer.verify_signature("RO9185472906", "2026-09", 5, 7, good)


def test_routes_require_bank_token():
    assert client.post("/api/zk/demo", json={}).status_code == 401


@needs_tools
def test_honest_client_gets_yes_and_bank_never_sees_salary():
    r = client.post("/api/zk/demo", json={"net_salary_ron": 8307, "installment_ron": 2500}, headers=AUTH)
    body = r.json()
    assert r.status_code == 200 and body["answer"] == "DA", body
    assert body["threshold_ron"] == 6250
    assert "8307" not in str(body["bank_saw"]) and "830700" not in str(body["bank_saw"])


@needs_tools
@pytest.mark.parametrize(("attack", "reason"), [
    ("lie_salary", "invalid commitment"),
    ("lower_threshold", "the ZK proof is not valid"),
    ("fake_signature", "employer signature"),
    ("replay", "already used"),
])
def test_attacks_are_rejected(attack, reason):
    body = client.post("/api/zk/demo", json={"attack": attack}, headers=AUTH).json()
    assert body["answer"] == "NU" and reason in body["reason"], body


@needs_tools
def test_income_below_threshold_cannot_be_proven():
    body = client.post("/api/zk/demo", json={"net_salary_ron": 3000, "installment_ron": 2500}, headers=AUTH).json()
    assert body["answer"] == "NU" and "income below threshold" in body["reason"]


@needs_tools
def test_step_by_step_api_flow():
    n = client.post("/api/zk/nonce", json={"installment_ron": 2000}, headers=AUTH).json()
    assert n["threshold_ron"] == 5000
    req = {"cui": "RO9185472906", "period": "2026-09", "net_salary_ron": 6100.5, "nonce": n["nonce"]}
    a = client.post("/api/zk/employer/attest", json=req, headers=AUTH).json()
    p = client.post("/api/zk/client/prove", json={**a["client"], "commitment": a["for_bank"]["commitment"],
                                                  "nonce": n["nonce"], "threshold_ron": n["threshold_ron"]},
                    headers=AUTH).json()
    v = client.post("/api/zk/verify", json={**a["for_bank"], "nonce": n["nonce"], "proof_b64": p["proof_b64"]},
                    headers=AUTH).json()
    assert v["answer"] == "DA", v
    # aceeași dovadă, altă cerere (nonce nou) → NU
    n2 = client.post("/api/zk/nonce", json={"installment_ron": 2000}, headers=AUTH).json()
    v2 = client.post("/api/zk/verify", json={**a["for_bank"], "nonce": n2["nonce"], "proof_b64": p["proof_b64"]},
                     headers=AUTH).json()
    assert v2["answer"] == "NU"
