"""Ailments: what certain foes build up in you with each blow that lands. Pure logic, no raylib.

Every ailment has a meter that fills by a foe's `inflicts` (`EnemyType.inflicts`) whenever its blow or
shot gets through (a blocked one adds nothing) and drains on its own when left alone. When a meter
fills (`FULL`) the ailment takes hold:

- poison: you lose `POISON_SHARE` of your max HP every `TICK` for `POISON_TIME`, and ST refills at
  `POISON_REFILL`. It can kill.
- bleed: the wound bursts at once for `BLEED_SHARE` of your max HP.
- rot: your HP can't rise past `ROT_CAP` of its maximum until you rest or are cured.
- corrosion: every piece of gear you hold or wear loses `CORRODE_WEAR` durability.
- frost (Frostbite, Vesperholm's moon-frost): it bursts for `FROSTBITE_SHARE` of your max HP, freezes
  your legs (`FROZEN` speed) for the first `FREEZE_TIME` seconds, and for `FROST_TIME` in all ST refills
  at `FROST_REFILL`.

Poison, rot and frost linger (`active`); while one does, its meter builds no further. Tamsin's remedies
cure them (`Item.cures`), and a shrine rest or waking after death clears everything (`Player.revive`)."""

from dataclasses import dataclass

from ashen_vault.util import rround


@dataclass(frozen=True)
class Kind:
    id: str
    label: str  # the HUD's three tiny letters
    rgb: tuple  # the HUD bar's colour
    decay: float  # meter points drained a second while nothing builds it


KINDS = {
    k.id: k
    for k in (
        Kind("poison", "PSN", (120, 190, 60), 4.0),
        Kind("bleed", "BLD", (200, 30, 40), 12.0),
        Kind("rot", "ROT", (150, 140, 125), 2.0),
        Kind("corrosion", "COR", (190, 110, 50), 8.0),
        Kind("frost", "FRS", (150, 200, 255), 6.0),
    )
}
ORDER = tuple(KINDS)  # the HUD stacks the bars in this order, from the vitals box up

FULL = 100.0  # a meter that reaches this takes hold
TICK = 1.0  # seconds between poison's bites
POISON_TIME = 30.0
POISON_SHARE = 0.02  # of max HP, each tick
POISON_REFILL = 0.5  # ST refills this much as fast while poisoned
BLEED_SHARE = 0.25  # of max HP, at once
ROT_CAP = 0.8  # the share of max HP you can have while rotting
CORRODE_WEAR = 8  # durability every held and worn piece loses
FROST_TIME = 20.0  # seconds Frostbite lingers
FROSTBITE_SHARE = 0.15  # of max HP, at once, as it takes hold
FREEZE_TIME = 3.0  # its first seconds, your legs frozen
FROZEN = 0.3  # speed multiplier while frozen
FROST_REFILL = 0.5  # ST refills this much as fast while frostbitten
FLARE_TIME = 2.5  # seconds a one-off ailment (bleed, corrosion) shows at the screen's edges once it strikes
FLARES = ("bleed", "corrosion")
POISON_FADE = 2.0  # poison's border fades over its last seconds
ROT_BORDER = 0.6  # how strongly rot shows at the edges while it lingers
FROST_LINGER = 0.35  # how strongly Frostbite shows once your legs thaw


def poison_bite(max_hp):
    return max(rround(max_hp * POISON_SHARE), 1)


def bleed_burst(max_hp):
    return max(rround(max_hp * BLEED_SHARE), 1)


def frostbite_burst(max_hp):
    return max(rround(max_hp * FROSTBITE_SHARE), 1)


def border_tint(strengths):
    """The shared edge glow for the ailments in `strengths` (kind -> 0..1): their colours mixed by
    strength, and how strong the glow is (their sum, capped at 1). None when nothing shows."""
    total = sum(strengths.values())
    if total <= 0:
        return None
    rgb = tuple(rround(sum(KINDS[k].rgb[i] * b for k, b in strengths.items()) / total) for i in range(3))
    return rgb, min(total, 1.0)


def rot_cap(max_hp):
    return max(rround(max_hp * ROT_CAP), 1)


