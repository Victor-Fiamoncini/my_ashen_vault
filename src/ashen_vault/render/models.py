"""Original low-poly models assembled from primitives. All face +X."""

import math
from contextlib import contextmanager

from ashen_vault.ai.enemy import COMBO_GAP
from ashen_vault.player.items import Items
from ashen_vault.render import bounds, shapes
from ashen_vault.util import rround
from ashen_vault.world import terrain, villagers

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
        "butcher": butcher,
        "bone_crawler": bone_crawler,
        "forge_golem": forge_models.forge_golem,
        "iron_bowman": forge_models.iron_bowman,
        "slag_hound": forge_models.slag_hound,
        "brand": forge_models.gargoyle,
        "bellows": forge_models.gargoyle,
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


# Armed foes chop overhead: the sword arm rises up in front over the windup and comes down onto you.
# Angles are radians in the arm's swing plane, about the shoulder from hanging straight down.
CHOP_RAISED = 3.4  # the arm up over the head, a little behind it
CHOP_LANDED = 0.9  # the arm out in front and down as the blow lands
# Where a held weapon points (0 = straight ahead, pi/2 = up). The wrist is whatever turns the weapon
# that way from the forearm (aim_wrist), so arm and blade turn together and the blade never folds
# back along the arm.
BLADE_REST = 0.26  # a guard: the point forward and a little raised
BLADE_RAISED = 2.8  # held high, the blade lying back over the head
BLADE_LANDED = -0.1  # the blow lands with the blade level with the target
ELBOW_REST, ELBOW_COCKED, ELBOW_STRIKE = 0.3, 0.7, 0.1  # forearm bend forward at the elbow


def _mix(a, b, k):
    return a + (b - a) * k


def _swing_pose(e, rest, cocked, strike):
    """A value that eases from `rest` to `cocked` over the windup, snaps to `strike` as the blow
    falls and settles back to `rest` while recovering."""
    if e.state == "windup":
        return _mix(rest, cocked, _ease(min(e.state_t / max(e.type.windup, 1e-3), 1)))
    if e.state == "attack":
        return _mix(cocked, strike, _ease(min(e.state_t / 0.2, 1)))
    if e.state == "recover":
        return _mix(strike, rest, _ease(min(e.state_t / max(e.type.recover, 1e-3), 1)))
    return rest


def chop_angle(e):
    """The sword arm of an armed foe: raised overhead on the windup, brought down on the attack."""
    return _swing_pose(e, 0.0, CHOP_RAISED, CHOP_LANDED)


def blade_angle(e):
    """Where an armed foe's weapon points through a chop (see BLADE_REST)."""
    return _swing_pose(e, BLADE_REST, BLADE_RAISED, BLADE_LANDED)


def elbow_bend(e):
    """How far a sword arm bends at the elbow: more as it raises the blade, straight as it strikes."""
    return _swing_pose(e, ELBOW_REST, ELBOW_COCKED, ELBOW_STRIKE)


def wrist_angle(e):
    """The wrist turn that points an armed foe's weapon along blade_angle through a chop."""
    return aim_wrist(blade_angle(e), chop_angle(e) + elbow_bend(e))


def aim_wrist(direction, arm):
    """The wrist angle that points a held weapon along `direction` (radians in the swing plane, 0 =
    forward, pi/2 = up) when the shoulder and elbow have turned the forearm by `arm` in total. It is
    the equivalent angle nearest zero, so easing towards it never swings the long way round."""
    w = direction - arm
    return (w + math.pi) % (2 * math.pi) - math.pi


@contextmanager
def held(r, wrist, rgb, size=0.12, splay=0.0):
    """Call at the tip of a forearm: draws the fist and yields the weapon's frame, turned by `wrist`
    and then `splay` radians out to the +Z side (where the sword arms hang), so a blade held in front
    still shows from the front instead of pointing straight at you. The grip runs along +X through
    the fist (the origin), so a weapon drawn in that frame has its pommel behind the hand and its
    blade or head beyond it."""
    r.part("cube", 0, 0, 0, size, size * 1.15, size * 1.3, rgb)
    with r.at(0, 0, 0, ry=-splay, rz=wrist):
        yield


def sword_parts(r, length, width, steel, grip=(60, 40, 28), guard=IRON, glow=False, **style):
    """A straight sword in a `held` frame (grip along +X through the fist, the blade's flat facing +-Z):
    the same `blade_parts` the player's swords use, turned onto the frame's +X. `style` passes on
    blade_parts' looks (pommel, guard style, ricasso)."""
    with r.at(0, 0, 0, rx=math.pi / 2), r.at(0, 0, 0, rz=-math.pi / 2):
        blade_parts(
            r,
            length - 0.13,
            width,
            steel,
            thick=0.036,
            base=0.17,
            guard_w=width * 2.6,
            guard_rgb=guard,
            grip=0.26,
            grip_rgb=grip,
            pommel_rgb=guard,
            glow=glow,
            **style,
        )


def _dim(rgb, k=0.7):
    return tuple(rround(c * k) for c in rgb)


def death_fall(e, time=0.6):
    """0..1 how far a dying body has collapsed into its death pose (eased), 0 while alive. The ash
    effect then bleaches and crumbles it where it lies."""
    if e.state != "dead":
        return 0.0
    k = min(e.state_t / time, 1.0)
    return k * k * (3 - 2 * k)


def walk_cycle(e, t):
    return math.sin(t * 7) * 0.5 if e.state in ("chase", "idle") else 0


