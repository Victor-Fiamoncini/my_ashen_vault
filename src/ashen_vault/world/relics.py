"""Boss relics: the sigils that bosses drop and the bell-keeper needs. Pure logic, no raylib."""

from dataclasses import dataclass

from ashen_vault.ai.enemy_types import EnemyTypes


@dataclass(frozen=True)
class Relic:
    item: str
    key: str  # prop key of the dropped pickup
    taken_flag: str  # global flag set once the player has picked it up


RELICS = {
    r.item: r
    for r in [
        # The Ember Sigil keeps its original key and flag so older saves still work.
        Relic(item="ember_sigil", key="sigil", taken_flag="sigil_taken"),
        Relic(item="verdant_sigil", key="verdant_sigil", taken_flag="verdant_sigil_taken"),
        Relic(item="iron_sigil", key="iron_sigil", taken_flag="iron_sigil_taken"),
    ]
}

# Odrin ends the game once the player brings him all of these.
ENDING_RELICS = ("ember_sigil", "verdant_sigil", "iron_sigil")


def get(item_id):
    return RELICS.get(item_id) or Relic(item=item_id, key=item_id, taken_flag=f"{item_id}_taken")


def mark_taken(item_id, flags):
    """Called when the player picks up an item; remembers relics so they are never dropped again."""
    if item_id in RELICS:
        flags.add(RELICS[item_id].taken_flag)


def pending_drops(map_, flags, has_item):
    """Relics that must lie on `map_` when it loads: the boss placed there is dead but its relic was
    neither picked up nor is it carried. Returns (item_id, tx, tz) at the boss's spawn tile.
    Twin bosses share one relic: it lies at the first of them."""
    out = []
    for spec in map_.entities:
        if not EnemyTypes.has(spec.kind):
            continue
        t = EnemyTypes.get(spec.kind)
        if not (t.boss and t.drop and t.dead_flag and t.dead_flag in flags):
            continue
        if has_item(t.drop) or get(t.drop).taken_flag in flags:
            continue
        if any(item == t.drop for item, _, _ in out):
            continue
        out.append((t.drop, spec.tx, spec.tz))
    return out


def boss_falls(type_, enemies):
    """Whether a boss of `type_` that has just died ends its fight: always, unless it is one of a pair
    of twins and the other still lives. Only then is its `dead_flag` set and its relic dropped."""
    if not type_.twin:
        return True
    return not any(e.alive and e.type.dead_flag == type_.dead_flag for e in enemies)


def held(has_item):
    """The ending relics the player carries, in ENDING_RELICS order."""
    return [i for i in ENDING_RELICS if has_item(i)]
