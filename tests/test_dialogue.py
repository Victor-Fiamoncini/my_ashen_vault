from ashen_vault import dialogue
from ashen_vault.player.player import Player


class FakeGame:
    def __init__(self, flags=(), items=()):
        self.flags = set(flags)
        self.player = Player()
        for i in items:
            self.player.inventory.add(i)
        self.finished = False
        self.messages = []
        self.shop_opened = None

    def finish_game(self):
        self.finished = True
        for i in ALL_SIGILS:
            self.player.inventory.remove(i)

    def message(self, text):
        self.messages.append(text)

    def open_shop(self, shop_id):
        self.shop_opened = shop_id


def talk(id_, game):
    speaker, lines, after = dialogue.for_npc(id_, game)
    assert lines and all(isinstance(l, str) and l for l in lines)
    if after:
        after(game)
    return speaker, " ".join(lines)


ALL_SIGILS = ["ember_sigil", "verdant_sigil", "iron_sigil", "argent_sigil"]
FIRST_THREE = ALL_SIGILS[:3]
TAKEN = {"sigil_taken", "verdant_sigil_taken", "iron_sigil_taken"}  # the first three, taken up


def test_odrin_intro_asks_for_all_three_sigils_and_gives_supplies():
    g = FakeGame()
    speaker, text = talk("odrin", g)
    assert speaker == "Odrin"
    assert "Ember Sigil" in text and "Verdant Sigil" in text and "Iron Sigil" in text
    assert "Cinderhold" in text and "north road" in text
    assert "quest" in g.flags
    assert g.player.inventory.gold == 60
    assert g.player.inventory.count("red_tonic") == 2
    assert not g.finished


def test_odrin_greets_a_woken_ashen_with_the_prophecy_of_four_sigils():
    """The player is one of the Ashen, woken by the bell: Odrin tells of the prophecy (four sigils to
    raise the stone king) and of the Ashen who failed before; nobody came off a boat."""
    _, text = talk("odrin", FakeGame())
    assert "bell" in text and "prophecy" in text and "four sigils" in text
    assert "Enthroned" in text and "king" in text and "cemetery" in text
    assert "boat" not in text and "traveller" not in text


def test_nobody_in_town_takes_the_ashen_for_a_sailor():
    from ashen_vault import dialogue

    for npc in ("odrin", "garrick", "ilse", "wren", "enthroned", "brannoc", "tamsin", "hollis", "pell",
                "aldous", "tobin", "fenn", "reyna"):  # fmt: skip
        _, text = talk(npc, FakeGame())
        assert "off the boat" not in text and "the tide brings" not in text, npc
    assert "fourth" in " ".join(dialogue.ENTHRONED_LINES[3])
    assert "four" in " ".join(dialogue.ENTHRONED_LINES[-1])


def test_odrin_without_sigils_gives_directions():
    g = FakeGame(flags={"quest"})
    _, text = talk("odrin", g)
    assert "well" in text and "green trail" in text and "north road" in text
    assert not g.finished


def test_odrin_with_only_the_ember_sigil_points_to_the_other_two():
    g = FakeGame(flags={"quest"}, items=["ember_sigil"])
    _, text = talk("odrin", g)
    assert "green trail" in text and "Verdant Sigil" in text
    assert "north road" in text and "Iron Sigil" in text
    assert "well in the square" not in text
    assert not g.finished
    assert g.player.inventory.has("ember_sigil")


def test_odrin_with_only_the_verdant_sigil_points_to_the_well_and_the_road():
    g = FakeGame(flags={"quest"}, items=["verdant_sigil"])
    _, text = talk("odrin", g)
    assert "well" in text and "Ember Sigil" in text and "Iron Sigil" in text
    assert not g.finished


def test_odrin_with_two_sigils_still_wants_the_third():
    g = FakeGame(flags={"quest"}, items=["ember_sigil", "verdant_sigil"])
    _, text = talk("odrin", g)
    assert not g.finished
    assert "Iron Sigil" in text and "Cinderhold" in text
    assert g.player.inventory.has("ember_sigil") and g.player.inventory.has("verdant_sigil")


