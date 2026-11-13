import math
import random

DEATH_TIME = 2.4  # seconds a body takes to burn down to ash
BOSS_DEATH_TIME = 4.5

BEHIND = 2.2  # radians off the facing beyond which a blow counts as from behind
GIVE_UP = 12.0  # a lurker chases this far before settling down again

# Boss moves: windup seconds, cooldown seconds, damage multiplier.
MOVES = {
    "sweep": (0.85, 4.0, 0.9),  # legs scythe all around; hits from any side
    "web": (0.6, 5.0, 0.5),  # spits silk that slows you
    "pounce": (0.75, 7.0, 1.3),  # leaps at where you stood when it sprang
    "summon": (1.3, 0.0, 0.0),  # shrieks and calls its brood (once, at half HP)
    "cinders": (0.9, 6.0, 0.45),  # flings a fan of three embers
}
SWEEP_REACH = 1.0  # extra reach of a sweep over the type's normal reach
POUNCE_SPEED = 13.0  # m/s through the air
POUNCE_TIME = 0.5  # longest a pounce can fly
TRAIL_HOLD = 0.6  # seconds the boss bar's damage trail waits before draining
TRAIL_RATE = 0.35  # fraction of max HP the trail drains per second


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class Enemy:
    """Enemy state machine. `world` must provide:
    player_x, player_z, player_alive, can_see(ax, az, bx, bz),
    move_enemy(enemy, dx, dz), enemy_strike(enemy, mult), enemy_fire(enemy, kind),
    and for bosses with a brood, summon(enemy, type_id, count)
    """

    def __init__(self, type_, x, z, yaw=0.0, marker=None, rng=None, loot=None, key=None):
        self.type = type_
        self.x = x
        self.z = z
        self.home_x = x
        self.home_z = z
        self.yaw = yaw
        self.hp = type_.hp
        self.trail_hp = float(type_.hp)  # lags behind hp after a hit: the boss bar's damage trail
        self._trail_hold = 0.0
        self.marker = marker
        self._rng = rng or random.Random()
        self.loot = loot  # item dropped on death
        self.key = key  # flag set on death for enemies that stay dead
        self.state = "dormant" if type_.ambush else "idle"
        self.state_t = 0.0
        self.anim_t = 0.0
        self._wander_dir = None
        self._struck = False
        # "melee", "shot", "bite" or a boss move: what the current windup will turn into.
        self.attack_kind = None
        # Boss moves start part-way cooled down so a fight doesn't open with all of them.
        self.cooldowns = {m: MOVES[m][1] * 0.4 for m in type_.moves}
        self.summoned = False
        self._target = None  # where a pounce is headed

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def gone(self):
        return self.state == "dead" and self.state_t > self.death_time

    @property
    def death_time(self):
        return BOSS_DEATH_TIME if self.type.boss else DEATH_TIME

    @property
    def death_progress(self):
        """0 at the killing blow, 1 once the body has fully turned to ash."""
        if self.alive:
            return 0.0
        return min(self.state_t / self.death_time, 1.0)

    @property
    def radius(self):
        return self.type.radius

    @property
    def name(self):
        return self.type.name

    def update(self, dt, world):
        self.anim_t += dt
        self.state_t += dt
        self._update_trail(dt)
        if self.state in ("dead", "dormant"):
            return
        for m in self.cooldowns:
            self.cooldowns[m] = max(self.cooldowns[m] - dt, 0.0)
        dist = math.hypot(world.player_x - self.x, world.player_z - self.z)
        if self._should_summon():
            self.summoned = True
            self.face(world.player_x, world.player_z)
            return self._begin_windup("summon")
        s = self.state
        if s == "idle":
            self._idle(dt, world, dist)
        elif s == "chase":
            self._chase(dt, world, dist)
        elif s == "windup":
            self._windup(world, dt)
        elif s == "attack":
            self._attack(world, dist, dt)
        elif s in ("recover", "hurt") and self.state_t >= (0.35 if s == "hurt" else self.type.recover):
            self._switch("chase")

    @property
    def windup_time(self):
        return MOVES[self.attack_kind][0] if self.attack_kind in MOVES else self.type.windup

    @property
    def enraged(self):
        """A boss that has called its brood fights harder: quicker moves, shorter cooldowns."""
        return self.summoned

    def _should_summon(self):
        return (
            self.type.brood is not None
            and not self.summoned
            and self.hp <= self.type.hp / 2
            and self.state in ("chase", "recover")
        )

    def _update_trail(self, dt):
        """After a short hold, the damage trail drains down to the current HP."""
        if self._trail_hold > 0:
            self._trail_hold = max(self._trail_hold - dt, 0.0)
            return
        self.trail_hp = max(self.trail_hp - self.type.hp * TRAIL_RATE * dt, float(self.hp))

    def kill(self):
        if self.alive:
            self.hp = 0
            self._switch("dead")

    def take_hit(self, amount, poise_mult=1.0):
        """Applies damage and returns True if the hit was fatal. Heavy blows (`poise_mult`)
        stagger tougher foes."""
        if not self.alive:
            return False
        was_dormant = self.dormant
        self.hp -= amount
        self._trail_hold = TRAIL_HOLD
        if self.hp <= 0:
            self.hp = 0
            self._switch("dead")
            return True
        if amount * poise_mult >= self.type.poise:
            self._switch("hurt")
        elif was_dormant:
            self._switch("chase")
        return False

    @property
    def dormant(self):
        return self.state == "dormant"

    def wake(self, px, pz):
        """A disguised enemy springs: it turns on whoever disturbed it and strikes straight away."""
        if not self.dormant:
            return
        self.face(px, pz)
        self._switch("windup")

    def face(self, tx, tz, dt=None):
        """Turns toward (tx, tz): instantly, or at the type's `turn_rate` when given a `dt`."""
        want = math.atan2(tz - self.z, tx - self.x)
        rate = self.type.turn_rate
        if rate is None or dt is None:
            self.yaw = want
            return
        diff = _wrap(want - self.yaw)
        step = rate * dt
        self.yaw = want if abs(diff) <= step else self.yaw + math.copysign(step, diff)

    def hit_mult(self, ax, az):
        """Damage multiplier for a blow from (ax, az): `back_mult` when it lands from behind."""
        if self.type.back_mult == 1.0:
            return 1.0
        diff = _wrap(math.atan2(az - self.z, ax - self.x) - self.yaw)
        return self.type.back_mult if abs(diff) > BEHIND else 1.0

    def _switch(self, state):
        self.state = state
        self.state_t = 0.0
        self._struck = False
        if state not in ("windup", "attack"):
            self.attack_kind = None

    def _notices(self, world, dist):
        return (
            world.player_alive
            and dist <= self.type.sight
            and world.can_see(self.x, self.z, world.player_x, world.player_z)
        )

    def _idle(self, dt, world, dist):
        if self._notices(world, dist):
            return self._switch("chase")
        if self.type.rooted or self.type.lurk:
            return
        # Ruby used nil both for "not decided yet" and "stand still", so a standing enemy re-rolls every tick.
        if self._wander_dir is None or self.state_t > 2.5:
            self.state_t = 0.0
            far = math.hypot(self.home_x - self.x, self.home_z - self.z) > 3.0
            if far:
                self._wander_dir = math.atan2(self.home_z - self.z, self.home_x - self.x)
            else:
                self._wander_dir = None if self._rng.random() < 0.5 else self._rng.random() * math.pi * 2
        if self._wander_dir is None:
            return
        self.yaw = self._wander_dir
        self._step(world, math.cos(self.yaw), math.sin(self.yaw), self.type.speed * 0.35 * dt)

    def _chase(self, dt, world, dist):
        if not world.player_alive:
            return self._switch("idle")
        give_up = GIVE_UP if self.type.lurk else self.type.sight * 1.5
        if dist > give_up:
            return self._switch("idle")
        self.face(world.player_x, world.player_z, dt)
        t = self.type
        move = self._pick_move(world, dist)
        if move:
            return self._begin_windup(move)
        if t.bite_reach and dist <= t.bite_reach:
            return self._begin_windup("bite")
        in_range = dist <= t.reach
        if t.ranged and in_range:
            in_range = world.can_see(self.x, self.z, world.player_x, world.player_z)
        # A slow turner must come round to face you before it can swing.
        squared_up = t.turn_rate is None or self._facing(world.player_x, world.player_z)
        if in_range and squared_up and (not t.ranged or t.bite_reach or dist >= 2.5):
            return self._begin_windup("shot" if t.ranged else "melee")
        if t.rooted:
            return
        direction = -1.0 if self.type.ranged and dist < 4.0 else 1.0
        speed = self.type.speed * (1.25 if self.enraged else 1.0)
        self._step(world, math.cos(self.yaw) * direction, math.sin(self.yaw) * direction, speed * dt)

    def _pick_move(self, world, dist):
        """Chooses a boss special attack for the range you are at, or None for a plain bite."""
        ready = [m for m, cd in self.cooldowns.items() if cd <= 0]
        if not ready:
            return None
        reach = self.type.reach
        options = []
        if "sweep" in ready and dist <= reach + SWEEP_REACH * 0.8:
            options.append("sweep")
        seen = world.can_see(self.x, self.z, world.player_x, world.player_z)
        if "web" in ready and seen and reach + 1.0 <= dist <= 12:
            options.append("web")
        if "pounce" in ready and seen and 4.5 <= dist <= 11:
            options.append("pounce")
        if "cinders" in ready and seen and 3.5 <= dist <= 14:
            options.append("cinders")
        if not options:
            return None
        # Up close a sweep is only sometimes chosen, so the plain bite stays in the mix.
        if options == ["sweep"] and self._rng.random() < 0.5:
            self.cooldowns["sweep"] = 1.0
            return None
        move = self._rng.choice(options)
        self.cooldowns[move] = MOVES[move][1] * (0.7 if self.enraged else 1.0)
        return move

    def _begin_windup(self, kind):
        self._switch("windup")
        self.attack_kind = kind

    def _windup(self, world, dt=None):
        windup = self.windup_time * (0.8 if self.enraged else 1.0)
        if self.state_t < windup * 0.6:
            self.face(world.player_x, world.player_z, dt)
        if self.state_t >= windup:
            kind = self.attack_kind
            self._switch("attack")
            self.attack_kind = kind
            if kind == "pounce":
                # It springs at where you stand now; step aside at the last moment to dodge.
                self._target = (world.player_x, world.player_z)

    def _attack(self, world, dist, dt=0.0):
        kind = self.attack_kind
        if kind == "pounce":
            return self._pounce(world, dt)
        if not self._struck:
            self._struck = True
            if kind in ("shot", "web", "cinders"):
                world.enemy_fire(self, kind)
            elif kind == "summon":
                world.summon(self, self.type.brood, 2)
            elif kind == "sweep":
                if dist <= self.type.reach + SWEEP_REACH:
                    world.enemy_strike(self, MOVES["sweep"][2])
            elif dist <= self._strike_reach() + 0.3 and self._facing(world.player_x, world.player_z):
                world.enemy_strike(self)
        if self.state_t >= (0.35 if kind == "sweep" else 0.2):
            self._switch("recover")

    def _pounce(self, world, dt):
        tx, tz = self._target
        dx = tx - self.x
        dz = tz - self.z
        d = math.hypot(dx, dz)
        landed = d < 0.4 or self.state_t >= POUNCE_TIME
        if not landed:
            step = min(POUNCE_SPEED * dt, d)
            ox, oz = self.x, self.z
            world.move_enemy(self, dx / d * step, dz / d * step)
            # Hit a wall (or you): the leap ends here.
            landed = math.hypot(self.x - ox, self.z - oz) < step * 0.3
        if landed:
            dist = math.hypot(world.player_x - self.x, world.player_z - self.z)
            if dist <= self.radius + 1.2:
                world.enemy_strike(self, MOVES["pounce"][2])
            self._switch("recover")

    def _strike_reach(self):
        return self.type.bite_reach if self.attack_kind == "bite" else self.type.reach

    def _facing(self, px, pz):
        return abs(_wrap(math.atan2(pz - self.z, px - self.x) - self.yaw)) < 0.9

    def _step(self, world, dx, dz, amount):
        world.move_enemy(self, dx * amount, dz * amount)
