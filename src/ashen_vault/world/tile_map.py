import math
from dataclasses import dataclass, field

from ashen_vault.util import rround

SEAT_DEPTH = 0.6  # how far a chest is pushed back from its tile's centre toward the wall behind it


@dataclass(eq=False)
class Tile:
    """One grid cell. Heights are in meters; ceil None means open sky."""

    solid: bool = False
    walkable: bool = False
    floor: float = 0.0
    ceil: float | None = None
    top: float | None = None
    floor_tex: str | None = None
    wall_tex: str | None = None
    ceil_tex: str | None = None
    liquid: bool = False
    pit: bool = False  # falling in hurts and sends you back to solid ground
    # Hazards: HP lost per tick while standing here, a current (m/s along x, z) that pushes
    # bodies, a walk-speed multiplier (sucking mud), and a sheer chasm (a ravine) that only a
    # ledge or a raft lets you onto.
    hurt: int = 0
    flow: tuple[float, float] | None = None
    slow: float = 1.0
    chasm: bool = False
    # How much of the map's ambient light this tile loses (0 = none, 1 = pitch black): caves and
    # hollows where only torches, glowing fungus and your own light show the way.
    dark: float = 0.0
    # Molten rock: it reads as a pit (you can walk in), but it sears whoever touches it and hauls
    # them back to the last solid ground. It also glows.
    lava: bool = False

    @property
    def hazardous(self):
        return self.liquid or self.pit or self.chasm or self.hurt > 0 or self.flow is not None

    @property
    def needs_footing(self):
        """Water and chasms: only somewhere to stand (a raft, a ledge) lets you onto them."""
        return self.liquid or self.chasm

    @property
    def open_sky(self):
        return self.ceil is None


@dataclass
class EntitySpec:
    """Marker placed in the grid, resolved to an entity at load time."""

    kind: str
    tx: int
    tz: int
    props: dict = field(default_factory=dict)
    marker: str | None = None


class TileMap:
    TILE = 2.0

    def __init__(self, name, width, depth, tiles, meta, entities):
        self.name = name
        self.width = width
        self.depth = depth
        self._tiles = tiles
        self._overrides = {}
        self.meta = meta
        self.entities = entities
        self._edge = Tile(
            solid=True,
            walkable=False,
            floor=0.0,
            ceil=None,
            top=meta.get("edge_top", 4.0),
            wall_tex=meta.get("edge_tex", "stone_brick"),
        )

    def __getitem__(self, key):
        tile = self._overrides.get(key)
        if tile is not None:
            return tile
        tx, tz = key
        if tx < 0 or tz < 0 or tx >= self.width or tz >= self.depth:
            return self._edge
        return self._tiles[tz * self.width + tx]

    def set_override(self, key, tile):
        """Swaps the tile at `key` (tx, tz) at runtime, e.g. a floor that crumbles; None restores it."""
        if tile is None:
            self._overrides.pop(key, None)
        else:
            self._overrides[key] = tile

    # yaw for each direction, in the order ties are broken
    FACINGS = (((1, 0), 0.0), ((0, 1), math.pi / 2), ((-1, 0), math.pi), ((0, -1), -math.pi / 2))

    def open_facing(self, tx, tz, reach=3):
        """Yaw pointing toward the most open direction from (tx, tz): how a chest set against a wall
        or tucked into a corner should face."""
        best_yaw, best = 0.0, -1
        for (dx, dz), yaw in self.FACINGS:
            n = 0
            while n < reach and self._standable(tx + dx * (n + 1), tz + dz * (n + 1)):
                n += 1
            if n > best:
                best_yaw, best = yaw, n
        return best_yaw

    WALL_CHECK = (((-1, 0), 0.0), ((1, 0), math.pi), ((0, -1), math.pi / 2), ((0, 1), -math.pi / 2))

    def wall_yaw(self, tx, tz):
        """Yaw facing out of the first solid wall beside (tx, tz), for things hung on walls
        (sconces, banners, shackles); None if the tile stands free."""
        for (dx, dz), yaw in self.WALL_CHECK:
            if self[tx + dx, tz + dz].solid:
                return yaw
        return None

    def seated(self, tx, tz, yaw, depth=SEAT_DEPTH):
        """Where something facing `yaw` on (tx, tz) stands once pushed back against the wall behind
        it (a chest's back to the stones), or the tile's centre if nothing solid stands behind."""
        x, z = self.center(tx, tz)
        bx, bz = -math.cos(yaw), -math.sin(yaw)
        if not self[tx + rround(bx), tz + rround(bz)].solid:
            return x, z
        return x + bx * depth, z + bz * depth

    def _standable(self, tx, tz):
        tile = self[tx, tz]
        return tile.walkable and not tile.pit

    def each_tile(self):
        for tz in range(self.depth):
            for tx in range(self.width):
                yield tx, tz, self[tx, tz]

    @staticmethod
    def tile_coord(world):
        return math.floor(world / TileMap.TILE)

    def tile_at(self, wx, wz):
        return self[TileMap.tile_coord(wx), TileMap.tile_coord(wz)]

    def floor_at(self, wx, wz):
        return self.tile_at(wx, wz).floor

    @staticmethod
    def center(tx, tz):
        return ((tx + 0.5) * TileMap.TILE, (tz + 0.5) * TileMap.TILE)
