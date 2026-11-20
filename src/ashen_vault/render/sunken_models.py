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


def _mix_rgb(a, b, k):
    return tuple(rround(x + (y - x) * k) for x, y in zip(a, b, strict=True))


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

CHAR = (64, 50, 44)  # the Keystone's stone once its shell has burst: charred, the fire showing through
TORCH_STONE = (164, 146, 118)  # the column it bears for a torch, pale with the years
IRON = (58, 54, 52)
COALS = (255, 96, 30)
TORCH_REST = 0.1  # how far the torch leans forward from upright while it is borne aloft


def keystone_pose(e):
    """(lean, left arm, left elbow, right arm, stamp, hurl, torch) for its moves: the lean forward of its
    body, the left (torch) arm's swing and elbow bend and the right arm's swing (radians from hanging,
    forward), how high it lifts its foot to stamp (0..1), how far it has wound back a block to throw
    (0..1, -1 once let go), and how far the torch tips forward from upright (radians: back for the
    windup of a rake, forward and down to drag its fire along the floor). Every blow travels down over
    its type's `impact`, heavily, rather than snapping."""
    k = _ease(_windup_k(e))
    hitting = e.state == "attack"
    snap = _ease(min(e.state_t / max(0.15, e.type.impact), 1.0)) if hitting else 0.0
    kind = e.attack_kind if e.state in ("windup", "attack") else None
    if kind == "torch_smash":  # the torch heaved back overhead, then brought down before it
        if not hitting:
            return -0.15 * k, -3.0 * k, 0.4, -0.6 * k, 0.0, 0.0, TORCH_REST - 0.9 * k
        return -0.15 + 0.6 * snap, -3.0 + 4.0 * snap, 0.4 - 0.3 * snap, -0.6, 0.0, 0.0, -0.8 + 2.4 * snap
    if kind == "cinder_rain":  # the torch thrust up overhead and shaken, harder as the embers fly
        shake = math.sin(e.anim_t * 14) * (0.12 * k if not hitting else 0.3)
        return -0.1 * k, -3.0 * k + shake, 0.15, -0.4 * k, 0.0, 0.0, shake * 1.5
    if kind == "ember_nova":  # the torch lifted high in both fists, then driven down at its feet
        if not hitting:
            return -0.12 * k, -2.7 * k, 0.3, -2.5 * k, 0.0, 0.0, 0.0
        return -0.12 + 0.55 * snap, -2.7 + 3.3 * snap, 0.3 + 0.5 * snap, -2.5 + 3.0 * snap, 0.0, 0.0, 0.0
    if kind == "slam":  # both fists overhead, the torch with them, then down
        up = -2.9 * k if not hitting else -2.9 + 3.7 * snap
        return 0.1 + 0.35 * snap, up, 0.3, up, 0.0, 0.0, -0.4 * k if not hitting else -0.4 + 2.0 * snap
    if kind == "sweep":  # arms flung out to scythe all round
        return 0.05, -1.5, 0.2, -1.5, 0.0, 0.0, 1.5
    if kind == "quake":  # the foot rises high, the torch held up out of the way
        return -0.1 * k, 0.3 - 0.6 * k, 1.2, -0.6 * k, (k if not hitting else 1.0 - snap), 0.0, -0.2 * k
    if kind == "hurl":  # the right arm winds back with a block; the torch stays aloft
        back = 2.4 * k if not hitting else 2.4 - 4.6 * snap
        return 0.1, 0.5, 0.9, back, 0.0, (k if not hitting else -1.0), TORCH_REST
    if kind == "breath":  # the torch swung back low behind it, then dragged forward along the floor
        if not hitting:
            return 0.15 - 0.2 * k, 0.5 - 1.6 * k, 0.9 - 0.7 * k, 0.4 * k, 0.0, 0.0, TORCH_REST - 2.3 * k
        return -0.05 + 0.45 * snap, -1.1 + 2.3 * snap, 0.2, 0.4, 0.0, 0.0, -2.2 + 4.4 * snap
    sway = math.sin(e.anim_t * 1.6) * 0.08
    if e.state == "hurt":
        return -0.2, 0.7, 0.6, 0.5, 0.0, 0.0, -0.3
    return 0.15, 0.5 + sway * 0.5, 0.9, -sway, 0.0, 0.0, TORCH_REST


