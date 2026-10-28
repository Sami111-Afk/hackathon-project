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


# rânduri vecine nu se suprapun deloc (sunt la ~1,5 înălțimi distanță); 30% acoperă o rotire de ~1°
MIN_OVERLAP = 0.3


def _overlap(a: dict, b: dict) -> float:
    """Cât se suprapun pe verticală, ca fracție din înălțimea celui mai mic."""
    inter = min(a["bbox"][3], b["bbox"][3]) - max(a["bbox"][1], b["bbox"][1])
    smaller = min(a["bbox"][3] - a["bbox"][1], b["bbox"][3] - b["bbox"][1]) or 1
    return inter / smaller


def group_lines(words: list[dict]) -> list[Line]:
    """Rândurile, citite stânga → dreapta: un cuvânt continuă rândul al cărui ultim cuvânt îl suprapune
    pe verticală (≥ 30% din înălțime). Așa o scanare ușor rotită (rândul „coboară” ~15 px pe
    lățimea paginii) nu rupe „Sold final … 26.480,00” în două rânduri."""
    if not words:
        return []
    lines: list[Line] = []
    for w in sorted(words, key=lambda w: (w["page"], w["bbox"][0], _center(w))):
        candidates = [ln for ln in lines if ln.page == w["page"] and _overlap(ln.words[-1], w) >= MIN_OVERLAP]
        if candidates:
            best = max(candidates, key=lambda ln: (_overlap(ln.words[-1], w), -abs(_center(ln.words[-1]) - _center(w))))
            best.words.append(w)
        else:
            lines.append(Line(page=w["page"], words=[w]))
    lines.sort(key=lambda ln: (ln.page, median(map(_center, ln.words)), ln.words[0]["bbox"][0]))
    return lines


def ordered_words(lines: list[Line]) -> list[dict]:
    """Cuvintele în ordinea de citire (rând cu rând, stânga → dreapta)."""
    return [w for line in lines for w in line.words]
