import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import settings

_hits: dict[str, deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    # în spatele tunelului (ngrok/cloudflare), IP-ul real vine în header
    fwd = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")


def limit(request: Request) -> None:
    ip, now = client_ip(request), time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.arena_rate_limit_per_min:
        raise HTTPException(429, "prea multe încercări — mai așteaptă un minut")
    q.append(now)
