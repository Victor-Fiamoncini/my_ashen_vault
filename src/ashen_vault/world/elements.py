"""Elements: lightning bites iron, fire splashes off what was forged in it. Pure logic, no raylib.

An attack's element is `"lightning"`, `"fire"` or None. Spell bolts carry theirs in their effect,
weapons in `Item.element`."""

LIGHTNING_MULT = 1.5  # conductive foes (iron) take this much more from lightning
FIREPROOF_MULT = 0.5  # fireproof foes take this much of a fire attack
WEAPON_BURN = (3.0, 3)  # seconds and HP per second a fire weapon leaves a foe burning

# Bolt effects and the element each carries.
EFFECT_ELEMENT = {"flame": "fire", "thunder": "lightning"}


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
