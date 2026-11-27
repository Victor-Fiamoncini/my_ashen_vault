"""Herran's Castle on the Hollow Peak, driven headless: the portal from Lyra's Chapel in Vesperholm,
the gorge under the causeway, the barbican's sealed gate and its Wardens, the Hall of Sentinels, the
keep, the way down to the laboratory, and Herran in his anatomy theatre."""

import math

from ashen_vault import map_path
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.world import seals, terrain
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import PLUNGE_MESSAGES, World
from test_verdant_world import JungleGame, foe
from test_world import BESIDE, _reachable, _spec

CASTLE = "herrans_castle"
LAB = "herran_laboratory"
CASTLE_FOES = ("grafted_footman", "castellan_warden", "amalgam", "handcrawler")
SENTINELS = ("bulwark_sentinel", "blade_sentinel")


def _castle():
    return MapLoader.load_file(map_path(CASTLE))


def _at(exit_spec):
    tx, tz, _yaw = (int(v) for v in exit_spec.props["at"].split(","))
    return tx, tz


def _start(m):
    return tuple(int(v) for v in m.meta["start"][:2])


def _beside(m, spec, reached):
    return any((spec.tx + dx, spec.tz + dz) in reached for dx, dz in BESIDE)


def _gate(m):
    (gate,) = _spec(m, "door", seal="gate")
    return gate


def _doors(m, *, gate=True, sentinels=True, herran=True, secret=True):
    """The tiles to count as open: the sealed gate, each boss's doors and the false wall, as asked."""
    tiles = []
    for s in _spec(m, "door"):
        boss = s.props.get("boss")
        if (
            (s.props.get("seal") and gate)
            or (boss == "sentinels_dead" and sentinels)
            or (boss == "herran_dead" and herran)
        ):
            tiles.append((s.tx, s.tz))
    if secret:
        tiles += [(s.tx, s.tz) for s in _spec(m, "secret_wall")]
    return tiles


def test_the_portal_joins_lyras_chapel_and_the_portal_ledge_both_ways():
    """In the apse of Lyra's Chapel a portal opens onto the Portal Ledge below the castle, where you
    arrive with its twin right behind you; stepping back through puts you in the chapel before it."""
    city, castle = MapLoader.load_file(map_path("vesperholm")), _castle()
    (up,) = _spec(city, "exit", map=CASTLE)
    (down,) = _spec(castle, "exit", map="vesperholm")
    assert up.props["model"] == down.props["model"] == "argent_portal"
    assert "hidden" in up.props and up.props["requires"] == "argent_sigil_taken"
    assert _at(up) == _start(castle)
    assert sum(abs(a - b) for a, b in zip(_at(up), (down.tx, down.tz), strict=True)) == 1
    bx, bz = _at(down)
    assert abs(bx - up.tx) + abs(bz - up.tz) == 1 and city[bx, bz].walkable


def test_the_castle_stands_on_the_mountain_in_the_storm():
    m = _castle()
    assert m.meta["name"] == "Herran's Castle" and m.meta["sky"] == "storm"
    (peak,) = _spec(m, "hollow_peak")
    assert peak.tz == 0 and m[peak.tx, peak.tz].solid  # beyond the keep, out of reach
    towers = _spec(m, "castle_tower")
    assert len(towers) >= 8  # many towers
    assert {"round", "square", "octagon", "belfry", "keep"} <= {t.props["style"] for t in towers}
    for t in towers:
        assert m[t.tx, t.tz].solid, (t.tx, t.tz)  # each stands where no one walks
    falls = {
        m[tx, tz].fall for tx, tz, tile in m.each_tile() if (tile.chasm and not tile.walkable) or tile.chasm
    }
    assert falls - {None} <= PLUNGE_MESSAGES.keys()


