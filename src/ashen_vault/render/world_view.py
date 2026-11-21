"""How a World looks: the map's baked mesh and props uploaded to the GPU, and every model drawn each
frame (props, platforms, foes, hazards, projectiles). The World holds the state; this only reads it."""

import math

from ashen_vault.render import (
    cemetery_models,
    forge_models,
    fortress_props,
    models,
    moon_models,
    prison_models,
    prop_bake,
    sewer_models,
    sunken_models,
    town_models,
)
from ashen_vault.render.mesh_builder import Batch, MeshBuilder
from ashen_vault.render.rig import Rig
from ashen_vault.util import rround
from ashen_vault.world import fences, great_gate, sea, sky, terrain, vault, villagers
from ashen_vault.world.ash import death_phases, rise_phases
from ashen_vault.world.hazards import CrumbleFloor, FlameJet, MagmaVent, SpikeTrap
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import (
    FROG_CROAK,
    LANDMARKS,
    RISE,
    STATIC_PROPS,
    TOWN_PROPS,
    flag,
    hinged,
    maiden_door,
)

LADDER_BACK = 0.7  # metres a sewer ladder stands back from its tile's middle, against the wall behind

DOOR_FRAME_SKY = 5.2  # an iron door's masonry under the open sky: tall enough to hide its raised leaf

WOODEN_LIFT_MAPS = ("verdant_hollow",)  # where the lifts' call plates are the jungle's rough timber

FALL_LIP = 0.4  # metres below the vault a waterfall without its own `top` spills from

SHIMMER_NEAR = 4.0  # metres within which a fake wall's motes give it away

HIT_RED = (2.2, 0.6, 0.5)  # the light a foe glows in the moment a blow lands (Enemy.flashing)

STATUS_TINT = {"poison": (0.45, 1.1, 0.3), "burn": (1.5, 0.7, 0.25)}

DETAIL_RANGE = 14.0  # metres within which fine carving (a statue's claws and fangs) is drawn

BEHIND_MARGIN = 3.0  # metres behind the eye a prop may reach and still poke into view (a wide model)


def secret_wall_tex(map_, tx, tz):
    """The texture an illusory wall on tile (tx, tz) takes: that of the real walls beside it (the one
    most of them share; on a tie, north first, then east, south, west), so it passes for one of
    them in any map. With no wall beside it, the side texture of its own tile."""
    texes = [
        map_[tx + dx, tz + dz].wall_tex
        for dx, dz in ((0, -1), (1, 0), (0, 1), (-1, 0))
        if map_[tx + dx, tz + dz].solid and map_[tx + dx, tz + dz].wall_tex
    ]
    if not texes:
        return map_[tx, tz].wall_tex or "stone_brick"
    return max(texes, key=texes.count)


def behind_view(dx, dz, fx, fz, margin=BEHIND_MARGIN):
    """Whether something at (dx, dz) from the eye lies wholly behind it, looking along (fx, fz): the
    view is far narrower than a half turn, so it cannot be seen and need not be drawn."""
    return dx * fx + dz * fz < -margin


