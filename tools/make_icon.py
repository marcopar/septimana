"""Generates assets/septimana.ico, the application icon used for the executable.

Run with: python tools/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CANVAS = 256
ICO_SIZES = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]

ACCENT = (0, 103, 192, 255)
PAPER = (255, 255, 255, 255)
RING = (90, 96, 104, 255)

_FONT_CANDIDATES = ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")


def _font(size: int) -> ImageFont.ImageFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fitted(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int):
    for size in range(max_h, 8, -2):
        font = _font(size)
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if right - left <= max_w and bottom - top <= max_h:
            return font
    return _font(10)


def build(text: str = "W7") -> Image.Image:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    body = (16, 44, 240, 236)
    header_h = 56
    radius = 26

    # Two hanging rings, drawn first so the header overlaps their lower half.
    for cx in (78, 178):
        d.rounded_rectangle((cx - 11, 14, cx + 11, 74), radius=11, fill=RING)

    d.rounded_rectangle(body, radius=radius, fill=PAPER)
    d.rounded_rectangle((body[0], body[1], body[2], body[1] + header_h + radius),
                        radius=radius, fill=ACCENT)
    d.rectangle((body[0], body[1] + header_h, body[2], body[1] + header_h + radius),
                fill=PAPER)
    d.rounded_rectangle(body, radius=radius, outline=ACCENT, width=8)

    text_top = body[1] + header_h
    area_w = body[2] - body[0] - 36
    area_h = body[3] - text_top - 28
    font = _fitted(d, text, area_w, area_h)
    left, top, right, bottom = d.textbbox((0, 0), text, font=font)
    x = (body[0] + body[2] - (right - left)) / 2 - left
    y = (text_top + body[3] - (bottom - top)) / 2 - top
    d.text((x, y), text, font=font, fill=ACCENT)
    return img


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "assets" / "septimana.ico"
    out.parent.mkdir(parents=True, exist_ok=True)
    icon = build()
    icon.save(out, format="ICO", sizes=ICO_SIZES)
    icon.save(out.with_suffix(".png"))
    print(f"wrote {out} ({', '.join(f'{w}x{h}' for w, h in ICO_SIZES)})")


if __name__ == "__main__":
    main()
