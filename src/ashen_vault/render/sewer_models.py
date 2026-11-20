"""Models for the Harrow Sewers under the town: its rats and their brood-mother Mother Gnawl, the sludge
slimes and the gobbets they burst into, the drowned that lie in the sludge, the bilge leeches, the Sodden
Pall (a hunched heap of green ooze hooded like a sodden shroud, the drowned's face in its shadow) in the deepest cistern and the clots it sheds, the ways down from the streets (a grate in town, a ladder below) and the sewers' dressing (drain pipes, sluice wheels, the outfall's great grate, a rat's nest).
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.ai.enemy import BURROW_TIME, BURST_TIME
from ashen_vault.render.parts import (
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
DROWNED_RAG = (62, 66, 54)
DROWNED_HAIR = (36, 40, 30)
WEED = (52, 74, 40)
HOLLOW = (14, 16, 12)

LEECH = (54, 46, 40)
LEECH_BELLY = (118, 92, 70)
LEECH_STRIPE = (130, 110, 50)
LEECH_MOUTH = (120, 40, 44)

PALL = (64, 122, 44)  # the Pall's ooze, a deep, wet green
PALL_DARK = (34, 72, 26)  # the runnels down its sides and the pool it drags
PALL_SHEEN = (120, 178, 74)  # the wet light on its folds
PALL_HOLLOW = (14, 30, 12)  # the arch in its hem
PALL_SOCKET = (26, 54, 20)  # the hollows of its face, sunk in the ooze
PALL_FACE = (196, 236, 156)  # the face risen in it, and the bile it spits
PALL_FACE_COLD = (40, 60, 34)
PALL_BONE = (204, 198, 172)

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
        elif kind == "burrow":  # nose down into the muck, the body sinking after it
            lift, pitch, stretch = -0.3 * k, -0.7 * k, 0.08 * k
    elif e.state == "attack" and kind == "burrow":  # bursting up out of the muck, rearing, then down
        u = min(max(e.state_t - BURROW_TIME, 0.0) / BURST_TIME, 1.0)
        rear = math.sin(min(u / 0.35, 1.0) * math.pi / 2) * (1 - _ease(max(u - 0.5, 0.0) / 0.5))
        lift, pitch, stretch = -0.3 + 0.48 * rear, 0.9 * rear, -0.08 * rear
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


def _rat(r, e, t, k, fur, eyes_lit, extras=None, blaze=False, sores=(), torn=False):
    """A rat `k` times a gutter rat's size, in a few bold shapes: a hunched body whose spine swells
    smoothly over the shoulders to a high hump and falls to the hips, old scars across its hide, the head
    carried low and long before it, thin pale legs ending in claws, a bare
    tail, big naked ears, a jaw hung open on its fangs and one round, milky eye a side that catches the
    light while it lives (if `eyes_lit`). `sores` are raw wounds in its hide, (x, y, z, size) in the
    body's frame. Slain, it rolls onto its side and its legs stick out. `extras(r, k)` adds to the
    body, in its frame; `blaze` sets its eyes ablaze; `torn` rips its right ear half away, the flap
    hanging by a strip of raw skin."""
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
        # The hunched spine: a smooth swell rising over the shoulders to the hump and falling to the hips.
        for x, y, sx, sy, sz in ((0.1, 0.1, 0.24, 0.13, 0.22), (-0.03, 0.13, 0.28, 0.15, 0.23),
                                 (-0.15, 0.09, 0.22, 0.12, 0.24)):  # fmt: skip
            r.part("sphere", x * k, y * k, 0, sx * k, sy * k, sz * k, hide if x > -0.1 else dark)
        for side in (-1, 1):  # the bones of its shoulders and hips standing out under the hide
            r.part("sphere", 0.13 * k, 0.05 * k, side * 0.1 * k, 0.12 * k, 0.1 * k, 0.08 * k, hide)
            r.part("sphere", -0.17 * k, 0.04 * k, side * 0.12 * k, 0.14 * k, 0.12 * k, 0.08 * k, dark)
        scar = _dim(hide, 0.55)  # old bite scars, bare and dark across the hide
        r.part("cube", -0.02 * k, 0.2 * k, 0.02 * k, 0.15 * k, 0.012 * k, 0.025 * k, scar, ry=0.6)
        r.part("cube", 0.04 * k, 0.1 * k, -0.115 * k, 0.13 * k, 0.025 * k, 0.012 * k, scar, rz=0.5)
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
                if torn and side > 0:  # a ragged stub, and the rest of the ear hanging off it
                    r.part(
                        "sphere", 0.0, 0.06 * k, 0.065 * k, 0.03 * k, 0.05 * k, 0.08 * k, RAT_EAR, rx=-0.35
                    )
                    r.part("cube", 0.0, 0.08 * k, 0.09 * k, 0.03 * k, 0.015 * k, 0.05 * k, RAT_SORE, rx=-0.35)
                    r.part("sphere", 0.01 * k, 0.03 * k, 0.12 * k, 0.025 * k, 0.08 * k, 0.06 * k, RAT_EAR,
                           rx=-0.2 - 0.1 * math.sin(t * 2.6))  # fmt: skip
                    continue
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
    its broken chain dragging. When she rages at half her strength, her old wounds split open into raw,
    weeping sores along her back and flank, one ear hangs torn, and her eyes blaze. Burrowing, she is
    gone under the muck: only the ripple of her passing shows (`burrow_ripple`)."""
    if e.burrowed:  # gone under the muck: only the ripple of her passing shows
        burrow_ripple(r, t, 4.4)
        return
    rage = e.phase2 and e.alive
    fall = death_fall(e, 0.8)

    def brood(r, k):
        r.part("sphere", 0, -0.08 * k, 0, 0.36 * k, 0.12 * k, 0.21 * k, (120, 96, 92))  # the hanging belly
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
    if rage:  # her wounds torn open: raw sores along the hump and down both flanks
        sores += ((0.08, 0.15, -0.08, 0.12), (-0.04, 0.19, 0.04, 0.1), (-0.15, 0.06, 0.13, 0.12))
    _rat(r, e, t, 4.4, (62, 60, 62), eyes_lit=True, extras=brood, blaze=rage, sores=sores, torn=rage)


