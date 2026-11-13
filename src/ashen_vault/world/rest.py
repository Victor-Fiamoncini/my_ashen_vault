"""Resting at a shrine: a few seconds of pixelated ember fog that rises, swallows the screen and
clears again. Pure timing and pattern math; the HUD turns it into coloured 4 px cells."""

import math

from ashen_vault.util import clamp

# 4x4 ordered-dither thresholds: cells switch on in this order as the fog thickens.
BAYER = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)

CELL = 4  # pixels per fog cell at 320x240
COLS = 80
ROWS = 60

RISE = 0.4  # fraction of the rest spent thickening (and, mirrored, clearing)
PEAK = 0.45  # fraction at which the screen is fully covered and the shrine does its work


def _smooth(k):
    k = clamp(k, 0.0, 1.0)
    return k * k * (3 - 2 * k)


class RestSequence:
    DURATION = 3.2

    def __init__(self, duration=DURATION):
        self.duration = duration
        self.t = 0.0
        self._peaked = False

    def update(self, dt):
        """Advances the rest. Returns True exactly once: on the frame the fog first covers the screen."""
        self.t = min(self.t + dt, self.duration)
        if not self._peaked and self.progress >= PEAK:
            self._peaked = True
            return True
        return False

    @property
    def progress(self):
        return self.t / self.duration

    @property
    def done(self):
        return self.t >= self.duration

    @property
    def density(self):
        return density(self.progress)


def density(k):
    """Fog thickness for rest progress `k` (0..1): eases in, holds, eases out."""
    if k <= RISE:
        return _smooth(k / RISE)
    if k >= 1 - RISE:
        return _smooth((1 - k) / RISE)
    return 1.0


def noise(cx, cy, t):
    """Smooth drifting swirl in 0..1, made from a few sines (deterministic, no RNG)."""
    a = math.sin(cx * 0.31 + t * 1.3 + math.sin(cy * 0.23 - t * 0.7) * 2)
    b = math.sin(cy * 0.27 - t * 0.9 + cx * 0.11)
    return clamp(0.5 + 0.25 * a + 0.25 * b, 0.0, 1.0)


def cell_alpha(cx, cy, t, dens):
    """Opacity (0..1) of fog cell (cx, cy): the fog rises from the bottom, swirls, and is quantised
    through the Bayer matrix so it reads as chunky pixels. Full cover at `dens` = 1."""
    if dens <= 0:
        return 0.0
    low = cy / (ROWS - 1)  # 0 at the top, 1 at the bottom
    fill = dens * 1.8 - (1 - low) * 0.6 + (noise(cx, cy, t) - 0.5) * 0.4
    fill = clamp(fill, 0.0, 1.0)
    threshold = (BAYER[cy % 4][cx % 4] + 0.5) / 16
    return 1.0 if fill > threshold else fill * 0.35


def fog_pixels(t, dens):
    """The whole fog as COLS x ROWS RGBA bytes (row-major): dark ash with drifting ember glows."""
    out = bytearray(COLS * ROWS * 4)
    i = 0
    for cy in range(ROWS):
        fade = 1 - cy / ROWS * 0.5
        for cx in range(COLS):
            a = cell_alpha(cx, cy, t, dens)
            if a > 0.01:
                n = noise(cx + 17, cy, t * 0.6)
                ember = clamp(n * 1.6 - 0.8, 0.0, 1.0) * fade
                out[i] = int(34 + 40 * n + 120 * ember)
                out[i + 1] = int(24 + 26 * n + 50 * ember)
                out[i + 2] = int(20 + 18 * n + 10 * ember)
                out[i + 3] = int(255 * a)
            i += 4
    return out
