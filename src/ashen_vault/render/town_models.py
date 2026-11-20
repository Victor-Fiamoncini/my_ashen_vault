"""Harrowmere's models: tiled roofs, the Silent Bell, the cathedral (its towers, spire, buttresses and
stained glass), pews, the dressing of its stone and half-timbered houses (mullioned windows of leaded glass behind
board shutters, jettied galleries, arched doorways and the doors that swing in them, corner turrets), the round towers of its wall, the shops'
hanging signs, the realm's crest on poles and plaques, the furniture and the street dressing of a harbour
town (beds, cupboards, shelves, hearths, a fountain, benches, carts and cargo, wattle fences, lantern posts, a
moored boat, the smith's bellows and grindstone). Pure part lists drawn through a Rig, like `models`."""

import itertools
import math

from ashen_vault.render.models import (
    IRON,
    REALM_VIOLET,
    SWORDS,
    WHITE,
    _arch_top,
    _bar,
    _dim,
    _flame,
    _pointed_arch,
    _weapon,
    _wheel,
    garment,
    gauntlet,
    katana,
    realm_crest,
    shield,
)
from ashen_vault.util import rround
from ashen_vault.world.tile_map import TileMap

T = TileMap.TILE
WOOD = (104, 74, 48)
DARK_WOOD = (70, 50, 34)
BRONZE = (120, 96, 54)
BRONZE_DARK = (74, 58, 34)
PALE_STONE = (150, 146, 136)
CLOTH = ((150, 50, 44), (60, 90, 120), (140, 120, 60), (70, 110, 70))
GLASS = ((120, 150, 200), (190, 150, 70), (150, 60, 60), (90, 140, 110))
# Stained glass: ruby, cobalt, gold, emerald and amethyst, leaded in dark came.
STAINED = ((178, 34, 44), (44, 70, 190), (226, 172, 48), (44, 140, 78), (120, 56, 150))
LEAD = (28, 26, 30)
GILT = (214, 176, 84)
SANDSTONE = (186, 160, 120)
REALM_CLOTH = REALM_VIOLET
HAY = (200, 168, 88)
SACK = (160, 136, 98)


CLAY_RIDGE = (150, 76, 52)  # the half-round ridge and hip tiles of a terracotta roof
PLASTER_WHITE = (240, 234, 222)  # lime plaster, under the plaster texture's own tint


def _ridge_rgb(tex):
    """The ridge's colour: capping tiles on a terracotta roof, an oak beam on slate."""
    return CLAY_RIDGE if tex == "clay_tile" else DARK_WOOD


def roof(r, w, d, ridge="x", top=4.2, pitch=1.8, tex="roof", wall_tex="timber", eave=0.35, hip=False):
    """A roof over a `w` x `d` tile building whose NW corner tile holds the prop, its eaves overhanging
    the walls by `eave` and a ridge along `ridge`. Gabled, it is a pitched slab with the gable ends
    filled in the wall's texture and barge boards up their slopes; `hip`ped, it slopes on all four
    sides at one pitch, its ridge shorter by the building's width and capped hips running down to
    each corner."""
    cx, cz = (w - 1) * T / 2, (d - 1) * T / 2
    span_x, span_z = w * T, d * T
    if ridge == "x":  # the wedge's ridge runs along its Z: turn it so it runs along X
        across, along, ry = span_z, span_x, math.pi / 2
    else:
        across, along, ry = span_x, span_z, 0.0
    cap = _ridge_rgb(tex)
    with r.at(cx, top, cz, ry=ry):
        if hip:
            _hip_roof(r, across + eave * 2, along + eave * 2, pitch, tex, cap)
            r.part("cube", 0, 0.02, 0, across + eave * 2, 0.08, along + eave * 2 + 0.02, _dim(DARK_WOOD, 0.8))
            return
        r.part("wedge", 0, pitch / 2, 0, across + eave * 2, pitch, along + eave * 2, WHITE, tex=tex)
        # The gable walls just inside the overhang, and a dark band where the roof meets them.
        r.part(
            "wedge", 0, (pitch - 0.1) / 2, 0, across - 0.05, pitch - 0.1, along + 0.04, WHITE, tex=wall_tex
        )
        r.part("cube", 0, 0.02, 0, across + eave * 2, 0.08, along + eave * 2 + 0.02, _dim(DARK_WOOD, 0.8))
        r.part("cube", 0, pitch + 0.04, 0, 0.18, 0.14, along + eave * 2 + 0.1, cap)  # ridge beam
        for end in (-1, 1):  # barge boards along each gable's slopes
            for side in (-1, 1):
                slope = math.atan2(pitch, across / 2 + eave)
                with r.at(side * (across / 4 + eave / 2), pitch / 2, end * (along / 2 + eave + 0.02)):
                    r.part("cube", 0, 0, 0, across / 2 + eave + 0.2, 0.1, 0.06, DARK_WOOD, rz=-side * slope)


def hip_ridge(across, along):
    """The length of a hipped roof's ridge over eaves `across` x `along` (the ridge running along
    `along`): all four slopes rise at one pitch, so each hip end takes half the width off each end."""
    return max(along - across, 0.0)


def _hip_roof(r, across, along, pitch, tex, cap):
    """A hipped roof's slopes over eaves `across` x `along`, its ridge along Z: a pyramid at each end
    whose long faces carry on the wedge's slopes between them, the wedge cut into lengths about the
    pyramids' own so the tiles keep one size all over, and capping along the ridge and down the hips."""
    ridge = hip_ridge(across, along)
    run = min(across, along) / 2  # how far each slope reaches in from the eaves
    pieces = max(1, rround(ridge / (run * 2))) if ridge > 0.01 else 0
    for i in range(pieces):
        z = -ridge / 2 + ridge * (i + 0.5) / pieces
        r.part("wedge", 0, pitch / 2, z, across, pitch, ridge / pieces + 0.01, WHITE, tex=tex)
    for end in (-1, 1):
        r.part("pyramid", 0, pitch / 2, end * ridge / 2, across, pitch, run * 2, WHITE, tex=tex)
        for side in (-1, 1):  # the hip, capped down to its corner
            _bar(r, (0, pitch + 0.04, end * ridge / 2), (side * across / 2, 0.04, end * along / 2), 0.14, cap)
    if ridge > 0.01:
        r.part("cube", 0, pitch + 0.04, 0, 0.18, 0.14, ridge + 0.1, cap)  # the ridge's capping


def silent_bell(r, t):
    """The Silent Bell on its plinth (a 3x3-tile low block whose centre holds the prop): four stone
    posts and a great oak headstock carrying a bronze bell taller than a man. A dark crack runs from
    its lip up toward the crown, the clapper hangs dead still, and a few candles gutter at its foot."""
    base = 0.8  # the plinth's top
    stone = PALE_STONE
    r.part("cube", 0, base + 0.15, 0, 5.4, 0.3, 5.4, stone, tex="flagstone")  # a top step
    for sx in (-1, 1):
        for sz in (-1, 1):  # four posts with capitals
            r.part("cube", sx * 2.0, base + 3.0, sz * 1.6, 0.6, 5.7, 0.6, stone, tex="rough_stone")
            r.part("cube", sx * 2.0, base + 5.95, sz * 1.6, 0.8, 0.3, 0.8, _dim(stone, 1.1))
            r.part("cube", sx * 2.0, base + 0.5, sz * 1.6, 0.8, 0.4, 0.8, _dim(stone, 0.9))  # foot
    for sz in (-1, 1):  # beams joining the posts
        r.part("cube", 0, base + 6.2, sz * 1.6, 4.8, 0.4, 0.4, DARK_WOOD, tex="wood_plank")
    r.part("cube", 0, base + 6.2, 0, 0.6, 0.5, 3.8, WOOD, tex="wood_plank")  # the headstock
    for sx in (-1, 1):
        r.part("cube", sx * 2.0, base + 6.55, 0, 0.5, 0.3, 3.8, DARK_WOOD, tex="wood_plank")
    r.part(
        "wedge", 0, base + 7.1, 0, 4.8, 1.0, 4.2, WHITE, tex="violet_slate", ry=math.pi / 2
    )  # a small roof
    # The bell: crown, waist flaring to the sound bow and lip, a band of raised lettering.
    with r.at(0, base + 2.4, 0):
        r.part("cube", 0, 3.4, 0, 0.3, 0.6, 0.3, IRON)  # the hanger
        r.part("sphere", 0, 3.0, 0, 1.2, 0.6, 1.2, BRONZE)  # crown
        r.part("cyl", 0, 2.2, 0, 1.5, 1.6, 1.5, BRONZE)  # waist
        r.part("cyl", 0, 1.05, 0, 2.0, 0.9, 2.0, BRONZE)  # sound bow
        r.part("cyl", 0, 0.55, 0, 2.5, 0.25, 2.5, _dim(BRONZE, 0.9))  # lip
        r.part("cyl", 0, 0.45, 0, 2.3, 0.06, 2.3, (20, 18, 16))  # the dark mouth
        r.part("cyl", 0, 2.75, 0, 1.36, 0.12, 1.36, _dim(BRONZE, 1.2))  # a raised band
        for i in range(8):  # its lettering, worn smooth
            a = i * math.pi / 4
            r.part("cube", math.cos(a) * 0.7, 2.75, math.sin(a) * 0.7, 0.06, 0.08, 0.14, BRONZE_DARK, ry=-a)
        # The crack: a jagged seam up the face toward you (+X), wide at the lip.
        for i, (y, z, h) in enumerate(
            ((0.65, 0.0, 0.35), (1.0, 0.08, 0.4), (1.4, 0.02, 0.4), (1.8, 0.1, 0.35))
        ):
            x = 1.25 - 0.13 * i if i else 1.25
            r.part("cube", x, y, z, 0.05, h, 0.05 - 0.008 * i, (16, 12, 10), rz=0.12 * (i % 2 * 2 - 1))
        r.part("cube", 0, 0.9, 0, 0.12, 2.0, 0.12, IRON)  # the clapper's shaft, hanging still
        r.part("sphere", 0, -0.05, 0, 0.36, 0.42, 0.36, IRON)  # its ball
    for i in range(5):  # candles left at its foot
        a = 0.4 + i * 0.35
        x, z = 2.3 + 0.2 * (i % 2), -1.0 + i * 0.5
        r.part("cyl", x, base + 0.42, z, 0.08, 0.24 + 0.05 * (i % 3), 0.08, (220, 210, 180))
        _flame(r, x, base + 0.6 + 0.025 * (i % 3), z, 0.05, t + a)


def cathedral_spire(r, height=18.0):
    """The cathedral's bell-less spire: a pale square tower with tall lancet windows, pinnacles at the
    corners, and a steep slate needle."""
    w = 3.0
    r.part("cube", 0, height / 2, 0, w, height, w, PALE_STONE, tex="rough_stone")
    r.part("cube", 0, 1.0, 0, w * 1.15, 2.0, w * 1.15, _dim(PALE_STONE, 0.9), tex="rough_stone")
    for i in range(3):  # string courses
        r.part("cube", 0, height * (0.3 + 0.25 * i), 0, w * 1.08, 0.2, w * 1.08, _dim(PALE_STONE, 1.1))
    for a in range(4):  # lancets on each face, glowing faintly
        with r.at(0, 0, 0, ry=a * math.pi / 2):
            r.part("cube", w / 2 + 0.01, height * 0.72, 0, 0.04, 2.6, 0.5, (30, 30, 40))
            r.part("cube", w / 2 + 0.02, height * 0.72, 0, 0.02, 2.3, 0.3, GLASS[0], glow=True)
            r.part(
                "wedge", w / 2 + 0.02, height * 0.72 + 1.45, 0, 0.04, 0.4, 0.5, (30, 30, 40), ry=math.pi / 2
            )
    for sx in (-1, 1):
        for sz in (-1, 1):
            r.part("cone", sx * w / 2, height + 1.0, sz * w / 2, 0.5, 2.0, 0.5, _dim(PALE_STONE, 1.05))
    r.part("cone", 0, height + 4.0, 0, w * 0.85, 8.0, w * 0.85, WHITE, tex="violet_slate")
    r.part("cube", 0, height + 8.3, 0, 0.08, 0.9, 0.08, IRON)  # a finial
    r.part("cube", 0, height + 8.5, 0, 0.08, 0.08, 0.5, IRON)


def pew(r, seed):
    """A long oak pew facing +X: seat, back, carved ends and a kneeler."""
    wood = _dim(WOOD, 0.85 + (seed % 3) * 0.05)
    r.part("cube", 0, 0.45, 0, 0.5, 0.08, 1.8, wood, tex="wood_plank")  # seat
    r.part("cube", -0.25, 0.85, 0, 0.08, 0.8, 1.8, wood, tex="wood_plank")  # back
    r.part("cube", -0.25, 1.27, 0, 0.12, 0.06, 1.85, _dim(wood, 0.8))  # its rail
    for z in (-0.92, 0.92):  # ends with rounded tops
        r.part("cube", -0.02, 0.5, z, 0.6, 1.0, 0.08, _dim(wood, 0.9))
        r.part("cyl", -0.02, 1.0, z, 0.3, 0.08, 0.3, _dim(wood, 0.9), rx=math.pi / 2)
    r.part("cube", 0.5, 0.15, 0, 0.18, 0.1, 1.7, _dim(wood, 0.7))  # kneeler in front


def _stained_glass(r, x, cy, w, h, seed, k=1.0):
    """A lancet of leaded glass in the plane x (facing +X), centred `cy` up and `w` x `h` across:
    quarries in shifting colours set in dark came, a gold sun roundel in the middle, a pointed head."""
    cols, rows = 3, 6
    body = h - w / 2
    qw, qh = w / cols, body / rows
    r.part("cube", x - 0.01, cy - w / 4, 0, 0.02, body, w + 0.04, LEAD)  # the came behind it all
    for j in range(rows):
        for i in range(cols):
            rgb = STAINED[(seed + i * 2 + j * 3 + (i * j) % 3) % len(STAINED)]
            y = cy - h / 2 + qh * (j + 0.5)
            r.part("cube", x, y, -w / 2 + qw * (i + 0.5), 0.02, qh * 0.84, qw * 0.8, _dim(rgb, k), glow=True)
    # The roundel: a gold sun on blue, as on the realm's crest.
    ry = cy - h / 2 + body * 0.55
    r.part("cyl", x + 0.01, ry, 0, w * 0.7, 0.02, w * 0.7, LEAD, rz=math.pi / 2)
    r.part("cyl", x + 0.015, ry, 0, w * 0.6, 0.02, w * 0.6, _dim(STAINED[1], k), glow=True, rz=math.pi / 2)
    r.part("cyl", x + 0.02, ry, 0, w * 0.3, 0.02, w * 0.3, _dim(STAINED[2], k), glow=True, rz=math.pi / 2)
    # The pointed head: two panes leaning together.
    top = cy + h / 2 - w / 4
    for side in (-1, 1):
        rgb = STAINED[(seed + 4 + side) % len(STAINED)]
        r.part("cube", x, top, side * w / 4, 0.02, w * 0.45, w * 0.36, _dim(rgb, k), glow=True, rx=side * 0.5)


def window(r, seed):
    """A tall lancet of stained glass set in the wall at local -X, glowing with the grey day outside:
    diamond quarries of ruby, cobalt, gold and green around a sun roundel, in stone tracery."""
    _stained_glass(r, -0.95, 2.6, 0.9, 3.4, seed)
    stone = PALE_STONE
    for z in (-0.52, 0.52):  # the splayed reveal
        r.part("cube", -0.94, 2.4, z, 0.1, 3.4, 0.12, stone, tex="rough_stone")
    r.part("cube", -0.94, 0.85, 0, 0.16, 0.1, 1.2, _dim(stone, 0.9))  # the sill
    r.part("cube", -0.94, 2.6, 0, 0.04, 3.2, 0.04, LEAD)  # the mullion
    for side in (-1, 1):  # the arch over it
        r.part("cube", -0.94, 4.25, side * 0.27, 0.1, 0.12, 0.62, stone, rx=side * 0.62)


def stained_window(r, seed):
    """The outside of a cathedral window, on the wall at local -X: the same glass, dimmer by day, in a
    stone surround with a hood mould over its point and a sill below."""
    _stained_glass(r, -0.96, 3.4, 0.9, 3.6, seed, k=0.7)
    stone = _dim(PALE_STONE, 1.05)
    for z in (-0.56, 0.56):
        r.part("cube", -0.92, 3.3, z, 0.18, 3.8, 0.2, stone, tex="rough_stone")
    r.part("cube", -0.88, 1.5, 0, 0.26, 0.14, 1.4, stone)  # sill
    for side in (-1, 1):  # the hood mould, ending in two carved stops
        r.part("cube", -0.88, 5.3, side * 0.3, 0.16, 0.14, 0.72, stone, rx=side * 0.6)
        r.part("cube", -0.88, 4.9, side * 0.62, 0.18, 0.2, 0.16, _dim(stone, 0.85))


def rose_window(r, seed, x=-0.92):
    """A rose window: a wheel of glowing petals round a gold sun, in a ring of stone with spoke
    tracery, in the plane x facing +X. Its centre is the origin."""
    radius = 1.0
    for i in range(16):  # the stone ring
        a = i * math.pi / 8
        r.part(
            "cube",
            x,
            math.sin(a) * radius,
            math.cos(a) * radius,
            0.16,
            0.16,
            0.42,
            PALE_STONE,
            rx=-a,
        )
    r.part("cyl", x - 0.02, 0, 0, radius * 1.9, 0.02, radius * 1.9, LEAD, rz=math.pi / 2)
    for i in range(12):  # the petals, alternating ruby and cobalt, each tipped in gold
        a = i * math.pi / 6
        rgb = STAINED[0] if i % 2 == 0 else STAINED[1]
        ca, sa = math.cos(a), math.sin(a)
        r.part("cube", x + 0.01, sa * 0.55, ca * 0.55, 0.02, 0.5, 0.2, rgb, glow=True, rx=math.pi / 2 - a)
        r.part("cube", x + 0.01, sa * 0.86, ca * 0.86, 0.02, 0.12, 0.12, STAINED[2 + i % 3], glow=True)
        r.part(
            "cube", x + 0.03, sa * 0.6, ca * 0.6, 0.03, 0.8, 0.04, _dim(PALE_STONE, 0.9), rx=math.pi / 2 - a
        )
    r.part("cyl", x + 0.02, 0, 0, 0.5, 0.03, 0.5, LEAD, rz=math.pi / 2)
    r.part("cyl", x + 0.03, 0, 0, 0.38, 0.03, 0.38, STAINED[2], glow=True, rz=math.pi / 2)  # the sun
    r.part("cyl", x + 0.04, 0, 0, 0.14, 0.03, 0.14, (250, 220, 140), glow=True, rz=math.pi / 2)


def bed(r, seed):
    """A box bed with a straw mattress and a rumpled blanket, its head toward local -X."""
    blanket = CLOTH[seed % len(CLOTH)]
    r.part("cube", 0, 0.25, 0, 1.9, 0.3, 1.0, DARK_WOOD, tex="wood_plank")
    r.part("cube", -0.95, 0.55, 0, 0.1, 0.9, 1.04, DARK_WOOD, tex="wood_plank")  # headboard
    r.part("cube", 0.95, 0.4, 0, 0.1, 0.6, 1.04, DARK_WOOD, tex="wood_plank")  # footboard
    r.part("cube", 0, 0.45, 0, 1.8, 0.14, 0.92, (190, 170, 120))  # straw mattress
    r.part("cube", -0.65, 0.56, 0, 0.36, 0.1, 0.6, (220, 214, 196))  # pillow
    r.part("cube", 0.25, 0.54, 0, 1.2, 0.1, 0.96, blanket, ry=0.04)
    r.part("cube", -0.3, 0.6, 0.1, 0.3, 0.08, 0.6, _dim(blanket, 0.85), ry=0.4)  # a fold thrown back


def cupboard(r, seed):
    """A tall cupboard against a wall, doors ajar on crockery."""
    r.part("cube", -0.6, 1.0, 0, 0.6, 2.0, 1.4, WOOD, tex="wood_plank")
    r.part("cube", -0.6, 2.05, 0, 0.7, 0.1, 1.5, DARK_WOOD)  # cornice
    r.part("cube", -0.28, 0.6, -0.35, 0.04, 1.0, 0.66, DARK_WOOD, tex="door_wood")  # a shut door
    with r.at(-0.28, 0.6, 0.68, ry=-0.9):
        r.part("cube", 0, 0, -0.33, 0.04, 1.0, 0.66, DARK_WOOD, tex="door_wood")  # one ajar
    r.part("cube", -0.31, 1.45, 0, 0.02, 0.04, 1.3, DARK_WOOD)  # an open shelf above
    for i in range(3):
        r.part("cyl", -0.45, 1.58, -0.4 + i * 0.4, 0.2, 0.22, 0.2, (190 - i * 20, 180, 160))  # jugs
    if seed % 2:
        r.part("cyl", -0.45, 1.86, 0, 0.36, 0.04, 0.36, (200, 196, 186), rz=1.3)  # a plate on edge


