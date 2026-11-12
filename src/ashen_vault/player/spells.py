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
        ]
    }
    LUMEN_DURATION = 45.0

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]

    @staticmethod
    def flame_damage(magic, gauge):
        return Combat.damage(base=10, strength=magic * 2, gauge=gauge, defense=0)

    @staticmethod
    def mend_amount(magic):
        return 20 + magic * 3
