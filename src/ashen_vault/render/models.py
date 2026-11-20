"""Original low-poly models assembled from primitives. All face +X."""

import functools
import itertools
import math
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass

from ashen_vault.ai.enemy import COMBO_GAP
from ashen_vault.player import view_blend, weapons
from ashen_vault.player.items import Items
from ashen_vault.render import bounds, shapes
from ashen_vault.util import rround
from ashen_vault.world import terrain, villagers

BONE = (214, 204, 178)
RUST = (120, 70, 44)
IRON = (92, 92, 98)
ASH = (96, 92, 88)
EMBER = (255, 140, 50)
HIT_GLOW = (255, 105, 85)  # a glowing part in the moment a blow lands: red, like the body's flash
PASSAGE_DARK = (6, 5, 6)  # the black of a way on into the unknown, seen through a gate
HIT_TINT = (1.0, 0.45, 0.4)  # how far a struck body's pale flash colour leans to red (1 keeps a channel)


def hit_tint(rgb):
    """The colour a body part flashes when struck: its pale flash colour, leaning red by HIT_TINT."""
    return tuple(rround(c * k) for c, k in zip(rgb, HIT_TINT, strict=True))


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
        "hollow_inmate": prison_models.hollow_inmate,
        "forge_golem": forge_models.forge_golem,
        "iron_bowman": forge_models.iron_bowman,
        "slag_hound": forge_models.slag_hound,
        "brand": forge_models.gargoyle,
        "bellows": forge_models.gargoyle,
        "sexton": cemetery_models.sexton,
        "mourner": cemetery_models.mourner,
        "ashen_husk": cemetery_models.ashen_husk,
        "sewer_rat": sewer_models.sewer_rat,
        "giant_rat": sewer_models.giant_rat,
        "rat_matron": sewer_models.rat_matron,
        "sludge_slime": sewer_models.sludge_slime,
        "slimelet": sewer_models.slimelet,
        "drowned": sewer_models.drowned,
        "bilge_leech": sewer_models.bilge_leech,
        "sodden_pall": sewer_models.sodden_pall,
        "pall_clot": sewer_models.pall_clot,
        "pale_sentinel": moon_models.pale_sentinel,
        "lantern_wraith": moon_models.lantern_wraith,
        "moonhound": moon_models.moonhound,
        "veiled_knight": moon_models.veiled_knight,
        "moon_duchess": moon_models.moon_duchess,
        "stone_golem": sunken_models.stone_golem,
        "sunken_sexton": sunken_models.sunken_sexton,
        "keystone": sunken_models.keystone,
        "harpy": sunken_models.harpy,
    }.get(e.type.id)
    if e.type.id == "bone_walker" and getattr(e, "look", None) == "grave":
        fn = cemetery_models.grave_walker  # the cemetery's own dead, risen in their winding sheets
    if fn:
        fn(r, e, t)


def strike_angle(e):
    """Arm swing for melee enemies: raised during windup, slammed down on attack."""
    if e.state == "windup":
        return -2.2 * min(e.state_t / e.windup_time, 1)
    if e.state == "attack":
        return -2.2 + 3.0 * min(e.state_t / 0.2, 1)
    if e.state == "recover":
        return 0.8 * (1 - min(e.state_t / e.recover_time, 1))
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
        return _mix(rest, cocked, _ease(min(e.state_t / max(e.windup_time, 1e-3), 1)))
    if e.state == "attack":  # a heavy foe's blow travels over its `impact`
        return _mix(cocked, strike, _ease(min(e.state_t / max(0.2, e.type.impact), 1)))
    if e.state == "recover":
        return _mix(strike, rest, _ease(min(e.state_t / max(e.recover_time, 1e-3), 1)))
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
    """`rgb` scaled by `k` (a k over 1 brightens it), each channel kept within 0..255."""
    return _dimmed(tuple(rgb), k)


@functools.lru_cache(maxsize=4096)
def _dimmed(rgb, k):
    return tuple(min(rround(c * k), 255) for c in rgb)


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
    bone = hit_tint((255, 240, 220)) if e.flashing else BONE
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
    green = hit_tint((200, 220, 160)) if e.flashing else SLIME
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


WISP_SHELLS = (  # (radius, height, tongues, colour) of each shell of a wisp's flame, outer first
    (0.42, 0.95, 6, (200, 58, 24)),
    (0.32, 0.78, 5, (255, 132, 38)),
    (0.22, 0.58, 4, (255, 214, 110)),
)
WISP_CINDERS = 5  # sparks rising off it


def cinder_wisp(r, e, t):
    """A burnt skull in a living flame. Three shells of flickering tongues, deep red outside, then
    orange, then a yellow core, wrap a blackened skull whose sockets glow. Below it a tail of embers
    gutters away and above it cinders drift up and fade. Winding up, the flame draws in and burns
    white, then flares as it throws; slain, it gutters into smoke and the cooled skull drops."""
    fade = death_fall(e, 0.9)
    lit = fade < 0.6
    bob = math.sin(t * 3) * 0.12 * (1 - fade)
    charge = min(e.state_t / max(e.type.windup, 1e-3), 1.0) if e.state == "windup" else 0.0
    flare = 1.0 - min(e.state_t / 0.25, 1.0) if e.state == "attack" else 0.0
    size = (1 - fade) * (1 - 0.3 * charge + 0.35 * flare)
    with r.at(0, e.type.hover + bob - 0.5 * fade, 0):
        if size > 0.05:
            for j, (rad, h, n, rgb) in enumerate(WISP_SHELLS):
                hot = _blend(rgb, (255, 250, 230), charge * (0.4 + 0.2 * j))
                for i in range(n):
                    a = i * math.tau / n + t * (0.9 + 0.5 * j) * (-1) ** j
                    k = 1 + 0.25 * math.sin(t * (9 + 2 * j) + i * 2.3)
                    lean = 0.25 + 0.1 * math.sin(t * 5 + i)
                    with r.at(
                        math.cos(a) * rad * 0.55 * size - 0.08, -0.3, math.sin(a) * rad * 0.55 * size, ry=-a
                    ):
                        r.part("cone", 0, h * k * size * 0.5, 0, rad * size, h * k * size, rad * 0.8 * size,
                               hot, rz=-lean, glow=True)  # fmt: skip
            r.part(
                "sphere", 0, 0.02, 0, 0.3 * size, 0.28 * size, 0.3 * size, (255, 236, 170), glow=True
            )  # core
        with r.at(0.16, -0.6 * fade * fade, 0, s=1.2, rz=-0.8 * fade):  # the skull, dropping as it cools
            eye = (255, 230, 150) if charge > 0.3 else EMBER
            skull(r, CHAR, eye if lit else (36, 22, 18), glow=lit, jaw=0.2 + 0.4 * charge + 0.3 * flare)
        for i in range(4):  # the tail: embers guttering away below, lagging behind as it drifts
            k = (t * 1.6 + i / 4) % 1.0
            y = -0.25 - k * 0.55
            sz = 0.09 * (1 - k) * (1 - fade)
            if sz > 0.01:
                r.part("cube", -0.12 * k + 0.05 * math.sin(t * 7 + i), y, 0.06 * math.cos(t * 5 + i * 2), sz, sz, sz,
                       (255, rround(170 - 110 * k), 40), glow=True)  # fmt: skip
        for i in range(WISP_CINDERS if fade == 0 else 0):  # cinders drifting up off the flame, going out
            k = (t * 0.7 + i / WISP_CINDERS) % 1.0
            a = i * 2.4 + t * 0.8
            sz = 0.045 * (1 - k)
            rgb = (255, rround(200 - 120 * k), rround(90 - 60 * k))
            r.part("cube", math.cos(a) * (0.2 + 0.3 * k), 0.3 + k * 0.45, math.sin(a) * (0.2 + 0.3 * k), sz, sz, sz,
                   rgb, glow=True)  # fmt: skip
        if fade > 0:  # the flame gone, smoke rising where it burned
            k = min(fade * 1.2, 1.0)
            g = rround(70 - 20 * k)
            for i in range(3):
                sz = 0.2 * (1 - 0.6 * k)
                r.part("cube", 0.08 * math.sin(i * 2.1), 0.05 + 0.2 * k + i * 0.1, 0.08 * math.cos(i * 1.7),
                       sz, sz, sz, (g, g, g))  # fmt: skip


def _blend(a, b, k):
    """Colour `a` blended a share `k` (0..1) toward `b`."""
    k = min(max(k, 0.0), 1.0)
    return tuple(rround(p + (q - p) * k) for p, q in zip(a, b, strict=True))


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
    """The prison's warden: a giant in soot-black plate under a ragged ash-grey tabard and cape, a crested
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
        # between the legs bearing the prison's sigil (a diamond with a bar through it).
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
    skin = hit_tint((240, 220, 200)) if e.flashing else (150, 120, 100)
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
    """The prison's slaughterman: a huge, lumpen brute, pot-bellied and humpbacked, in a stitched
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
    skin = hit_tint((240, 220, 200)) if e.flashing else (176, 110, 92) if rage else MEAT
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
    bone = hit_tint((255, 240, 220)) if e.flashing else BONE
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
    style = getattr(e, "look", None) or "wood"
    if e.state == "dormant":
        chest(r, False, style)
        return
    shell, tex = CHEST_SHELLS.get(style, CHEST_SHELLS["wood"])
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
        r.part("cube", 0, 0.25, 0, 0.6, 0.5, 0.9, shell, tex=tex)
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
            r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, shell, tex=tex)
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


SNARE_STALK = (112, 126, 100)  # a pale, grey-green stalk
SNARE_RIB = (78, 92, 70)
SNARE_LEAF = (100, 128, 86)
SNARE_LEAF_DARK = (70, 94, 62)
SNARE_FLESH = (176, 28, 44)
SNARE_THROAT = (236, 70, 56)
SNARE_TOOTH = (232, 226, 200)
SNARE_SEGMENTS = 4  # the stalk's segments, each this long
SNARE_SEGMENT = 0.32


def snare_bloom(r, e, t):
    """A man-eating plant on one tall stalk. A flared root bulb sits in a star of blade-like leaves;
    a pale, ribbed stalk rises from it, curling back on the windup and lashing forward on the strike;
    under its head a ruff of broad pointed leaves fans out, and the head itself is an upright pod of
    two ribbed, leafy lips that part sideways to bare red flesh lined with teeth and a glowing throat,
    crowned with spiky leaves. Slain, the stalk folds over and the lips hang slack."""
    hurt = e.flashing
    wilt = death_fall(e)
    gape = jaw_open(e, t)
    lunge = 0.35 if e.state == "windup" else (0.55 if e.state == "attack" else 0)
    sway = math.sin(t * 1.3) * 0.08 * (1 - wilt)
    stalk = hit_tint((236, 230, 220)) if hurt else SNARE_STALK
    leaf = hit_tint((226, 232, 220)) if hurt else SNARE_LEAF
    # The root bulb and its star of blade leaves splayed on the floor.
    r.part("frustum", 0, 0.12, 0, 0.62, 0.24, 0.62, _dim(stalk, 0.8))
    r.part("sphere", 0, 0.22, 0, 0.42, 0.26, 0.42, _dim(stalk, 0.9))
    for i in range(6):
        a = i * math.tau / 6 + 0.25
        with r.at(math.cos(a) * 0.2, 0.08, math.sin(a) * 0.2, ry=-a, rz=-1.35 + 0.08 * math.sin(t + i)):
            r.part("blade", 0, 0.38, 0, 0.03, 0.75, 0.22, leaf if i % 2 else _dim(leaf, 0.82))
            r.part("cube", 0.012, 0.3, 0, 0.012, 0.56, 0.02, SNARE_RIB)  # its midrib
    # The stalk: segments bending back on the windup, lashing forward on the strike, folding in death.
    bend = sway * 0.6 - lunge * 0.22
    angles = [bend + lunge * (0.32 if k >= 2 else -0.05) - 0.42 * wilt for k in range(SNARE_SEGMENTS)]
    with r.at(0, 0.3, 0):
        _snare_stalk(r, angles, stalk, leaf, gape, hurt, t, wilt)


def _snare_stalk(r, angles, stalk, leaf, gape, hurt, t, wilt, k=0):
    """One segment of the stalk, then the next on top of it, and the head on the last."""
    if k == len(angles):
        # Undo the stalk's bends so the pod stands upright, its mouth toward +X; it droops in death.
        with r.at(0, 0, 0, rz=-sum(angles) - 1.1 * wilt):
            _snare_head(r, gape, hurt, stalk, leaf, t, wilt)
        return
    with r.at(0, 0, 0, rz=angles[k]):
        w = 0.2 - 0.025 * k
        r.part("cyl", 0, SNARE_SEGMENT / 2, 0, w, SNARE_SEGMENT + 0.02, w, stalk)
        for i in range(3):  # ribs running up it
            a = i * math.tau / 3 + k
            r.part("cube", math.cos(a) * w * 0.45, SNARE_SEGMENT / 2, math.sin(a) * w * 0.45, 0.03,
                   SNARE_SEGMENT, 0.03, SNARE_RIB, ry=-a)  # fmt: skip
        r.part("cyl", 0, 0.0, 0, w * 1.15, 0.04, w * 1.15, _dim(stalk, 0.78))  # the node
        if k == 1:  # a single blade leaf springing from the stalk
            with r.at(0, 0.16, 0, ry=2.0, rz=-0.9 + 0.1 * math.sin(t * 1.7)):
                r.part("blade", 0, 0.3, 0, 0.025, 0.6, 0.16, _dim(leaf, 0.9))
        with r.at(0, SNARE_SEGMENT, 0):
            _snare_stalk(r, angles, stalk, leaf, gape, hurt, t, wilt, k + 1)


def _snare_head(r, gape, hurt, stalk, leaf, t, wilt):
    """The ruff of leaves, the two-lipped pod and its crest, from the top of the stalk."""
    flesh = hit_tint((240, 210, 210)) if hurt else SNARE_FLESH
    # The ruff: broad pointed leaves fanning out and down beneath the pod, stirring.
    for i in range(5):
        a = i * math.tau / 5 + 0.3
        flare = 1.05 + 0.25 * min(gape, 1.0) - 0.5 * wilt + 0.05 * math.sin(t * 2 + i)
        with r.at(0, 0.02, 0, ry=-a), r.at(0, 0, 0, rz=-flare):
            r.part(
                "blade", 0, 0.34, 0, 0.03, 0.7, 0.36, leaf if i % 2 else SNARE_LEAF_DARK if not hurt else leaf
            )
            r.part("cube", 0.016, 0.28, 0, 0.012, 0.5, 0.025, SNARE_RIB)  # midrib
    r.part("sphere", 0, 0.1, 0, 0.3, 0.22, 0.3, _dim(stalk, 0.85))  # the pod's base
    # The pod: two lips hinged at its back (-X), standing upright, parting sideways (+-Z).
    with r.at(-0.14, 0.55, 0, s=1.2):
        slack = 0.35 * wilt
        r.part("sphere", 0.02, 0, 0, 0.3, 0.72, 0.18, SNARE_THROAT, glow=gape > 0.6 and wilt < 0.5)  # throat
        for side in (1, -1):
            with r.at(0, 0, 0, ry=-side * (gape * 0.55 + slack)):
                _snare_lip(r, side, stalk, flesh)
    # The crest: spiky leaves standing up over the pod.
    for i, (a, h) in enumerate(((0.0, 0.42), (0.5, 0.32), (-0.5, 0.32))):
        with r.at(-0.1, 1.02, 0, rx=a, rz=-0.15 + 0.05 * math.sin(t * 1.5 + i)):
            r.part("wedge", 0, h / 2, 0, 0.04, h, 0.12, _dim(leaf, 0.95))


def _snare_lip(r, side, stalk, flesh):
    """One lip of the pod on side `side` (+-Z), its hinge at the origin: a ribbed leafy shell, red
    flesh on its inner face and a row of teeth down its front edge pointing across the mouth."""
    z = side * 0.11
    r.part("sphere", 0.17, 0, z, 0.42, 0.86, 0.2, stalk)  # the shell
    r.part("sphere", 0.17, 0, z - side * 0.035, 0.36, 0.78, 0.13, flesh)  # its inner flesh
    for dy in (-0.22, 0.0, 0.22):  # ribs across the shell
        r.part("cube", 0.17, dy, z + side * 0.09, 0.32, 0.03, 0.02, SNARE_RIB)
    r.part("cube", 0.17, 0, z + side * 0.1, 0.03, 0.72, 0.02, SNARE_RIB)  # the spine
    for k in range(6):  # teeth down the front edge
        y = -0.3 + k * 0.12
        r.part("cone", 0.36, y, z - side * 0.05, 0.035, 0.09, 0.035, SNARE_TOOTH, rx=-side * math.pi / 2)


HUSK_BARK = (112, 94, 80)  # grey-brown dead wood
HUSK_HOLLOW = (16, 10, 8)
HUSK_FIBRE = (78, 58, 46)  # the stringy wood hanging in its mouth
HUSK_ROOT_Y = 0.3  # where the trunk's flared foot meets its roots
HUSK_NECK_Y = 1.6  # where the flared foot narrows into the upper trunk
HUSK_TOP_Y = 2.4  # the broken top, crowned with splinters
# Its branches: (height, side, spread round the trunk, rest elevation, length, kink). The first pair,
# at the shoulders, does the slam.
HUSK_LIMBS = (
    (1.95, 1, 1.25, -0.1, 0.95, 0.35),
    (1.95, -1, 1.25, -0.1, 0.95, -0.3),
    (1.1, 1, 1.0, -0.45, 0.8, -0.4),
    (1.15, -1, 1.05, -0.5, 0.75, 0.45),
    (2.25, 1, 1.9, 0.35, 0.65, 0.5),
    (2.2, -1, 2.0, 0.3, 0.7, -0.45),
)


def _husk_radius(y):
    """The trunk's radius at height `y`: a flared foot narrowing to the neck, then straight."""
    if y >= HUSK_NECK_Y:
        return 0.36
    k = max(y - HUSK_ROOT_Y, 0.0) / (HUSK_NECK_Y - HUSK_ROOT_Y)
    return 0.575 - (0.575 - 0.356) * k


def bark_husk(r, e, t):
    """A hollow dead tree that walks on its roots. Its top is broken off into a crown of jagged
    splinters, a face is split into its trunk (slanted ember eyes under a heavy brow, a tall gaping
    mouth hung with stringy fibres) and long bare branches jut from it, the shoulder pair raised
    together and brought down in a double slam. Down its back a split in the bark shows the glowing
    heart-fungus: the weak spot."""
    hit = strike_angle(e)
    hurt = e.flashing
    dead = e.state == "dead"
    moving = e.state in ("chase", "idle")
    slump = death_fall(e, 0.8)
    bark = hit_tint((240, 220, 200)) if hurt else HUSK_BARK
    dark = hit_tint((200, 180, 160)) if hurt else DARK_BARK
    lean = -0.25 if e.state == "windup" else (0.12 if e.state == "hurt" else -0.06)
    lean -= 0.85 * slump  # keels over forward on its face as it dies
    _husk_roots(r, t, moving, dark)
    pivot = _husk_radius(HUSK_ROOT_Y)  # it tips over the front edge of its foot
    with r.at(pivot, 0, 0, rz=lean), r.at(-pivot, 0, 0):
        r.part("frustum", 0, (HUSK_ROOT_Y + HUSK_NECK_Y) / 2, 0, 1.15, HUSK_NECK_Y - HUSK_ROOT_Y, 1.1, bark,
               tex="bark")  # fmt: skip
        r.part("cyl", 0, HUSK_ROOT_Y / 2 + 0.02, 0, 1.12, HUSK_ROOT_Y, 1.06, bark, tex="bark")
        with r.at(0, HUSK_NECK_Y, 0, ry=0.12):
            r.part("cyl", 0, (HUSK_TOP_Y - HUSK_NECK_Y) / 2, 0, 0.72, HUSK_TOP_Y - HUSK_NECK_Y, 0.7, bark,
                   tex="bark")  # fmt: skip
        _husk_crown(r, bark, dark)
        _husk_face(r, e, t, dark)
        with r.at(-0.2, 1.45, 0):
            _husk_heart(r, t, hurt, dead=dead)
        for y, a, w in ((0.75, 2.0, 0.3), (0.95, 2.3, 0.22), (2.0, -2.0, 0.24)):  # shelf fungus
            rad = _husk_radius(y)
            x, z = math.cos(a) * rad, math.sin(a) * rad
            r.part("cyl", x, y, z, w, 0.05, w, (196, 172, 120))
            r.part("cyl", x, y - 0.03, z, w * 0.8, 0.02, w * 0.8, (126, 98, 64))
        for y, a in ((0.5, -1.2), (1.3, 1.6), (2.3, 2.7)):  # moss clinging to it
            rad = _husk_radius(y)
            with r.at(math.cos(a) * rad, y, math.sin(a) * rad, ry=-a):
                r.part("sphere", 0, 0, 0, 0.1, 0.3, 0.34, _dim(MOSS, 0.75))
        for i, (y, side, spread, rest, length, kink) in enumerate(HUSK_LIMBS):
            sway = math.sin(t * (2.4 if moving else 1.1) + i * 1.9) * 0.08
            if e.state == "hurt":
                sway += math.sin(t * 22 + i) * 0.18  # thrashing
            elev = rest + sway
            if i < 2:  # the slam: raised high and swept in, then brought down in front
                k = min(abs(hit) / 2.2, 1.0)
                elev = rest - hit * 0.5 + (0 if hit else sway)
                spread -= 0.55 * k
            elev -= 0.9 * slump  # the branches droop as it falls
            rad = _husk_radius(y) * 0.9
            with r.at(0, y, side * rad, ry=-side * spread, rz=elev):
                _husk_branch(r, length, bark, dark, kink)


def _husk_roots(r, t, moving, dark):
    """Buttress roots splayed round the foot, writhing as it glides along."""
    for i in range(6):
        a = i * math.tau / 6 + 0.3
        wr = math.sin(t * (5 if moving else 1.5) + i * 1.7) * (0.12 if moving else 0.04)
        with r.at(math.cos(a) * 0.38, 0.4, math.sin(a) * 0.38, ry=-a, rz=-2.05 + wr):
            r.part("frustum", 0, 0.32, 0, 0.3, 0.64, 0.22, dark, tex="bark")
            with r.at(0, 0.62, 0, rz=0.45 - wr):
                r.part("cone", 0, 0.22, 0, 0.16, 0.46, 0.12, dark)


def _husk_crown(r, bark, dark):
    """The broken top: a ring of jagged splinters leaning out round a dark hollow."""
    r.part("cyl", 0, HUSK_TOP_Y + 0.01, 0, 0.6, 0.04, 0.58, HUSK_HOLLOW)
    for k in range(7):
        a = k * math.tau / 7 + 0.2
        h = 0.32 + (k * 5 % 7) * 0.05
        with r.at(
            math.cos(a) * 0.28, HUSK_TOP_Y - 0.05, math.sin(a) * 0.28, ry=-a, rz=-0.22 - (k % 3) * 0.08
        ):
            r.part("blade", 0, h / 2, 0, 0.26, h, 0.2, bark if k % 2 else dark, tex="bark", ry=math.pi / 2)


def _husk_face(r, e, t, dark):
    """Split into the front of the trunk: a heavy brow over slanted eye slits lit by embers, a knot of a
    nose, and a tall mouth hung with fibres that gapes wider as it winds up."""
    dead = e.state == "dead"
    rad = _husk_radius(HUSK_NECK_Y)
    for side in (1, -1):
        z = side * 0.13
        slant = side * 0.35  # the inner ends lower: a scowl
        r.part("cube", rad + 0.03, 2.13, z, 0.12, 0.08, 0.22, dark, rx=slant)  # brow
        r.part("cube", rad, 2.03, z, 0.05, 0.065, 0.17, HUSK_HOLLOW, rx=slant)
        r.part("cube", rad + 0.02, 2.03, z, 0.02, 0.035, 0.1, (60, 40, 30) if dead else (255, 90, 40),
               rx=slant, glow=not dead)  # fmt: skip
    r.part("sphere", rad + 0.03, 1.86, 0, 0.1, 0.14, 0.1, dark)  # a knot for a nose
    gape = 0.42 + 0.22 * max(jaw_open(e, t), 0.0)
    mid = 1.42 - gape / 4
    with r.at(_husk_radius(mid) + 0.01, mid, 0, rz=0.17):  # follows the foot's slope
        r.part("cube", 0, 0, 0, 0.06, gape, 0.3, HUSK_HOLLOW)
        for y in (1, -1):  # the lips: splintered bark
            r.part("cube", 0.03, y * (gape / 2 + 0.03), 0, 0.09, 0.08, 0.38, dark)
        for z in (1, -1):
            r.part("cube", 0.03, 0, z * 0.18, 0.09, gape, 0.07, dark)
        for k in range(5):  # fibres hanging from above
            z = (k - 2) * 0.055
            ln = 0.1 + (k * 3 % 4) * 0.035
            r.part("cone", 0.03, gape / 2 - ln / 2, z, 0.035, ln, 0.035, HUSK_FIBRE, rx=math.pi)
        for k in range(4):  # and rising from below
            z = (k - 1.5) * 0.065
            ln = 0.07 + (k * 5 % 3) * 0.035
            r.part("cone", 0.03, -gape / 2 + ln / 2, z, 0.03, ln, 0.03, HUSK_FIBRE)


def _husk_branch(r, length, bark, dark, kink):
    """A bare branch along +X: a tapering limb, a knotted crook and a thinner forearm ending in three
    twig claws, with a dead twig off the crook."""
    r.part("frustum", length / 2, 0, 0, 0.17, length, 0.17, bark, tex="bark", rz=-math.pi / 2)
    r.part("sphere", length, 0, 0, 0.15, 0.15, 0.15, dark)
    with r.at(length, 0, 0, rz=-0.25, ry=kink):
        fore = length * 0.85
        r.part("frustum", fore / 2, 0, 0, 0.11, fore, 0.11, bark, tex="bark", rz=-math.pi / 2)
        r.part("cone", 0.1, 0.12, 0, 0.04, 0.3, 0.04, dark, rz=-0.6)  # a dead twig
        with r.at(fore, 0, 0):
            for k in (-1, 0, 1):
                r.part("cone", 0.14, 0, k * 0.04, 0.045, 0.3, 0.045, dark, rz=-math.pi / 2, ry=k * 0.45)


def _husk_heart(r, t, hurt, dead=False):
    """A split down the back (-X) with the pulsing heart-fungus inside. It gutters out on death."""
    pulse = 1 + math.sin(t * 3.1) * 0.12 * (not dead)
    r.part("cube", -0.21, 0.3, 0, 0.08, 1.0, 0.22, (16, 10, 8))
    glow = HIT_GLOW if hurt else (60, 90, 76) if dead else (110, 240, 190)
    r.part("sphere", -0.2, 0.35, 0, 0.2 * pulse, 0.55 * pulse, 0.24 * pulse, glow, glow=not dead)
    for y, z in ((0.0, 0.1), (0.7, -0.08), (-0.25, -0.1)):
        r.part("sphere", -0.24, y, z, 0.12, 0.07, 0.12, (80, 220, 170), glow=not dead)
    for y in (0.05, 0.4, 0.75):
        r.part("cube", -0.25, y, 0, 0.05, 0.06, 0.3, DARK_BARK)


def stump_mimic(r, e, t):
    """Looks like a mossy tree stump until you come close; then the lid splits open on a fanged maw
    and stubby roots lift it off the ground."""
    settle = death_fall(e, 0.5)
    awake = e.state not in ("idle", "dead")
    hurt = e.flashing
    bark = hit_tint((240, 220, 200)) if hurt else BARK
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
    hurt = e.flashing
    body = hit_tint((150, 130, 150)) if hurt else SPIDER
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


def npc(r, look, t=0.0, near=True):
    """A villager facing +X, built from a `villagers.Look` square and blocky, as the old PS1 crawlers
    drew their folk: chunky boots and box legs (or a long robe flaring to its hem, or a kimono's wide
    hakama), a box chest with square shoulders and a coat skirt flaring below the belt, trimmed at hem,
    collar and cuffs, an apron or cloak, box arms hanging flush from the shoulders' corners ending in
    faceted hands (a flat palm, four jointed fingers and a thumb, closed round what they hold; three
    parts each beyond `world.DETAIL_RANGE`, `near` False), and an angular, faceless head (a flat face, a brow and a nose, no eyes) sitting right on
    the collar, under block hair, a beard, a hat or hood. They hold their trade's tool and idle by it
    (`look.idle`): the smith works a billet on the anvil before him (`villagers.smith_cycle`), the
    swordmaster stands ready by his blades (`villagers.half_draw`)."""
    hs, ws, stoop = villagers.BUILDS[look.build]
    sway = math.sin(t * 1.5) * 0.03
    shift = 0.0
    lean, nod = _idle_lean(look, t)
    if look.idle == "ready":  # a swordmaster stands still, his weight easing from foot to foot
        sway, shift = math.sin(t * 0.9) * 0.008, math.sin(t * 0.45) * 0.025
    beat = max(math.sin(t * 2.4), 0.0) ** 3  # the old hammer idle, the guard's shifting weight
    with r.at(0, 0, 0, rz=sway, rx=shift, s=hs):
        _villager_legs(r, look, ws)
        if look.idle == "smith":
            _smith_anvil(r, t)
        with r.at(0, 0.95, 0, rz=-stoop - lean):  # everything above the hips leans with the stoop
            _villager_torso(r, look, ws)
            _villager_arms(r, look, ws, t, beat, near)
            with r.at(
                0.03,
                HEAD_AT,
                0,
                rz=stoop * 0.6 + lean * 0.5 - nod - (0.12 if look.idle == "pray" else 0.0),
                ry=villagers.glance(t) if look.idle == "watch" else 0.0,
            ):
                _villager_head(r, look, t)
            if look.blade == "back":  # a sheathed curved sword slung across the back
                with r.at(-0.22, 0.15, 0, rx=0.9):
                    r.part("cube", 0, 0, 0, 0.06, 1.1, 0.08, (30, 26, 30))
                    r.part("cube", 0, 0.62, 0, 0.05, 0.25, 0.05, (160, 30, 40))
            elif look.blade == "hip":
                _hip_blades(r, look, ws, t)


CHEST_TOP = 0.62  # the flat top of the chest, the shoulders' line, above the hips
HEAD_AT = CHEST_TOP + 0.02  # the head sits on the collar; its short neck sinks into the chest
FLIP = math.pi  # turns a frustum over, so it narrows downward


def _idle_lean(look, t):
    """(forward lean of the body, downward nod of the head) for the idle: the smith leans into each
    blow and bends his head over the billet, then straightens to look at it."""
    if look.idle != "smith":
        return 0.0, 0.0
    stage, k = villagers.smith_cycle(t)
    if stage == "strike":
        land = villagers.SMITH_LAND
        bow = _ease((k - 0.4) / (land - 0.4)) if k < land else 1 - _ease((k - land) / (1 - land))
        return 0.08 + 0.1 * bow, 0.12 + 0.08 * bow
    if stage == "turn":
        return 0.08, 0.2
    if stage == "inspect":
        up = _ease(min(k / 0.25, (1 - k) / 0.25, 1.0))
        return 0.08 - 0.1 * up, 0.15 - 0.3 * up
    return 0.02, -0.1 * math.sin(k * math.pi)  # wiping his brow, his head tipped back


def _chest_width(ws):
    return 0.46 * ws


def _trim(look):
    """The darker band edging a villager's hem, collar and cuffs."""
    return _dim(look.cloth, 0.68)


def _mitt(r, rgb, size=0.15, grip=False, length=1.0):
    """A blocky mitt of a hand hanging from the wrist at the origin (down -Y), fingers forward (+X): a
    thick palm, the fingers as one block (curled forward under the palm when it grips) and a thumb."""
    s, ln = size, size * length
    r.part("cube", 0, -ln * 0.45, 0, s * 0.72, ln * 0.9, s, rgb)  # palm and back
    if grip:
        r.part("cube", s * 0.22, -ln * 0.95, 0, s * 0.66, ln * 0.32, s * 0.94, _dim(rgb, 0.94))
    else:
        r.part("cube", 0, -ln * 1.15, 0, s * 0.56, ln * 0.55, s * 0.9, _dim(rgb, 0.94))
    r.part("cube", s * 0.42, -ln * 0.45, 0, s * 0.26, ln * 0.5, s * 0.3, _dim(rgb, 0.97), rz=0.4)  # thumb


HAND_SIZE = 1.3  # the hand's scale: a little smaller than the arm is wide, yet readable from afar
# Where a closed hand holds its haft: (below the wrist, toward the palm), the fingers wrapped round it.
GRIP_AT = (-0.155, -0.026)
POLE_TOOLS = ("staff", "spear", "halberd")
# A villager's four fingers, index (+X, by the thumb) to little: (offset along the knuckles, first
# and second segment lengths). The middle finger is the longest, the little one the shortest.
VILLAGER_FINGERS = (
    (0.034, 0.042, 0.034),
    (0.0115, 0.047, 0.037),
    (-0.0115, 0.044, 0.035),
    (-0.033, 0.034, 0.028),
)
KNUCKLES_AT = -0.1  # the finger roots, below the wrist
VILLAGER_BONES = 0.62  # a villager's finger bones against the player's (before HAND_SIZE)
VILLAGER_GIRTH = 0.68  # and their thickness: stouter for their length, so they read from afar
REST_CURL = 0.35  # a hanging hand's loosely bent fingers
GRIP_CURL = 1.45  # fingers closed round a haft


