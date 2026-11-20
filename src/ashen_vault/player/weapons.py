"""Weapon categories, their attacks and the secret moves hidden in some of them. Pure data, no raylib.

Every weapon has a light attack (tap) and a heavy one (hold, then release). Some categories also
hide a secret attack that only comes out in the right situation; see `secret()`. A weapon's `weight` class scales what each of its attacks
costs and deals (`WEIGHTS`)."""

from dataclasses import dataclass, replace

LIGHT, HEAVY, SECRET = "light", "heavy", "secret"


@dataclass(frozen=True)
class Attack:
    name: str
    motion: str  # animation key, see render/models.py MOTIONS
    kind: str = LIGHT
    damage: float = 1.0  # multiplier on Combat.damage
    reach: float = 1.0  # multiplier on the weapon's reach
    cone: float = 0.6  # min cos(angle) between facing and target; below 0 hits all around
    targets: int = 1  # most enemies one swing can hit (SINGLE; cuts CLEAVE)
    poise: float = 1.0  # multiplier on the stagger check against enemy poise
    stamina: float = 0.08  # ST spent (0..1)
    lunge: float = 0.0  # metres stepped forward as the hit lands
    pierce_def: bool = False  # ignores enemy defence
    time: float = 1.0  # swing length, as a multiple of Player.SWING_TIME (before the weapon's tempo)
    hit_at: float = 0.4  # fraction of the swing at which the blow lands
    pull: float = 0.0  # metres the target is dragged toward you
    pulses: int = 1  # how many times the blow lands (a second, weaker shockwave)
    pulse_gap: float = 0.3  # seconds between the blows of a multi-pulse attack
    pulse_damage: float = 0.6  # each later blow's share of the first

    @property
    def heavy(self):
        return self.kind in (HEAVY, SECRET)


CHARGE_TIME = 0.35  # seconds a button must be held for a heavy attack
DRAW_HOLD = 1.2  # katana: seconds held perfectly still for the Sheathed Draw
SPRINT_GRACE = 0.4  # seconds after a sprint that still count as running into the swing
REVENGE_GRACE = 1.0  # seconds after a blow lands on you (or your shield) that the Aftershock is ready
COMBO_WINDOW = 2.0  # seconds between club hits on the same foe that keep the combo alive
GAUGE_REFILL = 1.5  # every weapon's ATK gauge takes this many times its `speed` to refill
COMBO_HITS = 2  # club: hits already landed on one foe before the Skull-ringer comes out

# How many foes one blow can strike. A cut that travels across the arc goes through everyone in reach
# inside it (nearest first); a thrust, a jab or a blow that drops straight down stops on the first.
SINGLE = 1
CLEAVE = 3
CLEAVE_CONE = 0.45  # a cut's arc: about 63 degrees either side, where a straight blow keeps 0.6


def _light(name, motion, **kw):
    return Attack(name, motion, LIGHT, **kw)


def _heavy(name, motion, stamina, **kw):
    return Attack(name, motion, HEAVY, stamina=stamina, **{"time": 1.5, "hit_at": 0.45, **kw})


def _secret(name, motion, stamina, **kw):
    return Attack(name, motion, SECRET, stamina=stamina, **{"time": 1.4, "hit_at": 0.45, **kw})


