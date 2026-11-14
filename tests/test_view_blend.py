"""The first-person arms' smoothing: cross-fades between poses and the sway behind the turning view."""

import math

import pytest

from ashen_vault.player import view_blend
from ashen_vault.player.view_blend import PoseBlend, Sway


def test_the_first_pose_is_drawn_as_it_is():
    b = PoseBlend()
    assert b.apply("idle", (1.0, 2.0), 0.0, 0.3) == (1.0, 2.0)
    assert not b.blending


def test_a_new_source_fades_in_from_the_pose_drawn_last_and_arrives_on_time():
    b = PoseBlend()
    b.apply("swing", (1.0,), 0.0, 0.1)
    first = b.apply("idle", (0.0,), 1 / 60, 0.3)[0]
    assert 0.0 < first < 1.0  # on its way already, not stalled for a frame
    mid = b.apply("idle", (0.0,), 0.15, 0.3)[0]
    assert 0.0 < mid < first
    assert b.apply("idle", (0.0,), 0.4, 0.3) == (0.0,)
    assert not b.blending


def test_a_moving_target_is_followed_through_the_fade():
    b = PoseBlend()
    b.apply("idle", (0.0,), 0.0, 0.1)
    for i in range(1, 20):  # the new pose itself moves while the fade runs
        out = b.apply(("swing", 1), (i * 0.1,), i / 60, 0.1)[0]
    assert out == pytest.approx(1.9)


def test_the_same_key_never_restarts_the_fade_and_a_new_key_always_does():
    b = PoseBlend()
    b.apply(("swing", 1), (1.0,), 0.0, 0.1)
    b.apply(("swing", 1), (0.5,), 0.02, 0.1)
    assert not b.blending
    b.apply(("swing", 2), (0.0,), 0.04, 0.1)  # a double-click restarts the swing: a new swing id
    assert b.blending


def test_a_clock_that_goes_back_ends_the_fade():
    b = PoseBlend()
    b.apply("a", (1.0,), 5.0, 0.3)
    b.apply("b", (0.0,), 5.02, 0.3)
    assert b.apply("b", (0.0,), 0.0, 0.3) == (0.0,)


def test_the_arms_trail_a_turn_within_reason_and_catch_up():
    s = Sway()
    assert s.update(0.0, 0.0, 0.0) == (0.0, 0.0)
    yaw = 0.0
    for i in range(1, 30):  # a fast turn to the right
        yaw += 0.1
        lag, _ = s.update(yaw, 0.0, i / 60)
        assert -view_blend.SWAY_MAX <= lag <= 0.0
    assert lag == pytest.approx(-view_blend.SWAY_MAX)
    for i in range(30, 120):  # held still: it settles back
        lag, _ = s.update(yaw, 0.0, i / 60)
    assert abs(lag) < 1e-3


def test_sway_wraps_round_the_compass_and_ignores_pauses():
    s = Sway()
    s.update(math.pi - 0.01, 0.0, 0.0)
    lag, _ = s.update(-math.pi + 0.01, 0.0, 1 / 60)  # a small turn across the seam
    assert abs(lag) < 0.02
    assert s.update(2.0, 0.5, 5.0) == (0.0, 0.0)  # a long gap (a menu, a load): start afresh