def _villager_hand(r, rgb, side, curl=REST_CURL, thumb=0.45, thin=1.0, fat=1.0, knotty=False, seam=None):
    """A villager's hand hanging from the wrist at the origin (down -Y), faceted rather than round
    but shaped like a hand: smaller than the arm, a flat palm narrowing to the heel, the thumb toward
    +X and the palm toward the body (-`side` Z). Four fingers of two segments each curl in toward
    the palm by `curl` per joint (wrapping a haft along X at GRIP_CURL), and a two-segment thumb
    swings forward off the palm by `thumb`. `thin` slims the bones (an old hand, `knotty` at the
    joints), `fat` thickens them (a work glove, `seam` stitched down its back)."""
    # Built as the player's fist is (`_fist`: FINGERS' lengths and girths, three BONES a finger curling
    # by CURL's share at each joint, a three-bone thumb from the heel), but faceted like the villagers.
    k = VILLAGER_BONES / FIST_SCALE
    shade = _dim(rgb, 0.86)
    r.part("frustum", 0, -0.01, 0, 0.085 * fat, 0.05, 0.058 * fat, rgb, rz=FLIP)  # the wrist, narrowing
    r.part("frustum", 0, -0.058, 0, 0.1 * fat, 0.09, 0.044 * fat * thin, rgb)  # palm, wide at the knuckles
    r.part("frustum", -0.012, -0.03, -side * 0.006, 0.07 * fat, 0.04, 0.05 * fat, _dim(rgb, 0.95), rz=FLIP)
    if seam:
        r.part("cube", 0, -0.055, side * 0.023 * fat, 0.008, 0.08, 0.004, seam)
    for i, ((_, ln, girth), x) in enumerate(zip(FINGERS, (0.034, 0.0115, -0.0115, -0.033), strict=True)):
        tone = rgb if i % 2 == 0 else _dim(rgb, 0.9)  # neighbours apart, so each finger reads
        thick = FINGER * girth * VILLAGER_GIRTH * fat * thin
        with ExitStack() as stack:
            stack.enter_context(r.at(x * fat, KNUCKLES_AT, 0))
            j = thick * (1.35 if knotty else 1.15)
            r.part("cube", 0, 0, 0, j, j * 0.8, j, _bright(tone, 1.06, 4))  # the knuckle
            for bone, bend in zip(BONES, CURL, strict=True):
                stack.enter_context(r.at(0, 0, 0, rx=side * curl * bend / CURL[0]))
                length = bone * ln * k
                r.part("frustum", 0, -length / 2, 0, thick, length, thick, tone, rz=FLIP)
                stack.enter_context(r.at(0, -length, 0))
                thick *= 0.88
    # The thumb: from the heel's fleshy root on the index side, out and forward, closing across the
    # fingers by `thumb`.
    thick = FINGER * 1.2 * VILLAGER_GIRTH * fat * thin
    with ExitStack() as stack:
        stack.enter_context(r.at(0.04 * fat, -0.03, -side * 0.012, rz=0.3 - 0.1 * thumb))
        for n, (length, bend) in enumerate(((0.03, 0.25), (0.026, 0.55), (0.02, 0.45))):
            stack.enter_context(r.at(0, 0, 0, rx=side * (bend * thumb + (0.25 if n == 0 else 0.0))))
            r.part("frustum", 0, -length / 2, 0, thick, length, thick, rgb if n % 2 == 0 else shade, rz=FLIP)
            stack.enter_context(r.at(0, -length, 0))
            thick *= 0.88


def _villager_hand_far(r, rgb, side, curl=REST_CURL, fat=1.0):
    """The same hand for a villager seen from afar, in three parts: palm, the fingers as one curled
    slab and the thumb."""
    r.part("frustum", 0, -0.055, 0, 0.098 * fat, 0.1, 0.046 * fat, rgb)
    with r.at(0, KNUCKLES_AT, 0, rx=side * curl):
        r.part("cube", 0, -0.035, 0, 0.088 * fat, 0.07, 0.022 * fat, _dim(rgb, 0.92))
    r.part("cube", 0.05 * fat, -0.07, -side * 0.01, 0.022, 0.06, 0.022, rgb, rz=0.6)


def _villager_legs(r, look, ws):
    if look.garb == "robe":  # a robe flaring to the ankles, the boots' toes peeping out
        r.part("frustum", 0, 0.5, 0, 0.6 * ws, 1.0, 0.66 * ws, look.cloth)
        r.part("frustum", 0, 0.05, 0, 0.63 * ws, 0.1, 0.69 * ws, _trim(look))  # hem band
        r.part("cube", 0.17 * ws, 0.5, 0, 0.02, 0.9, 0.06, _trim(look))  # the seam down its front
        for z in (-0.1, 0.1):
            r.part("cube", 0.26 * ws, 0.04, z * ws, 0.14, 0.08, 0.11, look.boots)
        return
    if look.garb == "kimono":  # wide pleated hakama, split for each leg, over tabi and sandals
        pleat = _dim(look.trousers, 0.72)
        for z in (-0.13, 0.13):
            r.part("frustum", 0, 0.52, z * ws, 0.42, 0.86, 0.34, look.trousers)
            r.part("frustum", 0, 0.12, z * ws, 0.44, 0.06, 0.36, pleat)  # the hem
            for dz in (-0.07, 0.0, 0.07):  # pleats down the front
                r.part("cube", 0.17, 0.5, z * ws + dz, 0.012, 0.8, 0.012, pleat, rz=0.06)
            r.part("cube", 0.04, 0.05, z * ws, 0.26, 0.08, 0.13, look.boots)  # tabi
            r.part("cube", 0.04, 0.01, z * ws, 0.3, 0.025, 0.15, (96, 80, 52))  # the sandal's sole
            r.part("cube", 0.12, 0.07, z * ws, 0.08, 0.015, 0.03, (40, 30, 26))  # its thong
        r.part("cube", -0.08, 0.86, 0, 0.12, 0.16, 0.38 * ws, look.trousers)  # the stiff back panel
        return
    for z in (-0.12, 0.12):
        r.part("cube", 0, 0.7, z * ws, 0.19, 0.42, 0.18, look.trousers)  # thigh
        r.part("cube", 0, 0.36, z * ws, 0.16, 0.34, 0.15, _dim(look.trousers, 0.9))  # shin
        r.part("cube", 0, 0.14, z * ws, 0.19, 0.2, 0.18, look.boots)  # boot
        r.part("frustum", 0, 0.27, z * ws, 0.23, 0.1, 0.22, _dim(look.boots, 0.82), rz=FLIP)  # flared cuff
        r.part("cube", 0.07, 0.04, z * ws, 0.32, 0.08, 0.19, _dim(look.boots, 0.9))  # foot


def _villager_torso(r, look, ws):
    w = _chest_width(ws)
    trim = _trim(look)
    r.part("cube", 0, CHEST_TOP - 0.24, 0, 0.28, 0.48, w, look.cloth)  # chest, square at the shoulders
    if look.garb == "kimono":
        # The kimono's crossed front: the right panel under the left, each edged in a dark band, and a
        # pale under-collar showing in the V at the throat; an obi wound round the waist.
        for side in (1, -1):
            r.part("cube", 0.143, CHEST_TOP - 0.2, side * 0.05, 0.012, 0.42, 0.055, trim, rx=side * 0.36)
            r.part(
                "cube", 0.141, CHEST_TOP - 0.1, side * 0.025, 0.01, 0.2, 0.04, (222, 216, 200), rx=side * 0.36
            )
        r.part("cube", 0.142, CHEST_TOP - 0.3, -0.03, 0.006, 0.3, 0.08, _dim(look.cloth, 0.9))  # the overlap
        r.part("cube", 0, 0.06, 0, 0.3, 0.16, w * 0.98, look.sash)  # the obi
        r.part("cube", 0, 0.06, 0, 0.31, 0.03, w * 0.99, _dim(look.sash, 0.7))  # a cord bound round it
        r.part("cube", -0.17, 0.06, 0, 0.06, 0.12, 0.16, _dim(look.sash, 0.85))  # its knot behind
        r.part("cube", 0, CHEST_TOP + 0.015, 0, 0.22, 0.05, 0.26, trim)  # collar
        return
    r.part("cube", 0.145, CHEST_TOP - 0.24, 0, 0.012, 0.46, 0.05, trim)  # the coat's front edge
    r.part("cube", 0, 0.08, 0, 0.26, 0.14, w * 0.9, _dim(look.cloth, 0.92))  # waist
    r.part("cube", 0, 0.03, 0, 0.3, 0.07, w * 0.95, look.belt)  # belt
    r.part("cube", 0.155, 0.03, 0, 0.02, 0.07, 0.07, (170, 150, 90))  # buckle
    r.part("frustum", 0, -0.2, 0, 0.42, 0.42, w * 1.45, look.cloth)  # the coat's skirt, flaring below
    r.part("frustum", 0, -0.38, 0, 0.44, 0.06, w * 1.5, trim)  # its hem
    r.part("cube", 0, CHEST_TOP + 0.015, 0, 0.22, 0.05, 0.26, trim)  # collar
    if look.apron:
        long = look.idle == "smith"  # a smith's leather apron, down to his shins
        r.part("cube", 0.15, CHEST_TOP - 0.24, 0, 0.02, 0.3, w * 0.5, look.apron)  # bib
        r.part("cube", 0.185, -0.2 - 0.15 * long, 0, 0.02, 0.44 + 0.3 * long, w * 0.65, look.apron, rz=0.19)
        r.part("cube", 0.2, -0.26, 0, 0.01, 0.12, w * 0.3, _dim(look.apron, 0.8), rz=0.19)  # pocket
        if long:
            for side in (1, -1):  # straps over the shoulders, and a scorch on the leather
                r.part(
                    "cube", 0.08, CHEST_TOP - 0.02, side * w * 0.22, 0.16, 0.03, 0.04, _dim(look.apron, 0.8)
                )
            r.part("cube", 0.215, -0.44, w * 0.12, 0.008, 0.1, 0.08, _dim(look.apron, 0.55), rz=0.19)
            r.part("cube", 0.2, -0.26, -w * 0.18, 0.02, 0.16, 0.03, TOOL_IRON, rz=0.19)  # tongs in a loop
    if look.tabard:
        _tabard(r, look, w)
    if look.cloak:
        r.part("cube", -0.22, 0.05, 0, 0.05, 0.98, w * 1.25, look.cloak, rz=-0.1)
        r.part("cube", -0.02, CHEST_TOP - 0.02, 0, 0.34, 0.07, w + 0.36, _dim(look.cloak, 1.1))  # mantle
        r.part("cube", 0.165, CHEST_TOP - 0.06, 0, 0.03, 0.06, 0.06, (170, 150, 90))  # clasp


CREST_GOLD = (196, 160, 70)  # the realm's sun, on the watch's tabards and shields
CREST_DARK = (40, 34, 36)  # its lone watchtower


def _crest_badge(r, x, y, k=1.0, side=1):
    """The realm's crest, small, on a face looking along `side` X: a half-sunk sun behind a dark tower."""
    r.part("cube", x, y, 0, 0.008, 0.07 * k, 0.15 * k, CREST_GOLD)
    r.part("cube", x, y + 0.045 * k, 0, 0.008, 0.03 * k, 0.1 * k, CREST_GOLD)
    r.part("cube", x + side * 0.004, y + 0.02 * k, 0, 0.008, 0.14 * k, 0.035 * k, CREST_DARK)
    r.part("cube", x + side * 0.004, y + 0.09 * k, 0, 0.008, 0.025 * k, 0.055 * k, CREST_DARK)


def _tabard(r, look, w):
    """The watch's tabard over the mail coat: a panel front and back from the shoulders, belted at the
    waist and hanging past it over the coat's skirt, hemmed dark, the crest on the breast."""
    edge = _dim(look.tabard, 0.6)
    for side in (1, -1):
        x = side * 0.148
        r.part("cube", x, CHEST_TOP - 0.28, 0, 0.012, 0.56, w * 0.6, look.tabard)  # over the chest
        r.part("cube", side * 0.19, -0.2, 0, 0.012, 0.46, w * 0.6, look.tabard, rz=side * 0.19)  # the skirt
        r.part("cube", side * 0.232, -0.42, 0, 0.014, 0.04, w * 0.62, edge, rz=side * 0.19)  # its hem
        for dz in (-1, 1):  # its side edges
            r.part("cube", x, CHEST_TOP - 0.28, dz * w * 0.3, 0.014, 0.56, 0.02, edge)
    r.part("cube", 0, CHEST_TOP + 0.005, 0, 0.3, 0.03, w * 0.6, look.tabard)  # over the shoulders
    r.part("cube", 0, 0.03, 0, 0.32, 0.07, w * 0.96, look.belt)  # the belt cinched over it
    r.part("cube", 0.163, 0.03, 0, 0.02, 0.07, 0.07, (170, 150, 90))
    _crest_badge(r, 0.156, CHEST_TOP - 0.24)


def _kite_shield(r, rgb, side):
    """A kite shield slung on the forearm's outer face (`side` Z), its long axis down the arm: a painted
    board with a rim and a pointed foot, a pale stripe down it and an iron boss."""
    rim = (88, 80, 72)
    with r.at(0.06, -0.12, side * (ARM * 0.5 + 0.03)):
        r.part("cube", 0, 0.02, 0, 0.36, 0.4, 0.03, rgb)  # the board
        r.part("cube", 0, -0.2, 0, 0.18, 0.18, 0.03, rgb, rz=math.pi / 4)  # its pointed foot
        r.part("cube", 0, 0.225, 0, 0.38, 0.03, 0.04, rim)  # the rim along its top
        for dx in (-1, 1):
            r.part("cube", dx * 0.185, 0.04, 0, 0.025, 0.38, 0.04, rim)
            r.part("cube", dx * 0.09, -0.21, 0, 0.025, 0.24, 0.04, rim, rz=-dx * math.pi / 4)
        r.part("cube", 0, 0.02, side * 0.018, 0.06, 0.4, 0.01, _dim(CREST_GOLD, 0.9))  # a pale stripe down it
        r.part("frustum", 0, 0.06, side * 0.025, 0.09, 0.03, 0.09, TOOL_IRON, rx=side * math.pi / 2)  # boss


TOOL_WOOD = (96, 70, 44)
TOOL_IRON = (110, 110, 118)
ARM = 0.16  # a villager's arm, square in section
LACING = (150, 64, 44)  # the cords that lace a pauldron's plates


def _villager_arms(r, look, ws, t, beat, near=True):
    """Two box arms hanging flush from the chest's square shoulders, each an upper arm and a forearm
    with a trimmed cuff, ending in a hand (`_hand_of`). The right one (+Z) works the tool; the left rests, holds
    the smith's tongs or the swordmaster's scabbard, or both clasp in prayer."""
    sleeve = (look.cloak or look.cloth) if look.garb == "robe" else look.cloth
    reach = _chest_width(ws) / 2 + ARM / 2
    hand = look.gloves or look.skin
    for side in (1, -1):
        sh, el, tool, roll, wrist = _arm_pose(look, side, t, beat)
        with r.at(0, CHEST_TOP - 0.07, side * reach, rz=sh, rx=-side * 0.06 + roll):
            r.part("cube", 0, -0.11, 0, ARM, 0.36, ARM, sleeve)
            if look.pauldron and side == -1:
                _pauldron(r, look.pauldron)
            with r.at(0, -0.29, 0, rz=el):
                if look.sleeves == "rolled":  # the sleeve rolled to the elbow, the forearm bare
                    r.part("cube", 0, 0.0, 0, ARM * 1.14, 0.08, ARM * 1.14, _trim(look))
                    r.part("cube", 0, -0.14, 0, ARM * 0.86, 0.3, ARM * 0.86, look.skin)
                else:
                    r.part("cube", 0, -0.14, 0, ARM * 0.92, 0.3, ARM * 0.92, _dim(sleeve, 0.92))
                    if look.garb == "kimono":  # the wide sleeve hanging from the forearm
                        r.part("cube", -0.06, -0.12, 0, 0.26, 0.34, ARM * 1.08, sleeve)
                        r.part("cube", -0.06, -0.3, 0, 0.27, 0.03, ARM * 1.1, _trim(look))
                    else:
                        r.part("cube", 0, -0.27, 0, ARM * 1.12, 0.07, ARM * 1.12, _trim(look))  # cuff
                if look.shield and side == -1:
                    _kite_shield(r, look.shield, side)
                if look.gloves:  # a work glove's flared cuff
                    r.part("frustum", 0, -0.26, 0, ARM * 1.25, 0.09, ARM * 1.25, _dim(look.gloves, 0.85))
                pole = tool in POLE_TOOLS
                # A held tool turns the hand at the wrist: a haft along its knuckles, a staff or spear
                # cocked upright through the fist.
                turn = (math.pi / 2 - sh - el) if pole else wrist if tool else 0.0
                with r.at(0, -0.3, 0, rz=turn):
                    _hand_of(r, look, side, t, tool, hand, near)
                    if tool:
                        with r.at(0, GRIP_AT[0], side * GRIP_AT[1], rz=-math.pi / 2 if pole else 0.0):
                            _villager_tool(r, tool, t)


def _hand_of(r, look, side, t, tool, rgb, near):
    """Draws one villager hand at the wrist: closed round the tool it holds, else resting by the idle
    (the swordmaster's left on his scabbard, his right closing as it nears the hilt)."""
    curl, thumb = (GRIP_CURL, 1.0) if tool else (REST_CURL, 0.2)
    if look.idle == "ready":
        if side == -1:  # round the scabbard's mouth, the thumb pressed forward on the guard
            curl, thumb = 1.1, 0.0
        else:
            near_hilt = min(villagers.half_draw(t) / villagers.DRAW_SHOWN * 3, 1.0)
            curl, thumb = REST_CURL + (GRIP_CURL - REST_CURL) * near_hilt, 0.2 + 0.8 * near_hilt
    elif look.idle == "pray":
        curl = 0.7
    fat = 1.15 if look.gloves else 1.0
    with r.at(0, 0, 0, s=HAND_SIZE):
        if not near:
            _villager_hand_far(r, rgb, side, curl, fat)
            return
        bony = look.build == "stooped"
        _villager_hand(
            r, rgb, side, curl, thumb, thin=0.92 if bony else 1.0, fat=fat, knotty=bony,
            seam=_dim(look.gloves, 0.7) if look.gloves else None,
        )  # fmt: skip


def _pauldron(r, rgb):
    """A lacquered shoulder guard on the upper arm's outer face (-Z): a cap over the shoulder, then
    four plates hanging in a stack, each lapping the one below, laced together with cords."""
    r.part("cube", 0, 0.02, -0.02, 0.24, 0.05, 0.22, _dim(rgb, 1.15))  # the cap
    for k in range(4):
        y = -0.04 - k * 0.075
        z = -ARM / 2 - 0.025 - k * 0.006
        r.part("cube", 0, y, z, 0.26 + k * 0.01, 0.07, 0.03, rgb, rx=-0.12)
        r.part("cube", 0, y - 0.034, z, 0.27 + k * 0.01, 0.012, 0.034, _dim(rgb, 1.35), rx=-0.12)  # the rim
        for dx in (-0.07, 0.07):
            r.part("cube", dx, y, z - 0.016, 0.018, 0.06, 0.008, LACING)
    r.part("cube", 0, -0.37, -ARM / 2 - 0.05, 0.08, 0.03, 0.012, LACING)  # a cord's tassel


def _arm_pose(look, side, t, beat):
    """(shoulder, elbow, the tool held or None, inward roll, wrist) for one arm, from the idle. The
    shoulder and elbow swing the arm forward (+X), the roll turns it in across the body, and the wrist
    tips what the hand holds."""
    working = side == 1 and look.tool is not None
    idle = look.idle
    if idle == "smith":
        return _smith_arm(side, t)
    if idle == "ready":
        return _ready_arm(side, t)
    if idle == "pray":
        return 0.5, 1.2, look.tool if side == 1 and look.tool == "staff" else None, 0.0, 0.0
    if not working:
        if idle == "count":
            return 0.3, 1.1, None, 0.0, 0.0
        return 0.05 + 0.03 * math.sin(t * 1.3 + side), 0.15, None, 0.0, 0.0
    if idle == "hammer":
        return 0.2 + 1.4 * beat, 0.9 + 0.6 * (1 - beat), look.tool, 0.0, 0.0
    if idle == "stir":
        return 0.6 + 0.15 * math.sin(t * 3), 0.9 + 0.2 * math.cos(t * 3), look.tool, 0.0, 0.0
    if idle == "count":
        return 0.35, 1.25 + 0.08 * math.sin(t * 4), look.tool, 0.0, 0.0
    if look.tool in POLE_TOOLS:
        return 0.15, 0.55, look.tool, 0.0, 0.0
    if look.tool == "rod":
        return 0.7, 0.4, look.tool, 0.0, 0.0
    return 0.3, 1.0, look.tool, 0.0, 0.0


# The smith's hammer arm: (shoulder, elbow, wrist) at rest between blows, raised over his shoulder
# and landed on the billet; his tongs arm holding the billet on the anvil, and up to the light.
HAMMER_REST = (0.85, 0.5, -1.1)
HAMMER_TOP = (2.3, 0.75, -0.35)
HAMMER_LAND = (0.5, 0.5, -1.3)
TONGS_HOLD = (0.36, 0.1, -0.5)
TONGS_UP = (1.25, 0.95, -1.7)
SMITH_ROLL = (0.45, 0.45)  # how far the hammer arm and the tongs arm turn in toward the anvil


def _lerp3(a, b, k):
    return tuple(p + (q - p) * k for p, q in zip(a, b, strict=True))


def _smith_arm(side, t):
    stage, k = villagers.smith_cycle(t)
    roll = side * SMITH_ROLL[0 if side == 1 else 1]
    if side == 1:  # the hammer
        if stage == "strike":
            land = villagers.SMITH_LAND
            if k < 0.4:
                pose = _lerp3(HAMMER_REST, HAMMER_TOP, _ease(k / 0.4))
            elif k < land:
                pose = _lerp3(HAMMER_TOP, HAMMER_LAND, _ease_in((k - 0.4) / (land - 0.4)))
            elif k < 0.7:
                pose = HAMMER_LAND
            else:
                pose = _lerp3(HAMMER_LAND, HAMMER_REST, _ease((k - 0.7) / 0.3))
        elif stage == "wipe":  # the back of the wrist drawn across the brow, the hammer still in hand
            up = math.sin(k * math.pi)
            pose = _lerp3(HAMMER_REST, (2.0, 1.45, -0.2), _ease(min(up * 1.6, 1.0)))
            roll = SMITH_ROLL[0] + 0.5 * up + 0.25 * math.sin(k * math.tau * 2) * up
        else:  # resting the hammer while he works the billet
            pose = (0.35, 0.55, -0.5)
            if stage == "turn" and k > 0.85:
                pose = _lerp3(pose, HAMMER_REST, _ease((k - 0.85) / 0.15))
            if stage == "turn" and k < 0.15:
                pose = _lerp3(HAMMER_REST, pose, _ease(k / 0.15))
        sh, el, wrist = pose
        return sh, el, "hammer", roll, wrist
    if stage == "inspect":  # the billet raised to the light, then set back on the anvil
        up = _ease(min(k / 0.25, (1 - k) / 0.25, 1.0))
        sh, el, wrist = _lerp3(TONGS_HOLD, TONGS_UP, up)
        return sh, el, "tongs", roll * (1 - up), wrist
    if stage == "turn":  # lifted a hand's breadth, turned over, laid down again
        lift = math.sin(k * math.pi) * 0.25
        sh, el, wrist = TONGS_HOLD
        return sh + lift, el, "tongs", roll, wrist - lift
    sh, el, wrist = TONGS_HOLD
    return sh, el, "tongs", roll, wrist


def _ready_arm(side, t):
    """The swordmaster's arms: the left hand rests on the scabbard by its mouth, the thumb on the guard;
    the right hangs easy, coming across to the hilt as he eases a hand's width of steel out."""
    shown = villagers.half_draw(t) / villagers.DRAW_SHOWN
    if side == -1:
        return 0.38, 0.7, None, -0.34, 0.0
    near = min(shown * 3, 1.0) if shown > 0 else 0.0
    return 0.12 + 0.5 * near, 0.2 + 0.75 * near, None, 0.62 * near, 0.0


def _villager_tool(r, tool, t):
    """What a villager holds, in the hand's frame (the hand hangs down -Y, fingers forward +X)."""
    if tool == "hammer":  # held by the haft, head forward
        r.part("cube", 0.12, 0, 0, 0.34, 0.04, 0.04, TOOL_WOOD)
        r.part("cube", 0.3, 0, 0, 0.08, 0.1, 0.16, TOOL_IRON)
        r.part("cube", 0.3, -0.055, 0, 0.09, 0.02, 0.17, _dim(TOOL_IRON, 1.25))  # the worn face
    elif tool == "tongs":  # two long jaws, a glowing billet gripped at their tips
        stage, k = villagers.smith_cycle(t)
        turn = math.pi * _ease(k) if stage == "turn" else 0.0
        with r.at(0, 0, 0, rx=turn):
            for dz in (-0.018, 0.018):
                r.part("cube", 0.22, 0, dz, 0.46, 0.022, 0.016, (60, 58, 62), rx=dz * 3)
            r.part("cube", 0.04, 0, 0, 0.03, 0.03, 0.05, (60, 58, 62))  # the rivet
            heat = _billet_heat(t)
            hot = tuple(
                rround(c * heat + d * (1 - heat)) for c, d in zip((255, 190, 90), (90, 64, 54), strict=True)
            )
            r.part("cube", 0.47, 0, 0, 0.14, 0.035, 0.05, hot, glow=heat > 0.35)
    elif tool == "halberd":  # a long pole-arm stood upright: an axe blade, a back hook and a spike
        r.part("cube", 0, 0.55, 0, 0.045, 2.2, 0.045, TOOL_WOOD)
        r.part("cube", 0, -0.56, 0, 0.055, 0.06, 0.055, TOOL_IRON)  # the iron butt
        r.part("cube", 0, 1.42, 0, 0.06, 0.36, 0.06, _dim(TOOL_IRON, 0.85))  # the socket and langets
        r.part("lozenge", 0, 1.86, 0, 0.06, 0.34, 0.025, TOOL_IRON)  # the spike
        r.part("cube", 0.12, 1.5, 0, 0.2, 0.22, 0.016, TOOL_IRON)  # the axe blade
        r.part("cube", 0.225, 1.5, 0, 0.03, 0.3, 0.012, _dim(TOOL_IRON, 1.3))  # its bright edge
        r.part("cube", -0.08, 1.55, 0, 0.14, 0.035, 0.016, TOOL_IRON, rz=-0.35)  # the back hook
        r.part("cube", 0, 1.3, 0, 0.07, 0.04, 0.07, (120, 36, 32))  # a red tassel's knot
        r.part("cube", 0, 1.22, 0, 0.04, 0.12, 0.04, (110, 32, 30))
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


def _billet_heat(t):
    """How hot the smith's billet glows (0..1): white-hot out of the fire, dulling as he works it."""
    stage, k = villagers.smith_cycle(t)
    done = 0.0
    for name, d in villagers.SMITH_STAGES:
        if name == stage:
            break
        done += d
    elapsed = done + (k * d if stage != "strike" else (t % villagers.SMITH_LOOP))
    return 1.0 - 0.75 * elapsed / villagers.SMITH_LOOP


ANVIL_AT = 0.66  # metres before the smith that his anvil stands
ANVIL_TOP = 0.8  # the height of its face
ANVIL_IRON = (64, 62, 68)
STUMP = (98, 72, 48)


def _smith_anvil(r, t):
    """The smith's anvil before him on its stump: a waisted body, a broad face, a tapering horn toward
    his left and a square heel; sparks fly from it as each blow lands."""
    with r.at(ANVIL_AT, 0, 0):
        r.part("frustum", 0, 0.24, 0, 0.5, 0.48, 0.5, STUMP)  # the stump
        r.part("frustum", 0, 0.49, 0, 0.52, 0.03, 0.52, _dim(STUMP, 0.75))  # its cut ring
        r.part("cube", 0, 0.56, 0, 0.3, 0.12, 0.42, ANVIL_IRON)  # the foot
        r.part("cube", 0, 0.7, 0, 0.18, 0.18, 0.26, _dim(ANVIL_IRON, 0.9))  # the waist
        r.part("cube", 0, ANVIL_TOP - 0.05, 0, 0.26, 0.1, 0.46, ANVIL_IRON)  # the face's block
        r.part("cube", 0, ANVIL_TOP - 0.003, 0, 0.24, 0.006, 0.44, _dim(ANVIL_IRON, 1.5))  # the worn face
        r.part("wedge", 0, ANVIL_TOP - 0.05, -0.36, 0.14, 0.26, 0.09, ANVIL_IRON, rx=-math.pi / 2)  # horn
        r.part("cube", 0, ANVIL_TOP - 0.04, 0.27, 0.2, 0.08, 0.08, ANVIL_IRON)  # heel
        r.part("cube", 0.05, ANVIL_TOP - 0.001, 0.18, 0.04, 0.004, 0.04, (24, 22, 24))  # the hardy hole
    stage, k = villagers.smith_cycle(t)
    land = villagers.SMITH_LAND
    if stage != "strike" or not land <= k < land + 0.3:
        return
    s = (k - land) / 0.3
    for i in range(6):  # sparks thrown off the billet
        a = i * 1.9 + 0.4
        out = 0.12 + 0.5 * s * (0.7 + 0.3 * math.sin(i * 3.1))
        y = ANVIL_TOP + 0.05 + s * 0.45 * (1 + 0.3 * math.cos(i)) - s * s * 0.6
        size = 0.03 * (1 - s) + 0.008
        r.part("cube", ANVIL_AT + math.cos(a) * out * 0.7, y, math.sin(a) * out, size, size, size,
               (255, rround(230 - 90 * s), rround(140 - 100 * s)), glow=True)  # fmt: skip


def _hip_blades(r, look, ws, t):
    """A katana and a shorter wakizashi thrust through the obi on the left hip, hilts forward and up,
    scabbards sloping back and down; a hand's width of the long blade shows as he half-draws it."""
    w = _chest_width(ws)
    shown = villagers.half_draw(t)
    saya, wrap, tsuba = (34, 30, 36), (210, 204, 190), (70, 64, 50)
    for z, length, grip, drop, drawn in (
        (-w / 2 - 0.05, 0.78, 0.26, 0.42, shown),
        (-w / 2 - 0.0, 0.5, 0.18, 0.3, 0.0),
    ):
        with r.at(0.06, 0.06, z, rz=drop):
            r.part("cube", -length / 2, 0, 0, length, 0.05, 0.04, saya)  # the scabbard
            r.part("cube", -0.02, 0, 0, 0.04, 0.056, 0.046, _dim(saya, 1.6))  # its mouth
            r.part("cube", -length + 0.03, 0, 0, 0.06, 0.054, 0.044, _dim(saya, 1.6))  # its tip
            if drawn:
                r.part("cube", drawn / 2, 0.004, 0, drawn, 0.034, 0.012, (212, 214, 224))  # bare steel
            with r.at(drawn, 0, 0):
                r.part("cube", 0.01, 0, 0, 0.02, 0.09, 0.09, tsuba)  # the guard
                r.part("cube", 0.02 + grip / 2, 0, 0, grip, 0.045, 0.04, (30, 26, 30))  # the grip
                for k in range(int(grip / 0.05)):  # its wrapped cord's diamonds
                    r.part("cube", 0.045 + k * 0.05, 0, 0, 0.02, 0.05, 0.044, wrap)
                r.part("cube", 0.03 + grip, 0, 0, 0.02, 0.05, 0.046, tsuba)  # the pommel cap


