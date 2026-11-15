"""Generates docs/logo/ashen_vault.svg: a pixel-art emblem and wordmark.

Run: python3 docs/logo/make_logo.py
"""

import math
import os
import sys

# The letters live with the game, so the logo is set in the title screen's own fonts: the wordmark in
# the 5x7 capitals (`hud.big`) and the tagline in the small mixed-case font of its menu (`hud.text`).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
from ashen_vault.ui import logofont, smallfont

# The title screen's colours (ui/hud.py): HIGHLIGHT for the wordmark, DIM for the tagline, the HUD's
# gold trim for the frame, and its black drop shadow.
HIGHLIGHT = "#ffdc8c"
DIM = "#8c826e"
EDGE = "#aa8746"
SHADOW = "#000000"

# The silent bell: B = bronze body, c = crack, k = clapper.
BELL = [
    "......#......",
    ".....#.#.....",
    "....BBBBB....",
    "...BBBBBBB...",
    "...BBBcBBB...",
    "...BBBBcBB...",
    "..BBBBBcBBB..",
    "..BBBBcBBBB..",
    "..BBBBBcBBB..",
    ".BBBBBBBcBBB.",
    "BBBBBBBBBBBBB",
    ".............",
    "......k......",
]


def h(x, y, seed=7):
    v = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return (v ^ (v >> 16)) / 0xFFFFFFFF


def shade(rgb, k):
    return "#{:02x}{:02x}{:02x}".format(*tuple(max(0, min(255, round(c * k))) for c in rgb))


def emblem(ox, oy, s):
    """21x24 pixel stone arch with the bell inside, top-left at (ox, oy), pixel size s."""
    out = []
    w, top_h, legs = 21, 11, 12
    cx, cy = 10, 10.5
    for y in range(top_h + legs):
        for x in range(w):
            if y < top_h:
                d = math.hypot(x - cx, y - cy)
                stone, inside = 8 <= d < 10.6, d < 8
            else:
                stone, inside = x < 2 or x > 18, 2 <= x <= 18
            px, py = ox + x * s, oy + y * s
            if stone:
                mortar = (x + (y // 2) * 3) % 4 == 0 and y % 2 == 0
                k = 0.45 if mortar else 0.8 + h(x, y) * 0.35
                out.append(
                    f'<rect x="{px}" y="{py}" width="{s}" height="{s}" fill="{shade((118, 110, 100), k)}"/>'
                )
            elif inside:
                # Ember glow rising from the floor of the vault.
                glow = max(0.0, 1 - (top_h + legs - 1 - y) / 13) ** 2 * (0.75 + h(x, y, 3) * 0.5)
                col = (int(14 + 230 * glow), int(10 + 110 * glow), int(8 + 30 * glow))
                out.append(f'<rect x="{px}" y="{py}" width="{s}" height="{s}" fill="#%02x%02x%02x"/>' % col)
    bx, by = ox + 4 * s, oy + 3 * s
    for y, row in enumerate(BELL):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if ch == "B":
                k = 1.15 - (x / 12) * 0.55 + (0.1 if y == 10 else 0)
                fill = shade((200, 150, 80), k)
            elif ch == "c":
                fill = "#1a0f08"
            elif ch == "k":
                fill = "#8a6038"
            else:
                fill = "#6e4a2a"
            out.append(f'<rect x="{bx + x * s}" y="{by + y * s}" width="{s}" height="{s}" fill="{fill}"/>')
    return out


def pixels(runs, px, fill, ox, oy, shadow=None):
    """SVG rects for font runs (x, y, w, h in glyph pixels from the text's top-left), `px` screen pixels
    each, offset to (ox, oy); with `shadow`, a drop shadow first, offset like `hud.big`'s."""
    runs = list(runs)
    out = []
    if shadow:
        off = max(px // 2, 1)
        for x, y, w, h in runs:
            out.append(
                f'<rect x="{ox + x * px + off}" y="{oy + y * px + off}" width="{w * px}" height="{h * px}" '
                f'fill="{shadow}" fill-opacity="0.8"/>'
            )
    for x, y, w, h in runs:
        out.append(
            f'<rect x="{ox + x * px}" y="{oy + y * px}" width="{w * px}" height="{h * px}" fill="{fill}"/>'
        )
    return out


def wordmark(s, cx, y, px):
    """`s` in the title's 5x7 capitals, centred on `cx`, with its drop shadow."""
    x = cx - logofont.width(s, px) // 2
    return pixels(logofont.rects(s, 0, 0), px, HIGHLIGHT, x, y, shadow=SHADOW)


def tagline(s, cx, y, px):
    """`s` in the menu's small mixed-case font, centred on `cx`."""
    x = cx - smallfont.width(s) * px // 2
    return pixels(smallfont.rects(s, 0, 0), px, DIM, x, y)


def main():
    W, H = 640, 200
    parts = [
        f'<rect width="{W}" height="{H}" rx="14" fill="#14100c"/>',
        f'<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="11" fill="none" stroke="{EDGE}" stroke-width="2"/>',
    ]
    parts += emblem(34, 28, 6)
    cx = 405  # the middle of the space right of the emblem
    parts += wordmark("ASHEN VAULT", cx, 58, 6)
    parts += tagline("beneath the silent bell", cx, 122, 3)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'shape-rendering="crispEdges" role="img" aria-label="Ashen Vault">'
        f"<title>Ashen Vault</title>{''.join(parts)}</svg>\n"
    )
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ashen_vault.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