def _bar(r, a, b, thick, rgb, glow=False):
    """A box from point a to point b in the current frame, `thick` across (bones, struts, chains)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-6:
        return
    yaw = math.atan2(-dz, dx)
    pitch = math.asin(max(-1.0, min(1.0, dy / length)))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    r.part("cube", *mid, length, thick, thick, rgb, ry=yaw, rz=pitch, glow=glow)


def skull(r, bone, eyes=(30, 10, 10), glow=False, jaw=0.0):
    """A skull facing +X centred on the origin (about 0.3 m tall): cranium, brow ridge, deep sockets
    (lit with `eyes` when `glow`), cheekbones, a nasal hollow, a row of teeth and a jaw hinged open
    by `jaw` radians."""
    shade = _dim(bone, 0.78)
    r.part("sphere", -0.02, 0.04, 0, 0.27, 0.25, 0.24, bone)  # cranium
    r.part("cube", 0.07, -0.03, 0, 0.12, 0.12, 0.17, bone)  # face
    r.part("cube", 0.115, 0.035, 0, 0.05, 0.035, 0.19, shade)  # brow ridge
    for z in (-0.045, 0.045):
        r.part("cube", 0.125, -0.005, z, 0.03, 0.055, 0.06, eyes, glow=glow)  # sockets
        r.part("cube", 0.08, -0.055, z * 2.1, 0.07, 0.04, 0.035, bone)  # cheekbones
    r.part("cube", 0.132, -0.055, 0, 0.02, 0.04, 0.03, (40, 30, 26))  # nasal hollow
    r.part("cube", 0.125, -0.09, 0, 0.03, 0.03, 0.13, _bright(bone, 1.0, 18))  # teeth
    with r.at(0.0, -0.1, 0, rz=-jaw):
        r.part("cube", 0.06, -0.03, 0, 0.13, 0.04, 0.15, shade)  # jaw
        r.part("cube", 0.115, 0.005, 0, 0.03, 0.025, 0.12, _bright(bone, 1.0, 18))


def ribcage(r, bone, ribs=4, width=0.34, spacing=0.09, top=0.0, depth=0.17):
    """Rib pairs curving from a spine (running down Y at the origin) out round the sides and in to a
    breastbone `depth` in front (+X), each lower rib a little narrower."""
    front = depth * 0.65
    for i in range(ribs):
        y = top - i * spacing
        w = width * (1 - 0.07 * i) / 2
        for side in (1, -1):
            out = (front * 0.25, y - 0.02, side * w)
            _bar(r, (-0.02, y, side * 0.03), out, 0.032, bone)
            _bar(r, out, (front, y - 0.06, side * 0.035), 0.03, bone)
    _bar(r, (front, top - 0.03, 0), (front, top - (ribs - 1) * spacing - 0.07, 0), 0.04, _dim(bone, 0.85))


def hand(r, rgb, size=0.1, bony=False, curl=0.0):
    """A hand hanging from the wrist at the origin (down -Y), palm toward +Z... fingers forward (+X):
    a palm, three fingers (curled forward by `curl`) and a thumb. Bony hands are spindly."""
    thin = 0.45 if bony else 1.0
    r.part("cube", 0, -size * 0.45, 0, size * 0.5 * thin + 0.01, size * 0.9, size * 0.95, rgb)
    for i, z in enumerate((-0.32, 0.0, 0.32)):
        with r.at(0, -size * 0.9, z * size, rz=curl):
            r.part(
                "cube",
                0,
                -size * 0.32,
                0,
                size * 0.22 * thin + 0.008,
                size * (0.7 - 0.08 * (i == 2)),
                size * 0.24 * thin + 0.008,
                rgb,
            )
    r.part(
        "cube",
        size * 0.3,
        -size * 0.45,
        -size * 0.2,
        size * 0.2 * thin + 0.008,
        size * 0.55,
        size * 0.2 * thin + 0.008,
        rgb,
        rz=0.5,
    )


BONE_SHADE = (166, 156, 132)
RAG = (70, 58, 46)


def bone_walker(r, e, t):
    """A walking skeleton in the rags of a gaoler's tunic, a rusted pauldron strapped on and a notched
    sword in its fist, embers smouldering in its sockets. Slain, its knees give and it topples onto
    its back, and the embers go out."""
    swing = walk_cycle(e, t)
    fall = death_fall(e, 0.7)
    lean = (-0.3 if e.state == "hurt" else 0) + 1.35 * fall
    alive = fall < 0.5
    bone = (255, 240, 220) if e.state == "hurt" else BONE
    with r.at(-0.2 * fall, 0.12 * fall, 0, rz=lean):
        for side, a in ((-0.13, swing), (0.13, -swing)):
            knee = 0.1 + 0.45 * max(0.0, a) + 0.4 * fall
            with r.at(0, 0.9, side, rz=a + 0.35 * fall):
                r.part("cube", 0, -0.22, 0, 0.07, 0.42, 0.07, bone)  # thigh bone
                r.part("sphere", 0.01, -0.44, 0, 0.09, 0.08, 0.09, BONE_SHADE)  # knee
                with r.at(0, -0.44, 0, rz=-knee):
                    r.part("cube", 0, -0.21, 0.015, 0.055, 0.42, 0.04, bone)  # shin and calf bone
                    r.part("cube", 0, -0.21, -0.02, 0.035, 0.4, 0.03, BONE_SHADE)
                    with r.at(0, -0.44, 0, rz=knee * 0.8):
                        r.part("cube", 0.06, -0.01, 0, 0.18, 0.04, 0.09, bone)  # foot
                        r.part("cube", 0.15, -0.01, 0, 0.04, 0.03, 0.1, BONE_SHADE)  # toes
        # Pelvis: a basin with flaring hip blades, a rag hanging front and back.
        r.part("cube", 0, 0.94, 0, 0.14, 0.1, 0.24, bone)
        for side in (1, -1):
            r.part("cube", -0.02, 1.0, side * 0.13, 0.12, 0.12, 0.05, bone, rx=-side * 0.35)
        cloth = math.sin(t * 3) * 0.12 + swing * 0.2
        for x, k in ((0.09, 1), (-0.09, -1)):
            with r.at(x, 0.98, 0, rz=cloth * k):
                r.part("cube", 0, -0.16, 0, 0.03, 0.32, 0.22, RAG)
                r.part("cube", 0, -0.34, 0.05, 0.03, 0.06, 0.08, RAG)  # a tatter
        for i in range(5):  # the spine
            r.part("cube", -0.05, 1.03 + i * 0.075, 0, 0.06, 0.05, 0.06, BONE_SHADE if i % 2 else bone)
        ribcage(r, bone, ribs=4, width=0.36, top=1.35, depth=0.18)
        _bar(r, (0.03, 1.42, -0.27), (0.03, 1.42, 0.27), 0.05, bone)  # collarbones
        with r.at(0.02, 1.62, 0, rz=math.sin(t * 2) * 0.1 * (1 - fall) - 0.5 * fall):
            r.part("cube", -0.03, -0.08, 0, 0.05, 0.08, 0.05, BONE_SHADE)  # neck
            skull(
                r, bone, EMBER if alive else (40, 20, 14), glow=alive, jaw=0.15 + 0.25 * (e.state == "windup")
            )
        # The free arm: upper arm, elbow, forearm and a bony hand.
        with r.at(0, 1.4, -0.27, rz=swing * 0.6 - 0.3 * fall):
            r.part("cube", 0, -0.15, 0, 0.055, 0.3, 0.055, bone)
            with r.at(0, -0.3, 0, rz=0.35 + 0.2 * swing):
                r.part("cube", 0, -0.14, 0, 0.045, 0.28, 0.045, bone)
                with r.at(0, -0.29, 0):
                    hand(r, bone, 0.09, bony=True, curl=0.4)
        # The sword arm: a rusted pauldron, upper arm, a forearm bent at the elbow, and a bony fist
        # round the hilt. Slain, the sword falls flat beside it (the body has tipped back by `lean`).
        shoulder, elbow = chop_angle(e) - 0.5 * fall, elbow_bend(e) * (1 - fall)
        wrist = aim_wrist(_mix(blade_angle(e), -lean, fall), shoulder + elbow)
        with r.at(0, 1.4, 0.27, rz=shoulder):
            r.part("cube", 0, 0.0, 0.02, 0.2, 0.08, 0.16, RUST, rx=0.25)  # pauldron
            r.part("cube", 0, -0.06, 0.06, 0.18, 0.06, 0.13, _dim(RUST), rx=0.45)
            r.part("cube", 0, -0.02, -0.09, 0.2, 0.025, 0.025, (60, 44, 30))  # its strap
            r.part("cube", 0, -0.15, 0, 0.055, 0.3, 0.055, bone)
            with r.at(0, -0.3, 0, rz=elbow):
                r.part("cube", 0, -0.15, 0, 0.045, 0.3, 0.045, bone)
                with r.at(0, -0.32, 0), held(r, wrist, bone, size=0.08, splay=0.45):
                    sword_parts(r, 0.8, 0.07, (128, 104, 84), grip=(70, 50, 36), guard=RUST)


SLIME = (70, 120, 60)


def mire_slime(r, e, t):
    """A heap of bog jelly that has swallowed the last thing it caught: a skull half-sunk in its crown,
    old bones and a rusted hilt jutting from its flanks, bubbles welling and bursting on its skin.
    Slain, it slumps and spreads into a puddle."""
    squash = 1 + math.sin(t * (9 if e.state == "chase" else 4)) * 0.12
    if e.state == "windup":
        squash = 1.35
    if e.state == "attack":
        squash = 0.7
    fall = death_fall(e, 0.8)
    if e.state == "dead":
        squash = 1 + 1.2 * fall
    green = (200, 220, 160) if e.state == "hurt" else SLIME
    h = 0.7 / squash  # body height
    r.part("sphere", 0.05, 0.14, 0, 1.12 * squash, 0.28, 1.12 * squash, (46, 84, 40))  # the spreading foot
    r.part("sphere", 0, 0.32 / squash, 0, 0.95 * squash, h, 0.95 * squash, green)
    r.part("sphere", -0.08, 0.42 / squash, 0.1, 0.6 * squash, h * 0.7, 0.6 * squash, _bright(green, 1.0, 14))
    for i in range(5):  # drips beading round the foot
        a = i * 1.26 + 0.4
        r.part(
            "sphere",
            math.cos(a) * 0.5 * squash,
            0.04,
            math.sin(a) * 0.5 * squash,
            0.12,
            0.08,
            0.12,
            (40, 76, 36),
        )
    top = 0.32 / squash + h / 2
    # The swallowed dead: a skull in the crown, a thigh bone and a rib, and a hilt.
    with r.at(0.18 * squash, top - 0.1 - 0.15 * fall, -0.05, rz=-0.3, ry=0.3, s=0.75):
        skull(r, (190, 196, 150), (120, 230, 90), glow=e.state != "dead")
    r.part(
        "cube",
        -0.25 * squash,
        0.3 / squash + 0.1,
        0.35 * squash,
        0.06,
        0.4,
        0.06,
        (200, 196, 160),
        rx=0.9,
        rz=0.4,
    )
    r.part("cube", 0.1, 0.25 / squash + 0.1, -0.42 * squash, 0.05, 0.3, 0.05, (200, 196, 160), rx=-1.1)
    with r.at(-0.3 * squash, top - 0.12, -0.15, rz=0.6, rx=-0.3):
        r.part("cube", 0, 0.12, 0, 0.05, 0.22, 0.05, (70, 50, 36))
        r.part("cube", 0, 0.24, 0, 0.05, 0.04, 0.2, (110, 80, 56))
        r.part("blade", 0, 0.04, 0, 0.02, 0.12, 0.08, (110, 92, 70))
    for i in range(3):  # bubbles welling up the skin and bursting
        k = (t * 0.6 + i / 3) % 1.0
        a = i * 2.1
        rad = 0.42 * squash * (1 - k * 0.6)
        size = 0.06 + 0.08 * math.sin(k * math.pi)
        r.part(
            "sphere",
            math.cos(a) * rad,
            0.12 + (top - 0.12) * k,
            math.sin(a) * rad,
            size,
            size,
            size,
            (120, 170, 96),
        )
    r.part("sphere", 0.38 * squash, 0.4 / squash, -0.18, 0.1, 0.1, 0.1, (230, 220, 120))  # its own eyes
    r.part("sphere", 0.38 * squash, 0.4 / squash, 0.18, 0.1, 0.1, 0.1, (230, 220, 120))


CHAR = (52, 42, 38)


def cinder_wisp(r, e, t):
    """A burnt skull afloat in its own pyre: a crown of flame behind it, ember shards wheeling round it
    and a guttering tail of fire beneath. Slain, it gutters out and sinks, cooling as it falls."""
    fade = death_fall(e, 0.9)
    bob = math.sin(t * 3) * 0.15 * (1 - fade)
    lit = fade < 0.5
    hot = (255, 230, 140) if e.state == "windup" else EMBER
    flame = hot if lit else (90, 60, 50)
    with r.at(0, e.type.hover + bob - 0.3 * fade, 0, s=1 - 0.35 * fade):
        for i in range(3):  # the crown of flame behind the skull
            a = (i - 1) * 0.5
            k = 1 + 0.15 * math.sin(t * 9 + i * 2)
            r.part(
                "cone",
                -0.08,
                0.2 + 0.05 * (i == 1),
                a * 0.4,
                0.26,
                0.5 * k * (1 - fade),
                0.26,
                flame,
                rz=a * 0.3,
                glow=lit,
            )
        r.part("sphere", -0.1, 0.0, 0, 0.42, 0.46, 0.42, (200, 70, 30) if lit else (80, 50, 40), glow=lit)
        with r.at(0.06, 0.0, 0, s=1.35):
            skull(r, CHAR, hot if lit else (40, 20, 14), glow=lit, jaw=0.25 + 0.3 * (e.state == "windup"))
        for i in range(4):  # ember shards wheeling round it
            a = t * 3.5 + i * math.pi / 2
            r.part(
                "wedge",
                math.cos(a) * 0.48,
                math.sin(t * 5 + i) * 0.15,
                math.sin(a) * 0.48,
                0.06,
                0.14,
                0.04,
                (255, 200, 90) if lit else (90, 60, 50),
                ry=-a,
                rz=t * 4 + i,
                glow=lit,
            )
        for i in range(3):  # the tail, guttering away below
            k = 1 + 0.2 * math.sin(t * 11 + i)
            r.part(
                "cone",
                -0.05 * i,
                -0.3 - i * 0.18,
                0,
                0.3 - i * 0.08,
                0.3 * k,
                0.3 - i * 0.08,
                flame,
                rz=math.pi,
                glow=lit,
            )


def _warden_arms(e, t):
    """(sword arm, free arm, blade direction, elbow, twist, crouch, glowing sword) for the Warden's
    moves; the arms are chop_angle-style shoulder angles and the blade a blade_angle-style direction.
    Combo: three alternating cuts. Slam: both arms high, then down. Eruption: the blade is driven
    point-down into the floor. Kindle: the blade held straight up, trembling."""
    hit, blade, elbow = chop_angle(e), blade_angle(e), elbow_bend(e)
    free = 0.0
    twist = crouch = 0.0
    glow = False
    kind = e.attack_kind
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    up = _ease(k)  # how far a windup has raised the blade
    raised = (
        _mix(0.0, CHOP_RAISED, up),
        _mix(BLADE_REST, BLADE_RAISED, up),
        _mix(ELBOW_REST, ELBOW_COCKED, up),
    )
    if kind == "combo" and e.state == "attack":
        i = e.combo_swing
        u = (e.state_t - i * COMBO_GAP) / COMBO_GAP
        lift = _ease(min(u / 0.35, 1)) if u < 0.35 else 1 - _ease(min((u - 0.35) / 0.25, 1))
        hit = _mix(CHOP_LANDED, CHOP_RAISED - 0.4, lift)
        blade = _mix(BLADE_LANDED, BLADE_RAISED, lift)
        elbow = _mix(ELBOW_STRIKE, ELBOW_COCKED, lift)
        twist = 0.35 if i % 2 == 0 else -0.35
    elif kind == "slam" and e.state in ("windup", "attack"):
        if e.state == "windup":
            hit, blade, elbow = raised
            free = hit
            glow = True
        else:
            d = _ease(min(e.state_t / 0.12, 1))
            hit = free = _mix(CHOP_RAISED, CHOP_LANDED, d)
            blade, elbow = _mix(BLADE_RAISED, BLADE_LANDED, d), _mix(ELBOW_COCKED, ELBOW_STRIKE, d)
            crouch = -0.25 * d
    elif kind == "eruption" and e.state in ("windup", "attack"):
        if e.state == "windup":
            hit, blade, elbow = raised
        else:
            # Arm thrust forward and down, the point stabbing straight into the floor.
            hit, blade, elbow, crouch = 1.5, -math.pi / 2 + 0.35, 0.1, -0.2
        glow = True
    elif kind == "kindle" and e.state in ("windup", "attack"):
        hit = _mix(0.0, math.pi - 0.1, up) + math.sin(t * 40) * 0.05
        blade = _mix(BLADE_REST, math.pi / 2, up)
        elbow = _mix(ELBOW_REST, 0.15, up)
        glow = True
    return hit, free, blade, elbow, twist, crouch, glow


PLATE = (82, 78, 76)
PLATE_DARK = (58, 56, 56)
PLATE_EDGE = (124, 118, 112)
TABARD = (74, 68, 62)
COLD_EMBER = (70, 40, 30)


def ashen_warden(r, e, t):
    """The keep's warden: a giant in soot-black plate under a ragged ash-grey tabard and cape, a crested
    great-helm with an ember burning behind its visor, a sigil smouldering on his breastplate and a
    greatsword in his fist. In his second phase the plate cracks open on the fire inside and his blade
    burns. Slain, he sinks to his knees, braced on his blade, slumps, and every fire goes out."""
    swing = walk_cycle(e, t) * 0.7
    kneel = death_fall(e, 0.6)
    slump = death_fall(e, 1.6)
    dead = e.state == "dead"
    # Boss moves share the spider's timing: a sweep coils then spins him round, a leap crouches
    # then arcs him through the air. Embers: the free hand rises glowing, then flings forward.
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit, free, blade, elbow, twist, crouch, glow = _warden_arms(e, t)
    cinders = e.attack_kind == "cinders" and e.state in ("windup", "attack")
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    if cinders:
        free = -1.9 * k if e.state == "windup" else -1.9 + 1.4 * min(e.state_t / 0.15, 1)
    burning = e.phase2 and not dead
    fire = EMBER if not dead else COLD_EMBER
    steel = EMBER if burning else IRON
    cloth = math.sin(t * 2.2) * 0.08 + swing * 0.15
    with (
        r.at(0, lift * 0.8 + crouch - 0.42 * kneel, 0, s=1.35, ry=spin + twist),
        r.at(0, 0.95, 0, rz=-0.45 * slump),
        r.at(0, -0.95, 0),
    ):
        seam = (lambda rgb: EMBER) if burning else (lambda rgb: rgb)  # phase two: the plate's edges glow
        # Legs: a ridged cuisse, a faceted knee cop with a fan wing, a ridged greave and a sabaton of
        # overlapping lames closing in a pointed toe; kneeling, the shins fold under.
        for side, a in ((-0.18, swing), (0.18, -swing)):
            out = 1 if side > 0 else -1
            with r.at(0, 0.95, side, rz=a + 1.4 * kneel):
                r.part("cube", 0, -0.22, 0, 0.22, 0.46, 0.2, PLATE)
                r.part("lozenge", 0.1, -0.2, 0, 0.04, 0.36, 0.08, PLATE_EDGE)  # the cuisse's ridge
                r.part(
                    "cube", 0.02, -0.02, 0, 0.24, 0.05, 0.22, seam(PLATE_DARK), glow=burning
                )  # its top lame
                r.part("lozenge", 0.1, -0.46, 0, 0.1, 0.16, 0.16, PLATE_EDGE, rx=math.pi / 2)  # knee cop
                r.part("wedge", 0.05, -0.46, out * 0.11, 0.12, 0.14, 0.05, PLATE_DARK, rz=math.pi / 2)  # fan
                with r.at(0, -0.46, 0, rz=-0.1 * max(0.0, a) - 2.3 * kneel):
                    r.part("cube", 0, -0.21, 0, 0.19, 0.44, 0.17, PLATE_DARK)  # greave
                    r.part("lozenge", 0.09, -0.22, 0, 0.03, 0.36, 0.06, PLATE)  # its ridge
                    if burning:
                        r.part("cube", 0.1, -0.2, 0.06 * out, 0.02, 0.28, 0.02, EMBER, glow=True)
                    for i in range(3):  # sabaton lames, each overlapping the next
                        r.part(
                            "cube", 0.02 + i * 0.07, -0.42 - i * 0.012, 0, 0.12, 0.07, 0.2 - i * 0.01, PLATE
                        )
                    r.part("wedge", 0.27, -0.45, 0, 0.09, 0.12, 0.16, PLATE_DARK, rz=-math.pi / 2)
        # Faulds in three lames, square tassets hung over each thigh, and a straight-hemmed tabard
        # between the legs bearing the keep's sigil (a diamond with a bar through it).
        r.part("cube", 0, 1.0, 0, 0.38, 0.22, 0.52, PLATE_DARK)
        for i in range(3):
            r.part("cube", 0.12 - i * 0.01, 0.92 - i * 0.08, 0, 0.18, 0.07, 0.5 - i * 0.03, PLATE, rz=-0.25)
        for side in (-1, 1):
            with r.at(0.06, 0.94, side * 0.22, rx=side * 0.18):
                for i in range(2):
                    r.part(
                        "cube", 0.02, -0.08 - i * 0.12, 0, 0.26, 0.13, 0.22, PLATE if i == 0 else PLATE_DARK
                    )
                r.part("cube", 0.15, -0.26, 0, 0.02, 0.02, 0.22, seam(PLATE_EDGE), glow=burning)  # the edge
        with r.at(0.2, 0.98, 0, rz=cloth):
            r.part("cube", 0, -0.32, 0, 0.03, 0.64, 0.3, TABARD)
            r.part("cube", 0.01, -0.62, 0, 0.03, 0.04, 0.31, _dim(TABARD, 0.6))  # the straight hem
            r.part("cube", 0.02, -0.25, 0, 0.01, 0.12, 0.12, fire, rx=math.pi / 4, glow=not dead)  # sigil
            r.part("cube", 0.025, -0.25, 0, 0.01, 0.02, 0.2, _dim(TABARD, 0.5))  # the bar across it
            for z in (-0.13, 0.13):
                r.part("cube", 0.015, -0.32, z, 0.01, 0.6, 0.015, _dim(TABARD, 0.6))  # the selvedges
        # The cape: five straight-cut strips of differing length under a stiff collar band.
        r.part("cube", -0.25, 1.66, 0, 0.06, 0.08, 0.66, PLATE_DARK)
        for i, (z, drop) in enumerate(((-0.26, 1.2), (-0.13, 1.05), (0.0, 1.28), (0.13, 1.0), (0.26, 1.16))):
            with r.at(-0.26, 1.66, z, rz=-cloth * (1 + 0.2 * i) - 0.15 - 1.1 * kneel):
                r.part(
                    "cube", 0, -drop / 2, 0, 0.03, drop, 0.13, TABARD if i % 2 == 0 else _dim(TABARD, 0.85)
                )
                if burning:  # the hem smoulders
                    r.part("cube", 0.02, -drop + 0.03, 0, 0.02, 0.05, 0.12, EMBER, glow=True)
        # Breastplate: two faceted halves meeting at a raised centre ridge, the sigil on the ridge, a
        # riveted plackart over the belly, and a rim along the bottom.
        r.part("cube", 0, 1.38, 0, 0.42, 0.56, 0.64, PLATE)
        for side in (-1, 1):
            r.part("cube", 0.18, 1.42, side * 0.16, 0.08, 0.44, 0.3, PLATE, ry=side * 0.35)  # a facet
            r.part("cube", 0.21, 1.42, side * 0.31, 0.02, 0.44, 0.02, seam(PLATE_EDGE), glow=burning)
        r.part("lozenge", 0.23, 1.4, 0, 0.06, 0.5, 0.08, PLATE_EDGE)  # the centre ridge
        r.part("cube", 0.26, 1.5, 0, 0.03, 0.14, 0.14, fire, rx=math.pi / 4, glow=not dead)
        r.part("cube", 0.215, 1.22, 0, 0.06, 0.18, 0.46, PLATE_DARK)  # plackart
        for z in (-0.19, -0.06, 0.06, 0.19):
            r.part("cube", 0.25, 1.28, z, 0.02, 0.03, 0.03, PLATE_EDGE)  # its rivets
        r.part("cube", 0, 1.13, 0, 0.44, 0.06, 0.66, PLATE_DARK)  # the lower rim
        if burning:  # the plate splits on the fire inside
            for y, z, a in ((1.3, -0.15, 0.5), (1.45, 0.18, -0.6), (1.22, 0.05, 1.2)):
                r.part("cube", 0.24, y, z, 0.01, 0.22, 0.03, EMBER, rx=a, glow=True)
        # Gorget: three square lames stepping up to the helm.
        for i in range(3):
            r.part(
                "cube",
                0,
                1.69 + i * 0.05,
                0,
                0.36 - i * 0.04,
                0.05,
                0.38 - i * 0.04,
                PLATE_DARK if i % 2 else PLATE,
            )
        # The great-helm: a squared bucket with a faceted brow, a ridged bevor down its face, a visor slot
        # with three bars over the ember behind it, rivets at the temples and a stepped comb on top.
        with r.at(0.02, 1.92, 0):
            r.part("cube", 0, 0, 0, 0.32, 0.34, 0.3, PLATE)
            r.part("wedge", 0, 0.24, 0, 0.32, 0.16, 0.3, PLATE_DARK, ry=math.pi / 2)  # the point
            r.part("cube", 0.15, 0.1, 0, 0.04, 0.04, 0.31, PLATE_EDGE)  # brow
            r.part("lozenge", 0.17, -0.1, 0, 0.05, 0.16, 0.06, PLATE_EDGE)  # bevor ridge
            r.part("cube", 0.16, 0.03, 0, 0.02, 0.05, 0.22, fire, glow=not dead)  # the ember behind the slit
            bar = fire if burning else PLATE_DARK
            for z in (-0.07, 0.0, 0.07):
                r.part("cube", 0.17, 0.03, z, 0.02, 0.07, 0.018, bar, glow=burning)  # visor bars
            for z in (-0.06, 0.06):
                r.part("cube", 0.165, -0.11, z, 0.02, 0.08, 0.015, PLATE_DARK)  # breaths
            for side in (-1, 1):
                r.part("cube", 0.04, 0.03, side * 0.155, 0.04, 0.04, 0.02, PLATE_EDGE)  # temple rivets
                r.part("cube", -0.02, -0.04, side * 0.152, 0.26, 0.02, 0.01, seam(PLATE_DARK), glow=burning)
            for i in range(3):  # the comb, stepping down toward the back
                r.part("wedge", 0.06 - i * 0.12, 0.33 - i * 0.03, 0, 0.13, 0.16 - i * 0.03, 0.04, PLATE_EDGE)
            r.part("cone", 0.02, 0.42, 0, 0.07, 0.16, 0.07, PLATE_DARK)
        # Pauldrons: three angular lames over each shoulder, a trimmed edge, and a haute-piece standing
        # up beside the neck.
        for side in (-1, 1):
            with r.at(0, 1.72, side * 0.43, rx=side * 0.3):
                r.part("cube", 0, 0, 0, 0.36, 0.12, 0.3, PLATE)
                r.part("cube", 0, -0.09, side * 0.05, 0.34, 0.09, 0.28, PLATE_DARK)
                r.part("cube", 0, -0.17, side * 0.09, 0.3, 0.08, 0.24, PLATE)
                r.part("cube", 0.0, 0.07, -side * 0.02, 0.06, 0.05, 0.3, PLATE_EDGE)
                r.part("cube", 0.17, -0.06, side * 0.04, 0.02, 0.2, 0.3, seam(PLATE_EDGE), glow=burning)
                r.part("cube", 0, 0.11, -side * 0.13, 0.3, 0.14, 0.03, PLATE_DARK)  # haute-piece
        # The free arm: upper arm, vambrace, and a gauntlet; embers gather in it for a throw.
        with r.at(0, 1.6, -0.47, rz=free - 0.3 * kneel):
            r.part("cube", 0, -0.17, 0, 0.16, 0.36, 0.16, PLATE)
            r.part("lozenge", 0, -0.36, 0, 0.15, 0.13, 0.15, PLATE_EDGE, rx=math.pi / 2)  # couter
            r.part("wedge", -0.06, -0.36, 0, 0.1, 0.12, 0.12, PLATE_DARK, rz=math.pi / 2)  # its fan
            with r.at(0, -0.36, 0, rz=0.25):
                r.part("cube", 0, -0.17, 0, 0.15, 0.34, 0.15, PLATE_DARK)
                r.part("cube", 0.08, -0.17, 0, 0.02, 0.3, 0.05, PLATE_EDGE)  # the vambrace's ridge
                with r.at(0, -0.36, 0):
                    hand(r, PLATE, 0.13, curl=0.6)
                    if cinders and e.state == "windup":
                        with r.at(0.05, -0.12, 0):
                            fireball(r, EMBER, t, k)
        # The sword arm: upper arm, forearm bent at the elbow, and a gauntlet round the hilt. Slain, he
        # leans on the sword, its point on the floor.
        with r.at(0, 1.6, 0.47, rz=hit - 0.5 * kneel):
            r.part("cube", 0, -0.19, 0, 0.17, 0.38, 0.17, PLATE)
            r.part("lozenge", 0, -0.38, 0, 0.15, 0.13, 0.15, PLATE_EDGE, rx=math.pi / 2)  # couter
            r.part("wedge", -0.06, -0.38, 0, 0.1, 0.12, 0.12, PLATE_DARK, rz=math.pi / 2)
            elbow = _mix(elbow, 0.2, kneel)
            with r.at(0, -0.38, 0, rz=elbow):
                r.part("cube", 0, -0.17, 0, 0.15, 0.36, 0.15, PLATE_DARK)
                r.part("cube", 0.08, -0.17, 0, 0.02, 0.3, 0.05, PLATE_EDGE)
                r.part("cube", 0, -0.3, 0, 0.18, 0.06, 0.18, PLATE_EDGE)  # the gauntlet's cuff
                # Slain, he leans on the sword, its point on the floor ahead (the body slumps forward by
                # 0.45 * slump, so that is undone to keep the point where it rests).
                point = _mix(blade, -0.42 + 0.45 * slump, kneel)
                wrist = aim_wrist(point, hit - 0.5 * kneel + elbow)
                with r.at(0, -0.38, 0), held(r, wrist, PLATE, size=0.17, splay=0.3):
                    lit = burning or (glow and not dead)
                    sword_parts(
                        r, 1.55, 0.16, steel, grip=(54, 36, 26), guard=PLATE_DARK, glow=lit,
                        pommel="wheel", ricasso=0.1, ricasso_rgb=PLATE_DARK,
                    )  # fmt: skip
                    if lit:
                        _flame(r, 1.0, 0.0, 0, 0.12 + (0.06 if burning else 0.0), t)


LEATHER = (84, 60, 44)
SACKCLOTH = (124, 108, 82)
STITCH = (40, 30, 24)


def sack_hood(r, eyes=2, glow_rgb=None, mouth=True):
    """A sackcloth hood over a head, facing +X at the origin: coarse seams, drawstring at the neck,
    one or two cut eyeholes (lit when `glow_rgb` is given) and a crude stitched mouth."""
    r.part("sphere", 0, 0, 0, 0.44, 0.46, 0.42, SACKCLOTH)
    r.part("cube", 0.0, 0.0, 0, 0.45, 0.46, 0.02, _dim(SACKCLOTH, 0.82))  # the seam over the crown
    r.part("cyl", -0.02, -0.2, 0, 0.36, 0.05, 0.34, STITCH)  # the drawstring
    for z in (-0.09, 0.09)[:eyes] if eyes == 2 else (-0.09,):
        r.part("cube", 0.2, 0.03, z, 0.04, 0.06, 0.07, glow_rgb or (20, 14, 10), glow=glow_rgb is not None)
    if eyes == 1:  # the other eye sewn shut with an X
        r.part("cube", 0.205, 0.03, 0.09, 0.02, 0.09, 0.015, STITCH, rx=0.7)
        r.part("cube", 0.205, 0.03, 0.09, 0.02, 0.09, 0.015, STITCH, rx=-0.7)
    if mouth:
        r.part("cube", 0.2, -0.11, 0, 0.03, 0.02, 0.2, STITCH)
        for z in (-0.07, 0.0, 0.07):
            r.part("cube", 0.205, -0.11, z, 0.02, 0.07, 0.012, STITCH)


def gaoler(r, e, t):
    """A hulking, hunched jailer in a sackcloth hood and a riveted leather jerkin: a cudgel in one
    hand, a hooked chain in the other, a ring of keys and a lantern on his belt. The hook whirls
    overhead, then flies out at you. Slain, he drops to his knees and pitches forward onto his face."""
    swing = walk_cycle(e, t) * 0.6
    kneel = death_fall(e, 0.5)
    pitch = death_fall(e, 1.2)
    dead = e.state == "dead"
    hooking = e.attack_kind == "hook" and e.state in ("windup", "attack")
    k = min(e.state_t / max(e.windup_time, 1e-3), 1) if e.state == "windup" else 1.0
    skin = (240, 220, 200) if e.state == "hurt" else (150, 120, 100)
    with r.at(0, 0.45 - 0.4 * kneel, 0, rz=-1.25 * pitch), r.at(0, -0.45, 0):
        for side, a in ((-0.22, swing), (0.22, -swing)):
            with r.at(0, 0.85, side, rz=a - 1.5 * kneel):
                r.part("cube", 0, -0.42, 0, 0.26, 0.84, 0.24, LEATHER)
                for i in range(3):  # the wraps round his shins
                    r.part(
                        "cube", 0, -0.52 - i * 0.1, 0, 0.28, 0.04, 0.26, (110, 96, 72), rx=0.15 * (-1) ** i
                    )
                r.part("cube", 0.06, -0.84, 0, 0.36, 0.12, 0.26, (50, 40, 32))
        with r.at(0, 0.9, 0, rz=-0.25):  # the hunch
            r.part("cube", 0.02, 0.45, 0, 0.62, 0.9, 0.8, skin)
            r.part("sphere", -0.12, 0.72, 0, 0.6, 0.55, 0.85, skin)  # the hump of his back
            r.part("cube", 0.08, 0.42, 0, 0.5, 0.84, 0.82, LEATHER)  # jerkin
            for y in (0.2, 0.45, 0.7):  # its rivets
                for z in (-0.25, 0.25):
                    r.part("cube", 0.335, y, z, 0.03, 0.04, 0.04, RIVET_IRON)
            r.part("cube", 0.36, 0.35, 0.1, 0.02, 0.2, 0.18, (90, 30, 26))  # old stains
            r.part("cube", 0, 0.05, 0, 0.66, 0.1, 0.84, (60, 46, 36))  # belt
            r.part("cyl", 0.28, -0.08, -0.3, 0.16, 0.02, 0.16, BRASS, rz=math.pi / 2)  # the key ring
            for i in range(3):
                r.part("cube", 0.3, -0.18, -0.36 + i * 0.06, 0.02, 0.14, 0.03, BRASS, rx=0.2 * (i - 1))
            with r.at(0.22, -0.05, 0.36):  # a horn lantern on the belt
                r.part("cube", 0, -0.12, 0, 0.13, 0.18, 0.13, DARK_IRON)
                r.part(
                    "cube",
                    0,
                    -0.12,
                    0,
                    0.15,
                    0.12,
                    0.09,
                    (255, 180, 80) if not dead else (70, 50, 34),
                    glow=not dead,
                )
                r.part("cone", 0, 0.01, 0, 0.12, 0.08, 0.12, DARK_IRON)
            with r.at(0.2, 1.05, 0):  # hooded head, thrust forward
                sack_hood(r)
                r.part("cone", -0.05, 0.25, 0, 0.3, 0.3, 0.3, SACKCLOTH)
        # The cudgel arm.
        # Gripped at the end of its haft, the cudgel swings with the wrist; slain, it slips down.
        shoulder = (0.0 if hooking else chop_angle(e)) - 0.6 * kneel
        elbow = ELBOW_REST if hooking else elbow_bend(e)
        wrist = aim_wrist(BLADE_REST, ELBOW_REST) if hooking else wrist_angle(e)
        with r.at(0, 1.65, 0.5, rz=shoulder):
            r.part("cube", 0, -0.2, 0, 0.22, 0.42, 0.22, skin)
            with r.at(0, -0.4, 0, rz=elbow):
                r.part("cube", 0, -0.2, 0, 0.19, 0.42, 0.19, skin)
                r.part("cube", 0, -0.3, 0, 0.21, 0.12, 0.21, LEATHER)  # a bracer
                slip = aim_wrist(-math.pi / 2, shoulder + elbow)
                with r.at(0, -0.44, 0), held(r, _mix(wrist, slip, kneel), skin, size=0.18, splay=0.3):
                    r.part("cyl", 0.4, 0, 0, 0.1, 0.95, 0.1, (90, 64, 40), rz=math.pi / 2)
                    r.part("cyl", 0.85, 0, 0, 0.2, 0.3, 0.2, (70, 50, 32), rz=math.pi / 2)
                    for i in range(4):
                        a = i * math.pi / 2
                        r.part(
                            "wedge",
                            0.85,
                            math.cos(a) * 0.11,
                            math.sin(a) * 0.11,
                            0.05,
                            0.08,
                            0.05,
                            IRON,
                            rx=a,
                        )
        # The chain arm: upper arm, elbow, forearm and hand. The hook circles overhead on the windup
        # and flies out on the throw.
        if hooking and e.state == "windup":
            arm, whirl = -2.6, t * 14
        elif hooking:
            arm, whirl = -2.6 + 3.4 * min(e.state_t / 0.12, 1), None
        else:
            arm, whirl = swing * 0.5 - 0.3 * kneel, None
        with r.at(0, 1.65, -0.5, rz=arm):
            r.part("cube", 0, -0.2, 0, 0.21, 0.42, 0.21, skin)
            r.part("cube", 0, -0.6, 0, 0.19, 0.38, 0.19, skin)
            r.part("cube", 0, -0.66, 0, 0.21, 0.12, 0.21, LEATHER)
            with r.at(0, -0.8, 0):
                hand(r, skin, 0.15, curl=0.8)
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


RIVET_IRON = (120, 116, 112)
CLEAVER = (150, 146, 140)


def cleaver_parts(r, length=1.0, steel=CLEAVER):
    """A butcher's cleaver in a `held` frame: a short wrapped handle through the fist and a broad,
    square blade hanging below its spine, its bright edge ground to a bevel."""
    r.part("cube", 0.0, 0, 0, 0.36, 0.07, 0.07, (70, 50, 34))
    for x in (-0.08, 0.08):
        r.part("cube", x, 0, 0, 0.03, 0.08, 0.08, DARK_IRON)  # rivets through the scales
    r.part("cube", -0.18, 0, 0, 0.06, 0.09, 0.09, DARK_IRON)  # the butt cap
    blade = length - 0.2
    r.part("cube", 0.18 + blade / 2, -0.1, 0, blade, 0.32, 0.04, steel)
    r.part("wedge", 0.18 + blade / 2, -0.3, 0, 0.05, 0.08, blade, _bright(steel), ry=math.pi / 2, rz=math.pi)
    r.part("cube", 0.18 + blade / 2, 0.06, 0, blade, 0.04, 0.06, _dim(steel))  # the spine
    r.part("cube", 0.18 + blade * 0.85, -0.02, 0, 0.08, 0.08, 0.05, (20, 16, 14))  # the hanging hole
    r.part("cube", 0.18 + blade * 0.4, -0.18, 0, 0.18, 0.14, 0.045, (90, 26, 22))  # dried blood


MEAT = (160, 118, 98)
APRON = (88, 62, 46)
GORE = (96, 30, 26)


def butcher(r, e, t):
    """The keep's slaughterman: a huge, lumpen brute, pot-bellied and humpbacked, in a stitched
    leather apron black with old blood, a chain belt hung with meat hooks and a sack hood with one
    eye cut and the other sewn shut, a cleaver as long as a man's arm in one fist. His moves share
    the Warden's arm poses. Enraged, his apron runs wet, his eye burns red and steam rolls off him.
    Slain, he drops to his knees and pitches forward onto his face."""
    swing = walk_cycle(e, t) * 0.5
    kneel = death_fall(e, 0.6)
    pitch = death_fall(e, 1.4)
    dead = e.state == "dead"
    rage = e.phase2 and not dead
    lift, spin, _, _ = _spider_move(e, t, 0.0, 1.0)
    hit, free, blade, elbow, twist, crouch, _ = _warden_arms(e, t)
    skin = (240, 220, 200) if e.state == "hurt" else (176, 110, 92) if rage else MEAT
    apron = (110, 26, 22) if e.phase2 else APRON
    with (
        r.at(0, lift * 0.6 + crouch + 0.55 - 0.4 * kneel, 0, s=1.3, ry=spin + twist),
        r.at(0, 0, 0, rz=-1.2 * pitch),
        r.at(0, -0.55, 0),
    ):
        for side, a in ((-0.24, swing), (0.24, -swing)):
            with r.at(0, 0.8, side, rz=a - 1.5 * kneel):
                r.part("cube", 0, -0.4, 0, 0.28, 0.8, 0.26, (70, 54, 42))
                for i in range(3):  # rag wraps
                    r.part(
                        "cube", 0, -0.45 - i * 0.12, 0, 0.3, 0.05, 0.28, (120, 100, 76), rx=0.2 * (-1) ** i
                    )
                r.part("cube", 0.07, -0.8, 0, 0.38, 0.12, 0.28, (46, 36, 30))
        with r.at(0, 0.85, 0, rz=-0.2):  # the hunched bulk: chest, belly, hump and shoulders
            r.part("sphere", 0.02, 0.5, 0, 0.8, 1.0, 0.95, skin)
            r.part("sphere", 0.16, 0.2, 0, 0.62, 0.62, 0.8, skin)  # the belly
            r.part("sphere", -0.2, 0.85, 0, 0.58, 0.55, 0.8, _dim(skin, 0.92))  # the hump
            for side in (-1, 1):
                r.part("sphere", 0, 0.9, side * 0.42, 0.42, 0.38, 0.4, skin)
            r.part("cube", 0.32, 0.25, 0, 0.3, 0.95, 0.74, apron)  # apron
            for z in (-0.2, 0.2):  # its seams
                r.part("cube", 0.475, 0.25, z, 0.015, 0.9, 0.02, STITCH)
            r.part("cube", 0.48, 0.1, -0.1, 0.02, 0.4, 0.28, GORE)  # old blood
            r.part("cube", 0.48, 0.45, 0.15, 0.02, 0.2, 0.18, GORE)
            r.part("cube", 0.48, -0.15, 0.05, 0.02, 0.18, 0.12, GORE)
            r.part("cube", 0.1, 0.78, 0, 0.82, 0.08, 0.98, (54, 40, 32))  # the apron's strap
            r.part("cube", 0.12, -0.02, 0, 0.82, 0.06, 0.92, DARK_IRON)  # chain belt
            for i, z in enumerate((-0.32, 0.38)):  # meat hooks swinging from it
                with r.at(0.42, -0.04, z, rx=math.sin(t * 3 + i * 2) * 0.25):
                    r.part("cube", 0, -0.12, 0, 0.025, 0.24, 0.025, IRON)
                    r.part("wedge", 0, -0.27, 0.03, 0.025, 0.1, 0.06, STEEL, rx=-2.3)
            with r.at(0.22, 1.12, 0):  # the hooded head, thrust forward
                sack_hood(r, eyes=1, glow_rgb=(255, 60, 40) if rage else None)
            if rage:  # steam rolling off his shoulders
                for i in range(3):
                    k = (t * 0.8 + i / 3) % 1.0
                    size = 0.12 + 0.2 * k
                    side = (-1, 1, -1)[i]
                    r.part(
                        "sphere",
                        -0.1,
                        1.05 + k * 0.6,
                        side * (0.3 + 0.1 * k),
                        size,
                        size,
                        size,
                        (150, 140, 136),
                    )
        # The free arm hangs, or rises with the cleaver arm for a two-handed chop; a meaty hand.
        with r.at(0, 1.7, -0.56, rz=free + swing * 0.4 - 0.4 * kneel):
            r.part("cube", 0, -0.22, 0, 0.26, 0.46, 0.26, skin)
            r.part("sphere", 0, -0.44, 0, 0.24, 0.2, 0.24, skin)  # elbow
            with r.at(0, -0.44, 0, rz=0.3 + 0.2 * swing):
                r.part("cube", 0, -0.2, 0, 0.22, 0.4, 0.22, skin)
                r.part("cube", 0, -0.32, 0, 0.24, 0.1, 0.24, LEATHER)  # a bracer
                with r.at(0, -0.42, 0):
                    hand(r, skin, 0.17, curl=0.5)
        # The cleaver arm: shoulder, elbow, and the cleaver turned at the wrist; slain, it slips.
        with r.at(0, 1.7, 0.56, rz=hit - 0.6 * kneel):
            r.part("cube", 0, -0.21, 0, 0.26, 0.44, 0.26, skin)
            elbow = _mix(elbow, 0.2, kneel)
            with r.at(0, -0.42, 0, rz=elbow):
                r.part("cube", 0, -0.2, 0, 0.22, 0.42, 0.22, skin)
                r.part("cube", 0, -0.3, 0, 0.24, 0.1, 0.24, LEATHER)
                wrist = aim_wrist(blade, hit + elbow)
                slip = aim_wrist(-math.pi / 2, hit - 0.6 * kneel + elbow)
                with r.at(0, -0.44, 0), held(r, _mix(wrist, slip, kneel), skin, size=0.2, splay=0.3):
                    cleaver_parts(r, 1.1)


def bone_crawler(r, e, t):
    """A ribcage scuttling on long jointed finger-bones, a lashing tail of vertebrae behind and a
    skull slung low in front with embers in its sockets. At rest it is only a heap of bones; slain,
    it falls apart into one again."""
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
    lit = fall < 0.5
    with r.at(0, rise, 0, rz=rear * (1 - fall)):
        with r.at(0.05, 0.14, 0, rz=-math.pi / 2):  # the ribcage, lying along the body
            ribcage(r, bone, ribs=4, width=0.38, spacing=0.1, top=0.18, depth=-0.14)
        for i in range(5):  # spine
            r.part("cube", -0.2 + i * 0.1, 0.15, 0, 0.06, 0.06, 0.07, BONE_SHADE if i % 2 else bone)
        for i in range(5):  # the tail, lashing
            a = math.sin(t * 6 - i * 0.8) * 0.15 * (i + 1) * (1 - fall)
            r.part(
                "cube",
                -0.3 - i * 0.08,
                0.15 + i * 0.03,
                a * 0.4,
                0.06 - i * 0.008,
                0.05,
                0.06 - i * 0.008,
                bone,
            )
        with r.at(0.38, 0.02, 0, rz=-0.2):
            skull(
                r,
                bone,
                (255, 120, 60) if lit else (40, 20, 14),
                glow=lit,
                jaw=0.5 if e.state == "windup" else 0.1,
            )
        for i in range(6):  # finger-bone legs, each with a knuckle
            side = 1 if i % 2 else -1
            x = -0.2 + (i // 2) * 0.2
            step = gait * (1 if (i // 2 + i) % 2 else -1)
            with r.at(x, 0, side * 0.2, rx=side * (0.9 + 0.6 * fall), ry=step):
                r.part("cube", 0, 0, side * 0.18, 0.04, 0.04, 0.36, bone)
                r.part("sphere", 0, 0, side * 0.36, 0.06, 0.06, 0.06, BONE_SHADE)
                r.part("cube", 0, -0.14, side * 0.36, 0.035, 0.3, 0.035, bone, rx=-side * 0.3)
                r.part("wedge", 0, -0.3, side * 0.4, 0.03, 0.06, 0.03, BONE_SHADE, rz=math.pi)


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
        for z in (-0.3, 0.3):  # iron bands down its sides, studded
            r.part("cube", 0, 0.25, z, 0.62, 0.5, 0.06, IRON)
            r.part("cube", 0.315, 0.12, z, 0.02, 0.04, 0.04, RIVET_IRON)
        r.part("cube", 0.31, 0.32, 0, 0.03, 0.12, 0.1, BRASS)  # the lock plate, now a gullet's hinge
        r.part("cube", 0.02, 0.46, 0, 0.5, 0.08, 0.78, (90, 14, 20))  # maw
        r.part("cube", -0.05, 0.43, 0, 0.36, 0.06, 0.6, (50, 6, 12))  # the dark throat
        for i in range(7):  # two rows of teeth, the inner ones shorter
            r.part("wedge", 0.27, 0.56, -0.36 + i * 0.12, 0.05, 0.18, 0.06, BONE)
            if i % 2:
                r.part("wedge", 0.16, 0.54, -0.36 + i * 0.12, 0.04, 0.11, 0.05, BONE_SHADE)
        with r.at(0.05, 0.5, 0, rz=-0.3 - gape * 0.2):  # a long tongue, lolling in three pieces
            r.part("cube", 0.1, 0, 0, 0.22, 0.05, 0.16, (190, 50, 70))
            with r.at(0.2, 0, 0, rz=-0.4 + math.sin(t * 7) * 0.3):
                r.part("cube", 0.1, 0, 0, 0.2, 0.045, 0.14, (176, 44, 64))
                with r.at(0.2, 0, 0, rz=-0.4 + math.sin(t * 7 + 1) * 0.3):
                    r.part("wedge", 0.06, 0, 0, 0.04, 0.12, 0.12, (160, 40, 60), rz=-math.pi / 2)
        with r.at(-0.3, 0.5, 0, rz=gape):
            r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, WHITE, tex="wood_plank")
            r.part("cube", 0.3, 0.17, 0, 0.62, 0.02, 0.06, IRON)  # the lid's strap
            for i in range(7):
                r.part("wedge", 0.56, -0.06, -0.36 + i * 0.12, 0.05, 0.18, 0.06, BONE, rz=math.pi)
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
        _thorns(r, 0.62, 0.08, 4)
        with r.at(0, 0.35, 0.06, rx=0.9 + sway):  # a leaf unfurling from the stem
            r.part("sphere", 0, 0.18, 0, 0.05, 0.4, 0.2, DARK_LEAF)
        with r.at(0, 0.58, 0, rz=a2):
            r.part("cyl", 0, 0.28, 0, 0.13, 0.58, 0.13, (80, 120, 54))
            _thorns(r, 0.58, 0.065, 3)
            with r.at(0, 0.55, 0, rz=a3):
                r.part("cyl", 0, 0.12, 0, 0.11, 0.26, 0.11, (80, 120, 54))
                # Undo the stem's bends so the mouth faces forward, dipping a little as it lunges.
                with r.at(0, 0.26, 0, rz=-(a1 + a2 + a3) - lunge * 0.4 - 1.1 * wilt):
                    _bloom_head(r, gape, hurt, t)


def _thorns(r, length, radius, n, rgb=(176, 150, 96)):
    """Hooked thorns spiralling up a stem (along +Y from the origin)."""
    for k in range(n):
        a = k * 2.4
        y = (k + 0.5) * length / n
        r.part(
            "wedge",
            math.cos(a) * radius,
            y,
            math.sin(a) * radius,
            0.03,
            0.09,
            0.03,
            rgb,
            ry=-a,
            rz=-math.pi / 2 + 0.4,
        )


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
    for i in range(5):  # sepals, spiked, cupping the head from behind
        a = i * 2 * math.pi / 5
        with r.at(-0.2, 0, 0, rx=a):
            r.part("wedge", -0.04, 0.16, 0, 0.04, 0.22, 0.08, DARK_LEAF, rz=0.9)
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
            for y, ang, w in ((0.35, 1.2, 0.24), (0.55, 1.6, 0.18), (0.9, -1.4, 0.2)):  # shelf fungus
                x, z = math.cos(ang) * 0.27, math.sin(ang) * 0.25
                r.part("cyl", x, y, z, w, 0.04, w, (200, 176, 120))
                r.part("cyl", x, y - 0.025, z, w * 0.8, 0.02, w * 0.8, (130, 100, 64))
            for k in range(3):  # knots weeping sap down the trunk
                r.part("sphere", 0.28, 0.4 + k * 0.32, (-0.1, 0.12, 0.0)[k], 0.1, 0.12, 0.1, DARK_BARK)
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
        for y, a, w in ((0.25, 2.4, 0.26), (0.42, 2.0, 0.2), (0.18, -2.2, 0.22)):  # bracket fungus
            r.part("cyl", math.cos(a) * 0.48, y, math.sin(a) * 0.48, w, 0.04, w, (196, 168, 110))
            r.part(
                "cyl",
                math.cos(a) * 0.48,
                y - 0.025,
                math.sin(a) * 0.48,
                w * 0.8,
                0.02,
                w * 0.8,
                (120, 90, 56),
            )
        for k in range(5):  # roots curling up over its face like the teeth of a second jaw
            a = -0.8 + k * 0.4
            r.part(
                "wedge",
                math.cos(a) * 0.5,
                0.2,
                math.sin(a) * 0.5,
                0.06,
                0.24,
                0.07,
                DARK_BARK,
                ry=-a,
                rz=-0.25,
            )
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
    if e.type.id == "loom_mother":  # an egg sac slung under her abdomen, its brood stirring in it
        with r.at(-1.45, 0.9, 0, rz=math.sin(t * 1.3) * 0.05):
            r.part("sphere", 0, 0, 0, 0.78, 0.5, 0.7, (226, 222, 204))
            for k in range(4):
                a = k * 1.6 + 0.3
                r.part(
                    "sphere", math.cos(a) * 0.28, -0.12, math.sin(a) * 0.26, 0.2, 0.18, 0.2, (200, 196, 176)
                )
            r.part("cube", 0.2, 0.3, 0, 0.02, 0.5, 0.02, (236, 236, 226), rz=0.5)  # silk holding it up
    # Waist and head-chest, plated in chitin.
    r.part("cyl", -0.2, 0.98, 0, 0.32, 0.4, 0.32, body, rz=math.pi / 2)
    r.part("sphere", 0.3, 0.92, 0, 1.0, 0.62, 0.86, body)
    r.part("sphere", 0.32, 1.12, 0, 0.7, 0.3, 0.6, (64, 54, 66))
    for k, (x, w) in enumerate(((0.08, 0.5), (0.3, 0.56), (0.5, 0.42))):
        r.part("wedge", x, 1.27, 0, 0.16, 0.08, w, _dim(body, 0.8) if k % 2 else (80, 68, 84), rz=-0.2)
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
        r.part("wedge", 0.7, 0.09, 0, 0.05, 0.14, 0.05, band, rz=-0.6)  # a spur
        with r.at(1.1, 0, 0, rz=-1.9 - lift * 0.5 - 0.9 * curl):
            r.part("cube", 0.5, 0, 0, 1.0, 0.1, 0.1, body)
            r.part("cube", 1.0, 0, 0, 0.12, 0.12, 0.12, band)
            with r.at(1.0, 0, 0, rz=-0.25):
                r.part("cube", 0.4, 0, 0, 0.8, 0.07, 0.07, body)
                r.part("wedge", 0.45, 0.05, 0, 0.04, 0.09, 0.04, (40, 32, 40), rz=-0.5)  # a bristling spine


def npc(r, look, t=0.0):
    """A villager facing +X, built from a `villagers.Look`: boots and trousers (or a long robe), a belted
    tunic, an apron or cloak, jointed arms with hands, a face with brows and a nose, hair, a beard, a hat
    or hood, and whatever they hold. They idle by their trade (`look.idle`)."""
    hs, ws, stoop = villagers.BUILDS[look.build]
    sway = math.sin(t * 1.5) * 0.03
    beat = max(math.sin(t * 2.4), 0.0) ** 3  # the smith's hammer, the guard's shifting weight
    with r.at(0, 0, 0, rz=sway, s=hs):
        _villager_legs(r, look, ws)
        with r.at(0, 0.95, 0, rz=-stoop):  # everything above the hips leans with the stoop
            _villager_torso(r, look, ws)
            _villager_arms(r, look, ws, t, beat)
            with r.at(0.03, 0.72, 0, rz=stoop * 0.6 - (0.12 if look.idle == "pray" else 0.0)):
                _villager_head(r, look)
            if look.blade:  # a sheathed curved sword slung across the back
                with r.at(-0.2, 0.15, 0, rx=0.9):
                    r.part("cube", 0, 0, 0, 0.06, 1.1, 0.08, (30, 26, 30))
                    r.part("cube", 0, 0.62, 0, 0.05, 0.25, 0.05, (160, 30, 40))


def _villager_legs(r, look, ws):
    if look.garb == "robe":  # a robe falling to the ankles, hems of the boots peeping out
        r.part("cyl", 0, 0.48, 0, 0.5 * ws, 0.96, 0.56 * ws, look.cloth)
        r.part("cyl", 0, 0.06, 0, 0.56 * ws, 0.12, 0.62 * ws, _dim(look.cloth, 0.8))  # hem
        for z in (-0.1, 0.1):
            r.part("cube", 0.2, 0.04, z * ws, 0.16, 0.08, 0.1, look.boots)
        return
    for z in (-0.11, 0.11):
        r.part("cube", 0, 0.62, z * ws, 0.17, 0.5, 0.15, look.trousers)  # thigh
        r.part("cube", 0, 0.28, z * ws, 0.15, 0.4, 0.13, _dim(look.trousers, 0.9))  # shin
        r.part("cube", 0.04, 0.09, z * ws, 0.24, 0.18, 0.15, look.boots)  # boot
        r.part("cube", 0.0, 0.2, z * ws, 0.17, 0.04, 0.16, _dim(look.boots, 0.75))  # boot cuff


def _villager_torso(r, look, ws):
    w = 0.42 * ws
    r.part("cube", 0, 0.32, 0, 0.26, 0.5, w, look.cloth)  # chest
    r.part("cube", 0, 0.05, 0, 0.27, 0.16, w * 0.92, _dim(look.cloth, 0.92))  # waist
    r.part("cube", 0, 0.02, 0, 0.29, 0.06, w * 0.95, look.belt)  # belt
    r.part("cube", 0.15, 0.02, 0, 0.02, 0.06, 0.06, (170, 150, 90))  # buckle
    r.part("cube", 0, -0.12, 0, 0.27, 0.2, w * 0.98, look.cloth)  # tunic skirt over the hips
    r.part("cube", 0.12, 0.5, 0, 0.04, 0.1, 0.16, _dim(look.cloth, 0.75))  # collar
    if look.apron:
        r.part("cube", 0.14, 0.05, 0, 0.02, 0.62, w * 0.62, look.apron)
        r.part("cube", 0.14, 0.42, 0, 0.02, 0.18, w * 0.45, look.apron)  # bib
        r.part("cube", 0.155, -0.08, 0, 0.01, 0.14, w * 0.3, _dim(look.apron, 0.8))  # pocket
    if look.cloak:
        r.part("cube", -0.16, 0.05, 0, 0.05, 0.95, w * 1.15, look.cloak)
        r.part("cube", -0.05, 0.5, 0, 0.26, 0.08, w * 1.2, _dim(look.cloak, 1.1))  # mantle
        r.part("cube", 0.13, 0.48, 0, 0.03, 0.06, 0.06, (170, 150, 90))  # clasp


TOOL_WOOD = (96, 70, 44)
TOOL_IRON = (110, 110, 118)


def _villager_arms(r, look, ws, t, beat):
    """Two arms from the shoulders, each an upper arm, an elbow and a forearm ending in a hand. The
    right one (+Z) works the tool; the left rests, or both clasp in prayer."""
    sleeve = (look.cloak or look.cloth) if look.garb == "robe" else look.cloth
    for side in (1, -1):
        sh, el, tool = _arm_pose(look, side, t, beat)
        with r.at(0, 0.5, side * (0.25 * ws), rz=sh, rx=-side * 0.08):
            r.part("cube", 0, -0.16, 0, 0.12, 0.34, 0.12, sleeve)
            with r.at(0, -0.32, 0, rz=el):
                r.part("cube", 0, -0.14, 0, 0.1, 0.3, 0.1, _dim(sleeve, 0.92))
                r.part("cube", 0, -0.27, 0, 0.11, 0.05, 0.11, _dim(sleeve, 0.7))  # cuff
                with r.at(0, -0.3, 0):
                    hand(r, look.skin, size=0.09, curl=0.6 if tool else 0.2)
                    if tool:
                        with r.at(0, -0.06, 0):
                            _villager_tool(r, look.tool, t)


def _arm_pose(look, side, t, beat):
    """(shoulder, elbow, holds the tool) angles for one arm, from the idle."""
    working = side == 1 and look.tool is not None
    idle = look.idle
    if idle == "pray":
        return 0.5, 1.2, side == 1 and look.tool == "staff"
    if not working:
        return (0.05 + 0.03 * math.sin(t * 1.3 + side), 0.15, False) if idle != "count" else (0.3, 1.1, False)
    if idle == "hammer":
        return 0.2 + 1.4 * beat, 0.9 + 0.6 * (1 - beat), True
    if idle == "stir":
        return 0.6 + 0.15 * math.sin(t * 3), 0.9 + 0.2 * math.cos(t * 3), True
    if idle == "count":
        return 0.35, 1.25 + 0.08 * math.sin(t * 4), True
    if look.tool in ("spear", "staff"):
        return 0.15, 0.55, True
    if look.tool == "rod":
        return 0.7, 0.4, True
    return 0.3, 1.0, True


def _villager_tool(r, tool, t):
    """What a villager holds, in the hand's frame (the hand hangs down -Y, fingers forward +X)."""
    if tool == "hammer":  # held by the haft, head forward
        r.part("cube", 0.12, 0, 0, 0.34, 0.04, 0.04, TOOL_WOOD)
        r.part("cube", 0.3, 0, 0, 0.08, 0.1, 0.16, TOOL_IRON)
    elif tool in ("spear", "staff"):  # an upright pole through the fist
        r.part("cube", 0, 0.4, 0, 0.04, 1.9, 0.04, TOOL_WOOD)
        if tool == "spear":
            r.part("lozenge", 0, 1.45, 0, 0.06, 0.28, 0.025, TOOL_IRON)
        else:
            r.part("sphere", 0, 1.38, 0, 0.1, 0.1, 0.1, (150, 140, 110))  # a worn knob
            r.part("cube", 0, 1.3, 0, 0.06, 0.03, 0.06, (170, 150, 90))
    elif tool == "ladle":
        r.part("cube", 0.12, 0, 0, 0.3, 0.03, 0.03, TOOL_WOOD)
        r.part("sphere", 0.28, -0.03, 0, 0.09, 0.06, 0.09, TOOL_WOOD)
    elif tool == "ledger":
        r.part("cube", 0.08, 0.02, 0, 0.2, 0.04, 0.16, (110, 50, 40))
        r.part("cube", 0.08, 0.045, 0, 0.18, 0.01, 0.14, (220, 210, 180))
    elif tool == "rod":  # a fishing rod pointing out over the water, its line hanging
        with r.at(0, 0, 0, rz=0.5):
            r.part("cube", 0.8, 0, 0, 1.6, 0.025, 0.025, TOOL_WOOD)
        r.part("cube", 1.42, 0.1 - 0.4, 0, 0.005, 0.8 + 0.05 * math.sin(t), 0.005, (200, 200, 200))
    elif tool == "whetstone":
        r.part("cube", 0.06, 0, 0, 0.14, 0.05, 0.06, (120, 120, 126))
    elif tool == "tankard":
        r.part("cyl", 0.06, 0.02, 0, 0.1, 0.13, 0.1, (130, 110, 90))
        r.part("cyl", 0.06, 0.09, 0, 0.09, 0.02, 0.09, (230, 220, 200))  # froth
    elif tool == "lantern":
        r.part("cube", 0, -0.12, 0, 0.12, 0.16, 0.12, IRON)
        r.part("cube", 0, -0.12, 0, 0.08, 0.1, 0.08, (255, 200, 110), glow=True)