def shelf(r, seed):
    """Two plank shelves on the wall at local -X, with jars, bundles and a book."""
    for y in (1.2, 1.8):
        r.part("cube", -0.82, y, 0, 0.32, 0.05, 1.5, WOOD, tex="wood_plank")
        for z in (-0.6, 0.6):
            r.part("cube", -0.9, y - 0.1, z, 0.16, 0.16, 0.04, DARK_WOOD, rz=0.7)  # brackets
    for i in range(4):
        z = -0.55 + i * 0.37
        h = 0.18 + ((seed + i) % 3) * 0.06
        rgb = ((90, 120, 80), (150, 110, 70), (100, 90, 120), (170, 160, 140))[(seed + i) % 4]
        r.part("cyl", -0.82, 1.23 + h / 2, z, 0.14, h, 0.14, rgb)
    r.part("cube", -0.82, 1.92, -0.3, 0.2, 0.2, 0.06, (110, 50, 40))  # a book
    r.part("cube", -0.82, 1.9, 0.2, 0.22, 0.14, 0.4, (110, 140, 70))  # a bundle of herbs


def hearth(r, t):
    """A stone hearth against the wall at local -X: a fire on its bed, a pot hung over it, a mantel."""
    stone = (110, 104, 96)
    r.part("cube", -0.75, 0.9, 0, 0.5, 1.8, 1.8, stone, tex="rough_stone")  # chimney breast
    r.part("cube", -0.5, 0.1, 0, 1.0, 0.2, 1.6, _dim(stone, 0.85), tex="flagstone")  # hearthstone
    for z in (-0.7, 0.7):
        r.part("cube", -0.42, 0.6, z, 0.36, 1.0, 0.2, stone, tex="rough_stone")  # cheeks
    r.part("cube", -0.42, 1.18, 0, 0.5, 0.16, 1.8, DARK_WOOD)  # mantel
    r.part("cube", -0.45, 0.42, 0, 0.3, 0.6, 1.2, (24, 20, 18))  # the soot-black opening
    for k in range(3):  # logs
        r.part("cube", -0.38, 0.26, 0, 0.12, 0.12, 0.8, (60, 40, 26), ry=k * 0.6 - 0.6)
    _flame(r, -0.36, 0.34, -0.15, 0.2, t)
    _flame(r, -0.36, 0.34, 0.15, 0.17, t + 1.3)
    r.part("cube", -0.36, 0.95, 0, 0.02, 0.4, 0.02, IRON)  # the pot's chain
    r.part("sphere", -0.36, 0.7, 0, 0.32, 0.26, 0.32, (40, 38, 40))  # the pot
    for i in range(2):
        r.part("cyl", -0.42, 1.34, -0.4 + i * 0.8, 0.1, 0.16, 0.1, (170, 150, 110))  # mantel jars


SIGN_IRON = (52, 50, 54)


def _disc(r, x, y, w, h, thick, rgb, tex="white"):
    """An upright oval in the XY plane, `w` across and `h` tall, `thick` through along Z."""
    r.part("cyl", x, y, 0, w, thick, h, rgb, tex=tex, rx=math.pi / 2)


def _sign_anvil(r, x, y, z):
    r.part("cube", x, y + 0.05, z, 0.3, 0.06, 0.012, SIGN_IRON)  # the anvil's face
    r.part("cube", x - 0.19, y + 0.06, z, 0.1, 0.035, 0.012, SIGN_IRON)  # its horn
    r.part("cube", x + 0.01, y - 0.03, z, 0.11, 0.1, 0.012, SIGN_IRON)  # its waist
    r.part("cube", x + 0.01, y - 0.1, z, 0.24, 0.045, 0.012, SIGN_IRON)  # its foot
    r.part("cube", x + 0.06, y + 0.2, z, 0.24, 0.03, 0.012, (120, 84, 50), rz=-0.7)  # the hammer's haft
    r.part("cube", x - 0.02, y + 0.27, z, 0.06, 0.11, 0.012, SIGN_IRON, rz=-0.7)  # its head


def _sign_scroll(r, x, y, z):
    paper = (216, 198, 152)
    r.part("cube", x, y, z, 0.26, 0.3, 0.012, paper)  # the sheet
    for dy in (-0.16, 0.16):  # its rolled ends
        r.part("cube", x, y + dy, z, 0.32, 0.05, 0.016, _dim(paper, 0.82))
    for k in range(3):  # lines of writing
        r.part("cube", x - 0.01, y + 0.07 - k * 0.06, z, 0.17 - k * 0.03, 0.015, 0.016, (70, 52, 40))
    r.part("cube", x + 0.07, y - 0.1, z, 0.06, 0.06, 0.02, (150, 30, 30))  # its wax seal


def _sign_flask(r, x, y, z):
    r.part("cube", x, y - 0.06, z, 0.24, 0.22, 0.012, (150, 34, 40))  # the bottle's belly
    r.part("cube", x, y - 0.06, z, 0.18, 0.28, 0.012, (150, 34, 40))  # rounded above and below
    r.part("cube", x - 0.05, y - 0.02, z, 0.04, 0.08, 0.016, (226, 150, 140))  # a glint
    r.part("cube", x, y + 0.13, z, 0.08, 0.12, 0.012, (170, 186, 180))  # its glass neck
    r.part("cube", x, y + 0.21, z, 0.1, 0.05, 0.016, (130, 96, 60))  # its cork
    r.part("cube", x + 0.15, y + 0.12, z, 0.1, 0.04, 0.012, (70, 120, 60), rz=0.6)  # a sprig of herb
    r.part("cube", x + 0.17, y + 0.04, z, 0.08, 0.035, 0.012, (70, 120, 60), rz=-0.4)


def _sign_blades(r, x, y, z):
    steel, hilt = (196, 200, 206), (60, 40, 30)
    for side in (-1, 1):  # two blades crossed, points up
        turn = side * 0.62
        ux, uy = -math.sin(turn), math.cos(turn)
        r.part("cube", x + ux * 0.05, y + uy * 0.05, z, 0.035, 0.42, 0.012, steel, rz=turn)  # the blade
        gx, gy = x - ux * 0.16, y - uy * 0.16
        r.part("cube", gx, gy, z + side * 0.002, 0.13, 0.03, 0.016, GILT, rz=turn)  # its guard
        r.part("cube", gx - ux * 0.06, gy - uy * 0.06, z, 0.03, 0.1, 0.014, hilt, rz=turn)  # its grip


# What each shop paints on its sign: the board's colour and the emblem drawn on both its faces.
SIGN_EMBLEMS = {
    "anvil": ((178, 160, 126), _sign_anvil),
    "scroll": ((84, 52, 104), _sign_scroll),
    "flask": ((176, 162, 128), _sign_flask),
    "blades": ((96, 40, 40), _sign_blades),
}
SIGN_W, SIGN_H = 0.62, 0.84  # the plaque's painted oval, metres


def shop_sign(r, emblem="anvil"):
    """A shop's sign, hung from the wall at local -X: a wrought-iron bracket standing out over the
    street (its wall plate, the arm with a curled scroll and a finial, a brace beneath), and from two
    rings on it an oval plaque in a gilt rim and a dark frame, a little crest atop and a drop below,
    painted on both faces with the shop's emblem (`SIGN_EMBLEMS`: anvil, scroll, flask, blades)."""
    board, draw = SIGN_EMBLEMS.get(emblem, SIGN_EMBLEMS["anvil"])
    arm_y, cx = 3.35, -0.42
    r.part("cube", -0.97, 3.1, 0, 0.05, 0.7, 0.14, SIGN_IRON)  # the wall plate
    _bar(r, (-0.97, arm_y, 0), (0.02, arm_y, 0), 0.045, SIGN_IRON)  # the arm
    r.part("sphere", 0.04, arm_y, 0, 0.09, 0.09, 0.09, SIGN_IRON)  # its finial
    r.part("cone", 0.04, arm_y + 0.1, 0, 0.05, 0.12, 0.05, SIGN_IRON)
    _bar(r, (-0.97, 2.85, 0), (-0.38, arm_y, 0), 0.035, SIGN_IRON)  # the brace
    curl = [(-0.92, 2.95), (-0.78, 3.0), (-0.68, 3.1), (-0.7, 3.22), (-0.8, 3.24), (-0.84, 3.15)]
    for a, b in itertools.pairwise(curl):  # a scroll curled between arm and brace
        _bar(r, (a[0], a[1], 0), (b[0], b[1], 0), 0.028, SIGN_IRON)
    _bar(r, (-0.38, arm_y, 0), (-0.2, 3.22, 0), 0.028, SIGN_IRON)  # a smaller curl beyond
    _bar(r, (-0.2, 3.22, 0), (-0.14, 3.3, 0), 0.028, SIGN_IRON)
    top = 2.62 + SIGN_H / 2
    for x in (cx - 0.16, cx + 0.16):  # the rings it hangs by
        r.part("cube", x, (top + arm_y) / 2, 0, 0.03, arm_y - top + 0.04, 0.03, SIGN_IRON)
    y = 2.62
    _disc(r, cx, y, SIGN_W + 0.14, SIGN_H + 0.14, 0.04, DARK_WOOD)  # the frame
    _disc(r, cx, y, SIGN_W + 0.07, SIGN_H + 0.07, 0.05, GILT)  # the gilt rim
    _disc(r, cx, y, SIGN_W, SIGN_H, 0.06, board)  # the painted face
    r.part("cube", cx, top + 0.06, 0, 0.26, 0.08, 0.05, DARK_WOOD)  # the crest's base
    r.part("wedge", cx, top + 0.14, 0, 0.2, 0.12, 0.05, GILT)  # the crest atop
    r.part("sphere", cx, y - SIGN_H / 2 - 0.08, 0, 0.08, 0.1, 0.05, GILT)  # the drop below
    for side in (-1, 1):  # the emblem on each face
        draw(r, cx, y - 0.02, side * 0.034)


def forge_bellows(r, seed):
    """A smith's great bellows on a trestle: two tapering boards with a pleated leather bag between,
    an iron nozzle at the narrow end pointing toward the forge (+X), and a pole to work it."""
    leather = (92, 62, 40)
    for z in (-0.25, 0.25):  # the trestle's legs
        for x in (-0.5, 0.3):
            r.part("cube", x, 0.3, z, 0.08, 0.6, 0.08, DARK_WOOD)
    r.part("cube", -0.1, 0.6, 0, 0.9, 0.06, 0.6, WOOD, tex="wood_plank")  # its top
    r.part("wedge", -0.1, 0.7, 0, 0.12, 1.0, 0.6, WOOD, rz=-math.pi / 2)  # the lower board
    for k in range(3):  # the leather's pleats, narrowing toward the nozzle
        r.part("wedge", -0.12 - k * 0.02, 0.8 + k * 0.06, 0, 0.1, 0.92 - k * 0.1, 0.58 - k * 0.04,
               _dim(leather, 1 - 0.1 * (k % 2)), rz=-math.pi / 2)  # fmt: skip
    r.part("wedge", -0.16, 1.0, 0, 0.1, 0.9, 0.56, WOOD, rz=-math.pi / 2)  # the upper board
    r.part("cube", 0.48, 0.74, 0, 0.24, 0.06, 0.06, IRON)  # the nozzle
    r.part("cube", -0.6, 1.0, 0, 0.12, 0.08, 0.08, DARK_WOOD)  # the handle's yoke
    r.part("cube", -0.62, 1.4, 0, 0.05, 0.8, 0.05, DARK_WOOD, rz=0.25)  # the pole to work it


def grindstone(r, seed):
    """A grindstone on a wooden frame: a sandstone wheel on an iron axle, a crank, a drip pot above
    it and a trough of water beneath for the wheel to run through."""
    for z in (-0.3, 0.3):
        r.part("cube", 0, 0.45, z, 0.1, 0.9, 0.1, DARK_WOOD, rz=0.15)  # the frame's legs
        r.part("cube", 0, 0.45, z, 0.1, 0.9, 0.1, DARK_WOOD, rz=-0.15)
        r.part("cube", 0, 0.88, z, 0.12, 0.1, 0.12, WOOD)  # bearing blocks
    r.part("cube", 0, 0.25, 0, 0.6, 0.06, 0.66, WOOD)  # a stretcher
    r.part("cube", 0, 0.42, 0, 0.62, 0.22, 0.32, DARK_WOOD, tex="wood_plank")  # the trough
    r.part("cube", 0, 0.52, 0, 0.56, 0.02, 0.26, (60, 80, 90))  # its water
    r.part("cyl", 0, 0.88, 0, 0.62, 0.14, 0.62, SANDSTONE, rx=math.pi / 2)  # the wheel
    r.part("cyl", 0, 0.88, 0, 0.66, 0.1, 0.66, _dim(SANDSTONE, 0.8), rx=math.pi / 2)  # its worn rim
    r.part("cyl", 0, 0.88, 0, 0.05, 0.8, 0.05, IRON, rx=math.pi / 2)  # the axle
    r.part("cube", 0.1, 0.88, 0.42, 0.24, 0.04, 0.04, IRON)  # the crank
    r.part("cube", 0.2, 0.88, 0.48, 0.04, 0.04, 0.14, DARK_WOOD)  # its handle
    r.part("cube", 0, 1.32, 0, 0.06, 0.12, 0.06, DARK_WOOD)  # the drip pot's post
    r.part("cube", 0, 1.42, 0, 0.14, 0.1, 0.14, (120, 96, 70))  # the drip pot


def banner_pole(r, t, seed):
    """A tall flagpole on a stone foot flying the realm's banner from a crossbar: the setting-sun
    tower in gold on both faces of the cloth, its tails stirring in the wind."""
    stone = PALE_STONE
    r.part("cube", 0, 0.2, 0, 0.7, 0.4, 0.7, stone, tex="rough_stone")
    r.part("cube", 0, 0.5, 0, 0.5, 0.2, 0.5, _dim(stone, 1.1))
    r.part("cyl", 0, 3.8, 0, 0.14, 6.6, 0.14, DARK_WOOD)
    r.part("sphere", 0, 7.2, 0, 0.2, 0.2, 0.2, GILT)  # the finial
    r.part("cube", 0, 7.0, 0, 0.08, 0.08, 1.3, DARK_WOOD)  # the crossbar
    cloth = REALM_CLOTH[seed % len(REALM_CLOTH)]
    sway = math.sin(t * 0.9 + seed) * 0.05
    with r.at(0.1, 6.95, 0, rz=sway):
        r.part("cube", 0, -1.2, 0, 0.03, 2.4, 1.2, cloth)
        for i, z in enumerate((-0.45, -0.15, 0.15, 0.45)):  # swallow tails
            r.part("cube", 0, -2.5 - (i % 2) * 0.12, z, 0.03, 0.25 + (i % 2) * 0.2, 0.3, cloth)
        r.part("cube", 0.01, -0.06, 0, 0.03, 0.08, 1.22, GILT)  # a gold hem along the top
        realm_crest(r, GILT, cy=-1.1, scale=1.4, through=0.05)  # on both faces


def crest_plaque(r, seed):
    """The realm's crest carved in a slab of stone set into the wall at local -X, its relief gilded,
    under a little drip moulding."""
    stone = (226, 222, 214)
    r.part("cube", -0.94, 0, 0, 0.12, 1.5, 1.2, stone, tex="rough_stone")
    r.part("cube", -0.9, 0.82, 0, 0.2, 0.12, 1.36, _dim(stone, 0.9))  # the drip moulding
    r.part("cube", -0.9, -0.8, 0, 0.18, 0.1, 1.28, _dim(stone, 0.9))  # its ledge
    with r.at(-0.9, 0, 0):
        realm_crest(r, GILT if seed % 3 else _dim(GILT, 0.9), cy=0.0, scale=1.45)


SHUTTER_OAK = ((96, 40, 34), (58, 78, 60), (92, 66, 42), (62, 50, 40))  # oxblood, weathered green, oak
WINDOW_GLOW = (118, 90, 54)  # lamplight through leaded glass
OAK = (74, 54, 36)


def _board_shutter(r, w, h, paint, seed):
    """A board-and-batten shutter hung at the origin and reaching along +Z: upright planks, two ledges
    and a brace on its back, black iron strap hinges across its face."""
    for i in range(3):
        r.part("cube", 0, 0, w * (i + 0.5) / 3, 0.04, h - 0.02 * (i % 2), w / 3 - 0.01,
               _dim(paint, 0.92 + 0.08 * ((seed + i) % 2)), tex="wood_plank")  # fmt: skip
    for y in (-h * 0.32, h * 0.32):
        r.part("cube", 0.03, y, w / 2, 0.03, 0.08, w * 0.9, _dim(paint, 0.75))  # the ledges
        r.part("cube", 0.05, y, w * 0.38, 0.015, 0.05, w * 0.76, IRON)  # a strap hinge
        r.part("cube", 0.05, y, w * 0.76, 0.02, 0.07, 0.07, IRON)  # its spade end
        r.part("cube", 0.0, y, -0.02, 0.06, 0.08, 0.05, IRON)  # the pintle in the wall
    _bar(r, (0.03, -h * 0.32, w * 0.12), (0.03, h * 0.32, w * 0.88), 0.05, _dim(paint, 0.7))  # the brace


def shutters(r, seed, timber=False):
    """A medieval window deep in a house wall at local -X: two round-headed lights of leaded diamond
    quarries faintly lit within, parted by a mullion, in a dressed stone surround under a hood mould
    with carved stops (an oak frame under a pegged lintel in a half-timbered wall), its two board
    shutters strapped in iron and folded back, one now and then half shut, some lights barred."""
    stone = (236, 230, 218)
    frame = OAK if timber else stone
    tex = "wood_plank" if timber else "ashlar"
    paint = SHUTTER_OAK[seed % len(SHUTTER_OAK)]
    lw, low, spring = 0.36, -0.55, 0.3  # each light's width, its foot and where its head springs
    rad = lw / 2
    head = spring + rad + 0.1
    r.part("cube", -0.975, (head + 0.62) / 2, 0, 0.05, 0.62 - head + 0.02, 1.0, _dim(frame, 0.92),
           tex=tex)  # fmt: skip  # the head of the surround, over the arches
    for zc in (-0.24, 0.24):
        r.part("cube", -0.985, (low + spring) / 2, zc, 0.02, spring - low, lw, (30, 26, 22))  # the reveal
        r.part("cube", -0.955, (low + spring) / 2, zc, 0.01, spring - low - 0.04, lw - 0.04, WINDOW_GLOW,
               glow=True)  # fmt: skip
        for i in range(3):  # the round head, glazed in strips
            z = zc - rad + lw * (i + 0.5) / 3
            hh = math.sqrt(max(rad * rad - (z - zc) ** 2, 0.0)) * 0.9
            r.part("cube", -0.955, spring + hh / 2, z, 0.01, hh, lw / 3, WINDOW_GLOW, glow=True)
        # The leading: diagonal cames crossing into diamonds, and a saddle bar across.
        for k in range(5):
            y = low + rad + k * 0.18
            for rx in (math.pi / 4, -math.pi / 4):
                r.part("cube", -0.94, y, zc, 0.012, 0.015, lw * 1.36, LEAD, rx=rx)
        r.part("cube", -0.935, -0.12, zc, 0.014, 0.025, lw, IRON)
        for i in range(7):  # the voussoirs of its head
            a = math.pi * i / 6
            r.part("cube", -0.93, spring + math.sin(a) * (rad + 0.04), zc + math.cos(a) * (rad + 0.04),
                   0.08, 0.08, 0.1, _dim(frame, 0.95 + 0.06 * (i % 2)), rx=math.pi / 2 - a)  # fmt: skip
    r.part("cube", -0.93, (low + spring) / 2, 0, 0.08, spring - low, 0.1, frame, tex=tex)  # the mullion
    r.part("cube", -0.92, spring, 0, 0.1, 0.06, 0.14, _dim(frame, 1.08))  # its little capital
    for side in (-1, 1):  # the jambs, their chamfer a darker strip
        r.part("cube", -0.93, (low + spring) / 2 + 0.04, side * 0.46, 0.08, spring - low + 0.1, 0.08,
               frame, tex=tex)  # fmt: skip
        r.part("cube", -0.9, (low + spring) / 2 + 0.04, side * 0.415, 0.02, spring - low + 0.1, 0.025,
               _dim(frame, 0.78))  # fmt: skip
    r.part("cube", -0.88, low - 0.08, 0, 0.24, 0.1, 1.1, _dim(frame, 0.95), tex=tex)  # the sill
    r.part("cube", -0.8, low - 0.15, 0, 0.06, 0.04, 1.04, _dim(frame, 0.75))  # its drip
    if timber:  # a moulded oak lintel, pegged
        r.part("cube", -0.9, 0.64, 0, 0.16, 0.14, 1.2, _dim(OAK, 0.9), tex="wood_plank")
        r.part("cube", -0.84, 0.56, 0, 0.06, 0.04, 1.12, _dim(OAK, 0.7))
        for z in (-0.5, 0.5):
            r.part("cube", -0.815, 0.64, z, 0.02, 0.05, 0.05, (150, 128, 96))
    else:  # the hood mould, ending in carved stops
        r.part("cube", -0.88, 0.66, 0, 0.16, 0.1, 1.16, _dim(stone, 1.04), tex=tex)
        for side in (-1, 1):
            r.part("cube", -0.88, 0.53, side * 0.56, 0.18, 0.18, 0.1, _dim(stone, 0.85))
            r.part("cube", -0.8, 0.5, side * 0.56, 0.04, 0.08, 0.08, _dim(stone, 0.7))  # its worn face
    if seed % 3 == 2:  # an iron grille over the lights
        for z in (-0.32, -0.16, 0.16, 0.32):
            r.part("cube", -0.88, (low + spring) / 2, z, 0.03, spring - low, 0.03, IRON)
        r.part("cube", -0.88, -0.22, 0, 0.03, 0.03, 0.8, IRON)
    shut = seed % 4 == 1  # one shutter swung half shut
    for side in (-1, 1):
        swing = 0.9 if shut and side == 1 else 0.0
        with r.at(-0.95, 0.0, side * 0.5, ry=(swing if side == 1 else math.pi)):
            _board_shutter(r, 0.44, 1.12, paint, seed + side)


