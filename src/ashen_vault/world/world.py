"""Runtime state of one loaded map: GPU meshes, props, enemies and projectiles."""

import math
import random
from dataclasses import dataclass

from ashen_vault import map_path
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.player.player import Player
from ashen_vault.render import models
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.util import rround
from ashen_vault.world import collision
from ashen_vault.world.ash import AshCloud, death_phases
from ashen_vault.world.hazards import Pendulum, SpikeTrap
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


INTERACT_RANGE = 2.6

# Props that fill their whole tile: nothing walks or flies through them.
BLOCKING_PROPS = ("well", "save_statue", "npc", "barrel", "crate", "iron_maiden")
HAZARD_KINDS = ("spikes", "pendulum")
MAIDEN_CYCLE = 3.0  # seconds the iron maiden's door stays in motion after use

NPC_LOOKS = {
    "odrin": {"robe": (70, 60, 90), "hair": (200, 200, 200)},
    "pell": {"robe": (120, 90, 40)},
    "hollis": {"robe": (80, 84, 90), "hair": (40, 30, 22)},
    "maeve": {"robe": (60, 90, 100), "hair": (140, 70, 40)},
}


class World:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.map = MapLoader.load_file(map_path(name))
        self.builder = MeshBuilder(self.map, lights=MeshBuilder.lights_for(self.map)).build()
        self._meshes = [(game.gpu.upload_batch(batch), tex) for tex, batch in self.builder.batches.items()]
        self.props = []
        self.enemies = []
        self.projectiles = []
        self.hazards = []
        self.ash = AshCloud()
        self._time = 0.0
        self.blocker = self.blocked_tile
        self._spawn_entities()

    def unload(self):
        for mesh, _ in self._meshes:
            self.game.gpu.unload_mesh(mesh)
        self._meshes = []

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
            if spec.kind in HAZARD_KINDS:
                self.hazards.append(self._make_hazard(spec))
            elif not EnemyTypes.has(spec.kind):
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
                )
                if self._opened(prop):
                    prop.open_t = 1.0
                if spec.kind in ("door", "gate"):
                    prop.axis = self._door_axis(spec.tx, spec.tz)
                if spec.kind == "pickup" and key in self.flags:
                    continue
                self.props.append(prop)
        if (
            "boss_dead" in self.flags
            and self.name == "sunken_keep"
            and not self.player.inventory.has("ember_sigil")
            and "sigil_taken" not in self.flags
        ):
            self.drop_sigil(*TileMap.center(15, 4))

    def _make_hazard(self, spec):
        phase = float(spec.props.get("phase", "0"))
        if spec.kind == "spikes":
            return SpikeTrap(spec.tx, spec.tz, phase=phase)
        tile = self.map[spec.tx, spec.tz]
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

    def respawn_enemies(self):
        """Shrine rest: every normal enemy comes back fresh. A living boss is left as it is."""
        bosses = [e for e in self.enemies if e.type.boss and e.alive]
        self.enemies = bosses + spawn_enemies(self.map, self.flags, bosses=False)
        self.projectiles = []

    def _opened(self, prop):
        if prop.kind in ("door", "chest", "lever"):
            return prop.key in self.flags
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
            if p.kind == "exit" and p.props.get("model") == "well":
                return True
        return False

    @property
    def player_x(self):
        return self.player.x

    @property
    def player_z(self):
        return self.player.z

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
        if not tile.walkable or self.blocked_tile(TileMap.tile_coord(nx), TileMap.tile_coord(nz)):
            return
        if abs(tile.floor - self.map.floor_at(enemy.x, enemy.z)) > collision.STEP_HEIGHT:
            return
        enemy.x = nx
        enemy.z = nz

    def enemy_strike(self, enemy):
        dmg = max(
            rround(enemy.type.damage * (0.85 + random.random() * 0.3) - self.player.inventory.defense * 0.5),
            1,
        )
        self.game.hurt_player(dmg, enemy.name)

    def enemy_fire(self, enemy):
        y = self.enemy_y(enemy) + (enemy.type.hover or 1.2)
        dx = self.player.x - enemy.x
        dz = self.player.z - enemy.z
        d = math.hypot(dx, dz) or 1e-6
        self.projectiles.append(
            Projectile(
                x=enemy.x,
                y=y,
                z=enemy.z,
                dx=dx / d * 6,
                dz=dz / d * 6,
                life=4.0,
                damage=enemy.type.damage,
                hostile=True,
                rgb=(255, 120, 40),
            )
        )
        self.game.sfx("spell")

    def enemy_y(self, enemy):
        return self.map.floor_at(enemy.x, enemy.z)

    # --- update --------------------------------------------------------------

    def update(self, dt):
        self._time += dt
        for e in self.enemies:
            e.update(dt, self)
            if not e.alive:
                self._shed_ash(e, dt)
        self.enemies = [e for e in self.enemies if not e.gone]
        self.ash.update(dt)
        for p in self.props:
            if p.kind == "iron_maiden":
                self._update_maiden(p, dt)
            elif 0 < p.open_t < 1.0:
                p.open_t = min(p.open_t + dt * 0.8, 1.0)
        self._update_projectiles(dt)
        self._update_hazards(dt)
        self._push_player_out_of_bodies()

    def _update_hazards(self, dt):
        player = self.player
        for h in self.hazards:
            near = math.hypot(h.x - player.x, h.z - player.z) < 7
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
            pr_.x += pr_.dx * dt
            pr_.z += pr_.dz * dt
            pr_.life -= dt
            tile = self.map.tile_at(pr_.x, pr_.z)
            if (
                tile.solid
                or tile.floor > pr_.y
                or (tile.ceil is not None and tile.ceil < pr_.y)
                or self.blocked_tile(TileMap.tile_coord(pr_.x), TileMap.tile_coord(pr_.z))
            ):
                pr_.life = 0
            elif pr_.hostile:
                if math.hypot(pr_.x - player.x, pr_.z - player.z) < 0.6:
                    self.game.hurt_player(
                        max(rround(pr_.damage - player.inventory.defense * 0.3), 1), "Cinder Wisp"
                    )
                    pr_.life = 0
            else:
                target = next(
                    (
                        e
                        for e in self.enemies
                        if e.alive and math.hypot(pr_.x - e.x, pr_.z - e.z) < e.radius + 0.3
                    ),
                    None,
                )
                if target:
                    self.game.damage_enemy(target, pr_.damage)
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

    def fire_bolt(self, damage):
        player = self.player
        fx, fz = player.forward()
        self.projectiles.append(
            Projectile(
                x=player.x + fx * 0.5,
                y=player.eye_y - 0.25,
                z=player.z + fz * 0.5,
                dx=fx * 9,
                dz=fz * 9,
                life=3.0,
                damage=damage,
                hostile=False,
                rgb=(255, 160, 60),
            )
        )

    def focus(self):
        """Closest interactable prop in front of the player."""
        player = self.player
        fx, fz = player.forward()
        best = None
        best_d = None
        for p in self.props:
            if not self._interactable(p):
                continue
            dx = p.x - player.x
            dz = p.z - player.z
            d = math.hypot(dx, dz)
            in_reach = d < INTERACT_RANGE and (d < 0.8 or (dx * fx + dz * fz) / d > 0.55)
            if in_reach and (best is None or d < best_d):
                best, best_d = p, d
        return best

    @staticmethod
    def _interactable(p):
        if p.kind in ("npc", "save_statue", "exit", "pickup", "iron_maiden"):
            return True
        if p.kind in ("chest", "lever", "door"):
            return p.open_t == 0
        return False

    def open_prop(self, p):
        p.open_t = 0.01
        self.flags.add(p.key)

    def drop_sigil(self, x, z):
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
                props={"item": "ember_sigil"},
                key="sigil",
                yaw=0,
                open_t=0,
            )
        )

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

    def pull_lever(self, p):
        self.open_prop(p)
        self.flags.add(f"lever:{p.props.get('id')}")
        for g in self.props:
            if g.kind == "gate" and g.props.get("lever") == p.props.get("id"):
                g.open_t = 0.01

    # --- rendering ---------------------------------------------------------------

    def draw(self, rig, gpu):
        player = self.player
        for mesh, tex in self._meshes:
            gpu.draw_world_batch(mesh, tex)
        gpu.set_float("isModel", 1.0)
        far = self.meta.get("fog_range", [0, 40])[1] + 2
        for p in self.props:
            if math.hypot(p.x - player.x, p.z - player.z) > far:
                continue
            self._model_light(gpu, p.x, p.y + 1.0, p.z)
            with rig.entity(p.x, p.y, p.z, p.yaw):
                self._draw_prop(rig, p)
        for e in self.enemies:
            if math.hypot(e.x - player.x, e.z - player.z) > far:
                continue
            y = self.enemy_y(e)
            self._model_light(gpu, e.x, y + 1.0, e.z, flash=e.state == "hurt")
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
            if isinstance(h, SpikeTrap):
                self._model_light(gpu, h.x, y + 0.5, h.z)
                with rig.at(h.x, y, h.z):
                    models.spikes(rig, h.height)
            else:
                self._model_light(gpu, h.x, y + 1.5, h.z)
                with rig.at(h.x, h.pivot_y, h.z, ry=0 if h.axis == "x" else -math.pi / 2):
                    models.pendulum(rig, h.angle, h.length)
        self._draw_ash(rig, gpu, far)
        for pr_ in self.projectiles:
            gpu.model_light((1.6, 1.4, 1.2))
            with rig.at(pr_.x, pr_.y, pr_.z, ry=self._time * 6):
                models.bolt(rig, pr_.rgb)

    def _draw_ash(self, rig, gpu, far):
        player = self.player
        for f in self.ash:
            if math.hypot(f.x - player.x, f.z - player.z) > far:
                continue
            self._model_light(gpu, f.x, f.y, f.z)
            s = f.size * (0.3 + 0.7 * f.fade)
            rig.part("cube", f.x, f.y, f.z, s, s, s, f.rgb, rx=f.spin, ry=f.spin * 0.7, glow=f.ember)

    def _model_light(self, gpu, x, y, z, flash=False):
        light = (2.0, 1.6, 1.6) if flash else [min(c, 1.6) for c in self.builder.light_at(x, y, z)]
        gpu.model_light(light)

    def _draw_prop(self, rig, p):
        t = self._time
        k = p.kind
        if k == "torch":
            models.torch(rig, t)
        elif k == "brazier":
            models.brazier(rig, t)
        elif k == "chest":
            models.chest(rig, p.open_t > 0)
        elif k == "door":
            models.door(rig, p.open_t, p.axis)
        elif k == "gate":
            models.door(rig, p.open_t, p.axis, tex="iron_bars")
        elif k == "lever":
            models.lever(rig, p.open_t > 0)
        elif k == "save_statue":
            models.save_statue(rig, t)
        elif k == "tree":
            models.tree(rig, p.tx * 7 + p.tz)
        elif k == "pickup":
            models.pickup(rig, t)
        elif k == "npc":
            look = NPC_LOOKS.get(p.props.get("id"), {})
            models.npc(
                rig, look.get("robe", (110, 110, 110)), hair=look.get("hair", (70, 54, 40)), t=t + p.tx
            )
        elif k == "barrel":
            models.barrel(rig, p.tx * 7 + p.tz)
        elif k == "crate":
            models.crate(rig, p.tx * 5 + p.tz * 3)
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
            else:
                models.rope(rig, t)


def maiden_door(t):
    """0..1 door opening for the iron maiden `t` seconds into its cycle: open, hold, shut."""
    if t <= 0:
        return 0.0
    if t < 0.6:
        return t / 0.6
    if t < MAIDEN_CYCLE - 0.6:
        return 1.0
    return max((MAIDEN_CYCLE - t) / 0.6, 0.0)
