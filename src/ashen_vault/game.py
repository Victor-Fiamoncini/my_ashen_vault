import math
import random

import pyray as pr
import raylib as rl
from raylib import ffi

from ashen_vault import dialogue as dialogue_data
from ashen_vault import map_path
from ashen_vault.ai.enemy import Enemy
from ashen_vault.audio.synth import Audio
from ashen_vault.input import CONTROLS, Input
from ashen_vault.player import ailments, burden, durability, remnant, stash, view_blend, weapons
from ashen_vault.player.combat import Combat
from ashen_vault.player.inventory import LEFT, PRIMARY, RIGHT, SECONDARY, SLOT_ALIASES, SLOT_NAMES, SPELL
from ashen_vault.player.items import Item, Items
from ashen_vault.player.player import Player
from ashen_vault.player.spells import Spells
from ashen_vault.render import models
from ashen_vault.render.gpu import Gpu
from ashen_vault.render.rig import Rig
from ashen_vault.render.sky import SkyPass
from ashen_vault.render.world_view import WorldView
from ashen_vault.save import slots
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.save.settings import Settings
from ashen_vault.screen import (
    COLUMN_H,
    EQUIPPED_H,
    EQUIPPED_PANEL,
    FOV,
    ITEM_PANEL,
    LIST_ROWS,
    MENU_LIST,
    PREVIEW,
    ROW_H,
    ROW_TOP,
    SHOP_LIST,
    STASH_LIST,
    STATS_H,
    STATS_PANEL,
    STATS_ROW,
    STORE_LIST,
    H,
    W,
    centered_row_at,
    list_row_at,
    scroll_into_view,
)
from ashen_vault.ui import belongings, compare, smallfont
from ashen_vault.ui import hud as ui
from ashen_vault.ui.tally import GoldTally
from ashen_vault.util import clamp, rround
from ashen_vault.world import darkness, doors, elements, footsteps, loot, relics, shots
from ashen_vault.world.map_loader import map_title
from ashen_vault.world.rest import RestSequence
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import HOME_MAP, World, beside_shrine, home_spot

HIT_PITCH = (0.92, 1.08)  # each blow's sound is pitched at random within this, so no two ring alike
KIND_ORDER = ["service", "weapon", "shield", "armor", "spell", "consumable", "repair", "scroll", "key"]
HAND_BUTTON = {RIGHT: "attack", LEFT: "cast"}  # input actions: left mouse = Primary, right = Secondary
PAUSE_OPTIONS = ["Resume", "Options", "Controls", "Return to Title", "Quit"]
# (x, y, width) of each ui.list_menu panel, shared by drawing and mouse hit-testing.
PAUSE_LIST = (100, 80, 120)
OPTIONS_LIST = (90, 80, 140)
CONTROLS_LIST = (20, 6, 280)
# Controls rows that fit: the panel (title, rows, footer) ends a margin above the screen's bottom.
CONTROLS_ROWS = (H - 2 * CONTROLS_LIST[1] - ROW_TOP - 14) // ROW_H
PICK_LIST = (24, 60, 190)  # the "which slot?" chooser over Belongings
SLOTS_LIST = (40, 108, 240)  # the title's save slot chooser
CONFIRM_LIST = (90, 120, 140)  # "Overwrite Slot N?" over it
SHRINE_LIST = (110, 84, 100)  # what to do at a shrine
SHRINE_OPTIONS = ["Rest", "Storage", "Leave"]
STORE_SIDES = ("carried", "stored")
# Brannoc's first row: not an item for sale but his mending (scene "repair").
MEND_ROW = Item(
    id="mend_gear",
    name="Mend gear",
    kind="service",
    desc="Worn steel ground true, split straps restitched, dented plate beaten back. Paid by the piece.",
)
CONFIRM_OPTIONS = ["No", "Yes"]
# Scenes that count toward a save's play time: the title, pause and its submenus, and the ending don't.
PLAYED_SCENES = ("play", "dialogue", "menu", "shop", "repair", "rest", "shrine", "storage", "dead")
TITLE_Y, TITLE_STEP = 140, 14
TITLE_ORBIT = (25, 24)  # the title camera circles Harrowmere's Silent Bell (its tile)
# Comparing gear: a better stat green, a worse one red (keyed by compare.better).
COMPARE_COLORS = {1: ui.color(120, 210, 110), -1: ui.color(225, 95, 80), 0: ui.TEXT}
ENDING = [
    "The bell of Harrowmere rings again.",
    "Its note rolls down the grates into the drowned halls,",
    "through the roots of the green hollow and the forges,",
    "and over Vesperholm, where at last the moon goes down.",
    "On the hill, the stone king stirs upon his throne.",
    "",
    "Thank you for playing the Ashen Vault demo.",
]


STORY_MAP = "ashen_cemetery"  # where a new game begins


def _camera(pos, target, fovy):
    return pr.Camera3D(pos, target, (0, 1, 0), fovy, pr.CAMERA_PERSPECTIVE)


# What the prison's altar says as you lift the Warden's Key; an `altar said="...|..."` says its own.
WARDEN_ALTAR_SAID = "The statue's eyes gutter out as you lift the key.|Somewhere above, a great door awaits."


