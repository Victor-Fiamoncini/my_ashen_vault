# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor, Copilot, ...) working in this repository.
Humans are welcome to read it too.

## Project

Ashen Vault is a first-person dungeon crawler with PS1-style graphics, written in Python on top of
raylib (`raylib` package, imported as `pyray` and `raylib`). It is inspired by FromSoftware's King's
Field series, but everything in it is original: never copy names, maps, story, art, music or other
assets from King's Field or any other existing game.

All textures, models and sounds are generated in code at startup. Do not add image or audio files to
the game; `docs/` holds the only images (the logo and the README screenshots).

## Commands

Tooling is managed with uv; Python and uv versions are pinned in `mise.toml`, `.tool-versions` and
`.python-version`. `mise run <task>` wraps the same commands.

```sh
uv sync                     # create/update .venv from uv.lock
uv run ashen-vault          # play
uv run pytest               # tests (headless, no window)
uv run pytest --cov         # tests + branch coverage; fails below fail_under in pyproject.toml
uv run ruff check --fix     # lint
uv run ruff format          # format
uv run python tools/screenshots.py [names]   # retake the README screenshots
```

Before declaring work done, run all four checks: `ruff check`, `ruff format --check`,
`pytest --cov`, and a smoke run (below) if you touched anything that renders or runs per frame.
CI (`.github/workflows/ci.yml`) runs the first three.

## Smoke runs