# --- slimes ---------------------------------------------------------------------------------------


SLUDGE_COLOURS = (SLUDGE, SLUDGE_DARK, SLUDGE_SCUM, SLUDGE_EYE)
PALL_COLOURS = (PALL, PALL_DARK, PALL_SHEEN, PALL_FACE)


def _sludge(r, e, t, k, junk=True, colours=SLUDGE_COLOURS):
    """A crawling heap of sludge `k` times a sludge slime's size: a spreading foot, a quivering body
    flecked with scum, two milky eyes, bubbles welling and bursting on its skin and, in the big ones,
    the town's rubbish it has swallowed (a boot, a bottle, a rat's skull). Slain, it slumps into a
    spreading puddle. `colours` is (body, foot, scum, eyes)."""
    sludge, sludge_dark, scum, eye = colours
    squash = 1 + math.sin(t * (8 if e.state == "chase" else 3)) * 0.1
    if e.state == "windup":
        squash = 1.3
    if e.state == "attack":
        squash = 0.72
    fall = death_fall(e, 0.8)
    if e.state == "dead":
        squash = 1 + 1.3 * fall
    body = hit_tint((230, 220, 170)) if e.flashing else sludge
    h = 0.8 / squash
    r.part("sphere", 0.04 * k, 0.12 * k, 0, 1.2 * squash * k, 0.24 * k, 1.2 * squash * k, sludge_dark)
    r.part("sphere", 0, 0.34 / squash * k, 0, 0.95 * squash * k, h * k, 0.95 * squash * k, body)
    r.part("sphere", -0.06 * k, 0.46 / squash * k, 0.08 * k, 0.58 * squash * k, h * 0.65 * k,
           0.58 * squash * k, _dim(body, 1.12))  # fmt: skip
    top = (0.34 / squash + h / 2) * k
    for i in range(4):  # scum floating on its skin
        a = i * 1.7 + 0.3
        rad = 0.32 * squash * k
        r.part("sphere", math.cos(a) * rad, top * (0.55 + 0.1 * (i % 2)), math.sin(a) * rad,
               0.22 * k, 0.04 * k, 0.16 * k, scum, ry=a)  # fmt: skip
    for i in range(3):  # bubbles welling up and bursting
        u = (t * 0.7 + i / 3) % 1.0
        a = i * 2.1 + 0.5
        rad = 0.4 * squash * k * (1 - u * 0.6)
        size = (0.05 + 0.07 * math.sin(u * math.pi)) * k
        r.part("sphere", math.cos(a) * rad, (0.1 + (top / k - 0.1) * u) * k, math.sin(a) * rad,
               size, size, size, _dim(scum, 1.1))  # fmt: skip
    for side in (-1, 1):
        r.part("sphere", 0.36 * squash * k, 0.42 / squash * k, side * 0.15 * k, 0.09 * k, 0.11 * k, 0.09 * k,
               eye if e.alive else _dim(eye, 0.5))  # fmt: skip
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


