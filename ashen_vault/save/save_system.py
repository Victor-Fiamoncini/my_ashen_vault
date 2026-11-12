import json
import os

from ashen_vault.player.inventory import Inventory
from ashen_vault.player.player import Player
from ashen_vault.player.stats import Stats


class SaveSystem:
    """Persists the run to a single JSON slot."""
    DEFAULT_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "ashen_vault", "save.json")

    def __init__(self, path=None):
        self.path = path or os.environ.get("ASHEN_VAULT_SAVE", self.DEFAULT_PATH)

    def exists(self):
        return os.path.exists(self.path)

    def save(self, map, player, flags):  # noqa: A002 - mirrors the save file's key
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        data = {"version": 1, "map": map, "player": player.to_h(), "flags": sorted(flags)}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Returns (map_name, player, flags) or None."""
        if not self.exists():
            return None
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            p = data["player"]
            inv = p["inventory"]
            inventory = Inventory.from_h({"counts": {str(k): v for k, v in inv["counts"].items()},
                                          "weapon": inv.get("weapon"), "armor": inv.get("armor"),
                                          "gold": inv.get("gold")})
            player = Player(stats=Stats.from_h(p["stats"]), inventory=inventory, spells=p["spells"])
            player.x = p["x"]
            player.z = p["z"]
            player.yaw = p["yaw"]
            return data["map"], player, set(data["flags"])
        except (ValueError, KeyError, TypeError, AttributeError):
            return None
