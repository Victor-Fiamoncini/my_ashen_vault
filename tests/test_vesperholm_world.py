"""Vesperholm's World logic driven headless: the lances of moon-frost, the blink that steps a knight out
of the moonlight behind you, the Duchess's shafts of moonlight, her Argent Sigil, and the Vesper Gate
that stands open in Harrowmere."""

import math
import random

import pytest

from ashen_vault.ai.enemy import BLINK_RANGE, MOVES, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player import ailments
from ashen_vault.util import rround
from ashen_vault.world import relics, terrain
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import (
    BLINK_BEHIND,
    BRIDGE_RISING,
    LANCE_CHILL,
    MOON_FROST,
    MOONFALL_RINGS,
    World,
)
from test_verdant_world import JungleGame, foe, prop

BAILEY = (20, 22)  # the middle of the castle's open bailey
NORTH, EAST = -math.pi / 2, 0.0
THREE_TAKEN = {"sigil_taken", "verdant_sigil_taken", "iron_sigil_taken"}


def city(at=BAILEY, yaw=NORTH, flags=(), keep_foes=False):
    game = JungleGame(flags)
    world = World(game, "vesperholm")
    if not keep_foes:
        world.enemies = []  # placed by each test as needed
    game.player.place(*TileMap.center(*at), yaw, world.map)
    return game, world


# --- lances of moon-frost -------------------------------------------------------------------------


def test_a_lantern_wraith_throws_lances_of_moon_frost_one_at_a_time_or_three_at_once():
    game, world = city()
    wraith = foe(world, "lantern_wraith", (20, 19))
    world.enemy_fire(wraith, "shot")
    (lance,) = world.projectiles
    assert lance.effect == "lance" and lance.hostile and lance.damage == wraith.type.damage
    assert dict(lance.inflicts) == {"rot": 20, "frost": 30}
    world.projectiles = []
    world.enemy_fire(wraith, "frost_lance")  # the move: a fan of three
    assert len(world.projectiles) == 3
    damage = rround(wraith.type.damage * MOVES["frost_lance"][2])
    assert all(p.effect == "lance" and p.damage == damage for p in world.projectiles)
    headings = sorted(math.atan2(p.dz, p.dx) for p in world.projectiles)
    assert headings[-1] - headings[0] > 0.3  # a fan: step between its lances
    speed = math.hypot(world.projectiles[0].dx, world.projectiles[0].dz)
    assert speed > 8  # faster than a plain bolt
    assert "motes" in game.sounds


def test_a_lance_that_strikes_you_numbs_your_legs():
    game, world = city()
    wraith = foe(world, "lantern_wraith", (20, 19))
    world.enemy_fire(wraith, "shot")
    (lance,) = world.projectiles
    lance.x, lance.z, lance.y = game.player.x, game.player.z, game.player.y + 1.0
    hp = game.player.stats.hp
    world._update_projectiles(0.01)
    assert game.player.stats.hp < hp and not world.projectiles
    assert game.player.chill_t >= LANCE_CHILL - 0.01 and game.player.webbed_t == 0  # frost, not silk
    assert "Moon-frost numbs your legs!" in game.messages


# --- the blink --------------------------------------------------------------------------------------


def test_a_veiled_knight_steps_out_of_the_moonlight_behind_you():
    game, world = city(yaw=NORTH)
    knight = foe(world, "veiled_knight", (20, 18))
    assert world.blink(knight)
    assert math.hypot(knight.x - game.player.x, knight.z - (game.player.z + BLINK_BEHIND)) < 1e-6
    assert [w.style for w in world.shockwaves] == ["blink", "blink"]  # mist where it left and arrived
    assert "swoosh" in game.sounds
    assert not any("behind you" in m for m in game.messages)  # only a boss's blink is announced


