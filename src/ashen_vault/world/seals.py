"""Sealed doors (`door seal=<name>`): a door bound to the guardians that keep it, the foes a map marks
with the same `seal=<name>`. It will not open while any of them lives; once the last has fallen it
opens of itself, for good (its `door:<map>:x,z` flag, as any opened door). Each guardian must be a
`once` foe, so its fall is saved (`slain:<map>:x,z`) and a shrine rest never brings it back. Herran's
Castle's barbican gate is one, bound to the two Castellan Wardens atop the towers either side of it.
Pure logic: no raylib."""

from ashen_vault.ai.enemy_types import EnemyTypes


def guardians(map_, name):
    """The tiles of the foes bound to seal `name` on `map_`."""
    return [(s.tx, s.tz) for s in map_.entities if EnemyTypes.has(s.kind) and s.props.get("seal") == name]


def slain_key(map_, tile):
    return f"slain:{map_.name}:{tile[0]},{tile[1]}"


def living(map_, flags, name):
    """How many of seal `name`'s guardians still stand (one eye burning on its door for each)."""
    return sum(1 for tile in guardians(map_, name) if slain_key(map_, tile) not in flags)


def broken(map_, flags, name):
    """Whether every guardian of seal `name` has fallen. A seal with no guardians never breaks."""
    return bool(guardians(map_, name)) and living(map_, flags, name) == 0
