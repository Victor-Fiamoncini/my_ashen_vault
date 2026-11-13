"""What the Belongings menu shows, as data: which slot holds an item, what each slot holds, and the
slot chooser's rows. Pure logic, no raylib, so tests can cover it.

Players see two equip slots, Primary (the left mouse button) and Secondary (the right one), never
hands; the inventory still keys them RIGHT / LEFT so saves stay compatible."""

from ashen_vault.player.inventory import LEFT, RIGHT, SLOT_NAMES, SPELL
from ashen_vault.player.items import Items

SLOT_KEYS = {RIGHT: "1", LEFT: "2"}  # the number keys that equip into each slot, and the row marks
SLOT_BUTTONS = {RIGHT: "left", LEFT: "right"}  # the mouse button each slot answers to


def held_id(item):
    """The id a slot stores for `item`: a spell row is stored as the readied spell (`SPELL`)."""
    return SPELL if item.kind == "spell" else item.id


def slottable(item):
    """True for what goes in Primary / Secondary: weapons, shields and spells."""
    return item.kind in ("weapon", "shield", "spell")


def slot_mark(inv, item, spell_id):
    """Row suffix: " [1]", " [2]" or " [1+2]" for the slots holding the item, " [Worn]" for worn
    armor. `spell_id` is the readied spell; only its row is marked."""
    if item.kind == "armor":
        return " [Worn]" if inv.equipped(item.id) else ""
    if item.kind == "spell" and item.spell != spell_id:
        return ""
    id_ = held_id(item)
    nums = "+".join(SLOT_KEYS[h] for h in (RIGHT, LEFT) if inv.slots[h] == id_)
    return f" [{nums}]" if nums else ""


def occupant(inv, slot, spell_name):
    """The name of what `slot` holds: an item, the readied spell's name, Fists or nothing."""
    held = inv.slots[slot]
    if held == SPELL:
        return spell_name or "Spell"
    if held is None:
        return Items.FISTS.name if slot in (RIGHT, LEFT) else "-"
    return Items.get(held).name


def equipped_rows(inv, spell_name):
    """The Equipped panel: (mouse button or None, slot name, what it holds) per slot."""
    rows = []
    for slot in (RIGHT, LEFT):
        name = occupant(inv, slot, spell_name)
        if slot == LEFT and inv.two_handing():
            name = "(two-handed)"
        rows.append((SLOT_BUTTONS[slot], SLOT_NAMES[slot], name))
    rows.append((None, "Body", occupant(inv, "body", spell_name)))
    rows.append((None, "Hands", occupant(inv, "hands", spell_name)))
    return rows


def pick_options(inv, item, spell_name):
    """The slot chooser's rows: (label, slot) for Primary and Secondary, each naming what it holds
    now, then ("Unequip", None) when the item is already equipped."""
    opts = [(f"{SLOT_NAMES[s]}: {occupant(inv, s, spell_name)}", s) for s in (RIGHT, LEFT)]
    if inv.equipped(held_id(item)):
        opts.append(("Unequip", None))
    return opts