def test_stepping_off_the_causeway_where_its_parapet_has_fallen_is_a_plunge_into_the_gorge():
    game = JungleGame()
    world = World(game, CASTLE)
    world.enemies = []
    gap = next(
        (tx, tz)
        for tz in range(world.map.depth)
        for tx in range(1, world.map.width)
        if world.map[tx, tz].walkable
        and world.map[tx, tz].floor == 0
        and world.map[tx - 1, tz].fall == "gorge"
    )
    p = game.player
    p.x, p.z = TileMap.center(*gap)
    p.y = 0
    for _ in range(4):
        world.update_terrain(0.05)
    p.x, p.z = TileMap.center(gap[0] - 1, gap[1])
    for _ in range(round((terrain.PLUNGE_TIME + 0.3) / 0.05)):
        world.update_terrain(0.05)
    assert PLUNGE_MESSAGES["gorge"] in game.messages
    assert not p.alive


def test_the_barbican_gate_is_sealed_by_the_two_wardens_atop_its_towers():
    """The gate is bound to two Castellan Wardens, each on a tower's deck, which a lift climbs from the
    platform before it; both lifts and both Wardens are reached before the gate opens, and beyond it
    lies the rest of the castle. Every guardian is a foe that stays dead."""
    m = _castle()
    gate = _gate(m)
    assert gate.props["model"] == "sealed"
    wardens = _spec(m, "castellan_warden")
    assert len(wardens) == 2 and all(w.props["seal"] == "gate" for w in wardens)
    assert sorted(seals.guardians(m, "gate")) == sorted((w.tx, w.tz) for w in wardens)
    assert EnemyTypes.get("castellan_warden").once
    for s in m.entities:  # nothing else is bound to a seal, and every guardian stays dead
        if s.props.get("seal") and s.kind != "door":
            assert EnemyTypes.get(s.kind).once, s.kind
    before = _reachable(m, _start(m), open_tiles=[])
    for w in wardens:
        assert (w.tx, w.tz) in before
        assert m[w.tx, w.tz].floor == 8  # up on the tower's deck
    assert len(_spec(m, "lift")) == 2 and not any("locked" in s.props for s in _spec(m, "lift"))
    assert (gate.tx, gate.tz) not in before and _beside(m, gate, before)
    (shrine,) = [s for s in _spec(m, "save_statue") if s.tz < gate.tz and s.tz > 24]
    assert not _beside(m, shrine, before)  # the ward's shrine waits past the gate
    assert _beside(m, shrine, _reachable(m, _start(m), open_tiles=[(gate.tx, gate.tz)]))


def test_the_seal_breaks_only_once_both_wardens_have_fallen_and_stays_broken():
    game = JungleGame()
    world = World(game, CASTLE)
    (gate,) = [p for p in world.props if p.kind == "door" and p.props.get("seal")]
    assert world.seal_eyes(gate) == 2 and not world.seal_broken(gate)
    world.update(0.016)
    assert gate.open_t == 0
    first, second = seals.guardians(world.map, "gate")
    game.flags.add(f"slain:{CASTLE}:{first[0]},{first[1]}")
    world.update(0.016)
    assert world.seal_eyes(gate) == 1 and gate.open_t == 0
    game.flags.add(f"slain:{CASTLE}:{second[0]},{second[1]}")
    world.update(0.016)
    assert world.seal_eyes(gate) == 0 and gate.open_t > 0 and gate.key in game.flags
    assert any("grinds open" in m for m in game.messages)
    again = World(JungleGame(game.flags), CASTLE)  # a later visit: the gate stands open, the Wardens gone
    (gate,) = [p for p in again.props if p.kind == "door" and p.props.get("seal")]
    assert gate.open_t == 1.0
    assert not [e for e in again.enemies if e.type.id == "castellan_warden"]


def test_a_seal_with_no_guardians_never_breaks():
    m = _castle()
    assert seals.guardians(m, "nothing") == [] and not seals.broken(m, set(), "nothing")


