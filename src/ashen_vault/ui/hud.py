"""2D drawing at the 320x240 internal resolution."""

import itertools
import math

import pyray as pr
import raylib as rl
from raylib import ffi

from ashen_vault.screen import H, W
from ashen_vault.ui import smallfont, tinyfont
from ashen_vault.util import clamp, highlight_runs, rround
from ashen_vault.world import rest


def color(r, g, b, a=255):
    return pr.Color(int(r), int(g), int(b), int(a))


TEXT = color(220, 210, 180)
DIM = color(140, 130, 110)
SHADOW = color(0, 0, 0, 200)
PANEL = color(10, 8, 6, 210)
BORDER = color(120, 100, 70)
HIGHLIGHT_RGB = (255, 220, 140)
HIGHLIGHT = color(*HIGHLIGHT_RGB)


def measure(s, size=10):
    return pr.measure_text(s, size)


def text(s, x, y, col=TEXT, size=10):
    x, y = int(x), int(y)
    pr.draw_text(s, x + 1, y + 1, size, SHADOW)
    pr.draw_text(s, x, y, size, col)


def text_centered(s, cx, y, col=TEXT, size=10):
    text(s, cx - measure(s, size) // 2, y, col, size)


def panel(x, y, w, h):
    """A menu or dialogue window: the HUD's gold-edged box with a darker fill."""
    hud_box(x, y, w, h, fill=PANEL)


def bar(x, y, w, h, frac, rgb):
    pr.draw_rectangle(x - 1, y - 1, w + 2, h + 2, color(0, 0, 0, 220))
    pr.draw_rectangle(x, y, rround(w * clamp(frac, 0, 1)), h, color(*rgb))


def wrap(s, width, size=10):
    """Word-wraps `s` to `width` pixels."""
    lines = [""]
    for word in s.split():
        trial = word if not lines[-1] else f"{lines[-1]} {word}"
        if measure(trial, size) > width and lines[-1]:
            lines.append(word)
        else:
            lines[-1] = trial
    return lines


STAMINA_RGB = (70, 170, 80)
STAMINA_TIRED_RGB = (40, 85, 45)


def tiny(s, x, y, col=TEXT):
    """3x5 pixel text with a 1 px drop shadow (see tinyfont)."""
    x, y = int(x), int(y)
    runs = list(tinyfont.rects(s, x, y))
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx + 1, ry + 1, rw, rh, SHADOW)
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx, ry, rw, rh, col)


def tiny_centered(s, cx, y, col=TEXT):
    tiny(s, cx - tinyfont.width(s) // 2, y, col)


def small(s, x, y, col=TEXT):
    """In-game message text in the small pixel font (see smallfont), with a 1 px drop shadow.
    Returns the x just past the text."""
    x, y = int(x), int(y)
    runs = list(smallfont.rects(s, x, y))
    shadow = color(0, 0, 0, rround(SHADOW.a * col.a / 255))
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx + 1, ry + 1, rw, rh, shadow)
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx, ry, rw, rh, col)
    return x + smallfont.width(s) + smallfont.GAP


