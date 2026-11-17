"""The shrine store: what you put away at one shrine waits at every other. Pure logic, no raylib.

Items, weapons, armor and known spells can be stored (`Player.stash`, `Player.stashed_spells`); keys
and sigils can't, nor gold. A stored spell is out of your spell list, so it can't be readied or cast,
until you take it back. Stored things are still yours: shops and finds count them as owned
(`owns`, `knows`), and dying never touches them."""

from ashen_vault.player.inventory import HANDS, SPELL
from ashen_vault.player.items import Items

KEPT_KINDS = ("key",)  # never stored: keys open doors and sigils end the story


def can_store(item):
    """Whether `item` may go into the store."""
    return item.kind not in KEPT_KINDS


def deposit(player, id_, n=1):
    """Moves `n` of item `id_` from your pack into the store, taking it off if its last carried copy
    was held or worn. Returns False when you don't carry that many or it can't be stored."""
    inv = player.inventory
    item = Items.ALL.get(id_)
    if item is None or not can_store(item) or not inv.remove(id_, n):
        return False
    player.stash[id_] = player.stash.get(id_, 0) + n
    left = inv.count(id_)
    held = [s for s, v in inv.slots.items() if v == id_]
    if left == 0:
        inv.unequip(id_)
    elif left == 1 and len(held) > 1 and not item.two_handed:  # one copy can't fill both hands
        inv.slots[held[-1]] = None
    return True


def withdraw(player, id_, n=1):
    """Takes `n` of item `id_` out of the store into your pack. False when there aren't that many."""
    if player.stash.get(id_, 0) < n:
        return False
    player.stash[id_] -= n
    if player.stash[id_] == 0:
        del player.stash[id_]
    player.inventory.add(id_, n)
    return True


def deposit_spell(player, spell_id):
    """Puts a known spell away: it leaves your spell list (and your hand, if it was the only one).
    The readied spell stays readied when another is put away."""
    if spell_id not in player.spells:
        return False
    current = player.current_spell()
    player.spells.remove(spell_id)
    player.stashed_spells.append(spell_id)
    if not player.spells:
        player.spell_index = 0
        for h in HANDS:
            if player.inventory.slots[h] == SPELL:
                player.inventory.slots[h] = None
    elif current and current.id != spell_id:
        player.equip_spell(current.id)
    else:
        player.spell_index %= len(player.spells)
    return True


def withdraw_spell(player, spell_id):
    """Takes a stored spell back into your spell list."""
    if spell_id not in player.stashed_spells:
        return False
    player.stashed_spells.remove(spell_id)
    current = player.current_spell()
    player.spells.append(spell_id)
    if current:
        player.equip_spell(current.id)
    return True


def owns(player, id_):
    """Whether you carry or have stored item `id_`."""
    return player.inventory.has(id_) or player.stash.get(id_, 0) > 0


def known_spells(player):
    """Every spell you know, stored ones included."""
    return [*player.spells, *player.stashed_spells]
