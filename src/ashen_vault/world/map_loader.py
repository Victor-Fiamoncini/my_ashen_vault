"""Parses the plain-text .map format:

[meta]     key = value lines
[legend]   <char> = <floor|wall|water> key=value ...
[grid]     rows of legend chars and entity markers
[entities] <marker> = <kind> key=value ... (on=<legend char> picks the tile under it)
"""

import os
import re
import shlex

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
                    ch = spec["props"].get("on", default_char)
                if ch == " " and " " not in legend:
                    ch = default_char
                tile = legend.get(ch)
                if tile is None:
                    raise MapError(f"{self.name}: unknown tile '{ch}' at {tx},{tz}")
                tiles.append(tile)
        return TileMap(
            name=self.name, width=width, depth=len(rows), tiles=tiles, meta=meta, entities=entities
        )

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

    @staticmethod
    def _build_tile(kind, p):
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
        return Tile(
            solid=False,
            walkable=True,
            floor=floor,
            ceil=ceil,
            pit="pit" in p,
            floor_tex=p.get("tex", "flagstone"),
            wall_tex=p.get("side", "stone_brick"),
            ceil_tex=p.get("ceil_tex", "rough_stone"),
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
