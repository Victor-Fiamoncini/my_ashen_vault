"""One-way doors: `door from=n|s|e|w` is barred on that side and can only be opened from there.
North is toward row 0 (smaller z), west toward column 0 (smaller x)."""

SIDES = ("n", "s", "e", "w")


def opens_from(side, door_x, door_z, px, pz):
    """True if someone at (px, pz) stands on the barred `side` of a door at (door_x, door_z) and can
    lift the bar. A door without a side opens from anywhere."""
    if side not in SIDES:
        return True
    if side == "n":
        return pz < door_z
    if side == "s":
        return pz > door_z
    if side == "w":
        return px < door_x
    return px > door_x
