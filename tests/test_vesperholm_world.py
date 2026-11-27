"""Vesperholm's World logic driven headless: the lances of moon-frost, the blink that steps a knight out
of the moonlight behind you, the Duchess's shafts of moonlight, her Argent Sigil, and the Vesper Gate
that stands open in Harrowmere."""

import itertools
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

BAILEY = (20, 42)  # the middle of the castle's open bailey
NORTH, EAST = -math.pi / 2, 0.0
CHAPEL_ALTAR = (21, 5)  # Lyra's altar, in the middle of her chapel's nave
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
    wraith = foe(world, "lantern_wraith", (20, 39))
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
    wraith = foe(world, "lantern_wraith", (20, 39))
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
    knight = foe(world, "veiled_knight", (20, 38))
    assert world.blink(knight)
    assert math.hypot(knight.x - game.player.x, knight.z - (game.player.z + BLINK_BEHIND)) < 1e-6
    assert [w.style for w in world.shockwaves] == ["blink", "blink"]  # mist where it left and arrived
    assert "swoosh" in game.sounds
    assert not any("behind you" in m for m in game.messages)  # only a boss's blink is announced


def test_a_blink_never_lands_in_a_wall_or_the_gorge():
    _game, world = city(at=(3, 40), yaw=EAST)  # the bailey's west wall at your back
    knight = foe(world, "veiled_knight", (8, 40))
    assert world.blink(knight)
    tile = world.map.tile_at(knight.x, knight.z)
    assert tile.walkable and not tile.solid
    _game, world = city(at=(21, 52), yaw=-NORTH)  # on the Landing's brink, the gorge at your back
    knight = foe(world, "veiled_knight", (21, 55))
    assert world.blink(knight)
    tile = world.map.tile_at(knight.x, knight.z)
    assert not tile.chasm and tile.floor == 0


def test_a_knight_kept_at_bay_blinks_and_strikes_from_where_it_steps_out():
    game, world = city(yaw=NORTH)
    knight = foe(world, "veiled_knight", (20, 39))
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
    duchess = foe(world, "moon_duchess", (20, 38))
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
    duchess = foe(world, "moon_duchess", (20, 38))
    world.moonfall(duchess)
    assert len(world.eruptions) == 1 + sum(count for _, count, _ in MOONFALL_RINGS)
    rings = {round(math.hypot(f.x - game.player.x, f.z - game.player.z), 1) for f in world.eruptions}
    assert rings == {0.0, *(r for r, _, _ in MOONFALL_RINGS)}
    assert "Duchess Ilvane raises her glaive, and the moon falls!" in game.messages


def test_the_duchess_is_the_moonwed_who_keeps_the_fourth_sigil():
    t = EnemyTypes.get("moon_duchess")
    assert t.boss and t.proper and t.called == "Duchess Ilvane"
    assert t.drop is None and t.dead_flag == "duchess_dead" and t.rise == "ash"  # it lies on an altar
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
    duchess = Enemy(EnemyTypes.get("moon_duchess"), *TileMap.center(20, 38), rng=random.Random(0))
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
    great, back = sorted((a for a in world.arenas if a.flag == "duchess_dead"), key=lambda a: a.gate[0])
    assert (great.gate, back.gate) == ((21, 29), (32, 23))  # the great door, and her choir's back door
    tile = (TileMap.tile_coord(duchess.x), TileMap.tile_coord(duchess.z))
    assert tile in great.tiles and great.tiles == back.tiles  # one choir, two mouths
    assert all(world.map[t].floor_tex == "moon_glass" for t in great.tiles)  # none of the stair beyond


