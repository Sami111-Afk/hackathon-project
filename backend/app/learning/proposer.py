"""🧠 Self-learning — Samuel. Un fals a trecut → Claude Opus propune reguli → validare → backtest → om.

LLM-ul NU scrie cod: propune reguli JSON într-un limbaj restrâns (learning/engine.py).
O regulă e respinsă automat dacă:
  - folosește câmpuri/operatori care nu există;
  - nu prinde falsul care a declanșat-o;
  - prinde vreun fluturaș legitim (fals pozitiv) din setul de verificare.
"""
import asyncio
import logging
import threading
import uuid
from datetime import date, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.arena import service as arena
from app.arena.forge import net_from_gross
from app.arena.missions import COMPANIES
from app.core.events import bus, now_iso
from app.core.llm import chat
from app.learning import engine

log = logging.getLogger("orb.learning")

FIELDS = {
    "doc.gross_salary": "number, gross salary (lei)",
    "doc.net_salary": "number, net salary (lei)",
    "doc.employer": "text, numele angajatorului",
    "doc.job_title": "text, job title",
    "doc.issue_date": "ISO date, issue date",
    "company.active": "bool, company is active at ANAF",
    "company.founded": "ISO date, founding date",
    "company.employees": "number of declared employees",
    "company.median_gross": "median gross salary in the company (lei)",
    "company.role_median": "median gross at the company for the document job title (lei; missing = no such title)",
}

SYSTEM = (
    "You are a fraud analyst at a bank. A FORGED payslip passed all checks. "
    "Propose 1-3 general rules that would have caught it but do NOT catch legitimate payslips. "
    "Rules are JSON in a restricted language: conditions {left, op, right} combined with all/any/not. "
    "`left` is a field from the catalog; `right` is a value or another catalog field, or a list [field, number] "
    "for abs_diff_gt / ratio_gt (e.g. {\"left\":\"doc.gross_salary\",\"op\":\"ratio_gt\","
    "\"right\":[\"company.median_gross\",2.0]} = gross > 2 × the median). "
    "Do not use fixed amount thresholds if you can compare against the company data. "
    "Keep descriptions and messages in English, short."
)


class Then(BaseModel):
    code: str = Field(pattern=r"^[A-Z0-9_]{3,40}$")
    severity: Literal["medium", "high", "critical"]
    message: str = Field(max_length=160)


class ProposedRule(BaseModel):
    description: str = Field(max_length=200)
    when: dict[str, Any]
    then: Then


class Proposal(BaseModel):
    reasoning: str = Field(max_length=600)
    rules: list[ProposedRule] = Field(min_length=1, max_length=3)


_lock = threading.Lock()
PROPOSED: list[dict] = []
_tasks: set[asyncio.Task] = set()


def legit_dataset() -> list[dict]:
    """Fluturași legitimi (sintetici) pentru backtest: salarii plauzibile, firme active, date valide."""
    docs = []
    for name, c in COMPANIES.items():
        if not c["active"]:
            continue
        for role, median in c["role_medians"].items():
            for factor in (0.6, 0.8, 1.0, 1.2, 1.5):
                gross = round(median * factor / 50) * 50
                if c["employees"] < 50 and gross > 2.5 * c["median_gross"]:
                    continue  # ar fi prins deja de verificările existente
                for days_ago in (1, 17, 29, 46, 75, 120):
                    issued = date(2026, 10, 1) - timedelta(days=days_ago)
                    if issued < c["founded"]:
                        continue
                    docs.append({"employee": "[PERSOANA_X]", "employer": name, "job_title": role,
                                 "gross_salary": gross, "net_salary": net_from_gross(gross, issued.isoformat()[:7]),
                                 "issue_date": issued.isoformat(), "tricks": []})
    return docs


def _fields_in(cond: dict) -> set[str]:
    if "all" in cond or "any" in cond:
        return set().union(*(_fields_in(c) for c in cond.get("all", cond.get("any", []))))
    if "not" in cond:
        return _fields_in(cond["not"])
    out = {cond.get("left")}
    right = cond.get("right", cond.get("value"))
    for r in right if isinstance(right, list) else [right]:
        if isinstance(r, str) and r.split(".")[0] in ("doc", "company"):
            out.add(r)
    return out


def _valid_ops(cond: dict) -> bool:
    if "all" in cond or "any" in cond:
        items = cond.get("all", cond.get("any"))
        return isinstance(items, list) and bool(items) and all(_valid_ops(c) for c in items)
    if "not" in cond:
        return isinstance(cond["not"], dict) and _valid_ops(cond["not"])
    return cond.get("op") in engine.OPS and isinstance(cond.get("left"), str)


