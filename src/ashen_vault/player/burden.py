"""Equipment load: what your gear weighs against what your strength can carry. Pure, no raylib.

Every weapon, shield and piece of armor has a `mass` in kilograms. Their total against your capacity
(which grows with STR) puts you in a load tier: light gear lets you move a touch quicker, heavy gear
slows your stride, your ST refill and makes every swing, sprint and block cost more."""

from dataclasses import dataclass

from ashen_vault.player.inventory import ARMOR_SLOTS, HANDS, SPELL
from ashen_vault.player.items import Items

BASE_CAPACITY = 20.0  # kilograms anyone can carry
CAPACITY_PER_STR = 2.0


@dataclass(frozen=True)
class Tier:
    name: str
    upto: float  # highest load / capacity ratio in this tier
    speed: float  # walking speed multiplier
    refill: float  # ST refill rate multiplier
    cost: float  # ST cost multiplier for attacks, sprinting and blocking


TIERS = (
    Tier("Light", 0.3, 1.05, 1.1, 0.95),
    Tier("Medium", 0.6, 1.0, 1.0, 1.0),
    Tier("Heavy", 1.0, 0.85, 0.8, 1.15),
    Tier("Overloaded", float("inf"), 0.6, 0.55, 1.35),
)


def load(slots):
    """Kilograms of gear in `slots` (an Inventory's slots dict): a two-hander counts once."""
    worn = {slots.get(h) for h in HANDS} | {slots.get(a) for a in ARMOR_SLOTS}
    return sum(Items.get(id_).mass for id_ in worn if id_ and id_ != SPELL)


def capacity(strength):
    return BASE_CAPACITY + CAPACITY_PER_STR * strength


def tier(kg, cap):
    ratio = kg / cap if cap > 0 else float("inf")
    return next(t for t in TIERS if ratio <= t.upto)


def of(inventory, stats):
    """The load tier `inventory`'s gear puts a body with `stats` in."""
    return tier(load(inventory.slots), capacity(stats.strength))
