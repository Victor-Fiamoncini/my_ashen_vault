"""The Cinderhold's dressing: stone gargoyles on plinths, barred forge windows, the smithy's hearth,
trough, crucible, tool rack, ingots and slag, the impaling stakes on the road, a run of battlements
for the skyline and a gargoyle spout spilling lava. Pure part lists drawn through a Rig, like
`models`: props face +X, wall props hang on the wall at local -X, and the spout (like the landmarks)
faces +Z with its wall at local -Z."""

import math
import random

from ashen_vault.render.forge_models import (
    BLACK_IRON,
    CRUST,
    DARK,
    MOLTEN,
    RIVET,
    STATUE,
    STATUE_DARK,
    STONE,
    STONE_LIGHT,
    WHITE_HOT,
    _dim_rgb,
    _slit,
)
from ashen_vault.render.models import EMBER, RUST, _bar, _flame

BRICK = (86, 60, 52)
SOOT = (30, 24, 24)
TIMBER = (70, 50, 34)
HANDLE = (90, 64, 40)
STAKE = (78, 56, 38)
RAG = (92, 78, 62)
WATER = (28, 38, 44)
STEAM = (150, 150, 150)
COOL_SLAG = (40, 32, 30)
SLAG_LIGHT = (64, 48, 40)
RUBBLE = (90, 84, 80)
WARM = (180, 70, 30)  # iron just past red heat


def _flicker(t, seed, k=0.15):
    return 1 + math.sin(t * 9 + seed * 1.7) * k + math.sin(t * 23 + seed) * k * 0.5


# --- the statues ---------------------------------------------------------------------------------


