"""Intro-ul animat al videoului (4 s, randat la rezoluție dublă pentru margini netede):
6 puncte de lumină (cei 6 agenți) se adună într-un „ochi” holografic, flash + undă, apoi ochiul proiectează
un fascicul în jos și „scanează” pe ecran numele ORB și propoziția. Fundal: gradient, podea în perspectivă, praf luminos.

Rulare din rădăcina repo-ului:  backend/.venv/bin/python scripts/make_orb_intro.py [--final] [--ss 2]
Scrie video/out/orb_intro.mp4 (sau orb_outro.mp4 cu --final, cu propoziția de final).
"""
import argparse
import math
import random
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "backend" / "app" / "arena" / "fonts"
OW, OH, FPS = 1920, 1080, 30
BRAND, WHITE, GREY = (255, 230, 0), (255, 255, 255), (205, 210, 218)
T_MERGE = 1.15                 # când se adună punctele în ochi
T_BEAM = 1.55                  # când pornește fasciculul
T_SCAN0, T_SCAN1 = 1.65, 3.05  # scanarea textului, de sus în jos

LINES_INTRO = [("Checks a loan file in 20 seconds.", True),
               ("The AI never sees the customer's name. A human always decides.", False)]
LINES_FINAL = [("ORB does the checking.", True), ("Your people decide.", False)]

SS = 2                         # factorul de supraeșantionare (se setează din argumente)


def px(v: float) -> int:
    return int(round(v * SS))


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), px(size))


def clamp(t: float) -> float:
    return min(max(t, 0.0), 1.0)


def ease_out(t: float) -> float:
    return 1 - (1 - clamp(t)) ** 3


def ease_in(t: float) -> float:
    return clamp(t) ** 2


def ease_in_out(t: float) -> float:
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_back(t: float) -> float:
    t = clamp(t)
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ---------------------------------------------------------------- fundal
class Background:
    def __init__(self) -> None:
        W, H = px(OW), px(OH)
        self.W, self.H = W, H
        # gradient radial: centrul ușor luminat, marginile aproape negre
        small = Image.new("RGB", (192, 108))
        for y in range(108):
            for x in range(192):
                d = math.hypot((x - 96) / 96, (y - 42) / 70)
                k = clamp(d / 1.25) ** 1.3
                small.putpixel((x, y), tuple(int(a + (b - a) * k) for a, b in zip((34, 38, 48), (6, 7, 10))))
        self.base = small.resize((W, H), Image.BICUBIC).convert("RGBA")
        rng = random.Random(3)
        self.dust = [(rng.uniform(0, OW), rng.uniform(0, OH), rng.uniform(1.2, 3.5), rng.uniform(0.15, 0.6),
                      rng.uniform(-8, 8), rng.uniform(-14, -4)) for _ in range(70)]
        self.grain = [Image.effect_noise((W // 2, H // 2), 22).resize((W, H)).convert("L") for _ in range(4)]
        hy = px(600)
        fade = Image.linear_gradient("L").resize((W, H - hy))   # podeaua se stinge spre orizont
        self.floor_mask = Image.new("L", (W, H), 0)
        self.floor_mask.paste(fade, (0, hy))

    def frame(self, t: float, i: int) -> Image.Image:
        img = self.base.copy()
        W, H = self.W, self.H
        # podeaua în perspectivă (linii fine care vin spre cameră)
        floor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(floor)
        hy = px(600)                                   # orizontul
        vx = W / 2
        for k in range(-14, 15):                       # liniile care fug spre orizont
            d.line((vx + k * px(14), hy, vx + k * px(170), H), fill=(*BRAND, 60), width=px(1.2))
        off = (t * 0.35) % 1.0                         # liniile orizontale vin spre noi
        for n in range(12):
            z = (n + off) / 12
            y = hy + (H - hy) * z ** 2.2
            d.line((0, y, W, y), fill=(*BRAND, int(25 + 50 * z)), width=px(1.2))
        floor.putalpha(ImageChops.multiply(floor.getchannel("A"), self.floor_mask))
        img.alpha_composite(floor)
        # praful luminos
        dust = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dust)
        for x, y, s, a, vx_, vy_ in self.dust:
            xx = (x + vx_ * t) % OW
            yy = (y + vy_ * t) % OH
            dd.ellipse((px(xx - s), px(yy - s), px(xx + s), px(yy + s)), fill=(255, 236, 160, int(255 * a * 0.5)))
        img.alpha_composite(dust.filter(ImageFilter.GaussianBlur(px(1.6))))
        # granulație fină (aspect de film)
        g = self.grain[i % 4]
        img = Image.composite(img, Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.03), g)
        return img


# ---------------------------------------------------------------- piese
CX, CY, R = OW / 2, 330, 120


def glow_paste(img: Image.Image, layer: Image.Image, blur: float, pos=(0, 0)) -> None:
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(px(blur))), pos)
    img.alpha_composite(layer, pos)


