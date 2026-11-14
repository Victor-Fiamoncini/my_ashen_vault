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
GARBS = ("tunic", "robe")
HAIR_STYLES = ("short", "long", "bald", "bun")
HATS = (None, "brim", "cap", "coif")
TOOLS = (None, "hammer", "spear", "ladle", "staff", "ledger", "rod", "whetstone", "tankard", "lantern")
IDLES = ("sway", "hammer", "watch", "stir", "pray", "count")


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
    beard: bool = False
    tool: str | None = None
    blade: bool = False  # a sheathed curved sword slung across the back
    idle: str = "sway"

    def __post_init__(self):
        assert self.build in BUILDS, self.build
        assert self.garb in GARBS, self.garb
        assert self.hair_style in HAIR_STYLES, self.hair_style
        assert self.hat in HATS, self.hat
        assert self.tool in TOOLS, self.tool
        assert self.idle in IDLES, self.idle


LOOKS = {
    "odrin": Look(
        cloth=(70, 60, 90), hair=(200, 200, 200), build="stooped", garb="robe", beard=True,
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
        cloth=(40, 40, 56), hair=(150, 150, 150), build="slight", hood=True, blade=True, garb="robe",
        tool="whetstone",
    ),
    "brannoc": Look(
        cloth=(96, 70, 52), hair=(40, 26, 18), skin=(176, 128, 92), build="stout", hair_style="bald",
        beard=True, apron=(70, 50, 34), tool="hammer", idle="hammer", trousers=(54, 46, 40),
    ),
    "garrick": Look(
        cloth=(100, 40, 36), hair=(110, 90, 60), build="tall", cloak=(76, 30, 28), hat="coif",
        hat_rgb=(130, 130, 136), tool="spear", idle="watch", beard=True,
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
