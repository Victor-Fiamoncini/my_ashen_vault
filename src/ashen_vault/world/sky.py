"""Skies over open ground: a gradient dome that meets the fog at the horizon, stars, banks of cloud
drifting around it, a sun glowing through them and a band of mist along the horizon. A map names its sky in
`[meta]` (`sky = overcast`); maps without one keep the plain fog colour.

Pure: this builds the geometry (vertices around the camera, uv, vertex colours) and the colours,
which darken with the darkness where you stand and turn pale under the Veil, as the fog does.
`render/sky.py` uploads it and draws it before the world."""

import math
import random
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
# The sea of cloud's rings (elevations below the horizon, from straight down up to it), its uv per
# metre, and how far its edge at the horizon fades into the mist there.
CLOUD_SEA_RINGS = (-90.0, -55.0, -30.0, -16.0, -8.0, -3.0, 0.0)
CLOUD_SEA_SCALE = 1 / 34.0
MIST_BAND = (-6.0, 8.0)
MIST_REPEATS = 10
# Where the sun stands over every map: low in the south, over Harrowmere's sea. Every map shares the
# same axes (+x east, +z south), so one bearing keeps it in the same place wherever you travel.
SUN_AT = (90.0, 13.0)
SUN_THROUGH_CLOUD = 0.1  # how far the disc takes the cloud undersides' colour, as if seen through them
SUN_GLARE = 0.4  # how far the disc's colour runs toward white, so it glares against the sky
STAR_COUNT = 220
STAR_BAND = (16.0, 88.0)  # elevations the stars fill, above the horizon's mist and the low cloud bank
STAR_SIZE = (0.22, 0.45)  # a star's radius, degrees: one to three pixels at 320x240
STAR_SEED = 1709  # the same sky of stars over every map, every time
STAR_TINTS = ((0.92, 0.95, 1.0), (1.0, 0.94, 0.82), (0.78, 0.86, 1.0))  # cool white, warm white, pale blue
# Where Vesperholm's moon hangs: in the north, over the Duchess's cathedral, high enough to stand clear
# of its roofs (and the flèche on its ridge) from Lantern Square and the gate court. It never sets.
MOON_AT = (270.0, 30.0)
# Vesperholm's moon is full: its whole disc lit, a touch dimmer toward its limb (LIMB_SHADE), so it
# reads as a sphere, its seas scattered across it.
LIMB_SHADE = 0.93
# The moon's seas: (across, up, size, wobble), as shares of its radius, each a darker patch with a
# ragged rim (`wobble` shares of its size), all well inside the disc.
MARIA = (
    (-0.34, 0.36, 0.25, 0.22),
    (0.08, 0.5, 0.17, 0.18),
    (0.36, 0.14, 0.22, 0.2),
    (-0.5, -0.06, 0.19, 0.25),
    (-0.1, -0.06, 0.14, 0.2),
    (0.22, -0.4, 0.18, 0.22),
    (-0.3, -0.56, 0.12, 0.2),
    (0.58, -0.18, 0.1, 0.15),
)
MARIA_SHADE = 0.8  # how dark the seas are against the disc (a sky can set its own, `maria_shade`)
MARIA_STEPS = 14
# Wisps of cloud trailing across the moon: (height across the disc, bow, thickness, length), as shares
# of its radius, the rise measured up the disc.
WISPS = (
    (0.35, -0.1, 0.22, 3.4),
    (-0.25, 0.08, 0.16, 2.8),
    (-0.7, -0.06, 0.26, 3.8),
    (0.95, 0.05, 0.12, 2.6),
    (-1.15, -0.04, 0.18, 3.2),
)
WISP_SLOPE = -0.18  # they lean a little, rising to the left
WISP_LIGHT = 0.35  # how far the moon lights them
WISP_SCALE = 1 / 30.0  # uv per degree along them
# A moon's corona: a bright glow hugging the disc, CORONA_SCALE times its radius, inside the wide halo.
CORONA_SCALE = 2.4
# A band of the galaxy across the night: a crowd of faint stars strewn about a great circle tipped
# across the sky, thickest along it. Its pole, as (azimuth, elevation) degrees.
GALAXY_POLE = (200.0, 38.0)
GALAXY_COUNT = 700
GALAXY_SPREAD = 7.0  # degrees: how far, typically, its stars stray from the circle
GALAXY_SIZE = (0.16, 0.3)  # smaller than the field's stars
GALAXY_SEED = 3301
# The sun Vesperholm denies: still low in the south (SUN_AT), but buried in a bank of cloud so only a
# cold glow leaks round its edges. (centre across, up, size) of each billow, in VEILED_SIZE degrees.
VEILED_SIZE = 3.6
VEILED_GLOW = 26.0  # the faint glow around the bank, degrees
SHROUD = (
    (-2.4, 0.3, 1.4),
    (2.5, 0.2, 1.5),
    (-1.1, 1.3, 1.5),
    (1.3, 1.2, 1.6),
    (0.1, 1.9, 1.3),
    (0.0, 0.4, 2.0),
)
SHROUD_STEPS = 14
SHROUD_RIM = 0.7  # how far each billow's rim takes the hidden sun's light


