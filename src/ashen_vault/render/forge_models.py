"""Models for the Cinderhold: its iron foes, the twin gargoyles and the fortress dressing.
Original low-poly models assembled from primitives; like everything in `models`, they face +X."""

import math

from ashen_vault.ai.enemy import COMBO_GAP
from ashen_vault.render.models import (
    EMBER,
    _flame,
    _spider_move,
    death_fall,
    strike_angle,
    walk_cycle,
)

BLACK_IRON = (62, 60, 66)
DARK = (40, 38, 44)
RIVET = (110, 106, 112)
MOLTEN = (255, 120, 30)
WHITE_HOT = (255, 230, 150)
CRUST = (52, 40, 36)
STATUE = (112, 110, 106)  # a perched gargoyle, grey as the parapet it squats on
STATUE_DARK = (84, 82, 80)
BOW_WOOD = (78, 52, 34)
STRING = (200, 196, 180)
THUNDER = (200, 225, 255)
ARCANE = (190, 120, 255)


def _windup_k(e):
    return min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0


# --- the Forge Golem ---------------------------------------------------------------------------


def forge_golem(r, e, t):
    """A walking furnace of riveted black iron: stubby legs, fists like anvils, a slit of fire for
    eyes, and its firebox hanging open on its back, the weak spot. A sweep spins it round with its
    arms out; a slam raises both fists and brings them down. Slain, it sinks to its knees, topples
    forward and its fire goes out."""
    swing = walk_cycle(e, t) * 0.4
    kneel = death_fall(e, 0.6)
    topple = death_fall(e, 1.5)
    dead = e.state == "dead"
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit = strike_angle(e)
    k = _windup_k(e)
    both = None
    crouch = 0.0
    if e.attack_kind == "slam" and e.state in ("windup", "attack"):
        if e.state == "windup":
            both = -2.8 * k
        else:
            both = -2.8 + 3.6 * min(e.state_t / 0.15, 1)
            crouch = -0.2 * min(e.state_t / 0.15, 1)
    elif e.attack_kind == "sweep" and e.state in ("windup", "attack"):
        both = -1.55  # arms held out level while it spins
    hot = (255, 240, 200) if e.state == "hurt" else MOLTEN
    fire = CRUST if dead else hot
    with (
        r.at(0, lift * 0.4 + crouch - 0.5 * kneel + 0.95 * topple, 0, ry=spin),
        r.at(0, 0.0, 0, rz=-1.2 * topple),
    ):
        for side, a in ((-0.32, swing), (0.32, -swing)):
            with r.at(0, 0.8, side, rz=a + 1.5 * kneel):
                r.part("cube", 0, -0.4, 0, 0.42, 0.8, 0.38, BLACK_IRON)
                r.part("cube", 0.1, -0.78, 0, 0.6, 0.16, 0.44, DARK)
        r.part("cube", 0, 0.95, 0, 0.7, 0.3, 0.9, DARK)  # hips
        r.part("cube", 0, 1.55, 0, 0.9, 1.0, 1.15, BLACK_IRON)  # the furnace body
        for i in range(4):  # rivet rows
            r.part("cube", 0.46, 1.2 + i * 0.22, 0, 0.03, 0.04, 1.0, RIVET)
        r.part("cube", 0.46, 1.65, 0, 0.04, 0.3, 0.5, fire, glow=not dead)  # belly grate
        for i in range(3):
            r.part("cube", 0.48, 1.65, -0.16 + i * 0.16, 0.04, 0.34, 0.04, DARK)
        # The open firebox on its back: strike it from behind.
        r.part("cube", -0.47, 1.6, 0, 0.06, 0.62, 0.7, fire, glow=not dead)
        r.part("cube", -0.62, 1.95, 0, 0.3, 0.06, 0.74, DARK, rz=0.6)  # the hatch, hanging open
        if not dead:
            _flame(r, -0.5, 1.85, 0, 0.16, t)
        r.part("cyl", -0.2, 2.25, 0.3, 0.12, 0.5, 0.12, DARK)  # chimney stack
        with r.at(0.15, 2.18, 0):  # a squat helm-head sunk between the shoulders
            r.part("cube", 0, 0, 0, 0.5, 0.36, 0.56, BLACK_IRON)
            r.part("cube", 0.26, 0.02, 0, 0.03, 0.06, 0.38, fire, glow=not dead)
        for side, z in ((1, 0.68), (-1, -0.68)):
            a = both if both is not None else (hit if side == 1 else swing * 0.6)
            with r.at(0, 1.95, z, rz=a - 0.5 * kneel):
                r.part("cube", 0, -0.1, 0, 0.42, 0.42, 0.42, DARK)  # shoulder
                r.part("cube", 0, -0.55, 0, 0.3, 0.75, 0.3, BLACK_IRON)
                r.part("cube", 0.05, -1.05, 0, 0.5, 0.42, 0.5, DARK)  # anvil fist
                r.part("cube", 0.05, -1.05, 0, 0.56, 0.1, 0.56, RIVET)


# --- the Iron Bowman ---------------------------------------------------------------------------


