import glob
import math
import numbers
import os

import pytest

from ashen_vault import MAP_DIR
from ashen_vault.world import collision, terrain
from ashen_vault.world.hazards import CrumbleFloor
from ashen_vault.world.map_loader import MapError, MapLoader
from ashen_vault.world.tile_map import Tile, TileMap
from ashen_vault.world.world import LANDMARKS
from conftest import ROOM


def test_parses_grid_and_meta(room):
    assert room.width == 6
    assert room.depth == 5
    assert room.meta["name"] == "Test Room"
    assert room.meta["start"] == [1.0, 1.0, 0.0]
    assert room[0, 0].solid
    assert room[3, 1].floor == pytest.approx(0.5)
    assert room[1, 3].liquid


def test_out_of_bounds_is_solid(room):
    assert room[-1, 2].solid
    assert room[99, 2].solid


def test_entity_markers_become_specs_on_default_floor(room):
    spec = room.entities[0]
    assert spec.kind == "bone_walker"
    assert (spec.tx, spec.tz) == (2, 2)
    assert spec.props["yaw"] == "90"
    assert room[2, 2].walkable


def test_unknown_tile_raises():
    bad = ROOM.replace("#..,^#", "#..?^#", 1)
    with pytest.raises(MapError):
        MapLoader(bad).parse()


def test_shipped_maps_load():
    paths = glob.glob(os.path.join(MAP_DIR, "*.map"))
    assert paths
    for path in paths:
        m = MapLoader.load_file(path)
        sx, sz = m.meta["start"][:2]
        assert m[int(sx), int(sz)].walkable, f"{path}: start tile must be walkable"
        torch = m.meta.get("torch", [0, 0, 0, 0])
        assert len(torch) == 4, f"{path}: torch is radius r g b"
        assert all(isinstance(v, numbers.Number) for v in torch), f"{path}: torch values must be numbers"


def test_walls_stop_movement(room):
    x, z = TileMap.center(1, 1)
    nx, _ = collision.move(room, x, z, -5.0, 0, radius=0.4)
    assert nx == pytest.approx(2.0 + 0.4, abs=0.01)


def test_small_step_is_climbable_but_tall_step_is_not(room):
    x, z = TileMap.center(2, 1)
    nx, _ = collision.move(room, x, z, 2.0, 0, radius=0.4)
    assert TileMap.tile_coord(nx) == 3, "should step up 0.5m"

    x, z = TileMap.center(3, 1)
    nx, _ = collision.move(room, x, z, 2.0, 0, radius=0.4)
    assert TileMap.tile_coord(nx + 0.4 - 0.01) == 3, "1.0m step blocks"


def test_water_blocks(room):
    x, z = TileMap.center(1, 2)
    _, nz = collision.move(room, x, z, 0, 2.0, radius=0.4)
    assert TileMap.tile_coord(nz) == 2


def test_dynamic_blocker(room):
    x, z = TileMap.center(1, 2)
    nx, _ = collision.move(room, x, z, 2.0, 0, radius=0.4, blocked=lambda tx, tz: tx == 2 and tz == 2)
    assert TileMap.tile_coord(nx) == 1


def test_line_of_sight(room):
    ax, az = TileMap.center(1, 1)
    bx, bz = TileMap.center(3, 2)
    assert collision.line_of_sight(room, ax, az, bx, bz)
    cx, cz = TileMap.center(1, 1)
    assert not collision.line_of_sight(room, cx, cz, cx, cz - 6)


def test_separate_pushes_apart():
    x, z = collision.separate(0.0, 0.0, 0.5, 0.5, 0.0, 0.5)
    assert x == pytest.approx(-0.5)
    assert z == pytest.approx(0.0)


STATIC_BLOCKERS = (
    *("barrel", "crate", "urn", "iron_maiden", "save_statue", "well", "npc"),
    *("altar", "table", "rack", "rubble", "cocoon", "frog_idol"),
    *("pillar", "sarcophagus", "headsman_block", "bonfire", "giant_mushroom", "totem"),
    *("anvil", "chimney"),
)


