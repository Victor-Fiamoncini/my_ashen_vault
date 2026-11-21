"""Old Harrowmere, the sunken first city under the sewers, driven headless: the way down through its
tiers, the gate from the Pall's cistern, the shortcut lift, the sextons' bells and the Keystone."""

import math

from ashen_vault import map_path
from ashen_vault.ai.enemy import (
    PILLAR_RADIUS,
    PILLAR_REACH,
    QUAKE_RADIUS,
    QUAKE_SAFE,
    SLAB_REACH,
    TOLL_RADIUS,
)
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.util import rround
from ashen_vault.world import collision, relics, terrain
from ashen_vault.world.hazards import Eruption
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import (
    BOULDER_FLIGHT,
    BOULDER_RADIUS,
    BOULDER_SCATTER,
    BOULDER_SHARDS,
    MORTAR_TEAL,
    NOVA_RINGS,
    QUENCHED_HP,
    World,
)
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
    gallery = _gallery_door(m)
    before = _reachable(m, start, open_tiles=[gallery])
    assert (keystone.tx, keystone.tz) not in before  # its court lies behind its great door
    (shrine,) = _spec(m, "save_statue")
    assert {(shrine.tx + dx, shrine.tz + dz) for dx, dz in BESIDE} & before
    (front,) = [d for d in doors if m[d[0], d[1] - 1].walkable]  # the one the plaza's stair leads to
    court = _reachable(m, start, open_tiles=[gallery, front])
    assert (keystone.tx, keystone.tz) in court
    # Behind the false walls and the cell fronts (raised by the levers of the Oubliette, the gaolers'
    # postern and the Under-Cells) every chest but the boss's reward and the lift room's hidden one lies
    # open before the Keystone falls.
    secrets = [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    cells = [(s.tx, s.tz) for s in _spec(m, "gate")]
    explored = _reachable(m, start, open_tiles=[gallery, *secrets, *cells])
    behind_boss = {(s.tx, s.tz) for s in _spec(m, "chest") if (s.tx, s.tz) not in explored}
    (coffer,) = _spec(m, "chest", model="coffer")
    (lift_room,) = [w for w in secrets if m[w[0], w[1]].floor == m[coffer.tx, coffer.tz].floor]
    assert behind_boss == {(coffer.tx, coffer.tz), next(t for t in _beside(lift_room) if t in behind_boss)}
    everything = [gallery, *doors, *secrets, *cells]
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


def _gallery_door(m):
    """The plain door in the landing's south wall, down into the dark old gallery. Nothing locks it, so
    the walks below count it open."""
    (door,) = [s for s in _spec(m, "door") if not s.props.get("boss")]
    return (door.tx, door.tz)


def test_a_plain_door_leads_from_the_landing_down_into_the_old_gallery():
    """The landing's south wall is closed but for one doorway onto the dark gallery, and a plain door
    stands in it: no key, no bar, no boss, so it opens from either side. The lift shortcut comes up the
    gallery's shaft and through that door back onto the landing."""
    m = _map()
    start = (4, 3)
    door = _gallery_door(m)
    (spec,) = [s for s in _spec(m, "door") if (s.tx, s.tz) == door]
    assert not {"key", "from", "boss"} & spec.props.keys()
    assert spec.props.get("model") == "stone"  # the sunken city's carved slab, not a wooden door
    landing, gallery = (door[0], door[1] - 1), (door[0], door[1] + 1)
    assert m[landing].walkable and m[landing].ceil is None  # under the open cavern
    assert m[gallery].walkable and m[gallery].ceil is not None  # cut through the rock
    assert m[door].floor == m[landing].floor == m[gallery].floor
    # The landing's south wall is whole but for the door.
    assert all(not m[x, door[1]].walkable for x in range(2, 12) if x != door[0])
    assert gallery not in _reachable(m, start)
    assert gallery in _reachable(m, start, open_tiles=[door])
    (lift,) = [p for p in terrain.build_platforms(m) if p.kind == "lift"]
    foot = next(
        t
        for t in _beside((TileMap.tile_coord(lift.x), TileMap.tile_coord(lift.z)))
        if m[t].walkable and m[t].floor == lift.low
    )
    assert start not in _reachable(
        m, foot, shortcuts=True
    )  # shut, the door keeps the gallery from the landing
    assert start in _reachable(m, foot, open_tiles=[door], shortcuts=True)


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
    door = _gallery_door(m)
    plain = _reachable(m, start, open_tiles=[door])
    inside = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz)])
    assert (lever.tx, lever.tz) not in plain and (lever.tx, lever.tz) in inside
    cells = [(s.tx, s.tz) for s in _spec(m, "gate", lever="oubliette")]
    assert len(cells) == 6 and not set(cells) & inside
    freed = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz), *cells])
    held = [npc for npc in _spec(m, "npc") if npc.props["id"] in {"aubel", "coldry", "ysolde"}]
    for npc in held:
        (front,) = [c for c in cells if c in _beside((npc.tx, npc.tz))]  # each behind its own bars
        assert front in freed, npc.props["id"]
        reach = float(npc.props["reach"])
        assert any(math.hypot(x - npc.tx, z - npc.tz) * 2 <= reach for x, z in inside), npc.props["id"]
    assert {s.props["id"] for s in _spec(m, "npc")} == {
        "aubel",
        "coldry",
        "ysolde",
        "brannick",
        "sister_vell",
    }
    (hammer,) = _spec(m, "chest", item="torch_greathammer")
    (sword,) = _spec(m, "chest", item="ember_stone_sword")
    assert (hammer.tx, hammer.tz) in inside and (sword.tx, sword.tz) not in plain


