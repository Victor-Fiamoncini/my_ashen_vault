"""Original low-poly models assembled from primitives. All face +X."""

import math

from ashen_vault.ai.enemy import COMBO_GAP
from ashen_vault.player.items import Items
from ashen_vault.util import rround
from ashen_vault.world import terrain

BONE = (214, 204, 178)
RUST = (120, 70, 44)
IRON = (92, 92, 98)
ASH = (96, 92, 88)
EMBER = (255, 140, 50)
WHITE = (255, 255, 255)
SKIN = (196, 158, 120)
LEAF = (58, 104, 44)
DARK_LEAF = (34, 70, 30)
BARK = (88, 64, 42)
DARK_BARK = (58, 42, 30)
SPIDER = (100, 80, 96)
MOSS = (70, 110, 50)


def enemy(r, e):
    t = e.anim_t
    fn = {
        "bone_walker": bone_walker,
        "mire_slime": mire_slime,
        "cinder_wisp": cinder_wisp,
        "ashen_warden": ashen_warden,
        "mimic": mimic,
        "snare_bloom": snare_bloom,
        "bark_husk": bark_husk,
        "stump_mimic": stump_mimic,
        "loom_mother": loom_mother,
        "loom_brood": loom_brood,
        "gaoler": gaoler,
        "bone_crawler": bone_crawler,
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


def death_fall(e, time=0.6):
    """0..1 how far a dying body has collapsed into its death pose (eased), 0 while alive. The ash
    effect then bleaches and crumbles it where it lies."""
    if e.state != "dead":
        return 0.0
    k = min(e.state_t / time, 1.0)
    return k * k * (3 - 2 * k)


def walk_cycle(e, t):
    return math.sin(t * 7) * 0.5 if e.state in ("chase", "idle") else 0


def bone_walker(r, e, t):
    """A walking skeleton with a rusted blade. Slain, its knees give and it topples onto its back."""
    swing = walk_cycle(e, t)
    hit = strike_angle(e)
    fall = death_fall(e, 0.7)
    lean = (-0.3 if e.state == "hurt" else 0) + 1.35 * fall
    with r.at(-0.2 * fall, 0.12 * fall, 0, rz=lean):
        for side, a in ((-0.14, swing), (0.14, -swing)):
            with r.at(0, 0.9, side, rz=a + 0.35 * fall):
                r.part("cube", 0, -0.22, 0, 0.08, 0.45, 0.08, BONE)
                r.part("cube", 0, -0.66, 0, 0.07, 0.45, 0.07, BONE)
                r.part("cube", 0.06, -0.88, 0, 0.18, 0.05, 0.1, BONE)
        r.part("cube", 0, 0.95, 0, 0.18, 0.12, 0.34, BONE)
        r.part("cyl", 0, 1.18, 0, 0.08, 0.4, 0.08, BONE)
        for i in range(4):
            r.part("cube", 0.02, 1.08 + i * 0.1, 0, 0.16, 0.03, 0.36 - i * 0.02, BONE)
        r.part("cube", 0, 1.42, 0, 0.14, 0.06, 0.46, BONE)
        with r.at(0.02, 1.6, 0, rz=math.sin(t * 2) * 0.1 * (1 - fall) - 0.5 * fall):
            r.part("sphere", 0, 0, 0, 0.26, 0.28, 0.24, BONE)
            r.part("cube", 0.11, -0.03, -0.05, 0.05, 0.06, 0.06, (30, 10, 10))
            r.part("cube", 0.11, -0.03, 0.05, 0.05, 0.06, 0.06, (30, 10, 10))
            r.part("cube", 0.08, -0.15, 0, 0.12, 0.06, 0.16, BONE)
        with r.at(0, 1.4, -0.27, rz=swing * 0.6):
            r.part("cube", 0, -0.3, 0, 0.06, 0.6, 0.06, BONE)
        with r.at(0, 1.4, 0.27, rz=hit - 0.9 * fall):
            r.part("cube", 0, -0.3, 0, 0.06, 0.6, 0.06, BONE)
            with r.at(0.05, -0.6, 0, rz=1.4):
                r.part("cube", 0.4, 0, 0, 0.8, 0.07, 0.03, RUST)
                r.part("cube", 0.0, 0, 0, 0.05, 0.05, 0.2, IRON)


def mire_slime(r, e, t):
    """A heap of bog jelly. Slain, it slumps and spreads into a puddle."""
    squash = 1 + math.sin(t * (9 if e.state == "chase" else 4)) * 0.12
    if e.state == "windup":
        squash = 1.35
    if e.state == "attack":
        squash = 0.7
    if e.state == "dead":
        squash = 1 + 1.2 * death_fall(e, 0.8)
    green = (200, 220, 160) if e.state == "hurt" else (70, 120, 60)
    r.part("sphere", 0, 0.32 / squash, 0, 0.95 * squash, 0.7 / squash, 0.95 * squash, green)
    r.part("sphere", 0.05, 0.14, 0, 1.05 * squash, 0.28, 1.05 * squash, (50, 90, 44))
    r.part("sphere", 0.3, 0.45 / squash, -0.14, 0.12, 0.12, 0.12, (230, 220, 120))
    r.part("sphere", 0.3, 0.45 / squash, 0.14, 0.12, 0.12, 0.12, (230, 220, 120))


def cinder_wisp(r, e, t):
    """A floating ember with a flame crown. Slain, it gutters out and sinks, cooling as it falls."""
    fade = death_fall(e, 0.9)
    bob = math.sin(t * 3) * 0.15 * (1 - fade)
    lit = fade < 0.5
    glow = (255, 230, 140) if e.state == "windup" else EMBER if lit else (120, 70, 50)
    with r.at(0, e.type.hover + bob - 0.3 * fade, 0, s=1 - 0.35 * fade):
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
                glow=lit,
            )
        r.part("cone", 0, 0.42, 0, 0.3, 0.45 * (1 - fade), 0.3, (255, 120, 40), glow=lit)


def _warden_arms(e, t):
    """(sword arm, free arm, blade tilt, twist, crouch, glowing sword) for the Warden's moves.
    Combo: three alternating cuts. Slam: both arms high, then down. Eruption: the blade is driven
    point-down into the floor. Kindle: the blade held straight up, trembling."""
    hit = strike_angle(e)
    free = 0.0
    blade = 1.45
    twist = crouch = 0.0
    glow = False
    kind = e.attack_kind
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    if kind == "combo" and e.state == "attack":
        i = e.combo_swing
        u = (e.state_t - i * COMBO_GAP) / COMBO_GAP
        hit = -2.0 * min(u / 0.35, 1) if u < 0.35 else -2.0 + 2.9 * min((u - 0.35) / 0.25, 1)
        twist = 0.35 if i % 2 == 0 else -0.35
    elif kind == "slam" and e.state in ("windup", "attack"):
        if e.state == "windup":
            hit = free = -2.7 * k
            glow = True
        else:
            hit = free = -2.7 + 3.5 * min(e.state_t / 0.12, 1)
            crouch = -0.25 * min(e.state_t / 0.12, 1)
    elif kind == "eruption" and e.state in ("windup", "attack"):
        if e.state == "windup":
            hit = -2.4 * k
        else:
            hit, blade, crouch = 1.1, 2.9, -0.2
        glow = True
    elif kind == "kindle" and e.state in ("windup", "attack"):
        hit = -2.9 * k + math.sin(t * 40) * 0.05
        blade = 1.45 + 1.4 * k
        glow = True
    return hit, free, blade, twist, crouch, glow


def ashen_warden(r, e, t):
    """The keep's armoured warden. Slain, he sinks to his knees, braced on his blade, and slumps.
    In his second phase his blade burns."""
    swing = walk_cycle(e, t) * 0.7
    kneel = death_fall(e, 0.6)
    slump = death_fall(e, 1.6)
    dead = e.state == "dead"
    # Boss moves share the spider's timing: a sweep coils then spins him round, a leap crouches
    # then arcs him through the air. Embers: the free hand rises glowing, then flings forward.
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit, free, blade, twist, crouch, glow = _warden_arms(e, t)
    cinders = e.attack_kind == "cinders" and e.state in ("windup", "attack")
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    if cinders:
        free = -1.9 * k if e.state == "windup" else -1.9 + 1.4 * min(e.state_t / 0.15, 1)
    burning = e.phase2 and not dead
    steel = EMBER if burning else IRON
    with (
        r.at(0, lift * 0.8 + crouch - 0.42 * kneel, 0, s=1.35, ry=spin + twist),
        r.at(0, 0.95, 0, rz=-0.45 * slump),
        r.at(0, -0.95, 0),
    ):
        for side, a in ((-0.18, swing), (0.18, -swing)):
            with r.at(0, 0.95, side, rz=a + 1.4 * kneel):
                r.part("cube", 0, -0.45, 0, 0.2, 0.9, 0.18, ASH)
                r.part("cube", 0.05, -0.92, 0, 0.32, 0.1, 0.2, (60, 58, 56))
        r.part("cube", 0, 1.0, 0, 0.36, 0.24, 0.5, (70, 66, 62))
        r.part("cube", 0, 1.35, 0, 0.4, 0.55, 0.62, ASH)
        r.part("cube", 0, 1.68, 0, 0.44, 0.14, 0.86, (76, 72, 68))
        with r.at(0.02, 1.88, 0):
            r.part("cube", 0, 0, 0, 0.3, 0.32, 0.28, (70, 66, 62))
            r.part("cube", 0.15, 0.02, 0, 0.02, 0.05, 0.2, (70, 40, 30) if dead else EMBER, glow=not dead)
            r.part("cone", 0, 0.26, 0, 0.12, 0.3, 0.12, (60, 58, 56))
        with r.at(0, 1.6, -0.47, rz=free):
            r.part("cube", 0, -0.35, 0, 0.16, 0.7, 0.16, ASH)
            if cinders and e.state == "windup":
                r.part("sphere", 0, -0.75, 0, 0.3 * k, 0.3 * k, 0.3 * k, EMBER, glow=True)
        with r.at(0, 1.6, 0.47, rz=hit - 0.5 * kneel):
            r.part("cube", 0, -0.35, 0, 0.16, 0.7, 0.16, ASH)
            with r.at(0.05, -0.72, 0, rz=blade - 1.0 * kneel):
                r.part("cube", 0.6, 0, 0, 1.4, 0.08, 0.08, (60, 44, 30))
                r.part("cube", 1.2, 0.0, 0, 0.36, 0.5, 0.05, steel, glow=burning or (glow and not dead))
                if burning or (glow and not dead):
                    _flame(r, 1.2, 0.2, 0, 0.12 + (0.06 if burning else 0.0), t)


LEATHER = (84, 60, 44)
SACKCLOTH = (124, 108, 82)


def gaoler(r, e, t):
    """A hulking, hunched jailer in a sackcloth hood and a stained leather apron: a cudgel in one
    hand, a hooked chain in the other. The hook whirls overhead, then flies out at you.
    Slain, he drops to his knees and pitches forward onto his face."""
    swing = walk_cycle(e, t) * 0.6
    hit = strike_angle(e)
    kneel = death_fall(e, 0.5)
    pitch = death_fall(e, 1.2)
    hooking = e.attack_kind == "hook" and e.state in ("windup", "attack")
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    skin = (240, 220, 200) if e.state == "hurt" else (150, 120, 100)
    with r.at(0, 0.45 - 0.4 * kneel, 0, rz=-1.25 * pitch), r.at(0, -0.45, 0):
        for side, a in ((-0.22, swing), (0.22, -swing)):
            with r.at(0, 0.85, side, rz=a - 1.5 * kneel):
                r.part("cube", 0, -0.42, 0, 0.26, 0.84, 0.24, LEATHER)
                r.part("cube", 0.06, -0.84, 0, 0.36, 0.12, 0.26, (50, 40, 32))
        with r.at(0, 0.9, 0, rz=-0.25):  # the hunch
            r.part("cube", 0.02, 0.45, 0, 0.62, 0.9, 0.8, skin)
            r.part("cube", 0.2, 0.3, 0, 0.3, 0.95, 0.66, LEATHER)  # apron
            r.part("cube", 0.36, 0.35, 0.1, 0.02, 0.2, 0.18, (90, 30, 26))  # old stains
            r.part("cube", 0, 0.75, 0, 0.66, 0.1, 0.84, (60, 46, 36))  # belt of keys
            for i in range(3):
                r.part("cube", 0.2, 0.62, -0.3 + i * 0.12, 0.03, 0.16, 0.05, BRASS)
            with r.at(0.2, 1.05, 0):  # hooded head, thrust forward
                r.part("sphere", 0, 0, 0, 0.42, 0.44, 0.4, SACKCLOTH)
                r.part("cone", -0.05, 0.25, 0, 0.3, 0.3, 0.3, SACKCLOTH)
                r.part("cube", 0.2, 0.02, -0.08, 0.04, 0.05, 0.06, (20, 14, 10))
                r.part("cube", 0.2, 0.02, 0.08, 0.04, 0.05, 0.06, (20, 14, 10))
        # The cudgel arm.
        with r.at(0, 1.65, 0.5, rz=(0.0 if hooking else hit) - 0.6 * kneel):
            r.part("cube", 0, -0.4, 0, 0.2, 0.8, 0.2, skin)
            with r.at(0.05, -0.8, 0, rz=1.4 - 2.9 * kneel):  # slain, the cudgel slips down
                r.part("cyl", 0.45, 0, 0, 0.1, 0.9, 0.1, (90, 64, 40), rz=math.pi / 2)
                r.part("cyl", 0.85, 0, 0, 0.2, 0.3, 0.2, (70, 50, 32), rz=math.pi / 2)
                for i in range(3):
                    r.part("cube", 0.85, 0.1 * (i - 1), 0.18, 0.06, 0.05, 0.05, IRON)
        # The chain arm: the hook circles overhead on the windup and flies out on the throw.
        if hooking and e.state == "windup":
            arm, whirl = -2.6, t * 14
        elif hooking:
            arm, whirl = -2.6 + 3.4 * min(e.state_t / 0.12, 1), None
        else:
            arm, whirl = swing * 0.5 - 0.3 * kneel, None
        with r.at(0, 1.65, -0.5, rz=arm):
            r.part("cube", 0, -0.4, 0, 0.2, 0.8, 0.2, skin)
            if whirl is not None:
                with r.at(0, -0.85, 0, rx=whirl):
                    for i in range(5):
                        r.part("cube", 0, 0, 0.15 + i * 0.15, 0.05, 0.05, 0.12, IRON, rx=i * 1.2)
                    r.part("cone", 0, 0, 0.95, 0.18, 0.3, 0.06, STEEL, rx=math.pi / 2)
            elif hooking:
                reach = 6.0 * min(e.state_t / 0.12, 1) * k
                with r.at(0, -0.85, 0, rz=math.pi / 2 - arm):  # the chain flies level, straight out
                    n = max(int(reach / 0.25), 1)
                    for i in range(n):
                        r.part("cube", 0, -(i + 0.5) * reach / n, 0, 0.05, 0.14, 0.05, IRON, ry=i * 1.2)
                    r.part("cone", 0, -reach, 0, 0.2, 0.32, 0.06, STEEL, rx=math.pi)
            else:
                for i in range(5):  # the chain hangs loose, the hook trailing on the floor
                    r.part("cube", 0, -0.9 - i * 0.14, 0, 0.05, 0.12, 0.05, IRON, ry=i * 1.2)
                r.part("cone", 0.05, -1.62, 0, 0.18, 0.3, 0.06, STEEL, rz=math.pi)


