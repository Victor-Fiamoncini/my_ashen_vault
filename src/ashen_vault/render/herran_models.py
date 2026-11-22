"""Models for Herran's Castle, which hangs over a sea of cloud between the sun and Vesperholm's moon:
the stair of light between it and Vesperholm, built in the castle's Victorian Gothic manner (gilt cast
iron, brass and glass), and the castle's own dressing.
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.render.parts import HIT_GLOW, _bar, _dim, death_fall, hit_tint
from ashen_vault.util import rround

GILT = (196, 150, 70)  # gilt cast iron and brass, the castle's metal
GILT_DARK = (120, 86, 42)
IRON = (46, 52, 48)  # cast iron painted a dark green, flaking
SUNLIGHT = (255, 214, 140)  # the stair's light: the sun's, caught and held
MOONLIGHT = (214, 230, 255)
LAMP_GLASS = (255, 226, 160)


def _blend(a, b, k):
    """The colour `k` of the way from `a` to `b`."""
    return tuple(rround(x + (y - x) * k) for x, y in zip(a, b, strict=True))


def _lamp_post(r, z, t, height=2.6):
    """A gilt cast-iron lamp post: a fluted base, a slender column and a lantern of four glass panes
    under a domed cap, the flame in it breathing."""
    with r.at(0, 0, z):
        r.part("cyl", 0, 0.12, 0, 0.34, 0.24, 0.34, IRON)  # the plinth
        r.part("cyl", 0, 0.3, 0, 0.24, 0.12, 0.24, GILT_DARK)
        r.part("cyl", 0, height / 2, 0, 0.1, height - 0.4, 0.1, IRON)  # the column
        for y in (0.7, height - 0.5):
            r.part("cyl", 0, y, 0, 0.16, 0.05, 0.16, GILT)  # its rings
        r.part("cube", 0, height, 0, 0.3, 0.36, 0.3, LAMP_GLASS, glow=True)  # the lantern's glass
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # its corner ribs
            r.part("cube", dx * 0.15, height, dz * 0.15, 0.03, 0.4, 0.03, GILT_DARK)
        r.part("pyramid", 0, height + 0.27, 0, 0.38, 0.18, 0.38, IRON)  # the cap
        r.part("sphere", 0, height + 0.42, 0, 0.06, 0.06, 0.06, GILT)  # its finial
        flame = 0.09 + 0.012 * math.sin(t * 5 + z)
        r.part("sphere", 0, height - 0.02, 0, flame, flame * 1.5, flame, SUNLIGHT, glow=True)


def sky_stair(r, t, way="up"):
    """The stair of light between Vesperholm and Herran's Castle, its head at the tile's middle and
    running off along +X: at its head two gilt lamp posts and a wrought-iron arch between them crowned
    with a sun; past it, treads of held light, edged in brighter light, hanging on nothing. `way="up"`
    climbs (Vesperholm's end, up into the sky); `way="out"` runs out level from the quay's edge and
    fades into the cloud. Motes of light drift up off it. Nothing of it is below the floor."""
    with r.at(0.85, 0, 0):  # its head on the tile's +X edge, so the stair runs off it, not across it
        _sky_stair(r, t, way)


def _sky_stair(r, t, way):
    half = 0.95  # the arch's half-width
    for side in (-1, 1):
        _lamp_post(r, side * half, t)
    for i in range(9):  # the arch: a round of wrought-iron bars between the posts' lanterns
        a0, a1 = math.pi * i / 9, math.pi * (i + 1) / 9
        p0 = (0, 3.05 + math.sin(a0) * 0.8, math.cos(a0) * half)
        p1 = (0, 3.05 + math.sin(a1) * 0.8, math.cos(a1) * half)
        _bar(r, p0, p1, 0.06, IRON if i % 2 else GILT_DARK)
    for side in (-1, 1):  # scrolls hung inside it
        r.part("cyl", 0, 3.25, side * 0.42, 0.24, 0.03, 0.24, GILT, rz=math.pi / 2)
    with r.at(0, 4.05, 0):  # the sun that crowns it
        r.part("cyl", 0, 0, 0, 0.36, 0.06, 0.36, GILT, rz=math.pi / 2)
        r.part("cyl", 0.02, 0, 0, 0.22, 0.06, 0.22, SUNLIGHT, rz=math.pi / 2, glow=True)
        for i in range(8):
            a = i * math.pi / 4 + t * 0.2
            r.part("cube", 0, math.sin(a) * 0.3, math.cos(a) * 0.3, 0.04, 0.16, 0.05, GILT, rx=-a)
    treads = 10
    for i in range(treads):
        fade = 1 - i / (treads + 2)
        if way == "up":
            x, y = 0.6 + i * 0.6, 0.12 + i * 0.42
        else:
            x, y = 0.6 + i * 0.7, 0.06 + 0.02 * i
        light = _blend(MOONLIGHT, SUNLIGHT, i / treads)
        pulse = 0.85 + 0.15 * math.sin(t * 2 - i * 0.6)
        r.part("cube", x, y, 0, 0.5, 0.06, 1.5 - i * 0.03, _dim(light, 0.7 * fade * pulse), glow=True)
        r.part("cube", x + 0.24, y + 0.03, 0, 0.04, 0.04, 1.54 - i * 0.03, _dim(light, fade), glow=True)
    for k in range(6):  # motes drifting up off the treads
        s = (t * 0.35 + k / 6) % 1
        x = 0.8 + (k * 1.37) % 5
        y = (x * 0.7 if way == "up" else 0.1) + s * 1.6
        r.part("sphere", x, y, (k % 3 - 1) * 0.5, 0.04, 0.04, 0.04, _dim(SUNLIGHT, 1 - s), glow=True)


# --- The castle's dressing ------------------------------------------------------------------------

BRICK = (156, 66, 48)
BRICK_DARK = (112, 46, 36)
CREAM = (214, 196, 158)
ASHLAR = (214, 202, 178)
ASHLAR_DARK = (160, 148, 124)
SLATE = (66, 62, 84)
SLATE_DARK = (40, 38, 54)
GLASS = (168, 196, 210)
WINDOW_LIT = (255, 210, 130)
SPECIMEN = (120, 210, 120)  # the green of the vats' fluid
FLESH = (196, 150, 130)


def gas_lamp(r, seed):
    """A gilt cast-iron gas lamp on a fluted column, its lantern lit: the castle's courts and bridges."""
    _lamp_post(r, 0, 1.0 + (seed % 5) * 0.2, height=2.9)


def _window(r, x, y, z, w, h, lit, face=0.0):
    """A tall round-headed window on a wall facing +X (turned `face` about Y): an ashlar surround, a
    glazed or lit light in it and a sill."""
    with r.at(x, y, z, ry=face):
        r.part("cube", 0, 0, 0, 0.12, h + 0.24, w + 0.24, ASHLAR)  # the surround
        r.part("cube", 0.04, 0, 0, 0.08, h, w, WINDOW_LIT if lit else (36, 40, 52), glow=lit)
        r.part(
            "cyl", 0.04, h / 2, 0, w, 0.08, w, WINDOW_LIT if lit else (36, 40, 52), rz=math.pi / 2, glow=lit
        )
        r.part("cube", 0.12, -h / 2 - 0.16, 0, 0.2, 0.08, w + 0.34, ASHLAR_DARK)  # the sill
        r.part("cube", 0.07, 0, 0, 0.04, h, 0.04, IRON)  # the mullion


def herran_tower(r, seed, height, style):
    """One of the castle's towers rising off a wall top into the clouds, each its own shape (`style`):
    a `round` drum under a conical cap, an `octagon` under a spire, a `clock` tower with a clock face on
    each side under a pyramid and lantern, a `belvedere` with an open loggia of arches under its dome,
    a `needle` that thins in stages to a long iron spike. Red brick banded in cream, ashlar quoins and
    cornices, lit windows up it, slate caps with gilt finials. Its foot is at the wall top (y 0)."""
    sides = {"round": 12, "octagon": 8, "clock": 4, "belvedere": 8, "needle": 6}[style]
    width = {"round": 3.4, "octagon": 3.6, "clock": 3.8, "belvedere": 3.2, "needle": 2.6}[style]
    shaft = height * 0.68
    kind = "cyl" if style in ("round", "belvedere") else "cube"
    with r.at(0, 0, 0, ry=math.pi / sides if kind == "cube" and sides == 8 else 0):
        if kind == "cyl":
            r.part("cyl", 0, shaft / 2, 0, width, shaft, width, BRICK, tex="herran_brick")
        else:
            r.part("cube", 0, shaft / 2, 0, width, shaft, width, BRICK, tex="herran_brick")
            if sides == 8:
                r.part(
                    "cube", 0, shaft / 2, 0, width, shaft, width, BRICK, tex="herran_brick", ry=math.pi / 4
                )
            if sides == 6:
                r.part(
                    "cube", 0, shaft / 2, 0, width, shaft, width, BRICK, tex="herran_brick", ry=math.pi / 3
                )
        bands = max(2, int(shaft / 3.2))
        for i in range(1, bands + 1):  # cream bands and cornices up the shaft
            y = shaft * i / (bands + 0.5)
            r.part(kind, 0, y, 0, width + 0.12, 0.22, width + 0.12, CREAM, tex="herran_ashlar")
        r.part(
            kind, 0, shaft + 0.15, 0, width + 0.5, 0.3, width + 0.5, ASHLAR, tex="herran_ashlar"
        )  # cornice
        r.part(kind, 0, 0.3, 0, width + 0.3, 0.6, width + 0.3, ASHLAR_DARK, tex="herran_ashlar")  # plinth
        for i in range(4):  # windows up it, on four faces, some lit
            a = i * math.pi / 2 + (seed % 3) * 0.1
            for k, y in enumerate((shaft * 0.35, shaft * 0.7)):
                lit = (seed + i + k) % 3 != 0
                with r.at(0, 0, 0, ry=a):
                    _window(r, width / 2 + 0.02, y, 0, 0.5, 1.2, lit)
    top = shaft + 0.3
    if style == "round":
        r.part(
            "cone",
            0,
            top + height * 0.16,
            0,
            width + 0.6,
            height * 0.32,
            width + 0.6,
            SLATE,
            tex="herran_slate",
        )
        r.part("cyl", 0, top + height * 0.32 + 0.5, 0, 0.08, 1.0, 0.08, GILT)
    elif style == "octagon":
        r.part("pyramid", 0, top + height * 0.15, 0, width + 0.4, height * 0.3, width + 0.4, SLATE,
               tex="herran_slate", ry=math.pi / 8)  # fmt: skip
        r.part("pyramid", 0, top + height * 0.15, 0, width + 0.4, height * 0.3, width + 0.4, SLATE,
               tex="herran_slate", ry=math.pi / 8 + math.pi / 4)  # fmt: skip
        for i in range(4):  # lucarnes at its foot
            a = i * math.pi / 2
            with r.at(math.cos(a) * width * 0.42, top + 0.7, math.sin(a) * width * 0.42, ry=-a):
                r.part("cube", 0, 0, 0, 0.5, 1.2, 0.8, ASHLAR, tex="herran_ashlar")
                r.part("pyramid", 0, 0.8, 0, 0.6, 0.5, 0.9, SLATE_DARK)
        r.part("cyl", 0, top + height * 0.3 + 0.4, 0, 0.07, 0.8, 0.07, GILT)
    elif style == "clock":
        for i in range(4):  # a clock face on each side, its hands at a different hour on each
            a = i * math.pi / 2
            with r.at(math.cos(a) * (width / 2 + 0.06), top - 1.4, math.sin(a) * (width / 2 + 0.06), ry=-a):
                r.part("cyl", 0, 0, 0, 1.9, 0.08, 1.9, ASHLAR, rz=math.pi / 2)
                r.part("cyl", 0.04, 0, 0, 1.6, 0.06, 1.6, (238, 230, 206), rz=math.pi / 2)
                for h in range(12):
                    ha = h * math.tau / 12
                    r.part(
                        "cube", 0.08, math.sin(ha) * 0.66, math.cos(ha) * 0.66, 0.02, 0.1, 0.05, IRON, rx=-ha
                    )
                hour = (seed + i * 5) % 12 * math.tau / 12
                r.part(
                    "cube", 0.1, math.sin(hour) * 0.18, math.cos(hour) * 0.18, 0.03, 0.06, 0.4, GILT, rx=-hour
                )
                r.part("cube", 0.11, 0.26, 0, 0.03, 0.56, 0.05, GILT)
        r.part(
            "pyramid",
            0,
            top + height * 0.08,
            0,
            width + 0.3,
            height * 0.16,
            width + 0.3,
            SLATE,
            tex="herran_slate",
        )
        with r.at(0, top + height * 0.16, 0):  # the lantern on its top
            for i in range(4):
                a = i * math.pi / 2 + math.pi / 4
                r.part("cube", math.cos(a) * 0.5, 0.6, math.sin(a) * 0.5, 0.12, 1.2, 0.12, IRON)
            r.part("cube", 0, 0.6, 0, 0.7, 0.9, 0.7, WINDOW_LIT, glow=True)
            r.part("pyramid", 0, 1.45, 0, 1.3, 0.7, 1.3, SLATE_DARK)
            r.part("cyl", 0, 2.2, 0, 0.06, 0.9, 0.06, GILT)
    elif style == "belvedere":
        for i in range(8):  # the loggia's columns and arches, open on the sky
            a = i * math.tau / 8
            x, z = math.cos(a) * width * 0.42, math.sin(a) * width * 0.42
            r.part("cyl", x, top + 1.2, z, 0.24, 2.4, 0.24, ASHLAR, tex="herran_ashlar")
            r.part("cube", x, top + 2.55, z, 0.4, 0.3, 0.4, CREAM)
        r.part("cyl", 0, top + 2.85, 0, width + 0.3, 0.3, width + 0.3, ASHLAR, tex="herran_ashlar")
        r.part(
            "sphere", 0, top + 3.0, 0, width * 0.55, width * 0.5, width * 0.55, (90, 120, 110)
        )  # verdigris dome
        r.part("cyl", 0, top + 4.9, 0, 0.3, 0.6, 0.3, GILT)
        r.part("sphere", 0, top + 5.4, 0, 0.3, 0.3, 0.3, (255, 206, 96), glow=True)  # a gilt sun on its top
    else:  # needle
        for k in range(3):  # thinning in stages
            w = width * (0.7 - k * 0.18)
            y = top + k * 2.2
            r.part("cube", 0, y + 1.0, 0, w, 2.0, w, BRICK, tex="herran_brick", ry=k * 0.4)
            r.part("cube", 0, y + 2.05, 0, w + 0.2, 0.15, w + 0.2, CREAM, ry=k * 0.4)
        r.part("cone", 0, top + 6.6 + height * 0.08, 0, width * 0.3, height * 0.16, width * 0.3, SLATE)
        r.part("cyl", 0, top + 6.6 + height * 0.16 + 1.2, 0, 0.05, 2.4, 0.05, IRON)


def glasshouse(r, span_x, span_z, height):
    """The aviary's glasshouse: a barrel vault of glass in gilt iron ribs over the whole court of it
    (`span_x` by `span_z` metres from its north-west corner, its spring at `height` over the floor),
    many panes long since broken out so the drakes come and go; a ridge lantern along its crown. It
    stands on the walls either side and bears on nothing else."""
    radius = span_x / 2
    cx = span_x / 2 - 1.0  # from the NW corner tile's centre
    ribs = max(3, int(span_z / 3) + 1)
    for k in range(ribs):
        z = -1.0 + span_z * k / (ribs - 1)
        for i in range(8):  # a rib: a half-hoop of iron bars
            a0, a1 = math.pi * i / 8, math.pi * (i + 1) / 8
            p0 = (cx - math.cos(a0) * radius, height + math.sin(a0) * radius * 0.8, z)
            p1 = (cx - math.cos(a1) * radius, height + math.sin(a1) * radius * 0.8, z)
            _bar(r, p0, p1, 0.14, GILT_DARK if i % 2 else IRON)
    for i in range(8):  # purlins along it, and the panes between, some broken out
        a = math.pi * (i + 0.5) / 8
        x, y = cx - math.cos(a) * radius, height + math.sin(a) * radius * 0.8
        r.part("cube", x, y, span_z / 2 - 1.0, 0.08, 0.08, span_z, IRON)
        for k in range(ribs - 1):
            if (i * 3 + k * 5) % 4 == 0:
                continue  # broken out
            z = -1.0 + span_z * (k + 0.5) / (ribs - 1)
            r.part("cube", x, y, z, 0.03, radius * 0.8 * math.pi / 8 * 1.1, span_z / (ribs - 1) * 0.95, GLASS,
                   rz=-a)  # fmt: skip
    crown = height + radius * 0.8
    r.part("cube", cx, crown + 0.5, span_z / 2 - 1.0, 1.2, 0.9, span_z * 0.9, GLASS)  # the ridge lantern
    r.part("cube", cx, crown + 1.0, span_z / 2 - 1.0, 1.4, 0.1, span_z * 0.92, GILT)
    for side in (-1, 1):  # its gables' finials
        r.part("cyl", cx, crown + 1.5, -1.0 + (span_z if side > 0 else 0), 0.08, 1.2, 0.08, GILT)


def drake_fountain(r, seed):
    """The court's dry fountain: a quatrefoil basin of ashlar and on a pedestal in it a drake of
    bronze gone green, wings half-raised, four arms reaching out of its flanks palms up, as the old
    god holds hers; the spouts in its jaws long dry."""
    bronze = (82, 116, 96)
    dark = _dim(bronze, 0.7)
    for i in range(4):  # the quatrefoil basin
        a = i * math.pi / 2
        r.part("cyl", math.cos(a) * 0.55, 0.3, math.sin(a) * 0.55, 1.2, 0.6, 1.2, ASHLAR, tex="herran_ashlar")
    r.part("cyl", 0, 0.5, 0, 1.6, 0.25, 1.6, (70, 64, 56))  # the dry bed
    r.part("cyl", 0, 1.0, 0, 0.5, 1.2, 0.5, ASHLAR_DARK, tex="herran_ashlar")  # the pedestal
    with r.at(0, 1.6, 0, ry=seed * 0.3):
        r.part("sphere", 0, 0.5, 0, 0.5, 0.45, 0.32, bronze)  # the body
        r.part("cube", 0.35, 0.95, 0, 0.2, 0.5, 0.18, bronze, rz=-0.4)  # the neck
        r.part("cube", 0.55, 1.25, 0, 0.36, 0.18, 0.16, bronze)  # the head
        r.part("wedge", 0.78, 1.2, 0, 0.2, 0.1, 0.14, dark)  # the jaw
        for side in (-1, 1):
            r.part("wedge", -0.1, 0.95, side * 0.45, 0.7, 0.05, 0.6, dark, rx=side * 0.5)  # a wing
            for k in range(2):  # two arms each side, palms up
                y = 0.35 + k * 0.25
                _bar(r, (0.0, y, side * 0.25), (0.25, y + 0.05, side * 0.6), 0.07, bronze)
                r.part("cube", 0.28, y + 0.08, side * 0.62, 0.12, 0.03, 0.1, dark)
        r.part("cube", -0.6, 0.3, 0, 0.6, 0.12, 0.12, bronze, rz=0.3)  # the tail


def specimen_jar(r, seed):
    """A tall glass jar on a brass base in the laboratories, green fluid lit from within, and in it
    something Herran grafted: an arm, or a drake's claw with too many fingers, hung from a wire."""
    r.part("cyl", 0, 0.12, 0, 0.8, 0.24, 0.8, GILT_DARK)
    r.part("cyl", 0, 1.0, 0, 0.66, 1.5, 0.66, SPECIMEN, glow=True)
    r.part("cyl", 0, 1.0, 0, 0.7, 1.52, 0.7, GLASS)  # the glass
    r.part("cyl", 0, 1.8, 0, 0.76, 0.12, 0.76, GILT)  # the lid
    r.part("cyl", 0, 1.95, 0, 0.12, 0.2, 0.12, GILT_DARK)
    with r.at(0, 1.0, 0, ry=seed * 0.7):
        r.part("cube", 0, 0.2, 0, 0.1, 0.5, 0.1, FLESH)  # the forearm
        for f in range(3 + seed % 3):  # too many fingers
            r.part("cube", 0, -0.12, (f - 1.5) * 0.04, 0.03, 0.16, 0.025, FLESH)
        r.part("cube", 0, 0.5, 0, 0.01, 0.3, 0.01, IRON)  # the wire
    for i in range(3):  # bubbles rising in it
        r.part("sphere", 0.12 * (i - 1), 0.5 + i * 0.4, 0.1, 0.04, 0.04, 0.04, (200, 255, 200), glow=True)
    r.part("cube", 0.34, 1.0, 0, 0.02, 0.3, 0.24, (226, 214, 180))  # its label


def alembic_bench(r, seed):
    """A laboratory bench of dark oak with a tiled top: an alembic over a spirit burner, retorts and a
    rack of stoppered phials in poison colours, papers weighted with a skull of a drake."""
    oak = (70, 48, 34)
    r.part("cube", 0, 0.45, 0, 1.1, 0.9, 1.7, oak, tex="wood_plank")
    r.part("cube", 0, 0.92, 0, 1.2, 0.06, 1.8, (214, 214, 198), tex="lab_tile")
    r.part("sphere", 0.1, 1.15, -0.4, 0.34, 0.34, 0.34, (150, 200, 120), glow=True)  # the alembic's belly
    _bar(r, (0.1, 1.3, -0.4), (0.0, 1.55, 0.2), 0.05, GLASS)  # its swan neck
    r.part("cyl", 0.1, 0.98, -0.4, 0.16, 0.08, 0.16, (255, 160, 80), glow=True)  # the burner's flame
    for i in range(5):  # the phials
        tint = ((170, 60, 160), (90, 170, 220), (210, 190, 60), (110, 200, 90), (200, 70, 60))[(i + seed) % 5]
        r.part("cyl", -0.3, 1.05, 0.3 + i * 0.12, 0.07, 0.22, 0.07, tint, glow=True)
    r.part("cube", -0.25, 0.96, -0.2, 0.4, 0.02, 0.5, (226, 214, 180))  # papers
    r.part("sphere", -0.25, 1.05, -0.2, 0.16, 0.12, 0.2, (210, 200, 176))  # a drake's skull on them


def vat(r, seed):
    """A great copper vat bound in iron, its lid thrown back, something pale and half-formed in the
    green within; pipes run from it into the floor."""
    copper = (150, 90, 56)
    r.part("cyl", 0, 0.75, 0, 1.6, 1.5, 1.6, copper)
    for y in (0.3, 0.8, 1.3):
        r.part("cyl", 0, y, 0, 1.66, 0.08, 1.66, IRON)
    r.part("cyl", 0, 1.48, 0, 1.4, 0.04, 1.4, SPECIMEN, glow=True)  # the fluid's top
    r.part("sphere", 0.1, 1.5, 0.1, 0.4, 0.2, 0.3, FLESH)  # the thing in it
    r.part("cube", -0.2, 1.55, 0.3, 0.08, 0.3, 0.08, FLESH, rx=0.6)  # a reaching arm
    r.part("cyl", -0.82, 1.6, 0, 1.4, 0.06, 1.4, copper, rz=1.2)  # the lid, thrown back
    _bar(r, (0.8, 0.4, 0), (1.0, 0.0, 0), 0.12, copper)  # a pipe into the floor
    _bar(r, (0, 0.2, 0.8), (0, 0.0, 1.0), 0.12, copper)
    for i in range(4):  # rivets round its rim, and a gauge on its side
        a = i * math.pi / 2 + 0.4
        r.part("sphere", math.cos(a) * 0.82, 1.35, math.sin(a) * 0.82, 0.06, 0.06, 0.06, IRON)
    r.part("cyl", 0.82, 1.0, 0.3, 0.2, 0.04, 0.2, GILT, rz=math.pi / 2)
    r.part("cube", 0.85, 1.0, 0.3, 0.01, 0.08, 0.02, IRON, rx=0.6)  # its needle


def surgery_table(r, seed):
    """Herran's operating table: an iron table on clawed feet, straps and buckles across it, a tray of
    saws and needles at its foot, an arm lamp over it and a drain under it, stained."""
    r.part("cube", 0, 0.82, 0, 0.9, 0.08, 1.9, (130, 130, 124))  # the top
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * 0.38, 0.4, dz * 0.85, 0.08, 0.8, 0.08, IRON)
        r.part("sphere", dx * 0.38, 0.04, dz * 0.85, 0.12, 0.08, 0.12, GILT_DARK)  # a clawed foot
    for z in (-0.5, 0.0, 0.5):  # the straps
        r.part("cube", 0, 0.88, z, 0.94, 0.03, 0.1, (90, 60, 40))
        r.part("cube", 0.47, 0.88, z, 0.04, 0.08, 0.08, GILT)
    r.part("cube", 0, 0.87, 0.2, 0.6, 0.01, 0.8, (110, 40, 34))  # the stain
    r.part("cube", 0.2, 0.92, -0.85, 0.3, 0.04, 0.2, (180, 180, 176))  # the tray
    for i in range(3):
        r.part("cube", 0.12 + i * 0.07, 0.95, -0.85, 0.02, 0.01, 0.16, (220, 220, 220))
    _bar(r, (-0.45, 0.0, 0.9), (-0.45, 2.0, 0.9), 0.06, IRON)  # the lamp's arm
    _bar(r, (-0.45, 2.0, 0.9), (0.0, 1.8, 0.2), 0.05, IRON)
    r.part("cone", 0.0, 1.7, 0.2, 0.36, 0.2, 0.36, GILT_DARK)
    r.part("sphere", 0.0, 1.62, 0.2, 0.1, 0.06, 0.1, WINDOW_LIT, glow=True)