def test_the_under_cells_lie_down_the_gaolers_stair_and_the_wardens_lever_opens_them():
    """Below the Oubliette: the gaoler's hall holds a second lever, which raises the bars either side of
    the gallery (the gaolers' postern) onto their stair. It winds down to the Under-Cells, a tier
    beneath: the flooded cell block, the interrogation hall, the warden's office and the deep cells,
    whose fronts the warden's lever raises. Brannick and Sister Vell are held there, each behind their
    own bars, and can be spoken to from the corridor."""
    m = _map()
    start = (4, 3)
    (wall,) = [w for w in _spec(m, "secret_wall") if m[w.tx, w.tz].ceil is not None]
    oubliette = [(s.tx, s.tz) for s in _spec(m, "gate", lever="oubliette")]
    postern = [(s.tx, s.tz) for s in _spec(m, "gate", lever="under_stair")]
    deep = [(s.tx, s.tz) for s in _spec(m, "gate", lever="undercells")]
    assert len(postern) == 2 and len(deep) >= 10
    (stair_lever,) = _spec(m, "lever", id="under_stair")
    (warden_lever,) = _spec(m, "lever", id="undercells")
    door = _gallery_door(m)
    inside = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz)])
    assert (stair_lever.tx, stair_lever.tz) in inside  # in the gaoler's hall, past no cell front
    # The postern's gates stand either side of the gallery: the hall on one side, the stair on the other.
    (cross,) = set(_beside(postern[0])) & set(_beside(postern[1]))
    assert (
        m[cross].ceil is not None and m[cross].floor == 0 and cross in _reachable(m, start, open_tiles=[door])
    )
    shut = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz), *oubliette])
    assert (warden_lever.tx, warden_lever.tz) not in shut
    down = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz), *postern])
    assert (warden_lever.tx, warden_lever.tz) in down
    assert m[warden_lever.tx, warden_lever.tz].floor <= -6  # a tier below the Oubliette
    assert all(m[x, z].ceil is not None for x, z in down - inside if m[x, z].walkable)  # all under rock
    flooded = [t for t in down if m[t].floor_tex == "water" and m[t].walkable]
    assert len(flooded) >= 20 and all(m[t].slow < 1 for t in flooded)
    assert {s.kind for s in m.entities if (s.tx, s.tz) in down} >= {"gaoler", "hollow_inmate", "stone_golem"}
    opened = _reachable(m, start, open_tiles=[door, (wall.tx, wall.tz), *postern, *deep])
    for npc_id in ("brannick", "sister_vell"):
        (npc,) = _spec(m, "npc", id=npc_id)
        (front,) = [c for c in deep if c in _beside((npc.tx, npc.tz))]
        assert front in opened and (npc.tx, npc.tz) not in down
        reach = float(npc.props["reach"])
        assert any(math.hypot(x - npc.tx, z - npc.tz) * 2 <= reach for x, z in down), npc_id
    chests = {(s.tx, s.tz) for s in _spec(m, "chest") if s.tz >= 47}
    assert len(chests) >= 6 and chests <= opened and not chests <= down
    for tile in opened:
        assert start in _reachable(m, tile, open_tiles=[door, (wall.tx, wall.tz), *postern, *deep]), tile
    # Brannick is held in the cell beside the warden's office; the way to the deep cells runs through it.
    (brannick,) = _spec(m, "npc", id="brannick")
    office = _reachable(m, (warden_lever.tx, warden_lever.tz), avoid=deep)
    assert any(t in office for t in _beside((brannick.tx, brannick.tz + 2)))
    (vell,) = _spec(m, "npc", id="sister_vell")
    corridor = (vell.tx, vell.tz - 2)
    assert m[corridor].floor_tex == "water"  # the water stands high in the deep cells


