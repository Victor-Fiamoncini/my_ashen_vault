"""The gold counter's bookkeeping: a fresh gain lingers as "+N", then counts into the total."""

from ashen_vault.util import rround

GAIN_HOLD = 1.5  # seconds a gain shows as "+N" before it counts in
ROLL_TIME = 0.5  # seconds it takes to count in
FADE_TIME = 0.4  # seconds the emptied "+N" takes to fade


class GoldTally:
    def __init__(self, gold=0):
        self.shown = gold  # the number on the counter
        self.gain = 0  # gold still waiting to count in
        self.shown_gain = 0  # the "+N" on screen (kept while it fades)
        self.age = 0.0  # seconds since the last gain arrived
        self._base = gold  # `shown` when the roll began
        self._target = gold

    def update(self, gold, dt):
        if gold > self._target:
            # A gain: hold the whole pending amount as "+N" and restart the clock.
            self.gain += gold - self._target
            self._base = self.shown
            self.shown_gain = self.gain
            self.age = 0.0
        elif gold < self._target:
            # Spending shows at once.
            self.shown = self._base = gold
            self.gain = self.shown_gain = 0
        self._target = gold
        self.age += dt
        if self.gain:
            k = (self.age - GAIN_HOLD) / ROLL_TIME
            if k > 0:
                self.shown = gold if k >= 1 else self._base + rround((gold - self._base) * k)
                self.gain = gold - self.shown
            if not self.gain:
                # Counted in (rounding can finish it a frame early): the fade starts now.
                self.age = GAIN_HOLD + ROLL_TIME

    def gain_alpha(self):
        """How visible the "+N" is: solid while pending, then fading out (always within 0..1)."""
        if not self.shown_gain:
            return 0.0
        if self.gain:
            return 1.0
        return min(1.0, max(0.0, 1 - (self.age - GAIN_HOLD - ROLL_TIME) / FADE_TIME))
