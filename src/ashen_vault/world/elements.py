"""Elements: lightning bites iron, fire splashes off what was forged in it. Pure logic, no raylib.

Stone foes are `brittle`: a blunt blow (`STRIKE_CATEGORIES`) cracks them, an edge skates off.

An attack's element is `"lightning"`, `"fire"` or None. Spell bolts carry theirs in their effect,
weapons in `Item.element`."""

LIGHTNING_MULT = 1.5  # conductive foes (iron) take this much more from lightning
FIREPROOF_MULT = 0.5  # fireproof foes take this much of a fire attack
WEAPON_BURN = (3.0, 3)  # seconds and HP per second a fire weapon leaves a foe burning

BRITTLE_STRIKE_MULT = 1.5  # a blunt weapon on a brittle (stone) foe: it cracks
BRITTLE_EDGE_MULT = 0.75  # any other weapon on one: the edge skates off the stone
STRIKE_CATEGORIES = frozenset({"club", "hammer", "mace", "fists"})

# Bolt effects and the element each carries.
EFFECT_ELEMENT = {"flame": "fire", "thunder": "lightning"}
# Shots that land like a blunt blow on a brittle foe (Sister Vell's Mortar Shard).
CRACKING_EFFECTS = frozenset({"mortar"})


def mult(type_, element):
    """Damage multiplier for an attack of `element` landing on an enemy of `type_`."""
    if element == "lightning" and type_.conductive:
        return LIGHTNING_MULT
    if element == "fire" and type_.fireproof:
        return FIREPROOF_MULT
    return 1.0


def burns(type_, element):
    """Whether a fire attack sets this foe alight."""
    return element == "fire" and not type_.fireproof


def staggers(type_, element):
    """Lightning jolts conductive foes off their feet whatever their poise (bosses excepted)."""
    return element == "lightning" and type_.conductive and not type_.boss


def blunt(weapon):
    """Whether `weapon` (an Item, or None for bare fists) strikes with a blunt blow that cracks stone."""
    return (weapon.category if weapon is not None else "fists") in STRIKE_CATEGORIES


def brittle_mult(type_, weapon):
    """Damage multiplier for a blow of `weapon` (an Item, or None for bare fists) on `type_`."""
    if not type_.brittle:
        return 1.0
    return BRITTLE_STRIKE_MULT if blunt(weapon) else BRITTLE_EDGE_MULT


def shot_mult(type_, effect):
    """Damage multiplier for one of your shots of `effect` on `type_`: spells leave stone alone, except
    the ones that crack it."""
    return BRITTLE_STRIKE_MULT if type_.brittle and effect in CRACKING_EFFECTS else 1.0
