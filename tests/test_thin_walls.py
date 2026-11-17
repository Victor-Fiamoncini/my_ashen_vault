import math
import os

import pytest

from ashen_vault import MAP_DIR
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.world import collision, thin_walls
from ashen_vault.world.map_loader import MapLoader

# A thin-walled house in a yard: two rooms split by a partition, a door in the south wall.
HOUSE = """[meta]
name = House
start = 1 1 0

[legend]
# = wall tex=stone_brick top=6
H = wall tex=plaster top=4 thin=0.5
. = floor h=0
i = floor h=0.2 ceil=3

[grid]
#########
#.......#
#.HHHHH.#
#.HiHiH.#
#.HiiiH.#
#.HHiHH.#
#.......#
#########
"""


@pytest.fixture
def house():
    return MapLoader(HOUSE, name="house").parse()


def _local_slab(lay):
    return {cell for cell, owner in lay.cells.items() if owner is None}


def test_the_legend_marks_a_thin_wall(house):
    assert house[2, 2].thin == 0.5
    assert house[0, 0].thin is None
    assert house.layout(0, 0) is None


def test_a_straight_run_spans_its_tile_against_the_open_sky(house):
    assert sorted(house.layout(3, 2).boxes()) == [
        (6.0, 4.0, 6.75, 4.5),
        (6.75, 4.0, 7.25, 4.5),
        (7.25, 4.0, 8.0, 4.5),
    ]
    margins = house.layout(3, 2).margins()
    assert {owner for _, owner in margins} == {(3, 3)}  # the room runs on up to the slab


def test_a_corner_hugs_both_outer_sides(house):
    lay = house.layout(2, 2)
    assert _local_slab(lay) == {(1, 1), (2, 1), (1, 2)}
    assert lay.xs[:3] == (0.0, 0.0, 0.5) and lay.zs[:3] == (0.0, 0.0, 0.5)
    assert lay.margins() == [((4.5, 4.5, 6.0, 6.0), (3, 3))]  # the room's corner, lent by its diagonal


def test_a_partition_joins_the_outer_wall_in_a_t_and_stands_centred(house):
    tee = house.layout(4, 2)
    assert _local_slab(tee) == {(0, 1), (1, 1), (2, 1), (1, 2)}
    assert tee.xs[1:3] == (0.75, 1.25)
    part = house.layout(4, 3)
    assert part.xs[1:3] == (0.75, 1.25)
    assert {owner for _, owner in part.margins()} == {(3, 3), (5, 3), (4, 4)}  # the room below too


def test_a_door_jamb_spans_to_the_doorway(house):
    lay = house.layout(3, 5)
    assert lay.zs[1:3] == (1.5, 2.0)  # against the yard to the south
    x0 = min(b[0] for b in lay.boxes())
    x1 = max(b[2] for b in lay.boxes())
    assert (x0, x1) == (6.0, 8.0)


def test_a_margin_lends_its_floor_and_the_slab_is_solid(house):
    assert house.tile_at(7.0, 5.5) is house[3, 3]
    assert house.floor_at(7.0, 5.5) == pytest.approx(0.2)
    assert house.tile_at(7.0, 4.2).solid
    assert house.tile_at(9.0, 7.0).solid  # inside the partition


def test_wall_inset_reaches_the_slab(house):
    assert house.wall_inset(3, 3, 0, -1) == pytest.approx(1.5)  # north wall, hugging the yard
    assert house.wall_inset(3, 3, 1, 0) == pytest.approx(0.75)  # the centred partition
    assert house.wall_inset(1, 1, -1, 0) == 0.0  # a full wall
    assert thin_walls.inset(house, 1, 1, 1, 0) == 0.0  # not a thin wall at all


def test_props_back_onto_a_thin_slab(house):
    x, z = house.backed(3, 3, math.pi / 2)  # facing south, its back to the north wall
    assert (x, z) == pytest.approx((7.0, 5.5))
    assert house.seated(3, 3, math.pi / 2) == pytest.approx((7.0, 5.5 - 0.6))
    assert house.backed(3, 4, math.pi / 2) == pytest.approx((7.0, 9.0))  # nothing behind


def test_walking_stops_at_the_slab_not_the_tile_edge(house):
    x, z = 7.0, 7.0
    for _ in range(60):
        x, z = collision.move(house, x, z, 0, -0.1, radius=0.4)
    assert z == pytest.approx(4.5 + 0.4, abs=0.01)
    assert collision.circle_clear(house, 7.0, 5.0, 0.4, 0.2, None)
    assert not collision.circle_clear(house, 7.0, 4.8, 0.4, 0.2, None)


def test_walking_out_through_the_door(house):
    x, z = 9.0, 9.0
    for _ in range(40):
        x, z = collision.move(house, x, z, 0, 0.1, radius=0.4)
    assert z > 12.5  # out in the yard


