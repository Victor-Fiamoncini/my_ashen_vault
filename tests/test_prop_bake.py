"""Static props baked into world-space batches (`render/prop_bake.py`, `world.STATIC_PROPS`)."""

import math

import pytest

from ashen_vault.render import prop_bake
from ashen_vault.render.rig import Rig
from ashen_vault.world import world as world_mod
from ashen_vault.world.world import STATIC_PROPS, World
from test_prison_world import FakeGame

MAPS = (
    "ashen_cemetery",
    "harrowmere",
    "abandoned_prison",
    "verdant_hollow",
    "cinderhold",
    "cinder_keep",
    "harrow_sewers",
    "vesperholm",
    "old_harrowmere",
    "vigil_chapel",
)
# Props whose look follows their state (opened, broken, pulled, taken, kindled) or who speak.
STATEFUL = {
    *world_mod.BREAKABLE_PROPS,
    *world_mod.KINDLING,
    *("chest", "door", "gate", "lever", "pickup", "npc", "exit", "altar", "iron_maiden"),
    *("winch", "frog_idol", "mimic"),
}


def _cube():
    """A unit cube as flat (verts, normals, uvs): 12 triangles, like the GPU's own."""
    verts, normals, uvs = [], [], []
    for axis in range(3):
        for sign in (-0.5, 0.5):
            u, v = [a for a in range(3) if a != axis]
            corners = []
            for a, b in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                p = [0.0, 0.0, 0.0]
                p[axis], p[u], p[v] = sign, a, b
                corners.append(p)
            n = [0.0, 0.0, 0.0]
            n[axis] = 1.0 if sign > 0 else -1.0
            for i in (0, 1, 2, 0, 2, 3):
                verts.extend(corners[i])
                normals.extend(n)
                uvs.extend((corners[i][u] + 0.5, corners[i][v] + 0.5))
    return verts, normals, uvs


def _tris(_kind):
    return _cube()


class _Recorder:
    def __init__(self):
        self.parts = []

    @staticmethod
    def to_matrix(m):
        return tuple(round(v, 5) for v in m)

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        self.parts.append((kind, m, tuple(rgb), tex, glow))


def _record(world, p, t):
    world._time = t
    gpu = _Recorder()
    rig = Rig(gpu)
    with rig.entity(p.x, p.y, p.z, p.yaw):
        world._draw_prop(rig, p)
    return gpu.parts


@pytest.mark.parametrize("name", MAPS)
def test_static_props_never_change_with_time(name):
    """A baked prop is drawn once: one that animates (or flickers) must not be in STATIC_PROPS."""
    world = World(FakeGame(), name)
    for p in world.props:
        if p.kind in STATIC_PROPS:
            assert _record(world, p, 0.0) == _record(world, p, 7.3), p.kind


def test_no_prop_that_changes_state_is_baked():
    assert not STATIC_PROPS & STATEFUL


def test_every_static_kind_is_placed_somewhere():
    placed = {p.kind for name in MAPS for p in World(FakeGame(), name).props}
    assert placed >= STATIC_PROPS


def test_a_baked_part_is_placed_and_lit_as_the_shader_lights_a_model():
    baker = prop_bake.PropBaker(_tris)
    baker.group = "g"
    baker.model_light((0.5, 0.4, 0.3))
    rig = Rig(baker)
    with rig.at(10.0, 1.0, -4.0):
        rig.part("cube", 0, 0.5, 0, 2.0, 1.0, 2.0, (200, 100, 50), tex="stone")
    batch = baker.batches[("g", "stone")]
    assert batch.vertex_count == 36 and len(batch.uvs) == 72
    xs, ys, zs = batch.verts[0::3], batch.verts[1::3], batch.verts[2::3]
    assert (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)) == pytest.approx((9, 11, 1, 2, -5, -3))
    # The colour is baked halved and unlit; the light rides beside it. The top face looks up: it
    # takes the most of the sun; the bottom one the least (0.55).
    up = 0.55 + 0.45 * prop_bake.SUN[1]
    assert batch.colors[:3] == pytest.approx([c / 255 * prop_bake.BAKE_SCALE for c in (200, 100, 50)])
    tops = [batch.light[i * 3 : i * 3 + 3] for i in range(36) if ys[i] == pytest.approx(2.0)]
    assert any(li == pytest.approx([(c + 0.12) * up for c in (0.5, 0.4, 0.3)]) for li in tops)
    assert len(batch.light) == len(batch.colors)
    assert all(0.0 <= c <= 0.5 for c in batch.colors)


def _shade_baked(color, light, torch):
    """`ps1.vs`'s baked branch (isModel -1), then `ps1.fs`'s colour on a white texture."""
    return [c * 2.0 * (li + t) for c, li, t in zip(color, light, torch, strict=True)]


def _shade_live(rgb, model_light, shade, torch):
    """`ps1.vs`'s model branch with the colour in `colDiffuse`, as `Gpu.draw_part` draws."""
    return [c / 255 * (m * shade + t) for c, m, t in zip(rgb, model_light, torch, strict=True)]


