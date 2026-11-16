"""Models for the Cemetery of Ashes, where the Ashen wake: the Ashen Sexton that keeps its gate,
the husks of the Ashen who failed before you, its Shrouded Mourners, its risen dead (the
Bone Walkers dressed as `grave_walker`), and its dressing (gravestones, the open grave you
climb out of, the cemetery's wrought-iron gate). Original low-poly models assembled from primitives;
like everything in `models`, they face +X."""

import math

from ashen_vault.ai.enemy import KNELL_GAP
from ashen_vault.render.models import (
    BLADE_LANDED,
    BLADE_REST,
    CHOP_LANDED,
    CHOP_RAISED,
    ELBOW_REST,
    ELBOW_STRIKE,
    EMBER,
    _bar,
    _dim,
    _ease,
    _flame,
    _mix,
    _spider_move,
    _warden_arms,
    aim_wrist,
    blade_angle,
    chop_angle,
    death_fall,
    elbow_bend,
    hand,
    held,
    ribcage,
    skull,
    strike_angle,
    walk_cycle,
)
from ashen_vault.util import rround

ASH_BODY = (104, 100, 98)  # the Ashen's grey, a shade paler than the player's own arms
ASH_DARK = (70, 67, 66)
SHROUD = (128, 120, 104)  # a burial shroud, yellowed and grimed
SHROUD_DARK = (92, 86, 74)
COAL = (46, 34, 30)  # the cold heart of an Ashen that has not kindled
COLD = (40, 30, 26)  # an ember gone out
GRAVE_IRON = (58, 56, 60)
RUST = (112, 66, 42)
CLAY = (132, 104, 80)
HEADSTONE = (126, 124, 118)
MOSS = (70, 96, 56)
EARTH = (74, 58, 44)
PIT = (22, 18, 16)
GATE_SET_BACK = 0.7  # the cemetery gate stands this far back toward the wall behind its tile


def sexton(r, e, t):
    """The Ashen Sexton: a hulking Ashen of long ago, hunched under a burial shroud, its ash
    cracked like dry clay, three urns of others' ashes strapped to its back and a rusted grave-spade
    on a long haft in its fist. Through the ribs a cold coal sits in its chest; at half HP the bell's
    note kindles it, and the cracks, the eyes and the spade's edge burn. Slain, it sinks to its knees,
    leaning on the spade, and slumps forward; every fire goes out."""
    swing = walk_cycle(e, t) * 0.6
    kneel = death_fall(e, 0.6)
    slump = death_fall(e, 1.6)
    dead = e.state == "dead"
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit, free, blade, elbow, twist, crouch = sexton_arms(e, t)
    lit = e.phase2 and not dead
    body = (236, 232, 226) if e.flashing else ASH_BODY
    dark = _dim(body, 0.68)
    heart = EMBER if lit else (COLD if dead else COAL)
    cloth = math.sin(t * 1.8) * 0.08 + swing * 0.12
    with (
        r.at(0, lift * 0.8 + crouch - 0.36 * kneel, 0, s=1.2, ry=spin + twist),
        r.at(0, 0.95, 0, rz=-0.5 * slump),
        r.at(0, -0.95, 0),
    ):
        # Legs: thick, cracked ash wound in strips of grave-cloth; kneeling, the shins fold under.
        for side, a in ((-0.2, swing), (0.2, -swing)):
            with r.at(0, 0.95, side, rz=a + 1.4 * kneel):
                r.part("cube", 0, -0.22, 0, 0.24, 0.46, 0.22, body, tex="ash_skin")
                for i in range(2):
                    r.part("cube", 0, -0.12 - i * 0.18, 0, 0.26, 0.05, 0.24, SHROUD_DARK, rx=0.2 * (-1) ** i)
                r.part("sphere", 0.04, -0.46, 0, 0.2, 0.18, 0.2, dark)  # knee
                with r.at(0, -0.46, 0, rz=-0.1 * max(0.0, a) - 2.3 * kneel):
                    r.part("cube", 0, -0.21, 0, 0.2, 0.44, 0.19, body, tex="ash_skin")
                    r.part("cube", 0.08, -0.43, 0, 0.36, 0.08, 0.22, dark)  # a broad, bare foot
                    if lit:
                        r.part("cube", 0.105, -0.2, 0, 0.02, 0.26, 0.03, EMBER, rx=0.4, glow=True)
        # The shroud's skirt, hanging in torn strips, and a rope belt hung with little urns.
        r.part("cube", 0, 1.0, 0, 0.4, 0.22, 0.56, SHROUD)
        for i, z in enumerate((-0.22, -0.08, 0.08, 0.22)):
            drop = 0.5 + 0.08 * ((i * 3) % 4)
            with r.at(0.17, 0.98, z, rz=cloth * (1 + 0.15 * i)):
                r.part("cube", 0, -drop / 2, 0, 0.03, drop, 0.13, SHROUD if i % 2 else SHROUD_DARK)
        r.part("cyl", 0, 1.1, 0, 0.46, 0.05, 0.6, (84, 70, 52))  # the rope belt
        for i, z in enumerate((-0.26, 0.04, 0.27)):
            with r.at(0.2, 1.0, z, rx=math.sin(t * 2 + i) * 0.15):
                r.part("cube", 0, 0.06, 0, 0.02, 0.1, 0.02, (84, 70, 52))
                r.part("sphere", 0, -0.04, 0, 0.11, 0.13, 0.11, CLAY)
                r.part("cyl", 0, 0.03, 0, 0.06, 0.04, 0.06, _dim(CLAY, 0.7))  # its stopper
        # The chest: a barrel of ash with its ribs showing through the cracks, and the heart behind them.
        r.part("cube", 0, 1.38, 0, 0.44, 0.58, 0.62, body, tex="ash_skin")
        r.part("sphere", -0.12, 1.55, 0, 0.5, 0.5, 0.66, dark)  # the hunched back
        r.part("sphere", 0.2, 1.42, 0, 0.12, 0.16, 0.14, heart, glow=lit)  # the heart in its hollow
        r.part("cube", 0.215, 1.42, 0, 0.02, 0.3, 0.26, (30, 26, 24))  # the hollow round it
        for i in range(4):  # ribs bared over it
            y = 1.56 - i * 0.09
            for side in (-1, 1):
                r.part("cube", 0.225, y, side * 0.12, 0.03, 0.035, 0.18, _dim(body, 1.15), ry=side * 0.25)
        cracks = ((1.25, -0.2, 0.6), (1.5, 0.24, -0.5), (1.2, 0.15, 1.1), (1.62, -0.26, 0.3))
        for y, z, a in cracks:  # the ash split like dry clay; kindled, the fire shows through
            r.part("cube", 0.225, y, z, 0.01, 0.2, 0.025, EMBER if lit else dark, rx=a, glow=lit)
        # Three big urns of other Ashen's ashes, chained across its back.
        for i, (y, z) in enumerate(((1.55, -0.2), (1.62, 0.18), (1.25, 0.0))):
            with r.at(-0.34, y, z, rz=0.15):
                r.part("sphere", 0, 0, 0, 0.22, 0.28, 0.22, _dim(CLAY, 1 - 0.08 * i))
                r.part("cyl", 0, 0.15, 0, 0.12, 0.06, 0.12, _dim(CLAY, 0.75))  # the neck
                r.part("cube", 0, 0.19, 0, 0.13, 0.03, 0.13, (58, 50, 44))  # its lid
        for side in (-1, 1):
            r.part("cube", 0, 1.48, side * 0.2, 0.62, 0.04, 0.04, GRAVE_IRON, rz=side * 0.6)  # the chains
        # The shroud over its shoulders: five strips down its back, and a hood.
        for i, z in enumerate((-0.28, -0.14, 0.0, 0.14, 0.28)):
            drop = 0.9 + 0.12 * ((i * 2) % 3)
            with r.at(-0.28, 1.72, z, rz=-cloth * (1 + 0.2 * i) - 0.12 - 1.0 * kneel):
                r.part("cube", 0, -drop / 2, 0, 0.03, drop, 0.13, SHROUD if i % 2 == 0 else SHROUD_DARK)
        # Head, thrust low and forward: a hood over a cracked ash face, two deep eye-holes and a jaw.
        with r.at(0.16, 1.82, 0, rz=-0.2):
            r.part("sphere", 0, 0.05, 0, 0.42, 0.44, 0.4, SHROUD)  # the hood
            r.part("cube", -0.04, 0.22, 0, 0.3, 0.06, 0.34, SHROUD_DARK)  # its fold
            r.part("cube", 0.1, -0.02, 0, 0.18, 0.26, 0.24, body, tex="ash_skin")  # face
            for z in (-0.06, 0.06):
                eye = EMBER if lit else (24, 20, 20)
                r.part("cube", 0.19, 0.04, z, 0.02, 0.05, 0.05, eye, glow=lit)
            r.part("cube", 0.18, -0.1, 0, 0.04, 0.06, 0.16, dark)  # a slack jaw
        # The free arm: a long ash arm ending in a grasping hand; it rises with the other for a slam.
        with r.at(0, 1.66, -0.44, rz=free + swing * 0.3 - 0.3 * kneel):
            r.part("sphere", 0, 0, 0, 0.26, 0.24, 0.26, dark)  # shoulder
            r.part("cube", 0, -0.2, 0, 0.17, 0.4, 0.17, body, tex="ash_skin")
            with r.at(0, -0.4, 0, rz=0.3):
                r.part("cube", 0, -0.18, 0, 0.15, 0.36, 0.15, body, tex="ash_skin")
                r.part("cube", 0, -0.08, 0, 0.17, 0.06, 0.17, SHROUD_DARK)  # a wrapping
                with r.at(0, -0.38, 0):
                    urn = (
                        e.attack_kind == "ashfall" and e.state == "windup" and e.state_t > 0.3 * e.windup_time
                    )
                    hand(r, body, 0.15, curl=0.9 if urn else 0.5)
                    if urn:  # an urn of others' ashes, torn from its back, about to be dashed down
                        r.part("sphere", 0.02, -0.26, 0, 0.26, 0.32, 0.26, CLAY)
                        r.part("cyl", 0.02, -0.08, 0, 0.14, 0.06, 0.14, _dim(CLAY, 0.75))
                        r.part("cube", 0.02, -0.04, 0, 0.15, 0.03, 0.15, (58, 50, 44))
        # The spade arm: shoulder, elbow, and the grave-spade on its long haft turned at the wrist.
        # Slain, it leans on the spade, the blade on the ground ahead.
        with r.at(0, 1.66, 0.44, rz=hit - 0.5 * kneel):
            r.part("sphere", 0, 0, 0, 0.26, 0.24, 0.26, dark)
            r.part("cube", 0, -0.2, 0, 0.17, 0.4, 0.17, body, tex="ash_skin")
            bend = _mix(elbow, 0.2, kneel)
            with r.at(0, -0.4, 0, rz=bend):
                r.part("cube", 0, -0.18, 0, 0.15, 0.36, 0.15, body, tex="ash_skin")
                r.part("cube", 0, -0.3, 0, 0.17, 0.06, 0.17, SHROUD_DARK)
                point = _mix(blade, -0.25 + 0.5 * slump, kneel)
                wrist = aim_wrist(point, hit - 0.5 * kneel + bend)
                with r.at(0, -0.38, 0), held(r, wrist, body, size=0.17, splay=0.3):
                    grave_spade(r, lit, t)


