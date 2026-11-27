<p align="center">
  <img src="docs/logo/ashen_vault.svg" alt="Ashen Vault — beneath the silent bell" width="640">
</p>

<p align="center">
  A slow, atmospheric first-person dungeon crawler with PS1-era graphics.<br>
  Written in Python with <a href="https://github.com/electronstudio/raylib-python-cffi">raylib</a>.
  Every texture, model and sound is generated in code.
</p>

---

You are one of the Ashen, woken in a cemetery of ashes by a single toll of Harrowmere's bell, though no
hand was on its rope. Old Odrin, the bell-keeper, knows the prophecy: whoever wakes must win five sigils
to raise the king who sits turned to stone in the cathedral. Many Ashen woke before you. None came back.
Beneath the grate in the old gaol's yard, the sealed cells of the Abandoned Prison have begun to stir, and at the end of a green trail out of the square a cave opens on the jungle of the
Verdant Hollow, which has swallowed the old woodcutters' camp. Up the north road, past a long bridge over
a gorge of fire, the forges of the Cinderhold burn again, and two iron gargoyles keep watch from its roof.
Take up a rusted sword, bring back the Ember Sigil from the prison, the Verdant Sigil from the hollow and the
Iron Sigil from the Cinderhold. At the head of the cathedral steps the Vesper Gate stands open on
Vesperholm, a city drowned in the light of a full moon that never sets, where a duchess keeps the fourth
sigil in her cathedral. The fifth was never the king's: above the clouds, in a castle of towers between
the sun and the moon, Herran keeps it, Ilvane's brother, who wanted the many hands of their mother, the
old god Lyra, and sewed the arms of drakes and men onto his own back. Bring all five
home and let the bell sing again.

### Inspiration

Ashen Vault is a love letter to **FromSoftware's *King's Field*** series, the slow, first-person
dungeon crawlers from the early PlayStation era that later led to *Demon's Souls* and *Dark Souls*.
It borrows their spirit: a lonely descent through dark stone halls, deliberate stamina-gauge combat,
magic learned from scrolls, and a world that tells its story through the places you walk.

It also owes a great deal to FromSoftware's **_Dark Souls_** series: shrines that heal you and raise
the fallen again, gold left in a heap where you died, shortcuts that fold an area back onto its
shrine, bosses behind fog-sealed doors, and a story told in fragments by a few strange people who
stayed. Vesperholm, the moonlit city, takes its mood from *Dark Souls III*'s cold, moonlit
cathedral city: pale stone, eternal night and ghostly knights.

It is a fan project, not a remake. All names, maps, monsters, story, art and sound are original, and
the game is not affiliated with or endorsed by FromSoftware. *King's Field* and *Dark Souls* are
trademarks of FromSoftware, Inc. (*Dark Souls* is published by Bandai Namco Entertainment).

## Screenshots

<table>
  <tr>
    <td><img src="docs/screenshots/village.png" alt="The Silent Bell in its frame on Harrowmere's paved Bell Square, a cathedral tower behind, a hatchet and a buckler in hand"></td>
    <td><img src="docs/screenshots/cemetery.png" alt="Waking bare-handed in the Cemetery of Ashes: grey ash underfoot between soot-stained walls, a shrine's flame burning in its iron dish, the first hint below"></td>
  </tr>
  <tr>
    <td align="center"><sub>The Silent Bell, at the heart of Harrowmere</sub></td>
    <td align="center"><sub>Waking in the Cemetery of Ashes, by its first shrine</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/cistern.png" alt="The sewers' cistern: brick pillars, a grate in the floor and its shrine's flame burning in the dark"></td>
    <td><img src="docs/screenshots/harrowmere_chasm.png" alt="Looking out from a ledge over a vast amber-lit chasm, ruined brick towers rising out of it and a plaza far below"></td>
  </tr>
  <tr>
    <td align="center"><sub>The Cistern, where the sewers meet</sub></td>
    <td align="center"><sub>Old Harrowmere, from the Breach Landing</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/vigil_chapel.png" alt="A dim moonstone nave, a red runner between dark pews leading to a faint glow on the altar, tall pillars either side"></td>
    <td><img src="docs/screenshots/combat.png" alt="A claymore held in both hands, ringmail sleeves and chain mitts, facing a bone walker in a torchlit cell row"></td>
  </tr>
  <tr>
    <td align="center"><sub>The Vigil Chapel, the one hall the fall never reached</sub></td>
    <td align="center"><sub>The Abandoned Prison's Claymore, against a Bone Walker</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/verdant_hollow.png" alt="A vine-walled path under the canopy of the Verdant Hollow"></td>
    <td><img src="docs/screenshots/cinderhold_bridge.png" alt="A long stone bridge leading to a black fortress under a smoky red sky: a crenellated great wall with burning windows rising from the lava, a gatehouse, a bastion, a great keep and smelter stacks"></td>
  </tr>
  <tr>
    <td align="center"><sub>The Verdant Hollow, through the cave at the end of Harrowmere's green trail</sub></td>
    <td align="center"><sub>The long bridge to the Cinderhold, up Harrowmere's north road</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/keep_hall.png" alt="The Cinderhold Keep's great hall: iron pillars and a brazier, a forge golem standing among them"></td>
    <td><img src="docs/screenshots/vesperholm.png" alt="Lantern Square in Vesperholm, pale stone and silver roofs under a huge moon and a sky full of stars"></td>
  </tr>
  <tr>
    <td align="center"><sub>The great hall of the Cinderhold Keep</sub></td>
    <td align="center"><sub>Vesperholm, the Moonbound City, under a moon that never sets</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/herrans_castle.png" alt="A terrace of pale stone high over the clouds, red-brick Victorian towers and a needle spire beyond"></td>
    <td><img src="docs/screenshots/herran.png" alt="Herran's grafted arms reaching in under the broken iron dome of his observatory, his health bar above"></td>
  </tr>
  <tr>
    <td align="center"><sub>Herran's Castle, its towers over a sea of cloud</sub></td>
    <td align="center"><sub>Herran, the Many-Handed, in his observatory</sub></td>
  </tr>