def test_stepping_down_into_the_under_cells_is_remembered():
    """The foot of the gaolers' stair marks the Under-Cells visited (`visited_undercells`), which their
    prisoners and the Oubliette's speak of."""
    m = _map()
    (mark,) = [s for s in _spec(m, "hint") if s.props.get("sets") == "visited_undercells"]
    game, world = sunken(at=(mark.tx, mark.tz - 3))
    world._update_hints()
    assert "visited_undercells" not in game.flags
    game.player.place(*TileMap.center(mark.tx, mark.tz), 0.0, world.map)
    world._update_hints()
    assert "visited_undercells" in game.flags and game.messages


def test_the_mortar_sisters_workshop_stands_east_of_the_roads():
    """The Mortar Sisters' Workshop, on its quay east of the roads of light: carving benches, a lore
    hint, golems and a sexton, and a reward chest, reached over the roads (one turn of them)."""
    m = _map()
    assert (m.width, m.depth) == (64, 60)
    (chest,) = _spec(m, "chest", item="tower_shield")
    assert chest.tx >= 48
    states = _ward_states(m, (4, 3))
    assert _least(states, set(_beside((chest.tx, chest.tz)))) == 1
    shop = [s for s in m.entities if s.tx >= 45 and 18 <= s.tz <= 33]
    kinds = {s.kind for s in shop}
    assert {"table", "grindstone", "stone_golem", "sunken_sexton", "hint", "ward_crystal"} <= kinds
    assert any("Mortar Sisters" in s.props.get("text", "") for s in shop if s.kind == "hint")
    teal = [s for s in _spec(m, "light") if s.props.get("color") == "0.45,1.25,1.0"]
    assert len(teal) >= 5


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


def test_a_sextons_toll_wakes_the_stone_round_it_and_nothing_further():
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
    assert keystone.state == "ashes"  # the toll never wakes the giant
    assert "bell" in game.sounds and any("raises its staff" in m for m in game.messages)
    ring = [p for p in world.projectiles if p.effect == "flare" and p.damage == 0]
    assert len(ring) >= 8 and all(p.rgb == MORTAR_TEAL for p in ring)  # its ring of mortar-light
    world.enemies = [sexton]
    assert not world.can_toll(sexton)  # nothing near to wake: it saves its toll


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


def _land(world, f, dt=0.05):
    """Runs the world's fire until `f` has come down."""
    for _ in range(200):
        world._update_fire(dt)
        if f.state != "warn":
            return


def test_the_keystone_lobs_its_boulder_to_where_you_stood_and_it_bursts_into_shards():
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    keystone.face(game.player.x, game.player.z)
    world.eruptions = []
    stood = (game.player.x, game.player.z)
    boulder = world.hurl(keystone)
    assert world.projectiles == [] and world.eruptions == [boulder]  # lobbed, not shot straight
    assert (boulder.x, boulder.z) == stood and boulder.style == "boulder"
    assert boulder.radius >= BOULDER_RADIUS and boulder.warn == BOULDER_FLIGHT  # its shadow glows meanwhile
    _ox, oy, oz = boulder.origin
    assert oy - boulder.floor > 6.0  # let go from up over its head
    world._update_fire(BOULDER_FLIGHT / 2)
    x, y, z = boulder.bomb()
    assert y > (oy + boulder.floor) / 2 + 1.0  # on an arc...
    assert min(oz, stood[1]) < z < max(oz, stood[1]) and abs(x - stood[0]) < 0.5  # ...on its way to you
    game.wounds.clear()
    _land(world, boulder)
    assert game.wounds and "boulder" in game.wounds[0][1]  # you never moved: it crushes you
    assert "boulder" in game.sounds
    shards = [f for f in world.eruptions if f is not boulder]
    # (none where a wall stands)
    assert 4 <= len(shards) <= BOULDER_SHARDS and all(f.style == "core" and f.origin for f in shards)
    for f in shards:  # flung out in a ring round where it landed
        assert abs(math.hypot(f.x - boulder.x, f.z - boulder.z) - BOULDER_SCATTER) < 0.01


def test_step_out_from_under_the_boulder_or_meet_it_with_your_shield():
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    world.eruptions = []
    boulder = world.hurl(keystone)
    game.player.x += BOULDER_RADIUS + 0.5  # stepped aside while it flew
    _land(world, boulder)
    assert not any("boulder" in src for _, src in game.wounds)
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    world.eruptions = []
    boulder = world.hurl(keystone)
    p = game.player
    p.inventory.add("tower_shield")
    p.inventory.equip("tower_shield")
    p.yaw = math.atan2(keystone.z - p.z, keystone.x - p.x)  # facing its thrower
    assert p.raise_guard(True)
    _land(world, boulder)
    assert not any("boulder" in src for _, src in game.wounds) and p.stamina.value < 1.0  # blocked


