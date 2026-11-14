"""Raylib-free UI logic: message markup, the small pixel font and the shrine rest fog."""

import pathlib
import re

import pytest

from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.player.items import Items
from ashen_vault.player.spells import Spells
from ashen_vault.ui import smallfont
from ashen_vault.util import highlight_runs, plain
from ashen_vault.world import rest
from ashen_vault.world.world import FALL_MESSAGES, HAZARD_MESSAGES

SRC = pathlib.Path(__file__).resolve().parent.parent / "src" / "ashen_vault"


# --- markup ---------------------------------------------------------------------------


def test_plain_message_is_one_run():
    assert highlight_runs("The door grinds open.") == [("The door grinds open.", False)]


def test_braces_mark_highlighted_spans():
    assert highlight_runs("Found {Red Tonic x2} and {30 gold}.") == [
        ("Found ", False),
        ("Red Tonic x2", True),
        (" and ", False),
        ("30 gold", True),
        (".", False),
    ]
    assert plain("Found {Red Tonic x2} and {30 gold}.") == "Found Red Tonic x2 and 30 gold."


def test_unclosed_brace_and_empty_span_stay_plain():
    assert highlight_runs("odd {brace") == [("odd {brace", False)]
    assert highlight_runs("a{}b") == [("a", False), ("b", False)]
    assert highlight_runs("") == []


# --- small font -----------------------------------------------------------------------


def test_glyph_rows_are_rectangular_and_sized():
    for ch, rows in smallfont.GLYPHS.items():
        assert 6 <= len(rows) <= 8, ch
        assert len({len(r) for r in rows}) == 1, ch
        assert set("".join(rows)) <= {"#", "."}, ch
        assert len(rows) <= smallfont.HEIGHT < smallfont.LINE


def test_width_and_rects():
    assert smallfont.width("") == 0
    assert smallfont.width("A") == 4
    assert smallfont.width("Ai") == 4 + smallfont.GAP + 1
    runs = list(smallfont.rects("i", 10, 20))
    assert (10, 20, 1, 1) in runs and (10, 21, 1, 1) not in runs  # the dot, then a gap
    # The A's crossbar is one 4 px run on its fourth row.
    assert (0, 3, 4, 1) in list(smallfont.rects("A", 0, 0))
    # Unknown characters fall back to '?'.
    assert list(smallfont.rects("☃", 0, 0)) == list(smallfont.rects("?", 0, 0))


def _game_texts():
    """Every fixed string the HUD draws in the small font, plus the names that fill f-strings."""
    texts = [i.name for i in Items.ALL.values()]
    texts += [t.name for t in EnemyTypes.ALL.values()]
    texts += [t.epitaph for t in EnemyTypes.ALL.values() if t.epitaph]
    texts += [s.name for s in Spells.ALL.values()]
    texts += list(FALL_MESSAGES.values()) + list(HAZARD_MESSAGES.values())
    for path in SRC.rglob("*.py"):
        for f, body in re.findall(r'message\((f?)"([^"]*)"', path.read_text(encoding="utf-8")):
            if f:  # drop the {placeholders}; the names that fill them are listed above
                body = re.sub(r"\{[^{}]*\}", "", body.replace("{{", "").replace("}}", ""))
            texts.append(body)
    return texts


def test_small_font_covers_every_game_message():
    missing = {ch for t in _game_texts() for ch in plain(t) if ch not in smallfont.GLYPHS}
    assert not missing


def _menu_texts():
    """What menus, dialogue, the title, death and ending screens draw: every string literal with a
    space in dialogue.py, the menu tables, and literal ui.text / ui.list_menu / footer strings."""
    import ast

    from ashen_vault import dialogue, game
    from ashen_vault.input import CONTROLS

    texts = [*game.ENDING, *game.PAUSE_OPTIONS, *dialogue.SHOP_NAMES.values()]
    texts += [t for row in CONTROLS for t in row]
    tree = ast.parse((SRC / "dialogue.py").read_text())
    texts += [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "\n" not in n.value  # not docstrings
    ]
    src = (SRC / "game.py").read_text()
    texts += re.findall(r'ui\.(?:text|text_centered|list_menu)\(\s*f?"([^"{\n]*)', src)
    texts += re.findall(r'"([^"{\n]*(?:Enter|Esc|Click|click)[^"{\n]*)"', src)
    texts += ["> New Game <"]  # the title's cursor
    return [t for t in texts if " " in t]


def test_small_font_covers_every_menu_and_dialogue_line():
    missing = {ch for t in _menu_texts() for ch in plain(t) if ch not in smallfont.GLYPHS}
    assert not missing


