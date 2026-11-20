"""The prison's World logic driven without a window: a fake game records messages, sounds and wounds."""

import math
import random

import pytest

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.player import Player
from ashen_vault.world.hazards import Eruption
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import LIFT_LOCKED, World, stair_footprint


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
        self.volumes = []  # (name, volume) of every sound, in the order played
        self.wounds = []

    def message(self, text):
        self.messages.append(text)

    def sfx(self, name, volume=1.0):
        self.sounds.append(name)
        self.volumes.append((name, volume))

    def hurt_player(self, dmg, source):
        self.wounds.append((dmg, source))
        self.player.stats.hp -= dmg

    def blocked(self, _block):
        pass


def prison(flags=(), at=(15, 21)):
    game = FakeGame(flags)
    world = World(game, "abandoned_prison")
    x, z = TileMap.center(*at)
    game.player.place(x, z, 0.0, world.map)
    return game, world


CRYPT_LIFT, BELFRY_LIFT = (12, 26), (25, 16)  # the shortcut lifts: shrine to Undercroft, Gallery down


def lift(world, at):
    return next(
        p
        for p in world.terrain.platforms
        if p.kind == "lift" and (TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)) == at
    )


def run_terrain(world, game, seconds):
    for _ in range(round(seconds / 0.05)):
        world.update_terrain(0.05)
        game.player.y = world.player_floor()


def stand_on(game, world, plate):
    game.player.x, game.player.z = plate.x, plate.z
    game.player.y = world.player_floor()


def test_shortcut_lifts_load_locked_with_no_lever_beside_them():
    _game, world = prison(at=(13, 26))  # the shrine room landing; its lift waits below, fastened
    assert lift(world, CRYPT_LIFT).locked and lift(world, BELFRY_LIFT).locked
    assert not lift(world, (4, 25)).locked
    assert not [p for p in world.props if p.kind == "lift_call"]  # the call plates do the calling


def test_a_fastened_lift_refuses_the_call_plate_on_its_far_landing():
    game, world = prison(at=(13, 26))
    shaft = lift(world, CRYPT_LIFT)
    (plate,) = [c for c in shaft.calls if c.end == "high"]
    stand_on(game, world, plate)
    run_terrain(world, game, 1.0)
    assert plate.pressed and shaft.at == "low" and not shaft.moving
    assert [m for m in game.messages if "fastened from the other end" in m] == [LIFT_LOCKED]


def test_riding_a_shortcut_lift_from_its_open_end_frees_it_for_good():
    game, world = prison(at=(11, 26))  # the Undercroft landing, beside the lift resting there
    game.player.y = world.player_floor()
    shaft = lift(world, CRYPT_LIFT)
    game.player.x, game.player.z = shaft.x, shaft.z  # onto the plate
    run_terrain(world, game, 0.7 + (shaft.high - shaft.low) / shaft.speed + 1.0)
    assert shaft.at == "high" and not shaft.locked
    assert f"lift:abandoned_prison:{CRYPT_LIFT[0]},{CRYPT_LIFT[1]}" in game.flags
    assert any("grinds free" in m for m in game.messages)
    # Come back later: it stays free, and the call plate below brings it down.
    again_game, again = prison(game.flags, at=(11, 26))
    freed = lift(again, CRYPT_LIFT)
    assert not freed.locked
    freed.at, freed.deck = "high", freed.high
    (plate,) = [c for c in freed.calls if c.end == "low"]
    stand_on(again_game, again, plate)
    run_terrain(again, again_game, 0.1)
    assert freed.moving and "chain" in again_game.sounds
    run_terrain(again, again_game, (freed.high - freed.low) / freed.speed + 0.5)
    assert freed.at == "low"


def test_every_lift_landing_has_a_call_plate_that_brings_it():
    game, world = prison()
    for p in (p for p in world.terrain.platforms if p.kind == "lift"):
        assert len(p.calls) == len(p.doors) and {c.end for c in p.calls} == {"low", "high"}
        for c in p.calls:
            tile = world.map.tile_at(c.x, c.z)
            assert tile.walkable and not tile.chasm and c.floor == (p.low if c.end == "low" else p.high)
    free = lift(world, (4, 25))
    (plate,) = [c for c in free.calls if c.end == "high"]
    stand_on(game, world, plate)
    run_terrain(world, game, 0.1)
    assert free.moving
    run_terrain(world, game, (free.high - free.low) / free.speed + 0.5)
    assert free.at == "high"
    run_terrain(world, game, 2.0)  # standing on the plate calls it only once
    assert free.at == "high"


