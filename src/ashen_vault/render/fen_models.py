"""The Sallow Fen's models: the marsh below the Cinderhold's cliffs, fouled violet by the fortress's
slag runoff. Its foes (the Fen Lurk, the Bilegut, the Mire Tyrant) and its props (the beacons, dead
cypresses, reed clumps, a sunken stilt hut, the stumps of an old walkway). +X is forward, as in every
enemy model."""

import math

from ashen_vault.render.parts import BONE, FLAME, IRON, _bar, _dim, _ease, _flame, death_fall, hit_tint

FEN_VIOLET = (190, 90, 240)  # the beacons' fire and the creatures' toxin
VIOLET_PALE = (236, 196, 255)
GLOW_COLD = (40, 30, 46)  # an eye or a fire gone dark
REED = (104, 112, 62)
REED_DARK = (68, 74, 40)
CATTAIL = (86, 58, 40)
DEAD_WOOD = (78, 68, 58)
MOSS = (110, 118, 96)


def _seed(e):
    return int(abs(e.home_x * 3 + e.home_z * 7))


def _charge(e):
    """0..1 through a windup (eased), 1 through the blow itself, else 0."""
    if e.state == "windup":
        return _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
    return 1.0 if e.state == "attack" else 0.0


# --- the Fen Lurk ------------------------------------------------------------------------------------


SPEAR_Z = 0.08  # the spear rides a little to the lurk's right, both fists on it
SPEAR_HANDS = {1: -0.32, -1: 0.28}  # where each fist closes on the haft: right behind, left before


def _spear_grip(draw, lean):
    """How the Fen Lurk holds its spear, in its hunched body's frame: the haft's centre `(x, y)`, the
    angle (about z) that keeps the haft level whatever the body's `lean`, and each fist's `(x, y)` on
    the haft by side (+1 its right, behind; -1 its left, before), at z SPEAR_Z. `draw` slides the
    spear back through a windup and drives it forward in the thrust, and the fists go with it."""
    ox, oy = 0.22 + draw, 0.12
    angle = -lean - 0.05
    c, s = math.cos(angle), math.sin(angle)
    hands = {side: (ox + c * along, oy + s * along) for side, along in SPEAR_HANDS.items()}
    return (ox, oy), angle, hands


def fen_lurk(r, e, t):
    """The Fen Lurk: a marsh-dweller bent double under a cloak of rotten reed, its skin the mire's
    violet-grey, two pin-points of violet for eyes under its hood, a hooked spear of bone in its fists.
    Lurking, it is a hummock of reed sunk in the water with only the glint of its eyes and the spear's
    hook above it. Woken, it lopes hunched; through its windup it draws the spear back and sinks on its
    haunches, then springs and drives it forward. It holds the spear level in both fists, the right
    behind and the left before (`_spear_grip`), its elbows bent out. Slain, it pitches forward on its
    face."""
    seed = _seed(e)
    lit = e.alive
    eye = FEN_VIOLET if lit else GLOW_COLD
    if e.state == "idle":  # sunk to the shoulders among the reeds
        r.part("sphere", 0, 0.12, 0, 1.0, 0.5, 0.9, REED_DARK)
        for k in range(9):
            a = k * 2.4 + seed
            x, z = math.cos(a) * 0.35, math.sin(a) * 0.32
            r.part("cone", x, 0.45, z, 0.06, 0.6 + 0.1 * (k % 3), 0.06, REED, rx=z * 0.6, rz=-x * 0.6)
        for side in (-1, 1):
            r.part("cube", 0.42, 0.3, side * 0.07, 0.04, 0.03, 0.04, eye, glow=lit)
        _bar(r, (0.1, 0.15, 0.2), (0.55, 0.55, 0.25), 0.05, BONE)
        r.part("cone", 0.58, 0.6, 0.25, 0.06, 0.16, 0.06, BONE, rz=-0.7)
        return
    fall = death_fall(e, 0.6)
    skin = hit_tint((235, 215, 255)) if e.flashing else (96, 78, 108)
    shade = _dim(skin, 0.72)
    charge = _charge(e)
    thrust = 1.0 if e.state == "attack" else 0.0
    running = e.state == "chase"
    stride = math.sin(t * 9) * 0.45 if running else 0.0
    crouch = 0.16 * charge * (1 - thrust)
    if fall > 0:  # its spear drops from its fists and lies in the mud beside it
        _bar(r, (-0.4, 0.04, 0.45), (1.1, 0.04, 0.6), 0.05, _dim(BONE, 0.8))
        r.part("cone", 1.2, 0.04, 0.61, 0.07, 0.2, 0.07, BONE, rz=-math.pi / 2)
    with r.at(0.25 * fall, 0.35 * fall, 0, rz=-1.4 * fall):
        hip = 0.62 - crouch
        for side in (-1, 1):  # crooked legs, bent at the knee
            swing = stride * side
            with r.at(0, hip, side * 0.14, rz=swing - 0.5):
                r.part("cube", 0, -0.17, 0, 0.11, 0.36, 0.12, shade)  # the thigh
                with r.at(0, -0.34, 0, rz=1.0 - 0.3 * crouch * 4):
                    r.part("cube", 0, -0.18, 0, 0.09, 0.36, 0.1, skin)  # the shin
                    r.part("cube", 0.08, -0.37, 0, 0.22, 0.06, 0.12, shade)  # the foot
        lean = (-0.55 - 0.3 * charge + 0.25 * thrust) * (1 - fall)
        with r.at(0, hip, 0, rz=lean):  # the hunched body
            r.part("sphere", 0.05, 0.24, 0, 0.42, 0.5, 0.44, skin)  # the belly
            r.part("sphere", -0.04, 0.42, 0, 0.5, 0.42, 0.5, shade)  # the hump of its back
            for k in range(12):  # the reed cloak hanging off its back and shoulders
                a = (k / 12) * math.pi * 1.4 - math.pi * 0.2
                x, z = -math.sin(a) * 0.26 - 0.06, math.cos(a) * 0.3
                h = 0.5 + 0.12 * ((seed + k) % 3)
                r.part("cone", x, 0.32, z, 0.07, h, 0.07, REED if k % 2 else REED_DARK, rx=math.pi + z * 0.4)
            with r.at(0.2, 0.62, 0, rz=0.75 - 0.2 * charge):  # the head, thrust out low
                r.part("sphere", 0.08, 0, 0, 0.28, 0.24, 0.26, skin)
                r.part("cone", -0.02, 0.1, 0, 0.36, 0.3, 0.36, REED_DARK, rz=0.5)  # the reed hood
                r.part("cube", 0.2, -0.07, 0, 0.12, 0.06, 0.14, shade)  # the jaw
                for side in (-1, 1):
                    r.part("cube", 0.2, 0.02, side * 0.07, 0.04, 0.03, 0.04, eye, glow=lit)
            draw = -0.35 * charge * (1 - thrust) + 0.32 * thrust  # spear drawn back, then driven
            if fall > 0:  # its arms hang limp at its sides
                for side in (-1, 1):
                    _bar(r, (0.0, 0.42, side * 0.2), (0.02 - 0.2 * fall, 0.12, side * 0.22), 0.08, skin)
                return
            (ox, oy), angle, hands = _spear_grip(draw, lean)
            for side, (hx, hy) in hands.items():  # both arms on the spear: shoulder, bent elbow, fist
                shoulder = (0.0, 0.42, side * 0.2)
                hand = (hx, hy, SPEAR_Z)
                elbow = ((shoulder[0] + hx) / 2 - 0.04, (shoulder[1] + hy) / 2 - 0.1, side * 0.3)
                _bar(r, shoulder, elbow, 0.09, shade)  # the upper arm
                _bar(r, elbow, hand, 0.08, skin)  # the forearm
                r.part("cube", hx, hy, SPEAR_Z + side * 0.02, 0.12, 0.12, 0.13, skin, rz=angle)  # the fist
                r.part("cube", hx, hy + 0.05, SPEAR_Z + side * 0.06, 0.13, 0.04, 0.04, shade, rz=angle)
            with r.at(ox, oy, SPEAR_Z, rz=angle):  # the spear, held level in both fists
                _bar(r, (-0.7, 0, 0), (0.9, 0, 0), 0.05, _dim(BONE, 0.8))  # the haft
                r.part("cone", 0.98, 0, 0, 0.07, 0.2, 0.07, BONE, rz=-math.pi / 2)  # the point
                _bar(r, (0.86, 0, 0), (0.78, 0.1, 0), 0.035, BONE)  # the barb of its hook
                r.part("sphere", 0.9, -0.04, 0, 0.05, 0.06, 0.05, FEN_VIOLET, glow=lit)  # dripping fen
                for k in range(3):  # reed bindings round the haft, clear of its fists
                    r.part("cyl", -0.55 + k * 0.6, 0, 0, 0.08, 0.04, 0.08, REED_DARK, rz=math.pi / 2)


