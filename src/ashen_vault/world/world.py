"""Runtime state of one loaded map: GPU meshes, props, enemies and projectiles."""

import math
import random
from dataclasses import dataclass

from ashen_vault import map_path
from ashen_vault.ai.enemy import MOVES, SLAM_RADIUS, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.player.player import Player
from ashen_vault.player.spells import Spells
from ashen_vault.render import forge_models, models
from ashen_vault.render.mesh_builder import KINDLING, MeshBuilder
from ashen_vault.util import rround
from ashen_vault.world import collision, elements, loot, relics, shots, terrain
from ashen_vault.world.ash import AshCloud, death_phases
from ashen_vault.world.hazards import (
    CrumbleFloor,
    Eruption,
    FlameJet,
    MagmaVent,
    Pendulum,
    Shockwave,
    SpikeTrap,
)
from ashen_vault.world.map_loader import MapLoader
from ashen_vault.world.tile_map import TileMap


@dataclass(eq=False)
class Prop:
    kind: str
    x: float
    z: float
    y: float
    tx: int
    tz: int
    props: dict
    key: str
    yaw: float = 0.0
    open_t: float = 0.0
    axis: str | None = None
    wall: bool = False  # hung on the wall behind it (at local -X)


@dataclass(eq=False)
class Projectile:
    x: float
    y: float
    z: float
    dx: float
    dz: float
    life: float
    damage: int
    hostile: bool
    rgb: tuple
    source: str = ""
    # "web": slows whoever it hits; "venom": poisons it; "flame": kindles cold fires it passes;
    # "flare": a spark of Pyre's fire that only shows; "thunder": a lightning spear; "mote": an arcane
    # spark; "arrow": an iron bowman's arrow.
    effect: str | None = None
    dy: float = 0.0  # climb (or drop) per second: spells follow the view up and down
    homing: bool = False  # steers itself toward the nearest foe it can see (Arcane Motes)


INTERACT_RANGE = 2.6
WEB_TIME = 2.5  # seconds a web shot slows you
THORN_SENSE = 3.4  # metres at which thorn plants bristle as you approach
FALL_MESSAGES = {
    "river": "The river drags you under and casts you back ashore.",
    "ravine": "You plunge into the ravine, and claw your way back up battered.",
}
HAZARD_MESSAGES = {
    "landed": "You land hard.",
    "logs_first": "A rotten rope snaps above, and the woodpile starts to roll!",
    "logs_last": "The last log tumbles down. The woodpile is spent.",
    "spores": "Choking spores fill your lungs.",
    "lift_locked": "The lift's chain is locked fast. Somewhere a winch holds it.",
}

# Props that fill their whole tile: nothing walks or flies through them.
BLOCKING_PROPS = (
    "well",
    "save_statue",
    "npc",
    "iron_maiden",
    "altar",
    "table",
    "rack",
    "rubble",
    "frog_idol",
    "pillar",
    "sarcophagus",
    "headsman_block",
    "bonfire",
    "giant_mushroom",
    "totem",
    "anvil",
    "chimney",
)
# Props that block only until they are broken or revealed.
BREAKABLE_PROPS = ("barrel", "crate", "urn", "cocoon", "secret_wall")
# Containers among the breakables: smashing one may spill a little loot.
SPILLING_PROPS = ("barrel", "crate", "urn", "cocoon")
# Props that hang on a wall when they stand beside one.
WALL_PROPS = (
    "torch",
    "banner",
    "shackles",
    "rack",
    "lever",
    "cobweb",
    "skull_niche",
    "winch",
    "shelf_fungus",
)
# Props drawn as far as the fog lets you see, however far that is: they make a skyline.
LANDMARKS = ("spire", "keep", "bastion", "smokestack", "gatehouse", "lavafall")
# Props that turn to face into the room.
FACING_PROPS = ("chest", "altar", "table")
HAZARD_KINDS = ("spikes", "pendulum", "crumble", "flame_jet", "magma_vent")
FALL_DAMAGE = 25
FALL_DEPTH = 1.5  # metres below the pit's rim before a fall counts
LAVA_SHARE = 0.35  # share of your max HP a dip in lava burns away
LAVA_MIN = 20
MOTE_SIGHT = 14.0  # metres an arcane mote looks for a foe to steer toward
BREATH_STEP = 1.2  # metres between the fire circles of a gargoyle's breath
BREATH_PAST = 2.5  # metres the breath rakes on past where you stand
MAIDEN_CYCLE = 3.0  # seconds the iron maiden's door stays in motion after use
FROG_CROAK = 1.2  # seconds the stone frog's throat swells after a pat
FROG_GOLD = 33  # coins the frog coughs up the first time it is patted
# Turns that put a drawbridge model's hinge (its local -X edge) on the named side of its tile.
BRIDGE_YAW = {"w": 0.0, "e": math.pi, "n": -math.pi / 2, "s": math.pi / 2}
STATUS_TINT = {"poison": (0.45, 1.1, 0.3), "burn": (1.5, 0.7, 0.25)}
KINDLE_REACH = 1.2  # a flame bolt passing this close to a cold brazier sets it alight

NPC_LOOKS = {
    "odrin": {"robe": (70, 60, 90), "hair": (200, 200, 200)},
    "pell": {"robe": (120, 90, 40)},
    "hollis": {"robe": (80, 84, 90), "hair": (40, 30, 22)},
    "maeve": {"robe": (60, 90, 100), "hair": (140, 70, 40)},
    "corvane": {"robe": (40, 40, 56), "hair": (150, 150, 150), "hood": True, "blade": True},
}


