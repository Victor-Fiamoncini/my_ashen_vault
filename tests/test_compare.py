"""Comparing gear before equipping it: ATK, DEF and load, now and then."""

from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
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