class WorldView:
    """The GPU side of a World: its uploaded meshes and baked props, and the drawing of it all."""

    def __init__(self, world, gpu):
        self.world = world
        self.gpu = gpu
        self._meshes = []
        self._sea = None  # the open sea's mesh (`world/sea.py`), drawn with its own thin fog
        self._glitter = None  # (key, mesh) of the sun's path of glints on it
        self._baked = []  # (mesh, tex, chunk, landmark) of the static props, `prop_bake`
        self._baking = False
        self.builder = None

    def bake(self):
        """Builds the map's mesh with its light baked in, and uploads it (again, after a fire is lit)."""
        world = self.world
        self.unload()
        lights = MeshBuilder.lights_for(world.map, lit=world._light_on)
        self.builder = MeshBuilder(world.map, lights=lights).build()
        self._meshes = [(self.gpu.upload_batch(b), tex) for tex, b in self.builder.batches.items()]
        if self.builder.sea.vertex_count:
            self._sea = self.gpu.upload_batch(self.builder.sea)

    def unload(self):
        for mesh, _ in self._meshes:
            self.gpu.unload_mesh(mesh)
        self._meshes = []
        if self._sea is not None:
            self.gpu.unload_mesh(self._sea)
            self._sea = None
        self._unload_glitter()
        self._unload_baked()

    def _unload_baked(self, chunks=None):
        keep = []
        for entry in self._baked:
            if chunks is None or entry[2] in chunks:
                self.gpu.unload_mesh(entry[0])
            else:
                keep.append(entry)
        self._baked = keep

    def bake_props(self, chunks=None):
        """Bakes the static props (of `chunks`, or all) into lit world-space batches, one per chunk,
        texture and draw range. Only a real GPU can: a headless one has no primitives to bake."""
        world = self.world
        tris = getattr(self.gpu, "primitive_tris", None)
        if tris is None:
            return
        self._unload_baked(chunks)
        baker = prop_bake.PropBaker(tris, self._bake_light)
        rig = Rig(baker)
        self._baking = True
        try:
            for p in world.props:
                chunk = prop_bake.chunk_of(p.tx, p.tz)
                if p.kind not in STATIC_PROPS or (chunks is not None and chunk not in chunks):
                    continue
                baker.group = (chunk, p.kind in LANDMARKS)
                # big enough for the light to change across it (a colossal pillar, from floor to vault)
                baker.spread = p.kind in LANDMARKS or p.props.get("model") == "colossal"
                self._model_light(baker, p.x, p.y + 1.0, p.z)
                with rig.entity(p.x, p.y, p.z, p.yaw):
                    self._draw_prop(rig, p)
        finally:
            self._baking = False
        for ((chunk, landmark), tex), batch in baker.batches.items():
            self._baked.append((self.gpu.upload_batch(batch), tex, chunk, landmark))

    def add_light(self, p, spec):
        """Bakes the light of a fire just kindled (`spec`, the entity of prop `p`) into the map's mesh,
        uploading again only the batches it reaches, and bakes the props round it again."""
        light = MeshBuilder.light_for(self.world.map, spec)
        for tex in self.builder.add_light(light):
            i = next(i for i, (_, t) in enumerate(self._meshes) if t == tex)
            self.gpu.unload_mesh(self._meshes[i][0])
            self._meshes[i] = (self.gpu.upload_batch(self.builder.batches[tex]), tex)
        self._rebake_near(p.x, p.z, MeshBuilder.light_for(self.world.map, spec).radius)

    def _bake_light(self, x, y, z):
        """The light a part of a big baked prop takes at its own centre, as `_model_light` gives it."""
        return [min(c, 1.6) for c in self.builder.model_light_at(x, y, z)]

    def _rebake_near(self, x, z, radius):
        """Bakes again the static props a new light can reach: the chunks within its radius."""
        world = self.world
        chunks = {
            prop_bake.chunk_of(p.tx, p.tz)
            for p in world.props
            if p.kind in STATIC_PROPS and math.hypot(p.x - x, p.z - z) < radius + prop_bake.CHUNK_REACH
        }
        if chunks:
            self.bake_props(chunks)

    def _unload_glitter(self):
        if self._glitter is not None:
            self.gpu.unload_mesh(self._glitter[1])
            self._glitter = None

    def glitter_batch(self, dark=0.0, veil=False):
        """The sun's path of glints on the open sea as an uploadable batch, for where you stand now;
        None without an open sea or a sun over it."""
        world = self.world
        spec = sky.get(world.meta)
        if self._sea is None or spec is None or not spec.sun:
            return None
        z_from = min(tz for _tx, tz, _ in sea.deep_tiles(world.map)) * TileMap.TILE
        frame = int(world._time / sea.GLITTER_FRAME)
        built = sea.glitter(
            rround(world.player.x), rround(world.player.z), z_from, sea.level(world.map), spec.sun_at, frame
        )
        if built is None:
            return None
        verts, uvs, weights = built
        rgb = sky.sun_color(spec, dark, veil)
        batch = Batch(verts=verts, uvs=uvs)
        for w in weights:
            batch.colors.extend(c * w for c in rgb)
        return batch

    def _draw_sea(self, gpu, fog_range, dark, veil):
        """The open sea under its own thin fog, so it runs on to the horizon, and the sun's glints."""
        world = self.world
        if self._sea is None:
            return
        gpu.set_vec2("fogRange", sea.fog_range(fog_range))
        gpu.draw_world_batch(self._sea, "water")
        key = (
            rround(world.player.x),
            rround(world.player.z),
            int(world._time / sea.GLITTER_FRAME),
            rround(dark * 48),
            veil,
        )
        if self._glitter is None or self._glitter[0] != key:
            self._unload_glitter()
            batch = self.glitter_batch(dark, veil)
            if batch is not None:
                self._glitter = (key, gpu.upload_batch(batch))
        if self._glitter is not None:
            gpu.set_vec2("fogRange", sea.glitter_fog_range(fog_range))
            gpu.draw_world_batch(self._glitter[1], "glitter")
        gpu.set_vec2("fogRange", fog_range)

    def draw(self, rig, gpu, fog_range=(8.0, 40.0), dark=0.0, veil=False):
        world = self.world
        player = world.player
        for mesh, tex in self._meshes:
            gpu.draw_world_batch(mesh, tex)
        self._draw_sea(gpu, fog_range, dark, veil)
        gpu.set_float("isModel", 1.0)
        sight = world.meta.get("fog_range", [0, 40])[1] + 2
        # Small models stop being drawn sooner than the fog's end on a map that sees far (the
        # fortress from its bridge); landmarks are drawn as far as the eye can see.
        far = min(float(world.meta.get("model_range", sight)), sight)
        if "indoor_range" in world.meta and world.map.tile_at(player.x, player.z).ceil is not None:
            far = min(far, float(world.meta["indoor_range"]))  # under a roof the far rooms are walled off
        fx, fz = player.forward()
        self._draw_baked(gpu, sight, far, fx, fz)
        gpu.set_float("isModel", 1.0)
        for p in world.props:
            if p.kind in STATIC_PROPS and self._baked:
                continue
            if math.hypot(p.x - player.x, p.z - player.z) > (sight if p.kind in LANDMARKS else far):
                continue
            if p.kind not in LANDMARKS and behind_view(p.x - player.x, p.z - player.z, fx, fz):
                continue
            self._model_light(gpu, p.x, p.y + 1.0, p.z)
            with rig.entity(p.x, p.y, p.z, p.yaw):
                self._draw_prop(rig, p)
        for (tx, tz), rise in world._thorns.items():
            x, z = TileMap.center(tx, tz)
            if math.hypot(x - player.x, z - player.z) > far:
                continue
            y = world.map[tx, tz].floor
            self._model_light(gpu, x, y + 0.5, z)
            with rig.at(x, y, z):
                models.thorn_plant(rig, tx * 7 + tz * 3, world._time, rise)
        for pl in world.terrain.platforms:
            if math.hypot(pl.x - player.x, pl.z - player.z) > far:
                continue
            self._model_light(gpu, pl.x, pl.deck + 0.5, pl.z)
            shake = math.sin(world._time * 40) * 0.03 * pl.creaking
            with rig.at(pl.x, pl.deck - pl.sink + shake, pl.z):
                if pl.kind == "lift":
                    tile = world.map[TileMap.tile_coord(pl.x), TileMap.tile_coord(pl.z)]
                    chain_h = (tile.ceil or pl.high + 3.0) - pl.deck
                    models.lift(
                        rig, world._time, pl.moving, chain_h, pl.model, pl.doors, pl.plate_sink, pl.locked
                    )
                elif pl.kind == "raft":
                    models.raft(rig, world._time)
                elif pl.kind == "ledge":
                    models.ledge(rig, pl.creaking, int(pl.x * 3 + pl.z * 7))
                elif pl.kind == "boards":
                    models.boards(rig, pl.creaking, broken=not pl.afloat)
                elif pl.kind == "ward":
                    sunken_models.ward_deck(rig, world._time + pl.x * 0.1, pl.lowered, pl.ward)
                elif pl.kind == "bridge":
                    hinge = world._bridge_hinge.get((TileMap.tile_coord(pl.x), TileMap.tile_coord(pl.z)), 0.0)
                    with rig.at(0, 0, 0, ry=hinge):
                        models.bridge(rig, pl.lowered)
                else:
                    models.plank(rig, pl.creaking)
            for c in pl.calls:
                with rig.entity(c.x, c.floor, c.z, math.atan2(c.z - pl.z, c.x - pl.x)):
                    if pl.model == "rune":
                        sunken_models.rune_call_plate(rig, c.sink, cold=pl.fastened_at(c.end))
                    else:
                        models.call_plate(rig, c.sink, wood=world.name in WOODEN_LIFT_MAPS)
        for chute in world.terrain.chutes:
            y = world.map.floor_at(chute.x, chute.z)
            self._model_light(gpu, chute.x, y + 0.8, chute.z)
            back = terrain.PILE_BACK
            with rig.at(
                chute.x - chute.ux * back, y, chute.z - chute.uz * back, ry=math.atan2(chute.ux, chute.uz)
            ):
                models.log_pile(rig, chute.stock, world._time, chute.t / chute.every if chute.active else 0.0)
        for log in world.terrain.logs:
            if math.hypot(log.x - player.x, log.z - player.z) > far:
                continue
            self._model_light(gpu, log.x, log.y + 0.5, log.z)
            yaw = math.atan2(log.dx, log.dz)
            with rig.at(log.x, log.y + terrain.LOG_R, log.z, ry=yaw):
                models.rolling_log(rig, log.spin)
        for pod in world.terrain.pods:
            if math.hypot(pod.x - player.x, pod.z - player.z) > far:
                continue
            self._model_light(gpu, pod.x, pod.y + 0.5, pod.z)
            with rig.at(pod.x, pod.y, pod.z):
                models.spore_pod(rig, world._time, pod.cloud, pod.t / pod.every)
        for e in world.enemies:
            if math.hypot(e.x - player.x, e.z - player.z) > far:
                continue
            y = world.enemy_y(e)
            self._model_light(gpu, e.x, y + 1.0, e.z, flash=e.flashing, tint=STATUS_TINT.get(e.afflicted))
            forming = e.state in ("ashes", "rising") and e.type.rise == "ash"
            if forming:  # the heap it waits in, sinking as it rises out of it
                with rig.at(e.x, y, e.z):
                    if e.type.ash_spread:  # a giant's ash, spread wide over the floor, drawn in under it
                        cemetery_models.ash_spread(
                            rig, world._time, e.rise_progress, e.radius * e.type.ash_spread
                        )
                    cemetery_models.ash_heap(rig, world._time, e.rise_progress, max(e.radius, 0.8) * 1.2)
                if e.state == "ashes":
                    continue
            dying = not e.alive or forming
            if dying:
                ashen, dissolve = rise_phases(e.rise_progress) if forming else death_phases(e.death_progress)
                gpu.set_float("ashen", ashen)
                gpu.set_float("dissolve", dissolve)
                gpu.set_vec2("dissolveSpan", world.body_span(e))
            with rig.entity(e.x, y, e.z, e.yaw):
                models.enemy(rig, e)
            if dying:
                gpu.set_float("ashen", 0.0)
                gpu.set_float("dissolve", 0.0)
        for h in world.hazards:
            if math.hypot(h.x - player.x, h.z - player.z) > far:
                continue
            y = world.map[h.tx, h.tz].floor
            if isinstance(h, CrumbleFloor):
                self._model_light(gpu, h.x, h.floor + 0.5, h.z)
                with rig.at(h.x, h.floor, h.z):
                    models.crumble_slab(rig, h.shake, h.drop, h.rise, world._time + h.tx)
            elif isinstance(h, SpikeTrap):
                self._model_light(gpu, h.x, y + 0.5, h.z)
                with rig.at(h.x, y, h.z):
                    models.spikes(rig, h.height)
            elif isinstance(h, FlameJet):
                self._model_light(gpu, h.x, y + 0.5, h.z, flash=h.reach > 0)
                with rig.at(h.x, y, h.z, ry=-math.atan2(h.dz, h.dx)):
                    forge_models.flame_jet(rig, h.glow, h.reach, h.length * TileMap.TILE, world._time)
            elif isinstance(h, MagmaVent):
                gpu.model_light((1.6, 1.2, 1.0))
                with rig.at(h.x, y, h.z):
                    forge_models.magma_vent(rig, world._time + h.tx)
            else:
                self._model_light(gpu, h.x, y + 1.5, h.z)
                with rig.at(h.x, h.pivot_y, h.z, ry=0 if h.axis == "x" else -math.pi / 2):
                    models.pendulum(rig, h.angle, h.length)
        for f in world.eruptions:
            self._model_light(gpu, f.x, f.floor + 0.5, f.z)
            with rig.at(f.x, f.floor, f.z):
                if f.style == "hands":
                    cemetery_models.ash_hands(rig, f.glow, f.flame, world._time + f.x)
                elif f.style == "filth":
                    sewer_models.filth_burst(rig, f.flame, world._time + f.x)
                elif f.style == "moon":
                    moon_models.moonbeam(rig, f.glow, f.flame, world._time + f.x)
                elif f.style == "core":
                    sunken_models.core_burst(rig, f.glow, f.flame, world._time, f.radius)
                elif f.style == "boulder":
                    sunken_models.boulder_mark(rig, f.glow, f.flame, world._time, f.radius)
                else:
                    models.eruption(rig, f.glow, f.flame, world._time, f.radius)
            bomb = f.bomb()
            if bomb:
                gpu.model_light((1.6, 1.4, 1.2))
                with rig.at(*bomb):
                    if f.style == "core":
                        sunken_models.core_shard(rig, world._time + f.x)
                    elif f.style == "boulder":
                        sunken_models.boulder(rig, world._time, world._time)
                    else:
                        forge_models.magma_bomb(rig, world._time)
        for w in world.shockwaves:
            if w.style in ("ash", "squeal", "blink"):  # lit by the room rather than glowing
                self._model_light(gpu, w.x, w.floor + 1.0, w.z)
            else:
                gpu.model_light((1.6, 1.4, 1.2))
            with rig.at(w.x, w.floor, w.z):
                if w.style == "ash":
                    cemetery_models.ash_billow(rig, w.progress, w.radius, world._time)
                elif w.style == "squeal":
                    sewer_models.squeal_ring(rig, w.progress, w.radius)
                elif w.style == "blink":
                    moon_models.blink_mist(rig, w.progress, w.radius)
                elif w.style == "core":
                    sunken_models.core_ring(rig, w.progress, w.radius)
                else:
                    models.shockwave_ring(rig, w.progress, w.radius)
        for d in world.devils:
            self._model_light(gpu, d.x, d.floor + 1.0, d.z)
            with rig.at(d.x, d.floor, d.z):
                cemetery_models.dust_devil(rig, d.strength, world._time + d.x)
        self._draw_ash(rig, gpu, far)
        for g in world.gouts:
            if g.style == "ash":
                self._model_light(gpu, g.x, g.y, g.z)
            else:
                gpu.model_light((1.6, 1.4, 1.2))
            for i, (x, y, z, size, heat) in enumerate(g.puffs()):
                with rig.at(x, y, z):
                    if g.style == "ash":
                        cemetery_models.dust_puff(rig, size, heat, world._time, seed=i * 1.7)
                    else:
                        models.gout_puff(rig, size, heat, world._time, seed=i * 1.7)
        for pr_ in world.projectiles:
            gpu.model_light((1.6, 1.4, 1.2))
            if pr_.effect in (
                "arrow",
                "thunder",
                "thorn",
                "mote",
                "lance",
                "crescent",
                "rift",
                "moonray",
            ):  # point first
                heading = -math.atan2(pr_.dz, pr_.dx)
                climb = math.atan2(pr_.dy, math.hypot(pr_.dx, pr_.dz))
                with rig.at(pr_.x, pr_.y, pr_.z, ry=heading, rz=climb):
                    if pr_.effect == "arrow":
                        forge_models.arrow(rig, pr_.rgb)
                    elif pr_.effect == "thorn":
                        models.thorn_shot(rig, pr_.rgb, world._time)
                    elif pr_.effect == "mote":
                        forge_models.mote(rig, world._time + id(pr_) % 7)
                    elif pr_.effect == "lance":
                        moon_models.frost_lance(rig, pr_.rgb, world._time + id(pr_) % 3)
                    elif pr_.effect == "crescent":
                        moon_models.crescent_wave(rig, pr_.rgb, pr_.width, pr_.life, world._time)
                    elif pr_.effect == "rift":
                        sunken_models.rift_lance(rig, pr_.rgb, world._time + id(pr_) % 3)
                    elif pr_.effect == "moonray":  # its tail stops short of the eye it left
                        tail = math.dist((pr_.x, pr_.z), (world.player.x, world.player.z)) - 1.0
                        moon_models.moon_ray(rig, pr_.rgb, pr_.width, pr_.life, world._time, tail)
                    else:
                        forge_models.thunder_spear(rig, world._time)
                continue
            if pr_.effect not in ("web", "flare", "mote") and models.fiery(pr_.rgb):
                speed = math.sqrt(pr_.dx**2 + pr_.dy**2 + pr_.dz**2) or 1.0
                with rig.at(pr_.x, pr_.y, pr_.z):  # a fireball, its embers trailing behind it
                    models.bolt(
                        rig, pr_.rgb, world._time, (-pr_.dx / speed, -pr_.dy / speed, -pr_.dz / speed)
                    )
                continue
            with rig.at(pr_.x, pr_.y, pr_.z, ry=world._time * 6):
                if pr_.effect == "web":
                    models.web_shot(rig, world._time)
                elif pr_.effect == "flare":
                    models.flare(rig, pr_.rgb, min(pr_.life / 0.45, 1.0), world._time)
                elif pr_.effect == "mote":
                    forge_models.mote(rig, world._time)
                elif pr_.effect == "ash":
                    cemetery_models.ash_clod(rig, world._time)
                else:
                    models.bolt(rig, pr_.rgb, world._time)

    def _draw_ash(self, rig, gpu, far):
        world = self.world
        player = world.player
        for f in world.ash:
            if math.hypot(f.x - player.x, f.z - player.z) > far:
                continue
            self._model_light(gpu, f.x, f.y, f.z)
            s = f.size * (0.3 + 0.7 * f.fade)
            rig.part("cube", f.x, f.y, f.z, s, s, s, f.rgb, rx=f.spin, ry=f.spin * 0.7, glow=f.ember)

    def _draw_baked(self, gpu, sight, far, fx, fz):
        """The baked static props, chunk by chunk, culled like single props by range and heading."""
        world = self.world
        player = world.player
        reach = prop_bake.CHUNK_REACH
        for mesh, tex, chunk, landmark in self._baked:
            cx, cz = prop_bake.chunk_centre(*chunk)
            dx, dz = cx - player.x, cz - player.z
            if math.hypot(dx, dz) - reach > (sight if landmark else far):
                continue
            if behind_view(dx, dz, fx, fz, BEHIND_MARGIN + reach):
                continue
            gpu.draw_baked_batch(mesh, tex)

    def _model_light(self, gpu, x, y, z, flash=False, tint=None):
        world = self.world
        light = HIT_RED if flash else [min(c, 1.6) for c in self.builder.model_light_at(x, y, z)]
        if tint and not flash:
            pulse = 0.6 + 0.4 * math.sin(world._time * 6)
            light = [c * (1 - 0.5 * pulse) + t * pulse for c, t in zip(light, tint, strict=True)]
        gpu.model_light(light)

    def _ceil_h(self, p):
        """Height of the ceiling above a prop's floor (3.2 m under open sky)."""
        world = self.world
        tile = world.map[p.tx, p.tz]
        return (tile.ceil or tile.floor + 3.2) - tile.floor

    def _draw_prop(self, rig, p):
        draw = PROP_DRAWERS.get(p.kind)
        if draw:
            draw(self, rig, p, self.world._time)

    def _fall_top(self, p):
        """How high over its floor a `waterfall` pours from: its `top=`, else from a fissure just under
        the cavern's vault overhead."""
        world = self.world
        if "top" in p.props:
            return float(p.props["top"])
        if world.vault is None:
            return 12.0
        return world.vault.height_at(p.x, p.z) - FALL_LIP - p.y

    def _draw_town_prop(self, rig, p, k, t):
        world = self.world
        seed = p.tx * 7 + p.tz * 3
        if k == "roof":
            w, d = (int(v) for v in p.props.get("span", "2,2").split(","))
            town_models.roof(
                rig,
                w,
                d,
                ridge=p.props.get("ridge", "x"),
                top=float(p.props.get("top", "4.2")),
                pitch=float(p.props.get("pitch", "2.4")),
                tex=p.props.get("tex", "roof"),
                wall_tex=p.props.get("wall", "timber"),
                eave=float(p.props.get("eave", "0.35")),
                hip=flag(p.props, "hip"),
            )
        elif k == "silent_bell":
            town_models.silent_bell(rig, t)
        elif k == "cathedral_spire":  # `base=` lifts it onto the roof's ridge
            with rig.at(0, float(p.props.get("base", "0")), 0):
                town_models.cathedral_spire(rig, float(p.props.get("height", "18")))
        elif k == "cathedral_tower":  # `shift=dx,dz` centres it over the tiles it stands on
            dx, dz = (float(v) for v in p.props.get("shift", "0,0").split(","))
            with rig.at(dx, 0, dz):
                town_models.cathedral_tower(
                    rig,
                    float(p.props.get("height", "15")),
                    float(p.props.get("width", "3.8")),
                    "turret" not in p.props,
                    float(p.props.get("helm", "7")),
                )
        elif k == "flying_buttress":
            town_models.flying_buttress(rig, seed, float(p.props.get("top", "9")))
        elif k == "stained_window":
            town_models.stained_window(rig, seed)
        elif k in ("rose_window", "crest_plaque", "shutters", "balcony", "jetty"):  # `rise=`: up the wall
            with rig.at(0, float(p.props.get("rise", RISE[k])), 0):
                if k == "rose_window":
                    town_models.rose_window(rig, seed)
                elif k == "crest_plaque":
                    town_models.crest_plaque(rig, seed)
                elif k == "shutters":  # an oak frame in a half-timbered wall, dressed stone in any other
                    wall = world.map.wall_behind(p.tx, p.tz, p.yaw)
                    look = int(p.props.get("seed", seed))  # `seed=`: the windows of one house alike
                    town_models.shutters(rig, look, timber=wall is not None and wall.wall_tex == "timber")
                elif k == "jetty":
                    town_models.jetty(
                        rig, seed, int(p.props.get("len", "3")), float(p.props.get("height", "2.4"))
                    )
                else:
                    town_models.balcony(rig, seed, p.props.get("roof_tex", "violet_slate"))
        elif k == "door_arch":
            town_models.door_arch(
                rig,
                seed,
                float(p.props.get("height", "3.2")),
                float(p.props.get("spring", "2.2")),
                "rose" in p.props,
                leaf=not hinged(p.props),  # a house's own door is drawn apart, as it swings
            )
        elif k == "cathedral_portal":  # `rose=` sets the height of the great rose over it
            town_models.cathedral_portal(
                rig,
                seed,
                float(p.props.get("height", "9")),
                float(p.props.get("rose", "10.6")),
                float(p.props.get("gable", "3.5")),
                float(p.props.get("span", "14.7")),
            )
        elif k in ("grand_stair", "stair_flight"):  # down along its yaw from its top tile
            town_models.grand_stair(
                rig,
                int(p.props.get("run", "5")),
                int(p.props.get("width", "3")),
                float(p.props.get("rise", "0.4")),
                int(p.props.get("steps", "4")),
                float(p.props.get("offset", "0")),
                cheeks=k == "grand_stair",
            )
        elif k == "nave_runner":
            ends = p.props.get("ends", "head,foot").split(",")
            town_models.nave_runner(rig, int(p.props.get("length", "12")), "head" in ends, "foot" in ends)
        elif k == "house_door":
            town_models.house_door(rig, p.open_t, float(p.props.get("spring", "2.2")), seed)
        elif k == "roof_turret":  # `shift=dx,dz` sets it out on the house's corner
            dx, dz = (float(v) for v in p.props.get("shift", "0,0").split(","))
            with rig.at(dx, float(p.props.get("rise", "4.2")), dz):
                town_models.roof_turret(
                    rig,
                    seed,
                    float(p.props.get("height", "3.2")),
                    float(p.props.get("radius", "0.9")),
                    float(p.props.get("cap", "3.6")),
                    p.props.get("roof_tex", "violet_slate"),
                )
        elif k == "rampart_bay":
            town_models.rampart_bay(rig, p.props["kind"], float(p.props["height"]), seed)
        elif k == "wall_tower":
            dx, dz = (float(v) for v in p.props.get("shift", "0,0").split(","))
            with rig.at(dx, 0, dz):
                town_models.wall_tower(
                    rig,
                    seed,
                    float(p.props.get("height", "10")),
                    float(p.props.get("radius", "2.2")),
                    float(p.props.get("cap", "5")),
                    p.props.get("capped", "true") != "false",
                )
        elif k == "banner_pole":
            town_models.banner_pole(rig, t, seed)
        elif k == "fountain":
            town_models.fountain(rig, t, seed)
        elif k == "bench":
            town_models.bench(rig, seed)
        elif k == "hand_cart":
            town_models.hand_cart(rig, seed)
        elif k == "town_statue":
            town_models.town_statue(rig, seed)
        elif k == "hay_wagon":
            town_models.hay_wagon(rig, seed)
        elif k == "cargo":
            town_models.cargo(rig, seed)
        elif k == "pew":
            town_models.pew(rig, seed)
        elif k == "window":
            town_models.window(rig, seed)
        elif k == "bed":
            town_models.bed(rig, seed)
        elif k == "cupboard":
            town_models.cupboard(rig, seed)
        elif k == "shelf":
            town_models.shelf(rig, seed)
        elif k == "hearth":
            town_models.hearth(rig, t + p.tx)
        elif k == "fence":  # its hurdles run on into the fences and walls beside it
            town_models.fence(rig, seed, fences.fence_arms(world.map, p.tx, p.tz, world._fences))
        elif k == "lamp_post":
            town_models.lamp_post(rig, t + p.tx)
        elif k == "boat":
            town_models.boat(rig, t, seed)
        elif k == "shop_sign":
            town_models.shop_sign(rig, p.props.get("emblem", "anvil"))
        elif k == "forge_bellows":
            town_models.forge_bellows(rig, seed)
        elif k == "grindstone":
            town_models.grindstone(rig, seed)
        elif k == "weapon_rack":
            town_models.weapon_rack(rig, seed)
        elif k == "armor_stand":
            town_models.armor_stand(rig, seed)
        elif k == "katana_stand":
            town_models.katana_stand(rig, seed)
        elif k == "bookcase":
            town_models.bookcase(rig, seed, scrolls=p.props.get("style") == "scrolls")
        elif k == "drawers":
            town_models.drawers(rig, seed, apothecary=p.props.get("style") == "apothecary")
        elif k == "dormer":  # `y=` lifts it onto its roof's slope
            with rig.at(0, float(p.props.get("y", "5.6")), 0):
                town_models.dormer(rig, seed, p.props.get("roof_tex", "clay_tile"))
        elif k == "pentice":
            town_models.pentice(
                rig,
                seed,
                int(p.props.get("len", "1")),
                float(p.props.get("height", "2.5")),
                p.props.get("roof_tex", "clay_tile"),
            )
        elif k == "outside_stair":
            town_models.outside_stair(
                rig,
                seed,
                int(p.props.get("run", "2")),
                float(p.props.get("rise", "3")),
                flag(p.props, "flip"),
            )
        elif k == "street_arch":  # `shift=dx,dz` centres it between two tiles, over a street of even width
            dx, dz = (float(v) for v in p.props.get("shift", "0,0").split(","))
            with rig.at(dx, 0, dz):
                town_models.street_arch(
                    rig, seed, int(p.props.get("width", "3")), p.props.get("style", "crenel")
                )


