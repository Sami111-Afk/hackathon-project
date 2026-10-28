import asyncio

import pytest
from fastapi.testclient import TestClient

from app.arena import service
from app.learning import engine, proposer
from app.main import app
from tests.conftest import AUTH

WIN = {"nickname": "Vlad", "mission_id": "payslip_9000",
       "edits": {"gross_salary": 16000, "employer": "Bitwave Software SRL"}, "tricks": ["recompute_taxes"]}


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    service.reset()
    proposer.reset()
    monkeypatch.setattr(proposer, "on_arena_miss", lambda sid: None)  # fără LLM în teste
    from app.arena import ratelimit
    ratelimit._hits.clear()


def post(c, body):
    return c.post("/api/arena/submissions", json=body)


def test_public_routes_need_no_token():
    with TestClient(app) as c:
        assert c.get("/api/arena/missions").status_code == 200
        assert c.get("/api/arena/leaderboard").status_code == 200


def test_naive_fake_is_caught_and_explained():
    with TestClient(app) as c:
        r = post(c, {"nickname": "Ana", "mission_id": "payslip_9000", "edits": {"net_salary": 9500}}).json()
        assert r["outcome"] == "caught" and r["points"] > 0
        assert any("Calculated net pay" in x for x in r["reasons"])
        assert "doc" not in r  # proiecția publică nu conține date interne
        img = c.get(f"/api/arena/submissions/{r['id']}/image")
        assert img.headers["content-type"] == "image/jpeg"


def test_unchanged_or_target_missed_gives_no_points():
    with TestClient(app) as c:
        r = post(c, {"nickname": "Ana", "mission_id": "payslip_9000", "edits": {}}).json()
        assert r["outcome"] == "invalid" and r["points"] == 0


def test_clever_fake_passes_then_duplicate_gets_nothing():
    with TestClient(app) as c:
        first = post(c, WIN).json()
        assert first["outcome"] == "passed" and first["points"] == service.POINTS_PASSED
        again = post(c, WIN).json()
        assert again["duplicate"] and again["points"] == 0
        assert c.get("/api/arena/leaderboard").json()["top"][0] == {"rank": 1, "nickname": "Vlad", "points": 500}


def test_bad_nickname_and_rate_limit():
    with TestClient(app) as c:
        assert post(c, {**WIN, "nickname": "x"}).status_code == 400
        codes = [post(c, {**WIN, "nickname": f"P{i}"}).status_code for i in range(7)]
        assert 429 in codes


def test_learned_rule_catches_the_trick_after_approval(monkeypatch):
    rule = {"description": "Gross above 2× the job-title median", "then": {
        "code": "GROSS_ABOVE_ROLE", "severity": "medium", "message": "Gross far above the job-title median"},
        "when": {"left": "doc.gross_salary", "op": "ratio_gt", "right": ["company.role_median", 2.0]}}
    bad_rule = {**rule, "description": "Too broad", "when": {"left": "doc.gross_salary", "op": "gt", "right": 0}}

    class Fake:
        data = proposer.Proposal(reasoning="test", rules=[proposer.ProposedRule(**bad_rule),
                                                           proposer.ProposedRule(**rule)])
        usage = None

    async def fake_chat(*a, **k):
        return Fake

    monkeypatch.setattr(proposer, "chat", fake_chat)
    with TestClient(app) as c:
        sub = post(c, WIN).json()
        rules = c.post(f"/api/rules/learn/{sub['id']}", headers=AUTH).json()
        assert rules[0]["status"] == "rejected" and "legitimate" in rules[0]["vetting"]
        good = rules[1]
        assert good["status"] == "proposed" and good["backtest"]["false_positives"] == 0
        c.post(f"/api/rules/{good['id']}/approve", headers=AUTH, json={"decided_by": "Andrei"})
        assert len(engine.RULES) == 1
        retry = post(c, {**WIN, "nickname": "Vlad2", "edits": {**WIN["edits"], "gross_salary": 16100}}).json()
        assert retry["outcome"] == "caught"
        assert any("job-title" in x for x in retry["reasons"])
        # un programator cu salariu normal la aceeași firmă trece în continuare
        honest = post(c, {"nickname": "Ion", "mission_id": "payslip_ceo", "tricks": ["recompute_taxes"],
                          "edits": {"gross_salary": 34500, "job_title": "Director"}}).json()
        assert honest["outcome"] == "passed"


def test_rule_engine_rejects_unknown_fields():
    ok, why, _ = proposer.vet({"when": {"left": "doc.cnp", "op": "eq", "right": 1}}, {}, [])
    assert not ok and "unknown fields" in why
    asyncio.run(asyncio.sleep(0))



def test_attacker_adapts_and_finally_passes():
    from app.arena import attacker
    attacker.state.running, attacker.state.rounds = False, []
    with TestClient(app) as c:
        assert c.post("/api/admin/attacker/start", headers=AUTH, json={"rounds": 4}).status_code == 200
        for _ in range(300):
            s = c.get("/api/admin/attacker/status", headers=AUTH).json()
            if not s["running"]:
                break
            asyncio.run(asyncio.sleep(0.05))
        outcomes = [r["outcome"] for r in s["rounds"]]
        assert outcomes[0] == "caught" and "passed" in outcomes[1:]


def test_review_regressions():
    from app.learning import engine as eng
    with TestClient(app) as c:
        assert post(c, {**WIN, "nickname": "Big", "edits": {"gross_salary": "1e999"}}).status_code == 400
        a = post(c, {**WIN, "nickname": "Dup1"}).json()
        b = post(c, {**WIN, "nickname": "Dup2", "tricks": ["recompute_taxes", "recompute_taxes"]}).json()
        assert a["points"] == 500 and b["duplicate"] and b["points"] == 0
        assert post(c, {**WIN, "nickname": "AI-Atacator"}).status_code == 400
        futuristic = {**WIN, "nickname": "Futuristic", "edits": {**WIN["edits"], "gross_salary": 16100}}
        assert post(c, futuristic).status_code == 200
    broken = {"id": "r", "status": "approved", "then": {"code": "X", "severity": "high", "message": "x"},
              "when": {"left": "doc.issue_date", "op": "lt", "right": "nu-e-data"}}
    assert eng.apply_rules({"issue_date": "2026-09-30", "employer": "x"}, [broken]) == []
    doc = {"gross_salary": 16000, "net_salary": 9360, "employer": "Bitwave Software SRL",
           "job_title": "Operator date", "issue_date": "2026-09-30", "tricks": []}
    ok, why, _ = proposer.vet({"when": {"left": "doc.issue_date", "op": "eq", "right": "2026-09-30"}}, doc,
                              proposer.legit_dataset())
    assert not ok and "too specific" in why
