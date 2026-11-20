import os

from ashen_vault import MAP_DIR
from ashen_vault.world.fences import fence_arms
from ashen_vault.world.map_loader import MapLoader

E, W, S, N = (1, 0), (-1, 0), (0, 1), (0, -1)

# A garden: a fence along its north row from the wall, turning down its east side, with a gap in it.
GARDEN = """[meta]
name = Garden
start = 1 4 0

[legend]
# = wall tex=stone_brick top=4
. = floor h=0

[grid]
#######
#.....#
#.....#
#.....#
#.....#
#######

[entities]
| = fence
"""


def _garden(rows):
    text = GARDEN.replace("#.....#\n#.....#\n#.....#\n#.....#", "\n".join(rows))
    map_ = MapLoader(text, name="garden").parse()
    return map_, {(e.tx, e.tz) for e in map_.entities if e.kind == "fence"}


def test_a_fence_runs_along_its_row_and_turns_its_corner():
    map_, fences = _garden(["#.....#", "#|||..#", "#..|..#", "#.....#"])
    assert fence_arms(map_, 2, 2, fences) == (E, W)  # mid-run: the whole tile, along X
    assert fence_arms(map_, 1, 2, fences) == (E, W)  # its end against the wall
    assert set(fence_arms(map_, 3, 2, fences)) == {W, S}  # the corner: only its own two sides
    # The run's end beside its gap spans its whole tile, so the gap stays a tile wide.
    assert fence_arms(map_, 3, 3, fences) == (S, N)


def test_a_fence_under_a_wall_runs_alongside_it_not_into_it():
    map_, fences = _garden(["#.|||.#", "#.....#", "#.....#", "#.....#"])
    assert fence_arms(map_, 3, 1, fences) == (E, W)


def test_a_lone_fence_keeps_its_hurdle_along_z():
    map_, fences = _garden(["#.....#", "#..|..#", "#.....#", "#.....#"])
    assert fence_arms(map_, 3, 2, fences) == (S, N)


def test_harrowmeres_east_west_fences_run_along_their_rows():
    town = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    fences = {(e.tx, e.tz) for e in town.entities if e.kind == "fence"}
    for tx, tz in fences:
        arms = fence_arms(town, tx, tz, fences)
        row = (tx - 1, tz) in fences and (tx + 1, tz) in fences
        column = (tx, tz - 1) in fences and (tx, tz + 1) in fences
        if row and not column:
            assert arms == (E, W), (tx, tz)
        if column and not row:
            assert arms == (S, N), (tx, tz)
        # Every hurdle runs on into something: no fence stands across its own run.
        for dx, dz in arms:
            if (tx + dx, tz + dz) in fences:
                assert (-dx, -dz) in fence_arms(town, tx + dx, tz + dz, fences), (tx, tz)
