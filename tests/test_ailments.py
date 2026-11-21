"""Ailments foes build in the player: poison, bleed, rot and corrosion."""

import random

import pytest

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player import ailments
from ashen_vault.player.ailments import FULL, POISON_TIME, Ailments
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world.tile_map import TileMap
from test_prison_world import prison


def run(a, seconds, max_hp=100, dt=0.05):
    return sum(a.update(dt, max_hp) for _ in range(round(seconds / dt)))


def test_a_meter_takes_hold_only_when_full_and_then_empties():
    a = Ailments()
    assert not a.build("bleed", FULL - 1)
    assert a.building() == ["bleed"]
    assert a.build("bleed", 1)
    assert a.meters["bleed"] == 0
    assert a.building() == []


def test_meters_drain_when_left_alone():
    a = Ailments()
    a.build("bleed", 50)
    a.build("rot", 50)
    run(a, 2)
    assert a.meters["bleed"] < a.meters["rot"] < 50, "bleed drains fastest, rot slowest"
    run(a, 60)
    assert a.building() == []


def test_poison_lingers_bites_each_second_and_wears_off():
    a = Ailments()
    assert a.build("poison", FULL)
    assert a.poisoned and a.building() == ["poison"]
    assert not a.build("poison", FULL), "no further buildup while it lingers"
    lost = run(a, POISON_TIME + 1, max_hp=100)
    assert lost == ailments.poison_bite(100) * round(POISON_TIME / ailments.TICK)
    assert not a.poisoned


def test_poison_can_kill():
    p = Player()
    p.stats.hp = 1
    p.afflict("poison", FULL)
    p.stats.hurt(p.ailments.update(1.0, p.stats.max_hp))
    assert not p.alive


def test_toxic_lingers_bites_harder_than_poison_and_wears_off_sooner():
    a, b = Ailments(), Ailments()
    assert a.build("toxic", FULL) and b.build("poison", FULL)
    assert a.toxic and a.building() == ["toxic"]
    assert not a.build("toxic", FULL), "no further buildup while it lingers"
    assert ailments.TOXIC_TIME < POISON_TIME
    assert run(a, 5) > run(b, 5) * 2, "toxic bites much harder"
    lost = run(a, ailments.TOXIC_TIME, max_hp=100)
    assert lost == ailments.toxic_bite(100) * round((ailments.TOXIC_TIME - 5) / ailments.TICK)
    assert not a.toxic


def test_toxic_and_poison_take_hold_together_and_stack():
    a = Ailments()
    a.build("poison", FULL)
    a.build("toxic", FULL)
    assert a.building() == ["poison", "toxic"]
    assert run(a, 1) == ailments.poison_bite(100) + ailments.toxic_bite(100)
    a.clear("toxic")
    assert a.poisoned and not a.toxic


def test_toxic_halts_the_stamina_refill():
    p = Player()
    p.stamina.spend(0.8)
    before = p.stamina.value
    p.afflict("toxic", FULL)
    for _ in range(40):
        p.update_timers(0.05)
    assert p.stamina.value == pytest.approx(before)


def test_fenbane_purges_toxic_and_poison():
    p = Player()
    p.afflict("toxic", FULL)
    p.afflict("poison", FULL)
    for kind in Items.get("fenbane").cures:
        p.cure(kind)
    assert p.ailments.building() == []


def test_toxic_survives_a_save_and_old_saves_load_without_it(tmp_path):
    p = Player()
    p.afflict("toxic", FULL)
    s = SaveSystem(str(tmp_path / "save.json"))
    s.save("cinderhold", p, set())
    _, loaded, _ = s.load()
    assert loaded.ailments.toxic_t == pytest.approx(ailments.TOXIC_TIME)
    old = Ailments.from_h({"meters": {"poison": 10}, "poison_t": 3})
    assert not old.toxic and old.meters["toxic"] == 0


