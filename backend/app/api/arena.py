"""Rute PUBLICE ale Arenei (fără token). Nu ating niciodată dosarele băncii sau seiful."""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.arena import service
from app.arena.missions import public_missions
from app.arena.ratelimit import limit
from app.core.events import bus
from app.learning import proposer

router = APIRouter(prefix="/api/arena", tags=["arena"])


class SubmissionIn(BaseModel):
    nickname: str = Field(max_length=40)
    mission_id: str = Field(max_length=40)
    edits: dict = Field(default_factory=dict)
    tricks: list[str] = Field(default_factory=list, max_length=5)


@router.get("/missions")
def missions():
    return public_missions()


@router.post("/submissions", dependencies=[Depends(limit)])
async def submit(body: SubmissionIn):
    try:
        result = await asyncio.to_thread(service.submit, body.nickname, body.mission_id, body.edits, body.tricks)
    except service.ArenaError as exc:
        raise HTTPException(400, str(exc)) from exc
    service.announce(result)
    if result["outcome"] == "passed" and not result["duplicate"]:
        proposer.on_arena_miss(result["id"])  # self-learning în fundal
    return result


@router.get("/submissions/{sid}")
def submission(sid: str):
    s = service.get(sid)
    if not s:
        raise HTTPException(404, "submission not found")
    return s


@router.get("/submissions/{sid}/image")
def submission_image(sid: str):
    data = service.image(sid)
    if not data:
        raise HTTPException(404, "submission not found")
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


@router.get("/leaderboard")
def leaderboard():
    return {"top": service.leaderboard(), "feed": service.feed()[:15], "stats": service.stats()}


@router.get("/live")
def live(request: Request):
    """SSE pentru ecranul de pe proiector: fiecare trimitere, în timp real."""
    async def gen():
        q = bus.subscribe(service.LIVE_CHANNEL)
        try:
            while True:
                try:
                    e = await asyncio.wait_for(q.get(), timeout=15)
                except TimeoutError:
                    continue
                yield {"event": e.type, "data": e.model_dump_json(exclude_none=True)}
        finally:
            bus.unsubscribe(q, service.LIVE_CHANNEL)

    return EventSourceResponse(gen(), ping=15, headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})