# --- the Bilegut -------------------------------------------------------------------------------------

BILE_SKIN = (120, 96, 132)
BILE_BELLY = (170, 150, 150)


def bilegut(r, e, t):
    """The Bilegut: a slug as long as a cart, its mottled violet-grey skin ridged along its back and
    blistered with glowing sacs of bile, two eye stalks swaying over a round mouth that glows within.
    It ripples along on its belly in a glistening track; through its windup it rears its fore-body
    and the mouth opens wide and bright, and spits. Slain, it deflates and its sacs go dark."""
    seed = _seed(e)
    lit = e.alive
    fall = death_fall(e, 0.8)
    skin = hit_tint((240, 220, 255)) if e.flashing else BILE_SKIN
    shade = _dim(skin, 0.75)
    glow = FEN_VIOLET if lit else GLOW_COLD
    charge = _charge(e)
    crawl = math.sin(t * 4) * 0.05 if e.state == "chase" else 0.0
    rear = 0.9 * charge if e.state in ("windup", "attack") else 0.15 * (e.state == "chase")
    squash = 1 - 0.5 * fall
    r.part("cube", -0.5, 0.01, 0, 1.6, 0.02, 0.6, _dim(FEN_VIOLET, 0.45))  # its glistening track
    segs = ((-0.85, 0.36), (-0.55, 0.46), (-0.2, 0.52), (0.15, 0.5))
    for i, (x, w) in enumerate(segs):  # the body, rippling as it crawls
        y = (0.24 + crawl * math.sin(i * 1.7)) * squash
        r.part("sphere", x, y, 0, 0.5, w * 0.95 * squash, w + 0.1, skin if i % 2 else shade)
        r.part("cube", x, y + w * 0.4 * squash, 0, 0.26, 0.06, 0.08, _dim(skin, 0.55))  # its ridge
        r.part("sphere", x, 0.08, 0, 0.46, 0.12, w + 0.14, BILE_BELLY)  # the pale skirt of its foot
        if i % 2 == 0 or i == 3:  # sacs of bile blistering its sides
            for side in (-1, 1):
                k = 1 + 0.08 * math.sin(t * 3 + i + side) * lit
                r.part("sphere", x, y + 0.08, side * w * 0.48, 0.16 * k, 0.14 * k, 0.12 * k, glow, glow=lit)
    r.part(
        "cone", -1.2, 0.14 * squash, 0, 0.26, 0.4, 0.22 * squash, shade, rz=math.pi / 2
    )  # its tapering tail
    with r.at(0.35, 0.22 * squash, 0, rz=rear * (1 - fall)):  # the fore-body, rearing to spit
        r.part("sphere", 0.16, 0.02, 0, 0.5, 0.4 * squash, 0.46, shade)
        r.part("sphere", 0.42, 0.04, 0, 0.36, 0.34 * squash, 0.38, skin)  # the head
        gape = 0.1 + 0.16 * charge
        r.part("cyl", 0.6, 0.04, 0, gape + 0.08, 0.05, gape + 0.08, _dim(skin, 0.5), rz=math.pi / 2)  # lips
        r.part("sphere", 0.61, 0.04, 0, 0.06, gape, gape, _dim(glow, 1.1), glow=lit)  # the glowing gullet
        for side in (-1, 1):  # eye stalks, swaying
            sway = math.sin(t * 2.5 + side + seed) * 0.25 * lit
            with r.at(0.4, 0.16, side * 0.1, rx=side * 0.35 + sway, rz=-0.3):
                r.part("cyl", 0, 0.16 * squash, 0, 0.04, 0.32 * squash, 0.04, shade)
                r.part("sphere", 0, 0.33 * squash, 0, 0.08, 0.08, 0.08, _dim(BILE_BELLY, 1.1))
            r.part("cone", 0.55, -0.02, side * 0.14, 0.05, 0.12, 0.05, shade, rz=-1.9)  # feelers


