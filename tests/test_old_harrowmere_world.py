"""Old Harrowmere, the sunken first city under the sewers, driven headless: the way down through its
tiers, the gate from the Pall's cistern, the shortcut lift, the sextons' bells and the Keystone."""

import math

from ashen_vault import map_path
from ashen_vault.ai.enemy import QUAKE_RADIUS, QUAKE_SAFE, TOLL_RADIUS, TORCH_REACH
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.util import rround
from ashen_vault.world import collision, relics, terrain
from ashen_vault.world.hazards import Eruption
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import NOVA_RINGS, World
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
    # Behind the false walls and the Oubliette's cell fronts (raised by its lever) every chest but the
    # boss's reward and the lift room's hidden one lies open before the Keystone falls.
    secrets = [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    cells = [(s.tx, s.tz) for s in _spec(m, "gate", lever="oubliette")]
    explored = _reachable(m, start, open_tiles=secrets + cells)
    behind_boss = {(s.tx, s.tz) for s in _spec(m, "chest") if (s.tx, s.tz) not in explored}
    (coffer,) = _spec(m, "chest", model="coffer")
    (lift_room,) = [w for w in secrets if m[w[0], w[1]].floor == m[coffer.tx, coffer.tz].floor]
    assert behind_boss == {(coffer.tx, coffer.tz), next(t for t in _beside(lift_room) if t in behind_boss)}
    everything = doors + secrets + cells
    opened = _reachable(m, start, open_tiles=everything, shortcuts=True)
    assert (coffer.tx, coffer.tz) in opened and (coffer.tx, coffer.tz) not in court  # the boss's reward
    assert behind_boss <= opened
    for tile in opened:
        assert start in _reachable(m, tile, open_tiles=everything, shortcuts=True), tile
    (lift,) = [p for p in terrain.build_platforms(m) if p.kind == "lift"]
    assert lift.locked and lift.high - lift.low >= 20  # a long ride, from the city's foot to its top
    ground = [m[x, z].floor for x, z in before if not m[x, z].chasm]  # not the roads of light over it
    assert m[keystone.tx, keystone.tz].floor <= min(ground)  # the deepest


def _beside(tile):
    return [(tile[0] + dx, tile[1] + dz) for dx, dz in BESIDE]


def test_the_oubliette_hides_behind_a_false_wall_and_its_lever_opens_the_cells():
    """The Bell-keepers' Oubliette opens off the dark gallery through a false wall; its gaoler's lever
    lies in the hall at its end, past no cell front, and raises them all. Its prisoners can be spoken
    to through the bars from the corridor before then."""
    m = _map()
    (back,) = _spec(m, "exit", map="harrow_sewers")
    start = (back.tx + 1, back.tz)
    (lever,) = _spec(m, "lever", id="oubliette")
    gallery = [w for w in _spec(m, "secret_wall") if m[w.tx, w.tz].ceil is not None]
    assert len(gallery) == 1
    (wall,) = gallery
    assert m[wall.tx - 1, wall.tz].walkable and m[wall.tx - 1, wall.tz].floor == m[wall.tx, wall.tz].floor
    plain = _reachable(m, start)
    inside = _reachable(m, start, open_tiles=[(wall.tx, wall.tz)])
    assert (lever.tx, lever.tz) not in plain and (lever.tx, lever.tz) in inside
    cells = [(s.tx, s.tz) for s in _spec(m, "gate", lever="oubliette")]
    assert len(cells) == 6 and not set(cells) & inside
    freed = _reachable(m, start, open_tiles=[(wall.tx, wall.tz), *cells])
    for npc in _spec(m, "npc"):
        (front,) = [c for c in cells if c in _beside((npc.tx, npc.tz))]  # each behind its own bars
        assert front in freed, npc.props["id"]
        reach = float(npc.props["reach"])
        assert any(math.hypot(x - npc.tx, z - npc.tz) * 2 <= reach for x, z in inside), npc.props["id"]
    assert {s.props["id"] for s in _spec(m, "npc")} == {"aubel", "coldry", "ysolde"}
    (hammer,) = _spec(m, "chest", item="torch_greathammer")
    (sword,) = _spec(m, "chest", item="ember_stone_sword")
    assert (hammer.tx, hammer.tz) in inside and (sword.tx, sword.tz) not in plain


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
    # Its model is set into the cistern's wall: the wall lies behind it (its -X), the cistern before it.
    behind = world.map[prop.tx - rround(math.cos(prop.yaw)), prop.tz - rround(math.sin(prop.yaw))]
    ahead = world.map[prop.tx + rround(math.cos(prop.yaw)), prop.tz + rround(math.sin(prop.yaw))]
    assert behind.solid and ahead.walkable
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


def test_the_keystone_rakes_fire_with_its_torch_in_its_ember_phase():
    """Once its shell bursts, the Keystone drags its torch along the floor: a line of fire runs out
    from its feet toward you and on past you, each burst a moment after the one before."""
    t = EnemyTypes.get("keystone")
    assert "breath" in t.phase_moves and "breath" not in t.moves
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    world.eruptions = []
    world.breath(keystone)
    fire = world.eruptions
    assert len(fire) >= 3
    assert all(abs(e.x - keystone.x) < 0.5 for e in fire)  # straight at you down the court
    assert all(e.z < keystone.z for e in fire) and min(e.z for e in fire) < world.player.z  # and past you
    assert all(e.style == "fire" for e in fire)
    assert [e.t for e in fire] == sorted((e.t for e in fire), reverse=True)  # each bursting after the last


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


def test_a_foe_cannot_reach_you_riding_a_lift_past_it_above_or_below():
    """A foe at a lift's landing, you on the deck going by metres over its head or down below the
    brink: its blows cannot reach you, so it does not swing; level with it, they land."""
    game, world = sunken(at=(22, 43))
    drowned = foe(world, "drowned", (22, 44))
    drowned.state = "chase"
    floor = world.enemy_y(drowned)
    for rise, reaches in ((4.0, False), (-3.0, False), (0.0, True), (0.8, True)):
        game.player.y = floor + rise
        assert world.level_with(drowned) == reaches, rise
        game.wounds.clear()
        assert (world.enemy_strike(drowned) > 0) == reaches, rise
        assert bool(game.wounds) == reaches, rise
    game.player.y = floor + 4.0
    drowned.cooldowns = {}
    drowned.update(0.05, world)
    assert drowned.state == "chase"  # it waits at the brink rather than swing at the air
    game.player.y = floor
    for _ in range(40):
        drowned.update(0.05, world)
    assert drowned.state in ("windup", "attack", "recover")


def test_the_keystone_is_slow_and_bears_its_torch_into_both_phases():
    t = EnemyTypes.get("keystone")
    assert t.tempo > 1 and t.impact > 0  # every swing heaved through, as befits its size
    assert "torch_smash" in t.moves
    assert {"cinder_rain", "ember_nova"} <= set(t.phase_moves)
    assert not {"cinder_rain", "ember_nova"} & set(t.moves)


def test_the_keystone_brings_its_torch_down_in_a_great_burst_before_it():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    keystone.yaw = -math.pi / 2  # facing up the court, toward -z
    world.eruptions = []
    world.torch_smash(keystone)
    big, *coals = world.eruptions
    assert big.radius > 2 * Eruption.RADIUS and big.warn < Eruption.WARN  # wide, and with little warning
    assert math.hypot(big.x - keystone.x, big.z - (keystone.z - TORCH_REACH)) < 0.01
    assert len(coals) >= 4
    assert all(2.0 < math.hypot(c.x - big.x, c.z - big.z) < 4.0 for c in coals)
    assert all(c.t < 0 for c in coals)  # they burst a moment after it


def test_the_keystone_rains_embers_round_you_from_its_torch():
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    world.eruptions = []
    world.cinder_rain(keystone)
    first, *rest = world.eruptions
    p = game.player
    assert (first.x, first.z) == (p.x, p.z) and first.t == 0  # one where you stand, at once
    assert len(rest) >= 6
    assert all(math.hypot(f.x - p.x, f.z - p.z) < 6.0 for f in rest)
    assert all(f.origin is not None for f in world.eruptions)  # each lobbed out of its basket
    assert [f.t for f in world.eruptions] == sorted((f.t for f in world.eruptions), reverse=True)


def test_the_keystones_rings_of_fire_run_out_with_gaps_to_stand_in():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 43))
    world.eruptions = []
    world.ember_nova(keystone)
    fire = world.eruptions
    assert fire
    rings = {}
    for f in fire:
        assert world.map.tile_at(f.x, f.z).walkable  # nothing on a wall or over the chasm
        d = round(math.hypot(f.x - keystone.x, f.z - keystone.z), 1)
        rings.setdefault(d, []).append(f)
    assert sorted(rings) == [r for r, _ in NOVA_RINGS if r in rings] and len(rings) >= 2
    delays = [-ring[0].t for _, ring in sorted(rings.items())]
    assert delays == sorted(delays) and len(set(delays)) == len(delays)  # out from it, one after another
    for radius in rings:  # a gap wider than you between neighbouring bursts
        count = dict(NOVA_RINGS)[radius]
        assert 2 * math.pi * radius / count - 2 * Eruption.RADIUS > 0.6


