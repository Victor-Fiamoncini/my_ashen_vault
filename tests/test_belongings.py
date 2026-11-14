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


def test_another_spell_offers_slots_not_unequip():
    """With Flame Bolt readied in a slot, choosing Pyre asks for a slot; only Flame Bolt can be unequipped."""
    inv = Inventory()  # the spell sits in Secondary
    assert inv.equipped(SPELL)
    pyre = spell_row("pyre", "Pyre")
    assert ("Unequip", None) not in belongings.pick_options(inv, pyre, "Flame Bolt", "flame")
    assert belongings.pick_options(inv, spell_row(), "Flame Bolt", "flame")[-1] == ("Unequip", None)


def test_only_weapons_shields_and_spells_take_a_slot():
    assert belongings.slottable(Items.get("buckler"))
    assert belongings.slottable(spell_row())
    assert not belongings.slottable(Items.get("padded_coat"))
    assert not belongings.slottable(Items.get("red_tonic"))
    assert belongings.held_id(spell_row()) == SPELL


def test_every_item_has_a_tab_and_keys_and_sigils_are_unique():
    from ashen_vault.player.items import Items
    from ashen_vault.ui.belongings import TABS, tab_of

    for item in Items.ALL.values():
        assert tab_of(item) in TABS
    assert tab_of(Items.get("red_tonic")) == "Items"
    assert tab_of(Items.get("buckler")) == "Weapons"
    assert tab_of(Items.get("ringmail")) == "Armor"
    assert tab_of(Items.get("scroll_pyre")) == "Spells"
    assert tab_of(Items.get("ember_sigil")) == "Unique"


def test_tabs_wrap_and_clicks_find_the_label_under_the_pointer():
    from ashen_vault.ui.belongings import TAB_GAP, TABS, step_tab, tab_at, tab_spans

    assert step_tab(TABS[0], -1) == TABS[-1] and step_tab(TABS[-1], 1) == TABS[0]
    spans = tab_spans(10, [20, 30])
    assert spans == [(10, 30), (30 + TAB_GAP, 60 + TAB_GAP)]
    assert tab_at(spans, 12) == 0 and tab_at(spans, 40) == 1 and tab_at(spans, 5) is None
