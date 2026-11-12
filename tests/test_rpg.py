import os

import pytest

from ashen_vault.player.combat import Gauge, Combat
from ashen_vault.player.stats import Stats
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world.tile_map import TileMap


def test_gauge_refills_and_spend_returns_fill():
    g = Gauge(2.0)
    assert g.spend() == pytest.approx(1.0)
    g.update(1.0)
    assert g.value == pytest.approx(0.5)
    g.update(5.0)
    assert g.full


def test_low_gauge_swings_are_weak():
    full = Combat.damage(base=8, strength=6, gauge=1.0, defense=0)
    half = Combat.damage(base=8, strength=6, gauge=0.5, defense=0)
    empty = Combat.damage(base=8, strength=6, gauge=0.0, defense=0)
    assert full == 11
    assert half < full / 2.0 + 1
    assert empty >= 1


def test_defense_never_drops_damage_below_one():
    assert Combat.damage(base=1, strength=0, gauge=0.1, defense=50) == 1


def test_level_up():
    s = Stats()
    gained = s.gain_exp(Stats.exp_for(1) + Stats.exp_for(2))
    assert gained == 2
    assert s.level == 3
    assert s.hp == s.max_hp
    assert s.max_hp == 52


def test_inventory_equip_and_buy():
    inv = Inventory(gold=200)
    assert inv.has("rusted_sword")
    assert inv.buy("ashblade")
    assert inv.gold == 20
    assert not inv.buy("ringmail")
    assert inv.equip("ashblade")
    assert inv.weapon_item().power == 15
    assert not inv.equip("red_tonic")


def test_unequip_falls_back_to_fists_and_no_armor():
    inv = Inventory()
    assert not inv.unequip("red_tonic")
    assert inv.unequip("rusted_sword")
    assert inv.unequip("padded_coat")
    assert inv.weapon is None
    assert inv.weapon_item() == Items.FISTS
    assert inv.defense == 0
    assert inv.has("rusted_sword"), "unequipping keeps the item"
    assert inv.equip("rusted_sword")
    assert inv.equipped("rusted_sword")

    restored = Inventory.from_h(Inventory(weapon=None, armor=None).to_h())
    assert restored.weapon is None
    assert restored.armor is None


def test_inventory_remove():
    inv = Inventory()
    inv.add("red_tonic", 2)
    assert inv.remove("red_tonic")
    assert inv.count("red_tonic") == 1
    assert inv.remove("red_tonic")
    assert not inv.has("red_tonic")
    assert not inv.remove("red_tonic")


def test_save_round_trip(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x = 3.5
    player.z = 7.25
    player.stats.gain_exp(100)
    player.inventory.add("red_tonic", 3)
    player.spells.append("mend")
    saves.save(map="harrowmere", player=player, flags={"chest:a"})

    map_name, loaded, flags = saves.load()
    assert map_name == "harrowmere"
    assert loaded.z == pytest.approx(7.25)
    assert loaded.stats.level == player.stats.level
    assert loaded.inventory.count("red_tonic") == 3
    assert loaded.spells == ["flame", "mend"]
    assert "chest:a" in flags


def test_corrupt_save_returns_none(tmp_path):
    path = tmp_path / "save.json"
    path.write_text("{nope")
    assert SaveSystem(str(path)).load() is None


def test_save_path_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ASHEN_VAULT_SAVE", str(tmp_path / "x.json"))
    assert SaveSystem().path == str(tmp_path / "x.json")


def test_sprint_is_faster_and_holds_attack_gauge(room):
    x, z = TileMap.center(1, 2)
    walker = Player()
    runner = Player()
    for p in (walker, runner):
        p.place(x, z, 0.0, room)
    walker.walk(room, 1, 0, 0.1)
    runner.walk(room, 1, 0, 0.1, sprint=True)
    assert (runner.x - x) / (walker.x - x) == pytest.approx(Player.SPRINT, abs=1e-6)
    assert runner.sprinting
    assert not walker.sprinting

    runner.attack_gauge.spend()
    runner.update_timers(0.5)
    assert runner.attack_gauge.value == pytest.approx(0.0)
    runner.walk(room, 0, 0, 0.1, sprint=True)
    assert not runner.sprinting
    runner.update_timers(0.5)
    assert runner.attack_gauge.value > 0