OWN_POSES = ("exhale", "ashfall", "dust_devil", "spadeful", "grasp", "knell")


def sexton_arms(e, t):
    """(spade arm, free arm, spade direction, elbow, twist, crouch) for the Sexton's moves, in the
    terms of `models._warden_arms` (which gives its plain chop). Exhale: it rears up, both arms
    thrown wide, then hunches forward as the dust pours out. Ashfall: the free hand reaches back over
    its shoulder for an urn and dashes it down in front. Dust devil: the spade raised overhead and
    whirled round, then swept low. Spadeful: the spade dips low and scoops back, then flings up and
    forward. Grasp: raised, then driven blade-down into the ground. Knell: held straight up,
    trembling, then brought down like a clapper, twice."""
    hit, free, blade, elbow, twist, crouch, _ = _warden_arms(e, t)
    kind = e.attack_kind
    if e.state not in ("windup", "attack") or kind not in OWN_POSES:
        return hit, free, blade, elbow, twist, crouch
    k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1)) if e.state == "windup" else 1.0
    d = _ease(min(e.state_t / 0.15, 1))
    if kind == "exhale":
        if e.state == "windup":
            return (
                _mix(0.0, -0.6, k),
                _mix(0.0, -0.6, k),
                _mix(BLADE_REST, -0.8, k),
                ELBOW_REST,
                0.0,
                0.08 * k,
            )
        return _mix(-0.6, 0.5, d), _mix(-0.6, 0.9, d), _mix(-0.8, -0.4, d), 0.4, 0.0, _mix(0.08, -0.18, d)
    if kind == "ashfall":
        if e.state == "windup":
            return 0.2 * k, _mix(0.0, math.pi - 0.4, k), BLADE_REST, ELBOW_REST, -0.15 * k, 0.0
        return 0.2, _mix(math.pi - 0.4, 1.3, d), BLADE_REST, ELBOW_REST, _mix(-0.15, 0.1, d), -0.3 * d
    if kind == "dust_devil":
        if e.state == "windup":
            whirl = math.sin(e.state_t * 9) * 0.5 * k
            return _mix(0.0, math.pi - 0.3, k), 0.5 * k, _mix(BLADE_REST, math.pi / 2, k), 0.2, whirl, 0.0
        return _mix(math.pi - 0.3, 1.2, d), 0.5, _mix(math.pi / 2, -0.6, d), 0.2, _mix(0.4, -0.3, d), -0.2 * d
    if kind == "spadeful":
        if e.state == "windup":
            return (
                _mix(0.0, -0.5, k),
                0.3 * k,
                _mix(BLADE_REST, -1.0, k),
                _mix(ELBOW_REST, 0.2, k),
                0.3 * k,
                -0.2 * k,
            )
        return _mix(-0.5, 2.0, d), 0.3, _mix(-1.0, 1.0, d), 0.1, _mix(0.3, -0.2, d), _mix(-0.2, 0.0, d)
    if kind == "grasp":
        if e.state == "windup":
            return (
                _mix(0.0, CHOP_RAISED - 0.4, k),
                0.6 * k,
                _mix(BLADE_REST, 2.4, k),
                _mix(ELBOW_REST, 0.6, k),
                0,
                0,
            )
        return 1.5, 1.2, -math.pi / 2 + 0.35, 0.1, 0.0, -0.25
    # The knell: up on the windup, then two strokes, raised again between them.
    if e.state == "windup":
        up = k
    else:
        s = e.state_t % KNELL_GAP if e.state_t < 2 * KNELL_GAP else KNELL_GAP
        down = _ease(min(s / 0.12, 1))
        back = _ease(min(max((s - 0.25) / 0.25, 0), 1)) if e.state_t < KNELL_GAP else 0.0
        up = 1 - down * (1 - back)
    struck = e.state == "attack"
    hit = _mix(CHOP_LANDED if struck else 0.0, math.pi - 0.1, up) + math.sin(t * 40) * 0.05 * up
    blade = _mix(BLADE_LANDED if struck else BLADE_REST, math.pi / 2, up)
    elbow = _mix(ELBOW_STRIKE if struck else ELBOW_REST, 0.15, up)
    crouch = -0.25 * (1 - up) if struck else 0.0
    return hit, hit * 0.8, blade, elbow, 0.0, crouch


