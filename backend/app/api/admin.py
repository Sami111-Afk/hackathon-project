import json

from fastapi import APIRouter, Depends

from app.api.deps import require_bank
from app.config import REPO_ROOT
from app.core.events import bus, now_iso
from app.core.pipeline import start_pipeline
from app.core.store import store
from app.models import Case, Document

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_bank)])


@router.post("/rerun-demo")
async def rerun_demo():
    """Pornește din nou dosarul Mariei prin pipeline (cu agenții actuali). Pentru demo și pentru Erin."""
    fixture = json.loads((REPO_ROOT / "shared/fixtures/maria_case.json").read_text(encoding="utf-8"))
    case_id = f"case_maria_{now_iso()[11:19].replace(':', '')}"
    docs = [Document(id=d["id"], type=d["type"], filename=d["filename"], pages=d.get("pages", []))
            for d in fixture["documents"]]
    case = Case(id=case_id, created_at=now_iso(), requested_amount_ron=fixture["requested_amount_ron"],
                applicant_token=fixture["applicant_token"], fingerprints=fixture["fingerprints"], documents=docs)
    await store.save(case)
    bus.publish(case_id, "case_created", message=f"Dosar nou: {len(docs)} documente, credit 45.000 lei")
    start_pipeline(case)
    return {"case_id": case_id}


@router.post("/reset")
def reset():
    store.reset()
    bus.reset()
    return {"ok": True}
