"""The Cinderhold's mechanics driven headless: lava, flame jets and magma vents, lightning against
iron, seeking motes, and the twin gargoyles on the roof of its keep (a map of its own)."""

import math
import random

from ashen_vault.ai.enemy import DIVE_OVERSHOOT, MOVES, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.items import Items
from ashen_vault.player.spells import Spells
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.world import elements, relics, shots
from ashen_vault.world.hazards import Eruption, FlameJet, MagmaVent
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import LAVA_MIN, LAVA_SHARE, World
from test_enemy import FakeWorld, tick
from test_keep_world import FakeGame
from test_verdant_world import JungleGame, foe

KEEP = "cinder_keep"
ROOF = (10, 6)  # on the keep's roof, in sight of both perches
ANTECHAMBER = (22, 5)  # before the great door, far from the perches
BRIDGE = (29, 48)
FOUNDRY = (11, 18)  # beside the golem's crossing


def hold(at, yaw=0.0, flags=(), game=None, keep_enemies=False, map_name="cinderhold"):
    game = game or JungleGame(flags)
    world = World(game, map_name)
    if not keep_enemies:
        world.enemies = []
    x, z = TileMap.center(*at)
    game.player.place(x, z, yaw, world.map)
    return game, world


def run(world, seconds, dt=0.05):
    for _ in range(round(seconds / dt)):
        world.update(dt)


def twins(world):
    return {e.type.id: e for e in world.enemies if e.type.twin}


# --- lava ----------------------------------------------------------------------------------------


def test_lava_tiles_are_glowing_pits():
    _, world = hold(FOUNDRY)
    tile = world.map[8, 16]
    assert tile.lava and tile.pit and tile.hazardous
    assert not world.map[11, 16].lava


def test_lava_sears_a_share_of_your_hp_and_hauls_you_back_to_solid_ground():
    game, world = hold((10, 16))
    run(world, 0.1)  # remember the stone you stand on
    safe = (game.player.x, game.player.z)
    game.player.stats.max_hp = game.player.stats.hp = 100
    x, z = TileMap.center(9, 16)
    game.player.x, game.player.z = x, z
    game.player.y = world.map[9, 16].floor
    run(world, 0.05)
    assert game.wounds == [(max(LAVA_MIN, round(100 * LAVA_SHARE)), "The lava")]
    assert (game.player.x, game.player.z) == safe
    assert any("lava" in m for m in game.messages)


def test_lava_never_sears_the_dead_twice():
    game, world = hold((10, 16))
    run(world, 0.1)
    game.player.stats.hp = 1
    game.player.x, game.player.z = TileMap.center(9, 16)
    game.player.y = world.map[9, 16].floor
    run(world, 0.05)
    run(world, 0.05)
    assert len(game.wounds) == 1


def test_lava_floors_shine_and_light_their_shores_only():
    _, world = hold(FOUNDRY)
    lava = MeshBuilder.lava_lights(world.map)
    assert lava
    for light in lava:
        tx, tz = TileMap.tile_coord(light.x), TileMap.tile_coord(light.z)
        assert world.map[tx, tz].floor_tex == "lava"
    # The middle of the gorge, far from any footing, casts nothing.
    gorge = TileMap.center(10, 45)
    assert all(math.hypot(light.x - gorge[0], light.z - gorge[1]) > 3 for light in lava)
    # Lava ignores the dark: its floor is drawn at full brightness however dim its tile.
    colors = world.builder.batches["lava"].colors
    assert min(colors) >= 0.99


# --- flame jets ---------------------------------------------------------------------------------


def test_a_flame_jet_hisses_then_roars_along_its_line_and_wounds_once_a_burst():
    jet = FlameJet(5, 5, direction="e", length=3, every=4.0)
    x, z = TileMap.center(6, 5)  # two metres down its line
    assert jet.state == "idle" and jet.hit(x, z) == 0
    while jet.state == "idle":
        jet.update(0.05)
    assert jet.state == "warn" and jet.glow < 1.0 and jet.hit(x, z) == 0
    roared = False
    while jet.state == "warn":
        roared = jet.update(0.05) or roared
    assert roared
    for _ in range(4):
        jet.update(0.05)
    assert jet.hit(x, z) == FlameJet.DAMAGE
    assert jet.hit(x, z) == 0  # one wound per gout
    assert jet.hit(*TileMap.center(6, 6)) == 0  # off to the side of its line
    assert jet.hit(*TileMap.center(9, 5)) == 0  # past its reach


