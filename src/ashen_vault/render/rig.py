"""Row-major 4x4 matrix stack for building hierarchical low-poly models. Models face +X, up is +Y."""

import math
from contextlib import contextmanager

IDENTITY = (1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0)


def mul(a, b):
    out = [0.0] * 16
    for r in range(4):
        a0, a1, a2, a3 = a[r * 4], a[r * 4 + 1], a[r * 4 + 2], a[r * 4 + 3]
        for c in range(4):
            out[r * 4 + c] = a0 * b[c] + a1 * b[4 + c] + a2 * b[8 + c] + a3 * b[12 + c]
    return out


def translate(x, y, z):
    return (1.0, 0, 0, x, 0, 1.0, 0, y, 0, 0, 1.0, z, 0, 0, 0, 1.0)


def scale(x, y, z):
    return (x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1.0)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return (1.0, 0, 0, 0, 0, c, -s, 0, 0, s, c, 0, 0, 0, 0, 1.0)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return (c, 0, s, 0, 0, 1.0, 0, 0, -s, 0, c, 0, 0, 0, 0, 1.0)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return (c, -s, 0, 0, s, c, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0)


def affine(a, b):
    """`mul` for two affine matrices (bottom row 0, 0, 0, 1), which is all a Rig ever builds."""
    a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11 = a[:12]
    b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11 = b[:12]
    return (
        a0 * b0 + a1 * b4 + a2 * b8,
        a0 * b1 + a1 * b5 + a2 * b9,
        a0 * b2 + a1 * b6 + a2 * b10,
        a0 * b3 + a1 * b7 + a2 * b11 + a3,
        a4 * b0 + a5 * b4 + a6 * b8,
        a4 * b1 + a5 * b5 + a6 * b9,
        a4 * b2 + a5 * b6 + a6 * b10,
        a4 * b3 + a5 * b7 + a6 * b11 + a7,
        a8 * b0 + a9 * b4 + a10 * b8,
        a8 * b1 + a9 * b5 + a10 * b9,
        a8 * b2 + a9 * b6 + a10 * b10,
        a8 * b3 + a9 * b7 + a10 * b11 + a11,
        0.0,
        0.0,
        0.0,
        1.0,
    )


def local(x, y, z, rx=0, ry=0, rz=0, sx=1.0, sy=1.0, sz=1.0):
    """translate(x, y, z) * rot_y(ry) * rot_z(rz) * rot_x(rx) * scale(sx, sy, sz), built at once."""
    if not (rx or ry or rz):
        return (sx, 0.0, 0.0, x, 0.0, sy, 0.0, y, 0.0, 0.0, sz, z, 0.0, 0.0, 0.0, 1.0)
    cy, sny = (math.cos(ry), math.sin(ry)) if ry else (1.0, 0.0)
    cz, snz = (math.cos(rz), math.sin(rz)) if rz else (1.0, 0.0)
    cx, snx = (math.cos(rx), math.sin(rx)) if rx else (1.0, 0.0)
    return (
        cy * cz * sx,
        (sny * snx - cy * snz * cx) * sy,
        (cy * snz * snx + sny * cx) * sz,
        x,
        snz * sx,
        cz * cx * sy,
        -cz * snx * sz,
        y,
        -sny * cz * sx,
        (sny * snz * cx + cy * snx) * sy,
        (cy * cx - sny * snz * snx) * sz,
        z,
        0.0,
        0.0,
        0.0,
        1.0,
    )


class Rig:
    def __init__(self, gpu):
        self.gpu = gpu
        self._stack = [IDENTITY]

    @property
    def top(self):
        return self._stack[-1]

    def apply(self, m):
        self._stack[-1] = affine(self._stack[-1], m)

    @contextmanager
    def at(self, x=0, y=0, z=0, rx=0, ry=0, rz=0, s=None):
        """Nested transform: translate, then rotate (y, z, x radians), then uniform scale."""
        k = 1.0 if s is None else s
        self._stack.append(affine(self._stack[-1], local(x, y, z, rx, ry, rz, k, k, k)))
        try:
            yield
        finally:
            self._stack.pop()

    def entity(self, x, y, z, yaw):
        """Places an entity in the world: position plus heading (yaw toward +X at 0)."""
        return self.at(x, y, z, ry=-yaw)

    def part(self, kind, x, y, z, sx, sy, sz, rgb, tex="white", rx=0, ry=0, rz=0, glow=False):
        """Draws a primitive centered at (x, y, z) in the current frame."""
        m = affine(self._stack[-1], local(x, y, z, rx, ry, rz, sx, sy, sz))
        self.gpu.draw_part(kind, self.gpu.to_matrix(m), rgb, tex=tex, glow=glow)