def pall_clot(r, e, t):
    """A clot of green ooze sloughed off the Sodden Pall's hem, crawling at you on its own."""
    _sludge(r, e, t, 0.5, junk=False, colours=PALL_COLOURS)


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


# --- the Sodden Pall ------------------------------------------------------------------------------

PALL_LOBES = 10  # the lobes of its hem, round the skirt
PALL_RUNNELS = 8  # the runnels down its sides
PALL_SWELLS = 7  # the swells its bell is stacked of


def _pall_pose(e):
    """(lean, rear, flare, twist) of the Pall through its moves: `lean` tips its bell forward (+) or
    back (-), `rear` stretches it tall (+) or squashes it flat (-), `flare` throws its skirt out wide,
    `twist` turns it about. A slam rears it up and crashes it down flat, a sweep flings its skirt out
    as it turns, bile rocks it back and pitches it forward, the engulf stretches it long and low over
    its hem, a shed swells it fit to burst."""
    kind = e.attack_kind
    if kind == "slam":
        return 0.0, _swing_pose(e, 0, 0.4, -0.45), _swing_pose(e, 0, -0.1, 0.55), 0.0
    if kind == "sweep":
        return 0.0, _swing_pose(e, 0, -0.1, -0.15), _swing_pose(e, 0, 0.15, 0.8), _swing_pose(e, 0, -0.8, 1.2)
    if kind == "bile":
        return _swing_pose(e, 0, -0.25, 0.3), 0.1, 0.0, 0.0
    if kind == "engulf":
        return _swing_pose(e, 0, -0.15, 0.6), _swing_pose(e, 0, 0.1, -0.35), _swing_pose(e, 0, 0, 0.3), 0.0
    if kind == "shed":
        return 0.0, _swing_pose(e, 0, -0.15, 0.1), 0.2, 0.0
    return _swing_pose(e, 0, -0.2, 0.4), _swing_pose(e, 0, 0.1, -0.15), 0.0, 0.0


def _pall_gape(e):
    """How wide the mouth in its folds opens (0..1): wide to spit bile or to flow over you."""
    if e.attack_kind in ("bile", "engulf") and e.state in ("windup", "attack"):
        return _swing_pose(e, 0, 0.7, 1.0)
    return 0.0


PALL_RUST = (110, 62, 36)  # the rusted junk it has swallowed
PALL_STRANDS = ((-0.5, 0.55), (0.05, 0.95), (0.45, 0.4))  # (z, length) of the strands off its hood's lip
PALL_STRAND_BEADS = 5