def test_the_keystone_hammers_its_fists_down_before_it_and_not_beside_it():
    keystone_type = EnemyTypes.get("keystone")
    for d, side, hurt in (
        (PILLAR_REACH, 0.0, True),  # right where its fists come down
        (keystone_type.radius + 0.6, 0.0, True),  # up close before it
        (PILLAR_REACH + PILLAR_RADIUS + 0.6, 0.0, False),  # backed off out of reach
        (0.0, keystone_type.radius + 1.0, False),  # round at its flank
    ):
        game, world = sunken(at=(22, 39))
        keystone = foe(world, "keystone", (22, 44))
        keystone.yaw = -math.pi / 2  # facing up the court, toward -z
        game.player.x, game.player.z = keystone.x + side, keystone.z - d
        world.eruptions = []
        world.pillar_crush(keystone)
        (burst,) = world.eruptions
        assert burst.radius == PILLAR_RADIUS and burst.style == "core"
        assert math.hypot(burst.x - keystone.x, burst.z - (keystone.z - PILLAR_REACH)) < 0.01
        for _ in range(30):
            world._update_fire(0.05)
        assert bool(game.wounds) == hurt, (d, side)


def test_the_keystones_fault_line_runs_along_the_floor_at_you_and_glows_all_at_once():
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    world.eruptions = []
    world.fault_line(keystone)
    fault = world.eruptions
    p = game.player
    assert len(fault) >= 3 and all(f.style == "core" for f in fault)
    assert all(abs(f.x - keystone.x) < 0.01 for f in fault)  # straight at you...
    assert all(f.z < keystone.z for f in fault) and min(f.z for f in fault) < p.z  # ...and on past you
    assert all(f.t == 0 for f in fault)  # the whole line glows at once...
    assert [f.warn for f in fault] == sorted(f.warn for f in fault)  # ...and bursts running out from it
    assert len({f.warn for f in fault}) == len(fault)
    game.wounds.clear()
    p.x += 2.0  # stepped sideways off the line
    for _ in range(40):
        world._update_fire(0.05)
    assert not game.wounds
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    world.eruptions = []
    world.fault_line(keystone)
    for _ in range(40):
        world._update_fire(0.05)
    assert game.wounds  # stood your ground on it


def test_the_keystone_rises_out_of_a_wide_spread_of_ash():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    world.ash.flakes.clear()
    keystone.begin_rise(keystone.type.rise_secs)
    world._rising(keystone, True, 0.0, 0.05)
    spread = keystone.radius * keystone.type.ash_spread
    burst = list(world.ash.flakes)
    assert len(burst) >= 150  # a dense burst...
    far = max(math.hypot(f.x - keystone.x, f.z - keystone.z) for f in burst)
    assert spread * 0.8 < far <= spread + 0.01  # ...over the whole wide spread
    world.ash.flakes.clear()
    keystone.state_t = keystone.rise_time * 0.3
    world._rising(keystone, False, 0.25, 0.5)
    assert len(world.ash.flakes) >= 100  # drawn in hard, from all across it
    assert all(math.hypot(f.x - keystone.x, f.z - keystone.z) <= spread + 0.01 for f in world.ash.flakes)
    sexton = foe(world, "sexton", (22, 40))
    world.ash.flakes.clear()
    sexton.begin_rise(3.0)
    world._rising(sexton, True, 0.0, 0.05)
    assert len(world.ash.flakes) < 100  # the other bosses of ash rise as they did


def test_the_keystone_rakes_a_beam_of_light_from_its_heart_in_its_second_phase():
    """Once its shell sloughs off, the Keystone rakes the mortar-light from its heart along the floor:
    a line of bursts runs out from its feet toward you and on past you, each a moment after the last."""
    t = EnemyTypes.get("keystone")
    assert "core_beam" in t.phase_moves and "core_beam" not in t.moves
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    world.eruptions = []
    world.core_beam(keystone)
    fire = world.eruptions
    assert len(fire) >= 3
    assert all(abs(e.x - keystone.x) < 0.5 for e in fire)  # straight at you down the court
    assert all(e.z < keystone.z for e in fire) and min(e.z for e in fire) < world.player.z  # and past you
    assert all(e.style == "core" for e in fire)
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