</table>

## Features

- **PS1-style renderer**: 320×240 internal resolution, vertex snapping, affine texture warping,
  15-bit color with ordered dithering, distance fog and baked vertex lighting, under skies of drifting
  cloud.
- **Deliberate, weighty combat**: an ATK gauge that refills between swings, tap for a light attack
  and hold for a heavy, and enemy wind-ups you can read and interrupt. Every swing, sprint and block
  costs stamina.
- **Weapons with their own movesets**: swords, greatswords, katanas, whips, maces, clubs, axes and
  hammers, each light, medium, heavy or great, which sets its speed, stamina cost and force. Some
  hide a secret attack, and a few unleash an art of lightning, fire, thorns or slag.
- **Two slots**: put a weapon, a shield or a spell in either; the left mouse button works Primary and
  the right one Secondary. Two-handed weapons fill both. The best gear needs a higher level.
- **Gear that weighs and wears**: a heavy load slows you and costs more stamina; weapons dull, shields
  crack and armor splits until the smith mends them. Body armor and gauntlets change the arms you see.
- **Ailments**: poison, toxin, bleeding, rot, corrosion and moon-frost build up with each blow from the foes
  that carry them, and each one that takes hold marks the edges of the view. The herbalist sells their
  remedies.
- **Spells taught by scrolls**: Flame Bolt, Mend, Lumen, Ashen Ward, Venom Dart, Veil of Mist, Pyre,
  Thunder Spear and Arcane Motes, found in chests or sold in town. Iron foes conduct lightning and
  shrug off fire; stone ones crack under blunt weapons.
- **Bosses behind great doors**: the Ashen Sexton fights with grave ash, the Ashen Warden's blade
  catches fire at half health, the Butcher swings his cleaver among the meat hooks, Mother Gnawl and
  the Sodden Pall rule the sewers, the Keystone, the giant the first city stood on, rises in its sunken court, the Loom Mother calls her brood, the Mire Tyrant wallows on its island in the fen, two iron gargoyles take turns on
  the keep's roof, Duchess Ilvane, the Moonwed, calls the moon down on you in her cathedral, and
  Herran, the Many-Handed, rakes you with eight grafted arms in the observatory atop his spire. Die in
  an arena and only fog remains at its door.