def gargoyle_statue(r, t, seed, pose="hunched", detail=True):
    """A stone gargoyle crouched on a square plinth: haunches drawn up, forearms gripping the plinth's
    edge, wings folded down its back, horns sweeping back from a heavy brow. `pose="snarl"` rears the
    head and drops the jaw. All weathered stone: nothing on it glows. Without `detail` (seen from afar)
    it leaves off what no one could make out there: claws, fangs, eyes, horn tips and tail."""
    rear, jaw = (0.45, 0.55) if pose == "snarl" else (-0.15, 0.08)
    turn = ((seed % 3) - 1) * 0.3
    # The plinth: a skirt, a shaft with a carved panel on its face, a cap.
    r.part("cube", 0, 0.08, 0, 1.0, 0.16, 1.0, STATUE_DARK)
    r.part("cube", 0, 0.5, 0, 0.86, 0.68, 0.86, STATUE)
    r.part("cube", 0, 0.88, 0, 0.96, 0.08, 0.96, STATUE_DARK)
    if detail:
        r.part("cube", 0.435, 0.5, 0, 0.02, 0.44, 0.52, STATUE_DARK)
        r.part("cube", 0.44, 0.3 + (seed % 4) * 0.1, (seed % 5 - 2) * 0.15, 0.02, 0.22, 0.03, SOOT, rx=0.5)
    with r.at(0, 0.92, 0):
        for side in (-1, 1):  # haunches and taloned feet
            r.part("cube", 0.12, 0.05, side * 0.22, 0.38, 0.1, 0.16, STATUE_DARK)
            for c in (-0.05, 0.0, 0.05) if detail else ():
                r.part("cone", 0.34, 0.04, side * 0.22 + c, 0.04, 0.12, 0.04, STATUE_DARK, rz=-math.pi / 2)
            r.part("cube", -0.08, 0.26, side * 0.24, 0.24, 0.44, 0.2, STATUE, rz=0.7)
        with r.at(-0.05, 0.3, 0, rz=-0.45):  # the hunched body
            r.part("cube", 0, 0.3, 0, 0.5, 0.7, 0.54, STATUE)
            r.part("cube", 0.22, 0.25, 0, 0.1, 0.5, 0.36, STATUE_DARK)  # its plated belly
            for i in range(3 if detail else 0):
                r.part("wedge", -0.27, 0.15 + i * 0.2, 0, 0.12, 0.14, 0.05, STATUE_DARK, rz=math.pi / 2 + 0.4)
            for side in (-1, 1):  # wings folded down the back: a knuckle above the shoulder, the
                with r.at(-0.2, 0.5, side * 0.24, rz=0.7, rx=side * 0.12):  # membrane hanging behind
                    r.part("cube", 0, 0.12, 0, 0.1, 0.36, 0.08, STATUE_DARK)
                    r.part("wedge", 0, 0.34, 0, 0.06, 0.1, 0.06, STATUE_DARK)
                    r.part("wedge", -0.06, -0.3, side * 0.03, 0.3, 0.9, 0.03, STATUE, rz=math.pi)
                    r.part("cube", -0.1, -0.25, side * 0.05, 0.04, 0.7, 0.04, STATUE_DARK, rz=0.2)
            with r.at(0.22, 0.66, 0, rz=0.45 + rear, ry=turn):  # the head
                r.part("cube", 0.1, 0, 0, 0.34, 0.28, 0.32, STATUE)
                r.part("cube", 0.16, 0.12, 0, 0.26, 0.07, 0.36, STATUE_DARK)  # brow
                r.part("cube", 0.31, -0.03, 0, 0.2, 0.15, 0.24, STATUE)  # snout
                if detail:
                    r.part("cube", 0.41, 0.02, 0, 0.03, 0.05, 0.12, STATUE_DARK)  # nostrils
                for side in (-1, 1):
                    if detail:
                        r.part("cube", 0.27, 0.06, side * 0.09, 0.03, 0.04, 0.06, SOOT)  # hollow eyes
                        r.part(
                            "wedge", 0.37, -0.13, side * 0.07, 0.03, 0.09, 0.03, STATUE, rz=math.pi
                        )  # fang
                    r.part("wedge", 0.0, -0.02, side * 0.18, 0.05, 0.14, 0.05, STATUE_DARK, rx=side * 1.8)
                    with r.at(-0.02, 0.12, side * 0.13, rx=-side * 0.5, rz=0.5):  # a horn, sweeping back
                        r.part("lozenge", 0, 0.1, 0, 0.07, 0.2, 0.07, STATUE_DARK)
                        with r.at(0, 0.18, 0, rz=0.9):
                            r.part("lozenge", 0, 0.07, 0, 0.05, 0.15, 0.05, STATUE_DARK)
                            if detail:
                                r.part("wedge", 0, 0.17, 0, 0.04, 0.08, 0.04, STATUE_DARK, rz=0.4)
                with r.at(0.1, -0.12, 0, rz=-jaw):
                    r.part("cube", 0.16, -0.03, 0, 0.32, 0.07, 0.24, STATUE_DARK)
                    for side in (-1, 1) if detail else ():
                        r.part("wedge", 0.28, 0.03, side * 0.07, 0.03, 0.07, 0.03, STATUE)
                    if jaw > 0.3:  # the gullet, a dark hollow in the stone
                        r.part("cube", 0.12, 0.04, 0, 0.22, 0.04, 0.18, SOOT)
        for side in (-1, 1):  # forearms, bent at the elbow, claws hooked over the plinth's edge
            shoulder, elbow, hand = (
                (0.3, 0.75, side * 0.28),
                (0.24, 0.4, side * 0.3),
                (0.42, 0.06, side * 0.26),
            )
            _bar(r, shoulder, elbow, 0.13, STATUE)
            _bar(r, elbow, hand, 0.11, STATUE_DARK)
            r.part("cube", 0.44, 0.04, side * 0.26, 0.14, 0.08, 0.14, STATUE_DARK)
            for c in (-0.04, 0.0, 0.04) if detail else ():
                r.part("cone", 0.5, -0.04, side * 0.26 + c, 0.03, 0.1, 0.03, STATUE_DARK, rz=math.pi)
        if not detail:
            return
        for i, (x, z, a) in enumerate(
            ((-0.3, 0.06, 0.3), (-0.4, 0.2, 1.0), (-0.38, 0.34, 1.6), (-0.26, 0.42, 2.2))
        ):
            r.part("cube", x, 0.05, z, 0.16, 0.09 - i * 0.01, 0.11, STATUE_DARK, ry=-a)  # the tail
        r.part("wedge", -0.14, 0.05, 0.44, 0.06, 0.12, 0.03, STATUE, rz=-math.pi / 2)


# --- the forge -----------------------------------------------------------------------------------


