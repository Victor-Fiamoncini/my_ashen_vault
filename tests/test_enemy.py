import math
import random

import pytest

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.world.map_loader import MapLoader
from conftest import ROOM, risen


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
        self.raged = 0
        self.slams = 0
        self.eruptions = 0
        self.hooks = []

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

    def boss_rage(self, _enemy):
        self.raged += 1

    def slam(self, _enemy):
        self.slams += 1

    def eruption(self, _enemy):
        self.eruptions += 1

    def hook(self, _enemy, mult, pull):
        self.hooks.append((mult, pull))


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
    boss = risen(Enemy(EnemyTypes.get("ashen_warden"), 0, 0))
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
    s = risen(Enemy(EnemyTypes.get("loom_mother"), x, z, rng=random.Random(seed)))
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


def warden(seed=3):
    w = risen(Enemy(EnemyTypes.get("ashen_warden"), 0.0, 0.0, rng=random.Random(seed)))
    w.cooldowns = dict.fromkeys(w.cooldowns, 0.0)
    return w


def test_warden_has_his_own_moves():
    t = EnemyTypes.get("ashen_warden")
    assert set(t.moves) == {"sweep", "pounce", "cinders", "combo", "slam"}
    assert t.phase_moves == ("eruption",) and t.rage
    assert "web" not in t.moves  # silk is the spider's


def only(boss, move):
    """Leaves just `move` ready to use."""
    boss.cooldowns = {m: (0.0 if m == move else 99.0) for m in boss.cooldowns}
    boss._rng = random.Random(0)
    boss._rng.random = lambda: 0.9  # never skip a close-range special for a plain blow
    return boss


def test_warden_combo_strikes_three_times_up_close():
    boss = only(warden(), "combo")
    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(boss, world, 0.1)
    assert boss.attack_kind == "combo"
    tick(boss, world, 2.0)
    assert len(world.struck) == 3
    assert world.struck[2] > world.struck[0]  # the last cut hits hardest


def test_backing_out_of_a_combo_breaks_the_chain():
    boss = only(warden(), "combo")
    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(boss, world, 0.75)  # through the windup: the first cut lands
    world.player_x = 6.0  # step back out of reach
    tick(boss, world, 1.5)
    assert len(world.struck) == 1


def test_circling_a_combo_dodges_the_later_cuts():
    boss = only(warden(), "combo")
    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(boss, world, 0.75)
    world.player_x, world.player_z = -2.0, 0.3  # duck round behind him
    tick(boss, world, 1.5)
    assert len(world.struck) < 3


def test_warden_slam_shakes_the_floor_and_hits_from_behind():
    boss = only(warden(), "slam")
    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(boss, world, 0.1)
    assert boss.attack_kind == "slam"
    world.player_x, world.player_z = -3.0, 0.0  # behind him, but inside the shockwave
    tick(boss, world, 1.3)
    assert world.slams == 1 and len(world.struck) == 1


def test_backing_off_a_slam_escapes_the_shockwave():
    boss = only(warden(), "slam")
    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(boss, world, 0.1)
    world.player_x = 5.0
    tick(boss, world, 1.3)
    assert world.slams == 1 and world.struck == []