def bone_crawler(r, e, t):
    """A ribcage scuttling on long finger-bones, skull slung low in front. At rest it is only a heap
    of bones; slain, it falls apart into one again."""
    seed = int(abs(e.home_x * 3 + e.home_z * 7))
    fall = death_fall(e, 0.5)
    if e.state == "idle" or fall >= 1.0:
        bones(r, seed)
        return
    gait = math.sin(t * 16) * 0.35 if e.state == "chase" else math.sin(t * 3) * 0.08
    rear = 0.0
    if e.state == "windup":
        rear = -0.5 * min(e.state_t / e.type.windup, 1)
    elif e.state == "attack":
        rear = 0.3
    bone = (255, 240, 220) if e.state == "hurt" else BONE
    rise = 0.32 * (1 - fall)
    with r.at(0, rise, 0, rz=rear * (1 - fall)):
        for i in range(4):  # the ribcage
            r.part("cube", -0.15 + i * 0.1, 0.06, 0, 0.05, 0.16, 0.5 - abs(i - 1.5) * 0.06, bone, rx=0.2)
        r.part("cube", 0, 0.12, 0, 0.56, 0.06, 0.06, bone)  # spine
        with r.at(0.38, 0.0, 0, rz=-0.2):
            r.part("sphere", 0, 0, 0, 0.26, 0.22, 0.22, bone)
            r.part("cube", 0.11, 0.0, -0.05, 0.05, 0.05, 0.05, (255, 120, 60), glow=fall < 0.5)
            r.part("cube", 0.11, 0.0, 0.05, 0.05, 0.05, 0.05, (255, 120, 60), glow=fall < 0.5)
            jaw = 0.5 if e.state == "windup" else 0.1
            r.part("cube", 0.06, -0.12, 0, 0.16, 0.04, 0.14, bone, rz=jaw)
        for i in range(6):  # finger-bone legs
            side = 1 if i % 2 else -1
            x = -0.2 + (i // 2) * 0.2
            step = gait * (1 if (i // 2 + i) % 2 else -1)
            with r.at(x, 0, side * 0.2, rx=side * (0.9 + 0.6 * fall), ry=step):
                r.part("cube", 0, 0, side * 0.18, 0.04, 0.04, 0.36, bone)
                r.part("cube", 0, -0.14, side * 0.36, 0.04, 0.3, 0.04, bone, rx=-side * 0.3)


def mimic(r, e, t):
    """A chest with teeth. Asleep it is a plain closed chest; awake it gapes, chews and scuttles."""
    if e.state == "dormant":
        chest(r, False)
        return
    shut = death_fall(e, 0.4)
    dead = e.state == "dead"
    gape = 0.9 + math.sin(t * 9) * 0.25
    if e.state == "windup":
        gape = 1.5
    elif e.state == "attack":
        gape = 0.15
    elif dead:
        gape = 0.9 * (1 - shut)  # the lid slams shut
    lunge = 0.35 if e.state == "attack" else 0.0
    step = math.sin(t * 14) * 0.08 if e.state == "chase" else 0.0
    with r.at(lunge, 0.18 * (1 - shut), 0):
        for lx, lz in ((0.2, 0.32), (0.2, -0.32), (-0.2, 0.32), (-0.2, -0.32)):
            sway = step if (lx > 0) == (lz > 0) else -step
            leg = 0.3 * (1 - shut)  # the legs fold away under the chest
            if leg > 0.01:
                r.part(
                    "cube",
                    lx + sway,
                    -leg / 2 + 0.07,
                    lz,
                    0.08,
                    leg,
                    0.08,
                    (60, 40, 34),
                    rz=-0.3 if lx > 0 else 0.3,
                )
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
            eye = (70, 50, 30) if dead else (255, 200, 60)
            r.part("sphere", 0.45, 0.18, -0.22, 0.1, 0.1, 0.1, eye, glow=not dead)
            r.part("sphere", 0.45, 0.18, 0.22, 0.1, 0.1, 0.1, eye, glow=not dead)


def jaw_open(e, t):
    """How far a snapping mouth gapes: idle breathing, wide on windup, shut on the strike."""
    if e.state == "windup":
        return 0.3 + 0.9 * min(e.state_t / e.type.windup, 1)
    if e.state == "attack":
        return 1.2 * (1 - min(e.state_t / 0.12, 1))
    if e.state == "recover":
        return 0.25 * min(e.state_t / e.type.recover, 1)
    if e.state == "dead":
        return 0.9 - 0.4 * death_fall(e)  # the jaws go slack
    return 0.22 + math.sin(t * 2.3) * 0.12


def snare_bloom(r, e, t):
    """Rooted carnivorous plant: a leafy base, a swaying stem and a fanged pod ringed with petals."""
    hurt = e.state == "hurt"
    wilt = death_fall(e)
    gape = jaw_open(e, t)
    lunge = 0.35 if e.state == "windup" else (0.55 if e.state == "attack" else 0)
    sway = math.sin(t * 1.7) * 0.12 * (1 - wilt)
    # Root mound and broad leaves on the floor.
    r.part("sphere", 0, 0.08, 0, 0.9, 0.24, 0.9, (60, 50, 34))
    for i in range(5):
        a = i * 2 * math.pi / 5 + 0.3
        with r.at(math.cos(a) * 0.35, 0.12, math.sin(a) * 0.35, ry=-a, rz=-0.25):
            r.part("sphere", 0.28, 0, 0, 0.7, 0.07, 0.3, LEAF if i % 2 else DARK_LEAF)
    # Stem: three segments that curl back on windup and whip forward on the strike. In death the
    # stem wilts forward and the head hangs.
    bend = sway - lunge * 0.5
    a1 = bend * 0.5 - 0.45 * wilt
    a2 = bend * 0.4 + lunge * 0.9 - 0.75 * wilt
    a3 = -0.7 - lunge * 0.4 - 0.3 * wilt
    with r.at(0, 0, 0, s=1.2), r.at(0, 0.15, 0, rz=a1):
        r.part("cyl", 0, 0.3, 0, 0.16, 0.62, 0.16, (70, 110, 50))
        with r.at(0, 0.58, 0, rz=a2):
            r.part("cyl", 0, 0.28, 0, 0.13, 0.58, 0.13, (80, 120, 54))
            with r.at(0, 0.55, 0, rz=a3):
                r.part("cyl", 0, 0.12, 0, 0.11, 0.26, 0.11, (80, 120, 54))
                # Undo the stem's bends so the mouth faces forward, dipping a little as it lunges.
                with r.at(0, 0.26, 0, rz=-(a1 + a2 + a3) - lunge * 0.4 - 1.1 * wilt):
                    _bloom_head(r, gape, hurt, t)


def _bloom_head(r, gape, hurt, t):
    """Head at the stem tip, mouth facing +X (the stem frame is pitched so +X points forward)."""
    flesh = (230, 200, 190) if hurt else (150, 40, 60)
    petal = (210, 190, 200) if hurt else (196, 60, 92)
    # Petal ruff behind the mouth; it flares as the jaws open.
    for i in range(6):
        a = i * math.pi / 3
        with r.at(0, 0, 0, rx=a), r.at(-0.05, 0.18, 0, rz=0.5 + gape * 0.6):
            r.part("sphere", 0, 0.2, 0, 0.16, 0.42, 0.24, petal)
    r.part("sphere", -0.08, 0, 0, 0.34, 0.34, 0.34, (60, 96, 44))
    # Throat glows faintly so the open mouth reads in the dark.
    r.part("sphere", 0.05, 0, 0, 0.24, 0.2, 0.24, (220, 80, 60), glow=gape > 0.6)
    for side in (1, -1):
        with r.at(0, 0, 0, rz=side * gape * 0.5):
            r.part("sphere", 0.24, side * 0.08, 0, 0.56, 0.2, 0.44, flesh)
            r.part("sphere", 0.26, side * 0.14, 0, 0.5, 0.12, 0.4, (110, 150, 60))
            for k in range(4):
                z = -0.15 + k * 0.1
                r.part(
                    "cone",
                    0.42,
                    -side * 0.04,
                    z,
                    0.05,
                    0.12,
                    0.05,
                    (236, 230, 200),
                    rz=0 if side < 0 else math.pi,
                )


def bark_husk(r, e, t):
    """A gaunt weeping-willow husk. It hunches forward on a skirt of writhing roots, with long arms
    that drag on the ground and a pale carved mask under a curtain of hanging willow strands.
    Down its back a split in the bark shows the glowing heart-fungus: the weak spot."""
    hit = strike_angle(e)
    hurt = e.state == "hurt"
    moving = e.state in ("chase", "idle")
    slump = death_fall(e, 0.8)
    bark = (240, 220, 200) if hurt else (128, 118, 92)
    lean = -0.35 if e.state == "windup" else (0.15 if hurt else -0.15)
    lean -= 0.55 * slump  # topples forward over its roots as it dies
    with r.at(0, 0, 0, s=1.25):
        # Root skirt: roots fan out and writhe as it glides along.
        for i in range(9):
            a = i * 2 * math.pi / 9
            wr = math.sin(t * (5 if moving else 1.5) + i * 1.7) * (0.2 if moving else 0.06)
            with r.at(math.cos(a) * 0.18, 0.5, math.sin(a) * 0.18, ry=-a, rz=-0.75 + wr):
                r.part("cube", 0.32, 0, 0, 0.7, 0.13, 0.13, DARK_BARK)
                with r.at(0.65, 0, 0, rz=-0.5 - wr):
                    r.part("cube", 0.2, 0, 0, 0.42, 0.09, 0.09, DARK_BARK)
        with r.at(0, 0.45 - 0.3 * slump, 0, rz=lean):
            # Tall, narrow trunk that twists as it rises.
            r.part("cyl", 0, 0.65, 0, 0.6, 1.3, 0.54, bark, tex="bark")
            with r.at(0, 1.25, 0, rz=-0.15, ry=0.25):
                r.part("cyl", 0, 0.45, 0, 0.46, 0.9, 0.42, bark, tex="bark")
                _husk_heart(r, t, hurt, dead=e.state == "dead")
                _husk_mask(r, e)
                _willow_crown(r, e, t)
            # Long arms: both rise together and come down in a double slam.
            for side in (1, -1):
                arm = hit if side > 0 else hit * 0.9
                if moving:
                    arm = math.sin(t * 2.5 + side) * 0.12
                arm -= 0.9 * slump  # the arms fall forward and sprawl along the ground
                with r.at(0, 1.95, side * 0.36, rx=side * 0.18, rz=arm):
                    _willow_arm(r, bark)


def _husk_heart(r, t, hurt, dead=False):
    """A split down the back (-X) with the pulsing heart-fungus inside. It gutters out on death."""
    pulse = 1 + math.sin(t * 3.1) * 0.12 * (not dead)
    r.part("cube", -0.21, 0.3, 0, 0.08, 1.0, 0.22, (16, 10, 8))
    glow = (255, 255, 255) if hurt else (60, 90, 76) if dead else (110, 240, 190)
    r.part("sphere", -0.2, 0.35, 0, 0.2 * pulse, 0.55 * pulse, 0.24 * pulse, glow, glow=not dead)
    for y, z in ((0.0, 0.1), (0.7, -0.08), (-0.25, -0.1)):
        r.part("sphere", -0.24, y, z, 0.12, 0.07, 0.12, (80, 220, 170), glow=not dead)
    for y in (0.05, 0.4, 0.75):
        r.part("cube", -0.25, y, 0, 0.05, 0.06, 0.3, DARK_BARK)


def _husk_mask(r, e):
    """Pale carved mask: hollow eye slits with ember pupils and a long mouth slit."""
    mask = (214, 204, 178)
    r.part("cube", 0.24, 0.6, 0, 0.07, 0.72, 0.5, mask)
    r.part("cube", 0.25, 0.96, 0, 0.08, 0.08, 0.54, mask)
    dead = e.state == "dead"  # the ember pupils go out
    for z in (-0.12, 0.12):
        r.part("cube", 0.28, 0.74, z, 0.03, 0.08, 0.14, (16, 10, 8))
        r.part(
            "cube", 0.295, 0.74, z, 0.02, 0.05, 0.05, (60, 40, 30) if dead else (255, 120, 50), glow=not dead
        )
    gape = 0.18 if e.state in ("windup", "attack") else 0.05
    r.part("cube", 0.28, 0.44, 0, 0.03, 0.16 + gape, 0.07, (16, 10, 8))
    # Twisted antler-like twigs above the mask.
    for side in (1, -1):
        with r.at(0.1, 0.95, side * 0.12, rx=side * 0.6, rz=0.3):
            r.part("cube", 0, 0.2, 0, 0.05, 0.4, 0.05, DARK_BARK)
            r.part("cube", 0.06, 0.32, side * 0.05, 0.04, 0.2, 0.04, DARK_BARK, rx=side * 0.7)


def _willow_crown(r, e, t):
    """A dome of leaves with willow strands hanging all round. The strands part in front of the
    mask, and they swing up when it winds up."""
    flare = 0.5 if e.state == "windup" else 0.0
    with r.at(0, 1.0, 0):
        r.part("sphere", 0, 0.1, 0, 1.0, 0.4, 1.0, DARK_LEAF)
        r.part("sphere", -0.1, 0.25, 0.1, 0.7, 0.3, 0.7, LEAF)
        for k in range(16):
            a = k * 2 * math.pi / 16
            front = math.cos(a) > 0.4
            length = 0.25 if front else 0.9 + (k * 7 % 5) * 0.18
            sway = math.sin(t * 1.4 + k) * 0.08
            with r.at(math.cos(a) * 0.45, 0, math.sin(a) * 0.45, ry=-a, rz=sway - flare):
                r.part("cube", 0, -length / 2, 0, 0.05, length, 0.14, LEAF if k % 3 else MOSS)


def _willow_arm(r, bark):
    """Hangs from the shoulder: long upper arm, a knotted elbow and a forearm ending in twig claws."""
    r.part("cyl", 0, -0.48, 0, 0.16, 0.96, 0.16, bark)
    r.part("sphere", 0, -0.98, 0, 0.24, 0.24, 0.24, DARK_BARK)
    with r.at(0, -0.98, 0, rz=0.35):
        r.part("cyl", 0, -0.45, 0, 0.12, 0.9, 0.12, bark)
        for k in range(4):
            with r.at(0, -0.9, (k - 1.5) * 0.06, rx=(k - 1.5) * 0.35, rz=0.25):
                r.part("cone", 0, -0.24, 0, 0.06, 0.5, 0.06, DARK_BARK, rx=math.pi)


def stump_mimic(r, e, t):
    """Looks like a mossy tree stump until you come close; then the lid splits open on a fanged maw
    and stubby roots lift it off the ground."""
    settle = death_fall(e, 0.5)
    awake = e.state not in ("idle", "dead")
    hurt = e.state == "hurt"
    bark = (240, 220, 200) if hurt else BARK
    gape = jaw_open(e, t) if awake else 0.0
    rise = 0.22 if awake else 0.22 * (1 - settle) if e.state == "dead" else 0.0
    if awake:
        gait = walk_cycle(e, t) * 1.2
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            with r.at(
                math.cos(a) * 0.38, rise + 0.12, math.sin(a) * 0.38, ry=-a, rz=-0.9 + gait * (i % 2 - 0.5)
            ):
                r.part("cyl", 0.1, -0.1, 0, 0.12, 0.4, 0.12, DARK_BARK)
    else:
        for i in range(4):
            a = i * math.pi / 2 + 0.4
            r.part("cube", math.cos(a) * 0.5, 0.06, math.sin(a) * 0.5, 0.5, 0.12, 0.14, DARK_BARK, ry=-a)
    with r.at(0, rise, 0):
        r.part("cyl", 0, 0.33, 0, 1.0, 0.66, 1.0, bark, tex="bark")
        r.part("cyl", 0, 0.66, 0, 0.86, 0.04, 0.86, (26, 14, 10))
        if awake:
            r.part("sphere", 0.1, 0.66, 0, 0.5, 0.12, 0.5, (200, 60, 50), glow=gape > 0.6)
            for k in range(7):
                a = -1.3 + k * 0.43
                r.part("cone", math.cos(a) * 0.4, 0.74, math.sin(a) * 0.4, 0.06, 0.16, 0.06, BONE)
        # The lid hinges at the back and lifts at the front.
        with r.at(-0.45, 0.68, 0, rz=gape * 0.8):
            r.part("cyl", 0.45, 0.05, 0, 0.98, 0.1, 0.98, (160, 128, 92))
            r.part("cyl", 0.45, 0.1, 0, 0.6, 0.02, 0.6, (120, 94, 66))
            r.part("sphere", 0.2, 0.14, 0.25, 0.4, 0.12, 0.3, MOSS)
            if awake:
                for k in range(6):
                    a = -1.1 + k * 0.44
                    r.part(
                        "cone",
                        0.45 + math.cos(a) * 0.38,
                        -0.05,
                        math.sin(a) * 0.38,
                        0.05,
                        0.14,
                        0.05,
                        BONE,
                        rx=math.pi,
                    )
                for z in (-0.16, 0.16):
                    r.part("cube", 0.86, 0.0, z, 0.06, 0.07, 0.08, (255, 200, 70), glow=True)


def loom_mother(r, e, t):
    """Giant spider: eight jointed legs in a skittering gait, a swollen patterned abdomen, glowing eyes."""
    hurt = e.state == "hurt"
    body = (150, 130, 150) if hurt else SPIDER
    band = (196, 150, 90)
    moving = e.state in ("chase", "idle")
    gait = t * 11 if moving else t * 2
    amp = 1.0 if moving else 0.15
    # Rear up on windup, slam down on the strike.
    if e.state == "windup":
        rear = 0.4 * min(e.state_t / e.windup_time, 1)
    elif e.state == "attack":
        rear = 0.4 - 0.55 * min(e.state_t / 0.15, 1)
    elif e.state == "recover":
        rear = -0.15 * (1 - min(e.state_t / e.type.recover, 1))
    else:
        rear = 0
    fang = jaw_open(e, t)
    lift, spin, rear, amp = _spider_move(e, t, rear, amp)
    if e.state == "windup" and e.attack_kind in ("sweep", "summon"):
        gait = t * 16
    curl = death_fall(e, 0.7)
    if curl:
        # Dead: the legs stop and fold up over the body, and it settles onto the floor.
        amp *= 1 - curl
        lift -= 0.2 * curl
    with r.at(0, lift, 0, s=1.15, ry=spin), r.at(-1.0, 0, 0, rz=rear), r.at(1.0, 0, 0):
        bob = math.sin(gait * 2) * 0.04 * amp
        with r.at(0, bob, 0):
            _spider_body(r, e, t, body, fang)
        for side in (1, -1):
            for i in range(4):
                phase = gait + i * math.pi / 2 + (math.pi / 2 if side < 0 else 0)
                _spider_leg(r, i, side, phase, amp, body, band, curl)


def _spider_move(e, t, rear, amp):
    """Body lift, spin, rear and leg swing for a boss move, so each attack has its own tell:
    a sweep coils and spins, a web shot tips the spinnerets up, a pounce crouches then flies,
    and the summon rears up and trembles."""
    kind = e.attack_kind
    lift = spin = 0.0
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 0.0
    if kind == "sweep":
        if e.state == "windup":
            spin, lift, amp = -0.7 * k, -0.15 * k, 1.6
        elif e.state == "attack":
            spin = -0.7 + (2 * math.pi + 0.7) * min(e.state_t / 0.3, 1)
            amp = 1.6
    elif kind == "web":
        if e.state == "windup":
            rear = -0.35 * k
        elif e.state == "attack":
            rear = -0.35
    elif kind == "pounce":
        if e.state == "windup":
            lift, rear = -0.35 * k, 0.15 * k
        elif e.state == "attack":
            lift, rear, amp = math.sin(min(e.state_t / 0.5, 1) * math.pi) * 1.3, 0.3, 0.3
    elif kind == "summon" and e.state in ("windup", "attack"):
        rear = 0.7 * (k if e.state == "windup" else 1) + math.sin(t * 40) * 0.04
    return lift, spin, rear, amp


def loom_brood(r, e, t):
    """A hatchling of the Loom Mother: the same spider, small and quick."""
    with r.at(0, 0, 0, s=0.3):
        loom_mother(r, e, t)


def web_shot(r, t):
    """A wad of spun silk trailing loose strands."""
    r.part("sphere", 0, 0, 0, 0.45, 0.45, 0.45, (236, 236, 226), glow=True)
    for k in range(5):
        a = k * 1.26 + t * 3
        r.part("cube", -0.3, math.sin(a) * 0.15, math.cos(a) * 0.15, 0.7, 0.03, 0.03, (220, 220, 210))


def _spider_body(r, e, t, body, fang):
    breathe = 1 + math.sin(t * 1.6) * 0.03
    # Abdomen with a pale skull-like crest, banded sides and spinnerets.
    pale = (214, 200, 160)
    with r.at(-1.3, 1.3, 0, rz=0.22):
        r.part("sphere", 0, 0, 0, 2.3 * breathe, 1.7 * breathe, 2.0 * breathe, body)
        dead = e.state == "dead"  # the crest's glow dies with her
        r.part(
            "sphere", 0.15, 0.68, 0, 1.1, 0.4, 0.85, (70, 84, 62) if dead else (110, 140, 90), glow=not dead
        )
        r.part("sphere", 0.42, 0.68, -0.2, 0.24, 0.3, 0.24, (40, 20, 24))
        r.part("sphere", 0.42, 0.68, 0.2, 0.24, 0.3, 0.24, (40, 20, 24))
        for k in range(3):
            x = -0.3 - k * 0.36
            r.part("cube", x, 0.7 - k * 0.12, 0, 0.12, 0.14, 1.4 - k * 0.3, pale, rz=0.35 + k * 0.2)
        for side in (1, -1):
            r.part("sphere", -0.1, 0.05, side * 0.88, 1.4, 0.6, 0.26, (150, 60, 50))
        r.part("cone", -1.18, -0.05, 0, 0.22, 0.36, 0.22, body, rz=math.pi / 2)
    # Waist and head-chest.
    r.part("cyl", -0.2, 0.98, 0, 0.32, 0.4, 0.32, body, rz=math.pi / 2)
    r.part("sphere", 0.3, 0.92, 0, 1.0, 0.62, 0.86, body)
    r.part("sphere", 0.32, 1.12, 0, 0.7, 0.3, 0.6, (64, 54, 66))
    # Eyes: two large and six small, all glowing.
    dead = e.state == "dead"
    eye = (40, 44, 36) if dead else (255, 70, 50) if e.state == "windup" else (190, 255, 110)
    for z in (-0.11, 0.11):
        r.part("sphere", 0.76, 1.08, z, 0.14, 0.14, 0.14, eye, glow=not dead)
    for x, y, z in (
        (0.7, 1.2, -0.22),
        (0.7, 1.2, 0.22),
        (0.64, 1.27, -0.1),
        (0.64, 1.27, 0.1),
        (0.78, 0.96, -0.2),
        (0.78, 0.96, 0.2),
    ):
        r.part("sphere", x, y, z, 0.08, 0.08, 0.08, eye, glow=not dead)
    # Fangs spread during windup and snap together on the strike.
    for side in (1, -1):
        with r.at(0.74, 0.8, side * 0.14, rx=side * fang * 0.4):
            r.part("cube", 0.04, -0.08, 0, 0.14, 0.2, 0.12, body)
            r.part("cone", 0.08, -0.26, 0, 0.07, 0.24, 0.07, (220, 210, 180), rx=math.pi)
    # Pedipalps.
    for side in (1, -1):
        with r.at(0.7, 0.85, side * 0.3, rz=-0.6 + math.sin(t * 3 + side) * 0.15):
            r.part("cube", 0.2, 0, 0, 0.4, 0.07, 0.07, body)


def _spider_leg(r, i, side, phase, amp, body, band, curl=0.0):
    """One leg, hip on the head-chest. Femur rises outward, tibia drops to a foot on the floor.
    `curl` (0..1) folds it up and in over the body, the way a dead spider's legs draw in."""
    hip_x = 0.55 - i * 0.22
    spread = (0.9, 0.35, -0.25, -0.8)[i]  # front legs reach forward, back legs trail
    swing = math.sin(phase) * 0.28 * amp
    lift = max(math.sin(phase + math.pi / 2), 0) * 0.3 * amp
    # The first frame turns local +X outward along the leg, the second raises the femur.
    with (
        r.at(hip_x, 0.92, side * 0.3, ry=-side * (math.pi / 2 - spread - swing)),
        r.at(0, 0, 0, rz=0.8 + lift + 0.9 * curl),
    ):
        r.part("cube", 0.55, 0, 0, 1.1, 0.12, 0.12, body)
        r.part("cube", 1.02, 0, 0, 0.16, 0.14, 0.14, band)
        with r.at(1.1, 0, 0, rz=-1.9 - lift * 0.5 - 0.9 * curl):
            r.part("cube", 0.5, 0, 0, 1.0, 0.1, 0.1, body)
            r.part("cube", 1.0, 0, 0, 0.12, 0.12, 0.12, band)
            with r.at(1.0, 0, 0, rz=-0.25):
                r.part("cube", 0.4, 0, 0, 0.8, 0.07, 0.07, body)


def npc(r, robe, skin=SKIN, hair=(70, 54, 40), t=0, hood=False, blade=False):
    sway = math.sin(t * 1.5) * 0.03
    with r.at(0, 0, 0, rz=sway):
        if hood:  # a deep hood that hides most of the face
            r.part("sphere", -0.05, 1.6, 0, 0.4, 0.42, 0.4, robe)
            r.part("cube", -0.12, 1.4, 0, 0.22, 0.2, 0.46, robe)
        if blade:  # a sheathed curved sword slung across the back
            with r.at(-0.3, 1.0, 0, rx=0.9):
                r.part("cube", 0, 0, 0, 0.06, 1.1, 0.08, (30, 26, 30))
                r.part("cube", 0, 0.62, 0, 0.05, 0.25, 0.05, (160, 30, 40))
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


def brazier(r, t, lit=True):
    r.part("cyl", 0, 0.45, 0, 0.12, 0.9, 0.12, IRON)
    r.part("cyl", 0, 0.95, 0, 0.6, 0.2, 0.6, IRON)
    if not lit:  # a cold bowl of grey ash and charred sticks
        r.part("cyl", 0, 1.06, 0, 0.5, 0.06, 0.5, ASH)
        for k in range(3):
            r.part("cube", 0, 1.1, 0, 0.42, 0.05, 0.05, (40, 32, 26), ry=k * 1.05)
        return
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


OAK = (96, 66, 40)


def lever(r, k, wall=True, wood=False):
    """A winch lever: an iron-banded oak beam pivoting in a notched iron quadrant on a dressed-stone
    block, with a toothed wheel beside it whose chain runs up into the wall. `k` (0..1) is how far
    it has been hauled: the beam swings from up-and-back to down-and-forward and the wheel turns.
    Mounted on a wall at local -X, or free-standing."""
    with r.at(0, 0, 0, s=1.2):
        if wood:
            _wood_lever(r, k, wall)
        else:
            _lever(r, k, wall)


def _wood_lever(r, k, wall):
    """The jungle's lever: a rough beam on a wooden axle through a split-log post, with a pegged
    timber quadrant and vine lashings, and a rope that runs up from its spindle into the wall."""
    bx = -0.5 if wall else -0.15
    rope = (170, 150, 100)
    r.part("cyl", bx, 0.12, 0, 0.7, 0.24, 0.7, BARK, tex="bark")  # the stump it stands on
    for z in (-0.16, 0.16):  # the two halves of the split post
        r.part("cube", bx, 0.68, z, 0.3, 1.0, 0.12, (110, 80, 50), tex="bark")
    r.part("cube", bx, 1.18, 0, 0.34, 0.08, 0.46, DARK_BARK)  # a cap lashed across the top
    for y in (0.45, 0.9):
        r.part("cube", bx, y, 0, 0.32, 0.06, 0.48, (70, 110, 46))  # vine bindings
    px, py = bx + 0.3, 1.0
    for i in range(5):  # pegs in an arc mark the beam's travel
        a = -0.9 + i * 0.45
        r.part(
            "cyl",
            px + math.sin(a) * 0.4,
            py + math.cos(a) * 0.4,
            0.2,
            0.05,
            0.12,
            0.05,
            (150, 116, 76),
            rx=math.pi / 2,
        )
    r.part("cyl", px, py, 0, 0.14, 0.5, 0.14, (124, 92, 58), rx=math.pi / 2)  # the axle
    with r.at(px, py, 0, rz=0.95 - 1.9 * k):
        r.part("cube", 0, 0.5, 0, 0.14, 1.05, 0.12, (126, 92, 58), tex="bark")
        r.part("cube", 0, 0.62, 0, 0.16, 0.08, 0.14, (70, 110, 46))  # vine grip wraps
        r.part("cube", 0, 0.78, 0, 0.16, 0.08, 0.14, (70, 110, 46))
        r.part("cube", 0, 1.05, 0, 0.1, 0.1, 0.32, (110, 80, 50))  # cross handle
    # The spindle winds the rope as the beam is hauled.
    with r.at(bx + 0.05, py, -0.36, rz=-k * 3.0):
        r.part("cyl", 0, 0, 0, 0.32, 0.22, 0.32, (124, 92, 58), rx=math.pi / 2)
        r.part("cyl", 0, 0, 0, 0.24, 0.24, 0.24, rope, rx=math.pi / 2)
    top = 2.2 if wall else 1.4
    cx = bx - 0.16 if wall else bx + 0.05
    length = top - py
    sag = 0.1 * k
    r.part("cube", cx + sag, py + length / 2, -0.36, 0.04, length, 0.04, rope)
    if wall:
        r.part("cube", -0.8, top, -0.36, 0.08, 0.14, 0.14, DARK_BARK)  # a peg where it enters the wall


def _lever(r, k, wall):
    bx = -0.5 if wall else -0.15
    r.part("cube", bx, 0.45, 0, 0.55, 0.9, 0.8, WHITE, tex="rough_stone")
    r.part("cube", bx, 0.93, 0, 0.62, 0.06, 0.86, (110, 106, 100))  # capstone
    px, py = bx + 0.32, 1.05  # the pivot
    for i in range(7):  # the notched quadrant
        a = -1.0 + i * (2.0 / 6)
        r.part(
            "cube", px + math.sin(a) * 0.36, py + math.cos(a) * 0.36, 0.12, 0.06, 0.1, 0.05, DARK_IRON, rz=-a
        )
        r.part(
            "cube", px + math.sin(a) * 0.36, py + math.cos(a) * 0.36, -0.12, 0.06, 0.1, 0.05, DARK_IRON, rz=-a
        )
    r.part("cyl", px, py, 0, 0.12, 0.34, 0.12, DARK_IRON, rx=math.pi / 2)  # axle
    with r.at(px, py, 0, rz=0.95 - 1.9 * k):
        r.part("cube", 0, 0.45, 0, 0.13, 0.95, 0.13, OAK)
        for y in (0.15, 0.62):  # iron bands, riveted
            r.part("cube", 0, y, 0, 0.13, 0.06, 0.13, IRON)
            r.part("cube", 0.07, y, 0, 0.02, 0.03, 0.03, BRASS)
        r.part("cube", 0, 0.88, 0, 0.09, 0.08, 0.09, IRON)
        r.part("cube", 0, 0.95, 0, 0.06, 0.06, 0.36, IRON)  # the cross-grip
        r.part("cyl", 0, 1.02, 0, 0.18, 0.04, 0.18, IRON, rx=math.pi / 2)  # ring pommel
    # The toothed wheel turns as the beam is hauled.
    with r.at(bx + 0.1, py, -0.42, rz=-k * 3.0):
        r.part("cyl", 0, 0, 0, 0.5, 0.08, 0.5, DARK_IRON, rx=math.pi / 2)
        for i in range(8):
            a = i * math.pi / 4
            r.part("cube", math.cos(a) * 0.27, math.sin(a) * 0.27, 0, 0.08, 0.08, 0.06, IRON, rz=a)
        r.part("cube", 0, 0, 0.05, 0.42, 0.05, 0.03, OAK)
        r.part("cube", 0, 0, 0.05, 0.05, 0.42, 0.03, OAK)
    # Its chain runs up into the wall (or into a ring on the block); slack once hauled.
    top = 2.2 if wall else 1.0
    cx = bx - 0.18 if wall else bx + 0.1
    links = max(int((top - py) / 0.14), 1) if wall else 0
    for i in range(links):
        y = py + 0.25 + i * 0.14
        sag = math.sin(i / max(links - 1, 1) * math.pi) * 0.12 * k
        r.part("cube", cx + sag, y, -0.42, 0.03, 0.15, 0.07, IRON, ry=0 if i % 2 else math.pi / 2)
    if wall:
        r.part("cube", -0.8, top, -0.42, 0.06, 0.18, 0.18, DARK_IRON)  # where it vanishes into the wall


def lift(r, t, moving, chain_h):
    """A chain lift: an oak deck in an iron frame, hung from four chains that run up to a pulley
    beam under the shaft's ceiling. Riding, the chains shiver."""
    r.part("cube", 0, -0.08, 0, 1.92, 0.14, 1.92, WHITE, tex="wood_plank")
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # the iron frame
        r.part("cube", sx * 0.94, -0.05, sz * 0.94, 0.1 if sx else 1.98, 0.18, 0.1 if sz else 1.98, DARK_IRON)
    for z in (-0.5, 0.0, 0.5):  # the cross straps
        r.part("cube", 0, 0.005, z, 1.86, 0.02, 0.08, IRON)
    shiver = math.sin(t * 30) * 0.01 if moving else 0.0
    link = 0.45
    links = min(max(int(chain_h / link), 1), 40)
    for cx, cz in ((0.85, 0.85), (0.85, -0.85), (-0.85, 0.85), (-0.85, -0.85)):
        r.part("cube", cx, 0.1, cz, 0.14, 0.2, 0.14, DARK_IRON)  # the shackle
        for i in range(links):
            r.part(
                "cube",
                cx + shiver,
                0.2 + (i + 0.5) * link,
                cz,
                0.04,
                link,
                0.1,
                IRON,
                ry=0 if i % 2 else 1.57,
            )
    r.part("cube", 0, chain_h, 0, 1.9, 0.25, 0.3, OAK)  # the pulley beam
    for cx in (-0.85, 0.85):
        r.part("cyl", cx, chain_h - 0.2, 0, 0.35, 0.12, 0.35, DARK_IRON, rx=math.pi / 2)


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


def jungle_tree(r, seed, t):
    """Broad-leaved tree with buttress roots and hanging vines."""
    h = 3.4 + (seed % 4) * 0.35
    r.part("cyl", 0, h * 0.45, 0, 0.42, h * 0.9, 0.42, BARK, tex="bark")
    for i in range(4):
        a = i * math.pi / 2 + seed * 0.7
        r.part("cube", math.cos(a) * 0.32, 0.35, math.sin(a) * 0.32, 0.5, 0.7, 0.1, DARK_BARK, ry=-a, rz=0.3)
    sway = math.sin(t * 0.7 + seed) * 0.03
    with r.at(0, h * 0.9, 0, rz=sway):
        r.part("sphere", 0, 0, 0, 3.2, 1.0, 3.0, DARK_LEAF)
        r.part("sphere", 0.5, 0.45, -0.4, 2.2, 0.8, 2.0, LEAF)
        r.part("sphere", -0.6, 0.3, 0.6, 1.8, 0.7, 1.9, (48, 90, 40))
        for k in range(5):
            a = k * 1.3 + seed
            vx = math.cos(a) * 1.1
            vz = math.sin(a) * 1.1
            length = 1.0 + (k + seed) % 3 * 0.5
            r.part("cube", vx, -0.3 - length / 2, vz, 0.05, length, 0.05, (60, 96, 40))


def fungus(r, seed, t):
    """A cluster of glowing toadstools."""
    pulse = 1 + math.sin(t * 1.3 + seed) * 0.06
    for k, (x, z, h) in enumerate(((0, 0, 0.55), (0.25, 0.18, 0.35), (-0.2, 0.22, 0.3), (0.1, -0.25, 0.25))):
        r.part("cyl", x, h / 2, z, 0.08, h, 0.08, (190, 200, 170))
        d = (0.42 - k * 0.06) * pulse
        r.part("sphere", x, h, z, d, d * 0.45, d, (80, 220, 170), glow=True)


def bonfire(r, t, lit=True):
    """A ring of rough stones round a stack of crossed logs: blazing, or cold grey ash once dead."""
    for i in range(9):
        a = i * math.tau / 9
        d = 0.24 + (i * 7 % 3) * 0.04
        r.part(
            "sphere",
            math.cos(a) * 0.62,
            0.1,
            math.sin(a) * 0.62,
            d * 1.2,
            d,
            d,
            (92, 88, 80),
            tex="rough_stone",
        )
    r.part("cyl", 0, 0.03, 0, 1.0, 0.06, 1.0, ASH if not lit else (60, 40, 30))
    char = (34, 26, 20) if not lit else (70, 46, 28)
    for k in range(4):  # the logs, leaning in to a point
        a = k * math.pi / 2 + 0.4
        with r.at(math.cos(a) * 0.22, 0.28, math.sin(a) * 0.22, ry=-a, rz=0.9):
            r.part("cyl", 0, 0, 0, 0.12, 0.75, 0.12, char, tex="bark")
    if not lit:
        return
    for k in range(3):
        flick = 1 + math.sin(t * (9 + k * 3) + k) * 0.15
        h = (0.9 - k * 0.2) * flick
        r.part(
            "cone",
            (k - 1) * 0.12,
            0.35 + h / 2,
            (k % 2) * 0.08,
            0.36 - k * 0.07,
            h,
            0.36 - k * 0.07,
            EMBER,
            glow=True,
        )
    r.part("cone", 0, 0.55, 0, 0.2, 0.7 * (1 + math.sin(t * 15) * 0.1), 0.2, (255, 230, 140), glow=True)
    for k in range(3):  # sparks drifting up
        u = (t * 0.7 + k / 3) % 1
        r.part(
            "cube",
            math.sin(k * 2 + t) * 0.2,
            0.9 + u * 1.4,
            math.cos(k * 3 + t) * 0.2,
            0.04,
            0.04,
            0.04,
            EMBER,
            glow=True,
        )


def giant_mushroom(r, seed, t):
    """A toadstool taller than a man: a pale fibrous stem, a ragged skirt and a broad cap that
    glows violet from the gills."""
    h = 2.3 + (seed % 3) * 0.25
    lean = ((seed % 5) - 2) * 0.04
    with r.at(0, 0, 0, rz=lean):
        r.part("cyl", 0, h / 2, 0, 0.42, h, 0.42, (200, 190, 170))
        r.part("cyl", 0, 0.15, 0, 0.6, 0.3, 0.6, (170, 160, 140))  # swollen foot
        r.part("cyl", 0, h * 0.7, 0, 0.62, 0.08, 0.62, (220, 210, 196))  # the skirt
        pulse = 1 + math.sin(t * 1.1 + seed) * 0.05
        r.part("sphere", 0, h + 0.1, 0, 2.4, 0.7, 2.4, (120, 70, 140))
        r.part("cyl", 0, h - 0.05, 0, 2.1 * pulse, 0.08, 2.1 * pulse, (170, 120, 255), glow=True)  # gills
        for k in range(5):  # pale spots on the cap
            a = k * 1.3 + seed
            r.part(
                "sphere", math.cos(a) * 0.6, h + 0.38, math.sin(a) * 0.6, 0.22, 0.08, 0.22, (230, 220, 240)
            )


def shelf_fungus(r, seed, t):
    """Bracket fungi stepping up the wall at local -X, their undersides glowing teal."""
    pulse = 1 + math.sin(t * 0.9 + seed) * 0.08
    for k in range(4):
        y = 0.7 + k * 0.42 + (seed + k) % 3 * 0.08
        z = ((seed * 3 + k * 5) % 7 - 3) * 0.14
        w = 0.6 - k * 0.08
        r.part("sphere", -0.86, y, z, w * 0.75, 0.12, w, (150, 120, 84))
        r.part("cyl", -0.86, y - 0.06, z, w * 0.6 * pulse, 0.03, w * 0.8 * pulse, (90, 230, 210), glow=True)


def mushrooms(r, seed):
    """A small clump of brown and red caps in the leaf litter. They don't glow."""
    for k in range(5):
        a = k * 2.4 + seed
        d = 0.18 + (k * 13 + seed) % 4 * 0.06
        x, z = math.cos(a) * (0.15 + k * 0.08), math.sin(a) * (0.15 + k * 0.08)
        h = 0.12 + (k + seed) % 3 * 0.08
        r.part("cyl", x, h / 2, z, 0.05, h, 0.05, (220, 210, 190))
        cap = (150, 40, 30) if (k + seed) % 3 == 0 else (130, 92, 56)
        r.part("sphere", x, h, z, d, d * 0.5, d, cap)


def totem(r, seed, t):
    """A carved post: stacked faces with staring painted eyes, crowned by a ring of feathers."""
    wood = (104, 76, 50)
    r.part("cyl", 0, 1.2, 0, 0.5, 2.4, 0.5, wood, tex="bark")
    for k in range(3):
        y = 0.5 + k * 0.72
        r.part("cube", 0.24, y, 0, 0.1, 0.5, 0.5, (88, 62, 40))  # the face plank
        for z in (-0.12, 0.12):
            r.part("cube", 0.3, y + 0.08, z, 0.03, 0.08, 0.1, (230, 220, 190))
            r.part("cube", 0.31, y + 0.08, z, 0.03, 0.05, 0.04, (30, 24, 20))
        r.part("cube", 0.3, y - 0.12, 0, 0.03, 0.06, 0.3, (170, 50, 40) if k % 2 == 0 else (60, 120, 140))
        r.part("cube", 0.3, y + 0.2, 0, 0.03, 0.04, 0.4, (200, 170, 60))
    sway = math.sin(t * 1.4 + seed) * 0.08
    for k in range(6):
        a = k * math.tau / 6
        with r.at(math.cos(a) * 0.2, 2.45, math.sin(a) * 0.2, ry=-a, rz=-0.4 + sway):
            r.part("cube", 0.15, 0.2, 0, 0.06, 0.45, 0.12, (180, 60, 40) if k % 2 else (230, 220, 200))


def cave_mouth(r, t):
    """A cleft in the rock on the -X edge: a rough arch of boulders over a black opening, hung with
    roots and moss. Cold air seems to breathe out of it."""
    rock = (110, 104, 94)
    r.part("cube", -0.95, 1.3, 0, 0.1, 2.6, 1.6, (6, 6, 8))  # the dark beyond
    for z in (-0.95, 0.95):
        r.part("cube", -0.8, 1.2, z, 0.5, 2.4, 0.45, rock, tex="cliff_rock", rz=0.05 * z)
    r.part("cube", -0.8, 2.55, 0, 0.6, 0.5, 2.3, rock, tex="cliff_rock", rx=0.08)
    for k, (y, z, d) in enumerate(((0.3, -0.7, 0.55), (0.25, 0.8, 0.5), (2.8, 0.5, 0.6), (2.75, -0.6, 0.5))):
        r.part("sphere", -0.6, y, z, d, d * 0.8, d, rock, tex="cliff_rock")
        r.part("cube", -0.55, y + d * 0.35, z, d * 0.7, 0.06, d * 0.7, MOSS if k % 2 else (56, 92, 44))
    for k in range(7):  # roots trailing over the lip
        z = -0.75 + k * 0.25
        length = 0.4 + (k * 29 % 5) * 0.16
        sway = math.sin(t * 0.8 + k) * 0.03
        r.part("cube", -0.6, 2.3 - length / 2, z + sway, 0.05, length, 0.05, (80, 60, 40))


def bridge(r, lowered):
    """A drawbridge of lashed timbers, hinged on the -X edge of its tile. Raised, it stands upright
    against the far bank; `lowered` (0..1) swings it down flat across the gap (deck at y=0)."""
    k = _ease_in(lowered)
    with r.at(-1.0, 0, 0, rz=(1 - k) * math.pi / 2):
        for i in range(5):
            r.part("cube", 1.0, -0.06, -0.8 + i * 0.4, 2.0, 0.12, 0.36, (112, 82, 52), tex="wood_plank")
        for z in (-0.95, 0.95):  # side beams, lashed with rope
            r.part("cube", 1.0, -0.14, z, 2.0, 0.16, 0.12, DARK_BARK)
            for x in (0.3, 1.0, 1.7):
                r.part("cube", x, -0.12, z, 0.08, 0.2, 0.16, (170, 150, 100))
    # Hinge posts and the ropes that haul it, on the near bank.
    for z in (-1.0, 1.0):
        r.part("cyl", -1.0, 0.6, z, 0.16, 1.4, 0.16, DARK_BARK, tex="bark")
        reach = 2.0 * math.cos((1 - k) * math.pi / 2)
        top = 2.0 * math.sin((1 - k) * math.pi / 2)
        length = math.hypot(reach, 1.3 - top) or 0.01
        ang = math.atan2(1.3 - top, reach)
        with r.at(-1.0, 1.3, z, rz=-ang):
            r.part("cube", length / 2, 0, 0, length, 0.03, 0.03, (170, 150, 100))


def vine_door(r, t):
    """Overgrown doorway: a dark door in a timber frame, choked with vines. The door is on the -X edge."""
    frame = (78, 54, 34)
    r.part("cube", -0.94, 1.15, 0, 0.1, 2.3, 1.5, WHITE, tex="door_wood")
    r.part("cube", -0.9, 1.15, 0, 0.04, 2.1, 1.3, (26, 20, 16))
    r.part("cube", -0.85, 0.15, 0, 0.3, 0.3, 1.9, frame)
    for z in (-0.82, 0.82):
        r.part("cube", -0.86, 1.25, z, 0.22, 2.5, 0.22, frame)
    r.part("cube", -0.86, 2.5, 0, 0.26, 0.24, 1.9, frame)
    # Vines pour over the lintel and down the frame.
    for k in range(9):
        z = -0.85 + k * 0.21
        length = 0.5 + (k * 37 % 7) * 0.22
        sway = math.sin(t * 1.2 + k) * 0.03
        r.part("cube", -0.72, 2.45 - length / 2, z + sway, 0.05, length, 0.06, (54, 96, 40))
        r.part("cube", -0.7, 2.45 - length, z + sway, 0.1, 0.12, 0.16, (76, 128, 52))
    for y, z, d in (
        (2.6, -0.6, 0.6),
        (2.55, 0.1, 0.7),
        (2.65, 0.7, 0.55),
        (1.6, 0.9, 0.45),
        (0.9, -0.9, 0.5),
    ):
        r.part("sphere", -0.78, y, z, 0.35, d, d, (48, 92, 38))
    # Overgrowth spilling onto the facade on both sides of the doorway (the +X edge of the tile).
    for side in (1, -1):
        for k, (z, y, d) in enumerate(((1.35, 3.3, 0.9), (2.2, 3.7, 1.0), (1.6, 2.2, 0.6), (2.6, 1.2, 0.7))):
            r.part("sphere", 1.04, y, side * z, 0.2, d, d * 1.2, LEAF if k % 2 else DARK_LEAF)
        for k in range(4):
            z = side * (1.2 + k * 0.45)
            length = 1.2 + (k * 3 % 4) * 0.5
            r.part("cube", 1.04, 3.6 - length / 2, z, 0.05, length, 0.06, (54, 96, 40))
    r.part("sphere", 1.04, 3.4, 0, 0.2, 0.7, 1.6, DARK_LEAF)
    # Roots crawling out over the threshold.
    for k, z in enumerate((-0.6, -0.1, 0.5)):
        r.part("cube", -0.45 + k * 0.1, 0.06, z, 0.9, 0.1, 0.1, (70, 52, 34), ry=0.3 - k * 0.3)


def raft(r, t):
    """Four lashed logs, deck on top at y=0."""
    bob = math.sin(t * 1.6) * 0.03
    with r.at(0, bob, 0, rx=math.sin(t * 1.1) * 0.02):
        for z in (-0.68, -0.23, 0.23, 0.68):
            r.part("cyl", 0, -0.12, z, 0.44, 1.85, 0.44, BARK, tex="bark", rz=math.pi / 2)
        for x in (-0.6, 0.6):
            r.part("cube", x, 0.08, 0, 0.12, 0.06, 1.85, (140, 112, 70))
        r.part("cyl", 0.7, 0.5, 0.7, 0.08, 1.0, 0.08, DARK_BARK)
        r.part("cube", 0.7, 1.0, 0.7, 0.12, 0.06, 0.12, (150, 120, 80))


def plank(r, creak):
    """Rotten boardwalk section over the water. It tilts and darkens as it gives way."""
    tilt = creak * 0.12
    rot = (int(96 - 30 * creak), int(84 - 20 * creak), 52)
    with r.at(0, 0, 0, rz=tilt, rx=-tilt * 0.5):
        for k, z in enumerate((-0.6, 0.0, 0.6)):
            r.part(
                "cube", 0, -0.05, z + (k - 1) * 0.02, 1.9, 0.1, 0.52, rot, tex="wood_plank", ry=(k - 1) * 0.04
            )
        r.part("cube", 0.5, 0.02, -0.3, 0.3, 0.04, 0.25, MOSS)
    for x, z in ((-0.85, -0.85), (0.85, -0.85), (-0.85, 0.85), (0.85, 0.85)):
        r.part("cyl", x, -0.4, z, 0.14, 0.9, 0.14, DARK_BARK)


def ledge(r, creak, seed):
    """A cracked shelf of rock jutting over the chasm, deck at y=0. It shudders as it gives way."""
    rock = (104, 98, 86)
    with r.at(0, 0, 0, rz=creak * 0.06, rx=-creak * 0.04):
        r.part("cube", 0, -0.3, 0, 1.9, 0.6, 1.9, rock, tex="cliff_rock")
        r.part("cone", 0.1, -1.1, 0.05, 1.5, 1.0, 1.5, (84, 78, 70), tex="cliff_rock", rx=math.pi)
        r.part("cube", -0.4 + seed % 3 * 0.3, 0.02, 0.5, 0.5, 0.06, 0.4, MOSS)
        # The crack widens as the ledge creaks.
        r.part("cube", 0.2, 0.01, 0, 0.05 + creak * 0.08, 0.04, 1.8, (20, 18, 16), ry=0.3)
        if creak > 0.2:
            for k in range(3):
                r.part(
                    "cube",
                    -0.7 + k * 0.6,
                    -0.65 - creak * 0.4 * (k + 1),
                    0.8 - k * 0.5,
                    0.12,
                    0.12,
                    0.12,
                    rock,
                )


def boards(r, creak, broken=False):
    """Rotten cabin floorboards over a cellar, deck at y=0. Once broken they lie as a splintered heap."""
    rot = (int(100 - 34 * creak), int(76 - 24 * creak), 46)
    if broken:
        for k in range(5):
            r.part(
                "cube", -0.6 + k * 0.3, 0.05 + (k % 2) * 0.08, 0.1 * (k - 2), 1.2, 0.08, 0.3, rot, ry=k * 0.9
            )
        return
    for k in range(4):
        sag = creak * 0.05 * (1 if k % 2 else -1)
        r.part("cube", 0, -0.05 + sag, -0.72 + k * 0.48, 1.98, 0.1, 0.44, rot, tex="wood_plank")
    r.part("cube", 0.4, 0.01, 0.2, 0.3, 0.02, 0.25, (40, 30, 22))  # a dark rot stain


def rolling_log(r, spin):
    """A felled trunk rolling downhill along its local x axis; centred on its axis."""
    with r.at(0, 0, 0, rx=spin):
        r.part("cyl", 0, 0, 0, 0.7, 1.7, 0.7, BARK, tex="bark", rz=math.pi / 2)
        r.part("cyl", 0, 0.36, 0.0, 0.12, 0.5, 0.12, DARK_BARK)  # a snapped branch stub
    for x in (-0.86, 0.86):
        r.part("cyl", x, 0, 0, 0.6, 0.04, 0.6, (176, 140, 92), rz=math.pi / 2)  # pale cut ends


def log_pile(r, stock, t, strain):
    """A woodcutters' log rack at the top of a slope (+z is downhill): four corner posts on sill
    beams, side rails and a lean-to plank roof, with a pyramid of felled logs (`stock` of
    terrain.PILE_SLOTS) held in by a roped chock across the front. The rope shudders harder as the
    next log works loose (`strain` 0..1); once the rack is spent the rope hangs cut and the chock
    lies on the ground."""
    timber = (104, 76, 50)
    pale = (176, 140, 92)
    # Sill beams the logs rest on, and the four corner posts.
    for x in (-0.72, 0.72):
        r.part("cube", x, 0.1, 0, 0.26, 0.2, 2.0, timber, tex="bark")
    for x in (-0.98, 0.98):
        for z in (-0.95, 0.95):
            r.part("cube", x, 1.25, z, 0.18, 2.5, 0.18, DARK_BARK, tex="bark")
        # Side rails keep the logs from spilling sideways, with a cross brace.
        for y in (0.7, 1.5):
            r.part("cube", x, y, 0, 0.1, 0.12, 1.9, timber)
        r.part("cube", x, 1.25, 0, 0.08, 0.1, 2.5, timber, rx=0.75)
    # Tie beams and a lean-to roof of rough planks, higher at the back.
    for z in (-0.95, 0.95):
        r.part("cube", 0, 2.45 if z < 0 else 2.2, z, 2.1, 0.16, 0.2, timber)
    for k in range(5):
        x = -0.84 + k * 0.42
        r.part("cube", x, 2.42, 0, 0.4, 0.06, 2.4, (92, 68, 44), tex="wood_plank", rx=0.12, ry=(k - 2) * 0.01)
    r.part("cube", 0.3, 2.47, -0.4, 0.5, 0.04, 0.4, MOSS, rx=0.12)

    # The logs, bottom row first; the top one is next to go and rocks against the rope.
    for k, (z, y) in enumerate(terrain.PILE_SLOTS[:stock]):
        rock = math.sin(t * 30) * 0.05 * strain if k == stock - 1 else 0.0
        with r.at(0, y, z + rock):
            r.part("cyl", 0, 0, 0, 0.54, 1.8, 0.54, BARK, tex="bark", rz=math.pi / 2)
            for x in (-0.91, 0.91):
                r.part("cyl", x, 0, 0, 0.46, 0.03, 0.46, pale, rz=math.pi / 2)
                r.part("cyl", x * 1.002, 0, 0, 0.12, 0.035, 0.12, (140, 104, 64), rz=math.pi / 2)

    # The chock: a short log pegged across the front of the bottom row, lashed to the posts.
    rope = (150, 132, 92)
    if stock:
        shake = math.sin(t * 24) * 0.03 * strain
        r.part("cyl", 0, 0.32, 1.1, 0.3, 2.0, 0.3, DARK_BARK, tex="bark", rz=math.pi / 2)
        for y in (0.55, 1.05):
            r.part("cube", 0, y + shake, 1.03, 1.96, 0.04, 0.04, rope)
        r.part("cube", 0, 1.5 + shake, 0.85, 0.04, 0.04, 0.5, rope, rx=0.9)
    else:
        r.part("cyl", 0.3, 0.15, 1.35, 0.3, 2.0, 0.3, DARK_BARK, tex="bark", rz=math.pi / 2, ry=0.4)
        for x in (-0.98, 0.98):
            r.part("cube", x, 0.75, 1.06, 0.04, 0.45, 0.04, rope, rz=0.15 * x)
    # Wood chips and a forgotten axe beside the rack.
    r.part("cube", -1.2, 0.03, -0.6, 0.3, 0.04, 0.2, pale, ry=0.6)
    r.part("cube", -1.15, 0.03, 0.3, 0.2, 0.04, 0.14, pale, ry=-0.4)
    r.part("cyl", 1.25, 0.35, -0.5, 0.06, 0.8, 0.06, (110, 80, 50), rz=0.6)
    r.part("cube", 1.48, 0.66, -0.5, 0.08, 0.2, 0.26, IRON, rz=0.6)


def spore_pod(r, t, cloud, phase):
    """A swollen puffball that slowly fills, then bursts into a drifting cloud of spores."""
    swell = 0.55 + 0.35 * (phase if cloud is None else 0.2)
    r.part("cyl", 0, 0.15, 0, 0.18, 0.3, 0.18, (150, 140, 110))
    r.part("sphere", 0, 0.3 + swell * 0.4, 0, swell, swell * 0.85, swell, (170, 162, 96))
    for k in range(5):
        a = k * 1.26
        r.part(
            "sphere",
            math.cos(a) * swell * 0.4,
            0.35 + swell * 0.6,
            math.sin(a) * swell * 0.4,
            0.12,
            0.1,
            0.12,
            (120, 110, 60),
        )
    if cloud is None:
        return
    for k in range(10):
        a = k * 2.4 + t * 0.6
        d = 0.3 + cloud * (1.0 + (k % 3) * 0.3)
        size = 0.4 + cloud * 0.8 * (1 - cloud * 0.5)
        y = 0.6 + cloud * 1.2 + (k % 4) * 0.25
        r.part(
            "sphere", math.cos(a) * d, y, math.sin(a) * d, size, size * 0.8, size, (196, 206, 110), glow=True
        )


def thorn_plant(r, seed, t, rise):
    """A spiked carnivorous plant that carpets a thorn floor: a rosette of fleshy, saw-edged leaves
    around a sheaf of red spikes. The spikes stab upward (`rise` 0..1) when something steps in."""
    flesh = (88, 58, 48)
    for k in range(7):
        a = k * 2 * math.pi / 7 + seed * 0.9
        with r.at(math.cos(a) * 0.2, 0.05, math.sin(a) * 0.2, ry=-a, rz=0.25 + (k % 2) * 0.15):
            r.part("sphere", 0.4, 0, 0, 0.85, 0.08, 0.3, (60, 92, 46) if k % 2 else (74, 84, 40))
            for j in range(3):
                r.part("cone", 0.2 + j * 0.25, 0.04, 0.15, 0.04, 0.12, 0.04, (200, 180, 140), rx=-0.9)
    r.part("sphere", 0, 0.08, 0, 0.5, 0.18, 0.5, flesh)
    jab = 0.25 + 0.75 * rise
    for k in range(8):
        a = k * 2.4 + seed
        d = 0.12 + (k % 3) * 0.08
        h = (0.55 + (k * 5 % 4) * 0.12) * jab
        sway = math.sin(t * 1.3 + k) * 0.04 * (1 - rise)
        tilt = 0.25 * (k % 3) / 2
        with r.at(math.cos(a) * d, 0.1, math.sin(a) * d, ry=-a, rz=-tilt + sway):
            r.part("cone", 0, h / 2, 0, 0.07, h, 0.07, (150, 40, 44))
            r.part("cone", 0, h * 0.95, 0, 0.03, h * 0.18, 0.03, (236, 220, 180))


def rope(r, t):
    with r.at(0, 3.2, 0, rz=math.sin(t * 0.8) * 0.04):
        r.part("cyl", 0, -1.6, 0, 0.07, 3.2, 0.07, (150, 120, 80))
        r.part("cube", 0, -3.0, 0, 0.16, 0.12, 0.16, (130, 100, 70))
    r.part("cyl", 0, 0.05, 0, 1.0, 0.1, 1.0, (40, 40, 44))


def flare(r, rgb, k):
    """A tongue of Pyre's fire: a ragged glowing blob that swells, then gutters as `k` runs to 0."""
    size = 0.15 + 0.35 * math.sin(min(k, 1.0) * math.pi) ** 0.5
    r.part("sphere", 0, 0, 0, size, size * 1.3, size, rgb, glow=True)
    r.part("cone", 0, size * 0.6, 0, size * 0.6, size * 1.4, size * 0.6, (255, 220, 120), glow=True)


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


def secret_wall(r, height, open_t, tex="stone_brick"):
    """An illusory wall: a full tile that matches the real walls (brick in the keep, a curtain of
    vines in the jungle). Struck, it sinks and fades."""
    if open_t >= 1.0:
        return
    k = 1.0 - open_t
    h = height * k
    w = 2.0 * (0.6 + 0.4 * k)
    # Stacked 2 m blocks, so the texture repeats every 2 m like the map's own walls do.
    y = 0.0
    while y < h - 1e-3:
        seg = min(2.0 * k, h - y)
        r.part("cube", 0, y + seg / 2, 0, w, seg, w, WHITE, tex=tex)
        y += seg


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


def cocoon(r, seed, broken=False):
    """A silk-wrapped bundle, the Loom Mother's larder, lashed to the floor with strands.
    Cut open, it is a torn husk with something's leftovers inside."""
    silk = (222, 218, 204)
    with r.at(0, 0, 0, ry=seed * 1.1):
        if broken:
            for k in range(4):
                a = k * 1.6
                r.part("sphere", math.cos(a) * 0.3, 0.12, math.sin(a) * 0.2, 0.5, 0.18, 0.3, silk, ry=a)
            r.part("sphere", 0.05, 0.08, 0, 0.22, 0.2, 0.2, BONE)  # a small skull among the shreds
            return
        tilt = 0.25 + seed % 3 * 0.15
        with r.at(0, 0.42, 0, rz=tilt):
            r.part("sphere", 0, 0, 0, 0.62, 1.05, 0.58, silk)
            for k in range(5):  # wound strands
                r.part("cyl", 0, -0.4 + k * 0.2, 0, 0.64, 0.03, 0.6, (196, 192, 180), rz=0.25 * (k % 2 - 0.5))
            r.part("sphere", 0.12, 0.38, 0.1, 0.12, 0.16, 0.12, (90, 70, 60))  # a shape pressing through
        for k in range(3):  # anchor threads down to the floor
            a = k * 2.1 + seed
            r.part("cube", math.cos(a) * 0.45, 0.06, math.sin(a) * 0.45, 0.7, 0.02, 0.02, silk, ry=-a)


def frog_idol(r, croak):
    """A squat stone frog on a mossy rock by the water. Patted, its throat swells and it croaks."""
    stone = (110, 116, 102)
    swell = math.sin(min(croak, 1.0) * math.pi * 3) * 0.5 + 0.5 if croak > 0 else 0.0
    r.part("sphere", 0, 0.18, 0, 1.1, 0.36, 0.95, (78, 82, 70), tex="rough_stone")
    r.part("sphere", -0.1, 0.36, 0, 0.42, 0.12, 0.38, MOSS)
    with r.at(0, 0.36, 0):
        r.part("sphere", 0, 0.24, 0, 0.62, 0.42, 0.6, stone, tex="rough_stone")  # body
        r.part("sphere", 0.2, 0.42, 0, 0.42, 0.3, 0.46, stone, tex="rough_stone")  # head
        for z in (-0.16, 0.16):
            r.part("sphere", 0.26, 0.58, z, 0.14, 0.14, 0.14, stone)  # eye bumps
            r.part("sphere", 0.32, 0.6, z, 0.06, 0.06, 0.06, (30, 34, 26))
            r.part("cube", 0.22, 0.04, z * 1.9, 0.3, 0.08, 0.14, stone, ry=z * 2)  # front feet
            r.part("sphere", -0.18, 0.08, z * 2.2, 0.36, 0.14, 0.2, stone)  # haunches
        r.part("cube", 0.4, 0.34, 0, 0.02, 0.02, 0.3, (30, 34, 26))  # wide stone smile
        d = 0.12 + 0.2 * swell
        r.part("sphere", 0.33, 0.25, 0, d, d * 0.9, d * 1.3, (150, 156, 132))  # throat sac
        r.part("sphere", -0.05, 0.47, 0.1, 0.2, 0.05, 0.2, MOSS)


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
        ember_crest(r, (200, 180, 140))


def ember_crest(r, rgb):
    """The keep's crest, stitched on its banners: a teardrop flame (the ember) held inside a ring,
    with three sparks rising above it. Drawn flat on the cloth (its face is +X)."""
    cy = -0.82
    r.part("sphere", 0.02, cy - 0.06, 0, 0.02, 0.17, 0.17, rgb)  # the flame's round belly
    r.part("cone", 0.02, cy + 0.08, 0, 0.02, 0.3, 0.17, rgb)  # and its pointed tongue
    r.part("sphere", 0.025, cy - 0.06, 0, 0.02, 0.07, 0.07, (40, 30, 30))  # its dark heart
    for i in range(12):  # the ring
        a = i * math.pi / 6
        r.part("cube", 0.02, cy + math.cos(a) * 0.27, math.sin(a) * 0.27, 0.02, 0.05, 0.15, rgb, rx=a)
    for z, y in ((-0.16, -0.38), (0.0, -0.32), (0.16, -0.38)):  # sparks
        r.part("cube", 0.02, y, z, 0.02, 0.06, 0.06, rgb, rx=0.785)


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


SPELL_ORB = {
    "flame": (255, 120, 40),
    "mend": (120, 230, 140),
    "lumen": (210, 220, 255),
    "venom": (120, 210, 60),
    "veil": (200, 210, 215),
    "pyre": (255, 90, 30),
}


def spell_orb(r, id_, t):
    """Inventory preview for a known spell: a glowing orb in the spell's colour."""
    rgb = SPELL_ORB.get(id_, WHITE)
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


def _ease(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def _ease_in(k):
    k = min(max(k, 0.0), 1.0)
    return k * k


# --- first-person view ----------------------------------------------------------------------
#
# Camera space: +X forward, +Y up, +Z right. A weapon is posed by (x, y, z, rx, rz) around a rest
# pose; rz tilts the blade back over the shoulder (+) or forward and down (-), rx rolls it to the
# right (+) or left (-). Each attack motion is three key poses (offsets from rest):
#   wind  - drawn back, reached a little before the blow lands,
#   strike - where the blow lands (at the attack's hit_at),
#   follow - carried through past the target,
# then it eases back to rest. The wind -> strike leg accelerates, so swings snap rather than float.

REST = (0.0, 0.0, 0.0, 0.0, 0.0)
MOTIONS = {
    "slash": (
        (-0.05, 0.12, 0.12, 0.9, 0.5),
        (0.12, 0.0, -0.15, -0.6, -1.2),
        (0.05, -0.12, -0.35, -1.3, -1.0),
    ),
    "sweep": ((0.0, 0.03, 0.3, 1.0, -0.4), (0.05, 0.05, -0.15, -0.6, -1.0), (0.0, 0.0, -0.5, -1.5, -0.6)),
    "chop": ((-0.05, 0.14, 0.0, 0.0, 0.6), (0.15, 0.0, -0.1, 0.0, -1.2), (0.12, -0.08, -0.1, 0.0, -1.5)),
    "slam": ((-0.08, 0.2, -0.05, 0.0, 0.9), (0.15, -0.2, -0.12, 0.0, -1.4), (0.15, -0.3, -0.12, 0.0, -1.6)),
    "thrust": (
        (-0.22, 0.08, -0.2, 0.0, -1.15),
        (0.45, 0.08, -0.25, 0.0, -1.15),
        (0.4, 0.06, -0.25, 0.0, -1.1),
    ),
    "stab": ((-0.08, 0.04, -0.1, 0.0, -0.9), (0.3, 0.05, -0.15, 0.0, -1.1), (0.22, 0.04, -0.15, 0.0, -1.0)),
    "lash": ((-0.05, 0.15, 0.05, 0.4, 0.6), (0.05, 0.05, -0.15, -0.4, -1.6), (0.0, -0.05, -0.2, -0.8, -1.3)),
    "flick": ((0.0, -0.05, -0.25, -0.9, -0.6), (0.1, 0.1, 0.05, 0.6, -0.9), (0.05, 0.15, 0.2, 1.1, -0.4)),
    "bash": ((-0.1, 0.1, 0.05, 0.3, 0.4), (0.25, 0.0, -0.1, -0.2, -0.9), (0.2, -0.05, -0.12, -0.3, -1.1)),
    "hew": ((-0.08, 0.16, 0.15, 0.6, 0.7), (0.15, -0.05, -0.15, -0.4, -1.3), (0.1, -0.15, -0.3, -0.7, -1.5)),
    "draw": ((-0.05, 0.0, -0.15, -0.25, -1.0), (0.15, 0.05, 0.25, 0.9, -1.0), (0.05, 0.12, 0.4, 1.4, -0.6)),
    "snare": ((-0.1, 0.25, 0.1, 0.6, 0.9), (0.1, 0.0, -0.1, -0.3, -1.7), (-0.15, -0.05, 0.0, -0.2, -0.6)),
    "leap": ((-0.05, 0.25, 0.0, 0.0, 1.0), (0.25, -0.25, -0.1, 0.0, -1.5), (0.2, -0.3, -0.1, 0.0, -1.6)),
}


def _lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


def _motion(motion, p, hit_at=0.4):
    """Pose offsets (dx, dy, dz, rx, rz) for one attack motion at phase p (0..1), landing at hit_at."""
    wind, strike, follow = MOTIONS.get(motion, MOTIONS["slash"])
    wind_at = hit_at * 0.7
    follow_at = hit_at + (1 - hit_at) * 0.35
    if p < wind_at:
        return _lerp(REST, wind, _ease(p / wind_at))
    if p < hit_at:
        return _lerp(wind, strike, _ease_in((p - wind_at) / (hit_at - wind_at)))
    if p < follow_at:
        return _lerp(strike, follow, _ease((p - hit_at) / (follow_at - hit_at)))
    return _lerp(follow, REST, _ease((p - follow_at) / (1 - follow_at)))


# Where the hands close on each weapon's grip (model y), the first for one hand, both for two.
GRIPS = {
    "sword": (0.0, -0.12),
    "greatsword": (0.0, -0.24),
    "katana": (-0.02, -0.17),
    "whip": (-0.04, -0.14),
    "mace": (-0.18, -0.18),
    "club": (-0.15, -0.15),
    "axe": (-0.18, 0.25),
    "hammer": (-0.18, 0.25),
}
NODACHI_GRIP = (0.05, -0.3)

# Sleeve colour and trim for each body armor (None: a plain linen shirt).
SLEEVES = {
    None: ((190, 178, 150), (160, 148, 120)),
    "padded_coat": ((120, 104, 80), (90, 76, 56)),
    "ringmail": ((130, 132, 140), (70, 72, 80)),
    "lamellar_vest": ((140, 52, 40), (200, 170, 90)),
    "brigandine": ((150, 40, 40), (190, 190, 200)),
    "blackened_plate": ((52, 52, 58), (150, 150, 160)),
}
GLOVES = {
    None: (SKIN, tuple(c - 20 for c in SKIN)),
    "leather_gloves": ((96, 64, 40), (70, 46, 30)),
    "chain_mitts": ((150, 152, 160), (90, 92, 100)),
    "iron_gauntlets": ((120, 120, 130), (180, 180, 190)),
}


def _limb(r, a, b, thick, rgb):
    """A box from point a to point b (camera space), `thick` across."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-6:
        return
    yaw = math.atan2(-dz, dx)
    pitch = math.asin(max(-1.0, min(1.0, dy / length)))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    r.part("cube", *mid, length, thick, thick, rgb, ry=yaw, rz=pitch)


def arm(r, wrist, side, body=None, gloves=None):
    """A forearm from off-screen to `wrist` (camera space), in the sleeve of the body armor.
    side is +1 for the right arm, -1 for the left."""
    elbow = (wrist[0] - 0.75, wrist[1] - 0.42, wrist[2] + 0.28 * side)
    sleeve, trim = SLEEVES.get(body, SLEEVES[None])
    cuff = _lerp(wrist, elbow, 0.12)
    _limb(r, cuff, elbow, 0.15 if body == "blackened_plate" else 0.13, sleeve)
    if body == "ringmail":  # rows of rings
        for k in (0.35, 0.55, 0.75):
            _limb(r, _lerp(wrist, elbow, k), _lerp(wrist, elbow, k + 0.04), 0.138, trim)
    elif body in ("lamellar_vest", "brigandine"):  # laced plates / rivets
        for k in (0.3, 0.5, 0.7):
            _limb(r, _lerp(wrist, elbow, k), _lerp(wrist, elbow, k + 0.03), 0.14, trim)
    elif body == "blackened_plate":  # a vambrace with a bright edge
        _limb(r, _lerp(wrist, elbow, 0.14), _lerp(wrist, elbow, 0.2), 0.17, trim)
    else:  # a cuff seam
        _limb(r, _lerp(wrist, elbow, 0.14), _lerp(wrist, elbow, 0.19), 0.14, trim)
    hand, shade = GLOVES.get(gloves, GLOVES[None])
    if gloves == "iron_gauntlets":  # a flared cuff over the sleeve
        _limb(r, _lerp(wrist, elbow, 0.02), _lerp(wrist, elbow, 0.2), 0.17, shade)
    elif gloves:
        _limb(r, _lerp(wrist, elbow, 0.02), _lerp(wrist, elbow, 0.15), 0.145, shade)
    return hand, shade


def fist(r, hand, shade, gloves=None):
    """A closed hand around the grip at the origin of the current (weapon) frame; grip along +Y."""
    big = 1.15 if gloves == "iron_gauntlets" else 1.0
    r.part("cube", -0.02, 0, 0, 0.16 * big, 0.15 * big, 0.14 * big, hand)
    r.part("cube", 0.06, 0, 0, 0.05 * big, 0.14 * big, 0.15 * big, shade)  # knuckles
    r.part("cube", 0.02, 0.07, -0.06, 0.08, 0.05, 0.05, hand)  # thumb over the grip
    if gloves == "iron_gauntlets":
        for i in range(3):
            r.part("cube", 0.09, -0.05 + i * 0.05, 0, 0.03, 0.035, 0.17, (190, 190, 200))
    elif gloves == "chain_mitts":
        r.part("cube", 0.085, 0, 0, 0.01, 0.12, 0.13, (110, 112, 120))


def _pose_at(r, pose, side):
    """Enters a weapon pose (x, y, z, rx, ry, rz) mirrored for the left hand."""
    x, y, z, rx, ry, rz = pose
    return r.at(x, y, z * side, rx=rx * side, ry=ry * side, rz=rz, s=0.7)


def _weapon_point(pose, side, ly):
    """Camera-space position of a point `ly` up the weapon's grip in `pose` (for placing wrists)."""
    x, y, z, rx, ry, rz = pose
    rx, ry = rx * side, ry * side
    # local (0, ly*s, 0) through rot_y(ry) * rot_z(rz) * rot_x(rx)
    v = (0.0, ly * 0.7, 0.0)
    v = (v[0], v[1] * math.cos(rx), v[1] * math.sin(rx))
    v = (v[0] * math.cos(rz) - v[1] * math.sin(rz), v[0] * math.sin(rz) + v[1] * math.cos(rz), v[2])
    v = (v[0] * math.cos(ry) + v[2] * math.sin(ry), v[1], -v[0] * math.sin(ry) + v[2] * math.cos(ry))
    return x + v[0], y + v[1], z * side + v[2]


def _grips(item):
    if item.id == "nodachi":
        return NODACHI_GRIP
    return GRIPS.get(item.category, (0.0, -0.12))


def _heavy_look(item):
    return item.two_handed or item.category in ("greatsword", "hammer")


def weapon_view(r, player, bob, t=0.0):
    """Both hands in first person: each holds its weapon, shield or spell, or is a bare fist."""
    inv = player.inventory
    armor = {"body": inv.body, "gloves": inv.hands}
    sprint = 1.0 if player.sprinting else max(0.0, 1 - player.since_sprint / 0.25)
    breath = math.sin(t * 1.7) * 0.006
    if inv.two_handing():
        return _held_weapon(r, player, "right", bob + breath, sprint, armor, both=True)
    for hand in ("right", "left"):
        item = player.hand_item(hand)
        side = 1 if hand == "right" else -1
        if item.kind == "shield":
            shield_view(r, player, item, bob + breath, side, armor)
        elif item.kind == "spell":
            spell_hand_view(r, player, bob + breath, side, armor, t)
        elif item.category == "fists":
            fist_view(r, player, hand, bob + breath, armor)
        else:
            _held_weapon(r, player, hand, bob + breath, sprint, armor)
    return None


def _held_weapon(r, player, hand, bob, sprint, armor, both=False):
    item = player.hand_item(hand)
    side = 1 if hand == "right" else -1
    heavy = _heavy_look(item)
    x, y, z = 0.9, (-0.4 if heavy else -0.33) + bob, (0.2 if both else (0.32 if heavy else 0.27))
    rx, ry, rz = 0.25, 0.7, -0.55
    swinging = player.swing_t is not None and player.swing_hand == hand
    charge = player.charge_frac if (player.swing_t is None and player.charge_hand == hand) else 0.0
    if swinging:
        a = player.attack
        dx, dy, dz, drx, drz = _motion(a.motion, player.swing_phase, a.hit_at)
        x, y, z, rx, rz = x + dx, y + dy, z + dz, rx + drx, rz + drz
    elif charge > 0:  # drawing back for a heavy: raise it, with a tremble once it is ready
        k = _ease(charge)
        shake = math.sin(player.charge_t * 60) * 0.006 if charge >= 1 else 0.0
        x, y, z = x - 0.05 * k, y + 0.14 * k + shake, z - 0.04 * k
        rx, rz = rx + 0.4 * k, rz + 0.3 * k
        if item.category == "katana":  # held on: settle low into the draw stance
            d = _ease((player.charge_t - 0.35) / (1.2 - 0.35))
            wx, wy, wz, wrx, wrz = MOTIONS["draw"][0]
            x, y, z = x + (wx + 0.05) * d, y + (wy - 0.14) * d, z + (wz + 0.04) * d
            rx, rz = rx + (wrx - 0.4) * d, rz + (wrz - 0.3) * d
    else:  # sprinting: carried low, blade forward
        y -= 0.08 * sprint
        rz -= 0.35 * sprint
    pose = (x, y, z, rx, ry, rz)
    hand_rgb, shade = arm(r, _weapon_point(pose, side, _grips(item)[0]), side, armor["body"], armor["gloves"])
    if both:
        lp = _weapon_point(pose, side, _grips(item)[1])
        lhand, lshade = arm(r, lp, -1, armor["body"], armor["gloves"])
    phase = player.swing_phase if swinging else None
    with _pose_at(r, pose, side):
        weapon(r, item.id, phase)
        with r.at(0, _grips(item)[0], 0):
            fist(r, hand_rgb, shade, armor["gloves"])
        if both:
            with r.at(0, _grips(item)[1], 0):
                fist(r, lhand, lshade, armor["gloves"])


def fist_view(r, player, hand, bob, armor):
    """A bare hand: a jab straight forward, or a hook from the outside."""
    side = 1 if hand == "right" else -1
    swinging = player.swing_t is not None and player.swing_hand == hand
    phase = player.swing_phase if swinging else None
    motion = player.attack.motion if swinging else "jab"
    hit_at = player.attack.hit_at if swinging else 0.4
    jab = 0.0
    out = 0.0
    if phase is not None:
        k = _ease(phase / hit_at) if phase < hit_at else 1 - _ease((phase - hit_at) / (1 - hit_at))
        jab = k * 0.32
        if motion == "hook":
            out = 0.3 * (1 - _ease(phase / max(hit_at, 1e-6))) if phase < hit_at else 0.0
            jab *= 0.6
    charge = player.charge_frac if (not swinging and player.charge_hand == hand) else 0.0
    pull = -0.1 * _ease(charge)
    wrist = (
        0.95 + jab + pull,
        -0.34 + bob + jab * 0.2,
        (0.34 - jab * 0.5 * (1 if motion != "hook" else 0) + out) * side,
    )
    hand_rgb, shade = arm(r, wrist, side, armor["body"], armor["gloves"])
    with r.at(*wrist, ry=0.25 * side, rz=0.2, s=0.8), r.at(0.06, 0, 0, rz=-math.pi / 2):
        fist(r, hand_rgb, shade, armor["gloves"])


def shield_view(r, player, item, bob, side, armor):
    """A shield on the forearm: carried at the side, brought to the centre while you block."""
    up = 1.0 if player.guarding else 0.0
    jolt = max(0.0, 0.18 - player.since_block) * 0.8  # a blow knocks it back
    reel = player.guard_break_t * 0.5  # a broken guard flings it wide
    x = 0.85 - jolt - reel * 0.3
    y = -0.44 + bob + 0.3 * up - reel * 0.3
    z = (0.38 - 0.28 * up + reel * 0.3) * side
    wrist = (x - 0.12, y - 0.05, z)
    hand_rgb, shade = arm(r, wrist, side, armor["body"], armor["gloves"])
    with r.at(*wrist, s=0.85):
        fist(r, hand_rgb, shade, armor["gloves"])
    with r.at(x, y, z, ry=(-0.35 + 0.35 * up) * side, rz=0.1, s=0.75):
        shield(r, item.id)


def spell_hand_view(r, player, bob, side, armor, t):
    """An open hand holding the readied spell's light; it pushes forward as the spell is cast."""
    spell = player.current_spell()
    cast = 1 - min(player.magic_gauge.value / 0.25, 1.0)  # just after casting
    x = 0.9 + 0.2 * _ease(cast)
    y = -0.31 + bob
    z = 0.3 * side
    hand_rgb, shade = arm(r, (x - 0.06, y - 0.04, z), side, armor["body"], armor["gloves"])
    with r.at(x, y, z, ry=0.2 * side, s=0.8):
        r.part("cube", 0, 0, 0, 0.14, 0.05, 0.15, hand_rgb)  # palm up
        for i in range(4):  # fingers, slightly curled
            r.part("cube", 0.1, 0.02, (-0.06 + i * 0.04) * side, 0.08, 0.035, 0.03, shade)
        r.part("cube", 0.03, 0.02, -0.09 * side, 0.07, 0.035, 0.035, hand_rgb)  # thumb
        if spell and player.magic_gauge.full:
            glow = SPELL_GLOW.get(spell.id, (220, 220, 220))
            pulse = 1 + math.sin(t * 5) * 0.12
            r.part("sphere", 0.02, 0.1, 0, 0.09 * pulse, 0.09 * pulse, 0.09 * pulse, glow, glow=True)


SPELL_GLOW = {
    "flame": EMBER,
    "mend": (130, 230, 130),
    "lumen": (235, 235, 180),
    "venom": (130, 220, 70),
    "veil": (205, 215, 220),
    "pyre": (255, 110, 40),
}


WOOD = (90, 60, 38)
LEATHER = (70, 46, 30)
BRASS = (150, 130, 80)
STEEL = (190, 190, 200)
OAK = (118, 84, 52)

# Rough length of each weapon model (grip to tip), used to fit previews.
WEAPON_LEN = {
    "bastard_sword": 1.4,
    "claymore": 1.85,
    "zweihander": 2.1,
    "katana": 1.35,
    "moonless_tachi": 1.6,
    "nodachi": 2.1,
    "war_hammer": 1.5,
    "felling_axe": 1.45,
    "bearded_axe": 1.15,
    "hatchet": 0.9,
    "oak_cudgel": 1.0,
    "spiked_club": 1.05,
}


def weapon(r, item_id, phase=None):
    """A weapon model with the grip at the origin, pointing up +Y."""
    if item_id in ("claymore", "zweihander"):
        greatsword(r, item_id == "zweihander")
    elif item_id in ("katana", "moonless_tachi", "nodachi"):
        katana(r, item_id)
    elif item_id in ("leather_whip", "thornlash"):
        whip(r, phase, thorns=item_id == "thornlash")
    elif item_id == "mace":
        mace(r)
    elif item_id in ("oak_cudgel", "spiked_club"):
        club(r, item_id == "spiked_club")
    elif item_id == "war_hammer":
        hammer(r)
    elif item_id == "felling_axe":
        felling_axe(r)
    elif item_id in ("hatchet", "bearded_axe"):
        hand_axe(r, item_id == "bearded_axe")
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


# blade, edge, grip wrap, cord, segments, grip length
KATANAS = {
    "katana": ((205, 208, 218), (245, 245, 250), (40, 30, 40), (160, 30, 40), 3, 0.3),
    "moonless_tachi": ((70, 72, 90), (200, 205, 220), (20, 18, 24), (60, 60, 80), 4, 0.32),
    "nodachi": ((200, 202, 212), (245, 245, 250), (30, 26, 30), (200, 170, 70), 5, 0.5),
}


def katana(r, item_id="katana"):
    blade, edge, wrap, cord, segments, grip = KATANAS[item_id]
    r.part("cube", 0, 0.07 - grip / 2, 0, 0.055, grip, 0.055, wrap)
    for i in range(round(grip / 0.075)):  # cord wrap
        r.part("cube", 0, 0.05 - grip + 0.04 + i * 0.075, 0, 0.06, 0.02, 0.06, cord)
    r.part("cyl", 0, 0.08, 0, 0.16, 0.025, 0.16, (60, 50, 30))
    r.part("cube", 0, 0.11, 0, 0.04, 0.04, 0.06, (170, 150, 70))
    with r.at(0, 0.13, 0):
        _katana_segment(r, segments, blade, edge)


def _katana_segment(r, left, blade=(205, 208, 218), edge=(245, 245, 250)):
    """A gentle curve: each segment hangs off the last, bent a little further back."""
    if left == 0:
        r.part("cube", 0, 0.03, -0.01, 0.022, 0.07, 0.05, blade, rx=0.35)
        return
    with r.at(0, 0, 0, rx=0.05):
        r.part("cube", 0, 0.17, 0, 0.025, 0.36, 0.07, blade)
        r.part("cube", 0.013, 0.17, -0.025, 0.006, 0.36, 0.015, edge)
        with r.at(0, 0.34, 0):
            _katana_segment(r, left - 1, blade, edge)


def whip(r, phase=None, thorns=False):
    r.part("cube", 0, -0.04, 0, 0.06, 0.3, 0.06, LEATHER)
    r.part("cube", 0, 0.12, 0, 0.075, 0.04, 0.075, (90, 90, 96) if thorns else BRASS)
    # Hanging coils at rest; the lash straightens out at the crack.
    straight = math.sin(phase * math.pi) if phase is not None else 0.0
    bend = 0.42 * (1 - straight) + 0.04
    with r.at(0, 0.14, 0):
        _whip_segment(r, 8 if thorns else 7, bend, 0.06, thorns)


def _whip_segment(r, left, bend, thick, thorns=False):
    if left == 0:
        r.part("cube", 0, 0.04, 0, 0.02, 0.08, 0.05, (120, 90, 60))
        return
    with r.at(0, 0, 0, rx=bend):
        r.part("cube", 0, 0.1, 0, thick, 0.2, thick, (70, 60, 36) if thorns else (100, 70, 44))
        if thorns:
            for i, (dz, dx) in enumerate(((1, 0), (-1, 0), (0, 1))):
                r.part("cube", dx * thick * 0.7, 0.04 + i * 0.05, dz * thick * 0.7, 0.025, 0.04, 0.025, IRON)
        with r.at(0, 0.2, 0):
            _whip_segment(r, left - 1, bend, max(thick * 0.86, 0.025), thorns)


def mace(r):
    r.part("cube", 0, 0.1, 0, 0.06, 0.7, 0.06, WOOD)
    r.part("cube", 0, -0.2, 0, 0.075, 0.12, 0.075, LEATHER)
    r.part("sphere", 0, 0.55, 0, 0.17, 0.22, 0.17, (88, 88, 96))
    for i in range(4):
        with r.at(0, 0.55, 0, ry=i * math.pi / 4):
            r.part("cube", 0, 0, 0, 0.03, 0.2, 0.26, (120, 120, 130))
    r.part("cube", 0, 0.69, 0, 0.05, 0.07, 0.05, (120, 120, 130))


def club(r, spiked):
    """A knotted oak club that swells toward the end; the spiked one is a root-ball full of nails."""
    r.part("cube", 0, -0.15, 0, 0.08, 0.16, 0.08, LEATHER)
    for i, (w, h) in enumerate(((0.07, 0.25), (0.1, 0.25), (0.14, 0.22), (0.18 if spiked else 0.16, 0.2))):
        r.part("cyl", 0, 0.02 + i * 0.22, 0, w, h, w, OAK if i % 2 else (104, 74, 46))
    r.part("sphere", 0.05, 0.45, 0.03, 0.06, 0.08, 0.06, (90, 62, 40))  # knots
    r.part("sphere", -0.04, 0.25, -0.04, 0.05, 0.06, 0.05, (90, 62, 40))
    if spiked:
        r.part("sphere", 0, 0.78, 0, 0.26, 0.24, 0.26, (96, 70, 44))
        for i in range(7):
            a = i * 2.4
            with r.at(0, 0.66 + (i % 3) * 0.08, 0, ry=a):
                r.part("cube", 0, 0, 0.15, 0.02, 0.02, 0.12, (150, 150, 158))
        r.part("cube", 0, 0.92, 0, 0.02, 0.1, 0.02, (150, 150, 158))
    else:
        r.part("sphere", 0, 0.76, 0, 0.18, 0.16, 0.18, (104, 74, 46))


def felling_axe(r):
    """A woodcutter's long-hafted axe: a heavy wedge head, notched and patched with moss."""
    r.part("cube", 0, 0.35, 0, 0.06, 1.25, 0.06, WOOD)
    r.part("cube", 0, -0.2, 0, 0.075, 0.2, 0.075, LEATHER)
    r.part("cube", 0, 1.02, 0.12, 0.08, 0.28, 0.32, (120, 116, 112))  # the wedge
    r.part("cube", 0, 1.02, 0.31, 0.05, 0.4, 0.08, (175, 175, 180))  # bit, the cutting edge
    r.part("cube", 0, 1.02, -0.1, 0.1, 0.18, 0.12, (96, 92, 90))  # poll
    r.part("cube", 0.045, 1.08, 0.16, 0.01, 0.08, 0.1, MOSS)
    r.part("cube", 0, 0.92, 0.0, 0.08, 0.06, 0.08, LEATHER)  # wedge binding


def hand_axe(r, bearded):
    """A one-handed axe. The bearded one has a long lower edge that hooks down past the haft."""
    haft = 0.85 if bearded else 0.6
    r.part("cube", 0, haft / 2 - 0.25, 0, 0.055, haft, 0.055, OAK)
    r.part("cube", 0, -0.2, 0, 0.07, 0.14, 0.07, LEATHER)
    top = haft - 0.3
    r.part("cube", 0, top, 0.06, 0.07, 0.14, 0.16, (110, 108, 106))  # eye and cheek
    if bearded:
        r.part("cube", 0, top - 0.06, 0.2, 0.04, 0.32, 0.12, (150, 150, 156))  # the beard
        r.part("cube", 0.022, top - 0.08, 0.26, 0.01, 0.36, 0.03, (215, 215, 222))  # edge
        r.part("cube", 0, top - 0.24, 0.16, 0.04, 0.06, 0.06, (150, 150, 156))  # its hooked tip
    else:
        r.part("cube", 0, top, 0.17, 0.04, 0.2, 0.08, (150, 150, 156))
        r.part("cube", 0.022, top, 0.21, 0.01, 0.22, 0.02, (215, 215, 222))
    r.part("cube", 0, top + 0.08, 0, 0.065, 0.03, 0.065, LEATHER)


def hammer(r):
    """A war hammer: an eight-sided iron head with a broad face and a curved back spike, steel
    langets riveted down the haft and a rondel to guard the hands."""
    r.part("cube", 0, 0.35, 0, 0.065, 1.25, 0.065, WOOD)
    r.part("cube", 0, -0.2, 0, 0.08, 0.22, 0.08, LEATHER)
    r.part("cube", 0, -0.33, 0, 0.1, 0.05, 0.1, (90, 90, 98))  # pommel cap
    r.part("cyl", 0, 0.07, 0, 0.17, 0.03, 0.17, (120, 120, 128))  # rondel
    for dz in (-0.036, 0.036):  # langets
        r.part("cube", 0, 0.78, dz, 0.04, 0.42, 0.012, STEEL)
        for k in range(3):
            r.part("cube", 0, 0.64 + k * 0.12, dz * 1.2, 0.02, 0.02, 0.012, (90, 90, 98))
    with r.at(0, 1.04, 0.05, rx=math.pi / 2):
        r.part("cyl", 0, 0, 0, 0.26, 0.42, 0.26, (110, 110, 118))  # head
        r.part("cyl", 0, 0.23, 0, 0.3, 0.06, 0.3, (140, 140, 150))  # striking face
        r.part("cyl", 0, 0.27, 0, 0.2, 0.03, 0.2, (175, 175, 185))
    r.part("cube", 0, 1.04, -0.22, 0.08, 0.08, 0.16, (100, 100, 108))  # spike root
    r.part("cube", 0, 1.0, -0.34, 0.05, 0.05, 0.14, STEEL, rx=-0.35)  # curved back spike
    r.part("cube", 0, 0.95, -0.42, 0.03, 0.03, 0.08, STEEL, rx=-0.7)
    r.part("cube", 0, 1.26, 0, 0.05, 0.12, 0.05, STEEL)  # top spike


def shield(r, item_id):
    """Shields face +X (away from you); the arm holds them from behind at the origin. The first-person
    view draws without depth testing, so the back (what you see) is drawn last."""
    if item_id == "buckler":
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.42, 0.04, 0.42, (128, 128, 136))
            r.part("cyl", 0, -0.035, 0, 0.18, 0.06, 0.18, (170, 170, 180))  # boss
            r.part("cyl", 0, 0.03, 0, 0.12, 0.03, 0.12, LEATHER)  # grip
    elif item_id == "round_shield":
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.82, 0.04, 0.82, (96, 120, 140))
            r.part("cyl", 0, 0.002, 0, 0.86, 0.035, 0.86, (90, 90, 96))  # iron rim
            r.part("cyl", 0, -0.04, 0, 0.2, 0.07, 0.2, (150, 150, 158))  # boss
            r.part("cyl", 0, 0.03, 0, 0.8, 0.02, 0.8, (104, 78, 50))  # the wooden back
        for k in (-0.2, 0.0, 0.2):  # planks seen from behind
            r.part("cube", -0.03, 0, k, 0.01, 0.74, 0.015, (80, 60, 40))
        r.part("cube", -0.04, 0, 0, 0.03, 0.16, 0.05, LEATHER)
    elif item_id == "kite_shield":
        face, trim = (160, 50, 44), (200, 180, 120)
        r.part("cube", 0, 0.18, 0, 0.04, 0.42, 0.56, face)
        for i in range(5):  # tapering to a point
            w = 0.5 - i * 0.1
            r.part("cube", 0, -0.08 - i * 0.09, 0, 0.04, 0.1, w, face)
        r.part("cube", 0.025, 0.4, 0, 0.01, 0.04, 0.58, trim)
        r.part("cube", 0.025, 0.0, 0, 0.01, 0.78, 0.04, trim)
        back = (98, 74, 48)
        r.part("cube", -0.025, 0.18, 0, 0.01, 0.42, 0.56, back)
        for i in range(5):
            r.part("cube", -0.025, -0.08 - i * 0.09, 0, 0.01, 0.1, 0.5 - i * 0.1, back)
        r.part("cube", -0.04, 0.05, 0, 0.03, 0.18, 0.05, LEATHER)
    else:  # tower shield
        r.part("cube", 0, 0.12, 0, 0.06, 1.25, 0.66, (96, 74, 50))
        for dy in (-0.35, 0.12, 0.6):
            r.part("cube", 0.035, dy, 0, 0.015, 0.06, 0.68, (100, 100, 108))  # iron bands
        for dz in (-0.16, 0.16):
            r.part("cube", -0.035, 0.12, dz, 0.01, 1.2, 0.012, (70, 52, 34))
        r.part("cube", -0.05, 0.05, 0, 0.03, 0.2, 0.06, LEATHER)


def item(r, id_, t):
    """Inventory preview models, roughly 1 unit tall and centered on the origin."""
    if Items.ALL.get(id_) and Items.get(id_).kind == "weapon":
        k = 1.2 / WEAPON_LEN.get(id_, 1.2)
        with r.at(0, -0.8 * k, 0, rx=0.3, s=1.45 * k):
            weapon(r, id_)
    elif Items.ALL.get(id_) and Items.get(id_).kind == "shield":
        k = 1.0 if id_ != "tower_shield" else 0.75
        with r.at(0, 0, 0, s=1.3 * k):
            shield(r, id_)
    elif id_ in SLEEVES:
        garment(r, id_)
    elif id_ in GLOVES:
        gauntlet(r, id_)
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
    elif id_ in SCROLL_RIBBON:
        ribbon = SCROLL_RIBBON[id_]
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
    elif id_ == "briar_key":
        key(r, (70, 92, 46), 1.7)
    elif id_ == "verdant_sigil":
        glow = 1 + math.sin(t * 3) * 0.08
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.7, 0.12, 0.7, (60, 90, 70))
            r.part("cyl", 0, 0, 0, 0.42 * glow, 0.14, 0.42 * glow, (110, 230, 120), glow=True)
            r.part("cube", 0, 0.1, 0, 0.5, 0.02, 0.1, (40, 120, 50), ry=0.6)
    elif id_ == "ember_sigil":
        glow = 1 + math.sin(t * 4) * 0.08
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.7, 0.12, 0.7, (110, 80, 70))
            r.part("cyl", 0, 0, 0, 0.36 * glow, 0.14, 0.36 * glow, EMBER, glow=True)
    else:
        r.part("cube", 0, 0, 0, 0.5, 0.5, 0.5, (130, 100, 70))


