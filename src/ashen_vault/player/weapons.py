"""Weapon categories and their light / heavy attacks. Pure data, no raylib."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Attack:
    name: str
    motion: str  # animation key: slash | sweep | chop | thrust | lash | slam | jab | hook
    damage: float = 1.0  # multiplier on Combat.damage
    reach: float = 1.0  # multiplier on the weapon's reach
    cone: float = 0.6  # min cos(angle) between facing and target; below 0 hits all around
    targets: int = 1  # most enemies one swing can hit
    poise: float = 1.0  # multiplier on the stagger check against enemy poise
    stamina: float = 0.0  # ST spent (0..1)
    lunge: float = 0.0  # metres stepped forward as the hit lands
    pierce_def: bool = False  # ignores enemy defence

    @property
    def heavy(self):
        return self.stamina > 0


CHARGE_TIME = 0.35  # seconds LMB must be held for a heavy attack
HEAVY_TIME = 1.5  # heavy swings take this much longer than light ones

MOVESETS = {
    "fists": (
        Attack("Jab", "jab"),
        Attack("Hook", "hook", damage=1.4, poise=1.5, stamina=0.2),
    ),
    "sword": (
        Attack("Slash", "slash"),
        Attack("Overhead chop", "chop", damage=1.6, poise=1.5, stamina=0.3),
    ),
    "greatsword": (
        Attack("Wide sweep", "sweep", cone=0.25, targets=3),
        Attack("Overhead cleave", "chop", damage=2.0, poise=2.0, stamina=0.45),
    ),
    "katana": (
        Attack("Quick slash", "slash"),
        Attack("Lunging thrust", "thrust", damage=1.7, reach=1.4, cone=0.8, lunge=1.0, stamina=0.3),
    ),
    "whip": (
        Attack("Crack", "lash", cone=0.85),
        Attack("Wide lash", "sweep", damage=1.2, cone=0.1, targets=4, stamina=0.3),
    ),
    "mace": (
        Attack("Bash", "slash", pierce_def=True),
        Attack("Crush", "chop", damage=1.8, poise=2.5, pierce_def=True, stamina=0.35),
    ),
    "hammer": (
        Attack("Smash", "chop", poise=1.5),
        Attack("Ground slam", "slam", damage=1.5, reach=1.1, cone=-1, targets=8, poise=2.0, stamina=0.5),
    ),
}

CATEGORY_NAMES = {
    "fists": "Fists",
    "sword": "Sword",
    "greatsword": "Greatsword",
    "katana": "Katana",
    "whip": "Whip",
    "mace": "Mace",
    "hammer": "Hammer",
}


def moveset(item):
    return MOVESETS[item.category or "sword"]


def attack(item, heavy=False):
    """The light or heavy attack of a weapon item."""
    return moveset(item)[1 if heavy else 0]