def balcony(r, seed, roof_tex="violet_slate"):
    """An upper-floor gallery jettied out of the wall at local -X: a plank deck on carved corbels and
    raking braces, a parapet of boards under a rail, a half-open door behind it, and a pent roof of slate
    (or `roof_tex`) over it on two brackets; some days a rug airs over the boards or a lantern hangs from the roof."""
    wood = _dim(WOOD, 0.9)
    r.part("cube", -0.98, 1.05, 0, 0.03, 2.1, 1.0, (34, 28, 24))  # the doorway behind
    with r.at(-0.97, 1.05, -0.5, ry=-1.1):
        r.part("cube", 0.02, 0, 0.45, 0.06, 2.0, 0.9, DARK_WOOD, tex="door_wood")  # its door, ajar
    r.part("cube", -0.92, 2.2, 0, 0.14, 0.14, 1.2, _dim(DARK_WOOD, 1.1))  # the lintel beam
    r.part("cube", -0.58, -0.06, 0, 0.84, 0.12, 2.0, wood, tex="wood_plank")  # the deck
    for z in (-0.8, 0.0, 0.8):  # corbels: joists running out of the wall
        r.part("cube", -0.6, -0.18, z, 0.8, 0.14, 0.16, DARK_WOOD)
        r.part("cube", -0.2, -0.24, z, 0.08, 0.1, 0.17, _dim(DARK_WOOD, 0.8))  # its carved end
    for z in (-0.8, 0.8):  # raking braces down to the wall
        _bar(r, (-0.98, -1.0, z), (-0.32, -0.22, z), 0.12, DARK_WOOD)
    for i in range(8):  # the parapet's boards
        r.part("cube", -0.18, 0.45, -0.875 + i * 0.25, 0.05, 0.82 - 0.03 * (i % 2), 0.24,
               _dim(wood, 0.9 + 0.08 * ((seed + i) % 3)), tex="wood_plank")  # fmt: skip
    for z in (-0.97, 0.97):
        r.part("cube", -0.58, 0.45, z, 0.8, 0.82, 0.05, wood, tex="wood_plank")  # its ends
        r.part("cube", -0.58, 0.9, z, 0.84, 0.08, 0.09, DARK_WOOD)
        r.part("cube", -0.18, 0.45, z, 0.1, 0.96, 0.1, DARK_WOOD)  # the corner posts
    r.part("cube", -0.18, 0.9, 0, 0.1, 0.08, 2.0, DARK_WOOD)  # the rail
    r.part("cube", -0.18, 0.12, 0, 0.08, 0.08, 2.0, DARK_WOOD)  # the bottom rail
    for z in (-0.95, 0.95):  # the pent roof's brackets
        _bar(r, (-0.98, 1.9, z), (-0.3, 2.5, z), 0.08, DARK_WOOD)
    with r.at(-0.55, 2.62, 0, rz=-0.38):  # the pent roof, slates over boards
        r.part("cube", 0, 0, 0, 1.05, 0.06, 2.3, DARK_WOOD, tex="wood_plank")
        r.part("cube", 0, 0.05, 0, 1.05, 0.05, 2.3, WHITE, tex=roof_tex)
    if seed % 3 == 0:
        r.part("cube", -0.12, 0.62, 0.2, 0.05, 0.62, 0.9, CLOTH[seed % len(CLOTH)])  # a rug over the boards
    elif seed % 3 == 1:
        with r.at(-0.4, 2.2, 0.6):  # a lantern hung from the roof, unlit by day
            r.part("cube", 0, 0.16, 0, 0.02, 0.2, 0.02, IRON)
            r.part("cube", 0, -0.04, 0, 0.14, 0.2, 0.14, (52, 50, 48))
            r.part("cube", 0, -0.04, 0, 0.11, 0.15, 0.15, (150, 126, 86))
            r.part("cone", 0, 0.1, 0, 0.18, 0.1, 0.18, (52, 50, 48))


def door_arch(r, seed, height=3.2, spring=2.2, rose=False, leaf=True):
    """A house's front door, set in the doorway tile and facing out along +X: a round arch of dressed
    voussoirs on two pilasters at the wall's outer face (x = 1), filled solid above it to the room's
    ceiling, and a studded plank door standing open against the jamb inside (without `leaf`, the
    `house_door` that swings in it is drawn apart). With `rose`, a rose window glows in the tympanum
    (the cathedral's west door)."""
    stone = (236, 230, 218) if not rose else (226, 222, 214)
    tex = "rough_stone" if rose else "ashlar"
    half = 0.9
    for side in (-1, 1):  # the pilasters, with plinths and capitals
        z = side * (half + 0.06)
        r.part("cube", 0.9, spring / 2, z, 0.3, spring, 0.24, stone, tex=tex)
        r.part("cube", 0.93, 0.15, z, 0.36, 0.3, 0.3, _dim(stone, 0.9))
        r.part("cube", 0.93, spring - 0.05, z, 0.36, 0.12, 0.32, _dim(stone, 1.08))
    for i in range(11):  # the voussoirs, the keystone proud and a shade larger
        a = math.pi * i / 10
        key = i == 5
        r.part(
            "cube",
            0.92 + (0.04 if key else 0.0),
            spring + math.sin(a) * half,
            math.cos(a) * half,
            0.32,
            0.3 if key else 0.24,
            0.2 if key else 0.26,
            _dim(stone, 1.1 if key else 0.95 + 0.05 * (i % 2)),
            rx=math.pi / 2 - a,
        )
    # The spandrels and tympanum: solid wall from the arch up to the ceiling, in strips.
    strips = 10
    for i in range(strips):
        z0, z1 = -1.0 + 2.0 * i / strips, -1.0 + 2.0 * (i + 1) / strips
        zm = (z0 + z1) / 2
        under = spring + math.sqrt(max(half * half - zm * zm, 0.0)) if abs(zm) < half else spring
        if height > under:
            r.part(
                "cube",
                0.86,
                (under + height) / 2,
                zm,
                0.28,
                height - under,
                z1 - z0,
                stone,
                tex=tex,
            )
    if rose:
        top = spring + half
        with r.at(1.0, (top + height) / 2 + 0.1, 0):
            rose_window(r, seed, x=0.04)
    else:
        with r.at(1.04, spring + half + 0.02, 0):
            r.part("cube", 0, 0, 0, 0.06, 0.2, 0.2, GILT, rx=math.pi / 4)  # a gilt boss on the keystone
    r.part("cube", 1.02, 0.03, 0, 0.2, 0.06, 2.0, _dim(stone, 0.85), tex="flagstone")  # the threshold
    if not leaf:
        return
    # The door, open against the jamb inside: planks, iron straps, a ring.
    r.part("cube", 0.0, spring / 2 + 0.1, -0.86, 1.5, spring + 0.1, 0.08, DARK_WOOD, tex="door_wood", ry=0.08)
    for y in (0.5, 1.3, 2.0):
        r.part("cube", 0.0, y, -0.81, 1.4, 0.07, 0.03, IRON, ry=0.08)
    r.part("cyl", -0.55, 1.1, -0.79, 0.14, 0.03, 0.14, IRON, rx=math.pi / 2)


DOOR_HINGE = (0.8, -0.86)  # (x, z) of a house door's hinge, just inside the arch's outer face
DOOR_SWING = 1.45  # radians a house door turns, inward, when it stands open
DOOR_HALF = 0.86  # half the leaf's width: it fills the arch's opening


def house_door(r, open_t, spring=2.2, seed=0):
    """A house's own front door in its `door_arch`: a leaf of dark planks filling the arch, round at
    the top, banded with iron straps and a ring on each face, hung on the jamb at `DOOR_HINGE` and
    swung inward (toward -X) by `open_t` (0 shut, 1 open) of `DOOR_SWING`. Drawn every frame, so lean."""
    w = DOOR_HALF * 2
    wood = _dim(DARK_WOOD, 0.9 + 0.1 * (seed % 3))
    with r.at(DOOR_HINGE[0], 0, DOOR_HINGE[1], ry=-open_t * DOOR_SWING):
        r.part("cube", 0, spring / 2 + 0.05, w / 2, 0.08, spring + 0.1, w, wood, tex="door_wood")
        strips = 4  # the round head, built up in strips under the arch
        for i in range(strips):
            zc = -DOOR_HALF + w * (i + 0.5) / strips
            h = math.sqrt(max(DOOR_HALF * DOOR_HALF - zc * zc, 0.0)) * 0.96
            r.part("cube", 0, spring + h / 2, w / 2 + zc, 0.08, h, w / strips, wood, tex="door_wood")
        for y in (0.5, 1.45):  # iron straps through both faces, nailed at the hinge
            r.part("cube", 0, y, w / 2 - 0.05, 0.1, 0.08, w - 0.1, IRON)
            r.part("cube", 0, y, 0.12, 0.12, 0.14, 0.16, IRON)
        for side in (-1, 1):  # a ring on each face, by the latch
            r.part("cyl", side * 0.07, 1.1, w - 0.3, 0.14, 0.03, 0.14, IRON, rz=math.pi / 2)
            r.part("cube", side * 0.05, 1.18, w - 0.3, 0.03, 0.08, 0.08, IRON)


VIOLET_TRIM = (60, 44, 70)  # the dark painted timber of turrets


def roof_turret(r, seed, height=3.2, radius=0.9, cap=3.6, roof_tex="violet_slate"):
    """A little round turret set out on a house's corner, its foot at the origin: a cone of corbels
    swelling out of the wall below, a plastered drum with a slit window or two lit from within, a
    timber band at the eaves, and a tall witch-hat cone of violet slate (or `roof_tex`) with an iron
    finial."""
    d = radius * 2
    trim = VIOLET_TRIM if roof_tex == "violet_slate" else OAK  # painted to suit its roof
    stone = (176, 166, 152)
    r.part("cone", 0, -0.6, 0, d, 1.2, d, _dim(stone, 0.85), tex="ashlar", rx=math.pi)  # the corbelling
    r.part("cyl", 0, height / 2, 0, d, height, d, stone, tex="plaster" if seed % 2 else "ashlar")
    r.part("cyl", 0, 0.05, 0, d + 0.1, 0.16, d + 0.1, trim)  # string course at its foot
    r.part("cyl", 0, height - 0.08, 0, d + 0.12, 0.18, d + 0.12, trim)  # band at the eaves
    for k in range(2 if seed % 3 else 1):  # slit windows, warm behind
        a = seed * 0.7 + k * math.pi * 0.8
        x, z = math.cos(a) * (radius - 0.02), math.sin(a) * (radius - 0.02)
        r.part("cube", x, height * 0.55, z, 0.08, 0.7, 0.22, (32, 26, 24), ry=-a)
        r.part("cube", x * 1.01, height * 0.55, z * 1.01, 0.06, 0.56, 0.12, (150, 108, 62), ry=-a, glow=True)
    r.part("cone", 0, height + cap / 2, 0, d + 0.5, cap, d + 0.5, WHITE, tex=roof_tex)  # witch's hat
    r.part("cyl", 0, height + 0.1, 0, d + 0.56, 0.12, d + 0.56, _dim(trim, 0.8))  # its flared eave
    r.part("cube", 0, height + cap + 0.3, 0, 0.06, 0.7, 0.06, IRON)  # the finial
    r.part("sphere", 0, height + cap + 0.2, 0, 0.14, 0.14, 0.14, IRON)


def wall_tower(r, seed, height=10.0, radius=2.2, cap=5.0, capped=True):
    """A round tower in the town wall: a battered plinth, coursed rough stone with arrow slits, a ring
    of machicolation corbels carrying a crenellated parapet and, `capped`, a steep cone of violet
    slate rising inside it to a gilt finial."""
    d = radius * 2
    stone = (196, 190, 180)
    r.part("cone", 0, 1.2, 0, d + 1.2, 2.4, d + 1.2, _dim(stone, 0.85), tex="rough_stone")  # the batter
    r.part("cyl", 0, height / 2, 0, d, height, d, stone, tex="rough_stone")
    r.part("cyl", 0, height * 0.45, 0, d + 0.14, 0.2, d + 0.14, _dim(stone, 1.08))  # a string course
    for k in range(3):  # arrow slits, staggered up the drum
        a = seed * 0.9 + k * 2.1
        x, z = math.cos(a) * (radius - 0.02), math.sin(a) * (radius - 0.02)
        r.part("cube", x, height * (0.3 + 0.2 * k), z, 0.08, 1.0, 0.16, (24, 22, 26), ry=-a)
    top = height + 0.6
    r.part("cyl", 0, top, 0, d + 0.7, 1.2, d + 0.7, stone, tex="rough_stone")  # the parapet's ring
    n = 10
    for k in range(n):
        a = k * 2 * math.pi / n
        x, z = math.cos(a) * (radius + 0.25), math.sin(a) * (radius + 0.25)
        r.part("cube", x, height - 0.2, z, 0.4, 0.5, 0.4, _dim(stone, 0.8), ry=-a)  # machicolation corbel
        if k % 2 == 0:  # merlons, every other bay
            x, z = math.cos(a) * (radius + 0.2), math.sin(a) * (radius + 0.2)
            r.part("cube", x, top + 0.95, z, 0.4, 0.7, 0.9, stone, tex="rough_stone", ry=-a)
    if capped:
        r.part("cone", 0, top + 0.6 + cap / 2, 0, d + 0.2, cap, d + 0.2, WHITE, tex="violet_slate")
        r.part("cube", 0, top + 0.6 + cap + 0.4, 0, 0.08, 0.8, 0.08, IRON)
        r.part("sphere", 0, top + 0.6 + cap + 0.85, 0, 0.22, 0.22, 0.22, GILT)


def cathedral_tower(r, height=15.0, width=3.8, belfry=True, helm=7.0):
    """A square cathedral tower rising from the ground: stepped buttresses at its corners, lancets
    climbing its faces, a belfry of louvred openings, a corbelled parapet with a pinnacle at each
    corner, and a steep slate helm with a gilt sun on its spike. Narrow and belfry-less, it is one of
    the little stair turrets at the apse."""
    stone = (226, 222, 214)  # pale, under the rough stone's grain, like the walls
    w = width
    r.part("cube", 0, height / 2, 0, w, height, w, stone, tex="rough_stone")
    r.part("cube", 0, 0.8, 0, w + 0.3, 1.6, w + 0.3, _dim(stone, 0.88), tex="rough_stone")  # plinth
    for i in range(3):  # string courses
        r.part("cube", 0, height * (0.28 + 0.24 * i), 0, w + 0.16, 0.2, w + 0.16, _dim(stone, 1.1))
    for sx in (-1, 1):  # stepped buttresses, two to a corner
        for sz in (-1, 1):
            for step, (hh, d) in enumerate(((height * 0.75, 0.5), (height * 0.45, 0.8))):
                x, z = sx * (w / 2 + d / 2 - 0.1), sz * (w / 2 - 0.3)
                r.part("cube", x, hh / 2, z, d, hh, 0.5, _dim(stone, 0.95), tex="rough_stone")
                r.part(
                    "cube",
                    z * sx * sz,
                    hh / 2,
                    sz * (w / 2 + d / 2 - 0.1),
                    0.5,
                    hh,
                    d,
                    _dim(stone, 0.95),
                    tex="rough_stone",
                )
                r.part("wedge", x, hh + 0.25, z, d, 0.5, 0.5, _dim(stone, 1.05), ry=math.pi / 2 * (step % 2))
    belfry_y = height - 2.6
    for a in range(4):  # each face: lancets up its height, then the belfry
        with r.at(0, 0, 0, ry=a * math.pi / 2):
            for y in (height * 0.4, height * 0.62):
                r.part("cube", w / 2 + 0.01, y, 0, 0.04, 1.8, 0.4, (30, 30, 40))
                r.part("cube", w / 2 + 0.02, y, 0, 0.02, 1.5, 0.24, _dim(STAINED[a % 5], 0.7), glow=True)
            if belfry:
                for z in (-0.6, 0.6):
                    r.part("cube", w / 2 + 0.01, belfry_y, z, 0.06, 2.4, 0.7, (24, 22, 26))
                    for k in range(3):  # louvres
                        r.part(
                            "cube",
                            w / 2 + 0.04,
                            belfry_y - 0.7 + k * 0.7,
                            z,
                            0.06,
                            0.06,
                            0.66,
                            DARK_WOOD,
                            rz=0.5,
                        )
                    r.part("wedge", w / 2 + 0.02, belfry_y + 1.45, z, 0.06, 0.5, 0.7, stone, ry=math.pi / 2)
                r.part("cube", w / 2 + 0.05, belfry_y, 0, 0.1, 2.6, 0.14, stone)  # the shaft between
    # The parapet on its corbels, and pinnacles.
    r.part("cube", 0, height + 0.35, 0, w + 0.5, 0.7, w + 0.5, _dim(stone, 1.05), tex="rough_stone")
    for a in range(4):
        with r.at(0, 0, 0, ry=a * math.pi / 2):
            for k in range(4):
                r.part(
                    "cube",
                    w / 2 + 0.12,
                    height - 0.15,
                    -w / 2 + 0.3 + k * (w - 0.6) / 3,
                    0.24,
                    0.3,
                    0.16,
                    _dim(stone, 0.85),
                )
    for sx in (-1, 1):
        for sz in (-1, 1):
            x, z = sx * (w / 2 + 0.1), sz * (w / 2 + 0.1)
            r.part("cube", x, height + 1.0, z, 0.5, 0.9, 0.5, stone)
            r.part("cone", x, height + 2.1, z, 0.5, 1.6, 0.5, _dim(stone, 1.05))
            r.part("sphere", x, height + 2.95, z, 0.14, 0.14, 0.14, GILT)
    r.part(
        "cone", 0, height + 0.7 + helm / 2, 0, w * 0.82, helm, w * 0.82, WHITE, tex="violet_slate"
    )  # the helm
    top = height + 0.7 + helm
    r.part("cube", 0, top + 0.5, 0, 0.08, 1.0, 0.08, IRON)
    r.part("cyl", 0, top + 1.0, 0, 0.36, 0.06, 0.36, GILT, rx=math.pi / 2)  # the gilt sun
    for i in range(8):
        a = i * math.pi / 4
        r.part("cube", math.cos(a) * 0.28, top + 1.0 + math.sin(a) * 0.28, 0, 0.12, 0.05, 0.05, GILT, rz=a)


def flying_buttress(r, seed, top=9.0):
    """A flying buttress beside the nave, the wall at local -X: a stepped pier on the ground with a
    pinnacle, and a sloping flyer on a half arch reaching from it to the wall's head."""
    stone = (226, 222, 214)
    r.part("cube", 0.35, 2.6, 0, 0.9, 5.2, 0.8, stone, tex="rough_stone")  # the pier
    r.part("cube", 0.35, 0.5, 0, 1.1, 1.0, 1.0, _dim(stone, 0.88), tex="rough_stone")
    r.part("wedge", 0.35, 5.45, 0, 0.9, 0.5, 0.8, _dim(stone, 1.05), ry=math.pi / 2)
    r.part("cube", 0.35, 6.2, 0, 0.55, 1.4, 0.55, stone)
    r.part("cone", 0.35, 7.6, 0, 0.55, 1.6, 0.55, _dim(stone, 1.05))  # pinnacle
    r.part("sphere", 0.35, 8.45, 0, 0.12, 0.12, 0.12, GILT if seed % 2 else _dim(stone, 1.1))
    # The flyer: a slab sloping from the pier to the wall, the half arch beneath it.
    x0, y0, x1, y1 = 0.0, 5.6, -1.0, top - 0.6
    length = math.hypot(x1 - x0, y1 - y0)
    ang = math.atan2(y1 - y0, x0 - x1)
    r.part(
        "cube", (x0 + x1) / 2, (y0 + y1) / 2, 0, length + 0.2, 0.36, 0.5, stone, tex="rough_stone", rz=-ang
    )
    for k in range(5):  # the half arch's voussoirs
        a = math.pi / 2 * k / 4
        cx, cy = -1.0, y0 - 0.6
        r.part(
            "cube",
            cx + math.cos(a) * 0.95,
            cy + math.sin(a) * 0.95,
            0,
            0.26,
            0.2,
            0.46,
            _dim(stone, 0.92),
            rz=a - math.pi / 2,
        )


# --- the cathedral's great west front, its stair and its nave -------------------------------------

CATHEDRAL_STONE = (226, 222, 214)  # the cathedral's pale stone, under the rough stone's grain
STEP_STONE = (204, 198, 186)  # the treads of its stairs, worn smooth
PORTAL_HALF = 3.0  # half the width of the cathedral's doorway: three tiles across
PORTAL_SPRING = 3.8  # where its arches spring from their colonnettes
PORTAL_OFF = 0.9  # how far past the middle its arcs are centred: how sharply they point
PORTAL_ORDER = 0.35  # the depth of each receding order of the arch


