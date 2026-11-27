"""Herran's Castle's dressing: its great walls' buttresses and string courses, its windows and arrow
loops, his banners, standards and tapestries bearing the hand, the sconces and fire-baskets held up in
iron hands, and the anatomist's household goods (charts, specimen jars, surgical trolleys, the stitched
dead hung up on the walls, chains), with the broken statues and the storm's rubble. Original low-poly
models assembled from primitives, in the castle's sooted dark ashlar, black slate, lead and iron.

A wall prop is drawn with its wall at local -X (the tile's edge at x = -1); a piece built down a great
wall's face (`castle_buttress`) stands on the wall's own tile with its face at `FACE`, +X out of it.
All are static, baked once, but the sconce and the brazier, whose flames move."""

import math
import random

from ashen_vault.render.herran_models import (
    CASTLE,
    CASTLE_DARK,
    GILT,
    LEAD,
    OAK_DARK,
    PALLID,
    PANE,
    SLATE,
    STATUE_DARK,
    STATUE_MOSS,
    STATUE_STONE,
    STITCH,
    SUN_GOLD,
    TABARD,
    TABARD_TRIM,
    TALLOW,
    WINDOW_DARK,
    WINDOW_LIT,
    gargoyle_spout,
)
from ashen_vault.render.parts import _bar, _dim, _flame, ribcage, skull

FACE = 1.0  # a wall tile's face, from its centre
WALL = -1.0  # the wall behind a wall prop, from its tile's centre
STORM_LIT = (176, 196, 232)  # a window lit cold by the storm behind it
CANDLE_LIT = WINDOW_LIT
# The dressed stone of buttresses, surrounds and statues, a shade lighter than the walls they stand out
# from, and wrought iron, which must read against the dark stone it hangs on.
DRESSED = (230, 230, 240)  # (the castle_stone texture darkens it to the walls' own grey)
DRESSED_DARK = (170, 170, 182)
WROUGHT = (70, 68, 76)
PARCHMENT = (206, 188, 150)
INK = (52, 40, 34)
SEPIA = (140, 70, 52)  # the red-brown wash of a drawn muscle
BLOOD = (110, 24, 22)
WAX_RED = (150, 30, 28)
CLOTH_DARK = _dim(TABARD, 0.7)
WOOL = (88, 70, 60)  # the tapestry's woven ground, browned with age
GRAFT_SKIN = (176, 150, 132)  # another man's arm, sewn on
SOOT = (30, 28, 32)
WET = (34, 40, 52)  # rainwater pooled in the theatre's flags
COAL = (255, 120, 50)
CASTLE_CRACK = (
    (12, 12, 16),
    (44, 44, 52),
    (150, 170, 220),
)  # cracks in castle stone: rain-dark, a cold glint
WINDOW_HEAD = 1.7  # metres a window's surround reaches above its `rise`
BANNER_TOP = 0.3  # and a banner's brackets above its pole


def hand_sigil(r, x, y, z, size, rgb, sun=SUN_GOLD, face=1):
    """Herran's device, the open hand, on a cloth or stone face turned toward `face` * +X: a palm, four
    fingers fanned apart, a thumb, a sun with eight rays in its palm, and a row of black stitches across
    the wrist where the hand was sewn on."""
    x = x + face * 0.004
    r.part("cube", x, y, z, 0.02, size * 0.5, size * 0.46, rgb)  # the palm
    for f in range(4):  # the fingers, fanned apart
        spread = (f - 1.5) * 0.16
        fz = z + (f - 1.5) * size * 0.13
        length = size * (0.3 if f in (0, 3) else 0.36)
        with r.at(x, y + size * 0.25, fz, rx=spread):
            r.part("cube", 0, length / 2, 0, 0.02, length, size * 0.085, rgb)
    with r.at(x, y - size * 0.05, z - size * 0.25, rx=-0.9):  # the thumb, out to the side
        r.part("cube", 0, size * 0.14, 0, 0.02, size * 0.28, size * 0.09, rgb)
    r.part("cube", x, y - size * 0.34, z, 0.02, size * 0.2, size * 0.26, rgb)  # the wrist
    sx = x + face * 0.012
    r.part("cyl", sx, y, z, size * 0.2, 0.02, size * 0.2, sun, rz=math.pi / 2)  # the sun in the palm
    for k in range(8):
        with r.at(sx, y, z, rx=k * math.pi / 4):
            r.part("cube", 0, size * 0.15, 0, 0.02, size * 0.08, size * 0.025, sun)
    for k in range(5):  # the stitches across the wrist
        r.part(
            "cube", sx, y - size * 0.26, z + (k - 2) * size * 0.05, 0.02, size * 0.07, size * 0.012, STITCH
        )
    r.part("cube", sx, y - size * 0.26, z, 0.02, size * 0.012, size * 0.24, STITCH)  # the seam


# --- the great walls ------------------------------------------------------------------------------


def _pinnacle(r, x, y, z, height, width):
    """A pinnacle rising from (x, y, z): a square shaft with a blind arch on each face, a gablet at its
    head, then a crocketed spirelet of slate and a leaded finial."""
    shaft = height * 0.4
    r.part("cube", x, y + shaft / 2, z, width, shaft, width, DRESSED, tex="castle_stone")
    for k in range(4):
        a = k * math.pi / 2
        r.part("cube", x + math.cos(a) * (width / 2 + 0.01), y + shaft * 0.55, z + math.sin(a) * (width / 2 + 0.01),
               0.02, shaft * 0.55, width * 0.4, SOOT, ry=-a)  # fmt: skip  # its blind arch
    r.part("cube", x, y + shaft + 0.05, z, width * 1.15, 0.1, width * 1.15, DRESSED_DARK)  # the cap
    spire = height - shaft
    r.part(
        "pyramid", x, y + shaft + spire / 2, z, width * 0.95, spire, width * 0.95, SLATE, tex="castle_slate"
    )
    for k in range(3):  # crockets up its edges
        h = y + shaft + spire * (0.2 + 0.25 * k)
        w = width * 0.48 * (1 - 0.2 - 0.25 * k)
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            r.part("cube", x + dx * w, h, z + dz * w, 0.1, 0.1, 0.1, DRESSED_DARK)
    r.part("sphere", x, y + height + 0.05, z, 0.14, 0.14, 0.14, LEAD)  # the finial's knop
    r.part("cube", x, y + height + 0.3, z, 0.05, 0.4, 0.05, LEAD)


