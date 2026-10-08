"""Build Pintu's sprite sheet (npm/lib/pet.json) from one base body plus face parts.

Run: python3 scripts/build_pet.py && python3 scripts/make_assets.py
Legend: B body, D belt, K outline, H highlight, P blush, E ink, W glint, A amber bell,
L stalk, Y light yellow, R pink-red, C blue (tear/star), '.' empty.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASE = """\
..................
........AA........
.......AAAA.......
........LL........
...BBBBBBBBBBBB...
..BBBBBBBBBBBBBB..
..BBBBBBBBBBBBBB..
..BBBBBBBBBBBBBB..
..BBBBBBBBBBBBBB..
.BBBBBBBBBBBBBBBB.
.BBBBBBBBBBBBBBBB.
..BBBBBBBBBBBBBB..
...DDDDDDDDDDDD...
....BBB....BBB....
....BBB....BBB....
..................""".split("\n")


def put(g, pts, c):
    for x, y in pts:
        g[y][x] = c


def px(g, rows, c, x0=0):
    """Draw an ASCII sketch (x = ink) at column x0, row index from the list order (y, string)."""
    for y, line in rows:
        for i, ch in enumerate(line):
            if ch == "x":
                g[y][x0 + i] = c


EYE_L, EYE_R = (5, 6), (11, 12)


def eyes_open(g, glint="tl"):
    for xs in (EYE_L, EYE_R):
        put(g, [(x, y) for x in xs for y in (7, 8)], "E")
        put(g, [(xs[0] if glint == "tl" else xs[1], 7)], "W")


def clear(g, xs, ys):
    put(g, [(x, y) for x in xs for y in ys], "B")


def smile(g):
    put(g, [(7, 10), (10, 10), (8, 11), (9, 11)], "E")


def frown(g):
    put(g, [(8, 10), (9, 10), (7, 11), (10, 11)], "E")


def arms_down(g):
    pass  # the base already has them


def arm_up_right(g, hand=(4, 5, 6)):
    put(g, [(16, 9), (16, 10)], ".")
    put(g, [(16, 8), (16, 7), (16, 6)], "B")
    put(g, [(17, y) for y in hand], "B")


def both_arms_up(g):
    put(g, [(1, 9), (1, 10), (16, 9), (16, 10)], ".")
    put(g, [(1, 8), (1, 7), (1, 6), (0, 5), (0, 4), (16, 8), (16, 7), (16, 6), (17, 5), (17, 4)], "B")


def ping(g, near):
    xs = (5, 12) if near else (4, 13)
    put(g, [(x, y) for x in xs for y in (1, 2)], "Y")


def make():
    f = {}

    def new():
        g = [list(r) for r in BASE]
        eyes_open(g)
        smile(g)
        return g

    g = new(); f["idle"] = g
    g = new(); clear(g, (5, 6, 11, 12), (7,)); f["blink"] = g

    g = new(); arm_up_right(g); ping(g, True); f["waveA"] = g
    g = new(); arm_up_right(g, (5, 6, 7)); ping(g, False); f["waveB"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); both_arms_up(g)
    put(g, [(4, 8), (5, 7), (6, 8), (11, 8), (12, 7), (13, 8)], "E")
    put(g, [(0, 1), (1, 2), (17, 1), (16, 2), (3, 0), (14, 0)], "Y"); f["done"] = g

    g = new(); put(g, [(15, 0), (16, 0), (17, 0), (17, 1), (16, 2), (17, 2), (16, 4)], "A"); f["question"] = g

    g = new(); arm_up_right(g, (4, 5, 6))
    put(g, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 4), (1, 4)], "A"); f["approval"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); frown(g); clear(g, (7, 10), (10, 10))
    put(g, [(4, 7), (6, 7), (5, 8), (11, 7), (13, 7), (12, 8)], "E"); f["error"] = g

    g = new(); put(g, [(11, 8), (12, 8), (13, 8)], "E"); clear(g, (11, 12), (7,)); clear(g, (12,), (8,))
    put(g, [(13, 7)], "B"); put(g, [(11, 8), (12, 8), (13, 8)], "E"); put(g, [(5, 7), (6, 7), (5, 8), (6, 8)], "E"); put(g, [(5, 7)], "W")
    put(g, [(6, 10)], "E"); f["wink"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); clear(g, (7, 10), (10, 10)); clear(g, (8, 9), (11,))
    for xs in (EYE_L, EYE_R):
        put(g, [(x, y) for x in xs for y in (6, 7, 8)], "E")
    put(g, [(5, 6), (11, 6)], "W"); put(g, [(8, 10), (9, 10), (8, 11), (9, 11)], "E"); f["surprised"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); clear(g, (7, 10), (10, 10)); clear(g, (8, 9), (11,))
    put(g, [(4, 8), (5, 8), (6, 8), (11, 8), (12, 8), (13, 8)], "E"); put(g, [(8, 10), (9, 10)], "E")
    px(g, [(0, "xxxx"), (1, "..x."), (2, ".x.."), (3, "xxxx")], "Y", 14); f["sleepy"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8))
    put(g, [(4, 7), (6, 7), (4, 8), (5, 8), (6, 8), (5, 9), (11, 7), (13, 7), (11, 8), (12, 8), (13, 8), (12, 9)], "R"); f["love"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); clear(g, (7, 10), (10, 10)); clear(g, (8, 9), (11,))
    for xs in (EYE_L, EYE_R):
        put(g, [(x, y) for x in xs for y in (7, 8)], "E")
    put(g, [(6, 7), (12, 7)], "W"); put(g, [(8, 11), (9, 11)], "E")
    put(g, [(13, 1), (15, 1), (17, 1)], "Y"); f["thinking"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); put(g, [(5, 8), (6, 8), (11, 8), (12, 8)], "E")
    put(g, [(4, 6), (5, 7), (6, 7), (13, 6), (12, 7), (11, 7)], "E"); clear(g, (7, 10), (10, 10)); frown(g); f["angry"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); clear(g, (7, 10), (10, 10))
    put(g, [(4, 7), (5, 7), (6, 7), (4, 8), (6, 8), (4, 9), (5, 9), (6, 9), (11, 7), (12, 7), (13, 7), (11, 8), (13, 8), (11, 9), (12, 9), (13, 9)], "E")
    put(g, [(7, 10), (8, 11), (9, 10), (10, 11)], "E"); put(g, [(1, 2), (16, 3), (3, 1), (14, 1)], "Y"); f["dizzy"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8))
    put(g, [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7)], "E")
    put(g, [(4, 8), (5, 8), (6, 8), (11, 8), (12, 8), (13, 8)], "E"); put(g, [(4, 7)], "W"); f["cool"] = g

    g = new(); clear(g, (7, 10), (10, 10)); frown(g); put(g, [(5, 9), (5, 10)], "C")
    put(g, [(4, 6), (5, 6)], "E") if False else None; f["sad"] = g

    g = new(); clear(g, (5, 6, 11, 12), (7, 8)); both_arms_up(g)
    put(g, [(4, 8), (5, 7), (6, 8), (11, 8), (12, 7), (13, 8)], "E"); clear(g, (7, 10), (10, 10))
    put(g, [(7, 10), (8, 10), (9, 10), (10, 10), (8, 11), (9, 11)], "E")
    put(g, [(0, 1), (3, 0), (14, 0), (17, 1), (2, 3), (15, 3), (1, 7)], "R")
    put(g, [(1, 2), (16, 2), (4, 1), (13, 1)], "A"); put(g, [(0, 3), (17, 4), (2, 1), (15, 1)], "C"); f["party"] = g

    return {k: finish(v, k) for k, v in f.items()}


# Flat look (the original Pintu). Set True for a dark outline, head highlight and blush.
OUTLINE = False


def finish(g, name):
    """Optionally pad by one cell and add an outline around the body, a highlight and blush."""
    if not OUTLINE:
        return ["".join(r) for r in g]
    rows = [list("." + "".join(r) + ".") for r in g]
    rows = [["."] * (len(rows[0]))] + rows + [["."] * (len(rows[0]))]
    if name not in ("error",):
        put(rows, [(4, 6), (5, 6), (4, 7)], "H")  # shifted by the 1-cell pad
    for x, y in ((4, 10), (15, 10)):
        if rows[y][x] == "B":
            rows[y][x] = "P"
    solid = {"B", "D", "H", "P"}
    h, w = len(rows), len(rows[0])
    out = [r[:] for r in rows]
    for y in range(h):
        for x in range(w):
            if rows[y][x] == ".":
                near = [rows[yy][xx] for xx, yy in ((x+1, y), (x-1, y), (x, y+1), (x, y-1))
                        if 0 <= xx < w and 0 <= yy < h]
                if any(c in solid for c in near):
                    out[y][x] = "K"
    return ["".join(r) for r in out]


pet = {
    "palette": {
        "B": [72, 214, 190], "D": [40, 160, 150], "K": [22, 104, 112], "H": [150, 240, 225],
        "P": [255, 160, 180], "E": [16, 22, 52], "W": [255, 255, 255], "A": [255, 184, 48],
        "L": [150, 170, 200], "Y": [255, 226, 150], "R": [255, 92, 130], "C": [120, 200, 255],
    },
    "frames": make(),
    "tints": {
        "error": {"B": [255, 122, 122], "D": [205, 80, 92], "K": [150, 50, 64], "H": [255, 180, 180], "P": [255, 150, 150]},
        "angry": {"B": [255, 150, 110], "D": [215, 100, 70], "K": [150, 60, 40], "H": [255, 200, 170]},
    },
    "sequence": ["idle", "idle", "blink", "idle", "waveA", "waveB", "waveA", "waveB", "idle"],
    "delay_ms": 380,
    "icon_frame": "waveA",
}
(ROOT / "npm/lib/pet.json").write_text(json.dumps(pet, indent=1) + "\n")
print(len(pet["frames"]), "frames:", ", ".join(pet["frames"]))