def test_odrin_with_all_four_sigils_ends_the_game():
    g = FakeGame(flags={"quest", *TAKEN, "vesper_gate_open"}, items=ALL_SIGILS)
    _, text = talk("odrin", g)
    assert g.finished
    assert not any(g.player.inventory.has(i) for i in ALL_SIGILS)
    # The story closes: the moon sets over Vesperholm, and the king rang the bell from his stone.
    assert "Vesperholm" in text and "moon" in text and "rope" in text and "stone" in text
    assert "still lost" not in text


def test_odrin_with_all_four_sigils_ends_the_game_even_before_the_quest():
    g = FakeGame(items=ALL_SIGILS)
    talk("odrin", g)
    assert g.finished


def test_the_first_three_sigils_do_not_end_the_game_and_odrin_sends_you_for_the_fourth():
    """Three of the four once ended the demo; now Odrin sends you through the Vesper Gate for the fourth."""
    g = FakeGame(flags={"quest", *TAKEN}, items=FIRST_THREE)
    _, text = talk("odrin", g)
    assert not g.finished
    assert "Vesper Gate" in text and "Argent Sigil" in text and "cathedral steps" in text
    assert all(g.player.inventory.has(i) for i in FIRST_THREE)


def test_odrin_names_the_fourth_sigil_and_its_open_gate_from_the_start():
    """The Vesper Gate stands open from the start, so Odrin names the fourth sigil at the first meeting
    and points the way to it before a single sigil is taken."""
    _, text = talk("odrin", FakeGame())
    assert "Argent Sigil" in text and "Vesper Gate" in text and "Vesperholm" in text
    assert "cathedral steps" in text and "stands open" in text
    g = FakeGame(flags={"quest"}, items=["ember_sigil"])
    _, text = talk("odrin", g)
    assert dialogue.SIGIL_HINT["argent_sigil"] in text
    _, text = talk("odrin", FakeGame(flags={"quest"}))
    assert "Vesper Gate" in text


def test_odrin_reminds_about_the_argent_sigil_once_the_duchess_falls():
    g = FakeGame(flags={"quest", *TAKEN, "vesper_gate_open", "duchess_dead"}, items=FIRST_THREE)
    _, text = talk("odrin", g)
    assert "Duchess has fallen" in text and "Argent Sigil" in text
    g.flags.add("argent_sigil_taken")
    _, text = talk("odrin", g)
    assert "Duchess has fallen" not in text


def test_odrin_reminds_about_fallen_bosses_relics():
    g = FakeGame(flags={"quest", "boss_dead"})
    _, text = talk("odrin", g)
    assert "Warden" in text and "Ember Sigil" in text
    g = FakeGame(flags={"quest", "spider_dead"})
    _, text = talk("odrin", g)
    assert "Verdant Sigil" in text
    g = FakeGame(flags={"quest", "gargoyles_dead"})
    _, text = talk("odrin", g)
    assert "gargoyles" in text and "Iron Sigil" in text and "roof" in text
    g = FakeGame(flags={"quest", "boss_dead", "sigil_taken"})
    _, text = talk("odrin", g)
    assert "Warden has fallen" not in text


def test_odrin_reminds_about_a_fallen_keeper_while_you_hold_another_sigil():
    g = FakeGame(flags={"quest", "gargoyles_dead"}, items=["ember_sigil"])
    _, text = talk("odrin", g)
    assert "Iron Sigil lies up on the Cinderhold's roof" in text


def test_hollis_hints_at_the_green_trail_until_the_spider_dies():
    _, text = talk("hollis", FakeGame())
    assert "green trail" in text
    _, text = talk("hollis", FakeGame(flags={"spider_dead"}))
    assert "green trail" not in text
    _, text = talk("hollis", FakeGame(flags={"lever:north_lever"}))
    assert "north gate" in text and "green trail" in text


def test_hollis_warns_of_the_fortress_until_the_gargoyles_fall():
    _, text = talk("hollis", FakeGame())
    assert "north road" in text
    _, text = talk("hollis", FakeGame(flags={"gargoyles_dead"}))
    assert "north road" not in text


def test_pell_greets_once_then_opens_the_shop():
    g = FakeGame()
    speaker, first = talk("pell", g)
    assert speaker == "Pell" and g.shop_opened == "pell"
    assert "met_pell" in g.flags
    _, second = talk("pell", g)
    assert second != first


