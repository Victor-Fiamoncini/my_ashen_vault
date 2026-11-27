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
    SMOKE,
    STATUE,
    STATUE_DARK,
    STONE,
    STONE_LIGHT,
    WHITE_HOT,
    _dim_rgb,
    _slit,
)
from ashen_vault.render.parts import EMBER, RUST, _bar, _flame
from ashen_vault.render.town_models import cart_wheel

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


def forge_statue(r, seed):
    """A statue of a smith-knight on a soot-blackened plinth: an armoured figure in iron gone dark, his
    great hammer's head resting on the anvil before him and both gauntlets on its haft, a helm with a
    slit visor, a cloak of beaten plates and a ring of iron spikes round the plinth's cornice."""
    iron = _dim_rgb(BLACK_IRON, 1.15 if seed % 2 else 1.0)
    dark = _dim_rgb(iron, 0.7)
    r.part("cube", 0, 0.15, 0, 1.8, 0.3, 1.8, STONE)  # the plinth's foot
    r.part("cube", 0, 0.8, 0, 1.3, 1.0, 1.3, STONE_LIGHT)  # its die
    r.part("cube", 0, 1.36, 0, 1.5, 0.12, 1.5, STONE)  # the cornice
    for k in range(8):  # spikes round its edge
        a = k * math.pi / 4 + math.pi / 8
        r.part("cube", math.cos(a) * 0.68, 1.52, math.sin(a) * 0.68, 0.05, 0.22, 0.05, BLACK_IRON)
    r.part("cube", 0.66, 0.8, 0, 0.02, 0.5, 0.7, SOOT)  # soot licked up its face
    r.part("cube", 0.665, 0.95, 0, 0.02, 0.2, 0.34, (60, 50, 46))  # a cast iron plaque
    with r.at(0, 1.42, 0):
        for z in (-0.16, 0.16):  # sabatons, greaves and cuisses
            r.part("cube", 0.04, 0.06, z, 0.3, 0.12, 0.16, dark)
            r.part("cube", 0, 0.38, z, 0.16, 0.56, 0.17, iron)
            r.part("cube", 0.08, 0.66, z, 0.06, 0.12, 0.14, dark)  # the knee cop
            r.part("cube", 0, 0.92, z, 0.2, 0.48, 0.2, iron)
        r.part("frustum", 0, 1.16, 0, 0.5, 0.2, 0.62, dark)  # the fauld, flaring over the hips
        r.part("cube", 0, 1.5, 0, 0.36, 0.56, 0.58, iron)  # the breastplate
        r.part("cube", 0.19, 1.52, 0, 0.02, 0.44, 0.06, _dim_rgb(iron, 1.3))  # its ridge
        for z in (-1, 1):
            r.part("cube", 0, 1.8, z * 0.34, 0.36, 0.14, 0.24, dark, rx=z * 0.3)  # pauldrons
            r.part("cube", 0.16, 1.42, z * 0.3, 0.14, 0.44, 0.14, iron, rz=0.75)  # the arms, reaching down
            r.part("cube", 0.36, 1.18, z * 0.12, 0.14, 0.12, 0.14, dark)  # gauntlets on the haft
        for k in range(4):  # the cloak of beaten plates hanging behind
            r.part("cube", -0.25, 1.62 - k * 0.32, 0, 0.06, 0.3, 0.7 - k * 0.04, _dim_rgb(dark, 1 - k * 0.05),
                   rz=-0.06)  # fmt: skip
        r.part("cube", 0.02, 2.0, 0, 0.3, 0.32, 0.28, iron)  # the helm
        r.part("frustum", 0.0, 2.2, 0, 0.3, 0.1, 0.28, dark)  # its brow
        r.part("cube", 0.17, 2.02, 0, 0.02, 0.03, 0.2, (16, 12, 12))  # the visor's slit
        r.part("cube", 0.0, 2.27, 0, 0.24, 0.05, 0.04, _dim_rgb(iron, 1.2))  # a crest along its top
        r.part("cube", 0.38, 0.85, 0, 0.06, 0.66, 0.06, TIMBER)  # the hammer's haft, standing upright
        r.part("cube", 0.38, 0.38, 0, 0.26, 0.24, 0.38, BLACK_IRON)  # its head, resting on the anvil
        r.part("cube", 0.4, 0.13, 0, 0.42, 0.2, 0.3, dark)  # the anvil's face
        r.part("cube", 0.4, 0.02, 0, 0.3, 0.06, 0.22, dark)