def _saint(r, s, seed):
    """A carved saint of the realm in a hooded robe, a book held open against the chest and a gilt
    halo behind the head: the cathedral's statues, standing on their corbels."""
    stone = _dim(CATHEDRAL_STONE, 1.04)
    with r.at(0, 0, 0, s=s):
        r.part("cone", 0, 0.75, 0, 0.56, 1.5, 0.5, stone, tex="rough_stone")  # the robe
        r.part("cube", 0, 1.42, 0, 0.26, 0.36, 0.42, stone, tex="rough_stone")  # the shoulders
        r.part("sphere", 0.02, 1.72, 0, 0.14, 0.18, 0.14, stone)  # the head
        r.part("cone", -0.02, 1.7, 0, 0.3, 0.44, 0.3, _dim(stone, 0.92))  # the hood
        r.part("cyl", -0.14, 1.78, 0, 0.5, 0.03, 0.5, GILT, rz=math.pi / 2)  # the halo
        r.part("cube", 0.16, 1.22, 0, 0.08, 0.3, 0.36, _dim(stone, 0.86), ry=0.1 * (seed % 3 - 1))  # the book
        for side in (-1, 1):
            _bar(r, (0.04, 1.38, side * 0.2), (0.18, 1.2, side * 0.12), 0.08, stone)  # the arms holding it


def great_rose(r, seed, radius=1.6):
    """The cathedral's great rose over its west door, centred on the origin in the plane x = 0 facing
    +X: a deep moulded ring under a hood, an outer ring of glowing roundels, twelve lancet petals of
    ruby and cobalt between stone spokes, a ring of trefoils of gold and green, and a gold sun at its
    heart."""
    rad = radius
    stone = CATHEDRAL_STONE
    r.part("cyl", -0.08, 0, 0, 2 * rad + 0.5, 0.06, 2 * rad + 0.5, _dim(stone, 0.8), tex="rough_stone",
           rz=math.pi / 2)  # fmt: skip  # the stone it is set in
    r.part("cyl", -0.03, 0, 0, 2 * rad, 0.04, 2 * rad, LEAD, rz=math.pi / 2)  # the leading behind
    _wheel(r, 0.08, rad, 28, 0.26, 0.26, stone, tex="rough_stone")  # the moulded ring
    _wheel(r, 0.14, rad + 0.24, 32, 0.12, 0.16, _dim(stone, 0.8))  # its hood
    for i in range(16):  # the outer roundels
        a = 2 * math.pi * (i + 0.5) / 16
        rgb = STAINED[(i + seed) % 2 * 2]  # ruby and gold in turn
        r.part("cyl", 0.0, math.sin(a) * 0.86 * rad, math.cos(a) * 0.86 * rad, 0.17 * rad, 0.03, 0.17 * rad,
               rgb, glow=True, rz=math.pi / 2)  # fmt: skip
    for i in range(12):  # the petals, parted by stone spokes
        a = 2 * math.pi * i / 12
        ca, sa = math.cos(a), math.sin(a)
        rgb = STAINED[1] if i % 2 else STAINED[0]
        r.part("cube", 0.0, sa * 0.52 * rad, ca * 0.52 * rad, 0.03, 0.4 * rad, 0.16 * rad, rgb, glow=True,
               rx=math.pi / 2 - a)  # fmt: skip
        r.part("cube", 0.0, sa * 0.73 * rad, ca * 0.73 * rad, 0.03, 0.08 * rad, 0.09 * rad, STAINED[4],
               glow=True, rx=math.pi / 2 - a)  # fmt: skip
        b = a + math.pi / 12  # the spoke between this petal and the next
        r.part("cube", 0.05, math.sin(b) * 0.56 * rad, math.cos(b) * 0.56 * rad, 0.1, 0.62 * rad, 0.06,
               _dim(stone, 0.92), rx=math.pi / 2 - b)  # fmt: skip
    _wheel(r, 0.06, 0.74 * rad, 24, 0.06, 0.1, _dim(stone, 0.95))  # the ring between petals and roundels
    _wheel(r, 0.06, 0.3 * rad, 16, 0.08, 0.12, stone)  # the inner ring
    for i in range(6):  # trefoils of gold and green round the heart
        a = 2 * math.pi * i / 6
        rgb = STAINED[2] if i % 2 else STAINED[3]
        for j in range(3):
            b = a + j * 2 * math.pi / 3
            r.part("cyl", 0.01, math.sin(a) * 0.2 * rad + math.sin(b) * 0.04 * rad,
                   math.cos(a) * 0.2 * rad + math.cos(b) * 0.04 * rad, 0.07 * rad, 0.03, 0.07 * rad, rgb,
                   glow=True, rz=math.pi / 2)  # fmt: skip
    r.part("cyl", 0.04, 0, 0, 0.18 * rad, 0.04, 0.18 * rad, STAINED[2], glow=True, rz=math.pi / 2)  # the sun
    r.part("cyl", 0.06, 0, 0, 0.08 * rad, 0.04, 0.08 * rad, (250, 220, 140), glow=True, rz=math.pi / 2)


def cathedral_portal(r, seed, height=9.0, rose=10.6, gable=3.5, span=14.7):
    """The cathedral's great west door, in the middle of its three-tile doorway and facing out along +X
    from the wall's outer face (x = 1), as a `door_arch` does. Three receding orders of pointed arches
    on clustered colonnettes, a crocketed hood mould with a gilt sun at its point, the realm's crest in
    gilt in the tympanum in a ring of rays; stepped buttresses either side with a saint on a corbel under
    a canopy, rising into crocketed pinnacles; and the two great leaves of dark oak, banded in iron,
    standing open against the jambs inside. The wall above runs up to `height`; over it a stone gable
    (`gable` high, `span` across its foot) fronts the nave's roof and holds the great rose
    (`great_rose`), centred `rose` up."""
    half, spring, off = PORTAL_HALF, PORTAL_SPRING, PORTAL_OFF
    stone, pale, dark = CATHEDRAL_STONE, _dim(CATHEDRAL_STONE, 1.08), _dim(CATHEDRAL_STONE, 0.78)
    # The wall above the inner arch, up to the wall's top, across the whole doorway.
    strips = 16
    for i in range(strips):
        z0 = -half - 0.2 + (2 * half + 0.4) * i / strips
        z1 = z0 + (2 * half + 0.4) / strips
        under = _arch_top((z0 + z1) / 2, spring, half, off)
        r.part("cube", 0.86, (under + height) / 2, (z0 + z1) / 2, 0.3, height - under, z1 - z0 + 0.01, stone,
               tex="rough_stone")  # fmt: skip
    # The receding orders, innermost (recessed into the doorway) to outermost.
    for k in range(3):
        hk = half + PORTAL_ORDER * (k + 0.5)
        xk = 0.62 + 0.28 * k
        for side in (-1, 1):
            z = side * hk
            r.part("cube", xk, spring / 2, z, 0.38, spring, PORTAL_ORDER, stone, tex="ashlar")  # the jamb
            r.part("cube", xk + 0.04, 0.3, z, 0.48, 0.6, PORTAL_ORDER + 0.08, dark, tex="ashlar")  # plinth
            r.part("cyl", xk + 0.2, spring / 2 + 0.25, z, 0.18, spring - 0.9, 0.18, pale)  # its colonnette
            r.part("cube", xk + 0.12, spring - 0.15, z, 0.46, 0.3, PORTAL_ORDER + 0.12, pale)  # its capital
            r.part("cube", xk + 0.18, spring - 0.34, z, 0.32, 0.1, 0.28, _dim(pale, 0.9))  # leaves under it
        _pointed_arch(r, xk, spring, hk, off, 9, 0.4, PORTAL_ORDER, pale if k % 2 else stone, tex="ashlar")
        if k == 1:  # little gilt suns carved along the middle order's soffit
            turn = math.acos(off / (hk + off))
            for i in range(1, 9, 2):
                a = turn * i / 9
                y = spring + (hk + off - 0.2) * math.sin(a)
                zz = (hk + off - 0.2) * math.cos(a) - off
                for side in (-1, 1):
                    r.part("cyl", xk + 0.21, y, side * zz, 0.14, 0.04, 0.14, GILT, rz=math.pi / 2)
    # The hood mould over the outermost order, crocketed, with carved heads for its label stops.
    hood_half = half + PORTAL_ORDER * 3 + 0.1
    apex = _pointed_arch(r, 1.42, spring, hood_half, off, 10, 0.22, 0.2, dark, tex="ashlar")
    radius = hood_half + off
    turn = math.acos(off / radius)
    for side in (-1, 1):
        r.part("cube", 1.42, spring - 0.22, side * hood_half, 0.28, 0.3, 0.3, pale)  # a label stop
        r.part("sphere", 1.56, spring - 0.24, side * hood_half, 0.16, 0.2, 0.16, _dim(pale, 0.95))  # its head
        for i in range(1, 10, 2):  # crockets curling up off the hood
            a = turn * i / 10
            r.part("cube", 1.44, spring + (radius + 0.18) * math.sin(a), side * ((radius + 0.18) * math.cos(a) - off),
                   0.14, 0.14, 0.14, pale, rx=math.pi / 4)  # fmt: skip
    r.part("cube", 1.42, apex + 0.3, 0, 0.12, 0.5, 0.12, pale)  # the finial at its point
    r.part("cyl", 1.46, apex + 0.6, 0, 0.36, 0.05, 0.36, GILT, rz=math.pi / 2)  # a gilt sun on it
    # The lintel over the doorway, a carved frieze along it, and the tympanum above.
    r.part("cube", 0.5, spring - 0.25, 0, 0.36, 0.5, 2 * half + 0.1, pale, tex="ashlar")
    for i in range(13):
        r.part("cube", 0.69, spring - 0.25, -half + 0.25 + i * (2 * half - 0.5) / 12, 0.04, 0.22, 0.22,
               GILT if i % 2 else dark, rx=math.pi / 4)  # fmt: skip
    for i in range(12):
        z0 = -half + 2 * half * i / 12
        zm = z0 + half / 12
        hi = _arch_top(zm, spring, half, off)
        if hi > spring + 0.05:
            r.part("cube", 0.44, (spring + hi) / 2, zm, 0.06, hi - spring, 2 * half / 12 + 0.01,
                   _dim(stone, 0.9), tex="ashlar")  # fmt: skip
    with r.at(0.48, spring + 1.75, 0):  # the realm's crest in gilt, in a ring of rays
        _wheel(r, 0.02, 1.25, 20, 0.12, 0.08, pale)
        for i in range(16):
            a = 2 * math.pi * i / 16
            r.part("cube", 0.02, math.sin(a) * 1.0, math.cos(a) * 1.0, 0.03, 0.3 + 0.12 * (i % 2), 0.05, GILT,
                   rx=math.pi / 2 - a)  # fmt: skip
        realm_crest(r, GILT, cy=0.0, scale=2.2)
    # The buttresses either side, stepping back as they rise into crocketed pinnacles.
    bz = hood_half + 0.5
    top = height - 0.6
    for side in (-1, 1):
        z = side * bz
        r.part("cube", 1.4, 1.9, z, 0.84, 3.8, 0.66, stone, tex="ashlar")
        r.part("wedge", 1.56, 4.0, z, 0.66, 0.4, 0.52, dark, tex="ashlar", ry=math.pi / 2)  # its set-off
        r.part("cube", 1.28, (3.8 + top) / 2, z, 0.6, top - 3.8, 0.56, stone, tex="ashlar")
        r.part("cube", 1.28, top - 0.1, z, 0.7, 0.2, 0.66, dark)
        r.part("cone", 1.28, top + 1.3, z, 0.66, 2.6, 0.66, pale, tex="ashlar")  # the pinnacle
        for i in range(3):  # crockets up its edges
            for j in range(4):
                a = j * math.pi / 2 + math.pi / 4
                kk = 0.2 + 0.25 * i
                rr = 0.3 * (1 - kk)
                r.part("cube", 1.28 + math.cos(a) * rr, top + 2.6 * kk, z + math.sin(a) * rr, 0.08, 0.08, 0.08,
                       pale)  # fmt: skip
        r.part("sphere", 1.28, top + 2.66, z, 0.12, 0.12, 0.12, GILT)
        # A saint on a corbel up its face, under a gabled canopy.
        r.part("cone", 1.88, 4.5, z, 0.5, 0.36, 0.5, dark, rx=math.pi)  # the corbel
        with r.at(1.86, 4.68, z):
            _saint(r, 0.95, seed + side)
        r.part("wedge", 1.86, 6.75, z, 0.66, 0.44, 0.62, pale, tex="ashlar", ry=math.pi / 2)  # canopy
        r.part("cube", 1.86, 6.47, z, 0.6, 0.12, 0.56, dark)
    # The gable over the wall, fronting the roof, coped, with the great rose in it.
    r.part("wedge", 1.4, height + gable / 2, 0, span, gable, 0.16, stone, tex="rough_stone", ry=math.pi / 2)
    tilt = math.atan2(gable, span / 2)
    length = math.hypot(gable, span / 2)
    for side in (-1, 1):
        r.part(
            "cube", 1.5, height + gable / 2, side * span / 4, 0.24, 0.2, length + 0.2, dark, rx=side * tilt
        )
    r.part("cube", 1.5, height + gable + 0.3, 0, 0.1, 0.8, 0.1, IRON)  # a gilt sun over the gable
    r.part("cyl", 1.5, height + gable + 0.75, 0, 0.5, 0.05, 0.5, GILT, rz=math.pi / 2)
    r.part("cube", 1.42, height + 0.05, 0, 0.3, 0.16, span - 0.4, dark)  # a string course at its foot
    with r.at(1.62, rose, 0):
        great_rose(r, seed)
    # The leaves, standing open against the jambs inside: dark oak, iron bands, great ring handles.
    leaf_h = spring - 0.4
    for side in (-1, 1):
        z = side * (half - 0.1)
        face = z - side * 0.08
        r.part("cube", -1.05, leaf_h / 2, z, half - 0.1, leaf_h, 0.12, DARK_WOOD, tex="door_wood")
        for y in (0.6, leaf_h / 2, leaf_h - 0.6):  # its iron bands, studded
            r.part("cube", -1.05, y, face, half - 0.2, 0.12, 0.04, IRON)
            for x in (-0.3, -1.05, -1.8):
                r.part("cube", x, y, face - side * 0.02, 0.06, 0.06, 0.04, IRON)
        r.part("cyl", -2.1, 1.3, face - side * 0.03, 0.26, 0.04, 0.26, IRON, rx=math.pi / 2)  # a ring handle
    r.part("cube", 1.02, 0.03, 0, 0.24, 0.06, 2 * half, _dim(stone, 0.85), tex="flagstone")  # the threshold


def grand_stair(r, run=5, width=3, rise=0.4, steps=4, offset=0.0, cheeks=True):
    """A flight of stone steps from the prop's tile (the top) down along +X over `run` tiles, each a
    stair tile `rise` below the last and cut into `steps` steps, so its top step meets the floor above
    it; `width` tiles across, centred `offset` metres along Z. With `cheeks`, the cathedral's own: on
    the cheek walls either side a raking stone balustrade, a pedestal at each end, wrought-iron
    lanterns burning on the top pair and stone urns on the foot pair. A tile's floor is its lowest
    step, so everything sits on or above it."""
    d = T / steps
    across = width * T
    for i in range(run):
        floor = -i * rise
        for k in range(steps):
            x0 = i * T - T / 2 + k * d
            h = rise * (steps - k) / steps
            rgb = _dim(STEP_STONE, 0.94 + 0.06 * ((i * steps + k) % 2))
            r.part("cube", x0 + d / 2, floor + h / 2, offset, d, h, across, rgb, tex="flagstone")
            r.part(
                "cube", x0 + d - 0.02, floor + h - 0.02, offset, 0.08, 0.05, across + 0.02, _dim(rgb, 0.82)
            )
    if not cheeks:
        return
    slope = rise / T
    x_top, x_foot = -T / 2, run * T - T / 2
    length = (x_foot - x_top) / math.cos(math.atan(slope))
    tilt = -math.atan(slope)

    def line(x):  # the height of the cheek walls' tops where they step down, at x
        return rise - (x - T / 2) * slope

    stone = CATHEDRAL_STONE
    mid = (x_top + x_foot) / 2
    for side in (-1, 1):
        zc = offset + side * (across / 2 + T / 2)  # the middle of the cheek wall
        zb = offset + side * (across / 2 + 0.45)  # the balustrade, along its inner edge
        r.part("cube", mid, line(mid) - 0.1, zc, length, 0.7, T + 0.04, stone, tex="rough_stone", rz=tilt)
        r.part(
            "cube", mid, line(mid) + 0.27, zb, length, 0.06, 0.62, _dim(stone, 1.08), rz=tilt
        )  # the plinth
        r.part("cube", mid, line(mid) + 1.16, zb, length, 0.14, 0.4, _dim(stone, 1.1), rz=tilt)  # the rail
        r.part("cube", mid, line(mid) + 1.07, zb, length, 0.06, 0.3, _dim(stone, 0.9), rz=tilt)
        n = int((x_foot - x_top - 2.4) / 0.36)
        for j in range(n + 1):  # the balusters, upright under the raking rail
            x = x_top + 1.2 + j * (x_foot - x_top - 2.4) / n
            b = line(x) + 0.3
            r.part("cyl", x, b + 0.08, zb, 0.16, 0.16, 0.16, stone)
            r.part("sphere", x, b + 0.3, zb, 0.2, 0.3, 0.2, stone)
            r.part("cyl", x, b + 0.58, zb, 0.1, 0.26, 0.1, stone)
            r.part("cube", x, b + 0.73, zb, 0.18, 0.06, 0.18, _dim(stone, 0.92))
        # The newel pedestals, panelled, capped: the top pair at the head of the flight, the foot pair
        # standing on the ground at its bottom.
        for x, base, h in ((x_top + 0.55, rise, 1.5), (x_foot - 0.55, -(run - 1) * rise, 1.7)):
            r.part("cube", x, base + h / 2, zb, 1.0, h, 1.0, stone, tex="rough_stone")
            r.part("cube", x, base + 0.15, zb, 1.16, 0.3, 1.16, _dim(stone, 0.86), tex="rough_stone")
            r.part("cube", x, base + h + 0.08, zb, 1.2, 0.16, 1.2, _dim(stone, 1.1))
            for face in (-1, 1):  # sunk panels on its faces
                r.part("cube", x + face * 0.5, base + h / 2 + 0.1, zb, 0.02, h - 0.6, 0.6, _dim(stone, 0.8))
                r.part("cube", x, base + h / 2 + 0.1, zb + face * 0.5, 0.6, h - 0.6, 0.02, _dim(stone, 0.8))
            top = base + h + 0.16
            if x < mid:  # a wrought-iron lantern on a scrolled stand
                r.part("cube", x, top + 0.06, zb, 0.5, 0.12, 0.5, IRON)
                r.part("cyl", x, top + 0.6, zb, 0.1, 1.0, 0.1, IRON)
                for a in range(4):
                    ca, sa = math.cos(a * math.pi / 2), math.sin(a * math.pi / 2)
                    _bar(r, (x + ca * 0.24, top + 0.1, zb + sa * 0.24), (x, top + 0.7, zb), 0.04, IRON)
                with r.at(x, top + 1.35, zb):
                    r.part("cube", 0, -0.3, 0, 0.44, 0.06, 0.44, IRON)
                    r.part("cube", 0, 0, 0, 0.36, 0.54, 0.36, (236, 184, 100), glow=True)  # its panes, lit
                    for dx in (-0.19, 0.19):
                        for dz in (-0.19, 0.19):
                            r.part("cube", dx, 0, dz, 0.04, 0.6, 0.04, IRON)
                    r.part("cone", 0, 0.45, 0, 0.56, 0.36, 0.56, IRON)  # its crown
                    r.part("sphere", 0, 0.68, 0, 0.08, 0.08, 0.08, GILT)
            else:  # a stone urn
                r.part("cyl", x, top + 0.1, zb, 0.4, 0.2, 0.4, stone)
                r.part("sphere", x, top + 0.5, zb, 0.7, 0.6, 0.7, stone)
                r.part("cyl", x, top + 0.86, zb, 0.6, 0.14, 0.6, _dim(stone, 1.06))
                r.part("cone", x, top + 1.08, zb, 0.36, 0.34, 0.36, _dim(stone, 0.95))


def nave_runner(r, length=12, head=True, foot=True):
    """A long crimson runner down the nave from the prop's tile toward local -X for `length` tiles: a
    gold border, gold lozenges down its middle a tile apart, and a fringe at its `head` (the door's
    end) and its `foot`. Without one, that end runs on to the tile's edge to meet the next stretch:
    a runner longer than a bake chunk is laid in stretches, each in a chunk of its own."""
    crimson, gold = (122, 28, 36), (190, 150, 70)
    x0 = T / 2 - (0.3 if head else 0.0)
    x1 = T / 2 - length * T + (0.3 if foot else 0.0)
    mid, span = (x0 + x1) / 2, x0 - x1
    r.part("cube", mid, 0.012, 0, span, 0.02, 1.6, crimson, tex="plaster")
    for side in (-1, 1):
        r.part("cube", mid, 0.024, side * 0.68, span, 0.01, 0.1, gold)
        r.part("cube", mid, 0.024, side * 0.56, span, 0.01, 0.03, gold)
    for i in range(length):
        r.part("cube", -i * T, 0.024, 0, 0.42, 0.01, 0.42, gold, ry=math.pi / 4)
        r.part("cube", -i * T, 0.03, 0, 0.22, 0.01, 0.22, (86, 30, 90), ry=math.pi / 4)
    for x, end in ((x0, head), (x1, foot)):
        if end:
            r.part("cube", x, 0.016, 0, 0.12, 0.02, 1.6, _dim(gold, 0.85))  # the fringe


