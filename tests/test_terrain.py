import math

import pytest

from ashen_vault.player.stats import Stats
from ashen_vault.world import collision, terrain
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap

RIVER = """[meta]
name = River
start = 1 1 0

[legend]
# = wall
. = floor h=0
- = floor h=-0.2 slow=0.5
w = floor h=-0.2 flow=0,2.0
* = floor h=0 hurt=5
~ = water h=-0.5

[grid]
#########
#.~~~~..#
#.~~~~-.#
#.R~~~..#
#.~K~~*.#
#.www...#
#.~~~~..#
#########

[entities]
R = raft to=5,3 speed=2 on=~
K = plank on=~
"""


class Body:
    RADIUS = 0.4

    def __init__(self, tx, tz):
        self.x, self.z = TileMap.center(tx, tz)
        self.y = 0.0
        self.stats = Stats()


@pytest.fixture
def river():
    m = MapLoader(RIVER, name="river").parse()
    return m, terrain.Terrain(m)


def run(h, body, seconds, dt=0.05):
    hits = []
    events = []
    for _ in range(round(seconds / dt)):
        events.append(h.update(dt, body, lambda dmg, src: hits.append((dmg, src))))
    return hits, events


def test_loader_reads_hazard_tiles(river):
    m, _ = river
    assert m[6, 2].slow == 0.5
    assert m[2, 5].flow == (0.0, 2.0)
    assert m[6, 4].hurt == 5
    assert m[2, 5].hazardous and m[6, 4].hazardous and m[2, 1].hazardous
    assert not m[1, 1].hazardous


def test_platforms_are_built_from_entities_not_props(river):
    _, h = river
    kinds = sorted(p.kind for p in h.platforms)
    assert kinds == ["plank", "raft"]
    raft = next(p for p in h.platforms if p.kind == "raft")
    assert (raft.bx, raft.bz) == TileMap.center(5, 3)
    assert raft.deck == pytest.approx(-0.5 + terrain.DECK)


def test_you_can_step_onto_a_raft_but_not_onto_open_water(river):
    m, h = river
    x, z = TileMap.center(1, 3)
    nx, _ = collision.move(m, x, z, 1.5, 0, 0.4, floating=h.floating)
    assert nx == pytest.approx(x + 1.5)
    x, z = TileMap.center(1, 1)
    nx, _ = collision.move(m, x, z, 1.5, 0, 0.4, floating=h.floating)
    assert nx < 4.0


def test_raft_ferries_its_passenger_across(river):
    _, h = river
    body = Body(2, 3)
    run(h, body, terrain.RAFT_PAUSE + 0.1)
    start = body.x
    hits, _ = run(h, body, 3.0)  # 6 m at 2 m/s
    assert body.x == pytest.approx(start + 6.0, abs=0.05)
    assert hits == []
    assert h.floor(body.x, body.z) == pytest.approx(-0.2)


def test_rotten_plank_gives_way_and_the_river_throws_you_back(river):
    _, h = river
    h.safe = TileMap.center(1, 4)
    body = Body(3, 4)
    plank = next(p for p in h.platforms if p.kind == "plank")
    hits, events = run(h, body, terrain.PLANK_CREAK + 0.1)
    assert not plank.afloat
    assert "fell" in events
    assert hits and hits[0][1] == "The river"
    assert (body.x, body.z) == TileMap.center(1, 4)
    run(h, Body(1, 1), terrain.PLANK_SUNK)
    assert plank.afloat


def test_stepping_off_a_plank_in_time_saves_it(river):
    _, h = river
    plank = next(p for p in h.platforms if p.kind == "plank")
    body = Body(3, 4)
    run(h, body, terrain.PLANK_CREAK * 0.6)
    body.x, body.z = TileMap.center(1, 4)
    run(h, body, 2.0)
    assert plank.afloat and plank.load_t == 0


def test_current_sweeps_you_off_the_ford(river):
    _, h = river
    h.safe = TileMap.center(1, 5)
    body = Body(3, 5)
    _, events = run(h, body, 1.5)
    assert "fell" in events
    assert (body.x, body.z) == TileMap.center(1, 5)


def test_thorns_prick_on_a_timer(river):
    _, h = river
    body = Body(6, 4)
    hits, _ = run(h, body, terrain.THORN_TICK * 3 - 0.01)
    assert [d for d, _ in hits] == [5, 5, 5]
    assert all(src == "Thorns" for _, src in hits)


def test_safe_ground_is_remembered_and_hazards_are_not(river):
    _, h = river
    run(h, Body(1, 2), 0.1)
    assert h.safe == TileMap.center(1, 2)
    run(h, Body(6, 4), 0.1)
    assert h.safe == TileMap.center(1, 2)


def test_fall_without_safe_ground_returns_you_to_the_start(river):
    _, h = river
    body = Body(4, 1)
    _, events = run(h, body, 0.05)
    assert events == ["fell"]
    assert (body.x, body.z) == TileMap.center(1, 1)


