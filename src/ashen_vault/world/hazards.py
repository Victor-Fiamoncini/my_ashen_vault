"""Level hazards: platforms floating on water (drifting rafts, rotting planks), river currents,
thorn floors and falls into deep water. Pure logic; the World feeds it the player and draws it."""

import math
from dataclasses import dataclass

from ashen_vault.util import rround
from ashen_vault.world import collision
from ashen_vault.world.tile_map import TileMap

PLATFORM_KINDS = ("raft", "plank")
HALF = 0.95  # half the side of a platform's square deck, in metres
GRACE = 0.15  # how far past the deck's edge you still count as standing on it
DECK = 0.3  # deck height above the water tile's floor
RAFT_PAUSE = 1.6  # seconds a raft waits at each landing
PLANK_CREAK = 1.1  # seconds a rotten plank holds your weight
PLANK_SUNK = 3.5  # seconds before a sunk plank bobs back up
THORN_TICK = 0.6  # seconds between thorn pricks
FALL_FRAC = 0.15  # share of max HP a fall into the river costs


@dataclass(eq=False)
class Platform:
    kind: str
    x: float
    z: float
    deck: float
    ax: float = 0.0
    az: float = 0.0
    bx: float = 0.0
    bz: float = 0.0
    speed: float = 1.0
    t: float = 0.0
    load_t: float = 0.0  # plank: how long it has carried you
    sunk_t: float = 0.0  # plank: > 0 while under water
    dx: float = 0.0  # movement over the last update
    dz: float = 0.0

    @property
    def afloat(self):
        return self.sunk_t <= 0

    def covers(self, x, z):
        """Is (x, z) standing on the deck? A little lenient, so stepping on from a bank is safe."""
        reach = HALF + GRACE
        return self.afloat and abs(x - self.x) < reach and abs(z - self.z) < reach

    def floats_on(self, tx, tz):
        """True when the deck overlaps tile (tx, tz) enough to step onto."""
        if not self.afloat:
            return False
        t = TileMap.TILE
        ox = min(self.x + HALF, (tx + 1) * t) - max(self.x - HALF, tx * t)
        oz = min(self.z + HALF, (tz + 1) * t) - max(self.z - HALF, tz * t)
        return ox > 0.3 and oz > 0.3

    @property
    def creaking(self):
        """0..1 how close a plank is to giving way (for the shake animation)."""
        return min(self.load_t / PLANK_CREAK, 1.0)

    @property
    def sink(self):
        """How far under the surface a sunk plank sits, easing back up near the end."""
        if self.afloat:
            return 0.0
        return 0.6 * min(self.sunk_t / 0.6, 1.0)

    def update(self, dt, loaded):
        ox, oz = self.x, self.z
        if self.kind == "raft":
            self._drift(dt)
        else:
            self._rot(dt, loaded)
        self.dx = self.x - ox
        self.dz = self.z - oz

    def _drift(self, dt):
        """Ferries back and forth between its two landings, pausing at each."""
        dist = math.hypot(self.bx - self.ax, self.bz - self.az)
        travel = dist / self.speed if self.speed > 0 else 0
        cycle = 2 * (travel + RAFT_PAUSE)
        if cycle <= 0:
            return
        self.t = (self.t + dt) % cycle
        p = self.t
        if p < RAFT_PAUSE:
            k = 0.0
        elif p < RAFT_PAUSE + travel:
            k = (p - RAFT_PAUSE) / travel
        elif p < 2 * RAFT_PAUSE + travel:
            k = 1.0
        else:
            k = 1 - (p - 2 * RAFT_PAUSE - travel) / travel
        k = k * k * (3 - 2 * k)  # ease in and out at the landings
        self.x = self.ax + (self.bx - self.ax) * k
        self.z = self.az + (self.bz - self.az) * k

    def _rot(self, dt, loaded):
        if not self.afloat:
            self.sunk_t = max(self.sunk_t - dt, 0.0)
            return
        if loaded:
            self.load_t += dt
            if self.load_t >= PLANK_CREAK:
                self.load_t = 0.0
                self.sunk_t = PLANK_SUNK
        else:
            self.load_t = max(self.load_t - dt * 0.5, 0.0)


