"""Level traps: floor spikes and swinging pendulum blades. Pure timing and hit logic, no rendering."""

import math

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

    def __init__(self, x, z, floor=0.0, delay=0.0, damage=DAMAGE):
        self.x = x
        self.z = z
        self.floor = floor
        self.t = -delay  # a later circle in a row waits its turn before it starts glowing
        self.damage = damage
        self.spent = False  # has it wounded someone yet

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
