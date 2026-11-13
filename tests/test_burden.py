"""Equipment load: heavier gear slows you and makes ST dearer."""

import math

from ashen_vault.player import burden
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.player.stats import Stats


def test_every_equippable_item_has_a_mass():
    for item in Items.ALL.values():
        if item.kind in ("weapon", "shield", "armor"):
            assert item.mass > 0, item.id


def test_a_two_hander_counts_once_and_the_spell_weighs_nothing():
    inv = Inventory(right="zweihander", left=None, body=None)
    assert burden.load(inv.slots) == Items.get("zweihander").mass
    assert burden.load(Inventory(right=None, left="spell", body=None).slots) == 0


def test_tiers_climb_with_load_and_strength_pushes_them_back():
    assert burden.tier(0, 32).name == "Light"
    assert burden.tier(16, 32).name == "Medium"
    assert burden.tier(30, 32).name == "Heavy"
    assert burden.tier(40, 32).name == "Overloaded"
    assert burden.capacity(10) > burden.capacity(6)
    heavy = Inventory(right="war_hammer", left=None, body="blackened_plate", hands="iron_gauntlets")
    assert burden.of(heavy, Stats(strength=2)).name == "Overloaded"
    assert burden.of(heavy, Stats(strength=20)).name == "Medium"


def _stride(inventory):
    """Metres walked east across the test room in 0.3 s."""
    from conftest import make_room

    room = make_room()
    p = Player(inventory=inventory)
    p.place(3.0, 4.6, 0.0, room)
    p.walk(room, 1, 0, 0.3)
    return p.x - 3.0


def test_heavy_gear_walks_slower_and_pays_more_per_swing():
    light = Player(inventory=Inventory(right="rusted_sword", left=None, body=None))
    heavy = Player(inventory=Inventory(right="rusted_sword", left="tower_shield", body="blackened_plate"))
    assert _stride(light.inventory) > _stride(heavy.inventory) > 0
    a = light.start_swing()
    b = heavy.start_swing()
    assert b.stamina > a.stamina
    assert math.isclose(1.0 - heavy.stamina.value, b.stamina)