def barred_window(r, t, seed):
    """A pointed window slit in the wall behind (-X), framed in pale stone and crossed by iron bars,
    with a forge's dim glow flickering behind them."""
    k = 0.45 + 0.12 * _flicker(t, seed)
    glow = _dim_rgb(MOLTEN, min(k, 1.0))
    r.part("cube", -0.98, 2.25, 0, 0.02, 1.3, 0.62, glow, glow=True)  # the light behind
    r.part("wedge", -0.98, 3.08, 0, 0.62, 0.36, 0.02, glow, ry=math.pi / 2, glow=True)  # its pointed head
    r.part("cube", -0.96, 1.62, 0, 0.02, 0.06, 0.6, WHITE_HOT if k > 0.6 else MOLTEN, glow=True)  # sill glare
    for z in (-0.42, 0.42):  # jambs
        r.part("cube", -0.9, 2.3, z, 0.18, 1.5, 0.2, STONE_LIGHT)
    r.part("cube", -0.89, 1.52, 0, 0.2, 0.12, 1.04, STONE_LIGHT)  # sill
    for side in (-1, 1):  # the pointed arch: two leaning stones under a keystone
        r.part("cube", -0.9, 3.18, side * 0.2, 0.18, 0.18, 0.56, STONE_LIGHT, rx=side * 0.6)
    r.part("cube", -0.89, 3.38, 0, 0.2, 0.2, 0.18, STONE)
    for z in (-0.18, 0.0, 0.18):
        r.part("cyl", -0.88, 2.35, z, 0.04, 1.6 - abs(z), 0.04, BLACK_IRON)
    for y in (2.0, 2.7):
        r.part("cyl", -0.88, y, 0, 0.04, 0.68, 0.04, BLACK_IRON, rx=math.pi / 2)
    u = (t * 0.6 + seed * 0.37) % 1.0  # a spark drifting out
    r.part(
        "cube", -0.86 + 0.3 * u, 2.5 + 0.9 * u, math.sin(seed + t) * 0.2, 0.03, 0.03, 0.03, EMBER, glow=True
    )


def forge_hearth(r, t, seed):
    """A big brick forge: a block with a mouth of glowing coal on its face (+X), a bed of coals on
    top under a sloping iron hood held up on posts, a flue rising from the hood, and a leather bellows
    at one side."""
    f = _flicker(t, seed)
    r.part("cube", -0.1, 0.5, 0, 1.6, 1.0, 1.7, BRICK, tex="stone_brick")
    r.part("cube", -0.1, 1.04, 0, 1.7, 0.08, 1.8, DARK)  # the iron rim of the firebed
    # The mouth: a sooty recess, a lintel over it, coals heaped inside.
    r.part("cube", 0.69, 0.42, 0, 0.04, 0.5, 0.8, SOOT)
    r.part("cube", 0.72, 0.74, 0, 0.12, 0.14, 1.0, STONE_LIGHT)
    for z in (-0.46, 0.46):
        r.part("cube", 0.72, 0.4, z, 0.12, 0.6, 0.12, STONE_LIGHT)
    r.part("cube", 0.66, 0.26, 0, 0.1, 0.12, 0.72, MOLTEN, glow=True)
    for i in range(4):
        z = -0.27 + i * 0.18
        hot = WHITE_HOT if (i + seed) % 3 == 0 else MOLTEN
        s = 0.1 * (1 + 0.15 * math.sin(t * 7 + i * 2.1))
        r.part("sphere", 0.67, 0.34, z, s, s, s, hot, glow=True)
    # The firebed on top and the flames over it.
    r.part("cube", -0.1, 1.1, 0, 1.0, 0.06, 1.0, _dim_rgb(MOLTEN, min(0.7 + 0.2 * f, 1.0)), glow=True)
    for x, z in ((-0.3, -0.2), (0.1, 0.25)):
        r.part("sphere", x, 1.14, z, 0.22, 0.1, 0.22, WHITE_HOT, glow=True)
    _flame(r, -0.15, 1.3, 0.0, 0.16 * f, t)
    _flame(r, 0.15, 1.24, -0.25, 0.1 * f, t + 1.3)
    for i in range(3):  # embers rising into the hood
        u = (t * 0.7 + i / 3 + seed * 0.21) % 1.0
        r.part("cube", math.sin(i * 2.3 + t) * 0.3, 1.2 + 0.8 * u, math.cos(i * 1.9) * 0.3,
               0.04, 0.04, 0.04, EMBER, glow=True)  # fmt: skip
    # The hood: four sloping plates over the bed, held on two posts at the back.
    for x in (-0.82, 0.62):
        for z in (-0.78, 0.78):
            r.part("cube", x, 1.5, z, 0.08, 0.9, 0.08, BLACK_IRON)
    r.part("cube", -0.1, 1.95, 0, 1.8, 0.1, 1.8, BLACK_IRON)  # the hood's lip
    for side in (-1, 1):
        r.part("cube", -0.1 + side * 0.5, 2.3, 0, 0.05, 0.75, 1.3, DARK, rz=-side * 0.7, tex="iron_plate")
        r.part("cube", -0.1, 2.3, side * 0.5, 1.3, 0.75, 0.05, DARK, rx=side * 0.7, tex="iron_plate")
    r.part("cube", -0.1, 2.85, 0, 0.5, 0.6, 0.5, BRICK, tex="stone_brick")  # the flue
    r.part("cube", -0.1, 3.18, 0, 0.6, 0.08, 0.6, DARK)
    # The bellows, on the side the seed picks.
    side = 1 if seed % 2 else -1
    with r.at(0.2, 0.75, side * 0.88):
        r.part("wedge", 0, 0, 0, 0.6, 0.12, 0.08, (96, 60, 40), rz=-math.pi / 2)
        r.part("cube", -0.38, 0, 0, 0.24, 0.05, 0.05, HANDLE)


