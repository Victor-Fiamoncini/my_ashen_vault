"""The keep's World logic driven without a window: a fake game records messages, sounds and wounds."""

import math
import random

import pytest

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.player import Player
from ashen_vault.world.hazards import Eruption
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World


class _Gpu:
    def upload_batch(self, _batch):
        return None

    def unload_mesh(self, _mesh):
        pass


class FakeGame:
    def __init__(self, flags=()):
        self.gpu = _Gpu()
        self.flags = set(flags)
        self.player = Player()
        self.messages = []
        self.sounds = []
        self.wounds = []

    def message(self, text):
        self.messages.append(text)

    def sfx(self, name, volume=1.0):
        self.sounds.append(name)

    def hurt_player(self, dmg, source):
        self.wounds.append((dmg, source))
        self.player.stats.hp -= dmg

    def blocked(self, _block):
        pass


def keep(flags=(), at=(15, 21)):
    game = FakeGame(flags)
    world = World(game, "sunken_keep")
    x, z = TileMap.center(*at)
    game.player.place(x, z, 0.0, world.map)
    return game, world


def lift(world, lever):
    return next(p for p in world.terrain.platforms if p.kind == "lift" and p.lever == lever)


def test_chained_lifts_load_locked_until_their_winch_is_pulled():
    game, world = keep()
    assert lift(world, "crypt_winch").locked and lift(world, "belfry_winch").locked
    assert not lift(world, None).locked
    winch = next(p for p in world.props if p.kind == "lever" and p.props.get("id") == "crypt_winch")
    world.pull_lever(winch)
    assert not lift(world, "crypt_winch").locked and lift(world, "belfry_winch").locked
    assert "lever:crypt_winch" in game.flags and "chain" in game.sounds
    # Come back later: the freed lift stays free.
    _game, again = keep(game.flags)
    assert not lift(again, "crypt_winch").locked


def test_a_locked_lift_says_so_when_you_wait_for_it():
    game, world = keep(at=(13, 26))  # the shrine room landing; its lift waits below, chained
    for _ in range(20):
        world.update_terrain(0.05)
    assert any("locked fast" in m for m in game.messages)


def test_gaoler_hook_drags_you_toward_him():
    game, world = keep(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(19, 21), rng=random.Random(1))
    before = math.hypot(g.x - game.player.x, g.z - game.player.z)
    world.hook(g, 0.4, 2.5)
    after = math.hypot(g.x - game.player.x, g.z - game.player.z)
    assert game.wounds and after == pytest.approx(before - 2.5, abs=0.05)
    assert any("hook" in m for m in game.messages)


def test_gaoler_hook_never_drags_you_into_him_or_off_a_lift():
    game, world = keep(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(16, 21), rng=random.Random(1))
    world.hook(g, 0.4, 2.5)
    gap = math.hypot(g.x - game.player.x, g.z - game.player.z)
    assert gap >= g.radius + Player.RADIUS
    game.player.y += 3.0  # riding a lift above him: the chain only bites
    x = game.player.x
    world.hook(g, 0.4, 2.5)
    assert game.player.x == x


def test_warden_slam_and_eruptions_burn_where_you_stood():
    game, world = keep(at=(15, 5))
    w = Enemy(EnemyTypes.get("ashen_warden"), *TileMap.center(15, 3), rng=random.Random(1))
    world.slam(w)
    assert world.shockwaves and "quake" in game.sounds
    world.eruption(w)
    assert len(world.eruptions) == 3
    assert all(isinstance(f, Eruption) for f in world.eruptions)
    first = world.eruptions[0]
    assert (first.x, first.z) == (game.player.x, game.player.z)
    for _ in range(round((Eruption.WARN + 0.1) / 0.05)):
        world.update(0.05)
    assert any(src == "The fire" for _, src in game.wounds)
    for _ in range(40):
        world.update(0.05)
    assert world.eruptions == [] and world.shockwaves == []


def test_the_wardens_rage_is_announced():
    game, world = keep()
    w = Enemy(EnemyTypes.get("ashen_warden"), 0, 0)
    world.boss_rage(w)
    assert game.messages == [EnemyTypes.get("ashen_warden").rage]


def test_a_shrine_rest_puts_out_the_fires():
    _game, world = keep(at=(15, 5))
    w = Enemy(EnemyTypes.get("ashen_warden"), *TileMap.center(15, 3))
    world.eruption(w)
    world.slam(w)
    world.respawn_enemies()
    assert world.eruptions == [] and world.shockwaves == []


def test_new_props_block_their_tiles():
    _game, world = keep()
    for kind in ("pillar", "sarcophagus", "headsman_block"):
        p = next(p for p in world.props if p.kind == kind)
        assert world.blocked_tile(p.tx, p.tz), kind
    for kind in ("cage", "roots", "grate", "cobweb", "skull_niche", "winch"):
        p = next(p for p in world.props if p.kind == kind)
        assert not world.blocked_tile(p.tx, p.tz), kind


