"""Text + bbox-uri pe cuvânt. Vezi ARCHITECTURE.md §4, pașii 1–2.

PDF digital → stratul de text (pypdfium2), exact. Imagine → Tesseract `ron`, `--psm 6`.
Coordonatele sunt în pixeli pe imaginea paginii (PDF randat la RENDER_DPI), ca bbox-urile
să se potrivească direct cu imaginea redactată și cu ce afișează frontend-ul.
CPU-intensiv → se apelează cu asyncio.to_thread.
"""
import io
from dataclasses import dataclass, field

from PIL import Image

from app.config import settings

RENDER_DPI = 200
OCR_MIN_WIDTH = 2000  # sub atât, mărim imaginea (~300 DPI pe A4) — Tesseract greșește mult pe imagini mici


class OCRUnavailable(RuntimeError):
    pass


@dataclass
class Word:
    text: str
    page: int
    bbox: tuple[float, float, float, float]  # x0, y0, x1, y1 în pixeli
    conf: float = 100.0                       # încrederea Tesseract (0–100); 100 pentru stratul de text PDF


@dataclass
class PageImage:
    page: int
    image: Image.Image


@dataclass
class Extraction:
    text: str
    words: list[Word]
    char_word: list[int]                     # pentru fiecare caracter din text: indexul cuvântului sau -1
    pages: list[PageImage] = field(default_factory=list)
    source: str = "ocr"                      # "pdf_text" | "ocr"

    def quality(self) -> float:
        """Încrederea medie a OCR-ului (0–100), ponderată cu lungimea cuvintelor. PDF digital = 100."""
        if self.source == "pdf_text":
            return 100.0
        scored = [(w.conf, len(w.text)) for w in self.words if any(c.isalnum() for c in w.text)]
        total = sum(n for _, n in scored)
        return round(sum(c * n for c, n in scored) / total, 1) if total else 0.0

    def words_for_span(self, start: int, end: int) -> list[Word]:
        idx = sorted({self.char_word[i] for i in range(start, min(end, len(self.char_word))) if self.char_word[i] >= 0})
        return [self.words[i] for i in idx]


def _assemble(lines: list[list[Word]]) -> tuple[str, list[Word], list[int]]:
    """Cuvintele unite cu spații, liniile cu \\n, plus maparea caracter → cuvânt."""
    parts: list[str] = []
    char_word: list[int] = []
    words: list[Word] = []
    for li, line in enumerate(lines):
        if li:
            parts.append("\n")
            char_word.append(-1)
        for wi, w in enumerate(line):
            if wi:
                parts.append(" ")
                char_word.append(-1)
            parts.append(w.text)
            char_word.extend([len(words)] * len(w.text))
            words.append(w)
    return "".join(parts), words, char_word


# ── PDF ──

def _pdf_lines(data: bytes) -> tuple[list[list[Word]], list[PageImage]]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    scale = RENDER_DPI / 72
    lines: list[list[Word]] = []
    pages: list[PageImage] = []
    for pno in range(len(pdf)):
        page = pdf[pno]
        height = page.get_height()
        pages.append(PageImage(pno + 1, page.render(scale=scale).to_pil().convert("RGB")))
        tp = page.get_textpage()
        n = tp.count_chars()
        line: list[Word] = []
        cur, box = "", None
        for i in range(n):
            ch = tp.get_text_range(i, 1)
            if ch.isspace() or not ch:
                if cur:
                    line.append(Word(cur, pno + 1, box))
                    cur, box = "", None
                if ch in ("\n", "\r") and line:
                    lines.append(line)
                    line = []
                continue
            left, bottom, right, top = tp.get_charbox(i)
            b = (left * scale, (height - top) * scale, right * scale, (height - bottom) * scale)
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
            cur += ch
        if cur:
            line.append(Word(cur, pno + 1, box))
        if line:
            lines.append(line)
    return lines, pages


# ── Imagine ──

def ocr_available() -> bool:
    """Tesseract instalat, cu limba română."""
    try:
        import pytesseract
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        return "ron" in pytesseract.get_languages(config="")
    except Exception:
        return False


def _ocr_lines(img: Image.Image, page: int) -> list[list[Word]]:
    if not ocr_available():
        raise OCRUnavailable("Tesseract is not installed, lacks the \"ron\" language, or TESSERACT_CMD is wrong")
    import pytesseract

    factor = max(1.0, OCR_MIN_WIDTH / img.width)
    work = img.convert("L")
    if factor > 1:
        work = work.resize((round(img.width * factor), round(img.height * factor)), Image.LANCZOS)
    d = pytesseract.image_to_data(work, lang="ron", config="--psm 6", output_type=pytesseract.Output.DICT)
    grouped: dict[tuple[int, int, int], list[Word]] = {}
    for i, text in enumerate(d["text"]):
        text = text.strip()
        if not text or float(d["conf"][i]) < 0:
            continue
        x, y, w, h = (d[k][i] / factor for k in ("left", "top", "width", "height"))
        key = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        grouped.setdefault(key, []).append(Word(text, page, (x, y, x + w, y + h), float(d["conf"][i])))
    return [grouped[k] for k in sorted(grouped)]


def extract(data: bytes, kind: str) -> Extraction:
    """kind = extensia din files.sniff: "pdf" | "png" | "jpg"."""
    if kind == "pdf":
        lines, pages = _pdf_lines(data)
        if sum(len(line) for line in lines) >= 5:  # PDF digital cu strat de text
            text, words, char_word = _assemble(lines)
            return Extraction(text, words, char_word, pages, source="pdf_text")
        # PDF scanat → OCR pe paginile randate
        lines = [ln for p in pages for ln in _ocr_lines(p.image, p.page)]
        text, words, char_word = _assemble(lines)
        return Extraction(text, words, char_word, pages, source="ocr")
    img = Image.open(io.BytesIO(data))
    img.load()
    img = img.convert("RGB")
    text, words, char_word = _assemble(_ocr_lines(img, 1))
    return Extraction(text, words, char_word, [PageImage(1, img)], source="ocr")