def quench_trough(r, t):
    """A riveted iron trough of dark water for quenching, steam curling off its surface."""
    for z in (-0.6, 0.6):  # feet
        r.part("cube", 0, 0.05, z, 0.66, 0.1, 0.12, DARK)
    r.part("cube", 0, 0.12, 0, 0.6, 0.06, 1.6, BLACK_IRON)  # the floor of it
    for x in (-0.28, 0.28):
        r.part("cube", x, 0.35, 0, 0.04, 0.5, 1.6, BLACK_IRON, tex="iron_plate")
    for z in (-0.78, 0.78):
        r.part("cube", 0, 0.35, z, 0.6, 0.5, 0.04, BLACK_IRON, tex="iron_plate")
    for x in (-0.3, 0.3):  # the rolled rim and the rivets along it
        r.part("cube", x, 0.6, 0, 0.06, 0.04, 1.64, DARK)
        for i in range(5):
            r.part("cube", x * 1.04, 0.5, -0.64 + i * 0.32, 0.03, 0.04, 0.04, RIVET)
    r.part("cube", 0, 0.5, 0, 0.52, 0.02, 1.52, WATER)
    _bar(r, (0.3, 0.62, 0.2), (-0.05, 0.42, 0.55), 0.03, BLACK_IRON)  # tongs left in the water
    _bar(r, (0.3, 0.62, 0.26), (-0.05, 0.42, 0.5), 0.03, BLACK_IRON)
    for i in range(2):  # steam puffs swelling as they rise
        u = (t * 0.4 + i * 0.5) % 1.0
        s = 0.12 + 0.2 * u
        r.part("sphere", math.sin(t + i * 2) * 0.1, 0.6 + 0.9 * u, -0.3 + i * 0.6, s, s * 0.7, s, STEAM)


def crucible(r, t):
    """An iron crucible on a three-legged stand over a bed of coals: a pour lip, ring handles, and
    molten metal glowing at its brim, bubbling."""
    for i in range(3):
        a = i * 2 * math.pi / 3
        _bar(r, (math.cos(a) * 0.36, 0.62, math.sin(a) * 0.36), (math.cos(a) * 0.5, 0.0, math.sin(a) * 0.5),
             0.05, BLACK_IRON)  # fmt: skip
    r.part("cyl", 0, 0.62, 0, 0.78, 0.05, 0.78, BLACK_IRON)  # the stand's ring
    for i in range(5):  # the coals beneath
        a = i * 1.3
        hot = WHITE_HOT if i % 3 == 0 else MOLTEN
        s = 0.1 + 0.02 * math.sin(t * 6 + i)
        r.part("sphere", math.cos(a) * 0.18, 0.06, math.sin(a) * 0.18, s * 1.4, s, s * 1.4, hot, glow=True)
    _flame(r, 0, 0.2, 0, 0.09, t)
    r.part("sphere", 0, 0.7, 0, 0.5, 0.3, 0.5, DARK)  # the pot's round belly
    r.part("cyl", 0, 0.88, 0, 0.6, 0.36, 0.6, DARK)
    r.part("cyl", 0, 0.98, 0, 0.64, 0.05, 0.64, BLACK_IRON)  # a band below the brim
    r.part("cyl", 0, 1.06, 0, 0.5, 0.02, 0.5, MOLTEN, glow=True)  # the melt
    r.part("wedge", 0.33, 1.05, 0, 0.14, 0.12, 0.16, DARK, rz=-math.pi / 2)  # the pour lip
    r.part("cube", 0.32, 1.065, 0, 0.12, 0.01, 0.06, MOLTEN, glow=True)
    for z in (-0.33, 0.33):  # ring handles
        r.part("cyl", 0, 0.92, z, 0.14, 0.03, 0.14, BLACK_IRON, rx=math.pi / 2)
    for i in range(3):  # bubbles swelling and bursting on the surface
        u = (t * 1.3 + i / 3) % 1.0
        s = 0.03 + 0.06 * u
        r.part(
            "sphere", math.cos(i * 2.2) * 0.12, 1.07, math.sin(i * 2.2) * 0.12, s, s, s, WHITE_HOT, glow=True
        )


