"""Build all MadScientist character art from the vanilla Tinker Time event illustration.

Source: Slay the Spire 2  images/events/tinker_time.png  (3440x1616)
The character is the "mad scientist" who appears in the Act 3 Tinker Time event.

Run:  python art/build_art.py
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
REF = Path(r"D:\DSH_work\ref")
SRC = REF / "tinker_time.png"
OUT = ROOT / "MadScientist" / "images"

# Region of the event illustration that contains the character (native pixels).
CROP = (930, 795, 1510, 1540)  # left, top, right, bottom

# Silhouette of the body (head, backpack, coat, planted arm).  The raised arm and
# hand are picked up automatically from the background difference mask.
BODY_POLY = [
    (230, 57), (285, 51), (325, 62), (345, 85), (358, 115), (362, 145),
    (355, 175), (342, 200), (336, 220), (355, 238), (375, 245), (385, 270),
    (390, 305), (392, 345), (388, 385), (382, 425), (376, 465), (366, 505),
    (350, 540), (325, 570), (295, 588), (262, 592), (238, 575), (220, 545),
    (208, 510), (200, 470), (194, 432), (180, 405), (155, 395),
    (125, 390), (95, 375), (70, 352), (52, 322), (42, 288), (45, 250),
    (55, 215), (70, 180), (88, 150), (110, 125), (138, 102), (170, 85),
    (200, 70),
]

# Raised right arm and hand (kept as a separate polygon so the gap between the
# arm and the head stays transparent).
ARM_POLY = [
    (368, 25), (400, 28), (430, 40), (445, 60), (442, 75), (425, 92),
    (415, 110), (408, 135), (402, 160), (398, 185), (396, 210), (392, 232),
    (370, 240), (350, 225), (344, 205), (346, 185), (352, 165), (355, 140),
    (352, 115), (350, 90), (352, 65), (358, 42),
]

GREEN = (168, 224, 95)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def premultiply(im: Image.Image) -> Image.Image:
    a = im.getchannel("A")
    rgb = Image.new("RGB", im.size)
    rgb.paste(im.convert("RGB"))
    out = Image.new("RGB", im.size)
    out.paste(rgb)
    out = Image.composite(rgb, Image.new("RGB", im.size, (0, 0, 0)), a)
    res = Image.merge("RGBA", (*out.split(), a))
    return res


def resize_rgba(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize RGBA without dark fringes (premultiplied alpha)."""
    a = im.getchannel("A")
    rgb = im.convert("RGB")
    black = Image.new("RGB", im.size, (0, 0, 0))
    pm = Image.composite(rgb, black, a)
    pm = pm.resize(size, Image.LANCZOS)
    a2 = a.resize(size, Image.LANCZOS)
    out_rgb = Image.new("RGB", size)
    # un-premultiply
    arr = np.asarray(pm).astype(np.float32)
    aa = np.asarray(a2).astype(np.float32) / 255.0
    safe = np.maximum(aa, 1e-3)[..., None]
    arr = np.clip(arr / safe, 0, 255)
    arr[aa < 0.01] = 0
    out_rgb = Image.fromarray(arr.astype(np.uint8))
    return Image.merge("RGBA", (*out_rgb.split(), a2))


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep only the connected component that contains the body polygon."""
    from collections import deque

    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = None
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            if mask[y, x] and not seen[y, x]:
                q = deque([(y, x)])
                seen[y, x] = True
                pts = []
                while q:
                    cy, cx = q.popleft()
                    pts.append((cy, cx))
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
                if best is None or len(pts) > len(best):
                    best = pts
    out = np.zeros_like(mask)
    if best:
        ys = np.fromiter((p[0] for p in best), dtype=np.int32)
        xs = np.fromiter((p[1] for p in best), dtype=np.int32)
        out[ys, xs] = True
    return out


def fill_holes(mask: Image.Image) -> Image.Image:
    """Fill holes by flood filling the background from the border."""
    inv = Image.eval(mask, lambda v: 255 - v)
    w, h = inv.size
    ff = inv.copy()
    ImageDraw.floodfill(ff, (0, 0), 128)
    arr = np.asarray(ff)
    holes = arr == 255  # untouched inside regions
    base = np.asarray(mask).copy()
    base[holes] = 255
    return Image.fromarray(base)


def build_alpha(src: Image.Image) -> Image.Image:
    """Combine a background-difference mask with the body polygons.

    The event illustration is lit from the front, so the scientist differs
    strongly from the local background.  Inside the hand-traced silhouette the
    very dark background pockets are rejected by brightness, while the (dark but
    not black) coat and backpack are kept.
    """
    a = np.asarray(src).astype(np.float32)
    lum = 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]

    bg = src.filter(ImageFilter.MedianFilter(81))
    diff = np.sqrt(((a - np.asarray(bg).astype(np.float32)) ** 2).sum(2))
    diff_m = Image.fromarray(((diff > 13) * 255).astype(np.uint8))
    diff_m = diff_m.filter(ImageFilter.MedianFilter(5))
    diff_m = diff_m.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

    poly = Image.new("L", src.size, 0)
    d = ImageDraw.Draw(poly)
    d.polygon(BODY_POLY, fill=255)
    d.polygon(ARM_POLY, fill=255)

    inside = np.asarray(poly) > 0
    bright_enough = lum > 24

    yy = np.arange(src.size[1])[:, None]
    lower_body = inside & (yy > 390)
    alpha = ((np.asarray(diff_m) > 100) | (inside & bright_enough) | lower_body).astype(np.uint8) * 255
    mask = Image.fromarray(alpha)
    mask = fill_holes(mask)
    # never keep anything well outside the hand traced silhouette
    allowed = np.asarray(poly.filter(ImageFilter.MaxFilter(21))) > 0
    m = (np.asarray(mask) > 0) & allowed
    m = largest_component(m)
    mask = Image.fromarray((m * 255).astype(np.uint8))
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.GaussianBlur(1.3))

    # dissolve the bottom of the coat into shadow (the illustration fades there)
    mm = np.asarray(mask).astype(np.float32) / 255.0
    fade = np.clip((590.0 - yy.astype(np.float32)) / 95.0, 0.0, 1.0)
    mm = mm * fade
    return Image.fromarray((mm * 255).astype(np.uint8))


def cutout() -> Image.Image:
    src = Image.open(SRC).convert("RGB").crop(CROP)
    alpha = build_alpha(src)
    out = src.convert("RGBA")
    out.putalpha(alpha)
    return out


def content_bbox(im: Image.Image, thresh: int = 8) -> tuple[int, int, int, int]:
    a = np.asarray(im.getchannel("A"))
    ys, xs = np.where(a > thresh)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def crop_square(im: Image.Image, center: tuple[int, int], size: int) -> Image.Image:
    cx, cy = center
    half = size // 2
    return im.crop((cx - half, cy - half, cx + half, cy + half))


def silhouette(im: Image.Image, size: tuple[int, int], color=(0, 0, 0)) -> Image.Image:
    a = im.getchannel("A").resize(size, Image.LANCZOS)
    layer = Image.new("RGBA", size, (*color, 0))
    layer.putalpha(a)
    return layer


def recolor(im: Image.Image, color: tuple[int, int, int], amount=1.0) -> Image.Image:
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    lum = rgb.mean(2, keepdims=True)
    tint = np.array(color, dtype=np.float32)[None, None, :]
    out = rgb * (1 - amount) + (lum * (tint / 255.0)) * amount
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------- #
# assets
# --------------------------------------------------------------------------- #
def main() -> None:
    char = cutout()
    char.save(REF / "char_cutout2.png")
    bbox = content_bbox(char)
    body = char.crop(bbox)
    print("cutout bbox", bbox, "body", body.size)

    # ---- combat visual (static NCreatureVisuals image) ----
    combat = body
    if combat.height > 760:
        s = 760 / combat.height
        combat = resize_rgba(combat, (int(combat.width * s), 760))
    (OUT / "character").mkdir(parents=True, exist_ok=True)
    combat.save(OUT / "character" / "combat.png")

    # ---- character select portrait 132x195 ----
    portrait = char.crop((150, 20, 480, 507))  # 330 x 487
    p = resize_rgba(portrait, (132, 195))
    (OUT / "charui").mkdir(parents=True, exist_ok=True)
    p.save(OUT / "charui" / "char_select_mad_scientist.png")

    # locked: black silhouette
    silhouette(p, (132, 195)).save(OUT / "charui" / "char_select_mad_scientist_locked.png")

    # ---- top panel / stats icon 88x88 ----
    icon = crop_square(char, (325, 140), 180)
    resize_rgba(icon, (88, 88)).save(OUT / "charui" / "character_icon_mad_scientist.png")
    # white silhouette, matching the vanilla *_outline.png icons
    out_icon = resize_rgba(icon, (88, 88))
    white = Image.new("RGBA", (88, 88), (255, 255, 255, 0))
    white.putalpha(out_icon.getchannel("A"))
    white.save(OUT / "charui" / "character_icon_mad_scientist_outline.png")

    # ---- map marker 49x64 ----
    marker = resize_rgba(body, (49, 64))
    marker.save(OUT / "charui" / "map_marker_mad_scientist.png")

    # ---- mod image 420x420 ----
    # empty cave wall on the left of the event illustration, no character in it
    bg = Image.open(SRC).convert("RGB").crop((120, 640, 900, 1420)).resize((420, 420), Image.LANCZOS)
    bg = Image.eval(bg, lambda v: int(v * 0.62))
    canvas = bg.convert("RGBA")
    shade = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    dsh = ImageDraw.Draw(shade)
    dsh.rectangle((0, 250, 420, 420), fill=(8, 12, 10, 150))
    canvas.alpha_composite(shade)
    fig = resize_rgba(body, (int(body.width * 0.68), int(body.height * 0.68)))
    canvas.alpha_composite(fig, (420 - fig.width - 8, 420 - fig.height + 32))

    # green vignette
    vig = Image.new("L", (420, 420), 0)
    dv = ImageDraw.Draw(vig)
    dv.rectangle((0, 0, 420, 420), outline=255, width=6)
    canvas.alpha_composite(Image.merge("RGBA", (
        Image.new("L", (420, 420), GREEN[0]),
        Image.new("L", (420, 420), GREEN[1]),
        Image.new("L", (420, 420), GREEN[2]),
        vig.point(lambda v: int(v * 0.25)),
    )))

    font_path = r"C:\Windows\Fonts\msyhbd.ttc"
    d = ImageDraw.Draw(canvas)
    if os.path.exists(font_path):
        f_big = ImageFont.truetype(font_path, 44)
        f_small = ImageFont.truetype(font_path, 19)
        d.text((20, 296), "疯狂科学家", font=f_big, fill=(*GREEN, 255),
               stroke_width=4, stroke_fill=(10, 14, 10, 255))
        d.text((22, 352), "THE MAD SCIENTIST", font=f_small, fill=(225, 235, 215, 255),
               stroke_width=3, stroke_fill=(10, 14, 10, 255))
    canvas.convert("RGB").save(OUT / "mod_image.png")

    # ---- extras: card art from the event's mad science cards, tinted green ----
    print("done")


if __name__ == "__main__":
    main()
