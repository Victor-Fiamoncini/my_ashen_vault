"""Thin walls: a wall tile whose legend sets `thin=<m>` stands as a slab that many metres thick instead
of filling its whole 2 m tile, so a house's rooms are as wide as its outline allows.

The slab runs toward every solid neighbour (a straight run, an L corner, a T where a partition meets
the outer wall) and hugs the side open to the sky, so the street outline, outdoor collision and the
roofs over the walls stay where they were; a wall between two rooms (or two yards) stands centred.
The rest of the tile is margin: each piece of it is lent to the open neighbour it faces, whose floor,
ceiling and darkness it shares, so a room simply runs on up to the slab.

A tile is cut into a 3x3 grid of cells by the slab's two bands; each cell is either slab or margin
owned by a neighbour (`Layout`)."""

from dataclasses import dataclass

TILE = 2.0  # metres a side (`TileMap.TILE`)
N, S, W, E = (0, -1), (0, 1), (-1, 0), (1, 0)


@dataclass(frozen=True)
class Layout:
    """How one thin tile is cut: `xs` and `zs` are the four cut positions (local metres, 0..TILE) along
    each axis, and `cells[(i, j)]` is None for a slab cell or the (tx, tz) of the tile that owns that
    margin cell. Cells of zero size are left out."""

    tx: int
    tz: int
    xs: tuple[float, float, float, float]
    zs: tuple[float, float, float, float]
    cells: dict

    def rect(self, i, j):
        """World (x0, z0, x1, z1) of cell (i, j)."""
        ox, oz = self.tx * TILE, self.tz * TILE
        return (ox + self.xs[i], oz + self.zs[j], ox + self.xs[i + 1], oz + self.zs[j + 1])

    def boxes(self):
        """World rectangles of the slab."""
        return [self.rect(i, j) for (i, j), owner in self.cells.items() if owner is None]

    def margins(self):
        """[(world rect, owner (tx, tz))] for the margin cells."""
        return [(self.rect(i, j), owner) for (i, j), owner in self.cells.items() if owner is not None]

    def cell_at(self, lx, lz):
        """The cell holding local point (lx, lz) of the tile, or None off its cells."""
        i = _index(self.xs, lx)
        j = _index(self.zs, lz)
        if (i, j) in self.cells:
            return i, j
        return None

    def owner_at(self, lx, lz):
        """The (tx, tz) lending its floor to local point (lx, lz), or None inside the slab."""
        cell = self.cell_at(lx, lz)
        return None if cell is None else self.cells[cell]


def _index(cuts, v):
    """Which of the three spans between `cuts` holds `v` (empty spans hold nothing)."""
    for i in range(3):
        if cuts[i] <= v < cuts[i + 1]:
            return i
    for i in (2, 1, 0) if v >= cuts[3] else (0, 1, 2):
        if cuts[i + 1] > cuts[i]:
            return i
    return 0


def _band(map_, tx, tz, before, after, size, thick):
    """Where the slab's band lies across one axis: against whichever side (`before` at 0, `after` at
    `size`) is open to the sky, centred when both or neither are."""
    a = map_[tx + before[0], tz + before[1]]
    b = map_[tx + after[0], tz + after[1]]
    sky_a = not a.solid and a.open_sky
    sky_b = not b.solid and b.open_sky
    if sky_a and not sky_b:
        return 0.0
    if sky_b and not sky_a:
        return size - thick
    return (size - thick) / 2


def layout(map_, tx, tz):
    """The cut of thin tile (tx, tz)."""
    size = TILE
    thick = min(max(map_[tx, tz].thin, 0.05), size)
    joins = {d: map_[tx + d[0], tz + d[1]].solid for d in (N, S, W, E)}
    across_x = joins[W] or joins[E]  # a run along X: its band spans Z
    across_z = joins[N] or joins[S]
    zb = _band(map_, tx, tz, N, S, size, thick)
    xb = _band(map_, tx, tz, W, E, size, thick)
    xs = (0.0, xb, xb + thick, size)
    zs = (0.0, zb, zb + thick, size)
    slab = {(1, 1)}
    if across_x and not across_z:
        slab |= {(0, 1), (2, 1)}  # a straight run (or its end) spans the whole tile
    elif across_z and not across_x:
        slab |= {(1, 0), (1, 2)}
    else:
        if joins[W]:
            slab.add((0, 1))
        if joins[E]:
            slab.add((2, 1))
        if joins[N]:
            slab.add((1, 0))
        if joins[S]:
            slab.add((1, 2))
    cells = {}
    for i in range(3):
        for j in range(3):
            if xs[i + 1] - xs[i] <= 1e-6 or zs[j + 1] - zs[j] <= 1e-6:
                continue
            cells[(i, j)] = None if (i, j) in slab else _owner(map_, tx, tz, i, j)
    return Layout(tx, tz, xs, zs, cells)


def _owner(map_, tx, tz, i, j):
    """The open tile a margin cell faces: a side neighbour, else the diagonal one at a corner. A cell
    with no open tile beside it stays slab."""
    sides = []
    if j == 0:
        sides.append(N)
    if j == 2:
        sides.append(S)
    if i == 0:
        sides.append(W)
    if i == 2:
        sides.append(E)
    for dx, dz in sides:
        if not map_[tx + dx, tz + dz].solid:
            return (tx + dx, tz + dz)
    if len(sides) == 2:
        dx = sides[0][0] + sides[1][0]
        dz = sides[0][1] + sides[1][1]
        if not map_[tx + dx, tz + dz].solid:
            return (tx + dx, tz + dz)
    return None


def inset(map_, tx, tz, dx, dz):
    """How far past the edge it shares with (tx - dx, tz - dz) the face of thin tile (tx, tz) stands:
    what a torch or a bed set against it must move back to touch it. Measured along the middle of
    that neighbour; 0 if no slab crosses there."""
    size = TILE
    lay = map_.layout(tx, tz)
    if lay is None:
        return 0.0
    mid = size / 2
    best = None
    for (i, j), owner in lay.cells.items():
        if owner is not None:
            continue
        x0, x1, z0, z1 = lay.xs[i], lay.xs[i + 1], lay.zs[j], lay.zs[j + 1]
        if dx:
            if not z0 <= mid <= z1:
                continue
            gap = x0 if dx > 0 else size - x1  # the wall lies east (dx > 0) or west of the tile
        else:
            if not x0 <= mid <= x1:
                continue
            gap = z0 if dz > 0 else size - z1
        best = gap if best is None else min(best, gap)
    return best or 0.0
