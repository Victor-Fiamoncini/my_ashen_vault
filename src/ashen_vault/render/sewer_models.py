"""Models for the Harrow Sewers under the town: its rats and their brood-mother Mother Gnawl, the sludge
slimes and the gobbets they burst into, the drowned that lie in the sludge, the bilge leeches, the Sump
Maw (the Sump itself grown hungry: a wave of sludge with a fanged maw, crusted with skulls) in the deepest
cistern, the ways down from the streets (a grate in town, a ladder below) and the sewers' dressing (drain pipes, sluice wheels, the outfall's great grate, a rat's nest).
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.render.models import (
    PASSAGE_DARK,
    _bar,
    _dim,
    _ease,
    _mix,
    _swing_pose,
    death_fall,
    hand,
    hit_tint,
    strike_angle,
)

RAT_FUR = (76, 74, 76)  # dark, sooty grey
RAT_DARK = (46, 44, 46)
RAT_PINK = (168, 128, 118)  # legs and tail, bare and pale
RAT_CLAW = (70, 56, 48)
RAT_EAR = (130, 84, 74)  # naked, the light showing red through
RAT_NOSE = (150, 70, 72)
RAT_GUM = (130, 48, 52)
RAT_TOOTH = (214, 190, 120)
RAT_EYE = (48, 44, 36)
RAT_EYE_LIT = (226, 214, 170)  # round, milky, catching the light
RAT_SORE = (124, 40, 44)  # raw, weeping wounds in the hide
RAT_FLESH = (176, 82, 78)
MANGE = (132, 104, 92)  # bald, grey-pink skin where the fur has gone

SLUDGE = (70, 64, 38)
SLUDGE_DARK = (46, 44, 28)
SLUDGE_SCUM = (118, 116, 56)
SLUDGE_EYE = (220, 214, 150)

DROWNED_SKIN = (124, 138, 112)  # bloated, grey-green
DROWNED_DARK = (84, 96, 76)
DROWNED_RAG = (62, 66, 54)
DROWNED_HAIR = (36, 40, 30)
WEED = (52, 74, 40)
HOLLOW = (14, 16, 12)

LEECH = (54, 46, 40)
LEECH_BELLY = (118, 92, 70)
LEECH_STRIPE = (130, 110, 50)
LEECH_MOUTH = (120, 40, 44)

MAW_SLIME = (56, 86, 116)  # the Maw's bulk, black-blue, darker than any slime
MAW_DARK = (34, 50, 68)
MAW_GLOW = (110, 200, 140)  # its gullet, the skulls' eyes when it rages, and the sludge it spits
MAW_GLOW_COLD = (36, 52, 50)
MAW_GULLET = (16, 40, 36)
MAW_FANG = (22, 28, 34)  # black, glassy fangs
MAW_BONE = (218, 210, 190)
MAW_DIRT = (70, 56, 40)
MAW_STONE = (96, 94, 88)

BRICK = (100, 70, 56)
IRON = (62, 60, 64)
RUST = (112, 66, 42)
OLD_WOOD = (74, 62, 46)


# --- rats -----------------------------------------------------------------------------------------


def _rat_pose(e, t):
    """(lift, pitch, stretch, spin): how a rat crouches, rears and springs through its attacks. `lift`
    raises the body, `pitch` tips the head up, `stretch` reaches the body forward, `spin` turns it
    (a sweep's rake all round, a tail lash's whip behind)."""
    lift = pitch = stretch = spin = 0.0
    kind = e.attack_kind
    if e.state == "windup":
        k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
        lift, pitch, stretch = -0.03 * k, 0.5 * k, -0.06 * k  # crouched, head up, ready to spring
        if kind == "sweep":
            spin = -0.6 * k
        elif kind == "tail_lash":
            spin = 0.5 * k  # coiling the other way
        elif kind == "squeal":
            lift, pitch, stretch = 0.12 * k, 0.9 * k, -0.1 * k  # rearing, the head thrown back
    elif e.state == "attack":
        k = min(e.state_t / 0.2, 1.0)
        lift, pitch, stretch = 0.05 * k, -0.2 * k, 0.1 * k
        if kind == "pounce":
            lift, pitch = 0.18, 0.25
        elif kind == "sweep":
            spin = -0.6 + 2 * math.pi * _ease(min(e.state_t / 0.35, 1.0))
        elif kind == "tail_lash":
            spin = 0.5 - 1.6 * _ease(min(e.state_t / 0.25, 1.0))  # the hindquarters whip round
        elif kind == "squeal":
            lift, pitch, stretch = 0.12, 1.0 + 0.1 * math.sin(t * 40), -0.1  # shrieking, the jaw shaking
    elif e.state == "hurt":
        pitch = 0.4
    return lift, pitch, stretch, spin


def _rat(r, e, t, k, fur, eyes_lit, extras=None, blaze=False, sores=()):
    """A rat `k` times a gutter rat's size, in a few bold shapes: a hunched body that rises to a high,
    bristling back, the head carried low and long before it, thin pale legs ending in claws, a bare
    tail, big naked ears, a jaw hung open on its fangs and one round, milky eye a side that catches the
    light while it lives (if `eyes_lit`). `sores` are raw wounds in its hide, (x, y, z, size) in the
    body's frame. Slain, it rolls onto its side and its legs stick out. `extras(r, k)` adds to the
    body, in its frame; `blaze` sets its eyes ablaze."""
    fall = death_fall(e, 0.6)
    running = e.state == "chase"
    gait = math.sin(t * (15 if running else 4)) * (0.6 if running else 0.15) * (1 - fall)
    lift, pitch, stretch, spin = _rat_pose(e, t)
    hide = hit_tint((240, 200, 190)) if e.flashing else fur
    dark = _dim(hide, 0.7)
    eye = RAT_EYE_LIT if eyes_lit and fall < 0.5 else RAT_EYE
    y0 = (0.15 + lift + 0.01 * abs(gait)) * (1 - fall) + 0.14 * fall  # on its side, haunches on the floor
    jaw = 0.25 + (0.35 if e.state in ("windup", "attack") else 0.1 * math.sin(t * 3) ** 2)
    with r.at(stretch * k, y0 * k, 0, ry=spin, rx=fall * math.pi / 2):
        r.part("sphere", -0.02 * k, 0.03 * k, 0, 0.5 * k, 0.27 * k, 0.27 * k, hide)  # the hunched body
        r.part("sphere", -0.14 * k, 0.03 * k, 0, 0.3 * k, 0.27 * k, 0.3 * k, dark)  # haunches
        for i in range(5):  # the bristling ridge of its back, highest over the hump
            x = (0.14 - i * 0.08) * k
            tall = (0.07 + 0.04 * math.sin(i / 4 * math.pi)) * k
            r.part("cube", x, 0.16 * k + tall / 2, 0, 0.05 * k, tall, 0.13 * k, dark, rz=0.5)
        for x, y, z, size in sores:  # raw, weeping wounds in its hide
            r.part("sphere", x * k, y * k, z * k, size * k, size * 0.6 * k, size * k, RAT_SORE)
            r.part("cube", x * k, y * k, z * k, size * 0.45 * k, size * 0.4 * k, size * 0.45 * k, RAT_FLESH)
        for i, (lx, lz) in enumerate(((0.14, 0.08), (0.14, -0.08), (-0.15, 0.1), (-0.15, -0.1))):
            a = gait * (1 if i in (0, 3) else -1)
            with r.at(lx * k, -0.04 * k, lz * k, rz=a):  # thin pale legs, toes splayed in claws
                r.part("cube", 0, -0.06 * k, 0, 0.035 * k, 0.13 * k, 0.035 * k, RAT_PINK)
                r.part("cube", 0.025 * k, -0.125 * k, 0, 0.07 * k, 0.015 * k, 0.05 * k, RAT_CLAW)
        sway = math.sin(t * 3) * 0.12 * (1 - fall)
        mid = (-0.42 * k, -0.06 * k, sway * 0.5 * k)
        _bar(r, (-0.27 * k, -0.01 * k, 0.0), mid, 0.035 * k, RAT_PINK)  # the bare tail, swishing behind
        _bar(r, mid, (-0.62 * k, -0.09 * k, sway * k), 0.022 * k, RAT_PINK)
        with r.at(0.22 * k, -0.01 * k, 0, rz=pitch - 0.15 + math.sin(t * 2.3) * 0.08):  # carried low
            r.part("sphere", 0.05 * k, 0, 0, 0.18 * k, 0.14 * k, 0.14 * k, hide)  # skull
            r.part("cube", 0.16 * k, -0.005 * k, 0, 0.14 * k, 0.07 * k, 0.08 * k, hide, rz=-0.12)  # muzzle
            r.part("cube", 0.235 * k, -0.01 * k, 0, 0.03 * k, 0.04 * k, 0.045 * k, RAT_NOSE)  # nose
            with r.at(0.06 * k, -0.04 * k, 0, rz=-jaw):  # the jaw, hung open
                r.part("cube", 0.07 * k, -0.01 * k, 0, 0.14 * k, 0.03 * k, 0.07 * k, RAT_GUM)
                r.part("cube", 0.13 * k, 0.025 * k, 0, 0.015 * k, 0.05 * k, 0.04 * k, RAT_TOOTH)  # incisors
            for side in (-1, 1):
                r.part("cube", 0.17 * k, -0.045 * k, side * 0.03 * k, 0.012 * k, 0.04 * k, 0.012 * k,
                       RAT_TOOTH)  # the upper fangs  # fmt: skip
                r.part("sphere", 0.1 * k, 0.03 * k, side * 0.06 * k, 0.045 * k, 0.045 * k, 0.03 * k, eye,
                       glow=eye is RAT_EYE_LIT)  # fmt: skip
                if blaze and eye is RAT_EYE_LIT:
                    r.part("cube", 0.115 * k, 0.03 * k, side * 0.065 * k, 0.05 * k, 0.03 * k, 0.04 * k,
                           (255, 220, 140), glow=True)  # fmt: skip
                r.part("sphere", 0.0, 0.09 * k, side * 0.065 * k, 0.03 * k, 0.11 * k, 0.09 * k,
                       RAT_EAR, rx=-side * 0.35)  # big naked ears  # fmt: skip
        if extras:
            extras(r, k)


def sewer_rat(r, e, t):
    """A gutter rat the size of a cat, dark and bristling, its eyes glinting pale in the dark."""
    _rat(r, e, t, 1.0, RAT_FUR, eyes_lit=True, sores=((-0.1, 0.1, 0.1, 0.08),))


def giant_rat(r, e, t):
    """A cistern rat as big as a hound and as mangy: raw sores on its flank and haunch, a bald patch
    on its hump and one ear torn off short."""

    def mange(r, k):
        r.part("sphere", 0.0, 0.15 * k, 0, 0.16 * k, 0.05 * k, 0.12 * k, MANGE)  # the bald patch
        r.part("cube", 0.23 * k, 0.07 * k, 0.065 * k, 0.04 * k, 0.03 * k, 0.04 * k, RAT_SORE)  # the torn ear

    _rat(r, e, t, 2.4, (70, 68, 70), eyes_lit=True, extras=mange,
         sores=((0.04, 0.05, 0.12, 0.1), (-0.17, 0.08, -0.12, 0.09), (0.25, 0.04, 0.05, 0.05)))  # fmt: skip


def rat_matron(r, e, t):
    """Mother Gnawl, the brood-mother of the sewers' rats: a rat swollen to the size of a cart-horse,
    her hide torn open in weeping sores, her belly hanging heavy, a rusted iron collar on her neck with
    its broken chain dragging. When she has called her litter her hackles rise in a mane and her eyes
    blaze."""
    rage = e.phase2 and e.alive
    fall = death_fall(e, 0.8)

    def brood(r, k):
        r.part("sphere", 0, -0.08 * k, 0, 0.36 * k, 0.12 * k, 0.21 * k, (120, 96, 92))  # the hanging belly
        if rage:
            for i in range(6):  # her hackles risen in a mane over the ridge
                x = (0.2 - i * 0.07) * k
                r.part("cube", x, 0.25 * k, 0, 0.03 * k, 0.12 * k, 0.15 * k, RAT_DARK, rz=0.6)
        with r.at(0.2 * k, 0.03 * k, 0):  # the collar and its broken chain
            r.part("cyl", 0, 0, 0, 0.07 * k, 0.18 * k, 0.18 * k, RUST, rz=math.pi / 2)
            link = (0.0, -0.08 * k, 0.0)
            for i in range(3):
                swing = math.sin(t * 2 + i) * 0.03 * k * (1 - fall)
                nxt = (link[0] - 0.06 * k, link[1] - 0.035 * k, link[2] + swing + 0.01 * k)
                _bar(r, link, nxt, 0.022 * k, _dim(IRON, 0.9 + 0.05 * (i % 2)))
                link = nxt

    sores = (
        (0.05, 0.06, 0.13, 0.1),
        (-0.2, 0.1, -0.12, 0.11),
        (-0.08, 0.17, 0.05, 0.08),
        (0.24, 0.05, -0.06, 0.05),
    )
    _rat(r, e, t, 4.4, (62, 60, 62), eyes_lit=True, extras=brood, blaze=rage, sores=sores)


# --- slimes ---------------------------------------------------------------------------------------


def _sludge(r, e, t, k, junk=True):
    """A crawling heap of sludge `k` times a sludge slime's size: a spreading foot, a quivering body
    flecked with scum, two milky eyes, bubbles welling and bursting on its skin and, in the big ones,
    the town's rubbish it has swallowed (a boot, a bottle, a rat's skull). Slain, it slumps into a
    spreading puddle."""
    squash = 1 + math.sin(t * (8 if e.state == "chase" else 3)) * 0.1
    if e.state == "windup":
        squash = 1.3
    if e.state == "attack":
        squash = 0.72
    fall = death_fall(e, 0.8)
    if e.state == "dead":
        squash = 1 + 1.3 * fall
    body = hit_tint((230, 220, 170)) if e.flashing else SLUDGE
    h = 0.8 / squash
    r.part("sphere", 0.04 * k, 0.12 * k, 0, 1.2 * squash * k, 0.24 * k, 1.2 * squash * k, SLUDGE_DARK)
    r.part("sphere", 0, 0.34 / squash * k, 0, 0.95 * squash * k, h * k, 0.95 * squash * k, body)
    r.part("sphere", -0.06 * k, 0.46 / squash * k, 0.08 * k, 0.58 * squash * k, h * 0.65 * k,
           0.58 * squash * k, _dim(body, 1.12))  # fmt: skip
    top = (0.34 / squash + h / 2) * k
    for i in range(4):  # scum floating on its skin
        a = i * 1.7 + 0.3
        rad = 0.32 * squash * k
        r.part("sphere", math.cos(a) * rad, top * (0.55 + 0.1 * (i % 2)), math.sin(a) * rad,
               0.22 * k, 0.04 * k, 0.16 * k, SLUDGE_SCUM, ry=a)  # fmt: skip
    for i in range(3):  # bubbles welling up and bursting
        u = (t * 0.7 + i / 3) % 1.0
        a = i * 2.1 + 0.5
        rad = 0.4 * squash * k * (1 - u * 0.6)
        size = (0.05 + 0.07 * math.sin(u * math.pi)) * k
        r.part("sphere", math.cos(a) * rad, (0.1 + (top / k - 0.1) * u) * k, math.sin(a) * rad,
               size, size, size, _dim(SLUDGE_SCUM, 1.1))  # fmt: skip
    for side in (-1, 1):
        r.part("sphere", 0.36 * squash * k, 0.42 / squash * k, side * 0.15 * k, 0.09 * k, 0.11 * k, 0.09 * k,
               SLUDGE_EYE if e.alive else _dim(SLUDGE_EYE, 0.5))  # fmt: skip
        r.part("cube", 0.4 * squash * k, 0.42 / squash * k, side * 0.15 * k, 0.02 * k, 0.04 * k, 0.03 * k,
               HOLLOW)  # fmt: skip
    if not junk:
        return
    sink = 0.15 * fall
    with r.at(-0.2 * squash * k, (0.32 / squash - sink) * k, 0.3 * k, rz=0.9, rx=0.4):  # a boot
        r.part("cube", 0, 0.1 * k, 0, 0.09 * k, 0.22 * k, 0.1 * k, (58, 42, 30))
        r.part("cube", 0.06 * k, 0, 0, 0.2 * k, 0.07 * k, 0.1 * k, (58, 42, 30))
    with r.at(0.12 * k, (top / k - 0.14 - sink) * k, -0.25 * k, rz=-0.6, rx=0.5):  # a green bottle
        r.part("cyl", 0, 0, 0, 0.08 * k, 0.2 * k, 0.08 * k, (60, 110, 70))
        r.part("cyl", 0, 0.14 * k, 0, 0.035 * k, 0.08 * k, 0.035 * k, (60, 110, 70))
    r.part("sphere", -0.15 * k, (top / k - 0.08 - sink) * k, -0.05 * k, 0.12 * k, 0.09 * k, 0.1 * k,
           (200, 190, 160))  # a rat's skull, picked clean  # fmt: skip


def sludge_slime(r, e, t):
    _sludge(r, e, t, 1.0)


def slimelet(r, e, t):
    """A gobbet of sludge burst from a slain slime, crawling on."""
    _sludge(r, e, t, 0.5, junk=False)


# --- the drowned ----------------------------------------------------------------------------------


def _drowned_body(r, e, t, skin, claw):
    """A drowned townsman standing, feet at the origin: bloated grey-green flesh in sodden rags, lank
    hair plastered over a swollen face with hollow eyes and a slack mouth, weed and sludge hanging off
    him. `claw` (0..1) raises the arms to claw down."""
    dark = _dim(skin, 0.72)
    sway = math.sin(t * 1.6) * 0.06
    for side in (-1, 1):  # legs, knees bent under the weight
        with r.at(0, 0.88, side * 0.14, rz=0.15 + sway * side):
            r.part("cube", 0, -0.22, 0, 0.16, 0.46, 0.16, DROWNED_RAG)  # sodden breeches
            with r.at(0, -0.44, 0, rz=-0.3):
                r.part("cube", 0, -0.2, 0, 0.13, 0.42, 0.13, dark)
                r.part("cube", 0.06, -0.42, 0, 0.24, 0.07, 0.12, skin)  # a bare, swollen foot
    r.part("sphere", 0, 0.98, 0, 0.42, 0.34, 0.44, DROWNED_RAG)  # hips in rags
    with r.at(0.08, 1.0, 0, rz=-0.35 - sway):  # hunched over
        r.part("sphere", 0, 0.32, 0, 0.5, 0.62, 0.56, skin)  # the bloated trunk
        r.part("sphere", 0.12, 0.2, 0, 0.32, 0.36, 0.44, _dim(skin, 1.1))  # its swollen belly
        r.part("cube", -0.05, 0.42, 0, 0.5, 0.5, 0.58, DROWNED_RAG)  # the rag of a shirt
        r.part("cube", 0.2, 0.2, 0.1, 0.06, 0.4, 0.12, DROWNED_RAG, rx=0.3)  # its torn front
        for i, (y, z) in enumerate(((0.55, 0.22), (0.3, -0.25), (0.15, 0.2))):  # weed hanging off him
            r.part("cube", 0.05, y - 0.12, z, 0.04, 0.3 + 0.1 * i, 0.05, WEED, rx=0.1 * i)
        for side in (-1, 1):  # arms, raised to claw down
            lift = 0.3 + claw * 2.4
            with r.at(0, 0.6, side * 0.32, rz=lift, rx=side * 0.2):
                r.part("cube", 0, -0.18, 0, 0.13, 0.38, 0.13, skin)
                with r.at(0, -0.37, 0, rz=0.5 - 0.3 * claw):
                    r.part("cube", 0, -0.17, 0, 0.11, 0.36, 0.11, dark)
                    with r.at(0, -0.36, 0):
                        hand(r, _dim(skin, 0.9), 0.13, curl=0.6)
        with r.at(0.06, 0.72, 0, rz=0.3 + sway):
            r.part("cube", 0, 0.05, 0, 0.12, 0.12, 0.12, dark)  # neck
            r.part("sphere", 0.04, 0.22, 0, 0.32, 0.34, 0.3, skin)  # the swollen head
            r.part("cube", -0.04, 0.32, 0, 0.32, 0.12, 0.33, DROWNED_HAIR)  # lank hair plastered down
            for z in (-0.12, 0.0, 0.12):
                r.part("cube", -0.06, 0.12, z, 0.24, 0.32, 0.04, DROWNED_HAIR)  # hanging in strands
            for side in (-1, 1):
                r.part("cube", 0.17, 0.25, side * 0.07, 0.04, 0.06, 0.07, HOLLOW)  # hollow eyes
            r.part("cube", 0.18, 0.13, 0, 0.04, 0.07, 0.1, (40, 30, 30))  # the slack mouth


def drowned(r, e, t):
    """A drowned wretch: lurking, it lies face down in the sludge like a floating corpse; woken, it
    heaves itself up, bloated and dripping, and claws at you. Slain, it topples back into the muck."""
    skin = hit_tint((236, 236, 210)) if e.flashing else DROWNED_SKIN
    if e.state == "idle":  # lying face down, rising and falling a little on the sludge
        bob = math.sin(t * 1.3) * 0.02
        with r.at(-0.85, 0.36 + bob, 0, rz=-math.pi / 2):
            _drowned_body(r, e, t, skin, 0.0)
        for i in range(3):  # ripples round the body
            u = (t * 0.4 + i / 3) % 1.0
            r.part(
                "cube", -0.3 + 0.4 * i, 0.03, 0, 0.3 + 0.6 * u, 0.01, 0.5 + 0.6 * u, _dim(SLUDGE_SCUM, 1 - u)
            )
        return
    fall = death_fall(e, 0.8)
    claw = max(0.0, -strike_angle(e) / 2.2) * (1 - fall)
    lean = (-0.25 if e.state == "hurt" else 0.0) + 1.4 * fall
    with r.at(-0.3 * fall, 0.1 * fall, 0, rz=lean):
        _drowned_body(r, e, t, skin, claw)
    for i in range(2):  # sludge dripping off him
        u = (t * 0.9 + i / 2) % 1.0
        r.part("cube", 0.1, 1.2 * (1 - u) * (1 - fall) + 0.05, (i - 0.5) * 0.4, 0.04, 0.08, 0.04, SLUDGE)


# --- the bilge leech ------------------------------------------------------------------------------

LEECH_SEGMENTS = 9


def _leech_spine(e, t):
    """(x, y) of each body segment, mouth first: flat in the sludge while it lurks, its front reared
    up once woken, drawn back on the windup and lunging out on the attack."""
    fall = death_fall(e, 0.7)
    rear = 0.0 if e.state in ("idle", "dead") else 0.55
    reach = 0.0
    if e.state == "windup":
        k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
        rear, reach = 0.55 + 0.25 * k, -0.35 * k
    elif e.state == "attack":
        rear, reach = 0.3, 0.9 * _ease(min(e.state_t / 0.15, 1.0))
    rear *= 1 - fall
    out = []
    for i in range(LEECH_SEGMENTS):
        u = 1 - i / (LEECH_SEGMENTS - 1)  # 1 at the mouth, 0 at the tail
        wave = math.sin(t * 4 - i * 0.8) * 0.05 * (1 - fall)
        x = 0.7 - i * 0.2 + reach * u * u
        y = 0.08 + rear * u * u + max(wave, 0)
        out.append((x, y, math.sin(t * 2 - i * 0.6) * 0.08 * (1 - fall) * (1 - u)))
    return out


def bilge_leech(r, e, t):
    """A leech as long as a man: a ribbed, slick brown body striped in dull yellow, a sucker of a mouth
    ringed with teeth. It lies flat in the sludge until it rears to lunge."""
    hide = hit_tint((220, 190, 170)) if e.flashing else LEECH
    spine = _leech_spine(e, t)
    for i, (x, y, z) in enumerate(spine):
        w = 0.34 - 0.02 * abs(i - 3)
        r.part("sphere", x, y, z, 0.26, 0.17, w, hide if i % 2 else _dim(hide, 1.12))
        r.part("cube", x, y + 0.075, z, 0.14, 0.02, 0.05, LEECH_STRIPE)  # its dull stripe
        if i < LEECH_SEGMENTS - 1:
            nx, ny, nz = spine[i + 1]
            _bar(r, (x, y - 0.05, z), (nx, ny - 0.05, nz), 0.12, LEECH_BELLY)
    x, y, z = spine[0]
    pitch = math.atan2(y - spine[1][1], x - spine[1][0])
    with r.at(x + 0.12, y, z, rz=pitch):
        r.part("cyl", 0, 0, 0, 0.26, 0.06, 0.26, LEECH_MOUTH, rz=math.pi / 2)  # the sucker
        r.part("cyl", 0.02, 0, 0, 0.14, 0.04, 0.14, HOLLOW, rz=math.pi / 2)
        for i in range(6):  # its ring of teeth
            a = i * math.pi / 3
            r.part("cone", 0.03, math.cos(a) * 0.09, math.sin(a) * 0.09, 0.03, 0.06, 0.03, (214, 200, 160),
                   rz=-math.pi / 2)  # fmt: skip


# --- the Sump Maw ---------------------------------------------------------------------------------


def _maw_pose(e):
    """(gape, lean, twist, rear) of the Maw through its moves: `gape` opens its jaws from shut (0) to
    wide (1), `lean` pitches its head forward (+) or back (-), `twist` turns its whole bulk, `rear`
    stretches it tall (+) or squashes it flat (-). A slam rears it up and crashes it down, a sweep
    swings it round and its tail with it, bile and the gulp throw its jaws wide, the undertow sinks it
    into itself, a shed swells it fit to burst."""
    kind = e.attack_kind
    if kind == "slam":
        return _swing_pose(e, 0.3, 0.6, 0.1), _swing_pose(e, 0, -0.35, 0.6), 0.0, _swing_pose(e, 0, 0.3, -0.3)
    if kind == "sweep":
        return 0.3, 0.1, _swing_pose(e, 0.0, -0.9, 1.4), 0.0
    if kind == "bile":
        return _swing_pose(e, 0.35, 0.9, 1.0), _swing_pose(e, 0, -0.25, 0.25), 0.0, 0.1
    if kind == "undertow":
        return 0.1, 0.2, 0.0, _swing_pose(e, 0, -0.35, -0.2)
    if kind == "gulp":
        return (
            _swing_pose(e, 0.35, 1.0, 1.0),
            _swing_pose(e, 0, -0.4, 0.5),
            0.0,
            _swing_pose(e, 0, 0.25, -0.15),
        )
    if kind == "shed":
        return 0.2, 0.0, 0.0, _swing_pose(e, 0, -0.15, 0.1)
    return _swing_pose(e, 0.45, 0.8, 0.5), _swing_pose(e, 0, -0.2, 0.45), 0.0, 0.0


def _skull(r, x, y, z, size, eyes=None, ry=0.0):
    """A skull stuck in the sludge, facing +X in its own turn `ry`: dark sockets, or `eyes` (a colour)
    kindled in them."""
    with r.at(x, y, z, ry=ry, s=size):
        r.part("sphere", 0, 0, 0, 1.0, 0.9, 0.9, MAW_BONE)
        r.part("cube", 0.3, -0.38, 0, 0.4, 0.22, 0.56, _dim(MAW_BONE, 0.85))  # its jaw
        for side in (-1, 1):
            r.part("cube", 0.4, 0.05, side * 0.2, 0.2, 0.24, 0.24, eyes or HOLLOW, glow=eyes is not None)


def sump_maw(r, e, t):
    """The Sump Maw: the Sump itself grown hungry, a wave of black-blue sludge as tall as a house that
    rears from a spreading pool and crests forward into a vast maw: a ring of black fangs round a gullet
    glowing sickly green. Its crest is crusted with the skulls of the drowned, and bones, skulls and
    clods of the drains' dirt stick out of its sides; a tail of it curls up behind. It swells and
    bubbles as it crawls; raging, the eyes of the skulls kindle green. Slain, it slumps into a black,
    still pool, the skulls lying in it."""
    fall = death_fall(e, 1.2)
    lit = e.alive
    rage = e.phase2 and lit
    skin = hit_tint((200, 220, 240)) if e.flashing else MAW_SLIME
    glow_rgb = MAW_GLOW if lit else MAW_GLOW_COLD
    eyes = glow_rgb if rage else None
    gape, lean, twist, rear = _maw_pose(e)
    gape, lean = _mix(gape, 0.05, fall), _mix(lean, 0.0, fall)
    quiver = math.sin(t * (6 if e.state == "chase" else 2.2)) * 0.05
    if e.attack_kind == "shed" and e.state == "windup":
        quiver += 0.06 * math.sin(t * 30)  # shuddering, fit to burst
    tall = (1 + rear + quiver) * (1 - 0.8 * fall)
    wide = (1 - 0.4 * rear - quiver) * (1 + 0.4 * fall)
    spew = e.attack_kind in ("bile", "gulp") and e.state in ("windup", "attack") and lit
    # The spreading pool it rises from, and the lumps of it heaped round its foot.
    r.part("sphere", 0.2, 0.1, 0, 4.2 * wide, 0.2, 3.6 * wide, MAW_DARK)
    for i in range(5):  # ripples running out across the pool
        a = i * 1.26 + 0.4
        r.part("sphere", math.cos(a) * 1.8 * wide, 0.06, math.sin(a) * 1.6 * wide, 0.7, 0.08, 0.3,
               _dim(MAW_DARK, 1.3), ry=-a)  # fmt: skip
    for x, z, s in ((-1.1, 1.0, 1.3), (-1.2, -0.9, 1.2), (0.9, 1.1, 1.0), (0.8, -1.1, 1.1), (-1.8, 0.1, 1.0)):
        r.part("sphere", x * wide, 0.42 * s * tall, z * wide, s * wide, 0.85 * s * tall, s * wide,
               _dim(skin, 0.9 + 0.08 * s))  # fmt: skip
    # Its tail, curling up behind it, swung round with a sweep.
    with r.at(-1.9 * wide, 0, -0.8 * wide, ry=-0.5 + twist * 0.6):
        for i in range(5):
            k = i / 4
            size = (0.9 - 0.6 * k) * wide
            high = size * 1.1 * min(tall * 1.5, 1.0)  # flattening with the rest of it, slain
            r.part("sphere", -0.45 * i + 0.2 * k * k, max((0.6 + 1.4 * k * k) * tall, high / 2), 0, size, high,
                   size, _dim(skin, 0.95 + 0.1 * k))  # fmt: skip
        r.part(
            "cone", -1.45, max(2.25 * tall, 0.3), 0, 0.22, 0.6 * tall, 0.22, _dim(skin, 1.1), rz=0.9
        )  # its tip
    with r.at(0, 0, 0, ry=twist):
        # The wave of it, rising and leaning back, then cresting forward into the head.
        r.part("sphere", -0.5 * wide, 1.0 * tall, 0, 2.6 * wide, 2.0 * tall, 2.4 * wide, skin)
        r.part("sphere", -0.4 * wide, 1.85 * tall, 0, 2.0 * wide, 1.6 * tall, 1.9 * wide, _dim(skin, 1.06))
        r.part("sphere", -0.1 * wide, 2.5 * tall, 0, 1.6 * wide, 1.2 * tall, 1.6 * wide, _dim(skin, 1.1))
        for i, (a, y) in enumerate(((0.6, 0.7), (1.9, 1.1), (3.0, 0.6), (4.2, 1.3), (5.4, 0.9))):
            d = 1.2 * wide  # bubbles welling up its sides
            u = (t * (0.9 if rage else 0.5) + i / 5) % 1.0
            b = 0.1 + 0.18 * math.sin(u * math.pi)
            r.part("sphere", -0.4 + math.cos(a) * d, (y + 1.2 * u) * tall, math.sin(a) * d, b, b, b,
                   _dim(skin, 1.25))  # fmt: skip
        # What it swallowed, stuck in its sides: skulls, bones and clods of the drains' dirt.
        for a, y, size in ((0.9, 0.5, 0.34), (2.2, 0.9, 0.3), (-0.8, 0.6, 0.36), (-2.4, 1.0, 0.28)):
            y = max(y * tall, size * 0.6)
            _skull(r, -0.4 + math.cos(a) * 1.25 * wide, y, math.sin(a) * 1.15 * wide, size, eyes, -a)
        for a, y, tilt in ((1.4, 1.3, 0.7), (-1.6, 0.9, -0.5), (2.8, 1.5, 1.1), (-2.9, 0.4, 0.3)):
            r.part("cube", -0.4 + math.cos(a) * 1.3 * wide, max(y * tall, 0.4), math.sin(a) * 1.25 * wide, 0.1, 0.1,
                   0.7, MAW_BONE, ry=-a + tilt, rx=tilt)  # fmt: skip
        for a, y, size in (
            (0.3, 0.3, 0.4),
            (1.2, 0.8, 0.3),
            (-1.2, 1.4, 0.34),
            (2.6, 0.3, 0.45),
            (-2.2, 0.3, 0.4),
        ):
            r.part("sphere", -0.4 + math.cos(a) * 1.3 * wide, max(y * tall, size * 0.35), math.sin(a) * 1.2 * wide, size,
                   size * 0.7, size, MAW_DIRT if size > 0.35 else MAW_STONE)  # fmt: skip
        # The head: its lower jaw the lip of the wave, its upper jaw the crest, hinged at the back.
        with r.at(0.55, 2.6 * tall, 0, rz=-lean, s=_mix(1.35, 0.45, fall)):
            r.part("sphere", 0.7, -0.6, 0, 2.0, 0.75, 1.8, skin)  # the lower jaw
            r.part("sphere", 0.8, -0.28, 0, 1.6, 0.2, 1.4, glow_rgb, glow=lit)  # the glowing gullet floor
            r.part("sphere", 0.15, -0.1, 0, 0.7, 0.6, 0.9, MAW_GULLET)  # the throat
            for i in range(7):  # the lower fangs, pointing up
                a = -1.35 + i * 0.45
                r.part("cone", 0.8 + math.cos(a) * 0.82, -0.12, math.sin(a) * 0.72, 0.16, 0.38, 0.16,
                       MAW_FANG, rz=-0.15)  # fmt: skip
            if spew:  # a gout of glowing sludge welling up its gullet
                r.part("sphere", 0.7, -0.15, 0, 0.7, 0.45, 0.6, glow_rgb, glow=True)
            with r.at(-0.2, -0.2, 0, rz=0.12 + gape * 0.85):
                r.part("sphere", 0.95, 0.45, 0, 2.1, 0.75, 1.75, _dim(skin, 1.08))  # the upper jaw
                r.part("sphere", 0.3, 0.8, 0, 1.6, 0.8, 1.5, _dim(skin, 1.12))  # the crest
                r.part("sphere", 0.95, 0.12, 0, 1.7, 0.12, 1.4, _dim(glow_rgb, 0.8), glow=lit)  # its roof
                for i in range(8):  # the upper fangs, hanging down
                    a = -1.4 + i * 0.4
                    r.part("cone", 0.95 + math.cos(a) * 0.9, -0.12, math.sin(a) * 0.76, 0.18, 0.5, 0.18,
                           MAW_FANG, rz=math.pi + 0.15)  # fmt: skip
                # The drowned's skulls crusting its crest.
                for x, y, z, size in (
                    (0.2, 1.2, 0.0, 0.34), (0.6, 1.05, 0.45, 0.3), (0.6, 1.05, -0.45, 0.3),
                    (-0.2, 1.1, 0.4, 0.28), (-0.2, 1.1, -0.4, 0.3), (1.0, 0.85, 0.15, 0.26),
                    (1.0, 0.85, -0.25, 0.24), (-0.5, 0.9, 0.0, 0.3),
                ):  # fmt: skip
                    _skull(r, x, y + 0.1, z, size * 1.25, eyes, ry=z * 0.6)
                for x, z, tilt in ((0.0, 0.6, 0.6), (-0.4, -0.55, -0.8), (0.8, 0.0, 0.3)):
                    r.part("cube", x, 1.2, z, 0.08, 0.5, 0.08, MAW_BONE, rx=tilt, rz=-0.4)  # bones in it
        for i in range(3):  # sludge drooling off its lip
            u = (t * 0.8 + i / 3) % 1.0
            r.part("cube", 1.5 * wide, (0.5 + 1.4 * (1 - u)) * tall, (i - 1) * 0.5, 0.08, 0.2, 0.08, skin)


def drowned_hands(r, glow, rise, t):
    """The Maw's undertow, where it will burst (`hazards.Eruption` style "drowned"): first the floor
    wells with bubbling sludge (`glow` 0..1), then grey-green arms of the drowned grope up out of it
    (`rise` 0..1) and sink again."""
    if glow > 0:
        r.part("cyl", 0, 0.015, 0, 1.4 * glow, 0.02, 1.4 * glow, SLUDGE_DARK)  # the welling sludge
        for i in range(5):
            a = i * 1.26 + t * 0.4
            pop = 0.5 + 0.5 * math.sin(t * 7 + i * 1.7)
            b = 0.08 + 0.1 * glow * pop
            r.part(
                "sphere", math.cos(a) * 0.55 * glow, b / 2, math.sin(a) * 0.55 * glow, b, b, b, SLUDGE_SCUM
            )
    if rise <= 0:
        return
    for i in range(3):
        a = i * 2.1 + 0.3
        x, z = math.cos(a) * 0.3, math.sin(a) * 0.3
        length = (0.8 + 0.3 * i) * rise
        with r.at(x, 0, z, rx=math.sin(a) * 0.3, rz=-math.cos(a) * 0.3):
            r.part("cube", 0, length / 2, 0, 0.14, length, 0.14, DROWNED_DARK)
            r.part("sphere", 0, 0.05, 0, 0.22, 0.12, 0.22, SLUDGE)  # sludge round the wrist
            with r.at(0, length, 0, rz=math.pi):
                hand(r, DROWNED_SKIN, 0.22, curl=1.2 - 0.8 * rise + 0.15 * math.sin(t * 11 + i))


def squeal_ring(r, k, radius):
    """Mother Gnawl's squeal running out through the air: two pale rings at head height, widening and
    thinning as they go."""
    for ring, lag in ((0, 0.0), (1, 0.2)):
        q = min(max(k - lag, 0.0) / (1 - lag), 1.0)
        if q <= 0:
            continue
        d = radius * q
        size = 0.18 * (1 - q) + 0.04
        for i in range(12):
            a = i * math.pi / 6 + ring * 0.26
            r.part("cube", math.cos(a) * d, 1.0 + 0.3 * ring, math.sin(a) * d, size, size * 2.5, size,
                   (214, 206, 196), ry=-a, tex="mist")  # fmt: skip


def swarm_rat(r, t):
    """One of Mother Gnawl's litter scurrying along the floor at you, nose first (+X), its tail
    whipping behind."""
    bob = abs(math.sin(t * 24)) * 0.04
    with r.at(0, -0.18 + bob, 0):
        r.part("sphere", 0, 0, 0, 0.36, 0.17, 0.2, RAT_FUR)
        r.part("sphere", 0.17, 0.02, 0, 0.16, 0.12, 0.12, RAT_FUR)  # head
        r.part("cube", 0.26, 0.0, 0, 0.08, 0.05, 0.05, RAT_PINK)  # snout
        for side in (-1, 1):
            r.part("cube", 0.2, 0.05, side * 0.04, 0.025, 0.025, 0.02, RAT_EYE_LIT, glow=True)
        _bar(r, (-0.17, 0, 0), (-0.42, -0.04, math.sin(t * 18) * 0.1), 0.025, RAT_PINK)


# --- the ways down from the streets ---------------------------------------------------------------

GRATE_STONE = (110, 104, 96)
GRATE_IRON = (50, 50, 54)


def sewer_grate(r, t):
    """A way down into the sewers from the street: a kerb of dressed stones round a dark square shaft,
    its iron grate lifted and propped open on its hinges, the top of an iron ladder showing above the
    rim, a lantern hook beside it, and the sewers' breath curling up out of the dark."""
    r.part("cube", 0, 0.02, 0, 1.2, 0.03, 1.2, PASSAGE_DARK)  # the black of the shaft
    for i in range(4):  # the kerb: four long stones and four corner blocks
        a = i * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        r.part("cube", c * 0.72, 0.1, s * 0.72, 0.26, 0.2, 1.2, GRATE_STONE, ry=-a)
        r.part("cube", (c - s) * 0.72, 0.13, (s + c) * 0.72, 0.3, 0.26, 0.3, _dim(GRATE_STONE, 0.85))
        r.part("cube", c * 0.6, 0.21, s * 0.6, 0.04, 0.02, 1.0, _dim(GRATE_STONE, 0.6), ry=-a)  # its worn lip
    with r.at(-0.62, 0.22, 0, rz=1.35):  # the grate, swung up on its hinges and propped open
        r.part("cube", 0.6, 0, 0, 1.2, 0.05, 0.06, GRATE_IRON)
        r.part("cube", 0.6, 0, 0, 1.2, 0.05, 0.06, GRATE_IRON, ry=math.pi / 2)
        for z in (-0.55, 0.55):
            r.part("cube", 0.6, 0, z, 1.2, 0.06, 0.06, GRATE_IRON)
        for x in (0.05, 1.15):
            r.part("cube", x, 0, 0, 0.06, 0.06, 1.16, GRATE_IRON)
        for k in range(4):
            r.part("cube", 0.25 + k * 0.23, 0, 0, 0.04, 0.04, 1.1, _dim(GRATE_IRON, 1.2))
    for z in (-0.3, 0.3):  # the ladder's top, poking above the rim
        r.part("cube", 0.35, 0.35, z, 0.06, 0.7, 0.06, RUST)
        r.part("cube", 0.35, 0.72, z, 0.12, 0.04, 0.06, RUST, rz=-0.6)  # curled over the rim
    for y in (0.15, 0.45):
        r.part("cube", 0.35, y, 0, 0.04, 0.04, 0.6, RUST)
    with r.at(0.95, 0, 0.7):  # a hooked post for a lantern
        r.part("cube", 0, 0.6, 0, 0.08, 1.2, 0.08, GRATE_IRON)
        r.part("cube", -0.1, 1.18, 0, 0.24, 0.04, 0.04, GRATE_IRON)
        r.part("cube", -0.2, 1.12, 0, 0.03, 0.1, 0.03, GRATE_IRON)
    for i in range(4):  # the sewers' breath, curling up
        u = (t * 0.3 + i / 4) % 1.0
        s = 0.18 + 0.3 * u
        r.part("cube", math.sin(t * 0.7 + i * 1.9) * 0.2, 0.1 + u * 1.6, math.cos(i * 2.3) * 0.2,
               s, s * 0.5, s, (104, 112, 96), tex="mist")  # fmt: skip


