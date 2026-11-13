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
    ]
}

# Odrin ends the game once the player brings him all of these.
ENDING_RELICS = ("ember_sigil", "verdant_sigil")


def get(item_id):
    return RELICS.get(item_id) or Relic(item=item_id, key=item_id, taken_flag=f"{item_id}_taken")


def mark_taken(item_id, flags):
    """Called when the player picks up an item; remembers relics so they are never dropped again."""
    if item_id in RELICS:
        flags.add(RELICS[item_id].taken_flag)


def pending_drops(map_, flags, has_item):
    """Relics that must lie on `map_` when it loads: the boss placed there is dead but its relic was
    neither picked up nor is it carried. Returns (item_id, tx, tz) at the boss's spawn tile."""
    out = []
    for spec in map_.entities:
        if not EnemyTypes.has(spec.kind):
            continue
        t = EnemyTypes.get(spec.kind)
        if not (t.boss and t.drop and t.dead_flag and t.dead_flag in flags):
            continue
        if has_item(t.drop) or get(t.drop).taken_flag in flags:
            continue
        out.append((t.drop, spec.tx, spec.tz))
    return out


def held(has_item):
    """The ending relics the player carries, in ENDING_RELICS order."""
    return [i for i in ENDING_RELICS if has_item(i)]