def _pall_arms(e):
    """(raise, spread) of the Pall's two pseudopods: `raise` lifts them from dragging on the floor
    ahead (0) up over its hood (1) and crashes them past rest (-), `spread` flings them out to its
    sides. A slam rears both up and brings them down together, a sweep flings them out wide as it turns,
    bile draws them back, the engulf reaches them out ahead, a shed hugs them in."""
    kind = e.attack_kind if e.state in ("windup", "attack", "recover") else None
    if kind == "slam":
        return _swing_pose(e, 0.0, 1.0, -0.35), _swing_pose(e, 0.0, -0.15, 0.1)
    if kind == "sweep":
        return _swing_pose(e, 0.0, 0.35, 0.2), _swing_pose(e, 0.0, 0.35, 1.0)
    if kind == "bile":
        return _swing_pose(e, 0.0, 0.25, 0.05), _swing_pose(e, 0.0, 0.3, 0.1)
    if kind == "engulf":
        return _swing_pose(e, 0.0, 0.2, -0.15), _swing_pose(e, 0.0, -0.25, -0.3)
    if kind == "shed":
        return 0.15, -0.35
    return 0.0, 0.0


def _pall_arm(r, side, raise_, spread, skin, t, k):
    """One pseudopod of ooze out of its flank on `side`, a thick rope narrowing to a splayed, dripping
    tip: at rest it droops forward to drag on the floor, raised it rears over the hood."""
    pitch = _mix(-0.55, 1.45, raise_) if raise_ >= 0 else -0.55 + 0.6 * raise_
    yaw = side * (0.35 + 0.95 * spread)
    bx, by, bz = 0.35 * k, 1.15 * k, side * 1.25 * k
    sway = 0.05 * math.sin(t * 1.7 + side)
    x, y, z = bx, by, bz
    for i in range(5):
        d = 0.42 * k
        p = pitch - 0.1 * i * (1 - raise_ if raise_ > 0 else 1)  # it sags under its own weight
        x += math.cos(p) * math.cos(yaw) * d
        z += math.cos(p) * math.sin(yaw) * d + sway * i
        y = max(y + math.sin(p) * d, 0.15)
        w = (0.62 - 0.08 * i) * k
        r.part("sphere", x, y, z, w * 1.1, w, w, _dim(skin, 0.92 + 0.04 * (i % 2)))
    for f in (-1, 0, 1):  # the splayed tip
        a = yaw + f * 0.45
        r.part("sphere", x + math.cos(a) * 0.22 * k, max(y - 0.05, 0.1), z + math.sin(a) * 0.22 * k,
               0.26 * k, 0.16 * k, 0.16 * k, _dim(skin, 1.05), ry=-a)  # fmt: skip
    u = (t * 0.9 + (side > 0) * 0.5) % 1.0  # a drop falling from it
    r.part("sphere", x, max(y - 0.15 - 0.6 * u, 0.05), z, 0.07, 0.11, 0.07, _dim(skin, 1.2))