def _draw_pillar(view, rig, p):
    seed = p.tx * 3 + p.tz
    cavern = getattr(view.builder, "vault", None)
    if p.props.get("model") == "colossal" and cavern is not None:  # up to the cavern's vault
        floor = view.world.map[p.tx, p.tz].floor
        sunken_models.colossal_pillar(rig, seed, cavern.column_height(floor, p.x, p.z))
    else:
        models.pillar(rig, seed, view._ceil_h(p))


def _draw_torch(view, rig, p, t):
    if p.wall:
        models.sconce(rig, t + p.tx)
    else:
        models.torch(rig, t)


def _draw_altar(view, rig, p, t):
    if p.props.get("model") == "moon":  # the vigil chapel's, the Moonbrand planted in it
        moon_models.moon_altar(rig, p.open_t > 0, t)
    else:
        models.warden_altar(rig, p.open_t > 0, t, p.props.get("model", "warden"))


def _draw_door(view, rig, p, t):
    world = view.world
    if p.props.get("boss"):
        a = world.arena_at_door(p)
        great = _great_gate(view, rig, p)
        if a and a.fogged(world.flags):
            tile = world.map[p.tx, p.tz]
            height = models.BOSS_DOOR_TOP if great is None else models.GREAT_DOOR_TOP
            if tile.ceil is not None:
                height = min(height, tile.ceil - tile.floor)
            if great is not None:  # its masonry stays round the fog
                models.boss_door(
                    rig, 0.0, p.axis, t, lit=True, boss=p.props["boss"], great=great, leaves=False
                )
            models.fog_gate(rig, t, p.axis, a.sealed, height)
        else:
            lit = not (a and a.cleared(world.flags))
            models.boss_door(rig, p.open_t, p.axis, t, lit=lit, boss=p.props.get("boss"), great=great)
    else:
        tile = world.map[p.tx, p.tz]
        frame = (tile.ceil - tile.floor) if tile.ceil is not None else DOOR_FRAME_SKY
        models.door(rig, p.open_t, p.axis, style=p.props.get("model", "wood"), frame=frame)


