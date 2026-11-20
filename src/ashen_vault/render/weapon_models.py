"""The weapons' models: swords, katanas, whips, maces, axes, hammers and shields, and `weapon`, which
draws any of them by item id, the area modules' own weapons included."""

import math

from ashen_vault.render import forge_models, moon_models, sunken_models
from ashen_vault.render.parts import (
    BRASS,
    DARK_IRON,
    EMBER,
    IRON,
    LEATHER,
    _dim,
    blade_parts,
)
from ashen_vault.util import rround

# Weapons whose striking head is built with its edge (or face) on +Z, as models of its kind are, and
# turned a quarter about the haft by `weapon` so it leads along +X: the way every swing travels.
HEADED = {
    "hatchet", "bearded_axe", "butcher_cleaver", "war_hammer", "great_iron_hammer", "slagbreaker",
    "torch_greathammer",
}  # fmt: skip

WOOD = (90, 60, 38)

STEEL = (190, 190, 200)
OAK = (118, 84, 52)

# Rough length of each weapon model (grip to tip), used to fit previews.
WEAPON_LEN = {
    "rusted_sword": 1.3,
    "ashblade": 1.4,
    "bastard_sword": 1.68,
    "claymore": 2.2,
    "zweihander": 2.5,
    "katana": 1.7,
    "moonless_tachi": 1.95,
    "nodachi": 2.45,
    "war_hammer": 1.5,
    "great_iron_hammer": 1.55,
    "flamberge": 2.15,
    "bearded_axe": 1.15,
    "hatchet": 0.9,
    "butcher_cleaver": 1.0,
    "oak_cudgel": 1.0,
    "spiked_club": 1.05,
    "stormbrand": 1.45,
    "slagbreaker": 1.5,
    "torch_greathammer": 1.55,
    "ember_stone_sword": 1.45,
    "vesper_moonbrand": 2.45,
}


def weapon(r, item_id, phase=None):
    """A weapon model with the grip at the origin, pointing up +Y; an edge or striking face leads
    along +X (see HEADED and `edge_turn`)."""
    turn = edge_turn(item_id)
    if turn:
        with r.at(0, 0, 0, ry=turn):
            return _weapon(r, item_id, phase)
    return _weapon(r, item_id, phase)


def edge_turn(item_id):
    """The quarter turn about the grip that brings a weapon's edge onto +X, the way swings travel and the
    hand's knuckles face: axe bits, hammer faces and straight blades are built on +-Z, a katana's edge
    on -Z."""
    if (
        item_id in HEADED
        or item_id in SWORDS
        or item_id in ("stormbrand", "ember_stone_sword", "vesper_moonbrand")
    ):
        return math.pi / 2
    if item_id in KATANAS:
        return -math.pi / 2
    return 0.0


def _weapon(r, item_id, phase=None):
    if item_id in ("katana", "moonless_tachi", "nodachi"):
        katana(r, item_id)
    elif item_id in ("leather_whip", "thornlash"):
        whip(r, phase, thorns=item_id == "thornlash")
    elif item_id == "mace":
        mace(r)
    elif item_id in ("oak_cudgel", "spiked_club"):
        club(r, item_id == "spiked_club")
    elif item_id == "war_hammer":
        hammer(r)
    elif item_id == "great_iron_hammer":
        great_iron_hammer(r)
    elif item_id in ("hatchet", "bearded_axe"):
        hand_axe(r, item_id == "bearded_axe")
    elif item_id == "butcher_cleaver":
        cleaver(r)
    elif item_id == "stormbrand":
        forge_models.stormbrand(r)
    elif item_id == "slagbreaker":
        forge_models.slagbreaker(r)
    elif item_id == "torch_greathammer":
        sunken_models.torch_greathammer(r)
    elif item_id == "ember_stone_sword":
        sunken_models.ember_stone_sword(r)
    elif item_id == "vesper_moonbrand":
        moon_models.moonbrand(r)
    else:
        sword(r, item_id)


