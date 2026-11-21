"""Models for Old Harrowmere, the sunken first city under the sewers: its Stone Golems, Sunken Sextons
and the Keystone, the boulder the Keystone hurls, and the city's dressing (the shaft of light from the
crack overhead, the drowned towers of its skyline, the breach in the cistern wall that leads down and
its rune lift). Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math
import random

from ashen_vault.ai.enemy import STATUE_BURST
from ashen_vault.render.parts import (
    BLADE_REST,
    ELBOW_REST,
    EMBER,
    HIT_GLOW,
    IRON,
    PASSAGE_DARK,
    _bar,
    _dim,
    _ease,
    _mix,
    _spider_move,
    _swing_pose,
    aim_wrist,
    blade_parts,
    chop_angle,
    death_fall,
    elbow_bend,
    held,
    hit_tint,
    walk_cycle,
    wrist_angle,
)
from ashen_vault.util import rround
from ashen_vault.world.terrain import CALL_PLATE_R, PLATE_SINK
from ashen_vault.world.vault import CRACK_LEN, CRACK_WIDTH, SHAFT_LEAN

MASONRY = (138, 120, 96)  # the old city's warm, worn sandstone
MASONRY_DARK = (98, 84, 68)
MORTAR = (70, 60, 50)
MOSS = (74, 92, 50)
STATUE_MOSS = (88, 100, 64)  # a golem asleep on its plinth: greener, the moss grown over it
EYE = (255, 176, 80)  # amber: the light of the old city's lamps
GOLEM_STONE = (126, 140, 134)  # the golems' faceted rock: dark grey-green
GOLEM_DARK = (86, 98, 94)
COLD = (60, 52, 46)  # an eye or a crack gone dark
ROBE = (58, 62, 54)  # a sexton's sodden robe, dark with the water
ROBE_DARK = (40, 44, 38)
SEXTON_SKIN = (170, 168, 146)  # waterlogged, grey-green
BELL_BRONZE = (150, 116, 60)
HAFT = (82, 62, 42)
GOLD_LIGHT = (255, 214, 140)  # the daylight in the rift overhead
CORE_TEAL = (70, 235, 190)  # the mortar-light that animates the giants
CORE_HEART = (200, 255, 235)  # its white-teal heart
CORE_DEAD = (112, 118, 114)  # the core's crystal once quenched: grey, cracked, cold
TOWER_LIT = (230, 222, 210)  # a pale tint, so a tower's brick texture shows its own warm colour


def _mix_rgb(a, b, k):
    return tuple(rround(x + (y - x) * k) for x, y in zip(a, b, strict=True))


def _windup_k(e):
    return min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0


# --- the Stone Golem ------------------------------------------------------------------------------
#
# The golems and the Keystone are one family, built from the same parts: a hunched body of faceted
# rock, a broad chest tapering to a narrow waist, short thick legs, a small blocky head set low and
# forward under shoulders that rise above it, and long arms (a boulder shoulder, an upper block and a
# huge slab of a forearm, widening to the fist) that hang down to near the ground. The mortar-light
# that animates them glows teal in their eyes and cracks. A golem is drawn at the family's own size
# (some 2.4 m); the Keystone is the same body scaled up (`KEYSTONE_SCALE`) and dressed with more.

GOLEM_TEX = "white"  # the golems' rock: flat-shaded facets read better than a texture at their size
GOLEM_HUNCH = 0.42  # how far forward (radians) the body leans from its waist
GOLEM_WAIST = 0.9  # the waist's height, where the body pivots
GOLEM_HIP = 0.78  # the hips' height, where the legs hang
GOLEM_SHOULDER = (0.0, 1.3, 0.82)  # a shoulder's (x, y, +-z) in the leaning body's frame
GOLEM_HEAD = (0.46, 1.08)  # the head's (x, y) in the leaning body's frame: low and forward


def _golem_leg(r, z, swing, knee, stone, dark):
    """A short thick leg hung from the hips at `z`: a thigh block, a shin bent back by `knee` and a
    broad slab of a foot."""
    with r.at(0, GOLEM_HIP, z, rz=swing):
        r.part("cube", 0, -0.17, 0, 0.5, 0.42, 0.48, stone, tex=GOLEM_TEX, ry=0.08)  # the thigh
        r.part("cube", 0.2, -0.12, 0, 0.14, 0.3, 0.4, _dim(stone, 1.12), rz=-0.2)  # a facet of it
        with r.at(0.02, -0.36, 0, rz=knee):
            r.part("cube", 0, -0.14, 0, 0.44, 0.34, 0.46, _dim(stone, 0.9), tex=GOLEM_TEX)  # shin
            r.part("cube", 0.1, -0.33, 0, 0.66, 0.16, 0.54, dark, tex=GOLEM_TEX)  # the foot
            r.part("cube", 0.36, -0.36, 0, 0.16, 0.1, 0.46, _dim(dark, 1.1), rz=0.3)  # its blunt toe


def _golem_torso(r, stone, dark, moss, seam, lit):
    """The leaning body: a broad chest course over a V of rock tapering to the waist, a hump of rock
    over the shoulders, slabs faceted at odd angles, moss in the seams, and down its back the crack the
    mortar-light shows through, its weak spot."""
    pale = _dim(stone, 1.14)
    r.part("cube", 0, 0.12, 0, 0.48, 0.34, 0.56, dark, tex=GOLEM_TEX)  # the narrow waist
    # The V: an inverted wedge across the body, from the broad chest down to the waist.
    r.part("wedge", 0.02, 0.5, 0, 1.5, 0.82, 0.78, stone, tex=GOLEM_TEX, ry=math.pi / 2, rx=math.pi)
    r.part("cube", 0.05, 0.98, 0, 0.92, 0.42, 1.5, stone, tex=GOLEM_TEX)  # the chest course
    r.part("cube", -0.2, 1.16, 0, 0.74, 0.42, 1.0, _dim(stone, 0.92), tex=GOLEM_TEX, rz=0.35)  # hump
    for side in (-1, 1):  # slabs over the breast, each tilted its own way
        r.part("cube", 0.4, 1.0, side * 0.36, 0.16, 0.42, 0.62, pale, tex=GOLEM_TEX,
               rx=side * 0.12, rz=-0.18)  # fmt: skip
        r.part(
            "cube", 0.3, 0.6, side * 0.26, 0.14, 0.34, 0.4, stone, rx=-side * 0.25, rz=0.15
        )  # ribs of rock
    r.part("cube", 0.0, 1.2, 0, 0.7, 0.05, 1.3, MORTAR)  # the seam under the hump
    for x, y, z, s in ((0.42, 0.78, -0.42, 0.13), (0.4, 1.24, 0.5, 0.15), (-0.2, 1.42, -0.3, 0.14)):
        r.part("sphere", x, y, z, s * 0.6, s, s * 1.5, moss)  # moss in the seams
    # Its back has split open down the spine: strike it from behind.
    r.part("cube", -0.44, 0.9, 0, 0.06, 0.8, 0.2, PASSAGE_DARK, rz=0.2)
    r.part("cube", -0.46, 0.9, 0, 0.04, 0.6, 0.07, seam, rz=0.2, glow=lit)


def _golem_head(r, stone, dark, eye, lit, flare=0.0):
    """A small blocky head under a jutting brow, two eyes of the mortar-light set deep below it. A
    `flare` (0..1) throws a halo of light round each eye."""
    r.part("cube", 0, 0, 0, 0.38, 0.34, 0.4, stone, tex=GOLEM_TEX)
    r.part("cube", 0.1, 0.16, 0, 0.3, 0.1, 0.46, dark, tex=GOLEM_TEX, rz=-0.15)  # the brow
    r.part("cube", 0.12, -0.15, 0, 0.26, 0.12, 0.32, _dim(stone, 0.85), rz=0.2)  # a heavy jaw
    for z in (-0.1, 0.1):
        r.part("cube", 0.2, 0.05, z, 0.04, 0.06, 0.09, eye if lit else COLD, glow=lit)
        if flare > 0 and lit:
            s = 0.12 + 0.12 * flare
            r.part("sphere", 0.22, 0.05, z, s * 0.5, s, s, _mix_rgb(CORE_TEAL, CORE_HEART, 0.5), glow=True)


def _golem_arm(r, side, swing, elbow, stone, dark, vein, lit, wide=1.0):
    """A long arm at its shoulder: a boulder of a shoulder, an upper block and a great slab of a
    forearm widening to a blunt fist (`wide` widens the slab), a crack of the mortar-light down it.
    `swing` turns it from hanging straight down (forward is positive), `elbow` bends the forearm."""
    with r.at(0, 0, 0, rz=swing):
        r.part("sphere", 0, 0.06, 0, 0.74, 0.7, 0.7, _dim(stone, 0.95), tex=GOLEM_TEX)  # the shoulder
        r.part("cube", -0.05, 0.16, side * 0.12, 0.46, 0.3, 0.42, _dim(stone, 1.1), tex=GOLEM_TEX,
               rx=side * 0.35, rz=0.3)  # fmt: skip
        r.part("cube", 0, -0.42, 0, 0.4, 0.56, 0.4, stone, tex=GOLEM_TEX, ry=0.2)  # the upper arm
        r.part("cube", 0, -0.64, 0, 0.34, 0.08, 0.34, MORTAR)  # the elbow's seam
        with r.at(0, -0.66, 0, rz=elbow):
            # The slab: a faceted block of rock that widens down to the fist.
            r.part("frustum", 0.02, -0.5, 0, 0.62 * wide, 1.0, 0.58 * wide, _dim(stone, 0.92),
                   tex=GOLEM_TEX)  # fmt: skip
            r.part("cube", 0.2, -0.58, 0, 0.12, 0.78, 0.44 * wide, _dim(stone, 1.12), tex=GOLEM_TEX,
                   rz=0.12)  # fmt: skip
            r.part("cube", 0, -0.6, side * 0.27 * wide, 0.46, 0.6, 0.1, _dim(stone, 0.8), rx=side * 0.1)
            r.part("cube", 0.22, -0.56, 0, 0.03, 0.54, 0.05, vein if lit else PASSAGE_DARK, rz=0.12, glow=lit)
            r.part("cube", 0.04, -1.12, 0, 0.74 * wide, 0.36, 0.66 * wide, dark, tex=GOLEM_TEX)  # fist
            for z in (-0.17, 0.17):  # knuckles of rock
                r.part("cube", 0.34 * wide, -1.1, z * wide, 0.16, 0.24, 0.22, _dim(stone, 1.05), rz=0.2)


def stone_golem(r, e, t):
    """A golem of the old city's stone, hunched and heavy: a broad chest of faceted, grey-green rock
    tapering to a narrow waist, short thick legs, and a small blocky head set low and forward under
    shoulders that rise above it, two eyes of teal mortar-light deep under its brow. Its arms hang
    almost to the ground: boulder shoulders, and forearms that are great slabs of rock widening to the
    fist. Its back has split open down the spine on the light inside, the weak spot. Asleep on its
    plinth it stands as a statue, moss grown over it and its eyes dark; woken, the moss tears off it.
    A sweep spins it with its arms out, a slam brings both slabs down. Slain, it sinks to its knees
    and topples forward."""
    k = e.rise_progress
    asleep = 1.0 - _ease(min(max((k - STATUE_BURST) / 0.2 + 0.5, 0.0), 1.0))
    statue = asleep > 0.5
    dead = e.state == "dead"
    lit = not statue and not dead
    swing = walk_cycle(e, t) * 0.3
    kneel = death_fall(e, 0.6)
    topple = death_fall(e, 1.5)
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit = _swing_pose(e, 0.1, -2.2, 0.8)
    wk = _windup_k(e)
    both = None
    if e.attack_kind == "slam" and e.state in ("windup", "attack"):
        both = -2.7 * wk if e.state == "windup" else -2.7 + 3.3 * min(e.state_t / 0.15, 1)
    elif e.attack_kind == "sweep" and e.state in ("windup", "attack"):
        both = -1.4
    stone = hit_tint((220, 232, 214)) if e.flashing else GOLEM_STONE
    dark = hit_tint((190, 200, 186)) if e.flashing else GOLEM_DARK
    moss = STATUE_MOSS if statue else MOSS
    eye = HIT_GLOW if e.flashing else CORE_TEAL
    vein = HIT_GLOW if e.flashing else _dim(CORE_TEAL, 0.8)
    rear = 0.3 * wk if both is not None and e.state == "windup" else 0.0  # it rears back to slam
    hunch = GOLEM_HUNCH - rear + 0.25 * kneel
    with (
        r.at(0, lift * 0.3 - 0.4 * kneel + 0.95 * topple, 0, ry=spin),
        r.at(0, 0, 0, rz=-1.15 * topple),
    ):
        for side, a in ((-0.38, swing), (0.38, -swing)):
            _golem_leg(r, side, a + 1.5 * kneel, -0.3 * abs(a) - 1.4 * kneel, stone, dark)
        r.part("cube", 0, GOLEM_HIP + 0.04, 0, 0.6, 0.28, 0.92, dark, tex=GOLEM_TEX)  # the hips
        with r.at(0, GOLEM_WAIST, 0, rz=-hunch):
            _golem_torso(r, stone, dark, moss, CORE_TEAL if lit else COLD, lit)
            if statue:  # a blanket of moss grown over its hump and head
                r.part("cube", -0.1, 1.48, 0, 0.8, 0.1, 1.4, moss, rz=0.35)
                r.part("cube", GOLEM_HEAD[0], GOLEM_HEAD[1] + 0.2, 0, 0.36, 0.08, 0.44, moss)
            with r.at(*GOLEM_HEAD, 0, rz=hunch - 0.1):  # the head looks ahead, whatever the body does
                _golem_head(r, stone, dark, eye, lit)
            sx, sy, sz = GOLEM_SHOULDER
            for side in (1, -1):
                a = both if both is not None else (hit if side == 1 else 0.1 - swing * 0.5)
                with r.at(sx, sy, side * sz, rz=hunch):  # the arms hang from the world's vertical
                    _golem_arm(r, side, a - 1.0 * kneel, 0.2 - 0.9 * kneel, stone, dark, vein, lit)


# --- the Sunken Sexton ----------------------------------------------------------------------------


def sexton_arms(e):
    """The staff arm's (shoulder, elbow, wrist) and how far a toll has raised it (0..1) for its pose:
    it chops overhead with the staff, and on a toll lifts it high, head up, so its mortar-light flares
    and calls the stone round it awake."""
    tolling = e.attack_kind == "toll" and e.state in ("windup", "attack")
    if tolling:
        ring = 1.0 if e.state == "attack" else _ease(_windup_k(e))
        shoulder, elbow = 2.5 * ring, ELBOW_REST - 0.1 * ring
        return shoulder, elbow, aim_wrist(_mix(BLADE_REST, math.pi / 2, ring), shoulder + elbow), ring
    return chop_angle(e), elbow_bend(e), wrist_angle(e), 0.0


SEXTON_STAFF_LEN = 1.7  # metres of the staff, butt to crown


def sexton_staff(r, t, flare=0.0, lit=True):
    """A sexton's staff in a `held` frame (the grip along +X): a long dark haft shod in iron at the
    butt, crowned with a shard of the golems' mortar-light caged in bent bronze tines, breathing
    teal. `flare` (0..1) blazes it up as a toll is rung through it; slain, it goes cold."""
    r.part("cube", 0.35, 0, 0, SEXTON_STAFF_LEN, 0.05, 0.05, HAFT)  # the long haft
    r.part("cube", -0.5, 0, 0, 0.1, 0.07, 0.07, IRON)  # the iron shoe at its butt
    head = 0.35 + SEXTON_STAFF_LEN / 2
    r.part("cube", head - 0.06, 0, 0, 0.1, 0.08, 0.08, BELL_BRONZE)  # the collar under the crown
    breath = 0.5 + 0.5 * math.sin(t * 2.2)
    with r.at(head + 0.14, 0, 0):
        for i in range(3):  # the bronze tines, bent round the shard like a claw
            a = i * math.tau / 3
            with r.at(0, math.cos(a) * 0.08, math.sin(a) * 0.08, rx=a):
                r.part("cube", 0, 0.02, 0, 0.26, 0.025, 0.025, BELL_BRONZE, rz=0.35)
        if not lit:
            r.part("lozenge", 0, 0, 0, 0.1, 0.24, 0.1, COLD, rz=-math.pi / 2)
            return
        s = 1.0 + 0.5 * flare
        r.part("lozenge", 0, 0, 0, 0.12 * s, 0.28 * s, 0.12 * s, _dim(CORE_TEAL, 0.8 + 0.2 * breath),
               rz=-math.pi / 2, ry=t * 1.5, glow=True)  # fmt: skip
        r.part("lozenge", 0, 0, 0, 0.06 * s, 0.18 * s, 0.06 * s, CORE_HEART, rz=-math.pi / 2, glow=True)
        if flare > 0.0:  # the light blazing out of it as the toll rings
            r.part("sphere", 0, 0, 0, 0.5 * flare, 0.5 * flare, 0.5 * flare, _dim(CORE_TEAL, 0.5 + 0.3 * breath),
                   tex="ward_net", glow=True, ry=t * 3)  # fmt: skip
            for i in range(4):  # motes spun off it
                a = t * 4 + i * math.tau / 4
                r.part("cube", math.cos(a) * 0.35 * flare, math.sin(a) * 0.35 * flare, 0.0, 0.04, 0.04, 0.04,
                       CORE_HEART, glow=True)  # fmt: skip


def sunken_sexton(r, e, t):
    """One of the old city's bell-keepers, stooped and sodden: a long robe dark with the water,
    clinging and dripping at the hem, a hood fallen forward over a grey, swollen face and a horn lantern
    hung at its belt, burning low. It carries a staff crowned with a shard of the golems' teal
    mortar-light (`sexton_staff`) and chops with it overhead. Given room, it lifts the staff high and
    the shard flares, waking the stone round it. Slain, it sags and falls onto its back."""
    fall = death_fall(e, 0.8)
    dead = e.state == "dead"
    swing = walk_cycle(e, t) * 0.5
    skin = hit_tint((236, 230, 214)) if e.flashing else SEXTON_SKIN
    robe = hit_tint((200, 200, 190)) if e.flashing else ROBE
    shoulder, elbow, wrist, ring = sexton_arms(e)
    if dead:  # the staff sinks with it, to lie along the floor beside the body on its back
        wrist = aim_wrist(BLADE_REST - 1.7 * fall, shoulder + elbow)
    hunch = 0.35 - 0.15 * ring
    with r.at(-0.2 * fall, 0.32 * fall, 0, rz=1.35 * fall):
        for side, a in ((-0.11, swing), (0.11, -swing)):  # thin legs under the robe
            with r.at(0, 0.7, side, rz=a):
                r.part("cube", 0, -0.32, 0, 0.11, 0.64, 0.11, ROBE_DARK)
                r.part("cube", 0.06, -0.66, 0, 0.22, 0.06, 0.12, (54, 46, 40))  # a sodden boot
        r.part("cone", 0, 0.62, 0, 0.62, 1.2, 0.6, robe)  # the robe, clinging, falling wide at the hem
        for i in range(5):  # its ragged, dripping hem
            a = i * math.tau / 5 + 0.3
            r.part("cube", math.cos(a) * 0.27, 0.06, math.sin(a) * 0.27, 0.1, 0.12, 0.08, ROBE_DARK, ry=-a)
        for i in range(3):  # drips off it
            u = (t * 0.8 + i / 3) % 1.0
            r.part(
                "cube", 0.2 - 0.18 * i, 0.5 * (1 - u) + 0.04, (i - 1) * 0.2, 0.02, 0.05, 0.02, (150, 170, 160)
            )
        r.part("cube", 0, 0.92, 0, 0.3, 0.05, 0.4, (60, 48, 36))  # a rope belt
        with r.at(0.05, 0.86, 0.24):  # a horn lantern hung beside it, burning low
            r.part("cube", 0, -0.1, 0, 0.1, 0.16, 0.1, (150, 120, 80))
            r.part("cube", 0, -0.1, 0, 0.06, 0.1, 0.06, EMBER if not dead else COLD, glow=not dead)
            r.part("cube", 0, 0.01, 0, 0.12, 0.03, 0.12, (60, 50, 40))
        with r.at(0, 0.95, 0, rz=-hunch):
            r.part("cube", 0, 0.32, 0, 0.26, 0.62, 0.42, robe)  # chest
            r.part("cube", -0.1, 0.5, 0, 0.12, 0.34, 0.46, ROBE_DARK)  # the hunched back
            r.part("cube", 0.01, 0.6, 0, 0.2, 0.08, 0.5, _dim(robe, 0.85))  # a sodden mantle
            with r.at(0.08, 0.76, 0, rz=-0.25):  # the head under its hood
                r.part("sphere", 0.02, 0, 0, 0.22, 0.26, 0.21, skin)
                r.part("cube", 0.11, 0.02, 0, 0.03, 0.04, 0.13, (60, 60, 50))  # sunken eyes
                r.part("cube", 0.11, -0.08, 0, 0.02, 0.03, 0.08, (52, 40, 36))  # a slack mouth
                r.part("sphere", -0.03, 0.04, 0, 0.3, 0.32, 0.3, ROBE_DARK)  # the hood
                r.part("cube", 0.1, 0.13, 0, 0.12, 0.06, 0.3, ROBE_DARK)  # its brow, fallen forward
            # The free arm (-Z): hangs, or spreads its hand toward the stone as the toll rings.
            with r.at(0, 0.55, -0.25, rz=_mix(0.2, 1.2, ring)):
                r.part("cube", 0, -0.15, 0, 0.09, 0.3, 0.09, robe)
                with r.at(0, -0.3, 0, rz=0.3):
                    r.part("cube", 0, -0.13, 0, 0.08, 0.26, 0.08, robe)
                    r.part("sphere", 0, -0.28, 0, 0.09, 0.09, 0.09, skin)
            # The staff arm (+Z): chops overhead, or raises the staff high to toll.
            with r.at(0, 0.55, 0.25, rz=shoulder):
                r.part("sphere", 0, 0, 0, 0.12, 0.12, 0.12, _dim(robe, 0.9))
                r.part("cube", 0, -0.15, 0, 0.09, 0.3, 0.09, robe)
                with r.at(0, -0.3, 0, rz=elbow):
                    r.part("cube", 0, -0.13, 0, 0.08, 0.26, 0.08, robe)
                    with r.at(0, -0.3, 0), held(r, wrist, skin, size=0.1, splay=0.2):
                        sexton_staff(r, t, ring, lit=not dead)


# --- the Bell-Harpy -------------------------------------------------------------------------------

HARPY_SKIN = (150, 140, 132)  # grey and drawn, like something kept too long in the dark
HARPY_WING = (104, 94, 86)
HARPY_FEATHER = (84, 76, 70)
HARPY_HAIR = (30, 26, 26)
TALON = (40, 36, 30)


def harpy_pose(e, t):
    """(wing beat, wing lift, body pitch, talon reach) for a Bell-Harpy: an easy flap on the wing, the
    wings hauled high and the body tipped forward as it gathers to stoop, swept back with its talons
    thrust out as it swoops, beating hard to climb away after. Landed (`e.landed`), it stands with its
    wings folded down its sides, mantling them high as it gathers to strike and lunging forward with a
    rake of one foot's talons."""
    beat = math.sin(t * 8.0)
    if getattr(e, "landed", False):  # (a positive lift droops the wings, a negative one raises them)
        if e.state == "windup":
            k = _windup_k(e)
            return beat * 0.2 * k, 0.5 - 1.4 * k, 0.15 + 0.2 * k, 0.0
        if e.state == "attack":
            return 0.0, -0.4, 0.6, 1.0
        if e.state in ("recover", "hurt"):
            return math.sin(t * 14.0) * 0.3, 0.2, 0.0, 0.0
        return math.sin(t * 2.0) * 0.08, 0.5, 0.2, 0.0
    if e.state == "windup":
        k = _windup_k(e)
        return beat * (1 - k) * 0.5, 0.2 + 0.9 * k, 0.5 * k, 0.3 * k
    if e.state == "attack":
        return 0.0, -0.9, 0.9, 1.0
    if e.state in ("recover", "hurt"):
        return math.sin(t * 14.0), 0.2, -0.2, 0.2
    return beat * 0.7, 0.1, 0.1, 0.0


