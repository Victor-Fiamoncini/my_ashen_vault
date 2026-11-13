from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    kind: str
    price: int = 0
    desc: str = ""
    power: int | None = None
    reach: float | None = None
    speed: float | None = None
    heal: int | None = None
    mana: int | None = None
    spell: str | None = None
    category: str | None = None  # weapons: see player/weapons.py


class Items:
    ALL: ClassVar[dict[str, Item]] = {
        i.id: i
        for i in [
            Item(
                id="rusted_sword",
                name="Rusted Sword",
                kind="weapon",
                category="sword",
                price=0,
                power=8,
                reach=2.1,
                speed=1.4,
                desc="Pitted and dull, but it still cuts.",
            ),
            Item(
                id="ashblade",
                name="Ashblade",
                kind="weapon",
                category="sword",
                price=180,
                power=15,
                reach=2.4,
                speed=1.7,
                desc="Forged from the grey iron of the old keep.",
            ),
            Item(
                id="bastard_sword",
                name="Bastard Sword",
                kind="weapon",
                category="sword",
                price=130,
                power=12,
                reach=2.5,
                speed=1.6,
                desc="A hand-and-a-half blade with a long grip.",
            ),
            Item(
                id="claymore",
                name="Claymore",
                kind="weapon",
                category="greatsword",
                price=260,
                power=18,
                reach=2.8,
                speed=2.3,
                desc="A highland greatsword. Its sweep cuts through crowds.",
            ),
            Item(
                id="zweihander",
                name="Zweihander",
                kind="weapon",
                category="greatsword",
                price=380,
                power=24,
                reach=3.0,
                speed=2.8,
                desc="Taller than its bearer. Slow, and ruinous when it lands.",
            ),
            Item(
                id="katana",
                name="Katana",
                kind="weapon",
                category="katana",
                price=200,
                power=11,
                reach=2.3,
                speed=1.1,
                desc="A curved blade from across the sea. Its heavy lunges forward.",
            ),
            Item(
                id="leather_whip",
                name="Leather Whip",
                kind="weapon",
                category="whip",
                price=90,
                power=6,
                reach=3.6,
                speed=1.2,
                desc="Braided hide. Weak, but it reaches far and lashes wide.",
            ),
            Item(
                id="mace",
                name="Flanged Mace",
                kind="weapon",
                category="mace",
                price=140,
                power=12,
                reach=1.9,
                speed=1.6,
                desc="Iron flanges that ignore armor. Its heavy always staggers.",
            ),
            Item(
                id="war_hammer",
                name="War Hammer",
                kind="weapon",
                category="hammer",
                price=300,
                power=22,
                reach=2.0,
                speed=2.6,
                desc="A block of iron on a long haft. Its heavy slams all around you.",
            ),
            Item(
                id="padded_coat",
                name="Padded Coat",
                kind="armor",
                price=0,
                power=2,
                desc="Quilted wool. Better than nothing.",
            ),
            Item(
                id="ringmail",
                name="Ringmail",
                kind="armor",
                price=140,
                power=6,
                desc="Linked iron rings, heavy on the shoulders.",
            ),
            Item(
                id="red_tonic",
                name="Red Tonic",
                kind="consumable",
                price=20,
                heal=30,
                desc="Bitter red draught. Restores 30 HP.",
            ),
            Item(
                id="blue_moss",
                name="Blue Moss",
                kind="consumable",
                price=25,
                mana=15,
                desc="Glowing moss from the cliffs. Restores 15 MP.",
            ),
            Item(
                id="scroll_mend",
                name="Scroll of Mend",
                kind="scroll",
                price=90,
                spell="mend",
                desc="Teaches the healing rite of Mend.",
            ),
            Item(
                id="scroll_lumen",
                name="Scroll of Lumen",
                kind="scroll",
                price=0,
                spell="lumen",
                desc="Teaches Lumen, a light that pushes back the dark.",
            ),
            Item(
                id="cell_key",
                name="Cell Key",
                kind="key",
                price=0,
                desc="A small iron key, flaked with rust.",
            ),
            Item(
                id="warden_key",
                name="Warden's Key",
                kind="key",
                price=0,
                desc="A heavy key stamped with a tower.",
            ),
            Item(
                id="ember_sigil",
                name="Ember Sigil",
                kind="key",
                price=0,
                desc="A warm stone disc. The bell-keeper is waiting for it.",
            ),
            Item(
                id="briar_key",
                name="Briar Key",
                kind="key",
                price=0,
                desc="Black wood, grown into the shape of a key rather than carved.",
            ),
            Item(
                id="verdant_sigil",
                name="Verdant Sigil",
                kind="key",
                price=0,
                desc="A cool disc of green glass with a living leaf sealed inside. It hums.",
            ),
        ]
    }

    # What you fight with when no weapon is equipped. Not an inventory item.
    FISTS = Item(
        id="fists",
        name="Bare Hands",
        kind="weapon",
        category="fists",
        price=0,
        power=3,
        reach=1.6,
        speed=0.9,
        desc="Your own two fists.",
    )

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]
