"""Apeluri către uneltele ZK: `nargo` (witness) și `bb` (dovadă / verificare).

Versiuni fixate (vezi zk/README.md): nargo 1.0.0-beta.13 + bb 1.2.0.
Fiecare apel lucrează într-un director temporar propriu → apeluri concurente sigure.
"""
import logging
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

from app.config import REPO_ROOT, settings

log = logging.getLogger("orb.zk")

CIRCUITS = REPO_ROOT / "zk" / "circuits"
MAIN = "income_threshold"
COMMIT = "commitment"
FIELD_MODULUS = 0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000001  # BN254
TIMEOUT_S = 60

_vk_lock = threading.Lock()
_vk: bytes | None = None


class ZkUnavailable(RuntimeError):
    """Uneltele lipsesc sau au eșuat — ruta răspunde 503, nu „NU”."""


def _bin(name: str, configured: str, fallback: Path) -> str:
    for cand in (configured, shutil.which(name), str(fallback)):
        if cand and Path(cand).is_file():
            return cand
    raise ZkUnavailable(f"{name} is not installed (see zk/README.md)")


def nargo() -> str:
    return _bin("nargo", settings.zk_nargo_bin, Path.home() / ".nargo" / "bin" / "nargo")


def bb() -> str:
    return _bin("bb", settings.zk_bb_bin, Path.home() / ".bb" / "bb")


def available() -> bool:
    try:
        nargo(), bb()
        return (CIRCUITS / MAIN / "src" / "main.nr").is_file()
    except ZkUnavailable:
        return False


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_S)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ZkUnavailable(f"{Path(cmd[0]).name}: {e}") from e


def _execute(circuit: str, inputs: dict[str, int], work: Path) -> tuple[Path, str]:
    """Copiază circuitul în `work`, scrie Prover.toml și rulează `nargo execute`. Întoarce (director, stdout)."""
    prog = work / circuit
    shutil.copytree(CIRCUITS / circuit, prog, ignore=shutil.ignore_patterns("target", "Prover.toml"))
    (prog / "Prover.toml").write_text("".join(f'{k} = "{v}"\n' for k, v in inputs.items()))
    r = _run([nargo(), "execute"], cwd=prog)
    if r.returncode != 0:
        # constrângere încălcată (ex. venit sub prag) → nu se poate genera dovada
        raise ValueError(_nargo_error(r.stderr + r.stdout))
    return prog, r.stdout


def _nargo_error(text: str) -> str:
    m = re.search(r"(venit sub prag|angajament invalid)", text)
    if not m:
        return "witness invalid"
    return {"venit sub prag": "income below threshold", "angajament invalid": "invalid commitment"}[m.group(1)]


def commitment(salary_bani: int, salt: int, case_nonce: int) -> int:
    """pedersen_hash([salariu, salt, nonce]) — exact ca în circuit (rulăm același cod Noir)."""
    with tempfile.TemporaryDirectory(prefix="orb-zk-") as tmp:
        _, out = _execute(COMMIT, {"salary_bani": salary_bani, "salt": salt, "case_nonce": case_nonce}, Path(tmp))
    m = re.search(r"Circuit output: (0x[0-9a-fA-F]+)", out)
    if not m:
        raise ZkUnavailable("nargo did not return the commitment")
    return int(m.group(1), 16)


def verification_key() -> bytes:
    """Cheia de verificare a circuitului — calculată o dată de bancă din circuitul compilat."""
    global _vk
    with _vk_lock:
        if _vk is None:
            with tempfile.TemporaryDirectory(prefix="orb-zk-vk-") as tmp:
                prog = Path(tmp) / MAIN
                shutil.copytree(CIRCUITS / MAIN, prog, ignore=shutil.ignore_patterns("target", "Prover.toml"))
                r = _run([nargo(), "compile"], cwd=prog)
                if r.returncode != 0:
                    raise ZkUnavailable("circuit compilation failed: " + r.stderr[-300:])
                r = _run([bb(), "write_vk", "-b", str(prog / "target" / f"{MAIN}.json"), "-o", str(prog / "target")])
                if r.returncode != 0:
                    raise ZkUnavailable("bb write_vk failed: " + r.stderr[-300:])
                _vk = (prog / "target" / "vk").read_bytes()
        return _vk


def public_inputs(threshold_bani: int, commitment_value: int, case_nonce: int) -> bytes:
    """Ordinea și formatul `bb`: câte 32 de octeți big-endian, în ordinea parametrilor `pub` din main.nr."""
    return b"".join(v.to_bytes(32, "big") for v in (threshold_bani, commitment_value, case_nonce))


def prove(salary_bani: int, salt: int, threshold_bani: int, commitment_value: int, case_nonce: int) -> bytes:
    """Partea CLIENTULUI (în demo rulează pe server; în producție în browser/telefon cu noir_js + bb.js)."""
    vk = verification_key()
    with tempfile.TemporaryDirectory(prefix="orb-zk-") as tmp:
        prog, _ = _execute(MAIN, {"salary_bani": salary_bani, "salt": salt, "threshold_bani": threshold_bani,
                               "commitment": commitment_value, "case_nonce": case_nonce}, Path(tmp))
        t = prog / "target"
        (t / "vk").write_bytes(vk)
        r = _run([bb(), "prove", "-b", str(t / f"{MAIN}.json"), "-w", str(t / f"{MAIN}.gz"),
                  "-k", str(t / "vk"), "-o", str(t)])
        if r.returncode != 0:
            raise ZkUnavailable("bb prove failed: " + r.stderr[-300:])
        return (t / "proof").read_bytes()


def verify(proof: bytes, pub: bytes) -> bool:
    """Partea BĂNCII: inputurile publice le construiește banca, nu le ia de la client."""
    vk = verification_key()
    with tempfile.TemporaryDirectory(prefix="orb-zk-v-") as tmp:
        d = Path(tmp)
        (d / "vk").write_bytes(vk)
        (d / "proof").write_bytes(proof)
        (d / "public_inputs").write_bytes(pub)
        r = _run([bb(), "verify", "-k", str(d / "vk"), "-p", str(d / "proof"), "-i", str(d / "public_inputs")])
        return r.returncode == 0