def potion_shelf(r, seed):
    """Shelves on the wall behind (-X) of stoppered bottles in every poison's colour, labels curling
    off them, and a few jars of something pickled."""
    oak = (70, 48, 34)
    with r.at(-0.85, 0, 0):
        r.part("cube", 0, 1.2, 0, 0.3, 2.4, 1.6, _dim(oak, 0.7), tex="wood_plank")  # the back
        for y in (0.5, 1.1, 1.7, 2.3):
            r.part("cube", 0.12, y, 0, 0.32, 0.05, 1.6, oak, tex="wood_plank")
        tints = ((170, 60, 160), (90, 170, 220), (210, 190, 60), (110, 200, 90), (200, 70, 60), SPECIMEN)
        for k, y in enumerate((0.5, 1.1, 1.7)):
            for i in range(5):
                tint = tints[(i + k * 2 + seed) % len(tints)]
                tall = 0.2 + ((i + k + seed) % 3) * 0.06
                r.part(
                    "cyl",
                    0.16,
                    y + 0.03 + tall / 2,
                    -0.6 + i * 0.3,
                    0.1,
                    tall,
                    0.1,
                    tint,
                    glow=(i + k) % 2 == 0,
                )


def bonesaw(r):
    """Herran's Bonesaw, grip at the origin pointing up +Y and its toothed edge on +Z (turned onto +X
    with the cleaver and the axes): a turned oak handle with a brass ferrule and heel, a long blade with
    a hooked back, too many teeth down its edge, and a stain it never lost."""
    oak = (70, 48, 34)
    steel = (176, 176, 182)
    r.part("cyl", 0, 0.0, 0, 0.07, 0.4, 0.07, oak)  # the handle
    for y in (-0.12, 0.0, 0.12):  # its turnings
        r.part("cyl", 0, y, 0, 0.085, 0.03, 0.085, _dim(oak, 0.8))
    r.part("cyl", 0, -0.22, 0, 0.09, 0.05, 0.09, GILT)  # the butt
    r.part("cyl", 0, 0.22, 0, 0.09, 0.05, 0.09, GILT)  # the ferrule
    r.part("cube", 0, 0.28, 0.03, 0.05, 0.08, 0.14, GILT_DARK)  # the heel
    r.part("cube", 0, 0.62, 0.06, 0.025, 0.66, 0.16, steel)  # the blade
    r.part("cube", 0, 0.62, -0.03, 0.035, 0.66, 0.03, _dim(steel, 0.7))  # its thick back
    r.part("cube", 0, 0.98, -0.0, 0.035, 0.08, 0.1, _dim(steel, 0.7), rx=0.6)  # the hook at its tip
    for k in range(11):  # the teeth
        r.part("wedge", 0, 0.33 + k * 0.06, 0.15, 0.02, 0.04, 0.04, (220, 220, 226), rx=math.pi / 2)
    r.part("cube", 0.014, 0.55, 0.08, 0.004, 0.18, 0.08, (110, 34, 28))  # the stain
    for y in (0.4, 0.84):  # rivets
        r.part("sphere", 0.015, y, 0.0, 0.03, 0.03, 0.03, GILT)