def test_the_argent_sigil_lies_in_lyras_hands_in_her_chapel():
    """She drops nothing: the sigil she wed the moon on rests in the old god's hands, on her altar in the
    middle of Lyra's Chapel, under its vault on the crag behind the cathedral, high over the choir."""
    _game, world = city(flags={"duchess_dead"}, keep_foes=True)
    assert not any(e.type.id == "moon_duchess" for e in world.enemies)
    assert not any(p.kind == "pickup" for p in world.props)
    (altar,) = [p for p in world.props if p.kind == "altar"]
    assert (altar.tx, altar.tz) == CHAPEL_ALTAR
    assert altar.props["item"] == "argent_sigil" and altar.props["model"] == "lyra"
    tile = world.map[CHAPEL_ALTAR]
    assert tile.floor == 11.5 and tile.ceil is not None and tile.floor_tex == "moon_glass"
    assert altar.open_t == 0
    assert world.take_from_altar(altar) == "argent_sigil" and altar.open_t > 0


def _climb():
    """The way from her choir's back door to the chapel's door, tile by tile: north up the wall stair,
    west along the flying stair to the Moon Terrace, north up the grand stair to the forecourt."""
    wall = [(33, z) for z in range(23, 16, -1)]
    flying = [(x, 17) for x in range(32, 20, -1)]
    grand = [(21, z) for z in range(16, 8, -1)]
    return wall + flying + grand


def test_the_stair_behind_her_choir_climbs_to_lyras_chapel_high_over_it():
    """The back door opens on the old stair's foot, level with the choir, and the stair climbs north from
    it up through the cathedral's east wall, each step under its own vault; out of its tower a flying stair climbs west over the drop behind the cathedral to the
    Moon Terrace, and a grand stair north off it between cheek walls to the chapel's forecourt: never a
    step over half a metre, and the chapel's walls tower over the cathedral's."""
    _game, world = city()
    m = world.map
    way = _climb()
    assert m[way[0]].floor == 0 and m[32, 23].floor == 0  # through the back door onto its level foot
    (flight,) = [p for p in m.entities if p.kind == "stair_flight" and p.tx == 33]
    head = int(flight.props["run"]) - 1  # its steps reach down onto the foot, from the choir's floor up
    assert (flight.tz + head, m[flight.tx, flight.tz + head].floor) == (23, 0)
    for a, b in itertools.pairwise(way):
        assert 0 <= m[b].floor - m[a].floor <= 0.5 + 1e-6, (a, b)
    assert all(m[33, z].ceil is not None for z in range(18, 24))  # the wall stair, vaulted
    assert all(m[33, z].solid for z in range(24, 38))  # nothing of the old stair to the garden is left
    flying = [(x, 17) for x in range(24, 33)]
    assert all(m[t].ceil is None for t in flying)
    for x, z in flying[:-1]:  # nothing either side of it but the drop (the last step is by the tower)
        assert m[x, z - 1].chasm and m[x, z + 1].chasm, (x, z)
    for z in range(11, 17):  # the grand stair, three abreast, between its cheek walls
        assert m[19, z].solid and m[23, z].solid
        assert {m[x, z].floor for x in (20, 21, 22)} == {m[21, z].floor}
    assert m[way[-1]].floor == 11.5 and m[way[-1]].ceil is not None  # in the chapel's door
    chapel_walls = [t for _x, _z, t in m.each_tile() if t.solid and t.top is not None and t.top > 20]
    assert chapel_walls and min(t.top for t in chapel_walls) > m[20, 29].top  # over the cathedral's


def test_great_windows_of_moon_glass_look_out_of_the_choirs_back_wall_over_the_drop():
    """Seen from the Moon Terrace and the chapel's forecourt, the choir's back wall is no blank: three
    great windows of moon-glass hang high in it, in line with the choir's own windows inside."""
    _game, world = city()
    m = world.map
    inside = sorted(p.tx for p in m.entities if p.kind == "moon_window" and p.tz == 21)
    outside = [p for p in m.entities if p.kind == "moon_window" and p.tz == 19]
    assert sorted(p.tx for p in outside) == inside == [16, 21, 26]
    for w in outside:
        assert m[w.tx, w.tz].chasm and m[w.tx, w.tz + 1].solid  # hung on the wall's face over the drop
        size = float(w.props["size"])
        foot = m[w.tx, w.tz].floor + float(w.props["rise"])
        assert size >= 2 and foot > 0 and foot + 3.4 * size <= m[w.tx, w.tz + 1].top  # within the wall