def castle_buttress(r, seed, top=14.0, foot=0.0, span=2.0):
    """A buttress built down a great wall's face, from its top to the ground it stands on, with the
    wall's dressing `span` metres along either side of it: a chamfered plinth, two string courses and
    a corbel table under the wall's head. The buttress steps back in three stages under sloped
    set-offs (shallow enough at its foot to walk past), Herran's hand carved on a shield on its middle
    stage, a gargoyle spout at its head with its rain stain run down below it, and a crocketed
    pinnacle rising over the wall top."""
    rng = random.Random(seed)
    h = top - foot
    tex = "castle_stone"
    r.part("cube", FACE + 0.09, foot + 0.35, 0, 0.18, 0.7, span, DRESSED_DARK, tex=tex)  # the plinth
    r.part("wedge", FACE, foot + 0.78, 0, 0.36, 0.16, span, DRESSED_DARK)  # its chamfer
    for k in (0.5, 0.76):  # the string courses
        y = foot + h * k
        r.part("cube", FACE + 0.08, y, 0, 0.16, 0.22, span, DRESSED_DARK, tex=tex)
        r.part("cube", FACE + 0.13, y - 0.13, 0, 0.06, 0.05, span, SOOT)  # its drip, dark with rain
    n = max(1, int(span / 0.55))  # the corbel table under the wall's head
    for i in range(n):
        z = -span / 2 + (i + 0.5) * span / n
        r.part("cube", FACE + 0.15, top - 1.15, z, 0.3, 0.32, 0.2, DRESSED_DARK, tex=tex)
        r.part("cube", FACE + 0.08, top - 1.38, z, 0.16, 0.14, 0.16, DRESSED_DARK)
    r.part("cube", FACE + 0.2, top - 0.86, 0, 0.4, 0.26, span, DRESSED, tex=tex)  # the cornice on them
    for _ in range(4):  # weathered stones, darker in the face
        y = foot + 1.0 + rng.random() * (h - 3.0)
        z = (rng.random() - 0.5) * (span - 0.6)
        r.part("cube", FACE + 0.006, y, z, 0.01, 0.3 + rng.random() * 0.3, 0.4 + rng.random() * 0.5,
               _dim(DRESSED, 0.72))  # fmt: skip
    stages = ((0.36, 1.3, 0.38), (0.28, 1.14, 0.7), (0.2, 1.0, 0.92))  # depth, width, top as a share
    y0 = foot
    for d, w, k in stages:
        y1 = foot + h * k
        r.part("cube", FACE + d / 2, (y0 + y1) / 2, 0, d, y1 - y0, w, DRESSED, tex=tex)
        r.part("wedge", FACE, y1 + 0.22, 0, 2 * d, 0.44, w, DRESSED_DARK)  # its sloped set-off
        y0 = y1 + 0.44
    mid = foot + h * 0.54  # the shield on the middle stage, the hand carved on it
    r.part("cube", FACE + 0.31, mid, 0, 0.06, 0.8, 0.62, STATUE_STONE)
    r.part("pyramid", FACE + 0.31, mid - 0.55, 0, 0.06, 0.3, 0.62, STATUE_STONE, rx=math.pi)
    hand_sigil(r, FACE + 0.34, mid + 0.02, 0, 0.5, STATUE_DARK, sun=STATUE_DARK)
    r.part("cube", FACE + 0.205, foot + h * 0.62, 0.0, 0.01, h * 0.5, 0.18, SOOT)  # the rain stain
    gargoyle_spout(r, FACE + 0.2, top - 1.6, 0, 1.2)
    _pinnacle(r, FACE - 0.3, top, 0, 3.2, 0.6)


# --- windows and banners --------------------------------------------------------------------------


def _surround(r, w, h, depth=0.16):
    """A window's dressed surround on the wall at local -X, its light `w` by `h` centred on the origin:
    long and short blocks up its jambs, voussoirs round its pointed head, a hood mould with carved stops
    and a sill with its drip."""
    x = WALL + depth / 2
    for side in (-1, 1):
        for k in range(4):  # the jambs' blocks, long and short in turn
            y = -h / 2 + (k + 0.5) * h / 4
            wide = 0.2 if k % 2 else 0.3
            r.part(
                "cube",
                x,
                y,
                side * (w / 2 + wide / 2),
                depth,
                h / 4 - 0.02,
                wide,
                DRESSED_DARK,
                tex="castle_stone",
            )
        with r.at(x, h / 2, side * w / 2, rx=-side * 0.6):  # the head's voussoirs, to a point
            r.part("cube", 0, w * 0.42, 0, depth, w * 0.9, 0.22, DRESSED_DARK, tex="castle_stone")
        with r.at(x + 0.06, h / 2 + 0.08, side * (w / 2 + 0.2), rx=-side * 0.6):  # the hood mould
            r.part("cube", 0, w * 0.5, 0, 0.1, w * 1.05, 0.08, DRESSED)
        r.part(
            "cube", x + 0.08, h / 2 + 0.05, side * (w / 2 + 0.34), 0.12, 0.14, 0.12, STATUE_STONE
        )  # a stop
    r.part(
        "cube", WALL + 0.12, -h / 2 - 0.08, 0, 0.24, 0.12, w + 0.5, DRESSED, tex="castle_stone"
    )  # the sill
    r.part("cube", WALL + 0.2, -h / 2 - 0.17, 0, 0.08, 0.05, w + 0.4, SOOT)  # its drip


def _light(r, w, h, rgb, glow):
    """A window's light against the wall at local -X: a pane under a pointed head, its leading laid in
    diamonds over it."""
    r.part("cube", WALL + 0.02, 0, 0, 0.02, h, w, rgb, glow=glow)
    r.part("pyramid", WALL + 0.02, h / 2 + w * 0.38, 0, 0.02, w * 0.76, w, rgb, glow=glow)
    for k in (-1, 0, 1):  # the leading, crossed
        for lean in (-0.7, 0.7):
            r.part("cube", WALL + 0.035, k * h * 0.3, 0, 0.01, 0.014, w * 1.3, LEAD, rx=lean)


def castle_window(r, seed, light="candle", style="lancet"):
    """A window in the castle's wall at local -X, its sill at the origin's -0.9: a pointed `lancet`
    behind an iron grille, a `twin` pair under one arch with a quatrefoil over the mullion, or a `loop`,
    an arrow loop's cross-slit with round oillets at its ends. Lit by `light`: "candle" (amber, a
    candle's shape or a hanged man's shadow against it), "storm" (cold, the lightning's), "dark"."""
    lit = light in ("candle", "storm")
    rgb = {"candle": CANDLE_LIT, "storm": STORM_LIT}.get(light, WINDOW_DARK)
    if style == "loop":
        r.part("cube", WALL + 0.06, 0, 0, 0.12, 2.0, 0.8, DRESSED_DARK, tex="castle_stone")  # its block
        r.part("cube", WALL + 0.1, 0, 0, 0.06, 1.7, 0.56, DRESSED, tex="castle_stone")  # the splay
        for side in (-1, 1):  # the quoins either side, long and short in turn, and the splay's shadow
            for k in range(4):
                wide = 0.22 if k % 2 else 0.32
                r.part("cube", WALL + 0.08, -0.75 + k * 0.5, side * (0.4 + wide / 2), 0.16, 0.48, wide,
                       DRESSED_DARK, tex="castle_stone")  # fmt: skip
            r.part("cube", WALL + 0.128, 0, side * 0.12, 0.01, 1.5, 0.08, SOOT)
        r.part("cube", WALL + 0.1, 1.08, 0, 0.2, 0.18, 1.3, DRESSED, tex="castle_stone")  # the lintel
        r.part("cube", WALL + 0.19, 1.0, 0, 0.04, 0.04, 1.3, SOOT)  # its drip
        r.part("cube", WALL + 0.135, 0, 0, 0.02, 1.4, 0.1, rgb, glow=lit)  # the slit
        r.part("cube", WALL + 0.135, 0.15, 0, 0.02, 0.1, 0.46, rgb, glow=lit)  # its cross-arm
        for y, z in ((0.72, 0.0), (-0.72, 0.0), (0.15, 0.25), (0.15, -0.25)):  # the oillets
            r.part("cyl", WALL + 0.135, y, z, 0.13, 0.02, 0.13, rgb, rz=math.pi / 2, glow=lit)
        r.part("cube", WALL + 0.14, -1.05, 0, 0.2, 0.1, 0.9, DRESSED_DARK)  # the sill
        return
    w, h = (1.2, 1.8) if style == "twin" else (0.7, 1.8)
    _surround(r, w, h)
    if style == "twin":
        for side in (-1, 1):
            with r.at(0, -0.1, side * 0.3):
                _light(r, 0.44, 1.5, rgb, lit)
        r.part("cube", WALL + 0.07, -0.1, 0, 0.12, 1.7, 0.12, DRESSED_DARK)  # the mullion
        r.part(
            "cyl", WALL + 0.02, h / 2 + 0.36, 0, 0.36, 0.02, 0.36, rgb, rz=math.pi / 2, glow=lit
        )  # quatrefoil
        for k in range(4):
            with r.at(WALL + 0.04, h / 2 + 0.36, 0, rx=k * math.pi / 2 + math.pi / 4):
                r.part("cube", 0, 0.12, 0, 0.03, 0.14, 0.05, DRESSED_DARK)  # its cusps
        r.part("cube", WALL + 0.05, h / 2 + 0.05, 0, 0.08, 0.5, w, DRESSED_DARK)  # the spandrel
    else:
        _light(r, w, h, rgb, lit)
        for z in (-0.18, 0.18):  # the grille
            r.part("cube", WALL + 0.08, 0, z, 0.04, h + 0.1, 0.04, WROUGHT)
        for y in (-0.5, 0.1, 0.65):
            r.part("cube", WALL + 0.08, y, 0, 0.04, 0.04, w + 0.06, WROUGHT)
    if light == "candle":  # what stands in the window: a candle, or a shadow hanging in the room
        if seed % 3 == 0:
            with r.at(WALL + 0.04, -0.55, 0.12):  # a hanged shape against the light
                r.part("cube", 0, 0.3, 0, 0.01, 0.6, 0.16, SOOT)
                r.part("cube", 0, 0.7, 0, 0.01, 0.14, 0.12, SOOT)
                r.part("cube", 0, 1.05, 0, 0.01, 0.6, 0.02, SOOT)
        else:
            r.part("cube", WALL + 0.06, -0.72, 0, 0.06, 0.24, 0.06, TALLOW)  # a candle on the sill
            r.part("cone", WALL + 0.06, -0.54, 0, 0.04, 0.1, 0.04, (255, 236, 170), glow=True)


