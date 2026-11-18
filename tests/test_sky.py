import math
import os

import pytest

from ashen_vault import MAP_DIR
from ashen_vault.world import sky
from ashen_vault.world.darkness import VEIL_FOG
from ashen_vault.world.map_loader import MapLoader

FOG = (0.42, 0.46, 0.55)


def _meta(name):
    return MapLoader.load_file(os.path.join(MAP_DIR, f"{name}.map")).meta


def test_each_outdoor_map_names_a_sky_and_the_keep_has_none():
    maps = ("harrowmere", "verdant_hollow", "cinderhold", "vesperholm")
    names = {name: sky.get(_meta(name)) for name in maps}
    assert names == {
        "harrowmere": sky.SKIES["dusk"],
        "verdant_hollow": sky.SKIES["jungle"],
        "cinderhold": sky.SKIES["ember"],
        "vesperholm": sky.SKIES["moonlit"],
    }
    assert sky.get(_meta("sunken_keep")) is None
    assert sky.get({"sky": "no_such_sky"}) is None


def test_the_dome_meets_the_fog_at_the_horizon_and_the_zenith_overhead():
    zenith = (0.1, 0.2, 0.3)
    assert sky.dome_color(0.0, FOG, zenith) == list(FOG)
    assert sky.dome_color(-30.0, FOG, zenith) == list(FOG)
    assert sky.dome_color(90.0, FOG, zenith) == pytest.approx(zenith)
    low, high = sky.dome_color(10.0, FOG, zenith), sky.dome_color(60.0, FOG, zenith)
    assert abs(low[2] - FOG[2]) < abs(high[2] - FOG[2])  # it eases from fog to zenith on the way up


def test_darkness_dims_the_sky_and_the_veil_turns_it_pale():
    rgb = (0.8, 0.4, 0.2)
    assert sky.shade(rgb, 0.0) == pytest.approx(rgb)
    assert sky.shade(rgb, 1.0) == pytest.approx((0.0, 0.0, 0.0))
    veiled = sky.shade((0.0, 0.0, 0.0), 0.0, veil=True)
    assert all(0 < c < v for c, v in zip(veiled, VEIL_FOG, strict=True))


@pytest.mark.parametrize("name", sorted(sky.SKIES))
def test_every_sky_builds_whole_triangles_around_the_eye(name):
    spec = sky.SKIES[name]
    built = dict(sky.layers(spec, FOG))
    assert "dome" in built and "clouds" in built and "mist" in built
    assert set(built) <= set(sky.TEXTURES)
    for layer, mesh in built.items():
        n = mesh.vertex_count
        assert n and n % 3 == 0, layer
        assert len(mesh.uvs) == n * 2 and len(mesh.colors) == n * 3, layer
        assert all(0.0 <= c <= 1.0 for c in mesh.colors), layer
        for i in range(n):  # every vertex lies on (or just inside) the dome
            r = math.dist((0, 0, 0), mesh.verts[i * 3 : i * 3 + 3])
            assert sky.RADIUS * 0.8 < r <= sky.RADIUS + 1e-6, layer


def test_the_dome_rim_is_the_fog_colour_so_the_far_world_melts_into_it():
    mesh = sky.dome(sky.SKIES["overcast"], FOG)
    for i in range(mesh.vertex_count):
        y = mesh.verts[i * 3 + 1]
        if y <= 0 and abs(y) < sky.RADIUS * 0.5:  # at or below the horizon, away from the sun's halo
            assert mesh.colors[i * 3 : i * 3 + 3] == pytest.approx(FOG)


@pytest.mark.parametrize("name", sorted(sky.SKIES))
def test_the_sun_sits_where_its_sky_puts_it(name):
    spec = sky.SKIES[name]
    mesh = sky.sun(spec)
    d = sky.direction(*spec.sun_at)
    brightest = max(range(mesh.vertex_count), key=lambda i: sum(mesh.colors[i * 3 : i * 3 + 3]))
    p = mesh.verts[brightest * 3 : brightest * 3 + 3]
    r = math.dist((0, 0, 0), p)
    assert sum(a * b / r for a, b in zip(p, d, strict=True)) > math.cos(math.radians(spec.sun_size + 0.5))


def test_a_clear_sky_has_only_its_dome():
    clear = sky.Sky(zenith=(0.2, 0.3, 0.5))
    assert [name for name, _ in sky.layers(clear, FOG)] == ["dome"]


def test_dark_places_darken_every_layer():
    spec = sky.SKIES["ember"]
    lit = dict(sky.layers(spec, FOG))
    dark = dict(sky.layers(spec, [0.0, 0.0, 0.0], dark=1.0))
    for layer in lit:
        assert max(dark[layer].colors) == pytest.approx(0.0), layer
        assert max(lit[layer].colors) > 0.05, layer


