"""Tutorial hints: words that appear once, the first time you step onto one of a hint's tiles. A map
places one with `hint text="Some words.|More words."` (`|` starts another line, and braces mark a span
to highlight, as in every message; unquoted, underscores stand for spaces). Its marker may stand on several
tiles (both lanes of a path, say): they share the hint, which fires once for good and leaves a
`hint:<map>:<marker>` flag. Pure, no raylib."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Hint:
    marker: str
    lines: tuple

    def flag(self, map_name):
        return f"hint:{map_name}:{self.marker}"


def lines_of(text):
    """The message lines a hint's `text=` stands for."""
    return tuple(part.replace("_", " ").strip() for part in (text or "").split("|") if part.strip("_ "))


def build(map_):
    """Every hint on `map_`, keyed by each tile it stands on."""
    return {
        (s.tx, s.tz): Hint(s.marker or f"{s.tx},{s.tz}", lines_of(s.props.get("text")))
        for s in map_.entities
        if s.kind == "hint"
    }


def due(hints, tile, flags, map_name):
    """The hint waiting on `tile` that has not yet been shown, or None."""
    hint = hints.get(tile)
    if hint is None or hint.flag(map_name) in flags:
        return None
    return hint