# --- the Mire Tyrant ---------------------------------------------------------------------------------

TYRANT_SHELL = (92, 84, 96)
TYRANT_UNDER = (150, 120, 128)


def mire_tyrant(r, e, t):
    """The Mire Tyrant: a crab-shelled brute the size of a hut, its domed back crusted with knobs and
    spines, reeds and old bones grown into it, slime hanging from its rim. It walks on six jointed
    legs; one claw is a crushing hammer, the other a long shear. Through a slam's windup both claws
    rise high and crash down; through a sweep's it draws the shear back across its body and scythes it
    round. Its eyes glow violet on their stalks. Slain, its legs buckle and it settles in the mud with
    its claws sprawled and its eyes dark."""
    seed = _seed(e)
    lit = e.alive
    fall = death_fall(e, 0.9)
    shell = hit_tint((236, 226, 240)) if e.flashing else TYRANT_SHELL
    shade = _dim(shell, 0.7)
    under = hit_tint((255, 230, 230)) if e.flashing else TYRANT_UNDER
    eye = FEN_VIOLET if lit else GLOW_COLD
    charge = _charge(e)
    move = e.attack_kind if e.state in ("windup", "attack") else None
    striking = e.state == "attack"
    walking = e.state == "chase"
    bob = math.sin(t * 5) * 0.04 if walking else 0.0
    body_y = (1.15 + bob - 0.1 * charge * (move == "slam")) * (1 - fall) + 0.62 * fall
    with r.at(0, body_y, 0, rx=0.12 * fall, rz=-0.06 * fall):
        r.part("sphere", 0, 0, 0, 2.2, 1.0, 2.0, shell)  # the domed carapace
        r.part("sphere", 0, -0.3, 0, 1.9, 0.5, 1.7, under)  # its pale underside
        r.part("cube", 0.95, -0.05, 0, 0.3, 0.3, 1.3, shade)  # the rim of its brow
        for k in range(7):  # knobs and spines crusting its back
            a = k * 2.1 + seed
            x, z = math.cos(a) * 0.6, math.sin(a) * 0.55
            r.part("cone", x, 0.46, z, 0.18, 0.28, 0.18, _dim(shell, 1.2), rx=z * 0.5, rz=-x * 0.5)
        for k in range(5):  # reeds grown up out of the muck on its back
            a = k * 1.3 + seed * 0.7
            x, z = math.cos(a) * 0.35 - 0.2, math.sin(a) * 0.4
            r.part("cone", x, 0.62, z, 0.05, 0.4, 0.05, REED if k % 2 else REED_DARK, rx=z * 0.3)
        _bar(r, (-0.5, 0.45, -0.35), (0.1, 0.5, -0.5), 0.07, BONE)  # old bones in the crust
        _bar(r, (-0.3, 0.48, 0.3), (0.2, 0.44, 0.45), 0.06, BONE)
        r.part("sphere", -0.45, 0.5, 0.1, 0.16, 0.14, 0.14, BONE)  # a skull half-swallowed by it
        for k in range(6):  # slime hanging from the rim
            z = -0.8 + k * 0.32
            r.part("cone", 0.7 - abs(z) * 0.3, -0.42, z, 0.06, 0.24, 0.06, _dim(FEN_VIOLET, 0.6), rx=math.pi)
        for side in (-1, 1):  # eyes on stalks over its brow
            with r.at(1.0, 0.2, side * 0.25, rz=-0.2 - 0.4 * fall):
                r.part("cyl", 0, 0.18, 0, 0.06, 0.36, 0.06, shade)
                r.part("sphere", 0, 0.38, 0, 0.13, 0.13, 0.13, eye, glow=lit)
        for side in (-1, 1):  # its mouthparts, working
            work = math.sin(t * 6 + side) * 0.15 * lit
            r.part("cube", 1.05, -0.28, side * 0.12, 0.2, 0.06, 0.06, under, ry=side * (0.3 + work))
    for side in (-1, 1):  # six legs, two joints each, buckling in death
        for j, x in enumerate((0.55, 0.0, -0.55)):
            step = math.sin(t * 5 + j * 2 + (side > 0) * math.pi) * 0.3 * walking
            splay = 0.5 + 0.5 * fall  # the upper leg rises from its side to the knee
            with r.at(x, body_y - 0.15, side * 0.8, ry=step, rx=-side * splay):
                r.part("cube", 0, 0, side * 0.35, 0.16, 0.16, 0.7, shade)  # the upper leg
                with r.at(0, 0, side * 0.7, rx=side * (1.7 - 0.1 * fall)):  # and plunges down to the mud
                    r.part("cube", 0, 0, side * 0.72, 0.12, 0.12, 1.43, shell)  # the lower leg
                    r.part(
                        "cone", 0, 0, side * 1.45, 0.1, 0.18, 0.1, _dim(shell, 0.55), rx=side * math.pi / 2
                    )
    # The claws. A slam lifts both overhead and crashes them down; a sweep draws the shear back across
    # its body and scythes it round.
    raise_ = 0.0
    sweep = 0.0
    if move == "slam":
        raise_ = 1.3 * charge * (0 if striking else 1) - 0.5 * striking
    elif move == "sweep":
        sweep = -1.2 * charge * (0 if striking else 1) + 1.3 * striking
    claw_y = body_y - 0.1
    hammer_side, shear_side = 1, -1
    with r.at(1.0, claw_y, hammer_side * 0.75, rz=raise_ * (1 - fall), ry=-0.3):  # the hammer claw
        r.part("cube", 0.35, 0, 0, 0.7, 0.24, 0.24, shade)  # its arm
        with r.at(0.7, 0, 0, rz=-0.3):
            r.part("cube", 0.3, 0, 0, 0.6, 0.3, 0.3, shell)  # its forearm
            r.part("sphere", 0.75, 0, 0, 0.7, 0.62, 0.6, _dim(shell, 1.1))  # the great crushing fist
            for k in range(4):  # knuckles of shell
                r.part("cone", 0.9, 0.2 - k * 0.13, 0.28, 0.12, 0.16, 0.12, _dim(shell, 0.6), rx=-math.pi / 2)
    with r.at(1.0, claw_y, shear_side * 0.75, rz=raise_ * (1 - fall), ry=0.3 + sweep):  # the shear claw
        r.part("cube", 0.35, 0, 0, 0.7, 0.2, 0.2, shade)
        with r.at(0.7, 0, 0, rz=-0.15):
            r.part("cube", 0.3, 0, 0, 0.6, 0.24, 0.24, shell)
            for k, open_ in enumerate((0.2 + 0.25 * charge, -0.15)):  # the two long blades of the shear
                with r.at(0.6, 0.04 - k * 0.08, 0, rz=open_):
                    r.part("cube", 0.45, 0, 0, 0.9, 0.12, 0.08, _dim(BONE, 0.85))
                    r.part("cone", 0.98, 0, 0, 0.08, 0.22, 0.06, BONE, rz=-math.pi / 2)


