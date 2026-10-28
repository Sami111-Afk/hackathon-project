"""Intro-ul animat al videoului: globul ORB se formează, pulsează o dată, apare numele și propoziția.

Rulare din rădăcina repo-ului:  backend/.venv/bin/python scripts/make_orb_intro.py [--secunde 3] [--final]
Scrie video/out/orb_intro.mp4 (sau orb_outro.mp4 cu --final: globul rămâne pe ecran, fără propoziția de început).
"""
import argparse
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "backend" / "app" / "arena" / "fonts"
W, H, FPS = 1920, 1080, 30
NIGHT, BRAND, WHITE, GREY = (17, 20, 24), (255, 230, 0), (255, 255, 255), (201, 206, 214)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size)


def ease_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_back(t: float) -> float:
    """Depășește puțin ținta și revine (efect de „pop”)."""
    t = min(max(t, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def orb_layer(r: float, glow: float) -> Image.Image:
    """Globul: gradient radial galben, cu strălucire în jur."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if r < 1:
        return layer
    cx, cy = W // 2 - 260, H // 2 - 40
    # strălucirea
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gr = r * (1.6 + 0.5 * glow)
    gd.ellipse((cx - gr, cy - gr, cx + gr, cy + gr), fill=(*BRAND, int(70 + 90 * glow)))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.55))
    layer.alpha_composite(g)
    # globul, în inele concentrice (alb în centru-stânga-sus → galben → auriu la margine)
    d = ImageDraw.Draw(layer)
    steps = 40
    for i in range(steps):
        k = i / (steps - 1)
        rr = r * (1 - k * 0.92)
        ox, oy = -r * 0.28 * k, -r * 0.30 * k
        col = tuple(int(a + (b - a) * k) for a, b in zip((214, 160, 0), (255, 247, 170)))
        d.ellipse((cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr), fill=(*col, 255))
    return layer


def ring_layer(r: float, alpha: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if alpha <= 0:
        return layer
    cx, cy = W // 2 - 260, H // 2 - 40
    d = ImageDraw.Draw(layer)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(*BRAND, int(255 * alpha)), width=6)
    return layer


def frame(t: float, total: float, final: bool) -> Image.Image:
    img = Image.new("RGBA", (W, H), (*NIGHT, 255))
    base_r = 150
    # 0–0,6 s: globul crește cu „pop”; 0,6–1,1 s: un inel pleacă din el (pulsul)
    r = base_r * ease_back(t / 0.6)
    pulse = math.exp(-((t - 0.75) ** 2) / 0.02)
    img.alpha_composite(orb_layer(r * (1 + 0.04 * pulse), pulse))
    rt = (t - 0.6) / 0.7
    if 0 <= rt <= 1:
        img.alpha_composite(ring_layer(base_r * (1 + 1.2 * ease_out(rt)), 1 - rt))
    # 0,7–1,3 s: „ORB” intră din dreapta globului
    tt = ease_out((t - 0.7) / 0.6)
    if tt > 0:
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(txt)
        x = W // 2 - 60 + int(60 * (1 - tt))
        d.text((x, H // 2 - 150), "ORB", font=font(220), fill=(*WHITE, int(255 * tt)))
        img.alpha_composite(txt)
    # 1,3–1,9 s: propoziția de sub nume
    st = ease_out((t - 1.3) / 0.6)
    if st > 0:
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(txt)
        lines = (["ORB does the checking.", "Your people decide."] if final else
                 ["AI agents that do the repetitive checks", "on loan applications"])
        for i, line in enumerate(lines):
            d.text((W // 2 - 52, H // 2 + 110 + i * 62 + int(20 * (1 - st))), line,
                   font=font(46, bold=(i == 0)), fill=(*(WHITE if i == 0 else GREY), int(255 * st)))
        img.alpha_composite(txt)
    # bara galbenă de sus, ca pe celelalte carduri
    ImageDraw.Draw(img).rectangle((0, 0, int(W * ease_out(t / 0.8)), 10), fill=(*BRAND, 255))
    # ultimele 0,3 s: fade spre negru (doar la intro, ca să intre lin scena următoare)
    if not final and t > total - 0.3:
        k = (t - (total - 0.3)) / 0.3
        img = Image.blend(img, Image.new("RGBA", (W, H), (*NIGHT, 255)), k * 0.6)
    return img.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--secunde", type=float, default=3.0)
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    out = ROOT / "video" / "out" / ("orb_outro.mp4" if a.final else "orb_intro.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    n = int(a.secunde * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            frame(i / FPS, a.secunde, a.final).save(f"{tmp}/f{i:04d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    print("scris:", out)


if __name__ == "__main__":
    main()