def test_flame_jets_on_the_ledge_burn_the_player_who_stands_in_them():
    game, world = hold((24, 30))
    world.hazards = [h for h in world.hazards if isinstance(h, FlameJet) and (h.tx, h.tz) == (24, 30)]
    run(world, 4.0)
    assert any(source == "The flames" for _, source in game.wounds)
    assert "jet" in game.sounds


# --- magma vents ---------------------------------------------------------------------------------


def test_a_magma_vent_lobs_bombs_at_the_player_on_open_ground_in_reach():
    vent = MagmaVent(0, 0, targets=[(9.0, 9.0, 0.0)], every=2.0, count=2, radius=12)
    assert vent.update(1.0, player_spot=(3.0, 1.0, 0.0)) == []
    bombs = vent.update(1.0, player_spot=(3.0, 1.0, 0.0))
    assert len(bombs) == 2
    first, second = bombs
    assert (first.x, first.z) == (3.0, 1.0)
    assert (second.x, second.z) == (9.0, 9.0)
    assert second.t < first.t  # the second lands a beat later
    assert first.origin == (vent.x, vent.HEIGHT, vent.z)


def test_a_lobbed_bomb_arcs_from_its_vent_and_lands_as_the_flame_bursts():
    f = Eruption(10.0, 0.0, 0.0, origin=(0.0, 2.0, 0.0))
    assert f.bomb() is not None
    x0, y0, _ = f.bomb()
    assert (x0, y0) == (0.0, 2.0)
    f.update(Eruption.WARN / 2)
    x, y, _ = f.bomb()
    assert 0 < x < 10 and y > 2.0  # high in its arc
    f.update(Eruption.WARN / 2 + 0.01)
    assert f.state == "burst" and f.bomb() is None


def test_bridge_vents_only_aim_at_solid_open_ground():
    _, world = hold(BRIDGE)
    vents = [h for h in world.hazards if isinstance(h, MagmaVent)]
    assert len(vents) >= 4
    for vent in vents:
        assert vent.targets
        for x, z, floor in vent.targets:
            tile = world.map.tile_at(x, z)
            assert tile.walkable and not tile.hazardous and tile.open_sky and tile.floor == floor


def test_the_bridge_vents_rain_fire_on_whoever_crosses():
    game, world = hold(BRIDGE)
    game.player.stats.max_hp = game.player.stats.hp = 999
    run(world, 12.0)
    assert any(source == "The fire" for _, source in game.wounds)
    assert "lob" in game.sounds


def test_fire_and_lava_sound_softly_and_fade_with_distance():
    """Vents, their bombs and the jets are background: never loud, quieter the farther they are, and
    silent from across the fortress."""
    game, world = hold(BRIDGE)
    near = Eruption(world.player.x + 1, world.player.z, origin=(0.0, 2.0, 0.0))
    far = Eruption(world.player.x + 40, world.player.z, origin=(0.0, 2.0, 0.0))
    world.eruptions = [near, far]
    run(world, Eruption.WARN + 0.1)
    bursts = [v for name, v in game.volumes if name == "eruption"]
    assert len(bursts) == 1 and bursts[0] <= 0.25  # only the near one, and softly
    game.volumes.clear()
    run(world, 12.0)
    assert game.volumes and all(v <= 0.3 for _, v in game.volumes)
    _game, world = hold(FOUNDRY)
    world.sfx_near("jet", world.player.x + 30, world.player.z, 0.3, 10)
    assert not _game.volumes
    world.sfx_near("jet", world.player.x + 5, world.player.z, 0.3, 10)
    ((name, volume),) = _game.volumes
    assert name == "jet" and math.isclose(volume, 0.15)


# --- elements -----------------------------------------------------------------------------------