def _villager_head(r, look, t=0.0):
    """An angular, faceless head on the collar: a faceted skull narrowing to the chin, a flat face
    with only a brow and a nose (no eyes or mouth), block ears, block hair, and a short neck sunk
    into the chest so no gap opens between head and body."""
    skin = look.skin
    r.part("frustum", 0, -0.02, 0, 0.13, 0.14, 0.13, skin)  # neck, from inside the chest
    r.part("frustum", 0, 0.17, 0, 0.24, 0.3, 0.22, skin, rz=FLIP)  # the skull, narrowing to the chin
    r.part("cube", 0.1, 0.15, 0, 0.03, 0.2, 0.14, _dim(skin, 0.97))  # the flat face
    r.part("cube", 0.115, 0.22, 0, 0.04, 0.035, 0.17, _dim(skin, 0.86))  # the brow
    r.part("wedge", 0.13, 0.15, 0, 0.05, 0.08, 0.04, _dim(skin, 0.92))  # nose
    for side in (-1, 1):
        r.part("cube", 0, 0.17, side * 0.115, 0.06, 0.08, 0.03, _dim(skin, 0.9))  # ears
    if look.beard == "short":  # a block of beard falling from the jaw over the chest
        r.part("cube", 0.09, 0.04, 0, 0.1, 0.18, 0.2, look.hair)
        r.part("cube", 0.12, -0.09, 0, 0.08, 0.16, 0.16, _dim(look.hair, 0.94))
    elif look.beard == "long":
        _long_beard(r, look, t)
    hood = look.cloak or look.cloth
    if look.hood:  # a deep cowl over the head and shoulders, the face in its mouth
        r.part("frustum", -0.05, 0.15, 0, 0.36, 0.46, 0.36, hood)
        r.part("cube", -0.06, -0.02, 0, 0.26, 0.12, 0.44, hood)
        return
    style = look.hair_style
    if style == "bald":
        r.part("cube", -0.01, 0.325, 0, 0.22, 0.03, 0.2, _dim(skin, 0.95))  # a bare pate
    elif style == "topknot":  # swept back from a high brow and tied in a knot on the crown
        r.part("cube", -0.05, 0.31, 0, 0.21, 0.07, 0.25, look.hair)  # swept back over the top
        r.part("cube", -0.115, 0.19, 0, 0.06, 0.24, 0.25, look.hair)  # down the back
        for side in (-1, 1):  # wild locks over the temples, falling past the ears
            r.part("cube", -0.03, 0.2, side * 0.125, 0.16, 0.22, 0.035, look.hair, rx=side * 0.12)
            r.part("cube", -0.09, 0.02, side * 0.12, 0.08, 0.22, 0.04, _dim(look.hair, 0.92), rx=side * 0.2)
        r.part("cube", -0.06, 0.37, 0, 0.07, 0.05, 0.07, _dim(look.hair, 0.7))  # the tie
        r.part("cube", -0.12, 0.4, 0, 0.12, 0.05, 0.06, look.hair, rz=0.3)  # the knot's tuft, swept back
        r.part("cube", -0.15, 0.03, 0, 0.06, 0.34, 0.2, _dim(look.hair, 0.95), rz=-0.1)  # a mane behind
    else:
        r.part("cube", -0.02, 0.31, 0, 0.27, 0.08, 0.26, look.hair)  # a block of hair over the top
        r.part("cube", -0.11, 0.2, 0, 0.06, 0.2, 0.25, look.hair)  # down the back
        r.part("cube", 0.11, 0.28, 0, 0.04, 0.05, 0.22, _dim(look.hair, 0.92))  # the fringe
    if style == "long":
        r.part("cube", -0.12, 0.06, 0, 0.08, 0.36, 0.26, look.hair)
    elif style == "bun":
        r.part("cube", -0.15, 0.32, 0, 0.1, 0.1, 0.1, look.hair)
    if look.hat == "brim":
        r.part("frustum", 0, 0.35, 0, 0.46, 0.04, 0.46, look.hat_rgb)
        r.part("frustum", 0, 0.44, 0, 0.26, 0.16, 0.26, look.hat_rgb)
    elif look.hat == "cap":  # a squat skullcap on a band
        r.part("frustum", -0.01, 0.37, 0, 0.29, 0.12, 0.28, look.hat_rgb)
        r.part("cube", -0.01, 0.315, 0, 0.29, 0.04, 0.28, _dim(look.hat_rgb, 0.7))
    elif look.hat == "coif":  # a mail coif over the head and neck
        r.part("cube", -0.04, 0.2, 0, 0.27, 0.32, 0.28, look.hat_rgb)
        r.part("cube", -0.05, -0.02, 0, 0.2, 0.12, 0.32, look.hat_rgb)
    elif look.hat == "helm":  # a kettle helm: a raised crown and a broad brim, over a mail coif
        mail = _dim(look.hat_rgb, 0.8)
        r.part("cube", -0.04, 0.17, 0, 0.27, 0.28, 0.28, mail)  # the coif round the face
        r.part("cube", -0.05, -0.02, 0, 0.2, 0.12, 0.32, mail)  # falling over the neck
        r.part("frustum", -0.01, 0.42, 0, 0.3, 0.16, 0.3, look.hat_rgb)  # the crown
        r.part("cube", -0.01, 0.5, 0, 0.2, 0.025, 0.035, _dim(look.hat_rgb, 1.2))  # its comb
        r.part("frustum", -0.01, 0.335, 0, 0.5, 0.04, 0.5, _dim(look.hat_rgb, 0.92))  # the brim
        r.part("cube", -0.01, 0.36, 0, 0.31, 0.03, 0.31, _dim(look.hat_rgb, 0.7))  # the band


LONG_BEARD_TIERS = (  # (x, y, height, width, depth): blocks narrowing down the chest to the belt
    (0.1, 0.03, 0.2, 0.22, 0.1),
    (0.14, -0.15, 0.2, 0.18, 0.08),
    (0.155, -0.33, 0.2, 0.13, 0.07),
)
BEARD_RING = (130, 124, 116)


def _long_beard(r, look, t):
    """A long beard in the head's frame: a drooping moustache, then tiers that narrow down over the
    chest to the belt, stirring a little, its tip bound in an iron ring (and greying, if `beard_tip`)."""
    hair, tip = look.hair, look.beard_tip or look.hair
    for side in (-1, 1):  # the moustache, drooping past the corners of the mouth
        r.part("cube", 0.13, 0.095, side * 0.045, 0.04, 0.035, 0.07, hair, rx=side * 0.3)
        r.part("cube", 0.135, 0.04, side * 0.085, 0.035, 0.1, 0.03, _dim(hair, 0.94))
    stir = math.sin(t * 1.1) * 0.025
    with r.at(0, 0.1, 0, rz=stir):
        for i, (x, y, h, w, d) in enumerate(LONG_BEARD_TIERS):
            rgb = tuple(rround(a + (b - a) * i / 2) for a, b in zip(hair, tip, strict=True))
            r.part("cube", x, y - 0.1, 0, d, h, w, rgb)
            r.part("cube", x + d / 2, y - 0.1, w * 0.18, 0.006, h * 0.9, 0.02, _dim(rgb, 0.85))  # a strand
        r.part("cube", 0.155, -0.53, 0, 0.08, 0.04, 0.1, BEARD_RING)  # the binding ring
        r.part("wedge", 0.155, -0.6, 0, 0.06, 0.1, 0.08, tip, rz=math.pi)  # the tip below it


THRONE_STONE = (118, 114, 108)
THRONE_CUSHION = (92, 34, 40)


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


PETRIFIED = (146, 141, 132)  # the Enthroned's stone: a shade paler than the throne it grew into
PETRIFIED_SHADE = _dim(PETRIFIED, 0.78)
CRACK = (48, 46, 44)
LICHEN = (132, 140, 92)
SETTLED_DUST = (168, 162, 150)
DUST_MOTE = (200, 196, 180)


def enthroned(r, t):
    """The Enthroned: an ancient, gaunt figure far taller than a man, turned to stone where it sat on
    the cathedral throne, facing +X. Grey robes pool down the dais in stiff folds, long bony hands lie
    on the arms, and a crown of spikes (two broken) rises over a cowled, faceless head. Built square
    and blocky like the villagers, a broad flat mantle over its shoulders. Cracks
    run through it, lichen and moss creep up from the dais, and dust lies on every ledge. Only the dust
    drifting through the light moves."""
    # The moon's keeping: when his sister wed the moon on the fourth sigil it kept him as he sat, in
    # stone, and he still listens from inside it (`dialogue.ENTHRONED_LINES`).
    throne(r)
    robe, under, skin = PETRIFIED, PETRIFIED_SHADE, _dim(PETRIFIED, 1.06)
    with r.at(-0.2, 1.0, 0):  # the seat
        # Legs: thighs along the seat, shins down the dais, robes pooling over them.
        for side in (-1, 1):
            r.part("cube", 0.3, 0.12, side * 0.2, 0.75, 0.2, 0.22, robe, tex="rough_stone")
            r.part("cube", 0.66, -0.35, side * 0.22, 0.2, 0.85, 0.2, under, tex="rough_stone")
            r.part("cube", 0.74, -0.72, side * 0.22, 0.32, 0.1, 0.16, under)  # feet
            r.part("cube", 0.3, 0.23, side * 0.2, 0.6, 0.02, 0.18, SETTLED_DUST)  # dust on the lap
        r.part("cube", 0.75, -0.45, 0, 0.12, 0.95, 0.75, robe, tex="rough_stone")  # the robe's fall
        r.part("wedge", 1.0, -0.8, 0, 0.5, 0.25, 0.95, under, rz=math.pi / 2, tex="rough_stone")  # hem
        for i in range(4):  # stiff folds in the stone robe
            r.part("cube", 0.82, -0.4, -0.27 + i * 0.18, 0.03, 0.85, 0.04, under)
        for z, h in ((-0.3, 0.3), (0.1, 0.22), (0.32, 0.36)):  # lichen and moss creeping up the hem
            r.part("cube", 0.83, -0.82 + h / 2, z, 0.02, h, 0.12, LICHEN)
            r.part("cube", 1.05, -0.84, z, 0.2, 0.04, 0.16, MOSS)
        r.part("cube", 0.82, -0.3, 0.05, 0.01, 0.5, 0.02, CRACK, rx=0.4)  # a crack down the robe
        # Torso: long and narrow, leaning back into the throne, a chain of office over the chest.
        with r.at(-0.15, 0.25, 0, rz=0.08):
            r.part("cube", 0, 0.55, 0, 0.36, 1.1, 0.62, robe)
            r.part("cube", 0.03, 0.98, 0, 0.42, 0.22, 1.04, _dim(robe, 1.08))  # a square mantle
            r.part("cube", 0.03, 1.095, 0, 0.38, 0.015, 1.0, SETTLED_DUST)  # dust on the shoulders
            r.part("cube", -0.12, 0.45, 0, 0.14, 1.0, 0.7, under)  # its back
            for i in range(5):  # the chain of office, stone like the rest
                a = (i - 2) * 0.32
                r.part("cube", 0.19, 0.78 - abs(a) * 0.5, a * 0.6, 0.03, 0.06, 0.08, under)
            r.part("cube", 0.2, 0.55, 0, 0.03, 0.14, 0.12, under)  # its pendant
            r.part("cube", 0.215, 0.55, 0, 0.01, 0.06, 0.04, CRACK)  # the gem, gone dull and dark
            # A crack splitting the chest from the collar down past the pendant.
            for k, (y, z, rx) in enumerate(((0.9, 0.08, 0.5), (0.72, 0.02, -0.4), (0.45, 0.06, 0.3))):
                r.part("cube", 0.185, y, z, 0.01, 0.2 - 0.03 * k, 0.018, CRACK, rx=rx)
            # Arms hanging from the shoulders to the throne's arms, forearms laid along them and long
            # bony hands drooping over the carved scrolls.
            for side in (-1, 1):
                with r.at(0, 0.94, side * 0.4, rx=-side * 0.06), r.at(0, 0, 0, rz=0.12):
                    r.part("cube", 0, -0.45, 0, 0.17, 0.9, 0.17, robe, tex="rough_stone")
                    with r.at(0, -0.88, 0, rz=1.5):
                        r.part("cube", 0, -0.32, 0, 0.15, 0.64, 0.15, robe)
                        r.part("cube", 0.076, -0.32, 0, 0.01, 0.5, 0.02, SETTLED_DUST)  # dust along it
                        r.part("cube", 0, -0.62, 0, 0.2, 0.08, 0.2, under)  # cuff
                        if side == 1:  # a crack ringing one forearm
                            r.part("cube", 0, -0.45, 0, 0.16, 0.012, 0.16, CRACK)
                        with r.at(0, -0.68, 0, rz=-1.3):
                            _mitt(r, skin, size=0.17, length=1.4)  # long, drooping over the scroll
            # Head: long, gaunt and faceless under a square-browed cowl, and the spiked crown.
            with r.at(0.04, 1.2, 0, rz=0.12):
                r.part("cube", 0, 0.05, 0, 0.12, 0.16, 0.14, skin)  # neck
                r.part("frustum", 0, 0.33, 0, 0.3, 0.46, 0.28, skin, rz=FLIP)  # the skull, to a long chin
                r.part("cube", 0.12, 0.2, 0, 0.08, 0.14, 0.14, _dim(skin, 0.9))  # long jaw
                r.part("cube", 0.125, 0.34, 0, 0.03, 0.3, 0.17, _dim(skin, 0.96))  # the flat face
                r.part("cube", 0.14, 0.44, 0, 0.04, 0.04, 0.2, _dim(skin, 0.86))  # the brow
                r.part("wedge", 0.16, 0.35, 0, 0.06, 0.12, 0.05, _dim(skin, 0.92))  # nose
                r.part("frustum", -0.1, 0.38, 0, 0.44, 0.6, 0.44, under)  # the cowl, framing the face
                r.part("cube", 0.05, 0.6, 0, 0.3, 0.06, 0.4, robe)  # its brim
                r.part("cube", 0.05, 0.635, 0, 0.26, 0.012, 0.36, SETTLED_DUST)
                r.part("frustum", -0.02, 0.66, 0, 0.36, 0.08, 0.36, under, rz=FLIP)  # crown band
                for i in range(7):  # stone spikes, tallest at the front; two have snapped off
                    a = (i - 3) * 0.42
                    h = (0.5 - abs(i - 3) * 0.07) * (0.4 if i in (1, 5) else 1.0)
                    r.part(
                        "cone", -0.02 + math.cos(a) * 0.16, 0.7 + h / 2, math.sin(a) * 0.16,
                        0.06, h, 0.06, under,
                    )  # fmt: skip
    for x, z in ((0.85, -0.6), (1.15, 0.5), (0.6, 0.75)):  # chips of stone fallen on the dais
        r.part("cube", x, 0.27, z, 0.08, 0.05, 0.06, under, ry=x * 3)
    for i in range(10):  # dust drifting through the light about the throne
        u = (t * 0.05 + i / 10) % 1.0
        r.part(
            "cube", 0.6 + math.sin(i * 2.3 + t * 0.2) * 0.8, 0.5 + 3.5 * u, math.sin(i * 1.7) * 1.0,
            0.03, 0.03, 0.03, DUST_MOTE, glow=True,
        )  # fmt: skip


IRON_CHEST = (150, 146, 156)  # tint over the iron plate of an iron chest
IRON_CHEST_BAND = (52, 50, 56)
WORN_WOOD = (168, 158, 146)  # tint over the planks of a worn chest: weathered grey
BANDED_WOOD = (140, 112, 96)  # dark-stained
COFFER_WOOD = (196, 150, 118)  # warm, oiled
CHEST_ROPE = (150, 128, 88)
CHEST_BRASS = (178, 150, 82)
# A chest's look, chosen by its entity's `model=`: (tint over its planks, texture).
CHEST_SHELLS = {
    "wood": (WHITE, "wood_plank"),
    "iron": (IRON_CHEST, "iron_plate"),
    "worn": (WORN_WOOD, "wood_plank"),
    "banded": (BANDED_WOOD, "wood_plank"),
    "coffer": (COFFER_WOOD, "wood_plank"),
}


CHEST_WALL = 0.05  # how thick an open chest's planks show at its rim
CHEST_CLOTH = (150, 50, 44)  # the faded red cloth an open chest's floor is lined with


def chest(r, is_open, style="wood"):
    """A chest facing +X, its lid hinged at the back. `style` (see CHEST_SHELLS) picks its look: "wood"
    the plain one; "worn" weathered, roped shut, its lid cracked; "banded" dark wood strapped in iron
    with a ring pull; "coffer" a small brass-cornered strongbox on feet with a domed lid; "iron" the
    Cinderhold's: riveted black bands, corner brackets, iron feet, a rounded lid and a heavy hasp with
    an ember-lit keyhole. Shut, its body is one block; open, it is hollow (`_chest_body`), and the
    battens under its lid show."""
    shell, tex = CHEST_SHELLS.get(style, CHEST_SHELLS["wood"])
    if style in _CHEST_STYLES:
        _CHEST_STYLES[style](r, is_open, shell, tex)
        return
    if style != "iron":
        _chest_body(r, 0.6, 0.5, 0.9, 0.0, shell, tex, is_open)
        _belt(r, 0, 0.26, 0, 0.62, 0.06, 0.92, IRON, is_open)
        with r.at(-0.3, 0.5, 0, rz=1.9 if is_open else 0):
            r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, shell, tex=tex)
            if is_open:
                _lid_inside(r, 0.3, 0.6, 0.9, shell, tex)
        if not is_open:
            r.part("cube", 0.31, 0.42, 0, 0.04, 0.12, 0.1, (200, 170, 80))
        return
    _chest_body(r, 0.6, 0.46, 0.9, 0.06, shell, tex, is_open)
    for x, z in ((0.25, 0.4), (0.25, -0.4), (-0.25, 0.4), (-0.25, -0.4)):
        r.part("cube", x, 0.04, z, 0.14, 0.08, 0.14, IRON_CHEST_BAND)  # feet
        r.part("cube", x * 1.06, 0.29, z * 1.03, 0.06, 0.48, 0.06, IRON_CHEST_BAND)  # corner brackets
    for z in (-0.25, 0.25):  # bands over the front and back, riveted
        _belt(r, 0, 0.29, z, 0.63, 0.48, 0.07, IRON_CHEST_BAND, is_open)
        for y in (0.12, 0.29, 0.46):
            r.part("cube", 0.32, y, z, 0.02, 0.035, 0.035, RIVET_IRON)
    _belt(r, 0, 0.5, 0, 0.63, 0.05, 0.93, IRON_CHEST_BAND, is_open)  # the rim
    with r.at(-0.3, 0.52, 0, rz=1.9 if is_open else 0):
        r.part("cube", 0.3, 0.06, 0, 0.6, 0.12, 0.9, shell, tex=tex)
        r.part("cyl", 0.3, 0.12, 0, 0.58, 0.88, 0.2, shell, tex=tex, rx=math.pi / 2)  # the rounded top
        for z in (-0.25, 0.25):
            r.part("cyl", 0.3, 0.12, z, 0.62, 0.07, 0.24, IRON_CHEST_BAND)
        r.part("cube", 0.6, 0.0, 0, 0.04, 0.18, 0.14, IRON_CHEST_BAND)  # the hasp, hanging from the lid
        if is_open:
            _lid_inside(r, 0.3, 0.6, 0.9, shell, tex, strap=IRON_CHEST_BAND)
    if not is_open:
        r.part("cube", 0.315, 0.36, 0, 0.04, 0.16, 0.16, IRON)  # the lock plate
        r.part("cube", 0.34, 0.35, 0, 0.01, 0.06, 0.025, (200, 90, 30), glow=True)  # the keyhole


def _chest_body(r, w, h, d, y0, shell, tex, is_open, wall=CHEST_WALL):
    """A chest's body, `w` deep (x), `h` tall from `y0` and `d` wide (z), centred on the origin. Shut,
    a single block; open, a hollow box: a bottom and four plank walls `wall` thick, lined inside in
    darker wood, a batten round the inside of the rim and a crumpled cloth on the floor."""
    if not is_open:
        r.part("cube", 0, y0 + h / 2, 0, w, h, d, shell, tex=tex)
        return
    ym = y0 + h / 2
    iw, id_ = w - 2 * wall, d - 2 * wall
    r.part("cube", 0, y0 + wall / 2, 0, w, wall, d, shell, tex=tex)  # the bottom
    for side in (1, -1):
        r.part("cube", side * (w - wall) / 2, ym, 0, wall, h, d, shell, tex=tex)  # front and back
        r.part("cube", 0, ym, side * (d - wall) / 2, iw, h, wall, shell, tex=tex)  # the ends
    lining = _dim(shell, 0.45)
    inner_h = h - wall
    yi = y0 + wall + inner_h / 2
    r.part("cube", 0, y0 + wall + 0.004, 0, iw, 0.008, id_, lining, tex=tex)  # the floor's lining
    for side in (1, -1):  # the walls' lining, and a batten round the inside of the rim
        r.part("cube", side * (iw / 2 - 0.004), yi, 0, 0.008, inner_h, id_, lining, tex=tex)
        r.part("cube", 0, yi, side * (id_ / 2 - 0.004), iw, inner_h, 0.008, lining, tex=tex)
        r.part("cube", side * (iw / 2 - 0.015), y0 + h - 0.03, 0, 0.03, 0.03, id_, _dim(shell, 0.6), tex=tex)
    # The cloth the treasure lay on, crumpled into a few folds.
    cloth_y = y0 + wall + 0.02
    r.part("cube", -0.02 * w, cloth_y, 0, iw * 0.82, 0.04, id_ * 0.86, CHEST_CLOTH, ry=0.05)
    for k, z in enumerate((-0.25, 0.1, 0.3)):
        r.part("cube", (k - 1) * iw * 0.18, cloth_y + 0.035, z * id_, iw * 0.5, 0.04, 0.06,
               _dim(CHEST_CLOTH, 0.8), ry=0.4 * (k - 1))  # fmt: skip


def _belt(r, x, y, z, sx, sy, sz, rgb, is_open, t=0.035):
    """A band of iron (or rope) wrapped round a chest's body. Shut, a block just bigger than the body;
    open, only its outside shows: a belt thin in y runs round all four sides, a strap thin in z
    runs down the front, under the bottom and up the back, so neither fills the hollow."""
    if not is_open:
        r.part("cube", x, y, z, sx, sy, sz, rgb)
        return
    for side in (1, -1):
        r.part("cube", x + side * (sx - t) / 2, y, z, t, sy, sz, rgb)
    if sy <= min(sx, sz):  # a belt round the sides
        for side in (1, -1):
            r.part("cube", x, y, z + side * (sz - t) / 2, sx - 2 * t, sy, t, rgb)
    else:  # a strap round the front, bottom and back
        r.part("cube", x, y - sy / 2 + t / 2, z, sx - 2 * t, t, sz, rgb)


def _lid_inside(r, cx, w, d, shell, tex, strap=None):
    """The underside of an open lid (in the lid's frame, its underside at y=0): darker boards and two
    battens across them, or iron straps."""
    r.part("cube", cx, -0.004, 0, w * 0.88, 0.008, d * 0.9, _dim(shell, 0.5), tex=tex)
    for z in (-0.28 * d, 0.28 * d):
        r.part("cube", cx, -0.02, z, w * 0.8, 0.03, 0.06, strap or _dim(shell, 0.65), tex="white")


def _chest_worn(r, is_open, shell, tex):
    """Weathered planks gone grey, a corner of the lid split away, roped shut and pegged."""
    _chest_body(r, 0.6, 0.5, 0.9, 0.0, shell, tex, is_open, wall=0.045)
    r.part("cube", 0.0, 0.03, 0, 0.64, 0.06, 0.94, _dim(shell, 0.7), tex=tex)  # the warped skid
    for z in (-0.3, 0.3):  # rope lashings round the body
        _belt(r, 0, 0.3, z, 0.63, 0.04, 0.05, CHEST_ROPE, is_open, t=0.02)
    with r.at(-0.3, 0.5, 0, rz=1.9 if is_open else 0):
        r.part("cube", 0.3, 0.07, 0.05, 0.6, 0.14, 0.8, shell, tex=tex)  # a corner plank gone
        r.part("cube", 0.3, 0.07, -0.41, 0.36, 0.14, 0.08, shell, tex=tex, ry=0.05)
        r.part("cube", 0.3, 0.145, 0.1, 0.62, 0.01, 0.03, (40, 34, 28))  # the split along it
        r.part("cube", 0.61, 0.0, 0, 0.03, 0.12, 0.1, CHEST_ROPE)  # the loop of the rope
        if is_open:
            _lid_inside(r, 0.3, 0.6, 0.8, shell, tex)
    if not is_open:
        r.part("cube", 0.32, 0.42, 0, 0.05, 0.1, 0.04, (110, 86, 58))  # the peg through it


def _chest_banded(r, is_open, shell, tex):
    """Dark-stained wood strapped by three iron bands, studded, capped at the corners, with a heavy
    ring pull on the front."""
    _chest_body(r, 0.6, 0.5, 0.9, 0.0, shell, tex, is_open)
    for z in (-0.32, 0, 0.32):
        _belt(r, 0, 0.25, z, 0.63, 0.52, 0.06, DARK_IRON, is_open)
        r.part("cube", 0.32, 0.1, z, 0.02, 0.03, 0.03, RIVET_IRON)
    for x, z in ((0.28, 0.43), (0.28, -0.43), (-0.28, 0.43), (-0.28, -0.43)):
        r.part("cube", x, 0.06, z, 0.08, 0.12, 0.08, DARK_IRON)  # corner caps
    with r.at(-0.3, 0.5, 0, rz=1.9 if is_open else 0):
        r.part("cube", 0.3, 0.08, 0, 0.6, 0.16, 0.9, shell, tex=tex)
        for z in (-0.32, 0, 0.32):
            r.part("cube", 0.3, 0.08, z, 0.63, 0.18, 0.06, DARK_IRON)
        if is_open:
            _lid_inside(r, 0.3, 0.6, 0.9, shell, tex, strap=DARK_IRON)
    r.part("cyl", 0.33, 0.3, 0, 0.16, 0.025, 0.16, RIVET_IRON, rz=math.pi / 2)  # the ring pull
    r.part("cube", 0.315, 0.38, 0, 0.03, 0.08, 0.08, DARK_IRON)  # its boss
    if not is_open:
        r.part("cube", 0.32, 0.46, 0, 0.03, 0.1, 0.1, IRON)  # the hasp


def _chest_coffer(r, is_open, shell, tex):
    """A small strongbox on short feet: oiled wood, brass corners and a brass lock plate, a domed lid."""
    for x, z in ((0.17, 0.28), (0.17, -0.28), (-0.17, 0.28), (-0.17, -0.28)):
        r.part("sphere", x, 0.04, z, 0.08, 0.08, 0.08, CHEST_BRASS)  # feet
    _chest_body(r, 0.45, 0.36, 0.7, 0.06, shell, tex, is_open, wall=0.04)
    for x, z in ((0.22, 0.34), (0.22, -0.34), (-0.22, 0.34), (-0.22, -0.34)):
        r.part("cube", x, 0.24, z, 0.04, 0.38, 0.04, CHEST_BRASS)
    with r.at(-0.22, 0.42, 0, rz=1.9 if is_open else 0):
        r.part("cyl", 0.22, 0.02, 0, 0.44, 0.7, 0.2, shell, tex=tex, rx=math.pi / 2)  # the dome
        for z in (-0.33, 0.33):
            r.part("cyl", 0.22, 0.02, z, 0.46, 0.04, 0.22, CHEST_BRASS)
        if is_open:
            _lid_inside(r, 0.22, 0.44, 0.7, shell, tex, strap=CHEST_BRASS)
    if not is_open:
        r.part("cube", 0.235, 0.34, 0, 0.02, 0.12, 0.12, CHEST_BRASS)  # the lock plate
        r.part("cube", 0.25, 0.33, 0, 0.01, 0.05, 0.02, (30, 24, 20))  # its keyhole


_CHEST_STYLES = {"worn": _chest_worn, "banded": _chest_banded, "coffer": _chest_coffer}


DOOR_FRAME = (70, 64, 66)  # the dark dressed stone round an iron door
DOOR_FRAME_LIGHT = (88, 80, 80)


def door(r, open_t, axis, tex="door_wood", style="wood", frame=4.0):
    """Door slab spanning the tile; axis 'x' means it blocks movement along X. `style` "iron" is the
    Cinderhold's: a riveted iron leaf banded and studded, with a ring on each face, sliding up into a
    frame of dark stone (jambs and a lintel `frame` metres up, the passage's ceiling) that stays put."""
    lift = open_t * 2.4
    ry = 0 if axis == "x" else math.pi / 2
    with r.at(0, 0, 0, ry=ry):
        if style != "iron":
            r.part("cube", 0, 1.25 + lift, 0, 0.18, 2.5, 2.0, WHITE, tex=tex)
            return
        _iron_door_frame(r, frame)
        with r.at(0, lift, 0):
            r.part("cube", 0, 1.3, 0, 0.16, 2.6, 1.5, IRON_CHEST, tex="iron_plate")
            for side in (-1, 1):
                x = side * 0.09
                for y in (0.35, 1.3, 2.25):  # the bands, studded along their length
                    r.part("cube", x, y, 0, 0.02, 0.16, 1.52, IRON_CHEST_BAND)
                    for dz in (-0.6, -0.2, 0.2, 0.6):
                        r.part("cube", x + side * 0.015, y, dz, 0.02, 0.06, 0.06, RIVET_IRON)
                for dz in (-0.72, 0.72):  # the border stiles
                    r.part("cube", x, 1.3, dz, 0.02, 2.6, 0.08, IRON_CHEST_BAND)
                r.part(
                    "cyl", x + side * 0.03, 1.15, 0.35, 0.22, 0.03, 0.22, RIVET_IRON, rz=math.pi / 2
                )  # ring
                r.part("cube", x + side * 0.01, 1.35, 0.35, 0.03, 0.12, 0.12, IRON_CHEST_BAND)  # its boss


def _iron_door_frame(r, frame):
    """Jambs, a lintel and a threshold round an iron door, its masonry filling up to `frame`."""
    frame = max(frame, 3.0)
    for z in (-0.88, 0.88):
        r.part("cube", 0, frame / 2, z, 0.5, frame, 0.26, DOOR_FRAME, tex="black_brick")
        r.part("cube", 0, 0.2, z, 0.56, 0.4, 0.3, DOOR_FRAME_LIGHT)  # the jamb's plinth
    r.part("cube", 0, 2.75, 0, 0.56, 0.3, 2.0, DOOR_FRAME_LIGHT)  # the lintel
    r.part("cube", 0, 2.9, 0, 0.6, 0.22, 0.4, DOOR_FRAME)  # its keystone
    if frame > 2.9:
        r.part("cube", 0, (2.9 + frame) / 2, 0, 0.44, frame - 2.9, 1.6, DOOR_FRAME, tex="black_brick")
    r.part("cube", 0, 0.03, 0, 0.6, 0.06, 1.7, DOOR_FRAME_LIGHT)  # the threshold


BOSS_DOOR_WOOD = (92, 66, 46)
BOSS_DOOR_IRON = (54, 52, 58)
BOSS_DOOR_STONE = (104, 100, 96)
BLOOD = (110, 18, 16)
OLD_BLOOD = (70, 16, 14)
SILK = (226, 222, 210)
LOOM_GLOW = (150, 235, 140)


@dataclass(frozen=True)
class DoorStyle:
    """How one boss's great door looks: the leaves' wood and texture, the iron, the arch's stone and
    texture, and what burns on its jambs (`lamp`: "ember", "silk", "candle", "gargoyle", "lantern",
    "tallow", "moon" or "core")."""

    wood: tuple
    wood_tex: str
    iron: tuple
    stone: tuple
    stone_tex: str
    lamp: str


# Each boss's door, keyed by the boss's `dead_flag` (the door's `boss=`).
BOSS_DOORS = {
    # The Ashen Warden: charred, ash-grey oak cracked with embers, under a crowned keystone.
    "boss_dead": DoorStyle(
        (96, 82, 72), "door_wood", BOSS_DOOR_IRON, BOSS_DOOR_STONE, "rough_stone", "ember"
    ),
    # The Butcher: rough planks lashed with crude straps, running with blood, hung with hooks.
    "butcher_dead": DoorStyle(
        (104, 70, 48), "wood_plank", (66, 58, 54), (96, 88, 82), "rough_stone", "ember"
    ),
    # The Loom Mother: gnarled root-wood bound in silk, a cocoon over it, lit by pale green glow.
    "spider_dead": DoorStyle((88, 74, 56), "bark", (60, 66, 56), (92, 100, 86), "rough_stone", "silk"),
    # The twin gargoyles: black riveted iron in a cracked, ember-veined arch, a stone beast on each jamb.
    "gargoyles_dead": DoorStyle(
        (150, 146, 156), "iron_plate", (40, 38, 44), (78, 72, 72), "black_brick", "gargoyle"
    ),
    # The Ashen Sexton: grey, weathered grave-boards under a lintel of urns, candles on the jambs.
    "sexton_dead": DoorStyle(
        (118, 112, 106), "wood_plank", (58, 56, 60), (122, 118, 112), "rough_stone", "candle"
    ),
    # The Sodden Pall: the old sluice-boards of the deepest cistern, slimed green, in a sewer-brick arch,
    # drain-keepers' lanterns burning sickly green on the jambs.
    "pall_dead": DoorStyle((76, 82, 60), "wood_plank", (88, 62, 44), (100, 74, 62), "sewer_brick", "lantern"),
    # Mother Gnawl: rotten boards gnawed ragged at the foot, in a sewer-brick arch, a tallow-and-rag lamp
    # guttering smoky on each jamb while she lives.
    "matron_dead": DoorStyle((88, 74, 58), "wood_plank", (70, 60, 56), (92, 70, 60), "sewer_brick", "tallow"),
    # Duchess Ilvane: leaves of frosted moon-glass leaded in silver, in a moonstone arch crowned with a
    # crescent, cold moon-lanterns on the jambs.
    "duchess_dead": DoorStyle(
        (176, 190, 220), "moon_glass", (170, 176, 190), (150, 158, 176), "moonstone", "moon"
    ),
    # The Keystone: sun-bleached old timber in an arch of the drowned city's sandstone, a carved
    # keystone over it, braziers on the jambs burning with the teal mortar-light that animates it.
    "keystone_dead": DoorStyle(
        (120, 104, 82), "wood_plank", (78, 66, 56), (138, 120, 96), "sunken_brick", "core"
    ),
}
DEFAULT_DOOR = "boss_dead"


BOSS_DOOR_TOP = 3.3  # the top of a boss door's lintel: the fog left in its place stands this tall


def boss_door(r, open_t, axis, t, lit=True, boss=None):
    """The great double door before a boss's lair, spanning its tile, dressed for the boss behind it
    (BOSS_DOORS, by its `dead_flag`): two banded leaves between plain stone jambs under a flat lintel,
    a lamp (or a beast) on each jamb that burns while the boss lives, and one motif of its boss. The
    leaves swing apart (inward) as `open_t` runs to 1. Axis 'x' means it blocks movement along X."""
    key = boss if boss in BOSS_DOORS else DEFAULT_DOOR
    style = BOSS_DOORS[key]
    swing = _ease(min(open_t, 1.0)) * 1.45
    with r.at(0, 0, 0, ry=0 if axis == "x" else math.pi / 2):
        _door_frame(r, style, t, lit)
        DOOR_ARCHES[key](r, style, t, lit)
        for side in (-1, 1):
            with r.at(0, 0, side * 0.9, ry=side * swing), r.at(0, 0, -side * 0.45):
                r.part("cube", 0, 1.4, 0, 0.14, 2.8, 0.9, style.wood, tex=style.wood_tex)
                for face in (-1, 1):
                    for y in (0.5, 2.3):  # two iron bands across each face
                        r.part("cube", face * 0.08, y, 0, 0.03, 0.14, 0.9, style.iron)
                    DOOR_LEAVES[key](r, style, side, face, t, lit)


