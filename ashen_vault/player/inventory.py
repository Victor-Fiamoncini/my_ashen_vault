from ashen_vault.player.items import Items


class Inventory:
    def __init__(self, counts=None, weapon="rusted_sword", armor="padded_coat", gold=0):
        self.counts = dict(counts or {})
        self.weapon = weapon
        self.armor = armor
        self.gold = gold
        if weapon and not self.has(weapon):
            self.add(weapon)
        if armor and not self.has(armor):
            self.add(armor)

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

    def equip(self, id_):
        item = Items.get(id_)
        if not self.has(id_):
            return False
        if item.kind == "weapon":
            self.weapon = id_
        elif item.kind == "armor":
            self.armor = id_
        else:
            return False
        return True

    def equipped(self, id_):
        return id_ in (self.weapon, self.armor)

    def unequip(self, id_):
        """Takes off the weapon or armor `id_`; returns False if it wasn't equipped."""
        if self.weapon == id_:
            self.weapon = None
        elif self.armor == id_:
            self.armor = None
        else:
            return False
        return True

    def weapon_item(self):
        return Items.get(self.weapon) if self.weapon else Items.FISTS

    def armor_item(self):
        return Items.get(self.armor) if self.armor else None

    @property
    def defense(self):
        a = self.armor_item()
        return (a.power or 0) if a else 0

    def buy(self, id_):
        price = Items.get(id_).price
        if self.gold < price:
            return False
        self.gold -= price
        self.add(id_)
        return True

    def to_h(self):
        return {"counts": dict(self.counts), "weapon": self.weapon, "armor": self.armor, "gold": self.gold}

    @classmethod
    def from_h(cls, h):
        return cls(counts=dict(h.get("counts") or {}), weapon=h.get("weapon"), armor=h.get("armor"),
                   gold=h.get("gold"))
