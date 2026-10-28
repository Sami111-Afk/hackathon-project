"""Rutele ZK: banca (nonce, verificare) + părțile simulate pentru demo (angajator, portofelul clientului)."""
import asyncio
import base64
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import require_bank
from app.zk import bank, employer, tools

router = APIRouter(prefix="/api/zk", dependencies=[Depends(require_bank)])

PERIOD_RX = r"^\d{4}-(0[1-9]|1[0-2])$"
HEX_OR_INT = r"^(0x[0-9a-fA-F]{1,64}|\d{1,78})$"


def _int(v: str) -> int:
    return int(v, 0)


def _bani(ron: float) -> int:
    return round(ron * 100)


def _hex(v: int) -> str:
    return f"{v:#066x}"


def _require_tools() -> None:
    if not tools.available():
        raise HTTPException(503, "ZK unavailable on this server (nargo/bb missing, see zk/README.md)")


async def _call(fn, *args, **kw):
    try:
        return await asyncio.to_thread(fn, *args, **kw)
    except tools.ZkUnavailable as e:
        raise HTTPException(503, f"ZK unavailable: {e}") from e


class NonceIn(BaseModel):
    installment_ron: float = Field(gt=0, le=1_000_000)
    case_id: str | None = Field(default=None, max_length=64)


class AttestIn(BaseModel):
    cui: str = Field(pattern=r"^RO\d{2,10}$")
    period: str = Field(pattern=PERIOD_RX)
    net_salary_ron: float = Field(ge=0, le=10_000_000)
    nonce: str = Field(pattern=HEX_OR_INT)


class ProveIn(BaseModel):
    net_salary_ron: float = Field(ge=0, le=10_000_000)
    salt: str = Field(pattern=HEX_OR_INT)
    commitment: str = Field(pattern=HEX_OR_INT)
    nonce: str = Field(pattern=HEX_OR_INT)
    threshold_ron: float = Field(ge=0, le=10_000_000)


class VerifyIn(BaseModel):
    nonce: str = Field(pattern=HEX_OR_INT)
    cui: str = Field(pattern=r"^RO\d{2,10}$")
    period: str = Field(pattern=PERIOD_RX)
    commitment: str = Field(pattern=HEX_OR_INT)
    signature: str = Field(max_length=200)
    proof_b64: str = Field(max_length=100_000)


class DemoIn(BaseModel):
    net_salary_ron: float = Field(default=8307, ge=0, le=10_000_000)
    installment_ron: float = Field(default=2500, gt=0, le=1_000_000)
    cui: str = Field(default="RO9341910290", pattern=r"^RO\d{2,10}$")
    period: str = Field(default="2026-09", pattern=PERIOD_RX)
    attack: Literal["none", "lie_salary", "lower_threshold", "fake_signature", "replay"] = "none"
    case_id: str | None = Field(default=None, max_length=64)


@router.get("/status")
def status():
    ok = tools.available()
    return {"available": ok, "scheme": "UltraHonk (Barretenberg)", "circuit": tools.MAIN,
            "nargo": "1.0.0-beta.13", "bb": "1.2.0", "dsti": bank.DSTI,
            "statement": "net income (attested by the employer, for this application) ≥ installment / 0.40"}


@router.get("/registry")
def registry():
    return {"employers": employer.registry()}


@router.post("/nonce")
def nonce(body: NonceIn):
    _require_tools()
    ch = bank.new_challenge(_bani(body.installment_ron), body.case_id)
    return {"nonce": _hex(ch.nonce), "threshold_ron": ch.threshold_bani / 100, "expires_in_s": bank.NONCE_TTL_S}


@router.post("/employer/attest")
async def attest(body: AttestIn):
    """ANGAJATORUL (simulat): răspunsul complet merge la CLIENT; banca primește doar `for_bank`."""
    _require_tools()
    try:
        a = await _call(employer.attest, body.cui, body.period, _bani(body.net_salary_ron), _int(body.nonce))
    except KeyError:
        raise HTTPException(404, "unknown employer") from None
    return {"client": {"net_salary_ron": a.salary_bani / 100, "salt": _hex(a.salt)}, "for_bank": a.for_bank(),
            "nonce": body.nonce}