# --- Herran's creatures ---------------------------------------------------------------------------

DRAKE_HIDE = (92, 104, 84)  # a drake's scaled hide, grey-green
DRAKE_BELLY = (168, 150, 112)
DRAKE_WING = (70, 60, 58)
STITCH = (60, 30, 26)  # the black thread of Herran's grafts
GRAFT_SKIN = (196, 156, 134)  # the human arms sewn onto them
SUN_GOLD = (255, 200, 96)
COLD = (52, 46, 40)  # a gold glow gone out


def _windup_k(e):
    return min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0


def _graft_arm(r, x, y, z, side, reach, skin, brass):
    """A human arm sewn onto a flank: a band of brass and a seam of stitches where it joins, the upper
    arm and forearm reaching out along +X by `reach` (0 hanging, 1 thrust out), fingers spread."""
    with r.at(x, y, z):
        r.part("cyl", 0, 0, 0, 0.13, 0.05, 0.13, brass, rx=math.pi / 2)  # the band at the seam
        r.part("cube", 0.01, 0, 0, 0.02, 0.1, 0.02, STITCH)  # a stitch
        with r.at(0, 0, side * 0.05, rz=-0.9 + 1.4 * reach, rx=side * 0.3):
            r.part("cube", 0, -0.14, 0, 0.07, 0.28, 0.07, skin)
            with r.at(0, -0.28, 0, rz=0.6 - 0.5 * reach):
                r.part("cube", 0, -0.12, 0, 0.06, 0.24, 0.06, skin)
                for f in range(3):
                    r.part("cube", 0.02, -0.28, (f - 1) * 0.025, 0.02, 0.08, 0.02, skin, rz=0.2)