def tool_rack(r, t, seed):
    """A board on the wall behind (-X) with a smith's tools hung from iron pegs: tongs, two hammers,
    a hooked poker and a file."""
    r.part("cube", -0.94, 1.7, 0, 0.06, 1.0, 1.4, TIMBER, tex="wood_plank")
    for y in (1.35, 2.05):
        r.part("cube", -0.9, y, 0, 0.02, 0.06, 1.42, BLACK_IRON)
    tools = ["tongs", "hammer", "poker", "sledge", "file"]
    shift = seed % len(tools)
    tools = tools[shift:] + tools[:shift]
    for i, tool in enumerate(tools):
        z = -0.52 + i * 0.26
        r.part("cyl", -0.86, 2.05, z, 0.04, 0.1, 0.04, BLACK_IRON, rz=math.pi / 2)  # the peg
        sway = math.sin(t * 0.8 + i * 1.7) * 0.03
        with r.at(-0.84, 2.05, z, rx=sway):
            if tool == "tongs":
                for s in (-1, 1):
                    r.part("cube", 0, -0.35, s * 0.03, 0.03, 0.6, 0.02, BLACK_IRON, rx=s * 0.06)
                    r.part("cube", 0, -0.72, s * 0.035, 0.03, 0.16, 0.03, DARK, rx=-s * 0.3)
                r.part("cube", 0, -0.62, 0, 0.04, 0.04, 0.06, RIVET)  # the pivot
            elif tool in ("hammer", "sledge"):
                big = tool == "sledge"
                r.part("cube", 0, -0.3, 0, 0.04, 0.5 if big else 0.4, 0.04, HANDLE)
                r.part("cube", 0, -0.6 if big else -0.52, 0, 0.1, 0.12 if big else 0.08,
                       0.22 if big else 0.16, BLACK_IRON)  # fmt: skip
            elif tool == "poker":
                r.part("cyl", 0, -0.45, 0, 0.03, 0.9, 0.03, BLACK_IRON)
                r.part("cube", 0, -0.92, 0.04, 0.03, 0.03, 0.1, BLACK_IRON)  # its hook
                r.part("cyl", 0, 0.0, 0, 0.08, 0.02, 0.08, BLACK_IRON, rx=math.pi / 2)  # the hanging loop
            else:
                r.part("cube", 0, -0.12, 0, 0.03, 0.18, 0.04, HANDLE)
                r.part("lozenge", 0, -0.42, 0, 0.02, 0.42, 0.05, (110, 108, 112))


def ingot_pile(r, seed):
    """A small stack of iron ingots, three, two crosswise, one on top; one of them still warm."""
    warm = seed % 6
    layout = [(-0.0, 0.05, z, 0.0) for z in (-0.18, 0.0, 0.18)]
    layout += [(x, 0.15, 0.0, math.pi / 2) for x in (-0.1, 0.1)]
    layout += [(0.0, 0.25, 0.0, 0.2 + (seed % 3) * 0.2)]
    with r.at(0, 0, 0, ry=seed * 0.5):
        for i, (x, y, z, a) in enumerate(layout):
            hot = i == warm
            rgb = WARM if hot else BLACK_IRON
            r.part("cube", x, y - 0.01, z, 0.42, 0.08, 0.16, rgb, ry=a, glow=hot)
            r.part("cube", x, y + 0.035, z, 0.34, 0.02, 0.11, _dim_rgb(rgb, 0.85) if not hot else rgb, ry=a,
                   glow=hot)  # fmt: skip


