"""Comparing gear before equipping it: ATK, DEF and load, now and then."""

from ashen_vault.player.inventory import PRIMARY, SECONDARY, Inventory
from ashen_vault.player.items import Item, Items
from ashen_vault.player.spells import Spells
from ashen_vault.ui import compare


def test_iron_gauntlets_over_leather_gloves_raise_defense_and_load():
    inv = Inventory(hands="leather_gloves")
    changes = compare.preview(inv, Items.get("iron_gauntlets"))
    now, then = changes["DEF"]
    assert then > now and compare.better("DEF", now, then) == 1
    now, then = changes["Load"]
    assert then > now and compare.better("Load", now, then) == -1
    assert inv.hands == "leather_gloves"  # the real inventory is untouched
    assert compare.deltas(changes)[0][0].startswith("DEF +")


def test_a_two_hander_changes_attack_and_drops_whats_in_secondary():
    inv = Inventory(right="rusted_sword", left="buckler")
    trial = compare.would_equip(inv, Items.get("zweihander"))
    assert trial.slots["left"] == "zweihander" and not trial.equipped("buckler")
    assert compare.preview(inv, Items.get("zweihander"))["ATK"][1] == Items.get("zweihander").power


def test_nothing_to_compare_for_what_you_already_wear_or_cannot():
    inv = Inventory()
    assert compare.preview(inv, Items.get("rusted_sword")) == {}
    assert compare.preview(inv, Items.get("red_tonic")) == {}


def test_bare_fists_hit_harder_in_gauntlets():
    assert compare.swing_power(Items.FISTS, Items.get("iron_gauntlets")) > compare.swing_power(
        Items.FISTS, None
    )
    assert compare.fmt(3.0) == "3" and compare.fmt(1.5) == "1.5"
    assert compare.better("ATK", 8, 8) == 0 and compare.better("Load", 9, 4) == 1


def test_a_shield_shows_how_much_more_it_blocks():
    inv = Inventory(left="buckler")
    inv.add("kite_shield")
    now, then = compare.preview(inv, Items.get("kite_shield"))["Block"]
    assert then > now
    assert any(
        text.startswith("Block +") and text.endswith("%")
        for text, _ in compare.deltas({"Block": (now, then)})
    )


def spell_row(id_):
    return Item(id=f"spell_{id_}", name=id_, kind="spell", spell=id_, desc="")


def test_readying_another_spell_shows_its_power():
    inv = Inventory()  # the spell (Flame Bolt) sits in Secondary
    now, then = compare.preview(inv, spell_row("thunder"), magic=3, spell="flame")["SPL"]
    assert now == Spells.power("flame", 3) and then == Spells.power("thunder", 3) and then > now
    assert compare.preview(inv, spell_row("flame"), magic=3, spell="flame") == {}  # already readied


def test_a_spell_in_primary_trades_the_sword_for_the_spell():
    inv = Inventory(left="buckler")  # no spell in a slot yet
    changes = compare.preview(inv, spell_row("flame"), hand=PRIMARY, magic=2, spell="flame")
    assert changes["SPL"] == (0, Spells.power("flame", 2))
    assert changes["ATK"][1] < changes["ATK"][0]  # the sword gives way to the spell


def test_taking_off_what_you_wear_shows_what_you_lose():
    inv = Inventory(left="buckler")
    changes = compare.preview(inv, Items.get("buckler"), unequip=True)
    assert changes["Block"][1] == 0 and changes["Load"][1] < changes["Load"][0]
    assert compare.preview(inv, Items.get("kite_shield"), unequip=True) == {}  # not worn


def test_the_slot_chooser_compares_each_slot():
    inv = Inventory(right="rusted_sword", left="buckler")
    inv.add("hatchet")
    primary = compare.preview(inv, Items.get("hatchet"), hand=PRIMARY)
    secondary = compare.preview(inv, Items.get("hatchet"), hand=SECONDARY)
    assert "Block" not in primary and secondary["Block"][1] == 0