def _keystone_torch(r, t, lit, blaze, phase2, spray=0.0):
    """The torch it bears: a fluted column of the old city's sandstone bound in iron, an iron basket of
    coals at its head, burning (a roaring blaze in its ember phase), cold and dark once it is slain.
    Shaken (`spray`, 0..1), embers fly up out of the basket in a fountain."""
    r.part("cyl", 0, 0.7, 0, 0.36, 3.4, 0.36, TORCH_STONE, tex="rough_stone")  # the column's shaft
    for i in range(4):  # its fluting
        a = i * math.pi / 2 + 0.4
        r.part("cube", math.cos(a) * 0.17, 0.7, math.sin(a) * 0.17, 0.05, 3.2, 0.05, _dim(TORCH_STONE, 0.72))
    r.part("cube", 0, -1.05, 0, 0.5, 0.12, 0.5, _dim(TORCH_STONE, 0.82))  # its broken base
    for y in (-0.55, 0.55, 1.6):  # iron bands round it
        r.part("cyl", 0, y, 0, 0.42, 0.1, 0.42, IRON)
    r.part("cube", 0, 2.45, 0, 0.78, 0.22, 0.78, _dim(TORCH_STONE, 0.9))  # the capital
    for i in range(6):  # the fire-basket: iron bars rising round the coals, splayed out
        a = i * math.pi / 3
        r.part("cube", math.cos(a) * 0.38, 2.85, math.sin(a) * 0.38, 0.06, 0.62, 0.06, IRON,
               rx=math.sin(a) * 0.3, rz=-math.cos(a) * 0.3)  # fmt: skip
    r.part("cyl", 0, 3.12, 0, 0.98, 0.08, 0.98, IRON)  # its rim
    r.part("sphere", 0, 2.75, 0, 0.66, 0.36, 0.66, COALS if lit else COLD, glow=lit)  # the coals
    if not lit:
        return
    _flame(r, 0, 3.3, 0, 0.6 * blaze, t)
    if spray > 0:  # shaken: a fountain of embers flung up out of the basket
        for i in range(8):
            u = (t * 1.6 + i / 8) % 1.0
            a = i * 2.4 + t
            d = 0.3 + 1.6 * u
            r.part("cube", math.cos(a) * d, 3.2 + 3.0 * u - 2.2 * u * u, math.sin(a) * d, 0.16 * spray,
                   0.16 * spray, 0.16 * spray, (255, rround(220 - 120 * u), 60), glow=True)  # fmt: skip
    if phase2:  # a roaring blaze: a second flame, and sparks whirled up off it
        _flame(r, 0.1, 4.2, 0.05, 0.4 * blaze, t + 1.3)
        for i in range(5):
            u = (t * 0.7 + i / 5) % 1.0
            a = t * 2 + i * 1.3
            r.part("cube", math.cos(a) * 0.4 * u, 3.4 + u * 2.4, math.sin(a) * 0.4 * u, 0.07, 0.07, 0.07,
                   _dim(EMBER, 1.0 - 0.6 * u), glow=True)  # fmt: skip


