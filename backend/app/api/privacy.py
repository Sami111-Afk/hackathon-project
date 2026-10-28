"""Dovezile de confidențialitate ale unui dosar, adunate într-un loc pentru UI și pitch.

Nu decriptează nimic: arată ce e pe disc (criptat), ce a primit AI-ul (redactat + audit),
ce a calculat verificatorul HE (pe ciphertext) și rezultatul ZK, dacă există.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.agents.paznic.detect import find_prompt_injection
from app.agents.paznic.vault import vault
from app.api.deps import require_bank
from app.core import audit
from app.core.files import UPLOAD_DIR, _safe
from app.core.store import store
from app.zk import bank as zk_bank

router = APIRouter(prefix="/api/cases", dependencies=[Depends(require_bank)])

SAMPLE = 48


def _sample(blob: bytes) -> str:
    return blob[:SAMPLE].decode("ascii", "replace") + "…"


@router.get("/{case_id}/privacy")
def privacy(case_id: str):
    case = store.get(case_id)
    if not case:
        raise HTTPException(404, "dosar inexistent")

    # 1. în repaus: documentele și valorile personale stau criptate (Fernet: AES-128-CBC + HMAC-SHA256)
    docs = []
    for d in case.documents:
        path = UPLOAD_DIR / _safe(case.id) / f"{_safe(d.id)}.enc"
        if path.exists():
            blob = path.read_bytes()
            docs.append({"doc_id": d.id, "filename": d.filename, "encrypted_bytes": len(blob), "sample": _sample(blob)})
    sealed = vault.sealed(case.id)
    vault_info = {"labels": sorted(label for label, _ in sealed), "count": len(sealed),
                  "sample": _sample(sealed[0][1]) if sealed else None}

    # 2. ce a văzut AI-ul: doar text redactat; fiecare apel trece prin poarta anti-PII și e auditat
    calls = [e for e in audit.recent(5000) if e.get("case_id") == case.id and e.get("kind") == "llm"]
    redacted = next((d.redacted_text for d in case.documents if d.redacted_text), None)
    ai = {"llm_calls": len(calls),
          "with_pii": sum(1 for e in calls if e.get("pii_detected")),
          # câte valori personale ale dosarului a căutat poarta în fiecare payload (0 = verificare goală)
          "pii_values_checked": max((e.get("pii_values_checked", 0) for e in calls), default=0),
          "blocked": sum(1 for e in calls if e.get("outcome") == "blocked"),
          "destinations": sorted({e.get("destination") for e in calls if e.get("destination")}),
          "models": sorted({e.get("model") for e in calls if e.get("model")}),
          "redacted_sample": redacted[:400] if redacted else None}

    # 3. criptare homomorfică: verificatorul a calculat netul pe ciphertext, fără cheia secretă
    he = None
    for r in case.results or []:
        if "he_scheme" in r.artifacts:
            he = {**r.artifacts, "verifier_has_secret_key": False,
                  "result_returned_to_bank": "doar diferența criptată; banca decriptează și compară cu toleranța"}

    # 4. ZK: dovada de venit (dacă s-a cerut pentru acest dosar)
    zk = zk_bank.last_by_case.get(case.id)

    injection = any(find_prompt_injection(d.redacted_text or "") for d in case.documents)
    return {"case_id": case.id,
            "at_rest": {"scheme": "Fernet (AES-128-CBC + HMAC-SHA256)", "documents": docs, "vault": vault_info},
            "ai_saw": ai, "homomorphic": he, "zk": zk, "prompt_injection_detected": injection}
