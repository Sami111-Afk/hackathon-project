"""😈 Atacatorul — Samuel. Fuzzer automat care joacă în Arena, rundă după rundă.

Nu e un LLM: e o căutare ghidată de feedback. După fiecare încercare citește
DE CE a fost prins (codurile dovezilor) și evită data viitoare ce l-a dat de gol:
  NET_MISMATCH        → recalculează taxele
  COMPANY_* / DOC_*   → schimbă firma / data
  SALARY_IMPLAUSIBLE  → firmă mai mare
  reguli învățate     → schimbă funcția / coboară salariul spre limită
Când trece, self-learning-ul (Claude Opus) propune o regulă; cu `auto_approve` (doar demo)
regula intră imediat, iar atacatorul trebuie să se adapteze. Pe proiector: AI atacator vs AI apărător.
"""
import asyncio
import logging
import random

from app.arena import service
from app.arena.missions import COMPANIES, MISSIONS
from app.config import settings
from app.core.events import bus

log = logging.getLogger("orb.attacker")
NICK = "AI-Atacator"


class State:
    running = False
    rounds: list[dict] = []
    task: asyncio.Task | None = None


state = State()


def status() -> dict:
    done = state.rounds
    return {"running": state.running, "rounds": done,
            "passed": sum(r["outcome"] == "passed" for r in done),
            "caught": sum(r["outcome"] == "caught" for r in done)}


def next_attempt(mission: dict, history: list[dict], rng: random.Random) -> tuple[dict, list[str], str]:
    """Alege următoarea încercare pe baza a ceea ce l-a dat de gol până acum."""
    target = mission["target"]["min"]
    blocked = set().union(*(set(h["codes"]) for h in history)) if history else set()
    tried = {(h["edits"].get("employer"), h["edits"].get("job_title"), h["edits"].get("gross_salary"))
             for h in history}

    tricks, why = [], []
    if not history:
        return {"net_salary": target + 500}, [], "Prima încercare: schimb doar netul și văd ce se întâmplă."
    tricks.append("recompute_taxes")
    if "NET_MISMATCH" in blocked:
        why.append("netul nu se potrivea cu brutul → recalculez taxele")
    min_gross = int(target / 0.585) + 50

    companies = [n for n, c in COMPANIES.items() if c["active"]]
    if blocked & {"COMPANY_INACTIVE", "COMPANY_NOT_FOUND"}:
        why.append("firma era inactivă → aleg una activă")
    if "SALARY_IMPLAUSIBLE" in blocked:
        companies = [n for n in companies if COMPANIES[n]["employees"] >= 50] or companies
        why.append("salariul era nerealist pentru o firmă mică → aleg o firmă mare")
    learned = {c for c in blocked if c not in {"NET_MISMATCH", "COMPANY_INACTIVE", "COMPANY_NOT_FOUND",
                                               "SALARY_IMPLAUSIBLE", "DOC_BEFORE_COMPANY", "DOC_FUTURE_DATE"}}
    candidates = []
    for name in companies:
        for role, median in COMPANIES[name]["role_medians"].items():
            for factor in (1.0, 1.15, 1.3, 1.6, 2.2, 3.0):
                gross = max(min_gross, round(median * factor / 100) * 100)
                if (name, role, gross) in tried:
                    continue
                # cu reguli învățate în joc, preferă salarii apropiate de medianul funcției
                penalty = (gross / median) if learned else 0
                candidates.append((penalty + rng.random() * 0.3, name, role, gross))
    if learned:
        why.append(f"a apărut o regulă nouă ({', '.join(sorted(learned))}) → caut o funcție unde salariul pare normal")
    if not candidates:
        return {"gross_salary": min_gross}, tricks, "Am epuizat combinațiile."
    _, name, role, gross = min(candidates)
    company = COMPANIES[name]
    date_ok = max(company["founded"].isoformat(), "2026-09-30")
    edits = {"gross_salary": gross, "employer": name, "job_title": role, "issue_date": date_ok}
    return edits, tricks, ("; ".join(why) or "încerc o combinație nouă") + f" → {role} la {name}, brut {gross}"


async def run(mission_id: str, rounds: int, auto_approve: bool, seed: int | None) -> None:
    from app.learning import proposer

    mission = MISSIONS[mission_id]
    rng = random.Random(seed)
    state.rounds = []
    history: list[dict] = []
    try:
        for n in range(1, rounds + 1):
            edits, tricks, thinking = next_attempt(mission, history, rng)
            try:
                result = await asyncio.to_thread(service.submit, NICK, mission_id, edits, tricks)
            except service.ArenaError as exc:
                result = {"outcome": "invalid", "reasons": [str(exc)], "id": None, "duplicate": False}
            codes = [f.code for r in service.last_results(result.get("id")) for f in r.findings]
            history.append({"edits": edits, "codes": codes})
            state.rounds.append({"round": n, "edits": edits, "tricks": tricks, "thinking": thinking,
                                 "outcome": result["outcome"], "reasons": result["reasons"]})
            bus.publish(service.LIVE_CHANNEL, "agent_progress",
                        message=f"😈 Runda {n}: {result['outcome']} — {thinking[:140]}",
                        data={"attacker": status()})
            if result["outcome"] == "passed" and result.get("id") and not result["duplicate"]:
                sub = service._submissions[result["id"]]
                try:
                    rules = await proposer.propose_for(result["id"], sub["doc"])
                except Exception as exc:  # noqa: BLE001
                    log.warning("self-learning a eșuat: %s", type(exc).__name__)
                    rules = []
                if auto_approve:
                    for rule in rules:
                        if rule["status"] == "proposed":
                            proposer.decide(rule["id"], True, "auto (demo)")
            await asyncio.sleep(0 if settings.env == "test" else 0.8)  # ritm vizibil pe proiector
    finally:
        state.running = False


def start(mission_id: str, rounds: int, auto_approve: bool, seed: int | None = None) -> bool:
    """Trebuie apelat din cod async (rută `async def`)."""
    if state.running or mission_id not in MISSIONS:
        return False
    loop = asyncio.get_running_loop()
    state.running = True
    state.task = loop.create_task(run(mission_id, rounds, auto_approve, seed))
    return True