def _overfit(cond: dict, trigger_doc: dict) -> bool:
    """Regulă care compară exact cu o valoare literală din falsul declanșator (ex. data emiterii == 2026-09-30)."""
    if "all" in cond or "any" in cond:
        return any(_overfit(c, trigger_doc) for c in cond.get("all", cond.get("any", [])))
    if "not" in cond:
        return _overfit(cond["not"], trigger_doc)
    if cond.get("op") not in ("eq", "in"):
        return False
    field = str(cond.get("left", ""))
    if not field.startswith("doc."):
        return False
    value = trigger_doc.get(field[4:])
    right = cond.get("right", cond.get("value"))
    return right == value or (isinstance(right, list) and value in right)


def vet(rule: dict, trigger_doc: dict, legit: list[dict]) -> tuple[bool, str, dict]:
    try:
        return _vet(rule, trigger_doc, legit)
    except Exception as exc:  # noqa: BLE001 — o regulă stricată e respinsă, nu oprește restul
        return False, f"invalid rule ({type(exc).__name__})", {}


def _vet(rule: dict, trigger_doc: dict, legit: list[dict]) -> tuple[bool, str, dict]:
    if not isinstance(rule.get("when"), dict) or not _valid_ops(rule["when"]):
        return False, "invalid operator or structure", {}
    unknown = _fields_in(rule["when"]) - set(FIELDS)
    if unknown:
        return False, f"unknown fields: {sorted(unknown)}", {}
    if _overfit(rule["when"], trigger_doc):
        return False, "too specific (compares with an exact value from the forgery)", {}
    probe = {**rule, "status": "approved"}
    catches_trigger = bool(engine.apply_rules(trigger_doc, [probe]))
    fps = sum(bool(engine.apply_rules(d, [probe])) for d in legit)
    bt = {"cases": len(legit) + 1, "true_positives": int(catches_trigger), "false_positives": fps,
          "fp_rate": round(fps / max(len(legit), 1), 4)}
    if not catches_trigger:
        return False, "does not catch the forgery that triggered it", bt
    if fps:
        return False, f"flags {fps} legitimate payslips", bt
    return True, "ok", bt


async def propose_for(submission_id: str, doc: dict) -> list[dict]:
    legit = legit_dataset()
    company = {k: v for k, v in COMPANIES.get(doc["employer"], {}).items() if k != "role_medians"}
    company["role_median"] = COMPANIES.get(doc["employer"], {}).get("role_medians", {}).get(doc["job_title"])
    prompt = (
        f"Falsul care a trecut:\n{ {k: v for k, v in doc.items() if k != 'employee'} }\n"
        f"Datele firmei din registru: {company}\n"
        f"Existing checks (already applied): net matches gross; the company exists and is active; "
        f"the date is after the founding and not in the future; gross > 2.5×median at companies under 50 employees.\n"
        f"Field catalog: {FIELDS}\nOperators: {sorted(engine.OPS)}\n"
        f"The legitimate set has {len(legit)} payslips, with gross between 0.6× and 1.5× "
        f"the median for their job title."
    )
    r = await chat("learn", case_id=None, system=SYSTEM, prompt=prompt, json_schema=Proposal,
                   cache_key=f"learn|{doc['employer']}|{doc['gross_salary']}|{doc['issue_date']}", max_tokens=6000)
    out = []
    for p in r.data.rules:
        rule = {"id": f"rule_{uuid.uuid4().hex[:6]}", "description": p.description, "applies_to": ["payslip"],
                "when": p.when, "then": p.then.model_dump(), "created_at": now_iso(),
                "origin": {"type": "arena", "submission_id": submission_id, "created_by": "llm",
                           "model": r.usage.model if r.usage else None}}
        ok, why, bt = vet(rule, doc, legit)
        rule.update(status="proposed" if ok else "rejected", backtest=bt, vetting=why)
        out.append(rule)
        with _lock:
            PROPOSED.append(rule)
        bus.publish(arena.LIVE_CHANNEL, "rule_proposed",
                    message=f"New rule proposed: {rule['description']}" if ok
                    else f"Rule automatically rejected ({why})", data=rule)
    return out


def on_arena_miss(submission_id: str) -> None:
    """Apelat din Arena când un fals trece. Rulează în fundal, nu blochează jucătorul."""
    sub = arena._submissions.get(submission_id)
    if not sub:
        return

    async def job():
        try:
            await propose_for(submission_id, sub["doc"])
        except Exception as exc:  # noqa: BLE001
            log.warning("self-learning a eșuat pentru %s: %s", submission_id, type(exc).__name__)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # apelat din thread fără loop (ex. teste sincrone) — se poate porni manual
    task = loop.create_task(job())
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


def decide(rule_id: str, approve: bool, decided_by: str) -> dict | None:
    with _lock:
        rule = next((r for r in PROPOSED if r["id"] == rule_id), None)
        if not rule or rule["status"] != "proposed":
            return None
        rule["status"] = "approved" if approve else "rejected"
        rule["decided_by"] = decided_by
    if approve:
        engine.add_rule(rule)
        bus.publish(arena.LIVE_CHANNEL, "rule_approved",
                    message=f"Rule #{len(engine.RULES)} takes effect: {rule['description']}", data=rule)
    return rule


def reset() -> None:
    with _lock:
        PROPOSED.clear()
    engine.clear()
