"""Build animated menu-bar frames for Pintu: assets/menubar/<name>_<i>.png (36x32, 18x16pt @2x).

Existing states reuse the pet GIF frames; extra moods (sweater, coffee, music, sleep) are drawn
on the 22x20 pixel grid. Run: python3 tools/gen_menubar.py
"""
from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).parent.parent / "npm" / "python" / "assets"
OUT = ASSETS / "menubar"
X0, Y0, W, H = 2, 2, 18, 16  # crop of the 22x20 grid -> 36x32 at 2px per cell

BODY, SHADE, EYE, WHITE = (72, 214, 190), (40, 160, 150), (16, 22, 52), (255, 255, 255)
SWEATER, CREAM, STEAM, NOTE = (255, 107, 80), (255, 226, 150), (190, 200, 220), (255, 184, 48)


def grid(gif, n):
    im = Image.open(ASSETS / "pet" / f"{gif}.gif"); im.seek(n); im = im.convert("RGBA")
    return {(x, y): p for x in range(22) for y in range(20)
            if (p := im.getpixel((x * 16 + 8, y * 16 + 8)))[3] > 10}


def put(g, color, *cells):
    for c in cells:
        g[c] = color + (255,) if len(color) == 3 else color
    return g


def blink(g):                       # eyes -> single line
    return put(g, BODY, (7, 9), (8, 9), (13, 9), (14, 9))


def sweater(g):
    for y in (11, 12, 13):
        for x in range(3, 19):
            if (x, y) in g:
                g[(x, y)] = (CREAM if y == 12 and x % 2 else SWEATER) + (255,)
    return g


def coffee(g, steam):
    for y in (11, 12, 13):
        put(g, WHITE, (18, y), (19, y))
    return put(g, STEAM, (19, 9) if steam else (18, 9), (18, 10) if steam else (19, 10))


def music(g, up):
    for y in (8, 9, 10):
        put(g, EYE, (3, y), (18, y))
    return put(g, NOTE, (16, 4) if up else (17, 4), (16, 3) if up else (17, 5), (17, 3) if up else (16, 5))


def sleep(g, n):
    blink(g); put(g, EYE, (7, 10), (8, 10), (13, 10), (14, 10))
    z = {0: [(16, 5)], 1: [(16, 5), (17, 4), (18, 4)], 2: [(16, 5), (17, 5), (18, 5), (17, 4), (18, 3), (16, 3), (17, 3)]}[n]
    return put(g, NOTE, *z)


DARK, GLOW, PINK = (58, 65, 80), (154, 216, 255), (255, 107, 80)


def hat(g):
    put(g, DARK, *[(x, y) for x in range(7, 15) for y in (2, 3)], *[(x, 5) for x in range(6, 16)])
    return put(g, SWEATER, *[(x, 4) for x in range(7, 15)])


def glasses(g, wink):
    for lx in (6, 12):
        cells = [(lx + i, y) for i in range(4) for y in (8, 11)] + [(lx, y) for y in (9, 10)] + [(lx + 3, y) for y in (9, 10)]
        put(g, EYE, *cells)
    put(g, EYE, (10, 9), (11, 9))
    return put(g, GLOW, (7, 9)) if wink else g


def umbrella(g, n):
    put(g, SWEATER, *[(x, 0) for x in range(7, 15)], *[(x, 1) for x in range(5, 17)], *[(x, 2) for x in range(4, 18)])
    put(g, CREAM, (6, 1), (10, 1), (14, 1), (5, 2), (9, 2), (13, 2))
    put(g, (150, 170, 200), (10, 3), (11, 3), (10, 4), (11, 4), (10, 5), (11, 5))
    for x, y in ((1, 3), (20, 4), (2, 9), (19, 8), (0, 13), (21, 12)):
        put(g, GLOW, (x, (y + n * 2) % 15 + 2))
    return g


def party(g, n):
    put(g, CREAM, (10, 0), (11, 0), (9, 2), (10, 2), (11, 2), (12, 2))
    put(g, SWEATER, (10, 1), (11, 1), *[(x, 3) for x in range(8, 14)])
    for x, y in ((2, 4), (19, 3), (1, 9), (20, 8), (3, 14), (18, 15)):
        if (n + x) % 3:
            put(g, (NOTE, SWEATER, GLOW)[(x + n) % 3], (x, y))
    return g


def faces():
    """Transparent 128px faces for notifications (assets/faces/<name>.png)."""
    out = ASSETS / "faces"
    out.mkdir(exist_ok=True)
    def render(g, name):
        xs, ys = [x for x, _ in g], [y for _, y in g]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        im = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1))
        for (x, y), p in g.items():
            im.putpixel((x - x0, y - y0), p)
        k = max(1, 120 // max(im.size))
        im = im.resize((im.width * k, im.height * k), Image.NEAREST)
        canvas = Image.new("RGBA", (128, 128))
        canvas.alpha_composite(im, ((128 - im.width) // 2, (128 - im.height) // 2))
        canvas.save(out / f"{name}.png")
    for name, gif, n in (("done", "done", 1), ("approval", "approval", 0), ("question", "question", 0), ("error", "error", 0),
                         ("thinking", "working", 0), ("sleepy", "idle", 0), ("stuck", "question", 1)):
        render(grid(gif, n), name)
    render(party(grid("done", 1), 1), "party")


def save(name, frames):
    for i, g in enumerate(frames):
        im = Image.new("RGBA", (W * 2, H * 2))
        for (x, y), p in g.items():
            if X0 <= x < X0 + W and Y0 <= y < Y0 + H:
                im.paste(p, ((x - X0) * 2, (y - Y0) * 2, (x - X0) * 2 + 2, (y - Y0) * 2 + 2))
        im.save(OUT / f"{name}_{i}.png")


def main():
    for old in OUT.glob("*.png"):
        old.unlink()
    for state in ("approval", "done", "error", "question", "working", "idle"):
        n = Image.open(ASSETS / "pet" / f"{state}.gif").n_frames
        save(state, [grid(state, i) for i in range(n)])
    save("empty", [grid("empty", i) for i in range(8)])       # the wave
    base = lambda: {c: p for c, p in grid("working", 0).items() if c[1] != 3 or c[0] < 14}  # drop the typing dots
    save("sweater", [sweater(base()), sweater(blink(base()))] * 2)
    save("coffee", [coffee(base(), s) for s in (0, 1, 0, 1)])
    save("music", [music(base(), u) for u in (0, 1, 0, 1)])
    save("sleep", [sleep(base(), n) for n in (0, 1, 2, 1)])
    save("hat", [hat(base()), hat(blink(base()))] * 2)
    save("glasses", [glasses(base(), w) for w in (0, 1, 0, 0)])
    save("umbrella", [umbrella(base(), n) for n in range(4)])
    save("party", [party(grid("done", i % 2), i) for i in range(4)])
    faces()


if __name__ == "__main__":
    main()