def grave_spade(r, lit, t):
    """A gravedigger's spade forged into a polearm, in a `held` frame (the haft along +X through the
    fist): an iron-shod butt, a long ash-wood haft bound in rags, a socket, and a broad rusted blade
    with a hook behind it. Kindled, its edge glows and it smoulders."""
    wood = (92, 72, 52)
    r.part("cube", 0.55, 0, 0, 2.1, 0.07, 0.07, wood)  # the haft
    r.part("cube", -0.5, 0, 0, 0.12, 0.09, 0.09, GRAVE_IRON)  # the shod butt
    for x in (-0.12, 0.12):
        r.part("cube", x, 0, 0, 0.08, 0.09, 0.09, (100, 90, 72))  # rag bindings round the grip
    r.part("cube", 1.6, 0, 0, 0.16, 0.1, 0.1, GRAVE_IRON)  # the socket
    r.part("cube", 1.86, 0, 0, 0.4, 0.4, 0.04, RUST)  # the spade's blade, flat to the sides
    r.part("cube", 2.07, 0, 0, 0.04, 0.42, 0.05, EMBER if lit else (150, 136, 120), glow=lit)  # its edge
    r.part("wedge", 1.62, -0.16, 0, 0.18, 0.16, 0.04, GRAVE_IRON, rz=math.pi)  # the hook behind it
    if lit:
        _flame(r, 1.9, 0.18, 0, 0.12, t)


HUSK = (98, 95, 94)
HUSK_CRUST = (150, 146, 140)  # pale ash caked on its shoulders and crown
HUSK_CHAR = (54, 50, 50)  # charred grey where the ash has burned through
HUSK_SEAM = (170, 70, 30)  # the last heat smouldering in its cracks
RAG = (82, 74, 62)