def test_iron_foes_conduct_lightning_and_shrug_off_fire():
    golem = EnemyTypes.get("forge_golem")
    hound = EnemyTypes.get("slag_hound")
    bowman = EnemyTypes.get("iron_bowman")
    walker = EnemyTypes.get("bone_walker")
    assert elements.mult(golem, "lightning") == elements.LIGHTNING_MULT
    assert elements.mult(golem, "fire") == elements.FIREPROOF_MULT
    assert elements.mult(bowman, "lightning") == elements.LIGHTNING_MULT
    assert elements.mult(bowman, "fire") == 1.0
    assert elements.mult(hound, "lightning") == 1.0
    assert elements.mult(walker, None) == 1.0
    assert elements.burns(walker, "fire") and not elements.burns(golem, "fire")
    assert elements.staggers(bowman, "lightning")
    assert not elements.staggers(EnemyTypes.get("brand"), "lightning")  # bosses are too heavy


def test_a_thunder_spear_bites_iron_harder_and_jolts_it():
    _game, world = hold(FOUNDRY, yaw=-math.pi / 2)
    golem = foe(world, "forge_golem", (11, 16))
    world.fire_bolt(20, effect="thunder", rgb=(200, 225, 255), speed=Spells.THUNDER_SPEED)
    for _ in range(20):
        world.update(0.02)
        if golem.hp < golem.type.hp:
            break
    assert golem.hp == golem.type.hp - 30
    assert golem.state == "hurt"  # jolted, for all its poise


def test_fire_splashes_off_fireproof_foes():
    _game, world = hold(FOUNDRY, yaw=-math.pi / 2)
    golem = foe(world, "forge_golem", (11, 17))
    world.pyre(magic=10, gauge=1.0)
    full = Spells.pyre_damage(10, 1.0)
    assert golem.hp == golem.type.hp - round(full * elements.FIREPROOF_MULT)
    assert "burn" not in golem.status


def test_the_new_weapons_carry_their_elements():
    storm, slag = Items.get("stormbrand"), Items.get("slagbreaker")
    assert storm.element == "lightning" and storm.category == "sword"
    assert slag.element == "fire" and slag.two_handed and slag.level > storm.level


# --- the new spells -----------------------------------------------------------------------------


def test_thunder_and_motes_are_taught_by_scrolls():
    for spell in ("thunder", "motes"):
        assert Items.get(f"scroll_{spell}").spell == spell
        assert spell in Spells.ALL
    assert Spells.thunder_damage(10, 1.0) > Spells.thunder_damage(4, 1.0)
    assert 3 * Spells.mote_damage(6, 1.0) > Spells.mote_damage(6, 1.0)


def test_a_mote_steers_toward_a_foe_off_to_the_side():
    dx, _dy, dz = shots.home(6.0, 0.0, 0.0, 0.0, 1.0, 0.0, 5.0, 1.0, 5.0, turn=3.0, dt=0.1)
    assert dz > 0 and math.isclose(math.hypot(dx, dz), 6.0)
    assert math.atan2(dz, dx) <= 0.3 + 1e-9  # turns no faster than it may


def test_arcane_motes_fan_out_and_seek_out_a_foe_you_did_not_aim_at():
    _game, world = hold(FOUNDRY, yaw=-math.pi / 2)  # facing north, up the hall
    wisp = foe(world, "cinder_wisp", (12, 16))  # off to the right
    wisp.state = "chase"
    motes = world.motes(5)
    assert len(motes) == Spells.MOTES and all(m.homing for m in motes)
    run(world, 2.0)
    assert wisp.hp < wisp.type.hp


def test_motes_ignore_perched_statues():
    _game, world = hold(ROOF, map_name=KEEP, yaw=math.pi, keep_enemies=True)
    world.enemies = [e for e in world.enemies if e.perched]
    pr_ = world.motes(5)[1]
    before = (pr_.dx, pr_.dz)
    world._steer(pr_, 0.1)
    assert (pr_.dx, pr_.dz) == before


# --- enemies ------------------------------------------------------------------------------------


def test_iron_bowmen_loose_arrows_that_fly_fast():
    _game, world = hold(BRIDGE)
    bowman = foe(world, "iron_bowman", (29, 42))
    world.enemy_fire(bowman)
    (arrow,) = world.projectiles
    assert arrow.effect == "arrow"
    assert math.hypot(arrow.dx, arrow.dz) > 10


