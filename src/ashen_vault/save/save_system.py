import json
import math
import os

from ashen_vault import map_path
from ashen_vault.player.ailments import Ailments
from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.player.stats import Stats
from ashen_vault.save.slots import SLOTS, SlotSummary, slot_path
from ashen_vault.world.map_loader import MapLoader

VERSION = 4
# Maps whose id changed: older saves name them by the old id, in the map, the remnant and the flags.
RENAMED_MAPS = {"sunken_keep": "abandoned_prison"}
# Maps whose grid grew on its north or west side, by (tiles across, tiles down), and the save version
# the growth came in: an older save's spot, remnant and tile flags there are moved to match. Vesperholm
# gained the crag behind its cathedral, and Lyra's Chapel on it, twenty rows to the north.
SHIFTED_MAPS = {"vesperholm": (0, 20, 3)}
TILE = 2.0  # metres a tile (`TileMap.TILE`)
# Maps torn down and built anew (or gone into another), by the map an older save made there wakes on
# instead, and the save version the rebuild came in: the spot and the remnant go to that map's `start`,
# and every flag naming the old map is dropped, since none of its tiles mean what they did. Herran's
# Castle above the clouds, and the spire on it, became his castle on the Hollow Peak.
REBUILT_MAPS = {"herrans_castle": ("herrans_castle", 4), "herran_spire": ("herrans_castle", 4)}
# Items taken out of the game with nothing to replace them (`Items.RENAMED` has those with): an older
# save loses them, from its pack, its hands and body, its quick slots and its shrine store.
RETIRED_ITEMS = frozenset({"graft_draught", "sun_tincture", "herran_bonesaw", "spire_key"})


def _renamed_flag(flag):
    """A flag with any renamed map id in it (`door:<map>:x,z`, `left:<map>`) turned to the new id."""
    parts = flag.split(":")
    return ":".join(RENAMED_MAPS.get(part, part) if i else part for i, part in enumerate(parts))


def _shifted_flag(flag, version):
    """A flag ending in a tile (`chest:<map>:x,z`, `loot:slain:<map>:x,z`) on a map whose grid has grown
    since `version`, moved with the map."""
    parts = flag.split(":")
    for map_name, (dx, dz, since) in SHIFTED_MAPS.items():
        if version < since and map_name in parts[1:-1]:
            try:
                tx, tz = (int(v) for v in parts[-1].split(","))
            except ValueError:
                return flag
            return ":".join([*parts[:-1], f"{tx + dx},{tz + dz}"])
    return flag


def _shift_spot(spot, map_name, version):
    """Moves a saved `{x, z}` (the player, a remnant) with its map's grid, if it has grown since."""
    dx, dz, since = SHIFTED_MAPS.get(map_name, (0, 0, 0))
    if spot is not None and version < since:
        spot["x"] = spot["x"] + dx * TILE
        spot["z"] = spot["z"] + dz * TILE


def _start_spot(map_name):
    """A map's `start` as a saved spot: {x, z, yaw} (yaw in radians, as a player saves it)."""
    tx, tz, yaw = MapLoader.load_file(map_path(map_name)).meta["start"][:3]
    return {"x": (int(tx) + 0.5) * TILE, "z": (int(tz) + 0.5) * TILE, "yaw": yaw * math.pi / 180}


def _rebuilt(map_name, version):
    """The map a save made on `map_name` before `version` wakes on, if that map has been rebuilt since."""
    into, since = REBUILT_MAPS.get(map_name, (None, 0))
    return into if version < since else None


def _retire_items(player):
    """Takes the retired items out of a saved player dict, wherever they are kept."""
    inv = player.get("inventory") or {}
    for key in ("counts", "wear"):
        for id_ in RETIRED_ITEMS & set(inv.get(key) or {}):
            del inv[key][id_]
    for key, value in list(inv.items()):
        if isinstance(value, str) and value in RETIRED_ITEMS:
            inv[key] = None
    for id_ in RETIRED_ITEMS & set(player.get("stash") or {}):
        del player["stash"][id_]
    if player.get("quick_slots"):
        player["quick_slots"] = [None if i in RETIRED_ITEMS else i for i in player["quick_slots"]]
    if player.get("quick") in RETIRED_ITEMS:
        player["quick"] = None


