"""Turn a game map into an underlay for the level sketch (tools/level_sketch/index.html).

    uv run python tools/level_sketch/map_to_underlay.py src/ashen_vault/maps/harrowmere.map > harrowmere.underlay.json

Load the output with the sketch's Underlay button: it is drawn faintly behind the sketch so a level can be
redrawn over what exists. Each tile becomes a broad kind (wall, floor, indoor, sea, water, lava, chasm, mud,
thorns), one character per tile in `rows`; exits, shrines, NPCs, boss doors, lifts and the start become
`marks`, placed at their tile's centre in metres (one tile = 2 m).
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "level_planner"))
from map_to_planner import entries, sections

TILE_M = 2
CODES = {
    "#": "wall",
    ".": "floor",
    "i": "indoor",
    "~": "sea",
    "r": "water",
    "L": "lava",
    "c": "chasm",
    "m": "mud",
    "t": "thorns",
}
CODE = {kind: code for code, kind in CODES.items()}


def underlay_kind(spec: str) -> str:
    """The broad kind of a legend entry, e.g. `floor tex=lava h=-8 chasm` -> "lava"."""
    words = spec.split()
    if not words:
        return "floor"
    if words[0] == "wall":
        return "wall"
    if words[0] == "water":
        return "sea" if "deep" in words else "water"
    if "lava" in words or "tex=lava" in words:
        return "lava"
    if "chasm" in words or "pit" in words:
        return "chasm"
    if any(w.startswith("slow=") for w in words):
        return "mud"
    if any(w.startswith("hurt=") for w in words):
        return "thorns"
    if any(w.startswith("ceil=") for w in words):
        return "indoor"
    return "floor"


def _meta(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines:
        key, sep, value = line.partition(" = ")
        if sep and not key.startswith("//"):
            out[key.strip()] = value.strip()
    return out


def _tiles(grid: list[str], legend: dict[str, str], ents: dict[str, str], default: str) -> list[list[str]]:
    height, width = len(grid), max(len(row) for row in grid)
    tiles: list[list[str | None]] = [[None] * width for _ in range(height)]
    for z, row in enumerate(grid):
        for x, char in enumerate(row):
            if char in legend:
                tiles[z][x] = underlay_kind(legend[char])
                continue
            on = re.search(r"\bon=(\S)", ents.get(char, ""))
            if on and on.group(1) in legend:
                tiles[z][x] = underlay_kind(legend[on.group(1)])
    # A marker without `on=` stands on the floor most of its open neighbours share.
    for _ in range(3):
        for z in range(height):
            for x in range(width):
                if tiles[z][x] is not None:
                    continue
                near = collections.Counter(
                    tiles[nz][nx]
                    for nz, nx in ((z - 1, x), (z + 1, x), (z, x - 1), (z, x + 1))
                    if 0 <= nz < height and 0 <= nx < width and tiles[nz][nx] not in (None, "wall")
                )
                if near:
                    tiles[z][x] = near.most_common(1)[0][0]
    fallback = underlay_kind(legend[default]) if default in legend else "floor"
    return [[t or fallback for t in row] for row in tiles]


def _marks(grid: list[str], ents: dict[str, str], meta: dict[str, str]) -> list[dict]:
    marks: list[dict] = []

    def add(kind: str, tx: int, tz: int, label: str, note: str = "") -> None:
        marks.append({"kind": kind, "x": tx * TILE_M + 1, "y": tz * TILE_M + 1, "label": label, "note": note})

    for z, row in enumerate(grid):
        for x, char in enumerate(row):
            spec = ents.get(char)
            if not spec:
                continue
            kind = spec.split()[0]
            if kind == "npc":
                npc = re.search(r"\bid=(\w+)", spec)
                add("npc", x, z, npc.group(1).capitalize() if npc else "NPC")
            elif kind == "exit":
                to = re.search(r"\bmap=(\w+)", spec)
                to_map = to.group(1) if to else "?"
                label = re.search(r"\blabel=(\S+)", spec)
                name = label.group(1).replace("_", " ") if label else f"Exit to {to_map}"
                where = "well" if "model=well" in spec else "cave" if "model=cave" in spec else "gate"
                add(where, x, z, name, f"To {to_map}")
            elif kind == "cemetery_gate":
                add("gate", x, z, "Cemetery gate", "To ashen_cemetery")
            elif kind == "save_statue":
                add("shrine", x, z, "Shrine")
            elif kind == "door" and "boss=" in spec:
                flag = re.search(r"\bboss=(\w+)", spec).group(1)
                add("boss", x, z, flag, "Boss door")
            elif kind == "lift":
                add("lift", x, z, "Lift", spec)
    start = meta.get("start", "").split()
    if len(start) >= 2:
        add("start", int(start[0]), int(start[1]), "Start", "Player arrives here")
    return marks


def convert(path: Path) -> dict:
    sec = sections(path.read_text(encoding="utf-8"))
    grid = [row for row in sec["grid"] if row.strip()]
    legend, ents = entries(sec["legend"]), entries(sec.get("entities", []))
    meta = _meta(sec.get("meta", []))
    tiles = _tiles(grid, legend, ents, meta.get("default", ""))
    return {
        "format": "ashen-vault-underlay",
        "version": 1,
        "map": path.stem,
        "name": meta.get("name", path.stem),
        "w": len(tiles[0]),
        "h": len(tiles),
        "tile_m": TILE_M,
        "codes": CODES,
        "rows": ["".join(CODE[t] for t in row) for row in tiles],
        "marks": _marks(grid, ents, meta),
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: map_to_underlay.py <map file>")
    print(json.dumps(convert(Path(sys.argv[1])), ensure_ascii=False))


if __name__ == "__main__":
    main()