def test_logo_font_spells_the_headings():
    from ashen_vault.ui import logofont

    for s in ("ASHEN VAULT", "YOU HAVE FALLEN"):
        assert all(ch == " " or ch in logofont.FONT for ch in s)
    assert all(len(rows) == logofont.HEIGHT for rows in logofont.FONT.values())
    assert all(len({len(r) for r in rows}) == 1 for rows in logofont.FONT.values())
    assert set(logofont.FONT) >= set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    # Spaces advance like the SVG logo's (4 glyph pixels), letters by their width plus the gap.
    assert logofont.width("A A", 2) == (5 + 1 + 3 + 1 + 5) * 2
    assert logofont.width("", 3) == 0
    assert list(logofont.rects(" ", 0, 0)) == []
    assert len(list(logofont.rects("I", 0, 0, 3))) == sum(r.count("#") for r in logofont.FONT["I"])


# --- shrine rest ----------------------------------------------------------------------


def test_rest_density_rises_holds_and_clears():
    assert rest.density(0) == 0
    assert rest.density(1) == 0
    assert rest.density(0.5) == 1
    assert rest.density(rest.PEAK) == 1
    assert 0 < rest.density(0.2) < rest.density(0.3) < 1


def test_rest_sequence_peaks_once_then_finishes():
    seq = rest.RestSequence(duration=1.0)
    peaks = [seq.update(0.05) for _ in range(30)]
    assert peaks.count(True) == 1
    assert peaks.index(True) == pytest.approx(rest.PEAK / 0.05 - 1, abs=1)
    assert seq.done
    assert seq.t == 1.0
    assert seq.density == 0


def test_cell_alpha_is_bounded_and_grows_with_density():
    assert rest.cell_alpha(5, 5, 0.0, 0.0) == 0
    for cx, cy in ((0, 0), (40, 30), (79, 59), (13, 7)):
        prev = 0.0
        for d in (0.1, 0.3, 0.5, 0.7, 0.9, 1.0):
            a = rest.cell_alpha(cx, cy, 1.3, d)
            assert 0 <= a <= 1
            assert a >= prev
            prev = a
        assert prev == 1.0  # full density covers every cell


def test_fog_rises_from_the_bottom():
    def cover(row):
        return sum(rest.cell_alpha(cx, row, 0.0, 0.35) for cx in range(rest.COLS))

    assert cover(rest.ROWS - 1) > cover(0)


def test_fog_pixels():
    empty = rest.fog_pixels(0.0, 0.0)
    assert len(empty) == rest.COLS * rest.ROWS * 4
    assert not any(empty)
    full = rest.fog_pixels(0.5, 1.0)
    assert all(full[i + 3] == 255 for i in range(0, len(full), 4))


# --- HUD layout -----------------------------------------------------------------------


def test_hud_boxes_fit_the_screen_without_overlapping():
    """The vitals box and the mouse share the bottom row; messages, the prompt and dialogue sit above
    them, never over them (a taller HUD once pushed the dialogue box onto the slots)."""
    from ashen_vault.screen import H, W
    from ashen_vault.ui import hud, smallfont, tinyfont

    m = hud.HUD_MARGIN
    mouse_x = W - m - hud.MOUSE_HUD_W
    assert mouse_x > m + hud.VITALS_W  # mouse right of the vitals box
    row_top = H - m - hud.HUD_BOX_H
    assert hud.DIALOGUE_Y >= 0 and row_top - hud.HUD_GAP == hud.DIALOGUE_Y + hud.DIALOGUE_H
    assert row_top - hud.HUD_GAP == hud.MESSAGE_Y + smallfont.HEIGHT
    assert hud.PROMPT_Y + smallfont.HEIGHT < hud.MESSAGE_Y - 2 * smallfont.LINE  # above the messages
    assert m == hud.DIALOGUE_X and W - m == hud.DIALOGUE_X + hud.DIALOGUE_W
    # The boss bar and the gold counter hang from the same top margin.
    assert hud.BOSS_BAR_STEP == hud.BOSS_BOX_H + hud.HUD_GAP
    # The vitals' numbers end before the compass's shadow begins.
    vx = m + hud.HUD_PAD + 1
    left = vx + hud.VITAL_NUM_X + tinyfont.width("100")
    right = m + hud.VITALS_W - hud.HUD_PAD - 1
    assert right - left >= 2 * (hud.COMPASS_R + 2)
    # Each button's label fits its half of the mouse in the micro font, as do the quick count's.
    button = (hud.MOUSE_HUD_W - hud.WHEEL_W) // 2 - hud.HUD_PAD
    assert all(tinyfont.width(label) <= button for label in hud.BUTTON_LABELS.values())
    assert all(ch in tinyfont.MICRO for label in hud.BUTTON_LABELS.values() for ch in label)
    assert all(ch in tinyfont.MICRO for ch in "X0123456789")  # the quick item's count


