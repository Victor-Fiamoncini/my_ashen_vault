"""Weapon arts: a heavy released with both the ATK gauge and the heavy charge full, with the MP to pay,
looses something more than steel (weapons.ARTS), and the ATK bar that shows when one is ready."""

import math

import pytest

from ashen_vault.player import weapons
from ashen_vault.player.inventory import RIGHT, Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.ui import atk_bar
from ashen_vault.world import elements
from ashen_vault.world.world import SLAG_GOUTS
from test_cinderhold_world import hold
from test_verdant_world import foe, jungle, prop


def primed(weapon_id):
    """A player holding `weapon_id` with a full ATK gauge and a full heavy charge."""
    p = Player(inventory=Inventory(right=weapon_id))
    p.stats.level = 99
    p.charge_hand = RIGHT
    p.charge_t = weapons.CHARGE_TIME
    return p


# --- data ----------------------------------------------------------------------------------------


def test_every_art_belongs_to_a_real_weapon_and_costs_mp():
    for item_id, art in weapons.ARTS.items():
        item = Items.ALL[item_id]
        assert item.kind == "weapon"
        assert weapons.art(item) is art
        assert art.mp > 0 and art.damage > 0
        assert art.kind in (weapons.CONE, weapons.BOLT, weapons.VOLLEY, weapons.RING, weapons.WAVE)
        assert (art.reach > 0) == (art.kind in (weapons.CONE, weapons.RING)), item_id
        assert len(art.rgb) == 3


def test_arts_are_unique_and_only_some_weapons_have_one():
    names = [a.name for a in weapons.ARTS.values()]
    assert len(set(names)) == len(names)
    assert weapons.art(Items.ALL["rusted_sword"]) is None
    assert weapons.art(Items.FISTS) is None
    assert weapons.art(None) is None


def test_the_ashblade_spills_fire_at_low_to_mid_range():
    art = weapons.art(Items.ALL["ashblade"])
    assert art.kind == weapons.CONE and art.element == "fire"
    assert 3.2 < art.reach <= 5.0  # past Pyre's reach, short of a bolt


# --- when an art is ready ------------------------------------------------------------------------


def test_an_art_is_ready_only_with_both_bars_full_and_the_mp():
    p = primed("ashblade")
    assert p.art_ready() is weapons.ARTS["ashblade"]
    p.gauge(RIGHT).value = 0.9
    assert p.art_ready() is None, "the ATK gauge must be full"
    p = primed("ashblade")
    p.charge_t = weapons.CHARGE_TIME * 0.9
    assert p.art_ready() is None, "the heavy must be charged"
    p = primed("ashblade")
    p.stats.mp = weapons.ARTS["ashblade"].mp - 1
    assert p.art_ready() is None and p.art_primed() is not None, "primed, but short of MP"
    p = primed("ashblade")
    p.stamina.value = 0.01
    assert p.art_ready() is None, "too winded for the heavy"
    assert primed("rusted_sword").art_ready() is None


def test_releasing_a_ready_art_spends_its_mp_and_rides_on_the_heavy():
    p = primed("ashblade")
    mp = p.stats.mp
    a = p.start_swing(kind=weapons.HEAVY, art=True)
    assert a.kind == weapons.HEAVY
    assert p.swing_art is weapons.ARTS["ashblade"]
    assert p.stats.mp == mp - p.swing_art.mp


def test_a_plain_heavy_or_a_light_carries_no_art_and_spends_no_mp():
    p = primed("ashblade")
    mp = p.stats.mp
    p.start_swing(kind=weapons.HEAVY)  # not asked for: the button wasn't released as a heavy
    assert p.swing_art is None and p.stats.mp == mp
    p = primed("ashblade")
    p.start_swing(kind=weapons.LIGHT, art=True)
    assert p.swing_art is None and p.stats.mp == mp


def test_short_of_mp_the_art_comes_out_a_plain_heavy():
    p = primed("ashblade")
    p.stats.mp = 1
    a = p.start_swing(kind=weapons.HEAVY, art=True)
    assert a.kind == weapons.HEAVY and p.swing_art is None and p.stats.mp == 1


def test_a_secret_outranks_an_art():
    p = primed("slagbreaker")
    p.take_blow(5, 3, 0)  # a blow just landed: the hammer answers with its Aftershock
    p.charge_t = weapons.CHARGE_TIME
    mp = p.stats.mp
    a = p.start_swing(kind=weapons.HEAVY, art=True)
    assert a.kind == weapons.SECRET
    assert p.swing_art is None and p.stats.mp == mp


def test_the_next_swing_forgets_the_last_art():
    p = primed("ashblade")
    p.start_swing(kind=weapons.HEAVY, art=True)
    p.swing_t = None
    p.start_swing()
    assert p.swing_art is None


# --- the ATK bar ---------------------------------------------------------------------------------


