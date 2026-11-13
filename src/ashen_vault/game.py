import math
import random

import pyray as pr
import raylib as rl
from raylib import ffi

from ashen_vault import dialogue as dialogue_data
from ashen_vault.audio.synth import Audio
from ashen_vault.input import CONTROLS, Input
from ashen_vault.player import weapons
from ashen_vault.player.combat import Combat
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.player.spells import Spells
from ashen_vault.render import models
from ashen_vault.render.gpu import Gpu
from ashen_vault.render.rig import Rig
from ashen_vault.save.save_system import SaveSystem
from ashen_vault.screen import FOV, PREVIEW, H, W, centered_row_at, list_row_at
from ashen_vault.ui import hud as ui
from ashen_vault.util import clamp, rround
from ashen_vault.world import relics
from ashen_vault.world.tile_map import TileMap
from ashen_vault.world.world import World

KIND_ORDER = ["weapon", "armor", "consumable", "scroll", "key"]
PAUSE_OPTIONS = ["Resume", "Controls", "Return to Title", "Quit"]
# (x, y, width) of each ui.list_menu panel, shared by drawing and mouse hit-testing.
PAUSE_LIST = (100, 80, 120)
MENU_LIST = (6, 6, 170)
SHOP_LIST = (6, 6, 308)
TITLE_Y, TITLE_STEP = 140, 14
ENDING = [
    "The bell of Harrowmere rings again.",
    "Its note rolls down the well into the drowned halls",
    "and through the roots beneath the overgrown house.",
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
        self._hit_done = False
        self._attack_down = False  # attack button held last frame (tap = light, hold = heavy)
        self._step_phase = 0.0
        self._dialogue = None
        self._controls_from = None
        self._dead_t = 0.0
        self._ending_t = 0.0
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
            f"pos={round(p.x, 2)},{round(p.z, 2)} hp={p.stats.hp} lv={p.stats.level} exp={p.stats.exp} "
            f"gold={inv.gold} scene={self.scene} flags={','.join(sorted(self.flags))} items={inv.counts} "
            f"enemies={enemies} shot={shot}",
            flush=True,
        )
        self._running = False

    def update(self, dt):
        for m in self.messages:
            m[1] += dt
        self.messages = [m for m in self.messages if m[1] <= 5]
        handler = {
            "title": lambda: self._update_title(),
            "play": lambda: self._update_play(dt),
            "dialogue": lambda: self._update_dialogue(),
            "menu": lambda: self._update_menu(),
            "shop": lambda: self._update_shop(),
            "pause": lambda: self._update_pause(),
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
        else:
            pr.enable_cursor()

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
        wheel = self._input.wheel()
        if self._input.pressed("up") or wheel > 0:
            self._menu_index = (self._menu_index - 1) % n
        if self._input.pressed("down") or wheel < 0:
            self._menu_index = (self._menu_index + 1) % n

    def _menu_pointer(self, hit):
        """Mouse over a menu. `hit(px, py)` maps a 320x240 point to a row index or None.
        Moving onto a row selects it; a left click on a row selects it and returns True."""
        ptr = self._input.pointer()
        if ptr is None:
            return False
        px, py, moved = ptr
        i = hit(px, py)
        if i is None:
            return False
        if moved:
            self._menu_index = i
        if self._input.pressed("click"):
            self._menu_index = i
            return True
        return False

    def _back(self):
        return self._input.pressed("cancel") or self._input.pressed("back")

    def _advance(self):
        return self._input.pressed("confirm") or self._input.pressed("click")

    def new_game(self, map_name, at=None):
        self.flags = set()
        self.player = Player()
        self.messages.clear()
        self._load_world(map_name)
        x, z, yaw = self._spot(at) if at else self.world.start_position()
        self.player.place(x, z, yaw, self.world.map)
        self._enter_play()

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
            p.turn(md.x * 0.0032)
            p.look(-md.y * 0.0032)
        moved = p.walk(
            self.world.map,
            self._axis("forward", "back"),
            self._axis("strafe_r", "strafe_l"),
            dt,
            blocked=self.world.blocker,
            sprint=inp.down("sprint"),
            floating=self.world.hazards.floating,
        )
        self.world.update_hazards(dt)
        p.settle(self.world.map, dt, floor=self.world.player_floor())
        if moved:
            self._footstep()

        p.update_timers(dt)
        self._update_attack(dt)
        if p.swinging and not self._hit_done and p.swing_t >= p.swing_hit_at:
            self._resolve_swing()
        if inp.pressed("cast"):
            self._cast_spell()
        wheel = inp.wheel()
        if wheel:
            step = -1 if wheel > 0 else 1  # wheel down = next
            if inp.down("sprint"):
                self._cycle_quick(step)
            else:
                self._cycle_spell(step)
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

    def _update_attack(self, dt):
        """Tap the attack button for a light attack; hold it to charge a heavy one, which lands on
        release. A scripted `attack` taps, `attack:0.6` holds."""
        p = self.player
        inp = self._input
        if inp.down("attack"):
            if not p.swinging:
                p.charge_t += dt
            self._attack_down = True
            return
        released, self._attack_down = self._attack_down, False
        if not (released or inp.pressed("attack")):
            p.charge_t = 0.0
            return
        heavy = p.charge_t >= weapons.CHARGE_TIME
        p.charge_t = 0.0
        if not p.start_swing(heavy):
            return
        self._hit_done = False
        if p.attack.heavy:
            self.sfx("heavy", 0.7)
        else:
            self.sfx("swing", 0.6)
            if heavy:
                self.message("Too winded for a heavy attack.")

    def _resolve_swing(self):
        self._hit_done = True
        p = self.player
        weapon = p.inventory.weapon_item()
        a = p.attack
        if a.lunge:
            p.nudge(self.world.map, a.lunge, blocked=self.world.blocker)
        targets = self.world.melee_targets(weapon.reach * a.reach, a.cone, a.targets)
        if not targets:
            return
        self.sfx("hit")
        for target in targets:
            back = target.hit_mult(p.x, p.z)
            dmg = Combat.damage(
                base=weapon.power,
                strength=p.stats.strength,
                gauge=p.swing_power,
                defense=4 if target.type.boss and not a.pierce_def else 0,
                mult=a.damage * back,
            )
            if back > 1:
                self.message(f"You strike the {target.name}'s weak spot!")
            self.damage_enemy(target, dmg, a.poise * back)

    def damage_enemy(self, enemy, dmg, poise_mult=1.0):
        if not enemy.take_hit(dmg, poise_mult):
            return
        self.sfx("enemy_die")
        t = enemy.type
        gold = random.choice(t.gold)
        self.player.inventory.gold += gold
        self.message(f"{t.name} destroyed. {t.exp} EXP, {gold} gold.")
        if self.player.stats.gain_exp(t.exp) > 0:
            self.sfx("levelup")
            self.message(f"You reached level {self.player.stats.level}!")
        if not t.boss:
            return
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
        if spell.id == "flame":
            self.world.fire_bolt(Spells.flame_damage(p.stats.magic, gauge))
        elif spell.id == "mend":
            amount = Spells.mend_amount(p.stats.magic)
            p.stats.heal(amount)
            self.message(f"Warmth closes your wounds. +{amount} HP")
        elif spell.id == "lumen":
            p.lumen_t = Spells.LUMEN_DURATION
            self.message("A pale light gathers around you.")

    def _cycle_spell(self, step=1):
        spell = self.player.cycle_spell(step)
        if spell:
            self.message(spell.name)

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
            if item.spell not in self.player.spells:
                self.player.spells.append(item.spell)
            self.sfx("levelup")
            self.message(f"You learned {Spells.get(item.spell).name}.")
        elif item.kind in ("weapon", "armor"):
            if inv.unequip(item.id):
                self.message(f"Unequipped {item.name}.")
            else:
                inv.equip(item.id)
                self.message(f"Equipped {item.name}.")
        else:
            self.message(item.desc)

    def focus_label(self):
        if self.scene != "play" or not self.world:
            return None
        p = self.world.focus()
        if not p:
            return None
        return {
            "npc": "[E] Talk",
            "chest": "[E] Open chest",
            "door": "[E] Open door",
            "lever": "[E] Pull lever",
            "save_statue": "[E] Pray at the shrine",
            "exit": f"[E] {(p.props.get('label') or 'Leave').replace('_', ' ')}",
            "pickup": "[E] Take",
        }.get(p.kind)

    def _interact(self):
        prop = self.world.focus()
        if not prop:
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
            self.message("Somewhere chains rattle, and iron grinds against stone.")
        elif k == "save_statue":
            s = self.player.stats
            s.heal(s.max_hp)
            s.restore_mp(s.max_mp)
            self.player.stamina.fill()
            self.world.respawn_enemies()
            self._saves.save(map=self.world.name, player=self.player, flags=self.flags)
            self.sfx("save")
            self.message("The shrine restores you. Your journey is recorded.")
            self.message("Somewhere below, the fallen stir again.")
        elif k == "exit":
            self._travel(prop.props["map"], prop.props["at"])
        elif k == "pickup":
            item = Items.get(prop.props["item"])
            self.player.inventory.add(item.id)
            relics.mark_taken(item.id, self.flags)
            self.world.remove_prop(prop)
            self.sfx("pickup")
            self.message(f"Obtained {item.name}.")

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
            parts.append(f"{Items.get(item).name}{f' x{count}' if count > 1 else ''}")
        if gold > 0:
            parts.append(f"{gold} gold")
        self.message(f"Found {' and '.join(parts)}.")

    def _open_door(self, prop):
        key = prop.props.get("key")
        if key and not self.player.inventory.has(key):
            self.message(f"It is locked. You need the {Items.get(key).name}.")
            return
        self.world.open_prop(prop)
        self.sfx("door")
        self.message(f"The {Items.get(key).name} turns in the lock." if key else "The door grinds open.")

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
        self._mouse_look(False)

    def _menu_items(self):
        return sorted(self.player.inventory.items(), key=lambda i: (KIND_ORDER.index(i.kind), i.name))

    def _update_menu(self):
        items = self._menu_items()
        if self._back():
            return self._enter_play()
        if not items:
            return
        self._menu_nav(len(items))
        self._menu_index = clamp(self._menu_index, 0, len(items) - 1)
        clicked = self._menu_pointer(lambda px, py: list_row_at(*MENU_LIST, len(items), px, py))
        if clicked or self._input.pressed("confirm"):
            self._use_item(items[self._menu_index])

    # --- shop ----------------------------------------------------------------------

    def open_shop(self):
        self.scene = "shop"
        self._menu_index = 0
        self._mouse_look(False)

    def _shop_stock(self):
        p = self.player
        out = []
        for id_ in dialogue_data.SHOP:
            item = Items.get(id_)
            if item.kind == "scroll" and (item.spell in p.spells or p.inventory.has(id_)):
                continue
            if item.kind in ("weapon", "armor") and p.inventory.has(id_):
                continue
            out.append(item)
        return out

    def _update_shop(self):
        stock = self._shop_stock()
        if self._back() or not stock:
            return self._enter_play()
        self._menu_nav(len(stock))
        self._menu_index = clamp(self._menu_index, 0, len(stock) - 1)
        clicked = self._menu_pointer(lambda px, py: list_row_at(*SHOP_LIST, len(stock), px, py))
        if not (clicked or self._input.pressed("confirm")):
            return
        item = stock[self._menu_index]
        if self.player.inventory.buy(item.id):
            self.sfx("pickup")
            self.message(f"Bought {item.name}.")
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
        if self._saves.exists():
            self.continue_game()
        else:
            self.show_title()

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
        fog = self.world.meta.get("fog", [0, 0, 0])
        pr.clear_background(ui.color(*(rround(c * 255) for c in fog)))
        self._render_world(fog)
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

    def _render_world(self, fog):
        self._setup_camera()
        meta = self.world.meta
        gpu = self.gpu
        gpu.set_vec2("snapRes", (W // 2, H // 2))
        gpu.set_vec3("fogColor", fog)
        gpu.set_vec2("fogRange", meta.get("fog_range", [4, 30]))
        radius, *torch = meta.get("torch", [0, 0, 0, 0])
        if self.player.lumen_t > 0:
            radius = max(radius, 0) + 9
            torch = [0.6, 0.65, 0.75]
        gpu.set_vec3("torchColor", torch)
        gpu.set_float("torchRadius", radius)

        pr.begin_mode_3d(self._camera)
        self.world.draw(self._rig, gpu)
        pr.end_mode_3d()

        if self.scene not in ("play", "dialogue", "menu", "shop") or not self.player.alive:
            return
        p = self.player
        pr.begin_mode_3d(self._view_camera)
        rl.rlDisableDepthTest()  # begin_mode_3d turns depth on; the viewmodel must draw over the world
        gpu.set_float("isModel", 1.0)
        gpu.model_light([min(c + 0.15, 1.4) for c in self.world.builder.light_at(p.x, p.eye_y, p.z)])
        bob = math.sin(p.bob_t) * 0.02
        models.weapon_view(self._rig, p, bob)
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
        cam.target = (p.x + fx * cp, eye + math.sin(p.pitch), p.z + fz * cp)

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
        ui.text_centered("ASHEN VAULT", W // 2, 56, ui.HIGHLIGHT, size=20)
        ui.text_centered("beneath the silent bell", W // 2, 80, ui.DIM)
        for i, o in enumerate(self._title_options()):
            sel = i == self._menu_index
            ui.text_centered(
                f"> {o} <" if sel else o, W // 2, TITLE_Y + i * TITLE_STEP, ui.HIGHLIGHT if sel else ui.TEXT
            )

    def _draw_menu(self):
        items = self._menu_items()
        inv = self.player.inventory
        rows = [
            (
                f"{i.name}{' (E)' if inv.equipped(i.id) else ''}",
                f"x{inv.count(i.id)}" if i.kind == "consumable" else None,
            )
            for i in items
        ]
        ui.list_menu("Belongings", *MENU_LIST, rows, self._menu_index)
        s = self.player.stats
        ui.panel(182, 6, 132, 144)
        stats = [
            ("Level", s.level),
            ("EXP", f"{s.exp}/{s.next_level_exp}"),
            ("HP", f"{s.hp}/{s.max_hp}"),
            ("MP", f"{s.mp}/{s.max_mp}"),
            ("STR", s.strength),
            ("MAG", s.magic),
            ("DEF", inv.defense),
            ("Weapon", inv.weapon_item().power),
            ("Gold", inv.gold),
        ]
        for i, (k, v) in enumerate(stats):
            ui.text(k, 190, 12 + i * 11, ui.DIM)
            ui.text(str(v), 306 - ui.measure(str(v)), 12 + i * 11)
        # Known spells with their MP cost (the HUD only shows the selected spell's icon).
        pr.draw_line(188, 111, 308, 111, ui.BORDER)
        for i, id_ in enumerate(self.player.spells[:3]):
            spell = Spells.get(id_)
            cost = f"{spell.cost} MP"
            ui.text(spell.name, 190, 114 + i * 11)
            ui.text(cost, 306 - ui.measure(cost), 114 + i * 11, ui.color(120, 150, 230))

        item = items[self._menu_index] if self._menu_index < len(items) else None
        self._draw_item_panel(
            item, self._item_detail(item) if item else "", "Enter/Click: use   Tab/R-click: close"
        )

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
                light, heavy = weapons.moveset(item)
                lines = [f"{light.name} / Heavy: {heavy.name}", *lines]
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
        if item.kind == "weapon":
            kind = weapons.CATEGORY_NAMES[item.category]
            return f"{kind}   ATK {item.power}   Reach {item.reach}"
        if item.kind == "armor":
            return f"Armor   DEF {item.power}"
        if item.kind == "consumable":
            return f"Consumable   x{self.player.inventory.count(item.id)}"
        if item.kind == "scroll":
            spell = Spells.get(item.spell)
            return f"Scroll   {spell.name}   {spell.cost} MP"
        return "Key item"

    def _draw_shop(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(0, 0, 0, 120))
        stock = self._shop_stock()
        gold = self.player.inventory.gold
        rows = [(i.name, f"{i.price}g", i.price > gold) for i in stock]
        ui.list_menu(f"Pell's Goods  (you have {gold}g)", *SHOP_LIST, rows, self._menu_index)
        item = self._selected_item()
        detail = f"{self._item_detail(item)}   {item.price}g" if item else ""
        self._draw_item_panel(item, detail, "Enter/Click: buy   Esc/R-click: leave")

    def _draw_dead(self):
        pr.draw_rectangle(0, 0, W, H, ui.color(40, 0, 0, rround(min(self._dead_t * 120, 200))))
        ui.text_centered("YOU HAVE FALLEN", W // 2, 100, ui.color(220, 80, 70), size=20)
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