# --- props -------------------------------------------------------------------------------------------

BEACON_FLAME_Y = 3.1  # where the beacon's fire burns (mesh_builder.LIGHT_Y lights the fen from there)


def fen_beacon(r, t, lit=True):
    """A fen beacon: a squat watch-tower of mossy stone on a stepped footing, four timber posts at its
    corners holding up an iron fire-bowl where violet fire roars. Smothered, the bowl holds a sodden
    black heap of reed and ash."""
    r.part("cube", 0, 0.2, 0, 1.6, 0.4, 1.6, (255, 255, 255), tex="rough_stone")  # the footing
    r.part("cube", 0, 1.1, 0, 1.2, 1.5, 1.2, (255, 255, 255), tex="rough_stone")  # the tower
    r.part("cube", 0, 1.9, 0, 1.36, 0.14, 1.36, _dim((255, 255, 255), 0.8), tex="rough_stone")
    r.part("cube", 0, 2.2, 0, 1.0, 0.5, 1.0, (255, 255, 255), tex="rough_stone")
    for k in range(4):  # moss down its sides
        a = k * math.pi / 2 + 0.4
        r.part("cube", math.cos(a) * 0.61, 0.9, math.sin(a) * 0.61, 0.3, 0.8, 0.3, MOSS, ry=-a)
    for sx in (-1, 1):
        for sz in (-1, 1):
            r.part("cube", sx * 0.42, 2.55, sz * 0.42, 0.1, 0.7, 0.1, DEAD_WOOD)  # the posts
    r.part("cyl", 0, 2.9, 0, 1.0, 0.24, 1.0, IRON)  # the fire-bowl
    r.part("cyl", 0, 2.78, 0, 0.6, 0.1, 0.6, _dim(IRON, 0.7))
    if not lit:
        r.part("sphere", 0, 3.03, 0, 0.8, 0.22, 0.8, (34, 28, 34))  # a sodden black heap
        for k in range(3):
            r.part("cube", 0, 3.1, 0, 0.7, 0.05, 0.05, (50, 52, 30), ry=k * 1.05)
        return
    for k in range(3):  # the violet fire
        f = 1 + math.sin(t * 9 + k * 2.1) * 0.15
        a = k * 2.1
        r.part(
            "cone",
            math.cos(a) * 0.16,
            3.25,
            math.sin(a) * 0.16,
            0.5 * f,
            0.8 * f,
            0.5 * f,
            FEN_VIOLET,
            glow=True,
        )
    r.part("cone", 0, 3.3, 0, 0.32, 1.1 * (1 + math.sin(t * 13) * 0.12), 0.32, VIOLET_PALE, glow=True)


