# Player, gear, spells and saves

Equipment, combat, spells, shops, saves and the story.

## Modules

| Path | Contents |
| --- | --- |
| `src/ashen_vault/player/weapons.py` | Weapon categories, light and heavy attacks, swing tempo and the secret attacks (`secret()`) |
| `src/ashen_vault/player/guard.py` | Shield blocking: what a raised shield stops and what it costs in ST |
| `src/ashen_vault/player/burden.py` | Equipment load: each item's `mass` against `capacity(STR)` gives a tier (Light / Medium / Heavy / Overloaded) scaling walk speed, ST refill and every ST cost |
| `src/ashen_vault/player/durability.py` | Gear durability: each weapon, shield and armor piece's maximum (`max_durability`, by weight, stability or slot; `Item.durability` overrides it), how a landed swing, a block and a foe's blow wear it, what a broken piece loses (`BROKEN_POWER`, `effective_shield`, no DEF) and Brannoc's `repair_cost`. What is left lives in `Inventory.wear` (per item id, absent = whole); `Player.wear` queues `wear_news` that `Game._announce_wear` turns into messages |
| `src/ashen_vault/player/ailments.py` | The player's ailments (poison, bleed, rot, corrosion): meters a foe's `inflicts` fills with each blow or shot that gets through (`World.strike_player`; a block builds nothing), draining on their own; a full one takes hold (`World.afflict_player`): poison bites `POISON_SHARE` a second for `POISON_TIME` and slows ST (it can kill, `Game._update_ailments`), bleed bursts for `BLEED_SHARE`, rot caps HP at `ROT_CAP` (`Stats.hp_cap`, greyed on the HP bar), corrosion wears all gear. Tamsin's remedies cure them (`Item.cures`), `Player.revive` clears all; saved with the player. The HUD stacks a bar per ailment above the vitals (`hud.ailment_bars`) and lifts the messages over them |
| `src/ashen_vault/player/stash.py` | The shrine store: deposit and withdraw items and spells, what may be stored, and what still counts as owned |
| `src/ashen_vault/player/remnant.py` | The gold you drop when you die (`Player.remnant`, saved with the player): a heap of your ashes (`cemetery_models.remnant`) at `World.death_spot` (the last solid ground if you died down a chasm, in water or lava); walk over it or interact to gather it, die again first and it is lost |
| `src/ashen_vault/ui/compare.py` | ATK / DEF / Block / SPL / Load now and after equipping (or taking off) an item or spell: the Belongings stats panel, its slot chooser and the shop show it before you choose |
| `src/ashen_vault/ui/belongings.py` | Belongings as data: its tabs, slot marks, the Equipped panel and the slot chooser (Primary / Secondary) |
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
  `maw_dead`) and relics a
  `<relic>_taken` flag (`sigil_taken` for the Ember Sigil). Shown hints add `hint:<map>:<marker>`, a one-way
  exit `left:<map>`.
- Equipment (`player/inventory.py`): two hand slots, shown to players as **Primary** (`right` = left
  mouse button) and **Secondary** (`left` = right button) via `SLOT_NAMES`; never say "hand" in text the
  player sees. Each holds a weapon, a shield, the readied spell (`SPELL`) or nothing (a fist), plus
  `body` and `hands` armor. `two_handed` weapons fill both slots and swing from Primary only. The HUD
  draws the slots on a mouse in the bottom right (`hud.mouse_hud`: Primary on its left button, Secondary
  on its right, the quick item on the wheel). HUD spacing comes from `HUD_MARGIN` (screen edge),
  `HUD_PAD` (inside a box) and `HUD_GAP` (between elements); derive new positions from them. Belongings and the
  shop lay their panels out from `screen.MENU_SPACE` (one margin from the screen edge and between
  panels: `MENU_LIST`, `EQUIPPED_PANEL`, `STATS_PANEL`, `ITEM_PANEL`). Belongings doesn't pause the game
  (`Game._tick_unpaused`): the world, lifts and foes go on while it is open, you just neither walk nor fight. Every
  box and window is `hud.hud_box` (or `panel`), drawn in whole pixels with `HUD_RADIUS` corners
  (`HUD_INNER_RADIUS` for a well inside a box); never pass another radius
  (`test_every_hud_box_shares_the_named_corner_radii`). The
  compass marks the nearest great door whose boss lives (`World.boss_bearing`). A mouse action must never share a name with
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
  the `menders_kit` (kind `repair`, Items tab, not a quick item) mends one piece through the slot
  chooser. Kits are sold, gifted, in a few chests and in breakables (`loot.KIT_CHANCE`).
