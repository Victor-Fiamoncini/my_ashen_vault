# Ashen Vault

A first-person dungeon crawler in the spirit of 1990s PS1 King's Field games, written in Ruby with
[raylib-bindings](https://github.com/vaiorabbit/raylib-bindings). All names, maps, monsters, story and
art are original. Every texture, model and sound is generated in code.

## Run

```sh
bundle config set --local path vendor/bundle
bundle install
bundle exec bin/ashen_vault      # or: bundle exec rake run
bundle exec rake test            # headless logic tests
```

## Controls

| Action | Keys |
| --- | --- |
| Move / strafe | W S / A D (or arrow up/down) |
| Sprint | Hold Shift |
| Turn / look | Arrow left/right, mouse, PgUp/PgDn |
| Attack | Space / left mouse |
| Cast spell / cycle spell | F or right mouse / R |
| Use, talk, open | E |
| Belongings | Tab or I |
| Quick Red Tonic / Blue Moss | 1 / 2 |
| Pause | Esc |

The same list is in the game under **Controls** on the title and pause menus. In Belongings, Enter on an
equipped item (marked `(E)`) takes it off; with no weapon you fight bare-handed.

Your swing damage scales with the **ATK** gauge, so wait for it to refill (it won't while you sprint). Spells need a full **MAG** gauge.
The stone shrines save your progress and restore you.

## Layout

- `lib/ashen_vault/core.rb`: raylib-free game logic (maps, collision, combat, AI, saves), covered by `test/`
- `lib/ashen_vault/render/`: PS1 shader, procedural textures, map mesh builder, low-poly models
- `data/maps/*.map`: plain-text tile maps (`[meta]`, `[legend]`, `[grid]`, `[entities]`)
- `data/dialogue.rb`: NPC conversations

## Debug flags

```sh
bin/ashen_vault --map sunken_keep --at 15,21,180 --smoke 100 --script "wait:1.2 attack" --shot out.png
```

`--smoke N` runs N frames, writes a 3x screenshot and prints a state summary. `--script` drives input.
The save file lives at `~/.local/share/ashen_vault/save.json`; set `ASHEN_VAULT_SAVE` to override it.
