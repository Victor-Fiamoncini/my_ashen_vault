from dataclasses import dataclass


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


class Items:
    ALL = {i.id: i for i in [
        Item(id="rusted_sword", name="Rusted Sword", kind="weapon", price=0, power=8, reach=2.1, speed=1.4,
             desc="Pitted and dull, but it still cuts."),
        Item(id="ashblade", name="Ashblade", kind="weapon", price=180, power=15, reach=2.4, speed=1.7,
             desc="Forged from the grey iron of the old keep."),
        Item(id="padded_coat", name="Padded Coat", kind="armor", price=0, power=2,
             desc="Quilted wool. Better than nothing."),
        Item(id="ringmail", name="Ringmail", kind="armor", price=140, power=6,
             desc="Linked iron rings, heavy on the shoulders."),
        Item(id="red_tonic", name="Red Tonic", kind="consumable", price=20, heal=30,
             desc="Bitter red draught. Restores 30 HP."),
        Item(id="blue_moss", name="Blue Moss", kind="consumable", price=25, mana=15,
             desc="Glowing moss from the cliffs. Restores 15 MP."),
        Item(id="scroll_mend", name="Scroll of Mend", kind="scroll", price=90, spell="mend",
             desc="Teaches the healing rite of Mend."),
        Item(id="scroll_lumen", name="Scroll of Lumen", kind="scroll", price=0, spell="lumen",
             desc="Teaches Lumen, a light that pushes back the dark."),
        Item(id="cell_key", name="Cell Key", kind="key", price=0, desc="A small iron key, flaked with rust."),
        Item(id="warden_key", name="Warden's Key", kind="key", price=0, desc="A heavy key stamped with a tower."),
        Item(id="ember_sigil", name="Ember Sigil", kind="key", price=0,
             desc="A warm stone disc. The bell-keeper is waiting for it."),
    ]}

    # What you fight with when no weapon is equipped. Not an inventory item.
    FISTS = Item(id="fists", name="Bare Hands", kind="weapon", price=0, power=3, reach=1.6, speed=0.9,
                 desc="Your own two fists.")

    @classmethod
    def get(cls, id_):
        return cls.ALL[id_]
