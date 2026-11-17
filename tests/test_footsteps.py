from pathlib import Path
from types import SimpleNamespace

from ashen_vault.audio import synth
from ashen_vault.world import footsteps
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import Tile

MAPS = Path(__file__).resolve().parent.parent / "src" / "ashen_vault" / "maps"


def _floor_texes():
    texes = set()
    for path in MAPS.glob("*.map"):
        m = MapLoader.load_file(path)
        for tz in range(m.depth):
            for tx in range(m.width):
                tile = m[tx, tz]
                if not tile.solid:
                    texes.add(tile.floor_tex)
    return texes


def test_every_floor_in_every_map_has_a_surface_of_its_own():
    unmapped = {
        t for t in _floor_texes() if t not in footsteps.TEX_SURFACE and t not in ("flagstone", "lava")
    }
    # Anything else is stone by default: name it here if it sounds like stone, else map it.
    stone_like = {
        "cobble", "setts", "slate", "rough_stone", "ashlar", "stone_brick", "black_brick", "mossy_brick",
        "ash_flagstone", "ash_stone", "ash_brick", "ossuary", "cliff_rock",
    }  # fmt: skip
    assert unmapped <= stone_like, unmapped - stone_like


def test_each_surface_has_its_step_sound():
    names = synth.sounds().keys()
    for surface in footsteps.SURFACES:
        assert f"step_{surface}" in names
    assert set(footsteps.TEX_SURFACE.values()) <= set(footsteps.SURFACES)


def test_the_floor_sets_the_sound_and_a_platform_overrides_it():
    assert footsteps.sound(Tile(floor_tex="wood_plank")) == "step_wood"
    assert footsteps.sound(Tile(floor_tex="mud")) == "step_mud"
    assert footsteps.sound(Tile(floor_tex="flagstone")) == "step_stone"
    assert footsteps.sound(Tile(floor_tex=None)) == "step_stone"
    water = Tile(floor_tex="water")
    assert footsteps.sound(water) == "step_water"
    assert footsteps.sound(water, SimpleNamespace(kind="raft", model="")) == "step_wood"
    assert footsteps.sound(water, SimpleNamespace(kind="ledge", model="")) == "step_stone"
    assert footsteps.sound(water, SimpleNamespace(kind="lift", model="cage")) == "step_metal"
    assert footsteps.sound(water, SimpleNamespace(kind="lift", model="")) == "step_wood"
