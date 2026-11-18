"""Models for Vesperholm, the Moonbound City, where the moon never sets: its moonlit dead (the Pale
Sentinel, an empty suit of silvered plate full of moonlight; the Lantern Wraith, a legless shade with a
lantern of trapped moonlight; the Moonhound; the Veiled Knight, who steps through the moonlight) and
Duchess Ilvane, the Moonwed, in her cathedral; their frost lances, the shafts of moonlight she calls
down and the mist of a blink; the Vesper Gate between the city and Harrowmere; and the city's dressing
(moon lamps, veiled statues, silver trees, windows of moon-glass and slender spires).
Original low-poly models assembled from primitives; like everything in `models`, they face +X. Their
ghostliness is the PS1's: pale glowing parts and stippled `mist` that the shader cuts to a dither."""

import math

from ashen_vault.render.models import (
    BLADE_LANDED,
    BLADE_RAISED,
    BLADE_REST,
    CHOP_LANDED,
    CHOP_RAISED,
    ELBOW_COCKED,
    ELBOW_REST,
    ELBOW_STRIKE,
    PASSAGE_DARK,
    _bar,
    _dim,
    _ease,
    _mix,
    aim_wrist,
    blade_angle,
    chop_angle,
    death_fall,
    elbow_bend,
    hand,
    held,
    hit_tint,
    sword_parts,
    walk_cycle,
)

MOON_GLOW = (214, 230, 255)  # moonlight: what fills the dead of Vesperholm, and what they throw
GLOW_COLD = (58, 64, 80)  # moonlight gone out
SPECTRE = (178, 196, 228)  # the pale blue-white of a moonlit shade
SPECTRE_DARK = (112, 128, 166)
VOID = (14, 16, 26)  # the dark inside a hood or a helm
SILVER = (184, 190, 206)
SILVER_DARK = (116, 122, 140)
FROST = (230, 238, 252)
MOON_SILK = (222, 226, 240)
SILK_SHADE = (168, 176, 204)
SHROUD = (92, 104, 140)  # a wraith's robe, dusk-blue
HOUND = (206, 212, 224)
HOUND_DARK = (146, 154, 172)
MOONSTONE = (150, 158, 176)
MOONSTONE_DARK = (108, 116, 136)
DUCHESS_SKIN = (226, 228, 238)  # porcelain, untouched by any sun
DUCHESS_HAIR = (232, 236, 246)  # gone white as frost


def _glow(lit):
    return MOON_GLOW if lit else GLOW_COLD


# --- the Pale Sentinel ----------------------------------------------------------------------------


def _sweep_spin(e):
    """How far a sweeper has turned through its sweep: wound back on the windup, round on the attack."""
    if e.attack_kind != "sweep":
        return 0.0
    if e.state == "windup":
        return -0.7 * _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
    if e.state == "attack":
        return -0.7 + (2 * math.pi + 0.7) * _ease(min(e.state_t / 0.35, 1.0))
    return 0.0


def glaive(r, length, steel, lit, glow=False, rime=0.0, trail=False):
    """A crescent glaive in a `held` frame: a long silver-shod haft along +X, a crescent blade at its
    head (its edge on +Y, horns curling back), a crescent of moonlight set in its socket. `rime` (0..1)
    creeps frost up the head; `trail` leaves ghosts of the blade behind its edge as it cuts."""
    r.part("cube", length * 0.45 - 0.3, 0, 0, length, 0.05, 0.05, SILVER_DARK)  # the haft
    r.part("cube", -0.3 - length * 0.05, 0, 0, 0.12, 0.08, 0.08, SILVER)  # the butt-cap
    for k in (0.25, 0.55):
        r.part("cube", length * k - 0.3, 0, 0, 0.05, 0.07, 0.07, SILVER)  # silver bands
    head = length * 0.95 - 0.3
    r.part("cube", head, 0, 0, 0.16, 0.1, 0.09, SILVER)  # the socket
    r.part("sphere", head, 0.0, 0, 0.07, 0.07, 0.1, _glow(lit), glow=lit)
    for i in range(6):  # the crescent blade, a bow of steel from the socket's back round to its tip
        a = -0.5 + i * 0.42
        x, y = head + 0.12 + math.sin(a) * 0.28, 0.1 + math.cos(a) * 0.22 - 0.12
        r.part("lozenge", x, y + 0.12, 0, 0.18, 0.06, 0.03, steel, rz=-a, glow=glow)
        if trail and lit:  # the light it leaves behind its edge
            for j in (1, 2):
                r.part("lozenge", x, y + 0.12 - 0.16 * j, 0, 0.18, 0.05, 0.02, _dim(MOON_GLOW, 1 - 0.3 * j),
                       rz=-a, glow=True, tex="mist")  # fmt: skip
    if rime > 0 and lit:  # frost creeping up from the socket over the blade
        for i in range(5):
            if i / 5 < rime:
                r.part("cone", head - 0.3 + 0.12 * i, 0.07, 0.05 * (1 if i % 2 else -1), 0.05, 0.14, 0.05, FROST,
                       rz=0.3 * (1 if i % 2 else -1), glow=True)  # fmt: skip


def pale_sentinel(r, e, t):
    """The Pale Sentinel: an empty suit of silvered plate, still keeping its watch, moonlight shining
    out of its joints and the slit of its great helm. A crescent crest on the helm, a tattered cloak
    of stippled mist, a tall shield with a crescent on its face, and a crescent glaive it sweeps all
    round. Slain, it topples back and the light in it goes out."""
    fall = death_fall(e, 0.8)
    lit = e.alive
    swing = walk_cycle(e, t) * 0.7
    plate = hit_tint((250, 236, 236)) if e.flashing else SILVER
    dark = _dim(plate, 0.68)
    light = _glow(lit)
    lean = (-0.3 if e.state == "hurt" else 0.0) + 1.4 * fall
    with r.at(-0.3 * fall, 0.3 * fall, 0, rz=lean, ry=_sweep_spin(e) * (1 - fall)):
        for side, a in ((-0.16, swing), (0.16, -swing)):  # the legs: greaves, knee-cops, sabatons
            with r.at(0, 1.0, side, rz=a + 0.3 * fall):
                r.part("cube", 0, -0.24, 0, 0.17, 0.48, 0.17, plate)
                r.part("sphere", 0.06, -0.5, 0, 0.13, 0.12, 0.13, dark)
                with r.at(0, -0.5, 0, rz=-0.1 - 0.3 * fall):
                    r.part("cube", 0, -0.22, 0, 0.15, 0.44, 0.15, plate)
                    r.part("cube", 0.08, -0.46, 0, 0.3, 0.07, 0.15, dark)  # the sabaton
        r.part("cube", 0, 1.0, 0, 0.3, 0.12, 0.5, light, glow=lit)  # moonlight at the hips
        r.part("cube", 0, 1.08, 0, 0.36, 0.22, 0.54, dark)  # the fauld
        for z in (-0.16, 0.0, 0.16):  # its lames hanging over the thighs
            r.part("cube", 0.12, 0.92, z, 0.06, 0.22, 0.14, plate, rz=-0.1)
        r.part("cube", 0, 1.45, 0, 0.42, 0.56, 0.58, plate)  # the cuirass
        r.part("cube", 0.21, 1.48, 0, 0.04, 0.4, 0.06, _dim(plate, 1.12))  # its ridge
        r.part("cube", 0.22, 1.4, 0, 0.02, 0.12, 0.2, light, glow=lit)  # light through a rent in it
        r.part("cube", 0, 1.78, 0, 0.3, 0.12, 0.34, dark)  # the gorget
        for side in (-1, 1):  # the pauldrons
            r.part("sphere", 0, 1.74, side * 0.34, 0.24, 0.18, 0.24, plate)
        flap = math.sin(t * 1.9) * 0.1
        for i, z in enumerate((-0.2, 0.0, 0.2)):  # the cloak, worn to a mist
            drop = 1.1 - 0.15 * (i % 2)
            with r.at(-0.24, 1.76, z, rz=-0.12 - flap):
                r.part("cube", 0, -drop / 2, 0, 0.03, drop, 0.2, SPECTRE_DARK, tex="mist", glow=lit)
        with r.at(0.02, 1.98, 0, rz=math.sin(t * 1.3) * 0.05 * (1 - fall)):  # the great helm
            r.part("cube", 0, 0, 0, 0.3, 0.34, 0.28, plate)
            r.part("cube", 0.15, 0.02, 0, 0.02, 0.04, 0.2, light, glow=lit)  # the eye slit
            r.part("cube", 0.15, -0.08, 0, 0.02, 0.1, 0.04, VOID)  # the breaths
            r.part("cone", 0, 0.2, 0, 0.3, 0.1, 0.28, dark)  # its crown
            for i in range(5):  # the crescent crest, horns up
                a = math.pi * (0.15 + 0.7 * i / 4)
                r.part("cube", -math.cos(a) * 0.18, 0.3 + (1 - math.sin(a)) * 0.14, 0, 0.07, 0.07, 0.04,
                       _dim(plate, 1.1), rz=a - math.pi / 2)  # fmt: skip
        # The shield arm: a tall shield, a crescent of silver on its face.
        with r.at(0, 1.66, -0.4, rz=-0.3 * fall + 0.15 * swing):
            r.part("cube", 0, -0.2, 0, 0.13, 0.4, 0.13, plate)
            with r.at(0.18, -0.3, -0.12):
                r.part("cube", 0, 0, 0, 0.08, 1.0, 0.56, dark)
                r.part("cube", 0.05, 0, 0, 0.02, 0.92, 0.48, MOONSTONE)
                for i in range(5):
                    a = math.pi * (0.2 + 0.6 * i / 4)
                    r.part("cube", 0.065, math.sin(a) * 0.18 - 0.05, math.cos(a) * 0.18, 0.02, 0.07, 0.06,
                           SILVER, rx=a)  # fmt: skip
        # The glaive arm.
        shoulder, elbow = chop_angle(e) - 0.4 * fall, elbow_bend(e) * (1 - fall)
        if e.attack_kind == "sweep" and e.state in ("windup", "attack"):
            shoulder, elbow = 1.5, 0.1  # held out flat for the sweep
            blade = 0.0
        else:
            blade = blade_angle(e)
        wrist = aim_wrist(_mix(blade, -lean, fall), shoulder + elbow)
        with r.at(0, 1.66, 0.4, rz=shoulder):
            r.part("cube", 0, -0.18, 0, 0.13, 0.36, 0.13, plate)
            r.part("sphere", 0, -0.36, 0, 0.1, 0.1, 0.1, light, glow=lit)  # light at the elbow
            with r.at(0, -0.36, 0, rz=elbow):
                r.part("cube", 0, -0.16, 0, 0.12, 0.32, 0.12, plate)
                with r.at(0, -0.36, 0), held(r, wrist, dark, size=0.13, splay=0.4):
                    glaive(r, 2.0, (206, 214, 232), lit)