def test_a_rift_lance_runs_through_every_foe_in_its_path():
    from ashen_vault.player.spells import Spells

    game, world = sunken(at=(14, 28))
    game.player.yaw = 0.0  # down the plaza, toward +x
    near = foe(world, "sunken_sexton", (16, 28))
    far = foe(world, "sunken_sexton", (19, 28))
    aside = foe(world, "sunken_sexton", (17, 31))
    world.rift_lance(20)
    (lance,) = world.projectiles
    assert lance.pierce and lance.effect == "rift" and lance.width == Spells.RIFT_WIDTH
    for _ in range(40):
        world._update_projectiles(0.05)
    assert near.hp < near.type.hp and far.hp < far.type.hp  # through the first and on into the second
    assert aside.hp == aside.type.hp


def test_bellward_staggers_every_foe_about_you_and_spares_those_further():
    from ashen_vault.player.spells import Spells

    _game, world = sunken(at=(20, 28))
    close = foe(world, "stone_golem", (21, 28))
    behind = foe(world, "sunken_sexton", (19, 29))
    far = foe(world, "sunken_sexton", (26, 28))
    for e in (close, behind, far):
        e.state = "chase"
    struck = world.bell_toll(2, Spells.BELL_RADIUS)
    assert set(map(id, struck)) == {id(close), id(behind)}
    assert close.state == "hurt" and behind.state == "hurt" and far.state == "chase"
    assert sum(p.effect == "flare" and p.damage == 0 for p in world.projectiles) >= 8  # the toll's ring


