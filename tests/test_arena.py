"""Boss arenas: the great door, the fight that seals it, and the fog left after you fall."""

import math

import pytest

from ashen_vault.player.player import Player
from ashen_vault.world.arena import Arena, flood
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import FOG_WALK_SPEED, World
from conftest import risen
from test_prison_world import FakeGame


def world_on(name, flags=(), at=None):
    game = FakeGame(flags)
    world = World(game, name)
    if at:
        game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world


@pytest.mark.parametrize(
    ("map_name", "flag", "lair"),
    [
        ("abandoned_prison", "boss_dead", (15, 4)),
        ("abandoned_prison", "butcher_dead", (27, 4)),
        ("verdant_hollow", "spider_dead", (15, 3)),
        ("cinder_keep", "gargoyles_dead", (4, 4)),
        ("ashen_cemetery", "sexton_dead", (10, 5)),
        ("harrow_sewers", "pall_dead", (41, 8)),
        ("vesperholm", "duchess_dead", (21, 4)),
        ("old_harrowmere", "keystone_dead", (22, 43)),
        ("herran_spire", "herran_dead", (17, 6)),
    ],
)
def test_every_boss_has_a_closed_arena_behind_a_great_door(map_name, flag, lair):
    _game, world = world_on(map_name)
    (arena, *more) = [a for a in world.arenas if a.flag == flag]
    assert all(a.tiles == arena.tiles for a in more)  # a lair with two doors (the Keystone's) is one arena
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
    """The prison with the Warden's door opened, the player stepped inside, the Warden awake."""
    game, world = world_on("abandoned_prison", {"door:abandoned_prison:15,9", *flags}, at=(15, 7))
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
    # Waking at the shrine reloads the prison: fog stands where the door was.
    game2, world2 = world_on("abandoned_prison", game.flags, at=(15, 10))
    (fog,) = [a for a in world2.arenas if a.flag == "boss_dead"]
    assert fog.fogged(game2.flags)
    assert not world2.blocked_tile(15, 9)  # the boss can come through after you
    assert world2.player_blocked(15, 9)  # you only cross on purpose
    assert world2.fog_gate(fog.door) is fog and world2._interactable(fog.door)
    start = (world2.player.x, world2.player.z)
    world2.cross_fog(fog)
    assert (world2.player.x, world2.player.z) == start  # no jump: you walk through
    steps = []
    while world2.fog_walk:
        world2._update_fog_walk(0.05)
        steps.append((world2.player.x, world2.player.z))
    assert all(
        math.dist(a, b) <= 0.05 * FOG_WALK_SPEED + 1e-9
        for a, b in zip([start, *steps[:-1]], steps, strict=True)
    )
    here = (TileMap.tile_coord(world2.player.x), TileMap.tile_coord(world2.player.z))
    assert here == (15, 8) and fog.clear_of_gate(world2.player.x, world2.player.z, Player.RADIUS)
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
    game, world = world_on("cinder_keep", at=(10, 4))
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


def test_the_boss_rises_from_its_ashes_as_you_step_in_and_the_door_slams_behind_you():
    from ashen_vault.ai.enemy import ASH_RISE

    game, world, arena, warden = warden_fight()
    game.player.place(*TileMap.center(15, 10), 0.0, world.map)  # outside, at the door
    world.update(1 / 30)
    assert warden.state == "ashes" and not arena.sealed
    assert warden not in world.melee_targets(99.0, cone=-1.0)  # a heap of ash: nothing to strike
    game.player.place(*TileMap.center(15, 7), 0.0, world.map)
    world.update(1 / 30)
    assert warden.state == "rising" and warden.rise_time == ASH_RISE
    assert arena.sealed and any("rises from the ashes" in m for m in game.messages)
    assert len(world.ash) > 0  # embers flare as it forms
    for _ in range(int(ASH_RISE * 30) + 5):
        world.update(1 / 30)
    assert not warden.unseen