@dataclass(frozen=True)
class FarMoon:
    """Another land's moon seen from afar: a small full moon (its seas on it) in a faint halo, low
    enough that the drifting cloud banks pass over it, with wisps of the sky's own cloud across it."""

    at: tuple = MOON_AT  # (azimuth, elevation) in degrees
    size: float = 5.0  # the disc's radius, degrees
    color: tuple = (0.8, 0.84, 0.92)
    halo: tuple = (0.24, 0.26, 0.36)
    halo_size: float = 13.0
    maria_shade: float = 0.84
    wisps: float = 0.85  # how much of the sky's cloud colour its wisps take (the rest the moon's light)


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
    stars: float = 0.0  # how brightly the stars show through it (0: none)
    star_count: int = STAR_COUNT  # how many: a clear night shows far more than a dusk
    star_clear: float | None = None  # degrees kept clear of stars around the disc (None: its whole halo)
    galaxy: bool = False  # a band of the galaxy strewn across the stars
    moon: bool = False  # the disc is a full moon: its seas on it (`maria`), wisps across it
    maria_shade: float = MARIA_SHADE  # how dark a moon's seas are against its disc
    corona: tuple | None = None  # a moon's bright glow hugging its disc
    veiled: tuple | None = None  # a sun hidden in a bank of cloud in the south: the light leaking round it
    far_moon: FarMoon | None = None  # another land's moon, far off, behind the cloud banks
    # A sea of cloud below the horizon, seen from above it (Herran's Castle): the lit tops' colour, and
    # its shadowed hollows'. None for a sky seen from the ground.
    cloud_sea: tuple | None = None
    cloud_sea_under: tuple = (0.5, 0.52, 0.62)