def sewer_ladder(r, t, height=3.4, back=0.0):
    """The way back up to the street: an iron ladder bolted to the brick from the floor to a square
    shaft in the vault, a faint shaft of daylight falling down it, drips glinting in the light and a
    puddle at its foot. `back` sets it that far back toward a wall behind it (-X)."""
    with r.at(-back, 0, 0):
        _ladder(r, t, height)


def _ladder(r, t, height):
    for z in (-0.28, 0.28):
        r.part("cube", 0, height / 2, z, 0.07, height, 0.07, RUST)  # the rails
        for y in (0.3, height - 0.4):
            r.part("cube", -0.25, y, z, 0.5, 0.05, 0.05, GRATE_IRON)  # bolted brackets
    rungs = int(height / 0.32)
    for k in range(rungs):
        r.part("cube", 0, 0.25 + k * 0.32, 0, 0.05, 0.05, 0.56, _dim(RUST, 1.1))
    for i in range(4):  # the shaft's collar in the vault
        a = i * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        r.part("cube", c * 0.62, height - 0.08, s * 0.62, 0.18, 0.16, 1.4, GRATE_STONE, ry=-a)
    r.part("cube", 0, height - 0.02, 0, 1.1, 0.03, 1.1, (150, 156, 170), glow=True)  # daylight up the shaft
    r.part(
        "cube", 0.1, height * 0.6, 0, 0.5, height * 0.8, 0.5, (58, 64, 72), tex="mist", glow=True
    )  # its fall
    r.part("cube", 0.2, 0.012, 0, 1.2, 0.02, 1.0, (70, 80, 72))  # the puddle at its foot
    for k in range(4):  # drips falling through the light
        u = (t * 0.7 + k / 4) % 1.0
        r.part("cube", 0.25 + 0.1 * math.sin(k * 2.1), height - 0.1 - u * (height - 0.2), (k - 1.5) * 0.15,
               0.025, 0.06, 0.025, (190, 200, 210), glow=True)  # fmt: skip


