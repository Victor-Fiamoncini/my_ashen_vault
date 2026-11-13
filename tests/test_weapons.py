import math
import os
import random
from types import SimpleNamespace

from ashen_vault import MAP_DIR
from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player import weapons
from ashen_vault.player.combat import Combat
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.world import World


def armed(weapon_id, level=99):
    p = Player(inventory=Inventory(right=weapon_id))
    p.stats.level = level
    return p


ALL_WEAPONS = [i for i in Items.ALL.values() if i.kind == "weapon"] + [Items.FISTS]


def test_every_weapon_has_light_heavy_and_quick_attacks_that_cost_stamina():
    assert len(ALL_WEAPONS) >= 17
    for item in ALL_WEAPONS:
        assert item.category in weapons.CATEGORY_NAMES, item.id
        assert item.category in weapons.TEMPO, item.id
        light = weapons.attack(item)
        heavy = weapons.attack(item, weapons.HEAVY)
        quick = weapons.attack(item, weapons.QUICK)
        assert (light.kind, heavy.kind, quick.kind) == ("light", "heavy", "quick")
        assert not light.heavy and heavy.heavy, item.id
        assert heavy.damage > light.damage or heavy.targets > light.targets or heavy.cone < 0
        assert 0 < quick.stamina <= light.stamina < heavy.stamina, item.id
        assert quick.time < light.time < heavy.time, item.id
        assert quick.min_power > 0


def test_bigger_weapons_swing_slower():
    p_katana, p_sword, p_zwei = armed("katana"), armed("rusted_sword"), armed("zweihander")
    for p in (p_katana, p_sword, p_zwei):
        assert p.start_swing()
    assert p_katana.swing_time < p_sword.swing_time < p_zwei.swing_time
    assert weapons.tempo(Items.get("nodachi")) > weapons.tempo(Items.get("katana"))


def test_heavy_swing_spends_stamina_and_lasts_longer():
    p = armed("claymore")
    light = armed("claymore")
    assert p.start_swing(kind=weapons.HEAVY).name == "Overhead cleave"
    assert math.isclose(p.stamina.value, 1 - p.attack.stamina)
    light.start_swing()
    assert light.stamina.value < 1.0, "light attacks cost stamina too"
    assert p.swing_time > light.swing_time
    assert p.swing_hit_at > light.swing_hit_at


def test_winded_heavy_falls_back_to_light_and_exhaustion_stops_swings():
    p = armed("war_hammer")
    p.stamina.value = 0.2  # a ground slam costs more than that
    assert not p.can_heavy()
    assert p.start_swing(kind=weapons.HEAVY).name == "Smash"
    assert p.stamina.value < 0.2
    tired = armed("rusted_sword")
    tired.stamina.drain(99)
    assert tired.stamina.exhausted
    assert tired.start_swing() is None


def test_sprint_drains_slower_than_before():
    from ashen_vault.player.combat import Stamina

    assert Stamina.DRAIN_TIME >= 5.0


def test_click_again_mid_swing_chains_a_quick_strike():
    p = armed("rusted_sword")
    p.start_swing()
    assert p.queue_quick("right")
    assert not p.queue_quick("left"), "only the swinging hand chains"
    assert p.chain_quick() is None, "not before the blow has landed"
    while p.swing_t < p.swing_time * Player.QUICK_FROM:
        p.update_timers(0.01)
    quick = p.chain_quick()
    assert quick is not None and quick.kind == "quick"
    assert p.swing_power >= quick.min_power
    assert not p.queue_quick("right"), "a quick strike doesn't chain again"


def test_hit_stop_holds_the_swing():
    p = armed("war_hammer")
    p.start_swing()
    p.update_timers(0.1)
    t = p.swing_t
    p.land_hit(object())
    p.update_timers(0.01)
    assert p.swing_t == t


def ctx(**kw):
    return weapons.Context(**kw)