- **Nine areas, hand-built**:
  - the Cemetery of Ashes where you wake, a short first level that teaches as you go;
  - Harrowmere, a walled town of stone and half-timbered houses under clay-tile roofs, climbing in
    terraces from its harbour past the Silent Bell to the cathedral where the Enthroned sits, with a smith, an
    herbalist, a trader and a swordsmith to trade with;
  - the Harrow Sewers under its streets, four grates down to rats, slimes that split, the drowned and
    leeches in the sludge;
  - Old Harrowmere below them, the sunken first city: tiers of drowned towers and stairs over a sheer
    chasm, a rift of daylight far overhead, stone golems that stand like statues and bell-keepers
    whose mortar-light staves wake them, and once the Keystone falls, the untouched Vigil Chapel;
  - the Abandoned Prison below the gaol's grate: dark cell blocks where hollow inmates still kneel, a captive
    monk behind his bars, a chapel to faceless old gods, traps, and cage lifts down to a skull-walled
    Undercroft and up to the Warden's Gallery;
  - the Verdant Hollow at the end of the green trail: rafts, ledges, a log slope, spore pods, dark caves
    and a canopy walk;
  - the Cinderhold up the north road, a fortress of lava, flame jets and iron, its keep a map of its own,
    reached across the Sallow Fen, a violet mire whose wading poisons you and whose three beacons
    must be smothered before its gate opens;
  - and Vesperholm, the Moonbound City behind the Vesper Gate at the head of the cathedral steps:
    moonlit streets drowned in the light of a moon that never sets, a glass bridge over a gorge,
    and a castle where the dead keep watch as pale shades;
  - and above them all, through a portal in Lyra's Chapel, Herran's Castle: Victorian towers of sooted
    dark brick and gilt iron over a sea of cloud, a walk of iron grating between them, many-armed drakes
    on the wing, gowned drake magi, a secret laboratory of elixirs and grafts, and the spire where Herran waits.
- **Shortcuts and secrets**: barred doors, fastened lifts and drawbridges fold each area back onto its
  shrine; some walls aren't walls and some chests aren't chests.
- **Dark places**: caves swallow your light until you burn Lumen or kindle the cold braziers, which
  stay lit for good.
- **Save shrines**: rest to heal and record your journey (the fallen rise again when you do), and use
  the shrine store shared by every shrine. Die and your gold stays in a heap of ash where you fell.
- **Everything procedural**: textures, low-poly models and sound effects are all generated at startup.
  The game itself ships no image or audio files.

## Installing

### What you need

- **Python 3.11 or newer**. Check with `python3 --version`.
- **A GPU with OpenGL 3.3**. Any graphics card or integrated GPU from the last ten years works.
- **Linux, macOS or Windows**. The `raylib` package ships prebuilt binaries for all three, so no C
  compiler is required.

### Option 1: install it as an app (recommended for players)