def iron_bowman(r, e, t):
    """A gaunt archer in black scale and a tall slit-visored helm, a longbow of dark wood. He draws
    the string back to his cheek on the windup and lets fly; close in, he clubs you with the bow.
    Slain, he sags and falls onto his back."""
    swing = walk_cycle(e, t) * 0.6
    fall = death_fall(e, 0.8)
    dead = e.state == "dead"
    k = _windup_k(e)
    shooting = e.attack_kind == "shot" and e.state in ("windup", "attack")
    bashing = e.attack_kind == "bite" and e.state in ("windup", "attack")
    draw = k if shooting and e.state == "windup" else 0.0
    bow_arm = -1.5 if shooting else strike_angle(e) if bashing else swing * 0.4 - 0.3
    with r.at(0, 0.3 * fall, 0, rz=1.35 * fall):
        for side, a in ((-0.13, swing), (0.13, -swing)):
            with r.at(0, 0.9, side, rz=a):
                r.part("cube", 0, -0.45, 0, 0.14, 0.9, 0.14, DARK)
                r.part("cube", 0.05, -0.88, 0, 0.24, 0.08, 0.15, BLACK_IRON)
        r.part("cube", 0, 1.15, 0, 0.3, 0.5, 0.44, BLACK_IRON)  # scale coat
        r.part("cube", 0, 0.9, 0, 0.34, 0.3, 0.48, (54, 44, 40))  # skirt
        r.part("cube", -0.18, 1.3, 0.1, 0.1, 0.55, 0.12, BOW_WOOD, rz=0.2)  # quiver
        for i in range(3):
            r.part("cube", -0.2, 1.62, 0.06 + i * 0.04, 0.02, 0.16, 0.02, RIVET)
        with r.at(0.02, 1.58, 0):
            r.part("cube", 0, 0.08, 0, 0.26, 0.4, 0.26, BLACK_IRON)  # tall helm
            r.part("cone", 0, 0.38, 0, 0.12, 0.22, 0.12, DARK)
            r.part("cube", 0.14, 0.08, 0, 0.02, 0.03, 0.18, MOLTEN if not dead else CRUST, glow=not dead)
        # The bow hand holds the bow out in front; the other draws the string back.
        with r.at(0, 1.42, -0.26, rz=bow_arm):
            r.part("cube", 0, -0.3, 0, 0.1, 0.6, 0.1, DARK)
            with r.at(0, -0.62, 0, rz=-bow_arm):
                r.part("cube", 0, 0, 0, 0.11, 0.13, 0.13, DARK)  # the fist round the bow's grip
                for i in range(5):  # the bow, a gentle curve of five staves
                    y = (i - 2) * 0.28
                    r.part(
                        "cube", -0.04 * abs(i - 2) ** 1.5, y, 0, 0.05, 0.3, 0.05, BOW_WOOD, rz=(i - 2) * 0.25
                    )
                pull = 0.08 + 0.45 * draw
                r.part("cube", -pull / 2 - 0.15, 0.3, 0, pull, 0.01, 0.01, STRING, rz=-0.9)
                r.part("cube", -pull / 2 - 0.15, -0.3, 0, pull, 0.01, 0.01, STRING, rz=0.9)
                if shooting and e.state == "windup":
                    r.part("cube", 0.15 - pull / 2, 0, 0, 0.9, 0.03, 0.03, (120, 116, 120))
        with r.at(0, 1.42, 0.24, rz=-1.4 * draw if shooting else -swing * 0.4):
            r.part("cube", 0, -0.3, 0, 0.1, 0.6, 0.1, DARK)
            r.part("cube", 0, -0.64, 0, 0.11, 0.12, 0.12, DARK)  # the drawing hand


# --- the Slag Hound ----------------------------------------------------------------------------


def slag_hound(r, e, t):
    """A lean hound of cooled slag, glowing through the cracks in its hide. It crouches and leaps.
    Slain, it rolls onto its side and the cracks go dark."""
    fall = death_fall(e, 0.5)
    dead = e.state == "dead"
    gait = math.sin(t * 15) * 0.6 if e.state == "chase" else math.sin(t * 2) * 0.05
    lift, _, rear, _ = _spider_move(e, t, 0.0, 1.0)
    bite = strike_angle(e) * 0.2
    crack = CRUST if dead else (255, 230, 160) if e.state == "hurt" else MOLTEN
    with r.at(0, lift * 0.7 + 0.15 * fall, 0, rx=1.4 * fall), r.at(0, 0, 0, rz=-rear):
        for x, ph in ((0.42, 0), (-0.42, math.pi)):
            for z, side in ((0.18, 1), (-0.18, -1)):
                a = gait * side * (1 if ph == 0 else -1)
                with r.at(x, 0.62, z, rz=a):
                    r.part("cube", 0, -0.3, 0, 0.12, 0.6, 0.12, CRUST)
        r.part("cube", 0, 0.75, 0, 1.0, 0.36, 0.4, CRUST)  # body
        for i in range(4):  # molten cracks along the flank
            r.part(
                "cube",
                -0.3 + i * 0.2,
                0.78,
                0.205,
                0.12,
                0.03,
                0.01,
                crack,
                rz=0.5 * (-1) ** i,
                glow=not dead,
            )
            r.part(
                "cube",
                -0.3 + i * 0.2,
                0.78,
                -0.205,
                0.12,
                0.03,
                0.01,
                crack,
                rz=0.5 * (-1) ** i,
                glow=not dead,
            )
        r.part("cube", -0.6, 0.85, 0, 0.35, 0.06, 0.06, CRUST, rz=-0.6)  # tail
        with r.at(0.55, 0.9, 0, rz=bite):
            r.part("cube", 0.15, 0, 0, 0.36, 0.26, 0.26, CRUST)
            r.part("cube", 0.36, -0.08, 0, 0.22, 0.06, 0.2, crack, glow=not dead)  # glowing maw
            r.part(
                "cube", 0.24, 0.06, 0.08, 0.03, 0.03, 0.03, WHITE_HOT if not dead else CRUST, glow=not dead
            )
            r.part(
                "cube", 0.24, 0.06, -0.08, 0.03, 0.03, 0.03, WHITE_HOT if not dead else CRUST, glow=not dead
            )
            r.part("cone", 0.05, 0.18, 0.09, 0.05, 0.14, 0.05, CRUST)
            r.part("cone", 0.05, 0.18, -0.09, 0.05, 0.14, 0.05, CRUST)