def build_platforms(map_):
    """Platforms for every `raft` and `plank` entity. A raft's `to=tx,tz` is its far landing."""
    out = []
    for spec in map_.entities:
        if spec.kind not in PLATFORM_KINDS:
            continue
        x, z = TileMap.center(spec.tx, spec.tz)
        deck = map_[spec.tx, spec.tz].floor + DECK
        p = Platform(kind=spec.kind, x=x, z=z, deck=deck, ax=x, az=z, bx=x, bz=z)
        if spec.kind == "raft":
            tx, tz = (int(v) for v in spec.props.get("to", f"{spec.tx},{spec.tz}").split(","))
            p.bx, p.bz = TileMap.center(tx, tz)
            p.speed = float(spec.props.get("speed", "1.0"))
            p.t = float(spec.props.get("phase", "0"))
        out.append(p)
    return out


class Hazards:
    """What the river and the undergrowth do to the player each frame.
    `body` needs x, z, y and RADIUS; damage goes through the `hurt(dmg, source)` callback."""

    def __init__(self, map_, platforms=None):
        self.map = map_
        self.platforms = build_platforms(map_) if platforms is None else platforms
        self._thorn_t = 0.0
        self.safe = None  # last solid ground the player stood on: (x, z)
        self.under = None  # the platform the player stands on

    def floating(self, tx, tz):
        return any(p.floats_on(tx, tz) for p in self.platforms)

    def support(self, x, z):
        return next((p for p in self.platforms if p.covers(x, z)), None)

    def floor(self, x, z):
        """Height the player stands at: a platform's deck, or the tile's floor."""
        p = self.support(x, z)
        if p:
            return p.deck - p.sink
        return self.map.floor_at(x, z)

    def update(self, dt, body, hurt, blocked=None):
        """Moves platforms, carries the player, applies currents and thorns, and catches falls.
        Returns "fell" when the player went into the water this frame, else None."""
        under = self.support(body.x, body.z)
        for p in self.platforms:
            p.update(dt, loaded=p is under)
        if under is not None and under.afloat:
            body.x += under.dx
            body.z += under.dz

        tile = self.map.tile_at(body.x, body.z)
        if tile.flow and self.support(body.x, body.z) is None:
            fx, fz = tile.flow
            # The current can drag you off the ford into deep water, so water does not stop it.
            body.x, body.z = collision.move(
                self.map, body.x, body.z, fx * dt, fz * dt, body.RADIUS, blocked=blocked, floating=_always
            )
            tile = self.map.tile_at(body.x, body.z)

        self.under = self.support(body.x, body.z)
        if tile.liquid and self.under is None:
            return self._fall(body, hurt)
        if tile.hurt:
            self._thorn_t -= dt
            if self._thorn_t <= 0:
                self._thorn_t = THORN_TICK
                hurt(tile.hurt, "Thorns")
        else:
            self._thorn_t = 0.0
        if self.under is None and tile.walkable and not tile.hazardous:
            # The middle of the tile, so a fall never puts you back on the brink.
            self.safe = TileMap.center(TileMap.tile_coord(body.x), TileMap.tile_coord(body.z))
        return None

    def _fall(self, body, hurt):
        hurt(max(rround(body.stats.max_hp * FALL_FRAC), 6), "The river")
        if self.safe is None:
            sx, sz = self.map.meta["start"][:2]
            self.safe = TileMap.center(int(sx), int(sz))
        body.x, body.z = self.safe
        body.y = self.map.floor_at(body.x, body.z)
        return "fell"


def _always(_tx, _tz):
    return True