def _harpy_wing(r, side, beat, lift, rgb, feather):
    """One wing, its leading edge (the arm) in three joints out along +-Z, a fringe of long tattered
    feathers hanging from each, wider toward the tip."""
    with r.at(0, 0, 0, rx=side * (lift + beat * 0.6)):
        r.part("cube", 0, 0, side * 0.25, 0.09, 0.08, 0.5, rgb)  # the upper arm
        for i in range(2):
            r.part("cube", -0.12, -0.12, side * (0.12 + i * 0.22), 0.26, 0.24, 0.02, feather)
        with r.at(0, 0, side * 0.5, rx=side * (0.25 + beat * 0.3)):
            r.part("cube", 0, 0, side * 0.3, 0.07, 0.06, 0.6, rgb)  # the forearm
            for i in range(3):
                r.part("cube", -0.18, -0.2, side * (0.08 + i * 0.2), 0.36, 0.38, 0.02, feather, ry=0.1 * i)
            with r.at(0, 0, side * 0.6, rx=side * (0.2 + beat * 0.25)):
                r.part("cube", 0, 0, side * 0.2, 0.05, 0.05, 0.4, rgb)  # the long finger bones
                for i in range(3):  # the ragged primaries, longest at the tip
                    r.part("cube", -0.24 - 0.04 * i, -0.06, side * (0.1 + i * 0.13), 0.5 + 0.08 * i, 0.04, 0.1,
                           feather, ry=-side * 0.15 * i)  # fmt: skip


def harpy(r, e, t):
    """A Bell-Harpy: a gaunt grey body with arms grown into great ragged wings, long black hair, and
    for a face a curved shard of a broken bronze bell, the city's teal mortar-light behind its eye slits. Bird legs end
    in hooked talons. It hangs in the air on easy beats; to stoop it hauls its wings high and tips
    forward, then sweeps them back and thrusts its talons out. Slain, it crumples in a heap of wing."""
    fall = death_fall(e, 0.7)
    dead = e.state == "dead"
    beat, lift, pitch, reach = harpy_pose(e, t)
    if dead:
        beat, lift, pitch, reach = 0.0, 0.0, 0.0, 0.0
    skin = hit_tint((236, 226, 216)) if e.flashing else HARPY_SKIN
    wing = hit_tint((200, 190, 184)) if e.flashing else HARPY_WING
    feather = hit_tint((170, 160, 156)) if e.flashing else HARPY_FEATHER
    glow = not dead
    eye = (HIT_GLOW if e.flashing else CORE_TEAL) if glow else COLD
    # It hangs from its shoulders in flight; slain, it pitches onto its face, wings spread flat.
    landed = getattr(e, "landed", False) and not dead
    with r.at(-0.3 * fall, 0.75 - 0.5 * fall, 0, rz=-pitch * (1 - fall) - 1.45 * fall):
        for side in (-1, 1):  # the legs, drawn up in flight, thrust forward to strike
            if landed:  # standing on them, bird-kneed; the right foot rakes forward to strike
                thigh, knee = pitch + 0.3 - 1.3 * reach * (side > 0), -0.6 + 0.4 * reach * (side > 0)
            else:
                thigh, knee = 0.6 - 1.4 * reach, -0.9 + 0.6 * reach
            with r.at(0, -0.05, side * 0.1, rz=thigh):
                r.part("cube", 0, -0.18, 0, 0.09, 0.36, 0.09, skin)  # the thigh
                with r.at(0, -0.36, 0, rz=knee):
                    r.part("cube", 0, -0.16, 0, 0.06, 0.32, 0.06, TALON)  # the scaled shank
                    for k in (-1, 0, 1):  # hooked talons
                        r.part("cone", 0.06, -0.34, k * 0.05, 0.03, 0.12, 0.03, TALON, rz=-1.2 + 0.2 * k)
        r.part("cube", 0, 0.25, 0, 0.26, 0.52, 0.3, skin)  # the gaunt torso
        for i in range(3):  # ribs showing through
            r.part("cube", 0.13, 0.15 + i * 0.1, 0, 0.02, 0.03, 0.26, _dim(skin, 0.75))
        r.part("cube", -0.06, 0.08, 0, 0.2, 0.2, 0.26, feather)  # the ragged down at its hips
        with r.at(0, 0.48, 0):  # the shoulders, from which the wings spread
            for side in (-1, 1):
                with r.at(0, 0, side * 0.14):
                    _harpy_wing(r, side, beat * (1 - fall), lift * (1 - fall), wing, feather)
            with r.at(0.04, 0.16, 0):  # the head
                r.part("sphere", 0, 0, 0, 0.18, 0.2, 0.17, skin)
                for i in range(4):  # long black hair, hanging lank behind
                    r.part("cube", -0.1, -0.14 - 0.04 * (i % 2), (i - 1.5) * 0.06, 0.06, 0.34, 0.05, HARPY_HAIR,
                           rz=0.25)  # fmt: skip
                with r.at(0.09, 0.01, 0):  # the mask: a curved shard of a bell
                    r.part("cube", 0, 0, 0, 0.05, 0.22, 0.2, BELL_BRONZE)
                    r.part("cube", 0.01, 0.1, 0, 0.05, 0.03, 0.22, _dim(BELL_BRONZE, 0.75))  # its lip
                    r.part("cube", 0.03, -0.1, 0.04, 0.03, 0.06, 0.04, _dim(BELL_BRONZE, 0.85))  # broken edge
                    for side in (-1, 1):  # eye slits, a small flare of the mortar-light at each
                        r.part("cube", 0.03, 0.03, side * 0.05, 0.02, 0.025, 0.05, eye, glow=glow)
                        if glow:
                            r.part("sphere", 0.04, 0.03, side * 0.05, 0.02, 0.03, 0.04,
                                   _mix_rgb(CORE_TEAL, CORE_HEART, 0.5), glow=True)  # fmt: skip
                    r.part("cube", 0.03, -0.06, 0, 0.02, 0.02, 0.07, (40, 30, 24))  # the mouth slot


