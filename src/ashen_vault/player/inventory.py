from ashen_vault.player.items import Item, Items

RIGHT, LEFT = "right", "left"  # the right hand is the left mouse button, the left hand the right one
HANDS = (RIGHT, LEFT)
ARMOR_SLOTS = ("body", "hands")
SPELL = "spell"  # what a hand holds when it is ready to cast the selected spell

# Stands in for the readied spell when a hand holds it. Not an inventory item.
SPELL_HAND = Item(id=SPELL, name="Spell", kind="spell", desc="An open hand, ready to cast.")


def other(hand):
    return LEFT if hand == RIGHT else RIGHT


class Inventory:
    """What you carry and what you wear. Each hand holds a weapon, a shield, the readied spell
    (`SPELL`) or nothing (your fist); a two-handed weapon fills both. Armor has a body and a hands slot.
    """

    def __init__(
        self,
        counts=None,
        right="rusted_sword",
        left=SPELL,
        body="padded_coat",
        hands=None,
        gold=0,
    ):
        self.counts = dict(counts or {})
        self.slots = {RIGHT: right, LEFT: left, "body": body, "hands": hands}
        self.gold = gold or 0
        for slot, id_ in self.slots.items():
            if id_ and id_ != SPELL and not self.has(id_):
                self.add(id_)
            if slot in HANDS and id_ and id_ != SPELL and Items.get(id_).two_handed:
                self.slots[other(slot)] = id_

    # --- carrying -----------------------------------------------------------------

    def add(self, id_, n=1):
        key = Items.get(id_).id
        self.counts[key] = self.counts.get(key, 0) + n
        return self.counts[key]

    def has(self, id_):
        return self.counts.get(id_, 0) > 0

    def count(self, id_):
        return self.counts.get(id_, 0)

    def remove(self, id_, n=1):
        if self.count(id_) < n:
            return False
        self.counts[id_] -= n
        if self.counts[id_] == 0:
            del self.counts[id_]
        return True

    def items(self):
        return [Items.get(i) for i in self.counts]

    def buy(self, id_):
        price = Items.get(id_).price
        if self.gold < price:
            return False
        self.gold -= price
        self.add(id_)
        return True

    # --- equipment ------------------------------------------------------------------

    @property
    def right(self):
        return self.slots[RIGHT]

    @property
    def left(self):
        return self.slots[LEFT]

    @property
    def body(self):
        return self.slots["body"]

    @property
    def hands(self):
        return self.slots["hands"]

    @staticmethod
    def default_hand(item):
        """Where Enter puts an item: weapons in the right hand, shields and spells in the left."""
        return RIGHT if item.kind == "weapon" else LEFT

    def equip_error(self, id_, level=None):
        """Why `id_` can't be equipped ("missing", "kind", "level"), or None if it can."""
        if id_ == SPELL:
            return None
        item = Items.ALL.get(id_)
        if item is None or not self.has(id_):
            return "missing"
        if item.kind not in ("weapon", "shield", "armor"):
            return "kind"
        if level is not None and level < item.level:
            return "level"
        return None

    def equip(self, id_, hand=None, level=None):
        """Wears armor in its slot, or puts a weapon, shield or the spell (`SPELL`) in `hand` (its
        default hand when None). A two-hander fills both hands and leaves them both when replaced.
        Returns False when the item can't be equipped."""
        if self.equip_error(id_, level):
            return False
        item = SPELL_HAND if id_ == SPELL else Items.get(id_)
        if item.kind == "armor":
            self.slots[item.slot or "body"] = id_
            return True
        hand = hand or self.default_hand(item)
        for h in HANDS:  # drop a two-hander from both hands first
            held = self.slots[h]
            if held and held != SPELL and Items.get(held).two_handed:
                self.slots[RIGHT] = self.slots[LEFT] = None
                break
        if item.two_handed:
            self.slots[RIGHT] = self.slots[LEFT] = id_
            return True
        # Only one of each item fits your hands unless you carry two of them.
        if id_ != SPELL and self.slots[other(hand)] == id_ and self.count(id_) < 2:
            self.slots[other(hand)] = None
        if id_ == SPELL and self.slots[other(hand)] == SPELL:
            self.slots[other(hand)] = None
        self.slots[hand] = id_
        return True

    def equipped(self, id_):
        return id_ in self.slots.values()

    def unequip(self, id_):
        """Takes `id_` off wherever it is worn or held; returns False if it wasn't equipped."""
        hit = False
        for slot, held in self.slots.items():
            if held == id_:
                self.slots[slot] = None
                hit = True
        return hit

    def hand_item(self, hand):
        """What `hand` holds: an Item, SPELL_HAND, or Items.FISTS when it is empty."""
        held = self.slots[hand]
        if held is None:
            return Items.FISTS
        return SPELL_HAND if held == SPELL else Items.get(held)

    def two_handing(self):
        return self.right is not None and self.right != SPELL and Items.get(self.right).two_handed

    def shield_hand(self):
        """The hand holding a shield (the right one first), or None."""
        for h in HANDS:
            if self.hand_item(h).kind == "shield":
                return h
        return None

    def weapon_item(self):
        """The main weapon: the right hand's, else the left hand's, else your fists."""
        for h in HANDS:
            item = self.hand_item(h)
            if item.kind == "weapon":
                return item
        return Items.FISTS

    def body_item(self):
        return Items.get(self.body) if self.body else None

    def hands_item(self):
        return Items.get(self.hands) if self.hands else None

    def armor_item(self):
        return self.body_item()

    @property
    def defense(self):
        return sum((a.power or 0) for a in (self.body_item(), self.hands_item()) if a)

    def to_h(self):
        return {"counts": dict(self.counts), **self.slots, "gold": self.gold}

    @classmethod
    def from_h(cls, h):
        """Reads a save; saves from before hand slots had one `weapon` and one `armor`, and the spell in
        the right mouse button (now the left hand)."""
        counts = dict(h.get("counts") or {})
        if "right" in h:
            inv = cls(counts=counts, right=None, left=None, body=None, gold=h.get("gold"))
            inv.slots.update({k: h.get(k) for k in (*HANDS, *ARMOR_SLOTS)})
            return inv
        return cls(counts=counts, right=h.get("weapon"), left=SPELL, body=h.get("armor"), gold=h.get("gold"))
