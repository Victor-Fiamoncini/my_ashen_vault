"""The jungle's new mechanics driven headless: darkness, fires you kindle, the new spells, one-way
doors and the drawbridge."""

import math

import pytest

from ashen_vault.ai.enemy import STATUS_TICK, VEIL_LOSE, VEIL_NOTICE, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.spells import Spells
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.world import darkness, doors
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import Gout, World
from test_enemy import FakeWorld
from test_keep_world import FakeGame


class JungleGame(FakeGame):
    def __init__(self, flags=()):
        super().__init__(flags)
        self.kills = []

    def damage_enemy(self, enemy, dmg, poise_mult=1.0, stagger=True):
        if enemy.take_hit(dmg, poise_mult, stagger=stagger):
            self.kills.append(enemy)


def jungle(at, yaw=0.0, flags=()):
    game = JungleGame(flags)
    world = World(game, "verdant_hollow")
    world.enemies = []  # placed by each test as needed
    x, z = TileMap.center(*at)
    game.player.place(x, z, yaw, world.map)
    return game, world


def prop(world, kind, **props):
    return next(
        p for p in world.props if p.kind == kind and all(p.props.get(k) == v for k, v in props.items())
    )


def foe(world, type_id, at):
    x, z = TileMap.center(*at)
    e = Enemy(EnemyTypes.get(type_id), x, z)
    world.enemies.append(e)
    return e


# --- darkness ------------------------------------------------------------------------------------


def test_dark_legend_tiles_lose_ambient_light():
    m = MapLoader(
        """[meta]
name = Dark
start = 1 1 0
ambient = 0.5 0.5 0.5

[legend]
# = wall
. = floor h=0
d = floor h=0 dark=0.8

[grid]
####
#.d#
####
"""
    ).parse()
    assert m[1, 1].dark == 0.0 and m[2, 1].dark == pytest.approx(0.8)
    b = MeshBuilder(m)
    lit = b.light_at(*TileMap.center(1, 1)[:1], 0.0, TileMap.center(1, 1)[1])
    dim = b.light_at(TileMap.center(2, 1)[0], 0.0, TileMap.center(2, 1)[1])
    assert lit == pytest.approx([0.5, 0.5, 0.5])
    assert dim == pytest.approx([0.1, 0.1, 0.1])


def test_dark_places_shrink_your_light_and_lumen_pushes_it_back():
    torch = [8, 0.7, 0.78, 0.55]
    assert darkness.player_light(torch, 0.0) == (8, [0.7, 0.78, 0.55])
    radius, _ = darkness.player_light(torch, 1.0)
    assert radius == darkness.DARK_RADIUS
    lumen, rgb = darkness.player_light(torch, 1.0, lumen=True)
    assert lumen == darkness.DARK_RADIUS + darkness.LUMEN_RADIUS and rgb == list(darkness.LUMEN_RGB)
    # A map that gives you no light of your own still leaves a faint glow in the dark.
    radius, rgb = darkness.player_light([0, 0, 0, 0], 1.0)
    assert radius == darkness.DARK_RADIUS and rgb == list(darkness.DARK_GLOW)


def test_dark_fog_closes_in_and_turns_black_and_the_veil_turns_it_pale():
    rgb, rng = darkness.fog_for([0.2, 0.4, 0.2], [3, 22], 1.0)
    assert rgb == [0.0, 0.0, 0.0] and rng == darkness.DARK_FOG_RANGE
    _, lit = darkness.fog_for([0.2, 0.4, 0.2], [3, 22], 1.0, lumen=True)
    assert lit[1] > rng[1]
    pale, near = darkness.fog_for([0.2, 0.4, 0.2], [3, 22], 0.0, veil=True)
    assert all(c > 0.3 for c in pale) and near[1] == darkness.VEIL_FOG_RANGE[1]


def test_the_eye_adjusts_gradually():
    k = darkness.ease_toward(0.0, 1.0, 0.1)
    assert 0.0 < k < 1.0
    assert darkness.ease_toward(0.95, 1.0, 1.0) == 1.0
    assert darkness.ease_toward(1.0, 0.0, 0.1) == pytest.approx(1.0 - darkness.EASE_RATE * 0.1)


# --- fires you kindle -------------------------------------------------------------------------------


def test_a_cold_brazier_is_kindled_by_pyre_and_stays_lit():
    game, world = jungle((15, 31), yaw=math.pi)
    brazier = prop(world, "brazier")
    assert not world.is_lit(brazier)
    before = len(world.builder.lights)
    assert world._interactable(brazier)  # you can look at the cold ashes
    world.pyre(magic=4, gauge=1.0)
    assert world.is_lit(brazier) and f"lit:verdant_hollow:{brazier.tx},{brazier.tz}" in game.flags
    assert len(world.builder.lights) == before + 1  # its light is baked into the cave now
    assert not world.kindle(brazier)  # already burning
    assert not world._interactable(brazier)
    # On the next visit it is still alight.
    _, again = jungle((15, 31), flags=game.flags)
    assert again.is_lit(prop(again, "brazier"))


