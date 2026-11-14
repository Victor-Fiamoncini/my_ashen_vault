"""Weapon categories, their attacks and the secret moves hidden in some of them. Pure data, no raylib.

Every weapon has a light attack (tap), a heavy one (hold, then release) and a quick one of its own
(a fast double-click, see `DOUBLE_CLICK`). Some categories also hide a secret attack that only comes
out in the right situation; see `secret()`. A weapon's `weight` class scales what each of its attacks
costs and deals (`WEIGHTS`)."""

from dataclasses import dataclass, replace

LIGHT, HEAVY, QUICK, SECRET = "light", "heavy", "quick", "secret"


@dataclass(frozen=True)
class Attack:
    name: str
    motion: str  # animation key, see render/models.py MOTIONS
    kind: str = LIGHT
    damage: float = 1.0  # multiplier on Combat.damage
    reach: float = 1.0  # multiplier on the weapon's reach
    cone: float = 0.6  # min cos(angle) between facing and target; below 0 hits all around
    targets: int = 1  # most enemies one swing can hit
    poise: float = 1.0  # multiplier on the stagger check against enemy poise
    stamina: float = 0.08  # ST spent (0..1)
    lunge: float = 0.0  # metres stepped forward as the hit lands
    pierce_def: bool = False  # ignores enemy defence
    time: float = 1.0  # swing length, as a multiple of Player.SWING_TIME (before the weapon's tempo)
    hit_at: float = 0.4  # fraction of the swing at which the blow lands
    min_power: float = 0.0  # lowest ATK gauge the swing counts as (quick attacks never hit at nothing)
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
COMBO_HITS = 2  # club: hits already landed on one foe before the Skull-ringer comes out
DOUBLE_CLICK = 0.3  # seconds after a light swing starts that a second click turns it into the quick attack


def _light(name, motion, **kw):
    return Attack(name, motion, LIGHT, **kw)


def _heavy(name, motion, stamina, **kw):
    return Attack(name, motion, HEAVY, stamina=stamina, **{"time": 1.5, "hit_at": 0.45, **kw})


def _quick(name, motion, **kw):
    base = {"damage": 0.7, "stamina": 0.05, "time": 0.6, "hit_at": 0.35, "min_power": 0.5}
    return Attack(name, motion, QUICK, **{**base, **kw})


def _secret(name, motion, stamina, **kw):
    return Attack(name, motion, SECRET, stamina=stamina, **{"time": 1.4, "hit_at": 0.45, **kw})


