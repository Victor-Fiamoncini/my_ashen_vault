"""Original low-poly models assembled from primitives. All face +X."""

import math

from ashen_vault.player.items import Items

BONE = (214, 204, 178)
RUST = (120, 70, 44)
IRON = (92, 92, 98)
ASH = (96, 92, 88)
EMBER = (255, 140, 50)
WHITE = (255, 255, 255)
SKIN = (196, 158, 120)


def enemy(r, e):
    t = e.anim_t
    fn = {
        "bone_walker": bone_walker,
        "mire_slime": mire_slime,
        "cinder_wisp": cinder_wisp,
        "ashen_warden": ashen_warden,
        "mimic": mimic,
    }.get(e.type.id)
    if fn:
        fn(r, e, t)


def strike_angle(e):
    """Arm swing for melee enemies: raised during windup, slammed down on attack."""
    if e.state == "windup":
        return -2.2 * min(e.state_t / e.type.windup, 1)
    if e.state == "attack":
        return -2.2 + 3.0 * min(e.state_t / 0.2, 1)
    if e.state == "recover":
        return 0.8 * (1 - min(e.state_t / e.type.recover, 1))
    return 0


def walk_cycle(e, t):
    return math.sin(t * 7) * 0.5 if e.state in ("chase", "idle") else 0


def bone_walker(r, e, t):
    swing = walk_cycle(e, t)
    hit = strike_angle(e)
    lean = -0.3 if e.state == "hurt" else 0
    with r.at(0, 0, 0, rz=lean):
        for side, a in ((-0.14, swing), (0.14, -swing)):
            with r.at(0, 0.9, side, rz=a):
                r.part("cube", 0, -0.22, 0, 0.08, 0.45, 0.08, BONE)
                r.part("cube", 0, -0.66, 0, 0.07, 0.45, 0.07, BONE)
                r.part("cube", 0.06, -0.88, 0, 0.18, 0.05, 0.1, BONE)
        r.part("cube", 0, 0.95, 0, 0.18, 0.12, 0.34, BONE)
        r.part("cyl", 0, 1.18, 0, 0.08, 0.4, 0.08, BONE)
        for i in range(4):
            r.part("cube", 0.02, 1.08 + i * 0.1, 0, 0.16, 0.03, 0.36 - i * 0.02, BONE)
        r.part("cube", 0, 1.42, 0, 0.14, 0.06, 0.46, BONE)
        with r.at(0.02, 1.6, 0, rz=math.sin(t * 2) * 0.1):
            r.part("sphere", 0, 0, 0, 0.26, 0.28, 0.24, BONE)
            r.part("cube", 0.11, -0.03, -0.05, 0.05, 0.06, 0.06, (30, 10, 10))
            r.part("cube", 0.11, -0.03, 0.05, 0.05, 0.06, 0.06, (30, 10, 10))
            r.part("cube", 0.08, -0.15, 0, 0.12, 0.06, 0.16, BONE)
        with r.at(0, 1.4, -0.27, rz=swing * 0.6):
            r.part("cube", 0, -0.3, 0, 0.06, 0.6, 0.06, BONE)
        with r.at(0, 1.4, 0.27, rz=hit):
            r.part("cube", 0, -0.3, 0, 0.06, 0.6, 0.06, BONE)
            with r.at(0.05, -0.6, 0, rz=1.4):
                r.part("cube", 0.4, 0, 0, 0.8, 0.07, 0.03, RUST)
                r.part("cube", 0.0, 0, 0, 0.05, 0.05, 0.2, IRON)


def mire_slime(r, e, t):
    squash = 1 + math.sin(t * (9 if e.state == "chase" else 4)) * 0.12
    if e.state == "windup":
        squash = 1.35
    if e.state == "attack":
        squash = 0.7
    green = (200, 220, 160) if e.state == "hurt" else (70, 120, 60)
    r.part("sphere", 0, 0.32 / squash, 0, 0.95 * squash, 0.7 / squash, 0.95 * squash, green)
    r.part("sphere", 0.05, 0.14, 0, 1.05 * squash, 0.28, 1.05 * squash, (50, 90, 44))
    r.part("sphere", 0.3, 0.45 / squash, -0.14, 0.12, 0.12, 0.12, (230, 220, 120))
    r.part("sphere", 0.3, 0.45 / squash, 0.14, 0.12, 0.12, 0.12, (230, 220, 120))


def cinder_wisp(r, e, t):
    bob = math.sin(t * 3) * 0.15
    glow = (255, 230, 140) if e.state == "windup" else EMBER
    with r.at(0, e.type.hover + bob, 0):
        r.part("sphere", 0, 0, 0, 0.45, 0.45, 0.45, glow)
        r.part("sphere", 0, 0, 0, 0.62, 0.3, 0.62, (180, 60, 30))
        for i in range(3):
            a = t * 4 + i * 2.1
            r.part(
                "cube",
                math.cos(a) * 0.5,
                math.sin(t * 5 + i) * 0.15,
                math.sin(a) * 0.5,
                0.1,
                0.1,
                0.1,
                (255, 200, 90),
                glow=True,
            )
        r.part("cone", 0, 0.42, 0, 0.3, 0.45, 0.3, (255, 120, 40), glow=True)


def ashen_warden(r, e, t):
    swing = walk_cycle(e, t) * 0.7
    hit = strike_angle(e)
    with r.at(0, 0, 0, s=1.35):
        for side, a in ((-0.18, swing), (0.18, -swing)):
            with r.at(0, 0.95, side, rz=a):
                r.part("cube", 0, -0.45, 0, 0.2, 0.9, 0.18, ASH)
                r.part("cube", 0.05, -0.92, 0, 0.32, 0.1, 0.2, (60, 58, 56))
        r.part("cube", 0, 1.0, 0, 0.36, 0.24, 0.5, (70, 66, 62))
        r.part("cube", 0, 1.35, 0, 0.4, 0.55, 0.62, ASH)
        r.part("cube", 0, 1.68, 0, 0.44, 0.14, 0.86, (76, 72, 68))
        with r.at(0.02, 1.88, 0):
            r.part("cube", 0, 0, 0, 0.3, 0.32, 0.28, (70, 66, 62))
            r.part("cube", 0.15, 0.02, 0, 0.02, 0.05, 0.2, EMBER, glow=True)
            r.part("cone", 0, 0.26, 0, 0.12, 0.3, 0.12, (60, 58, 56))
        with r.at(0, 1.6, -0.47):
            r.part("cube", 0, -0.35, 0, 0.16, 0.7, 0.16, ASH)
        with r.at(0, 1.6, 0.47, rz=hit):
            r.part("cube", 0, -0.35, 0, 0.16, 0.7, 0.16, ASH)
            with r.at(0.05, -0.72, 0, rz=1.45):
                r.part("cube", 0.6, 0, 0, 1.4, 0.08, 0.08, (60, 44, 30))
                r.part("cube", 1.2, 0.0, 0, 0.36, 0.5, 0.05, IRON)


