"""Blocking with a shield. Pure logic, no raylib.

Hold the shield's mouse button to raise it. A raised shield stops blows from the front: it lets
through only `1 - guard` of the damage and pays for the rest with ST (a full bar absorbs `stability`
damage). Run out of ST and the guard breaks: the rest of the blow lands and you reel for a moment.
While the shield is up you walk slower, can't sprint and ST refills slowly."""

from dataclasses import dataclass

from ashen_vault.util import rround

FRONT = 0.3  # min cos(angle) between your facing and the attacker for the shield to cover it
WALK = 0.7  # walk speed multiplier while guarding
REFILL = 0.35  # ST refill rate multiplier while guarding
BREAK_TIME = 0.6  # seconds you reel after a guard break


@dataclass(frozen=True)
class Block:
    taken: int  # damage that still lands
    stamina: float  # ST the block costs
    broken: bool  # the guard gave way

    @property
    def blocked(self):
        return self.stamina > 0 or self.taken == 0


def facing_cos(px, pz, fx, fz, ax, az):
    """cos of the angle between the facing (fx, fz) at (px, pz) and the direction to (ax, az)."""
    dx, dz = ax - px, az - pz
    d = (dx * dx + dz * dz) ** 0.5
    if d < 1e-6:
        return 1.0
    return (fx * dx + fz * dz) / d


def block(dmg, cos, shield, stamina):
    """How a raised `shield` deals with a blow of `dmg` from a direction `cos` (see facing_cos) when
    you have `stamina` (0..1) left. Blows from the side or behind are not blocked at all."""
    if cos < FRONT:
        return Block(dmg, 0.0, False)
    stopped = dmg * shield.guard
    cost = stopped / shield.stability
    if cost <= stamina:
        return Block(rround(dmg - stopped), cost, False)
    # Not enough ST: the shield takes what ST can pay for and the rest comes through.
    held = stamina * shield.stability
    return Block(max(rround(dmg - held), 1), stamina, True)
