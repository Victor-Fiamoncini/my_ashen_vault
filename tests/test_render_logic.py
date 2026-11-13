"""Headless checks for the raylib-free parts of the renderer."""

import random

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
    models.cocoon(r, 4)
    models.cocoon(r, 4, broken=True)
    models.frog_idol(r, 0.0)
    models.frog_idol(r, 0.5)
    models.secret_wall(r, 6.0, 0.3, tex="vine_wall")
    for id_ in Items.ALL:
        models.item(r, id_, 0.5)
    assert len(gpu.parts) > 100


class _ExtentGpu:
    """Tracks how high a model reaches (corner of every part) and whether anything still glows."""

    def __init__(self):
        self.top = -1e9
        self.bottom = 1e9
        self.glows = 0

    def to_matrix(self, m):
        return m

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        for cx in (-0.5, 0.5):
            for cy in (-0.5, 0.5):
                for cz in (-0.5, 0.5):
                    y = m[4] * cx + m[5] * cy + m[6] * cz + m[7]
                    self.top, self.bottom = max(self.top, y), min(self.bottom, y)
        self.glows += glow


JUNGLE_ENEMIES = ("snare_bloom", "bark_husk", "stump_mimic", "loom_mother", "loom_brood")


def _extent(type_id, state, state_t):
    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    e = Enemy(EnemyTypes.get(type_id), 0, 0, rng=random.Random(0))
    e.state, e.state_t, e.anim_t = state, state_t, 1.3
    gpu = _ExtentGpu()
    models.enemy(rig.Rig(gpu), e)
    return e, gpu


def test_death_fall_eases_from_alive_to_settled():
    from ashen_vault.render import models

    e, _ = _extent("loom_mother", "idle", 5.0)
    assert models.death_fall(e) == 0.0
    e.state, e.state_t = "dead", 0.0
    assert models.death_fall(e) == 0.0
    e.state_t = 0.3
    assert 0.0 < models.death_fall(e) < 1.0
    e.state_t = 5.0
    assert models.death_fall(e) == 1.0


def test_every_enemy_collapses_into_a_death_pose():
    from ashen_vault.ai.enemy_types import EnemyTypes

    for type_id in EnemyTypes.ALL:
        _, alive = _extent(type_id, "chase", 0.5)  # awake: a Stump Mimic at rest is already stump-sized
        e, dead = _extent(type_id, "dead", 3.0)
        # The body sinks into its death pose, and the ash dissolve's span covers it, so it crumbles
        # from its real top rather than losing its top all at once.
        assert dead.top < alive.top, type_id
        span_top = (e.type.hover + e.type.height / 2) if e.type.hover else e.type.height
        assert dead.top <= span_top * 1.1, (type_id, dead.top, span_top)
        # Nothing sinks further through the floor in death than it does alive (a husk's roots dig in).
        assert dead.bottom >= min(alive.bottom, 0.0) - 0.15, (type_id, dead.bottom, alive.bottom)


def test_dead_glowing_enemies_go_dark():
    for type_id in ("loom_mother", "bark_husk", "ashen_warden", "mimic", "cinder_wisp"):
        _, alive = _extent(type_id, "idle", 0.5)
        _, dead = _extent(type_id, "dead", 3.0)
        assert alive.glows > 0 and dead.glows == 0, type_id


def test_long_lists_scroll():
    assert screen.scroll_into_view(0, 3, 30) == 0
    assert screen.scroll_into_view(0, 12, 30) == 12 - screen.LIST_ROWS + 1
    assert screen.scroll_into_view(5, 3, 30) == 3
    assert screen.scroll_into_view(19, 29, 30) == 30 - screen.LIST_ROWS
    assert screen.scroll_into_view(4, 2, 5) == 0
    # Scrolled by 10: the first visible row is item 10; rows past the visible window miss.
    assert screen.list_row_at(40, 30, 240, 30, 50, 50, first=10, visible=11) == 10
    assert screen.list_row_at(40, 30, 240, 30, 50, 50 + 11 * 11, first=10, visible=11) is None


def test_motions_start_and_end_at_rest_and_land_on_the_blow():
    from ashen_vault.render import models

    for motion, (_, strike, _) in models.MOTIONS.items():
        assert models._motion(motion, 0.0) == models.REST, motion
        assert all(abs(v) < 1e-9 for v in models._motion(motion, 1.0)), motion
        hit = models._motion(motion, 0.45, hit_at=0.45)
        assert all(abs(a - b) < 1e-9 for a, b in zip(hit, strike, strict=True)), motion


