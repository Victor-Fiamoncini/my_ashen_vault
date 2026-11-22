import json

import pytest

from ashen_vault.player.combat import Combat, Gauge, Stamina
from ashen_vault.player.inventory import SPELL, Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.player.stats import BASE_ST, ST_PER_LEVEL, Stats
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.world.tile_map import TileMap


def test_gauge_refills_and_spend_returns_fill():
    g = Gauge(2.0)
    assert g.spend() == pytest.approx(1.0)
    g.update(1.0)
    assert g.value == pytest.approx(0.5)
    g.update(5.0)
    assert g.full


def test_low_gauge_swings_are_weak():
    full = Combat.damage(base=8, strength=6, gauge=1.0, defense=0)
    half = Combat.damage(base=8, strength=6, gauge=0.5, defense=0)
    empty = Combat.damage(base=8, strength=6, gauge=0.0, defense=0)
    assert full == 11
    assert half < full / 2.0 + 1
    assert empty >= 1


def test_defense_never_drops_damage_below_one():
    assert Combat.damage(base=1, strength=0, gauge=0.1, defense=50) == 1


def test_level_up():
    s = Stats()
    gained = s.gain_exp(Stats.exp_for(1) + Stats.exp_for(2))
    assert gained == 2
    assert s.level == 3
    assert s.hp == s.max_hp
    assert s.max_hp == 52
    assert s.max_st == BASE_ST + 2 * ST_PER_LEVEL


def test_an_old_save_without_max_st_gets_what_its_level_gives():
    assert Stats.from_h({"level": 5}).max_st == BASE_ST + 4 * ST_PER_LEVEL
    assert Stats.from_h({"level": 5, "max_st": 140}).max_st == 140
    assert Stats.from_h(Stats(level=4).to_h()).max_st == BASE_ST + 3 * ST_PER_LEVEL


def test_a_bigger_stamina_bar_refills_in_the_same_time_and_sprints_longer():
    small, big = Stamina(), Stamina(lambda: 1.5)
    assert big.value == pytest.approx(1.5)
    for st in (small, big):
        st.spend(st.value)
        st.update(Stamina.REFILL_DELAY + Stamina.REFILL_TIME / 2)
    assert big.value == pytest.approx(0.75) and small.value == pytest.approx(0.5)
    assert big.share == pytest.approx(small.share)
    small.fill()
    big.fill()
    for st in (small, big):
        st.drain(Stamina.DRAIN_TIME)
    assert small.exhausted and not big.exhausted


def test_the_players_stamina_follows_its_level():
    p = Player(stats=Stats(level=11))
    assert p.stamina.value == pytest.approx((BASE_ST + 10 * ST_PER_LEVEL) / BASE_ST)
    p.stamina.spend(1.0)
    p.stats.gain_exp(Stats.exp_for(11))
    p.stamina.fill()
    assert p.stamina.value == pytest.approx((BASE_ST + 11 * ST_PER_LEVEL) / BASE_ST)


def test_inventory_equip_and_buy():
    inv = Inventory(gold=200)
    assert inv.has("rusted_sword")
    assert inv.buy("ashblade")
    assert inv.gold == 20
    assert not inv.buy("ringmail")
    assert inv.equip("ashblade")
    assert inv.weapon_item().power == 15
    assert not inv.equip("red_tonic")


def test_unequip_falls_back_to_fists_and_no_armor():
    inv = Inventory()
    assert not inv.unequip("red_tonic")
    assert inv.unequip("rusted_sword")
    assert inv.unequip("padded_coat")
    assert inv.right is None
    assert inv.hand_item("right") == Items.FISTS
    assert inv.defense == 0
    assert inv.has("rusted_sword"), "unequipping keeps the item"
    assert inv.equip("rusted_sword")
    assert inv.equipped("rusted_sword")

    restored = Inventory.from_h(Inventory(right=None, left=None, body=None).to_h())
    assert restored.right is None and restored.left is None
    assert restored.body is None


def test_hands_hold_weapons_shields_and_the_spell():
    inv = Inventory()
    assert inv.right == "rusted_sword" and inv.left == SPELL
    assert inv.hand_item("left").kind == "spell"
    inv.add("buckler")
    assert inv.equip("buckler")
    assert inv.left == "buckler" and inv.shield_hand() == "left"
    # One sword can't be in both hands; it moves.
    assert inv.equip("rusted_sword", "left")
    assert inv.left == "rusted_sword" and inv.right is None
    inv.add("rusted_sword")
    assert inv.equip("rusted_sword", "right")
    assert inv.right == inv.left == "rusted_sword", "carrying two lets you dual-wield"
    assert inv.equip(SPELL, "right")
    assert inv.right == SPELL


