import math
import random

import pytest

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.world.map_loader import MapLoader
from conftest import ROOM


class FakeWorld:
    """Minimal world stub implementing the interface Enemy expects."""

    def __init__(self, px, pz):
        self.player_x = px
        self.player_z = pz
        self.visible = True
        self.strikes = 0
        self.shots = 0
        self.player_alive = True
        self.fired = []
        self.struck = []
        self.summoned = []

    def can_see(self, *_):
        return self.visible

    def move_enemy(self, enemy, dx, dz):
        enemy.x += dx
        enemy.z += dz

    def enemy_strike(self, _enemy, mult=1.0):
        self.strikes += 1
        self.struck.append(mult)

    def enemy_fire(self, _enemy, kind="shot"):
        self.shots += 1
        self.fired.append(kind)

    def summon(self, enemy, type_id, count):
        self.summoned.append((type_id, count))


def tick(enemy, world, seconds, dt=0.05):
    for _ in range(round(seconds / dt)):
        enemy.update(dt, world)


def walker(x=0.0, z=0.0):
    return Enemy(EnemyTypes.get("bone_walker"), x, z, rng=random.Random(1))


def test_notices_and_chases():
    e = walker()
    w = FakeWorld(8.0, 0.0)
    e.update(0.05, w)
    assert e.state == "chase"
    tick(e, w, 1.0)
    assert e.x > 1.0


def test_stays_idle_without_sight():
    e = walker()
    w = FakeWorld(5.0, 0.0)
    w.visible = False
    tick(e, w, 1.0)
    assert e.state == "idle"


def test_winds_up_then_strikes_once():
    e = walker()
    w = FakeWorld(1.0, 0.0)
    tick(e, w, 0.1)
    assert e.state == "windup"
    assert w.strikes == 0
    tick(e, w, 1.0)
    assert w.strikes == 1


def test_hit_staggers_and_interrupts_windup():
    e = walker()
    w = FakeWorld(1.0, 0.0)
    tick(e, w, 0.1)
    e.take_hit(3)
    assert e.state == "hurt"
    tick(e, w, 0.3)
    assert w.strikes == 0


def test_boss_has_poise():
    boss = Enemy(EnemyTypes.get("ashen_warden"), 0, 0)
    boss.take_hit(5)
    assert boss.state != "hurt"
    boss.take_hit(20)
    assert boss.state == "hurt"


def test_death():
    e = walker()
    assert e.take_hit(999)
    assert not e.alive
    tick(e, FakeWorld(1, 0), 2.0)
    assert not e.gone  # still crumbling to ash
    tick(e, FakeWorld(1, 0), 1.0)
    assert e.gone


def test_ranged_enemy_fires():
    e = Enemy(EnemyTypes.get("cinder_wisp"), 0, 0)
    w = FakeWorld(6.0, 0.0)
    tick(e, w, 1.5)
    assert w.shots == 1


BOSS_ROOM = """[meta]
name = Boss Room
start = 1 1 0

[legend]
# = wall tex=stone_brick top=3
. = floor h=0 ceil=3

[grid]
#####
#a.b#
#####

[entities]
a = bone_walker yaw=90
b = ashen_warden
"""


def test_spawn_enemies_respects_boss_rules():
    map_ = MapLoader(BOSS_ROOM, name="boss_room").parse()
    assert [e.type.id for e in spawn_enemies(map_, set())] == ["bone_walker", "ashen_warden"]
    assert [e.type.id for e in spawn_enemies(map_, {"boss_dead"})] == ["bone_walker"]
    fresh = spawn_enemies(map_, set(), bosses=False)
    assert [e.type.id for e in fresh] == ["bone_walker"]
    assert fresh[0].hp == fresh[0].type.hp
    assert fresh[0].alive


def mimic(x=0.0, z=0.0):
    return Enemy(EnemyTypes.get("mimic"), x, z, rng=random.Random(1))


def test_mimic_sleeps_as_a_chest_until_woken():
    m = mimic()
    world = FakeWorld(1.0, 0.0)  # right next to it, in plain sight
    tick(m, world, 3.0)
    assert m.dormant
    assert (m.x, m.z) == (0.0, 0.0)
    assert world.strikes == 0


def test_woken_mimic_bites_at_once():
    m = mimic()
    world = FakeWorld(0.0, 1.5)
    m.wake(world.player_x, world.player_z)
    assert m.state == "windup"
    assert m.yaw == pytest.approx(math.pi / 2)
    tick(m, world, m.type.windup + 0.1)
    assert world.strikes == 1


def test_striking_a_dormant_mimic_wakes_it():
    m = mimic()
    assert not m.take_hit(1)  # too light to stagger it, but it notices
    assert m.state == "chase"
    m2 = mimic()
    assert not m2.take_hit(30)
    assert m2.state == "hurt"


