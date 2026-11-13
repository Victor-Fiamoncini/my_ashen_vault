"""Boss arenas: the great door at a boss's lair, and the fog that takes its place once you have died
in there. Pure, no raylib.

A `door boss=<dead_flag>` entity guards an arena: every tile reachable from the boss's lair without
passing that door. The first time, you open the door. Once you are inside and the boss has woken (all
of its bosses inside with you), the arena seals: the door slams shut behind you and nothing passes
it until the boss or you fall. Die in there and the door is gone for good, replaced by a wall of fog
(`fog:<map>:<tx>,<tz>` in the flags). Until the fight starts, the fog lets the boss through, so it can
see you and come after you outside; you cross it only on purpose (interact), and crossing it inward
starts the fight. When the boss dies, the way out opens and stays open."""

from dataclasses import dataclass

ARENA_LIMIT = 900  # tiles; a flood that spills further has leaked out of its walls


def flood(tile_at, starts, gates):
    """Tiles reachable from `starts` without stepping onto a solid tile or one of `gates`.
    `tile_at(tx, tz)` returns the map tile, or None off the map. None if the flood runs over
    ARENA_LIMIT tiles (the arena isn't closed)."""
    seen = set(starts)
    stack = list(starts)
    while stack:
        tx, tz = stack.pop()
        for n in ((tx + 1, tz), (tx - 1, tz), (tx, tz + 1), (tx, tz - 1)):
            if n in seen or n in gates:
                continue
            tile = tile_at(*n)
            if tile is None or tile.solid:
                continue
            seen.add(n)
            stack.append(n)
            if len(seen) > ARENA_LIMIT:
                return None
    return seen


@dataclass(eq=False)
class Arena:
    flag: str  # the dead_flag of the boss (or twins) inside
    gate: tuple  # the door's tile
    tiles: frozenset  # every tile of the arena, the gate not included
    fog_key: str
    door: object = None  # the door prop guarding it
    sealed: bool = False

    def cleared(self, flags):
        return self.flag in flags

    def fogged(self, flags):
        """The door has given way to fog (you died in here) and the boss still lives."""
        return self.fog_key in flags and not self.cleared(flags)

    def should_seal(self, flags, player_tile, bosses):
        """Whether the fight starts now: you stand inside with every living boss of the arena (each
        `(tile, awake)`), and at least one of them has woken, or you came in through the fog."""
        if self.sealed or self.cleared(flags) or not bosses or player_tile not in self.tiles:
            return False
        if any(tile not in self.tiles for tile, _ in bosses):
            return False
        return self.fogged(flags) or any(awake for _, awake in bosses)

    def blocks(self, flags, door_shut):
        """Whether the gate stops anything right now: a sealed fight shuts it, open fog lets bodies
        through, otherwise it is as shut as its door."""
        if self.sealed:
            return True
        if self.fogged(flags):
            return False
        return door_shut

    def crossing(self, axis, px, pz):
        """The tile beyond the gate for someone at tile (px, pz) walking through it. `axis` is the
        door's: "x" when the passage runs east-west."""
        gx, gz = self.gate
        if axis == "x":
            return (gx + (1 if px <= gx else -1), gz)
        return (gx, gz + (1 if pz <= gz else -1))