def test_poison_slows_the_stamina_refill():
    clean, sick = Player(), Player()
    for p in (clean, sick):
        p.stamina.spend(0.8)
    sick.afflict("poison", FULL)
    for _ in range(40):  # past the pause before ST starts refilling
        clean.update_timers(0.05)
        sick.update_timers(0.05)
    assert sick.stamina.value < clean.stamina.value


def test_rot_caps_hp_until_cured():
    p = Player()
    full = p.stats.max_hp
    assert p.afflict("rot", FULL)
    cap = ailments.rot_cap(full)
    assert p.stats.hp == cap < full, "HP above the cap is clipped"
    p.stats.heal(999)
    assert p.stats.hp == cap
    p.cure("rot")
    p.stats.heal(999)
    assert p.stats.hp == full


def test_revive_clears_every_ailment():
    p = Player()
    p.afflict("rot", FULL)
    p.afflict("poison", FULL)
    p.afflict("bleed", 40)
    p.revive()
    assert p.ailments.building() == []
    assert p.stats.hp == p.stats.max_hp


def test_corrosion_wears_everything_held_and_worn():
    p = Player(inventory=Inventory(right="rusted_sword", left="buckler", body="brigandine", hands=None))
    for id_ in ("rusted_sword", "buckler", "brigandine"):
        p.inventory.add(id_)
    p.corrode()
    for id_ in ("rusted_sword", "buckler", "brigandine"):
        assert p.inventory.durability(id_) == p.inventory.max_durability(id_) - ailments.CORRODE_WEAR


def test_cures_clear_their_ailment():
    for id_, kind in (
        ("bitter_root", "poison"),
        ("clotting_salve", "bleed"),
        ("grave_lily", "rot"),
        ("ember_draught", "frost"),
    ):
        assert Items.get(id_).cures == (kind,)
    assert set(Items.get("fenbane").cures) == {"toxic", "poison"}


def test_ailments_survive_a_save(tmp_path):
    p = Player()
    p.afflict("rot", FULL)
    p.afflict("bleed", 30)
    s = SaveSystem(str(tmp_path / "save.json"))
    s.save("abandoned_prison", p, set())
    _, loaded, _ = s.load()
    assert loaded.ailments.rotted
    assert loaded.ailments.meters["bleed"] == pytest.approx(30)
    assert loaded.stats.hp_cap < loaded.stats.max_hp


def test_old_saves_load_without_ailments():
    a = Ailments.from_h(None)
    assert a.building() == [] and not a.rotted


def test_a_butchers_blow_builds_bleed_and_bursts():
    game, world = prison()
    butcher = Enemy(EnemyTypes.get("butcher"), *TileMap.center(15, 20), rng=random.Random(1))
    game.player.stats.hp = game.player.stats.max_hp = 400
    while not any(src == "Bleeding" for _, src in game.wounds):
        world.enemy_strike(butcher)
    assert (ailments.bleed_burst(400), "Bleeding") in game.wounds
    assert "bleed" in game.sounds


def test_a_blocked_blow_builds_nothing():
    game, world = prison()
    world.strike_player(0, "Butcher", 0, 0, (("bleed", 40),))
    assert game.player.ailments.building() == []
    world.strike_player(5, "Butcher", 0, 0, (("bleed", 40),))
    assert game.player.ailments.building() == ["bleed"]


def test_corrosion_taking_hold_wears_gear_and_says_so():
    game, world = prison()
    p = game.player
    p.inventory.add("rusted_sword")
    p.inventory.equip("rusted_sword")
    assert world.afflict_player("corrosion", FULL)
    assert p.inventory.durability("rusted_sword") < p.inventory.max_durability("rusted_sword")
    assert any("Corrosion" in m for m in game.messages)


def test_foes_that_inflict_name_known_ailments():
    for t in EnemyTypes.ALL.values():
        for kind, amount in t.inflicts:
            assert kind in ailments.KINDS and 0 < amount < FULL, t.id
    assert {k for t in EnemyTypes.ALL.values() for k, _ in t.inflicts} == set(ailments.KINDS)


# --- frost -------------------------------------------------------------------------------------------