def test_a_margin_over_a_step_too_high_blocks():
    walled = HOUSE.replace("i = floor h=0.2 ceil=3", "i = floor h=1.4 ceil=4")
    house = MapLoader(walled, name="house").parse()
    # From the yard, beside the corner of the house, you can't climb into the room's margin.
    assert not collision.circle_clear(house, 5.5, 5.5, 0.4, 0.0, None, home=(1, 1))


def test_sight_crosses_margins_but_not_slabs(house):
    assert collision.line_of_sight(house, 7.0, 5.0, 7.0, 9.0)
    assert not collision.line_of_sight(house, 7.0, 7.0, 11.0, 7.0)  # the partition


def _triangles(builder):
    for batch in builder.batches.values():
        v = batch.verts
        for k in range(0, len(v), 9):
            yield [(v[k + n], v[k + n + 1], v[k + n + 2]) for n in (0, 3, 6)]


def test_the_mesh_draws_the_slab_not_the_tile_edge(house):
    builder = MeshBuilder(house).build()
    tris = list(_triangles(builder))

    def on_plane(z):
        return [t for t in tris if all(p[2] == pytest.approx(z) and 6.0 <= p[0] <= 8.0 for p in t)]

    assert not on_plane(6.0)  # no face left at the room's edge of the north wall's tile
    inner = on_plane(4.5)
    assert inner and max(p[1] for t in inner for p in t) == pytest.approx(3.0)  # up to the ceiling
    outer = on_plane(4.0)
    assert outer and max(p[1] for t in outer for p in t) == pytest.approx(4.0)  # the full wall outside


def test_the_lintel_over_the_door_rises_with_the_walls(house):
    tris = list(_triangles(MeshBuilder(house).build()))
    lintel = [t for t in tris if all(p[2] == pytest.approx(12.0) and 8.0 <= p[0] <= 10.0 for p in t)]
    assert max(p[1] for t in lintel for p in t) == pytest.approx(4.0)


def test_a_point_on_the_far_edge_of_a_tile_still_finds_its_cell(house):
    lay = house.layout(2, 2)
    assert lay.owner_at(2.0, 2.0) == (3, 3)  # the room's corner, at the tile's very edge
    assert lay.owner_at(0.0, 0.0) is None  # the slab's outer corner


def _edge_slab(map_, tx, tz, d):
    """The spans of slab along the edge of tile (tx, tz) toward d, merged: the whole edge for a full
    wall, nothing for an open tile."""
    tile = map_[tx, tz]
    if not tile.solid:
        return []
    lay = map_.layout(tx, tz)
    if lay is None:
        a = (tz if d[0] else tx) * thin_walls.TILE
        return [(a, a + thin_walls.TILE)]
    spans = []
    for x0, z0, x1, z1 in lay.boxes():
        edge = {
            (1, 0): math.isclose(x1, (tx + 1) * thin_walls.TILE),
            (-1, 0): math.isclose(x0, tx * thin_walls.TILE),
            (0, 1): math.isclose(z1, (tz + 1) * thin_walls.TILE),
            (0, -1): math.isclose(z0, tz * thin_walls.TILE),
        }[d]
        if edge:
            spans.append((z0, z1) if d[0] else (x0, x1))
    merged = []
    for a, b in sorted(spans):
        if merged and a <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    return [(round(a, 3), round(b, 3)) for a, b in merged]


def _seams(map_):
    """Every edge where two thin tiles meet with their slabs out of line: each slab's end is left
    open there (the other's margin lies against it), a see-through slit from the street."""
    seams = []
    for tx, tz, tile in map_.each_tile():
        if not tile.thin:
            continue
        for d in ((1, 0), (0, 1)):
            nx, nz = tx + d[0], tz + d[1]
            if not (nx < map_.width and nz < map_.depth) or not map_[nx, nz].thin:
                continue
            if _edge_slab(map_, tx, tz, d) != _edge_slab(map_, nx, nz, (-d[0], -d[1])):
                seams.append(((tx, tz), (nx, nz)))
    return seams


# A house backing onto a low court wall (`_`) at its north-west corner and one tile of its west side.
BACKED = """[meta]
name = Backed
start = 1 1 0

[legend]
# = wall tex=stone_brick top=6
_ = wall tex=stone_brick top=2
H = wall tex=plaster top=4 thin=0.5
. = floor h=0
i = floor h=0.2 ceil=3

[grid]
##########
#...._...#
#....HHHH#
#....HiiH#
#..._HiiH#
#....HiiH#
#....HHHH#
##########
"""


def test_a_slab_backing_onto_a_low_wall_keeps_the_line_of_its_run():
    backed = MapLoader(BACKED, name="backed").parse()
    assert backed.layout(5, 3).xs[1] == 0.0  # hugs the sky to the west
    assert backed.layout(5, 4).xs[1] == 0.0  # backs onto the low wall, in line with the run
    assert backed.layout(5, 2).zs[1] == 0.0  # the corner under the low wall hugs it, like its run
    assert _seams(backed) == []


def test_harrowmere_has_no_slits_between_its_thin_walls():
    town = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    assert _seams(town) == []