SCROLL_RIBBON = {
    "scroll_mend": (170, 40, 40),
    "scroll_lumen": (210, 200, 120),
    "scroll_venom": (90, 150, 50),
    "scroll_veil": (150, 160, 170),
    "scroll_pyre": (220, 90, 30),
}


def garment(r, id_):
    """Body armor on an invisible torso: its colour and trim match the first-person sleeve."""
    col, trim = SLEEVES[id_]
    r.part("cube", 0, 0, 0, 0.3, 0.8, 0.62, col)
    r.part("cube", 0, 0.34, 0, 0.32, 0.14, 0.86, col)
    r.part("cube", 0, 0.0, -0.42, 0.22, 0.6, 0.18, col, rx=-0.15)
    r.part("cube", 0, 0.0, 0.42, 0.22, 0.6, 0.18, col, rx=0.15)
    if id_ == "blackened_plate":  # pauldrons and a ridged breastplate
        for dz in (-0.42, 0.42):
            r.part("sphere", 0, 0.32, dz, 0.3, 0.22, 0.3, col)
        r.part("cube", 0.16, 0.05, 0, 0.04, 0.6, 0.06, trim)
    # Ring rows on mail, laced plates on lamellar, rivets on brigandine, quilting on the coat.
    for i in range(4):
        r.part("cube", 0, 0.2 - i * 0.14, 0, 0.32, 0.03, 0.64, trim)
    if id_ == "brigandine":
        for i in range(3):
            for dz in (-0.2, 0.0, 0.2):
                r.part("cube", 0.16, 0.13 - i * 0.14, dz, 0.02, 0.03, 0.03, trim)
    r.part("cube", 0, -0.18, 0, 0.33, 0.06, 0.65, (70, 50, 34))