def test_the_keystone_is_slow_and_smashes_with_its_slabs_in_both_phases():
    from ashen_vault.ai.enemy import ATTACK_TIMES, MOVES

    t = EnemyTypes.get("keystone")
    assert t.tempo > 1 and t.impact > 0  # every swing heaved through, as befits its size
    assert "slab_smash" in t.moves
    assert {"core_beam", "shard_rain", "core_nova"} <= set(t.phase_moves)
    assert not {"core_beam", "shard_rain", "core_nova"} & set(t.moves)
    for move in ("slab_smash", "core_beam", "shard_rain", "core_nova"):
        assert move in MOVES and move in ATTACK_TIMES
    # The beam is the gargoyles' breath restyled: the same timing and weight.
    assert MOVES["core_beam"] == MOVES["breath"] and ATTACK_TIMES["core_beam"] == ATTACK_TIMES["breath"]


def test_the_keystone_brings_a_slab_down_in_a_great_burst_before_it():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 44))
    keystone.yaw = -math.pi / 2  # facing up the court, toward -z
    world.eruptions = []
    world.slab_smash(keystone)
    big, *coals = world.eruptions
    assert big.radius > 2 * Eruption.RADIUS and big.warn < Eruption.WARN  # wide, and with little warning
    assert all(f.style == "core" for f in world.eruptions)  # the mortar-light, not fire
    assert math.hypot(big.x - keystone.x, big.z - (keystone.z - SLAB_REACH)) < 0.01
    assert len(coals) >= 4
    assert all(2.0 < math.hypot(c.x - big.x, c.z - big.z) < 4.0 for c in coals)
    assert all(c.t < 0 for c in coals)  # they burst a moment after it


def test_the_keystone_rains_shards_of_its_shell_round_you():
    game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 45))
    world.eruptions = []
    world.shard_rain(keystone)
    first, *rest = world.eruptions
    p = game.player
    assert (first.x, first.z) == (p.x, p.z) and first.t == 0  # one where you stand, at once
    assert len(rest) >= 6
    assert all(math.hypot(f.x - p.x, f.z - p.z) < 6.0 for f in rest)
    assert all(f.origin is not None for f in world.eruptions)  # each flung down from over its head
    assert [f.t for f in world.eruptions] == sorted((f.t for f in world.eruptions), reverse=True)


def test_the_keystones_rings_of_light_run_out_with_gaps_to_stand_in():
    _game, world = sunken(at=(22, 39))
    keystone = foe(world, "keystone", (22, 43))
    world.eruptions = []
    world.core_nova(keystone)
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

    _game, world = sunken(at=(16, 32))
    close = foe(world, "stone_golem", (17, 32))
    behind = foe(world, "sunken_sexton", (15, 33))
    far = foe(world, "sunken_sexton", (22, 32))
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

    game, world = sunken(at=(16, 32))
    harpy = foe(world, "harpy", (16, 32))
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


def _swoop(world, harpy, target, dt=0.05):
    """Sends a harpy on a swoop at `target` and runs it until it ends."""
    harpy.state, harpy.state_t, harpy.attack_kind, harpy._struck = "attack", 0.0, "dive", True
    harpy.alt = 0.3
    harpy._target = target
    for _ in range(60):
        harpy.update(dt, world)
        world._ground(harpy)
        if harpy.state != "attack":
            break


def test_a_harpy_lands_after_its_first_swoop_and_fights_on_foot_within_reach():
    game, world = sunken(at=(16, 32))
    harpy = foe(world, "harpy", (20, 32))
    world._ground(harpy)
    game.player.x, game.player.z = TileMap.center(16, 32)
    assert harpy.aloft and not harpy.landed
    _swoop(world, harpy, (game.player.x + 1.5, game.player.z))
    assert harpy.landed and not harpy.aloft and "dive" not in harpy.cooldowns  # it never swoops again
    _fly(world, harpy, 1.0)
    assert world.enemy_y(harpy) == world.map.floor_at(harpy.x, harpy.z)  # down on the plaza
    game.player.x, game.player.z = harpy.x - 1.2, harpy.z
    assert world.level_with(harpy) and world.melee_targets(2.5, cone=-1) == [harpy]
    for _ in range(100):  # stalking you, it only ever rakes you within reach: no more swoops
        harpy.update(0.05, world)
        world._ground(harpy)
        assert harpy.attack_kind in (None, "melee")
        assert world.enemy_y(harpy) == world.map.floor_at(harpy.x, harpy.z)