def dead_cypress(r, seed):
    """A dead fen cypress: a trunk flaring out into buttresses at the waterline, knobbed 'knees'
    poking up round it, a few bare crooked limbs and grey moss hanging off them."""
    h = 5.0 + (seed % 3) * 0.8
    for k in range(5):  # the flared buttresses
        a = k * 1.25 + seed
        r.part("cone", math.cos(a) * 0.35, 0.5, math.sin(a) * 0.35, 0.4, 1.2, 0.3, DEAD_WOOD, ry=-a)
    r.part("cyl", 0, h * 0.5, 0, 0.45, h, 0.45, DEAD_WOOD, tex="bark")
    for k in range(4):  # its knees
        a = k * 1.6 + seed * 0.3
        d = 1.0 + (k % 2) * 0.3
        r.part("cone", math.cos(a) * d, 0.25, math.sin(a) * d, 0.18, 0.5, 0.18, _dim(DEAD_WOOD, 0.85))
    for k in range(4):  # bare crooked limbs, moss hanging from each
        a = k * 1.7 + seed
        y = h * (0.6 + 0.1 * k)
        end = (math.cos(a) * 1.6, y + 0.7, math.sin(a) * 1.6)
        _bar(r, (0, y, 0), end, 0.14, DEAD_WOOD)
        r.part("cone", end[0] * 0.7, y - 0.3, end[2] * 0.7, 0.2, 1.0, 0.2, MOSS, rx=math.pi)
    r.part("cone", 0, h + 0.3, 0, 0.3, 0.8, 0.3, _dim(DEAD_WOOD, 0.8))  # the broken crown


def fen_reeds(r, seed):
    """A clump of reeds and cattails standing out of the mire."""
    for k in range(12):
        a = k * 2.39 + seed
        d = 0.15 + (k % 4) * 0.12
        x, z = math.cos(a) * d, math.sin(a) * d
        h = 1.0 + ((seed + k * 3) % 5) * 0.15
        lean = (x * 0.4, z * 0.4)
        r.part("cube", x, h / 2, z, 0.03, h, 0.03, REED if k % 3 else REED_DARK, rx=lean[1], rz=-lean[0])
        if k % 3 == 0:  # a cattail's brown head
            r.part("cyl", x + lean[0] * h * 0.5, h * 0.95, z + lean[1] * h * 0.5, 0.07, 0.22, 0.07, CATTAIL)


def sunken_hut(r, seed):
    """A marsh-folk hut on stilts, its legs rotted on one side so it lists into the mire: a plank
    floor, walls of wattle and timber, a sagging thatched roof, a black doorway."""
    with r.at(0, 0, 0, rz=0.14, rx=-0.06):
        for sx in (-1, 1):
            for sz in (-1, 1):
                r.part("cyl", sx * 0.8, 0.5, sz * 0.8, 0.14, 1.2, 0.14, DEAD_WOOD)  # its stilts
        r.part("cube", 0, 1.1, 0, 2.0, 0.12, 2.0, (255, 255, 255), tex="wood_plank")  # the floor
        for side in (-1, 1):
            r.part("cube", 0, 1.8, side * 0.9, 1.8, 1.3, 0.1, (255, 255, 255), tex="timber")
            r.part("cube", side * 0.9, 1.8, 0, 0.1, 1.3, 1.8, (255, 255, 255), tex="timber")
        r.part("cube", 0.96, 1.6, 0, 0.04, 0.9, 0.5, (14, 10, 14))  # its black doorway
        r.part("pyramid", 0, 2.8, 0, 2.6, 0.9, 2.6, (124, 110, 70))  # the sagging thatch
        r.part("cube", 0, 2.45, 0, 2.5, 0.1, 2.5, _dim((124, 110, 70), 0.7))


def stilt_posts(r, seed):
    """The rotted stumps of an old walkway's posts, standing out of the mire in a broken row, a
    plank or two still pegged across them."""
    for k in range(3):
        z = -0.7 + k * 0.7
        h = 0.6 + ((seed + k) % 3) * 0.25
        r.part("cyl", 0, h / 2, z, 0.18, h, 0.18, DEAD_WOOD)
    r.part("cube", 0, 0.7, -0.35, 0.3, 0.06, 0.8, (255, 255, 255), tex="wood_plank", rx=0.2)


# --- the great trees, the old moot's lever and its rotten bridges --------------------------------------

ROT_TIMBER = (96, 80, 60)
ROT_TIMBER_DARK = (64, 52, 40)
HOLLOW = (12, 9, 12)  # the black inside of a hollow trunk
SHELF = (176, 158, 124)  # pale shelf fungus on dead wood
SLIME = (120, 64, 150)  # violet slime off the mire, on wet timber
HANGING_MOSS = (96, 104, 86)
# Tints over the textures (which carry the wood's own dark tone): rotten boards, sodden bark, a great bole.
BOARD_TINT = (215, 200, 185)
SODDEN_BARK = (150, 132, 112)
BOLE = (128, 116, 102)