def hand_banner(r, seed, rise=3.4, length=2.4, style="banner"):
    """Herran's banner hung on the wall at local -X from a pole `rise` metres up on two iron brackets,
    `length` metres of wine-dark cloth bordered in tarnished gold, its swallowtail hem trimmed, the
    open hand with the sun in its palm worked large on it, gilt hands for the pole's finials and
    tassels on cords at its ends. A `tapestry` is broader and woven: the Many-Handed himself, robed,
    his eight arms fanned out behind him under a sun, two of his grafted men kneeling either side, a
    border of small hands across its head and a fringe along its foot."""
    x = WALL + 0.12
    wide = 1.8 if style == "tapestry" else 0.9
    for side in (-1, 1):  # the brackets
        _bar(r, (WALL, rise + BANNER_TOP, side * wide * 0.42), (x, rise, side * wide * 0.42), 0.05, WROUGHT)
        r.part("cube", WALL + 0.02, rise + BANNER_TOP, side * wide * 0.42, 0.04, 0.16, 0.1, WROUGHT)
    r.part("cyl", x, rise, 0, 0.05, wide + 0.3, 0.05, OAK_DARK, rx=math.pi / 2)  # the pole
    for side in (-1, 1):  # its finials, little gilt hands, and the tassels
        z = side * (wide / 2 + 0.17)
        r.part("cube", x, rise + 0.06, z, 0.04, 0.1, 0.08, GILT)
        for f in range(3):
            r.part("cube", x, rise + 0.14, z + (f - 1) * 0.026, 0.03, 0.08, 0.018, GILT)
        r.part("cube", x, rise - 0.25, z - side * 0.04, 0.012, 0.5, 0.012, TABARD_TRIM)
        r.part("cone", x, rise - 0.55, z - side * 0.04, 0.06, 0.16, 0.06, TABARD_TRIM, rz=math.pi)
    top = rise - 0.06
    if style == "tapestry":
        _tapestry(r, x, top, length, wide)
        return
    body = length - 0.45
    r.part("cube", x, top - body / 2, 0, 0.03, body, wide, TABARD)
    for side in (-1, 1):  # the swallowtail
        r.part(
            "wedge",
            x,
            top - body - 0.22,
            side * wide / 4,
            wide / 2,
            0.45,
            0.03,
            TABARD,
            rz=math.pi,
            ry=math.pi / 2,
        )
        r.part(
            "cube", x + 0.017, top - body / 2, side * (wide / 2 - 0.04), 0.01, body, 0.05, TABARD_TRIM
        )  # its border
        r.part(
            "cube",
            x + 0.017,
            top - body - 0.2,
            side * wide * 0.24,
            0.01,
            0.48,
            0.04,
            TABARD_TRIM,
            rx=side * 0.5,
        )
    r.part("cube", x + 0.017, top - 0.08, 0, 0.01, 0.05, wide, TABARD_TRIM)
    r.part("cube", x + 0.017, top - 0.2, 0, 0.01, 0.025, wide - 0.1, CLOTH_DARK)
    size = min(wide * 0.82, body * 0.5)
    hand_sigil(r, x + 0.016, top - body * 0.42, 0, size, GILT)
    for k in range(3):  # three bars of gold thread beneath it, the household's count of years
        r.part("cube", x + 0.017, top - body * 0.78 - k * 0.1, 0, 0.01, 0.04, wide * 0.5, TABARD_TRIM)
    r.part(
        "cube", x + 0.02, top - body * 0.15 - (seed % 3) * 0.2, wide * 0.3, 0.01, 0.12, 0.08, CLOTH_DARK
    )  # a tear


def _tapestry(r, x, top, length, wide):
    """The Many-Handed's tapestry under its pole, in the cloth's frame on the wall at local -X."""
    f = x + 0.017  # its face
    mid = top - length / 2
    r.part("cube", x, mid, 0, 0.03, length, wide, WOOL)
    for side in (-1, 1):  # the border
        r.part("cube", f, mid, side * (wide / 2 - 0.06), 0.01, length, 0.1, TABARD)
        r.part("cube", f + 0.002, mid, side * (wide / 2 - 0.13), 0.01, length - 0.2, 0.03, TABARD_TRIM)
    r.part("cube", f, top - 0.2, 0, 0.01, 0.36, wide - 0.2, TABARD)
    r.part("cube", f, top - length + 0.12, 0, 0.01, 0.2, wide - 0.2, TABARD)
    for k in range(5):  # small hands across its head
        hand_sigil(r, f, top - 0.2, -0.56 + k * 0.28, 0.22, TABARD_TRIM, sun=GILT)
    for k in range(18):  # the fringe
        z = -wide / 2 + 0.05 + k * (wide - 0.1) / 17
        r.part(
            "cube",
            x,
            top - length - 0.08 - (k % 3) * 0.02,
            z,
            0.012,
            0.18 + (k % 3) * 0.04,
            0.02,
            TABARD_TRIM,
        )
    sky = top - length * 0.4  # the scene: a sun behind him, his arms fanned under it
    r.part("cyl", f, sky + 0.25, 0, 0.62, 0.01, 0.62, _dim(SUN_GOLD, 0.8), rz=math.pi / 2)
    for k in range(12):
        with r.at(f, sky + 0.25, 0, rx=k * math.pi / 6):
            r.part("cube", 0, 0.42, 0, 0.01, 0.18, 0.04, _dim(SUN_GOLD, 0.7))
    for k in range(8):  # his eight arms, four to a side, each ending in an open hand
        side = -1 if k < 4 else 1
        a = (0.35 + (k % 4) * 0.36) * side
        with r.at(f + 0.004, sky - 0.1, 0, rx=a):
            r.part("cube", 0, 0.3, 0, 0.01, 0.52, 0.05, PALLID)
            r.part("cube", 0, 0.58, 0, 0.01, 0.1, 0.09, PALLID)
            for g in range(3):
                r.part("cube", 0, 0.66, (g - 1) * 0.03, 0.01, 0.08, 0.016, PALLID)
            r.part("cube", 0, 0.2, 0, 0.012, 0.015, 0.06, STITCH)  # a seam where it was sewn on
    r.part("cube", f + 0.008, sky - 0.45, 0, 0.01, 0.8, 0.3, (60, 46, 54))  # his robe
    r.part("pyramid", f + 0.008, sky - 0.95, 0, 0.01, 0.4, 0.5, (60, 46, 54))
    r.part("cube", f + 0.009, sky - 0.15, 0, 0.01, 0.1, 0.34, TABARD_TRIM)  # its collar
    r.part("cube", f + 0.01, sky + 0.02, 0, 0.01, 0.2, 0.15, PALLID)  # his head
    r.part("cube", f + 0.012, sky + 0.02, 0, 0.01, 0.03, 0.1, SOOT)  # the band over his eyes
    for side in (-1, 1):  # a grafted man kneeling either side, his hands raised
        z = side * 0.6
        r.part("cube", f + 0.006, sky - 0.95, z, 0.01, 0.34, 0.16, CLOTH_DARK)  # body
        r.part("cube", f + 0.006, sky - 1.16, z - side * 0.05, 0.01, 0.1, 0.26, CLOTH_DARK)  # knees
        r.part("cube", f + 0.007, sky - 0.71, z, 0.01, 0.12, 0.1, PALLID)  # head
        r.part(
            "cube", f + 0.007, sky - 0.75, z - side * 0.13, 0.01, 0.26, 0.04, PALLID, rx=-side * 0.4
        )  # arm
    r.part(
        "cube", f + 0.004, sky - 1.3, 0, 0.01, 0.06, wide - 0.4, _dim(WOOL, 0.7)
    )  # the ground they kneel on


