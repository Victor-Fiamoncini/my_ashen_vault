"""Herran's Castle, over the clouds, driven headless: the stair of light up from Lyra's altar in
Vesperholm, the sea of cloud round the castle, and the way through it to the foot of Herran's Spire."""

import math

from ashen_vault import map_path
from ashen_vault.world import terrain
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import PLUNGE_MESSAGES, World
from test_verdant_world import JungleGame
from test_world import BESIDE, _reachable, _spec

CASTLE = "herrans_castle"


def _castle():
    return MapLoader.load_file(map_path(CASTLE))


def _vesperholm():
    return MapLoader.load_file(map_path("vesperholm"))


def _at(exit_spec):
    tx, tz, _yaw = (int(v) for v in exit_spec.props["at"].split(","))
    return tx, tz


def _start(m):
    return tuple(int(v) for v in m.meta["start"][:2])


def test_the_stair_of_light_joins_lyras_altar_and_the_cloud_quay_both_ways():
    """Off the bridge beside Lyra's altar a stair of light climbs to the Cloud Quay, where you arrive
    with its head right behind you; going back down puts you on the bridge beside it."""
    city, castle = _vesperholm(), _castle()
    (up,) = _spec(city, "exit", map=CASTLE)
    (down,) = _spec(castle, "exit", map="vesperholm")
    assert up.props["model"] == down.props["model"] == "sky_stair"
    assert _at(up) == _start(castle)
    assert sum(abs(a - b) for a, b in zip(_at(up), (down.tx, down.tz), strict=True)) == 1
    bx, bz = _at(down)
    assert abs(bx - up.tx) + abs(bz - up.tz) == 1 and city[bx, bz].walkable
    (altar,) = _spec(city, "altar", item="argent_sigil")
    assert city[up.tx, up.tz].floor == city[altar.tx, altar.tz].floor  # on the altar's bridge
    assert abs(up.tx - altar.tx) + abs(up.tz - altar.tz) == 2  # not on its doorstep: the altar keeps its own


def test_the_stair_of_light_is_not_there_until_the_argent_sigil_is_taken():
    for flags, there in (((), False), (("duchess_dead",), False), (("argent_sigil_taken",), True)):
        world = World(JungleGame(flags), "vesperholm")
        (stair,) = [p for p in world.props if p.kind == "exit" and p.props.get("map") == CASTLE]
        assert world.exit_open(stair) is there
        assert world._interactable(stair) is there


def test_the_castle_floats_on_a_sea_of_cloud_you_fall_through_to_your_death():
    """All round the castle, and under its bridges, lies the sea of cloud: a chasm far below with
    words of its own for the fall. Every edge of the map is cloud, and no rim wall stands round it."""
    m = _castle()
    assert m.meta["sky"] == "storm" and m.meta["name"] == "Herran's Castle"
    edges = [(tx, 0) for tx in range(m.width)] + [(tx, m.depth - 1) for tx in range(m.width)]
    edges += [(0, tz) for tz in range(m.depth)] + [(m.width - 1, tz) for tz in range(m.depth)]
    for tx, tz in edges:
        tile = m[tx, tz]
        assert tile.chasm and tile.fall == "cloud" and tile.floor <= -30, (tx, tz)
    assert float(m.meta["edge_top"]) <= min(m[t].floor for t in edges)
    falls = {t.fall for _tx, _tz, t in m.each_tile() if t.fall}
    assert falls <= PLUNGE_MESSAGES.keys()


def test_stepping_off_the_quays_broken_balustrade_is_a_fall_through_the_clouds():
    game = JungleGame()
    world = World(game, CASTLE)
    world.enemies = []
    gap = next(
        (tx, tz)
        for tz in range(world.map.depth)
        for tx in range(world.map.width - 1)
        if world.map[tx, tz].walkable
        and world.map[tx, tz].floor == 0
        and world.map[tx + 1, tz].fall == "cloud"
    )
    p = game.player
    p.x, p.z = TileMap.center(*gap)
    p.y = 0
    for _ in range(4):
        world.update_terrain(0.05)
    p.x, p.z = TileMap.center(gap[0] + 1, gap[1])
    for _ in range(round((terrain.PLUNGE_TIME + 0.3) / 0.05)):
        world.update_terrain(0.05)
    assert PLUNGE_MESSAGES["cloud"] in game.messages
    assert not p.alive


