"""Smoothing for the first-person arms. Pure, no raylib.

An attack's motion (`models._motion`) is a fixed curve over the swing, but what the arm does between
swings is not: a swing ends, a new one starts before the arm is home, a charged heavy is let go, a shield is raised.
Each of those used to jump straight to the next pose. `PoseBlend` cross-fades from wherever the arm was
drawn to the new pose instead, and `Sway` lets the arms lag a touch behind the turning view.
"""

import math

INTO_SWING = 0.1  # seconds a new swing takes to catch the arm: short, so blows still snap
INTO_CHARGE = 0.15  # raising the weapon to wind up a heavy
RECOVER = 0.3  # bringing the weapon home after a swing (times the weapon's tempo)
GUARD = 0.12  # raising or lowering a shield

SWAY_GAIN = 0.6  # radians of lag added for each radian the view turns
SWAY_RATE = 12.0  # 1/s: how quickly the lag eases back to nothing
SWAY_MAX = 0.05  # radians the arms may trail the view by


def _ease_out(k):
    k = min(max(k, 0.0), 1.0)
    return 1 - (1 - k) ** 3


class PoseBlend:
    """Cross-fades a pose (any tuple of numbers) whenever its source changes.

    `apply(key, target, t, dur)` returns the pose to draw at render time `t`: `target` itself while
    the same `key` keeps coming, or, for `dur` seconds after the key changes, a blend from the pose drawn
    last onto `target` (which may keep moving under it, as a swing does)."""

    def __init__(self):
        self.key = None
        self.last = None  # the pose drawn last
        self._last_t = None  # and when
        self._from = None
        self._t0 = 0.0
        self._dur = 0.0

    def apply(self, key, target, t, dur):
        target = tuple(target)
        if key != self.key:
            self.key = key
            if self.last is not None and len(self.last) == len(target) and dur > 0:
                # From the frame drawn last, so this frame already moves on (no one-frame stall).
                t0 = self._last_t if self._last_t is not None and 0 < t - self._last_t < 0.1 else t
                self._from, self._t0, self._dur = self.last, t0, dur
            else:
                self._from = None
        pose = target
        if self._from is not None:
            k = (t - self._t0) / self._dur
            if k >= 1 or k < 0:  # done (or the clock went back: a new game)
                self._from = None
            else:
                e = _ease_out(k)
                pose = tuple(a + (b - a) * e for a, b in zip(self._from, target, strict=True))
        self.last, self._last_t = pose, t
        return pose

    @property
    def blending(self):
        return self._from is not None


class Sway:
    """The arms trail the view a little as you turn and look up or down, then catch up.

    `update(yaw, pitch, t)` returns (yaw_lag, pitch_lag) in radians, each within SWAY_MAX."""

    def __init__(self):
        self._yaw = None
        self._pitch = None
        self._t = None
        self.yaw_lag = 0.0
        self.pitch_lag = 0.0

    def update(self, yaw, pitch, t):
        if self._t is None or t <= self._t or t - self._t > 0.25:  # first frame, or after a pause
            self._yaw, self._pitch, self._t = yaw, pitch, t
            self.yaw_lag = self.pitch_lag = 0.0
            return 0.0, 0.0
        dt = t - self._t
        dyaw = (yaw - self._yaw + math.pi) % (2 * math.pi) - math.pi
        dpitch = pitch - self._pitch
        self._yaw, self._pitch, self._t = yaw, pitch, t
        decay = math.exp(-SWAY_RATE * dt)
        self.yaw_lag = _clamp(self.yaw_lag * decay - dyaw * SWAY_GAIN, SWAY_MAX)
        self.pitch_lag = _clamp(self.pitch_lag * decay - dpitch * SWAY_GAIN, SWAY_MAX)
        return self.yaw_lag, self.pitch_lag


def _clamp(v, m):
    return max(-m, min(m, v))


class ViewBlends:
    """Everything the first-person view remembers between frames: a blend per hand, one per shield
    raise, and the sway."""

    def __init__(self):
        self.hands = {"right": PoseBlend(), "left": PoseBlend()}
        self.shields = {"right": PoseBlend(), "left": PoseBlend()}
        self.sway = Sway()
