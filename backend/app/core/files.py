"""Fișierele încărcate: verificate după conținut (magic bytes), salvate criptate (VAULT_KEY)."""
from cryptography.fernet import Fernet

from app.config import REPO_ROOT, settings

UPLOAD_DIR = REPO_ROOT / "backend" / "uploads"

MAGIC = {
    b"\x89PNG\r\n\x1a\n": ("png", "image/png"),
    b"\xff\xd8\xff": ("jpg", "image/jpeg"),
    b"%PDF-": ("pdf", "application/pdf"),
}


def sniff(data: bytes) -> tuple[str, str] | None:
    return next((v for k, v in MAGIC.items() if data.startswith(k)), None)


def _fernet() -> Fernet:
    return Fernet(settings.vault_key.encode())


def _safe(part: str) -> str:
    if not part.replace("_", "").isalnum():
        raise ValueError("id invalid")
    return part


def save_encrypted(case_id: str, doc_id: str, data: bytes) -> None:
    folder = UPLOAD_DIR / _safe(case_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_safe(doc_id)}.enc").write_bytes(_fernet().encrypt(data))


def load_decrypted(case_id: str, doc_id: str) -> bytes | None:
    path = UPLOAD_DIR / _safe(case_id) / f"{_safe(doc_id)}.enc"
    return _fernet().decrypt(path.read_bytes()) if path.exists() else None
