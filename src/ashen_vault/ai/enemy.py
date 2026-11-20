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
    "kindle": (1.2, 0.0, 0.0),  # raises his blade and sets it alight (once, at half HP)
    "combo": (0.6, 5.0, 0.6),  # three swings in a row; back off to break the chain
    "slam": (1.0, 7.0, 1.1),  # an overhead slam whose shockwave hits all around
    "eruption": (1.1, 8.0, 0.9),  # plants the blade: fire bursts up under you (second phase)
    "hook": (0.8, 6.0, 0.4),  # a hooked chain that drags you in
    "breath": (1.0, 7.0, 0.8),  # rakes a line of fire along the floor toward you and past you
    "dive": (0.9, 8.0, 1.2),  # swoops low straight through where you stood
    # The Ashen Sexton's own: a cone of grave dust breathed out at you, an urn of ashes dashed down
    # so the ash billows out all round, a spadeful of grave ash flung in a fan, grasping hands of ash
    # bursting up in a line toward you, two whirlwinds of ash raised to hunt you, and (second phase)
    # the knell, two rings of embers tolled outward.
    "exhale": (0.9, 6.0, 0.7),
    "ashfall": (1.1, 7.0, 1.0),
    "dust_devil": (1.0, 12.0, 0.5),
    "spadeful": (0.8, 6.0, 0.4),
    "grasp": (1.0, 7.0, 0.7),
    "knell": (1.3, 9.0, 0.6),
    # The Shrouded Mourner's own: a ball of grave-fire kindled in its bony palm and thrown.
    "fireball": (0.9, 5.0, 0.8),
    # The Sodden Pall's own: a fan of bile spat from the mouth in its folds; and (second phase) the
    # engulf, a lurch along the floor hem-first that flows over you if it passes over you, and clots of
    # itself sloughed off to crawl at you.
    "bile": (0.9, 6.0, 0.55),
    "engulf": (1.3, 10.0, 1.25),
    "shed": (1.1, 13.0, 0.0),
    # Mother Gnawl's own: a lash of her tail at whoever stands behind her, a piercing squeal that
    # staggers all round, a burrow (she sinks into the muck, tunnels after you and bursts up under
    # you in a ring of filth).
    "tail_lash": (0.45, 3.5, 0.8),
    "squeal": (0.8, 9.0, 0.3),
    "burrow": (0.6, 10.0, 1.2),
    # Vesperholm's: a lance of moon-frost thrown from afar (a fan of three from the Duchess), and a
    # blink, a step through the moonlight to reappear behind you and strike. The Duchess's own: shafts
    # of moonlight falling where you stand and where you would step, and (second phase) the moonfall,
    # rings of them raining down round you.
    "frost_lance": (0.8, 6.0, 0.7),
    "blink": (0.6, 8.0, 1.0),
    "moonbeam": (0.9, 7.0, 0.9),
    "moonfall": (1.2, 11.0, 0.8),
    # Old Harrowmere's: a sexton's toll, its staff raised so its mortar-light wakes whatever sleeps in
    # stone round it; the
    # Keystone's (second phase) quake, a stamp whose ring of shock runs out along the floor (it passes
    # under whoever stands in close), and a block of masonry hurled from afar.
    "toll": (0.9, 14.0, 0.0),
    "quake": (1.3, 9.0, 1.1),
    "hurl": (1.0, 6.0, 0.9),
    # The Keystone's mortar-light: a slab of a forearm brought down overhead in a great burst of it
    # before it (and the shards it scatters), and (second phase) a beam of it raked along the floor from
    # its heart, shards of its shell rained down round you, or its fists driven down at its feet so
    # rings of the light run out from it.
    "slab_smash": (1.2, 6.0, 1.2),
    "core_beam": (1.0, 7.0, 0.8),
    "shard_rain": (1.4, 11.0, 0.8),
    "core_nova": (1.5, 12.0, 1.0),
}
COMBO_SWINGS = 3
COMBO_GAP = 0.45  # seconds between the swings of a combo (scaled by a type's `tempo`: `Enemy.combo_gap`)
MIN_WINDUP = 0.3  # a quick foe's tempo never cuts a windup shorter than this: the tell stays readable
COMBO_TURN = 2.0  # rad/s he can turn while chaining swings
SLAM_RADIUS = 4.0  # the slam's shockwave reaches this far, from any side
HOOK_RANGE = (3.0, 7.0)  # distances a hook is thrown from
HOOK_PULL = 2.5  # metres a hook drags you toward the thrower
SWEEP_REACH = 1.0  # extra reach of a sweep over the type's normal reach
POUNCE_SPEED = 13.0  # m/s through the air
POUNCE_TIME = 0.5  # longest a pounce can fly
DIVE_SPEED = 11.0  # m/s along a swoop
DIVE_TIME = 1.1  # longest a swoop lasts
DIVE_OVERSHOOT = 3.0  # metres a swoop carries on past where you stood
DIVE_HIT = 1.1  # a swoop passing this close (beyond its radius) strikes you, once
BREATH_RANGE = (3.0, 10.0)  # distances a gout of breath is loosed from
SLAB_REACH = 4.5  # metres before the Keystone its slab of a forearm comes down
SLAB_SMASH_RANGE = (2.5, 6.5)  # distances it brings its slab down from
SHARD_RAIN_RANGE = 16.0  # it rains shards on you from anywhere up to this far
CORE_NOVA_RANGE = 9.0  # it drives its fists down only with you this close: its rings would miss you
DIVE_RANGE = (5.0, 13.0)
# A flyer (`EnemyType.fly`) holds its cruising height and drops to STRIKE_ALT over a swoop's windup and
# its swoop. Once that first swoop is spent it lands (`Enemy.landed`) and fights on foot from then on,
# within a blade's reach, at LAND_PACE of its speed on the wing; dead, it falls like a stone.
STRIKE_ALT = 0.3
DESCEND_RATE = 7.0  # m/s it drops into a swoop
CLIMB_RATE = 2.5  # m/s it climbs back to its cruising height
FALL_RATE = 14.0  # m/s a slain flyer drops
LAND_PACE = 0.6  # a landed flyer stalks you at this share of its speed on the wing
SPADEFUL_RANGE = (3.5, 11.0)
GRASP_RANGE = (2.5, 10.0)
FIREBALL_RANGE = (2.5, 10.0)
BILE_RANGE = (3.0, 11.0)
ENGULF_RANGE = (3.5, 10.0)  # distances the Pall lurches at you from
ENGULF_SPEED = 8.0  # m/s along its lurch
ENGULF_TIME = 1.4  # longest a lurch lasts
ENGULF_OVERSHOOT = 1.5  # metres it lurches on past where you stood
ENGULF_HIT = 0.6  # a lurch passing this close (beyond its radius) flows over you, once
SHED_RANGE = 12.0  # it sheds its gobbets only while you are this close
# The lunges along a straight line: speed (m/s), longest (s), overshoot past you (m), hit reach (m).
LUNGES = {
    "dive": (DIVE_SPEED, DIVE_TIME, DIVE_OVERSHOOT, DIVE_HIT),
    "engulf": (ENGULF_SPEED, ENGULF_TIME, ENGULF_OVERSHOOT, ENGULF_HIT),
}
FROST_LANCE_RANGE = (3.0, 12.0)
BLINK_RANGE = (3.0, 10.0)  # it steps through the moonlight only while you keep your distance
MOONBEAM_RANGE = (2.0, 12.0)
MOONFALL_RANGE = 12.0
TOLL_RANGE = (3.0, 14.0)  # a sexton rings its bell only while you keep this far off and in sight
TOLL_RADIUS = 14.0  # metres round the bell that stone sleepers wake
QUAKE_RANGE = 9.0  # the Keystone stamps only while you are this close
QUAKE_SAFE = 1.2  # metres beyond its body the ring has not yet risen: stand in close and it passes
QUAKE_RADIUS = 8.0  # metres the ring of shock runs out
HURL_RANGE = (5.0, 16.0)
SQUEAL_RADIUS = 4.5  # metres her squeal staggers you, from any side
BURROW_RANGE = (4.0, 9.0)  # distances she burrows after you from
BURROW_TIME = 1.2  # seconds she tunnels under the muck, out of reach
BURROW_SPEED = 1.3  # times her chase speed she tunnels at: step aside as she comes up and she misses
BURST_TIME = 0.45  # seconds she rears up out of the muck once she bursts
BURROW_RADIUS = 2.2  # metres round where she bursts up that the filth catches you
TAIL_ARC = 1.9  # radians off her facing beyond which you stand in reach of her tail
TAIL_REACH = 1.0  # extra reach of her tail over her bite
EXHALE_REACH = 5.0  # metres the Sexton's breath of grave dust carries
EXHALE_CONE = 0.45  # half-angle (radians) of that breath: step aside out of it
ASHFALL_RADIUS = 3.8  # metres the ash of a dashed urn billows out, from any side
DEVIL_RANGE = (4.0, 13.0)  # distances the Sexton raises its whirlwinds of ash from
KNELL_RANGE = 12.0  # it tolls only while you are this close
KNELL_GAP = 0.5  # seconds between the knell's two rings
TRAIL_HOLD = 0.6  # seconds the boss bar's damage trail waits before draining
TRAIL_RATE = 0.35  # fraction of max HP the trail drains per second
VEIL_NOTICE = 1.8  # a foe notices you through a Veil of Mist only this close
VEIL_LOSE = 4.0  # a chaser loses you in the mist beyond this
STATUS_TICK = 1.0  # seconds between the bites of poison or fire
FLASH_TIME = 0.15  # seconds a body glows red after any direct blow, staggered or not
# A boss's entrance (`EnemyType.rise`): one of ash waits as a smouldering heap until you step into its
# lair, then builds itself from the feet up out of the burning ash; a statue cracks and tears free.
ASH_RISE = 3.0  # seconds, the first time you meet it
ASH_RISE_AGAIN = 1.5  # seconds, when you come back through its fog
STATUE_RISE = 2.2
STATUE_BURST = 0.55  # share of a statue's rise at which its stone skin bursts off


