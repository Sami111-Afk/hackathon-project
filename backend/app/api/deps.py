import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_bank(authorization: str = Header(default="")) -> None:
    """Rutele „bancă”/„admin”: Authorization: Bearer <BANK_UI_TOKEN>. Nu acceptăm token în URL (ajunge în loguri)."""
    token = authorization.removeprefix("Bearer ").strip()
    if not token or not secrets.compare_digest(token, settings.bank_ui_token):
        raise HTTPException(status_code=401, detail="neautorizat")