def mimic(r, e, t):
    """A chest with teeth. Asleep it is a plain closed chest; awake it gapes, chews and scuttles."""
    if e.state == "dormant":
        chest(r, False)
        return
    gape = 0.9 + math.sin(t * 9) * 0.25
    if e.state == "windup":
        gape = 1.5
    elif e.state == "attack":
        gape = 0.15
    lunge = 0.35 if e.state == "attack" else 0.0
    step = math.sin(t * 14) * 0.08 if e.state == "chase" else 0.0
    with r.at(lunge, 0.18, 0):
        for lx, lz in ((0.2, 0.32), (0.2, -0.32), (-0.2, 0.32), (-0.2, -0.32)):
            sway = step if (lx > 0) == (lz > 0) else -step
            r.part("cube", lx + sway, -0.08, lz, 0.08, 0.3, 0.08, (60, 40, 34), rz=-0.3 if lx > 0 else 0.3)
        r.part("cube", 0, 0.25, 0, 0.6, 0.5, 0.9, WHITE, tex="wood_plank")
        r.part("cube", 0, 0.26, 0, 0.62, 0.06, 0.92, IRON)
        r.part("cube", 0.02, 0.46, 0, 0.5, 0.08, 0.78, (90, 14, 20))  # maw
        for i in range(6):
            r.part("cone", 0.28, 0.54, -0.35 + i * 0.14, 0.07, 0.16, 0.07, BONE)
        r.part("cube", 0.25, 0.5, 0, 0.5, 0.05, 0.16, (190, 50, 70), rz=-0.3 - gape * 0.2)  # tongue
        with r.at(-0.3, 0.5, 0, rz=gape):
            r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, WHITE, tex="wood_plank")
            for i in range(6):
                r.part("cone", 0.56, -0.05, -0.35 + i * 0.14, 0.07, 0.16, 0.07, BONE, rx=math.pi)
            r.part("sphere", 0.45, 0.18, -0.22, 0.1, 0.1, 0.1, (255, 200, 60), glow=True)
            r.part("sphere", 0.45, 0.18, 0.22, 0.1, 0.1, 0.1, (255, 200, 60), glow=True)


def npc(r, robe, skin=SKIN, hair=(70, 54, 40), t=0):
    sway = math.sin(t * 1.5) * 0.03
    with r.at(0, 0, 0, rz=sway):
        r.part("cyl", 0, 0.55, 0, 0.55, 1.1, 0.6, robe)
        r.part("cube", 0, 1.2, 0, 0.32, 0.35, 0.5, robe)
        r.part("cube", 0, 1.15, -0.3, 0.14, 0.5, 0.12, robe)
        r.part("cube", 0, 1.15, 0.3, 0.14, 0.5, 0.12, robe)
        r.part("sphere", 0, 1.55, 0, 0.3, 0.32, 0.28, skin)
        r.part("sphere", -0.03, 1.64, 0, 0.32, 0.18, 0.3, hair)
        r.part("cube", 0.14, 1.56, -0.06, 0.02, 0.04, 0.04, (20, 16, 14))
        r.part("cube", 0.14, 1.56, 0.06, 0.02, 0.04, 0.04, (20, 16, 14))


def chest(r, is_open):
    r.part("cube", 0, 0.25, 0, 0.6, 0.5, 0.9, WHITE, tex="wood_plank")
    r.part("cube", 0, 0.26, 0, 0.62, 0.06, 0.92, IRON)
    with r.at(-0.3, 0.5, 0, rz=1.9 if is_open else 0):
        r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, WHITE, tex="wood_plank")
    if not is_open:
        r.part("cube", 0.31, 0.42, 0, 0.04, 0.12, 0.1, (200, 170, 80))


def door(r, open_t, axis, tex="door_wood"):
    """Door slab spanning the tile; axis 'x' means it blocks movement along X."""
    lift = open_t * 2.4
    ry = 0 if axis == "x" else math.pi / 2
    with r.at(0, 0, 0, ry=ry):
        r.part("cube", 0, 1.25 + lift, 0, 0.18, 2.5, 2.0, WHITE, tex=tex)


def brazier(r, t):
    r.part("cyl", 0, 0.45, 0, 0.12, 0.9, 0.12, IRON)
    r.part("cyl", 0, 0.95, 0, 0.6, 0.2, 0.6, IRON)
    flicker = 1 + math.sin(t * 13) * 0.12
    r.part("cone", 0, 1.2, 0, 0.4 * flicker, 0.45 * flicker, 0.4 * flicker, (255, 150, 50), glow=True)
    r.part("cone", 0, 1.2, 0, 0.22, 0.6 * flicker, 0.22, (255, 230, 140), glow=True)


def torch(r, t):
    r.part("cyl", 0, 0.8, 0, 0.08, 1.6, 0.08, (80, 56, 36))
    flicker = 1 + math.sin(t * 11) * 0.15
    r.part("cone", 0, 1.72, 0, 0.2 * flicker, 0.3 * flicker, 0.2 * flicker, (255, 170, 60), glow=True)


def save_statue(r, t):
    r.part("cube", 0, 0.15, 0, 0.9, 0.3, 0.9, WHITE, tex="rough_stone")
    r.part("cube", 0, 0.9, 0, 0.5, 1.2, 0.5, WHITE, tex="rough_stone")
    with r.at(0, 1.75 + math.sin(t * 2) * 0.06, 0, ry=t):
        r.part("cube", 0, 0, 0, 0.3, 0.4, 0.3, (120, 200, 255), rx=0.6, rz=0.6, glow=True)


def lever(r, pulled):
    r.part("cube", 0, 0.5, 0, 0.3, 1.0, 0.3, WHITE, tex="rough_stone")
    with r.at(0.16, 0.8, 0, rz=-0.8 if pulled else 0.8):
        r.part("cube", 0, 0.3, 0, 0.06, 0.6, 0.06, IRON)
        r.part("sphere", 0, 0.62, 0, 0.12, 0.12, 0.12, (140, 30, 30))


def pickup(r, t):
    with r.at(0, 0.3 + math.sin(t * 3) * 0.05, 0, ry=t * 1.5):
        r.part("sphere", 0, 0, 0, 0.3, 0.26, 0.3, (130, 100, 70))
        r.part("cube", 0, 0.15, 0, 0.12, 0.1, 0.12, (200, 170, 80))


def well(r):
    for i in range(8):
        a = i * math.pi / 4
        r.part(
            "cube", math.cos(a) * 0.75, 0.4, math.sin(a) * 0.75, 0.3, 0.8, 0.62, WHITE, tex="cobble", ry=-a
        )
    r.part("cube", -0.85, 1.3, 0, 0.12, 1.8, 0.12, (90, 64, 40))
    r.part("cube", 0.85, 1.3, 0, 0.12, 1.8, 0.12, (90, 64, 40))
    r.part("cube", 0, 2.2, 0, 2.0, 0.12, 0.12, (90, 64, 40))
    r.part("cube", 0, 2.45, 0, 2.2, 0.08, 1.2, WHITE, tex="roof")
    r.part("cube", 0, 0.05, 0, 1.2, 0.05, 1.2, (10, 12, 14))


