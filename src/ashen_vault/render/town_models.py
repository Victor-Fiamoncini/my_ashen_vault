"""Harrowmere's models: tiled roofs, the Silent Bell, the cathedral (its towers, spire, buttresses and
stained glass), pews, the dressing of its sun-warmed stone houses (shuttered windows, balconies, arched
doorways), the realm's crest on poles and plaques, the furniture and the street dressing of a harbour
town (beds, cupboards, shelves, hearths, a fountain, benches, carts and cargo, fences, lamp posts, a
moored boat, the smith's sign, bellows and grindstone). Pure part lists drawn through a Rig, like `models`."""

import itertools
import math

from ashen_vault.render.models import IRON, WHITE, _dim, _flame, realm_crest
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
SHUTTER_PAINT = ((70, 104, 78), (62, 86, 120), (120, 84, 50), (128, 56, 44))
REALM_CLOTH = ((122, 30, 32), (36, 48, 92))
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
    r.part("wedge", 0, base + 7.1, 0, 4.8, 1.0, 4.2, WHITE, tex="slate", ry=math.pi / 2)  # a small roof
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
    r.part("cone", 0, height + 4.0, 0, w * 0.85, 8.0, w * 0.85, WHITE, tex="slate")
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


def smith_sign(r, seed):
    """The smith's sign, hung from the wall at local -X: a wrought bracket and its brace standing out
    over the street, two short chains and a painted board swinging from them, an iron anvil and
    hammer on each face."""
    r.part("cube", -0.5, 2.95, 0, 0.94, 0.05, 0.05, SIGN_IRON)  # the bracket's arm
    r.part("cube", -0.97, 2.75, 0, 0.06, 0.5, 0.12, SIGN_IRON)  # its wall plate
    r.part("cube", -0.68, 2.72, 0, 0.6, 0.035, 0.035, SIGN_IRON, rz=0.62)  # the brace
    r.part("cube", -0.04, 2.95, 0, 0.08, 0.08, 0.08, SIGN_IRON)  # a knob at its end
    for x in (-0.68, -0.22):  # chains
        r.part("cube", x, 2.84, 0, 0.02, 0.18, 0.02, SIGN_IRON)
    board = SHUTTER_PAINT[seed % len(SHUTTER_PAINT)]
    r.part("cube", -0.45, 2.48, 0, 0.62, 0.56, 0.05, board, tex="wood_plank")
    r.part("cube", -0.45, 2.48, 0, 0.66, 0.6, 0.035, DARK_WOOD)  # its frame
    for side in (-1, 1):  # the anvil and hammer, on both faces
        z = side * 0.03
        r.part("cube", -0.45, 2.4, z, 0.3, 0.06, 0.01, SIGN_IRON)  # the anvil's face
        r.part("cube", -0.45, 2.33, z, 0.12, 0.08, 0.01, SIGN_IRON)  # its waist
        r.part("cube", -0.45, 2.27, z, 0.24, 0.04, 0.01, SIGN_IRON)  # its foot
        r.part("cube", -0.63, 2.41, z, 0.08, 0.03, 0.01, SIGN_IRON)  # the horn
        r.part("cube", -0.39, 2.58, z, 0.24, 0.03, 0.01, (150, 110, 70), rz=-0.6)  # the hammer's haft
        r.part("cube", -0.5, 2.66, z, 0.1, 0.06, 0.01, SIGN_IRON, rz=-0.6)  # its head


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


def shutters(r, seed):
    """A window deep in a house wall at local -X: a dark casement faintly lit within, a cross of wooden
    mullions, a stone sill and lintel, and two painted, louvred shutters folded back against the wall."""
    paint = SHUTTER_PAINT[seed % len(SHUTTER_PAINT)]
    stone = (236, 230, 218)
    r.part("cube", -0.985, 0, 0, 0.03, 1.2, 0.86, (36, 30, 26))  # the reveal, in shadow
    r.part("cube", -0.98, 0, 0, 0.02, 1.0, 0.7, (120, 92, 56), glow=True)  # lamplight behind the glass
    r.part("cube", -0.97, 0, 0, 0.03, 1.04, 0.06, DARK_WOOD)  # the mullion
    r.part("cube", -0.97, 0.1, 0, 0.03, 0.06, 0.74, DARK_WOOD)  # the transom
    r.part("cube", -0.9, -0.66, 0, 0.22, 0.1, 1.06, stone, tex="ashlar")  # sill
    r.part("cube", -0.93, 0.68, 0, 0.16, 0.16, 1.1, stone, tex="ashlar")  # lintel
    for side in (-1, 1):  # the shutters, folded back
        z = side * 0.72
        r.part("cube", -0.96, 0, z, 0.04, 1.16, 0.5, paint, tex="wood_plank")
        for y in (-0.25, 0.25):  # louvred panels
            r.part("cube", -0.94, y, z, 0.02, 0.4, 0.38, _dim(paint, 0.72), tex="wood_plank")


