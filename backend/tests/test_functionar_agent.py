"""Funcționarul pe cuvintele redactate ale Mariei (layout-ul din data/generator/build_demo.py)."""
import asyncio

import pytest

from app.agents.functionar import agent as functionar_agent
from app.agents.functionar.agent import Functionar
from app.agents.functionar.grounding import find_in_text, find_in_words
from app.agents.functionar.layout import group_lines
from app.agents.functionar.schemas import PayslipFields, RawField
from app.agents.functionar.statement import parse_statement
from app.core.llm import LLMResponse, LLMUnavailable
from app.core.pii_gate import PIIGateBlocked
from app.models import Case, Document, LLMUsage

CHAR_W, H = 12, 30


def words_of(layout, page=1):
    """layout = [(y, [(x, "text cu spații"), ...]), ...] → cuvinte {text, page, bbox}."""
    out = []
    for y, cells in layout:
        for x, text in cells:
            for token in text.split():
                out.append({"text": token, "page": page, "bbox": [x, y, x + CHAR_W * len(token), y + H]})
                x += CHAR_W * (len(token) + 1)
    return out


PAYSLIP = words_of([
    (80, [(80, "[FIRMA_1]")]),
    (125, [(80, "CUI [CUI_1] · Ploiești, jud. Prahova")]),
    (230, [(80, "FLUTURAȘ DE SALARIU")]),
    (290, [(80, "Luna: septembrie 2026 · Emis: 30.09.2026")]),
    (380, [(80, "Angajat"), (950, "[PERSOANA_1]")]),
    (450, [(80, "CNP"), (1000, "[CNP_1]")]),
    (520, [(80, "Funcția"), (1050, "Contabil")]),
    (590, [(80, "Salariu brut"), (1050, "14.200,00")]),
    (660, [(80, "CAS 25%"), (1040, "-3.550,00")]),
    (730, [(80, "CASS 10%"), (1040, "-1.420,00")]),
    (800, [(80, "Impozit 10%"), (1070, "-923,00")]),
    (900, [(80, "NET DE PLATĂ"), (1050, "8.500,00")]),
])

STATEMENT = words_of([
    (45, [(80, "Raiffeisen BANK")]),
    (200, [(80, "EXTRAS DE CONT")]),
    (260, [(80, "Titular: [PERSOANA_1]")]),
    (295, [(80, "IBAN: [IBAN_1]")]),
    (330, [(80, "Perioada: 01.09.2026 – 30.09.2026")]),
    (420, [(80, "Data"), (230, "Descriere"), (780, "Sumă"), (1100, "Sold")]),
    (470, [(80, "01.09"), (230, "Sold inițial"), (1050, "1.240,50")]),
    (515, [(80, "05.09"), (230, "Plată pensie"), (740, "2.310,00"), (1050, "3.550,50")]),
    (560, [(80, "12.09"), (230, "Cumpărături card"), (760, "-412,30"), (1050, "3.138,20")]),
    (605, [(80, "20.09"), (230, "Factură utilități"), (760, "-286,70"), (1050, "2.851,50")]),
    (680, [(80, "Sold final"), (1030, "26.480,00")]),
])

ID_CARD = words_of([
    (30, [(40, "ROMÂNIA · ROUMANIE · ROMANIA")]),
    (140, [(40, "CARTE DE IDENTITATE / IDENTITY CARD"), (900, "SERIA [SERIE_1] NR [NR_1]")]),
    (190, [(900, "CNP [CNP_1]")]),
    (250, [(440, "Nume/Nom/Last name")]), (276, [(440, "[PERSOANA_1]")]),
    (322, [(440, "Prenume/Prénom/First name")]), (348, [(440, "[PERSOANA_1]")]),
    (394, [(440, "Cetățenie/Nationalité/Nationality")]), (420, [(440, "Română / ROU")]),
    (466, [(440, "Sex/Sexe/Sex")]), (492, [(440, "F")]),
    (538, [(440, "Loc naștere/Lieu de naissance/Place of birth")]), (564, [(440, "Mun. Ploiești, Jud. PH")]),
    (610, [(440, "Domiciliu/Adresse/Address")]), (636, [(440, "[ADRESA_1]")]),
    (682, [(440, "Valabilitate/Validité/Validity")]), (708, [(440, "20.05.19-12.03.2029")]),
    (840, [(40, "[MRZ_1]")]),
])


