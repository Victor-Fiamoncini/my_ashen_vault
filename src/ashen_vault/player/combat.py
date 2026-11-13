from ashen_vault.util import rround


class Gauge:
    """A stamina gauge that empties on use and refills over `refill_time` seconds."""

    def __init__(self, refill_time):
        self.refill_time = refill_time
        self.value = 1.0
        self.full_t = 10.0  # seconds since the gauge last became full (starts long settled)

    def update(self, dt):
        if self.value >= 1.0:
            self.full_t += dt
        self.value = min(self.value + dt / self.refill_time, 1.0)
        return self.value

    @property
    def full(self):
        return self.value >= 1.0

    def spend(self):
        """Empties the gauge and returns how full it was."""
        used = self.value
        self.value = 0.0
        self.full_t = 0.0
        return used

    def fill(self):
        self.value = 1.0


class Stamina:
    """Sprint stamina. Drains while sprinting and refills after a short rest. Running it dry
    leaves you exhausted: no sprinting until it recovers to RECOVER."""

    DRAIN_TIME = 6.0  # seconds of sprint from full
    REFILL_TIME = 2.5  # seconds to refill from empty
    REFILL_DELAY = 0.5  # rest needed before it starts refilling
    RECOVER = 0.3

    def __init__(self):
        self.value = 1.0
        self.exhausted = False
        self._rest_t = self.REFILL_DELAY

    @property
    def can_sprint(self):
        return not self.exhausted and self.value > 0

    def drain(self, dt):
        self.value = max(self.value - dt / self.DRAIN_TIME, 0.0)
        self._rest_t = 0.0
        if self.value <= 0:
            self.exhausted = True

    def spend(self, amount):
        """Pays for an attack or a blocked blow; resets the rest delay like sprinting does."""
        self.value = max(self.value - amount, 0.0)
        self._rest_t = 0.0
        if self.value <= 0:
            self.exhausted = True

    def update(self, dt, rate=1.0):
        """Call on frames without sprinting. `rate` slows the refill (a raised shield)."""
        # Only the part of `dt` after the rest delay counts toward refilling.
        rested = self._rest_t + dt - max(self._rest_t, self.REFILL_DELAY)
        self._rest_t += dt
        if rested <= 0:
            return
        self.value = min(self.value + rested * rate / self.REFILL_TIME, 1.0)
        if self.exhausted and self.value >= self.RECOVER:
            self.exhausted = False

    def fill(self):
        self.value = 1.0
        self.exhausted = False


class Combat:
    @staticmethod
    def power(gauge):
        """A swing with a half-empty gauge is weak; a full one hits hardest."""
        return 0.15 + 0.85 * (gauge**1.5)

    @staticmethod
    def damage(base, strength, gauge, defense, mult=1.0):
        raw = (base + strength * 0.5) * Combat.power(gauge) * mult
        return max(rround(raw - defense * 0.5), 1)
