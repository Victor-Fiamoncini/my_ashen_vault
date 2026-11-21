"""The Keystone's court: its great gate (`door ... great=<side>`, `world/great_gate.py`,
`sunken_models.great_keystone_gate`) and the colossal pillars rising to the cavern's vault
(`pillar model=colossal`, `Vault.column_height`, `sunken_models.colossal_pillar`)."""

import math

import pytest

from ashen_vault import map_path
from ashen_vault.render import bounds, models, sunken_models
from ashen_vault.render.bounds import BoundsGpu
from ashen_vault.render.rig import Rig
from ashen_vault.world import great_gate
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.vault import COLUMN_EMBED, COLUMN_RADIUS, Vault
from ashen_vault.world.world import World
from test_prison_world import FakeGame

MAPS = (
    "ashen_cemetery",
    "abandoned_prison",
    "verdant_hollow",
    "cinder_keep",
    "harrow_sewers",
    "vesperholm",
    "old_harrowmere",
)


def _harrowmere():
    return MapLoader.load_file(map_path("old_harrowmere"))


def _keystone_doors(m):
    return [s for s in m.entities if s.kind == "door" and s.props.get("boss") == "keystone_dead"]


def test_a_great_gate_faces_the_side_named_if_the_door_opens_that_way():
    assert great_gate.outward({"great": "n"}, "z") == (0, -1)
    assert great_gate.outward({"great": "s"}, "z") == (0, 1)
    assert great_gate.outward({"great": "w"}, "x") == (-1, 0)
    assert great_gate.outward({"great": "e"}, "x") == (1, 0)
    assert great_gate.outward({"great": "e"}, "z") is None  # a door blocking z opens north and south
    assert great_gate.outward({"great": "n"}, "x") is None
    assert great_gate.outward({"great": None}, "z") is None
    assert great_gate.outward({}, "z") is None


def test_only_the_keystones_front_door_is_great_its_facade_out_over_the_chasm():
    m = _harrowmere()
    doors = {(s.tx, s.tz): s for s in _keystone_doors(m)}
    assert set(doors) == {(21, 38), (12, 42)}
    assert "great" not in doors[12, 42].props  # the rear door, from the lift room, stays a boss door
    front = doors[21, 38]
    step = great_gate.outward(front.props, "z")
    assert step == (0, -1)
    assert great_gate.porch(m, 21, 38, step) == 1  # the notch in the court's outer wall before it
    assert great_gate.wall_rise(m, 21, 38, "z") == pytest.approx(12.0)  # sunken brick, top -10 over -22


def test_a_porch_ends_where_the_walls_either_side_do_and_a_gate_without_walls_has_no_rise():
    m = MapLoader(
        """[meta]
name = Porch
start = 2 4 0

[legend]
# = wall top=6
. = floor h=0

[grid]
#...#
##.##
##.##
##D##
#...#
#####

[entities]
D = door boss=keystone_dead great=n on=.
""",
        name="porch",
    ).parse()
    assert great_gate.porch(m, 2, 3, (0, -1)) == 2  # two tiles walled in before it opens out
    assert great_gate.porch(m, 2, 3, (0, -1), limit=1) == 1
    assert great_gate.porch(m, 2, 3, (0, 1)) == 0  # straight out onto the open floor
    assert great_gate.wall_rise(m, 2, 3, "z") == pytest.approx(6.0)
    assert great_gate.wall_rise(m, 2, 4, "z") is None  # floor beside it, not walls


def test_every_great_door_placed_has_a_great_gate():
    for name in MAPS:
        for s in MapLoader.load_file(map_path(name)).entities:
            if s.kind == "door" and "great" in s.props:
                assert s.props.get("boss") in models.GREAT_GATES, name
                assert s.props["great"] in great_gate.DIRS, name


class _GlowGpu(BoundsGpu):
    def __init__(self):
        super().__init__()
        self.parts = 0
        self.glows = 0

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        super().draw_part(kind, m, rgb, tex, glow)
        self.parts += 1
        self.glows += glow


def _gate(open_t=0.0, lit=True, front=1, porch=2.0, rise=12.0, leaves=True, axis="x"):
    gpu = _GlowGpu()
    great = models.GreatGate(front, porch, rise)
    models.boss_door(Rig(gpu), open_t, axis, 0.7, lit=lit, boss="keystone_dead", great=great, leaves=leaves)
    return gpu


def test_the_great_gate_is_twice_a_boss_doors_height_dressed_and_its_light_dies_with_the_keystone():
    lit, cold = _gate(lit=True), _gate(lit=False)
    assert 60 <= lit.parts <= 160  # a great door, but still a door
    assert lit.glows > 0 and cold.glows == 0
    assert models.GREAT_DOOR_TOP >= 1.9 * models.BOSS_DOOR_TOP
    ys = [p[1] for p in lit.points]
    assert max(ys) >= 12.0 + sunken_models.GATE_CROWN - 0.01  # built up to the walls, crowned over them
    plain = BoundsGpu()
    models.boss_door(Rig(plain), 0.0, "x", 0.7, boss="keystone_dead")  # no `great`: the boss door
    assert max(p[1] for p in plain.points) < 4.5