def test_the_hall_of_sentinels_holds_two_stone_twins_between_its_two_doors():
    """West of the Great Hall, up a short stair, two stone giants wait as statues between the hall's
    great door and its rear door onto the keep stair; each drops a piece of its armour."""
    m = _castle()
    front = [s for s in _spec(m, "door", boss="sentinels_dead") if "rear" not in s.props]
    rear = [s for s in _spec(m, "door", boss="sentinels_dead") if "rear" in s.props]
    assert len(front) == len(rear) == 1
    for i, j in ((0, 1), (1, 0)):
        t = EnemyTypes.get(SENTINELS[i])
        assert t.boss and t.perch and t.twin == SENTINELS[j] and t.dead_flag == "sentinels_dead"
        assert t.brittle and t.tall >= 4.5
    drops = {s.props["item"] for k in SENTINELS for s in _spec(m, k)}
    assert drops == {"sentinel_plate", "sentinel_gauntlets"}
    gate = _gate(m)
    past_gate = _reachable(m, _start(m), open_tiles=[(gate.tx, gate.tz)])
    for k in SENTINELS:
        (s,) = _spec(m, k)
        assert (s.tx, s.tz) not in past_gate
    assert _beside(m, front[0], past_gate) and not _beside(m, rear[0], past_gate)


def test_the_castle_is_solvable_to_herrans_door_and_never_strands_you():
    """From the ledge: past the sealed gate, through the Hall of Sentinels, up the keep to Herran's
    door; every chest is reached, the study's shrine stands before his door, and nowhere you can get to
    strands you."""
    m = _castle()
    start = _start(m)
    (door,) = _spec(m, "door", boss="herran_dead")
    (herran,) = _spec(m, "herran")
    open_ = _doors(m, herran=False)
    before = _reachable(m, start, open_tiles=open_)
    assert (herran.tx, herran.tz) not in before and _beside(m, door, before)
    study_shrine = min(_spec(m, "save_statue"), key=lambda s: abs(s.tx - door.tx) + abs(s.tz - door.tz))
    assert abs(study_shrine.tx - door.tx) + abs(study_shrine.tz - door.tz) <= 8 and _beside(
        m, study_shrine, before
    )
    for s in m.entities:
        if s.kind in ("chest", "exit", "save_statue"):
            assert _beside(m, s, before) or (s.tx, s.tz) in before, (s.kind, s.tx, s.tz)
    full = _reachable(m, start, open_tiles=_doors(m))
    assert (herran.tx, herran.tz) in full
    lair = m[herran.tx, herran.tz]
    assert lair.ceil is None and lair.floor == 10  # open to the storm, at the top of the keep
    for tile in full:
        assert start in _reachable(m, tile, open_tiles=_doors(m)), tile


def test_the_way_up_climbs_half_a_metre_a_tile_at_most():
    """From the ledge to the library at 8 m and the theatre at 10, the stairs rise no more than half a
    metre a tile, so the keep is walked up, never dropped down (the towers' decks are reached by lift)."""
    m = _castle()
    blocked = {(s.tx, s.tz) for s in m.entities if s.kind in ("door", "secret_wall")} - set(_doors(m))
    seen, todo = {_start(m)}, [_start(m)]
    while todo:
        x, z = todo.pop()
        for dx, dz in BESIDE:
            n = (x + dx, z + dz)
            if n in seen or n in blocked or not m[n].walkable or m[n].needs_footing:
                continue
            if abs(m[n].floor - m[x, z].floor) <= 0.5:
                seen.add(n)
                todo.append(n)
    (herran,) = _spec(m, "herran")
    assert (herran.tx, herran.tz) in seen
    assert {0.0, 2.0, 8.0, 10.0} <= {m[t].floor for t in seen}


def test_the_library_hides_the_way_down_to_the_laboratory_and_it_comes_back_up():
    """Behind the library's one false wall, a stair goes down into the mountain to the laboratory; its
    foot leads back to the passage behind the wall. The laboratory's far stair climbs out to the Great
    Hall, one way."""
    m, lab = _castle(), MapLoader.load_file(map_path(LAB))
    (secret,) = _spec(m, "secret_wall")
    (down,) = _spec(m, "exit", map=LAB)
    assert m[secret.tx, secret.tz].floor == 8 and m[down.tx, down.tz].floor == 8
    no_secret = _reachable(m, _start(m), open_tiles=_doors(m, secret=False, herran=False))
    assert not _beside(m, down, no_secret)
    assert _beside(m, down, _reachable(m, _start(m), open_tiles=_doors(m, herran=False)))
    assert _at(down) == _start(lab)
    back = [s for s in _spec(lab, "exit", map=CASTLE) if "oneway" not in s.props]
    (out,) = [s for s in _spec(lab, "exit", map=CASTLE) if "oneway" in s.props]
    assert len(back) == 1 and _at(back[0]) in no_secret | {(secret.tx, secret.tz + 1)}
    assert m[_at(back[0])].floor == 8
    hall = _at(out)
    assert m[hall].floor == 0 and m[hall].ceil == 12  # out in the Great Hall
    assert hall in _reachable(m, _start(m), open_tiles=[(_gate(m).tx, _gate(m).tz)])