def test_every_sky_puts_the_sun_low_in_the_south_over_the_towns_sea():
    assert {spec.sun_at for spec in sky.SKIES.values() if not spec.moon} == {sky.SUN_AT}
    azimuth, elevation = sky.SUN_AT
    d = sky.direction(azimuth, elevation)
    assert d[2] > 0.9 and 0 < elevation < 20  # south (+z), low over the horizon
    town = MapLoader.load_file(os.path.join(MAP_DIR, "harrowmere.map"))
    sea = [town[tx, town.depth - 2] for tx in range(town.width // 2)]  # its southern shore
    assert sum(t is not None and t.deep for t in sea) > len(sea) // 2  # the open sea lies south


def test_the_stars_are_the_same_every_time_and_fill_their_band():
    field = sky.star_field()
    assert field == sky.star_field() and len(field) == sky.STAR_COUNT
    lo, hi = sky.STAR_BAND
    for d, size, _, _ in field:
        assert lo - 1e-6 <= sky._elev(d) <= hi + 1e-6
        assert sky.STAR_SIZE[0] <= size <= sky.STAR_SIZE[1]


def test_the_town_has_stars_and_none_shine_in_the_suns_halo():
    spec = sky.SKIES["dusk"]
    mesh = sky.stars(spec, FOG)
    assert mesh.vertex_count >= sky.STAR_COUNT  # most of them, two triangles each
    sun_d = sky.direction(*spec.sun_at)
    for i in range(mesh.vertex_count):
        p = mesh.verts[i * 3 : i * 3 + 3]
        r = math.dist((0, 0, 0), p)
        assert sum(a * b / r for a, b in zip(p, sun_d, strict=True)) < math.cos(
            math.radians(spec.halo_size - 1)
        )


def test_the_stars_are_brighter_than_the_sky_behind_them():
    spec = sky.SKIES["dusk"]
    mesh = sky.stars(spec, FOG)
    zenith = sky.shade(spec.zenith, 0.0)
    for i in range(0, mesh.vertex_count, 6):
        p = mesh.verts[i * 3 : i * 3 + 3]
        behind = sky.dome_color(sky._elev([c / math.dist((0, 0, 0), p) for c in p]), FOG, zenith)
        assert sum(mesh.colors[i * 3 : i * 3 + 3]) > sum(behind)


def test_the_jungles_daylight_hides_the_stars():
    assert sky.stars(sky.SKIES["jungle"], FOG) is None
    assert "stars" not in dict(sky.layers(sky.SKIES["jungle"], FOG))


@pytest.mark.parametrize("name", ["dusk", "overcast", "ember"])
def test_the_stars_shine_behind_the_clouds(name):
    order = [layer for layer, _ in sky.layers(sky.SKIES[name], FOG)]
    assert order.index("dome") < order.index("stars") < order.index("cap") < order.index("clouds")


@pytest.mark.parametrize("name", sorted(sky.SKIES))
def test_the_sun_is_drawn_over_the_clouds_and_its_halo_behind_them(name):
    order = [layer for layer, _ in sky.layers(sky.SKIES[name], FOG)]
    assert order.index("sun") > order.index("clouds")
    assert order.index("sun") < order.index("mist")  # the horizon haze still softens it


def test_vesperholms_moon_hangs_vast_in_the_north_among_a_crowd_of_stars():
    """Vesperholm's sky is a night that never ends: in place of a sun a moon many times its size, high
    in the north over the cathedral, its seas laid on its face, and far more stars than the town's."""
    spec, dusk = sky.SKIES["moonlit"], sky.SKIES["dusk"]
    assert spec.moon and not dusk.moon
    assert spec.sun_size >= 3 * dusk.sun_size
    d = sky.direction(*spec.sun_at)
    assert d[2] < -0.9 and 15 < spec.sun_at[1] < 35  # north (-z), clear of the cathedral's roofs
    assert min(spec.sun) > 0.8 and spec.sun[2] >= spec.sun[0]  # pale, a little blue
    assert spec.star_count >= 2 * dusk.star_count and spec.stars > dusk.stars
    stars = sky.stars(spec, FOG)
    assert stars.vertex_count > 2 * sky.stars(dusk, FOG).vertex_count
    layers = [name for name, _ in sky.layers(spec, FOG)]
    assert layers.index("sun") < layers.index("maria") < layers.index("mist")
    seas = sky.maria(spec)
    lit = sky.sun_color(spec)
    for i in range(seas.vertex_count):  # every sea lies on the disc, darker than it
        p = seas.verts[i * 3 : i * 3 + 3]
        r = math.dist((0, 0, 0), p)
        assert sum(a * b / r for a, b in zip(p, d, strict=True)) > math.cos(math.radians(spec.sun_size))
        assert sum(seas.colors[i * 3 : i * 3 + 3]) < sum(lit)
    assert sky.maria(dusk) is None  # a sun has no seas


def test_a_sky_without_a_sun_has_no_disc():
    assert sky.sun(sky.Sky(zenith=(0.2, 0.3, 0.5))) is None
