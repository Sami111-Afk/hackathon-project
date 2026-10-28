"""Cardurile grafice pentru videoul de 3:00 (1920×1080 PNG, culorile aplicației).

Rulare din rădăcina repo-ului:  backend/.venv/bin/python scripts/make_video_cards.py
Scrie în video/cards/. Overlay-urile (*_overlay.png) au fundal transparent — se pun peste clipuri în CapCut.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "video" / "cards"
FONTS = ROOT / "backend" / "app" / "arena" / "fonts"
W, H = 1920, 1080
INK, INK2, INK3, BRAND, WHITE = "#1F2328", "#4E5764", "#6B7480", "#FFE600", "#FFFFFF"
NIGHT, OK, DANGER = "#111418", "#47CD89", "#F97066"


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / ("NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf")), size)


def centered(d: ImageDraw.ImageDraw, y: int, text: str, f, fill) -> int:
    box = d.textbbox((0, 0), text, font=f)
    d.text(((W - (box[2] - box[0])) / 2, y), text, font=f, fill=fill)
    return y + (box[3] - box[1])


def logo(d: ImageDraw.ImageDraw, x: int, y: int, s: int = 72) -> None:
    d.rectangle((x, y, x + s, y + s), fill=INK if d.im.mode != "RGBA" else INK)
    d.text((x + s * 0.27, y + s * 0.02), "O", font=font(int(s * 0.8)), fill=BRAND)


def full(name: str, lines: list[tuple[str, int, str, bool]], dark: bool = True, top_bar: bool = True) -> None:
    img = Image.new("RGB", (W, H), NIGHT if dark else "#EDEFF2")
    d = ImageDraw.Draw(img)
    if top_bar:
        d.rectangle((0, 0, W, 10), fill=BRAND)
    total = sum(size * 1.35 for _, size, _, _ in lines)
    y = int((H - total) / 2)
    for text, size, color, bold in lines:
        centered(d, y, text, font(size, bold), color)
        y += int(size * 1.35)
    img.save(OUT / f"{name}.png")


def overlay(name: str, text: str, sub: str | None = None, accent: str = BRAND) -> None:
    """Text mare pe o bandă semi-transparentă, în treimea de jos a ecranului."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    band_h = 230 if sub else 170
    y0 = H - band_h - 90
    d.rounded_rectangle((120, y0, W - 120, y0 + band_h), radius=18, fill=(17, 20, 24, 225))
    d.rectangle((120, y0, 134, y0 + band_h), fill=accent)
    f = font(78)
    box = d.textbbox((0, 0), text, font=f)
    d.text(((W - (box[2] - box[0])) / 2, y0 + 30), text, font=f, fill=WHITE)
    if sub:
        fs = font(36, bold=False)
        box = d.textbbox((0, 0), sub, font=fs)
        d.text(((W - (box[2] - box[0])) / 2, y0 + 150), sub, font=fs, fill="#C9CED6")
    img.save(OUT / f"{name}_overlay.png")


def numbers() -> None:
    img = Image.new("RGB", (W, H), NIGHT)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 10), fill=BRAND)
    centered(d, 120, "Measured with the real AI · 60 synthetic applications", font(54), WHITE)
    cards = [("0", "names or ID numbers\nsent to the cloud", OK), ("0 / 12", "honest applicants\nflagged high-risk", OK),
             ("36 / 36", "simple forgeries\ncaught", BRAND), ("12 / 12", "perfect forgeries\nsent to a human", BRAND)]
    cw, gap = 380, 40
    x = (W - (4 * cw + 3 * gap)) / 2
    for big, small, color in cards:
        d.rounded_rectangle((x, 300, x + cw, 720), radius=20, outline="#323843", width=3, fill="#171B21")
        fb = font(100)
        box = d.textbbox((0, 0), big, font=fb)
        d.text((x + (cw - (box[2] - box[0])) / 2, 360), big, font=fb, fill=color)
        fs = font(34, bold=False)
        for i, line in enumerate(small.split("\n")):
            box = d.textbbox((0, 0), line, font=fs)
            d.text((x + (cw - (box[2] - box[0])) / 2, 560 + i * 48), line, font=fs, fill="#C9CED6")
        x += cw + gap
    centered(d, 800, "3 of 12 honest files went to a human for a second look  ·  ~10 s per file  ·  ~0.005 $ per file", font(40), WHITE)
    centered(d, 880, "Synthetic data and forgeries made by us: a correctness test of the pipeline, not accuracy on real fraud.",
             font(28, bold=False), INK3)
    img.save(OUT / "05_numbers.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    full("01_title", [("ORB", 150, BRAND, True),
                      ("AI agents that do the repetitive checks on loan applications", 52, WHITE, True),
                      ("— without customer data leaving the bank", 44, "#C9CED6", False)])
    full("09_end", [("ORB", 130, BRAND, True),
                    ("Shadow-mode pilot: next to your analysts, never instead of them", 46, WHITE, True),
                    ("orb-raiffeisen.vercel.app", 44, "#C9CED6", False),
                    ("Try to fool it: orb-raiffeisen.vercel.app/arena", 40, BRAND, False)])
    overlay("02_twenty_minutes", "~20 min per application", "read · recalculate taxes · look up the employer · cross-check")
    overlay("03_twenty_seconds", "from 20 min to 20 s")
    overlay("04_net_mismatch", "8,307 ≠ 8,500 lei", "the net pay doesn't follow from the gross", accent=DANGER)
    overlay("06_ring", "1 IBAN · 6 identities", "a ring no analyst sees one file at a time", accent=DANGER)
    overlay("07_ai_doesnt_decide", "The AI doesn't decide", "the risk level comes from the evidence · the analyst signs")
    overlay("08_privacy", "0 personal data to the cloud", "the AI sees [PERSOANA_1], never a name")
    overlay("10_realtime", "real time: 20 s", accent=OK)
    numbers()
    print(f"scris în {OUT}:", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))


if __name__ == "__main__":
    main()
