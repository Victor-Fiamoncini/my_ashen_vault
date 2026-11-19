"""Runtime state of one loaded map: GPU meshes, props, enemies and projectiles."""

import math
import random
from dataclasses import dataclass, field

from ashen_vault import map_path
from ashen_vault.ai.enemy import (
    ASH_RISE,
    ASH_RISE_AGAIN,
    ASHFALL_RADIUS,
    EXHALE_CONE,
    EXHALE_REACH,
    MOVES,
    SLAM_RADIUS,
    SQUEAL_RADIUS,
    STATUE_BURST,
    Enemy,
)
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.ai.spawns import spawn_enemies
from ashen_vault.player import ailments, remnant
from ashen_vault.player.player import Player
from ashen_vault.player.spells import Spells
from ashen_vault.render import (
    cemetery_models,
    forge_models,
    fortress_props,
    models,
    moon_models,
    prop_bake,
    sewer_models,
    town_models,
)
from ashen_vault.render.mesh_builder import KINDLING, Batch, MeshBuilder
from ashen_vault.render.rig import Rig
from ashen_vault.util import rround
from ashen_vault.world import (
    collision,
    elements,
    hints,
    loot,
    ramparts,
    relics,
    sea,
    shots,
    sky,
    terrain,
    villagers,
)
from ashen_vault.world.arena import Arena, flood
from ashen_vault.world.ash import AshCloud, death_phases, rise_phases
from ashen_vault.world.hazards import (
    CrumbleFloor,
    DustDevil,
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
    lift: object = None  # the terrain.Platform a lift_call lever summons
    goal: float = 0.0  # the open_t a house door is swinging toward (0 shut, 1 open)


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
    # spark; "arrow": an iron bowman's arrow; "thorn": a barbed thorn (a Snare Bloom's, or Thornlash's
    # Thorn Volley, which poisons what it strikes).
    effect: str | None = None
    dy: float = 0.0  # climb (or drop) per second: spells follow the view up and down
    homing: bool = False  # steers itself toward the nearest foe it can see (Arcane Motes)
    inflicts: tuple = ()  # a foe's shot: the ailments it builds in you (`EnemyType.inflicts`)
    # A piercing shot (the Moonless Tachi's Pale Crescent, effect "crescent") cuts through the foes it
    # meets instead of stopping at the first, each only once (`hit_ids`), and only a wall ends it.
    pierce: bool = False
    hit_ids: set = field(default_factory=set)
    width: float = 0.0  # metres across: a wide shot strikes a body this far to either side of its path


@dataclass(eq=False)
class Gout:
    """Pyre's gout of fire, only for show: from your hand along where you aimed, it rushes out to
    its full reach, roils there, then gutters."""

    x: float
    y: float
    z: float
    dx: float  # unit direction it was breathed in
    dy: float
    dz: float
    reach: float
    age: float = 0.0
    style: str = "fire"  # or "ash": the Sexton's breath of grave dust
    LIFE = 0.45  # seconds it burns
    RUSH = 0.12  # seconds its front takes to reach full length
    PUFFS = 9  # balls of flame along its length
    START = 0.8  # metres out from your eyes where the first one burns, clear of the view

    @property
    def alive(self):
        return self.age < self.LIFE

    def puffs(self):
        """(x, y, z, size, heat) of each ball of flame out to the front: they swell with distance and
        shrink as it gutters; `heat` runs from 1 (white-hot, at your hand) to 0 (the red front)."""
        front = self.reach * min(self.age / self.RUSH, 1.0)
        fade = 1.0 - max(0.0, (self.age / self.LIFE - 0.5) / 0.5)
        out = []
        for i in range(self.PUFFS):
            d = self.START + i / (self.PUFFS - 1) * (self.reach - self.START)
            if d > front:
                break
            k = d / self.reach
            rise = 0.25 * k * k + 0.6 * self.age * k  # heat lifts the far end
            size = (0.3 + 1.05 * k) * fade
            out.append((self.x + self.dx * d, self.y + self.dy * d + rise, self.z + self.dz * d, size, 1 - k))
        return out


INTERACT_RANGE = 2.6
LADDER_BACK = 0.7  # metres a sewer ladder stands back from its tile's middle, against the wall behind
DOOR_FRAME_SKY = 5.2  # an iron door's masonry under the open sky: tall enough to hide its raised leaf
# Props you reach from further away: the Silent Bell hangs in the middle of a plinth you can't climb.
INTERACT_REACH = {"silent_bell": 3.8}
WEB_TIME = 2.5  # seconds a web shot slows you
WEB_BURN_RATE = 0.45  # a web wall that fire has caught burns away over 1 / this many seconds
THORN_SENSE = 3.4  # metres at which thorn plants bristle as you approach
FALL_MESSAGES = {
    "river": "The river drags you under and casts you back ashore.",
}
FALL_DEATH = "You fall to your death."
DROWN_DEATH = "The sea drags you under."
DROWN_MESSAGE = "You plunge into the sea, and it will not let you go."
HAZARD_MESSAGES = {
    "landed": "You land hard.",
    "logs_first": "A rotten rope snaps above, and the woodpile starts to roll!",
    "logs_last": "The last log tumbles down. The woodpile is spent.",
    "spores": "Choking spores fill your lungs.",
    "lift_unlocked": "The lift's chain grinds free. It will answer from either end now.",
}
LIFT_LOCKED = "It won't budge. The lift is fastened from the other end."
CALL_REACH_Y = 1.5  # metres above or below a call lever you can still pull it from
# Lifts that a lever unchained in older saves (before they were freed by riding them).
LEGACY_LIFT_LEVERS = {
    ("sunken_keep", 12, 26): "crypt_winch",
    ("sunken_keep", 25, 16): "belfry_winch",
    ("verdant_hollow", 33, 15): "rim_lift",
    ("verdant_hollow", 20, 38): "root_lift",
    ("cinderhold", 19, 24): "smelt_lift",
}
WOODEN_LEVER_MAPS = ("verdant_hollow",)  # where the call levers are the jungle's rough timber

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
    "gargoyle_statue",
    "forge_hearth",
    "quench_trough",
    "crucible",
    "impaler",
    "pew",
    "bed",
    "cupboard",
    "fence",
    "lamp_post",
    "banner_pole",
    "fountain",
    "tree",
    "bench",
    "hand_cart",
    "hay_wagon",
    "cargo",
    "flying_buttress",
    "gravestone",
    "cemetery_gate",
    "mourning_statue",
    "grave_railing",
    "forge_bellows",
    "grindstone",
    "town_statue",
    "forge_statue",
    "ore_cart",
    "armor_stand",
    "katana_stand",
    "bookcase",
    "drawers",
    "moon_lamp",
    "veiled_statue",
    "silver_tree",
)
# How high a low blocking prop reaches above its floor, in metres: a shot flying higher passes over it
# (a bolt over a table, a casket or a barrel). Anything not listed stands full height.
PROP_TOP = {
    "table": 0.85,
    "altar": 1.1,
    "rubble": 0.5,
    "frog_idol": 1.0,
    "sarcophagus": 0.9,
    "gravestone": 1.1,
    "grave_railing": 1.15,
    "headsman_block": 0.7,
    "anvil": 0.95,
    "gargoyle_statue": 2.2,
    "quench_trough": 0.65,
    "crucible": 1.1,
    "pew": 1.3,
    "bed": 0.9,
    "fence": 1.1,
    "rack": 1.5,
    "barrel": 1.1,
    "crate": 1.5,  # sometimes a second crate stands on the first
    "urn": 0.85,
    "cocoon": 0.95,
    "bench": 0.55,
    "hand_cart": 1.2,
    "hay_wagon": 1.8,
    "cargo": 1.2,
    "ore_cart": 1.2,
    "forge_bellows": 1.1,
    "grindstone": 1.2,
    "katana_stand": 1.2,
    "drawers": 1.05,
}
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
    "shelf",
    "hearth",
    "window",
    "barred_window",
    "tool_rack",
    "great_window",
    "crest_plaque",
    "shutters",
    "balcony",
    "stained_window",
    "rose_window",
    "flying_buttress",
    "crypt_front",
    "shop_sign",
    "weapon_rack",
    "drain_pipe",
    "sluice_wheel",
    "outfall_grate",
    "moon_window",
)
# Props drawn as far as the fog lets you see, however far that is: they make a skyline.
LANDMARKS = (
    "spire",
    "keep",
    "bastion",
    "smokestack",
    "gatehouse",
    "lavafall",
    "battlement",
    "great_window",
    "roof",
    "silent_bell",
    "cathedral_spire",
    "cathedral_tower",
    "banner_pole",
    "roof_turret",
    "wall_tower",
    "rampart_bay",
    "moon_spire",
)
# Props that never move, open, break or flicker: they are baked once into world-space batches
# (`render/prop_bake.py`) instead of being drawn part by part every frame. A prop drawn with the time
# `t`, or one whose look follows its state, must not be listed (`tests/test_prop_bake.py`).
STATIC_PROPS = frozenset(
    {
        *("roof", "cathedral_spire", "cathedral_tower", "flying_buttress", "door_arch", "shutters"),
        *("balcony", "window", "stained_window", "rose_window", "crest_plaque", "pew", "shelf"),
        *("bed", "cupboard", "fence", "bench", "hand_cart", "hay_wagon", "cargo", "tree"),
        *("gargoyle_statue", "pillar", "sarcophagus", "headsman_block", "rack", "rubble", "bones"),
        *("shackles", "cobweb", "mushrooms", "slag_heap", "ingot_pile", "gatehouse", "bastion"),
        *("gravestone", "open_grave", "cemetery_gate", "mourning_statue", "crypt_front", "grave_railing"),
        *("shop_sign", "forge_bellows", "grindstone", "town_statue", "forge_statue", "ore_cart"),
        *("roof_turret", "wall_tower", "rampart_bay"),
        *("weapon_rack", "armor_stand", "katana_stand", "bookcase", "drawers"),
        *("sluice_wheel", "outfall_grate", "rat_nest", "inkcaps", "sump_caps"),
        *("moon_lamp", "veiled_statue", "silver_tree", "moon_window", "moon_spire"),
        "ash_mound",
        "spire",
    }
)
# How far up its wall a hung town prop is set, in metres, unless its entity says `rise=`.
RISE = {"rose_window": "6", "crest_plaque": "3", "shutters": "1.7", "balcony": "3.6"}
# Props that turn to face into the room.
FACING_PROPS = (
    *("chest", "altar", "table", "bed", "cupboard", "gargoyle_statue", "forge_hearth"),
    *("bench", "hand_cart", "hay_wagon", "mourning_statue", "forge_bellows", "town_statue", "forge_statue"),
    *("ore_cart", "armor_stand", "katana_stand", "bookcase", "drawers"),
)
# Ways through a wall that its rampart bays keep clear of (`World._dress_ramparts`).
RAMPART_GATES = ("exit", "cemetery_gate", "door", "gate", "door_arch")
# Harrowmere's buildings, furniture and street dressing (`render/town_models.py`).
TOWN_PROPS = (
    "rampart_bay",
    "roof",
    "silent_bell",
    "cathedral_spire",
    "pew",
    "window",
    "bed",
    "cupboard",
    "shelf",
    "hearth",
    "fence",
    "lamp_post",
    "boat",
    "banner_pole",
    "crest_plaque",
    "shutters",
    "balcony",
    "door_arch",
    "cathedral_tower",
    "flying_buttress",
    "stained_window",
    "rose_window",
    "fountain",
    "bench",
    "hand_cart",
    "hay_wagon",
    "cargo",
    "town_statue",
    "shop_sign",
    "forge_bellows",
    "grindstone",
    "roof_turret",
    "wall_tower",
    "house_door",
    "weapon_rack",
    "armor_stand",
    "katana_stand",
    "bookcase",
    "drawers",
)
ANVIL_SOUND = (0.35, 14.0)  # (volume, metres to silence) of the smith's hammer on his anvil
HAZARD_KINDS = ("spikes", "pendulum", "crumble", "flame_jet", "magma_vent")
FALL_DAMAGE = 25
FALL_DEPTH = 1.5  # metres below the pit's rim before a fall counts
LAVA_SHARE = 0.35  # share of your max HP a dip in lava burns away
SECRET_FALL_RATE = 0.7  # per second: a struck fake wall sears and crumbles over about 1.4 s
OPEN_RATE = 0.8  # per second: how fast doors, lids and levers swing
HOUSE_DOOR_RATE = 1.7  # per second: a house door swings open or shut in about 0.6 s
SHIMMER_NEAR = 4.0  # metres within which a fake wall's motes give it away
FOE_DAMAGE = 1.5  # every blow, shot and spell a foe lands on you hits this much harder
LAVA_MIN = 20
MOTE_SIGHT = 14.0  # metres an arcane mote looks for a foe to steer toward
BREATH_STEP = 1.2  # metres between the fire circles of a gargoyle's breath
BREATH_PAST = 2.5  # metres the breath rakes on past where you stand
GRASP_STEP = 1.1  # metres between the hands of the Sexton's grasping ash
GRASP_PAST = 2.0  # metres the line runs on past where you stand
GRASP_HOLD = 1.6  # seconds a hand that catches you holds you (slowed, as by silk)
KNELL_SHOTS = 10  # embers in each ring of the Sexton's knell
KNELL_SPEED = 5.0
# What wounds you when an eruption of each style catches you (fire otherwise).
ERUPTION_SOURCES = {"hands": "The grasping ash", "drowned": "A drowned hand", "moon": "The moonlight"}
SQUEAL_STAGGER = 1.2  # seconds Mother Gnawl's squeal leaves you stumbling
SWARM_SPEED = 7.0  # m/s her litter scurries along the floor
SWARM_HEIGHT = 0.3  # metres off the floor they run
SWARM_ROT = (("rot", 22),)
UNDERTOW_RING = 1.3  # metres from your spot to each of the four hands round it
UNDERTOW_ROT = 25  # rot the drowned's grip builds
GULP_GLOOM = 2.5  # seconds the dark of the Maw's gut stays on your eyes after it spits you out
GULP_DARK = 0.85  # how dark it gets, as on a `dark=` tile
LANCE_SPEED = 10.0  # m/s a lance of moon-frost flies
LANCE_FAN = 0.22  # radians between the lances of a fan of three
LANCE_CHILL = 1.2  # seconds moon-frost numbs your legs (`Player.chill_t`: slowed, as by silk)
MOON_FROST = 30  # frost a shaft of moonlight builds in you (see player/ailments.py)
BLINK_BEHIND = 1.8  # metres behind you a blinker steps out of the moonlight
BLINK_MIST = 1.2  # metres the mist of a blink billows out
MOONBEAM_ASIDE = 2.4  # metres to either side of you the Duchess's second and third shafts fall
MOONFALL_RINGS = ((2.6, 6, 0.3), (4.8, 8, 0.6))  # (radius, shafts, delay) of each ring of the moonfall
SHED_COUNT = 2  # gobbets the Maw sloughs off at a time
SHED_MAX = 4  # it sheds no more while this many of them still crawl
ASH_CLOD = (150, 144, 138)  # the grey of a spadeful of grave ash
MAIDEN_CYCLE = 3.0  # seconds the iron maiden's door stays in motion after use
FROG_CROAK = 1.2  # seconds the stone frog's throat swells after a pat
FROG_GOLD = 33  # coins the frog coughs up the first time it is patted
# Turns that put a drawbridge model's hinge (its local -X edge) on the named side of its tile.
BRIDGE_YAW = {"w": 0.0, "e": math.pi, "n": -math.pi / 2, "s": math.pi / 2}
FOG_WALK_SPEED = 1.6  # m/s: you push through a boss's fog at a slow, steady walk (World.cross_fog)
HIT_RED = (2.2, 0.6, 0.5)  # the light a foe glows in the moment a blow lands (Enemy.flashing)
STATUS_TINT = {"poison": (0.45, 1.1, 0.3), "burn": (1.5, 0.7, 0.25)}
KINDLE_REACH = 1.2  # a flame bolt passing this close to a cold brazier sets it alight
SLAG_GOUTS = 8  # tongues of molten flame Slag Burst throws out around you