def tree(r, seed):
    h = 2.6 + (seed % 5) * 0.3
    r.part("cyl", 0, h * 0.35, 0, 0.32, h * 0.7, 0.32, (84, 60, 40))
    r.part("cone", 0, h * 0.75, 0, 2.4, h * 0.7, 2.4, (44, 74, 40))
    r.part("cone", 0, h * 1.1, 0, 1.7, h * 0.55, 1.7, (52, 86, 46))


def rope(r, t):
    with r.at(0, 3.2, 0, rz=math.sin(t * 0.8) * 0.04):
        r.part("cyl", 0, -1.6, 0, 0.07, 3.2, 0.07, (150, 120, 80))
        r.part("cube", 0, -3.0, 0, 0.16, 0.12, 0.16, (130, 100, 70))
    r.part("cyl", 0, 0.05, 0, 1.0, 0.1, 1.0, (40, 40, 44))


def bolt(r, rgb):
    r.part("sphere", 0, 0, 0, 0.3, 0.3, 0.3, rgb, glow=True)
    r.part("sphere", 0, 0, 0, 0.5, 0.18, 0.18, (255, 230, 160), glow=True)


# --- dungeon dressing --------------------------------------------------------

DARK_IRON = (58, 56, 60)


def barrel(r, seed, broken=False):
    """A squat banded cask; the seed nudges its spot, height and lean so rows don't look cloned.
    A broken one is a ring of staves and a fallen hoop."""
    h = 0.95 + (seed % 3) * 0.08
    ox = ((seed * 37) % 7 - 3) * 0.08
    oz = ((seed * 53) % 7 - 3) * 0.08
    if broken:
        _barrel_wreck(r, ox, oz, seed)
        return
    with r.at(ox, 0, oz, ry=seed * 0.7, rz=0.04 if seed % 4 == 0 else 0):
        r.part("cyl", 0, h / 2, 0, 0.78, h, 0.78, WHITE, tex="wood_plank")
        r.part("cyl", 0, h / 2, 0, 0.86, h * 0.55, 0.86, WHITE, tex="wood_plank")
        for y in (0.12, h - 0.12):
            r.part("cyl", 0, y, 0, 0.82, 0.06, 0.82, DARK_IRON)
        r.part("cyl", 0, h + 0.01, 0, 0.7, 0.02, 0.7, (70, 48, 30))
    if seed % 3 == 0:  # a second, smaller cask beside it
        with r.at(ox - 0.55, 0, oz + 0.45, ry=seed):
            r.part("cyl", 0, 0.35, 0, 0.55, 0.7, 0.55, WHITE, tex="wood_plank")
            r.part("cyl", 0, 0.35, 0, 0.6, 0.05, 0.6, DARK_IRON)


def _barrel_wreck(r, ox, oz, seed):
    with r.at(ox, 0, oz, ry=seed * 0.7):
        r.part("cyl", 0, 0.03, 0, 0.84, 0.06, 0.84, DARK_IRON, rx=0.08)
        r.part("cyl", 0, 0.03, 0, 0.66, 0.05, 0.66, (70, 48, 30))
        for i in range(7):
            a = i * 0.9 + seed
            d = 0.45 + (i % 3) * 0.12
            r.part(
                "cube",
                math.cos(a) * d,
                0.04,
                math.sin(a) * d,
                0.5 - (i % 2) * 0.15,
                0.04,
                0.12,
                WHITE,
                tex="wood_plank",
                ry=a * 1.3,
            )
        r.part("cube", 0.25, 0.18, -0.2, 0.06, 0.36, 0.12, WHITE, tex="wood_plank", rz=0.3)


def secret_wall(r, height, open_t):
    """An illusory wall: a full tile of brick that matches the real walls. Struck, it sinks and fades."""
    if open_t >= 1.0:
        return
    k = 1.0 - open_t
    h = height * k
    r.part("cube", 0, h / 2, 0, 2.0 * (0.6 + 0.4 * k), h, 2.0 * (0.6 + 0.4 * k), WHITE, tex="stone_brick")


def crumble_slab(r, shake, drop, rise, t):
    """A cracked slab over a pit. It trembles before it falls, plunges, and grows back."""
    if drop >= 4.0:
        return
    jx = math.sin(t * 61) * 0.05 * shake
    jz = math.cos(t * 47) * 0.05 * shake
    s = 1.0 - drop / 5.0
    y = -drop - (1.0 - rise) * 0.6
    with r.at(jx, y, jz, rx=drop * 0.12, rz=drop * 0.08, s=max(s, 0.1) * (0.5 + 0.5 * rise)):
        r.part("cube", 0, -0.2, 0, 1.96, 0.4, 1.96, WHITE, tex="flagstone")
        r.part("cube", 0.3, 0.005, -0.1, 1.2, 0.01, 0.04, (30, 26, 24), ry=0.6)  # cracks
        r.part("cube", -0.4, 0.005, 0.3, 0.8, 0.01, 0.04, (30, 26, 24), ry=-0.9)
        r.part("cone", 0, -0.7, 0, 1.2, 0.6, 1.2, WHITE, tex="rough_stone", rx=math.pi)


def crate(r, seed, broken=False):
    """A plank crate with dark battens; sometimes a smaller one stacked on top. Broken, it is a heap of
    split planks with the lid lying askew."""
    with r.at(((seed * 29) % 5 - 2) * 0.1, 0, ((seed * 41) % 5 - 2) * 0.1, ry=(seed % 5) * 0.3):
        if broken:
            for i in range(6):
                a = i * 1.1 + seed
                d = 0.2 + (i % 3) * 0.15
                r.part(
                    "cube", math.cos(a) * d, 0.04 + (i % 2) * 0.05, math.sin(a) * d,
                    0.8 - (i % 3) * 0.15, 0.05, 0.16, WHITE, tex="wood_plank", ry=a * 1.4, rz=(i % 2) * 0.15,
                )  # fmt: skip
            r.part("cube", -0.15, 0.12, 0.1, 0.85, 0.06, 0.85, WHITE, tex="wood_plank", ry=0.5, rz=0.2)
            return
        _crate_box(r, 0.9)
        if seed % 2 == 0:
            with r.at(0.05, 0.9, -0.05, ry=0.5):
                _crate_box(r, 0.6)


def _crate_box(r, s):
    r.part("cube", 0, s / 2, 0, s, s, s, WHITE, tex="wood_plank")
    edge = (60, 40, 26)
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * s / 2, s / 2, dz * s / 2, 0.08, s + 0.02, 0.08, edge)
    r.part("cube", 0, s / 2, 0, s + 0.02, 0.08, s + 0.02, edge)


def chains(r, t, ceil_h):
    """Two lengths of chain hanging from the ceiling, swaying slowly; one ends in a hook."""
    for side, phase, ending in ((-0.35, 0.0, "hook"), (0.3, 1.7, "cuff")):
        links = max(int((ceil_h - 1.2) / 0.16), 4)
        sway = math.sin(t * 0.9 + phase) * 0.05
        with r.at(0, ceil_h, side, rx=sway, rz=sway * 0.6):
            for i in range(links):
                ry = 0 if i % 2 == 0 else math.pi / 2
                r.part("cube", 0, -0.08 - i * 0.16, 0, 0.03, 0.18, 0.09, IRON, ry=ry)
            end = -0.08 - links * 0.16
            if ending == "hook":
                r.part("cube", 0, end - 0.05, 0, 0.04, 0.16, 0.04, DARK_IRON)
                r.part("cube", 0.07, end - 0.13, 0, 0.16, 0.04, 0.04, DARK_IRON)
                r.part("cube", 0.14, end - 0.08, 0, 0.04, 0.12, 0.04, DARK_IRON)
            else:
                r.part("cyl", 0, end - 0.08, 0, 0.2, 0.08, 0.2, DARK_IRON, rx=math.pi / 2)