def gauntlet(r, id_):
    """A single glove or gauntlet, fingers up: palm, four fingers, a thumb and the cuff."""
    hand, shade = GLOVES[id_]
    iron = id_ == "iron_gauntlets"
    r.part("cube", 0, -0.05, 0, 0.16, 0.36, 0.42, hand)  # back of the hand
    for i in range(4):
        r.part("cube", 0, 0.24 + (0.03 if i in (1, 2) else 0), -0.15 + i * 0.1, 0.13, 0.26, 0.08, hand)
        if iron:  # knuckle plates
            r.part("cube", 0.08, 0.2, -0.15 + i * 0.1, 0.03, 0.06, 0.085, (190, 190, 200))
    r.part("cube", 0, -0.02, 0.26, 0.12, 0.22, 0.09, hand, rx=-0.5)  # thumb
    cuff = 0.5 if iron else 0.46
    r.part("cube", 0, -0.36, 0, 0.22, 0.28, cuff, shade)
    if id_ == "chain_mitts":
        for k in range(3):
            r.part("cube", 0.085, -0.15 + k * 0.1, 0, 0.01, 0.02, 0.4, (110, 112, 120))


def key(r, rgb, size):
    with r.at(0, 0, 0, rx=-0.6, s=size):
        r.part("cyl", 0, 0.32, 0, 0.32, 0.06, 0.32, rgb, rz=math.pi / 2)
        r.part("cube", 0, -0.08, 0, 0.06, 0.6, 0.06, rgb)
        r.part("cube", 0, -0.3, 0.08, 0.05, 0.06, 0.12, rgb)
        r.part("cube", 0, -0.18, 0.07, 0.05, 0.05, 0.1, rgb)