def test_a_blink_never_lands_in_a_wall_or_the_gorge():
    _game, world = city(at=(3, 20), yaw=EAST)  # the bailey's west wall at your back
    knight = foe(world, "veiled_knight", (8, 20))
    assert world.blink(knight)
    tile = world.map.tile_at(knight.x, knight.z)
    assert tile.walkable and not tile.solid
    _game, world = city(at=(21, 32), yaw=-NORTH)  # on the Landing's brink, the gorge at your back
    knight = foe(world, "veiled_knight", (21, 35))
    assert world.blink(knight)
    tile = world.map.tile_at(knight.x, knight.z)
    assert not tile.chasm and tile.floor == 0


def test_a_knight_kept_at_bay_blinks_and_strikes_from_where_it_steps_out():
    game, world = city(yaw=NORTH)
    knight = foe(world, "veiled_knight", (20, 19))
    knight.state = "chase"
    knight.cooldowns["blink"] = 0.0
    dist = math.hypot(knight.x - game.player.x, knight.z - game.player.z)
    assert BLINK_RANGE[0] <= dist <= BLINK_RANGE[1]
    assert knight._pick_move(world, dist) == "blink"
    knight._begin_windup("blink")
    for _ in range(40):
        knight.update(0.05, world)
        if knight.attack_kind == "melee":
            break
    assert knight.state == "windup" and knight.attack_kind == "melee"  # already raising its blade
    assert knight.z > game.player.z  # behind you: you face north
    facing = math.atan2(game.player.z - knight.z, game.player.x - knight.x)
    assert abs(facing - knight.yaw) < 1e-6


# --- the Duchess -------------------------------------------------------------------------------------


def test_the_duchess_calls_shafts_of_moonlight_where_you_stand_and_to_either_side():
    game, world = city(yaw=NORTH)
    duchess = foe(world, "moon_duchess", (20, 18))
    world.moonbeam(duchess)
    assert len(world.eruptions) == 3 and all(f.style == "moon" for f in world.eruptions)
    first = world.eruptions[0]
    assert (first.x, first.z) == (game.player.x, game.player.z)
    xs = sorted(f.x for f in world.eruptions)
    assert xs[-1] - xs[0] > 4  # across your facing: step forward or back out of the line
    hp = game.player.stats.hp
    for _ in range(30):
        world._update_fire(0.05)
    assert game.player.stats.hp < hp and game.player.chill_t > 0
    assert "The moonlight burns you with cold!" in game.messages
    assert "motes" in game.sounds


def test_in_her_second_phase_the_moon_falls_round_you_in_rings():
    game, world = city()
    duchess = foe(world, "moon_duchess", (20, 18))
    world.moonfall(duchess)
    assert len(world.eruptions) == 1 + sum(count for _, count, _ in MOONFALL_RINGS)
    rings = {round(math.hypot(f.x - game.player.x, f.z - game.player.z), 1) for f in world.eruptions}
    assert rings == {0.0, *(r for r, _, _ in MOONFALL_RINGS)}
    assert "Duchess Ilvane raises her glaive, and the moon falls!" in game.messages


def test_the_duchess_is_the_moonwed_who_keeps_the_fourth_sigil():
    t = EnemyTypes.get("moon_duchess")
    assert t.boss and t.proper and t.called == "Duchess Ilvane"
    assert t.drop == "argent_sigil" and t.dead_flag == "duchess_dead" and t.rise == "ash"
    assert t.rage and {"frost_lance", "moonbeam"} <= set(t.moves)
    assert set(t.phase_moves) == {"blink", "moonfall"}
    assert t.material == "spirit"
    for type_id in ("pale_sentinel", "lantern_wraith", "moonhound", "veiled_knight"):
        regular = EnemyTypes.get(type_id)
        assert not regular.boss and (regular.moves or regular.ranged), type_id
        assert regular.material in ("iron", "spirit", "flesh"), type_id
    assert EnemyTypes.get("veiled_knight").moves == ("blink",)


def test_at_half_hp_she_casts_off_her_veil_and_learns_to_blink():
    game, world = city()
    duchess = Enemy(EnemyTypes.get("moon_duchess"), *TileMap.center(20, 18), rng=random.Random(0))
    world.enemies = [duchess]
    duchess.state, duchess.hp = "chase", duchess.type.hp // 2
    duchess.update(0.01, world)
    assert duchess.phase2 and duchess.attack_kind == "kindle"
    assert {"blink", "moonfall"} <= set(duchess.cooldowns)
    assert world.blink(duchess)
    assert "Duchess Ilvane steps out of the moonlight behind you!" in game.messages