def _great_gate(view, rig, p):
    """Where a `door ... great=<side>` stands, as `models.GreatGate`: its facade turned to that side.
    It takes the light out before its facade, where it is seen from, not the dark of its doorway."""
    step = great_gate.outward(p.props, p.axis)
    if step is None:
        return None
    world = view.world
    porch = TileMap.TILE * great_gate.porch(world.map, p.tx, p.tz, step)
    reach = TileMap.TILE + porch
    view._model_light(rig.gpu, p.x + step[0] * reach, p.y + 4.0, p.z + step[1] * reach)
    front = step[0] if p.axis == "x" else -step[1]  # a door's frame turns local +x onto world -z
    return models.GreatGate(front, porch, great_gate.wall_rise(world.map, p.tx, p.tz, p.axis))


def _draw_winch(view, rig, p, t):
    world = view.world
    turning = any(pl.moving and math.hypot(pl.x - p.x, pl.z - p.z) < 4 for pl in world.terrain.platforms)
    models.winch(rig, t, turning)


def _draw_tree(view, rig, p, t):  # `kind=cypress|pine|olive`, or one picked by the tile
    world = view.world
    seed = p.tx * 7 + p.tz
    kind = p.props.get("kind", town_models.TREE_KINDS[seed % len(town_models.TREE_KINDS)])
    near = view._baking or math.hypot(p.x - world.player.x, p.z - world.player.z) < DETAIL_RANGE
    town_models.town_tree(rig, kind, seed, t, near)


