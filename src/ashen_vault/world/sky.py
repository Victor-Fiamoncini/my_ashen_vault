"""Skies over open ground: a gradient dome that meets the fog at the horizon, banks of cloud drifting
around it, a sun glowing through them and a band of mist along the horizon. A map names its sky in
`[meta]` (`sky = overcast`); maps without one keep the plain fog colour.

Pure: this builds the geometry (vertices around the camera, uv, vertex colours) and the colours,
which darken with the darkness where you stand and turn pale under the Veil, as the fog does.
`render/sky.py` uploads it and draws it before the world."""

import math
from dataclasses import dataclass, field
from itertools import pairwise

from ashen_vault.world.darkness import VEIL_FOG, VEIL_MIX

RADIUS = 80.0  # metres from the eye to the dome; the sky pass draws without fog or depth
SEGMENTS = 16  # around the dome
# Elevations (degrees) of the dome's rings, from below the horizon (where only fog shows) up.
RINGS = (-40.0, -4.0, 0.0, 5.0, 12.0, 22.0, 36.0, 55.0, 75.0, 90.0)
CLOUD_BANDS = ((1.0, 19.0, 9, 0.0), (10.0, 34.0, 7, 0.5))  # (low, high elevation, uv repeats, u offset)
CAP_FROM = 40.0  # elevation where the overhead cloud cap starts
CAP_SCALE = 1 / 60.0  # uv per metre of the overhead cap
MIST_BAND = (-6.0, 8.0)
MIST_REPEATS = 10
# Where the sun stands over every map: low in the west, as Harrowmere first shows it. Every map shares
# the same axes (+x east, +z south), so one bearing keeps it in the same place wherever you travel.
SUN_AT = (180.0, 13.0)
SUN_THROUGH_CLOUD = 0.2  # how far the disc takes the cloud undersides' colour, as if seen through them


@dataclass(frozen=True)
class Sky:
    zenith: tuple  # colour straight up; the horizon is always the map's fog colour
    sun: tuple | None = None  # the sun's disc colour (None: no sun)
    sun_at: tuple = SUN_AT  # (azimuth, elevation) in degrees; azimuth 0 = +x (east), 90 = +z
    sun_size: float = 2.5  # the disc's radius, degrees
    halo: tuple | None = None  # the glow around the sun
    halo_size: float = 20.0
    clouds: tuple | None = None  # lit tops of the cloud banks (None: a clear sky)
    cloud_under: tuple = (0.3, 0.3, 0.3)  # their undersides
    drift: float = 0.004  # rad/s the cloud banks turn around you
    cap: bool = True  # a thinner layer of cloud overhead
    mist: tuple | None = None  # the haze along the horizon


SKIES = {
    # Harrowmere: a low grey ceiling with a pale, warm sun breaking through it.
    "overcast": Sky(
        zenith=(0.27, 0.33, 0.45),
        sun=(1.0, 0.94, 0.78),
        sun_at=SUN_AT,
        sun_size=2.6,
        halo=(0.92, 0.8, 0.6),
        halo_size=24.0,
        clouds=(0.74, 0.74, 0.76),
        cloud_under=(0.42, 0.44, 0.5),
        mist=(0.6, 0.62, 0.66),
    ),
    # The hollow: thick, humid green-gold haze over the canopy and a pale sun glaring through it.
    "jungle": Sky(
        zenith=(0.16, 0.26, 0.2),
        sun=(0.95, 0.92, 0.66),
        sun_at=SUN_AT,
        sun_size=3.0,
        halo=(0.55, 0.6, 0.36),
        halo_size=34.0,
        clouds=(0.26, 0.34, 0.24),
        cloud_under=(0.1, 0.17, 0.11),
        drift=0.002,
        cap=False,
        mist=(0.2, 0.3, 0.2),
    ),
    # The Cinderhold: smoke lit from beneath by the forges, and a blood-orange sun through it.
    "ember": Sky(
        zenith=(0.08, 0.03, 0.03),
        sun=(1.0, 0.5, 0.2),
        sun_at=SUN_AT,
        sun_size=3.4,
        halo=(0.62, 0.2, 0.08),
        halo_size=26.0,
        clouds=(0.2, 0.12, 0.11),
        cloud_under=(0.55, 0.2, 0.08),
        drift=0.006,
        mist=(0.36, 0.13, 0.07),
    ),
}


def get(meta):
    """The sky a map's `[meta]` names, or None."""
    return SKIES.get(str(meta.get("sky", "")).strip())


def shade(rgb, dark, veil=False):
    """A sky colour as the eye sees it where you stand: darkness dims it as it dims the fog, and the
    Veil turns it toward the same pale grey (see darkness.fog_for)."""
    out = [c * (1.0 - dark) for c in rgb]
    if veil:
        out = [c + (v - c) * VEIL_MIX for c, v in zip(out, VEIL_FOG, strict=True)]
    return out