def ashen_husk(r, e, t):
    """One of the Ashen who woke before you and failed: a gaunt, hunched figure burned down to ash,
    pale crust caked on its shoulders and crown, charred grey beneath, its last heat smouldering in
    the cracks that split it and in the hollow where its heart burned out. The winding sheet it was
    buried in hangs off it in strips. Its head hangs low, the face crumbled to a skull's sockets and a
    slack jaw; its arms hang long to its knees, ending in cracked claws, and flakes of ash fall from
    it as it drags one foot. It claws with both hands. Slain, its knees give, it folds forward onto the
    ground, and its embers go out."""
    swing = walk_cycle(e, t) * 0.6
    fall = death_fall(e, 0.7)
    alive = fall < 0.5
    arm = strike_angle(e)
    body = (236, 232, 226) if e.flashing else HUSK
    crust = (246, 244, 240) if e.flashing else HUSK_CRUST
    char = _dim(body, 0.55)
    heat = 0.6 + 0.4 * math.sin(t * 2.3) if alive else 0.0
    seam = _dim(HUSK_SEAM, 0.55 + 0.45 * heat) if alive else COLD
    lurch = math.sin(t * 3.5) * 0.06 if e.state == "chase" else 0.0
    with r.at(0, -0.3 * fall, 0), r.at(0, 0.9, 0, rz=-0.42 - lurch - 1.0 * fall), r.at(0, -0.9, 0):
        # Legs, thin and knobbed at the knee; the left drags behind, its foot turned in.
        for side, a, drag in ((-0.12, swing, 0.25), (0.12, -swing * 0.5, 0.0)):
            with r.at(0, 0.88, side, rz=a + 1.3 * fall - drag * 0.4):
                r.part("cube", 0, -0.22, 0, 0.11, 0.44, 0.11, body, tex="ash_skin")
                r.part("sphere", 0.02, -0.44, 0, 0.13, 0.11, 0.13, char)  # the knee
                with r.at(0, -0.44, 0, rz=-0.25 - 1.8 * fall + drag):
                    r.part("cube", 0, -0.2, 0, 0.09, 0.42, 0.09, char, tex="ash_skin")
                    r.part("cube", 0.05, -0.18, 0, 0.012, 0.22, 0.03, seam, glow=alive)  # a smouldering split
                    r.part("cube", 0.06, -0.41, 0, 0.2, 0.05, 0.1, char, ry=drag * 1.2)  # the foot
        # Its hips, and the winding sheet hanging from them in strips that sway as it lurches.
        r.part("cube", 0, 0.93, 0, 0.2, 0.16, 0.3, char, tex="ash_skin")
        for i, z in enumerate((-0.14, -0.04, 0.06, 0.15)):
            drop = 0.3 + 0.08 * (i % 3)
            with r.at(0.09 - 0.18 * (i % 2), 0.98, z, rz=0.12 + swing * 0.3 * (i % 2 * 2 - 1)):
                r.part("cube", 0, -drop / 2, 0, 0.02, drop, 0.09, _dim(RAG, 0.8 + 0.1 * (i % 2)))
        # A gaunt chest, its ribs pressing out, and the hollow where its heart burned out.
        r.part("cube", -0.02, 1.2, 0, 0.2, 0.4, 0.3, body, tex="ash_skin")
        for i in range(3):
            for z in (-0.09, 0.09):
                r.part("cube", 0.09, 1.31 - i * 0.075, z, 0.03, 0.025, 0.1, _dim(body, 1.15), ry=z * 3)
        r.part("cube", 0.085, 1.12, 0.04, 0.03, 0.15, 0.1, PIT)  # the hollow
        r.part("sphere", 0.08, 1.11, 0.04, 0.05 + 0.02 * heat, 0.05 + 0.02 * heat, 0.05, seam, glow=alive)
        r.part("cube", 0.11, 1.25, -0.08, 0.012, 0.2, 0.025, seam, rx=0.5, glow=alive)  # a crack
        r.part("cube", 0.11, 1.02, 0.11, 0.012, 0.14, 0.02, seam, rx=-0.6, glow=alive)
        # The hunched back, crusted pale, a spine of knuckled bone down it, and the sheet's last
        # band wound round its chest over one shoulder.
        r.part("sphere", -0.08, 1.36, 0, 0.3, 0.3, 0.38, crust, tex="ash_skin")
        for i in range(4):
            r.part("cube", -0.21 + i * 0.01, 1.42 - i * 0.09, 0, 0.05, 0.05, 0.06, _dim(crust, 0.85))
        r.part("cube", 0, 1.24, 0, 0.24, 0.07, 0.34, RAG, rx=0.55)  # the band of sheet
        r.part("cube", -0.14, 1.12, -0.12, 0.02, 0.3, 0.1, _dim(RAG, 0.85), rz=0.15)  # its loose end
        # The head, hung low and forward on a thin neck: a crumbled face, deep sockets with a spark
        # left in each, a slack jaw, and the crust heaped on its crown.
        with r.at(0.08, 1.46, 0, rz=-0.55 + math.sin(t * 1.7) * 0.06 * (1 - fall)):
            r.part("cube", 0.02, 0.05, 0, 0.07, 0.12, 0.07, char)  # the neck
            with r.at(0.06, 0.18, 0):
                r.part("sphere", -0.02, 0.03, 0, 0.24, 0.24, 0.22, body, tex="ash_skin")
                r.part("sphere", -0.05, 0.1, 0, 0.22, 0.12, 0.2, crust)  # the crust on its crown
                r.part("cube", 0.09, 0.03, 0, 0.04, 0.035, 0.17, _dim(crust, 0.9))  # its brow
                for z in (-0.045, 0.045):
                    r.part("cube", 0.1, -0.01, z, 0.03, 0.05, 0.05, PIT)  # a socket
                    r.part("cube", 0.11, -0.01, z, 0.012, 0.015, 0.015, seam, glow=alive)  # its spark
                r.part("cube", 0.11, -0.05, 0, 0.02, 0.03, 0.025, PIT)  # where the nose was
                with r.at(0.02, -0.08, 0, rz=-0.35 - 0.3 * (e.state == "windup")):
                    r.part("cube", 0.05, -0.02, 0, 0.11, 0.04, 0.13, char)  # the slack jaw
                    r.part("cube", 0.1, 0.0, 0, 0.02, 0.02, 0.1, _dim(BONE_PALE, 0.8))  # a few teeth
        # Both arms hang long and reach and claw together, a shoulder knob crusted pale.
        for side in (-1, 1):
            reach = arm + swing * 0.3 * side + 0.75
            with r.at(0, 1.38, side * 0.2, rz=reach * (1 - fall) + 0.2 * fall):
                r.part("sphere", 0, 0.0, 0, 0.14, 0.13, 0.14, crust)
                r.part("cube", 0, -0.2, 0, 0.08, 0.4, 0.08, body, tex="ash_skin")
                with r.at(0, -0.4, 0, rz=0.35):
                    r.part("cube", 0, -0.19, 0, 0.07, 0.38, 0.07, char, tex="ash_skin")
                    r.part("cube", 0.04, -0.2, 0, 0.01, 0.16, 0.02, seam, glow=alive)
                    with r.at(0, -0.39, 0):
                        hand(r, char, 0.12, bony=True, curl=0.8 if e.state == "attack" else 0.55)
    if alive:  # flakes of ash drift down off it
        for i in range(3):
            k = (t * 0.45 + i / 3) % 1
            x = -0.05 + 0.1 * math.sin(i * 2.1 + t * 0.7)
            z = 0.12 * math.sin(i * 3.7 + t)
            r.part("cube", x, 1.45 - 1.3 * k, z, 0.025, 0.025, 0.025, crust, rx=t * 3 + i, ry=t * 2)


def gravestone(r, seed):
    """A weathered headstone, one of a few shapes picked by `seed`: a round-topped slab, a cross or a
    small obelisk, leaning a little, chipped and furred with moss, a mound of earth before it."""
    shape = seed % 3
    lean = ((seed * 7) % 5 - 2) * 0.05
    stone = _dim(HEADSTONE, 0.9 + 0.05 * (seed % 3))
    r.part("cube", 0.45, 0.06, 0, 0.9, 0.14, 0.7, EARTH)  # the grave's mound
    r.part("cube", 0.45, 0.14, 0, 0.7, 0.06, 0.5, _dim(EARTH, 0.85))
    with r.at(0, 0, 0, rz=lean, ry=((seed * 3) % 5 - 2) * 0.08):
        r.part("cube", 0, 0.06, 0, 0.3, 0.12, 0.8, _dim(stone, 0.8), tex="rough_stone")  # its footing
        if shape == 0:  # a slab with a rounded top
            r.part("cube", 0, 0.55, 0, 0.16, 0.9, 0.62, stone, tex="rough_stone")
            r.part("cyl", 0, 1.0, 0, 0.62, 0.16, 0.62, stone, tex="rough_stone", rz=math.pi / 2)
            r.part("cube", 0.085, 0.7, 0, 0.01, 0.04, 0.34, _dim(stone, 0.6))  # a worn line of letters
            r.part("cube", 0.085, 0.6, 0, 0.01, 0.04, 0.26, _dim(stone, 0.6))
        elif shape == 1:  # a cross
            r.part("cube", 0, 0.65, 0, 0.16, 1.2, 0.18, stone, tex="rough_stone")
            r.part("cube", 0, 0.92, 0, 0.16, 0.16, 0.64, stone, tex="rough_stone")
            r.part("cube", 0.02, 0.92, 0.0, 0.14, 0.2, 0.2, _dim(stone, 1.1), rx=math.pi / 4)  # its boss
        else:  # a small obelisk
            r.part("cube", 0, 0.3, 0, 0.34, 0.36, 0.34, stone, tex="rough_stone")
            r.part("cube", 0, 0.85, 0, 0.24, 0.8, 0.24, stone, tex="rough_stone")
            r.part("cone", 0, 1.35, 0, 0.24, 0.24, 0.24, stone, tex="rough_stone")
        r.part("cube", 0.02, 0.18, 0.2, 0.18, 0.14, 0.2, MOSS)  # moss creeping up from the ground
        r.part("cube", -0.04, 0.4, -0.18, 0.16, 0.2, 0.14, _dim(MOSS, 0.8))


