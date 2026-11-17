"""Durability: weapons, shields and armor wear down with use. Pure logic, no raylib.

Each piece of gear has a maximum (`max_durability`); the inventory keeps what is left of it
(`Inventory.wear`). A weapon wears a little every swing that connects, a shield by how much of a blow it
stops, and every worn armor piece whenever a foe's blow lands on you (traps, falls and lava don't wear
it). At zero the piece is broken but still usable, only weakened: a broken weapon lands
`BROKEN_POWER` of its blows and can't loose its art, a broken shield stops and holds only
`BROKEN_GUARD` as well, and broken armor gives no DEF. Nothing mends at a shrine: Brannoc repairs gear
for gold (`repair_cost`), and a Mender's Kit (`KIT`) mends one piece whole anywhere."""

import dataclasses
import math

from ashen_vault.util import rround

GEAR = ("weapon", "shield", "armor")
WEAPON_MAX = {"light": 60, "medium": 80, "heavy": 100, "great": 120}
SHIELD_BASE = 40  # a shield's maximum is this plus its stability
ARMOR_MAX = {"body": 120, "hands": 80}

WEAPON_WEAR = 1  # per swing that connects, however many it strikes
BLOCK_WEAR_PER = 8  # a block wears a shield 1 for every this much damage it stops (at least 1)
BREAK_WEAR = 5  # a guard break wears the shield this much more
ARMOR_WEAR = 1  # each worn piece, per foe's blow that lands

BROKEN_POWER = 0.3  # a broken weapon's share of its blows
BROKEN_GUARD = 0.5  # a broken shield's share of its guard and stability
WORN = 0.25  # at or below this share of its maximum a piece is badly worn

REPAIR_SHARE = 0.3  # a full repair costs this share of the item's value
KIT = "menders_kit"  # the repair item


def max_durability(item):
    """The most durability `item` can have, or None when it never wears (fists, spells, items)."""
    if item is None or item.kind not in GEAR or item.id == "fists":
        return None
    if item.durability is not None:
        return item.durability
    if item.kind == "weapon":
        return WEAPON_MAX.get(item.weight or "medium", WEAPON_MAX["medium"])
    if item.kind == "shield":
        return SHIELD_BASE + rround(item.stability or 0)
    return ARMOR_MAX.get(item.slot or "body", ARMOR_MAX["body"])


def block_wear(stopped, broke=False):
    """How much a block that stopped `stopped` damage wears the shield."""
    return max(1, rround(stopped / BLOCK_WEAR_PER)) + (BREAK_WEAR if broke else 0)


def effective_shield(item, broken):
    """The shield as it blocks: a broken one stops and holds only `BROKEN_GUARD` as well."""
    if not broken:
        return item
    return dataclasses.replace(
        item, guard=(item.guard or 0) * BROKEN_GUARD, stability=(item.stability or 1) * BROKEN_GUARD
    )


def value(item):
    """What repairs are priced from: the item's price, or 100 a level for gear never sold."""
    return item.price or 100 * item.level


def repair_cost(item, missing):
    """Gold to mend `missing` points of `item`'s durability (0 when nothing is missing)."""
    top = max_durability(item)
    if not top or missing <= 0:
        return 0
    return max(1, math.ceil(value(item) * REPAIR_SHARE * missing / top))
