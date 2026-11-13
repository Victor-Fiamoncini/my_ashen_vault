"""What a smashed barrel, crate or urn holds: usually a few coins, rarely a potion, often nothing.
Rolled from the prop's key, so the same barrel always holds the same thing."""

import zlib

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
