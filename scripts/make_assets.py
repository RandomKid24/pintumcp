"""Render the pet from npm/lib/pet.json into assets/ (icons, per-event icons, animated GIF)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
pet = json.loads((ROOT / "npm/lib/pet.json").read_text())
PALETTE = {k: tuple(v) for k, v in pet["palette"].items()}
BG_TOP, BG_BOT = (30, 36, 82), (12, 14, 38)


def sprite(name, px):
    rows = pet["frames"][name]
    pal = {**PALETTE, **{k: tuple(v) for k, v in pet.get("tints", {}).get(name, {}).items()}}
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

(ROOT / "assets/transparent/icons").mkdir(parents=True, exist_ok=True)
(ROOT / "assets/transparent/previews").mkdir(exist_ok=True)
for name in ("idle", "blink", "waveA", "waveB"):  # the pet alone, transparent background
    sprite(name, 24).save(ROOT / f"assets/transparent/icons/pintu-{name}.png")


def transparent_gif(path, names, px=16, pad=2):
    frames = []
    for n in names:
        s = sprite(n, px)
        im = Image.new("RGBA", (s.width + 2 * pad * px, s.height + 2 * pad * px), (0, 0, 0, 0))
        im.alpha_composite(s, (pad * px, pad * px))
        p = im.convert("RGB").quantize(255)
        alpha = im.getchannel("A").point(lambda a: 255 if a < 128 else 0)
        p.paste(255, mask=alpha)  # index 255 = transparent
        frames.append(p)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=pet["delay_ms"],
                   loop=0, disposal=2, transparency=255)


transparent_gif(ROOT / "assets/transparent/previews/pintu-pet.gif", pet["sequence"])

# Drop-in transparent twins of assets/icons/*.png (same 512px canvas and scale, pet only),
# plus a small animated GIF per pose: it hops, and sparkles blink.
for event in ("done", "question", "approval", "error"):
    s = sprite(event, 22)
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.alpha_composite(s, ((512 - s.width) // 2, (512 - s.height) // 2))
    canvas.save(ROOT / f"assets/transparent/icons/{event}.png")

    rows = pet["frames"][event]
    hop = ["." * len(rows[0])] + [r.replace("Y", ".") for r in rows[:-1]]  # up one pixel, no sparkles
    pet["frames"][f"{event}_hop"] = hop
    pet.setdefault("tints", {})[f"{event}_hop"] = pet["tints"].get(event, {})
    transparent_gif(ROOT / f"assets/transparent/previews/pintu-{event}.gif", [event, f"{event}_hop"])
(ROOT / "assets/icons").mkdir(exist_ok=True)
for event in ("done", "question", "approval", "error"):
    squircle(compose(event, 512, 22)).save(ROOT / f"assets/icons/{event}.png")

frames = [compose(n, 360, 16).convert("P", palette=Image.ADAPTIVE) for n in pet["sequence"]]
frames[0].save(ROOT / "assets/pintumcp-pet.gif", save_all=True, append_images=frames[1:],
               duration=pet["delay_ms"], loop=0, disposal=2)


# Illustration of the popups (rendered, not a screenshot) for the README.
def preview(transparent=False):
    from PIL import ImageFont

    font = "/System/Library/Fonts/Helvetica.ttc"
    try:
        title_f, body_f = ImageFont.truetype(font, 30, index=1), ImageFont.truetype(font, 27)
    except OSError:  # non-macOS machine: skip, the committed PNG stays as is
        return
    cards = [
        ("done", "API · Agent 2: Task Complete", "3 tasks completed: Built API; Wrote tests; Fixed lint"),
        ("approval", "API · Agent 1: Approval Needed", "Approve deploying v2.4.0 to production?"),
        ("error", "Web: Error", "Build failed: missing dependency 'lodash'"),
    ]
    W, H, pad, ch = 980, 0, 36, 132
    H = pad + len(cards) * (ch + 24)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)) if transparent else background(W).crop((0, 0, W, H)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for i, (event, title, body) in enumerate(cards):
        y = pad // 2 + i * (ch + 24) + 12
        shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((pad, y + 6, W - pad, y + ch + 6), radius=30, fill=(0, 0, 0, 110))
        from PIL import ImageFilter
        img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((pad, y, W - pad, y + ch), radius=30, fill=(244, 244, 248, 255))
        icon = Image.open(ROOT / f"assets/icons/{event}.png").resize((96, 96), Image.LANCZOS)
        img.alpha_composite(icon, (pad + 22, y + 18))
        d.text((pad + 142, y + 26), title, font=title_f, fill=(20, 20, 30, 255))
        d.text((pad + 142, y + 72), body, font=body_f, fill=(70, 72, 90, 255))
    img.save(ROOT / ("assets/transparent/previews/alert-preview.png" if transparent else "assets/alert-preview.png"))


preview()
preview(transparent=True)
