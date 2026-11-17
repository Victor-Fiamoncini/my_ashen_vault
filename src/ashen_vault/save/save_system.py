import json
import os

from ashen_vault.player.inventory import Inventory
from ashen_vault.player.items import Items
from ashen_vault.player.player import Player
from ashen_vault.player.stats import Stats
from ashen_vault.save.slots import SLOTS, SlotSummary, slot_path


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
        data = {"version": 1, "map": map, "player": player.to_h(), "flags": sorted(flags)}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def summary(self):
        """What the slot chooser shows of this slot (`slots.SlotSummary`), or None if it is empty or
        can't be read."""
        if not self.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
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
                data = json.load(f)
            p = data["player"]
            inv = p["inventory"]
            inventory = Inventory.from_h({**inv, "counts": {str(k): v for k, v in inv["counts"].items()}})
            player = Player(stats=Stats.from_h(p["stats"]), inventory=inventory, spells=p["spells"])
            player.x = p["x"]
            player.z = p["z"]
            player.yaw = p["yaw"]
            player.quick = p.get("quick", player.quick)
            player.remnant = p.get("remnant")
            player.play_time = float(p.get("play_time", 0.0))
            renamed = Items.RENAMED.get
            for id_, n in (p.get("stash") or {}).items():  # the shrine store (saves before it have none)
                key = renamed(id_, id_)
                if key in Items.ALL:
                    player.stash[key] = player.stash.get(key, 0) + int(n)
            player.stashed_spells = list(p.get("stashed_spells") or [])
            if p.get("spell"):
                player.equip_spell(p["spell"])
            return data["map"], player, set(data["flags"])
        except (ValueError, KeyError, TypeError, AttributeError):
            return None
