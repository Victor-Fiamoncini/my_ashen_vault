"""Parses the plain-text .map format:

[meta]     key = value lines
[legend]   <char> = <floor|wall|water> key=value ...
           floors may add hurt=<hp per tick> flow=<dx>,<dz> slow=<speed multiplier>,
           pit (walk in and fall), lava (a glowing pit that sears) or chasm (needs a ledge or raft
           to cross)
           any tile may add dark=<0..1>: the share of the map's ambient light it loses
[grid]     rows of legend chars and entity markers
[entities] <marker> = <kind> key=value ... (on=<legend char> picks the tile under it)

With `entity_floor = auto` in [meta], an entity without `on=` stands on the floor most of its four
neighbours share (hazards such as pits only when nothing else is there), rather than on `default`.
"""

import os
import re
import shlex
from collections import Counter

from ashen_vault.world.tile_map import EntitySpec, Tile, TileMap


class MapError(Exception):
    pass


class MapLoader:
    Error = MapError
    TILE_KINDS = ("floor", "wall", "water")

    @classmethod
    def load_file(cls, path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        return cls(text, name=os.path.splitext(os.path.basename(path))[0]).parse()

    def __init__(self, text, name="map"):
        self.text = text
        self.name = name

    def parse(self):
        sections = self._split_sections()
        meta = self._parse_meta(sections.get("meta", []))
        legend = self._parse_legend(sections.get("legend", []))
        specs = self._parse_entities(sections.get("entities", []))
        if "grid" not in sections:
            raise MapError(f"{self.name}: missing [grid]")
        rows = [r for r in sections["grid"] if r.strip()]
        if not rows:
            raise MapError(f"{self.name}: empty grid")

        width = max(len(r) for r in rows)
        default_char = meta.get("default", ".")
        auto = meta.get("entity_floor") == "auto"
        floors = self._auto_floors(rows, legend, specs) if auto else {}
        tiles = []
        entities = []
        for tz, row in enumerate(rows):
            for tx in range(width):
                ch = row[tx] if tx < len(row) else " "
                spec = specs.get(ch)
                if spec:
                    entities.append(
                        EntitySpec(kind=spec["kind"], tx=tx, tz=tz, props=spec["props"], marker=ch)
                    )
                    ch = spec["props"].get("on") or floors.get((tx, tz), default_char)
                if ch == " " and " " not in legend:
                    ch = default_char
                tile = legend.get(ch)
                if tile is None:
                    raise MapError(f"{self.name}: unknown tile '{ch}' at {tx},{tz}")
                tiles.append(tile)
        return TileMap(
            name=self.name, width=width, depth=len(rows), tiles=tiles, meta=meta, entities=entities
        )

    @staticmethod
    def _auto_floors(rows, legend, specs):
        """Floor chars for entities without `on=`: whatever most of their four neighbours stand on.
        Neighbours that are entities count with their own floor once that is known, so a prop
        boxed in by walls and other props still finds the room's floor. Hazardous floors (pits,
        water) only win when nothing else touches the cell."""
        known = {}
        pending = []
        for tz, row in enumerate(rows):
            for tx, ch in enumerate(row):
                if ch in specs:
                    on = specs[ch]["props"].get("on")
                    if on:
                        known[tx, tz] = on
                    else:
                        pending.append((tx, tz))
        resolved = {}
        while pending:
            left = []
            for tx, tz in pending:
                safe, risky = Counter(), Counter()
                for dx, dz in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    x, z = tx + dx, tz + dz
                    if not (0 <= z < len(rows) and 0 <= x < len(rows[z])):
                        continue
                    ch = known.get((x, z), rows[z][x])
                    tile = None if ch in specs and (x, z) not in known else legend.get(ch)
                    if tile is None or not tile.walkable:
                        continue
                    (risky if tile.hazardous else safe)[ch] += 1
                best = safe or risky
                if best:
                    resolved[tx, tz] = best.most_common(1)[0][0]
                else:
                    left.append((tx, tz))
            if len(left) == len(pending):
                break  # walled in by walls alone: they keep the map's default
            known.update(resolved)
            pending = left
        return resolved

    def _split_sections(self):
        sections = {}
        current = None
        for line in self.text.splitlines():
            m = re.fullmatch(r"\[(\w+)\]\s*", line)
            if m:
                current = sections[m.group(1)] = []
            elif current is not None:
                current.append(line)
        return sections

    @staticmethod
    def _content_lines(lines):
        return [l for l in lines if l.strip() and not l.strip().startswith("//")]

    def _parse_meta(self, lines):
        meta = {}
        for line in self._content_lines(lines):
            key, value = (s.strip() for s in line.split("=", 1))
            meta[key] = self._coerce_meta(key, value)
        return meta

    @staticmethod
    def _coerce_meta(key, value):
        if key in ("ambient", "fog", "fog_range", "start", "sky", "torch"):
            return [float(v) for v in value.split()]
        if key == "edge_top":
            return float(value)
        return value

    def _split_def(self, line):
        rest = re.sub(r"\A\s*=\s*", "", line[1:])
        parts = shlex.split(rest)
        return parts[0], parts[1:]

    def _parse_legend(self, lines):
        legend = {}
        for line in self._content_lines(lines):
            ch = line[0]
            kind, pairs = self._split_def(line)
            if kind not in self.TILE_KINDS:
                raise MapError(f"{self.name}: bad tile kind '{kind}' for '{ch}'")
            legend[ch] = self._build_tile(kind, self._kv(pairs))
        return legend

    @classmethod
    def _build_tile(cls, kind, p):
        tile = cls._tile_of_kind(kind, p)
        tile.dark = min(max(float(p.get("dark", "0")), 0.0), 1.0)
        return tile

    @staticmethod
    def _tile_of_kind(kind, p):
        floor = float(p.get("h", "0"))
        ceil = float(p["ceil"]) if "ceil" in p else None
        if kind == "wall":
            return Tile(
                solid=True,
                walkable=False,
                floor=floor,
                ceil=None,
                top=float(p.get("top", "3")),
                wall_tex=p.get("tex", "stone_brick"),
                floor_tex=p.get("cap") or p.get("tex", "stone_brick"),
            )
        if kind == "water":
            return Tile(
                solid=False,
                walkable=False,
                floor=floor,
                ceil=ceil,
                liquid=True,
                floor_tex=p.get("tex", "water"),
                wall_tex=p.get("side", "stone_brick"),
                ceil_tex=p.get("ceil_tex", "rough_stone"),
            )
        flow = None
        if "flow" in p:
            fx, fz = (float(v) for v in p["flow"].split(","))
            flow = (fx, fz)
        return Tile(
            solid=False,
            walkable=True,
            floor=floor,
            ceil=ceil,
            pit="pit" in p or "lava" in p,
            lava="lava" in p,
            floor_tex=p.get("tex", "flagstone"),
            wall_tex=p.get("side", "stone_brick"),
            ceil_tex=p.get("ceil_tex", "rough_stone"),
            hurt=int(p.get("hurt", "0")),
            flow=flow,
            slow=float(p.get("slow", "1")),
            chasm="chasm" in p,
        )

    def _parse_entities(self, lines):
        specs = {}
        for line in self._content_lines(lines):
            kind, pairs = self._split_def(line)
            specs[line[0]] = {"kind": kind, "props": self._kv(pairs)}
        return specs

    @staticmethod
    def _kv(pairs):
        out = {}
        for pair in pairs:
            k, _, v = pair.partition("=")
            out[k] = v if "=" in pair else None
        return out
