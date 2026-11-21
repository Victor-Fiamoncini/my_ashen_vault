"""A boss's great gate (`door boss=<dead_flag> great=n|s|e|w`, the Keystone's front door): a door
twice the height of the others, its masonry built up to the walls either side and its facade turned
toward the side named, the way you come to it. Only its look changes: it still fills its one tile,
and blocks, seals and fogs as any boss door does. Here is what the drawing needs to know of where it
stands: which way it faces, how deep a porch runs out before it, and how high the walls round it rise."""

DIRS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}


def outward(props, axis):
    """(dx, dz), the step from the gate's tile toward the way its facade faces (`great=n|s|e|w`, the
    side you come to it from). None unless that is a way through the door: a door blocking along
    `axis` "x" opens onto its tiles either side in x, "z" in z."""
    step = DIRS.get(props.get("great") or "")
    if step is None or (step[0] != 0) != (axis == "x"):
        return None
    return step


def porch(map_, tx, tz, step, limit=3):
    """How many tiles the gate's opening runs on outward (`step`, from `outward`) between walls either
    side before it opens out: its facade stands that far out past its own tile."""
    dx, dz = step
    across = ((dz, dx), (-dz, -dx))  # the tiles either side of each step of the porch
    n = 0
    while n < limit:
        x, z = tx + dx * (n + 1), tz + dz * (n + 1)
        if map_[x, z].solid or not all(map_[x + a, z + b].solid for a, b in across):
            break
        n += 1
    return n


def wall_rise(map_, tx, tz, axis):
    """How high the walls either side of the gate's opening stand above its floor (the lower of the
    two), so its masonry can fill the gap over the arch up to them. None unless both are walls of a
    set height."""
    sides = ((tx, tz - 1), (tx, tz + 1)) if axis == "x" else ((tx - 1, tz), (tx + 1, tz))
    tiles = [map_[x, z] for x, z in sides]
    if not all(t.solid and t.top is not None for t in tiles):
        return None
    return min(t.top for t in tiles) - map_[tx, tz].floor