def test_two_handers_fill_both_hands():
    inv = Inventory()
    inv.add("claymore")
    inv.add("buckler")
    assert inv.equip("claymore", "left")
    assert inv.right == inv.left == "claymore" and inv.two_handing()
    assert inv.equip("buckler")
    assert inv.left == "buckler" and inv.right is None, "a shield takes the two-hander off"
    assert Inventory(right="claymore").left == "claymore"


def test_level_gates_equipment():
    inv = Inventory()
    inv.add("katana")
    assert inv.equip_error("katana", level=1) == "level"
    assert not inv.equip("katana", level=4)
    assert inv.equip("katana", level=5)
    assert inv.equip_error("red_tonic") == "missing"
    inv.add("red_tonic")
    assert inv.equip_error("red_tonic") == "kind"


def test_body_armor_and_gauntlets_add_up():
    inv = Inventory()
    inv.add("iron_gauntlets")
    assert inv.equip("iron_gauntlets")
    assert inv.hands == "iron_gauntlets" and inv.body == "padded_coat"
    assert inv.defense == Items.get("padded_coat").power + Items.get("iron_gauntlets").power


def test_old_saves_put_the_weapon_right_and_the_spell_left():
    inv = Inventory.from_h({"counts": {"ashblade": 1}, "weapon": "ashblade", "armor": None, "gold": 5})
    assert inv.right == "ashblade" and inv.left == SPELL and inv.body is None
    again = Inventory.from_h(inv.to_h())
    assert again.slots == inv.slots and again.gold == 5


def test_inventory_remove():
    inv = Inventory()
    inv.add("red_tonic", 2)
    assert inv.remove("red_tonic")
    assert inv.count("red_tonic") == 1
    assert inv.remove("red_tonic")
    assert not inv.has("red_tonic")
    assert not inv.remove("red_tonic")