class Ailments:
    def __init__(self):
        self.meters = dict.fromkeys(ORDER, 0.0)
        self.poison_t = 0.0  # seconds of poison left
        self.poison_tick = TICK  # seconds to its next bite
        self.rotted = False
        self.frost_t = 0.0  # seconds of Frostbite left
        self.flare = dict.fromkeys(FLARES, 0.0)  # seconds left of a one-off ailment's border (not saved)

    @property
    def poisoned(self):
        return self.poison_t > 0

    @property
    def frostbitten(self):
        return self.frost_t > 0

    @property
    def frozen(self):
        """Frostbite's first FREEZE_TIME seconds, while your legs are frozen."""
        return self.frost_t > FROST_TIME - FREEZE_TIME

    def active(self, kind):
        return (
            (kind == "poison" and self.poisoned)
            or (kind == "rot" and self.rotted)
            or (kind == "frost" and self.frostbitten)
        )

    def build(self, kind, amount):
        """Adds `amount` to `kind`'s meter. Returns True when that fills it and the ailment takes hold;
        the meter then empties (poison, rot and frost start lingering)."""
        if kind not in self.meters or amount <= 0 or self.active(kind):
            return False
        self.meters[kind] = min(self.meters[kind] + amount, FULL)
        if self.meters[kind] < FULL:
            return False
        self.meters[kind] = 0.0
        if kind in self.flare:
            self.flare[kind] = FLARE_TIME
        if kind == "poison":
            self.poison_t = POISON_TIME
            self.poison_tick = TICK
        elif kind == "rot":
            self.rotted = True
        elif kind == "frost":
            self.frost_t = FROST_TIME
        return True

    def update(self, dt, max_hp):
        """Drains the meters, thaws Frostbite and lets poison bite. Returns the HP poison takes this
        frame."""
        for kind, value in self.meters.items():
            if value > 0:
                self.meters[kind] = max(value - KINDS[kind].decay * dt, 0.0)
        self.frost_t = max(self.frost_t - dt, 0.0)
        for kind, value in self.flare.items():
            self.flare[kind] = max(value - dt, 0.0)
        if not self.poisoned:
            return 0
        lost = 0
        self.poison_t = max(self.poison_t - dt, 0.0)
        self.poison_tick -= dt
        while self.poison_tick <= 0:
            self.poison_tick += TICK
            lost += poison_bite(max_hp)
        if not self.poisoned:
            self.poison_tick = TICK
        return lost

    def clear(self, kind=None):
        """Cures `kind` (its meter and what lingers), or every ailment when None."""
        for k in ORDER if kind is None else (kind,):
            self.meters[k] = 0.0
            if k in self.flare:
                self.flare[k] = 0.0
            if k == "poison":
                self.poison_t = 0.0
                self.poison_tick = TICK
            elif k == "rot":
                self.rotted = False
            elif k == "frost":
                self.frost_t = 0.0

    def share(self, kind):
        """How full the HUD draws `kind`'s bar: the poison (or Frostbite) left while it lingers, full
        while rotting, else its meter."""
        if kind == "poison" and self.poisoned:
            return self.poison_t / POISON_TIME
        if kind == "frost" and self.frostbitten:
            return self.frost_t / FROST_TIME
        if kind == "rot" and self.rotted:
            return 1.0
        return self.meters[kind] / FULL

    def building(self):
        """The ailments the HUD shows: building up or lingering, in `ORDER`."""
        return [k for k in ORDER if self.meters[k] > 0 or self.active(k)]

    def border(self, kind):
        """How strongly `kind` shows at the screen's edges, 0..1: lingering ailments while they last
        (poison fading over its last `POISON_FADE` seconds, Frostbite strongest while your legs are
        frozen), one-off ones for `FLARE_TIME` after they strike."""
        if kind == "poison":
            return min(self.poison_t / POISON_FADE, 1.0)
        if kind == "rot":
            return ROT_BORDER if self.rotted else 0.0
        if kind == "frost":
            return 1.0 if self.frozen else (FROST_LINGER if self.frostbitten else 0.0)
        return self.flare.get(kind, 0.0) / FLARE_TIME

    def borders(self):
        """Every ailment showing at the screen's edges and how strongly, in `ORDER`."""
        return {k: b for k in ORDER if (b := self.border(k)) > 0}

    def to_h(self):
        return {
            "meters": dict(self.meters),
            "poison_t": self.poison_t,
            "rotted": self.rotted,
            "frost_t": self.frost_t,
        }

    @classmethod
    def from_h(cls, h):
        a = cls()
        if not h:
            return a
        for k, v in (h.get("meters") or {}).items():
            if k in a.meters:
                a.meters[k] = min(max(float(v), 0.0), FULL)
        a.poison_t = min(max(float(h.get("poison_t", 0.0)), 0.0), POISON_TIME)
        a.rotted = bool(h.get("rotted", False))
        a.frost_t = min(max(float(h.get("frost_t", 0.0)), 0.0), FROST_TIME)
        return a
