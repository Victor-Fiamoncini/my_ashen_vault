"""The open sea: on a map with `[meta] open_sea = true` (Harrowmere) the deep water runs on past the
grid's far edge out to the horizon, fogged far more thinly than the land, and the sun lays a path of
glints across it.

Pure: this lays out the far water's cells and the glints' strip; `render/mesh_builder.py` builds the
sea's batch from the cells and `World` draws it, and the strip, with `fog_range`."""

import math
from itertools import pairwise

from ashen_vault.util import rround
from ashen_vault.world.tile_map import TileMap

T = TileMap.TILE
SEA_REACH = 8.0  # the sea's fog ends this many times farther off than the land's
GLITTER_REACH = 2.0  # and the glints' this many times farther again: the sun's path shows to the horizon
FAR = 900.0  # metres the open water runs on past the grid (inside the camera's 1000 m far plane)
SIDE = 120.0  # metres the water runs on to either side of the grid, besides its distance out
BANDS = 8  # rows of cells in each band of the far water; each band's cells are twice the last's
FIRST_CELL = 2.0  # the cell size by the grid: as fine as a tile's, so the seam doesn't warp
LAST_CELL = 64.0
GLITTER_SPREAD = 0.16  # half the path's width over its distance (about 9 degrees either side)
GLITTER_NEAR = 0.6  # metres of half width where the path starts
GLITTER_STEPS = 14
GLITTER_UV = 6.0  # metres of water to one repeat of the glitter texture
GLITTER_LIFT = 0.03  # metres over the water
GLITTER_RISE = 0.002  # metres more per metre out, so far off it never fights the water for depth
GLITTER_FRAME = 0.2  # seconds each twinkle of the glints lasts
GLITTER_LANES = (-1.0, -0.5, 0.0, 0.5, 1.0)  # across the path, its edges at +-1
GLITTER_START = 12.0  # metres out from the eye where the glints begin; nearer they would loom
GLITTER_FADE = 14.0  # metres over which they brighten from nothing beyond that


def is_open(map_):
    return str(map_.meta.get("open_sea", "")).strip() == "true"


def fog_range(land):
    """The sea's fog range, from the land's (as darkness and the Veil have set it)."""
    return (land[0], land[1] * SEA_REACH)


def glitter_fog_range(land):
    start, end = fog_range(land)
    return (start, end * GLITTER_REACH)


def deep_tiles(map_):
    return [(tx, tz, tile) for tx, tz, tile in map_.each_tile() if tile.deep]


def level(map_):
    """The sea's surface height, or None on a map without deep water."""
    deep = deep_tiles(map_)
    return deep[0][2].floor if deep else None


def far_cells(map_):
    """[(x0, z0, x1, z1)] of open water beyond the grid's south edge, out to FAR: bands of cells,
    each band's twice the size of the last, so the near ones warp no more than a tile and the far
    ones cost little. Empty unless the map's sea is open and reaches the south edge."""
    if not is_open(map_) or not any(tz == map_.depth - 1 for _tx, tz, _ in deep_tiles(map_)):
        return []
    width = map_.width * T
    cells = []
    z = map_.depth * T
    size = FIRST_CELL
    end = z + FAR
    while z < end - 1e-6:
        rows = BANDS if size < LAST_CELL else math.ceil((end - z) / size)
        out = z + rows * size - map_.depth * T
        reach = math.ceil((out + SIDE) / size) * size
        x0, x1 = -reach, math.ceil((width + reach) / size) * size
        for j in range(rows):
            for i in range(rround((x1 - x0) / size)):
                cells.append((x0 + i * size, z + j * size, x0 + (i + 1) * size, z + (j + 1) * size))
        z += rows * size
        size = min(size * 2, LAST_CELL)
    return cells


def sun_path(sun_at):
    """The sun's bearing over the water, a unit (dx, dz)."""
    a = math.radians(sun_at[0])
    return math.cos(a), math.sin(a)


def glitter(eye_x, eye_z, z_from, y, sun_at, frame=0):
    """The sun's path of glints on the water: a strip from where the sea begins out to the horizon
    along the sun's bearing, widening with distance (so it keeps one width to the eye), lanes bright
    down its middle and dim at its edges. Returns (verts, uvs, colour weights): triangles in world
    space, uvs anchored to the water (shifted by `frame` so the glints twinkle), and per vertex how
    much of the sun's colour it takes (1 down the middle, none at the edges or close by). None if the sun
    stands over no sea (`z_from`, where the sea starts, lies behind its bearing)."""
    dx, dz = sun_path(sun_at)
    if dz <= 1e-6:
        return None
    start = max(GLITTER_START, (z_from - eye_z) / dz)
    side = (-dz, dx)  # to the left of the path
    verts, uvs, weights = [], [], []
    shift = (frame * 0.37) % 1.0

    def point(d, lane):
        half = max(GLITTER_NEAR, d * GLITTER_SPREAD)
        x = eye_x + dx * d + side[0] * half * lane
        z = eye_z + dz * d + side[1] * half * lane
        return (x, y + GLITTER_LIFT + d * GLITTER_RISE, z), (x / GLITTER_UV, z / GLITTER_UV + shift)

    ds = [start + FAR * (k / GLITTER_STEPS) ** 2 for k in range(GLITTER_STEPS + 1)]
    for d0, d1 in pairwise(ds):
        for l0, l1 in pairwise(GLITTER_LANES):
            corners = [(d0, l0), (d0, l1), (d1, l1), (d1, l0)]
            for i in (0, 1, 2, 0, 2, 3):
                d, lane = corners[i]
                p, uv = point(d, lane)
                verts.extend(p)
                uvs.extend(uv)
                weights.append((1.0 - abs(lane) * 0.75) * min((d - start) / GLITTER_FADE, 1.0))
    return verts, uvs, weights