def eruption(r, glow, flame, t):
    """The Warden's fire from below: a glowing ring of cracks on the floor, then a column of flame."""
    if glow > 0:
        for i in range(8):
            a = i * math.pi / 4 + t * 0.5
            r.part(
                "cube", math.cos(a) * 0.8, 0.03, math.sin(a) * 0.8, 0.5, 0.03, 0.08,
                (255, rround(80 + 120 * glow), 30), ry=-a + math.pi / 2, glow=True,
            )  # fmt: skip
        r.part("cyl", 0, 0.02, 0, 0.6 * glow, 0.02, 0.6 * glow, EMBER, glow=True)
    if flame > 0:
        h = 2.6 * flame
        r.part("cone", 0, h / 2, 0, 1.4, h, 1.4, (255, 120, 40), glow=True)
        r.part("cone", 0, h * 0.45, 0, 0.8, h * 1.1, 0.8, (255, 220, 130), glow=True)


def shockwave_ring(r, k, radius):
    """A slam's ring of dust and embers running out across the floor."""
    d = radius * k
    size = 0.35 * (1 - k) + 0.08
    for i in range(16):
        a = i * math.pi / 8
        rgb = EMBER if i % 2 else (150, 130, 110)
        r.part("cube", math.cos(a) * d, 0.1 + 0.2 * (1 - k), math.sin(a) * d, size, size, size, rgb,
               ry=a, glow=i % 2 == 1)  # fmt: skip


