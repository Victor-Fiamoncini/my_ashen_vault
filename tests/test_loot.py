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