def test_every_cinderhold_foe_fights_from_its_map_spot():
    _, world = hold(BRIDGE, keep_enemies=True)
    kinds = {e.type.id for e in world.enemies}
    assert {"forge_golem", "iron_bowman", "slag_hound", "mimic"} <= kinds
    _, keep = hold(ROOF, map_name=KEEP, keep_enemies=True)
    assert {"brand", "bellows", "forge_golem", "iron_bowman", "slag_hound"} <= {
        e.type.id for e in keep.enemies
    }


# --- the twin gargoyles --------------------------------------------------------------------------


def test_the_gargoyles_perch_as_statues_until_you_come_near_then_wake_together():
    game, world = hold(ANTECHAMBER, map_name=KEEP, keep_enemies=True)
    pair = twins(world)
    assert set(pair) == {"brand", "bellows"}
    assert all(e.perched and e.alive for e in pair.values())
    run(world, 0.5)
    assert all(e.perched for e in pair.values())  # still too far off
    game.player.x, game.player.z = TileMap.center(*ROOF)
    run(world, 0.2)
    assert not any(e.perched for e in pair.values())
    assert "screech" in game.sounds
    assert sum("tear free" in m for m in game.messages) == 1


def test_striking_a_perched_gargoyle_wakes_it():
    e = Enemy(EnemyTypes.get("brand"), 0, 0)
    assert e.perched
    e.take_hit(3)
    assert not e.perched and e.alive


def test_a_twin_waits_its_turn_while_the_other_is_mid_move():
    _game, world = hold(ROOF, map_name=KEEP, keep_enemies=True)
    pair = twins(world)
    brand, bellows = pair["brand"], pair["bellows"]
    for e in (brand, bellows):
        e.rouse()
        e.cooldowns = dict.fromkeys(e.cooldowns, 0.0)
    brand._begin_windup("slam")
    assert world.twin_busy(bellows)
    assert bellows._pick_move(world, 6.0) is None
    brand._switch("recover")
    assert not world.twin_busy(bellows)


class TwinWorld(FakeWorld):
    def __init__(self, px, pz, fallen=False, busy=False):
        super().__init__(px, pz)
        self.fallen = fallen
        self.busy = busy
        self.breaths = 0
        self.roused = []

    def twin_fallen(self, _enemy):
        return self.fallen

    def twin_busy(self, _enemy):
        return self.busy

    def breath(self, _enemy):
        self.breaths += 1

    def rouse_twin(self, enemy):
        self.roused.append(enemy)


def test_a_twin_flies_into_its_rage_only_when_the_other_falls():
    e = Enemy(EnemyTypes.get("bellows"), 0, 0, rng=random.Random(2))
    e.rouse()
    w = TwinWorld(12.0, 0.0, busy=True)  # its twin keeps it from any special move
    e.hp = 10  # half HP is no trigger for a twin
    tick(e, w, 0.5)
    assert not e.phase2 and w.raged == 0
    w.fallen = True
    tick(e, w, 2.0)
    assert e.phase2 and w.raged == 1
    assert "eruption" in e.cooldowns


def test_bellows_breathes_fire_in_a_line_toward_you_and_past():
    game, world = hold(ROOF, map_name=KEEP, keep_enemies=True)
    bellows = twins(world)["bellows"]
    bellows.rouse()
    world.breath(bellows)
    line = world.eruptions
    assert len(line) >= 4
    px, pz = game.player.x, game.player.z
    reach = max(math.hypot(f.x - bellows.x, f.z - bellows.z) for f in line)
    assert reach > math.hypot(px - bellows.x, pz - bellows.z)  # rakes on past you
    delays = [-f.t for f in line]
    assert delays == sorted(delays)  # bursts in order, from its jaws outward
    assert "breath" in game.sounds


def test_bellows_chooses_its_breath_at_range_and_looses_it_once():
    e = Enemy(EnemyTypes.get("bellows"), 0, 0, rng=random.Random(0))
    e.rouse()
    w = TwinWorld(6.0, 0.0)
    e.cooldowns = {m: (0.0 if m == "breath" else 99.0) for m in e.cooldowns}
    tick(e, w, 0.05)
    assert e.attack_kind == "breath"
    tick(e, w, MOVES["breath"][0] + 0.8)
    assert w.breaths == 1