# --- the twin gargoyles --------------------------------------------------------------------------

GARGOYLES = {
    # scale, iron, horn, tail blade, glowing throat
    "brand": (1.15, (70, 66, 72), (40, 36, 40), True, False),
    "bellows": (1.0, (78, 70, 64), (50, 42, 38), False, True),
}


def _gargoyle_pose(e, t):
    """(lift, spin, pitch, arm_r, arm_l, wing, head, jaw, glow) for a gargoyle's moves. `pitch`
    tilts the whole body forward; `wing` spreads the wings (0 folded .. 1 wide); `head` lowers or
    raises it; `glow` is how hot the throat or eyes burn."""
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    k = _windup_k(e)
    kind = e.attack_kind
    acting = e.state in ("windup", "attack")
    pitch = 0.25
    arm_r = strike_angle(e)
    arm_l = -strike_angle(e) * 0.5
    wing = 0.35 + 0.15 * math.sin(t * 3)
    head = jaw = 0.0
    glow = 0.4
    if not acting:
        return lift, spin, pitch, arm_r, arm_l, wing, head, jaw, glow
    a = min(e.state_t / 0.15, 1)
    if kind == "combo" and e.state == "attack":
        i = e.combo_swing
        u = (e.state_t - i * COMBO_GAP) / COMBO_GAP
        swipe = -2.0 * min(u / 0.35, 1) if u < 0.35 else -2.0 + 2.9 * min((u - 0.35) / 0.25, 1)
        arm_r, arm_l = (swipe, 0.3) if i % 2 == 0 else (0.3, swipe)
    elif kind in ("slam", "eruption"):
        if e.state == "windup":
            arm_r = arm_l = -2.8 * k
            wing = 0.35 + 0.65 * k
            lift = 0.3 * k
        else:
            arm_r = arm_l = -2.8 + 3.6 * a
            lift = 0.3 - 0.5 * a
            wing = 1.0 - 0.5 * a
            glow = 1.0
    elif kind == "breath":
        head = -0.35 * k if e.state == "windup" else -0.45
        jaw = 0.5 * k if e.state == "windup" else 0.7
        glow = 0.4 + 0.6 * k
        pitch = 0.25 + 0.2 * k
    elif kind == "cinders":
        head = 0.5 * k if e.state == "windup" else 0.5 - 0.9 * a
        jaw = 0.6
        glow = 0.4 + 0.6 * k
    elif kind == "dive":
        if e.state == "windup":
            wing, lift, pitch = 0.35 + 0.65 * k, 0.4 * k, 0.25 - 0.3 * k
        else:
            wing, pitch, arm_r, arm_l = 0.15, 1.1, -1.2, -1.2
    elif kind == "kindle":
        pitch = 0.25 - 0.6 * (k if e.state == "windup" else 1)
        wing = 1.0
        jaw = 0.8
        head = 0.4
        glow = 1.0
        arm_r = arm_l = -1.8 + math.sin(t * 40) * 0.05
    elif kind == "pounce":
        wing = 0.8
    elif kind == "sweep":
        wing = 0.6
    return lift, spin, pitch, arm_r, arm_l, wing, head, jaw, glow


