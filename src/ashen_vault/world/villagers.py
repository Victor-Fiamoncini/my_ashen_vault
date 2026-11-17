"""How each villager of Harrowmere looks: build, clothes, hair and what they hold. Pure data, no raylib;
`models.npc` draws a `Look`."""

from dataclasses import dataclass

BUILDS = {
    # (height scale, shoulder width scale, forward stoop in radians)
    "average": (1.0, 1.0, 0.0),
    "stout": (0.95, 1.22, 0.0),
    "slight": (1.03, 0.86, 0.0),
    "stooped": (0.92, 0.95, 0.28),
    "tall": (1.12, 1.05, 0.0),
}
GARBS = ("tunic", "robe", "kimono")
HAIR_STYLES = ("short", "long", "bald", "bun", "topknot")
HATS = (None, "brim", "cap", "coif")
TOOLS = (None, "hammer", "spear", "ladle", "staff", "ledger", "rod", "whetstone", "tankard", "lantern")
IDLES = ("sway", "hammer", "watch", "stir", "pray", "count", "smith", "ready")
BEARDS = (None, "short", "long")
BLADES = (None, "back", "hip")
SLEEVES = ("full", "rolled")

# The smith's work, a loop of stages (name, seconds): four blows on the billet, a turn of it in the
# tongs, a long look at it held up to the light, and a wipe of the brow before he starts again.
SMITH_BEAT = 0.8  # seconds per hammer blow
SMITH_BLOWS = 4
SMITH_STAGES = (("strike", SMITH_BEAT * SMITH_BLOWS), ("turn", 1.2), ("inspect", 1.8), ("wipe", 1.4))
SMITH_LOOP = sum(d for _, d in SMITH_STAGES)
SMITH_LAND = 0.55  # share of a beat at which the hammer lands on the anvil


def smith_cycle(t):
    """(stage, k) of the smith's work at time `t`: k runs 0..1 through the stage, except while striking,
    where it runs 0..1 through each blow (the hammer lands at SMITH_LAND)."""
    left = t % SMITH_LOOP
    for name, d in SMITH_STAGES:
        if left < d:
            if name == "strike":
                return name, (left / SMITH_BEAT) % 1.0
            return name, left / d
        left -= d
    return SMITH_STAGES[-1][0], 1.0  # pragma: no cover - float rounding at the loop's very end


