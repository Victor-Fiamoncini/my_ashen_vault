"""The open sea past Harrowmere's grid (`world/sea.py`)."""

import math
from itertools import pairwise
from pathlib import Path

import pytest

from ashen_vault import map_path
from ashen_vault.world import sea
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.sky import SUN_AT

MAPS = sorted(
    p.stem for p in (Path(__file__).resolve().parent.parent / "src" / "ashen_vault" / "maps").glob("*.map")
)


@pytest.fixture(scope="module")
def town():
    return MapLoader.load_file(map_path("harrowmere"))


def test_only_the_town_opens_its_sea_to_the_horizon():
    assert [n for n in MAPS if sea.is_open(MapLoader.load_file(map_path(n)))] == ["harrowmere"]


def test_the_sea_fog_reaches_farther_than_the_land_and_follows_it():
    assert sea.fog_range((8, 40)) == (8, 40 * sea.SEA_REACH)
    assert sea.fog_range((2, 10))[1] < sea.fog_range((8, 40))[1]  # darkness pulls it in too
    assert sea.glitter_fog_range((8, 40))[1] > sea.fog_range((8, 40))[1]


def test_the_far_water_runs_from_the_grid_edge_to_the_horizon_without_gaps(town):
    cells = sea.far_cells(town)
    edge = town.depth * sea.T
    assert cells and all(z0 >= edge - 1e-6 for _x0, z0, _x1, _z1 in cells)
    assert min(z0 for _x0, z0, _x1, _z1 in cells) == pytest.approx(edge)
    assert max(z1 for _x0, _z0, _x1, z1 in cells) >= edge + sea.FAR
    # Every row of cells spans the whole grid's width and more, edge to edge with the next row.
    rows = {}
    for x0, z0, x1, z1 in cells:
        rows.setdefault((z0, z1), []).append((x0, x1))
    spans = sorted(rows)
    for (_, a1), (b0, _) in pairwise(spans):
        assert a1 == pytest.approx(b0)
    for xs in rows.values():
        xs.sort()
        assert xs[0][0] < 0 and xs[-1][1] > town.width * sea.T
        assert all(a[1] == pytest.approx(b[0]) for a, b in pairwise(xs))


def test_the_far_cells_grow_with_distance(town):
    cells = sea.far_cells(town)
    near = min(cells, key=lambda c: c[1])
    far = max(cells, key=lambda c: c[1])
    assert near[2] - near[0] == sea.FIRST_CELL
    assert far[2] - far[0] == sea.LAST_CELL
    assert len(cells) < 8000


def test_a_map_without_an_open_sea_has_no_far_water():
    assert sea.far_cells(MapLoader.load_file(map_path("sunken_keep"))) == []


def test_the_suns_glints_lie_along_its_bearing_over_the_sea():
    verts, uvs, weights = sea.glitter(40.0, 60.0, 82.0, -0.8, SUN_AT, frame=0)
    pts = [verts[i : i + 3] for i in range(0, len(verts), 3)]
    assert len(pts) == len(weights) == len(uvs) // 2
    dx, dz = sea.sun_path(SUN_AT)
    assert all((p[0] - 40.0) * dx + (p[2] - 60.0) * dz >= 82.0 - 60.0 - 1e-6 for p in pts)  # all on the sea
    assert all(p[1] > -0.8 for p in pts)
    near = [p for p in pts if p[2] < 90]
    far = [p for p in pts if p[2] > 500]
    width = lambda ps: max(p[0] for p in ps) - min(p[0] for p in ps)  # noqa: E731
    assert width(far) > width(near) * 5  # it widens with distance, keeping one width to the eye
    assert max(weights) == pytest.approx(1.0) and min(weights) == 0.0
    # It twinkles: another frame shifts its glints, never its shape.
    verts2, uvs2, _ = sea.glitter(40.0, 60.0, 82.0, -0.8, SUN_AT, frame=1)
    assert verts2 == verts and uvs2 != uvs


def test_no_glints_where_the_sun_stands_over_land():
    assert sea.glitter(0.0, 0.0, 82.0, -0.8, (270.0, 13.0)) is None


def test_the_sun_path_is_a_unit_bearing():
    dx, dz = sea.sun_path(SUN_AT)
    assert math.hypot(dx, dz) == pytest.approx(1.0)
