# Ruby → Python port progress

Ruby original: commit 4ce7f52. Python package: `ashen_vault/`. Run tests with `.venv/bin/pytest -q`.

Notes: use `ashen_vault.util.rround` wherever Ruby called `.round` (Ruby rounds half away from zero).
Ruby `a..b` gold ranges are `range(a, b + 1)`; pick with `rng.choice(type.gold)`.
Ruby predicates `alive?`/`gone?`/`full?`/`dead?` became properties; `has?`/`equipped?` are methods.

## Done
- [x] core logic: world/tile_map, world/map_loader, world/collision
- [x] player: combat, stats, items, inventory, spells, player
- [x] ai: enemy_types, enemy
- [x] save/save_system
- [x] tests: test_world, test_rpg, test_enemy (29 passing)

## To do
- [ ] render/shaders (copy ps1.vs / ps1.fs as-is)
- [ ] render/texture_gen
- [ ] render/mesh_builder
- [ ] render/gpu
- [ ] render/rig
- [ ] render/models
- [ ] world/world (raylib-dependent runtime world)
- [ ] audio/synth
- [ ] input (incl. --script driver)
- [ ] ui/hud
- [ ] data/dialogue.py
- [ ] game.py + __main__.py + bin/ashen_vault launcher (--map --at --smoke --script --shot)
- [ ] smoke run on both maps
- [ ] remove Ruby files, update README
