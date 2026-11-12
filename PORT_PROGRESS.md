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
- [x] tests/test_render_logic.py (textures, mesh batches, rig math) — 32 passing

GPU note: `gpu.py` is untested until the game window opens (smoke run). Rig.at/entity are context managers: `with rig.at(...):`.

## To do
- [x] render/shaders (copy ps1.vs / ps1.fs as-is)
- [x] render/texture_gen
- [x] render/mesh_builder
- [x] render/gpu
- [x] render/rig
- [x] render/models
- [x] world/world (raylib-dependent runtime world)
- [x] audio/synth
- [x] input (incl. --script driver)
- [x] ui/hud
- [x] data/dialogue.py
- [x] game.py + __main__.py + bin/ashen_vault launcher (--map --at --smoke --script --shot)
- [x] smoke run on both maps
- [ ] remove Ruby files, update README

## Smoke results (pass 3)
- harrowmere 60 frames: state line identical to Ruby build; screenshot pixel-identical to Ruby's.
- sunken_keep --at 15,21,180 scripted attack/cast/menu: combat, flame bolt, inventory preview OK, 60 fps.
- title -> Controls via script OK.
- `python -m ashen_vault` is the entry point; bin/ashen_vault is still the Ruby script (swap in final pass).
