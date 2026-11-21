"""Models for the Abandoned Prison under Harrowmere's well: the Hollow Inmates (the prisoners it was shut
on, gone hollow in their cells), the remains of those who died in their chains, and the faceless idols
of the old gods its chapel made them kneel to. Original low-poly models assembled from primitives;
like everything in `models`, they face +X (a wall prop's wall is at -X)."""

import math

from ashen_vault.render.parts import (
    BONE,
    DARK_IRON,
    IRON,
    WHITE,
    _bar,
    _dim,
    _mix,
    _swing_pose,
    death_fall,
    hand,
    hit_tint,
    ribcage,
    skull,
    walk_cycle,
)
from ashen_vault.render.rig import scale

INMATE_SKIN = (150, 136, 118)  # grey, sunless skin stretched over bone
INMATE_RAGS = (92, 80, 62)  # what is left of a prison smock
RAGS_DARK = (62, 52, 42)
GRIME = (48, 40, 34)
RUST = (104, 62, 40)
IDOL_STONE = (104, 98, 92)
IDOL_DARK = (66, 62, 60)
OFFERING = (110, 26, 22)  # old blood, dried on the idol's bowl


def _links(r, a, b, sag, n, rgb=IRON):
    """A chain of `n` links hanging from point a to point b, sagging `sag` metres in the middle."""
    pts = []
    for i in range(n + 1):
        k = i / n
        pts.append((_mix(a[0], b[0], k), _mix(a[1], b[1], k) - sag * 4 * k * (1 - k), _mix(a[2], b[2], k)))
    for i in range(n):
        _bar(r, pts[i], pts[i + 1], 0.045 if i % 2 else 0.03, rgb)


def _cuff(r, rgb=DARK_IRON):
    """An iron manacle round a limb at the origin, the limb running along Y."""
    r.part("cyl", 0, 0, 0, 0.15, 0.08, 0.15, rgb)
    r.part("cube", 0.08, 0, 0, 0.04, 0.05, 0.05, RUST)  # its hasp