def drake_pose(e, t):
    """(wing beat, wing lift, body pitch, arms' reach) for a Grafted Drake, as a Bell-Harpy flies: an
    easy flap aloft, wings hauled high and body tipped down as it gathers to stoop, swept back as it
    swoops. Landed, its grafted arms reach and rake (`rend`) while its wings mantle."""
    beat = math.sin(t * 7.0)
    if getattr(e, "landed", False):
        if e.state == "windup":
            k = _windup_k(e)
            return beat * 0.15 * k, 0.4 - 1.2 * k, 0.1 + 0.2 * k, 0.3 * k
        if e.state == "attack":
            flurry = 0.5 + 0.5 * math.sin(t * 30) if e.attack_kind == "rend" else 1.0
            return 0.0, -0.3, 0.45, flurry
        if e.state in ("recover", "hurt"):
            return math.sin(t * 14.0) * 0.3, 0.2, 0.0, 0.1
        return math.sin(t * 2.0) * 0.08, 0.45, 0.15, 0.1
    if e.state == "windup":
        k = _windup_k(e)
        return beat * (1 - k) * 0.5, 0.2 + 0.8 * k, 0.45 * k, 0.4 * k
    if e.state == "attack":
        return 0.0, -0.8, 0.8, 1.0
    if e.state in ("recover", "hurt"):
        return math.sin(t * 14.0), 0.2, -0.2, 0.3
    return beat * 0.7, 0.1, 0.1, 0.2


def _drake_wing(r, side, beat, lift, rgb, membrane):
    with r.at(0, 0, 0, rx=side * (lift + beat * 0.6)):
        r.part("cube", 0, 0, side * 0.35, 0.1, 0.09, 0.7, rgb)  # the upper arm of the wing
        with r.at(0, 0, side * 0.7, rx=side * (0.3 + beat * 0.3)):
            r.part("cube", 0, 0, side * 0.4, 0.07, 0.07, 0.8, rgb)
            for i in range(3):  # its long fingers and the membrane between them
                with r.at(0, 0, side * (0.15 + i * 0.3), ry=-side * (0.5 + i * 0.25)):
                    r.part("cube", -0.45, 0, 0, 0.9, 0.04, 0.04, rgb)
                    r.part("cube", -0.45, -0.02, side * 0.12, 0.85, 0.02, 0.26, membrane)
            r.part("cone", 0.05, 0.05, side * 0.05, 0.05, 0.14, 0.05, (220, 210, 190))  # the thumb claw