def test_every_attack_motion_has_a_pose():
    from ashen_vault.player import weapons
    from ashen_vault.render import models

    for moves in weapons.MOVESETS.values():
        for a in moves.values():
            assert a.motion in models.MOTIONS or a.motion in ("jab", "hook"), a.motion


def test_first_person_view_draws_every_hand_and_swing():
    from ashen_vault.player import weapons
    from ashen_vault.player.inventory import SPELL, Inventory
    from ashen_vault.player.items import Items
    from ashen_vault.player.player import Player
    from ashen_vault.render import models

    held = [i.id for i in Items.ALL.values() if i.kind in ("weapon", "shield")]
    for body in (None, "ringmail", "blackened_plate"):
        for gloves in (None, "iron_gauntlets", "chain_mitts"):
            for id_ in [*held, None]:
                inv = Inventory(right=None, left=SPELL, body=body, hands=gloves)
                if id_:
                    inv.add(id_)
                    inv.equip(id_)
                p = Player(inventory=inv)
                p.spells = ["flame"]
                for kind in (weapons.LIGHT, weapons.HEAVY, None):
                    p.swing_t = None
                    p.guarding = kind is None
                    hand = "right"
                    if kind and p.hand_item(hand).kind == "weapon":
                        p.start_swing(hand, kind)
                        p.swing_t = p.swing_time * 0.5
                    gpu = _RecordingGpu()
                    models.weapon_view(rig.Rig(gpu), p, 0.0, t=1.0)
                    assert len(gpu.parts) >= 6, (id_, body, gloves, kind)
    # Holding a katana heavy settles into the draw stance without errors.
    p = Player(inventory=Inventory(right="katana"))
    p.charge_t = 1.0
    gpu = _RecordingGpu()
    models.weapon_view(rig.Rig(gpu), p, 0.0)
    assert gpu.parts


def test_every_special_move_has_a_pose():
    import random

    from ashen_vault.ai.enemy import COMBO_GAP, MOVES, Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    for type_ in EnemyTypes.ALL.values():
        for move in (*type_.moves, *type_.phase_moves, "kindle"):
            for state, t in (("windup", 0.3), ("attack", 0.05), ("attack", COMBO_GAP * 2.2)):
                gpu = _RecordingGpu()
                e = Enemy(type_, 0, 0, rng=random.Random(0))
                e.state, e.state_t, e.anim_t, e.attack_kind = state, t, 1.3, move
                e.phase2 = move in type_.phase_moves
                models.enemy(rig.Rig(gpu), e)
                assert len(gpu.parts) >= 4, (type_.id, move, state)
                if type_.id in ("ashen_warden", "gaoler"):
                    assert min(y for _, y in gpu.parts) > -0.3, (type_.id, move, state)
        assert set(type_.moves) <= set(MOVES), type_.id


def test_the_wardens_blade_burns_in_his_second_phase():
    import random

    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    e = Enemy(EnemyTypes.get("ashen_warden"), 0, 0, rng=random.Random(0))
    e.state, e.anim_t = "chase", 1.0
    calm, burning = _ExtentGpu(), _ExtentGpu()
    models.enemy(rig.Rig(calm), e)
    e.phase2 = True
    models.enemy(rig.Rig(burning), e)
    assert burning.glows > calm.glows


def test_keep_props_lift_lever_and_fire_draw():
    from ashen_vault.render import models

    gpu = _RecordingGpu()
    r = rig.Rig(gpu)
    for k in (0.0, 0.5, 1.0):
        models.lever(r, k, wall=True)
        models.lever(r, k, wall=False)
    models.lift(r, 0.5, True, 6.0)
    models.lift(r, 0.5, False, 60.0)  # a very tall shaft caps its chain links
    models.ember_crest(r, (200, 180, 140))
    models.banner(r, 0.5, 2)
    models.pillar(r, 3, 4.9)
    models.sarcophagus(r, 2)
    models.cage(r, 0.5, 1, 3.4)
    models.cobweb(r, 1)
    models.cobweb(r, 2)
    models.skull_niche(r, 0.5, 3)
    models.grate(r, 0.5)
    models.roots(r, 0.5, 2, 3.4)
    models.winch(r, 0.5, True)
    models.winch(r, 0.5, False)
    models.bell(r, 0.5, 1)
    models.eruption(r, 0.6, 0.0, 0.5)
    models.eruption(r, 0.0, 0.8, 0.5)
    models.shockwave_ring(r, 0.4, 4.0)
    assert len(gpu.parts) > 300


def test_ossuary_texture_is_built():
    from ashen_vault.render import texture_gen

    tex = texture_gen.all_textures()
    assert "ossuary" in tex and len(tex["ossuary"]) == len(tex["stone_brick"])
