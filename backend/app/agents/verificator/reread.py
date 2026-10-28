"""Recitirea unei sume de pe imagine, înainte de a acuza pe baza ei.

OCR-ul de pagină (Paznic, Tesseract `--psm 6`) mai greșește câte o cifră (benchmark: 7.952 citit 1.952).
Când un calcul nu iese, decupăm DOAR zona sumei, o mărim și o citim din nou doar cu cifre, în 6 feluri
(2 variante de contrast × 3 moduri Tesseract). Tesseract e inconsecvent pe decupaje mici, așa că votăm:
acceptăm o valoare doar dacă iese de cel puțin 2 ori și mai des decât oricare alta. Votăm pe MĂRIME:
modurile 8/13 adaugă des un „-” fals, iar semnul îl știm oricum din citirea inițială (coloana sumei).

Totul local (zona sumei nu pleacă nicăieri). Coordonatele sunt cele ale Paznicului: pixeli pe imaginea
originală, PDF-ul randat la paznic.ocr.RENDER_DPI. CPU-intensiv → se apelează din asyncio.to_thread.
"""
import io
import logging
import re
from collections import Counter

from PIL import Image, ImageOps

from app.core.files import sniff

log = logging.getLogger("orb.verificator")

PAD_PX = 8
UPSCALE = 3
BORDER_PX = 30  # Tesseract taie cifrele lipite de margine („7.952” → „952”) → bordură albă în jurul decupajului
WHITELIST = "-c tessedit_char_whitelist=0123456789.,-"
PSMS = (7, 8, 13)  # o linie, un cuvânt, linie „brută”
MIN_VOTES = 2  # modurile 8/13 pierd des virgula (nu votează); două citiri identice, fără egalitate


def _page_images(data: bytes) -> list[Image.Image]:
    from app.agents.paznic.ocr import RENDER_DPI

    kind = sniff(data)
    if kind and kind[0] == "pdf":
        import pypdfium2 as pdfium

        pdf = pdfium.PdfDocument(data)
        return [pdf[i].render(scale=RENDER_DPI / 72).to_pil().convert("RGB") for i in range(len(pdf))]
    return [Image.open(io.BytesIO(data)).convert("RGB")]


_AMOUNT_RX = re.compile(r"(\d{1,3}(?:[.,]\d{3})+|\d+)[.,](\d{2})")


def parse_ocr_amount(text: str) -> float | None:
    """„9.547,50” și „9,547.50” (Tesseract trece des pe format englezesc) → 9547.5. Ultimul separator urmat de
    exact 2 cifre e zecimala; acceptăm doar sume complete, cu bani — altfel None (nu votează)."""
    m = _AMOUNT_RX.fullmatch(text.strip().strip(" -.,"))
    if not m:
        return None
    return float(re.sub(r"[.,]", "", m.group(1)) + "." + m.group(2))


def read_amount(img: Image.Image, bbox: list[float]) -> float | None:
    """Mărimea sumei din chenar (fără semn), sau None dacă citirile nu dau o majoritate clară."""
    import pytesseract

    x0, y0, x1, y1 = bbox
    pad_x = max(PAD_PX, int((y1 - y0) * 0.4))  # chenarul OCR e uneori mai îngust decât prima cifră
    box = (max(0, int(x0) - pad_x), max(0, int(y0) - PAD_PX),
           min(img.width, int(x1) + pad_x), min(img.height, int(y1) + PAD_PX))
    if box[2] - box[0] < 4 or box[3] - box[1] < 4:
        return None
    gray = img.crop(box).convert("L")
    gray = gray.resize((gray.width * UPSCALE, gray.height * UPSCALE), Image.LANCZOS)
    variants = [ImageOps.expand(v, BORDER_PX, fill=255)
                for v in (ImageOps.autocontrast(gray), gray.point(lambda p: 255 if p > 150 else 0))]
    votes: Counter = Counter()
    for v in variants:
        for psm in PSMS:
            value = parse_ocr_amount(pytesseract.image_to_string(v, config=f"--psm {psm} {WHITELIST}"))
            if value is not None:
                votes[abs(value)] += 1
    ranked = votes.most_common(2)
    if not ranked or ranked[0][1] < MIN_VOTES or (len(ranked) > 1 and ranked[1][1] == ranked[0][1]):
        return None
    return ranked[0][0]


class Rereader:
    """Recitește sume din fișierele dosarului; paginile se randează o singură dată."""

    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = files
        self._pages: dict[str, list[Image.Image]] = {}

    @staticmethod
    def available() -> bool:
        try:
            from app.agents.paznic.ocr import ocr_available
        except ImportError:
            return False
        return ocr_available()

    def amount(self, doc_id: str, page: int | None, bbox: list[float] | None) -> float | None:
        data = self.files.get(doc_id)
        if not data or not bbox:
            return None
        try:
            if doc_id not in self._pages:
                self._pages[doc_id] = _page_images(data)
            pages = self._pages[doc_id]
            return read_amount(pages[(page or 1) - 1], bbox)
        except Exception:  # recitirea e o confirmare în plus; dacă pică, rămâne citirea inițială
            log.warning("recitirea unei sume a eșuat pentru %s", doc_id)
            return None
