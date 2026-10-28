"""Motorul de reguli (ARCHITECTURE §8). Regulile sunt JSON, nu cod — evaluate cu operatori din whitelist.

Câmpuri disponibile pentru Arenă: doc.<câmp din fluturaș>, company.<câmp din registru>.
"""
import threading
from datetime import date

from app.arena.missions import COMPANIES
from app.models import Finding

OPS = {
    "eq": lambda a, b: a == b, "ne": lambda a, b: a != b,
    "lt": lambda a, b: a < b, "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b, "gte": lambda a, b: a >= b,
    "in": lambda a, b: a in b, "not_in": lambda a, b: a not in b,
    "exists": lambda a, _b: a is not None, "missing": lambda a, _b: a is None,
    "abs_diff_gt": lambda a, b: abs(a - b[0]) > b[1],
    "ratio_gt": lambda a, b: b[0] != 0 and a / b[0] > b[1],
}

_lock = threading.Lock()
RULES: list[dict] = []  # doar regulile aprobate se aplică


def context(doc: dict) -> dict:
    company = dict(COMPANIES.get(doc.get("employer"), {}))
    company["role_median"] = company.pop("role_medians", {}).get(doc.get("job_title"))
    ctx = {f"doc.{k}": v for k, v in doc.items()}
    ctx.update({f"company.{k}": v for k, v in company.items()})
    if "doc.issue_date" in ctx:
        ctx["doc.issue_date"] = date.fromisoformat(ctx["doc.issue_date"])
    return ctx


def _value(ctx: dict, x):
    if isinstance(x, str) and x.split(".")[0] in ("doc", "company"):
        return ctx.get(x)
    if isinstance(x, list):
        return [_value(ctx, i) for i in x]
    return x


def evaluate(cond: dict, ctx: dict) -> bool:
    if "all" in cond:
        return all(evaluate(c, ctx) for c in cond["all"])
    if "any" in cond:
        return any(evaluate(c, ctx) for c in cond["any"])
    if "not" in cond:
        return not evaluate(cond["not"], ctx)
    op = OPS[cond["op"]]
    left = _value(ctx, cond["left"])
    right = _value(ctx, cond.get("right", cond.get("value")))
    if left is None and cond["op"] not in ("exists", "missing"):
        return False
    if isinstance(left, date) and isinstance(right, str):
        right = date.fromisoformat(right)
    try:
        return bool(op(left, right))
    except (TypeError, ZeroDivisionError):
        return False


def apply_rules(doc: dict, rules: list[dict] | None = None) -> list[Finding]:
    ctx = context(doc)
    out = []
    with _lock:
        active = [r for r in (rules if rules is not None else RULES) if r.get("status") == "approved"]
    for r in active:
        if evaluate(r["when"], ctx):
            out.append(Finding(code=r["then"]["code"], severity=r["then"]["severity"],
                               message=r["then"]["message"], rule_id=r["id"]))
    return out


def add_rule(rule: dict) -> None:
    with _lock:
        RULES.append(rule)