def sodden_pall(r, e, t):
    """The Sodden Pall: a heap of green ooze twice a man's height, hunched and lopsided like a sodden
    shroud thrown over the drowned it has taken. Broad and low at the back, it heaves up and forward
    into a heavy hood that sags over the front, slime stretching in strands from its lip; deep in the
    hood's shadow hangs the face of the drowned, slack-jawed. Two thick pseudopods of ooze drag from
    its flanks and rear up to slam and fling out to sweep (`_pall_arms`). Its swallowed dead and the
    town's rubbish show through its sides: ribs and a hand reaching out, a second face pressing up out
    of its flank, a rusted lantern, a length of chain, a cart wheel's rim. Runnels, crawling drops and
    welling bubbles move in it, wet sheen on its curves; a dark pool spreads round its hem of lobes.
    Raging, the faces rise pale and their hollows glow. Its moves rock, stretch and fling it about
    (`_pall_pose`). Slain, it slumps into a wide, still pool."""
    fall = death_fall(e, 1.2)
    lit = e.alive
    rage = e.phase2 and lit
    skin = hit_tint((214, 240, 196)) if e.flashing else PALL
    lean, rear, flare, twist = _pall_pose(e)
    lean = _mix(lean, 0.0, fall)
    gape = _pall_gape(e) if lit else 0.0
    quiver = math.sin(t * (4.5 if e.state == "chase" else 1.8)) * 0.04
    if e.attack_kind == "shed" and e.state == "windup":
        quiver += 0.06 * math.sin(t * 30)  # shuddering, fit to burst
    tall = (1 + rear + quiver) * (1 - 0.85 * fall)
    body = (1 - 0.35 * rear - quiver) * (1 + 0.5 * fall)
    hem = (1 + flare - 0.2 * rear) * (1 + 0.6 * fall)
    low = min(tall, 1.0)
    # The pool it drags along, and the lobes of its skirt lying out over it, rippling outward.
    r.part("cyl", 0.1, 0.02, 0, 4.4 * hem, 0.04, 4.2 * hem, PALL_DARK)
    with r.at(0, 0, 0, ry=twist * 0.5):
        for i in range(PALL_LOBES):
            a = (i + 0.5) * math.tau / PALL_LOBES
            ripple = 1 + 0.06 * math.sin(t * 2.4 + i * 1.3)
            d = (1.5 + 0.25 * (math.cos(a) < 0)) * hem * ripple  # it spreads wider behind
            r.part("sphere", math.cos(a) * d, 0.24 * low, math.sin(a) * d, 1.2 * hem, 0.55 * low, 0.95 * hem,
                   _dim(skin, 0.84 + 0.05 * (i % 3)), ry=-a)  # fmt: skip
        for a, tilt in ((2.3, 0.5), (-2.6, -0.4), (1.2, 0.8)):  # bones of the drowned poking out of its hem
            d = 2.0 * hem
            r.part("cube", math.cos(a) * d, 0.12, math.sin(a) * d, 0.08, 0.08, 0.6, PALL_BONE, ry=-a + tilt)
        for i in range(5):  # a length of chain trailing out of its hem behind
            r.part("cube", -1.9 * hem - 0.18 * i, 0.06, -0.9 + 0.12 * i, 0.16, 0.05, 0.08, PALL_RUST,
                   rx=(i % 2) * math.pi / 2, ry=0.6)  # fmt: skip

    def bent(y):
        """It leans by bending: its hem stays put on the floor, and the higher up, the further over."""
        return r.at(0, 0, 0, rz=-lean * min(max((y - 0.4) / 2.4, 0.0), 1.0))

    with r.at(0, 0, 0, ry=twist):
        # The heap: swells broad and low, held back from the front, hunched off to one side.
        for i in range(PALL_SWELLS):
            u = i / (PALL_SWELLS - 1)
            w = 3.4 - 1.5 * u
            y = 0.5 + 1.7 * u
            with bent(y):
                r.part("sphere", (-0.45 + 0.1 * u) * body, y * tall, 0.18 * math.sin(u * math.pi) * body,
                       w * body * 1.05, 1.0 * tall, w * body * (0.95 - 0.08 * u), _dim(skin, 0.88 + 0.18 * u))  # fmt: skip
        with bent(2.9):  # its hunched back, the highest of it
            r.part(
                "sphere",
                -0.35 * body,
                2.75 * tall,
                0.15,
                2.0 * body,
                1.3 * tall,
                2.0 * body,
                _dim(skin, 1.05),
            )
        with bent(2.5):
            # The hood: a heavy fold heaved forward off its hump, sloping down to a lip that sags low
            # over the face, the shadow under it hollowed back into the ooze.
            r.part("sphere", 0.45 * body, 2.45 * tall, 0, 2.3 * body, 1.15 * tall, 2.15 * body, _dim(skin, 1.12),
                   rz=-0.3 * (1 - fall))  # fmt: skip
            r.part(
                "sphere",
                1.2 * body,
                2.0 * tall,
                0,
                0.75,
                0.6 * tall,
                1.85,
                _dim(skin, 1.02),
                rz=-0.25 * (1 - fall),
            )  # its lip
            r.part("sphere", 0.98 * body, 1.55 * tall, 0, 0.5, 1.0 * tall, 1.35, PALL_HOLLOW)  # its shadow
            for i, (z, reach) in enumerate(PALL_STRANDS):  # slime drooping in strands off its lip
                length = (reach + 0.08 * math.sin(t * 0.8 + i * 2.1)) * tall
                top = 1.85 * tall
                for j in range(PALL_STRAND_BEADS):  # each strand thins as it stretches, then gathers a drop
                    u = (j + 1) / PALL_STRAND_BEADS
                    sway = 0.08 * u * u * math.sin(t * 1.3 + i * 1.7)
                    w = 0.2 - 0.13 * math.sin(u * math.pi * 0.85) if j < PALL_STRAND_BEADS - 1 else 0.17
                    r.part("sphere", 1.45 * body + 0.06 * u + sway, top - length * u, z + sway * 0.5,
                           w, length / PALL_STRAND_BEADS * 1.4, w, _dim(skin, 1.1 + 0.1 * u))  # fmt: skip
            for x, y, z, w in ((0.7, 2.9, 0.4, 0.5), (-0.3, 3.35, -0.5, 0.45), (1.25, 2.25, -0.55, 0.3)):
                r.part("sphere", x * body, y * tall, z, w, w * 0.5, w, PALL_SHEEN)  # wet light on its curves
            if fall < 0.6:
                _pall_face(r, body, tall, rage, lit, gape)
        # Runnels and sheen down its sides, a drop crawling down each.
        for i in range(PALL_RUNNELS):
            a = i * math.tau / PALL_RUNNELS + 0.4
            c, sn = math.cos(a), math.sin(a)
            shade = PALL_DARK if i % 2 else PALL_SHEEN
            for y, rad, length, tilt in ((0.75, 1.55, 1.2, 0.5), (1.8, 1.1, 1.1, 0.35)):
                with bent(y), r.at(c * rad * body, y * tall, sn * rad * body, ry=-a):
                    r.part("sphere", 0.04, 0, 0, 0.12, length * tall, 0.16, shade, rz=tilt)
            u = (t * 0.22 + i / PALL_RUNNELS) % 1.0
            rad, y = 0.85 + 0.85 * u, 2.5 - 2.0 * u
            with bent(y):
                r.part("sphere", c * rad * body, y * tall, sn * rad * body, 0.14, 0.2, 0.14, _dim(skin, 1.25))
        for i in range(4):  # bubbles welling up in it
            a = i * 1.6 + 0.9
            u = (t * (0.7 if rage else 0.4) + i / 4) % 1.0
            rad = (1.4 - 0.7 * u) * body
            b = 0.08 + 0.12 * math.sin(u * math.pi)
            y = 0.6 + 1.9 * u
            with bent(y):
                r.part("sphere", math.cos(a) * rad, y * tall, math.sin(a) * rad, b, b, b, PALL_SHEEN)
        if fall < 0.6:
            with bent(1.3):
                _pall_swallowed(r, body, tall, rage, lit)
            raise_, spread = _pall_arms(e) if lit else (0.0, 0.0)
            k = 1 - fall
            for side in (-1, 1):
                _pall_arm(r, side, raise_, spread, skin, t, k)


