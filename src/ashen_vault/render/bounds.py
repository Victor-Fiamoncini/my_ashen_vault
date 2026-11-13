"""Measures a model without drawing it: a stand-in GPU that records the box around every part. Pure,
no raylib, so previews can frame a model and tests can check its size."""

from ashen_vault.render.rig import Rig

CORNERS = [(cx, cy, cz) for cx in (-0.5, 0.5) for cy in (-0.5, 0.5) for cz in (-0.5, 0.5)]


class BoundsGpu:
    """Collects the corners of each part's unit box in model space."""

    def __init__(self):
        self.points = []

    def to_matrix(self, m):
        return m

    def draw_part(self, kind, m, rgb, tex="white", glow=False):
        for cx, cy, cz in CORNERS:
            self.points.append(
                (
                    m[0] * cx + m[1] * cy + m[2] * cz + m[3],
                    m[4] * cx + m[5] * cy + m[6] * cz + m[7],
                    m[8] * cx + m[9] * cy + m[10] * cz + m[11],
                )
            )


def measure(draw):
    """The box around what `draw(rig)` draws: ((min x, y, z), (max x, y, z))."""
    gpu = BoundsGpu()
    draw(Rig(gpu))
    xs, ys, zs = zip(*gpu.points, strict=True)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))
