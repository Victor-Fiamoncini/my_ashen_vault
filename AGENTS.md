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
  the keys of `KEYS` and `MOUSE` in `src/ashen_vault/input.py`, plus `wheel_up` / `wheel_down` and
  `look_up` / `look_down` (hold them to tilt the view, 1.5 rad/s).
  `attack` is the left mouse button (the right hand) and `cast` the right one (the left hand): each
  swings, blocks or casts depending on what that hand holds.
- `--equip right=katana,left=buckler,body=brigandine,hands=iron_gauntlets` starts with that gear (a slot
  set to `none` empties it; `left=spell` readies the spell there, `left=spell:pyre` learns Pyre and
  readies it) and `--level 6` at that level.
- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first.
- Combat rolls are random, so HP in the `smoke:` line can vary between runs. Positions, scenes, flags
  and items are deterministic.
- On Wayland, `GLFW: Error: 65548` warnings are harmless.
- A negative heading must be written `--at=15,7,-90` (with `=`), or argparse reads it as a flag.
- The `smoke:` line includes the player's height (`y=`), handy for checking lifts.
- Useful starts: `--at 4,24,90 --script "forward:0.9 wait:5 forward:0.6"` (the Cistern lift down to
  the Undercroft), `--at=11,26,90 --script "interact strafe_l:0.7 wait:5"` (free the shrine lift and
  ride it up), `--at=23,13,0 --script "forward:0.7 wait:5"` (the lift up to the Warden's Gallery),
  `--map harrowmere --at 40,14,0` (the jungle trail and its cave mouth), `--map verdant_hollow`
  (Mossmouth, the dark cave you arrive in), `--at=15,31,180 --equip left=spell:pyre --script "cast"`
  (kindle Mossmouth's cold brazier), `--at=6,41,-90` (the Root Caverns), `--at=32,3,180` (the Canopy
  Walk), `--at=15,20,-90 --script interact` (the barred door, from its wrong side),
  `--at=14,41,-90 --script "interact wait:2.5 strafe_l:2"` (lower the drawbridge and cross),
  `--at=49,12,-90` (the Highland log slope), `--at=15,7,-90` (the Loom Mother),
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
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. `harrowmere` (the village), `sunken_keep` (the dungeon below the well, with the Undercroft below its cells and the Warden's Gallery above the boss door), `verdant_hollow` (the jungle through the cave at the end of the village's east trail: Mossmouth cave, the Root Caverns below the bog, the Canopy Walk to the boss) |
| `src/ashen_vault/world/darkness.py` | Dark tiles: how your light and the fog close in, Lumen and the Veil of Mist |
| `src/ashen_vault/world/doors.py` | One-way doors (`door from=`): which side lifts the bar |
| `src/ashen_vault/world/hazards.py` | Dungeon traps: floor spikes, pendulum blades, crumbling floors; the Warden's fire eruptions and slam shockwaves |
| `src/ashen_vault/world/terrain.py` | Terrain: rafts, planks, ledges, rotten floorboards, chain lifts, currents, thorns, chasm and river falls, hard landings, the log rack, spore pods (`World.terrain`) |
| `src/ashen_vault/world/rest.py` | The shrine rest: timing and the pixelated ember fog pattern drawn while you pray |
| `src/ashen_vault/ui/smallfont.py` | The small mixed-case pixel font used for in-game messages, prompts and the boss bar |
| `src/ashen_vault/player/weapons.py` | Weapon categories, light/heavy/quick attacks, swing tempo and the secret attacks (`secret()`) |
| `src/ashen_vault/world/shots.py` | Shots in 3D: spells follow the view's pitch, enemy shots aim at your chest, and a shot only hits a body it passes through |
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
  is pure but still mostly untested, which makes it a good place to add coverage:
  `tests/test_keep_world.py` builds a real `World` headless with a `FakeGame` (a no-op GPU that records
  messages, sounds and wounds), so world logic can be driven without a window.
  `tests/test_verdant_world.py` does the same for the jungle (spells, kindled fires, darkness,
  shortcuts), with a `JungleGame` that also applies damage to enemies.
- Internal resolution is 320x240 (`screen.py`); UI coordinates are in that space.
- Map grids are whitespace-sensitive. Don't reformat `.map` files. Each grid character is one 2 m tile;
  an `[entities]` marker places a prop, enemy or hazard there, standing on the legend tile named by
  `on=` (the map's `default` otherwise). With `entity_floor = auto` in `[meta]` (the keep uses it), a
  marker without `on=` stands on the floor most of its neighbours share, so one marker serves every
  level. The jungle uses it too; it ran out of ASCII markers, so a few of its markers are Latin-1
  letters (`À`, `Ñ`...). Wall props (torches, banners, shackles, racks) hang on the
  adjacent wall and chests/altars turn to face the open side automatically, so they rarely need `yaw=`.
- Floor legend entries can add hazards: `hurt=<hp per tick>` (thorns), `flow=<dx>,<dz>` (a current),
  `slow=<multiplier>` (mud), `pit` (a hole you can walk into; you fall, are hurt and hauled out) and
  `chasm` (only a raft, plank or ledge lets you onto it). Drops over 1.8 m cost HP, except into a `pit`.
  Any tile may add `dark=<0..1>`: the share of the map's ambient light it loses. Lights still shine
  there, and standing in one shrinks your own light and pulls the fog in (`world/darkness.py`);
  Lumen pushes both back.
  Terrain entities: `raft to=tx,tz speed= phase=`, `plank`, `ledge deck=`, `boards deck=` (rotten
  floorboards that break for good), `lift top= [start=top] [lever=id] [speed=]` (a chain lift: its
  tile is a `chasm` shaft whose floor is the bottom stop and whose `ceil` clears `top`; it carries
  whoever stands on it to the other end, and comes when someone waits at a landing. With `lever=` it
  stays chained until the matching lever is pulled, a shortcut opened from one side),
  `bridge lever=id hinge=n|s|e|w deck=` (a drawbridge standing raised on its hinge side until its
  lever lets it down, for good), `log_chute to=tx,tz every= speed= logs=` (a log rack that only
  releases while someone climbs its slope) and `spore_pod every=`.
- Enemy behaviour flags in `ai/enemy_types.py`: `ambush` spawns dormant (the chest Mimic) until woken;
  `lurk` sits still until you come close (the Stump Mimic, the Bone Crawler); `once` stays dead;
  bosses set `dead_flag` and drop a relic. Any type picks special attacks from `moves` (see `MOVES` in
  `ai/enemy.py`: `sweep`, `web`, `pounce`, `cinders`, `combo`, `slam`, `eruption`, `hook`). At half
  HP a boss with a `brood` calls it and one with a `rage` kindles it (the Warden's burning blade);
  either way it enters its second phase (`Enemy.phase2`), fights faster and adds its `phase_moves`.
  An enemy entity's `item=` is loot it drops when slain. `flammable` types (the jungle's plants) take
  more from Pyre and keep burning. Enemies carry lingering harm in `Enemy.status` (`poison` from Venom
  Dart, `burn` from Pyre), one bite a second (`status_tick`) that never staggers.
- An enemy type's `height` is the top of its body as it dies: the ash dissolve crumbles that span.
  Every model has a death pose (eased by `models.death_fall`); `tests/test_render_logic.py` checks
  that each one collapses, stays above the floor and fits its `height`, so update both together.
  Its `tall` is the top of the standing body: a spell bolt flying higher misses it (`world/shots.py`).
- Props that fill their tile are listed in `world/world.py` (`BLOCKING_PROPS`, `BREAKABLE_PROPS`;
  the keep adds `pillar`, `sarcophagus` and `bell`, the jungle `bonfire`, `giant_mushroom` and
  `totem`). Decor that blocks nothing: `cage` and `roots` hang from the ceiling, `grate` sits in the
  floor, `mushrooms` dot it, and `cobweb`, `skull_niche`, `winch`, `lever` and `shelf_fungus` mount on
  the nearest wall (`WALL_PROPS`). `lever model=wood` is the jungle's wooden lever.
  Light comes from `mesh_builder.LIGHT_KINDS` (torches, braziers, fungus, bonfires, the glowing
  toadstools). A `brazier unlit` or `bonfire unlit` stays cold until Pyre or a Flame Bolt kindles it
  (`World.kindle`); it then burns for good under a `lit:<map>:<tx>,<tz>` flag, and its light is added
  to the baked mesh in place (`MeshBuilder.add_light`).
  Breakables (`barrel`, `crate`, `urn`, `cocoon`) spill loot from `world/loot.py`; a `secret_wall`
  dissolves when struck (`model=vines top=6` matches the jungle's vine walls; `model=web` is a sheet of
  silk that blades can't cut and only fire burns). `door from=n|s|e|w` is barred on that side: it
  only opens from there.
  After placing props in `sunken_keep.map`, run `tests/test_world.py`: its reachability test fails if
  anything cuts off a chest, door, lever, exit, altar or the iron maiden, or if a chained lift is
  needed to get anywhere (shortcuts must stay optional). `verdant_hollow.map` has its
  own solvability test (counting planks, ledges and floorboards as footing, and decor as solid): every
  chest, lever and the boss must be reachable without barred doors, chained lifts or drawbridges, each
  of those must join two places already reachable, and every drop must have a way back.
- `game.message()` text may wrap spans in braces, e.g. `f"Obtained {{{item.name}}}."`: the HUD draws
  them in the highlight colour (`util.highlight_runs`). `tests/test_ui_logic.py` checks the small font
  has a glyph for every character used in game messages and names.
- Praying at a shrine plays the `rest` scene; it heals, respawns normal enemies and saves while the fog
  covers the screen. Dying keeps everything the player carries and every flag: you wake at the last
  shrine (`Game._wake_at_shrine`) and only normal enemies (and a living boss's HP) come back.
- Persistent world state lives in the save's `flags` set, keyed `<kind>:<map>:<tx>,<tz>` (opened
  chests, broken barrels, revealed walls, slain mimics, kindled fires as `lit:`) or `loot:<key>` for
  dropped items. Bosses add
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
- Spells are `player/spells.py` (`Spells.ALL`, their formulas) and are taught by `scroll_<id>` items;
  `Game._cast_spell` dispatches them. Venom Dart and Flame Bolt are bolts (`World.fire_bolt` with an
  `effect`), Pyre is a short cone (`World.pyre`), Veil of Mist sets `Player.veil_t` (ordinary foes then
  notice you only very close; striking or casting anything else lifts it), Lumen sets `lumen_t`. A new
  spell also needs a HUD icon (`hud.spell_icon`) and colours in `models.SPELL_GLOW` / `SPELL_ORB`.
- Shops are `dialogue.SHOPS` (Pell's goods, and Corvane's blades in the hut west of the square; Corvane
  won't talk below `CORVANE_LEVEL`).
- Add dependencies with `uv add` (runtime) or `uv add --dev` (tooling), never by hand-editing
  `uv.lock`.

## Git

- Work on the `development` branch; `master` only receives fast-forward merges from it.
- Contributor workflow (PRs to `development`, DCO sign-off) is in CONTRIBUTING.md.
- Commit only when asked. Don't commit `.idea/`, screenshots outside `docs/`, or coverage files.
