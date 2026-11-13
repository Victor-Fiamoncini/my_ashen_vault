"""Terrain hazards: platforms you stand on over water or a chasm (drifting rafts, rotting planks,
crumbling ledges, rotten floorboards, chain lifts up and down a shaft), river currents, thorn floors, rolling logs, spore pods, falls
into deep water or a ravine, and hard landings from high drops.
Pure logic; the World feeds it the player and draws it."""

import math
from dataclasses import dataclass, field

from ashen_vault.util import rround
from ashen_vault.world import collision
from ashen_vault.world.tile_map import TileMap

PLATFORM_KINDS = ("raft", "plank", "ledge", "boards", "lift")
TERRAIN_KINDS = (*PLATFORM_KINDS, "log_chute", "spore_pod")
HALF = 0.95  # half the side of a platform's square deck, in metres
GRACE = 0.15  # how far past the deck's edge you still count as standing on it
DECK = 0.3  # deck height above the water tile's floor (when the map gives no `deck=`)
RAFT_PAUSE = 1.6  # seconds a raft waits at each landing
PLANK_CREAK = 1.1  # seconds a rotten plank holds your weight
PLANK_SUNK = 3.5  # seconds before a sunk plank bobs back up
LEDGE_CREAK = 1.0  # seconds a cracked ledge holds before it breaks off
LEDGE_GONE = 4.0  # seconds before the ledge's spot firms up again
BOARDS_CREAK = 0.45  # rotten floorboards give way almost at once, and for good
DROP_TIME = 0.35  # seconds a broken platform takes to fall away
THORN_TICK = 0.6  # seconds between thorn pricks
FALL_FRAC = 0.15  # share of max HP a fall into the river or the ravine costs
FALL_SAFE = 1.8  # metres you can drop without getting hurt
FALL_PER_M = 10  # HP per metre dropped past FALL_SAFE
LOG_R = 0.35  # rolling log radius
LOG_HALF = 0.85  # half its length, across the lane
LOG_DAMAGE = 14
LOG_KNOCK = 1.8  # metres a log shoves you down the slope
LOG_FALL = 6.0  # m/s a log drops when it rolls off a step or into the chasm
LOG_WARN = 0.8  # seconds between stepping onto the slope and the first log tipping off the pile
PILE_BACK = 0.1  # metres the log rack sits behind its tile centre (away from the slope)
# Where each log lies in the rack, as (z, y) with +z downhill: a 4-3-2-1 pyramid, bottom row
# first. The top log is the first to go.
PILE_SLOTS = tuple(
    ((k - (n - 1) / 2) * 0.56, 0.42 + row * 0.49) for row, n in enumerate((4, 3, 2, 1)) for k in range(n)
)
LOG_STOCK = len(PILE_SLOTS)
SLOPE_REACH = 2.5  # how far either side of the lane counts as "on the slope" (the notches included)
SPORE_TIME = 1.6  # seconds a pod's cloud hangs in the air
SPORE_R = 1.8  # cloud radius
SPORE_LINGER = 1.2  # seconds the spores keep you sluggish after you leave the cloud
SPORE_TICK = 0.8  # seconds between choking coughs
SPORE_DAMAGE = 3
LIFT_SPEED = 1.6  # m/s a lift climbs or sinks at
LIFT_DELAY = 0.7  # seconds you stand on a resting lift before it sets off
LIFT_CALL = 1.0  # seconds you wait at an empty landing before the lift comes for you
CALL_REACH = 3.0  # metres from the shaft's centre that count as waiting at its landing
HEARING = 14.0  # metres within which the player hears a pod burst or a platform give way

# Sounds a platform makes (name, volume): when you first load it, and when it gives way.
CREAK_SOUND = {"plank": ("crack", 0.25), "ledge": ("crack", 0.45), "boards": ("crack", 0.5)}
LIFT_SOUND = {"lift_start": ("chain", 0.9), "lift_stop": ("clunk", 0.9)}
BREAK_SOUND = {"plank": ("splash", 0.7), "ledge": ("door", 0.7), "boards": ("crack", 1.0)}

