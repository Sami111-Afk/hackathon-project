"""📄 Funcționar — Stefan. Clasifică documentele și extrage câmpurile, cu grounding.

Pentru fiecare document (ARCHITECTURE.md §5):
  1. tipul: după titlurile fixe; LLM doar dacă nu se recunoaște nimic;
  2. câmpurile: LLM pe textul redactat (string-uri brute + source_text) și, în paralel,
     extragerea pe etichete; câștigă primul candidat care trece de grounding;
  3. extrasul de cont: rândurile citite determinist (statement.py), LLM doar pentru antet;
  4. Python parsează sumele și datele (parsing.py).

Scrie în case: doc.type, doc.extracted. Lasă în ctx.scratch["functionar"][doc_id]:
  {"fields": {câmp: {"page", "bbox"}}, "statement": StatementTable.to_dict() | None}
"""
import asyncio
import logging
from dataclasses import dataclass, field

from app.agents.functionar.classify import classify_by_keywords
from app.agents.functionar.grounding import (
    Match,
    find_in_text,
    find_in_words,
    narrow_to_value,
    value_matches_source,
)
from app.agents.functionar.labels import extract_by_labels
from app.agents.functionar.layout import group_lines, ordered_words
from app.agents.functionar.parsing import parse_amount, parse_date, parse_month
from app.agents.functionar.schemas import (
    DOC_LABELS,
    FIELD_KINDS,
    IDENTIFIER_FIELDS,
    SCHEMAS,
    SYSTEM_CLASSIFY,
    SYSTEM_EXTRACT,
    ClassifyOut,
    RawField,
    is_label,
)
from app.agents.functionar.statement import parse_statement
from app.agents.stubs import StubAgent
from app.core.llm import LLMUnavailable, chat
from app.core.pii_gate import PIIGateBlocked
from app.models import AgentResult, Document, Evidence, ExtractedValue, Finding, LLMUsage

log = logging.getLogger("orb.functionar")

PARSERS = {"amount": parse_amount, "date": parse_date, "month": parse_month}
SHORT_LABELS = {"id_card": "buletin", "payslip": "fluturaș", "bank_statement": "extras",
                "employment_certificate": "adeverință", "other": "alt document", "unknown": "necunoscut"}
FIELD_RO = {"gross_salary": "salariul brut", "net_salary": "salariul net", "closing_balance": "soldul final",
            "opening_balance": "soldul inițial", "employer_cui": "CUI-ul angajatorului"}


@dataclass
class _Calls:
    """Ce s-a întâmplat cu LLM-ul pe tot dosarul (pentru llm_usage și finding-uri)."""

    usages: list[LLMUsage] = field(default_factory=list)
    unavailable: bool = False
    blocked: set[str] = field(default_factory=set)

    async def ask(self, case_id: str, **kwargs):
        try:
            r = await chat("extract", case_id=case_id, **kwargs)
        except PIIGateBlocked as exc:
            self.blocked.update(exc.kinds)
            return None
        except LLMUnavailable as exc:
            log.warning("LLM indisponibil în Funcționar: %s", exc)
            self.unavailable = True
            return None
        if r.usage:
            self.usages.append(r.usage)
        return r.data

    def total_usage(self) -> LLMUsage | None:
        if not self.usages:
            return None
        first = self.usages[0]
        return LLMUsage(provider=first.provider, model=first.model,
                        input_tokens=sum(u.input_tokens for u in self.usages),
                        output_tokens=sum(u.output_tokens for u in self.usages),
                        cost_usd=round(sum(u.cost_usd for u in self.usages), 6))


def _ground(raw: RawField | None, kind: str, words: list[dict], text: str) -> Match | None:
    if not raw or not raw.value or not raw.source_text:
        return None
    if not value_matches_source(raw.value, raw.source_text, kind):
        return None
    m = find_in_words(raw.source_text, words) if words else find_in_text(raw.source_text, text)
    parse = PARSERS.get(kind)
    if m and parse and words and parse(m.text) != parse(raw.value):
        return None  # fuzzy pe text, dar altă sumă/dată (ex. 14.209 vs 14.200)
    return m


def _parsed(raw: RawField, kind: str):
    parse = PARSERS.get(kind)
    return parse(raw.value) if parse else raw.value.strip()


