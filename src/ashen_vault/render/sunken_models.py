"""Models for Old Harrowmere, the sunken first city under the sewers: its Stone Golems, Sunken Sextons
and the Keystone, the rubble the Keystone hurls, and the city's dressing (the shaft of light from the
crack overhead, the drowned towers of its skyline and the breach in the cistern wall that leads down).
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

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
MASK_GLOW = (230, 220, 180)  # the pale light behind the slits of its bell-shard mask


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
    for a face a curved shard of a broken bronze bell, a pale light behind its eye slits. Bird legs end
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
    eye = MASK_GLOW if glow else COLD
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
                    for side in (-1, 1):
                        r.part(
                            "cube", 0.03, 0.03, side * 0.05, 0.02, 0.025, 0.05, eye, glow=glow
                        )  # eye slits
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


def keystone_pose(e):
    """(lean, left arm, left elbow, right arm, right elbow, stamp, hurl, charge) for its moves: the lean
    forward of its body, each arm's swing (radians from hanging, forward) and elbow bend, how high it
    lifts its foot to stamp (0..1), how far it has wound back a block to throw (0..1, -1 once let go),
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
    if kind == "slam":  # both slabs overhead, then down
        up = -2.9 * k if not hitting else -2.9 + 3.7 * snap
        return 0.1 + 0.35 * snap, up, 0.3, up, 0.3, 0.0, 0.0, 0.0
    if kind == "sweep":  # arms flung out before it to scythe all round
        return 0.05, 1.3, 0.1, 1.3, 0.1, 0.0, 0.0, 0.0
    if kind == "quake":  # the foot rises high
        return -0.1 * k, 0.3 - 0.6 * k, 0.6, -0.6 * k, 0.6, (k if not hitting else 1.0 - snap), 0.0, 0.0
    if kind == "hurl":  # the right arm winds back with a block, then lets it fly
        back = -2.4 * k if not hitting else -2.4 + 3.6 * snap
        return 0.1, 0.3, 0.4, back, 0.5, 0.0, (k if not hitting else -1.0), 0.0
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
    flare and motes of light lift off it. It slams and sweeps and brings a slab down before it; then
    it stamps (the foot rises high), hurls blocks of masonry, rakes a beam of the light along the floor
    from its heart, rains shards of its shell down round you and drives its fists down so rings of
    light run out from it. Slain, it sinks to its knees and slumps forward on its fists, and the light
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
                        if hurl > 0 and side == 1:  # the block it is about to throw
                            r.part("cube", 0.1, -1.5, 0, 0.32, 0.26, 0.26, (150, 132, 104))
                        if raining:  # shards of its shell torn loose over its fists, glowing
                            for i in range(3):
                                u = (t * 1.6 + i / 3) % 1.0
                                r.part("lozenge", 0.2 * math.sin(t * 3 + i), -1.5 - 0.6 * u, 0.15 * (i - 1),
                                       0.06, 0.14, 0.06, CORE_TEAL, glow=True, ry=t * 4 + i)  # fmt: skip


def rubble_chunk(r, rgb, t):
    """A block of masonry the Keystone hurls, tumbling, grit trailing off it."""
    r.part("cube", 0, 0, 0, 0.62, 0.5, 0.52, rgb, rx=t * 3, rz=t * 2)
    r.part("cube", 0.12, 0.1, 0.08, 0.3, 0.24, 0.3, _dim(rgb, 0.8), rx=t * 3)
    for i in range(3):
        a = t * 6 + i * 2.1
        r.part(
            "cube", -0.3 - 0.12 * i, math.sin(a) * 0.12, math.cos(a) * 0.12, 0.06, 0.06, 0.06, _dim(rgb, 0.7)
        )


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


def energy_core(r, t, height=1.2, quenched=False, shielded=False, tethers=(), yaw=0.0):
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
            a, b = (0.0, heart_y, 0.0), (dx, dy + 1.8, dz)
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


BREACH_HALF = 1.05  # half the width of the ragged hole in the wall, at its foot
BREACH_TOP = 3.1  # its height, at the middle of its broken crown
BREACH_BRICK = (100, 74, 62)  # the sewers' brick round the hole
WALL_FACE = -1.0  # a gate model's tile stands against its wall, whose face is here (local -X)


