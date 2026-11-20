"""The energy core (the mortar-light) of Old Harrowmere, driven headless: it mends the golems it
sustains while it burns, a blunt blow quenches it once its ward is down, and quenched, its golems crack
easier. Each test swaps the map's own core, beside the fountain, for one with the props it needs."""

import math

from ashen_vault.player.items import Items
from ashen_vault.render import mesh_builder, rig, sunken_models
from ashen_vault.world import world as world_mod
from ashen_vault.world.tile_map import EntitySpec, TileMap
from ashen_vault.world.world import CORE_QUENCHED_MULT, CORE_REGEN, Prop, World
from test_old_harrowmere_world import sunken
from test_verdant_world import foe

CORE_AT = (21, 27)


def _core(world, **props):
    world.props = [q for q in world.props if q.kind != "energy_core"]
    x, z = TileMap.center(*CORE_AT)
    p = Prop("energy_core", x, z, world.map[CORE_AT].floor, *CORE_AT, {"height": "1.2", **props}, "core")
    world.props.append(p)
    return p


def _facing_core(flags=(), **props):
    """You stand a tile south of the core, facing it."""
    game, world = sunken(at=(CORE_AT[0], CORE_AT[1] + 1), flags=flags)
    game.player.yaw = -math.pi / 2
    return game, world, _core(world, **props)


def _weapon(category):
    return next(i for i in Items.ALL.values() if i.category == category)


def test_a_lit_core_mends_the_golems_within_its_reach_and_no_others():
    _, world, _ = _facing_core(radius="10")
    near = foe(world, "stone_golem", (CORE_AT[0] + 3, CORE_AT[1]))
    far = foe(world, "stone_golem", (CORE_AT[0] + 9, CORE_AT[1]))
    sexton = foe(world, "sunken_sexton", (CORE_AT[0] - 2, CORE_AT[1]))
    for e in (near, far, sexton):
        e.hp = e.type.hp - 20
        e.rouse() if e.perched else None
    sustained = world.core_sustained(world.props[-1])
    assert near in sustained and far not in sustained and sexton not in sustained
    world._update_core(1.0)
    world._update_core(1.0)
    assert near.hp == near.type.hp - 20 + round(2 * CORE_REGEN)
    assert far.hp == far.type.hp - 20 and sexton.hp == sexton.type.hp - 20
    for _ in range(40):  # never past its full HP
        world._update_core(1.0)
    assert near.hp == near.type.hp


def test_a_quenched_core_mends_nothing_and_its_golems_take_more():
    _, world, p = _facing_core(flags=("core_quenched:old_harrowmere",))
    assert world.core_quenched()
    golem = foe(world, "stone_golem", (CORE_AT[0] + 3, CORE_AT[1]))
    golem.hp -= 20
    world._update_core(5.0)
    assert golem.hp == golem.type.hp - 20 and world.core_sustained(p) == []
    assert world.core_mult(golem) == CORE_QUENCHED_MULT
    golem.x += 100  # one that woke within its reach keeps the weakness wherever it goes
    assert world.core_mult(golem) == CORE_QUENCHED_MULT
    stranger = foe(world, "stone_golem", (5, 5))
    assert world.core_mult(stranger) == 1.0
    assert world.core_mult(foe(world, "sunken_sexton", (CORE_AT[0] + 1, CORE_AT[1]))) == 1.0


def test_a_lit_core_leaves_its_golems_as_hard_as_ever():
    _, world, _ = _facing_core()
    assert world.core_mult(foe(world, "stone_golem", (CORE_AT[0] + 3, CORE_AT[1]))) == 1.0


def test_only_a_blunt_blow_with_the_ward_down_quenches_the_core_and_the_save_remembers():
    game, world, p = _facing_core(seal="c")
    assert world.core_shielded(p)
    assert world.strike_core(2.0, _weapon("hammer")) == "shielded"
    assert not world.core_quenched()
    world.core_shielded = lambda p=None: False  # the teal road stands: the dome is down
    assert world.strike_core(2.0, _weapon("sword")) == "edge"
    assert not world.core_quenched()
    assert world.strike_core(2.0, _weapon("hammer")) == "quenched"
    assert world.core_quenched() and "core_quench" in game.sounds
    assert any("mortar-light" in m for m in game.messages)
    assert world.strike_core(2.0, _weapon("hammer")) is None  # already out
    again = World(game, "old_harrowmere")
    assert again.core_quenched()


def test_a_core_without_a_seal_has_no_dome_and_a_swing_elsewhere_misses_it():
    game, world, p = _facing_core()
    assert not world.core_shielded(p)
    game.player.yaw = math.pi / 2  # turned away
    assert world.strike_core(2.0, None) is None
    game.player.yaw = -math.pi / 2
    assert world.strike_core(2.0, None) == "quenched"  # bare fists are blunt


def test_the_core_blocks_its_tile_hums_and_is_drawn_live():
    game, world, p = _facing_core()
    assert "energy_core" in world_mod.BLOCKING_PROPS
    assert "energy_core" not in world_mod.STATIC_PROPS
    world.player.place(p.x + 1.5, p.z, 0.0, world.map)
    world._update_core(world_mod.CORE_HUM[2] + 0.1)
    assert "core_hum" in game.sounds


def test_the_core_lights_the_plaza_teal_until_it_is_quenched():
    spec = EntitySpec(kind="energy_core", tx=CORE_AT[0], tz=CORE_AT[1], props={"radius": "16"}, marker="?")
    m = sunken()[1].map
    light = mesh_builder.MeshBuilder.light_for(m, spec)
    assert light.color == [0.45, 1.25, 1.0] and light.radius == 9.0  # `radius=` is its reach, not its light
    m.entities.append(spec)
    assert (
        len(mesh_builder.MeshBuilder.lights_for(m, lit=lambda s: s is not spec))
        == len(mesh_builder.MeshBuilder.lights_for(m)) - 1
    )


class _Count:
    def __init__(self):
        self.parts = 0
        self.glows = 0

    def draw_part(self, kind, matrix, rgb, tex="white", glow=False):
        self.parts += 1
        self.glows += glow

    @staticmethod
    def to_matrix(m):
        return m


def test_the_core_model_glows_while_lit_and_goes_cold_when_quenched():
    lit, dome, out = _Count(), _Count(), _Count()
    sunken_models.energy_core(rig.Rig(lit), 1.0, tethers=[(5.0, 0.0, 3.0)], sunlit=True)
    sunken_models.energy_core(rig.Rig(dome), 1.0, shielded=True)
    sunken_models.energy_core(rig.Rig(out), 1.0, quenched=True)
    assert lit.glows > 15 and dome.parts > lit.parts - 4
    assert out.glows == 0 and out.parts < lit.parts
    assert sunken_models.WARD_RGB["c"] == sunken_models.CORE_TEAL == (70, 235, 190)
    assert sunken_models.CORE_HEART == (200, 255, 235)
