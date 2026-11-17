"""The carved bays along Harrowmere's great walls (`world/ramparts.py`)."""

import math

import pytest

from ashen_vault import map_path
from ashen_vault.render import bounds, town_models
from ashen_vault.world import ramparts
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from test_keep_world import FakeGame


@pytest.fixture(scope="module")
def town():
    return MapLoader.load_file(map_path("harrowmere"))


@pytest.fixture(scope="module")
def bays(town):
    return ramparts.bays(town)


def test_every_bay_dresses_a_great_wall_facing_open_ground(town, bays):
    assert len(bays) > 60
    for b in bays:
        wall, ground = town[b.tx, b.tz], town[b.tx + b.dx, b.tz + b.dz]
        assert wall.dress == ramparts.DRESS and wall.solid
        assert not ground.solid and ground.ceil is None
        assert b.height >= ramparts.MIN_HEIGHT
        assert (math.cos(b.yaw), math.sin(b.yaw)) == pytest.approx((b.dx, b.dz), abs=1e-9)  # out of the wall


def test_bays_stay_clear_of_the_wall_towers(town, bays):
    for e in (e for e in town.entities if e.kind == "wall_tower"):
        x, z = TileMap.center(e.tx, e.tz)
        sx, sz = (float(v) for v in e.props.get("shift", "0,0").split(","))
        radius = float(e.props.get("radius", "2.2"))
        for b in bays:
            assert math.hypot(b.x - x - sx, b.z - z - sz) >= radius + 1.0


def test_piers_recur_along_every_run_and_close_its_ends(bays):
    faces = {(b.tx, b.tz, b.dx, b.dz): b.kind for b in bays}
    for (tx, tz, dx, dz), kind in faces.items():
        ax, az = abs(dz), abs(dx)
        if (tx - ax, tz - az, dx, dz) not in faces or (tx + ax, tz + az, dx, dz) not in faces:
            assert kind == "pier"
    kinds = [b.kind for b in bays]
    assert kinds.count("arch") > 30 and kinds.count("pier") > 10


def test_the_sea_wall_is_dressed_too(town, bays):
    assert any(b.tx == 0 and town[b.tx + b.dx, b.tz + b.dz].deep for b in bays)


def test_the_world_hangs_no_bay_by_a_gate_or_on_anything_hung_there():
    from ashen_vault.world.world import RAMPART_GATES, WALL_PROPS, World

    world = World(FakeGame(), "harrowmere")
    placed = [p for p in world.props if p.kind == "rampart_bay"]
    assert placed
    gates = [(e.tx, e.tz) for e in world.map.entities if e.kind in RAMPART_GATES]
    hung = {(e.tx, e.tz) for e in world.map.entities if e.kind in WALL_PROPS}
    for p in placed:
        ground = (
            TileMap.tile_coord(p.x + math.cos(p.yaw) * 0.5),
            TileMap.tile_coord(p.z + math.sin(p.yaw) * 0.5),
        )
        assert ground not in hung
        assert all(max(abs(ground[0] - gx), abs(ground[1] - gz)) > 1 for gx, gz in gates)


@pytest.mark.parametrize("kind", ["pier", "arch"])
def test_a_bay_stands_out_no_farther_than_you_stand_off_a_wall(kind):
    (_, lo_y, lo_z), (hi_x, hi_y, hi_z) = bounds.measure(lambda r: town_models.rampart_bay(r, kind, 7.0, 2))
    assert hi_x <= 0.41  # the player's radius: you brush along it as along the bare wall
    assert lo_y >= -0.01 and hi_y > 7.0  # its merlons stand on the wall top
    assert lo_z >= -1.0 - 1e-6 and hi_z <= 1.0 + 1e-6  # within its own tile's span