def _villager_head(r, look):
    skin = look.skin
    r.part("cube", 0, 0.0, 0, 0.12, 0.1, 0.12, skin)  # neck
    r.part("sphere", 0, 0.16, 0, 0.27, 0.3, 0.25, skin)
    r.part("cube", 0.125, 0.15, 0, 0.05, 0.06, 0.04, _dim(skin, 0.9))  # nose
    for z in (-0.055, 0.055):
        r.part("cube", 0.12, 0.2, z, 0.02, 0.03, 0.035, (24, 20, 18))  # eyes
        r.part("cube", 0.125, 0.235, z, 0.02, 0.02, 0.05, _dim(look.hair, 0.9))  # brows
        r.part("cube", 0.0, 0.17, z * 2.4, 0.06, 0.08, 0.03, _dim(skin, 0.92))  # ears
    r.part("cube", 0.12, 0.09, 0, 0.015, 0.015, 0.06, _dim(skin, 0.6))  # mouth
    if look.beard:
        r.part("cube", 0.09, 0.06, 0, 0.1, 0.14, 0.2, look.hair)
        r.part("cube", 0.11, 0.0, 0, 0.07, 0.1, 0.12, look.hair)
    if look.hood:  # a deep hood that hides most of the face
        r.part("sphere", -0.03, 0.2, 0, 0.36, 0.38, 0.34, look.cloak or look.cloth)
        r.part("cube", -0.1, 0.0, 0, 0.2, 0.2, 0.4, look.cloak or look.cloth)
        return
    style = look.hair_style
    if style != "bald":
        r.part("sphere", -0.03, 0.25, 0, 0.29, 0.17, 0.27, look.hair)
    else:
        r.part("sphere", -0.02, 0.26, 0, 0.25, 0.1, 0.23, _dim(skin, 0.95))  # a bare pate
    if style == "long":
        r.part("cube", -0.1, 0.08, 0, 0.1, 0.32, 0.26, look.hair)
    elif style == "bun":
        r.part("sphere", -0.13, 0.3, 0, 0.12, 0.12, 0.12, look.hair)
    if look.hat == "brim":
        r.part("cyl", 0, 0.3, 0, 0.44, 0.03, 0.44, look.hat_rgb)
        r.part("cyl", 0, 0.37, 0, 0.24, 0.13, 0.24, look.hat_rgb)
    elif look.hat == "cap":
        r.part("sphere", -0.01, 0.29, 0, 0.29, 0.14, 0.27, look.hat_rgb)
        r.part("cube", 0.13, 0.27, 0, 0.1, 0.02, 0.18, _dim(look.hat_rgb, 0.85))  # peak
    elif look.hat == "coif":  # a mail coif over the head and neck
        r.part("sphere", -0.01, 0.2, 0, 0.3, 0.3, 0.28, look.hat_rgb)
        r.part("cube", -0.04, 0.0, 0, 0.18, 0.12, 0.28, look.hat_rgb)