# The player's straight swords: blade_parts arguments per item.
SWORDS = {
    "rusted_sword": {
        "length": 1.1,
        "width": 0.13,
        "steel": (142, 136, 126),
        "edge": (180, 176, 166),
        "fuller": (92, 84, 74),
        "guard_rgb": (96, 80, 62),
        "guard_w": 0.3,
        "grip_rgb": (74, 56, 40),
        "wrap": (112, 94, 68),
        "pommel_rgb": (96, 80, 62),
    },
    "ashblade": {
        "length": 1.2,
        "width": 0.125,
        "steel": (190, 190, 202),
        "edge": (238, 238, 245),
        "fuller": (66, 62, 66),
        "guard": "flared",
        "guard_rgb": (70, 66, 72),
        "grip_rgb": (40, 36, 40),
        "wrap": (120, 110, 100),
        "pommel": "stopper",
        "pommel_rgb": (70, 66, 72),
    },
    "bastard_sword": {
        "length": 1.4,
        "width": 0.12,
        "steel": (176, 178, 190),
        "guard": "droop",
        "guard_w": 0.4,
        "guard_rgb": (112, 108, 102),
        "grip": 0.32,
        "wrap": (40, 30, 22),
        "pommel": "wheel",
        "pommel_rgb": (112, 108, 102),
    },
    "claymore": {
        "length": 1.72,
        "width": 0.15,
        "thick": 0.04,
        "steel": (170, 172, 182),
        "guard": "quatrefoil",
        "guard_w": 0.52,
        "guard_rgb": (120, 110, 90),
        "grip": 0.4,
        "wrap": (40, 30, 22),
        "pommel": "wheel",
        "pommel_rgb": (120, 110, 90),
        "ricasso": 0.12,
    },
    "zweihander": {  # a Landsknecht's two-hander: broad, blued, ringed and horned
        "length": 2.0,
        "width": 0.19,
        "thick": 0.042,
        "base": 0.12,
        "steel": (188, 190, 200),
        "fuller": (128, 130, 142),
        "guard": "rings",
        "guard_w": 0.66,
        "guard_rgb": (82, 88, 108),
        "trim_rgb": (164, 168, 182),
        "grip": 0.46,
        "grip_rgb": (28, 24, 22),
        "ferrule": True,
        "pommel": "pear",
        "pommel_rgb": (82, 88, 108),
        "ricasso": 0.3,
        "ricasso_rgb": (126, 34, 30),
        "lugs": "horns",
    },
    "flamberge": {  # a flame-bladed sword: blackened and gilt, its ricasso bare and etched
        "length": 1.78,
        "width": 0.15,
        "thick": 0.036,
        "base": 0.12,
        "steel": (178, 180, 192),
        "edge": (236, 236, 244),
        "fuller": (214, 214, 224),
        "guard": "flame",
        "guard_w": 0.5,
        "guard_rgb": (52, 48, 54),
        "trim_rgb": (196, 158, 78),
        "grip": 0.42,
        "grip_rgb": (86, 26, 24),
        "wrap": (176, 140, 70),
        "pommel": "fig",
        "pommel_rgb": (52, 48, 54),
        "ricasso": 0.2,
        "ricasso_rgb": (120, 120, 132),
        "lugs": "flames",
        "waves": 5,
    },
}
SWORD_RUST = (118, 92, 72)


def sword(r, item_id):
    """A straight sword: rusted, the Ashblade, the bastard sword or a greatsword (see SWORDS)."""
    spec = SWORDS.get(item_id, SWORDS["rusted_sword"])
    blade_parts(r, **spec)
    w, base = spec["width"], spec.get("base", 0.13)
    if item_id == "rusted_sword":  # one faint stain of rust creeping up from the guard
        r.part("cube", 0, base + 0.1, 0, 0.034, 0.06, w * 0.35, SWORD_RUST)
    elif item_id == "ashblade":  # an ember that never quite went out, near the point
        r.part("cube", 0, base + spec["length"] * 0.8, 0, 0.036, 0.05, 0.02, EMBER, glow=True)
    elif item_id == "flamberge":  # a gilt flame etched on both faces of the bare ricasso
        y, gilt, x = base + spec["ricasso"] * 0.45, spec["trim_rgb"], spec["thick"] * 0.86
        for side in (1, -1):  # a tall tongue between two that lean out from its foot
            r.part("cube", side * x, y + 0.01, 0, 0.004, 0.11, 0.012, gilt)
            for tilt in (1, -1):
                r.part("cube", side * x, y - 0.012, tilt * 0.018, 0.004, 0.065, 0.01, gilt, rx=-tilt * 0.45)


