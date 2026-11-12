import math

from ashen_vault.player.combat import Gauge
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.spells import Spells
from ashen_vault.player.stats import Stats
from ashen_vault.util import clamp
from ashen_vault.world import collision


class Player:
    """First-person body: deliberately slow, old-school dungeon-crawler movement."""

    RADIUS = 0.4
    EYE = 1.55
    WALK_SPEED = 2.6
    BACK_SPEED = 1.8
    SPRINT = 1.75  # speed multiplier while sprinting
    TURN_SPEED = 1.7  # rad/s on keys
    LOOK_LIMIT = 0.9
    SWING_TIME = 0.45
    SWING_HIT_AT = 0.16

    def __init__(self, stats=None, inventory=None, spells=None):
        self.stats = stats or Stats()
        self.inventory = inventory or Inventory()
        self.spells = spells if spells is not None else ["flame"]
        self.spell_index = 0
        self.x = self.z = self.y = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.bob_t = 0.0
        self.hurt_t = 0.0
        self.lumen_t = 0.0
        self.swing_t = None
        self.swing_power = 0.0
        self.sprinting = False
        self.attack_gauge = Gauge(self.inventory.weapon_item().speed)
        self.magic_gauge = Gauge(2.2)

    def place(self, x, z, yaw, map_):
        self.x = x
        self.z = z
        self.yaw = yaw
        self.pitch = 0.0
        self.y = map_.floor_at(x, z)

    def forward(self):
        return math.cos(self.yaw), math.sin(self.yaw)

    @property
    def eye_y(self):
        return self.y + self.EYE + math.sin(self.bob_t * 2) * 0.035

    @property
    def alive(self):
        return not self.stats.dead

    def current_spell(self):
        if not self.spells:
            return None
        return Spells.get(self.spells[self.spell_index % len(self.spells)])

    @property
    def heading(self):
        """Compass heading in degrees, north (-Z) = 0."""
        return ((self.yaw * 180 / math.pi) + 90) % 360

    def turn(self, amount):
        self.yaw = (self.yaw + amount) % (2 * math.pi)

    def look(self, amount):
        self.pitch = clamp(self.pitch + amount, -self.LOOK_LIMIT, self.LOOK_LIMIT)

    def walk(self, map_, fwd, strafe, dt, blocked=None, sprint=False):
        """fwd/strafe are -1..1 intents. Returns True if the player moved.
        Sprinting is faster but holds the ATK gauge from refilling."""
        self.sprinting = False
        if fwd == 0 and strafe == 0:
            return False
        fx, fz = self.forward()
        speed = self.BACK_SPEED if fwd < 0 else self.WALK_SPEED
        if sprint:
            speed *= self.SPRINT
        dx = (fx * fwd - fz * strafe) * speed * dt
        dz = (fz * fwd + fx * strafe) * speed * dt
        length = math.hypot(fwd, strafe)
        if length > 1:
            dx /= length
            dz /= length
        ox, oz = self.x, self.z
        self.x, self.z = collision.move(map_, self.x, self.z, dx, dz, radius=self.RADIUS, blocked=blocked)
        moved = math.hypot(self.x - ox, self.z - oz)
        self.bob_t += moved * 2.2
        self.sprinting = sprint and moved > 1e-4
        return moved > 1e-4

    def settle(self, map_, dt):
        """Eases eye height onto the floor below (stairs, drops)."""
        target = map_.floor_at(self.x, self.z)
        self.y += (target - self.y) * min(dt * 10, 1)
        if abs(target - self.y) < 0.005:
            self.y = target

    def update_timers(self, dt):
        self.attack_gauge.refill_time = self.inventory.weapon_item().speed
        if not (self.swinging or self.sprinting):
            self.attack_gauge.update(dt)
        self.magic_gauge.update(dt)
        self.hurt_t = max(self.hurt_t - dt, 0)
        self.lumen_t = max(self.lumen_t - dt, 0)
        if self.swing_t is None:
            return
        self.swing_t += dt
        if self.swing_t > self.SWING_TIME:
            self.swing_t = None

    @property
    def swinging(self):
        return self.swing_t is not None

    def start_swing(self):
        if self.swinging:
            return False
        self.swing_power = self.attack_gauge.spend()
        self.swing_t = 0.0
        return True

    def to_h(self):
        return {
            "x": self.x,
            "z": self.z,
            "yaw": self.yaw,
            "stats": self.stats.to_h(),
            "inventory": self.inventory.to_h(),
            "spells": list(self.spells),
        }
