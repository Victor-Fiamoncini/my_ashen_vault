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
    # Per vertex, what a light added later needs: shade factor, normal and the unclamped light.
    lit: list = field(default_factory=list)

    @property
    def vertex_count(self):
        return len(self.verts) // 3


SEG = 1.0  # max quad size in meters, keeps affine warping tolerable
# Light-emitting entities and their defaults; a map can override them with y=, color= and radius=.
LIGHT_KINDS = (
    "torch",
    "brazier",
    "light",
    "candles",
    "fungus",
    "bonfire",
    "giant_mushroom",
    "shelf_fungus",
    "hearth",
    "lamp_post",
    "window",
)
LIGHT_Y = {
    "lamp_post": "2.6",
    "light": "2.0",
    "candles": "0.6",
    "fungus": "0.7",
    "bonfire": "0.9",
    "giant_mushroom": "2.2",
}
LIGHT_Y_WALL = {"shelf_fungus": "1.4", "hearth": "0.6", "window": "3.0"}
LIGHT_COLOR = {
    "fungus": "0.3,0.85,0.65",
    "giant_mushroom": "0.55,0.35,0.85",
    "shelf_fungus": "0.25,0.7,0.75",
    "bonfire": "1.0,0.55,0.25",
    "hearth": "1.0,0.6,0.3",
    "lamp_post": "1.0,0.78,0.45",
    "window": "0.55,0.62,0.8",
}
LIGHT_RADIUS = {
    "hearth": "6",
    "lamp_post": "7",
    "window": "8",
    "candles": "3",
    "shelf_fungus": "4",
    "giant_mushroom": "6",
    "bonfire": "9",
}
# Fires that can stand cold (`unlit`) until something kindles them.
KINDLING = ("brazier", "bonfire")
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
T = TileMap.TILE
# Floors that shine by themselves: drawn at full brightness, and they light what is around them.
GLOWING_FLOORS = ("lava",)
LAVA_LIGHT = (1.0, 0.45, 0.15)
LAVA_LIGHT_RADIUS = 6.0
LAVA_LIGHT_SPACING = 3  # tiles between the lights a lava field casts
MODEL_LIGHT_GRID = 0.5  # metres: models are lit from the nearest point of a grid this fine


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _shine(l, rgb, x, y, z, nx, ny, nz):
    """Adds light `l`'s share at a point (with normal n) to `rgb`, in place."""
    dx = l.x - x
    dy = l.y - y
    dz = l.z - z
    d2 = dx * dx + dy * dy + dz * dz
    if d2 >= l.radius * l.radius:
        return
    d = math.sqrt(d2)
    f = (1.0 - d / l.radius) ** 2
    facing = 1.0 if d < 1e-3 else max((dx * nx + dy * ny + dz * nz) / d, 0.0) * 0.7 + 0.3
    k = f * facing * 1.4
    rgb[0] += l.color[0] * k
    rgb[1] += l.color[1] * k
    rgb[2] += l.color[2] * k