def keystone(r, e, t):
    """A titan of the old city's foundation stone, standing upright: squat piers of legs, a broad body of
    dressed courses under rough boulder plates, moss and roots in its seams, a heavy brow over two
    slits of amber light and a beard of moss and hanging roots; on its head a crown of broken column
    stubs, the last of the city it bore. In its left fist it bears a torch, a fluted column with an
    iron basket of burning coals at its head. At half HP its shell bursts: the boulder plates fall away,
    the stone under them is charred, an ember core glows through every seam, its eyes and mouth blaze,
    embers lift off its shoulders and the torch roars up. It slams and sweeps; then it stamps (the foot
    rises high), hurls blocks of masonry and drags its torch along the floor in a line of fire. Slain,
    it sinks to its knees and slumps forward on its fists, the torch going out."""
    dead = e.state == "dead"
    lit = not dead
    split = e.phase2 and lit
    kneel = death_fall(e, 0.9)
    slump = death_fall(e, 2.0)
    lean, left, left_elbow, right, stamp, hurl, torch = keystone_pose(e)
    raining = e.attack_kind == "cinder_rain" and e.state in ("windup", "attack")
    spray = (_windup_k(e) if e.state == "windup" else 1.0) if raining and lit else 0.0
    swing = walk_cycle(e, t) * 0.25
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    pulse = 0.5 + 0.5 * math.sin(t * 3.0)
    flashing = e.flashing
    base = CHAR if e.phase2 else MASONRY
    stone = hit_tint((236, 220, 200)) if flashing else base
    dark = _dim(stone, 0.72)
    eye = HIT_GLOW if flashing else (255, 236, 170) if split else EYE
    core = HIT_GLOW if flashing else _mix_rgb(CORE, (255, 210, 120), 0.5 * pulse) if split else COLD
    vein = 0.05 if not split else 0.11
    sink = -0.8 * kneel  # down onto its knees, the shins laid flat behind it
    with r.at(0, lift * 0.3 + sink, 0, ry=spin):
        for i, side in enumerate((-0.85, 0.85)):  # squat piers of legs
            raise_ = 1.0 * stamp if i == 1 else 0.0
            a = (swing if i else -swing) * (1 - kneel)
            with r.at(0, 2.45 + raise_, side, rz=a + (0.5 * stamp if i == 1 else 0.0)):
                r.part("cube", 0, -0.6, 0, 1.0, 1.2, 0.96, stone)  # the thigh
                r.part("cube", 0.02, -1.18, 0, 0.94, 0.08, 0.9, MORTAR)
                r.part("cube", 0.52, -0.6, 0, 0.1, 0.4, 0.04, core, glow=split)  # a seam down it
                with r.at(0, -1.2, 0, rz=-1.5 * kneel - (0.6 * stamp if i == 1 else 0.0)):
                    r.part("cube", 0, -0.55, 0, 0.9, 1.1, 0.9, dark)  # the shin
                    if not e.phase2:
                        r.part("sphere", 0.42, -0.3, 0, 0.3, 0.4, 0.56, MASONRY_DARK, tex="rough_stone")
                    r.part(
                        "cube",
                        0.25 * (1 - kneel),
                        -1.15,
                        0,
                        1.4 - 0.9 * kneel,
                        0.2,
                        1.1,
                        MASONRY_DARK,
                        tex="rough_stone",
                    )  # a foot, its toes curled under as it kneels
        with r.at(0, 2.5, 0, rz=-lean - 0.55 * slump):
            r.part("cube", 0, 0.15, 0, 1.4, 0.6, 2.0, MASONRY_DARK)  # hips
            for i, (y, w, d) in enumerate(
                ((0.7, 1.5, 2.2), (1.25, 1.7, 2.6), (1.8, 1.9, 2.9), (2.3, 1.9, 3.0))
            ):
                _course(r, y, w, d, 0.52, stone, i)
                r.part("cube", 0, y + 0.27, 0, w * 0.96, 0.04, d * 0.98, MORTAR)
            # Boulder plates over its body; in the ember phase most have burst off, two still clinging.
            plates = ((0.95, 1.65, -0.6, 0.5), (0.95, 1.65, 0.6, 0.5), (0.85, 0.85, 0.0, 0.46),
                      (0.7, 2.25, -1.2, 0.44), (0.7, 2.25, 1.2, 0.44), (-0.8, 1.6, 0.0, 0.6))  # fmt: skip
            for i, (x, y, z, s) in enumerate(plates):
                if e.phase2 and i not in (1, 5):
                    continue
                r.part(
                    "sphere",
                    x,
                    y,
                    z,
                    s * 0.6,
                    s,
                    s * 1.2,
                    _dim(stone, 0.9 + 0.05 * (i % 3)),
                    tex="rough_stone",
                )
            for y, z, s in ((0.9, -0.95, 0.3), (1.5, 1.05, 0.36), (2.05, -0.45, 0.28), (0.6, 0.6, 0.24)):
                r.part("sphere", 0.8, y, z, 0.1, s, s * 1.5, MOSS if not e.phase2 else _dim(MOSS, 0.5))
            for z in (-0.7, 0.35, 1.0):  # roots hanging out of its seams
                r.part("cube", 0.9, 1.1, z, 0.04, 0.8, 0.04, (90, 70, 48), rx=0.15 * z)
            # The cracks in its shell: dark seams, splitting open on its ember core in the ember phase.
            cracks = ((1.0, -0.4, 0.5), (1.55, 0.25, -0.6), (2.0, -0.9, 0.3), (0.7, 0.85, -0.2),
                      (2.35, 0.7, 0.4), (1.3, -1.05, -0.3))  # fmt: skip
            for y, z, a in cracks:
                r.part("cube", 0.97, y, z, 0.03, 0.5, vein, core, rx=a, glow=split)
            if split:
                r.part("sphere", 0.7, 1.5, 0, 0.32, 0.9, 1.1, core, glow=True)  # the core through its chest
                for z in (-0.6, 0.0, 0.6):
                    r.part("cube", -0.97, 1.4, z, 0.04, 1.6, 0.1, core, glow=True)  # down its back
                for i in range(6):  # embers lifting off its shoulders
                    u = (t * 0.45 + i / 6) % 1.0
                    side = 1 if i % 2 else -1
                    r.part("cube", -0.1 + 0.3 * math.sin(t + i), 2.6 + u * 2.2, side * (0.9 + 0.3 * u), 0.08,
                           0.08, 0.08, _dim(EMBER, 1.0 - 0.7 * u), glow=True)  # fmt: skip
            with r.at(0.55, 2.85, 0, rz=0.15):  # the head: a keystone, wider at its crown
                r.part("wedge", 0, 0, 0, 0.95, 0.85, 1.1, stone, rx=math.pi)
                r.part("cube", 0.2, 0.3, 0, 0.72, 0.18, 1.24, MASONRY_DARK, tex="rough_stone")  # a heavy brow
                for z in (-0.25, 0.25):
                    r.part("cube", 0.48, 0.14, z, 0.04, 0.07, 0.22, eye if lit else COLD, glow=lit)
                r.part("cube", 0.47, -0.16, 0, 0.03, 0.05, 0.5, core if split else PASSAGE_DARK, glow=split)
                for i in range(5):  # a beard of moss and hanging roots
                    z = (i - 2) * 0.2
                    length = 0.5 + 0.25 * ((i * 3) % 4) / 3
                    r.part("cube", 0.38, -0.4 - length / 2, z, 0.12, length, 0.14,
                           _dim(MOSS if i % 2 else (84, 66, 46), 0.6 if e.phase2 else 1.0))  # fmt: skip
                r.part("cube", -0.05, 0.48, 0, 0.9, 0.12, 1.15, MASONRY_DARK)  # the crown's ring of stone
                for x, z, h in ((0.25, -0.4, 0.6), (0.25, 0.4, 0.45), (-0.3, -0.35, 0.4), (-0.3, 0.3, 0.7)):
                    r.part(
                        "cyl", x, 0.54 + h / 2, z, 0.26, h, 0.26, (156, 140, 116) if not e.phase2 else CHAR
                    )
                    if split:
                        r.part(
                            "cube", x, 0.56 + h, z, 0.18, 0.04, 0.18, core, glow=True
                        )  # embers in its crown
            # Arms: long, boulder fists; the right free, the left bearing the torch.
            for side, swing_a, elbow in ((1, right, 0.25), (-1, left, left_elbow)):
                with r.at(0.1, 2.15, side * 1.6, rz=swing_a - 0.4 * slump):
                    r.part("sphere", 0, 0.05, 0, 1.0, 0.9, 0.9, dark)  # the shoulder
                    if not e.phase2 or side == 1:  # a boulder of a pauldron
                        r.part("sphere", -0.05, 0.35, side * 0.15, 0.7, 0.5, 0.8, stone, tex="rough_stone")
                    r.part("cube", 0, -0.7, 0, 0.66, 1.2, 0.66, stone)
                    r.part("cube", 0, -1.32, 0, 0.68, 0.06, 0.68, MORTAR)
                    r.part("cube", 0.34, -0.7, 0, 0.04, 0.6, vein, core, glow=split)
                    with r.at(0, -1.4, 0, rz=elbow + 0.9 * slump):
                        r.part("cube", 0, -0.6, 0, 0.6, 1.1, 0.6, _dim(stone, 0.9))
                        r.part("sphere", 0.05, -1.35, 0, 0.98, 0.84, 0.98, MASONRY_DARK)  # fist
                        for z in (-0.24, 0.24):
                            r.part("sphere", 0.4, -1.3, z, 0.28, 0.26, 0.28, stone)  # knuckle-stones
                        if hurl > 0 and side == 1:  # the block it is about to throw
                            r.part("cube", 0.1, -1.9, 0, 0.8, 0.66, 0.66, (150, 132, 104))
                        if side == -1:  # the torch, held upright whatever its arm does
                            fall = 0.8 * slump
                            with r.at(
                                0.05,
                                -1.35,
                                0,
                                rz=-(torch + fall) - (swing_a - 0.4 * slump) - (elbow + 0.9 * slump),
                            ):
                                _keystone_torch(r, t, lit, 2.4 if split else 1.0, e.phase2, spray)


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


