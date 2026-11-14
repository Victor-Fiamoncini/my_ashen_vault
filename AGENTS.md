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
  `attack` is the left mouse button (the Primary slot) and `cast` the right one (Secondary): each
  swings, blocks or casts depending on what that slot holds (`Inventory.button_action`); with a
  two-hander `cast` does nothing. `menu` then `slot1` / `slot2` equips the selected Belongings row.
- `--equip right=katana,left=buckler,body=brigandine,hands=iron_gauntlets` (or `primary=` /
  `secondary=` for `right=` / `left=`) starts with that gear (a slot
  set to `none` empties it; `left=spell` readies the spell there, `left=spell:pyre` learns Pyre and
  readies it) and `--level 6` at that level.
- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first.
- Combat rolls are random, so HP in the `smoke:` line can vary between runs. Positions, scenes, flags
  and items are deterministic.
- On Wayland, `GLFW: Error: 65548` warnings are harmless.
- A negative heading must be written `--at=15,7,-90` (with `=`), or argparse reads it as a flag.
- The `smoke:` line includes the player's height (`y=`), handy for checking lifts.
- Useful starts: `--at 4,24,90 --script "wait:0.2 interact wait:4.5 forward:0.6 wait:5"` (call the
  Cistern lift up, step onto its plate and ride down to the Undercroft), `--at=11,26,90 --script
  "strafe_l:0.7 wait:5"` (ride the shrine lift up, which frees it), `--at=13,26,180 --script "wait:0.2
  interact"` (its call lever above, refusing while it is still fastened), `--at=23,13,0 --script "forward:0.7 wait:5"` (the cage lift up to the Warden's Gallery),
  `--at=27,7,-90` (the Butcher in his slaughter hall north of the Gallery),
  `--map harrowmere --at=47,30,0` (the hedged jungle trail; `--at=56,34,-90` its dark end at the cave
  mouth), `--map verdant_hollow`
  (Mossmouth, the dark cave you arrive in), `--at=15,31,180 --equip left=spell:pyre --script "cast"`
  (kindle Mossmouth's cold brazier), `--at=6,41,-90` (the Root Caverns), `--at=32,3,180` (the Canopy
  Walk), `--at=15,20,-90 --script interact` (the barred door, from its wrong side),
  `--at=14,41,-90 --script "interact wait:2.5 strafe_l:2"` (lower the drawbridge and cross),
  `--at=49,12,-90` (the Highland log slope), `--at=15,7,-90` (the Loom Mother),
  `--at=15,7,-90` (the Ashen Warden in his hall), `--map harrowmere --at=28,25,-90 --script "wait:0.2
  interact"` (Odrin's dialogue box, by the Silent Bell), `--map harrowmere --at=25,22,90 --script
  "forward:0.6 interact"` (touch the Silent Bell; `world.INTERACT_REACH` lets you reach it from its plinth), `--map harrowmere --at=6,26,180 --script "forward:2 interact"`
  (Corvane; below `--level 5` they stay silent), `--map harrowmere --at=31,4,-90` (the north road's gate),
  `--map harrowmere --at=22,30,-60` (the Bell Square), `--map harrowmere --at=17,6,180` (the cathedral's nave;
  `--at=6,6,180 --script "wait:0.2 interact"` speaks to the Enthroned), `--map harrowmere --at=7,18,180 --script
  "wait:0.2 interact"` (Brannoc's gift and forge), `--map harrowmere --at=37,20,0` (the sunken well court),
  `--map cinderhold --at=29,52,-90 --script "look_up:0.15"` (the long bridge and the fortress's skyline), `--map cinderhold --at=28,30,180`
  (the postern ledge and its flame jets), `--map cinderhold --at=18,17,180` (the foundry),
  `--map cinderhold --at=5,24,0` (the smelter pits), `--map cinderhold --at=47,3,180 --script interact`
  (the door at the top of the tower stair, into the keep), `--map cinder_keep --at=17,18,180` (the keep's
  great hall), `--map cinder_keep --at=9,6,180 --level 10`
  (the keep's walled roof: the gargoyles wake at once).
- Boss doors: `--map sunken_keep --at=15,11,-90` faces the Warden's great door, `--at=28,10,-116` the
  Butcher's, `--map verdant_hollow --at=15,11,-90` the Loom Mother's, `--map cinder_keep --at=22,5,180`
  the gargoyles'. The fog appears only
  after dying in a sealed arena (or with its `fog:` flag set); `tests/test_arena.py` drives the flow.
- `--level` only sets the level (for equipment requirements); HP and stats stay at level 1, so judge boss
  balance headless (`World` with a `JungleGame`) rather than from a smoke fight.

## Layout

| Path | Contents |
| --- | --- |
| `src/ashen_vault/world/`, `player/`, `ai/`, `save/` | Pure game logic. **No raylib imports here**; covered by `tests/` |
| `src/ashen_vault/render/` | Shaders (`shaders/ps1.*`), procedural textures, mesh builder, matrix rig, models |
| `src/ashen_vault/game.py` | Scenes and the main loop |
| `src/ashen_vault/ui/hud.py` | HUD, menus, dialogue boxes |
| `src/ashen_vault/audio/synth.py` | Synthesized sound effects. Ambient fire (jets, vents, bombs) plays through `World.sfx_near`, which fades it with distance |
| `src/ashen_vault/input.py` | Key bindings and the `--script` driver |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. `harrowmere` (the town, climbing from its harbour past the market and the Bell Square, with the Silent Bell, to the cathedral on the hill where the Enthroned sits; the sunken well court, the trail gap and the north gate lead out), `sunken_keep` (the dungeon below the well, with the Undercroft below its cells and the Warden's Gallery above the boss door, the Butcher's slaughter hall north of it), `verdant_hollow` (the jungle through the cave at the end of the village's east trail: Mossmouth cave, the Root Caverns below the bog, the Canopy Walk to the boss), `cinderhold` (the lava fortress up the north road: the long bridge, the gatehouse and postern, the foundry and the smelter pits below it, the ashworks, the rampart and the tower stair up to the keep), `cinder_keep` (the keep, a map of its own
  behind the door at the top of the tower stair: the postern landing, the great hall, the switchback stair,
  the antechamber's shrine and the walled rooftop where the twin gargoyles perch) |
| `src/ashen_vault/world/sky.py`, `render/sky.py` | Skies (`[meta] sky = overcast\|jungle\|ember`): a gradient dome meeting the fog at the horizon, a sun and halo, drifting cloud banks and an overhead cap, horizon mist; every sky's sun stands at `SUN_AT` (low in the west, as over the town), its disc drawn over the clouds (`sky.sun`) and its halo behind them; dimmed by darkness and the Veil. Built pure in `world/sky.py`, drawn first each frame without fog or depth by `render/sky.py` |
| `src/ashen_vault/world/darkness.py` | Dark tiles: how your light and the fog close in, Lumen and the Veil of Mist |
| `src/ashen_vault/world/doors.py` | One-way doors (`door from=`): which side lifts the bar |
| `src/ashen_vault/world/arena.py` | Boss arenas behind a `door boss=<dead_flag>`: the flood-filled lair, the fight that seals the great door, and the fog (`fog:<map>:<tx>,<tz>`) left after you die in there |
| `src/ashen_vault/player/burden.py` | Equipment load: each item's `mass` against `capacity(STR)` gives a tier (Light / Medium / Heavy / Overloaded) scaling walk speed, ST refill and every ST cost |
| `src/ashen_vault/ui/compare.py` | ATK / DEF / Block / SPL / Load now and after equipping (or taking off) an item or spell: the Belongings stats panel, its slot chooser and the shop show it before you choose |
| `src/ashen_vault/render/bounds.py` | Measures a model without drawing it (a recording GPU); `models.preview_frame` centres and fits every weapon in its preview with it |
| `src/ashen_vault/world/hazards.py` | Dungeon traps: floor spikes, pendulum blades, crumbling floors, flame jets, magma vents (whose bombs are `Eruption`s with an `origin`); the bosses' fire eruptions and slam shockwaves |
| `src/ashen_vault/world/elements.py` | Elements: lightning against `conductive` foes, fire against `fireproof` ones, which weapons burn |
| `src/ashen_vault/render/fortress_props.py` | The Cinderhold's dressing: `gargoyle_statue` (`pose=snarl`; far ones drop their fine carving, `world.DETAIL_RANGE`), `barred_window`, `tool_rack` and `great_window` (wall props; `great_window rise=` hangs high in a wall over the moat, a landmark), `forge_hearth`, `crucible`, `quench_trough`, `ingot_pile`, `slag_heap`, `impaler`, the `battlement` landmark (a crenellated walk on a wall top) and `lava_spout` (`lavafall spout=gargoyle`) |
| `src/ashen_vault/render/forge_models.py` | The Cinderhold's models (golem, bowman, hound, the gargoyles, Stormbrand and Slagbreaker, arrows, thunder and motes, flame jets, and the skyline: spires, bastions, smokestacks, the gatehouse, the keep, lavafalls); `models` imports it last and borrows its helpers |
| `src/ashen_vault/render/town_models.py` | Harrowmere's models: gabled `roof`s (one per building, on its NW wall tile with `span=W,D ridge=x\|z`), the `silent_bell`, the `cathedral_spire`, pews, windows, beds, cupboards, shelves, hearths, market stalls, fences, lamp posts and boats |
| `src/ashen_vault/world/villagers.py` | How each villager looks (`Look`: build, garb, hair, hat, beard, apron, cloak, held tool, idle) |
| `src/ashen_vault/render/shapes.py` | Model primitives raylib lacks (`blade`, `lozenge`, `wedge`) as pure triangle lists; `Gpu.primitive` uploads them |
| `src/ashen_vault/world/terrain.py` | Terrain: rafts, planks, ledges, rotten floorboards, chain lifts (pressure plate, call levers, `summon`), currents, thorns, chasm and river falls, hard landings, the log rack, spore pods (`World.terrain`) |
| `src/ashen_vault/world/rest.py` | The shrine rest: timing and the pixelated ember fog pattern drawn while you pray |
| `src/ashen_vault/ui/smallfont.py` | The small mixed-case pixel font for all game text: menus, dialogue, messages, prompts and the boss bar (`hud.text` draws with it) |
| `src/ashen_vault/ui/tinyfont.py` | The HUD's tiny fonts: 3x5 `GLYPHS` (the HP/MP/ST labels and numbers, `hud.tiny`) and 3x4 `MICRO` (the HUD mouse's PRI / SEC labels and the quick item's count, `hud.micro_centered`; only the characters they use) |
| `src/ashen_vault/ui/tally.py` | `GoldTally`: the top-right gold counter's bookkeeping (a gain lingers as "+N", then rolls in; spending shows at once). `Game.update` feeds it |
| `src/ashen_vault/ui/logofont.py` | The logo's 5x7 capitals, shared by `docs/logo/make_logo.py` and big headings (`hud.big`: the title, the death screen) |
| `src/ashen_vault/ui/belongings.py` | Belongings as data: its tabs, slot marks, the Equipped panel and the slot chooser (Primary / Secondary) |
| `src/ashen_vault/player/weapons.py` | Weapon categories, light/heavy/quick attacks, swing tempo and the secret attacks (`secret()`) |
| `src/ashen_vault/world/shots.py` | Shots in 3D: spells follow the view's pitch, enemy shots aim at your chest, and a shot only hits a body it passes through |
| `src/ashen_vault/player/guard.py` | Shield blocking: what a raised shield stops and what it costs in ST |
| `src/ashen_vault/world/relics.py` | Boss relics (Ember, Verdant and Iron Sigils), their drop/taken flags, `boss_falls` (twins fall together) and the three-sigil ending |
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
  shortcuts), with a `JungleGame` that also applies damage to enemies, and `tests/test_cinderhold_world.py`
  for the fortress (lava, jets, vents, sound falloff, elements, motes, and the twins on the keep's roof,
  `hold(..., map_name="cinder_keep")`).
- Internal resolution is 320x240 (`screen.py`); UI coordinates are in that space.
- Map grids are whitespace-sensitive. Don't reformat `.map` files. Each grid character is one 2 m tile;
  an `[entities]` marker places a prop, enemy or hazard there, standing on the legend tile named by
  `on=` (the map's `default` otherwise). With `entity_floor = auto` in `[meta]` (the keep uses it), a
  marker without `on=` stands on the floor most of its neighbours share, so one marker serves every
  level. The jungle uses it too; it ran out of ASCII markers, so a few of its markers are Latin-1
  letters (`À`, `Ñ`...). Wall props (torches, banners, shackles, racks) hang on the
  adjacent wall and chests/altars turn to face the open side automatically, so they rarely need `yaw=`.
  A chest (and the chest mimic) with a wall behind it sits back against that wall (`TileMap.seated`,
  `tests/test_seating.py`), so place chests beside a wall.
- Floor legend entries can add hazards: `hurt=<hp per tick>` (thorns), `flow=<dx>,<dz>` (a current),
  `slow=<multiplier>` (mud), `pit` (a hole you can walk into; you fall, are hurt and hauled out), `lava` (a
  pit that sears `LAVA_SHARE` of your max HP the moment you touch it and hauls you out; give it
  `tex=lava`) and `chasm` (only a raft, plank or ledge lets you onto it). Floors with `tex=lava` are drawn
  at full brightness and light their shores (`mesh_builder.lava_lights`), chasms included. Drops over
  1.8 m cost HP, except into a `pit`.
  Any tile may add `dark=<0..1>`: the share of the map's ambient light it loses. Lights still shine
  there, and standing in one shrinks your own light and pulls the fog in (`world/darkness.py`);
  Lumen pushes both back.
  Terrain entities: `raft to=tx,tz speed= phase=`, `plank`, `ledge deck=`, `boards deck=` (rotten
  floorboards that break for good), `lift top= [start=top] [locked] [speed=] [model=cage]` (a chain lift:
  its tile is a `chasm` shaft whose floor is the bottom stop and whose `ceil` clears `top`. It works
  like Dark Souls': stepping onto the pressure plate in the middle of its deck (`terrain.PLATE_R`)
  sends it to the other end (step off the plate and on again to go back), and a call lever that
  `World` places on every landing (`terrain.call_spots`, prop `lift_call`) brings it. A `locked`
  lift is a one-way shortcut: it rests at its `start` end, the end you reach first, its call levers
  refuse until its first ride, which frees it for good (`lift:<map>:<tx>,<tz>` flag). `model=cage`
  draws the keep's barred jail cage, open on the sides that face a landing (`terrain.lift_doors`)),
  `bridge lever=id hinge=n|s|e|w deck=` (a drawbridge standing raised on its hinge side until its
  lever lets it down, for good), `log_chute to=tx,tz every= speed= logs=` (a log rack that only
  releases while someone climbs its slope) and `spore_pod every=`.
  Hazard entities: `spikes`, `pendulum`, `crumble`, `flame_jet dir=n|s|e|w len= every= phase=` (a
  nozzle on the wall behind its tile firing `len` tiles along `dir`) and `magma_vent radius= every=
  count= phase=` (stands in a lava chasm; lobs bombs at open-sky solid ground within `radius` metres,
  the first at you).
  `[meta]` may set `model_range`: metres beyond which small models stop being drawn, short of the fog's
  end, on a map that sees far, and `indoor_range` a shorter one while you stand under a ceiling (the far
  rooms are walled off). Props wholly behind the eye are never drawn (`world.behind_view`).
  A wall standing behind a lower one (a curtain wall behind its cliff, a tower behind its parapet) is
  built where it rises above it (`MeshBuilder._exposed_walls`), so a tall wall can back a low one.
  `LANDMARKS` (`spire`, `keep`, `bastion`, `smokestack`, `gatehouse`, `lavafall`, `battlement`) are
  drawn out to the fog. They stand on tiles no one reaches (wall tops, the moat)
  or above a passage's roof (`bastion base=`, `gatehouse`), and no two Cinderhold towers share a shape
  (`test_cinderhold_skyline_has_no_two_towers_alike_and_stands_out_of_reach`).
- Enemy behaviour flags in `ai/enemy_types.py`: `ambush` spawns dormant (the chest Mimic) until woken;
  `lurk` sits still until you come close (the Stump Mimic, the Bone Crawler); `once` stays dead;
  bosses set `dead_flag` and drop a relic (the Butcher, a mini-boss, sets `butcher_dead` but has no
  relic: his cleaver is an entity `item=`). Any type picks special attacks from `moves` (see `MOVES` in
  `ai/enemy.py`: `sweep`, `web`, `pounce`, `cinders`, `combo`, `slam`, `eruption`, `hook`, `breath`
  (a line of `Eruption`s raking toward you and past), `dive` (a swoop through where you stood)). At half
  HP a boss with a `brood` calls it and one with a `rage` kindles it (the Warden's burning blade);
  either way it enters its second phase (`Enemy.phase2`), fights faster and adds its `phase_moves`.
  `perch` spawns a statue (`Enemy.perched`) that wakes when it sees you, or is struck. `twin=<type>`
  pairs two bosses: waking one wakes the other (`World.rouse_twin`), they take turns with special moves
  (`World.twin_busy`), the survivor enters phase two when the other falls (not at half HP), they share a
  `dead_flag` and relic set only when both are dead (`relics.boss_falls`), and a shrine rest brings a
  fallen twin back beside its living other at full HP. `conductive` foes take `LIGHTNING_MULT` from
  lightning and are jolted (`staggers`); `fireproof` ones take half from fire and never burn. `shot=arrow`
  draws a ranged foe's shots as arrows (and they fly faster).
  An enemy entity's `item=` is loot it drops when slain. `flammable` types (the jungle's plants) take
  more from Pyre and keep burning. Enemies carry lingering harm in `Enemy.status` (`poison` from Venom
  Dart, `burn` from Pyre), one bite a second (`status_tick`) that never staggers.
- An enemy type's `height` is the top of its body as it dies: the ash dissolve crumbles that span.
  Every model has a death pose (eased by `models.death_fall`); `tests/test_render_logic.py` checks
  that each one collapses, stays above the floor and fits its `height`, so update both together.
  Its `tall` is the top of the standing body: a spell bolt flying higher misses it (`world/shots.py`).
  Bosses must stay boss-sized in detail (at least 50 parts, 30 for armed and armoured regulars) and
  look different in their second phase (`test_bosses_have_boss_level_detail`,
  `test_phase_two_changes_how_each_boss_looks`), and every glow goes out in death.
- Foes that wield a weapon chop overhead (`models.chop_angle`) and hold it in a fist (`models.held`,
  `sword_parts`): give the arm an elbow (`elbow_bend`) and point the weapon with
  `aim_wrist(blade_direction, shoulder + elbow)` rather than a fixed angle, so it never folds back along
  the arm. `tests/test_render_logic.py` checks the wrist stays within 150 degrees of the forearm's line.
- Props that fill their tile are listed in `world/world.py` (`BLOCKING_PROPS`, `BREAKABLE_PROPS`;
  the keep adds `pillar`, `sarcophagus` and `headsman_block`, the jungle `bonfire`, `giant_mushroom` and
  `totem`, the town `pew`, `bed`, `cupboard`, `stall`, `fence` and `lamp_post`). Decor that blocks nothing:
  `boat` rides on water, `shelf`, `hearth` and `window` hang on a wall (the last two are lights), `cage`, `roots` and `meat_hooks` hang from the ceiling, `grate` sits in the
  floor, `mushrooms` dot it, and `cobweb`, `skull_niche`, `winch`, `lever` and `shelf_fungus` mount on
  the nearest wall (`WALL_PROPS`). `lever model=wood` is the jungle's wooden lever.
  Light comes from `mesh_builder.LIGHT_KINDS` (torches, braziers, fungus, bonfires, the glowing
  toadstools). A `brazier unlit` or `bonfire unlit` stays cold until Pyre or a Flame Bolt kindles it
  (`World.kindle`); it then burns for good under a `lit:<map>:<tx>,<tz>` flag, and its light is added
  to the baked mesh in place (`MeshBuilder.add_light`).
  `chest model=iron` is the Cinderhold's iron chest (`models.chest` style), and `mimic model=iron` hides as
  one (`Enemy.look`). An `exit` with `boss=<dead_flag>` is a way on to a boss on another map: the compass
  points at it while that boss lives (`World.boss_target`).
  Breakables (`barrel`, `crate`, `urn`, `cocoon`) spill loot from `world/loot.py` (`loot.roll`); a `secret_wall`
  dissolves when struck (`model=vines top=6` matches the jungle's vine walls; `model=web` is a sheet of
  silk that blades can't cut and only fire burns). `door boss=<dead_flag>` is a boss's great door
  (`models.boss_door`, dressed for its boss by `BOSS_DOORS` / `DOOR_ARCHES` / `DOOR_LEAVES`, keyed by
  the `dead_flag`; a new boss door needs an entry in each): the arena behind it seals once you are inside with its boss awake, opens when
  the boss dies, and after you die in there becomes a fog gate (`models.fog_gate`) the boss walks
  through freely and you cross with interact. Each arena must stay closed behind its one door
  (`tests/test_arena.py`). `door from=n|s|e|w` is barred on that side: it
  only opens from there. `door model=iron` is the Cinderhold's riveted iron door, set in a stone frame
  that rises to the passage's ceiling (`world.DOOR_FRAME_SKY` under the open sky).
  After placing props in `sunken_keep.map`, run `tests/test_world.py`: its reachability test fails if
  anything cuts off a chest, door, lever, exit, altar or the iron maiden, or if a locked lift is
  needed to get anywhere (shortcuts must stay optional). `verdant_hollow.map` has its
  own solvability test (counting planks, ledges and floorboards as footing, and decor as solid): every
  chest, lever and the boss must be reachable without barred doors, locked lifts or drawbridges, each
  of those must join two places already reachable, and every drop must have a way back.
  `cinderhold.map` has one too (`test_cinderhold_is_solvable`, lava counted as impassable), and so does
  `cinder_keep.map` (`test_cinder_keep_is_solvable`; `test_cinder_keep_roof_is_walled_in` keeps every wall
  round the rooftop at least 6 m above it). Their tiles are lowercase letters, digits and punctuation and
  their entity markers uppercase or Latin-1, so the two never collide; keep it that way.
- `game.message()` text may wrap spans in braces, e.g. `f"Obtained {{{item.name}}}."`: the HUD draws
  them in the highlight colour (`util.highlight_runs`). `tests/test_ui_logic.py` checks the small font
  has a glyph for every character used in game messages and names.
- Praying at a shrine plays the `rest` scene; it heals, respawns normal enemies and saves while the fog
  covers the screen. Dying keeps everything the player carries and every flag: you wake at the last
  shrine (`Game._wake_at_shrine`) and only normal enemies (and a living boss's HP) come back.
- Persistent world state lives in the save's `flags` set, keyed `<kind>:<map>:<tx>,<tz>` (opened
  chests, broken barrels, revealed walls, slain mimics, kindled fires as `lit:`) or `loot:<key>` for
  dropped items. Bosses add
  their `dead_flag` (`boss_dead`, `spider_dead`, `gargoyles_dead`, `butcher_dead`) and relics a `<relic>_taken` flag
  (`sigil_taken` for the Ember Sigil).
- Equipment (`player/inventory.py`): two hand slots, shown to players as **Primary** (`right` = left
  mouse button) and **Secondary** (`left` = right button) via `SLOT_NAMES`; never say "hand" in text the
  player sees. Each holds a weapon, a shield, the readied spell (`SPELL`) or nothing (a fist), plus
  `body` and `hands` armor. `two_handed` weapons fill both slots and swing from Primary only. The HUD
  draws the slots on a mouse in the bottom right (`hud.mouse_hud`: Primary on its left button, Secondary
  on its right, the quick item on the wheel). HUD spacing comes from `HUD_MARGIN` (screen edge),
  `HUD_PAD` (inside a box) and `HUD_GAP` (between elements); derive new positions from them. Every
  box and window is `hud.hud_box` (or `panel`), drawn in whole pixels with `HUD_RADIUS` corners
  (`HUD_INNER_RADIUS` for a well inside a box); never pass another radius
  (`test_every_hud_box_shares_the_named_corner_radii`). The
  compass marks the nearest great door whose boss lives (`World.boss_bearing`). A mouse action must never share a name with
  a movement key (`tests/test_input.py`): `"back"` once did, and a raised shield walked you backward. Items carry a `level` requirement: buying is
  allowed, equipping is not (`Inventory.equip_error`). The first-person arms (`models.weapon_view`)
  take their sleeve and glove looks from `SLEEVES` / `GLOVES`, so new armor needs an entry there; a new
  shield needs its strap in `models.SHIELD_GRIPS`, where the fist closes (drawn after the shield, so a
  raised shield shows the hand).
- Weapons, shields and armor carry a `mass` (kg). Their total sets the player's load tier
  (`player/burden.py`, `Player.burden`): heavier gear walks slower, refills ST slower and pays more ST
  for attacks, sprinting and blocking. New gear needs a `mass` (`tests/test_burden.py`).
- Belongings is split into tabs (`belongings.TABS`: Items, Weapons, Armor, Spells, Unique), switched
  with `tab_prev` / `tab_next` (A / D, Left / Right) or a click; `tab_of` files each item kind.
- Shots stop at a blocking prop only below its top (`world.PROP_TOP`, `shots.clears`): a bolt flies
  over tables, caskets and barrels. A low prop not listed there counts as full height.
- Every attack costs ST. Each category's moveset (`weapons.MOVESETS`) is tuned for a medium weapon;
  an item's `weight` (`light` / `medium` / `heavy` / `great`) scales each attack's ST, damage and poise
  through `weapons.WEIGHTS` (`weapons.attack` returns the sized Attack) and adds `WEIGHT_TEMPO` to its
  `tempo`, which sets how long its swings take. The quick attack is a double-click: a second click
  within `weapons.DOUBLE_CLICK` of a light swing's start calls it off (refunding its ST) and starts the
  quick one (`Player.double_strike`), or queues it if the blow already landed (`chain_quick`). In a
  smoke run that is `attack wait:0.1 attack`. Quick moves that strike twice use `pulses` with a short
  `pulse_gap`. Attack poses are keyframed in `models.MOTIONS` (wind, strike, follow, each
  `(dx, dy, dz, rx, ry, rz)`), the strike lands at the attack's `hit_at`, and edged weapons (`TRAILS`)
  smear a fan of ghost blades through the blow. The viewmodel draws without depth testing, so draw
  what faces the camera last.
- Besides raylib's cube, sphere, cyl, cone and quad, models can draw `blade` (a lozenge-section slab
  that comes to a point), `lozenge` (the same section, straight) and `wedge` (a triangular prism),
  generated in `render/shapes.py`. Straight swords, the player's and the foes', are `models.blade_parts`
  (guard styles, pommels, ricasso, fuller, bevelled edges). Axe, cleaver and hammer heads are built with
  their edge or face on +Z and `models.weapon` turns those in `HEADED` a quarter so it leads along +X,
  the way swings travel (`test_axe_and_hammer_heads_lead_their_blows`; the jungle's Heartwood Maul
  is one). Keys and relic sigils draw from
  `KEY_STYLES` / `SIGILS` (each key its own shape in `KEY_SHAPES`), in Belongings and on the ground (`models.pickup`). Enemy anatomy has helpers too: `skull`,
  `ribcage`, `hand`, `sack_hood` and `_bar` (a box between two points).
- Secret attacks are listed in `weapons.secret()`; performing one adds a `secret:<category>` flag,
  which reveals its name in Belongings and the shop.
- Weapons may carry an `element` (`"lightning"`, `"fire"`): `Game._strike` multiplies by
  `elements.mult` and a fire weapon leaves `burn` on what it hits.
- Each weapon has its own small, animated glyph on the HUD mouse (`hud.WEAPON_ICONS`, keyed by item id,
  within `ICON_REACH` of the button's centre); a new weapon needs one, unlike any other
  (`test_weapon_icons_all_look_different_and_fit_their_button`).
- Spells are `player/spells.py` (`Spells.ALL`, their formulas) and are taught by `scroll_<id>` items;
  `Game._cast_spell` dispatches them. Venom Dart and Flame Bolt are bolts (`World.fire_bolt` with an
  `effect`; Thunder Spear is a fast `effect="thunder"` bolt), Arcane Motes are three `homing`
  projectiles (`World.motes`, steered by `shots.home`), Pyre is a short cone (`World.pyre`)
  drawn as a `Gout` of flame plus sparks, Veil of Mist sets `Player.veil_t` (ordinary foes then
  notice you only very close; striking or casting anything else lifts it), Lumen sets `lumen_t`, and Ashen
  Ward sets `ward_t` (`Game.hurt_player` passes every blow through `Spells.warded`; embers circle the view
  and the vitals box's trim glows). A spell's
  `recovery` is how long the magic gauge takes to refill after it (Pyre's is short). A new
  spell also needs a HUD icon (`hud.spell_icon`), colours in `models.SPELL_GLOW` / `SPELL_ORB`, and its
  scroll's parchment, rods and wax in `models.SCROLLS` with a rune in `models.SCROLL_RUNES` (no two alike).
- Shops are `dialogue.SHOPS`: Brannoc's forged steel and armour, Pell's scrolls and salvage, Tamsin's remedies,
  and Corvane's blades in the hut on the town's west edge (Corvane won't talk below `CORVANE_LEVEL`).
  Villagers in `dialogue.GIFTS` hand a newcomer something once (`gift:<id>` flag) and then open their shop,
  if they keep one. Shops hide gear you own; a chest, pickup or gift holding gear or a scroll you already
  own pays gold instead (`loot.claim`). No spell scroll, gear or key may be placed twice across maps and
  gifts (`tests/test_loot.py`): give a new find a new item.
- Villagers are drawn by `models.npc` from a `world/villagers.Look` (build, clothes, hair, hat, held tool,
  idle); a new villager needs an entry in `villagers.LOOKS`. The Enthroned (`npc id=enthroned`) is its own
  model, petrified on `models.throne`: all stone, nothing glows but the drifting dust, and their lines
  whisper from the stone (`dialogue.ENTHRONED_LINES`; the lore is a TODO).
- Add dependencies with `uv add` (runtime) or `uv add --dev` (tooling), never by hand-editing
  `uv.lock`.

## Git

- Work on the `development` branch; `master` only receives fast-forward merges from it.
- Contributor workflow (PRs to `development`, DCO sign-off) is in CONTRIBUTING.md.
- Commit only when asked. Don't commit `.idea/`, screenshots outside `docs/`, or coverage files.
- The README screenshots show the HUD and fonts: after changing either, retake them with the commands
  listed under README's Debug flags (each with a throwaway `ASHEN_VAULT_SAVE`).
