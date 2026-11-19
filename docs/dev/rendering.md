# Rendering, models and the HUD

Models, the prop bake, the first-person view, villagers, fonts and sound.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/render/` | Shaders (`shaders/ps1.*`), procedural textures, mesh builder, matrix rig, models |
| `src/ashen_vault/render/prop_bake.py` | Bakes static props (`world.STATIC_PROPS`) once into lit world-space batches, grouped by 8x8-tile chunk and texture and culled per chunk (`World._draw_baked`); the shader draws them with `isModel` -1, doubling their halved vertex colours and lighting them with the light baked into their normals (`Batch.light`) plus your torch, as it lights a live model. Kindling a fire bakes the chunks round it again |
| `src/ashen_vault/render/bounds.py` | Measures a model without drawing it (a recording GPU); `models.preview_frame` centres and fits every weapon in its preview with it |
| `src/ashen_vault/render/shapes.py` | Model primitives raylib lacks (`blade`, `lozenge`, `wedge`) as pure triangle lists; `Gpu.primitive` uploads them |
| `src/ashen_vault/render/town_models.py` | Harrowmere's models: gabled `roof`s (one per building, on its NW wall tile with `span=W,D ridge=x\|z`, `tex=violet_slate eave=`), a `roof_turret` corbelled out on a house's corner (`shift=` to the corner, `rise=`, a witch-hat cone; only on an L of two walls, `test_every_harrowmere_turret_is_seated_on_a_corner_of_its_house`), the town wall's round `wall_tower`s (landmarks, `shift=`, `radius=`, `capped=false`), the `rampart_bay`s carved along its great walls (laid out by `world/ramparts.py`, never placed by hand), the `house_door` swinging in each house's `door_arch`, each shop's `shop_sign` (`emblem=anvil|scroll|flask|blades`: an oval painted plaque hung from a wrought-iron bracket by its door, a wall prop), the `silent_bell`, the cathedral (`cathedral_spire base=` over the crossing, `cathedral_tower` with `shift=dx,dz` to centre it on a 2x2 footprint, `turret` for the small ones, `flying_buttress`, stained-glass `window` within and `stained_window` without, `rose_window`; the great west door, `cathedral_portal`: three receding orders of pointed arches, a crocketed hood, the realm's crest in gilt in its tympanum, buttresses with saints under canopies, open oak leaves, and a stone gable over the wall holding the `great_rose`; the `grand_stair` up to it, fine steps between raking balustrades with lanterns and urns on its newels, and the plain `stair_flight`; the crimson `nave_runner`; its floor is the `cathedral_floor` texture, marble lozenges in bordered panels), the houses' faces (`shutters`: a twin round-headed window of leaded diamond panes behind iron-strapped board shutters, in dressed stone or, set in a half-timbered wall (`TileMap.wall_behind`), an oak frame; `balcony`, a jettied timber gallery under a pent roof; `door_arch` on the doorway tile facing out; `rise=` sets a hung one's height, `world.RISE`), the realm's crest (`banner_pole`, `crest_plaque`), the square's `fountain`, `bench`es, `hand_cart`, `hay_wagon` and `cargo` (their spoked wheels are `cart_wheel`), the founder's bronze `town_statue`, the trees (`tree kind=cypress|pine|olive|dead`, the last the cemetery's bare one: slim cypresses, flat-crowned umbrella pines, gnarled olives, each a 3D trunk and limbs under clumps of crossed leaf cards: paper-thin cubes carrying the cut-out `leaf_card` texture), pews, beds, cupboards, shelves, hearths, wattle `fence`s, `lamp_post`s (an oak post with a wrought-iron lantern), boats, Brannoc's `forge_bellows` and `grindstone`, and the tradesfolk's furnishings built from the game's own weapon and armour models: the smith's `weapon_rack` (a wall prop) and `armor_stand`s, Corvane's lacquered `katana_stand`s, Pell's `bookcase`s (`style=scrolls` for a rack of rolled scrolls) and `drawers` in the homes (`style=apothecary`, Tamsin's cabinet of many small drawers) |
| `src/ashen_vault/render/fortress_props.py` | The Cinderhold's dressing: `gargoyle_statue` (`pose=snarl`; far ones drop their fine carving, `world.DETAIL_RANGE`), `barred_window`, `tool_rack` and `great_window` (wall props; `great_window rise=` hangs high in a wall over the moat, a landmark), `forge_hearth`, `crucible`, `quench_trough`, `ingot_pile`, `slag_heap`, `impaler`, the `battlement` landmark (a crenellated walk on a wall top), `lava_spout` (`lavafall spout=gargoyle`), the smith-knight `forge_statue` and the `ore_cart` |
| `src/ashen_vault/render/moon_models.py` | Vesperholm's dressing as well as its foes (see `enemies.md`): `vesper_gate` (a tall pointed arch of moonstone, silver tracery leaves, three sockets in its lintel lit once it opens), all built in a Victorian Gothic Revival manner: `moon_lamp` (a cast-iron gas lamp, fluted, with a ladder bar and a crowned lantern of moon-glass), `veiled_statue`, `silver_tree`, `moon_window` (paired lancets of frosted `moon_glass` under a containing arch with a quatrefoil oculus, colonnettes, a hood mould and a gablet, glowing), `moon_spire` (the skyline's slender towers: polychrome courses, iron cresting, lucarnes), `moon_roof` (polychrome slate, iron cresting along the ridge, pierced bargeboards with drops, dormers, chimney stacks and a lit gable oculus; `grand` swaps the chimneys for a flèche and corner pinnacles) and `moon_portal`, the cathedral's great gate (three receding orders of pointed arches, a crocketed hood and wimperg, pinnacled buttresses with handmaids, a moon-glass tympanum, open oak leaves in silver strapwork) with `moon_rose`, its great rose, over it. All static, baked. It also draws the Moonless Tachi's Pale Crescent in flight (`crescent_wave`) |
| `src/ashen_vault/world/villagers.py` | How each villager looks (`Look`: build, garb, hair, hat, beard, apron, cloak, held tool, idle) |
| `src/ashen_vault/ui/smallfont.py` | The small mixed-case pixel font for all game text: menus, dialogue, messages, prompts and the boss bar (`hud.text` draws with it) |
| `src/ashen_vault/ui/tinyfont.py` | The HUD's tiny fonts: 3x5 `GLYPHS` (the HP/MP/ST labels and numbers, `hud.tiny`) and 3x4 `MICRO` (the HUD mouse's PRI / SEC labels and the quick item's count, `hud.micro_centered`; only the characters they use) |
| `src/ashen_vault/ui/logofont.py` | The logo's 5x7 capitals, shared by `docs/logo/make_logo.py` and big headings (`hud.big`: the title, the death screen) |
| `src/ashen_vault/audio/synth.py` | Synthesized sound effects (a blow on a foe plays its material's `hit_<material>`; `hit` is a blocked blow). Ambient fire (jets, vents, bombs) plays through `World.sfx_near`, which fades it with distance |

## Rules

- Static props are baked, not drawn part by part each frame (`render/prop_bake.py`): a kind in
  `world.STATIC_PROPS` must look the same at any time and in any state
  (`tests/test_prop_bake.py`). A new prop that animates, flickers, opens or breaks stays out of it; a
  big animated one is best split into a static body and a small moving part. Every other model part
  costs a Python call per frame, so keep dynamic models lean.
- Besides raylib's cube, sphere, cyl, cone and quad, models can draw `blade` (a lozenge-section slab
  that comes to a point), `lozenge` (the same section, straight) and `wedge` (a triangular prism),
  generated in `render/shapes.py`. Straight swords, the player's and the foes', are `models.blade_parts`
  (guard styles, pommels, ricasso, fuller, bevelled edges). Axe, cleaver and hammer heads are built with
  their edge or face on +Z, straight blades their edges on +-Z and katanas theirs on -Z;
  `models.weapon` turns each a quarter (`models.edge_turn`) so the edge leads along +X, the way swings
  travel and the hand's knuckles face (`test_edges_and_heads_lead_their_blows`; the jungle's Great Iron
  Hammer is in `HEADED`). The jungle's Flamberge is a `SWORDS` entry with `waves`, its blade a run of
  straight segments stepped from side to side (`models._wavy_blade`). An old save holding an item since
  taken out of the game loads with its replacement (`Items.RENAMED`, `Inventory.from_h`). A full cut's follow-through carries the arm out of the view before it comes home. Keys and relic sigils draw from
  `KEY_STYLES` / `SIGILS` (each key its own shape in `KEY_SHAPES`), in Belongings and on the ground (`models.pickup`). Enemy anatomy has helpers too: `skull`,
  `ribcage`, `hand`, `sack_hood` and `_bar` (a box between two points).
- Villagers are drawn by `models.npc` from a `world/villagers.Look` (build, clothes, hair, hat, held tool,
  idle); a new villager needs an entry in `villagers.LOOKS`. Their hands (`models._villager_hand`) are the player's
  fist made faceted: three-boned fingers of `FINGERS`' lengths curling by `CURL`'s shares and a
  three-boned thumb, closed round a held tool (a staff or spear stands upright through the fist,
  `POLE_TOOLS`); beyond `world.DETAIL_RANGE` they drop to three parts (`_villager_hand_far`). Brannoc's idle is `smith`: a loop of four
  blows on a billet at the anvil his model carries before him, a turn of it in the tongs, a look at it
  and a wipe of the brow (`villagers.smith_cycle`); each blow throws sparks and rings the anvil through
  `World.sfx_near` (`smith_blows`). Corvane, an old swordmaster, wears a `kimono` over hakama, a long
  white beard, a `topknot` and a laced `pauldron`, his blades thrust through the obi (`blade="hip"`), and
  stands `ready`, now and then easing a hand's width of steel out (`villagers.half_draw`). The town watch stands at its gates (`dialogue.WATCH`: Aldous and Tobin at the north road, Fenn by the cemetery's gate, Reyna at the east trail's gap) in a `helm`, a crested `tabard` and sometimes a kite `shield`, with a `halberd` or spear, idling on `watch` (a glance down the road now and then, `villagers.glance`); `test_every_harrowmere_gate_has_a_watchman_beside_it` keeps one by each gate. The Enthroned (`npc id=enthroned`) is its own
  model, petrified on `models.throne`: all stone, nothing glows but the drifting dust, and the stone king's
  lines whisper from it (`dialogue.ENTHRONED_LINES`).