def _door_frame(r, style, t, lit):
    """Two square jambs and a flat lintel over them, a lamp (or a beast) on each jamb's faces."""
    for side in (-1, 1):
        r.part("cube", 0, 1.4, side * 1.0, 0.44, 2.8, 0.2, style.stone, tex=style.stone_tex)
        for face in (-1, 1):
            with r.at(face * 0.28, 2.1, side * 0.9):
                _door_lamp(r, style, face, t + side + face, lit)
    r.part("cube", 0, 3.05, 0, 0.5, 0.5, 2.2, _dim(style.stone, 1.1), tex=style.stone_tex)  # the lintel


def _door_lamp(r, style, face, t, lit):
    if style.lamp == "gargoyle":  # a squatting stone beast, its eyes kindled
        stone = _dim(style.stone, 1.2)
        r.part("sphere", face * 0.02, 0.1, 0, 0.16, 0.18, 0.15, stone)  # hunched body
        r.part("sphere", face * 0.08, 0.24, 0, 0.11, 0.1, 0.1, stone)  # head, thrust out
        for dz in (-1, 1):
            r.part(
                "cube", face * 0.13, 0.26, dz * 0.03, 0.02, 0.02, 0.02, EMBER if lit else COLD_EMBER, glow=lit
            )
        return
    r.part("cube", 0, 0, 0, 0.12, 0.16, 0.12, style.iron)
    if not lit:
        return
    if style.lamp == "silk":  # a glowing bulb of fungus in a cup of silk
        r.part("sphere", 0, 0.14, 0, 0.12, 0.14, 0.12, LOOM_GLOW, glow=True)
    elif style.lamp == "lantern":  # a drain-keeper's lantern, its flame burned bile-green
        r.part("cube", 0, 0.16, 0, 0.1, 0.14, 0.1, (150, 190, 60), glow=True)
        r.part("cube", 0, 0.25, 0, 0.14, 0.03, 0.14, style.iron)
    elif style.lamp == "moon":  # moonlight caught in a silver cage: a pale, cold, unflickering glow
        r.part("sphere", 0, 0.17, 0, 0.11, 0.13, 0.11, (200, 220, 255), glow=True)
        r.part("cone", 0, 0.3, 0, 0.12, 0.08, 0.12, style.iron)
    elif style.lamp == "tallow":  # a lump of tallow with a rag for a wick, burning low and smoky
        flicker = 1 + 0.15 * math.sin(t * 9 + face)
        r.part("sphere", 0, 0.14, 0, 0.11, 0.1 * flicker, 0.11, (236, 170, 70), glow=True)
        u = (t * 0.5) % 1.0  # a curl of its smoke, rising and thinning
        r.part("cube", 0.02 * math.sin(t * 2), 0.28 + 0.35 * u, 0, 0.04 * (1 - u) + 0.01, 0.06,
               0.04 * (1 - u) + 0.01, (60, 56, 52))  # fmt: skip
    elif style.lamp == "core":  # a brazier of the mortar-light: a cold teal flame over a lozenge of it
        teal = sunken_models.CORE_TEAL
        r.part("cyl", 0, 0.1, 0, 0.16, 0.05, 0.16, style.iron)  # the brazier's bowl
        r.part("lozenge", 0, 0.2, 0, 0.08, 0.14, 0.08, sunken_models.CORE_HEART, glow=True, ry=t)
        flicker = 1 + 0.12 * math.sin(t * 7 + face)
        r.part("cone", 0, 0.28, 0, 0.13, 0.2 * flicker, 0.13, teal, glow=True)
    elif style.lamp == "candle":  # a stub of tallow, guttering
        r.part("cyl", 0, 0.14, 0, 0.06, 0.14, 0.06, (214, 204, 180))
        _flame(r, 0, 0.24, 0, 0.05, t)
    else:
        _flame(r, 0, 0.14, 0, 0.08, t)


def _warden_arch(r, style, t, lit):
    """A small crown on the lintel, an ember set in each of its faces."""
    bright = _dim(style.stone, 1.25)
    r.part("cube", 0, 3.34, 0, 0.3, 0.08, 0.46, bright)  # its band
    for dz in (-0.16, 0.0, 0.16):  # the crown's three points
        r.part("cone", 0, 3.44 + (0.05 if dz == 0 else 0), dz, 0.1, 0.16, 0.1, bright)
    for face in (-1, 1):
        ember = EMBER if lit else COLD_EMBER
        r.part("cube", face * 0.26, 3.05, 0, 0.02, 0.14, 0.14, ember, rx=math.pi / 4, glow=lit)


def _warden_leaf(r, style, side, face, t, lit):
    """Charred oak with an ember glowing in a crack of its grain."""
    crack = EMBER if lit else (40, 34, 30)
    r.part("cube", face * 0.085, 1.45, side * 0.1, 0.02, 0.6, 0.03, crack, rx=0.35 * side, glow=lit)


def _butcher_arch(r, style, t, lit):
    """A meat hook on a chain from the lintel's middle, and blood pooled across the threshold."""
    for face in (-1, 1):
        sway = math.sin(t * 0.8 + face) * 0.06
        with r.at(face * 0.27, 2.8, 0, rx=sway):
            r.part("cube", 0, -0.18, 0, 0.025, 0.36, 0.05, IRON)  # the chain
            r.part("cube", 0, -0.42, 0.03, 0.03, 0.14, 0.03, DARK_IRON)  # the hook's shank
            r.part("cube", 0, -0.49, -0.01, 0.03, 0.03, 0.1, DARK_IRON)  # and its curl
    r.part("cube", 0, 0.01, 0, 1.3, 0.02, 1.5, OLD_BLOOD)  # the pool across the threshold


def _butcher_leaf(r, style, side, face, t, lit):
    """Rough planks run with blood, the cleaver left driven into one leaf."""
    k = 1 + 0.06 * math.sin(t * 0.5 + side + face)  # blood runs down from a smear
    r.part("cube", face * 0.085, 2.0 - 0.6 * k, -side * 0.15, 0.02, 1.2 * k, 0.04, BLOOD)
    if side > 0 and face > 0:  # the cleaver, buried in the wood
        with r.at(0.13, 1.7, 0.1, rx=0.5, rz=math.pi / 2):
            r.part("cube", 0, 0.25, 0, 0.36, 0.06, 0.06, LEATHER)  # handle, standing out from the leaf
            r.part("cube", 0, 0.04, 0, 0.42, 0.06, 0.25, CLEAVER)  # what shows of the blade


def _loom_arch(r, style, t, lit):
    """A cocoon hung from the lintel on its thread, a shape pressing through it."""
    sway = math.sin(t * 0.6) * 0.06
    with r.at(0, 2.8, 0, rx=sway):
        r.part("cube", 0, -0.08, 0, 0.015, 0.16, 0.015, SILK)  # its thread
        r.part("sphere", 0, -0.42, 0, 0.3, 0.5, 0.28, SILK)
        r.part("sphere", 0.06, -0.34, 0.05, 0.08, 0.1, 0.08, (90, 70, 60))


def _loom_leaf(r, style, side, face, t, lit):
    """Gnarled root-wood with a sheet of silk wound round it."""
    r.part("cube", face * 0.085, 1.4, 0, 0.02, 0.36, 0.92, SILK, rx=0.25 * side)


def _gargoyle_arch(r, style, t, lit):
    """Cracks run down the black stone of the jambs, molten while the twins live."""
    vein = EMBER if lit else COLD_EMBER
    for face in (-1, 1):
        for side in (-1, 1):
            r.part("cube", face * 0.225, 1.0, side * 1.0, 0.02, 0.9, 0.03, vein, rx=0.2 * side, glow=lit)


def _gargoyle_leaf(r, style, side, face, t, lit):
    """Black iron plates with a wing spread in relief across each pair."""
    dark = _dim(style.iron, 0.8)
    with r.at(face * 0.09, 1.45, -side * 0.38):  # the wing, spreading toward the hinge
        for a in (0.4, 1.0):  # its finger-ribs
            r.part(
                "cube", 0, math.cos(a) * 0.3, side * math.sin(a) * 0.3, 0.03, 0.6, 0.03, dark, rx=-side * a
            )
        r.part("cube", 0, -0.05, side * 0.3, 0.02, 0.35, 0.45, _dim(style.iron, 1.3), rx=side * 0.3)


def _sexton_arch(r, style, t, lit):
    """Two funeral urns on the lintel, and a bell carved in its faces whose clapper glows while the
    Sexton keeps its gate."""
    for z in (-0.7, 0.7):
        r.part("sphere", 0, 3.48, z, 0.18, 0.24, 0.18, (132, 104, 80))
    for face in (-1, 1):
        with r.at(face * 0.27, 3.08, 0):
            r.part("cone", 0, 0, 0, 0.18, 0.2, 0.18, _dim(style.stone, 1.2))
            r.part("sphere", 0, -0.12, 0, 0.05, 0.05, 0.05, EMBER if lit else COLD_EMBER, glow=lit)


def _sexton_leaf(r, style, side, face, t, lit):
    """Grey grave-boards with names scratched into them, one under another: the Ashen who came this
    way before."""
    for k in range(3):
        r.part("cube", face * 0.085, 1.75 - k * 0.25, -side * 0.08, 0.02, 0.03, 0.5 - 0.06 * k,
               _dim(style.wood, 0.5 + 0.08 * k))  # fmt: skip


def _pall_arch(r, style, t, lit):
    """A curtain of the Pall's green ooze drooping over the lintel in lobes, drips stretching off its
    hem and falling; it glows faintly from within while the Pall lives."""
    ooze = (70, 130, 48) if lit else (52, 78, 40)
    for face in (-1, 1):
        with r.at(face * 0.24, 3.2, 0):
            r.part("cube", 0, 0.12, 0, 0.1, 0.22, 1.9, _dim(ooze, 0.8))  # the ooze along the lintel
            for i in range(5):  # its lobes, hanging down
                z = -0.8 + i * 0.4
                hang = 0.3 + 0.12 * ((i * 7) % 3) + 0.03 * math.sin(t * 1.5 + i)
                r.part("sphere", 0, -hang / 2 + 0.05, z, 0.12, hang, 0.3, _dim(ooze, 0.95 + 0.05 * (i % 2)))
            for i in range(2):  # drips stretching off its hem and falling
                u = (t * 0.6 + i * 0.5 + face * 0.25) % 1.0
                z = -0.4 + i * 0.8
                r.part("sphere", 0, -0.5 - 1.2 * u, z, 0.05, 0.08 + 0.06 * (1 - u), 0.05, ooze)
            if lit:
                r.part("sphere", 0, 0.02, 0, 0.06, 0.12, 0.9, (150, 220, 110), glow=True)  # its glow within


def _pall_leaf(r, style, side, face, t, lit):
    """Old sluice-boards slimed green to the tide line, an iron ring to haul them by."""
    r.part("cube", face * 0.085, 0.45, 0, 0.02, 0.9, 0.92, (58, 82, 40))  # the slime below the tide line
    r.part("cube", face * 0.1, 1.5, -side * 0.25, 0.03, 0.16, 0.16, style.iron, rx=math.pi / 4)  # the ring


RAT_BONE = (196, 184, 156)


def _matron_arch(r, style, t, lit):
    """A tuft of her nest, rags and straw, stuffed along the lintel, gnawed long bones jutting out of it."""
    for face in (-1, 1):
        with r.at(face * 0.27, 3.32, 0):
            for z in (-0.6, -0.15, 0.3, 0.7):
                r.part("sphere", 0, 0, z, 0.14, 0.1, 0.24, (96, 84, 62) if z < 0 else (120, 104, 70))
            for z, tilt in ((-0.4, 0.5), (0.5, -0.35)):  # a gnawed bone, its knuckle end sticking out
                r.part("cube", face * 0.03, -0.02, z, 0.04, 0.04, 0.42, RAT_BONE, rx=tilt)
                r.part("sphere", face * 0.03, -0.02 - 0.2 * math.sin(tilt), z + 0.2 * math.cos(tilt),
                       0.07, 0.06, 0.07, _dim(RAT_BONE, 0.9))  # fmt: skip


def _matron_leaf(r, style, side, face, t, lit):
    """The boards gnawed ragged along their foot, the gaps dark."""
    for i in range(2):
        z = (-0.2 + i * 0.4) * side
        r.part(
            "cube", face * 0.085, 0.08 + 0.04 * (i % 2), z, 0.02, 0.16 + 0.06 * (i % 2), 0.16, PASSAGE_DARK
        )


def _duchess_arch(r, style, t, lit):
    """A crescent moon of silver over the lintel, horns up, a pale stone set in its hollow that shines
    while she lives; frost creeping down the jambs from it."""
    silver = _dim(style.iron, 1.15)
    with r.at(0, 3.55, 0):
        for i in range(7):  # the crescent, a bowed run of silver
            a = math.pi * (0.1 + 0.8 * i / 6)
            r.part("cube", 0, -math.sin(a) * 0.26, math.cos(a) * 0.36, 0.08, 0.09, 0.12, silver,
                   rx=a - math.pi / 2)  # fmt: skip
        r.part("sphere", 0, 0.02, 0, 0.1, 0.1, 0.1, (210, 228, 255) if lit else COLD_EMBER, glow=lit)
    for face in (-1, 1):
        for side in (-1, 1):
            r.part("cube", face * 0.23, 2.6, side * 0.93, 0.02, 0.9, 0.05, (214, 224, 240))  # the frost


def _duchess_leaf(r, style, side, face, t, lit):
    """Frosted moon-glass in silver leading, a tall lancet of it picked out on each leaf."""
    r.part("cube", face * 0.085, 1.6, -side * 0.05, 0.02, 1.6, 0.04, style.iron)  # the lancet's mullion
    r.part("cube", face * 0.085, 2.4, -side * 0.05, 0.02, 0.04, 0.5, style.iron)  # its transom


DOOR_ARCHES = {
    "boss_dead": _warden_arch,
    "butcher_dead": _butcher_arch,
    "spider_dead": _loom_arch,
    "gargoyles_dead": _gargoyle_arch,
    "sexton_dead": _sexton_arch,
    "pall_dead": _pall_arch,
    "matron_dead": _matron_arch,
    "duchess_dead": _duchess_arch,
    "keystone_dead": lambda *a: sunken_models._keystone_arch(*a),
}
DOOR_LEAVES = {
    "boss_dead": _warden_leaf,
    "butcher_dead": _butcher_leaf,
    "spider_dead": _loom_leaf,
    "gargoyles_dead": _gargoyle_leaf,
    "sexton_dead": _sexton_leaf,
    "pall_dead": _pall_leaf,
    "matron_dead": _matron_leaf,
    "duchess_dead": _duchess_leaf,
    "keystone_dead": lambda *a: sunken_models._keystone_leaf(*a),
}
FOG_RISE = 0.3  # how many times a second a billow of the fog gate climbs from the floor to its top


def fog_gate(r, t, axis, sealed=False, height=BOSS_DOOR_TOP):
    """A wall of fog where a boss's door once stood, filling the doorway from the floor to `height`:
    sheets of stippled grey mist layered through it, billows welling up at its foot and climbing it
    to the top, motes rising with them. Sealed (the fight is on), it thickens."""
    grey = (118, 122, 132) if not sealed else (140, 136, 128)
    with r.at(0, 0, 0, ry=0 if axis == "x" else math.pi / 2):
        for i in range(3 if not sealed else 4):  # the sheets, each the whole doorway
            dx = (i - 1) * 0.12 + math.sin(t * 0.9 + i * 1.7) * 0.04
            tex = "mist" if i == 1 else "cloud_cap"
            r.part("cube", dx, height / 2, 0, 0.02, height, 2.0, _dim(grey, 1 - 0.1 * i), tex=tex, glow=True)
        r.part("cube", 0, 0.15, 0, 0.3, 0.3, 2.0, _dim(grey, 1.2), tex="mist", glow=True)  # welling up
        billow = min(0.6, height / 3)
        for i in range(4):  # billows climbing from the floor to the top
            u = (t * FOG_RISE + i / 4) % 1.0
            y = billow / 2 + u * (height - billow)
            r.part("cube", math.sin(i * 2.1) * 0.08, y, 0, 0.06, billow, 2.0, _dim(grey, 1.15 - 0.3 * u),
                   tex="cloud_cap", glow=True)  # fmt: skip
        for i in range(9):  # motes drifting up through the mist
            u = (t * 0.25 + i / 9) % 1.0
            z = math.sin(i * 2.7 + t * 0.7) * 0.85
            r.part("cube", math.sin(i * 1.9 + t) * 0.18, 0.05 + (height - 0.1) * u, z, 0.05, 0.05, 0.05,
                   (190, 192, 200), rx=t + i, glow=True)  # fmt: skip


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


SHRINE_COALS = (64, 34, 24)
SHRINE_FLAME_Y = 2.36  # where the shrine's flame burns (mesh_builder.LIGHT_Y lights the ground from there)


def save_statue(r, t):
    """A shrine: a plain waist-high stone post on a stepped base, a carved collar, and on top an
    iron dish heaped with coals, where a flame always burns."""
    r.part("cube", 0, 0.1, 0, 1.1, 0.2, 1.1, WHITE, tex="rough_stone")  # the steps
    r.part("cube", 0, 0.28, 0, 0.84, 0.16, 0.84, WHITE, tex="rough_stone")
    r.part("cube", 0, 1.03, 0, 0.44, 1.34, 0.44, WHITE, tex="rough_stone")  # the post
    r.part("cube", 0, 1.76, 0, 0.6, 0.12, 0.6, WHITE, tex="rough_stone")  # the collar
    r.part("cube", 0, 1.88, 0, 0.5, 0.12, 0.5, _dim(WHITE, 0.85), tex="rough_stone")
    r.part("cyl", 0, 1.97, 0, 0.42, 0.06, 0.42, DARK_IRON)  # the iron dish
    r.part("sphere", 0, 2.1, 0, 0.44, 0.18, 0.44, SHRINE_COALS)  # the heap of coals
    for i in range(3):
        a = i * 2.1 + 0.4
        glow = 0.8 + 0.2 * math.sin(t * 3 + i * 1.7)
        r.part(
            "sphere",
            math.cos(a) * 0.12,
            2.16,
            math.sin(a) * 0.12,
            0.13,
            0.08,
            0.13,
            _dimmed(EMBER, glow),
            glow=True,
        )
    _flame(r, 0, SHRINE_FLAME_Y, 0, 0.24, t)


OAK = (96, 66, 40)


def lever(r, k, wall=True, wood=False):
    """A lever, thrown as `k` (0..1) runs. Mounted on a wall at local -X, or free-standing."""
    if wood:
        with r.at(0, 0, 0, s=1.2):
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


LEVER_PLATE_Y = 1.15  # height of an iron lever's pivot above the floor
LEVER_UP = (
    0.35  # radians the iron lever's arm leans off straight up when raised (and off straight down thrown)
)
LEVER_PLATE = (66, 50, 42)  # its backplate, iron gone brown with rust


def _lever(r, k, wall):
    """The prison's lever: a rusted iron plate bolted to the wall at waist height, and a short arm
    swinging across its face from raised to thrown down, a worn wooden handle at its end. Free-standing,
    the plate hangs on a squat iron post."""
    wx = -0.97 if wall else -0.08  # the face the plate is bolted to
    if not wall:
        r.part("cube", -0.14, 0.06, 0, 0.34, 0.12, 0.34, WHITE, tex="rough_stone")  # the footing
        r.part("cube", -0.14, 0.66, 0, 0.12, 1.1, 0.12, DARK_IRON)  # the post
    y = LEVER_PLATE_Y
    r.part("cube", wx + 0.02, y, 0, 0.04, 0.5, 0.26, LEVER_PLATE)  # the backplate
    for dy in (-0.21, 0.21):  # its rivets
        for dz in (-0.09, 0.09):
            r.part("cube", wx + 0.05, y + dy, dz, 0.02, 0.03, 0.03, DARK_IRON)
    for dz in (-0.07, 0.07):  # the cheeks the arm swings between
        r.part("cube", wx + 0.08, y, dz, 0.08, 0.1, 0.02, DARK_IRON)
    r.part("cyl", wx + 0.08, y, 0, 0.05, 0.18, 0.05, IRON, rx=math.pi / 2)  # the pin
    with r.at(wx + 0.08, y, 0, rx=-LEVER_UP - (math.pi - 2 * LEVER_UP) * k):
        r.part("cube", 0, 0.17, 0, 0.04, 0.34, 0.05, IRON)  # the arm
        r.part("cyl", 0.07, 0.33, 0, 0.045, 0.14, 0.045, (78, 54, 36), rz=math.pi / 2)  # the handle
        r.part("cube", 0.0, 0.33, 0, 0.03, 0.03, 0.06, DARK_IRON)  # the collar it turns in


def lift(r, t, moving, chain_h, model="", doors=(), pressed=0.0):
    """A chain lift. `model="cage"` is the prison's jail cage: an iron-barred box hung from a single
    heavy chain, open only on the `doors` sides (dx, dz) that face a landing. Otherwise an oak deck
    in an iron frame, hung from four chains. Both run up to a pulley beam under the shaft's ceiling;
    riding, the chains shiver. In the middle of either floor is the pressure plate that sends it,
    sunk `pressed` metres while someone stands on it."""
    shiver = math.sin(t * 30) * 0.01 if moving else 0.0
    _lift_plate(r, pressed)
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


PLATE_IRON = (124, 118, 108)


def _lift_plate(r, pressed):
    """A round iron plate raised on the floor, ringed with a rim and worn bright in the middle."""
    y = 0.035 - pressed
    r.part("cyl", 0, 0.02, 0, 1.12, 0.05, 1.12, DARK_IRON)  # the rim it sinks into
    r.part("cyl", 0, y, 0, 0.98, 0.05, 0.98, PLATE_IRON)
    r.part("cyl", 0, y + 0.01, 0, 0.5, 0.04, 0.5, _bright(PLATE_IRON, 1.15, 10))  # worn smooth
    for i in range(6):  # bolts round its edge
        a = i * math.tau / 6
        r.part("cube", math.cos(a) * 0.38, y + 0.02, math.sin(a) * 0.38, 0.06, 0.03, 0.06, DARK_IRON, ry=a)


CALL_PLATE = 0.84  # side of a landing's call plate, in metres


def call_plate(r, sink=0.0, wood=False):
    """A landing's call plate, set flush in the floor just out from the shaft: a square of riveted iron
    plate (in the jungle, a slab of planks) in a stone (or timber) frame. It sinks `sink` metres under
    your weight."""
    frame = (96, 70, 44) if wood else (88, 84, 78)
    half = CALL_PLATE / 2
    for sx, sz in ((1, 0), (-1, 0), (0, 1), (0, -1)):  # the frame round it
        r.part(
            "cube",
            sx * half,
            0.012,
            sz * half,
            0.08 if sx else CALL_PLATE + 0.08,
            0.025,
            0.08 if sz else CALL_PLATE + 0.08,
            frame,
        )
    r.part(
        "cube",
        0,
        0.01 - sink,
        0,
        CALL_PLATE - 0.06,
        0.03,
        CALL_PLATE - 0.06,
        (190, 160, 120) if wood else (205, 210, 220),
        tex="wood_plank" if wood else "iron_plate",
    )


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


def pickup(r, t, item_id=None):
    """Something lying where it fell, turning slowly. A key or a relic shows itself, hovering in a
    soft glow; anything else is a sack with a glint of gold."""
    if item_id in KEY_STYLES or item_id in SIGILS:
        with r.at(0, 0.6 + math.sin(t * 2.4) * 0.06, 0, ry=t * 1.2):
            glow = SIGILS[item_id][1] if item_id in SIGILS else (255, 220, 150)
            halo = 0.22 + 0.03 * math.sin(t * 4)
            r.part("sphere", 0, 0, 0, halo, halo, halo, _dim(glow, 0.5), glow=True)
            with r.at(0, 0, 0, s=0.32 if item_id in SIGILS else 0.22):
                item(r, item_id, t)
        return
    with r.at(0, 0.3 + math.sin(t * 3) * 0.05, 0, ry=t * 1.5):
        r.part("sphere", 0, 0, 0, 0.3, 0.26, 0.3, (130, 100, 70))
        r.part("cube", 0, 0.15, 0, 0.12, 0.1, 0.12, (200, 170, 80))


WELL_WOOD = (90, 64, 40)


def well(r, t=0.0):
    """The old well in its sunken court: a drum of coursed stones under a coping, two posts braced to
    a pitched roof of slates, and a winch between them, its crank on one side and its rope wound
    round the drum and running down to a bucket hung in the black shaft. Iron rungs lead down."""
    for course, (y, h, rad) in enumerate(((0.22, 0.44, 0.75), (0.62, 0.36, 0.74))):
        for i in range(8):
            a = i * math.pi / 4 + course * math.pi / 8  # each course laid over the joints below
            r.part("cube", math.cos(a) * rad, y, math.sin(a) * rad, 0.3, h, 0.62, WHITE, tex="cobble", ry=-a)
    for i in range(8):  # the coping: a lip of dressed stone round the top
        a = i * math.pi / 4 + math.pi / 8
        r.part("cube", math.cos(a) * 0.78, 0.86, math.sin(a) * 0.78, 0.4, 0.1, 0.66, (168, 160, 148), ry=-a)
    r.part("cube", 0, 0.05, 0, 1.2, 0.05, 1.2, (10, 12, 14))  # the dark below
    for k in range(3):  # iron rungs down the shaft's inner face
        r.part("cube", -0.5, 0.55 - k * 0.22, 0, 0.06, 0.03, 0.26, (70, 66, 64))
    for x in (-0.85, 0.85):
        r.part("cube", x, 1.4, 0, 0.14, 2.0, 0.14, WELL_WOOD)  # the posts
        r.part("cube", x, 0.92, 0, 0.22, 0.12, 0.22, _dim(WELL_WOOD, 0.8))  # set into the coping
        for dz in (-1, 1):  # braces up under the roof
            r.part("cube", x, 2.1, dz * 0.2, 0.08, 0.5, 0.08, _dim(WELL_WOOD, 0.9), rx=dz * 0.7)
    r.part("cube", 0, 2.38, 0, 2.1, 0.12, 0.12, WELL_WOOD)  # the ridge beam
    for dz in (-1, 1):  # the roof's two pitches and their barge boards
        r.part("cube", 0, 2.24, dz * 0.36, 2.3, 0.06, 0.84, WHITE, tex="roof", rx=dz * 0.45)
        r.part("cube", 0, 2.2, dz * 0.36, 2.34, 0.04, 0.86, _dim(WELL_WOOD, 0.75), rx=dz * 0.45)
    # The winch: a drum between the posts, the rope wound round it, a crank out past the right post.
    turn = math.sin(t * 0.3) * 0.05
    r.part("cube", 0, 1.55, 0, 1.6, 0.06, 0.06, (60, 56, 56))  # the axle
    r.part("cyl", 0, 1.55, 0, 0.28, 0.9, 0.28, WELL_WOOD, rz=math.pi / 2, rx=turn)
    for i in range(5):  # turns of rope wound on the drum
        r.part("cyl", -0.32 + i * 0.16, 1.55, 0, 0.31, 0.06, 0.31, (150, 120, 80), rz=math.pi / 2)
    with r.at(0.98, 1.55, 0, rx=turn * 6):
        r.part("cube", 0.04, 0, 0, 0.04, 0.04, 0.04, (60, 56, 56))
        r.part("cube", 0.06, -0.14, 0, 0.04, 0.3, 0.04, (60, 56, 56))  # the crank's arm
        r.part("cube", 0.12, -0.28, 0, 0.14, 0.05, 0.05, WELL_WOOD)  # its handle
    sway = math.sin(t * 0.9) * 0.02
    r.part("cube", 0.1 + sway, 1.1, 0.14, 0.03, 0.9, 0.03, (150, 120, 80))  # the rope down the shaft
    with r.at(0.1 + sway, 0.6, 0.14):  # the bucket, hung over the dark
        r.part("frustum", 0, 0, 0, 0.24, 0.24, 0.24, (104, 76, 50), rz=FLIP)
        r.part("cube", 0, 0.06, 0, 0.26, 0.03, 0.26, (60, 56, 56))  # its hoop
        r.part("cube", 0, 0.2, 0, 0.02, 0.02, 0.26, (60, 56, 56))  # and its bail


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


CAVE_TIMBER = (88, 64, 42)


def cave_mouth(r, t):
    """A cleft in the rock on the -X edge: a rough arch of boulders over a black opening, hung with
    roots and moss, shored by a timber frame someone set in its mouth long ago: two posts and a beam,
    notched and pegged, a lantern swinging from it and a cairn of stones with a guttering candle
    beside it. Cold air seems to breathe out of it."""
    rock = (110, 104, 94)
    r.part("cube", -0.95, 1.3, 0, 0.1, 2.6, 1.6, (6, 6, 8))  # the dark beyond
    for z in (-0.95, 0.95):
        r.part("cube", -0.8, 1.2, z, 0.5, 2.4, 0.45, rock, tex="cliff_rock", rz=0.05 * z)
        r.part("cube", -0.72, 0.25, z * 0.98, 0.62, 0.5, 0.55, _dim(rock, 0.85), tex="cliff_rock")  # its foot
    r.part("cube", -0.8, 2.55, 0, 0.6, 0.5, 2.3, rock, tex="cliff_rock", rx=0.08)
    for k, (y, z, d) in enumerate(((0.3, -0.7, 0.55), (0.25, 0.8, 0.5), (2.8, 0.5, 0.6), (2.75, -0.6, 0.5))):
        r.part("sphere", -0.6, y, z, d, d * 0.8, d, rock, tex="cliff_rock")
        r.part("cube", -0.55, y + d * 0.35, z, d * 0.7, 0.06, d * 0.7, MOSS if k % 2 else (56, 92, 44))
    # The shoring: two posts, a beam across, pegs and a notch cut in each post for the beam.
    for z in (-0.68, 0.68):
        r.part("cube", -0.42, 1.05, z, 0.16, 2.1, 0.16, CAVE_TIMBER, tex="bark")
        r.part("cube", -0.42, 0.05, z, 0.26, 0.1, 0.26, (70, 66, 60))  # a flat stone under it
        r.part("cube", -0.33, 1.95, z, 0.04, 0.06, 0.06, _dim(CAVE_TIMBER, 0.6))  # a peg
        for k in range(3):  # marks cut in it, counting the ones who went in
            r.part("cube", -0.335, 1.1 + k * 0.12, z, 0.01, 0.025, 0.1, _dim(CAVE_TIMBER, 0.55))
    r.part("cube", -0.42, 2.15, 0, 0.2, 0.18, 1.7, CAVE_TIMBER, tex="bark")  # the beam
    for z in (-0.68, 0.68):  # braces from post to beam
        r.part("cube", -0.42, 1.92, z * 0.78, 0.08, 0.36, 0.08, _dim(CAVE_TIMBER, 0.85), rx=-z * 0.9)
    swing = math.sin(t * 1.1) * 0.12
    with r.at(-0.3, 2.06, 0.25, rx=swing, s=1.8):  # the lantern, swinging on its chain from the beam
        r.part("cube", 0, -0.12, 0, 0.02, 0.24, 0.02, (60, 58, 62))
        r.part("cube", 0, -0.32, 0, 0.14, 0.18, 0.14, (54, 52, 56))
        flick = 0.85 + 0.15 * math.sin(t * 7)
        r.part("cube", 0, -0.32, 0, 0.1, 0.13, 0.15, _dim((255, 200, 110), flick), glow=True)
        r.part("frustum", 0, -0.2, 0, 0.18, 0.07, 0.18, (54, 52, 56))
    for k, (dx, dy, sz) in enumerate(((0, 0.1, 0.24), (0.02, 0.27, 0.18), (-0.01, 0.4, 0.12))):  # a cairn
        r.part("cube", 0.2 + dx, dy, -0.75, sz, sz * 0.7, sz, _dim(rock, 0.9 + 0.06 * k), ry=k * 0.6)
    r.part("cube", 0.2, 0.52, -0.75, 0.03, 0.08, 0.03, (220, 210, 180))  # a stub of candle on it
    r.part("cube", 0.2, 0.59, -0.75, 0.02, 0.04 + 0.01 * math.sin(t * 9), 0.02, (255, 200, 110), glow=True)
    for k in range(7):  # roots trailing over the lip
        z = -0.75 + k * 0.25
        length = 0.4 + (k * 29 % 5) * 0.16
        sway = math.sin(t * 0.8 + k) * 0.03
        r.part("cube", -0.6, 2.3 - length / 2, z + sway, 0.05, length, 0.05, (80, 60, 40))
        if k % 2 == 0:  # a tuft of leaves on every other one
            r.part("cube", -0.58, 2.3 - length, z + sway, 0.08, 0.06, 0.1, (64, 104, 52))


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


ROPE = (150, 120, 80)


def rope(r, t, top=3.2):
    """The rope up out of the Abandoned Prison: knotted every half metre for the hands and feet, hung
    `top` metres up from an iron ring on a beam across the shaft, a stone ring round its foot, a coil of
    slack on the floor and motes of dust drifting down in the daylight from the well."""
    with r.at(0, top, 0, rz=math.sin(t * 0.8) * 0.04 * 3.2 / top):
        r.part("cyl", 0, -top / 2, 0, 0.07, top, 0.07, ROPE)
        for k in range(int((top - 0.4) / 0.48)):  # the knots
            r.part("cube", 0, -0.45 - k * 0.48, 0, 0.12, 0.08, 0.12, _dim(ROPE, 0.85), ry=k * 0.5)
        r.part("cube", 0, 0.2 - top, 0, 0.16, 0.12, 0.16, (130, 100, 70))
    r.part("cube", 0, top + 0.1, 0, 0.2, 0.2, 2.0, (80, 60, 40))  # the beam across the shaft
    r.part("cube", 0, top - 0.02, 0, 0.14, 0.04, 0.14, (70, 66, 64))  # the ring it hangs from
    r.part("cube", 0, top - 0.02, 0, 0.04, 0.14, 0.14, (70, 66, 64))
    r.part("cyl", 0, 0.05, 0, 1.0, 0.1, 1.0, (40, 40, 44))
    for i in range(8):  # the stones round its foot
        a = i * math.pi / 4
        r.part("cube", math.cos(a) * 0.62, 0.1, math.sin(a) * 0.62, 0.22, 0.2, 0.3, (96, 92, 88), ry=-a)
    for k in range(3):  # the slack, coiled on the floor
        r.part(
            "cyl",
            0.3,
            0.06 + k * 0.05,
            0.25,
            0.42 - k * 0.08,
            0.05,
            0.42 - k * 0.08,
            _dim(ROPE, 0.9 - k * 0.05),
        )
    if top > 6:  # far up a well's shaft: the daylit mouth of the well, and its light slanting down
        r.part("cyl", 0, top + 0.25, 0, 1.7, 0.04, 1.7, (206, 214, 226), glow=True)
        r.part("cyl", 0, top + 0.22, 0, 2.0, 0.03, 2.0, (120, 128, 140), glow=True)  # its halo
    for k in range(4):  # motes of dust drifting down through the daylight from above
        y = top - ((t * 0.25 + k / 4) % 1.0) * (top - 0.2)
        r.part("cube", math.sin(k * 2.1 + t * 0.4) * 0.3, y, math.cos(k * 1.7) * 0.3, 0.025, 0.025, 0.025,
               (190, 196, 200), glow=True)  # fmt: skip