def test_a_dive_swoops_through_where_you_stood_and_strikes_once():
    e = Enemy(EnemyTypes.get("bellows"), 0, 0, rng=random.Random(0))
    e.rouse()
    w = TwinWorld(8.0, 0.0)
    e.cooldowns = {m: (0.0 if m == "dive" else 99.0) for m in e.cooldowns}
    tick(e, w, 0.05)
    assert e.attack_kind == "dive"
    tick(e, w, MOVES["dive"][0] + 0.1)
    assert e.diving
    tick(e, w, 1.2)
    assert w.strikes == 1 and w.struck == [MOVES["dive"][2]]
    assert e.x > 8.0 + DIVE_OVERSHOOT / 2  # carried on past


def test_the_pair_falls_together_one_relic_one_flag():
    _game, world = hold(ROOF, map_name=KEEP, keep_enemies=True)
    pair = twins(world)
    brand, bellows = pair["brand"], pair["bellows"]
    brand.kill()
    assert not relics.boss_falls(brand.type, world.enemies)  # Bellows fights on
    bellows.kill()
    assert relics.boss_falls(bellows.type, world.enemies)
    assert relics.boss_falls(EnemyTypes.get("ashen_warden"), [])
    # Back on the map later, one Iron Sigil waits on the roof, not two.
    drops = relics.pending_drops(world.map, {"gargoyles_dead"}, lambda _i: False)
    assert [d[0] for d in drops] == ["iron_sigil"]
    assert relics.pending_drops(world.map, {"gargoyles_dead", "iron_sigil_taken"}, lambda _i: False) == []


def test_the_iron_sigil_lies_on_the_roof_once_the_pair_has_fallen():
    _game, world = hold(ROOF, map_name=KEEP, flags={"gargoyles_dead"}, keep_enemies=True)
    assert not twins(world)
    (sigil,) = [p for p in world.props if p.kind == "pickup" and p.props.get("item") == "iron_sigil"]
    assert world.map[sigil.tx, sigil.tz].floor >= 12


def test_a_shrine_rest_brings_a_fallen_twin_back_beside_its_living_other():
    _game, world = hold(ROOF, map_name=KEEP, keep_enemies=True)
    pair = twins(world)
    pair["brand"].kill()
    pair["bellows"].hp = 40
    world.respawn_enemies()
    back = twins(world)
    assert back["brand"].alive and back["bellows"].alive
    assert back["bellows"].hp == back["bellows"].type.hp  # the pair starts over
    assert all(e.perched for e in back.values())


def test_a_shrine_rest_leaves_a_living_pair_as_it_is():
    _game, world = hold(ROOF, map_name=KEEP, keep_enemies=True)
    pair = twins(world)
    pair["bellows"].hp = 40
    world.respawn_enemies()
    assert twins(world)["bellows"] is pair["bellows"] and pair["bellows"].hp == 40


def test_the_three_sigils_end_the_game():
    assert relics.ENDING_RELICS == ("ember_sigil", "verdant_sigil", "iron_sigil")
    assert relics.held(lambda i: i != "verdant_sigil") == ["ember_sigil", "iron_sigil"]
    flags = set()
    relics.mark_taken("iron_sigil", flags)
    assert flags == {"iron_sigil_taken"}


def test_a_fake_game_without_jungle_damage_still_builds_the_hold():
    world = World(FakeGame(), "cinderhold")
    assert world.map.meta["name"] == "The Cinderhold"


def test_the_compass_points_up_to_the_keep_until_the_gargoyles_fall():
    _game, world = hold(BRIDGE)
    (door,) = [p for p in world.props if p.kind == "exit" and p.props.get("map") == KEEP]
    assert world.boss_target() == (door.x, door.z)
    assert world.boss_bearing() is not None
    _game, world = hold(BRIDGE, flags={"gargoyles_dead"})
    assert world.boss_target() is None


def test_the_fortress_mimic_wears_the_iron_chest_disguise():
    _game, world = hold(BRIDGE, keep_enemies=True)
    (mimic,) = [e for e in world.enemies if e.type.id == "mimic"]
    assert mimic.look == "iron"
    chests = [p for p in world.props if p.kind == "chest"]
    assert chests and all(p.props.get("model") == "iron" for p in chests)
