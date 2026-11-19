"""Retakes the README screenshots.

    uv run python tools/screenshots.py                 # every shot, into docs/screenshots/
    uv run python tools/screenshots.py sexton warden   # just these
    uv run python tools/screenshots.py --out /tmp/x    # somewhere else, to look before replacing
    uv run python tools/screenshots.py --table         # print the README's gallery table

Each shot is a smoke run with its own throwaway save, so the player's real save is never touched.
The gear in each shot is gear the player could hold by then: the --level and --equip follow the
game's progression (cemetery, town, sewers, prison, hollow, Cinderhold, Vesperholm).
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
        "title",
        "--smoke 60",
        "Title screen",
        "Title screen circling the Silent Bell on the foggy, cobbled Bell Square",
    ),
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
        "mourner",
        "--map ashen_cemetery --at=11,22,-90 --equip primary=rusted_sword,secondary=none --smoke 40",
        "A Shrouded Mourner, bowed at a grave until you come too close",
        "A Shrouded Mourner, a hooded figure in dark robes, bowed by a stone coffin in the cemetery's "
        "chapel, a rusted sword in hand",
    ),
    Shot(
        "silk",
        "--map ashen_cemetery --at=12,18,-135 --equip primary=rusted_sword,secondary=spell:flame "
        '--smoke 90 --script "wait:0.3 cast wait:0.9"',
        "Flame Bolt burning the silk off the chapel door",
        "The silk sealing the chapel's far door burning away from the bottom up, charred patches "
        "glowing at the edges, flames licking up its face",
    ),
    Shot(
        "sexton",
        "--map ashen_cemetery --at=10,11,-90 --equip primary=rusted_sword,secondary=spell:flame "
        '--smoke 700 --script "wait:0.1 interact wait:2.5 forward:2.0 wait:3.6"',
        "The Ashen Sexton, keeper of the cemetery's gate",
        "The Ashen Sexton in its walled yard, a hulking grave-digger of ash raising its spade, its health bar above",
        note="its moves are random: retake until its spade is raised",
    ),
    Shot(
        "dialogue",
        "--map harrowmere --at=28,25,-90 --equip primary=rusted_sword,secondary=spell:flame "
        '--smoke 40 --script "wait:0.2 interact"',
        "Odrin, keeper of the silent bell",
        "Talking to Odrin the bell-keeper",
    ),
    Shot(
        "forge",
        "--map harrowmere --at=8,18,180 --equip primary=hatchet,secondary=buckler --smoke 40",
        "Brannoc's forge",
        "Brannoc the smith hammering at his anvil in the forge",
    ),
    Shot(
        "cathedral",
        "--map harrowmere --at=18,6,180 --equip primary=ashblade,secondary=spell:mend --smoke 40",
        "The cathedral, where the Enthroned sits",
        "The cathedral's nave, pews and pillars between stained-glass windows, leading to the "
        "Enthroned under a rose window",
    ),
    Shot(
        "inventory",
        "--map harrowmere --at=20,44,-90 --level 3 "
        "--equip primary=mace,secondary=round_shield,body=ringmail,hands=leather_gloves "
        '--smoke 60 --script "wait:0.2 menu wait:0.2 tab_next"',
        "Belongings, with a spinning item preview",
        "The Belongings screen: a mace in the Primary slot, a round shield in Secondary, ringmail and "
        "leather gloves, the Equipped panel and the stats",
    ),
    Shot(
        "sewer_drains",
        "--map harrow_sewers --at=15,23,90 --level 3 --equip primary=leather_whip,secondary=spell:flame --smoke 40",
        "The Market Drains, under Harrowmere's streets",
        "A narrow vaulted sewer run, sludge underfoot between brick walls",
    ),
    Shot(
        "cistern",
        "--map harrow_sewers --at=22,20,-117 --level 3 --equip primary=spiked_club,secondary=round_shield "
        "--smoke 40",
        "The Cistern, where the sewers meet",
        "The sewers' cistern: brick pillars, a grate in the floor and its shrine's flame burning in the dark",
    ),
    Shot(
        "mother_gnawl",
        "--map harrow_sewers --at=34,32,-160 --level 4 --equip primary=bastard_sword,secondary=buckler "
        '--smoke 300 --script "wait:3.6 back:0.8"',
        "Mother Gnawl rising in her open nest",
        "Mother Gnawl, a giant rat with glowing red eyes, risen in her dark nest, her health bar above",
    ),
    Shot(
        "sump_maw",
        "--map harrow_sewers --at=41,13,-90 --level 4 --equip primary=spiked_club,secondary=round_shield "
        '--smoke 300 --script "wait:4.5"',
        "The Sump Maw, behind its great door",
        "The Sump Maw, a wave of black sludge crusted with skulls, its fanged maw open, in its flooded cistern",
    ),
    Shot(
        "combat",
        "--map abandoned_prison --at 15,22,0 --level 4 --equip primary=claymore,body=ringmail,hands=chain_mitts "
        "--smoke 100",
        "The prison's Claymore, against a Bone Walker",
        "A claymore held in both hands, ringmail sleeves and chain mitts, facing a bone walker",
    ),
    Shot(
        "warden",
        "--map abandoned_prison --at=15,7,-90 --level 4 --equip primary=claymore --smoke 300",
        "The Ashen Warden",
        "The Ashen Warden boss in his hall",
    ),
    Shot(
        "undercroft_lift",
        "--map abandoned_prison --at 4,24,90 --level 5 --equip primary=bastard_sword,secondary=kite_shield "
        '--smoke 680 --script "forward:0.15 wait:5 forward:0.6 wait:7"',
        "Riding the cage lift down into the Undercroft",
        "Riding a barred cage lift down a shaft toward a wall of skulls and bones",
    ),
    Shot(
        "gallery",
        "--map abandoned_prison --at=27,7,-90 --level 5 --equip primary=war_hammer --smoke 300",
        "The Butcher, waiting in his slaughter hall",
        "The Butcher, a hooded brute with a cleaver, in his slaughter hall above the Warden's Gallery, "
        "meat hooks hanging behind him",
    ),
    Shot(
        "corvane",
        "--map harrowmere --at=6,26,180 --level 5 --equip primary=war_hammer --smoke 700 "
        '--script "forward:2 interact wait:0.8 forward:2.2 wait:0.2 interact wait:0.3 confirm wait:0.3 confirm wait:0.3 confirm wait:0.3 confirm"',
        "Corvane's blades, for those who have proven themselves",
        "Corvane's shop of curved blades, the katana on show",
    ),
    Shot(
        "jungle_trail",
        "--map harrowmere --at=56,34,-90 --level 5 --equip primary=butcher_cleaver,secondary=spell:lumen "
        "--smoke 40",
        "The green trail out of Harrowmere, ending at the cave",
        "A narrow hedged trail under a darkening canopy, glowing toadstools at the cave mouth ahead",
    ),
    Shot(
        "mossmouth",
        "--map verdant_hollow --at=15,31,180 --level 5 --equip primary=thornlash,secondary=spell:pyre "
        '--smoke 120 --script "wait:0.3 cast wait:3"',
        "Mossmouth: a cold brazier kindled with Pyre",
        "A brazier just kindled in the dark Mossmouth cave, a chest beside it",
    ),
    Shot(
        "verdant_hollow",
        "--map verdant_hollow --at=9,12,90 --level 5 --equip primary=katana,secondary=spell:veil --smoke 40",
        "The Verdant Hollow, through the cave at the end of Harrowmere's green trail",
        "A vine-walled path under the canopy of the Verdant Hollow",
    ),
    Shot(
        "bark_husk",
        "--map verdant_hollow --at=26,17,-90 --level 5 --equip primary=leather_whip,secondary=spell:pyre --smoke 60",
        "A Bark Husk: circle it and strike the glow in its back",
        "A Bark Husk, a hollow dead tree with a gaping face and splintered crown, beside a thorn plant",
    ),
    Shot(
        "canopy_walk",
        "--map verdant_hollow --at=31,3,180 --level 5 --equip primary=katana,secondary=spell:venom "
        '--smoke 40 --script "look_down:0.12"',
        "The Canopy Walk, the long way to the Loom Mother",
        "A plank walkway lit by torches high in the treetops, a snare bloom waiting on it",
    ),
    Shot(
        "root_caverns",
        "--map verdant_hollow --at=6,38,-100 --level 5 --equip primary=flamberge --smoke 25",
        "A bonfire in the Root Caverns, under the bog",
        "A bonfire throwing sparks in the dark Root Caverns, roots hanging from the ceiling",
    ),
    Shot(
        "loom_mother",
        "--map verdant_hollow --at=15,7,-90 --level 6 --equip primary=flamberge --smoke 300",
        "The Loom Mother",
        "The Loom Mother, a giant spider boss",
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
        "postern_ledge",
        "--map cinderhold --at=28,30,180 --level 7 "
        "--equip primary=bearded_axe,secondary=kite_shield,body=brigandine --smoke 190",
        "The postern ledge: a magma bomb about to land, a bowman waiting",
        "A narrow ledge along the fortress wall above lava, a magma bomb arcing toward a glowing landing "
        "circle and an iron bowman ahead",
        note="the bomb's timing can drift: retake if no circle shows",
    ),
    Shot(
        "foundry",
        "--map cinderhold --at=18,17,180 --level 7 "
        "--equip primary=stormbrand,secondary=spell:thunder,hands=iron_gauntlets --smoke 40",
        "The foundry, where a Forge Golem guards the lava channels",
        "The torchlit foundry hall, a channel of lava across the floor and a forge golem beyond it, "
        "the Stormbrand in an iron gauntlet",
    ),
    Shot(
        "thunder_scroll",
        "--map cinderhold --at=4,15,-90 --level 7 --equip primary=zweihander --smoke 280 "
        '--script "interact wait:1.5 menu wait:0.2 tab_next wait:0.2 tab_next wait:0.2 tab_next '
        'wait:0.2 down wait:3"',
        "A spell scroll, sealed with its rune",
        "Belongings on the Spells tab, previewing the Scroll of Thunder Spear: a soot-dark scroll on iron "
        "rods, its blue wax seal pressed with a glowing lightning rune",
    ),
    Shot(
        "keep_hall",
        "--map cinder_keep --at=17,18,180 --level 9 --equip primary=slagbreaker --smoke 40",
        "The great hall of the Cinderhold Keep",
        "The Cinderhold Keep's great hall: iron pillars and a brazier, a forge golem standing among them",
    ),
    Shot(
        "gargoyles",
        "--map cinder_keep --at=9,6,180 --level 9 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 200 --script "wait:1 attack wait:1"',
        "Brand and Bellows, the twin gargoyles on the keep's roof",
        "Two iron gargoyles on the keep's walled rooftop, battlements and turrets behind them, under two "
        "boss health bars",
    ),
    Shot(
        "vesper_gate",
        "--map harrowmere --at=22,3,-90 --level 10 "
        '--equip primary=stormbrand,secondary=spell:ward --smoke 80 --script "back:0.35 look_up:0.12"',
        "The Vesper Gate, standing open at the head of the cathedral steps",
        "The Vesper Gate in Harrowmere's north wall standing open, pale moonlight pouring through it",
    ),
    Shot(
        "vesperholm",
        "--map vesperholm --at=21,43,-90 --level 10 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 60 --script "look_up:0.25"',
        "Vesperholm, the Moonbound City, under a moon that never sets",
        "Lantern Square in Vesperholm, pale stone and silver roofs under a huge moon and a sky full of stars",
    ),
    Shot(
        "veiled_knight",
        "--map vesperholm --at=17,21,180 --level 10 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 120 --script "wait:0.9 attack"',
        "A Veiled Knight in the castle bailey",
        "A Veiled Knight, a pale armored shade, closing in across the moonlit castle bailey",
    ),
    Shot(
        "lantern_wraith",
        "--map vesperholm --at=25,42,-90 --level 10 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 145 --script "wait:1.7"',
        "A Lantern Wraith's frost lance: moon-frost numbs your legs",
        "A lantern-bearing wraith in a moonlit square by a pale statue, frost creeping in at the screen's "
        "corners after its lance hits",
    ),
    Shot(
        "cathedral_long_night",
        "--map vesperholm --at=21,26,-90 --level 10 --equip primary=stormbrand,secondary=spell:ward "
        '--smoke 60 --script "look_up:0.25"',
        "The Cathedral of the Long Night, from the bailey",
        "The front of a pale cathedral rising over the castle bailey, its spires lit by the moon",
    ),
    Shot(
        "duchess",
        "--map vesperholm --at=21,8,-90 --level 10 "
        "--equip primary=stormbrand,secondary=spell:ward,body=brigandine,hands=iron_gauntlets "
        '--smoke 300 --script "wait:4.2"',
        "Duchess Ilvane, the Moonwed, in her choir",
        "Duchess Ilvane, a tall veiled noblewoman with a crescent glaive, rising in the cathedral's choir, "
        "her health bar above",
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
