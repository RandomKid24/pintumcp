"""Render the pet from npm/lib/pet.json into assets/ (icon PNG + animated GIF)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
pet = json.loads((ROOT / "npm/lib/pet.json").read_text())
pal = {k: tuple(v) for k, v in pet["palette"].items()}
BG_TOP, BG_BOT = (30, 36, 82), (12, 14, 38)


def sprite(name, px):
    rows = pet["frames"][name]
    im = Image.new("RGBA", (len(rows[0]) * px, len(rows) * px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                d.rectangle((x * px, y * px, (x + 1) * px - 1, (y + 1) * px - 1), fill=pal[c] + (255,))
    return im


def background(size):
    g = Image.linear_gradient("L").resize((size, size))
    return Image.composite(Image.new("RGB", (size, size), BG_BOT), Image.new("RGB", (size, size), BG_TOP), g).convert("RGBA")


def compose(name, size, px):
    im = background(size)
    s = sprite(name, px)
    d = ImageDraw.Draw(im)
    gy = (size + s.height) // 2 - px // 2  # soft pixel shadow under the feet
    d.rectangle(((size - 10 * px) // 2, gy, (size + 10 * px) // 2, gy + px // 2), fill=(6, 8, 24, 255))
    im.alpha_composite(s, ((size - s.width) // 2, (size - s.height) // 2))
    return im


def squircle(im):
    n = im.width
    m = Image.new("L", (n, n), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, n - 1, n - 1), radius=int(n * 0.225), fill=255)
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


icon = squircle(compose(pet["icon_frame"], 512, 22))
icon.save(ROOT / "assets/pintumcp-icon.png")

frames = [compose(n, 360, 16).convert("P", palette=Image.ADAPTIVE) for n in pet["sequence"]]
frames[0].save(ROOT / "assets/pintumcp-pet.gif", save_all=True, append_images=frames[1:],
               duration=pet["delay_ms"], loop=0, disposal=2)