def slag_heap(r, seed):
    """A low lumpy mound of spent slag, black and glassy, a few cracks in it still glowing."""
    rng = random.Random(seed)
    r.part("sphere", 0, 0.14, 0, 1.5, 0.35, 1.4, CRUST)
    for i in range(7):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.1, 0.55)
        s = rng.uniform(0.25, 0.45)
        rgb = (CRUST, COOL_SLAG, SLAG_LIGHT)[i % 3]
        r.part("sphere", math.cos(a) * d, 0.12 + s * 0.2, math.sin(a) * d, s, s * 0.7, s, rgb, ry=a)
    for _ in range(3):
        a = rng.uniform(0, math.tau)
        d = rng.uniform(0.2, 0.5)
        r.part("cube", math.cos(a) * d, 0.2 - d * 0.15, math.sin(a) * d, 0.3, 0.02, 0.03,
               _dim_rgb(MOLTEN, 0.7), ry=a + 1.2, rz=0.3, glow=True)  # fmt: skip


# --- the road ------------------------------------------------------------------------------------


def impaler(r, t, seed):
    """Tall iron-tipped stakes leaning out of a cairn of rubble, a rusted helm spitted on one and a
    torn rag fluttering from another: a warning to whoever walks the road."""
    rng = random.Random(seed)
    for i in range(6):  # the rubble
        a = i * 1.05 + rng.uniform(-0.3, 0.3)
        d = rng.uniform(0.2, 0.55)
        s = rng.uniform(0.25, 0.4)
        r.part("cube", math.cos(a) * d, s * 0.35, math.sin(a) * d, s, s * 0.7, s * 0.9,
               STONE_LIGHT if i % 2 else RUBBLE, ry=a, rz=rng.uniform(-0.3, 0.3))  # fmt: skip
    n = 2 + seed % 2
    for i in range(n):
        a = i * math.tau / n + seed * 0.4
        lean = 0.12 + 0.06 * i
        x, z = math.cos(a) * 0.15, math.sin(a) * 0.15
        with r.at(x, 0.1, z, rz=-math.cos(a) * lean, rx=math.sin(a) * lean):
            tall = 2.4 - 0.25 * i
            r.part("cube", 0, tall / 2, 0, 0.1, tall, 0.1, STAKE)
            r.part("cube", 0, tall - 0.3, 0, 0.12, 0.06, 0.12, BLACK_IRON)  # the binding
            r.part("cone", 0, tall + 0.14, 0, 0.1, 0.3, 0.1, BLACK_IRON)  # the iron tip
            r.part("cube", 0.02, tall - 0.8, 0, 0.11, 0.5, 0.11, (60, 30, 24))  # old blood run down
            if i == 0:  # a rusted helm spitted below the tip
                r.part("sphere", 0, tall - 0.25, 0, 0.3, 0.26, 0.3, RUST)
                r.part("cyl", 0, tall - 0.36, 0, 0.32, 0.04, 0.32, _dim_rgb(RUST, 0.8))
                r.part("cube", 0.15, tall - 0.27, 0, 0.02, 0.03, 0.18, SOOT)  # its eye slit
                r.part("cube", 0.15, tall - 0.34, 0, 0.03, 0.12, 0.03, _dim_rgb(RUST, 0.8))  # nasal
            elif i == 1:  # a torn rag stirring in the hot wind
                sway = math.sin(t * 1.6 + seed) * 0.15
                with r.at(0.05, tall - 0.5, 0, rx=sway):
                    r.part("cube", 0, -0.25, 0.12, 0.02, 0.5, 0.24, RAG)
                    r.part("cube", 0, -0.58, 0.06, 0.02, 0.18, 0.1, RAG)
                    r.part("cube", 0, -0.55, 0.19, 0.02, 0.12, 0.08, _dim_rgb(RAG, 0.8))


# --- the skyline ---------------------------------------------------------------------------------


