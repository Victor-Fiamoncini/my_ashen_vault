"""Primary / Secondary slots as the Belongings menu and the mouse buttons see them."""

from ashen_vault.player.inventory import (
    LEFT,
    PRIMARY,
    RIGHT,
    SECONDARY,
    SLOT_ALIASES,
    SLOT_NAMES,
    SPELL,
    Inventory,
)
from ashen_vault.player.items import Item, Items
from ashen_vault.ui import belongings


def spell_row(id_="flame", name="Flame Bolt"):
    return Item(id=f"spell_{id_}", name=name, kind="spell", spell=id_, desc="")


def test_slots_are_the_hands_by_another_name():
    assert (PRIMARY, SECONDARY) == (RIGHT, LEFT)
    assert SLOT_NAMES == {RIGHT: "Primary", LEFT: "Secondary"}
    assert SLOT_ALIASES["primary"] == RIGHT and SLOT_ALIASES["secondary"] == LEFT


def test_mouse_buttons_follow_what_each_slot_holds():
    inv = Inventory()  # rusted sword in Primary, the spell in Secondary
    assert inv.button_action(PRIMARY) == "swing"
    assert inv.button_action(SECONDARY) == "cast"
    inv.add("buckler")
    inv.equip("buckler", SECONDARY)
    assert inv.button_action(SECONDARY) == "guard"
    inv.slots[SECONDARY] = None
    assert inv.button_action(SECONDARY) == "swing"  # a bare fist still punches


def test_a_two_hander_swings_only_from_primary():
    inv = Inventory()
    inv.add("claymore")
    inv.equip("claymore")
    assert inv.two_handing()
    assert inv.button_action(PRIMARY) == "swing"
    assert inv.button_action(SECONDARY) is None


def test_row_marks_name_slots_not_hands():
    inv = Inventory()
    sword, coat = Items.get("rusted_sword"), Items.get("padded_coat")
    assert belongings.slot_mark(inv, sword, "flame") == " [1]"
    assert belongings.slot_mark(inv, coat, "flame") == " [Worn]"
    assert belongings.slot_mark(inv, spell_row(), "flame") == " [2]"
    assert belongings.slot_mark(inv, spell_row("pyre", "Pyre"), "flame") == ""
    inv.add("claymore")
    inv.equip("claymore")
    assert belongings.slot_mark(inv, Items.get("claymore"), "flame") == " [1+2]"
    assert belongings.slot_mark(inv, sword, "flame") == ""


def test_equipped_panel_lists_every_slot():
    inv = Inventory()
    rows = belongings.equipped_rows(inv, "Flame Bolt")
    assert rows == [
        ("left", "Primary", "Rusted Sword"),
        ("right", "Secondary", "Flame Bolt"),
        (None, "Body", "Padded Coat"),
        (None, "Hands", "-"),
    ]
    inv.slots[PRIMARY] = None
    assert belongings.equipped_rows(inv, None)[0][2] == Items.FISTS.name
    inv.add("claymore")
    inv.equip("claymore")
    assert belongings.equipped_rows(inv, None)[1][2] == "(two-handed)"


def test_slot_chooser_shows_what_it_replaces():
    inv = Inventory()
    inv.add("buckler")
    opts = belongings.pick_options(inv, Items.get("buckler"), "Flame Bolt")
    assert opts == [("Primary: Rusted Sword", RIGHT), ("Secondary: Flame Bolt", LEFT)]
    inv.equip("buckler", LEFT)
    opts = belongings.pick_options(inv, Items.get("buckler"), "Flame Bolt")
    assert opts[-1] == ("Unequip", None)
    assert belongings.pick_options(inv, spell_row(), "Flame Bolt")[-1] != ("Unequip", None)  # spell unheld


def test_only_weapons_shields_and_spells_take_a_slot():
    assert belongings.slottable(Items.get("buckler"))
    assert belongings.slottable(spell_row())
    assert not belongings.slottable(Items.get("padded_coat"))
    assert not belongings.slottable(Items.get("red_tonic"))
    assert belongings.held_id(spell_row()) == SPELL
