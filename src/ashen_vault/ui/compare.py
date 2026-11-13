"""What equipping an item would change, before you equip it: ATK, DEF, how much a raised shield
stops (Block, in %) and the load you carry.
Pure logic, no raylib, shared by the Belongings stats panel and the shop.

Each stat comes as (now, then); `better` says which way is an improvement (a lighter load is)."""

from ashen_vault.player import burden
from ashen_vault.player.inventory import Inventory
from ashen_vault.util import rround

STATS = ("ATK", "DEF", "Block", "Load")
LOWER_IS_BETTER = ("Load",)


def swing_power(weapon, gloves):
    """A weapon's ATK; bare fists hit harder in gauntlets."""
    if weapon.category != "fists":
        return weapon.power
    return weapon.power + 2 * ((gloves.power or 0) if gloves else 0)


def numbers(inv):
    """ATK, DEF, Block (% the held shield stops) and Load (kg) of what `inv` has equipped now."""
    shield = inv.shield_hand()
    return {
        "ATK": swing_power(inv.weapon_item(), inv.hands_item()),
        "DEF": inv.defense,
        "Block": rround(inv.hand_item(shield).guard * 100) if shield else 0,
        "Load": burden.load(inv.slots),
    }


def would_equip(inv, item, hand=None):
    """A copy of `inv` with `item` (a weapon, shield or armor, carried or not) equipped in `hand`
    (its default slot when None). None for anything that isn't worn or held, or is already equipped."""
    if item.kind not in ("weapon", "shield", "armor") or inv.equipped(item.id):
        return None
    trial = Inventory.from_h(inv.to_h())
    if not trial.has(item.id):
        trial.add(item.id)
    trial.equip(item.id, None if item.two_handed else hand)
    return trial


def preview(inv, item, hand=None):
    """{stat: (now, then)} for every stat equipping `item` would change, or {} when it changes
    nothing (or can't be equipped)."""
    trial = would_equip(inv, item, hand)
    if trial is None:
        return {}
    now, then = numbers(inv), numbers(trial)
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