# --- the sewers' dressing -------------------------------------------------------------------------


def drain_pipe(r, t, seed):
    """A clay drain pipe's mouth jutting from the wall behind (-X), banded in iron, a trickle of sludge
    pouring out of it into a spreading splash on the floor."""
    y = 1.1 + (seed % 3) * 0.25
    r.part("cyl", -0.82, y, 0, 0.5, 0.4, 0.5, (120, 82, 60), rz=math.pi / 2)
    r.part("cyl", -0.6, y, 0, 0.56, 0.06, 0.56, GRATE_IRON, rz=math.pi / 2)  # its band
    r.part("cyl", -0.6, y, 0, 0.36, 0.08, 0.36, HOLLOW, rz=math.pi / 2)  # the dark inside
    for k in range(3):  # the trickle, falling and spattering
        u = (t * 1.2 + k / 3) % 1.0
        r.part("cube", -0.5 + 0.12 * u, y - 0.1 - u * (y - 0.1), 0, 0.09, 0.3, 0.09, SLUDGE)
    r.part("sphere", -0.4, 0.02, 0, 0.7, 0.04, 0.8, SLUDGE_DARK)
    r.part("cube", -0.58, y - 0.24, 0, 0.04, 0.1, 0.14, SLUDGE_SCUM)  # the slime under its lip