def test_secret_attacks_need_their_moment():
    katana, whip, axe, club, hammer, sword = (
        Items.get(i)
        for i in ("katana", "leather_whip", "felling_axe", "oak_cudgel", "war_hammer", "ashblade")
    )
    H, L = weapons.HEAVY, weapons.LIGHT
    assert weapons.secret(katana, H, ctx(charge_t=1.3, still_t=2.0)).name == "Sheathed Draw"
    assert weapons.secret(katana, H, ctx(charge_t=1.3, still_t=0.5)) is None, "moved during the draw"
    assert weapons.secret(katana, H, ctx(charge_t=0.5, still_t=2.0)) is None
    assert weapons.secret(whip, H, ctx(sprinting=True, since_sprint=0)).name == "Snare"
    assert weapons.secret(whip, H, ctx()) is None
    assert weapons.secret(axe, H, ctx(since_sprint=0.3)).name == "Leaping Hew"
    assert weapons.secret(axe, H, ctx(since_sprint=1.0)) is None
    assert weapons.secret(club, L, ctx(combo=2)).name == "Skull-ringer"
    assert weapons.secret(club, L, ctx(combo=1)) is None
    assert weapons.secret(club, H, ctx(combo=5)) is None
    assert weapons.secret(hammer, H, ctx(since_hit=0.5)).name == "Aftershock"
    assert weapons.secret(hammer, H, ctx()) is None
    assert weapons.secret(sword, H, ctx(sprinting=True, since_hit=0, charge_t=5, still_t=9)) is None
    for item in ALL_WEAPONS:
        if weapons.has_secret(item):
            s = weapons.attack(item, weapons.SECRET)
            assert s.kind == "secret" and s.heavy and s.stamina > 0


def test_player_unleashes_the_club_secret_on_the_third_blow():
    p = armed("oak_cudgel")
    foe = object()
    for _ in range(2):
        p.start_swing()
        p.land_hit(foe)
        p.swing_t = None
        p.stamina.fill()
    assert p.start_swing().name == "Skull-ringer"
    assert p.combo_n == 0


def test_hammer_answers_a_blow_with_the_aftershock():
    p = armed("war_hammer")
    p.charge_t = weapons.CHARGE_TIME
    assert p.start_swing(kind=weapons.HEAVY).name == "Ground slam"
    p.swing_t = None
    p.stamina.fill()
    p.take_blow(5, 3, 0)
    p.charge_t = weapons.CHARGE_TIME
    assert p.start_swing(kind=weapons.HEAVY).name == "Aftershock"


def test_shields_and_spells_never_swing():
    p = Player(inventory=Inventory(right="rusted_sword"))
    p.inventory.add("buckler")
    p.inventory.equip("buckler", "right")
    assert p.start_swing("right") is None
    assert p.start_swing("left") is None, "the left hand holds the spell"
    assert p.stamina.value == 1.0 and not p.swinging


def test_katana_draw_from_a_still_hold():
    p = armed("katana")
    p.update_timers(1.5)
    p.charge_t = 1.3
    assert p.start_swing(kind=weapons.HEAVY).name == "Sheathed Draw"


def test_damage_multiplier():
    base = Combat.damage(10, 4, 1.0, 0)
    assert Combat.damage(10, 4, 1.0, 0, mult=2.0) == base * 2


def test_heavy_blow_staggers_the_boss_when_a_light_one_does_not():
    boss = Enemy(EnemyTypes.get("ashen_warden"), 0, 0, rng=random.Random(1))
    boss.take_hit(10)
    assert boss.state != "hurt"
    boss.take_hit(10, poise_mult=2.0)
    assert boss.state == "hurt"


def fake_world(*enemy_xz):
    """Just enough of a World for melee_targets: the player at the origin facing +X."""
    enemies = [Enemy(EnemyTypes.get("bone_walker"), x, z, rng=random.Random(1)) for x, z in enemy_xz]
    player = Player()
    player.yaw = 0.0
    return SimpleNamespace(player=player, enemies=enemies, can_see=lambda *_: True)


def test_melee_cone_and_limit():
    w = fake_world((1.5, 0.0), (0.0, 1.6), (-1.5, 0.0), (1.8, 0.3))
    ahead = World.melee_targets(w, 2.0)
    assert ahead == [w.enemies[0], w.enemies[3]]
    assert World.melee_targets(w, 2.0, limit=1) == [w.enemies[0]]
    everywhere = World.melee_targets(w, 2.0, cone=-1)
    assert set(everywhere) == set(w.enemies)
    narrow = World.melee_targets(w, 2.0, cone=0.99)
    assert narrow == [w.enemies[0]]


def test_keep_has_the_new_weapon_chests():
    m = MapLoader.load_file(os.path.join(MAP_DIR, "sunken_keep.map"))
    items = {s.props.get("item") for s in m.entities if s.kind == "chest"}
    assert {"claymore", "war_hammer"} <= items