def grafted_drake(r, e, t):
    """A Grafted Drake: a lean wyvern of grey-green scale, leather wings, a long neck and tail, and down
    its flanks four human arms Herran sewed on, banded in brass where they join, the seams stitched in
    black. A brass plate is riveted over one eye; the other burns sun-gold. It flies like a harpy,
    stoops once, then lands and rakes with all four arms at once. Slain, it falls in a heap of wing."""
    fall = death_fall(e, 0.7)
    dead = e.state == "dead"
    beat, lift, pitch, reach = drake_pose(e, t)
    if dead:
        beat, lift, pitch, reach = 0.0, 0.0, 0.0, 0.0
    hide = hit_tint((220, 230, 210)) if e.flashing else DRAKE_HIDE
    belly = hit_tint((240, 230, 210)) if e.flashing else DRAKE_BELLY
    skin = hit_tint((240, 220, 210)) if e.flashing else GRAFT_SKIN
    glow = not dead
    eye = (HIT_GLOW if e.flashing else SUN_GOLD) if glow else COLD
    # Slain, it drops flat on its belly and sprawls, its wings flung out flat.
    with r.at(0, 0.9 - 0.62 * fall, 0, rz=-pitch * (1 - fall)):
        r.part("sphere", 0, 0.1, 0, 0.7, 0.42, 0.42, hide)  # the body
        r.part("sphere", 0.05, 0.0, 0, 0.55, 0.3, 0.34, belly)  # its pale belly
        for i in range(4):  # the ridge of plates down its back
            r.part("wedge", 0.25 - i * 0.18, 0.3, 0, 0.12, 0.1, 0.04, _dim(hide, 0.7))
        for side in (-1, 1):  # the hind legs, clawed
            with r.at(-0.15, -0.1, side * 0.18, rz=0.4 - 0.8 * reach * (1 - fall) + 1.1 * fall):
                r.part("cube", 0, -0.18, 0, 0.12, 0.36, 0.12, hide)
                r.part("cube", 0.06, -0.38, 0, 0.18, 0.06, 0.1, _dim(hide, 0.8))
                for k in (-1, 1):
                    r.part("cone", 0.16, -0.38, k * 0.04, 0.03, 0.1, 0.03, (220, 210, 190), rz=-1.3)
            for k in range(2):  # the grafted arms, two down each flank
                _graft_arm(
                    r, 0.2 - k * 0.28, -0.02, side * 0.32, side, reach * (1 - fall) + 1.75 * fall, skin, GILT
                )
            with r.at(0.1, 0.25, side * 0.18):
                _drake_wing(r, side, beat * (1 - fall), lift * (1 - fall), hide, DRAKE_WING)
        for i in range(4):  # the tail, tapering
            r.part("cube", -0.45 - i * 0.22, 0.05 - i * 0.03, 0, 0.26, 0.14 - i * 0.025, 0.14 - i * 0.025, hide,
                   rz=0.1 * math.sin(t * 2 + i))  # fmt: skip
        r.part("wedge", -1.35, 0.0, 0, 0.18, 0.04, 0.16, _dim(hide, 0.7))  # the tail's barb
        with r.at(0.45, 0.25, 0, rz=(0.5 - 0.6 * pitch) * (1 - fall) - 0.2 * fall):  # the neck and head
            r.part("cube", 0.18, 0, 0, 0.36, 0.14, 0.14, hide)
            with r.at(0.4, 0.04, 0, rz=-0.5):
                r.part("cube", 0.1, 0, 0, 0.3, 0.13, 0.14, hide)  # the skull
                r.part("wedge", 0.27, -0.05, 0, 0.16, 0.05, 0.12, belly)  # the jaw
                for side in (-1, 1):
                    r.part(
                        "cone", -0.05, 0.1, side * 0.05, 0.03, 0.14, 0.03, (220, 210, 190), rz=1.9
                    )  # horns
                r.part(
                    "cyl", 0.12, 0.04, 0.075, 0.08, 0.02, 0.08, GILT, rx=math.pi / 2
                )  # the plate over one eye
                r.part("cube", 0.13, 0.04, -0.075, 0.05, 0.04, 0.02, eye, glow=glow)  # the other, burning


def magus_pose(e, t):
    """(arms raised 0..1, staff thrust 0..1, lean) for a Drake Magus: idle it holds its staff level in
    two hands and its other four open palm up, as the old god's; casting it raises the upper four
    overhead and thrusts the orrery-staff at you."""
    if e.state == "windup":
        k = _windup_k(e)
        return k, 0.2 * k, -0.1 * k
    if e.state == "attack":
        return 1.0, 1.0, 0.2
    if e.state in ("recover", "hurt"):
        return 0.3, 0.0, -0.1
    return 0.1 + 0.05 * math.sin(t * 1.5), 0.0, 0.0


def drake_magus(r, e, t):
    """A Drake Magus: a drake grown upright on Herran's tables, in the tattered black gown and hood of a
    natural philosopher, a drake's long snout jutting from the hood with a gilt pince-nez on it, six
    arms in three pairs (two hold a staff crowned with a brass orrery whose little sun burns gold, the
    four others held open palm up, Lyra's gesture) and a scaled tail dragging behind. It casts with its
    upper arms raised and the staff thrust out. Slain, it crumples into its gown."""
    fall = death_fall(e, 0.8)
    dead = e.state == "dead"
    raised, thrust, lean = magus_pose(e, t) if not dead else (0.0, 0.0, 0.0)
    gown = hit_tint((120, 110, 120)) if e.flashing else (36, 32, 40)
    trim = (120, 86, 42)
    hide = hit_tint((220, 230, 210)) if e.flashing else DRAKE_HIDE
    glow = not dead
    sun = (HIT_GLOW if e.flashing else SUN_GOLD) if glow else COLD
    with r.at(0, 0.5 * fall, 0, rz=-1.35 * fall):  # slain, it topples back onto its gown
        r.part("cone", 0, 0.6 * (1 - fall * 0.3), 0, 0.9, 1.2, 0.8, gown)  # the gown's skirts
        r.part("cyl", 0, 0.05, 0, 0.92, 0.06, 0.82, trim)  # its hem, gilt-edged
        for i in range(3):  # the rags of its hem
            r.part("cube", 0.2 - i * 0.2, 0.15, 0.4 - i * 0.4, 0.15, 0.3, 0.04, _dim(gown, 0.8), ry=i)
        for i in range(3):  # the tail dragging behind
            r.part("cube", -0.5 - i * 0.2, 0.1 - i * 0.02, 0, 0.24, 0.12 - i * 0.02, 0.12 - i * 0.02, hide)
        with r.at(0, 1.25, 0, rz=lean):
            r.part("cube", 0, 0.2, 0, 0.36, 0.6, 0.5, gown)  # the chest
            r.part("cube", 0.17, 0.2, 0, 0.04, 0.56, 0.08, trim)  # the gown's facing
            r.part("cube", 0, 0.5, 0, 0.4, 0.12, 0.62, _dim(gown, 0.85))  # the shoulders
            with r.at(0.08, 0.72, 0):  # the hood and the snout from it
                r.part("sphere", 0, 0, 0, 0.3, 0.32, 0.3, gown)
                r.part("cube", 0.22, -0.04, 0, 0.36, 0.12, 0.14, hide)  # the snout
                r.part("wedge", 0.35, -0.11, 0, 0.18, 0.04, 0.12, _dim(hide, 0.8))  # the jaw
                for side in (-1, 1):
                    r.part(
                        "cyl", 0.22, 0.03, side * 0.06, 0.06, 0.01, 0.06, GILT, rx=math.pi / 2
                    )  # pince-nez
                    r.part("cube", 0.2, 0.03, side * 0.08, 0.02, 0.025, 0.02, sun, glow=glow)  # eyes
            for k, y in enumerate((0.45, 0.25, 0.05)):  # three pairs of arms
                for side in (-1, 1):
                    with r.at(0.05, y, side * 0.28):
                        if k == 2:  # the lowest pair holds the staff
                            r.part("cube", 0.12, -0.05, -side * 0.05, 0.3, 0.07, 0.07, hide, ry=side * 0.4)
                        else:
                            up = raised * (1.3 if k == 0 else 0.9)
                            with r.at(0, 0, 0, rx=side * (0.4 + 0.3 * up), rz=-0.6 + 1.4 * up):
                                r.part("cube", 0, -0.15, 0, 0.07, 0.3, 0.07, gown)  # the sleeve
                                r.part("cube", 0, -0.33, 0, 0.06, 0.08, 0.1, hide)  # the hand, palm up
                                r.part("cube", 0.02, -0.38, 0, 0.02, 0.04, 0.1, _dim(hide, 0.8))
            with r.at(0.4 + 0.3 * thrust, 0.0, 0, rz=-0.2 - 0.9 * thrust):  # the orrery-staff
                r.part("cyl", 0, 0.2, 0, 0.05, 1.8, 0.05, (60, 44, 30))
                with r.at(0, 1.15, 0):
                    r.part("sphere", 0, 0, 0, 0.12, 0.12, 0.12, sun, glow=glow)  # its little sun
                    for i in range(3):  # the rings and planets about it
                        a = t * (1.5 - i * 0.3) + i
                        r.part("cyl", 0, 0, 0, 0.24 + i * 0.1, 0.015, 0.24 + i * 0.1, GILT, rx=0.4 * i)
                        r.part("sphere", math.cos(a) * (0.12 + i * 0.05), 0, math.sin(a) * (0.12 + i * 0.05),
                               0.04, 0.04, 0.04, GILT_DARK)  # fmt: skip