MOVESETS = {
    "fists": {
        LIGHT: _light("Jab", "jab", stamina=0.05),
        HEAVY: _heavy("Hook", "hook", 0.26, damage=1.4, poise=1.5, cone=CLEAVE_CONE, targets=2),
    },
    "sword": {
        LIGHT: _light("Slash", "slash", cone=CLEAVE_CONE, targets=CLEAVE),
        HEAVY: _heavy("Overhead chop", "chop", 0.39, damage=1.6, poise=1.5),
    },
    "greatsword": {
        LIGHT: _light("Wide sweep", "sweep", cone=0.25, targets=4, stamina=0.09),
        HEAVY: _heavy("Overhead cleave", "chop", 0.42, damage=2.0, poise=2.0, targets=2),
    },
    "katana": {
        LIGHT: _light("Quick slash", "katana_cut", cone=CLEAVE_CONE, targets=CLEAVE),
        HEAVY: _heavy("Lunging thrust", "thrust", 0.39, damage=1.7, reach=1.4, cone=0.8, lunge=1.0),
        SECRET: _secret(
            "Sheathed Draw",
            "draw",
            0.45,
            damage=2.4,
            reach=1.2,
            cone=0.2,
            targets=3,
            poise=2.0,
            pierce_def=True,
            time=0.9,
            hit_at=0.3,
        ),
    },
    "whip": {
        LIGHT: _light("Crack", "lash", cone=0.85),
        HEAVY: _heavy("Wide lash", "sweep", 0.39, damage=1.2, cone=0.1, targets=4),
        SECRET: _secret("Snare", "snare", 0.4, damage=1.1, cone=0.85, poise=99, pull=1.2),
    },
    "mace": {
        LIGHT: _light("Bash", "pound", pierce_def=True, stamina=0.1),
        HEAVY: _heavy("Crush", "chop", 0.45, damage=1.8, poise=2.5, pierce_def=True),
    },
    "club": {
        LIGHT: _light("Clout", "bash", poise=1.3, stamina=0.09, cone=0.5, targets=2),
        HEAVY: _heavy("Overhand smash", "chop", 0.4, damage=1.7, poise=2.2),
        SECRET: _secret("Skull-ringer", "chop", 0.4, damage=2.0, poise=99, time=1.0, hit_at=0.4),
    },
    "axe": {
        LIGHT: _light("Hew", "hew", damage=1.1, stamina=0.1, cone=0.5, targets=2),
        HEAVY: _heavy("Splitting chop", "cleave", 0.45, damage=1.8, poise=1.8, targets=2),
        SECRET: _secret("Leaping Hew", "leap", 0.55, damage=2.2, poise=2.5, lunge=1.5, reach=1.1),
    },
    "hammer": {
        LIGHT: _light("Smash", "pound", poise=1.5, stamina=0.09),
        HEAVY: _heavy("Ground slam", "slam", 0.45, damage=1.5, reach=1.1, cone=-1, targets=8, poise=2.0),
        SECRET: _secret(
            "Aftershock", "slam", 0.42, damage=1.6, reach=1.3, cone=-1, targets=8, poise=2.5, pulses=2
        ),
    },
}

# A few weapons swing their heavy differently from the rest of their category: the long katanas cut
# a reverse slash, high on the left and down across to the right, where the Katana lunges. Only the
# heavy changes; the light, the secret, the ST and the tempo stay the category's.
_REVERSE_CUT = _heavy(
    "Reverse cut", "slash_left", 0.39, damage=1.6, reach=1.1, cone=CLEAVE_CONE, targets=CLEAVE
)
HEAVY_OVERRIDES = {
    "moonless_tachi": _REVERSE_CUT,
    "nodachi": _REVERSE_CUT,
}

CATEGORY_NAMES = {
    "fists": "Fists",
    "sword": "Sword",
    "greatsword": "Greatsword",
    "katana": "Katana",
    "whip": "Whip",
    "mace": "Mace",
    "club": "Club",
    "axe": "Axe",
    "hammer": "Hammer",
}

# How long a category's swings take: light blades are quick, big iron is slow.
TEMPO = {
    "fists": 0.8,
    "katana": 0.8,
    "whip": 0.85,
    "sword": 1.0,
    "club": 1.0,
    "mace": 1.05,
    "axe": 1.05,
    "greatsword": 1.3,
    "hammer": 1.35,
}

