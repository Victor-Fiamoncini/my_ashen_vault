"""The great cracks down Old Harrowmere's cavern walls (`world/wall_cracks.py`)."""

import math

import pytest

from ashen_vault import map_path
from ashen_vault.render import bounds, sunken_models
from ashen_vault.world import wall_cracks
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from test_prison_world import FakeGame


@pytest.fixture(scope="module")
def city():
    return MapLoader.load_file(map_path("old_harrowmere"))


@pytest.fixture(scope="module")
def cracks(city):
    return wall_cracks.cracks(city)


@pytest.fixture(scope="module")
def world():
    from ashen_vault.world.world import World

    return World(FakeGame(), "old_harrowmere")


def test_the_same_map_always_cracks_the_same_way(city, cracks):
    assert wall_cracks.cracks(city) == cracks
    assert wall_cracks.cracks(MapLoader.load_file(map_path("old_harrowmere"))) == cracks


def test_every_crack_splits_a_dressed_wall_tall_over_the_open_ground_it_faces(city, cracks):
    assert 20 <= len(cracks) <= wall_cracks.MAX_CRACKS
    for c in cracks:
        wall, ground = city[c.tx, c.tz], city[c.tx + c.dx, c.tz + c.dz]
        assert wall_cracks.dressed(wall) and wall.solid
        assert not ground.solid and ground.ceil is None
        assert wall.top - max(ground.floor, wall.top - wall_cracks.MAX_SPAN) >= wall_cracks.MIN_HEIGHT
        assert c.y >= ground.floor - 1e-6 and c.y + c.height <= wall.top + 1e-6  # on the face, not past it
        assert (math.cos(c.yaw), math.sin(c.yaw)) == pytest.approx((c.dx, c.dz), abs=1e-9)  # out of the wall
        # its middle lies on the face of its own wall tile
        cx, cz = TileMap.center(c.tx, c.tz)
        assert abs((c.x - cx) * c.dx + (c.z - cz) * c.dz - TileMap.TILE / 2) < 1e-6
        assert (
            abs((c.x - cx) * c.dz) <= TileMap.TILE / 2 + 1e-6
            and abs((c.z - cz) * c.dx) <= TileMap.TILE / 2 + 1e-6
        )


def test_cracks_on_one_face_keep_apart(cracks):
    for a in cracks:
        for b in cracks:
            if a is not b and (a.dx, a.dz) == (b.dx, b.dz) and (a.x == b.x if a.dx else a.z == b.z):
                assert math.hypot(a.x - b.x, a.z - b.z) >= wall_cracks.MIN_GAP - 1e-6


def test_some_cracks_seep_mortar_light_but_most_are_dark(cracks):
    lit = sum(c.seep for c in cracks)
    assert 0 < lit < len(cracks) / 2


def test_the_cap_keeps_the_tallest(city, monkeypatch, cracks):
    monkeypatch.setattr(wall_cracks, "MAX_CRACKS", 10)
    few = wall_cracks.cracks(city)
    assert len(few) == 10
    assert min(c.height for c in few) >= sorted((c.height for c in cracks), reverse=True)[9]


def test_a_wall_can_carry_cracks_beside_another_dressing(city):
    wall = next(t for _, _, t in city.each_tile() if wall_cracks.dressed(t))
    for dress, cracked in (("cracks", True), ("rampart,cracks", True), ("rampart", False), (None, False)):
        wall.dress = dress
        assert wall_cracks.dressed(wall) is cracked
    wall.dress = "cracks"


def test_the_world_splits_no_crack_by_a_door_gate_lift_or_fall(world):
    from ashen_vault.world.world import CRACK_CLEAR, RAMPART_GATES, WALL_PROPS

    placed = [p for p in world.props if p.kind == "wall_crack"]
    assert placed
    keep = [(e.tx, e.tz) for e in world.map.entities if e.kind in RAMPART_GATES or e.kind in CRACK_CLEAR]
    assert any(e.kind == "lift" for e in world.map.entities)
    hung = [(e.tx, e.tz) for e in world.map.entities if e.kind in WALL_PROPS]
    for p in placed:
        reach = float(p.props["reach"])
        # every tile of open ground the crack spreads over, along its face
        ox, oz = p.x + math.cos(p.yaw) * 0.5, p.z + math.sin(p.yaw) * 0.5
        ax, az = abs(math.sin(p.yaw)), abs(math.cos(p.yaw))
        for s in (-reach, 0.0, reach):
            ground = TileMap.tile_coord(ox + ax * s), TileMap.tile_coord(oz + az * s)
            assert all(max(abs(ground[0] - gx), abs(ground[1] - gz)) > 2 for gx, gz in keep), p
            assert all(max(abs(ground[0] - hx), abs(ground[1] - hz)) > 1 for hx, hz in hung), p


@pytest.mark.parametrize("seep", [False, True])
def test_a_crack_lies_on_its_wall_within_its_reach(seep):
    from ashen_vault.render.rig import Rig
    from test_prop_bake import _Recorder

    gpu = _Recorder()
    sunken_models.wall_crack(Rig(gpu), 4242, 24.0, 2.0, seep)
    for kind, m, *_ in gpu.parts:
        assert kind == "quad"
        assert 0 < m[3] <= max(sunken_models.CRACK_OUT) + 1e-6  # a hair off the face, no farther
        assert (
            m[1] > 0 and m[5] == pytest.approx(0, abs=1e-4) and m[9] == pytest.approx(0, abs=1e-4)
        )  # faces out
    (_, lo_y, lo_z), (_, hi_y, hi_z) = bounds.measure(
        lambda r: sunken_models.wall_crack(r, 4242, 24.0, 2.0, seep)
    )
    assert lo_y >= -0.5 and hi_y <= 24.5  # within its own height, give or take a segment's end
    assert lo_z >= -2.5 and hi_z <= 2.5


def test_a_crack_glows_only_where_it_seeps():
    from ashen_vault.render.rig import Rig
    from test_prop_bake import _Recorder

    for seep in (False, True):
        gpu = _Recorder()
        sunken_models.wall_crack(Rig(gpu), 7, 18.0, 2.0, seep)
        assert len(gpu.parts) < 200  # cheap enough to bake dozens of them
        assert any(glow for *_, glow in gpu.parts) is seep


def test_a_map_can_crack_shorter_runs_and_let_more_cracks_seep(city):
    """`[meta] crack_run` lets runs shorter than MIN_RUN carry a crack (the Cinderhold's bays between its
    great windows; never less than two tiles), and `crack_seep` sets the share that seep (its fires glow
    through half)."""
    import copy

    base = wall_cracks.cracks(city)
    loose = copy.copy(city)
    loose.meta = {**city.meta, "crack_run": "1", "crack_seep": "1"}  # read as two
    more = wall_cracks.cracks(loose)
    assert len(more) >= len(base) and all(c.seep for c in more)
    assert all(c.reach <= wall_cracks.MAX_REACH for c in more)
    dry = copy.copy(city)
    dry.meta = {**city.meta, "crack_seep": "0"}
    assert not any(c.seep for c in wall_cracks.cracks(dry))
    assert [(c.x, c.z, c.height) for c in wall_cracks.cracks(dry)] == [(c.x, c.z, c.height) for c in base]
