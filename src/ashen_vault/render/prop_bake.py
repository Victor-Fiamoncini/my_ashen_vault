"""Bakes props that never change into world-space triangle batches, lit the way the PS1 shader lights
models, so a whole town of roofs, windows and statues costs a handful of draws a frame instead of a
Python call per part. Pure, no raylib: it stands in for the GPU under a `Rig` and the unit primitives'
triangles come from `tris(kind)` (the real meshes' data, from `Gpu.primitive_tris`)."""

import math

from ashen_vault.render.mesh_builder import Batch

CHUNK = 8  # tiles a side: baked props are grouped, and culled, by squares this big
TILE = 2.0
CHUNK_REACH = CHUNK * TILE * math.sqrt(0.5)  # metres from a chunk's centre to its corner
# The baked colour is halved to fit a byte, and the shader doubles it back (`isModel` -1).
BAKE_SCALE = 0.5
MODEL_LIGHT_FLOOR = 0.12  # as `Gpu.model_light`: models never vanish into the dark
GLOW_LIGHT = 1.5  # as `Gpu.draw_part` with `glow`
_SUN = (0.35, 1.0, 0.25)
_SUN_LEN = math.sqrt(sum(c * c for c in _SUN))
SUN = tuple(c / _SUN_LEN for c in _SUN)  # the light direction `ps1.vs` shades models by


def chunk_of(tx, tz):
    return tx // CHUNK, tz // CHUNK


def chunk_centre(cx, cz):
    return (cx + 0.5) * CHUNK * TILE, (cz + 0.5) * CHUNK * TILE


class PropBaker:
    """A recording GPU: every part drawn through a `Rig` on it lands, transformed and lit, in the batch
    of the current `group` and its texture (`batches[(group, tex)]`)."""

    def __init__(self, tris):
        self.tris = tris
        self.batches = {}
        self.group = None
        self._light = (1.0, 1.0, 1.0)

    def model_light(self, rgb):
        self._light = tuple(c + MODEL_LIGHT_FLOOR for c in rgb)

    @staticmethod
    def to_matrix(m):
        return m

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        batch = self.batches.get((self.group, tex))
        if batch is None:
            batch = self.batches[(self.group, tex)] = Batch()
        light = (GLOW_LIGHT,) * 3 if glow else self._light
        tint = [max(0, min(255, int(c))) / 255 * BAKE_SCALE for c in rgb]
        l0, l1, l2 = light
        m0, m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11 = m[:12]
        verts, normals, uvs = self.tris(kind)
        out_v, out_c, out_l = batch.verts, batch.colors, batch.light
        sx, sy, sz = SUN
        for i in range(0, len(verts), 3):
            x, y, z = verts[i], verts[i + 1], verts[i + 2]
            out_v.extend(
                (
                    m0 * x + m1 * y + m2 * z + m3,
                    m4 * x + m5 * y + m6 * z + m7,
                    m8 * x + m9 * y + m10 * z + m11,
                )
            )
            x, y, z = normals[i], normals[i + 1], normals[i + 2]
            nx, ny, nz = m0 * x + m1 * y + m2 * z, m4 * x + m5 * y + m6 * z, m8 * x + m9 * y + m10 * z
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            shade = 0.55 + 0.45 * max((nx * sx + ny * sy + nz * sz) / length, 0.0)
            out_c.extend(tint)
            out_l.extend((l0 * shade, l1 * shade, l2 * shade))
        batch.uvs.extend(uvs)
