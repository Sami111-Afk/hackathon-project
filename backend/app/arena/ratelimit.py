import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import settings

_hits: dict[str, deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # doar în demo (în spatele tunelului) avem încredere în headerele de forward; altfel oricine le-ar falsifica
    if settings.env == "demo":
        fwd = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "?"


def _hit(key: str, cap: int, now: float) -> None:
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= cap:
        raise HTTPException(429, "too many attempts — wait a minute")
    q.append(now)


def limit(request: Request, nickname: str = "") -> None:
    """Limita e pe JUCĂTOR (IP + pseudonim), nu doar pe IP: la finală toată sala iese pe internet prin
    același IP (Wi-Fi-ul evenimentului). Pe IP rămâne un plafon mare, contra abuzului."""
    ip, now = client_ip(request), time.monotonic()
    _hit(f"ip:{ip}", settings.arena_rate_limit_per_ip_min, now)
    _hit(f"p:{ip}:{nickname.strip().lower()[:40]}", settings.arena_rate_limit_per_min, now)
    if len(_hits) > 5000:  # curățăm cheile inactive
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
            _hits.pop(k, None)