def test_the_bar_shows_the_gauge_and_the_charge_on_their_own_rows():
    p = primed("rusted_sword")
    p.gauge(RIGHT).value = 0.5
    p.charge_t = weapons.CHARGE_TIME / 2
    bar = atk_bar.state(p, RIGHT)
    assert bar.gauge == 0.5 and bar.gauge_rgb == atk_bar.ATK_CHARGING_RGB
    assert bar.charge == pytest.approx(0.5) and bar.charge_rgb == atk_bar.HEAVY_RGB
    assert bar.glow == atk_bar.PLAIN


def test_the_bar_hides_the_charge_until_the_button_is_held():
    p = primed("rusted_sword")
    p.charge_t = 0.0
    bar = atk_bar.state(p, RIGHT)
    assert bar.charge == 0 and bar.gauge == 1 and bar.gauge_rgb == atk_bar.ATK_RGB
    p.charge_t = atk_bar.CHARGE_SHOW / 2  # a tap never flashes it
    assert atk_bar.state(p, RIGHT).charge == 0


def test_the_bar_pulses_for_a_heavy_and_burns_for_an_art():
    p = primed("rusted_sword")
    assert atk_bar.state(p, RIGHT).glow == atk_bar.HEAVY
    p = primed("ashblade")
    bar = atk_bar.state(p, RIGHT)
    assert bar.glow == atk_bar.ART and bar.art_rgb == weapons.ARTS["ashblade"].rgb
    assert bar.gauge == bar.charge == 1


def test_short_of_mp_the_bar_shows_a_plain_ready_heavy():
    p = primed("ashblade")
    p.stats.mp = 0
    assert atk_bar.state(p, RIGHT) == atk_bar.state(primed("rusted_sword"), RIGHT)


def test_the_bar_turns_winded_without_the_st_for_a_heavy():
    p = primed("ashblade")
    p.stamina.value = 0.01
    bar = atk_bar.state(p, RIGHT)
    assert bar.charge_rgb == atk_bar.WINDED_RGB and bar.glow == atk_bar.PLAIN


def test_the_bar_of_the_other_button_stays_quiet():
    p = Player(inventory=Inventory(right="ashblade", left="katana"))
    p.charge_hand, p.charge_t = RIGHT, weapons.CHARGE_TIME
    assert atk_bar.state(p, "left").charge == 0
    assert p.art_primed("left") is None


# --- what each art does in the world -------------------------------------------------------------


def test_ember_spill_burns_what_is_close_ahead_but_not_far_off():
    game, world = jungle((15, 31), yaw=0.0)
    near = foe(world, "mire_slime", (17, 31))  # 4 m ahead
    far = foe(world, "mire_slime", (18, 31))  # 6 m ahead
    art = weapons.ARTS["ashblade"]

    def burn(e):
        game.damage_enemy(e, 5)
        e.afflict("burn", *elements.WEAPON_BURN)

    assert world.flame_cone(art.reach, burn) == 1
    assert near.hp < near.type.hp and "burn" in near.status
    assert far.hp == far.type.hp
    (gout,) = world.gouts
    assert gout.reach == art.reach


def test_ember_spill_kindles_a_brazier_pyre_cannot_reach():
    def five_metres_off():
        game, world = jungle((15, 31), yaw=math.pi)
        brazier = prop(world, "brazier")
        game.player.x = brazier.x + 5.0
        return world, brazier

    world, brazier = five_metres_off()
    world.pyre(magic=4, gauge=1.0)
    assert not world.is_lit(brazier)
    world, brazier = five_metres_off()
    world.flame_cone(weapons.ARTS["ashblade"].reach, lambda e: None)
    assert world.is_lit(brazier)


def test_thorn_volley_fans_out_its_thorns():
    game, world = jungle((15, 31), yaw=0.0)
    art = weapons.ARTS["thornlash"]
    world.volley(7, art.count, art.spread, art.effect, art.rgb)
    shots_ = world.projectiles
    assert len(shots_) == art.count
    assert all(s.effect == "thorn" and not s.hostile and s.damage == 7 for s in shots_)
    headings = sorted(math.atan2(s.dz, s.dx) for s in shots_)
    assert headings[1] == pytest.approx(game.player.yaw, abs=1e-6)
    assert headings[2] - headings[1] == pytest.approx(art.spread)


def test_slag_burst_strikes_all_around_and_iron_shrugs_off_half():
    _, world = hold((11, 18))
    behind = foe(world, "mire_slime", (10, 18))
    hound = foe(world, "slag_hound", (11, 19))
    struck = world.slag_ring(lambda e: 8 * elements.mult(e.type, "fire"), 4.0)
    assert set(struck) == {behind, hound}
    assert behind.hp == behind.type.hp - 8
    assert "burn" in behind.status
    assert hound.type.fireproof and hound.hp == hound.type.hp - 4
    assert "burn" not in hound.status
    assert len(world.gouts) == SLAG_GOUTS
    assert all(abs(g.dy) < 0.1 for g in world.gouts), "the slag runs along the floor"


def test_thorn_volley_poisons_what_it_strikes():
    _game, world = jungle((15, 31), yaw=0.0)
    husk = foe(world, "bark_husk", (17, 31))
    art = weapons.ARTS["thornlash"]
    world.volley(1, art.count, art.spread, art.effect, art.rgb)
    for _ in range(60):
        world._update_projectiles(1 / 60)
    assert husk.afflicted == "poison"