def _fly(world, e, seconds, dt=0.05):
    for _ in range(round(seconds / dt)):
        e.update(dt, world)
        world._ground(e)


def test_a_harpy_wings_out_over_the_chasm_at_its_cruising_height():
    _game, world = sunken(at=(20, 28))
    harpy = foe(world, "harpy", (31, 27))  # on the plaza's east edge
    world._ground(harpy)
    floor = world.map[31, 27].floor
    assert world.enemy_y(harpy) == floor + harpy.type.fly
    for _ in range(40):  # out east, over the chasm
        world.move_enemy(harpy, 0.1, 0.0)
    tile = world.map.tile_at(harpy.x, harpy.z)
    assert tile.chasm and world.enemy_y(harpy) == floor + harpy.type.fly  # held up off the plaza's floor
    # A walker would have stopped at the brink.
    walker = foe(world, "sunken_sexton", (31, 27))
    x0 = walker.x
    for _ in range(40):
        world.move_enemy(walker, 0.1, 0.0)
    assert not world.map.tile_at(walker.x, walker.z).chasm and walker.x > x0  # up to the brink, no further


def test_a_harpy_cannot_fly_into_a_cliff_higher_than_it_flies():
    _game, world = sunken(at=(20, 28))
    harpy = foe(world, "harpy", (16, 24))  # at the plaza's foot of the Grand Stair
    world._ground(harpy)
    for _ in range(200):  # straight north, toward the colonnade 4 m above it and higher
        world.move_enemy(harpy, 0.0, -0.1)
    assert world.map.tile_at(harpy.x, harpy.z).floor <= world.enemy_y(harpy) + 0.5


