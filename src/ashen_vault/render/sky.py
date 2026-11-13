"""Draws the sky (`world/sky.py`) around the camera before the world: no fog, no depth, no culling,
so the world simply draws over it. Meshes are rebuilt only when the light they were baked for
changes (darkness easing in, the Veil), and the cloud banks turn slowly."""

import raylib as rl

from ashen_vault.util import rround
from ashen_vault.world import sky

# How finely the baked colours follow the darkness and the fog: a change smaller than this reuses
# the meshes already uploaded.
STEP = 1 / 48
NO_FOG = (1.0e5, 1.0e5 + 1.0)


class SkyPass:
    def __init__(self, gpu):
        self.gpu = gpu
        self._key = None
        self._meshes = []  # (mesh, texture, drifts)

    def _bake(self, spec, fog, dark, veil):
        key = (id(spec), tuple(rround(c / STEP) for c in fog), rround(dark / STEP), veil)
        if key == self._key:
            return
        self.release()
        self._key = key
        for name, built in sky.layers(spec, fog, dark, veil):
            self._meshes.append((self.gpu.upload_batch(built), sky.TEXTURES[name], name in sky.DRIFTING))

    def release(self):
        for mesh, _, _ in self._meshes:
            self.gpu.unload_mesh(mesh)
        self._meshes = []
        self._key = None

    def draw(self, meta, eye, fog, fog_range, dark, veil, t):
        """Call inside begin_mode_3d, before the world. Does nothing on a map without a sky."""
        spec = sky.get(meta)
        if spec is None:
            return
        self._bake(spec, fog, dark, veil)
        gpu = self.gpu
        gpu.set_vec2("fogRange", NO_FOG)
        rl.rlDisableDepthTest()
        rl.rlDisableDepthMask()
        rl.rlDisableBackfaceCulling()
        place = rl.MatrixTranslate(eye[0], eye[1], eye[2])
        turned = rl.MatrixMultiply(rl.MatrixRotateY(t * spec.drift), place)
        for mesh, tex, drifts in self._meshes:
            gpu.draw_sky_batch(mesh, tex, turned if drifts else place)
        rl.rlEnableBackfaceCulling()
        rl.rlEnableDepthMask()
        rl.rlEnableDepthTest()
        gpu.set_vec2("fogRange", fog_range)
