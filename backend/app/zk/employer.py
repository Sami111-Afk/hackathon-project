"""ANGAJATORUL (parte separată, simulată pentru demo): atestă salariul pentru O cerere.

Calculează angajamentul `pedersen(salariu, salt, nonce)` și semnează ECDSA P-256
mesajul `orb-zk-v1|CUI|perioadă|angajament|nonce`. Salariul și salt-ul merg DOAR la client;
banca primește angajamentul + semnătura și verifică semnătura cu cheia publică din registru.
Cheile private stau în data/zk/ (ignorat de git); în realitate fiecare angajator își ține cheia.
"""
import base64
import json
import secrets
import threading
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.arena.missions import COMPANIES
from app.config import settings
from app.zk import tools

_lock = threading.Lock()
_keys: dict[str, ec.EllipticCurvePrivateKey] = {}


def _keys_path():
    return settings.zk_data_dir / "employer_keys.json"


def _load() -> None:
    if _keys:
        return
    path = _keys_path()
    stored = json.loads(path.read_text()) if path.exists() else {}
    changed = False
    for info in COMPANIES.values():
        cui = info["cui"]
        if cui in stored:
            _keys[cui] = serialization.load_pem_private_key(stored[cui].encode(), password=None)
        else:
            _keys[cui] = ec.generate_private_key(ec.SECP256R1())
            stored[cui] = _keys[cui].private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                   serialization.NoEncryption()).decode()
            changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(stored))
        path.chmod(0o600)


def registry() -> dict[str, dict]:
    """Registrul public CUI → {nume, cheie publică PEM}. Asta e tot ce vede banca."""
    with _lock:
        _load()
        names = {info["cui"]: name for name, info in COMPANIES.items()}
        return {cui: {"name": names[cui], "public_key": k.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()}
            for cui, k in _keys.items()}


def message(cui: str, period: str, commitment: int, case_nonce: int) -> bytes:
    return f"orb-zk-v1|{cui}|{period}|{commitment:#066x}|{case_nonce}".encode()


@dataclass
class Attestation:
    cui: str
    period: str
    salary_bani: int  # doar pentru client
    salt: int         # doar pentru client
    commitment: int
    case_nonce: int
    signature: str    # base64 DER

    def for_bank(self) -> dict:
        return {"cui": self.cui, "period": self.period, "commitment": f"{self.commitment:#066x}",
                "signature": self.signature}


def attest(cui: str, period: str, salary_bani: int, case_nonce: int) -> Attestation:
    with _lock:
        _load()
        key = _keys.get(cui)
    if key is None:
        raise KeyError(cui)
    salt = secrets.randbelow(tools.FIELD_MODULUS)
    c = tools.commitment(salary_bani, salt, case_nonce)
    sig = key.sign(message(cui, period, c, case_nonce), ec.ECDSA(hashes.SHA256()))
    return Attestation(cui, period, salary_bani, salt, c, case_nonce, base64.b64encode(sig).decode())


def verify_signature(cui: str, period: str, commitment: int, case_nonce: int, signature_b64: str) -> bool:
    entry = registry().get(cui)
    if not entry:
        return False
    pub = serialization.load_pem_public_key(entry["public_key"].encode())
    try:
        pub.verify(base64.b64decode(signature_b64, validate=True), message(cui, period, commitment, case_nonce),
                   ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError):
        return False


def sign_with_unregistered_key(cui: str, period: str, commitment: int, case_nonce: int) -> str:
    """Pentru demo-ul de atac: o semnătură corectă matematic, dar cu o cheie pe care banca n-o cunoaște."""
    rogue = ec.generate_private_key(ec.SECP256R1())
    sig = rogue.sign(message(cui, period, commitment, case_nonce), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(sig).decode()
