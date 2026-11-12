# Ashen Vault

A first-person dungeon crawler in the spirit of 1990s PS1 dungeon crawlers, written in Python with
[raylib-python-cffi](https://github.com/electronstudio/raylib-python-cffi) (`pyray`). All names, maps, monsters,
story and art are original. Every texture, model and sound is generated in code.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
bin/ashen_vault                  # or: .venv/bin/python -m ashen_vault
.venv/bin/pytest                 # headless logic tests
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

- `ashen_vault/core.py`: re-exports the raylib-free game logic (maps, collision, combat, AI, saves), covered by `tests/`
- `ashen_vault/world/`, `player/`, `ai/`, `save/`: that logic, module by module
- `ashen_vault/render/`: PS1 shader, procedural textures, map mesh builder, low-poly models
- `ashen_vault/game.py`: scenes and the main loop; `ui/hud.py` the 2D overlay; `audio/synth.py` the sound effects
- `data/maps/*.map`: plain-text tile maps (`[meta]`, `[legend]`, `[grid]`, `[entities]`)
- `data/dialogue.py`: NPC conversations

## Debug flags

```sh
bin/ashen_vault --map sunken_keep --at 15,21,180 --smoke 100 --script "wait:1.2 attack" --shot out.png
```

`--smoke N` runs N frames, writes a 3x screenshot and prints a state summary. `--script` drives input.
The save file lives at `~/.local/share/ashen_vault/save.json`; set `ASHEN_VAULT_SAVE` to override it.
