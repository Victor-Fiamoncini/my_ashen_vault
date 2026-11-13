import math
import random

import pyray as pr
import raylib as rl
from raylib import ffi

from ashen_vault import dialogue as dialogue_data
from ashen_vault.ai.enemy import Enemy
from ashen_vault.audio.synth import Audio
from ashen_vault.input import CONTROLS, Input
from ashen_vault.player import weapons
from ashen_vault.player.combat import Combat
from ashen_vault.player.inventory import LEFT, PRIMARY, RIGHT, SECONDARY, SLOT_ALIASES, SLOT_NAMES, SPELL
from ashen_vault.player.items import Item, Items
from ashen_vault.player.player import Player
from ashen_vault.player.spells import Spells
from ashen_vault.render import models
from ashen_vault.render.gpu import Gpu
from ashen_vault.render.rig import Rig
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.screen import (
    FOV,
    LIST_ROWS,
    PREVIEW,
    ROW_H,
    ROW_TOP,
    H,
    W,
    centered_row_at,
    list_row_at,
    scroll_into_view,
)
from ashen_vault.ui import belongings
from ashen_vault.ui import hud as ui
from ashen_vault.util import clamp, rround
from ashen_vault.world import darkness, doors, elements, relics
from ashen_vault.world.rest import RestSequence
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World

KIND_ORDER = ["weapon", "shield", "armor", "spell", "consumable", "scroll", "key"]
HAND_BUTTON = {RIGHT: "attack", LEFT: "cast"}  # input actions: left mouse = Primary, right = Secondary
PULSE_DELAY = 0.3  # seconds between the blows of a multi-pulse attack (the hammer's Aftershock)
PULSE_DAMAGE = 0.6
PAUSE_OPTIONS = ["Resume", "Controls", "Return to Title", "Quit"]
# (x, y, width) of each ui.list_menu panel, shared by drawing and mouse hit-testing.
PAUSE_LIST = (100, 80, 120)
MENU_LIST = (6, 6, 170)
SHOP_LIST = (6, 6, 308)
PICK_LIST = (24, 60, 190)  # the "which slot?" chooser over Belongings
EQUIPPED_PANEL = (182, 6, 132)  # Belongings: what Primary, Secondary, Body and Hands hold
STATS_PANEL = (182, 80, 132)
TITLE_Y, TITLE_STEP = 140, 14
ENDING = [
    "The bell of Harrowmere rings again.",
    "Its note rolls down the well into the drowned halls",
    "and through the roots of the cave in the green hollow.",
    "The old keep and the green hollow sleep once more.",
    "",
    "Thank you for playing the Ashen Vault demo.",
]