# --- the Lantern Wraith ---------------------------------------------------------------------------


def lantern_wraith(r, e, t):
    """The Lantern Wraith: a hooded shade with no legs under its dusk-blue robe, drifting a hand above
    the ground, its hem fraying into mist. Two pale eyes in the dark of the hood; long thin arms, one
    holding up a crook from which hangs a lantern of trapped moonlight, the other reaching. As it winds
    up a throw the lantern blazes and frost gathers in its claw. Slain, it sinks into a heap of robe,
    and the lantern falls and goes dark."""
    fall = death_fall(e, 0.9)
    lit = e.alive
    cloth = hit_tint((240, 236, 250)) if e.flashing else SHROUD
    shade = _dim(cloth, 0.7)
    bob = math.sin(t * 1.6) * 0.06 * (1 - fall)
    winding = e.state == "windup"
    k = _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0)) if winding else 0.0
    sink = _mix(1.0, 0.25, fall)  # the robe empties and settles
    with r.at(-0.2 * fall, (0.3 + bob) * (1 - fall), 0, rz=(-0.25 if e.state == "hurt" else 0.0)):
        r.part("cone", 0, 0.75 * sink, 0, 0.62, 1.5 * sink, 0.62, cloth)  # the robe, tapering below
        r.part("cone", 0, 0.45 * sink, 0, 0.5, 1.0 * sink, 0.5, shade, rx=math.pi)  # its hollow skirts
        for i in range(6):  # the hem, fraying into mist
            a = i * math.pi / 3 + t * 0.4
            r.part("cube", math.cos(a) * 0.26, 0.1 - 0.1 * (i % 2), math.sin(a) * 0.26, 0.14, 0.4 * sink,
                   0.1, SPECTRE_DARK, ry=-a, tex="mist")  # fmt: skip
        with r.at(0, 1.4 * sink, 0):
            r.part("cube", 0, 0, 0, 0.34, 0.3, 0.46, cloth)  # the shoulders
            r.part("cube", 0.12, -0.25, 0, 0.12, 0.3, 0.24, shade)  # the folds down its front
            with r.at(0.04, 0.3, 0, rz=0.15 + 0.4 * fall):  # the hood, its head bowed
                r.part("sphere", 0, 0, 0, 0.32, 0.36, 0.32, cloth)
                r.part("cone", -0.08, 0.22, 0, 0.18, 0.24, 0.18, cloth, rz=0.5)  # its peak
                r.part("cube", 0.13, -0.02, 0, 0.08, 0.24, 0.2, VOID)  # nothing inside
                for side in (-1, 1):  # two pale eyes
                    r.part("cube", 0.17, 0.02, side * 0.05, 0.02, 0.03, 0.04, _glow(lit), glow=lit)
            # The lantern arm: up and forward, the crook in its claw, the lantern hung from its hook.
            raise_ = 0.9 + 0.7 * k
            with r.at(0, 0.08, 0.26, rz=_mix(raise_ + 0.2, 1.5, fall)):
                _bar(r, (0, 0, 0), (0, -0.38, 0), 0.08, cloth)
                with r.at(0, -0.38, 0, rz=-0.4):
                    _bar(r, (0, 0, 0), (0, -0.34, 0), 0.06, shade)
                    with r.at(0, -0.36, 0):
                        hand(r, SPECTRE, 0.08, bony=True, curl=1.0)
                        _bar(r, (-0.25, 0, 0), (0.55, 0, 0), 0.04, SILVER_DARK)  # the crook's staff
                        _bar(r, (0.55, 0, 0), (0.6, 0.12, 0), 0.04, SILVER_DARK)
                        _bar(r, (0.6, 0.12, 0), (0.7, 0.08, 0), 0.03, SILVER_DARK)
            # The lantern, hanging straight down from the crook's hook whatever the arm does.
            sway = math.sin(t * 2.1) * 0.08
            reach = math.sin(raise_ * (1 - fall) + 0.2 - 0.4)
            with r.at(0.25 + 0.5 * reach, _mix(-0.15 + 0.4 * k, -0.2, fall), 0.4, rx=sway * (1 - fall)):
                bright = 1.0 + 0.25 * k
                r.part("cube", 0, 0, 0, 0.2, 0.26, 0.2, SILVER_DARK, tex="iron_bars")  # its cage
                r.part("sphere", 0, 0, 0, 0.13 * bright, 0.17 * bright, 0.13 * bright, _glow(lit), glow=lit)
                r.part("cone", 0, 0.18, 0, 0.18, 0.1, 0.18, SILVER)
                r.part("cube", 0, -0.15, 0, 0.16, 0.04, 0.16, SILVER)
            # The reaching arm, frost gathering in its claw as it winds up.
            with r.at(0, 0.05, -0.26, rz=_mix(0.6 + 0.8 * k, 1.6, fall)):
                _bar(r, (0, 0, 0), (0, -0.38, 0), 0.08, cloth)
                with r.at(0, -0.38, 0, rz=-0.5):
                    _bar(r, (0, 0, 0), (0, -0.34, 0), 0.06, shade)
                    with r.at(0, -0.36, 0):
                        hand(r, SPECTRE, 0.08, bony=True, curl=0.3)
                        if winding and lit:
                            r.part("cone", 0.12, -0.1, 0, 0.06, 0.24 * k + 0.02, 0.06, FROST, rz=-math.pi / 2,
                                   glow=True)  # fmt: skip
        for i in range(3):  # wisps of mist trailing behind it
            u = (t * 0.5 + i / 3) % 1.0
            r.part("cube", -0.3 - 0.6 * u, 0.6 + 0.3 * i, math.sin(t + i) * 0.2, 0.3, 0.2, 0.2,
                   _dim(SPECTRE_DARK, 1 - 0.5 * u), tex="mist")  # fmt: skip


# --- the Moonhound --------------------------------------------------------------------------------