FIRE_CORE = (255, 246, 210)  # the white-hot heart of every fireball
FIRE_TIP = (255, 214, 110)  # the pale ends of its licking tongues


def fiery(rgb):
    """Whether a shot of colour `rgb` is fire (drawn as a fireball): red-hot, little blue."""
    r_, g, b = rgb
    return r_ >= 200 and g <= 210 and b <= 120


FIRE_LICKS = 3  # loose tongues of flame that break off the top and rise away
FIRE_SPARKS = 2  # embers drifting up out of it
FIRE_SMOKE = (150, 40, 16)  # the deep red a lick cools to as it rises away


def _flame_frame(trail):
    """The (ry, rz) turning a flame's +Y to where its tongues stream: straight up while it stands,
    swept back along `trail` (and a little up) while it flies."""
    if trail is None:
        return 0.0, 0.0
    dx, dy, dz = trail[0] * 0.85, trail[1] * 0.85 + 0.5, trail[2] * 0.85
    n = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
    dx, dy, dz = dx / n, dy / n, dz / n
    return math.atan2(dz, -dx), math.acos(max(-1.0, min(1.0, dy)))


def fireball(r, rgb, t, size=1.0, trail=None, seed=0.0, lean=False):
    """A flame `size` times a bolt's (0.3 m across): three nested teardrops, a white-hot core in a
    pale-gold heart in a shell of `rgb`, their tips licking and swaying out of step; loose tongues
    break off the top and rise away, shrinking and reddening, with embers drifting up out of it.
    With `trail` (the unit direction it came from) it streams back along it like a comet, leaving a
    wake of embers that shrink and redden behind it. A `lean` flame, one of many in a row, sheds a
    single loose tongue, no embers and no wake."""
    s = size
    flick = 1 + math.sin(t * 23 + seed) * 0.08
    ry, rz = _flame_frame(trail)
    with r.at(0, 0, 0, ry=ry, rz=rz):
        for k, (w, h, rgb_k) in enumerate(
            ((0.32, 0.62, rgb), (0.23, 0.46, FIRE_TIP), (0.14, 0.3, FIRE_CORE))
        ):
            w *= s * (flick if k == 0 else 1)
            h *= s * (1 + 0.16 * math.sin(t * (11 + 3 * k) + seed + k * 1.9))
            r.part("sphere", 0, 0, 0, w, w * 0.9, w, rgb_k, glow=True)
            sway = 0.22 * math.sin(t * (7 + 2 * k) + seed + k * 2.4)
            nod = 0.18 * math.sin(t * (5 + k) + seed * 1.3 + k)
            with r.at(0, w * 0.2, 0, rz=sway, rx=nod):
                r.part("cone", 0, h / 2, 0, w * 0.92, h, w * 0.92, rgb_k, glow=True)
            if k == 0:  # the shell forks: a second, shorter tongue licks out of step beside the first
                side = 0.3 * math.sin(t * 3 + seed)
                with r.at(-w * 0.3, w * 0.1, w * side, rz=0.3 - sway, rx=-nod):
                    r.part("cone", 0, h * 0.35, 0, w * 0.7, h * 0.7, w * 0.7, rgb_k, glow=True)
        for i in range(1 if lean else FIRE_LICKS):
            p = (t * 1.9 + i / FIRE_LICKS + seed * 0.37) % 1.0
            w = 0.13 * s * (1 - p)
            x = 0.1 * s * math.sin(i * 2.1 + seed + p * 4)
            z = 0.1 * s * math.cos(i * 1.7 + seed + p * 3)
            lick = _lerp(FIRE_TIP, rgb, min(p * 2, 1.0)) if p < 0.5 else _lerp(rgb, FIRE_SMOKE, p * 2 - 1)
            lick = tuple(rround(c) for c in lick)
            r.part("cone", x, (0.42 + 0.5 * p) * s, z, w, w * 2.4, w, lick, glow=True)
        for i in range(0 if lean else FIRE_SPARKS):
            p = (t * 0.9 + i / FIRE_SPARKS + seed * 0.21) % 1.0
            e = 0.035 * s * (1 - p)  # dwindling as it rises, until it winks out and another rises
            x = 0.2 * s * math.sin(i * 3.3 + seed + p * 6)
            r.part("cube", x, (0.3 + 0.9 * p) * s, 0.05 * s * math.cos(p * 5 + i), e, e, e, FIRE_TIP,
                   rx=t * 6 + i, ry=t * 4, glow=True)  # fmt: skip
    if trail is None or lean:
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
    """A spark of Pyre's fire: a ragged fireball that swells, then gutters to a red ember as `k`
    runs to 0."""
    size = 0.04 + 0.1 * math.sin(min(k, 1.0) * math.pi) ** 0.5
    cool = min(k * 2.2, 1.0)  # the last moments: dull red
    rgb = (rgb[0], rround(rgb[1] * cool + 40 * (1 - cool)), rround(rgb[2] * cool + 10 * (1 - cool)))
    fireball(r, rgb, t, size / 0.3, seed=k * 9)


GOUT_HOT = (255, 225, 140)
GOUT_COOL = (210, 50, 20)


def gout_puff(r, size, heat, t, seed=0.0):
    """One ball of Pyre's gout: white-gold where it leaves your hand (`heat` 1), deep red and smoky at
    its far, roiling front (`heat` 0)."""
    if size <= 0.02:
        return
    rgb = _lerp(GOUT_COOL, GOUT_HOT, heat)
    roil = 1 + 0.12 * math.sin(t * 31 + seed * 3)
    fireball(r, tuple(rround(c) for c in rgb), t, size * roil, seed=seed)
    if heat < 0.45:  # smoke curls off the cooling front
        k = 1 - heat / 0.45
        s = 0.35 * size * k
        r.part("sphere", 0.05, 0.3 * size + 0.1 * k, 0, s, s * 0.8, s, (60, 40, 32))


def bolt(r, rgb, t=0.0, trail=None):
    """A spell bolt or a foe's shot: fire burns as a fireball, anything else is a bright glob."""
    if fiery(rgb):
        fireball(r, rgb, t, trail=trail)
        return
    r.part("sphere", 0, 0, 0, 0.3, 0.3, 0.3, rgb, glow=True)
    r.part("sphere", 0, 0, 0, 0.5, 0.18, 0.18, (255, 230, 160), glow=True)


THORN_WOOD = (164, 132, 80)  # a thorn's pale, woody shaft
THORN_TIP = (64, 40, 26)  # darkening to a hard point
THORN_SCALE = 1.7


def thorn_shot(r, rgb, t):
    """A barbed thorn in flight, point first along +X: a fleshy green root torn from the plant, a pale
    shaft hardening to a dark point, hooked barbs raked back round it, a scrap of leaf flapping at its
    tail and a glowing bead of sap (`rgb`) trailing off it. Drawn at `THORN_SCALE`, so it reads in flight."""
    with r.at(s=THORN_SCALE):
        _thorn(r, rgb, t)


def _thorn(r, rgb, t):
    r.part("sphere", -0.2, 0, 0, 0.14, 0.1, 0.1, _dim(rgb, 0.6))  # the fleshy root
    r.part("frustum", -0.02, 0, 0, 0.08, 0.36, 0.08, THORN_WOOD, rz=-math.pi / 2)
    r.part("blade", 0.26, 0, 0, 0.07, 0.22, 0.07, THORN_TIP, rz=-math.pi / 2)
    for k in range(3):  # barbs, hooked back
        with r.at(-0.08 + k * 0.1, 0, 0, rx=k * 2.1 + 0.4):
            r.part("cone", -0.03, 0.045, 0, 0.03, 0.09, 0.03, THORN_TIP, rz=0.97)
    with r.at(-0.28, 0, 0, rx=math.sin(t * 22) * 0.7):  # a scrap of leaf
        r.part("cube", -0.06, 0, 0, 0.14, 0.01, 0.08, LEAF, ry=0.3)
    r.part("sphere", -0.36, -0.02 - 0.02 * math.sin(t * 9), 0, 0.05, 0.06, 0.05, rgb, glow=True)


# --- dungeon dressing --------------------------------------------------------

DARK_IRON = (58, 56, 60)


def variant(seed, n):
    """Which of `n` looks a prop takes, from its tile's seed: hashed, so it doesn't fall in step with
    the seed's other uses (`seed % 2` stacking a crate, `seed % 3` a barrel's height)."""
    return ((seed * 2654435761) >> 13) % n


BARREL_LOOKS = 3  # a banded cask, an open water butt, a cask on its side in a cradle
CRATE_LOOKS = 3  # a plank crate, a slatted one spilling straw, a long iron-strapped one
WATER_DARK = (30, 40, 44)
STRAW = (176, 152, 90)
SACKCLOTH = (132, 112, 80)


def barrel(r, seed, broken=False, t=1.0):
    """A cask; the seed picks its look (`variant`) and nudges its spot, height and lean so rows don't
    look cloned. A broken one is a ring of staves and a fallen hoop; `t` (0 the blow, 1 settled) flings
    them out to it (`_flung`)."""
    h = 0.95 + (seed % 3) * 0.08
    ox = ((seed * 37) % 7 - 3) * 0.08
    oz = ((seed * 53) % 7 - 3) * 0.08
    if broken:
        _barrel_wreck(r, ox, oz, seed, t)
        return
    look = variant(seed, BARREL_LOOKS)
    if look == 1:
        _water_butt(r, ox, oz, seed)
        return
    if look == 2:
        _cradled_cask(r, ox, oz, seed)
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


def _water_butt(r, ox, oz, seed):
    """A tall open barrel of standing water, three hoops, rope handles; a dipper hung on its rim."""
    with r.at(ox, 0, oz, ry=seed * 0.5):
        r.part("cyl", 0, 0.5, 0, 0.82, 1.0, 0.82, _dim(WHITE, 0.85), tex="wood_plank")
        for y in (0.1, 0.5, 0.9):
            r.part("cyl", 0, y, 0, 0.86, 0.05, 0.86, DARK_IRON)
        r.part("cyl", 0, 0.93, 0, 0.72, 0.02, 0.72, WATER_DARK)  # the water, a hand below the rim
        for z in (-0.42, 0.42):  # rope handles
            r.part("cube", 0, 0.75, z, 0.18, 0.04, 0.04, CHEST_ROPE)
        r.part("cube", 0.36, 0.95, 0, 0.06, 0.06, 0.3, (110, 86, 58), rz=0.4)  # the dipper's handle
        r.part("cyl", 0.48, 0.86, 0.1, 0.14, 0.08, 0.14, (110, 86, 58))


def _cradled_cask(r, ox, oz, seed):
    """A cask laid on its side in a timber cradle, a dark stain spreading under its bung."""
    with r.at(ox * 0.5, 0, oz * 0.5, ry=seed * 0.9):
        for x in (-0.3, 0.3):  # the cradle's chocks
            r.part("cube", x, 0.08, 0, 0.14, 0.16, 0.8, OAK)
        r.part("cyl", 0, 0.44, 0, 0.7, 0.95, 0.7, WHITE, tex="wood_plank", rx=math.pi / 2)
        r.part("cyl", 0, 0.44, 0, 0.76, 0.5, 0.76, WHITE, tex="wood_plank", rx=math.pi / 2)  # the belly
        for z in (-0.36, 0.36):
            r.part("cyl", 0, 0.44, z, 0.74, 0.05, 0.74, DARK_IRON, rx=math.pi / 2)
        for z in (-0.48, 0.48):
            r.part("cyl", 0, 0.44, z, 0.6, 0.01, 0.6, (70, 48, 30), rx=math.pi / 2)  # its heads
        r.part("cyl", 0, 0.82, 0, 0.08, 0.04, 0.08, (60, 40, 26))  # the bung
        r.part("cyl", 0.1, 0.005, 0.15, 0.6, 0.01, 0.45, (44, 34, 28))  # the stain


def _barrel_wreck(r, ox, oz, seed, t=1.0):
    with r.at(ox, 0, oz, ry=seed * 0.7):
        _flung(r, t, 0, 0.12, "cyl", 0, 0.03, 0, 0.84, 0.06, 0.84, DARK_IRON, rx=0.08)
        _flung(r, t, 1, 0.5, "cyl", 0, 0.03, 0, 0.66, 0.05, 0.66, (70, 48, 30))
        for i in range(7):
            a = i * 0.9 + seed
            d = 0.45 + (i % 3) * 0.12
            _flung(r, t, i + 2, 0.45, "cube", math.cos(a) * d, 0.04, math.sin(a) * d,
                   0.5 - (i % 2) * 0.15, 0.04, 0.12, WHITE, tex="wood_plank", ry=a * 1.3)  # fmt: skip
        _flung(r, t, 9, 0.4, "cube", 0.25, 0.18, -0.2, 0.06, 0.36, 0.12, WHITE, tex="wood_plank", rz=0.3)
        _break_dust(r, t, (92, 74, 56))


BREAK_LAND = 0.7  # share of a break by which a flung piece first lands; it bounces once, then lies still
BREAK_DUST = 4  # puffs of dust a prop throws up as it breaks


def _flung(r, t, i, from_y, kind, x, y, z, sx, sy, sz, rgb, **kw):
    """Piece `i` of a breaking prop at `t` (0 the blow, 1 settled): `r.part(kind, x, y, z, ...)` as it
    lies in the wreck, but on its way there. It leaves from near the prop's middle, `from_y` up, flies
    out along an eased path over a hop, spinning (a turn of its own that dies away), lands at
    BREAK_LAND, bounces once and settles. At t=1 it is exactly the wreck's part."""
    if t >= 1.0:
        r.part(kind, x, y, z, sx, sy, sz, rgb, **kw)
        return
    t = max(t, 0.0)
    u = min(t / BREAK_LAND, 1.0)
    out = 1 - (1 - u) ** 2  # fast at first, slowing as it comes down
    hop = (0.22 + 0.06 * (i % 3)) * 4 * u * (1 - u)
    if t > BREAK_LAND:  # the bounce
        v = (t - BREAK_LAND) / (1 - BREAK_LAND)
        hop += 0.05 * 4 * v * (1 - v)
    px, pz = x * (0.25 + 0.75 * out), z * (0.25 + 0.75 * out)
    py = from_y + (y - from_y) * u + hop
    spin = (1 - t) ** 2 * (5.0 + (i % 4))
    tumble = i * 2.399  # the golden angle: each piece tumbles about an axis of its own
    with r.at(px, py, pz, rx=spin * math.cos(tumble), rz=spin * math.sin(tumble)):
        r.part(kind, 0, 0, 0, sx, sy, sz, rgb, **kw)


def _break_dust(r, t, rgb, spread=1.0):
    """The dust a breaking prop throws up: BREAK_DUST dim puffs that billow out, swell and fade away
    before it settles. Nothing once it has (`t` 1)."""
    if t >= 1.0:
        return
    t = max(t, 0.0)
    fade = 1 - t
    for i in range(BREAK_DUST):
        a = i * math.tau / BREAK_DUST + 0.4
        d = (0.12 + 0.4 * _ease(min(t / 0.6, 1.0))) * spread
        size = (0.3 + 0.55 * t) * spread * (fade**0.5)
        y = 0.2 + 0.3 * t + 0.06 * (i % 2)
        r.part("sphere", math.cos(a) * d, y, math.sin(a) * d, size, size * 0.6, size,
               _blend(_dim(rgb, 0.8), (150, 140, 124), t), tex="mist")  # fmt: skip


SECRET_SEAR = 0.22  # share of a fake wall's fall spent turning to ash before it crumbles
SECRET_CELL = 0.5  # metres: the ashen wall crumbles away in cells this size
SHIMMER_CYCLE = 6.0  # seconds between the faint shimmers that give a fake wall away
SHIMMER_PASS = 1.6  # seconds a shimmer takes to climb the wall
SECRET_BASE = (238, 238, 238)  # an illusion is a shade duller than the stone it apes
SECRET_ASH = (104, 98, 94)
SECRET_ASH_DARK = (60, 56, 54)
CRACK = (255, 120, 40)
CRACK_DIM = (150, 60, 24)
SECRET_ASH_TEX = "ash_ground"  # what the crumbling cells show: loose ash, not the stone they aped


def secret_wall(r, height, open_t, tex="stone_brick", t=0.0, shimmer=False, near=False):
    """An illusory wall: a full tile in the texture of the walls beside it (brick in the prison, a
    curtain of vines in the jungle). Now and then a faint shimmer climbs it (`shimmer`), and up close
    a few pale motes drift on its faces (`near`): the only tells. Struck (`open_t` 0..1), ember cracks
    run across it as it sears to ash, then it crumbles top-down, cell by cell, into falling ash and
    rising embers, with a puff of dust at its foot."""
    if open_t >= 1.0:
        return
    if open_t < SECRET_SEAR:
        _secret_intact(r, height, open_t / SECRET_SEAR, tex, t, shimmer and open_t == 0, near and open_t == 0)
    else:
        _secret_crumble(r, height, (open_t - SECRET_SEAR) / (1 - SECRET_SEAR), t)


def _secret_intact(r, height, sear, tex, t, shimmer, near):
    """The whole wall in 2 m blocks, so its texture repeats every 2 m like the map's own walls.
    `sear` (0..1) greys it toward ash while glowing cracks spread over its faces."""
    phase = (t % SHIMMER_CYCLE) / SHIMMER_PASS if shimmer else 2.0
    band = phase * (height + 1.0) - 0.5  # the shimmer's height, climbing the wall
    y = 0.0
    while y < height - 1e-3:
        seg = min(2.0, height - y)
        glint = max(0.0, 1.0 - abs(band - (y + seg / 2)) / 1.4) if phase < 1 else 0.0
        rgb = _blend(_blend(SECRET_BASE, WHITE, glint), SECRET_ASH, sear)
        r.part("cube", 0, y + seg / 2, 0, 2.0, seg, 2.0, rgb, tex=tex)
        y += seg
    if near:
        for i in range(3):  # pale motes sliding over its faces
            a = i * 2.09 + t * 0.15
            k = (t * 0.2 + i / 3) % 1
            face = (math.cos(a) * 1.02, math.sin(a) * 1.02)
            r.part("cube", face[0], 0.4 + k * (height - 0.8), face[1], 0.03, 0.03, 0.03,
                   _blend((150, 150, 160), (220, 220, 235), 1 - abs(k * 2 - 1)), glow=True)  # fmt: skip
    if sear <= 0:
        return
    cracks = 28
    for i in range(cracks):  # hairline ember cracks spreading over every face as it sears
        if i / cracks > sear:
            break
        side = i % 4
        u = math.sin(i * 12.9898) * 43758.5453 % 1.0 * 1.6 - 0.8
        v = (math.sin(i * 78.233) * 12543.21 % 1.0) * height
        length = 0.12 + 0.3 * min(sear * 2 - i / cracks, 1.0)
        tilt = (math.sin(i * 4.1) * 0.9, math.sin(i * 4.1) * 0.9)[side % 2]
        nx, nz = ((1.005, u), (u, 1.005), (-1.005, u), (u, -1.005))[side]
        thin = 0.012
        rgb = _blend(CRACK_DIM, CRACK, sear)
        if side % 2 == 0:
            r.part("cube", nx, v, nz, thin, thin, length, rgb, rx=tilt, glow=True)
        else:
            r.part("cube", nx, v, nz, length, thin, thin, rgb, rz=tilt, glow=True)


def _crumble_order(x, z, row, rows):
    """When (0..1 of the crumble) the wall's cell at (x, z) in `row` falls: top first, with a ragged
    jitter so the falling edge never runs straight."""
    jitter = (math.sin(x * 12.9898 + z * 39.346 + row * 78.233) * 43758.5453) % 1.0
    return min(0.62 * (rows - 1 - row) / max(rows - 1, 1) + 0.18 * jitter, 0.8)


def _secret_crumble(r, height, c, t):
    """The seared wall crumbling (`c` 0..1): only its outer shell of cells is drawn. Each cell sags,
    darkens, tumbles and shrinks to nothing as it falls, ash drifts down and embers lift off."""
    rows = max(math.ceil(height / SECRET_CELL), 1)
    ring = [(i, 0) for i in range(4)] + [(3, j) for j in range(1, 4)] + [(i, 3) for i in range(2, -1, -1)]
    ring += [(0, j) for j in range(2, 0, -1)]
    for row in range(rows):
        y0 = row * SECRET_CELL
        h = min(SECRET_CELL, height - y0)
        for i, j in ring:
            x, z = -0.75 + i * SECRET_CELL, -0.75 + j * SECRET_CELL
            f = (c - _crumble_order(x, z, row, rows)) / 0.2
            if f >= 1.0:
                continue
            f = max(f, 0.0)
            k = 1.0 - f
            drop = f * f * 1.6
            tumble = f * (2.0 if (i + j + row) % 2 else -2.0)
            rgb = _blend(SECRET_ASH, SECRET_ASH_DARK, f)
            r.part("cube", x * (1 + f * 0.3), y0 + h / 2 - drop, z * (1 + f * 0.3), SECRET_CELL * k,
                   h * k, SECRET_CELL * k, rgb, tex=SECRET_ASH_TEX, rx=tumble, rz=tumble * 0.7)  # fmt: skip
            if 0 < f < 0.6 and (i + row) % 3 == 0:  # a glowing seam as it parts
                r.part("cube", x * 1.05, y0 + h - drop, z * 1.05, SECRET_CELL * k, 0.03, SECRET_CELL * k,
                       CRACK, rx=tumble, glow=True)  # fmt: skip
    for i in range(10):  # ash sifting down and out
        k = (c * 1.4 + i / 10) % 1
        a = i * 0.628 + c
        out = 0.9 + k * 0.8
        r.part("cube", math.cos(a) * out, height * (1 - c) * (1 - k) + 0.05, math.sin(a) * out, 0.06, 0.06, 0.06,
               _blend(SECRET_ASH, SECRET_ASH_DARK, k), rx=a + t, ry=k * 4)  # fmt: skip
    glow = 1.0 - c
    for i in range(6):  # embers lifting off
        k = (t * 0.7 + i / 6) % 1
        a = i * 1.047 + t * 0.5
        r.part("cube", math.cos(a) * 0.7, 0.3 + c * height * 0.6 + k * 1.6, math.sin(a) * 0.7, 0.05, 0.05, 0.05,
               _blend(SECRET_ASH_DARK, EMBER, glow * (1 - k)), rx=t * 3 + i, glow=glow > 0.05)  # fmt: skip
    puff = math.sin(min(c * 1.2, 1.0) * math.pi)
    if puff > 0.02:  # the dust thrown up at its foot
        for i in range(5):
            a = i * 1.257 + 0.3
            s_ = 0.3 + 0.35 * puff
            r.part("sphere", math.cos(a) * (0.6 + c), 0.25 + c * 0.3, math.sin(a) * (0.6 + c), s_, s_ * 0.7, s_,
                   _blend((168, 162, 156), (124, 120, 116), c))  # fmt: skip


WEB_CELL = 0.5  # metres: the burning silk falls away in cells this size
CHAR = (34, 28, 24)
BURN_EDGE = (255, 120, 40)


def _burn_order(x, z, row, rows):
    """When (0..1 of the burn) the web wall's cell at (x, z) in `row` catches: low first, the middle
    of each face before its corners, with a ragged jitter so the edge never runs straight."""
    side = min(abs(x), abs(z)) / 0.75
    jitter = (math.sin(x * 12.9898 + z * 39.346 + row * 78.233) * 43758.5453) % 1.0
    return min(0.62 * row / max(rows - 1, 1) + 0.18 * side + 0.16 * jitter, 1.0)


def burning_web(r, height, open_t, t):
    """A web wall burning away once fire has caught it (`open_t` 0..1): the flame climbs from the
    bottom, each cell of the silk blackening, glowing at its edge and licked by flames before it
    falls away, while embers drift up. Only the outer shell of cells is drawn (a ring round the tile)."""
    if open_t >= 1.0:
        return
    if open_t <= 0.0:
        return secret_wall(r, height, 0.0, tex="web_wall")
    front = open_t * 1.3
    band = 0.22
    rows = max(math.ceil(height / WEB_CELL), 1)
    ring = [(i, 0) for i in range(4)] + [(3, j) for j in range(1, 4)] + [(i, 3) for i in range(2, -1, -1)]
    ring += [(0, j) for j in range(2, 0, -1)]
    for row in range(rows):
        y0 = row * WEB_CELL
        h = min(WEB_CELL, height - y0)
        for n, (i, j) in enumerate(ring):
            x, z = -0.75 + i * WEB_CELL, -0.75 + j * WEB_CELL
            d = _burn_order(x, z, row, rows)
            if d < front - band:
                continue  # burnt through
            if d >= front:
                r.part("cube", x, y0 + h / 2, z, WEB_CELL, h, WEB_CELL, WHITE, tex="web_wall")
                continue
            k = (front - d) / band  # 0 as it catches, 1 as it falls
            s = WEB_CELL * (1 - 0.45 * k)
            r.part("cube", x, y0 + h / 2 - 0.1 * k, z, s, h * (1 - 0.5 * k), s, CHAR)
            r.part("cube", x, y0 + h - 0.04, z, s + 0.04, 0.05, s + 0.04, BURN_EDGE, glow=True)
            if (n + row) % 2 == 0:  # flames licking up the outside of the sheet
                _flame(r, x * 1.4, y0 + h * 0.35, z * 1.4, 0.28 * (1.2 - k), t + n)
    for i in range(10):  # embers drifting up off the burn
        seed = i * 2.39
        rise = (t * 0.9 + seed) % 1.0
        y = min(front, 1.0) * height * 0.8 + rise * 1.6
        a = seed * 2.7
        x = math.cos(a) * 1.2 + math.sin(t * 2 + seed) * 0.15
        z = math.sin(a) * 1.2
        size = 0.06 * (1 - rise) + 0.02
        r.part("cube", x, y, z, size, size, size, EMBER, glow=True)


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


def crate(r, seed, broken=False, t=1.0):
    """A plank crate with dark battens; sometimes a smaller one stacked on top. Broken, it is a heap of
    split planks with the lid lying askew; `t` (0 the blow, 1 settled) flings them out to it."""
    with r.at(((seed * 29) % 5 - 2) * 0.1, 0, ((seed * 41) % 5 - 2) * 0.1, ry=(seed % 5) * 0.3):
        if broken:
            for i in range(6):
                a = i * 1.1 + seed
                d = 0.2 + (i % 3) * 0.15
                _flung(
                    r, t, i, 0.45, "cube", math.cos(a) * d, 0.04 + (i % 2) * 0.05, math.sin(a) * d,
                    0.8 - (i % 3) * 0.15, 0.05, 0.16, WHITE, tex="wood_plank", ry=a * 1.4, rz=(i % 2) * 0.15,
                )  # fmt: skip
            _flung(r, t, 6, 0.85, "cube", -0.15, 0.12, 0.1, 0.85, 0.06, 0.85, WHITE, tex="wood_plank", ry=0.5,
                   rz=0.2)  # fmt: skip
            _break_dust(r, t, (92, 74, 56))
            return
        look = variant(seed, CRATE_LOOKS)
        if look == 1:
            _slatted_crate(r, seed)
            return
        if look == 2:
            _long_crate(r, seed)
            return
        _crate_box(r, 0.9)
        if seed % 2 == 0:
            with r.at(0.05, 0.9, -0.05, ry=0.5):
                _crate_box(r, 0.6)


def _slatted_crate(r, seed):
    """An open-slatted crate, dark gaps between its boards, X-braced on two faces, straw spilling over
    its top; sometimes a little one, upended, beside it."""
    s = 0.85
    edge = (60, 40, 26)
    r.part("cube", 0, s / 2, 0, s - 0.08, s - 0.04, s - 0.08, (26, 20, 16))  # the dark inside
    for k in range(4):  # slats round the four sides
        y = 0.12 + k * 0.21
        for side in (-1, 1):
            r.part("cube", side * s / 2, y, 0, 0.04, 0.14, s, WHITE, tex="wood_plank")
            r.part("cube", 0, y, side * s / 2, s, 0.14, 0.04, WHITE, tex="wood_plank")
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * s / 2, s / 2, dz * s / 2, 0.07, s, 0.07, edge)
    for side in (-1, 1):  # the braces
        for tilt in (-0.78, 0.78):
            r.part("cube", side * (s / 2 + 0.02), s / 2, 0, 0.03, 1.1, 0.07, edge, rx=tilt)
    for k in range(6):  # straw over the top
        a = k * 1.05 + seed
        r.part("cube", math.cos(a) * 0.15, s + 0.02, math.sin(a) * 0.15, 0.5, 0.03, 0.06, STRAW, ry=a, rz=0.2)
    if seed % 2 == 0:
        with r.at(0.0, 0, 0.72, ry=0.4):
            _crate_box(r, 0.45)


def _long_crate(r, seed):
    """A long, low crate (tools, or arms), its lid nailed and strapped with iron, a dark brand burnt in
    its side; sometimes a sack slumped against it."""
    r.part("cube", 0, 0.3, 0, 0.7, 0.6, 1.4, WHITE, tex="wood_plank")
    edge = (60, 40, 26)
    for dx, dz in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r.part("cube", dx * 0.35, 0.3, dz * 0.7, 0.07, 0.62, 0.07, edge)
    r.part("cube", 0, 0.61, 0, 0.74, 0.04, 1.44, _dim(WHITE, 0.8), tex="wood_plank")  # the lid
    for z in (-0.5, 0.5):
        r.part("cube", 0, 0.3, z, 0.73, 0.64, 0.06, DARK_IRON)  # straps
    r.part("cube", 0.355, 0.32, 0, 0.01, 0.22, 0.3, (40, 30, 24))  # the brand
    r.part("cube", 0.355, 0.32, 0, 0.012, 0.06, 0.18, (88, 64, 44))
    if seed % 2 == 1:
        with r.at(0.55, 0, 0.3, ry=seed * 0.3):
            r.part("sphere", 0, 0.24, 0, 0.42, 0.5, 0.36, SACKCLOTH, rz=-0.25)
            r.part("cube", 0.02, 0.5, 0, 0.12, 0.08, 0.12, _dim(SACKCLOTH, 0.7))  # its tied neck


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


def cocoon(r, seed, broken=False, t=1.0):
    """A silk-wrapped bundle, the Loom Mother's larder, lashed to the floor with strands.
    Cut open, it is a torn husk with something's leftovers inside; `t` (0 the cut, 1 settled) flings
    the shreds out to it."""
    silk = (222, 218, 204)
    with r.at(0, 0, 0, ry=seed * 1.1):
        if broken:
            for k in range(4):
                a = k * 1.6
                _flung(r, t, k, 0.45, "sphere", math.cos(a) * 0.3, 0.12, math.sin(a) * 0.2, 0.5, 0.18, 0.3,
                       silk, ry=a)  # fmt: skip
            _flung(
                r, t, 4, 0.4, "sphere", 0.05, 0.08, 0, 0.22, 0.2, 0.2, BONE
            )  # a small skull among the shreds
            _break_dust(r, t, (196, 192, 180), 0.8)  # a puff of loose silk
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
REALM_VIOLET = ((84, 40, 116), (62, 34, 92))  # the realm's banners, everywhere


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


CHAR = (34, 22, 18)  # cloth burned black
SCORCH_RIM = (70, 36, 22)  # the brown ring round a burn


def banner(r, t, seed, burnt=False):
    """A tattered banner of the realm hung from a pole on the wall at local -X, its crest in gold thread.
    A `burnt` one (the Cinderhold's) is the same cloth after the fires: see `_burnt_banner`."""
    sway = math.sin(t * 0.7) * 0.03
    pole = (40, 30, 24) if burnt else (70, 50, 32)
    r.part("cyl", -0.9, 2.55, 0, 0.05, 1.0, 0.05, pole, rx=math.pi / 2)
    for end in (-0.5, 0.5):
        r.part("sphere", -0.9, 2.55, end, 0.08, 0.08, 0.08, _dim(BRASS, 0.5) if burnt else BRASS)
    cloth = REALM_VIOLET[seed % 2]
    if burnt:
        with r.at(-0.9, 2.5, 0, rz=sway):
            _burnt_banner(r, t, seed, cloth)
        return
    with r.at(-0.9, 2.5, 0, rz=sway):
        r.part("cube", 0, -0.75, 0, 0.03, 1.5, 0.8, cloth)
        for i, z in enumerate((-0.3, -0.1, 0.1, 0.3)):  # ragged hem
            r.part("cube", 0, -1.55 - (i % 2) * 0.08, z, 0.03, 0.2 + (i % 2) * 0.12, 0.16, cloth)
        realm_crest(r, (210, 180, 110))