def test_herrans_castle_is_solvable_up_to_the_spires_door():
    """From the Cloud Quay every chest can be reached, the hidden labs' only through their false walls;
    the Spire Key lies in the open laboratory, reached before the spire's door it opens. The Belvedere's
    lift is a shortcut down to the court, both ends of it reached before its first ride, and nowhere
    you can get to strands you."""
    m = _castle()
    start = _start(m)
    plain = [(s.tx, s.tz) for s in _spec(m, "door") if "key" not in s.props]
    (spire_door,) = _spec(m, "door", key="spire_key")
    secrets = [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    assert len(secrets) == 3
    before = _reachable(m, start, open_tiles=plain)
    (key_chest,) = _spec(m, "chest", item="spire_key")
    assert (key_chest.tx, key_chest.tz) in before
    assert (spire_door.tx, spire_door.tz) not in before
    beside_door = {(spire_door.tx + dx, spire_door.tz + dz) for dx, dz in BESIDE}
    assert beside_door & before  # you come to the door with the key in hand
    hidden = _reachable(m, start, open_tiles=[*plain, *secrets])
    for chest in _spec(m, "chest"):
        assert (chest.tx, chest.tz) in hidden, chest.props
    labs = [c for c in _spec(m, "chest") if m[c.tx, c.tz].floor_tex == "lab_tile" and c is not key_chest]
    assert len(labs) == 3
    for chest in labs:  # each hidden lab's chest lies behind its false wall
        assert (chest.tx, chest.tz) not in before, chest.props
    (lift,) = _spec(m, "lift")
    assert "locked" in lift.props
    ends = [(lift.tx + dx, lift.tz + dz) for dx, dz in BESIDE if m[lift.tx + dx, lift.tz + dz].walkable]
    assert len(ends) == 2 and all(e in before for e in ends)
    assert {m[e].floor for e in ends} == {1.0, 10.0}
    doors = [*plain, *secrets, (spire_door.tx, spire_door.tz)]
    full = _reachable(m, start, open_tiles=doors, shortcuts=True)
    for tile in full:
        assert start in _reachable(m, tile, open_tiles=doors, shortcuts=True), tile


def test_the_castle_climbs_in_steps_never_too_tall():
    """The Great Stair and the clock tower's inner stair climb half a metre a tile, from the court at
    1 m to the terrace at 6 and the bridges at 10."""
    m = _castle()
    floors = {
        m[t].floor for t in _reachable(m, _start(m), open_tiles=[(s.tx, s.tz) for s in _spec(m, "door")])
    }
    assert {0.0, 1.0, 6.0, 10.0} <= floors


def test_the_castles_dressing_draws_and_stands_still():
    """Every piece of the castle's dressing is a model of some detail, stands on its floor and is baked
    once; the towers on the skyline are each their own shape."""
    from ashen_vault.render import herran_models, mesh_builder, rig
    from ashen_vault.world.world import BLOCKING_PROPS, LANDMARKS, STATIC_PROPS, WALL_PROPS
    from test_render_logic import _RecordingGpu

    def parts(fn):
        gpu = _RecordingGpu()
        fn(rig.Rig(gpu))
        return gpu.parts

    pieces = {
        "gas_lamp": lambda r: herran_models.gas_lamp(r, 4),
        "glasshouse": lambda r: herran_models.glasshouse(r, 18.0, 38.0, 8.0),
        "drake_fountain": lambda r: herran_models.drake_fountain(r, 4),
        "specimen_jar": lambda r: herran_models.specimen_jar(r, 4),
        "alembic_bench": lambda r: herran_models.alembic_bench(r, 4),
        "vat": lambda r: herran_models.vat(r, 4),
        "surgery_table": lambda r: herran_models.surgery_table(r, 4),
        "potion_shelf": lambda r: herran_models.potion_shelf(r, 4),
    }
    for name, fn in pieces.items():
        drawn = parts(fn)
        assert len(drawn) >= 12, name
        assert min(y for _, y in drawn) > -0.1, name
        assert name in STATIC_PROPS, name
    towers = {
        style: parts(lambda r, s=style: herran_models.herran_tower(r, 4, 14.0, s))
        for style in ("round", "octagon", "clock", "belvedere", "needle")
    }
    assert len({tuple(p) for p in towers.values()}) == len(towers)  # no two alike
    assert {"herran_tower", "glasshouse"} <= set(LANDMARKS) and "herran_tower" in STATIC_PROPS
    assert {"gas_lamp", "drake_fountain", "specimen_jar", "vat"} <= set(BLOCKING_PROPS)
    assert "potion_shelf" in WALL_PROPS
    assert {"gas_lamp", "specimen_jar"} <= set(mesh_builder.LIGHT_KINDS)
    m = _castle()
    styles = [s.props["style"] for s in _spec(m, "herran_tower")]
    assert {"round", "octagon", "clock", "belvedere", "needle"} <= set(styles)
    for s in _spec(m, "herran_tower"):
        assert m[s.tx, s.tz].solid, (s.tx, s.tz)  # on a wall top no one walks


def test_a_graft_draught_costs_hp_and_speeds_stamina_for_a_while():
    from ashen_vault.player import player as player_mod
    from ashen_vault.player.player import Player

    p = Player()
    hp = p.stats.hp
    p.drink("graft")
    assert p.stats.hp == hp - player_mod.GRAFT_HP and p.graft_t == player_mod.GRAFT_TIME
    p.stamina.spend(50)
    p.update_timers(0.6)  # past the rest before it starts refilling
    before = p.stamina.value
    p.update_timers(0.5)
    grafted = p.stamina.value - before
    q = Player()
    q.stamina.spend(50)
    q.update_timers(0.6)
    before = q.stamina.value
    q.update_timers(0.5)
    assert grafted > q.stamina.value - before > 0  # it refills faster while the draught lasts
    p.update_timers(player_mod.GRAFT_TIME)
    assert p.graft_t == 0
    weak = Player()
    weak.stats.hp = 3
    weak.drink("graft")
    assert weak.stats.hp == 1  # it never takes the last HP


def test_a_sun_tincture_cures_everything_and_keeps_ailments_out_for_a_minute():
    from ashen_vault.player import ailments
    from ashen_vault.player.items import Items
    from ashen_vault.player.player import Player

    tincture = Items.get("sun_tincture")
    assert set(tincture.cures) == set(ailments.KINDS)
    p = Player()
    p.ailments.build("poison", ailments.FULL)
    assert p.ailments.poisoned
    for kind in tincture.cures:
        p.cure(kind)
    p.drink(tincture.effect)
    assert not p.ailments.poisoned
    assert not p.ailments.build("bleed", ailments.FULL) and p.ailments.meters["bleed"] == 0
    p.ailments.update(ailments.SUN_WARD_TIME, p.stats.max_hp)
    assert p.ailments.build("bleed", ailments.FULL)  # the ward has worn off


def test_the_hidden_labs_keep_herrans_brews_and_his_bonesaw():
    m = _castle()
    found = {c.props["item"] for c in _spec(m, "chest") if m[c.tx, c.tz].floor_tex == "lab_tile"}
    assert {"graft_draught", "sun_tincture", "herran_bonesaw", "spire_key"} <= found


def test_herrans_journal_fits_the_screen_and_names_his_mother_and_sister():
    from ashen_vault.screen import W
    from ashen_vault.ui import smallfont

    world = World(JungleGame(), CASTLE)
    text = " ".join(line for h in world.hints.values() for line in h.lines)
    assert "Embracer" in text and "Ilvane" in text and "Mother" in text
    for h in world.hints.values():
        assert 1 <= len(h.lines) <= 2
        assert all(smallfont.width(line) <= W - 40 for line in h.lines), h.lines


def test_herrans_creatures_outmatch_vesperholms():
    """Past Vesperholm: every regular foe of the castle hits harder than any regular foe before it."""
    from ashen_vault.ai.enemy_types import EnemyTypes

    castle = ("grafted_drake", "drake_magus", "vat_spawn")
    before = [t for t in EnemyTypes.ALL.values() if t.id not in (*castle, "herran")]
    strongest = max(t.damage for t in before if not (t.boss or t.ambush))
    assert all(EnemyTypes.get(i).damage > strongest for i in castle)
    assert EnemyTypes.get("grafted_drake").fly and "rend" in EnemyTypes.get("grafted_drake").moves
    assert EnemyTypes.get("drake_magus").ranged and EnemyTypes.get("drake_magus").shot is None


def test_a_landed_drake_rends_and_a_magus_brands_the_floor_under_you():
    from ashen_vault.ai.enemy import MOVE_SPECS
    from test_verdant_world import foe

    game = JungleGame()
    world = World(game, CASTLE)
    world.enemies = []
    game.player.place(*TileMap.center(27, 57 + 2), 0.0, world.map)
    drake = foe(world, "grafted_drake", (28, 59))
    assert not world.grounded(drake)  # on the wing it only stoops
    drake.landed, drake.alt = True, 0.0  # come down to fight on foot
    assert world.grounded(drake) and MOVE_SPECS["rend"].allow == "grounded"
    hp = game.player.stats.hp
    world.rend(drake)
    assert game.player.stats.hp < hp
    magus = foe(world, "drake_magus", (27, 52))
    world.sunbrand(magus)
    (brand,) = world.eruptions
    assert (
        brand.style == "sun" and math.isclose(brand.x, game.player.x) and math.isclose(brand.z, game.player.z)
    )


SPIRE = "herran_spire"


def _spire():
    return MapLoader.load_file(map_path(SPIRE))


def test_the_spire_door_and_its_way_back_lead_to_each_other():
    """At the end of the passage behind the locked door, the spire's door lets you into its base hall,
    the way back right behind you; going back out puts you in the passage before it. The compass points
    at it while Herran lives."""
    castle, spire = _castle(), _spire()
    (into,) = _spec(castle, "exit", map=SPIRE)
    (out,) = _spec(spire, "exit", map=CASTLE)
    assert into.props["model"] == out.props["model"] == "spire_door" and into.props["boss"] == "herran_dead"
    assert _at(into) == _start(spire)
    assert sum(abs(a - b) for a, b in zip(_at(into), (out.tx, out.tz), strict=True)) == 1
    bx, bz = _at(out)
    assert abs(bx - into.tx) + abs(bz - into.tz) == 1 and castle[bx, bz].walkable
    (door,) = _spec(castle, "door", key="spire_key")
    assert (into.tx, into.tz) not in _reachable(castle, _start(castle))
    plain = [(s.tx, s.tz) for s in _spec(castle, "door") if "key" not in s.props]
    assert (bx, bz) in _reachable(castle, _start(castle), open_tiles=[*plain, (door.tx, door.tz)])


def test_herrans_spire_climbs_to_his_observatory_and_he_waits_only_behind_his_door():
    """From the base hall a stair climbs to the hatchery and on to the study, where the shrine stands;
    Herran waits out in his observatory, open to the sky, only through his great door. It stands 11 m
    up, and nowhere you can reach strands you."""
    m = _spire()
    assert m.meta["name"] == "Herran's Spire" and m.meta["sky"] == "storm"
    start = _start(m)
    (door,) = _spec(m, "door", boss="herran_dead")
    (herran,) = _spec(m, "herran")
    (shrine,) = _spec(m, "save_statue")
    before = _reachable(m, start)
    assert (herran.tx, herran.tz) not in before
    assert any((shrine.tx + dx, shrine.tz + dz) in before for dx, dz in BESIDE)
    assert abs(shrine.tx - door.tx) + abs(shrine.tz - door.tz) <= 10  # a shrine in the study before his door
    opened = _reachable(m, start, open_tiles=[(door.tx, door.tz)])
    assert (herran.tx, herran.tz) in opened
    lair = m[herran.tx, herran.tz]
    assert lair.ceil is None and lair.floor == 11
    for s in m.entities:
        if s.kind in ("chest", "exit", "save_statue"):
            assert any((s.tx + dx, s.tz + dz) in before for dx, dz in BESIDE), (s.kind, s.tx, s.tz)
    for tile in opened:
        assert start in _reachable(m, tile, open_tiles=[(door.tx, door.tz)]), tile


def test_herran_drops_the_auric_sigil_and_turns_in_his_rage():
    from ashen_vault.ai.enemy_types import EnemyTypes

    t = EnemyTypes.get("herran")
    assert t.boss and t.drop == "auric_sigil" and t.dead_flag == "herran_dead" and t.rise == "ash"
    assert t.rage and set(t.phase_moves) == {"embrace", "solar_gaze"}
    assert t.hp > EnemyTypes.get("moon_duchess").hp and t.damage > EnemyTypes.get("moon_duchess").damage


def _herran_at(at=(23, 3), herran_at=(23, 8)):
    from test_verdant_world import foe

    game = JungleGame()
    world = World(game, SPIRE)
    world.enemies = []
    game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world, foe(world, "herran", herran_at)


def test_herrans_hands_rise_in_a_line_and_his_elixir_lands_where_you_stood():
    game, world, herran = _herran_at()
    world.hand_rain(herran)
    hands = [f for f in world.eruptions if f.style == "grafts"]
    assert len(hands) >= 3
    assert sorted(h.warn for h in hands) == [h.warn for h in sorted(hands, key=lambda h: h.warn)]
    world.eruptions = []
    world.elixir_hurl(herran)
    (flask,) = world.eruptions
    assert flask.style == "elixir" and flask.origin is not None
    assert math.isclose(flask.x, game.player.x) and math.isclose(flask.z, game.player.z)


def test_herrans_sweep_and_embrace_reach_only_so_far():
    from ashen_vault.ai.enemy import EMBRACE_REACH, GRASP_SWEEP_REACH

    game, world, herran = _herran_at(at=(23, 7))
    hp = game.player.stats.hp
    world.grasp_sweep(herran)
    assert game.player.stats.hp < hp
    hp = game.player.stats.hp
    world.embrace(herran)
    assert game.player.stats.hp < hp and game.player.webbed_t > 0
    game, world, herran = _herran_at(at=(23, 2))
    assert math.hypot(game.player.x - herran.x, game.player.z - herran.z) > max(
        GRASP_SWEEP_REACH, EMBRACE_REACH
    )
    hp = game.player.stats.hp
    world.grasp_sweep(herran)
    world.embrace(herran)
    assert game.player.stats.hp == hp
