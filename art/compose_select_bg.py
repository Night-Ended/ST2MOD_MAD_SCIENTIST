"""Compose the character select background with the character standing on it.

The base game draws the big character as part of the character-select background
scene (a Spine diorama), not from char_select_*.png — that small portrait is only
the button art.  So for this mod we bake the event-art cutout into the right half
of the background, where the vanilla characters stand (the info panel is on the
left).

Run: python art/compose_select_bg.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "MadScientist" / "images"
EMPTY = ROOT / "art" / "incoming" / "assets" / "select_bg.png"   # clean cave, no character
CUTOUT = ROOT / "art" / "ref" / "event_cutout.png"

CANVAS = (1920, 1080)
FIG_HEIGHT = 800
FEET_Y = 1030
CENTER_X = 1345
FLIP = True  # face left, towards the info panel


def main() -> None:
    bg = Image.open(EMPTY).convert("RGB")
    # cover the canvas
    bw, bh = bg.size
    target = CANVAS[0] / CANVAS[1]
    if bw / bh > target:
        nw = int(bh * target)
        bg = bg.crop(((bw - nw) // 2, 0, (bw - nw) // 2 + nw, bh))
    else:
        nh = int(bw / target)
        bg = bg.crop((0, (bh - nh) // 2, bw, (bh - nh) // 2 + nh))
    bg = bg.resize(CANVAS, Image.LANCZOS)
    canvas = bg.convert("RGBA")

    fig = Image.open(CUTOUT).convert("RGBA")
    if FLIP:
        fig = fig.transpose(Image.FLIP_LEFT_RIGHT)
    s = FIG_HEIGHT / fig.height
    fig = fig.resize((max(1, int(fig.width * s)), FIG_HEIGHT), Image.LANCZOS)

    # slight colour match to the cave: a bit darker, a touch cooler in the shadows
    arr = np.asarray(fig).astype(np.float32)
    arr[:, :, :3] *= 0.93
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.03 + 2, 0, 255)
    fig = Image.fromarray(arr.astype(np.uint8), "RGBA")

    x = CENTER_X - fig.width // 2
    y = FEET_Y - fig.height

    # contact shadow
    shadow = Image.new("L", CANVAS, 0)
    sd = ImageDraw.Draw(shadow)
    sw, sh = int(fig.width * 0.78), 54
    sd.ellipse((CENTER_X - sw // 2, FEET_Y - sh // 2, CENTER_X + sw // 2, FEET_Y + sh // 2), fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    shadow_layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    shadow_layer.putalpha(shadow)
    canvas.alpha_composite(shadow_layer)

    # green bounce light from the lab flasks on the left side of the figure
    glow = Image.new("L", CANVAS, 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((x - 40, y + fig.height * 0.45, x + fig.width * 0.55,
                FEET_Y + 40), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    glow_layer = Image.new("RGBA", CANVAS, (60, 120, 70, 0))
    glow_layer.putalpha(glow)
    canvas.alpha_composite(glow_layer)

    canvas.alpha_composite(fig, (x, y))

    # subtle vignette so the character sits in the scene
    yy, xx = np.mgrid[0:CANVAS[1], 0:CANVAS[0]]
    dx = (xx - CANVAS[0] / 2) / (CANVAS[0] / 2)
    dy = (yy - CANVAS[1] / 2) / (CANVAS[1] / 2)
    r = np.sqrt(dx * dx + dy * dy)
    v = np.clip(1.0 - 0.30 * np.clip(r - 0.45, 0, 1.0) ** 1.5, 0.55, 1.0)
    arr = np.asarray(canvas).astype(np.float32)
    arr[:, :, :3] *= v[..., None]
    canvas = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    canvas.convert("RGB").save(IMG / "events" / "select_bg.png")
    canvas.convert("RGB").save(ROOT / "docs" / "select_bg_composed.png")
    print("composited", canvas.size, "figure at", (x, y), fig.size)


if __name__ == "__main__":
    main()