def _breach_opening(r, steps, lit, gloom, up):
    """A ragged hole knocked through the wall at the tile's -X face: a black opening flush on the face,
    broken courses of sewer brick standing out round it (stepped in toward a crown, a few bricks
    jutting), the lips of a stair painted down (or up) into the dark, fainter the farther they go, and
    the light at its far end: `gloom` low down for a stair going down, high up for one climbing."""
    x = WALL_FACE + 0.02
    r.part("cube", x, BREACH_TOP / 2, 0, 0.02, BREACH_TOP, 2 * BREACH_HALF, PASSAGE_DARK)
    for side in (-1, 1):  # the broken edge, its courses stepping in toward the crown
        for k in range(7):
            y = 0.22 + k * 0.44
            inward = 0.08 * k + 0.06 * ((k * 5 + (side > 0)) % 3)
            z = side * (BREACH_HALF + 0.12 - inward)
            jut = 0.18 + 0.1 * ((k * 3 + (side > 0)) % 3)
            r.part("cube", WALL_FACE + jut / 2, y, z, jut, 0.4, 0.36 + 0.08 * (k % 2),
                   _dim(BREACH_BRICK, 0.85 + 0.06 * (k % 3)), tex="sewer_brick", ry=0.12 * side * (k % 2))  # fmt: skip
    for k in range(5):  # the broken crown, lumps of brick fallen in over the hole
        z = -0.7 + k * 0.35
        y = BREACH_TOP - 0.1 + 0.18 * ((k * 2) % 3) - 0.12 * (k == 2)
        r.part("cube", WALL_FACE + 0.14, y, z, 0.28, 0.42, 0.42, _dim(BREACH_BRICK, 0.8 + 0.07 * (k % 2)),
               tex="sewer_brick", rx=0.2 * (k - 2))  # fmt: skip
    gy = BREACH_TOP - 0.55 if up else 0.42  # where the light at the stair's far end gathers
    for k in range(4):  # that light, soft: bands fading out from its heart, widest and faintest outside
        band = 0.16 + 0.22 * k
        r.part("cube", x + 0.004 + 0.002 * (3 - k), gy, 0, 0.004, band * 0.9, band * 2.2,
               _dim(gloom, 0.95 - 0.22 * k), glow=True)  # fmt: skip
    for k in range(steps):  # the stair's lips, in perspective, catching that light as they near it
        u = k / max(steps - 1, 1)
        y = (0.12 + 0.34 * k) if up else (0.9 - 0.11 * k)
        half = BREACH_HALF * (0.85 - 0.45 * u)
        rgb = _mix_rgb(_dim(lit, 0.75), _dim(gloom, 0.8), u)
        r.part("cube", x + 0.016, y, 0, 0.01, 0.045, 2 * half, rgb, glow=u > 0.5)


def cistern_breach(r, t):
    """The way down out of the Pall's cistern, set in the wall behind its tile (-X) and facing +X: a
    ragged hole where the cistern's wall gave way onto an older city beneath (`_breach_opening`), the
    worn sandstone lips of a stair going down into the dark, a warm glow far below, the brick it burst
    spilled out over the floor and dust still sifting from its broken crown."""
    _breach_opening(r, 5, MASONRY, (200, 140, 70), up=False)
    for i in range(9):  # the rubble, fanned out over the floor from the hole
        a = (i - 4) * 0.33
        d = 0.35 + 0.45 * ((i * 5) % 3)
        size = 0.34 - 0.06 * ((i * 5) % 3)
        r.part("cube", WALL_FACE + 0.1 + d * math.cos(a), size * 0.4, 1.1 * d * math.sin(a), size, size * 0.8,
               size * 0.9, _dim(BREACH_BRICK, 0.85 + 0.05 * (i % 3)), tex="sewer_brick", ry=i * 1.3)  # fmt: skip
    for i in range(3):  # dust sifting down from the broken crown
        u = (t * 0.4 + i / 3) % 1.0
        r.part("cube", WALL_FACE + 0.35, BREACH_TOP - 0.2 - 2.8 * u, -0.5 + 0.5 * i, 0.03, 0.06, 0.03,
               (170, 150, 120))  # fmt: skip


def sunken_stair(r, t):
    """The way back up to the sewers from the old city, set in the cavern wall behind its tile (-X): the
    same ragged hole (`_breach_opening`), seen from below, a stair of sewer brick climbing up into it
    toward the green gloom of the cistern, rubble at its foot and drips falling from its crown."""
    _breach_opening(r, 6, BREACH_BRICK, (60, 90, 50), up=True)
    for k in range(2):  # the stair's first steps, standing out of the hole
        r.part("cube", WALL_FACE + 0.25 - 0.12 * k, 0.1 + 0.2 * k, 0, 0.5, 0.2, 1.6, BREACH_BRICK,
               tex="sewer_brick")  # fmt: skip
    for i in range(6):
        a = i * 2.3
        r.part("cube", 0.0 + 0.4 * math.cos(a), 0.1, 0.7 * math.sin(a), 0.28, 0.18, 0.24, MASONRY_DARK, ry=a)
    for i in range(3):  # drips off the crown
        u = (t * 0.7 + i / 3) % 1.0
        r.part("cube", WALL_FACE + 0.3, BREACH_TOP - 0.3 - 2.8 * u, -0.4 + 0.4 * i, 0.02, 0.06, 0.02,
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
