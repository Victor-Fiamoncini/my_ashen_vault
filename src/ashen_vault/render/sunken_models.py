"""Models for Old Harrowmere, the sunken first city under the sewers: its Stone Golems, Sunken Sextons
and the Keystone, the rubble the Keystone hurls, and the city's dressing (the shaft of light from the
crack overhead, the drowned towers of its skyline and the breach in the cistern wall that leads down).
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.ai.enemy import STATUE_BURST
from ashen_vault.render.models import (
    BLADE_REST,
    EMBER,
    HIT_GLOW,
    PASSAGE_DARK,
    _dim,
    _ease,
    _flame,
    _mix,
    _spider_move,
    _swing_pose,
    aim_wrist,
    chop_angle,
    death_fall,
    elbow_bend,
    held,
    hit_tint,
    walk_cycle,
    wrist_angle,
)

MASONRY = (138, 120, 96)  # the old city's warm, worn sandstone
MASONRY_DARK = (98, 84, 68)
MORTAR = (70, 60, 50)
MOSS = (74, 92, 50)
STATUE_MOSS = (88, 100, 64)  # a golem asleep on its plinth: greener, the moss grown over it
EYE = (255, 176, 80)  # the amber light in a golem's eyes and the Keystone's
CORE = (255, 132, 40)  # the Keystone's ember core, showing through its split shell
COLD = (60, 52, 46)  # an eye or a crack gone dark
ROBE = (58, 62, 54)  # a sexton's sodden robe, dark with the water
ROBE_DARK = (40, 44, 38)
SEXTON_SKIN = (170, 168, 146)  # waterlogged, grey-green
BELL_BRONZE = (150, 116, 60)
HAFT = (82, 62, 42)
GOLD_LIGHT = (255, 214, 140)  # the shaft of light from the crack overhead
GOLD_MIST = (190, 150, 90)
TOWER_LIT = (230, 222, 210)  # a pale tint, so a tower's brick texture shows its own warm colour


def _windup_k(e):
    return min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0


def _course(r, y, w, d, h, rgb, seed):
    """One course of blocks across a body: two or three stones laid side by side with a seam of
    mortar between them, each a little proud or sunk of the next, as uneven as old masonry."""
    n = 2 if w < 0.8 else 3
    step = d / n
    for i in range(n):
        z = -d / 2 + step * (i + 0.5)
        jut = 0.02 * ((seed + i * 3) % 3)
        r.part("cube", jut, y, z, w + jut, h, step - 0.03, _dim(rgb, 0.92 + 0.05 * ((seed + i) % 3)))


# --- the Stone Golem ------------------------------------------------------------------------------


def stone_golem(r, e, t):
    """A golem of the old city's masonry: legs of stacked blocks, a body laid in three courses with
    moss in its seams, a keystone for a head with two slits of amber light, long arms of dressed stone
    ending in boulder fists, the right arm cracked through and bound with an old iron band. Its back
    has split open down the middle, the weak spot. Asleep on its plinth it stands as a statue, moss
    grown over it and its eyes dark; woken, the moss tears off it in clumps. A sweep spins it with its
    arms out, a slam brings both fists down. Slain, it sinks to its knees and topples forward."""
    k = e.rise_progress
    asleep = 1.0 - _ease(min(max((k - STATUE_BURST) / 0.2 + 0.5, 0.0), 1.0))
    statue = asleep > 0.5
    dead = e.state == "dead"
    lit = not statue and not dead
    swing = walk_cycle(e, t) * 0.35
    kneel = death_fall(e, 0.6)
    topple = death_fall(e, 1.5)
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit = _swing_pose(e, 0.0, -2.0, 0.9)
    wk = _windup_k(e)
    both = None
    if e.attack_kind == "slam" and e.state in ("windup", "attack"):
        both = -2.7 * wk if e.state == "windup" else -2.7 + 3.4 * min(e.state_t / 0.15, 1)
    elif e.attack_kind == "sweep" and e.state in ("windup", "attack"):
        both = -1.5
    stone = hit_tint((236, 220, 200)) if e.flashing else MASONRY
    moss = STATUE_MOSS if statue else MOSS
    eye = HIT_GLOW if e.flashing else EYE
    with (
        r.at(0, lift * 0.3 - 0.45 * kneel + 0.85 * topple, 0, ry=spin),
        r.at(0, 0, 0, rz=-1.15 * topple),
    ):
        for side, a in ((-0.28, swing), (0.28, -swing)):
            with r.at(0, 0.78, side, rz=a + 1.5 * kneel):
                r.part("cube", 0, -0.18, 0, 0.4, 0.38, 0.36, stone)  # thigh block
                r.part("cube", 0.02, -0.38, 0, 0.36, 0.06, 0.32, MORTAR)  # the joint, a seam of mortar
                with r.at(0, -0.4, 0):
                    r.part("cube", 0, -0.16, 0, 0.36, 0.34, 0.34, _dim(stone, 0.92))
                    r.part("cube", 0.08, -0.34, 0, 0.56, 0.12, 0.42, MASONRY_DARK)  # foot
        r.part("cube", 0, 0.92, 0, 0.62, 0.26, 0.82, MASONRY_DARK)  # hips
        for i, (y, w, d) in enumerate(((1.22, 0.78, 1.0), (1.56, 0.84, 1.1), (1.88, 0.8, 1.16))):
            _course(r, y, w, d, 0.32, stone, i)
            r.part("cube", 0.0, y + 0.17, 0, w * 0.96, 0.03, d * 0.98, MORTAR)  # the seam above it
        for y, z, s in ((1.4, -0.42, 0.18), (1.72, 0.38, 0.22), (1.06, 0.2, 0.16), (2.04, -0.3, 0.2)):
            r.part("sphere", 0.38, y, z, 0.08, s, s * 1.4, moss)  # moss in the seams
        if statue:  # a blanket of moss grown over its shoulders and head
            r.part("cube", 0.0, 2.08, 0, 0.86, 0.1, 1.2, moss)
            r.part("cube", 0.25, 2.3, 0, 0.36, 0.08, 0.5, moss)
        # Its back has split open down the middle: strike it from behind.
        r.part("cube", -0.41, 1.5, 0, 0.04, 0.7, 0.18, PASSAGE_DARK)
        r.part("cube", -0.42, 1.5, 0, 0.03, 0.5, 0.06, EMBER if lit else COLD, glow=lit)
        with r.at(0.12, 2.24, 0):  # a keystone of a head, wider at its crown, sunk between the shoulders
            r.part("wedge", 0, 0, 0, 0.42, 0.36, 0.5, stone, rx=math.pi)
            r.part("cube", 0, 0.2, 0, 0.46, 0.06, 0.56, MASONRY_DARK)  # its crown
            for z in (-0.1, 0.1):
                r.part("cube", 0.22, 0.04, z, 0.03, 0.04, 0.1, eye if lit else COLD, glow=lit)
            r.part("cube", 0.22, -0.1, 0, 0.02, 0.02, 0.2, MORTAR)  # a crack for a mouth
        for side, z in ((1, 0.6), (-1, -0.6)):
            a = both if both is not None else (hit if side == 1 else swing * 0.5)
            with r.at(0, 1.92, z, rz=a - 0.5 * kneel):
                r.part("cube", 0, -0.08, 0, 0.42, 0.4, 0.42, _dim(stone, 0.96))  # shoulder
                r.part("cube", 0, -0.42, 0, 0.3, 0.38, 0.3, stone)
                if side == 1:  # the cracked arm, bound with an old iron band
                    r.part("cube", 0.155, -0.4, 0, 0.02, 0.3, 0.03, PASSAGE_DARK, rx=0.4)
                    r.part("cube", 0, -0.5, 0, 0.33, 0.06, 0.33, (74, 64, 58))
                with r.at(0, -0.62, 0, rz=0.2):
                    r.part("cube", 0, -0.2, 0, 0.28, 0.38, 0.28, _dim(stone, 0.9))
                    r.part("sphere", 0.04, -0.48, 0, 0.5, 0.44, 0.5, MASONRY_DARK)  # fist
                    r.part("sphere", 0.2, -0.46, 0.08, 0.16, 0.14, 0.16, stone)  # a knuckle-stone


# --- the Sunken Sexton ----------------------------------------------------------------------------


def sexton_arms(e):
    """The bell-hammer arm's (shoulder, elbow, wrist) and how high the bell hand is raised (0..1)
    for its pose: it chops overhead with the hammer, and on a toll lifts the hand-bell high and
    shakes it."""
    tolling = e.attack_kind == "toll" and e.state in ("windup", "attack")
    if tolling:
        ring = 1.0 if e.state == "attack" else _ease(_windup_k(e))
        return 0.4, 0.3, aim_wrist(BLADE_REST, 0.7), ring
    return chop_angle(e), elbow_bend(e), wrist_angle(e), 0.0


def sunken_sexton(r, e, t):
    """One of the old city's bell-keepers, stooped and sodden: a long robe dark with the water,
    clinging and dripping at the hem, a hood fallen forward over a grey, swollen face, a bronze
    hand-bell on a cord at its belt and a horn lantern hung beside it, burning low. It carries a
    bell-hammer, a long haft with a heavy bronze head, and chops with it overhead. Given room, it
    lifts the bell high and shakes it. Slain, it sags and falls onto its back."""
    fall = death_fall(e, 0.8)
    dead = e.state == "dead"
    swing = walk_cycle(e, t) * 0.5
    skin = hit_tint((236, 230, 214)) if e.flashing else SEXTON_SKIN
    robe = hit_tint((200, 200, 190)) if e.flashing else ROBE
    shoulder, elbow, wrist, ring = sexton_arms(e)
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
        with r.at(0.1, 0.84, -0.22):  # the hand-bell on its cord, at the belt, when not in hand
            if ring == 0.0:
                r.part("cone", 0, -0.08, 0, 0.12, 0.14, 0.12, BELL_BRONZE)
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
            # The bell arm (-Z): hangs, or lifts the hand-bell high and shakes it.
            with r.at(0, 0.55, -0.25, rz=_mix(0.2, 2.6, ring)):
                r.part("cube", 0, -0.15, 0, 0.09, 0.3, 0.09, robe)
                with r.at(0, -0.3, 0, rz=0.3):
                    r.part("cube", 0, -0.13, 0, 0.08, 0.26, 0.08, robe)
                    r.part("sphere", 0, -0.28, 0, 0.09, 0.09, 0.09, skin)
                    if ring > 0.0:
                        shake = math.sin(t * 30) * 0.3 * ring
                        with r.at(0, -0.36, 0, rz=shake):
                            r.part("cyl", 0, 0.02, 0, 0.03, 0.12, 0.03, HAFT)
                            r.part("cone", 0, -0.12, 0, 0.18, 0.2, 0.18, BELL_BRONZE, rz=math.pi)
                            r.part("sphere", 0, -0.22, 0, 0.05, 0.05, 0.05, (90, 70, 40))  # its clapper
            # The hammer arm (+Z): chops overhead.
            with r.at(0, 0.55, 0.25, rz=shoulder):
                r.part("sphere", 0, 0, 0, 0.12, 0.12, 0.12, _dim(robe, 0.9))
                r.part("cube", 0, -0.15, 0, 0.09, 0.3, 0.09, robe)
                with r.at(0, -0.3, 0, rz=elbow):
                    r.part("cube", 0, -0.13, 0, 0.08, 0.26, 0.08, robe)
                    with r.at(0, -0.3, 0), held(r, wrist, skin, size=0.1, splay=0.2):
                        r.part("cube", 0.32, 0, 0, 0.9, 0.05, 0.05, HAFT)  # the long haft
                        r.part("cyl", 0.8, 0, 0, 0.16, 0.24, 0.16, BELL_BRONZE, rx=math.pi / 2)  # its head
                        r.part("cyl", 0.8, 0, 0, 0.2, 0.05, 0.2, _dim(BELL_BRONZE, 0.8), rx=math.pi / 2)
                        r.part("cube", -0.14, 0, 0, 0.06, 0.07, 0.07, _dim(HAFT, 0.8))  # the butt


# --- the Keystone ---------------------------------------------------------------------------------


def keystone_pose(e):
    """(lean, left arm, right arm, stamp, hurl) for its moves: the lean forward of its body, each
    arm's swing (radians from hanging, forward), how high it lifts its foot to stamp (0..1) and how
    far it has wound back a block to throw (0..1, -1 once let go)."""
    k = _ease(_windup_k(e))
    hitting = e.state == "attack"
    snap = min(e.state_t / 0.15, 1.0) if hitting else 0.0
    kind = e.attack_kind if e.state in ("windup", "attack") else None
    if kind == "slam":
        up = -2.9 * k if not hitting else -2.9 + 3.7 * snap
        return 0.1 + 0.35 * snap, up, up, 0.0, 0.0
    if kind == "sweep":
        return 0.05, -1.5, -1.5, 0.0, 0.0
    if kind == "quake":
        return -0.1 * k, -0.6 * k, -0.6 * k, (k if not hitting else 1.0 - snap), 0.0
    if kind == "hurl":
        back = 2.4 * k if not hitting else 2.4 - 4.6 * snap
        return 0.1, 0.3, back, 0.0, (k if not hitting else -1.0)
    sway = math.sin(e.anim_t * 1.6) * 0.08
    if e.state == "hurt":
        return -0.2, 0.5, 0.5, 0.0, 0.0
    return 0.25, sway, -sway, 0.0, 0.0


def keystone(r, e, t):
    """A giant of the old city's foundation stone, hunched under the slab of foundation it bore on
    its back: a broad body of dressed courses, moss and roots in its seams, the stubs of columns and
    a run of flagstones still standing on the slab across its shoulders. Its head is a keystone sunk
    low between them, two slits of amber light under a heavy brow; its arms hang long, knuckles of
    boulders near the floor, its legs are squat piers. At half HP its shell splits along the seams on
    an ember core that glows through every crack. It slams and sweeps; then it stamps (the foot rises
    high) and hurls blocks of masonry. Slain, it sinks to its knees and slumps forward on its fists."""
    dead = e.state == "dead"
    lit = not dead
    split = e.phase2 and lit
    kneel = death_fall(e, 0.9)
    slump = death_fall(e, 2.0)
    lean, left, right, stamp, hurl = keystone_pose(e)
    swing = walk_cycle(e, t) * 0.25
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    stone = hit_tint((236, 220, 200)) if e.flashing else MASONRY
    dark = _dim(stone, 0.72)
    eye = HIT_GLOW if e.flashing else EYE
    core = HIT_GLOW if e.flashing else CORE
    sink = -0.25 * kneel  # down onto its knees, the shins laid flat behind it
    with r.at(0, lift * 0.3 + sink, 0, ry=spin):
        for i, side in enumerate((-0.75, 0.75)):  # squat piers of legs
            raise_ = 0.9 * stamp if i == 1 else 0.0
            a = (swing if i else -swing) * (1 - kneel)
            with r.at(0, 1.5 + raise_, side, rz=a):
                r.part("cube", 0, -0.4, 0, 0.9, 0.8, 0.86, stone)
                r.part("cube", 0.02, -0.82, 0, 0.84, 0.08, 0.8, MORTAR)
                with r.at(0, -0.85, 0, rz=-1.5 * kneel):
                    r.part("cube", 0, -0.3, 0, 0.82, 0.6, 0.8, dark)
                    r.part(
                        "cube",
                        0.2 * (1 - kneel),
                        -0.58,
                        0,
                        1.2 - 0.8 * kneel,
                        0.12,
                        0.96,
                        MASONRY_DARK,
                        tex="rough_stone",
                    )  # a foot, its toes curled under as it kneels
        with r.at(0, 1.6, 0, rz=-lean - 0.55 * slump):
            r.part("cube", 0, 0.2, 0, 1.3, 0.5, 1.8, MASONRY_DARK)  # hips
            for i, (y, w, d) in enumerate(((0.75, 1.5, 2.1), (1.3, 1.7, 2.4), (1.85, 1.8, 2.6))):
                _course(r, y, w, d, 0.52, stone, i)
                r.part("cube", 0, y + 0.27, 0, w * 0.96, 0.04, d * 0.98, MORTAR)
            for y, z, s in ((0.9, -0.8, 0.3), (1.5, 0.9, 0.36), (2.0, -0.4, 0.28), (0.6, 0.5, 0.24)):
                r.part("sphere", 0.78, y, z, 0.1, s, s * 1.5, MOSS)  # moss in the seams
            for z in (-0.6, 0.3, 0.95):  # roots hanging out of them
                r.part("cube", 0.86, 1.1, z, 0.04, 0.7, 0.04, (90, 70, 48), rx=0.15 * z)
            # The cracks in its shell: dark seams, splitting open on its ember core in phase two.
            for y, z, a in ((1.0, -0.4, 0.5), (1.55, 0.55, -0.6), (2.0, -0.9, 0.3), (0.7, 0.85, -0.2)):
                r.part("cube", 0.79, y, z, 0.03, 0.42, 0.05 if not split else 0.1, core if split else COLD,
                       rx=a, glow=split)  # fmt: skip
            if split:
                r.part("sphere", 0.6, 1.4, 0, 0.3, 0.8, 1.0, core, glow=True)  # the core through its chest
                for z in (-0.5, 0.5):
                    r.part("cube", -0.8, 1.4, z, 0.04, 0.9, 0.08, core, glow=True)  # down its back
                _flame(r, 0.8, 1.95, 0.0, 0.18, t)
            # The slab of foundation across its back: flagstones and column stubs still standing on it.
            with r.at(-0.35, 2.45, 0, rz=0.12):
                r.part("cube", 0, 0, 0, 1.9, 0.36, 3.0, MASONRY_DARK)
                for i in range(4):
                    r.part("cube", -0.5 + (i % 2) * 0.9, 0.2, -1.1 + i * 0.72, 0.8, 0.06, 0.66,
                           _dim(stone, 0.95 + 0.04 * (i % 2)))  # fmt: skip
                for z, h in ((-1.1, 1.3), (0.9, 0.8)):  # two broken column stubs
                    r.part("cyl", -0.3, 0.2 + h / 2, z, 0.42, h, 0.42, (156, 140, 116))
                    r.part("cube", -0.3, 0.22, z, 0.56, 0.1, 0.56, MASONRY_DARK)  # its base
                r.part("cube", 0.2, 0.32, 0.2, 0.5, 0.26, 0.4, dark, ry=0.4)  # a tumbled block
            with r.at(0.75, 2.2, 0, rz=0.3):  # the head: a keystone sunk low between its shoulders
                r.part("wedge", 0, 0, 0, 0.7, 0.66, 0.9, stone, rx=math.pi)
                r.part("cube", 0.12, 0.28, 0, 0.6, 0.14, 1.0, MASONRY_DARK)  # its brow
                for z in (-0.2, 0.2):
                    r.part("cube", 0.36, 0.12, z, 0.04, 0.06, 0.18, eye if lit else COLD, glow=lit)
                r.part("cube", 0.36, -0.12, 0, 0.03, 0.04, 0.4, PASSAGE_DARK)  # a seam of a mouth
                if split:
                    r.part("cube", 0.37, -0.12, 0, 0.02, 0.02, 0.34, core, glow=True)
            # Arms: long and hanging, boulder fists near the floor.
            for side, swing_a in ((1, right), (-1, left)):
                with r.at(0.1, 1.8, side * 1.35, rz=swing_a - 0.4 * slump):
                    r.part("sphere", 0, 0.05, 0, 0.9, 0.8, 0.8, dark)  # the shoulder
                    r.part("cube", 0, -0.55, 0, 0.6, 0.9, 0.6, stone)
                    r.part("cube", 0, -1.02, 0, 0.62, 0.06, 0.62, MORTAR)
                    with r.at(0, -1.1, 0, rz=0.25 + 0.9 * slump):
                        r.part("cube", 0, -0.5, 0, 0.56, 0.9, 0.56, _dim(stone, 0.9))
                        r.part("sphere", 0.05, -1.1, 0, 0.95, 0.8, 0.95, MASONRY_DARK)  # fist
                        for z in (-0.22, 0.22):
                            r.part("sphere", 0.38, -1.05, z, 0.26, 0.24, 0.26, stone)  # knuckle-stones
                        if hurl > 0 and side == 1:  # the block it is about to throw
                            r.part("cube", 0.1, -1.6, 0, 0.7, 0.6, 0.6, (150, 132, 104))


def rubble_chunk(r, rgb, t):
    """A block of masonry the Keystone hurls, tumbling, grit trailing off it."""
    r.part("cube", 0, 0, 0, 0.62, 0.5, 0.52, rgb, rx=t * 3, rz=t * 2)
    r.part("cube", 0.12, 0.1, 0.08, 0.3, 0.24, 0.3, _dim(rgb, 0.8), rx=t * 3)
    for i in range(3):
        a = t * 6 + i * 2.1
        r.part(
            "cube", -0.3 - 0.12 * i, math.sin(a) * 0.12, math.cos(a) * 0.12, 0.06, 0.06, 0.06, _dim(rgb, 0.7)
        )


# --- Old Harrowmere's dressing --------------------------------------------------------------------


def sun_shaft(r, t, height=14.0, width=2.4):
    """The light that falls from a crack in the cavern's roof far overhead: a tall, slanting column of
    sunlit haze, threads of brighter light running down through it, brightest where it lands in a pool
    on the floor, motes of dust turning in it."""
    with r.at(0, 0, 0, rz=0.12):  # it falls a little aslant, from the crack off to one side
        for i in range(3):  # the haze, in layers, widening as it falls
            k = i / 2
            w = width * (0.55 + 0.45 * k)
            r.part("cube", 0, height * (0.82 - 0.3 * i), 0, w, height * 0.36, w * 0.85,
                   _dim(GOLD_LIGHT, 1.0 - 0.12 * i), tex="mist", glow=True, ry=0.4 * i)  # fmt: skip
        for i in range(5):  # threads of brighter light down through it
            a = i * 1.3 + 0.4
            rad = width * 0.28 * (0.4 + 0.6 * ((i * 3) % 5) / 5)
            shimmer = 0.85 + 0.15 * math.sin(t * 0.8 + i * 1.7)
            r.part("cube", math.cos(a) * rad, height * 0.5, math.sin(a) * rad, 0.06, height, 0.06,
                   _dim(GOLD_LIGHT, shimmer), glow=True)  # fmt: skip
    r.part("cyl", 0, 0.02, 0, width * 1.2, 0.02, width * 1.2, _dim(GOLD_LIGHT, 0.8), tex="mist", glow=True)
    r.part(
        "cyl", 0, 0.03, 0, width * 0.7, 0.02, width * 0.7, (255, 236, 190), glow=True
    )  # the pool it lands in
    for k in range(10):  # motes of dust turning in it
        u = (t * 0.05 + k / 10) % 1.0
        a = t * 0.3 + k * 2.4
        rad = width * 0.35 * (0.3 + 0.7 * ((k * 7) % 5) / 5)
        r.part("cube", math.cos(a) * rad, 0.3 + u * height * 0.8, math.sin(a) * rad, 0.04, 0.04, 0.04,
               GOLD_LIGHT, glow=True)  # fmt: skip


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


def cistern_breach(r, t):
    """The way down out of the Pall's cistern: a breach where the wall of the cistern gave way onto an
    older city beneath, its ragged edge of broken brick, the rubble spilled out over the floor, a
    stair of older, warmer stone going down into the dark beyond and a warm glow far below it."""
    for side in (-1, 1):  # the ragged jambs of the breach
        for k in range(5):
            r.part("cube", -0.6, 0.35 + k * 0.6, side * (0.85 + 0.12 * ((k * 3) % 2)), 0.5, 0.6,
                   0.4 + 0.1 * (k % 3), (100, 74, 62), tex="sewer_brick", rz=0.1 * side * k)  # fmt: skip
    for k in range(4):  # the broken lintel overhead
        r.part("cube", -0.6, 3.1 + 0.12 * (k % 2), -0.75 + k * 0.5, 0.5, 0.4, 0.5, (92, 70, 58),
               tex="sewer_brick", rx=0.15 * (k - 1.5))  # fmt: skip
    r.part("cube", -0.75, 1.6, 0, 0.1, 3.0, 1.5, PASSAGE_DARK)  # the dark beyond
    for k in range(5):  # the older stair, going down into it
        r.part("cube", -0.7 - 0.1 * k, 0.4 - 0.08 * k, 0, 0.12, 0.08, 1.3, _dim(MASONRY, 1 - 0.12 * k))
    r.part("cube", -0.76, 0.3, 0, 0.04, 0.4, 1.0, (200, 140, 70), glow=True)  # a warm glow far below
    for i in range(7):  # rubble spilled out over the floor
        a = i * 1.7
        r.part("cube", 0.1 + 0.4 * math.cos(a), 0.12, 0.7 * math.sin(a), 0.3 + 0.05 * (i % 3), 0.2,
               0.26, (96 + 6 * (i % 3), 76, 62), tex="sewer_brick", ry=a)  # fmt: skip
    for i in range(3):  # dust sifting down from the broken edge
        u = (t * 0.4 + i / 3) % 1.0
        r.part("cube", -0.4, 3.0 - 2.8 * u, -0.5 + 0.5 * i, 0.03, 0.06, 0.03, (170, 150, 120))


def sunken_stair(r, t):
    """The way back up to the sewers from the old city: a narrow stair of sewer brick climbing into a
    breach in the cavern wall, rubble at its foot, the green gloom of the cistern above it."""
    for k in range(6):  # the stair, climbing back into the wall
        r.part("cube", -0.3 - 0.12 * k, 0.1 + 0.25 * k, 0, 0.3, 0.2, 1.2, (100, 74, 62), tex="sewer_brick")
    for side in (-1, 1):
        for k in range(4):
            r.part("cube", -0.7, 0.4 + k * 0.7, side * 0.85, 0.5, 0.7, 0.4, (100, 74, 62), tex="sewer_brick",
                   rz=0.08 * side * k)  # fmt: skip
    r.part("cube", -0.9, 2.6, 0, 0.1, 1.2, 1.3, (60, 90, 50), glow=True)  # the cistern's green gloom above
    r.part("cube", -0.75, 3.1, 0, 0.5, 0.4, 2.1, (92, 70, 58), tex="sewer_brick")  # a lintel of brick
    for i in range(6):
        a = i * 2.3
        r.part("cube", 0.2 + 0.4 * math.cos(a), 0.1, 0.6 * math.sin(a), 0.28, 0.18, 0.24, MASONRY_DARK, ry=a)
    for i in range(3):  # drips off the lintel
        u = (t * 0.7 + i / 3) % 1.0
        r.part("cube", -0.5, 2.9 - 2.8 * u, -0.4 + 0.4 * i, 0.02, 0.06, 0.02, (150, 180, 150))


def _keystone_arch(r, style, t, lit):
    """A keystone of the old city's sandstone set over the lintel, carved with a giant's shoulders
    bearing up a slab; an amber light burns in the cracks round it while the Keystone lives."""
    for face in (-1, 1):
        with r.at(face * 0.25, 3.45, 0):
            r.part("wedge", 0, 0, 0, 0.12, 0.5, 0.6, MASONRY, tex="rough_stone", rx=math.pi)
            r.part("cube", 0, 0.32, 0, 0.12, 0.12, 1.2, MASONRY_DARK)  # the slab it bears up
            for z in (-0.38, 0.38):
                r.part(
                    "cube", face * 0.02, -0.1, z, 0.04, 0.26, 0.04, EYE if lit else COLD, glow=lit, rx=0.3 * z
                )


def _keystone_leaf(r, style, side, face, t, lit):
    """Leaves of old, sun-bleached timber, the water line still dark across them."""
    r.part("cube", face * 0.085, 0.9, 0, 0.02, 0.08, 0.92, (60, 54, 44))  # the water line
    r.part("cube", face * 0.1, 1.5, -side * 0.25, 0.03, 0.16, 0.16, style.iron, rx=math.pi / 4)  # the ring
