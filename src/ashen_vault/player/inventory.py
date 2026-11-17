from ashen_vault.player import durability
from ashen_vault.player.items import Item, Items

RIGHT, LEFT = "right", "left"  # the right hand is the left mouse button, the left hand the right one
HANDS = (RIGHT, LEFT)
# Players see slots, not hands: Primary is the left mouse button, Secondary the right one. The keys
# stay "right" / "left" so saves and `--equip right=` keep working.
PRIMARY, SECONDARY = RIGHT, LEFT
SLOT_NAMES = {PRIMARY: "Primary", SECONDARY: "Secondary"}
SLOT_ALIASES = {"primary": PRIMARY, "secondary": SECONDARY}
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
        self.wear = {}  # item id -> durability left; an id missing here is whole (player/durability.py)
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

    # --- durability -------------------------------------------------------------------

    @staticmethod
    def max_durability(id_):
        """The most durability item `id_` can have, or None if it never wears."""
        item = Items.ALL.get(id_)
        return durability.max_durability(item) if item else None

    def durability(self, id_):
        """What is left of `id_`'s durability, or None if it never wears."""
        top = self.max_durability(id_)
        if top is None:
            return None
        return min(self.wear.get(id_, top), top)

    def broken(self, id_):
        return self.durability(id_) == 0

    def worn(self, id_):
        """Badly worn: at or below `durability.WORN` of its maximum (broken included)."""
        left = self.durability(id_)
        return left is not None and left <= self.max_durability(id_) * durability.WORN

    def wear_down(self, id_, n=1):
        """Wears `id_` by `n`. Returns "broken" on the blow that breaks it, "worn" on the one that
        first leaves it badly worn, else None."""
        left = self.durability(id_)
        if left is None or left == 0 or n <= 0:
            return None
        was_worn = self.worn(id_)
        self.wear[id_] = max(left - n, 0)
        if self.wear[id_] == 0:
            return "broken"
        return "worn" if self.worn(id_) and not was_worn else None

    def repair(self, id_):
        """Mends `id_` whole; returns False if there was nothing to mend."""
        if id_ not in self.wear:
            return False
        del self.wear[id_]
        return True

    def missing(self, id_):
        """Points of durability `id_` has lost."""
        left = self.durability(id_)
        return 0 if left is None else self.max_durability(id_) - left

    def damaged(self, ids=None):
        """The gear among `ids` (default: everything carried) that has lost durability, by name."""
        ids = self.counts if ids is None else ids
        return sorted((Items.get(i) for i in ids if self.missing(i) > 0), key=lambda i: i.name)

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
        """Where an item goes by default: weapons in Primary, shields and spells in Secondary."""
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

    def button_action(self, hand):
        """What the mouse button of `hand` does: "swing" (a weapon or fist), "guard" (a shield),
        "cast" (the readied spell) or None. A two-hander swings only from Primary (the left button);
        Secondary then does nothing."""
        if hand == LEFT and self.two_handing():
            return None
        kind = self.hand_item(hand).kind
        return {"shield": "guard", "spell": "cast"}.get(kind, "swing")

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
        return sum(
            (a.power or 0) for a in (self.body_item(), self.hands_item()) if a and not self.broken(a.id)
        )

    def to_h(self):
        return {"counts": dict(self.counts), **self.slots, "gold": self.gold, "wear": dict(self.wear)}

    @classmethod
    def from_h(cls, h):
        """Reads a save; saves from before hand slots had one `weapon` and one `armor`, and the spell in
        the right mouse button (now the left hand). Items since taken out of the game come back as what
        replaced them (`Items.RENAMED`)."""
        new = Items.RENAMED.get
        counts = {}
        for id_, n in (h.get("counts") or {}).items():
            counts[new(id_, id_)] = counts.get(new(id_, id_), 0) + n
        if "right" in h:
            inv = cls(counts=counts, right=None, left=None, body=None, gold=h.get("gold"))
            inv.slots.update({k: new(h.get(k), h.get(k)) for k in (*HANDS, *ARMOR_SLOTS)})
        else:
            weapon = new(h.get("weapon"), h.get("weapon"))
            inv = cls(counts=counts, right=weapon, left=SPELL, body=h.get("armor"), gold=h.get("gold"))
        for id_, left in (h.get("wear") or {}).items():  # saves from before durability have none
            if inv.max_durability(new(id_, id_)) is not None:
                inv.wear[new(id_, id_)] = int(left)
        return inv
