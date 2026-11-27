"""tools/level_sketch/map_to_underlay.py: a game map turned into the level sketch's faint underlay."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAPS = ROOT / "src" / "ashen_vault" / "maps"
_spec = importlib.util.spec_from_file_location(
    "map_to_underlay", ROOT / "tools" / "level_sketch" / "map_to_underlay.py"
)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


@pytest.mark.parametrize(
    ("spec", "kind"),
    [
        ("wall tex=black_brick top=8 cap=slate", "wall"),
        ("wall tex=stone thin=0.5", "wall"),
        ("water tex=sea h=-1 deep", "sea"),
        ("water tex=bog h=-0.5 side=mud", "water"),
        ("floor tex=lava h=-8 side=cliff_rock chasm", "lava"),  # lava wins over chasm
        ("floor tex=lava h=-1 ceil=6 lava", "lava"),
        ("floor tex=ravine h=-5 side=cliff_rock chasm", "chasm"),
        ("floor tex=stone h=0 pit", "chasm"),
        ("floor tex=mud h=-0.2 side=mud slow=0.65", "mud"),
        ("floor tex=thorns h=0 side=mud hurt=5", "thorns"),
        ("floor tex=leaf_litter h=0 ceil=4.6", "indoor"),
        ("floor tex=jungle_floor h=0 side=bark", "floor"),
    ],
)
def test_underlay_kind(spec, kind):
    assert mod.underlay_kind(spec) == kind


@pytest.mark.parametrize("name", ["harrowmere", "verdant_hollow", "cinderhold", "cinder_keep"])
def test_convert_real_maps(name):
    out = mod.convert(MAPS / f"{name}.map")
    assert out["format"] == "ashen-vault-underlay" and out["version"] == 1 and out["tile_m"] == 2
    assert out["map"] == name
    assert len(out["rows"]) == out["h"] and all(len(r) == out["w"] for r in out["rows"])
    assert set("".join(out["rows"])) <= set(out["codes"])
    json.dumps(out)  # serialisable


def test_cinderhold_has_lava_and_harrowmere_has_sea():
    assert "L" in "".join(mod.convert(MAPS / "cinderhold.map")["rows"])
    assert "~" in "".join(mod.convert(MAPS / "harrowmere.map")["rows"])


def test_marks_are_tile_centres_in_metres():
    out = mod.convert(MAPS / "harrowmere.map")
    start = next(m for m in out["marks"] if m["kind"] == "start")
    assert (start["x"], start["y"]) == (2 * 2 + 1, 22 * 2 + 1)  # harrowmere: start = 2 22 0
    assert any(m["kind"] == "npc" and m["label"] == "Odrin" for m in out["marks"])
    assert any(m["kind"] == "shrine" for m in out["marks"])
