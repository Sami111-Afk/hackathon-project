"""Etichete + amprente pentru un dosar. Vezi ARCHITECTURE.md §4, pașii 7–8.

Aceeași valoare primește aceeași etichetă în toate documentele dosarului:
„IONESCU” + „MARIA” (buletin) și „Maria Ionescu” (fluturaș) → [PERSOANA_1].
"""
import hashlib
import hmac
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from app.agents.paznic.detect import Span
from app.core.pii_gate import normalize as _base_normalize

# cheile din Case.fingerprints (pe care le folosește Detectivul)
FINGERPRINT_KEYS = {"CNP": "cnp", "IBAN": "iban", "TELEFON": "phone", "EMAIL": "email", "ADRESA": "address",
                    "CUI": "cui", "PERSOANA": "name"}
ADDRESS_NOISE = re.compile(r"\b(?:mun|municipiul|oras|orasul|com|comuna|sat|jud|judetul|str|strada|nr|bl|sc|et|ap|"
                           r"sector|sect|bd|bdul|bulevardul|cal|calea|sos|soseaua)\b\.?")
PERSON_GAP = 80  # „Nume” și „Prenume” de pe buletin, la mai puțin de atâtea caractere → aceeași persoană


def name_tokens(value: str) -> frozenset[str]:
    return frozenset(t for t in re.split(r"[\s\-,.]+", _base_normalize(value)) if len(t) > 1)


def normalize_value(kind: str, value: str) -> str:
    if kind == "PERSOANA":
        return " ".join(sorted(name_tokens(value)))
    if kind in ("CNP", "IBAN", "CUI", "TELEFON", "SERIE", "NR", "MRZ"):
        clean = re.sub(r"[\s.\-]", "", value).upper()
        if kind == "CUI":
            clean = clean.removeprefix("RO")
        if kind == "TELEFON":
            clean = re.sub(r"^(?:\+40|0040)", "0", clean)
        return clean
    if kind == "ADRESA":
        text = ADDRESS_NOISE.sub(" ", _base_normalize(value))
        return " ".join(re.sub(r"[^\w\s]", " ", text).split())
    return _base_normalize(value)


def fingerprint(secret: str, kind: str, normalized: str) -> str:
    digest = hmac.new(secret.encode(), f"{kind}:{normalized}".encode(), hashlib.sha256).hexdigest()
    return f"hm_{digest[:16]}"


@dataclass
class Replacement:
    span: Span
    label: str


@dataclass
class CaseRedactor:
    secret: str
    labels: dict[tuple[str, str], str] = field(default_factory=dict)
    counts: Counter = field(default_factory=Counter)
    people: list[tuple[set[str], str]] = field(default_factory=list)
    vault: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))  # etichetă → valorile originale
    fingerprints: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    fingerprint_by_label: dict[str, str] = field(default_factory=dict)

    def _remember(self, label: str, value: str) -> None:
        if value not in self.vault[label]:
            self.vault[label].append(value)

    def _new_label(self, kind: str) -> str:
        self.counts[kind] += 1
        return f"[{kind}_{self.counts[kind]}]"

    def _person_label(self, tokens: frozenset[str]) -> str:
        for known, label in self.people:
            if tokens <= known or known <= tokens:
                known |= tokens
                return label
        label = self._new_label("PERSOANA")
        self.people.append((set(tokens), label))
        return label

    def _group_people(self, spans: list[Span]) -> dict[Span, frozenset[str]]:
        """Nume + prenume pe rânduri separate (buletin) → un singur set de tokeni."""
        people = [s for s in spans if s.kind == "PERSOANA"]
        groups: dict[Span, frozenset[str]] = {}
        i = 0
        while i < len(people):
            group = [people[i]]
            while (i + 1 < len(people) and people[i + 1].start - group[-1].end <= PERSON_GAP
                   and len(name_tokens(group[-1].value)) == 1 and len(name_tokens(people[i + 1].value)) == 1):
                i += 1
                group.append(people[i])
            tokens = frozenset().union(*(name_tokens(s.value) for s in group))
            groups.update({s: tokens for s in group})
            i += 1
        return groups

    def label_spans(self, spans: list[Span]) -> list[Replacement]:
        groups = self._group_people(spans)
        out = []
        for s in spans:
            if s.kind == "PERSOANA":
                tokens = groups.get(s, name_tokens(s.value))
                if not tokens:
                    continue
                label = self._person_label(tokens)
                norm = " ".join(sorted(next(set(t) for t, lbl in self.people if lbl == label)))
                self._remember(label, s.value)
            else:
                norm = normalize_value(s.kind, s.value)
                key = (s.kind, norm)
                label = self.labels.get(key) or self.labels.setdefault(key, self._new_label(s.kind))
                self._remember(label, s.value)
            if s.kind in FINGERPRINT_KEYS and norm:
                fp = fingerprint(self.secret, s.kind, norm)
                self.fingerprint_by_label[label] = fp
            out.append(Replacement(s, label))
        return out

    def finalize_fingerprints(self) -> dict[str, list[str]]:
        """Amprentele dosarului; pentru persoane folosim setul final de tokeni (după unire)."""
        result: dict[str, set[str]] = defaultdict(set)
        person_labels = {lbl for _, lbl in self.people}
        for label, fp in self.fingerprint_by_label.items():
            kind = label[1:].rsplit("_", 1)[0]
            if label in person_labels:
                tokens = next(t for t, lbl in self.people if lbl == label)
                fp = fingerprint(self.secret, "PERSOANA", " ".join(sorted(tokens)))
            result[FINGERPRINT_KEYS[kind]].add(fp)
        return {k: sorted(v) for k, v in result.items()}


def apply(text: str, replacements: list[Replacement]) -> str:
    """Înlocuiește span-urile cu etichete (de la coadă, ca offset-urile să rămână valabile)."""
    for r in sorted(replacements, key=lambda r: r.span.start, reverse=True):
        text = text[:r.span.start] + r.label + text[r.span.end:]
    return text
