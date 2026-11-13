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


def armed(weapon_id):
    return Player(inventory=Inventory(weapon=weapon_id))


def test_every_weapon_has_a_light_and_heavy_attack():
    weapons_ = [i for i in Items.ALL.values() if i.kind == "weapon"] + [Items.FISTS]
    assert len(weapons_) >= 10
    for item in weapons_:
        assert item.category in weapons.CATEGORY_NAMES, item.id
        light, heavy = weapons.moveset(item)
        assert weapons.attack(item) is light
        assert weapons.attack(item, heavy=True) is heavy
        assert not light.heavy and heavy.heavy, item.id
        assert heavy.damage > light.damage or heavy.targets > light.targets or heavy.cone < 0


def test_heavy_swing_spends_stamina_and_lasts_longer():
    p = armed("claymore")
    assert p.start_swing(heavy=True)
    assert p.attack.name == "Overhead cleave"
    assert math.isclose(p.stamina.value, 1 - p.attack.stamina)
    assert p.swing_time > Player.SWING_TIME
    assert p.swing_hit_at > Player.SWING_HIT_AT


def test_winded_heavy_falls_back_to_light():
    p = armed("war_hammer")
    p.stamina.value = 0.2  # a ground slam costs 0.5
    assert not p.can_heavy()
    assert p.start_swing(heavy=True)
    assert p.attack.name == "Smash"
    assert p.stamina.value == 0.2


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
