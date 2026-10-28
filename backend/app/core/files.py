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


VIEWS = {"redacted", "ela"}


def save_derived(case_id: str, doc_id: str, view: str, page: int, png: bytes) -> None:
    """Imagini produse de agenți (Paznic: view="redacted", Detector: view="ela"), salvate criptat."""
    if view not in VIEWS:
        raise ValueError("vedere necunoscută")
    folder = UPLOAD_DIR / _safe(case_id)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{_safe(doc_id)}.{view}.p{int(page)}.enc").write_bytes(_fernet().encrypt(png))


def load_derived(case_id: str, doc_id: str, view: str, page: int) -> bytes | None:
    if view not in VIEWS:
        return None
    path = UPLOAD_DIR / _safe(case_id) / f"{_safe(doc_id)}.{view}.p{int(page)}.enc"
    try:
        return _fernet().decrypt(path.read_bytes()) if path.exists() else None
    except InvalidToken:
        return None


def render_pages(data: bytes, scale: float = 2.0) -> list:
    """PDF → listă de imagini PIL (o pagină = o imagine); imagine → [imaginea]."""
    import io

    from PIL import Image

    kind = sniff(data)
    if kind and kind[0] == "pdf":
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(data)
        return [pdf[i].render(scale=scale).to_pil().convert("RGB") for i in range(len(pdf))]
    return [Image.open(io.BytesIO(data)).convert("RGB")]


def to_png(img) -> bytes:
    import io
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


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