# blade, edge (hamon), grip wrap, cord, segments, grip length
KATANAS = {
    "katana": ((205, 208, 218), (245, 245, 250), (40, 30, 40), (160, 30, 40), 4, 0.3),
    "moonless_tachi": ((70, 72, 90), (200, 205, 220), (20, 18, 24), (60, 60, 80), 5, 0.32),
    "nodachi": ((200, 202, 212), (245, 245, 250), (30, 26, 30), (200, 170, 70), 6, 0.5),
}


def katana(r, item_id="katana"):
    blade, edge, wrap, cord, segments, grip = KATANAS[item_id]
    r.part("cube", 0, 0.07 - grip / 2, 0, 0.055, grip, 0.06, wrap)
    for i in range(rround(grip / 0.075)):  # cord wrap, crossing diamonds down the hilt
        r.part("cube", 0, 0.05 - grip + 0.04 + i * 0.075, 0, 0.062, 0.02, 0.066, cord, rx=0.3 * (-1) ** i)
    r.part("cube", 0, 0.06 - grip, 0, 0.065, 0.03, 0.07, (170, 150, 70))  # kashira cap
    r.part("cyl", 0, 0.08, 0, 0.16, 0.025, 0.16, (60, 50, 30))  # tsuba
    r.part("cube", 0, 0.115, 0, 0.04, 0.045, 0.075, (170, 150, 70))  # habaki collar
    with r.at(0, 0.135, 0):
        _katana_segment(r, segments, blade, edge)


def _katana_segment(r, left, blade=(205, 208, 218), edge=(245, 245, 250)):
    """A gentle curve: each segment hangs off the last, bent a little further back; the edge (-Z) carries
    a pale temper line (the hamon) and the last segment closes in a angled point (the kissaki)."""
    if left == 0:
        r.part("blade", 0, 0.06, -0.004, 0.024, 0.13, 0.066, blade, rx=0.12)
        r.part("cube", 0.0, 0.03, -0.022, 0.012, 0.07, 0.014, edge, rx=0.2)
        return
    with r.at(0, 0, 0, rx=0.05):
        r.part("lozenge", 0, 0.17, 0, 0.026, 0.36, 0.07, blade)
        r.part("cube", 0, 0.17, -0.024, 0.012, 0.36, 0.014, edge)
        r.part("cube", 0, 0.17, 0.03, 0.03, 0.36, 0.01, _dim(blade, 0.6))  # the thick back (mune)
        with r.at(0, 0.34, 0):
            _katana_segment(r, left - 1, blade, edge)


def whip(r, phase=None, thorns=False):
    r.part("cube", 0, -0.04, 0, 0.06, 0.3, 0.06, LEATHER)
    r.part("cube", 0, 0.12, 0, 0.075, 0.04, 0.075, (90, 90, 96) if thorns else BRASS)
    # Hanging coils at rest; the lash straightens out at the crack.
    straight = math.sin(phase * math.pi) if phase is not None else 0.0
    bend = 0.42 * (1 - straight) + 0.04
    with r.at(0, 0.14, 0):
        _whip_segment(r, 8 if thorns else 7, bend, 0.06, thorns)


def _whip_segment(r, left, bend, thick, thorns=False):
    if left == 0:
        r.part("cube", 0, 0.04, 0, 0.02, 0.08, 0.05, (120, 90, 60))
        return
    with r.at(0, 0, 0, rx=bend):
        r.part("cube", 0, 0.1, 0, thick, 0.2, thick, (70, 60, 36) if thorns else (100, 70, 44))
        if thorns:
            for i, (dz, dx) in enumerate(((1, 0), (-1, 0), (0, 1))):
                r.part("cube", dx * thick * 0.7, 0.04 + i * 0.05, dz * thick * 0.7, 0.025, 0.04, 0.025, IRON)
        with r.at(0, 0.2, 0):
            _whip_segment(r, left - 1, bend, max(thick * 0.86, 0.025), thorns)