def huge_rotten_tree(r, seed, size=1.0):
    """A great dead fen tree, many times a dead cypress's height: a trunk two metres through, flared
    into buttress roots that run out over the mud, split near the top where the rot ate its heart out,
    a black hollow at its foot, crooked limbs hung with long beards of grey moss, shelf fungus up its
    sides and a few violet caps glowing among the roots. It fills its tile; its roots stay low past it."""
    with r.at(0, 0, 0, s=size):
        h = 12.0 + (seed % 4) * 1.1
        for k in range(7):  # the buttress roots, flaring out and down into the mud
            a = k * 0.9 + seed * 0.37
            ca, sa = math.cos(a), math.sin(a)
            reach = 2.2 + (k % 3) * 0.45
            _bar(r, (ca * 0.6, 2.4, sa * 0.6), (ca * reach, 0.05, sa * reach), 0.42, _dim(DEAD_WOOD, 0.62))
            _bar(
                r,
                (ca * reach, 0.05, sa * reach),
                (ca * (reach + 0.9), -0.1, sa * (reach + 0.9)),
                0.22,
                DEAD_WOOD,
            )
        r.part("cyl", 0, h * 0.28, 0, 2.2, h * 0.56, 2.2, BOLE, tex="bark")  # the great bole
        r.part("cyl", 0, 0.5, 0, 2.6, 1.0, 2.6, _dim(BOLE, 0.8), tex="bark")  # its swollen foot
        r.part("cube", 1.0, 1.0, 0.1, 0.3, 1.9, 0.8, HOLLOW)  # the hollow at its foot
        r.part("cube", 1.04, 2.0, 0.1, 0.32, 0.2, 0.5, HOLLOW)
        r.part("cyl", 0, h * 0.7, 0, 1.6, h * 0.32, 1.6, BOLE, tex="bark")  # the upper trunk
        for side in (-1, 1):  # split at the top into two leaning, broken leaders
            with r.at(0, h * 0.84, side * 0.35, rx=side * 0.22):
                r.part("cyl", 0, 1.3, 0, 0.8, 2.6, 0.75, BOLE, tex="bark")
                r.part("cone", 0, 2.9, 0, 0.75, 1.0 + (seed + side) % 2 * 0.6, 0.7, _dim(DEAD_WOOD, 0.7))
        for k in range(6):  # shelf fungus stepping up its sides
            a = k * 2.1 + seed
            y = 1.6 + k * h * 0.09
            rad = 1.1 if y < h * 0.56 else 0.8
            r.part("cyl", math.cos(a) * rad, y, math.sin(a) * rad, 0.7, 0.1, 0.7, SHELF)
        for k in range(6):  # crooked limbs, each bent once, hung with moss
            a = k * 1.05 + seed * 0.61
            ca, sa = math.cos(a), math.sin(a)
            y = h * (0.5 + 0.07 * k)
            reach = 3.2 + (seed + k) % 3 * 0.7
            elbow = (ca * reach * 0.55, y + 1.0, sa * reach * 0.55)
            bend = a + (0.5 if k % 2 else -0.5)
            end = (math.cos(bend) * reach, y + 2.0 + (k % 3) * 0.5, math.sin(bend) * reach)
            _bar(r, (ca * 0.6, y, sa * 0.6), elbow, 0.38, DEAD_WOOD)
            _bar(r, elbow, end, 0.22, DEAD_WOOD)
            for x, yy, z, long in (  # the beards of moss off the elbow and the tip
                (elbow[0], elbow[1], elbow[2], 2.2),
                (end[0], end[1], end[2], 1.4 + (k % 2)),
            ):
                r.part("cone", x, yy - long / 2, z, 0.34, long, 0.34, HANGING_MOSS, rx=math.pi)
        for k in range(9):  # knees standing out of the mud round it
            a = k * 0.71 + seed * 0.2
            d = 2.4 + (k % 3) * 0.5
            kh = 0.4 + ((seed + k) % 3) * 0.25
            r.part("cone", math.cos(a) * d, kh / 2, math.sin(a) * d, 0.32, kh, 0.32, _dim(DEAD_WOOD, 0.6))
        for k in range(4):  # violet caps glowing among the roots
            a = k * 1.7 + seed * 0.9
            x, z = math.cos(a) * 1.7, math.sin(a) * 1.7
            r.part("cyl", x, 0.12, z, 0.05, 0.24, 0.05, VIOLET_PALE)
            r.part("sphere", x, 0.26, z, 0.22, 0.09, 0.22, FEN_VIOLET, glow=True)


DRAWBRIDGE_POST = 3.6  # how tall the gallows posts on the bank stand, the chains hauling the span from them


def rotten_drawbridge(r, lowered, i=0, n=1):
    """One tile of a great rotten drawbridge `n` tiles long: tile `i` from the hinge, which lies on the
    -X edge of the first tile. The whole span swings on that one hinge as a single deck: raised (0) it
    stands upright on the bank, a wall of black timber `n` tiles tall; `lowered` (1) lays it across the
    sink-holes. Cross boards on two great stringers, warped and gapped, moss and violet slime on them; on
    the first tile also the gallows posts on the bank and the chains that let it down."""
    k = lowered * lowered  # it falls slowly at first, then crashes down
    lift = (1 - k) * math.pi / 2
    with r.at(-1.0 - 2.0 * i, 0, 0, rz=lift):
        x0 = 2.0 * i
        for z in (-0.92, 0.92):  # the two stringers, with a tie bolt where they meet the next tile
            r.part("cube", x0 + 1.0, -0.2, z, 2.0, 0.24, 0.2, SODDEN_BARK, tex="bark")
            r.part("cube", x0 + 0.05, -0.08, z, 0.1, 0.06, 0.24, _dim(IRON, 0.45))
        for b in range(5):  # the cross boards, warped and one in five split short
            x = x0 + 0.2 + b * 0.4
            short = (i * 5 + b) % 5 == 2
            w = 1.2 if short else 1.95
            zc = -0.35 if short else 0.0
            r.part(
                "cube", x, -0.04, zc, 0.36, 0.08, w, BOARD_TINT, tex="rotten_wood", rx=0.03 * ((b % 3) - 1)
            )
        r.part("sphere", x0 + 0.7, 0.02, 0.5, 0.5, 0.06, 0.4, MOSS)
        r.part("sphere", x0 + 1.5, 0.0, -0.6, 0.3, 0.05, 0.5, SLIME)
        if i == n - 1:  # the tip's iron lip, where the chains are made fast
            r.part("cube", x0 + 1.96, -0.1, 0, 0.08, 0.2, 1.9, _dim(IRON, 0.5))
    if i:
        return
    tip = 2.0 * n
    tx, ty = tip * math.cos(lift), tip * math.sin(lift)
    with r.at(-1.0, 0, 0):
        for z in (-1.05, 1.05):  # the gallows posts on the bank, and a chain from each to the tip
            r.part("cube", -0.2, DRAWBRIDGE_POST / 2, z, 0.34, DRAWBRIDGE_POST, 0.34, SODDEN_BARK, tex="bark")
            r.part("cube", -0.2, 0.8, z, 0.4, 0.14, 0.4, _dim(IRON, 0.45))  # an iron band
            _bar(r, (-0.05, DRAWBRIDGE_POST - 0.2, z), (tx, ty, z), 0.06, _dim(IRON, 0.55))
        r.part("cube", -0.2, DRAWBRIDGE_POST + 0.1, 0, 0.38, 0.3, 2.6, SODDEN_BARK, tex="bark")  # the lintel
        r.part("cone", -0.2, DRAWBRIDGE_POST - 0.6, 0.6, 0.18, 0.9, 0.18, HANGING_MOSS, rx=math.pi)


