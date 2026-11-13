import math

from ashen_vault.player import guard, weapons
from ashen_vault.player.combat import Gauge, Stamina
from ashen_vault.player.inventory import HANDS, RIGHT, Inventory
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
    SWING_TIME = 0.45  # a light swing of a sword; see Attack.time and weapons.tempo
    QUICK_FROM = 0.55  # a quick follow-up can cut in once a light swing is this far along
    HITSTOP = 0.05  # seconds a swing freezes when it connects
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
        self.swing_hand = RIGHT
        self.attack = weapons.attack(self.inventory.weapon_item())
        self.charge_t = 0.0  # seconds the attack button has been held
        self.charge_hand = RIGHT  # which button is being held
        self.queued_quick = False  # clicked again during a light swing
        self.hitstop_t = 0.0
        self.sprinting = False
        self.since_sprint = 99.0
        self.still_t = 0.0
        self.gauges = {h: Gauge(self.hand_weapon(h).speed or 1.0) for h in HANDS}
        self.magic_gauge = Gauge(2.2)
        self.stamina = Stamina()
        self.guarding = False
        self.guard_break_t = 0.0
        self.since_block = 99.0  # since your shield last stopped a blow
        self.since_hit = 99.0  # since any blow last landed on you or your shield
        self.combo_target = None  # the foe your last blows landed on, and how many in a row
        self.combo_n = 0
        self.combo_t = 99.0

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
        self.queued_quick = False
        self.guarding = False
        self.guard_break_t = self.hitstop_t = 0.0
        self.combo_n = 0
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
        sprint = sprint and self.stamina.can_sprint and not self.guarding
        if self.guarding:
            speed *= guard.WALK
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
        if moved > 1e-4:
            self.still_t = 0.0
        self.bob_t += moved * 2.2
        self.sprinting = sprint and moved > 1e-4
        if self.sprinting:
            self.stamina.drain(dt)
        return moved > 1e-4

    def settle(self, map_, dt, floor=None, snap=False):
        """Eases eye height onto the floor below (stairs, drops), or onto `floor` (a raft deck).
        `snap` keeps you exactly on it (riding a lift, so the deck never rises through your view)."""
        target = map_.floor_at(self.x, self.z) if floor is None else floor
        self.y += (target - self.y) * (1 if snap else min(dt * 10, 1))
        if abs(target - self.y) < 0.005:
            self.y = target

    def update_timers(self, dt):
        for h, gauge in self.gauges.items():
            gauge.refill_time = self.hand_weapon(h).speed or 1.0
            if not (self.swinging and self.swing_hand == h):
                gauge.update(dt)
        if not self.sprinting:
            self.stamina.update(dt, guard.REFILL if self.guarding else 1.0)
        self.since_sprint = 0.0 if self.sprinting else self.since_sprint + dt
        self.still_t += dt
        self.since_block += dt
        self.since_hit += dt
        self.combo_t += dt
        if self.combo_t > weapons.COMBO_WINDOW:
            self.combo_n = 0
        self.guard_break_t = max(self.guard_break_t - dt, 0)
        self.magic_gauge.update(dt)
        self.hurt_t = max(self.hurt_t - dt, 0)
        self.lumen_t = max(self.lumen_t - dt, 0)
        self.webbed_t = max(self.webbed_t - dt, 0)
        self.spore_t = max(self.spore_t - dt, 0)
        if self.swing_t is None:
            return
        if self.hitstop_t > 0:  # the blade bites: hold the swing a moment
            self.hitstop_t = max(self.hitstop_t - dt, 0)
            return
        self.swing_t += dt
        if self.swing_t > self.swing_time:
            self.swing_t = None
            self.queued_quick = False

    # --- hands -------------------------------------------------------------------------

    def hand_item(self, hand):
        return self.inventory.hand_item(hand)

    def hand_weapon(self, hand):
        """The weapon `hand` attacks with (its fist when it holds none); shields and spells too."""
        return self.inventory.hand_item(hand)

    @property
    def attack_gauge(self):
        """The ATK gauge of the right hand (the left mouse button)."""
        return self.gauges[RIGHT]

    def gauge(self, hand):
        """A hand's ATK gauge; a two-hander shares the right hand's."""
        return self.gauges[RIGHT if self.inventory.two_handing() else hand]

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
    def swing_weapon(self):
        return self.hand_weapon(self.swing_hand)

    @property
    def swing_time(self):
        return self.SWING_TIME * self.attack.time * weapons.tempo(self.swing_weapon)

    @property
    def swing_hit_at(self):
        return self.swing_time * self.attack.hit_at

    @property
    def swing_phase(self):
        """0..1 progress of the current swing, or None."""
        if self.swing_t is None:
            return None
        return min(self.swing_t / self.swing_time, 1.0)

    @property
    def charge_frac(self):
        """0..1 progress of a held attack towards a heavy one."""
        return min(self.charge_t / weapons.CHARGE_TIME, 1.0)

    def can_heavy(self, hand=RIGHT):
        heavy = weapons.attack(self.hand_weapon(hand), weapons.HEAVY)
        return not self.stamina.exhausted and self.stamina.value >= heavy.stamina

    def context(self):
        """What secrets look at as a swing starts."""
        return weapons.Context(
            sprinting=self.sprinting,
            since_sprint=self.since_sprint,
            still_t=self.still_t,
            charge_t=self.charge_t,
            combo=self.combo_n,
            since_hit=self.since_hit,
        )

    def start_swing(self, hand=RIGHT, kind=weapons.LIGHT, secrets=True):
        """Starts an attack with `hand`. Every attack costs ST: too winded and you can't swing at all,
        and a heavy you can't pay for comes out light. A light or heavy may turn into the weapon's
        secret attack (see weapons.secret). Returns the Attack, or None."""
        if self.swinging or self.guard_break_t > 0 or self.stamina.exhausted:
            return None
        item = self.hand_weapon(hand)
        if item.kind != "weapon":
            return None
        if kind == weapons.HEAVY and not self.can_heavy(hand):
            kind = weapons.LIGHT
        a = weapons.attack(item, kind)
        hidden = weapons.secret(item, kind, self.context()) if secrets else None
        if hidden and self.stamina.value >= hidden.stamina:
            a = hidden
            self.combo_n = 0
        self.stamina.spend(min(a.stamina, self.stamina.value))
        self.attack = a
        self.swing_hand = hand
        self.swing_power = max(self.gauge(hand).spend(), a.min_power)
        self.swing_t = 0.0
        self.hitstop_t = 0.0
        self.queued_quick = False
        self.guarding = False
        return a

    def queue_quick(self, hand):
        """A second click during a light swing of the same hand: a quick strike follows it."""
        if self.swinging and self.swing_hand == hand and self.attack.kind == weapons.LIGHT:
            self.queued_quick = True
            return True
        return False

    def chain_quick(self):
        """Cuts the light swing short with the queued quick strike once its blow has landed and it is
        far enough along. Returns the quick Attack, or None."""
        if not (self.queued_quick and self.swinging and self.swing_t >= self.swing_hit_at):
            return None
        if self.swing_t < self.swing_time * self.QUICK_FROM:
            return None
        hand = self.swing_hand
        self.swing_t = None
        return self.start_swing(hand, weapons.QUICK)

    def land_hit(self, target):
        """A swing connected with `target`: freezes it a moment and counts the combo."""
        self.hitstop_t = self.HITSTOP * weapons.tempo(self.swing_weapon)
        if target is self.combo_target and self.combo_t <= weapons.COMBO_WINDOW:
            self.combo_n += 1
        else:
            self.combo_target = target
            self.combo_n = 1
        self.combo_t = 0.0

    # --- guard -----------------------------------------------------------------------

    def raise_guard(self, up):
        """Holds the shield up (or lowers it). Not while swinging or reeling from a broken guard."""
        self.guarding = bool(
            up and self.inventory.shield_hand() and not self.swinging and self.guard_break_t <= 0
        )
        return self.guarding

    def take_blow(self, dmg, ax, az):
        """A blow of `dmg` from (ax, az): the raised shield blocks what it can. Returns the damage that
        lands and the Block (None when not guarding)."""
        self.since_hit = 0.0
        if not self.guarding:
            return dmg, None
        shield = self.hand_item(self.inventory.shield_hand())
        fx, fz = self.forward()
        b = guard.block(dmg, guard.facing_cos(self.x, self.z, fx, fz, ax, az), shield, self.stamina.value)
        if b.stamina:
            self.stamina.spend(b.stamina)
        if b.broken:
            self.guarding = False
            self.guard_break_t = guard.BREAK_TIME
        elif b.blocked:
            self.since_block = 0.0
        return b.taken, b

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