def test_eruptions_never_rise_inside_a_wall():
    _game, world = keep(at=(10, 4))  # against the hall's west wall
    w = Enemy(EnemyTypes.get("ashen_warden"), *TileMap.center(10, 2))
    world.eruption(w)  # the side circles fall east and west: the west one is in the wall
    assert len(world.eruptions) == 2
    assert all(not world.map.tile_at(f.x, f.z).solid for f in world.eruptions)


def test_a_shield_that_stops_the_hook_stops_the_drag():
    game, world = keep(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(19, 21))
    world.enemy_strike = lambda *_: 0  # the shield took it all
    x = game.player.x
    world.hook(g, 0.4, 2.5)
    assert game.player.x == x and game.messages == []


def butcher(world):
    return next((e for e in world.enemies if e.type.id == "butcher"), None)


def test_the_butcher_waits_in_his_hall_north_of_the_gallery():
    _game, world = keep()
    b = butcher(world)
    assert b is not None and b.type.boss and b.type.drop is None  # no relic: the ending is untouched
    assert world.map.tile_at(b.x, b.z).floor == pytest.approx(7.6)
    assert TileMap.tile_coord(b.z) < 9  # in the slaughter hall, beyond the old gallery's north wall


def test_the_butcher_drops_his_cleaver_and_stays_dead():
    _game, world = keep()
    b = butcher(world)
    b.kill()
    world.drop_enemy_loot(b)
    assert any(p.kind == "pickup" and p.props["item"] == "butcher_cleaver" for p in world.props)
    # A shrine rest brings back a living boss as he is...
    _game, world = keep()
    world.respawn_enemies()
    assert butcher(world) is not None
    # ...but once he has fallen, neither a reload nor a rest brings him back.
    _game, world = keep(flags={"butcher_dead"})
    assert butcher(world) is None
    world.respawn_enemies()
    assert butcher(world) is None


def test_the_keeps_lifts_are_jail_cages_open_toward_their_landings():
    _game, world = keep()
    lifts = [p for p in world.terrain.platforms if p.kind == "lift"]
    assert len(lifts) == 4 and all(p.model == "cage" for p in lifts)
    for p in lifts:
        assert p.doors, (p.x, p.z)  # every cage has a way in
        tx, tz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        for dx, dz in p.doors:
            assert world.map[tx + dx, tz + dz].walkable


def _bolt_past(world, kind, pitch=0.0):
    """Fires a bolt east from (15, 21) over a `kind` prop set on the next tile; returns how far it got."""
    from ashen_vault.world.world import Prop

    player = world.player
    player.yaw, player.pitch = 0.0, pitch
    tx, tz = TileMap.tile_coord(player.x) + 1, TileMap.tile_coord(player.z)
    x, z = TileMap.center(tx, tz)
    world.props.append(Prop(kind, x, z, world.map[tx, tz].floor, tx, tz, {}, f"test:{tx},{tz}"))
    world.fire_bolt(5)
    bolt = world.projectiles[-1]
    for _ in range(20):
        world._update_projectiles(0.05)
        if bolt.life <= 0:
            break
    return bolt.x - player.x


def test_a_bolt_flies_over_a_table_but_not_through_a_pillar():
    _game, world = keep()
    assert _bolt_past(world, "table") > 3.0
    _game, world = keep()
    assert _bolt_past(world, "pillar") < 3.0


def test_a_bolt_aimed_low_still_strikes_the_barrel():
    _game, world = keep()
    assert _bolt_past(world, "barrel", pitch=-0.5) < 3.0


def test_the_silent_bell_can_be_touched_from_the_edge_of_its_plinth():
    game = FakeGame()
    world = World(game, "harrowmere")
    bell = next(p for p in world.props if p.kind == "silent_bell")
    game.player.place(bell.x, bell.z - 3.4, math.pi / 2, world.map)  # at the plinth's edge, facing it
    assert world.focus() is bell
    game.player.place(bell.x, bell.z - 3.4, -math.pi / 2, world.map)  # turned away
    assert world.focus() is not bell


def test_the_compass_points_to_the_nearest_living_boss_and_then_to_none():
    game, world = keep()
    gates = {a.flag: TileMap.center(*a.gate) for a in world.arenas}
    near = min(gates.values(), key=lambda g: math.hypot(g[0] - game.player.x, g[1] - game.player.z))
    assert world.boss_target() == near
    tx, tz = near  # face the door: the bearing is your heading
    game.player.yaw = math.atan2(tz - game.player.z, tx - game.player.x)
    assert world.boss_bearing() == pytest.approx(game.player.heading)
    game.flags.add("butcher_dead")
    assert world.boss_target() == gates["boss_dead"]
    game.flags.add("boss_dead")
    assert world.boss_target() is None and world.boss_bearing() is None


def test_the_town_has_no_boss_to_point_at():
    game = FakeGame()
    world = World(game, "harrowmere")
    game.player.place(*TileMap.center(25, 21), 0.0, world.map)
    assert world.boss_bearing() is None
