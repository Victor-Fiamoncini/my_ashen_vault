"""Headless checks for the raylib-free parts of the renderer."""

import random

import pytest

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
    for ch, rows in tinyfont.MICRO.items():
        assert len(rows) == tinyfont.MICRO_HEIGHT and all(0 <= r < 8 for r in rows), ch
    assert [r[1] for r in tinyfont.rects("I", 0, 0, tinyfont.MICRO)] == [0, 1, 2, 3]
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
        assert kind in ("cube", "sphere", "cyl", "cone", "quad", "blade", "lozenge", "wedge")
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
            assert a.motion in models.MOTIONS or a.motion in ("jab", "hook", "onetwo"), a.motion


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
                for kind in (weapons.LIGHT, weapons.HEAVY, weapons.QUICK, None):
                    p.swing_t = None
                    p.guarding = kind is None
                    p.stamina.fill()
                    hand = "right"
                    if kind and p.hand_item(hand).kind == "weapon":
                        p.start_swing(hand, kind, secrets=False)
                        p.swing_t = p.swing_time * 0.5
                    gpu = _RecordingGpu()
                    models.weapon_view(rig.Rig(gpu), p, 0.0, t=1.0)
                    assert len(gpu.parts) >= 6, (id_, body, gloves, kind)
    # Edged weapons leave a smear of ghost blades through the blow; blunt ones don't.
    for id_, smears in (("rusted_sword", True), ("katana", True), ("mace", False)):
        p = Player(inventory=Inventory(right=id_))
        p.start_swing()
        p.swing_t = p.swing_hit_at
        gpu = _RecordingGpu()
        models.weapon_view(rig.Rig(gpu), p, 0.0)
        ghosts = models.TRAIL_GHOSTS if smears else 0
        blades = sum(1 for kind, _ in gpu.parts if kind == "blade")
        assert blades >= ghosts and (blades >= 1 if smears else blades == 0), id_
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


def _drawn(type_id, phase2=False, state="chase"):
    import random

    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    e = Enemy(EnemyTypes.get(type_id), 0, 0, rng=random.Random(0))
    e.state, e.state_t, e.anim_t, e.phase2 = state, 0.5, 1.0, phase2
    gpu = _ExtentGpu()
    models.enemy(rig.Rig(gpu), e)
    count = _RecordingGpu()
    models.enemy(rig.Rig(count), e)
    return gpu, len(count.parts)


def test_bosses_have_boss_level_detail():
    for boss in ("ashen_warden", "butcher", "brand", "bellows", "loom_mother"):
        assert _drawn(boss)[1] >= 50, boss
    for foe in ("bone_walker", "gaoler", "forge_golem", "iron_bowman", "slag_hound", "bone_crawler", "mimic"):
        assert _drawn(foe)[1] >= 30, foe


def test_phase_two_changes_how_each_boss_looks():
    for boss in ("ashen_warden", "butcher", "brand", "bellows"):
        (calm, calm_n), (raging, raging_n) = _drawn(boss), _drawn(boss, phase2=True)
        assert raging.glows > calm.glows or raging_n > calm_n, boss
        dead, _ = _drawn(boss, phase2=True, state="dead")
        assert dead.glows == 0, f"{boss}'s fires go out when it dies"


def test_keep_props_lift_lever_and_fire_draw():
    from ashen_vault.render import models

    gpu = _RecordingGpu()
    r = rig.Rig(gpu)
    for k in (0.0, 0.5, 1.0):
        models.lever(r, k, wall=True)
        models.lever(r, k, wall=False)
    models.lift(r, 0.5, True, 6.0)
    models.lift(r, 0.5, False, 60.0)  # a very tall shaft caps its chain links
    models.lift(r, 0.5, True, 6.0, "cage", ((1, 0),))
    models.lift(r, 0.5, False, 2.0, "cage", ())  # a low shaft squats the cage
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
    models.headsman_block(r, 1)
    models.meat_hooks(r, 0.5, 1, 4.0)
    models.eruption(r, 0.6, 0.0, 0.5)
    models.eruption(r, 0.0, 0.8, 0.5)
    models.shockwave_ring(r, 0.4, 4.0)
    assert len(gpu.parts) > 300


