"""Generates docs/logo/ashen_vault.svg: a pixel-art emblem and wordmark.

Run: python3 docs/logo/make_logo.py
"""

import math
import os

FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
}

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


def text(s, ox, oy, px, fill, shadow=None):
    out = []
    x = ox
    for ch in s:
        if ch == " ":
            x += 4 * px
            continue
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, c in enumerate(row):
                if c != "#":
                    continue
                if shadow:
                    out.append(
                        f'<rect x="{x + gx * px + px // 2}" y="{oy + gy * px + px // 2}" width="{px}" '
                        f'height="{px}" fill="{shadow}"/>'
                    )
                out.append(
                    f'<rect x="{x + gx * px}" y="{oy + gy * px}" width="{px}" height="{px}" fill="{fill}"/>'
                )
        x += (len(glyph[0]) + 1) * px
    return out, x - px - ox


def main():
    W, H = 640, 200
    parts = [
        f'<rect width="{W}" height="{H}" rx="14" fill="#14100c"/>',
        f'<rect x="3" y="3" width="{W - 6}" height="{H - 6}" rx="11" fill="none" stroke="#78644a" stroke-width="2"/>',
    ]
    parts += emblem(34, 28, 6)
    title, tw = text("ASHEN VAULT", 200, 62, 6, "#ffdc8c", shadow="#3a2410")
    parts += title
    tag, _ = text("BENEATH THE SILENT BELL", 202, 124, 3, "#8c826e")
    parts += tag
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'shape-rendering="crispEdges" role="img" aria-label="Ashen Vault">'
        f"<title>Ashen Vault</title>{''.join(parts)}</svg>\n"
    )
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ashen_vault.svg")
    with open(path, "w") as f:
        f.write(svg)
    print(f"wrote {path} (wordmark {tw}px wide)")


if __name__ == "__main__":
    main()
