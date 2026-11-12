import math
import random


class Enemy:
    """Enemy state machine. `world` must provide:
    player_x, player_z, player_alive, can_see(ax, az, bx, bz),
    move_enemy(enemy, dx, dz), enemy_strike(enemy), enemy_fire(enemy)
    """

    def __init__(self, type_, x, z, yaw=0.0, marker=None, rng=None):
        self.type = type_
        self.x = x
        self.z = z
        self.home_x = x
        self.home_z = z
        self.yaw = yaw
        self.hp = type_.hp
        self.marker = marker
        self._rng = rng or random.Random()
        self.state = "idle"
        self.state_t = 0.0
        self.anim_t = 0.0
        self._wander_dir = None
        self._struck = False

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def gone(self):
        return self.state == "dead" and self.state_t > 1.6

    @property
    def radius(self):
        return self.type.radius

    @property
    def name(self):
        return self.type.name

    def update(self, dt, world):
        self.anim_t += dt
        self.state_t += dt
        if self.state == "dead":
            return
        dist = math.hypot(world.player_x - self.x, world.player_z - self.z)
        s = self.state
        if s == "idle":
            self._idle(dt, world, dist)
        elif s == "chase":
            self._chase(dt, world, dist)
        elif s == "windup":
            self._windup(world)
        elif s == "attack":
            self._attack(world, dist)
        elif s in ("recover", "hurt") and self.state_t >= (0.35 if s == "hurt" else self.type.recover):
            self._switch("chase")

    def take_hit(self, amount):
        """Applies damage and returns True if the hit was fatal."""
        if not self.alive:
            return False
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self._switch("dead")
            return True
        if amount >= self.type.poise:
            self._switch("hurt")
        return False

    def face(self, tx, tz):
        self.yaw = math.atan2(tz - self.z, tx - self.x)

    def _switch(self, state):
        self.state = state
        self.state_t = 0.0
        self._struck = False

    def _notices(self, world, dist):
        return (
            world.player_alive
            and dist <= self.type.sight
            and world.can_see(self.x, self.z, world.player_x, world.player_z)
        )

    def _idle(self, dt, world, dist):
        if self._notices(world, dist):
            return self._switch("chase")
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
        if dist > self.type.sight * 1.5:
            return self._switch("idle")
        self.face(world.player_x, world.player_z)
        in_range = dist <= self.type.reach
        if self.type.ranged and in_range:
            in_range = world.can_see(self.x, self.z, world.player_x, world.player_z)
        if in_range and (not self.type.ranged or dist >= 2.5):
            return self._switch("windup")
        direction = -1.0 if self.type.ranged and dist < 4.0 else 1.0
        self._step(
            world, math.cos(self.yaw) * direction, math.sin(self.yaw) * direction, self.type.speed * dt
        )

    def _windup(self, world):
        if self.state_t < self.type.windup * 0.6:
            self.face(world.player_x, world.player_z)
        if self.state_t >= self.type.windup:
            self._switch("attack")

    def _attack(self, world, dist):
        if not self._struck:
            self._struck = True
            if self.type.ranged:
                world.enemy_fire(self)
            elif dist <= self.type.reach + 0.3 and self._facing(world.player_x, world.player_z):
                world.enemy_strike(self)
        if self.state_t >= 0.2:
            self._switch("recover")

    def _facing(self, px, pz):
        diff = (math.atan2(pz - self.z, px - self.x) - self.yaw + math.pi) % (2 * math.pi) - math.pi
        return abs(diff) < 0.9

    def _step(self, world, dx, dz, amount):
        world.move_enemy(self, dx * amount, dz * amount)
