import json
import os
from pathlib import Path

import pytest

from ashen_vault import map_path
from ashen_vault.player.player import Player
from ashen_vault.save import slots
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world.map_loader import map_title


def test_slot_one_is_the_old_single_save_and_the_others_sit_beside_it(tmp_path):
    base = str(tmp_path / "save.json")
    assert slots.slot_path(base, 1) == base
    assert slots.slot_path(base, 2) == str(tmp_path / "save_2.json")
    assert slots.slot_path(base, 3) == str(tmp_path / "save_3.json")
    with pytest.raises(ValueError):
        slots.slot_path(base, 4)
    saves = SaveSystem(base)
    assert saves.path == base and saves.slot == 1
    assert [s.path for s in saves.all_slots()] == [slots.slot_path(base, n) for n in (1, 2, 3)]
    assert saves.in_slot(2).base == base


def test_each_slot_keeps_its_own_journey_and_play_time(tmp_path):
    base = str(tmp_path / "save.json")
    one, two = SaveSystem(base, 1), SaveSystem(base, 2)
    p = Player()
    p.play_time = 3725.5
    p.stats.level = 4
    two.save("harrowmere", p, {"ending"})
    assert not one.exists() and two.exists()
    map_name, loaded, flags = two.load()
    assert (map_name, loaded.play_time, flags) == ("harrowmere", 3725.5, {"ending"})
    summary = two.summary()
    assert (summary.slot, summary.map, summary.level, summary.play_time) == (2, "harrowmere", 4, 3725.5)
    assert one.summary() is None