def _camera(pos, target, fovy):
    return pr.Camera3D(pos, target, (0, 1, 0), fovy, pr.CAMERA_PERSPECTIVE)


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
        self._audio = Audio()
        self._input = Input(self.opts.get("script"))
        self._saves = SaveSystem()
        self._camera = _camera((0, 0, 0), (1, 0, 0), FOV)
        self._view_camera = _camera((0, 0, 0), (1, 0, 0), 55)
        self._preview_camera = _camera((2.6, 0.5, 0), (0, 0, 0), 40)
        self.messages = []
        self.flags = set()
        self.player = Player()
        self.world = None
        self.scene = None
        self._menu_index = 0
        self._time = 0.0
        self._frames = 0
        self._running = True
        self._mouse_captured = None
        self._cursor_at = None  # where the free cursor was when mouse look was last released
        self._look_skip = 0  # frames of mouse delta to ignore after recapturing the cursor
        self._rest = None
        self._hit_done = False
        self._held = {"attack": False, "cast": False}  # hand buttons held last frame (tap / hold)
        self._spent = {"attack": False, "cast": False}  # this press already queued a quick strike
        self._pulse = None  # [seconds left, attack, weapon] of a pending second shockwave
        self._menu_top = 0  # first row shown by a scrolling list
        self._pick = None  # item waiting for a hand in the Belongings chooser
        self._pick_index = 0
        self._shop_id = "pell"
        self._step_phase = 0.0
        self._dialogue = None
        self._controls_from = None
        self._dead_t = 0.0
        self._ending_t = 0.0
        self._dark_k = None  # how dark it looks where you stand (eased, so cave mouths don't pop)
        if self.opts.get("map"):
            self.new_game(self.opts["map"], at=self.opts.get("at"))
        else:
            self.show_title()

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
        enemies = ",".join(f"{e.type.id}:{e.state}:{e.hp}" for e in self.world.enemies) if self.world else ""
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
        if self.world:
            target = self.world.map.tile_at(self.player.x, self.player.z).dark
            self._dark_k = target if self._dark_k is None else darkness.ease_toward(self._dark_k, target, dt)
        handler = {
            "title": lambda: self._update_title(),
            "play": lambda: self._update_play(dt),
            "dialogue": lambda: self._update_dialogue(),
            "menu": lambda: self._update_menu(),
            "shop": lambda: self._update_shop(),
            "pause": lambda: self._update_pause(),
            "rest": lambda: self._update_rest(dt),
            "controls": lambda: self._update_controls(),
            "dead": lambda: self._update_dead(dt),
            "ending": lambda: self._update_ending(),
        }.get(self.scene)
        if handler:
            handler()

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
        if self._saves.exists():
            return ["Continue", "New Game", "Controls", "Quit"]
        return ["New Game", "Controls", "Quit"]

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
            self.continue_game()
        elif choice == "New Game":
            self.new_game("harrowmere")
            self._audio.play("bell", volume=0.5)
            self.message("Harrowmere. The bell has gone quiet.")
        elif choice == "Controls":
            self._open_controls()
        elif choice == "Quit":
            self._running = False

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

    def new_game(self, map_name, at=None):
        self.flags = set()
        self.player = Player()
        self.messages.clear()
        self._load_world(map_name)
        x, z, yaw = self._spot(at) if at else self.world.start_position()
        self.player.place(x, z, yaw, self.world.map)
        self._debug_setup()
        self._enter_play()

    def _debug_setup(self):
        """--level and --equip (slot=id pairs) for smoke runs; gear is added to the pack first, and
        `spell:<id>` teaches that spell and readies it."""
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

    def continue_game(self):
        loaded = self._saves.load()
        if not loaded:
            return self.message("The save file could not be read.")
        map_name, player, flags = loaded
        self.player = player
        self.flags = flags
        self.messages.clear()
        self._load_world(map_name)
        self.player.place(player.x, player.z, player.yaw, self.world.map)
        self._enter_play()
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
        self.message(self.world.meta.get("name", map_name))

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
        moved = p.walk(
            self.world.map,
            self._axis("forward", "back"),
            self._axis("strafe_r", "strafe_l"),
            dt,
            blocked=self.world.blocker,
            sprint=inp.down("sprint"),
            floating=self.world.terrain.floating,
            ground=self.world.terrain.floor,
        )
        self.world.update_terrain(dt)
        under = self.world.terrain.under
        p.settle(self.world.map, dt, floor=self.world.player_floor(), snap=under is not None and under.moving)
        if moved:
            self._footstep()

        p.update_timers(dt)
        self._update_hands(dt)
        if p.swinging and not self._hit_done and p.swing_t >= p.swing_hit_at:
            self._resolve_swing()
        if self._hit_done and p.chain_quick():
            self._hit_done = False
            self.sfx("swing", 0.5)
        self._update_pulse(dt)
        wheel = inp.wheel()
        if wheel:
            self._cycle_quick(-1 if wheel > 0 else 1)  # wheel down = next
        if inp.pressed("quick"):
            self._quick_use(p.quick)
        if inp.pressed("interact"):
            self._interact()

        self.world.update(dt)
        if not p.alive:
            self._dead_t = 0.0
            self.scene = "dead"

    def _axis(self, pos, neg):
        return (1 if self._input.down(pos) else 0) - (1 if self._input.down(neg) else 0)

    def _footstep(self):
        phase = math.floor(self.player.bob_t / math.pi)
        if phase == self._step_phase:
            return
        self._step_phase = phase
        self.sfx("step", 0.35)

    def _update_hands(self, dt):
        """Each mouse button works its slot (left button = Primary, right = Secondary): a weapon swings
        (tap light, hold heavy, click again mid-swing for a quick strike), a shield is raised while
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
        if pressed and p.swinging and p.queue_quick(hand):
            self._spent[action] = True  # this click was the quick follow-up, not a new swing
            self._held[action] = False
            return
        if down:
            if not self._spent[action] and not p.swinging and (p.charge_hand == hand or p.charge_t == 0):
                p.charge_hand = hand
                p.charge_t += dt
            self._held[action] = True
            return
        released, self._held[action] = self._held[action], False
        if self._spent[action]:
            self._spent[action] = False
            return
        if not (released or pressed):
            if p.charge_hand == hand:
                p.charge_t = 0.0
            return
        heavy = p.charge_hand == hand and p.charge_t >= weapons.CHARGE_TIME
        self._swing(hand, weapons.HEAVY if heavy else weapons.LIGHT)
        if p.charge_hand == hand:
            p.charge_t = 0.0

    def _swing(self, hand, kind):
        p = self.player
        if p.swinging:
            return
        if p.stamina.exhausted:
            self.message("Too winded to swing.")
            return
        a = p.start_swing(hand, kind)
        if not a:
            return
        self._hit_done = False
        if a.kind == weapons.SECRET:
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
        if weapon.category != "fists":
            return weapon.power
        gloves = self.player.inventory.hands_item()
        return weapon.power + 2 * ((gloves.power or 0) if gloves else 0)

    def _resolve_swing(self):
        self._hit_done = True
        p = self.player
        weapon = p.swing_weapon
        a = p.attack
        if a.lunge:
            p.nudge(self.world.map, a.lunge, blocked=self.world.blocker)
        for prop in self.world.strike_props(weapon.reach * a.reach, a.cone):
            self._break(prop)
        targets = self._strike(weapon, a)
        if targets:
            p.land_hit(targets[0])
        if a.pulses > 1:
            self._pulse = [PULSE_DELAY, a, weapon, a.pulses - 1]

    def _strike(self, weapon, a, mult=1.0):
        """Deals one blow of attack `a` to everything in reach; returns who it hit."""
        p = self.player
        targets = self.world.melee_targets(weapon.reach * a.reach, a.cone, a.targets)
        if not targets:
            return targets
        self.sfx("hit")
        for target in targets:
            back = target.hit_mult(p.x, p.z)
            element = weapon.element
            dmg = Combat.damage(
                base=self._swing_power(weapon),
                strength=p.stats.strength,
                gauge=p.swing_power,
                defense=4 if target.type.boss and not a.pierce_def else 0,
                mult=a.damage * back * mult * elements.mult(target.type, element),
            )
            if back > 1:
                self.message(f"You strike the {target.name}'s weak spot!")
            jolt = elements.staggers(target.type, element)
            self.damage_enemy(target, dmg, 99.0 if jolt else a.poise * back)
            if elements.burns(target.type, element) and target.alive:
                target.afflict("burn", *elements.WEAPON_BURN)
            if a.pull and target.alive:
                self._pull(target, a.pull)
        return targets

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
        """The hammer's Aftershock: the ground answers the slam a moment later."""
        if not self._pulse:
            return
        self._pulse[0] -= dt
        if self._pulse[0] > 0:
            return
        _, a, weapon, left = self._pulse
        self._pulse = [PULSE_DELAY, a, weapon, left - 1] if left > 1 else None
        self.sfx("heavy", 0.6)
        self._strike(weapon, a, PULSE_DAMAGE)

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
            self.sfx("door", 0.8)
            self.message("The wall was an illusion!")

    def damage_enemy(self, enemy, dmg, poise_mult=1.0, stagger=True):
        if not enemy.take_hit(dmg, poise_mult, stagger=stagger):
            return
        self.sfx("enemy_die")
        t = enemy.type
        if enemy.key:
            self.flags.add(enemy.key)
        self.world.drop_enemy_loot(enemy)
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
        if t.brood:
            for e in self.world.enemies:
                if e.type.id == t.brood:
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
        self.player.stats.hurt(dmg)
        self.player.hurt_t = 0.4
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
        self.sfx("spell")
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

    def _cycle_quick(self, step=1):
        item = self.player.cycle_quick(step)
        if item:
            self.message(f"{item.name} x{self.player.inventory.count(item.id)}")

    def _quick_use(self, id_):
        if not self.player.inventory.has(id_):
            return self.message(f"You have no {Items.get(id_).name}.")
        self._use_item(Items.get(id_))

    def _use_item(self, item):
        inv = self.player.inventory
        if item.kind == "consumable":
            inv.remove(item.id)
            if item.heal:
                self.player.stats.heal(item.heal)
            if item.mana:
                self.player.stats.restore_mp(item.mana)
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
        elif item.kind == "spell":
            self.player.equip_spell(item.spell)
            self.sfx("spell", 0.4)
            if inv.equipped(SPELL):
                self.message(f"{Spells.get(item.spell).name} is ready.")
            else:
                self._open_pick(item)
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
            "brazier": "[E] Look at the cold brazier",
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
        elif k == "door":
            self._open_door(prop)
        elif k == "lever":
            self.world.pull_lever(prop)
            self.sfx("door")
            if prop.props.get("model") == "wood":
                self.message("Ropes groan through the timbers, and something heavy shifts.")
            else:
                self.message("Somewhere chains rattle, and iron grinds against stone.")
        elif k in ("brazier", "bonfire"):
            self.message("Cold ashes. It wants a flame.")
        elif k == "save_statue":
            self._start_rest()
        elif k == "altar":
            item = Items.get(self.world.take_from_altar(prop))
            self.player.inventory.add(item.id)
            self.sfx("bell", 0.7)
            self.message(f"Obtained {{{item.name}}}.")
            self.message("The statue's eyes gutter out as you lift the key.")
            self.message("Somewhere above, a great door awaits.")
        elif k == "iron_maiden":
            self._enter_maiden(prop)
        elif k == "frog_idol":
            self._pat_frog(prop)
        elif k == "exit":
            self._travel(prop.props["map"], prop.props["at"])
        elif k == "pickup":
            item = Items.get(prop.props["item"])
            self.player.inventory.add(item.id)
            self.flags.add(prop.key)
            relics.mark_taken(item.id, self.flags)
            self.world.remove_prop(prop)
            self.sfx("pickup")
            self.message(f"Obtained {{{item.name}}}.")

    # --- shrine rest ------------------------------------------------------------------

    def _start_rest(self):
        """Kneel at the shrine: ember fog rises over the screen, and while it hides everything the
        shrine restores you, wakes the fallen and records the journey."""
        self._rest = RestSequence()
        self.scene = "rest"
        self.player.charge_t = 0.0
        self._held = {"attack": False, "cast": False}
        self.player.guarding = False
        self.sfx("save")

    def _update_rest(self, dt):
        if self._rest.update(dt):
            self.player.revive()
            self.world.respawn_enemies()
            self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
        if self._rest.done:
            self._rest = None
            self.scene = "play"
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
        if item:
            self.player.inventory.add(item, count)
        self.player.inventory.gold += gold
        parts = []
        if item:
            parts.append(f"{{{Items.get(item).name}{f' x{count}' if count > 1 else ''}}}")
        if gold > 0:
            parts.append(f"{{{gold} gold}}")
        self.message(f"Found {' and '.join(parts)}.")

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
        if key:
            self.message(f"The {Items.get(key).name} turns in the lock.")
        elif prop.props.get("from"):
            self.message("You lift the bar. The way back lies open.")
        else:
            self.message("The door grinds open.")

    def message(self, text):
        self.messages.append([text, 0.0])

    def sfx(self, name, volume=1.0):
        self._audio.play(name, volume=volume)

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
        self._menu_index = 0
        self._menu_top = 0
        self._pick = None
        self._mouse_look(False)
        self.player.guarding = False

    def _open_pick(self, item):
        """Asks which slot (Primary or Secondary) a one-handed weapon, a shield or a spell goes in."""
        self._pick = item
        self._pick_index = 0

    def _spell_name(self):
        spell = self.player.current_spell()
        return spell.name if spell else None

    def _pick_options(self):
        return belongings.pick_options(self.player.inventory, self._pick, self._spell_name())

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
        if hand is None:
            self.player.inventory.unequip(belongings.held_id(item))
            self.message(f"Unequipped {item.name}.")
        else:
            self._equip_in(item, hand)

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
        rows = self.player.inventory.items() + spells
        return sorted(rows, key=lambda i: (KIND_ORDER.index(i.kind), i.name))

    def _update_menu(self):
        if self._pick:
            return self._update_pick()
        items = self._menu_items()
        if self._back():
            return self._enter_play()
        if not items:
            return
        self._menu_nav(len(items))
        self._menu_index = clamp(self._menu_index, 0, len(items) - 1)
        self._menu_top = scroll_into_view(self._menu_top, self._menu_index, len(items))
        clicked = self._menu_pointer(
            lambda px, py: list_row_at(*MENU_LIST, len(items), px, py, self._menu_top, LIST_ROWS)
        )
        if clicked or self._input.pressed("confirm"):
            return self._use_item(items[self._menu_index])
        item = items[self._menu_index]
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
        p = self.player
        out = []
        for id_ in dialogue_data.SHOPS[self._shop_id]:
            item = Items.get(id_)
            if item.kind == "scroll" and (item.spell in p.spells or p.inventory.has(id_)):
                continue
            if item.kind in ("weapon", "shield", "armor") and p.inventory.has(id_):
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
        if self.player.inventory.buy(item.id):
            self.sfx("pickup")
            self.message(f"Bought {{{item.name}}}.")
            if item.level > self.player.stats.level:
                self.message(f"You will need level {item.level} to use it.")
        else:
            self.message("You can't afford that.")

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
        elif choice == "Controls":
            self._open_controls()
        elif choice == "Return to Title":
            self.show_title()
        elif choice == "Quit":
            self._running = False

    def _open_controls(self):
        """Controls reference, opened from the title or pause menu; returns to it on cancel."""
        self._controls_from = self.scene
        self.scene = "controls"

    def _update_controls(self):
        if self._back() or self._advance():
            self.scene = self._controls_from

    def _draw_controls(self):
        if self._controls_from == "pause":
            ui.hud(self)
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        ui.list_menu("Controls", 20, 14, 280, CONTROLS, -1, footer="Esc / Enter / Click: back")

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
        self.player.revive()
        self.messages.clear()
        self._load_world(map_name)
        self.player.place(x, z, yaw, self.world.map)
        self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
        self._enter_play()
        self.message("You wake beside the shrine.")
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
        if self.scene in ("menu", "shop"):
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
            meta.get("torch", [0, 0, 0, 0]), self._dark_k or 0.0, self.player.lumen_t > 0
        )
        gpu.set_vec3("torchColor", torch)
        gpu.set_float("torchRadius", radius)

        pr.begin_mode_3d(self._camera)
        self.world.draw(self._rig, gpu)
        pr.end_mode_3d()

        if self.scene not in ("play", "dialogue", "menu", "shop", "rest") or not self.player.alive:
            return
        p = self.player
        pr.begin_mode_3d(self._view_camera)
        rl.rlDisableDepthTest()  # begin_mode_3d turns depth on; the viewmodel must draw over the world
        gpu.set_float("isModel", 1.0)
        gpu.model_light([min(c + 0.15, 1.4) for c in self.world.builder.light_at(p.x, p.eye_y, p.z)])
        bob = math.sin(p.bob_t) * 0.02
        models.weapon_view(self._rig, p, bob, self._time)
        pr.end_mode_3d()

    def _selected_item(self):
        """The highlighted row of the inventory or shop list, or None."""
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
        if self.scene == "title" or (self.scene == "controls" and self._controls_from == "title"):
            a = self._time * 0.08
            cx, cz = TileMap.center(15, 15)
            ex = cx + math.cos(a) * 9
            ez = cz + math.sin(a) * 9
            self.player.x = ex
            self.player.z = ez
            cam.position = (ex, 4.5, ez)
            cam.target = (cx, 1.5, cz)
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
        elif s == "rest":
            ui.hud(self)
            ui.rest_fog(self._rest, self._time)
        elif s == "pause":
            ui.hud(self)
            pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
            ui.list_menu("Paused", *PAUSE_LIST, [(o,) for o in PAUSE_OPTIONS], self._menu_index)
        elif s == "controls":
            self._draw_controls()
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
            "Belongings", *MENU_LIST, rows, self._menu_index, first=self._menu_top, visible=LIST_ROWS
        )
        self._draw_equipped()
        self._draw_stats()
        item = items[self._menu_index] if self._menu_index < len(items) else None
        self._draw_item_panel(
            item,
            self._item_detail(item) if item else "",
            "1: Primary   2: Secondary   Enter: choose   Tab: close",
        )
        if self._pick:
            x, y, w = PICK_LIST
            rows = [(label,) for label, _ in self._pick_options()]
            ui.list_menu(f"Equip {self._pick.name}", *PICK_LIST, rows, self._pick_index)
            for i, (_, slot) in enumerate(self._pick_options()):
                if slot is not None:
                    ui.mini_mouse(x + w - 13, y + ROW_TOP + i * ROW_H - 1, belongings.SLOT_BUTTONS[slot])

    def _menu_right(self, item):
        """A Belongings row's right column: how many, a spell's MP cost, or the level it needs."""
        if item.kind == "consumable":
            return f"x{self.player.inventory.count(item.id)}"
        if item.kind == "spell":
            return f"{Spells.get(item.spell).cost} MP"
        return self._level_mark(item)

    def _draw_equipped(self):
        """What each slot holds: a mini mouse with its button lit for Primary and Secondary."""
        x, y, w = EQUIPPED_PANEL
        ui.panel(x, y, w, 20 + 4 * ROW_H + 3)
        ui.text("Equipped", x + 8, y + 5, ui.HIGHLIGHT)
        for i, (button, slot, name) in enumerate(
            belongings.equipped_rows(self.player.inventory, self._spell_name())
        ):
            ry = y + ROW_TOP + i * ROW_H
            if button:
                ui.mini_mouse(x + 8, ry - 1, button)
            else:
                ui.tiny(slot.upper(), x + 6, ry + 2, ui.DIM)
            ui.text(name, x + 30, ry, ui.DIM if name.startswith("(") or name == "-" else ui.TEXT)

    def _draw_stats(self):
        """Level, vitals and attributes in two columns, EXP across the bottom."""
        s = self.player.stats
        inv = self.player.inventory
        x, y, w = STATS_PANEL
        ui.panel(x, y, w, 5 * ROW_H + 10)
        pairs = [
            (("Lv", s.level), ("Gold", inv.gold)),
            (("HP", f"{s.hp}/{s.max_hp}"), ("MP", f"{s.mp}/{s.max_mp}")),
            (("STR", s.strength), ("MAG", s.magic)),
            (("ATK", self._swing_power(inv.weapon_item())), ("DEF", inv.defense)),
        ]
        half = (w - 16) // 2
        for i, row in enumerate(pairs):
            for j, (k, v) in enumerate(row):
                cx = x + 8 + j * (half + 4)
                ui.text(k, cx, y + 6 + i * ROW_H, ui.DIM)
                ui.text(str(v), cx + half - 4 - ui.measure(str(v)), y + 6 + i * ROW_H)
        exp = f"{s.exp}/{s.next_level_exp}"
        ui.text("EXP", x + 8, y + 6 + 4 * ROW_H, ui.DIM)
        ui.text(exp, x + w - 8 - ui.measure(exp), y + 6 + 4 * ROW_H)

    def _equipped_mark(self, item):
        """Row suffix: which slots hold the item ([1], [2], [1+2]), or [Worn] for armor."""
        spell = self.player.current_spell()
        return belongings.slot_mark(self.player.inventory, item, spell.id if spell else None)

    def _level_mark(self, item):
        return f"Lv{item.level}" if item.level > 1 else None

    def _draw_item_panel(self, item, detail, footer):
        """Bottom panel shared by Belongings and the shop: spinning preview, name, details, description."""
        ui.panel(6, 156, 308, 78)
        if item:
            pr.draw_rectangle(10, 160, PREVIEW + 6, PREVIEW + 6, pr.BLACK)
            pr.draw_texture_rec(
                self._preview.texture, pr.Rectangle(0, 0, PREVIEW, -PREVIEW), pr.Vector2(13, 163), pr.WHITE
            )
            pr.draw_rectangle_lines(10, 160, PREVIEW + 6, PREVIEW + 6, ui.HUD_EDGE)
            ui.text(item.name, 84, 162, ui.HIGHLIGHT)
            ui.text(detail, 84, 174, ui.DIM)
            lines = ui.wrap(item.desc, 224)
            if item.kind == "weapon":
                moves = weapons.moveset(item)
                head = f"{moves[weapons.LIGHT].name} / Heavy: {moves[weapons.HEAVY].name}"
                if weapons.has_secret(item):
                    known = f"secret:{item.category}" in self.flags
                    head += f" / {moves[weapons.SECRET].name if known else '???'}"
                lines = [head, *lines]
            for i, l in enumerate(lines[:3]):
                ui.text(
                    l,
                    84,
                    187 + i * 11,
                    ui.color(240, 210, 90) if l is lines[0] and item.kind == "weapon" else ui.TEXT,
                )
        msg = self.messages[-1] if self.messages else None
        fresh = msg is not None and msg[1] < 2.5
        ui.text(msg[0] if fresh else footer, 84, 221, ui.TEXT if fresh else ui.DIM)

    def _item_detail(self, item):
        need = f"   Lv{item.level}" if item.level > 1 else ""
        if item.kind == "weapon":
            kind = weapons.CATEGORY_NAMES[item.category] + (" (2H)" if item.two_handed else "")
            return f"{kind}   ATK {item.power}   Reach {item.reach}{need}"
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
        return "Key item"

    def _draw_shop(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        stock = self._shop_stock()
        gold = self.player.inventory.gold
        level = self.player.stats.level
        rows = [
            (i.name, f"{f'Lv{i.level}  ' if i.level > level else ''}{i.price}g", i.price > gold)
            for i in stock
        ]
        title = f"{dialogue_data.SHOP_NAMES[self._shop_id]}  (you have {gold}g)"
        ui.list_menu(title, *SHOP_LIST, rows, self._menu_index, first=self._menu_top, visible=LIST_ROWS)
        item = self._selected_item()
        detail = f"{self._item_detail(item)}   {item.price}g" if item else ""
        self._draw_item_panel(item, detail, "Enter/Click: buy   Esc/R-click: leave")

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
