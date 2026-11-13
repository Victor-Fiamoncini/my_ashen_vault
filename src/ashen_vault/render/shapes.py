"""Model primitives that raylib has no generator for, as plain triangle lists (no raylib here).

All are unit-sized and centred on the origin like the stock ones in `Gpu.primitive`, so `Rig.part`
scales them the same way:

- `blade`: a lozenge-section slab (thickness along X, width along Z) that narrows a little along +Y,
  then closes to a point. Its two bevelled faces catch the light differently on each side of the ridge,
  so even a thin blade reads as an edge rather than a plank.
- `lozenge`: the blade's section without the point, straight from end to end: curved blade
  segments, fullers, horn and claw shafts.
- `wedge`: a triangular prism whose triangle (in X/Y) points up +Y: axe bits, spikes, teeth, fangs,
  quillon tips, horns.

Faces are flat-shaded (each triangle carries its own normal), which suits the PS1 look."""

SHOULDER = 0.16  # how far below the blade's tip its edges start converging
SHOULDER_WIDTH = 0.82  # the blade's width at the shoulder, as a share of its base width


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _norm(v):
    length = _dot(v, v) ** 0.5 or 1.0
    return (v[0] / length, v[1] / length, v[2] / length)


def _solid(tris):
    """Flat-shaded triangle soup for a convex solid: each triangle is wound counter-clockwise seen
    from outside (raylib culls the other side) and given its outward face normal.
    Returns (vertices, normals, uvs) as flat float lists."""
    points = {p for t in tris for p in t}
    inside = tuple(sum(p[i] for p in points) / len(points) for i in range(3))
    verts, normals, uvs = [], [], []
    for a, b, c in tris:
        n = _cross(_sub(b, a), _sub(c, a))
        centre = tuple((a[i] + b[i] + c[i]) / 3 for i in range(3))
        if _dot(n, _sub(centre, inside)) < 0:
            b, c = c, b
            n = (-n[0], -n[1], -n[2])
        n = _norm(n)
        for p in (a, b, c):
            verts.extend(p)
            normals.extend(n)
            uvs.extend((p[2] + 0.5, p[1] + 0.5))
    return verts, normals, uvs


def _quad(a, b, c, d):
    return [(a, b, c), (a, c, d)]


def blade():
    def ring(y, w):
        h = w / 2
        return [(0.5 * w, y, 0.0), (0.0, y, h), (-0.5 * w, y, 0.0), (0.0, y, -h)]

    base = ring(-0.5, 1.0)
    shoulder = ring(0.5 - SHOULDER, SHOULDER_WIDTH)
    tip = (0.0, 0.5, 0.0)
    tris = _quad(*base)
    for i in range(4):
        j = (i + 1) % 4
        tris += _quad(base[i], base[j], shoulder[j], shoulder[i])
        tris.append((shoulder[i], shoulder[j], tip))
    return _solid(tris)


def lozenge():
    def ring(y):
        return [(0.5, y, 0.0), (0.0, y, 0.5), (-0.5, y, 0.0), (0.0, y, -0.5)]

    lo, hi = ring(-0.5), ring(0.5)
    tris = _quad(*lo) + _quad(*hi)
    for i in range(4):
        j = (i + 1) % 4
        tris += _quad(lo[i], lo[j], hi[j], hi[i])
    return _solid(tris)


def wedge():
    a, b, c = (-0.5, -0.5), (0.5, -0.5), (0.0, 0.5)
    front = [(x, y, 0.5) for x, y in (a, b, c)]
    back = [(x, y, -0.5) for x, y in (a, b, c)]
    tris = [tuple(front), tuple(back)]
    for i in range(3):
        j = (i + 1) % 3
        tris += _quad(front[i], front[j], back[j], back[i])
    return _solid(tris)


SHAPES = {"blade": blade, "lozenge": lozenge, "wedge": wedge}
