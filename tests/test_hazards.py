import pytest

from ashen_vault.player.stats import Stats
from ashen_vault.world import collision, hazards
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
    return m, hazards.Hazards(m)


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
    assert raft.deck == pytest.approx(-0.5 + hazards.DECK)


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
    run(h, body, hazards.RAFT_PAUSE + 0.1)
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
    hits, events = run(h, body, hazards.PLANK_CREAK + 0.1)
    assert not plank.afloat
    assert "fell" in events
    assert hits and hits[0][1] == "The river"
    assert (body.x, body.z) == TileMap.center(1, 4)
    run(h, Body(1, 1), hazards.PLANK_SUNK)
    assert plank.afloat


def test_stepping_off_a_plank_in_time_saves_it(river):
    _, h = river
    plank = next(p for p in h.platforms if p.kind == "plank")
    body = Body(3, 4)
    run(h, body, hazards.PLANK_CREAK * 0.6)
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
    hits, _ = run(h, body, hazards.THORN_TICK * 3 - 0.01)
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
    h = hazards.Hazards(m)
    assert {p.kind for p in h.platforms} == {"raft", "plank"}
    for p in h.platforms:
        tx, tz = TileMap.tile_coord(p.x), TileMap.tile_coord(p.z)
        assert m[tx, tz].liquid
    assert any(t.flow for _, _, t in m.each_tile())
    assert any(t.hurt for _, _, t in m.each_tile())
