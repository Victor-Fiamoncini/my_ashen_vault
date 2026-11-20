"""A cavern's vault (`[meta] vault = <h>`, Old Harrowmere): a roof of rough rock over the whole map at
height `h`, lumpy, with stalactites hanging from it, and a crack in it over the map's `sun_shaft` where
the daylight falls through. It is only drawn (`MeshBuilder._build_vault`): no tile gains a ceiling, so
collision, sight lines and everything that asks for open sky are untouched.

Heights come from hashing the vertex's place, never from `random`, so the vault is the same every
time it is built."""

import math

from ashen_vault.util import rround
from ashen_vault.world.tile_map import TileMap

LUMP = 2.0  # metres the vault's lumps hang below its height at the most
LUMP_CELLS = (6.0, 2.5)  # the sizes of the two octaves of lumps, in metres
SPIKE_EVERY = 3  # stalactites hang only from vertices on a lattice this many metres apart
SPIKE_CHANCE = 0.14  # the share of those that do
SPIKE_DROP = (3.0, 7.0)  # how far a stalactite reaches down below the lumps round it
MAX_DROP = LUMP + SPIKE_DROP[1]
SHAFT_LEAN = 0.12  # radians the sun shaft leans (about z) from the crack down to the floor
CRACK_LEN = 5.5  # the crack's length (along z) and width (along x), in metres
CRACK_WIDTH = 2.0
CRACK_CALM = 3.0  # metres round the crack where the rock flattens out to meet its lip
CRACK_LIGHT = (1.3, 1.0, 0.55)  # the daylight glowing on the rock round the crack
CRACK_LIGHT_RADIUS = 12.0


def _hash(ix, iz, salt=0):
    """A value in [0, 1) for an integer point: the same every time."""
    h = (ix * 374761393 + iz * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def _smooth(k):
    return k * k * (3 - 2 * k)


def _noise(x, z, cell, salt):
    """Value noise in [0, 1): hashed lattice values every `cell` metres, eased between."""
    gx, gz = x / cell, z / cell
    ix, iz = math.floor(gx), math.floor(gz)
    kx, kz = _smooth(gx - ix), _smooth(gz - iz)
    a = _hash(ix, iz, salt) + (_hash(ix + 1, iz, salt) - _hash(ix, iz, salt)) * kx
    b = _hash(ix, iz + 1, salt) + (_hash(ix + 1, iz + 1, salt) - _hash(ix, iz + 1, salt)) * kx
    return a + (b - a) * kz


class Vault:
    def __init__(self, height, tex, crack=None, crack_len=CRACK_LEN, crack_width=CRACK_WIDTH, crack_yaw=0.0):
        self.height = height
        self.tex = tex
        self.crack = crack  # (x, z) of the crack's centre, or None
        # A `sun_shaft`'s `rift=<length>,<width>` and `rift_yaw=` (degrees from +z) make its crack a great
        # rift: longer, wider, and running whichever way across the roof.
        self.crack_len = crack_len
        self.crack_width = crack_width
        self.crack_yaw = crack_yaw

    @classmethod
    def of(cls, map_):
        """The map's vault, or None when its `[meta]` sets no `vault`."""
        if "vault" not in map_.meta:
            return None
        length, width, yaw = crack_shape(map_)
        return cls(
            float(map_.meta["vault"]),
            map_.meta.get("vault_tex", "cavern_rock"),
            crack_at(map_),
            length,
            width,
            yaw,
        )

    def _crack_reach(self, x, z):
        """How far (x, z) lies inside the crack's outline: below 1 inside it, 1 on its lip."""
        if self.crack is None:
            return math.inf
        dx, dz = x - self.crack[0], z - self.crack[1]
        if self.crack_yaw:  # into the rift's own frame: along it is local z, across it local x
            c, s = math.cos(self.crack_yaw), math.sin(self.crack_yaw)
            dx, dz = dx * c - dz * s, dx * s + dz * c
        # A jagged outline: its width changes along its length, hashed metre by metre.
        jag = 0.75 + 0.5 * _hash(rround(dz), 7, 31)
        return math.hypot(dz / (self.crack_len / 2), dx / (self.crack_width / 2 * jag))

    def in_crack(self, x, z):
        """Whether the point (a cell's centre) lies open in the crack."""
        return self._crack_reach(x, z) < 1.0

    def height_at(self, x, z):
        """The vault's underside at (x, z): lumps of rock, and now and then a stalactite."""
        ix, iz = rround(x), rround(z)
        lump = 0.6 * _noise(x, z, LUMP_CELLS[0], 1) + 0.4 * _noise(x, z, LUMP_CELLS[1], 2)
        drop = LUMP * lump
        if ix % SPIKE_EVERY == 0 and iz % SPIKE_EVERY == 0 and _hash(ix, iz, 3) < SPIKE_CHANCE:
            drop += SPIKE_DROP[0] + (SPIKE_DROP[1] - SPIKE_DROP[0]) * _hash(ix, iz, 4)
        if self.crack is not None:  # flat round the crack, so its lip meets the shaft's top
            past = (self._crack_reach(x, z) - 1.0) * min(self.crack_len, self.crack_width) / 2
            drop *= min(max(past / CRACK_CALM, 0.0), 1.0)
        return self.height - drop

    def covers(self, tile):
        """Whether the vault spans the tile: all but the walls already reaching it and the tiles
        roofed by their own ceiling (a gallery cut through the rock, a lift's shaft)."""
        if tile.solid:
            return tile.top < self.height
        return tile.ceil is None

    def crack_light(self):
        """(x, y, z, radius, color) of the daylight on the rock round the crack, or None."""
        if self.crack is None:
            return None
        radius = max(CRACK_LIGHT_RADIUS, self.crack_len * 0.75)
        return (self.crack[0], self.height - 2.0, self.crack[1], radius, list(CRACK_LIGHT))


def shaft_top(map_, spec):
    """(x, y, z) of the top of a `sun_shaft`: it leans by SHAFT_LEAN, its top off toward -x."""
    x, z = TileMap.center(spec.tx, spec.tz)
    height = float(spec.props.get("height", "14"))
    floor = map_[spec.tx, spec.tz].floor
    return x - height * math.sin(SHAFT_LEAN), floor + height * math.cos(SHAFT_LEAN), z


def crack_at(map_):
    """(x, z) of the crack over the map's sun shaft, or None if it has none."""
    for spec in map_.entities:
        if spec.kind == "sun_shaft":
            x, _, z = shaft_top(map_, spec)
            return x, z
    return None


def crack_shape(map_):
    """(length, width, yaw in radians) of the crack over the map's sun shaft: CRACK_LEN by CRACK_WIDTH
    along z unless the shaft sets `rift=<length>,<width>` and `rift_yaw=` (degrees)."""
    for spec in map_.entities:
        if spec.kind == "sun_shaft":
            length, width = rift_of(spec)
            return length, width, math.radians(float(spec.props.get("rift_yaw", "0")))
    return CRACK_LEN, CRACK_WIDTH, 0.0


def rift_of(spec):
    """(length, width) of a `sun_shaft`'s crack."""
    if "rift" not in spec.props:
        return CRACK_LEN, CRACK_WIDTH
    length, width = (float(v) for v in spec.props["rift"].split(","))
    return length, width
