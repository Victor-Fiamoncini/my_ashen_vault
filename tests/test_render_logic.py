"""Headless checks for the raylib-free parts of the renderer."""

from ashen_vault import map_path
from ashen_vault.render import rig, texture_gen
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.world.map_loader import MapLoader


def test_textures_are_rgba_64():
    tex = texture_gen.all_textures()
    for name, data in tex.items():
        assert len(data) == 64 * 64 * 4, name
    assert tex["iron_bars"][3] == 255  # bar pixel at (0, 0)


def test_mesh_builder_batches_shipped_maps():
    for name in ("harrowmere", "sunken_keep"):
        m = MapLoader.load_file(map_path(name))
        b = MeshBuilder(m, lights=MeshBuilder.lights_for(m)).build()
        assert b.batches
        for batch in b.batches.values():
            assert batch.vertex_count % 3 == 0
            assert len(batch.uvs) == batch.vertex_count * 2
            assert all(0.0 <= c <= 1.0 for c in batch.colors)


def test_rig_matrix_math():
    m = rig.mul(rig.translate(1, 2, 3), rig.scale(2, 2, 2))
    assert m[3] == 1 and m[7] == 2 and m[11] == 3 and m[0] == 2