def test_a_save_from_before_play_time_loads_with_none_played(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    saves.save("harrowmere", Player(), set())
    path = Path(saves.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["player"]["play_time"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert saves.load()[1].play_time == 0.0
    assert saves.summary().play_time == 0.0


def test_an_unreadable_slot_shows_as_empty(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    Path(saves.path).write_text("{not json", encoding="utf-8")
    assert saves.summary() is None


def test_continue_picks_the_slot_saved_last(tmp_path):
    base = str(tmp_path / "save.json")
    for n, at in ((1, 100), (2, 300), (3, 200)):
        s = SaveSystem(base, n)
        s.save("harrowmere", Player(), set())
        os.utime(s.path, (at, at))
    assert slots.latest(s.summary() for s in SaveSystem(base).all_slots()) == 2
    assert slots.latest([None, None, None]) is None


def test_play_time_reads_as_hours_minutes_seconds():
    assert slots.format_play_time(0) == "0:00:00"
    assert slots.format_play_time(59.9) == "0:00:59"
    assert slots.format_play_time(3725) == "1:02:05"
    assert slots.format_play_time(36000 + 61) == "10:01:01"
    assert slots.format_play_time(-5) == "0:00:00"


def test_slots_name_their_map_by_its_title(tmp_path):
    assert map_title(map_path("abandoned_prison")) == "The Abandoned Prison"
    assert map_title(str(tmp_path / "lost_halls.map")) == "Lost Halls"
    untitled = tmp_path / "bare.map"
    untitled.write_text("[meta]\nsky = dusk\n", encoding="utf-8")
    assert map_title(str(untitled)) == "Bare"


def test_a_save_from_before_the_prison_was_renamed_loads_into_it(tmp_path):
    """The Sunken Keep became the Abandoned Prison: an older save naming it by its old id wakes there,
    its remnant and its flags following it, and the slot shows the new name."""
    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.remnant = {"map": "sunken_keep", "x": 4.0, "z": 9.0, "gold": 12}
    s.save("sunken_keep", player, set())
    with open(s.path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = 1
    data["flags"] = [
        "boss_dead",
        "door:sunken_keep:15,9",
        "lift:sunken_keep:12,26",
        "loot:barrel:sunken_keep:3,4",
        "left:sunken_keep",
        "lever:crypt_winch",
        "chest:verdant_hollow:3,3",
    ]
    with open(s.path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    map_name, loaded, flags = s.load()
    assert map_name == "abandoned_prison"
    assert loaded.remnant["map"] == "abandoned_prison"
    assert flags == {
        "boss_dead",
        "door:abandoned_prison:15,9",
        "lift:abandoned_prison:12,26",
        "loot:barrel:abandoned_prison:3,4",
        "left:abandoned_prison",
        "lever:crypt_winch",
        "chest:verdant_hollow:3,3",
    }
    assert s.summary().map == "abandoned_prison"


def _old_save(s, map_name, player, flags, version):
    s.save(map_name, player, set())
    with open(s.path, encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = version
    data["flags"] = flags
    with open(s.path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_a_save_from_before_vesperholm_grew_its_crag_wakes_where_it_was_made(tmp_path):
    """Vesperholm gained twenty rows to the north, the crag behind its cathedral and Lyra's Chapel on
    it: an older save made there wakes on the same spot, its remnant and the tiles its flags name moved
    with the city; flags of other maps, and flags naming no tile, stay as they were."""
    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x, player.z = 35.0, 143.0  # the shrine on the overlook, by the old grid
    player.remnant = {"map": "vesperholm", "x": 43.0, "z": 45.0, "gold": 30}
    flags = [
        "duchess_dead",
        "lever:vesper_bridge",
        "chest:vesperholm:40,3",
        "slain:vesperholm:21,4",
        "loot:slain:vesperholm:21,4",
        "hint:vesperholm:P",
        "chest:verdant_hollow:3,3",
    ]
    _old_save(s, "vesperholm", player, flags, 2)
    _map, loaded, got = s.load()
    assert (loaded.x, loaded.z) == (35.0, 183.0)
    assert (loaded.remnant["x"], loaded.remnant["z"]) == (43.0, 85.0)
    assert got == {
        "duchess_dead",
        "lever:vesper_bridge",
        "chest:vesperholm:40,23",
        "slain:vesperholm:21,24",
        "loot:slain:vesperholm:21,24",
        "hint:vesperholm:P",
        "chest:verdant_hollow:3,3",
    }


def test_a_save_made_since_vesperholm_grew_or_elsewhere_stays_put(tmp_path):
    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x, player.z = 35.0, 183.0
    _old_save(s, "vesperholm", player, ["chest:vesperholm:40,23"], 3)
    _map, loaded, got = s.load()
    assert (loaded.x, loaded.z) == (35.0, 183.0) and got == {"chest:vesperholm:40,23"}
    player.x, player.z = 10.0, 20.0
    player.remnant = {"map": "verdant_hollow", "x": 4.0, "z": 6.0, "gold": 5}
    _old_save(s, "verdant_hollow", player, ["chest:verdant_hollow:3,3"], 2)
    _map, loaded, got = s.load()
    assert (loaded.x, loaded.z) == (10.0, 20.0) and loaded.remnant["z"] == 6.0
    assert got == {"chest:verdant_hollow:3,3"}


def test_a_save_from_the_old_town_wakes_at_the_new_towns_start(tmp_path):
    """Harrowmere was laid out anew, square inside its walls: an older save made there wakes at the cemetery
    gate, the new town's start, its remnant there too; the town's tile flags go (none of its tiles mean
    what they did), and every other flag stays."""
    from ashen_vault.save.save_system import _start_spot

    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x, player.z = 49.0, 49.0  # by the old Bell Square's shrine
    player.remnant = {"map": "harrowmere", "x": 82.0, "z": 60.0, "gold": 25}
    flags = [
        "quest",
        "maeve_gift",
        "loot:barrel:harrowmere:44,10",
        "hint:harrowmere:Z",
        "chest:vesperholm:40,23",
    ]
    _old_save(s, "harrowmere", player, flags, 4)
    map_name, loaded, got = s.load()
    start = _start_spot("harrowmere")
    assert map_name == "harrowmere"
    assert (loaded.x, loaded.z) == (start["x"], start["z"])
    assert loaded.remnant["map"] == "harrowmere" and loaded.remnant["gold"] == 25
    assert (loaded.remnant["x"], loaded.remnant["z"]) == (start["x"], start["z"])
    assert got == {"quest", "maeve_gift", "chest:vesperholm:40,23"}


def test_a_save_from_herrans_old_castle_wakes_at_the_new_ones_start_without_its_lost_things(tmp_path):
    """Herran's castle above the clouds and its spire were torn down and the castle built anew on the
    Hollow Peak: an older save made in either wakes at the new castle's start, its remnant there too;
    the old maps' tile flags go, the rest stay; and the items taken out with them are gone from the pack,
    the hands, the quick slots and the shrine store."""
    from ashen_vault.save.save_system import RETIRED_ITEMS, _start_spot

    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x, player.z = 30.0, 12.0
    player.remnant = {"map": "herrans_castle", "x": 50.0, "z": 50.0, "gold": 40}
    flags = [
        "argent_sigil_taken",
        "herran_dead",
        "chest:herrans_castle:5,6",
        "door:herran_spire:3,4",
        "fog:herran_spire:17,6",
        "left:herran_spire",
        "chest:vesperholm:40,23",
    ]
    _old_save(s, "herran_spire", player, flags, 3)
    with open(s.path, encoding="utf-8") as f:
        data = json.load(f)
    p = data["player"]
    p["inventory"]["counts"].update({"graft_draught": 2, "herran_bonesaw": 1})
    p["inventory"]["right"] = "herran_bonesaw"
    p["stash"] = {"sun_tincture": 1, "spire_key": 1}
    p["quick_slots"] = ["graft_draught", None, None, None]
    with open(s.path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    map_name, loaded, got = s.load()
    start = _start_spot("herrans_castle")
    assert map_name == "herrans_castle"
    assert (loaded.x, loaded.z) == (start["x"], start["z"])
    assert loaded.remnant["map"] == "herrans_castle" and loaded.remnant["gold"] == 40
    assert (loaded.remnant["x"], loaded.remnant["z"]) == (start["x"], start["z"])
    assert got == {"argent_sigil_taken", "herran_dead", "chest:vesperholm:40,23"}
    inv = loaded.inventory
    assert not RETIRED_ITEMS & set(inv.counts) and inv.slots["right"] is None
    assert not RETIRED_ITEMS & set(loaded.stash) and not RETIRED_ITEMS & set(filter(None, loaded.quick_slots))
    assert s.summary().map == "herrans_castle"


def test_a_save_made_in_the_new_castle_stays_put(tmp_path):
    s = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x, player.z = 9.0, 11.0
    _old_save(s, "herrans_castle", player, ["chest:herrans_castle:2,2"], 4)
    _map, loaded, got = s.load()
    assert (loaded.x, loaded.z) == (9.0, 11.0) and got == {"chest:herrans_castle:2,2"}
