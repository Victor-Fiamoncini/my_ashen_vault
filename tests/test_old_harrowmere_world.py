"""Old Harrowmere, the sunken first city under the sewers, driven headless: the way down through its
tiers, the gate from the Pall's cistern, the shortcut lift, the sextons' bells and the Keystone."""

import math

from ashen_vault import map_path
from ashen_vault.ai.enemy import QUAKE_RADIUS, QUAKE_SAFE, TOLL_RADIUS
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.world import collision, relics, terrain
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_verdant_world import JungleGame, foe
from test_world import BESIDE, _reachable, _spec


def _map():
    return MapLoader.load_file(map_path("old_harrowmere"))


def sunken(at=(4, 3), flags=()):
    game = JungleGame(flags)
    world = World(game, "old_harrowmere")
    world.enemies = []  # placed by each test as needed
    game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world


def test_old_harrowmere_is_solvable_from_the_breach_down_to_the_keystone():
    """From the breach every chest and the Keystone can be reached with only the Keystone's front door
    opened; the lift behind its court is a shortcut, opened by the rear door, that rides from the
    court's floor all the way up to the landing's gallery. Nowhere you can get to strands you."""
    m = _map()
    assert m.meta["name"] == "Old Harrowmere"
    (back,) = _spec(m, "exit", map="harrow_sewers")
    start = (back.tx + 1, back.tz)
    doors = [(s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead")]
    assert len(doors) == 2
    (keystone,) = _spec(m, "keystone")
    before = _reachable(m, start)
    assert (keystone.tx, keystone.tz) not in before  # its court lies behind its great door
    (shrine,) = _spec(m, "save_statue")
    assert {(shrine.tx + dx, shrine.tz + dz) for dx, dz in BESIDE} & before
    (front,) = [d for d in doors if m[d[0], d[1] - 1].walkable]  # the one the plaza's stair leads to
    court = _reachable(m, start, open_tiles=[front])
    assert (keystone.tx, keystone.tz) in court
    for s in m.entities:
        if s.kind == "chest" and s.props.get("model") != "coffer":
            assert (s.tx, s.tz) in before, s.props
    opened = _reachable(m, start, open_tiles=doors, shortcuts=True)
    (coffer,) = _spec(m, "chest", model="coffer")
    assert (coffer.tx, coffer.tz) in opened and (coffer.tx, coffer.tz) not in court  # the boss's reward
    for tile in opened:
        assert start in _reachable(m, tile, open_tiles=doors, shortcuts=True), tile
    (lift,) = [p for p in terrain.build_platforms(m) if p.kind == "lift"]
    assert lift.locked and lift.high - lift.low >= 20  # a long ride, from the city's foot to its top
    assert m[keystone.tx, keystone.tz].floor <= min(m[x, z].floor for x, z in before)  # the deepest


def test_old_harrowmere_falls_away_in_tiers():
    """A vertical map: from the landing the way down falls by tiers into a chasm that kills, and the
    drowned city's towers rise out of it."""
    m = _map()
    floors = {
        round(m[x, z].floor)
        for z in range(m.depth)
        for x in range(m.width)
        if m[x, z].walkable and not m[x, z].needs_footing
    }
    assert max(floors) - min(floors) >= 20
    assert {0, -8, -16, -20, -22} <= floors  # the landing, the terrace, the aqueduct, the plaza, the court
    chasm = [m[x, z] for z in range(m.depth) for x in range(m.width) if m[x, z].chasm]
    assert chasm and min(t.floor for t in chasm) <= -terrain.FALL_LETHAL - 22
    assert len(_spec(m, "sunken_tower")) >= 4
    assert _spec(m, "sun_shaft") and _spec(m, "light")


def test_the_breach_in_the_cistern_opens_only_once_the_pall_has_fallen():
    sewers = MapLoader.load_file(map_path("harrow_sewers"))
    (breach,) = _spec(sewers, "exit", map="old_harrowmere")
    assert breach.props["requires"] == "pall_dead" and breach.props["model"] == "cistern_breach"
    game = JungleGame()
    world = World(game, "harrow_sewers")
    (prop,) = [p for p in world.props if p.kind == "exit" and p.props.get("map") == "old_harrowmere"]
    assert not world.exit_open(prop)
    game.flags.add("pall_dead")
    assert world.exit_open(prop)
    # It lands you at the foot of the way back up, and that way leads back out beside the breach.
    m = _map()
    tx, tz = (int(v) for v in breach.props["at"].split(",")[:2])
    (back,) = _spec(m, "exit", map="harrow_sewers")
    assert abs(tx - back.tx) + abs(tz - back.tz) == 1 and m[tx, tz].walkable
    bx, bz = (int(v) for v in back.props["at"].split(",")[:2])
    assert abs(bx - breach.tx) + abs(bz - breach.tz) == 1 and sewers[bx, bz].walkable
    pall_arena = {a.flag: a for a in world.arenas}["pall_dead"]
    assert (breach.tx, breach.tz) in pall_arena.tiles  # you reach it through the Pall's cistern


def test_the_keystones_court_is_one_arena_behind_both_its_doors():
    world = World(JungleGame(), "old_harrowmere")
    arenas = [a for a in world.arenas if a.flag == "keystone_dead"]
    assert len(arenas) == 2 and arenas[0].tiles == arenas[1].tiles
    (keystone,) = [e for e in world.enemies if e.type.id == "keystone"]
    assert (TileMap.tile_coord(keystone.x), TileMap.tile_coord(keystone.z)) in arenas[0].tiles
    t = keystone.type
    assert t.boss and t.rise == "ash" and t.brittle and t.drop is None
    assert t.drop not in relics.RELICS


def test_a_sextons_bell_wakes_the_stone_round_it_and_nothing_further():
    game, world = sunken(at=(20, 30))
    sexton = foe(world, "sunken_sexton", (16, 30))
    near = foe(world, "stone_golem", (14, 30))
    far = foe(world, "stone_golem", (16 - 1, 30 - round(TOLL_RADIUS / 2) - 2))
    idle = foe(world, "sunken_sexton", (18, 31))
    keystone = foe(world, "keystone", (22, 43))
    assert near.perched and far.perched
    assert world.can_toll(sexton)
    world.toll(sexton)
    assert near.state == "rising"  # tearing free of its plinth
    assert far.perched == (math.hypot(far.x - sexton.x, far.z - sexton.z) > TOLL_RADIUS)
    assert idle.state == "chase"
    assert keystone.state == "ashes"  # the bell never wakes the giant
    assert "bell" in game.sounds and any("rings its bell" in m for m in game.messages)
    world.enemies = [sexton]
    assert not world.can_toll(sexton)  # nothing near to wake: it saves its bell


def test_the_quake_passes_under_you_close_in_and_runs_out_to_its_reach():
    for d, hurt in (
        (EnemyTypes.get("keystone").radius + QUAKE_SAFE - 0.3, False),
        (QUAKE_RADIUS - 1.0, True),
        (QUAKE_RADIUS + 1.0, False),
    ):
        game, world = sunken(at=(22, 43))
        keystone = foe(world, "keystone", (22, 43))
        game.player.x = keystone.x + d
        world.quake(keystone)
        assert bool(game.wounds) == hurt, d
        assert world.shockwaves


def test_the_keystone_hurls_masonry():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    world.enemy_fire(keystone, "hurl")
    (shot,) = world.projectiles
    assert shot.hostile and shot.effect == "rubble"
    assert math.hypot(shot.dx, shot.dz) > 6  # faster than a plain bolt


def test_golems_stand_on_their_plinths_and_sextons_walk_their_rounds():
    m = _map()
    golems = _spec(m, "stone_golem")
    sextons = _spec(m, "sunken_sexton")
    assert len(golems) >= 6 and len(sextons) >= 3
    for s in golems + sextons:
        tile = m[s.tx, s.tz]
        assert tile.walkable and not tile.liquid and not tile.needs_footing, (s.kind, s.tx, s.tz)
        assert collision.passable(m, s.tx, s.tz, tile.floor)
    for s in sextons:  # every sexton has stone within reach of its bell
        assert any(math.hypot(g.tx - s.tx, g.tz - s.tz) * 2 <= TOLL_RADIUS for g in golems), (s.tx, s.tz)