def open_grave(r, seed):
    """The grave you wake in: a dark pit dug in the earth, the spoil heaped beside it, a cracked
    headstone toppled at its head and a scatter of grey ash over the lip."""
    r.part("cube", 0, 0.01, 0, 1.0, 0.02, 1.7, PIT)  # the pit, black against the ground
    for side in (-1, 1):
        r.part("cube", side * 0.56, 0.04, 0, 0.12, 0.08, 1.8, EARTH)  # its lips
    r.part("cube", 0, 0.04, -0.92, 1.1, 0.08, 0.12, EARTH)
    r.part("cube", 0, 0.04, 0.92, 1.1, 0.08, 0.12, EARTH)
    for i in range(3):  # the spoil heaped along one side
        r.part("sphere", 0.85, 0.08, -0.5 + i * 0.5, 0.5, 0.26 - 0.04 * i, 0.55, _dim(EARTH, 1 - 0.08 * i))
    with r.at(-0.9, 0.12, 0.1, rz=1.3):  # the headstone, fallen
        r.part("cube", 0, 0, 0, 0.14, 0.7, 0.55, HEADSTONE, tex="rough_stone")
        r.part("cube", 0.075, 0.1, 0, 0.01, 0.04, 0.3, _dim(HEADSTONE, 0.6))
    for i in range(4):  # ash spilled over the lip
        a = seed + i * 1.7
        r.part("cube", math.cos(a) * 0.4, 0.05, 0.9 * math.sin(a), 0.22, 0.02, 0.18, ASH_BODY, ry=a)


def cemetery_gate(r, open_t=0.0):
    """The Cemetery of Ashes' gate: two stone piers capped with urns and a pair of wrought-iron leaves
    between them, barred and spiked along the top, a ring of iron for a lock. It spans its tile across
    Z, set back against the wall behind it (-X); `open_t` swings the leaves apart, away from +X."""
    with r.at(-GATE_SET_BACK, 0, 0):
        stone = (118, 114, 108)
        for z in (-0.95, 0.95):
            r.part("cube", 0, 1.3, z, 0.5, 2.6, 0.4, stone, tex="rough_stone")
            r.part("cube", 0, 2.66, z, 0.6, 0.12, 0.5, _dim(stone, 1.1), tex="rough_stone")  # the cap
            r.part("sphere", 0, 2.9, z, 0.3, 0.36, 0.3, CLAY)  # an urn on each
            r.part("cyl", 0, 3.1, z, 0.16, 0.08, 0.16, _dim(CLAY, 0.75))
        swing = min(max(open_t, 0.0), 1.0) * 1.4
        for side in (-1, 1):
            with r.at(0, 0, side * 0.75, ry=side * swing), r.at(0, 0, -side * 0.375):
                for k in range(5):  # upright bars, each spiked
                    z = -0.3 + k * 0.15
                    r.part("cube", 0, 1.1, z, 0.04, 2.0, 0.04, GRAVE_IRON)
                    r.part("cone", 0, 2.16, z, 0.06, 0.14, 0.06, GRAVE_IRON)
                for y in (0.25, 1.1, 1.95):  # rails across them
                    r.part("cube", 0, y, 0, 0.05, 0.06, 0.74, GRAVE_IRON)
                r.part(
                    "cube", 0, 1.55, 0, 0.03, 0.5, 0.5, GRAVE_IRON, rx=math.pi / 4
                )  # a diamond of scrollwork
                r.part("cube", 0.03, 1.55, 0, 0.03, 0.3, 0.3, _dim(GRAVE_IRON, 1.3), rx=math.pi / 4)
        if open_t <= 0.0:  # the lock's ring, where the leaves meet
            r.part("cyl", 0.06, 1.1, 0, 0.14, 0.03, 0.14, (120, 100, 70), rz=math.pi / 2)
        r.part("cube", 0, 0.03, 0, 0.6, 0.06, 2.3, _dim(stone, 0.8), tex="rough_stone")  # the threshold


def ash_hands(r, glow, rise, t):
    """The Sexton's grasping ash, where it will burst (`hazards.Eruption` style "hands"): first the
    ground stirs, a ring of grey ash heaving and cracking (`glow` 0..1), then three long ash arms claw
    up out of it (`rise` 0..1) and sink again."""
    if glow > 0:
        r.part("cyl", 0, 0.015, 0, 1.5 * glow, 0.02, 1.5 * glow, (40, 36, 34))  # the ground opening
        for i in range(6):
            a = i * math.pi / 3 + t * 0.3
            heave = 0.06 + 0.08 * glow * (0.5 + 0.5 * math.sin(t * 9 + i))
            r.part(
                "cube", math.cos(a) * 0.75, heave / 2, math.sin(a) * 0.75, 0.36, heave, 0.2, ASH_BODY, ry=-a
            )
    if rise <= 0:
        return
    for i in range(3):
        a = i * 2.1 + 0.5
        x, z = math.cos(a) * 0.35, math.sin(a) * 0.35
        length = (0.9 + 0.25 * i) * rise
        with r.at(x, 0, z, rx=math.sin(a) * 0.35, rz=-math.cos(a) * 0.35):
            r.part("cube", 0, length / 2, 0, 0.13, length, 0.13, ASH_BODY, tex="ash_skin")
            r.part("cube", 0, 0.08, 0, 0.2, 0.16, 0.2, ASH_DARK)  # ash heaped round the wrist
            with r.at(0, length, 0, rz=math.pi):
                hand(r, ASH_BODY, 0.2, bony=True, curl=1.2 - 0.8 * rise + 0.15 * math.sin(t * 12 + i))


def dust_puff(r, size, heat, t, seed=0.0):
    """One roiling ball of the Sexton's breath of grave dust (a `Gout` of style "ash"): dark and dense
    where it leaves its hood (`heat` 1), paler and thinning at the front, a few motes tumbling in it."""
    if size <= 0.02:
        return
    roil = 1 + 0.15 * math.sin(t * 17 + seed * 3)
    grey = _mix_rgb((110, 106, 102), (176, 170, 162), 1 - heat)
    s = size * roil * 0.55
    for i in range(4):  # a cluster of smaller billows, not one ball
        a = seed * 2.3 + i * math.tau / 4 + t * 1.5
        k = 0.55 + 0.15 * (i % 2)
        x, y, z = math.cos(a) * s * 0.35, (i - 1.5) * s * 0.12, math.sin(a) * s * 0.35
        r.part("sphere", x, y, z, s * k, s * k * 0.8, s * k, _dim(grey, 0.9 + 0.08 * i))
    for i in range(2):
        a = t * 6 + seed + i * 3.1
        r.part(
            "cube",
            math.cos(a) * s * 0.6,
            math.sin(a * 1.3) * s * 0.4,
            math.sin(a) * s * 0.6,
            0.05,
            0.05,
            0.05,
            ASH_DARK,
            rx=a,
            ry=a,
        )