def _burnt_banner(r, t, seed, cloth):
    """An old banner the fortress's fires have been at: the cloth gone dark with soot, one top corner
    torn from the pole and sagging, its lower edge burned away into ragged black tatters (a few
    tips still smouldering), burn holes ringed in brown, and the crest's thread tarnished.
    Drawn in the cloth's frame: hanging down from y = 0, its faces toward +-X."""
    soot = _dim(cloth, 0.5)
    r.part("cube", 0, -0.55, -0.07, 0.03, 1.1, 0.66, soot)  # the cloth still whole
    r.part("cube", 0, -0.7, 0.33, 0.03, 1.1, 0.14, soot, rx=0.12)  # the torn corner, sagging
    r.part("cube", 0, -1.18, 0, 0.032, 0.18, 0.8, _dim(cloth, 0.3))  # the scorched band above the hem
    ragged = (0.34, 0.12, 0.46, 0.2, 0.06, 0.38, 0.16)  # the hem's tatters, longest to barely there
    for i in range(7):  # what is left of the hem: overlapping, leaning, burned black at the tips
        k = (seed * 3 + i * 5) % 7
        z = -0.34 + i * 0.113 + (k % 3 - 1) * 0.015
        length = ragged[k]
        lean = (k % 3 - 1) * 0.12
        with r.at(0, -1.25, z, rx=lean):
            r.part("cube", 0, -length / 2, 0, 0.03, length, 0.1 + (k % 2) * 0.05, _dim(cloth, 0.3))
            r.part("cube", 0, -length, 0, 0.034, 0.06, 0.07, CHAR)
            if k % 3 == 0:
                glow = 0.6 + 0.4 * math.sin(t * 3 + i * 1.7)
                r.part("cube", 0, -length - 0.03, 0, 0.036, 0.03, 0.04, _dim(EMBER, glow), glow=True)
    for y, z, size, turn in ((-0.22, 0.2, 0.12, 0.6), (-1.0, -0.26, 0.1, -0.4), (-0.5, -0.35, 0.08, 0.9)):
        r.part("cube", 0, y, z, 0.036, size * 1.6, size * 1.3, SCORCH_RIM, rx=turn)  # a burn hole, ringed
        r.part("cube", 0, y, z, 0.04, size, size * 0.8, CHAR, rx=turn + 0.3)
        r.part("cube", 0, y - size * 0.3, z + size * 0.25, 0.04, size * 0.6, size * 0.7, CHAR, rx=-turn)
    realm_crest(r, (150, 118, 70))


def _arch_top(z, spring, half, off):
    """Height of a pointed arch's intrados over `z`: two arcs of radius `half + off`, centred `off`
    past the middle, springing at +-`half` and meeting at the apex. `spring` beyond its span."""
    if abs(z) >= half:
        return spring
    radius, u = half + off, abs(z) + off
    return spring + math.sqrt(max(radius * radius - u * u, 0.0))


def _pointed_arch(r, x, spring, half, off, n, depth, thick, rgb, tex="white"):
    """The voussoirs of a pointed arch in the plane x, facing +X: `n` a side along two arcs of radius
    `half + off` (their centres `off` past the middle), `thick` deep from intrados to extrados and `depth`
    thick through the wall. Its centre line springs at +-`half`. Returns the apex's height."""
    radius = half + off
    top = math.acos(off / radius)  # how far each arc turns, from its springing to the apex
    seg = radius * top / n * 1.1
    for side in (-1, 1):
        for i in range(n):
            a = (i + 0.5) * top / n
            r.part("cube", x, spring + radius * math.sin(a), side * (radius * math.cos(a) - off), depth, thick,
                   seg, _dim(rgb, 1.0 if i % 2 else 0.92), tex=tex, rx=side * (math.pi / 2 - a))  # fmt: skip
    return spring + radius * math.sin(top)


def _wheel(r, x, radius, n, thick, depth, rgb, tex="white"):
    """A ring of `n` blocks of radius `radius` round the origin in the plane x, facing +X."""
    seg = 2 * math.pi * radius / n * 1.08
    for i in range(n):
        a = 2 * math.pi * i / n
        r.part("cube", x, math.sin(a) * radius, math.cos(a) * radius, depth, thick, seg, rgb, tex=tex,
               rx=math.pi / 2 - a)  # fmt: skip


def realm_crest(r, rgb, cy=-0.82, scale=1.0, through=0.0):
    """The realm's crest, stitched on its banners and carved over its doors: a lone watchtower standing
    dark against a sun half sunk below the sea's horizon, rays fanning above, waves beneath, all
    inside a heater shield's border. Drawn flat on a face toward +X, centred `cy` up it, in the thread
    colour `rgb` (the tower in its shadow). With `through` (a thickness), it is drawn as a slab that
    thick centred on x = 0 instead, so one crest shows on both faces of a cloth or a block."""
    k = scale
    dark = _dim(rgb, 0.32)
    x0, depth = (0.0, through) if through else (0.02, 0.02)

    def flat(lift, y, z, w, h, rgb_, rx=0.0):
        r.part(
            "cube",
            x0 + lift * (0 if through else 1),
            cy + y * k,
            z * k,
            depth + lift * 2,
            h * k,
            w * k,
            rgb_,
            rx=rx,
        )

    # The shield: a straight top, upright sides and two edges sweeping in to its point.
    flat(0, 0.42, 0, 0.62, 0.04, rgb)
    for side in (-1, 1):
        flat(0, 0.17, side * 0.29, 0.04, 0.5, rgb)
        flat(0, -0.28, side * 0.15, 0.04, 0.42, rgb, rx=side * 0.62)
    # The horizon, and the sun sinking into it: a half disc built up in thin courses.
    flat(0, 0.0, 0, 0.5, 0.035, rgb)
    radius = 0.19
    for i in range(4):
        y = 0.04 + i * 0.045
        half = math.sqrt(max(radius * radius - (y - 0.02) ** 2, 0.0))
        flat(0.001, y, 0, half * 2, 0.047, rgb)
    for i in range(5):  # its rays
        a = math.pi * (i + 1) / 6
        r.part(
            "cube",
            x0,
            cy + math.sin(a) * 0.27 * k,
            math.cos(a) * 0.27 * k,
            depth,
            0.08 * k,
            0.024 * k,
            rgb,
            rx=math.pi / 2 - a,
        )
    # The watchtower before the sun: a tapering body, a jutting parapet, three merlons, a lit slit.
    flat(0.01, 0.08, 0, 0.12, 0.16, dark)
    flat(0.01, 0.2, 0, 0.1, 0.1, dark)
    flat(0.01, 0.265, 0, 0.14, 0.03, dark)
    for z in (-0.05, 0.0, 0.05):
        flat(0.01, 0.3, z, 0.028, 0.04, dark)
    flat(0.015, 0.17, 0, 0.02, 0.05, rgb)  # the window slit, lit by the sun behind
    # Two waves under the horizon.
    for row, y in enumerate((-0.07, -0.14)):
        for i in range(3 - row):
            z = (-0.12 + i * 0.12) if row == 0 else (-0.06 + i * 0.12)
            flat(0, y, z, 0.1, 0.022, rgb, rx=0.35 if i % 2 else -0.35)


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


def urn(r, seed, broken=False, t=1.0):
    """A clay pot; smashed, a few curved shards, which `t` (0 the blow, 1 settled) flings out."""
    clay = (150, 92, 60) if seed % 2 else (126, 110, 90)
    if broken:
        for i in range(5):
            a = i * 1.3 + seed
            _flung(r, t, i, 0.4, "sphere", math.cos(a) * 0.3, 0.04, math.sin(a) * 0.3, 0.22, 0.06, 0.16, clay,
                   ry=a)  # fmt: skip
        _flung(r, t, 5, 0.12, "cyl", 0, 0.06, 0, 0.3, 0.12, 0.3, clay)
        _break_dust(r, t, clay, 0.7)
        return
    with r.at(((seed * 13) % 5 - 2) * 0.1, 0, ((seed * 17) % 5 - 2) * 0.1):
        r.part("sphere", 0, 0.35, 0, 0.6, 0.62, 0.6, clay)
        r.part("cyl", 0, 0.7, 0, 0.3, 0.16, 0.3, clay)
        r.part("cyl", 0, 0.79, 0, 0.38, 0.05, 0.38, clay)
        r.part("cyl", 0, 0.4, 0, 0.62, 0.05, 0.62, tuple(c - 30 for c in clay))  # painted band


def warden_altar(r, taken, t, style="warden"):
    """A stepped altar before a stone statue of the Ashen Warden, who offers a floating key above his
    cupped hands. Faces +X; the statue stands at the back of the tile. `style` "idol" is the prison
    chapel's: one of its faceless old gods stands behind the altar instead, palms raised to the key."""
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
    if style == "idol":
        prison_models.altar_idol(r)
    else:
        _warden_statue(r, taken, t)
    if not taken:  # the key hovers just above his offered hands
        bob = math.sin(t * 1.6) * 0.04
        with r.at(0.3, 2.02 + bob, 0, ry=t * 0.8):
            r.part("sphere", 0, 0, 0, 0.16, 0.16, 0.16, (255, 150, 60), glow=True)
            with r.at(0, 0, 0, s=0.32):
                key(r, "warden_key", KEY_STYLES["warden_key"][1], t)


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
    "ward": (240, 170, 90),
    "rift_lance": (255, 226, 150),
    "bellward": (220, 200, 140),
    "mortar_shard": (150, 210, 190),
}


def spell_orb(r, id_, t):
    """Inventory preview for a known spell: a glowing orb in the spell's colour (fire spells burn as a
    fireball)."""
    rgb = SPELL_ORB.get(id_, WHITE)
    if id_ in FIRE_SPELLS:
        fireball(r, rgb, t, 2.0)
        return
    if id_ == "thunder":
        forge_models.thunder_orb(r, t)
        return
    if id_ == "motes":
        forge_models.motes_orb(r, t)
        return
    if id_ == "mend":
        mend_orb(r, t)
        return
    if id_ == "lumen":
        lumen_orb(r, t)
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
#   follow - carried through past the target (overshooting a touch, then settling): a full cut
#            carries the arm on out of the view, low or to the far side, as a real one would,
# then it eases part of the way home (to SETTLE between follow and rest) as the swing ends, and the
# view's PoseBlend (player/view_blend.py) carries it the rest of the way, slowing as it arrives, after
# the swing. The wind -> strike leg accelerates, so swings snap rather than float.

REST = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
MOTIONS = {
    # Light cuts: high right, down across to the low left.
    "slash": (
        (-0.08, 0.26, 0.3, 0.45, 0.4, 0.5),
        (0.16, -0.04, -0.16, -0.6, -0.4, -1.25),
        (0.0, -0.42, -0.72, -1.15, -0.75, -1.3),
    ),
    # The katana's cut: cocked up over the right shoulder with the blade in view, then drawn down across
    # the whole view on one diagonal, edge first, and carried on out low on the left.
    "katana_cut": (
        (-0.15, 0.22, 0.08, 0.67, 0.01, 0.15),
        (0.22, -0.14, -0.26, 0.34, 0.27, -0.43),
        (0.17, -0.5, -0.75, -1.22, -0.66, -1.03),
    ),
    # The reverse cut (the long katanas' heavy): the katana's cut mirrored, cocked up over the left
    # shoulder with the blade in view and cut down across to the low right, the wrist rolling over
    # through the cut so the edge still leads.
    "slash_left": (
        (-0.15, 0.22, -0.46, -1.07, -1.36, 0.01),
        (0.2, -0.11, -0.22, 0.18, -0.52, -0.62),
        (0.15, -0.5, 0.17, 1.48, 0.11, -1.32),
    ),
    # A flat arc from right to left, the whole arm turning with it.
    "sweep": (
        (-0.04, 0.04, 0.42, 1.0, 0.75, -0.4),
        (0.08, 0.03, -0.16, 0.2, -0.45, -1.0),
        (-0.06, -0.16, -0.88, -0.9, -1.1, -0.7),
    ),
    # Overhead: raised high over the shoulder, then straight down through the target. The arm drops
    # with the blow rather than the head tipping far past level, which would break the wrist.
    "chop": (
        (-0.12, 0.26, -0.04, 0.0, 0.1, 0.95),
        (0.18, -0.06, -0.12, 0.0, -0.05, -0.9),
        (0.12, -0.61, -0.14, 0.0, -0.1, -1.15),
    ),
    "slam": (
        (-0.12, 0.28, -0.06, 0.0, 0.1, 1.05),
        (0.16, -0.22, -0.12, 0.0, 0.0, -1.0),
        (0.14, -0.65, -0.14, 0.0, 0.0, -1.15),
    ),
    # The katana's lunge: the body carries the point in (the attack's `lunge`), so the arm drives on
    # only a short way, kept bent off to the right, the point angled in to the middle of the view.
    "thrust": (
        (-0.13, 0.13, -0.05, 0.1, -0.41, -1.0),
        (0.23, 0.03, -0.09, 0.0, -0.42, -1.02),
        (0.19, 0.0, -0.09, 0.0, -0.39, -1.0),
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
    "bash": (
        (-0.1, 0.1, 0.05, 0.3, 0.1, 0.4),
        (0.25, 0.0, -0.1, -0.2, -0.1, -0.9),
        (0.2, -0.05, -0.12, -0.3, -0.2, -1.1),
    ),
    # Axes swing their weight: the head is hauled up behind the shoulder and falls through the
    # target bit first, biting low rather than sliding across like a sword's cut.
    "hew": (  # a falling diagonal chop from over the right shoulder
        (-0.12, 0.26, 0.18, 0.25, 0.2, 1.1),
        (0.18, -0.1, -0.1, -0.15, -0.12, -0.9),
        (0.1, -0.59, -0.42, -0.25, -0.3, -1.1),
    ),
    "cleave": (  # the whole body behind it: wound far back overhead, buried low with a hard stop
        (-0.16, 0.32, -0.02, 0.0, 0.05, 1.4),
        (0.2, -0.18, -0.1, 0.0, -0.05, -1.0),
        (0.16, -0.67, -0.12, 0.0, -0.05, -1.2),
    ),
    # Hammers and maces: a short, heavy overhand blow that drops straight onto the target.
    "pound": (
        (-0.1, 0.22, 0.0, 0.0, 0.05, 0.9),
        (0.2, -0.12, -0.08, 0.0, 0.0, -0.8),
        (0.14, -0.51, -0.1, 0.0, 0.0, -0.95),
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
        (0.25, -0.25, -0.1, 0.0, 0.0, -1.1),
        (0.2, -0.45, -0.1, 0.0, 0.0, -1.0),
    ),
}


def _lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


def _ease_out_back(k, overshoot=1.2):
    """Eases out past 1 and settles back: a blade carried through its target that stops itself."""
    k = min(max(k, 0.0), 1.0) - 1
    return 1 + (overshoot + 1) * k**3 + overshoot * k**2


SETTLE = 0.5  # how far from the follow-through toward rest a swing has come back when it ends
WIND_AT = 0.7  # the fraction of the way to the blow at which a swing is fully wound up
# Katana cuts wind up sooner and spend longer on the cut itself, so the blade is seen sweeping across.
CUT_WIND_AT = {"katana_cut": 0.5, "slash_left": 0.5}


def _settle(motion):
    """The pose offsets a motion ends on, part way home: the view blends on from there to rest."""
    follow = MOTIONS.get(motion, MOTIONS["slash"])[2]
    return _lerp(follow, REST, SETTLE)


def _motion(motion, p, hit_at=0.4):
    """Pose offsets (dx, dy, dz, rx, ry, rz) for one attack motion at phase p (0..1), landing at hit_at.
    It ends at `_settle(motion)`, not at rest: the rest of the way home is the view's to blend."""
    wind, strike, follow = MOTIONS.get(motion, MOTIONS["slash"])
    wind_at = hit_at * CUT_WIND_AT.get(motion, WIND_AT)
    follow_at = hit_at + (1 - hit_at) * 0.35
    if p < wind_at:
        return _lerp(REST, wind, _ease(p / wind_at))
    if p < hit_at:
        return _lerp(wind, strike, _ease_in((p - wind_at) / (hit_at - wind_at)))
    if p < follow_at:
        return _lerp(strike, follow, _ease_out_back((p - hit_at) / (follow_at - hit_at)))
    # Gathering speed as it leaves the follow-through, so the view's blend home (fastest as it
    # starts, then slowing) carries straight on from it.
    return _lerp(follow, _settle(motion), _ease_in((p - follow_at) / (1 - follow_at)))


# Where the hands close on each weapon's grip (model y), the first for one hand, both for two.
GRIPS = {
    "sword": (0.0, -0.12),
    "greatsword": (0.0, -0.24),
    "katana": (-0.02, -0.17),
    "whip": (-0.04, -0.14),
    "mace": (-0.18, -0.18),
    "club": (-0.15, -0.15),
    "axe": (-0.2, 0.02),
    "hammer": (-0.2, 0.02),
}
NODACHI_GRIP = (0.05, -0.3)
# A two-handed axe or hammer: the leading (right) hand high on the haft, under the head, and the left
# just below it, as a woodsman holds a felling axe.
HEADED_GRIP = (0.02, -0.2)

# The player is one of the Ashen: their bare skin is dark, sooty grey ash. The forearm carries the `ash_skin`
# texture's grain and streaks; the hands are the same ash, drawn plain so the fingers stay clear at 320x240.
ASHEN = (96, 94, 96)
ASH_ARM = (88, 86, 88)  # the forearm: its grain lightens it, so a touch darker than the hands
# Sleeve colour and trim for each body armor (None: the bare ashen forearm). Dull, dark tones, as the PS1
# lit them.
SLEEVES = {
    None: (ASH_ARM, (118, 118, 128)),
    "padded_coat": ((100, 86, 64), (70, 58, 42)),
    "ringmail": ((112, 114, 120), (58, 60, 66)),
    "lamellar_vest": ((112, 44, 36), (170, 146, 80)),
    "brigandine": ((118, 36, 34), (168, 168, 176)),
    "blackened_plate": ((48, 48, 54), (138, 138, 148)),
}
GLOVES = {
    None: (ASHEN, (118, 118, 128)),
    "leather_gloves": ((86, 58, 38), (58, 38, 26)),
    "chain_mitts": ((128, 130, 138), (78, 80, 88)),
    "iron_gauntlets": ((108, 108, 118), (168, 168, 178)),
}
FOREARM = 0.15  # the forearm's girth where it leaves the view; it tapers to TAPER of that at the wrist
REACH = 1.3  # how far past the elbow (wrist 0, elbow 1) the forearm is drawn, out of the view
# Where the elbow lies from the wrist (forward, up, outward): well below the view, so the forearm rises
# steeply from the bottom of the screen into the hand.
ELBOW = (-0.12, -0.8, 0.3)


def _limb(r, a, b, thick, rgb, kind="cube", tex="white"):
    """A box from point a to point b (camera space), `thick` across. As a `frustum` it is widest at a
    and narrows toward b."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-6:
        return
    yaw = math.atan2(-dz, dx)
    pitch = math.asin(max(-1.0, min(1.0, dy / length)))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    if kind == "cube":
        r.part("cube", *mid, length, thick, thick, rgb, tex=tex, ry=yaw, rz=pitch)
        return
    with r.at(*mid, ry=yaw, rz=pitch):  # the shape's +Y turned onto the limb's line
        r.part(kind, 0, 0, 0, thick, length, thick, rgb, tex=tex, rz=-math.pi / 2)


def _girth(k, thick):
    """The forearm's thickness `k` of the way from wrist (0) to elbow (1)."""
    return thick * (shapes.TAPER + (1 - shapes.TAPER) * k / REACH)


WRIST_GIVE = 0.25  # how far the forearm runs on along the hand's heel, rather than down to ELBOW


def _elbow(wrist, side, heel=None, give=WRIST_GIVE):
    """Where the forearm drawn to `wrist` comes from: below the view (ELBOW), bent toward the line the
    heel of the hand points along (`heel`, a unit vector), as a wrist bends only so far."""
    e = (ELBOW[0], ELBOW[1], ELBOW[2] * side)
    if heel:
        n = math.sqrt(sum(c * c for c in e))
        d = [a / n * (1 - give) + b * give for a, b in zip(e, heel, strict=True)]
        k = n / (math.sqrt(sum(c * c for c in d)) or 1.0)
        e = _within_bend(tuple(c * k for c in d), heel, n)
    return (wrist[0] + e[0], wrist[1] + e[1], wrist[2] + e[2])


WRIST_BEND = math.radians(50)  # the most a wrist bends off its forearm's line, even mid-swing
ELBOW_DROP = 0.3  # the forearm always falls at least this steeply (the sine of its slope) to the elbow


def _within_bend(e, heel, n):
    """The forearm `e` (wrist to elbow, length n) swung toward the heel's line until the wrist bends no
    more than WRIST_BEND: in a hard swing the whole forearm turns with the hand, not the wrist alone.
    It turns only so far that it still rises from below the view (ELBOW_DROP); past that the wrist
    takes the rest."""
    u = [c / n for c in e]
    cos = max(-1.0, min(1.0, sum(a * b for a, b in zip(u, heel, strict=True))))
    bend = math.acos(cos)
    if bend <= WRIST_BEND:
        return e
    perp = [a - cos * b for a, b in zip(u, heel, strict=True)]
    pn = math.sqrt(sum(c * c for c in perp))
    if pn < 1e-6:
        return e

    def at(angle):  # the direction `angle` off the heel, in the plane of u and the heel
        s, c = math.sin(angle), math.cos(angle)
        return [h * c + p / pn * s for h, p in zip(heel, perp, strict=True)]

    lo, hi = WRIST_BEND, bend  # find the least bend whose forearm still falls steeply enough
    if at(lo)[1] > -ELBOW_DROP:
        for _ in range(16):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if at(mid)[1] > -ELBOW_DROP else (lo, mid)
        lo = hi
    return tuple(c * n for c in at(lo))


def arm(r, wrist, side, body=None, gloves=None, heel=None, give=WRIST_GIVE):
    """A forearm rising from below the view to `wrist` (camera space), where the heel of the hand
    meets it: one smooth taper from below the elbow to the wrist, the same girth in any armor. Bare,
    it is the player's sooty ash; in body armor, its sleeve's colour. Gloves sheathe the wrist end
    close-fitting. side is +1 for the right arm, -1 for the left. Returns the hand's colour and shade."""
    elbow = _elbow(wrist, side, heel, give)
    sleeve, _trim = SLEEVES.get(body, SLEEVES[None])
    hand, shade = GLOVES.get(gloves, GLOVES[None])
    tex = "ash_skin" if body is None else "white"
    _limb(r, _lerp(wrist, elbow, REACH), wrist, FOREARM, sleeve, "frustum", tex)
    if gloves:  # the glove's cuff, hugging the wrist
        cuff = 0.3 if gloves == "iron_gauntlets" else 0.22
        _limb(r, _lerp(wrist, elbow, cuff), wrist, _girth(cuff, FOREARM) + 0.008, hand, "frustum")
    return hand, shade


# The closed hand, in its own frame: the grip runs along +Y through the origin (index finger toward +Y),
# the back of the hand faces +Z (mirrored for the left hand) and the heel of the hand points -X, to the
# wrist. The fingers wrap the grip on a ring round it: each rises from its knuckle on that ring and
# curls through three joints.
FINGERS = (
    (0.047, 1.0, 1.0),
    (0.015, 1.1, 1.04),
    (-0.017, 1.02, 0.97),
    (-0.047, 0.84, 0.88),
)  # y, length, girth
BONES = (0.058, 0.04, 0.03)  # a finger's three bones, knuckle to tip
CURL = (1.44, 1.08, 0.74)  # how far each joint bends, wrapping the finger round the grip
CLENCH = (1.55, 1.5, 1.2)  # with nothing in it: the fingertips curl back into the palm
KNUCKLE = (0.034, 0.036)  # (x, z) of the knuckles, at the top of the ring the fingers wrap
WRIST_AT = (-0.155, 0.0, 0.032)  # where the forearm meets the heel of the hand
FIST_SCALE = 1.2  # a little over life, so the fingers read at 320x240
FINGER = 0.036  # an index finger's thickness


def _digit(r, bones, thick, rgb, bends, side=1, axis="ry", plate=None, ring=None):
    """A finger from its knuckle at the current origin, pointing +X: for each bone, its joint turns
    by the next of `bends` (about Y, mirrored by `side`, to curl it round a grip; about Z to cup an open
    palm), a rounded joint, then the bone itself, each a little thinner than the last. `plate` lays an
    iron plate of that colour on each bone's back, `ring` a band of mail."""
    back = (0, 0, side) if axis == "ry" else (0, -1, 0)  # which way the bones' backs face
    with ExitStack() as stack:
        for k, (ln, bend) in enumerate(zip(bones, bends, strict=True)):
            stack.enter_context(r.at(**{axis: bend * (side if axis == "ry" else 1)}))
            j = thick * 1.1
            r.part("sphere", 0, 0, 0, j, j, j, _bright(rgb, 1.08, 4) if k == 0 else rgb)
            r.part("cyl", ln / 2, 0, 0, thick, ln, thick, rgb, rz=-math.pi / 2)
            o = thick / 2 + 0.004
            if plate:
                r.part("cube", ln / 2, back[1] * o, back[2] * o, ln * 0.86, *_plate_size(axis, thick), plate)
            if ring:
                r.part("cyl", ln * 0.55, 0, 0, thick * 1.16, ln * 0.3, thick * 1.16, ring, rz=-math.pi / 2)
            stack.enter_context(r.at(ln, 0, 0))
            thick *= 0.88


def _plate_size(axis, thick):
    return (thick * 1.15, 0.01) if axis == "ry" else (0.01, thick * 1.15)


# A hand on a weapon holds it as a sword is held, in a handshake: the front of the fist (the fingers'
# middle bones) toward the edge, which leads every swing along +X, so the heel of the hand trails it
# and the grip crosses the palm on the slant (the heel dropped GRIP_TILT toward the pommel). The hand
# never turns about the grip; the forearm follows it (`arm`'s `heel`).
GRIP_TURN = (0.0, 0.8)


def _hand_turn(r, side):
    """How to turn the grip frame at hand (grip along +Y) so the heel of the hand faces the forearm:
    a turn about the grip, then a tilt dropping the heel toward the pommel, as a grip crosses the palm
    on the slant. Worked out from where the elbow lies, so the hand always rides on its wrist."""
    m = r.top
    ex, ey, ez = ELBOW[0], ELBOW[1], ELBOW[2] * side
    lx = m[0] * ex + m[4] * ey + m[8] * ez
    ly = m[1] * ex + m[5] * ey + m[9] * ez
    lz = m[2] * ex + m[6] * ey + m[10] * ez
    tilt = 0.55 * math.atan2(-ly, math.hypot(lx, lz))
    return math.atan2(lz, -lx), max(-0.3, min(0.75, tilt))


@contextmanager
def _in_hand(r, side, turn=None):
    a, tilt = turn or _hand_turn(r, side)
    with r.at(ry=a, rz=tilt, s=FIST_SCALE):
        yield


def hand_wrist(r, side, turn=None):
    """The camera-space wrist of a hand closing on the grip at the current frame (see `fist`), the
    turn that hand takes (`turn`, or worked out to face the elbow) and the way its heel points, along
    the forearm (a unit vector): draw the arm to the first along the last, then the fist with the
    second."""
    turn = turn or _hand_turn(r, side)
    with _in_hand(r, side, turn), r.at(WRIST_AT[0], WRIST_AT[1], WRIST_AT[2] * side):
        m = r.top
        with r.at(-1.0, 0, 0):
            h = r.top
    heel = (h[3] - m[3], h[7] - m[7], h[11] - m[11])
    n = math.sqrt(sum(c * c for c in heel)) or 1.0
    return (m[3], m[7], m[11]), turn, tuple(c / n for c in heel)


def fist(r, hand, shade, gloves=None, side=1, turn=None, curl=CURL):
    """A closed human hand round the grip at the origin of the current (weapon) frame, grip along +Y:
    the palm against it, four fingers of human lengths, each a chain of rounded bones curling round it
    (the index nearest the guard), and the thumb from the heel of the hand over the index and middle
    fingers. It turns about the grip to ride on its forearm (`turn`, from `hand_wrist`). Gauntlets plate
    each bone and the back of the hand; mitts band the fingers in mail. side -1 mirrors it (the left)."""
    with _in_hand(r, side, turn):
        _fist(r, hand, shade, gloves, side, curl)


def _fist(r, hand, shade, gloves, side, curl):
    iron = gloves == "iron_gauntlets"
    mitt = gloves == "chain_mitts"
    fat = 1.12 if mitt else 1.05 if iron else 1.0
    kx, kz = KNUCKLE
    # The palm, broad across the knuckles and narrowing to the heel, then the heel's rounded mound and
    # the fleshy root of the thumb under the index side.
    r.part("frustum", -0.058, 0, kz * side, 0.13 * fat, 0.19, 0.05 * fat, hand, rz=math.pi / 2)
    r.part("sphere", -0.12, -0.006, 0.03 * side, 0.08, 0.1 * fat, 0.052 * fat, hand)
    r.part("sphere", -0.08, 0.038, 0.004 * side, 0.09, 0.06 * fat, 0.05 * fat, _dim(hand, 0.94))
    for i, (y, ln, th) in enumerate(FINGERS):
        tone = hand if i % 2 == 0 else _dim(hand, 0.88)  # neighbours apart, so each finger reads
        x = kx - (0.01 if i == 3 else 0.0) + (0.004 if i == 1 else 0.0)
        with r.at(x, y, kz * side):
            _digit(
                r, [b * ln for b in BONES], FINGER * th * fat, tone, curl, side,
                plate=shade if iron else None, ring=shade if mitt else None,
            )  # fmt: skip
    # The thumb: up from its root over the grip, across the index and middle fingers.
    joints = [(-0.1, 0.03, -0.004), (-0.048, 0.056, -0.036), (-0.004, 0.056, -0.062), (0.036, 0.034, -0.068)]
    joints = [(x, y, z * side) for x, y, z in joints]
    for a, b, w in zip(joints, joints[1:], (0.048 * fat, 0.036 * fat, 0.031 * fat), strict=False):
        r.part("sphere", *a, w * 1.1, w * 1.1, w * 1.1, hand)
        _limb(r, a, b, w, hand, "cyl")
        if iron:
            _limb(r, a, b, w * 0.8, shade, "cube")
    if iron:  # a plate over the back of the hand, its knuckle edge bright
        r.part("frustum", -0.055, 0, (kz + 0.03) * side, 0.14, 0.17, 0.014, shade, rz=math.pi / 2)
        r.part("cyl", kx - 0.008, 0, (kz + 0.03) * side, 0.02, 0.13, 0.02, (196, 196, 206))
    elif gloves == "leather_gloves":  # a seam down the back
        r.part("cube", -0.055, 0, (kz + 0.026) * side, 0.17, 0.006, 0.004, shade)


def _pose_at(r, pose, side):
    """Enters a weapon pose (x, y, z, rx, ry, rz) mirrored for the left hand."""
    x, y, z, rx, ry, rz = pose
    return r.at(x, y, z * side, rx=rx * side, ry=ry * side, rz=rz, s=0.7)


def _pose_vector(pose, side, v):
    """A model-space vector `v` turned into camera space by `pose` (rot_y * rot_z * rot_x, as
    `_pose_at` enters it), unscaled."""
    _x, _y, _z, rx, ry, rz = pose
    rx, ry = rx * side, ry * side
    x, y, z = v
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    return x, y, z


def _weapon_point(pose, side, ly):
    """Camera-space position of a point `ly` up the weapon's grip in `pose` (for placing wrists)."""
    x, y, z = pose[:3]
    v = _pose_vector(pose, side, (0.0, ly * 0.7, 0.0))
    return x + v[0], y + v[1], z * side + v[2]


def _grips(item):
    if item.id == "nodachi":
        return NODACHI_GRIP
    if item.two_handed and item.category in ("axe", "hammer"):
        return HEADED_GRIP
    return GRIPS.get(item.category, (0.0, -0.12))


def _heavy_look(item):
    return item.two_handed or item.category in ("greatsword", "hammer")


def weapon_view(r, player, bob, t=0.0, blends=None):
    """Both hands in first person: each holds its weapon, shield or spell, or is a bare fist. `blends`
    (a view_blend.ViewBlends kept from frame to frame) smooths the arms between one pose and the next
    and lets them trail the turning view; without it every frame stands alone."""
    blends = blends or view_blend.ViewBlends()
    inv = player.inventory
    armor = {"body": inv.body, "gloves": inv.hands}
    sprint = 1.0 if player.sprinting else max(0.0, 1 - player.since_sprint / 0.25)
    breath = math.sin(t * 1.7) * 0.006
    sway = blends.sway.update(player.yaw, player.pitch, t)
    view = (blends, t, sway)
    if inv.two_handing():
        ward_embers(r, player, t)
        return _held_weapon(r, player, "right", bob + breath, sprint, armor, view, both=True)
    for hand in ("right", "left"):
        item = player.hand_item(hand)
        side = 1 if hand == "right" else -1
        if item.kind == "shield":
            shield_view(r, player, item, bob + breath, side, armor, view)
        elif item.kind == "spell":
            spell_hand_view(r, player, bob + breath + sway[1] * SWAY_SHIFT, side, armor, t)
        elif item.category == "fists":
            fist_view(r, player, hand, bob + breath, armor, view)
        else:
            _held_weapon(r, player, hand, bob + breath, sprint, armor, view)
    ward_embers(r, player, t)
    return None


SWORD_DROP = 0.1  # how much lower than other one-handers a sword is carried
SWAY_SHIFT = 0.8  # metres the arms shift per radian they trail the view


def _swayed(pose, side, sway):
    """A weapon pose shifted and turned by the view's sway (yaw lag, pitch lag): the same way in the
    camera for either hand, so the pose's mirrored z and ry take `side`."""
    x, y, z, rx, ry, rz = pose
    yaw_lag, pitch_lag = sway
    return (x, y + pitch_lag * SWAY_SHIFT, z + yaw_lag * SWAY_SHIFT * side, rx, ry + yaw_lag * side, rz)


def _blend_key(player, hand, charge):
    """What the arm is doing, and how long blending into it from the last pose takes."""
    if player.swing_t is not None and player.swing_hand == hand:
        return ("swing", player.swing_id), view_blend.INTO_SWING
    if charge > 0:
        return "charge", view_blend.INTO_CHARGE
    return "idle", view_blend.RECOVER * weapons.tempo(player.hand_item(hand))


def _held_weapon(r, player, hand, bob, sprint, armor, view=None, both=False):
    blends, t, sway = view or (view_blend.ViewBlends(), 0.0, (0.0, 0.0))
    item = player.hand_item(hand)
    side = 1 if hand == "right" else -1
    heavy = _heavy_look(item)
    x, y, z = 0.9, (-0.25 if heavy else -0.19), (0.2 if both else (0.3 if heavy else 0.28))
    if item.category == "sword":  # a one-handed sword rides lower and wider, so less of the arm shows
        y, z = y - SWORD_DROP, z + 0.04
    rx, ry, rz = 0.25, 0.7, -0.55
    dx = dy = dz = drx = dry = drz = 0.0
    swinging = player.swing_t is not None and player.swing_hand == hand
    charge = player.charge_frac if (player.swing_t is None and player.charge_hand == hand) else 0.0
    bob -= bob * 0.6 * charge  # winding up a heavy steadies the bob
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
    key, dur = _blend_key(player, hand, charge)
    x, y, z, rx, ry, rz = blends.hands[hand].apply(key, (x, y, z, rx, ry, rz), t, dur)
    pose = _swayed((x, y + bob, z, rx, ry, rz), side, sway)
    grips = _grips(item)
    with _pose_at(r, pose, side), r.at(0, grips[0], 0):
        wrist, turn, heel = hand_wrist(r, side, GRIP_TURN)
    hand_rgb, shade = arm(r, wrist, side, armor["body"], armor["gloves"], heel)
    if both:
        with _pose_at(r, pose, side), r.at(0, grips[1], 0):
            lwrist, lturn, lheel = hand_wrist(r, -1, GRIP_TURN)
        # The second hand's arm comes up from the left, across the body: its wrist bends further.
        lhand, lshade = arm(r, lwrist, -1, armor["body"], armor["gloves"], lheel, WRIST_GIVE * 0.3)
    phase = player.swing_phase if swinging else None
    if swinging and item.category in TRAILS:
        rest = tuple(a - b for a, b in zip(pose, (dx, dy, dz, drx, dry, drz), strict=True))
        art = player.swing_art  # an art's blow smears in its own light (the Pale Crescent's pale blue)
        _swing_trail(r, item, player.attack, phase, rest, side, art.rgb if art else None)
    with _pose_at(r, pose, side):
        weapon(r, item.id, phase)
        with r.at(0, grips[0], 0):
            fist(r, hand_rgb, shade, armor["gloves"], side, turn)
        if both:
            with r.at(0, grips[1], 0):
                fist(r, lhand, lshade, armor["gloves"], -1, lturn)


TRAILS = {"sword", "greatsword", "katana", "axe"}  # edged weapons leave a smear through the blow
# Weapons whose striking head is built with its edge (or face) on +Z, as models of its kind are, and
# turned a quarter about the haft by `weapon` so it leads along +X: the way every swing travels.
HEADED = {
    "hatchet", "bearded_axe", "butcher_cleaver", "war_hammer", "great_iron_hammer", "slagbreaker",
    "torch_greathammer",
}  # fmt: skip
TRAIL_LAG = 0.08  # how far back (in swing phase) the smear reaches
TRAIL_GHOSTS = 6
# A katana's long, fast cut leaves a crescent of light where its outer blade passed: many ghosts, each
# as wide as the gap to the next, so they close up into one sweep rather than a comb of slivers.
TRAIL_STYLE = {"katana": (0.16, 32)}  # category: (lag, ghosts)
CRESCENT = (0.45, 0.97)  # the stretch of the blade (fractions of its length) a crescent smear covers
TRAIL_MAX_W = 0.3  # the widest a crescent's ghost grows, in model units


def _swing_trail(r, item, a, phase, rest, side, tint=None):
    """A fading smear behind an edged weapon as it cuts: a fan of ghost blades between where it is and
    where it was a moment ago, dimmer the further back. Only around the blow, and drawn first so the
    weapon covers them. It follows the motion, so a reverse cut smears the other way; `tint` colours
    it (an art's light)."""
    wind_at = a.hit_at * (CUT_WIND_AT.get(a.motion, WIND_AT) + 0.1)
    follow_at = a.hit_at + (1 - a.hit_at) * 0.15
    if not wind_at < phase < follow_at:
        return
    lag, ghosts = TRAIL_STYLE.get(item.category, (TRAIL_LAG, TRAIL_GHOSTS))
    length = WEAPON_LEN.get(item.id, 1.0) * 0.85
    rgb = (255, 170, 90) if item.element == "fire" else (210, 225, 255) if item.element else (205, 205, 215)
    rgb = tint or rgb
    now = _motion(a.motion, phase, a.hit_at)
    then = _motion(a.motion, max(phase - lag, wind_at), a.hit_at)
    headed = item.id in HEADED  # an axe smears only where its bit passes, not along the haft
    filled = item.category in TRAIL_STYLE
    if filled:  # how far apart neighbouring ghosts lie across the crescent's middle, in model units
        mid = 0.2 + length * sum(CRESCENT) / 2
        ends = (tuple(b + o for b, o in zip(rest, m, strict=True)) for m in (now, then))
        gap = math.dist(*(_weapon_point(e, side, mid) for e in ends)) / ghosts / 0.7
        w = min(max(gap * 1.6, 0.035), TRAIL_MAX_W)
    for i in range(ghosts, 0, -1):  # the oldest (dimmest) first
        k = i / ghosts
        off = _lerp(now, then, k)
        pose = tuple(b + o for b, o in zip(rest, off, strict=True))
        with _pose_at(r, pose, side):
            col = _dim(rgb, 0.8 - 0.55 * k)
            # Each ghost is a pale sliver where the edge (on +X, `edge_turn`) passed: together they streak
            # the plane the cut travels through.
            if headed:
                r.part("blade", 0.1, length * 0.78, 0, 0.04, length * 0.5, 0.004, col, glow=True)
            elif filled:  # trailing back from the edge (-X), as wide as the gap to the next ghost
                lo, hi = (0.2 + length * c for c in CRESCENT)
                col = _dim(rgb, 0.7 - 0.6 * k)
                r.part("blade", 0.07 - w / 2, (lo + hi) / 2, 0, w, hi - lo, 0.004, col, glow=True)
            else:
                r.part("blade", 0.05, 0.2 + length / 2, 0, 0.035, length * 0.9, 0.004, col, glow=True)


def fist_view(r, player, hand, bob, armor, view=None):
    """A bare hand: a jab straight forward or a hook from the outside."""
    blends, t, sway = view or (view_blend.ViewBlends(), 0.0, (0.0, 0.0))
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
        -0.23 + jab * 0.25,
        (0.37 - jab * 0.5 * (1 if motion != "hook" else 0) + out) * side,
    )
    key, dur = _blend_key(player, hand, charge)
    wx, wy, wz = blends.hands[hand].apply(key, wrist, t, dur)
    # Held as a sword hand is, closed on nothing (GRIP_TURN): thumb on top, the back of the hand out
    # and the knuckles forward, levelling to lead the punch as it goes out.
    frame = {"x": wx, "y": wy + bob + sway[1] * SWAY_SHIFT, "z": wz + sway[0] * SWAY_SHIFT}
    frame.update(rx=0.25 * side, ry=0.7 * side, rz=-0.55 + 1.2 * jab, s=0.7)
    with r.at(**frame):
        wrist, turn, heel = hand_wrist(r, side, GRIP_TURN)
    hand_rgb, shade = arm(r, wrist, side, armor["body"], armor["gloves"], heel)
    with r.at(**frame):
        fist(r, hand_rgb, shade, armor["gloves"], side, turn, curl=CLENCH)