# --- the Keystone ---------------------------------------------------------------------------------

KEYSTONE_SCALE = 2.4  # the Keystone is a Stone Golem's body this many times over: some 6.5 m
KEYSTONE_BARE = (58, 66, 62)  # the stone under its shell, once the shell has sloughed off: dark and wet
COLUMN_STONE = (150, 140, 120)  # the broken columns it wears, pale with the years
SHELL_PLATES = (  # (x, y, z, size) of the boulder plates over its body, in the leaning body's frame
    (0.1, 1.42, -0.55, 0.36),
    (0.1, 1.42, 0.55, 0.36),
    (-0.38, 1.1, 0.0, 0.42),
    (0.28, 0.42, -0.42, 0.24),
    (0.28, 0.42, 0.42, 0.24),
    (-0.3, 0.55, 0.0, 0.3),
)
# Cracks the mortar-light shows through, (y, z, tilt) on its front: the first few while its shell
# holds, every one of them once it sloughs off.
VEINS = (
    (0.62, -0.3, 0.4),
    (1.1, 0.5, -0.5),
    (0.4, 0.2, -0.2),
    (1.3, -0.55, 0.3),
    (0.8, 0.62, 0.6),
    (0.25, -0.15, 0.5),
    (1.18, 0.1, -0.7),
    (0.55, 0.45, 0.2),
    (0.95, -0.66, -0.4),
    (0.2, 0.32, 0.7),
)
SHELL_VEINS = 4
CORE_Y = 0.62  # the chest core's height in the leaning body's frame, under its head
ARM_SLUMP = 0.4  # how its arms swing, and its elbows bend, as it slumps forward on its fists
ELBOW_SLUMP = 1.4


HURL_HOLD = (3.25, -1.0)  # (arm swing, elbow) holding the boulder up over its head, elbows bent


def keystone_pose(e):
    """(lean, left arm, left elbow, right arm, right elbow, stamp, hurl, charge) for its moves: the lean
    forward of its body, each arm's swing (radians from hanging, forward) and elbow bend, how high it
    lifts its foot to stamp (0..1), how far it has heaved up a boulder to throw (0..1, -1 once let go),
    and how hard its chest core draws in the mortar-light (0..1). Every blow travels down over its
    type's `impact`, heavily, rather than snapping."""
    k = _ease(_windup_k(e))
    hitting = e.state == "attack"
    snap = _ease(min(e.state_t / max(0.15, e.type.impact), 1.0)) if hitting else 0.0
    kind = e.attack_kind if e.state in ("windup", "attack") else None
    if kind == "slab_smash":  # the right slab heaved back overhead, then brought down before it
        if not hitting:
            return -0.2 * k, 0.1, 0.3, -3.0 * k, 0.5 * k, 0.0, 0.0, 0.3 * k
        return -0.2 + 0.65 * snap, 0.1, 0.3, -3.0 + 3.9 * snap, 0.5 - 0.4 * snap, 0.0, 0.0, 0.3
    if kind == "shard_rain":  # both slabs thrust up overhead and shaken, shards torn off its shell
        shake = math.sin(e.anim_t * 14) * (0.12 * k if not hitting else 0.3)
        charge = k if not hitting else 1.0
        return -0.15 * k, -2.9 * k + shake, 0.4 * k, -2.9 * k - shake, 0.4 * k, 0.0, 0.0, charge
    if kind == "core_nova":  # both fists lifted high, then driven down at its feet
        if not hitting:
            return -0.12 * k, -2.7 * k, 0.3, -2.5 * k, 0.3, 0.0, 0.0, k
        up = 0.3 + 0.5 * snap
        return -0.12 + 0.55 * snap, -2.7 + 3.3 * snap, up, -2.5 + 3.0 * snap, up, 0.0, 0.0, 1.0
    if kind == "core_beam":  # it rears, arms flung back to bare its heart, then bows to rake the floor
        if not hitting:
            return -0.3 * k, -0.9 * k, 0.2, -0.9 * k, 0.2, 0.0, 0.0, k
        return -0.3 + 0.75 * snap, -0.9, 0.2, -0.9, 0.2, 0.0, 0.0, 1.0
    if kind == "pillar_crush":  # both fists raised high together, rearing back, then hammered down before it
        if not hitting:
            return -0.3 * k, -3.1 * k, 0.15 * k, -3.1 * k, 0.15 * k, 0.0, 0.0, 0.5 * k
        down = -3.1 + 4.1 * snap
        return -0.3 + 0.85 * snap, down, 0.15, down, 0.15, 0.0, 0.0, 0.5
    if kind == "fault_line":  # the foot lifted high, arms flung out fore and aft for balance, then stamped
        if not hitting:
            return 0.15 * k, 0.8 * k, 0.4, -1.1 * k, 0.4, k, 0.0, 0.6 * k
        return 0.15 + 0.25 * snap, 0.8 - 0.4 * snap, 0.4, -1.1 + 0.6 * snap, 0.4, 1.0 - snap, 0.0, 0.6
    if kind == "quake":  # the foot rises high
        return -0.1 * k, 0.3 - 0.6 * k, 0.6, -0.6 * k, 0.6, (k if not hitting else 1.0 - snap), 0.0, 0.0
    if kind == "hurl":  # a boulder heaved up off the floor in both arms, up before it and over its head
        if not hitting:
            up, bend = HURL_HOLD[0] * k, HURL_HOLD[1] * k
            return -0.3 * k, up, bend, up, bend, 0.0, max(k, 0.05), 0.0
        up, bend = HURL_HOLD[0] - 0.8 * snap, HURL_HOLD[1] * (1 - 0.5 * snap)  # then flung forward
        held_ = 1.0 if e.state_t < e.type.impact else -1.0  # it lets go as its blow lands
        return -0.3 + 0.6 * snap, up, bend, up, bend, 0.0, held_, 0.0
    if e.state == "hurt":
        return -0.2, 0.5, 0.5, 0.4, 0.5, 0.0, 0.0, 0.0
    sway = math.sin(e.anim_t * 1.6) * 0.08
    return sway * 0.5, 0.1 + sway * 0.5, 0.25, 0.1 - sway, 0.25, 0.0, 0.0, 0.0


def _knuckle_guard(r, side, lit, split, wide):
    """The broken column stubs it has driven over its knuckles, a fluted drum across each fist."""
    for y, z in ((-0.98, 0.0), (-1.22, side * 0.06)):
        r.part("cyl", 0.42 * wide, y, z, 0.24, 0.66 * wide, 0.24, COLUMN_STONE, tex=GOLEM_TEX,
               rx=math.pi / 2)  # fmt: skip
    r.part("cube", 0.42 * wide, -1.1, 0, 0.27, 0.06, 0.7 * wide, _dim(COLUMN_STONE, 0.7))  # their seam


def _keystone_core(r, t, lit, split, charge, flashing):
    """Its heart: a core of the mortar-light bared in the middle of its chest, in a cage of stone
    ribs. It glows while it lives, blazes once its shell has sloughed off, and swells as it draws in
    the light for a move (`charge`)."""
    pulse = 0.5 + 0.5 * math.sin(t * (3.0 if not split else 5.0))
    glow = 0.3 + 0.4 * pulse + 0.3 * charge if not split else 0.6 + 0.4 * pulse
    core = HIT_GLOW if flashing else _mix_rgb(CORE_TEAL, CORE_HEART, glow * 0.6) if lit else COLD
    heart = HIT_GLOW if flashing else CORE_HEART if lit else COLD
    s = 1.2 + 0.25 * charge + (0.2 if split else 0.0)
    r.part("sphere", 0.46, CORE_Y, 0, 0.26 * s, 0.32 * s, 0.36 * s, core, glow=lit)
    r.part("lozenge", 0.58, CORE_Y, 0, 0.12 * s, 0.26 * s, 0.12 * s, heart, glow=lit, ry=t * 0.8)
    if split and lit:  # blazing: a halo of light round it
        r.part("sphere", 0.5, CORE_Y, 0, 0.42 * s, 0.52 * s, 0.56 * s, _dim(CORE_TEAL, 0.55), glow=True)
    for y in (-0.2, 0.0, 0.2):  # the cage of stone ribs over it, open down the middle
        for side in (-1, 1):
            r.part("cube", 0.6, CORE_Y + y, side * 0.2, 0.08, 0.08, 0.28, _dim(GOLEM_STONE, 1.1), tex=GOLEM_TEX,
                   ry=side * 0.6)  # fmt: skip
    r.part("cube", 0.56, CORE_Y + 0.34, 0, 0.12, 0.1, 0.6, GOLEM_DARK, tex=GOLEM_TEX)  # its collar of rock


def keystone(r, e, t):
    """The Stone Golems' giant, some 6.5 m of the same hunched body: a chest of faceted grey-green rock
    over a narrow waist, short thick legs, a small head set low and forward under its shoulders, and
    arms that hang to the ground, each forearm a slab of rock with broken columns driven over its
    knuckles. In the middle of its chest the mortar-light that animates them all is bared: a teal core
    in a cage of stone ribs, its light running out through cracks in the boulder plates of its shell.
    On its hump stand the stubs of the columns it once bore up. At half HP the shell sloughs off: the
    plates fall away, the dark stone under them is laced with veins of light, the core blazes, its eyes
    flare and motes of light lift off it. It brings a slab down before it, hammers both fists down
    together, stamps a fault of light along the floor and heaves a boulder up overhead in both arms to
    lob at you; then it stamps (the foot rises high), rakes a beam of the light along the floor from
    its heart, rains shards of its shell down round you and drives its fists down so rings of light
    run out from it. Slain, it sinks to its knees and slumps forward on its fists, and the light
    in it goes out."""
    dead = e.state == "dead"
    lit = not dead
    split = e.phase2 and lit
    kneel = death_fall(e, 0.9)
    slump = death_fall(e, 2.0)
    lean, left, left_elbow, right, right_elbow, stamp, hurl, charge = keystone_pose(e)
    acting = e.state in ("windup", "attack")
    raining = e.attack_kind == "shard_rain" and acting and lit
    beaming = e.attack_kind == "core_beam" and e.state == "attack" and lit
    swing = walk_cycle(e, t) * 0.25
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    flashing = e.flashing
    base = KEYSTONE_BARE if e.phase2 else GOLEM_STONE
    stone = hit_tint((220, 232, 214)) if flashing else base
    dark = hit_tint((190, 200, 186)) if flashing else _dim(base, 0.75)
    eye = HIT_GLOW if flashing else CORE_HEART if split else CORE_TEAL
    vein = HIT_GLOW if flashing else _mix_rgb(CORE_TEAL, CORE_HEART, 0.4) if split else _dim(CORE_TEAL, 0.8)
    veins = VEINS if e.phase2 else VEINS[:SHELL_VEINS]
    vein_w = 0.07 if split else 0.04
    moss = MOSS if not e.phase2 else _dim(MOSS, 0.5)
    hunch = GOLEM_HUNCH + lean + 0.3 * slump
    with r.at(0, lift * 0.3, 0, ry=spin, s=KEYSTONE_SCALE), r.at(0, -0.4 * kneel, 0):
        for i, z in enumerate((-0.38, 0.38)):  # short thick legs; the right one stamps
            raise_ = stamp if i == 1 else 0.0
            a = (swing if i else -swing) * (1 - kneel)
            with r.at(0, 0.38 * raise_, 0):
                _golem_leg(r, z, a + 0.5 * raise_ + 1.5 * kneel, -0.6 * raise_ - 1.4 * kneel, stone, dark)
        r.part("cube", 0, GOLEM_HIP + 0.04, 0, 0.6, 0.28, 0.92, dark, tex=GOLEM_TEX)  # the hips
        with r.at(0, GOLEM_WAIST, 0, rz=-hunch):
            _golem_torso(r, stone, dark, moss, vein if lit else COLD, lit)
            _keystone_core(r, t, lit, split, charge, flashing)
            for i, (x, y, z, s) in enumerate(SHELL_PLATES):  # its shell: most of it sloughed off at last
                if e.phase2 and i not in (1, 5):
                    continue
                r.part("cube", x, y, z, s * 1.1, s, s * 1.3, _dim(GOLEM_STONE, 0.9 + 0.06 * (i % 3)),
                       tex=GOLEM_TEX, rx=0.3 * (i % 3 - 1), ry=0.25 * (i % 2), rz=0.35 - 0.2 * i)  # fmt: skip
            for y, z, a in veins:  # the cracks the light shows through
                r.part("cube", 0.56, y, z, 0.03, 0.42, vein_w, vein if lit else COLD, rx=a, glow=lit)
            if split:  # down its back too, and motes of light lifting off its shoulders
                for z in (-0.4, 0.0, 0.4):
                    r.part("cube", -0.5, 0.9, z, 0.03, 0.7, 0.06, vein, rz=0.2, glow=True)
                for i in range(6):
                    u = (t * 0.45 + i / 6) % 1.0
                    side = 1 if i % 2 else -1
                    r.part("cube", -0.1 + 0.12 * math.sin(t + i), 1.5 + u * 0.9, side * (0.4 + 0.15 * u),
                           0.04, 0.04, 0.04, _dim(CORE_TEAL, 1.0 - 0.6 * u), glow=True)  # fmt: skip
            for z in (-0.5, 0.2, 0.62):  # roots hanging out of its seams
                r.part("cube", 0.5, 0.5, z, 0.02, 0.36, 0.02, (90, 70, 48), rx=0.2 * z)
            for x, z, h in ((-0.3, -0.3, 0.32), (-0.2, 0.34, 0.24), (-0.5, 0.05, 0.4)):
                # The broken columns it bore the city on, still standing on its hump.
                with r.at(x, 1.46, z, rz=hunch * 0.8):
                    r.part("cyl", 0, h / 2, 0, 0.16, h, 0.16, COLUMN_STONE if not e.phase2 else _dim(stone, 1.2),
                           tex="rough_stone")  # fmt: skip
                    r.part("cube", 0, h + 0.01, 0, 0.13, 0.03, 0.12, _dim(COLUMN_STONE, 0.75), ry=x * 3)
            with r.at(*GOLEM_HEAD, 0, rz=hunch - 0.1):  # the head looks ahead, whatever the body does
                _golem_head(r, stone, dark, eye, lit, flare=1.0 if split else 0.0)
                for i in range(3):  # a beard of moss and roots
                    r.part("cube", 0.14, -0.28 - 0.04 * (i % 2), (i - 1) * 0.1, 0.06, 0.2 + 0.06 * (i % 2),
                           0.06, _dim(moss if i % 2 else (84, 66, 46), 1.0))  # fmt: skip
            if beaming:  # the beam it rakes along the floor, out of its heart
                with r.at(0.6, CORE_Y, 0, rz=-1.0 + hunch):
                    r.part("cube", 1.4, 0, 0, 2.8, 0.1, 0.1, CORE_HEART, glow=True)
                    r.part("cube", 1.4, 0, 0, 2.8, 0.22, 0.22, _dim(CORE_TEAL, 0.8), glow=True)
            sx, sy, sz = GOLEM_SHOULDER
            for side, a, elbow in ((1, right, right_elbow), (-1, left, left_elbow)):
                a, elbow = a + ARM_SLUMP * slump, elbow + ELBOW_SLUMP * slump  # down onto its fists
                with r.at(sx, sy, side * sz, rz=GOLEM_HUNCH):
                    _golem_arm(r, side, a, elbow, stone, dark, vein, lit, wide=1.15)
                    with r.at(0, 0, 0, rz=a), r.at(0, -0.66, 0, rz=elbow):
                        _knuckle_guard(r, side, lit, split, 1.15)
                        if hurl > 0 and side == 1:  # the boulder it is about to throw, between its fists
                            with r.at(0.5, -1.45, -sz, s=BOULDER_HELD):
                                boulder(r, t)
                        if raining:  # shards of its shell torn loose over its fists, glowing
                            for i in range(3):
                                u = (t * 1.6 + i / 3) % 1.0
                                r.part("lozenge", 0.2 * math.sin(t * 3 + i), -1.5 - 0.6 * u, 0.15 * (i - 1),
                                       0.06, 0.14, 0.06, CORE_TEAL, glow=True, ry=t * 4 + i)  # fmt: skip