def vat_spawn(r, e, t):
    """A Vat Spawn: one of Herran's failures, crawled out of its vat. A hunched heap of pale flesh, too
    many arms of every size sprouting from it at random, a drake's half-formed head sunk in its
    shoulders, green fluid still running off it, a brass tag wired to it. It drags itself on its arms
    and heaves up to smash down. Slain, it slumps into a puddle of itself."""
    fall = death_fall(e, 0.7)
    dead = e.state == "dead"
    flesh = hit_tint((240, 220, 210)) if e.flashing else (186, 160, 144)
    dark = _dim(flesh, 0.75)
    glow = not dead
    fluid = SPECIMEN if glow else (70, 90, 60)
    heave = 0.0
    if e.state == "windup":
        heave = _windup_k(e)
    elif e.state == "attack":
        heave = -0.5
    squash = 1 - 0.55 * fall
    with r.at(0, 0, 0):
        r.part("sphere", 0, 0.6 * squash, 0, 1.1, 0.9 * squash + 0.2 * heave, 1.0, flesh)  # the heap
        r.part("sphere", -0.15, 0.45 * squash, 0.1, 0.8, 0.6 * squash, 0.8, dark)
        r.part("cyl", 0, 0.02, 0, 1.5 + fall, 0.03, 1.3 + fall, fluid, glow=glow)  # the puddle round it
        for i in range(3):  # fluid running off it
            r.part(
                "cube",
                0.3 - i * 0.3,
                0.5 * squash,
                0.45 - i * 0.2,
                0.04,
                0.4 * squash,
                0.04,
                fluid,
                glow=glow,
            )
        with r.at(0.35, (1.0 + 0.3 * heave) * squash, 0, rz=-0.3):  # the half-formed head
            r.part("cube", 0.15, 0, 0, 0.36, 0.2, 0.22, flesh)
            r.part("wedge", 0.32, -0.08, 0, 0.18, 0.06, 0.16, dark)
            r.part("sphere", 0.2, 0.08, 0.08, 0.05, 0.05, 0.05, fluid, glow=glow)  # its one eye
        arms = ((0.3, 0.6, 0.45, 1.0), (0.3, 0.6, -0.45, 1.0), (0.0, 0.9, 0.5, 0.7), (-0.2, 0.7, -0.5, 0.8),
                (0.5, 0.3, 0.2, 0.6), (-0.4, 0.4, 0.3, 0.5), (0.1, 1.1, -0.3, 0.55))  # fmt: skip
        for i, (x, y, z, size) in enumerate(arms):  # arms of every size, at random
            reach = heave * (1 if i < 2 else 0.5) + 0.1 * math.sin(t * 2 + i)
            with r.at(x, y * squash, z, rz=-1.2 + 1.6 * reach - fall, rx=math.copysign(0.5, z)):
                r.part("cube", 0, -0.25 * size, 0, 0.1 * size, 0.5 * size, 0.1 * size, flesh)
                r.part("cube", 0, -0.5 * size, 0, 0.12 * size, 0.06, 0.16 * size, dark)  # the hand
        r.part("cube", 0.5, 0.7 * squash, -0.3, 0.02, 0.12, 0.08, GILT)  # the brass tag
        r.part("cube", 0.46, 0.8 * squash, -0.3, 0.06, 0.01, 0.01, IRON)  # its wire


def sunbrand(r, glow, flame, t, radius=1.3):
    """A Drake Magus's sunbrand (`hazards.Eruption` style "sun"): a ring of gold glyphs kindles on the
    floor round you (`glow` 0..1), then a column of sunlight bursts up out of it (`flame` 0..1)."""
    for i in range(10):
        a = i * math.tau / 10 + t * 0.5
        r.part("cube", math.cos(a) * radius, 0.03, math.sin(a) * radius, 0.24, 0.02, 0.07,
               _dim(SUN_GOLD, 0.3 + 0.7 * glow), ry=-a, glow=True)  # fmt: skip
    r.part(
        "cyl",
        0,
        0.02,
        0,
        radius * 1.7 * glow,
        0.01,
        radius * 1.7 * glow,
        _dim(SUN_GOLD, 0.35 * glow),
        glow=True,
    )
    if flame > 0:
        r.part(
            "cyl", 0, 2.0 * flame, 0, radius * 1.4, 4.0 * flame, radius * 1.4, _dim(SUN_GOLD, 0.7), glow=True
        )
        r.part("cyl", 0, 2.2 * flame, 0, radius * 0.6, 4.4 * flame, radius * 0.6, (255, 240, 200), glow=True)


# --- Herran, the Many-Handed ------------------------------------------------------------------------

COAT = (54, 40, 46)  # the rags of a natural philosopher's frock coat, once plum
HERRAN_SKIN = (204, 186, 170)
GRAFT_SEAM = (120, 40, 36)
EYE_GOLD = (255, 214, 110)
BRACE = (170, 130, 70)  # the brass surgical braces that hold him together


def herran_pose(e, t):
    """(spread, lift, reach, plunge, lean, gaze) for Herran's eight grafted arms and his body: idle, the
    arms fanned and swaying; gathering a move, drawn up and back; then each move's own stroke: the
    `grasp_sweep` rakes them round low, `hand_rain` plunges them into the floor, `elixir_hurl` flings
    one high, `embrace` clamps them all forward together and `solar_gaze` throws them wide while he
    leans in, his eyes blazing."""
    sway = math.sin(t * 1.3) * 0.12
    kind = getattr(e, "attack_kind", None)
    if e.state == "windup":
        k = _windup_k(e)
        return 0.8 + 0.2 * k, 0.4 + 0.6 * k, -0.4 * k, 0.0, -0.15 * k, 0.4 * k
    if e.state == "attack":
        if kind == "grasp_sweep":
            return 1.2, -0.4, 0.9, 0.0, 0.2, 0.2
        if kind == "hand_rain":
            return 0.6, -0.2, 0.6, 1.0, 0.4, 0.2
        if kind == "elixir_hurl":
            return 0.9, 0.9, 1.0, 0.0, 0.1, 0.3
        if kind == "embrace":
            return 0.2, 0.2, 1.2, 0.0, 0.35, 0.5
        if kind == "solar_gaze":
            return 1.4, 0.6, 0.2, 0.0, 0.45, 1.0
        return 0.8, 0.0, 1.0, 0.0, 0.3, 0.2
    if e.state in ("recover", "hurt"):
        return 0.9 + sway, 0.1, 0.1, 0.0, -0.1, 0.0
    return 0.9 + sway, 0.2 + sway, 0.0, 0.0, 0.0, 0.0


def _herran_arm(r, i, spread, lift, reach, plunge, skin, seam, glow, raging):
    """The `i`th of his eight grafted arms, out of his back: upper arm and forearm (`_bar`s), a seam
    where it was sewn on, a hand of long fingers."""
    side = 1 if i % 2 else -1
    rank = i // 2  # 0 the topmost pair, 3 the lowest
    root = (-0.25, 3.05 - rank * 0.32, side * (0.28 + rank * 0.05))
    out = 0.35 + 0.35 * rank
    fan = spread * (0.5 + 0.28 * rank)
    elbow = (
        root[0] + 0.3 + 0.7 * reach,
        root[1] + (0.6 - 0.3 * rank) * lift - 0.8 * plunge,
        root[2] + side * (out + fan),
    )
    hand_at = (
        elbow[0] + 0.5 + 0.9 * reach + 0.4 * plunge,
        elbow[1] - 0.5 + 0.9 * lift - (elbow[1] - 0.1) * plunge,
        elbow[2] + side * (0.3 + 0.6 * fan) * (1 - 0.5 * reach),
    )
    thick = 0.13 - rank * 0.015
    _bar(r, root, elbow, thick, skin)
    _bar(r, elbow, hand_at, thick * 0.85, skin)
    r.part("cyl", *root, thick * 1.8, 0.06, thick * 1.8, seam, glow=raging and glow)  # the seam at its root
    r.part("sphere", *elbow, thick * 1.2, thick * 1.2, thick * 1.2, _dim(skin, 0.85))  # the elbow
    with r.at(*hand_at):
        r.part("cube", 0, 0, 0, 0.16, 0.1, 0.14, skin)  # the palm
        for f in range(4):  # long fingers
            r.part("cube", 0.12, -0.02, (f - 1.5) * 0.045, 0.16, 0.025, 0.025, skin, rz=-0.3)