def test_frostbite_lingers_freezing_you_at_first_then_thaws():
    a = Ailments()
    assert a.build("frost", FULL)
    assert a.frostbitten and a.frozen and a.active("frost")
    assert a.share("frost") == 1.0
    assert not a.build("frost", FULL), "no more builds while it lingers"
    run(a, ailments.FREEZE_TIME + 0.1)
    assert a.frostbitten and not a.frozen
    assert a.share("frost") < 1.0
    run(a, ailments.FROST_TIME)
    assert not a.frostbitten and a.building() == []


def test_frostbite_bursts_for_a_share_of_max_hp():
    assert ailments.frostbite_burst(100) == 15
    assert ailments.frostbite_burst(1) == 1


def test_frostbite_slows_your_legs_and_your_stamina(room):
    p = Player()
    p.place(*TileMap.center(5, 5), 0.0, room)
    p.stamina.value = 0
    p.update_timers(1.0)
    plain = p.stamina.value
    q = Player()
    q.place(*TileMap.center(5, 5), 0.0, room)
    q.stamina.value = 0
    q.afflict("frost", FULL)
    q.update_timers(1.0)
    assert q.stamina.value == pytest.approx(plain * ailments.FROST_REFILL)


def test_frostbite_is_cured_and_saved(tmp_path):
    a = Ailments()
    a.build("frost", FULL)
    back = Ailments.from_h(a.to_h())
    assert back.frostbitten and back.frost_t == a.frost_t
    a.clear("frost")
    assert not a.frostbitten
    assert Ailments.from_h({"frost_t": 999}).frost_t == ailments.FROST_TIME


def test_nothing_shows_at_the_edges_of_a_clean_view():
    assert Ailments().borders() == {}
    assert ailments.border_tint({}) is None


def test_a_meter_still_building_shows_no_border():
    a = Ailments()
    a.build("poison", FULL - 1)
    assert a.borders() == {}


@pytest.mark.parametrize("kind", ["poison", "toxic", "rot", "frost"])
def test_a_lingering_ailment_shows_at_the_edges_while_it_lasts(kind):
    a = Ailments()
    a.build(kind, FULL)
    assert list(a.borders()) == [kind]
    a.clear(kind)
    assert a.borders() == {}


@pytest.mark.parametrize("kind", ailments.FLARES)
def test_a_one_off_ailment_flares_at_the_edges_then_fades(kind):
    a = Ailments()
    a.build(kind, FULL)
    assert a.border(kind) == 1.0
    run(a, ailments.FLARE_TIME / 2)
    assert 0 < a.border(kind) < 1
    run(a, ailments.FLARE_TIME)
    assert a.borders() == {}


def test_poisons_border_fades_over_its_last_seconds():
    a = Ailments()
    a.build("poison", FULL)
    run(a, POISON_TIME - ailments.POISON_FADE / 2)
    assert a.border("poison") == pytest.approx(0.5, abs=0.05)


def test_frostbite_shows_strongest_while_your_legs_are_frozen():
    a = Ailments()
    a.build("frost", FULL)
    assert a.border("frost") == 1.0
    run(a, ailments.FREEZE_TIME + 0.5)
    assert a.border("frost") == ailments.FROST_LINGER


def test_several_ailments_combine_and_a_cure_clears_every_border():
    a = Ailments()
    for kind in ("poison", "bleed", "rot"):
        a.build(kind, FULL)
    assert list(a.borders()) == ["poison", "bleed", "rot"]
    a.clear()
    assert a.borders() == {}


def test_the_shared_glow_mixes_the_ailments_colours():
    poison, bleed = ailments.KINDS["poison"].rgb, ailments.KINDS["bleed"].rgb
    assert ailments.border_tint({"poison": 0.5}) == (poison, 0.5)
    rgb, k = ailments.border_tint({"poison": 1.0, "bleed": 1.0})
    assert rgb == tuple(ailments.rround((p + b) / 2) for p, b in zip(poison, bleed, strict=True))
    assert k == 1.0