def small_centered(s, cx, y, col=TEXT):
    small(s, cx - smallfont.width(s) // 2, y, col)


def small_marked_centered(s, cx, y, base, hi):
    """Centred message whose `{...}` spans (item names, gold) are drawn in the `hi` colour."""
    runs = highlight_runs(s)
    x = cx - smallfont.width("".join(seg for seg, _ in runs)) // 2
    for seg, marked in runs:
        x = small(seg, x, y, hi if marked else base)


def hud(game):
    p = game.player
    s = p.stats

    # Bottom left: the vitals and a small compass in one gold-edged box. It shares its height
    # and bottom edge with the mouse on the right, so both boxes are vertically centred together.
    bx, by = 4, H - 4 - HUD_BOX_H
    hud_box(bx, by, VITALS_W, HUD_BOX_H)
    rows = by + (HUD_BOX_H - 19) // 2  # three 5 px rows, 7 px apart
    vital("HP", bx + 6, rows, s.hp / s.max_hp, (230, 120, 110), (190, 40, 40), s.hp)
    vital("MP", bx + 6, rows + 7, s.mp / s.max_mp, (120, 150, 230), (50, 80, 200), s.mp)
    st = p.stamina
    vital(
        "ST",
        bx + 6,
        rows + 14,
        st.value,
        (130, 200, 130),
        STAMINA_TIRED_RGB if st.exhausted else STAMINA_RGB,
        rround(st.value * 100),
    )
    compass(p.heading, bx + VITALS_W - 18, by + HUD_BOX_H // 2 - 1, COMPASS_R)

    # Bottom right: a mouse whose buttons show what they do.
    mouse_hud(p, W - 4 - MOUSE_W, H - 4 - MOUSE_H)

    boss_bar(game)
    messages(game)
    prompt(game)
    flash(p)


def vital(label, x, y, frac, label_rgb, bar_rgb, value=None):
    """One compact row: label, a short bar, and an optional number."""
    tiny(label, x, y, color(*label_rgb))
    bar(x + 10, y + 1, 36, 3, frac, bar_rgb)
    if value is not None:
        tiny(str(value), x + 50, y, DIM)


SLOT_R = 7
SLOT_PULSE = 0.35  # seconds a ring flashes after it fills
FOCUS_RGB = (120, 220, 240)
FOCUS_CHARGING_RGB = (50, 100, 120)
ATK_RGB = (240, 210, 90)
ATK_CHARGING_RGB = (150, 120, 50)


def ready_slot(cx, cy, gauge, ready_rgb, charging_rgb, track_rgb, r=SLOT_R):
    """Backing disc plus a ring that fills clockwise with `gauge` and flashes once when full."""
    centre = pr.Vector2(cx, cy)
    pr.draw_circle(cx, cy, r + 4, color(0, 0, 0, 200))
    pr.draw_ring(centre, r + 1, r + 3, 0, 360, 32, color(*track_rgb))
    ready = gauge.full
    end = -90 + 360 * clamp(gauge.value, 0, 1)
    pr.draw_ring(centre, r + 1, r + 3, -90, end, 32, color(*(ready_rgb if ready else charging_rgb)))
    if ready and gauge.full_t < SLOT_PULSE:
        k = gauge.full_t / SLOT_PULSE
        grow = r + 3 + k * 4
        pr.draw_ring(centre, grow - 1, grow, 0, 360, 32, color(255, 250, 230, rround(220 * (1 - k))))
    return ready


HUD_FILL = color(20, 16, 12, 215)
HUD_EDGE = color(170, 135, 70)  # the gold trim shared by the vitals box and the mouse
HUD_RADIUS = 3  # corner radius in pixels, shared by every HUD box, menu and window
HUD_BOX_H = 38  # both bottom boxes share this height
VITALS_W = 104
COMPASS_R = 12
MOUSE_W = 70
MOUSE_H = HUD_BOX_H
MOUSE_SPLIT = 26  # height of the button row; the palm below holds the item count
WHEEL_W = 10


def hud_box(x, y, w, h, fill=HUD_FILL, radius=HUD_RADIUS, edge=HUD_EDGE):
    """A box with gold trim and `radius`-pixel corners, whatever its size."""
    rect = pr.Rectangle(x, y, w, h)
    roundness = min(2 * radius / min(w, h), 1)
    pr.draw_rectangle_rounded(rect, roundness, 4, fill)
    pr.draw_rectangle_rounded_lines_ex(rect, roundness, 4, 1, edge)


def mouse_hud(player, x, y):
    """A mouse whose buttons show what each hand holds: the right hand on the left button, the left
    hand on the right one; the quick item on the wheel (middle click uses it, rolling picks another)."""
    w, split = MOUSE_W, MOUSE_SPLIT
    hud_box(x, y, w, MOUSE_H)
    cx = x + w // 2
    cy = y + split // 2 + 1
    pr.draw_line(cx, y + 1, cx, y + split, HUD_EDGE)  # button divider
    pr.draw_line(x + 3, y + split, x + w - 3, y + split, HUD_EDGE)
    hand_slot(player, "right", x + 17, cy)
    hand_slot(player, "left", x + w - 17, cy)
    wheel_slot(player, cx, cy)

    # Palm: L / R marks and how many of the quick item are left.
    mark = color(120, 100, 64)
    tiny("L", x + 8, y + split + 4, mark)
    tiny("R", x + w - 11, y + split + 4, mark)
    n = player.inventory.count(player.quick)
    tiny_centered(f"X{n}", cx + 1, y + split + 4, TEXT if n else color(200, 80, 70))


def wheel_slot(player, cx, cy):
    """The wheel: the selected quick item (middle click) between up/down chevrons."""
    item = player.quick_item()
    n = player.inventory.count(item.id)
    hud_box(cx - WHEEL_W // 2, cy - 11, WHEEL_W, 22, fill=color(0, 0, 0, 220), radius=2)
    top = cy - 11
    chev = color(150, 120, 70)
    pr.draw_triangle(pr.Vector2(cx, top + 2), pr.Vector2(cx - 2, top + 4), pr.Vector2(cx + 2, top + 4), chev)
    pr.draw_triangle(
        pr.Vector2(cx - 2, top + 18), pr.Vector2(cx, top + 20), pr.Vector2(cx + 2, top + 18), chev
    )
    item_icon(item.id, cx, cy, pr.get_time(), 255 if n else 90)


def hand_slot(player, hand, cx, cy):
    """One mouse button: whatever that hand holds, drawn by kind."""
    item = player.hand_item(hand)
    if hand == "left" and player.inventory.two_handing():
        return two_hand_slot(player, item, cx, cy)
    if item.kind == "shield":
        return shield_slot(player, item, cx, cy)
    if item.kind == "spell":
        return spell_slot(player, cx, cy)
    return weapon_slot(player, hand, item, cx, cy)


def weapon_slot(player, hand, weapon, cx, cy):
    """A hand's weapon (or fist), ringed by its ATK gauge: swing when it glows for full damage."""
    gauge = player.gauge(hand)
    ready = ready_slot(cx, cy, gauge, ATK_RGB, ATK_CHARGING_RGB, (48, 40, 20))
    weapon_icon(weapon, cx, cy, pr.get_time(), 255 if ready else 110, ready)
    if player.charge_hand == hand:
        charge_ring(player, cx, cy)


def two_hand_slot(player, weapon, cx, cy):
    """The right mouse button of a two-hander: an instant heavy, ringed orange while ST allows it."""
    ok = player.can_heavy("right")
    pr.draw_circle(cx, cy, SLOT_R + 4, color(0, 0, 0, 200))
    ring = color(*HEAVY_RGB) if ok else color(140, 40, 30, 200)
    pr.draw_ring(pr.Vector2(cx, cy), SLOT_R + 1, SLOT_R + 3, 0, 360, 32, ring)
    weapon_icon(weapon, cx, cy, pr.get_time(), 200 if ok else 90)


def shield_slot(player, shield, cx, cy):
    """A shield, ringed by ST while it is raised (that is what blocking spends)."""
    centre = pr.Vector2(cx, cy)
    pr.draw_circle(cx, cy, SLOT_R + 4, color(0, 0, 0, 200))
    pr.draw_ring(centre, SLOT_R + 1, SLOT_R + 3, 0, 360, 32, color(40, 50, 40))
    up = player.guarding
    if up:
        end = -90 + 360 * clamp(player.stamina.value, 0, 1)
        pr.draw_ring(centre, SLOT_R + 1, SLOT_R + 3, -90, end, 32, color(*STAMINA_RGB))
    alpha = 110 if player.guard_break_t > 0 else 255
    shield_icon(shield, cx, cy, alpha, up)


CHARGE_SHOW = 0.08  # ignore the first moments of a hold so plain taps never flash the ring
HEAVY_RGB = (255, 140, 50)


def charge_ring(player, cx, cy, r=SLOT_R):
    """While the attack button is held: an orange ring that fills towards a heavy attack and
    pulses once it is ready. Dim red when there is not enough ST for one."""
    if player.swinging or player.charge_t < CHARGE_SHOW:
        return
    centre = pr.Vector2(cx, cy)
    k = player.charge_frac
    if not player.can_heavy():
        pr.draw_ring(centre, r + 4, r + 5.5, 0, 360, 32, color(140, 40, 30, 200))
        return
    pr.draw_ring(centre, r + 4, r + 5.5, -90, -90 + 360 * k, 32, color(*HEAVY_RGB))
    if k >= 1:
        pulse = 0.5 + 0.5 * math.sin(player.charge_t * 18)
        pr.draw_ring(centre, r + 4, r + 5.5, 0, 360, 32, color(255, 220, 150, rround(120 * pulse)))


def spell_slot(player, cx, cy):
    """The selected spell: an animated icon ringed by the focus (MAG) gauge."""
    spell = player.current_spell()
    if not spell:
        r = SLOT_R
        pr.draw_circle(cx, cy, r + 4, color(0, 0, 0, 200))
        pr.draw_ring(pr.Vector2(cx, cy), r + 1, r + 3, 0, 360, 32, color(60, 56, 48))
        return
    ready = ready_slot(cx, cy, player.magic_gauge, FOCUS_RGB, FOCUS_CHARGING_RGB, (25, 40, 48))
    spell_icon(spell.id, cx, cy, pr.get_time(), 255 if ready else 110)


def item_icon(id_, cx, cy, t, alpha=255):
    """Tiny quick-item glyphs for the mouse wheel."""
    a = int(alpha)
    if id_ == "red_tonic":
        pr.draw_rectangle(cx - 1, cy - 4, 2, 2, color(120, 90, 60, a))
        pr.draw_circle(cx, cy, 2.5, color(170, 30, 30, a))
        shine = rround(a * (0.5 + 0.5 * math.sin(t * 4)))
        pr.draw_rectangle(cx - 1, cy - 1, 1, 1, color(255, 160, 150, shine))
    elif id_ == "blue_moss":
        glow = 0.6 + 0.4 * math.sin(t * 3)
        pr.draw_circle(cx, cy, 3.5, color(60, 140, 190, rround(a * 0.3 * glow)))
        pr.draw_circle(cx - 1, cy + 1, 1.5, color(60, 140, 190, a))
        pr.draw_circle(cx + 1, cy - 1, 1.5, color(90, 170, 210, a))
    else:
        pr.draw_circle(cx, cy, 2, color(200, 200, 200, a))


def weapon_icon(item, cx, cy, t, alpha=255, ready=False):
    """Small weapon glyphs drawn from primitives, one per category; a glint runs up the
    blade of edged weapons while ready."""
    a = int(alpha)
    cat = item.category
    if cat == "fists":
        skin = color(200, 150, 110, a)
        pr.draw_rectangle(cx - 4, cy - 1, 8, 5, skin)
        for i in range(4):
            pr.draw_rectangle(cx - 4 + i * 2, cy - 4, 2, 3, skin)
            pr.draw_rectangle(cx - 4 + i * 2, cy - 4, 1, 1, color(240, 200, 160, a))
        pr.draw_rectangle(cx + 4, cy - 1, 2, 3, skin)
        return
    wood = color(110, 74, 44, a)
    iron = color(150, 150, 160, a)
    if cat == "mace":
        pr.draw_line_ex(pr.Vector2(cx - 5, cy + 5), pr.Vector2(cx + 2, cy - 2), 2, wood)
        pr.draw_circle(cx + 3, cy - 3, 3, iron)
        for dx, dy in ((0, -3), (3, 0), (-3, 0), (0, 3)):
            pr.draw_rectangle(cx + 3 + dx * 4 // 3, cy - 3 + dy * 4 // 3, 1, 1, color(210, 210, 220, a))
        return
    if cat == "hammer":
        pr.draw_line_ex(pr.Vector2(cx - 5, cy + 6), pr.Vector2(cx + 3, cy - 2), 2, wood)
        head = [pr.Vector2(cx - 1, cy - 6), pr.Vector2(cx + 7, cy + 2)]
        pr.draw_line_ex(head[0], head[1], 5, iron)
        pr.draw_line_ex(pr.Vector2(cx + 4, cy - 3), pr.Vector2(cx + 5, cy - 4), 2, color(200, 200, 210, a))
        return
    if cat == "club":
        pr.draw_line_ex(pr.Vector2(cx - 5, cy + 5), pr.Vector2(cx + 4, cy - 4), 3, wood)
        pr.draw_circle(cx + 3, cy - 3, 3, color(130, 90, 56, a))
        if item.id == "spiked_club":
            for dx, dy in ((2, -7), (7, -2), (6, -6), (0, -4)):
                pr.draw_rectangle(cx + dx, cy + dy, 1, 1, iron)
        return
    if cat == "axe":
        two = item.two_handed
        pr.draw_line_ex(pr.Vector2(cx - 5, cy + 6), pr.Vector2(cx + 3, cy - 5), 2, wood)
        head = [pr.Vector2(cx + 1, cy - 6), pr.Vector2(cx + 7, cy - 2 if two else cy - 3)]
        pr.draw_line_ex(head[0], head[1], 4 if two else 3, iron)
        pr.draw_line_ex(pr.Vector2(cx + 5, cy - 6), pr.Vector2(cx + 8, cy - 1), 1, color(220, 220, 230, a))
        return
    if cat == "whip":
        pr.draw_line_ex(pr.Vector2(cx - 6, cy + 6), pr.Vector2(cx - 3, cy + 3), 2, color(80, 54, 34, a))
        pts = [(-3, 3), (0, -1), (4, -4), (7, -3), (6, 1), (3, 2)]
        for (x0, y0), (x1, y1) in itertools.pairwise(pts):
            pr.draw_line_ex(
                pr.Vector2(cx + x0, cy + y0), pr.Vector2(cx + x1, cy + y1), 1.5, color(150, 110, 70, a)
            )
        return
    blade_rgb = {
        "ashblade": (215, 215, 225),
        "rusted_sword": (150, 132, 112),
        "katana": (225, 228, 238),
        "moonless_tachi": (120, 120, 140),
        "nodachi": (230, 232, 240),
    }.get(item.id, (190, 192, 202))
    blade = color(*blade_rgb, a)
    hilt = color(60, 50, 60, a) if item.id == "ashblade" else color(110, 70, 40, a)
    if item.id == "ashblade":
        glow = 0.5 + 0.5 * math.sin(t * 3)
        pr.draw_circle(cx + 1, cy - 1, 5, color(255, 120, 40, rround(a * 0.25 * glow)))
    big = cat == "greatsword"
    tip = pr.Vector2(cx + 7, cy - 7) if big or item.id == "bastard_sword" else pr.Vector2(cx + 6, cy - 6)
    base = pr.Vector2(cx - 3, cy + 3)
    if cat == "katana":
        pr.draw_line_ex(base, pr.Vector2(cx + 2, cy - 3), 1.5, blade)
        pr.draw_line_ex(pr.Vector2(cx + 2, cy - 3), pr.Vector2(cx + 7, cy - 6), 1.5, blade)
        pr.draw_line_ex(pr.Vector2(cx - 3, cy + 3), pr.Vector2(cx - 6, cy + 6), 2, color(40, 30, 40, a))
        pr.draw_circle(cx - 3, cy + 3, 1.5, color(200, 170, 70, a))
    else:
        pr.draw_line_ex(base, tip, 3 if big else 2, blade)
        pr.draw_line_ex(pr.Vector2(cx - 6, cy), pr.Vector2(cx, cy + 6), 2, hilt)
        pr.draw_line_ex(pr.Vector2(cx - 3, cy + 3), pr.Vector2(cx - 6, cy + 6), 2, hilt)
    if ready:
        k = (t * 0.6) % 1.5  # glint sweeps base -> tip, then rests
        if k < 1:
            gx = rround(cx - 2 + k * 8)
            gy = rround(cy + 2 - k * 8)
            pr.draw_rectangle(gx, gy, 1, 1, color(255, 255, 240, a))


def shield_icon(item, cx, cy, alpha=255, raised=False):
    """Shield glyphs: a round boss for the buckler and round shield, a kite or a tall slab."""
    a = int(alpha)
    wood = color(120, 84, 50, a)
    iron = color(160, 160, 170, a)
    lift = -1 if raised else 0
    if item.id == "tower_shield":
        pr.draw_rectangle(cx - 4, cy - 6 + lift, 9, 13, wood)
        pr.draw_rectangle_lines(cx - 4, cy - 6 + lift, 9, 13, iron)
        pr.draw_line(cx, cy - 5 + lift, cx, cy + 6 + lift, color(90, 60, 36, a))
    elif item.id == "kite_shield":
        top = cy - 6 + lift
        pr.draw_triangle(
            pr.Vector2(cx - 5, top + 3), pr.Vector2(cx, top + 13), pr.Vector2(cx + 5, top + 3), wood
        )
        pr.draw_rectangle(cx - 5, top, 11, 4, wood)
        pr.draw_line(cx - 5, top, cx + 5, top, iron)
        pr.draw_line(cx, top + 1, cx, top + 10, color(170, 40, 36, a))
    else:
        big = item.id == "round_shield"
        r = 6 if big else 4
        pr.draw_circle(cx, cy + lift, r, wood if big else iron)
        pr.draw_circle_lines(cx, cy + lift, r, iron)
        pr.draw_circle(cx, cy + lift, 2, color(200, 200, 210, a))


def spell_icon(id_, cx, cy, t, alpha=255):
    """Small animated glyphs drawn from primitives, so they stay crisp at 320x240."""
    a = int(alpha)
    if id_ == "flame":
        sway = math.sin(t * 9) * 1.2
        lick = math.sin(t * 13) * 1.0 + 1.0
        pr.draw_circle(cx, cy + 2, 4.5, color(200, 60, 20, a))
        pr.draw_triangle(
            pr.Vector2(cx + sway, cy - 7 - lick),
            pr.Vector2(cx - 4.5, cy + 2),
            pr.Vector2(cx + 4.5, cy + 2),
            color(230, 110, 30, a),
        )
        pr.draw_circle(cx, cy + 3, 2.5, color(255, 220, 90, a))
        pr.draw_triangle(
            pr.Vector2(cx - sway * 0.6, cy - 3 - lick * 0.5),
            pr.Vector2(cx - 2.5, cy + 3),
            pr.Vector2(cx + 2.5, cy + 3),
            color(255, 220, 90, a),
        )
    elif id_ == "mend":
        pulse = 1 + 0.15 * math.sin(t * 4)
        arm = rround(6 * pulse)
        thick = 2
        pr.draw_rectangle(cx - thick, cy - arm, thick * 2, arm * 2, color(90, 200, 110, a))
        pr.draw_rectangle(cx - arm, cy - thick, arm * 2, thick * 2, color(90, 200, 110, a))
        for i in range(3):
            k = (t * 0.8 + i / 3) % 1
            sx = cx + rround(math.sin(i * 2.1 + t) * 5)
            sy = cy + 6 - rround(k * 13)
            pr.draw_rectangle(sx, sy, 1, 1, color(200, 255, 200, rround(a * (1 - k))))
    elif id_ == "lumen":
        spin = t * 1.2
        for i in range(6):
            ang = spin + i * math.pi / 3
            c, s_ = math.cos(ang), math.sin(ang)
            pr.draw_line(
                rround(cx + c * 5),
                rround(cy + s_ * 5),
                rround(cx + c * 8),
                rround(cy + s_ * 8),
                color(240, 230, 170, rround(a * 0.8)),
            )
        glow = 3.5 + 0.6 * math.sin(t * 3)
        pr.draw_circle(cx, cy, glow + 1.5, color(240, 220, 140, rround(a * 0.35)))
        pr.draw_circle(cx, cy, glow, color(255, 250, 220, a))
    elif id_ == "venom":
        # A fang dripping green venom; the drop swells, falls and forms again.
        pr.draw_triangle(
            pr.Vector2(cx - 4, cy - 7),
            pr.Vector2(cx, cy + 1),
            pr.Vector2(cx + 4, cy - 7),
            color(225, 220, 200, a),
        )
        k = (t * 0.9) % 1
        dy = rround(k * k * 8)
        size = 1.5 + min(k * 4, 1) * 1.5
        pr.draw_circle(cx, cy + 2 + dy, size, color(110, 200, 60, rround(a * (1 - k * 0.6))))
        pr.draw_circle(cx, cy + 1 + dy, size * 0.45, color(200, 255, 140, rround(a * (1 - k * 0.6))))
    elif id_ == "veil":
        # Pale wisps curling round each other.
        for i in range(3):
            ang = t * 1.6 + i * 2.1
            for j in range(4):
                b = ang - j * 0.35
                rad = 3 + i * 1.6
                pr.draw_circle(
                    rround(cx + math.cos(b) * rad),
                    rround(cy + math.sin(b) * rad * 0.6),
                    2.0 - j * 0.4,
                    color(205, 215, 220, rround(a * (0.8 - j * 0.18))),
                )
    elif id_ == "pyre":
        # A fan of three tongues of flame.
        for i, ang in enumerate((-0.6, 0.0, 0.6)):
            lick = 7 + math.sin(t * 11 + i * 1.7) * 1.5
            tip = pr.Vector2(cx + math.sin(ang) * lick, cy + 5 - math.cos(ang) * lick)
            pr.draw_triangle(
                tip, pr.Vector2(cx - 2, cy + 5), pr.Vector2(cx + 2, cy + 5), color(230, 90, 30, a)
            )
        pr.draw_circle(cx, cy + 5, 2.5, color(255, 210, 90, a))
    else:
        pr.draw_circle(cx, cy, 4, color(200, 200, 200, a))


COMPASS_TILT = 0.5  # how far we look down onto the ball (radians)


def compass(heading, cx, cy, r=17):
    """Compass ball that rolls with your heading; the facing sits at the front-center."""
    pr.draw_circle(cx, cy, r + 2, color(0, 0, 0, 210))
    # Fake sphere shading: stacked discs drifting toward the light (upper left).
    for i in range(7):
        k = i / 6.0
        pr.draw_circle(
            cx - rround(k * r * 0.35),
            cy - rround(k * r * 0.4),
            r * (1 - k * 0.8),
            color(rround(70 + k * 120), rround(58 + k * 105), rround(40 + k * 80)),
        )

    ct = math.cos(COMPASS_TILT)
    st = math.sin(COMPASS_TILT)

    def project(az, lat):
        a = (az - heading) * math.pi / 180
        x = math.cos(lat) * math.sin(a)
        y = math.sin(lat)
        z = math.cos(lat) * math.cos(a)  # toward the viewer
        return cx + x * r, cy - (y * ct - z * st) * r, z * ct + y * st

    def line(a, b):
        ax, ay, ad = a
        bx, by, bd = b
        if ad < 0 or bd < 0:
            return
        alpha = clamp(rround(90 + min(ad, bd) * 150), 0, 230)
        pr.draw_line(rround(ax), rround(ay), rround(bx), rround(by), color(40, 28, 16, alpha))

    # Meridians every 45 degrees plus the equator, front hemisphere only.
    for az in range(0, 360, 45):
        for lat in range(-75, 61, 15):
            line(project(az, lat * math.pi / 180), project(az, (lat + 15) * math.pi / 180))
    for az in range(0, 360, 15):
        line(project(az, 0), project(az + 15, 0))

    for label, az in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        px, py, depth = project(az, 0)
        if depth < -0.05:
            continue
        alpha = rround(clamp(40 + depth * 400, 0, 255))
        rgb = (190, 20, 16) if label == "N" else (30, 18, 8)
        runs = list(tinyfont.rects(label, rround(px) - 1, rround(py) - 2))
        halo = color(245, 230, 190, rround(alpha * 0.8))  # pale outline keeps 3x5 letters legible
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            for rx, ry, rw, rh in runs:
                pr.draw_rectangle(rx + dx, ry + dy, rw, rh, halo)
        for rx, ry, rw, rh in runs:
            pr.draw_rectangle(rx, ry, rw, rh, color(*rgb, alpha))

    # Fixed pointer under the ball marks the facing.
    pr.draw_triangle(
        pr.Vector2(cx, cy + r), pr.Vector2(cx - 2, cy + r + 3), pr.Vector2(cx + 2, cy + r + 3), HIGHLIGHT
    )


BOSS_BAR_W = 168


def boss_bar(game):
    world = game.world
    if not world:
        return
    boss = next((e for e in world.enemies if e.type.boss and e.alive and e.state != "idle"), None)
    if not boss:
        return
    max_hp = boss.type.hp
    bw, bh = BOSS_BAR_W, 5
    x, y = W // 2 - bw // 2, 22
    hud_box(x - 6, 8, bw + 12, 23)
    small_centered(boss.name, W // 2, 11, HIGHLIGHT)
    pr.draw_rectangle(x - 1, y - 1, bw + 2, bh + 2, color(0, 0, 0, 230))
    pr.draw_rectangle(x, y, bw, bh, color(40, 14, 12))
    trail = rround(bw * clamp(boss.trail_hp / max_hp, 0, 1))
    fill = rround(bw * clamp(boss.hp / max_hp, 0, 1))
    if trail > fill:
        pr.draw_rectangle(x + fill, y, trail - fill, bh, color(235, 190, 110))
    if boss.enraged:
        pulse = 0.5 + 0.5 * math.sin(pr.get_time() * 8)
        red = color(rround(150 + 60 * pulse), rround(20 + 10 * pulse), 20)
    else:
        red = color(170, 36, 28)
    if fill > 0:
        pr.draw_rectangle(x, y, fill, bh, red)
        pr.draw_rectangle(x, y, fill, 1, color(230, 110, 90))
    for q in (1, 2, 3):
        pr.draw_rectangle(x + bw * q // 4, y, 1, bh, HUD_EDGE)


def messages(game):
    lines = game.messages[-3:]
    for i, (msg, age) in enumerate(lines):
        alpha = rround(clamp(255 * (5 - age), 0, 255)) if age > 4 else 255
        if alpha <= 0:
            continue
        y = H - 54 - (len(lines) - 1 - i) * smallfont.LINE
        small_marked_centered(msg, W // 2, y, color(230, 220, 190, alpha), color(*HIGHLIGHT_RGB, alpha))


def prompt(game):
    label = game.focus_label()
    if label:
        small_centered(label, W // 2, 140, HIGHLIGHT)


def flash(player):
    if player.webbed_t > 0:
        _web_overlay(clamp(player.webbed_t, 0, 1))
    if player.spore_t > 0:
        # A sickly yellow-green haze while you choke on spores.
        pr.draw_rectangle(0, 0, W, H, color(150, 170, 60, rround(clamp(player.spore_t, 0, 1) * 70)))
    if player.hurt_t <= 0:
        return
    pr.draw_rectangle(0, 0, W, H, color(160, 0, 0, rround(clamp(player.hurt_t * 300, 0, 120))))


def _web_overlay(k):
    """Silk strands across the corners of the view while you are webbed; they fade as it wears off."""
    c = color(230, 230, 220, rround(150 * k))
    for cx, cy, sx, sy in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        for i in range(5):
            a = i * 0.32 + 0.15
            pr.draw_line(cx, cy, cx + sx * rround(90 * math.cos(a)), cy + sy * rround(90 * math.sin(a)), c)
        for ring in (24, 46, 70):
            pts = [
                (
                    cx + sx * rround(ring * math.cos(i * 0.32 + 0.15)),
                    cy + sy * rround(ring * math.sin(i * 0.32 + 0.15)),
                )
                for i in range(5)
            ]
            for (x0, y0), (x1, y1) in itertools.pairwise(pts):
                pr.draw_line(x0, y0, x1, y1, c)


def dialogue(speaker, line, page, pages):
    panel(10, 150, 300, 56)
    text(speaker, 18, 155, HIGHLIGHT)
    for i, l in enumerate(wrap(line, 284)):
        text(l, 18, 168 + i * 11)
    text(f"{page + 1}/{pages}", 284, 195, DIM)


def list_menu(title, x, y, w, rows, selected, footer=None, first=0, visible=None):
    """rows are tuples (label, right=None, dim=False). A long list shows `visible` rows from `first`,
    with arrows on the title line when there is more above or below."""
    shown = rows[first : first + visible] if visible else rows
    height = 22 + max(len(shown), 1) * 11 + (12 if footer else 0)
    panel(x, y, w, height)
    text(title, x + 8, y + 5, HIGHLIGHT)
    if visible and first > 0:
        pr.draw_triangle(
            pr.Vector2(x + w - 12, y + 6), pr.Vector2(x + w - 15, y + 11), pr.Vector2(x + w - 9, y + 11), DIM
        )
    if visible and first + visible < len(rows):
        pr.draw_triangle(
            pr.Vector2(x + w - 25, y + 6), pr.Vector2(x + w - 22, y + 11), pr.Vector2(x + w - 19, y + 6), DIM
        )
    if not rows:
        text("(empty)", x + 12, y + 20, DIM)
    for j, row in enumerate(shown):
        i = first + j if visible else j
        label = row[0]
        right = row[1] if len(row) > 1 else None
        dim = row[2] if len(row) > 2 else False
        col = HIGHLIGHT if i == selected else (DIM if dim else TEXT)
        text(">" if i == selected else " ", x + 4, y + 20 + j * 11, col)
        text(label, x + 12, y + 20 + j * 11, col)
        if right is not None:
            rs = str(right)
            text(rs, x + w - 8 - measure(rs), y + 20 + j * 11, col)
    if footer:
        text(footer, x + 8, y + height - 13, DIM)


_fog_tex = None


def _fog_texture():
    """An 80x60 RGBA texture the rest fog is written into each frame and drawn scaled 4x."""
    global _fog_tex
    if _fog_tex is None:
        img = pr.gen_image_color(rest.COLS, rest.ROWS, pr.BLANK)
        _fog_tex = pr.load_texture_from_image(img)
        pr.unload_image(img)
        pr.set_texture_filter(_fog_tex, pr.TEXTURE_FILTER_POINT)
    return _fog_tex


def rest_fog(seq, t):
    """Shrine rest: chunky ember-and-ash fog rising over the view (see world.rest)."""
    if not seq:
        return
    dens = seq.density
    if dens <= 0:
        return
    tex = _fog_texture()
    pixels = rest.fog_pixels(t, dens)
    rl.UpdateTexture(tex, ffi.from_buffer(pixels))
    pr.draw_texture_pro(
        tex, pr.Rectangle(0, 0, rest.COLS, rest.ROWS), pr.Rectangle(0, 0, W, H), pr.Vector2(0, 0), 0, pr.WHITE
    )
    if dens >= 0.95:
        small_centered(
            "Resting...", W // 2, H // 2 - 4, color(*HIGHLIGHT_RGB, rround(255 * (dens - 0.95) * 20))
        )
