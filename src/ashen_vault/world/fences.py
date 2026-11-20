"""How a wattle fence tile joins its neighbours: which of its four sides run on into another fence or
butt against a wall, so a run of hurdles follows its row and turns its corners."""

# The four sides, as (dx, dz) steps: east, west, south, north.
SIDES = ((1, 0), (-1, 0), (0, 1), (0, -1))


def fence_arms(map_, tx, tz, fences):
    """The sides of fence tile (tx, tz) that join something: another fence (`fences` holds their
    tiles), or a solid wall it runs into: one on the axis of its run, not one it runs alongside (a
    garden's row of hurdles under a terrace wall). A tile joined on one axis only (a straight run, or
    a run's end beside its gap) gets both sides of that axis, so its hurdle spans the whole tile and
    the gap keeps its width; one joined on neither keeps a hurdle along Z. A corner or a T keeps just
    its own sides."""
    arms = {(dx, dz) for dx, dz in SIDES if (tx + dx, tz + dz) in fences}
    walls = {(dx, dz) for dx, dz in SIDES if map_.inside(tx + dx, tz + dz) and map_[tx + dx, tz + dz].solid}
    if arms:
        walls = {(dx, dz) for dx, dz in walls if any((dx and ax) or (dz and az) for ax, az in arms)}
    arms |= walls
    along_x = any(dx for dx, _ in arms)
    along_z = any(dz for _, dz in arms)
    if along_x and along_z:
        return tuple(s for s in SIDES if s in arms)
    if along_x:
        return ((1, 0), (-1, 0))
    return ((0, 1), (0, -1))