def gargoyle(r, e, t):
    """One of the iron gargoyles on the Cinderhold's roof: a hunched horned beast of riveted plate on
    bent legs, with bat wings of iron ribs. Brand is the bigger, with a tail ending in an axe-blade;
    Bellows is lighter, hovers on beating wings, and its throat glows like a forge. Perched, either is
    a grey statue, wings folded, head bowed. Slain, it pitches forward onto its face and goes cold."""
    scale, iron, horn, tail_blade, throat = GARGOYLES[e.type.id]
    perched = e.state == "perched"
    fall = death_fall(e, 0.9)
    dead = e.state == "dead"
    hover = (e.type.hover or 0.0) if not perched else 0.0
    lift, spin, pitch, arm_r, arm_l, wing, head, jaw, glow = _gargoyle_pose(e, t)
    flap = 0.0
    if hover and not dead:
        flap = math.sin(t * 9) * 0.45
        hover += math.sin(t * 4.5) * 0.1
    if perched:  # crouched on its perch, wings folded, head bowed
        pitch, arm_r, arm_l, wing, head = 0.55, 0.6, 0.6, 0.0, -0.35
        jaw = glow = spin = 0.0
        lift = -0.1
    fold = 0.0
    if dead:
        # It slumps onto its belly: the legs fold under, the chest tips level, the wings drop flat.
        wing = 0.1 * (1 - fall)
        flap = 0.0
        pitch += (1.25 - pitch) * fall
        arm_r = arm_l = -1.0 * fall
        head = -0.3 * fall
        fold = fall
    hurt = e.state == "hurt"
    body = STATUE if perched else (200, 196, 200) if hurt else iron
    dark = STATUE_DARK if perched else horn
    lit = not perched and not dead
    hot = WHITE_HOT if glow > 0.8 else MOLTEN
    legs = 0.0 if hover else walk_cycle(e, t) * 0.6
    y0 = hover * (1 - fall) + lift - 0.6 * fold
    with r.at(0, y0, 0, ry=spin, s=scale):
        # Bent, backward-jointed legs and taloned feet.
        for side, a in ((-0.25, legs), (0.25, -legs)):
            with r.at(-0.05, 0.85, side, rz=a + (0.6 if hover else 0.0) * (1 - fold) + 1.3 * fold):
                r.part("cube", 0.12, -0.2, 0, 0.18, 0.5, 0.18, body, rz=0.5)
                r.part("cube", 0.0, -0.6, 0, 0.14, 0.5, 0.14, dark, rz=-0.4)
                for c in (-0.08, 0.0, 0.08):
                    r.part("cone", 0.16, -0.85, c, 0.04, 0.16, 0.04, dark, rz=-math.pi / 2)
        with r.at(0, 0.95, 0, rz=-pitch):
            r.part("cube", 0, 0.45, 0, 0.6, 0.9, 0.7, body)  # hunched chest
            r.part("cube", 0.25, 0.4, 0, 0.12, 0.7, 0.5, dark)  # plated belly
            for i in range(3):
                r.part(
                    "cube",
                    -0.31,
                    0.3 + i * 0.22,
                    0,
                    0.03,
                    0.04,
                    0.6,
                    (120, 116, 120) if not perched else body,
                )
            if throat:  # Bellows: the furnace glow behind its ribs
                r.part("cube", 0.32, 0.65, 0, 0.04, 0.35, 0.3, hot if lit else dark, glow=lit and glow > 0.2)
            # Wings: three iron ribs and two webbed panels each, from the back of the shoulders.
            for side in (1, -1):
                spread = 0.25 + 1.2 * wing
                with r.at(-0.2, 0.85, 0.3 * side, rx=side * (spread + flap), ry=-0.3 * side):
                    for i in range(3):
                        length = 1.3 - i * 0.2
                        with r.at(0, 0, 0, rz=0.5 - i * 0.45):
                            r.part("cube", 0, 0, side * length / 2, 0.06, 0.06, length, dark)
                    r.part("cube", -0.15, -0.1, side * 0.55, 0.45, 0.02, 0.95, body, rz=0.35)
                    r.part("cube", -0.45, -0.3, side * 0.45, 0.35, 0.02, 0.75, body, rz=0.85)
            # The head: a blunt horned snout, jaw hanging open on a breath.
            with r.at(0.3, 0.95, 0, rz=head):
                r.part("cube", 0.15, 0, 0, 0.4, 0.3, 0.36, body)
                r.part("cube", 0.36, 0.0, 0, 0.18, 0.16, 0.3, body)
                with r.at(0.15, -0.12, 0, rz=-jaw):
                    r.part("cube", 0.18, -0.04, 0, 0.36, 0.08, 0.28, dark)
                    if jaw > 0.3 and lit:
                        r.part("cube", 0.18, 0.04, 0, 0.3, 0.06, 0.2, hot, glow=True)
                for side in (1, -1):
                    r.part("cone", -0.05, 0.22, side * 0.16, 0.07, 0.35, 0.07, dark, rx=-side * 0.6)
                    r.part("cube", 0.36, 0.06, side * 0.08, 0.02, 0.04, 0.05, hot if lit else dark, glow=lit)
                if jaw > 0.3 and lit and glow > 0.8 and e.attack_kind == "breath":
                    _flame(r, 0.6, -0.05, 0, 0.18, t)
            # Clawed arms.
            for side, a in ((1, arm_r), (-1, arm_l)):
                with r.at(0.1, 0.8, 0.42 * side, rz=a):
                    r.part("cube", 0, -0.3, 0, 0.16, 0.6, 0.16, body)
                    r.part("cube", 0.05, -0.62, 0, 0.14, 0.4, 0.14, dark, rz=0.4)
                    for c in (-0.06, 0.0, 0.06):
                        r.part("cone", 0.12, -0.85, c, 0.04, 0.2, 0.04, dark, rz=-0.6)
            # The tail: a chain of plates curling back and down; Brand's ends in an axe-blade.
            sway = math.sin(t * 2.5) * 0.3 if not perched and not dead else 0.0
            with r.at(-0.3, 0.05, 0, ry=sway):
                for i in range(5):
                    r.part(
                        "cube",
                        -0.15 - i * 0.22,
                        -0.05 * i,
                        0,
                        0.24,
                        0.12 - i * 0.012,
                        0.14,
                        dark,
                        rz=0.15 * i,
                    )
                if tail_blade:
                    r.part(
                        "cube", -1.25, -0.25, 0, 0.36, 0.42, 0.04, (150, 146, 150) if not perched else body
                    )
        if lit and glow > 0.8 and e.attack_kind in ("slam", "eruption", "kindle"):
            _flame(r, 0.6, 0.15, 0.45, 0.12, t)
            _flame(r, 0.6, 0.15, -0.45, 0.12, t)


# --- weapons (grip at the origin, pointing up +Y, like models.weapon) ---------------------------


