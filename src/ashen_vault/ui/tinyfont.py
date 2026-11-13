"""A 3x5 pixel font for the compact HUD. Pure data, no raylib: the HUD turns
the pixel runs into rectangles. raylib's built-in font is 10 px tall and
smears when scaled down on the point-filtered 320x240 target."""

ADVANCE = 4  # 3 px glyph + 1 px gap
HEIGHT = 5

# Each glyph is five rows of three bits, most significant bit = left column.
GLYPHS = {
    " ": (0, 0, 0, 0, 0),
    "A": (2, 5, 7, 5, 5),
    "B": (6, 5, 6, 5, 6),
    "C": (3, 4, 4, 4, 3),
    "D": (6, 5, 5, 5, 6),
    "E": (7, 4, 6, 4, 7),
    "F": (7, 4, 6, 4, 4),
    "G": (3, 4, 5, 5, 3),
    "H": (5, 5, 7, 5, 5),
    "I": (7, 2, 2, 2, 7),
    "J": (1, 1, 1, 5, 2),
    "K": (5, 5, 6, 5, 5),
    "L": (4, 4, 4, 4, 7),
    "M": (5, 7, 7, 5, 5),
    "N": (6, 5, 5, 5, 5),
    "O": (2, 5, 5, 5, 2),
    "P": (6, 5, 6, 4, 4),
    "Q": (2, 5, 5, 6, 3),
    "R": (6, 5, 6, 5, 5),
    "S": (3, 4, 2, 1, 6),
    "T": (7, 2, 2, 2, 2),
    "U": (5, 5, 5, 5, 7),
    "V": (5, 5, 5, 5, 2),
    "W": (5, 5, 7, 7, 5),
    "X": (5, 5, 2, 5, 5),
    "Y": (5, 5, 2, 2, 2),
    "Z": (7, 1, 2, 4, 7),
    "0": (7, 5, 5, 5, 7),
    "1": (2, 6, 2, 2, 7),
    "2": (6, 1, 2, 4, 7),
    "3": (6, 1, 2, 1, 6),
    "4": (5, 5, 7, 1, 1),
    "5": (7, 4, 6, 1, 6),
    "6": (3, 4, 7, 5, 7),
    "7": (7, 1, 1, 2, 2),
    "8": (7, 5, 7, 5, 7),
    "9": (7, 5, 7, 1, 6),
    "/": (1, 1, 2, 4, 4),
    ".": (0, 0, 0, 0, 2),
    "-": (0, 0, 7, 0, 0),
    ":": (0, 2, 0, 2, 0),
    "'": (2, 2, 0, 0, 0),
    "!": (2, 2, 2, 0, 2),
}


def width(s):
    """Pixel width of `s`, without the trailing gap."""
    return max(len(s) * ADVANCE - 1, 0)


def rects(s, x, y):
    """Yields (x, y, w, h) runs covering the lit pixels of `s`. Unknown characters draw as spaces."""
    for i, ch in enumerate(s.upper()):
        rows = GLYPHS.get(ch, GLYPHS[" "])
        gx = x + i * ADVANCE
        for row, bits in enumerate(rows):
            col = 0
            while col < 3:
                if not bits & (4 >> col):
                    col += 1
                    continue
                start = col
                while col < 3 and bits & (4 >> col):
                    col += 1
                yield gx + start, y + row, col - start, 1
