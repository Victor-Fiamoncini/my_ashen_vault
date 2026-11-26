"""Named regions within one map: the Cinderhold's Sallow Fen below the fortress, say. A map lays
`region name="Sallow Fen"` markers in pairs of bands across each border, one band on either side, each
naming the side it stands on (unquoted, underscores stand for spaces). Stepping onto a marker of another
region raises that region's name over the screen, as crossing between maps does; on arrival, the
nearest marker names the region you are in. A map without markers is one region, its `[meta] name`.
Pure, no raylib."""

import math

from ashen_vault.world.tile_map import TileMap


def build(map_):
    """Every region marker on `map_`: {(tx, tz): name}."""
    return {
        (s.tx, s.tz): (s.props.get("name") or "").replace("_", " ").strip()
        for s in map_.entities
        if s.kind == "region"
    }


def nearest(regions, x, z):
    """The name of the marker nearest the world point (x, z), or None on a map without markers."""
    if not regions:
        return None
    key = min(regions, key=lambda t: math.hypot(TileMap.center(*t)[0] - x, TileMap.center(*t)[1] - z))
    return regions[key]
