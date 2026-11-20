"""Villagers at work: the smith's cycle at his anvil, the swordmaster's half-draw, and how both draw."""

import math

from ashen_vault.render import models, rig
from ashen_vault.render.parts import _dim
from ashen_vault.world import villagers
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World
from test_prison_world import FakeGame


class _Parts:
    """Records each part's kind, colour and centre."""

    def __init__(self):
        self.parts = []

    def to_matrix(self, m):
        return m

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        self.parts.append((kind, tuple(rgb), (m[3], m[7], m[11])))


def _draw(look, t):
    gpu = _Parts()
    models.npc(rig.Rig(gpu), look, t)
    return gpu.parts


def test_the_smith_strikes_turns_inspects_and_wipes_his_brow_in_a_loop():
    seen = []
    t = 0.0
    while t < villagers.SMITH_LOOP * 2:
        stage, k = villagers.smith_cycle(t)
        assert 0.0 <= k <= 1.0
        if not seen or seen[-1] != stage:
            seen.append(stage)
        t += 0.05
    names = [n for n, _ in villagers.SMITH_STAGES]
    assert seen == names * 2


def test_the_smith_lands_four_blows_a_loop_and_counts_each_once():
    loop = villagers.SMITH_LOOP
    assert villagers.smith_blows(0.0, loop) == villagers.SMITH_BLOWS
    land = villagers.SMITH_LAND * villagers.SMITH_BEAT
    assert villagers.smith_blows(land - 0.01, land + 0.01) == 1
    assert villagers.smith_blows(land + 0.01, land + 0.3) == 0
    steps = [villagers.smith_blows(i * 0.016, (i + 1) * 0.016) for i in range(int(loop * 3 / 0.016))]
    assert sum(steps) == villagers.SMITH_BLOWS * 3  # frame by frame, no blow lost or heard twice


def test_the_smith_s_hammer_and_billet_meet_on_the_anvil():
    look = villagers.look("brannoc")
    hs = villagers.BUILDS[look.build][0]
    t = (villagers.SMITH_LAND + 0.05) * villagers.SMITH_BEAT  # just after the first blow lands
    parts = _draw(look, t)
    face = next(c for _, rgb, c in parts if rgb == _dim(models.TOOL_IRON, 1.25))
    rivet = max(i for i, (_, rgb, _) in enumerate(parts) if rgb == (60, 58, 62))
    billet = parts[rivet + 1][2]
    top, at = models.ANVIL_TOP * hs, models.ANVIL_AT * hs
    for x, y, z in (face, billet):
        assert abs(x - at) < 0.12 and abs(z) < 0.2, (x, z)  # over the anvil's face
        assert abs(y - top) < 0.06, (y, top)  # resting on it, not sunk in or floating
    assert math.dist(face, billet) < 0.15  # the hammer strikes the billet


def test_the_smith_sparks_only_as_a_blow_lands():
    look = villagers.look("brannoc")

    def sparks(t):
        return sum(1 for _, rgb, _ in _draw(look, t) if rgb[0] == 255 and rgb[2] < 150 and rgb[1] >= 140)

    beat = villagers.SMITH_BEAT
    assert sparks((villagers.SMITH_LAND + 0.1) * beat) >= 6
    assert sparks(0.2 * beat) == 0
    assert sparks(villagers.SMITH_BLOWS * beat + 0.5) == 0  # turning the billet


def test_a_long_beard_falls_to_the_belt():
    look = villagers.look("brannoc")
    hs = villagers.BUILDS[look.build][0]
    ring = [c for _, rgb, c in _draw(look, 0.0) if rgb == models.BEARD_RING]
    assert ring and ring[0][1] < (0.95 + 0.2) * hs  # below the chest, near the belt
    assert ring[0][1] > 0.95 * hs * 0.85


def test_the_swordmaster_shows_only_a_hand_s_width_of_steel():
    shown = [villagers.half_draw(i * 0.05) for i in range(int(villagers.DRAW_EVERY * 2 / 0.05))]
    assert max(shown) == villagers.DRAW_SHOWN
    assert min(shown) == 0.0
    assert sum(1 for s in shown if s == 0) > len(shown) / 2  # still, most of the time
    look = villagers.look("corvane")
    steel = (212, 214, 224)
    t_out = villagers.DRAW_TIME / 2
    assert any(rgb == steel for _, rgb, _ in _draw(look, t_out))
    assert not any(rgb == steel for _, rgb, _ in _draw(look, villagers.DRAW_EVERY - 0.5))


def test_the_swordmaster_wears_kimono_and_hakama_with_his_blades_at_his_hip():
    look = villagers.look("corvane")
    assert (look.garb, look.hair_style, look.beard, look.blade) == ("kimono", "topknot", "long", "hip")
    assert not look.hood and look.pauldron
    parts = _draw(look, 0.0)
    assert sum(1 for _, rgb, _ in parts if rgb == look.pauldron) >= 4  # its stacked plates
    assert any(rgb == look.sash for _, rgb, _ in parts)


def test_the_world_rings_the_smith_s_anvil_as_his_hammer_lands():
    game = FakeGame()
    world = World(game, "harrowmere")
    smith = next(p for p in world.props if p.kind == "npc" and p.props.get("id") == "brannoc")
    game.player.place(smith.x + 2, smith.z, 0.0, world.map)
    for _ in range(int(villagers.SMITH_LOOP / (1 / 60)) + 1):
        world.update(1 / 60)
    assert game.sounds.count("anvil") == villagers.SMITH_BLOWS
    far = FakeGame()
    world = World(far, "harrowmere")
    far.player.place(*TileMap.center(40, 40), 0.0, world.map)
    for _ in range(120):
        world.update(1 / 30)
    assert "anvil" not in far.sounds