THRONE_STONE = (118, 114, 108)
THRONE_CUSHION = (92, 34, 40)
ENTHRONED_IRON = (54, 52, 60)


def throne(r):
    """A high-backed stone throne facing +X on a two-step dais: carved arms ending in scrolls, a worn
    red cushion, a tall back with ribbed panels rising to a pointed crest and two finials."""
    stone = THRONE_STONE
    r.part("cube", 0, 0.12, 0, 1.9, 0.24, 1.9, stone, tex="flagstone")  # lower step
    r.part("cube", -0.2, 0.36, 0, 1.4, 0.24, 1.5, _dim(stone, 0.95), tex="flagstone")  # upper step
    r.part("cube", -0.25, 0.7, 0, 0.9, 0.44, 1.1, stone, tex="rough_stone")  # seat block
    r.part("cube", -0.2, 0.95, 0, 0.8, 0.08, 0.95, THRONE_CUSHION)  # cushion
    r.part("cube", 0.2, 0.95, 0, 0.06, 0.06, 0.95, _dim(THRONE_CUSHION, 0.8))  # its rolled edge
    for side in (-1, 1):  # arms
        r.part("cube", -0.25, 1.15, side * 0.62, 0.95, 0.12, 0.2, stone, tex="rough_stone")
        r.part("cube", -0.25, 0.95, side * 0.62, 0.85, 0.36, 0.14, _dim(stone, 0.9))
        r.part("cyl", 0.22, 1.15, side * 0.62, 0.22, 0.2, 0.22, stone, rx=math.pi / 2)  # scroll end
        r.part("cube", -0.25, 2.3, side * 0.62, 0.22, 3.3, 0.22, stone, tex="rough_stone")  # back post
        r.part("cone", -0.25, 4.1, side * 0.62, 0.3, 0.6, 0.3, _dim(stone, 1.1))  # finial
    r.part("cube", -0.68, 2.35, 0, 0.18, 3.4, 1.05, stone, tex="rough_stone")  # back slab
    for z in (-0.3, 0.0, 0.3):  # ribbed panels carved in the back
        r.part("cube", -0.58, 2.2, z, 0.04, 2.6, 0.08, _dim(stone, 0.8))
    r.part("wedge", -0.68, 4.35, 0, 0.18, 0.6, 1.05, stone, tex="rough_stone")  # pointed crest
    r.part("cube", -0.58, 4.0, 0, 0.04, 0.24, 0.24, _dim(stone, 0.75), rx=math.pi / 4)  # its sigil


