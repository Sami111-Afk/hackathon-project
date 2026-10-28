"""Cuvintele de la Paznic (ctx.scratch["paznic"][doc_id]["words"]) grupate pe rânduri.

Un cuvânt: {"text": str, "page": int, "bbox": [x0, y0, x1, y1]} în pixeli pe pagină;
valorile personale sunt deja înlocuite cu etichete ([PERSOANA_1] ...).
"""
from dataclasses import dataclass, field
from statistics import median


@dataclass
class Line:
    page: int
    words: list[dict] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(w["text"] for w in self.words)

    @property
    def bbox(self) -> list[float]:
        return union_bbox(self.words)


def union_bbox(words: list[dict]) -> list[float]:
    x0, y0, x1, y1 = zip(*(w["bbox"] for w in words), strict=True)
    return [min(x0), min(y0), max(x1), max(y1)]


def _center(w: dict) -> float:
    return (w["bbox"][1] + w["bbox"][3]) / 2


def group_lines(words: list[dict]) -> list[Line]:
    """Cuvinte cu centrul vertical apropiat (sub jumătate din înălțimea tipică) = același rând."""
    if not words:
        return []
    tol = median(w["bbox"][3] - w["bbox"][1] for w in words) / 2
    lines: list[Line] = []
    for w in sorted(words, key=lambda w: (w["page"], _center(w), w["bbox"][0])):
        last = lines[-1] if lines else None
        if last and last.page == w["page"] and abs(_center(w) - median(map(_center, last.words))) <= tol:
            last.words.append(w)
        else:
            lines.append(Line(page=w["page"], words=[w]))
    for line in lines:
        line.words.sort(key=lambda w: w["bbox"][0])
    return lines


def ordered_words(lines: list[Line]) -> list[dict]:
    """Cuvintele în ordinea de citire (rând cu rând, stânga → dreapta)."""
    return [w for line in lines for w in line.words]
