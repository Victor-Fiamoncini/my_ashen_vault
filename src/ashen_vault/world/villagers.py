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
HATS = (None, "brim", "cap", "coif", "helm")
TOOLS = (
    None,
    "hammer",
    "spear",
    "ladle",
    "staff",
    "ledger",
    "rod",
    "whetstone",
    "tankard",
    "lantern",
    "halberd",
    "bucket",
)
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


# A sentry's watch: every so often he turns his head to look down the road, holds it, and turns back.
GLANCE_EVERY = 7.0  # seconds between glances
GLANCE_TIME = 3.0  # how long one takes, there and back
GLANCE_TURN = 0.55  # radians his head turns at most


def glance(t):
    """How far (radians, + to his left) a sentry's head is turned at time `t`: 0 most of the time."""
    k = (t % GLANCE_EVERY) / GLANCE_TIME
    if k >= 1:
        return 0.0
    side = 1 if int(t // GLANCE_EVERY) % 2 == 0 else -1
    return side * GLANCE_TURN * min(k / 0.25, 1.0, (1 - k) / 0.25)


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
    tabard: tuple | None = None  # the watch's surcoat over mail, the realm's crest on its breast
    shield: tuple | None = None  # a kite shield slung on the left arm, its face painted this colour
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
    # The Bell-keepers' Oubliette, under Old Harrowmere: three who knew too much of the first city.
    "aubel": Look(
        cloth=(84, 74, 58), hair=(196, 192, 182), skin=(170, 150, 128), build="stooped", garb="robe",
        hair_style="bald", beard="long", beard_tip=(226, 222, 214), cloak=(62, 54, 42), tool="lantern",
        idle="watch",
    ),
    "coldry": Look(
        cloth=(92, 88, 82), hair=(60, 50, 44), skin=(186, 160, 134), garb="robe", hood=True,
        apron=(120, 112, 98), gloves=(70, 64, 58), idle="pray", trousers=(64, 60, 56),
    ),
    "ysolde": Look(
        cloth=(54, 60, 92), hair=(150, 40, 34), skin=(200, 172, 146), build="slight", garb="robe",
        hair_style="long", cloak=(150, 116, 60), tool="ledger", idle="count",
    ),
    # Below them, in the Under-Cells: the gaoler who turned the key on the bell-keepers, gone to seed in
    # his old leathers, and the last Sister of the Mortar who kept its light, in a sea-grey robe.
    "brannick": Look(
        cloth=(74, 62, 50), hair=(128, 122, 114), skin=(178, 146, 118), build="stooped", hair_style="bald",
        beard="short", apron=(58, 46, 36), belt=(40, 32, 26), trousers=(56, 50, 44), boots=(42, 34, 28),
        gloves=(66, 52, 40), sleeves="rolled", tool="hammer", idle="sway",
    ),
    "sister_vell": Look(
        cloth=(68, 90, 86), hair=(176, 176, 168), skin=(190, 168, 150), build="slight", garb="robe",
        hair_style="long", hood=True, cloak=(48, 64, 62), apron=(108, 110, 102), gloves=(64, 70, 68),
        tool="staff", idle="pray",
    ),
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
    # The town watch at its gates, in the realm's colours: a kettle helm over mail, a tabard with the
    # crest on the breast, a halberd or a spear, and a kite shield on the arm.
    "aldous": Look(
        cloth=(92, 94, 100), hair=(96, 74, 50), skin=(184, 146, 110), build="stout", hat="helm",
        hat_rgb=(122, 124, 130), tool="halberd", idle="watch", beard="short", tabard=(118, 36, 34),
        shield=(118, 36, 34), trousers=(60, 54, 50), gloves=(76, 60, 44),
    ),
    "tobin": Look(
        cloth=(86, 88, 96), hair=(150, 104, 56), skin=(204, 166, 128), build="slight", hat="helm",
        hat_rgb=(112, 114, 120), tool="spear", idle="watch", tabard=(108, 34, 32), shield=(40, 52, 82),
        trousers=(66, 58, 48),
    ),
    "reyna": Look(
        cloth=(90, 90, 98), hair=(58, 40, 30), skin=(168, 128, 96), build="tall", hair_style="long",
        hat="helm", hat_rgb=(128, 128, 134), tool="halberd", idle="watch", tabard=(112, 38, 36),
        cloak=(64, 40, 36), trousers=(54, 50, 48), gloves=(70, 56, 42),
    ),
    "fenn": Look(
        cloth=(84, 86, 92), hair=(170, 168, 160), skin=(190, 150, 116), build="average", hat="helm",
        hat_rgb=(104, 106, 112), tool="spear", idle="watch", beard="long", beard_tip=(210, 208, 200),
        tabard=(104, 32, 30), shield=(118, 36, 34),
    ),
    # Wynn keeps the Vesper Gate, where the cold comes through: a heavy wool cloak over the tabard.
    "wynn": Look(
        cloth=(88, 90, 98), hair=(122, 82, 52), skin=(196, 156, 120), build="tall", hat="helm",
        hat_rgb=(118, 120, 128), tool="halberd", idle="watch", beard="short", tabard=(114, 36, 34),
        cloak=(70, 74, 86), shield=(118, 36, 34), trousers=(58, 54, 52), gloves=(68, 58, 48),
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
    # The townsfolk. Two at prayer in the cathedral's nave: an old widow in black, and the acolyte who
    # keeps its candles.
    "hedda": Look(
        cloth=(46, 42, 46), hair=(196, 192, 186), skin=(188, 160, 136), build="stooped", garb="robe",
        hair_style="bun", hood=True, cloak=(34, 32, 36), idle="pray",
    ),
    "aubrey": Look(
        cloth=(150, 140, 120), hair=(120, 84, 48), skin=(206, 172, 140), build="slight", garb="robe",
        hair_style="short", belt=(110, 86, 60), tool="lantern", idle="pray",
    ),
    # About the plaza: the flower seller with her basket's ladle, the crier with his ledger of
    # notices, and old Merrit, who begs by the bell.
    "lisbet": Look(
        cloth=(150, 96, 120), hair=(170, 110, 60), build="slight", hair_style="long",
        apron=(210, 200, 176), tool="ladle",
    ),
    "osric": Look(
        cloth=(40, 70, 110), hair=(80, 56, 36), build="tall", hat="brim", hat_rgb=(50, 40, 34),
        cloak=(110, 34, 34), tool="ledger", idle="count", beard="short",
    ),
    "merrit": Look(
        cloth=(98, 90, 76), hair=(130, 124, 116), skin=(176, 142, 112), build="stooped", hair_style="long",
        beard="long", beard_tip=(170, 166, 160), cloak=(74, 66, 56), hood=True, tool="staff",
        trousers=(80, 72, 60), boots=(60, 50, 40),
    ),
    # The neighbourhood: the weaver, the cooper, the midwife, the old sailor, the baker, and out in
    # the lane the fisherman's wife, hauling a bucket of water home, and the lamplighter.
    "tilde": Look(
        cloth=(160, 120, 70), hair=(90, 50, 30), build="average", hair_style="bun", apron=(200, 190, 160),
        tool="rod", idle="count",
    ),
    "barnaby": Look(
        cloth=(110, 84, 56), hair=(60, 44, 32), skin=(180, 140, 104), build="stout", hair_style="bald",
        beard="short", apron=(96, 70, 44), sleeves="rolled", tool="hammer",
    ),
    "ottilie": Look(
        cloth=(90, 110, 120), hair=(150, 140, 130), build="average", hair_style="bun", hat="coif",
        hat_rgb=(220, 214, 200), apron=(220, 214, 200), tool="ladle", idle="stir",
    ),
    "hamund": Look(
        cloth=(50, 70, 96), hair=(190, 186, 176), skin=(170, 126, 94), build="stout", hat="cap",
        hat_rgb=(40, 50, 70), beard="long", beard_tip=(214, 210, 200), tool="tankard",
        trousers=(64, 60, 56),
    ),
    "sefa": Look(
        cloth=(200, 190, 170), hair=(110, 60, 30), skin=(160, 112, 80), build="stout", hair_style="short",
        apron=(230, 224, 210), sleeves="rolled", hat="coif", hat_rgb=(236, 230, 218), tool="ladle",
        idle="stir",
    ),
    "jorun": Look(
        cloth=(120, 62, 44), hair=(84, 56, 36), skin=(190, 150, 116), build="stout", hair_style="bun",
        hat="coif", hat_rgb=(206, 198, 180), apron=(176, 164, 136), sleeves="rolled", tool="bucket",
        trousers=(70, 50, 40), boots=(52, 40, 32),
    ),
    "cobb": Look(
        cloth=(70, 66, 60), hair=(150, 100, 60), build="tall", hat="brim", hat_rgb=(44, 40, 36),
        tool="lantern", idle="watch", trousers=(56, 52, 48),
    ),
    # Brother Marrow, the lay brother left in a cell of the Abandoned Prison: a grey, stained robe
    # gone to rags, bare feet, a shaven head and a long beard grown wild in the dark.
    "marrow": Look(
        cloth=(86, 80, 70), hair=(150, 146, 138), skin=(170, 150, 128), build="stooped", garb="robe",
        hair_style="bald", beard="long", beard_tip=(196, 192, 184), trousers=(70, 64, 56),
        boots=(150, 132, 112), belt=(60, 52, 40), idle="pray",
    ),
}  # fmt: skip


def look(npc_id):
    """The look of a villager by id; strangers wear plain grey."""
    return LOOKS.get(npc_id, Look())
