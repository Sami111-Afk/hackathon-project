"""Fișierele încărcate: verificate după conținut (magic bytes), salvate criptate (VAULT_KEY)."""
import re

from cryptography.fernet import Fernet, InvalidToken

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
    if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", part):
        raise ValueError("id invalid")
    return part


def delete_case_files(case_id: str) -> None:
    folder = UPLOAD_DIR / _safe(case_id)
    if folder.exists():
        for f in folder.iterdir():
            f.unlink()
        folder.rmdir()


def save_encrypted(case_id: str, doc_id: str, data: bytes) -> None:
    folder = UPLOAD_DIR / _safe(case_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_safe(doc_id)}.enc").write_bytes(_fernet().encrypt(data))


def load_decrypted(case_id: str, doc_id: str) -> bytes | None:
    path = UPLOAD_DIR / _safe(case_id) / f"{_safe(doc_id)}.enc"
    if not path.exists():
        return None
    try:
        return _fernet().decrypt(path.read_bytes())
    except InvalidToken:
        return None  # VAULT_KEY schimbat sau fișier corupt