def ore_cart(r, seed):
    """A mine cart left on a short run of rails: an iron tub riveted at its seams and banded, on four
    small spoked wheels, heaped with ore and cooling slag, a shovel thrust in it and its towing chain
    hanging from the front."""
    for z in (-0.42, 0.42):  # the rails on their sleepers
        r.part("cube", 0, 0.05, z, 2.0, 0.06, 0.06, BLACK_IRON)
    for x in (-0.8, -0.27, 0.27, 0.8):
        r.part("cube", x, 0.01, 0, 0.18, 0.04, 1.2, TIMBER)
    for x in (-0.4, 0.4):
        r.part("cube", x, 0.28, 0, 0.07, 0.07, 1.0, BLACK_IRON)  # the axle
        for z in (-0.42, 0.42):
            cart_wheel(r, x, 0.24, z, 0.2, 6, wood=BLACK_IRON)
    tub = _dim_rgb(BLACK_IRON, 1.2)
    r.part("cube", 0, 0.42, 0, 1.3, 0.1, 0.76, tub)  # the tub's floor
    for z in (-1, 1):  # its sides, flaring out
        r.part("cube", 0, 0.68, z * 0.42, 1.36, 0.5, 0.06, tub, rx=z * 0.15)
    for x in (-1, 1):
        r.part("cube", x * 0.68, 0.68, 0, 0.06, 0.5, 0.86, tub, rz=-x * 0.15)
    for x in (-0.5, 0.0, 0.5):  # bands round it, and rivets
        for z in (-1, 1):
            r.part("cube", x, 0.68, z * 0.455, 0.08, 0.52, 0.02, RUST, rx=z * 0.15)
            r.part("cube", x, 0.88, z * 0.47, 0.04, 0.04, 0.03, RIVET)
    rng = random.Random(seed)
    for k in range(7):  # the load: lumps of ore and slag, one still warm
        x, z = rng.uniform(-0.45, 0.45), rng.uniform(-0.25, 0.25)
        rgb = WARM if k == 0 else SLAG_LIGHT if k % 2 else COOL_SLAG
        r.part("cube", x, 0.95 + rng.uniform(0, 0.1), z, 0.24, 0.18, 0.22, rgb, ry=rng.uniform(0, 3), rz=0.3,
               glow=k == 0)  # fmt: skip
    with r.at(-0.2, 1.2, 0.15, rz=-0.4):  # a shovel thrust into it
        r.part("cube", 0, 0.3, 0, 0.04, 0.8, 0.04, TIMBER)
        r.part("cube", 0, 0.72, 0, 0.12, 0.04, 0.04, TIMBER)
        r.part("cube", 0, -0.12, 0, 0.03, 0.22, 0.2, BLACK_IRON)
    for k in range(4):  # its towing chain, hanging from the front to the ground
        r.part("cube", 0.74 + k * 0.06, 0.5 - k * 0.12, 0, 0.05, 0.1, 0.03 if k % 2 else 0.06, BLACK_IRON)


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
    # Its back stays within the wall's tile (z >= -1), so nothing juts out over the courts behind.
    r.part("cube", 0, -0.2, 0.25, span, 0.4, 2.5, STONE_LIGHT)  # the walk
    r.part("cube", 0, -4.2, 0.2, span - 0.2, 7.6, 2.2, STONE, tex="black_brick")  # the wall under it
    r.part("cube", 0, 0.2, 1.62, span, 1.0, 0.36, STONE)  # the parapet, overhanging the face
    r.part("cube", 0, 0.25, -0.88, span, 0.5, 0.2, STONE)  # the rail behind
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


