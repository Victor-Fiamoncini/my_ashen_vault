"""The shrine store: putting things away and taking them back, and what it still counts as yours."""

import json

from ashen_vault.player import stash
from ashen_vault.player.inventory import LEFT, RIGHT, SPELL, Inventory
from ashen_vault.player.player import Player
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world import loot


def test_deposit_and_withdraw_move_counts():
    p = Player()
    p.inventory.add("red_tonic", 3)
    assert stash.deposit(p, "red_tonic", 2)
    assert p.inventory.count("red_tonic") == 1 and p.stash == {"red_tonic": 2}
    assert not stash.deposit(p, "red_tonic", 5), "not that many carried"
    assert stash.withdraw(p, "red_tonic")
    assert p.inventory.count("red_tonic") == 2 and p.stash == {"red_tonic": 1}
    assert stash.withdraw(p, "red_tonic") and p.stash == {}
    assert not stash.withdraw(p, "red_tonic")


def test_storing_what_you_wear_takes_it_off():
    p = Player()
    assert p.inventory.right == "rusted_sword" and p.inventory.body == "padded_coat"
    stash.deposit(p, "rusted_sword")
    stash.deposit(p, "padded_coat")
    assert p.inventory.right is None and p.inventory.body is None
    stash.withdraw(p, "rusted_sword")
    assert p.inventory.has("rusted_sword") and p.inventory.right is None


def test_storing_one_of_a_pair_frees_one_hand():
    p = Player(inventory=Inventory(right="hatchet", left=None))
    p.inventory.add("hatchet")
    p.inventory.equip("hatchet", LEFT)
    assert p.inventory.right == p.inventory.left == "hatchet"
    stash.deposit(p, "hatchet")
    assert [p.inventory.right, p.inventory.left].count("hatchet") == 1


def test_keys_and_sigils_stay_with_you():
    p = Player()
    p.inventory.add("cell_key")
    p.inventory.add("ember_sigil")
    assert not stash.deposit(p, "cell_key") and not stash.deposit(p, "ember_sigil")
    assert p.inventory.has("cell_key") and p.stash == {}


def test_storing_a_spell_forgets_it_until_taken_back():
    p = Player(spells=["flame", "lumen", "pyre"])
    p.equip_spell("pyre")
    assert stash.deposit_spell(p, "flame")
    assert p.spells == ["lumen", "pyre"] and p.current_spell().id == "pyre", "the readied one stays"
    assert stash.deposit_spell(p, "pyre")
    assert p.current_spell().id == "lumen"
    assert not stash.deposit_spell(p, "pyre"), "already stored"
    assert stash.withdraw_spell(p, "flame")
    assert p.current_spell().id == "lumen" and "flame" in p.spells
    assert p.stashed_spells == ["pyre"]


def test_storing_the_last_spell_empties_its_slot():
    p = Player(spells=["flame"])
    assert p.inventory.left == SPELL
    stash.deposit_spell(p, "flame")
    assert p.spells == [] and p.current_spell() is None and p.inventory.left is None
    assert p.inventory.slots[RIGHT] == "rusted_sword"


def test_stored_things_still_count_as_yours():
    p = Player(spells=["flame", "veil"])
    stash.deposit(p, "rusted_sword")
    stash.deposit_spell(p, "veil")
    assert stash.owns(p, "rusted_sword") and "veil" in stash.known_spells(p)
    kept, gold = loot.claim(p.inventory, stash.known_spells(p), "rusted_sword", p.stash)
    assert kept is None
    kept, gold = loot.claim(p.inventory, stash.known_spells(p), "scroll_veil", p.stash)
    assert kept is None and gold == loot.SPARE_SCROLL_GOLD


def test_the_store_survives_a_save(tmp_path):
    saves = SaveSystem(tmp_path / "save.json")
    p = Player(spells=["flame", "veil"])
    p.inventory.add("blue_moss", 2)
    stash.deposit(p, "blue_moss", 2)
    stash.deposit_spell(p, "veil")
    p.inventory.wear_down("rusted_sword", 9)
    saves.save(map="harrowmere", player=p, flags=set())
    _, back, _ = saves.load()
    assert back.stash == {"blue_moss": 2} and back.stashed_spells == ["veil"]
    assert back.spells == ["flame"]
    assert back.inventory.missing("rusted_sword") == 9


def test_saves_from_before_the_store_load_empty(tmp_path):
    path = tmp_path / "save.json"
    saves = SaveSystem(path)
    saves.save(map="harrowmere", player=Player(), flags=set())
    data = json.loads(path.read_text())
    del data["player"]["stash"], data["player"]["stashed_spells"], data["player"]["inventory"]["wear"]
    path.write_text(json.dumps(data))
    _, back, _ = saves.load()
    assert back.stash == {} and back.stashed_spells == [] and back.inventory.wear == {}