# How each kind of platform rots: (seconds it bears you, seconds it stays gone, metres it drops).
# None for "gone" means it never comes back; None for the drop means "down to the tile's floor".
ROT = {
    "plank": (PLANK_CREAK, PLANK_SUNK, 0.6),
    "ledge": (LEDGE_CREAK, LEDGE_GONE, 7.0),
    "boards": (BOARDS_CREAK, None, None),
}


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
    load_t: float = 0.0  # how long it has carried you
    sunk_t: float = 0.0  # > 0 while broken or under water
    down_t: float = 0.0  # how long it has been gone
    bottom: float = 0.0  # floor of the tile below
    dx: float = 0.0  # movement over the last update
    dz: float = 0.0
    dy: float = 0.0
    # A lift rides between `low` and `high` in its shaft. `at` is "low"/"high" while it rests there,
    # None while it moves; `going` is +1 up, -1 down. A `locked` lift waits for its lever.
    low: float = 0.0
    high: float = 0.0
    at: str | None = None
    going: int = 0
    wait: float = 0.0
    locked: bool = False
    lever: str | None = None
    nagged: bool = False  # already said it is locked, until you step off
    hold: bool = False  # just arrived: whoever rode it must step off before it goes again

    @property
    def afloat(self):
        return self.sunk_t <= 0

    def covers(self, x, z):
        """Is (x, z) standing on the deck? A little lenient, so stepping on from a bank is safe.
        A lift fills its shaft exactly: standing at the landing's brink is not riding it."""
        reach = TileMap.TILE / 2 if self.kind == "lift" else HALF + GRACE
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
        """0..1 how close it is to giving way (for the shake animation)."""
        if self.kind not in ROT:
            return 0.0
        return min(self.load_t / ROT[self.kind][0], 1.0)

    @property
    def sink(self):
        """How far below its deck a broken platform sits: it drops away, and eases back up near the end."""
        if self.afloat or self.kind not in ROT:
            return 0.0
        depth = ROT[self.kind][2]
        if depth is None:
            depth = self.deck - self.bottom - 0.08
        k = min(self.down_t / DROP_TIME, 1.0)
        if ROT[self.kind][1] is not None:
            k = min(k, self.sunk_t / 0.6)
        return depth * k * k

    def update(self, dt, loaded, call=None):
        """Moves the platform. `call` is the end ("low"/"high") someone waits at for a lift.
        Returns a lift event ("lift_start", "lift_stop", "lift_locked") or None."""
        ox, oz, oy = self.x, self.z, self.deck
        event = None
        if self.kind == "raft":
            self._drift(dt)
        elif self.kind == "lift":
            event = self._lift(dt, loaded, call)
        else:
            self._rot(dt, loaded)
        self.dx = self.x - ox
        self.dz = self.z - oz
        self.dy = self.deck - oy
        return event

    @property
    def moving(self):
        return self.kind == "lift" and self.at is None

    def _lift(self, dt, loaded, call):
        """Rides the shaft. Stand on it and it carries you to the other end; wait at the far landing
        and it comes for you. A locked lift does neither, and says so once."""
        if self.at is None:
            self.deck += self.going * self.speed * dt
            if self.deck >= self.high or self.deck <= self.low:
                self.deck = min(max(self.deck, self.low), self.high)
                self.at = "high" if self.going > 0 else "low"
                self.going = 0
                self.wait = 0.0
                self.hold = True
                return "lift_stop"
            return None
        if not loaded:
            self.hold = False
        other = "low" if self.at == "high" else "high"
        wanted = (loaded and not self.hold) or call == other
        if not wanted:
            self.wait = 0.0
            self.nagged = False
            return None
        if self.locked:
            if self.nagged:
                return None
            self.nagged = True
            return "lift_locked"
        self.wait += dt
        if self.wait < (LIFT_DELAY if loaded else LIFT_CALL):
            return None
        self.at = None
        self.going = 1 if other == "high" else -1
        return "lift_start"

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
        creak, gone, _ = ROT[self.kind]
        if not self.afloat:
            self.down_t += dt
            self.sunk_t = max(self.sunk_t - dt, 0.0)
            return
        if loaded:
            self.load_t += dt
            if self.load_t >= creak:
                self.load_t = 0.0
                self.down_t = 0.0
                self.sunk_t = math.inf if gone is None else gone
        else:
            self.load_t = max(self.load_t - dt * 0.5, 0.0)


@dataclass(eq=False)
class Log:
    x: float
    z: float
    y: float
    dx: float  # unit direction it rolls in
    dz: float
    left: float  # metres still to roll
    spin: float = 0.0
    hit: bool = False