BOULDER_STONE = (150, 132, 104)  # masonry torn from the old city: its warm sandstone
BOULDER_HELD = 0.42  # the boulder's size in the Keystone's grip, in its unscaled body's units


def boulder(r, t, spin=0.0):
    """The boulder the Keystone heaves up and lobs (a `hazards.Eruption` of style "boulder" in flight),
    some 2 m of masonry: a squared block with a cornice still on it, lumps of rubble mortared to it and
    a cracked seam of the mortar-light, grit trailing off it as it tumbles (`spin`)."""
    with r.at(0, 0, 0, rx=spin * 2.2, rz=spin * 1.6):
        r.part("cube", 0, 0, 0, 1.7, 1.4, 1.5, BOULDER_STONE, tex="rough_stone")
        r.part("cube", 0.1, 0.72, 0, 1.85, 0.22, 1.6, _dim(BOULDER_STONE, 0.85), tex="rough_stone")  # cornice
        for x, y, z, w in ((0.7, -0.3, 0.6, 0.7), (-0.75, 0.2, -0.5, 0.8), (0.2, -0.65, -0.6, 0.6)):
            r.part("cube", x, y, z, w, w * 0.8, w * 0.9, _dim(BOULDER_STONE, 0.75), ry=x + z, rz=y)
        r.part("cube", 0.86, 0, 0.1, 0.04, 1.0, 0.08, CORE_TEAL, rx=0.4, glow=True)  # a seam of light
        r.part("cube", -0.3, -0.71, 0.2, 0.9, 0.04, 0.08, _dim(CORE_TEAL, 0.8), ry=0.6, glow=True)
    for i in range(4):  # grit trailing off it
        a = t * 6 + i * 1.6
        r.part("cube", -0.9 - 0.25 * i, math.sin(a) * 0.3, math.cos(a) * 0.3, 0.12, 0.12, 0.12,
               _dim(BOULDER_STONE, 0.7))  # fmt: skip


def boulder_mark(r, glow, flame, t, radius=1.0):
    """Where the Keystone's boulder will come down (an `Eruption` of style "boulder"): its shadow
    darkening on the floor and a ring of amber cracks closing in as it falls, then a burst of dust and
    broken stone where it lands, `radius` across."""
    if glow > 0:
        r.part("cyl", 0, 0.02, 0, radius * (0.4 + 0.6 * glow), 0.02, radius * (0.4 + 0.6 * glow),
               _dim(MORTAR, 0.6))  # fmt: skip  # its shadow
        ring = radius * (1.7 - 0.7 * glow)  # closing in as it falls
        for i in range(10):
            a = i * math.tau / 10 + t * 0.3
            r.part("cube", math.cos(a) * ring, 0.04, math.sin(a) * ring, 0.55 * radius, 0.03, 0.08,
                   _mix_rgb(_dim(EYE, 0.4), EYE, glow), ry=-a + math.pi / 2, glow=True)  # fmt: skip
    if flame > 0:
        h = 2.4 * flame
        r.part("cyl", 0, h / 2, 0, radius * 1.4, h, radius * 1.4, _dim(MASONRY, 0.9))  # the dust thrown up
        for i in range(8):  # the boulder's pieces, flung out
            a = i * math.tau / 8 + 0.3
            d = radius * (0.5 + 0.6 * flame)
            r.part("cube", math.cos(a) * d, 0.3 + h * 0.4 * (1 - 0.5 * (i % 2)), math.sin(a) * d,
                   0.4, 0.32, 0.36, _dim(BOULDER_STONE, 0.8 + 0.05 * (i % 3)), rx=t * 4 + i, ry=a)  # fmt: skip


def core_burst(r, glow, flame, t, radius=1.0):
    """The mortar-light bursting up through the floor (a `hazards.Eruption` of style "core", the
    Keystone's): a ring of teal cracks spreading where it will strike, then a column of hard light with
    shards of stone flung up in it, as wide as the burst's `radius`."""
    k = radius
    if glow > 0:
        for i in range(6):
            a = i * math.pi / 3 + t * 0.4
            r.part("cube", math.cos(a) * 0.7 * k, 0.03, math.sin(a) * 0.7 * k, 0.5 * k, 0.03, 0.06,
                   _mix_rgb(_dim(CORE_TEAL, 0.5), CORE_TEAL, glow), ry=-a + math.pi / 2, glow=True)  # fmt: skip
        r.part("cyl", 0, 0.02, 0, 0.7 * glow * k, 0.02, 0.7 * glow * k, CORE_TEAL, glow=True)
    if flame > 0:
        h = 3.0 * flame * (1 + 0.4 * (k - 1))
        r.part("cyl", 0, h / 2, 0, 1.1 * k, h, 1.1 * k, _dim(CORE_TEAL, 0.75), glow=True)
        r.part("cyl", 0, h * 0.55, 0, 0.45 * k, h * 1.1, 0.45 * k, CORE_HEART, glow=True)
        for i in range(4):  # shards flung up in it
            a = i * math.pi / 2 + t * 2
            r.part("lozenge", math.cos(a) * 0.6 * k, h * (0.3 + 0.15 * i), math.sin(a) * 0.6 * k,
                   0.1, 0.24, 0.1, GOLEM_STONE, ry=a)  # fmt: skip


def core_shard(r, t):
    """A shard of the Keystone's shell flung out on an arc, the light still in it."""
    r.part("lozenge", 0, 0, 0, 0.26, 0.6, 0.26, GOLEM_STONE, rx=t * 5, rz=t * 3)
    r.part("lozenge", 0, 0, 0, 0.14, 0.7, 0.14, CORE_TEAL, rx=t * 5, rz=t * 3, glow=True)
    for i in range(2):
        r.part(
            "cube", -0.15 - 0.15 * i, 0.08 * i, 0, 0.06, 0.06, 0.06, _dim(CORE_TEAL, 0.8 - 0.3 * i), glow=True
        )


def core_ring(r, k, radius):
    """A ring of the mortar-light running out across the floor from where the Keystone struck."""
    d = radius * k
    size = 0.3 * (1 - k) + 0.08
    for i in range(16):
        a = i * math.pi / 8
        rgb = CORE_TEAL if i % 2 else GOLEM_STONE
        r.part("cube", math.cos(a) * d, 0.1 + 0.2 * (1 - k), math.sin(a) * d, size, size, size, rgb,
               ry=a, glow=i % 2 == 1)  # fmt: skip


# --- Old Harrowmere's dressing --------------------------------------------------------------------


# --- weapons (grip at the origin, pointing up +Y, like weapon_models.weapon) ---------------------------

SIGNAL_STONE = (150, 136, 112)  # the brazier-hammer's pale stone haft
CAGE_IRON = (52, 48, 46)
COAL = (255, 110, 36)
EMBER_SEAM = (255, 150, 60)


def torch_greathammer(r):
    """The bell-keepers' signal brazier on a stone haft: a long column of pale stone banded in iron,
    then a squat iron cage full of coals, a flat iron striking plate on +Z, a short spike on -Z and
    flames licking up out of the cage."""
    r.part("cube", 0, 0.36, 0, 0.08, 1.34, 0.08, SIGNAL_STONE)  # the haft
    for k in range(4):
        r.part("cube", 0, 0.02 + k * 0.24, 0, 0.095, 0.035, 0.095, CAGE_IRON)
    r.part("cube", 0, -0.22, 0, 0.09, 0.24, 0.09, (78, 58, 40))  # the grip
    r.part("cube", 0, -0.37, 0, 0.12, 0.06, 0.12, CAGE_IRON)
    with r.at(0, 1.12, 0):
        r.part("cube", 0, -0.16, 0, 0.3, 0.05, 0.42, CAGE_IRON)  # the cage's floor
        for dx in (-0.14, 0.14):  # ...its open rim
            r.part("cube", dx, 0.16, 0, 0.03, 0.04, 0.42, CAGE_IRON)
        for dz in (-0.2, 0.2):
            r.part("cube", 0, 0.16, dz, 0.3, 0.04, 0.03, CAGE_IRON)
        for dx in (-0.13, 0.13):  # bars
            for dz in (-0.19, 0.0, 0.19):
                r.part("cube", dx, 0, dz, 0.03, 0.32, 0.03, CAGE_IRON)
        r.part("cube", 0, -0.02, 0, 0.26, 0.22, 0.38, COAL, glow=True)  # the coals, heaped to the bars
        r.part("cube", 0, 0, 0.23, 0.34, 0.34, 0.04, (88, 84, 82))  # the striking plate
        for dx in (-0.09, 0.09):
            r.part("cube", dx, 0, 0.255, 0.05, 0.28, 0.02, (120, 116, 112))
        r.part("wedge", 0, 0, -0.3, 0.1, 0.14, 0.1, CAGE_IRON, rx=-math.pi / 2)  # the spike
        for dz, size in ((-0.12, 0.1), (0.03, 0.14), (0.14, 0.09)):  # the flames licking out of it
            r.part("cone", 0, 0.1 + size, dz, size * 1.2, size * 2.6, size * 1.2, (255, 140, 40), glow=True)
            r.part("cone", 0, 0.08 + size, dz, size * 0.6, size * 1.8, size * 0.6, (255, 230, 150), glow=True)


def ember_stone_sword(r):
    """A slab of grey foundation stone ground to an edge, set in a plain iron guard, with seams of
    ember glowing through both faces and a coal for a pommel stone."""
    blade_parts(
        r,
        1.2,
        0.16,
        (118, 112, 106),
        thick=0.05,
        edge=(160, 154, 146),
        fuller=(84, 78, 72),
        guard="straight",
        guard_w=0.34,
        guard_rgb=CAGE_IRON,
        grip=0.24,
        grip_rgb=(60, 44, 34),
        wrap=(96, 76, 54),
        pommel="stopper",
        pommel_rgb=CAGE_IRON,
    )
    for i in range(6):  # the glowing seams, splitting the stone on both faces
        y = 0.3 + i * 0.16
        for side in (-1, 1):
            r.part(
                "cube",
                side * 0.027,
                y,
                0.02 * (-1) ** i,
                0.01,
                0.14,
                0.018,
                EMBER_SEAM,
                rx=0.5 * (-1) ** i,
                glow=True,
            )
    r.part("sphere", 0, -0.17, 0, 0.04, 0.04, 0.04, COAL, glow=True)


def vault_rift(r, height=14.0, rift=(CRACK_LEN, CRACK_WIDTH), yaw=0.0):
    """The rift in the cavern's roof far overhead, where the daylight shows through: a jagged sliver
    of light set in the vault's hole (`world/vault.py`), a rim of gold round it where the daylight
    catches the rock's broken lip. Drawn from a `sun_shaft`'s floor tile, `height` metres below it
    and leaning off by SHAFT_LEAN; `rift` (length, width) and `yaw` (radians) shape the crack. No
    beam falls from it: the light stays up in the roof."""
    length, crack_w = rift
    with r.at(-height * math.sin(SHAFT_LEAN), height * math.cos(SHAFT_LEAN), 0, ry=yaw):  # the crack
        r.part("cube", 0, 0.6, 0, crack_w * 1.2, 0.1, length * 1.1, (255, 248, 228), glow=True)
        n = max(5, rround(length / 1.4))
        for i in range(n):  # the sliver, jagged: wider and narrower along its length
            z = (i / (n - 1) - 0.5) * length * 0.85
            w = crack_w * (0.45 + 0.25 * ((i * 3) % 4) / 3)
            r.part("cube", 0.1 * (i % 2), 0.3, z, w, 0.12, length * 1.2 / n, (255, 244, 210), glow=True,
                   ry=0.25 * (i % 3 - 1))  # fmt: skip
        for side in (-1, 1):  # its rim of gold, where the daylight catches the rock's broken lip
            r.part("cube", side * crack_w * 0.45, -0.1, 0, 0.3 + crack_w * 0.04, 0.4, length * 0.95,
                   GOLD_LIGHT, tex="mist", glow=True, ry=side * 0.06)  # fmt: skip


def rift_lance(r, rgb, t):
    """A Rift Lance flying point first (+X): a long sliver of daylight, white at its heart, with a
    sheath of gold, two thin blades of light flaring off its sides and motes of dust in its wake."""
    r.part("lozenge", 0.0, 0, 0, 1.3, 0.07, 0.07, rgb, glow=True)  # the sliver
    r.part("cube", 0.05, 0, 0, 1.1, 0.03, 0.03, (255, 252, 236), glow=True)  # its white heart
    r.part("cone", 0.8, 0, 0, 0.07, 0.3, 0.07, (255, 246, 220), rz=-math.pi / 2, glow=True)  # the point
    flare = 0.8 + 0.2 * math.sin(t * 18)
    for side in (-1, 1):  # blades of light flaring off its sides
        r.part(
            "cube", -0.1, 0, side * 0.09, 0.7 * flare, 0.01, 0.05, _dim(rgb, 0.9), glow=True, ry=side * 0.12
        )
    for i in range(4):  # dust turning in its wake
        u = (t * 2.5 + i / 4) % 1.0
        r.part("cube", -0.7 - 0.7 * u, math.sin(i * 2.1) * 0.1, math.cos(i * 1.4) * 0.1, 0.04, 0.04, 0.04,
               _dim(GOLD_LIGHT, 1 - 0.6 * u), glow=True)  # fmt: skip