def moonhound(r, e, t):
    """The Moonhound: a gaunt hound gone white as frost, ribs showing under its coat, a long narrow
    head, its eyes two small moons. Mist streams off its back as it runs. It crouches before it springs
    and flies at you stretched out. Slain, it falls on its side and its eyes go dark."""
    fall = death_fall(e, 0.6)
    lit = e.alive
    coat = hit_tint((255, 236, 236)) if e.flashing else HOUND
    shade = _dim(coat, 0.72)
    running = e.state == "chase"
    gait = math.sin(t * (14 if running else 3)) * (0.7 if running else 0.1) * (1 - fall)
    crouch = stretch = 0.0
    if e.state == "windup":
        crouch = -0.18 * _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
    elif e.state == "attack" and e.attack_kind == "pounce":
        stretch = 1.0
    elif e.state == "attack":
        stretch = 0.4
    y0 = (0.62 + crouch) * (1 - fall) + 0.24 * fall
    with r.at(0, y0, 0, rx=fall * math.pi / 2):
        r.part("sphere", 0.12, 0.04, 0, 0.62, 0.34, 0.32, coat)  # the deep chest
        r.part("sphere", -0.32, 0.06, 0, 0.5, 0.26, 0.26, shade)  # the tucked belly and haunch
        for i in range(4):  # ribs showing through
            r.part("cube", 0.06 - i * 0.1, -0.02, 0, 0.03, 0.26, 0.33, _dim(coat, 0.85))
        r.part("cube", -0.1, 0.2, 0, 0.7, 0.04, 0.08, _dim(coat, 1.08))  # the spine's ridge
        for side in (-1, 1):
            for x, phase in ((0.28, 0.0), (-0.42, math.pi)):  # the long legs
                a = math.sin(t * 14 + phase + side) * 0.6 * (gait != 0) * (1 - fall) - stretch * (
                    0.9 if x > 0 else -0.9
                )
                with r.at(x, -0.08, side * 0.13, rz=a):
                    r.part("cube", 0, -0.2, 0, 0.09, 0.4, 0.09, coat)
                    with r.at(0, -0.4, 0, rz=0.3 if x < 0 else -0.2):
                        r.part("cube", 0, -0.12, 0, 0.06, 0.26, 0.06, shade)
                        r.part("cube", 0.05, -0.25, 0, 0.12, 0.04, 0.08, _dim(coat, 0.6))  # the paw
        with r.at(-0.62, 0.12, 0, rz=0.6 + gait * 0.3):  # the tail, streaming
            _bar(r, (0, 0, 0), (-0.45, 0.12, math.sin(t * 5) * 0.12), 0.06, coat)
        with r.at(0.42, 0.18 + 0.08 * stretch, 0, rz=-0.2 + 0.25 * stretch - 0.2 * crouch):  # the head
            r.part("cube", 0.08, 0.06, 0, 0.18, 0.18, 0.2, coat)  # the neck
            r.part("cube", 0.24, 0.12, 0, 0.22, 0.18, 0.18, coat)  # the skull
            r.part("cube", 0.44, 0.07, 0, 0.26, 0.09, 0.11, coat)  # the long muzzle
            r.part("cube", 0.57, 0.08, 0, 0.04, 0.05, 0.07, (60, 58, 70))  # the nose
            jaw = 0.4 if e.state in ("windup", "attack") else 0.1
            with r.at(0.34, 0.02, 0, rz=-jaw):
                r.part("cube", 0.1, -0.02, 0, 0.22, 0.04, 0.09, shade)  # the jaw
                r.part("cube", 0.12, 0.01, 0, 0.18, 0.02, 0.08, (232, 232, 236))  # its teeth
            for side in (-1, 1):
                r.part("cube", 0.3, 0.16, side * 0.08, 0.04, 0.04, 0.04, _glow(lit), glow=lit)  # eyes
                r.part("cone", 0.18, 0.28, side * 0.07, 0.07, 0.16, 0.05, shade, rz=-0.3)  # pricked ears
        for i in range(3):  # mist streaming off its back
            u = (t * 0.9 + i / 3) % 1.0
            r.part("cube", -0.2 - 0.6 * u, 0.24 + 0.15 * u, 0, 0.28, 0.12, 0.22, _dim(SPECTRE, 1 - 0.5 * u),
                   tex="mist")  # fmt: skip


# --- the Veiled Knight ----------------------------------------------------------------------------


def _fading(e):
    """0..1 how far a blinker has faded into the moonlight: through its windup, gone at the blink."""
    if e.attack_kind != "blink":
        return 0.0
    if e.state == "windup":
        return _ease(min(e.state_t / max(e.windup_time, 1e-3), 1.0))
    if e.state == "attack":
        return 1.0
    return 0.0


def veiled_knight(r, e, t):
    """The Veiled Knight: one of the Duchess's honour guard, half of him no longer quite here. Plate
    as pale as frost on glass under a long veil of moon-silk thrown over his helm and shoulders, a cape
    of mist, a crescent on his breast and a long straight sword. Winding up a blink he fades to a
    stipple of mist, light pouring out of him. Slain, he falls to his knees and over, and goes dark."""
    fall = death_fall(e, 0.8)
    lit = e.alive
    fade = _fading(e)
    ghost = "mist" if fade > 0.5 else "white"  # half faded: a dither of himself
    swing = walk_cycle(e, t) * 0.6
    plate = hit_tint((250, 236, 236)) if e.flashing else (196, 206, 226)
    dark = _dim(plate, 0.66)
    light = _glow(lit)
    lean = (-0.3 if e.state == "hurt" else 0.0) + 1.3 * fall
    with r.at(-0.25 * fall, 0.3 * fall, 0, rz=lean):
        for side, a in ((-0.14, swing), (0.14, -swing)):
            knee = 0.1 + 0.4 * max(0.0, a) + 0.9 * fall
            with r.at(0, 0.94, side, rz=a + 0.6 * fall):
                r.part("cube", 0, -0.22, 0, 0.15, 0.44, 0.15, plate, tex=ghost)
                r.part("sphere", 0.05, -0.46, 0, 0.11, 0.1, 0.11, dark, tex=ghost)
                with r.at(0, -0.46, 0, rz=-knee):
                    r.part("cube", 0, -0.21, 0, 0.13, 0.42, 0.13, plate, tex=ghost)
                    r.part("cube", 0.07, -0.43, 0, 0.26, 0.06, 0.13, dark, tex=ghost)
        r.part("cube", 0, 0.98, 0, 0.32, 0.2, 0.48, dark, tex=ghost)  # the tassets
        r.part("cone", 0, 0.86, 0, 0.5, 0.36, 0.56, _dim(dark, 0.9), tex=ghost)  # a skirt of mail
        r.part("cube", 0.17, 0.75, 0, 0.04, 0.6, 0.22, SHROUD, tex=ghost)  # the tabard's hanging front
        r.part("cube", 0, 1.36, 0, 0.36, 0.5, 0.5, plate, tex=ghost)  # the breastplate
        r.part("cube", 0, 1.62, 0, 0.26, 0.1, 0.3, dark, tex=ghost)  # the gorget
        for i in range(5):  # the crescent on his breast
            a = math.pi * (0.15 + 0.7 * i / 4)
            r.part("cube", 0.19, 1.3 + (1 - math.sin(a)) * 0.12, math.cos(a) * 0.12, 0.02, 0.05, 0.05, light,
                   glow=lit)  # fmt: skip
        for side in (-1, 1):
            r.part("sphere", 0, 1.62, side * 0.3, 0.2, 0.15, 0.2, plate, tex=ghost)  # the pauldrons
        flap = math.sin(t * 1.7) * 0.1
        for i, z in enumerate((-0.22, -0.07, 0.07, 0.22)):  # the cape of mist
            drop = 1.2 - 0.12 * (i % 2)
            with r.at(-0.2, 1.62, z, rz=-0.1 - flap):
                r.part("cube", 0, -drop / 2, 0, 0.02, drop, 0.16, SPECTRE_DARK, tex="mist")
        with r.at(0.02, 1.82, 0, rz=math.sin(t * 1.1) * 0.04 * (1 - fall)):  # the helm under its veil
            r.part("cube", 0, 0, 0, 0.26, 0.3, 0.24, plate, tex=ghost)
            r.part("cube", 0.13, 0.02, 0, 0.02, 0.03, 0.17, light, glow=lit)  # the visor's slit
            r.part("sphere", 0, 0.16, 0, 0.17, 0.1, 0.15, dark, tex=ghost)  # its rounded crown
            # The veil of moon-silk thrown over it, draped to the shoulders and trailing down his back.
            r.part("cone", 0, -0.02, 0, 0.42, 0.5, 0.42, MOON_SILK, tex="mist", glow=lit)
            r.part("sphere", 0, 0.2, 0, 0.2, 0.08, 0.18, MOON_SILK, tex="mist", glow=lit)
            for i, z in enumerate((-0.12, 0.0, 0.12)):
                sway = math.sin(t * 1.4 + i) * 0.08
                with r.at(-0.14, -0.1, z, rz=-0.15 - sway):
                    r.part("cube", 0, -0.35, 0, 0.02, 0.7 + 0.1 * i, 0.12, SILK_SHADE, tex="mist", glow=lit)
        with r.at(0, 1.56, -0.33, rz=swing * 0.4 - 0.3 * fall + 0.3 * fade):  # the free arm
            r.part("cube", 0, -0.16, 0, 0.11, 0.32, 0.11, plate, tex=ghost)
            with r.at(0, -0.32, 0, rz=0.4):
                r.part("cube", 0, -0.15, 0, 0.1, 0.3, 0.1, plate, tex=ghost)
                with r.at(0, -0.32, 0):
                    hand(r, dark, 0.09, curl=0.8)
        shoulder, elbow = chop_angle(e) - 0.4 * fall, elbow_bend(e) * (1 - fall)
        wrist = aim_wrist(_mix(blade_angle(e), -lean, fall), shoulder + elbow)
        with r.at(0, 1.56, 0.33, rz=shoulder):
            r.part("cube", 0, -0.16, 0, 0.11, 0.32, 0.11, plate, tex=ghost)
            with r.at(0, -0.32, 0, rz=elbow):
                r.part("cube", 0, -0.15, 0, 0.1, 0.3, 0.1, plate, tex=ghost)
                with r.at(0, -0.34, 0), held(r, wrist, dark, size=0.11, splay=0.4):
                    sword_parts(r, 1.25, 0.08, (214, 224, 246), grip=(70, 76, 100), guard=SILVER_DARK)
    if fade > 0 and lit:  # moonlight pouring out of him as he goes
        for i in range(5):
            a = i * 1.26 + t * 2
            u = (t * 1.5 + i / 5) % 1.0
            r.part("cube", math.cos(a) * 0.4 * fade, 0.4 + 1.6 * u, math.sin(a) * 0.4 * fade, 0.12, 0.12, 0.12,
                   MOON_GLOW, glow=True, tex="mist")  # fmt: skip


