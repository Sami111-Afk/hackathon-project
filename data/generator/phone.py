"""Degradări „poză de telefon”: documentul fotografiat pe masă, nu scanat.

Față de degrade() din scripts/benchmark_pipeline.py (scanare ușor proastă), aici adăugăm ce strică OCR-ul
în viața reală: perspectivă (telefonul nu e paralel cu foaia), rotație ±3°, fundal în jurul foii,
lumină neuniformă și umbra mâinii/telefonului, nuanță de culoare, zgomot de senzor, blur (focus sau mișcare)
și JPEG-ul telefonului (q 60–80).

phone_photo(img, rng) întoarce (imaginea, parametrii folosiți) — parametrii merg în etichetele .json.
"""
import random

import numpy as np
from PIL import Image, ImageFilter

from data.generator.build_demo import jpeg

TABLES = [(120, 92, 66), (158, 128, 96), (88, 90, 96), (176, 174, 168), (60, 62, 70)]  # lemn, gri, alb mat, negru


def _perspective_coeffs(src: list[tuple[float, float]], dst: list[tuple[float, float]]) -> list[float]:
    """Coeficienții pentru Image.transform(PERSPECTIVE): pentru fiecare punct din `dst` (ieșire) → `src` (intrare)."""
    a, b = [], []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b += [u, v]
    return np.linalg.solve(np.array(a, dtype=float), np.array(b, dtype=float)).tolist()


def _table(size: tuple[int, int], rng: random.Random) -> Image.Image:
    w, h = size
    base = np.array(rng.choice(TABLES), dtype=np.float32)
    nrng = np.random.default_rng(rng.randrange(2**32))
    # fibre orizontale (lemn) + pete mari, ca fundalul să nu fie o culoare plată
    grain = nrng.normal(0, 1, (h, 1)).repeat(w, 1) * 6 + nrng.normal(0, 1, (h, w)) * 3
    blotch = np.array(Image.fromarray(nrng.integers(0, 255, (h // 40 + 1, w // 40 + 1), dtype=np.uint8))
                      .resize((w, h), Image.BICUBIC), dtype=np.float32) / 255 - 0.5
    arr = base[None, None, :] + (grain + blotch * 24)[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _lighting(w: int, h: int, rng: random.Random) -> tuple[np.ndarray, dict]:
    """Mască multiplicativă: gradient de lumină dintr-o parte + umbră moale (mâna sau telefonul)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    angle = rng.uniform(0, 2 * np.pi)
    proj = (xx / w - 0.5) * np.cos(angle) + (yy / h - 0.5) * np.sin(angle)
    lo = rng.uniform(0.72, 0.9)
    mask = lo + (1.04 - lo) * (proj - proj.min()) / (np.ptp(proj) or 1)
    shadow = rng.random() < 0.7
    depth = 0.0
    if shadow:
        cx, cy = rng.uniform(-0.1, 1.1) * w, rng.uniform(-0.1, 1.1) * h
        rx, ry = rng.uniform(0.25, 0.55) * w, rng.uniform(0.2, 0.5) * h
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        depth = rng.uniform(0.18, 0.38)
        mask = mask * (1 - depth * np.exp(-d * 1.6))
    return mask, {"light_min": round(lo, 2), "shadow": shadow, "shadow_depth": round(depth, 2)}


def phone_photo(img: Image.Image, rng: random.Random) -> tuple[Image.Image, dict]:
    img = img.convert("RGB")
    w, h = img.size
    margin = rng.uniform(0.04, 0.1)
    cw, ch = round(w * (1 + 2 * margin)), round(h * (1 + 2 * margin))

    # colțurile foii în poză: rotație ±3° în jurul centrului + tragere de perspectivă (până la ~4% din latură)
    rot = np.deg2rad(rng.uniform(-3, 3))
    cx, cy = cw / 2, ch / 2
    corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    tilt = rng.uniform(0.01, 0.04)
    dst = []
    for x, y in corners:
        x += rng.uniform(-tilt, tilt) * w
        y += rng.uniform(-tilt, tilt) * h
        dst.append((cx + x * np.cos(rot) - y * np.sin(rot), cy + x * np.sin(rot) + y * np.cos(rot)))
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    coeffs = _perspective_coeffs(src, dst)
    paper = img.transform((cw, ch), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=(0, 0, 0))
    inside = Image.new("L", (w, h), 255).transform((cw, ch), Image.PERSPECTIVE, coeffs, Image.BILINEAR, fillcolor=0)
    photo = Image.composite(paper, _table((cw, ch), rng), inside.filter(ImageFilter.GaussianBlur(1.2)))

    arr = np.asarray(photo, dtype=np.float32)
    mask, light = _lighting(cw, ch, rng)
    cast = np.array([rng.uniform(0.94, 1.06) for _ in range(3)], dtype=np.float32)  # lumină caldă / rece
    arr = arr * mask[..., None] * cast
    sigma = rng.uniform(3, 8)
    arr += np.random.default_rng(rng.randrange(2**32)).normal(0, sigma, arr.shape)
    photo = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    motion = rng.random() < 0.3
    if motion:  # mână care tremură: blur pe orizontală
        photo = photo.filter(ImageFilter.Kernel((5, 5), [0] * 10 + [1] * 5 + [0] * 10, scale=5))
    blur = rng.uniform(0.4, 1.2)
    photo = photo.filter(ImageFilter.GaussianBlur(blur))
    quality = rng.randint(60, 80)
    params = {"rotation_deg": round(float(np.rad2deg(rot)), 2), "perspective": round(tilt, 3),
              "margin": round(margin, 3), **light, "color_cast": [round(float(c), 3) for c in cast],
              "noise_sigma": round(sigma, 1), "motion_blur": motion, "blur": round(blur, 2), "jpeg_quality": quality}
    return jpeg(photo, quality), params
