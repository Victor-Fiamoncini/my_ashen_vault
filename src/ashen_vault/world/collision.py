"""Grid collision for circles moving over tiles with floor heights."""

import math

from ashen_vault.world.tile_map import TileMap

STEP_HEIGHT = 0.6
BODY_HEIGHT = 1.7


def passable(map_, tx, tz, from_floor, blocked=None, floating=None):
    """Can a body standing at `from_floor` occupy tile (tx, tz)?
    `blocked` is an optional callable for dynamic blockers such as closed doors; `floating` says
    whether something you can stand on (a raft, a plank, a ledge) spans a water or chasm tile."""
    tile = map_[tx, tz]
    if tile.needs_footing:
        if not (floating and floating(tx, tz)):
            return False
    elif not tile.walkable:
        return False
    if tile.floor - from_floor > STEP_HEIGHT:
        return False
    if tile.ceil is not None and tile.ceil - tile.floor < BODY_HEIGHT:
        return False
    return not (blocked and blocked(tx, tz))


def move(map_, x, z, dx, dz, radius, blocked=None, floating=None, ground=None):
    """Moves a circle by (dx, dz), sliding along blocked tiles axis by axis. Returns (x, z).
    `ground(x, z)` gives the height you stand at when it is not the tile's floor (a ledge's deck)."""
    from_floor = ground(x, z) if ground else map_.floor_at(x, z)
    x = _slide(map_, x, z, dx, 0, radius, from_floor, blocked, floating)[0]
    z = _slide(map_, x, z, 0, dz, radius, from_floor, blocked, floating)[1]
    return x, z


def _slide(map_, x, z, dx, dz, radius, from_floor, blocked, floating=None):
    nx = x + dx
    nz = z + dz
    home = (TileMap.tile_coord(x), TileMap.tile_coord(z))
    if circle_clear(map_, nx, nz, radius, from_floor, blocked, home, floating):
        return nx, nz

    t = TileMap.TILE
    eps = 0.001
    tc = TileMap.tile_coord
    if dx != 0:
        nx = ((tc(x + radius) + 1) * t - radius - eps) if dx > 0 else (tc(x - radius) * t + radius + eps)
        if not circle_clear(map_, nx, nz, radius, from_floor, blocked, home, floating):
            nx = _closest(map_, x, z, dx, 0, radius, from_floor, blocked, home, floating)[0]
    else:
        nz = ((tc(z + radius) + 1) * t - radius - eps) if dz > 0 else (tc(z - radius) * t + radius + eps)
        if not circle_clear(map_, nx, nz, radius, from_floor, blocked, home, floating):
            nz = _closest(map_, x, z, 0, dz, radius, from_floor, blocked, home, floating)[1]
    return nx, nz


def _closest(map_, x, z, dx, dz, radius, from_floor, blocked, home, floating, steps=6):
    """How far along (dx, dz) the circle gets before it touches something that does not lie on a tile
    edge (a thin wall's slab): halves the step until it fits."""
    lo, hi = 0.0, 1.0
    for _ in range(steps):
        mid = (lo + hi) / 2
        if circle_clear(map_, x + dx * mid, z + dz * mid, radius, from_floor, blocked, home, floating):
            lo = mid
        else:
            hi = mid
    return x + dx * lo, z + dz * lo


def circle_clear(map_, x, z, radius, from_floor, blocked, home=None, floating=None):
    """Treats the circle as its bounding box against the tile grid.
    The tile we started in never counts as blocking, so a body can't get trapped."""
    tc = TileMap.tile_coord
    for tx in range(tc(x - radius), tc(x + radius) + 1):
        for tz in range(tc(z - radius), tc(z + radius) + 1):
            if map_[tx, tz].thin:
                if not _thin_clear(map_, tx, tz, x, z, radius, from_floor, blocked, home, floating):
                    return False
            elif (tx, tz) != home and not passable(map_, tx, tz, from_floor, blocked, floating):
                return False
    return True


def _thin_clear(map_, tx, tz, x, z, radius, from_floor, blocked, home, floating):
    """A circle over a thin wall's tile: clear of the slab, and every margin it touches is ground it
    could stand on (the tile lending that margin is). The slab always blocks, even for a body that
    started on this tile, since you can stand in its margins."""
    lay = map_.layout(tx, tz)
    for (i, j), owner in lay.cells.items():
        x0, z0, x1, z1 = lay.rect(i, j)
        if x + radius <= x0 or x - radius >= x1 or z + radius <= z0 or z - radius >= z1:
            continue
        if owner is None:
            return False
        if owner == home or (tx, tz) == home:
            continue
        if not passable(map_, owner[0], owner[1], from_floor, blocked, floating):
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
        tile = map_.tile_at(px, pz)
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