def hollow_inmate(r, e, t):
    """A prisoner the prison was shut on, gone hollow in the dark: gaunt and grey, ribs showing through
    a torn smock, an iron collar on its neck, manacles on its wrists with a length of chain still
    running between them and a cuff on one ankle trailing links. Left alone it kneels where it was
    made to, head bowed and rocking; roused, it shambles at you hunched, raises its chained hands
    overhead and brings the chain down. Slain, its knees fold and it pitches forward onto its face."""
    fall = death_fall(e, 0.7)
    kneel = 1.0 if e.state == "idle" else 0.0
    swing = walk_cycle(e, t) * 0.55 * (1 - kneel)
    skin = hit_tint((236, 226, 214)) if e.flashing else INMATE_SKIN
    shade = _dim(skin, 0.72)
    rags = INMATE_RAGS
    rock = math.sin(t * 1.3) * 0.06 * kneel  # rocking at its prayers
    hip = 0.88 - 0.36 * kneel
    lean = 0.35 + 0.35 * kneel + rock + 1.1 * fall
    with r.at(0, -0.42 * fall, 0), r.at(0, hip, 0, rz=-lean), r.at(0, -hip, 0):
        # Legs: bare and knobbed; kneeling, the thighs stand under it and the shins lie flat behind.
        for i, (side, a) in enumerate(((-0.12, swing), (0.12, -swing))):
            thigh = a + 0.15 * kneel + lean * kneel + 1.3 * fall
            with r.at(0, hip, side, rz=thigh):
                r.part("cube", 0, -0.22, 0, 0.12, 0.44, 0.12, skin)
                r.part("cube", 0, -0.08, 0, 0.17, 0.18, 0.16, rags)  # the smock's ragged hem
                r.part("sphere", 0.02, -0.44, 0, 0.13, 0.11, 0.13, shade)  # the knee
                with r.at(0, -0.44, 0, rz=-0.2 - 1.72 * kneel - 1.8 * fall):
                    r.part("cube", 0, -0.2, 0, 0.1, 0.42, 0.1, skin)
                    r.part("cube", 0.06, -0.41, 0, 0.22, 0.05, 0.1, shade)  # the bare foot
                    if i == 0:  # an iron cuff on its left ankle, a few links trailing from it
                        with r.at(0, -0.34, 0):
                            _cuff(r)
                        _links(r, (-0.04, -0.36, 0.06), (-0.4, -0.42, 0.12), 0.06, 4)
        # Hips and the torn smock.
        r.part("cube", 0, 0.94, 0, 0.22, 0.18, 0.32, rags)
        r.part("cube", 0, 0.86, 0, 0.24, 0.05, 0.34, RAGS_DARK)  # a rope belt
        for j, z in enumerate((-0.13, -0.04, 0.05, 0.14)):  # strips of it hanging
            r.part("cube", 0.1, 0.72 - 0.03 * (j % 2), z, 0.02, 0.24 + 0.05 * (j % 3), 0.07, _dim(rags, 0.9))
        with r.at(0, 0.98, 0):
            # A chest of skin over bone, the smock torn open down its front.
            r.part("cube", -0.02, 0.28, 0, 0.2, 0.54, 0.32, skin)
            with r.at(0.06, 0.48, 0):
                ribcage(r, _dim(skin, 1.08), ribs=4, width=0.3, spacing=0.07, depth=0.08)
            r.part("cube", -0.04, 0.28, -0.13, 0.22, 0.5, 0.08, rags)  # the smock's two flaps
            r.part("cube", -0.04, 0.28, 0.13, 0.22, 0.5, 0.08, rags)
            r.part("cube", -0.1, 0.33, 0, 0.06, 0.46, 0.3, RAGS_DARK)  # its back
            r.part("cube", 0.09, 0.06, 0, 0.04, 0.12, 0.2, GRIME)  # the sunken belly
            r.part("cube", -0.12, 0.5, 0, 0.1, 0.06, 0.22, shade)  # the knobs of its spine
            # Neck, iron collar and the head, hung low, hair lank over its face.
            r.part("cube", 0.02, 0.62, 0, 0.08, 0.12, 0.08, skin)
            r.part("cyl", 0.02, 0.62, 0, 0.2, 0.06, 0.2, DARK_IRON)
            r.part("cube", -0.08, 0.6, 0, 0.04, 0.1, 0.04, RUST)  # the collar's ring
            with r.at(0.06, 0.78, 0, rz=-0.4 - 0.3 * kneel):
                r.part("sphere", 0, 0, 0, 0.2, 0.24, 0.19, skin)
                r.part("cube", 0.09, -0.02, 0, 0.04, 0.06, 0.14, GRIME)  # sunken eyes
                r.part("cube", 0.1, -0.1, 0, 0.03, 0.04, 0.08, (40, 26, 24))  # a slack mouth
                r.part("cube", 0.08, -0.12, 0, 0.06, 0.04, 0.1, shade)  # the jaw
                for z in (-0.08, -0.03, 0.03, 0.08):  # lank hair
                    r.part("cube", -0.02, -0.02, z, 0.18, 0.26, 0.03, (52, 46, 40))
            # Arms: thin as sticks, manacled at the wrists with a chain between them. They hang or
            # fold in prayer; roused, they rise overhead and bring the chain down.
            raise_ = _swing_pose(e, 0.35, 2.75, 0.55)
            arm = _mix(raise_, 0.9, kneel) - 0.4 * fall
            fore = 0.5 * kneel + 0.15
            reach = 0.3
            wrists = []
            for side in (-0.2, 0.2):
                with r.at(0, 0.5, side, rz=arm):
                    r.part("sphere", 0, 0, 0, 0.11, 0.11, 0.11, shade)  # the shoulder's bony knob
                    r.part("cube", 0, -0.15, 0, 0.08, 0.3, 0.08, skin)
                    with r.at(0, -reach, 0, rz=fore):
                        r.part("cube", 0, -0.14, 0, 0.07, 0.28, 0.07, skin)
                        with r.at(0, -0.24, 0):
                            _cuff(r)
                        with r.at(0, -0.3, 0):
                            hand(r, skin, 0.1, bony=True, curl=0.9)
                a = arm + fore
                wx = reach * math.sin(arm) + 0.24 * math.sin(a)
                wy = 0.5 - reach * math.cos(arm) - 0.24 * math.cos(a)
                wrists.append((wx, wy, side))
            _links(r, wrists[0], wrists[1], 0.18 * (1 - kneel * 0.5), 6)  # the chain between its hands