def test_maeve_gives_moss_once():
    g = FakeGame()
    talk("maeve", g)
    assert g.player.inventory.count("blue_moss") == 2
    talk("maeve", g)
    assert g.player.inventory.count("blue_moss") == 2


def test_unknown_npc_is_a_silent_stranger():
    speaker, _ = talk("nobody", FakeGame())
    assert speaker == "Stranger"


def test_corvane_ignores_the_green_then_sells_blades():
    g = FakeGame()
    speaker, _ = talk("corvane", g)
    assert speaker == "Hooded figure"
    assert g.shop_opened is None and "met_corvane" not in g.flags
    g.player.stats.level = dialogue.CORVANE_LEVEL
    speaker, first = talk("corvane", g)
    assert speaker == "Corvane" and g.shop_opened == "corvane"
    assert "met_corvane" in g.flags
    g.shop_opened = None
    _, second = talk("corvane", g)
    assert second != first and g.shop_opened == "corvane"


def test_katanas_moved_from_pell_to_corvane():
    from ashen_vault.player.items import Items

    assert "katana" not in dialogue.SHOPS["pell"]
    assert all(Items.get(i).category == "katana" for i in dialogue.SHOPS["corvane"])
    for shop in dialogue.SHOPS.values():
        assert all(i in Items.ALL for i in shop)
    assert set(dialogue.SHOPS) == set(dialogue.SHOP_NAMES)


OLD_PELL_STOCK = [
    "red_tonic", "blue_moss", "scroll_mend", "leather_gloves", "oak_cudgel", "buckler", "hatchet",
    "leather_whip", "round_shield", "bastard_sword", "mace", "chain_mitts", "ringmail", "spiked_club",
    "ashblade", "lamellar_vest", "thornlash", "kite_shield", "iron_gauntlets", "bearded_axe", "brigandine",
    "zweihander", "tower_shield", "blackened_plate",
]  # fmt: skip


def test_pells_old_stock_is_split_between_the_smith_the_herbalist_and_pell():
    from ashen_vault.player.items import Items

    town = ("pell", "brannoc", "tamsin")
    for id_ in OLD_PELL_STOCK:
        assert sum(id_ in dialogue.SHOPS[s] for s in town) == 1, id_
    assert all(
        Items.get(i).kind in ("weapon", "shield", "armor", "repair") for i in dialogue.SHOPS["brannoc"]
    )
    assert all(Items.get(i).kind == "consumable" for i in dialogue.SHOPS["tamsin"])
    assert {"red_tonic", "blue_moss", "bitter_root", "clotting_salve", "grave_lily", "ember_draught"} == set(
        dialogue.SHOPS["tamsin"]
    )


def test_shopkeepers_open_their_own_shops():
    for id_, speaker in (("brannoc", "Brannoc"), ("tamsin", "Tamsin")):
        g = FakeGame()
        got, _ = talk(id_, g)
        assert got == speaker and g.shop_opened == id_


def test_each_villager_gives_their_gift_once():
    gifts = {
        "brannoc": {"hatchet": 1},
        "garrick": {"buckler": 1},
        "tamsin": {"red_tonic": 2, "blue_moss": 1},
        "ilse": {"scroll_lumen": 1},
    }
    for id_, items in gifts.items():
        g = FakeGame()
        _, first = talk(id_, g)
        assert f"gift:{id_}" in g.flags
        for item, n in items.items():
            assert g.player.inventory.count(item) == n, (id_, item)
        assert g.messages and g.messages[-1].startswith("Received {")
        _, second = talk(id_, g)
        assert second != first
        for item, n in items.items():
            assert g.player.inventory.count(item) == n, (id_, item)


def test_the_innkeeper_talks_of_the_bell_and_the_three_roads():
    g = FakeGame()
    _, first = talk("wren", g)
    assert "bell" in first.lower() and "met_wren" in g.flags
    _, second = talk("wren", g)
    assert second != first