def ash_billow(r, k, radius, t):
    """The ash of an urn the Sexton dashes down (a `Shockwave` of style "ash"), `k` 0..1 through its
    life: a ring of grey clouds rolls out to `radius`, swelling and rising, then thins and settles,
    shards of the urn skittering out before it."""
    out = radius * min(k / 0.45, 1.0)
    fade = 1.0 - max(0.0, (k - 0.55) / 0.45)
    for i in range(12):
        a = i * math.tau / 12 + 0.3 * math.sin(i * 1.7)
        size = (0.5 + 0.7 * min(k / 0.45, 1.0)) * fade * (0.85 + 0.15 * math.sin(i * 2.3))
        if size <= 0.03:
            continue
        rise = 0.35 + 0.6 * k
        grey = (184, 178, 170) if i % 2 else (150, 144, 138)
        r.part("sphere", math.cos(a) * out, rise, math.sin(a) * out, size, size * 0.7, size, grey)
        if i % 3 == 0:  # a shard of the urn, ahead of the cloud
            d = min(radius * 1.05, out + 0.4)
            r.part("cube", math.cos(a) * d, 0.04, math.sin(a) * d, 0.12, 0.05, 0.09, CLAY, ry=a + t)
    if k < 0.5:  # where the urn broke, a heap of ash still smoking
        r.part("sphere", 0, 0.1, 0, 0.7 * (1 - k), 0.25, 0.7 * (1 - k), ASH_DARK)


def dust_devil(r, strength, t):
    """A whirlwind of grave ash (`hazards.DustDevil`): a funnel of grey bands spinning, narrow at its
    foot and wide at its crown, ash and grit flung round it; `strength` 0..1 as it rises and dies."""
    if strength <= 0.02:
        return
    h = 2.4 * strength
    for i in range(6):
        k = i / 5
        y = h * (0.08 + 0.85 * k)
        w = (0.25 + 0.75 * k) * strength
        spin = t * (7 - 2 * k) + i * 0.9
        grey = (184, 178, 170) if i % 2 else (148, 142, 136)
        for j in range(3):
            a = spin + j * math.tau / 3
            r.part("cube", math.cos(a) * w * 0.5, y, math.sin(a) * w * 0.5, w * 0.9, 0.2, 0.16, grey, ry=-a)
    r.part(
        "cyl", 0, h * 0.45, 0, 0.35 * strength, h * 0.9, 0.35 * strength, (120, 116, 110)
    )  # its dense core
    for i in range(4):  # grit flung round it, and embers still alight in it
        a = t * 9 + i * 1.6
        y = h * ((t * 0.7 + i * 0.25) % 1)
        ember = i % 2 == 0
        r.part(
            "cube",
            math.cos(a) * 0.8 * strength,
            y,
            math.sin(a) * 0.8 * strength,
            0.06,
            0.06,
            0.06,
            EMBER if ember else ASH_DARK,
            rx=a,
            ry=a,
            glow=ember,
        )
    r.part("cyl", 0, 0.02, 0, 1.3 * strength, 0.03, 1.3 * strength, (62, 58, 56))  # the ash it scours up


def _mix_rgb(a, b, k):
    return tuple(rround(x + (y - x) * k) for x, y in zip(a, b, strict=True))


def ash_clod(r, t):
    """A clod of grave ash from the Sexton's spadeful, shedding dust as it flies."""
    clod = _dim(ASH_BODY, 0.75)
    r.part("sphere", 0, 0, 0, 0.18, 0.15, 0.17, clod)
    r.part("sphere", 0.06, 0.04, 0.03, 0.11, 0.1, 0.11, ASH_BODY)
    r.part("sphere", -0.04, -0.03, -0.05, 0.1, 0.08, 0.1, ASH_DARK)
    for i in range(3):
        a = t * 5 + i * 2.1
        r.part("cube", -0.2 - 0.06 * i, math.sin(a) * 0.08, math.cos(a) * 0.08, 0.05, 0.05, 0.05, ASH_DARK)


ROBE = (44, 48, 60)  # the mourner's robes, a dark slate blue
ROBE_DARK = (30, 32, 42)
BONE_PALE = (196, 190, 176)
HOLLOW = (10, 9, 12)
KNIFE = (120, 118, 112)


def _mourner_arm(e, lurking):
    """(shoulder, elbow, knife direction) for the mourner's knife arm: folded down before it while it
    lurks, drawn back low on the windup, thrust straight out on the attack."""
    if lurking:
        return 0.55, 0.9, -1.2
    if e.attack_kind == "fireball" and e.state in ("windup", "attack", "recover"):
        return 0.3, 0.6, -0.6  # the free hand throws; the knife waits
    if e.state == "windup":
        k = _ease(min(e.state_t / max(e.type.windup, 1e-3), 1))
        return _mix(0.3, -0.5, k), _mix(0.6, 1.3, k), _mix(-0.6, 0.0, k)
    if e.state == "attack":
        d = _ease(min(e.state_t / 0.12, 1))
        return _mix(-0.5, 1.45, d), _mix(1.3, 0.05, d), 0.0
    if e.state == "recover":
        k = _ease(min(e.state_t / max(e.type.recover, 1e-3), 1))
        return _mix(1.45, 0.3, k), _mix(0.05, 0.6, k), _mix(0.0, -0.6, k)
    return 0.3, 0.6, -0.6


def _mourner_cast(e):
    """((shoulder, elbow), fire) for the mourner's free arm while it throws a fireball: the arm draws
    back as the fire swells (fire 0..1), then flings forward and lets it go. (None, 0) otherwise."""
    if e.attack_kind != "fireball" or e.state not in ("windup", "attack"):
        return None, 0.0
    if e.state == "windup":
        k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1))
        return (_mix(0.2, -0.7, k), _mix(0.4, 1.6, k)), 0.3 + 0.7 * k
    d = _ease(min(e.state_t / 0.12, 1))
    return (_mix(-0.7, 1.5, d), _mix(1.6, 0.1, d)), 0.0