def herran(r, e, t):
    """Herran, the Many-Handed: Lyra's son, a towering gaunt figure in the rags of a natural
    philosopher's frock coat, on long thin legs; eight grafted arms (a drake's, men's, his own) fan out
    of his back, sewn on at seams that weep; his head is split open into a crown of lidless gold eyes,
    and brass surgical braces strap his ribs and his neck together. In his second phase the braces
    have burst and hang loose, every seam burns gold, his eyes blaze and his crown of them opens wider.
    Slain, he folds to his knees and slumps forward, his arms spread on the floor round him."""
    fall = death_fall(e, 1.0)
    dead = e.state == "dead"
    raging = bool(getattr(e, "phase2", False)) and not dead
    spread, lift, reach, plunge, lean, gaze = herran_pose(e, t) if not dead else (0.8, 0.6, 0.2, 0, 0, 0)
    skin = hit_tint((250, 230, 220)) if e.flashing else HERRAN_SKIN
    coat = hit_tint((150, 120, 130)) if e.flashing else COAT
    glow = not dead
    eye = (HIT_GLOW if e.flashing else EYE_GOLD) if glow else COLD
    seam = EYE_GOLD if raging else GRAFT_SEAM
    kneel = fall  # slain, his legs fold and he sinks
    for side in (-1, 1):  # the long thin legs
        with r.at(0, 1.6 - 1.0 * kneel, side * 0.3, rz=0.9 * kneel):
            r.part("cube", 0, -0.4, 0, 0.16, 0.8, 0.16, coat)  # the thigh, in its breeches
            with r.at(0, -0.8, 0, rz=-2.45 * kneel):  # kneeling, the shin lies along the floor behind
                r.part("cube", 0, -0.4, 0, 0.12, 0.8, 0.12, skin)  # the shin, bare and gaunt
                r.part("cube", 0.1, -0.82, 0, 0.32, 0.06, 0.14, _dim(skin, 0.8))  # the long foot
    # Everything above the hips, turned about them: leaning into a move, or slumped forward in death.
    with r.at(0, 1.75 - 1.0 * kneel, 0, rz=-lean - 0.6 * fall), r.at(0, -1.75, 0):
        r.part("cube", 0, 1.75, 0, 0.42, 0.3, 0.62, coat)  # the hips
        for side in (-1, 1):  # the coat's tails, hanging ragged
            r.part("cube", -0.18, 1.3, side * 0.18, 0.05, 0.9, 0.26, _dim(coat, 0.85), rz=0.15)
        r.part("cube", 0, 2.35, 0, 0.36, 0.95, 0.55, skin)  # the gaunt torso
        for i in range(4):  # ribs standing out
            r.part("cube", 0.17, 2.1 + i * 0.16, 0, 0.03, 0.04, 0.5, _dim(skin, 0.8))
        r.part("cube", -0.02, 2.5, 0, 0.4, 0.8, 0.64, coat)  # the coat over his back and shoulders
        r.part("cube", 0.2, 2.5, 0, 0.04, 0.7, 0.18, (226, 214, 190))  # a stained shirt-front
        if not raging:  # the braces strapped round him
            for y in (2.15, 2.45, 2.75):
                r.part("cube", 0, y, 0, 0.44, 0.05, 0.66, BRACE)
                r.part("cube", 0.22, y, 0.1, 0.03, 0.08, 0.06, _dim(BRACE, 0.7))  # its buckle
            r.part("cyl", 0.02, 3.15, 0, 0.3, 0.2, 0.3, BRACE)  # the collar round his neck
        else:  # burst, hanging loose, and the seams down his chest burning
            for y in (2.15, 2.45):
                r.part("cube", 0.2, y - 0.1, 0.25, 0.03, 0.3, 0.05, BRACE, rx=0.6)
            for i in range(3):
                r.part("cube", 0.19, 2.1 + i * 0.3, -0.1 + i * 0.08, 0.02, 0.24, 0.03, EYE_GOLD, glow=True)
        r.part("cyl", 0.02, 3.25, 0, 0.16, 0.25, 0.16, skin)  # the neck
        with r.at(0.06, 3.55, 0, rz=-0.3 * gaze):  # the head, split open into a crown of eyes
            r.part("sphere", 0, 0, 0, 0.26, 0.24, 0.24, skin)
            r.part("wedge", 0.15, -0.12, 0, 0.14, 0.08, 0.16, _dim(skin, 0.85))  # what is left of the jaw
            opened = 0.25 + (0.15 if raging else 0) + 0.1 * gaze
            for i in range(7):  # the lidless eyes, ringed up and out from the split
                a = (i - 3) * 0.42
                x, y, z = 0.12, 0.1 + math.cos(a) * opened, math.sin(a) * opened
                size = 0.07 + 0.02 * (i % 2) + (0.03 if raging else 0)
                r.part("sphere", x, y, z, size * 1.3, size * 1.3, size * 1.3, _dim(skin, 0.75))  # its socket
                r.part("sphere", x + 0.03, y, z, size, size, size, eye, glow=glow)
            if raging:  # the blaze behind them
                r.part("sphere", 0.1, 0.25, 0, 0.3, 0.3, 0.3, _dim(EYE_GOLD, 0.6), glow=True)
        with r.at(0, -0.1 * fall, 0):
            for i in range(8):
                _herran_arm(r, i, spread, lift, reach, plunge, skin, seam, glow, raging)
        if e.state == "windup" and getattr(e, "attack_kind", None) == "elixir_hurl":
            r.part("cyl", 1.2, 4.4, 0.6, 0.18, 0.3, 0.18, (120, 200, 100), glow=True)  # the flask, held high


def graft_hands(r, glow, flame, t, radius=1.0):
    """Herran's `hand_rain` (`hazards.Eruption` style "grafts"): a seam of gold splits the floor
    (`glow` 0..1), then pale arms burst up out of it, clutching (`flame` 0..1)."""
    r.part("cube", 0, 0.02, 0, radius * 1.6, 0.02, 0.12, _dim(EYE_GOLD, 0.3 + 0.7 * glow), glow=True)
    r.part("cube", 0, 0.02, 0, 0.12, 0.02, radius * 1.2, _dim(EYE_GOLD, 0.2 + 0.5 * glow), glow=True)
    if flame > 0:
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            x, z = math.cos(a) * radius * 0.45, math.sin(a) * radius * 0.45
            h = 1.4 * flame
            r.part("cube", x, h / 2, z, 0.12, h, 0.12, HERRAN_SKIN, rz=0.2 * math.sin(t * 6 + i))
            r.part("cube", x, h + 0.05, z, 0.18, 0.08, 0.16, _dim(HERRAN_SKIN, 0.85))


def elixir_splash(r, glow, flame, t, radius=1.4):
    """Herran's `elixir_hurl` (`hazards.Eruption` style "elixir"): where the flask will land a ring
    of green glows on the floor (`glow`), then it bursts into a toxic splash (`flame`)."""
    green = (120, 210, 100)
    r.part("cyl", 0, 0.02, 0, radius * 2 * glow, 0.01, radius * 2 * glow, _dim(green, 0.4), glow=True)
    if flame > 0:
        r.part(
            "sphere",
            0,
            0.4 * flame,
            0,
            radius * 1.6 * flame,
            0.8 * flame,
            radius * 1.6 * flame,
            green,
            glow=True,
        )
        for i in range(5):
            a = i * math.tau / 5 + t
            r.part("sphere", math.cos(a) * radius * flame, 0.9 * flame, math.sin(a) * radius * flame, 0.12, 0.12, 0.12,
                   (170, 240, 140), glow=True)  # fmt: skip


def elixir_flask(r, t):
    """The flask Herran lobs, tumbling as it flies."""
    with r.at(0, 0, 0, rz=t * 8):
        r.part("sphere", 0, 0, 0, 0.22, 0.22, 0.22, (120, 200, 100), glow=True)
        r.part("cyl", 0, 0.16, 0, 0.08, 0.14, 0.08, GLASS)
        r.part("cyl", 0, 0.25, 0, 0.1, 0.05, 0.1, GILT)


