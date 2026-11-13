import random

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.world.map_loader import MapLoader


class FakeWorld:
    """Minimal world stub implementing the interface Enemy expects."""

    def __init__(self, px, pz):
        self.player_x = px
        self.player_z = pz
        self.visible = True
        self.strikes = 0
        self.shots = 0
        self.player_alive = True

    def can_see(self, *_):
        return self.visible

    def move_enemy(self, enemy, dx, dz):
        enemy.x += dx
        enemy.z += dz

    def enemy_strike(self, _enemy):
        self.strikes += 1

    def enemy_fire(self, _enemy):
        self.shots += 1


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
