"""🔬 Detector — Narcis. Urme de editare în fișiere, fără LLM (ARCHITECTURE.md §5).

  JPEG (poză / scan)     → fantoma JPEG pe blocuri (ela.py): zona rescrisă peste un JPEG vechi
  PDF                    → producer/creator de editor de imagini, salvări incrementale,
                           JPEG-urile din pagini trec prin aceeași analiză
  EXIF                   → Software = editor de imagini

ELA e semnal slab (plafonat în Compliance); finding-urile spun pe ce câmp a căzut zona,
dacă Funcționarul a lăsat bbox-urile în ctx.scratch["functionar"].
Harta ELA: files.save_derived(..., "ela", ...) → ?view=ela în pagina Dosar.
"""
import asyncio
import io
import logging

from PIL import Image

from app.agents.detector import ela, structure
from app.core.files import save_derived, to_png
from app.models import AgentResult, Evidence, Finding

log = logging.getLogger("orb.detector")

SEVERITY_RISK = {"info": 0.0, "low": 0.1, "medium": 0.3, "high": 0.6, "critical": 0.85}

FIELD_RO = {"net_salary": "net pay", "gross_salary": "gross pay", "closing_balance": "closing balance",
            "opening_balance": "opening balance", "employer_name": "employer name", "employer_cui": "CUI",
            "full_name": "name", "cnp": "CNP"}


def _overlap(a, b) -> float:
    """Cât din zona `a` cade peste `b` (0..1)."""
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    area = (a[2] - a[0]) * (a[3] - a[1])
    return w * h / area if w > 0 and h > 0 and area > 0 else 0.0


def _field_at(fields: dict, page: int, bbox) -> str | None:
    best, score = None, 0.0
    for name, box in fields.items():
        if (box or {}).get("page") == page and box.get("bbox"):
            s = max(_overlap(bbox, box["bbox"]), _overlap(box["bbox"], bbox))
            if s > score:
                best, score = name, s
    return best if score >= 0.3 else None


def _scale(bbox, src_size, dst_size) -> list[float]:
    sx, sy = dst_size[0] / src_size[0], dst_size[1] / src_size[1]
    return [round(bbox[0] * sx), round(bbox[1] * sy), round(bbox[2] * sx), round(bbox[3] * sy)]


class Detector:
    name = "detector"
    start_message = "Looking for traces of editing"

    async def run(self, case, ctx) -> AgentResult:
        findings: list[Finding] = []
        ela_docs: list[str] = []
        flagged: list[str] = []
        fields_by_doc = ctx.scratch.get("functionar") or {}

        for doc in case.documents:
            data = ctx.files.get(doc.id)
            mime = ctx.mime(doc.id)
            if not data or not mime:
                continue
            fields = (fields_by_doc.get(doc.id) or {}).get("fields") or {}
            pages = await asyncio.to_thread(ctx.pages, doc.id)
            sizes = {i: p.size for i, p in enumerate(pages, start=1)}

            if mime == "application/pdf":
                info = await asyncio.to_thread(structure.read_pdf, data)
                findings += self._pdf_findings(doc.id, info)
                images = {no: imgs[0] for no, imgs in info.page_images.items()
                          if len(imgs) == 1 and no in sizes and self._covers_page(imgs[0].size, sizes[no])}
            elif mime == "image/jpeg":
                img = Image.open(io.BytesIO(data))
                software = structure.exif_software(img)
                tool = structure.editor_name(software)
                if tool:
                    findings.append(Finding(code="EXIF_EDITOR", severity="low",
                                            message=f"The image was saved from an editor ({tool})",
                                            evidence=Evidence(doc_id=doc.id)))
                images = {1: img}
            else:
                continue  # PNG etc.: fără compresie JPEG, fantoma nu are ce arăta

            for page_no, img in images.items():
                result = await asyncio.to_thread(ela.analyze, img)
                located = [(r, _scale(r.bbox, img.size, sizes[page_no])) for r in result.regions]
                located = [(r, bbox, _field_at(fields, page_no, bbox)) for r, bbox in located]
                # zona peste un câmp citit de Funcționar întâi; ELA e semnal slab → o singură zonă „medium”
                located.sort(key=lambda x: (x[2] is None, -x[0].z))
                for i, (region, bbox, field) in enumerate(located):
                    where = f"The {FIELD_RO.get(field, field)} area" if field else "An area of the document"
                    findings.append(Finding(
                        code="ELA_ANOMALY", severity="medium" if i == 0 else "info",
                        message=f"{where} lacks the trace of the original compression "
                                f"(rewritten after the first save, z={region.z:g})",
                        evidence=Evidence(doc_id=doc.id, page=page_no, bbox=bbox, field=field)))
                    if doc.id not in flagged:
                        flagged.append(doc.id)
                heatmap = await asyncio.to_thread(ela.ela_map, img, result.regions, sizes[page_no])
                png = await asyncio.to_thread(to_png, heatmap)
                save_derived(case.id, doc.id, "ela", page_no, png)
                if doc.id not in ela_docs:
                    ela_docs.append(doc.id)
            await ctx.emit("agent_progress", f"{doc.id}: checked")

        keep = 1.0
        for f in findings:
            keep *= 1 - SEVERITY_RISK[f.severity]
        shown = (flagged or ela_docs)[:1]
        artifacts = {"ela_image": f"/api/cases/{case.id}/documents/{shown[0]}/image?view=ela"} if shown else {}
        return AgentResult(agent="detector", status="done", risk=round(1 - keep, 4), findings=findings,
                           artifacts=artifacts)

    @staticmethod
    def _covers_page(img_size, page_size) -> bool:
        """Imaginea e toată pagina (scan / export din editor) → coordonatele se pot scala direct."""
        return abs(img_size[0] / img_size[1] - page_size[0] / page_size[1]) < 0.02

    @staticmethod
    def _pdf_findings(doc_id: str, info: structure.PdfInfo) -> list[Finding]:
        out = []
        tool = structure.editor_name(info.producer) or structure.editor_name(info.creator)
        if tool:
            out.append(Finding(code="PDF_EDITOR_PRODUCER", severity="medium",
                               message=f"The document was produced by an image editor "
                                       f"({info.producer or info.creator}), not by a bank system",
                               evidence=Evidence(doc_id=doc_id)))
        updates = structure.incremental_updates(info)
        if updates:
            out.append(Finding(code="PDF_INCREMENTAL_UPDATE", severity="medium",
                               message=f"The PDF was modified after issuance "
                                       f"({updates} saves added on top of the original)",
                               evidence=Evidence(doc_id=doc_id)))
        return out