def stormbrand(r):
    """A straight sword of blued steel, a jagged white-blue fork of lightning frozen down its fuller
    and a storm-grey stone in the pommel."""
    blade = (150, 170, 200)
    r.part("cube", 0, 0.0, 0, 0.06, 0.24, 0.06, (40, 44, 60))  # grip
    r.part("cube", 0, 0.13, 0, 0.08, 0.05, 0.4, (90, 100, 120), rz=0.0)  # cross-guard
    r.part("cube", 0, 0.13, 0.22, 0.06, 0.1, 0.05, (90, 100, 120), rx=0.5)
    r.part("cube", 0, 0.13, -0.22, 0.06, 0.1, 0.05, (90, 100, 120), rx=-0.5)
    r.part("cube", 0, 0.16 + 0.5, 0, 0.03, 1.0, 0.13, blade)
    for i in range(5):  # the frozen fork of lightning down the fuller
        y = 0.25 + i * 0.18
        r.part("cube", 0.017, y, 0.02 * (-1) ** i, 0.01, 0.2, 0.02, THUNDER, rx=0.45 * (-1) ** i, glow=True)
    r.part("cube", 0, 1.21, 0, 0.025, 0.1, 0.07, blade)
    r.part("sphere", 0, -0.15, 0, 0.07, 0.07, 0.07, (120, 130, 150))  # storm-stone pommel
    r.part("sphere", 0, -0.15, 0, 0.035, 0.035, 0.035, THUNDER, glow=True)


def slagbreaker(r):
    """A foundry maul: a black haft bound in iron bands and a blocky head whose cracks still glow."""
    r.part("cube", 0, 0.35, 0, 0.07, 1.3, 0.07, (44, 40, 40))
    for k in range(4):
        r.part("cube", 0, 0.0 + k * 0.3, 0, 0.09, 0.04, 0.09, BLACK_IRON)
    r.part("cube", 0, -0.32, 0, 0.1, 0.06, 0.1, DARK)
    with r.at(0, 1.08, 0):
        r.part("cube", 0, 0, 0, 0.3, 0.3, 0.55, CRUST)
        r.part("cube", 0, 0, 0.28, 0.32, 0.32, 0.04, BLACK_IRON)
        r.part("cube", 0, 0, -0.28, 0.32, 0.32, 0.04, BLACK_IRON)
        for i in range(3):
            r.part(
                "cube",
                0.151,
                -0.08 + i * 0.08,
                0.05 * (i - 1),
                0.01,
                0.03,
                0.3,
                MOLTEN,
                rx=0.6 * (i - 1),
                glow=True,
            )
            r.part(
                "cube",
                -0.151,
                0.06 - i * 0.07,
                -0.05 * (i - 1),
                0.01,
                0.03,
                0.28,
                MOLTEN,
                rx=-0.5 * (i - 1),
                glow=True,
            )


# --- shots ----------------------------------------------------------------------------------------


def arrow(r, rgb):
    """An iron bowman's arrow: a dark shaft, an iron head and grey fletching. Drawn along +X."""
    r.part("cube", 0, 0, 0, 0.8, 0.03, 0.03, (90, 70, 50))
    r.part("cone", 0.45, 0, 0, 0.05, 0.14, 0.05, rgb, rz=-math.pi / 2)
    r.part("cube", -0.35, 0, 0, 0.16, 0.08, 0.01, (170, 166, 160))
    r.part("cube", -0.35, 0, 0, 0.16, 0.01, 0.08, (170, 166, 160))


def thunder_spear(r, t):
    """A spear of lightning: a white-blue core with jagged forks crackling around it. Along +X."""
    r.part("cube", 0, 0, 0, 1.1, 0.07, 0.07, (240, 248, 255), glow=True)
    for i in range(4):
        a = t * 30 + i * 1.7
        r.part(
            "cube", -0.3 + i * 0.2, math.sin(a) * 0.12, math.cos(a) * 0.12, 0.28, 0.03, 0.03,
            THUNDER, rz=math.sin(a * 1.3) * 0.8, glow=True,
        )  # fmt: skip
    r.part("sphere", 0.5, 0, 0, 0.18, 0.18, 0.18, THUNDER, glow=True)


def mote(r, t):
    """An arcane mote: a violet spark wrapped in two tiny orbiting glints."""
    r.part("sphere", 0, 0, 0, 0.18, 0.18, 0.18, ARCANE, glow=True)
    for i in range(2):
        a = t * 12 + i * math.pi
        r.part("cube", math.cos(a) * 0.25, math.sin(a * 0.7) * 0.1, math.sin(a) * 0.25, 0.06, 0.06, 0.06,
               (240, 210, 255), glow=True)  # fmt: skip


def magma_bomb(r, t):
    """A lobbed glob of molten rock, crusting over as it flies."""
    r.part("sphere", 0, 0, 0, 0.4, 0.4, 0.4, MOLTEN, glow=True)
    for i in range(3):
        a = t * 5 + i * 2.1
        r.part("cube", math.cos(a) * 0.3, math.sin(a) * 0.3, 0.2, 0.18, 0.12, 0.18, CRUST, rx=a)


# --- hazards and dressing ---------------------------------------------------------------------------