def mace(r):
    r.part("cube", 0, 0.1, 0, 0.06, 0.7, 0.06, WOOD)
    r.part("cube", 0, -0.2, 0, 0.075, 0.12, 0.075, LEATHER)
    r.part("sphere", 0, 0.55, 0, 0.17, 0.22, 0.17, (88, 88, 96))
    for i in range(4):
        with r.at(0, 0.55, 0, ry=i * math.pi / 4):
            r.part("cube", 0, 0, 0, 0.03, 0.2, 0.26, (120, 120, 130))
    r.part("cube", 0, 0.69, 0, 0.05, 0.07, 0.05, (120, 120, 130))


def club(r, spiked):
    """A knotted oak club that swells toward the end; the spiked one is a root-ball full of nails."""
    r.part("cube", 0, -0.15, 0, 0.08, 0.16, 0.08, LEATHER)
    for i, (w, h) in enumerate(((0.07, 0.25), (0.1, 0.25), (0.14, 0.22), (0.18 if spiked else 0.16, 0.2))):
        r.part("cyl", 0, 0.02 + i * 0.22, 0, w, h, w, OAK if i % 2 else (104, 74, 46))
    r.part("sphere", 0.05, 0.45, 0.03, 0.06, 0.08, 0.06, (90, 62, 40))  # knots
    r.part("sphere", -0.04, 0.25, -0.04, 0.05, 0.06, 0.05, (90, 62, 40))
    if spiked:
        r.part("sphere", 0, 0.78, 0, 0.26, 0.24, 0.26, (96, 70, 44))
        for i in range(7):
            a = i * 2.4
            with r.at(0, 0.66 + (i % 3) * 0.08, 0, ry=a):
                r.part("cube", 0, 0, 0.15, 0.02, 0.02, 0.12, (150, 150, 158))
        r.part("cube", 0, 0.92, 0, 0.02, 0.1, 0.02, (150, 150, 158))
    else:
        r.part("sphere", 0, 0.76, 0, 0.18, 0.16, 0.18, (104, 74, 46))


def hand_axe(r, bearded):
    """A one-handed axe. The bearded one has a long lower edge that hooks down past the haft."""
    haft = 0.85 if bearded else 0.6
    r.part("cube", 0, haft / 2 - 0.25, 0, 0.055, haft, 0.055, OAK)
    r.part("cube", 0, -0.2, 0, 0.07, 0.14, 0.07, LEATHER)
    top = haft - 0.3
    r.part("cube", 0, top, 0.06, 0.07, 0.14, 0.16, (110, 108, 106))  # eye and cheek
    if bearded:
        r.part("cube", 0, top - 0.06, 0.2, 0.04, 0.32, 0.12, (150, 150, 156))  # the beard
        r.part("wedge", 0, top - 0.08, 0.27, 0.045, 0.05, 0.36, (215, 215, 222), rx=math.pi / 2)  # edge
        r.part("cube", 0, top - 0.24, 0.16, 0.04, 0.06, 0.06, (150, 150, 156))  # its hooked tip
    else:
        r.part("cube", 0, top, 0.17, 0.04, 0.2, 0.08, (150, 150, 156))
        r.part("wedge", 0, top, 0.22, 0.045, 0.05, 0.22, (215, 215, 222), rx=math.pi / 2)
    r.part("cube", 0, top + 0.08, 0, 0.065, 0.03, 0.065, LEATHER)