[uv](https://docs.astral.sh/uv/) (or [pipx](https://pipx.pypa.io/)) installs the game into its own
isolated environment and puts an `ashen-vault` command on your PATH:

```sh
git clone <this repository's URL> my_ashen_vault
cd my_ashen_vault
uv tool install .          # or: pipx install .
ashen-vault
```

To update later, `git pull` and then run `uv tool install --force .`. To remove the game, run
`uv tool uninstall ashen-vault`.

### Option 2: run from a source checkout (recommended for development)

Install uv once ([other install methods](https://docs.astral.sh/uv/getting-started/installation/)):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh                          # Linux and macOS
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"               # Windows
```

Then, on any platform:

```sh
git clone <this repository's URL> my_ashen_vault
cd my_ashen_vault
uv run ashen-vault
```

`uv run` creates `.venv`, installs the exact versions pinned in `uv.lock` (including dev tools) and
starts the game. It also downloads a matching Python if you don't have one. `uv run python -m
ashen_vault` works too.

Without uv, plain pip works: `python3 -m venv .venv`, `.venv/bin/pip install -e .`, then
`.venv/bin/ashen-vault`.

### Troubleshooting

| Problem | Fix |
| --- | --- |
| `GLFW: Error: 65548 ... Wayland: The platform does not provide the window position` | Harmless warning on Wayland. The game runs normally. |
| Window opens but no sound | No audio device was found. The game keeps running silently. |
| OpenGL errors or a black window on Linux | Install your distribution's Mesa / OpenGL drivers (e.g. `mesa` on Arch, `libgl1` on Debian/Ubuntu). |
| `No matching distribution found for raylib` | Your Python version or platform has no prebuilt `raylib` wheel. Try a different recent CPython release on x86_64 or arm64. |
| Want to start over | Delete the save file (see [Save file](#save-file)). |

## Controls

| Action | Keys |
| --- | --- |
| Move / strafe | W S / A D (or arrow up/down) |
| Sprint | Hold Shift |
| Turn / look | Mouse |
| Primary / Secondary | Left mouse / right mouse |
| Heavy attack | Hold the button, then release |
| Block | Hold the button of the slot with the shield |
| Cast spell | The button of the slot holding the spell |
| Equip, ready a spell | Belongings (Tab): 1 for Primary, 2 for Secondary, or Enter / click to choose |
| Use, talk, open | E |
| Belongings | Tab or I; A / D (or Left / Right) switch tabs |
| Use quick item / pick quick slot | Middle mouse / mouse wheel |
| Set quick slots | Belongings (Tab), Items tab: Enter / click a consumable |
| Pause | Esc |
| Menus | Up/Down, Enter, Esc, or point, click, right-click and scroll with the mouse |

The same list is in the game under **Controls** on the title and pause menus.

## Tips

- The mouse in the bottom right shows your slots: Primary on its left button, Secondary on its right
  and the item in your selected quick slot on the wheel. Fill the four quick slots from the Items tab
  of Belongings; the wheel steps only through the slots you filled. HP, MP, ST and a compass share the bottom-left box; an ember on the
  compass points to the nearest boss still alive.
- Your swing hits as hard as the gold **ATK** bar on its button is full: wait for it to flash. Hold
  the button to charge a **heavy attack** (the orange bar), then release.
- Spells need your **focus** back as well as MP: the cyan bar on the spell's button refills after each
  cast.
- Sprinting, swinging and blocking drain **ST**. Empty it and you are winded until it recovers. Every
  level you gain raises it, so you can sprint and fight for longer.
- Watch the **Load** line in Belongings: a Heavy or Overloaded load slows your stride and ST. Before
  you equip or buy, the stats show what would change: green is better, red is worse.
- Find a copy of gear you already own and it is sold on the spot for half its price.
- A solid hit during an enemy's wind-up staggers most of them.
- Traps keep a rhythm: watch the spikes, blades and flame jets before you cross, and don't stand
  still on cracked stone.
- Step onto the plate in a lift's middle to ride it, or the plate before its shaft to call it. A lift
  that won't come is fastened from the other end: find your way there and ride it once.
- A door that won't open from your side is barred from the other. Find the way round.
- Spells fly where you look: aim down at slimes. Iron things hate lightning.
- Talk to everyone in Harrowmere. They have gifts and directions.

## Save file

The game saves only at shrines. It keeps three save slots, each with its own journey and play time:
New Game and Load Game on the title let you choose one, and Continue wakes you in the one saved last.
Slot 1 is `~/.local/share/ashen_vault/save.json` (Windows:
`%USERPROFILE%\.local\share\ashen_vault\save.json`); slots 2 and 3 are `save_2.json` and `save_3.json`
beside it. Set the `ASHEN_VAULT_SAVE` environment variable to use a different path for slot 1 (the
others follow it).

## Development

The project uses [uv](https://docs.astral.sh/uv/) for environments and dependencies,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting, and pytest with
[pytest-cov](https://pytest-cov.readthedocs.io/) for tests and coverage, all configured in
`pyproject.toml` and pinned in `uv.lock`. With [mise](https://mise.jdx.dev), `mise install` sets up
the pinned Python and uv, and `mise run check` runs everything CI runs.

```sh
uv run pytest --cov         # headless tests with a branch-coverage report
uv run ruff check           # lint (add --fix to auto-fix)
uv run ruff format          # format
uv run python tools/screenshots.py   # retake the screenshots above (or name the ones to retake)
```

[`AGENTS.md`](AGENTS.md) is the developer guide, written for coding agents and humans alike: the
project layout, conventions and debug flags, with detailed guides in [`docs/dev/`](docs/dev/).

### Debug flags

```sh
ASHEN_VAULT_SAVE=/tmp/test_save.json \
  uv run ashen-vault --map abandoned_prison --at 15,21,180 --smoke 100 --script "wait:1.2 attack" --shot out.png
```

- `--map NAME` skips the title and starts on that map; `--at TX,TZ,YAW` sets the tile and heading (write
  a negative heading as `--at=15,7,-90`).
- `--smoke N` runs N frames at a fixed timestep, writes a screenshot to `--shot PATH` and prints the
  game state.
- `--script "..."` drives input: `action` presses once, `action:1.5` holds for 1.5 s, `wait:1` pauses.
- `--equip primary=katana,secondary=buckler,body=brigandine` starts with that gear, and `--level N` at
  that level (for equipment requirements only).
- Set `ASHEN_VAULT_SAVE` to a throwaway path to keep test runs away from your real save.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, the checks to run, and
the commit sign-off. Pull requests go against the `development` branch.

---

Released in 2026. This project is under the [GPL-3.0](LICENSE) license.

By [Victor B. Fiamoncini](https://github.com/Victor-Fiamoncini) ☕️