def _pall_swallowed(r, body, tall, rage, lit):
    """What shows through its sides: the ribs of a drowned man and his hand reaching out of its left
    flank, a second face pressing up out of its right, a rusted lantern and a cart wheel's rim."""
    glow = PALL_FACE if lit else PALL_FACE_COLD
    with r.at(-0.1 * body, 1.1 * tall, -1.72 * body, ry=0.3):  # the ribs, and the arm reaching out
        for i in range(4):
            r.part("cube", 0, 0.25 - 0.17 * i, 0, 0.5 - 0.04 * i, 0.05, 0.06, PALL_BONE, rx=0.35, ry=0.2)
        with r.at(0.25, 0.35, -0.15, rx=-0.7, rz=0.5):
            r.part("cube", 0, 0.35, 0, 0.07, 0.7, 0.07, PALL_BONE)  # the forearm
            for f in range(4):  # splayed fingers
                r.part("cube", 0.03 * (f - 1.5), 0.82, 0, 0.025, 0.24, 0.025, PALL_BONE, rz=0.22 * (f - 1.5))
    with r.at(-0.75 * body, 1.35 * tall, 1.5 * body, ry=-1.25, rz=0.3):  # a second face, pressing out of it
        r.part("sphere", 0, 0, 0, 0.16, 0.5, 0.36, _dim(PALL_FACE, 0.55) if rage else _dim(PALL, 1.2))
        for side in (-1, 1):
            r.part(
                "sphere", 0.07, 0.08, side * 0.08, 0.05, 0.1, 0.07, glow if rage else PALL_SOCKET, glow=rage
            )
        r.part("sphere", 0.07, -0.13, 0, 0.05, 0.12, 0.08, PALL_SOCKET)  # its mouth, stretched in a cry
    with r.at(-1.6 * body, 0.85 * tall, -1.2 * body, rz=0.4):  # a rusted lantern, swallowed whole
        r.part("cube", 0, 0, 0, 0.22, 0.3, 0.22, PALL_RUST)
        r.part("cube", 0, 0, 0, 0.24, 0.18, 0.12, _dim(PALL_FACE, 0.5) if rage else PALL_SOCKET, glow=rage)
        r.part("cube", 0, 0.2, 0, 0.04, 0.12, 0.14, PALL_RUST)
    with r.at(-2.05 * body, 0.95 * tall, 0.6 * body, ry=0.25, rx=0.2):  # a cart wheel's rim, half sunk
        for i in range(8):
            a = i * math.tau / 8
            r.part(
                "cube",
                0,
                math.sin(a) * 0.45,
                math.cos(a) * 0.45,
                0.06,
                0.08,
                0.36,
                PALL_RUST,
                rx=-a - math.pi / 2,
            )