def hand_standard(r, seed, top=1.2):
    """A standard set in a parapet whose top is `top` metres up: a tall iron pole in a collar on the
    stone, a gilt open hand for its finial, a crossbar and Herran's swallowtail banner hanging from it,
    the hand worked on both faces, a long pennon streaming from its head and its cords tied off."""
    base = top
    r.part("cube", 0, base + 0.1, 0, 0.36, 0.2, 0.36, WROUGHT)  # the collar
    r.part("cyl", 0, base + 0.3, 0, 0.14, 0.2, 0.14, WROUGHT)
    r.part("cyl", 0, base + 2.6, 0, 0.07, 4.6, 0.07, WROUGHT)  # the pole
    head = base + 4.9
    r.part("cube", 0, head - 0.12, 0, 0.05, 0.16, 0.12, GILT)  # the hand's palm
    for f in range(4):
        with r.at(0, head - 0.04, (f - 1.5) * 0.035, rx=(f - 1.5) * 0.15):
            r.part("cube", 0, 0.08, 0, 0.04, 0.16, 0.025, GILT)
    r.part("cube", 0, head - 0.18, -0.08, 0.04, 0.12, 0.03, GILT, rx=-0.8)  # its thumb
    bar = head - 0.55
    r.part("cyl", 0, bar, 0, 0.05, 1.1, 0.05, WROUGHT, rx=math.pi / 2)  # the crossbar
    for side in (-1, 1):
        r.part("sphere", 0, bar, side * 0.56, 0.08, 0.08, 0.08, GILT)
        _bar(r, (0, bar + 0.6, 0), (0, bar, side * 0.5), 0.02, WROUGHT)  # its stays
    body = 2.0
    r.part("cube", 0, bar - body / 2, 0, 0.03, body, 0.86, TABARD)
    for side in (-1, 1):
        r.part(
            "wedge", 0, bar - body - 0.2, side * 0.215, 0.43, 0.4, 0.03, TABARD, rz=math.pi, ry=math.pi / 2
        )
        for face in (-1, 1):
            r.part("cube", face * 0.017, bar - body / 2, side * 0.4, 0.01, body, 0.05, TABARD_TRIM)
    for face in (-1, 1):
        r.part("cube", face * 0.017, bar - 0.07, 0, 0.01, 0.05, 0.86, TABARD_TRIM)
        hand_sigil(r, face * 0.016, bar - body * 0.45, 0, 0.66, GILT, face=face)
    sway = (seed % 3 - 1) * 0.1  # the pennon off its head
    for k in range(4):
        r.part(
            "cube",
            0,
            head - 0.35 - k * 0.04,
            0.3 + k * 0.32,
            0.02,
            0.18 - k * 0.035,
            0.34,
            TABARD,
            rx=sway * k,
        )
    _bar(r, (0, bar, 0.56), (0, base + 1.0, 0.25), 0.015, TABARD_TRIM)  # the cords, tied off on the pole
    _bar(r, (0, bar, -0.56), (0, base + 1.0, -0.25), 0.015, TABARD_TRIM)


# --- light: a sconce and a fire-basket held in iron hands ------------------------------------------


def _iron_hand(r, grip=0.08, size=1.0):
    """An iron hand closed round something running along Y through its fist at the origin: a palm
    behind, four fingers curled round in front and a thumb over them."""
    s = size
    r.part("cube", -0.05 * s, 0, 0, 0.06 * s, 0.14 * s, 0.12 * s, WROUGHT)  # the palm
    for f in range(4):
        y = (f - 1.5) * 0.034 * s
        r.part("cube", grip * 0.6 * s, y, 0.05 * s, 0.1 * s, 0.03 * s, 0.03 * s, WROUGHT, ry=0.6)
        r.part("cube", grip * 0.9 * s, y, -0.02 * s, 0.03 * s, 0.03 * s, 0.08 * s, WROUGHT)
    r.part("cube", 0.02 * s, 0.08 * s, -0.05 * s, 0.1 * s, 0.03 * s, 0.03 * s, WROUGHT, rz=-0.4)  # the thumb


def castle_sconce(r, t):
    """A torch held out from the wall at local -X in an iron hand: a riveted wall plate, an iron forearm
    out of it, the fist closed round a tarred torch burning in an iron cresset, a soot stain spread on
    the stone above the flame."""
    r.part("cube", WALL + 0.03, 1.75, 0, 0.06, 0.5, 0.3, WROUGHT)  # the plate
    r.part("pyramid", WALL + 0.03, 1.42, 0, 0.06, 0.16, 0.3, WROUGHT, rx=math.pi)
    for y in (1.92, 1.58):
        r.part("sphere", WALL + 0.07, y, 0, 0.04, 0.04, 0.04, LEAD)  # its rivets
    _bar(r, (WALL + 0.05, 1.7, 0), (WALL + 0.28, 1.6, 0), 0.07, WROUGHT)  # the forearm
    r.part("cube", WALL + 0.12, 1.66, 0, 0.04, 0.09, 0.09, LEAD)  # its cuff
    with r.at(WALL + 0.32, 1.62, 0, rz=-0.3):
        _iron_hand(r)
        r.part("cyl", 0.04, 0.1, 0, 0.06, 0.6, 0.06, OAK_DARK)  # the torch
        r.part("cyl", 0.04, 0.43, 0, 0.09, 0.12, 0.09, SOOT)  # its tarred head
        for k in range(4):  # the cresset's straps
            a = k * math.pi / 2
            r.part(
                "cube", 0.04 + math.cos(a) * 0.08, 0.46, math.sin(a) * 0.08, 0.02, 0.18, 0.02, WROUGHT, ry=-a
            )
        _flame(r, 0.04, 0.58, 0, 0.2, t)
    r.part("cube", WALL + 0.005, 2.55, 0, 0.01, 0.9, 0.4, SOOT)  # the soot on the stone above


