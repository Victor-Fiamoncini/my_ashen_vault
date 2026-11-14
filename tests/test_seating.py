"""Chests (and the mimics that ape them) sit with their backs to the wall, not dropped mid-tile."""

import math

import pytest

from ashen_vault.world.tile_map import SEAT_DEPTH, TileMap
from ashen_vault.world.world import World
from test_keep_world import FakeGame

MAPS = ("sunken_keep", "verdant_hollow", "cinderhold", "cinder_keep")  # the town has no chests


def _tile(x, z):
    return int(x // TileMap.TILE), int(z // TileMap.TILE)


def test_seated_pushes_back_only_against_a_wall():
    m = World(FakeGame(), "cinderhold").map
    tx, tz = next((tx, tz) for tx, tz, t in m.each_tile() if t.walkable and m[tx - 1, tz].solid)
    cx, cz = TileMap.center(tx, tz)
    assert m.seated(tx, tz, 0.0) == pytest.approx((cx - SEAT_DEPTH, cz))
    tx, tz = next((tx, tz) for tx, tz, t in m.each_tile() if t.walkable and not m[tx - 1, tz].solid)
    assert m.seated(tx, tz, 0.0) == TileMap.center(tx, tz)


@pytest.mark.parametrize("name", MAPS)
def test_every_chest_backs_onto_its_wall_and_can_still_be_opened(name):
    game = FakeGame()
    world = World(game, name)
    chests = [p for p in world.props if p.kind == "chest"] + [e for e in world.enemies if e.dormant]
    assert chests
    for c in chests:
        tx, tz = _tile(c.x, c.z)
        cx, cz = TileMap.center(tx, tz)
        bx, bz = -math.cos(c.yaw), -math.sin(c.yaw)
        if world.map[tx + round(bx), tz + round(bz)].solid:
            assert (c.x - cx) * bx + (c.z - cz) * bz == pytest.approx(SEAT_DEPTH), (name, tx, tz)
        # walked up to from the open side, the chest is the thing in front of you
        px, pz = c.x - bx * 1.4, c.z - bz * 1.4
        game.player.place(px, pz, math.atan2(bz, bx), world.map)
        assert world.focus() is c, (name, tx, tz)


def test_props_wholly_behind_the_eye_are_not_drawn():
    from ashen_vault.world.world import BEHIND_MARGIN, behind_view

    assert behind_view(0.0, -(BEHIND_MARGIN + 0.1), 0.0, 1.0)
    assert not behind_view(0.0, -(BEHIND_MARGIN - 0.1), 0.0, 1.0)  # a wide model reaching past you
    assert not behind_view(5.0, 0.0, 0.0, 1.0)  # beside you, at the edge of a wide view