# --- the roads of light --------------------------------------------------------------------------

# The three sets of ward decks and the crystals that turn them: set "a" burns gold like the rift's
# daylight, set "b" pale blue like the water falling past it, set "c" teal like the mortar-light that
# feeds it.
WARD_RGB = {"a": (255, 200, 110), "b": (140, 200, 255), "c": CORE_TEAL}
WARD_STONE = (110, 100, 90)


def ward_deck(r, t, k, ward):
    """A span of one of the masons' roads of light over the chasm: a slab of translucent light set in a
    frame of rune-bars, a shimmer running across it. `k` (0..1) is how far it has woken: it grows in
    from its frame and fades back into it, and only the frame's runes glow while it sleeps."""
    rgb = WARD_RGB[ward]
    for side in (-1, 1):  # the frame's rune-bars along its two edges, always faintly there
        r.part("cube", 0, -0.05, side * 0.9, 1.9, 0.06, 0.08, _dim(rgb, 0.35 + 0.45 * k), glow=True)
        for i in range(3):
            r.part(
                "cube",
                (i - 1) * 0.6,
                -0.02,
                side * 0.9,
                0.12,
                0.05,
                0.12,
                _dim(rgb, 0.5 + 0.5 * k),
                glow=True,
            )
    if k <= 0.02:
        return
    shimmer = 0.85 + 0.15 * math.sin(t * 3.0)
    r.part("cube", 0, -0.06, 0, 1.9 * k, 0.08, 1.8 * k, _dim(rgb, 0.7 * shimmer), tex="mist", glow=True)
    r.part("cube", 0, -0.04, 0, 1.6 * k, 0.04, 0.12, _dim(rgb, shimmer), glow=True)  # the road's spine
    u = (t * 0.5) % 1.0
    r.part("cube", (u - 0.5) * 1.8 * k, -0.02, 0, 0.1, 0.04, 1.6 * k, (255, 250, 236), glow=True)  # a ripple


def ward_crystal(r, t, active):
    """A ward-stone: a squat pedestal of old masonry carved with the masons' marks, and on it a tall
    crystal turning slowly, burning the colour of the road that stands (`active`), a ring of motes
    round it."""
    rgb = WARD_RGB[active]
    r.part("cube", 0, 0.35, 0, 0.9, 0.7, 0.9, WARD_STONE)  # the pedestal
    r.part("cube", 0, 0.74, 0, 1.0, 0.08, 1.0, _dim(WARD_STONE, 1.15))  # its cap
    for i in range(4):  # the masons' marks on its faces
        a = i * math.pi / 2
        r.part("cube", math.cos(a) * 0.46, 0.38, math.sin(a) * 0.46, 0.04, 0.3, 0.04, _dim(rgb, 0.6),
               glow=True, ry=a)  # fmt: skip
    pulse = 0.8 + 0.2 * math.sin(t * 2.4)
    with r.at(0, 1.35, 0, ry=t * 0.6):
        r.part("lozenge", 0, 0, 0, 0.36, 1.1, 0.36, _dim(rgb, pulse), glow=True)
        r.part("lozenge", 0, 0, 0, 0.18, 0.8, 0.18, (255, 252, 240), glow=True)  # its white heart
    for i in range(5):  # motes circling it
        a = t * 1.2 + i * math.tau / 5
        r.part("cube", math.cos(a) * 0.5, 1.2 + 0.3 * math.sin(t * 2 + i), math.sin(a) * 0.5, 0.05, 0.05, 0.05,
               rgb, glow=True)  # fmt: skip


# --- the energy core (the mortar-light) -------------------------------------------------------


TETHER_Y = 1.8  # where a core's tether meets its golem, over its feet


def energy_core(r, t, height=1.2, quenched=False, shielded=False, tethers=(), yaw=0.0, scale=1.0):
    """The energy core, all of it sized by `scale` (its tethers still meet their golems): see `_energy_core`."""
    with r.at(0, 0, 0, s=scale):
        ends = [(dx / scale, (dy + TETHER_Y) / scale - TETHER_Y, dz / scale) for dx, dy, dz in tethers]
        _energy_core(r, t, height, quenched, shielded, ends, yaw)


def _energy_core(r, t, height, quenched, shielded, tethers, yaw):
    """The energy core: the mortar-light that animates the giants. A carved plinth `height` tall of
    stacked masonry, the masons' marks cut in its faces glowing teal, four stone claws rising from its
    cap to cradle a great faceted crystal heart (about 1.2 m) floating over it, turning slowly and
    breathing light, stone shards orbiting it. Thin teal tethers run from it to every golem it
    sustains (`tethers`: their offsets in world axes; `yaw` is the prop's heading, undone for them),
    beads of light running out along them. While its ward stands (`shielded`) a lattice dome of light
    covers it. Quenched, the crystal lies split in its cradle, grey and cold, the marks dark, the shards fallen."""
    breath = 0.5 + 0.5 * math.sin(t * 1.6)
    lit = not quenched
    mark = COLD if quenched else _dim(CORE_TEAL, 0.6 + 0.4 * breath)
    r.part("cube", 0, 0.12, 0, 1.9, 0.24, 1.9, MASONRY_DARK, tex="rough_stone")  # its footing
    r.part("cube", 0, 0.24 + height * 0.22, 0, 1.5, height * 0.44, 1.5, MASONRY, tex="rough_stone")
    r.part("cube", 0, 0.24 + height * 0.47, 0, 1.62, 0.08, 1.62, MASONRY_DARK, tex="rough_stone")
    r.part("cube", 0, 0.24 + height * 0.74, 0, 1.3, height * 0.46, 1.3, MASONRY, tex="rough_stone")
    top = 0.24 + height
    r.part("cube", 0, top - 0.05, 0, 1.55, 0.12, 1.55, _dim(MASONRY, 1.1), tex="rough_stone")  # its cap
    for i in range(4):  # the masons' marks on each face: a stroke under a chevron, a bar above
        a = i * math.pi / 2
        with r.at(math.cos(a) * 0.76, 0.24 + height * 0.22, -math.sin(a) * 0.76, ry=a):
            r.part("cube", 0, 0, 0, 0.03, height * 0.3, 0.05, mark, glow=lit)
            for side in (-1, 1):
                r.part("cube", 0, height * 0.14, side * 0.07, 0.03, 0.04, 0.18, mark, glow=lit, rx=side * 0.7)
        with r.at(math.cos(a) * 0.66, 0.24 + height * 0.74, -math.sin(a) * 0.66, ry=a):
            r.part("cube", 0, 0, 0, 0.03, 0.05, 0.4, mark, glow=lit)
    for i in range(4):  # the stone claws rising off the cap's corners to cradle the heart
        a = math.pi / 4 + i * math.pi / 2
        with r.at(math.cos(a) * 0.62, top, -math.sin(a) * 0.62, ry=a):
            r.part("cube", 0, 0.25, 0, 0.18, 0.55, 0.18, MASONRY_DARK, tex="rough_stone", rz=0.35)
            r.part("cube", -0.17, 0.62, 0, 0.13, 0.35, 0.13, MASONRY, tex="rough_stone", rz=0.9)
    heart_y = top + 1.05
    if quenched:
        for side in (-1, 1):  # the heart, split in two and fallen into its cradle
            r.part("lozenge", side * 0.18, top + 0.45, 0.05 * side, 0.4, 0.95, 0.4, CORE_DEAD,
                   rz=side * 0.5, ry=0.3)  # fmt: skip
        r.part("cube", 0, top + 0.12, 0, 0.5, 0.03, 0.04, COLD, ry=0.7)  # a crack across the cap
        for i in range(5):  # the shards it held up, fallen
            a = i * 1.3
            r.part("lozenge", math.cos(a) * 1.05, 0.08, math.sin(a) * 1.05, 0.14, 0.32, 0.14, MASONRY_DARK,
                   tex="rough_stone", rz=1.4, ry=a)  # fmt: skip
        return
    bob = 0.08 * math.sin(t * 0.9)
    swell = 1.0 + 0.05 * breath
    with r.at(0, heart_y + bob, 0, ry=t * 0.45, s=swell):  # the heart: a faceted crystal, breathing
        r.part("lozenge", 0, 0, 0, 0.62, 1.25, 0.62, _dim(CORE_TEAL, 0.75 + 0.3 * breath), glow=True)
        r.part("lozenge", 0, 0, 0, 0.5, 1.05, 0.5, _dim(CORE_TEAL, 0.95), glow=True, ry=math.pi / 4)
        r.part("lozenge", 0, 0, 0, 0.3, 0.85, 0.3, CORE_HEART, glow=True)  # its white heart
    r.part("sphere", 0, heart_y + bob, 0, 1.5 * swell, 1.9 * swell, 1.5 * swell,
           _dim(CORE_TEAL, 0.45 + 0.2 * breath), tex="ward_net", glow=True)  # its halo  # fmt: skip
    for i in range(6):  # stone shards orbiting it, a teal vein lit in each
        a = t * 0.5 + i * math.tau / 6
        y = heart_y + 0.35 * math.sin(t * 0.7 + i * 1.9)
        with r.at(math.cos(a) * 1.1, y, -math.sin(a) * 1.1, ry=a + t, rz=0.4 * i):
            r.part("lozenge", 0, 0, 0, 0.16, 0.36, 0.16, MASONRY_DARK, tex="rough_stone")
            r.part("cube", 0.07, 0, 0, 0.02, 0.24, 0.03, CORE_TEAL, glow=True)
    for i in range(4):  # motes rising off it, teal-white
        u = (t * 0.3 + i / 4) % 1.0
        a = i * 1.7 + t * 0.4
        r.part("cube", math.cos(a) * 0.5, heart_y - 0.6 + u * 2.2, math.sin(a) * 0.5, 0.05, 0.05, 0.05,
               CORE_HEART, glow=True)  # fmt: skip
    ring = (t * 0.4) % 1.0  # a ring of teal pulsing out over the floor
    d = 2.0 + 3.0 * ring
    r.part(
        "quad", 0, 0.08, 0, d, 1, d, _mix_rgb(CORE_HEART, _dim(CORE_TEAL, 0.5), ring), tex="ripple", glow=True
    )
    with r.at(0, 0, 0, ry=yaw):  # the tethers, in world axes
        for i, (dx, dy, dz) in enumerate(tethers):
            a, b = (0.0, heart_y, 0.0), (dx, dy + TETHER_Y, dz)
            _bar(r, a, b, 0.035, _dim(CORE_TEAL, 0.7 + 0.3 * breath), glow=True)
            u = (t * 0.7 + i * 0.37) % 1.0  # a bead of light running out along it
            r.part("cube", a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u,
                   0.1, 0.1, 0.1, CORE_HEART, glow=True)  # fmt: skip
    if shielded:  # the ward's dome of light over it
        r.part("sphere", 0, 0.4, 0, 3.4, (top + 2.2) * 2, 3.4, _dim(CORE_TEAL, 0.55 + 0.15 * breath),
               tex="ward_net", glow=True, ry=t * 0.15)  # fmt: skip
        r.part("cyl", 0, 0.04, 0, 3.5, 0.06, 3.5, _dim(CORE_TEAL, 0.8), tex="ripple", glow=True)


WATER_SHEET = (150, 178, 196)
WATER_DEEP = (84, 112, 132)
FOAM = (226, 236, 240)
SPRAY = (196, 214, 224)


def waterfall(r, t, top=12.0, width=3.0, foot=0.0):
    """Water pouring off a broken lip `top` metres up down to `foot` (below 0 it plunges on past the
    floor into the chasm's haze): a pale sheet as wide as `width` with a darker heart, ribs of foam
    sliding down it ever faster, a lip of white where it spills over, and at the foot a churned pool
    with spray and mist rising off it (over the chasm, with `foot` below 0, it only plunges on). Its
    sheet runs along X, thin along Z, so it faces +Z and -Z alike."""
    drop = top - foot
    mid = (top + foot) / 2
    r.part("cube", 0, top + 0.15, 0, width * 1.1, 0.3, 1.2, MASONRY_DARK)  # the broken lip it spills from
    r.part("cube", 0, top - 0.05, 0.1, width * 1.05, 0.2, 0.7, FOAM, glow=True)  # white where it pours over
    r.part("cube", 0, mid, 0, width, drop, 0.35, WATER_SHEET, tex="rapids", glow=True)
    # its darker heart
    r.part("cube", 0, mid, 0.02, width * 0.55, drop, 0.3, WATER_DEEP, tex="rapids", glow=True)
    for i in range(6):  # ribs of foam, sliding down and quickening as they fall
        u = (t * 0.55 + i / 6) % 1.0
        y = top - drop * u * u
        w = width * (0.6 + 0.35 * ((i * 5) % 3) / 2)
        r.part(
            "cube", (i % 3 - 1) * width * 0.15, y, 0.12, w, 0.15 + 0.6 * u, 0.08, _dim(FOAM, 0.8), glow=True
        )
    for i in range(4):  # threads of white down its face
        x = ((i + 0.5) / 4 - 0.5) * width * 0.8
        r.part("cube", x, mid, 0.19, 0.08, drop * 0.95, 0.04, _dim(FOAM, 0.85 + 0.1 * math.sin(t * 2 + i)))
    if foot >= -0.5:  # it lands: a churned pool, spray thrown up, mist rising
        r.part("cyl", 0, foot + 0.06, 0.6, width * 1.4, 0.12, 2.2, (120, 150, 166), tex="mist", glow=True)
        r.part("cyl", 0, foot + 0.1, 0.4, width * 0.9, 0.08, 1.2, FOAM, glow=True)
        for i in range(8):
            u = (t * 1.3 + i / 8) % 1.0
            a = i * 2.1
            r.part("cube", math.cos(a) * width * 0.5, foot + 0.2 + u * 1.6, 0.5 + math.sin(a) * 0.9,
                   0.12, 0.12, 0.12, SPRAY, glow=True)  # fmt: skip
        for i in range(3):  # mist rising off its foot
            u = (t * 0.25 + i / 3) % 1.0
            r.part("cube", (i - 1) * width * 0.3, foot + 0.6 + u * 3.0, 0.5, width * (0.7 + u * 0.6),
                   1.2 + u, 1.6 + u, _dim(SPRAY, 1.0 - 0.5 * u), tex="mist", glow=True)  # fmt: skip