def _draw_npc(view, rig, p, t):
    world = view.world
    npc_id = p.props.get("id")
    if npc_id == "enthroned":
        models.enthroned(rig, t)
    else:
        near = view._baking or math.hypot(p.x - world.player.x, p.z - world.player.z) < DETAIL_RANGE
        models.npc(rig, villagers.look(npc_id), t + p.tx, near)


def _draw_secret_wall(view, rig, p, t):
    world = view.world
    tile = world.map[p.tx, p.tz]
    top = float(p.props["top"]) if "top" in p.props else tile.ceil or tile.floor + 4.0
    if p.props.get("model") == "web":
        models.burning_web(rig, top - tile.floor, p.open_t, t)
    else:
        tex = "vine_wall" if p.props.get("model") == "vines" else secret_wall_tex(world.map, p.tx, p.tz)
        near = math.hypot(p.x - world.player.x, p.z - world.player.z) < SHIMMER_NEAR
        models.secret_wall(rig, top - tile.floor, p.open_t, tex=tex, t=t, shimmer=True, near=near)


def _draw_chains(view, rig, p, t):
    world = view.world
    tile = world.map[p.tx, p.tz]
    models.chains(rig, t + p.tx, (tile.ceil or tile.floor + 3.2) - tile.floor)


def _draw_exit(view, rig, p, t):
    world = view.world
    if p.props.get("model") == "well":
        models.well(rig, t)
    elif p.props.get("model") == "vine_door":
        models.vine_door(rig, t)
    elif p.props.get("model") == "cave_mouth":
        models.cave_mouth(rig, t)
    elif p.props.get("model") == "road_gate":
        forge_models.road_gate(rig, t, p.props.get("style", "town"))
    elif p.props.get("model") == "keep_door":
        forge_models.keep_door(rig, t)
    elif p.props.get("model") == "cemetery_gate":  # it swings open once its keeper falls
        cemetery_models.cemetery_gate(rig, 1.0 if world.exit_open(p) else 0.0)
    elif p.props.get("model") == "sewer_grate":
        sewer_models.sewer_grate(rig, t)
    elif p.props.get("model") == "gaol_grate":
        town_models.gaol_grate(rig, t)
    elif p.props.get("model") == "vesper_gate":  # it stands open once the three sigils are taken
        moon_models.vesper_gate(rig, 1.0 if world.exit_open(p) else 0.0, t)
    elif p.props.get("model") == "cistern_breach":
        sunken_models.cistern_breach(rig, t)
    elif p.props.get("model") == "chapel_door":
        moon_models.chapel_door(rig, t)
    elif p.props.get("model") == "sunken_stair":
        sunken_models.sunken_stair(rig, t)
    elif p.props.get("model") == "sewer_ladder":  # set back against the wall behind it, if any
        behind = world.map[p.tx - rround(math.cos(p.yaw)), p.tz - rround(math.sin(p.yaw))]
        sewer_models.sewer_ladder(rig, t, view._ceil_h(p), LADDER_BACK if behind.solid else 0.0)
    else:  # a rope hung from a beam just under the ceiling (high up a well's shaft)
        models.rope(rig, t, view._ceil_h(p) - 0.3)