MOVESETS = {
    "fists": {
        LIGHT: _light("Jab", "jab", stamina=0.05),
        HEAVY: _heavy("Hook", "hook", 0.26, damage=1.4, poise=1.5),
        QUICK: _quick("One-two", "onetwo", damage=0.55, pulses=2, pulse_gap=0.12, pulse_damage=1.0),
    },
    "sword": {
        LIGHT: _light("Slash", "slash"),
        HEAVY: _heavy("Overhead chop", "chop", 0.39, damage=1.6, poise=1.5),
        QUICK: _quick("Twin cut", "twin", damage=0.55, pulses=2, pulse_gap=0.12, pulse_damage=1.0),
    },
    "greatsword": {
        LIGHT: _light("Wide sweep", "sweep", cone=0.25, targets=3, stamina=0.09),
        HEAVY: _heavy("Overhead cleave", "chop", 0.42, damage=2.0, poise=2.0),
        QUICK: _quick("Pommel crack", "pommel", damage=0.8, reach=0.6, poise=2.2),
    },
    "katana": {
        LIGHT: _light("Quick slash", "slash"),
        HEAVY: _heavy("Lunging thrust", "thrust", 0.39, damage=1.7, reach=1.4, cone=0.8, lunge=1.0),
        QUICK: _quick("Iaido flick", "flick", damage=0.9, cone=0.8, pierce_def=True),
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
        QUICK: _quick(
            "Double crack", "doublelash", damage=0.5, cone=0.85, pulses=2, pulse_gap=0.14, pulse_damage=1.0
        ),
        SECRET: _secret("Snare", "snare", 0.4, damage=1.1, cone=0.85, poise=99, pull=1.2),
    },
    "mace": {
        LIGHT: _light("Bash", "pound", pierce_def=True, stamina=0.1),
        HEAVY: _heavy("Crush", "chop", 0.45, damage=1.8, poise=2.5, pierce_def=True),
        QUICK: _quick("Hilt rap", "rap", poise=2.0, pierce_def=True),
    },
    "club": {
        LIGHT: _light("Clout", "bash", poise=1.3, stamina=0.09),
        HEAVY: _heavy("Overhand smash", "chop", 0.4, damage=1.7, poise=2.2),
        QUICK: _quick("Butt rap", "rap", poise=1.8),
        SECRET: _secret("Skull-ringer", "chop", 0.4, damage=2.0, poise=99, time=1.0, hit_at=0.4),
    },
    "axe": {
        LIGHT: _light("Hew", "hew", damage=1.1, stamina=0.1),
        HEAVY: _heavy("Splitting chop", "cleave", 0.45, damage=1.8, poise=1.8),
        QUICK: _quick("Bearded hook", "hook_cut", pull=0.6),
        SECRET: _secret("Leaping Hew", "leap", 0.55, damage=2.2, poise=2.5, lunge=1.5, reach=1.1),
    },
    "hammer": {
        LIGHT: _light("Smash", "pound", poise=1.5, stamina=0.09),
        HEAVY: _heavy("Ground slam", "slam", 0.45, damage=1.5, reach=1.1, cone=-1, targets=8, poise=2.0),
        QUICK: _quick("Haft drive", "drive", reach=0.7, poise=2.2),
        SECRET: _secret(
            "Aftershock", "slam", 0.42, damage=1.6, reach=1.3, cone=-1, targets=8, poise=2.5, pulses=2
        ),
    },
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
        QUICK: (0.8, 1.0, 0.85),
        SECRET: (0.8, 1.0, 0.9),
    },
    MEDIUM: dict.fromkeys((LIGHT, HEAVY, QUICK, SECRET), (1.0, 1.0, 1.0)),
    HEAVYWEIGHT: {
        LIGHT: (1.2, 1.08, 1.2),
        HEAVY: (1.3, 1.15, 1.3),
        QUICK: (1.1, 1.05, 1.15),
        SECRET: (1.25, 1.1, 1.25),
    },
    GREAT: {
        LIGHT: (1.4, 1.15, 1.4),
        HEAVY: (1.6, 1.3, 1.6),
        QUICK: (1.2, 1.1, 1.3),
        SECRET: (1.4, 1.2, 1.4),
    },
}
WEIGHT_TEMPO = {LIGHTWEIGHT: -0.1, MEDIUM: 0.0, HEAVYWEIGHT: 0.1, GREAT: 0.2}
WEIGHT_NAMES = {LIGHTWEIGHT: "Light", MEDIUM: "Medium", HEAVYWEIGHT: "Heavy", GREAT: "Great"}


def moveset(item):
    return MOVESETS[item.category or "sword"]


def weight(item):
    return item.weight or MEDIUM


def sized(item, a):
    """Attack `a` as `item`'s weight class performs it."""
    st, dmg, poise = WEIGHTS[weight(item)][a.kind]
    if (st, dmg, poise) == (1.0, 1.0, 1.0):
        return a
    return replace(a, stamina=a.stamina * st, damage=a.damage * dmg, poise=a.poise * poise)


def attack(item, kind=LIGHT):
    """One of a weapon's attacks (light, heavy, quick or, if it has one, secret), sized to its weight."""
    if kind is True:  # attack(item, heavy=True) style callers
        kind = HEAVY
    return sized(item, moveset(item)[kind])


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
