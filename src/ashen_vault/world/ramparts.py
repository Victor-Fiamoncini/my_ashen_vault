"""The dressing of a town's great walls (`dress=rampart` in a wall's legend): along every face a wall
turns to open ground, a bay of carved stone (`town_models.rampart_bay`), clusters of engaged columns
every few metres with tall blind arches between them, a stepped plinth at the foot and a crenellated
parapet on top. The bays are laid out here from the map alone, so no marker need be placed for them.

Pure: `World` turns each bay into a static `rampart_bay` prop."""

import math
from dataclasses import dataclass

from ashen_vault.world.tile_map import TileMap

T = TileMap.TILE
DRESS = "rampart"
MIN_HEIGHT = 2.5  # metres of wall over the ground it faces, at the least, to carry a bay
PIER_EVERY = 3  # a cluster of columns every this many tiles along a run; arches between
TOWER_CLEAR = 1.0  # metres past a wall tower's drum that stay bare
FACES = ((1, 0), (-1, 0), (0, 1), (0, -1))  # from the wall toward the open ground


@dataclass(frozen=True)
class Bay:
    tx: int  # the wall tile
    tz: int
    dx: int  # toward the open ground it faces
    dz: int
    x: float  # the middle of the face, at the foot of the wall
    y: float
    z: float
    yaw: float  # local +X out of the wall
    kind: str  # "pier" or "arch"
    height: float  # from the ground it faces to the wall's top


def _towers(map_):
    """(x, z, radius) of every wall tower's drum."""
    out = []
    for e in map_.entities:
        if e.kind != "wall_tower":
            continue
        x, z = TileMap.center(e.tx, e.tz)
        sx, sz = (float(v) for v in e.props.get("shift", "0,0").split(","))
        out.append((x + sx, z + sz, float(e.props.get("radius", "2.2"))))
    return out


def _faces(map_, clear):
    """{(tx, tz, dx, dz): height} of every dressed wall face that can carry a bay."""
    towers = _towers(map_)
    taken = {(e.tx, e.tz) for e in map_.entities}
    out = {}
    for tx, tz, tile in map_.each_tile():
        if tile.dress != DRESS or not tile.solid or (tx, tz) in taken:
            continue
        for dx, dz in FACES:
            ox, oz = tx + dx, tz + dz
            ground = map_[ox, oz]
            if ground.solid or ground.ceil is not None or (ox, oz) in clear:
                continue
            height = tile.top - ground.floor
            if height < MIN_HEIGHT:
                continue
            cx, cz = TileMap.center(tx, tz)
            fx, fz = cx + dx * T / 2, cz + dz * T / 2
            if any(math.hypot(fx - x, fz - z) < r + T / 2 + TOWER_CLEAR for x, z, r in towers):
                continue
            out[(tx, tz, dx, dz)] = height
    return out


def bays(map_, clear=frozenset()):
    """Every bay along the map's dressed walls. `clear` holds open tiles whose face must stay bare
    (a gate stands there, or something already hangs on the wall)."""
    faces = _faces(map_, clear)
    out = []
    for (tx, tz, dx, dz), height in sorted(faces.items()):
        ax, az = abs(dz), abs(dx)  # along the run
        index = tx if dz else tz
        ends = (tx - ax, tz - az, dx, dz) not in faces or (tx + ax, tz + az, dx, dz) not in faces
        kind = "pier" if ends or index % PIER_EVERY == 0 else "arch"
        cx, cz = TileMap.center(tx, tz)
        ground = map_[tx + dx, tz + dz]
        out.append(
            Bay(
                tx=tx,
                tz=tz,
                dx=dx,
                dz=dz,
                x=cx + dx * T / 2,
                y=ground.floor,
                z=cz + dz * T / 2,
                yaw=math.atan2(dz, dx),
                kind=kind,
                height=height,
            )
        )
    return out
