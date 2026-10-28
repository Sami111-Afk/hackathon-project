"""Intro-ul animat al videoului (4 s): 6 puncte de lumină (cei 6 agenți) se rotesc și se adună într-un glob,
flash + undă + scântei, „ORB” intră cu literele strângându-se, apoi propoziția apare ca la tastare.

Rulare din rădăcina repo-ului:  backend/.venv/bin/python scripts/make_orb_intro.py [--final]
Scrie video/out/orb_intro.mp4 (sau orb_outro.mp4 cu --final, cu propoziția de final).
"""
import argparse
import math
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "backend" / "app" / "arena" / "fonts"
W, H, FPS = 1920, 1080, 30
NIGHT, BRAND, WHITE, GREY = (17, 20, 24), (255, 230, 0), (255, 255, 255), (201, 206, 214)
CX, CY = W // 2, 400          # centrul globului
R = 120                       # raza globului
T_MERGE = 1.2                 # când se adună punctele

LINES_INTRO = [("Checks a loan file in 20 seconds.", True),
               ("The AI never sees the customer's name. A human always decides.", False)]
LINES_FINAL = [("ORB does the checking.", True), ("Your people decide.", False)]


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size)


def clamp(t: float) -> float:
    return min(max(t, 0.0), 1.0)


def ease_out(t: float) -> float:
    return 1 - (1 - clamp(t)) ** 3


def ease_in(t: float) -> float:
    return clamp(t) ** 2


def ease_back(t: float) -> float:
    t = clamp(t)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def agent_pos(i: int, t: float) -> tuple[float, float]:
    """Punctul i pe o spirală care se strânge spre centru până la T_MERGE."""
    k = clamp(t / T_MERGE)
    radius = 520 * (1 - ease_in(k)) + 4
    ang = i * math.tau / 6 + 5.0 * ease_in(k) + 0.6 * t
    return CX + radius * math.cos(ang), CY + radius * 0.55 * math.sin(ang)


def glow(img: Image.Image, draw_fn, blur: float) -> None:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
    img.alpha_composite(layer)


def draw_orb(img: Image.Image, r: float, shine: float) -> None:
    if r < 1:
        return
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hr = r * (1.7 + 0.6 * shine)
    ImageDraw.Draw(halo).ellipse((CX - hr, CY - hr, CX + hr, CY + hr), fill=(*BRAND, int(60 + 120 * shine)))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(r * 0.6)))
    d = ImageDraw.Draw(img)
    steps = 40
    for i in range(steps):
        k = i / (steps - 1)
        rr = r * (1 - k * 0.92)
        ox, oy = -r * 0.28 * k, -r * 0.30 * k
        col = tuple(int(a + (b - a) * k) for a, b in zip((214, 158, 0), (255, 248, 180)))
        d.ellipse((CX + ox - rr, CY + oy - rr, CX + ox + rr, CY + oy + rr), fill=(*col, 255))


rng = random.Random(7)
SPARKS = [(rng.uniform(0, math.tau), rng.uniform(260, 900), rng.uniform(2, 6)) for _ in range(90)]


def frame(t: float, total: float, final: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (*NIGHT, 255))

    # 1) cei 6 agenți: puncte cu dâră, pe spirală
    if t < T_MERGE + 0.05:
        def dots(d: ImageDraw.ImageDraw) -> None:
            for i in range(6):
                for j in range(10):                      # dâra
                    tt = t - j * 0.025
                    if tt < 0:
                        continue
                    x, y = agent_pos(i, tt)
                    s = 16 * (1 - j / 10)
                    a = int(255 * (1 - j / 10) * clamp(t / 0.25))
                    d.ellipse((x - s, y - s, x + s, y + s), fill=(*BRAND, a))
        glow(img, dots, 14)

    # 2) globul apare cu „pop” la T_MERGE
    since = t - T_MERGE
    if since >= 0:
        pulse = math.exp(-(since ** 2) / 0.03)
        draw_orb(img, R * ease_back(since / 0.45) * (1 + 0.05 * pulse), pulse)

        # unda de șoc + scânteile
        if since < 0.9:
            k = ease_out(since / 0.9)
            def wave(d: ImageDraw.ImageDraw) -> None:
                rr = R + 700 * k
                d.ellipse((CX - rr, CY - rr * 0.9, CX + rr, CY + rr * 0.9), outline=(*BRAND, int(220 * (1 - k))), width=8)
                for ang, dist, size in SPARKS:
                    x = CX + math.cos(ang) * dist * k
                    y = CY + math.sin(ang) * dist * k * 0.8
                    s = size * (1 - k * 0.7)
                    d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 245, 190, int(255 * (1 - k))))
            glow(img, wave, 6)

    # 3) „ORB”: literele vin de departe și se strâng
    lt = ease_out((t - (T_MERGE + 0.25)) / 0.6)
    if lt > 0:
        f = font(190)
        gap = 18 + 160 * (1 - lt)
        widths = [f.getbbox(ch)[2] for ch in "ORB"]
        total_w = sum(widths) + gap * 2
        x = CX - total_w / 2
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for ch, w in zip("ORB", widths):
            d.text((x, 540), ch, font=f, fill=(*WHITE, int(255 * lt)))
            x += w + gap
        img.alpha_composite(layer)

    # 4) propoziția, ca la tastare (cu cursor)
    lines = LINES_FINAL if final else LINES_INTRO
    starts = [T_MERGE + 0.8, T_MERGE + 1.3]
    speed = 75                                            # caractere pe secundă
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for (text, bold), start, y in zip(lines, starts, (790, 858)):
        n = int((t - start) * speed)
        if n <= 0:
            continue
        f = font(50 if bold else 40, bold)
        shown = text[:n]
        full_w = f.getbbox(text)[2]
        x0 = CX - full_w / 2
        d.text((x0, y), shown, font=f, fill=WHITE if bold else GREY)
        if n < len(text) or int(t * 3) % 2 == 0:          # cursorul clipește
            cx = x0 + f.getbbox(shown)[2] + 6
            d.rectangle((cx, y + 8, cx + 4, y + (54 if bold else 42)), fill=BRAND)
    img.alpha_composite(layer)

    # 5) flash la contopire + bara galbenă de sus
    flash = math.exp(-((t - T_MERGE) ** 2) / 0.004)
    if flash > 0.02:
        img = Image.blend(img, Image.new("RGBA", (W, H), (255, 252, 230, 255)), 0.30 * flash)
    ImageDraw.Draw(img).rectangle((0, 0, int(W * ease_out(t / 1.0)), 10), fill=(*BRAND, 255))

    if not final and t > total - 0.25:                      # trecere lină spre scena 1
        img = Image.blend(img, Image.new("RGBA", (W, H), (*NIGHT, 255)), (t - (total - 0.25)) / 0.25 * 0.7)
    return img.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secunde", type=float, default=4.0)
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    out = ROOT / "video" / "out" / ("orb_outro.mp4" if a.final else "orb_intro.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    n = int(a.secunde * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            frame(i / FPS, a.secunde, a.final).save(f"{tmp}/f{i:04d}.png", compress_level=1)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", str(out)], check=True)
    print("scris:", out)


if __name__ == "__main__":
    main()