def test_slain_mimic_stays_dead_and_ambushers_spawn_dormant():
    text = ROOM.replace("a = bone_walker yaw=90", "a = mimic item=ringmail")
    m = MapLoader(text, name="room").parse()
    [e] = spawn_enemies(m, set())
    assert e.dormant
    assert e.loot == "ringmail"
    assert e.key == "slain:room:2,2"
    assert spawn_enemies(m, {"slain:room:2,2"}) == []


def bloom(x=0.0, z=0.0):
    return Enemy(EnemyTypes.get("snare_bloom"), x, z, rng=random.Random(2))


def test_rooted_bloom_never_moves():
    e = bloom()
    w = FakeWorld(30.0, 0.0)
    w.visible = False
    tick(e, w, 5.0)
    assert (e.x, e.z) == (0.0, 0.0)
    assert e.state == "idle"
    w.player_x = 6.0
    w.visible = True
    tick(e, w, 5.0)
    assert (e.x, e.z) == (0.0, 0.0)


def test_rooted_bloom_spits_at_range():
    e = bloom()
    w = FakeWorld(6.0, 0.0)
    tick(e, w, 1.2)
    assert w.shots == 1
    assert w.strikes == 0
    assert (e.x, e.z) == (0.0, 0.0)


def test_rooted_bloom_bites_up_close():
    e = bloom()
    w = FakeWorld(1.5, 0.0)
    tick(e, w, 1.2)
    assert w.strikes == 1
    assert w.shots == 0


def test_rooted_bloom_out_of_reach_just_watches():
    e = bloom()
    w = FakeWorld(12.0, 0.0)
    w.player_z = 0.0
    e.update(0.05, w)
    e._switch("chase")
    tick(e, w, 2.0)
    assert w.shots == 0 and w.strikes == 0
    assert (e.x, e.z) == (0.0, 0.0)
    assert e.state == "chase"


def test_bite_misses_when_player_steps_back():
    e = bloom()
    w = FakeWorld(1.5, 0.0)
    tick(e, w, 0.3)
    assert e.state == "windup" and e.attack_kind == "bite"
    w.player_x = 4.0
    tick(e, w, 1.0)
    assert w.strikes == 0


def test_bark_husk_is_slow_tanky_and_staggers_only_on_big_hits():
    husk = Enemy(EnemyTypes.get("bark_husk"), 0, 0)
    walker_type = EnemyTypes.get("bone_walker")
    assert husk.type.speed < walker_type.speed
    assert husk.type.hp > 2 * walker_type.hp
    husk.take_hit(5)
    assert husk.state != "hurt"
    husk.take_hit(12)
    assert husk.state == "hurt"


def test_new_enemy_types_have_sane_stats():
    for id_ in ("snare_bloom", "bark_husk", "stump_mimic", "loom_mother"):
        t = EnemyTypes.get(id_)
        assert t.hp > 0 and t.damage > 0 and t.exp > 0
        assert t.radius > 0 and t.height > 0
        assert t.windup > 0 and t.recover > 0
        assert len(t.gold) > 0
    bloom_t = EnemyTypes.get("snare_bloom")
    assert bloom_t.rooted and bloom_t.ranged and bloom_t.bite_reach < bloom_t.reach
    spider = EnemyTypes.get("loom_mother")
    warden = EnemyTypes.get("ashen_warden")
    assert spider.boss and spider.drop == "verdant_sigil" and spider.dead_flag == "spider_dead"
    assert spider.hp > warden.hp and spider.damage > warden.damage and spider.exp > warden.exp
    assert warden.dead_flag == "boss_dead" and warden.drop == "ember_sigil"
    assert spider.dead_flag != warden.dead_flag


TWO_BOSS_ROOM = BOSS_ROOM.replace("#a.b#", "#abc#").replace(
    "b = ashen_warden", "b = ashen_warden\nc = loom_mother"
)


def test_each_boss_is_suppressed_only_by_its_own_flag():
    map_ = MapLoader(TWO_BOSS_ROOM, name="two_bosses").parse()

    def ids(flags):
        return [e.type.id for e in spawn_enemies(map_, flags)]

    assert ids(set()) == ["bone_walker", "ashen_warden", "loom_mother"]
    assert ids({"boss_dead"}) == ["bone_walker", "loom_mother"]
    assert ids({"spider_dead"}) == ["bone_walker", "ashen_warden"]
    assert ids({"boss_dead", "spider_dead"}) == ["bone_walker"]