def prisoner_remains(r, seed):
    """A prisoner who died in their chains and was left to hang: a skeleton slumped against the wall
    behind (-X), its wrists still held up in iron rings on short chains, its rags rotted to shreds and
    its head fallen on its chest; the shin bones lie spilled on the floor before it."""
    lean = 0.08 * ((seed % 3) - 1)
    r.part("cube", -0.96, 1.85, 0, 0.06, 0.2, 1.0, DARK_IRON)  # the iron bar the chains hang from
    for side in (-1, 1):
        r.part("cube", -0.93, 1.85, side * 0.38, 0.04, 0.06, 0.06, RUST)  # its staples
        _links(r, (-0.9, 1.82, side * 0.38), (-0.72, 1.45, side * 0.32), 0.03, 3)
        with r.at(-0.72, 1.42, side * 0.32):
            _cuff(r)
    with r.at(-0.72, 0.0, 0, rx=lean):
        # Sat on the floor, its back to the wall, its knees drawn up.
        r.part("cube", 0.0, 0.12, 0, 0.18, 0.1, 0.3, BONE)  # the pelvis
        r.part("cube", 0.06, 0.18, 0, 0.12, 0.14, 0.34, INMATE_RAGS)  # the rag about its hips
        _bar(r, (0.0, 0.18, 0), (0.0, 0.66, 0), 0.05, _dim(BONE, 0.85))  # the spine
        with r.at(0.04, 0.6, 0):
            ribcage(r, BONE, ribs=4, width=0.3, spacing=0.07, depth=0.12)
        r.part("cube", 0.0, 0.66, 0, 0.08, 0.04, 0.36, BONE)  # the collarbones
        for side in (-1, 1):  # the arms, held up to the cuffs above
            sh = (0.0, 0.66, side * 0.18)
            el = (0.02, 1.05, side * 0.3)
            _bar(r, sh, el, 0.045, BONE)
            _bar(r, el, (0.0, 1.38, side * 0.32), 0.04, BONE)
            knee = (0.38, 0.42, side * 0.12)  # the legs, drawn up
            _bar(r, (0.04, 0.12, side * 0.1), knee, 0.05, BONE)
            _bar(r, knee, (0.62, 0.05, side * 0.14), 0.045, BONE)
        with r.at(0.1, 0.76, 0.02 * (seed % 2), rz=-0.7):  # the skull, fallen on its chest
            skull(r, BONE)
    for i in range(2 + seed % 2):  # bones fallen to the floor before it
        a = seed * 1.7 + i * 2.1
        r.part("cube", 0.2 + 0.25 * i, 0.03, math.sin(a) * 0.4, 0.38, 0.05, 0.05, _dim(BONE, 0.9), ry=a)