def enthroned(r, t):
    """The Enthroned: an ancient, gaunt figure far taller than a man, seated on the cathedral throne
    facing +X. Robes pool down the dais, long bony hands rest on the arms, and a crown of iron spikes
    rises over a face lost in shadow but for two cold glints. It never moves, save the dust that
    drifts about it and a breath every long while."""
    throne(r)
    robe = (58, 54, 64)
    under = _dim(robe, 0.7)
    skin = (150, 146, 140)
    breath = 1 + 0.015 * math.sin(t * 0.4)
    with r.at(-0.2, 1.0, 0):  # the seat
        # Legs: thighs along the seat, shins down the dais, robes pooling over them.
        for side in (-1, 1):
            r.part("cube", 0.3, 0.12, side * 0.2, 0.75, 0.2, 0.22, robe)
            r.part("cube", 0.66, -0.35, side * 0.22, 0.2, 0.85, 0.2, under)
            r.part("cube", 0.74, -0.72, side * 0.22, 0.32, 0.1, 0.16, (40, 36, 40))  # feet
        r.part("cube", 0.75, -0.45, 0, 0.12, 0.95, 0.75, robe)  # the robe's fall between the knees
        r.part("wedge", 1.0, -0.8, 0, 0.5, 0.25, 0.95, _dim(robe, 0.85), rz=math.pi / 2)  # pooled hem
        for i in range(4):  # folds in the robe
            r.part("cube", 0.82, -0.4, -0.27 + i * 0.18, 0.03, 0.85, 0.04, under)
        # Torso: long and narrow, leaning back into the throne, a chain of office over the chest.
        with r.at(-0.15, 0.25, 0, rz=0.08, s=breath):
            r.part("cube", 0, 0.55, 0, 0.36, 1.1, 0.62, robe)
            r.part("cube", 0.05, 0.95, 0, 0.3, 0.28, 0.78, _dim(robe, 1.15))  # mantle
            r.part("cube", -0.12, 0.45, 0, 0.14, 1.0, 0.7, under)  # its back
            for i in range(5):  # the chain of office
                a = (i - 2) * 0.32
                r.part("cube", 0.19, 0.78 - abs(a) * 0.5, a * 0.6, 0.03, 0.06, 0.08, (150, 130, 80))
            r.part("cube", 0.2, 0.55, 0, 0.03, 0.14, 0.12, (150, 130, 80))  # its pendant
            r.part("cube", 0.215, 0.55, 0, 0.01, 0.06, 0.04, (110, 150, 170), glow=True)
            # Arms hanging from the shoulders to the throne's arms, forearms laid along them and long
            # bony hands drooping over the carved scrolls.
            for side in (-1, 1):
                with r.at(0, 0.98, side * 0.42, rx=-side * 0.12), r.at(0, 0, 0, rz=0.12):
                    r.part("cube", 0, -0.45, 0, 0.17, 0.9, 0.17, robe)
                    with r.at(0, -0.88, 0, rz=1.5):
                        r.part("cube", 0, -0.32, 0, 0.15, 0.64, 0.15, robe)
                        r.part("cube", 0, -0.62, 0, 0.2, 0.08, 0.2, under)  # cuff
                        with r.at(0, -0.68, 0, rz=-1.3):
                            hand(r, skin, size=0.16, bony=True, curl=0.9)
            # Head: a long gaunt face lost under a cowl, two cold glints, the spiked crown.
            with r.at(0.04, 1.2, 0, rz=0.12):
                r.part("cube", 0, 0.05, 0, 0.12, 0.16, 0.14, skin)  # neck
                r.part("sphere", 0, 0.32, 0, 0.3, 0.42, 0.28, skin)
                r.part("cube", 0.12, 0.18, 0, 0.08, 0.14, 0.16, _dim(skin, 0.85))  # long jaw
                r.part("cube", 0.13, 0.36, 0, 0.06, 0.14, 0.05, _dim(skin, 0.9))  # nose
                for z in (-0.06, 0.06):
                    r.part("cube", 0.14, 0.42, z, 0.02, 0.025, 0.04, (150, 200, 230), glow=True)
                    r.part("cube", 0.1, 0.27, z * 1.9, 0.12, 0.08, 0.03, _dim(skin, 0.7))  # hollow cheeks
                r.part("sphere", -0.04, 0.38, 0, 0.42, 0.5, 0.42, under)  # the cowl
                r.part("cube", 0.05, 0.6, 0, 0.3, 0.06, 0.4, robe)  # its brim
                r.part("cyl", -0.02, 0.66, 0, 0.36, 0.08, 0.36, ENTHRONED_IRON)  # crown band
                for i in range(7):  # iron spikes, tallest at the front
                    a = (i - 3) * 0.42
                    h = 0.5 - abs(i - 3) * 0.07
                    r.part(
                        "cone", -0.02 + math.cos(a) * 0.16, 0.7 + h / 2, math.sin(a) * 0.16,
                        0.06, h, 0.06, ENTHRONED_IRON,
                    )  # fmt: skip
    for i in range(10):  # dust drifting through the light about the throne
        u = (t * 0.05 + i / 10) % 1.0
        r.part(
            "cube", 0.6 + math.sin(i * 2.3 + t * 0.2) * 0.8, 0.5 + 3.5 * u, math.sin(i * 1.7) * 1.0,
            0.03, 0.03, 0.03, (200, 196, 180), glow=True,
        )  # fmt: skip


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


