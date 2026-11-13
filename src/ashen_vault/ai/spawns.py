"""Builds the enemies a map places, without touching the GPU."""

import math

from ashen_vault.ai.enemy import Enemy
from ashen_vault.ai.enemy_types import EnemyTypes
from ashen_vault.world.tile_map import TileMap


def spawn_enemies(map_, flags, bosses=True):
    """Fresh enemies for every enemy entity in `map_`. A defeated boss (its `dead_flag` is set) stays dead;
    `bosses=False` leaves bosses out entirely (shrine respawns keep the living boss as it is)."""
    enemies = []
    for spec in map_.entities:
        if not EnemyTypes.has(spec.kind):
            continue
        type_ = EnemyTypes.get(spec.kind)
        if type_.boss and (not bosses or boss_defeated(type_, flags)):
            continue
        key = f"slain:{map_.name}:{spec.tx},{spec.tz}" if type_.once else None
        if key in flags:
            continue
        x, z = TileMap.center(spec.tx, spec.tz)
        if "yaw" in spec.props:
            yaw = float(spec.props["yaw"]) * math.pi / 180
        elif type_.ambush:
            yaw = map_.open_facing(spec.tx, spec.tz)
        else:
            yaw = 0.0
        enemies.append(Enemy(type_, x, z, yaw=yaw, marker=spec.marker, loot=spec.props.get("item"), key=key))
    return enemies


def boss_defeated(type_, flags):
    return bool(type_.dead_flag) and type_.dead_flag in flags
