"""Grounding: `source_text` întors de LLM trebuie să existe (fuzzy) în textul OCR.

Dacă există, potrivirea dă și pagina + bbox-ul (dovada pe imagine). Dacă nu,
câmpul devine null și Funcționarul emite EXTRACTION_UNGROUNDED.
"""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.agents.functionar.classify import normalize
from app.agents.functionar.layout import union_bbox
from app.agents.functionar.parsing import parse_amount, parse_date, parse_month
from app.agents.functionar.schemas import FieldKind

MIN_SCORE = 0.85


@dataclass
class Match:
    text: str
    score: float
    page: int | None = None
    bbox: list[float] | None = None


def compact(text: str) -> str:
    """Pentru comparații: fără diacritice, minuscule, fără spații și punctuație de margine."""
    return re.sub(r"[\s:;·|]+", "", normalize(text))


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _contains(hay: str, needle: str) -> bool:
    """`needle` în `hay`, dar nu lipit de alte cifre („8.500,00” nu e în „18.500,00”)."""
    start = hay.find(needle)
    while start != -1:
        end = start + len(needle)
        if not (start and hay[start - 1].isdigit()) and not (end < len(hay) and hay[end].isdigit()):
            return True
        start = hay.find(needle, start + 1)
    return False


def find_in_words(source_text: str, words: list[dict], min_score: float = MIN_SCORE) -> Match | None:
    """Cea mai bună fereastră de cuvinte consecutive (pe aceeași pagină) pentru `source_text`."""
    target = compact(source_text)
    if not target:
        return None
    best: tuple[float, int, int] | None = None
    keys = [compact(w["text"]) for w in words]
    max_len = len(target) * 1.3 + 2
    for i in range(len(words)):
        acc = ""
        for j in range(i, len(words)):
            if words[j]["page"] != words[i]["page"]:
                break
            acc += keys[j]
            if len(acc) > max_len:
                break
            score = 1.0 if acc == target else _ratio(acc, target)
            if best is None or score > best[0]:
                best = (score, i, j)
            if score == 1.0:
                break
        if best and best[0] == 1.0:
            break
    if not best or best[0] < 1.0:
        # fragment dintr-un cuvânt OCR lipit („20.05.19-12.03.2029” → „12.03.2029”)
        for w, key in zip(words, keys, strict=True):
            if len(target) >= 4 and _contains(key, target):
                return Match(text=source_text, score=1.0, page=w["page"], bbox=list(w["bbox"]))
    if not best or best[0] < min_score:
        return None
    score, i, j = best
    window = words[i:j + 1]
    return Match(text=" ".join(w["text"] for w in window), score=round(score, 3),
                 page=window[0]["page"], bbox=union_bbox(window))


def find_in_text(source_text: str, text: str, min_score: float = MIN_SCORE) -> Match | None:
    """Fără cuvinte cu bbox (ex. dosar redat din fixture): doar textul, fără dovadă pe imagine."""
    target, hay = compact(source_text), compact(text or "")
    if not target or not hay:
        return None
    if target in hay:
        return Match(text=source_text, score=1.0)
    n, best = len(target), 0.0
    for start in range(0, max(len(hay) - n, 0) + 1):
        window = hay[start:start + n]
        if SequenceMatcher(None, window, target).quick_ratio() >= min_score:
            best = max(best, _ratio(window, target))
    return Match(text=source_text, score=round(best, 3)) if best >= min_score else None


def value_matches_source(value: str, source_text: str, kind: FieldKind) -> bool:
    """LLM-ul n-are voie să „corecteze” valoarea: ea trebuie să reiasă din fragmentul citat."""
    parse = {"amount": parse_amount, "date": parse_date, "month": parse_month}.get(kind)
    if parse:
        return parse(value) is not None and parse(value) == parse(source_text)
    v, s = compact(value), compact(source_text)
    return bool(v) and (v in s or _ratio(v, s) >= MIN_SCORE)