def battlement(r, t, seed, span=8.0):
    """A landmark: a run of curtain wall `span` metres long (along X, centred) whose walk is at y=0,
    standing on the wall below: a crenellated, machicolated parapet over its +Z face, a low rail on
    its -Z side, buttresses down its face and burning slits between them."""
    r.part("cube", 0, -0.2, 0, span, 0.4, 3.0, STONE_LIGHT)  # the walk
    r.part("cube", 0, -4.2, 0, span - 0.2, 7.6, 2.6, STONE, tex="black_brick")  # the wall under it
    r.part("cube", 0, 0.2, 1.62, span, 1.0, 0.36, STONE)  # the parapet, overhanging the face
    r.part("cube", 0, 0.25, -1.4, span, 0.5, 0.2, STONE)  # the rail behind
    n = max(int(span / 1.6), 1)
    for i in range(n + 1):
        x = -span / 2 + 0.3 + i * (span - 0.6) / n
        r.part("cube", x, 1.05, 1.62, 0.7, 0.7, 0.4, STONE)  # merlons
    c = max(int(span / 1.2), 1)
    step = span / c
    for i in range(c):  # corbels under the overhang, murder holes between
        x = -span / 2 + step * (i + 0.5)
        r.part("cube", x, -0.55, 1.55, 0.3, 0.5, 0.5, STONE_LIGHT)
        r.part("wedge", x, -0.95, 1.5, 0.3, 0.3, 0.4, STONE_LIGHT, rz=math.pi)
        if i < c - 1:
            r.part("cube", x + step / 2, -0.32, 1.62, step - 0.4, 0.04, 0.3, SOOT)
    m = 2 + seed % 2
    for i in range(m):
        x = -span / 2 + span * (i + 0.5) / m
        r.part("cube", x, -4.6, 1.75, 0.9, 6.8, 0.9, STONE_LIGHT, rx=-0.06)  # a battered buttress
        r.part("wedge", x, -1.05, 1.62, 0.9, 0.4, 0.6, STONE_LIGHT, ry=math.pi / 2)  # its sloped cap
    for i in range(m - 1):
        x = -span / 2 + span * (i + 1) / m
        _slit(r, x, -3.0 - (i + seed) % 2, 1.31, "z", 0.9 + 0.1 * math.sin(t * 5 + i))
    for i in range(0, n, 2):  # fire bowls burning in every other crenel, beacons seen from the bridge
        x = -span / 2 + 0.3 + (i + 0.5) * (span - 0.6) / n
        _fire_bowl(r, t, x, 0.7, 1.4, seed + i)


def _fire_bowl(r, t, x, y, z, seed):
    """An iron bowl on a stubby stand, heaped with coals and a flame licking up out of it."""
    r.part("cyl", x, y, z, 0.12, 0.3, 0.12, BLACK_IRON)
    r.part("cyl", x, y + 0.2, z, 0.56, 0.16, 0.56, BLACK_IRON)
    r.part("cyl", x, y + 0.29, z, 0.46, 0.03, 0.46, MOLTEN, glow=True)  # the coals
    f = _flicker(t, seed, 0.2)
    r.part("cone", x, y + 0.5 * f, z, 0.36, 0.5 * f, 0.36, MOLTEN, glow=True)
    r.part("cone", x, y + 0.45 * f, z, 0.18, 0.4 * f, 0.18, WHITE_HOT, glow=True)
    u = (t * 0.8 + seed * 0.29) % 1.0  # a spark rising off it
    r.part("cube", x + math.sin(seed + t) * 0.15, y + 0.6 + u * 1.4, z, 0.05, 0.05, 0.05, EMBER, glow=True)


def great_window(r, t, seed):
    """A tall lancet in a great wall's face (the wall behind at -X, facing +X), its sill at y=0: deep
    stone reveals and a hood moulding round a grille of iron, and the fires of the halls within
    roaring behind it, bright enough to be seen across the moat."""
    k = 0.75 + 0.2 * _flicker(t, seed)
    glow = _dim_rgb(MOLTEN, min(k, 1.0))
    r.part("cube", -0.98, 1.4, 0, 0.02, 2.8, 1.1, glow, glow=True)  # the fire behind
    r.part("wedge", -0.98, 3.1, 0, 1.1, 0.6, 0.02, glow, ry=math.pi / 2, glow=True)  # its pointed head
    r.part("cube", -0.97, 0.7, 0, 0.02, 1.0, 0.7, WHITE_HOT, glow=True)  # the heart of the blaze
    for z in (-0.68, 0.68):  # the reveals
        r.part("cube", -0.86, 1.5, z, 0.28, 3.0, 0.3, STONE_LIGHT)
    r.part("cube", -0.84, -0.08, 0, 0.32, 0.16, 1.7, STONE_LIGHT)  # the sill
    for side in (-1, 1):  # the arch and the hood moulding over it
        r.part("cube", -0.86, 3.25, side * 0.36, 0.28, 0.26, 0.9, STONE_LIGHT, rx=side * 0.62)
        r.part("cube", -0.8, 3.45, side * 0.42, 0.14, 0.12, 1.05, STONE, rx=side * 0.62)
    r.part("cube", -0.84, 3.62, 0, 0.3, 0.3, 0.26, STONE)  # the keystone
    for z in (-0.33, 0.0, 0.33):  # the grille
        r.part("cyl", -0.8, 1.5, z, 0.06, 3.0 - abs(z) * 0.8, 0.06, BLACK_IRON)
    for y in (0.8, 1.8, 2.6):
        r.part("cyl", -0.8, y, 0, 0.06, 1.2, 0.06, BLACK_IRON, rx=math.pi / 2)
    for i in range(2):  # sparks blown out through the bars
        u = (t * 0.5 + i / 2 + seed * 0.37) % 1.0
        r.part("cube", -0.75 + 0.6 * u, 1.2 + 1.8 * u, math.sin(seed + t + i * 2) * 0.4,
               0.05, 0.05, 0.05, EMBER, glow=True)  # fmt: skip