def test_she_waits_in_her_choir_behind_a_great_door():
    _game, world = city(keep_foes=True)
    (duchess,) = [e for e in world.enemies if e.type.id == "moon_duchess"]
    assert duchess.state == "ashes"
    (arena,) = [a for a in world.arenas if a.flag == "duchess_dead"]
    tile = (TileMap.tile_coord(duchess.x), TileMap.tile_coord(duchess.z))
    assert tile in arena.tiles


def test_the_argent_sigil_lies_where_she_fell_until_it_is_taken():
    _game, world = city(flags={"duchess_dead"}, keep_foes=True)
    assert not any(e.type.id == "moon_duchess" for e in world.enemies)
    (sigil,) = [p for p in world.props if p.kind == "pickup" and p.props.get("item") == "argent_sigil"]
    assert (sigil.tx, sigil.tz) == (21, 4)
    _game, world = city(flags={"duchess_dead", "argent_sigil_taken"})
    assert not any(p.props.get("item") == "argent_sigil" for p in world.props if p.kind == "pickup")


# --- the Vesper Gate ---------------------------------------------------------------------------------


def test_taking_up_the_third_sigil_still_marks_the_first_three_taken():
    """GATE_FLAG no longer opens anything, but relics still records it once the first three are taken."""
    flags = set()
    for item in ("ember_sigil", "iron_sigil"):
        relics.mark_taken(item, flags)
        assert relics.GATE_FLAG not in flags
    relics.mark_taken("argent_sigil", flags)  # the fourth does not count toward it
    assert relics.GATE_FLAG not in flags
    relics.mark_taken("verdant_sigil", flags)
    assert relics.GATE_FLAG in flags
    assert relics.open_gate(flags)
    assert not relics.open_gate({"sigil_taken", "verdant_sigil_taken"})


def test_the_gate_in_town_is_always_open_even_on_a_fresh_save():
    for flags in (set(), THREE_TAKEN):
        game = JungleGame(flags)
        town = World(game, "harrowmere")
        (gate,) = [p for p in town.props if p.kind == "exit" and p.props.get("map") == "vesperholm"]
        assert town.exit_open(gate) and "shut" not in gate.props
        assert (relics.GATE_FLAG in game.flags) == bool(flags)  # an older save still catches up


def test_the_way_home_from_vesperholm_is_always_open():
    _game, world = city(at=(21, 100))  # the cave's hall, where the gate lets you in
    (home,) = [p for p in world.props if p.kind == "exit"]
    assert home.props["map"] == "harrowmere" and world.exit_open(home)
    assert world.map.meta["sky"] == "moonlit"


def test_moon_frost_slows_your_stride_until_it_thaws():
    strides = []
    for chill in (0.0, LANCE_CHILL):
        game, world = city()
        game.player.chill_t = chill
        z = game.player.z
        game.player.walk(world.map, 1.0, 0.0, 0.2)
        strides.append(z - game.player.z)
    assert 0 < strides[1] < strides[0]
    game.player.update_timers(LANCE_CHILL + 0.1)
    assert game.player.chill_t == 0


# --- frost and the Duchess's tempo -----------------------------------------------------------------


def test_a_lance_that_strikes_you_builds_frost():
    game, world = city()
    wraith = foe(world, "lantern_wraith", (20, 19))
    world.enemy_fire(wraith, "shot")
    (lance,) = world.projectiles
    lance.x, lance.z, lance.y = game.player.x, game.player.z, game.player.y + 1.0
    world._update_projectiles(0.01)
    assert game.player.ailments.meters["frost"] > 0


def test_a_shaft_of_moonlight_builds_frost():
    game, world = city()
    duchess = foe(world, "moon_duchess", (20, 18))
    world.moonbeam(duchess)
    for _ in range(30):
        world._update_fire(0.05)
    assert game.player.ailments.meters["frost"] >= MOON_FROST - 5  # drained a little since


