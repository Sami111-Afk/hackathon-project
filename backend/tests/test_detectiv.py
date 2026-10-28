"""Detectivul: rețele găsite doar între identități diferite, Arena izolată, graful pentru frontend."""
import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.agents.detectiv.agent import Detectiv, analyze, noisy_or
from app.agents.detectiv.graph import build_graph, cluster_of, graph_payload
from app.core.store import store
from app.main import app
from app.models import Case
from tests.conftest import AUTH

NOW = datetime(2026, 10, 28, 12, tzinfo=UTC)


def save_ring(prefix: str, phone: str = "hm_9c1e", n: int = 5) -> list[str]:
    """Pune în store n dosare recente, pe identități diferite, cu același telefon (fără /seed-demo,
    ca să nu încurce testele care verifică seed-ul)."""
    ids = []
    for i in range(n):
        ts = (datetime.now(UTC) - timedelta(days=3 + i)).isoformat().replace("+00:00", "Z")
        case = Case(id=f"{prefix}_{i}", created_at=ts, status="escalated",
                    fingerprints={"phone": [phone], "cnp": [f"{prefix}_cnp{i}"]})
        asyncio.run(store.save(case))
        ids.append(case.id)
    return ids


def mk(case_id: str, days_ago: float = 1, source: str = "bank", **fps) -> Case:
    ts = (NOW - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")
    return Case(id=case_id, created_at=ts, source=source, fingerprints={k: [v] for k, v in fps.items()})


def codes(findings) -> dict[str, str]:
    return {f.code: f.severity for f in findings}


def test_ring_of_five_identities_is_critical():
    maria = mk("maria", phone="P", cnp="C0", iban="I")
    ring = [mk(f"r{i}", days_ago=21 - 4 * i, phone="P", cnp=f"C{i + 1}") for i in range(5)]
    findings, stats = analyze(maria, ring, NOW)
    assert codes(findings) == {"FRAUD_RING_SUSPECTED": "critical"}
    assert "5 other applications, under 5 different identities, in the last 3 weeks" in findings[0].message
    assert stats == {"linked_cases": 5, "linked_identities": 5}
    assert noisy_or(findings) == 0.85


def test_same_person_applying_again_is_not_a_ring():
    """Același CNP = același client care revine, nu o rețea."""
    a = mk("a", phone="P", cnp="C")
    old = [mk(f"old{i}", phone="P", cnp="C") for i in range(4)]
    findings, _ = analyze(a, old, NOW)
    assert findings == []


def test_one_shared_phone_is_only_medium():
    """Un telefon comun cu o singură altă persoană poate fi familia → doar verificare."""
    findings, _ = analyze(mk("a", phone="P", cnp="C1"), [mk("b", phone="P", cnp="C2")], NOW)
    assert codes(findings) == {"SHARED_CONTACT": "medium"}


def test_shared_iban_with_other_identity_is_high():
    findings, _ = analyze(mk("a", iban="I", cnp="C1"), [mk("b", iban="I", cnp="C2")], NOW)
    assert codes(findings) == {"SHARED_IBAN": "high"}


def test_shared_address_needs_three_identities():
    a = mk("a", address="A", cnp="C0")
    assert analyze(a, [mk("b", address="A", cnp="C1"), mk("c", address="A", cnp="C2")], NOW)[0] == []
    three = [mk(f"x{i}", address="A", cnp=f"C{i + 1}") for i in range(3)]
    assert codes(analyze(a, three, NOW)[0]) == {"SHARED_ADDRESS": "medium"}


def test_cluster_follows_strong_links_only():
    """a –telefon– b –IBAN– c e un cluster; d are doar adresa comună → nu intră."""
    cases = [mk("a", phone="P", address="A"), mk("b", phone="P", iban="I"), mk("c", iban="I"), mk("d", address="A")]
    g = build_graph(cases)
    assert cluster_of(g, "a") == {"a", "b", "c"}
    payload = graph_payload(g, "a")
    assert set(payload["cluster"]) == {"a", "b", "c"}
    focus = [n for n in payload["nodes"] if n.get("is_focus")]
    assert len(focus) == 1 and focus[0]["case_id"] == "a"
    ids = {n["id"] for n in payload["nodes"]}
    assert all(lk["source"] in ids and lk["target"] in ids for lk in payload["links"])
    assert all(lk["source"].startswith("case:") and lk["target"].startswith("fp:") for lk in payload["links"])


class FakeCtx:
    def __init__(self):
        self.events = []

    async def emit(self, type, message="", data=None):
        self.events.append((type, message, data))


def test_arena_case_never_sees_bank_cases(monkeypatch):
    bank = [mk(f"r{i}", phone="P", cnp=f"C{i}") for i in range(5)]
    monkeypatch.setattr("app.agents.detectiv.agent.store.list", lambda: bank)
    ctx = FakeCtx()
    result = asyncio.run(Detectiv().run(mk("arena_1", source="arena", phone="P", cnp="X"), ctx))
    assert codes(result.findings) == {"NO_LINKS": "info"}
    assert ctx.events == []


def test_agent_streams_graph_without_personal_data(monkeypatch):
    maria = mk("maria", phone="P", cnp="C0")
    ring = [mk(f"r{i}", phone="P", cnp=f"C{i + 1}") for i in range(15)]
    monkeypatch.setattr("app.agents.detectiv.agent.store.list", lambda: [maria, *ring])
    ctx = FakeCtx()
    result = asyncio.run(Detectiv().run(maria, ctx))
    assert result.risk == 0.85 and result.artifacts["graph"] == "/api/graph?case_id=maria"
    sent = {n["id"] for _, _, d in ctx.events for n in d["graph_delta"]["nodes"]}
    assert {f"case:r{i}" for i in range(15)} <= sent  # și cele peste limita animației
    links = [lk for _, _, d in ctx.events for lk in d["graph_delta"]["links"]]
    assert all(lk["source"] in sent and lk["target"] in sent for lk in links)


def test_graph_endpoint():
    with TestClient(app) as c:
        assert c.get("/api/graph").status_code == 401
        ring = save_ring("t_graph", phone="hm_t_graph")
        lone = save_ring("t_lone", phone="hm_t_lone", n=1)
        g = c.get(f"/api/graph?case_id={ring[0]}", headers=AUTH).json()
        assert set(g["cluster"]) == set(ring)
        assert lone[0] not in g["cluster"]
        assert c.get("/api/graph?case_id=nu_exista", headers=AUTH).status_code == 404


def test_graph_labels_never_show_fingerprints():
    """Paznicul real pune o amprentă (hm_…) în applicant_token; pe graf apare ID-ul dosarului."""
    a = mk("a", phone="P", name="hm_nume1")
    a.applicant_token = "hm_nume1"
    b = mk("b", phone="P", name="hm_nume2")
    b.applicant_token = "[PERSOANA_B]"
    labels = {n["case_id"]: n["label"] for n in graph_payload(build_graph([a, b]), "a")["nodes"] if n["type"] == "case"}
    assert labels == {"a": "a", "b": "[PERSOANA_B]"}


def test_same_name_without_cnp_is_same_person():
    findings, _ = analyze(mk("a", phone="P", name="N"), [mk(f"b{i}", phone="P", name="N") for i in range(3)], NOW)
    assert findings == []


def test_colleague_with_same_employer_is_not_a_ring(monkeypatch):
    """Același CUI (angajator) la alt om: nimic semnalat, fără animație de graf, nod CUI neroșu."""
    me, colleague = mk("me", cui="FIRMA", cnp="C1"), mk("col", cui="FIRMA", cnp="C2")
    findings, stats = analyze(me, [colleague], NOW)
    assert findings == [] and stats["linked_cases"] == 0
    monkeypatch.setattr("app.agents.detectiv.agent.store.list", lambda: [me, colleague])
    ctx = FakeCtx()
    asyncio.run(Detectiv().run(me, ctx))
    assert ctx.events == []
    g = graph_payload(build_graph([me, colleague, mk("x", phone="P"), mk("y", phone="P")]))
    cui = next(n for n in g["nodes"] if n["id"] == "fp:cui:FIRMA")
    assert cui["in_cluster"] is False
