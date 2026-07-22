"""One-off script: generates assets/icon.ico and assets/logo.png from the
app's theme colors (a mic + soundwave mark). Not part of the app itself --
run manually with `python tools/make_icon.py` whenever the mark needs a
refresh.
"""

from pathlib import Path

from PIL import Image, ImageDraw

ACCENT = (124, 92, 255)
ACCENT_HOVER = (146, 119, 255)
BG = (27, 28, 34)
BG2 = (37, 38, 47)

OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def _rounded_bg(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * 0.22)
    for y in range(size):
        t = y / size
        color = tuple(int(BG[i] + (BG2[i] - BG[i]) * t) for i in range(3)) + (255,)
        draw.line([(0, y), (size, y)], fill=color)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def _draw_mark(img: Image.Image):
    size = img.width
    draw = ImageDraw.Draw(img)
    cx = size / 2

    # Mic capsule
    cap_w, cap_h = size * 0.24, size * 0.40
    cap_top = size * 0.16
    draw.rounded_rectangle(
        [cx - cap_w / 2, cap_top, cx + cap_w / 2, cap_top + cap_h],
        radius=cap_w / 2,
        fill=ACCENT + (255,),
    )

    # Mic body outline (open cage arc) below the capsule
    body_r = size * 0.20
    body_cy = cap_top + cap_h * 0.62
    bbox = [cx - body_r, body_cy - body_r, cx + body_r, body_cy + body_r]
    width = max(2, int(size * 0.028))
    draw.arc(bbox, start=25, end=155, fill=ACCENT_HOVER + (255, ), width=width)

    # Stand: stem + base
    stem_top = body_cy + body_r * 0.72
    stem_bottom = size * 0.78
    draw.line([(cx, stem_top), (cx, stem_bottom)], fill=ACCENT_HOVER + (255,), width=width)
    base_w = size * 0.22
    draw.line(
        [(cx - base_w / 2, stem_bottom), (cx + base_w / 2, stem_bottom)],
        fill=ACCENT_HOVER + (255,),
        width=width,
    )

    # Soundwave bars flanking the mic
    bar_w = max(2, int(size * 0.035))
    gap = size * 0.05
    heights = [0.10, 0.18, 0.10]
    for side in (-1, 1):
        for i, h in enumerate(heights):
            bx = cx + side * (cap_w / 2 + gap + i * (bar_w + gap * 0.6) + bar_w / 2)
            by = cap_top + cap_h * 0.5
            bh = size * h
            draw.rounded_rectangle(
                [bx - bar_w / 2, by - bh / 2, bx + bar_w / 2, by + bh / 2],
                radius=bar_w / 2,
                fill=(232, 232, 236, 200),
            )


def build(size: int) -> Image.Image:
    img = _rounded_bg(size)
    _draw_mark(img)
    return img


def main():
    OUT_DIR.mkdir(exist_ok=True)

    master = build(1024)
    master.save(OUT_DIR / "logo.png")

    icon_sizes = [16, 24, 32, 48, 64, 128, 256]
    icon_images = [build(s) for s in icon_sizes]
    icon_images[-1].save(
        OUT_DIR / "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in icon_sizes],
    )
    print(f"Wrote {OUT_DIR / 'logo.png'} and {OUT_DIR / 'icon.ico'}")


if __name__ == "__main__":
    main()