def _draw_spire(view, rig, p, t):
    width = float(p.props["width"]) if "width" in p.props else None
    roof = p.props.get("roof", "cone")
    forge_models.spire(rig, p.tx * 7 + p.tz * 13, float(p.props.get("height", "12")), width, roof)


def _draw_bastion(view, rig, p, t):
    forge_models.bastion(
        rig,
        p.tx * 7 + p.tz * 13,
        float(p.props.get("top", "6")),
        float(p.props.get("radius", "2.2")),
        float(p.props.get("base", "0")),
    )


def _draw_lavafall(view, rig, p, t):
    top = float(p.props.get("top", "18"))
    forge_models.lavafall(rig, t, top, p.tx)
    if p.props.get("spout") == "gargoyle":  # a stone head on the wall face, spewing it
        with rig.at(0, top - 1.75, 0):
            fortress_props.lava_spout(rig, t, p.tx)


def _draw_gargoyle_statue(view, rig, p, t):
    world = view.world
    near = view._baking or math.hypot(p.x - world.player.x, p.z - world.player.z) < DETAIL_RANGE
    fortress_props.gargoyle_statue(rig, t, p.tx * 7 + p.tz * 3, p.props.get("pose", "hunched"), near)


def _draw_great_window(view, rig, p, t):  # set high in a great wall's face, over the moat it stands in
    with rig.at(0, float(p.props.get("rise", "0")), 0):
        fortress_props.great_window(rig, t, p.tx * 7 + p.tz * 3)


