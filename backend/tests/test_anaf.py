"""ANAF: registrul demo, API-ul real (simulat aici, fără rețea), cache, rate limit, moduri fără rețea."""
import json
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest

from app.agents.verificator import anaf
from app.config import settings

# răspunsul real al PlatitorTvaRest v9 (prescurtat), pentru Raiffeisen Bank SA
RAIFFEISEN = {
    "date_generale": {"cui": 361820, "denumire": "RAIFFEISEN BANK SA", "data_inregistrare": "1992-12-10",
                      "stare_inregistrare": "INREGISTRAT din data 22.03.2005"},
    "stare_inactiv": {"dataInactivare": "", "dataReactivare": "", "dataPublicare": "", "dataRadiere": "",
                      "statusInactivi": False},
}
INACTIVE = {"date_generale": {"cui": 123456, "denumire": "FIRMA INACTIVA SRL", "data_inregistrare": "2020-01-01"},
            "stare_inactiv": {"dataInactivare": "2024-03-01", "dataRadiere": "", "statusInactivi": True}}


class FakeANAF:
    def __init__(self, found=None, fail=False):
        self.found, self.fail, self.calls = found, fail, []

    def __call__(self, url, json=None, timeout=None):
        self.calls.append(json)
        if self.fail:
            raise httpx.ConnectTimeout("timeout")
        body = {"found": [self.found] if self.found else [], "notFound": [] if self.found else [json[0]["cui"]]}
        status = 200 if self.found else 404  # așa răspunde ANAF-ul real pentru un CUI inexistent
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))


@pytest.fixture
def online(monkeypatch, tmp_path):
    monkeypatch.setattr(anaf, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(anaf, "MIN_INTERVAL_S", 0)
    monkeypatch.setattr(anaf, "online_allowed", lambda: True)
    return tmp_path


def use(monkeypatch, fake):
    monkeypatch.setattr(anaf.httpx, "post", fake)
    return fake


def test_demo_registry_first_without_network(online, monkeypatch):
    fake = use(monkeypatch, FakeANAF(RAIFFEISEN))
    company, source = anaf.resolve("RO40211937")
    assert (company.name, company.active, source) == ("Agro Prahova Distribuție SRL", False, "demo")
    assert fake.calls == []


def test_real_company_found_and_cached(online, monkeypatch):
    fake = use(monkeypatch, FakeANAF(RAIFFEISEN))
    company, source = anaf.resolve("RO361820", on=date(2026, 10, 28))
    assert source == "anaf" and company.name == "RAIFFEISEN BANK SA" and company.active
    assert company.founded == date(1992, 12, 10)
    assert fake.calls == [[{"cui": 361820, "data": "2026-10-28"}]]
    assert anaf.check_company(company, source, "d", "[CUI_1]") == []

    again, source = anaf.resolve("361820")
    assert source == "cache" and again == company and len(fake.calls) == 1


def test_inactive_company(online, monkeypatch):
    use(monkeypatch, FakeANAF(INACTIVE))
    company, source = anaf.resolve("123456")
    f = anaf.check_company(company, source, "d", "[CUI_1]")
    assert [x.code for x in f] == ["COMPANY_INACTIVE"]


def test_not_found_only_from_real_anaf(online, monkeypatch):
    use(monkeypatch, FakeANAF(None))
    company, source = anaf.resolve("99999999")
    assert company is None and source == "anaf"
    f = anaf.check_company(company, source, "d", "[CUI_1]")
    assert f[0].code == "COMPANY_NOT_FOUND" and f[0].severity == "critical"
    assert json.loads((online / "99999999.json").read_text())["record"] is None


def test_network_down_is_unverified_not_not_found(online, monkeypatch):
    use(monkeypatch, FakeANAF(fail=True))
    company, source = anaf.resolve("361820")
    assert (company, source) == (None, "unavailable")
    assert anaf.check_company(company, source, "d", "[CUI_1]")[0].code == "COMPANY_UNVERIFIED"


def test_network_down_falls_back_to_stale_cache(online, monkeypatch):
    stale = (datetime.now(UTC) - timedelta(days=3)).isoformat(timespec="seconds")
    (online / "361820.json").write_text(json.dumps({"fetched": stale, "record": RAIFFEISEN}))
    use(monkeypatch, FakeANAF(fail=True))
    company, source = anaf.resolve("361820")
    assert source == "cache" and company.name == "RAIFFEISEN BANK SA"


def test_local_mode_never_calls_out(monkeypatch, tmp_path):
    monkeypatch.setattr(anaf, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "env", "dev")
    monkeypatch.setattr(settings, "llm_mode", "local")
    fake = use(monkeypatch, FakeANAF(RAIFFEISEN))
    assert anaf.resolve("361820") == (None, "unavailable") and fake.calls == []


def test_tests_never_call_out_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(anaf, "CACHE_DIR", tmp_path)
    fake = use(monkeypatch, FakeANAF(RAIFFEISEN))
    assert anaf.resolve("361820")[1] == "unavailable" and fake.calls == []


def test_labels_and_garbage_are_not_sent(online, monkeypatch):
    fake = use(monkeypatch, FakeANAF(RAIFFEISEN))
    assert anaf.resolve("[CUI_1]") == (None, "unavailable")
    assert anaf.resolve(None) == (None, "unavailable")
    assert fake.calls == []


def test_rate_limit_spaces_calls(online, monkeypatch):
    monkeypatch.setattr(anaf, "MIN_INTERVAL_S", 0.2)
    slept = []
    monkeypatch.setattr(anaf.time, "sleep", slept.append)
    use(monkeypatch, FakeANAF(RAIFFEISEN))
    anaf.resolve("361820")
    anaf.resolve("361821")
    assert slept and 0 < slept[-1] <= 0.2


def test_external_call_is_audited(online, monkeypatch):
    from app.core import audit

    use(monkeypatch, FakeANAF(RAIFFEISEN))
    anaf.resolve("361820", case_id="case_a")
    entry = next(e for e in audit.recent() if e["kind"] == "anaf")  # recent(): cele mai noi primele
    assert entry["case_id"] == "case_a" and entry["outcome"] == "sent"


def test_http_404_without_anaf_body_is_an_error(online, monkeypatch):
    def broken(url, json=None, timeout=None):
        return httpx.Response(404, json={"error": "x"}, request=httpx.Request("POST", url))

    use(monkeypatch, broken)
    assert anaf.resolve("361820") == (None, "unavailable")