# --- Duchess Ilvane ---------------------------------------------------------------------------------


def duchess_arms(e, t):
    """(glaive arm, free arm, blade direction, elbow, twist, glow) for the Duchess's moves, angles as
    in `models._warden_arms`. Sweep: the glaive held out flat as she turns all the way round. Combo:
    three cuts, alternating. Frost lance: her free hand thrust out, frost in it. Moonbeam: both arms
    raised to the moon. Moonfall: the glaive raised straight up to it. Blink: her arms drawn in to her
    as she fades. Kindle (her rage): arms flung wide."""
    hit, blade, elbow = chop_angle(e), blade_angle(e), elbow_bend(e)
    free, twist, glow = 0.3, 0.0, False
    kind = e.attack_kind
    acting = e.state in ("windup", "attack")
    up = _ease(duchess_tell(e)) if e.state == "windup" else 1.0
    if kind == "sweep" and acting:
        hit, blade, elbow = _mix(0.0, 1.5, up), 0.0, 0.1
        twist = _sweep_spin(e)
    elif kind == "combo" and e.state == "attack":
        i = e.combo_swing
        gap = e.combo_gap
        u = (e.state_t - i * gap) / gap
        lift = _ease(min(u / 0.35, 1)) if u < 0.35 else 1 - _ease(min((u - 0.35) / 0.25, 1))
        hit = _mix(CHOP_LANDED, CHOP_RAISED - 0.4, lift)
        blade = _mix(BLADE_LANDED, BLADE_RAISED, lift)
        elbow = _mix(ELBOW_STRIKE, ELBOW_COCKED, lift)
        twist = 0.35 if i % 2 == 0 else -0.35
    elif kind == "frost_lance" and acting:
        hit, blade, elbow = 0.2, BLADE_REST, ELBOW_REST
        free, glow = _mix(0.3, 1.55, up), True
    elif kind == "moonbeam" and acting:
        hit = _mix(0.0, math.pi - 0.5, up)
        blade, elbow = _mix(BLADE_REST, math.pi / 2, up), _mix(ELBOW_REST, 0.2, up)
        free, glow = _mix(0.3, math.pi - 0.4, up), True
    elif kind == "moonfall" and acting:
        hit = _mix(0.0, math.pi - 0.15, up) + math.sin(t * 30) * 0.04
        blade, elbow = _mix(BLADE_REST, math.pi / 2, up), _mix(ELBOW_REST, 0.1, up)
        free, glow = _mix(0.3, 2.4, up), True
    elif kind == "blink" and acting:
        hit, blade, elbow = 0.4, _mix(BLADE_REST, -0.6, up), ELBOW_COCKED
        free = 0.6
    elif kind == "kindle" and acting:
        hit = _mix(0.0, 2.0, up) + math.sin(t * 40) * 0.05
        blade, elbow = _mix(BLADE_REST, 1.2, up), _mix(ELBOW_REST, 0.15, up)
        free, glow = _mix(0.3, 2.0, up), True
    return hit, free, blade, elbow, twist, glow


def duchess_tell(e):
    """0..1 how far the Duchess is through a windup (0 when she isn't winding up): what her tells
    build on, so they keep pace with her quickened tempo."""
    if e.state != "windup":
        return 0.0
    return min(e.state_t / max(e.windup_time, 1e-3), 1.0)


def _crescent(r, x, y, z, radius, n, size, rgb, glow=False, tex=None):
    """A small crescent, horns up, in the YZ plane (facing +X): `n` beads along a bow."""
    for i in range(n):
        a = math.pi * (0.12 + 0.76 * i / (n - 1))
        extra = {"tex": tex} if tex else {}
        r.part("cube", x, y + (1 - math.sin(a)) * radius - radius * 0.6, z + math.cos(a) * radius, size, size,
               size, rgb, glow=glow, **extra)  # fmt: skip


def _sleeve(r, silk, shade, lit, t, phase, ghost):
    """An upper arm in a bell sleeve: the puffed silk, its long cuff, and a second, sheer sleeve of
    moon-silk hanging from the elbow, stirring as she moves."""
    r.part("cube", 0, -0.22, 0, 0.13, 0.44, 0.13, silk, tex=ghost)
    r.part("cone", 0, -0.5, 0, 0.24, 0.3, 0.24, shade, rx=math.pi, tex=ghost)  # the bell cuff
    r.part("cube", 0, -0.37, 0, 0.15, 0.03, 0.15, SILVER)  # its silver band
    with r.at(-0.06, -0.5, 0, rz=-0.15 - math.sin(t * 1.5 + phase) * 0.12):
        r.part("cube", 0, -0.42, 0, 0.03, 0.84, 0.26, SILK_SHADE, tex="mist", glow=lit)


def _gown(r, silk, shade, skirt, rage, lit, t, ghost):
    """Her gown: three tiers of moon-silk spreading to the floor and a sheer fourth over them, a
    frosted hem and a jeweled train behind. In her rage the outer tiers tear into ragged panels of
    mist streaming in the moonlight."""
    r.part("cone", 0, 0.85 * skirt, 0, 2.3, 1.7 * skirt, 2.3, shade, tex=ghost)
    r.part("cone", 0, 1.0 * skirt, 0, 1.7, 1.4 * skirt, 1.7, silk, tex=ghost)
    r.part("cone", 0, 1.25 * skirt, 0, 1.1, 1.0 * skirt, 1.1, _dim(silk, 1.06), tex=ghost)
    if rage:  # the sheer tier torn to ragged panels
        for i in range(10):
            a = i * math.pi / 5 + 0.3
            drop = (1.2 + 0.35 * ((i * 7) % 3)) * skirt
            flap = math.sin(t * 3.1 + i * 1.7) * 0.18
            with (
                r.at(math.cos(a) * 0.62, 1.55 * skirt, math.sin(a) * 0.62, ry=-a),
                r.at(0, 0, 0, rz=-0.42 - flap),
            ):
                r.part("cube", 0, -drop / 2, 0, 0.03, drop, 0.34, SILK_SHADE, tex="mist", glow=lit)
    else:  # the sheer outer tier, whole, over the others
        r.part("cone", 0, 0.95 * skirt, 0, 2.55, 1.9 * skirt, 2.55, SILK_SHADE, tex="mist")
    for y in (0.6, 1.05):  # silver bands embroidered round the tiers
        rad = 1.15 - 0.42 * (y - 0.6) / 0.45
        for i in range(8):
            a = i * math.pi / 4 + (0.39 if y > 1 else 0)
            r.part("cube", math.cos(a) * rad, y * skirt, math.sin(a) * rad, 0.3, 0.03, 0.04, SILVER, ry=-a)
    hem = MOON_GLOW if rage else (150, 168, 214)
    for i in range(12):  # the frosted hem, a ring of scallops glimmering, blazing in her rage
        a = i * math.pi / 6
        r.part("cube", math.cos(a) * 1.1, 0.06, math.sin(a) * 1.1, 0.56, 0.12, 0.08, hem, ry=-a,
               glow=lit)  # fmt: skip


