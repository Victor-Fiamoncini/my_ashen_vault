"""What the ground underfoot sounds like: each floor texture belongs to a surface, and each surface
has its own step sound (`step_<surface>` in `audio/synth.py`)."""

SURFACES = ("stone", "wood", "soft", "mud", "water", "metal", "gravel", "glass")
DEFAULT = "stone"
VOLUME = 0.35  # a footstep's volume

_BY_TEX = {
    # Stone is the default; Harrowmere's cathedral floor, Vesperholm's moonstone paving and silvered slate and Old Harrowmere's
    # ochre paving are named all the same.
    "stone": (
        "cathedral_floor",
        "moonstone",
        "moon_paving",
        "silver_slate",
        "ochre_flag",
        "sunken_brick",
        "cavern_rock",
        "crystal_rock",
        "herran_ashlar",
        "herran_brick",
        "herran_slate",
        "encaustic_tile",
        "lab_tile",
    ),
    "wood": ("wood_plank", "timber", "bark", "rotten_wood"),
    "soft": (
        "dirt",
        "ash_ground",
        "ash_grass",
        "grass",
        "ash_road",
        "jungle_floor",
        "leaf_litter",
        "canopy",
        "thorns",
        "cloud_sea",
        "dirt_path",
    ),
    "mud": ("mud", "bog", "sludge", "fen_mud"),
    "water": ("water", "rapids", "sallow_mire"),
    "metal": ("iron_plate", "iron_grate", "iron_grating"),
    "gravel": ("slag", "ravine"),
    "glass": ("moon_glass",),
}
TEX_SURFACE = {tex: surface for surface, texes in _BY_TEX.items() for tex in texes}

# Platforms underfoot: rafts, planks, rotten boards, drawbridges and lift decks are timber; a
# crumbling ledge is stone; the prison's jail cage is iron, Old Harrowmere's rune lift stone.
PLATFORM_SURFACE = {"ledge": "stone"}
LIFT_SURFACE = {"cage": "metal", "rune": "stone"}


def surface(tile, platform=None):
    """The surface you tread on: the platform carrying you, else the floor of your tile."""
    if platform is not None:
        if platform.kind == "lift" and getattr(platform, "model", "") in LIFT_SURFACE:
            return LIFT_SURFACE[platform.model]
        return PLATFORM_SURFACE.get(platform.kind, "wood")
    return TEX_SURFACE.get(getattr(tile, "floor_tex", None), DEFAULT)


def sound(tile, platform=None):
    """The sound name of a step there."""
    return f"step_{surface(tile, platform)}"