def herran_arch(r, style, t, lit):
    """Over Herran's door: a gilt sun held out on six bronze hands, as his mother holds hers, its face
    burning while he lives."""
    with r.at(0, 3.6, 0):
        r.part("cyl", 0, 0, 0, 0.12, 0.42, 0.42, GILT, rz=math.pi / 2)
        r.part("cyl", 0, 0, 0, 0.14, 0.26, 0.26, EYE_GOLD if lit else COLD, rz=math.pi / 2, glow=lit)
        for i in range(6):
            a = i * math.tau / 6
            r.part("cube", 0, math.sin(a) * 0.36, math.cos(a) * 0.36, 0.06, 0.1, 0.14, (110, 90, 60), rx=-a)


def herran_leaf(r, style, side, face, t, lit):
    """Dark oak panels on each leaf, studded in brass."""
    for y in (0.9, 2.1):
        r.part("cube", face * 0.085, y, -side * 0.45, 0.02, 0.8, 0.6, _dim(style.wood, 0.8))  # a panel
        r.part("sphere", face * 0.09, y, -side * 0.45, 0.04, 0.04, 0.04, style.iron)  # its stud


def spire_door(r, t):
    """The door between the castle and Herran's Spire, set into the wall behind its tile (-X) and facing
    +X: two leaves of dark oak panelled and studded in brass under a round arch of pale ashlar with a
    cream-and-red banded head, a gilt sun on its keystone and a gas lamp on a bracket either side."""
    oak = (70, 48, 34)
    with r.at(-0.92, 0, 0):
        for side in (-1, 1):
            z = side * 0.85
            r.part("cube", 0, 1.3, z, 0.4, 2.6, 0.3, ASHLAR, tex="herran_ashlar")  # the jamb
            r.part("cube", 0.04, 0.12, z, 0.5, 0.24, 0.4, ASHLAR_DARK)  # its plinth
            for k in range(3):  # quoins up it, banded
                r.part("cube", 0.02, 0.5 + k * 0.8, z, 0.44, 0.16, 0.36, CREAM)
        for i in range(7):  # the round arch's voussoirs, red and cream in turn
            a = math.pi * (i + 0.5) / 7
            r.part("cube", 0, 2.6 + math.sin(a) * 0.75, math.cos(a) * 0.75, 0.42, 0.3, 0.3,
                   BRICK if i % 2 else CREAM, rx=a - math.pi / 2)  # fmt: skip
        r.part("cube", 0.04, 3.38, 0, 0.46, 0.36, 0.32, ASHLAR, tex="herran_ashlar")  # the keystone
        r.part("cyl", 0.28, 3.38, 0, 0.24, 0.05, 0.24, GILT, rz=math.pi / 2)  # the sun on it
        r.part("cyl", 0.3, 3.38, 0, 0.14, 0.05, 0.14, SUNLIGHT, rz=math.pi / 2, glow=True)
        for side in (-1, 1):  # the leaves
            zc = side * 0.35
            r.part("cube", 0.05, 1.3, zc, 0.1, 2.6, 0.68, oak, tex="wood_plank")
            for y in (0.7, 1.8):
                r.part("cube", 0.11, y, zc, 0.02, 0.7, 0.5, _dim(oak, 0.8))  # a panel
                r.part("sphere", 0.12, y, zc, 0.04, 0.04, 0.04, GILT)  # its stud
            r.part("cyl", 0.13, 1.2, side * 0.1, 0.12, 0.025, 0.12, GILT, rz=math.pi / 2)  # a ring
        r.part("cube", 0.12, 0.03, 0, 0.5, 0.06, 1.9, ASHLAR_DARK)  # the threshold
        r.part("cube", 0.06, 2.75, 0, 0.12, 0.3, 1.3, (20, 18, 22))  # the dark of the fanlight
        for side in (-1, 1):  # gas lamps on brackets
            with r.at(0.42, 2.2, side * 1.15):
                r.part("cube", -0.15, -0.1, 0, 0.3, 0.04, 0.04, IRON, rz=-0.5)
                r.part("cube", 0, 0, 0, 0.18, 0.26, 0.18, LAMP_GLASS, glow=True)
                r.part("pyramid", 0, 0.18, 0, 0.22, 0.1, 0.22, IRON)
                flame = 0.06 + 0.01 * math.sin(t * 5 + side)
                r.part("sphere", 0, 0, 0, flame, flame * 1.4, flame, SUNLIGHT, glow=True)


def telescope(r, seed):
    """Herran's great telescope: a long brass tube on a cast-iron mount, raised toward the sky, its
    eyepiece and finder, a wheel to train it and a chair before it, pointed at the moon."""
    r.part("cyl", 0, 0.15, 0, 1.6, 0.3, 1.6, IRON)  # the base
    r.part("cube", 0, 0.9, 0, 0.4, 1.4, 0.4, IRON)  # the pier
    r.part("cube", 0, 1.65, 0, 0.6, 0.15, 0.6, GILT_DARK)  # the mount's head
    with r.at(0, 1.8, 0, rz=0.7):
        r.part("cyl", 0.6, 0, 0, 0.36, 3.6, 0.36, GILT, rz=-math.pi / 2)  # the tube
        for x in (-0.6, 0.6, 1.8):
            r.part("cyl", x, 0, 0, 0.4, 0.08, 0.4, GILT_DARK, rz=-math.pi / 2)  # its bands
        r.part("cyl", 2.45, 0, 0, 0.44, 0.15, 0.44, GILT_DARK, rz=-math.pi / 2)  # the dew cap
        r.part("cyl", 2.53, 0, 0, 0.3, 0.02, 0.3, GLASS, rz=-math.pi / 2)  # the object glass
        r.part("cyl", -1.3, 0, 0, 0.1, 0.3, 0.1, IRON, rz=-math.pi / 2)  # the eyepiece
        r.part("cyl", 0.4, 0.3, 0, 0.1, 0.9, 0.1, GILT, rz=-math.pi / 2)  # the finder
    r.part("cyl", 0.3, 1.2, 0.3, 0.4, 0.04, 0.4, IRON, rx=math.pi / 2)  # the wheel
    r.part("cube", -1.2, 0.45, 0, 0.5, 0.06, 0.5, (70, 48, 34))  # the chair's seat
    r.part("cube", -1.42, 0.8, 0, 0.06, 0.7, 0.5, (70, 48, 34))  # its back
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", -1.2 + dx * 0.2, 0.22, dz * 0.2, 0.04, 0.44, 0.04, (60, 42, 30))


def observatory_dome(r, radius, height):
    """The observatory's dome, broken open: ribs of gilt iron curving up from the parapet (`radius`
    metres out, at `height` over the floor) to an iron ring at the crown, most of its glass long gone,
    a few panes still hanging between the ribs."""
    ribs = 12
    for i in range(ribs):
        a = i * math.tau / ribs
        for k in range(5):  # each rib in five bars, up to the crown
            e0, e1 = math.pi / 2 * k / 5, math.pi / 2 * (k + 1) / 5
            p0 = (
                math.cos(a) * radius * math.cos(e0),
                height + radius * 0.8 * math.sin(e0),
                math.sin(a) * radius * math.cos(e0),
            )
            p1 = (
                math.cos(a) * radius * math.cos(e1),
                height + radius * 0.8 * math.sin(e1),
                math.sin(a) * radius * math.cos(e1),
            )
            if i % 4 == 1 and k >= 3:
                continue  # a rib broken off short
            _bar(r, p0, p1, 0.12, GILT_DARK if k % 2 else IRON)
        if i % 3 == 0:  # a pane still hanging
            e = math.pi / 2 * 0.3
            r.part("cube", math.cos(a + 0.26) * radius * math.cos(e), height + radius * 0.8 * math.sin(e),
                   math.sin(a + 0.26) * radius * math.cos(e), 0.03, 1.4, 1.6, GLASS, ry=-a - 0.26 + math.pi / 2)  # fmt: skip
    r.part("cyl", 0, height + radius * 0.8, 0, radius * 0.4, 0.15, radius * 0.4, IRON)  # the crown ring
    for i in range(ribs):  # the iron ring at its foot, rib to rib
        a0, a1 = i * math.tau / ribs, (i + 1) * math.tau / ribs
        _bar(r, (math.cos(a0) * radius, height, math.sin(a0) * radius),
             (math.cos(a1) * radius, height, math.sin(a1) * radius), 0.16, GILT_DARK)  # fmt: skip