def test_save_round_trip(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.x = 3.5
    player.z = 7.25
    player.stats.gain_exp(100)
    player.inventory.add("red_tonic", 3)
    player.spells.append("mend")
    saves.save(map="harrowmere", player=player, flags={"chest:a"})

    map_name, loaded, flags = saves.load()
    assert map_name == "harrowmere"
    assert loaded.z == pytest.approx(7.25)
    assert loaded.stats.level == player.stats.level
    assert loaded.inventory.count("red_tonic") == 3
    assert loaded.spells == ["flame", "mend"]
    assert "chest:a" in flags


def test_corrupt_save_returns_none(tmp_path):
    path = tmp_path / "save.json"
    path.write_text("{nope")
    assert SaveSystem(str(path)).load() is None


def test_save_path_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ASHEN_VAULT_SAVE", str(tmp_path / "x.json"))
    assert SaveSystem().path == str(tmp_path / "x.json")


def test_sprint_is_faster_drains_stamina_and_keeps_attack_gauge_filling(room):
    x, z = TileMap.center(1, 2)
    walker = Player()
    runner = Player()
    for p in (walker, runner):
        p.place(x, z, 0.0, room)
    walker.walk(room, 1, 0, 0.1)
    runner.walk(room, 1, 0, 0.1, sprint=True)
    assert (runner.x - x) / (walker.x - x) == pytest.approx(Player.SPRINT, abs=1e-6)
    assert runner.sprinting
    assert not walker.sprinting
    assert runner.stamina.value < 1.0
    assert walker.stamina.value == pytest.approx(1.0)

    runner.attack_gauge.spend()
    runner.update_timers(0.5)
    assert runner.attack_gauge.value > 0


def test_exhausted_player_moves_at_walking_speed(room):
    x, z = TileMap.center(1, 2)
    tired = Player()
    tired.place(x, z, 0.0, room)
    tired.stamina.drain(Stamina.DRAIN_TIME)
    assert tired.stamina.exhausted
    walker = Player()
    walker.place(x, z, 0.0, room)
    walker.walk(room, 1, 0, 0.1)
    tired.walk(room, 1, 0, 0.1, sprint=True)
    assert not tired.sprinting
    assert tired.x == pytest.approx(walker.x)


def test_stamina_exhaustion_and_recovery():
    st = Stamina()
    assert st.can_sprint
    st.drain(Stamina.DRAIN_TIME / 2)
    assert st.value == pytest.approx(0.5)
    st.update(Stamina.REFILL_DELAY / 2)
    assert st.value == pytest.approx(0.5)  # no refill before the rest delay
    st.drain(Stamina.DRAIN_TIME)
    assert st.value == 0
    assert st.exhausted
    assert not st.can_sprint
    st.update(Stamina.REFILL_DELAY)
    st.update(Stamina.REFILL_TIME * 0.2)
    assert 0 < st.value < Stamina.RECOVER
    assert st.exhausted
    st.update(Stamina.REFILL_TIME * 0.2)
    assert not st.exhausted
    assert st.can_sprint
    st.fill()
    assert st.value == 1.0


def test_gauge_full_t_tracks_time_since_full():
    g = Gauge(1.0)
    g.spend()
    assert g.full_t == 0
    g.update(1.0)
    assert g.full
    assert g.full_t == 0
    g.update(0.25)
    assert g.full_t == pytest.approx(0.25)


def test_cycle_spell_wraps_both_ways():
    p = Player()
    assert p.cycle_spell() is None, "one spell: nothing to switch to"
    p.spells += ["mend", "lumen"]
    assert p.cycle_spell().id == "mend"
    assert p.cycle_spell(-1).id == "flame"
    assert p.cycle_spell(-1).id == "lumen"
    assert p.cycle_spell().id == "flame"


def test_the_wheel_cycles_only_the_filled_quick_slots():
    p = Player()
    assert p.quick_slots == ["red_tonic", "blue_moss", None, None]
    assert p.quick_item().id == "red_tonic"
    assert p.cycle_quick().id == "blue_moss", "the wheel works even with empty pockets"
    assert p.cycle_quick().id == "red_tonic", "empty slots are skipped"
    assert p.cycle_quick(-1).id == "blue_moss"
    p.assign_quick(3, "bitter_root")
    assert p.cycle_quick().id == "bitter_root"
    assert p.cycle_quick().id == "red_tonic"
    p.inventory.add("blue_moss", 2)
    assert p.quick_item().id == "red_tonic", "an empty-handed slot stays selected"


def test_one_filled_quick_slot_has_nothing_to_switch_to():
    p = Player()
    p.clear_quick(1)
    assert p.cycle_quick() is None
    assert p.quick_item().id == "red_tonic"
    p.clear_quick(0)
    assert p.quick_item() is None and p.cycle_quick() is None
    p.assign_quick(2, "grave_lily")
    assert p.quick_index == 2, "an empty selection moves to the first slot filled"
    assert p.quick_item().id == "grave_lily"


def test_assigning_a_quick_item_moves_it_and_its_selection():
    p = Player()
    assert p.assign_quick(3, "red_tonic")
    assert p.quick_slots == [None, "blue_moss", None, "red_tonic"]
    assert p.quick_index == 3, "the wheel follows the item it had selected"
    p.assign_quick(1, "clotting_salve")
    assert p.quick_slots == [None, "clotting_salve", None, "red_tonic"]
    assert not p.assign_quick(0, "rusted_sword"), "only consumables go on the wheel"
    assert not p.assign_quick(0, "menders_kit")
    assert p.quick_slots[0] is None


def test_clearing_the_selected_quick_slot_moves_the_wheel_on():
    p = Player()
    p.assign_quick(2, "bitter_root")
    p.quick_index = 1
    p.clear_quick(1)
    assert p.quick_index == 2
    p.clear_quick(2)
    assert p.quick_index == 0


def test_equip_spell_readies_only_known_spells():
    p = Player()
    p.spells += ["mend", "lumen"]
    assert p.equip_spell("lumen")
    assert p.current_spell().id == "lumen"
    assert not p.equip_spell("nonsense")
    assert p.current_spell().id == "lumen"


def test_save_keeps_the_equipped_spell(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.spells.append("mend")
    player.equip_spell("mend")
    saves.save(map="harrowmere", player=player, flags=set())
    assert saves.load()[1].current_spell().id == "mend"

    data = json.loads((tmp_path / "save.json").read_text())
    del data["player"]["spell"]  # saves from before spells were equipped
    (tmp_path / "save.json").write_text(json.dumps(data))
    assert saves.load()[1].current_spell().id == "flame"


def test_save_keeps_the_quick_slots(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    player = Player()
    player.assign_quick(2, "grave_lily")
    player.clear_quick(0)
    player.quick_index = 2
    saves.save(map="harrowmere", player=player, flags=set())
    loaded = saves.load()[1]
    assert loaded.quick_slots == [None, "blue_moss", "grave_lily", None]
    assert loaded.quick_index == 2


def test_old_saves_seed_quick_slot_one_from_their_quick_item(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    saves.save(map="harrowmere", player=Player(), flags=set())
    data = json.loads((tmp_path / "save.json").read_text())
    del data["player"]["quick_slots"], data["player"]["quick_index"]
    data["player"]["quick"] = "blue_moss"  # saves from before the slots kept one quick item
    (tmp_path / "save.json").write_text(json.dumps(data))
    loaded = saves.load()[1]
    assert loaded.quick_slots == ["blue_moss", "red_tonic", None, None]
    assert loaded.quick_index == 0

    del data["player"]["quick"]
    (tmp_path / "save.json").write_text(json.dumps(data))
    assert saves.load()[1].quick_slots == ["red_tonic", "blue_moss", None, None]


def test_restored_quick_slots_drop_unknown_and_doubled_items():
    p = Player()
    p.restore_quick(
        {"quick_slots": ["grave_lily", "nonsense", "rusted_sword", "grave_lily", "x"], "quick_index": 9}
    )
    assert p.quick_slots == ["grave_lily", None, None, None]
    assert p.quick_index == 0
    p.restore_quick({"quick_slots": [None, None, "bitter_root"], "quick_index": 0})
    assert p.quick_slots == [None, None, "bitter_root", None]
    assert p.quick_index == 2, "the selection lands on a filled slot"


def test_load_spot_gives_the_saved_place(tmp_path):
    saves = SaveSystem(str(tmp_path / "save.json"))
    assert saves.load_spot() is None
    player = Player()
    player.x, player.z, player.yaw = 4.0, 9.5, 1.25
    saves.save(map="abandoned_prison", player=player, flags=set())
    assert saves.load_spot() == ("abandoned_prison", 4.0, 9.5, 1.25)


def test_revive_restores_and_clears_effects():
    p = Player()
    p.inventory.add("warden_key")
    p.stats.hurt(p.stats.max_hp)
    p.stats.mp = 0
    p.stamina.drain(10)
    p.webbed_t = p.spore_t = p.hurt_t = p.chill_t = 1.0
    p.swing_t = 0.1
    assert not p.alive
    p.revive()
    assert p.alive
    assert p.stats.hp == p.stats.max_hp and p.stats.mp == p.stats.max_mp
    assert p.stamina.value == 1.0 and not p.stamina.exhausted
    assert p.webbed_t == p.spore_t == p.hurt_t == p.chill_t == 0
    assert not p.swinging
    assert p.inventory.has("warden_key")


def test_save_keeps_both_hands_and_armor(tmp_path):
    saves = SaveSystem(str(tmp_path / "s.json"))
    player = Player()
    inv = player.inventory
    for id_ in ("claymore", "iron_gauntlets", "brigandine"):
        inv.add(id_)
        inv.equip(id_)
    saves.save(map="harrowmere", player=player, flags=set())
    _, loaded, _ = saves.load()
    assert loaded.inventory.slots == {
        "right": "claymore",
        "left": "claymore",
        "body": "brigandine",
        "hands": "iron_gauntlets",
    }


def test_ashen_ward_blunts_blows_but_never_to_nothing():
    from ashen_vault.player.spells import Spells

    for magic in range(0, 40):
        assert 0.35 <= Spells.ward_cut(magic) <= 0.6
    assert Spells.ward_cut(30) == 0.6
    assert Spells.warded(20, 5) == 11  # 45% stopped
    assert Spells.warded(1, 30) == 1  # a blow always lands
    assert Spells.warded(0, 5) == 0
    assert Spells.power("ward", 5) == 45  # the stats panel's SPL: % of each blow stopped


def test_ashen_ward_wears_off_and_a_respawn_clears_it():
    from ashen_vault.player.spells import Spells

    p = Player()
    p.ward_t = Spells.WARD_DURATION
    p.update_timers(Spells.WARD_DURATION - 1)
    assert p.ward_t == pytest.approx(1)
    p.update_timers(2)
    assert p.ward_t == 0
    p.ward_t = 5
    p.revive()
    assert p.ward_t == 0
