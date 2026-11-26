"""Hearth Ash: the consumable that carries you home to Harrowmere, and where it refuses to."""

import math

from ashen_vault import dialogue
from ashen_vault.player.items import Items
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import HOME_MAP, World, home_spot
from test_prison_world import FakeGame, prison


def test_hearth_ash_is_a_consumable_sold_in_town():
    ash = Items.get("hearth_ash")
    assert ash.kind == "consumable"
    assert ash.effect == "homeward"
    assert ash.price > 0
    assert "hearth_ash" in dialogue.SHOPS["tamsin"]


def test_it_carries_you_home_from_the_prison():
    _, world = prison()
    assert world.homeward_refusal() is None


def test_it_refuses_in_harrowmere_itself():
    world = World(FakeGame(), HOME_MAP)
    assert world.homeward_refusal() == "You are already in Harrowmere."


def test_it_refuses_in_a_sealed_fight():
    _, world = prison()
    assert world.arenas
    world.arenas[0].sealed = True
    assert world.homeward_refusal() == "The fight holds you here."


def test_it_refuses_while_crossing_a_fog():
    _, world = prison()
    world.fog_walk = (0.0, 0.0)
    assert world.homeward_refusal() == "Not now."


def test_it_sets_you_down_beside_bell_squares_shrine_facing_it():
    world = World(FakeGame(), HOME_MAP)
    x, z, yaw = home_spot(world.map)
    assert world.map.tile_at(x, z).walkable
    (shrine,) = [s for s in world.map.entities if s.kind == "save_statue"]
    sx, sz = TileMap.center(shrine.tx, shrine.tz)
    assert math.isclose(math.hypot(sx - x, sz - z), TileMap.TILE)
    assert math.isclose(yaw, math.atan2(sz - z, sx - x))
    assert not world.blocked_tile(TileMap.tile_coord(x), TileMap.tile_coord(z))


def test_a_map_without_a_shrine_has_no_home_spot():
    world = World(FakeGame(), HOME_MAP)
    world.map.entities = [s for s in world.map.entities if s.kind != "save_statue"]
    assert home_spot(world.map) is None