def _train(r, silk, drift, lit):
    """The train sweeping out behind her, moonstones sewn along it."""
    for i in range(3):
        x, w = -0.9 - 0.45 * i, 1.0 - 0.18 * i
        r.part("cube", x, 0.04 + 0.02 * i, drift * i, 0.6, 0.06, w, _dim(silk, 0.9 - 0.06 * i))
        for side in (-1, 1):  # moonstones along its edges
            r.part("sphere", x, 0.09 + 0.02 * i, drift * i + side * (w / 2 - 0.08), 0.06, 0.04, 0.06,
                   _glow(lit), glow=lit)  # fmt: skip
        r.part("cube", x, 0.08 + 0.02 * i, drift * i, 0.5, 0.01, 0.03, SILVER)  # a seam of silver
    r.part("sphere", -2.15, 0.07, drift * 3, 0.14, 0.05, 0.14, _glow(lit), glow=lit)  # the last jewel


def _crown(r, light, lit, flare):
    """Her crown: a ring of silver crescents and three tall spires, a moonstone at each tip. They
    flare as she calls the moon down."""
    for i in range(6):
        a = i * math.pi / 3
        with r.at(math.cos(a) * 0.12, 0.44, math.sin(a) * 0.12, ry=-a):
            r.part("cube", 0, 0, 0, 0.03, 0.1, 0.06, SILVER)
            r.part("cube", 0, 0.06, 0.03, 0.03, 0.05, 0.03, SILVER, rx=0.6)
            r.part("cube", 0, 0.06, -0.03, 0.03, 0.05, 0.03, SILVER, rx=-0.6)
    gem = 0.04 * (1 + 1.2 * flare)
    for z, h in ((0.0, 0.3), (-0.09, 0.2), (0.09, 0.2)):  # the spires, the middle one tallest
        r.part("cone", 0.12, 0.48 + h / 2, z, 0.05, h, 0.05, SILVER)
        r.part("sphere", 0.12, 0.5 + h, z, gem, gem, gem, light, glow=lit)


def _veil(r, lit, t):
    """The long veil over her face, draped from the crown to her breast and down her back, a fringe of
    glowing beads at its hem."""
    r.part("cone", 0.02, 0.1, 0, 0.5, 0.78, 0.48, MOON_SILK, tex="mist", glow=lit)
    for i in range(10):  # the beaded fringe, swaying
        a = i * math.pi / 5
        sway = math.sin(t * 1.3 + i) * 0.015
        r.part("cube", 0.02 + math.cos(a) * 0.24, -0.3, math.sin(a) * 0.23 + sway, 0.03, 0.06, 0.03,
               _glow(lit), glow=lit)  # fmt: skip
    for i, z in enumerate((-0.16, 0.0, 0.16)):  # and trailing down her back
        with r.at(-0.12, 0.2, z, rz=-0.1 - math.sin(t * 1.1 + i) * 0.06):
            r.part("cube", 0, -0.5, 0, 0.02, 1.0 + 0.12 * i, 0.16, SILK_SHADE, tex="mist", glow=lit)


def _halo(r, t, flare):
    """The crescent halo blazing behind her head in her rage, turning slowly and pulsing, flaring as
    she brings the moon down."""
    pulse = 1.0 + 0.06 * math.sin(t * 3) + 0.35 * flare
    with r.at(-0.3, 0.3, 0, rx=t * 0.35):
        for i in range(9):  # horns round under the back of her head
            a = math.pi * (0.05 + 0.9 * i / 8)
            r.part("cube", 0, -math.sin(a) * 0.45 * pulse, math.cos(a) * 0.55 * pulse, 0.04, 0.12, 0.2,
                   MOON_GLOW, glow=True, rx=a - math.pi / 2)  # fmt: skip
        for i in range(6):  # rays between the horns
            a = math.pi * (0.15 + 0.7 * i / 5)
            r.part("cube", 0, -math.sin(a) * 0.72 * pulse, math.cos(a) * 0.8 * pulse, 0.02, 0.18, 0.04,
                   _dim(MOON_GLOW, 0.85), glow=True, rx=a - math.pi / 2)  # fmt: skip
    r.part(
        "sphere", -0.32, 0.3, 0, 0.06, 0.4 * pulse, 0.6 * pulse, _dim(MOON_GLOW, 0.8), tex="mist", glow=True
    )


def _shards(r, top, t):
    """Six shards of moon-frost circling her waist in her rage."""
    for i in range(6):
        a = i * math.pi / 3 + t * 1.1
        y = top - 0.1 + math.sin(t * 2 + i) * 0.12
        r.part("lozenge", math.cos(a) * 1.05, y, math.sin(a) * 1.05, 0.34, 0.08, 0.08, FROST, ry=-a + math.pi / 2,
               rz=0.5, glow=True)  # fmt: skip


def _sweep_ring(r, k):
    """A sweep's tell: a ring of moonlight spreading over the floor round her to the glaive's reach."""
    reach = 1.6 + 2.0 * k
    for i in range(16):
        a = i * math.pi / 8
        r.part("cube", math.cos(a) * reach, 0.03, math.sin(a) * reach, 0.6 * reach / 3, 0.02, 0.08,
               _dim(MOON_GLOW, 0.4 + 0.6 * k), ry=-a + math.pi / 2, glow=True)  # fmt: skip


