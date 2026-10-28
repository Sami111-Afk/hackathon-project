import asyncio
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.agents.compliance import report
from app.api.deps import require_bank
from app.config import settings
from app.core.events import bus, now_iso
from app.core.files import load_decrypted, load_derived, render_pages, save_encrypted, sniff, to_png
from app.core.pipeline import start_pipeline
from app.core.store import store
from app.models import Case, Decision, Document

router = APIRouter(prefix="/api", dependencies=[Depends(require_bank)])

MAX_FILES = 5
DECISION_STATUS = {"clear": "cleared", "reject": "rejected", "escalate": "escalated",
                   "flag_network": "escalated", "correct": "awaiting_review"}


@router.post("/cases")
async def create_case(files: list[UploadFile] = File(...),
                      requested_amount_ron: float | None = Form(default=None)):
    if not 1 <= len(files) <= MAX_FILES:
        raise HTTPException(400, f"între 1 și {MAX_FILES} fișiere")
    case_id = f"case_{uuid.uuid4().hex[:8]}"
    max_bytes = settings.arena_max_file_mb * 1024 * 1024
    documents, originals = [], {}
    for i, f in enumerate(files, start=1):  # 1. validăm toate fișierele
        data = await f.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise HTTPException(413, f"fișier prea mare (max {settings.arena_max_file_mb} MB)")
        kind = sniff(data)
        if not kind:
            raise HTTPException(415, "doar PNG, JPG sau PDF")
        doc_id = f"doc_{i}"
        originals[doc_id] = data
        documents.append(Document(id=doc_id, filename=f"document_{i}.{kind[0]}"))

    for doc_id, data in originals.items():  # 2. abia apoi le salvăm
        save_encrypted(case_id, doc_id, data)
    case = Case(id=case_id, created_at=now_iso(), requested_amount_ron=requested_amount_ron, documents=documents)
    await store.save(case)
    bus.publish(case_id, "case_created", message=f"Dosar nou: {len(documents)} documente")
    start_pipeline(case, originals)
    return {"case_id": case_id}


@router.get("/cases")
def list_cases(status: str | None = None, source: str = "bank"):
    cases = [c for c in store.list() if c.source == source and (status is None or c.status == status)]
    return [{"id": c.id, "status": c.status, "created_at": c.created_at,
             "requested_amount_ron": c.requested_amount_ron,
             "risk": c.verdict.risk if c.verdict else None,
             "recommendation": c.verdict.recommendation if c.verdict else None} for c in cases]


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    case = store.get(case_id)
    if not case:
        raise HTTPException(404, "dosar inexistent")
    return case.model_dump(exclude_none=True)


@router.get("/cases/{case_id}/report")
def case_report(case_id: str):
    """Raport de anchetă HTML (din browser: „Salvează ca PDF”)."""
    case = store.get(case_id)
    if not case:
        raise HTTPException(404, "dosar inexistent")
    return HTMLResponse(report.render(case), headers={"Cache-Control": "no-store"})


@router.get("/cases/{case_id}/documents/{doc_id}/image")
async def get_image(case_id: str, doc_id: str, view: str = "original", page: int = 1):
    """view=original | redacted (Paznic) | ela (Detector). PDF-urile se întorc randate ca PNG, pagina `page`."""
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if not store.get(case_id):
        raise HTTPException(404, "dosar inexistent")
    try:
        if view != "original":
            png = load_derived(case_id, doc_id, view, page)
            if not png:
                raise HTTPException(404, f"vederea '{view}' nu există (încă) pentru acest document")
            return Response(png, media_type="image/png", headers=headers)
        data = load_decrypted(case_id, doc_id)
    except ValueError:
        data = None
    if not data:
        raise HTTPException(404, "document inexistent")
    if sniff(data)[0] == "pdf":
        pages = await asyncio.to_thread(render_pages, data)
        if not 1 <= page <= len(pages):
            raise HTTPException(404, "pagină inexistentă")
        return Response(await asyncio.to_thread(to_png, pages[page - 1]), media_type="image/png", headers=headers)
    return Response(data, media_type=sniff(data)[1], headers=headers)


class DecisionIn(BaseModel):
    action: str
    decided_by: str = Field(max_length=60)
    notes: str = Field(default="", max_length=2000)
    corrections: dict = Field(default_factory=dict)


@router.post("/cases/{case_id}/decision")
async def decide(case_id: str, body: DecisionIn):
    case = store.get(case_id)
    if not case:
        raise HTTPException(404, "dosar inexistent")
    if case.status in ("received", "processing"):
        raise HTTPException(409, "dosarul încă e în lucru")
    if body.action not in DECISION_STATUS:
        raise HTTPException(400, "acțiune necunoscută")
    if not body.decided_by.strip():
        raise HTTPException(400, "decided_by e obligatoriu")
    if body.action == "clear" and case.verdict and case.verdict.recommendation == "escalate" \
            and len(body.notes.strip()) < 10:
        raise HTTPException(422, "aprobarea unui dosar marcat pentru investigație cere un motiv scris")
    case.decision = Decision(action=body.action, decided_by=body.decided_by.strip()[:60], notes=body.notes,
                             corrections=body.corrections, decided_at=now_iso())
    case.status = DECISION_STATUS[body.action]
    await store.save(case)
    bus.publish(case_id, "decision", message=f"{case.decision.decided_by}: {body.action}",
                data=case.decision.model_dump())
    # TODO (Samuel, P1): action == "correct" → self-learning propune o regulă
    return {**case.decision.model_dump(), "status": case.status}  # frontend-ul așteaptă Decision


def _sse(case_id: str | None, request: Request):
    last = request.headers.get("last-event-id")
    after = int(last) if last and last.isdigit() else -1

    async def gen():
        q = bus.subscribe(case_id)
        try:
            if case_id is not None:
                for e in bus.history(case_id, after):
                    yield {"id": str(e.seq), "event": e.type, "data": e.model_dump_json(exclude_none=True)}
            while True:
                try:
                    e = await asyncio.wait_for(q.get(), timeout=15)
                except TimeoutError:
                    continue  # sse-starlette trimite ping-ul
                yield {"id": str(e.seq) if case_id else None, "event": e.type,
                       "data": e.model_dump_json(exclude_none=True)}
        finally:
            bus.unsubscribe(q, case_id)

    return EventSourceResponse(gen(), ping=15, headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


@router.get("/cases/{case_id}/events")
def case_events(case_id: str, request: Request):
    if not store.get(case_id):
        raise HTTPException(404, "dosar inexistent")
    return _sse(case_id, request)


@router.get("/events")
def global_events(request: Request):
    return _sse(None, request)