def agent_pos(i: int, t: float) -> tuple[float, float]:
    k = clamp(t / T_MERGE)
    radius = 560 * (1 - ease_in(k)) + 3
    ang = i * math.tau / 6 + 5.0 * ease_in(k) + 0.6 * t
    return CX + radius * math.cos(ang), CY + radius * 0.5 * math.sin(ang)


def draw_agents(img: Image.Image, t: float) -> None:
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(6):
        for j in range(14):
            tt = t - j * 0.018
            if tt < 0:
                continue
            x, y = agent_pos(i, tt)
            s = 12 * (1 - j / 14) + 1
            a = int(255 * (1 - j / 14) ** 1.5 * clamp(t / 0.25))
            d.ellipse((px(x - s), px(y - s), px(x + s), px(y + s)), fill=(255, 236, 120, a))
    glow_paste(img, layer, 12)


def draw_orb(img: Image.Image, r: float, shine: float, t: float) -> None:
    if r < 2:
        return
    rr_ = px(r)
    S = rr_ * 4
    ox, oy = px(CX) - S // 2, px(CY) - S // 2
    c = S / 2
    halo = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    hr = rr_ * (1.4 + 0.5 * shine)
    ImageDraw.Draw(halo).ellipse((c - hr, c - hr, c + hr, c + hr), fill=(*BRAND, int(40 + 120 * shine)))
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(rr_ * 0.45)), (ox, oy))

    sph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(sph)
    for i in range(64):
        k = i / 63
        rad = rr_ * (1 - k)
        edge = (1 - k) ** 7
        col = tuple(int(dk + (lt - dk) * edge) for dk, lt in zip((10, 12, 18), (255, 212, 40)))
        d.ellipse((c - rad, c - rad, c + rad, c + rad), fill=(*col, 255))

    grid = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(grid)
    rot = t * 1.3
    for m in range(10):
        phi = m * math.pi / 10 + rot
        w = abs(math.cos(phi)) * rr_
        front = 0.5 + 0.5 * math.sin(phi)
        g.ellipse((c - w, c - rr_, c + w, c + rr_), outline=(255, 230, 0, int(30 + 100 * front)), width=px(1.3))
    for lat in (-0.66, -0.33, 0.0, 0.33, 0.66):
        y = c + lat * rr_
        hw = rr_ * math.sqrt(1 - lat * lat)
        g.ellipse((c - hw, y - hw * 0.16, c + hw, y + hw * 0.16), outline=(255, 230, 0, 60), width=px(1.3))
    sy = c - rr_ + (t * 0.8 % 1.0) * 2 * rr_       # scanarea din interiorul ochiului
    for j in range(24):
        a = int(80 * (1 - j / 24) ** 2)
        g.line((c - rr_, sy - j * px(1.5), c + rr_, sy - j * px(1.5)), fill=(255, 230, 0, a), width=px(1.5))
    g.line((c - rr_, sy, c + rr_, sy), fill=(255, 248, 200, 220), width=px(1.5))
    pr = rr_ * (0.12 + 0.035 * math.sin(t * 6)) * (1 + 0.5 * shine)
    core = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(core).ellipse((c - pr * 2.6, c - pr * 2.6, c + pr * 2.6, c + pr * 2.6), fill=(255, 225, 0, 160))
    grid.alpha_composite(core.filter(ImageFilter.GaussianBlur(pr * 1.3)))
    ImageDraw.Draw(grid).ellipse((c - pr, c - pr, c + pr, c + pr), fill=(255, 252, 228, 255))

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((c - rr_, c - rr_, c + rr_, c + rr_), fill=255)
    sph.alpha_composite(grid)
    sph.putalpha(ImageChops.multiply(sph.getchannel("A"), mask))
    img.alpha_composite(sph, (ox, oy))

    rim = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.ellipse((c - rr_, c - rr_, c + rr_, c + rr_), outline=(255, 242, 140, 255), width=px(2))
    for k in range(90):
        ang = k * math.tau / 90 + t * 0.7
        if math.sin(ang) < 0:
            continue
        x = c + math.cos(ang) * rr_ * 1.5
        y = c + math.sin(ang) * rr_ * 0.36 - (math.cos(ang) * rr_ * 1.5) * 0.22
        s = px(1.4 + 1.2 * ((k * 37) % 5) / 5)
        rd.ellipse((x - s, y - s, x + s, y + s), fill=(255, 238, 150, 220))
    glow_paste(img, rim, 3, (ox, oy))


