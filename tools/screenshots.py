"""Retakes the README screenshots.

    uv run python tools/screenshots.py                 # every shot, into docs/screenshots/
    uv run python tools/screenshots.py cemetery herran # just these
    uv run python tools/screenshots.py --out /tmp/x    # somewhere else, to look before replacing
    uv run python tools/screenshots.py --table         # print the README's gallery table

Each shot is a smoke run with its own throwaway save, so the player's real save is never touched.
The gear in each shot is gear the player could hold by then: the --level and --equip follow the
game's progression (cemetery, town, sewers, Old Harrowmere, prison, hollow, the Sallow Fen and the
Cinderhold, Vesperholm).
"""

import argparse
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "screenshots"


@dataclass(frozen=True)
class Shot:
    name: str
    args: str  # ashen-vault flags, without --shot
    caption: str
    alt: str
    note: str = ""  # why it may need a retake


SHOTS = [
    Shot(
        "village",
        "--map harrowmere --at=22,30,-60 --equip primary=hatchet,secondary=buckler --smoke 40",
        "The Silent Bell, at the heart of Harrowmere",
        "The Silent Bell in its frame on Harrowmere's paved Bell Square, a cathedral tower behind, "
        "a hatchet and a buckler in hand",
    ),
    Shot(
        "cemetery",
        "--map ashen_cemetery --equip primary=none,secondary=none,body=none,hands=none --smoke 40",
        "Waking in the Cemetery of Ashes, by its first shrine",
        "Waking bare-handed in the Cemetery of Ashes: grey ash underfoot between soot-stained walls, "
        "a shrine's flame burning in its iron dish, the first hint below",
    ),
    Shot(
        "cistern",
        "--map harrow_sewers --at=22,20,-117 --level 3 --equip primary=spiked_club,secondary=round_shield "
        "--smoke 40",
        "The Cistern, where the sewers meet",
        "The sewers' cistern: brick pillars, a grate in the floor and its shrine's flame burning in the dark",
    ),
    Shot(
        "harrowmere_chasm",
        "--map old_harrowmere --at=13,5,50 --level 5 --equip primary=spiked_club,secondary=round_shield "
        '--smoke 60 --script "look_down:0.22"',
        "Old Harrowmere, from the Breach Landing",
        "Looking out from a ledge over a vast amber-lit chasm, ruined brick towers rising out of it and a "
        "plaza far below",
    ),
    Shot(
        "vigil_chapel",
        "--map vigil_chapel --at=8,19,-90 --level 6 --equip primary=spiked_club,secondary=round_shield "
        "--smoke 60",
        "The Vigil Chapel, the one hall the fall never reached",
        "A dim moonstone nave, a red runner between dark pews leading to a faint glow on the altar, "
        "tall pillars either side",
    ),
    Shot(
        "combat",
        "--map abandoned_prison --at 15,22,0 --level 4 --equip primary=claymore,body=ringmail,hands=chain_mitts "
        "--smoke 100",
        "The Abandoned Prison's Claymore, against a Bone Walker",
        "A claymore held in both hands, ringmail sleeves and chain mitts, facing a bone walker in a torchlit cell row",
    ),
    Shot(
        "verdant_hollow",
        "--map verdant_hollow --at=9,12,90 --level 5 --equip primary=katana,secondary=spell:veil --smoke 40",
        "The Verdant Hollow, through the cave at the end of Harrowmere's green trail",
        "A vine-walled path under the canopy of the Verdant Hollow",
    ),
    Shot(
        "cinderhold_bridge",
        "--map cinderhold --at=29,52,-90 --level 7 --equip primary=moonless_tachi,secondary=spell:veil "
        '--smoke 60 --script "look_up:0.15"',
        "The long bridge to the Cinderhold, up Harrowmere's north road",
        "A long stone bridge leading to a black fortress under a smoky red sky: a crenellated great wall "
        "with burning windows rising from the lava, a gatehouse, a bastion, a great keep and smelter stacks",
    ),
    Shot(
        "keep_hall",
        "--map cinder_keep --at=17,18,180 --level 9 --equip primary=slagbreaker --smoke 40",
        "The great hall of the Cinderhold Keep",
        "The Cinderhold Keep's great hall: iron pillars and a brazier, a forge golem standing among them",
    ),
    Shot(
        "vesperholm",
        "--map vesperholm --at=21,63,-90 --level 10 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 60 --script "look_up:0.25"',
        "Vesperholm, the Moonbound City, under a moon that never sets",
        "Lantern Square in Vesperholm, pale stone and silver roofs under a huge moon and a sky full of stars",
    ),
    Shot(
        "herrans_castle",
        "--map herrans_castle --at=19,72,-90 --level 12 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 60 --script "look_up:0.25"',
        "Herran's Castle, on the mountain behind Vesperholm",
        "A long causeway over a gorge in the storm, a grafted footman on it, gothic towers and a black "
        "mountain under the moon beyond",
    ),
    Shot(
        "herran",
        "--map herrans_castle --at=23,5,0 --level 12 "
        "--equip primary=stormbrand,secondary=spell:ward,body=brigandine,hands=iron_gauntlets "
        '--smoke 520 --script "interact wait:0.8 forward:1.4 wait:5.5"',
        "Herran, the Many-Handed, in his anatomy theatre",
        "Herran rising in his anatomy theatre under its broken iron dome, open to the storm, "
        "his health bar above",
    ),
]


def take(shot, out):
    """Runs one smoke run into out/<name>.png with a throwaway save; returns its smoke: line."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, ASHEN_VAULT_SAVE=str(Path(tmp) / "save.json"))
        cmd = ["uv", "run", "ashen-vault", *shlex.split(shot.args), "--shot", str(out / f"{shot.name}.png")]
        run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    lines = [ln for ln in run.stdout.splitlines() if ln.startswith("smoke:")]
    if run.returncode or not lines:
        return f"FAILED ({run.returncode}): {run.stderr.strip().splitlines()[-1:]}"
    return lines[-1]


def table(shots):
    """The README's gallery: two shots a row, each with its caption beneath."""
    rows = ["<table>"]
    for i in range(0, len(shots), 2):
        pair = shots[i : i + 2]
        rows.append("  <tr>")
        for s in pair:
            rows.append(f'    <td><img src="docs/screenshots/{s.name}.png" alt="{s.alt}"></td>')
        rows.append("  </tr>")
        rows.append("  <tr>")
        for s in pair:
            rows.append(f'    <td align="center"><sub>{s.caption}</sub></td>')
        rows.append("  </tr>")
    rows.append("</table>")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="shots to take (default: all)")
    ap.add_argument("--out", type=Path, default=OUT, help="directory to write the PNGs to")
    ap.add_argument("--table", action="store_true", help="print the README gallery table and exit")
    opts = ap.parse_args()
    if opts.table:
        print(table(SHOTS))
        return 0
    known = {s.name: s for s in SHOTS}
    unknown = [n for n in opts.names if n not in known]
    if unknown:
        sys.exit(f"unknown shots: {', '.join(unknown)} (known: {', '.join(known)})")
    opts.out.mkdir(parents=True, exist_ok=True)
    for shot in [known[n] for n in opts.names] if opts.names else SHOTS:
        print(f"{shot.name}: {take(shot, opts.out)}" + (f"  [{shot.note}]" if shot.note else ""), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