def old_idol(r, seed):
    """An idol of Lyra the Embracer, the old god the prison's chapel made its inmates kneel to: a squat,
    faceless figure of dark stone on a stepped plinth, its smooth blank head bowed a little toward
    whoever kneels before it, six long arms reaching out from its shoulders with their palms turned up,
    a bowl in its lap still black with old offerings, and its plinth carved with a ring of eyes all
    closed."""
    stone, dark = IDOL_STONE, IDOL_DARK
    r.part("cube", 0, 0.2, 0, 1.5, 0.4, 1.5, WHITE, tex="rough_stone")  # the stepped plinth
    r.part("cube", 0, 0.55, 0, 1.2, 0.3, 1.2, WHITE, tex="stone_brick")
    for i in range(5):  # the closed eyes carved round its face
        z = -0.44 + i * 0.22
        r.part("cube", 0.61, 0.55, z, 0.02, 0.04, 0.12, dark)
        r.part("cube", 0.615, 0.58, z, 0.02, 0.02, 0.14, _dim(stone, 1.1))  # the lid's crease
    with r.at(0, 0.7, 0, ry=(seed % 3 - 1) * 0.06):
        r.part("cube", -0.05, 0.3, 0, 0.8, 0.6, 0.9, stone, tex="rough_stone")  # crossed legs
        r.part("cone", -0.05, 0.95, 0, 0.75, 1.0, 0.8, stone, tex="rough_stone")  # the robed body
        r.part("cube", 0.1, 1.45, 0, 0.5, 0.5, 0.7, stone, tex="rough_stone")  # the shoulders
        with r.at(0.25, 0.65, 0):  # the bowl in its lap
            r.part("cyl", 0, 0, 0, 0.45, 0.14, 0.45, dark)
            r.part("cyl", 0, 0.05, 0, 0.36, 0.06, 0.36, OFFERING)
        with r.at(0.18, 1.95, 0, rz=-0.25):  # the blank head, bowed
            r.part("sphere", 0, 0, 0, 0.4, 0.5, 0.4, stone)
            r.part("cube", 0.12, -0.05, 0, 0.12, 0.3, 0.26, _dim(stone, 1.06))  # a smooth, faceless face
            r.part("cone", -0.04, 0.32, 0, 0.3, 0.3, 0.3, dark)  # a peaked crown
        for k, y in enumerate((1.6, 1.4, 1.2)):  # six arms, three to a side, palms up
            for side in (-1, 1):
                sh = (0.1, y, side * 0.3)
                el = (0.4 + 0.05 * k, y - 0.1, side * (0.62 + 0.08 * k))
                wr = (0.72 + 0.04 * k, y + 0.05 - 0.05 * k, side * (0.75 + 0.1 * k))
                _bar(r, sh, el, 0.13, stone)
                _bar(r, el, wr, 0.11, stone)
                r.part(
                    "cube", wr[0] + 0.06, wr[1] + 0.02, wr[2], 0.2, 0.05, 0.16, _dim(stone, 1.05)
                )  # a palm
        r.part("cube", 0.3, 1.3, 0, 0.04, 0.5, 0.06, dark)  # a crack down its breast


def altar_idol(r):
    """The old god behind the prison chapel's altar (`altar model=idol`): a tall faceless figure of dark
    stone standing at the back of the tile (-X), its blank head tipped back and four arms raised with
    their palms up toward the key floating over the altar."""
    stone, dark = IDOL_STONE, IDOL_DARK
    with r.at(-0.6, 0.32, 0):
        r.part("cube", 0, 0.12, 0, 0.7, 0.24, 0.9, dark)  # its plinth
        r.part("cone", 0, 0.95, 0, 0.62, 1.5, 0.7, stone, tex="rough_stone")  # the robed body
        r.part("cube", 0.02, 1.62, 0, 0.36, 0.34, 0.62, stone, tex="rough_stone")  # the shoulders
        with r.at(0.04, 2.02, 0, rz=0.3):  # the blank head, tipped back to the key
            r.part("sphere", 0, 0, 0, 0.34, 0.42, 0.34, stone)
            r.part("cube", 0.11, -0.03, 0, 0.1, 0.24, 0.22, _dim(stone, 1.06))  # its faceless face
            r.part("cone", -0.04, 0.28, 0, 0.26, 0.26, 0.26, dark)  # a peaked crown
        for k, y in enumerate((1.7, 1.5)):  # four arms raised, palms up beneath the key
            for side in (-1, 1):
                sh = (0.05, y, side * 0.26)
                el = (0.35, y + 0.05 + 0.08 * k, side * (0.42 + 0.12 * k))
                wr = (0.72, y + 0.35 - 0.1 * k, side * (0.28 + 0.14 * k))
                _bar(r, sh, el, 0.11, stone)
                _bar(r, el, wr, 0.09, stone)
                r.part("cube", wr[0] + 0.05, wr[1] + 0.02, wr[2], 0.18, 0.04, 0.14, _dim(stone, 1.05))
        for z in (-0.2, 0.0, 0.2):  # closed eyes carved down its robe
            r.part("cube", 0.33, 0.7 + abs(z), z, 0.02, 0.03, 0.1, dark)