# --- the great wall's face ---------------------------------------------------------------------------
# The front of the great wall over the moat, seen from the long bridge: buttresses battered down into
# the lava, drains spilling slag down the face and gibbets hung from its top. Those on the wall stand
# on its tile, local +X out of its face toward the moat, the face itself at x = FACE; `top` is the
# wall's top and `foot` the ground (the lava) it falls to. The burnt ridge on the horizon beyond the
# keep is the `ember` sky's own (`world/sky.py`, `Ridge`), so no fog hides it.

FACE = 1.0
BONE = (206, 196, 172)
# A great crack down the fortress's black stone or its cliffs: soot-black in its depth, scorched stone
# either side, and in many the fires behind the wall glowing through (`sunken_models.wall_crack`).
BRICK_CRACK = ((12, 8, 8), (40, 32, 32), (255, 110, 30))
ROCK_CRACK = ((14, 10, 8), (58, 44, 40), (240, 96, 26))


def wall_buttress(r, seed, top=16.0, foot=-8.0):
    """A great buttress built down the wall's face from its top into the lava: three battered stages,
    each stepping out further than the one above under a sloped set-off, iron tie-plates riveted across
    them, a slit burning in the middle stage, the lowest stage scorched where the lava laps it, and on
    its head a fire basket over the moat."""
    h = (top - foot) / 3
    for k in range(3):
        d = 0.9 + 0.5 * k
        wd = 1.4 + 0.3 * k
        y = top - h * (k + 0.5)
        r.part("cube", FACE + d / 2, y, 0, d, h, wd, STONE if k % 2 else STONE_LIGHT, tex="black_brick")
        r.part("wedge", FACE + d + 0.25, top - h * k, 0, 0.5, 0.5, wd, STONE_LIGHT, ry=math.pi / 2)
        for side in (-1, 1):  # tie-plates and their rivets
            r.part("cube", FACE + d + 0.02, y + 0.6, side * wd * 0.3, 0.04, 0.7, 0.2, BLACK_IRON)
            r.part("cube", FACE + d + 0.05, y + 0.8, side * wd * 0.3, 0.05, 0.1, 0.1, RIVET)
            r.part("cube", FACE + d + 0.05, y + 0.4, side * wd * 0.3, 0.05, 0.1, 0.1, RIVET)
        if k == 1:
            _slit(r, FACE + d + 0.01, y, 0, "x", 1.4)
    r.part("cube", FACE + 1.15, foot + 1.0, 0, 2.5, 2.0, 2.4, SOOT, tex="black_brick")  # scorched foot
    r.part("cube", FACE + 1.2, foot + 0.25, 0, 2.7, 0.3, 2.6, WARM, glow=True)  # the lava's glow on it
    with r.at(FACE + 0.45, top, 0):  # the fire basket on its head
        r.part("cube", 0, 0.2, 0, 0.9, 0.4, 1.4, STONE_LIGHT)
        r.part("cyl", 0, 0.6, 0, 0.12, 0.4, 0.12, BLACK_IRON)
        r.part("frustum", 0, 0.95, 0, 0.6, 0.35, 0.6, BLACK_IRON)
        r.part("cyl", 0, 1.08, 0, 0.48, 0.04, 0.48, MOLTEN, glow=True)
        r.part("cone", 0, 1.4, 0, 0.4, 0.6, 0.4, MOLTEN, glow=True)
        r.part("cone", 0, 1.32, 0, 0.2, 0.42, 0.2, WHITE_HOT, glow=True)