rng = random.Random(7)
SPARKS = [(rng.uniform(0, math.tau), rng.uniform(260, 950), rng.uniform(1.5, 4.5)) for _ in range(110)]


def draw_wave(img: Image.Image, since: float) -> None:
    k = ease_out(since / 0.9)
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rr = R + 760 * k
    d.ellipse((px(CX - rr), px(CY - rr * 0.85), px(CX + rr), px(CY + rr * 0.85)),
              outline=(*BRAND, int(200 * (1 - k))), width=px(4))
    for ang, dist, size in SPARKS:
        x = CX + math.cos(ang) * dist * k
        y = CY + math.sin(ang) * dist * k * 0.8
        s = size * (1 - k * 0.6)
        d.ellipse((px(x - s), px(y - s), px(x + s), px(y + s)), fill=(255, 245, 190, int(255 * (1 - k))))
    glow_paste(img, layer, 5)


_TXT: dict = {}


def text_layer(lines, W: int, H: int) -> tuple[Image.Image, int, int]:
    """Numele ORB + cele două rânduri, centrate (o singură dată, apoi din cache)."""
    key = (tuple(lines), W)
    if key in _TXT:
        return _TXT[key]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(170)
    gap = px(22)
    widths = [f.getbbox(ch)[2] for ch in "ORB"]
    x = px(CX) - (sum(widths) + 2 * gap) / 2
    for ch, w in zip("ORB", widths):
        d.text((x, px(500)), ch, font=f, fill=WHITE)
        x += w + gap
    for (text, bold), y in zip(lines, (760, 826)):
        fl = font(48 if bold else 36, bold)
        w = fl.getbbox(text)[2]
        d.text((px(CX) - w / 2, px(y)), text, font=fl, fill=WHITE if bold else GREY)
    _TXT[key] = (layer, px(520), px(880))
    return _TXT[key]