def sluice_wheel(r, seed):
    """The handwheel of a sluice gate on the wall behind (-X): an iron wheel on a threaded spindle that
    climbs to the gearbox above, all on a backing of old oak."""
    r.part("cube", -0.93, 1.6, 0, 0.1, 2.4, 1.1, OLD_WOOD, tex="wood_plank")  # the backboard
    r.part("cube", -0.86, 2.75, 0, 0.3, 0.4, 0.5, IRON)  # the gearbox
    r.part("cube", -0.7, 2.75, 0, 0.06, 0.3, 0.3, RUST)  # its toothed wheel showing
    r.part("cyl", -0.7, 1.75, 0, 0.08, 1.9, 0.08, _dim(IRON, 1.2))  # the threaded spindle
    for k in range(6):
        r.part("cyl", -0.7, 1.2 + k * 0.18, 0, 0.11, 0.03, 0.11, IRON)  # its thread
    with r.at(-0.62, 1.35, 0):  # the wheel, standing out on its spindle
        r.part("cyl", 0, 0, 0, 0.16, 0.12, 0.16, IRON, rz=math.pi / 2)  # hub
        for i in range(8):
            a = i * math.pi / 4 + seed * 0.3
            r.part("cube", 0, math.cos(a) * 0.42, math.sin(a) * 0.42, 0.06, 0.06, 0.34, RUST, rx=-a)  # rim
        for i in range(4):
            a = i * math.pi / 4 + seed * 0.3
            r.part("cube", 0, 0, 0, 0.04, 0.04, 0.84, IRON, rx=-a)  # spokes
    r.part("cube", -0.84, 0.3, 0, 0.2, 0.6, 0.9, IRON)  # the gate's housing at the floor