def test_a_harpy_landing_over_the_chasm_glides_in_to_footing_and_keeps_to_it():
    game, world = sunken(at=(20, 28))
    harpy = foe(world, "harpy", (32, 27))  # by the plaza's east crystal
    world._ground(harpy)
    for _ in range(25):
        world.move_enemy(harpy, 0.1, 0.0)  # out over the chasm
    assert world.map.tile_at(harpy.x, harpy.z).chasm
    _swoop(world, harpy, (harpy.x + 0.5, harpy.z))  # its swoop ends out there
    assert harpy.landed
    game.player.x, game.player.z = TileMap.center(27, 27)
    harpy.state = "chase"
    for _ in range(200):
        harpy.update(0.05, world)
        world._ground(harpy)
        if world._afoot(harpy):
            break
    assert world._afoot(harpy)  # it glided in onto the plaza
    for _ in range(40):  # and as a walker it stops at the brink
        world.move_enemy(harpy, 0.1, 0.0)
    assert not world.map.tile_at(harpy.x, harpy.z).chasm


def test_harpies_wheel_over_the_plaza_and_the_terrace():
    m = _map()
    harpies = _spec(m, "harpy")
    assert len(harpies) >= 4
    for s in harpies:
        tile = m[s.tx, s.tz]
        assert tile.walkable and not tile.chasm  # they reckon their height from solid ground


# --- the roads of light ----------------------------------------------------------------------------

AROUND = [(dx, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1) if dx or dz]