def castle_brazier(r, t, lit=True):
    """A fire-basket of Herran's household: a stand of black iron on three clawed legs and a twisted
    stem, its bowl an iron hand cupped upward with its fingers curled round the coals, the fire
    burning in its palm (or a cold heap of ash, unlit)."""
    for k in range(3):  # the legs, splayed, each on a claw
        a = k * math.tau / 3
        foot = (math.cos(a) * 0.42, 0.06, math.sin(a) * 0.42)
        _bar(r, foot, (math.cos(a) * 0.1, 0.55, math.sin(a) * 0.1), 0.06, WROUGHT)
        for c in (-0.25, 0.0, 0.25):
            r.part("cone", foot[0] + math.cos(a + c) * 0.08, 0.04, foot[2] + math.sin(a + c) * 0.08, 0.04, 0.12,
                   0.04, WROUGHT, rz=-math.pi / 2, ry=-(a + c))  # fmt: skip
    for k in range(4):  # the twisted stem
        r.part("cube", 0, 0.65 + k * 0.14, 0, 0.07, 0.15, 0.07, WROUGHT, ry=k * 0.6)
    r.part("cyl", 0, 1.22, 0, 0.62, 0.12, 0.62, WROUGHT)  # the palm, a shallow bowl
    r.part("cyl", 0, 1.14, 0, 0.3, 0.08, 0.3, WROUGHT)
    for f in range(5):  # the fingers curling up round the coals, and the thumb across from them
        a = 0.3 + f * 0.85 if f < 4 else 4.6
        with r.at(math.cos(a) * 0.3, 1.26, math.sin(a) * 0.3, ry=-a):
            r.part("cube", 0, 0.12, 0, 0.06, 0.26, 0.08 if f < 4 else 0.1, WROUGHT, rz=0.25)
            r.part("cube", -0.06, 0.27, 0, 0.06, 0.12, 0.06, WROUGHT, rz=0.8)
            r.part("cube", -0.11, 0.33, 0, 0.05, 0.06, 0.05, WROUGHT, rz=1.3)  # the nail
    if not lit:
        r.part("cyl", 0, 1.3, 0, 0.48, 0.06, 0.48, (90, 88, 86))
        return
    r.part("cyl", 0, 1.3, 0, 0.48, 0.06, 0.48, COAL, glow=True)  # the coals
    _flame(r, 0, 1.55, 0, 0.5, t)
    _flame(r, 0.12, 1.45, 0.08, 0.28, t + 1.3)


# --- the anatomist's household --------------------------------------------------------------------


def _ink(r, x, a, b, thick=0.012, rgb=INK):
    """A drawn line on a sheet in the plane at `x`, from (y, z) point `a` to `b`."""
    _bar(r, (x, a[0], a[1]), (x, b[0], b[1]), thick, rgb)


def anatomy_chart(r, seed):
    """One of Herran's anatomical charts, pinned in an oak frame on the wall at local -X, its middle
    1.7 m up: a man flayed to the muscle with a second pair of arms drawn in dotted where they are to
    go, a great hand with its bones laid out and a sixth finger stitched on, or a bear's foreleg and a
    man's arm with the line of the cut between them. Labels in a crabbed hand down its sides, a nail at
    each top corner, a curled corner and a red wax seal."""
    cy = 1.7
    sheet = WALL + 0.05
    x = sheet + 0.012  # the drawing's face
    r.part("cube", WALL + 0.02, cy, 0, 0.04, 1.36, 1.0, OAK_DARK)  # the frame's back
    for side in (-1, 1):
        r.part("cube", WALL + 0.05, cy + side * 0.64, 0, 0.06, 0.08, 1.0, OAK_DARK)
        r.part("cube", WALL + 0.05, cy, side * 0.46, 0.06, 1.36, 0.08, OAK_DARK)
    r.part("cube", sheet, cy, 0, 0.01, 1.18, 0.82, PARCHMENT)
    for side in (-1, 1):
        r.part("cube", x, cy + 0.55, side * 0.36, 0.01, 0.03, 0.03, WROUGHT)  # the nails
    r.part("cube", x, cy - 0.55, 0.37, 0.01, 0.1, 0.1, _dim(PARCHMENT, 0.8), rx=math.pi / 4)  # the curl
    r.part("cyl", x, cy - 0.5, -0.3, 0.07, 0.01, 0.07, WAX_RED, rz=math.pi / 2)  # the seal
    for k in range(6):  # labels down both sides, each with its leader
        y = cy + 0.4 - k * 0.15
        side = -1 if k % 2 else 1
        r.part("cube", x, y, side * 0.3, 0.01, 0.018, 0.12, INK)
        _ink(r, x, (y, side * 0.23), (y - 0.04, side * 0.12), 0.006)
    r.part("cube", x, cy + 0.5, 0, 0.01, 0.025, 0.4, INK)  # its title
    subject = seed % 3
    if subject == 0:  # the flayed man, with the arms he is to be given dotted in
        r.part("cube", x, cy + 0.36, 0, 0.01, 0.1, 0.08, SEPIA)  # the head
        r.part("cube", x, cy + 0.12, 0, 0.01, 0.32, 0.16, SEPIA)  # the trunk
        for k in range(4):
            r.part("cube", x + 0.001, cy + 0.2 - k * 0.05, 0, 0.01, 0.01, 0.14, INK)  # the ribs
        for side in (-1, 1):
            _ink(r, x, (cy + 0.25, side * 0.08), (cy + 0.02, side * 0.18), 0.035, SEPIA)  # the arms
            _ink(r, x, (cy + 0.02, side * 0.18), (cy - 0.12, side * 0.2), 0.03, SEPIA)
            _ink(r, x, (cy - 0.05, side * 0.05), (cy - 0.42, side * 0.08), 0.04, SEPIA)  # the legs
            for d in range(4):  # the second arms, dotted in
                y0 = cy + 0.16 - d * 0.06
                r.part("cube", x, y0, side * (0.1 + d * 0.035), 0.01, 0.025, 0.02, BLOOD)
    elif subject == 1:  # the hand and its bones, a sixth finger sewn on
        r.part("cube", x, cy - 0.05, 0, 0.01, 0.3, 0.3, _dim(PARCHMENT, 0.9))  # the palm's outline
        for f in range(5):
            z = -0.12 + f * 0.06
            for j in range(3):
                r.part("cube", x + 0.001, cy + 0.14 + j * 0.08, z, 0.01, 0.06, 0.03, (226, 214, 190))
                r.part("cube", x + 0.002, cy + 0.11 + j * 0.08, z, 0.01, 0.008, 0.03, INK)
            _ink(r, x, (cy + 0.08, z), (cy - 0.16, z * 0.6), 0.012)  # its long bone
        with r.at(x, cy - 0.02, 0.17, rx=-0.7):  # the sixth finger
            r.part("cube", 0.001, 0.12, 0, 0.01, 0.2, 0.03, GRAFT_SKIN)
            for k in range(4):
                r.part("cube", 0.002, 0.03, -0.03 + k * 0.02, 0.01, 0.03, 0.006, BLOOD)  # its stitches
    else:  # the beast's foreleg and the man's arm, the cut between them
        _ink(r, x, (cy + 0.35, -0.18), (cy - 0.3, -0.12), 0.08, (92, 70, 58))  # the foreleg
        for k in range(4):
            r.part("cone", x, cy - 0.34, -0.17 + k * 0.03, 0.02, 0.06, 0.02, INK, rx=math.pi)  # its claws
        _ink(r, x, (cy + 0.35, 0.16), (cy - 0.3, 0.12), 0.05, SEPIA)  # the arm
        for k in range(6):  # the dotted line of the cut, and the arrow over to the shoulder
            r.part("cube", x, cy + 0.1, -0.24 + k * 0.08, 0.01, 0.012, 0.04, BLOOD)
        _ink(r, x, (cy + 0.25, -0.1), (cy + 0.25, 0.08), 0.01)
        r.part("pyramid", x, cy + 0.25, 0.1, 0.01, 0.05, 0.05, INK, rx=-math.pi / 2)


JAR_FLUIDS = ((190, 160, 80), (130, 170, 96), (156, 150, 118), (176, 120, 96))