def test_the_enthroned_stirs_a_little_more_with_each_sigil_held():
    texts = []
    for n in range(len(ALL_SIGILS) + 1):
        speaker, text = talk("enthroned", FakeGame(items=ALL_SIGILS[:n]))
        assert speaker == "The Enthroned"
        texts.append(text)
    assert len(set(texts)) == len(dialogue.ENTHRONED_LINES) == 5
    # Three held: his sister and the moon beyond the gate. All four: it was he who rang the bell.
    assert "sister" in texts[3] and "moon" in texts[3] and "gate" in texts[3]
    assert "rang the bell" in texts[4] and "ash" in texts[4]


def test_the_watch_talks_of_the_road_its_gate_keeps():
    for id_ in dialogue.WATCH:
        speaker, text = talk(id_, FakeGame())
        assert speaker != "Stranger" and text != "...", id_
    assert "north road" in talk("aldous", FakeGame())[1]
    assert talk("aldous", FakeGame()) != talk("aldous", FakeGame(flags={"gargoyles_dead"}))
    assert "cave" in talk("reyna", FakeGame())[1]
    assert talk("reyna", FakeGame()) != talk("reyna", FakeGame(flags={"spider_dead"}))
    assert "cemetery" in talk("fenn", FakeGame())[1]


def test_marrow_speaks_through_his_bars_then_gives_his_tonics_once_let_out():
    g = FakeGame()
    speaker, text = talk("marrow", g)
    assert speaker == "Brother Marrow" and "Warden's Key" in text and "lever" in text
    assert g.player.inventory.count("red_tonic") == 0 and "gift:marrow" not in g.flags
    g.flags.add(dialogue.MARROW_FREED)  # his cell's lever pulled in the warders' quarters
    before = g.player.inventory.count("red_tonic")
    talk("marrow", g)
    assert g.player.inventory.count("red_tonic") == before + 2 and "gift:marrow" in g.flags
    _speaker, later = talk("marrow", g)
    assert g.player.inventory.count("red_tonic") == before + 2 and "Warden" in later


def test_the_oubliettes_prisoners_talk_through_the_bars_and_change_once_freed():
    g = FakeGame()
    speaker, before = talk("aubel", g)
    assert speaker == "Aubel the Ringer" and "lever" in before
    speaker, _ = talk("ysolde", g)
    assert speaker == "Ysolde Vane" and g.shop_opened is None  # nothing to sell through the bars
    g.flags.add(dialogue.OUBLIETTE_OPEN)
    _, after = talk("aubel", g)
    assert after != before and "ward-stone" in after
    talk("ysolde", g)
    assert g.shop_opened == "ysolde" and "met_ysolde" in g.flags
    _, first = talk("coldry", g)
    _, second = talk("coldry", g)
    assert first != second
    g.flags.add(dialogue.KEYSTONE_DEAD)
    for id_ in ("aubel", "coldry"):
        _, done = talk(id_, g)
        assert "broken" in done or "still" in done


def test_ysolde_sells_the_only_copies_of_her_spells():
    from ashen_vault.player.items import Items

    stock = dialogue.SHOPS["ysolde"]
    spells = {Items.get(i).spell for i in stock if Items.get(i).kind == "scroll"}
    assert spells == {"rift_lance", "bellward"}
    for shop, items in dialogue.SHOPS.items():
        if shop != "ysolde":
            assert not {"scroll_rift_lance", "scroll_bellward"} & set(items)


# --- the Oubliette and the Under-Cells: the mortar-light, the roads, and the story gifts -------------

FREED = dialogue.OUBLIETTE_OPEN
QUENCHED = dialogue.CORE_QUENCHED
DEAD = dialogue.KEYSTONE_DEAD
BELOW = dialogue.UNDERCELLS


def test_aubel_tells_of_the_mortar_light_the_roads_and_brannick():
    _, bars = talk("aubel", FakeGame())
    _, bars_below = talk("aubel", FakeGame(flags={BELOW}))
    assert bars != bars_below and "Under-Cells" in bars_below
    _, freed = talk("aubel", FakeGame(flags={FREED}))
    assert "mortar-light" in freed and "ward-stone" in freed and "Coldry" in freed
    _, below = talk("aubel", FakeGame(flags={FREED, BELOW}))
    assert "Brannick" in below and "Brannick" not in freed
    _, quenched = talk("aubel", FakeGame(flags={FREED, QUENCHED}))
    assert "teal glow has gone" in quenched and "shield" not in quenched
    _, struck = talk("aubel", FakeGame(flags={FREED, dialogue.WARD_KEY}))
    assert "heard you at the ward-stones" in struck
    _, struck_c = talk("aubel", FakeGame(flags={FREED, dialogue.WARD_KEY + ":c"}))
    assert struck_c == struck