def moon_duchess(r, e, t):
    """Duchess Ilvane, the Moonwed: a woman as tall as two men in a gown of moon-silk that spreads in
    tiers to the floor under a sheer fourth, banded in silver, its hem rimed with frost and its train
    sewn with moonstones; a corset boned in silver with a crescent brooch, a high collar fanned out
    behind her head, bell sleeves trailing sheer silk, porcelain hands and a crescent glaive. Her
    crown is a ring of silver crescents under three spires, and her face is hidden behind a long veil
    fringed with beads of light.

    Her tells build over each windup: rime creeps up the glaive head and a ring of light spreads over
    the floor before a sweep, the blade kindles before a combo as she steps in, three shards of frost
    form over her hand before the lances, motes rise from her raised hands before the moonbeam, and
    her crown (or halo) flares before the moonfall. A blink fades her to a stipple of mist.

    In her second phase the veil is cast off: her white hair streams loose, her eyes burn with
    moonlight, a great crescent halo turns blazing behind her head, her gown tears into ragged mist,
    shards of frost circle her and her glaive trails light. Slain, she kneels, bows her head and the
    light goes out of her."""
    fall = death_fall(e, 1.4)
    lit = e.alive
    rage = e.phase2 and lit
    fade = _fading(e)
    ghost = "mist" if fade > 0.5 else "white"
    silk = hit_tint((255, 240, 244)) if e.flashing else MOON_SILK
    shade = _dim(silk, 0.76)
    skin = hit_tint((255, 240, 240)) if e.flashing else DUCHESS_SKIN
    light = _glow(lit)
    hit, free, blade, elbow, twist, glow = duchess_arms(e, t)
    kind = e.attack_kind if lit else None
    tell = _ease(duchess_tell(e)) if lit else 0.0
    kneel = fall  # in death the skirt settles and she sinks to her knees in it
    sway = math.sin(t * 0.9) * 0.04 * (1 - fall)
    drift = math.sin(t * 1.2) * 0.05 if e.state == "chase" else 0.0
    skirt = _mix(1.0, 0.45, kneel)
    stepping = kind == "combo" and e.state in ("windup", "attack")
    lunge = 0.3 * (tell if e.state == "windup" else 1.0) if stepping else 0.0
    if kind == "sweep" and e.state == "windup":
        _sweep_ring(r, tell)
    with r.at(lunge, 0, 0, ry=twist * (1 - fall)):
        _gown(r, silk, shade, skirt, rage, lit, t, ghost)
        _train(r, silk, drift, lit)
        for i in range(4):  # mist curling off the gown
            u = (t * 0.4 + i / 4) % 1.0
            a = i * 1.57 + t * 0.3
            r.part("cube", math.cos(a) * 0.9, 0.2 + 1.2 * u, math.sin(a) * 0.9, 0.4, 0.3, 0.4,
                   _dim(SPECTRE, 1 - 0.6 * u), tex="mist")  # fmt: skip
        top = 1.8 * skirt
        if rage:
            _shards(r, top, t)
        with r.at(0, top, 0, rz=sway - 0.45 * kneel):
            r.part("cube", 0, 0.32, 0, 0.36, 0.64, 0.5, silk, tex=ghost)  # the bodice
            r.part("cube", 0.19, 0.32, 0, 0.02, 0.56, 0.14, (176, 182, 200))  # its silver lacing
            for y in (0.12, 0.26, 0.4):
                r.part("cube", 0.195, y, 0, 0.02, 0.02, 0.2, SILVER)
            for z in (-0.2, -0.12, 0.12, 0.2):  # the corset's silver boning
                r.part("cube", 0.185, 0.24, z, 0.015, 0.4, 0.02, SILVER_DARK)
            # The crescent brooch at her breast, a moonstone in its bow.
            _crescent(r, 0.2, 0.55, 0, 0.09, 5, 0.035, SILVER)
            r.part("sphere", 0.21, 0.52, 0, 0.045, 0.045, 0.045, light, glow=lit)
            r.part("cube", 0, 0.02, 0, 0.42, 0.1, 0.62, (176, 182, 200))  # the girdle
            r.part("cube", 0.22, -0.08, 0, 0.06, 0.24, 0.06, SILVER)  # its hanging chain
            r.part("sphere", 0.22, -0.22, 0, 0.06, 0.06, 0.06, light, glow=lit)  # a moonstone on it
            for side in (-1, 1):
                r.part(
                    "sphere", 0, 0.62, side * 0.26, 0.2, 0.14, 0.2, silk, tex=ghost
                )  # the puffed shoulders
            # The high collar, fanned out behind her head, edged with silver.
            for i in range(7):
                a = -1.2 + i * 0.4
                r.part("cube", -0.12, 0.88, math.sin(a) * 0.24, 0.03, 0.42, 0.14, _dim(silk, 0.95),
                       rx=a * 0.6, rz=0.25)  # fmt: skip
                r.part("cube", -0.17, 1.09, math.sin(a) * 0.3, 0.02, 0.03, 0.12, SILVER, rx=a * 0.6, rz=0.25)
            with r.at(0.02, 0.86, 0, rz=-0.4 * kneel):  # the neck and head
                r.part("cube", 0, 0.04, 0, 0.1, 0.16, 0.1, skin)
                r.part("cube", 0.0, 0.02, 0, 0.12, 0.03, 0.12, SILVER)  # a silver choker
                r.part("sphere", 0.02, 0.24, 0, 0.17, 0.23, 0.16, skin)  # the head
                eyes = MOON_GLOW if rage else (60, 66, 90)
                for side in (-1, 1):
                    r.part("cube", 0.15, 0.26, side * 0.06, 0.02, 0.025, 0.045, eyes, glow=rage)
                r.part("cube", 0.16, 0.16, 0, 0.02, 0.02, 0.06, (150, 130, 150))  # her lips
                hair = DUCHESS_HAIR
                if rage:  # her white hair streaming loose
                    for i in range(5):
                        z = (i - 2) * 0.07
                        stream = math.sin(t * 3 + i) * 0.1
                        r.part("cube", -0.2, 0.06, z, 0.06, 0.6, 0.06, hair, rz=-0.5 + stream)
                else:  # bound up under the crown
                    r.part("sphere", -0.06, 0.36, 0, 0.16, 0.12, 0.17, hair)
                flare = tell if kind == "moonfall" else 0.0
                _crown(r, light, lit, 0.0 if rage else flare)
                if not rage:
                    _veil(r, lit, t)
                else:
                    _halo(r, t, flare)
            # Her free arm (-Z), the hand open: frost gathers in it for a lance.
            with r.at(0, 0.62, -0.32, rz=free * (1 - fall)):
                _sleeve(r, silk, shade, lit, t, 0.0, ghost)
                with r.at(0, -0.46, 0, rz=0.3):
                    r.part("cube", 0, -0.2, 0, 0.09, 0.4, 0.09, skin)
                    with r.at(0, -0.42, 0):
                        hand(r, skin, 0.11, curl=0.2 if glow else 0.7)
                        if glow and lit:
                            r.part("sphere", 0.08, -0.12, 0, 0.12, 0.12, 0.12, MOON_GLOW, glow=True)
                        if kind == "frost_lance" and e.state == "windup":
                            for spread in (-0.45, 0.0, 0.45):  # three shards forming, one per lance
                                with r.at(0.1, -0.2, 0, rx=spread):
                                    r.part("lozenge", 0, -0.12 - 0.2 * tell, 0, 0.07, 0.1 + 0.36 * tell, 0.07,
                                           FROST, glow=True)  # fmt: skip
            # The glaive arm (+Z).
            shoulder = _mix(hit, 1.0, fall)
            el = elbow * (1 - fall)
            wrist = aim_wrist(_mix(blade, 0.35, fall), shoulder + el)
            rime = tell if kind == "sweep" and e.state == "windup" else 0.0
            kindled = rage or (kind == "combo" and (e.state == "attack" or tell > 0.3))
            trailing = rage and e.state == "attack" and kind in ("sweep", "combo")
            with r.at(0, 0.62, 0.32, rz=shoulder):
                _sleeve(r, silk, shade, lit, t, 1.3, ghost)
                with r.at(0, -0.46, 0, rz=el):
                    r.part("cube", 0, -0.2, 0, 0.09, 0.4, 0.09, skin)
                    with r.at(0, -0.44, 0), held(r, wrist, skin, size=0.12, splay=0.35):
                        glaive(r, 2.6, (226, 234, 250), lit, glow=kindled, rime=rime, trail=trailing)
            if kind == "moonbeam" and e.state == "windup":  # motes rising off her raised hands
                for i in range(6):
                    u = (t * 1.6 + i / 6) % 1.0
                    r.part("cube", 0.1 + math.sin(i * 2.1) * 0.15, 1.3 + 1.6 * u * tell, math.cos(i * 1.3) * 0.25,
                           0.07, 0.07, 0.07, _dim(MOON_GLOW, 1 - 0.4 * u), glow=True)  # fmt: skip
    if fade > 0 and lit:  # moonlight pouring off her as she goes
        for i in range(6):
            a = i * 1.05 + t * 2
            u = (t * 1.2 + i / 6) % 1.0
            r.part("cube", math.cos(a) * 0.9 * fade, 0.4 + 2.6 * u, math.sin(a) * 0.9 * fade, 0.18, 0.18, 0.18,
                   MOON_GLOW, glow=True, tex="mist")  # fmt: skip


# --- what they throw and call down ----------------------------------------------------------------


def frost_lance(r, rgb, t):
    """A lance of moon-frost flying point first (+X): a long faceted shard with a glowing core, a
    collar of smaller shards round its butt and a trail of frost motes."""
    r.part("lozenge", 0.1, 0, 0, 0.8, 0.09, 0.09, rgb, glow=True)  # the shard
    r.part("cone", 0.56, 0, 0, 0.09, 0.3, 0.09, FROST, rz=-math.pi / 2, glow=True)  # its point
    r.part("cube", 0.1, 0, 0, 0.6, 0.04, 0.04, (255, 255, 255), glow=True)  # the core
    for i in range(3):
        a = i * 2.09 + t * 4
        r.part("cone", -0.25, math.cos(a) * 0.06, math.sin(a) * 0.06, 0.04, 0.2, 0.04, rgb, rz=math.pi / 2,
               glow=True)  # fmt: skip
    for i in range(3):  # frost motes trailing behind
        u = (t * 3 + i / 3) % 1.0
        r.part("cube", -0.4 - 0.5 * u, math.sin(i * 2.3) * 0.08, math.cos(i * 1.7) * 0.08, 0.05, 0.05, 0.05,
               _dim(rgb, 1 - 0.5 * u), glow=True)  # fmt: skip


