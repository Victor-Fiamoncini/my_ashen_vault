# Maps, terrain and props

How `.map` files work and what can stand on a tile.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/maps/*.map` | Plain-text tile maps: `[meta]`, `[legend]`, `[grid]`, `[entities]`. `ashen_cemetery` (the linear first level, the tutorial: the waking grave and its shrine, the lane with the Rusted Sword, the field of headstones, its husks and the Shrouded Mourners bowed at its graves, the chapel with the Flame Bolt's scroll and its silk-sealed far door, the shrine court, and the Sexton's yard with the one-way gate out to the town; walled and floored in its own ash textures, `ash_rock`, `ash_stone`, `ash_brick`, `ash_ground`, `ash_grass`, `ash_flagstone`), `harrowmere` (the walled hill town, laid out on terraces half a metre apart with every rise a `stair_flight` or a kerb: the harbour, the market's fountain and the Bell Square with the Silent Bell at 0 m, the Gaol Ward a metre up (its plaza with the old gaol's barred pit, `exit model=gaol_grate`, down into the Abandoned Prison, Hollis beside it, and a fenced orchard on grass), the east lane half a metre up to the gap in the wall, and the cathedral's terrace two metres up behind its parapet, where the Enthroned sits; a stone `street_arch` over the street at every change of district (`width=` tiles, its piers on the walls either side, `test_harrowmere_climbs_in_terraces_no_step_too_tall`); five houses, each lived in (`test_every_harrowmere_house_roof_covers_a_house_with_someone_living_in_it`) with their windows set symmetrically, either side of the door or of a doorless wall's middle (`shutters seed=` gives one house's windows one look) and each built its own way under clay-tile roofs (`tex=clay_tile`; only the cathedral keeps dark slate): Brannoc's forge, its door between two windows, Corvane's low timbered hut, Pell's L of two crossing gables (a full stone pier, `^`, in the L's elbow, so the thin walls meet without a slit), Wren's house in `stone_timber` with a `jetty` and `dormer`s, and Tamsin's stone hall under a hipped roof (`roof hip`); thin-walled (`thin=0.5`), paved in setts with flagged kerbs, wattle fences round grassed gardens (`tex=grass`, a soft footstep), a canal running up from the harbour; you arrive by the cemetery's gate in its west wall, its `start`; the gaol's grate, the trail gap, the north gate and four street grates down into the sewers lead out), `abandoned_prison` (the prison below Harrowmere's Gaol Ward, shut in a single night on its gaolers and prisoners: you climb down the ladder from the gaol's grate into its tall, daylit shaft (its `start`; the `sewer_ladder` there climbs back up to the plaza beside the grate, `test_the_gaol_grate_and_the_prisons_ladder_lead_to_each_other`) and come in through a breach in its outer wall to the gatehouse and its shrine; the guard hall, the west cell block (barred one-tile cells either side of a dark aisle, `gate lever=west_cells` raised all at once by the lever at its head, which lets out the Hollow Inmates still inside; the Cell Key lies in one), the warders' quarters behind the Cell Key's door, Brother Marrow's cell off the corridor (`npc id=marrow reach=3.6`, spoken to through its bars; its lever is in the warders' quarters), and at the corridor's east end the chapel of the old gods, its pews, faceless `old_idol`s and the altar (`altar model=idol`) where the Warden's Key lies; the Undercroft below its cells and the Warden's Gallery above the boss door, the Butcher's slaughter hall north of it. Its aisles are `dark=`; `test_abandoned_prison_opens_in_order_from_the_well_shaft_to_the_chapel`), `verdant_hollow` (the jungle through the cave at the end of the village's east trail: Mossmouth cave, the Root Caverns below the bog, the Canopy Walk to the boss), `cinderhold` (the lava fortress up the north road: the Sallow Fen first, grown south of the old arrival as Vesperholm's cave was (the north road lands you at its foot, `start = 30 111`; a violet mire, `tex=sallow_mire` with `afflict=toxic:`, its deep channels faster, round three `fen_beacon` islands whose violet fire must all be smothered (`World.douse`, `doused:` flags) before the great fen gate opens onto the ash road: three `gate lever=fen_beacons model=great` tiles side by side in the black-brick curtain wall that closes the fen's north side (`dress=rampart`, its bays turned to the fen), one portcullis six metres wide (`world.gate_runs` gives each tile its slice, `fen_models.great_portcullis`) under a gatehouse with its towers stood out into the fen either side (`fen_models.fen_great_gate`, drawn by the run's first tile, cressets and slits burning with firelight), `test_the_fen_gate_is_one_great_portcullis_three_tiles_wide_between_two_towers`; dry ways through it that work no toxin into you: dirt paths (`tex=dirt_path`) and mounds of firm earth (`tex=dirt_hill`, half a metre a step) crowned by great dead trees (`huge_rotten_tree size=`); a path winds north from the watch-post shrine to the great rotten bridge, decked in `rotten_wood` and two abreast, that crosses a lagoon of sink-holes (`water drown=mire`) to the great square, the old moot in the fen's middle ringed by sink-holes: two of the bridge's spans are rotting `plank`s over a fouled pool (`water afflict=toxic:` with no `drown`: a fall into it costs HP, works its whole dose in at once and casts you back onto the last sound timber), so you keep moving; the rotten lever at the square's heart (`lever model=rotten`) lets down two great rotten drawbridges (`bridge lever=fen_causeway model=rotten`), north to the path up to the north island and the gate and east toward the east beacon, after which the fen can be crossed dry (`test_once_the_bridges_are_down_the_fen_can_be_crossed_dry`); Fen Lurks squat in the mire, Bileguts crawl the banks and the Mire Tyrant keeps the north island; two sunken ways, trenches of mossy cobbles (`tex=cobble_moss`) cut a metre below the mire between low stone walls that hold it back, run dry out to two beacons, the west one from the shrine's court and the north-east one from the east path past the east drawbridge (`test_sunken_ways_run_dry_under_the_mire_between_low_walls_out_to_two_beacons`), and broken runs of the marsh-folk's old walls stand out of the mire here and there; `test_cinderhold_is_solvable`, the `test_*fen*` tests in `tests/test_cinderhold_world.py`), its card reads "Sallow Fen" (a `region` band either side of the fen gate) and "The Cinderhold" as you go up through the gate onto the Gargoyle Way, the ash road running straight to the long bridge between gargoyles crouched in facing pairs in niches in its cliffs, the wayside shrine in a court off its east side; then the long bridge, the gatehouse and postern, the foundry and the smelter pits below it, the ashworks, the rampart and the tower stair up to the keep), `cinder_keep` (the keep, a map of its own
  behind the door at the top of the tower stair: the postern landing, the great hall, the switchback stair,
  the antechamber's shrine and the walled rooftop where the twin gargoyles perch), `harrow_sewers` (the
  sewers under the town, reached by four grates (`sewer_grate`) in the town's corners that each drop onto the ladder
  (`sewer_ladder`) under them, at the same tile, each up its own 11 m brick shaft (a `ceil=11` floor, walls beside it `top=11`) to a black mouth: the North Sluices, the Market Drains (narrow vaulted runs,
  its `start`), the Canal Culvert and the Quay Outfall, all joined through the Cistern and its shrine;
  Mother Gnawl's nest between the Cistern and the outfall, a great door at each of its two mouths (two
  `door boss=matron_dead`: an arena each over the same tiles, sealing, fogging and opening together), and
  8 m down the outfall's U-turn stair the Sump and the Sodden Pall's cistern behind its great door. Shortcuts: a barred door down from the sluices, the sluice
  pit's drawbridge and a lift from the Sump up to the Cistern (an 8 m ride). Wadeable `sludge` floors (`slow=`, some with
  `flow=`) hold its drowned and leeches; walled in `sewer_brick` under a `sewer_vault`;
  `test_harrow_sewers_is_solvable`; once the Pall falls, the breach in its cistern's north wall,
  `exit model=cistern_breach yaw=90 requires=pall_dead`, leads down to Old Harrowmere (a brick-lined black tunnel stood out of the wall, `sunken_models._breach_opening`, as `sunken_stair` is at the other end); like every gate set
  into a wall, it needs the `yaw=` that turns its back (-X) to the wall), `old_harrowmere` (the
  sunken first city, in a cavern below the sewers: a vertical map of tiers over a 40 m `chasm` that kills,
  with no sky: the cavern's vault (`[meta] vault = 24`, below) hangs over it all. The Breach Landing (h 0, its shrine and the
  `sunken_stair` back up to the cistern), the Cliff Stair down the north wall to the bell-keepers' terrace
  (-8), a bridge out to the Bell Tower, whose stair winds down round three sides of its brick core to the
  Aqueduct (-16), the Colonnade, the Grand Stair down to the Drowned Plaza (-20) under a great rift of
  daylight in the vault (`sun_shaft height= width= rift=36,7 rift_yaw=90` over its fountain places the
  rift; no beam falls from it, with warm `light`s at its foot; `waterfall`s pour from fissures under the vault past the
  plaza and the Bell Tower into the chasm), and the Keystone's Foundation Court (-22) behind two
  `door boss=keystone_dead` (the front one at the end of the roads of light, ward decks over the chasm
  east of the plaza, below; the rear one out to the lift room; one arena, like Mother Gnawl's nest). The
  shortcut: a locked lift from the lift room 22 m up to the dark gallery cut through the rock from the
  landing, behind a plain stone `door model=stone` in the landing's south wall at 3,8 (unlocked, two-way;
  `test_a_plain_door_leads_from_the_landing_down_into_the_old_gallery`). A false wall in that gallery opens on the Bell-keepers' Oubliette (h 0, under its own
  `ceil`, lined in `sunken_brick`): a corridor of barred cells (`gate lever=oubliette`) holding Aubel,
  Coldry, Ysolde, a hollow inmate and a mimic, and the gaoler's hall with the lever and the Torch
  Greathammer. Every cell is walled off from the corridor but for its bars, so its prisoner is only
  spoken to through them until the lever (the test checks no prisoner's tile can be walked to before
  it). Two more false walls (`top=24`, as the map has no ceilings) open narrow fissures: one in
  the plaza's west cliff with the Ember Stone Sword, one in the lift room;
  `test_the_oubliette_hides_behind_a_false_wall_and_its_lever_opens_the_cells`. A second lever in the
  gaoler's hall (`lever id=under_stair`) raises the bars either side of the gallery, the gaolers'
  postern (`gate lever=under_stair` at 4,18 and 2,18), onto the Under-Stair: it winds down the cavern's
  west wall (0.5 m a tile, its own `ceil` all the way) to the Under-Cells (h -6, rows 47-58 below the
  court): the flooded cell block (a `water`-textured floor with `slow=`), the interrogation hall (a taller
  `ceil`; a gaoler and a golem), the warden's office, whose lever (`lever id=undercells`) raises every
  cell front below, and past it the flooded deep cells, where Brannick and Sister Vell are held. A hint at
  the stair's foot sets `visited_undercells` (a `hint` may add `sets=<flag>`);
  `test_the_under_cells_lie_down_the_gaolers_stair_and_the_wardens_lever_opens_them`. East of the roads,
  on its quay (x 45-47), the Mortar Sisters' Workshop: their ward-stone carving benches, golems and a
  sexton, a lore hint and a reward chest; `test_the_mortar_sisters_workshop_stands_east_of_the_roads`.
  Broken colossi of Lyra the Embracer (`lyra_statue`, `prison_models.lyra_ruin`: the prison's `old_idol`
  some 8 m tall, arms snapped, some lying at her sides, her head gone or toppled on some) stand on the
  plaza's north rim facing the fountain, two on its south rim flanking the view of the Keystone's great gate, at the back of the workshop and at the court's east
  end; each fills its tile, and nothing of her lies behind her, so her back can be to a drop or a wall.
  The `energy_core` (the mortar-light, `seal=c`) stands at the heart of the fountain's pool at 21,28,
  under the rift (the `sun_shaft` beside it at 21,27), teal `light`s (`color=0.45,1.25,1.0`) round it.
  Its `scale=1.7` draws it all bigger; past its own size its body fills the tiles round its own
  (`world.core_footprint`, here the whole pool, so you cannot wade in beside it) and a blow reaches it
  from their edge (`World.strike_core`). Its own light is raised to its heart with `y=` and widened with
  `light_radius=` (its `radius=` is the reach it sustains golems within);
  `test_a_scaled_core_fills_its_pool_and_is_struck_from_the_rim`.
  `sunken_tower height=` landmarks rise out of the chasm. Bell-Harpies (`harpy`, flyers) wheel over
  the plaza and the terrace and out over the chasm. Paved in `ochre_flag`, walled in
  `cavern_rock` and `sunken_brick`; the map is drawn by a script's layout, one legend letter per height;
  `test_old_harrowmere_is_solvable_from_the_breach_down_to_the_keystone`), `vesperholm` (the Moonbound City behind the Vesper Gate in
  Harrowmere's north wall, at the head of the cathedral steps: the town's `exit model=vesper_gate`, always
  open, ends a straight walk north up the steps and the porch past lamps and banner poles, and leads to
  its `start` in the hall of the Glimmering Cave, before the gate home (never shut either), which brings you
  back just south of it. The cave (`crystal_rock`, lit by `moon_crystal` clusters standing on its floors and
  `hanging_crystal`s hung from its roof, three Glassmites folded among them) climbs half a metre a tile,
  never a step too tall, from the gate's hall at 0 m through the tall geode gallery at 2 m, along a ledge
  over a crystal chasm (a Lantern Wraith throws across it from the gallery), up through the moon-pool
  grotto open to the sky (two Moonhounds, a coffer in the side grotto east of it) to its mouth (a
  `crystal_arch`, the cliff's face built up over the way out) onto the overlook, 6 m over the court
  under the open moon, where the shrine stands and the whole city spreads out north to the cathedral;
  a `moon_stair` 12 tiles long (the city's own grand stair, its pier lamps lit by orange `light`s on
  its 4th and 8th tiles) goes down from it into the Gate Court;
  `test_the_vesper_gate_opens_into_a_crystal_cave_that_climbs_to_an_overlook`. Under the `moonlit` sky (a vast, bright full
  moon in the north, wisps of cloud across it, the sun buried in a bank of cloud in the south), a pale
  blue-silver ambient and a fog reaching 84 m: the Gate Court, Lantern Square and its
  shallow moon pool, the Landing on the gorge's edge, Lamplighters' Row and a hidden court behind a false
  wall; the gorge (an 18 m `chasm`) between the lower town and the castle, crossed by the Glass Bridge
  (`moon_glass`) at the west street's head into the castle's postern; the bailey, the west chapel and
  the Duchess's garden; the Cathedral of the Long Night, its nave, and behind its great door
  (`door boss=duchess_dead`) the choir floored in moon-glass where Duchess Ilvane waits. Her choir has a
  second mouth, a back door in its east wall (`door boss=duchess_dead rear` at 32,22: it seals, fogs and
  opens with the great door, and `rear` keeps the compass off it), onto the old stair north up through
  the cathedral's east wall and the stair tower on its north-east corner (half a metre a tile under its
  own vaults), out onto a flying stair one tile wide that climbs west over the drop behind the
  cathedral (an 18 m `chasm` either side, a Lantern Wraith throwing down it from the Moon Terrace at
  8 m), then a grand stair (`moon_stair`, three abreast between cheek walls) north up to the forecourt
  of Lyra's Chapel at 11.5 m, on its crag behind the choir (two Pale Sentinels keep it): a nave of
  `moon_glass` under a vault 12.5 m high, its walls rising to 26 m over the cathedral's 14, behind its
  own `moon_portal` and under a `grand` `moon_roof` higher than the cathedral's. The Argent Sigil lies
  in the hands of Lyra the Embracer on her altar in the middle of the nave (`altar item=argent_sigil
  model=lyra` at 21,5; the Duchess drops nothing), and once it is lifted the portal to Herran's Castle
  opens in the apse behind her (`exit model=argent_portal requires=argent_sigil_taken hidden` at 21,2).
  The crag and the chapel are twenty rows north of the city's old edge: saves made before them are
  moved to match (`save_system.SHIFTED_MAPS`). Shortcut: the
  great bridge over the gorge, three tiles abreast and four long (`bridge rise=18`, one entity a tile),
  sunk on the gorge floor until its lever in the bailey raises it, back to the Landing. Walled in `moonstone`, paved in `moon_paving`, roofed in `silver_slate`;
  `test_vesperholm_is_solvable`), `vigil_chapel` (the Vigil Chapel, a small map of its own behind
  Old Harrowmere's lift room: the door in the lift room's south wall at 8,45, `exit model=chapel_door
  requires=keystone_dead`, stays shut until the Keystone falls, and leads to its `start` in the low
  vestibule, the way back right behind you. No foes: a tall nave of `moon_paving` under `silver_slate`, an
  arcade of pillars, pews facing the altar either side of a `nave_runner`, lower aisles lit by
  `moon_window`s, and up a half-metre step the chancel floored in `moon_glass`, where the Vesper
  Moonbrand stands planted in its altar (`altar model=moon yaw=90 said="..."`: `said=` gives the lines
  shown when you take its offering, one per `|`), veiled statues and candles about it;
  `tests/test_vigil_chapel_world.py`), `herrans_castle` (Herran's Castle, 32x42, over a sea of cloud under the
  `storm` sky: a stormy night, gas lamps for light: through the portal (`exit model=argent_portal
  requires=argent_sigil_taken hidden`, at 21,2 in the apse of Lyra's Chapel: `hidden` keeps an exit
  undrawn and out of reach while it is shut; its twin stands at the quay's edge) you arrive on the Cloud Quay, its `start` and shrine, a broken
  stretch of balustrade open on the clouds, and go north through the gatehouse corridor into the Ring, a
  roofed passage of sooted brick round a central void that falls to the clouds, its arches open on the drop.
  Four towers stand on it: the Laboratory (NW, the Spire Key, and in its back wall the one `secret_wall` onto
  the secret lab, with Herran's Graft Draught, Sun Tincture and Bonesaw and a page of his journal as a
  `hint`), the Clock Tower (SW, a spiral stair inside its wall up to 10 m), the Aviary (SE, drakes and a
  gallery) and the Belvedere (NE, a `locked` cage lift down to the Ring: the shortcut). The High Walk, a
  single line of `iron_grating` at 10 m over the void, joins the Clock Tower's top to the Belvedere's and runs
  on to the spire passage, where `door key=spire_key` guards the spire's door (`exit model=spire_door`). Its
  sea of cloud is a `chasm` with `fall=cloud` (the words for the plunge, `world.PLUNGE_MESSAGES`) and `void`
  (no floor drawn, so the sky's `cloud_sea` layer shows far below), under `edge_top = -40` so no rim wall
  stands round it. Walled in `herran_brick`, capped in `herran_slate`, paved in `herran_ashlar` and
  `encaustic_tile`, its labs in `lab_tile`; `herran_tower` landmarks
  (`style=round|octagon|clock|belvedere|needle`) make its skyline; `tests/test_herrans_castle_world.py`),
  `herran_spire` (Herran's Spire, behind the castle's spire door: the base hall (24x28), a stair to the drake
  hatchery at 6 m, a stair on to Herran's study at 11 m and its shrine, and behind `door boss=herran_dead` his
  observatory out on the tower's flank, open to the sky under an `observatory_dome`, its `telescope`, ringed
  by a parapet of wall tiles (never chasm, which an arena's flood would leak into)) |
| `src/ashen_vault/world/terrain.py` | Terrain: rafts, planks, ledges, rotten floorboards, chain lifts (pressure plates, call plates, `summon`), currents, thorns, chasm and river falls, hard landings, the log rack, spore pods (`World.terrain`) |
| `src/ashen_vault/world/hazards.py` | Dungeon traps: floor spikes, pendulum blades, crumbling floors, flame jets, magma vents (whose bombs are `Eruption`s with an `origin`); the bosses' fire eruptions and slam shockwaves |
| `src/ashen_vault/world/thin_walls.py` | Thin walls (`wall ... thin=<m>`): the slab each such tile stands as (hugging the side open to the sky, else a full wall it backs onto, centred between two rooms; a run keeps one line, `test_harrowmere_has_no_slits_between_its_thin_walls`), the margins it lends to its open neighbours (`Layout`), and how far a prop must move back to touch it (`inset`) |
| `src/ashen_vault/world/ramparts.py` | The great walls' dressing: every face of a `dress=rampart` wall turned to open sky-lit ground at least `MIN_HEIGHT` below its top gets a static `rampart_bay` (`town_models.rampart_bay`: a stepped plinth, a corbelled parapet with merlons, and a `pier` of three engaged columns every `PIER_EVERY` tiles and at each run's ends, blind round arches between), kept clear of wall towers, gates (`world.RAMPART_GATES`) and wall props. Nothing stands out past the player's radius, so bays need no collision |
| `src/ashen_vault/world/wall_cracks.py` | The cavern walls' cracks: along every straight run (at least `MIN_RUN` tiles, one top) of faces a `dress=cracks` wall turns to open sky-lit ground at least `MIN_HEIGHT` below its top, a few static `wall_crack`s (`sunken_models.wall_crack`: a long jagged fissure of quads a hair off the wall, a black core over a lip of shadowed stone, offshoots forking up and down it, a `SEEP` share with a faint thread of teal mortar-light), one about every `EVERY` m, at least `MIN_GAP` apart and `END_CLEAR` from a run's ends, seeded from the map so the same walls always crack the same way, the tallest kept past `MAX_CRACKS`. A face over the chasm is cracked only its top `MAX_SPAN` m. `World._dress_cracks` keeps them two tiles clear of gates (`world.RAMPART_GATES`), lifts, false walls and falls (`world.CRACK_CLEAR`) and a tile clear of wall props. No collision |
| `src/ashen_vault/world/sea.py` | The open sea (`[meta] open_sea = true`, Harrowmere only): the deep water and its far reaches past the grid's south edge (`far_cells`, bands of cells doubling in size out to `FAR`) go into the mesh builder's own `sea` batch, which `World._draw_sea` draws under a fog `SEA_REACH` times thinner than the land's, so it runs on to the horizon; the sun lays a twinkling path of glints on it (`glitter`, the cut-out `glitter` texture, coloured by `sky.sun_color`) |
| `src/ashen_vault/world/darkness.py` | Dark tiles: how your light and the fog close in, Lumen and the Veil of Mist |
| `src/ashen_vault/world/doors.py` | One-way doors (`door from=`): which side lifts the bar |
| `src/ashen_vault/world/arena.py` | Boss arenas behind a `door boss=<dead_flag>`: the flood-filled lair, the fight that seals the great door, and the fog (`fog:<map>:<tx>,<tz>`) left after you die in there |
| `src/ashen_vault/world/hints.py` | Tutorial hints (`hint text="...\|..."`): shown once, the first time you step onto any of its marker's tiles (`hint:<map>:<marker>` flag); `World._update_hints` fires them |
| `src/ashen_vault/world/regions.py` | Named regions within a map (`region name="..."`): markers in a band either side of a border; stepping onto one of another region raises its name as the area card (`World._update_regions`, `Game.announce_region`), and on arrival the nearest marker names the region you are in (`World.region_at`) |
| `src/ashen_vault/world/footsteps.py` | Footsteps: each floor `tex` belongs to a surface (stone, wood, soft, mud, water, metal, gravel, glass (Vesperholm's `moon_glass`); the platform under you overrides it), and `Game._footstep` plays its `step_<surface>` sound. A new floor texture needs a surface (`tests/test_footsteps.py`) |
| `src/ashen_vault/world/rest.py` | The shrine rest: timing and the pixelated ember fog pattern drawn while you pray |
| `src/ashen_vault/world/sky.py`, `render/sky.py` | Skies (`[meta] sky = overcast\|dusk\|jungle\|ember\|moonlit\|storm`): a gradient dome meeting the fog at the horizon, a sun and halo, drifting cloud banks and an overhead cap, horizon mist; every sky's sun stands at `SUN_AT` (low in the south, over the town's sea), the same `SUN_SIZE` disc (Harrowmere's) on every map, only its halo's colour and width changing with each sky's haze (`test_every_sky_puts_the_sun_low_in_the_south_over_the_towns_sea`), but Vesperholm's `moonlit` sky hangs a vast pale moon at `MOON_AT` instead (high in the north, over its cathedral; `Sky.moon` makes it full, lit all over and a touch dimmer at its limb, `LIMB_SHADE`, its seas scattered across it, `sky.maria` / `MARIA`, and still wisps of cloud across it, `sky.wisps`) and buries the sun itself in a bank of cloud silvered at its rims (`Sky.veiled`, `sky.shroud`, with a faint glow round it) among a crowd of stars (`Sky.star_count`) that reach up to the moon's bright corona (`Sky.corona`, `CORONA_SCALE`; stars keep only `Sky.star_clear` degrees clear of the disc, and shine over its halo), with the galaxy's band strewn across them (`Sky.galaxy`, `sky.galaxy_field`) and moonlit cloud overhead; every other sky shows that same moon from afar over its own land (`Sky.far_moon`, a `FarMoon`: the same `MOON_SIZE` disc as over Vesperholm, so it looks alike on every map, but paler and dimmed by its sky, its `far_moon` and `far_wisps` layers drawn under the drifting clouds so they pass over it, its halo, `FAR_MOON_HALO`, in the dome, no stars on it; `test_the_moon_is_the_same_size_over_every_map`); Herran's `storm` sky looks down on a sea of cloud (`Sky.cloud_sea`, `sky.cloud_sea`) and veils its sun too; stars glint behind the clouds (`Sky.stars`, their brightness; only faint ones in the jungle's haze), its disc drawn over the clouds (`sky.sun`) and its halo behind them; dimmed by darkness and the Veil. Built pure in `world/sky.py`, drawn first each frame without fog or depth by `render/sky.py` |
| `tools/level_planner/` | A top-down level planner (`index.html`, open it in a browser; a design aid, not part of the game): paint tiles, pin NPCs, gates and wells, export JSON or an ASCII grid. `map_to_planner.py <map>` turns a game map into JSON for its Import box |
| `tools/level_sketch/` | A free-form top-down sketchpad for level design (`index.html`, open it in Chrome; a design aid, not part of the game): shapes, lines and markers measured in metres, on layers, over an optional faint underlay of a game map (`map_to_underlay.py <map>`), saved as `<name>.sketch.json` + `.svg` in `sketches/` for planning a level's rebuild. Its logic is `model.js`, tested with `node --test tools/level_sketch/` (not in CI) |

## Rules

- `[meta] name` is the area's name as the player sees it: raised in the logofont over the screen as
  you enter (`hud.area_title`), so it must be letters and spaces and fit the screen
  (`tests/test_ui_logic.py`).
- Map grids are whitespace-sensitive. Don't reformat `.map` files. Each grid character is one 2 m tile;
  an `[entities]` marker places a prop, enemy or hazard there, standing on the legend tile named by
  `on=` (the map's `default` otherwise). With `entity_floor = auto` in `[meta]` (the prison uses it), a
  marker without `on=` stands on the floor most of its neighbours share, so one marker serves every
  level. The jungle uses it too; it ran out of ASCII markers, so a few of its markers are Latin-1
  letters (`À`, `Ñ`...). Wall props (torches, banners, shackles, racks) hang on the
  adjacent wall and chests/altars turn to face the open side automatically, so they rarely need `yaw=`.
  A chest (and the chest mimic) with a wall behind it sits back against that wall (`TileMap.seated`,
  `tests/test_seating.py`), so place chests beside a wall.
- Floor legend entries can add hazards: `hurt=<hp per tick>` (thorns), `flow=<dx>,<dz>` (a current),
  `slow=<multiplier>` (mud), `afflict=<ailment>:<per second>` (a fouled mire that builds that ailment while
  you wade it off any platform, `terrain.MIRE_TICK`; no hazard, so foes wade it too; on a `water` tile
  that casts you back, a fall into it works the whole dose into you at once), `pit` (a hole you can walk into; you fall, are hurt and hauled out), `lava` (a
  pit that sears `LAVA_SHARE` of your max HP the moment you touch it and hauls you out; give it
  `tex=lava`) and `chasm` (a sheer drop: a raft, plank or ledge carries you over it). No invisible walls:
  the player may walk off into water or a chasm (`Terrain.open_to`; only a lift's cage hanging above
  you shuts its shaft), while foes never step onto either. Water casts you back ashore, hurt, unless the legend marks
  it `deep` (the town's open sea, which `world/sea.py` and the mesh builder draw out to the horizon) or
  `drown=<key>` (water you drown in that is no open sea: Harrowmere's canal, `drown=canal`): going in is a drowning
  (`Terrain._drown`, the plunge again, sinking slowly) that kills you within `terrain.DROWN_TIME`.
  `Tile.drown` keys the words for it, `world.DROWN_MESSAGES` going in and `world.DROWN_DEATHS` at the
  end (`deep` water, and a bare `drown`, is the "sea"; a new key needs an entry in both). The bogs
  (the sewers', the Hollow's, Vesperholm's moon pool) only cast you back; going
  over a chasm's brink is a plunge (`Terrain.plunging`, input locked) that kills you within
  `terrain.PLUNGE_TIME`, unless the chasm floor lies within `FALL_SAFE` of you (an empty shaft's
  bottom, which is only ground). Floors with `tex=lava` are drawn
  at full brightness and light their shores (`mesh_builder.lava_lights`), chasms included. Drops over
  1.8 m cost HP (`FALL_PER_M` a metre), except into a `pit`; a drop of `terrain.FALL_LETHAL` (8 m) kills,
  but not on the spot: stepping off an edge over one (a ledge, an empty lift shaft, a lift's deck) you
  fall it, the view dropping, until you hit whatever is below (a lift's deck included), as over a chasm
  (`Terrain._lethal_drop`, `fell_into == "drop"`, `world.DROP_MESSAGE`).
  Any tile may add `dark=<0..1>`: the share of the map's ambient light it loses. Lights still shine
  there, and standing in one shrinks your own light and pulls the fog in (`world/darkness.py`);
  Lumen pushes both back.
  Terrain entities: `raft to=tx,tz speed= phase=`, `plank`, `ledge deck=`, `boards deck=` (rotten
  floorboards that break for good), `lift top= [start=top] [locked] [speed=] [model=cage|rune]` (a chain lift:
  its tile is a `chasm` shaft whose floor is the bottom stop and whose `ceil` clears `top`. It works
  like Dark Souls': stepping onto the pressure plate in the middle of its deck (`terrain.PLATE_R`)
  sends it to the other end (step off the plate and on again to go back), and stepping onto the call
  plate set in each landing's floor just out from the shaft (`Platform.calls`, `terrain.call_plates`)
  brings it. A `locked` lift is a one-way shortcut: it rests at its `start` end, the end you reach
  first; the far landing's call plate only clicks and says it is fastened (`Terrain.refused`), until
  its first ride frees it for good (`lift:<map>:<tx>,<tz>` flag; that plate then calls it too). Lifts
  have no levers. Floors a lift
  joins sit far apart (the prison's Undercroft at -10 m, its Gallery at 12 m), so a ride feels like one. `model=cage`
  draws the prison's barred jail cage, open on the sides that face a landing (`terrain.lift_doors`); `model=rune`
  Old Harrowmere's chainless stone deck borne on rings of teal glyphs, its plates rune plates that flare
  underfoot, its glyphs cold until a `locked` one is freed (which it announces in its own words,
  `world.LIFT_FREED`); it rings as stone underfoot),
  `bridge lever=id hinge=n|s|e|w deck=` (a drawbridge standing raised on its hinge side until its
  lever lets it down, for good; with `rise=<metres>` instead it is a span of a stone bridge sunk that far
  below its deck, which its lever raises out of the chasm over `terrain.BRIDGE_RISE` seconds, to one
  `stone_rise` rumble and one `stone_land` boom for all its spans: give every tile of it the same lever,
  and lay it out north to south, as many abreast as it is wide; `terrain.bridge_spans` works out each
  tile's parapet, piers and place along its arches, and `moon_models.great_bridge` draws it; with
  `model=rotten` it is a span of the Sallow Fen's great rotten drawbridges: a line of drawbridge tiles
  running out from their hinge with the same lever and `hinge=` swings as one deck from the bank,
  `world.bridge_runs` gives each tile its place along it, and `fen_models.rotten_drawbridge` draws it), `log_chute to=tx,tz every= speed= logs=` (a log rack that only
  releases while someone climbs its slope) and `spore_pod every=`.
  Hazard entities: `spikes`, `pendulum`, `crumble`, `flame_jet dir=n|s|e|w len= every= phase=` (a
  nozzle on the wall behind its tile firing `len` tiles along `dir`) and `magma_vent radius= every=
  count= phase=` (stands in a lava chasm; lobs bombs at open-sky solid ground within `radius` metres,
  the first at you).
  `[meta]` may set `model_range`: metres beyond which small models stop being drawn, short of the fog's
  end, on a map that sees far, and `indoor_range` a shorter one while you stand under a ceiling (the far
  rooms are walled off). Props wholly behind the eye are never drawn (`world_view.behind_view`).
  A wall standing behind a lower one (a curtain wall behind its cliff, a tower behind its parapet) is
  built where it rises above it (`MeshBuilder._exposed_walls`), so a tall wall can back a low one.
  `[meta] roofs = true` (the Cinderhold uses it) closes a map seen from above: every ceilinged tile
  gets a roof (`roof=<h>` in its legend, at least `mesh_builder.ROOF_SLAB` over its ceiling;
  `roof_tex=`), the walls rising past a roof show their faces above it, and every wall tile is capped.
  A passage through a wall is roofed at the wall's height (`roof=16`), so the wall runs on over it.
  `[meta] vault = <h>` (Old Harrowmere) hangs a cavern's roof of rock over the whole map at height `h`
  (`vault_tex=`, `cavern_rock` by default; `world/vault.py`, built by `MeshBuilder._build_vault`): lumpy,
  stalactites hanging from it, over every tile but the walls already reaching it and the tiles under
  their own `ceil`. It is only drawn: no tile gains a ceiling, so collision, sight and open-sky checks are
  as before. Over the map's `sun_shaft` it opens in a crack (at the top of the leaning shaft,
  `vault.SHAFT_LEAN`; give the shaft the `height=` to reach it), daylight glowing on the rock round it;
  `test_old_harrowmeres_vault_hangs_clear_of_everything_below_it`. The shaft's `rift=<length>,<width>`
  (metres) and `rift_yaw=` (degrees from +z) widen the crack into a long rift. Only the crack is drawn
  (`sunken_models.vault_rift`): no beam of light falls from it.
  Ward decks (`ward set=a|b|c deck=<h>`, a platform kind; Old Harrowmere's roads of light: gold, pale
  and teal) stand over a chasm one set at a time: striking any `ward_crystal` (a blocking prop, struck
  like a breakable, `World.strike_wards`) turns them to the next set (`terrain.next_ward`), saved as the
  `ward:<map>` flag (pale) or `ward:<map>:c` (teal). The teal set is fed from the energy core: until a
  `ward_crystal shield` (the core's shield ward) has rung (`ward_fed:<map>`) the crystals only turn gold
  and pale; that first strike wakes the teal road at once, and from then on every crystal turns gold,
  pale, teal. A core with `seal=c` keeps its shield up unless the teal road stands
  (`World.core_shielded`). A deck fades in and out over `terrain.WARD_FADE` and, like a drawbridge,
  bears weight only when fully in, so turning the road you stand on drops you. Keep a crystal on every
  island and on both shores, so any set standing leaves one within reach;
  `test_the_roads_of_light_take_three_turns_to_cross_and_never_strand_you` and
  `test_the_third_road_runs_out_to_the_cores_shield_ward_and_teal_home` search the (tile, standing set,
  fed) states: three turns to the court (never needing the teal road), one to the Mortar Sisters' quay,
  two to the shield ward, three home to the core with its shield down.
  A `waterfall width= [top=] [foot=]` (a landmark) pours from a broken lip down to `foot` over its
  floor: without `top=` it spills from just under the vault (`WorldView._fall_top`); `foot` below 0 plunges
  on without a pool (over the chasm), otherwise it lands in a churned pool with spray and mist. Its
  sheet runs along local X: `yaw=90` turns it to run along z.
  A wall tile may set `dress=rampart` (Harrowmere's great walls): carved bays along its open faces
  (`world/ramparts.py`).
  A wall tile may set `dress=cracks` (Old Harrowmere's cavern walls and the old city's tall brick): great
  branching cracks down its tall open faces (`world/wall_cracks.py`). Join dressings with commas
  (`dress=rampart,cracks`) to give a wall both.
  A wall tile may set `thin=<m>` (the town's houses use 0.5): it stands as a slab that thick, joined to
  its solid neighbours (and toward a doorway, a roofed tile with thin wall beyond it, so a corner beside
  a door keeps its face closed) and hugging the side open to the sky, so outlines, roofs and outdoor collision
  stay put while the room inside runs on up to the slab (`world/thin_walls.py`). `TileMap.tile_at` gives
  a margin's point to the tile lending it (its floor, ceiling and darkness), collision and sight lines
  test the slab itself, the mesh draws its faces and the margins' floors and ceilings, a doorway's
  lintel rises to the thin walls beside it, and wall props, facing props, chests and wall lights move
  back onto the slab (`TileMap.backed`, `wall_inset`). `tests/test_thin_walls.py` covers it.
  `LANDMARKS` (`spire`, `keep`, `bastion`, `smokestack`, `gatehouse`, `lavafall`, `battlement`,
  `waterfall`, ...) are
  drawn out to the fog. They stand on tiles no one reaches (wall tops, the moat)
  or above a passage's roof (`bastion base=`, `gatehouse`), and no two Cinderhold towers share a shape
  (`test_cinderhold_skyline_has_no_two_towers_alike_and_stands_out_of_reach`).
- Props that fill their tile are listed in `world/world.py` (`BLOCKING_PROPS`, `BREAKABLE_PROPS`;
  the prison adds `pillar` (`pillar model=colossal`, the Keystone's court: a column of drums rising
  from the floor into a cavern's `vault`, `Vault.column_height`, its head sunk in the rock), `sarcophagus`, `headsman_block` and `old_idol`, Old Harrowmere `lyra_statue`, the jungle `bonfire`, `giant_mushroom` and
  `totem`, the town `pew`, `bed`, `cupboard`, `fence`, `lamp_post`, `banner_pole`, `fountain`, `bench`,
  `hand_cart`, `hay_wagon`, `cargo`, `town_statue`, `flying_buttress`, `tree`, `forge_bellows`, `grindstone`, `armor_stand`, `katana_stand`, `bookcase` and `drawers`, the Cinderhold `forge_statue` and `ore_cart`, the cemetery `gravestone`, `cemetery_gate`, `mourning_statue` and `grave_railing`, Vesperholm's `moon_lamp` (a light), `veiled_statue`, `silver_tree` and `moon_crystal` (`size=`; a light, and it blocks), and `hanging_crystal` (hung from its tile's ceiling) and `crystal_arch` (`height=`, a cave mouth's face built up over its tile's -X edge); `test_harrowmere_trees_cut_off_no_part_of_the_town`
  keeps the trees out of the only way anywhere). Decor that blocks nothing:
  `boat` rides on water, `ash_mound` and `bones` lie on the floor, `crypt_front` is built out of a wall, `shelf`, `hearth` and `window` hang on a wall (the last two are lights), `cage`, `roots` and `meat_hooks` hang from the ceiling, `prisoner_remains` slump in their chains against a wall, `grate` sits in the
  floor, `mushrooms` dot it (the sewers grow their own: pale `inkcaps`, and `sump_caps` on rotten timber, a
  dim yellow-green light), and `cobweb`, `skull_niche`, `winch`, `lever` and `shelf_fungus` mount on
  the nearest wall (`WALL_PROPS`), as does Vesperholm's `moon_window`, a traceried pair of lancets of
  moon-glass and a light (`rise=` hangs it up its wall, `size=` scales it about the wall's face). Its skyline is
  `moon_spire`s (`height=`), landmarks on wall tiles no one walks. Its roofs are `moon_roof`s (the same
  `span=`, `ridge=`, `top=`, `pitch=` and `eave=` as `roof`, on the block's NW corner tile; `grand` makes
  the cathedral's, with a flèche on its ridge). `moon_portal` (`yaw=`, `height=` the wall's top, `rose=`
  the height of the great rose in the roof's gable) is the cathedral's great gate, in the middle tile
  of a doorway three tiles wide; it faces out as a `door_arch` does and blocks nothing. Harrowmere's
  cathedral has its own, `cathedral_portal` (`height=` the wall's top, `rose=` the great rose's height
  in the stone gable it raises over the wall, `gable=` and `span=` that gable's height and foot), set
  the same way. Its stairs are `grand_stair` and `stair_flight` (`run=` tiles, `rise=` metres each tile
  drops, `steps=` steps to a tile, `width=` tiles across, `offset=` metres across to centre it, `yaw=`
  the way it goes down): on the top tile, fine steps drawn over stair tiles that each sit `rise` below
  the last, a tile's floor its lowest step, so the top step meets the floor above. `grand_stair` adds
  raking balustrades on cheek walls either side (wall tiles whose `top=` is that tile's top step),
  newels with lanterns at its head (it is a light) and urns at its foot. Vesperholm's `moon_stair` takes
  the same `run=`, `rise=`, `steps=` and `width=` on the same footprint, in moonstone and silver (see
  `rendering.md`). `nave_runner` (`length=`
  tiles toward -X, `ends=head,foot` for its fringes) is laid in stretches, one to a bake chunk.
  `lever model=wood` is the jungle's wooden lever.
  Every `banner`, in every map, is the realm's crimson, the city's red (`parts.REALM_CRIMSON`) and carries its crest (`parts.realm_crest`: a lone watchtower dark
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
  Every house's `door_arch` (all but a `rose` one, or one marked `open`) hangs a `house_door`
  (`world.hinged`): shut whenever the map loads, never saved; interact swings it open or shut (`World.swing_door`,
  which won't shut it on anyone in the doorway), and shut it fills its tile.
  `chest model=iron` is the Cinderhold's iron chest (`models.chest` style), and `mimic model=iron` hides as
  one (`Enemy.look`); the wooden chests also come `model=worn` (weathered, roped shut), `banded` (dark wood
  strapped in iron) and `coffer` (a small brass-cornered strongbox), every style a key of `models.CHEST_SHELLS`. Opened, every chest is hollow (`models._chest_body`): a bottom and plank walls lined in darker wood, a batten round the inside of its rim and a crumpled cloth on its floor, its bands and ropes running only round the outside (`models._belt`), and battens or straps under its lid (`models._lid_inside`); shut, its body stays one block (`test_an_open_chest_is_hollow_with_a_bottom`). An exit's `model=` draws its way through (`road_gate` for both ends of the north road (each stands out in the open before its wall, never sunk between rock: a pointed arch of soot-black stone, as tall as the Vesper Gate, wrought in iron and fire for the Cinderhold, its joints glowing, an anvil-and-flame crest over the keystone, fire baskets on its piers and cornice, iron leaves swung back and a red haze down the road beyond), `well`, `gaol_grate` (Harrowmere's barred pit, flush with its plaza; like the `well` it fills its tile, so you take it with interact, and it casts no light, so a `light` stands beside it), `cave_mouth`, `keep_door`, `cemetery_gate`, `sewer_grate`, `sewer_ladder`, `vesper_gate` (Vesperholm's, both ends: shut, its
  three sockets dark; open, they shine and moonlight pours through), `chapel_door` (the Vigil Chapel's, both ends: oak leaves strapped in silver under a moonstone arch, a moon rosette over it), else a `rope`, hung from a beam just under its tile's ceiling, so it climbs a tall shaft, with the daylit mouth of the well above it there); each is a landmark of some detail (`test_every_way_between_maps_is_built_in_detail`), and one set against a wall shows black passage through it (`parts.PASSAGE_DARK`), never the wall, so the way on stays unseen; a cold `light` hangs over the cemetery's gate on both sides, and a warm one before the north road's Cinderhold end, so their stone shows. An `exit` with `boss=<dead_flag>` is a way on to a boss on another map: the compass
  points at it while that boss lives (`World.boss_target`), except a lair's `rear` door, reached only
  from inside it. `exit requires=<flag> shut="..."` stays shut
  (saying `shut=`) until that flag is set (`World.exit_open`), and `exit oneway` never leads back: going
  through records the journey on the far side at once, so you wake by its shrines, and sets `left:<map>`
  (`Game._take_exit`). `hint text="Line one.|Line two."` is a tutorial hint, not a prop (`world/hints.py`):
  put its marker on every tile of the way past it, keep it to two lines that fit the screen
  (`test_every_cemetery_hint_fits_the_screen`).
  `region name="Sallow Fen"` names a part of a map, not a prop (`world/regions.py`): lay a band of markers
  on either side of each border, each band naming its own side (`on=` keeps the floor under it). Crossing
  onto a band of another region raises its name as the area card does between maps, and the area card on
  arrival names the region of the nearest marker, so the bands must sit where the nearest one is always on
  your side. A map without markers is one region, its `[meta] name`.
  Breakables (`barrel`, `crate`, `urn`, `cocoon`) spill loot from `world/loot.py` (`loot.roll`); a barrel or
  crate takes one of several looks from its tile (`models.variant`: a cask, a water butt or a cask on its
  side; a plank crate, a slatted one or a long strapped one), so the same marker never repeats one model.
  Smashed, one is broken at once (`open_t` 1: its loot, its tile and the save), while its pieces fly out
  over `BREAK_TIME` (`Prop.break_t` 0 to 1; 1 for one loaded broken) to lie as its wreck
  (`models._flung`, `_break_dust`); a `secret_wall`
  takes the texture of the real walls beside it (`world_view.secret_wall_tex`), a shade duller, with a faint
  shimmer climbing it now and then and pale motes on its faces within `SHIMMER_NEAR`; struck, ember
  cracks sear it to ash and it crumbles top-down into falling ash and embers over about 1.4 s
  (`models.secret_wall`), letting you through at once (`model=vines top=6` matches the jungle's vine walls; `model=web` is a sheet of
  silk that blades can't cut and only fire burns: Pyre, a fiery art, or a Flame Bolt that strikes it;
  it burns away over about two seconds, `models.burning_web`, but lets you through at once). `door boss=<dead_flag>` is a boss's great door
  (`models.boss_door`, dressed for its boss by `BOSS_DOORS` / `DOOR_ARCHES` / `DOOR_LEAVES`, keyed by
  the `dead_flag`; a new boss door needs an entry in each): the arena behind it seals once you are inside with its boss awake, opens when
  the boss dies, and after you die in there becomes a fog gate (`models.fog_gate`) the boss walks
  through freely and you cross with interact: you walk through it slowly (`World.fog_walk`, `FOG_WALK_SPEED`), never jump. Each arena must stay closed behind its one door
  (`tests/test_arena.py`). `door boss=<dead_flag> great=n|s|e|w` makes it the boss's great gate
  (`models.GREAT_GATES`, only the Keystone's has one: `sunken_models.great_keystone_gate`), its facade
  turned to the side named, the way you come to it (`world/great_gate.py`): twice a boss door's height
  (`models.GREAT_DOOR_TOP`, and the fog as tall), its masonry built up to the walls either side of its
  tile (`wall_rise`), and, if the opening runs on between walls (`porch`, Old Harrowmere's notch in the
  court's wall), a ceiling over that porch and the facade at its mouth: buttresses rising from below,
  a stone giant before each bearing up its capital, a round arch, a tympanum carved round the teal core,
  a pediment over the walls' top. It takes its light from out before its facade. Only its look changes:
  it fills its one tile, blocks, seals, opens and fogs as any boss door (`tests/test_great_gate.py`). `door from=n|s|e|w` is barred on that side: it
  only opens from there. `door model=iron` is the Cinderhold's riveted iron door, set in a stone frame
  that rises to the passage's ceiling (`world_view.DOOR_FRAME_SKY` under the open sky); `door model=stone`
  is Old Harrowmere's (`sunken_models.stone_door`): a carved sandstone slab with a small teal glyph on
  each face, set in a frame of `sunken_brick` with a lintel and keystone, that sinks into the floor as it
  opens. Both open, shut and block exactly as the plain wooden door does.
  An `npc` may set `reach=` (metres): how far away it can be spoken to, through a cell's bars. After placing props in `abandoned_prison.map`, run `tests/test_world.py`: its reachability test fails if
  anything cuts off a chest, door, lever, exit, altar or the iron maiden, or if a locked lift is
  needed to get anywhere (shortcuts must stay optional). `verdant_hollow.map` has its
  own solvability test (counting planks, ledges and floorboards as footing, and decor as solid): every
  chest, lever and the boss must be reachable without barred doors, locked lifts or drawbridges, each
  of those must join two places already reachable, and every drop must have a way back.
  `cinderhold.map` has one too (`test_cinderhold_is_solvable`, lava counted as impassable), and so does
  `cinder_keep.map` (`test_cinder_keep_is_solvable`; `test_cinder_keep_roof_is_walled_in` keeps every wall
  round the rooftop at least 6 m above it), `vesperholm.map` (`test_vesperholm_is_solvable`: every
  chest and the lever over the Glass Bridge, the Duchess only through her door, Lyra's altar only
  through both of her choir's doors, the great bridge a
  shortcut between two places you can already reach), and `ashen_cemetery.map` (`test_ashen_cemetery_is_solvable_in_order`:
  the sword before any foe, the scroll before the silk, the gate only behind the Sexton, and no way
  back from town). Their tiles are lowercase letters, digits and punctuation and
  their entity markers uppercase or Latin-1, so the two never collide; keep it that way.
- Shots stop at a blocking prop only below its top (`world.PROP_TOP`, `shots.clears`): a bolt flies
  over tables, caskets and barrels. A low prop not listed there counts as full height.