def test_great_cracks_split_lyras_chapel_and_the_choirs_back_wall_and_nothing_else():
    """The great walls you climb past behind the Duchess's choir are split by cracks, in the moonstone's
    own cold tones; nothing else in the city is."""
    _game, world = city()
    cracks = [p for p in world.props if p.kind == "wall_crack"]
    chapel = [c for c in cracks if world.map[c.tx, c.tz].top == 26]
    choir = [c for c in cracks if c.tz == 20 and 12 <= c.tx <= 31]
    assert len(chapel) >= 3 and choir
    assert len(chapel) + len(choir) == len(cracks)
    assert {c.props["stone"] for c in cracks} == {"moonstone"}
    for c in cracks:  # near the walls' tops, where the climb sees them, never deep in the gorge
        assert c.y >= world.map[c.tx, c.tz].top - float(world.map.meta["crack_span"]) - 1e-6, (c.tx, c.tz)


def test_the_apse_holds_the_portals_arch_dormant_until_the_sigil_is_lifted():
    """The portal's arch always stands in Lyra's apse, but it can't be taken until the sigil is lifted."""
    _game, world = city(at=(21, 3), flags={"duchess_dead"})
    (portal,) = [p for p in world.props if p.kind == "exit" and p.props.get("model") == "argent_portal"]
    assert not world.exit_open(portal) and world.focus() is not portal
    _game, world = city(at=(21, 3), flags={"duchess_dead", "argent_sigil_taken"})
    (portal,) = [p for p in world.props if p.kind == "exit" and p.props.get("model") == "argent_portal"]
    assert world.exit_open(portal)


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
    _game, world = city(at=(21, 120))  # the cave's hall, where the gate lets you in
    (home,) = [p for p in world.props if p.kind == "exit" and p.props["map"] == "harrowmere"]
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
    wraith = foe(world, "lantern_wraith", (20, 39))
    world.enemy_fire(wraith, "shot")
    (lance,) = world.projectiles
    lance.x, lance.z, lance.y = game.player.x, game.player.z, game.player.y + 1.0
    world._update_projectiles(0.01)
    assert game.player.ailments.meters["frost"] > 0


def test_a_shaft_of_moonlight_builds_frost():
    game, world = city()
    duchess = foe(world, "moon_duchess", (20, 38))
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
    later = ("grafted_drake", "drake_magus", "vat_spawn", "herran")  # Herran's Castle, past Vesperholm
    earlier = [t for t in EnemyTypes.ALL.values() if t.id not in vesper + later]
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
    game, world = city(at=(21, 46))
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


def test_lyras_chapel_is_out_of_reach_from_below():
    """Her chapel stands on its crag 11.5 m over the drop: from the bailey, the garden or the Moon
    Terrace you can't reach the altar, only from the chapel's own floor."""
    for at, yaw in (((21, 41), NORTH), ((38, 23), NORTH), ((21, 17), NORTH)):
        _game, world = city(at=at, yaw=yaw, flags={"duchess_dead"})
        assert world.focus() is None or world.focus().kind != "altar", at
    _game, world = city(at=(21, 6), yaw=NORTH, flags={"duchess_dead"})
    assert world.player.y == 11.5
    assert world.focus().kind == "altar"


def test_the_compass_points_at_her_great_door_never_her_back_door():
    """From her garden the choir's back door lies nearer, but it is no way in: the compass keeps to the
    great door at the nave's head."""
    _game, world = city(at=(38, 25), keep_foes=True)
    assert world.boss_target() == TileMap.center(21, 29)