def _jar(r, x, y, z, rng, height):
    """A specimen jar standing on a shelf at (x, y, z): glass, its spirits tinted, something pickled in
    it, a cork or a waxed cloth over its mouth and a tag tied round its neck."""
    wide = height * 0.6
    fluid = JAR_FLUIDS[rng.randrange(len(JAR_FLUIDS))]
    glow = rng.random() < 0.12
    r.part("cyl", x, y + height / 2, z, wide * 0.92, height * 0.86, wide * 0.92, fluid if not glow else (120, 220, 130),
           glow=glow)  # fmt: skip
    r.part("cyl", x, y + height / 2, z, wide, height, wide, PANE)
    thing = rng.randrange(5)
    c = y + height * 0.45
    if thing == 0:  # a hand
        r.part("cube", x, c, z, wide * 0.25, height * 0.3, wide * 0.4, PALLID)
        for f in range(3):
            r.part("cube", x, c + height * 0.22, z + (f - 1) * wide * 0.13, wide * 0.1, height * 0.16, wide * 0.08,
                   PALLID)  # fmt: skip
    elif thing == 1:  # an eye
        r.part("sphere", x, c, z, wide * 0.4, wide * 0.4, wide * 0.4, (226, 220, 206))
        r.part("sphere", x + wide * 0.18, c, z, wide * 0.12, wide * 0.16, wide * 0.16, (60, 90, 70))
        r.part("cube", x - wide * 0.15, c - wide * 0.25, z, wide * 0.04, wide * 0.3, wide * 0.04, BLOOD)
    elif thing == 2:  # a heart
        r.part("sphere", x, c, z, wide * 0.5, height * 0.4, wide * 0.45, (120, 40, 40))
        r.part("cyl", x, c + height * 0.25, z, wide * 0.12, height * 0.16, wide * 0.12, (140, 60, 60))
    elif thing == 3:  # something curled up, unborn, with too many limbs
        r.part("sphere", x, c, z, wide * 0.5, height * 0.42, wide * 0.4, GRAFT_SKIN)
        r.part("sphere", x, c + height * 0.22, z, wide * 0.32, wide * 0.32, wide * 0.32, GRAFT_SKIN)
        for k in range(4):
            a = k * math.pi / 2 + 0.4
            _bar(r, (x, c, z), (x + math.cos(a) * wide * 0.4, c - height * 0.1, z + math.sin(a) * wide * 0.4),
                 wide * 0.08, GRAFT_SKIN)  # fmt: skip
    else:  # a tongue, or a length of gut coiled
        r.part("cube", x, c, z, wide * 0.3, height * 0.5, wide * 0.25, (168, 96, 96), rz=0.3)
    if rng.random() < 0.5:
        r.part("cyl", x, y + height + 0.03, z, wide * 0.5, 0.07, wide * 0.5, (150, 116, 80))  # a cork
    else:
        r.part(
            "cyl", x, y + height + 0.01, z, wide * 1.05, 0.04, wide * 1.05, (200, 186, 150)
        )  # a waxed cloth
        r.part("cyl", x, y + height - 0.03, z, wide * 1.04, 0.015, wide * 1.04, STITCH)  # its tie
    r.part("cube", x + wide * 0.52, y + height * 0.8, z, 0.01, 0.04, 0.05, PARCHMENT)  # the tag


def specimen_jars(r, seed):
    """Shelves of specimens against the wall at local -X: an open case of dark oak four shelves high,
    each crowded with jars of every size, a hand or an eye or a heart pickled in each, one of them
    glowing a sick green; a ledger lying on the top shelf."""
    rng = random.Random(seed)
    depth, wide, tall = 0.36, 1.6, 2.1
    x = WALL + depth / 2
    r.part(
        "cube", WALL + 0.02, tall / 2, 0, 0.03, tall, wide, _dim(OAK_DARK, 0.8), tex="wood_plank"
    )  # the back
    for side in (-1, 1):
        r.part("cube", x, tall / 2, side * wide / 2, depth, tall, 0.05, OAK_DARK, tex="wood_plank")
    r.part("cube", x, tall + 0.04, 0, depth + 0.06, 0.08, wide + 0.12, OAK_DARK)  # the cornice
    for k in range(4):  # the shelves and what is on them
        y = 0.08 + k * 0.52
        r.part("cube", x, y, 0, depth, 0.04, wide - 0.05, OAK_DARK, tex="wood_plank")
        z = -wide / 2 + 0.12
        while z < wide / 2 - 0.12:
            height = 0.18 + rng.random() * 0.24 if k < 3 else 0.14 + rng.random() * 0.12
            if k == 3 and z > 0.2:
                break
            _jar(r, x + 0.02, y + 0.02, z + height * 0.3, rng, height)
            z += height * 0.6 + 0.08
    r.part("cube", x, 1.66, 0.52, 0.24, 0.06, 0.32, (74, 34, 28))  # the ledger, on the top shelf


def surgical_trolley(r, seed):
    """A surgeon's trolley on iron castors, its rails running along Z: a tray with a raised rim laid
    with his instruments (a bone saw, scalpels, forceps, hooks, a curved needle and a spool of black
    thread, an open roll of tools in leather, a basin of blood), and on the shelf under it a pail,
    folded linen, stained, and a jar with an eye in it; a push-bar at one end."""
    w, d = 0.6, 1.0
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * (w / 2 - 0.03), 0.5, dz * (d / 2 - 0.03), 0.04, 0.84, 0.04, WROUGHT)  # the legs
        r.part(
            "cyl", dx * (w / 2 - 0.03), 0.05, dz * (d / 2 - 0.03), 0.09, 0.03, 0.09, SOOT, rx=math.pi / 2
        )  # castor
    r.part("cube", 0, 0.9, 0, w, 0.03, d, (120, 120, 126))  # the tray
    for side in (-1, 1):  # its rim
        r.part("cube", side * w / 2, 0.94, 0, 0.02, 0.06, d, WROUGHT)
        r.part("cube", 0, 0.94, side * d / 2, w, 0.06, 0.02, WROUGHT)
    r.part("cube", 0, 0.3, 0, w - 0.04, 0.03, d - 0.04, WROUGHT)  # the shelf
    _bar(r, (-w / 2, 1.02, d / 2), (w / 2, 1.02, d / 2), 0.03, WROUGHT)  # the push-bar
    for side in (-1, 1):
        _bar(r, (side * (w / 2 - 0.03), 0.9, d / 2 - 0.03), (side * w / 2, 1.02, d / 2), 0.025, WROUGHT)
    with r.at(0, 0.925, 0):  # the instruments on the tray
        r.part("cube", -0.12, 0, -0.3, 0.12, 0.01, 0.32, (196, 200, 206))  # the bone saw's blade
        r.part("cube", -0.12, 0.02, -0.12, 0.06, 0.04, 0.1, OAK_DARK)  # its grip
        for k in range(3):
            r.part("cube", 0.06 + k * 0.04, 0, -0.32, 0.01, 0.01, 0.16, (210, 214, 220))  # scalpels
            r.part("cube", 0.06 + k * 0.04, 0.005, -0.21, 0.015, 0.015, 0.07, OAK_DARK)
        _bar(r, (0.2, 0.01, -0.36), (0.18, 0.01, -0.18), 0.012, (180, 184, 190))  # forceps
        _bar(r, (0.2, 0.01, -0.36), (0.22, 0.01, -0.18), 0.012, (180, 184, 190))
        r.part("cyl", 0.16, 0.02, 0.0, 0.08, 0.04, 0.08, (60, 40, 30))  # the spool
        r.part("cyl", 0.16, 0.02, 0.0, 0.09, 0.03, 0.09, STITCH)  # its black thread
        _bar(r, (0.16, 0.04, 0.0), (0.05, 0.01, 0.08), 0.004, STITCH)
        r.part("cube", 0.05, 0.01, 0.09, 0.005, 0.005, 0.06, (210, 214, 220), ry=0.6)  # the curved needle
        r.part("cube", -0.12, 0, 0.18, 0.3, 0.01, 0.28, (74, 34, 28))  # the open roll
        for k in range(4):
            r.part("cube", -0.22 + k * 0.06, 0.01, 0.18, 0.01, 0.01, 0.22, (170, 174, 180))
        r.part("cyl", 0.14, 0.03, 0.32, 0.18, 0.05, 0.12, (150, 150, 156))  # the basin
        r.part("cyl", 0.14, 0.05, 0.32, 0.14, 0.01, 0.09, BLOOD)
        for k in range(2):
            r.part("cube", -0.2 + k * 0.08, 0.01, 0.4, 0.02, 0.01, 0.1, WROUGHT, ry=0.3)  # hooks
    r.part("cyl", 0.12, 0.42, -0.25, 0.22, 0.22, 0.22, WROUGHT)  # the pail
    r.part("cyl", 0.12, 0.52, -0.25, 0.19, 0.01, 0.19, BLOOD)
    r.part("cube", -0.12, 0.36, 0.1, 0.28, 0.08, 0.3, (200, 190, 170))  # the linen
    r.part("cube", -0.1, 0.405, 0.12, 0.12, 0.01, 0.1, (140, 60, 52))  # stained
    r.part("cyl", 0.14, 0.42, 0.3, 0.12, 0.2, 0.12, PANE)  # the jar
    r.part("sphere", 0.14, 0.42, 0.3, 0.07, 0.07, 0.07, (226, 220, 206))
    r.part("cube", -w / 2 - 0.005, 0.7, -0.1 + (seed % 3) * 0.05, 0.01, 0.3, 0.2, (190, 180, 160))  # a cloth
    r.part("cube", -w / 2 - 0.006, 0.6, -0.1, 0.01, 0.08, 0.1, (140, 60, 52))


