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
    _bar,
    _dim,
    _flame,
    _weapon,
    garment,
    gauntlet,
    katana,
    realm_crest,
    shield,
)
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


def roof(r, w, d, ridge="x", top=4.2, pitch=1.8, tex="roof", wall_tex="timber", eave=0.35):
    """A gabled roof over a `w` x `d` tile building whose NW corner tile holds the prop: a pitched
    slab running along `ridge`, the gable ends filled in the wall's texture, a ridge beam, and the
    eaves overhanging the walls by `eave`."""
    cx, cz = (w - 1) * T / 2, (d - 1) * T / 2
    span_x, span_z = w * T, d * T
    if ridge == "x":  # the wedge's ridge runs along its Z: turn it so it runs along X
        across, along, ry = span_z, span_x, math.pi / 2
    else:
        across, along, ry = span_x, span_z, 0.0
    with r.at(cx, top, cz, ry=ry):
        r.part("wedge", 0, pitch / 2, 0, across + eave * 2, pitch, along + eave * 2, WHITE, tex=tex)
        # The gable walls just inside the overhang, and a dark band where the roof meets them.
        r.part(
            "wedge", 0, (pitch - 0.1) / 2, 0, across - 0.05, pitch - 0.1, along + 0.04, WHITE, tex=wall_tex
        )
        r.part("cube", 0, 0.02, 0, across + eave * 2, 0.08, along + eave * 2 + 0.02, _dim(DARK_WOOD, 0.8))
        r.part("cube", 0, pitch + 0.04, 0, 0.18, 0.14, along + eave * 2 + 0.1, DARK_WOOD)  # ridge beam
        for end in (-1, 1):  # barge boards along each gable's slopes
            for side in (-1, 1):
                slope = math.atan2(pitch, across / 2 + eave)
                with r.at(side * (across / 4 + eave / 2), pitch / 2, end * (along / 2 + eave + 0.02)):
                    r.part("cube", 0, 0, 0, across / 2 + eave + 0.2, 0.1, 0.06, DARK_WOOD, rz=-side * slope)


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


def balcony(r, seed):
    """An upper-floor gallery jettied out of the wall at local -X: a plank deck on carved corbels and
    raking braces, a parapet of boards under a rail, a half-open door behind it, and a pent roof of slate
    over it on two brackets; some days a rug airs over the boards or a lantern hangs from the roof."""
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
        r.part("cube", 0, 0.05, 0, 1.05, 0.05, 2.3, WHITE, tex="violet_slate")
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


def roof_turret(r, seed, height=3.2, radius=0.9, cap=3.6):
    """A little round turret set out on a house's corner, its foot at the origin: a cone of corbels
    swelling out of the wall below, a plastered drum with a slit window or two lit from within, a
    timber band at the eaves, and a tall witch-hat cone of violet slate with an iron finial."""
    d = radius * 2
    stone = (176, 166, 152)
    r.part("cone", 0, -0.6, 0, d, 1.2, d, _dim(stone, 0.85), tex="ashlar", rx=math.pi)  # the corbelling
    r.part("cyl", 0, height / 2, 0, d, height, d, stone, tex="plaster" if seed % 2 else "ashlar")
    r.part("cyl", 0, 0.05, 0, d + 0.1, 0.16, d + 0.1, VIOLET_TRIM)  # string course at its foot
    r.part("cyl", 0, height - 0.08, 0, d + 0.12, 0.18, d + 0.12, VIOLET_TRIM)  # band at the eaves
    for k in range(2 if seed % 3 else 1):  # slit windows, warm behind
        a = seed * 0.7 + k * math.pi * 0.8
        x, z = math.cos(a) * (radius - 0.02), math.sin(a) * (radius - 0.02)
        r.part("cube", x, height * 0.55, z, 0.08, 0.7, 0.22, (32, 26, 24), ry=-a)
        r.part("cube", x * 1.01, height * 0.55, z * 1.01, 0.06, 0.56, 0.12, (150, 108, 62), ry=-a, glow=True)
    r.part("cone", 0, height + cap / 2, 0, d + 0.5, cap, d + 0.5, WHITE, tex="violet_slate")  # witch's hat
    r.part("cyl", 0, height + 0.1, 0, d + 0.56, 0.12, d + 0.56, _dim(VIOLET_TRIM, 0.8))  # its flared eave
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
