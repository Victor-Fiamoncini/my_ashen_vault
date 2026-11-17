def test_an_old_save_s_removed_weapons_come_back_as_their_replacements():
    from ashen_vault.player.inventory import Inventory

    inv = Inventory.from_h(
        {"counts": {"heartwood_maul": 1, "felling_axe": 1, "potion": 2}, "right": "felling_axe", "left": None,
         "body": None, "hands": None, "gold": 5}
    )  # fmt: skip
    assert inv.counts == {"great_iron_hammer": 1, "flamberge": 1, "potion": 2}
    assert inv.right == "flamberge"