def draw_beam_and_text(img: Image.Image, t: float, lines) -> None:
    W, H = img.size
    txt, y_top, y_bot = text_layer(lines, W, H)
    s = ease_in_out((t - T_SCAN0) / (T_SCAN1 - T_SCAN0))
    ys = y_top + (y_bot - y_top) * s if t >= T_SCAN0 else y_top
    beam_a = clamp((t - T_BEAM) / 0.25) * (1 - clamp((t - T_SCAN1 - 0.15) / 0.45))

    # fasciculul: un con de lumină din ochi până la linia de scanare
    if beam_a > 0:
        beam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(beam)
        top_w, bot_w = px(R * 0.5), px(760)
        y0 = px(CY + R * 0.75)
        flick = 0.85 + 0.15 * math.sin(t * 47) * math.sin(t * 13)
        steps = 40
        for n in range(steps):                       # gradient de sus în jos
            k0, k1 = n / steps, (n + 1) / steps
            ya, yb = y0 + (ys - y0) * k0, y0 + (ys - y0) * k1
            wa, wb = top_w + (bot_w - top_w) * k0, top_w + (bot_w - top_w) * k1
            a = int(70 * beam_a * flick * (0.35 + 0.65 * k1))
            bd.polygon([(W / 2 - wa / 2, ya), (W / 2 + wa / 2, ya), (W / 2 + wb / 2, yb), (W / 2 - wb / 2, yb)],
                       fill=(255, 226, 60, a))
        img.alpha_composite(beam.filter(ImageFilter.GaussianBlur(px(10))))

    if t < T_SCAN0:
        return
    # textul deja scanat (deasupra liniei)
    reveal = Image.new("L", (W, H), 0)
    ImageDraw.Draw(reveal).rectangle((0, 0, W, ys), fill=255)
    shown = txt.copy()
    shown.putalpha(ImageChops.multiply(txt.getchannel("A"), reveal))
    img.alpha_composite(shown)
    # banda de lângă linie: textul se aprinde galben, apoi se răcește la alb
    if s < 1:
        band = Image.new("L", (W, H), 0)
        bdraw = ImageDraw.Draw(band)
        for j in range(30):
            bdraw.rectangle((0, ys - px(j * 2 + 2), W, ys - px(j * 2)), fill=int(255 * (1 - j / 30)))
        hot = Image.new("RGBA", (W, H), (255, 225, 40, 255))
        hot.putalpha(ImageChops.multiply(ImageChops.multiply(txt.getchannel("A"), reveal), band))
        glow_paste(img, hot, 4)
        # linia de scanare
        line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(line).line((W / 2 - px(430), ys, W / 2 + px(430), ys),
                                  fill=(255, 246, 190, int(235 * beam_a)), width=px(2.5))
        glow_paste(img, line, 6)


# ---------------------------------------------------------------- cadru
def frame(bg: Background, t: float, i: int, total: float, final: bool) -> Image.Image:
    img = bg.frame(t, i)
    if t < T_MERGE + 0.04:
        draw_agents(img, t)
    since = t - T_MERGE
    if since >= 0:
        pulse = math.exp(-(since ** 2) / 0.03)
        draw_orb(img, R * ease_back(since / 0.45) * (1 + 0.04 * pulse), pulse, t)
        if since < 0.9:
            draw_wave(img, since)
    draw_beam_and_text(img, t, LINES_FINAL if final else LINES_INTRO)
    flash = math.exp(-((t - T_MERGE) ** 2) / 0.0035)
    if flash > 0.02:
        img = Image.blend(img, Image.new("RGBA", img.size, (255, 250, 225, 255)), 0.28 * flash)
    ImageDraw.Draw(img).rectangle((0, 0, int(img.size[0] * ease_out(t / 1.0)), px(8)), fill=(*BRAND, 255))
    if not final and t > total - 0.25:
        img = Image.blend(img, Image.new("RGBA", img.size, (6, 7, 10, 255)), (t - (total - 0.25)) / 0.25 * 0.7)
    return img.convert("RGB").resize((OW, OH), Image.LANCZOS)


def main() -> None:
    global SS
    ap = argparse.ArgumentParser()
    ap.add_argument("--secunde", type=float, default=4.0)
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--ss", type=int, default=2, help="supraeșantionare (2 = margini netede)")
    ap.add_argument("--cadre", default="", help="doar aceste cadre, ca PNG (ex. 40,70,100), pentru verificare")
    a = ap.parse_args()
    SS = a.ss
    bg = Background()
    out = ROOT / "video" / "out" / ("orb_outro.mp4" if a.final else "orb_intro.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.cadre:
        for n in map(int, a.cadre.split(",")):
            frame(bg, n / FPS, n, a.secunde, a.final).save(out.with_name(f"intro_cadru_{n}.png"))
        print("cadre scrise în", out.parent)
        return
    n = int(a.secunde * FPS)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            frame(bg, i / FPS, i, a.secunde, a.final).save(f"{tmp}/f{i:04d}.png", compress_level=1)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{tmp}/f%04d.png",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", str(out)], check=True)
    print("scris:", out)


if __name__ == "__main__":
    main()