def outfall_grate(r, seed):
    """The great grate where the sewers pour out into the sea, in the wall behind (-X): a round-headed
    arch of brick, black beyond, barred with heavy iron, the bars streaked with rust and weed."""
    r.part("cube", -0.98, 1.6, 0, 0.04, 3.0, 1.9, PASSAGE_DARK)
    for side in (-1, 1):
        r.part("cube", -0.88, 1.3, side * 1.05, 0.24, 2.6, 0.3, BRICK, tex="sewer_brick")  # jambs
    for i in range(7):  # the round head, in voussoirs
        a = math.pi * i / 6
        r.part("cube", -0.88, 2.6 + math.sin(a) * 0.9, math.cos(a) * 1.05, 0.26, 0.3, 0.36, _dim(BRICK, 1.1),
               rx=a - math.pi / 2)  # fmt: skip
    for k in range(7):
        z = -0.84 + k * 0.28
        top = 2.6 + math.sqrt(max(0.0, 0.81 - (z * 0.86) ** 2))
        r.part("cube", -0.86, top / 2, z, 0.08, top, 0.08, RUST if k % 2 else GRATE_IRON)
    for y in (0.6, 1.5, 2.4):
        r.part("cube", -0.85, y, 0, 0.1, 0.1, 1.9, GRATE_IRON)
    for z in (-0.6, 0.15, 0.5):  # weed caught on the bars
        r.part("cube", -0.8, 0.5 + (seed % 3) * 0.2, z, 0.04, 0.6, 0.12, WEED)


