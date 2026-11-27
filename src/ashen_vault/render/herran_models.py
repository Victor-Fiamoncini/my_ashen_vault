"""Herran, the Many-Handed, and what he throws at you: his model and the bursts of his moves (grafted
hands up out of the floor, his elixir's splash and its flask, a line of sunlight). Original low-poly
models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.ai.enemy import STATUE_BURST
from ashen_vault.render.parts import (
    HIT_GLOW,
    _bar,
    _dim,
    _ease,
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
from ashen_vault.util import rround

GILT = (196, 150, 70)  # gilt brass, the flask's collar
GLASS = (168, 196, 210)
SUN_GOLD = (255, 200, 96)
COLD = (52, 46, 40)  # a gold glow gone out
STITCH = (40, 22, 20)  # the black thread of Herran's grafts


def _windup_k(e):
    return min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0


def sunburst(r, glow, flame, t, radius=1.3):
    """A burst of sunlight from the floor (`hazards.Eruption` style "sun", Herran's `solar_gaze`): a
    ring of gold glyphs kindles on the floor (`glow` 0..1), then a column of sunlight bursts up out of
    it (`flame` 0..1)."""
    for i in range(10):
        a = i * math.tau / 10 + t * 0.5
        r.part("cube", math.cos(a) * radius, 0.03, math.sin(a) * radius, 0.24, 0.02, 0.07,
               _dim(SUN_GOLD, 0.3 + 0.7 * glow), ry=-a, glow=True)  # fmt: skip
    r.part(
        "cyl",
        0,
        0.02,
        0,
        radius * 1.7 * glow,
        0.01,
        radius * 1.7 * glow,
        _dim(SUN_GOLD, 0.35 * glow),
        glow=True,
    )
    if flame > 0:
        r.part(
            "cyl", 0, 2.0 * flame, 0, radius * 1.4, 4.0 * flame, radius * 1.4, _dim(SUN_GOLD, 0.7), glow=True
        )
        r.part("cyl", 0, 2.2 * flame, 0, radius * 0.6, 4.4 * flame, radius * 0.6, (255, 240, 200), glow=True)


# --- Herran, the Many-Handed ------------------------------------------------------------------------

COAT = (54, 40, 46)  # the rags of a natural philosopher's frock coat, once plum
HERRAN_SKIN = (204, 186, 170)
GRAFT_SEAM = (120, 40, 36)
EYE_GOLD = (255, 214, 110)
BRACE = (170, 130, 70)  # the brass surgical braces that hold him together


BEAST_HIDE = (92, 70, 58)  # the beast's arms: a bear's, coarse-pelted, sewn on below the rest
BEAST_CLAW = (40, 34, 30)
MAN_SKIN = (190, 158, 140)  # the men's arms, ruddier than his own
SCALPEL = (200, 206, 214)  # the blades sewn into his own fingers

# Which of his arms each rank is: his own, the topmost pair; the men's, the two pairs below; the
# beast's, the lowest pair (`_herran_arm`).
ARM_GROUPS = ("own", "men", "men", "beast")
# An arm's pose: (spread, lift, reach, plunge, sweep). `sweep` swings it about its root, forward round
# his body (+) or back behind him (-).
ARM_REST = (0.9, 0.2, 0.0, 0.0, 0.0)
ARM_DRAWN = (1.0, 1.0, -0.4, 0.0, -0.2)  # gathering a move: drawn up and back
ARM_TUCKED = (0.55, 0.35, -0.3, 0.0, -0.3)  # out of the way while other arms do the work
ARM_SPENT = (0.8, 0.0, 1.0, 0.0, 0.2)  # a plain blow
# Each move's (cocked, strike) for each group of arms: drawn back over the windup, then the stroke.
HERRAN_ARM_POSES = {
    "grasp_sweep": dict.fromkeys(ARM_GROUPS, ((1.2, 0.2, -0.3, 0.0, -0.6), (1.2, -0.4, 0.9, 0.0, 0.9))),
    "hand_rain": dict.fromkeys(ARM_GROUPS, ((0.8, 1.1, -0.2, 0.0, 0.0), (0.6, -0.2, 0.6, 1.0, 0.3))),
    "elixir_hurl": {
        "own": (ARM_TUCKED, ARM_TUCKED),
        "men": ((0.6, 1.3, -0.5, 0.0, -0.3), (0.9, 0.9, 1.0, 0.0, 0.6)),
        "beast": (ARM_TUCKED, ARM_TUCKED),
    },
    "embrace": dict.fromkeys(ARM_GROUPS, ((1.5, 0.6, 0.2, 0.0, -0.7), (0.1, 0.2, 1.2, 0.0, 1.1))),
    "solar_gaze": dict.fromkeys(ARM_GROUPS, ((1.4, 0.6, 0.2, 0.0, -0.4), (1.4, 0.6, 0.2, 0.0, -0.4))),
    "beast_rake": {
        "own": (ARM_TUCKED, ARM_TUCKED),
        "men": (ARM_TUCKED, ARM_TUCKED),
        "beast": ((1.4, 0.4, 0.1, 0.0, -1.0), (1.0, -0.3, 1.2, 0.0, 1.3)),
    },
    "scalpel_flurry": {
        "own": ((0.3, 0.9, 0.2, 0.0, 0.4), (0.2, 0.35, 1.35, 0.0, 0.9)),
        "men": (ARM_TUCKED, ARM_TUCKED),
        "beast": (ARM_TUCKED, ARM_TUCKED),
    },
    "hand_cage": dict.fromkeys(ARM_GROUPS, ((1.1, 1.3, -0.2, 0.0, -0.1), (1.2, -0.2, 0.5, 1.0, 0.2))),
    "flask_volley": {
        "own": (ARM_TUCKED, ARM_TUCKED),
        "men": ((0.7, 1.3, -0.4, 0.0, -0.3), (0.9, 1.0, 1.0, 0.0, 0.5)),
        "beast": (ARM_TUCKED, ARM_TUCKED),
    },
    "cradle_slam": dict.fromkeys(ARM_GROUPS, ((0.3, 1.7, 0.4, 0.0, 0.6), (0.2, -0.5, 1.2, 0.6, 1.1))),
}
SWEEPS = ("grasp_sweep", "beast_rake")  # strokes that travel over their attack rather than snapping
VOLLEY_ARMS = (2, 3, 4, 5)  # the men's arms (ranks 1, 2), each throwing its flask in turn
VOLLEY_BEAT = 0.12  # seconds between one arm's throw and the next


def _mix5(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


def herran_body(e, t):
    """(lean, gaze) of Herran's body: leaning into a move as he gathers it, his crown of eyes turned
    on you; leaning in hardest as his solar gaze or his clasped arms come down, his eyes blazing."""
    kind = getattr(e, "attack_kind", None)
    if e.state == "windup":
        k = _windup_k(e)
        if kind == "cradle_slam":
            return -0.35 * k, 0.6 * k  # reared back, his arms high over him
        return -0.15 * k, 0.4 * k
    if e.state == "attack":
        return {
            "grasp_sweep": (0.2, 0.2),
            "hand_rain": (0.4, 0.2),
            "elixir_hurl": (0.1, 0.3),
            "embrace": (0.35, 0.5),
            "solar_gaze": (0.45, 1.0),
            "beast_rake": (0.3, 0.3),
            "scalpel_flurry": (0.3, 0.6),
            "hand_cage": (0.45, 0.4),
            "flask_volley": (0.1, 0.5),
            "cradle_slam": (0.55, 0.7),
        }.get(kind, (0.3, 0.2))
    if e.state in ("recover", "hurt"):
        return -0.1, 0.0
    return 0.0, 0.0


def herran_arm_pose(e, i, t):
    """The pose of the `i`th of his eight arms: fanned and swaying idle; for each move its own group of
    arms at its own work (HERRAN_ARM_POSES) and the rest held out of the way: drawn back over the
    windup, then the stroke, a sweep travelling round him over its attack, settling back as he
    recovers. His own arms' scalpels cut in turn, one side then the other; the men's arms throw their
    flasks of a volley one after another."""
    sway = math.sin(t * 1.3 + i * 0.7) * 0.12
    rest = (ARM_REST[0] + sway, ARM_REST[1] + sway, 0.0, 0.0, 0.0)
    kind = getattr(e, "attack_kind", None)
    group = ARM_GROUPS[i // 2]
    poses = HERRAN_ARM_POSES.get(kind)
    cocked, strike = poses[group] if poses else (ARM_DRAWN, ARM_SPENT)
    if e.state == "windup":
        return _mix5(rest, cocked, _ease(_windup_k(e)))
    if e.state == "attack":
        if kind == "scalpel_flurry" and group == "own":
            cut = getattr(e, "combo_swing", 0)
            return strike if (cut + i) % 2 else cocked  # one blade cuts as the other draws back
        start = 0.0
        if kind == "flask_volley" and i in VOLLEY_ARMS:
            start = VOLLEY_ARMS.index(i) * VOLLEY_BEAT
        span = 0.35 if kind in SWEEPS else 0.15
        k = min(max(e.state_t - start, 0.0) / span, 1.0)
        return _mix5(cocked, strike, _ease(k))
    if e.state == "recover" and poses:
        return _mix5(strike, rest, _ease(min(e.state_t / max(e.recover_time, 1e-3), 1)))
    if e.state in ("recover", "hurt"):
        return (0.9 + sway, 0.1, 0.1, 0.0, 0.0)
    return rest


def holds_flask(e, i):
    """Whether the `i`th arm holds a flask of his elixir: a man's arm, over the windup of an elixir
    hurl (the first of them) or a volley (all four), and through the attack until it throws."""
    if i not in VOLLEY_ARMS or e.state not in ("windup", "attack"):
        return False
    kind = getattr(e, "attack_kind", None)
    if kind == "elixir_hurl":
        return i == VOLLEY_ARMS[0] and e.state == "windup"
    if kind != "flask_volley":
        return False
    return e.state == "windup" or e.state_t < VOLLEY_ARMS.index(i) * VOLLEY_BEAT + 0.08


def _herran_arm(r, e, i, pose, skin, seam, glow, raging):
    """The `i`th of his eight grafted arms, out of his back: upper arm and forearm (`_bar`s), a seam
    where it was sewn on, and its hand. His own arms (the topmost pair) are long and pale, scalpels
    sewn into their fingers; the men's (the two pairs below) are ruddier and thicker, stitched at the
    elbow; the beast's (the lowest) are thick and furred, with hooked black claws."""
    spread, lift, reach, plunge, sweep = pose
    side = 1 if i % 2 else -1
    rank = i // 2  # 0 the topmost pair, 3 the lowest
    group = ARM_GROUPS[rank]
    flash = skin != HERRAN_SKIN
    flesh = skin if group == "own" or flash else (MAN_SKIN if group == "men" else BEAST_HIDE)
    root = (-0.25, 3.05 - rank * 0.32, side * (0.28 + rank * 0.05))
    out = 0.35 + 0.35 * rank
    fan = spread * (0.5 + 0.28 * rank)
    elbow = (
        0.3 + 0.7 * reach,
        (0.6 - 0.3 * rank) * lift - 0.8 * plunge,
        side * (out + fan),
    )
    hand = (
        elbow[0] + 0.5 + 0.9 * reach + 0.4 * plunge,
        elbow[1] - 0.5 + 0.9 * lift - (elbow[1] + root[1] - 0.1) * plunge,
        elbow[2] + side * (0.3 + 0.6 * fan) * (1 - 0.5 * reach),
    )
    thick = {"own": 0.11, "men": 0.13, "beast": 0.19}[group]
    with r.at(*root, ry=side * sweep):  # swung about its root, forward round him or back
        _bar(r, (0, 0, 0), elbow, thick, flesh)
        _bar(r, elbow, hand, thick * 0.85, flesh)
        r.part("cyl", 0, 0, 0, thick * 1.8, 0.06, thick * 1.8, seam, glow=raging and glow)  # its seam
        r.part("sphere", *elbow, thick * 1.2, thick * 1.2, thick * 1.2, _dim(flesh, 0.85))  # the elbow
        if group == "men":  # a ring of black stitches round the elbow, where two men were made one
            r.part("cyl", *elbow, thick * 1.5, 0.03, thick * 1.5, STITCH)
        if group == "beast":  # coarse tufts of its pelt along the forearm
            for k in (0.3, 0.6):
                at = tuple(a + (b - a) * k for a, b in zip(elbow, hand, strict=True))
                r.part("cube", at[0], at[1] + thick * 0.5, at[2], 0.12, 0.06, 0.1, _dim(BEAST_HIDE, 0.75))
        with r.at(*hand):
            if group == "beast":  # a broad paw and four hooked claws
                r.part("cube", 0, 0, 0, 0.24, 0.14, 0.24, flesh)
                for f in range(4):
                    r.part("cone", 0.16, -0.06, (f - 1.5) * 0.06, 0.05, 0.18, 0.05, BEAST_CLAW, rz=-2.0)
            else:
                r.part("cube", 0, 0, 0, 0.16, 0.1, 0.14, flesh)  # the palm
                for f in range(4):  # long fingers
                    r.part("cube", 0.12, -0.02, (f - 1.5) * 0.045, 0.16, 0.025, 0.025, flesh, rz=-0.3)
                if group == "own":  # a scalpel sewn into the forefinger, glinting
                    r.part("cube", 0.28, -0.06, -0.06, 0.2, 0.02, 0.03, SCALPEL, rz=-0.3)
            if holds_flask(e, i):  # a flask of his elixir, green and glowing
                r.part("cyl", 0.08, 0.14, 0, 0.14, 0.24, 0.14, (120, 200, 100), glow=True)
                r.part("cyl", 0.08, 0.3, 0, 0.06, 0.1, 0.06, GILT)  # its gilt collar


def herran(r, e, t):
    """Herran, the Many-Handed: Lyra's son, a towering gaunt figure in the rags of a natural
    philosopher's frock coat, on long thin legs; eight grafted arms (a beast's, men's, his own) fan out
    of his back, sewn on at seams that weep; his head is split open into a crown of lidless gold eyes,
    and brass surgical braces strap his ribs and his neck together. In his second phase the braces
    have burst and hang loose, every seam burns gold, his eyes blaze and his crown of them opens wider.
    Slain, he folds to his knees and slumps forward, his arms spread on the floor round him."""
    fall = death_fall(e, 1.0)
    dead = e.state == "dead"
    raging = bool(getattr(e, "phase2", False)) and not dead
    lean, gaze = herran_body(e, t) if not dead else (0.0, 0.0)
    skin = hit_tint((250, 230, 220)) if e.flashing else HERRAN_SKIN
    coat = hit_tint((150, 120, 130)) if e.flashing else COAT
    glow = not dead
    eye = (HIT_GLOW if e.flashing else EYE_GOLD) if glow else COLD
    seam = EYE_GOLD if raging else GRAFT_SEAM
    kneel = fall  # slain, his legs fold and he sinks
    for side in (-1, 1):  # the long thin legs
        with r.at(0, 1.6 - 1.0 * kneel, side * 0.3, rz=0.9 * kneel):
            r.part("cube", 0, -0.4, 0, 0.16, 0.8, 0.16, coat)  # the thigh, in its breeches
            with r.at(0, -0.8, 0, rz=-2.45 * kneel):  # kneeling, the shin lies along the floor behind
                r.part("cube", 0, -0.4, 0, 0.12, 0.8, 0.12, skin)  # the shin, bare and gaunt
                r.part("cube", 0.1, -0.82, 0, 0.32, 0.06, 0.14, _dim(skin, 0.8))  # the long foot
    # Everything above the hips, turned about them: leaning into a move, or slumped forward in death.
    with r.at(0, 1.75 - 1.0 * kneel, 0, rz=-lean - 0.6 * fall), r.at(0, -1.75, 0):
        r.part("cube", 0, 1.75, 0, 0.42, 0.3, 0.62, coat)  # the hips
        for side in (-1, 1):  # the coat's tails, hanging ragged
            r.part("cube", -0.18, 1.3, side * 0.18, 0.05, 0.9, 0.26, _dim(coat, 0.85), rz=0.15)
        r.part("cube", 0, 2.35, 0, 0.36, 0.95, 0.55, skin)  # the gaunt torso
        for i in range(4):  # ribs standing out
            r.part("cube", 0.17, 2.1 + i * 0.16, 0, 0.03, 0.04, 0.5, _dim(skin, 0.8))
        r.part("cube", -0.02, 2.5, 0, 0.4, 0.8, 0.64, coat)  # the coat over his back and shoulders
        r.part("cube", 0.2, 2.5, 0, 0.04, 0.7, 0.18, (226, 214, 190))  # a stained shirt-front
        if not raging:  # the braces strapped round him
            for y in (2.15, 2.45, 2.75):
                r.part("cube", 0, y, 0, 0.44, 0.05, 0.66, BRACE)
                r.part("cube", 0.22, y, 0.1, 0.03, 0.08, 0.06, _dim(BRACE, 0.7))  # its buckle
            r.part("cyl", 0.02, 3.15, 0, 0.3, 0.2, 0.3, BRACE)  # the collar round his neck
        else:  # burst, hanging loose, and the seams down his chest burning
            for y in (2.15, 2.45):
                r.part("cube", 0.2, y - 0.1, 0.25, 0.03, 0.3, 0.05, BRACE, rx=0.6)
            for i in range(3):
                r.part("cube", 0.19, 2.1 + i * 0.3, -0.1 + i * 0.08, 0.02, 0.24, 0.03, EYE_GOLD, glow=True)
        r.part("cyl", 0.02, 3.25, 0, 0.16, 0.25, 0.16, skin)  # the neck
        with r.at(0.06, 3.55, 0, rz=-0.3 * gaze):  # the head, split open into a crown of eyes
            r.part("sphere", 0, 0, 0, 0.26, 0.24, 0.24, skin)
            r.part("wedge", 0.15, -0.12, 0, 0.14, 0.08, 0.16, _dim(skin, 0.85))  # what is left of the jaw
            opened = 0.25 + (0.15 if raging else 0) + 0.1 * gaze
            for i in range(7):  # the lidless eyes, ringed up and out from the split
                a = (i - 3) * 0.42
                x, y, z = 0.12, 0.1 + math.cos(a) * opened, math.sin(a) * opened
                size = 0.07 + 0.02 * (i % 2) + (0.03 if raging else 0)
                r.part("sphere", x, y, z, size * 1.3, size * 1.3, size * 1.3, _dim(skin, 0.75))  # its socket
                r.part("sphere", x + 0.03, y, z, size, size, size, eye, glow=glow)
            if raging:  # the blaze behind them
                r.part("sphere", 0.1, 0.25, 0, 0.3, 0.3, 0.3, _dim(EYE_GOLD, 0.6), glow=True)
        with r.at(0, -0.1 * fall, 0):
            for i in range(8):
                pose = herran_arm_pose(e, i, t) if not dead else (0.8, 0.6, 0.2, 0.0, 0.0)
                _herran_arm(r, e, i, pose, skin, seam, glow, raging)


def graft_hands(r, glow, flame, t, radius=1.0):
    """Herran's `hand_rain` (`hazards.Eruption` style "grafts"): a seam of gold splits the floor
    (`glow` 0..1), then pale arms burst up out of it, clutching (`flame` 0..1)."""
    r.part("cube", 0, 0.02, 0, radius * 1.6, 0.02, 0.12, _dim(EYE_GOLD, 0.3 + 0.7 * glow), glow=True)
    r.part("cube", 0, 0.02, 0, 0.12, 0.02, radius * 1.2, _dim(EYE_GOLD, 0.2 + 0.5 * glow), glow=True)
    if flame > 0:
        for i in range(4):
            a = i * math.tau / 4 + 0.4
            x, z = math.cos(a) * radius * 0.45, math.sin(a) * radius * 0.45
            h = 1.4 * flame
            r.part("cube", x, h / 2, z, 0.12, h, 0.12, HERRAN_SKIN, rz=0.2 * math.sin(t * 6 + i))
            r.part("cube", x, h + 0.05, z, 0.18, 0.08, 0.16, _dim(HERRAN_SKIN, 0.85))


def elixir_splash(r, glow, flame, t, radius=1.4):
    """Herran's `elixir_hurl` (`hazards.Eruption` style "elixir"): where the flask will land a ring
    of green glows on the floor (`glow`), then it bursts into a toxic splash (`flame`)."""
    green = (120, 210, 100)
    r.part("cyl", 0, 0.02, 0, radius * 2 * glow, 0.01, radius * 2 * glow, _dim(green, 0.4), glow=True)
    if flame > 0:
        r.part(
            "sphere",
            0,
            0.4 * flame,
            0,
            radius * 1.6 * flame,
            0.8 * flame,
            radius * 1.6 * flame,
            green,
            glow=True,
        )
        for i in range(5):
            a = i * math.tau / 5 + t
            r.part("sphere", math.cos(a) * radius * flame, 0.9 * flame, math.sin(a) * radius * flame, 0.12, 0.12, 0.12,
                   (170, 240, 140), glow=True)  # fmt: skip


def elixir_flask(r, t):
    """The flask Herran lobs, tumbling as it flies."""
    with r.at(0, 0, 0, rz=t * 8):
        r.part("sphere", 0, 0, 0, 0.22, 0.22, 0.22, (120, 200, 100), glow=True)
        r.part("cyl", 0, 0.16, 0, 0.08, 0.14, 0.08, GLASS)
        r.part("cyl", 0, 0.25, 0, 0.1, 0.05, 0.1, GILT)


# --- Herran's household and his keep's guardians ------------------------------------------------------

TABARD = (58, 30, 40)  # the household's tabards: a deep wine gone almost black in the rain
TABARD_TRIM = (150, 118, 70)
BLACKENED = (46, 46, 52)  # blackened steel, the household's plate
BLACKENED_EDGE = (92, 92, 102)
PALLID = (190, 170, 156)  # a grafted man's skin, grey with the cold
LANTERN = (255, 196, 110)
EMBER_EYE = (255, 120, 50)  # the eye of the gate's fire in a Warden's helm
STATUE_STONE = (104, 104, 112)  # the peak's own grey stone, cut into the sentinels
STATUE_DARK = (70, 70, 78)
STATUE_MOSS = (70, 84, 66)
CRACK_FIRE = (255, 130, 50)


def _hand_device(r, x, y, z, size, rgb):
    """Herran's device on a tabard or a shield: an open hand, palm out, fingers spread, a sun in its palm."""
    r.part("cube", x, y, z, 0.02, size * 0.5, size * 0.45, rgb)  # the palm
    for f in range(4):
        r.part("cube", x, y + size * 0.42, z + (f - 1.5) * size * 0.12, 0.02, size * 0.34, size * 0.07, rgb)
    r.part("cube", x, y + size * 0.1, z - size * 0.32, 0.02, size * 0.09, size * 0.24, rgb, rx=0.6)  # thumb
    r.part("cyl", x + 0.01, y, z, size * 0.18, 0.02, size * 0.18, SUN_GOLD, rz=math.pi / 2)


def halberd(r, length=2.3, steel=BLACKENED_EDGE):
    """A household halberd in a `held` frame: a long ash haft along +X banded in iron, and at its head
    an axe blade, a back hook and a long spike, a tassel of wine-red cloth under the head."""
    r.part("cube", length * 0.4 - 0.4, 0, 0, length, 0.05, 0.05, (78, 58, 40))  # the haft
    for k in (0.2, 0.5, 0.8):
        r.part("cube", -0.4 + length * k, 0, 0, 0.05, 0.07, 0.07, BLACKENED)  # its bands
    head = length * 0.9 - 0.4
    r.part("cube", head, 0, 0, 0.24, 0.08, 0.08, BLACKENED)  # the socket
    r.part("wedge", head + 0.02, 0.2, 0, 0.3, 0.34, 0.03, steel)  # the axe blade
    r.part("cube", head + 0.02, 0.38, 0, 0.32, 0.03, 0.035, _bright_edge(steel))  # its edge
    r.part("wedge", head, -0.14, 0, 0.12, 0.2, 0.03, steel, rz=math.pi)  # the back hook
    r.part("cone", head + 0.34, 0, 0, 0.06, 0.44, 0.06, steel, rz=-math.pi / 2)  # the spike
    r.part("cube", head - 0.18, -0.1, 0, 0.04, 0.16, 0.04, TABARD)  # the tassel


def _bright_edge(rgb):
    return tuple(min(c + 50, 255) for c in rgb)


def _hanging_arm(r, x, y, z, side, reach, skin, sleeve, seam):
    """A grafted arm sewn on below the first pair: a seam of black stitches round its root, the upper
    arm in a torn sleeve, the bare forearm reaching out along +X by `reach` (0 hanging, 1 held out)."""
    with r.at(x, y, z):
        r.part("cyl", 0, 0, 0, 0.12, 0.05, 0.12, seam, rx=math.pi / 2)  # the seam
        for k in (-1, 1):
            r.part("cube", 0.02, k * 0.04, side * 0.03, 0.02, 0.02, 0.06, STITCH)  # its stitches
        with r.at(0, 0, side * 0.04, rz=0.2 + 1.2 * reach, rx=side * 0.25):
            r.part("cube", 0, -0.15, 0, 0.09, 0.3, 0.09, sleeve)
            r.part("sphere", 0, -0.3, 0, 0.06, 0.06, 0.06, _dim(skin, 0.85))  # the elbow
            with r.at(0, -0.3, 0, rz=0.5 - 0.4 * reach):
                r.part("cube", 0, -0.13, 0, 0.07, 0.26, 0.07, skin)
                r.part("cube", 0, -0.3, 0, 0.08, 0.08, 0.1, skin)  # the hand
                for f in range(3):
                    r.part("cube", 0.03, -0.37, (f - 1) * 0.03, 0.02, 0.07, 0.02, skin, rz=0.3)


def grafted_footman(r, e, t):
    """A Grafted Footman of Herran's household: a gaunt man grown too tall, in a long wine-dark tabard
    bearing Herran's open hand over blackened mail, a tall pointed helm with a fluted brim. A second
    pair of arms is sewn on below his first, one holding up a lantern, the other clutching at nothing;
    his first pair works the halberd. Slain, he topples back and the lantern goes out."""
    fall = death_fall(e, 0.8)
    lit = e.alive
    swing = walk_cycle(e, t) * 0.6
    cloth = hit_tint((240, 200, 210)) if e.flashing else TABARD
    plate = hit_tint((230, 230, 240)) if e.flashing else BLACKENED
    skin = hit_tint((250, 230, 220)) if e.flashing else PALLID
    lean = (-0.25 if e.state == "hurt" else 0.0) + 1.4 * fall
    with r.at(-0.3 * fall, 0.3 * fall, 0, rz=lean):
        for side, a in ((-0.15, swing), (0.15, -swing)):  # the long legs: mail chausses and boots
            with r.at(0, 1.15, side, rz=a + 0.3 * fall):
                r.part("cube", 0, -0.28, 0, 0.15, 0.56, 0.15, plate, tex="iron_plate")
                r.part("sphere", 0.05, -0.56, 0, 0.1, 0.1, 0.1, _dim(plate, 1.2))  # the knee
                with r.at(0, -0.56, 0, rz=-0.1 - 0.3 * fall):
                    r.part("cube", 0, -0.27, 0, 0.13, 0.54, 0.13, (40, 30, 26))  # the boot
                    r.part("cube", 0.07, -0.54, 0, 0.3, 0.07, 0.15, (32, 24, 20))
        r.part("cube", 0, 1.2, 0, 0.32, 0.16, 0.48, plate, tex="iron_plate")  # the hips
        r.part("cube", 0, 1.22, 0, 0.36, 0.06, 0.5, (40, 30, 26))  # the belt
        r.part("cube", 0.03, 1.22, 0, 0.36, 0.08, 0.1, TABARD_TRIM)  # its buckle
        r.part("cube", 0, 1.62, 0, 0.36, 0.72, 0.5, plate, tex="iron_plate")  # the mailed chest
        r.part("cube", 0.04, 1.4, 0, 0.32, 1.2, 0.42, cloth)  # the long tabard, front and back
        r.part("cube", 0.2, 0.95, 0, 0.02, 0.06, 0.42, TABARD_TRIM)  # its hem's trim
        for z in (-0.21, 0.21):
            r.part("cube", 0.2, 1.4, z, 0.02, 1.2, 0.03, TABARD_TRIM)  # its edging
        _hand_device(r, 0.21, 1.62, 0, 0.36, TABARD_TRIM)
        for side in (-1, 1):  # the pauldrons
            r.part("sphere", 0, 1.98, side * 0.3, 0.2, 0.14, 0.2, plate)
            r.part("cube", 0, 1.9, side * 0.34, 0.24, 0.04, 0.16, _dim(plate, 1.3))  # its lame
        r.part("cyl", 0, 2.08, 0, 0.14, 0.12, 0.14, skin)  # the neck
        with r.at(0.02, 2.24, 0, rz=math.sin(t * 1.1) * 0.05 * (1 - fall)):  # the gaunt head and helm
            r.part("cube", 0.02, 0, 0, 0.22, 0.24, 0.2, skin)
            r.part("cube", 0.12, 0.03, 0, 0.02, 0.03, 0.14, (20, 14, 12))  # the sunken eyes
            r.part("cube", 0.12, -0.08, 0, 0.02, 0.02, 0.08, _dim(skin, 0.6))  # the thin mouth
            r.part("cyl", 0, 0.14, 0, 0.3, 0.04, 0.3, plate)  # the fluted brim
            r.part("cone", 0, 0.32, 0, 0.22, 0.36, 0.22, plate)  # the tall pointed crown
            r.part("cube", 0, 0.18, 0, 0.24, 0.04, 0.24, TABARD_TRIM)  # its band
        # The grafted lower pair: the lantern held up and out, the other clutching.
        reach = _swing_pose(e, 0.6, 0.9, 0.4)
        _hanging_arm(r, 0, 1.58, -0.27, -1, reach, skin, cloth, plate)
        with (
            r.at(0, 1.58, -0.27),
            r.at(0, 0, -0.04, rz=0.2 + 1.2 * reach),
            r.at(0, -0.3, 0, rz=0.5 - 0.4 * reach),
            r.at(0, -0.42, 0, rz=-(0.7 + 0.8 * reach)),  # the lantern hangs plumb below the fist
        ):
            r.part("cube", 0, -0.04, 0, 0.02, 0.08, 0.02, BLACKENED)  # its bail
            r.part("cube", 0, -0.18, 0, 0.16, 0.2, 0.16, LANTERN if lit else (60, 50, 40), glow=lit)
            r.part("pyramid", 0, -0.04, 0, 0.18, 0.08, 0.18, BLACKENED)  # its cap
            r.part("cube", 0, -0.3, 0, 0.18, 0.04, 0.18, BLACKENED)  # its base
        _hanging_arm(r, 0, 1.58, 0.27, 1, 0.3 + 0.3 * math.sin(t * 3.1), skin, cloth, plate)
        # The first pair: the halberd arm, and the other arm steadying the haft.
        shoulder, elbow = chop_angle(e) - 0.4 * fall, elbow_bend(e) * (1 - fall)
        wrist = wrist_angle(e) if fall == 0 else aim_wrist(-lean, shoulder + elbow)
        with r.at(0, 1.95, 0.32, rz=shoulder):
            r.part("cube", 0, -0.18, 0, 0.12, 0.36, 0.12, plate)
            with r.at(0, -0.36, 0, rz=elbow):
                r.part("cube", 0, -0.16, 0, 0.11, 0.32, 0.11, plate)
                with r.at(0, -0.36, 0), held(r, wrist, skin, size=0.12, splay=0.35):
                    halberd(r)
        with r.at(0, 1.95, -0.32, rz=0.5 * shoulder + 0.2):
            r.part("cube", 0, -0.18, 0, 0.12, 0.36, 0.12, plate)
            with r.at(0, -0.36, 0, rz=0.6):
                r.part("cube", 0, -0.15, 0, 0.11, 0.3, 0.11, plate)
                r.part("cube", 0, -0.33, 0, 0.11, 0.12, 0.12, skin)  # the fist


def great_maul(r, length=1.7, rgb=BLACKENED):
    """A Warden's great maul in a `held` frame: a thick iron-shod haft along +X, a block of a head
    flanged and riveted, a spike on its crown and an ember glowing in its cheek while it lives."""
    r.part("cube", length * 0.4 - 0.3, 0, 0, length, 0.08, 0.08, (60, 46, 34))  # the haft
    r.part("cube", -0.32, 0, 0, 0.14, 0.11, 0.11, rgb)  # the butt
    head = length * 0.9 - 0.3
    r.part("cube", head, 0, 0, 0.36, 0.34, 0.5, rgb, tex="iron_plate")  # the head
    for z in (-0.26, 0.26):  # its flanged faces
        r.part("cube", head, 0, z, 0.42, 0.4, 0.04, _dim(rgb, 1.35))
    for dx in (-0.12, 0.12):
        for dy in (-0.12, 0.12):
            r.part("cube", head + dx, dy, 0.28, 0.04, 0.04, 0.02, BLACKENED_EDGE)  # its rivets
    r.part("cone", head + 0.26, 0, 0, 0.12, 0.2, 0.12, rgb, rz=-math.pi / 2)  # the crown spike


def castellan_warden(r, e, t):
    """A Castellan Warden: a giant in black plate, broad as a door, a tower of a great helm with a
    single eye of fire burning in its visor (the gate's fire: there is one for each Warden on the
    gate it keeps), a short cape of soaked wool and a great maul. It turns slowly. A sweep spins it
    with the maul out; slain, it falls forward onto its knees and down, and the eye goes out."""
    from ashen_vault.render.moon_models import _sweep_spin

    fall = death_fall(e, 1.0)
    lit = e.alive
    swing = walk_cycle(e, t) * 0.35
    plate = hit_tint((230, 230, 240)) if e.flashing else BLACKENED
    edge = hit_tint((240, 240, 250)) if e.flashing else BLACKENED_EDGE
    eye = (HIT_GLOW if e.flashing else EMBER_EYE) if lit else COLD
    with r.at(0.5 * fall, 0.4 * fall, 0, rz=-1.3 * fall, ry=_sweep_spin(e) * (1 - fall)):
        for side, a in ((-0.24, swing), (0.24, -swing)):  # the legs, armoured to the toes
            with r.at(0, 1.2, side, rz=a - 0.6 * fall):
                r.part("cube", 0, -0.3, 0, 0.26, 0.6, 0.26, plate, tex="iron_plate")
                r.part("sphere", 0.1, -0.6, 0, 0.17, 0.15, 0.17, edge)  # the knee-cop
                with r.at(0, -0.6, 0, rz=-0.2 + 1.4 * fall):
                    r.part("cube", 0, -0.28, 0, 0.22, 0.56, 0.22, plate, tex="iron_plate")
                    r.part("cube", 0.1, -0.57, 0, 0.42, 0.1, 0.24, _dim(plate, 0.8))  # the sabaton
        r.part("cube", 0, 1.26, 0, 0.5, 0.3, 0.74, plate, tex="iron_plate")  # the fauld
        for z in (-0.26, 0.0, 0.26):  # tassets over the thighs
            r.part("cube", 0.2, 1.08, z, 0.06, 0.3, 0.22, edge, rz=-0.1)
        r.part("cube", 0, 1.78, 0, 0.62, 0.8, 0.86, plate, tex="iron_plate")  # the cuirass
        r.part("cube", 0.31, 1.82, 0, 0.04, 0.62, 0.08, edge)  # its ridge
        for y in (1.5, 1.66):
            r.part("cube", 0.31, y, 0, 0.03, 0.05, 0.7, edge)  # its lames
        for i, z in enumerate((-0.3, -0.1, 0.1, 0.3)):  # the cape, sodden
            drop = 1.2 - 0.12 * (i % 2)
            r.part("cube", -0.36, 2.15 - drop / 2, z, 0.04, drop, 0.2, (34, 30, 36))
        for side in (-1, 1):  # the great pauldrons, stacked lames
            r.part("sphere", 0, 2.2, side * 0.5, 0.34, 0.22, 0.32, plate)
            for k in range(2):
                r.part("cube", 0, 2.06 - k * 0.1, side * 0.56, 0.4, 0.05, 0.22, edge)
        with r.at(0.04, 2.48, 0):  # the great helm
            r.part("cube", 0, 0, 0, 0.44, 0.48, 0.42, plate, tex="iron_plate")
            r.part("cube", 0.22, 0.04, 0, 0.02, 0.06, 0.32, (16, 14, 16))  # the visor's slit
            r.part("sphere", 0.23, 0.04, 0, 0.06, 0.06, 0.06, eye, glow=lit)  # the eye of fire
            r.part("cube", 0.22, -0.12, 0, 0.02, 0.18, 0.04, edge)  # the breaths' ridge
            r.part("cube", 0, 0.28, 0, 0.5, 0.08, 0.48, edge)  # the crown band
            r.part("pyramid", 0, 0.42, 0, 0.36, 0.24, 0.36, plate)  # its peak
            for side in (-1, 1):  # the horns of its crest, swept back
                r.part("cone", -0.1, 0.42, side * 0.2, 0.06, 0.34, 0.06, edge, rz=0.8, rx=-side * 0.3)
        sweeping = e.attack_kind == "sweep" and e.state in ("windup", "attack")
        if sweeping:
            shoulder, elbow, wrist = 1.5, 0.1, aim_wrist(0.0, 1.6)
        else:
            shoulder, elbow = chop_angle(e) - 0.5 * fall, elbow_bend(e) * (1 - fall)
            wrist = wrist_angle(e) if fall == 0 else aim_wrist(1.3 * fall, shoulder + elbow)
        with r.at(0, 2.14, 0.5, rz=shoulder):  # the maul arm
            r.part("cube", 0, -0.22, 0, 0.2, 0.44, 0.2, plate)
            r.part("sphere", 0, -0.44, 0, 0.14, 0.14, 0.14, edge)
            with r.at(0, -0.44, 0, rz=elbow):
                r.part("cube", 0, -0.2, 0, 0.18, 0.4, 0.18, plate)
                with r.at(0, -0.44, 0), held(r, wrist, edge, size=0.18, splay=0.3):
                    great_maul(r)
        with r.at(0, 2.14, -0.5, rz=0.4 * shoulder + 0.1):  # the off arm
            r.part("cube", 0, -0.22, 0, 0.2, 0.44, 0.2, plate)
            with r.at(0, -0.44, 0, rz=0.4):
                r.part("cube", 0, -0.2, 0, 0.18, 0.4, 0.18, plate)
                r.part("cube", 0, -0.44, 0, 0.2, 0.18, 0.2, edge)  # the gauntlet


def _sentinel_awake(e):
    """How far a stone sentinel has torn out of its statue's skin: 0 a statue, 1 awake."""
    k = e.rise_progress
    return _ease(min(max((k - STATUE_BURST) / 0.2 + 0.5, 0.0), 1.0))


def _sentinel_body(r, e, t, stone, dark, glow, cracks, statue):
    """The stone giant's body, at a man's size (the caller scales it up): legs like pillars, a skirt of
    stone lames, a deep cuirass, a mantle carved as falling cloth, and a great helm with a fan of a
    crest and two eyes. `cracks` runs seams of fire down it (its second phase)."""
    swing = walk_cycle(e, t) * 0.25
    for side, a in ((-0.17, swing), (0.17, -swing)):
        with r.at(0, 1.05, side, rz=a):
            r.part("cube", 0, -0.26, 0, 0.2, 0.52, 0.2, stone)
            r.part("cube", 0.04, -0.52, 0, 0.24, 0.12, 0.24, dark)  # the knee
            with r.at(0, -0.52, 0, rz=-0.05):
                r.part("cube", 0, -0.24, 0, 0.18, 0.48, 0.18, stone)
                r.part("cube", 0.06, -0.48, 0, 0.36, 0.08, 0.22, dark)  # the foot
    for i in range(5):  # the skirt of stone lames
        a = (i - 2) * 0.32
        r.part("cube", math.cos(a) * 0.2, 0.92, math.sin(a) * 0.24, 0.06, 0.34, 0.18, stone, ry=-a)
    r.part("cube", 0, 1.1, 0, 0.36, 0.2, 0.5, dark)  # the hips
    r.part("cube", 0, 1.2, 0, 0.4, 0.06, 0.56, dark)  # the belt
    r.part("cube", 0.2, 1.2, 0, 0.03, 0.1, 0.12, stone)  # its buckle
    r.part("cube", 0, 1.48, 0, 0.42, 0.62, 0.6, stone)  # the cuirass
    r.part("cube", 0.21, 1.52, 0, 0.04, 0.5, 0.08, dark)  # its keel
    r.part("cube", -0.22, 1.25, 0, 0.06, 1.0, 0.56, dark)  # the mantle down its back
    for z in (-0.18, 0.0, 0.18):
        r.part("cube", -0.25, 1.15, z, 0.03, 0.9, 0.06, stone)  # the folds carved in it
    for side in (-1, 1):
        r.part("sphere", 0, 1.8, side * 0.36, 0.22, 0.16, 0.22, stone)  # the pauldrons
        r.part("cube", 0, 1.7, side * 0.4, 0.26, 0.05, 0.16, dark)
    with r.at(0.02, 2.02, 0):  # the great helm
        r.part("cube", 0, 0, 0, 0.3, 0.34, 0.28, stone)
        r.part("cube", 0.15, 0.02, 0, 0.02, 0.04, 0.22, (14, 14, 16))  # the eye slit
        for dz in (-0.06, 0.06):
            r.part("cube", 0.16, 0.02, dz, 0.02, 0.04, 0.04, glow if not statue else dark, glow=not statue)
        for i in range(5):  # the fan of its crest
            a = (i - 2) * 0.28
            r.part("cube", -0.04, 0.24 + math.cos(a) * 0.1, math.sin(a) * 0.1, 0.22, 0.14, 0.03, dark, rx=a)
    if cracks:  # seams of fire in the stone, its second phase
        for x, y, z, h, a in ((0.22, 1.5, 0.1, 0.4, 0.3), (0.22, 1.36, -0.16, 0.3, -0.4),
                              (0.16, 0.7, 0.17, 0.3, 0.2), (0.0, 1.85, 0.4, 0.2, 0.5)):  # fmt: skip
            r.part("cube", x, y, z, 0.02, h, 0.03, glow, rx=a, glow=True)


def sentinel_stance(e):
    """(lean, spin, hop, guard) of a sentinel's whole body through its own moves: the Bulwark crouching
    in behind its shield for a charge, and raising it high to drive its edge down for its rampart; the
    Blade coiling back and spinning a full turn for its whirlwind, and crouching to spring, then high
    in the air, for its leap. `guard` raises the shield arm."""
    kind = getattr(e, "attack_kind", None)
    if e.state not in ("windup", "attack", "recover"):
        return 0.0, 0.0, 0.0, None
    k = _windup_k(e) if e.state == "windup" else 1.0
    after = e.state == "recover"
    settle = 1.0 - _ease(min(e.state_t / max(e.recover_time, 1e-3), 1)) if after else 1.0
    if kind == "shield_charge":
        return 0.35 * k * settle, 0.0, 0.0, 1.1 * k * settle
    if kind == "rampart_slam":
        if e.state == "windup":
            return -0.15 * k, 0.0, 0.0, 1.8 * _ease(k)
        down = _ease(min(e.state_t / 0.15, 1.0)) if e.state == "attack" else 1.0
        return 0.35 * down * settle, 0.0, 0.0, (1.8 - 2.4 * down) * settle
    if kind == "whirlwind":
        if e.state == "windup":
            return 0.0, -0.8 * _ease(k), 0.0, None
        if e.state == "attack":  # one full turn round, over the move's attack
            p = _ease(min(e.state_t / 0.4, 1.0))
            return 0.1, -0.8 + (math.tau + 0.8) * p, 0.0, None
        return 0.0, 0.0, 0.0, None
    if kind == "sky_rend":
        if e.state == "windup":
            return 0.2 * k, 0.0, -0.25 * _ease(k), None
        if e.state == "attack":  # up through its flight and down on the blade
            p = min(e.state_t / 0.6, 1.0)
            return 0.3 * p, 0.0, 2.2 * math.sin(math.pi * p), None
        return 0.3 * settle, 0.0, 0.0, None
    return 0.0, 0.0, 0.0, None


def _sentinel(r, e, t, weapon):
    """Either stone sentinel: the shared body, scaled up to a giant, and its weapon (`weapon`: "shield"
    for the Bulwark, its tower shield and short blade; "blade" for the Blade Sentinel, its long blade).
    Asleep, it is a statue on its plinth, moss in its folds and its eyes dark; slain, it topples over
    backward like a felled statue, and its fires go out."""
    awake = _sentinel_awake(e)
    statue = awake < 0.5
    dead = e.state == "dead"
    lit = not statue and not dead
    fall = death_fall(e, 1.4)
    stone = hit_tint((236, 236, 240)) if e.flashing else STATUE_STONE
    dark = hit_tint((200, 200, 210)) if e.flashing else STATUE_DARK
    glow = (HIT_GLOW if e.flashing else CRACK_FIRE) if lit else COLD
    raging = bool(getattr(e, "phase2", False)) and lit
    lean, spin, hop, raised = sentinel_stance(e) if not dead else (0.0, 0.0, 0.0, None)
    kind = getattr(e, "attack_kind", None)
    with (
        r.at(0, max(hop, -0.25), 0, ry=spin),
        r.at(-0.6 * fall, 0.5 * fall, 0, rz=1.4 * fall - lean, s=2.0),
    ):
        _sentinel_body(r, e, t, stone, dark, glow, raging, not lit)
        if statue:  # moss grown into the folds of the mantle and over the helm
            r.part("cube", -0.2, 1.7, 0, 0.1, 0.3, 0.5, STATUE_MOSS)
            r.part("cube", 0.02, 2.2, 0, 0.32, 0.04, 0.3, STATUE_MOSS)
        shoulder, elbow = chop_angle(e) - 0.4 * fall, elbow_bend(e) * (1 - fall)
        sweeping = kind in ("sweep", "whirlwind") and e.state in ("windup", "attack")
        if sweeping:  # the blade held straight out to its side, to scythe round
            shoulder, elbow = 1.5, 0.1
        elif kind == "shield_charge" and e.state in ("windup", "attack"):  # tucked in behind the shield
            shoulder, elbow = -0.3, 1.2
        wrist = aim_wrist(0.0, shoulder + elbow) if sweeping else wrist_angle(e)
        if dead:  # the blade falls with it, along its body
            wrist = aim_wrist(-1.4 * fall, shoulder + elbow)
        with r.at(0, 1.78, 0.4, rz=shoulder):  # the sword arm
            r.part("cube", 0, -0.18, 0, 0.14, 0.36, 0.14, stone)
            r.part("sphere", 0, -0.36, 0, 0.1, 0.1, 0.1, dark)
            with r.at(0, -0.36, 0, rz=elbow):
                r.part("cube", 0, -0.16, 0, 0.13, 0.32, 0.13, stone)
                with r.at(0, -0.36, 0), held(r, wrist, dark, size=0.14, splay=0.3):
                    length = 1.9 if weapon == "blade" else 1.0
                    r.part("cube", -0.16, 0, 0, 0.32, 0.06, 0.06, dark)  # the grip
                    r.part("cube", 0.02, 0, 0, 0.06, 0.08, 0.44, stone)  # the cross
                    r.part("cube", 0.04 + length / 2, 0, 0, length, 0.04, 0.16, stone)  # the blade
                    r.part(
                        "cube", 0.04 + length / 2, 0, 0, length, 0.05, 0.03, _dim(stone, 1.2)
                    )  # its fuller
                    r.part(
                        "pyramid", 0.08 + length, 0, 0, 0.16, 0.2, 0.04, stone, rz=-math.pi / 2
                    )  # its point
                    r.part("sphere", -0.34, 0, 0, 0.08, 0.08, 0.08, stone)  # the pommel
                    r.part("cube", 0.14, 0, 0, 0.16, 0.06, 0.18, dark)  # the ricasso
                    rune = glow if raging else dark
                    for k in range(3):  # runes cut down the blade, burning in its rage
                        r.part("cube", 0.4 + k * length * 0.25, 0.03, 0, 0.08, 0.02, 0.06, rune, glow=raging)
        guard = 0.3 if weapon == "shield" and e.state in ("chase", "windup") else 0.0
        if weapon == "shield" and raised is not None:  # its own moves raise and drive the shield
            guard = raised
        with r.at(0, 1.78, -0.4, rz=guard + 0.2 * shoulder * (weapon == "blade") - 0.4 * fall):
            r.part("cube", 0, -0.18, 0, 0.14, 0.36, 0.14, stone)
            with r.at(0, -0.36, 0, rz=0.5):
                r.part("cube", 0, -0.16, 0, 0.13, 0.32, 0.13, stone)
                if weapon == "shield":  # the tower shield, Herran's hand carved on its face
                    with r.at(0.2, -0.1, -0.1, rz=-0.5 - guard):
                        r.part("cube", 0, 0, 0, 0.1, 1.3, 0.62, dark)
                        r.part("cube", 0.06, 0, 0, 0.02, 1.2, 0.54, stone)
                        r.part("cube", 0.07, 0.62, 0, 0.02, 0.06, 0.6, dark)  # its rim
                        r.part("cube", 0.07, -0.62, 0, 0.02, 0.06, 0.6, dark)
                        _hand_device(r, 0.08, 0.05, 0, 0.5, glow if raging else dark)
                else:
                    r.part("cube", 0, -0.36, 0, 0.13, 0.12, 0.14, dark)  # the fist


def bulwark_sentinel(r, e, t):
    _sentinel(r, e, t, "shield")


def blade_sentinel(r, e, t):
    _sentinel(r, e, t, "blade")


# --- what Herran made in his laboratory ----------------------------------------------------------------

AMALGAM_SKIN = (178, 140, 128)
AMALGAM_HIDE = (96, 76, 64)  # the hound's pelt, sewn in patches
AMALGAM_FUR = (70, 58, 50)  # the ape's
BILE = (150, 200, 90)  # the toxic fluid that weeps from its seams


def amalgam(r, e, t):
    """An Amalgam: a hound, an ape and a man sewn into one heaving body, crouched on the hound's legs
    and the ape's knuckles, crowded with arms: the ape's two great arms in front, a man's arms sewn on
    all down its flanks, reaching. Three heads in a row at its front (the hound's, the man's, the ape's),
    patches of pelt and bare skin joined by seams that weep a green bile. It rears up and brings both
    great fists down (`slam`), or rakes all its arms round it. Slain, it slumps over on its side, and
    the bile stops glowing."""
    fall = death_fall(e, 0.9)
    lit = e.alive
    skin = hit_tint((250, 220, 210)) if e.flashing else AMALGAM_SKIN
    hide = hit_tint((210, 190, 180)) if e.flashing else AMALGAM_HIDE
    fur = hit_tint((200, 180, 170)) if e.flashing else AMALGAM_FUR
    bile = (HIT_GLOW if e.flashing else BILE) if lit else _dim(BILE, 0.3)
    heave = math.sin(t * 2.2) * 0.04
    rear = _swing_pose(e, 0.0, 0.55, -0.1) if e.attack_kind == "slam" else 0.0
    rake = _swing_pose(e, 0.0, 0.8, -0.6) if e.attack_kind == "sweep" else 0.0
    with r.at(0, 0.3 * fall, 0, rx=1.3 * fall):
        for side in (-1, 1):  # the hound's hind legs
            with r.at(-0.5, 0.75, side * 0.3, rz=0.3):
                r.part("cube", 0, -0.24, 0, 0.18, 0.5, 0.16, hide)
                with r.at(0, -0.46, 0, rz=-0.8):
                    r.part("cube", 0, -0.2, 0, 0.12, 0.42, 0.12, hide)
                    r.part("cube", 0.08, -0.4, 0, 0.2, 0.06, 0.12, _dim(hide, 0.7))  # the paw
        with r.at(0, 0, 0, rz=-0.4 * rear):  # the body rears back about its haunches
            r.part("sphere", -0.2, 0.9 + heave, 0, 0.6, 0.42, 0.5, skin)  # the heaving bulk
            r.part("sphere", -0.45, 0.95, 0.12, 0.34, 0.3, 0.3, hide)  # a patch of the hound's pelt
            r.part("sphere", 0.15, 1.15 + heave, -0.1, 0.42, 0.38, 0.4, fur)  # the ape's shoulders
            for x, z, a in ((-0.3, 0.42, 0.2), (0.0, -0.44, -0.3), (-0.6, -0.3, 0.6), (0.2, 0.36, -0.5)):
                r.part("cube", x, 1.0, z, 0.36, 0.03, 0.03, bile, ry=a, glow=lit)  # the weeping seams
                r.part("cube", x, 1.0, z, 0.06, 0.06, 0.06, STITCH)
            for i, (x, y, z, size, rgb) in enumerate(
                ((0.5, 1.0, -0.22, 0.17, hide), (0.48, 1.18, 0.0, 0.16, skin), (0.45, 1.06, 0.24, 0.19, fur))
            ):  # the three heads: the hound's, the man's, the ape's
                with r.at(x, y + heave, z, rz=-0.1 * math.sin(t * 1.7 + i)):
                    r.part("sphere", 0, 0, 0, size, size, size, rgb)
                    r.part(
                        "cube",
                        size * 0.9,
                        -size * 0.3,
                        0,
                        size * 0.7,
                        size * 0.4,
                        size * 0.7,
                        _dim(rgb, 0.85),
                    )
                    for dz in (-1, 1):
                        r.part("cube", size * 0.85, size * 0.25, dz * size * 0.4, 0.02, 0.03, 0.03,
                               bile if i == 1 else (20, 14, 12), glow=lit and i == 1)  # fmt: skip
            slam = 1.4 * rear  # the ape's great arms, raised for the slam
            for side in (-1, 1):
                with r.at(0.25, 1.3, side * 0.4, rz=-0.3 + slam, rx=side * 0.2):
                    r.part("cube", 0, -0.28, 0, 0.2, 0.56, 0.2, fur)
                    with r.at(0, -0.56, 0, rz=0.2):
                        r.part("cube", 0, -0.26, 0, 0.18, 0.52, 0.18, fur)
                        r.part("sphere", 0.04, -0.56, 0, 0.16, 0.14, 0.18, _dim(fur, 0.8))  # the knuckles
            for i in range(6):  # the men's arms, sewn on all down its flanks, reaching
                side = 1 if i % 2 else -1
                x = 0.1 - (i // 2) * 0.32
                reach = 0.5 + 0.4 * math.sin(t * 3 + i) * (1 - fall) + rake * (1 if side > 0 else 0.5)
                _hanging_arm(r, x, 1.05 - (i // 2) * 0.05, side * 0.46, side, min(max(reach, 0), 1.2), skin,
                             skin, STITCH)  # fmt: skip


HAND_SKIN = (196, 172, 156)


def handcrawler(r, e, t):
    """A Handcrawler: a knot of six human arms joined at the shoulders round a sewn-up face, walking
    on its hands like a spider, its fingers drumming; it springs at you (`pounce`). The face at its
    middle looks up, its eyes rolled white. Slain, it sinks flat, its arms curled in like a dead spider's."""
    fall = death_fall(e, 0.6)
    skin = hit_tint((250, 230, 220)) if e.flashing else HAND_SKIN
    gait = math.sin(t * 12) if e.state == "chase" else math.sin(t * 2) * 0.3
    spring = _swing_pose(e, 0.0, -0.25, 0.3) if e.attack_kind == "pounce" else 0.0
    curl = fall
    body_y = 0.45 + spring - 0.3 * fall
    r.part("sphere", 0, body_y, 0, 0.26, 0.18, 0.26, skin)  # the knot of shoulders
    r.part("cube", 0, body_y + 0.02, 0, 0.5, 0.03, 0.03, STITCH, ry=0.7)  # the seams round it
    r.part("cube", 0, body_y + 0.02, 0, 0.5, 0.03, 0.03, STITCH, ry=-0.7)
    with r.at(0.12, body_y + 0.12, 0, rz=0.6):  # the face sewn into the middle, looking up
        r.part("sphere", 0, 0, 0, 0.14, 0.04, 0.12, _dim(skin, 0.9))
        for dz in (-0.05, 0.05):
            r.part("sphere", 0.04, 0.03, dz, 0.025, 0.02, 0.025, (236, 232, 222))  # the eyes, rolled white
        r.part("cube", -0.05, 0.03, 0, 0.02, 0.01, 0.08, STITCH)  # the mouth, sewn shut
    for i in range(6):
        a = i * math.tau / 6 + 0.25
        phase = gait * (1 if i % 2 else -1)
        with (
            r.at(math.cos(a) * 0.18, body_y, math.sin(a) * 0.18, ry=-a),
            r.at(0, 0, 0, rz=0.7 + 0.25 * phase - 0.5 * curl),  # the upper arm, up from the knot
        ):
            r.part("cube", 0.18, 0, 0, 0.36, 0.07, 0.07, skin)
            r.part("sphere", 0.36, 0, 0, 0.05, 0.05, 0.05, _dim(skin, 0.85))  # the elbow
            with r.at(0.36, 0, 0, rz=-1.9 + 1.5 * curl):  # the forearm, down to the hand
                r.part("cube", 0.2, 0, 0, 0.4, 0.06, 0.06, skin)
                with r.at(0.42, 0, 0, rz=0.9):
                    r.part("cube", 0.03, 0, 0, 0.07, 0.03, 0.08, skin)  # the hand
                    for f in range(3):
                        r.part("cube", 0.08, 0, (f - 1) * 0.025, 0.06, 0.015, 0.015, skin)


# --- the castle's dressing --------------------------------------------------------------------------

CASTLE = (96, 96, 104)  # the castle's dark grey stone, as `castle_stone` shows it
CASTLE_DARK = (62, 62, 70)
SLATE = (54, 56, 68)
LEAD = (70, 74, 80)  # the leaded finials and crestings
WINDOW_LIT = (255, 190, 110)
WINDOW_DARK = (16, 14, 18)
IRON = (40, 40, 46)
PANE = (150, 176, 190)  # the glass of the dome, the vats and the bench's vessels
CANDLE = (226, 214, 186)
FLAME = (255, 200, 110)
VAT_GREEN = (110, 220, 120)
TALLOW = (214, 204, 180)


def _lancet(r, x, y, z, w, h, lit, face=0.0):
    """A tall pointed lancet window, set into a face turned `face` radians about Y: its dark (or lit)
    light, a pointed head over it and a sill under it."""
    with r.at(x, y, z, ry=face):
        r.part("cube", 0, 0, 0, 0.12, h, w, WINDOW_LIT if lit else WINDOW_DARK, glow=lit)
        r.part(
            "pyramid", 0, h / 2 + w * 0.4, 0, 0.12, w * 0.8, w, WINDOW_LIT if lit else WINDOW_DARK, glow=lit
        )
        r.part("cube", 0.04, -h / 2 - 0.08, 0, 0.2, 0.12, w + 0.2, CASTLE_DARK)  # the sill


def _crenels(r, y, radius, n, rgb, square=False):
    """A ring (or square) of merlons round a tower's top at height `y`."""
    if square:
        for i in range(n):
            k = (i + 0.5) / n * 2 - 1
            for x, z in (
                (k * radius, radius),
                (k * radius, -radius),
                (radius, k * radius),
                (-radius, k * radius),
            ):
                r.part("cube", x, y, z, 0.6, 0.9, 0.6, rgb, tex="castle_stone")
        return
    for i in range(n):
        a = i * math.tau / n
        r.part(
            "cube",
            math.cos(a) * radius,
            y,
            math.sin(a) * radius,
            0.6,
            0.9,
            0.7,
            rgb,
            ry=-a,
            tex="castle_stone",
        )


def _spire_roof(r, y, width, height, sides=4):
    """A steep roof of dark slate from `y`, `width` across, `height` tall, with a leaded finial: a cone
    over a round tower, a pyramid over a square one (two crossed pyramids over an octagon)."""
    if sides == 0:
        r.part("cone", 0, y + height / 2, 0, width, height, width, SLATE, tex="castle_slate")
    else:
        r.part("pyramid", 0, y + height / 2, 0, width, height, width, SLATE, tex="castle_slate")
        if sides == 8:
            r.part(
                "pyramid",
                0,
                y + height / 2,
                0,
                width,
                height,
                width,
                SLATE,
                ry=math.pi / 4,
                tex="castle_slate",
            )
    r.part("cyl", 0, y + height + 0.4, 0, 0.12, 0.8, 0.12, LEAD)  # the finial's rod
    r.part("sphere", 0, y + height + 0.1, 0, 0.3, 0.3, 0.3, LEAD)  # its knop
    r.part("cube", 0, y + height + 0.7, 0, 0.06, 0.06, 0.7, LEAD)  # its cross-bar
    r.part(
        "cube", 0, y + 0.1, 0, width * 1.04, 0.2, width * 1.04, CASTLE_DARK, tex="castle_stone"
    )  # the eave


def gargoyle_spout(r, x, y, z, size=1.0, ry=0.0):
    """A gargoyle spout jutting out along +X from (x, y, z): a crouched winged beast, its forelegs
    braced on the stone, its jaws open over the drop and a lead spout in its throat."""
    s = size
    with r.at(x, y, z, ry=ry):
        r.part("cube", 0.35 * s, 0, 0, 0.8 * s, 0.36 * s, 0.4 * s, STATUE_STONE)  # the body, out of the wall
        r.part("cube", 0.25 * s, 0.2 * s, 0, 0.5 * s, 0.1 * s, 0.32 * s, STATUE_DARK)  # its spine ridge
        for side in (-1, 1):
            r.part(
                "cube", 0.55 * s, -0.24 * s, side * 0.16 * s, 0.14 * s, 0.3 * s, 0.1 * s, STATUE_DARK
            )  # a foreleg
            r.part("wedge", 0.15 * s, 0.25 * s, side * 0.24 * s, 0.5 * s, 0.4 * s, 0.04 * s, STATUE_DARK,
                   rx=side * 0.3)  # fmt: skip  # a folded wing
        with r.at(0.8 * s, 0.06 * s, 0, rz=-0.25):  # the head, craning out and down
            r.part("cube", 0.1 * s, 0.05 * s, 0, 0.3 * s, 0.22 * s, 0.28 * s, STATUE_STONE)  # the skull
            r.part("cube", 0.28 * s, 0.08 * s, 0, 0.18 * s, 0.08 * s, 0.2 * s, STATUE_STONE)  # the upper jaw
            r.part(
                "cube", 0.26 * s, -0.07 * s, 0, 0.16 * s, 0.06 * s, 0.18 * s, STATUE_DARK, rz=-0.35
            )  # the lower
            r.part("cube", 0.22 * s, 0.0, 0, 0.1 * s, 0.06 * s, 0.14 * s, WINDOW_DARK)  # the throat
            r.part("cyl", 0.32 * s, 0.0, 0, 0.06 * s, 0.14 * s, 0.06 * s, LEAD, rz=math.pi / 2)  # the spout
            for side in (-1, 1):
                r.part("cone", 0.0, 0.22 * s, side * 0.1 * s, 0.06 * s, 0.22 * s, 0.06 * s, STATUE_DARK,
                       rz=0.6)  # fmt: skip  # a horn swept back
                r.part(
                    "cube", 0.2 * s, 0.12 * s, side * 0.1 * s, 0.04 * s, 0.03 * s, 0.04 * s, WINDOW_DARK
                )  # an eye


def castle_tower(r, seed, height=24.0, style="round", width=5.0):
    """One of the many towers of Herran's Castle, for its skyline: a shaft of sooted grey stone `height`
    metres tall and `width` across, lancet windows up it (a few lit), a gargoyle spout at each corner
    under a corbelled parapet and its crenels, and a steep slate roof with a leaded finial. Each `style` its own shape: "round" (a cone),
    "square" (a pyramid, a bartizan at each corner), "octagon" (an eight-sided spire), "belfry" (an open
    stage of arches with its bell hanging in the dark of it) and "keep" (the great tower: broad, a
    spire on it and a turret at each corner)."""
    half = width / 2
    top = height
    round_ = style in ("round", "octagon")
    if style == "round":
        r.part("cyl", 0, height / 2, 0, width, height, width, CASTLE, tex="castle_stone")
    elif style == "octagon":
        r.part("cube", 0, height / 2, 0, width * 0.92, height, width * 0.92, CASTLE, tex="castle_stone")
        r.part(
            "cube",
            0,
            height / 2,
            0,
            width * 0.92,
            height,
            width * 0.92,
            CASTLE,
            ry=math.pi / 4,
            tex="castle_stone",
        )
    else:
        r.part("cube", 0, height / 2, 0, width, height, width, CASTLE, tex="castle_stone")
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # the corner buttresses, stepped
            r.part(
                "cube",
                dx * half,
                height * 0.3,
                dz * half,
                0.8,
                height * 0.6,
                0.8,
                CASTLE_DARK,
                tex="castle_stone",
            )
    for k in range(3):  # string courses up the shaft
        y = height * (0.3 + 0.25 * k)
        if round_:
            r.part("cyl", 0, y, 0, width + 0.2, 0.25, width + 0.2, CASTLE_DARK, tex="castle_stone")
        else:
            r.part("cube", 0, y, 0, width + 0.2, 0.25, width + 0.2, CASTLE_DARK, tex="castle_stone")
    for k in range(4):  # windows up it, on each face, a few lit
        y = height * (0.22 + 0.2 * k)
        for face in range(4):
            a = face * math.pi / 2
            lit = (seed + k * 3 + face) % 5 == 0
            _lancet(r, math.cos(a) * (half + 0.02), y, math.sin(a) * (half + 0.02), 0.7, 1.8, lit, -a)
    for k in range(4):  # a gargoyle spout jutting from each corner under the parapet
        a = math.pi / 4 + k * math.pi / 2
        reach = half * (1.0 if round_ else math.sqrt(2)) - 0.1
        gargoyle_spout(r, math.cos(a) * reach, top - 1.1, math.sin(a) * reach, 1.0, -a)
    corbel = width + 0.8  # the parapet, corbelled out over the shaft
    if round_:
        r.part("cyl", 0, top - 0.3, 0, corbel, 0.6, corbel, CASTLE_DARK, tex="castle_stone")
        _crenels(r, top + 0.45, corbel / 2 - 0.2, 12, CASTLE)
    else:
        r.part("cube", 0, top - 0.3, 0, corbel, 0.6, corbel, CASTLE_DARK, tex="castle_stone")
        _crenels(r, top + 0.45, corbel / 2 - 0.3, 3, CASTLE, square=True)
    if style == "belfry":  # an open stage of arches, the bell in the dark of it, then its roof
        stage = 4.0
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            r.part(
                "cube",
                dx * (half - 0.4),
                top + stage / 2,
                dz * (half - 0.4),
                0.8,
                stage,
                0.8,
                CASTLE,
                tex="castle_stone",
            )
        r.part("cube", 0, top + stage - 0.3, 0, width, 0.6, width, CASTLE_DARK, tex="castle_stone")
        r.part("cone", 0, top + stage * 0.45, 0, 1.6, 1.8, 1.6, (70, 60, 44))  # the bell
        r.part("cube", 0, top + stage - 0.8, 0, 0.2, 0.4, width - 1.0, (52, 40, 30))  # its headstock
        _spire_roof(r, top + stage, width, width * 1.8)
    elif style == "keep":  # a tall spire, and a turret at every corner with its own cone
        _spire_roof(r, top, width * 0.7, width * 1.6, 4)
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            with r.at(dx * half, top - 2.0, dz * half):
                r.part("cyl", 0, 1.5, 0, 1.8, 3.0, 1.8, CASTLE, tex="castle_stone")
                _spire_roof(r, 3.0, 2.2, 4.0, 0)
    elif style == "square":
        _spire_roof(r, top + 0.9, width * 0.95, width * 1.5, 4)
        for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # bartizans out on the corners
            with r.at(dx * (half + 0.3), top - 1.0, dz * (half + 0.3)):
                r.part("cyl", 0, 0.6, 0, 1.2, 2.2, 1.2, CASTLE, tex="castle_stone")
                r.part("cone", 0, -0.8, 0, 1.2, 0.8, 1.2, CASTLE_DARK, rx=math.pi)  # its corbel
                _spire_roof(r, 1.7, 1.4, 2.4, 0)
    else:
        _spire_roof(
            r,
            top + 0.9,
            width * 0.95,
            width * (1.9 if style == "octagon" else 1.6),
            8 if style == "octagon" else 0,
        )


def hollow_peak(r, seed, height=90.0, width=60.0):
    """The Hollow Peak, the black mountain Herran's Castle is built against, rising beyond its tile along
    +X: a ridge of sheer rock faces `width` metres across climbing to a cleft summit `height` metres
    tall, shoulders and spurs stepping down either side, snow lying on the tops. Its rock is lighter
    than the storm behind it, so it stands out against the night."""
    rnd = [((seed * 37 + i * 101) % 97) / 97 for i in range(24)]
    rock, near, snow = (64, 66, 78), (52, 54, 64), (176, 180, 194)
    with r.at(width * 0.45, 0, 0):
        for i in range(9):  # the ridge's spurs and shoulders, lower toward its ends
            k = (i - 4) / 4
            h = height * (0.3 + 0.35 * (1 - abs(k)) + 0.15 * rnd[i])
            w = width * (0.22 + 0.1 * rnd[i + 9])
            z = k * width * 0.5
            x = -width * 0.08 * rnd[i + 4] + abs(k) * width * 0.1
            r.part(
                "pyramid",
                x,
                h / 2,
                z,
                w,
                h,
                w * 0.9,
                near if i % 2 else rock,
                ry=0.4 * k,
                tex="mountain_rock",
            )
            r.part("pyramid", x, h * 0.92, z, w * 0.16, h * 0.16, w * 0.15, snow, ry=0.4 * k)  # its snow
        for dz, k in ((-0.07, 1.0), (0.09, 0.9)):  # the summit, cleft in two
            r.part("pyramid", width * 0.05, height * k / 2, dz * width, width * 0.32, height * k, width * 0.26, rock,
                   tex="mountain_rock")  # fmt: skip
            r.part("pyramid", width * 0.05, height * k * 0.93, dz * width, width * 0.06, height * k * 0.14, width * 0.05,
                   snow)  # fmt: skip


ROD = (176, 104, 60)  # copper: the lightning rod on the dome's crown
BRASS = (184, 140, 70)  # the telescope's brass
BRASS_DARK = (130, 96, 48)
OAK_DARK = (70, 48, 34)
LEATHER = (74, 34, 28)
OILCLOTH = (58, 62, 52)
VAULT_STEP = 4.0  # metres between the vault's ribs along its foot
BAR_STEP = 2.0  # and between the cage-wall's bars


def _vault_perimeter(x0, z0, x1, z1):
    """Points round the rectangle (x0, z0)-(x1, z1), clockwise from its -X/-Z corner, each side's first
    corner then the rest about `VAULT_STEP` apart: the feet of the vault's ribs."""
    corners = ((x0, z0), (x1, z0), (x1, z1), (x0, z1))
    points = []
    for i, (ax, az) in enumerate(corners):
        bx, bz = corners[(i + 1) % 4]
        n = max(1, rround(math.hypot(bx - ax, bz - az) / VAULT_STEP))
        points += [(ax + (bx - ax) * j / n, az + (bz - az) * j / n) for j in range(n)]
    return points


def _pane(r, a, b, c, e, rgb, hang=0.0):
    """A pane of glass between the vault's points a, b (below) and c, e (above), leaning with it, or
    `hang` radians further where it has come loose."""
    mid = [(a[i] + b[i] + c[i] + e[i]) / 4 for i in range(3)]
    across = math.hypot(b[0] - a[0], b[2] - a[2])
    up = [(c[i] + e[i] - a[i] - b[i]) / 2 for i in range(3)]
    ry = math.atan2(-(b[2] - a[2]), b[0] - a[0])
    lean = math.pi / 2 - math.atan2(up[1], math.hypot(up[0], up[2]))
    inward = math.sin(ry) * up[0] + math.cos(ry) * up[2]
    rx = (lean + hang) * (1 if inward > 0 else -1)
    r.part("cube", *mid, across * 0.8, math.hypot(*up) * 0.8, 0.03, rgb, rx=rx, ry=ry)


def anatomy_dome(r, w, d, spring=4.8, rise=6.0, walled="", seed=0):
    """The iron cage over Herran's anatomy theatre at the top of his keep, shutting in the whole of its
    `w` by `d` metres of floor (centred on the origin), corners and all. A cage-wall of black iron bars
    stands on the parapets, but not on the sides listed in `walled` ("n", "s", "e", "w", with -Z north
    and -X west), which stand against the keep: there the cage rests on iron corbels in its face, its
    springing beam `spring` metres up, clear of the door's arch. Over it a cloister vault of ribs rises
    `rise` metres more to a flat crown, with an iron lantern and a copper lightning rod. Its glass is
    long gone but for a few panes, and in its +X/-Z quarter the storm has broken it open: ribs snapped
    short and bent down, the panes between them hanging loose."""
    out = 0.4  # how far past the floor's edge the bars stand, on the parapet
    x0 = -w / 2 + (0.15 if "w" in walled else -out)
    x1 = w / 2 - (0.15 if "e" in walled else -out)
    z0 = -d / 2 + (0.15 if "n" in walled else -out)
    z1 = d / 2 - (0.15 if "s" in walled else -out)
    sides = {
        "n": ((x0, z0), (x1, z0)),
        "e": ((x1, z0), (x1, z1)),
        "s": ((x1, z1), (x0, z1)),
        "w": ((x0, z1), (x0, z0)),
    }
    bars = set()
    for side, (a, b) in sides.items():
        _bar(r, (a[0], spring, a[1]), (b[0], spring, b[1]), 0.2, IRON)  # the springing beam
        if side in walled:
            continue
        _bar(r, (a[0], 1.2, a[1]), (b[0], 1.2, b[1]), 0.16, IRON)  # the wall plate on the parapet
        _bar(r, (a[0], 3.0, a[1]), (b[0], 3.0, b[1]), 0.08, LEAD)  # the mid-rail
        n = max(1, rround(math.hypot(b[0] - a[0], b[1] - a[1]) / BAR_STEP))
        bars |= {(rround((a[0] + (b[0] - a[0]) * j / n) * 100), rround((a[1] + (b[1] - a[1]) * j / n) * 100))
                 for j in range(n + 1)}  # fmt: skip
    for bx, bz in sorted(bars):  # the cage-wall's bars
        _bar(r, (bx / 100, 1.2, bz / 100), (bx / 100, spring, bz / 100), 0.07, IRON)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    feet = _vault_perimeter(x0, z0, x1, z1)
    top = math.acos(0.18)  # the crown is the springing rectangle at 0.18 of its size

    def at(p, k):  # the point k fifths of the way up the rib springing from p
        s = math.cos(top * k / 5)
        return (
            cx + (p[0] - cx) * s,
            spring + rise * math.sin(top * k / 5) / math.sin(top),
            cz + (p[1] - cz) * s,
        )

    quarter = [i for i, p in enumerate(feet) if p[0] > cx and p[1] < cz]
    start = seed % max(1, len(quarter) - 2)
    broken = set(quarter[start : start + 3])
    for i, p in enumerate(feet):
        for k in range(2 if i in broken else 5):
            _bar(r, at(p, k), at(p, k + 1), 0.16, IRON if k % 2 == 0 else LEAD)  # the rib
        if i in broken:  # its stub, bent down and out where it snapped
            a = at(p, 2)
            dx, dz = p[0] - cx, p[1] - cz
            n = math.hypot(dx, dz)
            _bar(r, a, (a[0] + dx / n * 0.6, a[1] - 1.0, a[2] + dz / n * 0.6), 0.12, IRON)
        against = ("w" in walled and p[0] == x0) or ("e" in walled and p[0] == x1)
        against |= ("n" in walled and p[1] == z0) or ("s" in walled and p[1] == z1)
        if against:  # an iron corbel in the keep's face under its foot
            r.part("cube", p[0], spring - 0.35, p[1], 0.36, 0.5, 0.36, IRON)
    for k in range(1, 6):  # the purlins, rib to rib, ring above ring, and the crown
        for i, p in enumerate(feet):
            j = (i + 1) % len(feet)
            if k >= 2 and (i in broken or j in broken):
                continue
            _bar(r, at(p, k), at(feet[j], k), 0.08 if k < 5 else 0.16, LEAD if k % 2 else IRON)
    for i in sorted(broken):  # the panes hanging loose at the breach
        j = (i + 1) % len(feet)
        _pane(r, at(feet[i], 1), at(feet[j], 1), at(feet[i], 2), at(feet[j], 2), PANE, hang=0.5)
    for i in range(0, len(feet), 5):  # and the few still in their frames
        j = (i + 1) % len(feet)
        if i not in broken and j not in broken:
            _pane(r, at(feet[i], 0), at(feet[j], 0), at(feet[i], 1), at(feet[j], 1), PANE)
    crown = spring + rise
    r.part("cube", cx, crown + 0.1, cz, 1.2, 0.12, 1.2, IRON)  # the lantern on the crown
    for sx, sz in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        r.part("cube", cx + sx * 0.5, crown + 0.6, cz + sz * 0.5, 0.08, 1.0, 0.08, IRON)
    r.part("pyramid", cx, crown + 1.35, cz, 1.3, 0.6, 1.3, LEAD)
    r.part("cyl", cx, crown + 2.6, cz, 0.06, 2.0, 0.06, ROD)  # the lightning rod
    r.part("cone", cx, crown + 3.75, cz, 0.12, 0.3, 0.12, ROD)


def telescope(r, seed):
    """Herran's telescope: a brass refractor on an equatorial head, on a field tripod of dark oak, its
    object glass trained along +X and up at the storm. A tray between the legs keeps his folio, an
    eyepiece case, a pair of dividers and a hand lens; an oilcloth rag is thrown over one leg against
    the rain."""
    for i in range(3):  # the tripod, one leg back under the eyepiece
        a = math.pi + i * math.tau / 3
        foot = (math.cos(a) * 0.75, 0.0, math.sin(a) * 0.75)
        _bar(r, foot, (math.cos(a) * 0.1, 1.35, math.sin(a) * 0.1), 0.07, OAK_DARK)
        r.part("cube", foot[0], 0.06, foot[2], 0.09, 0.12, 0.09, BRASS_DARK)  # its brass shoe
    r.part("cyl", 0, 0.55, 0, 0.62, 0.03, 0.62, OAK_DARK)  # the spreader tray
    r.part("cube", -0.1, 0.58, 0.08, 0.26, 0.03, 0.2, LEATHER, ry=0.3 + seed * 0.1)  # his folio
    r.part("cube", 0.14, 0.6, -0.1, 0.12, 0.07, 0.08, BRASS_DARK, ry=-0.4)  # the eyepiece case
    _bar(r, (-0.05, 0.575, -0.15), (0.12, 0.575, -0.22), 0.015, BRASS)  # the dividers
    _bar(r, (-0.05, 0.575, -0.15), (0.13, 0.575, -0.16), 0.015, BRASS)
    r.part("cyl", 0.08, 0.575, 0.18, 0.08, 0.015, 0.08, PANE)  # the hand lens
    r.part("cube", 0.15, 0.575, 0.18, 0.08, 0.015, 0.02, BRASS)
    r.part("cyl", 0, 1.38, 0, 0.2, 0.08, 0.2, BRASS_DARK)  # the tripod's head
    r.part("cyl", 0, 1.5, 0, 0.08, 0.18, 0.08, BRASS)  # the pillar
    r.part("cube", 0, 1.66, 0, 0.3, 0.12, 0.12, BRASS, rz=0.7)  # the polar axis
    r.part("cyl", -0.06, 1.62, 0.08, 0.16, 0.02, 0.16, GILT, rx=math.pi / 2)  # its setting circle
    r.part("cube", 0.04, 1.78, 0, 0.12, 0.12, 0.16, BRASS_DARK)  # the declination housing
    _bar(r, (0.04, 1.76, -0.06), (-0.12, 1.5, -0.34), 0.03, IRON)  # the counterweight's shaft
    r.part("sphere", -0.12, 1.5, -0.34, 0.14, 0.14, 0.14, IRON)
    e = 0.6  # the tube's elevation
    ce, se = math.cos(e), math.sin(e)

    def tube(s, dia, length, rgb, up=0.0):  # a drum of the tube, s metres along it from its cradle
        r.part(
            "cyl",
            0.12 + ce * s - se * up,
            1.9 + se * s + ce * up,
            0,
            dia,
            length,
            dia,
            rgb,
            rz=e - math.pi / 2,
        )

    tube(0.0, 0.13, 1.3, BRASS)  # the main tube
    for s in (-0.45, 0.0, 0.45):
        tube(s, 0.15, 0.04, BRASS_DARK)  # its bands
    tube(-0.22, 0.145, 0.12, LEATHER)  # the grip
    tube(0.78, 0.17, 0.3, BRASS)  # the dew shield
    tube(0.93, 0.14, 0.01, PANE)  # the object glass
    tube(-0.72, 0.08, 0.15, BRASS_DARK)  # the draw tubes
    tube(-0.84, 0.06, 0.12, BRASS)
    tube(0.1, 0.045, 0.36, BRASS_DARK, up=0.13)  # the finder
    for s in (-0.05, 0.25):
        tube(s, 0.03, 0.1, BRASS, up=0.07)  # its brackets
    back = (0.12 - ce * 0.92, 1.9 - se * 0.92)
    r.part("cube", back[0], back[1], 0, 0.06, 0.06, 0.06, BRASS)  # the star diagonal
    r.part("cyl", back[0] - 0.02, back[1] + 0.08, 0, 0.04, 0.1, 0.04, BRASS_DARK)  # the eyepiece
    for side in (-1, 1):
        r.part("cyl", 0.12 - ce * 0.7, 1.9 - se * 0.7 - 0.06, side * 0.07, 0.04, 0.03, 0.04, BRASS,
               rx=math.pi / 2)  # fmt: skip  # the focus knobs
        _bar(r, (0.04, 1.74, side * 0.08), (0.1, 1.3, side * 0.16), 0.012, BRASS)  # the slow-motion rods
        r.part("sphere", 0.1, 1.29, side * 0.16, 0.04, 0.04, 0.04, BRASS_DARK)
    a = math.pi + math.tau / 3  # the rag over a leg
    r.part("cube", math.cos(a) * 0.45, 0.6, math.sin(a) * 0.45, 0.04, 0.4, 0.22, OILCLOTH, ry=-a, rz=0.4)


def candelabra(r, seed, t):
    """A tall standing candelabrum of black iron, taller than a man: a tripod foot, a twisted stem and
    five branches, a fat tallow candle guttering on each, wax run down over the drip-pans."""
    for i in range(3):  # the tripod
        a = i * math.tau / 3 + seed
        r.part("cube", math.cos(a) * 0.22, 0.08, math.sin(a) * 0.22, 0.4, 0.06, 0.06, IRON, ry=-a, rz=-0.3)
    r.part("cyl", 0, 0.2, 0, 0.16, 0.2, 0.16, IRON)  # the foot's boss
    for k in range(6):  # the twisted stem
        r.part("cube", 0, 0.35 + k * 0.22, 0, 0.06, 0.22, 0.06, IRON, ry=k * 0.6)
    r.part("cyl", 0, 1.7, 0, 0.12, 0.08, 0.12, IRON)  # the knop where the branches spring
    for i in range(5):
        a = i * math.tau / 5 + seed * 0.3
        x, z = (math.cos(a) * 0.36, math.sin(a) * 0.36) if i else (0.0, 0.0)
        y = 1.95 if i else 2.1
        if i:
            _bar(r, (0, 1.7, 0), (x, y - 0.06, z), 0.035, IRON)  # its branch
        r.part("cyl", x, y - 0.04, z, 0.14, 0.03, 0.14, IRON)  # the drip-pan
        r.part("cyl", x, y + 0.08, z, 0.07, 0.2, 0.07, TALLOW)  # the candle
        r.part("cube", x + 0.03, y, z, 0.02, 0.12, 0.02, _dim(TALLOW, 1.05))  # a run of wax
        flame = 0.045 * (1 + 0.15 * math.sin(t * 9 + i * 1.7 + seed))
        r.part("cone", x, y + 0.24, z, flame, flame * 3, flame, FLAME, glow=True)


def gate_statue(r, seed):
    """A statue along the causeway and the halls: a hooded knight of grey stone on a stepped plinth, a
    tall shield grounded at its side and a long sword held point-down before it, its face lost in the
    hood, rain-streaked and lichened."""
    stone, dark = CASTLE, CASTLE_DARK
    r.part("cube", 0, 0.2, 0, 1.4, 0.4, 1.4, dark, tex="castle_stone")  # the plinth
    r.part("cube", 0, 0.5, 0, 1.1, 0.2, 1.1, stone, tex="castle_stone")
    r.part("cube", 0, 0.7, 0, 0.9, 0.2, 0.9, dark)
    r.part("cube", 0, 1.45, 0, 0.5, 1.3, 0.7, stone)  # the robed legs
    r.part("cube", 0, 2.3, 0, 0.46, 0.6, 0.66, stone)  # the chest
    for side in (-1, 1):
        r.part("sphere", 0, 2.55, side * 0.34, 0.2, 0.14, 0.2, stone)  # the pauldrons
    r.part("cube", -0.04, 2.7, 0, 0.3, 0.3, 0.3, stone)  # the hood
    r.part("pyramid", -0.08, 2.92, 0, 0.32, 0.2, 0.3, stone)  # its peak
    r.part("cube", 0.12, 2.68, 0, 0.04, 0.18, 0.18, (30, 30, 34))  # the shadow of the face
    r.part("cube", 0.32, 1.6, 0, 0.06, 1.8, 0.14, _dim(stone, 1.1))  # the sword, point down
    r.part("cube", 0.32, 2.52, 0, 0.06, 0.06, 0.5, dark)  # its cross
    r.part("cube", 0.32, 2.66, 0, 0.05, 0.22, 0.05, dark)  # its grip
    for side in (-1, 1):  # the hands folded on the pommel
        r.part("cube", 0.28, 2.72, side * 0.06, 0.12, 0.1, 0.1, stone)
    with r.at(0.05, 1.6, -0.45):  # the shield, grounded at its side
        r.part("cube", 0, 0, 0, 0.1, 1.6, 0.6, dark)
        _hand_device(r, 0.06, 0.1, 0, 0.4, stone)
    r.part("cube", -0.25, 1.9, 0.22, 0.02, 0.8, 0.1, (80, 92, 76))  # lichen down its back


def _floating_arms(r, x, y, z, n, rgb, t):
    """A thing with many arms afloat in a vat (or slumped in a cage): a pale body and `n` arms reaching
    out of it, drifting."""
    r.part("sphere", x, y, z, 0.24, 0.3, 0.22, rgb)
    for i in range(n):
        a = i * math.tau / n
        sway = math.sin(t * 0.8 + i) * 0.2
        _bar(r, (x, y, z), (x + math.cos(a) * 0.3, y + 0.18 + sway, z + math.sin(a) * 0.3), 0.05, rgb)
        _bar(r, (x + math.cos(a) * 0.3, y + 0.18 + sway, z + math.sin(a) * 0.3),
             (x + math.cos(a) * 0.42, y - 0.1 + sway, z + math.sin(a) * 0.42), 0.045, rgb)  # fmt: skip


def vat(r, seed, t):
    """A vat of the laboratory: a tall glass tank bound in iron hoops, full of a green fluid that glows,
    a many-armed thing hung in it, bubbles rising past it; a lid of riveted iron with pipes running up
    out of it to the ceiling."""
    r.part("cyl", 0, 0.15, 0, 1.3, 0.3, 1.3, IRON)  # the base
    r.part("cyl", 0, 0.9, 0, 1.1, 1.3, 1.1, _dim(VAT_GREEN, 0.75), glow=True)  # the fluid
    r.part("cyl", 0, 0.9, 0, 1.16, 1.32, 1.16, PANE)  # the glass, round it
    for y in (0.35, 0.9, 1.45):
        r.part("cyl", 0, y, 0, 1.22, 0.06, 1.22, IRON)  # the hoops
    for i in range(4):  # the iron uprights
        a = i * math.pi / 2 + 0.4
        r.part("cube", math.cos(a) * 0.6, 0.9, math.sin(a) * 0.6, 0.06, 1.4, 0.06, IRON)
    _floating_arms(r, 0, 0.95 + math.sin(t * 0.6 + seed) * 0.05, 0, 5 + seed % 3, (200, 210, 180), t)
    for i in range(3):  # bubbles rising
        k = (t * 0.4 + i / 3 + seed * 0.1) % 1
        r.part("sphere", math.sin(i * 2.1 + seed) * 0.3, 0.35 + k * 1.1, math.cos(i * 2.1) * 0.3, 0.05, 0.05, 0.05,
               (190, 255, 190), glow=True)  # fmt: skip
    r.part("cyl", 0, 1.62, 0, 1.24, 0.12, 1.24, IRON)  # the lid
    for i in range(6):
        a = i * math.tau / 6
        r.part("sphere", math.cos(a) * 0.56, 1.69, math.sin(a) * 0.56, 0.04, 0.04, 0.04, LEAD)  # its rivets
    for dx in (-0.25, 0.25):  # the pipes up out of it
        r.part("cyl", dx, 2.3, 0.1, 0.12, 1.3, 0.12, IRON)


def dissecting_table(r, seed):
    """A dissecting table: a slab of iron on heavy legs, a gutter round its edge and a drain at its foot,
    leather straps across it, and on it a draped body with an extra arm hanging off the side; a tray of
    saws and knives on a stand beside it."""
    r.part("cube", 0, 0.88, 0, 1.0, 0.08, 1.9, (120, 120, 124))  # the slab
    r.part("cube", 0, 0.92, 0, 0.9, 0.02, 1.8, (90, 60, 56))  # old stains in its gutter
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * 0.42, 0.42, dz * 0.82, 0.1, 0.84, 0.1, IRON)  # the legs
    r.part("cyl", 0, 0.82, 0.92, 0.1, 0.1, 0.1, IRON)  # the drain
    r.part("cube", 0, 1.0, 0, 0.6, 0.14, 1.5, (170, 164, 150))  # the draped body
    r.part("sphere", 0, 1.05, -0.72, 0.16, 0.12, 0.14, (176, 170, 156))  # its head under the sheet
    for z in (-0.4, 0.1, 0.6):
        r.part("cube", 0, 1.08, z, 0.64, 0.03, 0.08, (70, 46, 30))  # the straps
    _bar(r, (0.32, 1.0, 0.0), (0.5, 0.6, 0.12), 0.06, (186, 160, 146))  # an arm hanging off the side
    _bar(r, (0.32, 1.0, -0.3), (0.52, 0.66, -0.4), 0.06, (186, 160, 146))  # and another, sewn on
    with r.at(-0.85, 0, 0.5):  # the tray of instruments
        r.part("cyl", 0, 0.45, 0, 0.06, 0.9, 0.06, IRON)
        r.part("cube", 0, 0.92, 0, 0.5, 0.03, 0.36, (130, 130, 134))
        for k in range(4):
            r.part("cube", -0.12 + k * 0.08, 0.95, 0, 0.03, 0.02, 0.26, (200, 200, 206))  # a knife, a saw


def specimen_cage(r, seed):
    """A tall cage of black iron bars, its door chained shut, and slumped in it one of Herran's
    failures, a heap of grey flesh with too many arms through the bars."""
    for i in range(12):  # the bars
        a = i * math.tau / 12
        r.part("cube", math.cos(a) * 0.7, 1.2, math.sin(a) * 0.7, 0.05, 2.4, 0.05, IRON)
    r.part("cyl", 0, 0.05, 0, 1.5, 0.1, 1.5, IRON)  # the floor of it
    r.part("cyl", 0, 2.4, 0, 1.5, 0.08, 1.5, IRON)  # the top ring
    r.part("cone", 0, 2.7, 0, 1.5, 0.5, 1.5, IRON)  # its cap
    r.part("cyl", 0, 3.0, 0, 0.05, 0.4, 0.05, IRON)  # the chain it hangs from
    r.part("cube", 0.72, 1.2, 0, 0.04, 0.3, 0.2, (90, 80, 60))  # the chain round its door
    rgb = (150, 140, 130)
    r.part("sphere", 0, 0.4, 0, 0.5, 0.36, 0.44, rgb)  # the heap
    for i in range(5 + seed % 3):  # its arms, some out through the bars
        a = i * math.tau / (5 + seed % 3) + seed
        _bar(r, (0, 0.5, 0), (math.cos(a) * 0.9, 0.3 + 0.2 * (i % 2), math.sin(a) * 0.9), 0.07, rgb)


def hand_rack(r, seed):
    """The ossuary of hands: a rack of black oak on the wall at local -X, rows of iron hooks, and on
    them hands, cut off at the wrist, sorted by size, each with a tag on a string."""
    r.part("cube", -0.86, 1.6, 0, 0.1, 1.8, 1.7, (52, 40, 30), tex="wood_plank")  # the board
    for y in (0.9, 1.6, 2.3):
        r.part("cube", -0.8, y + 0.22, 0, 0.06, 0.06, 1.7, (40, 30, 22))  # a rail
        for k in range(4):
            z = -0.6 + k * 0.4
            size = 0.08 + ((seed + k + rround(y * 3)) % 3) * 0.015
            r.part("cube", -0.76, y + 0.18, z, 0.04, 0.08, 0.02, IRON)  # the hook
            r.part("cube", -0.74, y, z, 0.05, size * 1.6, size * 1.2, (176, 156, 140))  # the hand
            for f in range(3):
                r.part(
                    "cube",
                    -0.74,
                    y - size * 1.2,
                    z + (f - 1) * size * 0.35,
                    0.03,
                    size,
                    0.02,
                    (170, 150, 134),
                )
            r.part("cube", -0.72, y + 0.04, z + size * 0.7, 0.01, 0.06, 0.05, (210, 200, 170))  # its tag


def lab_bench(r, seed):
    """A laboratory bench: a long table of stained oak, an alembic over a cold burner, retorts, a rack
    of phials (one still glowing), a ledger left open, and a jar with a hand in it."""
    oak = (70, 52, 38)
    r.part("cube", 0, 0.92, 0, 0.9, 0.08, 1.9, oak, tex="wood_plank")  # the top
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * 0.38, 0.45, dz * 0.85, 0.08, 0.9, 0.08, _dim(oak, 0.8))  # the legs
    r.part("cube", 0, 0.3, 0, 0.8, 0.04, 1.8, _dim(oak, 0.8))  # the shelf under it
    r.part("cyl", 0, 1.02, -0.6, 0.24, 0.12, 0.24, IRON)  # the burner
    r.part("sphere", 0, 1.24, -0.6, 0.3, 0.3, 0.3, PANE)  # the alembic's flask
    _bar(r, (0, 1.4, -0.6), (0.05, 1.55, -0.2), 0.04, PANE)  # its neck
    _bar(r, (0.05, 1.55, -0.2), (0.1, 1.1, 0.05), 0.03, PANE)  # the beak, down to the receiver
    r.part("sphere", 0.1, 1.06, 0.08, 0.16, 0.16, 0.16, PANE)  # the receiver
    for k in range(4):  # the rack of phials
        rgb = ((120, 200, 90), (160, 60, 60), (90, 120, 200), (200, 180, 80))[(seed + k) % 4]
        r.part("cyl", -0.28, 1.06, 0.4 + k * 0.1, 0.06, 0.2, 0.06, rgb, glow=k == seed % 4)
    r.part("cube", -0.28, 1.0, 0.55, 0.1, 0.04, 0.5, oak)  # the rack
    r.part("cube", 0.2, 0.97, 0.6, 0.3, 0.02, 0.4, (220, 210, 186))  # the ledger, open
    r.part("cube", 0.2, 0.98, 0.6, 0.3, 0.02, 0.02, (60, 40, 30))  # its spine
    r.part("cyl", 0.25, 1.1, -0.2, 0.2, 0.3, 0.2, PANE)  # the jar
    r.part("cube", 0.25, 1.08, -0.2, 0.08, 0.12, 0.06, (176, 156, 140))  # the hand in it


def sealed_gate(r, open_t, frame, eyes, t):
    """The barbican's sealed gate (`door model=sealed`, `world/seals.py`): two great leaves of black
    oak strapped in iron between jambs of dark stone, and over them a carved stone mask of Herran's
    hand with two eyes of fire in its palm, one for each Warden that keeps it; each goes out as its
    Warden falls, and with both out the leaves grind open (slide up, as `open_t` runs to 1)."""
    frame = max(frame, 4.2)
    stone, dark = CASTLE, CASTLE_DARK
    for z in (-0.92, 0.92):
        r.part("cube", 0, frame / 2, z, 0.6, frame, 0.3, stone, tex="castle_stone")  # the jamb
        r.part("cube", 0, 0.25, z, 0.7, 0.5, 0.36, dark)  # its plinth
    r.part("cube", 0, 3.3, 0, 0.66, 0.4, 2.1, dark, tex="castle_stone")  # the lintel
    if frame > 3.5:
        r.part("cube", 0, (3.5 + frame) / 2, 0, 0.5, frame - 3.5, 1.6, stone, tex="castle_stone")
    for face in (-1, 1):  # the mask of the hand, its eyes in the palm
        with r.at(face * 0.34, 3.82, 0):
            r.part("cube", 0, 0, 0, 0.06, 0.5, 0.56, dark)
            for f in range(4):
                r.part("cube", 0, 0.38, (f - 1.5) * 0.13, 0.06, 0.28, 0.08, dark)  # its fingers
            for k, dz in enumerate((-0.12, 0.12)):
                burning = k < eyes
                r.part(
                    "sphere",
                    face * 0.04,
                    0.02,
                    dz,
                    0.07,
                    0.07,
                    0.07,
                    EMBER_EYE if burning else COLD,
                    glow=burning,
                )
    lift = _ease(min(open_t, 1.0)) * 2.9
    with r.at(0, lift, 0):  # the leaves, sliding up into the masonry together
        for side in (-1, 1):
            z = side * 0.4
            r.part("cube", 0, 1.55, z, 0.2, 3.1, 0.78, (54, 40, 30), tex="wood_plank")
            for face in (-1, 1):
                for y in (0.4, 1.5, 2.6):
                    r.part("cube", face * 0.11, y, z, 0.03, 0.16, 0.8, IRON)  # the straps
                    r.part("sphere", face * 0.12, y, z + side * 0.3, 0.04, 0.04, 0.04, LEAD)  # their studs
        r.part("cube", 0, 1.55, 0, 0.24, 3.1, 0.04, IRON)  # the meeting stile


def herran_arch(r, style, t, lit):
    """Over Herran's great door: a carved hand of stone, palm out, a sun burning gold in it while he lives."""
    with r.at(0, 3.55, 0):
        _hand_device(r, 0.26, 0.0, 0, 0.6, _dim(style.stone, 1.15))
        r.part("cyl", 0.28, 0.0, 0, 0.14, 0.04, 0.14, SUN_GOLD if lit else COLD, rz=math.pi / 2, glow=lit)
        r.part("cyl", -0.28, 0.0, 0, 0.14, 0.04, 0.14, SUN_GOLD if lit else COLD, rz=math.pi / 2, glow=lit)


def herran_leaf(r, style, side, face, t, lit):
    """Dark oak leaves, an iron hand cast on each panel, palm out."""
    r.part("cube", face * 0.085, 1.4, -side * 0.45, 0.02, 1.2, 0.6, _dim(style.wood, 0.8))  # the panel
    r.part("cube", face * 0.09, 1.5, -side * 0.45, 0.02, 0.3, 0.22, style.iron)  # the cast hand


def sentinel_arch(r, style, t, lit):
    """Over the Hall of Sentinels' door: two stone blades crossed behind a carved great helm, its eyes
    burning while the sentinels stand."""
    with r.at(0, 3.6, 0):
        for a in (-0.6, 0.6):
            r.part("cube", 0.24, 0, 0, 0.04, 1.2, 0.12, _dim(style.stone, 1.15), rx=a)  # the blades
        r.part("cube", 0.26, 0, 0, 0.2, 0.32, 0.28, style.stone)  # the helm
        r.part("pyramid", 0.26, 0.24, 0, 0.2, 0.16, 0.28, style.stone)
        for dz in (-0.06, 0.06):
            r.part("cube", 0.37, 0.02, dz, 0.02, 0.04, 0.04, CRACK_FIRE if lit else COLD, glow=lit)


def sentinel_leaf(r, style, side, face, t, lit):
    """Plain leaves of stone-grey oak, a raised stone panel on each, a carved shield on it."""
    r.part("cube", face * 0.085, 1.5, -side * 0.45, 0.02, 1.6, 0.6, _dim(style.wood, 0.85))
    r.part("cube", face * 0.09, 1.6, -side * 0.45, 0.02, 0.5, 0.36, style.stone)  # the shield


def surgeons_cleaver(r):
    """Herran's own cleaver, from his laboratory: a turned ebony handle bound in brass, a long narrow
    blade of bright steel squared off at its tip, its spine notched for a thumb and a brass ferrule,
    graduations etched down its flat."""
    r.part("cyl", 0, 0.0, 0, 0.06, 0.4, 0.06, (34, 26, 24))  # the ebony handle
    for y in (-0.12, 0.08):
        r.part("cyl", 0, y, 0, 0.07, 0.03, 0.07, GILT)  # its brass bands
    r.part("sphere", 0, -0.22, 0, 0.05, 0.05, 0.05, GILT)  # the butt
    r.part("cyl", 0, 0.22, 0, 0.07, 0.05, 0.07, GILT)  # the ferrule
    r.part("cube", 0, 0.56, 0.1, 0.03, 0.66, 0.22, (176, 178, 186))  # the blade
    r.part("wedge", 0, 0.56, 0.22, 0.03, 0.04, 0.66, (226, 228, 236), rx=math.pi / 2)  # its edge
    r.part("cube", 0, 0.56, -0.015, 0.045, 0.68, 0.04, (110, 112, 120))  # the spine
    for k in range(4):  # the thumb notches along the spine
        r.part("cube", 0, 0.32 + k * 0.05, -0.04, 0.05, 0.02, 0.02, (110, 112, 120))
    for k in range(5):  # the graduations etched down its flat
        r.part("cube", 0.017, 0.4 + k * 0.1, 0.05, 0.005, 0.01, 0.08, (90, 92, 100))
