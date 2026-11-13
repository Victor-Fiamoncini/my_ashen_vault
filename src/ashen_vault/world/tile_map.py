import math
from dataclasses import dataclass, field


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
    # Hazards: HP lost per tick while standing here, a current (m/s along x, z) that pushes
    # bodies, a walk-speed multiplier (sucking mud), and a sheer drop (a ravine) you fall into.
    hurt: int = 0
    flow: tuple[float, float] | None = None
    slow: float = 1.0
    pit: bool = False

    @property
    def hazardous(self):
        return self.liquid or self.pit or self.hurt > 0 or self.flow is not None

    @property
    def needs_footing(self):
        """Water and chasms: only somewhere to stand (a raft, a ledge) lets you onto them."""
        return self.liquid or self.pit

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
        tx, tz = key
        if tx < 0 or tz < 0 or tx >= self.width or tz >= self.depth:
            return self._edge
        return self._tiles[tz * self.width + tx]

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