def cleaver(r):
    """The Butcher's cleaver: a wrapped oak handle and a broad, square blade, its spine along the
    top and a hole for the hook it hung from."""
    r.part("cube", 0, 0.0, 0, 0.06, 0.42, 0.06, LEATHER)
    r.part("cube", 0, -0.23, 0, 0.075, 0.05, 0.075, DARK_IRON)  # butt cap
    r.part("cube", 0, 0.5, 0.13, 0.035, 0.6, 0.3, (140, 136, 130))  # the blade
    r.part("wedge", 0, 0.5, 0.29, 0.035, 0.04, 0.6, (205, 202, 196), rx=math.pi / 2)  # its edge
    r.part("cube", 0, 0.5, -0.015, 0.05, 0.62, 0.04, (90, 88, 86))  # the spine
    r.part("cube", 0.02, 0.72, 0.1, 0.01, 0.06, 0.06, (24, 20, 18))  # hanging hole
    r.part("cube", 0.02, 0.35, 0.2, 0.01, 0.12, 0.08, (90, 30, 26))  # a stain


def hammer(r):
    """A war hammer: an eight-sided iron head with a broad face and a curved back spike, steel
    langets riveted down the haft and a rondel to guard the hands."""
    r.part("cube", 0, 0.35, 0, 0.065, 1.25, 0.065, WOOD)
    r.part("cube", 0, -0.2, 0, 0.08, 0.22, 0.08, LEATHER)
    r.part("cube", 0, -0.33, 0, 0.1, 0.05, 0.1, (90, 90, 98))  # pommel cap
    r.part("cyl", 0, 0.07, 0, 0.17, 0.03, 0.17, (120, 120, 128))  # rondel
    for dz in (-0.036, 0.036):  # langets
        r.part("cube", 0, 0.78, dz, 0.04, 0.42, 0.012, STEEL)
        for k in range(3):
            r.part("cube", 0, 0.64 + k * 0.12, dz * 1.2, 0.02, 0.02, 0.012, (90, 90, 98))
    with r.at(0, 1.04, 0.05, rx=math.pi / 2):
        r.part("cyl", 0, 0, 0, 0.26, 0.42, 0.26, (110, 110, 118))  # head
        r.part("cyl", 0, 0.23, 0, 0.3, 0.06, 0.3, (140, 140, 150))  # striking face
        r.part("cyl", 0, 0.27, 0, 0.2, 0.03, 0.2, (175, 175, 185))
    r.part("cube", 0, 1.04, -0.22, 0.08, 0.08, 0.16, (100, 100, 108))  # spike root
    r.part("cube", 0, 1.0, -0.34, 0.05, 0.05, 0.14, STEEL, rx=-0.35)  # curved back spike
    r.part("cube", 0, 0.95, -0.42, 0.03, 0.03, 0.08, STEEL, rx=-0.7)
    r.part("cube", 0, 1.26, 0, 0.05, 0.12, 0.05, STEEL)  # top spike


HAMMER_IRON = (92, 92, 100)
HAMMER_BAND = (60, 58, 64)


def great_iron_hammer(r):
    """The Great Iron Hammer: a long haft bound in iron rings, steel langets riveted up its top, and a
    massive squared block of a head, ringed by two riveted bands, a studded striking face on +Z and a
    short, square back spike."""
    r.part("cube", 0, 0.38, 0, 0.07, 1.32, 0.07, (70, 52, 36))  # the haft
    for k in range(4):  # iron rings down the haft
        r.part("cube", 0, 0.05 + k * 0.17, 0, 0.082, 0.03, 0.082, HAMMER_BAND)
    r.part("cube", 0, -0.2, 0, 0.085, 0.26, 0.085, LEATHER)  # the grip
    r.part("cube", 0, -0.36, 0, 0.11, 0.06, 0.11, HAMMER_BAND)  # butt cap
    r.part("wedge", 0, -0.42, 0, 0.07, 0.06, 0.07, HAMMER_BAND, rz=math.pi)
    for dz in (-0.04, 0.04):  # langets
        r.part("cube", 0, 0.82, dz, 0.045, 0.36, 0.012, STEEL)
        for k in range(2):
            r.part("cube", 0, 0.72 + k * 0.16, dz * 1.25, 0.022, 0.022, 0.012, HAMMER_BAND)
    with r.at(0, 1.1, 0.04):  # the head, its face on +Z
        r.part("cube", 0, 0, 0, 0.26, 0.28, 0.46, HAMMER_IRON)
        for dz in (-0.13, 0.13):  # riveted bands round it
            r.part("cube", 0, 0, dz, 0.28, 0.3, 0.05, HAMMER_BAND)
            for dx, dy in ((-0.14, 0.0), (0.14, 0.0), (0.0, 0.15)):
                r.part("cube", dx, dy, dz, 0.025, 0.025, 0.025, (150, 150, 158))
        r.part("cube", 0, 0, 0.24, 0.3, 0.32, 0.03, _dim(HAMMER_IRON, 1.2))  # striking face
        for dx in (-0.08, 0.08):  # its studs
            for dy in (-0.08, 0.08):
                r.part("cube", dx, dy, 0.265, 0.05, 0.05, 0.03, (170, 170, 178))
        r.part("cube", 0, 0, -0.26, 0.16, 0.16, 0.06, HAMMER_BAND)  # spike root
        r.part("wedge", 0, 0, -0.36, 0.12, 0.16, 0.12, STEEL, rx=-math.pi / 2)  # the back spike
        r.part("cube", 0, 0.16, 0, 0.12, 0.04, 0.2, HAMMER_BAND)  # cap over the eye
        r.part("wedge", 0, 0.22, 0, 0.08, 0.1, 0.08, STEEL)  # top spike