def mourner(r, e, t):
    """The Shrouded Mourner, found only in the cemetery: a tall, narrow figure in long robes of dark
    slate, a hood drawn into a peak over a hollow where a face should be (one pale gap in it, as of
    bone), a cowl spilling over its shoulders, and a robe whose hem hangs in uneven strips over bare,
    bony feet. Lurking, it stands bowed over a grave, hands folded; awake, it glides, hem swaying, and
    stabs with a crooked knife, or draws back its free hand as grave-fire swells in the palm and
    throws it. Slain, it folds forward and its robes settle in a heap."""
    fall = death_fall(e, 0.8)
    lurking = e.state == "idle"
    cloth = (236, 232, 226) if e.flashing else ROBE
    dark = (210, 206, 200) if e.flashing else ROBE_DARK
    bone = (250, 248, 244) if e.flashing else BONE_PALE
    bob = math.sin(t * 2.6) * 0.03 if e.state == "chase" else 0.0
    bow = 0.45 if lurking else 0.15
    sway = math.sin(t * 3.2) * (0.12 if e.state == "chase" else 0.04)
    with r.at(0, bob + 0.45 * fall, 0, rz=-1.4 * fall):
        for side in (-0.11, 0.11):  # bare, bony feet under the hem
            r.part("cube", 0.12, 0.03, side, 0.24, 0.05, 0.08, bone)
            r.part("cube", 0.25, 0.025, side, 0.05, 0.035, 0.09, _dim(bone, 0.85))  # the toes
        r.part("cone", 0, 0.78, 0, 0.62, 1.4, 0.62, cloth)  # the robe, falling wide from the chest
        for i in range(8):  # its hem, torn into strips of uneven length
            a = i * math.pi / 4 + 0.2
            drop = 0.22 + 0.1 * ((i * 5) % 3)
            turn = sway * (1 + 0.2 * i) * (i % 2 * 2 - 1)
            with r.at(math.cos(a) * 0.3, 0.06 + drop, math.sin(a) * 0.3, ry=-a, rz=turn):
                r.part("cube", 0, -drop / 2, 0, 0.03, drop, 0.16, dark if i % 2 else cloth)
        with r.at(0, 0.95, 0, rz=-bow):  # bowed at the waist over its grave
            r.part("cube", 0, 0.32, 0, 0.32, 0.5, 0.42, dark)  # the chest
            r.part("sphere", 0, 0.58, 0, 0.42, 0.24, 0.56, cloth)  # the shoulders
            for i, z in enumerate((-0.24, -0.08, 0.08, 0.24)):  # the cowl, spilling down its back
                drop = 0.5 + 0.12 * (i % 2)
                with r.at(-0.14, 0.62, z, rz=-0.15 - sway * 0.5):
                    r.part("cube", 0, -drop / 2, 0, 0.04, drop, 0.17, dark if i % 2 else cloth)
            with r.at(0.06, 0.74, 0, rz=-0.25 if lurking else -0.05):  # the hood, its peak bent back
                r.part("sphere", 0, 0.16, 0, 0.36, 0.5, 0.34, cloth)
                r.part("cone", -0.07, 0.48, 0, 0.18, 0.3, 0.18, cloth, rz=0.45)
                r.part("cube", 0.15, 0.12, 0, 0.05, 0.3, 0.2, HOLLOW)  # the hollow
                r.part(
                    "cube", 0.175, 0.13, 0.02, 0.01, 0.11, 0.045, _dim(bone, 0.8)
                )  # a pale gap, as of bone
                for z in (-0.12, 0.12):
                    r.part("cube", 0.15, 0.12, z, 0.07, 0.36, 0.05, dark)  # the hood's rim
            hit, elbow, point = _mourner_arm(e, lurking)
            # The free arm: folded across the body (lurking), held out a little (awake), or drawn
            # back while grave-fire swells in its palm, then flung forward (its fireball).
            cast, fire = _mourner_cast(e)
            shoulder, bend = (0.6, 1.0) if lurking else cast or (0.2 + sway, 0.4)
            with r.at(0.02, 0.5, -0.24, rz=shoulder):
                r.part("cube", 0, -0.16, 0, 0.14, 0.32, 0.14, cloth)  # the sleeve
                with r.at(0, -0.32, 0, rz=bend):
                    r.part("cube", 0, -0.06, 0, 0.18, 0.14, 0.18, dark)  # its wide cuff
                    r.part("cube", 0, -0.18, 0, 0.05, 0.24, 0.05, bone)  # the forearm, all bone
                    with r.at(0, -0.3, 0):
                        hand(r, bone, 0.11, bony=True, curl=0.25 if fire else 0.5)
                        if fire:  # the fire it kindles, cupped in its palm
                            size = 0.05 + 0.1 * fire
                            r.part(
                                "sphere",
                                0.02,
                                -0.14,
                                0,
                                size * 1.6,
                                size * 1.6,
                                size * 1.6,
                                (255, 150, 60),
                                glow=True,
                            )
                            r.part(
                                "sphere",
                                0.02,
                                -0.14,
                                0,
                                size * 0.8,
                                size * 0.8,
                                size * 0.8,
                                (255, 236, 180),
                                glow=True,
                            )
                            _flame(r, 0.02, -0.06, 0, size * 0.9, t)
            # The knife arm.
            with r.at(0.02, 0.5, 0.24, rz=hit):
                r.part("cube", 0, -0.16, 0, 0.14, 0.32, 0.14, cloth)
                with r.at(0, -0.32, 0, rz=elbow):
                    r.part("cube", 0, -0.06, 0, 0.18, 0.14, 0.18, dark)
                    r.part("cube", 0, -0.18, 0, 0.05, 0.24, 0.05, bone)
                    wrist = aim_wrist(point, hit + elbow)
                    with r.at(0, -0.32, 0), held(r, wrist, bone, size=0.08, splay=0.2):
                        r.part("cube", -0.02, 0, 0, 0.14, 0.04, 0.04, (54, 40, 30))  # the grip
                        r.part("cube", 0.07, 0, 0, 0.02, 0.1, 0.05, (70, 66, 60))  # a crossbar
                        r.part("cube", 0.2, 0.01, 0, 0.24, 0.05, 0.015, KNIFE)  # the blade
                        r.part("cube", 0.36, 0.04, 0, 0.12, 0.04, 0.015, KNIFE, rz=0.5)  # its crooked tip


GRAVE_BONE = (190, 182, 162)  # bone grimed grey with grave ash
WINDING = (112, 98, 78)  # a burial winding sheet, gone brown with the grave
HEADSTONE_SHARD = (112, 110, 104)


