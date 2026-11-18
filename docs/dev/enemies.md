# Enemies and bosses

Behaviour flags, special moves, bosses and the rules every enemy model must keep.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/world/elements.py` | Elements: lightning against `conductive` foes, fire against `fireproof` ones, which weapons burn |
| `src/ashen_vault/world/shots.py` | Shots in 3D: spells follow the view's pitch, enemy shots aim at your chest, and a shot only hits a body it passes through |
| `src/ashen_vault/world/relics.py` | Boss relics (the Ember, Verdant, Iron and Argent Sigils), their drop/taken flags, `boss_falls` (twins fall together), the four-sigil ending (`ENDING_RELICS`) and the Vesper Gate: taking up the last of the `FIRST_THREE` sets `GATE_FLAG` (`mark_taken`, `open_gate`, which `World` also calls as a map loads, so an older save catches up) |
| `src/ashen_vault/render/cemetery_models.py` | The Cemetery of Ashes' models: the Ashen Sexton (its `grave_spade`, and `sexton_arms`, its poses for each move; `dust_puff`, `ash_billow` and `dust_devil` draw its ash), the Ashen Husk, the Shrouded Mourner (the cemetery's own lurker), `grave_walker` (the cemetery's Bone Walkers, `bone_walker model=grave`: risen in their winding sheets, a headstone shard for a shield and a length of iron railing for a weapon; the keep's keep their own look), `ash_hands` (the Sexton's grasping ash) and `ash_clod` (its spadeful), `gravestone`, `open_grave` and `cemetery_gate` (a pointed stone arch built out of the wall, black passage behind its iron leaves, a hooded mourner in a niche over the lintel and, unless `sentinels=false` as in town, hooded stone wardens either side; also the gate exit's `model=`, swung open once its `requires=` flag is set) |
| `src/ashen_vault/render/sewer_models.py` | The Harrow Sewers' models: the Gutter Rat, the Cistern Rat and Mother Gnawl (one chunky rat of few parts, `_rat`, at three sizes: a high bristling back, the head low, pale legs, naked ears, milky eyes and raw `sores`; she adds her belly, collar and a mane that rises in phase two; `swarm_rat` is one of her litter loosed at you, `squeal_ring` her squeal), the Sludge Slime and its Sludge Gobbets (`_sludge`), the Drowned Wretch (face down in the sludge while it lurks), the Bilge Leech (`_leech_spine`), the Sump Maw (the Sump itself grown hungry: a wave of black-blue sludge as tall as a house, rising from a pool and cresting forward into a fanged maw that glows green within, its crest crusted with skulls (`_skull`, their eyes kindling in phase two), bones and clods of dirt stuck in its sides, a tail curling up behind; `_maw_pose` for its moves), the ways between town and sewers (`sewer_grate` in the street, `sewer_ladder` below, set back against a wall behind it, `world.LADDER_BACK`), and the dressing: `drain_pipe`, `sluice_wheel` and `outfall_grate` (wall props), `rat_nest` |
| `src/ashen_vault/render/moon_models.py` | Vesperholm's models: the Pale Sentinel (an empty suit of silvered plate full of moonlight, a crescent `glaive` it sweeps all round), the Lantern Wraith (a legless hooded shade with a lantern of moonlight hung from a crook), the Moonhound, the Veiled Knight (frost-pale plate under a veil of moon-silk; `_fading` stipples him to `mist` as he winds up a blink), Duchess Ilvane (a gown of moon-silk in tiers, a crown of crescents, a veil she casts off in phase two for a blazing crescent halo and streaming hair; `duchess_arms` for her moves), the `frost_lance` they throw, the `moonbeam` (an `Eruption` style "moon") and `blink_mist` (a `Shockwave` style "blink"), the `vesper_gate` and the city's dressing: `moon_lamp`, `veiled_statue`, `silver_tree`, `moon_window` and the `moon_spire` landmark. Their ghostliness is pale glowing parts and stippled `mist` |
| `src/ashen_vault/render/forge_models.py` | The Cinderhold's models (golem, bowman, hound, the gargoyles, Stormbrand and Slagbreaker, arrows, thunder and motes, flame jets, and the skyline: spires, bastions, smokestacks, the gatehouse, the keep, lavafalls); `models` imports it last and borrows its helpers |

## Rules

- Enemy behaviour flags in `ai/enemy_types.py`: `ambush` spawns dormant (the chest Mimic) until woken;
  `lurk` sits still until you come close (the Stump Mimic, the Bone Crawler, the Shrouded Mourner, the
  sewers' Drowned Wretch and Bilge Leech); `once` stays dead; `splits` bursts a slain foe into
  `split_count` of another type (the Sludge Slime's gobbets, `World.split`): the pieces don't split again,
  and as no map places them a shrine rest never brings them back;
  bosses set `dead_flag` and drop a relic (the Butcher, a mini-boss, sets `butcher_dead` but has no
  relic: his cleaver is an entity `item=`). Any type picks special attacks from `moves` (see `MOVES` in
  `ai/enemy.py`: `sweep`, `web`, `pounce`, `cinders`, `combo`, `slam`, `eruption`, `hook`, `breath`
  (a line of `Eruption`s raking toward you and past), `dive` (a swoop through where you stood), and the
  Ashen Sexton's own, all of ash: `exhale` (a cone of grave dust breathed `EXHALE_REACH` ahead, a `Gout`
  of style "ash"), `ashfall` (an urn of ashes dashed down: it hurts all round within `ASHFALL_RADIUS`, a
  `Shockwave` of style "ash"), `dust_devil` (two `hazards.DustDevil` whirlwinds that drift after you
  and die with it, `World.devils`), `spadeful` (a fan of five ash clods that slow you, `effect="ash"`), `grasp` (a line
  of `Eruption(style="hands")`: ash hands that hurt and hold you) and `knell` (second phase: two rings of
  embers, `KNELL_GAP` apart, the second turned half a gap; `World.knell`); each of the ash moves also
  slows you, and no other foe uses them), and the Shrouded Mourner's `fireball` (grave-fire kindled in
  its palm and thrown from afar; up close it stabs), the Sump Maw's own: `bile` (a fan of four gobbets
  that poison and corrode, `BILE_RANGE`), `undertow` (an `Eruption(style="drowned")` under where you stand
  and four round it: the hands of the dead it swallowed hurt, hold you and build rot,
  `sewer_models.drowned_hands`), `gulp` (second phase: a surge along the floor maw-first through where
  you stood, `GULP_RANGE`; a lunge like `dive`, both in `enemy.LUNGES`; passing within `GULP_HIT` it
  swallows you once, `World.gulp`, a heavy blow, and for `GULP_GLOOM` seconds the dark of its gut stays
  on your eyes, `World.gloom_t` / `World.dark_here`, which the game's darkness eases toward) and `shed` (second phase: `SHED_COUNT` of its `sheds` type, Sludge Gobbets,
  sloughed off round it, `World.shed`; never while `SHED_MAX` of them still crawl, `World.can_shed`;
  they die with it), and Mother Gnawl's own: `tail_lash` (never picked by `_pick_move`: in `_chase`,
  before she turns, she lashes at you when you stand behind her, past `TAIL_ARC` off her facing and within
  `Enemy.tail_reach`, and keeps her back to you through the windup; `World.tail_lash` only lands on you
  still behind her), `squeal` (unblockable, from any side within `SQUEAL_RADIUS`: light harm and a stagger,
  a `Shockwave(style="squeal")`) and `swarm` (second phase: five of her litter loosed in a fan along the
  floor, `SWARM_HEIGHT` up, projectiles of effect "rat" that build rot). Neither of the sewers' bosses
  (Mother Gnawl, `matron_dead`, behind a great door at each of her nest's two mouths; the Sump Maw,
  `maw_dead`) drops a relic. Vesperholm's: `frost_lance` (a fan of three lances of moon-frost,
  `FROST_LANCE_RANGE`, through `World.enemy_fire`; a type with `shot="lance"` throws them one at a
  time as its plain shot, fast and point first; one that strikes you numbs your legs, `Player.chill_t`,
  slowed as by silk under a frost overlay), `blink` (`BLINK_RANGE`: kept at bay, it fades into the
  moonlight and steps out `world.BLINK_BEHIND` behind you, or beside you where a wall, a drop, the gorge
  or a body is in the way, and winds straight up its blow, `Enemy._blink`, `World.blink`; the Veiled
  Knight's, and the Duchess's in phase two), and the Duchess's own `moonbeam` (shafts of moonlight
  under you and `MOONBEAM_ASIDE` to either side across your facing, `Eruption(style="moon")`, which
  hurt and chill) and `moonfall` (second phase: a shaft under you and rings of them round it,
  `MOONFALL_RINGS`; stand in a gap). Duchess Ilvane (`moon_duchess`, `proper`, `duchess_dead`) drops
  the Argent Sigil. At half
  HP a boss with a `brood` calls it and one with a `rage` kindles it (the Warden's burning blade);
  either way it enters its second phase (`Enemy.phase2`), fights faster and adds its `phase_moves`.
  `perch` spawns a statue (`Enemy.perched`) that wakes when it sees you, or is struck; it then spends
  `STATUE_RISE` in state `"rising"` (seams of fire spread, its stone bursts off at `STATUE_BURST`, the wings
  unfold and it lifts off). `rise="ash"` (the Warden, the Butcher, the Loom Mother, the Sexton, the sewers' two, the Duchess) spawns a
  boss as a smouldering heap (state `"ashes"`, `cemetery_models.ash_heap`) until you step into its arena
  (`World.rise_time`), then it forms from the feet up over `ASH_RISE` (`ASH_RISE_AGAIN` back through its
  fog): the death dissolve played backwards (`ash.rise_phases`) while `AshCloud.gather` draws embers in.
  The door slams as it starts (once you stand clear of the doorway, `Arena.clear_of_gate`); nothing strikes or touches it while `Enemy.unseen`, and the boss bar
  fills with `rise_progress`. Tests skip the entrance with `conftest.risen`. `twin=<type>`
  pairs two bosses: waking one wakes the other (`World.rouse_twin`), they take turns with special moves
  (`World.twin_busy`), the survivor enters phase two when the other falls (not at half HP), they share a
  `dead_flag` and relic set only when both are dead (`relics.boss_falls`), and a shrine rest brings a
  fallen twin back beside its living other at full HP. `conductive` foes take `LIGHTNING_MULT` from
  lightning and are jolted (`staggers`); `fireproof` ones take half from fire and never burn. `shot=arrow`
  draws a ranged foe's shots as arrows (and they fly faster), `shot=thorn` as barbed thorns
  (`models.thorn_shot`, the Snare Bloom's, and Thornlash's Thorn Volley, whose thorns poison).
  A type's `mouth` sets the height its shots leave from (the Snare Bloom's tall pod), else 1.2 m.
  An enemy entity's `item=` is loot it drops when slain. `flammable` types (the jungle's plants) take
  more from Pyre and keep burning. Enemies carry lingering harm in `Enemy.status` (`poison` from Venom
  Dart, `burn` from Pyre), one bite a second (`status_tick`) that never staggers.
- An enemy type's `height` is the top of its body as it dies: the ash dissolve crumbles that span.
  Any direct blow lights a foe red for `FLASH_TIME` (`Enemy.flashing`, `world.HIT_RED`), stagger or
  not; a model that recolours itself when hit keys on `e.flashing` (`models.hit_tint`, its strength in
  `HIT_TINT`), its glowing parts turn `models.HIT_GLOW`, and its reeling pose keys on `state == "hurt"`. A type's `material`
  (`enemy_types.MATERIALS`: flesh, bone, iron, stone, wood, ash, spirit (Vesperholm's moonlit dead, a
  glassy chime)) picks the `hit_<material>` sound a blow
  on it makes (`Enemy.hit_sound`; an iron-chest mimic rings as iron), pitched at random within
  `game.HIT_PITCH`.
  A hovering foe's shot span reaches from its hover height up to its `tall` (`shots.body_span`).
  Every model has a death pose (eased by `models.death_fall`); `tests/test_render_logic.py` checks
  that each one collapses, stays above the floor and fits its `height`, so update both together.
  Its `tall` is the top of the standing body: a spell bolt flying higher misses it (`world/shots.py`).
  Bosses must stay boss-sized in detail (at least 50 parts, 30 for armed and armoured regulars; the
  sewers' rats are the exception, kept to a few bold shapes on purpose: Mother Gnawl 25, the Cistern Rat 15) and
  look different in their second phase (`test_bosses_have_boss_level_detail`,
  `test_phase_two_changes_how_each_boss_looks`), and every glow goes out in death.
- Foes that wield a weapon chop overhead (`models.chop_angle`) and hold it in a fist (`models.held`,
  `sword_parts`): give the arm an elbow (`elbow_bend`) and point the weapon with
  `aim_wrist(blade_direction, shoulder + elbow)` rather than a fixed angle, so it never folds back along
  the arm. `tests/test_render_logic.py` checks the wrist stays within 150 degrees of the forearm's line.
- Every blow, shot, ash or fire a foe lands on you is scaled by `world.FOE_DAMAGE` (1.5) through
  `world.foe_harm`, before armour takes its share; traps, lava, thorns, spores, logs and falls are not.