def test_mud_slows_the_player(river):
    from ashen_vault.player.player import Player

    m, _ = river
    fast, slow = Player(), Player()
    fast.place(*TileMap.center(7, 1), 1.5708, m)
    slow.place(*TileMap.center(6, 2), 1.5708, m)
    fast.walk(m, 1, 0, 0.1)
    slow.walk(m, 1, 0, 0.1)
    assert (slow.z - TileMap.center(6, 2)[1]) == pytest.approx((fast.z - TileMap.center(7, 1)[1]) * 0.5)


def test_verdant_hollow_has_its_river():
    from ashen_vault import map_path

    m = MapLoader.load_file(map_path("verdant_hollow"))
    h = terrain.Terrain(m)
    assert {p.kind for p in h.platforms} == {"raft", "plank", "ledge", "boards"}
    for p in h.platforms:
        tx, tz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        assert m[tx, tz].needs_footing or p.kind == "boards"
    assert any(t.flow for _, _, t in m.each_tile())
    assert any(t.hurt for _, _, t in m.each_tile())


HIGHLAND = """[meta]
name = Highland
start = 1 1 0

[legend]
# = wall
. = floor h=0
g = floor h=3.2
3 = floor h=1.6
_ = floor h=-5 chasm
e = floor h=0.8

[grid]
#########
#..___..#
#..___..#
#gggeeg.#
#g.....3#
#########

[entities]
X = ledge deck=0 on=_
b = boards deck=3.2 on=e
J = log_chute to=1,4 every=1.0 speed=4 on=3
P = spore_pod every=3 on=.
"""


def highland(grid_patch=None):
    text = HIGHLAND
    if grid_patch:
        for old, new in grid_patch:
            text = text.replace(old, new, 1)
    m = MapLoader(text, name="highland").parse()
    return m, terrain.Terrain(m)


def test_pits_need_footing_and_ledges_span_them():
    m, h = highland([("#..___..#\n#..", "#..X__..#\n#..")])
    assert m[3, 1].chasm and m[3, 1].hazardous and m[3, 1].needs_footing
    assert not collision.passable(m, 4, 1, 0.0)
    assert collision.passable(m, 3, 1, 0.0, floating=h.floating)
    ledge = h.platforms[0]
    assert ledge.kind == "ledge" and ledge.deck == 0.0
    # Standing on the ledge you stand at its deck, so you can step back off onto the bank.
    x, z = TileMap.center(3, 1)
    assert h.floor(x, z) == 0.0
    nx, _ = collision.move(m, x, z, -1.2, 0, 0.4, floating=h.floating, ground=h.floor)
    assert nx < x - 1.0


def test_a_ledge_crumbles_and_drops_you_into_the_ravine():
    _m, h = highland([("#..___..#\n#..", "#..X__..#\n#..")])
    body = Body(2, 1)
    run(h, body, 0.1)  # stood on the bank: that is the safe ground
    body.x, body.z = TileMap.center(3, 1)
    hits, events = run(h, body, terrain.LEDGE_CREAK + 0.1)
    assert "fell" in events and h.fell_into == "ravine"
    assert hits[-1][1] == "The ravine"
    assert (body.x, body.z) == TileMap.center(2, 1)
    ledge = h.platforms[0]
    assert ledge.sink > 0
    run(h, Body(1, 4), terrain.LEDGE_GONE)
    assert ledge.afloat and ledge.sink == 0


def test_rotten_boards_break_for_good_and_you_land_hard():
    _m, h = highland([("#gggeeg.#", "#gggbeg.#")])
    body = Body(3, 3)
    body.y = 3.2
    run(h, body, 0.1)
    body.x, body.z = TileMap.center(4, 3)
    hits, events = run(h, body, terrain.BOARDS_CREAK + 0.1)
    assert "landed" in events
    (dmg, src) = hits[-1]
    assert src == "The fall"
    assert dmg == round((3.2 - 0.8 - terrain.FALL_SAFE) * terrain.FALL_PER_M)
    boards = h.platforms[0]
    run(h, Body(1, 4), 100)
    assert not boards.afloat
    assert boards.sink == pytest.approx(3.2 - 0.8 - 0.08)


def test_small_drops_and_teleports_do_not_hurt():
    _m, h = highland()
    body = Body(7, 4)
    body.y = 1.6
    run(h, body, 0.1)
    body.x -= 1.2  # step down 1.6 m onto the floor
    assert TileMap.tile_coord(body.x) == 6
    hits, _ = run(h, body, 0.1)
    assert hits == []
    body.x, body.z = TileMap.center(1, 3)
    run(h, body, 0.1)
    body.x, body.z = TileMap.center(1, 4)  # a 3.2 m drop, but 2 m away in one frame: a teleport
    hits, _ = run(h, body, 0.05)
    assert hits == []


def test_rolling_logs_strike_once_and_shove_you_downhill():
    _, h = highland([("#g.....3#", "#g.....J#")])
    chute = h.chutes[0]
    assert (chute.x, chute.z) == TileMap.center(7, 4)
    body = Body(4, 4)
    hits, events = run(h, body, 2.6)
    assert ("A rolling log" in [s for _, s in hits]) and "log" in events
    assert body.x < TileMap.center(4, 4)[0] - 1.0  # shoved along the lane
    assert [s for _, s in hits].count("A rolling log") == 1


