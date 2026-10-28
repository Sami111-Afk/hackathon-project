import asyncio
import json
import random
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agents.paznic.vault import vault
from app.api.deps import require_bank
from app.arena import attacker
from app.arena import service as arena_service
from app.config import REPO_ROOT, settings
from app.core import audit
from app.core.events import bus, now_iso
from app.core.files import delete_case_files
from app.core.pipeline import start_pipeline
from app.core.store import store
from app.learning import proposer
from app.models import AgentResult, Case, Decision, Document, Finding, Verdict

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_bank)])


@router.post("/rerun-demo")
async def rerun_demo():
    """Pornește din nou dosarul Mariei prin pipeline (cu agenții actuali). Pentru demo și pentru Erin."""
    fixture = json.loads((REPO_ROOT / "shared/fixtures/maria_case.json").read_text(encoding="utf-8"))
    case_id = f"case_maria_{uuid.uuid4().hex[:6]}"
    docs = [Document(id=d["id"], type=d["type"], filename=d["filename"], pages=d.get("pages", []))
            for d in fixture["documents"]]
    case = Case(id=case_id, created_at=now_iso(), requested_amount_ron=fixture["requested_amount_ron"],
                applicant_token=fixture["applicant_token"], fingerprints=fixture["fingerprints"], documents=docs)
    await store.save(case)
    bus.publish(case_id, "case_created", message=f"Dosar nou: {len(docs)} documente, credit 45.000 lei")
    start_pipeline(case)
    return {"case_id": case_id}


RING_NAMES = ["[PERSOANA_A]", "[PERSOANA_B]", "[PERSOANA_C]", "[PERSOANA_D]", "[PERSOANA_E]"]


def _past(days: float) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat(timespec="seconds").replace("+00:00", "Z")


def _seeded(case_id: str, days_ago: float, amount: float, fingerprints: dict, risk: float, label: str,
            rec: str, summary: str, findings: list[tuple[str, str, str, str]], status: str) -> Case:
    results = {}
    for agent, code, sev, msg in findings:
        results.setdefault(agent, []).append(Finding(code=code, severity=sev, message=msg))
    case = Case(id=case_id, created_at=_past(days_ago), requested_amount_ron=amount, status=status,
                applicant_token="[PERSOANA_1]", fingerprints=fingerprints,
                results=[AgentResult(agent=a, status="done", findings=f) for a, f in results.items()],
                verdict=Verdict(risk=risk, label=label, recommendation=rec, summary=summary))
    if status != "awaiting_review":
        case.decision = Decision(action={"cleared": "clear", "rejected": "reject", "escalated": "escalate"}[status],
                                 decided_by="Andrei", decided_at=_past(days_ago - 0.01))
    return case


@router.post("/seed-demo")
async def seed_demo():
    """Istoric realist pentru demo: rețeaua legată de dosarul Mariei + 10 dosare legitime.
    Amprentele (hm_9c1e = telefonul, hm_44ab = IBAN-ul) sunt aceleași ca în dosarul Mariei."""
    rng = random.Random(7)
    created = []
    for i, name in enumerate(RING_NAMES):
        fp = {"phone": ["hm_9c1e"], "cnp": [f"hm_r{i}c{i}"], "address": [f"hm_ra{i}"],
              "iban": ["hm_44ab"] if i in (1, 3) else [f"hm_ri{i}"]}
        st = "escalated" if i < 2 else "awaiting_review"
        case = _seeded(f"case_ring_{i + 1}", days_ago=21 - i * 4, amount=rng.choice([30000, 38000, 45000, 52000]),
                       fingerprints=fp, risk=round(0.82 + i * 0.03, 2), label="fraud_ring",
                       rec="escalate", status=st, summary="Telefonul din cerere apare pe mai multe identități.",
                       findings=[("detectiv", "FRAUD_RING_SUSPECTED", "critical",
                                  f"Telefonul din cerere apare la {i + 1} alte identități"),
                                 ("verificator", "NET_MISMATCH", "high", "Netul nu se potrivește cu brutul")])
        case.applicant_token = name
        created.append(case)
    for i in range(10):
        fp = {"phone": [f"hm_lp{i}"], "cnp": [f"hm_lc{i}"], "iban": [f"hm_li{i}"], "address": [f"hm_la{i}"]}
        created.append(_seeded(f"case_ok_{i + 1}", days_ago=rng.uniform(0.5, 20), amount=rng.choice(
            [12000, 18000, 25000, 40000, 60000]), fingerprints=fp, risk=round(rng.uniform(0.0, 0.2), 2),
            label="clean", rec="clear", status="cleared", findings=[],
            summary="Nicio problemă: dosarul poate merge la analiza normală de credit."))
    for case in created:
        await store.save(case)
        bus.publish(case.id, "verdict", agent="compliance", message=case.verdict.summary,
                    data=case.verdict.model_dump())
    return {"seeded": [c.id for c in created]}


@router.post("/seed-arena")
async def seed_arena():
    """Clasament pre-populat (dacă nu joacă nimeni în primele minute)."""
    tries = [("Echipa-Narcis", {"net_salary": 9500}, []),
             ("Echipa-Erin", {"gross_salary": 16000}, ["recompute_taxes"]),
             ("Echipa-Stefan", {"gross_salary": 16500, "employer": "Agro Prahova Distribuție SRL"},
              ["recompute_taxes"]),
             ("Echipa-Lorena", {"gross_salary": 16000, "employer": "Bitwave Software SRL"},
              ["recompute_taxes", "hide_injection"])]
    out = []
    for nick, edits, tricks in tries:
        out.append(await asyncio.to_thread(arena_service.submit, nick, "payslip_9000", edits, tricks))
    return {"seeded": [(o["nickname"], o["outcome"]) for o in out]}


@router.post("/reset")
def reset():
    if settings.env == "demo":
        raise HTTPException(403, "reset dezactivat în modul demo")
    for case in store.list():
        delete_case_files(case.id)
        vault.forget(case.id)
    vault.reset()
    store.reset()
    bus.reset()
    audit.reset()
    arena_service.reset()
    proposer.reset()
    return {"ok": True}


class AttackIn(BaseModel):
    mission_id: str = "payslip_9000"
    rounds: int = Field(default=6, ge=1, le=15)
    auto_approve: bool = False  # doar pentru demo: regulile intră fără om


@router.post("/attacker/start")
async def attacker_start(body: AttackIn):
    if not attacker.start(body.mission_id, body.rounds, body.auto_approve):
        raise HTTPException(409, "atacatorul rulează deja sau misiunea nu există")
    return attacker.status()


@router.get("/attacker/status")
def attacker_status():
    return attacker.status()