class Ctx:
    def __init__(self, scratch):
        self.scratch = scratch
        self.events = []

    async def emit(self, type, message="", data=None):
        self.events.append(message)


def maria_case():
    docs = [Document(id="doc_1", filename="buletin.jpg"), Document(id="doc_2", filename="fluturas.jpg"),
            Document(id="doc_3", filename="extras.pdf")]
    return Case(id="case_t", created_at="2026-10-28T10:00:00Z", documents=docs)


def paznic_scratch():
    return {"paznic": {"doc_1": {"source": "ocr", "is_id_card": True, "words": ID_CARD},
                       "doc_2": {"source": "ocr", "is_id_card": False, "words": PAYSLIP},
                       "doc_3": {"source": "ocr", "is_id_card": False, "words": STATEMENT}}}


def run_agent(case, ctx):
    return asyncio.run(Functionar().run(case, ctx))


def codes(result):
    return [f.code for f in result.findings]


@pytest.fixture
def no_llm(monkeypatch):
    async def unavailable(*a, **k):
        raise LLMUnavailable("mod mock: niciun răspuns salvat")

    monkeypatch.setattr(functionar_agent, "chat", unavailable)


def test_maria_without_llm_reads_everything_by_labels(no_llm):
    case, ctx = maria_case(), Ctx(paznic_scratch())
    result = run_agent(case, ctx)
    card, slip, stmt = case.documents

    assert [d.type for d in case.documents] == ["id_card", "payslip", "bank_statement"]
    assert result.findings[0].message == "3 documente: buletin, fluturaș, extras"
    assert "EXTRACTION_RULES_ONLY" in codes(result) and "EXTRACTION_UNGROUNDED" not in codes(result)

    s = {k: v.value for k, v in slip.extracted.items()}
    assert s["gross_salary"] == 14200 and s["net_salary"] == 8500
    assert (s["cas"], s["cass"], s["income_tax"]) == (-3550, -1420, -923)
    assert (s["period"], s["issue_date"], s["employer_cui"]) == ("2026-09", "2026-09-30", "[CUI_1]")
    assert s["employer_name"] == "[FIRMA_1]" and s["job_title"] == "Contabil"
    assert slip.extracted["net_salary"].source_text == "8.500,00"

    c = {k: v.value for k, v in card.extracted.items()}
    assert (c["sex"], c["issue_date"], c["expiry_date"]) == ("F", "2019-05-20", "2029-03-12")
    assert c["series"] == "[SERIE_1]" and c["last_name"] == "[PERSOANA_1]"

    t = {k: v.value for k, v in stmt.extracted.items()}
    assert (t["opening_balance"], t["closing_balance"]) == (1240.5, 26480)
    assert (t["period_start"], t["period_end"], t["iban"]) == ("2026-09-01", "2026-09-30", "[IBAN_1]")


def test_evidence_and_statement_rows_for_verificator(no_llm):
    case, ctx = maria_case(), Ctx(paznic_scratch())
    run_agent(case, ctx)
    out = ctx.scratch["functionar"]

    net = out["doc_2"]["fields"]["net_salary"]
    assert net["page"] == 1 and net["bbox"][1] == 900  # bbox-ul sumei, pentru dovada din UI

    table = out["doc_3"]["statement"]
    assert [r["balance"] for r in table["rows"]] == [1240.5, 3550.5, 3138.2, 2851.5]
    assert [r["amount"] for r in table["rows"]] == [None, 2310.0, -412.3, -286.7]
    assert table["rows"][2]["description"] == "Cumpărături card"
    assert table["closing_balance"] == 26480 and table["closing_evidence"]["bbox"][1] == 680