def _pall_face(r, body, tall, rage, lit, gape):
    """The face of the drowned deep in the shadow of its hood, facing +X: a sunken brow, two hollow
    sockets and a slack, hanging jaw. Raging, the face rises pale and its hollows glow; the jaw drops
    to spit or engulf."""
    glow = PALL_FACE if lit else PALL_FACE_COLD
    x = 1.2 * body
    skin = _dim(PALL_FACE, 0.7) if rage else _dim(PALL, 0.85)
    r.part("sphere", x, 1.55 * tall, 0, 0.26, 0.7 * tall, 0.52, skin)  # the face, sunk in the shadow
    r.part("sphere", x + 0.08, 1.8 * tall, 0, 0.14, 0.08 * tall, 0.48, _dim(skin, 1.15))  # its brow
    for side in (-1, 1):
        r.part("sphere", x + 0.09, 1.7 * tall, side * 0.13, 0.11, 0.15 * tall, 0.1, glow if rage else PALL_SOCKET,
               glow=rage)  # fmt: skip
    jaw = (0.18 + 0.4 * gape) * tall
    r.part("sphere", x + 0.11, (1.4 - 0.5 * jaw) * tall, 0, 0.12, jaw, 0.14 + 0.18 * gape,
           glow if rage else PALL_SOCKET, glow=rage)  # fmt: skip
    if gape > 0.3:  # a gout of glowing bile welling in its mouth
        r.part("sphere", x + 0.15, (1.32 - 0.4 * jaw) * tall, 0, 0.14, 0.3 * gape * tall, 0.22 * gape, PALL_FACE,
               glow=lit)  # fmt: skip


