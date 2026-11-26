# Player, gear, spells and saves

Equipment, combat, spells, shops, saves and the story.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/player/weapons.py` | Weapon categories, light and heavy attacks, swing tempo and the secret attacks (`secret()`) |
| `src/ashen_vault/player/guard.py` | Shield blocking: what a raised shield stops and what it costs in ST |
| `src/ashen_vault/player/burden.py` | Equipment load: each item's `mass` against `capacity(STR)` gives a tier (Light / Medium / Heavy / Overloaded) scaling walk speed, ST refill and every ST cost |
| `src/ashen_vault/player/durability.py` | Gear durability: each weapon, shield and armor piece's maximum (`max_durability`, by weight, stability or slot; `Item.durability` overrides it), how a landed swing, a block and a foe's blow wear it, what a broken piece loses (`BROKEN_POWER`, `effective_shield`, no DEF) and Brannoc's `repair_cost`. What is left lives in `Inventory.wear` (per item id, absent = whole); `Player.wear` queues `wear_news` that `Game._announce_wear` turns into messages |
| `src/ashen_vault/player/ailments.py` | The player's ailments (poison, toxic, bleed, rot, corrosion, frost): meters a foe's `inflicts` fills with each blow or shot that gets through (`World.strike_player`; a block builds nothing), draining on their own; a full one takes hold (`World.afflict_player`): poison bites `POISON_SHARE` a second for `POISON_TIME` and slows ST (it can kill, `Game._update_ailments`), toxic (the Sallow Fen's mire, `Tile.afflict`, and its foes) bites the harder `TOXIC_SHARE` for the shorter `TOXIC_TIME` and stops ST refilling, lingering on its own clock beside poison, bleed bursts for `BLEED_SHARE`, rot caps HP at `ROT_CAP` (`Stats.hp_cap`, greyed on the HP bar), corrosion wears all gear, frost (Vesperholm's moon-frost: its lances, shafts of moonlight, `world.MOON_FROST`, and its foes' blows) brings on Frostbite, a burst of `FROSTBITE_SHARE`, legs frozen to `FROZEN` speed for `FREEZE_TIME` and ST refilling at `FROST_REFILL` for `FROST_TIME` (`Ailments.frozen` / `frostbitten`, under the frost overlay). Tamsin's remedies cure them (the Ember Draught thaws frost; the Fenbane Tincture purges toxic and poison, stocked once you have seen the fen, `SHOP_EXTRAS`, `visited_sallow_fen`) (`Item.cures`); Herran's Sun Tincture, from a hidden laboratory of his castle, cures them all and, by its `Item.effect` (`Player.drink`, `"sun_ward"`), keeps any from building for `SUN_WARD_TIME` (`Ailments.ward_t`), as his Graft Draught (`"graft"`) takes `GRAFT_HP` for `GRAFT_TIME` of ST refilling `GRAFT_REFILL` times as fast and blows costing `GRAFT_COST` of their ST; `Player.revive` clears all; saved with the player. The HUD stacks a bar per ailment above the vitals (`hud.ailment_bars`) and lifts the messages over them. Each ailment also shows at the edges of the view (`Ailments.borders`, drawn under the HUD boxes by `hud.ailment_borders`): one glow in their colours mixed (`ailments.border_tint`), then each one's mark over it (venom bubbles, a throbbing violet ooze for toxic, blood drips for `FLARE_TIME` after a bleed, corner mould, rust pits after corrosion, frost rime), so several combine |
| `src/ashen_vault/player/stash.py` | The shrine store: deposit and withdraw items and spells, what may be stored, and what still counts as owned |
| `src/ashen_vault/player/remnant.py` | The gold you drop when you die (`Player.remnant`, saved with the player): a heap of your ashes (`cemetery_models.remnant`) at `World.death_spot` (the last solid ground if you died down a chasm, in water or lava); walk over it or interact to gather it, die again first and it is lost |
| `src/ashen_vault/ui/compare.py` | ATK / DEF / Block / SPL / Load now and after equipping (or taking off) an item or spell: the Belongings stats panel, its slot chooser and the shop show it before you choose |
| `src/ashen_vault/ui/belongings.py` | Belongings as data: its tabs, slot marks, the Equipped panel, the slot chooser (Primary / Secondary) and the quick slots' marks (`[Q2]`), chooser rows and Quick panel |
| `src/ashen_vault/ui/atk_bar.py` | What a weapon button's two-row bar shows (ATK gauge, heavy charge, a ready art), as data; `hud.draw_atk_bar` draws it |
| `src/ashen_vault/ui/tally.py` | `GoldTally`: the top-right gold counter's bookkeeping (a gain lingers as "+N", then rolls in; spending shows at once). `Game.update` feeds it |
| `src/ashen_vault/save/slots.py` | Save slots: three journeys side by side (`SLOTS`), slot 1 the base save path (an old single save) and `save_<n>.json` beside it; each records `Player.play_time` (counted by `Game.update` in `PLAYED_SCENES`). The title's New Game and Load Game open the slot chooser (New Game asks before overwriting a used slot), Continue loads the slot saved last (`latest`) |
| `src/ashen_vault/save/settings.py` | Player options (sound on/off, volume) in `settings.json` beside the save (shared by every slot); the title and pause menus' Options screen edits them and `Audio.set_volume` applies them as the master gain |
| `src/ashen_vault/dialogue.py` | NPC conversations and the shop list |

## Rules

- `game.message()` text may wrap spans in braces, e.g. `f"Obtained {{{item.name}}}."`: the HUD draws
  them in the highlight colour (`util.highlight_runs`). `tests/test_ui_logic.py` checks the small font
  has a glyph for every character used in game messages and names.
- Interacting with a shrine opens the `shrine` scene (Rest / Storage / Leave; `SHRINE_OPTIONS`), so a
  smoke run rests with `--script "interact confirm"`. Rest plays the `rest` scene; it heals, respawns
  normal enemies and saves while the fog covers the screen (it never mends gear). Storage is the shrine
  store (`player/stash.py`, scene `storage`): `Player.stash` and `Player.stashed_spells`, shared by every
  shrine, saved with the player. Keys and sigils can't be stored; a stored spell leaves `Player.spells`
  until taken back; shops (`Game._shop_stock`) and finds (`loot.claim`'s `stored`) count stored things as
  owned (`stash.owns`, `stash.known_spells`). Dying keeps everything the player carries but its gold, and every flag: the gold is
  left in a heap of your ashes (`player/remnant.py`, `Game._drop_remnant`) to gather on your next life,
  lost if you die again first; you wake at the last shrine (`Game._wake_at_shrine`) and only normal
  enemies (and a living boss's HP) come back.
- Persistent world state lives in the save's `flags` set, keyed `<kind>:<map>:<tx>,<tz>` (opened
  chests, broken barrels, revealed walls, slain mimics, kindled fires as `lit:`) or `loot:<key>` for
  dropped items. Bosses add
  their `dead_flag` (`boss_dead`, `spider_dead`, `gargoyles_dead`, `butcher_dead`, `sexton_dead`, `matron_dead`,
  `pall_dead`, `duchess_dead`) and relics a
  `<relic>_taken` flag (`sigil_taken` for the Ember Sigil); once the first three are taken
  `vesper_gate_open` (`relics.GATE_FLAG`) is set, though the Vesper Gate stands open from the start and
  nothing waits on it. Shown hints add `hint:<map>:<marker>`, a one-way
  exit `left:<map>`.
- Equipment (`player/inventory.py`): two hand slots, shown to players as **Primary** (`right` = left
  mouse button) and **Secondary** (`left` = right button) via `SLOT_NAMES`; never say "hand" in text the
  player sees. Each holds a weapon, a shield, the readied spell (`SPELL`) or nothing (a fist), plus
  `body` and `hands` armor. `two_handed` weapons fill both slots and swing from Primary only. The HUD
  draws the slots on a mouse in the bottom right (`hud.mouse_hud`: Primary on its left button, Secondary
  on its right, the selected quick slot's item on the wheel). HUD spacing comes from `HUD_MARGIN` (screen edge),
  `HUD_PAD` (inside a box) and `HUD_GAP` (between elements); derive new positions from them. Belongings and the
  shop lay their panels out from `screen.MENU_SPACE` (one margin from the screen edge and between
  panels: `MENU_LIST`, `EQUIPPED_PANEL`, `STATS_PANEL`, `ITEM_PANEL`). Belongings doesn't pause the game
  (`Game._tick_unpaused`): the world, lifts and foes go on while it is open, you just neither walk nor fight. Every
  box and window is `hud.hud_box` (or `panel`), drawn in whole pixels with `HUD_RADIUS` corners
  (`HUD_INNER_RADIUS` for a well inside a box); never pass another radius
  (`test_every_hud_box_shares_the_named_corner_radii`). The
  compass marks the nearest great door whose boss lives (`World.boss_bearing`), never a `rear` one. A mouse action must never share a name with
  a movement key (`tests/test_input.py`): `"back"` once did, and a raised shield walked you backward. Items carry a `level` requirement: buying is
  allowed, equipping is not (`Inventory.equip_error`). The first-person arms (`models.weapon_view`)
  take their sleeve and glove looks from `SLEEVES` / `GLOVES`, so new armor needs an entry there (the player is one of the Ashen: bare, the forearm is grey ash, `models.ASH_ARM` with the `ash_skin` texture, and the hands `models.ASHEN`; a hand on a weapon holds it in a handshake grip, `models.GRIP_TURN`: knuckles toward the edge, which leads every swing, and the forearm bends to follow it (`arm`'s `heel`), swinging with the hand so the wrist never bends past `models.WRIST_BEND` (`test_wrists_bend_only_so_far_through_every_swing`); a bare fist is held the same way, closed on nothing (and lands only `compare.BARE_HANDED` of a blow
  unless gloves add power), while a shield's turns about its grip to sit on its forearm. Either way draw the arm to `models.hand_wrist` and pass its turn to `fist`); a new
  shield needs its strap in `models.SHIELD_GRIPS`, where the fist closes (drawn after the shield, so a
  raised shield shows the hand).
- Weapons, shields and armor wear (`player/durability.py`): a swing that connects wears the weapon once
  (`Game._resolve_swing`, not the pulses after it), a block wears the shield by what it stopped
  (`Player.take_blow`, `Block.stopped`), a foe's blow that lands wears each armor piece
  (`World.strike_player`); traps, falls and lava wear nothing. Broken gear stays usable but weak, and a
  broken weapon looses no art. The shield's mouse button shows its durability, not ST (`hud.mouse_button`);
  broken gear carries `hud.broken_mark`. Belongings shows `Dur n/max` by the item's name and `(Broken)` in
  Equipped. Brannoc (`dialogue.REPAIRERS`) opens his shop with `MEND_ROW`, leading to the `repair` scene;
  the `menders_kit` (kind `repair`, Items tab, never in a quick slot) mends one piece through the slot
  chooser. Kits are sold, gifted, in a few chests and in breakables (`loot.KIT_CHANCE`).
- Weapons, shields and armor carry a `mass` (kg). Their total sets the player's load tier
  (`player/burden.py`, `Player.burden`): heavier gear walks slower, refills ST slower and pays more ST
  for attacks, sprinting and blocking. New gear needs a `mass` (`tests/test_burden.py`).
- Belongings is split into tabs (`belongings.TABS`: Items, Weapons, Armor, Spells, Unique), switched
  with `tab_prev` / `tab_next` (A / D, Left / Right) or a click; `tab_of` files each item kind.
- Quick items: four slots the player fills (`Player.quick_slots`, `QUICK_SLOTS`; a new player has
  `DEFAULT_QUICK`, Red Tonic and Blue Moss). In Belongings' Items tab, choosing a consumable opens the
  chooser with Use and a row per slot (`belongings.consumable_options`; Remove when it is slotted);
  `Player.assign_quick` moves an item already in another slot, `clear_quick` empties one. Rows show
  `[Q<n>]` (`belongings.quick_mark`) and the Items tab shows a Quick panel in Equipped's place
  (`Game._draw_quick`). In play the mouse wheel steps through the filled slots only
  (`Player.cycle_quick`, `quick_index`) and middle click uses the selected one (`Game._quick_use`); a
  slot whose item has run out stays selected and greys out. Saved as `quick_slots` / `quick_index`;
  `Player.restore_quick` reads them, seeding slot 1 from an older save's single `quick` item.
- Hearth Ash (`hearth_ash`, `effect="homeward"`; Tamsin sells it, and a chest in the Cinder Keep's
  great hall and one on the floor of Herran's Aviary hold two each) carries you home:
  `Game._use_hearth_ash` raises the shrine's ember fog (`RestSequence`, labelled "Homeward...") and,
  under it, loads `world.HOME_MAP` and sets you beside its first shrine (`world.home_spot`). It
  restores nothing, wakes no one and records nothing. `World.homeward_refusal` keeps it in your pack
  in Harrowmere, in a sealed boss fight and while you fall or cross a fog.
- Every attack costs ST. Each category's moveset (`weapons.MOVESETS`) is tuned for a medium weapon;
  an item's `weight` (`light` / `medium` / `heavy` / `great`) scales each attack's ST, damage and poise
  through `weapons.WEIGHTS` (`weapons.attack` returns the sized Attack) and adds `WEIGHT_TEMPO` to its
  `tempo`, which sets how long its swings take. Heavy and great weapons (`weapons.is_heavy`) also
  stagger a foe with `heavy_stagger` on every blow, past its poise (see enemies.md). Each hand's ATK gauge refills over the weapon's
  `speed` times `weapons.GAUGE_REFILL` (`weapons.refill_time`); a swing hits as hard as the gauge was
  full. A blow strikes the living foes in its `reach` and inside its `cone` (`World.melee_targets`,
  nearest first), up to `targets` of them: cuts that travel across the arc (the slashes, the Reverse cut,
  the hew, the clout, the hook) go through `weapons.CLEAVE` foes in a wider `CLEAVE_CONE`, while
  thrusts, jabs, the whip's crack and blows that drop straight down stop on one (`SINGLE`); every foe
  struck takes the full blow, the combo and the hitstop follow the nearest. Attacks that strike twice
  (the Aftershock) use `pulses`. A weapon may swing a heavy of its own
  in place of its category's (`weapons.HEAVY_OVERRIDES`, resolved by `weapons.moveset`, so ST, tempo, the
  charge, arts and secrets work unchanged): the Katana keeps the Lunging thrust, while the Moonless Tachi
  and the Nodachi cut a Reverse cut (`slash_left`, the katana's cut mirrored: high left down to low right,
  the wrist rolled so the edge leads). Katanas cut their light with `katana_cut` (wound up with the blade
  still in view, then one long diagonal across the view), not the sword's `slash`. An attack's `lunge` carries you forward over a few frames
  (`Player.step_lunge`, `LUNGE_SPEED`), setting off `LUNGE_LEAD` of the swing before the blow lands; walls
  and fog stop it as they stop walking, it ends short of a foe's body (`collision.runs_into`,
  `World.bodies`), and a blow, a shove, the swing's end or being set down elsewhere cancels it. Attack poses are keyframed in
  `models.MOTIONS` (wind, strike, follow, each `(dx, dy, dz, rx, ry, rz)`), the strike lands at the
  attack's `hit_at`, and edged weapons (`TRAILS`) smear a fan of ghost blades through the blow; a katana's
  (`TRAIL_STYLE`) is a denser crescent along its outer blade, and its cuts wind up sooner
  (`CUT_WIND_AT`) so more of the swing is the cut. A motion
  ends part way home (`models._settle`); the view's `PoseBlend` (`player/view_blend.py`, kept by `Game`
  and passed to `models.weapon_view`) eases the arms the rest of the way, into each new swing, charge or
  shield raise, and lets them trail the turning view (`Sway`). The viewmodel draws over the world
  on a depth buffer of its own (`Game` wipes only depth before it), so its parts sort among themselves:
  a fist's fingers pass in front of the grip they close round and its palm behind.
- Secret attacks are listed in `weapons.secret()`; performing one adds a `secret:<category>` flag,
  which reveals its name in Belongings and the shop.
- Weapon arts (`weapons.ARTS`, keyed by item id: the Ashblade's Ember Spill, Stormbrand's Thunderstroke,
  Thornlash's Thorn Volley, Slagbreaker's Slag Burst, the Moonless Tachi's Pale Crescent, the Torch
  Greathammer's Brand Sweep, the Ember Stone Sword's Kindle Seam, the Vesper Moonbrand's Vesper Ray): releasing a heavy with both the ATK gauge and the
  heavy charge full, and the art's `mp`, sets `Player.swing_art` (`art_ready`; a secret outranks it), and
  `Game._release_art` looses it as the blow lands, through the spells' plumbing (`World.flame_cone`, which
  Pyre shares, `fire_bolt`, `volley`, `slag_ring`, `crescent_wave`). An art with a `motion` swings that
  instead of the heavy (the Pale Crescent is drawn as the `draw`). The Pale Crescent (kind `WAVE`) looses
  one wide crescent of pale light (`Projectile` with `pierce`, its `width`; `shots.sweeps`) that cuts
  through every foe across its breadth, each once (`hit_ids`), until a wall or its `life` ends it; it is
  drawn by `moon_models.crescent_wave`, and the blade's smear burns in the art's `rgb`. The Vesper Ray
  is a `WAVE` too, narrow and fast (effect `moonray`): a ray of moonlight that runs through every foe in
  a line twice as far as the crescent flies, drawn by `moon_models.moon_ray`, its shaft trailing back
  toward the blade (never past the eye). The Vesper Moonbrand, a two-handed greatsword of pale glass, is
  the Vigil Chapel's relic (`moon_models.moonbrand`), planted in its altar behind the Keystone. The weapon button's bar shows the ATK gauge on its top
  row and the heavy charge on its bottom one (`ui/atk_bar.py`); a ready art burns it in the art's `rgb`.
  Belongings and the shop list the art under the weapon's moves.
- Weapons may carry an `element` (`"lightning"`, `"fire"`): `Game._strike` multiplies by
  `elements.mult` and a fire weapon leaves `burn` on what it hits. It also multiplies by
  `elements.brittle_mult`: a `brittle` foe (Old Harrowmere's Stone Golems and the Keystone) takes
  `BRITTLE_STRIKE_MULT` from the blunt categories (`STRIKE_CATEGORIES`: club, hammer, mace, fists) and
  `BRITTLE_EDGE_MULT` from everything else. Spells are untouched.
- A weapon's `light` (metres) is firelight it sheds while held (the Torch Greathammer, the Ember Stone
  Sword, both in Old Harrowmere): `Inventory.carried_light` takes the brightest in your hands and
  `darkness.player_light` keeps it from shrinking in the dark and tints your light toward `FIRE_RGB`.
- Each weapon has its own small, animated glyph on the HUD mouse (`hud.WEAPON_ICONS`, keyed by item id,
  within `ICON_REACH` of the button's centre); a new weapon needs one, unlike any other
  (`test_weapon_icons_all_look_different_and_fit_their_button`).
- Spells are `player/spells.py` (`Spells.ALL`, their formulas) and are taught by `scroll_<id>` items, every
  one of them: a woken Ashen knows none, and finds Flame Bolt's (`scroll_flame`) in the cemetery's chapel;
  `Game._cast_spell` dispatches them. Venom Dart and Flame Bolt are bolts (`World.fire_bolt` with an
  `effect`; Thunder Spear is a fast `effect="thunder"` bolt), Arcane Motes are three `homing`
  projectiles (`World.motes`, steered by `shots.home`), Pyre is a short cone (`World.pyre`)
  drawn as a `Gout` of flame plus sparks, Veil of Mist sets `Player.veil_t` (ordinary foes then
  notice you only very close; striking or casting anything else lifts it), Lumen sets `lumen_t`, and Ashen
  Ward sets `ward_t` (`Game.hurt_player` passes every blow through `Spells.warded`; embers circle the view
  and the vitals box's trim glows). Rift Lance (`World.rift_lance`) is a narrow piercing shot of daylight
  (`effect="rift"`, `pierce`, drawn by `sunken_models.rift_lance`) that runs through every foe on its line;
  Bellward (`World.bell_toll`) tolls a phantom bell that staggers every foe within `Spells.BELL_RADIUS`,
  a ring of pale flares showing its reach. Both are sold only by Ysolde Vane. A spell's
  `recovery` is how long the magic gauge takes to refill after it (Pyre's is short). A new
  spell also needs a HUD icon (`hud.spell_icon`), colours in `models.SPELL_GLOW` / `SPELL_ORB`, and its
  scroll's parchment, rods and wax in `models.SCROLLS` with a rune in `models.SCROLL_RUNES` (no two alike).
- Shops are `dialogue.SHOPS`: Brannoc's forged steel and armour, Pell's scrolls and salvage, Tamsin's remedies,
  and Corvane's blades in the hut on the town's west edge (Corvane won't talk below `CORVANE_LEVEL`),
  and Ysolde Vane's two copied spells in Old Harrowmere's Oubliette, sold only once the gaoler's lever
  (`dialogue.OUBLIETTE_OPEN`) has raised her cell front. Her fellow prisoners there, Aubel the Ringer and
  Sister Coldry, tell the first city's story (raised on the sleeping Keystone, sunk when its bells fell
  silent) and how the two roads of light below the plaza work; both change once the Keystone falls.
  Villagers in `dialogue.GIFTS` hand a newcomer something once (`gift:<id>` flag) and then open their shop,
  if they keep one; Brother Marrow, in his cell in the Abandoned Prison, gives his only once you have pulled
  his cell's lever (`dialogue.MARROW_FREED`), and through the bars points you to the chapel and the
  Warden's Key. Shops hide gear you own; a chest, pickup or gift holding gear or a scroll you already
  own pays gold instead (`loot.claim`). No spell scroll, gear or key may be placed twice across maps and
  gifts (`tests/test_loot.py`): give a new find a new item.
- The story: the player is one of the Ashen, woken in the Cemetery of Ashes by a toll of the town's bell
  that no one rang. Odrin knows the prophecy: whoever wakes must win five sigils to raise the king turned
  to stone on the cathedral's throne (the Enthroned); many Ashen woke before and failed. Nobody arrived by
  sea. The four sigils were the realm's four seals, and the king held them. His sister, Duchess Ilvane
  of Vesperholm, wed the moon on the fourth, the Argent Sigil, so her city would never see a dawn or a
  death: the moon stopped over it, and it keeps whatever it shines on as it is, her people as pale shades
  and her brother as stone on his throne. With the fourth bent to the moon, the other three fell to
  keepers who went bad (the Warden, the Loom Mother, the gargoyles). Older than the realm is Lyra the
  Embracer, the faceless old god of six hands held out palms up: the first city raised her colossi
  (broken now in Old Harrowmere's halls) and the prison's chapel still made its inmates kneel to her
  idols. Ilvane wed the moon on her altar: the Argent Sigil lies in Lyra's hands on the altar at the
  end of the bridge over the Duchess's garden, up the stair behind her choir. Taking an altar's sigil
  marks it taken as picking one up does (`relics.mark_taken`). Brother Marrow and a hint on the
  Drowned Plaza name her too. From inside the stone the king rang
  the bell himself, once, to wake the Ashen: the dead, whom the moon cannot keep. Odrin names all five
  at the first meeting: the fourth lies with the Duchess beyond the Vesper Gate at the head of the
  cathedral steps, which stands open (nobody remembers it shut, nor who opened it), so the whole realm is
  open to explore from the start; the fifth is Herran's, and the way to him opens from Lyra's altar. The fifth seal, the Auric Sigil (the sun's, gold), was never the
  king's: Ilvane and her brother Herran are both children of Lyra (the Enthroned's own parentage is left a
  mystery), and Herran kept it in his castle of towers above the clouds, Herran's Castle
  (`herrans_castle`, then `herran_spire`), up the stair of light that rises off the bridge beside Lyra's
  altar in Vesperholm once the Argent Sigil is lifted from her hands. He wanted his mother's many hands:
  he grafted arms onto his drakes, then the arms of drakes and men onto his own back until he bore eight,
  and went mad (his journal tells it: pages in the secret laboratory, atop the Clock Tower and the
  Belvedere, and the last in his spire's study). He drops the Auric Sigil. Odrin no longer ends the game: shown all five
  (`relics.ENDING_RELICS`) he sets `dialogue.BELL_UNSEALED` and you keep them, and ringing the Silent
  Bell with all five in hand (`dialogue.bell`) plays the ending. The Enthroned stirs a stage further for
  each you carry (`dialogue.ENTHRONED_LINES`, six stages), and at five confesses he rang the bell. What
  lies below the Bell Square, which will take the ending's place, is still a `TODO(story)` in `game.py`.