def test_ossuary_texture_is_built():
    from ashen_vault.render import texture_gen

    tex = texture_gen.all_textures()
    assert "ossuary" in tex and len(tex["ossuary"]) == len(tex["stone_brick"])


def test_jungle_fires_mushrooms_bridge_and_wooden_lever_draw():
    from ashen_vault.render import models

    gpu = _RecordingGpu()
    r = rig.Rig(gpu)
    for lit in (True, False):
        models.brazier(r, 0.5, lit=lit)
        models.bonfire(r, 0.5, lit=lit)
    for k in (0.0, 0.5, 1.0):
        models.lever(r, k, wall=True, wood=True)
        models.lever(r, k, wall=False, wood=True)
        models.bridge(r, k)
        models.flare(r, (255, 140, 40), k)
    models.giant_mushroom(r, 3, 0.5)
    models.shelf_fungus(r, 2, 0.5)
    models.mushrooms(r, 4)
    models.totem(r, 1, 0.5)
    models.cave_mouth(r, 0.5)
    models.secret_wall(r, 1.4, 0.0, tex="web_wall")
    for id_ in ("venom", "veil", "pyre"):
        models.spell_orb(r, id_, 0.5)
    assert len(gpu.parts) > 150  # the levers are plain now


def test_a_cold_fire_draws_no_flame():
    from ashen_vault.render import models

    for draw in (models.brazier, models.bonfire):
        cold, burning = _ExtentGpu(), _ExtentGpu()
        draw(rig.Rig(cold), 0.5, lit=False)
        draw(rig.Rig(burning), 0.5, lit=True)
        assert cold.glows == 0 and burning.glows > 0


def test_web_wall_texture_has_holes_to_see_through():
    from ashen_vault.render import texture_gen

    tex = texture_gen.web_wall()
    alphas = tex[3::4]
    assert 0 in alphas and 255 in alphas


def test_cinderhold_props_shots_and_hazards_draw():
    from ashen_vault.render import forge_models

    gpu = _ExtentGpu()
    r = rig.Rig(gpu)
    forge_models.road_gate(r)
    forge_models.spire(r, 3, 10.0)
    forge_models.spire(r, 4, 7.0, 2.8, "flat")
    forge_models.bastion(r, 2, 6.0)
    forge_models.bastion(r, 3, 14.0, 2.6, base=6.2)
    forge_models.smokestack(r, 0.5, 18.0)
    forge_models.gatehouse(r, 0.5, 1)
    forge_models.keep(r, 0.5, 2)
    forge_models.lavafall(r, 0.5, 20.0, 11)
    forge_models.anvil(r, 0.5)
    forge_models.chimney(r, 0.5, 2.6)
    forge_models.embers_rain(r, 0.5, 2)
    forge_models.magma_vent(r, 0.5)
    forge_models.magma_bomb(r, 0.5)
    forge_models.arrow(r, (150, 150, 160))
    forge_models.thunder_spear(r, 0.5)
    forge_models.mote(r, 0.5)
    assert gpu.glows > 0
    cold, roaring = _ExtentGpu(), _ExtentGpu()
    forge_models.flame_jet(rig.Rig(cold), 0.0, 0.0, 2.0, 0.5)
    forge_models.flame_jet(rig.Rig(roaring), 1.0, 1.0, 2.0, 0.5)
    assert cold.glows == 0 and roaring.glows > 0
    assert roaring.glows > 4  # the gout of flame itself


