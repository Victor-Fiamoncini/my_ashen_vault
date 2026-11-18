"""The Harrow Sewers' World logic driven headless: slimes that burst into gobbets, the Maw's bile,
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


def test_the_maw_spits_a_fan_of_bile_that_poisons_and_corrodes():
    game, world = sewers(at=(41, 12))
    maw = foe(world, "sump_maw", (41, 7))
    world.enemy_fire(maw, "bile")
    assert len(world.projectiles) == 4
    damage = round(maw.type.damage * MOVES["bile"][2])
    for p in world.projectiles:
        assert p.hostile and p.damage == damage and p.rgb == maw.type.shot_rgb
        assert dict(p.inflicts) == {"poison": 30, "corrosion": 35}
    headings = sorted(math.atan2(p.dz, p.dx) for p in world.projectiles)
    assert headings[-1] - headings[0] > 0.5  # a fan: sidestep between its gobbets
    assert "hiss" in game.sounds


def test_the_sewers_bosses_guard_no_relic():
    """The prophecy's fourth sigil is not down here: neither boss drops a relic, and the three-sigil
    ending is untouched."""
    for type_id, flag in (("rat_matron", "matron_dead"), ("sump_maw", "maw_dead")):
        t = EnemyTypes.get(type_id)
        assert t.boss and t.dead_flag == flag and t.drop is None and t.rise == "ash"
    assert len(relics.RELICS) == len(relics.ENDING_RELICS) == 4
    assert not {t.drop for t in map(EnemyTypes.get, ("rat_matron", "sump_maw"))} & set(relics.RELICS)
    assert EnemyTypes.get("rat_matron").brood == "sewer_rat"
    assert EnemyTypes.get("sump_maw").rage and "bile" in EnemyTypes.get("sump_maw").moves


def test_the_brood_mother_calls_her_rats_and_wakes_from_her_heap_behind_her_doors():
    game, world = sewers(at=(29, 29))
    (matron,) = [e for e in World(world.game, "harrow_sewers").enemies if e.type.id == "rat_matron"]
    world.enemies = [matron]
    assert matron.state == "ashes"
    assert {a.gate for a in world.arenas if a.flag == "matron_dead"} == {(29, 28), (33, 34)}
    assert world.rise_time(matron)  # you stand in her nest, in plain sight of her heap: she rises
    world.summon(matron, matron.type.brood, 2)
    assert [e.type.id for e in world.enemies[1:]] == ["sewer_rat", "sewer_rat"]
    assert "Mother Gnawl shrieks, and her brood answers." in game.messages  # no "The" before her name
    assert EnemyTypes.get("sump_maw").called == "The Sump Maw"
    assert EnemyTypes.get("sludge_slime").called == "The Sludge Slime"


# --- the bosses' own moves --------------------------------------------------------------------------


def test_each_sewer_boss_has_moves_no_other_foe_uses():
    own = {
        "rat_matron": {"tail_lash", "squeal", "swarm"},
        "sump_maw": {"bile", "undertow", "gulp", "shed"},
    }
    for type_id, moves in own.items():
        t = EnemyTypes.get(type_id)
        assert moves <= set(t.moves) | set(t.phase_moves), type_id
        for other in EnemyTypes.ALL.values():
            if other.id != type_id:
                assert not moves & (set(other.moves) | set(other.phase_moves)), (type_id, other.id)
    assert "swarm" in EnemyTypes.get("rat_matron").phase_moves  # her litter comes at half HP
    assert {"gulp", "shed"} <= set(EnemyTypes.get("sump_maw").phase_moves)


def gnawl(world, at=(30, 31)):
    matron = foe(world, "rat_matron", at)
    matron.state, matron.yaw = "chase", 0.0  # facing +x
    matron.cooldowns = dict.fromkeys(matron.cooldowns, 99.0)
    return matron


def test_her_tail_lashes_whoever_slips_behind_her_before_she_turns():
    _game, world = sewers(at=(29, 31))  # a tile behind her
    matron = gnawl(world)
    matron.cooldowns["tail_lash"] = 0.0
    matron.update(0.01, world)
    assert matron.state == "windup" and matron.attack_kind == "tail_lash"
    assert matron.yaw == 0.0  # she lashes without turning round to you
    for _ in range(int(MOVES["tail_lash"][0] / 0.05) + 2):
        matron.update(0.05, world)
    assert matron.yaw == 0.0
    # In front of her, she turns and bites as ever: the lash is only for her back.
    _game, world = sewers(at=(32, 31))
    matron = gnawl(world)
    matron.cooldowns["tail_lash"] = 0.0
    matron.update(0.01, world)
    assert matron.attack_kind != "tail_lash"


def test_a_tail_lash_lands_behind_her_and_misses_in_front():
    game, world = sewers(at=(29, 31))
    matron = gnawl(world)
    hp = game.player.stats.hp
    world.tail_lash(matron)
    assert game.player.stats.hp < hp and "Mother Gnawl's tail lashes you!" in game.messages
    game, world = sewers(at=(31, 31))
    matron = gnawl(world)
    hp = game.player.stats.hp
    world.tail_lash(matron)
    assert game.player.stats.hp == hp


def test_her_squeal_staggers_you_from_any_side_but_only_in_earshot():
    from ashen_vault.ai.enemy import SQUEAL_RADIUS

    game, world = sewers(at=(29, 31))  # behind her: a sound has no front
    matron = gnawl(world)
    hp = game.player.stats.hp
    world.squeal(matron)
    assert game.player.stats.hp < hp and game.player.webbed_t > 0
    assert [w.style for w in world.shockwaves] == ["squeal"] and world.shockwaves[0].radius == SQUEAL_RADIUS
    game, world = sewers(at=(25, 30))  # out of earshot
    matron = gnawl(world, at=(31, 30))
    hp = game.player.stats.hp
    world.squeal(matron)
    assert game.player.stats.hp == hp and game.player.webbed_t == 0


def test_her_litter_swarms_along_the_floor_and_rots_what_it_bites():
    from ashen_vault.world.world import SWARM_HEIGHT

    _game, world = sewers(at=(30, 34))
    matron = gnawl(world)
    world.enemy_fire(matron, "swarm")
    assert len(world.projectiles) == 5
    floor = world.enemy_y(matron)
    for p in world.projectiles:
        assert p.effect == "rat" and p.hostile and p.dy == 0
        assert p.y == floor + SWARM_HEIGHT  # low along the floor, under your chest
        assert dict(p.inflicts) == {"rot": 22}
        assert p.damage == round(matron.type.damage * MOVES["swarm"][2])


def test_the_maws_undertow_bursts_up_where_you_stand_and_drags_at_you():
    game, world = sewers(at=(41, 11))
    maw = foe(world, "sump_maw", (41, 6))
    world.undertow(maw)
    assert len(world.eruptions) == 5 and all(f.style == "drowned" for f in world.eruptions)
    first = world.eruptions[0]
    assert (first.x, first.z) == (game.player.x, game.player.z)  # right under you
    hp = game.player.stats.hp
    for _ in range(30):
        world._update_fire(0.05)
    assert game.player.stats.hp < hp and game.player.webbed_t > 0
    assert game.player.ailments.meters["rot"] > 0
    assert "The drowned drag at your legs!" in game.messages


def test_the_maws_gulp_swallows_you_and_leaves_its_dark_on_your_eyes():
    from ashen_vault.world.world import GULP_DARK, GULP_GLOOM

    game, world = sewers(at=(41, 11))
    maw = foe(world, "sump_maw", (41, 10))
    before, hp = world.dark_here(), world.player.stats.hp
    world.gulp(maw)
    assert world.player.stats.hp < hp
    assert "The Sump Maw swallows you whole, and spits you out!" in game.messages
    assert world.gloom_t == GULP_GLOOM and world.dark_here() == max(before, GULP_DARK)
    world._update_fire(GULP_GLOOM + 0.1)
    assert world.dark_here() == before


def test_the_sump_lies_eight_metres_down():
    _game, world = sewers()
    assert world.map[41, 20].floor == -8  # the Sump
    assert world.map[41, 8].floor == -8  # the Maw's cistern
    (lift,) = [p for p in world.terrain.platforms if p.kind == "lift"]
    assert lift.high - lift.low == 8


def test_the_maw_sloughs_off_gobbets_that_crawl_at_you_but_only_so_many():
    from ashen_vault.world.world import SHED_COUNT, SHED_MAX

    game, world = sewers(at=(41, 11))
    maw = foe(world, "sump_maw", (41, 6))
    world.shed(maw)
    gobbets = [e for e in world.enemies if e.type.id == "slimelet"]
    assert len(gobbets) == SHED_COUNT and all(g.state == "chase" for g in gobbets)
    assert "The Sump Maw sloughs off gobbets of itself, and they crawl at you!" in game.messages
    while world.can_shed(maw):
        world.shed(maw)
    assert sum(e.type.id == "slimelet" for e in world.enemies) == SHED_MAX
    world.shed(maw)  # no room: nothing more
    assert sum(e.type.id == "slimelet" for e in world.enemies) == SHED_MAX
    assert not world.can_shed(foe(world, "rat_matron", (41, 9)))  # she has no gobbets to shed
