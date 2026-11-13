"""Runtime state of one loaded map: GPU meshes, props, enemies and projectiles."""

import math
import random
from dataclasses import dataclass

from ashen_vault import map_path
from ashen_vault.ai.enemy import MOVES, Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.player.player import Player
from ashen_vault.render import models
from ashen_vault.render.mesh_builder import MeshBuilder
from ashen_vault.util import rround
from ashen_vault.world import collision, hazards, relics
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
    source: str = ""
    effect: str | None = None  # "web": slows whoever it hits


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
}

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
        self._time = 0.0
        self.blocker = self.blocked_tile
        self.hazards = hazards.Hazards(self.map)
        self._piles = {(TileMap.tile_coord(c.x), TileMap.tile_coord(c.z)) for c in self.hazards.chutes}
        # Thorn floors grow spiked plants; each one's spikes rise (0..1) when stepped in.
        self._thorns = {(tx, tz): 0.0 for tx, tz, tile in self.map.each_tile() if tile.hurt}
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
            if not EnemyTypes.has(spec.kind) and spec.kind not in hazards.HAZARD_KINDS:
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
        for item_id, tx, tz in relics.pending_drops(self.map, self.flags, self.player.inventory.has):
            self.drop_relic(item_id, *TileMap.center(tx, tz))

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
            if p.kind in ("well", "save_statue", "npc"):
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
        base = enemy.type.damage * mult * (0.85 + random.random() * 0.3)
        dmg = max(rround(base - self.player.inventory.defense * 0.5), 1)
        self.game.hurt_player(dmg, enemy.name)

    def enemy_fire(self, enemy, kind="shot"):
        web = kind == "web"
        y = self.enemy_y(enemy) + (enemy.type.hover or 1.2)
        dx = self.player.x - enemy.x
        dz = self.player.z - enemy.z
        d = math.hypot(dx, dz) or 1e-6
        speed = 7.5 if web else 6
        self.projectiles.append(
            Projectile(
                x=enemy.x + dx / d * enemy.radius,
                y=y,
                z=enemy.z + dz / d * enemy.radius,
                dx=dx / d * speed,
                dz=dz / d * speed,
                life=4.0,
                damage=rround(enemy.type.damage * MOVES["web"][2]) if web else enemy.type.damage,
                hostile=True,
                rgb=(230, 230, 220) if web else enemy.type.shot_rgb,
                source=enemy.name,
                effect="web" if web else None,
            )
        )
        self.game.sfx("spell")

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
        return self.hazards.floor(self.player.x, self.player.z)

    def update_hazards(self, dt):
        """River, ravine, platforms, currents, thorns, logs and spores acting on the player."""
        event = self.hazards.update(dt, self.player, self.game.hurt_player, blocked=self.blocker)
        if event == "fell":
            self.game.sfx("hurt")
            self.game.message(FALL_MESSAGES[self.hazards.fell_into])
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
        self.enemies = [e for e in self.enemies if not e.gone]
        for p in self.props:
            if 0 < p.open_t < 1.0:
                p.open_t = min(p.open_t + dt * 0.8, 1.0)
        self._update_projectiles(dt)
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
                        max(rround(pr_.damage - player.inventory.defense * 0.3), 1), pr_.source or "Something"
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
        if p.kind in ("npc", "save_statue", "exit", "pickup"):
            return True
        if p.kind in ("chest", "lever", "door"):
            return p.open_t == 0
        return False

    def open_prop(self, p):
        p.open_t = 0.01
        self.flags.add(p.key)

    def drop_relic(self, item_id, x, z):
        """Leaves a boss relic on the floor as a pickup."""
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
                props={"item": item_id},
                key=relics.get(item_id).key,
                yaw=0,
                open_t=0,
            )
        )

    def remove_prop(self, p):
        if p in self.props:
            self.props.remove(p)

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
        for (tx, tz), rise in self._thorns.items():
            x, z = TileMap.center(tx, tz)
            if math.hypot(x - player.x, z - player.z) > far:
                continue
            y = self.map[tx, tz].floor
            self._model_light(gpu, x, y + 0.5, z)
            with rig.at(x, y, z):
                models.thorn_plant(rig, tx * 7 + tz * 3, self._time, rise)
        for pl in self.hazards.platforms:
            if math.hypot(pl.x - player.x, pl.z - player.z) > far:
                continue
            self._model_light(gpu, pl.x, pl.deck + 0.5, pl.z)
            shake = math.sin(self._time * 40) * 0.03 * pl.creaking
            with rig.at(pl.x, pl.deck - pl.sink + shake, pl.z):
                if pl.kind == "raft":
                    models.raft(rig, self._time)
                elif pl.kind == "ledge":
                    models.ledge(rig, pl.creaking, int(pl.x * 3 + pl.z * 7))
                elif pl.kind == "boards":
                    models.boards(rig, pl.creaking, broken=not pl.afloat)
                else:
                    models.plank(rig, pl.creaking)
        for chute in self.hazards.chutes:
            y = self.map.floor_at(chute.x, chute.z)
            self._model_light(gpu, chute.x, y + 0.8, chute.z)
            back = hazards.PILE_BACK
            with rig.at(
                chute.x - chute.ux * back, y, chute.z - chute.uz * back, ry=math.atan2(chute.ux, chute.uz)
            ):
                models.log_pile(rig, chute.stock, self._time, chute.t / chute.every if chute.active else 0.0)
        for log in self.hazards.logs:
            if math.hypot(log.x - player.x, log.z - player.z) > far:
                continue
            self._model_light(gpu, log.x, log.y + 0.5, log.z)
            yaw = math.atan2(log.dx, log.dz)
            with rig.at(log.x, log.y + hazards.LOG_R, log.z, ry=yaw):
                models.rolling_log(rig, log.spin)
        for pod in self.hazards.pods:
            if math.hypot(pod.x - player.x, pod.z - player.z) > far:
                continue
            self._model_light(gpu, pod.x, pod.y + 0.5, pod.z)
            with rig.at(pod.x, pod.y, pod.z):
                models.spore_pod(rig, self._time, pod.cloud, pod.t / pod.every)
        for e in self.enemies:
            if math.hypot(e.x - player.x, e.z - player.z) > far:
                continue
            y = self.enemy_y(e)
            sink = -e.state_t * 1.1 if e.state == "dead" else 0
            self._model_light(gpu, e.x, y + 1.0, e.z, flash=e.state == "hurt")
            with rig.entity(e.x, y + sink, e.z, e.yaw):
                models.enemy(rig, e)
        for pr_ in self.projectiles:
            gpu.model_light((1.6, 1.4, 1.2))
            with rig.at(pr_.x, pr_.y, pr_.z, ry=self._time * 6):
                if pr_.effect == "web":
                    models.web_shot(rig, self._time)
                else:
                    models.bolt(rig, pr_.rgb)

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
        elif k == "jungle_tree":
            models.jungle_tree(rig, p.tx * 7 + p.tz, t)
        elif k == "fungus":
            models.fungus(rig, p.tx * 5 + p.tz, t)
        elif k == "pickup":
            models.pickup(rig, t)
        elif k == "npc":
            look = NPC_LOOKS.get(p.props.get("id"), {})
            models.npc(
                rig, look.get("robe", (110, 110, 110)), hair=look.get("hair", (70, 54, 40)), t=t + p.tx
            )
        elif k == "exit":
            if p.props.get("model") == "well":
                models.well(rig)
            elif p.props.get("model") == "vine_door":
                models.vine_door(rig, t)
            else:
                models.rope(rig, t)
