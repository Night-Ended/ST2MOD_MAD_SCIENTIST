"""Turn the AI generated art (art/incoming) into the mod's image files.

Inputs
  art/incoming/base/base_v2.png        full body, flat white background
  art/incoming/assets/portrait.png     bust
  art/incoming/assets/icon.png         head
  art/incoming/assets/select_bg.png    cave laboratory background
  art/incoming/assets/design.png       character design sheet (docs only)

Outputs (MadScientist/images/...)
  character/combat.png                 700 px tall, feet on the bottom edge
  charui/char_select_mad_scientist.png 132x195 (+ _locked silhouette)
  charui/character_icon_*.png          88x88 (+ white outline version)
  charui/map_marker_mad_scientist.png  49x64
  events/select_bg.png                 1920x1080

Run: python art/build_ai_assets.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
INCOMING = ROOT / "art" / "incoming"
OUT = ROOT / "MadScientist" / "images"
DOCS = ROOT / "docs"


# --------------------------------------------------------------------------- #
# white background removal
# --------------------------------------------------------------------------- #
def cut_white(im: Image.Image, thresh: int = 22, shadow: bool = True, corners=None) -> Image.Image:
    """Remove a flat white background, keeping the character's white coat.

    Uses a flood fill from the four corners so enclosed white areas (the lab
    coat) are not touched.  The soft grey ground shadow is removed separately by
    dropping low-saturation pixels in the bottom part of the image.
    """
    rgb = im.convert("RGB")
    w, h = rgb.size
    sentinel = (255, 0, 255)
    probe = rgb.copy()
    seeds = corners or ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))
    for corner in seeds:
        if probe.getpixel(corner) != sentinel:
            ImageDraw.floodfill(probe, corner, sentinel, thresh=thresh)

    arr = np.asarray(probe)
    bg = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 255)
    alpha = (~bg).astype(np.float32)

    if shadow:
        a = np.asarray(rgb).astype(np.float32) / 255.0
        mx = a.max(2)
        mn = a.min(2)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        yy = np.arange(h)[:, None]
        bottom = yy > h * 0.72
        shadow_mask = bottom & (sat < 0.13) & (mx > 0.55)
        alpha[shadow_mask] = 0.0

    # enclosed pure-white pockets (between the backpack straps, between the arm
    # and the body, inside the wrench, ...) are not reachable from the border.
    # The lab coat is white too, but shaded, so a high threshold only hits the
    # flat background leftovers.
    mn = np.asarray(rgb).min(2)
    alpha[(mn >= 248) & (~bg)] = 0.0

    alpha_img = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    out = rgb.convert("RGBA")
    out.putalpha(alpha_img)
    return out


def cut_dark(im: Image.Image, thresh: int = 45) -> Image.Image:
    """Key out a flat dark background (used for the portrait with the teal backdrop)."""
    rgb = im.convert("RGB")
    w, h = rgb.size
    sentinel = (255, 0, 255)
    probe = rgb.copy()
    for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(probe, corner, sentinel, thresh=thresh)
    arr = np.asarray(probe)
    bg = (arr[:, :, 0] == 255) & (arr[:, :, 1] == 0) & (arr[:, :, 2] == 255)
    alpha = Image.fromarray(((~bg) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    out = rgb.convert("RGBA")
    out.putalpha(alpha)

    # eat the dark glow fringe that the flood fill leaves around the head
    arr = np.asarray(out).astype(np.int16).copy()
    corners = [np.asarray(rgb.getpixel((0, 0))), np.asarray(rgb.getpixel((w - 1, 0))),
               np.asarray(rgb.getpixel((0, h - 1))), np.asarray(rgb.getpixel((w - 1, h - 1)))]
    bgc = np.median(np.stack(corners), axis=0)
    dist = np.sqrt(((arr[:, :, :3] - bgc) ** 2).sum(2))
    a = arr[:, :, 3]
    for _ in range(8):
        trans = a < 20
        neigh = np.zeros_like(trans)
        neigh[1:, :] |= trans[:-1, :]
        neigh[:-1, :] |= trans[1:, :]
        neigh[:, 1:] |= trans[:, :-1]
        neigh[:, :-1] |= trans[:, 1:]
        kill = (a > 0) & neigh & (dist < 85)
        if not kill.any():
            break
        a[kill] = 0
    arr[:, :, 3] = a
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def bbox(im: Image.Image, thresh: int = 8) -> tuple[int, int, int, int]:
    a = np.asarray(im.getchannel("A"))
    ys, xs = np.where(a > thresh)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def resize_rgba(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    a = im.getchannel("A")
    rgb = im.convert("RGB")
    black = Image.new("RGB", im.size, (0, 0, 0))
    pm = Image.composite(rgb, black, a).resize(size, Image.LANCZOS)
    a2 = a.resize(size, Image.LANCZOS)
    arr = np.asarray(pm).astype(np.float32) / np.maximum(np.asarray(a2).astype(np.float32) / 255.0, 1e-3)[..., None]
    arr[np.asarray(a2) < 3] = 0
    return Image.merge("RGBA", (*Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).split(), a2))


def silhouette(im: Image.Image, size: tuple[int, int], color=(8, 8, 10)) -> Image.Image:
    a = im.getchannel("A").resize(size, Image.LANCZOS)
    layer = Image.new("RGBA", size, (*color, 0))
    layer.putalpha(a)
    return layer


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    (OUT / "character").mkdir(parents=True, exist_ok=True)
    (OUT / "charui").mkdir(parents=True, exist_ok=True)
    (OUT / "events").mkdir(parents=True, exist_ok=True)

    # ---- full body ----
    body_src = Image.open(INCOMING / "assets" / "base_dark2.png")
    body = cut_dark(body_src, thresh=46)
    x0, y0, x1, y1 = bbox(body)
    body = body.crop((x0, y0, x1, y1))
    h = 700
    body = resize_rgba(body, (round(body.width * h / body.height), h))
    body.save(OUT / "character" / "combat.png")
    print("combat", body.size)

    # ---- portrait: vanilla event-art cutout (per request, not the AI one) ----
    ev = Image.open(ROOT / "art" / "ref" / "event_cutout.png").convert("RGBA")
    portrait = ev.crop((150, 20, 480, 507))
    p = resize_rgba(portrait, (132, 195))
    p.save(OUT / "charui" / "char_select_mad_scientist.png")
    silhouette(p, (132, 195)).save(OUT / "charui" / "char_select_mad_scientist_locked.png")
    print("portrait", p.size)

    # ---- icon ----
    icon_src = cut_white(Image.open(INCOMING / "assets" / "icon.png"), thresh=24, corners=[(0, 0), (1023, 0)])
    iw, ih = icon_src.size
    side = int(min(iw, ih) * 0.94)
    icon = icon_src.crop(((iw - side) // 2, (ih - side) // 2,
                          (iw - side) // 2 + side, (ih - side) // 2 + side))
    icon88 = resize_rgba(icon, (88, 88))
    icon88.save(OUT / "charui" / "character_icon_mad_scientist.png")
    white = Image.new("RGBA", (88, 88), (255, 255, 255, 0))
    white.putalpha(icon88.getchannel("A"))
    white.save(OUT / "charui" / "character_icon_mad_scientist_outline.png")
    print("icon", icon88.size)

    # ---- map marker ----
    resize_rgba(body, (49, 64)).save(OUT / "charui" / "map_marker_mad_scientist.png")

    # ---- select background ----
    bg = Image.open(INCOMING / "assets" / "select_bg.png").convert("RGB")
    bw, bh = bg.size
    target = 16 / 9
    if bw / bh > target:
        nw = int(bh * target)
        bg = bg.crop(((bw - nw) // 2, 0, (bw - nw) // 2 + nw, bh))
    else:
        nh = int(bw / target)
        bg = bg.crop((0, (bh - nh) // 2, bw, (bh - nh) // 2 + nh))
    bg.resize((1920, 1080), Image.LANCZOS).save(OUT / "events" / "select_bg.png")

    # ---- design sheet for the docs ----
    Image.open(INCOMING / "assets" / "design.png").save(DOCS / "design_sheet.png")
    print("done")


if __name__ == "__main__":
    main()