def _seam(r, a, b):
    """A line of black stitches across a graft from `a` to `b`: a dark thread and the stitches over it."""
    _bar(r, a, b, 0.012, STITCH)
    for k in range(4):
        m = tuple(a[i] + (b[i] - a[i]) * (k + 0.5) / 4 for i in range(3))
        r.part("cube", m[0], m[1], m[2], 0.03, 0.05, 0.012, STITCH)


def _bracket(r, height=3.6, out=0.65):
    """An iron gibbet bracket on the wall at local -X: a plate, an arm out `out` metres at `height`, a
    strut under it, and a ring at its end. Returns the ring's x."""
    r.part("cube", WALL + 0.03, height - 0.3, 0, 0.06, 0.9, 0.18, WROUGHT)
    _bar(r, (WALL + 0.04, height, 0), (WALL + out, height, 0), 0.07, WROUGHT)
    _bar(r, (WALL + 0.04, height - 0.6, 0), (WALL + out * 0.7, height, 0), 0.05, WROUGHT)
    r.part("cube", WALL + out, height - 0.07, 0, 0.04, 0.12, 0.08, WROUGHT)
    return WALL + out


def _chain(r, x, y0, y1, z=0.0):
    """Links of chain hanging straight down from y0 to y1 at (x, z)."""
    n = max(1, int((y0 - y1) / 0.14))
    for i in range(n):
        r.part("cube", x, y0 - 0.07 - i * 0.14, z, 0.025, 0.16, 0.07, WROUGHT, ry=0 if i % 2 else math.pi / 2)


def hung_cadaver(r, seed, style="hook"):
    """One of Herran's failures hung up from an iron gibbet bracket on the wall at local -X: on a `hook`
    a stitched cadaver, pallid, hung by a hook through its back, head lolling, a third arm of another
    man's skin sewn on at its side and black seams across its chest and limbs; in a `cage` (a gibbet)
    what is left of one, slumped among its bars, a hand out through them."""
    end = _bracket(r)
    if style == "cage":
        _chain(r, end, 3.5, 3.05)
        with r.at(end, 1.4, 0):
            for k in range(8):  # the bars
                a = k * math.tau / 8
                r.part("cube", math.cos(a) * 0.32, 0.8, math.sin(a) * 0.32, 0.035, 1.6, 0.035, WROUGHT)
            for y in (0.0, 0.8, 1.6):
                r.part("cyl", 0, y, 0, 0.7, 0.04, 0.7, WROUGHT)  # its hoops
            r.part("cone", 0, 1.72, 0, 0.7, 0.24, 0.7, WROUGHT)
            r.part("cyl", 0, 0.01, 0, 0.62, 0.02, 0.62, (50, 44, 40))  # its floor
            with r.at(0.02, 0.62, 0, rz=0.5):  # the skull, hanging forward
                skull(r, (196, 186, 162), jaw=0.3)
            with r.at(-0.06, 0.4, 0):
                ribcage(r, (196, 186, 162), ribs=3, width=0.26)
            _bar(r, (0.0, 0.3, 0.12), (0.45, 0.5, 0.2), 0.04, (190, 176, 150))  # an arm out through the bars
            r.part("cube", 0.48, 0.42, 0.22, 0.04, 0.12, 0.08, (190, 176, 150))
            for k in range(3):
                _bar(r, (-0.12, 0.05, -0.15 + k * 0.12), (0.12, 0.05, -0.1 + k * 0.1), 0.035, (190, 176, 150))
        return
    _chain(r, end, 3.5, 2.95)
    with r.at(end, 0, 0):
        r.part("cube", 0, 2.88, 0, 0.04, 0.14, 0.04, WROUGHT)  # the hook
        r.part("cube", 0.06, 2.8, 0, 0.1, 0.04, 0.04, WROUGHT)
        skin = PALLID
        r.part("cube", 0.02, 2.4, 0, 0.24, 0.66, 0.4, skin, rz=0.08)  # the trunk, hung by the back
        r.part("cube", 0.05, 2.0, 0, 0.22, 0.2, 0.36, (70, 60, 56))  # a rag round its loins
        with r.at(0.12, 2.82, 0, rz=-0.6):  # its head, lolling forward
            r.part("cube", 0, 0.1, 0, 0.2, 0.24, 0.18, skin)
            r.part("cube", 0.1, 0.08, 0, 0.02, 0.02, 0.14, STITCH)  # its eyes sewn shut
        for side in (-1, 1):  # the arms, hanging, and the legs
            _bar(r, (0.0, 2.66, side * 0.22), (0.06, 2.12, side * 0.26), 0.09, skin)
            _bar(r, (0.06, 2.12, side * 0.26), (0.1, 1.68, side * 0.24), 0.08, skin)
            r.part("cube", 0.1, 1.6, side * 0.24, 0.06, 0.14, 0.08, skin)
            _bar(r, (0.02, 1.96, side * 0.1), (0.06, 1.46, side * 0.11), 0.12, skin)
            _bar(r, (0.06, 1.46, side * 0.11), (0.04, 0.98, side * 0.1), 0.1, skin)
            r.part("cube", 0.08, 0.92, side * 0.1, 0.16, 0.06, 0.08, skin)
        _bar(r, (0.1, 2.5, 0.22), (0.2, 2.0, 0.34), 0.08, GRAFT_SKIN)  # the third arm, sewn on
        _bar(r, (0.2, 2.0, 0.34), (0.24, 1.6, 0.36), 0.07, GRAFT_SKIN)
        r.part("cube", 0.25, 1.52, 0.36, 0.06, 0.12, 0.07, GRAFT_SKIN)
        _seam(r, (0.15, 2.56, 0.2), (0.15, 2.4, 0.24))  # where it is sewn on
        _seam(r, (0.15, 2.66, -0.16), (0.15, 2.24, 0.16))  # the seams down its chest
        _seam(r, (0.1, 1.7, -0.16), (0.1, 1.72, -0.06))  # and round a thigh
        r.part("cube", 0.15, 2.3, -0.05, 0.01, 0.2, 0.06, BLOOD)