def rotten_lever(r, k):
    """The old moot's lever: a windlass of black, rotten timber on a squat plinth of mossy stone, its
    drum wound with rusted chain that runs off to the bridges, and a long gnarled arm swinging across
    it, from raised back (k=0) to thrown forward and down (k=1). Iron bands keep it from splitting."""
    r.part("cube", 0, 0.2, 0, 1.3, 0.4, 1.1, (255, 255, 255), tex="rough_stone")  # the plinth
    r.part("sphere", 0.4, 0.42, -0.35, 0.4, 0.08, 0.3, MOSS)
    for z in (-0.42, 0.42):  # the two uprights the drum turns between
        r.part("cube", 0, 0.95, z, 0.26, 1.1, 0.2, SODDEN_BARK, tex="bark")
        r.part("cube", 0, 0.7, z, 0.3, 0.1, 0.24, _dim(IRON, 0.45))
    drum_y = 1.3
    with r.at(0, drum_y, 0, rz=-2.4 * k):  # the drum turns as the arm is thrown
        r.part("cyl", 0, 0, 0, 0.42, 0.64, 0.42, BOARD_TINT, tex="rotten_wood", rx=math.pi / 2)
        for z in (-0.2, 0.0, 0.2):  # its wound chain
            r.part("cyl", 0, 0, z, 0.48, 0.07, 0.48, _dim(IRON, 0.55), rx=math.pi / 2)
    for z in (-0.25, 0.25):  # the chain running off it, down to the flagstones and away
        _bar(r, (-0.2, drum_y - 0.1, z), (-1.0, 0.04, z * 1.6), 0.05, _dim(IRON, 0.55))
    with r.at(0, drum_y, 0.36, rz=0.95 - 1.9 * k):  # the arm, on the drum's axle
        r.part("cube", 0, 0.8, 0, 0.16, 1.6, 0.14, SODDEN_BARK, tex="bark")
        r.part("cube", 0, 0.45, 0, 0.2, 0.08, 0.18, _dim(IRON, 0.45))
        r.part("cube", 0, 1.45, 0, 0.2, 0.3, 0.18, _dim(ROT_TIMBER, 0.75))  # the worn grip


# --- the great fen gate --------------------------------------------------------------------------------
# The fortress's gate in the curtain wall over the fen (`gate lever=fen_beacons model=great`): a row of
# gate tiles that share a lever is one portcullis under one gatehouse (`world.gate_runs`). Local +X runs
# through the gate, local +Z along the row; the wall it stands in is one tile (2 m) deep.

GREAT_GATE_OPEN = 5.6  # the height of its square opening, from the floor to the lintel
GREAT_GATE_LIFT = 5.3  # how far the portcullis rises into the masonry over it when it is open
GATE_BRICK = (255, 255, 255)  # black_brick, untinted, so it reads as the wall it is built into
GATE_TRIM = (214, 204, 206)
GATE_IRON = (58, 54, 62)
GATE_RIVET = (112, 106, 116)


def great_portcullis(r, open_t, i=0, n=1):
    """One tile's slice of the great gate's portcullis: tile `i` of a row `n` wide, the slices meeting
    into one grille of square black-iron bars on riveted rails, spiked at the foot. It winds up into
    the masonry over the opening as `open_t` runs to 1, its teeth still showing under the lintel."""
    lift = _ease(min(open_t, 1.0)) * GREAT_GATE_LIFT
    h = GREAT_GATE_OPEN
    with r.at(0, lift, 0):
        for k in range(5):  # the uprights, spaced evenly across the row's seams
            z = -0.8 + k * 0.4
            r.part("cube", 0, h / 2, z, 0.12, h, 0.12, GATE_IRON)
            r.part("lozenge", 0, -0.1, z, 0.08, 0.3, 0.08, GATE_IRON, rz=math.pi)  # its spike
        for y in (0.5, 1.6, 2.7, 3.8, 4.9):  # the rails, run edge to edge so the slices join
            r.part("cube", 0, y, 0, 0.16, 0.14, 2.0, _dim(GATE_IRON, 0.85))
            for k in range(5):
                for face in (-1, 1):
                    r.part("cube", face * 0.09, y, -0.8 + k * 0.4, 0.03, 0.07, 0.07, GATE_RIVET)
        if i in (0, n - 1):  # a heavier stile at each end, riding in the jambs' grooves
            z = -0.96 if i == 0 else 0.96
            r.part("cube", 0, h / 2, z, 0.18, h, 0.1, _dim(GATE_IRON, 0.8))