BOSS_DOOR_WOOD = (92, 66, 46)
BOSS_DOOR_IRON = (54, 52, 58)
BOSS_DOOR_STONE = (104, 100, 96)


def boss_door(r, open_t, axis, t, lit=True):
    """The great double door before a boss's lair, spanning its tile: two iron-banded leaves studded
    in rows, with ring knockers, under a stone arch of wedge voussoirs and a keystone; an ember burns
    in a lamp on each jamb while the boss lives. The leaves swing apart (inward) as `open_t` runs to 1.
    Axis 'x' means it blocks movement along X."""
    swing = _ease(min(open_t, 1.0)) * 1.45
    with r.at(0, 0, 0, ry=0 if axis == "x" else math.pi / 2):
        # Jambs with an iron lamp on each face, the arch over them, and its keystone (on both faces).
        for side in (-1, 1):
            r.part("cube", 0, 1.45, side * 0.98, 0.42, 2.9, 0.16, BOSS_DOOR_STONE, tex="rough_stone")
            for face in (-1, 1):
                r.part("cube", face * 0.22, 1.45, side * 0.92, 0.04, 2.7, 0.04, _dim(BOSS_DOOR_STONE, 0.6))
                with r.at(face * 0.26, 2.05, side * 0.86):
                    r.part("cube", 0, 0, 0, 0.12, 0.16, 0.12, BOSS_DOOR_IRON)
                    if lit:
                        _flame(r, 0, 0.14, 0, 0.08, t + side + face)
        for i in range(5):  # voussoirs fanning across the head of the arch
            u = (i + 0.5) / 5 - 0.5
            r.part(
                "wedge", 0, 2.98 + 0.08 * math.cos(u * math.pi), u * 1.9, 0.44, 0.24, 0.34,
                BOSS_DOOR_STONE, tex="rough_stone", rx=-u * 0.9,
            )  # fmt: skip
        r.part("cube", 0, 3.08, 0, 0.5, 0.3, 0.22, _dim(BOSS_DOOR_STONE, 1.15), tex="rough_stone")  # key
        for face in (-1, 1):
            r.part("cube", face * 0.26, 3.08, 0, 0.02, 0.12, 0.08, (255, 140, 50) if lit else COLD_EMBER,
                   rx=math.pi / 4, glow=lit)  # fmt: skip
        # The leaves, hinged at the jambs, swinging away from +X; banded, studded and ringed both sides.
        for side in (-1, 1):
            with r.at(0, 0, side * 0.9, ry=side * swing), r.at(0, 0, -side * 0.45):
                r.part("cube", 0, 1.4, 0, 0.14, 2.8, 0.9, BOSS_DOOR_WOOD, tex="door_wood")
                for face in (-1, 1):
                    fx = face * 0.08
                    for y in (0.35, 1.15, 1.95, 2.6):  # iron bands
                        r.part("cube", fx, y, 0, 0.03, 0.12, 0.88, BOSS_DOOR_IRON)
                        for z in (-0.3, 0.0, 0.3):  # studs along each band
                            r.part("cube", fx * 1.25, y, z, 0.03, 0.05, 0.05, (150, 144, 140))
                    r.part("cube", fx, 1.4, side * 0.43, 0.03, 2.8, 0.06, BOSS_DOOR_IRON)  # the meeting edge
                    with r.at(fx * 1.5, 1.3, side * 0.3):  # a ring knocker on a diamond plate
                        r.part("cube", 0, 0, 0, 0.03, 0.16, 0.16, BOSS_DOOR_IRON, rx=math.pi / 4)
                        r.part(
                            "cyl", face * 0.03, -0.12, 0, 0.18, 0.03, 0.18, (170, 150, 100), rz=math.pi / 2
                        )


def fog_gate(r, t, axis, sealed=False):
    """A wall of fog where a boss's door once stood: drifting sheets of stippled grey mist layered
    through the doorway, motes swirling across them. Sealed (the fight is on), it thickens."""
    grey = (118, 122, 132) if not sealed else (140, 136, 128)
    with r.at(0, 0, 0, ry=0 if axis == "x" else math.pi / 2):
        for i in range(3 if not sealed else 4):
            dx = (i - 1) * 0.14 + math.sin(t * 0.9 + i * 1.7) * 0.05
            dy = math.sin(t * 0.6 + i * 2.3) * 0.15
            dz = math.sin(t * 0.45 + i * 1.1) * 0.25
            tex = "mist" if i == 1 else "cloud_cap"
            r.part("cube", dx, 1.55 + dy, dz, 0.02, 3.1, 2.0, _dim(grey, 1 - 0.1 * i), tex=tex, glow=True)
        for i in range(9):  # motes drifting up through the mist
            u = (t * 0.25 + i / 9) % 1.0
            z = math.sin(i * 2.7 + t * 0.7) * 0.85
            r.part("cube", math.sin(i * 1.9 + t) * 0.18, 0.1 + 3.0 * u, z, 0.05, 0.05, 0.05, (190, 192, 200),
                   rx=t + i, glow=True)  # fmt: skip


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
    """A plain lever: a shaft pivoting on a block, thrown from up-and-back to down-and-forward as
    `k` (0..1) runs. Mounted on a wall at local -X, or free-standing."""
    with r.at(0, 0, 0, s=1.2):
        if wood:
            _wood_lever(r, k, wall)
        else:
            _lever(r, k, wall)


def _wood_lever(r, k, wall):
    """The jungle's lever: a rough beam on a peg through a stump post, its grip wound with vine."""
    bx = -0.5 if wall else -0.15
    r.part("cyl", bx, 0.45, 0, 0.5, 0.9, 0.5, BARK, tex="bark")  # the stump post
    px, py = bx + 0.3, 0.75
    r.part("cyl", px, py, 0, 0.12, 0.4, 0.12, (124, 92, 58), rx=math.pi / 2)  # the axle peg
    with r.at(px, py, 0, rz=0.95 - 1.9 * k):
        r.part("cube", 0, 0.45, 0, 0.14, 0.95, 0.12, (126, 92, 58), tex="bark")
        r.part("cube", 0, 0.75, 0, 0.17, 0.22, 0.15, (70, 110, 46))  # vine-wound grip


def _lever(r, k, wall):
    """The keep's lever: an iron shaft with a ball grip, pivoting in a slotted plate on a stone block."""
    bx = -0.5 if wall else -0.15
    r.part("cube", bx, 0.4, 0, 0.55, 0.8, 0.7, WHITE, tex="rough_stone")
    r.part("cube", bx, 0.83, 0, 0.62, 0.06, 0.76, (110, 106, 100))  # capstone
    px, py = bx + 0.3, 0.95
    for z in (-0.1, 0.1):  # the slotted plate the shaft swings in
        r.part("cube", px - 0.02, py - 0.02, z, 0.3, 0.3, 0.04, DARK_IRON)
    r.part("cyl", px, py, 0, 0.1, 0.3, 0.1, IRON, rx=math.pi / 2)  # the axle
    with r.at(px, py, 0, rz=0.95 - 1.9 * k):
        r.part("cube", 0, 0.42, 0, 0.08, 0.85, 0.08, IRON)
        r.part("sphere", 0, 0.88, 0, 0.18, 0.18, 0.18, DARK_IRON)  # the ball grip


def lift(r, t, moving, chain_h, model="", doors=()):
    """A chain lift. `model="cage"` is the keep's jail cage: an iron-barred box hung from a single
    heavy chain, open only on the `doors` sides (dx, dz) that face a landing. Otherwise an oak deck
    in an iron frame, hung from four chains. Both run up to a pulley beam under the shaft's ceiling;
    riding, the chains shiver."""
    shiver = math.sin(t * 30) * 0.01 if moving else 0.0
    if model == "cage":
        _cage_lift(r, chain_h, shiver, doors)
        return
    r.part("cube", 0, -0.08, 0, 1.92, 0.14, 1.92, WHITE, tex="wood_plank")
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # the iron frame
        r.part("cube", sx * 0.94, -0.05, sz * 0.94, 0.1 if sx else 1.98, 0.18, 0.1 if sz else 1.98, DARK_IRON)
    for z in (-0.5, 0.0, 0.5):  # the cross straps
        r.part("cube", 0, 0.005, z, 1.86, 0.02, 0.08, IRON)
    links = _links(chain_h - 0.2)
    for cx, cz in ((0.85, 0.85), (0.85, -0.85), (-0.85, 0.85), (-0.85, -0.85)):
        r.part("cube", cx, 0.1, cz, 0.14, 0.2, 0.14, DARK_IRON)  # the shackle
        _chain(r, cx + shiver, 0.2, cz, links, 0.04)
    _pulley(r, chain_h)


LINK = 0.45  # length of one lift chain link
CAGE_H = 2.5  # height of the jail cage's roof above its floor
CAGE_BARS = 5  # bars along each closed side


def _links(span):
    return min(max(int(span / LINK), 1), 40)


def _chain(r, x, y, z, links, thick):
    for i in range(links):
        r.part("cube", x, y + (i + 0.5) * LINK, z, thick, LINK, thick * 2.5, IRON, ry=0 if i % 2 else 1.57)


def _pulley(r, chain_h):
    r.part("cube", 0, chain_h, 0, 1.9, 0.25, 0.3, OAK)  # the pulley beam
    for cx in (-0.85, 0.85):
        r.part("cyl", cx, chain_h - 0.2, 0, 0.35, 0.12, 0.35, DARK_IRON, rx=math.pi / 2)


def _cage_lift(r, chain_h, shiver, doors):
    h = max(min(CAGE_H, chain_h - 0.6), 1.9)
    r.part("cube", 0, -0.08, 0, 1.92, 0.14, 1.92, (110, 100, 92), tex="wood_plank")  # a scorched floor
    for i in range(-2, 3):  # an iron grating over it
        r.part("cube", i * 0.4, 0.005, 0, 0.06, 0.03, 1.9, DARK_IRON)
    for cx, cz in ((0.9, 0.9), (0.9, -0.9), (-0.9, 0.9), (-0.9, -0.9)):  # corner posts
        r.part("cube", cx, h / 2, cz, 0.12, h, 0.12, DARK_IRON)
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        door = (dx, dz) in doors
        for y in (0.06, h) if door else (0.06, h * 0.5, h):  # rails; a doorway keeps its sill and lintel
            r.part("cube", dx * 0.9, y, dz * 0.9, 0.08 if dx else 1.86, 0.08, 0.08 if dz else 1.86, DARK_IRON)
        if door:
            continue
        for i in range(CAGE_BARS):  # the bars
            u = -0.9 + (i + 1) * 1.8 / (CAGE_BARS + 1)
            r.part("cube", dx * 0.9 or u, h / 2, dz * 0.9 or u, 0.05, h, 0.05, IRON)
    for u in (-0.3, 0.3):  # a barred roof
        r.part("cube", u, h, 0, 0.06, 0.06, 1.86, IRON)
        r.part("cube", 0, h, u, 1.86, 0.06, 0.06, IRON)
    r.part("cyl", 0, h + 0.08, 0, 0.4, 0.1, 0.4, DARK_IRON)  # the ring the chain is shackled to
    _chain(r, shiver, h + 0.1, 0, _links(chain_h - h - 0.3), 0.07)
    _pulley(r, chain_h)


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


FIRE_CORE = (255, 246, 210)  # the white-hot heart of every fireball
FIRE_TIP = (255, 214, 110)  # the pale ends of its licking tongues
FIRE_TONGUES = 5


def fiery(rgb):
    """Whether a shot of colour `rgb` is fire (drawn as a fireball): red-hot, little blue."""
    r_, g, b = rgb
    return r_ >= 200 and g <= 210 and b <= 120


def fireball(r, rgb, t, size=1.0, trail=None, seed=0.0):
    """A ball of fire `size` times a bolt's (0.3 m shell): a white-hot core in a flickering shell of
    `rgb`, tongues licking out and up as it turns, and with `trail` (the unit direction it came from)
    a wake of embers that shrink and redden behind it."""
    s = size
    flick = 1 + math.sin(t * 23 + seed) * 0.08
    r.part("sphere", 0, 0, 0, 0.16 * s, 0.16 * s, 0.16 * s, FIRE_CORE, glow=True)
    r.part("sphere", 0, 0, 0, 0.3 * s * flick, 0.3 * s * flick, 0.3 * s * flick, rgb, glow=True)
    r.part("sphere", 0, 0.03 * s, 0, 0.4 * s, 0.34 * s * flick, 0.4 * s, _dim(rgb, 0.8), glow=True)
    for i in range(FIRE_TONGUES):
        a = t * 5 + seed + i * 2 * math.pi / FIRE_TONGUES
        lick = (0.22 + 0.1 * math.sin(t * 13 + i * 2.3 + seed)) * s
        with r.at(0, 0, 0, ry=a, rz=0.8 + 0.3 * math.sin(t * 9 + i * 1.7)):
            r.part("cone", 0, 0.14 * s + lick / 2, 0, 0.13 * s, lick, 0.13 * s, FIRE_TIP, glow=True)
    r.part("cone", 0, 0.22 * s, 0, 0.22 * s, 0.36 * s * flick, 0.22 * s, FIRE_TIP, glow=True)  # it rises
    if trail is None:
        return
    tx, ty, tz = trail
    for i in range(1, 5):
        d = (0.16 + 0.15 * i) * s
        e = (0.15 - 0.028 * i) * s
        wob = math.sin(t * 17 + i * 2.1 + seed) * 0.04 * s
        rgb_i = (255, max(rround(rgb[1] * (1 - 0.18 * i)), 30), max(rround(rgb[2] * (1 - 0.25 * i)), 10))
        r.part(
            "cube", tx * d + wob, ty * d + 0.03 * i * s, tz * d - wob, e, e, e, rgb_i,
            rx=t * 7 + i, ry=t * 5 + i * 1.3, glow=True,
        )  # fmt: skip