def fountain(r, t, seed):
    """The market's fountain, filling its tile: an octagonal basin of pale stone brimming with water, a
    fluted shaft, an upper bowl spilling three falling streams, and a block on top carved with the
    realm's crest on all four faces."""
    stone = (236, 230, 218)  # sandstone, like the houses
    for i in range(8):  # the basin's eight sides and their coping
        a = i * math.pi / 4 + math.pi / 8
        x, z = math.cos(a) * 0.9, math.sin(a) * 0.9
        r.part("cube", x, 0.3, z, 0.2, 0.6, 0.78, stone, tex="ashlar", ry=-a)
        r.part("cube", x * 1.02, 0.63, z * 1.02, 0.3, 0.08, 0.82, _dim(stone, 1.1), ry=-a)
    r.part("cyl", 0, 0.48, 0, 1.75, 0.04, 1.75, WHITE, tex="water")  # the water
    r.part("cyl", 0, 0.05, 0, 1.9, 0.1, 1.9, _dim(stone, 0.8), tex="flagstone")  # the step
    r.part("cyl", 0, 1.0, 0, 0.32, 1.1, 0.32, stone, tex="ashlar")  # the shaft
    for i in range(6):  # its flutes
        a = i * math.pi / 3
        r.part("cube", math.cos(a) * 0.16, 1.0, math.sin(a) * 0.16, 0.04, 1.0, 0.04, _dim(stone, 0.8))
    r.part("cyl", 0, 1.55, 0, 1.0, 0.16, 1.0, stone, tex="ashlar")  # the upper bowl
    r.part("cyl", 0, 1.64, 0, 0.86, 0.03, 0.86, WHITE, tex="water")
    r.part("cube", 0, 2.05, 0, 0.42, 0.7, 0.42, _dim(stone, 1.05), tex="ashlar")  # the crest block
    r.part("cube", 0, 2.45, 0, 0.52, 0.1, 0.52, _dim(stone, 0.95))
    r.part("cyl", 0, 2.62, 0, 0.16, 0.24, 0.16, GILT)  # a gilt finial
    for i in range(2):  # through the block, so each shows on two of its faces
        with r.at(0, 2.05, 0, ry=i * math.pi / 2):
            realm_crest(r, GILT, cy=0.0, scale=0.6, through=0.46)
    for i in range(3):  # three streams from the bowl's lip, falling to the basin
        a = i * 2 * math.pi / 3 + seed
        ca, sa = math.cos(a), math.sin(a)
        r.part("cube", ca * 0.5, 1.62, sa * 0.5, 0.1, 0.06, 0.1, _dim(stone, 0.8))  # a spout
        for k in range(3):
            f = (t * 1.4 + k / 3) % 1.0
            d = 0.52 + f * 0.3
            y = 1.6 - f * f * 1.1
            r.part("sphere", ca * d, y, sa * d, 0.07, 0.11, 0.07, (160, 196, 220))
        f = (t * 0.8 + i / 3) % 1.0  # a ripple spreading where it lands
        r.part("cyl", ca * 0.82, 0.51, sa * 0.82, 0.1 + f * 0.3, 0.01, 0.1 + f * 0.3, (190, 214, 230))


def bench(r, seed):
    """A stone bench facing +X: a worn slab on two carved legs, a little moss in its joints."""
    stone = _dim((236, 230, 218), 0.95 + (seed % 3) * 0.04)
    r.part("cube", 0, 0.46, 0, 0.5, 0.1, 1.7, stone, tex="ashlar")
    for z in (-0.65, 0.65):
        r.part("cube", 0, 0.2, z, 0.42, 0.42, 0.24, _dim(stone, 0.85), tex="ashlar")
        r.part("cube", 0.12, 0.38, z, 0.18, 0.08, 0.26, _dim(stone, 0.9))  # a scrolled end
    if seed % 2:
        r.part("cube", -0.1, 0.52, 0.4, 0.3, 0.02, 0.3, (70, 100, 60))  # a cloak left on it


