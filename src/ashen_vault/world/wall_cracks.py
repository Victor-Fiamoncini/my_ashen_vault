"""Great cracks down the tall walls of a cavern (`dress=cracks` in a wall's legend; a wall may carry more
than one dressing, `dress=rampart,cracks`): along every straight run of faces a wall turns to open
ground, rising at least `MIN_HEIGHT` above it, long branching fissures are split into the stone
(`sunken_models.wall_crack`), a few on each big face, spaced apart. They are laid out here from the map
alone, so no marker need be placed for them, and the same map always cracks the same way.

Pure: `World` turns each crack into a static `wall_crack` prop."""

import math
import random
from dataclasses import dataclass

from ashen_vault.world.tile_map import TileMap

T = TileMap.TILE
DRESS = "cracks"
MIN_HEIGHT = 6.0  # metres of wall over the ground it faces, at the least, to carry a crack
MAX_SPAN = 46.0  # how far down from its top a face is cracked at most (a face over the chasm drops on)
# A map may crack its walls less far down (`[meta] crack_span = <m>`): Vesperholm's, whose faces drop
# into the gorge far below where anyone looks, crack only near their tops, where they are seen.
MIN_RUN = 3  # tiles of straight face, unbroken, that a run must have to carry a crack
EVERY = 10.0  # metres of run per crack, about
MIN_GAP = 6.0  # metres between the middles of two cracks on one run, at the least
END_CLEAR = 2.0  # metres a crack's middle keeps from its run's ends
MAX_REACH = 2.4  # metres a crack may wander to either side of its middle
MAX_CRACKS = 90  # on the whole map: the tallest faces keep theirs
SEEP = 0.2  # the share of cracks the mortar-light seeps faintly through
FACES = ((1, 0), (-1, 0), (0, 1), (0, -1))  # from the wall toward the open ground


@dataclass(frozen=True)
class Crack:
    tx: int  # the wall tile its middle is on
    tz: int
    dx: int  # toward the open ground it faces
    dz: int
    x: float  # its middle on the face, at its foot
    y: float
    z: float
    yaw: float  # local +X out of the wall
    height: float  # from its foot up to its head
    reach: float  # how far it may wander to either side along the face
    seed: int
    seep: bool  # the faint teal of the mortar-light in it


def dressed(tile, name=DRESS):
    """Whether a tile's `dress=` (one value, or several joined by commas) names `name`."""
    return bool(tile.dress) and name in tile.dress.split(",")


def _faces(map_, clear):
    """{(tx, tz, dx, dz): (top, base)} of every dressed wall face that turns to open ground."""
    taken = {(e.tx, e.tz) for e in map_.entities}
    span = min(MAX_SPAN, float(map_.meta.get("crack_span", MAX_SPAN)))
    out = {}
    for tx, tz, tile in map_.each_tile():
        if not tile.solid or not dressed(tile) or (tx, tz) in taken:
            continue
        for dx, dz in FACES:
            ox, oz = tx + dx, tz + dz
            ground = map_[ox, oz]
            if ground.solid or ground.ceil is not None or (ox, oz) in clear:
                continue
            out[(tx, tz, dx, dz)] = (tile.top, max(ground.floor, tile.top - span))
    return out


def _runs(faces):
    """Straight runs of faces turned the same way, unbroken and of one top, each in order along it."""
    runs = []
    seen = set()
    for key in sorted(faces):
        if key in seen:
            continue
        tx, tz, dx, dz = key
        ax, az = abs(dz), abs(dx)  # along the run
        while (tx - ax, tz - az, dx, dz) in faces and faces[(tx - ax, tz - az, dx, dz)][0] == faces[key][0]:
            tx, tz = tx - ax, tz - az
        run = []
        while (tx, tz, dx, dz) in faces and faces[(tx, tz, dx, dz)][0] == faces[key][0]:
            run.append((tx, tz, dx, dz))
            tx, tz = tx + ax, tz + az
        seen.update(run)
        runs.append(run)
    return runs


def _slots(length, rng):
    """Where along a run of `length` metres its cracks' middles go: evenly, each jittered within its
    share, never nearer than MIN_GAP to the next nor END_CLEAR to an end."""
    span = length - 2 * END_CLEAR
    count = min(max(1, round(length / EVERY)), int(span // MIN_GAP) + 1)
    share = span / count
    slack = max(0.0, (share - MIN_GAP) / 2) if count > 1 else share / 2
    return [END_CLEAR + share * (i + 0.5) + rng.uniform(-slack, slack) for i in range(count)]


def cracks(map_, clear=frozenset()):
    """Every crack down the map's dressed walls. `clear` holds open tiles whose face must stay bare (a
    door or gate stands there, a lift rides there, or something already hangs on the wall)."""
    faces = _faces(map_, clear)
    out = []
    for run in _runs(faces):
        if len(run) < MIN_RUN:
            continue
        tx0, tz0, dx, dz = run[0]
        ax, az = abs(dz), abs(dx)
        rng = random.Random(tx0 * 7919 + tz0 * 104729 + dx * 13 + dz * 31 + len(run) * 3)
        length = len(run) * T
        top = faces[run[0]][0]
        for along in _slots(length, rng):
            reach = min(MAX_REACH, along - 0.6, length - along - 0.6)
            near = [faces[f][1] for i, f in enumerate(run) if abs((i + 0.5) * T - along) < reach + T / 2]
            base = max(near)  # its foot clears the highest ground it spreads over
            height = top - base
            if height < MIN_HEIGHT:
                continue
            span = min(height, max(MIN_HEIGHT * 0.8, height * rng.uniform(0.45, 0.85)))
            foot = base + (height - span) * rng.uniform(0.0, 0.6) ** 1.5  # most rise from near the ground
            tx, tz, _, _ = run[min(int(along // T), len(run) - 1)]
            cx, cz = TileMap.center(tx0, tz0)
            off = along - T / 2  # from the first face's middle along the run
            out.append(
                Crack(
                    tx=tx,
                    tz=tz,
                    dx=dx,
                    dz=dz,
                    x=cx + dx * T / 2 + ax * off,
                    y=foot,
                    z=cz + dz * T / 2 + az * off,
                    yaw=math.atan2(dz, dx),
                    height=round(span, 2),
                    reach=round(reach, 2),
                    seed=rng.randrange(1 << 16),
                    seep=rng.random() < SEEP,
                )
            )
    if len(out) > MAX_CRACKS:
        keep = sorted(out, key=lambda c: (-c.height, c.tx, c.tz, c.dx, c.dz, c.x, c.z))[:MAX_CRACKS]
        keep = set(keep)
        out = [c for c in out if c in keep]
    return out
