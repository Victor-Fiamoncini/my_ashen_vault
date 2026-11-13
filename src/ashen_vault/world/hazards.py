"""Level traps: floor spikes, swinging pendulum blades, crumbling floors, flame jets and magma vents,
plus the fire columns and shockwaves bosses call up. Pure timing and hit logic, no rendering."""

import math
import random

from ashen_vault.world.tile_map import Tile, TileMap

HIT_COOLDOWN = 0.8  # seconds before the same trap can hurt the player again
HEAD = 1.6  # height above the floor a body can be hit up to


class SpikeTrap:
    """Spikes that rest in the floor, rattle as a warning, then thrust up."""

    DOWN = 1.3
    WARN = 0.4
    UP = 1.1
    PERIOD = DOWN + WARN + UP
    DAMAGE = 16
    RISE = 0.12  # seconds the spikes take to shoot up or sink back

    def __init__(self, tx, tz, phase=0.0):
        self.tx = tx
        self.tz = tz
        self.x, self.z = TileMap.center(tx, tz)
        self.t = phase % self.PERIOD
        self.cooldown = 0.0

    def update(self, dt):
        """Advances the cycle; returns True on the frame the spikes spring up."""
        before = self.state
        self.t = (self.t + dt) % self.PERIOD
        self.cooldown = max(self.cooldown - dt, 0.0)
        return before != "up" and self.state == "up"

    @property
    def state(self):
        if self.t < self.DOWN:
            return "down"
        if self.t < self.DOWN + self.WARN:
            return "warn"
        return "up"

    @property
    def height(self):
        """0..1 extension, for drawing: tips peek out while warning, full while up."""
        s = self.state
        if s == "down":
            return 0.0
        if s == "warn":
            return 0.15
        k = self.t - self.DOWN - self.WARN
        rise = min(k / self.RISE, 1.0)
        fall = min((self.UP - k) / self.RISE, 1.0)
        return 0.15 + 0.85 * max(min(rise, fall), 0.0)

    def covers(self, px, pz):
        return TileMap.tile_coord(px) == self.tx and TileMap.tile_coord(pz) == self.tz

    def hit(self, px, pz):
        """Damage dealt to a body at (px, pz) this frame, or 0. Each thrust wounds once."""
        if self.state != "up" or self.cooldown > 0 or not self.covers(px, pz):
            return 0
        self.cooldown = self.UP  # one wound per thrust
        return self.DAMAGE


class Pendulum:
    """A heavy blade hung from the ceiling, swinging along the corridor it guards.

    `axis` is "x" when the corridor runs along X (walls on its north and south sides)."""

    AMP = 1.0  # radians either side of straight down
    SPEED = 2.4  # radians of phase per second (period ~2.6 s)
    DAMAGE = 20
    BLADE = 0.55  # half-width of the blade along the swing
    PUSH = 1.1  # knockback distance in metres

    def __init__(self, tx, tz, axis, pivot_y, length, floor=0.0, phase=0.0):
        self.tx = tx
        self.tz = tz
        self.x, self.z = TileMap.center(tx, tz)
        self.axis = axis
        self.pivot_y = pivot_y
        self.length = length
        self.floor = floor
        self.t = phase / self.SPEED
        self.cooldown = 0.0

    def update(self, dt):
        """Advances the swing; returns True when the blade passes its lowest point."""
        before = math.sin(self.t * self.SPEED)
        self.t += dt
        self.cooldown = max(self.cooldown - dt, 0.0)
        after = math.sin(self.t * self.SPEED)
        return (before < 0) != (after < 0)

    @property
    def angle(self):
        return self.AMP * math.sin(self.t * self.SPEED)

    @property
    def direction(self):
        """+1 or -1: which way along the axis the blade is moving."""
        return 1 if math.cos(self.t * self.SPEED) >= 0 else -1

    def blade_offset(self):
        """Blade position along the swing axis, relative to the pivot."""
        return self.length * math.sin(self.angle)

    def blade_bottom(self):
        """World height of the blade's lowest edge."""
        return self.pivot_y - self.length * math.cos(self.angle) - 0.3

    def _local(self, px, pz):
        """(along, across) offsets of a point from the pivot, in the swing frame."""
        dx = px - self.x
        dz = pz - self.z
        return (dx, dz) if self.axis == "x" else (dz, dx)

    def hit(self, px, pz):
        """(damage, push_dx, push_dz) for a body at (px, pz) this frame, or None."""
        if self.cooldown > 0:
            return None
        along, across = self._local(px, pz)
        if abs(across) > TileMap.TILE / 2:
            return None
        if abs(along - self.blade_offset()) > self.BLADE:
            return None
        if self.blade_bottom() > self.floor + HEAD:
            return None
        self.cooldown = HIT_COOLDOWN
        push = self.PUSH * self.direction
        return (self.DAMAGE, push, 0.0) if self.axis == "x" else (self.DAMAGE, 0.0, push)