def test_warden_kindles_his_rage_once_at_half_hp():
    boss = warden()
    boss.cooldowns = dict.fromkeys(boss.cooldowns, 99.0)
    world = FakeWorld(2.0, 0.0)
    boss.state = "chase"
    assert not boss.enraged and "eruption" not in boss.cooldowns
    boss.take_hit(boss.type.hp // 2 + 1, poise_mult=0)
    tick(boss, world, 2.0)
    assert world.raged == 1 and world.summoned == []
    assert boss.enraged and "eruption" in boss.cooldowns
    tick(boss, world, 3.0)
    assert world.raged == 1


def test_eruptions_only_come_in_the_second_phase():
    boss = warden()
    world = FakeWorld(6.0, 0.0)
    world.move_enemy = lambda *_: None
    boss.phase2 = True
    boss.cooldowns = dict.fromkeys(boss.cooldowns, 99.0)
    boss.cooldowns["eruption"] = 0.0
    tick(boss, world, 0.1)
    assert boss.attack_kind == "eruption"
    tick(boss, world, 1.5)
    assert world.eruptions == 1


def test_bosses_without_a_rage_or_brood_never_turn():
    m = Enemy(EnemyTypes.get("mimic"), 0, 0, rng=random.Random(1))
    m.state = "chase"
    m.take_hit(40, poise_mult=0)
    tick(m, FakeWorld(1.5, 0.0), 1.0)
    assert not m.enraged


def gaoler():
    g = Enemy(EnemyTypes.get("gaoler"), 0.0, 0.0, rng=random.Random(2))
    g.cooldowns = dict.fromkeys(g.cooldowns, 0.0)
    return g


def test_gaoler_hooks_you_from_mid_range():
    g = gaoler()
    world = FakeWorld(5.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(g, world, 0.1)
    assert g.attack_kind == "hook"
    tick(g, world, 1.2)
    assert world.hooks == [(0.4, 2.5)]


def test_gaoler_hook_misses_if_you_slip_aside():
    g = gaoler()
    world = FakeWorld(5.0, 0.0)
    world.move_enemy = lambda *_: None
    tick(g, world, 0.7)  # he has stopped turning to track you
    world.player_x, world.player_z = 0.0, 5.0  # sidestep far round as he throws
    tick(g, world, 0.8)
    assert world.hooks == []


def test_gaoler_clubs_you_up_close():
    g = gaoler()
    world = FakeWorld(1.8, 0.0)
    world.move_enemy = lambda *_: None
    tick(g, world, 1.5)
    assert world.hooks == [] and world.strikes == 1


def test_bone_crawler_lies_still_until_you_come_close():
    c = Enemy(EnemyTypes.get("bone_crawler"), 0.0, 0.0, rng=random.Random(1))
    world = FakeWorld(6.0, 0.0)
    tick(c, world, 2.0)
    assert c.state == "idle" and (c.x, c.z) == (0.0, 0.0)
    world.player_x = 2.5
    tick(c, world, 0.2)
    assert c.state in ("chase", "windup")


def test_warden_flings_embers_or_leaps_from_mid_range():
    seen = set()
    for seed in range(12):
        boss = warden(seed)
        world = FakeWorld(8.0, 0.0)
        world.move_enemy = lambda *_: None
        tick(boss, world, 0.1)
        seen.add(boss.attack_kind)
    assert seen == {"cinders", "pounce"}


def test_warden_ember_fan_is_fired_as_cinders():
    boss = warden()
    boss.cooldowns["pounce"] = 99
    world = FakeWorld(8.0, 0.0)
    tick(boss, world, 1.2)
    assert world.fired == ["cinders"]
    assert boss.cooldowns["cinders"] > 0


def test_warden_embers_need_a_line_of_sight():
    boss = warden()
    boss.cooldowns["pounce"] = 99
    world = FakeWorld(8.0, 0.0)
    world.visible = False
    boss._switch("chase")
    tick(boss, world, 0.3)
    assert boss.attack_kind != "cinders"


def test_boss_bar_trail_holds_then_drains_to_hp():
    from ashen_vault.ai.enemy import TRAIL_HOLD

    boss = Enemy(EnemyTypes.get("ashen_warden"), 0, 0, rng=random.Random(1))
    world = FakeWorld(30, 30)
    world.visible = False
    full = boss.type.hp
    boss.take_hit(30)
    assert boss.trail_hp == full
    boss.update(TRAIL_HOLD * 0.9, world)
    assert boss.trail_hp == full  # still holding
    for _ in range(200):
        boss.update(0.05, world)
    assert boss.trail_hp == boss.hp


def test_every_direct_blow_flashes_even_when_it_does_not_stagger():
    from ashen_vault.ai.enemy import FLASH_TIME

    boss = risen(Enemy(EnemyTypes.get("bellows"), 0, 0, rng=random.Random(0)))
    assert not boss.flashing
    boss.take_hit(1)  # far below its poise: no stagger, but the blow shows
    assert boss.state != "hurt" and boss.flashing
    tick(boss, FakeWorld(0, 30), FLASH_TIME + 0.05)
    assert not boss.flashing


def test_a_killing_blow_flashes_but_poison_and_fire_ticks_do_not():
    w = walker()
    w.take_hit(1, stagger=False)
    assert not w.flashing
    w.take_hit(w.hp)
    assert not w.alive and w.flashing


def test_a_boss_of_ash_waits_as_a_heap_untouchable_until_it_rises():
    from ashen_vault.ai.enemy import ASH_RISE

    world = FakeWorld(3, 0)  # no rise_time: it rises when it notices you
    for type_id in (
        "ashen_warden",
        "butcher",
        "loom_mother",
        "sexton",
        "rat_matron",
        "sodden_pall",
        "moon_duchess",
        "keystone",
    ):
        boss = Enemy(EnemyTypes.get(type_id), 0, 0, rng=random.Random(0))
        assert boss.state == "ashes" and boss.unseen and boss.rise_progress == 0.0
        assert not boss.take_hit(10_000) and boss.hp == boss.type.hp  # nothing to strike yet
        world.visible = False
        tick(boss, world, 1.0)
        assert boss.state == "ashes"
        world.visible = True
        boss.update(0.05, world)
        assert boss.state == "rising" and boss.rise_time == ASH_RISE
        tick(boss, world, ASH_RISE / 2)
        assert 0.3 < boss.rise_progress < 0.7
        assert not boss.take_hit(10_000) and boss.hp == boss.type.hp  # not whole yet
        tick(boss, world, ASH_RISE / 2 + 0.1)
        assert boss.state not in ("ashes", "rising") and boss.rise_progress == 1.0 and not boss.unseen


def test_the_world_says_when_a_heap_rises_and_how_fast():
    class Lair(FakeWorld):
        seconds = None

        def rise_time(self, _enemy):
            return self.seconds

    world = Lair(3, 0)
    boss = Enemy(EnemyTypes.get("sexton"), 0, 0, rng=random.Random(0))
    tick(boss, world, 1.0)
    assert boss.state == "ashes"  # it sees you, but you are not in its lair
    world.seconds = 1.5
    boss.update(0.05, world)
    assert boss.state == "rising" and boss.rise_time == 1.5


def test_a_boss_of_ash_rises_facing_you_and_turns_as_you_move():
    world = FakeWorld(0, 3)  # you stand to its south, not where its yaw points
    boss = Enemy(EnemyTypes.get("sexton"), 0, 0, yaw=0.0, rng=random.Random(0))
    boss.update(0.05, world)
    assert boss.state == "rising" and abs(boss.yaw - math.pi / 2) < 1e-6
    world.player_x, world.player_z = -3, 0  # you step round to its west while it forms
    tick(boss, world, 2.0)
    assert boss.state == "rising" and abs(abs(boss.yaw) - math.pi) < 0.05


def test_a_struck_statue_cracks_and_tears_free_before_it_fights():
    from ashen_vault.ai.enemy import STATUE_RISE

    boss = Enemy(EnemyTypes.get("brand"), 0, 0, rng=random.Random(0))
    assert boss.perched and boss.rise_progress == 0.0
    assert not boss.take_hit(5)
    assert boss.state == "rising" and boss.rise_time == STATUE_RISE
    tick(boss, FakeWorld(3, 0), STATUE_RISE + 0.1)
    assert boss.state not in ("perched", "rising")


def test_every_foe_is_made_of_a_known_material_with_its_own_hit_sound():
    from ashen_vault.ai.enemy_types import MATERIALS

    assert {t.material for t in EnemyTypes.ALL.values()} <= set(MATERIALS)
    walker = Enemy(EnemyTypes.get("bone_walker"), 0, 0)
    assert walker.hit_sound == "hit_bone"
    assert Enemy(EnemyTypes.get("forge_golem"), 0, 0).hit_sound == "hit_stone"
    assert Enemy(EnemyTypes.get("butcher"), 0, 0).hit_sound == "hit_flesh"


def test_an_iron_chest_mimic_rings_like_iron():
    assert Enemy(EnemyTypes.get("mimic"), 0, 0).hit_sound == "hit_wood"
    assert Enemy(EnemyTypes.get("mimic"), 0, 0, look="iron").hit_sound == "hit_iron"


# --- the sewers' bosses ------------------------------------------------------------------------------


class SewerWorld(FakeWorld):
    def __init__(self, px, pz):
        super().__init__(px, pz)
        self.moves = []
        self.room = True  # space for more of the Pall's clots

    def can_shed(self, _enemy):
        return self.room

    def __getattr__(self, name):
        if name in ("tail_lash", "squeal", "engulf", "shed", "burrow_burst"):
            return lambda _enemy: self.moves.append(name)
        raise AttributeError(name)


class SureRng(random.Random):
    """Never skips a close-range special for a plain blow."""

    def random(self):
        return 0.99


def sewer_boss(type_id, ready, phase2=False):
    """A sewer boss awake and facing +x, only `ready` off cooldown."""
    e = risen(Enemy(EnemyTypes.get(type_id), 0.0, 0.0, rng=SureRng()))
    e.state, e.yaw, e.phase2 = "chase", 0.0, phase2
    moves = set(e.type.moves) | (set(e.type.phase_moves) if phase2 else set())
    e.cooldowns = {m: 0.0 if m == ready else 99.0 for m in moves}
    return e


@pytest.mark.parametrize(
    ("type_id", "move", "near", "far", "phase2"),
    [
        ("rat_matron", "squeal", 3.0, 6.0, False),
        ("rat_matron", "burrow", 6.0, 11.0, False),
        ("rat_matron", "burrow", 6.0, 3.0, True),  # in both phases, but never from up close
        ("sodden_pall", "bile", 6.0, 13.0, False),
        ("sodden_pall", "engulf", 6.0, 14.0, True),
        ("sodden_pall", "shed", 6.0, 14.0, True),
    ],
)
def test_the_sewer_bosses_use_their_own_moves_at_their_own_range(type_id, move, near, far, phase2):
    e = sewer_boss(type_id, move, phase2)
    assert e._pick_move(SewerWorld(near, 0.0), near) == move
    e = sewer_boss(type_id, move, phase2)
    assert e._pick_move(SewerWorld(far, 0.0), far) is None


def test_their_second_phase_moves_wait_for_half_hp():
    for type_id, move in (("sodden_pall", "engulf"), ("sodden_pall", "shed")):
        e = risen(Enemy(EnemyTypes.get(type_id), 0.0, 0.0))
        assert move not in e.cooldowns  # not its own until the second phase
        assert move in e.type.phase_moves


def test_the_palls_engulf_lurches_through_where_you_stood_and_flows_over_you_once():
    def surge(dodge):
        e = sewer_boss("sodden_pall", "engulf", phase2=True)
        e.cooldowns["engulf"] = 99.0  # just the one
        w = SewerWorld(5.0, 0.0)
        e._begin_windup("engulf")
        while e.state == "windup":
            tick(e, w, 0.05)
        if dodge:
            w.player_z = 4.0  # stepped aside as it surged
        while e.state == "attack":
            tick(e, w, 0.05)
        return e, w

    e, w = surge(dodge=False)
    assert w.moves == ["engulf"]  # once, however long it passes over you
    assert e.x > 5.0  # it lurched on past where you stood
    e, w = surge(dodge=True)
    assert w.moves == [] and e.x > 5.0


def test_a_tail_lash_strikes_through_the_world_once_it_lands():
    e = sewer_boss("rat_matron", "tail_lash")
    w = SewerWorld(-2.0, 0.0)  # behind her
    tick(e, w, 1.0)
    assert w.moves == ["tail_lash"] and e.yaw == 0.0
    e = sewer_boss("rat_matron", "tail_lash")
    w = SewerWorld(2.0, 0.0)  # in front of her
    tick(e, w, 0.3)
    assert "tail_lash" not in w.moves


def test_she_burrows_out_of_reach_after_you_and_bursts_up_no_faster_than_her_cap():
    from ashen_vault.ai.enemy import BURROW_SPEED, BURROW_TIME, BURST_TIME

    e = sewer_boss("rat_matron", "burrow")
    e.cooldowns["burrow"] = 99.0
    w = SewerWorld(6.0, 0.0)
    e._begin_windup("burrow")
    while e.state == "windup":
        tick(e, w, 0.05)
    assert e.state == "attack" and e.burrowed and e.unseen
    hp = e.hp
    assert e.take_hit(50) is False and e.hp == hp  # nothing reaches her under the muck
    start = e.x
    w.player_z = 1.0  # you move: she tunnels after where you are now
    tick(e, w, BURROW_TIME - 0.1)
    assert e.burrowed and w.moves == []
    tick(e, w, 0.2)
    assert not e.burrowed and w.moves == ["burrow_burst"]  # once she surfaces
    cap = e.type.speed * BURROW_SPEED * BURROW_TIME
    travelled = math.hypot(e.x - start, e.z)
    assert 0.5 * cap < travelled <= cap + 1e-6
    assert e.z > 0  # she turned after you
    assert e.take_hit(1) is False and e.hp == hp - 1  # back in reach as she rears
    tick(e, w, BURST_TIME)
    assert e.state == "recover" and w.moves == ["burrow_burst"]


def test_the_sewer_bosses_moves_reach_the_world():
    for type_id, move in (
        ("rat_matron", "squeal"),
        ("sodden_pall", "engulf"),
        ("sodden_pall", "shed"),
    ):
        e = sewer_boss(type_id, move, phase2=move in ("engulf", "shed"))
        w = SewerWorld(3.0, 0.0)
        e._begin_windup(move)
        tick(e, w, 2.0)
        assert move in w.moves, move
    e = sewer_boss("sodden_pall", "shed", phase2=True)
    w = SewerWorld(3.0, 0.0)
    w.room = False  # four of its clots already crawl: it holds the rest in
    assert e._pick_move(w, 3.0) is None
    e = sewer_boss("sodden_pall", "bile")
    w = SewerWorld(6.0, 0.0)
    e._begin_windup("bile")
    tick(e, w, 2.0)
    assert "bile" in w.fired


# --- Vesperholm -----------------------------------------------------------------------------------


class MoonWorld(SewerWorld):
    def __getattr__(self, name):
        if name in ("moonbeam", "moonfall", "blink"):
            return lambda _enemy: self.moves.append(name)
        raise AttributeError(name)


@pytest.mark.parametrize(
    ("type_id", "move", "near", "far", "phase2"),
    [
        ("lantern_wraith", "frost_lance", 6.0, 13.0, False),
        ("veiled_knight", "blink", 6.0, 11.0, False),
        ("moon_duchess", "frost_lance", 6.0, 13.0, False),
        ("moon_duchess", "moonbeam", 6.0, 13.0, False),
        ("moon_duchess", "blink", 6.0, 11.0, True),
        ("moon_duchess", "moonfall", 6.0, 13.0, True),
    ],
)
def test_vesperholms_dead_use_their_own_moves_at_their_own_range(type_id, move, near, far, phase2):
    e = sewer_boss(type_id, move, phase2)
    assert e._pick_move(MoonWorld(near, 0.0), near) == move
    e = sewer_boss(type_id, move, phase2)
    assert e._pick_move(MoonWorld(far, 0.0), far) is None


def test_the_duchess_calls_down_the_moon_and_throws_her_lances_through_the_world():
    e = sewer_boss("moon_duchess", "moonbeam")
    w = MoonWorld(6.0, 0.0)
    e._begin_windup("moonbeam")
    for _ in range(40):
        tick(e, w, 0.05)
    assert w.moves == ["moonbeam"]
    e = sewer_boss("moon_duchess", "frost_lance")
    e._begin_windup("frost_lance")
    for _ in range(40):
        tick(e, w, 0.05)
    assert w.fired == ["frost_lance"]


def test_a_blink_ends_in_a_blow_wound_up_where_it_steps_out():
    e = sewer_boss("veiled_knight", "blink")
    w = MoonWorld(6.0, 0.0)
    e._begin_windup("blink")
    while e.attack_kind == "blink":
        tick(e, w, 0.05)
    assert w.moves == ["blink"] and e.state == "windup" and e.attack_kind == "melee"


# --- tempo -------------------------------------------------------------------------------------------


def test_tempo_quickens_windups_recovers_cooldowns_and_combos():
    import dataclasses

    from ashen_vault.ai.enemy import COMBO_GAP, MIN_WINDUP, MOVES

    base = EnemyTypes.get("ashen_warden")
    quick = dataclasses.replace(base, tempo=0.5)
    slow_e, quick_e = Enemy(base, 0.0, 0.0), Enemy(quick, 0.0, 0.0)
    for e in (slow_e, quick_e):
        e.attack_kind = "slam"
    assert slow_e.windup_time == MOVES["slam"][0]  # tempo 1 keeps its own times
    assert quick_e.windup_time == pytest.approx(MOVES["slam"][0] * 0.5)
    assert quick_e.recover_time == pytest.approx(base.recover * 0.5)
    assert quick_e.combo_gap == pytest.approx(COMBO_GAP * 0.5)
    assert quick_e._cooldown("slam") == pytest.approx(MOVES["slam"][1] * 0.5)
    slow_e.phase2 = True
    assert slow_e.windup_time == pytest.approx(MOVES["slam"][0] * 0.8)
    assert slow_e._cooldown("slam") == pytest.approx(MOVES["slam"][1] * 0.7)
    blur = Enemy(dataclasses.replace(base, tempo=0.1), 0.0, 0.0)
    blur.attack_kind = "slam"
    assert blur.windup_time == MIN_WINDUP, "never too quick to read"
    rat = Enemy(dataclasses.replace(EnemyTypes.get("sewer_rat"), tempo=0.5), 0.0, 0.0)
    rat.attack_kind = "melee"
    assert rat.windup_time == rat.type.windup, "a windup already under the floor is left alone"


def test_a_quick_boss_strikes_sooner():
    import dataclasses

    world = FakeWorld(2.0, 0.0)
    world.move_enemy = lambda *_: None
    plain = only(warden(), "combo")
    quick = only(
        risen(Enemy(dataclasses.replace(EnemyTypes.get("ashen_warden"), tempo=0.6), 0.0, 0.0)), "combo"
    )
    quick.cooldowns = {m: (0.0 if m == "combo" else 99.0) for m in quick.cooldowns}
    tick(plain, world, 0.6)
    quick_world = FakeWorld(2.0, 0.0)
    quick_world.move_enemy = lambda *_: None
    tick(quick, quick_world, 0.6)
    assert len(quick_world.struck) > len(world.struck)


# --- Old Harrowmere ------------------------------------------------------------------------------


class BellWorld(FakeWorld):
    def __init__(self, px, pz, sleepers=True):
        super().__init__(px, pz)
        self.sleepers = sleepers
        self.tolls = 0
        self.quakes = 0

    def can_toll(self, _enemy):
        return self.sleepers

    def toll(self, _enemy):
        self.tolls += 1

    def quake(self, _enemy):
        self.quakes += 1


def _awake(type_id, x=0.0):
    e = Enemy(EnemyTypes.get(type_id), x, 0, rng=random.Random(0))
    e.state = "chase"
    return e


def test_a_sexton_rings_its_bell_only_with_sleepers_near_and_you_kept_off():
    from ashen_vault.ai.enemy import TOLL_RANGE

    sexton = _awake("sunken_sexton")
    sexton.cooldowns["toll"] = 0.0
    assert sexton._pick_move(BellWorld(TOLL_RANGE[0] + 1, 0, sleepers=False), TOLL_RANGE[0] + 1) is None
    assert sexton._pick_move(BellWorld(1.0, 0), 1.0) is None  # too close: it swings instead
    world = BellWorld(TOLL_RANGE[0] + 1, 0)
    assert sexton._pick_move(world, TOLL_RANGE[0] + 1) == "toll"
    sexton._begin_windup("toll")
    tick(sexton, world, 2.0)
    assert world.tolls == 1


def test_the_keystone_quakes_and_hurls_only_in_its_second_phase():
    keystone = _awake("keystone")
    assert "quake" not in keystone.cooldowns and "hurl" not in keystone.cooldowns
    world = BellWorld(10.0, 0)
    keystone.hp = keystone.type.hp // 2 - 1
    keystone.update(0.05, world)
    assert keystone.phase2 and {"quake", "hurl"} <= set(keystone.cooldowns)
    keystone.cooldowns = dict.fromkeys(keystone.cooldowns, 0.0)
    keystone.cooldowns["quake"] = 99.0
    assert keystone._pick_move(world, 10.0) == "hurl"
    keystone._switch("chase")
    keystone._begin_windup("hurl")
    tick(keystone, world, 2.0)
    assert world.fired == ["hurl"]
    keystone._switch("chase")
    keystone._begin_windup("quake")
    tick(keystone, world, 2.0)
    assert world.quakes == 1


def test_a_golem_stands_as_a_statue_until_you_come_close_or_strike_it():
    golem = Enemy(EnemyTypes.get("stone_golem"), 0, 0, rng=random.Random(0))
    assert golem.perched
    tick(golem, FakeWorld(12.0, 0), 1.0)
    assert golem.perched  # far off: it stays stone
    golem.update(0.05, FakeWorld(3.0, 0))
    assert golem.state == "rising"


def test_an_idle_foe_answers_the_bell():
    walker_ = walker()
    walker_.state = "idle"
    walker_.alert()
    assert walker_.state == "chase"
    walker_.alert()
    assert walker_.state == "chase"