def wall_chains(r, seed):
    """Chains on the wall at local -X: two iron rings leaded into the stone at shoulder height with a
    swag of chain sagging between them, a manacle hanging from each on a short length, one still closed
    round a severed hand; old blood run down the stone under them."""
    for side in (-1, 1):
        z = side * 0.55
        r.part("cube", WALL + 0.02, 2.3, z, 0.04, 0.14, 0.14, LEAD)  # the ring's lead plug
        r.part("cyl", WALL + 0.06, 2.22, z, 0.12, 0.025, 0.12, WROUGHT, rz=math.pi / 2)  # the ring
        _chain(r, WALL + 0.07, 2.16, 1.6, z)
        with r.at(WALL + 0.08, 1.52, z):  # the manacle
            r.part("cyl", 0, 0, 0, 0.16, 0.05, 0.16, WROUGHT, rx=math.pi / 2)
            if side == 1:  # a hand still in it
                r.part("cube", 0, -0.06, 0, 0.06, 0.14, 0.1, (176, 156, 140))
                for f in range(3):
                    r.part("cube", 0, -0.18, (f - 1) * 0.03, 0.03, 0.1, 0.02, (170, 150, 134))
                r.part("cube", 0, 0.06, 0, 0.07, 0.03, 0.09, BLOOD)  # the stump
    for k in range(9):  # the swag between the rings
        z = -0.5 + k * 0.125
        y = 2.16 - 0.42 * (1 - (z / 0.55) ** 2)
        r.part(
            "cube",
            WALL + 0.06,
            y,
            z,
            0.025,
            0.07,
            0.15,
            WROUGHT,
            rx=(z / 0.55) * 0.6,
            ry=0 if k % 2 else math.pi / 2,
        )
    r.part("cube", WALL + 0.004, 1.1, 0.55, 0.01, 0.8, 0.1, _dim(BLOOD, 0.6))  # the blood run down
    r.part("cube", WALL + 0.004, 0.7, 0.5 + (seed % 3) * 0.02, 0.01, 0.4, 0.05, _dim(BLOOD, 0.5))


# --- what the storm and the years have broken ------------------------------------------------------


def broken_statue(r, seed):
    """A statue of the household broken off its plinth, facing +X: the stepped plinth with the robed
    legs snapped off at the knee, the hooded trunk fallen on the flags before it, its head rolled off
    to the side, the long sword in two pieces and the shield fallen face down against the plinth, the
    stone gone green with lichen where the rain runs."""
    stone, dark = CASTLE, CASTLE_DARK  # the gate statues' own stone
    with r.at(-0.4, 0, 0):
        r.part("cube", 0, 0.2, 0, 1.1, 0.4, 1.1, dark, tex="castle_stone")  # the plinth
        r.part("cube", 0, 0.5, 0, 0.86, 0.2, 0.86, stone, tex="castle_stone")
        r.part("cube", 0, 0.9, 0, 0.42, 0.6, 0.6, stone)  # the legs' stumps
        for k in range(3):  # the break, jagged
            r.part("wedge", 0, 1.26, -0.2 + k * 0.2, 0.42, 0.14 + (k % 2) * 0.1, 0.2, stone)
        r.part("cube", 0.22, 0.85, 0.1, 0.02, 0.5, 0.2, STATUE_MOSS)  # lichen down it
        with r.at(0.6, 0.35, -0.42, rx=-0.5):  # the shield, fallen against it
            r.part("cube", 0, 0, 0, 0.1, 1.2, 0.5, dark)
    with r.at(0.2, 0.21, 0.15, rz=-math.pi / 2 + 0.1, ry=0.4):  # the trunk, lying
        r.part("cube", 0, 0.3, 0, 0.42, 0.62, 0.62, stone)
        for side in (-1, 1):
            r.part("sphere", 0, 0.56, side * 0.32, 0.2, 0.14, 0.2, stone)  # its pauldrons
        r.part("cube", 0.15, 0.3, 0, 0.02, 0.4, 0.3, STATUE_MOSS)
    with r.at(0.55, 0.15, -0.55, ry=1.1):  # the hooded head, rolled away
        r.part("cube", 0, 0, 0, 0.3, 0.3, 0.3, stone)
        r.part("pyramid", -0.04, 0.2, 0, 0.3, 0.16, 0.28, stone, rz=0.3)
        r.part("cube", 0.15, 0, 0, 0.02, 0.16, 0.16, SOOT)
    r.part("cube", 0.1, 0.04, 0.6, 0.9, 0.06, 0.12, _dim(stone, 1.1), ry=0.3 + (seed % 3) * 0.1)  # the blade
    r.part("cube", -0.3, 0.04, 0.72, 0.5, 0.06, 0.12, _dim(stone, 1.1), ry=-0.5)  # its point
    r.part("cube", 0.48, 0.06, 0.48, 0.06, 0.08, 0.4, dark, ry=0.3)  # its cross
    rng = random.Random(seed)
    for _ in range(5):  # chips of stone round about
        s = 0.1 + rng.random() * 0.14
        r.part("cube", (rng.random() - 0.3) * 1.4, s / 2, (rng.random() - 0.5) * 1.6, s, s * 0.8, s,
               stone if rng.random() < 0.5 else dark, ry=rng.random() * 3)  # fmt: skip


def breach_rubble(r, seed):
    """What the storm brought down through the anatomy theatre's broken dome, lying on the flags and
    low enough to step over: blocks of ashlar, slates split from the roofs, a length of the dome's iron
    rib bent where it fell, shards of its glass, and the rain pooled in the hollows."""
    rng = random.Random(seed)
    r.part("cube", 0.15, 0.006, -0.1, 1.2, 0.012, 0.9, WET, ry=rng.random())  # the pool
    r.part("cube", 0.2, 0.014, -0.05, 0.6, 0.004, 0.3, _dim(STORM_LIT, 0.5), ry=rng.random())  # its sheen
    for _ in range(9):  # ashlar, broken
        s = 0.2 + rng.random() * 0.24
        x, z = (rng.random() - 0.5) * 1.6, (rng.random() - 0.5) * 1.6
        r.part("cube", x, s * 0.35, z, s * 1.4, s * 0.7, s, DRESSED if rng.random() < 0.6 else DRESSED_DARK,
               ry=rng.random() * 3, rz=(rng.random() - 0.5) * 0.4, tex="castle_stone")  # fmt: skip
    for _ in range(6):  # slates
        x, z = (rng.random() - 0.5) * 1.7, (rng.random() - 0.5) * 1.7
        r.part("cube", x, 0.05, z, 0.34, 0.025, 0.22, _dim(SLATE, 1.5), ry=rng.random() * 3, rx=(rng.random() - 0.5) * 0.5,
               tex="castle_slate")  # fmt: skip
    a = (-0.8, 0.05, 0.4)  # the bent rib
    b = (-0.1, 0.12, 0.6)
    c = (0.5, 0.3, 0.2)
    _bar(r, a, b, 0.09, WROUGHT)
    _bar(r, b, c, 0.09, WROUGHT)
    r.part("cube", c[0], c[1] - 0.12, c[2], 0.12, 0.24, 0.12, DRESSED_DARK)  # propped on a block
    for _ in range(6):  # shards of the dome's glass
        x, z = (rng.random() - 0.5) * 1.5, (rng.random() - 0.5) * 1.5
        r.part("cube", x, 0.02, z, 0.12, 0.01, 0.08, PANE, ry=rng.random() * 3)