class World:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.map = MapLoader.load_file(map_path(name))
        self._meshes = []
        self._bake()
        self.props = []
        self.enemies = []
        self.projectiles = []
        self.hazards = []
        self.eruptions = []  # fire columns the Warden calls up
        self.shockwaves = []  # rings sent out by his slam (only for show)
        self._safe = None  # centre of the last solid tile the player stood on
        self.ash = AshCloud()
        self._time = 0.0
        self.blocker = self.blocked_tile
        self.terrain = terrain.Terrain(self.map)
        for p in self.terrain.platforms:
            if p.lever and f"lever:{p.lever}" in game.flags:
                p.locked = False
                p.lowered = 1.0  # a drawbridge let down on an earlier visit is still down
        # Which way each drawbridge hangs from: its `hinge=` side, as a turn of the model.
        self._bridge_hinge = {
            (s.tx, s.tz): BRIDGE_YAW.get(s.props.get("hinge"), 0.0)
            for s in self.map.entities
            if s.kind == "bridge"
        }
        self._piles = {(TileMap.tile_coord(c.x), TileMap.tile_coord(c.z)) for c in self.terrain.chutes}
        # Thorn floors grow spiked plants; each one's spikes rise (0..1) when stepped in.
        self._thorns = {(tx, tz): 0.0 for tx, tz, tile in self.map.each_tile() if tile.hurt}
        self._spawn_entities()

    def _bake(self):
        """Builds the map's mesh with its light baked in, and uploads it (again, after a fire is lit)."""
        self.unload()
        lights = MeshBuilder.lights_for(
            self.map, lit=lambda spec: self._lit_key(spec.tx, spec.tz) in self.flags
        )
        self.builder = MeshBuilder(self.map, lights=lights).build()
        self._meshes = [(self.game.gpu.upload_batch(b), tex) for tex, b in self.builder.batches.items()]

    def unload(self):
        for mesh, _ in self._meshes:
            self.game.gpu.unload_mesh(mesh)
        self._meshes = []

    def _lit_key(self, tx, tz):
        return f"lit:{self.name}:{tx},{tz}"

    def is_lit(self, p):
        """A brazier or bonfire burns unless it stands cold (`unlit`) and nothing has kindled it."""
        return "unlit" not in p.props or self._lit_key(p.tx, p.tz) in self.flags

    def kindle(self, p):
        """Sets a cold brazier or bonfire alight for good. Returns False if it already burns."""
        if p.kind not in KINDLING or self.is_lit(p):
            return False
        self.flags.add(self._lit_key(p.tx, p.tz))
        spec = next(e for e in self.map.entities if (e.tx, e.tz) == (p.tx, p.tz) and e.kind == p.kind)
        for tex in self.builder.add_light(MeshBuilder.light_for(self.map, spec)):
            i = next(i for i, (_, t) in enumerate(self._meshes) if t == tex)
            self.game.gpu.unload_mesh(self._meshes[i][0])
            self._meshes[i] = (self.game.gpu.upload_batch(self.builder.batches[tex]), tex)
        self.game.sfx("pyre", 0.8)
        self.game.message("The fire catches, and the dark draws back.")
        return True

    @property
    def meta(self):
        return self.map.meta

    @property
    def player(self):
        return self.game.player

    @property
    def flags(self):
        return self.game.flags

    def start_position(self):
        tx, tz, yaw = self.meta["start"][:3]
        x, z = TileMap.center(int(tx), int(tz))
        return x, z, yaw * math.pi / 180

    # --- setup ---------------------------------------------------------------

    def _spawn_entities(self):
        self.enemies = spawn_enemies(self.map, self.flags)
        for spec in self.map.entities:
            x, z = TileMap.center(spec.tx, spec.tz)
            y = self.map[spec.tx, spec.tz].floor
            yaw = float(spec.props.get("yaw", "0")) * math.pi / 180
            wall_yaw = self.map.wall_yaw(spec.tx, spec.tz) if spec.kind in WALL_PROPS else None
            if "yaw" not in spec.props:
                if wall_yaw is not None:
                    yaw = wall_yaw
                elif spec.kind in FACING_PROPS:
                    yaw = self.map.open_facing(spec.tx, spec.tz)
            if spec.kind in HAZARD_KINDS:
                self.hazards.append(self._make_hazard(spec))
            elif not EnemyTypes.has(spec.kind) and spec.kind not in terrain.TERRAIN_KINDS:
                key = f"{spec.kind}:{self.name}:{spec.tx},{spec.tz}"
                prop = Prop(
                    kind=spec.kind,
                    x=x,
                    z=z,
                    y=y,
                    tx=spec.tx,
                    tz=spec.tz,
                    props=spec.props,
                    key=key,
                    yaw=yaw,
                    open_t=0.0,
                    wall=wall_yaw is not None,
                )
                if self._opened(prop):
                    prop.open_t = 1.0
                if spec.kind in ("door", "gate"):
                    prop.axis = self._door_axis(spec.tx, spec.tz)
                if spec.kind == "pickup" and key in self.flags:
                    continue
                self.props.append(prop)
                if spec.kind in SPILLING_PROPS and prop.open_t > 0:
                    self._spill(prop)  # a potion left lying in an earlier visit is still there
        self._respill_slain_loot()
        if (
            "boss_dead" in self.flags
            and self.name == "sunken_keep"
            and not self.player.inventory.has("ember_sigil")
            and "sigil_taken" not in self.flags
        ):
            self.drop_sigil(*TileMap.center(15, 4))
        # Other bosses' relics (the Ember Sigil has its own place, above) lie where the boss fell.
        for item_id, tx, tz in relics.pending_drops(self.map, self.flags, self.player.inventory.has):
            if item_id != "ember_sigil":
                self.drop_relic(item_id, *TileMap.center(tx, tz))

    def _respill_slain_loot(self):
        """Loot from an enemy that stays dead (a mimic) waits where it fell until it is picked up."""
        for spec in self.map.entities:
            if not EnemyTypes.has(spec.kind) or not spec.props.get("item"):
                continue
            key = f"slain:{self.name}:{spec.tx},{spec.tz}"
            if EnemyTypes.get(spec.kind).once and key in self.flags:
                self.drop_pickup(*TileMap.center(spec.tx, spec.tz), spec.props["item"], f"loot:{key}")

    def _make_hazard(self, spec):
        phase = float(spec.props.get("phase", "0"))
        if spec.kind == "crumble":
            floor = CrumbleFloor(
                spec.tx, spec.tz, float(spec.props.get("floor", "0")), self.map[spec.tx, spec.tz]
            )
            self.map.set_override((spec.tx, spec.tz), floor.solid_tile())
            return floor
        if spec.kind == "spikes":
            return SpikeTrap(spec.tx, spec.tz, phase=phase)
        tile = self.map[spec.tx, spec.tz]
        if spec.kind == "flame_jet":
            return FlameJet(
                spec.tx,
                spec.tz,
                direction=spec.props.get("dir", "e"),
                length=int(spec.props.get("len", "3")),
                every=float(spec.props.get("every", "3.6")),
                phase=phase,
                floor=tile.floor,
            )
        if spec.kind == "magma_vent":
            radius = float(spec.props.get("radius", "8"))
            return MagmaVent(
                spec.tx,
                spec.tz,
                self._vent_targets(spec.tx, spec.tz, radius),
                every=float(spec.props.get("every", "3")),
                phase=phase,
                count=int(spec.props.get("count", "2")),
                floor=tile.floor,
                radius=radius,
            )
        pivot = tile.ceil if tile.ceil is not None else tile.floor + 4.0
        return Pendulum(
            spec.tx,
            spec.tz,
            axis=self._door_axis(spec.tx, spec.tz),
            pivot_y=pivot,
            length=pivot - tile.floor - 1.1,
            floor=tile.floor,
            phase=phase,
        )

    def _vent_targets(self, tx, tz, radius):
        """Open-sky solid ground a magma vent's bombs can land on: (x, z, floor) of each tile centre."""
        out = []
        cx, cz = TileMap.center(tx, tz)
        for x_, z_, tile in self.map.each_tile():
            x, z = TileMap.center(x_, z_)
            if math.hypot(x - cx, z - cz) > radius:
                continue
            if tile.walkable and not tile.hazardous and not tile.needs_footing and tile.open_sky:
                out.append((x, z, tile.floor))
        return out

    def respawn_enemies(self):
        """Shrine rest: every normal enemy comes back fresh. A living boss is left as it is, unless it
        is a twin whose other half has fallen: then the pair comes back fresh together."""
        alive = {e.type.id for e in self.enemies if e.type.boss and e.alive}
        bosses = [
            e for e in self.enemies if e.type.boss and e.alive and (not e.type.twin or e.type.twin in alive)
        ]
        kept = {e.type.id for e in bosses}
        twins = [
            e
            for e in spawn_enemies(self.map, self.flags)
            if e.type.boss and e.type.twin and e.type.id not in kept
        ]
        self.enemies = bosses + twins + spawn_enemies(self.map, self.flags, bosses=False)
        self.projectiles = []
        self.eruptions = []
        self.shockwaves = []

    def _opened(self, prop):
        if prop.kind in ("door", "chest", "lever", "altar", *BREAKABLE_PROPS):
            return prop.key in self.flags or f"chest:{self.name}:{prop.tx},{prop.tz}" in self.flags
        if prop.kind == "gate":
            return f"lever:{prop.props.get('lever')}" in self.flags
        return False

    def _door_axis(self, tx, tz):
        """A door blocks the axis it is not aligned with: corridor walls tell us which."""
        return "x" if self.map[tx, tz - 1].solid and self.map[tx, tz + 1].solid else "z"

    # --- queries used by collision and AI ------------------------------------

    def blocked_tile(self, tx, tz):
        for p in self.props:
            if p.tx != tx or p.tz != tz:
                continue
            if p.kind in ("door", "gate") and p.open_t < 0.9:
                return True
            if p.kind in BLOCKING_PROPS:
                return True
            if p.kind in BREAKABLE_PROPS and p.open_t == 0:
                return True
            if p.kind == "exit" and p.props.get("model") == "well":
                return True
        return (tx, tz) in self._piles

    @property
    def player_x(self):
        return self.player.x

    @property
    def player_z(self):
        return self.player.z

    @property
    def player_hidden(self):
        """Wrapped in a Veil of Mist: ordinary foes overlook you unless you come very close."""
        return self.player.veil_t > 0

    @property
    def player_alive(self):
        return self.player.alive

    def can_see(self, ax, az, bx, bz):
        return collision.line_of_sight(self.map, ax, az, bx, bz, blocked=self.blocker)

    def move_enemy(self, enemy, dx, dz):
        nx, nz = collision.move(self.map, enemy.x, enemy.z, dx, dz, radius=enemy.radius, blocked=self.blocker)
        nx, nz = collision.separate(nx, nz, enemy.radius, self.player.x, self.player.z, Player.RADIUS)
        for other in self.enemies:
            if other is enemy or not other.alive:
                continue
            nx, nz = collision.separate(nx, nz, enemy.radius, other.x, other.z, other.radius)
        tile = self.map.tile_at(nx, nz)
        if tile.needs_footing or not tile.walkable:
            return
        if self.blocked_tile(TileMap.tile_coord(nx), TileMap.tile_coord(nz)):
            return
        if abs(tile.floor - self.map.floor_at(enemy.x, enemy.z)) > collision.STEP_HEIGHT:
            return
        enemy.x = nx
        enemy.z = nz

    def enemy_strike(self, enemy, mult=1.0):
        """Returns how much of the blow got through a raised shield."""
        base = enemy.type.damage * mult * (0.85 + random.random() * 0.3)
        dmg = max(rround(base - self.player.inventory.defense * 0.5), 1)
        return self.strike_player(dmg, enemy.name, enemy.x, enemy.z)

    def strike_player(self, dmg, source, ax, az):
        """A blow from (ax, az): a raised shield takes what it can before the rest lands.
        Returns the damage that got through."""
        taken, block = self.player.take_blow(dmg, ax, az)
        if block is not None and block.blocked:
            self.game.blocked(block)
        if taken > 0:
            self.game.hurt_player(taken, source)
        return taken

    def boss_rage(self, enemy):
        """A boss enters its second phase."""
        self.game.sfx("eruption", 0.9)
        self.game.message(enemy.type.rage)

    def slam(self, enemy):
        """The shockwave of a slam: a ring that runs out along the floor."""
        self.shockwaves.append(Shockwave(enemy.x, enemy.z, self.enemy_y(enemy), SLAM_RADIUS))
        self.game.sfx("quake")

    def eruption(self, enemy):
        """Fire wells up under the player, then on either side of them a moment later."""
        player = self.player
        damage = rround(enemy.type.damage * MOVES["eruption"][2])
        ax = math.atan2(player.z - enemy.z, player.x - enemy.x) + math.pi / 2
        spots = [(player.x, player.z, 0.0)]
        for side in (-1.6, 1.6):
            spots.append((player.x + math.cos(ax) * side, player.z + math.sin(ax) * side, 0.35))
        for x, z, delay in spots:
            tile = self.map.tile_at(x, z)
            if tile.solid or not tile.walkable:
                continue
            self.eruptions.append(Eruption(x, z, tile.floor, delay=delay, damage=damage))
        self.game.sfx("spell", 0.6)

    def breath(self, enemy):
        """A gargoyle's breath: a line of fire circles from its jaws toward you and on past, each
        bursting a moment after the one before. Step sideways out of the line."""
        player = self.player
        dx, dz = player.x - enemy.x, player.z - enemy.z
        d = math.hypot(dx, dz) or 1.0
        ux, uz = dx / d, dz / d
        damage = rround(enemy.type.damage * MOVES["breath"][2])
        s, n = enemy.radius + 0.6, 0
        while s <= d + BREATH_PAST:
            x, z = enemy.x + ux * s, enemy.z + uz * s
            tile = self.map.tile_at(x, z)
            if tile.solid or not tile.walkable:
                break
            self.eruptions.append(Eruption(x, z, tile.floor, delay=n * 0.12, damage=damage))
            s += BREATH_STEP
            n += 1
        self.game.sfx("breath", 0.9)

    # --- twin bosses -------------------------------------------------------------

    def _twins_of(self, enemy):
        return [e for e in self.enemies if enemy.type.twin and e.type.id == enemy.type.twin]

    def rouse_twin(self, enemy):
        """One perched gargoyle wakes: its twin tears free of its perch as well."""
        woke = False
        for e in self._twins_of(enemy):
            if e.perched:
                e.rouse()
                woke = True
        if woke or not enemy.type.twin:
            self.game.sfx("screech")
            self.game.message("The iron gargoyles tear free of their perches!")

    def twin_fallen(self, enemy):
        return enemy.type.twin is not None and not any(e.alive for e in self._twins_of(enemy))

    def twin_busy(self, enemy):
        """Its twin is winding up or carrying out a special move: the pair takes turns."""
        return any(
            e.alive and e.state in ("windup", "attack") and e.attack_kind in MOVES
            for e in self._twins_of(enemy)
        )

    def hook(self, enemy, mult, pull):
        """A hooked chain: a light blow that drags you toward the thrower, unless a shield stops it."""
        if self.enemy_strike(enemy, mult) <= 0:
            return
        player = self.player
        if abs(player.y - self.enemy_y(enemy)) > collision.STEP_HEIGHT:
            return  # out of his reach above or below (riding a lift): the chain only bites
        dx, dz = enemy.x - player.x, enemy.z - player.z
        d = math.hypot(dx, dz)
        room = d - enemy.radius - Player.RADIUS - 0.3  # never drags you into its body
        step = min(pull, room)
        if d > 0 and step > 0:
            self._knock_player(dx / d * step, dz / d * step)
            self.game.message(f"The {enemy.name}'s hook drags you in!")

    def enemy_fire(self, enemy, kind="shot"):
        if kind == "cinders":
            # A fan of three embers: step sideways out of the spread, or between two of them.
            for spread in (-0.28, 0.0, 0.28):
                self._fire_one(enemy, kind, spread)
            self.game.sfx("spell")
            return
        self._fire_one(enemy, kind)
        self.game.sfx("spell")

    def _fire_one(self, enemy, kind, spread=0.0):
        web = kind == "web"
        y = self.enemy_y(enemy) + (enemy.type.hover or 1.2)
        player = self.player
        speed = 7.5 if web else 11 if enemy.type.shot == "arrow" else 6
        dx, dy, dz = shots.toward(
            enemy.x, y, enemy.z, player.x, player.y + shots.AIM_HEIGHT, player.z, speed, spread
        )
        lead = enemy.radius / speed  # leaves from the edge of its body
        damage = enemy.type.damage
        if kind in ("web", "cinders"):
            damage = rround(damage * MOVES[kind][2])
        self.projectiles.append(
            Projectile(
                x=enemy.x + dx * lead,
                y=y + dy * lead,
                z=enemy.z + dz * lead,
                dx=dx,
                dy=dy,
                dz=dz,
                life=4.0,
                damage=damage,
                hostile=True,
                rgb=(230, 230, 220) if web else enemy.type.shot_rgb,
                source=enemy.name,
                effect="web" if web else enemy.type.shot,
            )
        )

    def summon(self, enemy, type_id, count):
        """A boss calls `count` of its brood, spread out around itself."""
        type_ = EnemyTypes.get(type_id)
        for i in range(count):
            a = enemy.yaw + math.pi / 2 + i * 2 * math.pi / count
            x = enemy.x + math.cos(a) * (enemy.radius + 0.8)
            z = enemy.z + math.sin(a) * (enemy.radius + 0.8)
            tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
            if not collision.passable(self.map, tx, tz, self.enemy_y(enemy), blocked=self.blocker):
                x, z = enemy.x, enemy.z
            child = Enemy(type_, x, z, yaw=a)
            child.state = "chase"
            self.enemies.append(child)
        self.game.sfx("enemy_die", 0.5)
        self.game.message(f"The {enemy.name} shrieks, and its brood answers.")

    def player_floor(self):
        return self.terrain.floor(self.player.x, self.player.z)

    def update_terrain(self, dt):
        """River, ravine, platforms, currents, thorns, logs and spores acting on the player."""
        event = self.terrain.update(dt, self.player, self.game.hurt_player, blocked=self.blocker)
        for name, volume in self.terrain.sounds:
            self.game.sfx(name, volume)
        if event == "fell":
            self.game.sfx("hurt")
            self.game.message(FALL_MESSAGES[self.terrain.fell_into])
        else:
            if event in HAZARD_MESSAGES:
                self.game.message(HAZARD_MESSAGES[event])
            if event and event.startswith("logs_"):
                self.game.sfx("heavy", 0.8)

    def enemy_y(self, enemy):
        return self.map.floor_at(enemy.x, enemy.z)

    # --- update --------------------------------------------------------------

    def update(self, dt):
        self._time += dt
        for e in self.enemies:
            e.update(dt, self)
            harm = e.status_tick(dt)
            if harm:
                self.game.damage_enemy(e, harm, stagger=False)
            if not e.alive:
                self._shed_ash(e, dt)
        self.enemies = [e for e in self.enemies if not e.gone]
        self.ash.update(dt)
        for p in self.props:
            if p.kind == "iron_maiden":
                self._update_maiden(p, dt)
            elif p.kind == "frog_idol" and p.open_t > 0:
                p.open_t = p.open_t + dt if p.open_t + dt < FROG_CROAK else 0.0
            elif 0 < p.open_t < 1.0:
                p.open_t = min(p.open_t + dt * 0.8, 1.0)
        self._update_projectiles(dt)
        self._update_hazards(dt)
        self._update_fire(dt)
        self._check_fall()
        self._push_player_out_of_bodies()
        self._update_thorns(dt)

    def _update_thorns(self, dt):
        """Spikes stab up fully under your feet and bristle half-way as you come near."""
        player = self.player
        here = (TileMap.tile_coord(player.x), TileMap.tile_coord(player.z))
        for key, rise in self._thorns.items():
            x, z = TileMap.center(*key)
            if key == here:
                want = 1.0
            elif math.hypot(x - player.x, z - player.z) < THORN_SENSE:
                want = 0.55
            else:
                want = 0.0
            step = dt * (9 if want > rise else 1.2)
            self._thorns[key] = min(rise + step, want) if want > rise else max(rise - step, want)

    def _update_hazards(self, dt):
        player = self.player
        ptx, ptz = TileMap.tile_coord(player.x), TileMap.tile_coord(player.z)
        for h in self.hazards:
            near = math.hypot(h.x - player.x, h.z - player.z) < 7
            if isinstance(h, CrumbleFloor):
                self._update_crumble(h, dt, player.alive and (h.tx, h.tz) == (ptx, ptz))
                continue
            if isinstance(h, MagmaVent):
                self._update_vent(h, dt)
                continue
            if isinstance(h, FlameJet):
                if h.update(dt) and math.hypot(h.x - player.x, h.z - player.z) < 10:
                    self.game.sfx("jet", 0.6)
                if player.alive and abs(player.y - h.floor) < 1.6:
                    dmg = h.hit(player.x, player.z)
                    if dmg:
                        self.game.hurt_player(
                            max(rround(dmg - player.inventory.defense * 0.3), 1), "The flames"
                        )
                continue
            if h.update(dt) and near:
                self.game.sfx("trap" if isinstance(h, SpikeTrap) else "swoosh", 0.5)
            if not player.alive:
                continue
            if isinstance(h, SpikeTrap):
                dmg = h.hit(player.x, player.z)
                if dmg:
                    self.game.hurt_player(dmg, "The spikes")
                continue
            hit = h.hit(player.x, player.z)
            if hit:
                dmg, px, pz = hit
                self.game.hurt_player(dmg, "The pendulum")
                self._knock_player(px, pz)

    def _update_vent(self, h, dt):
        """A magma vent lobs its bombs: the first at you when you stand on open ground in its reach."""
        player = self.player
        spot = None
        if player.alive and h.reaches(player.x, player.z):
            tile = self.map.tile_at(player.x, player.z)
            if tile.walkable and not tile.hazardous and tile.open_sky:
                spot = (player.x, player.z, tile.floor)
        bombs = h.update(dt, spot)
        if bombs:
            self.eruptions.extend(bombs)
            if math.hypot(h.x - player.x, h.z - player.z) < h.radius + 6:
                self.game.sfx("lob", 0.6)

    def _update_fire(self, dt):
        """The Warden's fire columns and slam rings."""
        player = self.player
        for f in self.eruptions:
            if f.update(dt):
                self.game.sfx("eruption", 0.6)
            if player.alive:
                dmg = f.hit(player.x, player.z)
                if dmg:
                    self.game.hurt_player(max(rround(dmg - player.inventory.defense * 0.3), 1), "The fire")
        self.eruptions = [f for f in self.eruptions if not f.done]
        for w in self.shockwaves:
            w.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]

    def _update_crumble(self, h, dt, player_on):
        change = h.update(dt, player_on)
        if change == "shaking":
            self.game.sfx("crack", 0.8)
        elif change == "fallen":
            self.map.set_override((h.tx, h.tz), None)
            self.game.sfx("door", 0.5)
        elif change == "solid":
            self.map.set_override((h.tx, h.tz), h.solid_tile())

    def _check_fall(self):
        """Remembers solid ground; a player who drops into a pit is hurt and hauled back to it."""
        player = self.player
        tx, tz = TileMap.tile_coord(player.x), TileMap.tile_coord(player.z)
        tile = self.map[tx, tz]
        if tile.lava:
            if player.alive and self._safe is not None and player.y <= tile.floor + 0.3:
                self._burn_in_lava()
            return
        crumbling = any(isinstance(h, CrumbleFloor) and (h.tx, h.tz) == (tx, tz) for h in self.hazards)
        if not tile.pit and not crumbling:
            if abs(player.y - tile.floor) < 0.05:
                self._safe = TileMap.center(tx, tz)
            return
        if not tile.pit or self._safe is None or not player.alive:
            return
        rim = self.map.floor_at(*self._safe)
        if player.y > rim - FALL_DEPTH:
            return
        self.game.hurt_player(FALL_DAMAGE, "The fall")
        self.game.message("You fall into the dark and claw your way back up.")
        if player.alive:
            player.place(*self._safe, player.yaw, self.map)

    def _burn_in_lava(self):
        """Lava sears a big share of your HP and you scramble back to the last solid ground."""
        player = self.player
        dmg = max(LAVA_MIN, rround(player.stats.max_hp * LAVA_SHARE))
        self.game.hurt_player(dmg, "The lava")
        self.game.sfx("hiss")
        self.game.message("The lava sears you! You scramble back onto the stone.")
        if player.alive:
            player.place(*self._safe, player.yaw, self.map)

    def _knock_player(self, dx, dz):
        """Shoves the player in small steps so walls stop the push."""
        player = self.player
        for _ in range(8):
            player.x, player.z = collision.move(
                self.map, player.x, player.z, dx / 8, dz / 8, radius=Player.RADIUS, blocked=self.blocker
            )

    def body_span(self, enemy):
        """(base y, height) of an enemy's body in world space, for the ash dissolve."""
        t = enemy.type
        base = self.enemy_y(enemy)
        if t.hover:
            base += t.hover - t.height / 2
        return base, t.height

    def _shed_ash(self, e, dt):
        base, height = self.body_span(e)
        rate = 70 if e.type.boss else 30
        self.ash.shed(e.x, base, e.z, e.radius, height, e.death_progress, rate, dt)

    def _push_player_out_of_bodies(self):
        player = self.player
        for e in self.enemies:
            if not e.alive:
                continue
            nx, nz = collision.separate(player.x, player.z, Player.RADIUS, e.x, e.z, e.radius)
            tile = self.map.tile_at(nx, nz)
            ok = collision.passable(
                self.map, TileMap.tile_coord(nx), TileMap.tile_coord(nz), player.y, blocked=self.blocker
            )
            if not ok and tile is not self.map.tile_at(player.x, player.z):
                continue
            player.x = nx
            player.z = nz

    def _update_projectiles(self, dt):
        player = self.player
        for pr_ in self.projectiles:
            if pr_.homing:
                self._steer(pr_, dt)
            pr_.x += pr_.dx * dt
            pr_.y += pr_.dy * dt
            pr_.z += pr_.dz * dt
            pr_.life -= dt
            if pr_.effect == "flame":
                for p in self.props:
                    if p.kind in KINDLING and math.hypot(p.x - pr_.x, p.z - pr_.z) < KINDLE_REACH:
                        self.kindle(p)
            tile = self.map.tile_at(pr_.x, pr_.z)
            if (
                tile.solid
                or tile.floor > pr_.y
                or (tile.ceil is not None and tile.ceil < pr_.y)
                or self.blocked_tile(TileMap.tile_coord(pr_.x), TileMap.tile_coord(pr_.z))
            ):
                pr_.life = 0
            elif pr_.effect == "flare":
                continue
            elif pr_.hostile:
                if shots.strikes(
                    pr_.x, pr_.y, pr_.z, player.x, player.z, shots.PLAYER_RADIUS, shots.player_span(player.y)
                ):
                    self.strike_player(
                        max(rround(pr_.damage - player.inventory.defense * 0.3), 1),
                        pr_.source or "Something",
                        pr_.x - pr_.dx,
                        pr_.z - pr_.dz,
                    )
                    if pr_.effect == "web":
                        player.webbed_t = WEB_TIME
                        self.game.message("Sticky silk binds your legs!")
                    pr_.life = 0
            else:
                target = next(
                    (
                        e
                        for e in self.enemies
                        if e.alive
                        and shots.strikes(
                            pr_.x, pr_.y, pr_.z, e.x, e.z, e.radius, shots.body_span(e.type, self.enemy_y(e))
                        )
                    ),
                    None,
                )
                if target:
                    element = elements.EFFECT_ELEMENT.get(pr_.effect)
                    dmg = max(rround(pr_.damage * elements.mult(target.type, element)), 1)
                    jolt = elements.staggers(target.type, element)
                    self.game.damage_enemy(target, dmg, 99.0 if jolt else 1.0)
                    if pr_.effect == "venom" and target.alive:
                        target.afflict("poison", *Spells.venom_poison(self.player.stats.magic))
                        self.game.sfx("hiss", 0.6)
                    pr_.life = 0
        self.projectiles = [p for p in self.projectiles if p.life > 0]

    # --- player actions --------------------------------------------------------

    def melee_targets(self, reach, cone=0.6, limit=None):
        """Living enemies a swing can hit, nearest first. `cone` is the minimum cosine between
        facing and target (below 0 hits all around); `limit` caps how many."""
        player = self.player
        fx, fz = player.forward()
        out = []
        for e in self.enemies:
            if not e.alive:
                continue
            dx = e.x - player.x
            dz = e.z - player.z
            d = math.hypot(dx, dz)
            if d > reach + e.radius:
                continue
            if d < e.radius + 0.2 or (
                (cone < 0 or (dx * fx + dz * fz) / d > cone) and self.can_see(player.x, player.z, e.x, e.z)
            ):
                out.append(e)
        out.sort(key=lambda e: math.hypot(e.x - player.x, e.z - player.z))
        return out[:limit] if limit else out

    def _steer(self, pr_, dt):
        """An arcane mote turns toward the nearest living foe it can see ahead of it."""
        best, best_d = None, MOTE_SIGHT
        for e in self.enemies:
            if not e.alive or e.perched:
                continue
            d = math.hypot(e.x - pr_.x, e.z - pr_.z)
            if d < best_d and self.can_see(pr_.x, pr_.z, e.x, e.z):
                best, best_d = e, d
        if best is None:
            return
        lo, hi = shots.body_span(best.type, self.enemy_y(best))
        pr_.dx, pr_.dy, pr_.dz = shots.home(
            pr_.dx, pr_.dy, pr_.dz, pr_.x, pr_.y, pr_.z, best.x, (lo + hi) / 2, best.z, Spells.MOTE_TURN, dt
        )

    def motes(self, damage):
        """Arcane Motes: three slow sparks fanned out along the view, each seeking a foe of its own
        accord. Returns them."""
        player = self.player
        out = []
        for i in range(Spells.MOTES):
            spread = (i - (Spells.MOTES - 1) / 2) * Spells.MOTE_SPREAD
            dx, dy, dz = shots.aim(player.yaw + spread, player.pitch, Spells.MOTE_SPEED)
            pr_ = Projectile(
                x=player.x + dx * 0.08,
                y=player.eye_y - shots.BOLT_DROP + dy * 0.08,
                z=player.z + dz * 0.08,
                dx=dx,
                dy=dy,
                dz=dz,
                life=4.0,
                damage=damage,
                hostile=False,
                rgb=(190, 120, 255),
                effect="mote",
                homing=True,
            )
            self.projectiles.append(pr_)
            out.append(pr_)
        return out

    def fire_bolt(self, damage, effect="flame", rgb=(255, 160, 60), speed=shots.BOLT_SPEED):
        player = self.player
        dx, dy, dz = shots.aim(player.yaw, player.pitch, speed)
        lead = 0.5 / speed  # starts half a metre out along the aim
        self.projectiles.append(
            Projectile(
                x=player.x + dx * lead,
                y=player.eye_y - shots.BOLT_DROP + dy * lead,
                z=player.z + dz * lead,
                dx=dx,
                dy=dy,
                dz=dz,
                life=3.0,
                damage=damage,
                hostile=False,
                rgb=rgb,
                effect=effect,
            )
        )

    def pyre(self, magic, gauge):
        """A short gout of fire in front of you: it burns the foes it reaches (plants catch and keep
        burning), kindles cold braziers and burns away webs. Returns how many foes it struck."""
        player = self.player
        targets = self.melee_targets(Spells.PYRE_REACH, cone=0.5)
        for e in targets:
            flammable = e.type.flammable
            dmg = Spells.pyre_damage(magic, gauge, flammable)
            self.game.damage_enemy(e, max(rround(dmg * elements.mult(e.type, "fire")), 1))
            if flammable and e.alive:
                e.afflict("burn", *Spells.BURN)
        fx, fz = player.forward()
        for p in list(self.props):
            dx, dz = p.x - player.x, p.z - player.z
            d = math.hypot(dx, dz) or 1e-6
            if d > Spells.PYRE_REACH + TileMap.TILE / 2 or (dx * fx + dz * fz) / d < 0.4:
                continue
            if p.kind in KINDLING:
                self.kindle(p)
            elif self._web(p) and p.open_t == 0:
                self.flags.add(p.key)
                p.open_t = 0.01
                self.game.message("The web shrivels in the flame.")
        dx, dy, dz = shots.aim(player.yaw, player.pitch)
        rng = random.Random(int(self._time * 1000))
        for i in range(12):  # a ragged spray of flame that only shows
            spread = (i / 11 - 0.5) * 0.9 + rng.uniform(-0.08, 0.08)
            ca, sa = math.cos(spread), math.sin(spread)
            sx, sz = dx * ca - dz * sa, dx * sa + dz * ca
            speed = rng.uniform(5.0, 9.0)
            self.projectiles.append(
                Projectile(
                    x=player.x + sx * 0.5,
                    y=player.eye_y - shots.BOLT_DROP + rng.uniform(-0.15, 0.2),
                    z=player.z + sz * 0.5,
                    dx=sx * speed,
                    dy=dy * speed + rng.uniform(0.0, 1.2),
                    dz=sz * speed,
                    life=rng.uniform(0.25, 0.45),
                    damage=0,
                    hostile=False,
                    rgb=(255, rng.randint(80, 200), 40),
                    effect="flare",
                )
            )
        return len(targets)

    @staticmethod
    def _web(p):
        return p.kind == "secret_wall" and p.props.get("model") == "web"

    def focus(self):
        """Closest interactable prop in front of the player. A dormant mimic counts: it looks like a chest."""
        player = self.player
        fx, fz = player.forward()
        best = None
        best_d = None
        candidates = [p for p in self.props if self._interactable(p)]
        candidates += [e for e in self.enemies if e.dormant]
        for p in candidates:
            dx = p.x - player.x
            dz = p.z - player.z
            d = math.hypot(dx, dz)
            in_reach = d < INTERACT_RANGE and (d < 0.8 or (dx * fx + dz * fz) / d > 0.55)
            if in_reach and (best is None or d < best_d):
                best, best_d = p, d
        return best

    def _interactable(self, p):
        if p.kind in ("npc", "save_statue", "exit", "pickup", "iron_maiden", "frog_idol"):
            return True
        if p.kind in ("chest", "lever", "door", "altar"):
            return p.open_t == 0
        return p.kind in KINDLING and not self.is_lit(p)  # a cold fire: you can look at its ashes

    def open_prop(self, p):
        p.open_t = 0.01
        self.flags.add(p.key)

    def drop_sigil(self, x, z):
        self.drop_pickup(x, z, "ember_sigil", "sigil")

    def drop_relic(self, item_id, x, z):
        """Leaves a boss relic on the floor as a pickup."""
        self.drop_pickup(x, z, item_id, relics.get(item_id).key)

    def drop_pickup(self, x, z, item, key):
        """Leaves `item` on the floor at (x, z); `key` is flagged once it is taken."""
        if key in self.flags:
            return
        tx = TileMap.tile_coord(x)
        tz = TileMap.tile_coord(z)
        self.props.append(
            Prop(
                kind="pickup",
                x=x,
                z=z,
                y=self.map[tx, tz].floor,
                tx=tx,
                tz=tz,
                props={"item": item},
                key=key,
                yaw=0,
                open_t=0,
            )
        )

    # --- breakables -------------------------------------------------------------

    def strike_props(self, reach, cone=0.6):
        """Intact barrels and illusory walls a swing reaches, using the same facing test as
        `melee_targets`. Props fill a tile, so half a tile is added to the reach."""
        player = self.player
        fx, fz = player.forward()
        out = []
        for p in self.props:
            if p.kind not in BREAKABLE_PROPS or p.open_t > 0 or self._web(p):
                continue  # a web wall shrugs off blades: only fire clears it
            dx = p.x - player.x
            dz = p.z - player.z
            d = math.hypot(dx, dz) or 1e-6
            if d > reach + TileMap.TILE / 2:
                continue
            if cone < 0 or (dx * fx + dz * fz) / d > min(cone, 0.5):
                out.append(p)
        return out

    def break_prop(self, p):
        """Smashes a container or dispels an illusory wall; both stay that way in the save.
        Returns (gold, item) spilled: gold goes straight to the purse, an item lands on the floor."""
        self.flags.add(p.key)
        if p.kind not in SPILLING_PROPS:
            p.open_t = 0.01  # the wall fades out over the next second
            return 0, None
        p.open_t = 1.0
        gold, item = loot.roll(p.key, p.props)
        self.player.inventory.gold += gold
        self._spill(p)
        return gold, item

    def _spill(self, p):
        _, item = loot.roll(p.key, p.props)
        if item:
            self.drop_pickup(p.x, p.z, item, f"loot:{p.key}")

    def take_from_altar(self, p):
        """Lifts the altar's offering; returns the item id."""
        self.open_prop(p)
        p.open_t = 1.0
        return p.props.get("item")

    def drop_enemy_loot(self, enemy):
        if enemy.loot:
            key = f"loot:{enemy.key}" if enemy.key else f"loot:{enemy.marker}:{enemy.home_x},{enemy.home_z}"
            self.drop_pickup(enemy.x, enemy.z, enemy.loot, key)

    def remove_prop(self, p):
        if p in self.props:
            self.props.remove(p)

    @staticmethod
    def _update_maiden(p, dt):
        """The maiden's door swings open, holds a moment, then clanks shut again."""
        if p.open_t <= 0:
            return
        p.open_t += dt
        if p.open_t >= MAIDEN_CYCLE:
            p.open_t = 0.0

    def enter_maiden(self, p):
        p.open_t = 0.01

    def pat_frog(self, p):
        """The stone frog croaks. The first pat ever, it coughs up a few coins (once per save).
        Returns the gold it gave."""
        p.open_t = 0.01
        if p.key in self.flags:
            return 0
        self.flags.add(p.key)
        self.player.inventory.gold += FROG_GOLD
        return FROG_GOLD

    def pull_lever(self, p):
        self.open_prop(p)
        self.flags.add(f"lever:{p.props.get('id')}")
        for g in self.props:
            if g.kind == "gate" and g.props.get("lever") == p.props.get("id"):
                g.open_t = 0.01
        for lift in self.terrain.platforms:
            if lift.lever and lift.lever == p.props.get("id"):
                lift.locked = False
                self.game.sfx("chain", 0.8)

    # --- rendering ---------------------------------------------------------------

    def draw(self, rig, gpu):
        player = self.player
        for mesh, tex in self._meshes:
            gpu.draw_world_batch(mesh, tex)
        gpu.set_float("isModel", 1.0)
        sight = self.meta.get("fog_range", [0, 40])[1] + 2
        # Small models stop being drawn sooner than the fog's end on a map that sees far (the
        # fortress from its bridge); landmarks are drawn as far as the eye can see.
        far = min(float(self.meta.get("model_range", sight)), sight)
        for p in self.props:
            if math.hypot(p.x - player.x, p.z - player.z) > (sight if p.kind in LANDMARKS else far):
                continue
            self._model_light(gpu, p.x, p.y + 1.0, p.z)
            with rig.entity(p.x, p.y, p.z, p.yaw):
                self._draw_prop(rig, p)
        for (tx, tz), rise in self._thorns.items():
            x, z = TileMap.center(tx, tz)
            if math.hypot(x - player.x, z - player.z) > far:
                continue
            y = self.map[tx, tz].floor
            self._model_light(gpu, x, y + 0.5, z)
            with rig.at(x, y, z):
                models.thorn_plant(rig, tx * 7 + tz * 3, self._time, rise)
        for pl in self.terrain.platforms:
            if math.hypot(pl.x - player.x, pl.z - player.z) > far:
                continue
            self._model_light(gpu, pl.x, pl.deck + 0.5, pl.z)
            shake = math.sin(self._time * 40) * 0.03 * pl.creaking
            with rig.at(pl.x, pl.deck - pl.sink + shake, pl.z):
                if pl.kind == "lift":
                    tile = self.map[TileMap.tile_coord(pl.x), TileMap.tile_coord(pl.z)]
                    chain_h = (tile.ceil or pl.high + 3.0) - pl.deck
                    models.lift(rig, self._time, pl.moving, chain_h, pl.model, pl.doors)
                elif pl.kind == "raft":
                    models.raft(rig, self._time)
                elif pl.kind == "ledge":
                    models.ledge(rig, pl.creaking, int(pl.x * 3 + pl.z * 7))
                elif pl.kind == "boards":
                    models.boards(rig, pl.creaking, broken=not pl.afloat)
                elif pl.kind == "bridge":
                    hinge = self._bridge_hinge.get((TileMap.tile_coord(pl.x), TileMap.tile_coord(pl.z)), 0.0)
                    with rig.at(0, 0, 0, ry=hinge):
                        models.bridge(rig, pl.lowered)
                else:
                    models.plank(rig, pl.creaking)
        for chute in self.terrain.chutes:
            y = self.map.floor_at(chute.x, chute.z)
            self._model_light(gpu, chute.x, y + 0.8, chute.z)
            back = terrain.PILE_BACK
            with rig.at(
                chute.x - chute.ux * back, y, chute.z - chute.uz * back, ry=math.atan2(chute.ux, chute.uz)
            ):
                models.log_pile(rig, chute.stock, self._time, chute.t / chute.every if chute.active else 0.0)
        for log in self.terrain.logs:
            if math.hypot(log.x - player.x, log.z - player.z) > far:
                continue
            self._model_light(gpu, log.x, log.y + 0.5, log.z)
            yaw = math.atan2(log.dx, log.dz)
            with rig.at(log.x, log.y + terrain.LOG_R, log.z, ry=yaw):
                models.rolling_log(rig, log.spin)
        for pod in self.terrain.pods:
            if math.hypot(pod.x - player.x, pod.z - player.z) > far:
                continue
            self._model_light(gpu, pod.x, pod.y + 0.5, pod.z)
            with rig.at(pod.x, pod.y, pod.z):
                models.spore_pod(rig, self._time, pod.cloud, pod.t / pod.every)
        for e in self.enemies:
            if math.hypot(e.x - player.x, e.z - player.z) > far:
                continue
            y = self.enemy_y(e)
            self._model_light(
                gpu, e.x, y + 1.0, e.z, flash=e.state == "hurt", tint=STATUS_TINT.get(e.afflicted)
            )
            dying = not e.alive
            if dying:
                ashen, dissolve = death_phases(e.death_progress)
                gpu.set_float("ashen", ashen)
                gpu.set_float("dissolve", dissolve)
                gpu.set_vec2("dissolveSpan", self.body_span(e))
            with rig.entity(e.x, y, e.z, e.yaw):
                models.enemy(rig, e)
            if dying:
                gpu.set_float("ashen", 0.0)
                gpu.set_float("dissolve", 0.0)
        for h in self.hazards:
            if math.hypot(h.x - player.x, h.z - player.z) > far:
                continue
            y = self.map[h.tx, h.tz].floor
            if isinstance(h, CrumbleFloor):
                self._model_light(gpu, h.x, h.floor + 0.5, h.z)
                with rig.at(h.x, h.floor, h.z):
                    models.crumble_slab(rig, h.shake, h.drop, h.rise, self._time + h.tx)
            elif isinstance(h, SpikeTrap):
                self._model_light(gpu, h.x, y + 0.5, h.z)
                with rig.at(h.x, y, h.z):
                    models.spikes(rig, h.height)
            elif isinstance(h, FlameJet):
                self._model_light(gpu, h.x, y + 0.5, h.z, flash=h.reach > 0)
                with rig.at(h.x, y, h.z, ry=-math.atan2(h.dz, h.dx)):
                    forge_models.flame_jet(rig, h.glow, h.reach, h.length * TileMap.TILE, self._time)
            elif isinstance(h, MagmaVent):
                gpu.model_light((1.6, 1.2, 1.0))
                with rig.at(h.x, y, h.z):
                    forge_models.magma_vent(rig, self._time + h.tx)
            else:
                self._model_light(gpu, h.x, y + 1.5, h.z)
                with rig.at(h.x, h.pivot_y, h.z, ry=0 if h.axis == "x" else -math.pi / 2):
                    models.pendulum(rig, h.angle, h.length)
        for f in self.eruptions:
            self._model_light(gpu, f.x, f.floor + 0.5, f.z)
            with rig.at(f.x, f.floor, f.z):
                models.eruption(rig, f.glow, f.flame, self._time)
            bomb = f.bomb()
            if bomb:
                gpu.model_light((1.6, 1.4, 1.2))
                with rig.at(*bomb):
                    forge_models.magma_bomb(rig, self._time)
        for w in self.shockwaves:
            gpu.model_light((1.6, 1.4, 1.2))
            with rig.at(w.x, w.floor, w.z):
                models.shockwave_ring(rig, w.progress, w.radius)
        self._draw_ash(rig, gpu, far)
        for pr_ in self.projectiles:
            gpu.model_light((1.6, 1.4, 1.2))
            if pr_.effect in ("arrow", "thunder"):  # these fly point first
                heading = -math.atan2(pr_.dz, pr_.dx)
                climb = math.atan2(pr_.dy, math.hypot(pr_.dx, pr_.dz))
                with rig.at(pr_.x, pr_.y, pr_.z, ry=heading, rz=climb):
                    if pr_.effect == "arrow":
                        forge_models.arrow(rig, pr_.rgb)
                    else:
                        forge_models.thunder_spear(rig, self._time)
                continue
            if pr_.effect not in ("web", "flare", "mote") and models.fiery(pr_.rgb):
                speed = math.sqrt(pr_.dx**2 + pr_.dy**2 + pr_.dz**2) or 1.0
                with rig.at(pr_.x, pr_.y, pr_.z):  # a fireball, its embers trailing behind it
                    models.bolt(rig, pr_.rgb, self._time, (-pr_.dx / speed, -pr_.dy / speed, -pr_.dz / speed))
                continue
            with rig.at(pr_.x, pr_.y, pr_.z, ry=self._time * 6):
                if pr_.effect == "web":
                    models.web_shot(rig, self._time)
                elif pr_.effect == "flare":
                    models.flare(rig, pr_.rgb, min(pr_.life / 0.45, 1.0), self._time)
                elif pr_.effect == "mote":
                    forge_models.mote(rig, self._time)
                else:
                    models.bolt(rig, pr_.rgb, self._time)

    def _draw_ash(self, rig, gpu, far):
        player = self.player
        for f in self.ash:
            if math.hypot(f.x - player.x, f.z - player.z) > far:
                continue
            self._model_light(gpu, f.x, f.y, f.z)
            s = f.size * (0.3 + 0.7 * f.fade)
            rig.part("cube", f.x, f.y, f.z, s, s, s, f.rgb, rx=f.spin, ry=f.spin * 0.7, glow=f.ember)

    def _model_light(self, gpu, x, y, z, flash=False, tint=None):
        light = (2.0, 1.6, 1.6) if flash else [min(c, 1.6) for c in self.builder.model_light_at(x, y, z)]
        if tint and not flash:
            pulse = 0.6 + 0.4 * math.sin(self._time * 6)
            light = [c * (1 - 0.5 * pulse) + t * pulse for c, t in zip(light, tint, strict=True)]
        gpu.model_light(light)

    def _ceil_h(self, p):
        """Height of the ceiling above a prop's floor (3.2 m under open sky)."""
        tile = self.map[p.tx, p.tz]
        return (tile.ceil or tile.floor + 3.2) - tile.floor

    def _draw_prop(self, rig, p):
        t = self._time
        k = p.kind
        if k == "torch":
            if p.wall:
                models.sconce(rig, t + p.tx)
            else:
                models.torch(rig, t)
        elif k == "banner":
            models.banner(rig, t + p.tz, p.tx * 3 + p.tz)
        elif k == "rack":
            models.rack(rig, p.tx + p.tz)
        elif k == "table":
            models.table(rig, t, p.tx * 5 + p.tz)
        elif k == "candles":
            models.candles(rig, t + p.tx, p.tx * 7 + p.tz * 3)
        elif k == "rubble":
            models.rubble(rig, p.tx * 11 + p.tz * 5)
        elif k == "urn":
            models.urn(rig, p.tx * 3 + p.tz * 7, broken=p.open_t > 0)
        elif k == "altar":
            models.warden_altar(rig, p.open_t > 0, t)
        elif k == "brazier":
            models.brazier(rig, t, lit=self.is_lit(p))
        elif k == "bonfire":
            models.bonfire(rig, t + p.tx, lit=self.is_lit(p))
        elif k == "giant_mushroom":
            models.giant_mushroom(rig, p.tx * 5 + p.tz * 3, t)
        elif k == "shelf_fungus":
            models.shelf_fungus(rig, p.tx * 3 + p.tz * 7, t)
        elif k == "mushrooms":
            models.mushrooms(rig, p.tx * 7 + p.tz * 5)
        elif k == "totem":
            models.totem(rig, p.tx * 3 + p.tz, t)
        elif k == "chest":
            models.chest(rig, p.open_t > 0)
        elif k == "door":
            models.door(rig, p.open_t, p.axis)
        elif k == "gate":
            models.door(rig, p.open_t, p.axis, tex="iron_bars")
        elif k == "lever":
            models.lever(rig, p.open_t, p.wall, wood=p.props.get("model") == "wood")
        elif k == "pillar":
            models.pillar(rig, p.tx * 3 + p.tz, self._ceil_h(p))
        elif k == "sarcophagus":
            models.sarcophagus(rig, p.tx * 5 + p.tz)
        elif k == "cage":
            models.cage(rig, t, p.tx * 3 + p.tz, self._ceil_h(p))
        elif k == "cobweb":
            models.cobweb(rig, p.tx * 7 + p.tz)
        elif k == "skull_niche":
            models.skull_niche(rig, t + p.tx, p.tx + p.tz)
        elif k == "grate":
            models.grate(rig, t + p.tx)
        elif k == "roots":
            models.roots(rig, t, p.tx * 5 + p.tz * 3, self._ceil_h(p))
        elif k == "winch":
            turning = any(
                pl.moving and math.hypot(pl.x - p.x, pl.z - p.z) < 4 for pl in self.terrain.platforms
            )
            models.winch(rig, t, turning)
        elif k == "headsman_block":
            models.headsman_block(rig, p.tx + p.tz)
        elif k == "meat_hooks":
            models.meat_hooks(rig, t, p.tx * 3 + p.tz, self._ceil_h(p))
        elif k == "save_statue":
            models.save_statue(rig, t)
        elif k == "tree":
            models.tree(rig, p.tx * 7 + p.tz)
        elif k == "jungle_tree":
            models.jungle_tree(rig, p.tx * 7 + p.tz, t)
        elif k == "fungus":
            models.fungus(rig, p.tx * 5 + p.tz, t)
        elif k == "pickup":
            models.pickup(rig, t)
        elif k == "npc":
            look = NPC_LOOKS.get(p.props.get("id"), {})
            models.npc(
                rig,
                look.get("robe", (110, 110, 110)),
                hair=look.get("hair", (70, 54, 40)),
                t=t + p.tx,
                hood=look.get("hood", False),
                blade=look.get("blade", False),
            )
        elif k == "barrel":
            models.barrel(rig, p.tx * 7 + p.tz, broken=p.open_t > 0)
        elif k == "secret_wall":
            tile = self.map[p.tx, p.tz]
            top = float(p.props["top"]) if "top" in p.props else tile.ceil or tile.floor + 4.0
            tex = {"vines": "vine_wall", "web": "web_wall"}.get(p.props.get("model"), "stone_brick")
            models.secret_wall(rig, top - tile.floor, p.open_t, tex=tex)
        elif k == "cocoon":
            models.cocoon(rig, p.tx * 7 + p.tz * 3, broken=p.open_t > 0)
        elif k == "frog_idol":
            models.frog_idol(rig, p.open_t / FROG_CROAK if p.open_t > 0 else 0.0)
        elif k == "crate":
            models.crate(rig, p.tx * 5 + p.tz * 3, broken=p.open_t > 0)
        elif k == "bones":
            models.bones(rig, p.tx * 3 + p.tz * 11)
        elif k == "chains":
            tile = self.map[p.tx, p.tz]
            models.chains(rig, t + p.tx, (tile.ceil or tile.floor + 3.2) - tile.floor)
        elif k == "shackles":
            models.shackles(rig)
        elif k == "iron_maiden":
            models.iron_maiden(rig, maiden_door(p.open_t))
        elif k == "exit":
            if p.props.get("model") == "well":
                models.well(rig)
            elif p.props.get("model") == "vine_door":
                models.vine_door(rig, t)
            elif p.props.get("model") == "cave_mouth":
                models.cave_mouth(rig, t)
            elif p.props.get("model") == "road_gate":
                forge_models.road_gate(rig)
            else:
                models.rope(rig, t)
        elif k == "spire":
            width = float(p.props["width"]) if "width" in p.props else None
            roof = p.props.get("roof", "cone")
            forge_models.spire(rig, p.tx * 7 + p.tz * 13, float(p.props.get("height", "12")), width, roof)
        elif k == "bastion":
            forge_models.bastion(
                rig,
                p.tx * 7 + p.tz * 13,
                float(p.props.get("top", "6")),
                float(p.props.get("radius", "2.2")),
                float(p.props.get("base", "0")),
            )
        elif k == "smokestack":
            forge_models.smokestack(rig, t + p.tx, float(p.props.get("height", "12")))
        elif k == "gatehouse":
            forge_models.gatehouse(rig, t, p.tx + p.tz, float(p.props.get("base", "6.2")))
        elif k == "keep":
            forge_models.keep(rig, t, p.tx + p.tz)
        elif k == "lavafall":
            forge_models.lavafall(rig, t, float(p.props.get("top", "18")), p.tx)
        elif k == "anvil":
            forge_models.anvil(rig, t + p.tx)
        elif k == "chimney":
            forge_models.chimney(rig, t + p.tx, float(p.props.get("height", "2.6")))
        elif k == "embers":
            forge_models.embers_rain(rig, t, p.tx * 3 + p.tz)


def maiden_door(t):
    """0..1 door opening for the iron maiden `t` seconds into its cycle: open, hold, shut."""
    if t <= 0:
        return 0.0
    if t < 0.6:
        return t / 0.6
    if t < MAIDEN_CYCLE - 0.6:
        return 1.0
    return max((MAIDEN_CYCLE - t) / 0.6, 0.0)