def balcony(r, seed):
    """An upper-floor balcony on the wall at local -X: a plank deck on carved corbels, a turned rail,
    a half-open door behind it and, some days, a rug or a washing line airing over the rail."""
    wood = _dim(WOOD, 0.9)
    r.part("cube", -0.98, 1.05, 0, 0.03, 2.1, 1.0, (34, 28, 24))  # the doorway behind
    with r.at(-0.97, 1.05, -0.5, ry=-1.1):
        r.part("cube", 0.02, 0, 0.45, 0.06, 2.0, 0.9, DARK_WOOD, tex="door_wood")  # its door, ajar
    r.part("cube", -0.92, 2.2, 0, 0.14, 0.14, 1.2, _dim(SANDSTONE, 1.05))  # lintel
    r.part("cube", -0.58, -0.06, 0, 0.84, 0.12, 2.0, wood, tex="wood_plank")  # the deck
    for z in (-0.8, 0.0, 0.8):  # corbels
        r.part("cube", -0.82, -0.32, z, 0.36, 0.34, 0.16, DARK_WOOD)
        r.part("cube", -0.6, -0.2, z, 0.3, 0.12, 0.16, DARK_WOOD, rz=-0.5)
    r.part("cube", -0.18, 0.92, 0, 0.08, 0.08, 2.0, DARK_WOOD)  # the rail
    for z in (-0.95, 0.95):
        r.part("cube", -0.58, 0.92, z, 0.8, 0.08, 0.08, DARK_WOOD)
        r.part("cube", -0.58, 0.45, z, 0.06, 0.9, 0.06, wood)  # side posts
    for i in range(10):  # balusters
        r.part("cube", -0.18, 0.45, -0.9 + i * 0.2, 0.05, 0.86, 0.05, wood)
    if seed % 3 == 0:
        r.part("cube", -0.14, 0.62, 0.2, 0.06, 0.62, 0.9, CLOTH[seed % len(CLOTH)])  # a rug over the rail
    elif seed % 3 == 1:
        r.part("cyl", -0.32, 0.18, 0.7, 0.3, 0.3, 0.3, (150, 80, 50))  # a pot of herbs
        r.part("sphere", -0.32, 0.42, 0.7, 0.34, 0.28, 0.34, (70, 110, 50))


def door_arch(r, seed, height=3.2, spring=2.2, rose=False):
    """A house's front door, set in the doorway tile and facing out along +X: a round arch of dressed
    voussoirs on two pilasters at the wall's outer face (x = 1), filled solid above it to the room's
    ceiling, and a studded plank door standing open against the jamb inside. With `rose`, a rose window
    glows in the tympanum (the cathedral's west door)."""
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
    # The door, open against the jamb inside: planks, iron straps, a ring.
    r.part("cube", 0.0, spring / 2 + 0.1, -0.86, 1.5, spring + 0.1, 0.08, DARK_WOOD, tex="door_wood", ry=0.08)
    for y in (0.5, 1.3, 2.0):
        r.part("cube", 0.0, y, -0.81, 1.4, 0.07, 0.03, IRON, ry=0.08)
    r.part("cyl", -0.55, 1.1, -0.79, 0.14, 0.03, 0.14, IRON, rx=math.pi / 2)


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
    r.part("cone", 0, height + 0.7 + helm / 2, 0, w * 0.82, helm, w * 0.82, WHITE, tex="slate")  # the helm
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


