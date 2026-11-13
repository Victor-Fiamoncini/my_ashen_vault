"""Boss arenas: the great door, the fight that seals it, and the fog left after you fall."""

import pytest

from ashen_vault.world.arena import Arena, flood
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_keep_world import FakeGame


def world_on(name, flags=(), at=None):
    game = FakeGame(flags)
    world = World(game, name)
    if at:
        game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world


@pytest.mark.parametrize(
    ("map_name", "flag", "lair"),
    [
        ("sunken_keep", "boss_dead", (15, 4)),
        ("sunken_keep", "butcher_dead", (27, 4)),
        ("verdant_hollow", "spider_dead", (15, 3)),
        ("cinderhold", "gargoyles_dead", (24, 4)),
    ],
)
def test_every_boss_has_a_closed_arena_behind_a_great_door(map_name, flag, lair):
    _game, world = world_on(map_name)
    (arena,) = [a for a in world.arenas if a.flag == flag]
    assert lair in arena.tiles
    assert arena.gate not in arena.tiles
    assert 10 < len(arena.tiles) < 200  # closed: the flood never leaked out past the door
    for e in world.enemies:
        if e.type.dead_flag == flag:
            assert (TileMap.tile_coord(e.x), TileMap.tile_coord(e.z)) in arena.tiles


def test_flood_stops_at_gates_and_gives_up_when_it_leaks():
    class T:
        def __init__(self, solid):
            self.solid = solid

    grid = {(x, z): T(x in (0, 4) or z in (0, 4)) for x in range(5) for z in range(5)}
    grid[(4, 2)] = T(False)  # a doorway in the east wall
    tiles = flood(lambda x, z: grid.get((x, z)), {(2, 2)}, {(4, 2)})
    assert tiles == {(x, z) for x in range(1, 4) for z in range(1, 4)}
    assert flood(lambda x, z: T(False), {(0, 0)}, set()) is None


def warden_fight(flags=()):
    """The keep with the Warden's door opened, the player stepped inside, the Warden awake."""
    game, world = world_on("sunken_keep", {"door:sunken_keep:15,9", *flags}, at=(15, 7))
    (arena,) = [a for a in world.arenas if a.flag == "boss_dead"]
    warden = next(e for e in world.enemies if e.type.dead_flag == "boss_dead")
    return game, world, arena, warden


def test_the_door_slams_once_the_boss_wakes_with_you_inside():
    game, world, arena, warden = warden_fight()
    assert arena.door.open_t == 1.0 and not world.blocked_tile(15, 9)
    world._update_arenas()
    assert not arena.sealed  # he hasn't noticed you yet
    warden.state = "chase"
    world._update_arenas()
    assert arena.sealed and world.blocked_tile(15, 9) and world.player_blocked(15, 9)
    assert any("slams shut" in m for m in game.messages)
    assert not world._interactable(arena.door)  # no way out mid-fight


def test_the_way_out_opens_when_the_boss_falls():
    game, world, arena, warden = warden_fight()
    warden.state = "chase"
    world._update_arenas()
    game.flags.add("boss_dead")
    world._update_arenas()
    assert not arena.sealed and arena.door.open_t > 0
    for _ in range(40):
        world.update(0.05)
    assert not world.blocked_tile(15, 9)


def test_dying_in_the_fight_leaves_fog_that_only_the_boss_walks_through():
    game, world, arena, warden = warden_fight()
    warden.state = "chase"
    world._update_arenas()
    world.mist_arenas()
    assert arena.fog_key in game.flags
    # Waking at the shrine reloads the keep: fog stands where the door was.
    game2, world2 = world_on("sunken_keep", game.flags, at=(15, 10))
    (fog,) = [a for a in world2.arenas if a.flag == "boss_dead"]
    assert fog.fogged(game2.flags)
    assert not world2.blocked_tile(15, 9)  # the boss can come through after you
    assert world2.player_blocked(15, 9)  # you only cross on purpose
    assert world2.fog_gate(fog.door) is fog and world2._interactable(fog.door)
    world2.cross_fog(fog)
    here = (TileMap.tile_coord(world2.player.x), TileMap.tile_coord(world2.player.z))
    assert here == (15, 8)
    world2._update_arenas()
    assert fog.sealed and world2.blocked_tile(15, 9)  # crossing in starts the fight
    assert world2.fog_gate(fog.door) is None


def test_the_fight_waits_while_the_boss_is_still_outside_its_arena():
    a = Arena("x", (5, 0), frozenset({(1, 1), (2, 2)}), "fog:m:5,0")
    assert not a.should_seal(set(), (1, 1), [((9, 9), True)])
    assert a.should_seal(set(), (1, 1), [((2, 2), True)])
    assert not a.should_seal({"x"}, (1, 1), [((2, 2), True)])  # already beaten
    assert a.should_seal({"fog:m:5,0"}, (1, 1), [((2, 2), False)])  # through the fog: at once
    assert a.crossing("x", 4, 0) == (6, 0) and a.crossing("z", 5, 1) == (5, -1)


def test_the_gargoyles_arena_clears_only_when_both_have_fallen():
    game, world = world_on("cinderhold", at=(30, 4))
    (arena,) = [a for a in world.arenas if a.flag == "gargoyles_dead"]
    for e in world.enemies:
        if e.type.dead_flag == "gargoyles_dead":
            e.state = "chase"
    world._update_arenas()
    assert arena.sealed
    twins = [e for e in world.enemies if e.type.dead_flag == "gargoyles_dead"]
    twins[0].state = "dead"
    world._update_arenas()
    assert arena.sealed  # one still stands
    game.flags.add("gargoyles_dead")
    world._update_arenas()
    assert not arena.sealed