def rat_nest(r, seed):
    """A rat's nest heaped on the floor: rags and straw dragged down from the streets, gnawed bones,
    tufts of shed fur."""
    rags = ((96, 84, 62), (82, 60, 56), (70, 76, 66), (110, 98, 80))
    for i in range(7):
        a = i * 0.9 + seed
        d = 0.15 + 0.12 * (i % 3)
        r.part("sphere", math.cos(a) * d * 2, 0.08 + 0.03 * (i % 2), math.sin(a) * d * 2, 0.7, 0.18, 0.5,
               rags[i % 4], ry=a)  # fmt: skip
    for i in range(6):  # straw
        a = i * 1.1 + seed * 0.5
        r.part("cube", math.cos(a) * 0.4, 0.17, math.sin(a) * 0.4, 0.5, 0.02, 0.03, (170, 150, 90), ry=a)
    for i in range(4):  # gnawed bones
        a = i * 1.6 + seed * 0.3
        x, z = math.cos(a) * 0.55, math.sin(a) * 0.55
        _bar(r, (x, 0.12, z), (x + math.cos(a + 1) * 0.35, 0.1, z + math.sin(a + 1) * 0.35), 0.05,
             (206, 196, 170))  # fmt: skip
    for i in range(3):  # tufts of fur
        a = i * 2.2 + seed
        r.part("sphere", math.cos(a) * 0.3, 0.22, math.sin(a) * 0.3, 0.16, 0.08, 0.14, RAT_FUR)