def test_the_laboratory_is_dark_solvable_and_full_of_his_failures():
    lab = MapLoader.load_file(map_path(LAB))
    assert lab.meta["name"] == "Herran's Laboratory" and "sky" not in lab.meta
    start = _start(lab)
    reached = _reachable(lab, start)
    floors = [tile for tx, tz, tile in lab.each_tile() if tile.walkable]
    assert floors and all(tile.dark >= 0.6 for tile in floors)
    for s in lab.entities:
        if s.kind in ("chest", "exit"):
            assert _beside(lab, s, reached) or (s.tx, s.tz) in reached, (s.kind, s.tx, s.tz)
    items = {s.props["item"] for s in _spec(lab, "chest")}
    assert "surgeons_cleaver" in items
    kinds = {s.kind for s in lab.entities}
    assert {
        "amalgam",
        "handcrawler",
        "vat",
        "specimen_cage",
        "hand_rack",
        "dissecting_table",
        "lab_bench",
    } <= kinds
    assert len(_spec(lab, "hint")) >= 2
    for tile in reached:
        assert start in _reachable(lab, tile), tile


def test_herrans_journal_fits_the_screen():
    from ashen_vault.screen import W
    from ashen_vault.ui import smallfont

    for name in (CASTLE, LAB):
        for h in _spec(MapLoader.load_file(map_path(name)), "hint"):
            lines = h.props["text"].split("|")
            assert 1 <= len(lines) <= 2
            for line in lines:
                assert smallfont.width(line) <= W - 40, line


def test_herrans_creatures_outmatch_vesperholms():
    """Past Vesperholm: every regular foe of the castle and the laboratory hits harder than any regular
    foe before it, and the sentinels and Herran outmatch the Duchess."""
    later = {*CASTLE_FOES, *SENTINELS, "herran"}
    before = [t for t in EnemyTypes.ALL.values() if t.id not in later]
    strongest = max(t.damage for t in before if not (t.boss or t.ambush))
    assert all(EnemyTypes.get(i).damage > strongest for i in CASTLE_FOES)
    duchess = EnemyTypes.get("moon_duchess")
    assert all(EnemyTypes.get(i).damage > duchess.damage - 1 for i in SENTINELS)
    herran = EnemyTypes.get("herran")
    assert herran.hp > duchess.hp and herran.damage > duchess.damage


def test_herran_waits_only_behind_his_door_and_drops_the_auric_sigil():
    t = EnemyTypes.get("herran")
    assert t.boss and t.drop == "auric_sigil" and t.dead_flag == "herran_dead" and t.rise == "ash"
    assert t.rage and set(t.phase_moves) == {"embrace", "solar_gaze"}
    m = _castle()
    (herran,) = _spec(m, "herran")
    (dome,) = _spec(m, "anatomy_dome")
    assert abs(dome.tx - herran.tx) + abs(dome.tz - herran.tz) <= 2


def _herran_at(at, herran_at=(31, 6)):
    game = JungleGame()
    world = World(game, CASTLE)
    world.enemies = []
    game.player.place(*TileMap.center(*at), 0.0, world.map)
    return game, world, foe(world, "herran", herran_at)


def test_herrans_hands_rise_in_a_line_and_his_elixir_lands_where_you_stood():
    game, world, herran = _herran_at((27, 6))
    world.hand_rain(herran)
    hands = [f for f in world.eruptions if f.style == "grafts"]
    assert len(hands) >= 3
    assert sorted(h.warn for h in hands) == [h.warn for h in sorted(hands, key=lambda h: h.warn)]
    world.eruptions = []
    world.elixir_hurl(herran)
    (flask,) = world.eruptions
    assert flask.style == "elixir" and flask.origin is not None
    assert math.isclose(flask.x, game.player.x) and math.isclose(flask.z, game.player.z)
    world.eruptions = []
    world.solar_gaze(herran)
    assert world.eruptions and all(f.style == "sun" for f in world.eruptions)