def _keep_reach(m, lifts):
    """Flood fill over the keep from its start (doors and gates count as open). Each lift in
    `lifts` links the landings at its two ends; a lift chained fast is just a hole in the floor."""
    solid = {(e.tx, e.tz) for e in m.entities if e.kind in STATIC_BLOCKERS}
    links = {}
    for p in lifts:
        sx, sz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        sides = [(sx + dx, sz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        ends = [
            [t for t in sides if not m[t].solid and abs(m[t].floor - h) <= collision.STEP_HEIGHT]
            for h in (p.low, p.high)
        ]
        assert all(ends), f"lift at {sx},{sz} needs a landing at each end"
        for a in ends[0]:
            links.setdefault(a, []).extend(ends[1])
        for b in ends[1]:
            links.setdefault(b, []).extend(ends[0])
    sx, sz = (int(v) for v in m.meta["start"][:2])
    seen = {(sx, sz)}
    todo = [(sx, sz)]
    while todo:
        tx, tz = todo.pop()
        steps = [(tx + 1, tz), (tx - 1, tz), (tx, tz + 1), (tx, tz - 1)]
        for nx, nz in steps + links.get((tx, tz), []):
            if (nx, nz) in seen or (nx, nz) in solid:
                continue
            ridden = (nx, nz) in links.get((tx, tz), [])
            if not ridden and (not collision.passable(m, nx, nz, m[tx, tz].floor) or m[nx, nz].pit):
                continue
            seen.add((nx, nz))
            todo.append((nx, nz))
    return seen


def _keep():
    m = MapLoader.load_file(os.path.join(MAP_DIR, "sunken_keep.map"))
    for e in m.entities:  # crumbling floors start solid
        if e.kind == "crumble":
            m.set_override(
                (e.tx, e.tz), CrumbleFloor(e.tx, e.tz, float(e.props["floor"]), m[e.tx, e.tz]).solid_tile()
            )
    return m


def test_sunken_keep_decor_never_cuts_off_anything():
    """Flood fill from the start (doors and gates count as open, lifts chained fast count as
    shut): every chest, door, lever, exit and the iron maiden must stay reachable, so no barrel
    plugs a corridor and no shortcut is ever needed."""
    m = _keep()
    lifts = [p for p in terrain.build_platforms(m) if p.kind == "lift"]
    seen = _keep_reach(m, [p for p in lifts if not p.locked])

    def touched(tx, tz):
        return any((tx + dx, tz + dz) in seen for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))

    kinds = ("chest", "door", "gate", "lever", "exit", "iron_maiden", "mimic", "barrel", "altar")
    targets = [e for e in m.entities if e.kind in kinds]
    assert {"iron_maiden", "mimic"} <= {e.kind for e in targets}
    for e in targets:
        assert touched(e.tx, e.tz), f"{e.kind} at {e.tx},{e.tz} is unreachable"
    # Both ends of every chained lift can be reached, so freeing it really is a shortcut.
    for p in lifts:
        sx, sz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        near = {(sx + dx, sz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))} & seen
        assert {round(m[t].floor, 1) for t in near} >= {p.low, p.high}, (sx, sz)


def test_sunken_keep_lifts_reach_the_undercroft_and_the_gallery():
    m = _keep()
    lifts = {p.lever: p for p in terrain.build_platforms(m) if p.kind == "lift"}
    assert set(lifts) == {None, "crypt_winch", "belfry_winch"}
    levers = {e.props["id"] for e in m.entities if e.kind == "lever"}
    assert {"crypt_winch", "belfry_winch"} <= levers  # every chained lift has its winch
    free = [p for p in terrain.build_platforms(m) if p.kind == "lift" and not p.locked]
    seen = _keep_reach(m, free)
    assert any(m[t].floor == -6.0 for t in seen)  # the Undercroft
    assert any(m[t].floor == 7.6 for t in seen)  # the Gallery
    no_lifts = _keep_reach(m, [])
    assert not any(m[t].floor in (-6.0, 7.6) for t in no_lifts)


def test_wall_yaw_faces_out_of_the_nearest_wall(room):
    assert room.wall_yaw(1, 2) == pytest.approx(0.0)  # wall to the west: face east
    assert room.wall_yaw(4, 2) == pytest.approx(math.pi)  # wall to the east
    assert room.wall_yaw(2, 1) == pytest.approx(math.pi / 2)  # wall to the north
    assert room.wall_yaw(2, 3) == pytest.approx(-math.pi / 2)  # wall to the south
    assert room.wall_yaw(2, 2) is None  # the middle of the room touches no wall