def test_bark_husk_turns_slowly_so_you_can_flank_it():
    husk = Enemy(EnemyTypes.get("bark_husk"), 0, 0, yaw=0.0)
    w = FakeWorld(-2.0, 0.0)  # right behind it
    tick(husk, w, 0.5)
    assert husk.state == "chase"
    # Half a second at its turn rate is nowhere near the half turn it needs to face you.
    assert abs(husk.yaw) < 1.0
    assert w.strikes == 0


def test_bark_husk_only_swings_once_it_faces_you():
    husk = Enemy(EnemyTypes.get("bark_husk"), 0, 0, yaw=math.pi)
    w = FakeWorld(2.0, 0.0)
    w.move_enemy = lambda *_: None
    tick(husk, w, 0.4)
    assert husk.state == "chase"
    tick(husk, w, 3.0)
    assert w.strikes >= 1


def test_blows_from_behind_hit_the_weak_spot():
    husk = Enemy(EnemyTypes.get("bark_husk"), 0, 0, yaw=0.0)  # facing +X
    assert husk.hit_mult(2.0, 0.0) == 1.0  # from the front
    assert husk.hit_mult(0.0, 2.0) == 1.0  # from the side
    assert husk.hit_mult(-2.0, 0.0) == husk.type.back_mult > 1
    assert walker().hit_mult(-2.0, 0.0) == 1.0


def test_stump_mimic_waits_until_you_are_close():
    mimic = Enemy(EnemyTypes.get("stump_mimic"), 0, 0)
    w = FakeWorld(4.0, 0.0)
    tick(mimic, w, 3.0)
    assert mimic.state == "idle" and (mimic.x, mimic.z) == (0, 0)
    w.player_x = 2.0
    tick(mimic, w, 0.1)
    assert mimic.state != "idle"
    # Once awake it keeps after you well past its tiny ambush range.
    w.player_x = 8.0
    tick(mimic, w, 0.5)
    assert mimic.state == "chase" and mimic.x > 0


def spider(x=0.0, z=0.0, seed=3):
    s = Enemy(EnemyTypes.get("loom_mother"), x, z, rng=random.Random(seed))
    s.cooldowns = dict.fromkeys(s.cooldowns, 0.0)
    return s


def test_spider_spits_web_or_pounces_from_mid_range():
    seen = set()
    for seed in range(12):
        s = spider(seed=seed)
        w = FakeWorld(8.0, 0.0)
        w.move_enemy = lambda *_: None
        tick(s, w, 0.1)
        seen.add(s.attack_kind)
    assert seen == {"web", "pounce"}


def test_web_shot_is_fired_as_web():
    s = spider()
    s.cooldowns["pounce"] = 99
    w = FakeWorld(8.0, 0.0)
    tick(s, w, 1.0)
    assert w.fired == ["web"]
    assert s.cooldowns["web"] > 0


def test_pounce_leaps_to_where_you_stood_and_lands_hard():
    s = spider()
    s.cooldowns["web"] = 99
    w = FakeWorld(7.0, 0.0)
    tick(s, w, 0.1)
    assert s.attack_kind == "pounce"
    tick(s, w, 1.3)
    assert s.x > 5.0
    assert w.struck and w.struck[0] > 1.0


def test_dodging_a_pounce_makes_it_miss():
    s = spider()
    s.cooldowns["web"] = 99
    w = FakeWorld(7.0, 0.0)
    tick(s, w, 0.75)  # it is about to spring
    w.player_z = 6.0  # side-step out of the way
    tick(s, w, 0.6)
    assert w.struck == []


def test_sweep_hits_you_even_from_behind():
    hits = 0
    for seed in range(10):
        s = spider(seed=seed)
        s.cooldowns.update(web=99, pounce=99)
        w = FakeWorld(2.0, 0.0)
        tick(s, w, 0.1)
        if s.attack_kind != "sweep":
            continue
        w.player_x, w.player_z = -3.5, 0.0  # slip round behind it during the windup
        tick(s, w, 1.3)
        hits += len(w.struck)
    assert hits > 0


def test_spider_calls_its_brood_once_at_half_hp():
    s = spider()
    s.cooldowns = dict.fromkeys(s.cooldowns, 99.0)
    w = FakeWorld(2.0, 0.0)
    s.state = "chase"
    s.take_hit(s.type.hp // 2 + 1, poise_mult=0)
    tick(s, w, 2.0)
    assert w.summoned == [("loom_brood", 2)]
    assert s.enraged
    tick(s, w, 3.0)
    assert len(w.summoned) == 1


def test_brood_is_small_fast_and_dies_with_its_mother():
    brood = EnemyTypes.get("loom_brood")
    mother = EnemyTypes.get("loom_mother")
    assert mother.brood == "loom_brood"
    assert brood.speed > mother.speed and brood.hp < 20 and not brood.boss
    child = Enemy(brood, 0, 0)
    child.kill()
    assert not child.alive and child.hp == 0
