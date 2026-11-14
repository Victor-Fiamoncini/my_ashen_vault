from ashen_vault.world import loot


def keys(n=600):
    return [f"barrel:sunken_keep:{i},{i * 7 % 31}" for i in range(n)]


def test_roll_is_deterministic():
    for k in keys(50):
        assert loot.roll(k) == loot.roll(k)


def test_mostly_small_gold_or_nothing_potions_rare():
    rolls = [loot.roll(k) for k in keys()]
    potions = sum(1 for _, item in rolls if item)
    gold = [g for g, _ in rolls if g]
    assert 0 < potions < len(rolls) * 0.25
    assert len(gold) > len(rolls) * 0.3
    assert all(g in loot.GOLD for g in gold)
    assert {item for _, item in rolls if item} <= set(loot.POTIONS)


def test_map_props_override_the_roll():
    assert loot.roll("x", {"item": "red_tonic"}) == (0, "red_tonic")
    assert loot.roll("x", {"gold": "15"}) == (15, None)


def _free_sources():
    """Every item the world hands out for free, once each: chest, altar, mimic and boss `item=`
    entries in the maps, and the villagers' gifts."""
    import pathlib
    import re

    from ashen_vault import dialogue

    maps = pathlib.Path(loot.__file__).resolve().parent.parent / "maps"
    found = []
    for path in sorted(maps.glob("*.map")):
        found += re.findall(r"\bitem=([a-z_]+)", path.read_text(encoding="latin-1"))
    for _, items, *_ in dialogue.GIFTS.values():
        found += list(items)
    return found


def test_no_spell_gear_or_key_can_be_found_twice():
    """A second Lumen scroll (Sister Ilse's gift and a keep chest) and a second Claymore (a keep and a
    jungle chest) once hid where a new find belonged: only remedies may be found more than once."""
    from collections import Counter

    from ashen_vault.player.items import Items

    counts = Counter(_free_sources())
    twice = {i: n for i, n in counts.items() if n > 1 and Items.get(i).kind != "consumable"}
    assert not twice


def test_every_spell_but_the_first_is_taught_by_one_free_scroll_or_a_shop():
    from ashen_vault import dialogue
    from ashen_vault.player.items import Items
    from ashen_vault.player.spells import Spells

    sold = {i for stock in dialogue.SHOPS.values() for i in stock}
    taught = [Items.get(i).spell for i in [*_free_sources(), *sold] if Items.get(i).kind == "scroll"]
    assert sorted(taught) == sorted(s for s in Spells.ALL if s != "flame")


def test_a_spare_copy_of_owned_gear_is_paid_in_gold():
    from ashen_vault.player.inventory import Inventory
    from ashen_vault.player.items import Items

    inv = Inventory()
    assert loot.claim(inv, ["flame"], "zweihander") == ("zweihander", 0)
    inv.add("zweihander")
    assert loot.claim(inv, ["flame"], "zweihander") == (None, Items.get("zweihander").price // 2)
    assert loot.claim(inv, ["flame"], "scroll_ward") == ("scroll_ward", 0)
    assert loot.claim(inv, ["flame", "ward"], "scroll_ward") == (None, loot.SPARE_SCROLL_GOLD)
    inv.add("red_tonic")
    assert loot.claim(inv, ["flame"], "red_tonic") == ("red_tonic", 0)  # remedies stack
