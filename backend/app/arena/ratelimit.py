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


def limit(request: Request) -> None:
    ip, now = client_ip(request), time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.arena_rate_limit_per_min:
        raise HTTPException(429, "prea multe încercări — mai așteaptă un minut")
    q.append(now)
    if len(_hits) > 5000:  # curățăm IP-urile inactive
        for k in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
            _hits.pop(k, None)