INKCAP = (196, 192, 180)  # pale, scaly grey-white
INKCAP_DARK = (150, 144, 134)
INK = (24, 22, 26)  # the black the old caps melt into
INKCAP_STEM = (214, 208, 194)


def inkcaps(r, seed):
    """A clump of inkcaps sprouting from the damp at the foot of the brick: tall pale bells on slender
    stems, the old ones blackening and melting into ink at their rims, one already collapsed into a
    black puddle. They don't glow."""
    count = 4 + seed % 3
    for k in range(count):
        a = k * 2.3 + seed * 0.7
        d = 0.12 + (k * 5 + seed) % 4 * 0.1
        x, z = math.cos(a) * d, math.sin(a) * d
        h = 0.22 + (k * 7 + seed) % 4 * 0.1  # stem
        lean = ((k * 3 + seed) % 5 - 2) * 0.06
        old = (k + seed) % 3 == 0  # its rim spread and running black
        with r.at(x, 0, z, rx=lean, rz=-lean):
            r.part("cyl", 0, h / 2, 0, 0.045, h, 0.045, INKCAP_STEM)
            bell = 0.2 + (k + seed) % 3 * 0.035
            tall = bell * 1.6
            r.part("cone", 0, h + tall * 0.3, 0, bell * (1.3 if old else 1.0), tall, bell, INKCAP)
            crown = bell * 0.55  # its darker, scaly crown
            r.part("sphere", 0, h + tall * 0.75, 0, crown, bell * 0.4, crown, INKCAP_DARK)
            if old:
                r.part("cyl", 0, h - tall * 0.2, 0, bell * 1.4, 0.04, bell * 1.4, INK)  # the melting rim
                for i in range(3):  # drips of ink hanging from it
                    b = i * 2.1 + seed
                    r.part("cube", math.cos(b) * bell * 0.6, h - tall * 0.2 - 0.06, math.sin(b) * bell * 0.6,
                           0.025, 0.08, 0.025, INK)  # fmt: skip
    a = seed * 1.3
    r.part("cyl", math.cos(a) * 0.45, 0.01, math.sin(a) * 0.45, 0.34, 0.02, 0.26, INK)  # a cap gone to ink
    r.part("cyl", math.cos(a) * 0.45, 0.06, math.sin(a) * 0.45, 0.05, 0.1, 0.05, INKCAP_DARK, rz=1.3)


