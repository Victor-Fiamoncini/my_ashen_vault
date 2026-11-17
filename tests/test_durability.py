"""Gear durability: wear, breaking, the weakened broken gear and mending it."""

from types import SimpleNamespace

import pytest

from ashen_vault.player import durability, guard
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.ui import compare


def test_every_piece_of_gear_wears_and_nothing_else_does():
    for item in Items.ALL.values():
        top = durability.max_durability(item)
        if item.kind in durability.GEAR:
            assert top and top > 0, item.id
        else:
            assert top is None, item.id
    assert durability.max_durability(Items.FISTS) is None


def test_heavier_weapons_and_steadier_shields_last_longer():
    m = durability.max_durability
    assert m(Items.get("katana")) < m(Items.get("rusted_sword")) < m(Items.get("claymore"))
    assert m(Items.get("claymore")) < m(Items.get("zweihander"))
    assert m(Items.get("buckler")) < m(Items.get("tower_shield"))
    assert m(Items.get("leather_gloves")) < m(Items.get("padded_coat"))


def test_wear_down_breaks_once_and_warns_once():
    inv = Inventory()
    top = inv.max_durability("rusted_sword")
    assert inv.durability("rusted_sword") == top and not inv.worn("rusted_sword")
    assert inv.wear_down("rusted_sword", top // 2) is None
    assert inv.wear_down("rusted_sword", top // 2 - top // 8) == "worn"
    assert inv.wear_down("rusted_sword", 1) is None, "warned only the first time"
    assert inv.wear_down("rusted_sword", top) == "broken"
    assert inv.broken("rusted_sword") and inv.durability("rusted_sword") == 0
    assert inv.wear_down("rusted_sword", 5) is None, "already broken"
    assert inv.wear_down("red_tonic", 5) is None and inv.durability("red_tonic") is None


def test_repair_mends_whole():
    inv = Inventory()
    inv.wear_down("padded_coat", 500)
    assert inv.missing("padded_coat") == inv.max_durability("padded_coat")
    assert [i.id for i in inv.damaged()] == ["padded_coat"]
    assert inv.repair("padded_coat") and not inv.broken("padded_coat")
    assert not inv.repair("padded_coat"), "nothing left to mend"
    assert inv.damaged() == []


def test_broken_armor_gives_no_defense():
    inv = Inventory(hands="iron_gauntlets")
    whole = inv.defense
    inv.wear_down("iron_gauntlets", 999)
    assert inv.defense == whole - Items.get("iron_gauntlets").power


def test_a_broken_shield_stops_and_holds_half_as_well():
    tower = Items.get("tower_shield")
    broken = durability.effective_shield(tower, True)
    assert durability.effective_shield(tower, False) is tower
    assert broken.guard == pytest.approx(tower.guard * durability.BROKEN_GUARD)
    assert guard.block(20, 1.0, broken, 1.0).taken > guard.block(20, 1.0, tower, 1.0).taken


def test_repair_cost_scales_with_the_wear_and_the_item():
    sword, plate = Items.get("bastard_sword"), Items.get("blackened_plate")
    assert durability.repair_cost(sword, 0) == 0
    assert durability.repair_cost(sword, 1) >= 1
    full = durability.repair_cost(sword, durability.max_durability(sword))
    assert full == pytest.approx(sword.price * durability.REPAIR_SHARE, abs=1)
    assert durability.repair_cost(plate, 30) > durability.repair_cost(sword, 30)
    gift = Items.get("stormbrand")  # never sold: priced by its level
    assert durability.repair_cost(gift, 10) > 0


def test_wear_survives_a_save_and_old_saves_load_whole():
    inv = Inventory()
    inv.wear_down("rusted_sword", 7)
    back = Inventory.from_h(inv.to_h())
    assert back.durability("rusted_sword") == inv.durability("rusted_sword")
    old = inv.to_h()
    del old["wear"]
    assert Inventory.from_h(old).wear == {}


def shielded():
    inv = Inventory()
    inv.add("round_shield")
    inv.equip("round_shield")
    p = Player(inventory=inv)
    p.yaw = 0.0  # facing +X
    return p


def test_blocking_wears_the_shield_by_what_it_stops():
    p = shielded()
    p.raise_guard(True)
    _, block = p.take_blow(16, 3, 0)
    lost = p.inventory.missing("round_shield")
    assert lost == durability.block_wear(block.stopped) and lost >= 1
    p.take_blow(48, 3, 0)
    assert p.inventory.missing("round_shield") > 2 * lost


def test_a_guard_break_wears_the_shield_more():
    assert durability.block_wear(8, broke=True) == durability.block_wear(8) + durability.BREAK_WEAR


def test_a_broken_shield_lets_more_through_and_says_so_once():
    p = shielded()
    p.raise_guard(True)
    whole, _ = p.take_blow(20, 3, 0)
    p.inventory.wear_down("round_shield", 999)
    p.wear_news.clear()
    p.stamina.fill()
    p.raise_guard(True)
    broken, _ = p.take_blow(20, 3, 0)
    assert broken > whole
    assert p.wear_news == [], "a shield already broken doesn't break again"


def test_landing_a_swing_wears_the_weapon_and_fists_never_wear():
    p = Player()
    p.start_swing()
    p.wear_weapon()
    assert p.inventory.missing("rusted_sword") == durability.WEAPON_WEAR
    bare = Player(inventory=Inventory(right=None, left=None))
    bare.start_swing()
    assert bare.wear_weapon() is None


def test_a_broken_weapon_cannot_loose_its_art():
    inv = Inventory(right="ashblade")
    p = Player(inventory=inv)
    p.charge_hand, p.charge_t = "right", 99.0
    p.gauge("right").value = 1.0
    p.stats.mp = 99
    assert p.art_primed("right")
    inv.wear_down("ashblade", 999)
    assert p.art_primed("right") is None


def test_breaking_queues_word_of_it():
    p = Player()
    p.wear("rusted_sword", 999)
    assert p.wear_news == [(Items.get("rusted_sword"), "broken")]


def test_foes_blows_wear_armor_but_only_when_they_land():
    from ashen_vault.world.world import World

    p = shielded()
    p.inventory.add("leather_gloves")
    p.inventory.equip("leather_gloves")
    game = SimpleNamespace(blocked=lambda b: None, hurt_player=lambda d, s: None)
    w = SimpleNamespace(player=p, game=game)
    World.strike_player(w, 10, "Bone", 3, 0)
    assert p.inventory.missing("padded_coat") == durability.ARMOR_WEAR
    assert p.inventory.missing("leather_gloves") == durability.ARMOR_WEAR
    p.raise_guard(True)
    p.inventory.wear.clear()
    World.strike_player(w, 1, "Bone", 3, 0)  # the shield stops it all: nothing lands
    assert p.inventory.missing("round_shield") >= 1
    assert p.inventory.missing("padded_coat") == 0


def test_compare_shows_broken_gear_weaker():
    inv = Inventory()
    before = compare.numbers(inv)
    inv.wear_down("rusted_sword", 999)
    inv.wear_down("padded_coat", 999)
    after = compare.numbers(inv)
    assert after["ATK"] < before["ATK"] and after["DEF"] < before["DEF"]
