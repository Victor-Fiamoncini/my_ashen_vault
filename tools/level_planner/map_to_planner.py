"""Turn a game map into a level for the planner (tools/level_planner/index.html).

    python tools/level_planner/map_to_planner.py src/ashen_vault/maps/harrowmere.map > harrowmere.json

Paste the output into the planner's Import box. Each legend tile becomes one of the planner's broad
tile kinds (wall, house, street, water...), entity markers take the floor they stand on, and NPCs,
exits, shrines, landmarks and doors become markers. Everything else (props, lights, trees) is left out.
"""

from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

# Map legend character -> planner tile character. Covers Harrowmere's legend; other maps fall back to
# the floor/wall kind of their legend entry (see `planner_tile`).
HARROWMERE = {
    "R": "#", "A": "^", "[": "#", "]": "#", "9": "#", "8": "#", "7": "#", "6": "#",
    "H": "H", "#": "H", "q": "H", "^": "H", "C": "C", "P": "_",
    ",": ".", ".": ".", "t": ".", "_": ".", "s": "s", "-": "s", "/": "s", "e": "s",
    ";": "=", "4": "/", "3": "/", "2": "/", "1": "/",
    "n": "n", "a": "n", "i": "i", "k": "i",
    "p": "p", "~": "~", "G": "G", "V": "G", "w": "j", "y": "j", "v": "j", "c": "c",
}  # fmt: skip
SOLID = set("#^HJC_G")
ROLES = {
    "odrin": "Odrin, keeper of the prophecy",
    "pell": "Pell, scrolls and salvage (shop)",
    "brannoc": "Brannoc, the forge (shop)",
    "tamsin": "Tamsin, remedies (shop)",
    "corvane": "Corvane, swordmaster's blades (shop, level 5+)",
    "aldous": "Aldous, watch at the north gate",
    "tobin": "Tobin, watch at the north gate",
    "fenn": "Fenn, watch by the cemetery gate",
    "reyna": "Reyna, watch at the east gate",
    "wynn": "Wynn, watch at the Vesper Gate",
    "garrick": "Garrick, captain of the watch, in the watch office",
    "hollis": "Hollis, keeper of the gaol's pit",
    "maeve": "Maeve, fishing off the pier (gift)",
    "wren": "Wren, the Drowned Lantern's keeper",
    "ilse": "Sister Ilse, in the cathedral",
    "enthroned": "The Enthroned, the stone king",
    "hedda": "Old Hedda, at prayer in the nave",
    "aubrey": "Aubrey, the cathedral's acolyte",
    "lisbet": "Lisbet, the flower seller",
    "osric": "Osric, the town crier",
    "merrit": "Merrit, begging by the bell",
    "tilde": "Tilde, the weaver",
    "barnaby": "Barnaby, the cooper",
    "ottilie": "Ottilie, the midwife",
    "hamund": "Old Hamund, a sailor ashore",
    "sefa": "Sefa, the baker",
    "jorun": "Jorun, a fisherman's wife",
    "cobb": "Cobb, the lamplighter",
}


def sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = None
    for line in text.split("\n"):
        header = re.match(r"^\[(\w+)\]\s*$", line)
        if header:
            current = header.group(1)
            out[current] = []
        elif current:
            out[current].append(line)
    return out


def entries(lines: list[str]) -> dict[str, str]:
    return {line[0]: line[4:] for line in lines if len(line) > 4 and line[1:4] == " = "}


def planner_tile(char: str, legend: dict[str, str]) -> str | None:
    if char in HARROWMERE:
        return HARROWMERE[char]
    spec = legend.get(char)
    if spec is None:
        return None
    kind = spec.split()[0]
    if kind == "wall":
        return "#"
    if kind == "water":
        return "~" if "deep" in spec else "r"
    if "chasm" in spec or "pit" in spec or "lava" in spec:
        return "c"
    return "i" if "ceil=" in spec else "."


def convert(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    sec = sections(text)
    grid = [row for row in sec["grid"] if row.strip()]
    legend, ents = entries(sec["legend"]), entries(sec["entities"])
    height, width = len(grid), max(len(row) for row in grid)

    tiles: list[list[str | None]] = [[None] * width for _ in range(height)]
    for z, row in enumerate(grid):
        for x, char in enumerate(row):
            tiles[z][x] = planner_tile(char, legend)
            if tiles[z][x] is None:
                on = re.search(r"\bon=(\S)", ents.get(char, ""))
                tiles[z][x] = planner_tile(on.group(1), legend) if on else None
    # A marker without `on=` stands on the floor most of its open neighbours share.
    for _ in range(3):
        for z in range(height):
            for x in range(width):
                if tiles[z][x] is not None:
                    continue
                near = collections.Counter(
                    tiles[nz][nx]
                    for nz, nx in ((z - 1, x), (z + 1, x), (z, x - 1), (z, x + 1))
                    if 0 <= nz < height and 0 <= nx < width and tiles[nz][nx] and tiles[nz][nx] not in SOLID
                )
                tiles[z][x] = near.most_common(1)[0][0] if near else None
    rows = ["".join(t or "." for t in row) for row in tiles]

    marks: list[dict] = []

    def add(kind: str, x: int, z: int, label: str, note: str = "") -> None:
        marks.append({"id": f"m{len(marks) + 1}", "kind": kind, "x": x, "y": z, "label": label, "note": note})

    for z, row in enumerate(grid):
        for x, char in enumerate(row):
            spec = ents.get(char)
            if not spec:
                continue
            kind = spec.split()[0]
            if kind == "npc":
                npc = re.search(r"id=(\w+)", spec).group(1)
                add("npc", x, z, npc.capitalize(), ROLES.get(npc, ""))
            elif kind == "exit":
                to = re.search(r"map=(\w+)", spec).group(1)
                label = re.search(r"label=(\S+)", spec)
                name = label.group(1).replace("_", " ") if label else f"Exit to {to}"
                descent = any(f"model={m}" in spec for m in ("well", "gaol_grate"))  # a way down
                where = "well" if descent else "cave" if "model=cave" in spec else "gate"
                add(where, x, z, name, f"To {to}")
            elif kind == "cemetery_gate":
                add("gate", x, z, "Cemetery gate", "Arrival from ashen_cemetery (one-way)")
            elif kind == "save_statue":
                add("shrine", x, z, "Shrine", "Rest and save")
            elif kind == "silent_bell":
                add("landmark", x, z, "The Silent Bell")
            elif kind == "fountain":
                add("landmark", x, z, "Fountain")
            elif kind == "town_statue":
                add("landmark", x, z, "Founder's statue")
            elif kind == "cathedral_spire":
                add("landmark", x, z, "Cathedral spire")
            elif kind == "door_arch":
                add("door", x, z, "Cathedral door" if "rose" in spec else "Door")

    start = re.search(r"^start = (\d+) (\d+)", text, re.M)
    if start:
        add("start", int(start.group(1)), int(start.group(2)), "Start", "Player arrives here")
    name = re.search(r"^name = (.+)$", text, re.M)
    return {
        "name": name.group(1).strip() if name else path.stem,
        "w": width,
        "h": height,
        "rows": rows,
        "marks": marks,
        "notes": f"Imported from {path.name}. One cell = one 2 m tile; x = column, z = row (as in --at).",
    }


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: map_to_planner.py <map file>")
    print(json.dumps(convert(Path(sys.argv[1])), ensure_ascii=False))


if __name__ == "__main__":
    main()