def test_a_perched_gargoyle_is_a_cold_grey_statue():
    import random

    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    for type_id in ("brand", "bellows"):
        e = Enemy(EnemyTypes.get(type_id), 0, 0, rng=random.Random(0))
        perched = _ExtentGpu()
        models.enemy(rig.Rig(perched), e)
        e.rouse()
        e.anim_t = 1.0
        awake = _ExtentGpu()
        models.enemy(rig.Rig(awake), e)
        assert perched.glows == 0 and awake.glows > 0, type_id
    # Bellows hovers once awake; perched, it squats on the parapet like Brand.
    assert awake.bottom > 0.3 and perched.bottom < 0.1


def _off_forearm(wrist):
    """Degrees between a held weapon and the forearm's line (0 = extending it, 180 = folded back)."""
    import math

    rel = (wrist + math.pi / 2 + math.pi) % (2 * math.pi) - math.pi
    return abs(math.degrees(rel))


def test_aim_wrist_points_the_weapon_and_takes_the_short_way():
    import math

    from ashen_vault.render import models

    for direction in (-math.pi / 2, 0.0, 1.0, math.pi / 2):
        for arm in (-2.0, 0.0, 1.5, 3.4):
            w = models.aim_wrist(direction, arm)
            assert -math.pi <= w <= math.pi
            assert math.cos(arm + w) == pytest.approx(math.cos(direction))
            assert math.sin(arm + w) == pytest.approx(math.sin(direction))


def test_armed_foes_hold_weapons_out_from_the_fist_through_a_chop():
    """The weapon stays out from the hand, never folded back along the arm (the old 'glued' look),
    and the chop comes down from overhead in front rather than swinging up from behind."""
    import random

    from ashen_vault.ai.enemy import Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    e = Enemy(EnemyTypes.get("bone_walker"), 0, 0, rng=random.Random(0))
    for state in ("idle", "chase", "windup", "attack", "recover", "hurt"):
        for t in (0.0, 0.05, 0.1, 0.2, 0.5, 2.0):
            e.state, e.state_t = state, t
            assert _off_forearm(models.wrist_angle(e)) <= 150, (state, t)
    e.state, e.state_t = "windup", 5.0
    raised = models.chop_angle(e)
    e.state, e.state_t = "attack", 5.0
    assert raised > models.chop_angle(e) > 0  # down from overhead, landing in front


def test_the_wardens_blade_never_folds_back_in_any_move():
    import random

    from ashen_vault.ai.enemy import COMBO_GAP, Enemy
    from ashen_vault.ai.enemy_types import EnemyTypes
    from ashen_vault.render import models

    type_ = EnemyTypes.get("ashen_warden")
    for move in (None, *type_.moves, *type_.phase_moves, "kindle"):
        for state in ("chase", "windup", "attack", "recover"):
            for t in (0.0, 0.1, 0.3, COMBO_GAP * 1.2, COMBO_GAP * 2.5):
                e = Enemy(type_, 0, 0, rng=random.Random(0))
                e.state, e.state_t, e.attack_kind = state, t, move
                hit, _, blade, elbow, *_ = models._warden_arms(e, 1.3)
                wrist = models.aim_wrist(blade, hit + elbow)
                assert _off_forearm(wrist) <= 150, (move, state, t)


def test_every_weapon_preview_is_centred_and_fits_its_window():
    from ashen_vault.player.items import Items
    from ashen_vault.render import bounds, models

    for item in Items.ALL.values():
        if item.kind != "weapon":
            continue
        lo, hi = bounds.measure(lambda r, i=item: models.item(r, i.id, 0.0))
        assert abs((lo[1] + hi[1]) / 2) < 0.05, item.id  # the whip once hung at the bottom
        assert hi[1] - lo[1] <= models.PREVIEW_HEIGHT + 1e-6, item.id
        assert hi[1] - lo[1] >= 0.9, item.id