def test_aubel_gives_the_keepers_tithe_once_when_the_keystone_falls():
    g = FakeGame(flags={FREED})
    talk("aubel", g)
    assert "gift:aubel" not in g.flags and g.player.inventory.gold == 0
    g.flags.add(DEAD)
    _, text = talk("aubel", g)
    assert "tithe" in text and "gift:aubel" in g.flags
    assert g.player.inventory.gold == 600 and g.player.inventory.count("red_tonic") == 2
    assert g.player.inventory.count("menders_kit") == 1
    assert g.messages[-1] == "Received {600 gold} and {2 Red Tonics} and {Mender's Kit}."
    _, later = talk("aubel", g)
    assert later != text and "still" in later and "mortar-light still burns" in later
    assert g.player.inventory.gold == 600
    g.flags.add(QUENCHED)
    _, both = talk("aubel", g)
    assert "teal light is out" in both


def test_coldry_explains_the_third_teal_road_and_the_core_s_shield():
    g = FakeGame(flags={FREED})
    _, first = talk("coldry", g)
    assert "mortar-light" in first and "ward-stones" in first
    _, second = talk("coldry", g)
    assert "teal road" in second and "Three roads" in second
    assert "shield" in second and "drops only while the teal road stands" in second
    assert "heavy" in second
    g.flags.add(dialogue.WARD_KEY)
    _, struck = talk("coldry", g)
    assert "at my stones" in struck
    g.flags.add(BELOW)
    _, below = talk("coldry", g)
    assert "Vell" in below


def test_coldry_gives_mender_s_kits_once_the_core_is_quenched():
    g = FakeGame(flags={FREED, "met_coldry", QUENCHED})
    _, text = talk("coldry", g)
    assert "You broke the core" in text and "gift:coldry" in g.flags
    assert g.player.inventory.count("menders_kit") == 2
    _, again = talk("coldry", g)
    assert g.player.inventory.count("menders_kit") == 2 and "Mender's kits" not in again
    g.flags.add(DEAD)
    _, done = talk("coldry", g)
    assert "broken" in done and "Vell will grieve" in done


def test_ysolde_gives_moss_for_the_under_cells_news_and_still_opens_her_shop():
    g = FakeGame(flags={BELOW})
    talk("ysolde", g)
    assert g.shop_opened is None and "gift:ysolde" not in g.flags  # nothing through the bars
    g.flags.add(FREED)
    _, text = talk("ysolde", g)
    assert "Under-Cells" in text and "gift:ysolde" in g.flags and g.shop_opened == "ysolde"
    assert g.player.inventory.count("blue_moss") == 3 and g.player.inventory.gold == 250
    g.shop_opened = None
    _, later = talk("ysolde", g)
    assert "Under-Cells" not in later and g.shop_opened == "ysolde"
    assert g.player.inventory.count("blue_moss") == 3


def test_ysolde_s_shelves_fill_once_the_mortar_light_is_out():
    from ashen_vault.player.items import Items

    base = dialogue.shop_stock("ysolde", {FREED})
    assert base == dialogue.SHOPS["ysolde"]
    more = dialogue.shop_stock("ysolde", {FREED, QUENCHED})
    assert set(base) < set(more) and len(more) == len(set(more))
    assert all(Items.get(i).kind != "scroll" for i in more if i not in base)  # her spells stay her two
    assert dialogue.shop_stock("pell", {QUENCHED}) == dialogue.SHOPS["pell"]
    for flag, extras in dialogue.SHOP_EXTRAS.values():
        assert all(i in Items.ALL for i in extras), flag
    _, text = talk("ysolde", FakeGame(flags={FREED, "met_ysolde", QUENCHED}))
    assert "mortar-light out" in text