SUMP_CAP = (156, 158, 92)  # sallow, sickly olive
SUMP_CAP_DARK = (110, 112, 64)
SUMP_GILL = (190, 210, 110)  # the cold, sickly light under their caps
SUMP_STEM = (150, 146, 112)
SUMP_STUMP = (190, 170, 140)  # tint over the bark of the rotten timber they grow on


def sump_caps(r, seed):
    """Flat, slimy caps crowding a rotten stump of timber washed down from the streets, their gills
    giving off a dim, sickly yellow-green light: what little light the deep tunnels have of their own.
    The light is steady; it doesn't pulse."""
    r.part("cyl", 0, 0.16, 0, 0.36, 0.32, 0.3, SUMP_STUMP, tex="bark", rz=0.08)  # the stump
    r.part("cyl", 0, 0.33, 0, 0.3, 0.02, 0.25, _dim(SUMP_STUMP, 0.6))
    caps = 5 + seed % 3
    for k in range(caps):
        a = k * math.tau / caps + seed * 0.4
        d = 0.24 + (k * 3 + seed) % 3 * 0.09
        x, z = math.cos(a) * d, math.sin(a) * d
        h = 0.1 + (k * 5 + seed) % 4 * 0.09
        w = 0.24 - (k % 3) * 0.04
        r.part("cyl", x, h / 2, z, 0.05, h, 0.05, SUMP_STEM)
        r.part("cyl", x, h + 0.02, z, w, 0.05, w, SUMP_CAP)
        r.part("sphere", x, h + 0.04, z, w * 0.6, 0.04, w * 0.6, SUMP_CAP_DARK)  # its slick, darker crown
        r.part("cyl", x, h - 0.01, z, w * 0.85, 0.015, w * 0.85, SUMP_GILL, glow=True)
    for k in range(3):  # small ones up the stump's flank
        a = k * 2.0 + seed
        r.part("cyl", math.cos(a) * 0.17, 0.18 + k * 0.05, math.sin(a) * 0.17, 0.12, 0.03, 0.12, SUMP_CAP)
        r.part("cyl", math.cos(a) * 0.17, 0.165 + k * 0.05, math.sin(a) * 0.17, 0.1, 0.01, 0.1, SUMP_GILL,
               glow=True)  # fmt: skip
