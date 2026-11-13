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
    names = {name: sky.get(_meta(name)) for name in ("harrowmere", "verdant_hollow", "cinderhold")}
    assert names == {
        "harrowmere": sky.SKIES["overcast"],
        "verdant_hollow": sky.SKIES["jungle"],
        "cinderhold": sky.SKIES["ember"],
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


def test_the_sun_sits_where_its_sky_puts_it():
    spec = sky.SKIES["overcast"]
    mesh = sky.dome(spec, FOG)
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