STONE = (120, 116, 110)


def pillar(r, seed, height):
    """A square-based stone column up to the ceiling, its capital cracked and a chunk fallen."""
    r.part("cube", 0, 0.2, 0, 1.2, 0.4, 1.2, WHITE, tex="stone_brick")
    r.part("cyl", 0, height / 2, 0, 0.85, height - 0.6, 0.85, WHITE, tex="rough_stone")
    r.part("cube", 0, height - 0.2, 0, 1.2, 0.4, 1.2, WHITE, tex="stone_brick", ry=0.05 * (seed % 3))
    a = seed * 1.3
    r.part("cube", math.cos(a) * 0.75, 0.12, math.sin(a) * 0.75, 0.3, 0.24, 0.28, STONE, ry=a)


def sarcophagus(r, seed):
    """A stone coffin with a carved effigy on its lid, which someone has shoved a little ajar."""
    r.part("cube", 0, 0.4, 0, 0.9, 0.8, 1.9, WHITE, tex="rough_stone")
    r.part("cube", 0, 0.1, 0, 1.0, 0.2, 2.0, WHITE, tex="stone_brick")
    shift = 0.12 + (seed % 3) * 0.06
    with r.at(shift, 0.86, 0, ry=0.08 * (1 if seed % 2 else -1)):
        r.part("cube", 0, 0, 0, 0.96, 0.12, 1.96, WHITE, tex="rough_stone")
        r.part("sphere", 0, 0.12, -0.65, 0.3, 0.18, 0.3, STONE)  # the effigy's head
        r.part("cube", 0, 0.1, 0.05, 0.4, 0.12, 1.0, STONE)
        r.part("cube", 0, 0.18, -0.05, 0.08, 0.06, 0.6, STONE)  # hands folded on a sword
    r.part("cube", -0.48 + shift, 0.75, 0, 0.04, 0.06, 1.6, (20, 18, 16))  # the dark gap


