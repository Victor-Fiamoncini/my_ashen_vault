import random

from ashen_vault.ai.enemy import BOSS_DEATH_TIME, DEATH_TIME, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.world.ash import ASH_RGB, EMBER_RGB, AshCloud, death_phases


def test_death_phases_bleach_then_crumble():
    assert death_phases(0.0) == (0.0, 0.0)
    ashen, dissolve = death_phases(0.1)
    assert 0 < ashen < 1 and dissolve == 0
    assert death_phases(0.3)[0] == 1.0
    assert death_phases(1.0) == (1.0, 1.0)
    assert death_phases(5.0) == (1.0, 1.0)
    assert death_phases(-1.0) == (0.0, 0.0)


def test_death_progress_and_boss_takes_longer():
    e = Enemy(EnemyTypes.get("bone_walker"), 0, 0)
    assert e.death_progress == 0.0
    e.take_hit(999)
    e.state_t = DEATH_TIME / 2
    assert e.death_progress == 0.5
    assert not e.gone
    e.state_t = DEATH_TIME + 0.01
    assert e.death_progress == 1.0
    assert e.gone

    boss = Enemy(EnemyTypes.get("ashen_warden"), 0, 0)
    boss.take_hit(9999)
    boss.state_t = DEATH_TIME + 0.01
    assert not boss.gone
    boss.state_t = BOSS_DEATH_TIME + 0.01
    assert boss.gone


def test_flakes_rise_and_fade_out():
    cloud = AshCloud(random.Random(3))
    cloud.emit(0.0, 1.0, 0.0, radius=0.5, count=20)
    assert len(cloud) == 20
    start = [f.y for f in cloud]
    cloud.update(0.5)
    assert all(f.y > y0 for f, y0 in zip(cloud, start, strict=True))
    assert all(0 < f.fade < 1 for f in cloud)
    for _ in range(40):
        cloud.update(0.1)
    assert len(cloud) == 0


def test_shed_waits_for_dissolve_and_stops_when_done():
    cloud = AshCloud(random.Random(1))
    cloud.shed(0, 0, 0, 0.5, 1.8, k=0.05, rate=100, dt=0.1)
    assert len(cloud) == 0
    cloud.shed(0, 0, 0, 0.5, 1.8, k=1.0, rate=100, dt=0.1)
    assert len(cloud) == 0
    cloud.shed(0, 0, 0, 0.5, 1.8, k=0.5, rate=100, dt=0.1)
    assert len(cloud) == 10
    # Flakes come off the crumbling front, which has moved down from the top of the body.
    assert all(f.y < 1.8 for f in cloud)


def test_fractional_rate_still_emits():
    cloud = AshCloud(random.Random(2))
    for _ in range(100):
        cloud.shed(0, 0, 0, 0.5, 1.8, k=0.5, rate=10, dt=0.01)
    assert 3 <= len(cloud) <= 20


def test_embers_cool_to_ash():
    cloud = AshCloud(random.Random(5))
    cloud.emit(0, 0, 0, 0.3, 50, ember_chance=1.0)
    f = cloud.flakes[0]
    assert f.rgb == EMBER_RGB
    f.life = 0.0
    assert f.rgb == ASH_RGB
    cloud.clear()
    cloud.emit(0, 0, 0, 0.3, 5, ember_chance=0.0)
    assert all(f.rgb == ASH_RGB for f in cloud)
