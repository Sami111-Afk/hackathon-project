"""🛡️ Paznic — Narcis. Ascunde local datele personale, înainte ca orice să plece mai departe.

Pentru fiecare document: text + bbox-uri (OCR / strat PDF) → detecție (regex + cifre de control,
MRZ, ancore pe etichete) → etichete [CNP_1] + amprente HMAC → seif criptat → imagine redactată.
Ce rămâne pentru restul pipeline-ului: doc.redacted_text, doc.pages, case.fingerprints,
iar în ctx.scratch["paznic"][doc_id] cuvintele redactate cu bbox (pentru grounding-ul Funcționarului).
"""
import asyncio
import logging
from collections import Counter

from app.agents.paznic import detect, images, ocr, redact
from app.agents.paznic.validators import mrz_matches_cnp, parse_mrz_td2_line2
from app.agents.paznic.vault import vault
from app.agents.stubs import StubAgent
from app.config import settings
from app.core import pii_gate
from app.core.files import save_derived, sniff
from app.models import AgentResult, Evidence, Finding, PageInfo

log = logging.getLogger("orb.paznic")

KIND_RO = {"PERSOANA": "nume", "CNP": "CNP", "IBAN": "IBAN", "ADRESA": "adresă", "MRZ": "MRZ", "CUI": "CUI",
           "TELEFON": "telefon", "EMAIL": "email", "SERIE": "serie buletin", "NR": "nr. buletin", "FIRMA": "firmă"}
CHECKSUM_FINDINGS = {
    "CNP": ("CNP_CHECKSUM_INVALID", "high", "CNP cu cifră de control invalidă"),
    "IBAN": ("IBAN_CHECKSUM_INVALID", "medium", "IBAN cu cifre de control invalide"),
    "CUI": ("CUI_CHECKSUM_INVALID", "medium", "CUI cu cifră de control invalidă"),
    "MRZ": ("MRZ_INVALID", "high", "Zona MRZ a buletinului are cifre de control invalide"),
}


def _evidence(doc_id: str, ext: ocr.Extraction, span: detect.Span, label: str) -> Evidence:
    words = ext.words_for_span(span.start, span.end)
    if not words:
        return Evidence(doc_id=doc_id, field=label)
    xs0, ys0, xs1, ys1 = zip(*(w.bbox for w in words), strict=True)
    return Evidence(doc_id=doc_id, page=words[0].page, bbox=[min(xs0), min(ys0), max(xs1), max(ys1)], field=label)


def _is_id_card(text: str, spans: list[detect.Span]) -> bool:
    return "CARTE DE IDENTITATE" in text.upper() or any(s.kind == "MRZ" for s in spans)