class MeshBuilder:
    def __init__(self, map_, lights=()):
        self.map = map_
        self.lights = list(lights)
        self.ambient = map_.meta.get("ambient", [0.2, 0.2, 0.2])
        self.batches = defaultdict(Batch)
        self._model_light = {}  # light for models, by spot on a MODEL_LIGHT_GRID

    @staticmethod
    def light_for(map_, e):
        """The Light an emitting entity casts (see LIGHT_KINDS), ignoring whether it is lit."""
        x, z = TileMap.center(e.tx, e.tz)
        height = LIGHT_Y.get(e.kind, "1.6")
        wall = map_.wall_yaw(e.tx, e.tz) if e.kind in ("torch", "shelf_fungus", "hearth", "window") else None
        if wall is not None:  # a sconce, a bracket fungus, a hearth or a window: up against the wall
            x -= math.cos(wall) * 0.6
            z -= math.sin(wall) * 0.6
            height = LIGHT_Y_WALL.get(e.kind, "1.9")
        y = map_[e.tx, e.tz].floor + float(e.props.get("y", height))
        color = [float(c) for c in e.props.get("color", LIGHT_COLOR.get(e.kind, "1.0,0.62,0.32")).split(",")]
        radius = e.props.get("radius", LIGHT_RADIUS.get(e.kind, "7"))
        return Light(x, y, z, float(radius), color)

    @staticmethod
    def lights_for(map_, lit=None):
        """Lights from the map's entities. A cold (`unlit`) brazier or bonfire only counts once
        `lit(spec)` says it has been kindled."""
        lights = []
        for e in map_.entities:
            if e.kind not in LIGHT_KINDS:
                continue
            if e.kind in KINDLING and "unlit" in e.props and not (lit and lit(e)):
                continue
            lights.append(MeshBuilder.light_for(map_, e))
        return lights + MeshBuilder.lava_lights(map_)

    @staticmethod
    def lava_lights(map_):
        """A glow along the shores of every lava field, where it lights something you walk on: one
        light per patch of shore, spread at least LAVA_LIGHT_SPACING tiles apart, so a wide gorge
        doesn't cost hundreds of lights nobody would see."""
        lights = []
        taken = []
        for tx, tz, tile in map_.each_tile():
            if tile.solid or tile.floor_tex not in GLOWING_FLOORS:
                continue
            shore = any(
                (nb := map_[tx + dx, tz + dz]).walkable and not nb.hazardous and not nb.needs_footing
                for dx in (-1, 0, 1)
                for dz in (-1, 0, 1)
            )
            if not shore:
                continue
            if any(abs(tx - x) < LAVA_LIGHT_SPACING and abs(tz - z) < LAVA_LIGHT_SPACING for x, z in taken):
                continue
            taken.append((tx, tz))
            x, z = TileMap.center(tx, tz)
            lights.append(Light(x, tile.floor + 1.0, z, LAVA_LIGHT_RADIUS, list(LAVA_LIGHT)))
        return lights

    def light_at(self, x, y, z, nx=0.0, ny=1.0, nz=0.0):
        """Light reaching a point, without shadows. Used for models too. A dark tile keeps only part
        of the ambient light; the point is nudged along its normal so a wall face takes the
        darkness of the tile it faces."""
        keep = 1.0 - self.map.tile_at(x + nx * 0.05, z + nz * 0.05).dark
        rgb = [c * keep for c in self.ambient]
        for l in self.lights:
            _shine(l, rgb, x, y, z, nx, ny, nz)
        return rgb

    def model_light_at(self, x, y, z):
        """Light falling on a model at (x, y, z), looked up on a coarse grid and remembered: models
        are lit every frame, and the baked lights only change when a fire is kindled."""
        g = MODEL_LIGHT_GRID
        key = (round(x / g), round(y / g), round(z / g))
        rgb = self._model_light.get(key)
        if rgb is None:
            rgb = self._model_light[key] = self.light_at(key[0] * g, key[1] * g, key[2] * g)
        return rgb

    def add_light(self, light):
        """Adds a light after the build (a brazier kindled) by brightening only the vertices it
        reaches. Returns the textures whose batches changed and need uploading again."""
        self.lights.append(light)
        self._model_light.clear()
        changed = set()
        r2 = light.radius * light.radius
        for tex, batch in self.batches.items():
            verts, colors, lit = batch.verts, batch.colors, batch.lit
            touched = False
            for i, (k, nx, ny, nz, raw) in enumerate(lit):
                x, y, z = verts[i * 3], verts[i * 3 + 1], verts[i * 3 + 2]
                if (light.x - x) ** 2 + (light.y - y) ** 2 + (light.z - z) ** 2 >= r2:
                    continue
                _shine(light, raw, x, y, z, nx, ny, nz)
                colors[i * 3 : i * 3 + 3] = [min(max(ch * k, 0.0), 1.0) for ch in raw]
                touched = True
            if touched:
                changed.add(tex)
        return changed

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
        glow = tile.floor_tex in GLOWING_FLOORS
        self._horizontal(tile.floor_tex, x0, z0, tile.floor, 1, 0.85 if tile.liquid else 1.0, glow=glow)
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

    def _horizontal(self, tex, x0, z0, y, up, shade, glow=False):
        """Floor (up = 1) or ceiling (up = -1) of one tile, split into SEG squares. A glowing floor
        (lava) ignores the light and shows at full brightness."""
        n = rround(T / SEG)
        for i in range(n):
            for j in range(n):
                ax = x0 + i * SEG
                az = z0 + j * SEG
                pts = [(ax, y, az), (ax, y, az + SEG), (ax + SEG, y, az + SEG), (ax + SEG, y, az)]
                uvs = [(p[0] / T, p[2] / T) for p in pts]
                self._quad(tex, pts, uvs, (0.0, float(up), 0.0), shade, glow=glow)

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

    def _quad(self, tex, pts, uvs, normal, shade, ao_floor=None, glow=False):
        a, b, c = pts[0], pts[1], pts[2]
        if _dot(_cross(_sub(b, a), _sub(c, a)), normal) < 0:
            pts = pts[::-1]
            uvs = uvs[::-1]
        batch = self.batches[tex]
        colors = []
        lit = []
        for p in pts:
            k = shade
            if ao_floor is not None:
                k *= 0.7 + 0.3 * min((p[1] - ao_floor) / 0.8, 1.0)
            raw = [1.0, 1.0, 1.0] if glow else self.light_at(p[0], p[1], p[2], *normal)
            colors.append([min(max(ch * k, 0.0), 1.0) for ch in raw])
            lit.append((k, *normal, raw))
        for i in (0, 1, 2, 0, 2, 3):
            batch.verts.extend(pts[i])
            batch.uvs.extend(uvs[i])
            batch.colors.extend(colors[i])
            batch.lit.append((lit[i][0], *lit[i][1:4], list(lit[i][4])))