def test_pyre_only_reaches_what_is_in_front_and_close():
    _, world = jungle((18, 31), yaw=math.pi)  # three tiles off
    world.pyre(magic=4, gauge=1.0)
    assert not world.is_lit(prop(world, "brazier"))
    _, world = jungle((14, 31), yaw=0.0)  # right beside it, facing away
    world.pyre(magic=4, gauge=1.0)
    assert not world.is_lit(prop(world, "brazier"))


def test_pyres_gout_rushes_out_to_its_reach_then_gutters():
    game, world = jungle((15, 31), yaw=math.pi)
    world.pyre(magic=4, gauge=1.0)
    (gout,) = world.gouts
    assert gout.puffs() == []  # nothing yet: it has only just left your hand
    world.update(Gout.RUSH)
    puffs = gout.puffs()
    assert len(puffs) == Gout.PUFFS
    far = puffs[-1]
    assert math.hypot(far[0] - gout.x, far[2] - gout.z) == pytest.approx(
        Spells.PYRE_REACH * math.cos(game.player.pitch)
    )
    assert far[3] > puffs[0][3] and far[4] < puffs[0][4]  # wider and cooler at the front
    world.update(Gout.LIFE)
    assert world.gouts == []


def test_pyre_comes_back_faster_than_other_spells():
    assert Spells.get("pyre").recovery < Spells.get("flame").recovery


def test_a_flame_bolt_flying_past_a_cold_brazier_lights_it():
    game, world = jungle((17, 31), yaw=math.pi)
    world.fire_bolt(10)
    for _ in range(120):
        world._update_projectiles(1 / 60)
    assert world.is_lit(prop(world, "brazier"))
    assert "kindle" in game.sounds


def test_lit_fires_and_glowing_decor_add_lights_and_cold_ones_do_not():
    m = MapLoader(
        """[meta]
name = Fires
start = 1 1 0

[legend]
# = wall
. = floor h=0

[grid]
#######
#abcde#
#######

[entities]
a = bonfire
b = bonfire unlit
c = brazier unlit
d = giant_mushroom
e = shelf_fungus
"""
    ).parse()
    assert len(MeshBuilder.lights_for(m)) == 3
    lit = MeshBuilder.lights_for(m, lit=lambda spec: spec.kind == "brazier")
    assert len(lit) == 4


# --- spells ----------------------------------------------------------------------------------------------


def test_new_spells_are_known_by_their_scrolls():
    from ashen_vault.player.items import Items

    for id_ in ("venom", "veil", "pyre"):
        assert Spells.get(id_).cost > 0
        assert Items.get(f"scroll_{id_}").spell == id_


def test_spell_formulas_scale_with_magic():
    assert Spells.venom_damage(8, 1.0) > Spells.venom_damage(2, 1.0)
    seconds, per_tick = Spells.venom_poison(6)
    assert seconds > 0 and per_tick > Spells.venom_poison(0)[1]
    assert Spells.pyre_damage(4, 1.0, flammable=True) > Spells.pyre_damage(4, 1.0)


def test_venom_dart_poisons_what_it_strikes_and_the_poison_keeps_biting():
    game, world = jungle((15, 31), yaw=0.0)
    husk = foe(world, "bark_husk", (17, 31))
    world.fire_bolt(1, effect="venom", rgb=(130, 220, 60))
    for _ in range(60):
        world._update_projectiles(1 / 60)
    assert husk.afflicted == "poison"
    hp = husk.hp
    seconds, per_tick = Spells.venom_poison(game.player.stats.magic)
    for _ in range(int(STATUS_TICK * 60) + 1):
        world.update(1 / 60)
    assert husk.hp == max(hp - per_tick, 0) or not husk.alive
    assert husk.state != "hurt"  # the venom never staggers
    for _ in range(int(seconds * 60) + 60):
        world.update(1 / 60)
    assert husk.afflicted is None


def test_status_ticks_once_a_second_and_runs_out():
    e = Enemy(EnemyTypes.get("bark_husk"), 0, 0)
    e.afflict("burn", 2.5, 3)
    assert sum(e.status_tick(0.5) for _ in range(2)) == 3
    assert sum(e.status_tick(0.5) for _ in range(10)) == 3  # one more bite, then it burns out
    assert e.afflicted is None
    e.afflict("poison", 5, 2)
    e.afflict("poison", 2, 4)  # a fresh dose keeps the longer time and the harder bite
    assert e.status["poison"][:2] == [5, 4]
    e.kill()
    assert e.status_tick(1.0) == 0 and not e.status


def test_lingering_harm_never_staggers():
    e = Enemy(EnemyTypes.get("bark_husk"), 0, 0)
    e.state = "windup"
    assert not e.take_hit(1, poise_mult=99.0, stagger=False)
    assert e.state == "windup"
    e.take_hit(1, poise_mult=99.0)
    assert e.state == "hurt"