def moonbeam(r, glow, flame, t):
    """A shaft of moonlight called down (`hazards.Eruption` style "moon"): first a ring of pale runes
    kindles on the floor and frost spreads in it (`glow` 0..1), then the shaft falls, a column of
    light with a brighter core and motes drifting up it (`flame` 0..1)."""
    if glow > 0:
        r.part("cyl", 0, 0.015, 0, 1.9 * glow, 0.02, 1.9 * glow, (150, 170, 214), glow=True)  # the frost
        for i in range(8):  # the runes, turning
            a = i * math.pi / 4 + t * 0.6
            r.part("cube", math.cos(a) * 0.85, 0.03, math.sin(a) * 0.85, 0.22, 0.02, 0.06,
                   _dim(MOON_GLOW, 0.5 + 0.5 * glow), ry=-a, glow=True)  # fmt: skip
    if flame <= 0:
        return
    h = 7.0
    r.part("cyl", 0, h / 2, 0, 1.6 * flame, h, 1.6 * flame, (170, 190, 236), tex="mist", glow=True)
    r.part("cyl", 0, h / 2, 0, 0.7 * flame, h, 0.7 * flame, MOON_GLOW, glow=True)  # its core
    for i in range(5):
        u = (t * 0.8 + i / 5) % 1.0
        a = i * 1.26
        r.part(
            "cube", math.cos(a) * 0.6, 0.2 + u * 3.5, math.sin(a) * 0.6, 0.08, 0.08, 0.08, FROST, glow=True
        )


def blink_mist(r, k, radius):
    """The mist of a blink: a ring of pale puffs billowing out from where a blinker stepped into (or
    out of) the moonlight, thinning as they go."""
    for i in range(10):
        a = i * math.pi / 5
        d = radius * (0.3 + 0.7 * k)
        size = 0.5 * (1 - k) + 0.1
        r.part("cube", math.cos(a) * d, 0.4 + 0.8 * k + 0.2 * (i % 2), math.sin(a) * d, size, size, size,
               _dim(SPECTRE, 1.1 - 0.4 * k), ry=-a, tex="mist")  # fmt: skip
    r.part("cyl", 0, 1.0, 0, 0.6 * (1 - k) + 0.05, 2.0, 0.6 * (1 - k) + 0.05, MOON_SILK, tex="mist")


# --- the Vesper Gate ------------------------------------------------------------------------------

GATE_SPRING = 3.8  # where the Vesper Gate's pointed arch springs from its piers
GATE_HALF = 0.9  # half the width of its doorway


def vesper_gate(r, open_t, t):
    """The Vesper Gate between Harrowmere and Vesperholm, built out of the wall behind its tile (-X)
    and facing +X: a tall pointed arch of pale moonstone on clustered piers, a crescent of silver over
    its keystone and three empty sockets in its lintel, one for each sigil the prophecy can name.
    Shut, its leaves of silver tracery stand before black passage. Open (`open_t` 1), the leaves have
    swung out, the three sockets shine and the cold light of the moonlit city pours through, motes of
    frost drifting out with it."""
    stone, dark = MOONSTONE, MOONSTONE_DARK
    spring, half = GATE_SPRING, GATE_HALF
    radius = 2 * half
    mid = radius + 0.2
    opened = min(max(open_t, 0.0), 1.0)
    lit = opened > 0
    beyond = (120, 136, 176) if lit else PASSAGE_DARK
    r.part("cube", -0.97, (spring + 1.2) / 2, 0, 0.04, spring + 1.2, 2 * half + 0.04, beyond, glow=lit)
    for side in (-1, 1):
        z = side * (half + 0.2)
        r.part("cube", -0.86, (spring + 0.1) / 2, side * (half - 0.01), 0.22, spring + 0.1, 0.02,
               _dim(dark, 0.5))  # fmt: skip
        r.part("cube", -0.66, 0.25, z, 0.8, 0.5, 0.56, dark, tex="moonstone")  # the pier's base
        r.part("cube", -0.7, spring / 2, z, 0.62, spring, 0.38, stone, tex="moonstone")  # the pier
        for dz in (-0.16, 0.16):  # clustered shafts up its face
            r.part("cyl", -0.36, spring / 2, z + dz, 0.12, spring - 0.4, 0.12, _dim(stone, 1.12))
        r.part("cube", -0.66, spring - 0.08, z, 0.74, 0.16, 0.5, dark, tex="moonstone")  # its capital
        span = math.pi - math.acos(-half / mid)
        for i in range(6):  # the voussoirs of the pointed arch
            a = math.pi - (i + 0.5) * span / 6
            vz, vy = half + mid * math.cos(a), spring + mid * math.sin(a)
            r.part("cube", -0.7, vy, side * vz, 0.62, 0.38, 0.4, stone if i % 2 else _dim(stone, 0.92),
                   tex="moonstone", rx=side * (math.pi / 2 - a))  # fmt: skip
    apex = spring + math.sqrt(mid * mid - half * half)
    r.part("cube", -0.66, apex, 0, 0.72, 0.6, 0.4, _dim(stone, 1.1), tex="moonstone")  # the keystone
    with r.at(-0.3, apex + 0.6, 0):  # the silver crescent over it, horns up
        for i in range(7):
            a = math.pi * (0.1 + 0.8 * i / 6)
            r.part("cube", 0, -math.sin(a) * 0.3, math.cos(a) * 0.42, 0.08, 0.1, 0.14, SILVER,
                   rx=a - math.pi / 2)  # fmt: skip
    r.part("cube", -0.72, spring + 0.1, 0, 0.5, 0.2, 2 * half + 0.04, dark, tex="moonstone")  # the lintel
    for i in range(3):  # its three sockets: dark until the three sigils are taken, then shining
        z = (i - 1) * 0.5
        r.part("cyl", -0.45, spring + 0.1, z, 0.22, 0.06, 0.22, SILVER_DARK, rz=math.pi / 2)
        r.part("cyl", -0.42, spring + 0.1, z, 0.13, 0.06, 0.13, MOON_GLOW if lit else VOID, rz=math.pi / 2,
               glow=lit)  # fmt: skip
    for k in range(6):  # the tympanum between lintel and arch
        h = 0.3 + k * 0.24
        w = math.sqrt(max(radius * radius - h * h, 0.0)) - half + 0.05
        if w > 0:
            r.part("cube", -0.86, spring + h + 0.12, 0, 0.2, 0.24, 2 * w, stone, tex="moonstone")
    swing = opened * 1.4
    for side in (-1, 1):  # the leaves of silver tracery, swinging out
        with r.at(-0.62, 0, side * half, ry=-side * swing), r.at(0, 0, -side * half / 2):
            for k in range(3):  # mullions
                z = -0.3 + k * 0.3
                r.part("cube", 0, (spring - 0.1) / 2, z, 0.05, spring - 0.1, 0.05, SILVER)
            for y in (0.3, 1.6, 2.9, spring - 0.15):  # rails across them
                r.part("cube", 0, y, 0, 0.05, 0.06, half - 0.02, SILVER)
            for i in range(5):  # a crescent in its tracery
                a = math.pi * (0.15 + 0.7 * i / 4)
                r.part("cube", 0, 2.25 - math.sin(a) * 0.22, math.cos(a) * 0.3, 0.03, 0.06, 0.08, SILVER_DARK,
                       rx=a - math.pi / 2)  # fmt: skip
            r.part("cube", 0, 1.0, 0, 0.02, 1.2, half - 0.08, (140, 156, 196), tex="moon_glass")  # glass
    r.part("cube", -0.45, 0.04, 0, 0.9, 0.08, 2 * half + 0.6, dark, tex="moonstone")  # the threshold
    if lit:  # moonlight and frost pouring out through it
        for k in range(3):  # thin veils of it, fainter the further out they drift
            r.part("cube", -0.85 + 0.25 * k, 0.9 + 0.3 * k, 0, 0.04, 1.8 + 0.6 * k, 2 * half - 0.2,
                   _dim((120, 136, 184), 1 - 0.25 * k), tex="mist", glow=True)  # fmt: skip
        for i in range(5):
            u = (t * 0.3 + i / 5) % 1.0
            r.part("cube", -0.6 + 1.6 * u, 0.3 + 2.2 * ((i * 0.37) % 1.0), (i - 2) * 0.32, 0.06, 0.06, 0.06,
                   FROST, glow=True)  # fmt: skip


# --- the city's dressing --------------------------------------------------------------------------


