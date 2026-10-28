"""Imaginea redactată: dreptunghiuri negre pe bbox-urile PII + zonele de șablon (ARCHITECTURE.md §4, pașii 6, 10).

Zonele de șablon (poză, semnătură, MRZ pe buletin) se maschează indiferent de OCR.
Coordonatele sunt fracții din pagină, luate din șablonul generatorului (data/generator/build_demo.py,
`id_card`, 1600×1010): poza la x 40–400, y 200–660; textul începe la x=440; MRZ de la y=820.
"""
import io

from PIL import Image, ImageDraw

from app.agents.paznic.ocr import Extraction
from app.agents.paznic.redact import Replacement

PAD = 4  # pixeli în jurul fiecărui cuvânt, ca să nu rămână margini de litere

# x0, y0, x1, y1 ca fracții din lățimea/înălțimea paginii
# (zonele nu ating coloana de text de la x=440, altfel ascund etichetele și strică grounding-ul)
ID_CARD_ZONES = {
    "poza": (0.02, 0.19, 0.26, 0.665),
    "semnatura": (0.02, 0.665, 0.26, 0.80),  # sub poză, unde o are buletinul real; zona e goală în șablon
    "mrz": (0.0, 0.805, 1.0, 1.0),
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
