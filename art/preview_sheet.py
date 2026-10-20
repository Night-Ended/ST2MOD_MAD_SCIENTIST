"""Offline previews for the mod page / docs.

Not part of the mod.  Renders:
  docs/select_mockup.png  - the character select backdrop + portrait composition
  docs/anim_preview.png   - contact sheet of the combat animation key poses

The poses mirror MadScientistVisuals.cs (same offsets/rotations/scales), so this
is a good approximation of what the in-game AnimationPlayer does.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "MadScientist" / "images"
DOCS = ROOT / "docs"
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"

GREEN = (168, 224, 95)


def select_mockup() -> None:
    bg = Image.open(IMG / "events" / "select_bg.png").convert("RGB").resize((1920, 1080))
    canvas = bg.convert("RGBA")

    portrait = Image.open(IMG / "charui" / "char_select_mad_scientist.png").convert("RGBA")
    scale = 3.4
    p = portrait.resize((int(portrait.width * scale), int(portrait.height * scale)), Image.LANCZOS)
    canvas.alpha_composite(p, (250, 1080 - p.height - 90))

    d = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_B, 64)
    f_sub = ImageFont.truetype(FONT, 26)
    d.text((250, 120), "疯狂科学家", font=f_title, fill=GREEN, stroke_width=5, stroke_fill=(8, 12, 9, 255))
    d.text((252, 200), "THE MAD SCIENTIST", font=f_sub, fill=(226, 236, 220), stroke_width=3, stroke_fill=(8, 12, 9, 255))

    # fake info panel on the right, just for composition
    panel = Image.new("RGBA", (470, 560), (12, 16, 13, 170))
    canvas.alpha_composite(panel, (1330, 260))
    d.text((1362, 300), "生命 70 / 70", font=ImageFont.truetype(FONT, 34), fill=(230, 235, 225))
    d.text((1362, 360), "初始遗物：燃烧之血（占位）", font=ImageFont.truetype(FONT, 26), fill=(190, 200, 185))
    d.text((1362, 420), "卡池：疯狂科学家", font=ImageFont.truetype(FONT, 26), fill=(190, 200, 185))
    canvas.convert("RGB").save(DOCS / "select_mockup.png")


def anim_preview() -> None:
    sprite = Image.open(IMG / "character" / "combat.png").convert("RGBA")
    w, h = sprite.size
    pad = 40
    cell_w, cell_h = w + pad * 2, h + pad * 2

    poses = [
        ("待机 0.0s", 0, 0, -0.010, 1.000, 1.000, 1.0, (255, 255, 255)),
        ("待机 1.4s", 0, -5, 0.012, 1.004, 0.996, 1.0, (255, 255, 255)),
        ("攻击 蓄力", -6, 2, -0.030, 0.970, 1.040, 1.0, (255, 255, 255)),
        ("攻击 命中", 46, -8, 0.075, 1.060, 0.940, 1.0, (255, 248, 210)),
        ("施法", 0, -14, 0.000, 1.050, 1.050, 1.0, (200, 255, 210)),
        ("受击", -11, 1, -0.030, 1.000, 1.000, 1.0, (255, 140, 130)),
    ]

    sheet = Image.new("RGB", (cell_w * 3, (cell_h + 60) * 2 + 70), (24, 28, 26))
    d = ImageDraw.Draw(sheet)
    label_font = ImageFont.truetype(FONT, 24)
    title_font = ImageFont.truetype(FONT_B, 34)
    d.text((20, 6), "战斗动画关键帧预览（与代码里的关键帧一致）", font=title_font, fill=GREEN)

    for i, (label, dx, dy, rot, sx, sy, alpha, tint) in enumerate(poses):
        cell = Image.new("RGBA", (cell_w, cell_h), (34, 38, 36, 255))
        # ground line
        gd = ImageDraw.Draw(cell)
        gd.line([(30, cell_h - 44), (cell_w - 30, cell_h - 44)], fill=(60, 66, 62), width=2)

        frame = sprite.copy()
        frame.putalpha(frame.getchannel("A").point(lambda v: int(v * alpha)))
        frame = frame.resize((int(w * sx), int(h * sy)), Image.LANCZOS)
        frame = frame.rotate(-rot * 57.2958, resample=Image.BICUBIC, center=(frame.width // 2, frame.height))
        tint_layer = Image.new("RGBA", frame.size, (*tint, 0))
        r, g, b, a = frame.split()
        tr = Image.merge("RGBA", (
            r.point(lambda v: min(255, int(v * tint[0] / 255))),
            g.point(lambda v: min(255, int(v * tint[1] / 255))),
            b.point(lambda v: min(255, int(v * tint[2] / 255))),
            a,
        ))
        frame = Image.blend(frame, tr, 0.55) if tint != (255, 255, 255) else frame
        cell.alpha_composite(frame, (pad + dx, cell_h - 44 - frame.height + dy))

        col, row = i % 3, i // 3
        sheet.paste(cell.convert("RGB"), (col * cell_w, 50 + row * (cell_h + 60)))
        d.text((col * cell_w + 16, 50 + row * (cell_h + 60) + cell_h + 16), label,
               font=label_font, fill=(200, 210, 195))

    sheet.save(DOCS / "anim_preview.png")


if __name__ == "__main__":
    DOCS.mkdir(exist_ok=True)
    select_mockup()
    anim_preview()
    print("previews written to docs/")
