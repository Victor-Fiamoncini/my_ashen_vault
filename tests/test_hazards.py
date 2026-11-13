import math

import pytest

from ashen_vault.world.hazards import HIT_COOLDOWN, CrumbleFloor, Pendulum, SpikeTrap
from ashen_vault.world.tile_map import Tile, TileMap


def run(trap, seconds, step=1 / 60):
    for _ in range(round(seconds / step)):
        trap.update(step)


def test_spike_cycle_goes_down_warn_up():
    s = SpikeTrap(2, 3)
    assert s.state == "down"
    assert s.height == 0
    run(s, SpikeTrap.DOWN + 0.1)
    assert s.state == "warn"
    assert 0 < s.height < 0.5
    run(s, SpikeTrap.WARN)
    assert s.state == "up"
    run(s, SpikeTrap.RISE + 0.05)
    assert s.height == pytest.approx(1.0)
    run(s, SpikeTrap.UP)
    assert s.state == "down"


def test_spike_update_reports_springing_up_once():
    s = SpikeTrap(0, 0)
    sprung = 0
    for _ in range(round(SpikeTrap.PERIOD * 60)):
        sprung += s.update(1 / 60)
    assert sprung == 1


def test_spikes_only_hurt_when_up_and_on_the_tile():
    s = SpikeTrap(2, 3)
    x, z = TileMap.center(2, 3)
    assert s.hit(x, z) == 0  # down
    s.t = SpikeTrap.DOWN + 0.1
    assert s.hit(x, z) == 0  # warning only
    s.t = SpikeTrap.DOWN + SpikeTrap.WARN + 0.2
    assert s.hit(x + TileMap.TILE, z) == 0  # next tile over
    assert s.hit(x, z) == SpikeTrap.DAMAGE
    assert s.hit(x, z) == 0  # cooling down
    s.cooldown = 0
    assert s.hit(x, z) == SpikeTrap.DAMAGE


def test_spike_phase_offsets_the_cycle():
    assert SpikeTrap(0, 0, phase=SpikeTrap.DOWN + 0.5).state == "up"


def pendulum(axis="x", phase=0.0):
    return Pendulum(5, 5, axis=axis, pivot_y=4.4, length=3.3, floor=0.0, phase=phase)


def test_pendulum_swings_and_reports_lowest_point():
    p = pendulum()
    assert p.angle == pytest.approx(0)
    assert p.blade_bottom() == pytest.approx(4.4 - 3.3 - 0.3)
    p = pendulum(phase=0.3)  # start just past the bottom so the count isn't ambiguous
    passes = 0
    for _ in range(round(2 * math.pi / Pendulum.SPEED * 60)):  # one full period
        passes += p.update(1 / 60)
    assert passes == 2


def test_pendulum_hits_under_the_blade_and_pushes_along_the_swing():
    p = pendulum("x")
    x, z = TileMap.center(5, 5)
    dmg, dx, dz = p.hit(x, z)
    assert dmg == Pendulum.DAMAGE
    assert dx > 0  # moving toward +X at phase 0
    assert dz == 0
    assert p.hit(x, z) is None  # cooldown
    p.cooldown = 0
    p.t = math.pi / Pendulum.SPEED  # back at the bottom, now swinging the other way
    assert p.hit(x, z)[1] < 0


def test_pendulum_on_z_axis_pushes_along_z():
    p = pendulum("z")
    x, z = TileMap.center(5, 5)
    _, dx, dz = p.hit(x, z)
    assert dx == 0
    assert dz > 0


def test_pendulum_misses_when_high_or_away():
    p = pendulum()
    x, z = TileMap.center(5, 5)
    assert p.hit(x, z + TileMap.TILE) is None  # beside the corridor
    p.t = (math.pi / 2) / Pendulum.SPEED  # top of the swing
    assert p.blade_bottom() > 1.6
    assert p.hit(x + p.blade_offset(), z) is None


def test_hazard_cooldown_wears_off():
    p = pendulum()
    x, z = TileMap.center(5, 5)
    assert p.hit(x, z)
    p.update(HIT_COOLDOWN + 0.01)
    p.t = 0
    assert p.hit(x, z)


def crumble():
    pit = Tile(walkable=True, floor=-3.4, ceil=4.8, pit=True, floor_tex="dirt", wall_tex="stone_brick")
    return CrumbleFloor(2, 1, 1.6, pit)


def test_crumble_holds_until_stepped_on():
    c = crumble()
    assert c.update(5.0, player_on=False) is None
    assert c.state == "solid"
    assert c.rise == 1.0


def test_crumble_shakes_falls_and_reforms():
    c = crumble()
    assert c.update(0.01, player_on=True) == "shaking"
    assert 0 <= c.shake < 1
    assert c.update(CrumbleFloor.SHAKE, player_on=False) == "fallen"
    assert not c.standing
    c.update(0.2)
    assert c.drop > 0
    assert c.update(CrumbleFloor.GONE) == "solid"
    assert c.rise == pytest.approx(0.0)
    c.update(CrumbleFloor.REFORM)
    assert c.rise == pytest.approx(1.0)


def test_crumble_solid_tile_stands_in_for_the_pit():
    tile = crumble().solid_tile()
    assert tile.walkable
    assert not tile.pit
    assert tile.floor == pytest.approx(1.6)
    assert (tile.floor_tex, tile.wall_tex, tile.ceil) == ("dirt", "stone_brick", 4.8)
