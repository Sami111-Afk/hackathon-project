"""/api/graph — graful Detectivului pentru frontend (react-force-graph)."""
from fastapi import APIRouter, Depends, HTTPException

from app.agents.detectiv.graph import bank_cases, build_graph, graph_payload
from app.api.deps import require_bank
from app.core.store import store

router = APIRouter(prefix="/api", dependencies=[Depends(require_bank)])


@router.get("/graph")
def get_graph(case_id: str | None = None):
    if case_id and not store.get(case_id):
        raise HTTPException(404, "application not found")
    return graph_payload(build_graph(bank_cases(store.list())), case_id)