class Paznic:
    name = "paznic"
    start_message = "Ascund datele personale"

    async def run(self, case, ctx) -> AgentResult:
        if not any(ctx.files.get(d.id) for d in case.documents):
            # dosar redat din fixture (rerun-demo), fără fișiere reale → rezultatul de probă
            return await StubAgent(self.name, self.start_message, delay=1.5).run(case, ctx)
        secret =settings.arena_hmac_secret if case.source == "arena" else settings.hmac_secret
        redactor = redact.CaseRedactor(secret=secret)
        findings: list[Finding] = []
        hidden: Counter = Counter()
        zones = 0
        scratch = ctx.scratch.setdefault("paznic", {})

        # faza 1: citim toate documentele și aflăm numele persoanelor (din etichete, pe orice document)
        extracted: list[tuple] = []
        known_names: set[str] = set()
        for doc in case.documents:
            data = ctx.files.get(doc.id)
            kind = sniff(data) if data else None
            if not kind:
                findings.append(Finding(code="DOCUMENT_UNREADABLE", severity="low",
                                        message="Un document nu a putut fi citit", evidence=Evidence(doc_id=doc.id)))
                continue
            try:
                ext = await asyncio.to_thread(ocr.extract, data, kind[0])
            except ocr.OCRUnavailable:
                log.error("OCR indisponibil pentru %s", doc.id)
                raise  # fără OCR nu putem garanta redactarea → agentul pică, Compliance marchează „incomplet”
            how = "strat text" if ext.source == "pdf_text" else "OCR"
            await ctx.emit("agent_progress", f"Citit {doc.filename} ({how})")
            for s in detect.find_all(ext.text):
                if s.kind == "PERSOANA":
                    known_names |= redact.name_tokens(s.value)
            extracted.append((doc, ext))

        # faza 2: redactăm, ascunzând numele oriunde apar în dosar
        for doc, ext in extracted:
            spans = detect.find_all(ext.text, known_names)
            replacements = redactor.label_spans(spans)
            doc.redacted_text = redact.apply(ext.text, replacements)
            doc.pages = [PageInfo(page=p.page, width=p.image.width, height=p.image.height) for p in ext.pages]
            hidden.update(r.span.kind for r in replacements)

            for r in replacements:
                if r.span.valid is False and r.span.kind in CHECKSUM_FINDINGS:
                    code, sev, msg = CHECKSUM_FINDINGS[r.span.kind]
                    findings.append(Finding(code=code, severity=sev, message=f"{msg} ({r.label})",
                                            evidence=_evidence(doc.id, ext, r.span, r.label)))
            findings.extend(self._mrz_vs_cnp(doc.id, ext, replacements))
            if detect.find_prompt_injection(ext.text):
                findings.append(Finding(code="PROMPT_INJECTION_SUSPECTED", severity="high",
                                        message="Documentul conține instrucțiuni adresate AI-ului",
                                        evidence=Evidence(doc_id=doc.id)))

            id_card = _is_id_card(ext.text, spans)
            zones += len(images.ID_CARD_ZONES) if id_card else 0
            redacted = await asyncio.to_thread(images.redact_pages, ext, replacements, id_card)
            for page_no, img in enumerate(redacted, start=1):
                png = await asyncio.to_thread(images.to_png, img)
                save_derived(case.id, doc.id, "redacted", page_no, png)
            scratch[doc.id] = {"source": ext.source, "is_id_card": id_card,
                               "words": redacted_words(doc.id, ext, replacements)}

        values = dict(redactor.vault)
        await asyncio.to_thread(vault.put, case.id, values, False)
        # poarta anti-PII se actualizează pe loop (nu din thread: scan() poate itera setul în paralel)
        pii_gate.register_vault_values(case.id, [x for vals in values.values() for x in vals])
        case.fingerprints = redactor.finalize_fingerprints()
        case.applicant_token = (case.fingerprints.get("cnp") or case.fingerprints.get("name") or [None])[0]

        total = sum(hidden.values()) + zones
        parts = ", ".join(f"{KIND_RO.get(k, k.lower())} ×{n}" for k, n in hidden.most_common())
        if zones:
            parts += f", zone buletin ×{zones}"
        findings.insert(0, Finding(code="PII_REDACTED", severity="info",
                                   message=f"{total} valori personale ascunse ({parts or 'nimic găsit'})"))
        return AgentResult(agent="paznic", status="done", findings=findings,
                           artifacts={"redacted_view": "redacted"})

    @staticmethod
    def _mrz_vs_cnp(doc_id, ext, replacements) -> list[Finding]:
        cnps = [r.span.value for r in replacements if r.span.kind == "CNP" and r.span.valid]
        out = []
        for r in replacements:
            if r.span.kind != "MRZ" or not r.span.valid:
                continue
            mrz = parse_mrz_td2_line2(r.span.value)
            if mrz and cnps and not any(mrz_matches_cnp(mrz, c) for c in cnps):
                out.append(Finding(code="MRZ_CNP_MISMATCH", severity="high",
                                   message="Data nașterii / sexul din MRZ nu corespund cu CNP-ul",
                                   evidence=_evidence(doc_id, ext, r.span, r.label)))
        return out


def redacted_words(doc_id: str, ext: ocr.Extraction, replacements: list[redact.Replacement]) -> list[dict]:
    """Cuvintele documentului cu bbox, în care fiecare valoare PII e înlocuită de eticheta ei
    (cu bbox-ul reunit) — Funcționarul poate face grounding fără să vadă valorile."""
    hidden: set[int] = set()
    out = []
    for r in replacements:
        idx = {ext.char_word[i] for i in range(r.span.start, min(r.span.end, len(ext.char_word)))} - {-1}
        hidden |= idx
        ev = _evidence(doc_id, ext, r.span, r.label)
        if ev.bbox:
            out.append({"text": r.label, "page": ev.page, "bbox": ev.bbox})
    out += [{"text": w.text, "page": w.page, "bbox": list(w.bbox)}
            for i, w in enumerate(ext.words) if i not in hidden]
    return sorted(out, key=lambda w: (w["page"], round(w["bbox"][1] / 10), w["bbox"][0]))