def test_the_great_gates_leaves_fill_its_opening_shut_and_swing_inward_aside_open():
    for front in (1, -1):
        frame = _gate(leaves=False, front=front)
        assert frame.glows > 0  # the fog's frame keeps its lit masonry
        for open_t, shut in ((0.0, True), (1.0, False)):
            gate = _gate(open_t=open_t, front=front)
            leaves = gate.points[len(frame.points) :]  # the leaves are drawn last
            assert leaves
            ys = [p[1] for p in leaves]
            assert min(ys) >= -0.01 and max(ys) <= models.GREAT_DOOR_TOP + 0.01
            assert all(abs(p[2]) <= 1.1 for p in leaves)  # between the jambs, swung back against them
            if shut:
                assert all(abs(p[0]) <= 0.3 for p in leaves)  # across the doorway
            else:
                xs = [p[0] * front for p in leaves]
                assert max(xs) <= 0.3 and min(xs) < -0.6  # swung in, away from the facade


def test_the_great_gate_turns_its_facade_to_its_front_out_past_its_porch():
    for axis in ("x", "z"):
        for front in (1, -1):
            gpu = _gate(front=front, porch=2.0, axis=axis)
            k = 0 if axis == "x" else 2
            sign = front if axis == "x" else -front  # a door's frame turns local +x onto world -z
            out = [p[k] * sign for p in gpu.points]
            assert max(out) >= 3.0 + 1.5  # the giants stand out before the facade, 3 m out
            assert min(out) >= -1.3  # on the arena's side, only pilasters on the wall's face


def test_old_harrowmeres_pillars_are_colossal_and_rise_into_the_vault():
    world = World(FakeGame(), "old_harrowmere")
    v = Vault.of(world.map)
    pillars = [p for p in world.props if p.kind == "pillar" and p.props.get("model") == "colossal"]
    assert {(p.tx, p.tz) for p in pillars} == {(16, 41), (28, 41), (16, 44), (28, 44)}
    for p in pillars:
        floor = world.map[p.tx, p.tz].floor
        height = v.column_height(floor, p.x, p.z)
        assert height > 40  # from the court's floor to the cavern's roof
        assert height == pytest.approx(v.rise_over(p.x, p.z, COLUMN_RADIUS) + COLUMN_EMBED - floor)
        assert v.rise_over(p.x, p.z, COLUMN_RADIUS) >= v.height_at(p.x, p.z)
        lo, hi = bounds.measure(lambda r, p=p: world.view._draw_prop(r, p))
        assert hi[1] == pytest.approx(height, abs=0.01)  # its head sunk into the rock
        assert lo[1] == pytest.approx(0.0, abs=0.01)


def test_a_colossal_pillar_stands_in_its_tile_and_spreads_only_at_its_head():
    for seed in range(6):
        gpu = BoundsGpu()
        sunken_models.colossal_pillar(Rig(gpu), seed, 30.0)
        assert max(p[1] for p in gpu.points) == pytest.approx(30.0)
        low = [p for p in gpu.points if p[1] < 27.0]  # below its head: the boxes round its round drums
        assert all(math.hypot(p[0], p[2]) <= TileMap.TILE / 2 * math.sqrt(2) + 1e-6 for p in low)
        plinth = [p for p in gpu.points if p[1] < 0.6]
        assert max(max(abs(p[0]), abs(p[2])) for p in plinth) == pytest.approx(TileMap.TILE / 2)


def test_a_vault_rises_highest_over_a_disc_at_least_as_high_as_at_its_middle():
    v = Vault(24.0, "cavern_rock")
    for x, z in ((3.0, 4.0), (33.0, 83.0), (57.5, 89.0)):
        assert v.rise_over(x, z, 1.3) >= v.height_at(x, z)
        assert v.rise_over(x, z, 0.0) == pytest.approx(v.height_at(x, z))  # no disc: its middle
        assert v.column_height(-22.0, x, z) == pytest.approx(
            v.rise_over(x, z, COLUMN_RADIUS) + COLUMN_EMBED + 22
        )


class _LitGpu(BoundsGpu):
    def __init__(self):
        super().__init__()
        self.lights = []

    def model_light(self, rgb):
        self.lights.append(rgb)


def test_old_harrowmeres_great_gate_is_drawn_shut_open_and_as_a_fog_twice_as_tall():
    world = World(FakeGame(), "old_harrowmere")
    (gate,) = [p for p in world.props if p.kind == "door" and p.props.get("great")]
    arena = world.arena_at_door(gate)
    (rear,) = [p for p in world.props if p.kind == "door" and p.props.get("boss") and p is not gate]

    def top(p):
        gpu = _LitGpu()
        world.view._draw_prop(Rig(gpu), p)
        return max(q[1] for q in gpu.points)

    assert top(gate) == pytest.approx(12.0 + sunken_models.GATE_CROWN)  # up over the walls
    assert top(rear) < 4.5  # the rear door stays a boss door
    world.flags.add(arena.fog_key)  # you died in there: the fog stands in the great gate's opening
    assert arena.fogged(world.flags)
    fog = BoundsGpu()
    models.fog_gate(Rig(fog), 0.0, gate.axis, height=models.GREAT_DOOR_TOP)
    drawn = _LitGpu()
    world.view._draw_prop(Rig(drawn), gate)
    assert drawn.lights  # lit from out before its facade
    assert max(p[1] for p in drawn.points) == pytest.approx(12.0 + sunken_models.GATE_CROWN)  # its masonry
    assert len(drawn.points) > len(fog.points)