def test_frostbite_bursts_and_freezes_your_legs():
    game, world = city()
    p = game.player

    def stride():
        x, z = p.x, p.z
        p.walk(world.map, 1, 0, 0.1)
        d = math.hypot(p.x - x, p.z - z)
        p.x, p.z = x, z
        return d

    free = stride()
    hp = p.stats.hp
    assert world.afflict_player("frost", ailments.FULL)
    assert p.stats.hp == hp - ailments.frostbite_burst(p.stats.max_hp)
    assert p.ailments.frozen and p.ailments.frostbitten
    assert "{Frostbite} seizes your legs!" in game.messages
    assert stride() == pytest.approx(free * ailments.FROZEN)


def test_the_duchess_fights_faster_than_any_other_boss_until_her_rage():
    """Her first phase is the quickest of any boss's; in her rage she eases off (her new moves are
    the danger), though she never grows slower than a boss of the common tempo."""
    duchess = EnemyTypes.get("moon_duchess")
    assert duchess.tempo < 1 and all(
        t.tempo >= 1 for t in EnemyTypes.ALL.values() if t.boss and t is not duchess
    )
    e = Enemy(duchess, 0.0, 0.0)
    e.attack_kind = "moonbeam"
    calm = e.windup_time
    assert calm < MOVES["moonbeam"][0]
    e.phase2 = True
    assert calm < e.windup_time < MOVES["moonbeam"][0]


def test_vesperholm_outmatches_the_areas_before_it():
    """The last area: each of its foes hits harder than the same kind of foe anywhere before."""
    vesper = ("pale_sentinel", "lantern_wraith", "moonhound", "veiled_knight", "glassmite", "moon_duchess")
    earlier = [t for t in EnemyTypes.ALL.values() if t.id not in vesper]
    assert EnemyTypes.get("moon_duchess").hp > max(t.hp for t in earlier if t.boss)
    assert EnemyTypes.get("moon_duchess").damage > max(t.damage for t in earlier if t.boss)
    assert EnemyTypes.get("veiled_knight").damage > max(
        t.damage for t in earlier if not (t.boss or t.ambush)
    )  # a mimic's ambush aside
    assert all(
        any(kind == "frost" for kind, _ in EnemyTypes.get(i).inflicts) for i in vesper if i != "moonhound"
    )


# --- the great bridge and the Glimmering Cave -----------------------------------------------------


def test_the_bailey_lever_raises_the_great_bridge_out_of_the_gorge_for_good():
    """One pull of the lever and all twelve spans of the stone bridge grind up out of the gorge
    together, to one long rumble, and it stays up on every visit after."""
    game, world = city(at=(21, 26))
    spans = [p for p in world.terrain.platforms if p.kind == "bridge"]
    assert len(spans) == 12 and all(p.locked and not p.afloat and p.risen_y < -17 for p in spans)
    world.pull_lever(prop(world, "lever", id="vesper_bridge"))
    assert game.sounds.count("stone_rise") == 1 and "chain" not in game.sounds
    assert BRIDGE_RISING in game.messages
    for _ in range(round(terrain.BRIDGE_RISE * 60) + 10):
        world.update_terrain(1 / 60)
    assert all(p.afloat and p.risen_y == pytest.approx(0.0) for p in spans)
    _, again = city(flags=game.flags)
    assert all(p.afloat for p in again.terrain.platforms if p.kind == "bridge")


def test_glassmites_lie_folded_in_the_cave_among_real_crystals():
    """Every Glassmite waits under the cave's roof with a cluster of moon-crystal close by, so folded
    down it is one more cluster among them."""
    _game, world = city(keep_foes=True)
    mites = [e for e in world.enemies if e.type.id == "glassmite"]
    crystals = [p for p in world.props if p.kind == "moon_crystal"]
    assert len(mites) == 3
    for e in mites:
        assert world.map.tile_at(e.x, e.z).ceil is not None  # in the cave
        assert min(math.hypot(c.x - e.x, c.z - e.z) for c in crystals) < 3 * TileMap.TILE
