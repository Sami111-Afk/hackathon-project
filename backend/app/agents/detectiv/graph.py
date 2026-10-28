"""Graful Detectivului: noduri = dosare + amprente, muchii = „dosarul folosește amprenta”.

Amprentele sunt HMAC-uri (vezi Paznicul) — aici nu există nicio valoare personală.
Dosarele din Arena nu intră niciodată în graf.
"""
from datetime import UTC, datetime

import networkx as nx

from app.models import Case

# Amprente care, comune între identități diferite, sugerează o rețea.
STRONG_KINDS = {"phone", "iban", "email"}
# Adresa poate fi comună legitim (familie, bloc) → semnal slab, nu extinde clusterul.
WEAK_KINDS = {"address"}
# CNP-ul identifică persoana → nu e „legătură”, e aceeași identitate.
IDENTITY_KINDS = {"cnp"}

KIND_LABEL = {"phone": "telefon", "iban": "cont IBAN", "email": "email", "address": "adresă", "cnp": "CNP"}


def case_node(case_id: str) -> str:
    return f"case:{case_id}"


def fp_node(kind: str, value: str) -> str:
    return f"fp:{kind}:{value}"


def identity_of(case: Case) -> str:
    """Cine e solicitantul: amprenta CNP-ului; fără CNP, amprenta numelui; altfel dosarul e o identitate separată
    (altfel aceeași persoană cu două dosare fără CNP citit ar apărea ca „rețea”)."""
    cnps = sorted(case.fingerprints.get("cnp", []))
    if cnps:
        return "cnp:" + "|".join(cnps)
    names = sorted(case.fingerprints.get("name", []))
    return "name:" + "|".join(names) if names else f"case:{case.id}"


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def bank_cases(cases: list[Case], window_days: float | None = None, now: datetime | None = None) -> list[Case]:
    now = now or datetime.now(UTC)
    out = []
    for c in cases:
        if c.source != "bank":
            continue
        if window_days is not None and (now - parse_ts(c.created_at)).total_seconds() > window_days * 86400:
            continue
        out.append(c)
    return out


def build_graph(cases: list[Case]) -> nx.Graph:
    g = nx.Graph()
    for c in cases:
        risk = c.verdict.risk if c.verdict else None
        g.add_node(case_node(c.id), type="case", case_id=c.id, identity=identity_of(c), created_at=c.created_at,
                   applicant=c.applicant_token, status=c.status, risk=risk, amount=c.requested_amount_ron)
        for kind, values in c.fingerprints.items():
            for v in values:
                n = fp_node(kind, v)
                if n not in g:
                    g.add_node(n, type="fingerprint", kind=kind, value=v)
                g.add_edge(case_node(c.id), n, kind=kind)
    return g


def cluster_of(g: nx.Graph, case_id: str) -> set[str]:
    """Dosarele legate de case_id prin amprente puternice (telefon, IBAN, email), oricât de departe."""
    start = case_node(case_id)
    if start not in g:
        return set()
    seen, stack = {start}, [start]
    while stack:
        node = stack.pop()
        for nb in g.neighbors(node):
            if nb in seen:
                continue
            if g.nodes[nb]["type"] == "fingerprint" and g.nodes[nb]["kind"] not in STRONG_KINDS:
                continue
            # o amprentă folosită de un singur dosar nu leagă nimic
            if g.nodes[nb]["type"] == "fingerprint" and g.degree(nb) < 2:
                continue
            seen.add(nb)
            stack.append(nb)
    return {g.nodes[n]["case_id"] for n in seen if g.nodes[n]["type"] == "case"}


def node_payload(g: nx.Graph, node: str, cluster: set[str], focus: str | None) -> dict:
    a = g.nodes[node]
    if a["type"] == "case":
        return {"id": node, "type": "case", "case_id": a["case_id"], "label": a["applicant"] or a["case_id"],
                "status": a["status"], "risk": a["risk"], "created_at": a["created_at"],
                "in_cluster": a["case_id"] in cluster, "is_focus": a["case_id"] == focus}
    shared = g.degree(node)
    return {"id": node, "type": "fingerprint", "kind": a["kind"], "label": f"{KIND_LABEL.get(a['kind'], a['kind'])}",
            "shared_by": shared, "in_cluster": shared >= 2 and any(
                g.nodes[nb]["case_id"] in cluster for nb in g.neighbors(node))}


def graph_payload(g: nx.Graph, case_id: str | None = None) -> dict:
    """JSON pentru /api/graph și pentru react-force-graph: {nodes, links, cluster}.

    Cu case_id: doar vecinătatea dosarului (clusterul + amprentele lui). Fără: tot graful,
    dar fără amprentele folosite de un singur dosar (zgomot).
    """
    if case_id:
        cluster = cluster_of(g, case_id)
        cases = {case_node(c) for c in cluster} or ({case_node(case_id)} & set(g.nodes))
        keep = set(cases)
        for cn in cases:
            for fp in g.neighbors(cn):
                if g.degree(fp) >= 2 or cn == case_node(case_id):
                    keep.add(fp)
    else:
        cluster = set()
        keep = {n for n in g.nodes if g.nodes[n]["type"] == "case" or g.degree(n) >= 2}
    sub = g.subgraph(keep)
    return {
        "focus": case_id,
        "cluster": sorted(cluster),
        "nodes": [node_payload(g, n, cluster, case_id) for n in sub.nodes],
        "links": [{"source": u if sub.nodes[u]["type"] == "case" else v,
                   "target": v if sub.nodes[u]["type"] == "case" else u,
                   "kind": d["kind"]} for u, v, d in sub.edges(data=True)],
    }
