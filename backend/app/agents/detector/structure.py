"""Structura fișierului: metadate PDF, actualizări incrementale, imagini din PDF, EXIF.

Tot local și determinist; semnalele de aici nu au nevoie de OCR sau de LLM.
"""
import io
import re
from dataclasses import dataclass, field

from PIL import Image

# produse de un editor de imagini / grafică, nu de sistemul unei bănci sau al unui angajator
EDITORS = re.compile(r"gimp|photoshop|paint\.net|\bmspaint\b|pixelmator|affinity|krita|inkscape|canva|"
                     r"photopea|corel", re.I)


@dataclass
class PdfInfo:
    producer: str = ""
    creator: str = ""
    eof_count: int = 0
    linearized: bool = False
    page_images: dict[int, list[Image.Image]] = field(default_factory=dict)  # pagina → JPEG-uri


def editor_name(text: str) -> str | None:
    m = EDITORS.search(text or "")
    return m.group(0) if m else None


def read_pdf(data: bytes) -> PdfInfo:
    from pypdf import PdfReader

    info = PdfInfo(eof_count=data.count(b"%%EOF"), linearized=b"/Linearized" in data[:2048])
    reader = PdfReader(io.BytesIO(data))
    meta = reader.metadata or {}
    info.producer = str(meta.get("/Producer") or "")
    info.creator = str(meta.get("/Creator") or "")
    for no, page in enumerate(reader.pages, start=1):
        jpegs = []
        try:
            for im in page.images:
                if im.data[:3] == b"\xff\xd8\xff":  # doar JPEG-urile au ce analiza ELA
                    jpegs.append(Image.open(io.BytesIO(im.data)))
        except Exception:  # imagini cu filtre exotice: le sărim, nu dărâmăm agentul
            pass
        info.page_images[no] = jpegs
    return info


def incremental_updates(info: PdfInfo) -> int:
    """Câte salvări s-au adăugat peste fișierul original (un PDF linearizat are legitim 2 %%EOF)."""
    return max(0, info.eof_count - (2 if info.linearized else 1))


def exif_software(img: Image.Image) -> str:
    try:
        return str(img.getexif().get(0x0131) or "")  # tag-ul Software
    except Exception:
        return ""