def bones(r, seed):
    """A skull and a scatter of long bones on the floor."""
    with r.at(0, 0, 0, ry=seed * 0.9):
        with r.at(0.3, 0.12, -0.2, ry=seed * 0.4, rz=0.3):
            r.part("sphere", 0, 0, 0, 0.24, 0.22, 0.22, BONE)
            r.part("cube", 0.09, -0.02, -0.05, 0.05, 0.05, 0.05, (30, 22, 18))
            r.part("cube", 0.09, -0.02, 0.05, 0.05, 0.05, 0.05, (30, 22, 18))
        for i in range(3 + seed % 3):
            a = i * 2.3 + seed
            x = math.cos(a) * 0.35
            z = math.sin(a) * 0.35
            r.part("cube", x, 0.04, z, 0.5, 0.06, 0.06, BONE, ry=a * 1.7)
            r.part(
                "sphere",
                x + math.cos(a * 1.7) * 0.25,
                0.05,
                z - math.sin(a * 1.7) * 0.25,
                0.1,
                0.1,
                0.1,
                BONE,
            )
        r.part("cube", -0.25, 0.05, 0.25, 0.3, 0.05, 0.28, (200, 190, 165), ry=0.4)  # ribs


def shackles(r):
    """Iron manacles pinned to the wall; the prop faces +X, so the wall is at -X."""
    r.part("cube", -0.95, 1.7, 0, 0.06, 0.3, 0.9, DARK_IRON)
    for side in (-0.3, 0.3):
        for i in range(4):
            ry = 0 if i % 2 == 0 else math.pi / 2
            r.part("cube", -0.9, 1.55 - i * 0.13, side, 0.03, 0.15, 0.08, IRON, ry=ry)
        r.part("cyl", -0.86, 1.0, side, 0.18, 0.08, 0.18, IRON, rz=math.pi / 2)


def spikes(r, height):
    """A floor plate with a grid of spikes raised by `height` (0..1)."""
    r.part("cube", 0, 0.02, 0, 1.9, 0.04, 1.9, DARK_IRON)
    for i in range(5):
        for j in range(5):
            r.part("cube", -0.72 + i * 0.36, 0.045, -0.72 + j * 0.36, 0.12, 0.01, 0.12, (20, 18, 18))
    if height <= 0:
        return
    tall = 0.9 * height
    for i in range(5):
        for j in range(5):
            jitter = ((i * 7 + j * 3) % 4) * 0.04
            r.part("cone", -0.72 + i * 0.36, tall / 2, -0.72 + j * 0.36, 0.11, tall + jitter, 0.11, STEEL)


def pendulum(r, angle, length):
    """A crescent blade on a rod. The origin is the ceiling pivot; it swings along +X."""
    r.part("cube", 0, -0.08, 0, 0.5, 0.16, 0.5, DARK_IRON)
    with r.at(0, 0, 0, rz=angle):
        r.part("cube", 0, -length / 2, 0, 0.07, length, 0.07, IRON)
        with r.at(0, -length, 0):  # a broad crescent spanning the corridor, edge leading the swing
            r.part("cube", 0, 0.08, 0, 0.14, 0.3, 0.4, DARK_IRON)
            r.part("cube", 0, -0.1, 0, 0.06, 0.26, 1.3, STEEL)
            r.part("cube", 0, 0.02, -0.75, 0.06, 0.18, 0.4, STEEL, rx=-0.5)
            r.part("cube", 0, 0.02, 0.75, 0.06, 0.18, 0.4, STEEL, rx=0.5)
            r.part("cube", 0, -0.24, 0, 0.07, 0.04, 1.25, (235, 235, 245))


# Iron maiden body profile, feet to shoulders: (bottom, top, width across).
MAIDEN_PROFILE = (
    (0.25, 0.65, 0.6),
    (0.65, 1.15, 0.7),
    (1.15, 1.55, 0.8),
    (1.55, 1.95, 0.9),
    (1.95, 2.2, 1.0),
)
MAIDEN_IRON = (66, 62, 64)
MAIDEN_DARK = (40, 36, 38)


def iron_maiden(r, door):
    """A figure-shaped iron casket on a stone plinth: flared shoulders, a sculpted face, and two spiked
    doors that part down the middle and swing outward (door 0..1). Faces +X."""
    r.part("cube", 0, 0.12, 0, 1.15, 0.24, 1.35, WHITE, tex="rough_stone")
    r.part("cube", 0, 0.255, 0, 1.0, 0.03, 1.2, (70, 64, 58))
    # Back shell, hollow and dark inside, its inner wall bristling with spikes.
    for y0, y1, w in MAIDEN_PROFILE:
        h = y1 - y0
        r.part("cyl", -0.14, (y0 + y1) / 2, 0, 0.6, h, w, MAIDEN_IRON)
        r.part("cube", 0.02, (y0 + y1) / 2, 0, 0.3, h, w * 0.78, (20, 14, 14))
        for z in (-w * 0.2, w * 0.2):
            r.part("cone", -0.02, (y0 + y1) / 2, z, 0.07, 0.22, 0.07, STEEL, rz=-math.pi / 2)
    r.part("cyl", -0.14, 2.26, 0, 0.45, 0.12, 0.5, MAIDEN_IRON)  # neck
    with r.at(-0.12, 2.6, 0):  # the head, with its stern iron face
        r.part("sphere", 0, 0, 0, 0.55, 0.62, 0.56, MAIDEN_IRON)
        r.part("cone", -0.04, 0.38, 0, 0.42, 0.28, 0.46, MAIDEN_DARK)  # coif peak
        r.part("cube", 0.24, 0.08, 0, 0.06, 0.06, 0.36, MAIDEN_DARK)  # brow
        r.part("cube", 0.27, -0.03, 0, 0.06, 0.16, 0.06, (88, 82, 80))  # nose ridge
        for z in (-0.1, 0.1):
            r.part("cube", 0.255, 0.02, z, 0.03, 0.03, 0.09, (10, 8, 8))  # eye slits
        r.part("cube", 0.25, -0.15, 0, 0.03, 0.025, 0.16, (10, 8, 8))  # mouth
        r.part("cube", 0.22, -0.24, 0, 0.06, 0.05, 0.22, (100, 90, 84))  # chin
    for side in (-1, 1):  # the two doors: hinged at the outer edges, meeting down the middle
        with r.at(0.17, 0, side * 0.5, ry=-side * door * 1.75):
            _maiden_door(r, side)
    if door == 0:  # a chain and padlock bind the doors shut
        r.part("cube", 0.25, 1.62, 0, 0.04, 0.05, 0.9, IRON)
        r.part("cube", 0.28, 1.5, 0, 0.08, 0.16, 0.12, (110, 90, 50))
        r.part("cube", 0.28, 1.6, 0, 0.04, 0.08, 0.07, IRON)