class CrumbleFloor:
    """A slab bridging a pit. Step on it and it shakes, gives way, and some seconds later grows back."""

    SHAKE = 1.0  # walking pace crosses a 2 m slab in ~0.77 s: keep moving and you make it
    GONE = 4.0
    REFORM = 0.5  # seconds the slab takes to rise back into place

    def __init__(self, tx, tz, floor, base):
        self.tx = tx
        self.tz = tz
        self.x, self.z = TileMap.center(tx, tz)
        self.floor = floor
        self.base = base  # the pit tile underneath
        self.state = "solid"
        self.t = self.REFORM  # already in place when the map loads

    def solid_tile(self):
        """The walkable stand-in for the pit tile while the slab holds."""
        b = self.base
        return Tile(
            solid=False,
            walkable=True,
            floor=self.floor,
            ceil=b.ceil,
            floor_tex=b.floor_tex,
            wall_tex=b.wall_tex,
            ceil_tex=b.ceil_tex,
        )

    @property
    def standing(self):
        """True while something can stand on it."""
        return self.state != "fallen"

    def update(self, dt, player_on=False):
        """Advances the slab; returns the new state on the frame it changes, else None."""
        self.t += dt
        if self.state == "solid":
            if not player_on:
                return None
            return self._switch("shaking")
        if self.state == "shaking" and self.t >= self.SHAKE:
            return self._switch("fallen")
        if self.state == "fallen" and self.t >= self.GONE:
            return self._switch("solid")
        return None

    def _switch(self, state):
        self.state = state
        self.t = 0.0
        return state

    @property
    def shake(self):
        """0..1 tremble strength while shaking."""
        return min(self.t / self.SHAKE, 1.0) if self.state == "shaking" else 0.0

    @property
    def rise(self):
        """0..1 while a reformed slab grows back into place, 1 once settled."""
        return min(self.t / self.REFORM, 1.0) if self.state == "solid" else 1.0

    @property
    def drop(self):
        """How far the slab has fallen, for drawing: 0 in place, growing once it gives way."""
        if self.state == "fallen":
            return min(self.t * 6.0, 4.0)
        return 0.0


class Eruption:
    """A column of fire the Warden calls up through the floor: a glowing circle warns where it will
    burst, then flame roars up for a moment. Each burst wounds once."""

    WARN = 0.9
    BURN = 0.55
    RADIUS = 1.0
    DAMAGE = 18

    def __init__(self, x, z, floor=0.0, delay=0.0, damage=DAMAGE, origin=None):
        self.x = x
        self.z = z
        self.floor = floor
        self.t = -delay  # a later circle in a row waits its turn before it starts glowing
        self.damage = damage
        self.spent = False  # has it wounded someone yet
        # (x, y, z) a lobbed magma bomb flies from: it arcs down while the circle glows.
        self.origin = origin

    def update(self, dt):
        """Advances it; returns True on the frame the flame bursts up."""
        before = self.state
        self.t += dt
        return before != "burst" and self.state == "burst"

    @property
    def state(self):
        if self.t < 0:
            return "waiting"
        if self.t < self.WARN:
            return "warn"
        if self.t < self.WARN + self.BURN:
            return "burst"
        return "done"

    @property
    def done(self):
        return self.state == "done"

    @property
    def glow(self):
        """0..1 brightness of the warning circle; it brightens as the burst nears."""
        return min(max(self.t / self.WARN, 0.0), 1.0) if self.state == "warn" else 0.0

    def bomb(self, arc=6.0):
        """Where a lobbed bomb is in its flight, (x, y, z), or None when it is not in the air: it
        leaves `origin` as the circle starts to glow and lands as the flame bursts."""
        if self.origin is None or self.state != "warn":
            return None
        k = self.t / self.WARN
        ox, oy, oz = self.origin
        y = oy + (self.floor - oy) * k + arc * 4 * k * (1 - k)
        return ox + (self.x - ox) * k, y, oz + (self.z - oz) * k

    @property
    def flame(self):
        """0..1 height of the flame column: shoots up, then dies away."""
        if self.state != "burst":
            return 0.0
        k = (self.t - self.WARN) / self.BURN
        return min(k / 0.2, 1.0) * (1 - max(k - 0.6, 0.0) / 0.4)

    def hit(self, px, pz):
        """Damage to a body at (px, pz) this frame, or 0."""
        if self.state != "burst" or self.spent:
            return 0
        if math.hypot(px - self.x, pz - self.z) > self.RADIUS:
            return 0
        self.spent = True
        return self.damage


