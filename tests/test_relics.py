from ashen_vault.world import relics
from ashen_vault.world.map_loader import MapLoader

ROOM = """[meta]
name = Relic Room
start = 1 1 0

[legend]
# = wall tex=stone_brick top=3
. = floor h=0 ceil=3

[grid]
#######
#.w.l.#
#######

[entities]
w = ashen_warden
l = loom_mother
"""


def room():
    return MapLoader(ROOM, name="relic_room").parse()


def nothing(_):
    return False


def test_ember_sigil_keeps_its_legacy_key_and_flag():
    r = relics.get("ember_sigil")
    assert (r.key, r.taken_flag) == ("sigil", "sigil_taken")


def test_verdant_sigil_has_its_own_taken_flag():
    r = relics.get("verdant_sigil")
    assert r.taken_flag not in ("sigil_taken", "boss_dead", "spider_dead")
    assert r.key != "sigil"


def test_unknown_relic_falls_back_to_its_id():
    r = relics.get("mystery")
    assert r.key == "mystery" and r.taken_flag == "mystery_taken"


def test_no_drops_while_bosses_live():
    assert relics.pending_drops(room(), set(), nothing) == []


def test_drop_lies_on_the_dead_boss_tile_only():
    assert relics.pending_drops(room(), {"boss_dead"}, nothing) == [("ember_sigil", 2, 1)]
    assert relics.pending_drops(room(), {"spider_dead"}, nothing) == [("verdant_sigil", 4, 1)]
    both = relics.pending_drops(room(), {"boss_dead", "spider_dead"}, nothing)
    assert both == [("ember_sigil", 2, 1), ("verdant_sigil", 4, 1)]


def test_taken_or_carried_relics_are_not_dropped_again():
    flags = {"boss_dead", "spider_dead"}
    relics.mark_taken("verdant_sigil", flags)
    assert relics.pending_drops(room(), flags, nothing) == [("ember_sigil", 2, 1)]
    assert relics.pending_drops(room(), flags, lambda i: i == "ember_sigil") == []
    relics.mark_taken("ember_sigil", flags)
    assert "sigil_taken" in flags


def test_mark_taken_ignores_ordinary_items():
    flags = set()
    relics.mark_taken("red_tonic", flags)
    assert flags == set()


def test_held_lists_relics_in_order():
    inv = {"verdant_sigil", "ember_sigil", "red_tonic"}
    assert relics.held(inv.__contains__) == ["ember_sigil", "verdant_sigil"]
    assert relics.held(nothing) == []