# Fire and lava sounds fade with distance: (base volume, metres at which they fall silent).
JET_SOUND = (0.3, 10.0)
LOB_SOUND = (0.25, 26.0)  # a soft warning from across the lava
BOMB_SOUND = (0.25, 14.0)  # a vent's bomb bursting where it lands
ERUPTION_SOUND = (0.6, 24.0)  # a boss's fire column
QUIET = 0.03  # a sound fainter than this is not played at all
SHRINE_REACH = 3.0  # metres: a save made closer than this to a shrine is taken to have been made there


def beside_shrine(map_, x, z, yaw):
    """Where a saved player wakes: where they knelt, unless that is no longer beside a shrine (the map
    was rebuilt since), then on the first open tile beside the nearest shrine, facing it."""
    shrines = [TileMap.center(s.tx, s.tz) for s in map_.entities if s.kind == "save_statue"]
    if not shrines or (
        map_.tile_at(x, z).walkable and any(math.hypot(x - cx, z - cz) <= SHRINE_REACH for cx, cz in shrines)
    ):
        return x, z, yaw
    cx, cz = min(shrines, key=lambda c: math.hypot(c[0] - x, c[1] - z))
    tx, tz = TileMap.tile_coord(cx), TileMap.tile_coord(cz)
    taken = {(s.tx, s.tz) for s in map_.entities}
    for dx, dz in ((0, 1), (1, 0), (-1, 0), (0, -1)):
        if map_[tx + dx, tz + dz].walkable and (tx + dx, tz + dz) not in taken:
            nx, nz = TileMap.center(tx + dx, tz + dz)
            return nx, nz, math.atan2(cz - nz, cx - nx)
    return x, z, yaw


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


def foe_harm(dmg):
    """What a foe's blow, shot or fire does to you before your armour takes its share."""
    return dmg * FOE_DAMAGE


def behind_view(dx, dz, fx, fz, margin=BEHIND_MARGIN):
    """Whether something at (dx, dz) from the eye lies wholly behind it, looking along (fx, fz): the
    view is far narrower than a half turn, so it cannot be seen and need not be drawn."""
    return dx * fx + dz * fz < -margin