class Functionar:
    name = "functionar"
    start_message = "Citesc documentele"

    async def run(self, case, ctx) -> AgentResult:
        paznic = ctx.scratch.get("paznic") or {}
        if not paznic:
            # dosar redat din fixture (rerun-demo), fără ieșirea reală a Paznicului → rezultatul de probă
            return await StubAgent(self.name, self.start_message, delay=2.0).run(case, ctx)

        calls = _Calls()
        findings: list[Finding] = []
        out = ctx.scratch.setdefault("functionar", {})

        async def one(doc: Document) -> list[Finding]:
            info = paznic.get(doc.id) or {}
            doc_findings, out[doc.id] = await self._document(case.id, doc, info.get("words") or [], info, calls)
            await ctx.emit("agent_progress", f"{SHORT_LABELS[doc.type]}: {len(doc.extracted or {})} câmpuri")
            return doc_findings

        for doc_findings in await asyncio.gather(*(one(d) for d in case.documents)):
            findings += doc_findings

        types = [SHORT_LABELS[d.type] for d in case.documents]
        summary = Finding(code="DOCS_CLASSIFIED", severity="info",
                          message=f"{len(types)} documente: {', '.join(types)}" if len(types) != 1
                          else f"1 document: {types[0]}")
        findings.insert(0, summary)
        if calls.blocked:
            kinds = ", ".join(sorted(calls.blocked))
            findings.append(Finding(code="PII_GATE_BLOCKED", severity="low",
                                    message=f"Poarta anti-PII a blocat un apel AI ({kinds})"))
        if calls.unavailable or calls.blocked:
            findings.append(Finding(code="EXTRACTION_RULES_ONLY", severity="info",
                                    message="AI indisponibil: unele câmpuri au fost citite doar după etichete"))
        return AgentResult(agent="functionar", status="done", findings=findings, llm_usage=calls.total_usage())

    async def _document(self, case_id: str, doc: Document, words: list[dict], paznic: dict,
                        calls: _Calls) -> tuple[list[Finding], dict]:
        lines = group_lines(words)
        words = ordered_words(lines)
        text = doc.redacted_text or "\n".join(line.text for line in lines)

        doc_type = "id_card" if paznic.get("is_id_card") else classify_by_keywords(text)
        offline = bool(paznic.get("cloud_blocked"))  # poză neclară: Paznicul nu garantează redactarea → fără cloud
        if not doc_type and not offline:
            r = await calls.ask(case_id, system=SYSTEM_CLASSIFY, prompt=text, json_schema=ClassifyOut, max_tokens=50)
            doc_type = r.doc_type if r else "unknown"
        doc_type = doc_type or "unknown"
        doc.type = doc_type
        schema = SCHEMAS.get(doc_type)
        if not schema:
            doc.extracted = {}
            return [], {"fields": {}, "statement": None}

        by_labels = extract_by_labels(doc_type, lines)
        llm = None if offline else await calls.ask(
            case_id, system=SYSTEM_EXTRACT.format(label=DOC_LABELS[doc_type]),
            prompt=text, json_schema=schema, max_tokens=1500)

        findings: list[Finding] = []
        extracted: dict[str, ExtractedValue] = {}
        evidence: dict[str, dict] = {}
        unredacted: list[str] = []
        for name in schema.model_fields:
            kind = FIELD_KINDS.get(name, "text")
            llm_raw = getattr(llm, name, None) if llm else None
            chosen = None
            for raw in (llm_raw, by_labels.get(name)):
                if (m := _ground(raw, kind, words, text)) and (value := _parsed(raw, kind)) is not None:
                    chosen = (raw, m, value)
                    break
            if chosen and name in IDENTIFIER_FIELDS and not is_label(chosen[2]):
                unredacted.append(name)  # Paznicul n-a recunoscut valoarea (ex. IBAN citit greșit de OCR)
            elif chosen:
                raw, m, value = chosen
                extracted[name] = ExtractedValue(value=value, source_text=raw.source_text)
                if m.bbox:
                    m = narrow_to_value(m, raw.value, words)
                    evidence[name] = {"page": m.page, "bbox": m.bbox}
            elif llm_raw and llm_raw.value:
                findings.append(Finding(
                    code="EXTRACTION_UNGROUNDED", severity="low",
                    message=f"Câmpul „{FIELD_RO.get(name, name)}” nu se regăsește în document; ignorat",
                    evidence=Evidence(doc_id=doc.id, field=name)))
        if unredacted:
            findings.append(Finding(
                code="UNREDACTED_IDENTIFIER", severity="info",
                message=f"Identificator neascuns de Paznic, nepreluat ({', '.join(unredacted)})",
                evidence=Evidence(doc_id=doc.id)))

        table = None
        if doc_type == "bank_statement":
            table = parse_statement(lines)
            for name, value in (("opening_balance", table.opening_balance), ("closing_balance", table.closing_balance)):
                if value is not None and name not in extracted:
                    extracted[name] = ExtractedValue(value=value, source_text=None)
            if table.closing_evidence:
                evidence["closing_balance"] = table.closing_evidence

        doc.extracted = extracted
        return findings, {"fields": evidence, "statement": table.to_dict() if table else None}