# Seconds a move holds its attack pose before recovering (a plain blow: 0.2).
ATTACK_TIMES = {
    "sweep": 0.35,
    "slam": 0.45,
    "kindle": 0.6,
    "eruption": 0.5,
    "breath": 0.6,
    "grasp": 0.6,
    "spadeful": 0.35,
    "exhale": 0.6,
    "ashfall": 0.45,
    "dust_devil": 0.5,
    "tail_lash": 0.3,
    "squeal": 0.5,
    "shed": 0.5,
    "frost_lance": 0.3,
    "moonbeam": 0.5,
    "moonfall": 0.6,
    "toll": 0.8,
    "quake": 0.5,
    "hurl": 0.35,
    "slab_smash": 0.5,
    "core_beam": 0.6,
    "shard_rain": 0.6,
    "core_nova": 0.7,
}


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


class Enemy:
    """Enemy state machine. `world` must provide:
    player_x, player_z, player_alive, can_see(ax, az, bx, bz),
    move_enemy(enemy, dx, dz), enemy_strike(enemy, mult), enemy_fire(enemy, kind),
    for bosses with a brood, summon(enemy, type_id, count); for bosses with a rage, boss_rage(enemy),
    slam(enemy) and eruption(enemy); for hook throwers, hook(enemy, mult, pull);
    for fire-breathers, breath(enemy); for the Sexton, grasp(enemy) and knell(enemy, wave); for
    Mother Gnawl, tail_lash(enemy), squeal(enemy) and burrow_burst(enemy); for the Sodden Pall,
    engulf(enemy), shed(enemy) and can_shed(enemy); for Vesperholm's blinkers, blink(enemy); for the
    Duchess, moonbeam(enemy) and moonfall(enemy); for the Keystone, quake(enemy), slab_smash(enemy),
    core_beam(enemy), shard_rain(enemy) and core_nova(enemy). Optional, for twin bosses: rouse_twin(enemy), twin_fallen(enemy)
    and twin_busy(enemy); for bosses that rise from ash, rise_time(enemy) (seconds, or None while it
    should stay a heap; without it the heap rises when it notices you); level_with(enemy), False while
    you are out of its reach above or below (riding a lift past it), so it does not swing at you.
    """

    def __init__(self, type_, x, z, yaw=0.0, marker=None, rng=None, loot=None, key=None, look=None):
        self.type = type_
        self.look = look  # a model variant from the map (`model=`): a mimic's iron disguise
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
        self.state = (
            "dormant"
            if type_.ambush
            else "perched"
            if type_.perch
            else "ashes"
            if type_.rise == "ash"
            else "idle"
        )
        self.state_t = 0.0
        self.rise_time = 0.0  # how long the current rise takes
        self.anim_t = 0.0
        self.flash_t = 0.0  # counts down after a direct blow: the red hit flash
        self._wander_dir = None
        self._struck = False
        # "melee", "shot", "bite" or a boss move: what the current windup will turn into.
        self.attack_kind = None
        # Boss moves start part-way cooled down so a fight doesn't open with all of them.
        self.cooldowns = {m: MOVES[m][1] * 0.4 for m in type_.moves}
        self.phase2 = False  # past half HP: called its brood or kindled its rage
        self._target = None  # where a pounce is headed
        # Lingering harm: kind ("poison", "burn") -> [seconds left, HP per tick, time to next tick].
        self.status = {}
        # A flyer's height over `ground`, the floor of the last solid tile it crossed (set by the world).
        self.alt = type_.fly or 0.0
        self.ground = None
        self.landed = False  # a flyer that has spent its swoop and come down to fight on foot

    @property
    def aloft(self):
        """Whether it is a flyer still on the wing (it has not landed yet)."""
        return self.type.fly is not None and not self.landed

    @property
    def alive(self):
        return self.state != "dead"

    @property
    def hit_sound(self):
        """The sound a blow on it makes: its material's (an iron-chest mimic rings like iron)."""
        return "hit_iron" if self.look == "iron" else f"hit_{self.type.material}"

    @property
    def flashing(self):
        """Whether the body glows red: just struck (even when the blow didn't stagger it), or reeling."""
        return self.flash_t > 0 or self.state == "hurt"

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
        self.flash_t = max(self.flash_t - dt, 0.0)
        self._update_trail(dt)
        if self.type.fly is not None:
            self.fly(dt)
        if self.state in ("dead", "dormant"):
            return
        dist = math.hypot(world.player_x - self.x, world.player_z - self.z)
        if self.state == "perched":
            if self._notices(world, dist):
                self.rouse()
                if hasattr(world, "rouse_twin"):
                    world.rouse_twin(self)
            return
        if self.state == "ashes":
            ask = getattr(world, "rise_time", None)
            seconds = ask(self) if ask else (ASH_RISE if self._notices(world, dist) else None)
            if seconds:
                self.face(world.player_x, world.player_z)  # the heap has no front: it forms facing you
                self.begin_rise(seconds)
            return
        if self.state == "rising":
            if self.type.rise == "ash":
                self.face(world.player_x, world.player_z, dt)  # and keeps turning to you as you move
            if self.state_t >= self.rise_time:
                self.face(world.player_x, world.player_z)
                self._switch("chase")
            return
        for m in self.cooldowns:
            self.cooldowns[m] = max(self.cooldowns[m] - dt, 0.0)
        if self._should_turn(world):
            self.phase2 = True
            for m in self.type.phase_moves:
                self.cooldowns[m] = MOVES[m][1] * 0.3
            self.face(world.player_x, world.player_z)
            return self._begin_windup("summon" if self.type.brood else "kindle")
        s = self.state
        if s == "idle":
            self._idle(dt, world, dist)
        elif s == "chase":
            self._chase(dt, world, dist)
        elif s == "windup":
            self._windup(world, dt)
        elif s == "attack":
            self._attack(world, dist, dt)
        elif s in ("recover", "hurt") and self.state_t >= (0.35 if s == "hurt" else self.recover_time):
            self._switch("chase")

    @property
    def windup_time(self):
        """Seconds the current windup lasts: the move's (or the type's) own, quickened by the type's
        `tempo` and by a boss's rage, but never below MIN_WINDUP (nor its own time, if that is less)."""
        base = MOVES[self.attack_kind][0] if self.attack_kind in MOVES else self.type.windup
        quick = base * self.type.tempo * (0.8 if self.enraged else 1.0)
        return max(quick, min(base, MIN_WINDUP))

    @property
    def recover_time(self):
        return self.type.recover * self.type.tempo

    @property
    def combo_gap(self):
        """Seconds between the swings of its combo."""
        return COMBO_GAP * self.type.tempo

    def flight_target(self):
        """The height a flyer heads for: down to strike over a swoop, its cruising height otherwise,
        the ground once it has landed, and nowhere but down once it is dead."""
        if not self.alive:
            return -math.inf
        if self.landed:
            return 0.0
        if self.state in ("windup", "attack") and self.attack_kind == "dive":
            return STRIKE_ALT
        return self.type.fly

    def fly(self, dt):
        """Eases a flyer's height toward `flight_target`: it drops fast into a swoop, climbs back
        slower, and falls when slain (the world stops it on whatever floor lies under it)."""
        target = self.flight_target()
        if target < self.alt:
            rate = FALL_RATE if not self.alive else DESCEND_RATE
            self.alt = max(self.alt - rate * dt, target)
        else:
            self.alt = min(self.alt + CLIMB_RATE * dt, target)

    def _cooldown(self, move):
        """Seconds before `move` comes round again: quicker for a quick type and in a boss's rage."""
        return MOVES[move][1] * self.type.tempo * (0.7 if self.enraged else 1.0)

    @property
    def enraged(self):
        """A boss in its second phase fights harder: quicker moves, shorter cooldowns."""
        return self.phase2

    def _should_turn(self, world=None):
        """Half HP: a boss with a brood calls it, one with a rage kindles it. Once only. A twin
        instead turns when the other one falls."""
        if self.phase2 or self.state not in ("chase", "recover"):
            return False
        if self.type.twin:
            fallen = getattr(world, "twin_fallen", None)
            return bool(fallen and fallen(self))
        return (self.type.brood is not None or self.type.rage is not None) and self.hp <= self.type.hp / 2

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

    def afflict(self, kind, seconds, per_tick):
        """Poisons or sets fire to the enemy. A fresh dose renews the longer time and the harder bite."""
        if not self.alive:
            return
        old = self.status.get(kind)
        if old:
            old[0] = max(old[0], seconds)
            old[1] = max(old[1], per_tick)
        else:
            self.status[kind] = [seconds, per_tick, STATUS_TICK]

    @property
    def afflicted(self):
        """The status to show: fire over poison, or None."""
        return "burn" if "burn" in self.status else "poison" if "poison" in self.status else None

    def status_tick(self, dt):
        """Advances poison and fire; returns the HP they take this frame (apply it without a stagger)."""
        if not self.alive:
            self.status.clear()
            return 0
        dmg = 0
        for kind, st in list(self.status.items()):
            st[2] -= dt
            if st[2] <= 0:
                st[2] += STATUS_TICK
                dmg += st[1]
            st[0] -= dt
            if st[0] <= 0:
                del self.status[kind]
        return dmg

    def take_hit(self, amount, poise_mult=1.0, stagger=True):
        """Applies damage and returns True if the hit was fatal. Heavy blows (`poise_mult`)
        stagger tougher foes; lingering harm (`stagger=False`) never does."""
        if not self.alive or self.unseen:
            return False
        was_dormant = self.dormant or self.perched
        self.hp -= amount
        self._trail_hold = TRAIL_HOLD
        if stagger:  # a direct blow (not a poison or fire tick) always shows
            self.flash_t = FLASH_TIME
        if self.hp <= 0:
            self.hp = 0
            self._switch("dead")
            return True
        if self.perched:  # struck on its perch: the statue cracks open
            self.rouse()
        elif stagger and amount * poise_mult >= self.type.poise:
            self._switch("hurt")
        elif was_dormant:
            self._switch("chase")
        return False

    @property
    def dormant(self):
        return self.state == "dormant"

    @property
    def perched(self):
        return self.state == "perched"

    @property
    def unseen(self):
        """Still a heap of ash, not yet whole, or tunnelling under the muck: nothing can strike it."""
        return self.state in ("ashes", "rising") or self.burrowed

    @property
    def burrowed(self):
        """Under the muck mid-burrow: out of reach and in no one's way, only a ripple shows."""
        return self.state == "attack" and self.attack_kind == "burrow" and self.state_t < BURROW_TIME

    @property
    def rise_progress(self):
        """0 as its rise begins, 1 once it stands whole (and ever after); 0 while it waits."""
        if self.state == "rising":
            return min(self.state_t / self.rise_time, 1.0) if self.rise_time > 0 else 1.0
        return 0.0 if self.state in ("ashes", "perched") else 1.0

    def begin_rise(self, seconds):
        self._switch("rising")
        self.rise_time = seconds

    def rouse(self):
        """A perched statue comes to life: it cracks and tears free of its perch, then gives chase."""
        if self.perched:
            self.begin_rise(STATUE_RISE)

    def alert(self):
        """Something called it (a sexton's bell): an idle foe gives chase at once."""
        if self.state == "idle":
            self._switch("chase")

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

    def _veiled(self, world, dist, reach):
        """You are lost in a Veil of Mist beyond `reach`. Bosses see through it."""
        return getattr(world, "player_hidden", False) and not self.type.boss and dist > reach

    def _notices(self, world, dist):
        return (
            world.player_alive
            and dist <= self.type.sight
            and not self._veiled(world, dist, VEIL_NOTICE)
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
        if dist > give_up or self._veiled(world, dist, VEIL_LOSE):
            return self._switch("idle")
        if self._lash_ready(world, dist):  # caught slipping round behind her: before she turns
            self.cooldowns["tail_lash"] = self._cooldown("tail_lash")
            return self._begin_windup("tail_lash")
        self.face(world.player_x, world.player_z, dt)
        t = self.type
        move = self._pick_move(world, dist)
        if move:
            return self._begin_windup(move)
        # Riding a lift past it, you are out of its reach above or below: it waits rather than swing.
        level = getattr(world, "level_with", None)
        level = level is None or level(self)
        if t.bite_reach and dist <= t.bite_reach and level:
            return self._begin_windup("bite")
        in_range = dist <= t.reach and (level or t.ranged)
        if t.ranged and in_range:
            in_range = world.can_see(self.x, self.z, world.player_x, world.player_z)
        # A slow turner must come round to face you before it can swing.
        squared_up = t.turn_rate is None or self._facing(world.player_x, world.player_z)
        if in_range and squared_up and (not t.ranged or t.bite_reach or dist >= 2.5):
            return self._begin_windup("shot" if t.ranged else "melee")
        if t.rooted:
            return
        # A shooter keeps its distance; so does a flyer over your head, out to where it can swoop again.
        aloft = self.aloft and not level and dist < DIVE_RANGE[0]
        direction = -1.0 if (self.type.ranged and dist < 4.0) or aloft else 1.0
        speed = self.type.speed * (1.25 if self.enraged else 1.0) * (LAND_PACE if self.landed else 1.0)
        self._step(world, math.cos(self.yaw) * direction, math.sin(self.yaw) * direction, speed * dt)

    def behind_me(self, px, pz):
        """Whether (px, pz) lies in the arc behind its back that a tail lash sweeps."""
        return abs(_wrap(math.atan2(pz - self.z, px - self.x) - self.yaw)) > TAIL_ARC

    def tail_reach(self):
        return self.type.reach + TAIL_REACH

    def _lash_ready(self, world, dist):
        """A tail lasher whips round at you when you stand behind it, in its tail's reach."""
        return (
            self.cooldowns.get("tail_lash", 1.0) <= 0
            and dist <= self.tail_reach()
            and self.behind_me(world.player_x, world.player_z)
        )

    def _pick_move(self, world, dist):
        """Chooses a boss special attack for the range you are at, or None for a plain bite."""
        ready = [m for m, cd in self.cooldowns.items() if cd <= 0]
        if not ready:
            return None
        busy = getattr(world, "twin_busy", None)
        if busy and busy(self):
            return None  # its twin is mid-move: it waits its turn
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
        if "combo" in ready and dist <= reach + 0.3:
            options.append("combo")
        if "slam" in ready and dist <= SLAM_RADIUS * 0.75:
            options.append("slam")
        if "eruption" in ready and seen and 2.5 <= dist <= 12:
            options.append("eruption")
        if "hook" in ready and seen and HOOK_RANGE[0] <= dist <= HOOK_RANGE[1]:
            options.append("hook")
        if "breath" in ready and seen and BREATH_RANGE[0] <= dist <= BREATH_RANGE[1]:
            options.append("breath")
        if "dive" in ready and seen and DIVE_RANGE[0] <= dist <= DIVE_RANGE[1]:
            options.append("dive")
        if "spadeful" in ready and seen and SPADEFUL_RANGE[0] <= dist <= SPADEFUL_RANGE[1]:
            options.append("spadeful")
        if "grasp" in ready and seen and GRASP_RANGE[0] <= dist <= GRASP_RANGE[1]:
            options.append("grasp")
        if "exhale" in ready and seen and dist <= EXHALE_REACH * 0.8:
            options.append("exhale")
        if "ashfall" in ready and dist <= ASHFALL_RADIUS * 0.8:
            options.append("ashfall")
        if "dust_devil" in ready and seen and DEVIL_RANGE[0] <= dist <= DEVIL_RANGE[1]:
            options.append("dust_devil")
        if "fireball" in ready and seen and FIREBALL_RANGE[0] <= dist <= FIREBALL_RANGE[1]:
            options.append("fireball")
        if "bile" in ready and seen and BILE_RANGE[0] <= dist <= BILE_RANGE[1]:
            options.append("bile")
        if "engulf" in ready and seen and ENGULF_RANGE[0] <= dist <= ENGULF_RANGE[1]:
            options.append("engulf")
        if "shed" in ready and dist <= SHED_RANGE and world.can_shed(self):
            options.append("shed")
        if "burrow" in ready and BURROW_RANGE[0] <= dist <= BURROW_RANGE[1]:
            options.append("burrow")
        if "squeal" in ready and dist <= SQUEAL_RADIUS * 0.8:
            options.append("squeal")
        if "frost_lance" in ready and seen and FROST_LANCE_RANGE[0] <= dist <= FROST_LANCE_RANGE[1]:
            options.append("frost_lance")
        if "blink" in ready and seen and BLINK_RANGE[0] <= dist <= BLINK_RANGE[1]:
            options.append("blink")
        if "moonbeam" in ready and seen and MOONBEAM_RANGE[0] <= dist <= MOONBEAM_RANGE[1]:
            options.append("moonbeam")
        if "moonfall" in ready and dist <= MOONFALL_RANGE:
            options.append("moonfall")
        if "slab_smash" in ready and SLAB_SMASH_RANGE[0] <= dist <= SLAB_SMASH_RANGE[1]:
            options.append("slab_smash")
        if "core_beam" in ready and seen and BREATH_RANGE[0] <= dist <= BREATH_RANGE[1]:
            options.append("core_beam")
        if "shard_rain" in ready and seen and dist <= SHARD_RAIN_RANGE:
            options.append("shard_rain")
        if "core_nova" in ready and dist <= CORE_NOVA_RANGE:
            options.append("core_nova")
        if "toll" in ready and seen and TOLL_RANGE[0] <= dist <= TOLL_RANGE[1] and world.can_toll(self):
            options.append("toll")
        if "quake" in ready and dist <= QUAKE_RANGE:
            options.append("quake")
        if "hurl" in ready and seen and HURL_RANGE[0] <= dist <= HURL_RANGE[1]:
            options.append("hurl")
        if "knell" in ready and dist <= KNELL_RANGE:
            options.append("knell")
        if not options:
            return None
        # Up close a special is only sometimes chosen, so the plain blow stays in the mix.
        close = {"sweep", "combo", "slam", "exhale", "ashfall", "squeal"}
        if set(options) <= close and self._rng.random() < 0.5:
            for m in options:
                self.cooldowns[m] = 1.0
            return None
        move = self._rng.choice(options)
        self.cooldowns[move] = self._cooldown(move)
        return move

    def _begin_windup(self, kind):
        self._switch("windup")
        self.attack_kind = kind

    def _windup(self, world, dt=None):
        windup = self.windup_time
        if self.state_t < windup * 0.6 and self.attack_kind != "tail_lash":  # a lash keeps its back to you
            self.face(world.player_x, world.player_z, dt)
        if self.state_t >= windup:
            kind = self.attack_kind
            self._switch("attack")
            self.attack_kind = kind
            if kind == "pounce":
                # It springs at where you stand now; step aside at the last moment to dodge.
                self._target = (world.player_x, world.player_z)
            elif kind in LUNGES:
                # It swoops (or surges) through where you stand now and carries on past.
                overshoot = LUNGES[kind][2]
                dx, dz = world.player_x - self.x, world.player_z - self.z
                d = math.hypot(dx, dz) or 1.0
                self._target = (world.player_x + dx / d * overshoot, world.player_z + dz / d * overshoot)

    def _attack(self, world, dist, dt=0.0):
        kind = self.attack_kind
        if kind == "pounce":
            return self._pounce(world, dt)
        if kind == "combo":
            return self._combo(world, dist, dt)
        if kind in LUNGES:
            return self._dive(world, dt)
        if kind == "knell":
            return self._knell(world)
        if kind == "blink":
            return self._blink(world)
        if kind == "burrow":
            return self._burrow(world, dt)
        if not self._struck and self.state_t >= self.type.impact:  # a heavy swing follows through first
            self._struck = True
            if kind in ("shot", "web", "cinders", "spadeful", "fireball", "bile", "frost_lance", "hurl"):
                world.enemy_fire(self, kind)
            elif kind == "summon":
                world.summon(self, self.type.brood, 2)
            elif kind == "kindle":
                world.boss_rage(self)
            elif kind == "slam":
                world.slam(self)
                if dist <= SLAM_RADIUS:
                    world.enemy_strike(self, MOVES["slam"][2])
            elif kind == "eruption":
                world.eruption(self)
            elif kind == "breath":
                world.breath(self)
            elif kind == "grasp":
                world.grasp(self)
            elif kind == "exhale":
                world.exhale(self)
            elif kind == "ashfall":
                world.ashfall(self)
            elif kind == "dust_devil":
                world.dust_devils(self)
            elif kind == "tail_lash":
                world.tail_lash(self)
            elif kind == "squeal":
                world.squeal(self)
            elif kind == "shed":
                world.shed(self)
            elif kind == "moonbeam":
                world.moonbeam(self)
            elif kind == "moonfall":
                world.moonfall(self)
            elif kind == "toll":
                world.toll(self)
            elif kind == "quake":
                world.quake(self)
            elif kind == "slab_smash":
                world.slab_smash(self)
            elif kind == "core_beam":
                world.core_beam(self)
            elif kind == "shard_rain":
                world.shard_rain(self)
            elif kind == "core_nova":
                world.core_nova(self)
            elif kind == "hook":
                if dist <= HOOK_RANGE[1] + 0.5 and self._facing(world.player_x, world.player_z):
                    world.hook(self, MOVES["hook"][2], HOOK_PULL)
            elif kind == "sweep":
                if dist <= self.type.reach + SWEEP_REACH:
                    world.enemy_strike(self, MOVES["sweep"][2])
            elif dist <= self._strike_reach() + 0.3 and self._facing(world.player_x, world.player_z):
                world.enemy_strike(self)
        if self.state_t >= ATTACK_TIMES.get(kind, 0.2) + self.type.impact:
            self._switch("recover")

    def _knell(self, world):
        """Two rings of embers, KNELL_GAP apart, the second turned half a gap from the first: stand
        in a gap of the first, then step aside for the second, or keep far off and strafe."""
        due = 1 if self.state_t < KNELL_GAP else 2
        while int(self._struck) < due:
            world.knell(self, int(self._struck))
            self._struck += 1
        if self.state_t >= KNELL_GAP + 0.3:
            self._switch("recover")

    def _blink(self, world):
        """It steps through the moonlight: gone from where it stood and, the same moment, behind you
        (or beside you, where a wall is in the way), already winding up its blow. Turn and meet it."""
        if not self._struck:
            self._struck = True
            world.blink(self)
            self.face(world.player_x, world.player_z)
            self._begin_windup("melee")

    def _burrow(self, world, dt):
        """Under the muck for BURROW_TIME, tunnelling after you no faster than BURROW_SPEED times her
        chase; then she bursts up where she has got to, and rears there for BURST_TIME."""
        if self.state_t < BURROW_TIME:
            dx, dz = world.player_x - self.x, world.player_z - self.z
            d = math.hypot(dx, dz)
            if d > 1e-6:
                speed = self.type.speed * (1.25 if self.enraged else 1.0) * BURROW_SPEED
                step = min(speed * dt, d)
                self.yaw = math.atan2(dz, dx)
                world.move_enemy(self, dx / d * step, dz / d * step)
            return
        if not self._struck:
            self._struck = True
            world.burrow_burst(self)
        if self.state_t >= BURROW_TIME + BURST_TIME:
            self._switch("recover")

    @property
    def combo_swing(self):
        """Which swing (0, 1, 2) of a combo is under way."""
        return min(int(self.state_t / self.combo_gap), COMBO_SWINGS - 1)

    def _combo(self, world, dist, dt):
        """Three swings, `combo_gap` apart. Each must reach you and face you, so stepping back or
        round him breaks the chain; the last one hits hardest. He turns only slowly between swings."""
        want = math.atan2(world.player_z - self.z, world.player_x - self.x)
        diff = _wrap(want - self.yaw)
        step = COMBO_TURN * dt
        self.yaw = want if abs(diff) <= step else self.yaw + math.copysign(step, diff)
        due = min(int(self.state_t / self.combo_gap) + 1, COMBO_SWINGS)
        while int(self._struck) < due:
            self._struck += 1
            if dist <= self.type.reach + 0.3 and self._facing(world.player_x, world.player_z):
                last = self._struck == COMBO_SWINGS
                world.enemy_strike(self, MOVES["combo"][2] * (1.4 if last else 1.0))
        if self.state_t >= self.combo_gap * (COMBO_SWINGS - 1) + 0.25:
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

    def _dive(self, world, dt):
        """A low swoop (or the Pall's lurch) along a straight line: it strikes you once if it passes
        close, and ends at its mark, against a wall, or when its time runs out."""
        kind = self.attack_kind
        speed, longest, _, hit = LUNGES[kind]
        tx, tz = self._target
        dx, dz = tx - self.x, tz - self.z
        d = math.hypot(dx, dz)
        done = d < 0.4 or self.state_t >= longest
        if not done:
            step = min(speed * dt, d)
            ox, oz = self.x, self.z
            world.move_enemy(self, dx / d * step, dz / d * step)
            done = math.hypot(self.x - ox, self.z - oz) < step * 0.3
        if not self._struck:
            near = math.hypot(world.player_x - self.x, world.player_z - self.z)
            if near <= self.radius + hit:
                self._struck = True
                if kind == "engulf":
                    world.engulf(self)
                else:
                    world.enemy_strike(self, MOVES["dive"][2])
        if done:
            self._switch("recover")
            if kind == "dive" and self.type.fly is not None:  # its swoop spent, it comes down to fight
                self.landed = True
                self.cooldowns.pop("dive", None)

    @property
    def diving(self):
        return self.state == "attack" and self.attack_kind == "dive"

    def _strike_reach(self):
        return self.type.bite_reach if self.attack_kind == "bite" else self.type.reach

    def _facing(self, px, pz):
        return abs(_wrap(math.atan2(pz - self.z, px - self.x) - self.yaw)) < 0.9

    def _step(self, world, dx, dz, amount):
        world.move_enemy(self, dx * amount, dz * amount)
