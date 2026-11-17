"""Save slots: three journeys kept side by side. Slot 1 is the base save path itself (`save.json`,
so a save from before slots loads as slot 1); slot n is `save_<n>.json` beside it. Each records how
long it has been played."""

import os
from dataclasses import dataclass

SLOTS = 3


@dataclass(frozen=True)
class SlotSummary:
    """What the slot chooser shows of a used slot."""

    slot: int
    map: str
    level: int
    play_time: float  # seconds
    saved_at: float  # the file's modification time, for Continue


def slot_path(base, n):
    """The save file of slot `n` (1-based) beside the base save path."""
    if not 1 <= n <= SLOTS:
        raise ValueError(f"no save slot {n}")
    if n == 1:
        return base
    root, ext = os.path.splitext(base)
    return f"{root}_{n}{ext or '.json'}"


def format_play_time(seconds):
    """Play time as H:MM:SS."""
    total = max(int(seconds), 0)
    return f"{total // 3600}:{total // 60 % 60:02d}:{total % 60:02d}"


def latest(summaries):
    """The slot saved most recently among `summaries` (None entries are empty slots), or None."""
    used = [s for s in summaries if s is not None]
    return max(used, key=lambda s: s.saved_at).slot if used else None