def test_herrans_sweep_and_embrace_reach_only_so_far():
    from ashen_vault.ai.enemy import EMBRACE_REACH, GRASP_SWEEP_REACH

    game, world, herran = _herran_at((30, 6))
    hp = game.player.stats.hp
    world.grasp_sweep(herran)
    assert game.player.stats.hp < hp
    hp = game.player.stats.hp
    world.embrace(herran)
    assert game.player.stats.hp < hp and game.player.webbed_t > 0
    game, world, herran = _herran_at((26, 2))
    assert math.hypot(game.player.x - herran.x, game.player.z - herran.z) > max(
        GRASP_SWEEP_REACH, EMBRACE_REACH
    )
    hp = game.player.stats.hp
    world.grasp_sweep(herran)
    world.embrace(herran)
    assert game.player.stats.hp == hp


def test_every_new_prop_and_landmark_is_built_in_detail():
    from ashen_vault.render import herran_models, rig
    from ashen_vault.world.world import BLOCKING_PROPS, LANDMARKS, STATIC_PROPS, WALL_PROPS
    from test_render_logic import _RecordingGpu

    def parts(fn):
        gpu = _RecordingGpu()
        fn(rig.Rig(gpu))
        return gpu.parts

    built = {
        "candelabra": lambda r: herran_models.candelabra(r, 4, 0.3),
        "gate_statue": lambda r: herran_models.gate_statue(r, 4),
        "vat": lambda r: herran_models.vat(r, 4, 0.3),
        "dissecting_table": lambda r: herran_models.dissecting_table(r, 4),
        "specimen_cage": lambda r: herran_models.specimen_cage(r, 4),
        "hand_rack": lambda r: herran_models.hand_rack(r, 4),
        "lab_bench": lambda r: herran_models.lab_bench(r, 4),
        "anatomy_dome": lambda r: herran_models.anatomy_dome(r, 11.0, 1.2),
        "hollow_peak": lambda r: herran_models.hollow_peak(r, 4, 140.0, 120.0),
        "sealed_gate": lambda r: herran_models.sealed_gate(r, 0.0, 5.0, 2, 0.3),
        **{
            f"castle_tower {style}": lambda r, s=style: herran_models.castle_tower(r, 4, 26.0, s)
            for style in ("round", "square", "octagon", "belfry", "keep")
        },
    }
    for name, fn in built.items():
        assert len(parts(fn)) >= 20, name
    looks = {len(parts(lambda r, s=s: herran_models.castle_tower(r, 4, 26.0, s))) for s in
             ("round", "square", "octagon", "belfry", "keep")}  # fmt: skip
    assert len(looks) == 5  # no two tower styles alike
    assert {"castle_tower", "hollow_peak", "anatomy_dome"} <= set(LANDMARKS) <= set(LANDMARKS) | STATIC_PROPS
    assert {"candelabra", "gate_statue", "vat", "dissecting_table", "specimen_cage", "lab_bench"} <= set(
        BLOCKING_PROPS
    )
    assert "hand_rack" in WALL_PROPS
    lit, out = parts(lambda r: herran_models.sealed_gate(r, 0.0, 5.0, 2, 0.0)), None
    out = parts(lambda r: herran_models.sealed_gate(r, 0.0, 5.0, 0, 0.0))
    assert len(lit) == len(out)  # its eyes go out; nothing else changes


def test_the_sentinels_drop_their_armour_and_the_laboratory_keeps_herrans_cleaver():
    from ashen_vault.player.items import Items

    plate, gauntlets, cleaver = (
        Items.get("sentinel_plate"),
        Items.get("sentinel_gauntlets"),
        Items.get("surgeons_cleaver"),
    )
    assert plate.slot == "body" and gauntlets.slot == "hands" and cleaver.category == "axe"
    assert plate.power > Items.get("brigandine").power
