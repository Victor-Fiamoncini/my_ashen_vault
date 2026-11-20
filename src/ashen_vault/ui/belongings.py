"""What the Belongings menu shows, as data: which slot holds an item, what each slot holds, the
slot chooser's rows and the quick item slots. Pure logic, no raylib, so tests can cover it.

Players see two equip slots, Primary (the left mouse button) and Secondary (the right one), never
hands; the inventory still keys them RIGHT / LEFT so saves stay compatible."""

from ashen_vault.player.inventory import LEFT, RIGHT, SLOT_NAMES, SPELL
from ashen_vault.player.items import Items

SLOT_KEYS = {RIGHT: "1", LEFT: "2"}  # the number keys that equip into each slot, and the row marks
SLOT_BUTTONS = {RIGHT: "left", LEFT: "right"}  # the mouse button each slot answers to
# Belongings tabs, left to right, and the item kinds each one lists (spells and the scrolls that
# teach them share a tab; keys and boss sigils are the unique items).
TABS = ("Items", "Weapons", "Armor", "Spells", "Unique")
TAB_KINDS = {
    "Items": ("consumable", "repair"),
    "Weapons": ("weapon", "shield"),
    "Armor": ("armor",),
    "Spells": ("spell", "scroll"),
    "Unique": ("key",),
}
TAB_GAP = 5  # pixels between tab labels


def tab_of(item):
    """The Belongings tab that lists `item`."""
    return next(t for t in TABS if item.kind in TAB_KINDS[t])


def step_tab(tab, step):
    """The tab `step` places along from `tab`, wrapping around."""
    return TABS[(TABS.index(tab) + step) % len(TABS)]


def tab_spans(x, widths):
    """(left, right) pixel span of each tab label laid out from `x`, given their text widths."""
    spans = []
    for w in widths:
        spans.append((x, x + w))
        x += w + TAB_GAP
    return spans


def tab_at(spans, px):
    """Index of the tab label under pointer x `px` (gaps count toward the label before), or None."""
    for i, (lo, hi) in enumerate(spans):
        if lo <= px < hi + TAB_GAP:
            return i
    return None


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
    return Items.get(held).name + (" (Broken)" if inv.broken(held) else "")


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


def pick_options(inv, item, spell_name, spell_id=None):
    """The slot chooser's rows: (label, slot) for Primary and Secondary, each naming what it holds
    now, then ("Unequip", None) when the item is already equipped. A spell row counts as equipped
    only when it is the readied spell (`spell_id`) sitting in a slot."""
    opts = [(f"{SLOT_NAMES[s]}: {occupant(inv, s, spell_name)}", s) for s in (RIGHT, LEFT)]
    readied = item.kind != "spell" or item.spell == spell_id
    if readied and inv.equipped(held_id(item)):
        opts.append(("Unequip", None))
    return opts


# --- quick items -----------------------------------------------------------------
# A consumable's chooser: use it now, or put it in one of the quick slots the mouse wheel picks from.
USE = "use"  # the chooser row that uses the item
UNQUICK = "unquick"  # the chooser row that takes it out of its quick slot


def quick_mark(player, id_):
    """Row suffix " [Q2]" for an item sitting in a quick slot, else ""."""
    slot = player.quick_slot_of(id_)
    return "" if slot is None else f" [Q{slot + 1}]"


def quick_name(player, slot):
    """What quick slot `slot` holds, by name, or "(empty)"."""
    id_ = player.quick_slots[slot]
    return Items.get(id_).name if id_ else "(empty)"


def quick_options(player, item):
    """The quick-slot rows of a consumable's chooser: (label, slot index) for each slot, naming what
    it holds now, then ("Remove", UNQUICK) when the item already sits in one."""
    opts = [(f"Quick {i + 1}: {quick_name(player, i)}", i) for i in range(len(player.quick_slots))]
    if player.quick_slot_of(item.id) is not None:
        opts.append(("Remove", UNQUICK))
    return opts


def consumable_options(player, item):
    """A consumable's chooser: ("Use", USE), then its quick-slot rows."""
    return [("Use", USE), *quick_options(player, item)]


def quick_rows(player):
    """The Quick panel: (slot number, item or None, selected on the wheel) per slot."""
    return [
        (i + 1, Items.get(id_) if id_ else None, i == player.quick_index)
        for i, id_ in enumerate(player.quick_slots)
    ]
