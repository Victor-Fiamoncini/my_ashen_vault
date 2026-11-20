"""A cavern's vault (`world/vault.py`): Old Harrowmere's roof of rock, its stalactites and the crack in
it over the shaft of daylight."""

import math

import pytest

from ashen_vault import map_path
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.world import vault
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.vault import MAX_DROP, Vault


def _harrowmere():
    return MapLoader.load_file(map_path("old_harrowmere"))


def _shaft(m):
    (spec,) = [s for s in m.entities if s.kind == "sun_shaft"]
    return spec


VAULTED = """[meta]
name = Vaulted
start = 1 1 0
edge_top = 10
vault = 10
vault_tex = ochre_flag

[legend]
# = wall tex=cavern_rock top=10
, = wall tex=sunken_brick top=2
. = floor h=0
g = floor h=0 ceil=3

[grid]
#######
#..,..#
#.....#
#g....#
#######
"""


def _vaulted():
    return MapLoader(VAULTED, name="vaulted").parse()


def test_a_map_without_a_vault_has_none():
    m = _vaulted()
    del m.meta["vault"]
    assert Vault.of(m) is None
    assert not MeshBuilder(m).build().batches["ochre_flag"].verts


def test_the_vault_hangs_lumpy_from_its_height_the_same_every_time():
    v = Vault(24.0, "cavern_rock")
    heights = [v.height_at(x, z) for x in range(0, 60) for z in range(0, 60)]
    assert heights == [Vault(24.0, "cavern_rock").height_at(x, z) for x in range(0, 60) for z in range(0, 60)]
    assert all(24.0 - MAX_DROP <= h <= 24.0 for h in heights)
    assert len({round(h, 2) for h in heights}) > 100  # lumpy, not flat
    assert any(h < 24.0 - vault.LUMP - vault.SPIKE_DROP[0] + 0.01 for h in heights)  # stalactites


def test_the_vault_spans_all_but_the_walls_reaching_it_and_the_ceiled_tiles():
    m = _vaulted()
    v = Vault.of(m)
    assert v.height == 10 and v.tex == "ochre_flag" and v.crack is None
    assert not v.covers(m[0, 0])  # the cavern wall already reaches it
    assert v.covers(m[3, 1])  # a low wall: no hole in the roof over it
    assert v.covers(m[2, 2])
    assert not v.covers(m[1, 3])  # a gallery under its own ceiling


def test_the_vault_is_drawn_facing_down_at_its_heights():
    m = _vaulted()
    b = MeshBuilder(m).build()
    v = Vault.of(m)
    verts = b.batches["ochre_flag"].verts
    assert len(verts) == 3 * 6 * 4 * 14  # four 1 m cells over each of the 14 tiles it spans (not the gallery)
    for i in range(0, len(verts), 3):
        x, y, z = verts[i : i + 3]
        assert 10 - MAX_DROP <= y <= 10 and y == pytest.approx(v.height_at(x, z))
    assert b.batches["ochre_flag"].lit[0][2] == -1.0  # facing down


def test_old_harrowmeres_vault_hangs_clear_of_everything_below_it():
    m = _harrowmere()
    v = Vault.of(m)
    assert v is not None and v.height == 24
    low = v.height - MAX_DROP
    for _tx, _tz, tile in m.each_tile():
        if v.covers(tile):
            top = tile.top if tile.solid else tile.floor
            assert top + 6 <= low
    for spec in m.entities:
        if spec.kind == "sunken_tower":
            assert m[spec.tx, spec.tz].floor + float(spec.props["height"]) + 6 <= low


def test_the_shaft_of_daylight_falls_from_a_crack_in_the_vault():
    m = _harrowmere()
    v = Vault.of(m)
    spec = _shaft(m)
    x, y, z = vault.shaft_top(m, spec)
    assert v.crack == pytest.approx((x, z))
    assert x < (spec.tx + 0.5) * 2  # it leans, its top off to the west of where it lands
    assert v.height - 0.5 <= y <= v.height + 1.0  # the shaft reaches up to the crack
    # A great rift running along x, across the plaza.
    assert v.in_crack(x, z) and v.in_crack(x + 12, z) and v.in_crack(x - 12, z)
    assert not v.in_crack(x, z + v.crack_width) and not v.in_crack(x + v.crack_len, z)
    lip = next(d / 4 for d in range(80) if not v.in_crack(x, z + d / 4))
    assert v.height_at(x, z + lip) == pytest.approx(v.height, abs=0.3)  # flat round its lip
    # Its light glows on the rock round the crack.
    lights = MeshBuilder.lights_for(m)
    assert any(math.hypot(l.x - x, l.z - z) < 0.1 and l.y > 20 for l in lights)
    b = MeshBuilder(m).build()
    verts = b.batches["cavern_rock"].verts
    cells = 0
    for i in range(0, len(verts), 18):  # each quad: six vertices, centred on its cell
        quad = verts[i : i + 18]
        cx, cy, cz = (sum(quad[k::3]) / 6 for k in range(3))
        flat = min(quad[0::3]) < max(quad[0::3]) and min(quad[2::3]) < max(quad[2::3])  # not a wall's face
        if cy > 10 and flat:  # a cell of the roof, never one in the crack
            cells += 1
            assert not v.in_crack(cx, cz)
    assert cells > 1000


def test_a_rift_runs_long_and_wide_whichever_way_it_is_turned():
    v = Vault(24.0, "cavern_rock", (50.0, 50.0), crack_len=30.0, crack_width=6.0, crack_yaw=math.pi / 2)
    # Turned a quarter, it runs along x: open 12 m out along x, closed 6 m out along z.
    assert v.in_crack(50.0, 50.0) and v.in_crack(62.0, 50.0) and v.in_crack(38.0, 50.0)
    assert not v.in_crack(50.0, 56.0) and not v.in_crack(70.0, 50.0)
    assert v.crack_light()[3] >= 30.0 * 0.75  # its daylight spreads along it


def test_old_harrowmeres_crack_is_a_great_rift():
    m = _harrowmere()
    v = Vault.of(m)
    assert v.crack_len >= 20 and v.crack_width >= 5