def sunken_tower(r, seed, height=18.0):
    """One of the drowned city's towers, rising out of the chasm: a square shaft of warm sandstone in
    tiers, each set back from the one below and girt by a cornice, arched openings dark on each face,
    a broken crown, as if the top had been sheared away when the city sank."""
    w = 3.2 + (seed % 3) * 0.3
    tiers = 3
    y = 0.0
    for i in range(tiers):
        h = height / tiers
        ww = w * (1 - 0.12 * i)
        r.part("cube", 0, y + h / 2, 0, ww, h, ww, _dim(TOWER_LIT, 0.9 + 0.05 * i), tex="sunken_brick")
        r.part(
            "cube", 0, y + h, 0, ww + 0.4, 0.3, ww + 0.4, _dim(TOWER_LIT, 0.8), tex="sunken_brick"
        )  # cornice
        for face in range(4):  # an arched opening (or two) on each face
            a = face * math.pi / 2
            c, s = math.cos(a), math.sin(a)
            for j in (-1, 1) if i < 2 else (0,):
                off = j * ww * 0.22
                x, z = c * ww / 2 - s * off, s * ww / 2 + c * off
                r.part("cube", x, y + h * 0.5, z, 0.08, h * 0.45, 0.55, PASSAGE_DARK, ry=-a)
                r.part(
                    "cyl", x, y + h * 0.5 + h * 0.225, z, 0.6, 0.1, 0.6, PASSAGE_DARK, ry=-a, rx=math.pi / 2
                )
            for j in (-1, 1):  # a column at each side of the face
                x, z = c * (ww / 2 + 0.1) - s * j * ww * 0.45, s * (ww / 2 + 0.1) + c * j * ww * 0.45
                r.part("cyl", x, y + h * 0.5, z, 0.3, h * 0.9, 0.3, (156, 140, 116), tex="rough_stone")
        y += h
    top = w * (1 - 0.12 * (tiers - 1))
    for i in range(5):  # the broken crown: stumps of wall, ragged and uneven
        a = i * math.tau / 5 + seed
        h = 0.6 + ((seed + i * 3) % 4) * 0.5
        r.part("cube", math.cos(a) * top * 0.4, y + h / 2, math.sin(a) * top * 0.4, 0.7, h, 0.7, TOWER_LIT,
               tex="sunken_brick", ry=a)  # fmt: skip


CRACK_CORE = (22, 18, 16)  # the black of a fissure's depth
CRACK_LIP = (52, 44, 38)  # the shadowed stone either side of it
CRACK_SEEP = _dim(CORE_TEAL, 0.2)  # the mortar-light seeping faintly up its depth, in a few
CRACK_OUT = (0.06, 0.1, 0.13)  # how far off the wall its lip, core and seep lie: so no depth fight shows


def _crack_path(rng, y, z, height, reach, step, lean, wobble):
    """[(y, z)] of a fissure climbing from (y, z) to `height`, jagged by `wobble`, kept within `reach`."""
    pts = [(y, z)]
    while y < height - 1e-6:
        a = lean + rng.uniform(-wobble, wobble)  # from straight up, toward +z
        d = min(step * rng.uniform(0.6, 1.3), (height - y) / max(math.cos(a), 0.3))
        y, z = y + d * math.cos(a), max(-reach, min(reach, z + d * math.sin(a)))
        pts.append((min(y, height), z))
    return pts


def _crack_seg(r, a, b, width, out, rgb, glow=False):
    """One straight stretch of fissure from face point `a` to `b` ((y, z) each), a quad lying on the
    wall (`wall_crack` draws in a frame turned so a quad's face looks out of it)."""
    (y0, z0), (y1, z1) = a, b
    dy, dz = y1 - y0, z1 - z0
    length = math.hypot(dy, dz)
    if length < 1e-3:
        return
    # the frame's local x runs down the wall and local z along it; its local y is out of the wall
    r.part("quad", -(y0 + y1) / 2, out, (z0 + z1) / 2, length + width, 1, width, rgb,
           ry=math.atan2(-dz, -dy), glow=glow)  # fmt: skip


def wall_crack(r, seed, height, reach=2.0, seep=False):
    """A great crack split down a cavern wall, its foot at the origin and the wall's face the local
    YZ plane (+X out of it): a long jagged fissure climbing `height` metres, wandering no farther than
    `reach` to either side, widest in its middle and closing to a hair at its ends, with offshoots
    forking off it and a few of those forking again. Each stretch is a black core over a wider lip of
    shadowed stone, laid a hair off the wall. In a few (`seep`), the mortar-light that runs in the old
    city's stone seeps faintly teal through the middle of the trunk; most are dark."""
    rng = random.Random(seed)  # the same crack is always split the same way
    lip_out, core_out, seep_out = CRACK_OUT
    big = min(1.0, height / 20)
    width = 0.2 + 0.16 * big  # at its widest
    step = 1.0 + 0.8 * big
    trunk = _crack_path(rng, 0.0, rng.uniform(-0.3, 0.3) * reach, height, reach * 0.8, step,
                        rng.uniform(-0.15, 0.15), 0.55)  # fmt: skip
    with r.at(rz=-math.pi / 2):
        n = len(trunk) - 1
        for i in range(n):
            k = (i + 0.5) / n
            w = width * (0.25 + 0.75 * math.sin(math.pi * k) ** 0.6)  # closing toward both ends
            _crack_seg(r, trunk[i], trunk[i + 1], w * 2.2, lip_out, CRACK_LIP)
            _crack_seg(r, trunk[i], trunk[i + 1], w, core_out, CRACK_CORE)
            if seep and 0.2 < k < 0.8:  # a thread of light deep in the dark
                _crack_seg(r, trunk[i], trunk[i + 1], w * 0.35, seep_out, CRACK_SEEP, glow=True)
        for i in range(1, n - 1):  # the offshoots, forking off the trunk now and then
            if rng.random() > 0.42:
                continue
            k = i / n
            side = rng.choice((-1, 1))
            y, z = trunk[i]
            rise = rng.uniform(1.5, 4.5) * (0.6 + big)
            if rng.random() < 0.35 and y > rise:  # a few run down from the trunk instead
                shoot = [(-py, pz) for py, pz in _crack_path(
                    rng, -y, z, -y + rise, reach, step * 0.6, side * rng.uniform(0.6, 1.1), 0.4)]  # fmt: skip
            else:
                shoot = _crack_path(rng, y, z, min(height, y + rise), reach, step * 0.6,
                                    side * rng.uniform(0.6, 1.1), 0.4)  # fmt: skip
            bw = width * 0.45 * (0.4 + 0.6 * math.sin(math.pi * k))
            for j in range(len(shoot) - 1):
                w = bw * (1 - j / len(shoot))
                _crack_seg(r, shoot[j], shoot[j + 1], w * 2, lip_out, CRACK_LIP)
                _crack_seg(r, shoot[j], shoot[j + 1], w, core_out, CRACK_CORE)
                if j == 0 and len(shoot) > 2 and rng.random() < 0.5:  # a hairline forking off it again
                    y2, z2 = shoot[1]
                    hair = _crack_path(rng, y2, z2, min(height, y2 + rng.uniform(0.8, 2.0)), reach, step * 0.4,
                                       -side * rng.uniform(0.3, 0.8), 0.3)  # fmt: skip
                    for m in range(len(hair) - 1):
                        _crack_seg(r, hair[m], hair[m + 1], w * 0.5, core_out, CRACK_CORE)


BREACH_HALF = 0.82  # half the width of the passage through the hole in the wall
BREACH_TOP = 2.9  # the height of its dark roof
BREACH_DEPTH = 0.8  # how far the brick round the hole stands out of the wall, the passage running through it
BREACH_BRICK = (100, 74, 62)  # the sewers' brick round the hole
WALL_FACE = -1.0  # a gate model's tile stands against its wall, whose face is here (local -X)
BREACH_FRONT = WALL_FACE + BREACH_DEPTH  # the face of the brick, where the passage opens


def _breach_opening(r):
    """A ragged hole knocked through the wall at the tile's -X face, built like the road gate's tunnel:
    a passage running back into the wall, black at its end, its sides and its roof, walled in by a
    thick lining of sewer brick that stands out of the wall, so it reads as a way on from any angle and
    shows no black past its edges. Round the mouth the broken courses step in toward a crown of bricks
    fallen in over it, a few of them jutting."""
    mid = (WALL_FACE + BREACH_FRONT) / 2
    r.part("cube", WALL_FACE + 0.02, BREACH_TOP / 2, 0, 0.04, BREACH_TOP, 2 * BREACH_HALF, PASSAGE_DARK)
    for side in (-1, 1):
        r.part("cube", mid, BREACH_TOP / 2, side * BREACH_HALF, BREACH_DEPTH, BREACH_TOP, 0.04, PASSAGE_DARK)
    r.part("cube", mid, BREACH_TOP, 0, BREACH_DEPTH, 0.04, 2 * BREACH_HALF, PASSAGE_DARK)
    # The lining, carried from the wall out to the mouth, so the passage is walled in brick on its
    # flanks and over its roof; its outer edge ragged course by course.
    for side in (-1, 1):
        for k in range(7):
            y = 0.22 + k * 0.44
            w = 0.34 + 0.1 * ((k * 2 + (side > 0)) % 3)
            d = BREACH_DEPTH - 0.08 * ((k + (side > 0)) % 2)
            r.part("cube", WALL_FACE + d / 2, y, side * (BREACH_HALF + 0.02 + w / 2), d, 0.44, w,
                   _dim(BREACH_BRICK, 0.92 + 0.06 * (k % 3)), tex="sewer_brick")  # fmt: skip
    for k in range(4):  # over the roof, stepped back as they rise
        h = 0.3 + 0.1 * (k % 2)
        r.part("cube", WALL_FACE + (BREACH_DEPTH - 0.12 * k) / 2, BREACH_TOP + 0.2 + 0.32 * k, 0,
               BREACH_DEPTH - 0.12 * k, h, 2 * BREACH_HALF + 0.8 - 0.35 * k, _dim(BREACH_BRICK, 0.9 + 0.05 * k),
               tex="sewer_brick")  # fmt: skip
    for side in (-1, 1):  # the broken edge at the mouth, its courses stepping in toward the crown
        for k in range(7):
            y = 0.22 + k * 0.44
            inward = 0.05 * k + 0.05 * ((k * 5 + (side > 0)) % 3)
            z = side * (BREACH_HALF + 0.1 - inward)
            jut = 0.12 + 0.08 * ((k * 3 + (side > 0)) % 3)
            r.part("cube", BREACH_FRONT - 0.12 + jut / 2, y, z, 0.24 + jut, 0.4, 0.3 + 0.08 * (k % 2),
                   _dim(BREACH_BRICK, 0.95 + 0.06 * (k % 3)), tex="sewer_brick", ry=0.12 * side * (k % 2))  # fmt: skip
    for k in range(5):  # the broken crown, lumps of brick fallen in over the mouth
        z = -0.64 + k * 0.32
        y = BREACH_TOP - 0.08 + 0.16 * ((k * 2) % 3) - 0.14 * (k == 2)
        r.part("cube", BREACH_FRONT - 0.04, y, z, 0.36, 0.42, 0.4, _dim(BREACH_BRICK, 0.8 + 0.07 * (k % 2)),
               tex="sewer_brick", rx=0.2 * (k - 2))  # fmt: skip


def cistern_breach(r, t):
    """The way down out of the Pall's cistern, set in the wall behind its tile (-X) and facing +X: a
    ragged hole where the cistern's wall gave way onto an older city beneath (`_breach_opening`), a
    worn sandstone lip where its floor falls away into the dark, the brick it burst spilled out over the
    floor and dust still sifting from its broken crown."""
    _breach_opening(r)
    lip = BREACH_FRONT - 0.3  # past this the floor drops away down a stair no light reaches
    r.part("cube", (WALL_FACE + lip) / 2, 0.012, 0, lip - WALL_FACE, 0.02, 2 * BREACH_HALF, PASSAGE_DARK)
    r.part(
        "cube", lip + 0.06, 0.03, 0, 0.12, 0.06, 2 * BREACH_HALF - 0.1, _dim(MASONRY, 0.7), tex="rough_stone"
    )
    for i in range(9):  # the rubble, fanned out over the floor from the hole
        a = (i - 4) * 0.33
        d = 0.3 + 0.45 * ((i * 5) % 3)
        size = 0.34 - 0.06 * ((i * 5) % 3)
        r.part("cube", BREACH_FRONT + 0.1 + d * math.cos(a), size * 0.4, 1.1 * d * math.sin(a), size,
               size * 0.8, size * 0.9, _dim(BREACH_BRICK, 0.85 + 0.05 * (i % 3)), tex="sewer_brick",
               ry=i * 1.3)  # fmt: skip
    for i in range(3):  # dust sifting down from the broken crown
        u = (t * 0.4 + i / 3) % 1.0
        r.part("cube", BREACH_FRONT + 0.25, BREACH_TOP - 0.2 - 2.6 * u, -0.5 + 0.5 * i, 0.03, 0.06, 0.03,
               (170, 150, 120))  # fmt: skip


def sunken_stair(r, t):
    """The way back up to the sewers from the old city, set in the cavern wall behind its tile (-X): the
    same ragged hole (`_breach_opening`), seen from below, a stair of sewer brick climbing out of it and
    on up into the dark, each step dimmer than the last, rubble at its foot and drips falling from its
    crown."""
    _breach_opening(r)
    for k in range(4):  # the stair, climbing back into the passage and fading as it goes
        h = 0.2 * (k + 1)
        r.part("cube", BREACH_FRONT + 0.25 - 0.27 * k, h / 2, 0, 0.28, h, 2 * BREACH_HALF - 0.04,
               _dim(BREACH_BRICK, 1.1 - 0.3 * k), tex="sewer_brick")  # fmt: skip
    for i in range(6):
        a = i * 2.3
        r.part("cube", BREACH_FRONT + 0.7 + 0.35 * math.cos(a), 0.1, 0.7 * math.sin(a), 0.28, 0.18, 0.24,
               MASONRY_DARK, ry=a)  # fmt: skip
    for i in range(3):  # drips off the crown
        u = (t * 0.7 + i / 3) % 1.0
        r.part("cube", BREACH_FRONT + 0.25, BREACH_TOP - 0.3 - 2.6 * u, -0.4 + 0.4 * i, 0.02, 0.06, 0.02,
               (150, 180, 150))  # fmt: skip


def _keystone_arch(r, style, t, lit):
    """A keystone of the old city's sandstone set over the lintel, carved with a giant's shoulders
    bearing up a slab; the teal mortar-light burns in the cracks round it while the Keystone lives."""
    for face in (-1, 1):
        with r.at(face * 0.25, 3.45, 0):
            r.part("wedge", 0, 0, 0, 0.12, 0.5, 0.6, MASONRY, tex="rough_stone", rx=math.pi)
            r.part("cube", 0, 0.32, 0, 0.12, 0.12, 1.2, MASONRY_DARK)  # the slab it bears up
            for z in (-0.38, 0.38):
                r.part(
                    "cube",
                    face * 0.02,
                    -0.1,
                    z,
                    0.04,
                    0.26,
                    0.04,
                    CORE_TEAL if lit else COLD,
                    glow=lit,
                    rx=0.3 * z,
                )


def _keystone_leaf(r, style, side, face, t, lit):
    """Leaves of old, sun-bleached timber, the water line still dark across them."""
    r.part("cube", face * 0.085, 0.9, 0, 0.02, 0.08, 0.92, (60, 54, 44))  # the water line
    r.part("cube", face * 0.1, 1.5, -side * 0.25, 0.03, 0.16, 0.16, style.iron, rx=math.pi / 4)  # the ring


