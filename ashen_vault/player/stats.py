from ashen_vault.util import rround


class Stats:
    FIELDS = ("level", "exp", "hp", "max_hp", "mp", "max_mp", "strength", "magic")

    def __init__(self, level=1, exp=0, hp=40, max_hp=40, mp=16, max_mp=16, strength=6, magic=4):
        self.level = level
        self.exp = exp
        self.hp = hp
        self.max_hp = max_hp
        self.mp = mp
        self.max_mp = max_mp
        self.strength = strength
        self.magic = magic

    @staticmethod
    def exp_for(level):
        return rround(30 * (level ** 1.6))

    @property
    def next_level_exp(self):
        return Stats.exp_for(self.level)

    @property
    def dead(self):
        return self.hp <= 0

    def gain_exp(self, amount):
        """Adds experience; returns the number of levels gained."""
        self.exp += amount
        gained = 0
        while self.exp >= self.next_level_exp:
            self.exp -= self.next_level_exp
            self.level += 1
            self.max_hp += 6
            self.max_mp += 3
            self.strength += 1
            self.magic += 1
            self.hp = self.max_hp
            self.mp = self.max_mp
            gained += 1
        return gained

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.max_hp)

    def restore_mp(self, amount):
        self.mp = min(self.mp + amount, self.max_mp)

    def hurt(self, amount):
        self.hp = max(self.hp - amount, 0)

    def spend_mp(self, cost):
        if self.mp < cost:
            return False
        self.mp -= cost
        return True

    def to_h(self):
        return {f: getattr(self, f) for f in self.FIELDS}

    @classmethod
    def from_h(cls, h):
        return cls(**{k: v for k, v in h.items() if k in cls.FIELDS})
