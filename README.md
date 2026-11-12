<p align="center">
  <img src="docs/logo/ashen_vault.svg" alt="Ashen Vault — beneath the silent bell" width="640">
</p>

<p align="center">
  A slow, atmospheric first-person dungeon crawler with PS1-era graphics.<br>
  Written in Python with <a href="https://github.com/electronstudio/raylib-python-cffi">raylib</a>.
  Every texture, model and sound is generated in code.
</p>

---

The bell of Harrowmere has cracked. Beneath the village well, the drowned halls of the Sunken Keep have
begun to stir. Take up a rusted sword, descend into the dark, and bring back the Ember Sigil before the
keep wakes for good.

### Inspiration

Ashen Vault is a love letter to **FromSoftware's *King's Field*** series, the slow, first-person
dungeon crawlers from the early PlayStation era that later led to *Demon's Souls* and *Dark Souls*.
It borrows their spirit: a lonely descent through dark stone halls, deliberate stamina-gauge combat,
magic learned from scrolls, and a world that tells its story through the places you walk.

It is a fan project, not a remake. All names, maps, monsters, story, art and sound are original, and
the game is not affiliated with or endorsed by FromSoftware. *King's Field* is a trademark of
FromSoftware, Inc.

## Screenshots

<table>
  <tr>
    <td><img src="docs/screenshots/title.png" alt="Title screen over the foggy village square"></td>
    <td><img src="docs/screenshots/village.png" alt="Harrowmere's cobbled square, with the shrine and the well"></td>
  </tr>
  <tr>
    <td align="center"><sub>Title screen</sub></td>
    <td align="center"><sub>Harrowmere, the village above the keep</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/dialogue.png" alt="Talking to Odrin the bell-keeper"></td>
    <td><img src="docs/screenshots/flame_bolt.png" alt="A flame bolt flying at a bone walker"></td>
  </tr>
  <tr>
    <td align="center"><sub>Odrin, keeper of the silent bell</sub></td>
    <td align="center"><sub>Flame Bolt against a Bone Walker</sub></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/warden.png" alt="The Ashen Warden boss in its hall"></td>
    <td><img src="docs/screenshots/inventory.png" alt="The Belongings screen with a rotating item preview"></td>
  </tr>
  <tr>
    <td align="center"><sub>The Ashen Warden</sub></td>
    <td align="center"><sub>Belongings, with a spinning item preview</sub></td>
  </tr>
</table>

## Features

- **PS1-style renderer**: 320×240 internal resolution, vertex snapping, affine texture warping,
  15-bit color with ordered dithering, distance fog and baked vertex lighting.
- **Deliberate, weighty combat**: an ATK gauge that refills between swings, enemy wind-ups you can read
  and interrupt, and a boss with poise.
- **Spells**: Flame Bolt, Mend and Lumen, cast from a MAG gauge.
- **Two hand-built areas**: the village of Harrowmere and the Sunken Keep, with locked doors, levers,
  a flooded cellar, chests, a shop and four villagers to talk to.
- **Everything procedural**: textures, low-poly models and sound effects are all generated at startup.
  The game itself ships no image or audio files.
- **Save shrines**: pray at a stone shrine to heal and record your journey.

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
| Turn / look | Arrow left/right, mouse, PgUp/PgDn |
| Attack | Space / left mouse |
| Cast spell / cycle spell | F or right mouse / R |
| Use, talk, open | E |
| Belongings | Tab or I |
| Quick Red Tonic / Blue Moss | 1 / 2 |
| Pause | Esc |

The same list is in the game under **Controls** on the title and pause menus.

## Tips

- Your swing damage scales with the **ATK** gauge (gold bar, bottom right). Wait for it to refill
  before swinging. It doesn't refill while you sprint.
- Spells need a full **MAG** gauge (cyan bar) as well as enough MP.
- Watch for enemies raising their weapons. A solid hit during the wind-up staggers most of them.
- In Belongings, press Enter on an equipped item (marked `(E)`) to take it off. With no weapon you fight
  bare-handed.
- Talk to everyone in Harrowmere before you descend. They have gifts and directions.

## Save file

The game saves only at shrines, to `~/.local/share/ashen_vault/save.json` (Windows:
`%USERPROFILE%\.local\share\ashen_vault\save.json`). Set the `ASHEN_VAULT_SAVE` environment variable
to use a different path.

## Development

The project uses [uv](https://docs.astral.sh/uv/) for environments and dependencies,
[ruff](https://docs.astral.sh/ruff/) for linting and formatting, and pytest with
[pytest-cov](https://pytest-cov.readthedocs.io/) for tests and coverage. All of them are configured in
`pyproject.toml` and pinned in `uv.lock`.

```sh
uv run pytest               # headless tests: maps, collision, combat, AI, saves, mesh building
uv run pytest --cov         # same, with a branch-coverage report (fails under the floor in pyproject.toml)
uv run ruff check           # lint (add --fix to auto-fix)
uv run ruff format          # format
uv add <package>            # add a runtime dependency; `uv add --dev <package>` for a dev tool
```

CI runs the same checks on every push and pull request (`.github/workflows/ci.yml`).

### Tool versions and editor settings

- Python and uv versions are pinned in `mise.toml`, `.tool-versions` and `.python-version`. With
  [mise](https://mise.jdx.dev), run `mise install` once; asdf users get the same versions from
  `.tool-versions`, and uv reads `.python-version`. Keep all three in sync when bumping.
- mise also has tasks for the commands above: `mise run play`, `test`, `lint`, `fmt` and `check`
  (`check` runs everything CI runs).
- `.editorconfig` sets UTF-8, LF line endings, a final newline, trimmed whitespace and 4-space
  indents (2 for TOML/YAML/JSON/Markdown). Most editors pick it up automatically; JetBrains and
  VS Code with the EditorConfig extension both do.

### AI coding agents

`AGENTS.md` describes the project, commands and conventions for coding agents. `CLAUDE.md` imports
it, so Claude Code, Codex, Cursor and Copilot all follow the same rules.

### Project layout

| Path | What lives there |
| --- | --- |
| `src/ashen_vault/world/`, `player/`, `ai/`, `save/` | Game logic with no raylib dependency, covered by `tests/` |
| `src/ashen_vault/render/` | PS1 shaders, procedural textures, map mesh builder, matrix rig, low-poly models |
| `src/ashen_vault/game.py` | Scenes and the main loop |
| `src/ashen_vault/ui/hud.py` | HUD, compass, menus and dialogue boxes |
| `src/ashen_vault/audio/synth.py` | Synthesized sound effects |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps (`[meta]`, `[legend]`, `[grid]`, `[entities]`) |
| `src/ashen_vault/dialogue.py` | NPC conversations |
| `docs/logo/make_logo.py` | Generates the pixel-art logo SVG |

### Debug flags

```sh
uv run ashen-vault --map sunken_keep --at 15,21,180 --smoke 100 --script "wait:1.2 attack" --shot out.png
```

- `--map NAME` skips the title screen and starts on that map.
- `--at TX,TZ,YAW` sets the start tile and heading in degrees.
- `--smoke N` runs N frames at a fixed timestep, writes a 3× screenshot and prints a state summary.
- `--script "..."` drives input: `action` presses once, `action:1.5` holds for 1.5 s, `wait:1` pauses.
- `--shot PATH` sets where `--smoke` writes its screenshot.

The README screenshots were taken this way. For example, the flame bolt shot is
`uv run ashen-vault --map sunken_keep --at 15,22,0 --smoke 30 --script "wait:0.3 cast" --shot flame_bolt.png`.