SLAB = (156, 140, 116)  # a stone door's pale, water-worn sandstone
SLAB_SHADOW = (112, 98, 80)  # its carved-back panels


def stone_door(r, open_t, frame):
    """Old Harrowmere's plain door (`door model=stone`): one carved sandstone slab, a raised border
    and two sunk panels on each face round a medallion where a small teal glyph of the mortar-light
    still glows, sinking into the floor as it opens, in a heavy frame of the city's brick (jambs on
    plinths, a lintel and a keystone, its masonry filling up to `frame`, the passage's ceiling)."""
    frame = max(frame, 3.1)
    for z in (-0.9, 0.9):  # the jambs and their plinths
        r.part("cube", 0, frame / 2, z, 0.56, frame, 0.3, MASONRY, tex="sunken_brick")
        r.part("cube", 0, 0.22, z, 0.64, 0.44, 0.36, MASONRY_DARK, tex="rough_stone")
        r.part("cube", 0, 2.62, z, 0.62, 0.12, 0.36, MASONRY_DARK)  # the impost under the lintel
    r.part("cube", 0, 2.86, 0, 0.62, 0.36, 2.1, MASONRY, tex="rough_stone")  # the lintel
    r.part("wedge", 0, 2.96, 0, 0.68, 0.5, 0.44, MASONRY_DARK, tex="rough_stone", rx=math.pi)  # keystone
    if frame > 3.04:
        r.part("cube", 0, (3.04 + frame) / 2, 0, 0.5, frame - 3.04, 1.6, MASONRY, tex="sunken_brick")
    r.part("cube", 0, 0.02, 0, 0.66, 0.04, 1.6, MASONRY_DARK)  # the worn threshold
    with r.at(0, -open_t * 2.66, 0):  # the slab sinks into the floor
        r.part("cube", 0, 1.3, 0, 0.2, 2.6, 1.52, SLAB, tex="rough_stone")
        for side in (-1, 1):
            x = side * 0.1
            for y, h in ((0.1, 0.2), (2.52, 0.16), (1.3, 0.12)):  # the plinth band, the head, the waist
                r.part("cube", x, y, 0, 0.04, h, 1.52, SLAB, tex="rough_stone")
            for z in (-0.68, 0.68):  # the border stiles
                r.part("cube", x, 1.3, z, 0.04, 2.6, 0.16, SLAB, tex="rough_stone")
            for y in (0.72, 1.92):  # the two sunk panels, a fillet carved round each
                r.part("cube", x - side * 0.008, y, 0, 0.02, 0.88, 1.1, SLAB_SHADOW, tex="rough_stone")
                r.part("cube", x, y, 0, 0.028, 0.06, 0.96, MASONRY_DARK)
            # the medallion on the waist, and the glyph glowing in its sunk face
            r.part("cyl", x + side * 0.02, 1.3, 0, 0.44, 0.04, 0.44, SLAB, rz=math.pi / 2)
            r.part("cyl", x + side * 0.042, 1.3, 0, 0.34, 0.01, 0.34, MORTAR, rz=math.pi / 2)
            gx = x + side * 0.05
            glyph = _dim(CORE_TEAL, 0.75)
            r.part("cube", gx, 1.3, 0, 0.01, 0.24, 0.03, glyph, glow=True)  # the stem
            for dz in (-0.06, 0.06):  # two strokes rising from it like a bearer's arms
                r.part("cube", gx, 1.33, dz, 0.01, 0.12, 0.025, glyph, glow=True, rx=dz * 9)
            r.part("cube", gx, 1.2, 0, 0.01, 0.025, 0.14, glyph, glow=True)  # the ground it stands on


# --- the rune lift (Old Harrowmere's lift, `lift model=rune`) -----------------------------------
#
# The masons raised their lift with the same mortar-light that walks their golems: no chains and no
# pulley, only a carved stone deck with a glyph circle let into it, a ring of glyphs turning under its
# keel and another hovering over it as a crown, tied to the deck's corners by threads of light. Its
# plates are rune plates: discs of stone whose glyphs flare as they sink under your weight.

RUNE_IDLE = 0.45  # how brightly the glyphs burn while the lift rests
RUNE_CROWN = 2.5  # the crown ring's height over the deck, lowered under a low ceiling
RUNE_KEEL = 0.36  # how far under the deck's top the keel ring turns
RUNE_SEGMENTS = 10  # glyph segments round each ring
RUNE_STONE = (236, 224, 204)  # a pale tint, so the city's flagstone and brick textures show their own colour


def rune_glow(moving, locked, pressed=0.0):
    """How brightly (0..1) a rune lift's glyphs burn: cold (0) while it is still fastened and at rest,
    dim while it waits, full while it rides; stepping on a plate (`pressed`, 0..1) wakes it too."""
    rest = 0.0 if locked else RUNE_IDLE
    return max(1.0 if moving else rest, min(max(pressed, 0.0), 1.0))


def _rune_rgb(k, heart=False):
    """The glyphs' colour at glow `k`: COLD stone at 0, the teal mortar-light (or its heart) at 1."""
    return _mix_rgb(COLD, CORE_HEART if heart else CORE_TEAL, k)


def _glyph_ring(r, y, radius, turn, k, thick=0.05):
    """A ring of glyph segments, every other one notched with a rune, turned `turn` radians."""
    rgb, lit = _rune_rgb(k), k > 0
    seg = radius * math.tau / RUNE_SEGMENTS * 0.8
    for i in range(RUNE_SEGMENTS):
        a = turn + i * math.tau / RUNE_SEGMENTS
        x, z = math.cos(a) * radius, math.sin(a) * radius
        r.part("cube", x, y, z, thick, thick, seg, rgb, glow=lit, ry=-a)
        if i % 2 == 0:  # a rune hung off the ring
            r.part("cube", x, y - thick * 1.6, z, thick * 0.7, thick * 2.4, thick * 0.7, rgb, glow=lit, ry=-a)


def rune_lift(r, t, moving, chain_h, pressed=0.0, locked=False):
    """Old Harrowmere's lift: a deck of carved sandstone with a glyph circle let into it, a ring of
    glyphs turning under it and a crown of glyphs hovering over it, tied to its corner stones by
    threads of light. The glyphs lie cold while it is fastened, wake dim, and blaze as it rides. In the
    middle is its rune plate, sunk `pressed` metres (and flaring) while someone stands on it."""
    k = rune_glow(moving, locked)
    pulse = 0.9 + 0.1 * math.sin(t * 6) if moving else 1.0
    rgb, lit = _rune_rgb(k * pulse), k > 0
    r.part("cube", 0, -0.12, 0, 1.92, 0.22, 1.92, RUNE_STONE, tex="ochre_flag")  # the deck
    r.part("cube", 0, -0.32, 0, 1.6, 0.2, 1.6, _dim(RUNE_STONE, 0.8), tex="sunken_brick")  # its carved keel
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # the kerb round its edge, cut with runes
        r.part(
            "cube", sx * 0.9, 0.0, sz * 0.9, 0.12 if sx else 1.92, 0.06, 0.12 if sz else 1.92, MASONRY_DARK
        )
        for u in (-0.45, 0.45):
            r.part("cube", sx * 0.9 or u, 0.035, sz * 0.9 or u, 0.05, 0.02, 0.05, rgb, glow=lit, ry=0.785)
    for i in range(16):  # the glyph circle let into the deck
        a = i * math.tau / 16
        r.part("cube", math.cos(a) * 0.74, 0.0, math.sin(a) * 0.74, 0.035, 0.012, 0.25, rgb, glow=lit, ry=-a)
    crown = max(min(RUNE_CROWN, chain_h - 0.5), 1.9)
    for cx, cz in ((0.84, 0.84), (0.84, -0.84), (-0.84, 0.84), (-0.84, -0.84)):  # the corner stones
        r.part("cube", cx, 0.1, cz, 0.18, 0.2, 0.18, RUNE_STONE, tex="sunken_brick")
        r.part("cube", cx, 0.22, cz, 0.08, 0.06, 0.08, rgb, glow=lit, ry=0.785)  # a glyph-stone on each
        if lit:  # a thread of light up to the crown
            r.part("cube", cx, (0.25 + crown) / 2, cz, 0.018, crown - 0.25, 0.018,
                   _dim(rgb, 0.6), glow=True)  # fmt: skip
    _glyph_ring(r, crown, 0.8, t * 0.35, k * pulse)  # the crown
    _glyph_ring(r, -RUNE_KEEL, 0.9, -t * 0.5, k * pulse, thick=0.06)  # the keel ring
    _rune_plate(r, k, min(pressed / PLATE_SINK, 1.0) if pressed > 0 else 0.0, pressed)


def _rune_plate(r, k, press, sink):
    """The deck's rune plate: a disc of dressed stone in a dark collar, a four-armed rune cut in it that
    flares as the plate sinks under your weight."""
    glow = max(k, press)
    rgb, heart, lit = _rune_rgb(glow), _rune_rgb(glow, heart=True), glow > 0
    y = 0.035 - sink
    r.part("cyl", 0, 0.02, 0, 1.12, 0.05, 1.12, MASONRY_DARK)  # the collar it sinks into
    r.part("cyl", 0, y, 0, 0.98, 0.05, 0.98, RUNE_STONE, tex="ochre_flag")
    for i in range(4):  # the rune's arms
        a = i * math.pi / 2 + math.pi / 4
        r.part(
            "cube", math.cos(a) * 0.22, y + 0.03, math.sin(a) * 0.22, 0.05, 0.012, 0.24, rgb, glow=lit, ry=-a
        )
    r.part("cyl", 0, y + 0.03, 0, 0.16, 0.014, 0.16, heart, glow=lit)  # its eye


def rune_call_plate(r, sink=0.0, cold=False):
    """A landing's rune plate, set flush in the floor just out from the shaft: a disc of stone in a
    collar ringed with glyphs, that sinks `sink` metres under your weight and flares as it goes. On
    the far landing of a lift still fastened (`cold`) its glyphs lie dark."""
    k = 0.0 if cold else (1.0 if sink > 0 else RUNE_IDLE)
    if cold and sink > 0:
        k = 0.15  # a flicker, and no more: it will not come
    rgb, lit = _rune_rgb(k), k > 0
    r.part("cyl", 0, 0.012, 0, CALL_PLATE_R * 2 + 0.16, 0.025, CALL_PLATE_R * 2 + 0.16, MASONRY_DARK)
    for i in range(8):  # the glyphs round its collar
        a = i * math.tau / 8
        x, z = math.cos(a) * (CALL_PLATE_R + 0.02), math.sin(a) * (CALL_PLATE_R + 0.02)
        r.part("cube", x, 0.027, z, 0.03, 0.01, 0.1 if i % 2 else 0.06, rgb, glow=lit, ry=-a)
    y = 0.01 - min(sink, PLATE_SINK)
    r.part(
        "cyl", 0, y, 0, CALL_PLATE_R * 2 - 0.06, 0.03, CALL_PLATE_R * 2 - 0.06, RUNE_STONE, tex="ochre_flag"
    )
    r.part("cube", 0, y + 0.017, 0, 0.3, 0.008, 0.04, rgb, glow=lit)  # the rune cut in the disc
    r.part("cube", 0, y + 0.017, 0, 0.04, 0.008, 0.3, rgb, glow=lit)


# --- the Keystone's great gate ---------------------------------------------------------------------

GATE_TOP = 6.4  # the opening's height under its lintel (`models.GREAT_DOOR_TOP`, which the fog fills)
GATE_LINTEL = 0.8  # the lintel's depth over the opening
GATE_STONE = (230, 224, 214)  # a pale tint, so the sunken brick shows its own warm colour, as walls do
GATE_LEAF = (150, 136, 112)  # the leaves' great slabs of old sandstone, a shade greyer than the arch
GATE_IRON = (64, 58, 52)
GATE_PIER = 1.1  # the width (across) of each buttress flanking the facade
GATE_REACH = 2.3  # how far its foot and capital stand out from the facade, the giant before it between
GATE_ARCH_SPRING = GATE_TOP + GATE_LINTEL  # where the facade's arch springs from the buttresses
GATE_ARCH_R = 1.0  # its inner radius: the porch's half-width
GATE_ARCH_DEEP = 0.85  # how far its voussoirs run, inner curve to outer
GATE_VOUSSOIRS = 7
GATE_CROWN = 1.8  # the height of the pediment set over the facade, above the walls either side


def great_keystone_gate(r, style, swing, t, lit, great):
    """The Keystone's great gate, twice a boss door's height: two leaves of carved sandstone slabs
    (a seam of the mortar-light down their meeting edges) between deep jambs, its lintel's masonry
    built up to the walls either side (`great.rise`), and out past its porch (`great.porch`) a facade
    on the side it faces (`great.front`): two buttresses rising from below, each crowned with a
    kneeling stone giant bearing up the arch on its raised hands, a round arch of voussoirs over the
    porch and in the tympanum under it a carved keystone with the teal core burning in its heart,
    cracks of the light running out from it, braziers of the light on the buttresses, a pediment over
    it all. On the arena's side, plain pilasters and a lintel band. The teal burns while the Keystone
    lives. `swing` is how far the leaves have swung inward; None leaves them out (the fog's frame)."""
    f = great.front
    lintel_top = GATE_TOP + GATE_LINTEL
    top = max(great.rise or lintel_top, lintel_top)
    face = 1.0 + great.porch  # the facade's plane
    teal = CORE_TEAL if lit else COLD
    _gate_masonry(r, f, lintel_top, top, face)
    _gate_inner(r, f, teal, lit)
    with r.at(f * face, 0, 0):
        _gate_facade(r, f, t, teal, lit, top)
    if swing is not None:
        for side in (-1, 1):
            with r.at(0, 0, side * 0.88, ry=side * swing * f), r.at(0, 0, -side * 0.44):
                _gate_leaf(r, side, teal, lit)


def _gate_masonry(r, f, lintel_top, top, face):
    """The jambs and lintel in the gate's own tile, the masonry over it up to the walls, and the porch's
    ceiling out to the facade, so no sky shows round the arch."""
    for side in (-1, 1):
        r.part("cube", 0, GATE_TOP / 2, side * 1.0, 1.0, GATE_TOP, 0.24, GATE_STONE, tex="sunken_brick")
        r.part("cube", 0, 0.3, side * 0.98, 1.2, 0.6, 0.34, MASONRY_DARK, tex="rough_stone")  # plinth
    r.part("cube", 0, GATE_TOP + GATE_LINTEL / 2, 0, 1.4, GATE_LINTEL, 2.1, MASONRY, tex="rough_stone")
    y = lintel_top
    while y < top - 1e-3:  # in 2 m courses, so the brick repeats as the walls' does
        seg = min(2.0, top - y)
        r.part("cube", 0, y + seg / 2, 0, 2.0, seg, 2.0, GATE_STONE, tex="sunken_brick")
        y += seg
    if face > 1.0:  # the porch's ceiling, a slab spanning it at the lintel's top
        depth = face - 1.0
        r.part("cube", f * (1.0 + depth / 2), lintel_top - 0.25, 0, depth, 0.5, 2.0, MASONRY_DARK,
               tex="rough_stone")  # fmt: skip


