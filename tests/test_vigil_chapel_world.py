"""The Vigil Chapel behind the Keystone's court in Old Harrowmere, driven headless: the sealed door in
the lift room, the way in and back out, and the Vesper Moonbrand on its altar."""

from ashen_vault import map_path
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_verdant_world import JungleGame
from test_world import BESIDE, _reachable, _spec

CHAPEL = "vigil_chapel"


def _chapel():
    return MapLoader.load_file(map_path(CHAPEL))


def _sunken():
    return MapLoader.load_file(map_path("old_harrowmere"))


def _at(exit_spec):
    tx, tz, _yaw = (int(v) for v in exit_spec.props["at"].split(","))
    return tx, tz


def test_the_chapel_door_waits_behind_the_keystone_in_the_lift_room():
    """One door leads to the chapel: in the lift room behind the Keystone's court, so it is only
    reached through the great door, and it stays shut until the Keystone falls."""
    m = _sunken()
    (door,) = _spec(m, "exit", map=CHAPEL)
    assert door.props["requires"] == "keystone_dead" and door.props["shut"]
    assert door.props["model"] == "chapel_door"
    (back,) = _spec(m, "exit", map="harrow_sewers")
    start = (back.tx + 1, back.tz)
    assert (door.tx, door.tz) not in _reachable(m, start)
    bosses = [(s.tx, s.tz) for s in _spec(m, "door", boss="keystone_dead")]
    assert (door.tx, door.tz) in _reachable(m, start, open_tiles=bosses)
    (coffer,) = _spec(m, "chest", model="coffer")
    assert m[door.tx, door.tz].floor == m[coffer.tx, coffer.tz].floor  # in the lift room, by the coffer


def test_the_chapel_door_opens_only_once_the_keystone_is_dead():
    for flags, opened in (((), False), (("keystone_dead",), True)):
        world = World(JungleGame(flags), "old_harrowmere")
        (door,) = [p for p in world.props if p.kind == "exit" and p.props.get("map") == CHAPEL]
        assert world.exit_open(door) is opened


def test_the_chapel_door_and_its_way_back_lead_to_each_other():
    """Through the door you arrive just inside the chapel, its door right behind you; going back out
    puts you in the lift room, before the door you came through."""
    sunken, chapel = _sunken(), _chapel()
    (into,) = _spec(sunken, "exit", map=CHAPEL)
    (out,) = _spec(chapel, "exit", map="old_harrowmere")
    assert _at(into) == tuple(int(v) for v in chapel.meta["start"][:2])
    assert sum(abs(a - b) for a, b in zip(_at(into), (out.tx, out.tz), strict=True)) == 1
    bx, bz = _at(out)
    assert abs(bx - into.tx) + abs(bz - into.tz) == 1 and sunken[bx, bz].walkable


def test_the_vigil_chapel_is_solvable_and_every_floor_tile_is_in_reach():
    """No enemies, no locked doors: from the door every open tile of the nave, the aisles and the
    chancel can be walked to past the pews and pillars, and you can always walk back out."""
    m = _chapel()
    assert m.meta["name"] == "The Vigil Chapel"
    assert not [s for s in m.entities if s.kind in ("door", "gate", "lift", "secret_wall")]
    start = tuple(int(v) for v in m.meta["start"][:2])
    reach = _reachable(m, start)
    (out,) = _spec(m, "exit")
    assert (out.tx, out.tz) in reach
    (altar,) = _spec(m, "altar")
    assert {(altar.tx + dx, altar.tz + dz) for dx, dz in BESIDE} & reach
    blocked = {(s.tx, s.tz) for s in m.entities if s.kind in ("pew", "pillar", "altar", "veiled_statue")}
    for tz in range(m.depth):
        for tx in range(m.width):
            if m[tx, tz].walkable and (tx, tz) not in blocked:
                assert (tx, tz) in reach, (tx, tz)
    for tile in reach:
        assert start in _reachable(m, tile), tile
    chancel = m[altar.tx, altar.tz].floor
    assert chancel > m[start].floor  # the altar stands raised, up the chancel's step


def test_the_altar_gives_up_the_vesper_moonbrand_once():
    game = JungleGame()
    world = World(game, CHAPEL)
    (altar,) = [p for p in world.props if p.kind == "altar"]
    assert altar.props["model"] == "moon" and world._interactable(altar)
    assert world.take_from_altar(altar) == "vesper_moonbrand"
    assert not world._interactable(altar)
    assert altar.key in game.flags
    again = World(JungleGame(game.flags), CHAPEL)  # a saved game finds the altar bare
    (bare,) = [p for p in again.props if p.kind == "altar"]
    assert bare.open_t > 0 and not again._interactable(bare)


def test_the_vigil_chapel_is_lit_by_moonlight():
    m = _chapel()
    kinds = [s.kind for s in m.entities]
    assert kinds.count("moon_window") >= 6 and "light" in kinds and "candles" in kinds
    assert not [s for s in m.entities if s.kind == "chest"]
    x, z = TileMap.center(*(int(v) for v in m.meta["start"][:2]))
    assert m.tile_at(x, z).floor_tex == "moon_paving"