def test_brannick_confesses_points_to_the_key_ring_and_sells_heavy_blunt_gear():
    from ashen_vault.player.items import Items
    from ashen_vault.world import elements

    g = FakeGame()
    speaker, first = talk("brannick", g)
    assert speaker == "Gaoler Brannick" and g.shop_opened == "brannick" and "met_brannick" in g.flags
    assert "key ring" in first and "warden's office" in first and "bell-keepers" in first
    g.shop_opened = None
    _, second = talk("brannick", g)
    assert second != first and g.shop_opened == "brannick"
    assert talk("brannick", g) != talk("brannick", FakeGame(flags={"met_brannick", QUENCHED}))
    assert "He's down" in talk("brannick", FakeGame(flags={"met_brannick", DEAD}))[1]
    stock = [Items.get(i) for i in dialogue.SHOPS["brannick"]]
    weapons = [i for i in stock if i.kind == "weapon"]
    assert weapons and all(i.category in elements.STRIKE_CATEGORIES for i in weapons)
    assert any(i.weight in ("heavy", "great") for i in weapons)
    assert all(i.kind in ("weapon", "consumable", "repair") for i in stock)


def test_sister_vell_urges_the_quench_and_gives_mortar_shard_after_it():
    g = FakeGame()
    speaker, first = talk("sister_vell", g)
    assert speaker == "Sister Vell" and "mortar-light" in first and "Quench" in first
    assert "met_vell" in g.flags
    _, second = talk("sister_vell", g)
    assert second != first and "core still burns" in second
    _, spared = talk("sister_vell", FakeGame(flags={DEAD}))
    assert "still the mortar-light burns" in spared
    g.flags.add(QUENCHED)
    _, thanks = talk("sister_vell", g)
    assert "It's out" in thanks and "gift:sister_vell" in g.flags
    assert g.player.inventory.has("scroll_mortar_shard")
    _, after = talk("sister_vell", g)
    assert after != thanks and "only stones" in after
    g.flags.add(DEAD)
    _, end = talk("sister_vell", g)
    assert end != after and "sleeps at last" in end


def test_story_gifts_name_real_items_and_new_npcs_have_looks():
    from ashen_vault.player.items import Items
    from ashen_vault.world import villagers

    for id_, (_flag, items, gold) in dialogue.STORY_GIFTS.items():
        assert all(i in Items.ALL for i in items) and gold >= 0, id_
    for id_ in ("brannick", "sister_vell"):
        assert id_ in villagers.LOOKS
        assert villagers.look(id_) != villagers.look("coldry")


def test_the_mortar_light_is_never_called_fire_by_those_who_know_it():
    lines = []
    told = {DEAD, QUENCHED, FREED, BELOW, "met_coldry", "met_ysolde", "met_vell", "met_brannick"}
    for flags in ({FREED}, {BELOW}, told, {FREED, QUENCHED}, {FREED, DEAD}, set()):
        for id_ in ("aubel", "coldry", "ysolde", "brannick", "sister_vell"):
            lines.append(talk(id_, FakeGame(flags=flags))[1])
    text = " ".join(lines).lower()
    assert "mortar-light" in text
    assert "torch" not in text and " fire" not in text and " hand" not in text


def test_every_dialogue_line_fits_two_rows_of_the_box():
    import ast
    import pathlib

    from ashen_vault.ui import hud

    width = hud.DIALOGUE_W - 2 * hud.PANEL_PAD
    for n in ast.walk(ast.parse(pathlib.Path(dialogue.__file__).read_text())):
        if (
            isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and " " in n.value
            and "\n" not in n.value
        ):
            assert len(hud.wrap(n.value, width)) <= 2, n.value


def test_vell_s_mortar_shard_cracks_stone_like_a_hammer():
    from types import SimpleNamespace

    from ashen_vault.player.spells import Spells
    from ashen_vault.world import elements

    stone, flesh = SimpleNamespace(brittle=True), SimpleNamespace(brittle=False)
    assert elements.shot_mult(stone, "mortar") == elements.BRITTLE_STRIKE_MULT
    assert elements.shot_mult(stone, "flame") == 1.0 and elements.shot_mult(flesh, "mortar") == 1.0
    assert Spells.power("mortar_shard", 5) == Spells.mortar_damage(5, 1.0) > 0
