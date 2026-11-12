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


def make_room():
    return MapLoader(ROOM, name="room").parse()


@pytest.fixture
def room():
    return make_room()