def _maiden_door(r, side):
    """One door half, in the hinge's frame: it reaches from the hinge (z=0) toward the middle."""
    inward = -side
    for i, (y0, y1, w) in enumerate(MAIDEN_PROFILE):
        h = y1 - y0
        half = w / 2
        zc = inward * (0.5 - half / 2)  # the panel's middle, measured from the hinge line
        r.part("cube", 0, (y0 + y1) / 2, zc, 0.08, h + 0.01, half, MAIDEN_IRON)
        r.part("cube", 0.05, y1 - 0.03, zc, 0.04, 0.05, half + 0.01, RUST)  # band
        r.part("sphere", 0.07, y1 - 0.03, zc + inward * half * 0.3, 0.06, 0.06, 0.06, (140, 120, 100))
        if i % 2 == 0:  # rust weeping down from the band
            r.part("cube", 0.045, (y0 + y1) / 2, zc - inward * half * 0.2, 0.01, h * 0.8, 0.05, RUST)
        r.part("cone", -0.12, (y0 + y1) / 2, zc, 0.06, 0.2, 0.06, STEEL, rz=math.pi / 2)  # inner spike
    for y in (0.9, 2.05):  # hinge knuckles at the outer edge
        r.part("cyl", 0, y, inward * 0.02, 0.09, 0.2, 0.09, MAIDEN_DARK)


FLAME = (255, 170, 60)
FLAME_CORE = (255, 235, 150)
STONE = (128, 124, 118)
CLOTH_RED = (120, 30, 30)


def _flame(r, x, y, z, size, t):
    flicker = 1 + math.sin(t * 11 + x * 7 + z * 5) * 0.15
    r.part("cone", x, y, z, size * flicker, size * 1.5 * flicker, size * flicker, FLAME, glow=True)
    r.part("cone", x, y + 0.02, z, size * 0.5, size * 1.9 * flicker, size * 0.5, FLAME_CORE, glow=True)


def sconce(r, t):
    """A torch held out from the wall (at local -X) by an iron bracket."""
    r.part("cube", -0.97, 1.7, 0, 0.05, 0.4, 0.22, DARK_IRON)  # wall plate
    r.part("cube", -0.86, 1.62, 0, 0.22, 0.04, 0.05, DARK_IRON, rz=0.5)  # bracket arm
    with r.at(-0.74, 1.66, 0, rz=-0.35):
        r.part("cyl", 0, 0.12, 0, 0.07, 0.5, 0.07, (80, 56, 36))
        r.part("cyl", 0, 0.36, 0, 0.13, 0.08, 0.13, DARK_IRON)  # cup
        _flame(r, 0, 0.5, 0, 0.18, t)


def banner(r, t, seed):
    """A tattered banner hung from a pole on the wall at local -X."""
    sway = math.sin(t * 0.7) * 0.03
    r.part("cyl", -0.9, 2.55, 0, 0.05, 1.0, 0.05, (70, 50, 32), rx=math.pi / 2)
    for end in (-0.5, 0.5):
        r.part("sphere", -0.9, 2.55, end, 0.08, 0.08, 0.08, BRASS)
    cloth = CLOTH_RED if seed % 2 == 0 else (40, 50, 80)
    with r.at(-0.9, 2.5, 0, rz=sway):
        r.part("cube", 0, -0.75, 0, 0.03, 1.5, 0.8, cloth)
        for i, z in enumerate((-0.3, -0.1, 0.1, 0.3)):  # ragged hem
            r.part("cube", 0, -1.55 - (i % 2) * 0.08, z, 0.03, 0.2 + (i % 2) * 0.12, 0.16, cloth)
        r.part("cube", 0.02, -0.6, 0, 0.02, 0.5, 0.08, (200, 180, 140))  # pale sigil: a sword
        r.part("cube", 0.02, -0.5, 0, 0.02, 0.06, 0.3, (200, 180, 140))
        r.part("sphere", 0.02, -0.98, 0, 0.02, 0.16, 0.16, (200, 180, 140))


def rack(r, seed):
    """A weapon rack against the wall at local -X: spears and a sword leaning in a wooden frame."""
    wood = (84, 58, 36)
    for z in (-0.6, 0.6):
        r.part("cube", -0.75, 0.75, z, 0.1, 1.5, 0.1, wood)
    r.part("cube", -0.75, 1.35, 0, 0.1, 0.08, 1.3, wood)
    r.part("cube", -0.6, 0.25, 0, 0.3, 0.08, 1.3, wood)
    for z in (-0.4, -0.15, 0.1):
        with r.at(-0.62, 0.95, z, rz=0.12):
            r.part("cube", 0, 0, 0, 0.04, 1.6, 0.04, wood)
            r.part("cone", 0, 0.9, 0, 0.08, 0.25, 0.04, STEEL)
    if seed % 2 == 0:
        with r.at(-0.62, 0.6, 0.4, rz=0.1):
            sword(r, "rusted_sword")


def table(r, t, seed):
    """A rough plank table with a guttering candle and a plate or tankard."""
    wood = (96, 66, 40)
    r.part("cube", 0, 0.78, 0, 1.0, 0.08, 1.5, WHITE, tex="wood_plank")
    for dx, dz in ((0.4, 0.62), (0.4, -0.62), (-0.4, 0.62), (-0.4, -0.62)):
        r.part("cube", dx, 0.37, dz, 0.08, 0.74, 0.08, wood)
    r.part("cyl", 0.1, 0.88, -0.4, 0.08, 0.14, 0.08, (220, 210, 180))
    _flame(r, 0.1, 0.98, -0.4, 0.05, t)
    if seed % 2:
        r.part("cyl", -0.1, 0.83, 0.2, 0.36, 0.03, 0.36, (150, 150, 156))  # plate
        r.part("sphere", -0.1, 0.87, 0.2, 0.14, 0.08, 0.14, (110, 80, 40))  # stale bread
    else:
        r.part("cyl", -0.15, 0.9, 0.25, 0.16, 0.2, 0.16, (110, 90, 60))  # tankard
    r.part("cube", 0.6, 0.45, 0.2, 0.36, 0.06, 0.36, WHITE, tex="wood_plank")  # a stool
    r.part("cube", 0.6, 0.22, 0.2, 0.06, 0.44, 0.06, wood)


def candles(r, t, seed):
    """A cluster of candles melted onto the floor."""
    r.part("cyl", 0, 0.02, 0, 0.6, 0.04, 0.5, (210, 200, 170))  # wax puddle
    for i in range(3 + seed % 3):
        a = i * 2.1 + seed
        d = 0.08 + (i % 3) * 0.1
        h = 0.18 + ((i * 5 + seed) % 4) * 0.08
        x, z = math.cos(a) * d, math.sin(a) * d
        r.part("cyl", x, h / 2, z, 0.07, h, 0.07, (225, 215, 185))
        _flame(r, x, h + 0.04, z, 0.04, t + i)