def test_gold_tally_starts_settled():
    from ashen_vault.ui.tally import GoldTally

    t = GoldTally(250)
    t.update(250, 0.1)
    assert (t.shown, t.gain, t.gain_alpha()) == (250, 0, 0.0)


def test_gold_tally_holds_a_gain_then_counts_it_in():
    from ashen_vault.ui.tally import FADE_TIME, GAIN_HOLD, ROLL_TIME, GoldTally

    t = GoldTally(100)
    t.update(140, 0.0)
    assert (t.shown, t.gain, t.shown_gain, t.gain_alpha()) == (100, 40, 40, 1.0)
    t.update(140, GAIN_HOLD - 0.1)
    assert t.shown == 100  # still held
    t.update(140, 0.1 + ROLL_TIME / 2)
    assert 100 < t.shown < 140 and t.shown + t.gain == 140
    t.update(140, ROLL_TIME)
    assert (t.shown, t.gain) == (140, 0)
    assert 0 < t.gain_alpha() <= 1  # the "+40" fades out
    t.update(140, FADE_TIME + 0.01)
    assert t.gain_alpha() == 0


def test_gold_tally_adds_gains_in_a_row():
    from ashen_vault.ui.tally import GAIN_HOLD, ROLL_TIME, GoldTally

    t = GoldTally(0)
    t.update(10, 0.5)
    t.update(25, 0.5)
    assert (t.shown, t.gain, t.shown_gain) == (0, 25, 25)
    t.update(25, GAIN_HOLD + ROLL_TIME)
    assert t.shown == 25


def test_gold_tally_shows_spending_at_once():
    from ashen_vault.ui.tally import GoldTally

    t = GoldTally(100)
    t.update(130, 0.2)
    t.update(60, 0.0)
    assert (t.shown, t.gain, t.gain_alpha()) == (60, 0, 0.0)


def test_gold_tally_alpha_stays_in_range_when_rounding_finishes_early():
    """A small gain can round all the way in before the roll's time is up; the "+N" fade must still
    start from 1 (it once went above 1 and overflowed the colour byte)."""
    from ashen_vault.ui.tally import GAIN_HOLD, GoldTally

    t = GoldTally(0)
    t.update(3, 0.0)
    t.update(3, GAIN_HOLD)
    for _ in range(200):
        t.update(3, 1 / 144)  # uneven real frame times
        assert 0.0 <= t.gain_alpha() <= 1.0
    assert (t.shown, t.gain, t.gain_alpha()) == (3, 0, 0.0)


def test_hud_box_corners_are_a_whole_pixel_quarter_circle():
    from ashen_vault.ui import hud

    for radius in range(1, 7):
        insets = hud.corner_insets(radius)
        assert len(insets) == radius
        assert insets[-1] == 0, "the last corner row reaches the box's side"
        assert list(insets) == sorted(insets, reverse=True), "a corner only widens downward"
    assert hud.corner_insets(hud.HUD_RADIUS) == (2, 1, 0)


def test_every_hud_box_shares_the_named_corner_radii():
    """Mismatched corners crept in from ad-hoc radii (the mouse once had 9, the wheel 2): every box
    takes HUD_RADIUS, and a well inside a box HUD_INNER_RADIUS."""
    for path in (SRC / "ui" / "hud.py", SRC / "game.py"):
        for literal in re.findall(r"radius=([^,)]+)", path.read_text()):
            assert literal in ("HUD_RADIUS", "HUD_INNER_RADIUS", "ui.HUD_RADIUS", "ui.HUD_INNER_RADIUS"), (
                f"{path.name}: radius={literal}"
            )


def test_every_sound_the_game_plays_is_synthesized():
    """`sfx("name")` with no matching sound in `audio/synth.py` plays nothing, silently: Ashen Ward's
    `ward`, Pyre's `pyre` and the braziers' `kindle` were all added by name in two places."""
    made = set(re.findall(r'^\s+"([a-z_]+)": gen\(', (SRC / "audio" / "synth.py").read_text(), re.M))
    played = set()
    for path in SRC.rglob("*.py"):
        played |= set(re.findall(r'sfx\(\s*"([a-z_]+)"', path.read_text()))
    assert played and not played - made, sorted(played - made)
