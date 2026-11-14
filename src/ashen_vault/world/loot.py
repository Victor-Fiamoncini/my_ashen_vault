"""What a smashed barrel, crate or urn holds: usually a few coins, rarely a potion, often nothing.
Rolled from the prop's key, so the same barrel always holds the same thing."""

import zlib

from ashen_vault.player.items import Items

POTION_CHANCE = 12  # percent
GOLD_CHANCE = 50  # percent, after the potion roll
GOLD = range(2, 10)
POTIONS = ("red_tonic", "blue_moss")


def roll(key, props=None):
    """(gold, item or None) for the breakable with this key. Map props `item=` / `gold=` override."""
    props = props or {}
    if "item" in props or "gold" in props:
        return int(props.get("gold") or 0), props.get("item")
    h = zlib.crc32(key.encode())
    pick = h % 100
    if pick < POTION_CHANCE:
        return 0, POTIONS[(h >> 8) % len(POTIONS)]
    if pick < POTION_CHANCE + GOLD_CHANCE:
        return GOLD[(h >> 8) % len(GOLD)], None
    return 0, None


GEAR = ("weapon", "shield", "armor")
SPARE_SCROLL_GOLD = 40  # what a scroll you have already learned fetches (scrolls carry no price)


def already_owned(inv, spells, item_id):
    """True if `item_id` is gear (weapon, shield, armor) you already carry, or a scroll whose spell
    you know or whose copy you carry: something a second copy of would only clutter Belongings."""
    item = Items.get(item_id)
    if item.kind in GEAR:
        return inv.has(item_id)
    if item.kind == "scroll":
        return item.spell in spells or inv.has(item_id)
    return False


def claim(inv, spells, item_id):
    """(item to add or None, gold instead) for finding `item_id`: a spare copy of something you already
    own is worth half its price in gold (a learned scroll a flat SPARE_SCROLL_GOLD) rather than a
    duplicate in your pack."""
    if not already_owned(inv, spells, item_id):
        return item_id, 0
    item = Items.get(item_id)
    return None, (SPARE_SCROLL_GOLD if item.kind == "scroll" else item.price // 2)


def spare_message(gold):
    """The note under "Found ..." when a find was a spare copy, paid out by `claim`."""
    return f"You already own one. It fetches {{{gold} gold}}."