def test_gaoler_hook_drags_you_toward_him():
    game, world = prison(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(19, 21), rng=random.Random(1))
    before = math.hypot(g.x - game.player.x, g.z - game.player.z)
    world.hook(g, 0.4, 2.5)
    after = math.hypot(g.x - game.player.x, g.z - game.player.z)
    assert game.wounds and after == pytest.approx(before - 2.5, abs=0.05)
    assert any("hook" in m for m in game.messages)


def test_gaoler_hook_never_drags_you_into_him_or_off_a_lift():
    game, world = prison(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(16, 21), rng=random.Random(1))
    world.hook(g, 0.4, 2.5)
    gap = math.hypot(g.x - game.player.x, g.z - game.player.z)
    assert gap >= g.radius + Player.RADIUS
    game.player.y += 3.0  # riding a lift above him: the chain only bites
    x = game.player.x
    world.hook(g, 0.4, 2.5)
    assert game.player.x == x


def test_warden_slam_and_eruptions_burn_where_you_stood():
    game, world = prison(at=(15, 5))
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
    game, world = prison()
    w = Enemy(EnemyTypes.get("ashen_warden"), 0, 0)
    world.boss_rage(w)
    assert game.messages == [EnemyTypes.get("ashen_warden").rage]


def test_a_shrine_rest_puts_out_the_fires():
    _game, world = prison(at=(15, 5))
    w = Enemy(EnemyTypes.get("ashen_warden"), *TileMap.center(15, 3))
    world.eruption(w)
    world.slam(w)
    world.respawn_enemies()
    assert world.eruptions == [] and world.shockwaves == []


def test_new_props_block_their_tiles():
    _game, world = prison()
    for kind in ("pillar", "sarcophagus", "headsman_block"):
        p = next(p for p in world.props if p.kind == kind)
        assert world.blocked_tile(p.tx, p.tz), kind
    for kind in ("cage", "roots", "grate", "cobweb", "skull_niche", "winch"):
        p = next(p for p in world.props if p.kind == kind)
        assert not world.blocked_tile(p.tx, p.tz), kind


def test_eruptions_never_rise_inside_a_wall():
    _game, world = prison(at=(10, 4))  # against the hall's west wall
    w = Enemy(EnemyTypes.get("ashen_warden"), *TileMap.center(10, 2))
    world.eruption(w)  # the side circles fall east and west: the west one is in the wall
    assert len(world.eruptions) == 2
    assert all(not world.map.tile_at(f.x, f.z).solid for f in world.eruptions)


def test_a_shield_that_stops_the_hook_stops_the_drag():
    game, world = prison(at=(15, 21))
    g = Enemy(EnemyTypes.get("gaoler"), *TileMap.center(19, 21))
    world.enemy_strike = lambda *_: 0  # the shield took it all
    x = game.player.x
    world.hook(g, 0.4, 2.5)
    assert game.player.x == x and game.messages == []


def butcher(world):
    return next((e for e in world.enemies if e.type.id == "butcher"), None)


def test_the_butcher_waits_in_his_hall_north_of_the_gallery():
    _game, world = prison()
    b = butcher(world)
    assert b is not None and b.type.boss and b.type.drop is None  # no relic: the ending is untouched
    assert world.map.tile_at(b.x, b.z).floor == pytest.approx(12.0)
    assert TileMap.tile_coord(b.z) < 9  # in the slaughter hall, beyond the old gallery's north wall


def test_the_butcher_drops_his_cleaver_and_stays_dead():
    _game, world = prison()
    b = butcher(world)
    b.kill()
    world.drop_enemy_loot(b)
    assert any(p.kind == "pickup" and p.props["item"] == "butcher_cleaver" for p in world.props)
    # A shrine rest brings back a living boss as he is...
    _game, world = prison()
    world.respawn_enemies()
    assert butcher(world) is not None
    # ...but once he has fallen, neither a reload nor a rest brings him back.
    _game, world = prison(flags={"butcher_dead"})
    assert butcher(world) is None
    world.respawn_enemies()
    assert butcher(world) is None