class World:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.map = MapLoader.load_file(map_path(name))
        relics.open_gate(game.flags)  # an older save that holds the first three sigils catches up
        self._meshes = []
        self._sea = None  # the open sea's mesh (`world/sea.py`), drawn with its own thin fog
        self._glitter = None  # (key, mesh) of the sun's path of glints on it
        self._baked = []  # (mesh, tex, chunk, landmark) of the static props, `prop_bake`
        self._baking = False
        self._bake()
        self.props = []
        self.enemies = []
        self.projectiles = []
        self.gouts = []  # Pyre's fire, for show
        self.hazards = []
        self.eruptions = []  # fire columns the Warden calls up
        self.shockwaves = []  # rings sent out by his slam (only for show)
        self.gloom_t = 0.0  # seconds left of the dark the Sump Maw's gut leaves on you
        self.devils = []  # the Sexton's whirlwinds of ash
        self._safe = None  # centre of the last solid tile the player stood on
        self.ash = AshCloud()
        self._time = 0.0
        self.blocker = self.blocked_tile
        self.terrain = terrain.Terrain(self.map)
        for p in self.terrain.platforms:
            if p.lever and f"lever:{p.lever}" in game.flags:
                p.locked = False
                p.lowered = 1.0  # a drawbridge let down on an earlier visit is still down
            if p.kind == "lift" and self._lift_freed(p, game.flags):
                p.locked = False
        # Which way each drawbridge hangs from: its `hinge=` side, as a turn of the model.
        self._bridge_hinge = {
            (s.tx, s.tz): BRIDGE_YAW.get(s.props.get("hinge"), 0.0)
            for s in self.map.entities
            if s.kind == "bridge"
        }
        self._piles = {(TileMap.tile_coord(c.x), TileMap.tile_coord(c.z)) for c in self.terrain.chutes}
        # Thorn floors grow spiked plants; each one's spikes rise (0..1) when stepped in.
        self._thorns = {(tx, tz): 0.0 for tx, tz, tile in self.map.each_tile() if tile.hurt}
        self.arenas = []
        self.fog_walk = None  # (x, z) you walk to while pushing through a fog, input locked
        self.hints = hints.build(self.map)
        self._spawn_entities()
        self._bake_props()
        self.arenas = self._build_arenas()
        self.player_blocker = self.player_blocked

    def _bake(self):
        """Builds the map's mesh with its light baked in, and uploads it (again, after a fire is lit)."""
        self.unload()
        lights = MeshBuilder.lights_for(
            self.map, lit=lambda spec: self._lit_key(spec.tx, spec.tz) in self.flags
        )
        self.builder = MeshBuilder(self.map, lights=lights).build()
        self._meshes = [(self.game.gpu.upload_batch(b), tex) for tex, b in self.builder.batches.items()]
        if self.builder.sea.vertex_count:
            self._sea = self.game.gpu.upload_batch(self.builder.sea)

    def unload(self):
        for mesh, _ in self._meshes:
            self.game.gpu.unload_mesh(mesh)
        self._meshes = []
        if self._sea is not None:
            self.game.gpu.unload_mesh(self._sea)
            self._sea = None
        self._unload_glitter()
        self._unload_baked()

    def _unload_baked(self, chunks=None):
        keep = []
        for entry in self._baked:
            if chunks is None or entry[2] in chunks:
                self.game.gpu.unload_mesh(entry[0])
            else:
                keep.append(entry)
        self._baked = keep

    def _bake_props(self, chunks=None):
        """Bakes the static props (of `chunks`, or all) into lit world-space batches, one per chunk,
        texture and draw range. Only a real GPU can: a headless one has no primitives to bake."""
        tris = getattr(self.game.gpu, "primitive_tris", None)
        if tris is None:
            return
        self._unload_baked(chunks)
        baker = prop_bake.PropBaker(tris)
        rig = Rig(baker)
        self._baking = True
        try:
            for p in self.props:
                chunk = prop_bake.chunk_of(p.tx, p.tz)
                if p.kind not in STATIC_PROPS or (chunks is not None and chunk not in chunks):
                    continue
                baker.group = (chunk, p.kind in LANDMARKS)
                self._model_light(baker, p.x, p.y + 1.0, p.z)
                with rig.entity(p.x, p.y, p.z, p.yaw):
                    self._draw_prop(rig, p)
        finally:
            self._baking = False
        for ((chunk, landmark), tex), batch in baker.batches.items():
            self._baked.append((self.game.gpu.upload_batch(batch), tex, chunk, landmark))

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
        self._rebake_near(p.x, p.z, MeshBuilder.light_for(self.map, spec).radius)
        self.game.sfx("kindle", 0.8)
        self.game.message("The fire catches, and the dark draws back.")
        return True

    def _rebake_near(self, x, z, radius):
        """Bakes again the static props a new light can reach: the chunks within its radius."""
        chunks = {
            prop_bake.chunk_of(p.tx, p.tz)
            for p in self.props
            if p.kind in STATIC_PROPS and math.hypot(p.x - x, p.z - z) < radius + prop_bake.CHUNK_REACH
        }
        if chunks:
            self._bake_props(chunks)

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
            if spec.kind == "hint":  # words, not a thing: `hints` shows them
                continue
            x, z = TileMap.center(spec.tx, spec.tz)
            y = self.map[spec.tx, spec.tz].floor
            yaw = float(spec.props.get("yaw", "0")) * math.pi / 180
            wall_yaw = self.map.wall_yaw(spec.tx, spec.tz) if spec.kind in WALL_PROPS else None
            if "yaw" not in spec.props:
                if wall_yaw is not None:
                    yaw = wall_yaw
                elif spec.kind in FACING_PROPS:
                    yaw = self.map.open_facing(spec.tx, spec.tz)
            if spec.kind == "chest":
                x, z = self.map.seated(spec.tx, spec.tz, yaw)
            elif wall_yaw is not None or spec.kind in FACING_PROPS:
                x, z = self.map.backed(spec.tx, spec.tz, yaw)  # against a thin wall's slab
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
                if spec.kind == "door_arch" and hinged(spec.props):
                    self.props.append(
                        Prop(
                            kind="house_door",
                            x=x,
                            z=z,
                            y=y,
                            tx=spec.tx,
                            tz=spec.tz,
                            props=spec.props,
                            key=f"house_door:{self.name}:{spec.tx},{spec.tz}",
                            yaw=yaw,
                        )
                    )  # shut whenever you come: it is never saved
                if spec.kind == "pickup" and key in self.flags:
                    continue
                self.props.append(prop)
                if spec.kind in SPILLING_PROPS and prop.open_t > 0:
                    self._spill(prop)  # a potion left lying in an earlier visit is still there
        self._dress_ramparts()
        self._respill_slain_loot()
        self._place_call_levers()
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
        self.lay_remnant()

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
        self.gouts = []
        self.eruptions = []
        self.shockwaves = []
        self.devils = []

    def _lift_key(self, lift):
        return f"lift:{self.name}:{TileMap.tile_coord(lift.x)},{TileMap.tile_coord(lift.z)}"

    def _lift_freed(self, lift, flags):
        """Ridden once on an earlier visit (or, in an older save, its winch was pulled)."""
        legacy = LEGACY_LIFT_LEVERS.get((self.name, TileMap.tile_coord(lift.x), TileMap.tile_coord(lift.z)))
        return self._lift_key(lift) in flags or (legacy is not None and f"lever:{legacy}" in flags)

    def _place_call_levers(self):
        """A lever on the far landing of every shortcut lift (`terrain.lever_spot`), hung on the wall
        beside the shaft: it tells you the lift is fastened from the other end, and calls it once
        freed. Every other landing calls its lift with the plate in its floor."""
        for i, lift in enumerate(p for p in self.terrain.platforms if p.kind == "lift"):
            spot = terrain.lever_spot(self.map, lift)
            if spot is None:
                continue
            x, z, floor, end, yaw, on_wall = spot
            props = {"end": end}
            if self.name in WOODEN_LEVER_MAPS:
                props["model"] = "wood"
            if not on_wall:
                props["post"] = "1"
            self.props.append(
                Prop(
                    kind="lift_call",
                    x=x,
                    z=z,
                    y=floor,
                    tx=TileMap.tile_coord(x + math.cos(yaw) * 0.1),  # the landing, not the wall it hangs on
                    tz=TileMap.tile_coord(z + math.sin(yaw) * 0.1),
                    props=props,
                    key=f"lift_call:{self.name}:{i}:{end}",
                    yaw=yaw,
                    lift=lift,
                )
            )

    def call_lift(self, prop):
        """Pulls a landing's call lever: the lever springs back, and the lift comes if it can."""
        prop.open_t = 0.01
        self.game.sfx("door", 0.6)
        event = prop.lift.summon(prop.props["end"])
        if event == "lift_locked":
            self.game.message(LIFT_LOCKED)
        elif event:
            self.game.sfx(*terrain.LIFT_SOUND[event])

    def _opened(self, prop):
        if prop.kind in ("door", "chest", "lever", "altar", *BREAKABLE_PROPS):
            return prop.key in self.flags or f"chest:{self.name}:{prop.tx},{prop.tz}" in self.flags
        if prop.kind == "gate":
            return f"lever:{prop.props.get('lever')}" in self.flags
        return False

    # --- boss arenas ------------------------------------------------------------

    def _build_arenas(self):
        """One Arena per `door boss=<dead_flag>`: the tiles its bosses' lair spans behind the door."""
        arenas = []
        doors = [p for p in self.props if p.kind == "door" and p.props.get("boss")]
        gates = {(p.tx, p.tz) for p in doors}
        for p in doors:
            flag = p.props["boss"]
            homes = {
                (TileMap.tile_coord(e.home_x), TileMap.tile_coord(e.home_z))
                for e in self.enemies
                if e.type.dead_flag == flag
            }
            tiles = flood(lambda tx, tz: self.map[tx, tz], homes, gates) if homes else set()
            a = Arena(flag, (p.tx, p.tz), frozenset(tiles or ()), f"fog:{self.name}:{p.tx},{p.tz}", door=p)
            if a.fogged(self.flags):
                p.open_t = 1.0  # the door is gone; only the fog stands there
            arenas.append(a)
        return arenas

    def boss_target(self):
        """(x, z) of the nearest great door whose boss still lives, or of a way on to one (an `exit`
        with `boss=<dead_flag>`, like the Cinderhold's door to its keep). None when this map has no
        boss left (or never had one). The compass points there."""
        p = self.player
        gates = [TileMap.center(*a.gate) for a in self.arenas if a.tiles and not a.cleared(self.flags)]
        gates += [
            (q.x, q.z)
            for q in self.props
            if q.kind == "exit" and q.props.get("boss") and q.props["boss"] not in self.flags
        ]
        if not gates:
            return None
        return min(gates, key=lambda g: math.hypot(g[0] - p.x, g[1] - p.z))

    def boss_bearing(self):
        """The compass heading (degrees, like `Player.heading`) toward `boss_target`, or None."""
        target = self.boss_target()
        if target is None:
            return None
        p = self.player
        return (math.degrees(math.atan2(target[1] - p.z, target[0] - p.x)) + 90) % 360

    def arena_at_door(self, prop):
        return next((a for a in self.arenas if a.door is prop), None)

    def fog_gate(self, prop):
        """The arena whose fog stands at `prop`, if it is a fog you can cross now."""
        a = self.arena_at_door(prop) if prop.kind == "door" else None
        return a if a and a.fogged(self.flags) and not a.sealed else None

    def player_blocked(self, tx, tz):
        """What stops the player: everything that stops a body, and every fog (crossed only on purpose)."""
        if self.blocked_tile(tx, tz):
            return True
        return any(a.gate == (tx, tz) and a.fogged(self.flags) for a in self.arenas)

    def cross_fog(self, arena):
        """Starts the player walking through the fog: from where they stand, straight through the gate,
        to just clear of it on the far side (`_update_fog_walk`). No jump: you see yourself go in."""
        player = self.player
        gx, gz = TileMap.center(*arena.gate)
        reach = TileMap.TILE / 2 + Player.RADIUS + 0.05
        if arena.door.axis == "x":
            self.fog_walk = (gx + (reach if player.x <= gx else -reach), gz)
        else:
            self.fog_walk = (gx, gz + (reach if player.z <= gz else -reach))
        self.game.sfx("spell", 0.5)
        self.game.message("You pass through the fog.")

    def _update_fog_walk(self, dt):
        """Carries the player a step further through the fog, drifting onto the gate's centre line."""
        player = self.player
        tx, tz = self.fog_walk
        dx, dz = tx - player.x, tz - player.z
        dist = math.hypot(dx, dz)
        step = FOG_WALK_SPEED * dt
        if dist <= step:
            player.x, player.z = tx, tz
            self.fog_walk = None
        else:
            player.x += dx / dist * step
            player.z += dz / dist * step

    def mist_arenas(self):
        """You fell: every arena you were fighting in (or stood in, its boss alive) fills with fog."""
        here = (TileMap.tile_coord(self.player.x), TileMap.tile_coord(self.player.z))
        for a in self.arenas:
            if not a.cleared(self.flags) and (a.sealed or here in a.tiles):
                self.flags.add(a.fog_key)

    def _player_inside(self, arena):
        """Whether you stand wholly inside `arena`: on one of its tiles and clear of its doorway."""
        p = self.player
        here = (TileMap.tile_coord(p.x), TileMap.tile_coord(p.z))
        return here in arena.tiles and arena.clear_of_gate(p.x, p.z, Player.RADIUS)

    def _update_arenas(self):
        """Seals and opens the arenas. A lair with two mouths has a door (an Arena) at each, all under
        one flag: they seal, fog and open together, and say so once."""
        here = (TileMap.tile_coord(self.player.x), TileMap.tile_coord(self.player.z))
        told = set()  # (flag, event) already announced this update

        def tell(a, event, message, sound=True):
            if (a.flag, event) in told:
                return
            told.add((a.flag, event))
            if sound:
                self.game.sfx("door")
            self.game.message(message)

        for a in self.arenas:
            if a.sealed and a.cleared(self.flags):
                a.sealed = False
                if a.door.open_t < 1.0:
                    a.door.open_t = max(a.door.open_t, 0.01)
                tell(a, "open", "The way out grinds open.")
                continue
            bosses = [
                (
                    (TileMap.tile_coord(e.x), TileMap.tile_coord(e.z)),
                    e.state not in ("idle", "perched", "dormant", "ashes"),
                )
                for e in self.enemies
                if e.alive and e.type.dead_flag == a.flag
            ]
            inside = here if self._player_inside(a) else None
            if not self.player.alive or not a.should_seal(self.flags, inside, bosses):
                continue
            a.sealed = True
            if a.fogged(self.flags):
                tell(a, "fog", "The fog closes behind you.", sound=False)
            else:
                a.door.open_t = 0.0
                tell(a, "slam", "The great door slams shut behind you!")

    def _door_axis(self, tx, tz):
        """A door blocks the axis it is not aligned with: corridor walls tell us which."""
        return "x" if self.map[tx, tz - 1].solid and self.map[tx, tz + 1].solid else "z"

    # --- queries used by collision and AI ------------------------------------

    def blocked_tile(self, tx, tz):
        for p in self.props:
            if p.tx == tx and p.tz == tz and self._blocks(p):
                return True
        return (tx, tz) in self._piles

    def _blocks(self, p):
        """Whether prop `p` fills its tile right now."""
        if p.kind == "door" and p.props.get("boss"):
            a = self.arena_at_door(p)
            if a is not None:
                return a.blocks(self.flags, p.open_t < 0.9)
        if p.kind in ("door", "gate", "house_door"):
            return p.open_t < 0.9
        if p.kind in BREAKABLE_PROPS:
            return p.open_t == 0
        return p.kind in BLOCKING_PROPS or (p.kind == "exit" and p.props.get("model") == "well")

    def shot_blocked(self, x, y, z):
        """Whether a shot at (x, y, z) runs into a prop on its tile: low props only stop it below their
        top, so a bolt flies on over tables, caskets and barrels."""
        tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
        if (tx, tz) in self._piles:
            return True
        for p in self.props:
            if p.tx != tx or p.tz != tz or not self._blocks(p):
                continue
            if not shots.clears(y, p.y, PROP_TOP.get(p.kind)):
                return True
        return False

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
            if other is enemy or not other.alive or other.state == "ashes":
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
        base = foe_harm(enemy.type.damage * mult * (0.85 + random.random() * 0.3))
        dmg = max(rround(base - self.player.inventory.defense * 0.5), 1)
        return self.strike_player(dmg, enemy.name, enemy.x, enemy.z, enemy.type.inflicts)

    def strike_player(self, dmg, source, ax, az, inflicts=()):
        """A blow from (ax, az): a raised shield takes what it can before the rest lands, and only a
        blow that gets through builds the ailments it `inflicts`. Returns the damage that got through."""
        taken, block = self.player.take_blow(dmg, ax, az)
        if block is not None and block.blocked:
            self.game.blocked(block)
        if taken > 0:
            self.player.wear_armor()  # a foe's blow wears what you wear; traps and falls don't
            self.game.hurt_player(taken, source)
            for kind, amount in inflicts:
                self.afflict_player(kind, amount)
        return taken

    def afflict_player(self, kind, amount):
        """Builds ailment `kind` in the player by `amount`; when it takes hold, it strikes
        (see player/ailments.py). Returns True if it took hold."""
        player = self.player
        if not player.alive or not player.afflict(kind, amount):
            return False
        if kind == "poison":
            self.game.sfx("hiss", 0.9)
            self.game.message("You are {poisoned}!")
        elif kind == "bleed":
            self.game.sfx("bleed")
            self.game.message("Your wounds {burst open}!")
            self.game.hurt_player(ailments.bleed_burst(player.stats.max_hp), "Bleeding")
        elif kind == "rot":
            self.game.sfx("afflict")
            self.game.message("{Rot} sets in. Your flesh greys.")
        elif kind == "corrosion":
            self.game.sfx("afflict", 1.3)
            self.game.message("{Corrosion} eats at your gear!")
            player.corrode()
        elif kind == "frost":
            self.game.sfx("afflict", 1.6)
            self.game.message("{Frostbite} seizes your legs!")
            self.game.hurt_player(ailments.frostbite_burst(player.stats.max_hp), "Frostbite")
        return True

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

    def grasp(self, enemy):
        """The Sexton drives its spade into the ground: hands of ash burst up in a line from it toward
        you and on past, each a moment after the one before. One that catches you hurts and holds you
        (`Eruption` style "hands"). Step sideways out of the line."""
        player = self.player
        dx, dz = player.x - enemy.x, player.z - enemy.z
        d = math.hypot(dx, dz) or 1.0
        ux, uz = dx / d, dz / d
        damage = rround(enemy.type.damage * MOVES["grasp"][2])
        s, n = enemy.radius + 0.8, 0
        while s <= d + GRASP_PAST:
            x, z = enemy.x + ux * s, enemy.z + uz * s
            tile = self.map.tile_at(x, z)
            if tile.solid or not tile.walkable:
                break
            self.eruptions.append(Eruption(x, z, tile.floor, delay=n * 0.15, damage=damage, style="hands"))
            s += GRASP_STEP
            n += 1
        self.game.sfx("quake", 0.7)

    def _choke(self, enemy, move, message):
        """One of the Sexton's ash moves catches you: the blow, and the ash that clogs your stride."""
        if self.enemy_strike(enemy, MOVES[move][2]) > 0:
            self.player.webbed_t = max(self.player.webbed_t, GRASP_HOLD)
            self.game.message(message)

    def exhale(self, enemy):
        """The Sexton breathes out a cone of grave dust from under its hood, EXHALE_REACH long:
        caught in it, you choke and are slowed. Step aside out of it, or back out of its reach."""
        player = self.player
        dx, dz = player.x - enemy.x, player.z - enemy.z
        d = math.hypot(dx, dz)
        y = self.enemy_y(enemy) + 2.0
        ux, uz = math.cos(enemy.yaw), math.sin(enemy.yaw)
        g = Gout(
            enemy.x + ux * enemy.radius,
            y,
            enemy.z + uz * enemy.radius,
            ux,
            -0.25,
            uz,
            EXHALE_REACH,
            style="ash",
        )
        g.LIFE, g.RUSH = 0.9, 0.3
        self.gouts.append(g)
        self.game.sfx("breath", 0.6)
        off = abs((math.atan2(dz, dx) - enemy.yaw + math.pi) % math.tau - math.pi)
        if player.alive and d <= EXHALE_REACH + shots.PLAYER_RADIUS and off <= EXHALE_CONE:
            self._choke(enemy, "exhale", "You choke on grave dust!")

    def ashfall(self, enemy):
        """The Sexton tears an urn of others' ashes from its back and dashes it down: the ash billows
        out all round it, ASHFALL_RADIUS far, from any side. Be out of its reach when the urn breaks."""
        floor = self.enemy_y(enemy)
        self.shockwaves.append(Shockwave(enemy.x, enemy.z, floor, ASHFALL_RADIUS, style="ash"))
        self.game.sfx("quake", 0.8)
        self.game.sfx("crack", 0.7)
        player = self.player
        if player.alive and math.hypot(player.x - enemy.x, player.z - enemy.z) <= ASHFALL_RADIUS:
            self._choke(enemy, "ashfall", "The ash of the dead engulfs you!")

    def dust_devils(self, enemy):
        """The Sexton whirls its spade and raises two whirlwinds of ash, one on either side of it,
        that drift after you (`hazards.DustDevil`)."""
        damage = rround(enemy.type.damage * MOVES["dust_devil"][2])
        for side in (-1, 1):
            a = enemy.yaw + side * math.pi / 2
            x, z = enemy.x + math.cos(a) * (enemy.radius + 1.2), enemy.z + math.sin(a) * (enemy.radius + 1.2)
            if not self._devil_open(x, z):
                x, z = enemy.x + math.cos(enemy.yaw) * 1.5, enemy.z + math.sin(enemy.yaw) * 1.5
            self.devils.append(DustDevil(x, z, self.map.tile_at(x, z).floor, damage, enemy.name))
        self.game.sfx("breath", 0.8)
        self.game.message("The ash rises and whirls about the Sexton!")

    def _devil_open(self, x, z):
        tile = self.map.tile_at(x, z)
        return (
            not tile.solid
            and tile.walkable
            and not self.blocker(TileMap.tile_coord(x), TileMap.tile_coord(z))
        )

    def _update_devils(self, dt):
        player = self.player
        # The whirlwinds die with the Sexton that raised them.
        raisers = {e.name for e in self.enemies if e.alive}
        self.devils = [d for d in self.devils if not d.done and d.source in raisers]
        for d in self.devils:
            dmg = d.update(dt, player.x, player.z, self._devil_open)
            if dmg and player.alive:
                hurt = max(rround(foe_harm(dmg) - player.inventory.defense * 0.3), 1)
                self.game.hurt_player(hurt, "The whirling ash")
                player.webbed_t = max(player.webbed_t, GRASP_HOLD)
                self.game.message("The whirling ash flays you and drags at your legs!")

    def knell(self, enemy, wave):
        """One ring of the Sexton's knell: KNELL_SHOTS embers flung out all round at chest height,
        the second `wave` turned half a gap from the first."""
        y = self.enemy_y(enemy) + 1.2
        damage = rround(enemy.type.damage * MOVES["knell"][2])
        lead = enemy.radius / KNELL_SPEED
        for i in range(KNELL_SHOTS):
            a = enemy.yaw + (i + 0.5 * wave) * math.tau / KNELL_SHOTS
            dx, dz = math.cos(a) * KNELL_SPEED, math.sin(a) * KNELL_SPEED
            self.projectiles.append(
                Projectile(
                    x=enemy.x + dx * lead,
                    y=y,
                    z=enemy.z + dz * lead,
                    dx=dx,
                    dz=dz,
                    life=3.0,
                    damage=damage,
                    hostile=True,
                    rgb=enemy.type.shot_rgb,
                    source=enemy.name,
                    inflicts=enemy.type.inflicts,
                )
            )
        self.game.sfx("bell", 0.9 if wave == 0 else 0.7)

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
        if kind == "bile":
            # A fan of bile spewed from the gullet: four gobbets, the gaps between them wide enough
            # to slip through.
            for spread in (-0.36, -0.12, 0.12, 0.36):
                self._fire_one(enemy, kind, spread)
            self.game.sfx("hiss", 0.9)
            return
        if kind == "swarm":
            # Her litter loosed at you along the floor: five rats in a fan, low enough that only
            # stepping out of their lines avoids them.
            for spread in (-0.4, -0.2, 0.0, 0.2, 0.4):
                self._fire_rat(enemy, spread)
            self.game.sfx("enemy_die", 0.4)
            self.game.message(f"{enemy.type.called}'s litter pours out at you!")
            return
        if kind == "frost_lance":
            # A fan of three lances of moon-frost: each that strikes numbs your legs. Step out of the
            # fan, or between two of its lances.
            for spread in (-LANCE_FAN, 0.0, LANCE_FAN):
                self._fire_one(enemy, kind, spread)
            self.game.sfx("motes", 0.8)
            return
        if kind == "spadeful":
            # A spadeful of grave ash flung in a fan of five clods: each that hits clogs your stride.
            for spread in (-0.44, -0.22, 0.0, 0.22, 0.44):
                self._fire_one(enemy, kind, spread)
            self.game.sfx("quake", 0.5)
            return
        self._fire_one(enemy, kind)
        self.game.sfx("spell")

    def _fire_one(self, enemy, kind, spread=0.0):
        web = kind == "web"
        ash = kind == "spadeful"
        y = self.enemy_y(enemy) + (enemy.type.hover or enemy.type.mouth or 1.2)
        player = self.player
        speed = (
            7.5
            if web
            else 11
            if enemy.type.shot == "arrow"
            else LANCE_SPEED
            if enemy.type.shot == "lance"
            else 6
        )
        dx, dy, dz = shots.toward(
            enemy.x, y, enemy.z, player.x, player.y + shots.AIM_HEIGHT, player.z, speed, spread
        )
        lead = enemy.radius / speed  # leaves from the edge of its body
        damage = enemy.type.damage
        if kind in ("web", "cinders", "spadeful", "fireball", "bile", "frost_lance"):
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
                rgb=(230, 230, 220) if web else ASH_CLOD if ash else enemy.type.shot_rgb,
                source=enemy.name,
                effect="web" if web else "ash" if ash else enemy.type.shot,
                inflicts=enemy.type.inflicts,
            )
        )

    def _fire_rat(self, enemy, spread):
        y = self.enemy_y(enemy) + SWARM_HEIGHT
        player = self.player
        dx, _dy, dz = shots.toward(enemy.x, y, enemy.z, player.x, y, player.z, SWARM_SPEED, spread)
        lead = enemy.radius / SWARM_SPEED
        self.projectiles.append(
            Projectile(
                x=enemy.x + dx * lead,
                y=y,
                z=enemy.z + dz * lead,
                dx=dx,
                dz=dz,
                life=2.0,
                damage=rround(enemy.type.damage * MOVES["swarm"][2]),
                hostile=True,
                rgb=sewer_models.RAT_FUR,
                source=enemy.name,
                effect="rat",
                inflicts=SWARM_ROT,
            )
        )

    def tail_lash(self, enemy):
        """Mother Gnawl whips her tail round through the arc behind her: it lands only on someone still
        standing there, in its reach."""
        player = self.player
        self.game.sfx("swing", 0.8)
        d = math.hypot(player.x - enemy.x, player.z - enemy.z)
        reached = player.alive and enemy.behind_me(player.x, player.z) and d <= enemy.tail_reach() + 0.3
        if reached and self.enemy_strike(enemy, MOVES["tail_lash"][2]) > 0:
            self.game.message(f"{enemy.type.called}'s tail lashes you!")

    def squeal(self, enemy):
        """Mother Gnawl rears and squeals: within SQUEAL_RADIUS, from any side, it pierces you (no
        shield stops a sound) and leaves you stumbling. Be out of earshot when she rears."""
        floor = self.enemy_y(enemy)
        self.shockwaves.append(Shockwave(enemy.x, enemy.z, floor, SQUEAL_RADIUS, style="squeal"))
        self.game.sfx("enemy_die", 1.0)
        player = self.player
        if player.alive and math.hypot(player.x - enemy.x, player.z - enemy.z) <= SQUEAL_RADIUS:
            dmg = foe_harm(enemy.type.damage * MOVES["squeal"][2])
            self.game.hurt_player(max(rround(dmg - player.inventory.defense * 0.3), 1), enemy.name)
            player.webbed_t = max(player.webbed_t, SQUEAL_STAGGER)
            self.game.message(f"{enemy.type.called}'s squeal pierces your skull!")

    def undertow(self, enemy):
        """The Sump Maw sinks into itself: the sludge bubbles where you stand and round it, then the
        hands of the dead it swallowed burst up there (`Eruption` style "drowned"). Step off it."""
        player = self.player
        damage = rround(enemy.type.damage * MOVES["undertow"][2])
        spots = [(player.x, player.z)]
        for i in range(4):
            a = i * math.pi / 2 + enemy.yaw
            spots.append((player.x + math.cos(a) * UNDERTOW_RING, player.z + math.sin(a) * UNDERTOW_RING))
        for n, (x, z) in enumerate(spots):
            tile = self.map.tile_at(x, z)
            if tile.solid or not tile.walkable:
                continue
            self.eruptions.append(
                Eruption(x, z, tile.floor, delay=0.0 if n == 0 else 0.12, damage=damage, style="drowned")
            )
        self.game.sfx("hiss", 1.0)
        self.game.message("The sludge stirs under your feet!")

    def gulp(self, enemy):
        """The Sump Maw's surge has passed over you: it swallows you whole (a heavy blow, as any
        shield allows), and for GULP_GLOOM seconds after it spits you out the dark of its gut stays
        on your eyes."""
        if self.enemy_strike(enemy, MOVES["gulp"][2]) > 0:
            self.gloom_t = GULP_GLOOM
            self.game.sfx("hiss", 1.0)
            self.game.message(f"{enemy.type.called} swallows you whole, and spits you out!")

    def blink(self, enemy):
        """A blinker steps through the moonlight: mist where it stood, and it steps out BLINK_BEHIND
        behind you, or beside you if a wall, a drop or a body is in the way there (on its own floor,
        never across a chasm onto another level). Where there is nowhere to stand it stays put."""
        player = self.player
        fx, fz = player.forward()
        floor = self.enemy_y(enemy)
        for ax, az in ((-fx, -fz), (fz, -fx), (-fz, fx), (fx, fz)):
            x, z = player.x + ax * BLINK_BEHIND, player.z + az * BLINK_BEHIND
            tile = self.map.tile_at(x, z)
            tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
            if tile.hazardous or not collision.passable(self.map, tx, tz, floor, blocked=self.blocker):
                continue
            if abs(tile.floor - floor) > collision.STEP_HEIGHT or not self.can_see(player.x, player.z, x, z):
                continue
            if any(e is not enemy and e.alive and math.hypot(e.x - x, e.z - z) < e.radius + enemy.radius
                   for e in self.enemies):  # fmt: skip
                continue
            self.shockwaves.append(Shockwave(enemy.x, enemy.z, floor, BLINK_MIST, style="blink"))
            enemy.x, enemy.z = x, z
            self.shockwaves.append(Shockwave(x, z, tile.floor, BLINK_MIST, style="blink"))
            self.game.sfx("swoosh", 0.9)
            if enemy.type.boss:
                self.game.message(f"{enemy.type.called} steps out of the moonlight behind you!")
            return True
        return False

    def moonbeam(self, enemy):
        """The Duchess calls the moon down: a shaft of moonlight where you stand, and one to either side
        of you, across your facing (`Eruption` style "moon"). Step forward or back out of the line."""
        player = self.player
        damage = rround(enemy.type.damage * MOVES["moonbeam"][2])
        fx, fz = player.forward()
        spots = [(player.x, player.z, 0.0)]
        for side in (-1, 1):
            spots.append((player.x - fz * side * MOONBEAM_ASIDE, player.z + fx * side * MOONBEAM_ASIDE, 0.15))
        self._moonlight(spots, damage)
        self.game.message("The moonlight gathers over you!")

    def moonfall(self, enemy):
        """Second phase: the moon rains down round you, a shaft where you stand and then rings of them
        farther out (MOONFALL_RINGS). Stand in a gap between the shafts of a ring."""
        player = self.player
        damage = rround(enemy.type.damage * MOVES["moonfall"][2])
        spots = [(player.x, player.z, 0.0)]
        for n, (radius, count, delay) in enumerate(MOONFALL_RINGS):
            for i in range(count):
                a = (i + 0.5 * n) * 2 * math.pi / count + enemy.yaw
                spots.append((player.x + math.cos(a) * radius, player.z + math.sin(a) * radius, delay))
        self._moonlight(spots, damage)
        self.game.message(f"{enemy.type.called} raises her glaive, and the moon falls!")

    def _moonlight(self, spots, damage):
        for x, z, delay in spots:
            tile = self.map.tile_at(x, z)
            if tile.solid or not tile.walkable:
                continue
            self.eruptions.append(Eruption(x, z, tile.floor, delay=delay, damage=damage, style="moon"))
        self.game.sfx("ward", 0.8)

    def dark_here(self):
        """How dark it is where you stand (0..1): the tile's own darkness, or deeper while the dark of
        the Maw's gut is still on your eyes."""
        dark = self.map.tile_at(self.player.x, self.player.z).dark
        return max(dark, GULP_DARK) if self.gloom_t > 0 else dark

    def summon(self, enemy, type_id, count):
        """A boss calls `count` of its brood, spread out around itself."""
        self._spawn_round(enemy, EnemyTypes.get(type_id), count)
        self.game.sfx("enemy_die", 0.5)
        self.game.message(
            f"{enemy.type.called} shrieks, and {'her' if enemy.type.proper else 'its'} brood answers."
        )

    def _spawn_round(self, enemy, type_, count):
        """`count` foes of `type_` spread round `enemy`, already after you (where a wall is in the way,
        on its own spot)."""
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

    def can_shed(self, enemy):
        """Whether the Maw may slough off more gobbets: not while SHED_MAX of them still crawl."""
        alive = sum(e.alive and e.type.id == enemy.type.sheds for e in self.enemies)
        return enemy.type.sheds is not None and alive < SHED_MAX

    def shed(self, enemy):
        """The Maw sloughs SHED_COUNT gobbets of itself off its sides, and they crawl at you."""
        if not self.can_shed(enemy):
            return
        self._spawn_round(enemy, EnemyTypes.get(enemy.type.sheds), SHED_COUNT)
        self.game.sfx("hiss", 1.0)
        self.game.message(f"{enemy.type.called} sloughs off gobbets of itself, and they crawl at you!")

    def split(self, enemy):
        """A slain splitter bursts into `split_count` of its `splits` type, spread round where it fell
        and already after you. Returns them (none for a foe that does not split)."""
        t = enemy.type
        if not t.splits:
            return []
        type_ = EnemyTypes.get(t.splits)
        y = self.enemy_y(enemy)
        out = []
        for i in range(t.split_count):
            a = enemy.yaw + math.pi / 2 + i * 2 * math.pi / t.split_count
            x = enemy.x + math.cos(a) * enemy.radius * 0.8
            z = enemy.z + math.sin(a) * enemy.radius * 0.8
            tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
            if not collision.passable(self.map, tx, tz, y, blocked=self.blocker):
                x, z = enemy.x, enemy.z
            child = Enemy(type_, x, z, yaw=a)
            child.state = "chase"
            out.append(child)
        self.enemies.extend(out)
        self.game.sfx("hiss", 0.6)
        return out

    def player_floor(self):
        return self.terrain.floor(self.player.x, self.player.z)

    def update_terrain(self, dt):
        """River, ravine, platforms, currents, thorns, logs and spores acting on the player."""
        event = self.terrain.update(dt, self.player, self.game.hurt_player, blocked=self.blocker)
        for name, volume in self.terrain.sounds:
            self.game.sfx(name, volume)
        for lift in self.terrain.unlocked:
            self.flags.add(self._lift_key(lift))
        if event == "fell":
            self.game.sfx("hurt")
            self.game.message(FALL_MESSAGES[self.terrain.fell_into])
        elif event == "fell_dead" and self.terrain.plunging and self.terrain.fell_into == "sea":
            self.game.sfx("hurt")
            self.game.message(DROWN_DEATH)
        elif event == "fell_dead":
            self.game.sfx("hurt")
            self.game.sfx("crack", 0.8)
            self.game.message(FALL_DEATH)
        elif event == "drown":
            self.game.message(DROWN_MESSAGE)
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
        if self.fog_walk:
            self._update_fog_walk(dt)
        for e in self.enemies:
            was, rose = e.state, e.rise_progress
            e.update(dt, self)
            if e.state == "rising":
                self._rising(e, was != "rising", rose, dt)
            harm = e.status_tick(dt)
            if harm:
                self.game.damage_enemy(e, harm, stagger=False)
            if not e.alive:
                self._shed_ash(e, dt)
        self.enemies = [e for e in self.enemies if not e.gone]
        self.ash.update(dt)
        for p in self.props:
            if p.kind == "npc":
                self._update_smith(p, dt)
            elif p.kind == "iron_maiden":
                self._update_maiden(p, dt)
            elif p.kind == "lift_call" and p.open_t > 0:  # thrown, then it springs back
                p.open_t = p.open_t + dt * 1.6 if p.open_t + dt * 1.6 < 1.0 else 0.0
            elif p.kind == "frog_idol" and p.open_t > 0:
                p.open_t = p.open_t + dt if p.open_t + dt < FROG_CROAK else 0.0
            elif p.kind == "house_door":
                step = dt * HOUSE_DOOR_RATE
                p.open_t = min(p.open_t + step, p.goal) if p.goal > p.open_t else max(p.open_t - step, p.goal)
            elif 0 < p.open_t < 1.0:
                p.open_t = min(p.open_t + dt * self._open_rate(p), 1.0)
        self._update_remnant()
        self._update_projectiles(dt)
        for g in self.gouts:
            g.age += dt
        self.gouts = [g for g in self.gouts if g.alive]
        self._update_hazards(dt)
        self._update_fire(dt)
        self._check_fall()
        self._push_player_out_of_bodies()
        self._update_thorns(dt)
        self._update_arenas()
        self._update_hints()

    def _update_hints(self):
        """A tutorial hint shows the first time you step onto its tile, and never again."""
        if not self.player.alive:
            return
        here = (TileMap.tile_coord(self.player.x), TileMap.tile_coord(self.player.z))
        hint = hints.due(self.hints, here, self.flags, self.name)
        if hint is None:
            return
        self.flags.add(hint.flag(self.name))
        for line in hint.lines:
            self.game.message(line)

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
                if h.update(dt):
                    self.sfx_near("jet", h.x, h.z, *JET_SOUND)
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

    def _update_smith(self, p, dt):
        """A smith at work rings his anvil each time his hammer lands (his model keeps the same time)."""
        if villagers.look(p.props.get("id")).idle != "smith":
            return
        t = self._time + p.tx  # the villager's own clock, as `_draw_props` gives `models.npc`
        if villagers.smith_blows(t - dt, t):
            self.sfx_near("anvil", p.x, p.z, *ANVIL_SOUND)

    def sfx_near(self, name, x, z, volume, reach):
        """Plays a sound from (x, z), fading with your distance from it to silence at `reach`."""
        d = math.hypot(x - self.player.x, z - self.player.z)
        loud = volume * max(1 - d / reach, 0.0)
        if loud >= QUIET:
            self.game.sfx(name, loud)

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
            self.sfx_near("lob", h.x, h.z, *LOB_SOUND)

    def _update_fire(self, dt):
        """The Warden's fire columns and slam rings, the hands that burst up, and the Maw's gloom."""
        player = self.player
        self.gloom_t = max(self.gloom_t - dt, 0.0)
        for f in self.eruptions:
            if f.update(dt):
                sound = {"hands": "quake", "drowned": "hiss", "moon": "motes"}.get(f.style, "eruption")
                self.sfx_near(sound, f.x, f.z, *(BOMB_SOUND if f.origin else ERUPTION_SOUND))
            if player.alive:
                dmg = f.hit(player.x, player.z)
                if dmg:
                    hands = f.style in ("hands", "drowned")
                    if f.style == "moon":
                        player.chill_t = max(player.chill_t, LANCE_CHILL)
                    if f.origin is None:  # a foe's fire, not a magma vent's bomb
                        dmg = foe_harm(dmg)
                    hurt = max(rround(dmg - player.inventory.defense * 0.3), 1)
                    self.game.hurt_player(hurt, ERUPTION_SOURCES.get(f.style, "The fire"))
                    if hands:
                        player.webbed_t = max(player.webbed_t, GRASP_HOLD)
                    if f.style == "hands":
                        self.game.message("Hands of ash clutch at your legs!")
                    elif f.style == "drowned":
                        self.afflict_player("rot", UNDERTOW_ROT)
                        self.game.message("The drowned drag at your legs!")
                    elif f.style == "moon":
                        self.game.message("The moonlight burns you with cold!")
                        self.afflict_player("frost", MOON_FROST)
        self.eruptions = [f for f in self.eruptions if not f.done]
        for w in self.shockwaves:
            w.update(dt)
        self.shockwaves = [w for w in self.shockwaves if not w.done]
        self._update_devils(dt)

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
        """Shoves the player in small steps so walls stop the push (and ends a lunge under way)."""
        player = self.player
        player.cancel_lunge()
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

    def rise_time(self, enemy):
        """How long a boss of ash takes to rise once you step into its lair (shorter when you come back
        through the fog you left dying), or None while you stand outside it. A boss with no lair
        rises when it notices you."""
        arena = next((a for a in self.arenas if a.flag == enemy.type.dead_flag and a.tiles), None)
        if arena is None:
            near = math.hypot(self.player.x - enemy.x, self.player.z - enemy.z) <= enemy.type.sight
            return ASH_RISE if near and self.can_see(enemy.x, enemy.z, self.player.x, self.player.z) else None
        if not self.player.alive or not self._player_inside(arena):
            return None
        return ASH_RISE_AGAIN if arena.fogged(self.flags) else ASH_RISE

    def _rising(self, e, began, before, dt):
        """A boss's entrance as it plays: embers flare and ash streams in while one of ash forms; a
        statue bursts its stone skin part way through tearing free."""
        base, height = self.body_span(e)
        k = e.rise_progress
        if e.type.rise == "ash":
            if began:
                self.game.sfx("rise")
                name = e.type.called
                self.game.message(f"{name} rises from the ashes!")
                self.ash.emit(e.x, base, e.z, e.radius * 1.6, 50, band=0.2, ember_chance=0.7)
            self.ash.gather(e.x, base, e.z, e.radius, height, k, 90, dt)
        elif before < STATUE_BURST <= k:
            self.game.sfx("crack")
            self.ash.emit(e.x, base + height * 0.5, e.z, e.radius, 60, band=height * 0.4, ember_chance=0.15)

    def _shed_ash(self, e, dt):
        base, height = self.body_span(e)
        rate = 70 if e.type.boss else 30
        self.ash.shed(e.x, base, e.z, e.radius, height, e.death_progress, rate, dt)

    def _push_player_out_of_bodies(self):
        player = self.player
        for e in self.enemies:
            if not e.alive or e.state == "ashes":
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
                or self.shot_blocked(pr_.x, pr_.y, pr_.z)
            ):
                pr_.life = 0
                if pr_.effect == "flame" and not pr_.hostile:  # a flame bolt sets a web it strikes alight
                    tx, tz = TileMap.tile_coord(pr_.x), TileMap.tile_coord(pr_.z)
                    for p in self.props:
                        if self._web(p) and p.open_t == 0 and (p.tx, p.tz) == (tx, tz):
                            self._burn_web(p)
            elif pr_.effect == "flare":
                continue
            elif pr_.hostile:
                if shots.strikes(
                    pr_.x, pr_.y, pr_.z, player.x, player.z, shots.PLAYER_RADIUS, shots.player_span(player.y)
                ):
                    self.strike_player(
                        max(rround(foe_harm(pr_.damage) - player.inventory.defense * 0.3), 1),
                        pr_.source or "Something",
                        pr_.x - pr_.dx,
                        pr_.z - pr_.dz,
                        pr_.inflicts,
                    )
                    if pr_.effect == "web":
                        player.webbed_t = WEB_TIME
                        self.game.message("Sticky silk binds your legs!")
                    elif pr_.effect == "ash":
                        player.webbed_t = max(player.webbed_t, GRASP_HOLD)
                        self.game.message("Grave ash clogs your stride!")
                    elif pr_.effect == "lance":
                        player.chill_t = max(player.chill_t, LANCE_CHILL)
                        self.game.message("Moon-frost numbs your legs!")
                    pr_.life = 0
            elif pr_.pierce:
                self._cut_through(pr_)
            else:
                target = next(
                    (
                        e
                        for e in self.enemies
                        if e.alive
                        and not e.unseen
                        and shots.strikes(
                            pr_.x, pr_.y, pr_.z, e.x, e.z, e.radius, shots.body_span(e.type, self.enemy_y(e))
                        )
                    ),
                    None,
                )
                if target:
                    self._shot_lands(pr_, target)
                    pr_.life = 0
        self.projectiles = [p for p in self.projectiles if p.life > 0]

    def _shot_lands(self, pr_, target):
        """One of your shots strikes `target`: its damage, its element's touch and its poison."""
        element = elements.EFFECT_ELEMENT.get(pr_.effect)
        dmg = max(rround(pr_.damage * elements.mult(target.type, element)), 1)
        jolt = elements.staggers(target.type, element)
        self.game.damage_enemy(target, dmg, 99.0 if jolt else 1.0)
        if pr_.effect in ("venom", "thorn") and target.alive:
            target.afflict("poison", *Spells.venom_poison(self.player.stats.magic))
            self.game.sfx("hiss", 0.6)

    def _cut_through(self, pr_):
        """A piercing wave cuts every foe across its breadth that it has not cut yet, and flies on."""
        for e in self.enemies:
            if not e.alive or e.unseen or id(e) in pr_.hit_ids:
                continue
            span = shots.body_span(e.type, self.enemy_y(e))
            if shots.sweeps(pr_.x, pr_.y, pr_.z, pr_.dx, pr_.dz, pr_.width, e.x, e.z, e.radius, span):
                pr_.hit_ids.add(id(e))
                self._shot_lands(pr_, e)

    # --- player actions --------------------------------------------------------

    def melee_targets(self, reach, cone=0.6, limit=None):
        """Living enemies a swing can hit, nearest first. `cone` is the minimum cosine between
        facing and target (below 0 hits all around); `limit` caps how many."""
        player = self.player
        fx, fz = player.forward()
        out = []
        for e in self.enemies:
            if not e.alive or e.unseen:
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
            if not e.alive or e.perched or e.unseen:
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

    def fire_bolt(self, damage, effect="flame", rgb=(255, 160, 60), speed=shots.BOLT_SPEED, yaw_offset=0.0):
        player = self.player
        dx, dy, dz = shots.aim(player.yaw + yaw_offset, player.pitch, speed)
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

        def burn(e):
            flammable = e.type.flammable
            dmg = Spells.pyre_damage(magic, gauge, flammable)
            self.game.damage_enemy(e, max(rround(dmg * elements.mult(e.type, "fire")), 1))
            if flammable and e.alive:
                e.afflict("burn", *Spells.BURN)

        return self.flame_cone(Spells.PYRE_REACH, burn)

    def flame_cone(self, reach, burn, cone=0.5):
        """A gout of fire `reach` metres ahead: `burn(enemy)` for each foe it reaches, then cold
        braziers kindle and webs shrivel in it. Pyre's, and the Ashblade's Ember Spill. Returns how
        many foes it struck."""
        player = self.player
        targets = self.melee_targets(reach, cone=cone)
        for e in targets:
            burn(e)
        self._fire_touches(lambda d, cos: d <= reach + TileMap.TILE / 2 and cos >= 0.4)
        dx, dy, dz = shots.aim(player.yaw, player.pitch, speed=1.0)  # the unit direction you aim
        y0 = player.eye_y - shots.BOLT_DROP
        self.gouts.append(Gout(player.x, y0, player.z, dx, dy, dz, reach))
        rng = random.Random(int(self._time * 1000))
        for i in range(18):  # sparks and embers thrown out of the gout, rising as they cool
            spread = (i / 17 - 0.5) * 0.9 + rng.uniform(-0.1, 0.1)
            ca, sa = math.cos(spread), math.sin(spread)
            sx, sz = dx * ca - dz * sa, dx * sa + dz * ca
            speed = rng.uniform(4.5, 10.0)
            self.projectiles.append(
                Projectile(
                    x=player.x + sx * Gout.START,
                    y=y0 + rng.uniform(-0.15, 0.2),
                    z=player.z + sz * Gout.START,
                    dx=sx * speed,
                    dy=dy * speed + rng.uniform(0.3, 2.0),
                    dz=sz * speed,
                    life=rng.uniform(0.2, 0.5),
                    damage=0,
                    hostile=False,
                    rgb=(255, rng.randint(70, 210), rng.randint(20, 60)),
                    effect="flare",
                )
            )
        return len(targets)

    def _fire_touches(self, reaches):
        """Kindles the cold fires and burns the webs a burst of flame reaches: `reaches(distance,
        cos_from_facing)` says which props it touches."""
        player = self.player
        fx, fz = player.forward()
        for p in list(self.props):
            dx, dz = p.x - player.x, p.z - player.z
            d = math.hypot(dx, dz) or 1e-6
            if not reaches(d, (dx * fx + dz * fz) / d):
                continue
            if p.kind in KINDLING:
                self.kindle(p)
            elif self._web(p) and p.open_t == 0:
                self._burn_web(p)

    def _burn_web(self, p):
        self.flags.add(p.key)
        p.open_t = 0.01
        self.game.message("The web shrivels in the flame.")
        self.game.sfx("eruption", 0.5)

    def volley(self, damage, count, spread, effect, rgb, speed=shots.BOLT_SPEED):
        """`count` shots fanned `spread` radians apart about your aim (Thornlash's Thorn Volley)."""
        for i in range(count):
            self.fire_bolt(damage, effect, rgb, speed, yaw_offset=(i - (count - 1) / 2) * spread)

    def crescent_wave(self, damage, width, speed, life, rgb, effect="crescent"):
        """The Moonless Tachi's Pale Crescent: one wide crescent of pale light loosed along your view.
        It cuts every foe across its `width` that it meets, each once, and flies on through them until
        a wall or its `life` ends it. Returns it."""
        player = self.player
        dx, dy, dz = shots.aim(player.yaw, player.pitch, speed)
        lead = 0.9 / speed  # sets out where the blade's cut ended, a step ahead
        pr_ = Projectile(
            x=player.x + dx * lead,
            y=player.eye_y - shots.BOLT_DROP + dy * lead,
            z=player.z + dz * lead,
            dx=dx,
            dy=dy,
            dz=dz,
            life=life,
            damage=damage,
            hostile=False,
            rgb=rgb,
            effect=effect,
            pierce=True,
            width=width,
        )
        self.projectiles.append(pr_)
        return pr_

    def bodies(self):
        """The foes' bodies a lunge stops short of, as (x, z, radius): the same ones that push you out."""
        return [(e.x, e.z, e.radius) for e in self.enemies if e.alive and e.state != "ashes"]

    def slag_ring(self, damage_for, radius):
        """Slagbreaker's Slag Burst: molten flame bursts out all around you along the floor.
        `damage_for(enemy)` is dealt to every foe within `radius` metres, fire burns them, and the
        cold fires and webs it reaches kindle and shrivel. Returns the foes struck."""
        player = self.player
        targets = self.melee_targets(radius, cone=-1)
        for e in targets:
            self.game.damage_enemy(e, max(rround(damage_for(e)), 1))
            if elements.burns(e.type, "fire") and e.alive:
                e.afflict("burn", *elements.WEAPON_BURN)
        self._fire_touches(lambda d, _cos: d <= radius + TileMap.TILE / 2)
        y0 = player.y + 0.3
        for i in range(SLAG_GOUTS):
            a = player.yaw + i * math.tau / SLAG_GOUTS
            self.gouts.append(Gout(player.x, y0, player.z, math.cos(a), 0.05, math.sin(a), radius))
        return targets

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
            reach = INTERACT_REACH.get(getattr(p, "kind", None), INTERACT_RANGE)
            in_reach = d < reach and (d < 0.8 or (dx * fx + dz * fz) / d > 0.55)
            if in_reach and (best is None or d < best_d):
                best, best_d = p, d
        return best

    def exit_open(self, p):
        """Whether an exit lets you through: one with `requires=<flag>` stays shut until that flag is
        set (the cemetery's gate, until the Sexton falls)."""
        need = p.props.get("requires")
        return not need or need in self.flags

    def _interactable(self, p):
        if p.kind in (
            "npc",
            "save_statue",
            "exit",
            "pickup",
            "remnant",
            "iron_maiden",
            "frog_idol",
            "silent_bell",
        ):
            return True
        if p.kind == "lift_call":  # only from its own landing, not from the floor below or a moving lift
            return p.open_t == 0 and not p.lift.moving and abs(p.y - self.player.y) < CALL_REACH_Y
        if p.kind == "door" and p.props.get("boss"):
            a = self.arena_at_door(p)
            if a and a.sealed:
                return False  # no way out until one of you falls
            if self.fog_gate(p):
                return True
        if p.kind in ("chest", "lever", "door", "altar"):
            return p.open_t == 0
        if p.kind == "house_door":
            return p.open_t == p.goal  # not while it swings
        return p.kind in KINDLING and not self.is_lit(p)  # a cold fire: you can look at its ashes

    def swing_door(self, p):
        """Opens a shut house door, or shuts an open one. It will not shut on someone standing in its
        doorway; you, on its step or just inside with only a shoulder over the threshold, step back
        clear of it as it shuts (the leaf hangs at the arch and a shut door fills its tile, so a body
        left overlapping the tile would be wedged). Returns whether it moved."""
        if p.goal >= 1.0 and (self._doorway_occupied(p) or not self._clear_doorway(p)):
            return False
        p.goal = 0.0 if p.goal >= 1.0 else 1.0
        self.game.sfx("door", 0.5)
        return True

    def _doorway_rect(self, p):
        x0, z0 = p.tx * TileMap.TILE, p.tz * TileMap.TILE
        return x0, z0, x0 + TileMap.TILE, z0 + TileMap.TILE

    def _doorway_occupied(self, p):
        """Whether anyone stands in the doorway: you with your feet on its floor (its tile, or the
        margin of a thin jamb it lends, where the open leaf rests), or a villager or a foe anywhere
        over it (they don't step aside)."""
        x0, z0, x1, z1 = self._doorway_rect(p)
        player = self.player
        if x0 <= player.x <= x1 and z0 <= player.z <= z1:
            return True
        tx, tz = TileMap.tile_coord(player.x), TileMap.tile_coord(player.z)
        lay = self.map.layout(tx, tz)
        if lay is not None and lay.owner_at(player.x - tx * TileMap.TILE, player.z - tz * TileMap.TILE) == (
            p.tx,
            p.tz,
        ):
            return True
        pad = 0.4  # a body's girth: a shoulder in the doorway counts
        bodies = [(q.x, q.z) for q in self.props if q.kind == "npc"]
        bodies += [(e.x, e.z) for e in self.enemies if e.alive]
        return any(x0 - pad < x < x1 + pad and z0 - pad < z < z1 + pad for x, z in bodies)

    def _clear_doorway(self, p):
        """Steps you back out of the doorway if your body would still overlap the shut door (your feet
        already outside it). Returns False if a wall behind you won't let you clear it."""
        player = self.player
        r = player.RADIUS

        def shut(tx, tz):
            return (tx, tz) == (p.tx, p.tz) or self.blocked_tile(tx, tz)

        def wedged(x, z):
            home = (TileMap.tile_coord(x), TileMap.tile_coord(z))
            return not collision.circle_clear(self.map, x, z, r, self.map.floor_at(x, z), shut, home)

        if not wedged(player.x, player.z):
            return True
        x0, z0, x1, z1 = self._doorway_rect(p)
        pushes = []
        if player.x < x0:
            pushes.append((x0 - r - player.x, 0.0))
        elif player.x > x1:
            pushes.append((x1 + r - player.x, 0.0))
        if player.z < z0:
            pushes.append((0.0, z0 - r - player.z))
        elif player.z > z1:
            pushes.append((0.0, z1 + r - player.z))
        for dx, dz in sorted(pushes, key=lambda d: abs(d[0]) + abs(d[1])):
            nx, nz = collision.move(self.map, player.x, player.z, dx * 1.01, dz * 1.01, r, self.blocked_tile)
            if not wedged(nx, nz):
                player.x, player.z = nx, nz
                return True
        return False

    def open_prop(self, p):
        p.open_t = 0.01
        self.flags.add(p.key)

    def drop_sigil(self, x, z):
        self.drop_pickup(x, z, "ember_sigil", "sigil")

    def drop_relic(self, item_id, x, z):
        """Leaves a boss relic on the floor as a pickup."""
        self.drop_pickup(x, z, item_id, relics.get(item_id).key)

    def lay_remnant(self):
        """Lays the heap of ashes holding the gold you dropped when you died, if it lies on this map."""
        self.props = [p for p in self.props if p.kind != "remnant"]
        spot = remnant.lies_on(self.player, self.name)
        if spot is None:
            return
        x, z = spot
        tx, tz = TileMap.tile_coord(x), TileMap.tile_coord(z)
        self.props.append(
            Prop(kind="remnant", x=x, z=z, y=self.map.floor_at(x, z), tx=tx, tz=tz, props={}, key=None, yaw=0)
        )

    def death_spot(self):
        """Where the gold you drop on dying comes to rest: where you fell, unless that was down a
        chasm, in the water, in lava or a pit; then the last solid ground you stood on."""
        player = self.player
        tile = self.map.tile_at(player.x, player.z)
        if not (self.terrain.plunging or tile.hazardous or tile.lava or not tile.walkable):
            return player.x, player.z
        return self.terrain.safe or self._safe or (player.x, player.z)

    def _open_rate(self, p):
        if self._web(p):
            return WEB_BURN_RATE
        return SECRET_FALL_RATE if p.kind == "secret_wall" else OPEN_RATE

    def _update_remnant(self):
        """Walking over your heap of ashes gathers it up."""
        player = self.player
        for p in self.props:
            if p.kind == "remnant" and player.alive:
                if remnant.within_reach(player.x, player.y, player.z, p.x, p.y, p.z):
                    self.game.gather_remnant()
                return

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
        for bridge in self.terrain.platforms:
            if bridge.lever and bridge.lever == p.props.get("id"):
                bridge.locked = False
                self.game.sfx("chain", 0.8)

    # --- rendering ---------------------------------------------------------------

    def _dress_ramparts(self):
        """Carved bays along the great walls (`world/ramparts.py`), kept clear of gates and of anything
        already hung on the wall."""
        clear = set()
        for e in self.map.entities:
            if e.kind in WALL_PROPS:
                clear.add((e.tx, e.tz))
            elif e.kind in RAMPART_GATES:
                clear.update((e.tx + i, e.tz + j) for i in (-1, 0, 1) for j in (-1, 0, 1))
        for bay in ramparts.bays(self.map, frozenset(clear)):
            self.props.append(
                Prop(
                    kind="rampart_bay",
                    x=bay.x,
                    z=bay.z,
                    y=bay.y,
                    tx=bay.tx,
                    tz=bay.tz,
                    props={"kind": bay.kind, "height": f"{bay.height:g}"},
                    key=None,
                    yaw=bay.yaw,
                )
            )

    def _unload_glitter(self):
        if self._glitter is not None:
            self.game.gpu.unload_mesh(self._glitter[1])
            self._glitter = None

    def glitter_batch(self, dark=0.0, veil=False):
        """The sun's path of glints on the open sea as an uploadable batch, for where you stand now;
        None without an open sea or a sun over it."""
        spec = sky.get(self.meta)
        if self._sea is None or spec is None or not spec.sun:
            return None
        z_from = min(tz for _tx, tz, _ in sea.deep_tiles(self.map)) * TileMap.TILE
        frame = int(self._time / sea.GLITTER_FRAME)
        built = sea.glitter(
            rround(self.player.x), rround(self.player.z), z_from, sea.level(self.map), spec.sun_at, frame
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
        if self._sea is None:
            return
        gpu.set_vec2("fogRange", sea.fog_range(fog_range))
        gpu.draw_world_batch(self._sea, "water")
        key = (
            rround(self.player.x),
            rround(self.player.z),
            int(self._time / sea.GLITTER_FRAME),
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
        player = self.player
        for mesh, tex in self._meshes:
            gpu.draw_world_batch(mesh, tex)
        self._draw_sea(gpu, fog_range, dark, veil)
        gpu.set_float("isModel", 1.0)
        sight = self.meta.get("fog_range", [0, 40])[1] + 2
        # Small models stop being drawn sooner than the fog's end on a map that sees far (the
        # fortress from its bridge); landmarks are drawn as far as the eye can see.
        far = min(float(self.meta.get("model_range", sight)), sight)
        if "indoor_range" in self.meta and self.map.tile_at(player.x, player.z).ceil is not None:
            far = min(far, float(self.meta["indoor_range"]))  # under a roof the far rooms are walled off
        fx, fz = player.forward()
        self._draw_baked(gpu, sight, far, fx, fz)
        gpu.set_float("isModel", 1.0)
        for p in self.props:
            if p.kind in STATIC_PROPS and self._baked:
                continue
            if math.hypot(p.x - player.x, p.z - player.z) > (sight if p.kind in LANDMARKS else far):
                continue
            if p.kind not in LANDMARKS and behind_view(p.x - player.x, p.z - player.z, fx, fz):
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
                    models.lift(rig, self._time, pl.moving, chain_h, pl.model, pl.doors, pl.plate_sink)
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
            for c in pl.calls:
                with rig.entity(c.x, c.floor, c.z, math.atan2(c.z - pl.z, c.x - pl.x)):
                    models.call_plate(rig, c.sink, wood=self.name in WOODEN_LEVER_MAPS)
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
            self._model_light(gpu, e.x, y + 1.0, e.z, flash=e.flashing, tint=STATUS_TINT.get(e.afflicted))
            forming = e.unseen and e.type.rise == "ash"
            if forming:  # the heap it waits in, sinking as it rises out of it
                with rig.at(e.x, y, e.z):
                    cemetery_models.ash_heap(rig, self._time, e.rise_progress, max(e.radius, 0.8) * 1.2)
                if e.state == "ashes":
                    continue
            dying = not e.alive or forming
            if dying:
                ashen, dissolve = rise_phases(e.rise_progress) if forming else death_phases(e.death_progress)
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
                if f.style == "hands":
                    cemetery_models.ash_hands(rig, f.glow, f.flame, self._time + f.x)
                elif f.style == "drowned":
                    sewer_models.drowned_hands(rig, f.glow, f.flame, self._time + f.x)
                elif f.style == "moon":
                    moon_models.moonbeam(rig, f.glow, f.flame, self._time + f.x)
                else:
                    models.eruption(rig, f.glow, f.flame, self._time)
            bomb = f.bomb()
            if bomb:
                gpu.model_light((1.6, 1.4, 1.2))
                with rig.at(*bomb):
                    forge_models.magma_bomb(rig, self._time)
        for w in self.shockwaves:
            if w.style in ("ash", "squeal", "blink"):  # lit by the room rather than glowing
                self._model_light(gpu, w.x, w.floor + 1.0, w.z)
            else:
                gpu.model_light((1.6, 1.4, 1.2))
            with rig.at(w.x, w.floor, w.z):
                if w.style == "ash":
                    cemetery_models.ash_billow(rig, w.progress, w.radius, self._time)
                elif w.style == "squeal":
                    sewer_models.squeal_ring(rig, w.progress, w.radius)
                elif w.style == "blink":
                    moon_models.blink_mist(rig, w.progress, w.radius)
                else:
                    models.shockwave_ring(rig, w.progress, w.radius)
        for d in self.devils:
            self._model_light(gpu, d.x, d.floor + 1.0, d.z)
            with rig.at(d.x, d.floor, d.z):
                cemetery_models.dust_devil(rig, d.strength, self._time + d.x)
        self._draw_ash(rig, gpu, far)
        for g in self.gouts:
            if g.style == "ash":
                self._model_light(gpu, g.x, g.y, g.z)
            else:
                gpu.model_light((1.6, 1.4, 1.2))
            for i, (x, y, z, size, heat) in enumerate(g.puffs()):
                with rig.at(x, y, z):
                    if g.style == "ash":
                        cemetery_models.dust_puff(rig, size, heat, self._time, seed=i * 1.7)
                    else:
                        models.gout_puff(rig, size, heat, self._time, seed=i * 1.7)
        for pr_ in self.projectiles:
            gpu.model_light((1.6, 1.4, 1.2))
            if pr_.effect in ("arrow", "thunder", "thorn", "mote", "rat", "lance", "crescent"):  # point first
                heading = -math.atan2(pr_.dz, pr_.dx)
                climb = math.atan2(pr_.dy, math.hypot(pr_.dx, pr_.dz))
                with rig.at(pr_.x, pr_.y, pr_.z, ry=heading, rz=climb):
                    if pr_.effect == "arrow":
                        forge_models.arrow(rig, pr_.rgb)
                    elif pr_.effect == "thorn":
                        models.thorn_shot(rig, pr_.rgb, self._time)
                    elif pr_.effect == "mote":
                        forge_models.mote(rig, self._time + id(pr_) % 7)
                    elif pr_.effect == "rat":
                        sewer_models.swarm_rat(rig, self._time + id(pr_) % 5)
                    elif pr_.effect == "lance":
                        moon_models.frost_lance(rig, pr_.rgb, self._time + id(pr_) % 3)
                    elif pr_.effect == "crescent":
                        moon_models.crescent_wave(rig, pr_.rgb, pr_.width, pr_.life, self._time)
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
                elif pr_.effect == "ash":
                    cemetery_models.ash_clod(rig, self._time)
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

    def _draw_baked(self, gpu, sight, far, fx, fz):
        """The baked static props, chunk by chunk, culled like single props by range and heading."""
        player = self.player
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
        light = HIT_RED if flash else [min(c, 1.6) for c in self.builder.model_light_at(x, y, z)]
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
            models.banner(rig, t + p.tz, p.tx * 3 + p.tz, burnt="burnt" in p.props)
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
            models.chest(rig, p.open_t > 0, p.props.get("model", "wood"))
        elif k == "door" and p.props.get("boss"):
            a = self.arena_at_door(p)
            if a and a.fogged(self.flags):
                tile = self.map[p.tx, p.tz]
                height = models.BOSS_DOOR_TOP
                if tile.ceil is not None:
                    height = min(height, tile.ceil - tile.floor)
                models.fog_gate(rig, t, p.axis, a.sealed, height)
            else:
                lit = not (a and a.cleared(self.flags))
                models.boss_door(rig, p.open_t, p.axis, t, lit=lit, boss=p.props.get("boss"))
        elif k == "door":
            tile = self.map[p.tx, p.tz]
            frame = (tile.ceil - tile.floor) if tile.ceil is not None else DOOR_FRAME_SKY
            models.door(rig, p.open_t, p.axis, style=p.props.get("model", "wood"), frame=frame)
        elif k == "gate":
            models.door(rig, p.open_t, p.axis, tex="iron_bars")
        elif k == "lever":
            models.lever(rig, p.open_t, p.wall, wood=p.props.get("model") == "wood")
        elif k == "lift_call":
            models.lift_call(
                rig, math.sin(math.pi * p.open_t), wood=p.props.get("model") == "wood", post="post" in p.props
            )
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
        elif k == "tree":  # `kind=cypress|pine|olive`, or one picked by the tile
            seed = p.tx * 7 + p.tz
            kind = p.props.get("kind", town_models.TREE_KINDS[seed % len(town_models.TREE_KINDS)])
            near = self._baking or math.hypot(p.x - self.player.x, p.z - self.player.z) < DETAIL_RANGE
            town_models.town_tree(rig, kind, seed, t, near)
        elif k == "jungle_tree":
            models.jungle_tree(rig, p.tx * 7 + p.tz, t)
        elif k == "fungus":
            models.fungus(rig, p.tx * 5 + p.tz, t)
        elif k == "pickup":
            models.pickup(rig, t, p.props.get("item"))
        elif k == "remnant":
            cemetery_models.remnant(rig, t)
        elif k == "npc":
            npc_id = p.props.get("id")
            if npc_id == "enthroned":
                models.enthroned(rig, t)
            else:
                near = self._baking or math.hypot(p.x - self.player.x, p.z - self.player.z) < DETAIL_RANGE
                models.npc(rig, villagers.look(npc_id), t + p.tx, near)
        elif k == "barrel":
            models.barrel(rig, p.tx * 7 + p.tz, broken=p.open_t > 0)
        elif k == "secret_wall":
            tile = self.map[p.tx, p.tz]
            top = float(p.props["top"]) if "top" in p.props else tile.ceil or tile.floor + 4.0
            if p.props.get("model") == "web":
                models.burning_web(rig, top - tile.floor, p.open_t, t)
            else:
                tex = (
                    "vine_wall" if p.props.get("model") == "vines" else secret_wall_tex(self.map, p.tx, p.tz)
                )
                near = math.hypot(p.x - self.player.x, p.z - self.player.z) < SHIMMER_NEAR
                models.secret_wall(rig, top - tile.floor, p.open_t, tex=tex, t=t, shimmer=True, near=near)
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
                cemetery_models.cemetery_gate(rig, 1.0 if self.exit_open(p) else 0.0)
            elif p.props.get("model") == "sewer_grate":
                sewer_models.sewer_grate(rig, t)
            elif p.props.get("model") == "vesper_gate":  # it stands open once the three sigils are taken
                moon_models.vesper_gate(rig, 1.0 if self.exit_open(p) else 0.0, t)
            elif p.props.get("model") == "sewer_ladder":  # set back against the wall behind it, if any
                behind = self.map[p.tx - rround(math.cos(p.yaw)), p.tz - rround(math.sin(p.yaw))]
                sewer_models.sewer_ladder(rig, t, self._ceil_h(p), LADDER_BACK if behind.solid else 0.0)
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
            top = float(p.props.get("top", "18"))
            forge_models.lavafall(rig, t, top, p.tx)
            if p.props.get("spout") == "gargoyle":  # a stone head on the wall face, spewing it
                with rig.at(0, top - 1.75, 0):
                    fortress_props.lava_spout(rig, t, p.tx)
        elif k == "battlement":
            fortress_props.battlement(rig, t, p.tx * 5 + p.tz, float(p.props.get("span", "8")))
        elif k == "gargoyle_statue":
            near = self._baking or math.hypot(p.x - self.player.x, p.z - self.player.z) < DETAIL_RANGE
            fortress_props.gargoyle_statue(rig, t, p.tx * 7 + p.tz * 3, p.props.get("pose", "hunched"), near)
        elif k == "great_window":  # set high in a great wall's face, over the moat it stands in
            with rig.at(0, float(p.props.get("rise", "0")), 0):
                fortress_props.great_window(rig, t, p.tx * 7 + p.tz * 3)
        elif k == "barred_window":
            fortress_props.barred_window(rig, t, p.tx * 7 + p.tz * 3)
        elif k == "forge_hearth":
            fortress_props.forge_hearth(rig, t, p.tx * 7 + p.tz * 3)
        elif k == "quench_trough":
            fortress_props.quench_trough(rig, t + p.tx)
        elif k == "crucible":
            fortress_props.crucible(rig, t + p.tx)
        elif k == "tool_rack":
            fortress_props.tool_rack(rig, t, p.tx * 7 + p.tz * 3)
        elif k == "ingot_pile":
            fortress_props.ingot_pile(rig, p.tx * 7 + p.tz * 3)
        elif k == "slag_heap":
            fortress_props.slag_heap(rig, p.tx * 7 + p.tz * 3)
        elif k == "impaler":
            fortress_props.impaler(rig, t, p.tx * 7 + p.tz * 3)
        elif k == "forge_statue":
            fortress_props.forge_statue(rig, p.tx * 7 + p.tz * 3)
        elif k == "ore_cart":
            fortress_props.ore_cart(rig, p.tx * 7 + p.tz * 3)
        elif k == "anvil":
            forge_models.anvil(rig, t + p.tx)
        elif k == "chimney":
            forge_models.chimney(rig, t + p.tx, float(p.props.get("height", "2.6")))
        elif k in TOWN_PROPS:
            self._draw_town_prop(rig, p, k, t)
        elif k == "embers":
            forge_models.embers_rain(rig, t, p.tx * 3 + p.tz)
        elif k == "gravestone":
            cemetery_models.gravestone(rig, p.tx * 7 + p.tz * 3)
        elif k == "open_grave":
            cemetery_models.open_grave(rig, p.tx * 3 + p.tz)
        elif k == "cemetery_gate":
            cemetery_models.cemetery_gate(rig, sentinels=p.props.get("sentinels") != "false")
        elif k == "mourning_statue":
            cemetery_models.mourning_statue(rig, p.tx * 7 + p.tz * 3)
        elif k == "crypt_front":
            cemetery_models.crypt_front(rig, p.tx * 7 + p.tz * 3)
        elif k == "grave_railing":
            cemetery_models.grave_railing(rig, p.tx * 7 + p.tz * 3)
        elif k == "ash_mound":
            cemetery_models.ash_mound(rig, p.tx * 7 + p.tz * 3)
        elif k == "drain_pipe":
            sewer_models.drain_pipe(rig, t + p.tx, p.tx * 7 + p.tz * 3)
        elif k == "sluice_wheel":
            sewer_models.sluice_wheel(rig, p.tx * 7 + p.tz * 3)
        elif k == "outfall_grate":
            sewer_models.outfall_grate(rig, p.tx * 7 + p.tz * 3)
        elif k == "rat_nest":
            sewer_models.rat_nest(rig, p.tx * 7 + p.tz * 3)
        elif k == "inkcaps":
            sewer_models.inkcaps(rig, p.tx * 7 + p.tz * 3)
        elif k == "sump_caps":
            sewer_models.sump_caps(rig, p.tx * 7 + p.tz * 3)
        elif k == "moon_lamp":
            moon_models.moon_lamp(rig, p.tx * 7 + p.tz * 3)
        elif k == "veiled_statue":
            moon_models.veiled_statue(rig, p.tx * 7 + p.tz * 3)
        elif k == "silver_tree":
            moon_models.silver_tree(rig, p.tx * 7 + p.tz * 3)
        elif k == "moon_window":  # `rise=` hangs it up its wall, `size=` scales it about the wall's face
            size = float(p.props.get("size", "1"))
            with (
                rig.at(-0.95, float(p.props.get("rise", "0")), 0),
                rig.at(0, 0, 0, s=size),
                rig.at(0.95, 0, 0),
            ):
                moon_models.moon_window(rig, p.tx * 7 + p.tz * 3)
        elif k == "moon_spire":
            moon_models.moon_spire(rig, p.tx * 7 + p.tz * 3, float(p.props.get("height", "14")))

    def _draw_town_prop(self, rig, p, k, t):
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
        elif k in ("rose_window", "crest_plaque", "shutters", "balcony"):  # `rise=` sets it up the wall
            with rig.at(0, float(p.props.get("rise", RISE[k])), 0):
                if k == "rose_window":
                    town_models.rose_window(rig, seed)
                elif k == "crest_plaque":
                    town_models.crest_plaque(rig, seed)
                elif k == "shutters":  # an oak frame in a half-timbered wall, dressed stone in any other
                    wall = self.map.wall_behind(p.tx, p.tz, p.yaw)
                    town_models.shutters(rig, seed, timber=wall is not None and wall.wall_tex == "timber")
                else:
                    town_models.balcony(rig, seed)
        elif k == "door_arch":
            town_models.door_arch(
                rig,
                seed,
                float(p.props.get("height", "3.2")),
                float(p.props.get("spring", "2.2")),
                "rose" in p.props,
                leaf=not hinged(p.props),  # a house's own door is drawn apart, as it swings
            )
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
        elif k == "fence":
            town_models.fence(rig, seed)
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


def hinged(props):
    """Whether a `door_arch` hangs a door that opens and shuts (a house's): every one but the
    cathedral's (`rose`) and one left standing `open`."""
    return "rose" not in props and "open" not in props


def maiden_door(t):
    """0..1 door opening for the iron maiden `t` seconds into its cycle: open, hold, shut."""
    if t <= 0:
        return 0.0
    if t < 0.6:
        return t / 0.6
    if t < MAIDEN_CYCLE - 0.6:
        return 1.0
    return max((MAIDEN_CYCLE - t) / 0.6, 0.0)
