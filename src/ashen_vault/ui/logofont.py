"""The 5x7 capitals of the Ashen Vault wordmark. Pure data, no raylib: docs/logo/make_logo.py draws
the SVG logo with them and the HUD draws the title and other big headings with them, scaled up by a
whole number of pixels so the two always match."""

HEIGHT = 7
GAP = 1  # glyph pixels between letters
SPACE = 3  # glyph pixels a space advances

# Each glyph is seven rows: '#' lit, '.' empty. The width is the row length.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#..##", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
}


def advance(ch):
    """Glyph pixels `ch` takes, without the gap after it."""
    return SPACE if ch == " " else len(FONT[ch][0])


def width(s, px=1):
    """Screen pixels `s` spans at `px` pixels per glyph pixel."""
    if not s:
        return 0
    return (sum(advance(ch) for ch in s) + GAP * (len(s) - 1)) * px


def cells(s):
    """Yields (gx, gy) of every lit glyph pixel in `s`, in glyph pixels from the top-left."""
    gx = 0
    for ch in s:
        if ch != " ":
            for gy, row in enumerate(FONT[ch]):
                for i, bit in enumerate(row):
                    if bit == "#":
                        yield gx + i, gy
        gx += advance(ch) + GAP


def rects(s, x, y, px=1):
    """Yields (x, y, w, h) squares covering `s` at `px` pixels per glyph pixel, top-left at (x, y)."""
    for gx, gy in cells(s):
        yield x + gx * px, y + gy * px, px, px
