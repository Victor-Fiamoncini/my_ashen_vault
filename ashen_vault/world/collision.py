"""Grid collision for circles moving over tiles with floor heights."""
import math

from ashen_vault.world.tile_map import TileMap

STEP_HEIGHT = 0.6
BODY_HEIGHT = 1.7


def passable(map_, tx, tz, from_floor, blocked=None):
    """Can a body standing at `from_floor` occupy tile (tx, tz)?
    `blocked` is an optional callable for dynamic blockers such as closed doors."""
    tile = map_[tx, tz]
    if not tile.walkable:
        return False
    if tile.floor - from_floor > STEP_HEIGHT:
        return False
    if tile.ceil is not None and tile.ceil - tile.floor < BODY_HEIGHT:
        return False
    if blocked and blocked(tx, tz):
        return False
    return True


def move(map_, x, z, dx, dz, radius, blocked=None):
    """Moves a circle by (dx, dz), sliding along blocked tiles axis by axis. Returns (x, z)."""
    from_floor = map_.floor_at(x, z)
    x = _slide(map_, x, z, dx, 0, radius, from_floor, blocked)[0]
    z = _slide(map_, x, z, 0, dz, radius, from_floor, blocked)[1]
    return x, z


def _slide(map_, x, z, dx, dz, radius, from_floor, blocked):
    nx = x + dx
    nz = z + dz
    home = (TileMap.tile_coord(x), TileMap.tile_coord(z))
    if circle_clear(map_, nx, nz, radius, from_floor, blocked, home):
        return nx, nz

    t = TileMap.TILE
    eps = 0.001
    tc = TileMap.tile_coord
    if dx != 0:
        nx = ((tc(x + radius) + 1) * t - radius - eps) if dx > 0 else (tc(x - radius) * t + radius + eps)
        if not circle_clear(map_, nx, nz, radius, from_floor, blocked, home):
            nx = x
    else:
        nz = ((tc(z + radius) + 1) * t - radius - eps) if dz > 0 else (tc(z - radius) * t + radius + eps)
        if not circle_clear(map_, nx, nz, radius, from_floor, blocked, home):
            nz = z
    return nx, nz


def circle_clear(map_, x, z, radius, from_floor, blocked, home=None):
    """Treats the circle as its bounding box against the tile grid.
    The tile we started in never counts as blocking, so a body can't get trapped."""
    tc = TileMap.tile_coord
    for tx in range(tc(x - radius), tc(x + radius) + 1):
        for tz in range(tc(z - radius), tc(z + radius) + 1):
            if (tx, tz) != home and not passable(map_, tx, tz, from_floor, blocked):
                return False
    return True


def line_of_sight(map_, ax, az, bx, bz, eye=1.4, blocked=None):
    """True if nothing solid lies between two points (eye-level sight line)."""
    dist = math.hypot(bx - ax, bz - az)
    steps = math.ceil(dist / 0.25)
    eye_y = map_.floor_at(ax, az) + eye
    for i in range(1, steps):
        t = i / steps
        px = ax + (bx - ax) * t
        pz = az + (bz - az) * t
        tx = TileMap.tile_coord(px)
        tz = TileMap.tile_coord(pz)
        tile = map_[tx, tz]
        if tile.solid:
            return False
        if tile.floor > eye_y or (tile.ceil is not None and tile.ceil < eye_y - 0.5):
            return False
        if blocked and blocked(tx, tz):
            return False
    return True


def separate(ax, az, ar, bx, bz, br):
    """Pushes circle a out of circle b; returns the corrected (x, z) for a."""
    dx = ax - bx
    dz = az - bz
    d = math.hypot(dx, dz)
    mn = ar + br
    if d >= mn:
        return ax, az
    if d < 1e-5:
        return ax + mn, az
    push = (mn - d) / d
    return ax + dx * push, az + dz * push
