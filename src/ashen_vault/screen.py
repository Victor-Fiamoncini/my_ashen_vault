"""Internal resolution and camera constants shared by the game and the UI,
plus the raylib-free maths for mapping the mouse onto menus."""

W = 320
H = 240
FOV = 62.0
PREVIEW = 64  # inventory item preview size in pixels

ROW_H = 11  # height of a ui.list_menu row
ROW_TOP = 20  # first list_menu row, relative to the panel top
LIST_ROWS = 11  # rows a full-height list_menu shows before it scrolls

# Belongings and the shop: every panel stands MENU_SPACE from the screen's edge and from its
# neighbours (the in-game HUD's margin), so the gaps match all round. The item list sits beside a
# column holding Equipped over the stats, both as tall as that column; the item panel fills the rest.
MENU_SPACE = 3
SIDE_W = 136  # the right column: Equipped and the stats
EQUIPPED_H = ROW_TOP + 4 * ROW_H + 3  # the title, four slots and the bottom pad
STATS_ROW = 10  # the stats panel's line pitch
STATS_H = 7 * STATS_ROW + 9  # seven lines, padded like Equipped above and below
COLUMN_H = EQUIPPED_H + MENU_SPACE + STATS_H  # the list's height too, so both end level
SIDE_X = W - MENU_SPACE - SIDE_W
MENU_LIST = (MENU_SPACE, MENU_SPACE, SIDE_X - 2 * MENU_SPACE)  # (x, y, width) of the Belongings list
SHOP_LIST = (MENU_SPACE, MENU_SPACE, W - 2 * MENU_SPACE)
EQUIPPED_PANEL = (SIDE_X, MENU_SPACE, SIDE_W)
STATS_PANEL = (SIDE_X, MENU_SPACE + EQUIPPED_H + MENU_SPACE, SIDE_W)
ITEM_Y = MENU_SPACE + COLUMN_H + MENU_SPACE
ITEM_PANEL = (MENU_SPACE, ITEM_Y, W - 2 * MENU_SPACE, H - MENU_SPACE - ITEM_Y)  # (x, y, w, h)


def to_internal(mx, my, sw, sh):
    """Window pixel -> 320x240 pixel, undoing the letterboxed scale in Game.render().
    Returns None when the point lies in the black bars."""
    scale = min(sw / W, sh / H)
    ox = (sw - W * scale) / 2
    oy = (sh - H * scale) / 2
    x = (mx - ox) / scale
    y = (my - oy) / scale
    if not (0 <= x < W and 0 <= y < H):
        return None
    return x, y


def list_row_at(x, y, w, n, px, py, first=0, visible=None):
    """Index of the ui.list_menu row under (px, py), or None. `first` is the first row shown when the
    list scrolls, `visible` how many rows fit."""
    top = y + ROW_TOP - 1
    if not (x <= px < x + w) or py < top:
        return None
    shown = n - first if visible is None else min(n - first, visible)
    i = int((py - top) // ROW_H)
    return first + i if i < shown else None


def scroll_into_view(first, selected, n, visible=LIST_ROWS):
    """The first row to show so `selected` stays on screen, moving the view as little as possible."""
    if n <= visible:
        return 0
    first = min(first, selected)
    first = max(first, selected - visible + 1)
    return max(0, min(first, n - visible))


def centered_row_at(cx, y0, step, n, half_w, px, py):
    """Index of a centred text row (rows at y0 + i*step) under (px, py), or None."""
    top = y0 - 2
    if abs(px - cx) > half_w or py < top:
        return None
    i = int((py - top) // step)
    return i if i < n else None