A debug mode opens a window for N fixed-timestep frames, writes a screenshot and prints one `smoke:`
line with the game state (position, height `y=`, HP, scene, flags, items, gear, every enemy's state):

```sh
ASHEN_VAULT_SAVE=/tmp/ashen_test_save.json \
  uv run ashen-vault --map abandoned_prison --at 15,21,180 --smoke 200 --script "wait:1.2 attack" --shot /tmp/out.png
```

- Always set `ASHEN_VAULT_SAVE` to a throwaway path, so you never touch the player's real save
  (`~/.local/share/ashen_vault/save.json`, slot 1; `save_2.json` / `save_3.json` beside it are slots 2
  and 3, and `settings.json` there holds the options).
- `--at TX,TZ,YAW`: tile and heading in degrees (0 faces +x, 90 faces +z). Write a negative heading as
  `--at=15,7,-90`, or argparse reads it as a flag.
- `--script` steps: `action` presses once, `action:1.5` holds for 1.5 s, `wait:1` pauses. Actions are
  the keys of `KEYS` and `MOUSE` in `input.py`, plus `wheel_up` / `wheel_down` and `look_up` /
  `look_down`. `attack` is the Primary button, `cast` the Secondary; `interact` uses whatever you face.
  The run stops after `--smoke` frames even if the script hasn't finished, so give it enough frames.
- `--equip right=katana,left=buckler,body=brigandine,hands=iron_gauntlets` (`primary=` / `secondary=`
  also work; `none` empties a slot, `left=spell:pyre` learns and readies Pyre) and `--level 6`, which
  only sets the level for equipment requirements: HP and stats stay at level 1. `--flags a,b` starts
  with those save flags set before the map loads (a boss's dead flag, a taken sigil), as a save would
  hold them: `--flags sigil_taken,verdant_sigil_taken,iron_sigil_taken` opens the Vesper Gate.
  `--afflict poison,toxic` starts with those ailments taking hold (bleed and frost hurt, corrosion wears
  your gear), to check their screen borders.
- A `--map` start skips the area's title card, so screenshots stay clear. To see the card, walk
  through an exit (or start a New Game or load a save without `--map`).
- Combat rolls are random, so HP can vary between runs; positions, scenes, flags and items do not.
- On Wayland, `GLFW: Error: 65548` warnings are harmless.
- Ready-made starts for every area, boss and shortcut: [`docs/dev/smoke-starts.md`](docs/dev/smoke-starts.md).

## Layout

| Path | Contents |
| --- | --- |
| `src/ashen_vault/world/`, `player/`, `ai/`, `save/` | Pure game logic. **No raylib imports here**; covered by `tests/` |
| `src/ashen_vault/render/` | Shaders, procedural textures, mesh builder, models, the prop bake; the shared model pieces in `parts`, the weapons in `weapon_models`, a World's meshes and drawing in `world_view`, each area's own models in a module of their own (`cemetery_models`, `town_models`, `forge_models`, `fortress_props`, `sewer_models`, `moon_models`, `sunken_models`, `herran_models`) |
| `src/ashen_vault/ui/` | HUD, menus, dialogue boxes, fonts (`hud.py` draws them all) |
| `src/ashen_vault/audio/synth.py` | Synthesized sound effects |
| `src/ashen_vault/game.py` | Scenes and the main loop |
| `src/ashen_vault/input.py` | Key bindings and the `--script` driver |
| `src/ashen_vault/dialogue.py` | NPC conversations, gifts and shops |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. One per area: `ashen_cemetery`, `harrowmere`, `harrow_sewers`, `abandoned_prison`, `verdant_hollow`, `cinderhold`, `cinder_keep`, `vesperholm`, `old_harrowmere`, `vigil_chapel`, `herrans_castle` and `herran_spire` (`docs/dev/maps.md` describes each) |
| `tests/` | pytest suite; `conftest.py` has a small test map, `test_*_world.py` build a real `World` headless |
| `tools/` | `screenshots.py` (the README gallery), the level planner and level sketch (design aids) |
| `docs/dev/` | The detailed guides below |

## Detailed guides

Read the one that covers what you are changing before you start:

- [`docs/dev/maps.md`](docs/dev/maps.md): the map format, floors and hazards, terrain (lifts, rafts,
  bridges), thin walls, roofs, landmarks, exits, doors and boss arenas, hints, props, and the
  solvability tests each map must pass.
- [`docs/dev/enemies.md`](docs/dev/enemies.md): AI flags, special moves, bosses (rising from ash,
  twins, phase two), materials, death poses and the detail every enemy model must keep.
- [`docs/dev/gameplay.md`](docs/dev/gameplay.md): equipment slots, weight, durability, ailments,
  weapons, arts and secrets, spells, shops and gifts, shrines, saves and flags, and the story.
- [`docs/dev/rendering.md`](docs/dev/rendering.md): static props and the bake, model primitives,
  weapon models and the first-person arms, villagers, town and fortress models, fonts.
- [`docs/dev/smoke-starts.md`](docs/dev/smoke-starts.md): smoke-run starts for every area and fight.

## Rules

- Python 3.11+ syntax; ruff settings in `pyproject.toml` (line length 110, double quotes).
- Use `util.rround` (round half away from zero) instead of built-in `round` in game math. The code was
  ported from Ruby and its numbers depend on that rounding.
- Keep new logic in the raylib-free packages and add tests for it. `world/world.py` is pure and imports
  nothing from `render/`: its GPU side and all its drawing live in `render/world_view.py` (`World.view`,
  which the game hands it through `game.world_view`). Drive it headless as `tests/test_prison_world.py`
  does (a `FakeGame` with a no-op GPU).
- Map grids are whitespace-sensitive: never reformat a `.map` file. Each grid character is one 2 m
  tile.
- Internal resolution is 320x240 (`screen.py`); UI coordinates are in that space. Derive HUD positions
  from `HUD_MARGIN` / `HUD_PAD` / `HUD_GAP` and draw every box with `hud.hud_box` (`HUD_RADIUS`
  corners).
- Players see the hand slots as **Primary** and **Secondary**: never say "hand" in text the player
  sees.
- New content often needs entries in lookup tables that tests enforce (a weapon's HUD icon, a boss
  door's dressing, a floor's footstep surface, a villager's look). Run the tests and read the failures.
- Add dependencies with `uv add` (runtime) or `uv add --dev` (tooling), never by hand-editing
  `uv.lock`.

## Git

- Work on the `development` branch; `master` only receives fast-forward merges from it.
- Contributor workflow (PRs to `development`, DCO sign-off) is in CONTRIBUTING.md.
- Commit only when asked. Don't commit `.idea/`, screenshots outside `docs/`, or coverage files.
- The README screenshots show the HUD and fonts. After changing either, they can be retaken with
  `tools/screenshots.py`, but leave that to the maintainer unless asked.
