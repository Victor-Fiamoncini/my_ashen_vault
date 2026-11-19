"""A lunging attack (the Katana's Lunging thrust, the axe's Leaping Hew) carries you forward over a few
frames, not in one jump: walls, fog and foes' bodies stop it short, and a blow cuts it off."""

import math

import pytest

from ashen_vault.player import weapons
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.player import Player
from ashen_vault.world import collision
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_prison_world import FakeGame

HALL = """[meta]
name = Hall
start = 1 1 0

[legend]
# = wall tex=stone_brick top=3
. = floor h=0 ceil=3

[grid]
##########
#........#
##########
"""

DT = 1 / 60


def hall():
    return MapLoader(HALL, name="hall").parse()


def lunger(map_, tx=2, weapon="katana"):
    """A player in the hall holding `weapon`, facing +x down it, who has just started a heavy."""
    p = Player(inventory=Inventory(right=weapon))
    p.stats.level = 99
    x, z = TileMap.center(tx, 1)
    p.place(x, z, 0.0, map_)
    a = p.start_swing(kind=weapons.HEAVY, secrets=False)
    assert a.lunge > 0
    return p


def swing_through(p, map_, blocked=None, bodies=()):
    """Plays the swing out frame by frame; returns each frame's step."""
    steps = []
    while p.swinging:
        p.update_timers(DT)
        steps.append(p.step_lunge(map_, DT, blocked=blocked, bodies=bodies))
    return steps


def test_the_katana_lunge_is_spread_over_several_frames():
    m = hall()
    p = lunger(m)
    x0 = p.x
    steps = swing_through(p, m)
    moving = [s for s in steps if s > 0]
    assert len(moving) >= 5
    assert max(steps) <= 0.15
    assert p.x - x0 == pytest.approx(1.0, abs=0.02)  # the whole lunge, on open floor
    assert p.lunge_left == 0


def test_the_lunge_sets_off_a_little_before_the_blow_lands():
    m = hall()
    p = lunger(m)
    x0 = p.x
    while p.swing_t < p.swing_hit_at:
        p.update_timers(DT)
        p.step_lunge(m, DT)
    assert 0 < p.x - x0 < 1.0  # already under way as the blow lands, not all of it yet
    assert p.lunge_at < p.swing_hit_at


def test_the_lunge_stops_short_of_a_foes_body():
    m = hall()
    p = lunger(m)
    body = (p.x + 1.2, p.z, 0.5)  # a foe a step ahead: the full metre would end inside it
    swing_through(p, m, bodies=[body])
    gap = math.hypot(p.x - body[0], p.z - body[1])
    assert gap >= Player.RADIUS + body[2] - 1e-6
    assert gap < Player.RADIUS + body[2] + Player.LUNGE_STEP + 1e-6  # right up against it


def test_the_lunge_stops_at_a_wall():
    m = hall()
    p = lunger(m, tx=8)  # one tile from the hall's east wall
    swing_through(p, m)
    assert p.x + Player.RADIUS <= 9 * TileMap.TILE + 1e-6


def test_the_lunge_stops_at_whatever_blocks_the_way():
    m = hall()
    p = lunger(m)
    swing_through(p, m, blocked=lambda tx, tz: tx == 3)  # a fog gate on the next tile
    assert p.x + Player.RADIUS <= 3 * TileMap.TILE + 1e-6


def test_a_blow_cuts_the_lunge_short():
    m = hall()
    p = lunger(m)
    x0 = p.x
    while p.x == x0:  # under way
        p.update_timers(DT)
        p.step_lunge(m, DT)
    p.take_blow(5, p.x + 1, p.z)
    assert p.lunge_left == 0
    at = p.x
    swing_through(p, m)
    assert p.x == at


def test_the_lunge_ends_with_the_swing_and_on_being_set_down_elsewhere():
    m = hall()
    p = lunger(m)
    p.swing_t = None
    assert p.step_lunge(m, DT) == 0 and p.lunge_left == 0
    p = lunger(m)
    p.place(*TileMap.center(5, 1), 0.0, m)
    assert p.lunge_left == 0


def test_the_leaping_hew_carries_its_longer_lunge_smoothly():
    m = hall()
    p = Player(inventory=Inventory(right="hatchet"))
    p.place(*TileMap.center(2, 1), 0.0, m)
    p.since_sprint = 0.0  # straight out of a sprint
    a = p.start_swing(kind=weapons.HEAVY)
    assert a.name == "Leaping Hew"
    x0 = p.x
    steps = swing_through(p, m)
    assert max(steps) <= 0.15
    assert p.x - x0 == pytest.approx(a.lunge, abs=0.02)


def test_a_body_you_already_touch_does_not_hold_you_but_one_ahead_does():
    assert collision.runs_into(0, 0, 0.1, 0, 0.4, [(0.8, 0, 0.5)])
    assert not collision.runs_into(0, 0, -0.1, 0, 0.4, [(0.5, 0, 0.5)])  # stepping away
    assert not collision.runs_into(0, 0, 0.1, 0, 0.4, [(3.0, 0, 0.5)])


def test_in_the_keep_a_lunge_never_crosses_a_boss_fog():
    game = FakeGame()
    world = World(game, "abandoned_prison")
    arena = world.arenas[0]
    game.flags.add(arena.fog_key)  # you died in there: its door has given way to fog
    assert arena.fogged(world.flags) and world.player_blocker(*arena.gate)
    gx, gz = TileMap.center(*arena.gate)
    axis = (1, 0) if arena.door.axis == "x" else (0, 1)
    for sign in (1, -1):  # whichever side of the fog has floor to stand on
        x, z = gx - axis[0] * sign * 1.5, gz - axis[1] * sign * 1.5
        tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
        if collision.passable(world.map, tx, tz, world.map.floor_at(gx, gz), world.player_blocker):
            break
    p = game.player
    p.inventory = Inventory(right="katana")
    p.place(x, z, math.atan2(axis[1] * sign, axis[0] * sign), world.map)
    p.start_swing(kind=weapons.HEAVY, secrets=False)
    while p.swinging:
        p.update_timers(DT)
        p.step_lunge(world.map, DT, blocked=world.player_blocker, bodies=world.bodies())
    assert (TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)) != arena.gate
    assert math.hypot(p.x - gx, p.z - gz) > TileMap.TILE / 2
