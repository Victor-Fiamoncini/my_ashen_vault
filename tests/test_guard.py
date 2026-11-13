import math

import pytest

from ashen_vault.player import guard
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player

BUCKLER = Items.get("buckler")
TOWER = Items.get("tower_shield")


def test_shields_stop_frontal_blows_only():
    front = guard.block(20, 1.0, TOWER, 1.0)
    assert front.taken == 0 and front.stamina == pytest.approx(20 / TOWER.stability)
    assert front.blocked and not front.broken
    behind = guard.block(20, -1.0, TOWER, 1.0)
    assert behind.taken == 20 and behind.stamina == 0 and not behind.blocked


def test_bucklers_leak_and_cost_more_stamina_per_point():
    small = guard.block(20, 1.0, BUCKLER, 1.0)
    assert small.taken == 8
    assert small.stamina / (20 * BUCKLER.guard) > 1 / TOWER.stability


def test_guard_breaks_when_stamina_runs_out():
    b = guard.block(40, 1.0, BUCKLER, 0.1)
    assert b.broken and b.stamina == 0.1
    assert b.taken == 40 - 3


def test_facing_cos():
    assert guard.facing_cos(0, 0, 1, 0, 5, 0) == pytest.approx(1.0)
    assert guard.facing_cos(0, 0, 1, 0, -5, 0) == pytest.approx(-1.0)
    assert guard.facing_cos(0, 0, 1, 0, 0, 0) == 1.0


def shielded():
    inv = Inventory()
    inv.add("round_shield")
    inv.equip("round_shield")
    p = Player(inventory=inv)
    p.yaw = 0.0  # facing +X
    return p


def test_raised_shield_blocks_spends_stamina_and_slows_refill():
    p = shielded()
    assert p.take_blow(10, 3, 0) == (10, None), "not raised"
    assert p.since_hit == 0.0, "any blow readies the hammer's Aftershock"
    assert p.raise_guard(True)
    taken, block = p.take_blow(10, 3, 0)
    assert block.blocked and taken < 10 and p.stamina.value < 1.0
    assert p.since_block == 0.0
    p.stamina.value = 0.5
    p.stamina._rest_t = 99
    p.update_timers(0.5)
    guarded = p.stamina.value
    p.raise_guard(False)
    p.stamina.value = 0.5
    p.update_timers(0.5)
    assert guarded - 0.5 < (p.stamina.value - 0.5) / 2


def test_guard_break_lowers_the_shield_and_blocks_attacks():
    p = shielded()
    p.raise_guard(True)
    p.stamina.value = 0.01
    _, block = p.take_blow(50, 3, 0)
    assert block.broken and not p.guarding and p.guard_break_t > 0
    assert not p.raise_guard(True)
    assert p.start_swing() is None


def test_guarding_walks_slowly_without_sprinting(room):
    from ashen_vault.world.tile_map import TileMap

    x, z = TileMap.center(1, 2)
    a, b = shielded(), shielded()
    for p in (a, b):
        p.place(x, z, 0.0, room)
    b.raise_guard(True)
    a.walk(room, 1, 0, 0.1)
    b.walk(room, 1, 0, 0.1, sprint=True)
    assert not b.sprinting
    assert (b.x - x) == pytest.approx((a.x - x) * guard.WALK)


@pytest.mark.parametrize("fwd, strafe", [(-1, 0), (0, 1), (0, -1), (-1, 1)])
def test_guarding_walks_every_way(room, fwd, strafe):
    """A raised shield slows you but never pins you: back off and sidestep at guard.WALK pace."""
    from ashen_vault.world.tile_map import TileMap

    x, z = TileMap.center(1, 2)
    a, b = shielded(), shielded()
    for p in (a, b):
        p.place(x, z, 0.0, room)
    b.raise_guard(True)
    assert a.walk(room, fwd, strafe, 0.05)
    assert b.walk(room, fwd, strafe, 0.05)
    moved_a = math.hypot(a.x - x, a.z - z)
    moved_b = math.hypot(b.x - x, b.z - z)
    assert moved_b == pytest.approx(moved_a * guard.WALK)


def test_backpedal_and_strafe_outpace_most_foes(room):
    from ashen_vault.ai.enemy_types import EnemyTypes

    assert Player.BACK_SPEED >= 2.5
    fast = [t for t in EnemyTypes.ALL.values() if t.speed > Player.WALK_SPEED]
    assert len(fast) <= 1


def test_world_routes_blows_through_the_shield():
    from types import SimpleNamespace

    from ashen_vault.world.world import World

    events = []
    game = SimpleNamespace(
        blocked=lambda b: events.append(("block", b)), hurt_player=lambda d, s: events.append(d)
    )
    p = shielded()
    w = SimpleNamespace(player=p, game=game)
    World.strike_player(w, 10, "Bone", 3, 0)
    assert events == [10]
    events.clear()
    p.raise_guard(True)
    World.strike_player(w, 10, "Bone", 3, 0)
    assert events[0][0] == "block" and events[1:] == [3]  # a round shield stops 75%: 2.5 rounds up


def test_blows_from_behind_land_in_full_and_keep_the_shield_up():
    p = shielded()
    p.raise_guard(True)
    taken, block = p.take_blow(10, -3, 0)  # facing +X, struck from -X
    assert taken == 10 and not block.blocked and not block.broken
    assert p.guarding and p.stamina.value == 1.0