def test_after_you_fall_the_boss_rises_quicker_through_its_fog():
    from ashen_vault.ai.enemy import ASH_RISE_AGAIN

    _game, world, _arena, warden = warden_fight({"fog:abandoned_prison:15,9"})
    world.update(1 / 30)
    assert warden.state == "rising" and warden.rise_time == ASH_RISE_AGAIN


def test_the_butcher_rises_without_a_doubled_article():
    game, world = world_on("abandoned_prison", {"door:abandoned_prison:28,10"}, at=(28, 7))
    world.update(1 / 30)
    assert "The Butcher rises from the ashes!" in game.messages


def test_the_fight_waits_until_you_stand_clear_of_the_doorway():
    """Sealing while your body still overlaps the doorway would put a shut door under you, and the next
    step would snap you out of it to the far edge of your tile."""
    game, world, arena, warden = warden_fight()
    player = game.player
    player.place(15 * TileMap.TILE + 1.0, 9 * TileMap.TILE - 0.3, 0.0, world.map)  # in (15, 8), over the gate
    assert TileMap.tile_coord(player.z) == 8
    assert not arena.clear_of_gate(player.x, player.z, player.RADIUS)
    world.update(1 / 30)
    assert warden.state == "ashes" and not arena.sealed
    player.place(*TileMap.center(15, 8), 0.0, world.map)
    assert arena.clear_of_gate(player.x, player.z, player.RADIUS)
    world.update(1 / 30)
    assert warden.state == "rising" and arena.sealed


def test_stepping_into_the_lair_never_jumps_you_forward():
    game, world, arena, warden = warden_fight()
    player = game.player
    z = 9 * TileMap.TILE - 0.1  # walking in from the door, heading north (-z)
    player.place(15 * TileMap.TILE + 1.0, z, -math.pi / 2, world.map)
    for _ in range(30):
        before = player.z
        player.walk(world.map, 1, 0, 1 / 30, blocked=world.player_blocker)
        world.update(1 / 30)
        assert abs(player.z - before) < 0.3  # one step's worth, never a snap to the tile's edge
    assert arena.sealed and warden.state == "rising"


def test_mother_gnawls_nest_has_a_great_door_at_each_mouth_that_seal_fog_and_open_together():
    """Her nest lies on the way from the cistern to the outfall, so it has two mouths, each with a
    great door under her flag: one arena each, the same tiles behind both. They act as one, and say so
    once."""
    game, world = world_on("harrow_sewers", {"door:harrow_sewers:29,28"}, at=(29, 30))
    arenas = [a for a in world.arenas if a.flag == "matron_dead"]
    assert {a.gate for a in arenas} == {(29, 28), (33, 34)}
    assert arenas[0].tiles == arenas[1].tiles and (30, 31) in arenas[0].tiles
    assert 10 < len(arenas[0].tiles) < 200
    matron = next(e for e in world.enemies if e.type.dead_flag == "matron_dead")
    risen(matron).state = "chase"
    world._update_arenas()
    assert all(a.sealed for a in arenas)
    assert world.blocked_tile(29, 28) and world.blocked_tile(33, 34)
    assert game.messages.count("The great door slams shut behind you!") == 1
    world.mist_arenas()
    assert all(a.fog_key in game.flags for a in arenas)
    # Back from the shrine, come round by the outfall: either fog lets you in, and both close.
    game2, world2 = world_on("harrow_sewers", game.flags, at=(33, 35))
    fogs = [a for a in world2.arenas if a.flag == "matron_dead"]
    assert all(a.fogged(game2.flags) for a in fogs)
    south = next(a for a in fogs if a.gate == (33, 34))
    world2.cross_fog(south)
    while world2.fog_walk:
        world2._update_fog_walk(0.05)
    world2._update_arenas()
    assert all(a.sealed for a in fogs)
    assert game2.messages.count("The fog closes behind you.") == 1
    game2.flags.add("matron_dead")
    world2._update_arenas()
    assert not any(a.sealed for a in fogs)
    assert game2.messages.count("The way out grinds open.") == 1
