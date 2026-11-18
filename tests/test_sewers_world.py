"""The Harrow Sewers' World logic driven headless: slimes that burst into gobbets, the Reeve's bile,
and the two bosses who guard no relic."""

import math

from ashen_vault.ai.enemy import MOVES
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.world import collision, relics
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_verdant_world import JungleGame, foe


def sewers(at=(24, 26), keep_foes=False):
    game = JungleGame()
    world = World(game, "harrow_sewers")
    if not keep_foes:
        world.enemies = []  # placed by each test as needed
    game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world


def test_a_slain_sludge_slime_bursts_into_gobbets_that_burst_no_further():
    game, world = sewers()
    slime = foe(world, "sludge_slime", (27, 26))
    slime.kill()
    gobbets = world.split(slime)
    assert len(gobbets) == EnemyTypes.get("sludge_slime").split_count == 2
    assert all(g in world.enemies for g in gobbets)
    for g in gobbets:
        assert g.type.id == "slimelet" and g.state == "chase"  # already after you
        assert math.hypot(g.x - slime.x, g.z - slime.z) <= slime.radius
        tx, tz = TileMap.tile_coord(g.x), TileMap.tile_coord(g.z)
        assert collision.passable(world.map, tx, tz, world.map[tx, tz].floor)
    assert "hiss" in game.sounds
    for g in gobbets:
        g.kill()
        assert world.split(g) == []
    assert len(world.enemies) == 3
    rat = foe(world, "sewer_rat", (22, 26))
    rat.kill()
    assert world.split(rat) == []


def test_a_slime_against_a_wall_drops_its_gobbets_where_it_fell():
    _game, world = sewers(at=(20, 20))
    slime = foe(world, "sludge_slime", (19, 20))  # against the cistern's west wall
    slime.x -= 0.6
    slime.yaw = math.pi  # the first gobbet would land in the wall
    for g in world.split(slime):
        tx, tz = TileMap.tile_coord(g.x), TileMap.tile_coord(g.z)
        assert not world.map[tx, tz].solid


def test_a_shrine_rest_brings_back_the_slimes_but_not_their_gobbets():
    _game, world = sewers(keep_foes=True)
    slimes = [e for e in world.enemies if e.type.id == "sludge_slime"]
    assert len(slimes) >= 4
    slimes[0].kill()
    world.split(slimes[0])
    assert any(e.type.id == "slimelet" for e in world.enemies)
    world.respawn_enemies()
    assert not any(e.type.id == "slimelet" for e in world.enemies)
    assert sum(e.type.id == "sludge_slime" for e in world.enemies) == len(slimes)


def test_the_reeve_spews_a_fan_of_bile_that_poisons_and_corrodes():
    game, world = sewers(at=(41, 12))
    reeve = foe(world, "sump_reeve", (41, 7))
    world.enemy_fire(reeve, "bile")
    assert len(world.projectiles) == 4
    damage = round(reeve.type.damage * MOVES["bile"][2])
    for p in world.projectiles:
        assert p.hostile and p.damage == damage and p.rgb == reeve.type.shot_rgb
        assert dict(p.inflicts) == {"poison": 30, "corrosion": 35}
    headings = sorted(math.atan2(p.dz, p.dx) for p in world.projectiles)
    assert headings[-1] - headings[0] > 0.5  # a fan: sidestep between its gobbets
    assert "hiss" in game.sounds


def test_the_sewers_bosses_guard_no_relic():
    """The prophecy's fourth sigil is not down here: neither boss drops a relic, and the three-sigil
    ending is untouched."""
    for type_id, flag in (("rat_matron", "matron_dead"), ("sump_reeve", "reeve_dead")):
        t = EnemyTypes.get(type_id)
        assert t.boss and t.dead_flag == flag and t.drop is None and t.rise == "ash"
    assert len(relics.RELICS) == len(relics.ENDING_RELICS) == 3
    assert EnemyTypes.get("rat_matron").brood == "sewer_rat"
    assert EnemyTypes.get("sump_reeve").rage and "bile" in EnemyTypes.get("sump_reeve").moves


def test_the_brood_mother_calls_her_rats_and_wakes_from_her_heap_without_a_door():
    game, world = sewers(at=(29, 29))
    (matron,) = [e for e in World(world.game, "harrow_sewers").enemies if e.type.id == "rat_matron"]
    world.enemies = [matron]
    assert matron.state == "ashes"
    assert not any(a.flag == "matron_dead" for a in world.arenas)  # an open nest: no great door
    assert world.rise_time(matron)  # you are in plain sight of her heap: she rises
    world.summon(matron, matron.type.brood, 2)
    assert [e.type.id for e in world.enemies[1:]] == ["sewer_rat", "sewer_rat"]
    assert "Mother Gnawl shrieks, and her brood answers." in game.messages  # no "The" before her name
    assert EnemyTypes.get("sump_reeve").called == "The Sump Reeve"
    assert EnemyTypes.get("sludge_slime").called == "The Sludge Slime"