def test_the_prisons_lifts_are_jail_cages_open_toward_their_landings():
    _game, world = prison()
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
    _game, world = prison()
    assert _bolt_past(world, "table") > 3.0
    _game, world = prison()
    assert _bolt_past(world, "pillar") < 3.0


def test_a_bolt_aimed_low_still_strikes_the_barrel():
    _game, world = prison()
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
    game, world = prison()
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


def test_town_props_hang_on_the_thin_house_walls_and_the_stalls_are_gone():
    game = FakeGame()
    world = World(game, "harrowmere")
    kinds = {p.kind for p in world.props}
    assert "stall" not in kinds
    assert {"fountain", "bench", "banner_pole", "shutters", "door_arch", "cathedral_tower"} <= kinds
    # Brannoc's forge hearth stands back against the west wall of his forge: its slab, not the tile's edge.
    hearth = next(p for p in world.props if p.kind == "forge_hearth" and (p.tx, p.tz) == (4, 17))
    assert world.map[3, 17].thin
    assert hearth.x == pytest.approx(TileMap.center(4, 17)[0] - world.map.wall_inset(4, 17, -1, 0))
    assert world.map.wall_inset(4, 17, -1, 0) == pytest.approx(1.5)


def test_pells_outside_stair_is_solid_and_leaves_his_doorstep_free():
    world = World(FakeGame(), "harrowmere")
    stair = next(p for p in world.props if p.kind == "outside_stair")
    tiles = stair_footprint(stair)
    assert len(tiles) == int(stair.props.get("run", "2"))
    assert all(world.blocked_tile(*t) for t in tiles)
    assert (10, 33) not in tiles and not world.blocked_tile(10, 33)  # the step outside Pell's door
    # The alley beside the flight stays open.
    assert all(world.map[11, z].walkable and not world.blocked_tile(11, z) for z in range(29, 34))


def _town_door(at=(9, 33)):
    """Harrowmere with you on the step outside Pell's door (a door arch at 9,33 facing east)."""
    game = FakeGame()
    world = World(game, "harrowmere")
    game.player.place(*TileMap.center(at[0] + 1, at[1]), math.pi, world.map)
    door = next(p for p in world.props if p.kind == "house_door" and (p.tx, p.tz) == at)
    return game, world, door


def _swing(world, seconds=1.0):
    for _ in range(round(seconds / 0.05)):
        world.update(0.05)


def test_house_doors_start_shut_and_bar_the_doorway():
    _game, world, door = _town_door()
    assert door.open_t == 0 and world.blocked_tile(9, 33)
    assert world.focus() is door
    # Every house's arch hangs a door; the cathedral's great west door stands open, with none.
    arches = [p for p in world.props if p.kind == "door_arch"]
    doors = {(p.tx, p.tz) for p in world.props if p.kind == "house_door"}
    assert {(p.tx, p.tz) for p in arches if "rose" not in p.props} == doors
    assert all((p.tx, p.tz) not in doors for p in arches if "rose" in p.props)
    assert len(doors) == 5  # the forge, Corvane's hut, Pell's, Wren's and Tamsin's


def test_a_house_door_opens_lets_you_in_and_shuts_again():
    game, world, door = _town_door()
    assert world.swing_door(door) and "door" in game.sounds
    world.update(0.05)
    assert 0 < door.open_t < 1 and not world._interactable(door)  # not while it swings
    _swing(world)
    assert door.open_t == 1.0 and not world.blocked_tile(9, 33)
    assert world._interactable(door)
    assert world.swing_door(door)
    _swing(world)
    assert door.open_t == 0.0 and world.blocked_tile(9, 33)


def test_a_house_door_will_not_shut_on_you_and_is_shut_again_when_you_return():
    game, world, door = _town_door()
    world.swing_door(door)
    _swing(world)
    game.player.x, game.player.z = TileMap.center(9, 33)  # standing in the doorway
    assert not world.swing_door(door) and door.goal == 1.0
    assert not any(k.startswith("house_door") for k in game.flags)  # never saved
    again = World(game, "harrowmere")
    assert next(p for p in again.props if p.kind == "house_door" and (p.tx, p.tz) == (9, 33)).open_t == 0