def cage(r, t, seed, ceil_h):
    """A gibbet cage hanging on a chain from the ceiling, a skull wedged in its bars."""
    sway = math.sin(t * 0.6 + seed) * 0.06
    bottom = 1.0
    with r.at(0, ceil_h, 0, rz=sway, rx=sway * 0.5):
        drop = ceil_h - bottom - 1.4
        links = max(int(drop / 0.2), 1)
        for i in range(links):
            r.part("cube", 0, -0.1 - i * 0.2, 0, 0.03, 0.22, 0.08, IRON, ry=0 if i % 2 else 1.57)
        with r.at(0, -drop - 1.4, 0):
            r.part("cyl", 0, 0.0, 0, 0.8, 0.05, 0.8, DARK_IRON)
            r.part("cyl", 0, 1.3, 0, 0.8, 0.05, 0.8, DARK_IRON)
            r.part("cone", 0, 1.38, 0, 0.8, 0.2, 0.8, DARK_IRON)
            for i in range(8):
                a = i * math.pi / 4
                r.part("cube", math.cos(a) * 0.38, 0.65, math.sin(a) * 0.38, 0.03, 1.3, 0.03, IRON)
            r.part("sphere", 0.1, 0.13, 0.05, 0.22, 0.2, 0.2, BONE)
            r.part("cube", 0.0, 0.05, -0.1, 0.4, 0.05, 0.05, BONE, ry=0.6)