def slag_runnel(r, seed, top=16.0, foot=-8.0):
    """A drain high in the wall's face spilling molten slag down it into the moat: an arched outlet in a
    dressed surround, a white-hot tongue in its mouth, the slag running down the stone in a wandering
    ribbon (white-hot under the mouth, cooling to orange and crusting black at its edges as it falls),
    a soot stain spread behind it, and a fan of cooled slag where it meets the lava."""
    rng = random.Random(seed)
    mouth = top - 2.6
    r.part("cube", FACE + 0.02, (mouth + foot) / 2, 0, 0.03, mouth - foot, 2.2, SOOT)  # the stain
    r.part("cube", FACE + 0.15, mouth, 0, 0.3, 1.5, 1.5, STONE_LIGHT, tex="black_brick")  # its surround
    r.part("wedge", FACE + 0.15, mouth + 0.95, 0, 0.3, 0.4, 1.5, STONE_LIGHT, ry=math.pi / 2)
    r.part("cube", FACE + 0.31, mouth - 0.1, 0, 0.03, 0.8, 0.8, DARK)  # the outlet
    for z in (-0.25, 0.0, 0.25):  # its grate
        r.part("cube", FACE + 0.34, mouth - 0.1, z, 0.04, 0.8, 0.06, BLACK_IRON)
    r.part("cube", FACE + 0.45, mouth - 0.45, 0, 0.4, 0.1, 0.6, WHITE_HOT, glow=True)  # the tongue
    y, z = mouth - 0.5, 0.0
    steps = max(int((mouth - 0.5 - foot) / 1.6), 2)
    seg = (mouth - 0.5 - foot) / steps
    for i in range(steps):
        k = i / steps
        dz = rng.uniform(-0.18, 0.18)
        w = 0.65 + 0.35 * k
        hot = WHITE_HOT if k < 0.2 else MOLTEN if k < 0.7 else WARM
        mid = y - seg / 2
        r.part("cube", FACE + 0.05, mid, z + dz / 2, 0.05, seg + 0.1, w, hot, glow=True)
        for side in (-1, 1):  # the crust at its edges
            r.part("cube", FACE + 0.06, mid, z + dz / 2 + side * (w / 2 + 0.06), 0.07, seg + 0.1, 0.14, CRUST)
        if i % 3 == 1:  # a drip cooled where it ran off the edge
            r.part("cone", FACE + 0.08, mid - 0.2, z + rng.choice((-1, 1)) * (w / 2 + 0.15), 0.12, 0.4, 0.12,
                   COOL_SLAG, rx=math.pi)  # fmt: skip
        y -= seg
        z += dz
    r.part("cyl", FACE + 0.9, foot + 0.15, z, 2.2, 0.3, 2.6, COOL_SLAG)  # the fan at its foot
    r.part("cyl", FACE + 0.6, foot + 0.32, z, 1.0, 0.06, 1.2, MOLTEN, glow=True)
    for i in range(3):
        r.part("cube", FACE + 0.7 + 0.5 * i, foot + 0.35, z + rng.uniform(-0.8, 0.8), 0.4, 0.2, 0.3, SLAG_LIGHT,
               ry=rng.uniform(0, math.pi))  # fmt: skip


def _cage(r, drop, bones, seed):
    """A gibbet cage hung `drop` metres below its chain's hook at the origin, its door rusted shut, and
    in it what is left of whoever was hung there (`bones`) or rags."""
    for i in range(int(drop / 0.35)):  # the chain, link by link
        r.part("cube", 0, -0.18 - i * 0.35, 0, 0.06, 0.3, 0.12 if i % 2 else 0.04, BLACK_IRON)
    with r.at(0, -drop, 0, ry=seed * 0.7):
        r.part("cone", 0, -0.15, 0, 0.9, 0.3, 0.9, BLACK_IRON)  # its dome
        r.part("cyl", 0, -1.8, 0, 0.9, 0.06, 0.9, BLACK_IRON)  # the floor
        r.part("cyl", 0, -1.0, 0, 0.94, 0.05, 0.94, RUST)  # a hoop
        for k in range(8):
            a = k * math.pi / 4
            r.part("cube", math.cos(a) * 0.44, -1.0, math.sin(a) * 0.44, 0.04, 1.6, 0.04, BLACK_IRON)
        if bones:
            r.part("sphere", 0.1, -1.55, 0.1, 0.22, 0.24, 0.22, BONE)  # a skull fallen to the floor
            for k in range(4):
                r.part("cube", -0.05, -1.2 - k * 0.1, -0.05, 0.36 - 0.04 * k, 0.03, 0.06, BONE, ry=0.4)
            r.part("cube", 0.15, -1.6, -0.2, 0.05, 0.05, 0.5, BONE, ry=1.1)  # a long bone
            r.part("cube", -0.1, -1.0, 0.36, 0.05, 0.5, 0.04, BONE, rz=0.3)  # an arm through the bars
        else:
            r.part("cube", 0, -1.3, 0, 0.5, 0.8, 0.4, (64, 54, 46))  # rags in a heap


