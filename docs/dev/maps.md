# Maps, terrain and props

How `.map` files work and what can stand on a tile.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. `ashen_cemetery` (the linear first level, the tutorial: the waking grave and its shrine, the lane with the Rusted Sword, the field of headstones, its husks and the Shrouded Mourners bowed at its graves, the chapel with the Flame Bolt's scroll and its silk-sealed far door, the shrine court, and the Sexton's yard with the one-way gate out to the town; walled and floored in its own ash textures, `ash_rock`, `ash_stone`, `ash_brick`, `ash_ground`, `ash_grass`, `ash_flagstone`), `harrowmere` (the walled town of stone and half-timbered houses under steep violet-slate roofs, turrets on their corners and round towers along its wall, thin-walled (`thin=0.5`), paved in cobbles and setts, a canal running up from the harbour, climbing from its harbour past the market's fountain and the Bell Square, with the Silent Bell, to the twin-towered cathedral on the hill where the Enthroned sits; you arrive by the cemetery's gate in its west wall, its `start`; the sunken well court, the trail gap, the north gate and four street grates down into the sewers lead out), `sunken_keep` (the dungeon below the well, with the Undercroft below its cells and the Warden's Gallery above the boss door, the Butcher's slaughter hall north of it), `verdant_hollow` (the jungle through the cave at the end of the village's east trail: Mossmouth cave, the Root Caverns below the bog, the Canopy Walk to the boss), `cinderhold` (the lava fortress up the north road: the long bridge, the gatehouse and postern, the foundry and the smelter pits below it, the ashworks, the rampart and the tower stair up to the keep), `cinder_keep` (the keep, a map of its own
  behind the door at the top of the tower stair: the postern landing, the great hall, the switchback stair,
  the antechamber's shrine and the walled rooftop where the twin gargoyles perch), `harrow_sewers` (the
  sewers under the town, reached by four street grates (`sewer_grate`) that each drop onto the ladder
  (`sewer_ladder`) under them, at the same tile: the North Sluices, the Market Drains (narrow vaulted runs,
  its `start`), the Canal Culvert and the Quay Outfall, all joined through the Cistern and its shrine;
  Mother Gnawl's nest between the Cistern and the outfall, a great door at each of its two mouths (two
  `door boss=matron_dead`: an arena each over the same tiles, sealing, fogging and opening together), and
  8 m down the outfall's U-turn stair the Sump and the Sump Maw's cistern behind its great door. Shortcuts: a barred door down from the sluices, the sluice
  pit's drawbridge and a lift from the Sump up to the Cistern (an 8 m ride). Wadeable `sludge` floors (`slow=`, some with
  `flow=`) hold its drowned and leeches; walled in `sewer_brick` under a `sewer_vault`;
  `test_harrow_sewers_is_solvable`), `vesperholm` (the Moonbound City behind the Vesper Gate in
  Harrowmere's north wall, behind the cathedral's apse: the town's `exit model=vesper_gate
  requires=vesper_gate_open`, shut until the first three sigils are taken (`relics.GATE_FLAG`), leads to
  its `start` in the Gate Court, before the gate home (never shut). Under the `moonlit` sky, a pale
  blue-silver ambient and a fog reaching 84 m: the Gate Court and its shrine, Lantern Square and its
  shallow moon pool, the Landing on the gorge's edge, Lamplighters' Row and a hidden court behind a false
  wall; the gorge (an 18 m `chasm`) between the lower town and the castle, crossed by the Glass Bridge
  (`moon_glass`) at the west street's head into the castle's postern; the bailey, the west chapel and
  the Duchess's garden; the Cathedral of the Long Night, its nave, and behind its great door
  (`door boss=duchess_dead`) the choir floored in moon-glass where Duchess Ilvane waits. Shortcut: the
  castle's drawbridge over the gorge (`bridge hinge=n`), let down by its lever in the bailey, back to the
  Landing. Walled in `moonstone`, paved in `moon_paving`, roofed in `silver_slate`;
  `test_vesperholm_is_solvable`) |
| `src/ashen_vault/world/terrain.py` | Terrain: rafts, planks, ledges, rotten floorboards, chain lifts (pressure plates, call plates, shortcut levers, `summon`), currents, thorns, chasm and river falls, hard landings, the log rack, spore pods (`World.terrain`) |
| `src/ashen_vault/world/hazards.py` | Dungeon traps: floor spikes, pendulum blades, crumbling floors, flame jets, magma vents (whose bombs are `Eruption`s with an `origin`); the bosses' fire eruptions and slam shockwaves |
| `src/ashen_vault/world/thin_walls.py` | Thin walls (`wall ... thin=<m>`): the slab each such tile stands as (hugging the side open to the sky, else a full wall it backs onto, centred between two rooms; a run keeps one line, `test_harrowmere_has_no_slits_between_its_thin_walls`), the margins it lends to its open neighbours (`Layout`), and how far a prop must move back to touch it (`inset`) |
| `src/ashen_vault/world/ramparts.py` | The great walls' dressing: every face of a `dress=rampart` wall turned to open sky-lit ground at least `MIN_HEIGHT` below its top gets a static `rampart_bay` (`town_models.rampart_bay`: a stepped plinth, a corbelled parapet with merlons, and a `pier` of three engaged columns every `PIER_EVERY` tiles and at each run's ends, blind round arches between), kept clear of wall towers, gates (`world.RAMPART_GATES`) and wall props. Nothing stands out past the player's radius, so bays need no collision |
| `src/ashen_vault/world/sea.py` | The open sea (`[meta] open_sea = true`, Harrowmere only): the deep water and its far reaches past the grid's south edge (`far_cells`, bands of cells doubling in size out to `FAR`) go into the mesh builder's own `sea` batch, which `World._draw_sea` draws under a fog `SEA_REACH` times thinner than the land's, so it runs on to the horizon; the sun lays a twinkling path of glints on it (`glitter`, the cut-out `glitter` texture, coloured by `sky.sun_color`) |
| `src/ashen_vault/world/darkness.py` | Dark tiles: how your light and the fog close in, Lumen and the Veil of Mist |
| `src/ashen_vault/world/doors.py` | One-way doors (`door from=`): which side lifts the bar |
| `src/ashen_vault/world/arena.py` | Boss arenas behind a `door boss=<dead_flag>`: the flood-filled lair, the fight that seals the great door, and the fog (`fog:<map>:<tx>,<tz>`) left after you die in there |
| `src/ashen_vault/world/hints.py` | Tutorial hints (`hint text="...\|..."`): shown once, the first time you step onto any of its marker's tiles (`hint:<map>:<marker>` flag); `World._update_hints` fires them |
| `src/ashen_vault/world/footsteps.py` | Footsteps: each floor `tex` belongs to a surface (stone, wood, soft, mud, water, metal, gravel, glass (Vesperholm's `moon_glass`); the platform under you overrides it), and `Game._footstep` plays its `step_<surface>` sound. A new floor texture needs a surface (`tests/test_footsteps.py`) |
| `src/ashen_vault/world/rest.py` | The shrine rest: timing and the pixelated ember fog pattern drawn while you pray |
| `src/ashen_vault/world/sky.py`, `render/sky.py` | Skies (`[meta] sky = overcast\|dusk\|jungle\|ember\|moonlit`): a gradient dome meeting the fog at the horizon, a sun and halo, drifting cloud banks and an overhead cap, horizon mist; every sky's sun stands at `SUN_AT` (low in the south, over the town's sea), but Vesperholm's `moonlit` sky hangs a vast pale moon at `MOON_AT` instead (high in the north, over its cathedral; `Sky.moon` lays its seas on its face, `sky.maria`) among a crowd of stars (`Sky.star_count`), stars glint behind the clouds (`Sky.stars`, their brightness; none in the jungle's daylight), its disc drawn over the clouds (`sky.sun`) and its halo behind them; dimmed by darkness and the Veil. Built pure in `world/sky.py`, drawn first each frame without fog or depth by `render/sky.py` |
| `tools/level_planner/` | A top-down level planner (`index.html`, open it in a browser; a design aid, not part of the game): paint tiles, pin NPCs, gates and wells, export JSON or an ASCII grid. `map_to_planner.py <map>` turns a game map into JSON for its Import box |
| `tools/level_sketch/` | A free-form top-down sketchpad for level design (`index.html`, open it in Chrome; a design aid, not part of the game): shapes, lines and markers measured in metres, on layers, over an optional faint underlay of a game map (`map_to_underlay.py <map>`), saved as `<name>.sketch.json` + `.svg` in `sketches/` for planning a level's rebuild. Its logic is `model.js`, tested with `node --test tools/level_sketch/` (not in CI) |

## Rules

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
  `tex=lava`) and `chasm` (a sheer drop: a raft, plank or ledge carries you over it). No invisible walls:
  the player may walk off into water or a chasm (`Terrain.open_to`; only a lift's cage hanging above
  you shuts its shaft), while foes never step onto either. Water casts you back ashore, hurt, unless the legend marks
  it `deep` (the town's open sea; its canal is not): going in is a drowning (`Terrain._drown`, the
  plunge again, sinking slowly) that kills you within `terrain.DROWN_TIME`; going
  over a chasm's brink is a plunge (`Terrain.plunging`, input locked) that kills you within
  `terrain.PLUNGE_TIME`, unless the chasm floor lies within `FALL_SAFE` of you (an empty shaft's
  bottom, which is only ground). Floors with `tex=lava` are drawn
  at full brightness and light their shores (`mesh_builder.lava_lights`), chasms included. Drops over
  1.8 m cost HP (`FALL_PER_M` a metre), except into a `pit`; a drop of `terrain.FALL_LETHAL` (8 m) kills.
  Any tile may add `dark=<0..1>`: the share of the map's ambient light it loses. Lights still shine
  there, and standing in one shrinks your own light and pulls the fog in (`world/darkness.py`);
  Lumen pushes both back.
  Terrain entities: `raft to=tx,tz speed= phase=`, `plank`, `ledge deck=`, `boards deck=` (rotten
  floorboards that break for good), `lift top= [start=top] [locked] [speed=] [model=cage]` (a chain lift:
  its tile is a `chasm` shaft whose floor is the bottom stop and whose `ceil` clears `top`. It works
  like Dark Souls': stepping onto the pressure plate in the middle of its deck (`terrain.PLATE_R`)
  sends it to the other end (step off the plate and on again to go back), and stepping onto the call
  plate set in each landing's floor just out from the shaft (`Platform.calls`, `terrain.call_plates`)
  brings it. A `locked` lift is a one-way shortcut: it rests at its `start` end, the end you reach
  first; the far landing's call plate ignores you and a lever hung on the wall beside the shaft there
  (`terrain.lever_spot`, prop `lift_call`, the only lift levers) says it is fastened, until its first
  ride frees it for good (`lift:<map>:<tx>,<tz>` flag; the lever then calls it too). Floors a lift
  joins sit far apart (the keep's Undercroft at -10 m, its Gallery at 12 m), so a ride feels like one. `model=cage`
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
  `[meta] roofs = true` (the Cinderhold uses it) closes a map seen from above: every ceilinged tile
  gets a roof (`roof=<h>` in its legend, at least `mesh_builder.ROOF_SLAB` over its ceiling;
  `roof_tex=`), the walls rising past a roof show their faces above it, and every wall tile is capped.
  A passage through a wall is roofed at the wall's height (`roof=16`), so the wall runs on over it.
  A wall tile may set `dress=rampart` (Harrowmere's great walls): carved bays along its open faces
  (`world/ramparts.py`).
  A wall tile may set `thin=<m>` (the town's houses use 0.5): it stands as a slab that thick, joined to
  its solid neighbours and hugging the side open to the sky, so outlines, roofs and outdoor collision
  stay put while the room inside runs on up to the slab (`world/thin_walls.py`). `TileMap.tile_at` gives
  a margin's point to the tile lending it (its floor, ceiling and darkness), collision and sight lines
  test the slab itself, the mesh draws its faces and the margins' floors and ceilings, a doorway's
  lintel rises to the thin walls beside it, and wall props, facing props, chests and wall lights move
  back onto the slab (`TileMap.backed`, `wall_inset`). `tests/test_thin_walls.py` covers it.
  `LANDMARKS` (`spire`, `keep`, `bastion`, `smokestack`, `gatehouse`, `lavafall`, `battlement`) are
  drawn out to the fog. They stand on tiles no one reaches (wall tops, the moat)
  or above a passage's roof (`bastion base=`, `gatehouse`), and no two Cinderhold towers share a shape
  (`test_cinderhold_skyline_has_no_two_towers_alike_and_stands_out_of_reach`).
- Props that fill their tile are listed in `world/world.py` (`BLOCKING_PROPS`, `BREAKABLE_PROPS`;
  the keep adds `pillar`, `sarcophagus` and `headsman_block`, the jungle `bonfire`, `giant_mushroom` and
  `totem`, the town `pew`, `bed`, `cupboard`, `fence`, `lamp_post`, `banner_pole`, `fountain`, `bench`,
  `hand_cart`, `hay_wagon`, `cargo`, `town_statue`, `flying_buttress`, `tree`, `forge_bellows`, `grindstone`, `armor_stand`, `katana_stand`, `bookcase` and `drawers`, the Cinderhold `forge_statue` and `ore_cart`, the cemetery `gravestone`, `cemetery_gate`, `mourning_statue` and `grave_railing`, Vesperholm's `moon_lamp` (a light), `veiled_statue` and `silver_tree`; `test_harrowmere_trees_cut_off_no_part_of_the_town`
  keeps the trees out of the only way anywhere). Decor that blocks nothing:
  `boat` rides on water, `ash_mound` and `bones` lie on the floor, `crypt_front` is built out of a wall, `shelf`, `hearth` and `window` hang on a wall (the last two are lights), `cage`, `roots` and `meat_hooks` hang from the ceiling, `grate` sits in the
  floor, `mushrooms` dot it, and `cobweb`, `skull_niche`, `winch`, `lever` and `shelf_fungus` mount on
  the nearest wall (`WALL_PROPS`), as does Vesperholm's `moon_window`, a lancet of moon-glass and a
  light (`rise=` hangs it up its wall, `size=` scales it about the wall's face). Its skyline is
  `moon_spire`s (`height=`), landmarks on wall tiles no one walks. `lever model=wood` is the jungle's wooden lever.
  Every `banner`, in every map, is the realm's violet (`models.REALM_VIOLET`) and carries its crest (`models.realm_crest`: a lone watchtower dark
  against a sun half sunk below the sea, in a heater shield); the town flies it on `banner_pole`s and
  carves it in `crest_plaque`s, and `through=` draws one crest that shows on both faces of a cloth or
  a block.
  `banner burnt` is the Cinderhold's: sooty cloth, a charred and smouldering hem, burn holes.
  A wall prop must hang on stone that rises past it (at least 2.5 m over its floor, or the ceiling):
  `test_wall_props_hang_on_a_wall_tall_enough_to_hold_them`.
  Light comes from `mesh_builder.LIGHT_KINDS` (torches, braziers, fungus, bonfires, the glowing
  toadstools, and every shrine, `save_statue`: a stone post with a flame burning in an iron dish). A `brazier unlit` or `bonfire unlit` stays cold until Pyre or a Flame Bolt kindles it
  (`World.kindle`); it then burns for good under a `lit:<map>:<tx>,<tz>` flag, and its light is added
  to the baked mesh in place (`MeshBuilder.add_light`).
  Every house's `door_arch` (all but the cathedral's `rose` one, or one marked `open`) hangs a `house_door`
  (`world.hinged`): shut whenever the map loads, never saved; interact swings it open or shut (`World.swing_door`,
  which won't shut it on anyone in the doorway), and shut it fills its tile.
  `chest model=iron` is the Cinderhold's iron chest (`models.chest` style), and `mimic model=iron` hides as
  one (`Enemy.look`). An exit's `model=` draws its way through (`road_gate` for both ends of the north road (each stands out in the open before its wall, never sunk between rock; `style=forge` is a sooty variant), `well`, `cave_mouth`, `keep_door`, `cemetery_gate`, `sewer_grate`, `sewer_ladder`, `vesper_gate` (Vesperholm's, both ends: shut, its
  three sockets dark; open, they shine and moonlight pours through), else a `rope`); each is a landmark of some detail (`test_every_way_between_maps_is_built_in_detail`), and one set against a wall shows black passage through it (`models.PASSAGE_DARK`), never the wall, so the way on stays unseen; a cold `light` hangs over the cemetery's gate on both sides, and a warm one before the north road's Cinderhold end, so their stone shows. An `exit` with `boss=<dead_flag>` is a way on to a boss on another map: the compass
  points at it while that boss lives (`World.boss_target`). `exit requires=<flag> shut="..."` stays shut
  (saying `shut=`) until that flag is set (`World.exit_open`), and `exit oneway` never leads back: going
  through records the journey on the far side at once, so you wake by its shrines, and sets `left:<map>`
  (`Game._take_exit`). `hint text="Line one.|Line two."` is a tutorial hint, not a prop (`world/hints.py`):
  put its marker on every tile of the way past it, keep it to two lines that fit the screen
  (`test_every_cemetery_hint_fits_the_screen`).
  Breakables (`barrel`, `crate`, `urn`, `cocoon`) spill loot from `world/loot.py` (`loot.roll`); a `secret_wall`
  takes the texture of the real walls beside it (`world.secret_wall_tex`), a shade duller, with a faint
  shimmer climbing it now and then and pale motes on its faces within `SHIMMER_NEAR`; struck, ember
  cracks sear it to ash and it crumbles top-down into falling ash and embers over about 1.4 s
  (`models.secret_wall`), letting you through at once (`model=vines top=6` matches the jungle's vine walls; `model=web` is a sheet of
  silk that blades can't cut and only fire burns: Pyre, a fiery art, or a Flame Bolt that strikes it;
  it burns away over about two seconds, `models.burning_web`, but lets you through at once). `door boss=<dead_flag>` is a boss's great door
  (`models.boss_door`, dressed for its boss by `BOSS_DOORS` / `DOOR_ARCHES` / `DOOR_LEAVES`, keyed by
  the `dead_flag`; a new boss door needs an entry in each): the arena behind it seals once you are inside with its boss awake, opens when
  the boss dies, and after you die in there becomes a fog gate (`models.fog_gate`) the boss walks
  through freely and you cross with interact: you walk through it slowly (`World.fog_walk`, `FOG_WALK_SPEED`), never jump. Each arena must stay closed behind its one door
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
  round the rooftop at least 6 m above it), `vesperholm.map` (`test_vesperholm_is_solvable`: every
  chest and the lever over the Glass Bridge, the Duchess only through her door, the drawbridge a
  shortcut between two places you can already reach), and `ashen_cemetery.map` (`test_ashen_cemetery_is_solvable_in_order`:
  the sword before any foe, the scroll before the silk, the gate only behind the Sexton, and no way
  back from town). Their tiles are lowercase letters, digits and punctuation and
  their entity markers uppercase or Latin-1, so the two never collide; keep it that way.
- Shots stop at a blocking prop only below its top (`world.PROP_TOP`, `shots.clears`): a bolt flies
  over tables, caskets and barrels. A low prop not listed there counts as full height.
