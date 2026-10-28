"""Verificarea netului pe date criptate (CKKS). Se sar dacă TenSEAL nu e instalat (CI cu requirements-core)."""
import asyncio
import random

import pytest

pytest.importorskip("tenseal")

from app.agents.verificator import he_bank, he_verifier  # noqa: E402
from app.agents.verificator.agent import Verificator  # noqa: E402
from app.agents.verificator.tax import check_net  # noqa: E402
from app.config import settings  # noqa: E402
from tests.test_functionar_agent import Ctx, maria_case, paznic_scratch  # noqa: E402
from tests.test_verificator import MARIA_VAULT, TODAY, run_both  # noqa: E402

bank = he_bank.Bank()


def test_maria_net_mismatch_on_encrypted_data():
    report = bank.verify_nets([he_bank.NetItem("doc_2", 14200, 8500, "2026-09")])
    check = report.checks[0]
    assert not check.ok and check.computed_net == 8307
    assert report.slots == 5  # 0–4 persoane în întreținere, într-un singur vector


def test_encrypted_result_is_identical_to_clear_calculation():
    rng = random.Random(7)
    items, expected = [], []
    for i in range(300):
        gross = rng.choice([rng.randint(4050, 6600), rng.randint(6600, 40000)])
        period = rng.choice(["2026-03", "2026-09", None])
        net = rng.choice([gross * 0.585, gross * 0.585 + rng.uniform(-6, 6), gross * 0.6])
        items.append(he_bank.NetItem(f"d{i}", gross, round(net, 2), period))
        expected.append(check_net(gross, round(net, 2), period=period) is None)
    report = bank.verify_nets(items)
    assert [c.ok for c in report.checks] == expected
    assert report.slots == 1500


def test_tolerance_edge_matches_clear_to_the_ban():
    # netul corect e 14.772: la exact 2,00 lei diferență trece (ca în clar), la 2,01 nu
    ok = bank.verify_nets([he_bank.NetItem("a", 25251, 14770.0), he_bank.NetItem("b", 25251, 14769.99)])
    assert [c.ok for c in ok.checks] == [True, False]
    assert check_net(25251, 14770.0) is None and check_net(25251, 14769.99) is not None


def test_honest_low_wage_with_children_is_accepted():
    # brut 4.500, 2 copii: deducere mare → netul real e peste forma fără deducere
    from app.agents.verificator.tax import compute_payslip

    net = compute_payslip(4500, 2, None, "2026-09").net
    assert bank.verify_nets([he_bank.NetItem("d", 4500, net, "2026-09")]).checks[0].ok
    assert not bank.verify_nets([he_bank.NetItem("d", 4500, net, "2026-09", dependents=0)]).checks[0].ok


def test_verifier_only_sees_public_context_and_cannot_decrypt():
    seen = {}

    def spy(package):
        import tenseal as ts

        ctx = ts.context_from(package["context"])
        seen["secret"] = ctx.has_secret_key()
        with pytest.raises(ValueError):
            ts.ckks_vector_from(ctx, package["gross"]).decrypt()
        return he_verifier.compute_net_diff(package)

    report = bank.verify_nets([he_bank.NetItem("d", 14200, 8500)], verifier=spy)
    assert seen["secret"] is False and not report.checks[0].ok


def test_verifier_refuses_context_with_secret_key():
    ctx = bank._context()
    with pytest.raises(ValueError):
        he_verifier.compute_net_diff({"context": ctx.serialize(save_secret_key=True)})


def test_artifacts_for_ui():
    art = bank.verify_nets([he_bank.NetItem("d", 14200, 8500)]).artifacts()
    assert art["he_scheme"].startswith("CKKS") and int(art["he_context_kb"]) > 100
    assert len(art["he_ciphertext_sample"]) == 32 and art["he_formula"] == he_verifier.FORMULA


def test_agent_uses_encryption_when_enabled(monkeypatch):
    from app.agents.functionar import agent as functionar_agent
    from app.core.llm import LLMUnavailable

    async def unavailable(*a, **k):
        raise LLMUnavailable("mock")

    monkeypatch.setattr(functionar_agent, "chat", unavailable)
    monkeypatch.setattr(settings, "he_enabled", True)
    result = run_both(maria_case(), paznic_scratch(), monkeypatch, MARIA_VAULT)
    assert result.artifacts["he_slots"] == "5"
    f = next(f for f in result.findings if f.code == "NET_MISMATCH")
    assert f.message == "Calculated net pay (8.307 lei) differs from the declared one (8.500 lei)" and f.evidence.bbox

    monkeypatch.setattr(settings, "he_enabled", False)
    clear = run_both(maria_case(), paznic_scratch(), monkeypatch, MARIA_VAULT)
    assert "he_slots" not in clear.artifacts
    assert [f.message for f in clear.findings] == [f.message for f in result.findings]


def test_agent_falls_back_to_clear_if_encryption_breaks(monkeypatch):
    from app.agents.functionar import agent as functionar_agent
    from app.core.llm import LLMUnavailable

    async def unavailable(*a, **k):
        raise LLMUnavailable("mock")

    def broken(*a, **k):
        raise RuntimeError("TenSEAL a picat")

    monkeypatch.setattr(functionar_agent, "chat", unavailable)
    monkeypatch.setattr(settings, "he_enabled", True)
    monkeypatch.setattr(he_bank.bank, "verify_nets", broken)
    result = run_both(maria_case(), paznic_scratch(), monkeypatch, MARIA_VAULT)
    assert "NET_MISMATCH" in [f.code for f in result.findings] and "he_slots" not in result.artifacts


def test_stub_path_unaffected():
    result = asyncio.run(Verificator(today=TODAY).run(maria_case(), Ctx({})))
    assert result.agent == "verificator"