def test_a_harpy_is_out_of_a_blades_reach_on_the_wing_and_stoops_to_strike():
    from ashen_vault.ai.enemy import MOVES

    game, world = sunken(at=(20, 28))
    harpy = foe(world, "harpy", (20, 28))
    world._ground(harpy)
    game.player.x, game.player.z = harpy.x - 1.0, harpy.z
    assert not world.melee_targets(2.5, cone=-1)  # over your head
    assert not world.level_with(harpy)
    # It drops into its swoop over the windup...
    harpy.state, harpy.state_t, harpy.attack_kind = "windup", 0.0, "dive"
    harpy._target = (game.player.x, game.player.z)
    for _ in range(round(MOVES["dive"][0] * harpy.type.tempo / 0.05) + 6):
        harpy.fly(0.05)
        world._ground(harpy)
    assert world.level_with(harpy) and world.melee_targets(2.5, cone=-1) == [harpy]
    # ...and climbs back to its cruising height after.
    harpy.state, harpy.attack_kind = "recover", None
    for _ in range(80):
        harpy.fly(0.05)
        world._ground(harpy)
    assert harpy.alt == harpy.type.fly


def test_a_slain_harpy_falls_into_the_chasm_or_onto_the_floor_below_it():
    _game, world = sunken(at=(20, 28))
    over_plaza = foe(world, "harpy", (24, 28))
    over_chasm = foe(world, "harpy", (32, 27))
    world._ground(over_plaza)
    world._ground(over_chasm)
    for _ in range(25):
        world.move_enemy(over_chasm, 0.1, 0.0)  # out over the chasm
    assert world.map.tile_at(over_chasm.x, over_chasm.z).chasm
    for e in (over_plaza, over_chasm):
        e.kill()
        _fly(world, e, 4.0)
    assert world.enemy_y(over_plaza) == world.map[24, 28].floor  # down on the plaza
    assert world.enemy_y(over_chasm) == world.map.floor_at(over_chasm.x, over_chasm.z)  # lost below


def test_harpies_wheel_over_the_plaza_and_the_terrace():
    m = _map()
    harpies = _spec(m, "harpy")
    assert len(harpies) >= 4
    for s in harpies:
        tile = m[s.tx, s.tz]
        assert tile.walkable and not tile.chasm  # they reckon their height from solid ground


# --- the roads of light ----------------------------------------------------------------------------

AROUND = [(dx, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1) if dx or dz]


