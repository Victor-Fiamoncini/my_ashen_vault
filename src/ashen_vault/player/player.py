import math

from ashen_vault.player import weapons
from ashen_vault.player.combat import Gauge, Stamina
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
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
    WEBBED = 0.45  # speed multiplier while caught in silk
    SPORED = 0.6  # speed multiplier while choking on spores

    def __init__(self, stats=None, inventory=None, spells=None):
        self.stats = stats or Stats()
        self.inventory = inventory or Inventory()
        self.spells = spells if spells is not None else ["flame"]
        self.spell_index = 0
        self.quick = "red_tonic"  # consumable on the middle mouse button
        self.x = self.z = self.y = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.bob_t = 0.0
        self.hurt_t = 0.0
        self.lumen_t = 0.0
        self.webbed_t = 0.0  # seconds left caught in spider silk
        self.spore_t = 0.0  # seconds left choking on spores
        self.swing_t = None
        self.swing_power = 0.0
        self.attack = weapons.attack(self.inventory.weapon_item())
        self.charge_t = 0.0  # seconds the attack button has been held
        self.sprinting = False
        self.attack_gauge = Gauge(self.inventory.weapon_item().speed)
        self.magic_gauge = Gauge(2.2)
        self.stamina = Stamina()

    def place(self, x, z, yaw, map_):
        self.x = x
        self.z = z
        self.yaw = yaw
        self.pitch = 0.0
        self.y = map_.floor_at(x, z)

    def revive(self):
        """Back on your feet at a shrine: full HP, MP and ST, and every lingering effect cleared."""
        s = self.stats
        s.heal(s.max_hp)
        s.restore_mp(s.max_mp)
        self.stamina.fill()
        self.hurt_t = self.lumen_t = self.webbed_t = self.spore_t = 0.0
        self.swing_t = None
        self.charge_t = 0.0
        self.pitch = 0.0

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

    def cycle_spell(self, step=1):
        """Selects the next (or previous) known spell; None when there is nothing to switch to."""
        if len(self.spells) < 2:
            return None
        self.spell_index = (self.spell_index + step) % len(self.spells)
        return self.current_spell()

    def equip_spell(self, id_):
        """Readies a known spell for the right mouse button; False if it isn't known."""
        if id_ not in self.spells:
            return False
        self.spell_index = self.spells.index(id_)
        return True

    def quick_items(self):
        """Every kind of consumable, carried or not, in a stable order: the wheel steps through them
        all and the HUD greys out the ones you have none of."""
        return sorted((i for i in Items.ALL.values() if i.kind == "consumable"), key=lambda i: i.name)

    def quick_item(self):
        """The selected quick item, even when you have none left (the HUD greys it out)."""
        return Items.get(self.quick)

    def cycle_quick(self, step=1):
        """Selects the next (or previous) consumable; None when there is nothing to switch to."""
        ids = [i.id for i in self.quick_items()]
        if len(ids) < 2 and self.quick in ids:
            return None
        if self.quick in ids:
            self.quick = ids[(ids.index(self.quick) + step) % len(ids)]
        else:
            self.quick = ids[0 if step > 0 else -1]
        return self.quick_item()

    @property
    def heading(self):
        """Compass heading in degrees, north (-Z) = 0."""
        return ((self.yaw * 180 / math.pi) + 90) % 360

    def turn(self, amount):
        self.yaw = (self.yaw + amount) % (2 * math.pi)

    def look(self, amount):
        self.pitch = clamp(self.pitch + amount, -self.LOOK_LIMIT, self.LOOK_LIMIT)

    def walk(self, map_, fwd, strafe, dt, blocked=None, sprint=False, floating=None, ground=None):
        """fwd/strafe are -1..1 intents. Returns True if the player moved.
        Sprinting is faster but drains stamina; sucking mud (a tile's `slow`) holds you back.
        `floating` lets you walk onto rafts, planks and ledges over water or a chasm, and `ground`
        gives the height you stand at while on one."""
        self.sprinting = False
        if fwd == 0 and strafe == 0:
            return False
        fx, fz = self.forward()
        speed = self.BACK_SPEED if fwd < 0 else self.WALK_SPEED
        sprint = sprint and self.stamina.can_sprint
        if sprint:
            speed *= self.SPRINT
        speed *= map_.tile_at(self.x, self.z).slow
        if self.webbed_t > 0:
            speed *= self.WEBBED
        if self.spore_t > 0:
            speed *= self.SPORED
        dx = (fx * fwd - fz * strafe) * speed * dt
        dz = (fz * fwd + fx * strafe) * speed * dt
        length = math.hypot(fwd, strafe)
        if length > 1:
            dx /= length
            dz /= length
        ox, oz = self.x, self.z
        self.x, self.z = collision.move(
            map_,
            self.x,
            self.z,
            dx,
            dz,
            radius=self.RADIUS,
            blocked=blocked,
            floating=floating,
            ground=ground,
        )
        moved = math.hypot(self.x - ox, self.z - oz)
        self.bob_t += moved * 2.2
        self.sprinting = sprint and moved > 1e-4
        if self.sprinting:
            self.stamina.drain(dt)
        return moved > 1e-4

    def settle(self, map_, dt, floor=None):
        """Eases eye height onto the floor below (stairs, drops), or onto `floor` (a raft deck)."""
        target = map_.floor_at(self.x, self.z) if floor is None else floor
        self.y += (target - self.y) * min(dt * 10, 1)
        if abs(target - self.y) < 0.005:
            self.y = target

    def update_timers(self, dt):
        self.attack_gauge.refill_time = self.inventory.weapon_item().speed
        if not self.swinging:
            self.attack_gauge.update(dt)
        if not self.sprinting:
            self.stamina.update(dt)
        self.magic_gauge.update(dt)
        self.hurt_t = max(self.hurt_t - dt, 0)
        self.lumen_t = max(self.lumen_t - dt, 0)
        self.webbed_t = max(self.webbed_t - dt, 0)
        self.spore_t = max(self.spore_t - dt, 0)
        if self.swing_t is None:
            return
        self.swing_t += dt
        if self.swing_t > self.swing_time:
            self.swing_t = None

    @property
    def swinging(self):
        return self.swing_t is not None

    def nudge(self, map_, dist, blocked=None):
        """Steps straight ahead by `dist` metres, stopped by walls (a lunging attack)."""
        fx, fz = self.forward()
        steps = max(math.ceil(dist / 0.1), 1)  # small steps so it stops at a foe, never past it
        for _ in range(steps):
            self.x, self.z = collision.move(
                map_,
                self.x,
                self.z,
                fx * dist / steps,
                fz * dist / steps,
                radius=self.RADIUS,
                blocked=blocked,
            )

    @property
    def swing_time(self):
        return self.SWING_TIME * (weapons.HEAVY_TIME if self.attack.heavy else 1.0)

    @property
    def swing_hit_at(self):
        return self.SWING_HIT_AT * (weapons.HEAVY_TIME * 1.1 if self.attack.heavy else 1.0)

    @property
    def charge_frac(self):
        """0..1 progress of a held attack towards a heavy one."""
        return min(self.charge_t / weapons.CHARGE_TIME, 1.0)

    def can_heavy(self):
        heavy = weapons.attack(self.inventory.weapon_item(), heavy=True)
        return not self.stamina.exhausted and self.stamina.value >= heavy.stamina

    def start_swing(self, heavy=False):
        """Starts a light or heavy attack. A heavy one costs ST; without enough, it is light."""
        if self.swinging:
            return False
        heavy = heavy and self.can_heavy()
        self.attack = weapons.attack(self.inventory.weapon_item(), heavy)
        if heavy:
            self.stamina.spend(self.attack.stamina)
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
            "spell": self.current_spell().id if self.spells else None,
            "quick": self.quick,
        }