def flare(r, rgb, k, t=0.0):
    """A tongue of Pyre's fire: a ragged fireball that swells, then gutters as `k` runs to 0."""
    size = 0.15 + 0.35 * math.sin(min(k, 1.0) * math.pi) ** 0.5
    fireball(r, rgb, t, size / 0.3, seed=k * 9)


def bolt(r, rgb, t=0.0, trail=None):
    """A spell bolt or a foe's shot: fire burns as a fireball, anything else is a bright glob."""
    if fiery(rgb):
        fireball(r, rgb, t, trail=trail)
        return
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
    """A burning flame: an orange body, two side tongues leaning in the draught, and a white-hot core."""
    seed = x * 7 + z * 5
    flicker = 1 + math.sin(t * 11 + seed) * 0.15
    r.part("cone", x, y, z, size * flicker, size * 1.5 * flicker, size * flicker, FLAME, glow=True)
    for i, side in enumerate((-1, 1)):
        lean = side * (0.35 + 0.15 * math.sin(t * 9 + seed + i * 2.4))
        lick = 1 + math.sin(t * 14 + seed + i * 1.3) * 0.2
        with r.at(x + side * size * 0.15, y - size * 0.1, z, rz=lean):
            r.part("cone", 0, size * 0.4, 0, size * 0.45, size * 1.1 * lick, size * 0.45, FLAME, glow=True)
    r.part("cone", x, y + 0.02, z, size * 0.5, size * 1.9 * flicker, size * 0.5, FLAME_CORE, glow=True)
    r.part("sphere", x, y - size * 0.3, z, size * 0.45, size * 0.35, size * 0.45, FIRE_CORE, glow=True)


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


FIRE_SPELLS = ("flame", "pyre")
SPELL_ORB = {
    "flame": (255, 120, 40),
    "mend": (120, 230, 140),
    "lumen": (210, 220, 255),
    "venom": (120, 210, 60),
    "veil": (200, 210, 215),
    "pyre": (255, 90, 30),
    "thunder": (200, 225, 255),
    "motes": (190, 120, 255),
}


def spell_orb(r, id_, t):
    """Inventory preview for a known spell: a glowing orb in the spell's colour (fire spells burn as a
    fireball)."""
    rgb = SPELL_ORB.get(id_, WHITE)
    if id_ in FIRE_SPELLS:
        fireball(r, rgb, t, 2.0)
        return
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
# right (+) or left (-), ry swings it across the view (+ toward the right, - toward the left). Each
# attack motion is three key poses (offsets from rest, (dx, dy, dz, rx, ry, rz)):
#   wind  - drawn back, reached a little before the blow lands,
#   strike - where the blow lands (at the attack's hit_at),
#   follow - carried through past the target (overshooting a touch, then settling),
# then it eases back to rest. The wind -> strike leg accelerates, so swings snap rather than float.

REST = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
MOTIONS = {
    # Light cuts: high right, down across to the low left.
    "slash": (
        (-0.05, 0.18, 0.2, 0.45, 0.3, 0.3),
        (0.14, 0.0, -0.12, -0.6, -0.35, -1.2),
        (0.06, -0.08, -0.3, -1.2, -0.55, -1.0),
    ),
    # A flat arc from right to left, the whole arm turning with it.
    "sweep": (
        (0.0, 0.03, 0.32, 1.0, 0.6, -0.4),
        (0.06, 0.05, -0.12, -0.6, -0.4, -1.0),
        (0.0, 0.0, -0.5, -1.5, -0.9, -0.6),
    ),
    # Overhead: raised high over the shoulder, then straight down through the target.
    "chop": (
        (-0.1, 0.2, -0.02, 0.0, 0.1, 0.85),
        (0.16, -0.02, -0.1, 0.0, -0.05, -1.25),
        (0.12, -0.12, -0.1, 0.0, -0.1, -1.55),
    ),
    "slam": (
        (-0.1, 0.24, -0.05, 0.0, 0.1, 1.0),
        (0.15, -0.2, -0.12, 0.0, 0.0, -1.4),
        (0.15, -0.32, -0.12, 0.0, 0.0, -1.65),
    ),
    "thrust": (
        (-0.25, 0.08, -0.2, 0.0, -0.25, -1.15),
        (0.48, 0.08, -0.25, 0.0, -0.35, -1.15),
        (0.4, 0.06, -0.25, 0.0, -0.3, -1.1),
    ),
    "stab": (
        (-0.1, 0.04, -0.1, 0.0, -0.2, -0.9),
        (0.3, 0.05, -0.15, 0.0, -0.3, -1.1),
        (0.22, 0.04, -0.15, 0.0, -0.25, -1.0),
    ),
    "lash": (
        (-0.05, 0.15, 0.05, 0.4, 0.2, 0.6),
        (0.05, 0.05, -0.15, -0.4, -0.3, -1.6),
        (0.0, -0.05, -0.2, -0.8, -0.5, -1.3),
    ),
    "flick": (
        (0.0, -0.05, -0.25, -0.9, -0.4, -0.6),
        (0.1, 0.1, 0.05, 0.6, 0.2, -0.9),
        (0.05, 0.15, 0.2, 1.1, 0.45, -0.4),
    ),
    "bash": (
        (-0.1, 0.1, 0.05, 0.3, 0.1, 0.4),
        (0.25, 0.0, -0.1, -0.2, -0.1, -0.9),
        (0.2, -0.05, -0.12, -0.3, -0.2, -1.1),
    ),
    "hew": (
        (-0.08, 0.16, 0.15, 0.6, 0.3, 0.7),
        (0.15, -0.05, -0.15, -0.4, -0.3, -1.3),
        (0.1, -0.15, -0.3, -0.7, -0.6, -1.5),
    ),
    "draw": (
        (-0.05, 0.0, -0.15, -0.25, -0.5, -1.0),
        (0.15, 0.05, 0.25, 0.9, 0.3, -1.0),
        (0.05, 0.12, 0.4, 1.4, 0.7, -0.6),
    ),
    "snare": (
        (-0.1, 0.25, 0.1, 0.6, 0.2, 0.9),
        (0.1, 0.0, -0.1, -0.3, -0.2, -1.7),
        (-0.15, -0.05, 0.0, -0.2, 0.0, -0.6),
    ),
    "leap": (
        (-0.05, 0.25, 0.0, 0.0, 0.0, 1.0),
        (0.25, -0.25, -0.1, 0.0, 0.0, -1.5),
        (0.2, -0.3, -0.1, 0.0, 0.0, -1.6),
    ),
    # Double-click quick attacks.
    "twin": (  # an X: down to the left, then straight back up to the right
        (-0.05, 0.18, 0.2, 0.45, 0.3, 0.3),
        (0.14, 0.0, -0.12, -0.6, -0.35, -1.2),
        (0.12, 0.1, 0.22, 0.9, 0.4, -1.1),
    ),
    "pommel": (  # the blade tipped back, the hilt punched into the face in front
        (-0.15, 0.06, -0.05, 0.0, 0.2, 0.6),
        (0.28, 0.06, -0.12, 0.0, 0.1, 0.9),
        (0.22, 0.04, -0.1, 0.0, 0.1, 0.8),
    ),
    "doublelash": (  # cracked down, then snapped back up
        (-0.05, 0.15, 0.05, 0.4, 0.2, 0.6),
        (0.05, 0.05, -0.15, -0.4, -0.3, -1.6),
        (0.05, 0.12, 0.12, 0.3, 0.3, -1.4),
    ),
    "rap": (  # a short, straight punch with the head
        (-0.12, 0.08, -0.05, 0.0, 0.05, 0.3),
        (0.3, 0.02, -0.1, 0.0, -0.05, -0.6),
        (0.22, 0.0, -0.1, 0.0, -0.05, -0.7),
    ),
    "hook_cut": (  # reached out left, then hooked back in toward you
        (0.05, 0.1, -0.25, -0.6, -0.5, 0.4),
        (0.2, 0.0, 0.1, 0.5, 0.2, -1.1),
        (0.0, -0.05, 0.22, 0.8, 0.45, -0.8),
    ),
    "drive": (  # the haft rammed forward, held level
        (-0.15, 0.0, -0.05, 0.0, -0.1, -0.5),
        (0.32, 0.0, -0.1, 0.0, -0.2, -0.7),
        (0.25, -0.02, -0.1, 0.0, -0.15, -0.7),
    ),
}


def _lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


def _ease_out_back(k, overshoot=1.2):
    """Eases out past 1 and settles back: a blade carried through its target that stops itself."""
    k = min(max(k, 0.0), 1.0) - 1
    return 1 + (overshoot + 1) * k**3 + overshoot * k**2


def _motion(motion, p, hit_at=0.4):
    """Pose offsets (dx, dy, dz, rx, ry, rz) for one attack motion at phase p (0..1), landing at hit_at."""
    wind, strike, follow = MOTIONS.get(motion, MOTIONS["slash"])
    wind_at = hit_at * 0.7
    follow_at = hit_at + (1 - hit_at) * 0.35
    if p < wind_at:
        return _lerp(REST, wind, _ease(p / wind_at))
    if p < hit_at:
        return _lerp(wind, strike, _ease_in((p - wind_at) / (hit_at - wind_at)))
    if p < follow_at:
        return _lerp(strike, follow, _ease_out_back((p - hit_at) / (follow_at - hit_at)))
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
    y -= bob * 0.6 * charge  # winding up a heavy steadies the bob
    if swinging:
        a = player.attack
        dx, dy, dz, drx, dry, drz = _motion(a.motion, player.swing_phase, a.hit_at)
        x, y, z, rx, ry, rz = x + dx, y + dy, z + dz, rx + drx, ry + dry, rz + drz
        if player.hitstop_t > 0:  # the blade bites and the arm jars back
            x -= 0.03
            y += math.sin(player.hitstop_t * 300) * 0.008
    elif charge > 0:  # drawing back for a heavy: raise it, with a tremble once it is ready
        k = _ease(charge)
        shake = math.sin(player.charge_t * 60) * 0.006 if charge >= 1 else 0.0
        x, y, z = x - 0.05 * k, y + 0.14 * k + shake, z - 0.04 * k
        rx, rz = rx + 0.4 * k, rz + 0.3 * k
        if item.category == "katana":  # held on: settle low into the draw stance
            d = _ease((player.charge_t - 0.35) / (1.2 - 0.35))
            wx, wy, wz, wrx, wry, wrz = MOTIONS["draw"][0]
            x, y, z = x + (wx + 0.05) * d, y + (wy - 0.14) * d, z + (wz + 0.04) * d
            rx, ry, rz = rx + (wrx - 0.4) * d, ry + wry * d, rz + (wrz - 0.3) * d
    else:  # sprinting: carried low, blade forward
        y -= 0.08 * sprint
        rz -= 0.35 * sprint
    pose = (x, y, z, rx, ry, rz)
    hand_rgb, shade = arm(r, _weapon_point(pose, side, _grips(item)[0]), side, armor["body"], armor["gloves"])
    if both:
        lp = _weapon_point(pose, side, _grips(item)[1])
        lhand, lshade = arm(r, lp, -1, armor["body"], armor["gloves"])
    phase = player.swing_phase if swinging else None
    if swinging and item.category in TRAILS:
        _swing_trail(
            r, item, player.attack, phase, (x - dx, y - dy, z - dz, rx - drx, ry - dry, rz - drz), side
        )
    with _pose_at(r, pose, side):
        weapon(r, item.id, phase)
        with r.at(0, _grips(item)[0], 0):
            fist(r, hand_rgb, shade, armor["gloves"])
        if both:
            with r.at(0, _grips(item)[1], 0):
                fist(r, lhand, lshade, armor["gloves"])


TRAILS = {"sword", "greatsword", "katana", "axe"}  # edged weapons leave a smear through the blow
TRAIL_LAG = 0.08  # how far back (in swing phase) the smear reaches
TRAIL_GHOSTS = 6


def _swing_trail(r, item, a, phase, rest, side):
    """A fading smear behind an edged weapon as it cuts: a fan of ghost blades between where it is and
    where it was a moment ago, dimmer the further back. Only around the blow, and drawn first so the
    weapon covers them."""
    wind_at, follow_at = a.hit_at * 0.8, a.hit_at + (1 - a.hit_at) * 0.15
    if not wind_at < phase < follow_at:
        return
    length = WEAPON_LEN.get(item.id, 1.0) * 0.85
    rgb = (255, 170, 90) if item.element == "fire" else (210, 225, 255) if item.element else (205, 205, 215)
    now = _motion(a.motion, phase, a.hit_at)
    then = _motion(a.motion, max(phase - TRAIL_LAG, wind_at), a.hit_at)
    for i in range(TRAIL_GHOSTS, 0, -1):  # the oldest (dimmest) first
        k = i / TRAIL_GHOSTS
        off = _lerp(now, then, k)
        pose = tuple(b + o for b, o in zip(rest, off, strict=True))
        with _pose_at(r, pose, side):
            r.part("blade", 0, 0.2 + length / 2, 0, 0.004, length * 0.9, 0.16, _dim(rgb, 0.62 - 0.4 * k))


def fist_view(r, player, hand, bob, armor):
    """A bare hand: a jab straight forward, a hook from the outside, or the double-click's one-two."""
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
        elif motion == "onetwo":  # two snapping jabs in one swing
            jab = 0.32 * abs(math.sin(phase * 2 * math.pi)) ** 0.7
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
        glow = SPELL_GLOW.get(spell.id, (220, 220, 220)) if spell else None
        if spell and spell.id in FIRE_SPELLS:
            # A small fire licks over the palm; it gutters to an ember while the gauge refills.
            ready = player.magic_gauge.full
            with r.at(0.02, 0.16, 0):
                fireball(r, glow, t, 0.26 if ready else 0.08 + 0.1 * player.magic_gauge.value)
        elif spell and player.magic_gauge.full:
            pulse = 1 + math.sin(t * 5) * 0.12
            r.part("sphere", 0.02, 0.1, 0, 0.09 * pulse, 0.09 * pulse, 0.09 * pulse, glow, glow=True)


SPELL_GLOW = {
    "flame": EMBER,
    "mend": (130, 230, 130),
    "lumen": (235, 235, 180),
    "venom": (130, 220, 70),
    "veil": (205, 215, 220),
    "pyre": (255, 110, 40),
    "thunder": (190, 220, 255),
    "motes": (190, 120, 255),
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
    "butcher_cleaver": 1.0,
    "oak_cudgel": 1.0,
    "spiked_club": 1.05,
    "stormbrand": 1.2,
    "slagbreaker": 1.5,
}


def weapon(r, item_id, phase=None):
    """A weapon model with the grip at the origin, pointing up +Y."""
    if item_id in ("katana", "moonless_tachi", "nodachi"):
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
    elif item_id == "butcher_cleaver":
        cleaver(r)
    elif item_id == "stormbrand":
        forge_models.stormbrand(r)
    elif item_id == "slagbreaker":
        forge_models.slagbreaker(r)
    else:
        sword(r, item_id)


def _bright(rgb, k=1.25, add=20):
    return tuple(min(rround(c * k + add), 255) for c in rgb)