def burrow_ripple(r, t, k):
    """Mother Gnawl tunnelling under the muck toward you (+X): a low swell heaving along, the ridge of
    her back breaking the surface, a bow wave of scummy sludge before it, rings spreading out behind,
    and clumps of muck tumbling off its back."""
    heave = 0.5 + 0.5 * math.sin(t * 9)
    r.part("sphere", 0, 0.02, 0, 0.42 * k, (0.05 + 0.025 * heave) * k, 0.3 * k, SLUDGE_DARK)  # the swell
    r.part("sphere", -0.03 * k, 0.03 * k, 0, 0.22 * k, (0.04 + 0.02 * heave) * k, 0.1 * k,
           (62, 60, 62))  # her back, just breaking the surface  # fmt: skip
    r.part("sphere", 0.18 * k, 0.025 * k, 0, 0.12 * k, 0.045 * k, 0.32 * k, SLUDGE_SCUM)  # the bow wave
    for i in range(3):  # rings spreading out behind as it goes
        u = (t * 1.6 + i / 3) % 1.0
        d = (0.18 + 0.32 * u) * k
        r.part("cyl", -0.1 * k * u, 0.006, 0, d, 0.012, d * 0.8, _dim(SLUDGE, 1.1 - 0.3 * u))
    for i in range(5):  # clumps of muck heaved up and falling back
        u = (t * 2.2 + i * 0.37) % 1.0
        a = i * 2.4 + 0.6
        x, z = math.cos(a) * 0.16 * k - 0.05 * k * u, math.sin(a) * 0.14 * k * (0.6 + 0.6 * u)
        y = (0.03 + 0.5 * u * (1 - u)) * k
        size = (0.05 + 0.02 * (i % 2)) * k * (1 - 0.4 * u)
        r.part("sphere", x, y, z, size, size * 0.8, size, SLUDGE_SCUM if i % 3 == 0 else SLUDGE)


def filth_burst(r, rise, t):
    """A spout of filth where Mother Gnawl bursts up out of the muck (`hazards.Eruption` style
    "filth"): a column of black sludge thrown up (`rise` 0..1) and falling back, clods of muck and scum
    flung out round it, a dark stain spreading under it."""
    if rise <= 0:
        return
    r.part("cyl", 0, 0.012, 0, 1.3 * (0.6 + 0.4 * rise), 0.02, 1.3 * (0.6 + 0.4 * rise), SLUDGE_DARK)
    h = 1.5 * rise
    r.part("cyl", 0, h / 2, 0, 0.45 * rise, h, 0.45 * rise, SLUDGE_DARK)  # the spout
    r.part("sphere", 0, h, 0, 0.6 * rise, 0.35 * rise, 0.6 * rise, SLUDGE)  # its head, breaking
    for i in range(6):  # clods flung out and falling
        a = i * math.tau / 6 + t * 0.3
        d = 0.25 + 0.55 * (1 - rise)
        y = h * (0.4 + 0.15 * (i % 3))
        size = 0.12 + 0.05 * (i % 2)
        r.part("sphere", math.cos(a) * d, y, math.sin(a) * d, size, size * 0.8, size,
               SLUDGE_SCUM if i % 2 else _dim(SLUDGE, 0.8))  # fmt: skip


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
    """The way back up to the street: an iron ladder bolted to the brick from the floor up a tall shaft
    to a square opening in its vault, black with the dark of the climb beyond, slow drips falling from it
    and a puddle at its foot. `back` sets it that far back toward a wall behind it (-X)."""
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
    r.part("cube", 0, height - 0.02, 0, 1.1, 0.03, 1.1, PASSAGE_DARK)  # the black of the climb beyond
    r.part("cube", 0.2, 0.012, 0, 1.2, 0.02, 1.0, (70, 80, 72))  # the puddle at its foot
    for k in range(4):  # drips falling from the dark
        u = (t * 0.7 + k / 4) % 1.0
        r.part("cube", 0.25 + 0.1 * math.sin(k * 2.1), height - 0.1 - u * (height - 0.2), (k - 1.5) * 0.15,
               0.025, 0.06, 0.025, (74, 82, 76))  # fmt: skip


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