def cart_wheel(r, x, y, z, radius, spokes=8, wood=DARK_WOOD):
    """A spoked wheel turning about Z: an iron tyre over a rim of felloes, `spokes` spokes and a hub
    with its iron cap and linchpin."""
    for k in range(8):  # the rim, eight felloes round it, and the iron tyre over them
        a = k * math.pi / 4
        rim = radius * 0.92
        r.part("cube", x + math.cos(a) * rim, y + math.sin(a) * rim, z, radius * 0.8, 0.09, 0.1, wood,
               rz=a + math.pi / 2)  # fmt: skip
        r.part("cube", x + math.cos(a) * radius, y + math.sin(a) * radius, z, radius * 0.8, 0.03, 0.08, IRON,
               rz=a + math.pi / 2)  # fmt: skip
    for k in range(spokes // 2):  # each spoke runs through the hub to the far rim
        r.part("cube", x, y, z, radius * 1.75, 0.045, 0.045, _dim(wood, 1.2), rz=k * math.tau / spokes)
    r.part("cyl", x, y, z, radius * 0.4, 0.2, radius * 0.4, wood, rx=math.pi / 2)  # the hub
    r.part("cyl", x, y, z + math.copysign(0.11, z), radius * 0.26, 0.04, radius * 0.26, IRON, rx=math.pi / 2)


def _sack(r, x, y, z, k, rgb, ry=0.0):
    """A tied grain sack lying on its side: a plump body, a gathered neck and the cord round it."""
    r.part("sphere", x, y, z, 0.5 * k, 0.36 * k, 0.42 * k, rgb, ry=ry)
    with r.at(x, y, z, ry=ry):
        r.part("cube", 0.27 * k, 0.04 * k, 0, 0.1 * k, 0.12 * k, 0.12 * k, _dim(rgb, 0.92))
        r.part("cube", 0.24 * k, 0.04 * k, 0, 0.03, 0.13 * k, 0.13 * k, (86, 66, 40))


def _cask(r, x, y, z, length, rad, lying=True):
    """A coopered cask: a bulging belly of staves, its ends, and two iron hoops round each end."""
    turn = {"rz": math.pi / 2} if lying else {}
    with r.at(x, y, z, **turn):
        r.part("cyl", 0, 0, 0, rad * 2, length, rad * 2, WOOD, tex="wood_plank")
        r.part("cyl", 0, 0, 0, rad * 2.12, length * 0.6, rad * 2.12, _dim(WOOD, 1.05), tex="wood_plank")
        for y_ in (-0.42, -0.3, 0.3, 0.42):
            r.part("cyl", 0, y_ * length, 0, rad * 2.1, 0.035, rad * 2.1, IRON)
        r.part("cyl", 0, length * 0.5, 0, rad * 1.6, 0.02, rad * 1.6, _dim(WOOD, 0.75))  # the head


def hand_cart(r, seed):
    """A two-wheeled hand cart, its handles toward +X and its bed tipped forward onto a prop leg: plank
    sides held by stakes, a tailboard, an iron-bound axle under it on two spoked wheels, heaped with
    sacks and a crate or with a pair of casks, a coil of rope thrown over the side."""
    wood = _dim(WOOD, 0.9 + (seed % 3) * 0.05)
    r.part("cube", -0.25, 0.45, 0, 0.1, 0.1, 1.4, IRON)  # the axle
    for z in (-0.66, 0.66):
        cart_wheel(r, -0.25, 0.45, z, 0.45)
    with r.at(0, 0.72, 0, rz=0.12):  # the bed
        r.part("cube", 0, 0, 0, 1.3, 0.08, 1.0, wood, tex="wood_plank")
        for z in (-0.5, 0.5):
            r.part("cube", 0, 0.2, z, 1.3, 0.32, 0.05, wood, tex="wood_plank")  # sides
            r.part("cube", 0, 0.37, z, 1.34, 0.04, 0.07, _dim(wood, 0.8))  # their top rails
            for x in (-0.6, -0.1, 0.4):  # the stakes holding them
                r.part("cube", x, 0.18, z * 1.08, 0.06, 0.42, 0.04, DARK_WOOD)
            r.part("cube", 1.05, -0.05, z * 0.8, 0.9, 0.07, 0.07, DARK_WOOD)  # handles
            r.part("cube", 1.42, -0.05, z * 0.8, 0.16, 0.08, 0.08, _dim(DARK_WOOD, 0.75))  # worn grips
            r.part("cube", -0.25, -0.1, z * 0.8, 0.12, 0.14, 0.06, IRON)  # the axle's strap
        r.part("cube", -0.65, 0.2, 0, 0.05, 0.32, 1.0, wood, tex="wood_plank")  # the tailboard
        r.part("cube", 0.65, 0.12, 0, 0.05, 0.18, 1.0, wood, tex="wood_plank")  # the low front
        if seed % 2:
            for i, (x, z) in enumerate(((-0.3, -0.2), (0.2, 0.15), (-0.2, 0.25))):
                _sack(r, x, 0.27 + (i // 2) * 0.14, z, 1.0, _dim(SACK, 0.9 + i * 0.04), ry=i * 0.9)
            r.part(
                "cube", 0.3, 0.3, -0.22, 0.4, 0.4, 0.4, _dim(WOOD, 1.1), tex="wood_plank", ry=0.2
            )  # a crate
            r.part("cube", 0.3, 0.3, -0.22, 0.42, 0.06, 0.42, DARK_WOOD, ry=0.2)
        else:
            for z in (-0.24, 0.24):
                _cask(r, 0, 0.3, z, 0.95, 0.24)
        with r.at(0.1, 0.38, 0.52):  # a coil of rope hung over the side
            r.part("cyl", 0, -0.1, 0, 0.36, 0.05, 0.36, (150, 124, 80), rx=math.pi / 2)
            r.part("cyl", 0, -0.1, 0.02, 0.3, 0.05, 0.3, (138, 112, 72), rx=math.pi / 2)
    r.part("cube", 0.75, 0.27, 0, 0.06, 0.54, 0.06, DARK_WOOD)  # a prop leg
    r.part("cube", 0.75, 0.03, 0, 0.14, 0.06, 0.14, (110, 106, 100))  # on a flat stone


def hay_wagon(r, seed):
    """A four-wheeled farm wagon heaped with hay, its shaft tilted down to the ground toward +X: big
    spoked wheels behind and smaller ones before on their axles, a plank bed with slatted rails and
    stakes, the load roped down, a pitchfork stuck in it and a lantern on a hook at the front."""
    wood = _dim(WOOD, 0.85)
    for x, rad in ((-0.6, 0.42), (0.6, 0.34)):
        r.part("cube", x, rad, 0, 0.1, 0.1, 1.42, IRON)  # the axle
        for z in (-0.66, 0.66):
            cart_wheel(r, x, rad, z, rad)
    r.part("cube", 0, 0.68, 0, 1.6, 0.12, 0.16, DARK_WOOD)  # the reach pole joining the axles
    r.part("cube", 0, 0.8, 0, 1.9, 0.1, 1.15, wood, tex="wood_plank")  # the bed
    for z in (-0.58, 0.58):  # slatted rails and stakes
        for y in (0.98, 1.18):
            r.part("cube", 0, y, z, 1.9, 0.06, 0.05, DARK_WOOD)
        for x in (-0.9, -0.45, 0.0, 0.45, 0.9):
            r.part("cube", x, 1.04, z, 0.07, 0.5, 0.07, DARK_WOOD)
    for x in (-0.95, 0.95):  # the end boards
        r.part("cube", x, 1.04, 0, 0.06, 0.44, 1.12, wood, tex="wood_plank")
    r.part("cube", 0, 1.2, 0, 1.75, 0.6, 1.05, HAY)  # the hay
    r.part("sphere", -0.1, 1.5, 0, 1.6, 0.6, 1.0, _dim(HAY, 1.05))
    for x in (-0.45, 0.4):  # ropes thrown over the load
        r.part("cube", x, 1.62, 0, 0.04, 0.05, 1.1, (120, 96, 60))
        for z in (-0.56, 0.56):
            r.part("cube", x, 1.32, z, 0.04, 0.6, 0.04, (120, 96, 60))
    for i in range(8):  # loose wisps
        r.part("cube", -0.8 + i * 0.23, 1.62 + (i % 2) * 0.12, (i % 3 - 1) * 0.32, 0.32, 0.04, 0.05,
               _dim(HAY, 1.15), ry=i)  # fmt: skip
    with r.at(0.95, 0.62, 0, rz=-0.32):  # the shaft
        for z in (-0.3, 0.3):
            r.part("cube", 0.75, 0, z, 1.5, 0.08, 0.08, DARK_WOOD)
        r.part("cube", 1.45, 0, 0, 0.08, 0.08, 0.66, DARK_WOOD)
        r.part("cube", 0.75, 0, 0, 0.08, 0.08, 0.6, DARK_WOOD)  # a crossbar
    with r.at(0.98, 1.3, 0.5):  # a lantern on its hook at the front, unlit
        r.part("cube", 0, 0.12, 0, 0.04, 0.24, 0.04, IRON)
        r.part("cube", 0, -0.06, 0, 0.12, 0.16, 0.12, (60, 58, 56))
        r.part("cube", 0, -0.06, 0, 0.09, 0.12, 0.13, (150, 132, 96))
    if seed % 2:  # a pitchfork stuck in the hay
        with r.at(0.2, 1.75, 0.25, rx=0.4):
            r.part("cube", 0, 0, 0, 0.05, 1.2, 0.05, DARK_WOOD)
            r.part("cube", 0, -0.62, 0, 0.05, 0.05, 0.26, IRON)
            for dz in (-0.11, 0.0, 0.11):
                r.part("cube", 0, -0.75, dz, 0.03, 0.26, 0.03, IRON)
    else:  # a sack thrown up on the hay
        _sack(r, -0.4, 1.85, -0.2, 0.9, SACK, ry=0.7)


def cargo(r, seed):
    """Goods hauled up from the quay and left in a heap: tied sacks, a bale in rope-bound sacking, a
    crate stencilled with a merchant's mark, a cask or two and a fishing net heaped over a corner."""
    for i, (x, z) in enumerate(((-0.4, -0.4), (0.1, -0.5), (-0.5, 0.1))):
        _sack(r, x, 0.25, z, 1.15, _dim(SACK, 0.85 + 0.06 * ((seed + i) % 3)), ry=i * 1.1)
    _sack(r, -0.25, 0.6, -0.25, 1.0, SACK, ry=0.6)
    r.part("cube", 0.4, 0.35, 0.3, 0.8, 0.7, 0.7, (150, 128, 80), ry=0.2)  # the bale, in sacking
    with r.at(0.4, 0.35, 0.3, ry=0.2):
        for x in (-0.2, 0.2):  # its ropes, round it and across the top
            r.part("cube", x, 0, 0, 0.04, 0.74, 0.74, (86, 66, 40))
        r.part("cube", 0, 0.36, 0, 0.82, 0.03, 0.04, (86, 66, 40))
        r.part("cube", 0.41, 0.05, 0, 0.01, 0.2, 0.2, (90, 40, 34))  # a merchant's mark stencilled on it
        r.part("cube", 0.415, 0.05, 0, 0.01, 0.06, 0.26, (90, 40, 34))
    if seed % 3 == 0:
        r.part(
            "cube", -0.45, 0.25, 0.55, 0.5, 0.5, 0.5, _dim(WOOD, 1.1), tex="wood_plank", ry=-0.3
        )  # a crate
        with r.at(-0.45, 0.25, 0.55, ry=-0.3):
            for y in (-0.2, 0.2):
                r.part("cube", 0, y, 0, 0.52, 0.06, 0.52, DARK_WOOD)
    for k in range(1 + seed % 2):  # casks, stood on end
        x, z = (0.5, -0.45) if k == 0 else (-0.55, 0.6)
        _cask(r, x, 0.45, z, 0.9, 0.3, lying=False)
    for k in range(4):  # a net heaped over the corner, its floats strung along it
        r.part("cube", 0.55 + k * 0.05, 0.05 + k * 0.06, -0.85 + k * 0.08, 0.6 - k * 0.1, 0.06, 0.4,
               _dim((100, 92, 72), 1 - k * 0.06), ry=k * 0.4)  # fmt: skip
        r.part("cube", 0.4 + k * 0.12, 0.12 + k * 0.05, -0.75, 0.08, 0.06, 0.08, (170, 120, 60))


def town_statue(r, seed):
    """A statue of the realm's founder on a stepped plinth in the square: a cloaked, hooded figure in
    weathered bronze gone green, the crest's shield held before it and a sword's point resting at its
    feet, a carved band round the plinth and offerings left on its step."""
    stone = (170, 160, 140)
    bronze = (92, 120, 104) if seed % 2 == 0 else (110, 116, 96)
    dark = _dim(bronze, 0.7)
    r.part("cube", 0, 0.1, 0, 1.8, 0.2, 1.8, _dim(stone, 0.85), tex="ashlar")  # the plinth's steps
    r.part("cube", 0, 0.3, 0, 1.5, 0.2, 1.5, _dim(stone, 0.92), tex="ashlar")
    r.part("cube", 0, 0.85, 0, 1.1, 0.9, 1.1, stone, tex="ashlar")  # its die
    r.part("cube", 0, 1.33, 0, 1.24, 0.1, 1.24, _dim(stone, 1.05))  # the cornice
    r.part("cube", 0, 0.62, 0, 1.13, 0.08, 1.13, _dim(stone, 0.8))  # a carved band
    r.part("cube", 0.56, 0.9, 0, 0.02, 0.36, 0.6, _dim(stone, 0.75))  # the inscription's panel
    for k in range(3):  # its lines of letters, worn shallow
        r.part("cube", 0.57, 1.0 - k * 0.1, 0, 0.01, 0.03, 0.46 - k * 0.08, _dim(stone, 0.6))
    with r.at(0, 1.38, 0):
        for z in (-0.13, 0.13):  # feet and legs under the robe
            r.part("cube", 0.12, 0.05, z, 0.24, 0.1, 0.14, dark)
        r.part("frustum", 0, 0.6, 0, 0.72, 1.2, 0.72, bronze)  # the robe, falling in folds
        for k in range(5):  # the folds
            a = -0.9 + k * 0.45
            r.part("cube", math.cos(a) * 0.3, 0.55, math.sin(a) * 0.3, 0.06, 1.0, 0.06, dark, ry=-a, rz=0.08)
        r.part("cube", -0.05, 1.45, 0, 0.42, 0.55, 0.62, bronze)  # the chest and shoulders
        r.part("cube", -0.22, 0.95, 0, 0.12, 1.5, 0.82, dark, rz=-0.08)  # the cloak behind
        r.part("cube", -0.05, 1.74, 0, 0.5, 0.1, 0.78, _dim(bronze, 0.9))  # its mantle over the shoulders
        r.part("frustum", 0.0, 1.98, 0, 0.32, 0.38, 0.3, bronze)  # the hood
        r.part("cube", 0.12, 1.94, 0, 0.06, 0.24, 0.18, _dim(bronze, 0.4))  # the face in its shadow
        for z in (-1, 1):  # the arms, both hands on the shield's top
            r.part("cube", 0.12, 1.4, z * 0.3, 0.14, 0.4, 0.14, bronze, rz=0.6)
        with r.at(0.34, 1.05, 0):  # the shield stood before it, the crest raised on its face
            r.part("cube", 0, 0.1, 0, 0.06, 0.5, 0.5, bronze)
            r.part("cube", 0, -0.22, 0, 0.06, 0.3, 0.3, bronze, rx=math.pi / 4)
            realm_crest(r, _dim(bronze, 1.25), cy=0.05, scale=0.62)
        r.part("cube", 0.48, 0.2, 0.26, 0.04, 0.5, 0.06, dark)  # the sword, point down by its feet
        r.part("cube", 0.48, 0.5, 0.26, 0.04, 0.04, 0.2, dark)
    r.part("cube", 0.8, 0.44, 0.3, 0.12, 0.08, 0.12, (150, 80, 60))  # offerings on the step: a pot,
    r.part("cube", 0.8, 0.43, -0.25, 0.08, 0.06, 0.24, (180, 170, 120))  # a sheaf of wheat


def fence(r, seed):
    """A wattle hurdle running across the tile along Z: stout stakes driven in a row, withies woven in
    and out between them, and a split capping rail along the top."""
    withy = (128, 100, 66)
    stakes = (-0.9, -0.45, 0.0, 0.45, 0.9)
    for z in stakes:
        r.part("cube", 0, 0.55, z, 0.1, 1.1, 0.1, DARK_WOOD)
    for row in range(6):  # each withy passes before one stake and behind the next
        y = 0.22 + row * 0.13
        for i in range(len(stakes) - 1):
            side = 0.035 if (row + i) % 2 else -0.035
            z = (stakes[i] + stakes[i + 1]) / 2
            r.part("cube", side, y, z, 0.05, 0.1, 0.47, _dim(withy, 0.86 + 0.07 * ((seed + row + i) % 3)),
                   rx=0.06 * side / 0.035)  # fmt: skip
    r.part("cube", 0, 1.06, 0, 0.12, 0.07, 2.0, _dim(WOOD, 0.85), rx=0.015 * (seed % 3))


def lamp_post(r, t):
    """A squared oak post on a stone foot, a wrought-iron bracket with a scrolled brace reaching out from
    its head and a lantern of horn panes hung from it, burning under a pointed iron cap."""
    iron = (40, 38, 40)
    r.part("cube", 0, 0.15, 0, 0.44, 0.3, 0.44, (96, 92, 86), tex="ashlar")  # the stone foot
    r.part("cube", 0, 1.55, 0, 0.18, 2.6, 0.18, OAK, tex="wood_plank")  # the post
    r.part("cube", 0, 2.88, 0, 0.24, 0.1, 0.24, _dim(OAK, 0.8))  # its cap
    r.part("cube", 0.24, 2.8, 0, 0.5, 0.05, 0.05, iron)  # the bracket's arm
    _bar(r, (0.1, 2.35, 0), (0.36, 2.78, 0), 0.04, iron)  # its brace
    r.part("cyl", 0.2, 2.62, 0, 0.14, 0.03, 0.14, iron, rx=math.pi / 2)  # a scroll in the brace
    r.part("cube", 0.48, 2.86, 0, 0.04, 0.1, 0.04, iron)  # a finial curling up at its end
    with r.at(0.4, 2.55, 0):
        r.part("cube", 0, 0.22, 0, 0.02, 0.1, 0.02, iron)  # the hook
        r.part("cube", 0, -0.19, 0, 0.24, 0.04, 0.24, iron)  # the base
        r.part("cube", 0, 0, 0, 0.2, 0.32, 0.2, (230, 170, 90), glow=True)  # the horn panes, lit
        for dx in (-0.11, 0.11):  # the corner rods
            for dz in (-0.11, 0.11):
                r.part("cube", dx, 0, dz, 0.03, 0.36, 0.03, iron)
        r.part("cone", 0, 0.28, 0, 0.32, 0.22, 0.32, iron)  # the pointed cap
        r.part("sphere", 0, 0.42, 0, 0.05, 0.05, 0.05, iron)
        _flame(r, 0, -0.02, 0, 0.06, t)


def boat(r, t, seed):
    """A small clinker-built fishing boat riding at its mooring, bow toward +X, a furled sail."""
    bob = math.sin(t * 1.2 + seed) * 0.05
    with r.at(0, bob + 0.1, 0, rx=math.sin(t * 0.9 + seed) * 0.04):  # riding on the surface
        r.part("cube", 0, 0.3, 0, 3.0, 0.5, 1.3, WOOD, tex="wood_plank")  # hull
        r.part("cube", 0, 0.08, 0, 2.6, 0.2, 0.9, DARK_WOOD)  # keel side
        r.part("wedge", 1.9, 0.3, 0, 1.3, 0.8, 0.5, WOOD, tex="wood_plank", rz=-math.pi / 2)  # bow
        r.part("cube", -1.55, 0.35, 0, 0.12, 0.6, 1.3, DARK_WOOD)  # transom
        for z in (-0.66, 0.66):
            r.part("cube", 0, 0.58, z, 3.0, 0.06, 0.08, DARK_WOOD)  # gunwales
        r.part("cube", 0.4, 0.5, 0, 0.3, 0.06, 1.2, DARK_WOOD)  # a thwart
        r.part("cyl", 0.4, 1.9, 0, 0.1, 2.8, 0.1, DARK_WOOD)  # mast
        r.part("cube", -0.3, 1.0, 0, 1.6, 0.18, 0.18, (190, 180, 150))  # furled sail on the boom
        r.part("cube", -0.8, 0.6, 0.3, 0.4, 0.12, 0.3, (120, 90, 60))  # coiled rope


# Trees of a gloomy hill town: slim cypresses, flat-crowned umbrella pines and gnarled olives, all in
# the same dark, muted green on the same dark bark.
# Each is a 3D trunk and limbs under leaf cards: thin slabs carrying the cut-out `leaf_card` spray,
# crossed in clumps so the crown has body from any side and gaps you can see the sky through. Trees
# never move, so they are baked with the town's other static props (`world.STATIC_PROPS`).
TREE_LEAF = (52, 72, 50)
TREE_BARK = (88, 76, 64)
TREE_KINDS = ("olive", "cypress", "pine")
CARD = 0.02  # a leaf card's thickness


def _limb(r, x0, y0, z0, x1, y1, z1, w, rgb, tex="bark"):
    """A round limb from (x0, y0, z0) to (x1, y1, z1), `w` thick."""
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    tilt = math.atan2(math.hypot(dx, dz), dy)
    with r.at((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, ry=-math.atan2(dz, dx), rz=-tilt):
        r.part("cyl", 0, 0, 0, w, length + w * 0.5, w, rgb, tex=tex)  # a little long, to close the joints


def _bough(r, points, w0, w1, rgb):
    """A limb through `points`, tapering from `w0` thick to `w1`."""
    last = len(points) - 2
    for k, (a, b) in enumerate(itertools.pairwise(points)):
        _limb(r, *a, *b, w0 + (w1 - w0) * (k / last if last else 0.0), rgb)


def _card(r, x, y, z, w, h, rgb, ry=0.0, rx=0.0, rz=0.0):
    """One leaf card, `w` wide and `h` tall, facing along Z before it is turned."""
    r.part("cube", x, y, z, w, h, CARD, rgb, tex="leaf_card", rx=rx, ry=ry, rz=rz)


def _clump(r, x, y, z, w, h, rgb, turn, cards=3):
    """A clump of leaves: `cards` upright cards crossed about its centre, capped by a flat one so it
    still looks full from below and above."""
    for k in range(cards):
        _card(r, x, y, z, w, h, _dim(rgb, 0.92 + 0.08 * k), ry=turn + k * math.pi / cards)
    _card(r, x, y + h * 0.1, z, w * 0.9, w * 0.9, _dim(rgb, 1.08), ry=turn + 0.4, rx=math.pi / 2)


def cypress(r, seed, t=0.0, near=True):
    """A tall, slim cypress: a straight trunk in a dense spindle of dark foliage, widest a third of the
    way up and drawn to a flame-like point."""
    h = 7.8 + (seed % 3) * 0.6
    leaf = TREE_LEAF
    bark = TREE_BARK
    _bough(r, [(0, 0.1, 0), (0, 1.4, 0), (0.04, h * 0.55, 0), (0, h * 0.85, 0)], 0.3, 0.08, bark)
    tiers = 9 if near else 5
    for k in range(tiers):
        u = k / (tiers - 1)  # 0 at the bottom of the spindle, 1 at its tip
        y = 1.3 + u * (h - 2.3)
        w = 1.5 * math.sin(math.pi * (0.22 + 0.78 * u)) ** 0.8 * (1.0 - 0.35 * u) + 0.2
        tall = (h - 1.8) / tiers * 2.2
        off = 0.06 * math.sin(seed * 2.3 + k * 1.9)
        _clump(r, off, y, -off, w, tall, _dim(leaf, 0.9 + 0.05 * (k % 3)), seed * 0.7 + k * 0.9)
    for k in range(2):  # the pointed tip
        _card(r, 0, h - 0.4, 0, 0.45, 1.3, _dim(leaf, 1.05), ry=seed + k * math.pi / 2)


def umbrella_pine(r, seed, t=0.0, near=True):
    """A stone pine: a tall, leaning bare trunk forking into bare limbs under a broad, flat crown."""
    h = 5.9 + (seed % 3) * 0.5
    yaw = seed * 1.3
    lean = 0.08 + (seed % 2) * 0.06
    lx, lz = math.cos(yaw) * h * lean, math.sin(yaw) * h * lean  # where the leaning trunk forks
    fork = h * 0.68
    bend = (lx * 0.3 - lz * 0.1, fork * 0.5, lz * 0.3 + lx * 0.1)  # a gentle S in the trunk
    _bough(r, [(0, 0.16, 0), bend, (lx, fork, lz)], 0.44, 0.32, TREE_BARK)  # straight from the ground
    limbs = 4 if near else 3
    tips = []
    for k in range(limbs):
        a = yaw + 0.5 + k * math.tau / limbs
        d = 1.5 + 0.4 * ((k + seed) % 2)
        tip = (lx + math.cos(a) * d, h - 0.45, lz + math.sin(a) * d)
        mid = (lx + math.cos(a + 0.3) * d * 0.45, fork + (h - fork) * 0.55, lz + math.sin(a + 0.3) * d * 0.45)
        _bough(r, [(lx, fork - 0.15, lz), mid, tip], 0.22, 0.12, TREE_BARK)
        tips.append(tip)
    # The crown: a flat roof of clumps over the limbs' ends and between them, under a broad cap.
    under = _dim(TREE_LEAF, 0.8)
    _clump(r, lx, h - 0.05, lz, 3.0, 1.0, TREE_LEAF, yaw)
    for k, (tx, ty, tz) in enumerate(tips):
        _clump(r, tx, ty + 0.35, tz, 2.6, 0.95, _dim(TREE_LEAF, 0.9 + 0.06 * (k % 3)), yaw + k)
    if near:
        for k in range(limbs):  # between the limbs, so the rim reads round
            a = yaw + 0.5 + (k + 0.5) * math.tau / limbs
            _clump(r, lx + math.cos(a) * 1.9, h - 0.2, lz + math.sin(a) * 1.9, 2.0, 0.8, under, a)
    _card(r, lx, h + 0.25, lz, 4.6, 4.2, _dim(TREE_LEAF, 1.1), ry=yaw, rx=math.pi / 2)
    _card(r, lx, h - 0.3, lz, 4.2, 3.8, under, ry=yaw + 0.8, rx=math.pi / 2)


def olive(r, seed, t=0.0, near=True):
    """An old olive: a short, split and twisted trunk under a ragged crown of silvery clumps."""
    h = 3.2 + (seed % 3) * 0.3
    yaw = seed * 0.9
    _limb(r, 0, 0.1, 0, 0, 0.5, 0, 0.42, TREE_BARK)  # a short thick bole, straight from the ground
    stems = 3
    tips = []
    for k in range(stems):
        a = yaw + k * math.tau / stems
        mx, mz = math.cos(a + 0.7) * 0.3, math.sin(a + 0.7) * 0.3  # each stem twists as it climbs
        tx, tz = math.cos(a) * 0.9, math.sin(a) * 0.9
        _bough(r, [(0, 0.4, 0), (mx, 1.2, mz), (tx, h * 0.72, tz)], 0.3, 0.18, TREE_BARK)
        if near:  # a twig off each stem, reaching out
            b = a + 0.9
            _bough(
                r,
                [(tx, h * 0.72, tz), (tx + math.cos(b) * 0.7, h * 0.85, tz + math.sin(b) * 0.7)],
                0.12,
                0.08,
                TREE_BARK,
            )
        tips.append((tx, tz))
    clumps = 8 if near else 4
    for k in range(clumps):
        a = yaw + k * math.tau / clumps + 0.3
        d = 0.8 + ((k + seed) % 3) * 0.3
        s = 1.4 + ((k * 7 + seed) % 3) * 0.25
        y = h * 0.8 + ((k + seed) % 2) * 0.45
        shade = 0.88 + ((k + seed) % 3) * 0.08
        _clump(r, math.cos(a) * d, y, math.sin(a) * d, s, s * 0.8, _dim(TREE_LEAF, shade), a)
    _clump(r, 0, h + 0.3, 0, 2.0, 1.2, _dim(TREE_LEAF, 1.05), yaw)


DEAD_BARK = (78, 74, 70)  # bleached grey by ash and weather


def dead_tree(r, seed, t=0.0, near=True):
    """A dead tree of the cemetery: a split, leaning trunk and bare, crooked limbs clawing at the sky,
    the bark long gone grey. Never a leaf on it."""
    h = 3.6 + (seed % 3) * 0.4
    yaw = seed * 1.3
    lean = 0.35
    top = (math.cos(yaw) * lean, h * 0.62, math.sin(yaw) * lean)
    _bough(r, [(0, 0.0, 0), (0.05, h * 0.3, -0.05), top], 0.42, 0.26, DEAD_BARK)
    for k in range(3):  # the roots, gripping the ground
        a = yaw + k * math.tau / 3 + 0.5
        _limb(r, 0, 0.2, 0, math.cos(a) * 0.6, 0.02, math.sin(a) * 0.6, 0.14, DEAD_BARK)
    limbs = 4 if near else 2
    for k in range(limbs):
        a = yaw + k * math.tau / limbs + 0.4
        bend = a + (0.8 if k % 2 else -0.8)
        y0 = h * (0.45 + 0.08 * k)
        mid = (top[0] + math.cos(a) * 0.8, y0 + 0.7, top[2] + math.sin(a) * 0.8)
        tip = (mid[0] + math.cos(bend) * 0.7, mid[1] + 0.5 + 0.2 * (k % 2), mid[2] + math.sin(bend) * 0.7)
        _bough(r, [(top[0], y0, top[2]), mid, tip], 0.16, 0.06, DEAD_BARK)
        if near:  # a twig off each, crooked like a finger
            twig = (tip[0] + math.cos(a) * 0.35, tip[1] - 0.15, tip[2] + math.sin(a) * 0.35)
            _limb(r, *tip, *twig, 0.04, _dim(DEAD_BARK, 0.9))
    _bough(
        r,
        [top, (top[0] - 0.1, h * 0.95, top[2] + 0.1), (top[0], h * 1.1, top[2] - 0.2)],
        0.2,
        0.06,
        DEAD_BARK,
    )


def town_tree(r, kind, seed, t=0.0, near=True):
    """A tree by `kind`: one of the town's (`TREE_KINDS`) or the cemetery's `dead` one; far ones drop
    some limbs and clumps."""
    {"cypress": cypress, "pine": umbrella_pine, "olive": olive, "dead": dead_tree}[kind](r, seed, t, near)


RAMPART_STONE = (236, 230, 220)  # pale, under the rough stone's grain, like the wall it dresses
RAMPART_SHADOW = _dim(RAMPART_STONE, 0.42)  # the depth of a blind arch


def rampart_bay(r, kind, height, seed):
    """One 2 m bay of the town's great wall, carved onto its face (the plane x=0, facing +X, the
    ground at y=0, the wall's top at `height`): a stepped plinth, a corbel table under a parapet with
    two merlons on the wall top, and either a `pier` (a cluster of three engaged columns rising to a
    moulded capital) or an `arch` (a tall blind round-headed arch, a deep shadow within its jambs and
    voussoirs, a round oculus over every other one). Nothing stands out more than 0.4 m, so you walk
    along it as along the bare wall."""
    stone = RAMPART_STONE
    light, dark = _dim(stone, 1.08), _dim(stone, 0.82)
    h = height
    r.part("cube", 0, 0.45, 0, 0.5, 0.9, T, dark, tex="rough_stone")  # the plinth
    r.part("cube", 0, 1.05, 0, 0.3, 0.3, T, stone, tex="rough_stone")  # its upper course
    for z in (-0.66, 0.0, 0.66):  # the corbel table
        r.part("cube", 0, h - 0.95, z, 0.56, 0.3, 0.24, light, tex="rough_stone")
        r.part("cube", 0, h - 1.18, z, 0.34, 0.18, 0.18, dark, tex="rough_stone")  # its lower step
    r.part("cube", 0, h - 0.62, 0, 0.7, 0.36, T, stone, tex="rough_stone")  # the parapet's lip
    r.part("cube", -0.1, h + 0.18, 0, 0.9, 0.36, T, stone, tex="rough_stone")  # the breastwork
    for z in (-0.5, 0.5):  # merlons
        r.part("cube", -0.1, h + 0.72, z, 0.9, 0.72, 0.55, stone, tex="rough_stone")
    spring = max(h * 0.6, 2.6)
    if kind == "pier":
        _rampart_pier(r, h, stone, light, dark)
    else:
        _rampart_arch(r, h, spring, seed, stone, light, dark)


def _rampart_pier(r, h, stone, light, dark):
    """Three engaged columns on a deep base, the middle one broadest, their fillets in shadow."""
    top = h - 1.15
    r.part("cube", 0, 0.75, 0, 0.8, 1.5, 1.5, dark, tex="rough_stone")  # the base
    r.part("cube", 0, 1.56, 0, 0.7, 0.12, 1.4, light, tex="rough_stone")  # its torus
    span = top - 1.62
    mid = 1.62 + span / 2
    r.part("cyl", 0, mid, 0, 0.64, span, 0.64, light, tex="rough_stone")
    for z in (-0.42, 0.42):
        r.part("cyl", -0.04, mid, z, 0.44, span, 0.44, stone, tex="rough_stone")
        r.part("cube", 0.14, mid, z * 0.62, 0.06, span, 0.05, RAMPART_SHADOW)  # the fillet between
    r.part("cube", 0, top + 0.08, 0, 0.74, 0.16, 1.44, light, tex="rough_stone")  # the capital
    r.part("sphere", 0.1, top - 0.04, 0, 0.5, 0.26, 0.5, light, tex="rough_stone")  # its cushion
    r.part("cube", 0, top * 0.6, 0, 0.72, 0.16, 1.42, stone, tex="rough_stone")  # a band round the cluster


def _rampart_arch(r, h, spring, seed, stone, light, dark):
    """A tall blind arch: its shadowed recess, jambs, imposts, a ring of voussoirs with a keystone,
    a sill, and an oculus over it where the wall has room."""
    half = 0.62
    sill = 1.2
    rise = spring - sill
    r.part("cube", 0.01, sill + rise / 2, 0, 0.04, rise, half * 2, RAMPART_SHADOW)  # the recess
    for k in range(4):  # its round head, in slices
        y0 = k * half / 4
        w = 2 * math.sqrt(max(half * half - (y0 + half / 8) ** 2, 0.0))
        r.part("cube", 0.01, spring + y0 + half / 8, 0, 0.04, half / 4 + 0.01, w, RAMPART_SHADOW)
    r.part("cube", 0, sill, 0, 0.36, 0.14, half * 2 + 0.3, light, tex="rough_stone")  # the sill
    for s in (-1, 1):
        z = s * (half + 0.12)
        r.part("cube", 0, sill + rise / 2, z, 0.36, rise, 0.24, stone, tex="rough_stone")  # a jamb
        r.part("cube", 0, spring, z + s * 0.04, 0.44, 0.16, 0.34, light, tex="rough_stone")  # its impost
        r.part(
            "cube", 0, spring, s * 0.84, 0.24, 0.18, 0.32, light, tex="rough_stone"
        )  # the string course, out to the piers
    ring = half + 0.12
    n = 9
    for i in range(n):
        a = i * math.pi / (n - 1)
        key = i == n // 2
        r.part(
            "cube",
            0,
            spring + math.sin(a) * ring,
            math.cos(a) * ring,
            0.44 if key else 0.36,
            0.2,
            0.36 if key else 0.26,
            light if key else stone,
            tex="rough_stone",
            rx=-a,
        )
    room = h - 1.25 - (spring + ring + 0.15)
    if seed % 2 == 0 and room > 0.75:
        y = spring + ring + 0.15 + room / 2
        d = min(room * 0.8, 0.7)
        r.part(
            "cyl", 0, y, 0, d + 0.18, 0.3, d + 0.18, stone, rz=math.pi / 2, tex="rough_stone"
        )  # the oculus's ring
        r.part("cyl", 0.02, y, 0, d, 0.3, d, RAMPART_SHADOW, rz=math.pi / 2)


# --- The tradesfolk's furnishings: the smith's racks and stands, the swordmaster's katana stands, the
# scroll-seller's bookcases and the drawers in every home (the apothecary's of many small ones). All
# static, baked with the rest (`world.STATIC_PROPS`); the wall rack hangs at local -X, the others stand
# with their backs to -X and face +X, into the room.

LACQUER = (34, 26, 30)
LACQUER_RED = (118, 32, 30)
BRASS = (176, 146, 74)
BOOK_CLOTH = (
    (110, 44, 40), (52, 70, 104), (70, 92, 58), (124, 96, 52), (84, 54, 88), (140, 120, 92), (60, 50, 44),
)  # fmt: skip
PARCHMENT = (206, 190, 150)
# What each smith's rack hangs, left to right (turned by its seed): one-handers he forged and sells.
RACK_WEAPONS = ("bastard_sword", "hatchet", "war_hammer", "rusted_sword", "mace", "bearded_axe")
STAND_ARMOR = ("brigandine", "ringmail", "lamellar_vest", "blackened_plate")
STAND_GLOVES = ("iron_gauntlets", "chain_mitts", "leather_gloves")
STAND_SHIELDS = ("kite_shield", "round_shield", "buckler")


def weapon_rack(r, seed):
    """A smith's display board on the wall behind (-X): a plank backing on two battens, an iron rail
    with hooks, and four of his weapons hung upright from it, their flats to the room, under a little
    shelf with a whetstone and a coil of leather."""
    r.part("cube", -0.94, 1.55, 0, 0.06, 1.7, 1.56, WOOD, tex="wood_plank")
    for z in (-0.72, 0.72):
        r.part("cube", -0.9, 1.55, z, 0.06, 1.76, 0.1, DARK_WOOD)  # the battens
    r.part("cube", -0.86, 2.15, 0, 0.04, 0.05, 1.5, IRON)  # the rail
    r.part("cube", -0.78, 2.46, 0, 0.26, 0.05, 1.56, DARK_WOOD)  # the shelf on top
    r.part("cube", -0.78, 2.53, -0.4, 0.12, 0.08, 0.34, (96, 98, 104))  # a whetstone
    r.part("cyl", -0.78, 2.53, 0.38, 0.22, 0.08, 0.22, (90, 62, 40))  # a coil of leather
    picks = [RACK_WEAPONS[(seed + i) % len(RACK_WEAPONS)] for i in range(4)]
    for i, item_id in enumerate(picks):
        z = -0.54 + i * 0.36
        r.part("cube", -0.83, 2.12, z, 0.08, 0.04, 0.04, IRON)  # its hook
        lift = 0.95 if item_id in SWORDS else 1.3  # a blade hangs from its guard, a haft lower
        with r.at(-0.8, lift, z, s=0.85):
            _weapon(r, item_id)  # built with its flats to X: they face the room


def armor_stand(r, seed):
    """A wooden armour stand on a cross foot: a post and a shoulder bar wearing a coat of the smith's
    making, a helm on the post's head, a pair of gauntlets hung from the bar's ends and a shield
    leaning on its foot."""
    for ry in (0.0, math.pi / 2):
        r.part("cube", 0, 0.06, 0, 0.9, 0.1, 0.12, DARK_WOOD, ry=ry)  # the cross foot
    r.part("cube", 0, 0.85, 0, 0.1, 1.6, 0.1, WOOD)  # the post
    r.part("cube", 0, 1.58, 0, 0.1, 0.08, 0.92, WOOD)  # the shoulder bar
    with r.at(0, 1.22, 0, s=0.95):
        garment(r, STAND_ARMOR[seed % len(STAND_ARMOR)])
    # The helm: a kettle of iron with a brim, on the post's head.
    r.part("cyl", 0, 1.68, 0, 0.12, 0.1, 0.12, DARK_WOOD)
    r.part("sphere", 0, 1.86, 0, 0.36, 0.34, 0.36, (112, 112, 120))
    r.part("cyl", 0, 1.8, 0, 0.5, 0.03, 0.5, (96, 96, 104))  # its brim
    r.part("cube", 0.17, 1.82, 0, 0.03, 0.05, 0.2, (40, 40, 44))  # the eye slit's shadow
    gloves = STAND_GLOVES[seed % len(STAND_GLOVES)]
    for z in (-0.44, 0.44):
        with r.at(0, 1.36, z, rx=math.pi, s=0.5):  # hung by the cuff, fingers down
            gauntlet(r, gloves)
    with r.at(0.34, 0.5, 0.1, rz=-0.2, s=0.6):  # leaning back against the foot
        shield(r, STAND_SHIELDS[seed % len(STAND_SHIELDS)])


def katana_stand(r, seed):
    """A swordmaster's katana stand of black lacquer, red-lined: two curved uprights on a plinth with
    three tiers of arms, a sword resting in each, edge up and hilt to the left; the top one a long
    nodachi. A folded cloth and an oil flask lie on the plinth."""
    r.part("cube", 0, 0.08, 0, 0.5, 0.16, 1.5, LACQUER)  # the plinth
    r.part("cube", 0, 0.165, 0, 0.52, 0.02, 1.52, LACQUER_RED)  # its red lip
    for z in (-0.5, 0.5):
        r.part("cube", -0.08, 0.6, z, 0.12, 0.9, 0.1, LACQUER)  # the uprights
        r.part("cube", -0.04, 1.08, z, 0.22, 0.06, 0.14, LACQUER, rz=0.25)  # each a curling cap
        for y in (0.42, 0.7, 0.98):  # the arms, notched to cradle a blade
            r.part("cube", 0.04, y, z, 0.24, 0.05, 0.08, LACQUER)
            r.part("cube", 0.15, y + 0.04, z, 0.03, 0.06, 0.08, LACQUER_RED)
    blades = ("katana", "moonless_tachi", "nodachi")
    order = [blades[(seed + i) % 2] for i in range(2)] + ["nodachi"]
    for y, item_id in zip((0.47, 0.75, 1.03), order, strict=True):
        long = item_id == "nodachi"
        with r.at(0.06, y, -0.66 if long else -0.5, rx=math.pi / 2, s=0.82 if long else 1.0):
            katana(r, item_id)  # the hilt to -Z, the blade along +Z, the edge turned up
    r.part("cube", 0.12, 0.2, 0.42, 0.22, 0.04, 0.3, (200, 196, 184))  # a folded cloth
    r.part("cyl", 0.12, 0.25, -0.5, 0.08, 0.14, 0.08, (130, 110, 70))  # a flask of oil


def bookcase(r, seed, scrolls=False):
    """A tall bookcase with its back to the wall (-X): four shelves of books, spines out in every
    colour, some leaning, one lying flat, a few loose papers; or, `scrolls`, a rack of pigeonholes, a
    rolled scroll's end showing in most, tied with a ribbon."""
    r.part("cube", -0.5, 1.1, 0, 0.06, 2.2, 1.5, DARK_WOOD, tex="wood_plank")  # the back
    for z in (-0.74, 0.74):
        r.part("cube", -0.25, 1.1, z, 0.56, 2.2, 0.06, WOOD, tex="wood_plank")  # the sides
    r.part("cube", -0.22, 2.24, 0, 0.66, 0.08, 1.6, DARK_WOOD)  # the cornice
    r.part("cube", -0.25, 0.06, 0, 0.56, 0.12, 1.48, DARK_WOOD)  # the plinth
    shelves = (0.12, 0.64, 1.16, 1.68)
    for y in shelves[1:]:
        r.part("cube", -0.25, y, 0, 0.54, 0.04, 1.44, WOOD, tex="wood_plank")
    if scrolls:
        for z in (-0.37, 0.0, 0.37):  # the pigeonholes' partitions
            r.part("cube", -0.25, 1.1, z, 0.52, 2.04, 0.03, WOOD)
        for row, y in enumerate(shelves):
            for col in range(4):
                if (seed + row * 3 + col) % 5 == 4:
                    continue  # an empty hole
                zc = -0.555 + col * 0.37
                for k in range(3 if (row + col) % 2 else 2):  # a little stack of rolls
                    yy = y + 0.1 + (0.13 if k == 2 else 0.0)
                    zz = zc + (0.0 if k == 2 else (k - 0.5) * 0.14)
                    shade = _dim(PARCHMENT, 0.82 + 0.06 * ((seed + row + col + k) % 3))
                    r.part("cyl", -0.18, yy, zz, 0.13, 0.5, 0.13, shade, rz=math.pi / 2)
                    r.part("cyl", 0.08, yy, zz, 0.06, 0.02, 0.06, _dim(shade, 0.7), rz=math.pi / 2)
                ribbon = CLOTH[(seed + row + col) % len(CLOTH)]
                r.part("cube", -0.02, y + 0.1, zc, 0.02, 0.14, 0.03, ribbon)  # a ribbon hanging from one
        return
    for row, y in enumerate(shelves):
        z = -0.68
        i = seed * 7 + row * 5
        while z < 0.6:
            i += 1
            w = 0.05 + (i * 37 % 5) * 0.015
            h = 0.3 + (i * 13 % 4) * 0.045
            rgb = BOOK_CLOTH[i % len(BOOK_CLOTH)]
            if i % 11 == 3:  # one lying flat, a small pile
                for k in range(2):
                    r.part(
                        "cube", -0.2, y + 0.05 + k * 0.06, z + 0.13, 0.32, 0.06, 0.26, BOOK_CLOTH[(i + k) % 7]
                    )
                z += 0.3
                continue
            lean = 0.22 if i % 9 == 5 else 0.0
            r.part("cube", -0.22, y + 0.02 + h / 2, z + w / 2, 0.34, h, w, rgb, rx=lean)
            r.part("cube", -0.05, y + 0.02 + h * 0.75, z + w / 2, 0.01, 0.03, w + 0.004, GILT)  # its band
            z += w + (0.08 if lean else 0.008)
    r.part("cube", -0.1, 1.72, 0.5, 0.22, 0.01, 0.3, PARCHMENT, ry=0.3)  # loose papers on a shelf


def drawers(r, seed, apothecary=False):
    """A chest of drawers with its back to the wall (-X): three drawers on bracket feet with brass
    pulls, the middle one ajar on folded linen, and on top a candle stub, a jug or a little box; or,
    `apothecary`, a tall cabinet of many small drawers, each with a label and a ring pull, jars, a
    mortar and drying herbs on top."""
    body = _dim(WOOD, 0.95 + (seed % 3) * 0.05)
    if apothecary:
        r.part("cube", -0.3, 0.85, 0, 0.6, 1.6, 1.4, body, tex="wood_plank")
        r.part("cube", -0.28, 1.68, 0, 0.66, 0.06, 1.48, DARK_WOOD)
        for row in range(5):
            for col in range(4):
                y, z = 0.2 + row * 0.3, -0.495 + col * 0.33
                out = 0.06 if (seed + row * 4 + col) % 9 == 2 else 0.0  # one pulled out a little
                r.part("cube", 0.01 + out, y + 0.12, z, 0.03, 0.26, 0.3, DARK_WOOD, tex="door_wood")
                r.part("cube", 0.03 + out, y + 0.17, z, 0.01, 0.05, 0.12, PARCHMENT)  # its label
                r.part("cyl", 0.04 + out, y + 0.08, z, 0.05, 0.02, 0.05, BRASS, rz=math.pi / 2)
        for i, z in enumerate((-0.5, -0.25, 0.05)):  # jars of remedies
            rgb = ((90, 120, 80), (150, 60, 50), (110, 100, 140))[(seed + i) % 3]
            r.part("cyl", -0.3, 1.82, z, 0.16, 0.22, 0.16, rgb)
            r.part("cyl", -0.3, 1.95, z, 0.12, 0.04, 0.12, (140, 120, 90))  # a stopper
        r.part("frustum", -0.3, 1.77, 0.42, 0.26, 0.14, 0.26, PALE_STONE)  # the mortar
        r.part("cube", -0.25, 1.82, 0.48, 0.04, 0.24, 0.04, PALE_STONE, rz=0.5)  # its pestle
        for z in (-0.4, 0.3):  # bunches of herbs hung from the top to dry
            r.part("cube", -0.04, 1.5, z, 0.06, 0.26, 0.12, (100, 128, 70), rx=0.15)
        return
    for z in (-0.68, 0.68):
        for x in (-0.55, 0.05):
            r.part("cube", x, 0.06, z, 0.1, 0.12, 0.1, DARK_WOOD)  # bracket feet
    r.part("cube", -0.25, 0.56, 0, 0.6, 0.88, 1.4, body, tex="wood_plank")
    r.part("cube", -0.24, 1.02, 0, 0.66, 0.05, 1.48, DARK_WOOD)  # the top
    for k, y in enumerate((0.3, 0.57, 0.84)):
        out = 0.18 if k == 1 and seed % 2 else 0.0
        r.part("cube", 0.06 + out, y, 0, 0.03, 0.22, 1.28, DARK_WOOD, tex="door_wood")
        for z in (-0.36, 0.36):
            r.part("cube", 0.09 + out, y, z, 0.03, 0.04, 0.12, BRASS)  # its pulls
        if out:
            r.part("cube", 0.02, y + 0.08, 0, 0.18, 0.06, 1.1, (206, 200, 186))  # linen inside
    top = seed % 3
    if top == 0:  # a candle stub in a dish
        r.part("cyl", -0.3, 1.07, 0.4, 0.2, 0.03, 0.2, BRASS)
        r.part("cyl", -0.3, 1.14, 0.4, 0.06, 0.12, 0.06, (226, 216, 190))
    elif top == 1:  # a jug and a cup
        r.part("cyl", -0.3, 1.18, -0.35, 0.18, 0.26, 0.18, (150, 110, 80))
        r.part("cyl", -0.3, 1.1, -0.1, 0.1, 0.1, 0.1, (190, 180, 160))
    else:  # a little carved box
        r.part("cube", -0.3, 1.11, 0.25, 0.22, 0.12, 0.34, DARK_WOOD)
        r.part("cube", -0.2, 1.11, 0.25, 0.01, 0.04, 0.06, BRASS)
    r.part("cube", -0.3, 1.06, -0.1 if top != 1 else 0.4, 0.3, 0.02, 0.4, (180, 168, 140), ry=0.2)  # a cloth


# --- the redesigned town: jetties, dormers, pentices, outside stairs, street arches, the gaol grate ---

GATE_STONE = (206, 198, 184)  # the street arch's dressed stone, under the ashlar's grain
GAOL_IRON = (46, 44, 48)
GAOL_STONE = (128, 122, 112)
GAOL_RUST = (112, 66, 42)
SHAFT_DARK = (12, 11, 12)


def _lantern(r, x, y, z, t=None):
    """A small iron lantern hung from a hook at (x, y, z): horn panes lit within, corner rods, a pointed
    cap. With the time `t` a flame burns in it; without, it only glows (a baked prop must stay still)."""
    with r.at(x, y, z):
        r.part("cube", 0, 0.05, 0, 0.02, 0.1, 0.02, IRON)  # the hook
        r.part("cube", 0, -0.32, 0, 0.22, 0.04, 0.22, IRON)  # the base
        r.part("cube", 0, -0.16, 0, 0.18, 0.28, 0.18, (230, 170, 90), glow=True)  # the panes, lit
        for dx in (-0.1, 0.1):
            for dz in (-0.1, 0.1):
                r.part("cube", dx, -0.16, dz, 0.025, 0.32, 0.025, IRON)
        r.part("cone", 0, 0.06, 0, 0.28, 0.18, 0.28, IRON)  # the cap
        if t is not None:
            _flame(r, 0, -0.18, 0, 0.05, t)


def jetty(r, seed, length=3, height=2.4):
    """An overhanging upper storey along a house's wall at local -X, `length` tiles long and centred on
    the prop's tile, its sill at the origin (`rise=` sets it up the wall): floor joists running out of
    the wall carry a moulded bressummer 0.6 m proud of the face, curved brackets on stone corbels prop
    them from below, and over it a frame of oak posts, rails and braces holds a lime-plaster infill
    with a leaded window glowing in each tile's bay, under a moulded top plate."""
    span = length * T
    face = -0.4  # the jettied face, 0.6 m out from the wall
    oak = _dim(OAK, 0.95 + 0.05 * (seed % 3))
    r.part("cube", -0.7, 0.0, 0, 0.6, 0.04, span, _dim(DARK_WOOD, 0.85), tex="wood_plank")  # the soffit
    for z in range(-length * 2, length * 2 + 1):  # joists every half metre, their ends showing
        zj = z * span / (length * 4)
        r.part("cube", -0.7, -0.07, zj, 0.64, 0.14, 0.13, DARK_WOOD)
        r.part("cube", face + 0.01, -0.07, zj, 0.04, 0.12, 0.11, _dim(DARK_WOOD, 0.75))  # its end grain
    r.part("cube", face + 0.04, 0.1, 0, 0.16, 0.22, span + 0.08, oak, tex="wood_plank")  # the bressummer
    r.part("cube", face + 0.12, 0.0, 0, 0.04, 0.04, span + 0.08, _dim(oak, 0.7))  # its moulding
    for i in range(length + 1):  # a bracket under each post, rising off a stone corbel in the wall
        z = -span / 2 + i * T
        z = max(-span / 2 + 0.12, min(span / 2 - 0.12, z))
        r.part("cube", -0.94, -1.12, z, 0.14, 0.3, 0.22, (176, 166, 150), tex="ashlar")  # the corbel
        for k in range(4):  # the bracket's curve, built up in short lengths
            a0, a1 = k * math.pi / 8, (k + 1) * math.pi / 8
            p0 = (-1 + 0.56 * (1 - math.cos(a0)), -1.0 + 0.9 * math.sin(a0), z)
            p1 = (-1 + 0.56 * (1 - math.cos(a1)), -1.0 + 0.9 * math.sin(a1), z)
            _bar(r, p0, p1, 0.13, oak)
    # The infill, then the frame over it.
    r.part("cube", face - 0.03, height / 2 + 0.1, 0, 0.06, height - 0.2, span, PLASTER_WHITE, tex="plaster")
    for end in (-1, 1):  # the jetty's return at each end, back to the wall
        r.part("cube", -0.7, height / 2 + 0.1, end * span / 2, 0.6, height - 0.2, 0.06, PLASTER_WHITE,
               tex="plaster")  # fmt: skip
        r.part("cube", -0.7, height / 2 + 0.1, end * (span / 2 + 0.02), 0.6, 0.12, 0.04, oak)  # its rail
    r.part("cube", face + 0.03, height, 0, 0.16, 0.16, span + 0.1, oak, tex="wood_plank")  # the top plate
    r.part("cube", face + 0.09, height + 0.1, 0, 0.12, 0.06, span + 0.16, _dim(oak, 1.15))  # its moulding
    r.part("cube", face + 0.02, height * 0.42, 0, 0.06, 0.1, span, oak)  # the mid rail
    for i in range(length * 2 + 1):  # posts a metre apart
        z = -span / 2 + 0.05 + i * (span - 0.1) / (length * 2)
        r.part("cube", face + 0.02, height / 2 + 0.1, z, 0.08, height - 0.1, 0.13, oak)
    for i in range(length):  # each tile's bay: braces either side of a window
        zc = -span / 2 + T * (i + 0.5)
        lean = 1 if (seed + i) % 2 else -1
        for side in (-1, 1):
            low = (face + 0.03, 0.22, zc + side * 0.95)
            high = (face + 0.03, height * 0.42, zc + side * 0.55)
            _bar(r, low if lean > 0 else (low[0], low[1], zc + side * 0.55),
                 high if lean > 0 else (high[0], high[1], zc + side * 0.95), 0.08, oak)  # fmt: skip
        wy = height * 0.42 + (height - height * 0.42) / 2
        r.part("cube", face + 0.0, wy, zc, 0.03, 0.7, 0.62, (30, 26, 22))  # the reveal
        r.part("cube", face + 0.01, wy, zc, 0.02, 0.6, 0.52, WINDOW_GLOW, glow=True)
        for rx in (math.pi / 4, -math.pi / 4):  # leaded quarries
            r.part("cube", face + 0.03, wy, zc, 0.012, 0.015, 0.74, LEAD, rx=rx)
        r.part("cube", face + 0.04, wy, zc, 0.04, 0.66, 0.05, oak)  # the mullion
        r.part("cube", face + 0.06, wy - 0.36, zc, 0.12, 0.06, 0.72, oak)  # the sill
        r.part("cube", face + 0.05, wy + 0.36, zc, 0.1, 0.07, 0.72, oak)  # the head


def dormer(r, seed, roof_tex="clay_tile"):
    """A small gabled dormer window standing on a roof's slope, its foot at the origin and its face
    toward +X: a plastered front in an oak frame round a glowing leaded casement, tile-hung cheeks of
    `roof_tex` running back into the roof, and its own little gabled roof with barge boards and a
    finial at the apex. Its back stands 1.7 m deep, to bury itself in the main roof behind."""
    oak = OAK
    r.part("cube", 0.12, 0.02, 0, 0.3, 0.04, 1.5, (94, 96, 100))  # lead flashing at its foot
    r.part("cube", -0.04, 0.55, 0, 0.08, 1.1, 1.24, PLASTER_WHITE, tex="plaster")  # the front
    for z in (-0.62, 0.62):
        r.part("cube", 0.0, 0.55, z, 0.12, 1.14, 0.1, oak)  # corner posts
    r.part("cube", 0.0, 0.05, 0, 0.14, 0.1, 1.36, oak)  # the sill beam
    r.part("cube", 0.0, 1.08, 0, 0.14, 0.1, 1.36, oak)  # the head beam
    r.part("cube", 0.0, 0.58, 0, 0.03, 0.62, 0.6, (30, 26, 22))  # the casement's reveal
    r.part("cube", 0.01, 0.58, 0, 0.02, 0.54, 0.52, WINDOW_GLOW, glow=True)
    for rx in (math.pi / 4, -math.pi / 4):
        r.part("cube", 0.03, 0.58, 0, 0.012, 0.015, 0.72, LEAD, rx=rx)
    r.part("cube", 0.04, 0.58, 0, 0.04, 0.6, 0.05, oak)  # the mullion
    r.part("cube", 0.04, 0.58, 0, 0.04, 0.05, 0.58, oak)  # the transom
    r.part("cube", 0.08, 0.25, 0, 0.14, 0.05, 0.7, _dim(oak, 0.85))  # the casement's sill
    if seed % 2:  # a pot of something hardy on it
        r.part("cube", 0.12, 0.33, 0.2, 0.12, 0.12, 0.12, (150, 80, 52))
        r.part("sphere", 0.12, 0.43, 0.2, 0.16, 0.12, 0.16, (70, 96, 58))
    for side in (-1, 1):  # tile-hung cheeks back into the roof
        r.part("cube", -0.85, 0.55, side * 0.66, 1.7, 1.1, 0.06, WHITE, tex=roof_tex)
    with r.at(-0.8, 1.13, 0, ry=math.pi / 2):  # its own gabled roof, ridge running back into the slope
        r.part("wedge", 0, 0.28, 0, 1.6, 0.56, 1.9, WHITE, tex=roof_tex)
        r.part("cube", 0, 0.58, 0, 0.12, 0.1, 1.94, CLAY_RIDGE if roof_tex == "clay_tile" else DARK_WOOD)
    # The front gable: a plaster triangle under barge boards, an oak king post, a finial.
    r.part("wedge", -0.06, 1.38, 0, 1.24, 0.5, 0.06, PLASTER_WHITE, tex="plaster", ry=math.pi / 2)
    r.part("cube", -0.02, 1.36, 0, 0.06, 0.46, 0.08, oak)
    slope = math.atan2(0.56, 0.8)
    for side in (-1, 1):
        r.part("cube", 0.12, 1.41, side * 0.4, 0.05, 0.1, 0.98, DARK_WOOD, rx=side * slope)
    r.part("cube", 0.12, 1.8, 0, 0.06, 0.32, 0.06, DARK_WOOD)  # the finial
    r.part("sphere", 0.12, 1.98, 0, 0.09, 0.09, 0.09, DARK_WOOD)


def pentice(r, seed, length=1, height=2.5, roof_tex="clay_tile"):
    """A lean-to awning over a door or a shopfront in the wall at local -X, `length` tiles wide and
    centred on the prop's tile: a slab of `roof_tex` on rafters falls from a wall plate to a beam
    `height` up on two oak posts (stone pads at their feet, knee braces at their heads), the half-round
    tiles' mouths showing along its eave; now and then a string of something drying hangs under it."""
    span = length * T
    out = 0.45  # where the posts stand, out from the tile's middle
    rise = 0.6
    oak = _dim(OAK, 0.95 + 0.05 * (seed % 3))
    for side in (-1, 1):  # the posts, on stone pads, braced to the beam
        z = side * (span / 2 - 0.15)
        r.part("cube", out, 0.06, z, 0.3, 0.12, 0.3, (150, 142, 130), tex="ashlar")
        r.part("cube", out, height / 2, z, 0.16, height, 0.16, oak, tex="wood_plank")
        _bar(r, (out, height - 0.55, z), (out, height - 0.08, z - side * 0.5), 0.09, oak)
    r.part("cube", out, height, 0, 0.18, 0.18, span, oak, tex="wood_plank")  # the beam
    r.part("cube", -0.94, height + rise, 0, 0.12, 0.16, span, _dim(oak, 0.85))  # the wall plate
    for i in range(length * 4 + 1):  # rafters every half metre
        z = -span / 2 + 0.06 + i * (span - 0.12) / (length * 4)
        _bar(r, (-0.95, height + rise + 0.06, z), (out + 0.2, height + 0.08, z), 0.07, DARK_WOOD)
    run = out + 0.3 + 0.95
    slope = math.atan2(rise, run)
    mx, my = (out + 0.3 - 0.95) / 2, height + rise / 2 + 0.14
    with r.at(mx, my, 0, rz=-slope):
        r.part("cube", 0, 0, 0, run / math.cos(slope), 0.04, span + 0.2, DARK_WOOD, tex="wood_plank")
        r.part("cube", 0, 0.05, 0, run / math.cos(slope), 0.06, span + 0.2, WHITE, tex=roof_tex)
    n = length * 8  # the eave: each barrel tile's open mouth
    ex, ey = out + 0.28, height + 0.14
    for i in range(n):
        z = -span / 2 - 0.1 + (span + 0.2) * (i + 0.5) / n
        r.part("cyl", ex, ey, z, 0.16, 0.08, 0.16, _dim(CLAY_RIDGE, 0.9 + 0.1 * ((seed + i) % 3)),
               rz=math.pi / 2)  # fmt: skip
    r.part("cube", -0.92, height + rise + 0.14, 0, 0.08, 0.06, span + 0.2, (94, 96, 100))  # lead flashing
    if seed % 3 == 0:  # a string of onions (or herbs) drying under it
        for i in range(5):
            r.part("sphere", 0.1, height - 0.2 - 0.1 * (i % 2), -0.4 + i * 0.2, 0.1, 0.1, 0.1,
                   (186, 140, 82) if i % 2 else (120, 140, 70))  # fmt: skip


def outside_stair(r, seed, run=2, rise=3.0, flip=False):
    """A stone stair up the face of the wall at local -X to an upper door: a solid flight 0.9 m wide
    rising `rise` metres from the prop's tile toward local +Z (toward -Z when `flip`) over `run` tiles,
    its treads lighter than the risers, an iron handrail on balusters along its open side, and at the
    top a landing with a parapet before a plank door under a little tiled hood, a lantern glowing
    beside it."""
    sz = -1.0 if flip else 1.0
    stone = (176, 168, 154)
    x, w = -0.55, 0.9  # the flight's middle and its width
    landing = 1.1
    length = run * T - landing
    steps = max(2, rround(rise / 0.2))
    tread = length / steps
    lift = rise / steps
    z0 = -1.0  # the foot, at the tile's edge
    for k in range(steps):
        h = lift * (k + 1)
        zc = sz * (z0 + tread * (k + 0.5))
        r.part(
            "cube", x, h / 2, zc, w, h, tread + 0.01, _dim(stone, 0.92 + 0.06 * (k % 2)), tex="rough_stone"
        )
        r.part("cube", x + 0.02, h + 0.02, zc + sz * 0.02, w + 0.04, 0.05, tread, _dim(stone, 1.12))
    zl = sz * (z0 + length + landing / 2)  # the landing, on a solid pier
    r.part("cube", x, rise / 2, zl, w, rise, landing, stone, tex="rough_stone")
    r.part("cube", x + 0.02, rise + 0.03, zl, w + 0.06, 0.06, landing + 0.04, _dim(stone, 1.12))
    rail = (-0.13, 0.95)  # the handrail: along the flight, then round the landing
    for k in range(0, steps + 1, 2):
        zb = sz * (z0 + tread * (k + 0.5)) if k < steps else sz * (z0 + length - tread / 2)
        hb = lift * (min(k, steps - 1) + 1)
        r.part("cube", rail[0], hb + 0.45, zb, 0.04, 0.9, 0.04, IRON)  # a baluster
    _bar(r, (rail[0], lift + rail[1], sz * (z0 + tread / 2)),
         (rail[0], rise + rail[1], sz * (z0 + length)), 0.05, IRON)  # fmt: skip
    r.part("cube", -0.12, rise + 0.5, zl, 0.14, 0.9, landing, stone, tex="ashlar")  # the landing's parapet
    r.part("cube", -0.12, rise + 0.98, zl, 0.2, 0.08, landing + 0.06, _dim(stone, 1.1))  # its coping
    # The upper door, its lintel and the hood over it.
    r.part("cube", -0.97, rise + 1.05, zl, 0.06, 2.0, 0.86, DARK_WOOD, tex="door_wood")
    for y in (0.5, 1.5):
        r.part("cube", -0.93, rise + y, zl, 0.02, 0.06, 0.8, IRON)  # its straps
    r.part("cyl", -0.92, rise + 1.0, zl + sz * 0.28, 0.1, 0.03, 0.1, IRON, rz=math.pi / 2)  # its ring
    for side in (-1, 1):
        r.part("cube", -0.93, rise + 1.05, zl + side * 0.5, 0.1, 2.1, 0.14, _dim(stone, 1.05), tex="ashlar")
    r.part("cube", -0.92, rise + 2.15, zl, 0.14, 0.2, 1.16, _dim(stone, 1.05), tex="ashlar")  # the lintel
    with r.at(-0.7, rise + 2.45, zl, rz=-0.5):  # a little tiled hood on two brackets
        r.part("cube", 0, 0, 0, 0.7, 0.05, 1.1, WHITE, tex="clay_tile")
    for side in (-1, 1):
        _bar(r, (-0.97, rise + 2.25, zl + side * 0.55), (-0.5, rise + 2.4, zl + side * 0.55), 0.06, DARK_WOOD)
    r.part("cube", -0.95, rise + 1.9, zl - sz * 0.62, 0.06, 0.04, 0.04, IRON)  # the lantern's bracket
    _lantern(r, -0.82, rise + 1.88, zl - sz * 0.68)


def _segment_top(z, spring, half, rise):
    """Height of a segmental arch's intrados over `z`: an arc through (+-half, spring) rising `rise` at
    its crown; `spring` beyond its span."""
    if abs(z) >= half:
        return spring
    radius = (half * half + rise * rise) / (2 * rise)
    return spring + rise - radius + math.sqrt(max(radius * radius - z * z, 0.0))


ARCH_SPRING = 3.0  # where the street arch's segmental arch springs from its piers
ARCH_RISE = 1.1  # how far its crown rises over that
ARCH_WALL = 4.7  # the top of the wall it carries, under the parapet
ARCH_DEPTH = 1.0  # its thickness along the street


def street_arch(r, seed, width=3, style="crenel"):
    """A free-standing stone gate arch thrown across a street `width` tiles wide, centred on the prop's
    tile with the street running along local X beneath it: two piers on the tiles either side of the
    street (inside the walls or houses there), a segmental arch of dressed voussoirs with a keystone,
    a solid spandrel wall over it, a string course, and on top a crenellated parapet (`style=crenel`)
    or a little tiled gable (`style=gable`). The realm's crest is carved in a panel on both faces, and
    a lantern hangs on a chain under the crown. Nothing stands in the street: you walk under it."""
    half = width * T / 2 + 0.3  # the piers' inner faces, just outside the street
    pier = (width + 1) * T / 2  # the piers' middles, on the tiles flanking the street
    stone = GATE_STONE
    d = ARCH_DEPTH
    for side in (-1, 1):  # the piers: plinth, shaft, impost
        z = side * pier
        r.part("cube", 0, 0.2, z, d + 0.4, 0.4, 1.8, _dim(stone, 0.85), tex="ashlar")
        r.part("cube", 0, ARCH_SPRING / 2, z, d + 0.2, ARCH_SPRING, 1.4, stone, tex="ashlar")
        r.part("cube", 0, ARCH_SPRING - 0.1, z, d + 0.36, 0.2, 1.56, _dim(stone, 1.08))  # the impost
        for face in (-1, 1):  # a shallow pilaster on each face
            r.part("cube", face * (d / 2 + 0.14), ARCH_SPRING / 2, z - side * 0.3, 0.08, ARCH_SPRING - 0.6,
                   0.4, _dim(stone, 0.96), tex="ashlar")  # fmt: skip
    # The arch: voussoirs round a segment of a circle, the keystone proud.
    radius = (half * half + ARCH_RISE * ARCH_RISE) / (2 * ARCH_RISE)
    reach = math.asin(half / radius)
    n = 15
    seg = 2 * radius * reach / n * 1.06
    for i in range(n):
        a = -reach + (i + 0.5) * 2 * reach / n
        key = i == n // 2
        cy = ARCH_SPRING + ARCH_RISE - radius + math.cos(a) * (radius + 0.18)
        r.part("cube", 0.0, cy, math.sin(a) * (radius + 0.18), d + (0.12 if key else 0.04),
               0.46 if key else 0.36, seg * (0.85 if key else 1.0),
               _dim(stone, 1.1 if key else 0.92 + 0.06 * (i % 2)), tex="ashlar", rx=a)  # fmt: skip
    # The spandrels: solid wall from the arch's back up to the string course, in strips.
    strips = 12
    for i in range(strips):
        z0, z1 = (
            -pier - 0.7 + (2 * pier + 1.4) * i / strips,
            -pier - 0.7 + (2 * pier + 1.4) * (i + 1) / strips,
        )
        zm = (z0 + z1) / 2
        under = _segment_top(zm, ARCH_SPRING, half, ARCH_RISE) + 0.3 if abs(zm) < half else ARCH_SPRING
        if under < ARCH_WALL:
            r.part("cube", 0, (under + ARCH_WALL) / 2, zm, d, ARCH_WALL - under, z1 - z0, stone, tex="ashlar")
    span = 2 * pier + 1.4
    r.part("cube", 0, ARCH_WALL + 0.08, 0, d + 0.2, 0.16, span + 0.2, _dim(stone, 1.1))  # the string course
    if style == "gable":  # a little tiled gable over it
        with r.at(0, ARCH_WALL + 0.16, 0):
            r.part("wedge", 0, 0.4, 0, d + 0.5, 0.8, span + 0.3, WHITE, tex="clay_tile")
            r.part("cube", 0, 0.82, 0, 0.14, 0.1, span + 0.34, CLAY_RIDGE)
            for side in (-1, 1):  # finials at the ends of its ridge
                r.part("cone", 0, 1.05, side * (span / 2 + 0.1), 0.18, 0.4, 0.18, CLAY_RIDGE)
    else:  # a parapet, its merlons over the crown and the piers
        r.part("cube", 0, ARCH_WALL + 0.4, 0, d, 0.5, span, stone, tex="ashlar")
        merlons = 7
        for i in range(merlons):
            z = -span / 2 + 0.35 + i * (span - 0.7) / (merlons - 1)
            r.part("cube", 0, ARCH_WALL + 0.95, z, d + 0.04, 0.6, 0.62, _dim(stone, 0.96 + 0.06 * (i % 2)),
                   tex="ashlar")  # fmt: skip
            r.part("cube", 0, ARCH_WALL + 1.27, z, d + 0.12, 0.06, 0.7, _dim(stone, 1.1))  # its coping
    # The crest in a sunk panel over the crown, on both faces.
    crown = ARCH_SPRING + ARCH_RISE
    cy = (crown + 0.5 + ARCH_WALL) / 2
    r.part("cube", 0, cy, 0, d + 0.06, ARCH_WALL - crown - 0.55, 1.1, _dim(stone, 0.8), tex="ashlar")
    with r.at(0, cy, 0):
        realm_crest(r, GILT if seed % 2 else _dim(GILT, 0.85), cy=0.0, scale=0.9, through=d + 0.1)
    # The lantern, on a short chain from the crown's underside.
    for k in range(3):
        r.part("cube", 0, crown - 0.12 - k * 0.12, 0, 0.03, 0.12, 0.05 if k % 2 else 0.02, IRON)
    _lantern(r, 0, crown - 0.45, 0)


def gaol_grate(r, t):
    """The way down into the prison from a plaza: a 2 m square kerb of worn stones flush with the
    paving round a black shaft, its inner faces falling away darker and darker; a heavy square grid of
    crossing iron bars, riveted where they meet, over all of it but one hinged hatch, swung up and
    chained open to a short winch post with a crank on its drum and a lantern on its arm; an iron
    ladder's top curling over the rim in the hatch's mouth; and the cold breath of the cells rising."""
    hole = 0.7  # half the shaft's width
    r.part("cube", 0, 0.012, 0, hole * 2, 0.02, hole * 2, SHAFT_DARK)  # the black of the shaft
    for ring, shade in enumerate(((58, 54, 50), (38, 36, 34), (24, 22, 22))):  # its walls, falling away
        inset = hole - 0.04 - ring * 0.07
        for i in range(4):
            a = i * math.pi / 2
            r.part("cube", math.cos(a) * inset, 0.016, math.sin(a) * inset, 0.07, 0.01, inset * 2 + 0.07,
                   shade, ry=-a)  # fmt: skip
    for i in range(4):  # the kerb: four long stones and four corner blocks, flush with the ground
        a = i * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        r.part("cube", c * 0.85, 0.025, s * 0.85, 0.3, 0.05, 1.4, GAOL_STONE, tex="ashlar", ry=-a)
        r.part("cube", (c - s) * 0.85, 0.026, (s + c) * 0.85, 0.3, 0.052, 0.3, _dim(GAOL_STONE, 0.85),
               tex="ashlar")  # fmt: skip
        r.part(
            "cube", c * 0.715, 0.05, s * 0.715, 0.04, 0.012, 1.4, _dim(GAOL_STONE, 0.6), ry=-a
        )  # its rebate
    # The grid: five bars each way, but those that cross the hatch (x 0..0.7, z -0.7..0) stop at it.
    bars = (-0.56, -0.28, 0.0, 0.28, 0.56)
    for b in bars:
        if b > 0:  # bars along Z, east of the hatch's hinge line: only the half clear of it
            r.part("cube", b, 0.07, hole / 2, 0.07, 0.07, hole, GAOL_IRON)
        else:
            r.part("cube", b, 0.07, 0, 0.07, 0.07, hole * 2, GAOL_IRON)
        if b < 0:  # bars along X, over the hatch's half: only the half clear of it
            r.part("cube", -hole / 2, 0.085, b, hole, 0.07, 0.07, GAOL_IRON)
        else:
            r.part("cube", 0, 0.085, b, hole * 2, 0.07, 0.07, GAOL_IRON)
    for x, z in ((-0.28, -0.28), (-0.28, 0.28), (0.28, 0.28), (-0.56, 0.0), (0.0, 0.56)):  # rivet heads
        r.part("cube", x, 0.125, z, 0.1, 0.03, 0.1, _dim(GAOL_IRON, 1.3))
    for x, z, sx, sz in ((hole / 2, 0.0, hole, 0.1), (0.0, -hole / 2, 0.1, hole)):  # the hatch's frame
        r.part("cube", x, 0.08, z, sx, 0.08, sz, _dim(GAOL_IRON, 0.85))
    # The ladder's top, in the hatch's mouth against the shaft's east face.
    for z in (-0.55, -0.15):
        r.part("cube", 0.6, 0.3, z, 0.06, 0.6, 0.06, GAOL_RUST)
        r.part("cube", 0.66, 0.62, z, 0.16, 0.05, 0.06, GAOL_RUST, rz=-0.6)  # curled over the rim
    for y in (0.12, 0.38):
        r.part("cube", 0.6, y, -0.35, 0.04, 0.04, 0.44, _dim(GAOL_RUST, 1.1))
    # The hatch, hinged on the kerb's edge and swung up past upright, a grid of its own.
    with r.at(hole, 0.09, -hole / 2, rz=-(math.pi / 2 + 0.18)):
        r.part("cube", -hole / 2, 0, -0.33, hole, 0.06, 0.07, GAOL_IRON)
        r.part("cube", -hole / 2, 0, 0.33, hole, 0.06, 0.07, GAOL_IRON)
        for x in (-0.04, -0.66):
            r.part("cube", x, 0, 0, 0.07, 0.06, hole - 0.02, GAOL_IRON)
        for x in (-0.24, -0.45):
            r.part("cube", x, 0, 0, 0.05, 0.05, hole - 0.04, _dim(GAOL_IRON, 1.15))
        r.part("cube", -hole / 2, 0, 0, hole - 0.04, 0.05, 0.05, _dim(GAOL_IRON, 1.15))
        for z in (-0.25, 0.25):
            r.part("cyl", 0, 0, z, 0.1, 0.14, 0.1, GAOL_IRON, rx=math.pi / 2)  # its hinge knuckles
        r.part("cube", -0.68, 0.05, 0, 0.06, 0.06, 0.1, IRON)  # the eye for the chain
    free = (hole + 0.68 * math.cos(math.pi / 2 - 0.18), 0.09 + 0.68 * math.sin(math.pi / 2 - 0.18), -hole / 2)
    # The winch post on the kerb's corner, its drum, crank and lantern arm.
    px, pz = 0.85, -0.85
    r.part("cube", px, 0.65, pz, 0.2, 1.3, 0.2, OAK, tex="wood_plank")
    r.part("cube", px, 0.06, pz, 0.3, 0.12, 0.3, GAOL_IRON)  # its iron shoe, leaded into the kerb
    r.part("cyl", px - 0.16, 1.0, pz, 0.2, 0.26, 0.2, OAK, rz=math.pi / 2)  # the drum
    for k in range(3):  # chain wound round it
        r.part("cyl", px - 0.24 + k * 0.08, 1.0, pz, 0.23, 0.04, 0.23, GAOL_IRON, rz=math.pi / 2)
    r.part("cube", px + 0.14, 1.0, pz, 0.1, 0.04, 0.04, GAOL_IRON)  # the axle
    r.part("cube", px + 0.2, 0.88, pz, 0.04, 0.26, 0.04, GAOL_IRON)  # the crank's arm
    r.part("cube", px + 0.26, 0.76, pz, 0.14, 0.05, 0.05, OAK)  # its handle
    drum = (px - 0.16, 0.92, pz + 0.04)
    links = 7  # the chain from drum to hatch, link by link
    for k in range(links):
        a = [drum[i] + (free[i] - drum[i]) * k / links for i in range(3)]
        b = [drum[i] + (free[i] - drum[i]) * (k + 1) / links for i in range(3)]
        _bar(r, a, b, 0.035 if k % 2 else 0.05, _dim(GAOL_IRON, 1.2))
    r.part("cube", px, 1.36, pz + 0.22, 0.06, 0.06, 0.5, GAOL_IRON)  # the lantern's arm
    _lantern(r, px, 1.33, pz + 0.42, t)
    for i in range(4):  # the cells' cold breath, curling up through the bars
        u = (t * 0.28 + i / 4) % 1.0
        s = 0.2 + 0.32 * u
        r.part("cube", math.sin(t * 0.6 + i * 1.7) * 0.3, 0.12 + u * 1.5, math.cos(i * 2.1) * 0.3,
               s, s * 0.5, s, (112, 116, 120), tex="mist")  # fmt: skip
