"""2D drawing at the 320x240 internal resolution."""
import math

import pyray as pr

from ashen_vault.screen import W, H
from ashen_vault.util import rround, clamp


def color(r, g, b, a=255):
    return pr.Color(int(r), int(g), int(b), int(a))


TEXT = color(220, 210, 180)
DIM = color(140, 130, 110)
SHADOW = color(0, 0, 0, 200)
PANEL = color(10, 8, 6, 210)
BORDER = color(120, 100, 70)
HIGHLIGHT = color(255, 220, 140)


def measure(s, size=10):
    return pr.measure_text(s, size)


def text(s, x, y, col=TEXT, size=10):
    x, y = int(x), int(y)
    pr.draw_text(s, x + 1, y + 1, size, SHADOW)
    pr.draw_text(s, x, y, size, col)


def text_centered(s, cx, y, col=TEXT, size=10):
    text(s, cx - measure(s, size) // 2, y, col, size)


def panel(x, y, w, h):
    pr.draw_rectangle(x, y, w, h, PANEL)
    pr.draw_rectangle_lines(x, y, w, h, BORDER)


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


def hud(game):
    p = game.player
    s = p.stats

    # Vitals: a small block in the bottom-left corner.
    pr.draw_rectangle(4, H - 31, 108, 27, color(0, 0, 0, 110))
    text("HP", 8, H - 28, color(230, 120, 110))
    bar(26, H - 26, 54, 4, s.hp / s.max_hp, (190, 40, 40))
    text(str(s.hp), 84, H - 28, DIM)
    text("MP", 8, H - 16, color(120, 150, 230))
    bar(26, H - 14, 54, 4, s.mp / s.max_mp, (50, 80, 200))
    text(str(s.mp), 84, H - 16, DIM)

    # Gauges flank the compass ball in the bottom-right corner.
    cx = W - 25
    cy = H - 25
    gauge(cx - 31, cy - 12, p.attack_gauge.value, (240, 210, 90), (150, 120, 50))
    gauge(cx - 25, cy - 12, p.magic_gauge.value, (120, 220, 240), (60, 110, 130))
    compass(p.heading, cx, cy)
    spell = p.current_spell()
    label = f"{spell.name} {spell.cost}" if spell else "No spell"
    text(label, W - 8 - measure(label), cy - 34, DIM if spell else color(90, 84, 72))
    if p.sprinting:
        text("SPRINT", 8, H - 42, DIM)

    boss_bar(game)
    messages(game)
    prompt(game)
    flash(p)


def gauge(x, y, frac, full_rgb, fill_rgb):
    """Thin vertical gauge that brightens when full (gold = ATK, cyan = MAG)."""
    pr.draw_rectangle(x - 1, y - 1, 5, 26, color(0, 0, 0, 220))
    fill = rround(24 * clamp(frac, 0, 1))
    pr.draw_rectangle(x, y + 24 - fill, 3, fill, color(*(full_rgb if frac >= 1 else fill_rgb)))


COMPASS_TILT = 0.5  # how far we look down onto the ball (radians)


def compass(heading, cx, cy, r=17):
    """Compass ball that rolls with your heading; the facing sits at the front-center."""
    pr.draw_circle(cx, cy, r + 2, color(0, 0, 0, 210))
    # Fake sphere shading: stacked discs drifting toward the light (upper left).
    for i in range(7):
        k = i / 6.0
        pr.draw_circle(cx - rround(k * r * 0.35), cy - rround(k * r * 0.4), r * (1 - k * 0.8),
                       color(rround(70 + k * 120), rround(58 + k * 105), rround(40 + k * 80)))

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
        alpha = rround(clamp(60 + depth * 260, 0, 255))
        rgb = (200, 30, 24) if label == "N" else (36, 24, 12)
        pr.draw_text(label, rround(px) - measure(label) // 2, rround(py) - 5, 10, color(*rgb, alpha))

    # Fixed pointer under the ball marks the facing.
    pr.draw_triangle(pr.Vector2(cx, cy + r), pr.Vector2(cx - 3, cy + r + 5), pr.Vector2(cx + 3, cy + r + 5),
                     HIGHLIGHT)


def boss_bar(game):
    world = game.world
    if not world:
        return
    boss = next((e for e in world.enemies if e.type.boss and e.alive and e.state != "idle"), None)
    if not boss:
        return
    text_centered(boss.name, W // 2, 20, color(230, 180, 150))
    bar(W // 2 - 80, 32, 160, 4, boss.hp / boss.type.hp, (170, 40, 30))


def messages(game):
    lines = game.messages[-3:]
    for i, (msg, age) in enumerate(lines):
        alpha = rround(clamp(255 * (5 - age), 0, 255)) if age > 4 else 255
        if alpha <= 0:
            continue
        text_centered(msg, W // 2, H - 58 - (len(lines) - 1 - i) * 11, color(230, 220, 190, alpha))


def prompt(game):
    label = game.focus_label()
    if label:
        text_centered(label, W // 2, 140, HIGHLIGHT)


def flash(player):
    if player.hurt_t <= 0:
        return
    pr.draw_rectangle(0, 0, W, H, color(160, 0, 0, rround(clamp(player.hurt_t * 300, 0, 120))))


def dialogue(speaker, line, page, pages):
    panel(10, 150, 300, 56)
    text(speaker, 18, 155, HIGHLIGHT)
    for i, l in enumerate(wrap(line, 284)):
        text(l, 18, 168 + i * 11)
    text(f"{page + 1}/{pages}", 284, 195, DIM)


def list_menu(title, x, y, w, rows, selected, footer=None):
    """rows are tuples (label, right=None, dim=False)."""
    height = 22 + max(len(rows), 1) * 11 + (12 if footer else 0)
    panel(x, y, w, height)
    text(title, x + 8, y + 5, HIGHLIGHT)
    if not rows:
        text("(empty)", x + 12, y + 20, DIM)
    for i, row in enumerate(rows):
        label = row[0]
        right = row[1] if len(row) > 1 else None
        dim = row[2] if len(row) > 2 else False
        col = HIGHLIGHT if i == selected else (DIM if dim else TEXT)
        text(">" if i == selected else " ", x + 4, y + 20 + i * 11, col)
        text(label, x + 12, y + 20 + i * 11, col)
        if right is not None:
            rs = str(right)
            text(rs, x + w - 8 - measure(rs), y + 20 + i * 11, col)
    if footer:
        text(footer, x + 8, y + height - 13, DIM)
