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


class Rig:
    def __init__(self, gpu):
        self.gpu = gpu
        self._stack = [IDENTITY]

    @property
    def top(self):
        return self._stack[-1]

    def apply(self, m):
        self._stack[-1] = mul(self.top, m)

    @contextmanager
    def at(self, x=0, y=0, z=0, rx=0, ry=0, rz=0, s=None):
        """Nested transform: translate, then rotate (y, z, x radians), then uniform scale."""
        self._stack.append(self.top)
        try:
            self.apply(translate(x, y, z))
            if ry:
                self.apply(rot_y(ry))
            if rz:
                self.apply(rot_z(rz))
            if rx:
                self.apply(rot_x(rx))
            if s is not None:
                self.apply(scale(s, s, s))
            yield
        finally:
            self._stack.pop()

    def entity(self, x, y, z, yaw):
        """Places an entity in the world: position plus heading (yaw toward +X at 0)."""
        return self.at(x, y, z, ry=-yaw)

    def part(self, kind, x, y, z, sx, sy, sz, rgb, tex="white", rx=0, ry=0, rz=0, glow=False):
        """Draws a primitive centered at (x, y, z) in the current frame."""
        with self.at(x, y, z, rx=rx, ry=ry, rz=rz):
            m = mul(self.top, scale(sx, sy, sz))
            self.gpu.draw_part(kind, self.gpu.to_matrix(m), rgb, tex=tex, glow=glow)