@dataclass(eq=False)
class LogChute:
    """A woodcutters' log pile, roped behind stakes at the top of a slope that runs to `to=tx,tz`.
    While someone climbs the slope the rotten rope lets the logs go one at a time, every `every`
    seconds; it holds `logs=` of them, and once they are gone the slope is safe."""

    x: float
    z: float
    ex: float
    ez: float
    every: float = 3.5
    speed: float = 5.0
    stock: int = LOG_STOCK
    t: float = 0.0
    logs: list = field(default_factory=list)
    stirred: bool = False  # has anyone set it off yet
    active: bool = False  # someone is on the slope right now

    def __post_init__(self):
        self.length = math.hypot(self.ex - self.x, self.ez - self.z)
        self.ux, self.uz = (
            ((self.ex - self.x) / self.length, (self.ez - self.z) / self.length) if self.length else (0, 1)
        )
        self.t = self.every - LOG_WARN

    def on_slope(self, x, z):
        """Below the pile's own tile, along the lane (or in a notch beside it)."""
        rx, rz = x - self.x, z - self.z
        along = rx * self.ux + rz * self.uz
        across = abs(-rx * self.uz + rz * self.ux)
        return TileMap.TILE * 1.5 <= along <= self.length and across <= SLOPE_REACH

    def update(self, dt, floor_at, climber=None):
        """Rolls the logs. `climber` is the (x, z) of whoever might set the pile off. Returns
        "first", "next" or "last" when a log tips off the pile, else None."""
        released = None
        self.active = climber is not None and self.stock > 0 and self.on_slope(*climber)
        if self.active:
            self.t += dt
            if self.t >= self.every:
                self.t = 0.0
                self.stock -= 1
                released = "first" if not self.stirred else "last" if self.stock == 0 else "next"
                self.stirred = True
                # The top log rolls off the rack, over the chock, and drops onto the slope.
                z, y = PILE_SLOTS[self.stock]
                back = PILE_BACK - z
                px, pz = self.x - self.ux * back, self.z - self.uz * back
                y += floor_at(self.x, self.z)
                self.logs.append(Log(px, pz, y, self.ux, self.uz, self.length + back))
        else:
            self.t = self.every - LOG_WARN  # step back on and you get a moment's warning again
        for log in self.logs:
            step = min(self.speed * dt, log.left)
            log.x += log.dx * step
            log.z += log.dz * step
            log.left -= step
            log.spin += step / LOG_R
            ground = floor_at(log.x, log.z)
            log.y = ground if ground >= log.y else max(ground, log.y - LOG_FALL * dt)
        self.logs = [log for log in self.logs if log.left > 0]
        return released

    @staticmethod
    def touches(log, x, z, y, radius):
        """Does a body of `radius` standing at (x, y, z) touch the log?"""
        rx, rz = x - log.x, z - log.z
        along = rx * log.dx + rz * log.dz
        across = -rx * log.dz + rz * log.dx
        return abs(along) < LOG_R + radius and abs(across) < LOG_HALF + radius and abs(y - log.y) < 1.0


@dataclass(eq=False)
class SporePod:
    """A swollen fungus that bursts into a choking cloud every `every` seconds."""

    x: float
    z: float
    y: float
    every: float = 4.0
    t: float = 0.0

    @property
    def cloud(self):
        """0..1 through the burst while the cloud hangs, else None."""
        return self.t / SPORE_TIME if self.t < SPORE_TIME else None

    def update(self, dt):
        self.t = (self.t + dt) % self.every

    def engulfs(self, x, z):
        return self.cloud is not None and math.hypot(x - self.x, z - self.z) < SPORE_R


def _deck(map_, spec):
    if "deck" in spec.props:
        return float(spec.props["deck"])
    return map_[spec.tx, spec.tz].floor + DECK


def build_platforms(map_):
    """Platforms for every raft, plank, ledge and boards entity. A raft's `to=tx,tz` is its far landing;
    `deck=` sets a platform's height (a ledge over a chasm, floorboards over a cellar)."""
    out = []
    for spec in map_.entities:
        if spec.kind not in PLATFORM_KINDS:
            continue
        x, z = TileMap.center(spec.tx, spec.tz)
        bottom = map_[spec.tx, spec.tz].floor
        p = Platform(kind=spec.kind, x=x, z=z, deck=_deck(map_, spec), ax=x, az=z, bx=x, bz=z, bottom=bottom)
        if spec.kind == "lift":
            p.low = bottom
            p.high = float(spec.props.get("top", str(bottom)))
            p.at = "high" if spec.props.get("start") == "top" else "low"
            p.deck = p.high if p.at == "high" else p.low
            p.speed = float(spec.props.get("speed", str(LIFT_SPEED)))
            p.lever = spec.props.get("lever")
            p.locked = p.lever is not None
        elif spec.kind == "raft":
            tx, tz = _coords(spec.props.get("to"), spec.tx, spec.tz)
            p.bx, p.bz = TileMap.center(tx, tz)
            p.speed = float(spec.props.get("speed", "1.0"))
            p.t = float(spec.props.get("phase", "0"))
        out.append(p)
    return out


