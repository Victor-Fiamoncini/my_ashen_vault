from dataclasses import dataclass
from typing import ClassVar

from ashen_vault.player.combat import Combat
from ashen_vault.util import rround


@dataclass(frozen=True)
class Spell:
    id: str
    name: str
    cost: int
    desc: str
    recovery: float = 2.2  # seconds your focus (the magic gauge) takes to return after casting it


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
                id="pyre",
                name="Pyre",
                cost=6,
                desc="Breathe a short gout of fire. Kindles cold braziers.",
                recovery=1.3,  # a short-range spell: quick to loose again
            ),
            Spell(
                id="thunder", name="Thunder Spear", cost=8, desc="Hurl a spear of lightning. Iron hates it."
            ),
            Spell(id="motes", name="Arcane Motes", cost=7, desc="Loose three seeking sparks at your foes."),
            Spell(
                id="ward", name="Ashen Ward", cost=6, desc="Wreathe yourself in embers that blunt every blow."
            ),
            Spell(
                id="rift_lance",
                name="Rift Lance",
                cost=9,
                desc="Loose a shard of the rift's daylight. It runs through every foe in its path.",
                recovery=2.8,
            ),
            Spell(
                id="bellward",
                name="Bellward",
                cost=7,
                desc="Toll a phantom bell. Foes close about you reel from their swings.",
            ),
            Spell(
                id="mortar_shard",
                name="Mortar Shard",
                cost=7,
                desc="Hurl a shard of spent mortar-light. It cracks stone like a hammer.",
            ),
        ]
    }
    LUMEN_DURATION = 45.0
    VEIL_DURATION = 20.0
    WARD_DURATION = 15.0  # seconds the embers of an Ashen Ward circle you
    PYRE_REACH = 3.2  # metres the gout of fire reaches
    FLAMMABLE_MULT = 1.5  # plant foes take this much more from fire
    BURN = (3.0, 4)  # seconds and HP per second that Pyre leaves a plant foe burning
    THUNDER_SPEED = 16.0  # a thunder spear flies much faster than a flame bolt
    MOTES = 3  # sparks per cast of Arcane Motes
    MOTE_SPREAD = 0.35  # radians between them as they leave your hand
    MOTE_SPEED = 6.0
    MOTE_TURN = 3.2  # rad/s a mote can steer toward its mark
    RIFT_SPEED = 13.0  # a rift lance flies a little faster than a flame bolt...
    RIFT_WIDTH = 0.35  # ...and cuts this far to either side of its line
    RIFT_LIFE = 1.6  # seconds before it fades
    BELL_RADIUS = 4.5  # metres the phantom bell's toll reaches
    MORTAR_RGB = (150, 196, 182)  # a mortar shard: the grey-teal of the quenched light

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

    @staticmethod
    def thunder_damage(magic, gauge):
        return Combat.damage(base=14, strength=magic * 2, gauge=gauge, defense=0)

    @staticmethod
    def mote_damage(magic, gauge):
        """Each of the three sparks; all three landing beats a flame bolt."""
        return Combat.damage(base=5, strength=magic, gauge=gauge, defense=0)

    @staticmethod
    def rift_damage(magic, gauge):
        """Each foe the lance runs through: less than a thunder spear, but it never stops at one."""
        return Combat.damage(base=11, strength=magic * 2, gauge=gauge, defense=0)

    @staticmethod
    def bell_damage(magic, gauge):
        """The toll's bruise; the stagger is what it is for."""
        return Combat.damage(base=3, strength=magic, gauge=gauge, defense=0)

    @staticmethod
    def mortar_damage(magic, gauge):
        """A mortar shard's blow: a little under a flame bolt, but stone takes it like a hammer's
        (`elements.shot_mult`)."""
        return Combat.damage(base=9, strength=magic * 2, gauge=gauge, defense=0)

    @staticmethod
    def ward_cut(magic):
        """The share of every blow an Ashen Ward stops: a third at first, more with MAG, at most 60%."""
        return min(0.35 + 0.02 * magic, 0.6)

    @staticmethod
    def warded(dmg, magic):
        """What a blow of `dmg` still does through an Ashen Ward (a blow always does at least 1)."""
        if dmg <= 0:
            return dmg
        return max(rround(dmg * (1 - Spells.ward_cut(magic))), 1)

    @staticmethod
    def power(id_, magic):
        """What a full-gauge cast does at `magic`: damage (all three motes together), HP mended, the %
        of each blow a ward stops, or 0 for the rest. The Belongings stats panel compares it as SPL."""
        damage = {
            "flame": Spells.flame_damage,
            "venom": Spells.venom_damage,
            "pyre": Spells.pyre_damage,
            "thunder": Spells.thunder_damage,
            "rift_lance": Spells.rift_damage,
            "bellward": Spells.bell_damage,
            "mortar_shard": Spells.mortar_damage,
        }
        if id_ in damage:
            return damage[id_](magic, 1.0)
        if id_ == "motes":
            return Spells.MOTES * Spells.mote_damage(magic, 1.0)
        if id_ == "mend":
            return Spells.mend_amount(magic)
        if id_ == "ward":
            return rround(Spells.ward_cut(magic) * 100)
        return 0
