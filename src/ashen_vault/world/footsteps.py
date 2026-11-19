"""What the ground underfoot sounds like: each floor texture belongs to a surface, and each surface
has its own step sound (`step_<surface>` in `audio/synth.py`)."""

SURFACES = ("stone", "wood", "soft", "mud", "water", "metal", "gravel", "glass")
DEFAULT = "stone"
VOLUME = 0.35  # a footstep's volume

_BY_TEX = {
    # Stone is the default; Vesperholm's moonstone paving and silvered slate are named all the same.
    "stone": ("moonstone", "moon_paving", "silver_slate"),
    "wood": ("wood_plank", "timber", "bark"),
    "soft": (
        "dirt",
        "ash_ground",
        "ash_grass",
        "ash_road",
        "jungle_floor",
        "leaf_litter",
        "canopy",
        "thorns",
    ),
    "mud": ("mud", "bog", "sludge"),
    "water": ("water", "rapids"),
    "metal": ("iron_plate", "iron_grate"),
    "gravel": ("slag", "ravine"),
    "glass": ("moon_glass",),
}
TEX_SURFACE = {tex: surface for surface, texes in _BY_TEX.items() for tex in texes}

# Platforms underfoot: rafts, planks, rotten boards, drawbridges and lift decks are timber; a
# crumbling ledge is stone; the prison's jail cage is iron.
PLATFORM_SURFACE = {"ledge": "stone"}


def surface(tile, platform=None):
    """The surface you tread on: the platform carrying you, else the floor of your tile."""
    if platform is not None:
        if platform.kind == "lift" and getattr(platform, "model", "") == "cage":
            return "metal"
        return PLATFORM_SURFACE.get(platform.kind, "wood")
    return TEX_SURFACE.get(getattr(tile, "floor_tex", None), DEFAULT)


def sound(tile, platform=None):
    """The sound name of a step there."""
    return f"step_{surface(tile, platform)}"
