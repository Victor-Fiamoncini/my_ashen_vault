"""Foes hit harder than they used to: every blow a foe lands is scaled by FOE_DAMAGE before your
armour takes its share."""

import random

from ashen_vault.world import world as world_mod
from test_verdant_world import foe, jungle


def test_a_foes_blow_lands_half_again_as_hard(monkeypatch):
    monkeypatch.setattr(random, "random", lambda: 0.5)  # no spread: the blow's own damage
    _game, world = jungle((3, 3))
    world.player.inventory.slots["body"] = None
    world.player.inventory.slots["hands"] = None
    enemy = foe(world, "bone_walker", (4, 3))
    hp = world.player.stats.hp
    taken = world.enemy_strike(enemy)
    assert world_mod.FOE_DAMAGE == 1.5
    assert taken == max(round(enemy.type.damage * 1.5), 1)
    assert world.player.stats.hp == hp - taken


def test_foe_harm_scales_only_by_the_named_factor():
    assert world_mod.foe_harm(10) == 15.0