def _ward_states(m, start, ward="a", fed=False):
    """Breadth-first over (tile, standing set, fed): from where you stand you walk the ground and the
    decks of the set that stands; beside a ward crystal, on solid ground (never on a deck), you can
    strike it and turn the roads to the next set (gold, pale, and teal once fed). The core's shield ward,
    struck the first time, feeds the teal road and wakes it at once. Returns {(tile, set, fed): strikes
    it took to get there}."""
    decks = {}
    for s in _spec(m, "ward"):
        decks.setdefault(s.props["set"], set()).add((s.tx, s.tz))
    every_deck = set().union(*decks.values())
    crystals = {(s.tx, s.tz): "shield" in s.props for s in _spec(m, "ward_crystal")}
    doors = [(s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead")]
    front = [d for d in doors if m[d[0], d[1] - 1].walkable]
    cache = {}

    def reach(tile, ward):
        key = (tile, ward)
        if key not in cache:
            cache[key] = _reachable(m, tile, open_tiles=front, avoid=every_deck - decks.get(ward, set()))
        return cache[key]

    seen = {(start, ward, fed): 0}
    layer = [(start, ward, fed)]
    strikes = 0
    while layer:
        nxt = []
        for tile, w, f in layer:
            for t in reach(tile, w):
                seen.setdefault((t, w, f), strikes)
            for t in reach(tile, w):
                if t in every_deck:
                    continue
                for dx, dz in AROUND:
                    shield = crystals.get((t[0] + dx, t[1] + dz))
                    if shield is None:
                        continue
                    if shield and not f:
                        state = (t, terrain.FED_SET, True)
                    else:
                        state = (t, terrain.next_ward(w, f), f)
                    if state not in seen:
                        seen[state] = strikes + 1
                        nxt.append(state)
        layer = nxt
        strikes += 1
    return seen


def _least(states, tiles, ward=None):
    return min(n for (t, w, _f), n in states.items() if t in tiles and (ward is None or w == ward))


def _roads():
    m = _map()
    (back,) = _spec(m, "exit", map="harrow_sewers")
    return m, (back.tx + 1, back.tz)


def test_the_roads_of_light_take_three_turns_to_cross_and_never_strand_you():
    """The Keystone's court lies across the chasm, past the masons' roads of light: the plaza's old stair
    to its door is gone. Only one road stands at a time, and the way across turns them three times at the
    least, never needing the teal road. Wherever you can get to, whichever road stands, a ward crystal is
    within reach, so a fall or a wrong turn never strands you."""
    m, start = _roads()
    door = next((s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead") if m[s.tx, s.tz - 1].walkable)
    landing = (door[0], door[1] - 1)
    decks = {(s.tx, s.tz) for s in _spec(m, "ward")}
    plain = _reachable(m, start, avoid=decks)  # no road at all
    assert landing not in plain
    states = _ward_states(m, start)
    assert _least(states, {landing}) == 3
    # The boss's path never needs the core's shield ward: unfed, the court is as near.
    assert min(n for (t, _w, f), n in states.items() if t == landing and not f) == 3
    assert {w for _t, w, _f in states} == set(terrain.WARD_SETS)  # every road can be made to stand
    crystals = {(s.tx, s.tz) for s in _spec(m, "ward_crystal")}
    solid = {tile for tile, _w, _f in states if tile not in decks}
    for tile in solid:  # from any ground you reach, whichever road stands, a crystal is in reach
        for w in terrain.WARD_SETS:
            fading = {(s.tx, s.tz) for s in _spec(m, "ward") if s.props["set"] != w}
            near = _reachable(m, tile, open_tiles=[door], avoid=fading)
            assert any((x + dx, z + dz) in crystals for x, z in near - decks for dx, dz in AROUND), (tile, w)
    # Every set carries weight over the chasm at the plaza's height, so the road meets the islands level.
    for s in _spec(m, "ward"):
        assert m[s.tx, s.tz].chasm and float(s.props["deck"]) == m[32, 29].floor


def test_the_third_road_runs_out_to_the_cores_shield_ward_and_teal_home():
    """A pale road from the second island reaches the Mortar Sisters' quay (one turn); from the quay a
    gold road runs out to the core's shield ward (two). Striking it feeds the teal road, which only then
    joins the crystals' turn, and runs home to the plaza: the shield over the core only falls while it
    stands, three turns in at the least."""
    m, start = _roads()
    states = _ward_states(m, start)
    (shield,) = [s for s in _spec(m, "ward_crystal") if "shield" in s.props]
    (core,) = _spec(m, "energy_core")
    assert (core.tx, core.tz) == (21, 28) and core.props["seal"] == terrain.FED_SET
    pool = {(core.tx + dx, core.tz + dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1)}
    assert all(m[t].liquid for t in pool)  # at the heart of the fountain's pool...
    (shaft,) = _spec(m, "sun_shaft")
    assert (shaft.tx, shaft.tz) in pool  # ...under the rift
    (quay_crystal,) = [s for s in _spec(m, "ward_crystal") if s.tx >= 45]
    quay = {(quay_crystal.tx + dx, quay_crystal.tz + dz) for dx, dz in AROUND}
    assert _least(states, quay) == 1
    island = {(shield.tx + dx, shield.tz + dz) for dx, dz in AROUND}
    assert _least(states, island) == 2
    # The teal road never stands before the shield ward has rung.
    assert all(f for _t, w, f in states if w == terrain.FED_SET)
    teal = {(s.tx, s.tz) for s in _spec(m, "ward", set=terrain.FED_SET)}
    assert teal and not teal & {t for t, w, _f in states if w != terrain.FED_SET}
    # Home on the plaza beside the fountain, with the teal road standing and the shield down.
    fountain = {(core.tx + dx, core.tz + dz) for dx in range(-2, 3) for dz in range(-2, 3)}
    fountain = {t for t in fountain if m[t].walkable and not m[t].chasm}
    assert _least(states, fountain, terrain.FED_SET) == 3
    # ...and it is the teal road that brings you home: without it the island strands you on it.
    others = {(s.tx, s.tz) for s in _spec(m, "ward") if s.props["set"] != terrain.FED_SET}
    assert not fountain & _reachable(m, (shield.tx, shield.tz + 1), avoid=others | teal)
    assert fountain & _reachable(m, (shield.tx, shield.tz + 1), avoid=others)


def test_the_crystals_turn_gold_pale_and_teal_only_once_fed():
    assert terrain.ward_turn(False) == ("a", "b")
    assert terrain.ward_turn(True) == ("a", "b", "c")
    assert [terrain.next_ward(w, False) for w in "ab"] == ["b", "a"]
    assert [terrain.next_ward(w, True) for w in "abc"] == ["b", "c", "a"]
    assert terrain.next_ward("c", False) == "a"  # an unfed turn never keeps the teal road


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
    # Unfed, the next strike goes back to gold: the teal road is not yet in the turn.
    game.player.yaw = -math.pi / 2
    assert world.strike_wards(2.0) and world.ward_set == "a" and world.ward_key not in game.flags


def test_the_shield_ward_feeds_the_teal_road_and_drops_the_cores_shield():
    game, world = sunken(at=(38, 18))
    game.player.yaw = -math.pi / 2  # facing the shield ward, north of its island
    assert world.core_shielded() and not world.ward_fed
    assert world.strike_wards(2.0)
    assert world.ward_fed and world.ward_set == "c" and not world.core_shielded()
    assert world.ward_fed_key in game.flags and f"{world.ward_key}:c" in game.flags
    assert any("teal" in m for m in game.messages)
    teal = [p for p in world.terrain.platforms if p.kind == "ward" and p.ward == "c"]
    assert teal and all(p.active for p in teal)
    # The save keeps the teal road standing, and the shield down.
    again = World(game, "old_harrowmere")
    assert again.ward_set == "c" and not again.core_shielded()
    assert all(p.afloat for p in again.terrain.platforms if p.kind == "ward" and p.ward == "c")
    # Fed, every crystal now turns gold, pale, teal: the shield rises with gold and pale.
    assert world.strike_wards(2.0) and world.ward_set == "a" and world.core_shielded()
    assert f"{world.ward_key}:c" not in game.flags and world.ward_key not in game.flags
    assert world.strike_wards(2.0) and world.ward_set == "b" and world.core_shielded()
    assert world.strike_wards(2.0) and world.ward_set == "c" and not world.core_shielded()


def test_a_fading_road_drops_you_into_the_chasm():
    game, world = sunken(at=(34, 29))  # on the gold road
    t = world.terrain
    assert t.support(game.player.x, game.player.z) is not None
    t.set_wards("b")
    for p in t.platforms:
        p.update(0.05, loaded=False)
    assert t.support(game.player.x, game.player.z) is None  # it bears no weight as soon as it fades


def test_the_lit_core_floods_the_keystone_with_light_as_its_shell_sloughs_off():
    """While the plaza's core burns the Keystone starts whole, and at half HP the core's light floods
    a share of its HP back into it."""
    game, world = sunken(at=(22, 39))
    assert not world.core_quenched()
    world._spawn_entities()
    (keystone,) = [e for e in world.enemies if e.type.id == "keystone"]
    assert keystone.hp == keystone.type.hp
    keystone.hp = keystone.type.hp // 2
    world.boss_rage(keystone)
    assert keystone.hp == keystone.type.hp // 2 + rround(keystone.type.hp * keystone.type.surge)
    assert keystone.type.rage in game.messages


def test_quenching_the_core_weakens_the_keystone_and_denies_it_its_surge():
    game, world = sunken(at=(22, 39), flags=("core_quenched:old_harrowmere",))
    assert world.core_quenched()
    world._spawn_entities()
    (keystone,) = [e for e in world.enemies if e.type.id == "keystone"]
    full = keystone.type.hp
    assert keystone.hp == rround(full * QUENCHED_HP) and keystone.trail_hp <= keystone.hp
    world.starve_bosses()  # safe to call again: it never weakens it twice
    assert keystone.hp == rround(full * QUENCHED_HP)
    keystone.hp = full // 2
    world.boss_rage(keystone)
    assert keystone.hp == full // 2  # no light left to flood back into it
    assert any("gutters" in m for m in game.messages)
    # Only a boss the core fed: the golems keep their HP.
    assert all(e.hp == e.type.hp for e in world.enemies if e.type.id == "stone_golem")


def _clear(world, body_x, body_z, radius, floor):
    tile = (TileMap.tile_coord(body_x), TileMap.tile_coord(body_z))
    return collision.circle_clear(world.map, body_x, body_z, radius, floor, world.blocker, tile)


def test_a_body_shoved_against_the_cliff_stairs_wall_never_sinks_into_the_rock():
    """On the narrow Cliff Stair, pressing a sexton against the cavern's north wall (or being pressed
    against it) gives way only as far as the rock allows: neither body ends up half inside it."""
    game, world = sunken(at=(16, 2))
    sexton = foe(world, "sunken_sexton", (16, 2))
    floor = world.map[16, 2].floor
    wall_face = 2 * TileMap.TILE  # the north edge of row 2
    sexton.z = wall_face + sexton.radius + 0.2
    player = game.player
    for _ in range(30):  # you lean in on it from the south, step after step
        player.x, player.z = sexton.x, sexton.z + 0.3
        world.move_enemy(sexton, 0.0, 0.0)
        assert _clear(world, sexton.x, sexton.z, sexton.radius, floor)
    # And the other way round: it presses you into the rock.
    player.x, player.z = sexton.x + 3.0, wall_face + 0.6
    sexton.x, sexton.z = player.x, player.z + 0.3
    for _ in range(30):
        world._push_player_out_of_bodies()
        assert _clear(world, player.x, player.z, 0.4, player.y)


def test_the_shortcut_lift_is_the_masons_rune_lift_and_wakes_on_its_first_ride():
    """The lift behind the Keystone's court is a chainless stone deck borne on glyphs (`model=rune`),
    fastened from the gallery's end until it is first ridden up from the lift room; that ride frees it
    and says so in its own words."""
    game, world = sunken(at=(7, 40))
    (lift,) = [p for p in world.terrain.platforms if p.kind == "lift"]
    assert lift.model == "rune" and lift.locked and lift.at == "low"
    assert lift.fastened_at("high") and not lift.fastened_at("low")
    game.player.x, game.player.z = lift.x, lift.z  # onto its rune plate
    game.player.y = world.player_floor()
    for _ in range(round((terrain.LIFT_DELAY + (lift.high - lift.low) / lift.speed + 1.0) / 0.05)):
        world.update_terrain(0.05)
        game.player.y = world.player_floor()
    assert lift.at == "high" and not lift.locked and not lift.fastened_at("high")
    assert "lift:old_harrowmere:7,39" in game.flags
    assert any("glyphs wake" in m for m in game.messages)
    assert not any("chain" in m for m in game.messages)
