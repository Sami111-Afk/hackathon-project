"""Generează shared/fixtures/maria_case.json și maria_events.jsonl (date 100% inventate).
Sunt validate cu modelele din backend → dacă se schimbă contractul, rulați din nou.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import AgentResult, Case, PipelineEvent  # noqa: E402

CASE_ID = "case_maria"
t0 = datetime(2026, 10, 28, 10, 14, 0, tzinfo=timezone.utc)


def ts(sec: float) -> str:
    return (t0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


results = [
    {"agent": "paznic", "status": "done", "duration_ms": 1900, "findings": [
        {"code": "PII_REDACTED", "severity": "info", "message": "23 personal values hidden (name, CNP, IBAN, address, MRZ, photo)"}]},
    {"agent": "functionar", "status": "done", "duration_ms": 2600,
     "llm_usage": {"provider": "featherless", "model": "deepseek-ai/DeepSeek-V4-Flash", "input_tokens": 1820, "output_tokens": 410, "cost_usd": 0.00037},
     "findings": [{"code": "DOCS_CLASSIFIED", "severity": "info", "message": "3 documents: ID card, payslip, statement"}]},
    {"agent": "verificator", "status": "done", "risk": 0.9, "duration_ms": 1840, "findings": [
        {"code": "NET_MISMATCH", "severity": "high", "message": "The computed net (8,307 lei) differs from the declared one (8,500 lei)",
         "evidence": {"doc_id": "doc_2", "page": 1, "bbox": [980, 1310, 1260, 1360], "field": "net_salary"}},
        {"code": "COMPANY_INACTIVE", "severity": "critical", "message": "The employer [CUI_1] has been listed as inactive with ANAF (the tax authority) since 2024"},
        {"code": "AGE_EMPLOYMENT_MISMATCH", "severity": "medium", "message": "67-year-old applicant declared as an active full-time employee"}]},
    {"agent": "detector", "status": "done", "risk": 0.7, "duration_ms": 3100,
     "artifacts": {"ela_image": f"/api/cases/{CASE_ID}/documents/doc_3/image?view=ela"},
     "findings": [
        {"code": "ELA_ANOMALY", "severity": "medium", "message": "The final balance area has a different compression level from the rest of the page",
         "evidence": {"doc_id": "doc_3", "page": 1, "bbox": [1120, 1880, 1480, 1930]}},
        {"code": "PDF_EDITOR_PRODUCER", "severity": "medium", "message": "The document was produced by an image editor, not by a bank's system"}]},
    {"agent": "detectiv", "status": "done", "risk": 0.85, "duration_ms": 420, "findings": [
        {"code": "FRAUD_RING_SUSPECTED", "severity": "critical", "message": "The phone number in this application appears in 5 other applications, under 5 different identities, in the last 3 weeks"}]},
    {"agent": "compliance", "status": "done", "risk": 0.96, "duration_ms": 1500,
     "llm_usage": {"provider": "featherless", "model": "deepseek-ai/DeepSeek-V4-Flash", "input_tokens": 900, "output_tokens": 220, "cost_usd": 0.00019},
     "findings": [{"code": "IDENTITY_FRAUD_LIKELY", "severity": "critical", "message": "Identity theft likely, part of a ring"}]},
]

case = {
    "id": CASE_ID, "source": "bank", "status": "awaiting_review", "created_at": ts(0),
    "requested_amount_ron": 45000, "applicant_token": "[PERSOANA_1]",
    "documents": [
        {"id": "doc_1", "type": "id_card", "filename": "id_card.jpg", "pages": [{"page": 1, "width": 1600, "height": 1010}],
         "redacted_text": "ROMANIA IDENTITY CARD SERIES [SERIE_1] NO [NR_1] CNP [CNP_1] Name [PERSOANA_1] Address [ADRESA_1] [MRZ_1]",
         "extracted": {"birth_date": {"value": "1959-03-12", "source_text": "12.03.1959"}, "series_county": {"value": "PH", "source_text": "PH"}}},
        {"id": "doc_2", "type": "payslip", "filename": "payslip.jpg", "pages": [{"page": 1, "width": 1654, "height": 2339}],
         "redacted_text": "PAYSLIP Employer [FIRMA_1] CUI [CUI_1] Employee [PERSOANA_1] CNP [CNP_1] Position: Accountant Gross 14.200,00 Net 8.500,00",
         "extracted": {"gross_salary": {"value": 14200, "source_text": "14.200,00"}, "net_salary": {"value": 8500, "source_text": "8.500,00"},
                       "employer_cui": {"value": "[CUI_1]", "source_text": "[CUI_1]"}}},
        {"id": "doc_3", "type": "bank_statement", "filename": "bank_statement.pdf", "pages": [{"page": 1, "width": 1654, "height": 2339}],
         "redacted_text": "BANK STATEMENT [IBAN_1] Holder [PERSOANA_1] Opening balance 1.240,50 ... Closing balance 26.480,00",
         "extracted": {"closing_balance": {"value": 26480, "source_text": "26.480,00"}}},
    ],
    "fingerprints": {"phone": ["hm_9c1e"], "iban": ["hm_44ab"], "cnp": ["hm_0f2d"], "address": ["hm_aa71"]},
    "results": results,
    "verdict": {"risk": 0.96, "label": "identity_fraud", "recommendation": "escalate", "incomplete": False,
                "summary": "The payslip does not follow the tax calculation, the employer is inactive, the statement was edited, and the phone number links this application to 5 other identities. Recommendation: rejection and fraud investigation."},
    "decision": None,
}
Case.model_validate(case)

events, seq = [], 0


def ev(sec, type_, agent=None, message="", data=None):
    global seq
    e = {"case_id": CASE_ID, "seq": seq, "ts": ts(sec), "type": type_, "agent": agent, "message": message, "data": data}
    PipelineEvent.model_validate(e)
    events.append(e)
    seq += 1


ev(0, "case_created", message="New application: 3 documents, loan 45,000 lei")
ev(0.2, "agent_started", "paznic", "Hiding personal data")
ev(2.1, "agent_finished", "paznic", "23 personal values hidden", results[0])
ev(2.2, "agent_started", "functionar", "Reading the documents")
ev(4.8, "agent_finished", "functionar", "Payslip, statement, ID card — data extracted", results[1])
for i, (a, msg) in enumerate([("verificator", "Redoing the math (on encrypted data)"), ("detector", "Looking for traces of editing"), ("detectiv", "Comparing with other applications")]):
    ev(4.9 + i * 0.05, "agent_started", a, msg)
ev(5.4, "agent_finished", "detectiv", "Suspicious ring: 6 linked applications", results[4])
ev(6.7, "agent_finished", "verificator", "The math does not add up: difference -193 lei; inactive company", results[2])
ev(8.0, "agent_finished", "detector", "The balance area was edited", results[3])
ev(8.1, "agent_started", "compliance", "Weighing the evidence")
ev(8.6, "debate", "compliance", "The Detector only gave medium risk, but the Verifier and the Detective have critical evidence — escalating.")
ev(9.6, "agent_finished", "compliance", "Risk score 96", results[5])
ev(9.7, "verdict", "compliance", "Identity theft likely — investigation", case["verdict"])

(ROOT / "shared/fixtures/maria_case.json").write_text(json.dumps(case, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(ROOT / "shared/fixtures/maria_events.jsonl").write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
print(f"ok: 1 dosar, {len(events)} evenimente")
