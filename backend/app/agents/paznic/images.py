"""Imaginea redactată: dreptunghiuri negre pe bbox-urile PII + zonele de șablon (ARCHITECTURE.md §4, pașii 6, 10).

Zonele de șablon (poză, semnătură, MRZ pe buletin) se maschează indiferent de OCR.
Coordonatele sunt fracții din pagină — de ajustat pe documentele generate de Lorena.
"""
import io

from PIL import Image, ImageDraw

from app.agents.paznic.ocr import Extraction
from app.agents.paznic.redact import Replacement

PAD = 4  # pixeli în jurul fiecărui cuvânt, ca să nu rămână margini de litere

# x0, y0, x1, y1 ca fracții din lățimea/înălțimea paginii
ID_CARD_ZONES = {
    "poza": (0.02, 0.18, 0.32, 0.78),
    "semnatura": (0.33, 0.62, 0.62, 0.74),
    "mrz": (0.0, 0.76, 1.0, 1.0),
}


def redact_pages(ext: Extraction, replacements: list[Replacement], is_id_card: bool) -> list[Image.Image]:
    """O imagine redactată per pagină (copii; originalele rămân neatinse)."""
    out = []
    for p in ext.pages:
        img = p.image.copy()
        draw = ImageDraw.Draw(img)
        for r in replacements:
            for w in ext.words_for_span(r.span.start, r.span.end):
                if w.page == p.page:
                    x0, y0, x1, y1 = w.bbox
                    draw.rectangle((x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD), fill="black")
        if is_id_card and p.page == 1:
            W, H = img.size
            for x0, y0, x1, y1 in ID_CARD_ZONES.values():
                draw.rectangle((x0 * W, y0 * H, x1 * W, y1 * H), fill="black")
        out.append(img)
    return out


def to_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