def test_snare_blooms_spit_thorns():
    _game, world = jungle((15, 31), yaw=0.0)
    bloom = foe(world, "snare_bloom", (18, 31))
    world.enemy_fire(bloom)
    (thorn,) = world.projectiles
    assert thorn.effect == "thorn" and thorn.hostile


# --- the Moonless Tachi's Pale Crescent -----------------------------------------------------------


def test_the_pale_crescent_is_primed_and_paid_for_like_any_art_and_plays_as_a_draw():
    art = weapons.ARTS["moonless_tachi"]
    assert art.kind == weapons.WAVE and art.width > 2 and art.speed > 0 and art.life > 0
    p = primed("moonless_tachi")
    assert p.art_ready() is art
    mp = p.stats.mp
    a = p.start_swing(kind=weapons.HEAVY, art=True)
    assert p.swing_art is art and p.stats.mp == mp - art.mp
    assert a.kind == weapons.HEAVY and a.motion == "draw" and a.lunge == 0
    p = primed("moonless_tachi")  # without the art, the heavy is the reverse cut
    assert p.start_swing(kind=weapons.HEAVY).motion == "slash_left"


def _loose(world, art):
    return world.crescent_wave(9, art.width, art.speed, art.life, art.rgb, art.effect)


def _fly(world, seconds=1.0, dt=1 / 60):
    for _ in range(round(seconds / dt)):
        world._update_projectiles(dt)


def test_the_pale_crescent_cuts_through_a_line_of_foes_each_once():
    _game, world = jungle((15, 31), yaw=0.0)
    first = foe(world, "bark_husk", (17, 31))
    second = foe(world, "bark_husk", (19, 31))
    wide = foe(world, "bark_husk", (18, 31))
    wide.z += 1.0  # off its path, but within its breadth
    art = weapons.ARTS["moonless_tachi"]
    wave = _loose(world, art)
    assert wave.pierce and wave.width == art.width
    _fly(world)
    for e in (first, second, wide):
        assert e.hp == e.type.hp - 9, "struck once, and only once"
    assert len(wave.hit_ids) == 3
    assert not world.projectiles, "it fades after its flight"


def test_the_pale_crescent_misses_what_lies_beyond_its_breadth():
    _game, world = jungle((15, 31), yaw=0.0)
    aside = foe(world, "bark_husk", (17, 31))
    aside.z += 2.5
    _loose(world, weapons.ARTS["moonless_tachi"])
    _fly(world)
    assert aside.hp == aside.type.hp


def test_the_pale_crescent_dies_on_a_wall():
    _game, world = jungle((24, 31), yaw=0.0)  # the hollow's wall rises at tile 27
    beyond = foe(world, "bark_husk", (28, 31))
    wave = _loose(world, weapons.ARTS["moonless_tachi"])
    _fly(world, 0.6)
    assert wave not in world.projectiles
    assert beyond.hp == beyond.type.hp


def test_a_plain_bolt_still_stops_at_the_first_foe():
    _game, world = jungle((15, 31), yaw=0.0)
    first = foe(world, "bark_husk", (17, 31))
    second = foe(world, "bark_husk", (19, 31))
    world.fire_bolt(9)
    _fly(world)
    assert first.hp == first.type.hp - 9 and second.hp == second.type.hp


# --- the Vesper Moonbrand's Vesper Ray -----------------------------------------------------------


def test_the_vesper_ray_is_a_narrow_fast_piercing_beam_from_a_greatsword():
    art = weapons.ARTS["vesper_moonbrand"]
    tachi = weapons.ARTS["moonless_tachi"]
    assert art.kind == weapons.WAVE and art.effect == "moonray"
    assert art.width < tachi.width / 2 and art.speed > tachi.speed * 1.5
    assert art.speed * art.life > tachi.speed * tachi.life * 1.5  # it reaches well past the crescent
    item = Items.ALL["vesper_moonbrand"]
    assert item.two_handed and item.category == "greatsword"
    p = primed("vesper_moonbrand")
    assert p.art_ready() is art
    a = p.start_swing(kind=weapons.HEAVY, art=True)
    assert p.swing_art is art and a.kind == weapons.HEAVY


def test_the_vesper_ray_runs_through_a_line_of_foes_far_down_its_path():
    _game, world = jungle((15, 31), yaw=0.0)
    near = foe(world, "bark_husk", (17, 31))
    far = foe(world, "bark_husk", (22, 31))  # 14 m off: past the Pale Crescent's flight
    aside = foe(world, "bark_husk", (19, 31))
    aside.z += 1.5  # within a crescent's breadth, but wide of the ray
    ray = _loose(world, weapons.ARTS["vesper_moonbrand"])
    assert ray.pierce and ray.effect == "moonray"
    _fly(world)
    assert near.hp == near.type.hp - 9 and far.hp == far.type.hp - 9
    assert aside.hp == aside.type.hp
    assert not world.projectiles
