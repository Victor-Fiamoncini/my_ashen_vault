"""Models for the Harrow Sewers under the town: its rats and their brood-mother Mother Gnawl, the sludge
slimes and the gobbets they burst into, the drowned that lie in the sludge, the bilge leeches, the Sump
Reeve who rules the deepest cistern, the ways down from the streets (a grate in town, a ladder below)
and the sewers' dressing (drain pipes, sluice wheels, the outfall's great grate, a rat's nest).
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

RAT_FUR = (86, 78, 70)
RAT_DARK = (58, 52, 48)
RAT_PINK = (176, 120, 112)  # ears, paws, tail, snout
RAT_TOOTH = (210, 186, 110)
RAT_EYE = (40, 10, 10)
RAT_EYE_LIT = (230, 60, 40)
SCAB = (112, 58, 50)
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

REEVE_COAT = (40, 52, 52)  # his sodden coat of office
BRASS = (176, 140, 64)
BRASS_DARK = (110, 86, 40)
BILE = (150, 190, 60)  # the reeve's eyes and lantern, and his spewed bile
BILE_COLD = (52, 58, 40)

BRICK = (100, 70, 56)
IRON = (62, 60, 64)
RUST = (112, 66, 42)
OLD_WOOD = (74, 62, 46)


# --- rats -----------------------------------------------------------------------------------------


def _rat_pose(e, t):
    """(lift, pitch, stretch, spin): how a rat crouches, rears and springs through its attacks. `lift`
    raises the body, `pitch` tips the head up, `stretch` reaches the body forward, `spin` turns it
    (a sweep's rake all round)."""
    lift = pitch = stretch = spin = 0.0
    if e.state == "windup":
        k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
        lift, pitch, stretch = -0.03 * k, 0.5 * k, -0.06 * k  # crouched, head up, ready to spring
        if e.attack_kind == "sweep":
            spin = -0.6 * k
    elif e.state == "attack":
        k = min(e.state_t / 0.2, 1.0)
        lift, pitch, stretch = 0.05 * k, -0.2 * k, 0.1 * k
        if e.attack_kind == "pounce":
            lift, pitch = 0.18, 0.25
        if e.attack_kind == "sweep":
            spin = -0.6 + 2 * math.pi * _ease(min(e.state_t / 0.35, 1.0))
    elif e.state == "hurt":
        pitch = 0.4
    return lift, pitch, stretch, spin


def _rat(r, e, t, k, fur, eyes_lit, extras=None, blaze=False):
    """A rat `k` times a gutter rat's size: a hunched body over four scurrying legs, a long pink tail,
    a wedge of a head with yellow incisors, red eyes (lit while it lives, if `eyes_lit`). Slain, it
    rolls onto its side and its legs stick out. `extras(r, k)` adds to the body, in its frame; `blaze`
    sets its eyes ablaze."""
    fall = death_fall(e, 0.6)
    running = e.state == "chase"
    gait = math.sin(t * (15 if running else 4)) * (0.6 if running else 0.15) * (1 - fall)
    lift, pitch, stretch, spin = _rat_pose(e, t)
    hide = hit_tint((240, 200, 190)) if e.flashing else fur
    dark = _dim(hide, 0.72)
    eye = RAT_EYE_LIT if eyes_lit and fall < 0.5 else RAT_EYE
    y0 = (0.15 + lift + 0.01 * abs(gait)) * (1 - fall) + 0.09 * fall
    with r.at(stretch * k, y0 * k, 0, ry=spin, rx=fall * math.pi / 2):
        r.part("sphere", 0, 0, 0, 0.46 * k, 0.22 * k, 0.25 * k, hide)  # body
        r.part("sphere", -0.13 * k, 0.015 * k, 0, 0.28 * k, 0.25 * k, 0.29 * k, dark)  # haunches
        r.part("sphere", 0.12 * k, -0.005 * k, 0, 0.21 * k, 0.19 * k, 0.21 * k, hide)  # shoulders
        r.part("sphere", 0, -0.055 * k, 0, 0.34 * k, 0.1 * k, 0.17 * k, _dim(hide, 1.15))  # belly
        for i, (lx, lz) in enumerate(((0.13, 0.08), (0.13, -0.08), (-0.14, 0.09), (-0.14, -0.09))):
            a = gait * (1 if i in (0, 3) else -1)
            with r.at(lx * k, -0.06 * k, lz * k, rz=a):
                r.part("cube", 0, -0.045 * k, 0, 0.045 * k, 0.1 * k, 0.045 * k, dark)
                r.part("cube", 0.02 * k, -0.095 * k, 0, 0.065 * k, 0.02 * k, 0.045 * k, RAT_PINK)  # paw
        tail = (-0.25 * k, -0.01 * k, 0.0)
        for s in range(4):  # the tail, swishing behind
            sway = math.sin(t * 3 + s * 0.9) * 0.08 * (s + 1) * (1 - fall)
            nxt = (tail[0] - 0.13 * k, tail[1] - 0.025 * k + 0.01 * k * s, (sway + 0.02 * s) * k)
            _bar(r, tail, nxt, (0.035 - 0.006 * s) * k, RAT_PINK)
            tail = nxt
        with r.at(0.22 * k, 0.02 * k, 0, rz=pitch + math.sin(t * 2.3) * 0.08):
            r.part("sphere", 0.06 * k, 0, 0, 0.17 * k, 0.13 * k, 0.13 * k, hide)  # head
            r.part("cube", 0.15 * k, -0.015 * k, 0, 0.11 * k, 0.07 * k, 0.07 * k, hide, rz=-0.15)  # snout
            r.part("sphere", 0.21 * k, -0.02 * k, 0, 0.035 * k, 0.03 * k, 0.035 * k, RAT_PINK)  # nose
            r.part("cube", 0.19 * k, -0.06 * k, 0, 0.018 * k, 0.04 * k, 0.03 * k, RAT_TOOTH)  # incisors
            for side in (-1, 1):
                r.part("sphere", 0.1 * k, 0.035 * k, side * 0.045 * k, 0.03 * k, 0.03 * k, 0.025 * k, eye,
                       glow=eye is RAT_EYE_LIT)  # fmt: skip
                if blaze and eye is RAT_EYE_LIT:
                    r.part("sphere", 0.115 * k, 0.035 * k, side * 0.05 * k, 0.045 * k, 0.03 * k, 0.04 * k,
                           (255, 200, 120), glow=True)  # fmt: skip
                r.part("sphere", 0.01 * k, 0.065 * k, side * 0.05 * k, 0.035 * k, 0.07 * k, 0.06 * k,
                       RAT_PINK, rx=-side * 0.3)  # fmt: skip
                r.part("cube", 0.19 * k, -0.02 * k, side * 0.06 * k, 0.005 * k, 0.005 * k, 0.1 * k,
                       (200, 196, 180), ry=side * 0.3)  # whiskers  # fmt: skip
        if extras:
            extras(r, k)


def sewer_rat(r, e, t):
    """A gutter rat the size of a cat, grey and scabbed, its eyes red in the dark."""
    _rat(r, e, t, 1.0, RAT_FUR, eyes_lit=True)


def giant_rat(r, e, t):
    """A cistern rat as big as a hound, mangy: bald patches and scabs on its hide, a torn ear, a ridge
    of bristles along its spine."""

    def mange(r, k):
        for i, (x, y, z) in enumerate(((0.05, 0.1, 0.07), (-0.12, 0.11, -0.08), (0.1, 0.07, -0.09))):
            r.part("sphere", x * k, y * k, z * k, 0.1 * k, 0.04 * k, 0.08 * k, MANGE if i % 2 else SCAB)
        for i in range(5):  # bristles along the spine
            x = (0.14 - i * 0.07) * k
            r.part("cube", x, 0.12 * k, 0, 0.015 * k, 0.06 * k, 0.03 * k, RAT_DARK, rz=-0.4)
        r.part("cube", 0.24 * k, 0.1 * k, 0.05 * k, 0.03 * k, 0.03 * k, 0.03 * k, SCAB)  # the torn ear

    _rat(r, e, t, 2.4, (92, 82, 72), eyes_lit=True, extras=mange)


def rat_matron(r, e, t):
    """Mother Gnawl, the brood-mother of the sewers' rats: a rat swollen to the size of a cart-horse,
    her belly hanging heavy with teats, scabbed and bald in patches, a rusted iron collar on her neck
    with its broken chain dragging, rags and bones caught in her fur. When she has called her litter
    her hackles rise in a mane of bristles and her eyes blaze."""
    rage = e.phase2 and e.alive
    fall = death_fall(e, 0.8)

    def brood(r, k):
        r.part("sphere", 0, -0.08 * k, 0, 0.36 * k, 0.12 * k, 0.21 * k, (150, 112, 104))  # the hanging belly
        for i in range(6):  # teats
            x = (0.1 - (i // 2) * 0.1) * k
            r.part("sphere", x, -0.135 * k, (0.04 if i % 2 else -0.04) * k, 0.025 * k, 0.03 * k, 0.025 * k,
                   RAT_PINK)  # fmt: skip
        for i, (x, y, z) in enumerate(
            (
                (0.06, 0.1, 0.08),
                (-0.14, 0.12, -0.1),
                (0.13, 0.06, -0.09),
                (-0.05, 0.1, 0.11),
                (-0.2, 0.05, 0.1),
            )
        ):
            r.part("sphere", x * k, y * k, z * k, 0.09 * k, 0.035 * k, 0.07 * k, SCAB if i % 2 else MANGE)
        bristles = 12 if rage else 8
        for i in range(bristles):  # a ridge of bristles, a mane when she rages
            x = (0.18 - i * 0.36 / bristles) * k
            tall = (0.09 if rage else 0.05) * k
            r.part("cube", x, 0.12 * k + tall / 2, ((i % 3) - 1) * 0.02 * k, 0.012 * k, tall, 0.02 * k,
                   RAT_DARK, rz=-0.35)  # fmt: skip
        with r.at(0.2 * k, 0.03 * k, 0):  # the collar and its broken chain
            r.part("cyl", 0, 0, 0, 0.07 * k, 0.17 * k, 0.17 * k, RUST, rz=math.pi / 2)
            link = (0.0, -0.08 * k, 0.0)
            for i in range(5):
                swing = math.sin(t * 2 + i) * 0.03 * k * (1 - fall)
                nxt = (link[0] - 0.04 * k, link[1] - 0.025 * k, link[2] + swing + 0.01 * k)
                _bar(r, link, nxt, 0.018 * k, _dim(IRON, 0.9 + 0.05 * (i % 2)))
                link = nxt
        r.part(
            "cube", -0.05 * k, 0.09 * k, -0.12 * k, 0.12 * k, 0.03 * k, 0.05 * k, (96, 84, 62), rx=0.5
        )  # a rag
        _bar(
            r, (-0.1 * k, 0.1 * k, 0.1 * k), (0.02 * k, 0.12 * k, 0.13 * k), 0.012 * k, (206, 196, 170)
        )  # a bone

    _rat(r, e, t, 4.4, (78, 70, 64), eyes_lit=True, extras=brood, blaze=rage)


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


# --- the Sump Reeve -------------------------------------------------------------------------------


def _reeve_arms(e):
    """(shoulder, elbow, twist) of the Reeve's long arms through his moves: both raised for a slam and
    brought down onto the floor, swung round for a sweep, the head thrown back to spew bile."""
    kind = e.attack_kind
    if kind == "slam":
        return _swing_pose(e, 0.5, 3.0, 0.2), _swing_pose(e, 0.6, 0.3, 0.1), 0.0
    if kind == "sweep":
        twist = _swing_pose(e, 0.0, -0.9, 1.4)
        return 1.4, 0.3, twist
    if kind == "combo":
        return 0.6 + 1.8 * abs(math.sin(e.state_t * 9)), 0.4, math.sin(e.state_t * 9) * 0.3
    return _swing_pose(e, 0.5, 2.4, 0.9), _swing_pose(e, 0.6, 0.8, 0.2), 0.0


def sump_reeve(r, e, t):
    """The Sump Reeve: once the town's keeper of the drains, drowned at his post and grown into the
    sludge. A heap of sewage rises from the floor round his bloated body and every body the sewers
    took: their faces and hands break its surface. He still wears his sodden coat of office, his
    brass chain and badge, and a drooping wide-brimmed hat, and he carries the drain-keeper's lantern,
    its flame burned bile-green. Raging, the drowned in him claw their way out and their eyes kindle.
    Slain, he sinks into the heap and it slumps flat."""
    fall = death_fall(e, 1.0)
    lit = e.alive
    rage = e.phase2 and lit
    skin = hit_tint((236, 236, 210)) if e.flashing else DROWNED_SKIN
    muck = hit_tint((220, 210, 160)) if e.flashing else SLUDGE
    glow_rgb = BILE if lit else BILE_COLD
    heave = 1 + math.sin(t * 2.2) * 0.04
    flat = 1 - 0.45 * fall
    # The heap of sludge he rises from, with its drowned.
    r.part("sphere", 0, 0.14, 0, 2.9, 0.28, 2.9, SLUDGE_DARK)  # the spreading foot
    r.part("sphere", 0, 0.5 * flat, 0, 2.3 * heave, 1.0 * flat, 2.2 * heave, muck)
    r.part("sphere", -0.2, 0.8 * flat, 0.1, 1.5, 0.9 * flat, 1.4, _dim(muck, 1.1))
    for i in range(6):  # scum and drips round the heap
        a = i * 1.05 + 0.2
        r.part("sphere", math.cos(a) * 1.1, 0.08, math.sin(a) * 1.1, 0.4, 0.1, 0.3, SLUDGE_SCUM, ry=a)
    for a, y in ((0.9, 0.6), (2.6, 0.55), (4.2, 0.65)):  # faces breaking the surface
        x, z = math.cos(a) * 0.95, math.sin(a) * 0.95
        r.part("sphere", x, y * flat, z, 0.3, 0.26, 0.28, _dim(skin, 0.85))
        for side in (-1, 1):
            r.part("cube", x + math.cos(a) * 0.13, y * flat + 0.03, z + side * 0.06 + math.sin(a) * 0.13,
                   0.04, 0.05, 0.05, (255, 230, 120) if rage else HOLLOW, glow=rage)  # fmt: skip
    for i, a in enumerate((0.3, 1.8, 3.4, 5.0)):  # hands reaching up out of it
        with r.at(math.cos(a) * 1.15, 0.5 * flat, math.sin(a) * 1.15, rz=0.3, rx=math.sin(a) * 0.4):
            r.part("cube", 0, 0.12, 0, 0.09, 0.25, 0.09, _dim(skin, 0.8))
            with r.at(0, 0.25, 0, rz=math.pi):
                hand(r, _dim(skin, 0.8), 0.12, curl=0.5 + 0.2 * math.sin(t * 2 + i))
    if rage:  # the drowned claw their way out, flailing
        for i, a in enumerate((0.6, 2.2, 3.8, 5.4)):
            flail = math.sin(t * 5 + i * 1.3) * 0.5
            with r.at(math.cos(a) * 0.9, 0.7, math.sin(a) * 0.9, ry=-a, rz=1.0 + flail):
                r.part("cube", 0, 0.3, 0, 0.12, 0.6, 0.12, _dim(skin, 0.75))
                with r.at(0, 0.6, 0, rz=0.6):
                    r.part("cube", 0, 0.25, 0, 0.1, 0.5, 0.1, _dim(skin, 0.7))
                    with r.at(0, 0.5, 0, rz=math.pi):
                        hand(r, _dim(skin, 0.7), 0.14, curl=0.7)
    # The Reeve himself, rising from the heap: he sinks into it as he dies.
    shoulder, elbow, twist = _reeve_arms(e)
    shoulder, elbow = _mix(shoulder, -0.5, fall), _mix(elbow, 0.1, fall)
    spew = e.attack_kind == "bile" and e.state in ("windup", "attack")
    with r.at(0.1, 0.9 - 0.5 * fall, 0, ry=twist, rz=-0.15 - 0.9 * fall):
        r.part("sphere", 0, 0.65, 0, 0.95, 1.1, 0.95, skin)  # the bloated trunk
        r.part("cube", -0.06, 0.75, 0, 0.9, 1.0, 1.0, REEVE_COAT)  # his coat of office, sodden
        for side in (-1, 1):
            r.part(
                "cube", 0.36, 0.7, side * 0.3, 0.2, 0.9, 0.34, _dim(REEVE_COAT, 1.15), rx=side * 0.1
            )  # lapels
        for y in (0.45, 0.7, 0.95):
            r.part("sphere", 0.47, y, 0.12, 0.06, 0.06, 0.06, BRASS_DARK)  # buttons, gone green
        for i in range(7):  # the chain of office across his chest
            a = -1.2 + i * 0.4
            r.part("cube", 0.46 + 0.02 * math.cos(a), 1.1 - 0.22 * math.cos(a), math.sin(a) * 0.4,
                   0.05, 0.07, 0.1, BRASS, rx=a * 0.6)  # fmt: skip
        with r.at(0.5, 0.82, 0):  # the badge: a drain grate under a key
            r.part("cyl", 0, 0, 0, 0.22, 0.04, 0.22, BRASS, rz=math.pi / 2)
            for z in (-0.05, 0.0, 0.05):
                r.part("cube", 0.025, 0, z, 0.01, 0.14, 0.02, BRASS_DARK)
            r.part("cube", 0.025, 0.06, 0, 0.01, 0.02, 0.16, glow_rgb, glow=lit)
        for side, holds in ((1, True), (-1, False)):  # long arms; the right one holds his lantern
            with r.at(0, 1.2, side * 0.55, rz=shoulder, rx=side * 0.25):
                r.part("cube", 0, -0.35, 0, 0.26, 0.75, 0.26, REEVE_COAT)
                with r.at(0, -0.72, 0, rz=elbow):
                    r.part("cube", 0, -0.35, 0, 0.22, 0.72, 0.22, skin)
                    with r.at(0, -0.72, 0):
                        if holds:
                            r.part("cube", 0, -0.04, 0, 0.16, 0.16, 0.16, skin)  # his fist on the ring
                            with r.at(0, -0.12, 0, rz=-shoulder - elbow):
                                _lantern(r, t, lit)
                        else:
                            hand(r, skin, 0.28, curl=0.4)
        with r.at(0.15, 1.42, 0, rz=0.25 + (-0.6 if spew else 0.0)):
            r.part("cube", 0, 0.05, 0, 0.3, 0.2, 0.3, _dim(skin, 0.85))  # neck
            r.part("sphere", 0.05, 0.36, 0, 0.56, 0.58, 0.52, skin)  # the swollen head
            for side in (-1, 1):
                r.part("cube", 0.3, 0.42, side * 0.12, 0.04, 0.08, 0.1, glow_rgb, glow=lit)  # his eyes
            r.part("cube", 0.3, 0.2, 0, 0.06, 0.12 + (0.12 if spew else 0.0), 0.2, (40, 50, 24))  # his mouth
            if spew:
                r.part("sphere", 0.42, 0.18, 0, 0.18, 0.14, 0.16, glow_rgb, glow=lit)  # bile welling up
            r.part("cyl", 0.02, 0.64, 0, 1.15, 0.05, 1.05, REEVE_COAT, rz=-0.12)  # the drooping brim
            r.part("cyl", 0.0, 0.78, 0, 0.55, 0.3, 0.55, _dim(REEVE_COAT, 0.85))  # its crown
            r.part("cube", 0.0, 0.67, 0, 0.6, 0.06, 0.6, BRASS_DARK, ry=math.pi / 4)  # its band
    for i in range(3):  # sludge running down off him
        u = (t * 0.8 + i / 3) % 1.0
        r.part(
            "cube", 0.5 + 0.1 * i, 0.4 + 1.8 * (1 - u) * (1 - fall), (i - 1) * 0.5, 0.06, 0.16, 0.06, SLUDGE
        )


def _lantern(r, t, lit):
    """The drain-keeper's lantern, hanging from its ring: a caged iron box with a bile-green flame."""
    flicker = 0.85 + 0.15 * math.sin(t * 9)
    r.part("cube", 0, -0.08, 0, 0.04, 0.16, 0.04, IRON)  # the ring's stem
    r.part("cube", 0, -0.2, 0, 0.3, 0.04, 0.3, IRON)  # its cap
    r.part("cube", 0, -0.48, 0, 0.3, 0.04, 0.3, IRON)  # its base
    for x, z in ((-0.13, -0.13), (-0.13, 0.13), (0.13, -0.13), (0.13, 0.13)):
        r.part("cube", x, -0.34, z, 0.03, 0.28, 0.03, IRON)
    if lit:
        r.part("cube", 0, -0.34, 0, 0.16 * flicker, 0.22 * flicker, 0.16 * flicker, BILE, glow=True)
    else:
        r.part("cube", 0, -0.42, 0, 0.12, 0.06, 0.12, BILE_COLD)


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