def gibbet_cages(r, seed, top=16.0):
    """Gibbets hung over the moat from the wall's top: iron davits jutting from the parapet on braces,
    each with a cage hung on its chain at its own depth, the dead left in them."""
    for k, z in enumerate((-0.6, 0.65)):
        drop = 2.5 + ((seed + k * 3) % 4) * 0.9
        reach = 1.6 + 0.3 * k
        with r.at(0, top, z):
            r.part("cube", FACE + 0.1, -0.4, 0, 0.5, 0.5, 0.5, STONE_LIGHT, tex="black_brick")  # its block
            r.part("cube", FACE + reach / 2, -0.3, 0, reach, 0.14, 0.14, BLACK_IRON)  # the davit
            r.part(
                "cube", FACE + reach * 0.4, -0.85, 0, reach * 0.9, 0.1, 0.1, BLACK_IRON, rz=0.62
            )  # its brace
            r.part("cube", FACE + reach - 0.05, -0.38, 0, 0.12, 0.12, 0.16, RIVET)  # the hook's eye
            with r.at(FACE + reach - 0.05, -0.45, 0):
                _cage(r, drop, bones=(seed + k) % 2 == 0, seed=seed + k)


def chimney_cluster(r, t, seed):
    """Three flues of a smelting house on one plinth, rising from the wall tops behind the front: each a
    different height, banded in iron, glowing at its mouth, smoke rolling up out of each and embers
    blowing off them."""
    r.part("cube", 0, 1.2, 0, 5.4, 2.4, 3.4, STONE, tex="black_brick")
    r.part("cube", 0, 2.5, 0, 5.8, 0.3, 3.8, STONE_LIGHT)
    for i, (x, z, h, d) in enumerate(((-1.6, -0.3, 9.0, 1.4), (0.2, 0.4, 13.0, 1.8), (1.8, -0.2, 7.0, 1.2))):
        r.part("cyl", x, 2.6 + h / 2, z, d, h, d, (66, 48, 42))
        for k in range(1, int(h / 3) + 1):
            r.part("cyl", x, 2.6 + k * 3, z, d + 0.2, 0.22, d + 0.2, BLACK_IRON)
        top = 2.6 + h
        r.part("cyl", x, top + 0.1, z, d + 0.3, 0.3, d + 0.3, BLACK_IRON)
        r.part("cyl", x, top + 0.2, z, d * 0.7, 0.04, d * 0.7, MOLTEN, glow=True)
        for j in range(3):  # its smoke, swelling and thinning as it drifts off
            u = (t * 0.12 + j / 3 + i * 0.21) % 1.0
            s = (0.4 + u * 1.2) * (1.0 - u * 0.5)
            r.part("cube", x + u * 1.8 + math.sin(t * 0.6 + j + i) * 0.5, top + 0.7 + u * 5, z, s, s * 0.7, s,
                   SMOKE, ry=j + u)  # fmt: skip
        u = (t * 0.45 + i / 3) % 1.0
        r.part("cube", x + math.sin(i * 2.1 + t) * 0.4 + u * 0.6, top + 0.4 + 3 * u, z, 0.1, 0.1, 0.1, EMBER,
               glow=True)  # fmt: skip
