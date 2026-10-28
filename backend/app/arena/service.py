"""Arena: trimiteri, scor, clasament. Public — deci totul e limitat și filtrat.

- puncte doar dacă ținta misiunii e atinsă ȘI documentul diferă de șablon
- duplicatele (aceleași câmpuri + trucuri) nu mai primesc puncte
- plafon de puncte per pseudonim
- proiecția publică nu conține niciodată date interne
"""
import hashlib
import json
import re
import threading
import time
import uuid
from collections import defaultdict, deque

from app.arena.forge import apply_edits, render
from app.arena.judge import judge
from app.arena.missions import MISSIONS
from app.core.events import bus, now_iso

LIVE_CHANNEL = "arena_live"
POINTS_PASSED = 500
POINTS_CAUGHT = 10
POINTS_NEAR_MISS = 100      # prins de un singur agent = „aproape”
MAX_POINTS_PER_PLAYER = 3000

BAD_WORDS = {"pula", "pizda", "muie", "fut", "cacat", "fuck", "shit", "bitch", "nigger"}

_lock = threading.Lock()
_submissions: dict[str, dict] = {}
_images: dict[str, bytes] = {}
_seen: set[str] = set()
_scores: dict[str, int] = defaultdict(int)
_feed: deque = deque(maxlen=50)
_misses: list[dict] = []    # falsuri care au trecut → hrană pentru self-learning


class ArenaError(ValueError):
    pass


def clean_nickname(raw: str) -> str:
    nick = re.sub(r"[^\w .-]", "", (raw or "").strip(), flags=re.UNICODE)[:20].strip()
    if len(nick) < 2:
        raise ArenaError("pseudonim prea scurt")
    low = nick.lower().replace(" ", "")
    if any(w in low for w in BAD_WORDS):
        raise ArenaError("alege alt pseudonim")
    return nick


def submit(nickname: str, mission_id: str, edits: dict, tricks: list[str]) -> dict:
    nick = clean_nickname(nickname)
    mission = MISSIONS.get(mission_id)
    if not mission:
        raise ArenaError("misiune inexistentă")
    try:
        doc = apply_edits(mission["template"], edits, mission["editable"], tricks or [])
    except (TypeError, ValueError) as exc:
        raise ArenaError("câmpuri invalide") from exc

    changed = {k for k in mission["template"] if doc.get(k) != mission["template"][k]} | set(doc["tricks"])
    target = mission["target"]
    target_met = doc.get(target["field"], 0) >= target["min"]
    fingerprint = hashlib.sha256(json.dumps([mission_id, doc], sort_keys=True, default=str).encode()).hexdigest()

    t0 = time.perf_counter()
    result = judge(doc)
    sid = f"sub_{uuid.uuid4().hex[:12]}"

    with _lock:
        duplicate = fingerprint in _seen
        _seen.add(fingerprint)
        if not changed or not target_met:
            points, outcome = 0, "invalid"
        elif result["caught"]:
            points = POINTS_CAUGHT + (POINTS_NEAR_MISS if len(result["caught_by"]) == 1 else 0)
            outcome = "caught"
        else:
            points, outcome = POINTS_PASSED, "passed"
        if duplicate:
            points = 0
        points = max(0, min(points, MAX_POINTS_PER_PLAYER - _scores[nick]))
        _scores[nick] += points

        public = {
            "id": sid, "nickname": nick, "mission_id": mission_id, "mission_title": mission["title"],
            "outcome": outcome, "points": points, "duplicate": duplicate, "target_met": target_met,
            "caught_by": result["caught_by"], "reasons": result["reasons"],
            "risk": result["verdict"].risk, "changed": sorted(changed),
            "ms": int((time.perf_counter() - t0) * 1000), "ts": now_iso(),
        }
        _submissions[sid] = {**public, "doc": doc, "results": result["results"]}
        _images[sid] = render(doc)
        _feed.appendleft(public)
        if outcome == "passed" and not duplicate:
            _misses.append({"submission_id": sid, "mission_id": mission_id, "doc": doc})

    bus.publish(LIVE_CHANNEL, "arena_scored", message=_feed_line(public), data=public)
    bus.trim(LIVE_CHANNEL, keep=200)
    return public


def _feed_line(p: dict) -> str:
    if p["outcome"] == "passed":
        return f"{p['nickname']} a păcălit agenții! +{p['points']}"
    if p["outcome"] == "caught":
        return f"{p['nickname']} prins de {', '.join(p['caught_by'])}"
    return f"{p['nickname']}: fals invalid (ținta nu e atinsă)"


def get(sid: str) -> dict | None:
    s = _submissions.get(sid)
    return {k: v for k, v in s.items() if k not in ("doc", "results")} if s else None


def last_results(sid: str | None) -> list:
    return (_submissions.get(sid) or {}).get("results", []) if sid else []


def image(sid: str) -> bytes | None:
    return _images.get(sid)


def leaderboard(limit: int = 10) -> list[dict]:
    with _lock:
        top = sorted(_scores.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"rank": i + 1, "nickname": n, "points": p} for i, (n, p) in enumerate(top)]


def feed() -> list[dict]:
    return list(_feed)


def stats() -> dict:
    with _lock:
        subs = list(_submissions.values())
    valid = [s for s in subs if s["outcome"] != "invalid"]
    return {"submissions": len(subs), "valid": len(valid),
            "passed": sum(s["outcome"] == "passed" for s in valid),
            "caught": sum(s["outcome"] == "caught" for s in valid),
            "players": len(_scores)}


def pending_misses() -> list[dict]:
    return list(_misses)


def reset() -> None:
    with _lock:
        for c in (_submissions, _images, _scores):
            c.clear()
        _seen.clear()
        _feed.clear()
        _misses.clear()