def _gate_inner(r, f, teal, lit):
    """On the arena's side: two flat pilasters, a lintel band across them, a small keystone, lit."""
    x = -f * 1.06
    for side in (-1, 1):
        r.part("cube", x, 3.8, side * 1.3, 0.14, 7.6, 0.6, MASONRY, tex="rough_stone")
    r.part("cube", x, GATE_TOP + 0.45, 0, 0.16, 0.9, 3.2, MASONRY_DARK, tex="rough_stone")
    r.part("wedge", x - f * 0.06, GATE_TOP + 0.5, 0, 0.16, 0.7, 0.6, MASONRY, tex="rough_stone", rx=math.pi)
    r.part("lozenge", x - f * 0.12, GATE_TOP + 0.45, 0, 0.06, 0.3, 0.2, teal, glow=lit)


def _gate_facade(r, f, t, teal, lit, top):
    """The facade, its plane at local x 0 and standing out toward +x * f: a buttress either side of
    the porch, a giant standing before each bearing up its capital, braziers in the porch's mouth."""
    pier_z = 1.0 + GATE_PIER / 2
    for side in (-1, 1):
        z = side * pier_z
        # the buttress: a broad foot rising out of the dark below, the shaft, a capital jutting over the giant
        r.part("cube", f * GATE_REACH / 2, -9.0, z, GATE_REACH, 18.0, GATE_PIER + 0.3, MASONRY_DARK,
               tex="rough_stone")  # fmt: skip
        r.part("cube", f * 0.55, GATE_ARCH_SPRING / 2, z, 1.1, GATE_ARCH_SPRING, GATE_PIER, GATE_STONE,
               tex="sunken_brick")  # fmt: skip
        r.part("cube", f * GATE_REACH / 2, GATE_ARCH_SPRING - 0.3, z, GATE_REACH, 0.6, GATE_PIER + 0.2,
               MASONRY, tex="rough_stone")  # fmt: skip
        with r.at(f * 1.65, 0, z):
            _gate_atlas(r, f, side, teal, lit)
        with r.at(f * 0.25, 3.4, side * 0.86):  # a brazier of the mortar-light in the porch's mouth
            r.part("cube", 0, -0.22, side * 0.08, 0.08, 0.08, 0.2, GATE_IRON)  # its bracket
            r.part("cone", 0, 0, 0, 0.3, 0.2, 0.3, GATE_IRON, rx=math.pi)
            if lit:
                flick = 1 + 0.12 * math.sin(t * 7 + side)
                r.part("cone", 0, 0.22, 0, 0.2, 0.42 * flick, 0.2, CORE_TEAL, glow=True)
    _gate_arch(r, f, teal, lit, top)


def _gate_atlas(r, f, side, teal, lit):
    """A giant of the old city's stone standing before the buttress, its head bowed under the capital
    and both hands raised flat against it, bearing it up; the mortar-light in its eyes and chest."""
    stone, dark = COLUMN_STONE, _dim(COLUMN_STONE, 0.78)
    for leg in (-1, 1):
        r.part("cube", 0, 1.3, leg * 0.34, 0.6, 2.6, 0.5, dark)
        r.part("cube", 0.12 * f, 0.15, leg * 0.34, 0.85, 0.3, 0.6, dark)  # its feet
    r.part("cube", 0, 2.8, 0, 0.75, 0.6, 1.1, stone)  # the hips
    r.part("cube", 0, 3.7, 0, 0.8, 1.3, 1.2, stone)  # the belly
    r.part("cube", 0, 4.6, 0, 0.9, 0.8, 1.6, stone)  # the chest, broad at the shoulders
    r.part("lozenge", f * 0.52, 4.2, 0, 0.08, 0.36, 0.24, teal, glow=lit)  # its core
    r.part("cube", f * 0.2, 5.15, 0, 0.55, 0.55, 0.5, stone)  # the head, bowed under the load
    for dz in (-0.13, 0.13):
        r.part("cube", f * 0.48, 5.12, dz, 0.03, 0.05, 0.09, teal, glow=lit)  # its eyes
    for arm in (-1, 1):  # the arms, up from the shoulders to the capital, palms flat under it
        r.part("cube", 0, 5.55, arm * 0.68, 0.4, 1.7, 0.4, stone, rx=arm * 0.22)
        r.part("cube", 0.05 * f, 6.5, arm * 0.82, 0.55, 0.2, 0.5, dark)  # the hands


def _gate_arch(r, f, teal, lit, top):
    """The tympanum and the round arch over the porch, the carved keystone, the masonry up to the
    walls' top and the pediment crowning it."""
    spring = GATE_ARCH_SPRING
    # the tympanum: the facade's wall over the porch, from the arch's spring to the top
    r.part("cube", f * 0.2, (spring + top) / 2, 0, 0.4, top - spring, 2.0, GATE_STONE, tex="sunken_brick")
    # its carving: a ring of dark stone round the teal core, the cracks of the light running from it
    core_y = spring + 0.5
    r.part("cyl", f * 0.42, core_y, 0, 0.9, 0.1, 0.9, MASONRY_DARK, rz=math.pi / 2)
    r.part("lozenge", f * 0.5, core_y, 0, 0.16, 0.5, 0.34, teal, glow=lit)
    r.part("lozenge", f * 0.54, core_y, 0, 0.1, 0.24, 0.16, CORE_HEART if lit else COLD, glow=lit)
    for a in (0.5, 1.2, 1.95, 2.65):
        r.part("cube", f * 0.45, core_y + 0.55 * math.sin(a), 0.55 * math.cos(a), 0.03, 0.04, 0.42, teal,
               rx=math.pi / 2 - a, glow=lit)  # fmt: skip
    # the voussoirs, alternating light and dark, round from spring to spring
    radius = GATE_ARCH_R + GATE_ARCH_DEEP / 2
    span = math.pi / GATE_VOUSSOIRS
    for i in range(GATE_VOUSSOIRS):
        a = span * (i + 0.5)
        if i == GATE_VOUSSOIRS // 2:
            continue  # the keystone's place
        rgb = MASONRY if i % 2 else MASONRY_DARK
        r.part("cube", f * 0.55, spring + radius * math.sin(a), radius * math.cos(a), 0.7, GATE_ARCH_DEEP,
               2 * radius * math.sin(span / 2) + 0.04, rgb, tex="rough_stone", rx=math.pi / 2 - a)  # fmt: skip
    # the keystone: a great carved block standing proud of the arch, the giant's slab borne on it
    key_y = spring + radius + 0.15
    r.part("cube", f * 0.7, key_y, 0, 1.0, GATE_ARCH_DEEP + 0.5, 0.75, MASONRY, tex="rough_stone")
    r.part("cube", f * 1.2, key_y + 0.12, 0, 0.06, 0.5, 0.36, MASONRY_DARK)  # its carved face
    r.part("lozenge", f * 1.24, key_y + 0.12, 0, 0.06, 0.32, 0.2, teal, glow=lit)
    # a frieze across the tympanum: carved panels between dark bands
    frieze = (key_y + 0.9 + top - 0.4) / 2
    if top - 0.4 - (key_y + 0.9) > 1.0:
        r.part("cube", f * 0.45, frieze, 0, 0.1, 1.0, 2.0, MASONRY_DARK, tex="rough_stone")
        for z in (-0.6, 0.0, 0.6):
            r.part("cube", f * 0.52, frieze, z, 0.08, 0.7, 0.44, MASONRY, tex="rough_stone")
    # a cornice at the walls' top, and the pediment over it
    r.part("cube", f * 0.5, top - 0.2, 0, 1.0, 0.4, 2 * (1.0 + GATE_PIER) + 0.4, MASONRY, tex="rough_stone")
    width = 2 * (1.0 + GATE_PIER)
    r.part("wedge", f * 0.4, top + GATE_CROWN / 2, 0, width, GATE_CROWN, 0.8, GATE_STONE, tex="sunken_brick",
           ry=math.pi / 2)  # fmt: skip
    r.part("cube", f * 0.6, top + 0.5, 0, 0.5, 0.6, 0.6, MASONRY_DARK, rx=math.pi / 4)  # its boss
    r.part("cube", f * 0.86, top + 0.5, 0, 0.04, 0.2, 0.2, teal, rx=math.pi / 4, glow=lit)


def _gate_leaf(r, side, teal, lit):
    """One leaf, its middle at the origin (the meeting edge toward -side): slabs of old sandstone
    stacked in courses, carved bands across both faces, a giant's shoulder in relief bearing up the
    top band, a seam of the light down its meeting edge and an iron ring to haul it by."""
    height = GATE_TOP - 0.1
    for i in range(3):  # three great slabs, one over the next
        r.part("cube", 0, height / 6 * (2 * i + 1), 0, 0.3, height / 3 - 0.04, 0.86, GATE_LEAF,
               tex="sunken_brick")  # fmt: skip
    for face in (-1, 1):
        x = face * 0.16
        for y in (0.4, height / 3, 2 * height / 3, height - 0.3):  # carved bands across it
            r.part("cube", x, y, 0, 0.04, 0.22, 0.86, MASONRY_DARK)
        relief = _dim(GATE_LEAF, 1.12)  # a giant carved in relief, its arm raised to the top band
        r.part("cube", x, height * 0.55, side * 0.08, 0.06, 1.6, 0.3, relief)
        r.part("sphere", x, height * 0.55 + 0.9, side * 0.12, 0.1, 0.36, 0.44, relief)  # its shoulder
        r.part("cube", x, height * 0.45, -side * 0.42, 0.04, 1.4, 0.03, teal, glow=lit)  # the seam
        r.part(
            "cube", x, height * 0.45, -side * 0.4, 0.05, 0.3, 0.3, teal, rx=math.pi / 4, glow=lit
        )  # the core
        r.part("cube", face * 0.2, 2.0, -side * 0.24, 0.06, 0.26, 0.26, GATE_IRON, rx=math.pi / 4)  # the ring


# --- the colossal pillars of the Keystone's court ------------------------------------------------

COLUMN_DRUM = 3.2  # metres of each drum the shaft is stacked of
COLUMN_R = 0.8  # the shaft's radius: it all but fills its tile
COLUMN_BAND_EVERY = 4  # a broad band of darker stone clasps every this many drums
COLUMN_FLUTES = 8
COLUMN_PALE = (196, 182, 156)  # its drums: pale, so they still read high up in the cavern's gloom


def colossal_pillar(r, seed, height):
    """A column of the old city's sandstone rising `height` from the floor into the cavern's vault
    (`pillar model=colossal`): a stepped plinth, a shaft of drums with mortar seams between them and
    every few a broad band clasping it, flutes running up it, cracks in it, one or two of its seams
    leaking the teal mortar-light, and a spreading head sunk into the rock."""
    r.part("cube", 0, 0.3, 0, 2.0, 0.6, 2.0, MASONRY_DARK, tex="rough_stone")  # the plinth, its steps
    r.part("cube", 0, 0.8, 0, 1.8, 0.4, 1.8, COLUMN_PALE, tex="rough_stone", ry=0.02 * (seed % 5))
    r.part("cyl", 0, 1.15, 0, 2 * COLUMN_R + 0.2, 0.3, 2 * COLUMN_R + 0.2, MASONRY_DARK, tex="rough_stone")
    head = height - 2.4  # where the shaft ends under its spreading head
    base = 1.3
    drums = max(int((head - base) / COLUMN_DRUM + 0.5), 1)
    drum = (head - base) / drums
    lit_seams = {(seed * 7 + 3) % drums, (seed * 5 + drums // 2) % drums}
    for i in range(drums):
        y = base + drum * i
        shade = 1.0 - 0.06 * ((seed + i * 3) % 3)
        r.part("cyl", 0, y + drum / 2, 0, 2 * COLUMN_R, drum - 0.08, 2 * COLUMN_R, _dim(COLUMN_PALE, shade),
               tex="ashlar", ry=i * 0.7)  # fmt: skip
        if i == 0:
            continue
        if i % COLUMN_BAND_EVERY == 0:  # a broad band of darker stone
            r.part("cyl", 0, y, 0, 2 * COLUMN_R + 0.24, 0.5, 2 * COLUMN_R + 0.24, MASONRY_DARK,
                   tex="rough_stone")  # fmt: skip
        elif i in lit_seams:  # the mortar-light leaking from a seam
            r.part("cyl", 0, y, 0, 2 * COLUMN_R + 0.03, 0.06, 2 * COLUMN_R + 0.03, CORE_TEAL, glow=True)
        else:
            r.part("cyl", 0, y, 0, 2 * COLUMN_R + 0.02, 0.08, 2 * COLUMN_R + 0.02, MORTAR)
    for k in range(COLUMN_FLUTES):  # the flutes, in three runs between the bands
        a = (k + 0.5) * 2 * math.pi / COLUMN_FLUTES
        x, z = math.cos(a) * (COLUMN_R - 0.02), math.sin(a) * (COLUMN_R - 0.02)
        for lo, hi in ((base, base + (head - base) * 0.33), (base + (head - base) * 0.36, head - 0.3)):
            r.part("cube", x, (lo + hi) / 2, z, 0.1, hi - lo, 0.14, _dim(COLUMN_PALE, 0.62), ry=-a)
    for c in range(3):  # cracks across its drums, the lowest glowing faintly
        a = seed * 1.7 + c * 2.1
        y = base + 2.0 + (head - base) * (0.12 + 0.3 * c) + (seed % 3)
        x, z = math.cos(a) * (COLUMN_R + 0.01), math.sin(a) * (COLUMN_R + 0.01)
        r.part("cube", x, y, z, 0.04, 1.6 + c * 0.6, 0.05, CORE_TEAL if c == 0 else COLD, ry=-a,
               rx=0.4 * (1 if c % 2 else -1), glow=c == 0)  # fmt: skip
    # the head: a capital spreading wide, then a block of it sunk up into the rock of the vault
    r.part(
        "cyl", 0, head + 0.25, 0, 2 * COLUMN_R + 0.3, 0.5, 2 * COLUMN_R + 0.3, MASONRY_DARK, tex="rough_stone"
    )
    r.part("frustum", 0, head + 1.0, 0, 2 * COLUMN_R + 1.4, 1.0, 2 * COLUMN_R + 1.4, COLUMN_PALE, tex="rough_stone",
           rx=math.pi)  # fmt: skip
    r.part("cube", 0, height - 0.45, 0, 2.6, 0.9, 2.6, MASONRY_DARK, tex="rough_stone", ry=0.1 * (seed % 4))
    a = seed * 1.3  # a chunk fallen onto its plinth
    r.part("cube", math.cos(a) * 0.8, 1.1, math.sin(a) * 0.8, 0.24, 0.2, 0.22, MASONRY, ry=a)
