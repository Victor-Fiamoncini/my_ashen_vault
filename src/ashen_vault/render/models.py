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
