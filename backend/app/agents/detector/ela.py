"""Urme de editare în JPEG: „fantoma JPEG” (double compression) + harta ELA pentru UI.

O zonă lipită/rescrisă peste un JPEG nu mai poartă compresia originală. Re-salvăm imaginea
la calitatea q* a primei compresii: zonele care au trecut deja prin q* se schimbă foarte
puțin („fantoma”), zona editată se schimbă ca orice conținut nou. ELA-ul clasic nu merge
pe documente: marginile textului au eroare mare peste tot și acoperă semnalul.

Pe blocuri de 16×16 px: r = D(q*) / medie(D(q*−5), D(q*+5)), D = eroarea pătratică la re-salvare.
Ferestre pe rânduri de text, z-score robust (median/MAD) → zonele cu z mare sunt anomalii.
Fără dublă compresie la o calitate diferită de ultima salvare nu raportăm nimic: o singură
salvare nu are cu ce compara, iar conturul ștampilelor/antetele colorate ar ieși fals pozitive.
"""
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance

BLOCK = 16
WIN_H, WIN_W = 3, 8          # fereastra ≈ un rând de text (48×128 px)
Z_ANOMALY = 6.0              # pragul pe z robust; documentele curate rămân sub ~4
MIN_DIP = 0.75               # mediana r la q* sub prag = imaginea a fost compresată la q* înainte
QUALITIES = range(55, 96, 5)
# tabelul standard de luminanță JPEG (IJG), media celor 64 de valori
_STD_LUMA_MEAN = 57.625


@dataclass
class Region:
    bbox: tuple[int, int, int, int]  # pixeli în imaginea analizată
    z: float


@dataclass
class ElaResult:
    first_quality: int | None   # q* estimat; None = fără urme de dublă compresie
    regions: list[Region]


def _resave(gray: Image.Image, q: int) -> np.ndarray:
    buf = io.BytesIO()
    gray.save(buf, "JPEG", quality=q)
    return np.asarray(Image.open(io.BytesIO(buf.getvalue())), dtype=np.float32)


def _blocks(a: np.ndarray) -> np.ndarray:
    h, w = a.shape[0] // BLOCK * BLOCK, a.shape[1] // BLOCK * BLOCK
    return a[:h, :w].reshape(h // BLOCK, BLOCK, w // BLOCK, BLOCK).sum(axis=(1, 3))


def _window_sum(a: np.ndarray) -> np.ndarray:
    c = np.pad(a, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    return c[WIN_H:, WIN_W:] - c[:-WIN_H, WIN_W:] - c[WIN_H:, :-WIN_W] + c[:-WIN_H, :-WIN_W]


def last_quality(img: Image.Image) -> int | None:
    """Calitatea ultimei salvări, estimată din tabelul de cuantizare (formula IJG)."""
    tables = getattr(img, "quantization", None)
    if not tables or 0 not in tables:
        return None
    scale = sum(tables[0]) / 64 / _STD_LUMA_MEAN * 100
    return round((200 - scale) / 2 if scale <= 100 else 5000 / scale)


def analyze(img: Image.Image) -> ElaResult:
    """`img` = imaginea deschisă direct din JPEG (cu tabelele de cuantizare), nu una convertită."""
    q_last = last_quality(img)
    if q_last is None:
        return ElaResult(None, [])
    gray = img.convert("L")
    g = np.asarray(gray, dtype=np.float32)
    if g.shape[0] < BLOCK * WIN_H * 4 or g.shape[1] < BLOCK * WIN_W * 4:
        return ElaResult(None, [])
    err = {q: _blocks((g - _resave(gray, q)) ** 2) for q in QUALITIES}
    # doar blocurile cu conținut (hârtia albă nu spune nimic despre compresie)
    content = _blocks(np.abs(np.diff(g, axis=1, prepend=g[:, :1]))) > 2 * BLOCK * BLOCK

    if content.sum() < WIN_H * WIN_W * 4:
        return ElaResult(None, [])
    dips = {q: float(np.median(err[q][content] / ((err[q - 5][content] + err[q + 5][content]) / 2 + 1e-6)))
            for q in QUALITIES if q - 5 in err and q + 5 in err and q < q_last - 3}
    if not dips:
        return ElaResult(None, [])
    q_first = min(dips, key=dips.get)
    if dips[q_first] > MIN_DIP:
        return ElaResult(None, [])

    c = content.astype(np.float32)
    num = _window_sum(err[q_first] * c)
    den = _window_sum((err[q_first - 5] + err[q_first + 5]) / 2 * c)
    filled = _window_sum(c) >= WIN_H * WIN_W * 0.3
    ratio = np.where(filled, num / (den + 1e-6), np.nan)
    if np.count_nonzero(filled) < 20:
        return ElaResult(q_first, [])
    med = np.nanmedian(ratio)
    mad = np.nanmedian(np.abs(ratio - med)) * 1.4826 + 1e-9
    z = np.nan_to_num((ratio - med) / mad, nan=0.0)
    return ElaResult(q_first, _regions(z, content))


def _regions(z: np.ndarray, content: np.ndarray) -> list[Region]:
    """Ferestrele peste prag → blocuri marcate → componente conexe → dreptunghiuri."""
    hot = np.zeros(content.shape, dtype=bool)
    score = np.zeros(content.shape, dtype=np.float32)
    for y, x in zip(*np.nonzero(z > Z_ANOMALY), strict=True):
        hot[y:y + WIN_H, x:x + WIN_W] |= content[y:y + WIN_H, x:x + WIN_W]
        score[y:y + WIN_H, x:x + WIN_W] = np.maximum(score[y:y + WIN_H, x:x + WIN_W], z[y, x])

    seen = np.zeros_like(hot)
    regions = []
    for sy, sx in zip(*np.nonzero(hot), strict=True):
        if seen[sy, sx]:
            continue
        stack, cells = [(sy, sx)], []
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < hot.shape[0] and 0 <= nx < hot.shape[1] and hot[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        ys, xs = zip(*cells, strict=True)
        bbox = (int(min(xs)) * BLOCK, int(min(ys)) * BLOCK, (int(max(xs)) + 1) * BLOCK, (int(max(ys)) + 1) * BLOCK)
        regions.append(Region(bbox, round(float(max(score[y, x] for y, x in cells)), 1)))
    return sorted(_merge(regions), key=lambda r: -r.z)[:3]


def _merge(regions: list[Region], gap: int = 3 * BLOCK) -> list[Region]:
    """Zonele la mai puțin de `gap` px una de alta sunt aceeași editare (ex. o ștampilă rotundă)."""
    out: list[Region] = []
    for r in regions:
        for i, o in enumerate(out):
            a, b = r.bbox, o.bbox
            if a[0] - gap < b[2] and b[0] - gap < a[2] and a[1] - gap < b[3] and b[1] - gap < a[3]:
                out[i] = Region((min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])), max(r.z, o.z))
                return _merge(out + regions[regions.index(r) + 1:], gap)
        out.append(r)
    return out


def ela_map(img: Image.Image, regions: list[Region], size: tuple[int, int] | None = None) -> Image.Image:
    """Harta ELA clasică (re-salvare la q90, diferența amplificată) + zonele găsite încadrate."""
    rgb = img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, "JPEG", quality=90)
    diff = ImageChops.difference(rgb, Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
    out = ImageEnhance.Brightness(diff).enhance(12.0)
    d = ImageDraw.Draw(out)
    for r in regions:
        d.rectangle(r.bbox, outline=(255, 40, 40), width=4)
    return out.resize(size) if size and size != out.size else out
