"""BANCA: emite nonce-uri de unică folosință cu pragul fixat și verifică dovezile.

Banca nu află salariul: doar DA/NU la „venit net ≥ rată / 0,40” (plafonul DSTI de 40%).
"""
import math
import secrets
import threading
import time
from dataclasses import dataclass

from app.arena.missions import COMPANIES
from app.core import audit
from app.zk import employer, tools

DSTI = 0.40
NONCE_TTL_S = 15 * 60


@dataclass
class Challenge:
    nonce: int
    threshold_bani: int
    installment_bani: int
    case_id: str | None
    created: float


_lock = threading.Lock()
_challenges: dict[int, Challenge] = {}
last_by_case: dict[str, dict] = {}  # ultimul rezultat ZK per dosar (pentru panoul de confidențialitate)


def threshold_for(installment_bani: int) -> int:
    return math.ceil(installment_bani / DSTI)


def new_challenge(installment_bani: int, case_id: str | None = None) -> Challenge:
    ch = Challenge(secrets.randbits(128), threshold_for(installment_bani), installment_bani, case_id, time.time())
    with _lock:
        now = time.time()
        for n in [n for n, c in _challenges.items() if now - c.created > NONCE_TTL_S]:
            del _challenges[n]
        _challenges[ch.nonce] = ch
    return ch


def consume(nonce: int) -> Challenge | None:
    """Nonce-ul se consumă la PRIMA încercare (reușită sau nu) → fără replay, fără încercări repetate."""
    with _lock:
        ch = _challenges.pop(nonce, None)
    if ch and time.time() - ch.created > NONCE_TTL_S:
        return None
    return ch


def reset() -> None:
    with _lock:
        _challenges.clear()
    last_by_case.clear()


def verify(*, nonce: int, cui: str, period: str, commitment: int, signature: str, proof: bytes) -> dict:
    t0 = time.perf_counter()
    ch = consume(nonce)
    names = {info["cui"]: name for name, info in COMPANIES.items()}
    out = {"ok": False, "answer": "NU", "employer": names.get(cui), "cui": cui, "period": period}
    if ch is None:
        out["reason"] = "nonce unknown, expired or already used"
    else:
        out.update(threshold_ron=ch.threshold_bani / 100, installment_ron=ch.installment_bani / 100,
                   case_id=ch.case_id)
        if cui not in employer.registry():
            out["reason"] = "employer not in the registry"
        elif not employer.verify_signature(cui, period, commitment, nonce, signature):
            out["reason"] = "the employer signature is not valid"
        elif not tools.verify(proof, tools.public_inputs(ch.threshold_bani, commitment, nonce)):
            out["reason"] = "the ZK proof is not valid for the bank's threshold and request"
        else:
            out.update(ok=True, answer="DA",
                       reason="net income ≥ threshold, attested by the employer; the salary was not seen")
    out["verify_ms"] = round((time.perf_counter() - t0) * 1000)
    if out.get("case_id"):
        last_by_case[out["case_id"]] = {k: out.get(k) for k in ("answer", "reason", "threshold_ron", "employer",
                                                                "verify_ms")}
    audit.record(kind="zk_verify", destination="local", case_id=out.get("case_id"),
                 outcome="accepted" if out["ok"] else "rejected",
                 detail={"cui": cui, "reason": out["reason"], "threshold_ron": out.get("threshold_ron")})
    return out