def test_llm_answer_grounded_and_usage_summed(monkeypatch):
    async def fake_chat(task, *, json_schema=None, **k):
        data = json_schema()
        if json_schema is PayslipFields:
            data = PayslipFields(net_salary=RawField(value="8.500,00", source_text="NET DE PLATĂ 8.500,00"))
        return LLMResponse(text="{}", data=data,
                           usage=LLMUsage(provider="featherless", model="m", input_tokens=100, output_tokens=10,
                                          cost_usd=0.001))

    monkeypatch.setattr(functionar_agent, "chat", fake_chat)
    case, ctx = maria_case(), Ctx(paznic_scratch())
    result = run_agent(case, ctx)

    assert case.documents[1].extracted["net_salary"].source_text == "NET DE PLATĂ 8.500,00"
    assert result.llm_usage.input_tokens == 300 and result.llm_usage.cost_usd == 0.003
    assert "EXTRACTION_RULES_ONLY" not in codes(result)


def test_hallucinated_field_is_dropped_with_finding(monkeypatch):
    async def fake_chat(task, *, json_schema=None, **k):
        data = json_schema()
        if json_schema is PayslipFields:
            data = PayslipFields(personal_deduction=RawField(value="500,00", source_text="Deducere 500,00"),
                                 net_salary=RawField(value="8.307,00", source_text="8.307,00"))
        return LLMResponse(text="{}", data=data, usage=None)

    monkeypatch.setattr(functionar_agent, "chat", fake_chat)
    case = maria_case()
    result = run_agent(case, Ctx(paznic_scratch()))
    slip = case.documents[1]

    assert "personal_deduction" not in slip.extracted
    ungrounded = [f for f in result.findings if f.code == "EXTRACTION_UNGROUNDED"]
    assert [f.evidence.field for f in ungrounded] == ["personal_deduction"]
    assert slip.extracted["net_salary"].value == 8500  # netul „corectat” de LLM e respins; rămâne ce scrie pe document


def test_pii_gate_block_is_reported(monkeypatch):
    async def blocked(*a, **k):
        raise PIIGateBlocked(["CNP"])

    monkeypatch.setattr(functionar_agent, "chat", blocked)
    case = maria_case()
    result = run_agent(case, Ctx(paznic_scratch()))
    assert "PII_GATE_BLOCKED" in codes(result)
    assert case.documents[1].extracted["gross_salary"].value == 14200


def test_without_paznic_output_falls_back_to_fixture(no_llm):
    case = maria_case()
    result = run_agent(case, Ctx({}))
    assert result.agent == "functionar" and case.documents[1].type == "payslip"


def test_unknown_document_without_llm(no_llm):
    case = Case(id="c", created_at="2026-10-28T10:00:00Z", documents=[Document(id="d", filename="x.jpg")])
    words = words_of([(100, [(80, "Factură fiscală nr. 12")])])
    result = run_agent(case, Ctx({"paznic": {"d": {"words": words}}}))
    assert case.documents[0].type == "unknown" and case.documents[0].extracted == {}
    assert result.findings[0].message == "1 document: necunoscut"


def test_grounding_rejects_close_but_different_amount():
    assert find_in_words("14.200,00", PAYSLIP).bbox[1] == 590
    m = find_in_words("14.209,00", PAYSLIP)
    assert m is None or m.text != "14.209,00"
    assert find_in_text("NET DE PLATA 8.500,00", "...\nNET DE PLATĂ 8.500,00\n").score == 1.0
    assert find_in_text("Salariu brut 99.999,99", "NET DE PLATĂ 8.500,00") is None


def test_lines_group_label_and_value_on_same_row():
    lines = group_lines(PAYSLIP)
    assert "Salariu brut 14.200,00" in [line.text for line in lines]
    assert len(parse_statement(group_lines(STATEMENT)).rows) == 4
