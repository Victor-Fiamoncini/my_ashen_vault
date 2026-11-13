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
        for i in ("ember_sigil", "verdant_sigil"):
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


def test_odrin_intro_asks_for_both_sigils_and_gives_supplies():
    g = FakeGame()
    speaker, text = talk("odrin", g)
    assert speaker == "Odrin"
    assert "Ember Sigil" in text and "Verdant Sigil" in text
    assert "quest" in g.flags
    assert g.player.inventory.gold == 60
    assert g.player.inventory.count("red_tonic") == 2
    assert not g.finished


def test_odrin_without_sigils_gives_directions():
    g = FakeGame(flags={"quest"})
    _, text = talk("odrin", g)
    assert "well" in text and "green trail" in text
    assert not g.finished


def test_odrin_with_only_the_ember_sigil_points_to_the_hollow():
    g = FakeGame(flags={"quest"}, items=["ember_sigil"])
    _, text = talk("odrin", g)
    assert "green trail" in text and "Verdant Sigil" in text
    assert not g.finished
    assert g.player.inventory.has("ember_sigil")


def test_odrin_with_only_the_verdant_sigil_points_to_the_well():
    g = FakeGame(flags={"quest"}, items=["verdant_sigil"])
    _, text = talk("odrin", g)
    assert "well" in text and "Ember Sigil" in text
    assert not g.finished


def test_odrin_with_both_sigils_ends_the_game():
    g = FakeGame(flags={"quest"}, items=["ember_sigil", "verdant_sigil"])
    talk("odrin", g)
    assert g.finished
    assert not g.player.inventory.has("ember_sigil")
    assert not g.player.inventory.has("verdant_sigil")


def test_odrin_with_both_sigils_ends_the_game_even_before_the_quest():
    g = FakeGame(items=["ember_sigil", "verdant_sigil"])
    talk("odrin", g)
    assert g.finished


def test_odrin_reminds_about_fallen_bosses_relics():
    g = FakeGame(flags={"quest", "boss_dead"})
    _, text = talk("odrin", g)
    assert "Warden" in text and "Ember Sigil" in text
    g = FakeGame(flags={"quest", "spider_dead"})
    _, text = talk("odrin", g)
    assert "Verdant Sigil" in text
    g = FakeGame(flags={"quest", "boss_dead", "sigil_taken"})
    _, text = talk("odrin", g)
    assert "Warden has fallen" not in text


def test_hollis_hints_at_the_green_trail_until_the_spider_dies():
    _, text = talk("hollis", FakeGame())
    assert "green trail" in text
    _, text = talk("hollis", FakeGame(flags={"spider_dead"}))
    assert "green trail" not in text
    _, text = talk("hollis", FakeGame(flags={"lever:north_lever"}))
    assert "north gate" in text and "green trail" in text


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