def moon_lamp(r, seed):
    """A street lamp of Vesperholm: a slender fluted post of silvered iron on a stepped moonstone foot,
    a crook at its head from which hangs a lantern of moon-glass with cold moonlight in it."""
    r.part("cube", 0, 0.12, 0, 0.5, 0.24, 0.5, MOONSTONE_DARK, tex="moonstone")
    r.part("cube", 0, 0.3, 0, 0.36, 0.12, 0.36, MOONSTONE, tex="moonstone")
    r.part("cyl", 0, 1.6, 0, 0.1, 2.6, 0.1, SILVER_DARK)  # the post
    for y in (0.6, 1.8, 2.8):
        r.part("cyl", 0, y, 0, 0.14, 0.05, 0.14, SILVER)  # its collars
    _bar(r, (0, 2.85, 0), (0.42, 3.0, 0), 0.05, SILVER_DARK)  # the crook
    _bar(r, (0.42, 3.0, 0), (0.48, 2.86, 0), 0.04, SILVER_DARK)
    with r.at(0.48, 2.58, 0, ry=seed * 0.3):
        r.part("cube", 0, 0, 0, 0.26, 0.36, 0.26, (176, 196, 236), tex="moon_glass", glow=True)
        r.part("sphere", 0, 0, 0, 0.12, 0.16, 0.12, MOON_GLOW, glow=True)
        r.part("cone", 0, 0.24, 0, 0.32, 0.14, 0.32, SILVER)
        r.part("cube", 0, -0.2, 0, 0.3, 0.04, 0.3, SILVER)


def veiled_statue(r, seed):
    """A statue of one of the Duchess's handmaids on a moonstone plinth: a tall veiled woman in a long
    robe, both hands raising a crescent to the sky; frost has gathered in the folds."""
    stone, dark = _dim(MOONSTONE, 1.12), MOONSTONE_DARK
    r.part("cube", 0, 0.4, 0, 1.0, 0.8, 1.0, dark, tex="moonstone")  # the plinth
    r.part("cube", 0, 0.84, 0, 1.1, 0.08, 1.1, stone, tex="moonstone")
    r.part("cube", 0.51, 0.45, 0, 0.02, 0.24, 0.6, (90, 96, 116))  # a carved panel on its face
    with r.at(0, 0.88, 0, ry=(seed % 4) * 0.2 - 0.3):
        r.part("cone", 0, 1.0, 0, 0.7, 2.0, 0.66, stone, tex="moonstone")  # the robe
        r.part("cube", -0.04, 1.75, 0, 0.3, 0.42, 0.5, stone, tex="moonstone")  # the shoulders
        r.part("sphere", 0.02, 2.1, 0, 0.18, 0.24, 0.18, stone)  # the veiled head, tipped back
        r.part("cone", -0.04, 1.8, 0, 0.32, 0.7, 0.36, _dim(stone, 0.95))  # the veil falling
        for side in (-1, 1):  # the arms raised to the crescent
            _bar(r, (0, 1.85, side * 0.2), (0.12, 2.4, side * 0.14), 0.1, stone)
            _bar(r, (0.12, 2.4, side * 0.14), (0.1, 2.75, side * 0.1), 0.08, stone)
        with r.at(0.1, 2.95, 0):
            for i in range(7):  # the crescent, horns up
                a = math.pi * (0.1 + 0.8 * i / 6)
                r.part("cube", 0, -math.sin(a) * 0.22, math.cos(a) * 0.3, 0.08, 0.08, 0.1, SILVER,
                       rx=a - math.pi / 2)  # fmt: skip
        for z in (-0.2, 0.0, 0.2):  # frost in the robe's folds
            r.part("cube", 0.3, 0.6, z, 0.04, 1.0, 0.04, FROST)


def silver_tree(r, seed):
    """A tree of the Duchess's gardens, grown pale in the endless moonlight: a slender silver-grey trunk
    forking into crooked limbs, hung with clusters of white blossom that never falls."""
    bark, blossom = (176, 178, 190), (232, 236, 246)
    lean = ((seed % 5) - 2) * 0.04
    with r.at(0, 0, 0, rz=lean):
        r.part("cyl", 0, 1.2, 0, 0.26, 2.4, 0.26, bark, tex="bark")
        r.part("cone", 0, 0.2, 0, 0.5, 0.4, 0.5, _dim(bark, 0.85), tex="bark")  # its root flare
        for i in range(5):  # the limbs
            a = i * 1.26 + seed * 0.7
            out = 0.7 + 0.2 * (i % 2)
            tip = (math.cos(a) * out, 2.9 + 0.3 * (i % 3), math.sin(a) * out)
            _bar(r, (0, 2.1 + 0.1 * i, 0), tip, 0.1, bark)
            for j in range(2):  # its blossom
                r.part("sphere", tip[0] * (1 + 0.15 * j), tip[1] + 0.1 + 0.15 * j, tip[2] * (1 + 0.15 * j),
                       0.5 - 0.1 * j, 0.36, 0.5 - 0.1 * j, _dim(blossom, 1 - 0.06 * j))  # fmt: skip
        r.part("sphere", 0, 3.3, 0, 0.8, 0.5, 0.8, blossom)  # the crown


def moon_window(r, seed):
    """A tall lancet window of frosted moon-glass in the wall behind (-X): a pointed head, a silver
    mullion and transoms, cold light shining through it."""
    r.part("cube", -0.95, 1.7, 0, 0.06, 2.6, 0.9, (150, 170, 214), tex="moon_glass", glow=True)
    for i in range(4):  # its pointed head
        a = math.pi * (0.1 + 0.8 * i / 3)
        r.part("cube", -0.95, 3.05 + math.sin(a) * 0.25, math.cos(a) * 0.36, 0.06, 0.2, 0.2,
               (150, 170, 214), tex="moon_glass", glow=True)  # fmt: skip
    r.part("cube", -0.9, 1.9, 0, 0.06, 2.9, 0.06, SILVER_DARK)  # the mullion
    for y in (1.0, 2.1):
        r.part("cube", -0.9, y, 0, 0.06, 0.06, 0.9, SILVER_DARK)  # the transoms
    for side in (-1, 1):
        r.part("cube", -0.88, 1.7, side * 0.52, 0.16, 2.8, 0.14, MOONSTONE, tex="moonstone")  # the jambs
    r.part("cube", -0.84, 0.36, 0, 0.24, 0.1, 1.2, MOONSTONE_DARK, tex="moonstone")  # the sill
    r.part("cube", -0.84, 3.42, 0, 0.2, 0.2, 0.3, MOONSTONE, tex="moonstone")  # its keystone


def moon_spire(r, seed, height=14.0):
    """One of the slender spires of Vesperholm's skyline, standing on a wall no one walks: a round
    tower of moonstone banded in silver slate, a gallery of pointed windows near its top lit by the
    moon from within, a steep conical roof and a silver crescent on its finial."""
    radius = 1.0 + (seed % 3) * 0.15
    r.part("cyl", 0, height / 2, 0, radius * 2, height, radius * 2, MOONSTONE, tex="moonstone")
    for k in range(3):  # bands of silver slate up it
        y = height * (0.3 + 0.25 * k)
        r.part("cyl", 0, y, 0, radius * 2 + 0.12, 0.25, radius * 2 + 0.12, SILVER_DARK, tex="silver_slate")
    for i in range(6):  # the gallery's pointed windows, lit within
        a = i * math.pi / 3 + seed
        x, z = math.cos(a) * (radius - 0.02), math.sin(a) * (radius - 0.02)
        r.part("cube", x, height - 1.6, z, 0.12, 1.0, 0.36, (150, 170, 214), ry=-a, glow=True)
    r.part(
        "cyl", 0, height + 0.15, 0, radius * 2 + 0.4, 0.3, radius * 2 + 0.4, MOONSTONE_DARK, tex="moonstone"
    )
    roof = 4.0 + (seed % 2) * 1.5
    r.part("cone", 0, height + 0.3 + roof / 2, 0, radius * 2.2, roof, radius * 2.2, (96, 104, 124),
           tex="silver_slate")  # fmt: skip
    top = height + 0.3 + roof
    r.part("cyl", 0, top + 0.3, 0, 0.08, 0.6, 0.08, SILVER)
    with r.at(0, top + 0.8, 0):  # the crescent finial
        for i in range(5):
            a = math.pi * (0.1 + 0.8 * i / 4)
            r.part(
                "cube", 0, -math.sin(a) * 0.22, math.cos(a) * 0.3, 0.06, 0.08, 0.1, SILVER, rx=a - math.pi / 2
            )