def test_open_facing_turns_away_from_walls(room):
    # (1,1) is the room's NW corner: east runs 3 tiles to the raised step, south 2.
    assert room.open_facing(1, 1) == pytest.approx(0.0)
    m = MapLoader(ROOM.replace("#..,^#", "#.####", 1)).parse()
    assert m.open_facing(1, 1) == pytest.approx(math.pi / 2)  # only south is open


def test_open_facing_ignores_pits():
    text = ROOM.replace("^ = floor h=1.5 ceil=3", "^ = floor h=-3 ceil=3 pit").replace("#..,^#", "#.^^^#", 1)
    m = MapLoader(text).parse()
    assert m[2, 1].pit
    assert m.open_facing(1, 1) == pytest.approx(math.pi / 2)


def test_overrides_swap_and_restore_tiles(room):
    original = room[2, 1]
    stand_in = Tile(walkable=True, floor=2.5)
    room.set_override((2, 1), stand_in)
    assert room[2, 1] is stand_in
    assert room.floor_at(*TileMap.center(2, 1)) == pytest.approx(2.5)
    room.set_override((2, 1), None)
    assert room[2, 1] is original


def _spec(m, kind, **props):
    return [s for s in m.entities if s.kind == kind and all(s.props.get(k) == v for k, v in props.items())]


def test_harrowmere_has_the_jungle_cave():
    """The jungle is reached by a trail out of the square's east side, ending at a cave mouth."""
    m = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    (exit_,) = _spec(m, "exit", map="verdant_hollow")
    assert exit_.props["model"] == "cave_mouth"
    assert m[exit_.tx, exit_.tz].walkable
    assert m[exit_.tx + 1, exit_.tz].solid  # rock behind the mouth
    assert m[exit_.tx - 1, exit_.tz].walkable  # the trail in front of it
    sx, sz = (int(v) for v in m.meta["start"][:2])
    assert (exit_.tx - 1, exit_.tz) in _reachable(m, (sx, sz))
    assert not _spec(m, "exit", model="vine_door")  # the overgrown house is shut


def test_harrowmere_jungle_trail_is_a_narrow_path_darkening_under_the_canopy():
    """From the gap in the town wall to the cave mouth the trail is a corridor: never more than two
    tiles across, hedged in, and roofed by a canopy that grows darker toward the cave."""
    m = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    (exit_,) = _spec(m, "exit", map="verdant_hollow")
    trail = {
        (tx, tz)
        for tz in range(m.depth)
        for tx in range(32, exit_.tx)
        if m[tx, tz].walkable and m[tx, tz].floor_tex == "jungle_floor"
    }
    assert (exit_.tx - 1, exit_.tz) in _reachable(m, (31, exit_.tz))
    for tx, tz in trail:  # no open clearing: no 3x3 block of trail anywhere
        assert not all((tx + dx, tz + dz) in trail for dx in range(3) for dz in range(3)), (tx, tz)
    roofed = [m[t] for t in trail if not m[t].open_sky]
    assert roofed and len(roofed) > len(trail) / 2  # mostly under the canopy...
    assert len(roofed) < len(trail)  # ...with the sky still showing at the start
    near = max(m[t].dark for t in trail if abs(t[0] - exit_.tx) + abs(t[1] - exit_.tz) <= 4)
    far = min(m[t].dark for t in trail if t[0] <= 33)
    assert near > far  # darker toward the cave


