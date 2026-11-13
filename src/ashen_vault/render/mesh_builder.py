"""Turns a TileMap into triangle soup grouped by texture, with lighting baked
into vertex colors. Pure Python: the GPU upload lives in Gpu."""

import math
from collections import defaultdict
from dataclasses import dataclass, field

from ashen_vault.util import rround
from ashen_vault.world.tile_map import TileMap


@dataclass
class Light:
    x: float
    y: float
    z: float
    radius: float
    color: list


@dataclass
class Batch:
    verts: list = field(default_factory=list)
    uvs: list = field(default_factory=list)
    colors: list = field(default_factory=list)

    @property
    def vertex_count(self):
        return len(self.verts) // 3


SEG = 1.0  # max quad size in meters, keeps affine warping tolerable
# Defaults for light-emitting entities; a map can override them with y= and color=.
LIGHT_Y = {"light": "2.0", "candles": "0.6", "fungus": "0.7"}
LIGHT_COLOR = {"fungus": "0.3,0.85,0.65"}
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
T = TileMap.TILE


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


class MeshBuilder:
    def __init__(self, map_, lights=()):
        self.map = map_
        self.lights = list(lights)
        self.ambient = map_.meta.get("ambient", [0.2, 0.2, 0.2])
        self.batches = defaultdict(Batch)

    @staticmethod
    def lights_for(map_):
        lights = []
        for e in map_.entities:
            if e.kind not in ("torch", "brazier", "light", "candles", "fungus"):
                continue
            x, z = TileMap.center(e.tx, e.tz)
            height = LIGHT_Y.get(e.kind, "1.6")
            wall = map_.wall_yaw(e.tx, e.tz) if e.kind == "torch" else None
            if wall is not None:  # a sconce: the flame sits up against the wall
                x -= math.cos(wall) * 0.6
                z -= math.sin(wall) * 0.6
                height = "1.9"
            y = map_[e.tx, e.tz].floor + float(e.props.get("y", height))
            color = [
                float(c) for c in e.props.get("color", LIGHT_COLOR.get(e.kind, "1.0,0.62,0.32")).split(",")
            ]
            radius = e.props.get("radius", "3" if e.kind == "candles" else "7")
            lights.append(Light(x, y, z, float(radius), color))
        return lights

    def light_at(self, x, y, z, nx=0.0, ny=1.0, nz=0.0):
        """Light reaching a point, without shadows. Used for models too."""
        r, g, b = self.ambient
        for l in self.lights:
            dx = l.x - x
            dy = l.y - y
            dz = l.z - z
            d = math.sqrt(dx * dx + dy * dy + dz * dz)
            if d >= l.radius:
                continue
            f = (1.0 - d / l.radius) ** 2
            facing = 1.0 if d < 1e-3 else max((dx * nx + dy * ny + dz * nz) / d, 0.0) * 0.7 + 0.3
            k = f * facing * 1.4
            r += l.color[0] * k
            g += l.color[1] * k
            b += l.color[2] * k
        return [r, g, b]

    def build(self):
        for tx, tz, tile in self.map.each_tile():
            if tile.solid:
                self._build_solid(tx, tz, tile)
            else:
                self._build_open(tx, tz, tile)
        return self

    def _build_open(self, tx, tz, tile):
        x0 = tx * T
        z0 = tz * T
        self._horizontal(tile.floor_tex, x0, z0, tile.floor, 1, 0.85 if tile.liquid else 1.0)
        if tile.ceil is not None:
            self._horizontal(tile.ceil_tex, x0, z0, tile.ceil, -1, 0.75)

        for dx, dz in DIRS:
            nb = self.map[tx + dx, tz + dz]
            if nb.solid:
                top = tile.ceil if tile.ceil is not None else nb.top
                if top > tile.floor:
                    self._wall(nb.wall_tex, tx, tz, dx, dz, tile.floor, top)
            elif nb.floor < tile.floor:
                # Step face: drawn by the higher tile, facing down into the neighbor.
                self._wall(tile.wall_tex, tx, tz, dx, dz, nb.floor, tile.floor, face_out=True)
            if nb.solid:
                continue
            if tile.ceil is not None and nb.ceil is not None and nb.ceil > tile.ceil:
                self._wall(tile.wall_tex, tx, tz, dx, dz, tile.ceil, nb.ceil, face_out=True)
            elif tile.ceil is not None and nb.ceil is None:
                self._wall(tile.wall_tex, tx, tz, dx, dz, tile.ceil, tile.ceil + 0.6, face_out=True)

    def _build_solid(self, tx, tz, tile):
        exposed = any(not (nb := self.map[tx + dx, tz + dz]).solid and nb.ceil is None for dx, dz in DIRS)
        if not exposed:
            return
        self._horizontal(tile.floor_tex, tx * T, tz * T, tile.top, 1, 0.9)
        for dx, dz in DIRS:
            nb = self.map[tx + dx, tz + dz]
            if not (nb.solid and nb.top < tile.top):
                continue
            self._wall(tile.wall_tex, tx, tz, dx, dz, nb.top, tile.top, face_out=True)

    def _horizontal(self, tex, x0, z0, y, up, shade):
        """Floor (up = 1) or ceiling (up = -1) of one tile, split into SEG squares."""
        n = rround(T / SEG)
        for i in range(n):
            for j in range(n):
                ax = x0 + i * SEG
                az = z0 + j * SEG
                pts = [(ax, y, az), (ax, y, az + SEG), (ax + SEG, y, az + SEG), (ax + SEG, y, az)]
                uvs = [(p[0] / T, p[2] / T) for p in pts]
                self._quad(tex, pts, uvs, (0.0, float(up), 0.0), shade)

    def _wall(self, tex, tx, tz, dx, dz, y0, y1, face_out=False):
        """Vertical face on the edge of tile (tx, tz) toward (dx, dz). Faces into the tile unless face_out."""
        cx = (tx + 0.5) * T
        cz = (tz + 0.5) * T
        ex = cx + dx * T / 2
        ez = cz + dz * T / 2
        # Edge endpoints run perpendicular to the direction.
        ax = ex - abs(dz) * T / 2
        az = ez - abs(dx) * T / 2
        bx = ex + abs(dz) * T / 2
        bz = ez + abs(dx) * T / 2
        normal = (float(dx), 0.0, float(dz)) if face_out else (float(-dx), 0.0, float(-dz))
        shade = 0.9 if dx == 0 else 0.78
        cols = rround(T / SEG)
        rows = math.ceil((y1 - y0) / SEG)
        for i in range(cols):
            u0 = i / cols
            u1 = (i + 1) / cols
            px0 = ax + (bx - ax) * u0
            pz0 = az + (bz - az) * u0
            px1 = ax + (bx - ax) * u1
            pz1 = az + (bz - az) * u1
            for r in range(rows):
                ya = y0 + (y1 - y0) * r / rows
                yb = y0 + (y1 - y0) * (r + 1) / rows
                pts = [(px0, ya, pz0), (px1, ya, pz1), (px1, yb, pz1), (px0, yb, pz0)]
                uvs = [((p[0] + p[2]) / T, -p[1] / T) for p in pts]
                self._quad(tex, pts, uvs, normal, shade, ao_floor=y0)

    def _quad(self, tex, pts, uvs, normal, shade, ao_floor=None):
        a, b, c = pts[0], pts[1], pts[2]
        if _dot(_cross(_sub(b, a), _sub(c, a)), normal) < 0:
            pts = pts[::-1]
            uvs = uvs[::-1]
        batch = self.batches[tex]
        colors = []
        for p in pts:
            k = shade
            if ao_floor is not None:
                k *= 0.7 + 0.3 * min((p[1] - ao_floor) / 0.8, 1.0)
            colors.append([min(max(ch * k, 0.0), 1.0) for ch in self.light_at(p[0], p[1], p[2], *normal)])
        for i in (0, 1, 2, 0, 2, 3):
            batch.verts.extend(pts[i])
            batch.uvs.extend(uvs[i])
            batch.colors.extend(colors[i])
