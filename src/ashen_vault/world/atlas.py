"""Where the lands lie: every sky-lit area's place on one map of the world, and the great landmarks
seen from all of them (the burnt volcano beyond the Cinderhold, the Hollow Peak behind Vesperholm),
so each sky draws them at their true bearing and size. A map names its place in `[meta]`
(`atlas = harrowmere`); `world/sky.py` turns what it sees from there into far layers.

Kilometres, x east and z south, as on every map's grid (north is -z: Vesperholm's moon hangs at
azimuth 270 over every map). Harrowmere is the middle of the world: the cemetery lies west of it, the
Verdant Hollow east, the open sea south; the north road climbs NNW to the Cinderhold, with the volcano
beyond, and the Vesper Gate leads NNE to Vesperholm, the Hollow Peak behind it to the north-east (clear of
the moon, which hangs over the cathedral)."""

import math
from dataclasses import dataclass

# (x, z) in km, and how high the eye stands (km) above the lowlands.
PLACES = {
    "harrowmere": (0.0, 0.0, 0.0),
    "ashen_cemetery": (-1.5, 0.0, 0.0),
    "verdant_hollow": (1.5, 0.2, 0.0),
    "cinderhold": (-2.0, -6.0, 0.0),
    "cinder_keep": (-2.0, -6.0, 0.0),
    "vesperholm": (2.0, -8.0, 0.3),
    "herrans_castle": (5.5, -11.0, 1.0),
}

# The volcano is placed so that from the Cinderhold it stands at azimuth 243, 5 km off: the ridge the
# fortress was first drawn with.
VOLCANO_FROM = "cinderhold"
VOLCANO_BEARING = 243.0
VOLCANO_KM = 5.0
PEAK_WIDTH = 3.5  # km its shoulders spread across
NEAR = 1.0  # km: a landmark nearer than this is the ground you stand on, not part of the sky


@dataclass(frozen=True)
class Landmark:
    x: float
    z: float
    height: float  # km above the lowlands


def _volcano():
    x, z, _ = PLACES[VOLCANO_FROM]
    a = math.radians(VOLCANO_BEARING)
    return Landmark(x + VOLCANO_KM * math.cos(a), z + VOLCANO_KM * math.sin(a), 2.0)


LANDMARKS = {
    "volcano": _volcano(),
    "hollow_peak": Landmark(5.5, -11.0, 2.4),
}


@dataclass(frozen=True)
class Sight:
    """A landmark as seen from a place: its bearing (degrees, 0 east, 90 south), how far off it is
    (km), and how high its top stands over the horizon (degrees)."""

    azimuth: float
    km: float
    elevation: float


def place(meta):
    """The place a map's `[meta]` names (`atlas = ...`), or None."""
    name = str(meta.get("atlas", "")).strip()
    return name if name in PLACES else None


def sight(at, landmark):
    """How the landmark `landmark` looks from the place `at`, or None if you stand on it."""
    x, z, eye = PLACES[at]
    lm = LANDMARKS[landmark]
    dx, dz = lm.x - x, lm.z - z
    km = math.hypot(dx, dz)
    if km < NEAR:
        return None
    azimuth = math.degrees(math.atan2(dz, dx)) % 360.0
    return Sight(azimuth, km, math.degrees(math.atan2(lm.height - eye, km)))
