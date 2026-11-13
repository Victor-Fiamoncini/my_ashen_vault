"""Headless checks for the raylib-free parts of the renderer."""

from ashen_vault import map_path, screen
from ashen_vault.render import rig, texture_gen
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.ui import tinyfont
from ashen_vault.world.map_loader import MapLoader


def test_textures_are_rgba_64():
    tex = texture_gen.all_textures()
    for name, data in tex.items():
        assert len(data) == 64 * 64 * 4, name
    assert tex["iron_bars"][3] == 255  # bar pixel at (0, 0)


def test_mesh_builder_batches_shipped_maps():
    for name in ("harrowmere", "sunken_keep", "verdant_hollow"):
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


def test_tinyfont_glyphs_and_width():
    for ch, rows in tinyfont.GLYPHS.items():
        assert len(rows) == tinyfont.HEIGHT, ch
        assert all(0 <= r < 8 for r in rows), ch
    assert tinyfont.width("HP 40") == 5 * tinyfont.ADVANCE - 1
    assert tinyfont.width("") == 0
    # Unknown characters draw as blanks instead of raising; lower case is upper-cased.
    assert list(tinyfont.rects("~", 0, 0)) == []
    assert list(tinyfont.rects("i", 0, 0)) == list(tinyfont.rects("I", 0, 0))
    # "-" is one 3 px run on the middle row.
    assert list(tinyfont.rects("-", 10, 20)) == [(10, 22, 3, 1)]


def test_to_internal_undoes_letterbox():
    assert screen.to_internal(480, 360, 960, 720) == (160, 120)
    # 1920x1080: scale 4.5, the 1440 px wide picture starts 240 px in.
    assert screen.to_internal(240, 0, 1920, 1080) == (0, 0)
    assert screen.to_internal(240 + 4.5 * 10, 4.5 * 20, 1920, 1080) == (10, 20)
    assert screen.to_internal(100, 500, 1920, 1080) is None
    assert screen.to_internal(1800, 500, 1920, 1080) is None


def test_menu_hit_testing():
    # list_menu(x=40, y=30, w=240): rows start at y + 20, 11 px each.
    assert screen.list_row_at(40, 30, 240, 3, 50, 50) == 0
    assert screen.list_row_at(40, 30, 240, 3, 50, 50 + 22) == 2
    assert screen.list_row_at(40, 30, 240, 3, 50, 50 + 33) is None  # below the last row
    assert screen.list_row_at(40, 30, 240, 3, 50, 40) is None  # on the title
    assert screen.list_row_at(40, 30, 240, 3, 300, 50) is None  # past the right edge
    assert screen.centered_row_at(160, 140, 14, 3, 50, 160, 140) == 0
    assert screen.centered_row_at(160, 140, 14, 3, 50, 120, 140 + 28) == 2
    assert screen.centered_row_at(160, 140, 14, 3, 50, 160, 140 + 42) is None
    assert screen.centered_row_at(160, 140, 14, 3, 50, 20, 140) is None


def test_fungus_glows_teal_by_default():
    m = MapLoader.load_file(map_path("verdant_hollow"))
    lights = MeshBuilder.lights_for(m)
    fungus = [s for s in m.entities if s.kind == "fungus"]
    assert fungus
    teal = [l for l in lights if l.color == [0.3, 0.85, 0.65]]
    assert len(teal) == len(fungus)
    assert all(l.y < 1.6 + 1.2 for l in teal)


class _RecordingGpu:
    """Stands in for Gpu: counts the parts a model draws instead of touching raylib."""

    def __init__(self):
        self.parts = []

    def to_matrix(self, m):
        return m

    def draw_part(self, kind, matrix, rgb, tex="white", glow=False):
        assert kind in ("cube", "sphere", "cyl", "cone", "quad")
        assert all(0 <= c <= 255 for c in rgb), rgb
        self.parts.append((kind, matrix[7]))


def test_every_enemy_model_draws_in_every_state():
    import random

    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    for type_ in EnemyTypes.ALL.values():
        for state in ("idle", "chase", "windup", "attack", "recover", "hurt", "dead"):
            gpu = _RecordingGpu()
            e = Enemy(type_, 0, 0, rng=random.Random(0))
            e.state = state
            e.state_t = 0.1
            e.anim_t = 1.3
            models.enemy(rig.Rig(gpu), e)
            assert len(gpu.parts) >= 4, (type_.id, state)
            # Nothing sinks far below the floor (the y of each part's origin).
            assert min(y for _, y in gpu.parts) > -0.3, (type_.id, state)


def test_jungle_props_and_relic_icons_draw():
    from ashen_vault.player.items import Items
    from ashen_vault.render import models

    gpu = _RecordingGpu()
    r = rig.Rig(gpu)
    models.jungle_tree(r, 3, 0.5)
    models.fungus(r, 2, 0.5)
    models.vine_door(r, 0.5)
    for id_ in Items.ALL:
        models.item(r, id_, 0.5)
    assert len(gpu.parts) > 100
