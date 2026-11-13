# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex, Cursor, Copilot, ...) working in this repository.
Humans are welcome to read it too.

## Project

Ashen Vault is a first-person dungeon crawler with PS1-style graphics, written in Python on top of
raylib (`raylib` package, imported as `pyray` and `raylib`). It is inspired by FromSoftware's King's
Field series but everything in it is original: never copy names, maps, story, art, music or other
assets from King's Field or any other existing game.

All textures, models and sounds are generated in code at startup. Do not add image or audio files to
the game; `docs/` holds the only images (logo and README screenshots).

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
```

Before declaring work done, run all four checks: `ruff check`, `ruff format --check`,
`pytest --cov`, and a smoke run (below) if you touched anything that renders or runs per frame.
CI (`.github/workflows/ci.yml`) runs the first three.

## Smoke runs

The game has a headless-friendly debug mode. It opens a window for N fixed-timestep frames, writes a
screenshot and prints one `smoke:` line with the game state:

```sh
ASHEN_VAULT_SAVE=/tmp/ashen_test_save.json \
  uv run ashen-vault --map sunken_keep --at 15,21,180 --smoke 200 --script "wait:1.2 attack" --shot /tmp/out.png
```

- Always set `ASHEN_VAULT_SAVE` to a throwaway path so you never touch the player's real save
  (`~/.local/share/ashen_vault/save.json`).
- `--script` steps: `action` presses once, `action:1.5` holds for 1.5 s, `wait:1` pauses. Actions are
  the keys of `KEYS` and `MOUSE` in `src/ashen_vault/input.py`, plus `wheel_up` / `wheel_down`.
  `attack` is the left mouse button (the right hand) and `cast` the right one (the left hand): each
  swings, blocks or casts depending on what that hand holds.
- `--equip right=katana,left=buckler,body=brigandine,hands=iron_gauntlets` starts with that gear (a slot
  set to `none` empties it; `left=spell` readies the spell there) and `--level 6` at that level.
- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first.
- Combat rolls are random, so HP in the `smoke:` line can vary between runs. Positions, scenes, flags
  and items are deterministic.
- On Wayland, `GLFW: Error: 65548` warnings are harmless.
- A negative heading must be written `--at=15,7,-90` (with `=`), or argparse reads it as a flag.
- Useful starts: `--map harrowmere --at 25,13,-90` (the jungle doorway), `--map verdant_hollow` (the
  grove), `--at=49,12,-90` (the Highland log slope), `--at=15,7,-90` (the Loom Mother),
  `--map harrowmere --at=6,18,180 --script "forward:1 interact"` (Corvane; below
  `--level 5` they stay silent).

## Layout

| Path | Contents |
| --- | --- |
| `src/ashen_vault/world/`, `player/`, `ai/`, `save/` | Pure game logic. **No raylib imports here**; covered by `tests/` |
| `src/ashen_vault/render/` | Shaders (`shaders/ps1.*`), procedural textures, mesh builder, matrix rig, models |
| `src/ashen_vault/game.py` | Scenes and the main loop |
| `src/ashen_vault/ui/hud.py` | HUD, menus, dialogue boxes |
| `src/ashen_vault/audio/synth.py` | Synthesized sound effects |
| `src/ashen_vault/input.py` | Key bindings and the `--script` driver |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. `harrowmere` (the village), `sunken_keep` (the dungeon below the well), `verdant_hollow` (the jungle behind the overgrown house) |
| `src/ashen_vault/world/hazards.py` | Dungeon traps: floor spikes, pendulum blades, crumbling floors |
| `src/ashen_vault/world/terrain.py` | Outdoor terrain: rafts, planks, ledges, rotten floorboards, currents, thorns, chasm and river falls, hard landings, the log rack, spore pods (`World.terrain`) |
| `src/ashen_vault/world/rest.py` | The shrine rest: timing and the pixelated ember fog pattern drawn while you pray |
| `src/ashen_vault/ui/smallfont.py` | The small mixed-case pixel font used for in-game messages, prompts and the boss bar |
| `src/ashen_vault/player/weapons.py` | Weapon categories, light/heavy/quick attacks, swing tempo and the secret attacks (`secret()`) |
| `src/ashen_vault/player/guard.py` | Shield blocking: what a raised shield stops and what it costs in ST |
| `src/ashen_vault/world/relics.py` | Boss relics (Ember and Verdant Sigils), their drop/taken flags and the two-sigil ending |
| `src/ashen_vault/dialogue.py` | NPC conversations and the shop list |
| `tests/` | pytest suite; `conftest.py` has a small test map |
| `docs/logo/make_logo.py` | Regenerates `docs/logo/ashen_vault.svg` |

## Conventions

- Python 3.11+ syntax; ruff settings in `pyproject.toml` (line length 110, double quotes).
- Use `util.rround` (round half away from zero) instead of built-in `round` in game math. The code was
  ported from Ruby and its numbers depend on that rounding.
- Keep new logic in the raylib-free packages where possible and add tests for it. `world/world.py`
  is pure but still mostly untested, which makes it a good place to add coverage.
- Internal resolution is 320x240 (`screen.py`); UI coordinates are in that space.
- Map grids are whitespace-sensitive. Don't reformat `.map` files. Each grid character is one 2 m tile;
  an `[entities]` marker places a prop, enemy or hazard there, standing on the legend tile named by
  `on=` (the map's `default` otherwise). Wall props (torches, banners, shackles, racks) hang on the
  adjacent wall and chests/altars turn to face the open side automatically, so they rarely need `yaw=`.
- Floor legend entries can add hazards: `hurt=<hp per tick>` (thorns), `flow=<dx>,<dz>` (a current),
  `slow=<multiplier>` (mud), `pit` (a hole you can walk into; you fall, are hurt and hauled out) and
  `chasm` (only a raft, plank or ledge lets you onto it). Drops over 1.8 m cost HP, except into a `pit`.
  Terrain entities: `raft to=tx,tz speed= phase=`, `plank`, `ledge deck=`, `boards deck=` (rotten
  floorboards that break for good), `log_chute to=tx,tz every= speed= logs=` (a log rack that only
  releases while someone climbs its slope) and `spore_pod every=`.
- Enemy behaviour flags in `ai/enemy_types.py`: `ambush` spawns dormant (the chest Mimic) until woken;
  `lurk` sits still until you come close (the Stump Mimic); `once` stays dead; bosses set `dead_flag`
  and drop a relic, and pick special attacks from `moves` (see `MOVES` in `ai/enemy.py`: `sweep`,
  `web`, `pounce`, `cinders`). An enemy entity's `item=` is loot it drops when slain.
- An enemy type's `height` is the top of its body as it dies: the ash dissolve crumbles that span.
  Every model has a death pose (eased by `models.death_fall`); `tests/test_render_logic.py` checks
  that each one collapses, stays above the floor and fits its `height`, so update both together.
- Props that fill their tile are listed in `world/world.py` (`BLOCKING_PROPS`, `BREAKABLE_PROPS`).
  Breakables (`barrel`, `crate`, `urn`, `cocoon`) spill loot from `world/loot.py`; a `secret_wall`
  dissolves when struck (`model=vines top=6` matches the jungle's vine walls).
  After placing props in `sunken_keep.map`, run `tests/test_world.py`: its reachability test fails if
  anything cuts off a chest, door, lever, exit, altar or the iron maiden. `verdant_hollow.map` has its
  own solvability test (counting planks, ledges and floorboards as footing, and decor as solid): every
  chest and the boss must be reachable, and every drop must have a way back.
- `game.message()` text may wrap spans in braces, e.g. `f"Obtained {{{item.name}}}."`: the HUD draws
  them in the highlight colour (`util.highlight_runs`). `tests/test_ui_logic.py` checks the small font
  has a glyph for every character used in game messages and names.
- Praying at a shrine plays the `rest` scene; it heals, respawns normal enemies and saves while the fog
  covers the screen. Dying keeps everything the player carries and every flag: you wake at the last
  shrine (`Game._wake_at_shrine`) and only normal enemies (and a living boss's HP) come back.
- Persistent world state lives in the save's `flags` set, keyed `<kind>:<map>:<tx>,<tz>` (opened
  chests, broken barrels, revealed walls, slain mimics) or `loot:<key>` for dropped items. Bosses add
  their `dead_flag` (`boss_dead`, `spider_dead`) and relics a `<relic>_taken` flag (`sigil_taken` for
  the Ember Sigil).
- Equipment (`player/inventory.py`): two hand slots (`right` = left mouse button, `left` = right
  button) holding a weapon, a shield, the readied spell (`SPELL`) or nothing (a fist), plus `body` and
  `hands` armor. `two_handed` weapons fill both hands. Items carry a `level` requirement: buying is
  allowed, equipping is not (`Inventory.equip_error`). The first-person arms (`models.weapon_view`)
  take their sleeve and glove looks from `SLEEVES` / `GLOVES`, so new armor needs an entry there.
- Every attack costs ST. A light swing can chain into a quick one (`Player.queue_quick` /
  `chain_quick`); a weapon's `tempo` sets how long its swings take. Attack poses are keyframed in
  `models.MOTIONS` (wind, strike, follow) and the strike lands at the attack's `hit_at`. The
  viewmodel draws without depth testing, so draw what faces the camera last.
- Secret attacks are listed in `weapons.secret()`; performing one adds a `secret:<category>` flag,
  which reveals its name in Belongings and the shop.
- Shops are `dialogue.SHOPS` (Pell's goods, and Corvane's blades in the hut west of the square; Corvane
  won't talk below `CORVANE_LEVEL`).
- Add dependencies with `uv add` (runtime) or `uv add --dev` (tooling), never by hand-editing
  `uv.lock`.

## Git

- Work on the `development` branch; `master` only receives fast-forward merges from it.
- Contributor workflow (PRs to `development`, DCO sign-off) is in CONTRIBUTING.md.
- Commit only when asked. Don't commit `.idea/`, screenshots outside `docs/`, or coverage files.