def _draw_moon_window(
    view, rig, p, t
):  # `rise=` hangs it up its wall, `size=` scales it about the wall's face
    size = float(p.props.get("size", "1"))
    with (
        rig.at(-0.95, float(p.props.get("rise", "0")), 0),
        rig.at(0, 0, 0, s=size),
        rig.at(0.95, 0, 0),
    ):
        moon_models.moon_window(rig, p.tx * 7 + p.tz * 3)


def _draw_moon_roof(view, rig, p, t):
    w, d = (int(v) for v in p.props.get("span", "2,2").split(","))
    moon_models.moon_roof(
        rig,
        w,
        d,
        ridge=p.props.get("ridge", "x"),
        top=float(p.props.get("top", "5.5")),
        pitch=float(p.props.get("pitch", "3")),
        eave=float(p.props.get("eave", "0.4")),
        seed=p.tx * 7 + p.tz * 3,
        grand="grand" in p.props,
    )


def _draw_moon_portal(view, rig, p, t):  # `rose=` sets the height of the great rose over it
    moon_models.moon_portal(
        rig,
        p.tx * 7 + p.tz * 3,
        float(p.props.get("height", "14")),
        float(p.props.get("rose", "17.6")),
    )


def _draw_sun_shaft(view, rig, p, t):  # only the rift in the vault it would fall from: no beam
    sunken_models.vault_rift(
        rig,
        float(p.props.get("height", "14")),
        vault.rift_of(p),
        math.radians(float(p.props.get("rift_yaw", "0"))),
    )


def _draw_energy_core(view, rig, p, t):
    world = view.world
    quenched = world.core_quenched()
    tethers = (
        []
        if quenched or view._baking
        else [(e.x - p.x, world.enemy_y(e) - p.y, e.z - p.z) for e in world.core_sustained(p)]
    )
    sunken_models.energy_core(
        rig,
        t + p.tx,
        float(p.props.get("height", "1.2")),
        quenched=quenched,
        shielded=world.core_shielded(p) and not quenched,
        tethers=tethers,
        yaw=p.yaw,
        scale=float(p.props.get("scale", "1")),
    )


def _draw_waterfall(view, rig, p, t):
    sunken_models.waterfall(
        rig,
        t + p.tx * 0.37,
        view._fall_top(p),
        float(p.props.get("width", "3")),
        float(p.props.get("foot", "0")),
    )


