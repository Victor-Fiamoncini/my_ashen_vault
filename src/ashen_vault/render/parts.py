"""Pieces shared by every model module: colours, poses and the small parts (bars, flames, skulls,
hands, blades) the enemy, weapon and area models are built from. Imports no other model module."""

import functools
import itertools
import math
from contextlib import contextmanager

from ashen_vault.ai.enemy import COMBO_GAP
from ashen_vault.render import shapes
from ashen_vault.util import rround

BONE = (214, 204, 178)
RUST = (120, 70, 44)
IRON = (92, 92, 98)

EMBER = (255, 140, 50)
HIT_GLOW = (255, 105, 85)  # a glowing part in the moment a blow lands: red, like the body's flash
PASSAGE_DARK = (6, 5, 6)  # the black of a way on into the unknown, seen through a gate
HIT_TINT = (1.0, 0.45, 0.4)  # how far a struck body's pale flash colour leans to red (1 keeps a channel)


def hit_tint(rgb):
    """The colour a body part flashes when struck: its pale flash colour, leaning red by HIT_TINT."""
    return tuple(rround(c * k) for c, k in zip(rgb, HIT_TINT, strict=True))


WHITE = (255, 255, 255)


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


FIRE_CORE = (255, 246, 210)  # the white-hot heart of every fireball
FIRE_TIP = (255, 214, 110)  # the pale ends of its licking tongues

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


GOUT_HOT = (255, 225, 140)
GOUT_COOL = (210, 50, 20)

DARK_IRON = (58, 56, 60)

FLAME = (255, 170, 60)
FLAME_CORE = (255, 235, 150)

REALM_CRIMSON = ((150, 50, 44), (118, 36, 34))  # the realm's banners, everywhere: the city's red


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


def _ease(k):
    k = min(max(k, 0.0), 1.0)
    return k * k * (3 - 2 * k)


def _lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b, strict=True))


LEATHER = (70, 46, 30)
BRASS = (150, 130, 80)


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