def flame_jet(r, glow, reach, length, t):
    """An iron nozzle low on the wall (at local -X), firing along +X. It glows as it builds, then a
    roaring gout runs out `reach` of its `length` metres."""
    r.part("cube", -0.9, 0.5, 0, 0.2, 0.5, 0.6, DARK)  # the wall plate
    r.part("cyl", -0.7, 0.5, 0, 0.2, 0.4, 0.2, BLACK_IRON, rz=math.pi / 2)  # the nozzle
    mouth = (255, round(60 + 170 * glow), 30) if glow > 0 else (30, 26, 24)
    r.part("cyl", -0.48, 0.5, 0, 0.14, 0.04, 0.14, mouth, rz=math.pi / 2, glow=glow > 0)
    if reach <= 0:
        return
    span = length * reach
    n = max(int(span / 0.7), 1)
    for i in range(n):
        u = (i + 0.5) / n
        x = -0.45 + span * u
        size = 0.25 + 0.45 * u
        wob = math.sin(t * 25 + i * 1.9) * 0.08
        r.part("sphere", x, 0.5 + wob + 0.15 * u, 0, size, size * 0.8, size, (255, 130, 40), glow=True)
        r.part(
            "sphere", x, 0.5 + wob + 0.1 * u, 0, size * 0.55, size * 0.45, size * 0.55, WHITE_HOT, glow=True
        )


def magma_vent(r, t):
    """A crusted cone in the lava, its mouth glowing and puffing sparks."""
    r.part("cone", 0, 0.5, 0, 1.4, 1.0, 1.4, CRUST)
    r.part("cyl", 0, 1.0, 0, 0.45, 0.06, 0.45, MOLTEN, glow=True)
    for i in range(3):
        u = (t * 0.8 + i / 3) % 1.0
        r.part("cube", math.sin(i * 2.3) * 0.3 * u, 1.0 + 2.0 * u, math.cos(i * 2.3) * 0.3 * u,
               0.08, 0.08, 0.08, (255, 200, 90), glow=True)  # fmt: skip


def road_gate(r):
    """A stone arch over the road with an iron grille raised in its throat: the way out of town."""
    stone = (120, 116, 110)
    for z in (-1.0, 1.0):
        r.part("cube", 0, 1.6, z, 0.7, 3.2, 0.5, stone)
    r.part("cube", 0, 3.4, 0, 0.8, 0.5, 2.6, stone)
    r.part("cube", 0, 3.75, 0, 0.9, 0.2, 2.8, (96, 92, 88))
    for i in range(5):  # the grille, wound up into the arch
        r.part("cube", 0, 2.8, -0.6 + i * 0.3, 0.06, 0.6, 0.06, BLACK_IRON)
    r.part("cube", 0, 2.55, 0, 0.06, 0.06, 1.4, BLACK_IRON)


# --- the skyline --------------------------------------------------------------------------------
# Landmarks drawn out to the fog (world.LANDMARKS), so the fortress has a silhouette from the bridge:
# no two of them alike. Their fronts face +Z, toward the bridge.

STONE = (46, 42, 46)
STONE_LIGHT = (58, 52, 54)
SMOKE = (54, 44, 44)


def _slit(r, x, y, z, face, h=1.0):
    """A burning arrow slit on a wall face: `face` is "x" (on an east/west face) or "z"."""
    if face == "x":
        r.part("cube", x, y, z, 0.03, h, 0.28, MOLTEN, glow=True)
    else:
        r.part("cube", x, y, z, 0.28, h, 0.03, MOLTEN, glow=True)


def _merlons(r, w, d, y, step=1.6):
    """Crenellations round the edge of a flat roof `w` by `d` at height `y`."""
    for i in range(max(int(w / step), 1) + 1):
        x = -w / 2 + i * w / max(int(w / step), 1)
        for z in (-d / 2, d / 2):
            r.part("cube", x, y + 0.45, z, 0.6, 0.9, 0.5, STONE)
    for i in range(1, max(int(d / step), 1)):
        z = -d / 2 + i * d / max(int(d / step), 1)
        for x in (-w / 2, w / 2):
            r.part("cube", x, y + 0.45, z, 0.5, 0.9, 0.6, STONE)


def spire(r, seed, height, width=None, roof="cone"):
    """A watchtower of black stone with windows burning orange. `roof="cone"` is a tall iron cone;
    `"flat"` a crenellated top with a beacon burning in it."""
    w = width or 1.6 + (seed % 3) * 0.2
    r.part("cube", 0, height / 2, 0, w, height, w, (44, 40, 44))
    r.part("cube", 0, 0.6, 0, w * 1.2, 1.2, w * 1.2, STONE_LIGHT)  # a battered foot
    if roof == "flat":
        r.part("cube", 0, height + 0.15, 0, w * 1.25, 0.3, w * 1.25, STONE_LIGHT)
        _merlons(r, w * 1.2, w * 1.2, height + 0.3, step=0.9)
        r.part("cube", 0, height + 0.8, 0, 0.6, 0.8, 0.6, MOLTEN, glow=True)  # the beacon
    else:
        r.part("cone", 0, height + 1.4, 0, w * 0.8, 2.8, w * 0.8, (36, 32, 36))
    for i in range(int(height / 3)):
        y = 2 + i * 3 + (seed % 2)
        _slit(r, w / 2 + 0.01, y, 0, "x", 0.6)
        _slit(r, 0, y + 1.2, w / 2 + 0.01, "z", 0.6)