def _ward_states(m, start, ward="a"):
    """Breadth-first over (tile, standing set): from where you stand you walk the ground and the decks
    of the set that stands; beside a ward crystal, on solid ground (never on a deck), you can swap the
    sets. Returns {(tile, set): swaps it took to get there}."""
    decks = {}
    for s in _spec(m, "ward"):
        decks.setdefault(s.props["set"], set()).add((s.tx, s.tz))
    every_deck = set().union(*decks.values())
    crystals = {(s.tx, s.tz) for s in _spec(m, "ward_crystal")}
    other = {"a": "b", "b": "a"}
    doors = [(s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead")]
    front = [d for d in doors if m[d[0], d[1] - 1].walkable]
    cache = {}

    def reach(tile, ward):
        key = (tile, ward)
        if key not in cache:
            cache[key] = _reachable(m, tile, open_tiles=front, avoid=decks[other[ward]])
        return cache[key]

    seen = {(start, ward): 0}
    layer = [(start, ward)]
    swaps = 0
    while layer:
        nxt = []
        for tile, w in layer:
            for t in reach(tile, w):
                if (t, w) not in seen:
                    seen[(t, w)] = swaps
            for t in reach(tile, w):
                if t in every_deck or not any((t[0] + dx, t[1] + dz) in crystals for dx, dz in AROUND):
                    continue
                if (t, other[w]) not in seen:
                    seen[(t, other[w])] = swaps + 1
                    nxt.append((t, other[w]))
        layer = nxt
        swaps += 1
    return seen


def test_the_roads_of_light_take_three_swaps_to_cross_and_never_strand_you():
    """The Keystone's court lies across the chasm, past the masons' two roads of light: the plaza's
    old stair to its door is gone. Only one road stands at a time, and the way across swaps them three
    times at the least. Wherever you can get to, with either road standing, a ward crystal is within
    reach, so a fall or a wrong swap never strands you."""
    m = _map()
    (back,) = _spec(m, "exit", map="harrow_sewers")
    start = (back.tx + 1, back.tz)
    door = next((s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead") if m[s.tx, s.tz - 1].walkable)
    landing = (door[0], door[1] - 1)
    decks = {(s.tx, s.tz) for s in _spec(m, "ward")}
    plain = _reachable(m, start, avoid=decks)  # no road at all
    assert landing not in plain
    states = _ward_states(m, start)
    assert (landing, "a") in states or (landing, "b") in states
    least = min(n for (tile, _w), n in states.items() if tile == landing)
    assert least >= 3, least
    crystals = {(s.tx, s.tz) for s in _spec(m, "ward_crystal")}
    solid = {tile for tile, _w in states if tile not in decks}
    for tile in solid:  # from any ground you reach, either road standing, a crystal is in reach
        for w in ("a", "b"):
            fading = {(s.tx, s.tz) for s in _spec(m, "ward") if s.props["set"] != w}
            near = _reachable(m, tile, open_tiles=[door], avoid=fading)
            assert any((x + dx, z + dz) in crystals for x, z in near - decks for dx, dz in AROUND), (tile, w)
    # Both sets carry weight over the chasm at the plaza's height, so the road meets the islands level.
    for s in _spec(m, "ward"):
        assert m[s.tx, s.tz].chasm and float(s.props["deck"]) == m[32, 29].floor


def test_striking_a_ward_crystal_swaps_the_roads_and_the_save_remembers():
    game, world = sunken(at=(36, 29))
    game.player.yaw = -math.pi / 2  # facing the crystal north of the first island
    wards = [p for p in world.terrain.platforms if p.kind == "ward"]
    gold = [p for p in wards if p.ward == "a"]
    pale = [p for p in wards if p.ward == "b"]
    assert all(p.afloat for p in gold) and not any(p.afloat for p in pale)
    assert world.strike_wards(2.0)
    assert world.ward_key in game.flags and world.ward_set == "b"
    assert "bell" in game.sounds
    for _ in range(round(terrain.WARD_FADE / 0.05) + 2):
        for p in wards:
            p.update(0.05, loaded=False)
    assert all(p.afloat for p in pale) and not any(p.afloat for p in gold)
    # Back on the map later, the pale road still stands.
    again = World(game, "old_harrowmere")
    standing = [p for p in again.terrain.platforms if p.kind == "ward" and p.afloat]
    assert standing and all(p.ward == "b" for p in standing)
    # A swing that reaches no crystal swaps nothing.
    game.player.yaw = math.pi / 2
    assert not world.strike_wards(2.0) and world.ward_set == "b"


def test_a_fading_road_drops_you_into_the_chasm():
    game, world = sunken(at=(34, 29))  # on the gold road
    t = world.terrain
    assert t.support(game.player.x, game.player.z) is not None
    t.set_wards("b")
    for p in t.platforms:
        p.update(0.05, loaded=False)
    assert t.support(game.player.x, game.player.z) is None  # it bears no weight as soon as it fades
