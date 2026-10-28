"""Rândurile extrasului de cont, citite determinist (fără LLM, care ar sări/inventa rânduri).

Pe fiecare rând de tranzacție: data la început, ultima sumă = soldul după tranzacție,
suma dinainte (dacă există) = valoarea tranzacției. Așa nu depindem de coordonatele
exacte ale coloanelor, doar de ordinea lor (Data · Descriere · Sumă · Sold).
Verificarea soldurilor e treaba Verificatorului.
"""
import re
from dataclasses import asdict, dataclass, field

from app.agents.functionar.classify import normalize
from app.agents.functionar.layout import Line, union_bbox
from app.agents.functionar.parsing import parse_amount

_ROW_DATE = re.compile(r"^\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?$")
_AMOUNT_TOKEN = re.compile(r"^[-−–]?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}$")


@dataclass
class StatementRow:
    date: str
    description: str
    amount: float | None
    balance: float
    page: int
    bbox: list[float]
    amount_bbox: list[float] | None = None  # chenarul fiecărei sume, pentru recitire și dovadă
    balance_bbox: list[float] | None = None


@dataclass
class StatementTable:
    rows: list[StatementRow] = field(default_factory=list)
    opening_balance: float | None = None
    closing_balance: float | None = None
    closing_evidence: dict | None = None  # {"page", "bbox"} pe suma soldului final

    def to_dict(self) -> dict:
        return asdict(self)


def parse_statement(lines: list[Line]) -> StatementTable:
    table = StatementTable()
    for line in lines:
        amounts = [w for w in line.words if _AMOUNT_TOKEN.match(w["text"])]
        if not amounts:
            continue
        if normalize(line.text).startswith("sold final"):
            table.closing_balance = parse_amount(amounts[-1]["text"])
            table.closing_evidence = {"page": line.page, "bbox": union_bbox(amounts[-1:])}
            continue
        if not _ROW_DATE.match(line.words[0]["text"]):
            continue
        balance_w = amounts[-1]
        amount_w = amounts[-2] if len(amounts) > 1 else None
        desc = " ".join(w["text"] for w in line.words[1:] if w is not balance_w and w is not amount_w)
        row = StatementRow(
            date=line.words[0]["text"],
            description=desc,
            amount=parse_amount(amount_w["text"]) if amount_w else None,
            balance=parse_amount(balance_w["text"]),
            page=line.page,
            bbox=line.bbox,
            amount_bbox=list(amount_w["bbox"]) if amount_w else None,
            balance_bbox=list(balance_w["bbox"]),
        )
        if row.amount is None and not table.rows and "sold" in normalize(desc):
            table.opening_balance = row.balance
        table.rows.append(row)
    return table