def test_every_villager_draws_as_a_person_in_every_idle():
    """Each villager has legs, a torso, two jointed arms with hands and a face; whatever they do,
    nothing sinks below the floor and they stand about a person's height."""
    from ashen_vault.render import bounds, models
    from ashen_vault.world import villagers

    for id_ in (*villagers.LOOKS, "stranger"):
        look = villagers.look(id_)
        for t in (0.0, 0.7, 1.9):
            gpu = _RecordingGpu()
            models.npc(rig.Rig(gpu), look, t)
            assert len(gpu.parts) >= 35, id_
            assert min(y for _, y in gpu.parts) > -0.1, id_
        (_, lo_y, _), (_, hi_y, _) = bounds.measure(lambda r, look=look: models.npc(r, look, 0.0))
        assert lo_y > -0.1 and 1.5 < hi_y < 3.6, (id_, hi_y)  # a staff or spear may stand taller


def test_villager_looks_are_checked_and_strangers_wear_grey():

    from ashen_vault.world import villagers

    assert villagers.look("nobody") == villagers.Look()
    with pytest.raises(AssertionError):
        villagers.Look(build="giant")
    assert villagers.look("brannoc").tool == "hammer" and villagers.look("corvane").blade


def test_the_enthroned_is_boss_sized_on_a_throne_that_fits_its_tile():
    from ashen_vault.render import bounds, models

    gpu = _RecordingGpu()
    models.enthroned(rig.Rig(gpu), 1.0)
    assert len(gpu.parts) >= 50
    (lo_x, lo_y, lo_z), (hi_x, hi_y, hi_z) = bounds.measure(models.throne)
    assert lo_y >= 0 and hi_y > 4.0  # a high back
    assert max(-lo_x, hi_x, -lo_z, hi_z) <= 1.0  # inside its 2 m tile


def test_the_enthroned_is_stone_with_no_glow_but_the_drifting_dust():
    """Petrified: no eye glints, no glowing gem, no breath. The only lit specks are the dust motes."""
    from ashen_vault.render import models

    class Lit(_RecordingGpu):
        def __init__(self):
            super().__init__()
            self.lit = []

        def draw_part(self, kind, matrix, rgb, tex="white", glow=False):
            super().draw_part(kind, matrix, rgb, tex, glow)
            if glow:
                self.lit.append(rgb)

    for t in (0.0, 7.5):
        gpu = Lit()
        models.enthroned(rig.Rig(gpu), t)
        assert gpu.lit and set(gpu.lit) == {models.DUST_MOTE}
    still = [_RecordingGpu(), _RecordingGpu()]
    models.enthroned(rig.Rig(still[0]), 0.0)
    models.enthroned(rig.Rig(still[1]), 3.0)
    statue = len(still[0].parts) - 10  # all but the ten dust motes
    assert still[0].parts[:statue] == still[1].parts[:statue], "the stone never moves"


def test_town_props_draw_and_roofs_cover_their_buildings():
    from ashen_vault.render import bounds, town_models

    gpu = _RecordingGpu()
    r = rig.Rig(gpu)
    town_models.silent_bell(r, 0.5)
    town_models.cathedral_spire(r, 15)
    for seed in range(4):
        town_models.pew(r, seed)
        town_models.window(r, seed)
        town_models.bed(r, seed)
        town_models.cupboard(r, seed)
        town_models.shelf(r, seed)
        town_models.stall(r, seed, 0.5)
        town_models.fence(r, seed)
        town_models.boat(r, 0.5, seed)
    town_models.hearth(r, 0.5)
    town_models.lamp_post(r, 0.5)
    assert len(gpu.parts) > 300
    for w, d, ridge in ((6, 7, "z"), (8, 7, "x"), (17, 7, "x")):
        (lo_x, lo_y, lo_z), (hi_x, hi_y, hi_z) = bounds.measure(
            lambda r, w=w, d=d, ridge=ridge: town_models.roof(r, w, d, ridge, top=4.2, pitch=2.4)
        )
        # The NW corner tile is the origin: the roof spans every tile to the SE, eaves overhanging.
        assert lo_x < -1.0 and hi_x > (w - 1) * 2 + 1.0, (w, d)
        assert lo_z < -1.0 and hi_z > (d - 1) * 2 + 1.0, (w, d)
        assert lo_y >= 4.0 and hi_y == pytest.approx(4.2 + 2.4, abs=0.2)


