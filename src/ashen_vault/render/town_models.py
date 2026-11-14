"""Harrowmere's models: pitched roofs, the Silent Bell, the cathedral's spire, pews and windows, and the
furniture and street dressing of a fishing town (beds, cupboards, shelves, hearths, market stalls,
fences, lamp posts, a moored boat). Pure part lists drawn through a Rig, like `models`."""

import math

from ashen_vault.render.models import IRON, WHITE, _dim, _flame
from ashen_vault.world.tile_map import TileMap

T = TileMap.TILE
WOOD = (104, 74, 48)
DARK_WOOD = (70, 50, 34)
BRONZE = (120, 96, 54)
BRONZE_DARK = (74, 58, 34)
PALE_STONE = (150, 146, 136)
CLOTH = ((150, 50, 44), (60, 90, 120), (140, 120, 60), (70, 110, 70))
GLASS = ((120, 150, 200), (190, 150, 70), (150, 60, 60), (90, 140, 110))


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


def window(r, seed):
    """A tall lancet of coloured glass set in the wall at local -X, glowing with the grey day outside."""
    glass = GLASS[seed % len(GLASS)]
    r.part("cube", -0.98, 2.6, 0, 0.06, 3.4, 1.0, (40, 40, 48))  # the frame
    for i, y in enumerate((1.4, 2.2, 3.0, 3.6)):  # panes between the leading
        rgb = glass if i % 2 == 0 else GLASS[(seed + 1) % len(GLASS)]
        r.part("cube", -0.95, y, 0, 0.02, 0.7 if i < 3 else 0.45, 0.8, rgb, glow=True)
    r.part("cube", -0.94, 2.4, 0, 0.02, 3.0, 0.05, (30, 30, 36))  # the mullion
    r.part("wedge", -0.98, 4.45, 0, 1.0, 0.5, 0.06, (40, 40, 48))  # the pointed head


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


def stall(r, seed, t):
    """A market stall facing +X: a trestle counter heaped with goods under a striped awning."""
    cloth = CLOTH[seed % len(CLOTH)]
    r.part("cube", 0.2, 0.8, 0, 0.8, 0.08, 1.8, WOOD, tex="wood_plank")  # counter
    r.part("cube", 0.58, 0.45, 0, 0.04, 0.7, 1.8, DARK_WOOD, tex="wood_plank")  # its front
    for z in (-0.85, 0.85):
        for x in (-0.6, 0.6):
            r.part("cube", x, 1.15, z, 0.08, 2.3, 0.08, DARK_WOOD)  # poles
    sway = math.sin(t * 1.1 + seed) * 0.02
    with r.at(0, 2.3, 0, rz=-0.25 + sway):
        for i in range(4):  # striped awning
            rgb = cloth if i % 2 == 0 else (210, 200, 180)
            r.part("cube", 0, 0, -0.75 + i * 0.5, 1.5, 0.04, 0.5, rgb)
        for i in range(5):  # scalloped edge
            r.part("cube", 0.75, -0.08, -0.8 + i * 0.4, 0.04, 0.14, 0.3, cloth)
    goods = seed % 3
    for i in range(4):
        z = -0.6 + i * 0.4
        if goods == 0:  # fish
            r.part("cube", 0.25, 0.88, z, 0.4, 0.06, 0.1, (150, 160, 170), ry=0.3 * (i % 2))
        elif goods == 1:  # apples and roots
            r.part("sphere", 0.2, 0.9, z, 0.14, 0.14, 0.14, ((170, 40, 30), (180, 140, 60))[i % 2])
        else:  # bolts of cloth
            r.part("cyl", 0.2, 0.92, z, 0.18, 0.3, 0.18, CLOTH[(seed + i) % len(CLOTH)], rx=math.pi / 2)
    r.part("cube", -0.5, 0.3, 0.5, 0.5, 0.6, 0.5, WOOD, tex="wood_plank")  # a crate behind


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