def rubble(r, seed):
    """Fallen masonry: a broken column drum and loose stones."""
    with r.at(0, 0, 0, ry=seed * 0.8):
        r.part("cyl", 0.2, 0.25, -0.1, 0.7, 0.5, 0.7, WHITE, tex="rough_stone", rz=1.5 if seed % 2 else 0)
        for i in range(5):
            a = i * 1.7 + seed
            s = 0.18 + (i % 3) * 0.1
            r.part(
                "cube", math.cos(a) * 0.55, s / 2, math.sin(a) * 0.55, s, s, s * 1.2, WHITE,
                tex="stone_brick", ry=a, rx=i * 0.3,
            )  # fmt: skip


def urn(r, seed, broken=False):
    """A clay pot; smashed, a few curved shards."""
    clay = (150, 92, 60) if seed % 2 else (126, 110, 90)
    if broken:
        for i in range(5):
            a = i * 1.3 + seed
            r.part("sphere", math.cos(a) * 0.3, 0.04, math.sin(a) * 0.3, 0.22, 0.06, 0.16, clay, ry=a)
        r.part("cyl", 0, 0.06, 0, 0.3, 0.12, 0.3, clay)
        return
    with r.at(((seed * 13) % 5 - 2) * 0.1, 0, ((seed * 17) % 5 - 2) * 0.1):
        r.part("sphere", 0, 0.35, 0, 0.6, 0.62, 0.6, clay)
        r.part("cyl", 0, 0.7, 0, 0.3, 0.16, 0.3, clay)
        r.part("cyl", 0, 0.79, 0, 0.38, 0.05, 0.38, clay)
        r.part("cyl", 0, 0.4, 0, 0.62, 0.05, 0.62, tuple(c - 30 for c in clay))  # painted band


def warden_altar(r, taken, t):
    """A stepped altar before a stone statue of the Ashen Warden, who offers a floating key above his
    cupped hands. Faces +X; the statue stands at the back of the tile."""
    r.part("cube", 0, 0.08, 0, 1.95, 0.16, 1.95, WHITE, tex="rough_stone")  # dais
    r.part("cube", -0.2, 0.24, 0, 1.5, 0.16, 1.6, WHITE, tex="rough_stone")
    # The altar block with a cloth runner and candles.
    r.part("cube", 0.45, 0.68, 0, 0.6, 0.72, 1.3, WHITE, tex="rough_stone")
    r.part("cube", 0.45, 1.05, 0, 0.7, 0.06, 1.4, WHITE, tex="rough_stone")
    r.part("cube", 0.45, 1.09, 0, 0.72, 0.02, 0.42, CLOTH_RED)
    r.part("cube", 0.8, 0.85, 0, 0.02, 0.5, 0.42, CLOTH_RED)
    for z in (-0.55, 0.55):
        r.part("cyl", 0.55, 1.2, z, 0.08, 0.22, 0.08, (225, 215, 185))
        _flame(r, 0.55, 1.34, z, 0.05, t + z)
    _warden_statue(r, taken, t)
    if not taken:  # the key hovers just above his offered hands
        bob = math.sin(t * 1.6) * 0.04
        with r.at(0.3, 2.02 + bob, 0, ry=t * 0.8):
            r.part("sphere", 0, 0, 0, 0.16, 0.16, 0.16, (255, 150, 60), glow=True)
            with r.at(0, 0, 0, s=0.32):
                key(r, (150, 150, 160), 1.9)


def _warden_statue(r, taken, t):
    stone = STONE
    dark = (96, 92, 88)
    with r.at(-0.55, 0.32, 0, s=1.1):
        r.part("cube", 0, 0.12, 0, 0.7, 0.24, 0.9, dark)  # plinth
        for side in (-0.16, 0.16):  # legs in greaves
            r.part("cube", 0, 0.6, side, 0.24, 0.75, 0.2, stone)
        r.part("cube", 0, 1.05, 0, 0.32, 0.24, 0.5, dark)  # belt
        r.part("cube", 0, 1.42, 0, 0.36, 0.55, 0.6, stone)  # breastplate
        for side in (-1, 1):
            r.part("sphere", 0, 1.72, side * 0.38, 0.36, 0.22, 0.32, dark)  # pauldrons
            with r.at(0.05, 1.62, side * 0.36, rz=0.9):  # arms reaching forward to offer the key
                r.part("cube", 0, -0.22, 0, 0.14, 0.45, 0.14, stone)
                with r.at(0, -0.42, 0, rz=0.6):
                    r.part("cube", 0, -0.18, 0, 0.12, 0.36, 0.12, stone)
                    r.part("cube", 0.02, -0.38, -side * 0.04, 0.16, 0.08, 0.14, stone)  # cupped hand
        with r.at(0, 1.92, 0):  # horned great helm
            r.part("cube", 0, 0.12, 0, 0.32, 0.36, 0.3, stone)
            r.part("cone", 0, 0.38, 0, 0.18, 0.2, 0.18, dark)
            for side in (-1, 1):
                r.part("cone", 0, 0.32, side * 0.24, 0.08, 0.36, 0.08, dark, rx=side * 0.9)
            eye = (30, 26, 24) if taken else (255, 120, 40)
            r.part("cube", 0.165, 0.14, 0, 0.02, 0.04, 0.2, eye, glow=not taken)
        # A greatsword planted point-down at his side.
        with r.at(0.12, 0.25, 0.62):
            r.part("cube", 0, 0.7, 0, 0.04, 1.4, 0.14, (110, 108, 106))
            r.part("cube", 0, 1.42, 0, 0.08, 0.06, 0.46, dark)
            r.part("cube", 0, 1.62, 0, 0.06, 0.34, 0.06, dark)


def spell_orb(r, id_, t):
    """Inventory preview for a known spell: a glowing orb in the spell's colour."""
    rgb = {"flame": (255, 120, 40), "mend": (120, 230, 140), "lumen": (210, 220, 255)}.get(id_, WHITE)
    pulse = 1 + math.sin(t * 3) * 0.06
    r.part("sphere", 0, 0, 0, 0.7 * pulse, 0.7 * pulse, 0.7 * pulse, rgb, glow=True)
    for i in range(3):
        a = t * 2 + i * 2.1
        r.part(
            "cube",
            math.cos(a) * 0.6,
            math.sin(t * 3 + i) * 0.2,
            math.sin(a) * 0.6,
            0.1,
            0.1,
            0.1,
            rgb,
            glow=True,
        )


HEAVY_CATEGORIES = ("greatsword", "hammer")