def test_every_tool_hat_hair_and_build_a_villager_can_have_draws():
    """Options no villager uses yet (a lantern, a brimmed hat) still draw, so a new villager can."""
    from ashen_vault.render import models
    from ashen_vault.world import villagers

    for tool, hat, hair, build in zip(
        villagers.TOOLS,
        [*villagers.HATS] * 3,
        [*villagers.HAIR_STYLES] * 3,
        [*villagers.BUILDS] * 2,
        strict=False,
    ):
        for garb in villagers.GARBS:
            look = villagers.Look(tool=tool, hat=hat, hair_style=hair, build=build, garb=garb)
            gpu = _RecordingGpu()
            models.npc(rig.Rig(gpu), look, 0.4)
            assert len(gpu.parts) >= 30, (tool, hat, hair, build, garb)


def test_a_raised_shield_shows_the_hand_gripping_it():
    # The first-person view has no depth test: the arm and fist behind a raised shield must be drawn
    # after it, or the shield hides them.
    from ashen_vault.player.inventory import Inventory
    from ashen_vault.player.player import Player
    from ashen_vault.render import models

    class Colours(_RecordingGpu):
        def draw_part(self, kind, matrix, rgb, tex="white", glow=False):
            super().draw_part(kind, matrix, rgb, tex, glow)
            self.parts[-1] = tuple(rgb)

    for id_ in models.SHIELD_GRIPS:
        alone = Colours()
        models.shield(rig.Rig(alone), id_)
        p = Player(inventory=Inventory(right=None, left=id_))
        p.guarding = True
        gpu = Colours()
        models.shield_view(rig.Rig(gpu), p, p.hand_item("left"), 0.0, -1, {"body": None, "gloves": None})
        n = len(alone.parts)
        assert gpu.parts[:n] == alone.parts, id_  # the shield first...
        assert models.SKIN in gpu.parts[n:], id_  # ...then the arm and the fist on its strap


def test_axe_and_hammer_heads_lead_their_blows():
    """An axe's bit (a hammer's face) faces the way the swing travels as it lands, instead of lying
    flat along the swing with its edge pointing off to the side."""
    import math

    from ashen_vault.player import weapons
    from ashen_vault.player.items import Items
    from ashen_vault.render import models

    rest = (0.9, -0.33, 0.27, 0.25, 0.7, -0.55)
    for id_ in models.HEADED:
        item = Items.get(id_)
        reach = models.WEAPON_LEN.get(id_, 1.0)
        for kind in (weapons.LIGHT, weapons.HEAVY):
            a = weapons.moveset(item)[kind]

            def pose(p, a=a):
                return tuple(b + d for b, d in zip(rest, models._motion(a.motion, p, a.hit_at), strict=True))

            before = models._weapon_point(pose(a.hit_at - 0.03), 1, reach)
            at = models._weapon_point(pose(a.hit_at), 1, reach)
            v = [q - p for p, q in zip(before, at, strict=True)]
            edge = models._pose_vector(pose(a.hit_at), 1, (1.0, 0.0, 0.0))
            assert sum(e * d for e, d in zip(edge, v, strict=True)) / math.hypot(*v) > 0.7, (id_, kind)


def test_every_key_and_relic_has_its_own_model():
    """No key or sigil falls back to the plain preview cube; each draws its detailed model, in
    Belongings and lying on the ground."""
    from ashen_vault.player.items import Items
    from ashen_vault.render import models

    for item in Items.ALL.values():
        if item.kind != "key":
            continue
        assert item.id in models.KEY_STYLES or item.id in models.SIGILS, item.id
        gpu = _RecordingGpu()
        models.item(rig.Rig(gpu), item.id, 0.5)
        assert len(gpu.parts) >= 20, item.id  # the old key was four boxes
        ground = _RecordingGpu()
        models.pickup(rig.Rig(ground), 0.5, item.id)
        assert len(ground.parts) > len(gpu.parts), item.id  # the item itself, in its halo