def test_verdant_hollow_loads_with_start_exit_boss_and_enemies():
    m = MapLoader.load_file(os.path.join(MAP_DIR, "verdant_hollow.map"))
    assert m.meta["name"] == "The Verdant Hollow"
    assert (m.width, m.depth) == (54, 50)
    sx, sz = (int(v) for v in m.meta["start"][:2])
    assert m[sx, sz].walkable
    (back,) = _spec(m, "exit", map="harrowmere")
    assert (back.tx, back.tz) == (sx + 1, sz)  # you arrive just inside the cave mouth
    tx, tz, _ = (int(v) for v in back.props["at"].split(","))
    town = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    assert town[tx, tz].walkable
    (cave,) = _spec(town, "exit", map="verdant_hollow")
    assert (tx, tz) == (cave.tx - 1, cave.tz)  # lands in front of the cave
    assert [int(v) for v in cave.props["at"].split(",")[:2]] == [sx, sz]
    kinds = [s.kind for s in m.entities]
    assert kinds.count("loom_mother") == 1
    assert "snare_bloom" in kinds and "bark_husk" in kinds
    assert "save_statue" in kinds
    # The boss door needs a key that a chest on the map provides.
    keys = {s.props["key"] for s in m.entities if s.kind == "door" and s.props.get("key")}
    chest_items = {s.props.get("item") for s in m.entities if s.kind == "chest"}
    assert keys and keys <= chest_items


