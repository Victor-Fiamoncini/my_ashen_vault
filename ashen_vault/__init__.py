"""Ashen Vault: a first-person dungeon crawler."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_DIR = os.path.join(ROOT, "data", "maps")


def map_path(name):
    return os.path.join(MAP_DIR, f"{name}.map")