def test_pyre_burns_plant_foes_harder_and_sets_them_alight():
    _, world = jungle((15, 31), yaw=0.0)
    husk = foe(world, "bark_husk", (16, 31))
    slime = foe(world, "mire_slime", (16, 32))
    world.pyre(magic=4, gauge=1.0)
    assert husk.type.flammable and not slime.type.flammable
    assert husk.type.hp - husk.hp == Spells.pyre_damage(4, 1.0, flammable=True)
    assert husk.afflicted == "burn"
    assert slime.afflicted is None


def test_a_web_wall_shrugs_off_blades_but_burns():
    game, world = jungle((30, 39), yaw=-math.pi / 2)
    web = prop(world, "secret_wall", model="web")
    assert world.blocked_tile(web.tx, web.tz)
    assert web not in world.strike_props(reach=2.5)
    world.pyre(magic=4, gauge=1.0)
    assert web.open_t > 0 and web.key in game.flags


def test_a_veil_of_mist_hides_you_from_ordinary_foes():
    w = FakeWorld(0.0, 0.0)
    husk = Enemy(EnemyTypes.get("bark_husk"), 3.0, 0.0)
    w.player_hidden = True
    for _ in range(10):
        husk.update(0.1, w)
    assert husk.state == "idle"  # 3 m off, it doesn't see you
    husk.x = VEIL_NOTICE - 0.3
    husk.update(0.1, w)
    assert husk.state != "idle"  # right on top of it, it does
    husk.state = "chase"
    husk.x = VEIL_LOSE + 1.0
    husk.update(0.1, w)
    assert husk.state == "idle"  # and once you slip away it loses you
    boss = Enemy(EnemyTypes.get("loom_mother"), 5.0, 0.0)
    boss.update(0.1, w)
    assert boss.state == "chase"  # bosses see through it


def test_the_veil_lifts_when_you_strike():
    game, _ = jungle((15, 31))
    p = game.player
    p.veil_t = Spells.VEIL_DURATION
    p.start_swing()
    assert p.veil_t == 0.0


# --- shortcuts -------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("side", "spot", "ok"),
    [
        ("n", (0, -1), True),
        ("n", (0, 1), False),
        ("s", (0, 1), True),
        ("e", (1, 0), True),
        ("w", (1, 0), False),
    ],
)
def test_a_barred_door_opens_only_from_its_barred_side(side, spot, ok):
    assert doors.opens_from(side, 10.0, 10.0, 10.0 + spot[0], 10.0 + spot[1]) is ok


def test_a_door_without_a_side_opens_from_anywhere():
    assert doors.opens_from(None, 0, 0, 5, 5)


def test_the_root_lever_lowers_the_drawbridge_for_good():
    game, world = jungle((14, 41))
    bridge = next(p for p in world.terrain.platforms if p.kind == "bridge")
    assert bridge.locked and not bridge.afloat
    world.pull_lever(prop(world, "lever", id="root_bridge"))
    for _ in range(120):
        world.update_terrain(1 / 60)
    assert bridge.afloat
    _, again = jungle((14, 41), flags=game.flags)
    assert next(p for p in again.terrain.platforms if p.kind == "bridge").afloat


def test_kindling_brightens_the_baked_mesh_as_a_full_rebake_would():
    game, world = jungle((15, 31), yaw=math.pi)
    world.kindle(prop(world, "brazier"))
    _, fresh = jungle((15, 31), flags=game.flags)
    for tex, batch in fresh.builder.batches.items():
        assert world.builder.batches[tex].colors == pytest.approx(batch.colors, abs=1e-6), tex


def test_the_dead_cannot_be_poisoned():
    e = Enemy(EnemyTypes.get("bark_husk"), 0, 0)
    e.kill()
    e.afflict("poison", 5, 2)
    assert not e.status and e.afflicted is None


def test_poison_can_finish_a_foe_off():
    game, world = jungle((15, 31))
    husk = foe(world, "bark_husk", (20, 31))
    husk.hp = 2
    husk.afflict("poison", 3, 5)
    for _ in range(int(STATUS_TICK * 60) + 2):
        world.update(1 / 60)
    assert not husk.alive and game.kills == [husk]
    assert not husk.status


def test_a_shrine_rest_clears_the_veil():
    game, _ = jungle((15, 31))
    game.player.veil_t = Spells.VEIL_DURATION
    game.player.revive()
    assert game.player.veil_t == 0.0


def test_the_veil_wears_off_with_time():
    game, _ = jungle((15, 31))
    p = game.player
    p.veil_t = 1.0
    p.update_timers(0.6)
    assert p.veil_t == pytest.approx(0.4)
    p.update_timers(1.0)
    assert p.veil_t == 0.0


def test_dark_values_are_clamped_to_zero_and_one():
    m = MapLoader(
        """[meta]
name = Clamp
start = 1 1 0

[legend]
# = wall dark=2
. = floor h=0 dark=-1

[grid]
###
#.#
###
"""
    ).parse()
    assert m[1, 1].dark == 0.0 and m[0, 0].dark == 1.0