def blade_parts(
    r,
    length,
    width,
    steel,
    *,
    thick=0.032,
    base=0.13,
    edge=None,
    fuller=None,
    guard="straight",
    guard_w=0.32,
    guard_rgb=BRASS,
    grip=0.22,
    grip_rgb=LEATHER,
    wrap=None,
    pommel="disc",
    pommel_rgb=BRASS,
    ricasso=0.0,
    ricasso_rgb=LEATHER,
    glow=False,
):
    """A straight sword with its grip at the origin and its blade up +Y (the blade's flat faces +-X):
    pommel, grip (with `wrap` bands), a crossguard in one of a few `guard` styles, an optional
    leather-wrapped `ricasso`, then a lozenge-section blade that narrows to a point, a fuller down
    both faces and bright bevelled edges. Shared by the player's swords and the foes' (`sword_parts`).

    guard: "straight", "droop" (quillons bent toward the hand), "quatrefoil" (drooping, with
    trefoil knobs), "flared" (bent up toward the blade) or "hooks" (flared, with parrying hooks above
    the ricasso). pommel: "disc", "wheel" or "stopper"."""
    edge = edge or _bright(steel)
    fuller = fuller or _dim(steel, 0.62)
    # Grip and pommel.
    r.part("cube", 0, 0.1 - grip / 2, 0, 0.055, grip, 0.055, grip_rgb)
    if wrap:
        for i in range(max(int(grip / 0.065), 1)):
            r.part("cube", 0, 0.1 - grip + 0.035 + i * 0.065, 0, 0.062, 0.02, 0.062, wrap)
    py = 0.1 - grip - 0.035
    if pommel == "wheel":
        r.part("cyl", 0, py - 0.01, 0, 0.12, 0.045, 0.12, pommel_rgb, rz=math.pi / 2)
        r.part("cyl", 0, py - 0.01, 0, 0.05, 0.055, 0.05, _bright(pommel_rgb), rz=math.pi / 2)
    elif pommel == "stopper":
        r.part("sphere", 0, py, 0, 0.085, 0.08, 0.085, pommel_rgb)
        r.part("cone", 0, py - 0.065, 0, 0.06, 0.06, 0.06, pommel_rgb, rz=math.pi)
    else:
        r.part("sphere", 0, py, 0, 0.09, 0.075, 0.08, pommel_rgb)
    # Crossguard: a block and two quillons.
    gy = 0.115
    r.part("cube", 0, gy, 0, 0.07, 0.055, 0.09, guard_rgb)
    half = guard_w / 2
    bend = {"droop": 0.35, "quatrefoil": 0.3, "flared": -0.28, "hooks": -0.2}.get(guard, 0.0)
    for side in (1, -1):
        with r.at(0, gy, side * 0.04, rx=side * bend):
            r.part("lozenge", 0, 0, side * half / 2, 0.05, half, 0.045, guard_rgb, rx=math.pi / 2)
            if guard == "quatrefoil":
                r.part("sphere", 0, 0, side * (half + 0.02), 0.07, 0.07, 0.06, guard_rgb)
            else:
                r.part(
                    "wedge", 0, 0, side * (half + 0.02), 0.05, 0.05, 0.045, guard_rgb, rx=side * math.pi / 2
                )
    if ricasso:  # the unsharpened base of a big blade, wrapped so a second hand can choke up on it
        r.part("cube", 0, base + ricasso / 2, 0, thick * 1.7, ricasso, width * 0.9, ricasso_rgb)
        if guard == "hooks":  # parrying hooks at the top of the ricasso
            for side in (1, -1):
                r.part(
                    "wedge",
                    0,
                    base + ricasso,
                    side * width * 0.75,
                    0.04,
                    0.14,
                    0.05,
                    guard_rgb,
                    rx=side * 1.0,
                )
    # The blade.
    r.part("blade", 0, base + length / 2, 0, thick, length, width, steel, glow=glow)
    body = length * (1 - shapes.SHOULDER)
    lean = math.atan2(width * 0.09, body)
    for side in (1, -1):  # bevelled edges, bright on both faces, up to where the point begins
        r.part(
            "cube",
            0,
            base + ricasso + (body - ricasso) / 2,
            side * width * 0.4,
            thick * 0.32,
            body - ricasso - 0.02,
            width * 0.08,
            edge,
            rx=-side * lean,
            glow=glow,
        )
    fl = (body - ricasso) * 0.72
    r.part("cube", 0, base + ricasso + 0.03 + fl / 2, 0, thick * 1.12, fl, width * 0.2, fuller, glow=glow)


# The player's straight swords: blade_parts arguments per item.
SWORDS = {
    "rusted_sword": {
        "length": 0.88,
        "width": 0.13,
        "steel": (142, 136, 126),
        "edge": (180, 176, 166),
        "fuller": (92, 84, 74),
        "guard_rgb": (96, 80, 62),
        "guard_w": 0.3,
        "grip_rgb": (74, 56, 40),
        "wrap": (112, 94, 68),
        "pommel_rgb": (96, 80, 62),
    },
    "ashblade": {
        "length": 0.95,
        "width": 0.125,
        "steel": (190, 190, 202),
        "edge": (238, 238, 245),
        "fuller": (66, 62, 66),
        "guard": "flared",
        "guard_rgb": (70, 66, 72),
        "grip_rgb": (40, 36, 40),
        "wrap": (120, 110, 100),
        "pommel": "stopper",
        "pommel_rgb": (70, 66, 72),
    },
    "bastard_sword": {
        "length": 1.12,
        "width": 0.12,
        "steel": (176, 178, 190),
        "guard": "droop",
        "guard_w": 0.4,
        "guard_rgb": (112, 108, 102),
        "grip": 0.32,
        "wrap": (40, 30, 22),
        "pommel": "wheel",
        "pommel_rgb": (112, 108, 102),
    },
    "claymore": {
        "length": 1.38,
        "width": 0.15,
        "thick": 0.04,
        "steel": (170, 172, 182),
        "guard": "quatrefoil",
        "guard_w": 0.52,
        "guard_rgb": (120, 110, 90),
        "grip": 0.4,
        "wrap": (40, 30, 22),
        "pommel": "wheel",
        "pommel_rgb": (120, 110, 90),
        "ricasso": 0.12,
    },
    "zweihander": {
        "length": 1.62,
        "width": 0.17,
        "thick": 0.042,
        "base": 0.12,
        "steel": (185, 186, 196),
        "guard": "hooks",
        "guard_w": 0.6,
        "guard_rgb": (120, 110, 90),
        "grip": 0.42,
        "grip_rgb": (30, 26, 24),
        "wrap": (150, 40, 36),
        "pommel": "stopper",
        "pommel_rgb": (120, 110, 90),
        "ricasso": 0.26,
    },
}
SWORD_RUST = (118, 92, 72)


def sword(r, item_id):
    """A straight sword: rusted, the Ashblade, the bastard sword or a greatsword (see SWORDS)."""
    spec = SWORDS.get(item_id, SWORDS["rusted_sword"])
    blade_parts(r, **spec)
    w, base = spec["width"], spec.get("base", 0.13)
    if item_id == "rusted_sword":  # one faint stain of rust creeping up from the guard
        r.part("cube", 0, base + 0.1, 0, 0.034, 0.06, w * 0.35, SWORD_RUST)
    elif item_id == "ashblade":  # an ember that never quite went out, near the point
        r.part("cube", 0, base + spec["length"] * 0.8, 0, 0.036, 0.05, 0.02, EMBER, glow=True)


# blade, edge (hamon), grip wrap, cord, segments, grip length
KATANAS = {
    "katana": ((205, 208, 218), (245, 245, 250), (40, 30, 40), (160, 30, 40), 3, 0.3),
    "moonless_tachi": ((70, 72, 90), (200, 205, 220), (20, 18, 24), (60, 60, 80), 4, 0.32),
    "nodachi": ((200, 202, 212), (245, 245, 250), (30, 26, 30), (200, 170, 70), 5, 0.5),
}


def katana(r, item_id="katana"):
    blade, edge, wrap, cord, segments, grip = KATANAS[item_id]
    r.part("cube", 0, 0.07 - grip / 2, 0, 0.055, grip, 0.06, wrap)
    for i in range(round(grip / 0.075)):  # cord wrap, crossing diamonds down the hilt
        r.part("cube", 0, 0.05 - grip + 0.04 + i * 0.075, 0, 0.062, 0.02, 0.066, cord, rx=0.3 * (-1) ** i)
    r.part("cube", 0, 0.06 - grip, 0, 0.065, 0.03, 0.07, (170, 150, 70))  # kashira cap
    r.part("cyl", 0, 0.08, 0, 0.16, 0.025, 0.16, (60, 50, 30))  # tsuba
    r.part("cube", 0, 0.115, 0, 0.04, 0.045, 0.075, (170, 150, 70))  # habaki collar
    with r.at(0, 0.135, 0):
        _katana_segment(r, segments, blade, edge)


def _katana_segment(r, left, blade=(205, 208, 218), edge=(245, 245, 250)):
    """A gentle curve: each segment hangs off the last, bent a little further back; the edge (-Z) carries
    a pale temper line (the hamon) and the last segment closes in a angled point (the kissaki)."""
    if left == 0:
        r.part("blade", 0, 0.06, -0.004, 0.024, 0.13, 0.066, blade, rx=0.12)
        r.part("cube", 0.0, 0.03, -0.022, 0.012, 0.07, 0.014, edge, rx=0.2)
        return
    with r.at(0, 0, 0, rx=0.05):
        r.part("lozenge", 0, 0.17, 0, 0.026, 0.36, 0.07, blade)
        r.part("cube", 0, 0.17, -0.024, 0.012, 0.36, 0.014, edge)
        r.part("cube", 0, 0.17, 0.03, 0.03, 0.36, 0.01, _dim(blade, 0.6))  # the thick back (mune)
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
    r.part("wedge", 0, 1.02, 0.31, 0.07, 0.1, 0.42, (175, 175, 180), rx=math.pi / 2)  # bit, the cutting edge
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
        r.part("wedge", 0, top - 0.08, 0.27, 0.045, 0.05, 0.36, (215, 215, 222), rx=math.pi / 2)  # edge
        r.part("cube", 0, top - 0.24, 0.16, 0.04, 0.06, 0.06, (150, 150, 156))  # its hooked tip
    else:
        r.part("cube", 0, top, 0.17, 0.04, 0.2, 0.08, (150, 150, 156))
        r.part("wedge", 0, top, 0.22, 0.045, 0.05, 0.22, (215, 215, 222), rx=math.pi / 2)
    r.part("cube", 0, top + 0.08, 0, 0.065, 0.03, 0.065, LEATHER)


def cleaver(r):
    """The Butcher's cleaver: a wrapped oak handle and a broad, square blade, its spine along the
    top and a hole for the hook it hung from."""
    r.part("cube", 0, 0.0, 0, 0.06, 0.42, 0.06, LEATHER)
    r.part("cube", 0, -0.23, 0, 0.075, 0.05, 0.075, DARK_IRON)  # butt cap
    r.part("cube", 0, 0.5, 0.13, 0.035, 0.6, 0.3, (140, 136, 130))  # the blade
    r.part("wedge", 0, 0.5, 0.29, 0.035, 0.04, 0.6, (205, 202, 196), rx=math.pi / 2)  # its edge
    r.part("cube", 0, 0.5, -0.015, 0.05, 0.62, 0.04, (90, 88, 86))  # the spine
    r.part("cube", 0.02, 0.72, 0.1, 0.01, 0.06, 0.06, (24, 20, 18))  # hanging hole
    r.part("cube", 0.02, 0.35, 0.2, 0.01, 0.12, 0.08, (90, 30, 26))  # a stain


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


PREVIEW_TILT = 0.3  # weapons lean toward the camera a little in previews
PREVIEW_HEIGHT = 1.75  # how tall a weapon stands in its preview, in the camera's view
PREVIEW_WIDTH = 1.4  # how wide it may spin, so a broad axe or a coiled lash still fits
WHIP_PREVIEW = 0.3  # a whip's swing phase in previews: lash drawn out in a lazy curve
PREVIEW_ZOOM = 2.0  # the most a small weapon (a hatchet) is blown up
_frames = {}


def _preview_weapon(r, id_):
    with r.at(rx=PREVIEW_TILT):
        weapon(r, id_, WHIP_PREVIEW if id_ in ("leather_whip", "thornlash") else None)


def preview_frame(id_):
    """(scale, centre) that fits weapon `id_` in its preview: scaled to stand PREVIEW_HEIGHT tall (or
    to spin within PREVIEW_WIDTH) with the middle of its box on the origin. Measured once."""
    if id_ not in _frames:
        lo, hi = bounds.measure(lambda r: _preview_weapon(r, id_))
        centre = tuple((a + b) / 2 for a, b in zip(lo, hi, strict=True))
        reach = max(math.hypot(hi[0] - lo[0], hi[2] - lo[2]), 1e-3)
        fit = min(PREVIEW_HEIGHT / max(hi[1] - lo[1], 1e-3), PREVIEW_WIDTH / reach, PREVIEW_ZOOM)
        _frames[id_] = (fit, centre)
    return _frames[id_]


def item(r, id_, t):
    """Inventory preview models, roughly 1 unit tall and centered on the origin."""
    if Items.ALL.get(id_) and Items.get(id_).kind == "weapon":
        s, (cx, cy, cz) = preview_frame(id_)
        with r.at(-cx * s, -cy * s, -cz * s, s=s):
            _preview_weapon(r, id_)
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


def headsman_block(r, seed):
    """An executioner's block: a squat, stained oak stump with a neck notch, a broad axe bitten into
    its top, and a bucket at its foot."""
    stain = (70, 22, 18)
    r.part("cyl", 0, 0.32, 0, 1.0, 0.64, 1.0, (110, 78, 50), tex="bark")
    r.part("cyl", 0, 0.645, 0, 0.92, 0.02, 0.92, (128, 96, 62))  # the hewn top
    r.part("cube", 0, 0.66, 0, 0.94, 0.04, 0.22, stain)  # the notch, dark with old blood
    r.part("cube", 0.25, 0.005, 0.4, 0.9, 0.01, 0.6, stain)  # a stain spreading on the floor
    with r.at(-0.15, 0.66, -0.25, ry=0.4 + (seed % 3) * 0.2, rz=-0.5):
        r.part("cube", 0, 0.5, 0, 0.07, 1.1, 0.07, OAK)  # the haft
        r.part("cube", 0, 0.06, 0.16, 0.04, 0.32, 0.36, IRON)  # the head, sunk in the wood
    r.part("cyl", 0.75, 0.2, -0.55, 0.34, 0.4, 0.34, (80, 62, 44), tex="wood_plank")  # the bucket
    r.part("cyl", 0.75, 0.38, -0.55, 0.3, 0.02, 0.3, stain)
    r.part("cyl", 0.75, 0.3, -0.55, 0.36, 0.04, 0.36, DARK_IRON)  # its hoop


def meat_hooks(r, t, seed, ceil_h):
    """A rail of butcher's hooks hung from the ceiling on chains, a few still carrying slabs."""
    r.part("cube", 0, ceil_h - 0.1, 0, 1.8, 0.12, 0.12, DARK_IRON)  # the rail
    for i in range(3):
        x = -0.6 + i * 0.6
        length = 1.0 + ((seed + i) % 3) * 0.45
        sway = math.sin(t * 0.7 + seed + i * 1.7) * 0.05
        with r.at(x, ceil_h - 0.15, 0, rx=sway):
            for k in range(int(length / 0.2)):
                r.part("cube", 0, -0.1 - k * 0.2, 0, 0.03, 0.2, 0.07, IRON, ry=0 if k % 2 else 1.57)
            y = -length - 0.1
            r.part("cube", 0, y, 0.05, 0.04, 0.2, 0.04, DARK_IRON)  # the hook's shank
            r.part("cube", 0, y - 0.1, 0.0, 0.04, 0.04, 0.14, DARK_IRON)  # and its curl
            if (seed + i) % 3:
                r.part("cube", 0, y - 0.45, 0, 0.32, 0.6, 0.18, (120, 44, 40), rz=0.08)  # a slab
                r.part("cube", 0, y - 0.45, 0.095, 0.26, 0.5, 0.01, (170, 140, 116))  # its fat


# The Cinderhold's models live in their own module; it borrows the helpers above, so it is imported last.
from ashen_vault.render import forge_models  # noqa: E402
