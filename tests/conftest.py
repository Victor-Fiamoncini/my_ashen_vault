import pytest

from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.render.world_view import WorldView
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


class _LazyWorldView(WorldView):
    """A headless World's view that builds the map's lit mesh only when a test asks for it (its
    `builder`, meshes or sea): most World tests never look, and the build is nearly all of a World's
    cost. The lights are taken when the World bakes, so a later build is the one it would have made
    then. A GPU that can bake props (`primitive_tris`) gets the eager view, as the game does."""

    BUILT = ("builder", "_meshes", "_sea")

    def bake(self):
        if hasattr(self.gpu, "primitive_tris"):
            return super().bake()
        if "_meshes" in self.__dict__:
            self.unload()
            for name in self.BUILT:
                delattr(self, name)
        else:  # never built: only what else `unload` lets go of
            self._unload_glitter()
            self._unload_baked()
        self._lights = MeshBuilder.lights_for(self.world.map, lit=self.world._light_on)

    def __getattr__(self, name):  # only for attributes not set: the mesh, before it is built
        if name not in self.BUILT or "_lights" not in self.__dict__:
            raise AttributeError(name)
        self.builder = MeshBuilder(self.world.map, lights=self._lights).build()
        self._meshes = [(self.gpu.upload_batch(b), tex) for tex, b in self.builder.batches.items()]
        self._sea = self.gpu.upload_batch(self.builder.sea) if self.builder.sea.vertex_count else None
        return getattr(self, name)


@pytest.fixture(autouse=True, scope="session")
def _headless_worlds_build_their_mesh_on_demand():
    """`FakeGame` worlds (tests/test_prison_world.py) take the lazy view for the whole session. Outside
    pytest (scripts that import FakeGame) they keep the eager one."""
    import test_prison_world

    patch = pytest.MonkeyPatch()
    patch.setattr(
        test_prison_world.FakeGame, "world_view", lambda self, world: _LazyWorldView(world, self.gpu)
    )
    yield
    patch.undo()
