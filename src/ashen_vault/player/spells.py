from dataclasses import dataclass
from typing import ClassVar

from ashen_vault.player.combat import Combat


@dataclass(frozen=True)
class Spell:
    id: str
    name: str
    cost: int
    desc: str


class Spells:
    ALL: ClassVar[dict[str, Spell]] = {
        s.id: s
        for s in [
            Spell(id="flame", name="Flame Bolt", cost=5, desc="Hurl a bolt of fire."),
            Spell(id="mend", name="Mend", cost=8, desc="Close your wounds."),
            Spell(id="lumen", name="Lumen", cost=4, desc="Light the dark around you for a while."),
            Spell(id="venom", name="Venom Dart", cost=6, desc="Spit a dart of bog venom that festers."),
            Spell(id="veil", name="Veil of Mist", cost=7, desc="Wrap yourself in mist; foes overlook you."),
            Spell(
                id="pyre", name="Pyre", cost=6, desc="Breathe a short gout of fire. Kindles cold braziers."
            ),
        ]
    }
    LUMEN_DURATION = 45.0
    VEIL_DURATION = 20.0
    PYRE_REACH = 3.2  # metres the gout of fire reaches
    FLAMMABLE_MULT = 1.5  # plant foes take this much more from fire
    BURN = (3.0, 4)  # seconds and HP per second that Pyre leaves a plant foe burning

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @staticmethod
    def flame_damage(magic, gauge):
        return Combat.damage(base=10, strength=magic * 2, gauge=gauge, defense=0)

    @staticmethod
    def mend_amount(magic):
        return 20 + magic * 3

    @staticmethod
    def venom_damage(magic, gauge):
        """The dart's sting on impact; the venom does the rest (venom_poison)."""
        return Combat.damage(base=4, strength=magic, gauge=gauge, defense=0)

    @staticmethod
    def venom_poison(magic):
        """(seconds, HP per second) the venom keeps eating at whatever it struck."""
        return 6.0, 2 + magic // 2

    @staticmethod
    def pyre_damage(magic, gauge, flammable=False):
        mult = Spells.FLAMMABLE_MULT if flammable else 1.0
        return Combat.damage(base=8, strength=magic * 2, gauge=gauge, defense=0, mult=mult)