def hand_cart(r, seed):
    """A two-wheeled hand cart, its handles toward +X and its bed tipped back onto its wheels, heaped
    with sacks or a pair of casks."""
    wood = _dim(WOOD, 0.9 + (seed % 3) * 0.05)
    for z in (-0.62, 0.62):  # the wheels
        r.part("cyl", -0.25, 0.45, z, 0.9, 0.08, 0.9, DARK_WOOD, rx=math.pi / 2)
        r.part("cyl", -0.25, 0.45, z, 0.18, 0.12, 0.18, IRON, rx=math.pi / 2)
        for k in range(3):
            r.part("cube", -0.25, 0.45, z, 0.06, 0.82, 0.04, _dim(DARK_WOOD, 1.2), rz=k * math.pi / 3)
    with r.at(0, 0.7, 0, rz=0.12):  # the bed
        r.part("cube", 0, 0, 0, 1.3, 0.08, 1.0, wood, tex="wood_plank")
        for z in (-0.5, 0.5):
            r.part("cube", 0, 0.18, z, 1.3, 0.36, 0.06, wood, tex="wood_plank")  # sides
            r.part("cube", 1.05, -0.05, z * 0.8, 0.9, 0.06, 0.06, DARK_WOOD)  # handles
        r.part("cube", -0.65, 0.18, 0, 0.06, 0.36, 1.0, wood, tex="wood_plank")
        if seed % 2:
            for i, (x, z) in enumerate(((-0.3, -0.2), (0.2, 0.15), (-0.2, 0.25), (0.15, -0.25))):
                r.part("sphere", x, 0.3 + (i // 2) * 0.12, z, 0.5, 0.36, 0.42, _dim(SACK, 0.9 + i * 0.04))
        else:
            for z in (-0.24, 0.24):
                r.part("cyl", 0, 0.32, z, 0.5, 0.9, 0.5, WOOD, tex="wood_plank", rz=math.pi / 2)
                for x in (-0.3, 0.3):
                    r.part("cyl", x, 0.32, z, 0.52, 0.05, 0.52, IRON, rz=math.pi / 2)
    r.part("cube", 0.75, 0.25, 0, 0.06, 0.5, 0.06, DARK_WOOD)  # a prop leg


def hay_wagon(r, seed):
    """A four-wheeled farm wagon heaped with hay, its shaft tilted down to the ground toward +X."""
    wood = _dim(WOOD, 0.85)
    for x in (-0.6, 0.55):
        for z in (-0.62, 0.62):
            r.part("cyl", x, 0.38, z, 0.76, 0.08, 0.76, DARK_WOOD, rx=math.pi / 2)
            r.part("cyl", x, 0.38, z, 0.16, 0.12, 0.16, IRON, rx=math.pi / 2)
    r.part("cube", 0, 0.78, 0, 1.8, 0.1, 1.1, wood, tex="wood_plank")  # the bed
    for z in (-0.56, 0.56):  # rails and stakes
        r.part("cube", 0, 1.15, z, 1.8, 0.06, 0.06, DARK_WOOD)
        for x in (-0.8, -0.27, 0.27, 0.8):
            r.part("cube", x, 1.0, z, 0.06, 0.45, 0.06, DARK_WOOD)
    r.part("cube", 0, 1.15, 0, 1.7, 0.6, 1.05, HAY)  # the hay
    r.part("sphere", -0.1, 1.45, 0, 1.6, 0.6, 1.0, _dim(HAY, 1.05))
    for i in range(6):  # loose wisps
        r.part(
            "cube",
            -0.7 + i * 0.28,
            1.55 + (i % 2) * 0.1,
            (i % 3 - 1) * 0.3,
            0.3,
            0.04,
            0.05,
            _dim(HAY, 1.15),
            ry=i,
        )
    with r.at(0.9, 0.62, 0, rz=-0.32):  # the shaft
        for z in (-0.3, 0.3):
            r.part("cube", 0.75, 0, z, 1.5, 0.08, 0.08, DARK_WOOD)
        r.part("cube", 1.45, 0, 0, 0.08, 0.08, 0.66, DARK_WOOD)
    if seed % 2:
        r.part("cube", 0.2, 1.75, 0.25, 0.08, 0.08, 1.2, DARK_WOOD, rx=0.4)  # a pitchfork left on top


def cargo(r, seed):
    """Goods hauled up from the quay and left in a heap: sacks, a rope-bound bale, a cask or two."""
    for i, (x, z) in enumerate(((-0.4, -0.4), (0.1, -0.5), (-0.5, 0.1))):
        r.part("sphere", x, 0.25, z, 0.6, 0.5, 0.5, _dim(SACK, 0.85 + 0.06 * ((seed + i) % 3)), ry=i)
    r.part("sphere", -0.25, 0.62, -0.25, 0.55, 0.42, 0.45, SACK, ry=0.6)
    r.part("cube", 0.4, 0.35, 0.3, 0.8, 0.7, 0.7, (150, 128, 80), ry=0.2)  # the bale, in sacking
    for x in (0.2, 0.6):
        r.part("cube", x, 0.35, 0.3, 0.04, 0.74, 0.74, (86, 66, 40), ry=0.2)  # its ropes
    for k in range(1 + seed % 2):  # casks
        x, z = (0.5, -0.45) if k == 0 else (-0.55, 0.6)
        r.part("cyl", x, 0.45, z, 0.6, 0.9, 0.6, WOOD, tex="wood_plank")
        for y in (0.15, 0.75):
            r.part("cyl", x, y, z, 0.62, 0.05, 0.62, IRON)


def fence(r, seed):
    """A low split-rail fence running across the tile along Z."""
    for z in (-0.9, 0.0, 0.9):
        r.part("cube", 0, 0.55, z, 0.12, 1.1, 0.12, DARK_WOOD)
    for y in (0.4, 0.85):
        r.part("cube", 0, y, 0, 0.06, 0.08, 2.0, _dim(WOOD, 0.9), rx=0.02 * (seed % 3))


def lamp_post(r, t):
    """An iron lamp post: a lantern burning in its cage on a bracket."""
    r.part("cube", 0, 0.15, 0, 0.4, 0.3, 0.4, (90, 88, 84))  # a stone foot
    r.part("cyl", 0, 1.5, 0, 0.1, 2.7, 0.1, (40, 40, 44))
    r.part("cube", 0.2, 2.8, 0, 0.45, 0.05, 0.05, (40, 40, 44))  # bracket
    with r.at(0.4, 2.55, 0):
        r.part("cube", 0, 0, 0, 0.26, 0.36, 0.26, (40, 40, 44))
        r.part("cube", 0, 0, 0, 0.2, 0.28, 0.27, (255, 200, 110), glow=True)
        r.part("cone", 0, 0.28, 0, 0.3, 0.2, 0.3, (40, 40, 44))
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