SKIES = {
    # The cemetery: a low, gloomy grey ceiling with a dim, wan sun in the south and Vesperholm's
    # full moon in the north, both half-hidden by the cloud ceiling.
    "overcast": Sky(
        zenith=(0.17, 0.2, 0.27),
        sun=(0.95, 0.9, 0.76),
        sun_at=SUN_AT,
        sun_size=2.6,
        halo=(0.7, 0.62, 0.49),
        halo_size=24.0,
        clouds=(0.48, 0.48, 0.5),
        cloud_under=(0.27, 0.28, 0.32),
        mist=(0.39, 0.4, 0.43),
        stars=0.32,
        far_moon=FarMoon(
            at=MOON_AT,
            size=7.0,
            color=(0.8, 0.84, 0.92),
            halo=(0.24, 0.26, 0.36),
            halo_size=18.0,
            maria_shade=0.85,
            wisps=0.85,
        ),
    ),
    # Harrowmere: dusk under a bruised ceiling of cloud, a dull copper sun sinking in the south,
    # and in the north, over the Vesper Gate, Vesperholm's full moon.
    "dusk": Sky(
        zenith=(0.07, 0.07, 0.12),
        sun=(0.92, 0.6, 0.38),
        sun_at=SUN_AT,
        sun_size=2.4,
        halo=(0.43, 0.29, 0.23),
        halo_size=18.0,
        clouds=(0.24, 0.22, 0.27),
        cloud_under=(0.12, 0.12, 0.17),
        mist=(0.18, 0.18, 0.23),
        stars=0.5,
        far_moon=FarMoon(
            at=MOON_AT,
            size=7.0,
            color=(0.8, 0.84, 0.92),
            halo=(0.24, 0.26, 0.36),
            halo_size=18.0,
            maria_shade=0.82,
            wisps=0.85,
        ),
    ),
    # The hollow: thick, humid green-gold haze over the canopy, a pale sun glaring in the south,
    # and a full moon in the north.
    "jungle": Sky(
        zenith=(0.16, 0.26, 0.2),
        sun=(1.0, 0.98, 0.76),
        sun_at=SUN_AT,
        sun_size=3.0,
        halo=(0.64, 0.7, 0.42),
        halo_size=34.0,
        clouds=(0.26, 0.34, 0.24),
        cloud_under=(0.1, 0.17, 0.11),
        drift=0.002,
        cap=False,
        mist=(0.2, 0.3, 0.2),
        stars=0.2,
        far_moon=FarMoon(
            at=MOON_AT,
            size=6.0,
            color=(0.85, 0.88, 0.95),
            halo=(0.3, 0.32, 0.4),
            halo_size=16.0,
            maria_shade=0.75,
            wisps=0.7,
        ),
    ),
    # The Cinderhold: smoke lit from beneath by the forges, a blood-orange sun in the south,
    # and a full moon in the north, both struggling through the smoke.
    "ember": Sky(
        zenith=(0.08, 0.03, 0.03),
        sun=(1.0, 0.6, 0.26),
        sun_at=SUN_AT,
        sun_size=3.4,
        halo=(0.72, 0.24, 0.1),
        halo_size=26.0,
        clouds=(0.2, 0.12, 0.11),
        cloud_under=(0.55, 0.2, 0.08),
        drift=0.006,
        mist=(0.36, 0.13, 0.07),
        stars=0.24,
        far_moon=FarMoon(
            at=MOON_AT,
            size=5.5,
            color=(0.7, 0.7, 0.8),
            halo=(0.2, 0.2, 0.3),
            halo_size=15.0,
            maria_shade=0.7,
            wisps=0.6,
        ),
    ),
    # Vesperholm: a night that never ends, a full moon blazing in the north over the cathedral,
    # wisps of cloud trailing across it, a thin moonlit layer drifting overhead, stars crowded up
    # to the moon's glow and the galaxy strewn across them, and in the south the sun the city
    # denies, buried in a bank of cloud.
    "moonlit": Sky(
        zenith=(0.03, 0.05, 0.14),
        sun=(1.0, 1.0, 1.0),
        sun_at=MOON_AT,
        sun_size=8.5,
        halo=(0.48, 0.6, 0.84),
        halo_size=48.0,
        clouds=(0.36, 0.42, 0.58),
        cloud_under=(0.12, 0.15, 0.25),
        drift=0.0015,
        mist=(0.4, 0.46, 0.6),
        stars=1.0,
        star_count=960,
        star_clear=14.0,
        galaxy=True,
        moon=True,
        maria_shade=0.88,
        corona=(0.86, 0.92, 1.0),
        veiled=(0.62, 0.6, 0.55),
    ),
    # Herran's Castle: high over a sea of cloud in the clear thin air, a deep blue overhead fading
    # to gold toward the low sun in the south, bright banks of cloud drifting level with the towers,
    # and in the north, Vesperholm's full moon, near and huge.
    "aloft": Sky(
        zenith=(0.1, 0.2, 0.44),
        sun=(1.0, 0.9, 0.64),
        sun_at=SUN_AT,
        sun_size=3.2,
        halo=(0.86, 0.64, 0.4),
        halo_size=30.0,
        clouds=(0.92, 0.86, 0.8),
        cloud_under=(0.56, 0.58, 0.7),
        drift=0.003,
        cap=False,
        mist=(0.8, 0.76, 0.74),
        stars=0.12,
        cloud_sea=(0.96, 0.9, 0.82),
        cloud_sea_under=(0.56, 0.58, 0.7),
        far_moon=FarMoon(
            at=MOON_AT,
            size=9.0,
            color=(0.88, 0.9, 0.96),
            halo=(0.34, 0.38, 0.5),
            halo_size=20.0,
            wisps=0.6,
        ),
    ),
    # Herran's Castle in the storm: a near-black slate night over a sea of dark cloud, the sun a
    # dim glow buried in a heavy bank in the south, and a full moon in the north, half-lost in
    # the storm clouds.
    "storm": Sky(
        zenith=(0.04, 0.04, 0.07),
        sun=(0.5, 0.5, 0.55),
        sun_at=SUN_AT,
        sun_size=2.4,
        halo=(0.2, 0.2, 0.25),
        halo_size=24.0,
        clouds=(0.26, 0.26, 0.31),
        cloud_under=(0.1, 0.1, 0.14),
        drift=0.01,
        cap=True,
        mist=(0.2, 0.2, 0.25),
        veiled=(0.3, 0.3, 0.34),
        cloud_sea=(0.3, 0.3, 0.36),
        cloud_sea_under=(0.12, 0.12, 0.17),
        stars=0.15,
        far_moon=FarMoon(
            at=MOON_AT,
            size=5.0,
            color=(0.6, 0.6, 0.7),
            halo=(0.15, 0.15, 0.25),
            halo_size=14.0,
            maria_shade=0.6,
            wisps=0.5,
        ),
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
    if spec.sun and spec.corona:  # fading into the halo it lies on, not the bare sky
        halo = (shade(spec.halo or spec.sun, dark, veil), spec.halo_size)
        corona = shade(spec.corona, dark, veil)
        _glow(mesh, spec.sun_at, corona, spec.sun_size * CORONA_SCALE, fog, zenith, under=halo)
    if spec.veiled:
        _glow(mesh, SUN_AT, shade(spec.veiled, dark, veil), VEILED_GLOW, fog, zenith)
    if spec.far_moon:
        far = spec.far_moon
        _glow(mesh, far.at, shade(far.halo, dark, veil), far.halo_size, fog, zenith)
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
    _glow(mesh, spec.sun_at, shade(spec.halo or spec.sun, dark, veil), spec.halo_size, fog, zenith)


GLOW_RINGS = ((0.0, 1.0), (0.35, 0.55), (1.0, 0.0))  # (share of a glow's radius, how much glow shows)


def glow_share(share):
    """How much of a glow shows `share` of the way out to its rim (as `_glow` shades it)."""
    for (r0, k0), (r1, k1) in pairwise(GLOW_RINGS):
        if share <= r1:
            return k0 + (k1 - k0) * (max(share, r0) - r0) / (r1 - r0)
    return 0.0


def _glow(mesh, at, rgb, size, fog, zenith, under=None):
    """A glow of `rgb` `size` degrees round the direction `at`, fading into the dome at its rim (or
    into the glow `under` it, an (rgb, size) round the same direction)."""
    d = direction(*at)
    u, v = _basis(d)
    steps = 20
    for (r0, k0), (r1, k1) in pairwise(GLOW_RINGS):
        for i in range(steps):
            a0, a1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
            corners = []
            for r, k, a in ((r0, k0, a0), (r0, k0, a1), (r1, k1, a0), (r1, k1, a1)):
                p = _around(d, u, v, size * r, a)
                behind = dome_color(_elev(p), fog, zenith)
                if under:
                    behind = _mix(behind, under[0], glow_share(size * r / under[1]))
                corners.append((p, (0, 0), _mix(behind, rgb, k), RADIUS * 0.99))
            mesh.quad(*corners)


def _at(d, u, v, x, y):
    """The direction `x` degrees along `u` and `y` along `v` from `d` (a flat map of a small patch)."""
    return _around(d, u, v, math.hypot(x, y), math.atan2(y, x))


def sun_color(spec, dark=0.0, veil=False):
    """The sun's disc colour as the eye sees it (also the glints it lays on the sea): glaring toward
    white, a little of the clouds' undersides if it shines through them. A moon outshines its wisps."""
    rgb = _mix(spec.sun, (1.0, 1.0, 1.0), SUN_GLARE)
    if spec.clouds and not spec.moon:
        rgb = _mix(rgb, spec.cloud_under, SUN_THROUGH_CLOUD)
    return shade(rgb, dark, veil)


def sun(spec, dark=0.0, veil=False):
    """The sun's disc, drawn over the cloud banks so no sky hides it; under clouds it takes a little
    of their undersides' colour, as if it shone through them. A full moon is lit all over, a touch
    dimmer at its limb. None for a sky without a sun."""
    if not spec.sun:
        return None
    mesh = SkyMesh()
    rgb = sun_color(spec, dark, veil)
    rim = [c * LIMB_SHADE for c in rgb] if spec.moon else rgb
    _disc(mesh, spec.sun_at, spec.sun_size, rgb, rim, RADIUS * 0.84)
    return mesh


def _disc(mesh, at, size, rgb, rim, r):
    """A disc `size` degrees round the direction `at`: `rgb` at its heart, `rim` at its edge."""
    d = direction(*at)
    u, v = _basis(d)
    steps = 20
    for i in range(steps):
        a0, a1 = 2 * math.pi * i / steps, 2 * math.pi * (i + 1) / steps
        mesh.vertex(d, (0, 0), rgb, r)
        for a in (a0, a1):
            mesh.vertex(_around(d, u, v, size, a), (0, 0), rim, r)


def sea_reach(sea):
    """How far from its centre a sea's ragged rim reaches at most, in shares of the moon's radius."""
    _x, _y, size, wobble = sea
    return size * (1 + wobble)


def maria(spec, dark=0.0, veil=False):
    """The seas on a full moon: darker patches with ragged rims scattered over its face, laid just in
    front of it. None for a sun, or a sky without a disc."""
    if not (spec.sun and spec.moon):
        return None
    mesh = SkyMesh()
    rgb = [c * spec.maria_shade for c in sun_color(spec, dark, veil)]
    _seas(mesh, spec.sun_at, spec.sun_size, rgb, RADIUS * 0.835)
    return mesh


def _seas(mesh, at, moon_size, rgb, r):
    """The MARIA on a moon `moon_size` degrees across round `at`, in `rgb`."""
    d = direction(*at)
    u, v = _basis(d)
    for n, (x, y, size, wobble) in enumerate(MARIA):
        centre = _at(d, u, v, x * moon_size, y * moon_size)
        cu, cv = _basis(centre)
        rim = []
        for i in range(MARIA_STEPS + 1):
            a = 2 * math.pi * i / MARIA_STEPS
            ragged = 1 + wobble * math.sin(3 * a + n * 1.7) * math.cos(2 * a - n)
            rim.append(_around(centre, cu, cv, moon_size * size * ragged, a))
        for p0, p1 in pairwise(rim):
            for p in (centre, p0, p1):
                mesh.vertex(p, (0, 0), rgb, r)


def wisps(spec, dark=0.0, veil=False):
    """Thin streamers of cloud trailing across a moon, lit by it from above and dark beneath (the
    `cloud_cap` texture frays them). They hang still in front of it. None but for a moon."""
    if not (spec.sun and spec.moon and spec.clouds):
        return None
    mesh = SkyMesh()
    lit = _mix(shade(spec.clouds, dark, veil), sun_color(spec, dark, veil), WISP_LIGHT)
    under = _mix(shade(spec.cloud_under, dark, veil), lit, 0.4)
    _streamers(mesh, spec.sun_at, spec.sun_size, lit, under, RADIUS * 0.83)
    return mesh


def _streamers(mesh, at, size, lit, under, r):
    """The WISPS across a moon `size` degrees across round `at`: `lit` above, `under` beneath."""
    d = direction(*at)
    u, v = _basis(d)
    steps = 12
    for n, (height, bow, thick, length) in enumerate(WISPS):
        row = []
        for i in range(steps + 1):
            k = i / steps * 2 - 1  # -1..1 along the wisp
            x = k * length / 2 * size
            y = (height + bow * (1 - k * k) + WISP_SLOPE * k * length / 2) * size
            half = thick * size / 2 * (1 - 0.6 * k * k)  # thinning toward the ends
            uu = n * 0.37 + x * WISP_SCALE
            row.append(
                (
                    (_at(d, u, v, -x, y - half), (uu, 1.0), under, r),
                    (_at(d, u, v, -x, y + half), (uu, 0.0), lit, r),
                )
            )
        for (a, b), (c, e) in pairwise(row):
            mesh.quad(a, c, b, e)


def far_moon_color(spec, dark=0.0, veil=False):
    """A far moon's disc colour as the eye sees it, a little dulled by the cloud it lies behind."""
    far = spec.far_moon
    rgb = _mix(far.color, spec.cloud_under, SUN_THROUGH_CLOUD) if spec.clouds else far.color
    return shade(rgb, dark, veil)


def far_moon(spec, dark=0.0, veil=False):
    """Another land's full moon seen from afar: its disc, a touch dimmer at its limb, and its seas,
    behind the cloud banks so they drift across it. None for a sky without one."""
    far = spec.far_moon
    if not far:
        return None
    mesh = SkyMesh()
    rgb = far_moon_color(spec, dark, veil)
    _disc(mesh, far.at, far.size, rgb, [c * LIMB_SHADE for c in rgb], RADIUS * 0.97)
    _seas(mesh, far.at, far.size, [c * far.maria_shade for c in rgb], RADIUS * 0.965)
    return mesh


def far_wisps(spec, dark=0.0, veil=False):
    """Wisps of the sky's own cloud hanging still across a far moon, barely lit by it, so it shows
    half veiled even where the drifting banks leave it clear. None without a far moon under cloud."""
    far = spec.far_moon
    if not (far and spec.clouds):
        return None
    mesh = SkyMesh()
    moon = far_moon_color(spec, dark, veil)
    lit = _mix(moon, shade(spec.clouds, dark, veil), far.wisps)
    under = _mix(moon, shade(spec.cloud_under, dark, veil), far.wisps)
    _streamers(mesh, far.at, far.size, lit, under, RADIUS * 0.96)
    return mesh


def shroud(spec, dark=0.0, veil=False):
    """The bank of cloud the veiled sun hides in, low in the south: billows dark at their hearts and
    silvered at their rims by the light behind them. None for a sky whose sun shows."""
    if not spec.veiled:
        return None
    mesh = SkyMesh()
    heart = shade(spec.cloud_under, dark, veil)
    rim = _mix(heart, shade(spec.veiled, dark, veil), SHROUD_RIM)
    d = direction(*SUN_AT)
    u, v = _basis(d)
    for x, y, size in SHROUD:
        centre = _at(d, u, v, x * VEILED_SIZE, y * VEILED_SIZE)
        cu, cv = _basis(centre)
        for i in range(SHROUD_STEPS):
            a0, a1 = 2 * math.pi * i / SHROUD_STEPS, 2 * math.pi * (i + 1) / SHROUD_STEPS
            mesh.vertex(centre, (0, 0), heart, RADIUS * 0.86)
            for a in (a0, a1):
                p = _around(centre, cu, cv, size * VEILED_SIZE, a)
                mesh.vertex(p, (0, 0), rim, RADIUS * 0.86)
    return mesh


def star_field(count=STAR_COUNT):
    """[(direction, radius in degrees, tint, brightness)] for every star, the same each time: spread
    evenly over the band's share of the sphere (uniform in the sine of the elevation). A denser sky
    keeps the same first stars and adds more."""
    rng = random.Random(STAR_SEED)
    lo, hi = (math.sin(math.radians(e)) for e in STAR_BAND)
    out = []
    for _ in range(count):
        elev = math.degrees(math.asin(rng.uniform(lo, hi)))
        d = direction(rng.uniform(0.0, 360.0), elev)
        out.append((d, rng.uniform(*STAR_SIZE), rng.choice(STAR_TINTS), rng.uniform(0.45, 1.0)))
    return out


def galaxy_field(count=GALAXY_COUNT):
    """[(direction, radius, tint, brightness)] for the galaxy's faint stars, the same each time: strewn
    about the great circle round GALAXY_POLE, thickest along it, kept to the stars' band."""
    rng = random.Random(GALAXY_SEED)
    pole = direction(*GALAXY_POLE)
    e1, e2 = _basis(pole)
    lo, hi = STAR_BAND
    out = []
    while len(out) < count:
        along = rng.uniform(0.0, 2 * math.pi)
        off = math.radians(rng.gauss(0.0, GALAXY_SPREAD))
        d = tuple(
            math.cos(off) * (math.cos(along) * e1[k] + math.sin(along) * e2[k]) + math.sin(off) * pole[k]
            for k in range(3)
        )
        if lo <= _elev(d) <= hi:
            out.append((d, rng.uniform(*GALAXY_SIZE), rng.choice(STAR_TINTS), rng.uniform(0.3, 0.7)))
    return out


def star_clear(spec):
    """Degrees kept clear of stars around the sun or moon: its whole halo unless the sky says less."""
    return spec.halo_size if spec.star_clear is None else spec.star_clear


def stars(spec, fog, dark=0.0, veil=False):
    """Small diamonds of light over the dome, behind the clouds so the banks hide some and they glint
    in the gaps, and the galaxy's band if the sky has one. None where the light hides them
    (`spec.stars` 0); none within `star_clear` of the sun, nor in a far moon's halo."""
    if not spec.stars:
        return None
    mesh = SkyMesh()
    zenith = shade(spec.zenith, dark, veil)
    away = math.cos(math.radians(star_clear(spec))) if spec.sun else 2.0
    sun_d = direction(*spec.sun_at)
    field = star_field(spec.star_count) + (galaxy_field() if spec.galaxy else [])
    glows = []  # the halo and corona round the sun: a star there shines over them, not over bare sky
    if spec.sun:
        glows.append((shade(spec.halo or spec.sun, dark, veil), spec.halo_size))
        if spec.corona:
            glows.append((shade(spec.corona, dark, veil), spec.sun_size * CORONA_SCALE))
    far = spec.far_moon
    far_d = direction(*far.at) if far else None
    for d, size, tint, bright in field:
        cos = sum(a * b for a, b in zip(d, sun_d, strict=True))
        if cos > away:
            continue
        if far and sum(a * b for a, b in zip(d, far_d, strict=True)) > math.cos(math.radians(far.halo_size)):
            continue  # nor within a far moon's halo
        behind = dome_color(_elev(d), fog, zenith)
        apart = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        for rgb_glow, reach in glows:
            behind = _mix(behind, rgb_glow, glow_share(apart / reach))
        rgb = _mix(behind, shade(tint, dark, veil), spec.stars * bright)
        u, v = _basis(d)
        tips = [(_around(d, u, v, size, a * math.pi / 2), (0, 0), rgb, RADIUS * 0.98) for a in range(4)]
        mesh.quad(tips[0], tips[1], tips[3], tips[2])
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


def cloud_sea(spec, fog, dark=0.0, veil=False):
    """The sea of cloud far below (`cloud_sea_tex`): rings of quads from straight down up to the
    horizon with their uv laid flat, as the overhead cap's are, so it spreads level to the edge of the
    world, its billows lit `cloud_sea` and its hollows `cloud_sea_under`, both fading into the fog at
    the horizon. Drawn under it, a solid floor of the hollows' colour, so the cut-out billows never
    show the dome through them. None for a sky seen from the ground."""
    if not spec.cloud_sea:
        return None
    mesh = SkyMesh()
    fogged = shade(fog, dark, veil)
    lit, under = shade(spec.cloud_sea, dark, veil), shade(spec.cloud_sea_under, dark, veil)
    for depth, r in ((0, RADIUS * 0.97), (1, RADIUS * 0.96)):  # the floor, then the billows over it
        for lo, hi in pairwise(CLOUD_SEA_RINGS):
            for i in range(SEGMENTS):
                a0, a1 = 360.0 * i / SEGMENTS, 360.0 * (i + 1) / SEGMENTS
                corners = []
                for a, e in ((a0, lo), (a1, lo), (a0, hi), (a1, hi)):
                    fade = (e - CLOUD_SEA_RINGS[0]) / -CLOUD_SEA_RINGS[0]  # 0 straight down, 1 at the horizon
                    c = _mix(under if depth == 0 else lit, fogged, fade**2.5)
                    p = direction(a, e)
                    uv = (p[0] * r * CLOUD_SEA_SCALE, p[2] * r * CLOUD_SEA_SCALE) if depth else (0.0, 0.0)
                    corners.append((p, uv, c, r))
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


TEXTURES = {
    "dome": "white",
    "stars": "white",
    "cap": "cloud_cap",
    "cloud_sea": "cloud_cap",
    "clouds": "clouds",
    "far_moon": "white",
    "far_wisps": "cloud_cap",
    "shroud": "white",
    "sun": "white",
    "maria": "white",
    "wisps": "cloud_cap",
    "mist": "mist",
}
DRIFTING = ("cap", "clouds")  # layers that turn slowly around you


def layers(spec, fog, dark=0.0, veil=False):
    """[(layer, mesh)] for a sky, back to front: the dome (with the sun's halo), the stars, the overhead
    cap, a far moon and the wisps across it, the cloud banks, the bank a veiled sun hides in, the sun's disc (and a moon's seas and the wisps
    across it) and the mist. Layers the sky lacks are left out."""
    built = (
        ("dome", dome(spec, fog, dark, veil)),
        ("cloud_sea", cloud_sea(spec, fog, dark, veil)),
        ("stars", stars(spec, fog, dark, veil)),
        ("cap", cap(spec, dark, veil)),
        ("far_moon", far_moon(spec, dark, veil)),
        ("far_wisps", far_wisps(spec, dark, veil)),
        ("clouds", clouds(spec, dark, veil)),
        ("shroud", shroud(spec, dark, veil)),
        ("sun", sun(spec, dark, veil)),
        ("maria", maria(spec, dark, veil)),
        ("wisps", wisps(spec, dark, veil)),
        ("mist", mist(spec, dark, veil)),
    )
    return [(name, mesh) for name, mesh in built if mesh is not None]