def grave_walker(r, e, t):
    """The cemetery's own Bone Walkers (`bone_walker model=grave`): the long-buried dead, risen in what
    they were buried in. Bones grimed grey with grave ash; the strip of winding sheet that bound the
    jaw shut still knotted over the crown; the rest of the sheet hanging off the shoulders in shreds
    and wound round the hips; a shard of its own headstone lashed to the free forearm as a
    shield; and for a weapon a length of the cemetery's iron railing, pulled up spike and all. Embers
    smoulder in the sockets. Slain, its knees give and it topples onto its back, and the embers go out."""
    swing = walk_cycle(e, t)
    fall = death_fall(e, 0.7)
    lean = (-0.3 if e.state == "hurt" else 0) + 1.35 * fall
    alive = fall < 0.5
    bone = (255, 240, 220) if e.flashing else GRAVE_BONE
    shade = _dim(bone, 0.72)
    sheet = (240, 236, 228) if e.flashing else WINDING
    flap = math.sin(t * 2.7) * 0.1 + swing * 0.15
    with r.at(-0.2 * fall, 0.12 * fall, 0, rz=lean):
        for side, a in ((-0.13, swing), (0.13, -swing)):
            knee = 0.1 + 0.45 * max(0.0, a) + 0.4 * fall
            with r.at(0, 0.9, side, rz=a + 0.35 * fall):
                r.part("cube", 0, -0.22, 0, 0.065, 0.42, 0.065, bone)  # thigh bone
                r.part("sphere", 0.01, -0.44, 0, 0.09, 0.08, 0.09, shade)  # knee
                with r.at(0, -0.44, 0, rz=-knee):
                    r.part("cube", 0, -0.21, 0.015, 0.05, 0.42, 0.04, bone)  # shin and calf bone
                    r.part("cube", 0, -0.21, -0.02, 0.032, 0.4, 0.03, shade)
                    r.part("cube", 0, -0.08, 0, 0.08, 0.06, 0.08, _dim(sheet, 0.8))  # a rag bound round it
                    with r.at(0, -0.44, 0, rz=knee * 0.8):
                        r.part("cube", 0.06, -0.01, 0, 0.18, 0.04, 0.09, bone)  # foot
                        r.part("cube", 0.15, -0.01, 0, 0.04, 0.03, 0.1, shade)  # toes
        # Pelvis, wound round with the winding sheet, its ends hanging.
        r.part("cube", 0, 0.94, 0, 0.14, 0.1, 0.24, bone)
        r.part("cube", 0, 0.97, 0, 0.17, 0.07, 0.29, sheet, rx=0.15)
        for x, z, k in ((0.1, 0.06, 1), (-0.1, -0.08, -1), (0.1, -0.1, -1)):
            with r.at(x, 0.92, z, rz=flap * k):
                r.part("cube", 0, -0.17, 0, 0.02, 0.34, 0.08, _dim(sheet, 0.85))
        for i in range(5):  # the spine
            r.part("cube", -0.05, 1.03 + i * 0.075, 0, 0.06, 0.05, 0.06, shade if i % 2 else bone)
        ribcage(r, bone, ribs=4, width=0.36, top=1.35, depth=0.18)
        r.part("cube", 0.02, 1.2, 0, 0.16, 0.05, 0.38, _dim(sheet, 0.9), rx=-0.45)  # a band across the ribs
        _bar(r, (0.03, 1.42, -0.27), (0.03, 1.42, 0.27), 0.05, bone)  # collarbones
        # The rest of the sheet, hanging in shreds off its shoulders down its back.
        r.part("cube", -0.12, 1.44, 0, 0.14, 0.06, 0.46, _dim(sheet, 0.8))
        for i, z in enumerate((-0.2, -0.07, 0.07, 0.2)):
            drop = 0.42 + 0.12 * ((i * 2) % 3)
            with r.at(-0.17, 1.45, z, rz=-0.12 - flap * 0.6):
                r.part("cube", 0, -drop / 2, 0, 0.025, drop, 0.07, _dim(sheet, 0.75 if i % 2 else 0.6))
        with r.at(0.02, 1.62, 0, rz=math.sin(t * 2) * 0.1 * (1 - fall) - 0.5 * fall):
            r.part("cube", -0.03, -0.08, 0, 0.05, 0.08, 0.05, shade)  # neck
            skull(r, bone, EMBER if alive else COLD, glow=alive, jaw=0.04 + 0.08 * (e.state == "windup"))
            # The strip that bound its jaw, knotted on the crown, and the hood fallen back behind it.
            for z in (-0.118, 0.118):  # up the cheeks
                r.part("cube", 0.05, -0.03, z, 0.05, 0.24, 0.02, sheet, rz=0.3)
            r.part("cube", 0.09, -0.15, 0, 0.06, 0.03, 0.24, sheet)  # under the chin
            r.part("cube", -0.01, 0.15, 0.0, 0.07, 0.05, 0.07, _dim(sheet, 0.85))  # the knot
            r.part("cube", -0.05, 0.17, 0.02, 0.03, 0.1, 0.03, _dim(sheet, 0.85), rz=-0.7)  # its loose end
        # The free arm, a shard of its own headstone lashed to the forearm, carved face out.
        with r.at(0, 1.4, -0.27, rz=swing * 0.5 - 0.3 * fall + 0.4 * (e.state == "windup")):
            r.part("cube", 0, -0.15, 0, 0.05, 0.3, 0.05, bone)
            with r.at(0, -0.3, 0, rz=0.9 + 0.2 * swing):
                r.part("cube", 0, -0.14, 0, 0.042, 0.28, 0.042, bone)
                with r.at(0.02, -0.15, -0.07):
                    r.part("cube", 0, 0, 0, 0.36, 0.42, 0.06, HEADSTONE_SHARD)
                    r.part("wedge", 0.03, 0.25, 0, 0.3, 0.08, 0.06, HEADSTONE_SHARD)  # its broken top
                    r.part(
                        "cube", 0.0, 0.05, -0.035, 0.03, 0.22, 0.01, _dim(HEADSTONE_SHARD, 0.6)
                    )  # the carved cross
                    r.part("cube", 0.0, 0.1, -0.035, 0.14, 0.03, 0.01, _dim(HEADSTONE_SHARD, 0.6))
                    for y in (-0.1, 0.1):
                        r.part("cube", 0, y, 0.03, 0.38, 0.04, 0.03, _dim(sheet, 0.75))  # its lashings
                with r.at(0, -0.29, 0):
                    hand(r, bone, 0.09, bony=True, curl=0.6)
        # The weapon arm swings a length of iron railing, its spike leading.
        shoulder, elbow = chop_angle(e) - 0.5 * fall, elbow_bend(e) * (1 - fall)
        wrist = aim_wrist(_mix(blade_angle(e), -lean, fall), shoulder + elbow)
        with r.at(0, 1.4, 0.27, rz=shoulder):
            r.part("cube", 0, -0.15, 0, 0.05, 0.3, 0.05, bone)
            with r.at(0, -0.3, 0, rz=elbow):
                r.part("cube", 0, -0.15, 0, 0.042, 0.3, 0.042, bone)
                with r.at(0, -0.32, 0), held(r, wrist, bone, size=0.08, splay=0.45):
                    railing(r)


def railing(r):
    """A length of the cemetery's wrought-iron railing, torn up and swung like a mace, in a `held`
    frame: the bar along +X, a spear-head finial at its end, a collar and a stub of the cross-rail."""
    r.part("cube", 0.32, 0, 0, 0.95, 0.045, 0.045, GRAVE_IRON)  # the bar
    r.part("cube", -0.15, 0, 0, 0.06, 0.07, 0.07, RUST)  # its broken foot
    r.part("cube", 0.55, 0, 0, 0.06, 0.08, 0.08, RUST)  # a collar
    r.part("cube", 0.55, 0.0, 0, 0.04, 0.04, 0.22, GRAVE_IRON)  # the cross-rail's stub
    r.part("cube", 0.8, 0, 0, 0.08, 0.09, 0.09, GRAVE_IRON)  # the finial's knob
    r.part("wedge", 0.97, 0, 0, 0.13, 0.26, 0.03, GRAVE_IRON, rz=-math.pi / 2)  # its spear head
