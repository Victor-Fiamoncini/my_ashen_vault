# Smoke-run starts

Ready-made `--map` / `--at` / `--script` starts for checking a place or a fight. The basics of smoke runs are in AGENTS.md.

- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first.
- The `smoke:` line includes the player's height (`y=`), handy for checking lifts.
- Ailment borders: `--map abandoned_prison --at 15,21,180 --smoke 60 --afflict
  bleed,corrosion,poison,rot,frost` shows them all combined; bleed's and corrosion's last only
  `ailments.FLARE_TIME` (2.5 s), so keep `--smoke` under 150 frames for those.
- The Abandoned Prison (`abandoned_prison`): `--map abandoned_prison` (its `start`, in the gaol's shaft
  at the foot of the ladder; `--at=15,32,90 --script "back:0.3 look_up:0.5"` looks up the shaft at the grate;
  `--at=15,32,90 --script "wait:0.3 interact wait:1.5"` climbs the ladder back to the Gaol Ward, beside the grate),
  `--at=15,21,90` (the guard hall), `--at=4,23,-90` (the west cell block's dark aisle; `--at=4,16,-90
  --script "wait:0.2 interact wait:2"` pulls its lever and raises every cell's bars), `--at=22,21,90
  --script "forward:0.6 wait:0.2 interact"` (Brother Marrow, through his cell's bars), `--at=32,21,0`
  (the chapel of the old gods from its door; `--at=40,21,0` its altar and the Warden's Key).
- Useful starts: `--at 4,24,90 --script "forward:0.15 wait:5 forward:0.6 wait:5.5"` (step onto the
  landing's call plate to bring the Cistern lift up, then onto its deck's plate and ride 10 m down to the Undercroft), `--at=11,26,90 --script
  "strafe_l:0.7 wait:5"` (ride the shrine lift up, which frees it), `--at=13,26,180 --script "wait:0.2
  forward:0.2"` (its call plate above, refusing while it is still fastened), `--at=23,13,0 --script "forward:0.7 wait:5"` (the cage lift up to the Warden's Gallery),
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
  `--map harrowmere --at=22,30,-60` (the Bell Square), `--map harrowmere --at=28,37,-90` (the market's fountain
  and benches), `--map harrowmere --at=31,6,180` (the cathedral's great stair, west door and rose window),
  `--map harrowmere --at=8,25,-90 --script "look_up:0.1"` (a house's face, its balcony and the cathedral's
  towers behind), `--map harrowmere --at=14,33,-90 --script "forward:3"` (walk to a thin wall's slab:
  you stop at z=62.9), `--map harrowmere --at=17,6,180` (the cathedral's nave;
  `--at=6,6,180 --script "wait:0.2 interact"` speaks to the Enthroned), `--map harrowmere --at=7,18,180 --script
  "wait:0.2 interact"` (Brannoc's gift and forge), `--map harrowmere --at=10,18,-90 --script "look_up:0.3"` (the anvil sign by his forge),
  `--map harrowmere --at=10,33,180 --script "wait:0.2 interact wait:1"` (open Pell's door; `interact` again shuts it), `--map harrowmere --at=38,17,-90` (the Gaol Ward's plaza, the gaol's grate and Hollis beside it;
  `--at=38,14,-90 --script "wait:0.3 interact wait:1.5"` descends the grate into the prison), `--map harrowmere
  --at=28,22,-90` (the north road's stair up to the Gaol Ward, under its crenellated arch), `--map harrowmere
  --at=12,11,60` (from the cathedral's terrace over the clay roofs), `--map harrowmere --at=30,39,180` (the
  harbour, Tamsin's hipped roof behind), `--map harrowmere --at=43,29,0` (the east lane up to the gap, Garrick
  on its corner),
  `--map cinderhold --at=29,52,-90 --script "look_up:0.15"` (the long bridge and the fortress's skyline), `--map cinderhold --at=28,30,180`
  (the postern ledge and its flame jets), `--map cinderhold --at=18,17,180` (the foundry),
  `--map cinderhold --at=5,24,0` (the smelter pits), `--map cinderhold --at=47,3,180 --script interact`
  (the door at the top of the tower stair, into the keep), `--map cinder_keep --at=17,18,180` (the keep's
  great hall), `--map cinder_keep --at=9,6,180 --level 10`
  (the keep's walled roof: the gargoyles wake at once).
- The Harrow Sewers (`harrow_sewers`) lie under the town; each town grate stands over the sewer ladder that
  climbs back to it, at the same tile: `--map harrowmere --at=2,14,180 --script "wait:0.3 interact"`
  (go down the west lane's grate, under the cathedral terrace; the others are at 35,1 in the north road's
  corner by its gate, 3,37 at the harbour lane's west corner and 39,40 on the quay), `--map harrow_sewers
  --at=35,2,-90 --script "wait:0.3 interact"` (climb back up by the north road). Districts: `--map
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
  head at the gallery's end, fastened until ridden from below). Boss: `--at=22,39,90 --level 10 --script
  "wait:4.5"` (the Keystone rising in its court; its doors at 21,38 and 12,42); `--at=30,43,180 --level 10 --script
  "wait:4.6"` sees the whole titan and its torch down the court's clear row, between the pillars;
  `--at=22,39,90 --level 10 --smoke 480 --script "wait:4.5 back:1.5"` catches its first torch smash
  bursting before it. The lift head's empty shaft, `--at=7,38,90 --script "wait:0.3 forward:1.2"`, is a
  22 m fall you watch to the bottom (about 110 frames). The rift and its falls: `--at=14,29,0 --script "look_up:0.8"`
  (up to the rift), `--at=16,23,0` (a fall past the Grand Stair),
  `--at=22,24,-90 --script "look_down:0.5"` (one plunging into the chasm). The Oubliette:
  `--at=3,9,0 --equip right=torch_greathammer --level 9 --smoke 420 --script "attack wait:2.5 forward:1.6"`
  (break the gallery's false wall and step in, the hammer lighting the dark), `--at=7,9,90 --flags
  secret_wall:old_harrowmere:4,9` (down its corridor of cells), `--at=7,10,180 --flags
  secret_wall:old_harrowmere:4,9 --script "wait:0.5 interact"` (Aubel through his bars; add
  `lever:oubliette` to free them all, and `--at=7,12,180` for Ysolde's shop). The roads of light:
  `--at=31,31,-30` (the gold road out from the plaza to the first island), `--at=36,29,-90 --script
  "wait:0.3 attack"` (strike the first island's crystal: the gold road fades, the pale one wakes);
  `--flags ward:old_harrowmere` starts with the pale road standing, `--flags
  ward:old_harrowmere:c,ward_fed:old_harrowmere` with the teal road standing (the core's shield down).
  The third road: `--at=42,29,0` (the pale road east to the Mortar Sisters' quay), `--at=38,18,-90
  --script "wait:0.3 attack wait:1.2"` (strike the core's shield ward: it feeds and wakes the teal road),
  `--at=38,18,180 --flags ward:old_harrowmere:c,ward_fed:old_harrowmere` (the teal road home to the
  plaza), `--at=17,27,0` (the energy core on the fountain's plinth at 21,27, beside the shaft's foot, teal
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
- Vesperholm (`vesperholm`) lies behind the Vesper Gate in Harrowmere's north wall, at the head of the
  cathedral steps; it always stands open: `--map harrowmere --at=22,15,-90` (from the foot of the steps,
  the gate straight ahead up the porch), `--map harrowmere --at=22,2,-90 --script "wait:0.3 interact"`
  (goes through, even on a fresh save). Areas: `--map vesperholm` (the Gate Court, its `start`, the shrine at 16,50), `--at=21,43,-90
  --script "look_up:0.5"` (the moon and the stars over Lantern Square, from beside its moon pool),
  `--at=21,33,-90` (the Landing, the raised drawbridge across the gorge), `--at=4,35,-90` (the west street
  and the Glass Bridge), `--at=21,26,-90 --script "look_up:0.25"` (the cathedral's front from the bailey),
  `--at=21,17,-90` (the nave). A fight: `--at=25,42,-90 --level 6 --equip primary=katana,secondary=buckler
  --script "wait:2.2"` (a Lantern Wraith's lances), `--at=17,21,180 --script "wait:0.9 attack"` (a Veiled
  Knight in the bailey). Shortcut: `--at=20,25,90 --script "wait:0.2 interact wait:2.6 strafe_l:0.45 forward:4.5" --smoke 520`
  (the drawbridge's lever in the bailey; walk out through the gatehouse and over it to the Landing). Boss:
  `--at=21,8,-90 --level 8 --equip primary=katana,secondary=buckler --script "wait:4.2"` (Duchess Ilvane
  rising in her choir behind its great door at 21,9).
- The story begins in `ashen_cemetery` (the title's New Game, `Game.start_story`: bare hands and no
  spell, `Player.woken()`, the journey recorded at once). A `--map` run starts on any map with the default
  kit instead: `--map ashen_cemetery` (the waking grave and the first hint), `--map ashen_cemetery
  --at=10,19,-90 --script "wait:0.3 cast"` (burn the chapel's silk with Flame Bolt), `--map
  ashen_cemetery --at=10,3,-90 --script "wait:0.1 interact"` (the gate out, refusing while the
  Sexton lives). Without `--map`, `--script "wait:0.3 confirm confirm"` presses New Game on the title
  and picks the first empty slot in the chooser (with a throwaway save that doesn't exist yet).
- Boss doors: `--map abandoned_prison --at=15,11,-90` faces the Warden's great door, `--at=28,10,-116` the
  Butcher's, `--map verdant_hollow --at=15,11,-90` the Loom Mother's, `--map cinder_keep --at=22,5,180`
  the gargoyles', `--map ashen_cemetery --at=10,11,-90` the Sexton's, `--map vesperholm --at=21,11,-90` the Duchess's. The fog appears only
  after dying in a sealed arena (or with its `fog:` flag set); `tests/test_arena.py` drives the flow.
- `--level` only sets the level (for equipment requirements); HP and stats stay at level 1, so judge boss
  balance headless (`World` with a `JungleGame`) rather than from a smoke fight.
