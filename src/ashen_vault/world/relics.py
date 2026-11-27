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
        Relic(item="argent_sigil", key="argent_sigil", taken_flag="argent_sigil_taken"),
        # Herran's, the fifth seal the king never held: it lies with him atop his keep on the Hollow Peak.
        Relic(item="auric_sigil", key="auric_sigil", taken_flag="auric_sigil_taken"),
    ]
}

# The sigils of the prophecy: once Odrin has seen all five in your hands he unseals the Silent Bell,
# and ringing it with them ends the game (`dialogue.bell`).
ENDING_RELICS = ("ember_sigil", "verdant_sigil", "iron_sigil", "argent_sigil", "auric_sigil")
# The three sigils found this side of the Vesper Gate. The fourth, the Argent Sigil, lies in
# Vesperholm, beyond the gate at the head of Harrowmere's cathedral steps. The gate always stands open
# now; GATE_FLAG only records that the first three have been taken up (saves still carry it).
FIRST_THREE = ("ember_sigil", "verdant_sigil", "iron_sigil")
GATE_FLAG = "vesper_gate_open"


def get(item_id):
    return RELICS.get(item_id) or Relic(item=item_id, key=item_id, taken_flag=f"{item_id}_taken")


def mark_taken(item_id, flags):
    """Called when the player picks up an item; remembers relics so they are never dropped again, and
    sets GATE_FLAG once the third of the first three is taken."""
    if item_id in RELICS:
        flags.add(RELICS[item_id].taken_flag)
        open_gate(flags)


def open_gate(flags):
    """Sets GATE_FLAG once the first three sigils have all been taken up (an older save catches up when
    a map loads), and returns whether it is set. Harmless: nothing waits on the flag any more, since the
    Vesper Gate stands open from the start."""
    if all(RELICS[i].taken_flag in flags for i in FIRST_THREE):
        flags.add(GATE_FLAG)
    return GATE_FLAG in flags


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