LYRA_STONE = (156, 142, 120)  # the first city's sandstone, greyed by the cavern's damp
LYRA_DARK = (104, 92, 76)
LYRA_CRACK = (38, 32, 26)
LYRA_MOSS = (78, 96, 54)
LYRA_SCALE = 2.4  # how many times a chapel idol's girth she has
LYRA_STRETCH = 1.35  # and how much taller again she stands, for her tile's sake
LYRA_PLINTH = 1.76  # the height of her two-stepped plinth, in metres
LYRA_ARMS = (1.6, 1.4, 1.2)  # the shoulder height of each pair of arms, as on `old_idol`


def _lyra_roll(seed, i):
    """A fixed roll in 0..1 for the i-th choice made about the statue at `seed`."""
    h = (seed * 374761393 + i * 668265263) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 4294967296


def _fracture(r, x, y, z, size, rgb, roll):
    """The raw, broken face where stone snapped off at (x, y, z): two blocks set askew."""
    r.part("cube", x, y, z, size, size * 0.8, size, rgb, rx=roll * 2.1, ry=roll * 3.7, rz=roll * 1.3)
    r.part("cube", x, y, z, size * 0.7, size, size * 0.7, _dim(rgb, 0.85), rx=roll * 4.3, rz=roll * 2.9)


def _lyra_arm(k, side):
    """Shoulder, elbow and wrist of one of her six arms, in the figure's frame (as `old_idol` holds them)."""
    y = LYRA_ARMS[k]
    sh = (0.1, y, side * 0.3)
    el = (0.4 + 0.05 * k, y - 0.1, side * (0.62 + 0.08 * k))
    wr = (0.72 + 0.04 * k, y + 0.05 - 0.05 * k, side * (0.75 + 0.1 * k))
    return sh, el, wr


def _lyra_fallen_arm(r, seed, i, side, pieces, stone, dark):
    """A lost arm lying on the floor at her side, snapped where it broke: `pieces` are its lengths in the
    figure's units, the last ending in an upturned palm."""
    s = LYRA_SCALE
    th = 0.12 * s
    x = 0.1 + _lyra_roll(seed, 40 + i) * 1.1
    z = side * (1.45 + _lyra_roll(seed, 50 + i) * 0.45)
    with r.at(x, 0, z, ry=(_lyra_roll(seed, 60 + i) - 0.5) * 2.4, rz=0.05):
        px, bend = 0.0, 0.0
        for n, length in enumerate(pieces):
            end = (px + math.cos(bend) * length * s, th / 2, math.sin(bend) * length * s * 0.6)
            _bar(r, (px, th / 2, 0), end, th, stone)
            px = end[0]
            bend = 0.6 * side
            if n == 0:
                _fracture(r, 0, th / 2, 0, th * 1.1, dark, _lyra_roll(seed, 70 + i))  # where it snapped
        r.part("cube", px + 0.1 * s, th * 0.3, 0, 0.2 * s, 0.05 * s, 0.16 * s, _dim(stone, 1.05))  # its palm