def _mix(a, b, k):
    return [x + (y - x) * k for x, y in zip(a, b, strict=True)]


def dome_color(elev, fog, zenith):
    """Colour of the dome at `elev` degrees: the fog at and below the horizon, easing into the zenith."""
    if elev <= 0:
        return list(fog)
    k = min(elev / 90.0, 1.0) ** 0.6
    return _mix(fog, zenith, k)


def direction(azimuth, elev):
    a, e = math.radians(azimuth), math.radians(elev)
    return (math.cos(a) * math.cos(e), math.sin(e), math.sin(a) * math.cos(e))


def _elev(d):
    return math.degrees(math.asin(max(-1.0, min(1.0, d[1]))))


@dataclass
class SkyMesh:
    """Triangles around the eye (vertices relative to it), with uvs and 0..1 vertex colours."""

    verts: list = field(default_factory=list)
    uvs: list = field(default_factory=list)
    colors: list = field(default_factory=list)

    @property
    def vertex_count(self):
        return len(self.verts) // 3

    def vertex(self, d, uv, rgb, r=RADIUS):
        self.verts.extend((d[0] * r, d[1] * r, d[2] * r))
        self.uvs.extend(uv)
        self.colors.extend(min(max(c, 0.0), 1.0) for c in rgb)

    def quad(self, a, b, c, d):
        """Two triangles from four (direction, uv, rgb, radius) corners, in strip order a-b / c-d."""
        for v in (a, b, c, b, d, c):
            self.vertex(*v)


def dome(spec, fog, dark=0.0, veil=False):
    """The gradient dome, then the sun's halo over it (drawn in that order, no depth). The disc is a
    layer of its own (`sun`), drawn over the clouds."""
    mesh = SkyMesh()
    zenith = shade(spec.zenith, dark, veil)
    for lo, hi in pairwise(RINGS):
        c_lo, c_hi = dome_color(lo, fog, zenith), dome_color(hi, fog, zenith)
        for i in range(SEGMENTS):
            a0, a1 = 360.0 * i / SEGMENTS, 360.0 * (i + 1) / SEGMENTS
            mesh.quad(
                (direction(a0, lo), (0, 0), c_lo, RADIUS),
                (direction(a1, lo), (0, 0), c_lo, RADIUS),
                (direction(a0, hi), (0, 0), c_hi, RADIUS),
                (direction(a1, hi), (0, 0), c_hi, RADIUS),
            )
    if spec.sun:
        _halo(mesh, spec, fog, zenith, dark, veil)
    return mesh


def _basis(d):
    """Two unit vectors at right angles to `d` and to each other."""
    up = (0.0, 1.0, 0.0) if abs(d[1]) < 0.95 else (1.0, 0.0, 0.0)
    u = (up[1] * d[2] - up[2] * d[1], up[2] * d[0] - up[0] * d[2], up[0] * d[1] - up[1] * d[0])
    n = math.sqrt(sum(c * c for c in u))
    u = tuple(c / n for c in u)
    v = (d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0])
    return u, v


def _around(d, u, v, radius_deg, angle):
    r = math.radians(radius_deg)
    p = tuple(
        d[k] * math.cos(r) + (u[k] * math.cos(angle) + v[k] * math.sin(angle)) * math.sin(r) for k in range(3)
    )
    n = math.sqrt(sum(c * c for c in p))
    return tuple(c / n for c in p)


def _halo(mesh, spec, fog, zenith, dark, veil):
    """A soft halo whose rim takes the dome's own colour, so it fades into the sky. It stays behind
    the clouds: the sky has no alpha, so drawn over them its rim would cut a hole through them."""
    d = direction(*spec.sun_at)
    u, v = _basis(d)
    halo = shade(spec.halo or spec.sun, dark, veil)
    steps = 20
    rings = ((0.0, 1.0), (0.35, 0.55), (1.0, 0.0))  # (share of the halo's radius, how much halo shows)
    for (r0, k0), (r1, k1) in pairwise(rings):
        for i in range(steps):
            a0, a1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
            corners = []
            for r, k, a in ((r0, k0, a0), (r0, k0, a1), (r1, k1, a0), (r1, k1, a1)):
                p = _around(d, u, v, spec.halo_size * r, a)
                corners.append((p, (0, 0), _mix(dome_color(_elev(p), fog, zenith), halo, k), RADIUS * 0.99))
            mesh.quad(*corners)