def bastion(r, seed, top, radius=2.2, base=0.0):
    """A squat drum tower: a battered skirt, a ring of slits, crenellations and a shallow iron dome.
    It rises `top` metres from `base` (above a passage's roof, it closes the gap in the wall)."""
    d = radius * 2
    r.part("cyl", 0, base + top / 2, 0, d, top, d, STONE)
    r.part("cyl", 0, base + 1.2, 0, d * 1.14, 2.4, d * 1.14, STONE_LIGHT)
    r.part("cyl", 0, base + top + 0.15, 0, d * 1.12, 0.3, d * 1.12, STONE_LIGHT)  # the parapet's lip
    for i in range(8):
        a = i * math.pi / 4 + seed * 0.3
        r.part("cube", math.cos(a) * radius * 1.02, base + top + 0.75, math.sin(a) * radius * 1.02,
               0.7, 0.9, 0.7, STONE, ry=-a)  # fmt: skip
    r.part("sphere", 0, base + top + 0.6, 0, d * 0.82, radius * 1.1, d * 0.82, BLACK_IRON)
    r.part("cone", 0, base + top + 1.6, 0, 0.3, 1.4, 0.3, BLACK_IRON)
    for i in range(3):
        a = math.pi / 2 + (i - 1) * 0.7  # toward +Z
        _slit(r, math.cos(a) * radius, base + top * 0.6, math.sin(a) * radius, "z")


def smokestack(r, t, height):
    """A smelter's stack: a tapering iron-banded flue, its mouth glowing, with smoke and embers
    rolling up out of it."""
    r.part("cyl", 0, height * 0.3, 0, 2.4, height * 0.6, 2.4, (70, 50, 44))
    r.part("cyl", 0, height * 0.8, 0, 1.7, height * 0.4, 1.7, (64, 46, 42))
    for y in (height * 0.6, height * 0.85):
        r.part(
            "cyl",
            0,
            y,
            0,
            1.9 if y > height * 0.7 else 2.6,
            0.3,
            1.9 if y > height * 0.7 else 2.6,
            BLACK_IRON,
        )
    r.part("cyl", 0, height + 0.1, 0, 2.0, 0.3, 2.0, BLACK_IRON)
    r.part("cyl", 0, height + 0.2, 0, 1.3, 0.04, 1.3, MOLTEN, glow=True)
    for i in range(4):  # puffs of smoke, swelling and thinning as they drift off
        u = (t * 0.1 + i / 4) % 1.0
        s = (0.5 + u * 1.4) * (1.0 - u * 0.6)
        x = u * 2.2 + math.sin(t * 0.7 + i * 2.3) * 0.8
        z = math.cos(i * 1.3 + t * 0.5) * 0.9
        r.part("cube", x, height + 0.8 + u * 6, z, s, s * 0.7, s, SMOKE, ry=i + u)
    for i in range(3):
        u = (t * 0.4 + i / 3) % 1.0
        r.part("cube", math.sin(i * 2.1 + t) * 0.5 + u, height + 0.5 + 4 * u, math.cos(i * 1.7) * 0.5,
               0.12, 0.12, 0.12, EMBER, glow=True)  # fmt: skip


def gatehouse(r, t, seed, base=6.2):
    """The great gate's house above the passage (from its roof at `base` up): a tall block with a
    riveted iron front, a machicolated gallery, crenellations and two unequal corner turrets."""
    top = base + 13.0
    h = top - base
    r.part("cube", 0, base + h / 2, 0, 7.0, h, 4.4, STONE)
    r.part("cube", 0, base + 1.4, 0, 7.6, 2.8, 5.0, STONE_LIGHT)  # battered plinth
    r.part("cube", 0, top - 2.0, 0, 7.8, 0.5, 5.2, STONE_LIGHT)  # the machicolation gallery
    for i in range(6):
        r.part("cube", -3.0 + i * 1.2, top - 2.6, 2.45, 0.35, 0.7, 0.4, STONE)  # its corbels
    _merlons(r, 7.0, 4.4, top)
    r.part("cube", 0, base + 5.2, 2.22, 3.4, 5.0, 0.08, BLACK_IRON, tex="iron_plate")  # iron front
    for x in (-1.4, 1.4):
        for y in (base + 3.2, base + 5.2, base + 7.2):
            r.part("cube", x, y, 2.28, 0.12, 0.12, 0.06, RIVET)
    for x in (-2.2, 2.2):
        _slit(r, x, top - 4.5, 2.21, "z", 1.4)
    for side, extra in ((-1, 2.5 + seed % 2), (1, 0.0)):  # two corner turrets, one taller
        x = side * 3.7
        th = h + 2.5 + extra
        r.part("cyl", x, base + th / 2, 1.6, 2.6, th, 2.6, STONE)
        r.part("cone", x, base + th + 1.6, 1.6, 2.9, 3.2, 2.9, BLACK_IRON)
        _slit(r, x, base + th - 2.5, 2.9, "z")