@router.post("/client/prove")
async def prove(body: ProveIn):
    """PORTOFELUL CLIENTULUI (simulat pe server; în producție rulează pe telefon cu noir_js + bb.js)."""
    _require_tools()
    t0 = time.perf_counter()
    try:
        proof = await _call(tools.prove, _bani(body.net_salary_ron), _int(body.salt), _bani(body.threshold_ron),
                            _int(body.commitment), _int(body.nonce))
    except ValueError as e:
        raise HTTPException(422, f"cannot generate the proof: {e}") from None
    return {"proof_b64": base64.b64encode(proof).decode(), "proof_bytes": len(proof),
            "prove_ms": round((time.perf_counter() - t0) * 1000)}


@router.post("/verify")
async def verify(body: VerifyIn):
    """BANCA: verifică semnătura angajatorului + dovada; nonce-ul se consumă la prima încercare."""
    _require_tools()
    try:
        proof = base64.b64decode(body.proof_b64, validate=True)
    except ValueError:
        raise HTTPException(422, "invalid proof_b64") from None
    return await _call(bank.verify, nonce=_int(body.nonce), cui=body.cui, period=body.period,
                       commitment=_int(body.commitment), signature=body.signature, proof=proof)


@router.post("/demo")
async def demo(body: DemoIn):
    """Tot fluxul pe un buton: bancă → angajator → client → bancă, opțional cu un atac. Pentru UI și pitch."""
    _require_tools()
    steps: list[dict] = []
    ch = bank.new_challenge(_bani(body.installment_ron), body.case_id)
    detail = f"installment {body.installment_ron:.2f} lei → threshold {ch.threshold_bani / 100:.2f} lei, unique nonce"
    steps.append({"actor": "bank", "action": "requests proof", "detail": detail})
    try:
        a = await _call(employer.attest, body.cui, body.period, _bani(body.net_salary_ron), ch.nonce)
    except KeyError:
        raise HTTPException(404, "unknown employer") from None
    steps.append({"actor": "employer", "action": "attests",
                  "detail": "commitment + ECDSA signature (the salary goes only to the customer)"})
    for_bank = a.for_bank()

    salary, threshold = a.salary_bani, ch.threshold_bani
    if body.attack == "lie_salary":
        salary = max(salary, threshold) + 100_000  # clientul pretinde un salariu mai mare decât cel atestat
    if body.attack == "lower_threshold":
        threshold = threshold // 2  # clientul dovedește un prag mai mic decât cel cerut
    if body.attack == "fake_signature":
        # falsificatorul semnează singur, cu o cheie care nu e în registru
        for_bank = {**for_bank, "signature": employer.sign_with_unregistered_key(a.cui, a.period, a.commitment,
                                                                                  ch.nonce)}

    t0 = time.perf_counter()
    try:
        proof = await _call(tools.prove, salary, a.salt, threshold, a.commitment, ch.nonce)
    except ValueError as e:
        bank.consume(ch.nonce)
        steps.append({"actor": "customer", "action": "cannot generate proof", "detail": str(e)})
        return {"answer": "NU", "ok": False, "reason": f"the customer cannot prove it: {e}", "steps": steps,
                "attack": body.attack}
    steps.append({"actor": "customer", "action": "generates proof",
                  "detail": f"{len(proof)} bytes in {round((time.perf_counter() - t0) * 1000)} ms"})

    res = await _call(bank.verify, nonce=ch.nonce, cui=for_bank["cui"], period=for_bank["period"],
                      commitment=_int(for_bank["commitment"]), signature=for_bank["signature"], proof=proof)
    steps.append({"actor": "bank", "action": "verifies", "detail": f"{res['answer']} — {res['reason']}"})
    if body.attack == "replay":
        res = await _call(bank.verify, nonce=ch.nonce, cui=for_bank["cui"], period=for_bank["period"],
                          commitment=_int(for_bank["commitment"]), signature=for_bank["signature"], proof=proof)
        steps.append({"actor": "attacker", "action": "resends the same proof",
                      "detail": f"{res['answer']} — {res['reason']}"})
    return {**res, "steps": steps, "attack": body.attack,
            "bank_saw": {k: v for k, v in for_bank.items() if k != "signature"} | {"proof_bytes": len(proof)}}