@pytest.mark.parametrize("torch", [(0.0, 0.0, 0.0), (0.9, 0.7, 0.5)])
def test_a_baked_part_takes_the_torch_as_a_live_one_does(torch):
    """Walking up to a baked prop must not wash it out: the torch is scaled by its colour."""
    baker = prop_bake.PropBaker(_tris)
    baker.group = "g"
    baker.model_light((0.34, 0.3, 0.28))
    Rig(baker).part("cube", 0, 0, 0, 1, 1, 1, (110, 105, 100))
    batch = baker.batches[("g", "white")]
    up = 0.55 + 0.45 * prop_bake.SUN[1]
    i = max(range(36), key=lambda i: batch.light[i * 3])  # a vertex of the sunlit top face
    baked = _shade_baked(batch.colors[i * 3 : i * 3 + 3], batch.light[i * 3 : i * 3 + 3], torch)
    live = _shade_live((110, 105, 100), (0.46, 0.42, 0.40), up, torch)
    assert baked == pytest.approx(live)
    assert max(baked) < 0.8  # a grey stone stays grey right under the torch


def test_a_glowing_part_is_baked_at_glow_light():
    baker = prop_bake.PropBaker(_tris)
    baker.group = "g"
    Rig(baker).part("cube", 0, 0, 0, 1, 1, 1, (255, 255, 255), glow=True)
    batch = baker.batches[("g", "white")]
    up = 0.55 + 0.45 * prop_bake.SUN[1]  # the top face, the most sunlit
    assert max(batch.light) == pytest.approx(prop_bake.GLOW_LIGHT * up)
    assert max(batch.colors) == pytest.approx(prop_bake.BAKE_SCALE)


def test_chunks_group_tiles_by_eight():
    assert prop_bake.chunk_of(0, 7) == (0, 0)
    assert prop_bake.chunk_of(8, 15) == (1, 1)
    assert prop_bake.chunk_centre(0, 0) == (8.0, 8.0)
    assert pytest.approx(math.hypot(8, 8)) == prop_bake.CHUNK_REACH


class _BakingGpu:
    """A headless GPU that can bake: it has primitives, keeps uploads and records baked draws."""

    def __init__(self):
        self.uploads = 0
        self.drawn = []

    def primitive_tris(self, kind):
        return _cube()

    def upload_batch(self, batch):
        self.uploads += 1
        return batch

    def unload_mesh(self, _mesh):
        pass

    def set_float(self, *_args):
        pass

    def draw_baked_batch(self, mesh, tex):
        self.drawn.append((mesh, tex))


def _baking_world(name, flags=()):
    game = FakeGame(flags)
    game.gpu = _BakingGpu()
    return World(game, name), game


def test_static_props_are_baked_by_chunk_and_culled_like_props():
    world, game = _baking_world("harrowmere")
    assert world._baked
    chunks = {chunk for _, _, chunk, _ in world._baked}
    statics = {prop_bake.chunk_of(p.tx, p.tz) for p in world.props if p.kind in STATIC_PROPS}
    assert chunks == statics
    p = next(p for p in world.props if p.kind == "tree")
    world.player.x, world.player.z = p.x, p.z
    fx, fz = world.player.forward()
    world._draw_baked(game.gpu, 200.0, 30.0, fx, fz)
    drawn = len(game.gpu.drawn)
    assert 0 < drawn < len(world._baked)  # the far side of the town is left out
    game.gpu.drawn = []
    world._draw_baked(game.gpu, 200.0, 0.0, fx, fz)
    drawn = {id(mesh) for mesh, _ in game.gpu.drawn}
    for mesh, _, chunk, landmark in world._baked:
        if id(mesh) in drawn and not landmark:  # with no range, only the chunk you stand in is drawn
            assert chunk == prop_bake.chunk_of(p.tx, p.tz)
    assert any(landmark for mesh, _, _, landmark in world._baked if id(mesh) in drawn)  # and the skyline


def test_a_headless_world_without_primitives_bakes_nothing():
    assert World(FakeGame(), "harrowmere")._baked == []


def test_kindling_a_fire_bakes_the_props_round_it_again():
    world, game = _baking_world("verdant_hollow")
    cold = next(p for p in world.props if p.kind in world_mod.KINDLING and not world.is_lit(p))
    near = [b for b in world._baked if math.hypot(*_offset(b[2], cold)) < 30]
    before = {id(b[0]) for b in world._baked}
    uploads = game.gpu.uploads
    assert world.kindle(cold)
    assert near
    assert game.gpu.uploads > uploads
    assert {id(b[0]) for b in world._baked} != before
    assert len({(b[1], b[2], b[3]) for b in world._baked}) == len(world._baked)  # none left twice


def _offset(chunk, p):
    cx, cz = prop_bake.chunk_centre(*chunk)
    return cx - p.x, cz - p.z


def test_a_spread_prop_lights_each_part_where_it_stands():
    """A roof or a street arch is too big for one light: each part takes the light at its centre."""
    lamp_x = 4.0

    def light_at(x, y, z):
        near = max(0.0, 1.0 - abs(x - lamp_x) / 4.0)
        return [0.2 + near] * 3

    def lights(spread):
        baker = prop_bake.PropBaker(_tris, light_at)
        baker.group = "g"
        baker.spread = spread
        baker.model_light((0.3, 0.3, 0.3))
        rig = Rig(baker)
        rig.part("cube", 0, 0, 0, 1, 1, 1, (200, 200, 200))  # four metres from the lamp
        rig.part("cube", 4, 0, 0, 1, 1, 1, (200, 200, 200))  # right under it
        batch = baker.batches[("g", "white")]
        return max(batch.light[: 36 * 3]), max(batch.light[36 * 3 :])

    far, near = lights(spread=True)
    assert near > far * 2
    far, near = lights(spread=False)  # a small prop keeps the one light it was given
    assert near == pytest.approx(far)