# Weight classes: the movesets above are tuned for a medium weapon of each category. Lighter ones cost
# less ST and swing sooner; heavier ones cost more, hit harder and break poise better, and their heavy
# attacks feel it most. Per attack kind: (stamina, damage, poise) multipliers.
LIGHTWEIGHT, MEDIUM, HEAVYWEIGHT, GREAT = "light", "medium", "heavy", "great"
WEIGHTS = {
    LIGHTWEIGHT: {
        LIGHT: (0.8, 1.0, 0.85),
        HEAVY: (0.75, 0.95, 0.85),
        SECRET: (0.8, 1.0, 0.9),
    },
    MEDIUM: dict.fromkeys((LIGHT, HEAVY, SECRET), (1.0, 1.0, 1.0)),
    HEAVYWEIGHT: {
        LIGHT: (1.2, 1.08, 1.2),
        HEAVY: (1.3, 1.15, 1.3),
        SECRET: (1.25, 1.1, 1.25),
    },
    GREAT: {
        LIGHT: (1.4, 1.15, 1.4),
        HEAVY: (1.6, 1.3, 1.6),
        SECRET: (1.4, 1.2, 1.4),
    },
}
WEIGHT_TEMPO = {LIGHTWEIGHT: -0.1, MEDIUM: 0.0, HEAVYWEIGHT: 0.1, GREAT: 0.2}
WEIGHT_NAMES = {LIGHTWEIGHT: "Light", MEDIUM: "Medium", HEAVYWEIGHT: "Heavy", GREAT: "Great"}


def moveset(item):
    """`item`'s attacks by kind: its category's moveset, with its own heavy if it has one
    (`HEAVY_OVERRIDES`)."""
    moves = MOVESETS[item.category or "sword"]
    heavy = HEAVY_OVERRIDES.get(item.id)
    return {**moves, HEAVY: heavy} if heavy else moves


def weight(item):
    return item.weight or MEDIUM


def sized(item, a):
    """Attack `a` as `item`'s weight class performs it."""
    st, dmg, poise = WEIGHTS[weight(item)][a.kind]
    if (st, dmg, poise) == (1.0, 1.0, 1.0):
        return a
    return replace(a, stamina=a.stamina * st, damage=a.damage * dmg, poise=a.poise * poise)


def attack(item, kind=LIGHT):
    """One of a weapon's attacks (light, heavy or, if it has one, secret), sized to its weight."""
    if kind is True:  # attack(item, heavy=True) style callers
        kind = HEAVY
    return sized(item, moveset(item)[kind])


def refill_time(item):
    """Seconds an empty ATK gauge takes to fill again with `item` in hand."""
    return (item.speed or 1.0) * GAUGE_REFILL


def tempo(item):
    """Swing-length multiplier for a weapon: bigger weapons swing slower."""
    return TEMPO.get(item.category or "sword", 1.0) + WEIGHT_TEMPO[weight(item)]


def has_secret(item):
    return SECRET in moveset(item)


@dataclass(frozen=True)
class Context:
    """What the player was doing as the attack started; secrets look at it."""

    sprinting: bool = False
    since_sprint: float = 99.0  # seconds since you last sprinted (0 while sprinting)
    still_t: float = 0.0  # seconds since you last moved
    charge_t: float = 0.0  # seconds the button was held
    combo: int = 0  # hits already landed in a row on the foe in front of you
    since_hit: float = 99.0  # seconds since a blow last landed on you or your shield


def secret(item, kind, ctx):
    """The secret attack this swing turns into, or None.

    - Katana, Sheathed Draw: hold a heavy perfectly still for DRAW_HOLD seconds.
    - Whip, Snare: a heavy while sprinting.
    - Axe, Leaping Hew: a heavy straight out of a sprint (SPRINT_GRACE).
    - Club, Skull-ringer: the third light blow in a row on the same foe.
    - Hammer, Aftershock: a heavy straight after a blow lands on you (REVENGE_GRACE).
    """
    if not has_secret(item):
        return None
    cat = item.category
    hit = None
    if kind == HEAVY:
        if cat == "katana":
            hit = ctx.charge_t >= DRAW_HOLD and ctx.still_t >= ctx.charge_t
        elif cat == "whip":
            hit = ctx.sprinting or ctx.since_sprint <= 0.15
        elif cat == "axe":
            hit = ctx.since_sprint <= SPRINT_GRACE
        elif cat == "hammer":
            hit = ctx.since_hit <= REVENGE_GRACE
    elif kind == LIGHT and cat == "club":
        hit = ctx.combo >= COMBO_HITS
    return attack(item, SECRET) if hit else None