def _close_from(spot, yaw):
    """Opens Pell's door, then stands you at `spot` facing `yaw` and shuts it with what the prompt
    offers there, the way a player does: interact on whatever `focus` finds."""
    game, world, door = _town_door()
    world.swing_door(door)
    _swing(world)
    p = game.player
    p.x, p.z, p.yaw = *spot, yaw
    assert world.focus() is door
    return game, world, door, world.swing_door(door)


@pytest.mark.parametrize(
    "spot, yaw",
    [
        ((20.13, 67.0), math.pi),  # stepped back out onto the step, a shoulder still over the sill
        ((20.6, 67.6), math.pi),  # on the step, off to one side
        ((17.85, 67.0), 0.0),  # just inside, having walked in and turned round
        ((17.4, 66.3), 0.0),  # inside, beside the jamb
    ],
)
def test_a_house_door_shuts_from_wherever_you_stand_beside_it(spot, yaw):
    game, world, door, shut = _close_from(spot, yaw)
    assert shut and door.goal == 0.0
    _swing(world)
    assert door.open_t == 0.0 and world.blocked_tile(9, 33)
    p = game.player
    assert not (18.0 - p.RADIUS < p.x < 20.0 + p.RADIUS and 66.0 - p.RADIUS < p.z < 68.0 + p.RADIUS)
    # Nothing left you wedged against the shut leaf: you walk away from it freely.
    x0, z0 = p.x, p.z
    p.yaw = yaw + math.pi
    p.walk(world.map, 1, 0, 0.1, blocked=world.blocked_tile)
    assert math.hypot(p.x - x0, p.z - z0) > 0.1


def test_a_house_door_still_will_not_shut_on_you_in_its_doorway():
    for spot in ((19.0, 67.0), (19.9, 66.2)):
        _game, _world, door, shut = _close_from(spot, math.pi)
        assert not shut and door.goal == 1.0


def test_a_struck_foe_glows_red():
    from ashen_vault.world.world import HIT_RED

    _, world = prison()
    lights = []

    class Gpu:
        def model_light(self, rgb):
            lights.append(tuple(rgb))

    world._model_light(Gpu(), 0, 1, 0, flash=True, tint=(0.45, 1.1, 0.3))
    assert lights == [HIT_RED]
    red, green, blue = HIT_RED
    assert red > max(green, blue) * 1.5  # red leads, without drowning the body's own look


def test_a_smashed_barrel_flings_its_pieces_out_then_settles_and_a_loaded_one_lies_settled():
    from ashen_vault.world.world import BREAK_TIME

    _game, world = prison()
    barrel = next(p for p in world.props if p.kind in ("barrel", "crate"))
    assert barrel.open_t == 0.0 and barrel.break_t == 1.0  # whole: nothing to animate
    world.break_prop(barrel)
    assert barrel.open_t == 1.0 and barrel.break_t == 0.0  # broken at once (loot, path, save)
    world.update(BREAK_TIME / 2)
    assert 0.0 < barrel.break_t < 1.0
    world.update(BREAK_TIME)
    assert barrel.break_t == 1.0
    # Loaded from a save that holds it broken: its wreck already lies still.
    _game, world = prison(flags={barrel.key})
    again = next(p for p in world.props if p.key == barrel.key)
    assert again.open_t == 1.0 and again.break_t == 1.0


def test_hollow_inmates_kneel_until_you_come_near_then_rise_and_come_for_you():
    game, world = prison(at=(15, 32))  # down in the gaol's shaft, far from the guard hall
    (inmate,) = [
        e for e in world.enemies if e.type.id == "hollow_inmate" and (e.x, e.z) == TileMap.center(13, 20)
    ]
    for _ in range(20):
        world.update(0.05)
    assert inmate.state == "idle"
    x, z = TileMap.center(13, 22)
    game.player.place(x, z, -math.pi / 2, world.map)
    for _ in range(20):
        world.update(0.05)
    assert inmate.state != "idle"


def test_the_west_cells_lever_raises_every_cell_front_at_once():
    _game, world = prison(at=(4, 16))
    gates = [p for p in world.props if p.kind == "gate" and p.props.get("lever") == "west_cells"]
    (lever,) = [p for p in world.props if p.kind == "lever" and p.props.get("id") == "west_cells"]
    assert len(gates) >= 4 and all(world.blocked_tile(g.tx, g.tz) for g in gates)
    world.pull_lever(lever)
    for _ in range(60):
        world.update(0.05)
    assert not any(world.blocked_tile(g.tx, g.tz) for g in gates)