def lava_spout(r, t, seed):
    """A gargoyle's head jutting from the wall behind (-Z), facing +Z: horned stone with its jaws
    agape and molten iron brimming over its lip, dripping to the floor below."""
    r.part("cube", 0, 1.6, -0.94, 1.0, 1.0, 0.12, STONE_LIGHT)  # the plate it is set in
    r.part("cube", 0, 1.6, -0.86, 0.8, 0.8, 0.06, STONE)
    with r.at(0, 1.6, -0.85, ry=-math.pi / 2):  # +X now points out of the wall
        r.part("cube", 0.12, 0.0, 0, 0.26, 0.42, 0.44, STATUE_DARK)  # neck
        r.part("cube", 0.36, 0.06, 0, 0.32, 0.32, 0.38, STATUE)  # skull
        r.part("cube", 0.42, 0.2, 0, 0.26, 0.07, 0.42, STATUE_DARK)  # brow
        with r.at(0.5, 0.0, 0, rz=0.12):  # the upper jaw and snout
            r.part("cube", 0.12, 0.0, 0, 0.3, 0.12, 0.28, STATUE)
            r.part("cube", 0.26, 0.05, 0, 0.04, 0.05, 0.12, STATUE_DARK)  # nostrils
            for z in (-0.09, 0.09):
                r.part("wedge", 0.22, -0.09, z, 0.03, 0.08, 0.03, STATUE, rz=math.pi)
        with r.at(0.48, -0.1, 0, rz=-0.5):  # the lower jaw, gaping
            r.part("cube", 0.14, -0.03, 0, 0.3, 0.07, 0.26, STATUE_DARK)
            for z in (-0.08, 0.08):
                r.part("wedge", 0.24, 0.04, z, 0.03, 0.07, 0.03, STATUE)
            r.part("cube", 0.14, 0.01, 0, 0.26, 0.04, 0.18, MOLTEN, glow=True)  # the melt on its tongue
            r.part("cube", 0.29, -0.02, 0, 0.04, 0.06, 0.16, WHITE_HOT, glow=True)  # brimming at the lip
        for side in (-1, 1):
            r.part("cube", 0.47, 0.12, side * 0.12, 0.03, 0.05, 0.07, SOOT)  # hollow eyes
            with r.at(0.3, 0.2, side * 0.17, rx=-side * 0.6, rz=0.6):  # horns, swept back
                r.part("lozenge", 0, 0.12, 0, 0.07, 0.24, 0.07, STATUE_DARK)
                r.part("wedge", 0, 0.28, 0, 0.05, 0.1, 0.05, STATUE_DARK, rz=0.5)
    for i in range(3):  # drips falling from the lip
        u = (t * 1.1 + i / 3 + seed * 0.13) % 1.0
        y = 1.38 * (1 - u * u)
        r.part("cube", 0, y, -0.1, 0.05, 0.12, 0.05, MOLTEN if u > 0.2 else WHITE_HOT, glow=True)
    r.part("cyl", 0, 0.02, -0.1, 0.4, 0.03, 0.4, _dim_rgb(MOLTEN, 0.8), glow=True)  # the puddle it feeds
    r.part("cyl", 0, 0.01, -0.1, 0.55, 0.02, 0.55, CRUST)
