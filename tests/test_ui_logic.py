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
