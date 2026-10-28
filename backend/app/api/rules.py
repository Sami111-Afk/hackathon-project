from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import require_bank
from app.arena import service as arena
from app.learning import proposer

router = APIRouter(prefix="/api/rules", dependencies=[Depends(require_bank)])


class DecideIn(BaseModel):
    decided_by: str = Field(min_length=1, max_length=60)


@router.get("")
def list_rules():
    return {"rules": proposer.PROPOSED[::-1], "active": len(proposer.engine.RULES),
            "pending_misses": len(arena.pending_misses())}


@router.post("/{rule_id}/approve")
def approve(rule_id: str, body: DecideIn):
    rule = proposer.decide(rule_id, True, body.decided_by)
    if not rule:
        raise HTTPException(404, "regulă inexistentă sau deja decisă")
    return rule


@router.post("/{rule_id}/reject")
def reject(rule_id: str, body: DecideIn):
    rule = proposer.decide(rule_id, False, body.decided_by)
    if not rule:
        raise HTTPException(404, "regulă inexistentă sau deja decisă")
    return rule


@router.post("/learn/{submission_id}")
async def learn_now(submission_id: str):
    """Pornește manual propunerea de reguli pentru un fals din Arena (util la demo)."""
    sub = arena._submissions.get(submission_id)
    if not sub or sub["outcome"] != "passed":
        raise HTTPException(404, "nu e un fals care a trecut")
    return await proposer.propose_for(submission_id, sub["doc"])