def _ease(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def _motion(motion, p):
    """Pose offsets (dx, dy, dz, rx, rz) for one attack motion at phase p (0..1)."""
    arc = math.sin(p * math.pi)
    if motion == "sweep":  # wide, flat, right to left
        return 0.0, arc * 0.05, 0.25 - _ease(p) * 0.8, 0.9 - _ease(p) * 2.4, -arc * 0.9
    if motion in ("chop", "slam"):  # raise, then bring it down hard
        big = motion == "slam"
        up = 0.8 if big else 0.55
        down = 2.2 if big else 1.75
        if p < 0.4:
            k = _ease(p / 0.4)
            return -0.05 * k, 0.12 * k, 0.0, 0.0, up * k
        k = _ease((p - 0.4) / 0.35)
        drop = -0.25 * k if big else -0.08 * k
        return 0.15 * k, 0.12 - 0.12 * k + drop, -0.1 * k, 0.0, up - (up + down) * k
    if motion == "thrust":  # level the blade, pull back, drive forward
        k = _ease(p / 0.3)
        push = -0.2 * k if p < 0.35 else -0.2 + _ease((p - 0.35) / 0.25) * 0.7 - max(p - 0.75, 0) * 1.6
        return push, 0.08 * k, -0.25 * k, 0.0, -1.15 * k
    if motion == "lash":  # a quick flick of the wrist
        return 0.0, arc * 0.1, -arc * 0.2, 0.25 - p * 1.2, -arc * 1.7
    # slash: the original diagonal cut
    return 0.0, arc * 0.12, 0.0, -(p - 0.3) * 1.6, -arc * 1.3


def weapon_view(r, player, bob):
    """First-person weapon. Camera-space: +X forward, +Y up, +Z right."""
    item = player.inventory.weapon_item()
    swing_t = player.swing_t
    phase = min(swing_t / player.swing_time, 1.0) if swing_t is not None else None
    charge = player.charge_frac if phase is None else 0.0
    if item.id == "fists":
        return fist_view(r, phase, bob, player.attack.motion, charge)
    heavy = item.category in HEAVY_CATEGORIES
    x, y, z = 0.9, (-0.62 if heavy else -0.5) + bob, 0.42 if heavy else 0.36
    rx, rz = 0.25, -0.35
    if phase is not None:
        dx, dy, dz, drx, drz = _motion(player.attack.motion, phase)
        x, y, z, rx, rz = x + dx, y + dy, z + dz, rx + drx, rz + drz
    elif charge > 0:  # drawing back for a heavy: raise it, with a tremble once it is ready
        k = _ease(charge)
        shake = math.sin(player.charge_t * 60) * 0.006 if charge >= 1 else 0.0
        x, y, z = x - 0.05 * k, y + 0.14 * k + shake, z - 0.04 * k
        rx, rz = rx + 0.4 * k, rz + 0.3 * k
    with r.at(x, y, z, rx=rx, ry=0.7, rz=rz, s=0.7):
        weapon(r, item.id, phase)


def fist_view(r, phase, bob, motion="jab", charge=0.0):
    """Bare-handed: a jab straight forward, or a hook from the right."""
    jab = math.sin(phase * math.pi) * 0.3 if phase is not None else 0.0
    side = 0.0
    if phase is not None and motion == "hook":
        side = 0.3 - _ease(phase) * 0.8
        jab *= 0.6
    pull = -0.1 * _ease(charge)
    with r.at(0.95 + jab + pull, -0.46 + bob + jab * 0.2, 0.34 - jab * 0.5 + side, ry=0.25, rz=0.2, s=0.6):
        r.part("cube", -0.25, -0.05, 0, 0.5, 0.13, 0.13, (96, 80, 60))
        r.part("cube", 0.05, 0, 0, 0.16, 0.15, 0.17, SKIN)
        r.part("cube", 0.12, 0.03, 0, 0.06, 0.08, 0.18, tuple(c - 20 for c in SKIN))
        r.part("cube", 0.04, -0.06, -0.09, 0.1, 0.05, 0.05, SKIN)


WOOD = (90, 60, 38)
LEATHER = (70, 46, 30)
BRASS = (150, 130, 80)
STEEL = (190, 190, 200)

# Rough length of each weapon model (grip to tip), used to fit previews.
WEAPON_LEN = {"bastard_sword": 1.4, "claymore": 1.85, "zweihander": 2.1, "katana": 1.35, "war_hammer": 1.5}


def weapon(r, item_id, phase=None):
    """A weapon model with the grip at the origin, pointing up +Y."""
    if item_id in ("claymore", "zweihander"):
        greatsword(r, item_id == "zweihander")
    elif item_id == "katana":
        katana(r)
    elif item_id == "leather_whip":
        whip(r, phase)
    elif item_id == "mace":
        mace(r)
    elif item_id == "war_hammer":
        hammer(r)
    else:
        sword(r, item_id)


def sword(r, item_id):
    """Straight sword: rusted, Ashblade or the longer bastard sword."""
    blade = {"ashblade": (200, 200, 215), "bastard_sword": (175, 178, 188)}.get(item_id, (170, 150, 130))
    long = item_id == "bastard_sword"
    length = 1.15 if long else 0.9
    grip = 0.3 if long else 0.2
    r.part("cube", 0, 0.1 - grip / 2, 0, 0.06, grip, 0.06, LEATHER)
    r.part("cube", 0, 0.12, 0, 0.07, 0.04, 0.36 if long else 0.3, BRASS)
    r.part("cube", 0, 0.15 + length / 2, 0, 0.03, length, 0.12, blade)
    r.part(
        "cube",
        0.016,
        0.15 + length / 2,
        0,
        0.01,
        length - 0.04,
        0.025,
        tuple(min(c + 40, 255) for c in blade),
    )
    r.part("cube", 0, 0.19 + length, 0, 0.025, 0.08, 0.07, blade)
    r.part("cube", 0, 0.05 - grip, 0, 0.08, 0.06, 0.08, BRASS)


def greatsword(r, zwei):
    length = 1.6 if zwei else 1.4
    width = 0.17 if zwei else 0.15
    blade = (185, 186, 196) if zwei else (170, 172, 180)
    r.part("cube", 0, -0.12, 0, 0.07, 0.38, 0.07, LEATHER)
    r.part("cube", 0, -0.34, 0, 0.1, 0.08, 0.1, BRASS)
    r.part("cube", 0, 0.1, 0, 0.08, 0.05, 0.56 if zwei else 0.46, (120, 110, 90))
    if zwei:  # leather-wrapped ricasso and parrying hooks
        r.part("cube", 0, 0.24, 0, 0.05, 0.22, 0.09, LEATHER)
        r.part("cube", 0, 0.37, 0.1, 0.04, 0.04, 0.1, (120, 110, 90))
        r.part("cube", 0, 0.37, -0.1, 0.04, 0.04, 0.1, (120, 110, 90))
    base = 0.36 if zwei else 0.13
    r.part("cube", 0, base + length / 2, 0, 0.04, length, width, blade)
    r.part("cube", 0.02, base + length / 2, 0, 0.01, length - 0.05, 0.03, (225, 225, 235))
    r.part("cube", 0, base + length + 0.05, 0, 0.035, 0.1, width * 0.55, blade)


def katana(r):
    r.part("cube", 0, -0.08, 0, 0.055, 0.3, 0.055, (40, 30, 40))
    for i in range(4):  # cord wrap
        r.part("cube", 0, -0.2 + i * 0.08, 0, 0.06, 0.02, 0.06, (160, 30, 40))
    r.part("cyl", 0, 0.08, 0, 0.16, 0.025, 0.16, (60, 50, 30))
    r.part("cube", 0, 0.11, 0, 0.04, 0.04, 0.06, (170, 150, 70))
    with r.at(0, 0.13, 0):
        _katana_segment(r, 3)


def _katana_segment(r, left):
    """A gentle curve: each segment hangs off the last, bent a little further back."""
    if left == 0:
        r.part("cube", 0, 0.03, -0.01, 0.022, 0.07, 0.05, (205, 208, 218), rx=0.35)
        return
    with r.at(0, 0, 0, rx=0.05):
        r.part("cube", 0, 0.17, 0, 0.025, 0.36, 0.07, (205, 208, 218))
        r.part("cube", 0.013, 0.17, -0.025, 0.006, 0.36, 0.015, (245, 245, 250))
        with r.at(0, 0.34, 0):
            _katana_segment(r, left - 1)


def whip(r, phase=None):
    r.part("cube", 0, -0.04, 0, 0.06, 0.3, 0.06, LEATHER)
    r.part("cube", 0, 0.12, 0, 0.075, 0.04, 0.075, BRASS)
    # Hanging coils at rest; the lash straightens out at the crack.
    straight = math.sin(phase * math.pi) if phase is not None else 0.0
    bend = 0.42 * (1 - straight) + 0.04
    with r.at(0, 0.14, 0):
        _whip_segment(r, 7, bend, 0.06)


def _whip_segment(r, left, bend, thick):
    if left == 0:
        r.part("cube", 0, 0.04, 0, 0.02, 0.08, 0.05, (120, 90, 60))
        return
    with r.at(0, 0, 0, rx=bend):
        r.part("cube", 0, 0.1, 0, thick, 0.2, thick, (100, 70, 44))
        with r.at(0, 0.2, 0):
            _whip_segment(r, left - 1, bend, max(thick * 0.86, 0.025))


def mace(r):
    r.part("cube", 0, 0.1, 0, 0.06, 0.7, 0.06, WOOD)
    r.part("cube", 0, -0.2, 0, 0.075, 0.12, 0.075, LEATHER)
    r.part("sphere", 0, 0.55, 0, 0.17, 0.22, 0.17, (88, 88, 96))
    for i in range(4):
        with r.at(0, 0.55, 0, ry=i * math.pi / 4):
            r.part("cube", 0, 0, 0, 0.03, 0.2, 0.26, (120, 120, 130))
    r.part("cube", 0, 0.69, 0, 0.05, 0.07, 0.05, (120, 120, 130))


def hammer(r):
    r.part("cube", 0, 0.35, 0, 0.065, 1.25, 0.065, WOOD)
    r.part("cube", 0, -0.2, 0, 0.08, 0.2, 0.08, LEATHER)
    r.part("cube", 0, 1.02, 0, 0.24, 0.24, 0.5, (110, 110, 118))
    r.part("cube", 0, 1.02, 0.28, 0.2, 0.2, 0.06, (140, 140, 150))  # striking face
    r.part("cube", 0, 1.02, -0.32, 0.06, 0.06, 0.16, STEEL)  # back spike
    r.part("cube", 0, 1.18, 0, 0.1, 0.1, 0.1, (90, 90, 98))


def item(r, id_, t):
    """Inventory preview models, roughly 1 unit tall and centered on the origin."""
    if Items.ALL.get(id_) and Items.get(id_).kind == "weapon":
        k = 1.2 / WEAPON_LEN.get(id_, 1.2)
        with r.at(0, -0.8 * k, 0, rx=0.3, s=1.45 * k):
            weapon(r, id_)
    elif id_ in ("padded_coat", "ringmail"):
        garment(r, id_ == "ringmail")
    elif id_ == "red_tonic":
        r.part("sphere", 0, -0.18, 0, 0.5, 0.5, 0.5, (170, 30, 30))
        r.part("cyl", 0, 0.18, 0, 0.14, 0.32, 0.14, (150, 40, 36))
        r.part("cyl", 0, 0.38, 0, 0.12, 0.12, 0.12, (120, 90, 60))
    elif id_ == "blue_moss":
        for x, y, z, d in (
            (0, -0.1, 0, 0.5),
            (0.12, 0.08, 0.1, 0.34),
            (-0.1, 0.05, -0.12, 0.3),
            (0.05, 0.2, -0.05, 0.24),
        ):
            r.part("sphere", x, y, z, d, d * 0.8, d, (60, 140, 190), glow=True)
        r.part("cyl", 0, -0.32, 0, 0.6, 0.06, 0.6, (70, 60, 44))
    elif id_ in ("scroll_mend", "scroll_lumen"):
        ribbon = (170, 40, 40) if id_ == "scroll_mend" else (210, 200, 120)
        with r.at(0, 0, 0, rx=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.3, 0.9, 0.3, (210, 196, 160))
            r.part("cyl", 0, 0, 0, 0.32, 0.1, 0.32, ribbon)
            r.part("cyl", 0, 0.5, 0, 0.08, 0.14, 0.08, (110, 80, 50))
            r.part("cyl", 0, -0.5, 0, 0.08, 0.14, 0.08, (110, 80, 50))
    elif id_ in ("cell_key", "warden_key"):
        warden = id_ == "warden_key"
        key(r, (120, 120, 128) if warden else (150, 84, 50), 1.9 if warden else 1.6)
    elif id_.startswith("spell_"):
        spell_orb(r, id_.removeprefix("spell_"), t)
    elif id_ == "ember_sigil":
        glow = 1 + math.sin(t * 4) * 0.08
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.7, 0.12, 0.7, (110, 80, 70))
            r.part("cyl", 0, 0, 0, 0.36 * glow, 0.14, 0.36 * glow, EMBER, glow=True)
    else:
        r.part("cube", 0, 0, 0, 0.5, 0.5, 0.5, (130, 100, 70))