def lyra_ruin(r, seed):
    """A colossus of Lyra the Embracer, the faceless old god the prison chapel's idols were carved after,
    raised by the first city and broken when it sank: the same squat, robed figure on a stepped plinth
    ringed with closed eyes, but some eight metres tall, deep cracks running through her, moss in her lap.
    Each one broke its own way (`seed`): of her six arms reaching out palms up, most are snapped at the
    elbow or the shoulder, and some of what broke off lies on the floor at her sides; her blank, bowed
    head still stands on some, is gone from others, and on some lies toppled in front of her. Nothing
    lies behind her, so she can stand with her back to a drop or a wall."""
    stone, dark = LYRA_STONE, LYRA_DARK
    s = LYRA_SCALE
    # The plinth: a broad, chipped lower step and an upper one carved with a ring of closed eyes.
    r.part("cube", 0, 0.4, 0, 2.3, 0.8, 2.3, WHITE, tex="rough_stone")
    r.part("cube", 0, 1.25, 0, 2.0, 0.9, 2.0, (236, 226, 210), tex="sunken_brick")
    r.part("cube", 0, 1.73, 0, 2.06, 0.06, 2.06, dark)  # its worn coping
    for face in range(4):
        with r.at(0, 1.25, 0, ry=face * math.pi / 2):
            for i in range(5):
                if _lyra_roll(seed, 100 + face * 5 + i) < 0.18:  # an eye chipped away
                    _fracture(r, 1.0, 0.05, -0.72 + i * 0.36, 0.18, dark, _lyra_roll(seed, 120 + i))
                    continue
                r.part("cube", 1.01, 0, -0.72 + i * 0.36, 0.03, 0.06, 0.2, LYRA_CRACK)  # the shut eye
                r.part("cube", 1.015, 0.05, -0.72 + i * 0.36, 0.03, 0.04, 0.24, _dim(stone, 1.12))  # its lid
    corner = 1 if _lyra_roll(seed, 1) < 0.5 else -1  # a corner of the lower step broken off
    _fracture(r, 0.95, 0.65, corner * 0.95, 0.5, _dim(stone, 0.8), _lyra_roll(seed, 2))
    r.part("cube", 1.35, 0.17, corner * 1.5, 0.45, 0.34, 0.4, WHITE, tex="rough_stone", ry=0.6)
    r.part("cube", 0.35, 0.82, corner * -0.3, 0.04, 0.05, 1.5, LYRA_CRACK, ry=0.4)  # a crack across a step
    r.part("cube", 0.6, 1.77, corner * 0.5, 0.7, 0.05, 0.6, LYRA_MOSS)  # moss on the coping

    head = _lyra_roll(seed, 3)  # < 0.45 standing, < 0.75 gone, else toppled before her
    lean = (_lyra_roll(seed, 4) - 0.5) * 0.08
    fallen = []
    with r.at(0, LYRA_PLINTH, 0, ry=(seed % 3 - 1) * 0.06, rx=lean, s=s):  # the figure, in idol units
        r.apply(scale(1, LYRA_STRETCH, 1))
        r.part("cube", -0.05, 0.3, 0, 0.8, 0.6, 0.8, stone)  # crossed legs
        r.part("cone", -0.05, 0.95, 0, 0.75, 1.0, 0.8, stone)  # the robed body
        r.part("cube", 0.1, 1.45, 0, 0.5, 0.5, 0.7, stone)  # the shoulders
        with r.at(0.25, 0.65, 0, rz=0.12 * corner):  # the bowl in her lap, cracked and full of moss
            r.part("cyl", 0, 0, 0, 0.45, 0.14, 0.45, dark)
            r.part("cyl", 0, 0.05, 0, 0.36, 0.06, 0.36, LYRA_MOSS)
            r.part("cube", 0.18, 0.02, 0, 0.12, 0.16, 0.02, LYRA_CRACK, ry=0.3)
        if head < 0.45:  # the blank head, bowed
            with r.at(0.18, 1.95, 0, rz=-0.25):
                r.part("sphere", 0, 0, 0, 0.4, 0.5, 0.4, stone)
                r.part("cube", 0.12, -0.05, 0, 0.12, 0.3, 0.26, _dim(stone, 1.06))  # a smooth, faceless face
                r.part("cone", -0.04, 0.32, 0, 0.3, 0.3, 0.3, dark)  # a peaked crown
                r.part("cube", 0.15, 0.1, 0.08, 0.02, 0.36, 0.02, LYRA_CRACK, rx=0.4)  # a crack over the face
        else:  # snapped at the neck
            r.part("cyl", 0.12, 1.76, 0, 0.26, 0.14, 0.26, stone)
            _fracture(r, 0.12, 1.84, 0, 0.24, dark, head)
        for j, (k, side) in enumerate((k, side) for k in range(3) for side in (-1, 1)):
            sh, el, wr = _lyra_arm(k, side)
            roll = _lyra_roll(seed, 10 + j)
            if roll < 0.22:  # still whole, reaching out with its palm up
                _bar(r, sh, el, 0.13, stone)
                _bar(r, el, wr, 0.11, stone)
                r.part("cube", wr[0] + 0.06, wr[1] + 0.02, wr[2], 0.2, 0.05, 0.16, _dim(stone, 1.05))
                continue
            if roll < 0.6:  # snapped below the elbow
                cut = 0.2 + 0.25 * _lyra_roll(seed, 20 + j)
                bp = tuple(_mix(a, b, cut) for a, b in zip(el, wr, strict=True))
                _bar(r, sh, el, 0.13, stone)
                _bar(r, el, bp, 0.11, stone)
                lost = (math.dist(bp, wr),)
            else:  # snapped off at the shoulder
                cut = 0.3 + 0.3 * _lyra_roll(seed, 20 + j)
                bp = tuple(_mix(a, b, cut) for a, b in zip(sh, el, strict=True))
                _bar(r, sh, bp, 0.13, stone)
                lost = (math.dist(bp, el), math.dist(el, wr))
            _fracture(r, *bp, 0.14, dark, roll)
            fallen.append((side, lost))
        r.part("cube", 0.3, 1.3, 0, 0.04, 0.5, 0.06, LYRA_CRACK)  # a crack down her breast
        r.part("cube", 0.27, 0.9, 0.12, 0.04, 0.7, 0.05, LYRA_CRACK, rx=0.5)  # running on down her robe
        r.part("cube", 0.0, 1.71, -0.2 * corner, 0.4, 0.03, 0.4, LYRA_MOSS)  # moss on a shoulder
    # What broke off: the first lost arms lie whole at her sides, the rest shattered into chunks.
    for i, (side, lost) in enumerate(fallen[:3]):
        _lyra_fallen_arm(r, seed, i, side, lost, stone, dark)
    for i in range(len(fallen) - 3):
        a = _lyra_roll(seed, 80 + i) * 2.6 - 1.3
        size = 0.3 + 0.2 * _lyra_roll(seed, 90 + i)
        r.part("cube", 1.2 + math.cos(a) * 0.5, size / 2, math.sin(a) * 1.6, size, size * 0.8, size * 1.2,
               _dim(stone, 0.9), ry=a * 2, rx=0.3)  # fmt: skip
    if head >= 0.75:  # her head, toppled and lying on its side before her
        side = 1 if _lyra_roll(seed, 5) < 0.5 else -1
        with r.at(1.6, 0.48 * s * 0.85, side * 1.1, rx=side * 1.45, ry=0.5 * side, s=s):
            r.part("sphere", 0, 0, 0, 0.4, 0.5, 0.4, stone)
            r.part("cube", 0.12, -0.05, 0, 0.12, 0.3, 0.26, _dim(stone, 1.06))
            r.part("cone", -0.04, 0.32, 0, 0.3, 0.3, 0.3, dark)
            _fracture(r, 0, -0.22, 0, 0.2, dark, head)