def cobweb(r, seed):
    """Old webs strung across the upper corner of the wall at local -X."""
    silk = (200, 198, 190)
    with r.at(-0.97, 2.6, 0.95 if seed % 2 else -0.95, ry=0 if seed % 2 else math.pi):
        for i in range(5):
            a = -0.1 - i * 0.35
            r.part(
                "cube", 0, math.sin(a) * 0.45, -math.cos(a) * 0.45, 0.005, 0.9, 0.01, silk, rx=a + math.pi / 2
            )
        for k in (0.25, 0.5, 0.72):
            for i in range(4):
                a = -0.27 - i * 0.35
                r.part("cube", 0, math.sin(a) * k, -math.cos(a) * k, 0.005, 0.01, 0.35 * k, silk, rx=a)


def skull_niche(r, t, seed):
    """A recess in the wall at local -X, packed with skulls, a candle guttering among them."""
    r.part("cube", -0.97, 1.3, 0, 0.08, 0.8, 1.0, (24, 20, 18))
    r.part("cube", -0.9, 1.75, 0, 0.16, 0.12, 1.2, WHITE, tex="rough_stone")  # lintel
    r.part("cube", -0.9, 0.86, 0, 0.18, 0.1, 1.2, WHITE, tex="rough_stone")  # sill
    for i in range(3 + seed % 2):
        z = -0.32 + i * 0.22
        y = 1.05 + (0.22 if i % 2 else 0)
        r.part("sphere", -0.86, y, z, 0.2, 0.18, 0.18, BONE)
        r.part("cube", -0.77, y, z - 0.04, 0.03, 0.04, 0.04, (30, 22, 18))
        r.part("cube", -0.77, y, z + 0.04, 0.03, 0.04, 0.04, (30, 22, 18))
    r.part("cyl", -0.86, 1.03, 0.36, 0.06, 0.2, 0.06, (225, 215, 185))
    _flame(r, -0.86, 1.17, 0.36, 0.04, t)


def grate(r, t):
    """An iron drain grate set in the floor, cold mist curling up out of the dark below."""
    r.part("cube", 0, 0.005, 0, 1.0, 0.01, 1.0, (10, 10, 12))
    r.part("cube", 0, 0.02, 0, 1.06, 0.03, 0.08, DARK_IRON)
    for i in range(5):
        r.part("cube", -0.4 + i * 0.2, 0.02, 0, 0.05, 0.03, 1.0, DARK_IRON)
    for i in range(3):
        k = (t * 0.3 + i / 3) % 1.0
        s = 0.12 + 0.2 * k
        r.part("cube", (i - 1) * 0.25, 0.05 + k * 0.9, math.sin(t + i) * 0.15, s, s * 0.5, s, (90, 96, 100))


def roots(r, t, seed, ceil_h):
    """Pale roots pushed down through the ceiling, hanging in tangles."""
    for i in range(4 + seed % 3):
        a = i * 1.9 + seed
        x, z = math.cos(a) * (0.3 + (i % 3) * 0.2), math.sin(a) * (0.3 + (i % 3) * 0.2)
        length = 0.8 + ((i * 7 + seed) % 5) * 0.2
        sway = math.sin(t * 0.5 + i) * 0.04
        with r.at(x, ceil_h, z, rx=sway, rz=-sway):
            for k in range(3):
                seg = length / 3
                r.part("cube", (k % 2) * 0.04, -seg * (k + 0.5), 0, 0.06 - k * 0.012, seg, 0.06 - k * 0.012,
                       (170, 150, 116), rz=0.15 * (1 if k % 2 else -1))  # fmt: skip


def winch(r, t, turning):
    """The windlass that works a lift, bolted to the wall at local -X: a chain drum between two
    timber posts and a crank. It turns while the lift moves."""
    for z in (-0.55, 0.55):
        r.part("cube", -0.75, 0.6, z, 0.18, 1.2, 0.16, OAK)
    spin = t * 4 if turning else 0.0
    with r.at(-0.75, 0.95, 0, rx=spin):
        r.part("cyl", 0, 0, 0, 0.4, 0.95, 0.4, OAK, rx=math.pi / 2)
        for i in range(5):
            r.part("cyl", 0, 0, -0.36 + i * 0.18, 0.44, 0.05, 0.44, IRON, rx=math.pi / 2)
        r.part("cube", 0, 0.25, 0.7, 0.05, 0.5, 0.05, IRON)  # crank
        r.part("cube", 0.1, 0.5, 0.7, 0.2, 0.05, 0.05, OAK)
    for i in range(int(1.6 / 0.15)):  # the chain running up from the drum
        r.part("cube", -0.75, 1.2 + i * 0.15, 0.0, 0.03, 0.16, 0.08, IRON, ry=0 if i % 2 else 1.57)


BRONZE = (150, 108, 56)


def bell(r, t, seed):
    """A great bronze bell in a timber frame, green with age; it stirs in a draught."""
    for z in (-0.8, 0.8):
        r.part("cube", 0, 1.3, z, 0.2, 2.6, 0.2, OAK)
    r.part("cube", 0, 2.6, 0, 0.26, 0.24, 1.9, OAK)
    with r.at(0, 2.45, 0, rz=math.sin(t * 0.8 + seed) * 0.04):
        r.part("cube", 0, -0.08, 0, 0.16, 0.16, 0.3, DARK_IRON)  # the crown it hangs by
        r.part("sphere", 0, -0.45, 0, 0.8, 0.6, 0.8, BRONZE)  # shoulder
        r.part("cyl", 0, -0.75, 0, 0.82, 0.6, 0.82, BRONZE)  # waist
        r.part("cyl", 0, -1.1, 0, 1.0, 0.25, 1.0, BRONZE)  # flaring skirt
        r.part("cyl", 0, -1.25, 0, 1.15, 0.1, 1.15, (90, 120, 96))  # verdigris lip
        r.part("cyl", 0, -0.62, 0, 0.84, 0.05, 0.84, (110, 80, 44))  # a cast band
        r.part("sphere", 0, -1.25, 0, 0.2, 0.2, 0.2, DARK_IRON)  # clapper