def sun(spec, dark=0.0, veil=False):
    """The sun's disc, drawn over the cloud banks so no sky hides it; under clouds it takes a little
    of their undersides' colour, as if it shone through them. None for a sky without a sun."""
    if not spec.sun:
        return None
    mesh = SkyMesh()
    rgb = spec.sun
    if spec.clouds:
        rgb = _mix(rgb, spec.cloud_under, SUN_THROUGH_CLOUD)
    rgb = shade(rgb, dark, veil)
    d = direction(*spec.sun_at)
    u, v = _basis(d)
    steps = 20
    for i in range(steps):
        a0, a1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
        for p in (d, _around(d, u, v, spec.sun_size, a0), _around(d, u, v, spec.sun_size, a1)):
            mesh.vertex(p, (0, 0), rgb, RADIUS * 0.84)
    return mesh


def clouds(spec, dark=0.0, veil=False):
    """Banks of cloud in rings around the horizon (the `clouds` texture cuts their shapes and thins
    them toward their edges). Tops are lit, undersides take `cloud_under`. None for a clear sky."""
    if not spec.clouds:
        return None
    mesh = SkyMesh()
    top, under = shade(spec.clouds, dark, veil), shade(spec.cloud_under, dark, veil)
    for n, (lo, hi, repeats, offset) in enumerate(CLOUD_BANDS):
        r = RADIUS * (0.95 - n * 0.03)
        for i in range(SEGMENTS):
            a0, a1 = 360.0 * i / SEGMENTS, 360.0 * (i + 1) / SEGMENTS
            u0, u1 = offset + repeats * i / SEGMENTS, offset + repeats * (i + 1) / SEGMENTS
            mesh.quad(
                (direction(a0, lo), (u0, 1.0), under, r),
                (direction(a1, lo), (u1, 1.0), under, r),
                (direction(a0, hi), (u0, 0.0), top, r),
                (direction(a1, hi), (u1, 0.0), top, r),
            )
    return mesh


def cap(spec, dark=0.0, veil=False):
    """The thin overhead layer (`cloud_cap` texture): rings of quads from CAP_FROM to the zenith with
    their uv laid flat, so the cloud doesn't pinch together overhead. None without one."""
    if not (spec.clouds and spec.cap):
        return None
    mesh = SkyMesh()
    top, under = shade(spec.clouds, dark, veil), shade(spec.cloud_under, dark, veil)
    r = RADIUS * 0.9
    rings = (CAP_FROM, 60.0, 78.0, 90.0)
    for lo, hi in pairwise(rings):
        c_lo, c_hi = _mix(under, top, 0.5), top
        for i in range(SEGMENTS):
            a0, a1 = 360.0 * i / SEGMENTS, 360.0 * (i + 1) / SEGMENTS
            corners = []
            for a, e, c in ((a0, lo, c_lo), (a1, lo, c_lo), (a0, hi, c_hi), (a1, hi, c_hi)):
                p = direction(a, e)
                corners.append((p, (p[0] * r * CAP_SCALE, p[2] * r * CAP_SCALE), c, r))
            mesh.quad(*corners)
    return mesh


def mist(spec, dark=0.0, veil=False):
    """A band of haze along the horizon (the `mist` texture stipples it). None without mist."""
    if not spec.mist:
        return None
    mesh = SkyMesh()
    rgb = shade(spec.mist, dark, veil)
    lo, hi = MIST_BAND
    r = RADIUS * 0.85
    for i in range(SEGMENTS):
        a0, a1 = 360.0 * i / SEGMENTS, 360.0 * (i + 1) / SEGMENTS
        u0, u1 = MIST_REPEATS * i / SEGMENTS, MIST_REPEATS * (i + 1) / SEGMENTS
        mesh.quad(
            (direction(a0, lo), (u0, 1.0), rgb, r),
            (direction(a1, lo), (u1, 1.0), rgb, r),
            (direction(a0, hi), (u0, 0.0), rgb, r),
            (direction(a1, hi), (u1, 0.0), rgb, r),
        )
    return mesh


TEXTURES = {"dome": "white", "cap": "cloud_cap", "clouds": "clouds", "sun": "white", "mist": "mist"}
DRIFTING = ("cap", "clouds")  # layers that turn slowly around you


def layers(spec, fog, dark=0.0, veil=False):
    """[(layer, mesh)] for a sky, back to front: the dome (with the sun's halo), the overhead cap, the
    cloud banks, the sun's disc and the mist. Layers the sky lacks are left out."""
    built = (
        ("dome", dome(spec, fog, dark, veil)),
        ("cap", cap(spec, dark, veil)),
        ("clouds", clouds(spec, dark, veil)),
        ("sun", sun(spec, dark, veil)),
        ("mist", mist(spec, dark, veil)),
    )
    return [(name, mesh) for name, mesh in built if mesh is not None]
