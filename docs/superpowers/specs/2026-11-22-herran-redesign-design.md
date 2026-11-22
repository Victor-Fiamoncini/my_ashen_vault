# Herran's Castle & Spire redesign

## Intent
Rebuild `herrans_castle` and `herran_spire` as small, dark, claustrophobic areas: towers to climb,
narrow corridors, Victorian walls (in the spirit of Vesperholm). References: Heide's Tower of Flame
(DS2: towers joined by walkways over sheer drops) and Blasphemous 2's Crown of Towers (a ring of towers
round a central void, repeated lifts). Everything original; nothing copied.

## Goals
- Castle about 30x40 tiles (was ~56 wide); spire about half its size.
- Dark: stormy night over the cloud sea; gas lamps are the light (my call over a fully enclosed one).
- Victorian walls: sooty red brick, dark slate caps, iron railings, piers, lancet windows.
- Four explorable towers round a central void; 1-2 tile corridors.
- One secret lab (was three), darker than the rest, holding all three secret items and a journal page.

## Non-goals / anti-goals
- No new enemies, bosses, items or story beats.
- Don't break the links to the rest of the game: the sky stair, Spire Key, spire door, `herran_dead`,
  item flags, cage-lift shortcut, `fall=cloud` / `void` chasm.
- No image or audio files.

## Approach
Rewrite both `.map` files from scratch (picked), versus trimming the current maps (would keep the open
court layout we want gone). Retune the sky and textures in place; add only what the layout needs.

## Layout (castle)
1. Cloud Quay: arrival from the sky stair, shrine, one cramped gatehouse corridor in.
2. The Ring: a narrow brick passage round the void, arches opening onto the drop.
3. Towers: Aviary (drakes, loot), Clock (climb to the 10 m level), Belvedere (locked cage lift down to
   the Ring: the shortcut), Laboratory (Spire Key; secret lab behind a `secret_wall` below it,
   `dark` >= 0.6).
4. High Walk: one iron-grating bridge across the void at ~10 m to the spire door, seen from below
   throughout the climb.

## Layout (spire)
Base hall -> short dim hatchery corridor -> study with shrine and last journal page -> `door
boss=herran_dead` -> observatory, kept open and wide as the contrast.

## Dropped places (my call)
Lower Court as an open court, Great Stair, Belvedere Terrace, the two extra hidden labs.

## Left to the builder
Exact grids, enemy placement, lamp placement, sky constants; tests updated to the new routes.