class Game:
    W = W
    H = H

    def __init__(self, opts=None):
        self.opts = opts or {}
        pr.set_trace_log_level(pr.LOG_WARNING)
        pr.set_config_flags(pr.FLAG_WINDOW_RESIZABLE | pr.FLAG_VSYNC_HINT)
        pr.init_window(W * 3, H * 3, "Ashen Vault")
        pr.set_target_fps(60)
        pr.set_exit_key(pr.KEY_NULL)
        self._target = pr.load_render_texture(W, H)
        pr.set_texture_filter(self._target.texture, pr.TEXTURE_FILTER_POINT)
        self._preview = pr.load_render_texture(PREVIEW, PREVIEW)
        pr.set_texture_filter(self._preview.texture, pr.TEXTURE_FILTER_POINT)
        self.gpu = Gpu()
        self._rig = Rig(self.gpu)
        self._sky = SkyPass(self.gpu)
        self._audio = Audio()
        self._input = Input(self.opts.get("script"))
        self._saves = SaveSystem()
        self.settings = Settings.beside(self._saves.base)  # shared by every slot
        self._audio.set_volume(self.settings.gain)
        self._camera = _camera((0, 0, 0), (1, 0, 0), FOV)
        self._view_camera = _camera((0, 0, 0), (1, 0, 0), 55)
        self._view_blends = view_blend.ViewBlends()  # the arms' poses, carried from frame to frame
        self._preview_camera = _camera((2.6, 0.5, 0), (0, 0, 0), 40)
        self.messages = []
        self.area_title = None  # [name, seconds shown]: the card over the screen as you enter an area
        self.flags = set()
        self.player = Player()
        self.gold_tally = GoldTally(self.player.inventory.gold)
        self._tally_inv = self.player.inventory
        self.world = None
        self.scene = None
        self._menu_index = 0
        self._menu_tab = belongings.TABS[0]  # the Belongings tab shown; kept between visits
        self._tab_rows = {}  # Belongings: the row last highlighted on each tab
        self._time = 0.0
        self._frames = 0
        self._running = True
        self._mouse_captured = None
        self._cursor_at = None  # where the free cursor was when mouse look was last released
        self._look_skip = 0  # frames of mouse delta to ignore after recapturing the cursor
        self._rest = None
        self._rest_home = False  # the ember fog is Hearth Ash's, carrying you home, not a shrine's
        self._hit_done = False
        self._held = {"attack": False, "cast": False}  # hand buttons held last frame (tap / hold)
        self._pulse = None  # [seconds left, attack, weapon] of a pending second shockwave
        self._menu_top = 0  # first row shown by a scrolling list
        self._pick = None  # item waiting for a hand in the Belongings chooser
        self._pick_index = 0
        self._shop_id = "pell"
        self._store_side = STORE_SIDES[0]  # the shrine store's focused list
        self._store_at = dict.fromkeys(STORE_SIDES, 0)  # its highlighted row on each side
        self._store_top = dict.fromkeys(STORE_SIDES, 0)  # and the first row shown
        self._step_phase = 0.0
        self._dialogue = None
        self._controls_from = None  # the scene Controls or Options returns to
        self._slots_for = "new"  # what the slot chooser picks a slot for: "new" or "load"
        self._slot_rows = []  # what the slot chooser shows: a SlotSummary (or None) per slot
        self._overwrite = None  # the used slot New Game would overwrite, while it asks
        self._back_index = 0  # the menu row selected when it opened
        self._scroll_hold = 0  # frames Up / Down has been held on the Controls screen
        self._dead_t = 0.0
        self._remnant_news = []  # what became of your gold, told when you wake
        self._ending_t = 0.0
        self._dark_k = None  # how dark it looks where you stand (eased, so cave mouths don't pop)
        # Each scene's update, and whether it takes the frame's dt.
        self._scene_updates = {
            "title": (self._update_title, False),
            "slots": (self._update_slots, False),
            "play": (self._update_play, True),
            "dialogue": (self._update_dialogue, False),
            "menu": (self._update_menu, True),
            "shop": (self._update_shop, False),
            "repair": (self._update_repair, False),
            "shrine": (self._update_shrine, False),
            "storage": (self._update_storage, False),
            "pause": (self._update_pause, False),
            "rest": (self._update_rest, True),
            "controls": (self._update_controls, False),
            "options": (self._update_options, False),
            "dead": (self._update_dead, True),
            "ending": (self._update_ending, False),
        }
        if self.opts.get("map"):
            self.new_game(self.opts["map"], at=self.opts.get("at"))
        else:
            self.show_title()

    def world_view(self, world):
        """The GPU side of a World (`World.view`): its meshes, baked props and drawing."""
        return WorldView(world, self.gpu)

    # --- main loop ----------------------------------------------------------

    def run(self):
        try:
            while self._running and not pr.window_should_close():
                dt = min(pr.get_frame_time(), 0.05)
                if self.opts.get("smoke"):
                    dt = 1.0 / 60
                self._time += dt
                self._frames += 1
                self._input.update(dt)
                self.update(dt)
                self.render()
                self._smoke_check()
        finally:
            self.shutdown()

    def shutdown(self):
        if self.world:
            self.world.unload()
        self._audio.close()
        pr.unload_render_texture(self._preview)
        pr.unload_render_texture(self._target)
        pr.close_window()

    def _smoke_check(self):
        smoke = self.opts.get("smoke")
        if not smoke or self._frames < smoke:
            return
        shot = self.opts.get("shot") or "screenshot.png"
        image = rl.LoadImageFromTexture(self._target.texture)
        rl.ImageFlipVertical(ffi.addressof(image))
        rl.ImageResizeNN(ffi.addressof(image), W * 3, H * 3)
        rl.ExportImage(image, shot.encode())
        rl.UnloadImage(image)
        p = self.player
        inv = p.inventory
        enemies = (
            ",".join(
                f"{e.type.id}:{e.state}:{e.hp}{':landed' if e.landed else ''}" for e in self.world.enemies
            )
            if self.world
            else ""
        )
        print(
            f"smoke: {self._frames} frames, fps={pr.get_fps()}, map={self.world.name if self.world else None}, "
            f"pos={round(p.x, 2)},{round(p.z, 2)} y={round(p.y, 2)} hp={p.stats.hp} lv={p.stats.level} exp={p.stats.exp} "
            f"gold={inv.gold} scene={self.scene} flags={','.join(sorted(self.flags))} items={inv.counts} "
            f"equip={inv.slots} st={round(p.stamina.value, 2)} attack={p.attack.name} "
            f"enemies={enemies} shot={shot}",
            flush=True,
        )
        self._running = False

    def update(self, dt):
        for m in self.messages:
            m[1] += dt
        self.messages = [m for m in self.messages if m[1] <= 5]
        if self.area_title:
            self.area_title[1] += dt
            if self.area_title[1] > ui.AREA_TITLE_TIME:
                self.area_title = None
        inv = self.player.inventory
        if inv is not self._tally_inv:  # a new game or a loaded save: the counter starts settled
            self._tally_inv = inv
            self.gold_tally = GoldTally(inv.gold)
        self.gold_tally.update(inv.gold, dt)
        if self.world:
            target = self.world.dark_here()
            self._dark_k = target if self._dark_k is None else darkness.ease_toward(self._dark_k, target, dt)
        handler = self._scene_updates.get(self.scene)
        if handler:
            update, wants_dt = handler
            if wants_dt:
                update(dt)
            else:
                update()
        self._announce_wear()
        if self.scene in PLAYED_SCENES:
            self.player.play_time += dt

    def _mouse_look(self, on):
        if self.opts.get("smoke") or on == self._mouse_captured:
            return
        self._mouse_captured = on
        if on:
            pr.disable_cursor()
            if self._cursor_at is not None:
                pr.set_mouse_position(*self._cursor_at)
            # The first deltas after a recapture carry the cursor's travel while it was free
            # (pause, belongings, shop); dropping them keeps the view exactly where it was.
            self._look_skip = 2
        else:
            pos = pr.get_mouse_position()
            pr.enable_cursor()
            self._cursor_at = (int(pos.x), int(pos.y))

    # --- scenes: title / new game / travel ----------------------------------

    def show_title(self):
        self.scene = "title"
        self._menu_index = 0
        self.flags = set()
        self.player = Player()
        self._load_world("harrowmere")
        self._mouse_look(False)

    def _title_options(self):
        if any(s.exists() for s in self._saves.all_slots()):
            return ["Continue", "New Game", "Load Game", "Options", "Controls", "Quit"]
        return ["New Game", "Options", "Controls", "Quit"]

    def _update_title(self):
        opts = self._title_options()
        self._menu_nav(len(opts))
        clicked = self._menu_pointer(
            lambda px, py: centered_row_at(W // 2, TITLE_Y, TITLE_STEP, len(opts), 50, px, py)
        )
        if not (clicked or self._input.pressed("confirm")):
            return
        choice = opts[self._menu_index]
        if choice == "Continue":
            self._continue_latest()
        elif choice == "New Game":
            self._open_slots("new")
        elif choice == "Load Game":
            self._open_slots("load")
        elif choice == "Options":
            self._open_options()
        elif choice == "Controls":
            self._open_controls()
        elif choice == "Quit":
            self._running = False

    # --- save slots ------------------------------------------------------------

    def _use_slot(self, n):
        self._saves = self._saves.in_slot(n)

    def _continue_latest(self):
        """Continue: the slot saved most recently."""
        n = slots.latest(s.summary() for s in self._saves.all_slots())
        if n is None:
            return self.message("The save file could not be read.")
        self._use_slot(n)
        self.continue_game()

    def _open_slots(self, purpose):
        """The slot chooser: New Game picks a slot to begin in (asking before it overwrites one), Load
        Game a used slot to wake in."""
        self._slots_for = purpose
        self._slot_rows = [s.summary() for s in self._saves.all_slots()]
        self._back_index = self._menu_index
        self._overwrite = None
        rows = self._slot_rows
        if purpose == "new":  # the first empty slot, else the first
            self._menu_index = next((i for i, r in enumerate(rows) if r is None), 0)
        else:  # the slot saved most recently
            self._menu_index = (slots.latest(rows) or 1) - 1
        self.scene = "slots"

    def _update_slots(self):
        if self._overwrite is not None:
            return self._update_overwrite()
        if self._back():
            self.scene = "title"
            self._menu_index = self._back_index
            return
        self._menu_nav(slots.SLOTS)
        clicked = self._menu_pointer(lambda px, py: list_row_at(*SLOTS_LIST, slots.SLOTS, px, py))
        if not (clicked or self._input.pressed("confirm")):
            return
        n = self._menu_index + 1
        used = self._slot_rows[self._menu_index] is not None
        if self._slots_for == "load":
            if used:
                self._use_slot(n)
                self.continue_game()
        elif used:
            self._overwrite = n
            self._menu_index = 0  # "No"
        else:
            self._use_slot(n)
            self.start_story()

    def _update_overwrite(self):
        n = self._overwrite
        if self._back():
            self._overwrite = None
            self._menu_index = n - 1
            return
        self._menu_nav(len(CONFIRM_OPTIONS))
        clicked = self._menu_pointer(lambda px, py: list_row_at(*CONFIRM_LIST, len(CONFIRM_OPTIONS), px, py))
        if not (clicked or self._input.pressed("confirm")):
            return
        self._overwrite = None
        if CONFIRM_OPTIONS[self._menu_index] == "Yes":
            self._use_slot(n)
            self.start_story()
        else:
            self._menu_index = n - 1

    def _slot_row(self, n, summary):
        if summary is None:
            return (f"Slot {n}   - empty -", None, True)
        place = map_title(map_path(summary.map))
        return (f"Slot {n}   {place}", f"Lv {summary.level}  {slots.format_play_time(summary.play_time)}")

    def _draw_slots(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 90))
        ui.big("ASHEN VAULT", W // 2, 50, ui.HIGHLIGHT, px=3)
        title = "New Game: choose a slot" if self._slots_for == "new" else "Load Game"
        rows = [self._slot_row(i + 1, r) for i, r in enumerate(self._slot_rows)]
        n = self._overwrite
        ui.list_menu(title, *SLOTS_LIST, rows, (n - 1) if n else self._menu_index)
        if n:
            pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 110))
            options = [(o,) for o in CONFIRM_OPTIONS]
            ui.list_menu(f"Overwrite Slot {n}?", *CONFIRM_LIST, options, self._menu_index)

    def _menu_nav(self, n):
        self._menu_index = self._step_index(self._menu_index, n)

    def _step_index(self, i, n):
        wheel = self._input.wheel()
        if self._input.pressed("up") or wheel > 0:
            i = (i - 1) % n
        if self._input.pressed("down") or wheel < 0:
            i = (i + 1) % n
        return i

    def _menu_pointer(self, hit, pick=False):
        """Mouse over a menu. `hit(px, py)` maps a 320x240 point to a row index or None.
        Moving onto a row selects it; a left click on a row selects it and returns True."""
        ptr = self._input.pointer()
        if ptr is None:
            return False
        px, py, moved = ptr
        i = hit(px, py)
        if i is None:
            return False
        if moved or self._input.pressed("click"):
            if pick:
                self._pick_index = i
            else:
                self._menu_index = i
        return bool(self._input.pressed("click"))

    def _back(self):
        return self._input.pressed("cancel") or self._input.pressed("dismiss")

    def _advance(self):
        return self._input.pressed("confirm") or self._input.pressed("click")

    def new_game(self, map_name, at=None, player=None):
        """Starts afresh on `map_name` (at its `start`, or `at`). Debug runs (`--map`) start armed with
        the default kit; the story's start passes a bare `Player.woken()`. `--flags` sets save flags
        before the map loads, as a save would hold them."""
        self.flags = set(filter(None, (self.opts.get("flags") or "").split(",")))
        self.player = player or Player()
        self.messages.clear()
        self._load_world(map_name)
        x, z, yaw = self._spot(at) if at else self.world.start_position()
        self.player.place(x, z, yaw, self.world.map)
        self._debug_setup()
        self._enter_play()

    def start_story(self):
        """New Game: a ring of the town's bell wakes you, one more of the Ashen, in an open grave in the
        Cemetery of Ashes. The journey is recorded at once, so a death before the first prayer still
        wakes you beside the cemetery's first shrine."""
        self.new_game(STORY_MAP, player=Player.woken())
        self.announce_area()
        self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
        self._audio.play("bell", volume=0.5)
        self.message("A bell tolls, far off. The ash in you stirs.")

    def _debug_setup(self):
        """--level, --equip (slot=id pairs) and --afflict for smoke runs; gear is added to the pack
        first, `spell:<id>` teaches that spell and readies it, and each --afflict ailment takes hold at
        once, as a foe's blows would make it (bleed and frost hurt, corrosion wears your gear)."""
        p = self.player
        if self.opts.get("level"):
            p.stats.level = self.opts["level"]
        for pair in filter(None, (self.opts.get("equip") or "").split(",")):
            slot, _, id_ = pair.partition("=")
            slot = SLOT_ALIASES.get(slot, slot)  # primary= / secondary= name the hand slots too
            if id_.startswith(f"{SPELL}:"):  # left=spell:pyre learns that spell and readies it
                id_, _, spell = id_.partition(":")
                if spell not in p.spells:
                    p.spells.append(spell)
                p.equip_spell(spell)
            if id_ in ("", "none"):
                p.inventory.slots[slot] = None
                continue
            if id_ != SPELL:
                p.inventory.add(id_)
            p.inventory.equip(id_, slot if slot in (RIGHT, LEFT) else None)
        for kind in filter(None, (self.opts.get("afflict") or "").split(",")):
            self.world.afflict_player(kind, ailments.FULL)

    def continue_game(self):
        loaded = self._saves.load()
        if not loaded:
            return self.message("The save file could not be read.")
        map_name, player, flags = loaded
        self.player = player
        self.flags = flags
        self.messages.clear()
        self._load_world(map_name)
        self.player.place(*beside_shrine(self.world.map, player.x, player.z, player.yaw), self.world.map)
        self._enter_play()
        self.announce_area()
        self.message("You wake beside the shrine.")

    @staticmethod
    def _spot(at):
        parts = [float(v) for v in str(at).split(",")]
        tx, tz = parts[0], parts[1]
        yaw = parts[2] if len(parts) > 2 else 0
        x, z = TileMap.center(int(tx), int(tz))
        return x, z, yaw * math.pi / 180

    def _load_world(self, name):
        if self.world:
            self.world.unload()
        self.world = World(self, name)
        self._dark_k = None

    def _travel(self, map_name, at):
        self._load_world(map_name)
        x, z, yaw = self._spot(at)
        self.player.place(x, z, yaw, self.world.map)
        self.announce_area()

    def announce_area(self):
        """Raises the area's name over the screen, as you first see it: on waking, on loading a save and on
        every crossing between areas. Debug drops (`--map`) skip it, so their screenshots stay clear."""
        p = self.player
        self.world.region = self.world.region_at(p.x, p.z)
        self.announce_region(self.world.region)

    def announce_region(self, name):
        """Raises `name` over the screen: an area's, or a named region's within it as you cross into it
        (`World._update_regions`)."""
        self.area_title = [name, 0.0]

    def _enter_play(self):
        self.scene = "play"
        self._mouse_look(True)

    # --- play ------------------------------------------------------------------

    def _update_play(self, dt):
        p = self.player
        inp = self._input
        if inp.pressed("pause"):
            return self._open_pause()
        if inp.pressed("menu"):
            return self._open_menu()

        if self._mouse_captured:
            md = pr.get_mouse_delta()
            if self._look_skip > 0:
                self._look_skip -= 1
            else:
                p.turn(md.x * 0.0032)
                p.look(-md.y * 0.0032)
        # Scripted smoke runs tilt the view with held look_up / look_down steps.
        p.look((inp.down("look_up") - inp.down("look_down")) * 1.5 * dt)
        # Over the brink there is nothing to walk on; in the fog you are already walking.
        falling = self.world.terrain.plunging or self.world.fog_walk is not None
        moved = not falling and p.walk(
            self.world.map,
            self._axis("forward", "back"),
            self._axis("strafe_r", "strafe_l"),
            dt,
            blocked=self.world.player_blocker,
            sprint=inp.down("sprint"),
            floating=self.world.terrain.open_to,
            ground=self.world.terrain.floor,
        )
        moved = self._lunge(dt) or moved
        self._carry_player(dt)
        if moved:
            self._footstep()

        p.update_timers(dt)
        self._update_ailments(dt)
        self._update_hands(dt)
        self._update_blows(dt)
        wheel = inp.wheel()
        if wheel:
            self._cycle_quick(-1 if wheel > 0 else 1)  # wheel down = next
        if inp.pressed("quick"):
            self._quick_use()
        if inp.pressed("interact"):
            self._interact()
        self._update_world(dt)

    def _lunge(self, dt):
        """A lunging attack carries you on over a few frames (Player.step_lunge), stopped by walls,
        fog and foes' bodies as walking is."""
        w = self.world
        if w.terrain.plunging or w.fog_walk is not None:  # over the brink, or walking the fog
            self.player.cancel_lunge()
            return False
        return (
            self.player.step_lunge(
                w.map,
                dt,
                blocked=w.player_blocker,
                floating=w.terrain.open_to,
                ground=w.terrain.floor,
                bodies=w.bodies(),
            )
            > 1e-4
        )

    def _carry_player(self, dt):
        """Lifts, rafts and gravity move the player whether or not they walk."""
        self.world.update_terrain(dt)
        if self.world.terrain.plunging:
            return  # the plunge carries you down itself
        under = self.world.terrain.under
        p = self.player
        p.settle(self.world.map, dt, floor=self.world.player_floor(), snap=under is not None and under.moving)

    def _update_blows(self, dt):
        """A swing under way lands at its hit time, and a multi-pulse attack's later blows follow."""
        p = self.player
        if p.swinging and not self._hit_done and p.swing_t >= p.swing_hit_at:
            self._resolve_swing()
        self._update_pulse(dt)

    def _update_world(self, dt):
        self.world.update(dt)
        if not self.player.alive:
            self._dead_t = 0.0
            self.scene = "dead"
            self._drop_remnant()

    def _drop_remnant(self):
        """Death leaves your gold in a heap of ashes where you last stood on solid ground (not down the
        chasm or in the lava that killed you); an older heap you never gathered scatters."""
        x, z = self.world.death_spot()
        lost, left = remnant.leave(self.player, self.world.name, x, z)
        self._remnant_news = []
        if lost:
            self._remnant_news.append(f"The ashes you left behind have scattered. {{{lost} gold}} is lost.")
        if left:
            self._remnant_news.append(f"Your {{{left} gold}} lies with your ashes where you fell.")

    def gather_remnant(self):
        """You reach the heap of ashes you left when you died: its gold is yours again."""
        gold = remnant.gather(self.player)
        self.world.lay_remnant()
        if gold:
            self.sfx("pickup")
            self.message(f"You gather up your ashes. {{+{gold} gold}}")

    def _tick_unpaused(self, dt):
        """Belongings doesn't pause the game: the world goes on and foes still strike while you stand
        there, though you neither walk nor fight."""
        self._lunge(dt)
        self._carry_player(dt)
        self.player.update_timers(dt)
        self._update_ailments(dt)
        self._update_blows(dt)
        self._update_world(dt)

    def _update_ailments(self, dt):
        """Ailment meters drain, and poison and toxic bite (they can kill: see player/ailments.py)."""
        p = self.player
        if not p.alive:
            return
        was_poisoned, was_toxic = p.ailments.poisoned, p.ailments.toxic
        lost = p.ailments.update(dt, p.stats.max_hp)
        if lost:
            p.stats.hurt(lost)
            self.sfx("hiss", 0.35)
        if not p.alive:
            return
        if was_poisoned and not p.ailments.poisoned:
            self.message("The poison runs its course.")
        if was_toxic and not p.ailments.toxic:
            self.message("The toxin ebbs from your blood.")

    def _axis(self, pos, neg):
        return (1 if self._input.down(pos) else 0) - (1 if self._input.down(neg) else 0)

    def _footstep(self):
        phase = math.floor(self.player.bob_t / math.pi)
        if phase == self._step_phase:
            return
        self._step_phase = phase
        tile = self.world.map.tile_at(self.player.x, self.player.z)
        name = footsteps.sound(tile, self.world.terrain.under)
        self.sfx(name, footsteps.VOLUME, random.uniform(0.92, 1.08))

    def _update_hands(self, dt):
        """Each mouse button works its slot (left button = Primary, right = Secondary): a weapon swings
        (tap light, hold heavy), a shield is raised while
        held, a spell is cast. A two-hander swings from Primary only; Secondary then does nothing.
        A scripted `attack` / `cast` taps that button, `attack:0.6` holds it."""
        p = self.player
        inp = self._input
        guard_up = False
        for hand, action in HAND_BUTTON.items():
            does = p.inventory.button_action(hand)
            down, pressed = inp.down(action), inp.pressed(action)
            if does == "guard":
                guard_up = guard_up or down or pressed
            elif does == "cast":
                if pressed:
                    self._cast_spell()
            elif does == "swing":
                self._update_weapon_button(hand, action, dt, down, pressed)
        was = p.guarding
        if p.raise_guard(guard_up) and not was:
            self.sfx("step", 0.5)

    def _update_weapon_button(self, hand, action, dt, down, pressed):
        p = self.player
        if down:
            if not p.swinging and (p.charge_hand == hand or p.charge_t == 0):
                p.charge_hand = hand
                p.charge_t += dt
            self._held[action] = True
            return
        released, self._held[action] = self._held[action], False
        if not (released or pressed):
            if p.charge_hand == hand:
                p.charge_t = 0.0
            return
        heavy = p.charge_hand == hand and p.charge_t >= weapons.CHARGE_TIME
        self._swing(hand, weapons.HEAVY if heavy else weapons.LIGHT, art=heavy)
        if p.charge_hand == hand:
            p.charge_t = 0.0

    def _swing(self, hand, kind, art=False):
        """Starts a swing. `art`: a heavy released with both gauges full looses the weapon's art, if
        it has one and you have the MP (Player.art_ready)."""
        p = self.player
        if p.swinging:
            return
        if p.stamina.exhausted:
            self.message("Too winded to swing.")
            return
        a = p.start_swing(hand, kind, art=art)
        if not a:
            return
        self._hit_done = False
        if p.swing_art:
            self.sfx("heavy", 0.8)
            self.sfx("spell", 0.6)
            self.message(f"{{{p.swing_art.name}}}!")
        elif a.kind == weapons.SECRET:
            self.sfx("heavy", 0.9)
            self.sfx("swoosh", 0.6)
            self.message(f"{{{a.name}}}!")
            self.flags.add(f"secret:{p.swing_weapon.category}")
        elif a.heavy:
            self.sfx("heavy", 0.7)
        else:
            self.sfx("swing", 0.6)
            if kind == weapons.HEAVY:
                self.message("Too winded for a heavy attack.")

    def _swing_power(self, weapon):
        """A weapon's ATK; bare fists hit harder in gauntlets."""
        return compare.swing_power(weapon, self.player.inventory.hands_item())

    def _hands_mult(self, weapon):
        """Bare, ungloved fists land only a fraction of a blow (`compare.BARE_HANDED`)."""
        return compare.strike_mult(weapon, self.player.inventory.hands_item())

    def _resolve_swing(self):
        self._hit_done = True
        p = self.player
        weapon = p.swing_weapon
        a = p.attack
        for prop in self.world.strike_props(weapon.reach * a.reach, a.cone):
            self._break(prop)
        self.world.strike_wards(weapon.reach * a.reach, a.cone)
        self.world.strike_core(weapon.reach * a.reach, weapon, a.cone)
        targets = self._strike(weapon, a)
        if targets:
            p.land_hit(targets[0])
            p.wear_weapon()
        if a.pulses > 1:
            self._pulse = [a.pulse_gap, a, weapon, a.pulses - 1]
        if p.swing_art:
            self._release_art(weapon, p.swing_art)

    def _art_damage(self, weapon, art):
        """What a weapon art deals before elements: the weapon's full-gauge blow, scaled by the art."""
        p = self.player
        return Combat.damage(
            base=self._swing_power(weapon),
            strength=p.stats.strength,
            gauge=1.0,
            defense=0,
            mult=art.damage * self._hands_mult(weapon),
        )

    def _release_art(self, weapon, art):
        """The weapon art riding on the swing that just landed (weapons.ARTS)."""
        p = self.player
        p.veil_t = 0.0
        dmg = self._art_damage(weapon, art)
        speed = art.speed or shots.BOLT_SPEED
        if art.kind == weapons.CONE:
            self.sfx("spell", 0.5)

            def burn(e):
                self.damage_enemy(e, max(rround(dmg * elements.mult(e.type, art.element)), 1))
                if elements.burns(e.type, art.element) and e.alive:
                    e.afflict("burn", *elements.WEAPON_BURN)

            self.world.flame_cone(art.reach, burn)
        elif art.kind == weapons.BOLT:
            self.sfx("thunder" if art.effect == "thunder" else "spell")
            self.world.fire_bolt(dmg, effect=art.effect, rgb=art.rgb, speed=speed)
        elif art.kind == weapons.VOLLEY:
            self.sfx("spell", 0.7)
            self.world.volley(dmg, art.count, art.spread, art.effect, art.rgb, speed)
        elif art.kind == weapons.RING:
            self.sfx("heavy", 1.0)
            self.world.slag_ring(lambda e: dmg * elements.mult(e.type, art.element), art.reach)
        elif art.kind == weapons.WAVE:
            self.sfx("swoosh", 1.0, 0.7)
            self.sfx("spell", 0.5, 1.3)
            self.world.crescent_wave(dmg, art.width, speed, art.life, art.rgb, art.effect)

    def _strike(self, weapon, a, mult=1.0):
        """Deals one blow of attack `a` to everything in reach; returns who it hit."""
        p = self.player
        targets = self.world.melee_targets(weapon.reach * a.reach, a.cone, a.targets)
        if not targets:
            return targets
        for sound in sorted({t.hit_sound for t in targets}):  # one per material struck
            self.sfx(sound, pitch=random.uniform(*HIT_PITCH))
        for target in targets:
            back = target.hit_mult(p.x, p.z)
            element = weapon.element
            dmg = Combat.damage(
                base=self._swing_power(weapon),
                strength=p.stats.strength,
                gauge=p.swing_power,
                defense=4 if target.type.boss and not a.pierce_def else 0,
                mult=a.damage
                * back
                * mult
                * elements.mult(target.type, element)
                * elements.brittle_mult(target.type, weapon)
                * self._hands_mult(weapon)
                * self._worn_mult(weapon),
            )
            if back > 1:
                self.message(f"You strike the {target.name}'s weak spot!")
            jolt = elements.staggers(target.type, element)
            self.damage_enemy(target, dmg, 99.0 if jolt else a.poise * back, heavy=weapons.is_heavy(weapon))
            if elements.burns(target.type, element) and target.alive:
                target.afflict("burn", *elements.WEAPON_BURN)
            if a.pull and target.alive:
                self._pull(target, a.pull)
        return targets

    def _worn_mult(self, weapon):
        """A broken weapon lands only `durability.BROKEN_POWER` of its blows."""
        return durability.BROKEN_POWER if self.player.inventory.broken(weapon.id) else 1.0

    def _announce_wear(self):
        """Word of gear that just broke or grew badly worn (`Player.wear_news`)."""
        news, self.player.wear_news = self.player.wear_news, []
        for item, state in news:
            if state == "broken":
                self.sfx("crack", 0.8)
                self.message(f"Your {{{item.name}}} breaks!")
            else:
                self.message(f"Your {{{item.name}}} is badly worn.")

    def _pull(self, enemy, dist):
        """The whip's Snare: drags `enemy` up to `dist` metres toward you, stopping short of you."""
        p = self.player
        dx, dz = p.x - enemy.x, p.z - enemy.z
        d = math.hypot(dx, dz)
        step = min(dist, d - enemy.radius - p.RADIUS - 0.3)
        if step <= 0:
            return
        self.world.move_enemy(enemy, dx / d * step, dz / d * step)

    def _update_pulse(self, dt):
        """The later blows of a multi-pulse attack: the hammer's Aftershock (the ground answers the slam a
        moment later)."""
        if not self._pulse:
            return
        self._pulse[0] -= dt
        if self._pulse[0] > 0:
            return
        _, a, weapon, left = self._pulse
        self._pulse = [a.pulse_gap, a, weapon, left - 1] if left > 1 else None
        if a.heavy:
            self.sfx("heavy", 0.6)
        else:
            self.sfx("swing", 0.5)
        self._strike(weapon, a, a.pulse_damage)

    def blocked(self, block):
        """The world calls this when a raised shield meets a blow."""
        if block.broken:
            self.sfx("crack", 0.9)
            self.message("Your guard breaks!")
        else:
            self.sfx("hit", 0.5)

    def _break(self, prop):
        gold, item = self.world.break_prop(prop)
        if prop.kind == "cocoon":
            self.sfx("swoosh", 0.7)
            if gold:
                self.sfx("pickup", 0.4)
                self.message(f"You slit the cocoon. A few coins fall out. {{+{gold} gold}}")
            if item:
                self.message("Something drops out of the torn silk.")
        elif prop.kind != "secret_wall":
            self.sfx("crack")
            if gold:
                self.sfx("pickup", 0.4)
                self.message(f"A few coins spill out. {{+{gold} gold}}")
            if item:
                self.message(f"Something rolls out of the broken {prop.kind}.")
        elif prop.props.get("model") == "vines":
            self.sfx("swoosh", 0.9)
            self.message("You hack through the vines. There is a hollow behind them!")
        else:
            self.sfx("crack", 0.9)
            self.sfx("hiss", 0.5)  # it sears to ash before it crumbles
            self.message("The wall was an illusion! It crumbles into ash.")

    def damage_enemy(self, enemy, dmg, poise_mult=1.0, stagger=True, heavy=False):
        dmg = rround(dmg * self.world.core_mult(enemy))  # a golem cut off from its quenched core
        if not enemy.take_hit(dmg, poise_mult, stagger=stagger, heavy=heavy):
            return
        self.sfx("enemy_die")
        t = enemy.type
        if enemy.key:
            self.flags.add(enemy.key)
        self.world.drop_enemy_loot(enemy)
        if self.world.split(enemy):
            self.message(f"{t.called} bursts apart, and the pieces crawl on!")
        gold = random.choice(t.gold)
        self.player.inventory.gold += gold
        self.message(f"{t.name} destroyed. {t.exp} EXP, {gold} gold.")
        if self.player.stats.gain_exp(t.exp) > 0:
            self.sfx("levelup")
            self.message(f"You reached level {self.player.stats.level}!")
        if not t.boss:
            return
        if not relics.boss_falls(t, self.world.enemies):
            return  # its twin fights on; the pair falls together
        for spawn in (t.brood, t.sheds):
            for e in self.world.enemies:
                if spawn and e.type.id == spawn:
                    e.kill()
        if t.dead_flag:
            self.flags.add(t.dead_flag)
        if t.drop:
            self.world.drop_relic(t.drop, enemy.x, enemy.z)
        if t.epitaph:
            self.message(t.epitaph)

    def hurt_player(self, dmg, source):
        if not self.player.alive:
            return
        if self.player.ward_t > 0:
            dmg = Spells.warded(dmg, self.player.stats.magic)
        self.player.stats.hurt(dmg)
        self.player.hurt_t = 0.4
        self.player.cancel_lunge()  # a blow that lands stops a lunge short
        self.sfx("hurt")
        if dmg >= 10:
            self.message(f"{source} hits you for {dmg}.")

    def _cast_spell(self):
        p = self.player
        spell = p.current_spell()
        if not spell:
            return self.message("You know no spells.")
        if not p.magic_gauge.full:
            return self.message("Your focus has not returned.")
        if not p.stats.spend_mp(spell.cost):
            return self.message("Not enough MP.")
        gauge = p.magic_gauge.spend()
        p.magic_gauge.refill_time = spell.recovery
        self.sfx("spell", 0.5 if spell.id == "pyre" else 1.0)
        if spell.id != "veil":
            p.veil_t = 0.0  # any other spell lights you up through the mist
        if spell.id == "flame":
            self.world.fire_bolt(Spells.flame_damage(p.stats.magic, gauge))
        elif spell.id == "mend":
            amount = Spells.mend_amount(p.stats.magic)
            p.stats.heal(amount)
            self.message(f"Warmth closes your wounds. +{amount} HP")
        elif spell.id == "lumen":
            p.lumen_t = Spells.LUMEN_DURATION
            self.message("A pale light gathers around you.")
        elif spell.id == "venom":
            self.world.fire_bolt(
                Spells.venom_damage(p.stats.magic, gauge), effect="venom", rgb=(130, 220, 60)
            )
        elif spell.id == "veil":
            p.veil_t = Spells.VEIL_DURATION
            self.sfx("hiss", 0.8)
            self.message("Mist curls up around you. Foes lose sight of you.")
        elif spell.id == "pyre":
            self.sfx("pyre")
            self.world.pyre(p.stats.magic, gauge)
        elif spell.id == "thunder":
            self.sfx("thunder")
            self.world.fire_bolt(
                Spells.thunder_damage(p.stats.magic, gauge),
                effect="thunder",
                rgb=(200, 225, 255),
                speed=Spells.THUNDER_SPEED,
            )
        elif spell.id == "motes":
            self.sfx("motes")
            self.world.motes(Spells.mote_damage(p.stats.magic, gauge))
        elif spell.id == "ward":
            p.ward_t = Spells.WARD_DURATION
            self.sfx("ward")
            self.message("Embers wreathe you. Blows land softer.")
        elif spell.id == "rift_lance":
            self.sfx("thunder", 0.6, 1.4)
            self.world.rift_lance(Spells.rift_damage(p.stats.magic, gauge))
        elif spell.id == "bellward":
            self.sfx("bell", 1.0, 1.2)
            struck = self.world.bell_toll(Spells.bell_damage(p.stats.magic, gauge), Spells.BELL_RADIUS)
            if struck:
                self.message("The phantom bell tolls. Your foes reel.")
        elif spell.id == "mortar_shard":
            self.sfx("crack", 0.7, 0.8)
            self.world.fire_bolt(
                Spells.mortar_damage(p.stats.magic, gauge), effect="mortar", rgb=Spells.MORTAR_RGB
            )

    def _cycle_quick(self, step=1):
        item = self.player.cycle_quick(step)
        if item:
            self.message(f"{item.name} x{self.player.inventory.count(item.id)}")

    def _quick_use(self):
        """Middle click: uses the item in the selected quick slot."""
        item = self.player.quick_item()
        if item is None:
            return self.message("No quick item. Set one in Belongings.")
        if not self.player.inventory.has(item.id):
            return self.message(f"You have no {item.name}.")
        self._use_item(item)

    def _use_item(self, item):
        inv = self.player.inventory
        if item.effect == "homeward":
            return self._use_hearth_ash(item)
        if item.kind == "consumable":
            inv.remove(item.id)
            if item.heal:
                self.player.stats.heal(item.heal)
            if item.mana:
                self.player.stats.restore_mp(item.mana)
            for kind in item.cures:
                self.player.cure(kind)
            if item.effect:
                self.player.drink(item.effect)
            self.sfx("pickup", 0.6)
            self.message(f"Used {item.name}.")
        elif item.kind == "scroll":
            inv.remove(item.id)
            first = not self.player.spells
            if item.spell not in self.player.spells:
                self.player.spells.append(item.spell)
            if first:
                self.player.equip_spell(item.spell)
            self.sfx("levelup")
            self.message(f"You learned {{{Spells.get(item.spell).name}}}. Ready it from Belongings.")
        elif item.kind == "repair":
            if self._mendable():
                self._open_pick(item)  # ask which piece to mend
            else:
                self.message("Nothing needs mending.")
        elif item.kind == "spell":
            self._open_pick(item)  # like a weapon: always ask which slot it goes in
        elif item.kind in ("weapon", "shield", "armor"):
            if item.kind == "armor" or item.two_handed:
                if inv.unequip(item.id):
                    self.message(f"Unequipped {item.name}.")
                else:
                    self._equip(item)
            else:
                self._open_pick(item)
        else:
            self.message("Not usable from here.")

    def _equip(self, item, hand=None):
        """Equips `item` (a spell row puts the readied spell in `hand`), unless your level is too low."""
        inv = self.player.inventory
        level = self.player.stats.level
        id_ = SPELL if item.kind == "spell" else item.id
        if inv.equip_error(id_, level) == "level":
            verb = "wear" if item.kind == "armor" else "wield"
            self.sfx("hurt", 0.3)
            self.message(f"You need level {item.level} to {verb} the {item.name}.")
            return False
        if not inv.equip(id_, hand, level):
            return False
        where = f" as {SLOT_NAMES[hand]}" if hand and item.kind != "armor" and not item.two_handed else ""
        self.message(f"Equipped {{{item.name}}}{where}.")
        return True

    def focus_label(self):
        if self.scene != "play" or not self.world:
            return None
        p = self.world.focus()
        if not p:
            return None
        if isinstance(p, Enemy):
            return "[E] Open chest"
        if p.kind == "door" and self.world.fog_gate(p):
            return "[E] Pass through the fog"
        if p.kind == "house_door":
            return "[E] Close door" if p.goal >= 1.0 else "[E] Open door"
        return {
            "npc": "[E] Talk",
            "chest": "[E] Open chest",
            "door": "[E] Open door",
            "lever": "[E] Pull lever",
            "save_statue": "[E] Pray at the shrine",
            "exit": f"[E] {(p.props.get('label') or 'Leave').replace('_', ' ')}",
            "pickup": "[E] Take",
            "iron_maiden": "[E] Step inside",
            "frog_idol": "[E] Pat the stone frog",
            "silent_bell": (
                "[E] Ring the Silent Bell"
                if dialogue_data.BELL_UNSEALED in self.flags
                else "[E] Touch the Silent Bell"
            ),
            "brazier": "[E] Look at the cold brazier",
            "fen_beacon": "[E] Smother the beacon",
            "bonfire": "[E] Look at the cold ashes",
            "altar": f"[E] Take the {Items.get(p.props.get('item', 'warden_key')).name}",
        }.get(p.kind)

    def _interact(self):
        prop = self.world.focus()
        if not prop:
            return
        if isinstance(prop, Enemy):
            prop.wake(self.player.x, self.player.z)
            self.sfx("hurt", 0.6)
            self.message("The chest lunges at you!")
            return
        k = prop.kind
        if k == "npc":
            self._start_dialogue(*dialogue_data.for_npc(prop.props.get("id"), self))
        elif k == "chest":
            self._open_chest(prop)
        elif k == "door" and self.world.fog_gate(prop):
            self.world.cross_fog(self.world.fog_gate(prop))
        elif k == "door":
            self._open_door(prop)
        elif k == "house_door":
            self.world.swing_door(prop)
        elif k == "lever":
            self.world.pull_lever(prop)
            self.sfx("door")
            if prop.props.get("model") == "wood":
                self.message("Ropes groan through the timbers, and something heavy shifts.")
            else:
                self.message("Somewhere chains rattle, and iron grinds against stone.")
        elif k in ("brazier", "bonfire"):
            self.message("Cold ashes. It wants a flame.")
        elif k == "fen_beacon":
            self.world.douse(prop)
        elif k == "save_statue":
            self._open_shrine()
        elif k == "remnant":
            self.gather_remnant()
        elif k == "altar":
            item = Items.get(self.world.take_from_altar(prop))
            self.player.inventory.add(item.id)
            relics.mark_taken(item.id, self.flags)  # a sigil on an altar is taken up as any other
            self.sfx("bell", 0.7)
            self.message(f"Obtained {{{item.name}}}.")
            for line in prop.props.get("said", WARDEN_ALTAR_SAID).split("|"):
                self.message(line)
        elif k == "iron_maiden":
            self._enter_maiden(prop)
        elif k == "frog_idol":
            self._pat_frog(prop)
        elif k == "silent_bell":
            # TODO(story): the secret beneath the Silent Bell. Once unsealed, ringing it ends the game for
            # now; the descent below the Bell Square will take the ending's place.
            lines, ends = dialogue_data.bell(self.flags, relics.held(self.player.inventory.has))
            for line in lines:
                self.message(line)
            if ends:
                self.finish_game()
            else:
                self.sfx("bell", 0.25)
        elif k == "exit":
            self._take_exit(prop)
        elif k == "pickup":
            item = Items.get(prop.props["item"])
            p = self.player
            kept, spare = loot.claim(p.inventory, stash.known_spells(p), item.id, p.stash)
            if kept:
                p.inventory.add(kept)
            p.inventory.gold += spare
            self.flags.add(prop.key)
            relics.mark_taken(item.id, self.flags)
            self.world.remove_prop(prop)
            self.sfx("pickup")
            self.message(f"Obtained {{{item.name}}}.")
            if spare:
                self.message(loot.spare_message(spare))

    def _take_exit(self, prop):
        """Goes through an exit. One with `requires=<flag>` stays shut until that flag is set (its
        `shut=` words say why). A `oneway` exit never leads back: you are recorded on the far side at
        once (so you wake by its shrine, not behind you) and a `left:<map>` flag remembers it."""
        if not self.world.exit_open(prop):
            self.sfx("door", 0.5)
            self.message(prop.props.get("shut", "It will not open.").replace("_", " "))
            return
        left = self.world.name
        self._travel(prop.props["map"], prop.props["at"])
        if "oneway" in prop.props:
            self.flags.add(f"left:{left}")
            self._saves.save(map=self.world.name, player=self.player, flags=self.flags)

    # --- shrine rest ------------------------------------------------------------------

    def _start_rest(self, label="Resting..."):
        """Kneel at the shrine: ember fog rises over the screen, and while it hides everything the
        shrine restores you, wakes the fallen and records the journey."""
        self._rest = RestSequence(label=label)
        self.scene = "rest"
        self.player.charge_t = 0.0
        self._held = {"attack": False, "cast": False}
        self.player.guarding = False
        self.sfx("save")

    def _use_hearth_ash(self, item):
        """Hearth Ash: ember fog rises as at a shrine, and while it hides everything you are carried
        to Bell Square in Harrowmere. Nothing is restored or recorded. Refused (and kept) where the
        world won't let you go (`World.homeward_refusal`)."""
        refusal = self.world.homeward_refusal()
        if refusal:
            self.sfx("door", 0.5)
            return self.message(refusal)
        self.player.inventory.remove(item.id)
        self._pick = None
        self._mouse_look(True)
        self._start_rest("Homeward...")
        self._rest_home = True

    def _update_rest(self, dt):
        if self._rest.update(dt):
            if self._rest_home:
                self._load_world(HOME_MAP)
                spot = home_spot(self.world.map)
                if spot:
                    self.player.place(*spot, self.world.map)
                self.announce_area()
            else:
                self.player.revive()
                self.world.respawn_enemies()
                self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
        if self._rest.done:
            self._rest = None
            self.scene = "play"
            if self._rest_home:
                self._rest_home = False
                self.message("The embers carry you home.")
            else:
                self.message("The shrine restores you. Your journey is recorded.")
                self.message("Somewhere below, the fallen stir again.")

    def _pat_frog(self, prop):
        """A small joke by the river: the frog croaks, and the very first time it pays you for the pat."""
        if prop.open_t > 0:
            return
        gold = self.world.pat_frog(prop)
        self.sfx("croak")
        if gold:
            self.sfx("pickup", 0.5)
            self.message("The stone frog croaks. Something clinks in its mouth.")
            self.message(f"It spits out {{{gold} gold}}.")
        else:
            self.message("The stone frog croaks contentedly.")

    def _enter_maiden(self, prop):
        """A hidden kindness: the old spikes are blunt, and the embrace mends rather than kills.
        Unlike the shrine it neither records the journey nor wakes the fallen."""
        if prop.open_t > 0:
            return
        s = self.player.stats
        s.heal(s.max_hp)
        s.restore_mp(s.max_mp)
        self.player.stamina.fill()
        self.world.enter_maiden(prop)
        self.sfx("door", 0.8)
        self.sfx("save", 0.7)
        self.message("The spikes are blunt with age. The iron embraces you gently.")
        self.message("You step out whole again.")

    def _open_chest(self, prop):
        self.world.open_prop(prop)
        self.sfx("chest")
        item = prop.props.get("item")
        count = int(prop.props.get("count", "1"))
        gold = int(prop.props.get("gold", "0"))
        p = self.player
        kept, spare = loot.claim(p.inventory, stash.known_spells(p), item, p.stash) if item else (None, 0)
        if kept:
            p.inventory.add(kept, count)
        p.inventory.gold += gold + spare
        parts = []
        if item:
            parts.append(f"{{{Items.get(item).name}{f' x{count}' if count > 1 else ''}}}")
        if gold > 0:
            parts.append(f"{{{gold} gold}}")
        self.message(f"Found {' and '.join(parts)}.")
        if spare:
            self.message(loot.spare_message(spare))

    def _open_door(self, prop):
        if not doors.opens_from(prop.props.get("from"), prop.x, prop.z, self.player.x, self.player.z):
            self.sfx("clunk", 0.6)
            self.message("It is barred from the other side.")
            return
        key = prop.props.get("key")
        if key and not self.player.inventory.has(key):
            self.message(f"It is locked. You need the {Items.get(key).name}.")
            return
        self.world.open_prop(prop)
        self.sfx("door")
        if prop.props.get("boss") in self.flags:  # its boss has fallen: nothing waits beyond it now
            self.message("The great door groans open.")
        elif prop.props.get("boss"):
            self.message("The great door groans open. Something stirs beyond.")
        elif key:
            self.message(f"The {Items.get(key).name} turns in the lock.")
        elif prop.props.get("from"):
            self.message("You lift the bar. The way back lies open.")
        else:
            self.message("The door grinds open.")

    def message(self, text):
        self.messages.append([text, 0.0])

    def sfx(self, name, volume=1.0, pitch=1.0):
        self._audio.play(name, volume=volume, pitch=pitch)

    # --- dialogue ------------------------------------------------------------

    def _start_dialogue(self, speaker, lines, after):
        self._dialogue = {"speaker": speaker, "lines": lines, "page": 0, "after": after}
        self.scene = "dialogue"

    def _update_dialogue(self):
        inp = self._input
        if not (self._advance() or inp.pressed("interact") or self._back()):
            return
        d = self._dialogue
        d["page"] += 1
        if d["page"] < len(d["lines"]):
            return
        self.scene = "play"
        if d["after"]:
            d["after"](self)

    # --- inventory menu ------------------------------------------------------------

    def _open_menu(self):
        self.scene = "menu"
        self._menu_index = self._tab_rows.get(self._menu_tab, 0)
        self._menu_top = 0
        self._pick = None
        self._mouse_look(False)
        self.player.guarding = False
        self.player.charge_t = 0.0  # a heavy held as it opened is let go, not loosed
        self._held = dict.fromkeys(self._held, False)

    def _open_pick(self, item):
        """Asks which slot (Primary or Secondary) a one-handed weapon, a shield or a spell goes in,
        which piece a Mender's Kit mends, or whether to use a consumable or set it in a quick slot."""
        self._pick = item
        self._pick_index = 0

    def _spell_name(self):
        spell = self.player.current_spell()
        return spell.name if spell else None

    def _mendable(self):
        """Every piece of gear carried or stored that has lost durability."""
        p = self.player
        return p.inventory.damaged([*p.inventory.counts, *p.stash])

    def _wear_mark(self, item):
        inv = self.player.inventory
        return f"{inv.durability(item.id)}/{inv.max_durability(item.id)}"

    def _pick_options(self):
        if self._pick.kind == "repair":
            return [(f"{i.name}  {self._wear_mark(i)}", i.id) for i in self._mendable()]
        if self._pick.kind == "consumable":
            return belongings.consumable_options(self.player, self._pick)
        spell = self.player.current_spell()
        return belongings.pick_options(
            self.player.inventory, self._pick, self._spell_name(), spell.id if spell else None
        )

    def _update_pick(self):
        opts = self._pick_options()
        if self._back():
            self._pick = None
            return
        self._pick_index = self._step_index(self._pick_index, len(opts))
        clicked = self._menu_pointer(lambda px, py: list_row_at(*PICK_LIST, len(opts), px, py), pick=True)
        if not (clicked or self._input.pressed("confirm")):
            return
        item, (_, hand) = self._pick, opts[self._pick_index]
        self._pick = None
        if item.kind == "repair":
            return self._mend(hand, kit=True)
        if item.kind == "consumable":
            return self._choose_quick(item, hand)
        if hand is None:
            self.player.inventory.unequip(belongings.held_id(item))
            self.message(f"Unequipped {item.name}.")
        else:
            self._equip_in(item, hand)

    def _choose_quick(self, item, choice):
        """A consumable's chooser row: use it, put it in quick slot `choice`, or take it off the wheel."""
        p = self.player
        if choice == belongings.USE:
            return self._use_item(item)
        self.sfx("step", 0.4)
        if choice == belongings.UNQUICK:
            p.clear_quick(p.quick_slot_of(item.id))
            return self.message(f"{item.name} is off the wheel.")
        p.assign_quick(choice, item.id)
        self.message(f"{{{item.name}}} set in Quick {choice + 1}.")

    def _mend(self, id_, kit=False):
        """Mends `id_` whole: with a Mender's Kit (`kit`), or paying Brannoc. False if you can't pay."""
        inv = self.player.inventory
        item = Items.get(id_)
        if kit:
            inv.remove(durability.KIT)
        else:
            cost = durability.repair_cost(item, inv.missing(id_))
            if inv.gold < cost:
                self.message("You can't afford that.")
                return False
            inv.gold -= cost
        inv.repair(id_)
        self.sfx("anvil", 0.7)
        self.message(f"Your {{{item.name}}} is mended whole.")
        return True

    def _equip_in(self, item, slot):
        """Puts a weapon, shield or spell row into `slot` (a two-hander takes both)."""
        if item.kind == "spell":
            self.player.equip_spell(item.spell)
            self.sfx("spell", 0.4)
        self._equip(item, None if item.two_handed else slot)

    def _menu_items(self):
        """Belongings rows: carried items plus one row per known spell (choose it to ready it)."""
        spells = [
            Item(id=f"spell_{s.id}", name=s.name, kind="spell", spell=s.id, desc=s.desc)
            for s in (Spells.get(id_) for id_ in self.player.spells)
        ]
        rows = [i for i in self.player.inventory.items() + spells if belongings.tab_of(i) == self._menu_tab]
        return sorted(rows, key=lambda i: (KIND_ORDER.index(i.kind), i.name))

    def _tab_spans(self):
        x, _y, _w = MENU_LIST
        return belongings.tab_spans(x + 8, [ui.measure(t) for t in belongings.TABS])

    def _switch_tab(self, tab):
        """Shows Belongings tab `tab`, back on the row last highlighted there."""
        if tab == self._menu_tab:
            return
        self._tab_rows[self._menu_tab] = self._menu_index
        self._menu_tab = tab
        self._menu_index = self._tab_rows.get(tab, 0)
        self._menu_top = 0
        self.sfx("step", 0.4)

    def _update_tabs(self):
        """A / D (or Left / Right) step through the tabs; clicking a tab's label opens it."""
        for action, step in (("tab_prev", -1), ("tab_next", 1)):
            if self._input.pressed(action):
                self._switch_tab(belongings.step_tab(self._menu_tab, step))
        ptr = self._input.pointer()
        if ptr and self._input.pressed("click"):
            px, py, _ = ptr
            _x, y, _w = MENU_LIST
            i = belongings.tab_at(self._tab_spans(), px) if y + 2 <= py < y + 16 else None
            if i is not None:
                self._switch_tab(belongings.TABS[i])
                return True
        return False

    def _update_menu(self, dt):
        self._tick_unpaused(dt)
        if self.scene != "menu":  # fallen while browsing
            return self._mouse_look(True)
        if self._pick:
            return self._update_pick()
        if self._back():
            return self._enter_play()
        if self._update_tabs():
            return
        items = self._menu_items()
        if not items:
            return
        self._menu_nav(len(items))
        self._menu_index = clamp(self._menu_index, 0, len(items) - 1)
        self._menu_top = scroll_into_view(self._menu_top, self._menu_index, len(items))
        clicked = self._menu_pointer(
            lambda px, py: list_row_at(*MENU_LIST, len(items), px, py, self._menu_top, LIST_ROWS)
        )
        item = items[self._menu_index]
        if clicked or self._input.pressed("confirm"):
            if item.kind == "consumable":
                return self._open_pick(item)  # use it, or set it in a quick slot
            return self._use_item(item)
        for slot, action in ((PRIMARY, "slot1"), (SECONDARY, "slot2")):
            if self._input.pressed(action):
                if belongings.slottable(item):
                    self._equip_in(item, slot)
                else:
                    self.message(f"The {item.name} doesn't go in a slot.")

    # --- shop ----------------------------------------------------------------------

    def open_shop(self, shop_id="pell"):
        self.scene = "shop"
        self._shop_id = shop_id
        self._menu_index = 0
        self._menu_top = 0
        self._mouse_look(False)
        self.player.guarding = False

    def _shop_stock(self):
        """What the shop offers: Brannoc's mending first, then whatever you don't own yet (stored
        things count as owned)."""
        p = self.player
        out = [MEND_ROW] if self._shop_id in dialogue_data.REPAIRERS else []
        known = stash.known_spells(p)
        for id_ in dialogue_data.shop_stock(self._shop_id, self.flags):
            item = Items.get(id_)
            if item.kind == "scroll" and (item.spell in known or stash.owns(p, id_)):
                continue
            if item.kind in ("weapon", "shield", "armor") and stash.owns(p, id_):
                continue
            out.append(item)
        return out

    def _update_shop(self):
        stock = self._shop_stock()
        if self._back() or not stock:
            return self._enter_play()
        self._menu_nav(len(stock))
        self._menu_index = clamp(self._menu_index, 0, len(stock) - 1)
        self._menu_top = scroll_into_view(self._menu_top, self._menu_index, len(stock))
        clicked = self._menu_pointer(
            lambda px, py: list_row_at(*SHOP_LIST, len(stock), px, py, self._menu_top, LIST_ROWS)
        )
        if not (clicked or self._input.pressed("confirm")):
            return
        item = stock[self._menu_index]
        if item is MEND_ROW:
            return self._open_repair()
        if self.player.inventory.buy(item.id):
            self.sfx("pickup")
            self.message(f"Bought {{{item.name}}}.")
            if item.level > self.player.stats.level:
                self.message(f"You will need level {item.level} to use it.")
        else:
            self.message("You can't afford that.")

    # --- the smith's mending ------------------------------------------------------

    def _open_repair(self):
        if not self._mendable():
            return self.message("Nothing needs mending.")
        self.scene = "repair"
        self._menu_index = 0
        self._menu_top = 0

    def _leave_repair(self):
        self.scene = "shop"
        self._menu_index = 0
        self._menu_top = 0

    def _update_repair(self):
        worn = self._mendable()
        if self._back() or not worn:
            return self._leave_repair()
        self._menu_nav(len(worn))
        self._menu_index = clamp(self._menu_index, 0, len(worn) - 1)
        self._menu_top = scroll_into_view(self._menu_top, self._menu_index, len(worn))
        clicked = self._menu_pointer(
            lambda px, py: list_row_at(*SHOP_LIST, len(worn), px, py, self._menu_top, LIST_ROWS)
        )
        if clicked or self._input.pressed("confirm"):
            self._mend(worn[self._menu_index].id)

    def _repair_cost(self, item):
        return durability.repair_cost(item, self.player.inventory.missing(item.id))

    # --- shrine and its store --------------------------------------------------------

    def _open_shrine(self):
        """Kneel at the shrine: rest, open the store, or leave."""
        self.scene = "shrine"
        self._menu_index = 0
        self._mouse_look(False)
        self.player.guarding = False
        self.player.charge_t = 0.0
        self._held = dict.fromkeys(self._held, False)

    def _update_shrine(self):
        if self._back():
            return self._enter_play()
        self._menu_nav(len(SHRINE_OPTIONS))
        clicked = self._menu_pointer(lambda px, py: list_row_at(*SHRINE_LIST, len(SHRINE_OPTIONS), px, py))
        if not (clicked or self._input.pressed("confirm")):
            return
        choice = SHRINE_OPTIONS[self._menu_index]
        if choice == "Rest":
            self._mouse_look(True)
            self._start_rest()
        elif choice == "Storage":
            self._open_storage()
        else:
            self._enter_play()

    def _open_storage(self):
        self.scene = "storage"
        self._store_side = STORE_SIDES[0]
        self._store_at = dict.fromkeys(STORE_SIDES, 0)
        self._store_top = dict.fromkeys(STORE_SIDES, 0)

    @staticmethod
    def _spell_rows(ids):
        return [
            Item(id=f"spell_{s.id}", name=s.name, kind="spell", spell=s.id, desc=s.desc)
            for s in (Spells.get(i) for i in ids)
        ]

    def _store_rows(self, side):
        """The store's lists: what you carry that may be stored, or what waits in the store."""
        p = self.player
        if side == "carried":
            items = [i for i in p.inventory.items() if stash.can_store(i)] + self._spell_rows(p.spells)
        else:
            items = [Items.get(i) for i in p.stash] + self._spell_rows(p.stashed_spells)
        return sorted(items, key=lambda i: (KIND_ORDER.index(i.kind), i.name))

    def _store_count(self, side, item):
        if item.kind == "spell":
            return 1
        return (
            self.player.inventory.count(item.id) if side == "carried" else self.player.stash.get(item.id, 0)
        )

    def _store_list(self, side):
        return STORE_LIST if side == "carried" else STASH_LIST

    def _update_storage(self):
        if self._back():
            self.scene = "shrine"
            self._menu_index = SHRINE_OPTIONS.index("Storage")
            return
        for action, side in (("tab_prev", "carried"), ("tab_next", "stored")):
            if self._input.pressed(action):
                self._store_side = side
        ptr = self._input.pointer()
        clicked = False
        if ptr:  # the pointer picks a side and a row
            px, py, moved = ptr
            for side in STORE_SIDES:
                rows = self._store_rows(side)
                i = list_row_at(*self._store_list(side), len(rows), px, py, self._store_top[side], LIST_ROWS)
                if i is not None and (moved or self._input.pressed("click")):
                    self._store_side = side
                    self._store_at[side] = i
                    clicked = bool(self._input.pressed("click"))
        side = self._store_side
        rows = self._store_rows(side)
        if not rows:
            return
        self._store_at[side] = clamp(self._step_index(self._store_at[side], len(rows)), 0, len(rows) - 1)
        self._store_top[side] = scroll_into_view(self._store_top[side], self._store_at[side], len(rows))
        if clicked or self._input.pressed("confirm"):
            self._store_move(side, rows[self._store_at[side]])

    def _store_move(self, side, item):
        """Moves one of `item` across: into the store from your pack, or back."""
        p = self.player
        if item.kind == "spell":
            moved = (stash.deposit_spell if side == "carried" else stash.withdraw_spell)(p, item.spell)
        else:
            moved = (stash.deposit if side == "carried" else stash.withdraw)(p, item.id)
        if not moved:
            return
        self.sfx("pickup", 0.4)
        self.message(f"Stored {{{item.name}}}." if side == "carried" else f"Took {{{item.name}}}.")

    # --- pause / death / ending ----------------------------------------------------

    def _open_pause(self):
        self.scene = "pause"
        self._menu_index = 0
        self._mouse_look(False)

    def _update_pause(self):
        if self._back():
            return self._enter_play()
        self._menu_nav(len(PAUSE_OPTIONS))
        clicked = self._menu_pointer(lambda px, py: list_row_at(*PAUSE_LIST, len(PAUSE_OPTIONS), px, py))
        if not (clicked or self._input.pressed("confirm")):
            return
        choice = PAUSE_OPTIONS[self._menu_index]
        if choice == "Resume":
            self._enter_play()
        elif choice == "Options":
            self._open_options()
        elif choice == "Controls":
            self._open_controls()
        elif choice == "Return to Title":
            self.show_title()
        elif choice == "Quit":
            self._running = False

    def _open_controls(self):
        """Controls reference, opened from the title or pause menu; returns to it on cancel."""
        self._controls_from = self.scene
        self._back_index = self._menu_index
        self._menu_top = 0
        self.scene = "controls"

    def _leave_submenu(self):
        self.scene = self._controls_from
        self._menu_index = self._back_index

    def _update_controls(self):
        if self._back() or self._advance():
            return self._leave_submenu()
        wheel = self._input.wheel()
        step = (self._input.pressed("down") or wheel < 0) - (self._input.pressed("up") or wheel > 0)
        if self._input.down("down") or self._input.down("up"):
            self._scroll_hold += 1
            if self._scroll_hold > 15 and self._scroll_hold % 4 == 0:  # held: keep scrolling
                step = 1 if self._input.down("down") else -1
        else:
            self._scroll_hold = 0
        top = max(len(CONTROLS) - CONTROLS_ROWS, 0)
        self._menu_top = clamp(self._menu_top + step, 0, top)

    def _draw_submenu_backdrop(self):
        if self._controls_from == "pause":
            ui.hud(self)
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))

    def _draw_controls(self):
        self._draw_submenu_backdrop()
        ui.list_menu(
            "Controls",
            *CONTROLS_LIST,
            CONTROLS,
            -1,
            footer="Up Down / Wheel: scroll    Esc: back",
            first=self._menu_top,
            visible=CONTROLS_ROWS,
        )

    # --- options -------------------------------------------------------------------

    def _open_options(self):
        """Sound on or off and its volume, from the title or pause menu."""
        self._controls_from = self.scene
        self._back_index = self._menu_index
        self._menu_index = 0
        self.scene = "options"

    def _option_rows(self):
        st = self.settings
        return [
            ("Sound effects", "On" if st.sound else "Off"),
            ("Volume", f"< {st.percent}% >", not st.sound),
            ("Back",),
        ]

    def _update_options(self):
        if self._back():
            return self._leave_submenu()
        rows = self._option_rows()
        self._menu_nav(len(rows))
        clicked = self._menu_pointer(lambda px, py: list_row_at(*OPTIONS_LIST, len(rows), px, py))
        chosen = clicked or self._input.pressed("confirm")
        left, right = self._input.pressed("tab_prev"), self._input.pressed("tab_next")
        st = self.settings
        row = rows[self._menu_index][0]
        if row == "Back":
            if chosen:
                self._leave_submenu()
            return
        if row == "Sound effects" and (chosen or left or right):
            st.toggle_sound()
        elif row == "Volume" and (chosen or left or right):
            st.step_volume(-1 if left else 1, wrap=chosen)
        else:
            return
        st.save()
        self._audio.set_volume(st.gain)
        self.sfx("pickup", 0.6)  # a taste of the new volume

    def _draw_options(self):
        self._draw_submenu_backdrop()
        ui.list_menu("Options", *OPTIONS_LIST, self._option_rows(), self._menu_index, footer="A D: change")

    def _update_dead(self, dt):
        self._dead_t += dt
        self.world.update(dt)
        if not (self._dead_t > 1.5 and self._advance()):
            return
        if not self._wake_at_shrine():
            self.show_title()

    def _wake_at_shrine(self):
        """Death keeps everything you found: inventory, gold, level, keys, sigils and opened chests
        stay yours. You wake at the last shrine you prayed at, and only the fallen return (a living
        boss at full strength). False when there is no shrine to wake at."""
        spot = self._saves.load_spot()
        if not spot:
            return False
        map_name, x, z, yaw = spot
        if self.world:
            self.world.mist_arenas()  # the boss's door gives way to fog
        self.player.revive()
        self.messages.clear()
        self.area_title = None
        self._load_world(map_name)
        self.player.place(*beside_shrine(self.world.map, x, z, yaw), self.world.map)
        self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
        self._enter_play()
        self.message("You wake beside the shrine.")
        for line in self._remnant_news:
            self.message(line)
        self._remnant_news = []
        return True

    def finish_game(self):
        for item_id in relics.ENDING_RELICS:
            self.player.inventory.remove(item_id)
        self.flags.add("ending")
        self._audio.play("bell")
        self.scene = "ending"
        self._ending_t = 0.0
        self._mouse_look(False)

    def _update_ending(self):
        self._ending_t += pr.get_frame_time()
        if self._ending_t > 2 and self._advance():
            self.show_title()

    # --- rendering ---------------------------------------------------------------

    def render(self):
        if self.scene in ("menu", "shop", "repair", "storage"):
            self._render_preview(self._selected_item())
        pr.begin_texture_mode(self._target)
        meta = self.world.meta
        fog, fog_range = darkness.fog_for(
            meta.get("fog", [0, 0, 0]),
            meta.get("fog_range", [4, 30]),
            self._dark_k or 0.0,
            veil=self.player.veil_t > 0,
            lumen=self.player.lumen_t > 0,
        )
        pr.clear_background(ui.color(*(rround(c * 255) for c in fog)))
        self._render_world(fog, fog_range)
        self._render_ui()
        pr.end_texture_mode()

        pr.begin_drawing()
        pr.clear_background(pr.BLACK)
        sw = pr.get_screen_width()
        sh = pr.get_screen_height()
        scale = min(sw / W, sh / H)
        dw = W * scale
        dh = H * scale
        pr.draw_texture_pro(
            self._target.texture,
            pr.Rectangle(0, 0, W, -H),
            pr.Rectangle((sw - dw) / 2, (sh - dh) / 2, dw, dh),
            pr.Vector2(0, 0),
            0,
            pr.WHITE,
        )
        pr.end_drawing()

    def _render_world(self, fog, fog_range):
        self._setup_camera()
        meta = self.world.meta
        gpu = self.gpu
        gpu.set_vec2("snapRes", (W // 2, H // 2))
        gpu.set_vec3("fogColor", fog)
        gpu.set_vec2("fogRange", fog_range)
        radius, torch = darkness.player_light(
            meta.get("torch", [0, 0, 0, 0]),
            self._dark_k or 0.0,
            self.player.lumen_t > 0,
            self.player.inventory.carried_light(),
        )
        gpu.set_vec3("torchColor", torch)
        gpu.set_float("torchRadius", radius)

        pr.begin_mode_3d(self._camera)
        cam = self._camera.position
        dark = self._dark_k or 0.0
        veil = self.player.veil_t > 0
        self._sky.draw(meta, (cam.x, cam.y, cam.z), fog, fog_range, dark, veil, self._time)
        self.world.view.draw(self._rig, gpu, fog_range, dark, veil)
        pr.end_mode_3d()

        if self.scene not in ("play", "dialogue", "menu", "shop", "rest", "shrine") or not self.player.alive:
            return
        p = self.player
        pr.begin_mode_3d(self._view_camera)
        # The viewmodel must draw over the world, yet sort within itself (fingers round a grip, in front
        # of it and behind): wipe the depth buffer only, the colour mask keeping the world's pixels.
        rl.rlColorMask(False, False, False, False)
        rl.rlClearScreenBuffers()
        rl.rlColorMask(True, True, True, True)
        gpu.set_float("isModel", 1.0)
        gpu.model_light([min(c + 0.15, 1.4) for c in self.world.view.builder.light_at(p.x, p.eye_y, p.z)])
        bob = math.sin(p.bob_t) * 0.02
        models.weapon_view(self._rig, p, bob, self._time, self._view_blends)
        pr.end_mode_3d()

    def _selected_item(self):
        """The highlighted row of the inventory, shop, mending or store list, or None."""
        if self.scene == "storage":
            items, i = self._store_rows(self._store_side), self._store_at[self._store_side]
            return items[i] if i < len(items) else None
        if self.scene == "repair":
            items = self._mendable()
        else:
            items = self._menu_items() if self.scene == "menu" else self._shop_stock()
        return items[self._menu_index] if self._menu_index < len(items) else None

    def _render_preview(self, item):
        """Spins `item` in its own little PS1-styled viewport."""
        gpu = self.gpu
        pr.begin_texture_mode(self._preview)
        pr.clear_background(ui.color(16, 12, 9))
        if item:
            gpu.set_vec2("snapRes", (PREVIEW // 2, PREVIEW // 2))
            gpu.set_vec3("fogColor", (0, 0, 0))
            gpu.set_vec2("fogRange", (50, 60))
            gpu.set_vec3("torchColor", (0, 0, 0))
            gpu.set_float("torchRadius", 0)
            pr.begin_mode_3d(self._preview_camera)
            gpu.set_float("isModel", 1.0)
            gpu.model_light((1.25, 1.15, 1.0))
            with self._rig.at(0, math.sin(self._time * 2) * 0.04, 0, ry=self._time * 1.2):
                models.item(self._rig, item.id, self._time)
            pr.end_mode_3d()
        pr.end_texture_mode()

    def _setup_camera(self):
        cam = self._camera
        if self.scene in ("title", "slots") or (
            self.scene in ("controls", "options") and self._controls_from == "title"
        ):
            a = self._time * 0.08
            cx, cz = TileMap.center(*TITLE_ORBIT)
            ex = cx + math.cos(a) * 11
            ez = cz + math.sin(a) * 11
            self.player.x = ex
            self.player.z = ez
            cam.position = (ex, 5.0, ez)
            cam.target = (cx, 3.2, cz)
            return
        p = self.player
        fx, fz = p.forward()
        cp = math.cos(p.pitch)
        eye = p.eye_y
        cam.position = (p.x, eye, p.z)
        dip = p.hitstop_t * 0.8  # a blow that bites jolts the view down a touch
        cam.target = (p.x + fx * cp, eye + math.sin(p.pitch) - dip, p.z + fz * cp)

    def _render_ui(self):
        s = self.scene
        if s == "title":
            self._draw_title()
        elif s == "slots":
            self._draw_slots()
        elif s == "play":
            ui.hud(self)
        elif s == "dialogue":
            ui.hud(self)
            d = self._dialogue
            if d["page"] < len(d["lines"]):
                ui.dialogue(d["speaker"], d["lines"][d["page"]], d["page"], len(d["lines"]))
        elif s == "menu":
            self._draw_menu()
        elif s == "shop":
            self._draw_shop()
        elif s == "repair":
            self._draw_repair()
        elif s == "shrine":
            ui.hud(self)
            pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 90))
            ui.list_menu("Shrine", *SHRINE_LIST, [(o,) for o in SHRINE_OPTIONS], self._menu_index)
        elif s == "storage":
            self._draw_storage()
        elif s == "rest":
            ui.hud(self)
            ui.rest_fog(self._rest, self._time)
        elif s == "pause":
            ui.hud(self)
            pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
            ui.list_menu("Paused", *PAUSE_LIST, [(o,) for o in PAUSE_OPTIONS], self._menu_index)
        elif s == "controls":
            self._draw_controls()
        elif s == "options":
            self._draw_options()
        elif s == "dead":
            self._draw_dead()
        elif s == "ending":
            self._draw_ending()

    def _draw_title(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 90))
        ui.big("ASHEN VAULT", W // 2, 50, ui.HIGHLIGHT, px=3)
        ui.text_centered("beneath the silent bell", W // 2, 80, ui.DIM)
        for i, o in enumerate(self._title_options()):
            sel = i == self._menu_index
            ui.text_centered(
                f"> {o} <" if sel else o, W // 2, TITLE_Y + i * TITLE_STEP, ui.HIGHLIGHT if sel else ui.TEXT
            )

    def _draw_menu(self):
        items = self._menu_items()
        rows = [
            (
                f"{i.name}{self._equipped_mark(i)}",
                self._menu_right(i),
                i.level > self.player.stats.level,
            )
            for i in items
        ]
        ui.list_menu(
            "", *MENU_LIST, rows, self._menu_index, first=self._menu_top, visible=LIST_ROWS, height=COLUMN_H
        )
        self._draw_tabs()
        item = items[self._menu_index] if self._menu_index < len(items) else None
        if self._menu_tab == "Items":
            self._draw_quick()
        else:
            self._draw_equipped()
        self._draw_stats(self._changes(item) if item else {})
        self._draw_item_panel(
            item,
            self._item_detail(item) if item else "",
            "A/D: tab   Enter: use or set quick slot"
            if self._menu_tab == "Items"
            else "A/D: tab   1/2: Primary/Secondary   Enter: choose",
        )
        self._draw_marks(self._gear_marks(item) if item else [])
        if self._pick:
            x, y, w = PICK_LIST
            rows = [(label,) for label, _ in self._pick_options()]
            kind = self._pick.kind
            title = {"repair": "Mend which?", "consumable": self._pick.name}.get(
                kind, f"Equip {self._pick.name}"
            )
            ui.list_menu(title, *PICK_LIST, rows, self._pick_index)
            for i, (_, slot) in enumerate(self._pick_options()):
                ry = y + ROW_TOP + i * ROW_H
                if kind == "consumable":
                    held = self.player.quick_slots[slot] if isinstance(slot, int) else None
                    if held:  # what the quick slot holds now, by its wheel glyph
                        ui.item_icon(held, x + w - 9, ry + 4, pr.get_time())
                elif slot is not None and kind != "repair":
                    ui.mini_mouse(x + w - 11, ry, belongings.SLOT_BUTTONS[slot])

    def _changes(self, item):
        """What the highlighted row would change: in the slot chooser, putting it in the hovered slot
        (or taking it off, on Unequip); otherwise equipping it, or taking it off if it is equipped."""
        inv = self.player.inventory
        spell = self.player.current_spell()
        spell_id = spell.id if spell else None
        kw = {"magic": self.player.stats.magic, "spell": spell_id}
        if self._pick and self._pick.kind in ("repair", "consumable"):
            return {}
        if self._pick:
            opts = self._pick_options()
            _, slot = opts[min(self._pick_index, len(opts) - 1)]
            if slot is None:
                return compare.preview(inv, self._pick, unequip=True, **kw)
            return compare.preview(inv, self._pick, None if self._pick.two_handed else slot, **kw)
        worn = inv.equipped(compare.held(item)) and (item.kind != "spell" or item.spell == spell_id)
        if worn and item.kind in ("weapon", "shield", "armor", "spell"):
            return compare.preview(inv, item, unequip=True, **kw)
        return compare.preview(inv, item, **kw)

    def _draw_tabs(self):
        """The Belongings tabs along the list's title line, the open one lit and underlined."""
        _x, y, _w = MENU_LIST
        for tab, (lo, hi) in zip(belongings.TABS, self._tab_spans(), strict=True):
            on = tab == self._menu_tab
            ui.text(tab, lo, y + 5, ui.HIGHLIGHT if on else ui.DIM)
            if on:
                pr.draw_line(lo, y + 14, hi, y + 14, ui.HIGHLIGHT)

    def _menu_right(self, item):
        """A Belongings row's right column: how many, a spell's MP cost, or the level it needs."""
        if item.kind in ("consumable", "repair"):
            return f"x{self.player.inventory.count(item.id)}"
        if item.kind == "spell":
            return f"{Spells.get(item.spell).cost} MP"
        return self._level_mark(item)

    def _draw_equipped(self):
        """What each slot holds: a mini mouse with its button lit for Primary and Secondary."""
        x, y, w = EQUIPPED_PANEL
        ui.panel(x, y, w, EQUIPPED_H)
        ui.text("Equipped", x + 8, y + 5, ui.HIGHLIGHT)
        for i, (button, slot, name) in enumerate(
            belongings.equipped_rows(self.player.inventory, self._spell_name())
        ):
            ry = y + ROW_TOP + i * ROW_H
            if button:
                ui.mini_mouse(x + 9, ry, button)
            else:
                ui.tiny(slot.upper(), x + 6, ry + 2, ui.DIM)
            ui.text(name, x + 30, ry, ui.DIM if name.startswith("(") or name == "-" else ui.TEXT)

    def _draw_quick(self):
        """The Items tab's Quick panel, in Equipped's place: what each quick slot holds, the one the
        mouse wheel has selected lit, with how many you carry."""
        x, y, w = EQUIPPED_PANEL
        ui.panel(x, y, w, EQUIPPED_H)
        ui.text("Quick", x + 8, y + 5, ui.HIGHLIGHT)
        inv = self.player.inventory
        for num, item, selected in belongings.quick_rows(self.player):
            ry = y + ROW_TOP + (num - 1) * ROW_H
            ui.tiny(f"Q{num}", x + 6, ry + 2, ui.HIGHLIGHT if selected else ui.DIM)
            if item is None:
                ui.text("(empty)", x + 30, ry, ui.DIM)
                continue
            n = inv.count(item.id)
            ui.item_icon(item.id, x + 22, ry + 4, pr.get_time(), 255 if n else 90)
            ui.text(item.name, x + 30, ry, ui.HIGHLIGHT if selected else ui.TEXT if n else ui.DIM)
            count = f"x{n}"
            ui.text(count, x + w - 8 - ui.measure(count), ry, ui.TEXT if n else ui.DIM)

    def _draw_stats(self, changes=None):
        """Level, vitals and attributes in two columns, then your load and EXP across the bottom.
        `changes` ({stat: (now, then)}, see ui/compare.py) shows what equipping the highlighted item
        would do: "8>12", the new value green when it is better and red when it is worse."""
        changes = changes or {}
        s = self.player.stats
        inv = self.player.inventory
        x, y, w = STATS_PANEL
        ui.panel(x, y, w, STATS_H)
        spell = self.player.current_spell()
        nums = compare.numbers(inv, s.magic, spell.id if spell else None)
        pairs = [
            (("Lv", s.level), ("Gold", inv.gold)),
            (("HP", f"{s.hp}/{s.max_hp}"), ("MP", f"{s.mp}/{s.max_mp}")),
            (("STR", s.strength), ("MAG", s.magic)),
            (("ATK", nums["ATK"]), ("DEF", nums["DEF"])),
            (("SPL", nums["SPL"]), ("Block", nums["Block"])),
        ]
        top = y + 5  # on the title line of every other panel
        half = (w - 16) // 2
        for i, row in enumerate(pairs):
            for j, (k, v) in enumerate(row):
                cx = x + 8 + j * (half + 4)
                ui.text(k, cx, top + i * STATS_ROW, ui.DIM)
                self._stat_value(k, v, changes.get(k), cx + half - 4, top + i * STATS_ROW)
        ly = top + 5 * STATS_ROW
        cap = burden.capacity(s.strength)
        load = changes.get("Load", (nums["Load"], nums["Load"]))[1]
        tier = burden.tier(load, cap)
        heavy = tier.name in ("Heavy", "Overloaded")
        ui.text("Load", x + 8, ly, ui.DIM)
        name = f" {tier.name}"
        right = x + w - 8 - ui.measure(name)
        ui.text(name, right, ly, ui.color(220, 90, 80) if heavy else ui.DIM)
        self._stat_value("Load", nums["Load"], changes.get("Load"), right, ly, f"/{compare.fmt(cap)}")
        exp = f"{s.exp}/{s.next_level_exp}"
        ui.text("EXP", x + 8, top + 6 * STATS_ROW, ui.DIM)
        ui.text(exp, x + w - 8 - ui.measure(exp), top + 6 * STATS_ROW)

    def _stat_value(self, stat, value, change, right, y, suffix=""):
        """Draws a stat right-aligned to `right`: its value, or "now>then" with `then` coloured by
        whether equipping makes it better (green) or worse (red)."""
        if change is None:
            v = (compare.fmt(value) if stat == "Load" else str(value)) + suffix
            ui.text(v, right - ui.measure(v), y)
            return
        now, then = (compare.fmt(n) for n in change)
        tail = f"{then}{suffix}"
        x = right - ui.measure(tail) - ui.measure(now) - 7
        ui.text(now, x, y, ui.DIM)
        x += ui.measure(now) + 2
        for i in range(3):  # a 3 px arrow between the two values
            pr.draw_line(x + i, y + 2 + i, x + i, y + 7 - i, ui.DIM)
        ui.text(tail, x + 5, y, COMPARE_COLORS[compare.better(stat, *change)])

    def _equipped_mark(self, item):
        """Row suffix: which slots hold the item ([1], [2], [1+2]), [Worn] for armor, or the quick
        slot a consumable sits in ([Q2])."""
        if item.kind == "consumable":
            return belongings.quick_mark(self.player, item.id)
        spell = self.player.current_spell()
        return belongings.slot_mark(self.player.inventory, item, spell.id if spell else None)

    def _level_mark(self, item):
        return f"Lv{item.level}" if item.level > 1 else None

    def _gear_marks(self, item):
        """[(text, good)] beside an item's name: its durability (red once badly worn) and its weight."""
        inv = self.player.inventory
        marks = []
        if inv.max_durability(item.id) is not None:
            marks.append((f"Dur {self._wear_mark(item)}", -1 if inv.worn(item.id) else 0))
        return marks + self._weight_mark(item)

    def _draw_marks(self, marks):
        """Marks along the item panel's name line, right-aligned, the last one rightmost."""
        x = self._item_right()
        for text, good in reversed(marks):
            x -= ui.measure(text)
            ui.text(text, x, self._item_name_y(), COMPARE_COLORS[good] if good else ui.DIM)
            x -= 8

    @staticmethod
    def _weight_mark(item):
        """[("Wt N", 0)] for gear that adds to your load, else []."""
        return [(f"Wt {compare.fmt(item.mass)}", 0)] if item.mass else []

    @staticmethod
    def _item_inset():
        """The preview well's inset in the item panel: centred top to bottom, as far from the left."""
        return (ITEM_PANEL[3] - PREVIEW - 6) // 2

    def _item_text_x(self):
        return ITEM_PANEL[0] + 2 * self._item_inset() + PREVIEW + 6

    @staticmethod
    def _item_right():
        x, _y, w, _h = ITEM_PANEL
        return x + w - ui.PANEL_PAD

    def _item_name_y(self):
        return ITEM_PANEL[1] + self._item_inset() - ui.TEXT_DY  # the name's caps level with the well's top

    def _draw_item_panel(self, item, detail, footer):
        """Bottom panel shared by Belongings and the shop: spinning preview, name, details, description."""
        x, y, w, h = ITEM_PANEL
        ui.panel(x, y, w, h)
        inset = self._item_inset()
        tx, ty = self._item_text_x(), self._item_name_y()
        if item:
            well = PREVIEW + 6
            pr.draw_rectangle(x + inset, y + inset, well, well, pr.BLACK)
            pr.draw_texture_rec(
                self._preview.texture,
                pr.Rectangle(0, 0, PREVIEW, -PREVIEW),
                pr.Vector2(x + inset + 3, y + inset + 3),
                pr.WHITE,
            )
            pr.draw_rectangle_lines(x + inset, y + inset, well, well, ui.HUD_EDGE)
            ui.text(item.name, tx, ty, ui.HIGHLIGHT)
            ui.text(detail, tx, ty + 12, ui.DIM)
            lines = ui.wrap(item.desc, self._item_right() - tx)
            if item.kind == "weapon":
                moves = weapons.moveset(item)
                head = f"{moves[weapons.LIGHT].name} / Heavy: {moves[weapons.HEAVY].name}"
                if weapons.has_secret(item):
                    known = f"secret:{item.category}" in self.flags
                    head += f" / {moves[weapons.SECRET].name if known else '???'}"
                lines = [head, *lines]
            art = weapons.art(item) if item.kind == "weapon" else None
            if art:  # a weapon art takes its own line, in its colour
                lines.insert(1, f"Art: {art.name} ({art.mp} MP)")
            # Three lines sit 11 px apart; a fourth (a weapon with an art) packs them at the font's own.
            lines = lines[: 4 if art else 3]
            step, top = (11, ty + 25) if len(lines) <= 3 else (smallfont.LINE, ty + 23)
            for i, l in enumerate(lines):
                rgb = (240, 210, 90) if i == 0 and item.kind == "weapon" else None
                if art and i == 1:
                    rgb = art.rgb
                ui.text(l, tx, top + i * step, ui.color(*rgb) if rgb else ui.TEXT)
        msg = self.messages[-1] if self.messages else None
        fresh = msg is not None and msg[1] < 2.5
        # The footer's caps end level with the well's bottom.
        ui.text(
            msg[0] if fresh else footer, tx, y + h - inset - smallfont.HEIGHT, ui.TEXT if fresh else ui.DIM
        )

    def _item_detail(self, item):
        need = f"   Lv{item.level}" if item.level > 1 else ""
        if item.kind == "weapon":
            size = weapons.WEIGHT_NAMES[weapons.weight(item)]
            kind = f"{size} {weapons.CATEGORY_NAMES[item.category]}" + (" 2H" if item.two_handed else "")
            st = "/".join(  # light / heavy, in % of the ST bar
                str(rround(weapons.attack(item, k).stamina * 100)) for k in (weapons.LIGHT, weapons.HEAVY)
            )
            need = f"  Lv{item.level}" if item.level > 1 else ""
            return f"{kind}  ATK {item.power}  Rch {item.reach}  ST {st}{need}"
        if item.kind == "shield":
            return f"Shield   Block {rround(item.guard * 100)}%   Holds {item.stability}{need}"
        if item.kind == "armor":
            slot = "Gauntlets" if item.slot == "hands" else "Armor"
            return f"{slot}   DEF {item.power}{need}"
        if item.kind == "consumable":
            return f"Consumable   x{self.player.inventory.count(item.id)}"
        if item.kind == "scroll":
            spell = Spells.get(item.spell)
            return f"Scroll   {spell.name}   {spell.cost} MP"
        if item.kind == "spell":
            return f"Spell   {Spells.get(item.spell).cost} MP"
        if item.kind == "repair":
            return f"Repair   x{self.player.inventory.count(item.id)}"
        if item.kind == "service":
            n = len(self._mendable())
            return f"{n} piece{'s' if n != 1 else ''} to mend" if n else "Nothing needs mending"
        return "Key item"

    def _draw_shop(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        stock = self._shop_stock()
        gold = self.player.inventory.gold
        level = self.player.stats.level
        rows = [
            (i.name, None, not self._mendable())
            if i is MEND_ROW
            else (i.name, f"{f'Lv{i.level}  ' if i.level > level else ''}{i.price}g", i.price > gold)
            for i in stock
        ]
        title = f"{dialogue_data.SHOP_NAMES[self._shop_id]}  (you have {gold}g)"
        ui.list_menu(
            title,
            *SHOP_LIST,
            rows,
            self._menu_index,
            first=self._menu_top,
            visible=LIST_ROWS,
            height=COLUMN_H,
        )
        item = self._selected_item()
        priced = item and item is not MEND_ROW
        detail = (
            f"{self._item_detail(item)}   {item.price}g"
            if priced
            else self._item_detail(item)
            if item
            else ""
        )
        self._draw_item_panel(item, detail, "Enter/Click: buy   Esc/R-click: leave")
        if item:  # what wearing it would change, beside its name
            x = self._item_right()
            changes = compare.deltas(compare.preview(self.player.inventory, item))
            for text, good in reversed(changes or self._weight_mark(item)):
                x -= ui.measure(text)
                ui.text(text, x, self._item_name_y(), COMPARE_COLORS[good] if good else ui.DIM)
                x -= 8

    def _draw_repair(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        worn = self._mendable()
        gold = self.player.inventory.gold
        rows = []
        for i in worn:
            cost = self._repair_cost(i)
            rows.append((i.name, f"{self._wear_mark(i)}   {cost}g", cost > gold))
        ui.list_menu(
            f"Mend gear  (you have {gold}g)",
            *SHOP_LIST,
            rows,
            self._menu_index,
            first=self._menu_top,
            visible=LIST_ROWS,
            height=COLUMN_H,
        )
        item = self._selected_item()
        detail = f"{self._item_detail(item)}   {self._repair_cost(item)}g" if item else ""
        self._draw_item_panel(item, detail, "Enter/Click: mend   Esc/R-click: back")
        if item:
            self._draw_marks(self._gear_marks(item))

    def _draw_storage(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        for side, title in zip(STORE_SIDES, ("Carried", "Stored"), strict=True):
            items = self._store_rows(side)
            rows = []
            for i in items:
                n = self._store_count(side, i)
                mark = self._equipped_mark(i) if side == "carried" else ""
                rows.append((f"{i.name}{mark}", f"x{n}" if n > 1 else None))
            on = side == self._store_side
            ui.list_menu(
                title,
                *self._store_list(side),
                rows,
                self._store_at[side] if on else -1,
                first=self._store_top[side],
                visible=LIST_ROWS,
                height=COLUMN_H,
            )
        item = self._selected_item()
        verb = "store" if self._store_side == "carried" else "take"
        self._draw_item_panel(
            item, self._item_detail(item) if item else "", f"A/D: side   Enter/Click: {verb}   Esc: back"
        )
        if item:
            self._draw_marks(self._gear_marks(item))

    def _draw_dead(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(40, 0, 0, rround(min(self._dead_t * 120, 200))))
        ui.big("YOU HAVE FALLEN", W // 2, 96, ui.color(220, 80, 70), px=2)
        if self._dead_t > 1.5:
            hint = (
                "Press Enter or click to wake at the last shrine" if self._saves.exists() else "Press Enter"
            )
            ui.text_centered(hint, W // 2, 130, ui.DIM)

    def _draw_ending(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, rround(min(self._ending_t * 100, 230))))
        for i, l in enumerate(ENDING):
            ui.text_centered(l, W // 2, 70 + i * 14)
        if self._ending_t > 2:
            ui.text_centered("Press Enter", W // 2, 190, ui.DIM)
