"""The Cemetery of Ashes driven headless: where a new Ashen wakes, the hints that teach it to play, the
silk a flame bolt burns, and the gate that opens only once the Sexton falls."""

import math
import random

import pytest

from ashen_vault.ai.enemy import MOVES, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.player import Player
from ashen_vault.world import hints
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_verdant_world import JungleGame


def cemetery(at=None, yaw=-math.pi / 2, flags=()):
    game = JungleGame(flags)
    world = World(game, "ashen_cemetery")
    x, z, start_yaw = world.start_position()
    if at:
        x, z = TileMap.center(*at)
        start_yaw = yaw
    game.player.place(x, z, start_yaw, world.map)
    return game, world


def prop(world, kind, **props):
    return next(
        p for p in world.props if p.kind == kind and all(p.props.get(k) == v for k, v in props.items())
    )


def walk_to(game, world, tile):
    game.player.place(*TileMap.center(*tile), game.player.yaw, world.map)
    world.update(1 / 60)


def test_a_woken_ashen_has_bare_hands_and_no_spell():
    p = Player.woken()
    assert p.inventory.slots["right"] is None and p.inventory.slots["left"] is None
    assert p.spells == [] and p.current_spell() is None
    assert not p.inventory.has("rusted_sword")
    assert p.inventory.slots["body"] == "padded_coat"


def test_a_hint_shows_once_on_any_of_its_tiles_and_never_again():
    game, world = cemetery()
    world.update(1 / 60)  # the first hint waits where you wake
    assert any("walk" in m for m in game.messages)
    lane = [s for s in world.map.entities if s.kind == "hint" and s.marker == "Â"]
    assert len(lane) == 2  # both lanes of the path
    walk_to(game, world, (lane[0].tx, lane[0].tz))
    shown = len(game.messages)
    assert "Press {E} to open a chest." in game.messages
    walk_to(game, world, (lane[1].tx, lane[1].tz))  # its other tile: already shown
    walk_to(game, world, (lane[0].tx, lane[0].tz))
    assert len(game.messages) == shown
    # Reloaded (after a death, say), it stays shown.
    game2, world2 = cemetery(flags=game.flags)
    walk_to(game2, world2, (lane[0].tx, lane[0].tz))
    assert "Press {E} to open a chest." not in game2.messages


def test_hint_text_splits_into_lines_and_keeps_its_highlights():
    assert hints.lines_of("{Left mouse} strikes.|Hold it.") == ("{Left mouse} strikes.", "Hold it.")
    assert hints.lines_of("") == () and hints.lines_of(None) == ()
    m = MapLoader(
        "[meta]\nname = H\nstart = 1 1 0\ndefault = .\n\n[legend]\n# = wall\n. = floor h=0\n\n"
        '[grid]\n####\n#HH#\n####\n\n[entities]\nH = hint text="Two tiles|one hint"\n'
    ).parse()
    built = hints.build(m)
    assert set(built) == {(1, 1), (2, 1)} and len(set(built.values())) == 1
    assert hints.due(built, (1, 1), set(), "h").lines == ("Two tiles", "one hint")
    assert hints.due(built, (2, 1), {"hint:h:H"}, "h") is None
    assert hints.due(built, (3, 1), set(), "h") is None


def test_every_cemetery_hint_fits_the_screen():
    from ashen_vault.screen import W
    from ashen_vault.ui import smallfont
    from ashen_vault.util import highlight_runs

    _, world = cemetery()
    assert len({h.marker for h in world.hints.values()}) >= 10
    for h in world.hints.values():
        assert 1 <= len(h.lines) <= 2, h.marker  # the HUD shows the last three messages
        for line in h.lines:
            plain = "".join(text for text, _ in highlight_runs(line))
            assert smallfont.width(plain) <= W - 40, line


def test_a_flame_bolt_burns_the_silk_over_the_chapel_door():
    web_tile = (10, 16)
    game, world = cemetery(at=(10, 18), yaw=-math.pi / 2)
    web = prop(world, "secret_wall", model="web")
    assert (web.tx, web.tz) == web_tile and world.blocked_tile(*web_tile)
    world.fire_bolt(10)
    for _ in range(90):
        world._update_projectiles(1 / 60)
    assert web.key in game.flags and "The web shrivels in the flame." in game.messages
    for _ in range(60):
        world.update(1 / 30)
    assert not world.blocked_tile(*web_tile)


def test_the_gate_out_stays_shut_until_the_sexton_falls():
    game, world = cemetery(at=(10, 3), yaw=-math.pi / 2)
    gate = prop(world, "exit", map="harrowmere")
    assert "oneway" in gate.props and gate.props["requires"] == "sexton_dead"
    assert not world.exit_open(gate)
    warden = next(e for e in world.enemies if e.type.id == "sexton")
    assert warden.type.boss and warden.type.drop is None  # it keeps no sigil
    while warden.alive:
        game.damage_enemy(warden, 50)
    game.flags.add(warden.type.dead_flag)
    assert world.exit_open(gate)