def test_logs_miss_you_in_a_side_notch():
    _, h = highland([("#g.....3#", "#g.....J#")])
    body = Body(4, 3)  # a tile beside the lane
    body.y = 0.8
    h.chutes[0].t = 0.99
    hits, _ = run(h, body, 2.0)
    assert "A rolling log" not in [s for _, s in hits]
    assert h.logs  # the log is still rolling along the lane


def test_spore_clouds_choke_and_slow():
    _m, h = highland([("#g.....3#", "#g..P..3#")])
    body = Body(4, 4)
    body.spore_t = 0.0
    pod = h.pods[0]
    assert pod.cloud == 0.0
    hits, events = run(h, body, 0.1)
    assert events[0] == "spores"
    assert body.spore_t == pytest.approx(terrain.SPORE_LINGER)
    assert hits == [(terrain.SPORE_DAMAGE, "Spores")]
    run(h, body, terrain.SPORE_TIME)  # the cloud settles
    assert pod.cloud is None
    far = Body(1, 1)
    far.spore_t = 0.0
    pod.t = 0.0
    hits, _ = run(h, far, 0.2)
    assert hits == [] and far.spore_t == 0.0


def test_spores_slow_the_player():
    from ashen_vault.player.player import Player

    m, _ = highland()
    a, b = Player(), Player()
    a.place(*TileMap.center(2, 4), 1.5708, m)
    b.place(*TileMap.center(2, 4), 1.5708, m)
    b.spore_t = 1.0
    a.walk(m, 1, 0, 0.1)
    b.walk(m, 1, 0, 0.1)
    start = TileMap.center(2, 4)[1]
    assert (b.z - start) == pytest.approx((a.z - start) * Player.SPORED)


def test_walking_under_floorboards_in_the_cellar_keeps_you_on_the_cellar_floor():
    # Regression: a deck above you used to count as footing, lifting you onto the boards (which then
    # broke and dropped you for fall damage).
    _, h = highland([("#gggeeg.#", "#gggbbg.#")])
    body = Body(4, 3)
    h.platforms[0].sunk_t = math.inf  # you broke the first board and fell through
    body.y = 0.8
    run(h, body, 0.1)
    body.x, body.z = TileMap.center(5, 3)  # under the second, intact board
    hits, events = run(h, body, 1.0)
    assert hits == [] and events == [None] * len(events)
    assert h.floor(body.x, body.z) == pytest.approx(0.8)
    assert h.platforms[1].afloat


def _lane():
    _, h = highland([("#g.....3#", "#g.....J#")])
    return h, h.chutes[0]


def test_the_log_pile_waits_until_someone_climbs_the_slope():
    h, chute = _lane()
    hits, _ = run(h, Body(1, 1), 10)  # nowhere near the slope
    assert chute.stock == terrain.LOG_STOCK and not h.logs and hits == []
    assert not chute.on_slope(*TileMap.center(7, 4))  # the pile's own tile is not the slope
    assert chute.on_slope(*TileMap.center(5, 4)) and chute.on_slope(*TileMap.center(5, 3))


def test_the_pile_warns_you_then_runs_out():
    h, chute = _lane()
    body = Body(5, 3)  # in a notch beside the lane, so the logs miss
    body.y = 0.8
    _, events = run(h, body, terrain.LOG_WARN - 0.1)
    assert not h.logs
    _, events = run(h, body, 0.2)
    assert "logs_first" in events and chute.stock == terrain.LOG_STOCK - 1
    _, events = run(h, body, chute.every * terrain.LOG_STOCK)
    assert "logs_last" in events and chute.stock == 0
    run(h, body, 10)
    assert not h.logs  # the last one rolled away and no more come


def test_leaving_the_slope_stops_the_pile():
    h, chute = _lane()
    body = Body(5, 3)
    run(h, body, terrain.LOG_WARN + 0.1)
    left = chute.stock
    body.x, body.z = TileMap.center(1, 1)
    run(h, body, 20)
    assert chute.stock == left


def test_pit_traps_are_left_to_the_world():
    # The dungeon's pits hurt you through the World's own fall handling, so no hard landing on top.
    text = HIGHLAND.replace("e = floor h=0.8", "e = floor h=-3 pit")
    m = MapLoader(text, name="pits").parse()
    h = terrain.Terrain(m)
    body = Body(3, 3)
    body.x = 7.8  # the east edge of the solid tile
    body.y = 3.2
    run(h, body, 0.1)
    body.x = 8.3  # half a metre on: over the rim and down 6.2 m into the pit
    assert m.tile_at(body.x, body.z).pit
    hits, events = run(h, body, 0.1)
    assert hits == [] and "landed" not in events
    # The same drop onto plain floor would hurt.
    m2 = MapLoader(HIGHLAND, name="drop").parse()
    h2 = terrain.Terrain(m2)
    body = Body(3, 3)
    body.x, body.y = 7.8, 3.2
    run(h2, body, 0.1)
    body.x = 8.3
    _, events = run(h2, body, 0.1)
    assert "landed" in events
