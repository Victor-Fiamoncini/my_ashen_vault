"""The gold you drop when you die (`Player.remnant`): a smouldering heap of your ashes left where you
last stood on solid ground. Gather it up on your next life and the gold is yours again; die before
you do and the heap scatters, and that gold is gone for good.
Pure logic: the World draws the heap and the Game moves the gold."""

REACH = 1.0  # metres from the heap within which walking over it gathers it up
REACH_Y = 1.5  # metres above or below it you still reach it from


def leave(player, map_name, x, z):
    """You die at (x, z) on `map_name`: an older heap you never gathered scatters, and all the gold
    you carry is left in a new one there. Returns (gold lost, gold left behind)."""
    lost = player.remnant["gold"] if player.remnant else 0
    left = player.inventory.gold
    player.remnant = {"map": map_name, "x": x, "z": z, "gold": left} if left > 0 else None
    player.inventory.gold = 0
    return lost, left


def gather(player):
    """Takes your heap back: its gold returns to the purse. Returns how much (0 with no heap)."""
    if not player.remnant:
        return 0
    gold = player.remnant["gold"]
    player.inventory.gold += gold
    player.remnant = None
    return gold


def lies_on(player, map_name):
    """Your heap's (x, z) when it lies on `map_name`, else None."""
    r = player.remnant
    if not r or r["map"] != map_name:
        return None
    return r["x"], r["z"]


def within_reach(px, py, pz, x, y, z):
    return (px - x) ** 2 + (pz - z) ** 2 <= REACH * REACH and abs(py - y) <= REACH_Y
