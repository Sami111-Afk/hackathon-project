"""🕵️ Detectiv — Erin. Leagă dosarul de alte cereri prin amprente comune și găsește rețele.

Semnale (doar între identități DIFERITE — același CNP nu e o rețea, e un client care revine):
- telefon / email comun: 1 altă identitate → medium (poate fi familia); 2 → high; ≥3 → critical (rețea)
- cont IBAN comun cu altă identitate → high (banii ajung în același loc)
- adresă comună cu ≥3 identități → medium
Rulează pe CPU, fără LLM. Riscul = noisy-OR pe gravitatea finding-urilor (ca în Compliance).
"""
import asyncio
from collections import defaultdict
from datetime import UTC, datetime

from app.agents.detectiv.graph import (
    STRONG_KINDS,
    bank_cases,
    build_graph,
    case_node,
    fp_node,
    graph_payload,
    identity_of,
    parse_ts,
)
from app.config import settings
from app.core.store import store
from app.models import AgentResult, Case, Finding

WINDOW_DAYS = 90
SEVERITY_WEIGHT = {"info": 0.0, "low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.85}
MAX_LIVE_LINKS = 12  # câte legături animăm live în frontend


def _since(oldest: datetime, now: datetime) -> str:
    days = max(1, round((now - oldest).total_seconds() / 86400))
    if days <= 1:
        return "în ultima zi"
    if days < 7:
        return f"în ultimele {days} zile"
    weeks = round(days / 7)
    return "în ultima săptămână" if weeks <= 1 else f"în ultimele {weeks} săptămâni"


def analyze(case: Case, others: list[Case], now: datetime | None = None) -> tuple[list[Finding], dict]:
    """Funcție pură: dosarul + celelalte dosare ale băncii → finding-uri + statistici. Ușor de testat."""
    now = now or datetime.now(UTC)
    me = identity_of(case)
    # amprentă → dosarele (altor identități) care o folosesc
    users: dict[tuple[str, str], list[Case]] = defaultdict(list)
    index: dict[tuple[str, str], list[Case]] = defaultdict(list)
    for o in others:
        if o.id == case.id or identity_of(o) == me:
            continue
        for kind, values in o.fingerprints.items():
            for v in values:
                index[(kind, v)].append(o)
    for kind, values in case.fingerprints.items():
        for v in values:
            if (kind, v) in index:
                users[(kind, v)] = index[(kind, v)]

    findings: list[Finding] = []
    for (kind, _v), linked in sorted(users.items(), key=lambda kv: -len(kv[1])):
        identities = {identity_of(c) for c in linked}
        k, n = len(identities), len(linked)
        when = _since(min(parse_ts(c.created_at) for c in linked), now)
        cereri = "o altă cerere" if n == 1 else f"alte {n} cereri"
        if kind in ("phone", "email"):
            what = "Telefonul" if kind == "phone" else "Adresa de email"
            if k >= 2:
                findings.append(Finding(
                    code="FRAUD_RING_SUSPECTED", severity="critical" if k >= 3 else "high",
                    message=f"{what} din cerere apare în {cereri}, pe {k} identități diferite, {when}"))
            else:
                findings.append(Finding(
                    code="SHARED_CONTACT", severity="medium",
                    message=f"{what} din cerere apare și la o altă persoană ({when}) — poate fi un membru al familiei"))
        elif kind == "iban":
            findings.append(Finding(
                code="SHARED_IBAN", severity="high",
                message=f"Contul IBAN din cerere apare în {cereri}, pe "
                        f"{'o altă identitate' if k == 1 else f'{k} identități diferite'}, {when}"))
        elif kind == "address" and k >= 3:
            findings.append(Finding(
                code="SHARED_ADDRESS", severity="medium",
                message=f"Adresa din cerere apare la {k} persoane diferite, {when}"))

    # doar legăturile care pot forma o rețea (un coleg cu același angajator nu pornește animația grafului)
    strong = [c for (kind, _v), cs in users.items() if kind in STRONG_KINDS for c in cs]
    stats = {"linked_cases": len({c.id for c in strong}),
             "linked_identities": len({identity_of(c) for c in strong})}
    return findings, stats


def noisy_or(findings: list[Finding]) -> float:
    keep = 1.0
    for f in findings:
        keep *= 1 - SEVERITY_WEIGHT[f.severity]
    return round(1 - keep, 4)


class Detectiv:
    name = "detectiv"
    start_message = "Compar cu alte dosare"

    async def run(self, case: Case, ctx) -> AgentResult:
        now = datetime.now(UTC)
        pool = bank_cases(store.list(), window_days=WINDOW_DAYS, now=now)
        if case.source == "arena":  # Arena nu are voie să vadă dosarele băncii
            pool = []
        others = [c for c in pool if c.id != case.id]
        findings, stats = await asyncio.to_thread(analyze, case, others, now)

        # Animație live: trimitem graful bucată cu bucată (doar etichete + amprente HMAC, fără date personale).
        if case.source == "bank" and stats["linked_cases"]:
            g = await asyncio.to_thread(build_graph, [case, *others])
            await self._stream(ctx, g, case)

        if not findings:
            findings = [Finding(code="NO_LINKS", severity="info",
                                message=f"Nicio legătură cu alte {len(others)} dosare din ultimele {WINDOW_DAYS} zile")]
        return AgentResult(agent=self.name, status="done", risk=noisy_or(findings), findings=findings,
                           artifacts={"graph": f"/api/graph?case_id={case.id}"})

    async def _stream(self, ctx, g, case: Case) -> None:
        payload = graph_payload(g, case.id)
        focus = case_node(case.id)
        nodes = {n["id"]: n for n in payload["nodes"]}
        # întâi dosarul + amprentele lui, apoi fiecare dosar legat cu muchiile lui
        first = [nodes[focus]] + [nodes[fp_node(k, v)] for k, vs in case.fingerprints.items() for v in vs
                                  if fp_node(k, v) in nodes]
        sent = {n["id"] for n in first}
        await ctx.emit("agent_progress", "Construiesc graful", data={"graph_delta": {
            "nodes": first, "links": [lk for lk in payload["links"] if lk["source"] == focus]}})
        delay = 0 if settings.env == "test" else 0.15
        others = [n for n in payload["nodes"] if n["type"] == "case" and n["id"] != focus]
        others.sort(key=lambda n: (not n["in_cluster"], n["created_at"] or ""))
        live, rest = others[:MAX_LIVE_LINKS], others[MAX_LIVE_LINKS:]
        for cn in live:
            links = [lk for lk in payload["links"] if lk["source"] == cn["id"]]
            new_nodes = [cn] + [nodes[lk["target"]] for lk in links if lk["target"] not in sent]
            sent.update(n["id"] for n in new_nodes)
            await asyncio.sleep(delay)
            await ctx.emit("agent_progress", f"Legătură găsită: {cn['label']}",
                           data={"graph_delta": {"nodes": new_nodes, "links": links}})
        if rest:  # restul, dintr-o bucată
            rest_ids = {n["id"] for n in rest}
            links = [lk for lk in payload["links"] if lk["source"] in rest_ids]
            new_nodes = rest + [nodes[t] for t in {lk["target"] for lk in links} if t not in sent]
            await ctx.emit("agent_progress", f"Încă {len(rest)} dosare legate",
                           data={"graph_delta": {"nodes": new_nodes, "links": links}})