def shield_view(r, player, item, bob, side, armor, view=None):
    """A shield on the forearm: carried at the side, brought to the centre while you block."""
    blends, t, sway = view or (view_blend.ViewBlends(), 0.0, (0.0, 0.0))
    hand = "right" if side > 0 else "left"
    (up,) = blends.shields[hand].apply(
        player.guarding, (1.0 if player.guarding else 0.0,), t, view_blend.GUARD
    )
    bob += sway[1] * SWAY_SHIFT
    jolt = max(0.0, 0.18 - player.since_block) * 0.8  # a blow knocks it back
    reel = player.guard_break_t * 0.5  # a broken guard flings it wide
    x = 0.85 - jolt - reel * 0.3
    y = -0.44 + bob + 0.3 * up - reel * 0.3
    z = (0.38 - 0.28 * up + reel * 0.3) * side + sway[0] * SWAY_SHIFT
    frame = {"ry": (-0.35 + 0.35 * up) * side, "rz": 0.1, "s": 0.75}
    gx, gy = SHIELD_GRIPS.get(item.id, (-0.09, 0.0))
    # The fist closes on the strap behind the shield, nearer the camera than it: raised, you see your grip.
    with r.at(x, y, z, **frame), r.at(gx, gy, 0, s=0.85 / 0.75):
        wrist, turn, _heel = hand_wrist(r, side)
    with r.at(x, y, z, **frame):
        shield(r, item.id)
    hand_rgb, shade = arm(r, wrist, side, armor["body"], armor["gloves"])
    with r.at(x, y, z, **frame), r.at(gx, gy, 0, s=0.85 / 0.75):
        fist(r, hand_rgb, shade, armor["gloves"], side, turn)


# Where the fist closes behind each shield (its frame: x toward the face, y up), at the strap.
SHIELD_GRIPS = {
    "buckler": (-0.08, 0.0),
    "round_shield": (-0.1, 0.0),
    "kite_shield": (-0.1, 0.05),
    "tower_shield": (-0.11, 0.05),
}


MEND_GOLD = (235, 225, 140)  # the heart of Mend's light, where the green warms to gold
MEND_LEAF = (90, 200, 110)
LUMEN_CORE = (255, 252, 230)
LUMEN_RAYS = 8  # as its scroll's rune and HUD icon: an eight-rayed star
MEND_SPARKS = 6


def _mend_sparks(r, t, count, reach, size, rise):
    """Mend's motes: rising in a slow spiral from below, paling to gold, gone at the top."""
    for i in range(count):
        k = (t * 0.45 + i / count) % 1.0
        a = i * 2.4 + k * 3.0
        rgb = _blend(MEND_LEAF, MEND_GOLD, k)
        s = size * (1 - k * 0.6)
        y = -rise * 0.5 + rise * k
        r.part("cube", math.cos(a) * reach, y, math.sin(a) * reach, s, s, s, _dim(rgb, 1 - k * 0.5),
               ry=a, glow=True)  # fmt: skip


def mend_orb(r, t):
    """Mend in Belongings: a cross of warm green-gold light turning slowly over a cup of six leaves of
    light, a soft green heart breathing inside it and motes of healing rising round it."""
    breath = 1 + 0.08 * math.sin(t * 1.8)
    r.part("sphere", 0, -0.3, 0, 0.3 * breath, 0.18 * breath, 0.3 * breath, _dim(MEND_LEAF, 0.7), glow=True)
    with r.at(0, 0.04 * math.sin(t * 1.3), 0, ry=t * 0.7):
        r.part("cube", 0, 0, 0, 0.2, 0.86, 0.2, MEND_GOLD, glow=True)  # the cross's upright
        r.part("cube", 0, 0.12, 0, 0.62, 0.2, 0.2, MEND_GOLD, glow=True)  # and its arm
        r.part("cube", 0, 0.12, 0, 0.26, 0.26, 0.26, (255, 250, 210), glow=True)  # where they meet
    for i in range(6):  # the cup of leaves, opening and closing a little as it breathes
        a = i * math.tau / 6 + t * 0.25
        with r.at(math.cos(a) * 0.36, -0.4, math.sin(a) * 0.36, ry=-a):
            r.part("cube", 0.08, 0.14, 0, 0.36, 0.06, 0.16, _dim(MEND_LEAF, 0.85 + 0.1 * (i % 2)),
                   rz=0.75 + 0.08 * breath, glow=True)  # fmt: skip
    _mend_sparks(r, t, MEND_SPARKS, 0.62, 0.1, 1.6)


def lumen_orb(r, t):
    """Lumen in Belongings: a small white sun, eight rays turning about it, long and short by turns
    and each breathing on its own beat, inside a slow ring of pale facets: the light you carry."""
    pulse = 1 + 0.06 * math.sin(t * 2.5)
    r.part("sphere", 0, 0, 0, 0.42 * pulse, 0.42 * pulse, 0.42 * pulse, LUMEN_CORE, glow=True)
    r.part("sphere", 0, 0, 0.2, 0.22, 0.22, 0.04, (255, 255, 255), glow=True)  # its white-hot heart
    with r.at(0, 0, 0, rz=t * 0.5):
        for i in range(LUMEN_RAYS):
            a = i * math.tau / LUMEN_RAYS
            ln = (0.5 if i % 2 == 0 else 0.3) * (1 + 0.15 * math.sin(t * 3 + i * 1.7))
            mid = 0.3 + ln / 2
            r.part("cube", math.cos(a) * mid, math.sin(a) * mid, 0, ln, 0.07, 0.07, LUMEN_CORE, rz=a,
                   glow=True)  # fmt: skip
    with r.at(0, 0, 0, rx=0.5, ry=-t * 0.35):  # the halo, tilted so it rings the sun
        for i in range(10):
            a = i * math.tau / 10
            r.part("cube", math.cos(a) * 0.95, 0, math.sin(a) * 0.95, 0.09, 0.09, 0.09,
                   _dim(SPELL_ORB["lumen"], 0.8 + 0.2 * math.sin(t * 2 + i)), ry=-a + 0.78, rx=0.6,
                   glow=True)  # fmt: skip


def _palm_mend(r, t, ready, cast):
    """Mend readied: a little cross of green-gold light over the palm, motes rising from the fingers;
    a cast throws them up in a burst."""
    if ready:
        with r.at(0.02, 0.15 + 0.008 * math.sin(t * 2), 0, ry=t * 0.8):
            r.part("cube", 0, 0, 0, 0.03, 0.12, 0.03, MEND_GOLD, glow=True)
            r.part("cube", 0, 0.018, 0, 0.088, 0.03, 0.03, MEND_GOLD, glow=True)
            r.part("cube", 0, 0.018, 0, 0.04, 0.04, 0.04, (255, 250, 210), glow=True)
    with r.at(0.03, 0.1, 0):
        _mend_sparks(r, t, 3, 0.05, 0.016, 0.14)
    if cast > 0:
        with r.at(0.03, 0.12 + 0.1 * (1 - cast), 0):
            _mend_sparks(r, t * 3, 4, 0.04 + 0.08 * (1 - cast), 0.022 * cast, 0.1)


def _palm_lumen(r, t, ready, cast):
    """Lumen readied: a little white sun cupped in the palm, its rays turning; a cast flares it."""
    if not ready and cast <= 0:
        return
    flare = 1 + 1.5 * cast
    with r.at(0.02, 0.12, 0, ry=t * 0.6):
        r.part("sphere", 0, 0, 0, 0.05 * flare, 0.05 * flare, 0.05 * flare, LUMEN_CORE, glow=True)
        for i in range(LUMEN_RAYS):  # rays fanning out over the palm, tipped up and down by turns
            with r.at(0, 0, 0, ry=i * math.tau / LUMEN_RAYS, rz=0.3 * (1 if i % 2 else -1)):
                ln = (0.055 if i % 2 == 0 else 0.035) * flare * (1 + 0.15 * math.sin(t * 4 + i))
                r.part("cube", 0.035 + ln / 2, 0, 0, ln, 0.008, 0.008, LUMEN_CORE, glow=True)
    if ready:  # three sparks wheeling round it
        for i in range(3):
            a = -t * 2.5 + i * math.tau / 3
            r.part("cube", 0.02 + math.cos(a) * 0.09, 0.12 + 0.02 * math.sin(t * 3 + i), math.sin(a) * 0.09,
                   0.012, 0.012, 0.012, SPELL_ORB["lumen"], ry=a, glow=True)  # fmt: skip


def spell_hand_view(r, player, bob, side, armor, t):
    """An open hand holding the readied spell's light; it pushes forward as the spell is cast."""
    spell = player.current_spell()
    cast = 1 - min(player.magic_gauge.value / 0.25, 1.0)  # just after casting
    thrust = 0.3 if spell and spell.id == "pyre" else 0.2  # Pyre: the palm shoved out, fingers spread
    x = 0.9 + thrust * _ease(cast)
    y = -0.24 - SPELL_DROP + bob
    z = 0.34 * side
    # Held up and out, as if offering the light: the fingers rise forward, the palm tipped back toward
    # you and rolled a little toward the middle of the view, so you look into it.
    frame = {"ry": 0.2 * side, "rz": SPELL_TIP, "rx": -0.35 * side, "s": 0.8}
    with r.at(x, y, z, **frame), r.at(*OPEN_WRIST):
        m = r.top
    hand_rgb, shade = arm(r, (m[3], m[7], m[11]), side, armor["body"], armor["gloves"])
    with r.at(x, y, z, **frame):
        _open_hand(
            r,
            hand_rgb,
            shade,
            side,
            armor["gloves"],
            spread=0.5 if spell and spell.id == "pyre" else 0.2,
            curl=OPEN_CURL if spell and spell.id == "pyre" else CUP_CURL,
        )
        glow = SPELL_GLOW.get(spell.id, (220, 220, 220)) if spell else None
        if spell and spell.id in FIRE_SPELLS:
            # A small fire licks over the palm; it gutters to an ember while the gauge refills.
            ready = player.magic_gauge.full
            with r.at(0.02, 0.17, 0):
                fireball(r, glow, t, 0.26 if ready else 0.08 + 0.1 * player.magic_gauge.value)
            if spell.id == "pyre" and cast > 0:  # the gout bursts from the palm: a white-hot flash
                with r.at(0.25, 0.06, 0):
                    fireball(r, GOUT_HOT, t, 0.15 + 0.3 * cast, seed=3.0)
        elif spell and spell.id == "thunder" and player.magic_gauge.full:
            _palm_lightning(r, t)
        elif spell and spell.id == "motes":
            _palm_motes(r, t, player.magic_gauge.value)
        elif spell and spell.id == "mend":
            _palm_mend(r, t, player.magic_gauge.full, cast)
        elif spell and spell.id == "lumen":
            _palm_lumen(r, t, player.magic_gauge.full, cast)
        elif spell and player.magic_gauge.full:
            pulse = 1 + math.sin(t * 5) * 0.12
            r.part("sphere", 0.02, 0.1, 0, 0.09 * pulse, 0.09 * pulse, 0.09 * pulse, glow, glow=True)


def _palm_lightning(r, t):
    """Thunder Spear readied: a bright knot of lightning over the palm, arcs crackling from it to the
    cupped fingertips, struck anew many times a second."""
    seed = math.floor(t * forge_models.BOLT_FLICKER)
    r.part("sphere", 0.02, 0.1, 0, 0.07, 0.07, 0.07, (240, 248, 255), glow=True)
    for i in range(3):  # to three of the fingertips, in turn flickering
        if forge_models._jitter(seed, i + 3) < -0.4:
            continue
        tip = (0.11 + 0.02 * i, 0.06 + 0.02 * i, (i - 1) * 0.045)
        mid = tuple((p + q) / 2 + forge_models._jitter(seed, i * 3 + k) * 0.02 for k, (p, q) in
                    enumerate(zip((0.02, 0.1, 0.0), tip, strict=True)))  # fmt: skip
        forge_models._segment(r, (0.02, 0.1, 0.0), mid, 0.012, SPELL_GLOW["thunder"])
        forge_models._segment(r, mid, tip, 0.012, SPELL_GLOW["thunder"])


def _palm_motes(r, t, gauge):
    """Arcane Motes readied: three motes wheeling over the palm. Each is loosed by a cast and they come
    back one by one as the gauge refills."""
    shown = 3 if gauge >= 1.0 else min(int(gauge * 3.0), 2)
    r.part("sphere", 0.02, 0.1, 0, 0.035, 0.035, 0.035, _dim(SPELL_GLOW["motes"], 0.7), glow=True)
    for i in range(shown):
        a = t * 4 + i * math.tau / 3
        y = 0.12 + 0.025 * math.sin(t * 3 + i * 2)
        r.part("sphere", 0.02 + math.cos(a) * 0.07, y, math.sin(a) * 0.07, 0.026, 0.026, 0.026,
               SPELL_GLOW["motes"], glow=True)  # fmt: skip


OPEN_WRIST = (-0.115, -0.004, 0.0)  # where an open hand's heel meets the forearm
SPELL_DROP = 0.06  # how much lower the spell hand is carried, so only the hand and wrist show
SPELL_TIP = 0.45  # how far the spell hand's fingers rise from level
OPEN_CURL = (0.1, 0.16, 0.12)  # a relaxed open hand's fingers: barely curled
CUP_CURL = (0.38, 0.5, 0.42)  # a hand cupping a spell's orb: the fingers curl up round it


def _open_hand(r, hand, shade, side, gloves=None, spread=0.2, curl=OPEN_CURL):
    """An open human hand, palm up (+Y), fingers forward (+X), thumb inward: a palm narrowing to its
    heel, four relaxed fingers of rounded bones, curled by `curl` and fanned by `spread`, and the
    thumb out to the side from the fleshy root under the index side, rising as the fingers curl."""
    iron = gloves == "iron_gauntlets"
    mitt = gloves == "chain_mitts"
    fat = 1.12 if mitt else 1.05 if iron else 1.0
    r.part("frustum", -0.005, 0, 0, 0.042 * fat, 0.17, 0.13 * fat, hand, rz=math.pi / 2)  # palm
    r.part("sphere", -0.07, -0.004, 0.006 * side, 0.07, 0.05 * fat, 0.1 * fat, hand)  # its heel
    r.part("sphere", -0.035, 0.012, -0.04 * side, 0.08, 0.04 * fat, 0.05 * fat, _dim(hand, 0.94))
    for i, (y, ln, th) in enumerate(FINGERS):
        z = -y * side  # the index beside the thumb, inward
        fan = (i - 1.5) * spread * 0.2 * side
        tone = hand if i % 2 == 0 else _dim(hand, 0.88)
        with r.at(0.075 - (0.01 if i == 3 else 0.0), 0.004, z, ry=fan):
            _digit(
                r, [b * ln for b in BONES], FINGER * th * fat, tone, curl, axis="rz",
                plate=shade if iron else None, ring=shade if mitt else None,
            )  # fmt: skip
    # The thumb, resting out to the side of the palm and forward, nearly in its plane.
    joints = [(-0.055, 0.0, -0.04), (-0.008, 0.01, -0.078), (0.032, 0.016, -0.095), (0.064, 0.02, -0.102)]
    cup = curl[0] - OPEN_CURL[0]  # a cupping hand lifts its thumb toward the fingers
    joints = [(x, y + cup * 0.12 * k, z * side * (1 - cup * 0.25 * k)) for k, (x, y, z) in enumerate(joints)]
    for a, b, w in zip(joints, joints[1:], (0.048 * fat, 0.036 * fat, 0.031 * fat), strict=False):
        r.part("sphere", *a, w * 1.1, w * 1.1, w * 1.1, hand)
        _limb(r, a, b, w, hand, "cyl")
    if iron:  # a plate over the back
        r.part("frustum", 0, -0.028, 0, 0.014, 0.15, 0.13, shade, rz=math.pi / 2)


SPELL_GLOW = {
    "flame": EMBER,
    "mend": (130, 230, 130),
    "lumen": (235, 235, 180),
    "venom": (130, 220, 70),
    "veil": (205, 215, 220),
    "pyre": (255, 110, 40),
    "thunder": (190, 220, 255),
    "motes": (190, 120, 255),
    "ward": (245, 165, 80),
    "rift_lance": (255, 230, 160),
    "bellward": (225, 205, 145),
    "mortar_shard": (140, 214, 192),
}
WARD_EMBERS = 9  # motes circling you while an Ashen Ward holds
WARD_FADE = 2.0  # seconds before it ends that the embers gutter and flicker


def ward_embers(r, player, t):
    """An Ashen Ward in first person: embers wheeling around you at the edges of sight, each trailing
    a fainter spark, guttering and flickering in the ward's last seconds."""
    left = player.ward_t
    if left <= 0:
        return
    fade = min(left / WARD_FADE, 1.0)
    if fade < 1 and math.sin(t * 40) < -0.3:  # the guttering ward flickers
        return
    for i in range(WARD_EMBERS):
        a = t * 1.6 + i * math.tau / WARD_EMBERS
        y = -0.12 + 0.22 * math.sin(a * 2 + i)
        for j, (k, size) in enumerate(((0.0, 0.02), (0.25, 0.012))):
            b = a - k
            x, z = 1.3 + 0.3 * math.cos(b), 0.7 * math.sin(b)
            rgb = SPELL_GLOW["ward"] if j == 0 else (200, 90, 40)
            s = size * (0.6 + 0.4 * fade)
            r.part("cube", x, y - k * 0.06, z, s, s, s, rgb, glow=True)


WOOD = (90, 60, 38)
LEATHER = (70, 46, 30)
BRASS = (150, 130, 80)
STEEL = (190, 190, 200)
OAK = (118, 84, 52)

# Rough length of each weapon model (grip to tip), used to fit previews.
WEAPON_LEN = {
    "rusted_sword": 1.3,
    "ashblade": 1.4,
    "bastard_sword": 1.68,
    "claymore": 2.2,
    "zweihander": 2.5,
    "katana": 1.7,
    "moonless_tachi": 1.95,
    "nodachi": 2.45,
    "war_hammer": 1.5,
    "great_iron_hammer": 1.55,
    "flamberge": 2.15,
    "bearded_axe": 1.15,
    "hatchet": 0.9,
    "butcher_cleaver": 1.0,
    "oak_cudgel": 1.0,
    "spiked_club": 1.05,
    "stormbrand": 1.45,
    "slagbreaker": 1.5,
    "torch_greathammer": 1.55,
    "ember_stone_sword": 1.45,
    "vesper_moonbrand": 2.45,
}


def weapon(r, item_id, phase=None):
    """A weapon model with the grip at the origin, pointing up +Y; an edge or striking face leads
    along +X (see HEADED and `edge_turn`)."""
    turn = edge_turn(item_id)
    if turn:
        with r.at(0, 0, 0, ry=turn):
            return _weapon(r, item_id, phase)
    return _weapon(r, item_id, phase)


def edge_turn(item_id):
    """The quarter turn about the grip that brings a weapon's edge onto +X, the way swings travel and the
    hand's knuckles face: axe bits, hammer faces and straight blades are built on +-Z, a katana's edge
    on -Z."""
    if (
        item_id in HEADED
        or item_id in SWORDS
        or item_id in ("stormbrand", "ember_stone_sword", "vesper_moonbrand")
    ):
        return math.pi / 2
    if item_id in KATANAS:
        return -math.pi / 2
    return 0.0


def _weapon(r, item_id, phase=None):
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
    elif item_id == "great_iron_hammer":
        great_iron_hammer(r)
    elif item_id in ("hatchet", "bearded_axe"):
        hand_axe(r, item_id == "bearded_axe")
    elif item_id == "butcher_cleaver":
        cleaver(r)
    elif item_id == "stormbrand":
        forge_models.stormbrand(r)
    elif item_id == "slagbreaker":
        forge_models.slagbreaker(r)
    elif item_id == "torch_greathammer":
        sunken_models.torch_greathammer(r)
    elif item_id == "ember_stone_sword":
        sunken_models.ember_stone_sword(r)
    elif item_id == "vesper_moonbrand":
        moon_models.moonbrand(r)
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
    trim_rgb=None,
    grip=0.22,
    grip_rgb=LEATHER,
    wrap=None,
    ferrule=False,
    pommel="disc",
    pommel_rgb=BRASS,
    ricasso=0.0,
    ricasso_rgb=LEATHER,
    lugs=None,
    glow=False,
    waves=0,
):
    """A straight sword with its grip at the origin and its blade up +Y (the blade's flat faces +-X):
    pommel, grip (with `wrap` bands and, with `ferrule`, a collar halfway down it), a crossguard, an
    optional `ricasso` (the unsharpened base of a big blade) with parrying `lugs` at its top, then a
    lozenge-section blade that narrows to a point, a fuller down both faces and bright bevelled edges.
    Shared by the player's swords and the foes' (`sword_parts`).

    guard: see `_guard`. pommel: see `_pommel`. lugs: see `_lugs`. `trim_rgb` (the guard's colour by
    default) picks out the quillons' tips, the side rings, the ferrule and the lugs' flames. `waves` > 0
    ripples the blade like a flame (`_wavy_blade`), that many crests up each edge."""
    edge = edge or _bright(steel)
    fuller = fuller or _dim(steel, 0.62)
    trim = trim_rgb or guard_rgb
    # Grip and pommel.
    r.part("cube", 0, 0.1 - grip / 2, 0, 0.055, grip, 0.055, grip_rgb)
    if wrap:
        for i in range(max(int(grip / 0.065), 1)):
            r.part("cube", 0, 0.1 - grip + 0.035 + i * 0.065, 0, 0.062, 0.02, 0.062, wrap)
    if ferrule:  # a two-hander's grip swells to a collar between the hands
        r.part("cyl", 0, 0.1 - grip / 2, 0, 0.078, 0.035, 0.078, trim)
    _pommel(r, pommel, 0.1 - grip - 0.035, pommel_rgb, trim)
    _guard(r, guard, guard_w, guard_rgb, trim)
    if ricasso:
        r.part("cube", 0, base + ricasso / 2, 0, thick * 1.7, ricasso, width * 0.9, ricasso_rgb)
        if lugs:
            _lugs(r, lugs, base + ricasso, width, guard_rgb, trim)
    if waves:
        _wavy_blade(r, base + ricasso, length - ricasso, width, thick, steel, edge, fuller, waves)
        return
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


def _pommel(r, style, y, rgb, trim):
    """A sword's pommel hung below the grip at height `y`: "disc", "wheel", "stopper" (a ball drawn
    to a point), "pear" (a big teardrop with a button) or "fig" (a tall bulb on a collar, a finial
    under it)."""
    if style == "wheel":
        r.part("cyl", 0, y - 0.01, 0, 0.12, 0.045, 0.12, rgb, rz=math.pi / 2)
        r.part("cyl", 0, y - 0.01, 0, 0.05, 0.055, 0.05, _bright(rgb), rz=math.pi / 2)
    elif style == "stopper":
        r.part("sphere", 0, y, 0, 0.085, 0.08, 0.085, rgb)
        r.part("cone", 0, y - 0.065, 0, 0.06, 0.06, 0.06, rgb, rz=math.pi)
    elif style == "pear":
        r.part("sphere", 0, y - 0.03, 0, 0.11, 0.14, 0.11, rgb)
        r.part("cone", 0, y + 0.03, 0, 0.08, 0.06, 0.08, rgb)
        r.part("sphere", 0, y - 0.11, 0, 0.045, 0.04, 0.045, trim)
    elif style == "fig":
        r.part("cyl", 0, y + 0.025, 0, 0.075, 0.025, 0.075, trim)
        r.part("sphere", 0, y - 0.03, 0, 0.085, 0.11, 0.085, rgb)
        r.part("cone", 0, y - 0.1, 0, 0.04, 0.05, 0.04, trim, rz=math.pi)
    else:
        r.part("sphere", 0, y, 0, 0.09, 0.075, 0.08, rgb)


# How far each guard style bends its quillons toward the hand (negative: toward the blade).
GUARD_BEND = {"droop": 0.35, "quatrefoil": 0.3, "flared": -0.28, "flame": -0.3}
GUARD_Y = 0.115  # the crossguard's height above the grip's origin


def _guard(r, style, guard_w, rgb, trim):
    """A crossguard `guard_w` across, a block and two quillons: "straight", "droop" (bent toward the
    hand), "quatrefoil" (drooping, with trefoil knobs), "flared" (bent up toward the blade), "flame"
    (flared, the tips curling back down in `trim`) or "rings" (straight, the tips curled one up and one
    down, with a ring hung on each side of the grip)."""
    gy = GUARD_Y
    r.part("cube", 0, gy, 0, 0.07, 0.055, 0.09, rgb)
    half = guard_w / 2
    for side in (1, -1):
        with r.at(0, gy, side * 0.04, rx=side * GUARD_BEND.get(style, 0.0)):
            r.part("lozenge", 0, 0, side * half / 2, 0.05, half, 0.045, rgb, rx=math.pi / 2)
            if style == "quatrefoil":
                r.part("sphere", 0, 0, side * (half + 0.02), 0.07, 0.07, 0.06, rgb)
            elif style in ("rings", "flame"):
                # "rings" curls its tips into an S (rx turns +-Z toward the hand by side * rx);
                # "flame" curls both back down, toward the hand.
                with r.at(0, 0, side * half, rx=-1.1 if style == "rings" else side * 1.2):
                    r.part("lozenge", 0, 0, side * 0.045, 0.042, 0.09, 0.038, rgb, rx=math.pi / 2)
                    r.part("sphere", 0, 0, side * 0.095, 0.05, 0.05, 0.05, trim)
            else:
                r.part("wedge", 0, 0, side * (half + 0.02), 0.05, 0.05, 0.045, rgb, rx=side * math.pi / 2)
        if style == "rings":
            _hoop(r, gy - 0.045, side * 0.1, 0.06, 0.026, trim)