def smith_blows(t0, t1):
    """How many times the smith's hammer lands on the anvil between `t0` (exclusive) and `t1`."""

    def landed(t):  # blows landed from time 0 up to t
        loops, left = divmod(t, SMITH_LOOP)
        return loops * SMITH_BLOWS + min(
            max(int((left - SMITH_LAND * SMITH_BEAT) // SMITH_BEAT) + 1, 0), SMITH_BLOWS
        )

    return int(landed(t1) - landed(t0))


# A swordmaster's stillness: now and then he eases a hand's width of steel out of the scabbard and
# pushes it home again.
DRAW_EVERY = 6.0  # seconds between half-draws
DRAW_TIME = 2.2  # how long one takes, out and back
DRAW_SHOWN = 0.12  # metres of steel it shows at most


def half_draw(t):
    """Metres of blade showing above the scabbard's mouth at time `t` (0 most of the time)."""
    k = (t % DRAW_EVERY) / DRAW_TIME
    if k >= 1:
        return 0.0
    return DRAW_SHOWN * min(k / 0.35, 1.0, (1 - k) / 0.35)


@dataclass(frozen=True)
class Look:
    cloth: tuple = (110, 110, 110)  # tunic or robe
    hair: tuple = (70, 54, 40)
    skin: tuple = (196, 158, 120)
    build: str = "average"
    garb: str = "tunic"
    hair_style: str = "short"
    trousers: tuple = (70, 60, 50)
    boots: tuple = (48, 38, 30)
    belt: tuple = (60, 42, 28)
    apron: tuple | None = None
    cloak: tuple | None = None
    hood: bool = False
    hat: str | None = None
    hat_rgb: tuple = (80, 64, 44)
    beard: str | None = None  # "short": a block at the jaw; "long": tiers falling to the belt
    beard_tip: tuple | None = None  # a long beard's tip, if it greys or whitens toward the end
    tool: str | None = None
    blade: str | None = None  # a sheathed curved sword: slung across the "back", or thrust at the "hip"
    sleeves: str = "full"  # "rolled" bares the forearms
    gloves: tuple | None = None  # work gloves over the mitts
    pauldron: tuple | None = None  # a lacquered plate shoulder guard on the left shoulder
    sash: tuple = (60, 30, 30)  # a kimono's obi
    idle: str = "sway"

    def __post_init__(self):
        assert self.build in BUILDS, self.build
        assert self.garb in GARBS, self.garb
        assert self.hair_style in HAIR_STYLES, self.hair_style
        assert self.hat in HATS, self.hat
        assert self.tool in TOOLS, self.tool
        assert self.idle in IDLES, self.idle
        assert self.beard in BEARDS, self.beard
        assert self.blade in BLADES, self.blade
        assert self.sleeves in SLEEVES, self.sleeves


LOOKS = {
    "odrin": Look(
        cloth=(70, 60, 90), hair=(200, 200, 200), build="stooped", garb="robe", beard="short",
        cloak=(52, 46, 66), tool="staff", hair_style="long",
    ),
    "pell": Look(
        cloth=(120, 90, 40), hair=(90, 60, 34), build="stout", apron=(150, 130, 96), hat="cap",
        hat_rgb=(70, 52, 30), tool="ledger", idle="count",
    ),
    "hollis": Look(
        cloth=(80, 84, 90), hair=(40, 30, 22), cloak=(70, 50, 40), tool="spear", idle="watch",
        hat="coif", hat_rgb=(120, 120, 126),
    ),
    "maeve": Look(
        cloth=(60, 90, 100), hair=(140, 70, 40), build="slight", hair_style="long", tool="rod",
        trousers=(60, 56, 50),
    ),
    "corvane": Look(
        cloth=(70, 78, 92), hair=(214, 212, 204), skin=(168, 134, 104), build="tall", garb="kimono",
        hair_style="topknot", beard="long", trousers=(44, 44, 54), boots=(206, 200, 186),
        belt=(52, 40, 30), pauldron=(48, 44, 52), sash=(120, 108, 76), blade="hip", idle="ready",
    ),
    "brannoc": Look(
        cloth=(96, 70, 52), hair=(52, 34, 24), skin=(176, 128, 92), build="stout", hair_style="bald",
        beard="long", beard_tip=(120, 108, 96), apron=(84, 58, 38), tool="hammer", idle="smith",
        trousers=(54, 46, 40), sleeves="rolled", gloves=(92, 64, 40),
    ),
    "garrick": Look(
        cloth=(100, 40, 36), hair=(110, 90, 60), build="tall", cloak=(76, 30, 28), hat="coif",
        hat_rgb=(130, 130, 136), tool="spear", idle="watch", beard="short",
    ),
    "tamsin": Look(
        cloth=(84, 110, 66), hair=(60, 40, 30), build="slight", hair_style="bun", apron=(170, 160, 130),
        tool="ladle", idle="stir",
    ),
    "ilse": Look(
        cloth=(186, 180, 166), hair=(200, 180, 140), garb="robe", hood=True, cloak=(130, 120, 100),
        tool="staff", idle="pray",
    ),
    "wren": Look(
        cloth=(130, 74, 60), hair=(180, 120, 60), build="stout", hair_style="bun", apron=(190, 180, 160),
        tool="tankard",
    ),
}  # fmt: skip


def look(npc_id):
    """The look of a villager by id; strangers wear plain grey."""
    return LOOKS.get(npc_id, Look())
