"""2D drawing at the 320x240 internal resolution."""

import itertools
import math

import pyray as pr
import raylib as rl
from raylib import ffi

from ashen_vault.player.inventory import LEFT, RIGHT
from ashen_vault.screen import H, W
from ashen_vault.ui import logofont, smallfont, tinyfont
from ashen_vault.util import clamp, highlight_runs, plain, rround
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


def measure(s):
    """Pixel width of `s` in the game's text font (smallfont), without `{}` markup."""
    return smallfont.width(plain(s))


TEXT_DY = 1  # smallfont's caps are 6 px tall: one pixel down centres them on the old 10 px rows


def text(s, x, y, col=TEXT, hi=HIGHLIGHT):
    """Menu and dialogue text: the same small pixel font as messages and prompts. `{...}` spans
    (item names in a message) are drawn in `hi`."""
    for seg, marked in highlight_runs(s):
        x = small(seg, x, y + TEXT_DY, hi if marked else col)


def text_centered(s, cx, y, col=TEXT):
    text(s, cx - measure(s) // 2, y, col)


def big(s, cx, y, col=TEXT, px=2):
    """A heading in the logo's 5x7 capitals (see logofont), `px` pixels per glyph pixel, centred
    on `cx`, with a drop shadow."""
    x = cx - logofont.width(s, px) // 2
    off = max(px // 2, 1)
    runs = list(logofont.rects(s, x, int(y), px))
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx + off, ry + off, rw, rh, SHADOW)
    for rx, ry, rw, rh in runs:
        pr.draw_rectangle(rx, ry, rw, rh, col)


def panel(x, y, w, h):
    """A menu or dialogue window: the HUD's gold-edged box with a darker fill."""
    hud_box(x, y, w, h, fill=PANEL)


def bar(x, y, w, h, frac, rgb):
    pr.draw_rectangle(x - 1, y - 1, w + 2, h + 2, color(0, 0, 0, 220))
    pr.draw_rectangle(x, y, rround(w * clamp(frac, 0, 1)), h, color(*rgb))


def wrap(s, width):
    """Word-wraps `s` to `width` pixels."""
    lines = [""]
    for word in s.split():
        trial = word if not lines[-1] else f"{lines[-1]} {word}"
        if measure(trial) > width and lines[-1]:
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


def micro_centered(s, cx, y, col=TEXT):
    """3x4 pixel text (tinyfont.MICRO), no shadow: the mouse's slot labels and the quick count."""
    x = int(cx - tinyfont.width(s) // 2)
    for rx, ry, rw, rh in tinyfont.rects(s, x, int(y), tinyfont.MICRO):
        pr.draw_rectangle(rx, ry, rw, rh, col)


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
    # and bottom edge with the mouse on the right.
    bx, by = HUD_MARGIN, H - HUD_MARGIN - HUD_BOX_H
    hud_box(bx, by, VITALS_W, HUD_BOX_H, edge=ward_edge(p))
    rows = by + (HUD_BOX_H - 19) // 2  # three 5 px rows, 7 px apart
    vx = bx + HUD_PAD + 1  # inside the 1 px trim, like every box's contents
    vital("HP", vx, rows, s.hp / s.max_hp, (230, 120, 110), (190, 40, 40), s.hp)
    vital("MP", vx, rows + 7, s.mp / s.max_mp, (120, 150, 230), (50, 80, 200), s.mp)
    st = p.stamina
    vital(
        "ST",
        vx,
        rows + 14,
        st.value,
        (130, 200, 130),
        STAMINA_TIRED_RGB if st.exhausted else STAMINA_RGB,
        rround(st.value * 100),
    )
    # The ball's shadow and E/W letters reach COMPASS_R + 2 to each side; its pointer ends
    # COMPASS_R + 3 below the centre. It sits centred between the numbers and the box's right edge.
    reach = COMPASS_R + 2
    span = 2 * COMPASS_R + 6  # top of the shadow to the tip of the pointer
    left = vx + VITAL_NUM_X + tinyfont.width("100")
    right = bx + VITALS_W - HUD_PAD - 1
    target = game.world.boss_bearing() if game.world else None
    compass(p.heading, (left + right) // 2, by + (HUD_BOX_H - span) // 2 + reach, COMPASS_R, target)

    # Bottom right: a mouse whose buttons show what Primary and Secondary hold, the quick item
    # on its wheel.
    mouse_hud(p, W - HUD_MARGIN - MOUSE_HUD_W, H - HUD_MARGIN - HUD_BOX_H)

    gold_counter(game)
    boss_bar(game)
    messages(game)
    prompt(game)
    flash(p)


WARD_EDGE_RGB = (245, 150, 60)


def ward_edge(player):
    """The vitals box's trim: ember-lit and breathing while an Ashen Ward holds, gold otherwise."""
    if player.ward_t <= 0:
        return HUD_EDGE
    k = 0.55 + 0.45 * math.sin(pr.get_time() * 5)
    gold = (HUD_EDGE.r, HUD_EDGE.g, HUD_EDGE.b)
    return color(*(rround(g + (w - g) * k) for g, w in zip(gold, WARD_EDGE_RGB, strict=True)))


def vital(label, x, y, frac, label_rgb, bar_rgb, value=None):
    """One compact row: label, a short bar, and an optional number."""
    tiny(label, x, y, color(*label_rgb))
    bar(x + VITAL_BAR_X, y + 1, VITAL_BAR_W, 3, frac, bar_rgb)
    if value is not None:
        tiny(str(value), x + VITAL_NUM_X, y, DIM)


SLOT_PULSE = 0.35  # seconds a mouse button's edge flashes after its gauge fills
FOCUS_RGB = (120, 220, 240)
FOCUS_CHARGING_RGB = (50, 100, 120)
ATK_RGB = (240, 210, 90)
ATK_CHARGING_RGB = (150, 120, 50)
CHARGE_SHOW = 0.08  # ignore the first moments of a hold so plain taps never flash the bar
HEAVY_RGB = (255, 140, 50)
WINDED_RGB = (140, 40, 30)

HUD_FILL = color(20, 16, 12, 215)
HUD_EDGE = color(170, 135, 70)  # the gold trim shared by the vitals box and the mouse
HUD_RADIUS = 3  # corner radius in pixels, shared by every HUD box, menu and window
HUD_INNER_RADIUS = HUD_RADIUS - 1  # a well set inside a box (the mouse's wheel)
# One spacing scale for the whole HUD:
HUD_MARGIN = 3  # pixels between the HUD boxes and the screen edge
HUD_PAD = 3  # pixels from a HUD box's outer edge (its 1 px trim included) to its contents
HUD_GAP = 2  # pixels between neighbouring HUD elements (a box and the text above it)
HUD_BOX_H = 38  # the vitals box and the mouse share this height
VITALS_W = 90
VITAL_BAR_X, VITAL_BAR_W = 10, 30  # a vital's bar: after its 2-letter label, before its number
VITAL_NUM_X = VITAL_BAR_X + VITAL_BAR_W + 4
COMPASS_R = 10
MOUSE_HUD_W = 58  # the bottom-right mouse: two buttons and the wheel between them
MOUSE_SPLIT = 27  # height of its button row; the palm below holds the slot labels and the count
WHEEL_W = 9
BUTTON_LABELS = {RIGHT: "PRI", LEFT: "SEC"}
# Text stacks up from the bottom boxes: the newest message just above them, the prompt above that.
MESSAGE_Y = H - HUD_MARGIN - HUD_BOX_H - HUD_GAP - smallfont.HEIGHT
PROMPT_Y = MESSAGE_Y - 5 * smallfont.LINE  # three message lines and two empty ones below it


def corner_insets(radius):
    """How far in each of a rounded box's top `radius` rows starts (mirrored for the other corners):
    a quarter circle in whole pixels, so every box with the same radius has the very same corners."""
    return tuple(
        max(rround(radius - math.sqrt(radius * radius - (radius - i - 0.5) ** 2) + 0.25), 0)
        for i in range(radius)
    )


def hud_box(x, y, w, h, fill=HUD_FILL, radius=HUD_RADIUS, edge=HUD_EDGE):
    """A box with a 1 px gold trim and pixel-exact `radius` corners, whatever its size: drawn as runs
    of whole pixels rather than raylib's rounded rectangles, which rasterise differently by size."""
    x, y, w, h = rround(x), rround(y), rround(w), rround(h)
    insets = corner_insets(min(radius, w // 2, h // 2))
    r = len(insets)
    for i, inset in enumerate(insets):  # the rounded rows, top and bottom
        for row in (y + i, y + h - 1 - i):
            pr.draw_rectangle(x + inset, row, w - 2 * inset, 1, fill)
    pr.draw_rectangle(x, y + r, w, h - 2 * r, fill)
    if edge is None:
        return
    if not r:
        pr.draw_rectangle_lines(x, y, w, h, edge)
        return
    for row in (y, y + h - 1):  # the trim: top and bottom edges between the corners
        pr.draw_rectangle(x + insets[0], row, w - 2 * insets[0], 1, edge)
    for i in range(1, r):  # each lower corner row runs from its inset to the row above's
        run = max(insets[i - 1] - insets[i], 1)
        for row in (y + i, y + h - 1 - i):
            pr.draw_rectangle(x + insets[i], row, run, 1, edge)
            pr.draw_rectangle(x + w - insets[i] - run, row, run, 1, edge)
    pr.draw_rectangle(x, y + r, 1, h - 2 * r, edge)
    pr.draw_rectangle(x + w - 1, y + r, 1, h - 2 * r, edge)


MOUSE_W, MOUSE_H = 5, 7  # the mini mouse drawn beside equipped rows in Belongings


def mini_mouse(x, y, lit, dim=False):
    """A 5x7 mouse with the `lit` button ("left" / "right" / "wheel", or None for none) glowing."""
    body = color(150, 140, 120, 120 if dim else 255)
    pr.draw_rectangle_rounded(pr.Rectangle(x, y, MOUSE_W, MOUSE_H), 0.6, 4, body)
    off = color(60, 54, 44)
    on = color(*HIGHLIGHT_RGB) if not dim else color(120, 100, 64)
    pr.draw_rectangle(x + 1, y + 1, 1, 2, on if lit == "left" else off)
    pr.draw_rectangle(x + 3, y + 1, 1, 2, on if lit == "right" else off)
    pr.draw_rectangle(x + 2, y + 1, 1, 2, on if lit == "wheel" else color(30, 26, 20))
    pr.draw_line(x + 1, y + 4, x + 4, y + 4, color(90, 80, 64))


def mouse_hud(player, x, y):
    """Bottom right: a mouse whose left button shows Primary and right button Secondary (each with
    its gauge bar), the quick item on the wheel between them (middle click uses it, rolling picks
    another), and on the palm the slots' labels and how many quick items are left."""
    w, split = MOUSE_HUD_W, MOUSE_SPLIT
    hud_box(x, y, w, HUD_BOX_H)
    cx = x + w // 2
    pr.draw_line(cx, y + 1, cx, y + split, HUD_EDGE)  # the button divider
    pr.draw_line(x + HUD_PAD, y + split, x + w - HUD_PAD, y + split, HUD_EDGE)
    inner = cx - WHEEL_W // 2 - 1 - (x + HUD_PAD)  # a button's width between the trim and the wheel
    for hand, bx in ((RIGHT, x + HUD_PAD), (LEFT, cx + WHEEL_W // 2 + 2)):
        mouse_button(player, hand, bx, y, inner)
    wheel(player, cx, y + HUD_PAD + 1, split - 2 * HUD_PAD - 2)

    ly = y + HUD_BOX_H - HUD_PAD - tinyfont.MICRO_HEIGHT
    dim = color(120, 100, 64)
    two = player.inventory.two_handing()
    micro_centered(BUTTON_LABELS[RIGHT], x + HUD_PAD + inner // 2, ly, DIM)
    micro_centered(BUTTON_LABELS[LEFT], x + w - HUD_PAD - inner // 2, ly, dim if two else DIM)
    n = player.inventory.count(player.quick)
    micro_centered(f"X{n}", cx, ly, TEXT if n else color(200, 80, 70))


def mouse_button(player, hand, x, y, w):
    """One button, `w` wide from `x`: its gauge bar along the top, what the slot holds below."""
    two_handed = hand == LEFT and player.inventory.two_handing()
    bx, bw = x + 1, w - 2
    by = y + HUD_PAD + 2
    cx, cy = x + w // 2, y + HUD_PAD + 15
    item = player.hand_item(hand)
    t = pr.get_time()
    pulse = None
    if two_handed:
        # The other half of a two-hander, dimmed: only the left button swings it.
        weapon_icon(item, cx, cy, t, 70)
    elif item.kind == "shield":
        up = player.guarding
        gauge_bar(bx, by, bw, player.stamina.value if up else 0, STAMINA_RGB)
        shield_icon(item, cx, cy, 110 if player.guard_break_t > 0 else 255, up)
    elif item.kind == "spell":
        spell = player.current_spell()
        g = player.magic_gauge
        gauge_bar(bx, by, bw, g.value if spell else 0, FOCUS_RGB if g.full else FOCUS_CHARGING_RGB)
        if spell:
            spell_icon(spell.id, cx, cy, t, 255 if g.full else 110)
            pulse = g
        else:
            pr.draw_ring(pr.Vector2(cx, cy), 4, 6, 0, 360, 24, color(60, 56, 48))
    else:
        g = player.gauge(hand)
        gauge_bar(bx, by, bw, g.value, ATK_RGB if g.full else ATK_CHARGING_RGB)
        charge_bar(player, hand, bx, by, bw)
        weapon_icon(item, cx, cy, t, 255 if g.full else 110, g.full)
        pulse = g
    if pulse is not None and pulse.full and pulse.full_t < SLOT_PULSE:
        # The button flashes once when its gauge fills.
        k = pulse.full_t / SLOT_PULSE
        edge = color(255, 250, 230, rround(230 * (1 - k)))
        pr.draw_rectangle_lines(x - 1, by - 2, w + 2, MOUSE_SPLIT - HUD_PAD - 1, edge)


def wheel(player, cx, top, h):
    """The scroll wheel: the selected quick item between up/down chevrons."""
    item = player.quick_item()
    n = player.inventory.count(item.id)
    hud_box(cx - WHEEL_W // 2, top, WHEEL_W, h, fill=color(0, 0, 0, 220), radius=HUD_INNER_RADIUS)
    chev = color(150, 120, 70)
    pr.draw_triangle(pr.Vector2(cx, top + 2), pr.Vector2(cx - 2, top + 4), pr.Vector2(cx + 2, top + 4), chev)
    bottom = top + h - 2
    pr.draw_triangle(
        pr.Vector2(cx - 2, bottom - 2), pr.Vector2(cx, bottom), pr.Vector2(cx + 2, bottom - 2), chev
    )
    item_icon(item.id, cx, top + h // 2, pr.get_time(), 255 if n else 90)


def gauge_bar(x, y, w, frac, rgb, track=(40, 34, 26)):
    pr.draw_rectangle(x - 1, y - 1, w + 2, 5, color(0, 0, 0, 220))
    pr.draw_rectangle(x, y, w, 3, color(*track))
    pr.draw_rectangle(x, y, rround(w * clamp(frac, 0, 1)), 3, color(*rgb))


def charge_bar(player, hand, x, y, w):
    """While the attack button is held: an orange bar fills over the gauge towards a heavy attack
    and pulses once it is ready. Dim red when there is not enough ST for one."""
    if player.charge_hand != hand or player.swinging or player.charge_t < CHARGE_SHOW:
        return
    if not player.can_heavy(hand):
        pr.draw_rectangle(x, y, w, 3, color(*WINDED_RGB))
        return
    k = player.charge_frac
    pr.draw_rectangle(x, y, rround(w * k), 3, color(*HEAVY_RGB))
    if k >= 1:
        pulse = 0.5 + 0.5 * math.sin(player.charge_t * 18)
        pr.draw_rectangle(x - 1, y - 1, w + 2, 5, color(255, 220, 150, rround(140 * pulse)))


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
    """The weapon on a mouse button: each weapon its own small glyph drawn from primitives
    (`WEAPON_ICONS`, falling back to its category's), most with a touch of motion. Glyphs lie on
    the diagonal, grip bottom left and point top right, within `ICON_REACH` of the centre."""
    draw = WEAPON_ICONS.get(item.id) or CATEGORY_ICONS.get(item.category, _icon_rusted_sword)
    draw(cx, cy, t, int(alpha), ready)


ICON_REACH = 9  # pixels from the button's centre a weapon glyph may reach


def _line(cx, cy, p, q, w, col):
    pr.draw_line_ex(pr.Vector2(cx + p[0], cy + p[1]), pr.Vector2(cx + q[0], cy + q[1]), w, col)


def _poly(cx, cy, pts, w, col):
    for p, q in itertools.pairwise(pts):
        _line(cx, cy, p, q, w, col)


def _dot(cx, cy, dx, dy, col, w=1, h=1):
    pr.draw_rectangle(rround(cx + dx), rround(cy + dy), w, h, col)


def _tri(cx, cy, p, q, s, col):
    """A filled triangle in either winding (raylib only fills one)."""
    if (q[0] - p[0]) * (s[1] - p[1]) - (q[1] - p[1]) * (s[0] - p[0]) > 0:
        q, s = s, q
    pr.draw_triangle(
        pr.Vector2(cx + p[0], cy + p[1]),
        pr.Vector2(cx + q[0], cy + q[1]),
        pr.Vector2(cx + s[0], cy + s[1]),
        col,
    )


def _along(pts, k):
    """The point a share `k` (0..1) of the way along the polyline `pts`."""
    lengths = [math.dist(p, q) for p, q in itertools.pairwise(pts)]
    left = k * sum(lengths)
    for (p, q), n in zip(itertools.pairwise(pts), lengths, strict=True):
        if left <= n:
            f = left / n if n else 0
            return p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f
        left -= n
    return pts[-1]


def _glint(cx, cy, pts, t, a, rgb=(255, 255, 240), speed=0.6):
    """A bright pixel sweeping along `pts` (base to point), then resting a while."""
    k = (t * speed) % 1.5
    if k < 1:
        x, y = _along(pts, k)
        _dot(cx, cy, x, y, color(*rgb, a))


def _diag(g, n):
    """`n` pixels from guard offset `g` along the blade's diagonal (up and to the right)."""
    return (g + n, -g - n)


def _sword(
    cx,
    cy,
    t,
    a,
    ready,
    *,
    grip,
    length,
    width,
    steel,
    guard,
    guard_w,
    guard_rgb,
    wrap,
    pommel,
    pommel_rgb,
    start=-7,
):
    """A straight sword on the diagonal: pommel at `start` (the bottom-left corner), the guard
    across the blade's root, the point toward the top right. Returns the blade's (base, tip)."""
    g = start + grip + 1  # the guard's offset along the diagonal: (g, -g)
    root, tip = (g, -g), _diag(g, length)
    steel_c = color(*steel, a)
    _line(cx, cy, root, tip, width, steel_c)
    _line(cx, cy, root, (g - grip, -g + grip), 2, color(*wrap, a))
    gc = color(*guard_rgb, a)
    end1, end2 = (g - guard_w, -g - guard_w), (g + guard_w, -g + guard_w)
    _line(cx, cy, end1, end2, 2, gc)
    if guard == "droop":  # the quillons bend down toward the grip
        _dot(cx, cy, end1[0] - 1, end1[1] + 1, gc)
        _dot(cx, cy, end2[0] - 1, end2[1] + 1, gc)
    elif guard == "quatrefoil":  # a ring of lobes at each quillon's end
        pr.draw_circle_lines(rround(cx + end1[0]), rround(cy + end1[1]), 1.5, gc)
        pr.draw_circle_lines(rround(cx + end2[0]), rround(cy + end2[1]), 1.5, gc)
    elif guard == "flared":  # the quillons sweep up toward the point
        _dot(cx, cy, end1[0] + 1, end1[1] - 1, gc)
        _dot(cx, cy, end2[0] + 1, end2[1] - 1, gc)
    pc = color(*pommel_rgb, a)
    px, py = g - grip - 1, -g + grip + 1
    if pommel == "wheel":
        pr.draw_circle(rround(cx + px), rround(cy + py), 1.5, pc)
    else:
        _dot(cx, cy, px - 1, py - 1, pc, 2, 2)
    if ready:
        _glint(cx, cy, [_diag(g, 1), _diag(g, length - 1)], t, a)
    return root, tip


def _icon_fists(cx, cy, t, a, ready):
    skin = color(200, 150, 110, a)
    pr.draw_rectangle(cx - 4, cy - 1, 8, 5, skin)
    for i in range(4):
        pr.draw_rectangle(cx - 4 + i * 2, cy - 4, 2, 3, skin)
        pr.draw_rectangle(cx - 4 + i * 2, cy - 4, 1, 1, color(240, 200, 160, a))
    pr.draw_rectangle(cx + 4, cy - 1, 2, 3, skin)


def _icon_rusted_sword(cx, cy, t, a, ready):
    """Short and dull, rust creeping up from the guard and a nick near the point."""
    _sword(
        cx,
        cy,
        t,
        a,
        False,
        grip=3,
        length=9,
        width=2,
        steel=(150, 138, 122),
        guard="bar",
        guard_w=3,
        guard_rgb=(110, 92, 74),
        wrap=(96, 66, 44),
        pommel="stopper",
        pommel_rgb=(110, 92, 74),
    )
    rust = color(150, 84, 50, a)
    for n in (2, 3, 6):
        x, y = _diag(-3, n)
        _dot(cx, cy, x, y, rust)
    x, y = _diag(-3, 7)
    _dot(cx, cy, x + 1, y + 1, color(30, 24, 20, a))  # the nick
    if ready:
        _glint(cx, cy, [_diag(-3, 1), _diag(-3, 8)], t, a, (200, 190, 170), 0.4)


def _icon_ashblade(cx, cy, t, a, ready):
    """Grey iron with an ember near the point that never quite went out."""
    glow = 0.5 + 0.5 * math.sin(t * 3)
    pr.draw_circle(cx + 4, cy - 4, 3, color(255, 120, 40, rround(a * 0.25 * glow)))
    _sword(
        cx,
        cy,
        t,
        a,
        ready,
        grip=3,
        length=10,
        width=2,
        steel=(215, 215, 225),
        guard="bar",
        guard_w=3,
        guard_rgb=(70, 60, 70),
        wrap=(50, 42, 50),
        pommel="stopper",
        pommel_rgb=(70, 60, 70),
    )
    x, y = _diag(-3, 8)
    _dot(cx, cy, x, y, color(255, rround(120 + 100 * glow), 60, a))


def _icon_bastard_sword(cx, cy, t, a, ready):
    """Long in the blade and the grip, its guard drooping, a wheel pommel."""
    _sword(
        cx,
        cy,
        t,
        a,
        ready,
        grip=4,
        length=10,
        width=2,
        steel=(176, 178, 190),
        guard="droop",
        guard_w=3,
        guard_rgb=(130, 124, 116),
        wrap=(80, 60, 40),
        pommel="wheel",
        pommel_rgb=(130, 124, 116),
    )


def _icon_stormbrand(cx, cy, t, a, ready):
    """Blued steel, flared guard; a white-blue fork of lightning flickers down the blade."""
    _sword(
        cx,
        cy,
        t,
        a,
        ready,
        grip=3,
        length=10,
        width=3,
        steel=(120, 145, 190),
        guard="flared",
        guard_w=3,
        guard_rgb=(100, 110, 135),
        wrap=(70, 78, 100),
        pommel="stopper",
        pommel_rgb=(140, 170, 230),
    )
    flick = math.sin(t * 23) + math.sin(t * 37)
    if flick > -0.4:  # out for a moment now and then
        bright = rround(a * min(1.0, 0.55 + 0.3 * flick))
        jag = [(-2 + n + (n % 2), 2 - n + (n % 2)) for n in range(0, 9, 2)]
        _poly(cx, cy, jag, 1, color(215, 230, 255, bright))


def _icon_claymore(cx, cy, t, a, ready):
    """A broad blade, rings at the guard's ends, a wheel pommel."""
    _sword(
        cx,
        cy,
        t,
        a,
        ready,
        grip=3,
        length=10,
        width=3,
        steel=(176, 178, 188),
        guard="quatrefoil",
        guard_w=4,
        guard_rgb=(150, 136, 104),
        wrap=(80, 60, 40),
        pommel="wheel",
        pommel_rgb=(150, 136, 104),
    )


def _icon_zweihander(cx, cy, t, a, ready):
    """The longest blade, a red-wrapped ricasso above the guard and parrying hooks above that."""
    g = -3
    _sword(
        cx,
        cy,
        t,
        a,
        ready,
        grip=4,
        length=10,
        width=3.5,
        steel=(190, 192, 202),
        guard="bar",
        guard_w=4,
        guard_rgb=(150, 136, 104),
        wrap=(60, 50, 44),
        pommel="stopper",
        pommel_rgb=(150, 136, 104),
        start=-8,
    )
    _line(cx, cy, _diag(g, 0), _diag(g, 2), 2.5, color(160, 44, 40, a))
    hx, hy = _diag(g, 3)
    _line(cx, cy, (hx - 2, hy - 2), (hx + 2, hy + 2), 1, color(150, 136, 104, a))


def _katana(cx, cy, t, a, ready, *, grip, blade_pts, width, blade, cord, tsuba, hamon=None, glint=True):
    """A curved blade: a cord-wrapped grip from the bottom-left, a round tsuba, the blade bowing up."""
    root = blade_pts[0]
    end = (root[0] - grip, root[1] + grip)
    _line(cx, cy, end, root, 2, color(36, 28, 34, a))
    for n in range(1, grip, 2):  # the cord's diamonds down the grip
        _dot(cx, cy, root[0] - n, root[1] + n - 1, color(*cord, a))
    _poly(cx, cy, blade_pts, width, color(*blade, a))
    if hamon:
        _poly(cx, cy, [(x - 1, y + 1) for x, y in blade_pts[1:]], 1, color(*hamon, a))
    pr.draw_circle(rround(cx + root[0]), rround(cy + root[1]), 1.5, color(*tsuba, a))
    if ready and glint:
        _glint(cx, cy, blade_pts, t, a)


def _icon_katana(cx, cy, t, a, ready):
    _katana(
        cx,
        cy,
        t,
        a,
        ready,
        grip=4,
        blade_pts=[(-3, 3), (1, -2), (6, -5)],
        width=1.5,
        blade=(220, 224, 234),
        cord=(180, 40, 48),
        tsuba=(200, 170, 70),
    )


def _icon_moonless_tachi(cx, cy, t, a, ready):
    """Dark-lacquered, a pale temper line; a slow sheen comes and goes as it drinks the light."""
    pts = [(-3, 3), (1, -2), (7, -6)]
    _katana(
        cx,
        cy,
        t,
        a,
        ready,
        grip=4,
        blade_pts=pts,
        width=2,
        blade=(70, 72, 92),
        cord=(90, 90, 120),
        tsuba=(60, 60, 80),
        hamon=(150, 156, 180),
        glint=False,
    )
    sheen = 0.5 - 0.5 * math.cos(t * 1.3)
    _poly(cx, cy, pts, 1, color(200, 205, 230, rround(a * 0.55 * sheen)))


def _icon_nodachi(cx, cy, t, a, ready):
    """Taller than a door: the longest curve, a long grip bound in gold cord."""
    _katana(
        cx,
        cy,
        t,
        a,
        ready,
        grip=5,
        blade_pts=[(-3, 3), (2, -3), (8, -8)],
        width=2,
        blade=(214, 216, 226),
        cord=(210, 180, 80),
        tsuba=(150, 130, 60),
    )


def _whip(cx, cy, t, a, pts, cord, handle, thorns=None):
    """A handle and a coiled lash whose loose end sways."""
    _line(cx, cy, (-7, 7), (-4, 4), 2, color(*handle, a))
    sway = [(x + math.sin(t * 2.5 + i) * 0.7 * i / len(pts), y) for i, (x, y) in enumerate(pts)]
    _poly(cx, cy, sway, 1.5, color(*cord, a))
    if thorns:
        for p, q in itertools.pairwise(sway[1:]):
            x, y = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            _dot(cx, cy, x + 1, y - 1, color(*thorns, a))


def _icon_leather_whip(cx, cy, t, a, ready):
    _whip(cx, cy, t, a, [(-4, 4), (0, -1), (4, -4), (7, -3), (6, 1), (3, 2)], (160, 116, 72), (80, 54, 34))


def _icon_thornlash(cx, cy, t, a, ready):
    """A briar cord set with iron thorns, coiled tighter."""
    _whip(
        cx,
        cy,
        t,
        a,
        [(-4, 4), (-2, -2), (2, -6), (7, -5), (8, -1), (5, 2), (2, 0)],
        (90, 116, 60),
        (60, 44, 30),
        thorns=(190, 190, 200),
    )


def _icon_mace(cx, cy, t, a, ready):
    _line(cx, cy, (-5, 5), (2, -2), 2, color(110, 74, 44, a))
    pr.draw_circle(cx + 3, cy - 3, 3, color(150, 150, 160, a))
    flanges = ((3, -7), (7, -3), (3, 1), (-1, -3))
    for i, (dx, dy) in enumerate(flanges):
        lit = ready and int(t * 4) % 6 == i  # a glint runs round the flanges
        _dot(cx, cy, dx, dy, color(*((255, 255, 240) if lit else (200, 200, 212)), a))


def _icon_war_hammer(cx, cy, t, a, ready):
    _line(cx, cy, (-5, 6), (3, -2), 2, color(110, 74, 44, a))
    _line(cx, cy, (-1, -6), (7, 2), 5, color(150, 150, 160, a))
    _line(cx, cy, (4, -3), (5, -4), 2, color(200, 200, 210, a))
    if ready:
        _glint(cx, cy, [(5, -6), (8, -3)], t, a)


def _icon_heartwood_maul(cx, cy, t, a, ready):
    """A knotted burl of petrified heartwood on a crooked root haft, moss twinkling in its cracks."""
    _poly(cx, cy, [(-6, 7), (-3, 3), (-2, 1), (1, -1)], 2, color(96, 70, 44, a))
    pr.draw_circle(cx + 3, cy - 3, 4, color(118, 104, 86, a))
    pr.draw_circle(cx + 4, cy - 4, 2, color(140, 126, 104, a))
    for dx, dy in ((1, -2), (5, -1)):
        _dot(cx, cy, dx, dy, color(70, 56, 42, a))  # knots
    for i, (dx, dy) in enumerate(((2, -6), (6, -3), (0, -4))):
        twinkle = 0.55 + 0.45 * math.sin(t * 2.2 + i * 2.1)
        _dot(cx, cy, dx, dy, color(110, 180, 70, rround(a * twinkle)))


def _icon_slagbreaker(cx, cy, t, a, ready):
    """A black banded haft under a slag-crusted head whose cracks pulse hot; heat motes rise."""
    _line(cx, cy, (-6, 7), (2, -1), 2, color(70, 64, 62, a))
    for n in (-4, -1):
        _dot(cx, cy, n, -n, color(130, 126, 124, a))  # iron bands
    _line(cx, cy, (-1, -6), (6, 1), 5, color(78, 66, 60, a))
    _line(cx, cy, (-1, -6), (6, 1), 1, color(40, 34, 32, a))
    heat = 0.6 + 0.4 * math.sin(t * 4)
    hot = color(255, rround(110 + 80 * heat), 40, rround(a * heat))
    _poly(cx, cy, [(1, -4), (3, -3), (4, -1), (6, 0)], 1, hot)
    for i in range(2):
        k = (t * 0.7 + i * 0.5) % 1
        _dot(cx, cy, 2 + 3 * i + math.sin(t * 5 + i), -6 - k * 3, color(255, 170, 70, rround(a * (1 - k))))


def _icon_oak_cudgel(cx, cy, t, a, ready):
    """A knotted length of oak, thickening toward the head."""
    wood = color(130, 92, 58, a)
    _line(cx, cy, (-6, 6), (-1, 1), 2, wood)
    _line(cx, cy, (-1, 1), (3, -3), 3, wood)
    pr.draw_circle(cx + 4, cy - 4, 2.5, wood)
    for dx, dy in ((-3, 3), (1, -1), (4, -5)):
        _dot(cx, cy, dx, dy, color(80, 54, 34, a))


def _icon_spiked_club(cx, cy, t, a, ready):
    """Nails driven through a root-ball."""
    _line(cx, cy, (-5, 5), (4, -4), 3, color(110, 74, 44, a))
    pr.draw_circle(cx + 3, cy - 3, 3.5, color(130, 90, 56, a))
    nails = ((2, -8), (7, -2), (6, -7), (-1, -5), (0, -1), (4, 1))
    for i, (dx, dy) in enumerate(nails):
        lit = ready and int(t * 5) % 9 == i
        _dot(cx, cy, dx, dy, color(*((255, 255, 240) if lit else (170, 170, 180)), a))


def _axe_haft(cx, cy, p, q, a):
    _line(cx, cy, p, q, 2, color(118, 80, 48, a))


def _icon_hatchet(cx, cy, t, a, ready):
    """A short camp axe: a stubby haft and a small head."""
    _axe_haft(cx, cy, (-4, 5), (2, -2), a)
    _tri(cx, cy, (1, -4), (5, -3), (3, 0), color(150, 150, 160, a))
    edge = [(5, -3), (3, 0)]
    _line(cx, cy, *edge, 1, color(220, 220, 230, a))
    if ready:
        _glint(cx, cy, edge, t, a)


def _icon_bearded_axe(cx, cy, t, a, ready):
    """Its long lower edge hooks down past the haft."""
    _axe_haft(cx, cy, (-6, 6), (3, -5), a)
    iron = color(150, 150, 160, a)
    _tri(cx, cy, (1, -5), (6, -6), (7, 1), iron)
    _tri(cx, cy, (1, -5), (7, 1), (3, -1), iron)
    edge = [(6, -6), (7, -2), (6, 2)]
    _poly(cx, cy, edge, 1, color(220, 220, 230, a))
    if ready:
        _glint(cx, cy, edge, t, a)


def _icon_felling_axe(cx, cy, t, a, ready):
    """A long two-handed haft and a deep wedge of a head."""
    _axe_haft(cx, cy, (-7, 7), (4, -5), a)
    _tri(cx, cy, (2, -3), (5, -8), (8, -2), color(150, 150, 160, a))
    edge = [(5, -8), (8, -2)]
    _line(cx, cy, *edge, 1, color(220, 220, 230, a))
    if ready:
        _glint(cx, cy, edge, t, a)


def _icon_butcher_cleaver(cx, cy, t, a, ready):
    """Broad as a shovel, a hole to hang it by, and never quite clean."""
    _line(cx, cy, (-7, 6), (-3, 2), 2, color(90, 60, 40, a))
    pr.draw_rectangle(cx - 3, cy - 6, 10, 7, color(150, 150, 160, a))
    pr.draw_rectangle(cx - 3, cy, 10, 1, color(220, 220, 230, a))  # the edge
    _dot(cx, cy, 4, -4, color(20, 16, 14, a))  # the hang hole
    glisten = 0.6 + 0.4 * math.sin(t * 2)
    blood = color(150, 30, 30, rround(a * glisten))
    _dot(cx, cy, 0, -2, blood, 2, 2)
    _dot(cx, cy, 2, -1, blood)
    if ready:
        _glint(cx, cy, [(-3, 0), (6, 0)], t, a)


WEAPON_ICONS = {
    "fists": _icon_fists,
    "rusted_sword": _icon_rusted_sword,
    "ashblade": _icon_ashblade,
    "bastard_sword": _icon_bastard_sword,
    "stormbrand": _icon_stormbrand,
    "claymore": _icon_claymore,
    "zweihander": _icon_zweihander,
    "katana": _icon_katana,
    "moonless_tachi": _icon_moonless_tachi,
    "nodachi": _icon_nodachi,
    "leather_whip": _icon_leather_whip,
    "thornlash": _icon_thornlash,
    "mace": _icon_mace,
    "war_hammer": _icon_war_hammer,
    "heartwood_maul": _icon_heartwood_maul,
    "slagbreaker": _icon_slagbreaker,
    "oak_cudgel": _icon_oak_cudgel,
    "spiked_club": _icon_spiked_club,
    "hatchet": _icon_hatchet,
    "bearded_axe": _icon_bearded_axe,
    "felling_axe": _icon_felling_axe,
    "butcher_cleaver": _icon_butcher_cleaver,
}
# A weapon without its own glyph borrows its category's.
CATEGORY_ICONS = {
    "fists": _icon_fists,
    "sword": _icon_rusted_sword,
    "greatsword": _icon_claymore,
    "katana": _icon_katana,
    "whip": _icon_leather_whip,
    "mace": _icon_mace,
    "hammer": _icon_war_hammer,
    "club": _icon_oak_cudgel,
    "axe": _icon_hatchet,
}


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
    elif id_ == "thunder":
        # A jagged bolt that flickers, with a white flash now and then.
        flash = (t * 2.3) % 1 < 0.12
        pts = [(cx + 3, cy - 8), (cx - 2, cy - 1), (cx + 2, cy - 1), (cx - 3, cy + 8)]
        rgb = (255, 255, 255) if flash else (190, 220, 255)
        for (x0, y0), (x1, y1) in itertools.pairwise(pts):
            pr.draw_line(x0, y0, x1, y1, color(*rgb, a))
            pr.draw_line(x0 + 1, y0, x1 + 1, y1, color(120, 160, 255, rround(a * 0.7)))
        if flash:
            pr.draw_circle(cx, cy, 6, color(200, 220, 255, rround(a * 0.25)))
    elif id_ == "motes":
        # Three violet sparks circling a common centre, each trailing a glint.
        for i in range(3):
            ang = t * 2.4 + i * 2.094
            for j in range(3):
                b = ang - j * 0.3
                pr.draw_circle(
                    rround(cx + math.cos(b) * 5),
                    rround(cy + math.sin(b) * 5),
                    1.8 - j * 0.5,
                    color(190, 120, 255, rround(a * (1 - j * 0.3))),
                )
        pr.draw_circle(cx, cy, 1.5, color(240, 210, 255, a))
    elif id_ == "ward":
        # A ring of embers wheeling about an ashen core.
        pr.draw_circle(cx, cy, 2.5, color(110, 96, 84, a))
        pr.draw_circle(cx, cy, 1.2, color(255, 200, 120, a))
        for i in range(6):
            ang = t * 1.8 + i * math.tau / 6
            glow = 0.6 + 0.4 * math.sin(t * 6 + i)
            pr.draw_circle(
                rround(cx + math.cos(ang) * 6),
                rround(cy + math.sin(ang) * 6),
                1.4,
                color(245, 165, 80, rround(a * glow)),
            )
    else:
        pr.draw_circle(cx, cy, 4, color(200, 200, 200, a))


COMPASS_TILT = 0.5  # how far we look down onto the ball (radians)


def compass(heading, cx, cy, r=17, target=None):
    """Compass ball that rolls with your heading; the facing sits at the front-center. `target` is
    the heading (degrees) of the nearest living boss's door: an ember marks it on the ball's equator,
    or pinned dim to the rim on the side to turn toward while it is behind you."""
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

    if target is not None:
        boss_marker(project, heading, target, cx, cy, r)

    # Fixed pointer under the ball marks the facing.
    pr.draw_triangle(
        pr.Vector2(cx, cy + r), pr.Vector2(cx - 2, cy + r + 3), pr.Vector2(cx + 2, cy + r + 3), HIGHLIGHT
    )


BOSS_MARK_RGB = (255, 110, 40)


def boss_marker(project, heading, target, cx, cy, r):
    """The ember on the compass toward the boss: it glows hotter the straighter you face it."""
    off = (target - heading + 180) % 360 - 180  # -180..180, positive to your right
    px, py, depth = project(target, 0)
    t = pr.get_time()
    if depth < 0.05:  # behind you: a dim ember on the rim, on the side to turn toward
        side = 1 if off > 0 else -1
        x, y = cx + side * (r + 1), cy
        pr.draw_circle(x, y, 2, color(0, 0, 0, 200))
        pr.draw_circle(x, y, 1.2, color(*BOSS_MARK_RGB, 150))
        return
    ahead = clamp(1 - abs(off) / 30, 0, 1)
    pulse = 0.5 + 0.5 * math.sin(t * (4 + 6 * ahead))
    x, y = rround(px), rround(py)
    pr.draw_circle(x, y, 3 + ahead, color(*BOSS_MARK_RGB, rround(60 + 80 * pulse * (0.4 + 0.6 * ahead))))
    pts = (pr.Vector2(x, y - 3), pr.Vector2(x - 2, y), pr.Vector2(x, y + 3), pr.Vector2(x + 2, y))
    dark = color(60, 16, 6)
    pr.draw_triangle(pts[0], pts[1], pts[2], dark)
    pr.draw_triangle(pts[0], pts[2], pts[3], dark)
    core = color(255, rround(150 + 90 * ahead), rround(60 + 120 * ahead * pulse))
    pr.draw_rectangle(x - 1, y - 1, 2, 2, core)
    pr.draw_rectangle(x, y - 2, 1, 4, core)


GOLD_RGB = (235, 190, 80)
GOLD_H = 2 * HUD_PAD + 7  # the coin (and the 6 px caps under TEXT_DY) between the box's pads


def gold_counter(game):
    """Top right: the purse, like a soul counter. A fresh gain hangs under it as "+N", then counts in."""
    tally = game.gold_tally
    label = str(tally.shown)
    w = HUD_PAD + 7 + 1 + smallfont.width(label) + HUD_PAD  # coin, gap, number
    x, y = W - HUD_MARGIN - w, HUD_MARGIN
    hud_box(x, y, w, GOLD_H)
    coin(x + HUD_PAD + 3, y + GOLD_H // 2)
    small(label, x + HUD_PAD + 8, y + HUD_PAD + TEXT_DY, HIGHLIGHT)
    a = tally.gain_alpha()
    if a > 0:
        gain = f"+{tally.shown_gain}"
        gx = W - HUD_MARGIN - HUD_PAD - smallfont.width(gain)
        small(gain, gx, y + GOLD_H + HUD_GAP + TEXT_DY, color(*GOLD_RGB, rround(255 * a)))


def coin(cx, cy):
    """A 7 px gold coin with a dark rim and a glint."""
    pr.draw_circle(cx, cy, 3, color(120, 80, 20))
    pr.draw_circle(cx, cy, 2, color(*GOLD_RGB))
    pr.draw_rectangle(cx - 1, cy - 2, 1, 1, color(255, 245, 200))


BOSS_BAR_W = 168


def boss_bar(game):
    world = game.world
    if not world:
        return
    awake = [e for e in world.enemies if e.type.boss and e.alive and e.state not in ("idle", "perched")]
    for i, boss in enumerate(awake[:2]):  # twin bosses get a bar each, one under the other
        _boss_bar(boss, i * BOSS_BAR_STEP)


BOSS_BAR_H = 5
BOSS_BOX_H = 2 * HUD_PAD + 2 + smallfont.HEIGHT + HUD_GAP + BOSS_BAR_H  # name over bar, inside the pads
BOSS_BAR_STEP = BOSS_BOX_H + HUD_GAP  # pixels between stacked boss bars


def _boss_bar(boss, dy):
    max_hp = boss.type.hp
    bw, bh = BOSS_BAR_W, BOSS_BAR_H
    top = HUD_MARGIN + dy
    name_y = top + HUD_PAD + 1
    x, y = W // 2 - bw // 2, name_y + smallfont.HEIGHT + HUD_GAP
    hud_box(x - 2 * HUD_PAD, top, bw + 4 * HUD_PAD, BOSS_BOX_H)
    small_centered(boss.name, W // 2, name_y + TEXT_DY, HIGHLIGHT)
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
        y = MESSAGE_Y - (len(lines) - 1 - i) * smallfont.LINE
        base, hi = color(230, 220, 190, alpha), color(*HIGHLIGHT_RGB, alpha)
        small_marked_centered(msg, W // 2, y + TEXT_DY, base, hi)


def prompt(game):
    label = game.focus_label()
    if label:
        small_centered(label, W // 2, PROMPT_Y + TEXT_DY, HIGHLIGHT)


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


DIALOGUE_H = 56
DIALOGUE_Y = H - HUD_MARGIN - HUD_BOX_H - HUD_GAP - DIALOGUE_H  # just above the bottom HUD boxes
DIALOGUE_X, DIALOGUE_W = HUD_MARGIN, W - 2 * HUD_MARGIN  # as wide as the bottom row it sits on
PANEL_PAD = 8  # text inset in menus and dialogue panels (list_menu, Belongings, the speaker's box)


def dialogue(speaker, line, page, pages):
    """The speaker's box, sitting just above the bottom HUD boxes so it never covers them."""
    x, y, w = DIALOGUE_X, DIALOGUE_Y, DIALOGUE_W
    panel(x, y, w, DIALOGUE_H)
    text(speaker, x + PANEL_PAD, y + 5, HIGHLIGHT)
    for i, l in enumerate(wrap(line, w - 2 * PANEL_PAD)):
        text(l, x + PANEL_PAD, y + 18 + i * 11)
    page_mark = f"{page + 1}/{pages}"
    text(page_mark, x + w - PANEL_PAD - measure(page_mark), y + 45, DIM)


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
