"""The gold you drop when you die: left in a heap of your ashes where you last stood on solid ground,
gathered up again on your next life, and lost for good if you die again before you reach it."""

import math

from ashen_vault.player import remnant
from ashen_vault.player.player import Player
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_verdant_world import JungleGame


class AshenGame(JungleGame):
    def gather_remnant(self):
        if remnant.gather(self.player):
            self.message("gathered")
        self.world.lay_remnant()


def test_dying_leaves_all_your_gold_in_a_heap():
    p = Player()
    p.inventory.gold = 120
    assert remnant.leave(p, "harrowmere", 10.0, 12.0) == (0, 120)
    assert p.inventory.gold == 0
    assert p.remnant == {"map": "harrowmere", "x": 10.0, "z": 12.0, "gold": 120}
    assert remnant.lies_on(p, "harrowmere") == (10.0, 12.0)
    assert remnant.lies_on(p, "sunken_keep") is None


def test_gathering_the_heap_gives_the_gold_back():
    p = Player()
    p.inventory.gold = 75
    remnant.leave(p, "harrowmere", 1.0, 1.0)
    p.inventory.gold = 5  # found a little on the way back
    assert remnant.gather(p) == 75
    assert p.inventory.gold == 80 and p.remnant is None
    assert remnant.gather(p) == 0


def test_dying_again_before_you_gather_it_loses_it_for_good():
    p = Player()
    p.inventory.gold = 200
    remnant.leave(p, "harrowmere", 1.0, 1.0)
    p.inventory.gold = 30
    assert remnant.leave(p, "sunken_keep", 4.0, 6.0) == (200, 30)
    assert p.remnant["gold"] == 30 and p.remnant["map"] == "sunken_keep"


def test_dying_penniless_leaves_no_heap_but_still_scatters_the_old_one():
    p = Player()
    p.inventory.gold = 50
    remnant.leave(p, "harrowmere", 1.0, 1.0)
    assert remnant.leave(p, "harrowmere", 3.0, 3.0) == (50, 0)
    assert p.remnant is None


def test_the_heap_survives_a_save(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    p = Player()
    p.inventory.gold = 42
    remnant.leave(p, "harrowmere", 7.5, 9.0)
    saves.save("harrowmere", p, set())
    _map, loaded, _flags = saves.load()
    assert loaded.remnant == {"map": "harrowmere", "x": 7.5, "z": 9.0, "gold": 42}


def test_walking_over_your_heap_in_the_world_gathers_it():
    game = AshenGame(())
    world = World(game, "harrowmere")
    game.world = world
    x, z, yaw = world.start_position()
    game.player.place(x, z, yaw, world.map)
    world.update(1 / 60)
    spot = world.death_spot()
    assert spot == (game.player.x, game.player.z)  # solid ground: right where you fell
    game.player.inventory.gold = 90
    hx, hz = x + 4 * math.cos(yaw), z + 4 * math.sin(yaw)
    remnant.leave(game.player, "harrowmere", hx, hz)
    world.lay_remnant()
    heap = next(p for p in world.props if p.kind == "remnant")
    assert (heap.x, heap.z) == (hx, hz) and world._interactable(heap)
    world.update(1 / 60)  # too far yet
    assert game.player.inventory.gold == 0
    game.player.place(hx, hz, yaw, world.map)
    world.update(1 / 60)
    assert game.player.inventory.gold == 90 and game.player.remnant is None
    assert not any(p.kind == "remnant" for p in world.props)


def test_a_heap_on_another_map_is_not_laid_here():
    game = AshenGame(())
    game.player.remnant = {"map": "sunken_keep", "x": 1.0, "z": 1.0, "gold": 10}
    world = World(game, "harrowmere")
    assert not any(p.kind == "remnant" for p in world.props)
    game.player.remnant["map"] = "harrowmere"
    world = World(game, "harrowmere")
    assert any(p.kind == "remnant" for p in world.props)


def test_the_heap_lies_on_solid_ground_when_you_die_in_a_chasm():
    game = AshenGame(())
    world = World(game, "verdant_hollow")
    game.world = world
    world.terrain.safe = TileMap.center(3, 3)
    world.terrain.plunge = 0.5
    assert world.death_spot() == TileMap.center(3, 3)
