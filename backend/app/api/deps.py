import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_bank(authorization: str = Header(default="")) -> None:
    """Rutele „bancă”/„admin”: Authorization: Bearer <BANK_UI_TOKEN>. Nu acceptăm token în URL (ajunge în loguri)."""
    scheme, _, token = authorization.partition(" ")
    token = token.strip()
    if scheme != "Bearer" or not token or not settings.bank_ui_token or not secrets.compare_digest(
            token.encode(), settings.bank_ui_token.encode()):
        raise HTTPException(status_code=401, detail="unauthorized")
