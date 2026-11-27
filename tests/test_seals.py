"""Sealed doors (`world/seals.py`): a door bound to the foes marked with its seal opens only once they
have all fallen, and stays open."""

from ashen_vault.world import seals
from ashen_vault.world.map_loader import MapLoader

SEALED = """[meta]
name = Sealed
start = 1 1 0
default = .

[legend]
# = wall
. = floor

[grid]
#######
#.....#
#.W.V.#
###D###
#.....#
#######

[entities]
W = castellan_warden seal=gate
V = castellan_warden seal=gate
D = door seal=gate
"""


def _map():
    return MapLoader(SEALED, name="sealed").parse()


def test_the_guardians_of_a_seal_are_the_foes_marked_with_it():
    m = _map()
    assert sorted(seals.guardians(m, "gate")) == [(2, 2), (4, 2)]
    assert seals.living(m, set(), "gate") == 2 and not seals.broken(m, set(), "gate")
    one = {seals.slain_key(m, (2, 2))}
    assert seals.living(m, one, "gate") == 1 and not seals.broken(m, one, "gate")
    both = one | {seals.slain_key(m, (4, 2))}
    assert seals.living(m, both, "gate") == 0 and seals.broken(m, both, "gate")
    assert seals.guardians(m, "other") == [] and not seals.broken(m, both, "other")
