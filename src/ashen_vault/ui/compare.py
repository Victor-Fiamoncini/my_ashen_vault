"""What equipping (or taking off) an item would change, before you do it: ATK, DEF, how much a raised
shield stops (Block, in %), the readied spell's power (SPL, 0 with no spell in a slot) and the load
you carry.
Pure logic, no raylib, shared by the Belongings stats panel and the shop.

Each stat comes as (now, then); `better` says which way is an improvement (a lighter load is)."""

from ashen_vault.player import burden
from ashen_vault.player.inventory import SPELL, Inventory
from ashen_vault.player.spells import Spells
from ashen_vault.util import rround

STATS = ("ATK", "DEF", "Block", "SPL", "Load")
LOWER_IS_BETTER = ("Load",)


def swing_power(weapon, gloves):
    """A weapon's ATK; bare fists hit harder in gauntlets."""
    if weapon.category != "fists":
        return weapon.power
    return weapon.power + 2 * ((gloves.power or 0) if gloves else 0)


def numbers(inv, magic=0, spell=None):
    """ATK, DEF, Block (% the held shield stops), SPL (what the readied `spell` does at `magic`, when
    a slot holds it) and Load (kg) of what `inv` has equipped now."""
    shield = inv.shield_hand()
    return {
        "ATK": swing_power(inv.weapon_item(), inv.hands_item()),
        "DEF": inv.defense,
        "Block": rround(inv.hand_item(shield).guard * 100) if shield else 0,
        "SPL": Spells.power(spell, magic) if spell and inv.equipped(SPELL) else 0,
        "Load": burden.load(inv.slots),
    }


def held(item):
    """The id a slot stores for `item`: SPELL for a spell row, else the item's own."""
    return SPELL if item.kind == "spell" else item.id


def would_equip(inv, item, hand=None):
    """A copy of `inv` with `item` (a weapon, shield, armor or spell row, carried or not) equipped in
    `hand` (its default slot when None). None for anything that isn't worn or held, or that already
    sits where it would go."""
    if item.kind not in ("weapon", "shield", "armor", "spell"):
        return None
    id_ = held(item)
    if inv.equipped(id_) and (hand is None or inv.slots[hand] == id_):
        return None
    trial = Inventory.from_h(inv.to_h())
    if id_ != SPELL and not trial.has(id_):
        trial.add(id_)
    trial.equip(id_, None if item.two_handed else hand)
    return trial


def would_unequip(inv, item):
    """A copy of `inv` with `item` taken off, or None when it isn't equipped."""
    trial = Inventory.from_h(inv.to_h())
    return trial if trial.unequip(held(item)) else None


def preview(inv, item, hand=None, magic=0, spell=None, unequip=False):
    """{stat: (now, then)} for every stat equipping `item` in `hand` would change (taking it off when
    `unequip`), or {} when it changes nothing. `spell` is the readied spell's id; equipping a spell row
    readies that spell instead."""
    swap = (  # another spell into a slot already holding the spell: same slots, new spell readied
        item.kind == "spell"
        and not unequip
        and item.spell != spell
        and inv.equipped(SPELL)
        and (hand is None or inv.slots[hand] == SPELL)
    )
    if swap:
        trial = Inventory.from_h(inv.to_h())
    else:
        trial = would_unequip(inv, item) if unequip else would_equip(inv, item, hand)
    if trial is None:
        return {}
    then_spell = item.spell if item.kind == "spell" and not unequip else spell
    now, then = numbers(inv, magic, spell), numbers(trial, magic, then_spell)
    return {k: (now[k], then[k]) for k in STATS if now[k] != then[k]}


def better(stat, now, then):
    """+1 if going from `now` to `then` improves `stat`, -1 if it worsens it, 0 if equal."""
    if now == then:
        return 0
    up = then > now
    return (-1 if up else 1) if stat in LOWER_IS_BETTER else (1 if up else -1)


def fmt(value):
    """A stat for display: kilograms keep one decimal only when they need it."""
    return str(rround(value)) if float(value).is_integer() else f"{value:.1f}"


def deltas(changes):
    """The shop's compact line: [(text, better)] such as ("ATK +4", 1), ("Wt +3", -1)."""
    out = []
    for stat in STATS:
        if stat not in changes:
            continue
        now, then = changes[stat]
        diff = then - now
        name = "Wt" if stat == "Load" else stat
        unit = "%" if stat == "Block" else ""
        out.append((f"{name} {'+' if diff > 0 else '-'}{fmt(abs(diff))}{unit}", better(stat, now, then)))
    return out
