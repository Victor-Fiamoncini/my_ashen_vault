"""Death-to-ash effect: the timing curve a dying body follows and the flakes it sheds."""

import math
import random
from dataclasses import dataclass

ASH_RGB = (150, 144, 136)
EMBER_RGB = (255, 140, 50)


def death_phases(k):
    """Maps death progress `k` (0..1) to (ashen, dissolve), both 0..1. The body first bleaches to
    ash, then crumbles away from the top down while it is still graying out at the feet."""
    k = min(max(k, 0.0), 1.0)
    ashen = min(k / 0.3, 1.0)
    dissolve = min(max((k - 0.15) / 0.8, 0.0), 1.0)
    return ashen, dissolve


@dataclass
class Flake:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    life: float
    max_life: float
    size: float
    ember: bool
    spin: float

    @property
    def fade(self):
        """1 when fresh, 0 when the flake is about to vanish."""
        return max(self.life / self.max_life, 0.0)

    @property
    def rgb(self):
        """Embers cool from orange to ash gray as they drift."""
        if not self.ember:
            return ASH_RGB
        k = 1.0 - min(self.fade * 1.4, 1.0)
        return tuple(e + (a - e) * k for e, a in zip(EMBER_RGB, ASH_RGB, strict=True))


class AshCloud:
    """Flakes that drift up and away from a crumbling body, shrinking until they are gone."""

    LIFT = 0.35  # upward acceleration, m/s^2; ash floats on the heat
    DRAG = 0.6

    def __init__(self, rng=None):
        self._rng = rng or random.Random()
        self.flakes = []
        self._time = 0.0

    def __len__(self):
        return len(self.flakes)

    def __iter__(self):
        return iter(self.flakes)

    def emit(self, x, y, z, radius, count, band=0.15, ember_chance=0.3):
        """Spawns `count` flakes on a ring-ish disc of `radius` around (x, z), within `band` of `y`."""
        rng = self._rng
        for _ in range(count):
            a = rng.random() * math.tau
            d = math.sqrt(rng.random()) * radius
            out = 0.15 + rng.random() * 0.35
            life = 1.2 + rng.random() * 1.4
            self.flakes.append(
                Flake(
                    x=x + math.cos(a) * d,
                    y=y + (rng.random() * 2 - 1) * band,
                    z=z + math.sin(a) * d,
                    vx=math.cos(a) * out,
                    vy=0.25 + rng.random() * 0.45,
                    vz=math.sin(a) * out,
                    life=life,
                    max_life=life,
                    size=0.04 + rng.random() * 0.05,
                    ember=rng.random() < ember_chance,
                    spin=rng.random() * math.tau,
                )
            )

    def shed(self, x, base_y, z, radius, height, k, rate, dt):
        """Emits flakes from the crumbling front of a body that is `k` of the way through dying.
        `rate` is flakes per second; fractions carry over randomly so low rates still emit."""
        _, dissolve = death_phases(k)
        if dissolve <= 0.0 or k >= 1.0:
            return
        want = rate * dt
        count = int(want) + (1 if self._rng.random() < want - int(want) else 0)
        front = base_y + height * (1.0 - dissolve)
        self.emit(x, front, z, radius * 0.8, count)

    def update(self, dt):
        self._time += dt
        drag = math.exp(-self.DRAG * dt)
        for f in self.flakes:
            f.life -= dt
            # A lazy sideways sway so the ash swirls instead of rising in straight lines.
            sway = math.sin(self._time * 2.3 + f.spin) * 0.25
            f.vx = (f.vx + sway * dt) * drag
            f.vz = (f.vz + math.cos(self._time * 1.9 + f.spin) * 0.25 * dt) * drag
            f.vy += self.LIFT * dt
            f.x += f.vx * dt
            f.y += f.vy * dt
            f.z += f.vz * dt
            f.spin += dt * 3.0
        self.flakes = [f for f in self.flakes if f.life > 0]

    def clear(self):
        self.flakes = []