def build_chutes(map_):
    out = []
    for spec in map_.entities:
        if spec.kind != "log_chute":
            continue
        x, z = TileMap.center(spec.tx, spec.tz)
        ex, ez = TileMap.center(*_coords(spec.props.get("to"), spec.tx, spec.tz))
        out.append(
            LogChute(
                x,
                z,
                ex,
                ez,
                every=float(spec.props.get("every", "3.5")),
                speed=float(spec.props.get("speed", "5")),
                stock=min(int(spec.props.get("logs", str(LOG_STOCK))), LOG_STOCK),
            )
        )
    return out


def build_pods(map_):
    out = []
    for spec in map_.entities:
        if spec.kind != "spore_pod":
            continue
        x, z = TileMap.center(spec.tx, spec.tz)
        out.append(
            SporePod(
                x,
                z,
                map_[spec.tx, spec.tz].floor,
                every=float(spec.props.get("every", "4")),
                t=float(spec.props.get("phase", "0")),
            )
        )
    return out


def _coords(value, tx, tz):
    if not value:
        return tx, tz
    a, b = (int(v) for v in value.split(","))
    return a, b


class Terrain:
    """What the land does to the player each frame.
    `body` needs x, z, y, RADIUS and stats; damage goes through the `hurt(dmg, source)` callback.
    After a fall, `fell_into` says whether it was the "river" or the "ravine"."""

    def __init__(self, map_, platforms=None):
        self.map = map_
        self.platforms = build_platforms(map_) if platforms is None else platforms
        self.chutes = build_chutes(map_)
        self.pods = build_pods(map_)
        self._thorn_t = 0.0
        self._spore_t = 0.0
        self._ground = None  # height stood at last frame, for hard landings
        self._last = None  # (x, z) last frame, to tell a fall from a teleport
        self.safe = None  # last solid ground the player stood on: (x, z)
        self.under = None  # the platform the player stands on
        self.fell_into = None
        self.landed = 0  # metres of the last hard landing
        self.sounds = []  # (name, volume) to play this frame; the World plays and clears them

    @property
    def logs(self):
        return [log for chute in self.chutes for log in chute.logs]

    def floating(self, tx, tz):
        """Can you step onto tile (tx, tz) over water or a chasm? Only where a deck is, and for a
        lift only when its deck is level with you: an empty shaft is a sheer drop or a dead end."""
        return any(p.floats_on(tx, tz) and self._level(p) for p in self.platforms)

    def _level(self, p):
        if p.kind != "lift" or self._ground is None:
            return True
        return abs(p.deck - self._ground) <= collision.STEP_HEIGHT

    def support(self, x, z):
        """The platform under (x, z) that you could be standing on: one you can step onto from the
        height you stood at last frame. Walking beneath a deck (in a cellar under floorboards) never
        lifts you onto it."""
        for p in self.platforms:
            if not p.covers(x, z):
                continue
            if self._ground is None or p.deck - p.sink - self._ground <= collision.STEP_HEIGHT:
                return p
        return None

    def _calls(self, p, body):
        """Which end of a lift's shaft ("low"/"high") the body waits at, if any."""
        if p.covers(body.x, body.z) or math.hypot(body.x - p.x, body.z - p.z) > CALL_REACH:
            return None
        ground = self.map.floor_at(body.x, body.z)
        for end, h in (("low", p.low), ("high", p.high)):
            if abs(ground - h) <= collision.STEP_HEIGHT:
                return end
        return None

    def floor(self, x, z):
        """Height the player stands at: a platform's deck, or the tile's floor."""
        p = self.support(x, z)
        if p:
            return p.deck - p.sink
        return self.map.floor_at(x, z)

    def _move(self, body, dx, dz, blocked):
        """Shoves the body; water and chasms do not stop a shove, so it can tip you in."""
        steps = max(1, math.ceil(math.hypot(dx, dz) / 0.45))
        for _ in range(steps):
            body.x, body.z = collision.move(
                self.map,
                body.x,
                body.z,
                dx / steps,
                dz / steps,
                body.RADIUS,
                blocked=blocked,
                floating=_always,
                ground=self.floor,
            )

    def update(self, dt, body, hurt, blocked=None):
        """Moves platforms, logs and spores, carries the player, applies currents, thorns, logs and
        spores, and catches falls. Returns "fell" when the player went into the water or the ravine,
        "landed" after a hard landing, "log" when a log struck, "logs_first"/"logs_next"/"logs_last"
        when a log tips off a pile, "spores" when a cloud first engulfs, else None."""
        event = None
        self.sounds = []
        under = self.support(body.x, body.z)
        for p in self.platforms:
            was_afloat, was_loaded = p.afloat, p.load_t > 0
            if p.kind == "lift":
                lift_event = p.update(dt, loaded=p is under, call=self._calls(p, body))
                if lift_event == "lift_locked":
                    event = lift_event
                elif lift_event:
                    self._hear(p.x, p.z, body, *LIFT_SOUND[lift_event])
                continue
            p.update(dt, loaded=p is under)
            if p.kind not in ROT:
                continue
            if was_afloat and not p.afloat:
                self._hear(p.x, p.z, body, *BREAK_SOUND[p.kind])
            elif not was_loaded and p.load_t > 0:
                self._hear(p.x, p.z, body, *CREAK_SOUND[p.kind])
        if under is not None and under.afloat:
            body.x += under.dx
            body.z += under.dz
            if under.kind == "lift" and self._ground is not None:
                self._ground += under.dy  # a ride, not a fall

        for pod in self.pods:
            before = pod.t
            pod.update(dt)
            if pod.t < before:  # the cycle wrapped: it just burst
                self._hear(pod.x, pod.z, body, "puff", 0.8)
        for chute in self.chutes:
            released = chute.update(dt, self.map.floor_at, climber=(body.x, body.z))
            if released:
                event = f"logs_{released}"
            for log in chute.logs:
                if not log.hit and LogChute.touches(log, body.x, body.z, body.y, body.RADIUS):
                    log.hit = True
                    hurt(LOG_DAMAGE, "A rolling log")
                    self._move(body, log.dx * LOG_KNOCK, log.dz * LOG_KNOCK, blocked)
                    event = "log"

        tile = self.map.tile_at(body.x, body.z)
        if tile.flow and self.support(body.x, body.z) is None:
            fx, fz = tile.flow
            # The current can drag you off the ford into deep water, so water does not stop it.
            self._move(body, fx * dt, fz * dt, blocked)
            tile = self.map.tile_at(body.x, body.z)

        self.under = self.support(body.x, body.z)
        if tile.needs_footing and self.under is None:
            return self._fall(body, hurt, "river" if tile.liquid else "ravine")

        landed = self._landing(body, hurt)
        event = event or landed
        event = self._spores(dt, body, hurt) or event
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
        return event

    def _landing(self, body, hurt):
        """A drop of more than FALL_SAFE metres hurts. A big jump sideways is a teleport, not a fall,
        and dropping into a pit trap is left to the World's pit handling."""
        ground = self.floor(body.x, body.z)
        prev, last = self._ground, self._last
        self._ground, self._last = ground, (body.x, body.z)
        if prev is None or math.hypot(body.x - last[0], body.z - last[1]) > 1.0:
            return None
        if self.map.tile_at(body.x, body.z).pit:
            return None  # a pit trap: the World's own fall handling hurts you and hauls you out
        drop = prev - ground
        if drop <= FALL_SAFE:
            return None
        self.landed = drop
        hurt(max(rround((drop - FALL_SAFE) * FALL_PER_M), 1), "The fall")
        return "landed"

    def _spores(self, dt, body, hurt):
        if not any(pod.engulfs(body.x, body.z) for pod in self.pods):
            self._spore_t = 0.0
            return None
        first = getattr(body, "spore_t", 0) <= 0
        body.spore_t = SPORE_LINGER
        self._spore_t -= dt
        if self._spore_t <= 0:
            self._spore_t = SPORE_TICK
            hurt(SPORE_DAMAGE, "Spores")
        return "spores" if first else None

    def _hear(self, x, z, body, name, volume):
        """Queues a sound, quieter with distance and silent beyond HEARING."""
        d = math.hypot(x - body.x, z - body.z)
        if d < HEARING:
            self.sounds.append((name, volume * (1 - d / HEARING * 0.7)))

    def _fall(self, body, hurt, into):
        self.fell_into = into
        if into == "river":
            self.sounds.append(("splash", 1.0))
        hurt(max(rround(body.stats.max_hp * FALL_FRAC), 6), "The river" if into == "river" else "The ravine")
        if self.safe is None:
            sx, sz = self.map.meta["start"][:2]
            self.safe = TileMap.center(int(sx), int(sz))
        body.x, body.z = self.safe
        body.y = self.map.floor_at(body.x, body.z)
        self._ground, self._last = body.y, (body.x, body.z)
        return "fell"


def _always(_tx, _tz):
    return True