def keep(r, t, seed):
    """The Cinderhold's donjon: a battered plinth, two stepped tiers plated in iron, a crowning
    tower under a steep iron roof, buttresses on its face, a lower wing to one side, burning windows,
    and a stack smoking on its shoulder."""
    r.part("cube", 0, 2.0, 0, 10.4, 4.0, 5.8, STONE_LIGHT)
    r.part("cube", 0, 10.0, 0, 9.0, 12.0, 5.0, STONE)
    r.part("cube", 0, 16.15, 0, 9.3, 0.3, 5.3, BLACK_IRON)  # iron-plated shoulders
    r.part("cube", -0.6, 20.0, 0, 6.4, 8.0, 4.2, STONE)
    r.part("cube", -0.6, 24.15, 0, 6.7, 0.3, 4.5, BLACK_IRON)
    r.part("cube", -1.2, 26.5, 0, 3.8, 5.0, 3.2, STONE)
    r.part("cone", -1.2, 31.0, 0, 4.6, 4.0, 3.9, BLACK_IRON)  # the steep roof
    r.part("cone", -1.2, 33.6, 0, 0.25, 1.6, 0.25, BLACK_IRON)  # its finial
    for x in (-3.6, 0.0, 3.6):  # buttresses leaning on the face
        r.part("cube", x, 6.0, 2.8, 0.9, 11.0, 1.1, STONE_LIGHT, rx=-0.12)
    r.part("cube", 6.6, 4.5, 0.4, 4.0, 9.0, 4.4, STONE)  # the wing
    _merlons(r, 4.0, 4.4, 9.0)
    for i, (x, y) in enumerate(((-2.4, 9.0), (2.0, 9.0), (-1.8, 13.0), (1.6, 13.0), (-3.0, 13.0))):
        if (i + seed) % 4:
            _slit(r, x, y, 2.51, "z", 1.4)
    for y in (19.0, 22.0):
        _slit(r, -0.6, y, 2.11, "z", 1.2)
        _slit(r, 2.61, y, 0.0, "x", 1.2)
    _slit(r, -1.2, 27.0, 1.61, "z", 1.0)
    with r.at(3.2, 16.3, -1.2):
        smokestack(r, t, 5.0)


def lavafall(r, t, top, seed):
    """Molten iron pouring from a spout high on the wall behind (local -Z) down into the moat: a broad
    glowing sheet with brighter gouts sliding down it, and a seething pool where it lands."""
    r.part("cube", 0, top + 0.4, -2.5, 2.8, 1.0, 2.2, BLACK_IRON)  # the spout, run back into the wall
    r.part("cube", 0, top + 0.12, -1.6, 2.4, 0.25, 0.6, MOLTEN, glow=True)  # its lip
    fall_z = -1.0
    r.part("cube", 0, top / 2, fall_z, 2.4, top, 0.5, MOLTEN, glow=True)
    r.part("cube", 0, top * 0.45, fall_z + 0.1, 0.9, top * 0.9, 0.4, WHITE_HOT, glow=True)  # its hot core
    for i in range(3):  # gouts sliding down
        u = (t * 0.45 + i / 3 + seed * 0.17) % 1.0
        r.part("cube", 0, (top - 0.5) * (1 - u), fall_z + 0.08, 2.6, 1.6, 0.5, (255, 168, 60), glow=True)
    r.part("sphere", 0, 0.15, fall_z + 0.8, 3.2, 0.5, 2.6, MOLTEN, glow=True)  # the pool it boils up
    for i in range(3):
        u = (t * 0.9 + i / 3) % 1.0
        r.part("cube", math.sin(i * 2.3 + t * 2) * 1.0, 0.3 + u * 2.2, fall_z + 1.0 + math.cos(i * 1.9) * 0.6,
               0.15, 0.15, 0.15, EMBER, glow=True)  # fmt: skip


def anvil(r, t):
    """A smith's anvil on a stump of iron, a hammer left on it and a glowing billet."""
    r.part("cube", 0, 0.3, 0, 0.5, 0.6, 0.5, DARK)
    r.part("cube", 0, 0.72, 0, 0.9, 0.25, 0.4, BLACK_IRON)
    r.part("cone", 0.6, 0.76, 0, 0.12, 0.35, 0.12, BLACK_IRON, rz=-math.pi / 2)
    r.part("cube", -0.1, 0.88, 0.05, 0.4, 0.06, 0.1, MOLTEN, glow=True)
    r.part("cube", 0.15, 0.9, -0.12, 0.5, 0.05, 0.05, (90, 64, 40))
    r.part("cube", 0.38, 0.92, -0.12, 0.12, 0.12, 0.14, BLACK_IRON)
    _flame(r, -0.1, 0.92, 0.05, 0.03 + 0.01 * math.sin(t * 7), t)


def chimney(r, t, height=3.0):
    """A squat brick chimney on the roof with sparks rising from its cowl: cover from a breath."""
    brick = (86, 60, 52)
    r.part("cube", 0, height / 2, 0, 1.4, height, 1.4, brick)
    r.part("cube", 0, height + 0.1, 0, 1.6, 0.2, 1.6, (60, 44, 40))
    r.part("cube", 0, height + 0.2, 0, 1.0, 0.04, 1.0, MOLTEN, glow=True)
    for i in range(3):
        u = (t * 0.5 + i / 3) % 1.0
        r.part("cube", math.sin(i * 2.0 + t) * 0.3, height + 0.3 + 2.5 * u, math.cos(i * 1.7) * 0.3,
               0.06, 0.06, 0.06, (255, 190, 90), glow=True)  # fmt: skip


def embers_rain(r, t, seed):
    """Drifting embers in the hot air over the gorge and the roof (for show)."""
    for i in range(6):
        u = (t * 0.15 + i / 6 + seed * 0.13) % 1.0
        x = math.sin(i * 2.7 + seed) * 4 + math.sin(t * 0.7 + i) * 0.5
        z = math.cos(i * 1.9 + seed) * 4
        r.part("cube", x, 6 * (1 - u), z, 0.05, 0.05, 0.05, EMBER, glow=True)
