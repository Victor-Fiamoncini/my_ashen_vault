import math

import pytest

from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.player import Player
from ashen_vault.world import shots


def fly(pitch, target, floor=0.0, dist=3.0, steps=200):
    """Fire a bolt from the eye at `pitch` toward an enemy `dist` metres ahead; True if it strikes."""
    t = EnemyTypes.get(target)
    dx, dy, dz = shots.aim(0.0, pitch)
    x, y, z = 0.0, Player.EYE - shots.BOLT_DROP, 0.0
    span = shots.body_span(t, floor)
    dt = 1 / 60
    for _ in range(steps):
        x, y, z = x + dx * dt, y + dy * dt, z + dz * dt
        if y < floor:
            return False  # hit the ground first
        if shots.strikes(x, y, z, dist, 0.0, t.radius, span):
            return True
    return False


def test_aim_follows_yaw_and_pitch_at_constant_speed():
    dx, dy, dz = shots.aim(math.pi / 2, 0.0)
    assert dx == pytest.approx(0.0, abs=1e-9) and dy == 0.0 and dz == pytest.approx(shots.BOLT_SPEED)
    dx, dy, dz = shots.aim(0.0, -0.5)
    assert dy < 0 < dx
    assert math.hypot(dx, dy, dz) == pytest.approx(shots.BOLT_SPEED)


def test_a_level_bolt_sails_over_a_slime_but_looking_down_hits_it():
    assert not fly(0.0, "mire_slime")
    assert fly(-0.3, "mire_slime")


def test_a_level_bolt_hits_a_standing_foe_and_aiming_high_misses_it():
    assert fly(0.0, "bone_walker")
    assert not fly(0.8, "bone_walker")


def test_hovering_bodies_sit_around_their_hover_height():
    wisp = EnemyTypes.get("cinder_wisp")
    lo, hi = shots.body_span(wisp, 1.0)
    assert lo < 1.0 + wisp.hover < hi
    assert lo > 1.0  # nothing to hit at its feet
    assert fly(0.0, "cinder_wisp")


def test_a_raised_floor_lifts_the_body():
    slime = EnemyTypes.get("mire_slime")
    assert shots.body_span(slime, 1.0) == pytest.approx((1.0, 1.0 + slime.tall))
    assert fly(0.0, "mire_slime", floor=0.8)


def test_every_enemy_has_a_body_a_bolt_can_strike():
    for t in EnemyTypes.ALL.values():
        lo, hi = shots.body_span(t, 0.0)
        assert 0.0 <= lo < hi, t.id


def test_enemy_shots_drop_to_your_chest_from_a_ledge():
    dx, dy, dz = shots.toward(0.0, 3.0, 0.0, 4.0, 1.0, 0.0, 6.0)
    assert (dx, dz) == pytest.approx((6.0, 0.0))
    assert dy == pytest.approx(-3.0)  # 2 m down over 4 m across, at 6 m/s across


def test_spread_turns_a_shot_sideways_at_the_same_ground_speed():
    dx, _, dz = shots.toward(0.0, 1.0, 0.0, 5.0, 1.0, 0.0, 6.0, spread=0.28)
    assert dz > 0
    assert math.hypot(dx, dz) == pytest.approx(6.0)


def test_a_shot_at_your_feet_height_or_over_your_head_misses():
    span = shots.player_span(0.0)
    assert shots.strikes(0.2, 1.0, 0.0, 0.0, 0.0, shots.PLAYER_RADIUS, span)
    assert not shots.strikes(0.2, 2.3, 0.0, 0.0, 0.0, shots.PLAYER_RADIUS, span)
    assert not shots.strikes(0.7, 1.0, 0.0, 0.0, 0.0, shots.PLAYER_RADIUS, span)


def test_a_shot_straight_down_does_not_divide_by_zero():
    assert shots.toward(1.0, 3.0, 1.0, 1.0, 1.0, 1.0, 6.0)[1] == 0.0
