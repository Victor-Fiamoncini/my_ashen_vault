# Smoke-run starts

Ready-made `--map` / `--at` / `--script` starts for checking a place or a fight. The basics of smoke runs are in AGENTS.md.

- `interact` uses whatever the player faces within reach, nearest first: an unopened chest in front of
  another prop is opened first.
- The `smoke:` line includes the player's height (`y=`), handy for checking lifts.
- The Abandoned Prison (`abandoned_prison`): `--map abandoned_prison` (its `start`, in the well's shaft
  under the rope; `--at=15,32,90 --script "back:0.3 look_up:0.5"` looks up the shaft at the well's mouth),
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
  and benches), `--map harrowmere --at=23,6,180` (the cathedral's west door and rose window),
  `--map harrowmere --at=8,25,-90 --script "look_up:0.1"` (a house's face, its balcony and the cathedral's
  towers behind), `--map harrowmere --at=14,33,-90 --script "forward:3"` (walk to a thin wall's slab:
  you stop at z=62.9), `--map harrowmere --at=17,6,180` (the cathedral's nave;
  `--at=6,6,180 --script "wait:0.2 interact"` speaks to the Enthroned), `--map harrowmere --at=7,18,180 --script
  "wait:0.2 interact"` (Brannoc's gift and forge), `--map harrowmere --at=10,18,-90 --script "look_up:0.3"` (the anvil sign by his forge),
  `--map harrowmere --at=10,33,180 --script "wait:0.2 interact wait:1"` (open Pell's door; `interact` again shuts it), `--map harrowmere --at=37,20,0` (the sunken well court),
  `--map cinderhold --at=29,52,-90 --script "look_up:0.15"` (the long bridge and the fortress's skyline), `--map cinderhold --at=28,30,180`
  (the postern ledge and its flame jets), `--map cinderhold --at=18,17,180` (the foundry),
  `--map cinderhold --at=5,24,0` (the smelter pits), `--map cinderhold --at=47,3,180 --script interact`
  (the door at the top of the tower stair, into the keep), `--map cinder_keep --at=17,18,180` (the keep's
  great hall), `--map cinder_keep --at=9,6,180 --level 10`
  (the keep's walled roof: the gargoyles wake at once).
- The Harrow Sewers (`harrow_sewers`) lie under the town; each town grate stands over the sewer ladder that
  climbs back to it, at the same tile: `--map harrowmere --at=15,25,-90 --script "wait:0.3 interact"`
  (go down the market's grate; the others are at 27,5 by the north road, 7,37 at the canal's head and
  39,40 on the quay), `--map harrow_sewers --at=27,6,-90 --script "wait:0.3 interact"` (climb back up
  by the north road). Districts: `--map harrow_sewers` (the Market Drains, its `start`), `--at=27,6,0`
  (the North Sluices), `--at=4,36,0` (the Canal Culvert), `--at=36,36,90` (the Quay Outfall and its
  great grates), `--at=25,24,-120` (the Cistern, its shrine at 20,16), `--at=43,25,-120` (the Sump, 8 m down
  the outfall's U-turn stair from 45,35; the lift up to the Cistern at 36,20), `--at=26,36,180 --script "wait:0.2 interact wait:2.5"` (let the sluice pit's
  drawbridge down). Bosses: `--at=34,32,-160 --level 10 --script "wait:3.2"` (Mother Gnawl rising in her
  nest, its great doors at 29,28 and 33,34; `--at=29,27,90 --script "interact wait:1 forward:1.5"` walks in
  through the north one), `--at=41,13,-90 --level 10 --script "wait:4.5"` (the Sump Maw behind its door at 41,15).
- Vesperholm (`vesperholm`) lies behind the Vesper Gate in Harrowmere's north wall, in the lane behind
  the cathedral's apse: `--map harrowmere --at=5,2,-90 --script "back:0.35 look_up:0.12 wait:0.3
  interact"` (shut: its three sockets dark, and it says why), the same with `--flags
  sigil_taken,verdant_sigil_taken,iron_sigil_taken` (open, moonlight pouring through; `interact` goes
  through). Areas: `--map vesperholm` (the Gate Court, its `start`, the shrine at 16,50), `--at=21,43,-90
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