- Weapons, shields and armor carry a `mass` (kg). Their total sets the player's load tier
  (`player/burden.py`, `Player.burden`): heavier gear walks slower, refills ST slower and pays more ST
  for attacks, sprinting and blocking. New gear needs a `mass` (`tests/test_burden.py`).
- Belongings is split into tabs (`belongings.TABS`: Items, Weapons, Armor, Spells, Unique), switched
  with `tab_prev` / `tab_next` (A / D, Left / Right) or a click; `tab_of` files each item kind.
- Every attack costs ST. Each category's moveset (`weapons.MOVESETS`) is tuned for a medium weapon;
  an item's `weight` (`light` / `medium` / `heavy` / `great`) scales each attack's ST, damage and poise
  through `weapons.WEIGHTS` (`weapons.attack` returns the sized Attack) and adds `WEIGHT_TEMPO` to its
  `tempo`, which sets how long its swings take. Each hand's ATK gauge refills over the weapon's
  `speed` times `weapons.GAUGE_REFILL` (`weapons.refill_time`); a swing hits as hard as the gauge was
  full. Attacks that strike twice (the Aftershock) use `pulses`. Attack poses are keyframed in
  `models.MOTIONS` (wind, strike, follow, each `(dx, dy, dz, rx, ry, rz)`), the strike lands at the
  attack's `hit_at`, and edged weapons (`TRAILS`) smear a fan of ghost blades through the blow. A motion
  ends part way home (`models._settle`); the view's `PoseBlend` (`player/view_blend.py`, kept by `Game`
  and passed to `models.weapon_view`) eases the arms the rest of the way, into each new swing, charge or
  shield raise, and lets them trail the turning view (`Sway`). The viewmodel draws over the world
  on a depth buffer of its own (`Game` wipes only depth before it), so its parts sort among themselves:
  a fist's fingers pass in front of the grip they close round and its palm behind.
- Secret attacks are listed in `weapons.secret()`; performing one adds a `secret:<category>` flag,
  which reveals its name in Belongings and the shop.
- Weapon arts (`weapons.ARTS`, keyed by item id: the Ashblade's Ember Spill, Stormbrand's Thunderstroke,
  Thornlash's Thorn Volley, Slagbreaker's Slag Burst): releasing a heavy with both the ATK gauge and the
  heavy charge full, and the art's `mp`, sets `Player.swing_art` (`art_ready`; a secret outranks it), and
  `Game._release_art` looses it as the blow lands, through the spells' plumbing (`World.flame_cone`, which
  Pyre shares, `fire_bolt`, `volley`, `slag_ring`). The weapon button's bar shows the ATK gauge on its top
  row and the heavy charge on its bottom one (`ui/atk_bar.py`); a ready art burns it in the art's `rgb`.
  Belongings and the shop list the art under the weapon's moves.
- Weapons may carry an `element` (`"lightning"`, `"fire"`): `Game._strike` multiplies by
  `elements.mult` and a fire weapon leaves `burn` on what it hits.
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
- The story: the player is one of the Ashen, woken in the Cemetery of Ashes by a toll of the town's bell
  that no one rang. Odrin knows the prophecy: whoever wakes must win four sigils to raise the king turned
  to stone on the cathedral's throne (the Enthroned); many Ashen woke before and failed. Nobody arrived by
  sea. Only three sigils exist yet, and the ending takes those three; the fourth's place, who rang the
  bell and what petrified the king are `TODO(story)`s in `dialogue.py`.