# How each kind of prop is drawn: (view, rig, prop, time) -> None. Harrowmere's own (`TOWN_PROPS`) go
# to `WorldView._draw_town_prop`.
PROP_DRAWERS = {
    "torch": _draw_torch,
    "banner": lambda view, rig, p, t: models.banner(rig, t + p.tz, p.tx * 3 + p.tz, burnt="burnt" in p.props),
    "rack": lambda view, rig, p, t: models.rack(rig, p.tx + p.tz),
    "table": lambda view, rig, p, t: models.table(rig, t, p.tx * 5 + p.tz),
    "candles": lambda view, rig, p, t: models.candles(rig, t + p.tx, p.tx * 7 + p.tz * 3),
    "rubble": lambda view, rig, p, t: models.rubble(rig, p.tx * 11 + p.tz * 5),
    "urn": lambda view, rig, p, t: models.urn(rig, p.tx * 3 + p.tz * 7, broken=p.open_t > 0, t=p.break_t),
    "altar": _draw_altar,
    "brazier": lambda view, rig, p, t: models.brazier(rig, t, lit=view.world.is_lit(p)),
    "bonfire": lambda view, rig, p, t: models.bonfire(rig, t + p.tx, lit=view.world.is_lit(p)),
    "giant_mushroom": lambda view, rig, p, t: models.giant_mushroom(rig, p.tx * 5 + p.tz * 3, t),
    "shelf_fungus": lambda view, rig, p, t: models.shelf_fungus(rig, p.tx * 3 + p.tz * 7, t),
    "mushrooms": lambda view, rig, p, t: models.mushrooms(rig, p.tx * 7 + p.tz * 5),
    "totem": lambda view, rig, p, t: models.totem(rig, p.tx * 3 + p.tz, t),
    "chest": lambda view, rig, p, t: models.chest(rig, p.open_t > 0, p.props.get("model", "wood")),
    "door": _draw_door,
    "gate": lambda view, rig, p, t: models.door(rig, p.open_t, p.axis, tex="iron_bars"),
    "lever": lambda view, rig, p, t: models.lever(rig, p.open_t, p.wall, wood=p.props.get("model") == "wood"),
    "pillar": lambda view, rig, p, t: _draw_pillar(view, rig, p),
    "sarcophagus": lambda view, rig, p, t: models.sarcophagus(rig, p.tx * 5 + p.tz),
    "prisoner_remains": lambda view, rig, p, t: prison_models.prisoner_remains(rig, p.tx * 5 + p.tz * 3),
    "old_idol": lambda view, rig, p, t: prison_models.old_idol(rig, p.tx * 7 + p.tz),
    "lyra_statue": lambda view, rig, p, t: prison_models.lyra_ruin(rig, p.tx * 7 + p.tz),
    "cage": lambda view, rig, p, t: models.cage(rig, t, p.tx * 3 + p.tz, view._ceil_h(p)),
    "cobweb": lambda view, rig, p, t: models.cobweb(rig, p.tx * 7 + p.tz),
    "skull_niche": lambda view, rig, p, t: models.skull_niche(rig, t + p.tx, p.tx + p.tz),
    "grate": lambda view, rig, p, t: models.grate(rig, t + p.tx),
    "roots": lambda view, rig, p, t: models.roots(rig, t, p.tx * 5 + p.tz * 3, view._ceil_h(p)),
    "winch": _draw_winch,
    "headsman_block": lambda view, rig, p, t: models.headsman_block(rig, p.tx + p.tz),
    "meat_hooks": lambda view, rig, p, t: models.meat_hooks(rig, t, p.tx * 3 + p.tz, view._ceil_h(p)),
    "save_statue": lambda view, rig, p, t: models.save_statue(rig, t),
    "tree": _draw_tree,
    "jungle_tree": lambda view, rig, p, t: models.jungle_tree(rig, p.tx * 7 + p.tz, t),
    "fungus": lambda view, rig, p, t: models.fungus(rig, p.tx * 5 + p.tz, t),
    "pickup": lambda view, rig, p, t: models.pickup(rig, t, p.props.get("item")),
    "remnant": lambda view, rig, p, t: cemetery_models.remnant(rig, t),
    "npc": _draw_npc,
    "barrel": lambda view, rig, p, t: models.barrel(rig, p.tx * 7 + p.tz, broken=p.open_t > 0, t=p.break_t),
    "secret_wall": _draw_secret_wall,
    "cocoon": lambda view, rig, p, t: models.cocoon(
        rig, p.tx * 7 + p.tz * 3, broken=p.open_t > 0, t=p.break_t
    ),
    "frog_idol": lambda view, rig, p, t: models.frog_idol(
        rig, p.open_t / FROG_CROAK if p.open_t > 0 else 0.0
    ),
    "crate": lambda view, rig, p, t: models.crate(rig, p.tx * 5 + p.tz * 3, broken=p.open_t > 0, t=p.break_t),
    "bones": lambda view, rig, p, t: models.bones(rig, p.tx * 3 + p.tz * 11),
    "chains": _draw_chains,
    "shackles": lambda view, rig, p, t: models.shackles(rig),
    "iron_maiden": lambda view, rig, p, t: models.iron_maiden(rig, maiden_door(p.open_t)),
    "exit": _draw_exit,
    "spire": _draw_spire,
    "bastion": _draw_bastion,
    "smokestack": lambda view, rig, p, t: forge_models.smokestack(
        rig, t + p.tx, float(p.props.get("height", "12"))
    ),
    "gatehouse": lambda view, rig, p, t: forge_models.gatehouse(
        rig, t, p.tx + p.tz, float(p.props.get("base", "6.2"))
    ),
    "keep": lambda view, rig, p, t: forge_models.keep(rig, t, p.tx + p.tz),
    "lavafall": _draw_lavafall,
    "battlement": lambda view, rig, p, t: fortress_props.battlement(
        rig, t, p.tx * 5 + p.tz, float(p.props.get("span", "8"))
    ),
    "gargoyle_statue": _draw_gargoyle_statue,
    "great_window": _draw_great_window,
    "barred_window": lambda view, rig, p, t: fortress_props.barred_window(rig, t, p.tx * 7 + p.tz * 3),
    "forge_hearth": lambda view, rig, p, t: fortress_props.forge_hearth(rig, t, p.tx * 7 + p.tz * 3),
    "quench_trough": lambda view, rig, p, t: fortress_props.quench_trough(rig, t + p.tx),
    "crucible": lambda view, rig, p, t: fortress_props.crucible(rig, t + p.tx),
    "tool_rack": lambda view, rig, p, t: fortress_props.tool_rack(rig, t, p.tx * 7 + p.tz * 3),
    "ingot_pile": lambda view, rig, p, t: fortress_props.ingot_pile(rig, p.tx * 7 + p.tz * 3),
    "slag_heap": lambda view, rig, p, t: fortress_props.slag_heap(rig, p.tx * 7 + p.tz * 3),
    "impaler": lambda view, rig, p, t: fortress_props.impaler(rig, t, p.tx * 7 + p.tz * 3),
    "forge_statue": lambda view, rig, p, t: fortress_props.forge_statue(rig, p.tx * 7 + p.tz * 3),
    "ore_cart": lambda view, rig, p, t: fortress_props.ore_cart(rig, p.tx * 7 + p.tz * 3),
    "anvil": lambda view, rig, p, t: forge_models.anvil(rig, t + p.tx),
    "chimney": lambda view, rig, p, t: forge_models.chimney(
        rig, t + p.tx, float(p.props.get("height", "2.6"))
    ),
    "embers": lambda view, rig, p, t: forge_models.embers_rain(rig, t, p.tx * 3 + p.tz),
    "gravestone": lambda view, rig, p, t: cemetery_models.gravestone(rig, p.tx * 7 + p.tz * 3),
    "open_grave": lambda view, rig, p, t: cemetery_models.open_grave(rig, p.tx * 3 + p.tz),
    "cemetery_gate": lambda view, rig, p, t: cemetery_models.cemetery_gate(
        rig, sentinels=p.props.get("sentinels") != "false"
    ),
    "mourning_statue": lambda view, rig, p, t: cemetery_models.mourning_statue(rig, p.tx * 7 + p.tz * 3),
    "crypt_front": lambda view, rig, p, t: cemetery_models.crypt_front(rig, p.tx * 7 + p.tz * 3),
    "grave_railing": lambda view, rig, p, t: cemetery_models.grave_railing(rig, p.tx * 7 + p.tz * 3),
    "ash_mound": lambda view, rig, p, t: cemetery_models.ash_mound(rig, p.tx * 7 + p.tz * 3),
    "drain_pipe": lambda view, rig, p, t: sewer_models.drain_pipe(rig, t + p.tx, p.tx * 7 + p.tz * 3),
    "sluice_wheel": lambda view, rig, p, t: sewer_models.sluice_wheel(rig, p.tx * 7 + p.tz * 3),
    "outfall_grate": lambda view, rig, p, t: sewer_models.outfall_grate(rig, p.tx * 7 + p.tz * 3),
    "rat_nest": lambda view, rig, p, t: sewer_models.rat_nest(rig, p.tx * 7 + p.tz * 3),
    "inkcaps": lambda view, rig, p, t: sewer_models.inkcaps(rig, p.tx * 7 + p.tz * 3),
    "sump_caps": lambda view, rig, p, t: sewer_models.sump_caps(rig, p.tx * 7 + p.tz * 3),
    "moon_lamp": lambda view, rig, p, t: moon_models.moon_lamp(rig, p.tx * 7 + p.tz * 3),
    "veiled_statue": lambda view, rig, p, t: moon_models.veiled_statue(rig, p.tx * 7 + p.tz * 3),
    "silver_tree": lambda view, rig, p, t: moon_models.silver_tree(rig, p.tx * 7 + p.tz * 3),
    "moon_window": _draw_moon_window,
    "moon_spire": lambda view, rig, p, t: moon_models.moon_spire(
        rig, p.tx * 7 + p.tz * 3, float(p.props.get("height", "14"))
    ),
    "moon_roof": _draw_moon_roof,
    "moon_portal": _draw_moon_portal,
    "sunken_tower": lambda view, rig, p, t: sunken_models.sunken_tower(
        rig, p.tx * 7 + p.tz * 3, float(p.props.get("height", "18"))
    ),
    "wall_crack": lambda view, rig, p, t: sunken_models.wall_crack(
        rig,
        int(p.props["seed"]),
        float(p.props["height"]),
        float(p.props.get("reach", "2")),
        p.props.get("seep") == "true",
    ),
    "sun_shaft": _draw_sun_shaft,
    "ward_crystal": lambda view, rig, p, t: sunken_models.ward_crystal(rig, t + p.tx, view.world.ward_set),
    "energy_core": _draw_energy_core,
    "waterfall": _draw_waterfall,
}
for _kind in TOWN_PROPS:
    PROP_DRAWERS.setdefault(_kind, lambda view, rig, p, t: view._draw_town_prop(rig, p, p.kind, t))