def shield(r, item_id):
    """Shields face +X (away from you); the arm holds them from behind at the origin."""
    if item_id == "buckler":
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.42, 0.04, 0.42, (128, 128, 136))
            r.part("cyl", 0, -0.035, 0, 0.18, 0.06, 0.18, (170, 170, 180))  # boss
            r.part("cyl", 0, 0.03, 0, 0.12, 0.03, 0.12, LEATHER)  # grip
    elif item_id == "round_shield":
        with r.at(0, 0, 0, rz=math.pi / 2):
            r.part("cyl", 0, 0, 0, 0.82, 0.04, 0.82, (96, 120, 140))
            r.part("cyl", 0, 0.002, 0, 0.86, 0.035, 0.86, (90, 90, 96))  # iron rim
            r.part("cyl", 0, -0.04, 0, 0.2, 0.07, 0.2, (150, 150, 158))  # boss
            r.part("cyl", 0, 0.03, 0, 0.8, 0.02, 0.8, (104, 78, 50))  # the wooden back
        for k in (-0.2, 0.0, 0.2):  # planks seen from behind
            r.part("cube", -0.03, 0, k, 0.01, 0.74, 0.015, (80, 60, 40))
        r.part("cube", -0.04, 0, 0, 0.03, 0.16, 0.05, LEATHER)
    elif item_id == "kite_shield":
        face, trim = (160, 50, 44), (200, 180, 120)
        r.part("cube", 0, 0.18, 0, 0.04, 0.42, 0.56, face)
        for i in range(5):  # tapering to a point
            w = 0.5 - i * 0.1
            r.part("cube", 0, -0.08 - i * 0.09, 0, 0.04, 0.1, w, face)
        r.part("cube", 0.025, 0.4, 0, 0.01, 0.04, 0.58, trim)
        r.part("cube", 0.025, 0.0, 0, 0.01, 0.78, 0.04, trim)
        back = (98, 74, 48)
        r.part("cube", -0.025, 0.18, 0, 0.01, 0.42, 0.56, back)
        for i in range(5):
            r.part("cube", -0.025, -0.08 - i * 0.09, 0, 0.01, 0.1, 0.5 - i * 0.1, back)
        r.part("cube", -0.04, 0.05, 0, 0.03, 0.18, 0.05, LEATHER)
    else:  # tower shield
        r.part("cube", 0, 0.12, 0, 0.06, 1.25, 0.66, (96, 74, 50))
        for dy in (-0.35, 0.12, 0.6):
            r.part("cube", 0.035, dy, 0, 0.015, 0.06, 0.68, (100, 100, 108))  # iron bands
        for dz in (-0.16, 0.16):
            r.part("cube", -0.035, 0.12, dz, 0.01, 1.2, 0.012, (70, 52, 34))
        r.part("cube", -0.05, 0.05, 0, 0.03, 0.2, 0.06, LEATHER)
