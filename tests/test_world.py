import glob
import math
import numbers
import os

import pytest

from ashen_vault import MAP_DIR
from ashen_vault.world import collision
from ashen_vault.world.hazards import CrumbleFloor
from ashen_vault.world.map_loader import MapError, MapLoader
from ashen_vault.world.tile_map import Tile, TileMap
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
    *("altar", "table", "rack", "rubble"),
)


def test_sunken_keep_decor_never_cuts_off_anything():
    """Flood fill from the start (doors and gates count as open): every chest, door, lever,
    exit and the iron maiden must stay reachable, so no barrel plugs a corridor."""
    m = MapLoader.load_file(os.path.join(MAP_DIR, "sunken_keep.map"))
    for e in m.entities:  # crumbling floors start solid
        if e.kind == "crumble":
            m.set_override(
                (e.tx, e.tz), CrumbleFloor(e.tx, e.tz, float(e.props["floor"]), m[e.tx, e.tz]).solid_tile()
            )
    solid = {(e.tx, e.tz) for e in m.entities if e.kind in STATIC_BLOCKERS}
    sx, sz = (int(v) for v in m.meta["start"][:2])
    seen = {(sx, sz)}
    todo = [(sx, sz)]
    while todo:
        tx, tz = todo.pop()
        for nx, nz in ((tx + 1, tz), (tx - 1, tz), (tx, tz + 1), (tx, tz - 1)):
            if (nx, nz) in seen or (nx, nz) in solid:
                continue
            if not collision.passable(m, nx, nz, m[tx, tz].floor) or m[nx, nz].pit:
                continue
            seen.add((nx, nz))
            todo.append((nx, nz))

    def touched(tx, tz):
        return any((tx + dx, tz + dz) in seen for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)))

    kinds = ("chest", "door", "gate", "lever", "exit", "iron_maiden", "mimic", "barrel", "altar")
    targets = [e for e in m.entities if e.kind in kinds]
    assert {"iron_maiden", "mimic"} <= {e.kind for e in targets}
    for e in targets:
        assert touched(e.tx, e.tz), f"{e.kind} at {e.tx},{e.tz} is unreachable"


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