def garment(r, mail):
    col = (130, 132, 140) if mail else (120, 104, 80)
    r.part("cube", 0, 0, 0, 0.3, 0.8, 0.62, col)
    r.part("cube", 0, 0.34, 0, 0.32, 0.14, 0.86, col)
    r.part("cube", 0, 0.0, -0.42, 0.22, 0.6, 0.18, col, rx=-0.15)
    r.part("cube", 0, 0.0, 0.42, 0.22, 0.6, 0.18, col, rx=0.15)
    # Ring rows on the mail, quilting seams on the coat.
    for i in range(4):
        r.part("cube", 0, 0.2 - i * 0.14, 0, 0.32, 0.03, 0.64, (70, 72, 80) if mail else (90, 76, 56))
    r.part("cube", 0, -0.18, 0, 0.33, 0.06, 0.65, (70, 50, 34))


def key(r, rgb, size):
    with r.at(0, 0, 0, rx=-0.6, s=size):
        r.part("cyl", 0, 0.32, 0, 0.32, 0.06, 0.32, rgb, rz=math.pi / 2)
        r.part("cube", 0, -0.08, 0, 0.06, 0.6, 0.06, rgb)
        r.part("cube", 0, -0.3, 0.08, 0.05, 0.06, 0.12, rgb)
        r.part("cube", 0, -0.18, 0.07, 0.05, 0.05, 0.1, rgb)