def _reachable(m, start, open_tiles=(), shortcuts=False, avoid=()):
    """Tiles a walker can reach from `start`, honoring step heights; doors count as closed unless listed.
    Fixed platforms (planks, ledges, floorboards) count as footing at their deck height. Platforms
    chained to a lever (lifts, drawbridges) only count with `shortcuts`: a lift then links the
    landings at its two ends."""
    # Doors, gates and hidden walls block until opened; decor and breakables always count as
    # solid, so a crate or a cocoon can never be what cuts a path off.
    blocked = {
        (s.tx, s.tz) for s in m.entities if s.kind in ("door", "gate", "secret_wall", *STATIC_BLOCKERS)
    }
    blocked -= set(open_tiles)
    blocked |= set(avoid)
    platforms = [p for p in terrain.build_platforms(m) if p.kind != "raft" and (shortcuts or not p.lever)]
    decks = {
        (TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)): p.deck for p in platforms if p.kind != "lift"
    }
    links = {}
    for p in platforms:
        if p.kind != "lift":
            continue
        sx, sz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        sides = [(sx + dx, sz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        ends = [
            [t for t in sides if m[t].walkable and abs(m[t].floor - h) <= collision.STEP_HEIGHT]
            for h in (p.low, p.high)
        ]
        for a in ends[0]:
            links.setdefault(a, []).extend(ends[1])
        for b in ends[1]:
            links.setdefault(b, []).extend(ends[0])

    def floating(tx, tz):
        return (tx, tz) in decks

    seen = {start}
    todo = [start]
    while todo:
        x, z = todo.pop()
        steps = [(x + dx, z + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        for n in steps + links.get((x, z), []):
            if n in seen or n in blocked:
                continue
            ridden = n in links.get((x, z), [])
            if ridden or collision.passable(m, *n, decks.get((x, z), m[x, z].floor), floating=floating):
                seen.add(n)
                todo.append(n)
    return seen


def _verdant():
    return MapLoader.load_file(os.path.join(MAP_DIR, "verdant_hollow.map"))


def test_verdant_hollow_is_solvable():
    """The honest way through: every chest, lever and the boss can be reached with only the key
    and hidden walls opened. Barred doors, chained lifts and drawbridges are shortcuts: never needed,
    but each one joins two places you can already reach."""
    m = _verdant()
    start = tuple(int(v) for v in m.meta["start"][:2])
    reach = _reachable(m, start)
    at = {s.kind + ":" + (s.props.get("item") or s.props.get("id") or ""): (s.tx, s.tz) for s in m.entities}
    assert at["chest:briar_key"] in reach
    for s in _spec(m, "lever"):
        assert (s.tx, s.tz) in reach, s.props
    (boss,) = _spec(m, "loom_mother")
    assert (boss.tx, boss.tz) not in reach  # behind the locked door
    doors = [(s.tx, s.tz) for s in m.entities if s.kind in ("door", "gate", "secret_wall")]
    barred = [(s.tx, s.tz) for s in _spec(m, "door") if s.props.get("from")]
    honest = [d for d in doors if d not in barred]
    opened = _reachable(m, start, open_tiles=honest)
    assert (boss.tx, boss.tz) in opened
    # The caches behind the vine curtain and the web only open up once you get through them.
    for gold in ("150", "120"):
        (cache,) = [s for s in m.entities if s.kind == "chest" and s.props.get("gold") == gold]
        assert (cache.tx, cache.tz) not in reach and (cache.tx, cache.tz) in opened
    for s in m.entities:
        if s.kind == "chest":
            assert (s.tx, s.tz) in opened, s.props
    # Each shortcut joins two places the honest route already reaches.
    for tx, tz in barred:
        assert {(tx, tz - 1), (tx, tz + 1)} <= opened or {(tx - 1, tz), (tx + 1, tz)} <= opened
    for p in terrain.build_platforms(m):
        if not p.lever:
            continue
        sx, sz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        near = {(sx + dx, sz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        sides = {round(m[t].floor, 1) for t in near & opened}
        want = {p.low, p.high} if p.kind == "lift" else {round(p.deck, 1)}
        assert sides >= want, (p.kind, sx, sz)
        assert len(near & opened) >= 2, (p.kind, sx, sz)
    # Every tile you can drop into, you can climb back out of.
    full = _reachable(m, start, open_tiles=doors, shortcuts=True)
    for tile in full:
        assert start in _reachable(m, tile, open_tiles=doors, shortcuts=True), tile


def _steps(m, start, goal, open_tiles):
    """Fewest tile steps from `start` to `goal`, walking as `_reachable` does (no shortcuts)."""
    blocked = {
        (s.tx, s.tz) for s in m.entities if s.kind in ("door", "gate", "secret_wall", *STATIC_BLOCKERS)
    }
    blocked -= set(open_tiles)
    decks = {
        (TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)): p.deck
        for p in terrain.build_platforms(m)
        if p.kind != "raft" and not p.lever
    }
    dist = {start: 0}
    frontier = [start]
    while frontier:
        nxt = []
        for x, z in frontier:
            for n in ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1)):
                if n in dist or n in blocked:
                    continue
                if collision.passable(
                    m, *n, decks.get((x, z), m[x, z].floor), floating=lambda tx, tz: (tx, tz) in decks
                ):
                    dist[n] = dist[(x, z)] + 1
                    nxt.append(n)
        frontier = nxt
    return dist.get(goal)


def test_verdant_hollow_shortcuts_cut_the_way_to_the_boss():
    """The boss door is a long way round from the first shrine at first; the antechamber's barred
    door then opens straight back onto it."""
    m = _verdant()
    shrine = max(_spec(m, "save_statue"), key=lambda s: s.tz)  # the first shrine, by the clearing
    (boss_door,) = _spec(m, "door", key="briar_key")
    (barred,) = [s for s in _spec(m, "door") if s.props.get("from")]
    secrets = [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    front = (boss_door.tx, boss_door.tz + 1)
    here = (shrine.tx, shrine.tz - 1)
    long_way = _steps(m, here, front, secrets)
    short_way = _steps(m, here, front, [*secrets, (barred.tx, barred.tz)])
    assert long_way > 80 and short_way < 25, (long_way, short_way)


def test_verdant_hollow_has_dark_caves_with_cold_fires_and_new_spells():
    m = _verdant()
    sx, sz = (int(v) for v in m.meta["start"][:2])
    assert m[sx - 3, sz].dark >= 0.8  # Mossmouth
    cold = [s for s in m.entities if s.kind in ("brazier", "bonfire") and "unlit" in s.props]
    assert cold and all(m[s.tx, s.tz].dark > 0 for s in cold)
    scrolls = {s.props.get("item") for s in _spec(m, "chest")}
    assert {"scroll_pyre", "scroll_venom", "scroll_veil"} <= scrolls
    assert all(s.props.get("model") == "wood" for s in _spec(m, "lever"))


AUTO = """[meta]
name = Auto
start = 1 1 0
default = .
{auto}

[legend]
# = wall
. = floor h=0
_ = floor h=-4
o = floor h=-6 pit

[grid]
#######
#..#__#
#.b#b_#
#####c#
#__ooo#
#######

[entities]
b = barrel
c = crate
"""


def test_entities_take_their_neighbours_floor_when_asked():
    m = MapLoader(AUTO.replace("{auto}", "entity_floor = auto"), name="auto").parse()
    assert m[2, 2].floor == 0.0  # among the room's floor
    assert m[4, 2].floor == -4.0  # boxed in by walls and a crate, but beside the low floor
    assert m[5, 3].floor == -4.0  # safe floor wins over the pit below it
    plain = MapLoader(AUTO.replace("{auto}", ""), name="plain").parse()
    assert plain[4, 2].floor == 0.0 and plain[5, 3].floor == 0.0  # the old rule: the default


def test_an_entity_walled_in_on_every_side_keeps_the_default():
    text = AUTO.replace("{auto}", "entity_floor = auto")
    text = text.replace("#..#__#\n#.b#b_#\n#####c#", "#..####\n#.b#b##\n#####b#")
    m = MapLoader(text, name="walled").parse()
    assert m[4, 2].floor == 0.0
    assert m[5, 3].floor == -6.0  # only a pit beside it: a hazard is better than nothing


def test_auto_floor_looks_past_the_edge_of_the_grid():
    text = AUTO.replace("{auto}", "entity_floor = auto").replace("#######\n#..#__#", "##b####\n#..#__#", 1)
    m = MapLoader(text, name="edge").parse()
    assert m[2, 0].floor == 0.0  # nothing above it, the room below it


# --- the Cinderhold ---------------------------------------------------------------------------------


def _cinder():
    return MapLoader.load_file(os.path.join(MAP_DIR, "cinderhold.map"))


def _lava(m):
    """Lava tiles: you can step in, but only to be seared and hauled back out, so a walker avoids them."""
    return {(tx, tz) for tx, tz, tile in m.each_tile() if tile.lava}


def test_harrowmere_has_the_north_road():
    """The Cinderhold is reached by a gate in the town's north wall; each side lands you at the other."""
    town = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    (gate,) = _spec(town, "exit", map="cinderhold")
    assert gate.props["model"] == "road_gate"
    assert town[gate.tx, gate.tz - 1].solid  # the town wall behind it
    sx, sz = (int(v) for v in town.meta["start"][:2])
    assert (gate.tx, gate.tz + 1) in _reachable(town, (sx, sz))
    m = _cinder()
    (back,) = _spec(m, "exit", map="harrowmere")
    tx, tz, _ = (int(v) for v in back.props["at"].split(","))
    assert (tx, tz) == (gate.tx, gate.tz + 1)  # you come back through the gate, onto the track
    start = tuple(int(v) for v in m.meta["start"][:2])
    assert tuple(int(v) for v in gate.props["at"].split(",")[:2]) == start
    assert (back.tx, back.tz) == (start[0], start[1] + 1)  # the gate out is right behind you


def test_cinderhold_loads_with_its_bridge_fortress_and_twin_gargoyles():
    m = _cinder()
    assert m.meta["name"] == "The Cinderhold"
    kinds = [s.kind for s in m.entities]
    assert kinds.count("brand") == 1 and kinds.count("bellows") == 1
    for foe in ("forge_golem", "iron_bowman", "slag_hound"):
        assert foe in kinds
    for hazard in ("flame_jet", "magma_vent"):
        assert hazard in kinds
    assert kinds.count("save_statue") == 2
    assert {"spire", "chimney", "anvil"} <= set(kinds)
    assert any(t.lava for _, _, t in m.each_tile())
    # The long bridge: a deck at least twenty tiles long running north over the lava gorge.
    start = tuple(int(v) for v in m.meta["start"][:2])
    deck = [z for z in range(m.depth) if m[29, z].floor_tex == "flagstone" and m[29, z].floor == 0]
    gorge = [z for z in deck if m[27, z].chasm and m[27, z].floor_tex == "lava"]
    assert len(gorge) >= 20
    assert start[1] > max(gorge)  # you arrive south of it and cross northward
    # The roof is high above everything, where the twins perch.
    (brand,) = _spec(m, "brand")
    assert m[brand.tx, brand.tz].floor >= 12 and m[brand.tx, brand.tz].open_sky
    # The new loot is in its chests.
    items = {s.props.get("item") for s in _spec(m, "chest")}
    assert {"scroll_thunder", "scroll_motes", "stormbrand", "slagbreaker", "forge_key"} <= items


def test_cinderhold_skyline_has_no_two_towers_alike_and_stands_out_of_reach():
    """The fortress's silhouette: no landmark repeats another's shape, and every one stands where no
    one walks (on the wall tops, in the moat, or above a passage's roof)."""
    m = _cinder()
    marks = [s for s in m.entities if s.kind in LANDMARKS]
    assert {"keep", "gatehouse", "bastion", "smokestack", "lavafall", "spire"} <= {s.kind for s in marks}
    towers = [(s.kind, tuple(sorted(s.props.items()))) for s in marks if s.kind != "lavafall"]
    assert len(towers) == len(set(towers))
    reach = _reachable(m, tuple(int(v) for v in m.meta["start"][:2]), avoid=_lava(m))
    for s in marks:
        tile = m[s.tx, s.tz]
        roofed = tile.ceil is not None  # a passage: the landmark rises above its roof
        assert (s.tx, s.tz) not in reach or roofed, (s.kind, s.tx, s.tz)


def test_cinderhold_is_solvable():
    """Every chest, lever and both gargoyles can be reached with only the honest doors and the false
    wall opened: the forge key's chest without its door. The main gate and the smelter lift are
    shortcuts, each joining two places you can already reach. Nowhere strands you."""
    m = _cinder()
    lava = _lava(m)
    start = tuple(int(v) for v in m.meta["start"][:2])
    reach = _reachable(m, start, avoid=lava)
    (key_chest,) = [s for s in _spec(m, "chest") if s.props.get("item") == "forge_key"]
    (key_door,) = _spec(m, "door", key="forge_key")
    (postern,) = [s for s in _spec(m, "door") if not s.props.get("key")]
    secrets = [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    honest = [(postern.tx, postern.tz), *secrets]
    before_key = _reachable(m, start, open_tiles=honest, avoid=lava)
    assert (key_chest.tx, key_chest.tz) in before_key
    (brand,) = _spec(m, "brand")
    assert (brand.tx, brand.tz) not in before_key  # up past the locked rampart door
    opened = _reachable(m, start, open_tiles=[*honest, (key_door.tx, key_door.tz)], avoid=lava)
    assert (postern.tx, postern.tz) not in reach  # the postern is shut until you open it
    for s in m.entities:
        if s.kind in ("chest", "lever", "brand", "bellows", "mimic"):
            assert (s.tx, s.tz) in opened, (s.kind, s.props)
        if s.kind in ("save_statue", "anvil", "chimney"):  # solid: you stand beside them
            around = {(s.tx + dx, s.tz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))}
            assert around & opened, (s.kind, s.tx, s.tz)
    (store,) = [s for s in _spec(m, "chest") if s.props.get("item") == "stormbrand"]
    assert (store.tx, store.tz) not in _reachable(m, start, open_tiles=[(postern.tx, postern.tz)], avoid=lava)
    # The main gate joins the bridge to the gatehouse; the lift joins the pits to the guardroom.
    (gate,) = _spec(m, "gate")
    assert {(gate.tx, gate.tz - 1), (gate.tx, gate.tz + 1)} <= opened
    for p in terrain.build_platforms(m):
        if not p.lever:
            continue
        sx, sz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        near = {(sx + dx, sz + dz) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))}
        assert {round(m[t].floor, 1) for t in near & opened} >= {p.low, p.high}, (sx, sz)
    # Every tile you can drop into, you can climb back out of.
    doors = [(s.tx, s.tz) for s in m.entities if s.kind in ("door", "gate", "secret_wall")]
    full = _reachable(m, start, open_tiles=doors, shortcuts=True, avoid=lava)
    for tile in full:
        assert start in _reachable(m, tile, open_tiles=doors, shortcuts=True, avoid=lava), tile


def test_cinderhold_gate_shortcut_cuts_the_way_back_to_the_bridge():
    """Through the postern it is a long way round from the gatehouse shrine to the bridge; the main
    gate, once raised, opens straight onto it."""
    m = _cinder()
    shrine = min(_spec(m, "save_statue"), key=lambda s: s.tz)
    (gate,) = _spec(m, "gate")
    (postern,) = [s for s in _spec(m, "door") if not s.props.get("key")]
    here = (shrine.tx - 1, shrine.tz)
    bridge = (gate.tx, gate.tz + 2)
    long_way = _steps(m, here, bridge, [(postern.tx, postern.tz)])
    short_way = _steps(m, here, bridge, [(postern.tx, postern.tz), (gate.tx, gate.tz)])
    assert long_way > 2 * short_way, (long_way, short_way)