# --- weapon arts ----------------------------------------------------------------------------------
# A few weapons hide an art: release a heavy with both the ATK gauge and the heavy charge full, and
# with the MP to pay for it, and the swing looses something more than steel (the Ashblade spills fire).
CONE, BOLT, VOLLEY, RING, WAVE = "cone", "bolt", "volley", "ring", "wave"


@dataclass(frozen=True)
class Art:
    id: str
    name: str
    mp: int  # MP it costs; short of it, the swing is a plain heavy
    # CONE (a gout of flame ahead), BOLT (one shot), VOLLEY (a fan of shots), RING (all around), WAVE (one
    # wide crescent that cuts through every foe in its path)
    kind: str
    damage: float  # multiplier on the weapon's full-gauge blow (Combat.damage)
    rgb: tuple  # its colour on the HUD bar and in the world
    reach: float = 0.0  # metres a cone or ring reaches
    element: str | None = None  # "fire" burns what it hits; elements.mult applies to every art
    effect: str = "flame"  # a shot's look and touch (Projectile.effect)
    speed: float = 0.0  # a shot's speed (0: the spell bolt's)
    count: int = 1  # shots in a volley
    spread: float = 0.0  # radians between a volley's shots
    width: float = 0.0  # a wave's breadth, in metres
    life: float = 0.0  # seconds a wave flies
    motion: str | None = None  # the swing it plays as, when not the weapon's heavy (`models.MOTIONS`)


ARTS = {
    "ashblade": Art("ember_spill", "Ember Spill", 6, CONE, 1.3, (255, 110, 40), reach=4.5, element="fire"),
    "stormbrand": Art(
        "thunderstroke",
        "Thunderstroke",
        6,
        BOLT,
        1.6,
        (150, 200, 255),
        element="lightning",
        effect="thunder",
        speed=16.0,
    ),
    "thornlash": Art(
        "thorn_volley", "Thorn Volley", 5, VOLLEY, 0.6, (140, 220, 70), effect="thorn", count=3, spread=0.16
    ),
    "slagbreaker": Art("slag_burst", "Slag Burst", 8, RING, 1.2, (255, 80, 20), reach=4.0, element="fire"),
    # The bell-keepers' brazier swings round in a wheel of sparks that kindles every cold fire it passes.
    "torch_greathammer": Art(
        "brand_sweep", "Brand Sweep", 7, RING, 1.1, (255, 150, 50), reach=3.5, element="fire"
    ),
    # The stone's seams split and spit one coal down your aim.
    "ember_stone_sword": Art(
        "kindle_seam",
        "Kindle Seam",
        5,
        BOLT,
        1.4,
        (255, 120, 50),
        element="fire",
        effect="flame",
        speed=14.0,
    ),
    # The tachi is drawn in one stroke and its cut flies on as a crescent of pale light.
    "moonless_tachi": Art(
        "pale_crescent",
        "Pale Crescent",
        12,
        WAVE,
        1.6,
        (190, 215, 255),
        effect="crescent",
        speed=11.0,
        width=2.4,
        life=0.9,
        motion="draw",
    ),
    # The chapel's glass greatsword sheds its stored moonlight down the swing as one narrow, piercing ray.
    "vesper_moonbrand": Art(
        "vesper_ray",
        "Vesper Ray",
        16,
        WAVE,
        2.2,
        (150, 225, 240),
        effect="moonray",
        speed=24.0,
        width=0.7,
        life=0.75,
    ),
}


def art(item):
    """The art `item` hides, or None."""
    return ARTS.get(item.id) if item is not None else None
