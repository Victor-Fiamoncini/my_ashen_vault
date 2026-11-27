# Smoke-run starts

Ready-made `--map` / `--at` / `--script` starts for checking a place or a fight. The basics of smoke runs are in AGENTS.md.

- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first. A prop more than `world.INTERACT_RISE` (2 m) above or below your feet
  is out of reach.
- The `smoke:` line includes the player's height (`y=`), handy for checking lifts.
- Ailment borders: `--map abandoned_prison --at 15,21,180 --smoke 60 --afflict
  bleed,corrosion,poison,toxic,rot,frost` shows them all combined; bleed's and corrosion's last only
  `ailments.FLARE_TIME` (2.5 s), so keep `--smoke` under 150 frames for those.
- The Abandoned Prison (`abandoned_prison`): `--map abandoned_prison` (its `start`, in the gaol's shaft
  at the foot of the ladder; `--at=15,32,90 --script "back:0.3 look_up:0.5"` looks up the shaft at the grate;
  `--at=15,32,90 --script "wait:0.3 interact wait:1.5"` climbs the ladder back to the gaol yard, beside the grate),
  `--at=15,21,90` (the guard hall), `--at=4,23,-90` (the west cell block's dark aisle; `--at=4,16,-90
  --script "wait:0.2 interact wait:2"` pulls its lever and raises every cell's bars), `--at=22,21,90
  --script "forward:0.6 wait:0.2 interact"` (Brother Marrow, through his cell's bars), `--at=32,21,0`
  (the chapel of the old gods from its door; `--at=40,21,0` its altar and the Warden's Key).
- Useful starts: `--at 4,24,90 --script "forward:0.15 wait:5 forward:0.6 wait:5.5"` (step onto the
  landing's call plate to bring the Cistern lift up, then onto its deck's plate and ride 10 m down to the Undercroft), `--at=11,26,90 --script
  "strafe_l:0.7 wait:5"` (ride the shrine lift up, which frees it), `--at=13,26,180 --script "wait:0.2
  forward:0.2"` (its call plate above, refusing while it is still fastened), `--at=23,13,0 --script "forward:0.7 wait:5"` (the cage lift up to the Warden's Gallery),
  `--at=27,7,-90` (the Butcher in his slaughter hall north of the Gallery),
  `--map harrowmere --at=47,23,0` (the hedged jungle trail past the east gate; `--at=56,27,-90` its dark end at the cave
  mouth), `--map verdant_hollow`
  (Mossmouth, the dark cave you arrive in), `--at=15,31,180 --equip left=spell:pyre --script "cast"`
  (kindle Mossmouth's cold brazier), `--at=6,41,-90` (the Root Caverns), `--at=32,3,180` (the Canopy
  Walk), `--at=15,20,-90 --script interact` (the barred door, from its wrong side),
  `--at=14,41,-90 --script "interact wait:2.5 strafe_l:2"` (lower the drawbridge and cross),
  `--at=49,12,-90` (the Highland log slope), `--at=15,7,-90` (the Loom Mother),
  `--at=15,7,-90` (the Ashen Warden in his hall), `--map harrowmere --at=20,20,-90 --script "wait:0.2
  interact"` (Odrin's dialogue box, by the Silent Bell), `--map harrowmere --at=23,20,90 --script
  "forward:0.6 interact"` (touch the Silent Bell; `world.INTERACT_REACH` lets you reach it from its plinth), `--map harrowmere --at=8,7,180 --script "wait:0.2 interact wait:1
  forward:2.5 interact"` (open the hut's door and walk in to Corvane; below `--level 5` they stay silent), `--map harrowmere --at=10,4,-90` (the north road's gate),
  `--map harrowmere --at=23,33,-90` (across the plaza to the bell and the cathedral on its terrace),
  `--map harrowmere --at=24,33,0` (the market's fountain and stall by the south street), `--map harrowmere
  --at=23,19,-90 --script "look_up:0.3"` (the cathedral's grand stair, great door and rose window),
  `--map harrowmere --at=10,7,180 --script "look_up:0.1"` (Corvane's hut on the north road's street, its sign
  and its shuttered windows), `--map harrowmere --at=11,30,180 --script "forward:3"` (walk to the watch
  office's thin wall: you stop at its slab), `--map harrowmere --at=23,10,-90` (the cathedral's nave;
  `--at=23,5,-90 --script "wait:0.2 interact"` speaks to the Enthroned), `--map harrowmere --at=6,15,180 --script
  "wait:0.2 interact"` (Brannoc's gift and forge), `--map harrowmere --at=9,15,-90 --script "look_up:0.3"` (the anvil
  sign by his forge; `--at 11,15,180` faces its door between two windows), `--map harrowmere --at 41,3,-90 --script "wait:0.2 interact"` (Corporal Wynn of the watch, by the
  Vesper Gate; `--at=40,12,-90` looks up the Vesper street at the gate between its lamps),
  `--map harrowmere --at=38,14,180 --script "wait:0.2 interact wait:1"` (open Pell's door; `interact` again shuts
  it), `--map harrowmere --at=12,22,90` (the gaol yard's gate, the barred pit and Hollis inside;
  `--at=12,25,90 --script "wait:0.3 interact wait:1.5"` descends the grate into the prison), `--map harrowmere
  --at=8,29,180 --script "wait:0.2 interact wait:0.8 forward:0.5"` (into the watch office, Garrick at his
  table), `--map harrowmere --at=19,10,90` (from the cathedral's terrace down over the plaza and the clay roofs),
  `--map harrowmere --at=23,38,90 --script "forward:2.5"` (out through the sea gate onto the quay, the pier
  ahead and Maeve at its end), `--map harrowmere --at=36,31,-90 --script "wait:0.2 interact"` (the
  neighbourhood's lane: Jorun's lines, the homes round her), `--map harrowmere --at=44,23,0` (the east gate,
  Reyna beside it),
  `--map cinderhold` (its `start`: the Sallow Fen's foot, the north road behind you), `--map cinderhold
  --at=30,102,-90` (the dirt path north from the watch-post shrine, the mounds and great dead trees round it),
  `--map cinderhold --at=29,96,-90 --script forward:3` (over the great rotten bridge's rotting planks to the
  great square; `--script "wait:0.3 forward:1 wait:3"` stops on a plank, which sinks into the fouled pool), `--map cinderhold --at=10,88,-90 --script
  "wait:0.3 interact"` (smother the west beacon; the others stand at 49,91 and 46,75),
  `--map cinderhold --at=27,103,180` (down the west sunken way to the west beacon), `--map cinderhold
  --at=45,89,-90 --flags lever:fen_causeway` (up the north-east sunken way to the Mire Tyrant's island),
  `--map cinderhold --at=31,80,-100 --script "look_up:0.25"` (the great fen gate in the curtain wall; add
  `--flags lever:fen_beacons` to see it raised),
  `--map cinderhold --at=39,78,0 --level 8` (the Mire Tyrant on the north island), `--map cinderhold
  --at=30,72,-90 --flags lever:fen_beacons --smoke 230 --script "wait:0.3 forward:2.6"` (through the open fen gate
  onto the Gargoyle Way: the card reads "The Cinderhold"), `--map cinderhold --at=30,63,-90` (up the Gargoyle
  Way to the long bridge), `--map cinderhold --at=29,62,0` (the wayside shrine's court),
  `--map cinderhold --at=30,88,-90 --smoke 200 --script "wait:0.3 interact"` (the moot's rotten lever: both
  rotten drawbridges swing down), `--map cinderhold --at=29,85,-90 --flags lever:fen_causeway --script forward:6`
  (the dry way north over the lowered span to the north island),
  `--map cinderhold --at=29,52,-90 --script "look_up:0.15"` (the long bridge and the fortress's skyline), `--map cinderhold --at=28,30,180`
  (the postern ledge and its flame jets), `--map cinderhold --at=18,17,180` (the foundry),
  `--map cinderhold --at=5,24,0` (the smelter pits), `--map cinderhold --at=47,3,180 --script interact`
  (the door at the top of the tower stair, into the keep), `--map cinder_keep --at=17,18,180` (the keep's
  great hall), `--map cinder_keep --at=9,6,180 --level 10`
  (the keep's walled roof: the gargoyles wake at once).
- The Harrow Sewers (`harrow_sewers`) lie under the town; each town grate stands over the sewer ladder that
  climbs back to it, at the same tile, one in each corner of the town: `--map harrowmere --at=3,2,180 --script
  "wait:0.3 interact"` (go down the north-west grate, by the north road's gate; the others are at 45,2 by the
  Vesper Gate, 3,37 and 45,39 at the south lane's west and east ends), `--map harrow_sewers
  --at=2,3,-90 --script "wait:0.3 interact"` (climb back up by the north road). Districts: `--map
  harrow_sewers` (the drain into the Market Drains, its `start`), `--at=27,6,0`
  (the North Sluices), `--at=4,36,0` (the Canal Culvert), `--at=36,36,90` (the Quay Outfall and its
  great grates), `--at=25,24,-120` (the Cistern, its shrine at 20,16), `--at=43,25,-120` (the Sump, 8 m down
  the outfall's U-turn stair from 45,35; the lift up to the Cistern at 36,20), `--at=26,36,180 --script "wait:0.2 interact wait:2.5"` (let the sluice pit's
  drawbridge down). Bosses: `--at=34,32,-160 --level 10 --script "wait:3.2"` (Mother Gnawl rising in her
  nest, its great doors at 29,28 and 33,34; `--at=29,27,90 --script "interact wait:1 forward:1.5"` walks in
  through the north one), `--at=41,13,-90 --level 10 --script "wait:4.5"` (the Sodden Pall behind its door at 41,15).
- Old Harrowmere (`old_harrowmere`) lies below the Sodden Pall's cistern, through the breach at 41,4 in its
  north wall: `--map harrow_sewers --at=41,5,-90 --flags pall_dead --script "wait:0.3 interact"` (go down;
  without the flag it says it is shut). Tiers: `--map old_harrowmere` (the Breach Landing, its `start`, the
  shrine at 6,6), `--at=13,5,50 --script "look_down:0.5"` (the overlook: the chasm, the towers and the lit
  plaza far below), `--at=13,5,50 --script "look_up:0.5"` (the vault overhead), `--at=12,27,0 --script
  "look_up:0.9"` (the rift of daylight in the vault), `--at=15,3,0` (the Cliff Stair, a sexton and a golem on it), `--at=32,3,180` (the
  terrace), `--at=31,9,90` (the bridge to the Bell Tower), `--at=24,12,180` (the Aqueduct), `--at=15,12,180`
  (the Colonnade), `--at=15,24,40` (the Drowned Plaza under the rift), `--at=7,38,90` (the lift
  head at the gallery's end, fastened until ridden from below); the rune lift from the lift room below:
  `--at=7,42,-90` (resting cold, its near call plate lit), `--at=7,42,-90 --smoke 220 --script "forward:1.85 wait:0.3
  back:0.12 look_down:1.4 wait:8"` (riding up, its glyphs ablaze), `--smoke 900` with the same script (freed at the
  top, its glyphs dim). Boss: `--at=22,39,90 --level 10 --script
  "wait:4.5"` (the Keystone rising in its court; its doors at 21,38 and 12,42); `--at 21,31,90 --script
  "look_up:0.25"` (its great gate across the chasm, from the plaza), `--at 21,37,90 --flags keystone_dead
  --smoke 60 --script "wait:0.2 interact wait:0.4 back:0.4"` (the gate opening), `--at 30,46,200 --flags
  keystone_dead --script "look_up:0.15"` (the court's colossal pillars up to the vault); `--at=30,43,180 --level 10 --script
  "wait:4.6"` sees the whole titan and its torch down the court's clear row, between the pillars;
  `--at=22,39,90 --level 10 --smoke 480 --script "wait:4.5 back:1.5"` catches its first torch smash
  bursting before it; `--at=22,39,90 --level 10 --smoke 150 --script "wait:2"` its wide spread of ash
  drawn in mid-rise. From `--at=30,43,180 --level 10 --script "wait:30"`, about `--smoke 680` shows its
  first fault line glowing down the court at you (a sidestep, `right:0.9` from 10.6 s, lets you live on
  to see more of it); the boulder (`hurl`), the fists (`pillar_crush`) and the rest come at random. The lift head's empty shaft, `--at=7,38,90 --script "wait:0.3 forward:1.2"`, is a
  22 m fall you watch to the bottom (about 110 frames). The rift and its falls: `--at=14,29,0 --script "look_up:0.8"`
  (up to the rift), `--at=16,23,0` (a fall past the Grand Stair),
  `--at=22,24,-90 --script "look_down:0.5"` (one plunging into the chasm). The Oubliette:
  `--at=3,9,0 --equip right=torch_greathammer --level 9 --smoke 420 --script "attack wait:2.5 forward:1.6"`
  (break the gallery's false wall and step in, the hammer lighting the dark), `--at=7,9,90 --flags
  secret_wall:old_harrowmere:4,9` (down its corridor of cells), `--at=7,11,180 --flags
  secret_wall:old_harrowmere:4,9 --script "wait:0.5 interact"` (Aubel through his bars; add
  `lever:oubliette` to free them all, and `--at=7,13,180` for Ysolde's shop). The roads of light:
  `--at=31,31,-30` (the gold road out from the plaza to the first island), `--at=36,29,-90 --script
  "wait:0.3 attack"` (strike the first island's crystal: the gold road fades, the pale one wakes);
  `--flags ward:old_harrowmere` starts with the pale road standing, `--flags
  ward:old_harrowmere:c,ward_fed:old_harrowmere` with the teal road standing (the core's shield down).
  The third road: `--at=42,29,0` (the pale road east to the Mortar Sisters' quay), `--at=38,18,-90
  --script "wait:0.3 attack wait:1.2"` (strike the core's shield ward: it feeds and wakes the teal road),
  `--at=38,18,180 --flags ward:old_harrowmere:c,ward_fed:old_harrowmere` (the teal road home to the
  plaza), `--at=17,28,0` (the energy core on the fountain's plinth at 21,28, in the middle of its pool, teal
  lights round the pool). The Mortar Sisters' Workshop: `--at=46,28,0` (from the quay through its arch:
  benches, golems, a sexton; its chest at 60,23). The Under-Cells: `--at=3,18,180` (the gaolers' postern
  across the gallery, barred), `--at=7,17,0 --script "wait:0.3 interact wait:1.5"` (pull the postern's
  lever in the gaoler's hall), `--at=1,44,90 --script "forward:2.5"` (the stair's foot: sets
  `visited_undercells`), `--at=1,52,0` (down the flooded cell block), `--at=17,52,0` (the interrogation
  hall, its gaoler and golem), `--at=32,51,0 --script "wait:0.3 interact wait:1.5"` (the warden's lever:
  every cell front below rises), `--at=31,56,-90 --script "wait:0.5 interact"` (Brannick, in the cell
  beside the office), `--at=43,56,90 --script "wait:0.5 interact"` (Sister Vell, at the flooded deep
  cells' far end).
- The Vigil Chapel (`vigil_chapel`) lies behind the door in Old Harrowmere's lift room, shut until the
  Keystone falls: `--map old_harrowmere --at 8,42,90 --flags keystone_dead --script "look_up:0.2"` (the
  door), `--at 8,44,90 --flags keystone_dead --script "wait:0.3 interact"` (go through; without the flag
  it says it is sealed). In the chapel: `--map vigil_chapel --at=8,19,-90` (down the nave from the
  vestibule), `--at=8,4,-90 --script "look_up:0.25"` (the altar and the Moonbrand in it), `--at=8,2,-90
  --script "wait:0.3 interact"` (take it). The Vesper Ray: `--at=8,20,-90 --equip right=vesper_moonbrand
  --level 10 --smoke 230 --script "wait:1.5 attack:1.6"` (a full heavy, the ray running down the nave).
- Hollow chests: open one and look in, e.g. `--map old_harrowmere --at 10,44,0 --flags keystone_dead
  --smoke 110 --script "forward:0.35 interact wait:0.5 look_down:0.5"` (the Keystone's coffer) or `--map
  cinder_keep --at 3,23,180 --smoke 80 --script "interact wait:0.5 look_down:0.35"` (an iron chest).
- Vesperholm (`vesperholm`) lies behind the Vesper Gate in the east end of Harrowmere's north wall, at the
  head of the Vesper street; it always stands open: `--map harrowmere --at=40,15,-90` (from down the street,
  the gate straight ahead between its lamps), `--map harrowmere --at=40,2,-90 --script "wait:0.3 interact"`
  (goes through, even on a fresh save). Areas: `--map vesperholm` (the Glimmering Cave's hall, its
  `start`, the Vesper Gate behind you), `--at=8,113,-90 --smoke 75 --script "forward:0.75 wait:0.45"` (a
  Glassmite in the geode gallery unfolds), `--at 24,103,0` (the moon-pool grotto), `--at=16,80,-80` (the
  overlook's parapet: the city, the cathedral and the moon), `--at=21,92,-90` (the overlook at the cave's
  mouth, the shrine at 17,91, the grand stair down into the Gate Court), `--at 21,87,90 --script
  "look_up:0.15"` (the cave's mouth from the stair), `--at=21,74,-90` (the Gate Court), `--at=21,63,-90
  --script "look_up:0.5"` (the moon and the stars over Lantern Square, from beside its moon pool),
  `--at=19,52,-70 --script "forward:0.25 look_down:0.7"` (the great bridge sunk on the gorge floor),
  `--at=21,54,-90 --flags lever:vesper_bridge` (the great bridge raised, across to the castle's postern), `--at=4,55,-90` (the west street
  and the Glass Bridge), `--at=21,46,-90 --script "look_up:0.25"` (the cathedral's front from the bailey),
  `--at=21,37,-90` (the nave). A fight: `--at=25,62,-90 --level 6 --equip primary=katana,secondary=buckler
  --script "wait:2.2"` (a Lantern Wraith's lances), `--at=17,41,180 --script "wait:0.9 attack"` (a Veiled
  Knight in the bailey). Shortcut: `--at=20,45,90 --script "wait:0.2 interact wait:2.6 strafe_l:0.45 forward:4.5" --smoke 520`
  (the drawbridge's lever in the bailey; walk out through the gatehouse and over it to the Landing). Boss:
  `--at=21,28,-90 --level 8 --equip primary=katana,secondary=buckler --script "wait:4.2"` (Duchess Ilvane
  rising in her choir behind its great door at 21,29). After her, with `--flags duchess_dead`:
  `--at=31,23,0 --script "interact wait:1.2"` (her choir's back door onto the old stair),
  `--at=33,23,-90 --smoke 240 --script "forward:3.2"` (up the old stair through the wall and its tower),
  `--at=33,17,180` (the flying stair over the drop behind the cathedral, the chapel's crag beyond it),
  `--at=24,17,-90 --script "look_up:0.3"` (the grand stair from the Moon Terrace, the chapel's front at
  its head), `--at=21,8,-90` (Lyra's Chapel: her altar in the nave, the apse behind her),
  `--at=21,6,-90 --script "interact wait:1"` (take the Argent Sigil from Lyra's hands), `--at=22,7,-100 --script "look_up:0.1"` (the portal's
  arch dormant in the apse behind her; add `argent_sigil_taken` to the flags to see it open), `--at=21,10,90`
  (the great windows in the choir's back wall) and
  `--at=27,46,-110 --script "look_up:0.4"` (the chapel's roof over the cathedral's, from the bailey).
- Herran's Castle (`herrans_castle`) is through the portal behind Lyra's altar in Vesperholm, there
  only once the Argent Sigil is taken: `--map vesperholm --at=21,3,-90 --flags duchess_dead,argent_sigil_taken
  --script "wait:0.3 interact"` (go through; without the flag nothing stands there). Areas: `--map
  herrans_castle` (the Portal Ledge, its `start`), `--at=19,72,-90 --script "look_up:0.25"` (the Long
  Causeway, the towers and the Hollow Peak beyond), `--at=19,44,-90` (the sealed gate, its two eyes
  burning; `--flags` can't name the Wardens' `slain:` flags, whose tile holds a comma, so
  `tests/test_herrans_castle_world.py` checks it opening),
  `--at=13,40,180` (a Castellan Warden on its tower's deck), `--at=19,33,-90` (the Outer Ward),
  `--at=19,23,-90 --script "look_up:0.2"` (the Great Hall), `--at=10,8,90` (the library's false wall;
  `attack` it), `--at=20,5,0` (Herran's study and its shrine), `--at=25,10,-40 --flags herran_dead --script
  "look_up:0.5"` (the iron cage over the anatomy theatre), `--at=34,1,0 --flags herran_dead` (Herran's
  telescope). The laboratory: `--map herran_laboratory`
  (the vat cellar), `--at=5,8,180` (the dissecting rooms), `--at=27,8,0` (the menagerie),
  `--at=16,16,90` (the ossuary of hands), `--at=16,24,90` (Herran's own laboratory). Fights: `--map
  herrans_castle --at=10,18,180 --level 12 --equip right=claymore,body=brigandine --smoke 480 --script
  "interact wait:0.8 forward:1.6 wait:3"` (the Hall of Sentinels: the two stone giants tear free),
  `--map herrans_castle --at=23,5,0 --level 12 --equip right=claymore,body=brigandine --smoke 520 --script
  "interact wait:0.8 forward:1.4 wait:5.5"` (through his door; Herran rising before it, facing you). The
  ending: `--map harrowmere --at=23,24,-90 --flags bell_unsealed --script "wait:0.5 interact"` (the bell
  refuses without the five sigils in hand).
- The story begins in `ashen_cemetery` (the title's New Game, `Game.start_story`: bare hands and no
  spell, `Player.woken()`, the journey recorded at once). A `--map` run starts on any map with the default
  kit instead: `--map ashen_cemetery` (the waking grave and the first hint), `--map ashen_cemetery
  --at=10,19,-90 --script "wait:0.3 cast"` (burn the chapel's silk with Flame Bolt), `--map
  ashen_cemetery --at=10,3,-90 --script "wait:0.1 interact"` (the gate out, refusing while the
  Sexton lives). Without `--map`, `--script "wait:0.3 confirm confirm"` presses New Game on the title
  and picks the first empty slot in the chooser (with a throwaway save that doesn't exist yet).
- Boss doors: `--map abandoned_prison --at=15,11,-90` faces the Warden's great door, `--at=28,10,-116` the
  Butcher's, `--map verdant_hollow --at=15,11,-90` the Loom Mother's, `--map cinder_keep --at=22,5,180`
  the gargoyles', `--map ashen_cemetery --at=10,11,-90` the Sexton's, `--map vesperholm --at=21,31,-90` the Duchess's, `--map herrans_castle --at=10,18,180` the sentinels', `--at=23,5,0` Herran's. The fog appears only
  after dying in a sealed arena (or with its `fog:` flag set); `tests/test_arena.py` drives the flow.
- `--level` only sets the level (for equipment requirements); HP and stats stay at level 1, so judge boss
  balance headless (`World` with a `JungleGame`) rather than from a smoke fight.
- The world's skyline (`world/atlas.py`): `--map harrowmere --at=24,49,70` (from the pier: the harbour light, a wreck and
  the headlands either side of the sea), `--map harrowmere --at=23,33,-110 --script "look_up:0.15"` (the
  volcano's smoke in the north-west over the roofs), `--map vesperholm --at=16,80,-45` (the Hollow Peak under
  its storm north-east of the city), `--map vesperholm --at=21,63,180 --script "look_up:0.2"` (the volcano's
  plume in the west over Lantern Square), `--map cinderhold --at=30,100,-60` (the peak's storm over the
  fen's curtain wall) and `--at=30,96,10` / `--at=26,96,170` (the burnt hills over the fen's crags).
  Harrowmere's dressing: `--map harrowmere --at=11,33,-90 --script "look_up:0.3"` (washing between the
  watch office and Wren's house), `--at=32,43,60 --script "look_up:0.25"` (the harbour light, from the quay),
  `--at=26,29,0` (a market stall). The fen's:
  `--map cinderhold --at=20,74,-90 --script "look_up:0.2"` (a runoff sluice in the curtain wall),
  `--at=37,104,20` (the fallen watchtower).