def migrate(data):
    """Brings an older save's data up to date in place, and returns it: maps that were renamed are
    named by their new id (the saved spot, the remnant and every flag); on a map whose grid has grown
    since, the spot, the remnant and every flag naming a tile move with it; a save on a map rebuilt
    since wakes at the new map's start, its remnant there too, and the old map's flags are dropped;
    and retired items are taken away."""
    version = int(data.get("version", 1))
    player = data.get("player", {})
    remnant = player.get("remnant")
    gone = {name for name in REBUILT_MAPS if _rebuilt(name, version)}
    into = _rebuilt(data.get("map"), version)
    if into:
        data["map"] = into
        player.update(_start_spot(into))
    if remnant and _rebuilt(remnant.get("map"), version):
        remnant["map"] = _rebuilt(remnant["map"], version)
        remnant.update({k: v for k, v in _start_spot(remnant["map"]).items() if k != "yaw"})
    if gone:
        data["flags"] = [f for f in data.get("flags", []) if not gone & set(f.split(":")[1:])]
    _retire_items(player)
    data["map"] = RENAMED_MAPS.get(data["map"], data["map"])
    if remnant and remnant.get("map") in RENAMED_MAPS:
        remnant["map"] = RENAMED_MAPS[remnant["map"]]
    if "x" in player and "z" in player:
        _shift_spot(player, data["map"], version)
    if remnant:
        _shift_spot(remnant, remnant.get("map"), version)
    data["flags"] = [_shifted_flag(_renamed_flag(f), version) for f in data.get("flags", [])]
    data["version"] = VERSION
    return data


class SaveSystem:
    """Persists the run to one JSON file: save slot `slot` (1..SLOTS) beside the base save path.
    Slot 1 is the base path itself (`save.json`), so older single-slot saves load as slot 1."""

    DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "ashen_vault", "save.json")

    def __init__(self, path=None, slot=1):
        self.base = path or os.environ.get("ASHEN_VAULT_SAVE", self.DEFAULT_PATH)
        self.slot = slot
        self.path = slot_path(self.base, slot)

    def in_slot(self, slot):
        """The same save base, another slot."""
        return SaveSystem(self.base, slot)

    def all_slots(self):
        return [self.in_slot(n) for n in range(1, SLOTS + 1)]

    def exists(self):
        return os.path.exists(self.path)

    def save(self, map, player, flags):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        data = {"version": VERSION, "map": map, "player": player.to_h(), "flags": sorted(flags)}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def summary(self):
        """What the slot chooser shows of this slot (`slots.SlotSummary`), or None if it is empty or
        can't be read."""
        if not self.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = migrate(json.load(f))
            p = data["player"]
            return SlotSummary(
                slot=self.slot,
                map=data["map"],
                level=int(p["stats"]["level"]),
                play_time=float(p.get("play_time", 0.0)),
                saved_at=os.path.getmtime(self.path),
            )
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def load_spot(self):
        """Where the last save was made: (map_name, x, z, yaw), or None."""
        loaded = self.load()
        if not loaded:
            return None
        map_name, player, _flags = loaded
        return map_name, player.x, player.z, player.yaw

    def load(self):
        """Returns (map_name, player, flags) or None."""
        if not self.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = migrate(json.load(f))
            p = data["player"]
            inv = p["inventory"]
            inventory = Inventory.from_h({**inv, "counts": {str(k): v for k, v in inv["counts"].items()}})
            player = Player(stats=Stats.from_h(p["stats"]), inventory=inventory, spells=p["spells"])
            player.x = p["x"]
            player.z = p["z"]
            player.yaw = p["yaw"]
            player.restore_quick(p)  # older saves kept one `quick` item
            player.remnant = p.get("remnant")
            player.play_time = float(p.get("play_time", 0.0))
            renamed = Items.RENAMED.get
            for id_, n in (p.get("stash") or {}).items():  # the shrine store (saves before it have none)
                key = renamed(id_, id_)
                if key in Items.ALL:
                    player.stash[key] = player.stash.get(key, 0) + int(n)
            player.stashed_spells = list(p.get("stashed_spells") or [])
            player.ailments = Ailments.from_h(p.get("ailments"))  # saves before ailments have none
            player.sync_rot()
            if p.get("spell"):
                player.equip_spell(p["spell"])
            return data["map"], player, set(data["flags"])
        except (ValueError, KeyError, TypeError, AttributeError):
            return None
