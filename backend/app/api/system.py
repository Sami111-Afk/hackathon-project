from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_bank
from app.config import settings
from app.core.store import store

router = APIRouter(prefix="/api", dependencies=[Depends(require_bank)])


class SettingsIn(BaseModel):
    llm_mode: Literal["bedrock", "cloud", "local", "mock"] | None = None
    he_enabled: bool | None = None


@router.get("/settings")
def get_settings():
    return {"llm_mode": settings.llm_mode, "he_enabled": settings.he_enabled}


@router.post("/settings")
def set_settings(body: SettingsIn):
    """Butoanele din UI (ex. „mod 100% local”). Se schimbă live, fără restart."""
    if body.llm_mode is not None:
        settings.llm_mode = body.llm_mode
    if body.he_enabled is not None:
        settings.he_enabled = body.he_enabled
    return get_settings()


@router.get("/dashboard/stats")
def dashboard_stats():
    cases = [c for c in store.list() if c.source == "bank"]
    done = [c for c in cases if c.verdict]
    fraud = [c for c in done if c.verdict.label in {"identity_fraud", "fraud_ring", "forged"}]
    saved_min = len(done) * (settings.manual_minutes_per_case - settings.review_minutes_per_case)
    cost = sum(r.llm_usage.cost_usd for c in cases for r in c.results if r.llm_usage)
    return {
        "cases_processed": len(done),
        "hours_saved": round(saved_min / 60, 1),
        "money_saved_ron": round(saved_min / 60 * settings.cost_per_hour_ron),
        "frauds_stopped": len(fraud),
        "amount_stopped_ron": sum(c.requested_amount_ron or 0 for c in fraud),
        "ai_cost_usd": round(cost, 4),
        "assumptions": {"manual_minutes_per_case": settings.manual_minutes_per_case,
                        "review_minutes_per_case": settings.review_minutes_per_case,
                        "cost_per_hour_ron": settings.cost_per_hour_ron},
    }
