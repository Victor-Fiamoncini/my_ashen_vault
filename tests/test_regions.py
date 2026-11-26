"""Named regions within a map (`world/regions.py`)."""

from types import SimpleNamespace

from ashen_vault.world import regions
from ashen_vault.world.tile_map import TileMap


def spec(kind, tx, tz, **props):
    return SimpleNamespace(kind=kind, tx=tx, tz=tz, props=props)


def test_build_reads_each_marker_s_name_with_underscores_as_spaces():
    map_ = SimpleNamespace(
        entities=[
            spec("region", 1, 2, name="Sallow_Fen"),
            spec("region", 1, 4, name="The Hold"),
            spec("hint", 0, 0),
        ]
    )
    assert regions.build(map_) == {(1, 2): "Sallow Fen", (1, 4): "The Hold"}


def test_nearest_names_the_closest_marker_and_none_without_markers():
    marks = {(0, 0): "South", (0, 2): "North"}
    assert regions.nearest(marks, *TileMap.center(0, -5)) == "South"
    assert regions.nearest(marks, *TileMap.center(3, 9)) == "North"
    assert regions.nearest({}, 0.0, 0.0) is None