# --- weapons (grip at the origin, pointing up +Y, like models.weapon) ---------------------------

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


def sun_shaft(r, t, height=14.0, width=2.4, rift=(CRACK_LEN, CRACK_WIDTH), yaw=0.0):
    """The light that falls from a crack in the cavern's roof far overhead: a tall, slanting curtain of
    sunlit haze, threads of brighter light running down through it, brightest where it lands in a pool
    on the floor, motes of dust turning in it. At its top, the crack itself: a jagged sliver of daylight
    set in the vault's hole (`world/vault.py`), a rim of gold round it. `rift` (length, width) and `yaw`
    (radians) widen the crack into a great rift: the curtain then runs the length of it."""
    length, crack_w = rift
    span = max(width * 0.85, length * 0.4)  # how far the curtain of haze runs along the rift
    with r.at(-height * math.sin(SHAFT_LEAN), height * math.cos(SHAFT_LEAN), 0, ry=yaw):  # the crack
        r.part("cube", 0, 0.6, 0, crack_w * 1.2, 0.1, length * 1.1, (255, 246, 220), glow=True)
        n = max(5, rround(length / 1.4))
        for i in range(n):  # the sliver, jagged: wider and narrower along its length
            z = (i / (n - 1) - 0.5) * length * 0.85
            w = crack_w * (0.45 + 0.25 * ((i * 3) % 4) / 3)
            r.part("cube", 0.1 * (i % 2), 0.3, z, w, 0.12, length * 1.2 / n, (255, 240, 200), glow=True,
                   ry=0.25 * (i % 3 - 1))  # fmt: skip
        for side in (-1, 1):  # its rim of gold, where the daylight catches the rock's broken lip
            r.part("cube", side * crack_w * 0.45, -0.1, 0, 0.2 + crack_w * 0.03, 0.3, length * 0.9,
                   _dim(GOLD_LIGHT, 0.85), tex="mist", glow=True, ry=side * 0.06)  # fmt: skip
    with r.at(0, 0, 0, ry=yaw), r.at(0, 0, 0, rz=SHAFT_LEAN):  # it falls a little aslant
        for i in range(3):  # the haze, in thin layers, widening and fading as it falls
            k = i / 2
            w = width * (0.35 + 0.35 * k)
            r.part("cube", 0, height * (0.82 - 0.3 * i), 0, w, height * 0.36, span * (0.7 + 0.3 * k),
                   _dim(GOLD_LIGHT, 0.8 - 0.15 * i), tex="mist", glow=True, ry=0.1 * i)  # fmt: skip
        threads = max(5, rround(span / 1.5))
        for i in range(threads):  # threads of brighter light down through it
            a = i * 1.3 + 0.4
            x = math.cos(a) * width * 0.25
            z = (i / max(threads - 1, 1) - 0.5) * span * 0.9
            shimmer = 0.85 + 0.15 * math.sin(t * 0.8 + i * 1.7)
            r.part("cube", x, height * 0.5, z, 0.06, height, 0.06, _dim(GOLD_LIGHT, shimmer), glow=True)
        motes = 10 + rround(span)
        for k in range(motes):  # motes of dust turning in it
            u = (t * 0.05 + k / motes) % 1.0
            a = t * 0.3 + k * 2.4
            z = (((k * 7) % motes) / motes - 0.5) * span * 0.9
            r.part("cube", math.cos(a) * width * 0.3, 0.3 + u * height * 0.8, z + math.sin(a) * 0.4,
                   0.04, 0.04, 0.04, GOLD_LIGHT, glow=True)  # fmt: skip
    with r.at(0, 0, 0, ry=yaw):  # the pool it lands in, drawn out along the rift
        r.part("cyl", 0, 0.02, 0, width * 1.2, 0.02, max(width * 1.2, span), _dim(GOLD_LIGHT, 0.8),
               tex="mist", glow=True)  # fmt: skip
        r.part("cyl", 0, 0.03, 0, width * 0.7, 0.02, max(width * 0.7, span * 0.7), (255, 236, 190), glow=True)


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
        r.part("cube", (i % 3 - 1) * width * 0.15, y, 0.12, w, 0.25 + 1.2 * u, 0.12, FOAM, glow=True)
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