def _hoop(r, y, z, radius, thick, rgb, n=8):
    """A ring of `n` bars in the blade's plane (Y-Z), centred on (0, y, z)."""
    span = 2 * radius * math.tan(math.pi / n) * 1.15
    for i in range(n):
        a = i * math.tau / n
        r.part(
            "cube",
            0,
            y + radius * math.cos(a),
            z + radius * math.sin(a),
            thick,
            span,
            thick,
            rgb,
            rx=a + math.pi / 2,
        )


def _lugs(r, style, y, width, rgb, trim):
    """Parrying lugs at the top of a ricasso (height `y`), one each side: "hooks" (a short wedge),
    "horns" (a curved horn sweeping out and down toward the guard) or "flames" (three tongues of
    `trim` licking up and out)."""
    for side in (1, -1):
        if style == "hooks":
            r.part("wedge", 0, y, side * width * 0.75, 0.04, 0.14, 0.05, rgb, rx=side * 1.0)
        elif style == "horns":
            pts = [(0, y, 0.42), (0, y - 0.015, 0.95), (0, y - 0.075, 1.2), (0, y - 0.14, 1.1)]
            pts = [(x, py, side * width * k) for x, py, k in pts]
            for a, b in itertools.pairwise(pts):
                _bar(r, a, b, 0.036, rgb)
            r.part("sphere", *pts[-1], 0.045, 0.045, 0.045, trim)
        elif style == "flames":
            for drop, lean, length in ((0.0, 0.55, 0.13), (0.045, 0.95, 0.1), (0.09, 1.3, 0.07)):
                by, bz = y - drop, side * width * 0.42
                r.part(
                    "cone",
                    0,
                    by + math.cos(lean) * length / 2,
                    bz + side * math.sin(lean) * length / 2,
                    0.04,
                    length,
                    0.03,
                    trim,
                    rx=side * lean,
                )


WAVE_STEPS = 4  # segments to each half-wave of a flame-bladed sword's ripple


def _wavy_blade(r, y0, length, width, thick, steel, edge, ridge, waves):
    """A flame-bladed sword's blade from `y0` up, snaking from side to side in `waves` full ripples that
    ease as it narrows toward a straight `blade` point: a stack of thin slices, each shifted onto the
    ripple, with its bright edges and central `ridge` as bars laid along the ripple's slope, so its
    outline runs smooth."""
    point = length * 0.14
    body = length - point
    n = waves * 2 * WAVE_STEPS
    seg = body / n
    amp = width * 0.3

    def snake(p):
        return amp * (1 - 0.35 * p) * math.sin(p * waves * math.tau)

    for k in range(n):
        z0, z1 = snake(k / n), snake((k + 1) / n)
        w = width * (1 - 0.2 * (k + 0.5) / n)
        y, z = y0 + (k + 0.5) * seg, (z0 + z1) / 2
        r.part("cube", 0, y, z, thick, seg * 1.02, w * 0.86, steel)
        span = math.hypot(seg, z1 - z0) * 1.06
        with r.at(0, y, z, rx=math.atan2(z1 - z0, seg)):
            r.part("cube", 0, 0, 0, thick * 1.2, span, w * 0.1, ridge)
            for side in (1, -1):
                r.part("cube", 0, 0, side * w * 0.45, thick * 0.5, span, w * 0.12, edge)
    r.part("blade", 0, y0 + body + point / 2, 0, thick, point, width * 0.78, steel)


# The player's straight swords: blade_parts arguments per item.
SWORDS = {
    "rusted_sword": {
        "length": 1.1,
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
        "length": 1.2,
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
        "length": 1.4,
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
        "length": 1.72,
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
    "zweihander": {  # a Landsknecht's two-hander: broad, blued, ringed and horned
        "length": 2.0,
        "width": 0.19,
        "thick": 0.042,
        "base": 0.12,
        "steel": (188, 190, 200),
        "fuller": (128, 130, 142),
        "guard": "rings",
        "guard_w": 0.66,
        "guard_rgb": (82, 88, 108),
        "trim_rgb": (164, 168, 182),
        "grip": 0.46,
        "grip_rgb": (28, 24, 22),
        "ferrule": True,
        "pommel": "pear",
        "pommel_rgb": (82, 88, 108),
        "ricasso": 0.3,
        "ricasso_rgb": (126, 34, 30),
        "lugs": "horns",
    },
    "flamberge": {  # a flame-bladed sword: blackened and gilt, its ricasso bare and etched
        "length": 1.78,
        "width": 0.15,
        "thick": 0.036,
        "base": 0.12,
        "steel": (178, 180, 192),
        "edge": (236, 236, 244),
        "fuller": (214, 214, 224),
        "guard": "flame",
        "guard_w": 0.5,
        "guard_rgb": (52, 48, 54),
        "trim_rgb": (196, 158, 78),
        "grip": 0.42,
        "grip_rgb": (86, 26, 24),
        "wrap": (176, 140, 70),
        "pommel": "fig",
        "pommel_rgb": (52, 48, 54),
        "ricasso": 0.2,
        "ricasso_rgb": (120, 120, 132),
        "lugs": "flames",
        "waves": 5,
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
    elif item_id == "flamberge":  # a gilt flame etched on both faces of the bare ricasso
        y, gilt, x = base + spec["ricasso"] * 0.45, spec["trim_rgb"], spec["thick"] * 0.86
        for side in (1, -1):  # a tall tongue between two that lean out from its foot
            r.part("cube", side * x, y + 0.01, 0, 0.004, 0.11, 0.012, gilt)
            for tilt in (1, -1):
                r.part("cube", side * x, y - 0.012, tilt * 0.018, 0.004, 0.065, 0.01, gilt, rx=-tilt * 0.45)


# blade, edge (hamon), grip wrap, cord, segments, grip length
KATANAS = {
    "katana": ((205, 208, 218), (245, 245, 250), (40, 30, 40), (160, 30, 40), 4, 0.3),
    "moonless_tachi": ((70, 72, 90), (200, 205, 220), (20, 18, 24), (60, 60, 80), 5, 0.32),
    "nodachi": ((200, 202, 212), (245, 245, 250), (30, 26, 30), (200, 170, 70), 6, 0.5),
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


HAMMER_IRON = (92, 92, 100)
HAMMER_BAND = (60, 58, 64)


def great_iron_hammer(r):
    """The Great Iron Hammer: a long haft bound in iron rings, steel langets riveted up its top, and a
    massive squared block of a head, ringed by two riveted bands, a studded striking face on +Z and a
    short, square back spike."""
    r.part("cube", 0, 0.38, 0, 0.07, 1.32, 0.07, (70, 52, 36))  # the haft
    for k in range(4):  # iron rings down the haft
        r.part("cube", 0, 0.05 + k * 0.17, 0, 0.082, 0.03, 0.082, HAMMER_BAND)
    r.part("cube", 0, -0.2, 0, 0.085, 0.26, 0.085, LEATHER)  # the grip
    r.part("cube", 0, -0.36, 0, 0.11, 0.06, 0.11, HAMMER_BAND)  # butt cap
    r.part("wedge", 0, -0.42, 0, 0.07, 0.06, 0.07, HAMMER_BAND, rz=math.pi)
    for dz in (-0.04, 0.04):  # langets
        r.part("cube", 0, 0.82, dz, 0.045, 0.36, 0.012, STEEL)
        for k in range(2):
            r.part("cube", 0, 0.72 + k * 0.16, dz * 1.25, 0.022, 0.022, 0.012, HAMMER_BAND)
    with r.at(0, 1.1, 0.04):  # the head, its face on +Z
        r.part("cube", 0, 0, 0, 0.26, 0.28, 0.46, HAMMER_IRON)
        for dz in (-0.13, 0.13):  # riveted bands round it
            r.part("cube", 0, 0, dz, 0.28, 0.3, 0.05, HAMMER_BAND)
            for dx, dy in ((-0.14, 0.0), (0.14, 0.0), (0.0, 0.15)):
                r.part("cube", dx, dy, dz, 0.025, 0.025, 0.025, (150, 150, 158))
        r.part("cube", 0, 0, 0.24, 0.3, 0.32, 0.03, _dim(HAMMER_IRON, 1.2))  # striking face
        for dx in (-0.08, 0.08):  # its studs
            for dy in (-0.08, 0.08):
                r.part("cube", dx, dy, 0.265, 0.05, 0.05, 0.03, (170, 170, 178))
        r.part("cube", 0, 0, -0.26, 0.16, 0.16, 0.06, HAMMER_BAND)  # spike root
        r.part("wedge", 0, 0, -0.36, 0.12, 0.16, 0.12, STEEL, rx=-math.pi / 2)  # the back spike
        r.part("cube", 0, 0.16, 0, 0.12, 0.04, 0.2, HAMMER_BAND)  # cap over the eye
        r.part("wedge", 0, 0.22, 0, 0.08, 0.1, 0.08, STEEL)  # top spike


def shield(r, item_id):
    """Shields face +X (away from you); the arm holds them from behind at the origin."""
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
    elif id_ == "bitter_root":
        for x, y, ry, rz, d in (
            (0, -0.05, 0, 0.5, 0.7),
            (0.15, -0.25, 1.0, -0.7, 0.4),
            (-0.18, 0.12, -0.5, 1.2, 0.35),
        ):
            r.part("cyl", x, y, 0, 0.12, d, 0.12, (120, 82, 48), ry=ry, rz=rz)
        r.part("sphere", 0.12, 0.34, 0, 0.18, 0.06, 0.12, (110, 180, 60), rz=-0.45)
    elif id_ == "clotting_salve":
        r.part("cyl", 0, -0.12, 0, 0.6, 0.44, 0.6, (150, 90, 60))
        r.part("cyl", 0, 0.12, 0, 0.66, 0.06, 0.66, (125, 72, 46))
        r.part("cyl", 0, 0.16, 0, 0.5, 0.04, 0.5, (185, 180, 170))
    elif id_ == "ember_draught":
        r.part("sphere", 0, -0.12, 0, 0.44, 0.44, 0.44, (180, 56, 30))  # the flask
        r.part("sphere", 0, -0.12, 0, 0.22, 0.22, 0.22, (255, 150, 60), glow=True)  # the ember in it
        r.part("cyl", 0, 0.16, 0, 0.14, 0.2, 0.14, (180, 56, 30))  # its neck
        r.part("cyl", 0, 0.3, 0, 0.16, 0.1, 0.16, (120, 90, 60))  # the cork
    elif id_ == "grave_lily":
        r.part("cyl", 0, -0.2, 0, 0.05, 0.6, 0.05, (80, 120, 70))
        for k in range(5):
            a = k * math.tau / 5
            r.part(
                "sphere",
                math.cos(a) * 0.14,
                0.18,
                math.sin(a) * 0.14,
                0.2,
                0.08,
                0.12,
                (235, 235, 225),
                ry=-a,
            )
        r.part("sphere", 0, 0.2, 0, 0.1, 0.1, 0.1, (240, 220, 120), glow=True)
    elif id_ in ("menders_kit", "mend_gear"):
        menders_kit(r)
    elif Items.ALL.get(id_) and Items.get(id_).kind == "scroll":
        with r.at(0, 0, 0, s=1.2):
            scroll(r, id_, t)
    elif id_ in KEY_STYLES:
        key(r, id_, KEY_STYLES[id_][1], t)
    elif id_ in SIGILS:
        sigil(r, id_, t)
    elif id_.startswith("spell_"):
        spell_orb(r, id_.removeprefix("spell_"), t)
    else:
        r.part("cube", 0, 0, 0, 0.5, 0.5, 0.5, (130, 100, 70))


def menders_kit(r):
    """A Mender's Kit: a leather roll tied with cord, a grey whetstone and an awl laid across it, and a
    few rivets spilled beside them."""
    leather, cord = (112, 70, 40), (190, 170, 120)
    r.part("cyl", 0, -0.1, 0, 0.32, 0.7, 0.32, leather, rz=math.pi / 2)  # the rolled leather
    r.part("cyl", 0.36, -0.1, 0, 0.3, 0.02, 0.3, _dim(leather, 0.7), rz=math.pi / 2)  # its rolled end
    for x in (-0.2, 0.2):  # the cords that tie it
        r.part("cyl", x, -0.1, 0, 0.34, 0.05, 0.34, cord, rz=math.pi / 2)
    r.part("cube", -0.05, 0.13, 0.02, 0.5, 0.1, 0.16, (120, 124, 128), ry=0.3)  # the whetstone
    r.part("cube", 0.08, 0.2, -0.04, 0.42, 0.03, 0.03, (170, 170, 176), ry=-0.6)  # the awl's spike
    r.part("cyl", -0.14, 0.2, 0.08, 0.06, 0.14, 0.06, (90, 60, 34), rz=math.pi / 2, ry=-0.6)  # its haft
    for x, z in ((0.3, 0.3), (0.38, 0.22), (0.24, 0.36)):  # spilled rivets
        r.part("sphere", x, -0.24, z, 0.06, 0.04, 0.06, (150, 140, 120))


PARCHMENT = (214, 198, 160)
SOOTED_PARCHMENT = (150, 132, 110)  # scrolls kept in the Cinderhold, smudged by its smoke
ROD_WOOD = (110, 80, 50)
ROD_IRON = (80, 80, 88)
# Each scroll: its parchment, its rods and the wax of its seal (the ribbon is a darker shade of it).
# The rune pressed into the seal (SCROLL_RUNES) glows in the spell's own colour (SPELL_ORB).
SCROLLS = {
    "scroll_flame": (SOOTED_PARCHMENT, ROD_WOOD, (210, 96, 30)),  # found among the ashes of the cemetery
    "scroll_mend": (PARCHMENT, ROD_WOOD, (160, 34, 34)),
    "scroll_lumen": (PARCHMENT, ROD_WOOD, (196, 160, 60)),
    "scroll_venom": (PARCHMENT, ROD_WOOD, (70, 120, 40)),
    "scroll_veil": (PARCHMENT, ROD_WOOD, (110, 120, 132)),
    "scroll_pyre": (PARCHMENT, ROD_WOOD, (190, 70, 20)),
    "scroll_thunder": (SOOTED_PARCHMENT, ROD_IRON, (46, 66, 150)),
    "scroll_motes": (SOOTED_PARCHMENT, ROD_IRON, (100, 44, 140)),
    "scroll_ward": (PARCHMENT, ROD_WOOD, (130, 60, 26)),
    # Ysolde Vane's scrolls, copied in her cell in the Oubliette: grey paper, bronze rods, gold seals.
    "scroll_rift_lance": (SOOTED_PARCHMENT, ROD_IRON, (196, 160, 70)),
    "scroll_bellward": (PARCHMENT, ROD_IRON, (150, 116, 60)),
    # Sister Vell's last rite, written on mason's grey paper and sealed in the grey-teal of spent light.
    "scroll_mortar_shard": (SOOTED_PARCHMENT, ROD_WOOD, (92, 128, 118)),
}


def _ring(n, radius, length):
    """Bars set tangent around a circle: the rune of a ward."""
    return [
        (
            math.cos(i * math.tau / n) * radius,
            math.sin(i * math.tau / n) * radius,
            length,
            i * math.tau / n + math.pi / 2,
        )
        for i in range(n)
    ]


# Runes pressed into the seal as glowing bars: (y, z, length, angle in the seal's face; 0 is upright).
SCROLL_RUNES = {
    "flame": [(0.0, -0.022, 0.11, -0.4), (0.0, 0.022, 0.11, 0.4), (-0.05, 0.0, 0.08, math.pi / 2)],
    "pyre": [
        (0.0, -0.028, 0.11, -0.4), (0.0, 0.028, 0.11, 0.4), (0.0, 0.0, 0.07, 0.0),
        (-0.05, 0.0, 0.1, math.pi / 2),
    ],
    "mend": [(0.0, 0.0, 0.12, 0.0), (0.0, 0.0, 0.12, math.pi / 2)],
    "lumen": [(0.0, 0.0, 0.13, i * math.pi / 4) for i in range(4)],
    "venom": [(0.015, -0.02, 0.1, 0.3), (0.015, 0.02, 0.1, -0.3), (-0.055, 0.0, 0.025, 0.0)],
    "veil": [(0.04, -0.012, 0.09, math.pi / 2), (0.0, 0.012, 0.09, math.pi / 2), (-0.04, -0.012, 0.09, math.pi / 2)],
    "thunder": [(0.042, 0.014, 0.07, -0.5), (0.0, 0.0, 0.07, 1.1), (-0.042, -0.014, 0.07, -0.5)],
    "motes": [(0.042, 0.0, 0.035, 0.0), (-0.024, -0.036, 0.035, 0.0), (-0.024, 0.036, 0.035, 0.0)],
    "ward": _ring(6, 0.048, 0.052),
    "rift_lance": [(0.0, 0.0, 0.15, 0.0), (0.05, 0.0, 0.05, math.pi / 2), (-0.05, 0.0, 0.05, math.pi / 2)],
    "bellward": [(0.03, 0.0, 0.08, math.pi / 2), (0.0, -0.03, 0.07, 0.0), (0.0, 0.03, 0.07, 0.0),
                 (-0.05, 0.0, 0.02, 0.0)],
    # A mason's mark: a square stone split by one crack.
    "mortar_shard": [(0.04, 0.0, 0.08, math.pi / 2), (-0.04, 0.0, 0.08, math.pi / 2), (0.0, 0.04, 0.08, 0.0),
                     (0.0, -0.04, 0.08, 0.0), (0.0, 0.0, 0.07, 0.7)],
}  # fmt: skip


def scroll(r, id_, t):
    """A spell scroll lying along Z: a rolled parchment with a loose tongue hanging from it, rods
    capped with knobs at both ends, a ribbon round its middle and a big wax seal on it, the spell's
    rune pressed into the wax and glowing in the spell's colour."""
    parchment, rod, wax = SCROLLS[id_]
    spell = Items.get(id_).spell
    ribbon = _dim(wax, 0.75)
    with r.at(0, 0, 0, rx=math.pi / 2):  # the roll's axis along Z
        r.part("cyl", 0, 0, 0, 0.4, 0.84, 0.4, parchment)
        for end in (-1, 1):
            r.part("cyl", 0, end * 0.43, 0, 0.44, 0.04, 0.44, _dim(parchment, 0.8))  # the curled edge
            r.part("cyl", 0, end * 0.5, 0, 0.1, 0.14, 0.1, rod)
            r.part("sphere", 0, end * 0.6, 0, 0.15, 0.15, 0.15, rod)
        r.part("cyl", 0, 0, 0, 0.42, 0.12, 0.42, ribbon)
    # The unrolled tongue, curling off the front of the roll, and the ribbon's loose tails.
    r.part("cube", 0.2, -0.24, 0, 0.02, 0.3, 0.78, _dim(parchment, 0.92), rz=0.25)
    for side in (-1, 1):
        r.part("cube", 0.22, -0.2, side * 0.06, 0.02, 0.24, 0.06, ribbon, rx=side * 0.35)
    # The seal on the ribbon, facing out (+X), and the rune pressed into it.
    with r.at(0.23, 0.0, 0, rz=-math.pi / 2):
        r.part("cyl", 0, 0, 0, 0.32, 0.05, 0.32, _dim(wax, 0.8))
        r.part("cyl", 0, 0.02, 0, 0.26, 0.04, 0.26, wax)
    pulse = 0.85 + 0.15 * math.sin(t * 3)
    glow = _dim(SPELL_ORB.get(spell, WHITE), pulse)
    for y, z, length, ang in SCROLL_RUNES.get(spell, []):
        k = 1.5  # the runes are drawn for a 0.2 seal; this one is bigger
        r.part("cube", 0.275, y * k, z * k, 0.02, length * k, 0.032, glow, rx=ang, glow=True)


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


# Each key: (metal, preview size). Keys lie in the Y-Z plane, bow up, bit toward +Z, flats facing X.
KEY_STYLES = {
    "cell_key": ((150, 84, 50), 1.9),  # a gaoler's rusty iron key, short, crude and pitted
    "warden_key": ((150, 150, 160), 1.5),  # long, heavy steel, an ember in a crowned trefoil
    "briar_key": ((92, 104, 58), 1.7),  # verdigris bronze branches, thorned, with a leaf for a bit
    "forge_key": ((58, 52, 52), 1.8),  # blackened iron, an anvil for a bow, its bit still glowing
}


def key(r, id_, size, t=0.0):
    """A key of the style KEY_STYLES gives `id_`, each its own shape (KEY_SHAPES): bow up, bit
    toward +Z, flats facing X."""
    metal = KEY_STYLES.get(id_, KEY_STYLES["cell_key"])[0]
    with r.at(0, 0, 0, rx=-0.6, s=size):
        KEY_SHAPES.get(id_, _cell_key)(r, metal, t)


def _key_collar(r, y, metal, width=0.1):
    """Where the bow meets the shank: a bright collar over a darker ring."""
    r.part("cyl", 0, y, 0, width, 0.05, width, _bright(metal, 1.1, 15))
    r.part("cyl", 0, y - 0.06, 0, width * 0.8, 0.03, width * 0.8, _dim(metal, 0.65))


def _cell_key(r, metal, t):
    """A gaoler's key: short and crude, a squashed oval bow, a pitted shank and one blocky bit."""
    dark = _dim(metal, 0.65)
    rust = (110, 50, 30)
    for i in range(12):  # the oval bow, wider than tall
        a = i * math.tau / 12
        r.part("cube", 0, 0.26 + math.cos(a) * 0.11, math.sin(a) * 0.19, 0.06, 0.06, 0.1, metal, rx=-a)
    r.part("cube", 0, 0.26, 0, 0.05, 0.04, 0.3, dark)  # a bar across it
    r.part("cube", 0.03, 0.34, 0.1, 0.01, 0.05, 0.05, rust)
    _key_collar(r, 0.12, metal)
    r.part("cube", 0, -0.04, 0, 0.065, 0.26, 0.065, metal)  # a short, thick shank
    for y, z in ((0.0, 0.03), (-0.1, -0.02), (-0.13, 0.03)):  # pitting and rust
        r.part("cube", 0.035, y, z, 0.01, 0.03, 0.03, rust)
    r.part("cube", 0, -0.12, 0.11, 0.05, 0.12, 0.16, metal)  # one square bit
    r.part("cube", 0, -0.12, 0.17, 0.052, 0.04, 0.04, dark)  # notched once
    r.part("cube", 0.03, -0.1, 0.06, 0.01, 0.04, 0.05, rust)


def _warden_key(r, metal, t):
    """The Warden's key: long and heavy steel, a trefoil bow crowned over an ember, a square shank and
    a stepped double bit."""
    dark, bright = _dim(metal, 0.65), _bright(metal, 1.1, 15)
    for cy, cz in ((0.44, 0.0), (0.32, -0.12), (0.32, 0.12)):  # three lobes of the trefoil
        for i in range(8):
            a = i * math.tau / 8
            r.part(
                "cube", 0, cy + math.cos(a) * 0.09, cz + math.sin(a) * 0.09, 0.05, 0.05, 0.07, metal, rx=-a
            )
    pulse = 1 + math.sin(t * 3) * 0.08
    r.part("sphere", 0, 0.35, 0, 0.12 * pulse, 0.12 * pulse, 0.12 * pulse, EMBER, glow=True)
    for dz in (-0.08, 0, 0.08):  # the crown on top
        r.part("cone", 0, 0.58 + (0.03 if dz == 0 else 0), dz, 0.05, 0.1, 0.05, bright)
    r.part("cube", 0, 0.54, 0, 0.05, 0.03, 0.22, bright)
    _key_collar(r, 0.2, metal, 0.12)
    r.part("cube", 0, -0.12, 0, 0.07, 0.62, 0.07, metal, ry=math.pi / 4)  # a long square shank
    for y in (0.08, -0.12, -0.32):  # bands along it
        r.part("cube", 0, y, 0, 0.09, 0.03, 0.09, dark)
    r.part("cube", 0, -0.46, 0, 0.08, 0.06, 0.08, metal)  # the tip
    for y, reach in ((-0.44, 0.2), (-0.36, 0.14), (-0.28, 0.08)):  # a stepped bit, both sides
        for side in (-1, 1):
            r.part("cube", 0, y, side * (0.04 + reach / 2), 0.05, 0.07, reach, bright if side > 0 else metal)


def _briar_key(r, metal, t):
    """The briar key: no ring at all, a bow of three thorny branches twisted together, a crooked shank
    wound with vine and a bit shaped like a leaf."""
    vine, leaf, thorn = (60, 100, 44), (80, 140, 60), (70, 50, 30)
    for k in range(3):  # three branches curling up and out from the collar
        a = (k - 1) * 0.75
        with r.at(0, 0.16, 0, rx=-a):
            r.part("cube", 0, 0.12, 0, 0.045, 0.24, 0.045, metal)
            with r.at(0, 0.24, 0, rx=-a * 0.8):
                r.part("cube", 0, 0.08, 0, 0.04, 0.16, 0.04, metal)
                r.part("sphere", 0, 0.17, 0, 0.07, 0.05, 0.1, leaf)  # a bud at the end
            for y in (0.06, 0.18):  # thorns along each branch
                r.part("cone", 0, y, 0.03, 0.02, 0.06, 0.02, thorn, rx=math.pi / 2)
    _key_collar(r, 0.14, metal, 0.09)
    for k in range(3):  # a crooked shank, bent at each node
        with r.at(0, 0.04 - k * 0.12, 0, rx=0.12 * (1 if k % 2 else -1)):
            r.part("cube", 0, -0.06, 0, 0.05, 0.13, 0.05, metal)
            r.part("cube", 0, -0.04, 0, 0.065, 0.025, 0.065, vine, ry=k * 0.8)  # a vine wound down it
    with r.at(0, -0.3, 0.1, rx=math.pi / 2):  # the leaf-shaped bit, veined
        r.part("sphere", 0, 0, 0, 0.04, 0.2, 0.11, leaf)
        r.part("cube", 0.02, 0, 0, 0.01, 0.18, 0.015, vine)
        for side in (-1, 1):
            r.part("cube", 0.02, 0.02, side * 0.03, 0.01, 0.06, 0.01, vine, rx=side * 0.7)


def _forge_key(r, metal, t):
    """The forge key: blackened iron, its bow an anvil, a thick riveted shank and a hooked bit still
    glowing from the forge."""
    dark = _dim(metal, 0.65)
    hot = (230, 110, 40)
    glow = 0.9 + math.sin(t * 2.5) * 0.1
    r.part("cube", 0, 0.42, 0, 0.07, 0.07, 0.36, metal)  # the anvil's face
    r.part("wedge", 0, 0.42, 0.24, 0.07, 0.07, 0.12, metal, rx=math.pi / 2)  # its horn
    r.part("cube", 0, 0.33, 0, 0.06, 0.12, 0.16, dark)  # waist
    r.part("cube", 0, 0.24, 0, 0.08, 0.06, 0.28, metal)  # foot
    for side in (-1, 1):  # its splayed feet
        r.part("wedge", 0, 0.22, side * 0.15, 0.08, 0.04, 0.06, dark, rx=side * math.pi / 2)
    for z in (-0.1, 0.06):  # sparks still flying off the hot face
        r.part("cube", 0.01, 0.52 + glow * 0.03, z, 0.015, 0.015, 0.015, (255, 200, 90), glow=True)
    r.part(
        "cube", 0, 0.47, -0.04, 0.072, 0.02, 0.12, tuple(int(c * glow) for c in hot), glow=True
    )  # hot face
    _key_collar(r, 0.16, metal, 0.12)
    r.part("cube", 0, -0.06, 0, 0.09, 0.36, 0.09, metal)  # a thick shank
    for y in (0.1, -0.16):  # bands hammered round it
        r.part("cube", 0, y, 0, 0.11, 0.03, 0.11, dark)
    for y in (0.05, -0.08, -0.2):  # rivets driven through it
        r.part("sphere", 0.05, y, 0, 0.03, 0.03, 0.03, (90, 84, 80))
    r.part("cube", 0, -0.26, 0.08, 0.06, 0.06, 0.16, hot, glow=True)  # the hooked bit, glowing
    r.part("cube", 0, -0.2, 0.15, 0.06, 0.14, 0.05, hot, glow=True)
    r.part("cube", 0, -0.14, 0.12, 0.06, 0.04, 0.06, (255, 170, 70), glow=True)


KEY_SHAPES = {
    "cell_key": _cell_key,
    "warden_key": _warden_key,
    "briar_key": _briar_key,
    "forge_key": _forge_key,
}


# Each relic sigil: (rim metal, core glow, the device on its faces).
SIGILS = {
    "ember_sigil": ((112, 80, 68), EMBER, "flame"),
    "verdant_sigil": ((62, 92, 70), (110, 230, 120), "leaf"),
    "iron_sigil": ((96, 98, 108), (120, 200, 255), "gear"),
    "argent_sigil": ((176, 182, 198), (214, 230, 255), "crescent"),
}


def sigil(r, id_, t=0.0):
    """A relic sigil: a bevelled disc ringed with studs and runes, a glowing core that pulses, and its
    device raised on both faces. Faces +X / -X, like a coin on edge. (A `cyl`'s size is its
    diameter: the disc is 1.1 across.)"""
    rim, core, device = SIGILS[id_]
    pulse = 1 + math.sin(t * 3.5) * 0.08
    dark = _dim(rim, 0.6)
    with r.at(0, 0, 0, rz=math.pi / 2, s=1.5):  # local Y is the disc's normal, local X its "up"
        r.part("cyl", 0, 0, 0, 0.72, 0.1, 0.72, dark)  # the outer bevel
        r.part("cyl", 0, 0, 0, 0.66, 0.14, 0.66, rim)
        r.part("cyl", 0, 0, 0, 0.46, 0.16, 0.46, dark)  # the sunken field
        r.part("cyl", 0, 0, 0, 0.26 * pulse, 0.18, 0.26 * pulse, core, glow=True)
        for face in (1, -1):
            y = 0.075 * face
            for i in range(12):  # studs around the rim
                a = i * math.tau / 12
                r.part("cube", math.cos(a) * 0.28, y, math.sin(a) * 0.28, 0.035, 0.02, 0.035, _bright(rim))
            for i in range(8):  # runes cut into the field around the core
                a = i * math.tau / 8 + 0.2
                ra = 0.185 + 0.01 * (i % 3)
                r.part(
                    "cube",
                    math.cos(a) * ra,
                    y + 0.01 * face,
                    math.sin(a) * ra,
                    0.015,
                    0.02,
                    0.045,
                    _dim(core, 0.75),
                    ry=-a + (i % 2) * 0.6,
                    glow=True,
                )
            with r.at(0, 0.1 * face, 0, s=0.6):
                _sigil_device(r, device, core, 0.0, t)


def _sigil_device(r, device, core, y, t):
    """The raised device at a sigil's heart, in the disc's plane (local X is up)."""
    ink = (40, 26, 20)  # a dark silhouette against the glowing core
    if device == "flame":  # three tongues of fire licking upward
        lick = math.sin(t * 7) * 0.04
        r.part("cube", 0.06, y, 0, 0.36 + lick, 0.03, 0.08, ink)
        for side in (-1, 1):
            r.part("cube", 0.0, y, 0.09 * side, 0.24, 0.03, 0.06, ink, ry=0.45 * side)
        r.part("cube", -0.14, y, 0, 0.06, 0.03, 0.26, ink)  # the bed of embers
    elif device == "leaf":  # three leaves on a curling stem
        for i in range(3):
            a = i * math.tau / 3 + t * 0.4
            with r.at(math.cos(a) * 0.12, y, math.sin(a) * 0.12, ry=-a):
                r.part("cube", 0.04, 0, 0, 0.18, 0.03, 0.07, ink)
        r.part("cube", 0, y, 0, 0.06, 0.035, 0.06, ink)
    elif device == "crescent":  # a crescent moon, horns up, a star between its horns
        for i in range(7):
            a = math.pi * (1.1 + 0.8 * i / 6)  # the bow of it, round the disc's lower half
            r.part("cube", math.sin(a) * 0.2, y, math.cos(a) * 0.2, 0.07, 0.03, 0.08, ink, ry=-a)
        r.part("cube", 0.12, y, 0, 0.05, 0.035, 0.05, ink, ry=math.pi / 4 + t * 0.3)  # the star
    else:  # a gear around an anvil
        turn = t * 0.6
        for i in range(8):
            a = i * math.tau / 8 + turn
            r.part("cube", math.cos(a) * 0.24, y, math.sin(a) * 0.24, 0.07, 0.03, 0.06, ink, ry=-a)
        r.part("cube", 0.04, y, 0, 0.06, 0.035, 0.22, ink)  # the anvil's face
        r.part("cube", -0.05, y, 0, 0.12, 0.035, 0.08, ink)  # its waist


def eruption(r, glow, flame, t, radius=1.0):
    """The Warden's fire from below: a glowing ring of cracks on the floor, then a column of flame,
    as wide as the burst's `radius` (1 m for most; the Keystone's torch strikes wider and taller)."""
    k = radius
    if glow > 0:
        for i in range(8):
            a = i * math.pi / 4 + t * 0.5
            r.part(
                "cube", math.cos(a) * 0.8 * k, 0.03, math.sin(a) * 0.8 * k, 0.5 * k, 0.03, 0.08,
                (255, rround(80 + 120 * glow), 30), ry=-a + math.pi / 2, glow=True,
            )  # fmt: skip
        r.part("cyl", 0, 0.02, 0, 0.6 * glow * k, 0.02, 0.6 * glow * k, EMBER, glow=True)
    if flame > 0:
        h = 2.6 * flame * (1 + 0.4 * (k - 1))
        r.part("cone", 0, h / 2, 0, 1.4 * k, h, 1.4 * k, (255, 120, 40), glow=True)
        r.part("cone", 0, h * 0.45, 0, 0.8 * k, h * 1.1, 0.8 * k, (255, 220, 130), glow=True)


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
from ashen_vault.render import (  # noqa: E402
    cemetery_models,
    forge_models,
    moon_models,
    prison_models,
    sewer_models,
    sunken_models,
)