def fen_great_gate(r, n, t):
    """The gatehouse over the great fen gate, centred on its row of `n` tiles: deep jambs grooved for
    the portcullis, a square opening under a lintel of pale trim, the masonry over it built up to the
    curtain wall's top under a relieving arch of voussoirs on both faces, and over the wall a
    machicolated gate-house with merlons and slits lit by the fires within. On the towers either side
    an iron cresset on a bracket burns on the fen's face, and arrow slits glow up the towers."""
    w = 2.0 * n  # the opening's width
    h = GREAT_GATE_OPEN
    wall_top = 9.0
    for side in (-1, 1):  # the jambs, flush with the towers, grooved for the portcullis
        z = side * (w / 2 + 0.15)
        r.part("cube", 0, h / 2, z, 2.1, h, 0.3, GATE_BRICK, tex="black_brick")
        r.part("cube", 0, h / 2, side * (w / 2 + 0.01), 0.24, h, 0.04, (18, 16, 20))  # the groove
        for face in (-1, 1):  # a plinth at each jamb's foot
            r.part("cube", face * 1.0, 0.3, z, 0.3, 0.6, 0.5, GATE_TRIM, tex="rough_stone")
    # The masonry over the opening, up to the wall's top, and a lintel of pale trim across both faces.
    r.part("cube", 0, (h + wall_top) / 2, 0, 2.0, wall_top - h, w + 0.6, GATE_BRICK, tex="black_brick")
    for face in (-1, 1):
        x = face * 1.04
        r.part("cube", x, h + 0.2, 0, 0.12, 0.4, w + 0.6, GATE_TRIM, tex="rough_stone")
        rad = w / 2 - 0.2
        for k in range(9):  # the relieving arch, a half ring of voussoirs springing from the lintel
            a = math.pi * k / 8
            z, y = math.cos(a) * rad, h + 0.4 + math.sin(a) * (wall_top - h - 1.0)
            key = k == 4
            r.part(
                "cube", x, y, z, 0.16, 0.5 if key else 0.36, 0.7 if key else 0.55,
                GATE_TRIM, tex="rough_stone", rx=math.pi / 2 - a,
            )  # fmt: skip
        r.part("cube", x + face * 0.04, h + 0.62, 0, 0.04, 0.16, w - 0.2, (24, 22, 26))  # the lintel's shadow
    # The gate-house over the wall: a block between the towers, a gallery corbelled out on both faces
    # with its machicolations, merlons and two burning slits on each face.
    top = wall_top + 3.2
    r.part("cube", 0, (wall_top + top) / 2, 0, 2.0, top - wall_top, w + 0.4, GATE_BRICK, tex="black_brick")
    for face in (-1, 1):
        r.part("cube", face * 1.25, wall_top + 0.8, 0, 0.5, 0.3, w + 0.4, GATE_TRIM, tex="rough_stone")
        for k in range(int(w / 0.8) + 1):  # the corbels under the gallery
            r.part("cube", face * 1.2, wall_top + 0.4, -w / 2 + k * 0.8, 0.4, 0.5, 0.24, GATE_TRIM)
        for z in (-w / 4, w / 4):
            r.part("cube", face * 1.01, wall_top + 2.0, z, 0.03, 1.0, 0.24, FLAME, glow=True)
        for k in range(int(w / 1.2) + 1):  # its merlons
            r.part(
                "cube",
                face * 0.85,
                top + 0.45,
                -w / 2 + k * 1.2,
                0.3,
                0.9,
                0.6,
                GATE_BRICK,
                tex="black_brick",
            )
    # The cressets on the towers' fen faces (the towers' tiles run one tile out past the wall, -X).
    for side in (-1, 1):
        z = side * (w / 2 + 1.0)
        with r.at(-3.0, 5.2, z):
            _bar(r, (0, 0.6, 0), (-0.7, 0.0, 0), 0.1, GATE_IRON)  # the bracket
            r.part("cube", -0.04, 0.3, 0, 0.08, 1.0, 0.36, GATE_IRON)  # its plate on the wall
            r.part("cyl", -0.8, 0, 0, 0.6, 0.3, 0.6, GATE_IRON)  # the cresset
            r.part("cyl", -0.8, -0.24, 0, 0.3, 0.2, 0.3, _dim(GATE_IRON, 0.7))
            _flame(r, -0.8, 0.45, 0, 0.36, t + side)
        for face_x, y in ((-3.02, 9.5), (-3.02, 6.8)):  # arrow slits up the towers' fen faces
            r.part("cube", face_x, y, z, 0.03, 1.0, 0.24, FLAME, glow=True)
        with r.at(-1.0, 13.0, z):  # the tower's crown: a corbelled parapet and merlons
            r.part("cube", 0, 0.15, 0, 4.4, 0.3, 2.4, GATE_TRIM, tex="rough_stone")
            for mx in (-2.0, -1.0, 0.0, 1.0, 2.0):
                for mz in (-1.05, 1.05):
                    r.part("cube", mx, 0.75, mz, 0.5, 0.9, 0.3, GATE_BRICK, tex="black_brick")
            for mz in (-0.35, 0.35):
                for mx in (-2.05, 2.05):
                    r.part("cube", mx, 0.75, mz, 0.3, 0.9, 0.5, GATE_BRICK, tex="black_brick")