class Shockwave:
    """The ring of dust and embers a slam sends along the floor. Only for show: the slam's damage is
    dealt when it lands."""

    TIME = 0.6

    def __init__(self, x, z, floor, radius):
        self.x = x
        self.z = z
        self.floor = floor
        self.radius = radius
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    @property
    def progress(self):
        return min(self.t / self.TIME, 1.0)

    @property
    def done(self):
        return self.t >= self.TIME


# Unit steps along the four map directions, for things that point one way.
DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}


class FlameJet:
    """A nozzle low on the wall that roars a gout of fire along the floor in front of it. It hisses
    and glows before it fires: wait for the gout to die, then run past."""

    WARN = 0.7
    BURN = 1.1
    DAMAGE = 14
    HALF_WIDTH = 0.75  # metres either side of the jet's line that the fire licks

    def __init__(self, tx, tz, direction="e", length=3, every=3.6, phase=0.0, floor=0.0):
        self.tx = tx
        self.tz = tz
        self.x, self.z = TileMap.center(tx, tz)
        self.dx, self.dz = DIRS.get(direction, (1, 0))
        self.length = max(int(length), 1)
        self.period = max(every, self.WARN + self.BURN + 0.2)
        self.floor = floor
        self.t = phase % self.period
        self.cooldown = 0.0

    @property
    def idle(self):
        return self.period - self.WARN - self.BURN

    @property
    def state(self):
        if self.t < self.idle:
            return "idle"
        if self.t < self.idle + self.WARN:
            return "warn"
        return "burn"

    def update(self, dt):
        """Advances the cycle; returns True on the frame the jet starts to roar."""
        before = self.state
        self.t = (self.t + dt) % self.period
        self.cooldown = max(self.cooldown - dt, 0.0)
        return before != "burn" and self.state == "burn"

    @property
    def reach(self):
        """0..1 of its length the gout reaches now: it shoots out fast and shrinks back at the end."""
        if self.state != "burn":
            return 0.0
        k = (self.t - self.idle - self.WARN) / self.BURN
        return min(k / 0.15, 1.0) * min((1 - k) / 0.2, 1.0)

    @property
    def glow(self):
        """0..1 brightness of the nozzle while it builds up to fire."""
        if self.state == "warn":
            return (self.t - self.idle) / self.WARN
        return 1.0 if self.state == "burn" else 0.0

    def _start(self):
        """Where the gout leaves the nozzle: the back edge of its tile."""
        return self.x - self.dx * TileMap.TILE / 2, self.z - self.dz * TileMap.TILE / 2

    def covers(self, px, pz):
        sx, sz = self._start()
        along = (px - sx) * self.dx + (pz - sz) * self.dz
        across = abs((px - sx) * self.dz - (pz - sz) * self.dx)
        return 0 <= along <= self.length * TileMap.TILE * self.reach and across <= self.HALF_WIDTH

    def hit(self, px, pz):
        """Damage to a body at (px, pz) this frame, or 0."""
        if self.cooldown > 0 or self.reach < 0.5 or not self.covers(px, pz):
            return 0
        self.cooldown = HIT_COOLDOWN
        return self.DAMAGE


class MagmaVent:
    """A vent deep in the lava that spits molten bombs onto the ground around it. Each bomb is an
    `Eruption` with an `origin`: it glows where it will land while it arcs down, then bursts.
    `targets` are the (x, z, floor) spots it can reach; it aims at the player's spot when it can."""

    FLIGHT = Eruption.WARN  # the bomb is in the air while its circle glows
    DAMAGE = 16
    HEIGHT = 2.0  # metres above its tile the bombs leave from

    def __init__(self, tx, tz, targets, every=3.0, phase=0.0, count=2, floor=0.0, radius=8.0, seed=None):
        self.tx = tx
        self.tz = tz
        self.x, self.z = TileMap.center(tx, tz)
        self.floor = floor
        self.targets = list(targets)
        self.every = every
        self.count = count
        self.radius = radius
        self.t = phase % every
        self._rng = random.Random(seed if seed is not None else tx * 1000 + tz)

    def update(self, dt, player_spot=None):
        """Advances it; returns the Eruptions it lobs this frame (empty most frames). `player_spot` is
        the (x, z, floor) the player stands on, if it is in reach."""
        self.t += dt
        if self.t < self.every or not self.targets:
            return []
        self.t -= self.every
        out = []
        spots = list(self.targets)
        for i in range(self.count):
            if i == 0 and player_spot is not None:
                spot = player_spot
            else:
                spot = self._rng.choice(spots)
            x, z, floor = spot
            out.append(
                Eruption(
                    x,
                    z,
                    floor,
                    delay=i * 0.3,
                    damage=self.DAMAGE,
                    origin=(self.x, self.floor + self.HEIGHT, self.z),
                )
            )
        return out

    def reaches(self, x, z):
        return math.hypot(x - self.x, z - self.z) <= self.radius