def test_the_gate_lands_you_by_the_cemetery_gate_in_town():
    _, world = cemetery()
    gate = prop(world, "exit", map="harrowmere")
    tx, tz, _ = (int(v) for v in gate.props["at"].split(","))
    town = MapLoader.load_file(__import__("ashen_vault").map_path("harrowmere"))
    assert [int(v) for v in town.meta["start"][:2]] == [tx, tz]
    (decor,) = [s for s in town.entities if s.kind == "cemetery_gate"]
    assert (decor.tx + 1, decor.tz) == (tx, tz)  # it shuts behind you


def sexton_at(world, distance, phase2=False):
    """The Sexton, awake, `distance` metres east of you in its yard."""
    world.enemies = []
    p = world.player
    e = Enemy(EnemyTypes.get("sexton"), p.x + distance, p.z, yaw=math.pi, rng=random.Random(1))
    e.state, e.phase2 = "chase", phase2
    world.enemies.append(e)
    return e


def test_only_the_sexton_knows_its_own_moves():
    own = {"spadeful", "grasp", "knell"}
    for t in EnemyTypes.ALL.values():
        if t.id != "sexton":
            assert not own & set(t.moves + t.phase_moves), t.id
    sexton = EnemyTypes.get("sexton")
    assert {"spadeful", "grasp"} <= set(sexton.moves) and sexton.phase_moves == ("knell",)
    assert not {"pounce", "eruption"} & set(sexton.moves + sexton.phase_moves)


def test_the_sexton_picks_each_move_at_its_range():
    _, world = cemetery(at=(6, 6), yaw=0.0)
    picked = {}
    for distance, phase2 in ((1.5, False), (6.0, False), (6.0, True)):
        e = sexton_at(world, distance, phase2)
        moves = set(e.type.moves + (e.type.phase_moves if phase2 else ()))
        e.cooldowns = dict.fromkeys(moves, 0.0)
        seen = set()
        for _ in range(60):
            e.cooldowns = dict.fromkeys(moves, 0.0)
            seen.add(e._pick_move(world, distance))
        picked[(distance, phase2)] = seen
    assert {"spadeful", "grasp"} <= picked[(6.0, False)] and "knell" not in picked[(6.0, False)]
    assert "knell" in picked[(6.0, True)]
    assert not {"spadeful", "grasp"} & picked[(1.5, False)]


def test_a_spadeful_flings_five_clods_of_ash_that_clog_your_stride():
    game, world = cemetery(at=(10, 6), yaw=0.0)
    e = sexton_at(world, 6.0)
    world.enemy_fire(e, "spadeful")
    clods = [p for p in world.projectiles if p.hostile]
    assert len(clods) == 5 and all(p.effect == "ash" for p in clods)
    assert clods[0].damage == round(e.type.damage * MOVES["spadeful"][2])
    for _ in range(120):
        world._update_projectiles(1 / 60)
    assert game.player.webbed_t > 0 and "Grave ash clogs your stride!" in game.messages


def test_grasping_ash_bursts_in_a_line_toward_you_and_holds_you():
    game, world = cemetery(at=(10, 6), yaw=0.0)
    e = sexton_at(world, 6.0)
    world.grasp(e)
    hands = world.eruptions
    assert len(hands) >= 4 and all(f.style == "hands" for f in hands)
    assert all(abs(f.z - game.player.z) < 1e-6 for f in hands)  # a straight line along you
    assert min(f.x for f in hands) < game.player.x < max(f.x for f in hands) < e.x  # from it on past you
    for _ in range(180):
        world._update_fire(1 / 60)
    assert game.wounds and game.player.webbed_t > 0
    assert "Hands of ash clutch at your legs!" in game.messages


def test_the_knell_tolls_two_rings_of_embers_turned_half_a_gap_apart():
    _, world = cemetery(at=(10, 6), yaw=0.0)
    e = sexton_at(world, 3.0, phase2=True)
    e._begin_windup("knell")
    e.state, e.state_t = "attack", 0.0
    e.update(0.01, world)
    first = [math.atan2(p.dz, p.dx) for p in world.projectiles]
    assert len(first) == 10
    for _ in range(40):
        e.update(1 / 60, world)
    second = [math.atan2(p.dz, p.dx) for p in world.projectiles[10:]]
    assert len(second) == 10
    gap = math.tau / 10
    for a in second:  # each of the second ring flies between two of the first
        nearest = min(abs((a - b + math.pi) % math.tau - math.pi) for b in first)
        assert nearest == pytest.approx(gap / 2, abs=1e-6)


def test_the_mourners_stand_bowed_at_their_graves_until_you_come_close():
    _, world = cemetery()
    mourners = [e for e in world.enemies if e.type.id == "mourner"]
    assert len(mourners) == 3 and all(e.type.lurk for e in mourners)
    graves = {(s.tx, s.tz) for s in world.map.entities if s.kind in ("gravestone", "sarcophagus")}
    for m in mourners:
        tx, tz = int(m.x // 2), int(m.z // 2)
        assert any(abs(tx - gx) + abs(tz - gz) == 1 for gx, gz in graves), (tx, tz)
    m = mourners[0]
    world.player.place(m.x + 6, m.z, math.pi, world.map)
    for _ in range(30):
        world.update(1 / 30)
    assert m.state == "idle" and (m.x, m.z) == (m.home_x, m.home_z)
    world.player.place(m.x + 2.5, m.z, math.pi, world.map)
    for _ in range(10):
        world.update(1 / 30)
    assert m.state != "idle"
