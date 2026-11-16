import pytest

from ashen_vault.world.map_loader import MapLoader

ROOM = """[meta]
name = Test Room
start = 1 1 0

[legend]
# = wall tex=stone_brick top=3
. = floor h=0 ceil=3
, = floor h=0.5 ceil=3
^ = floor h=1.5 ceil=3
~ = water h=-0.4

[grid]
######
#..,^#
#.a..#
#~...#
######

[entities]
a = bone_walker yaw=90
"""


def risen(*enemies):
    """Skips a boss's entrance: one still in its ashes stands idle at once, as bosses did before they
    rose; a statue on its perch is awake and on the hunt, as a roused one was."""
    for e in enemies:
        if e.state in ("ashes", "rising", "perched"):
            e.state, e.state_t = ("chase" if e.type.perch else "idle"), 0.0
    return enemies[0] if len(enemies) == 1 else enemies


def make_room():
    return MapLoader(ROOM, name="room").parse()


@pytest.fixture
def room():
    return make_room()
