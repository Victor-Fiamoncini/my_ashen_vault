from ashen_vault.util import rround


class Gauge:
    """A stamina gauge that empties on use and refills over `refill_time` seconds."""

    def __init__(self, refill_time):
        self.refill_time = refill_time
        self.value = 1.0

    def update(self, dt):
        self.value = min(self.value + dt / self.refill_time, 1.0)
        return self.value

    @property
    def full(self):
        return self.value >= 1.0

    def spend(self):
        """Empties the gauge and returns how full it was."""
        used = self.value
        self.value = 0.0
        return used

    def fill(self):
        self.value = 1.0


class Combat:
    @staticmethod
    def power(gauge):
        """A swing with a half-empty gauge is weak; a full one hits hardest."""
        return 0.15 + 0.85 * (gauge**1.5)

    @staticmethod
    def damage(base, strength, gauge, defense):
        raw = (base + strength * 0.5) * Combat.power(gauge)
        return max(rround(raw - defense * 0.5), 1)
