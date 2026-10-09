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


if __name__ == "__main__":
    main()
