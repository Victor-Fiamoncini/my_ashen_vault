# Herran's Castle & Spire Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `herrans_castle` and `herran_spire` as small, dark, tower-heavy Victorian areas over a stormy night cloud sea, with one secret lab.

**Architecture:** Content work: new `.map` grids, a new `storm` sky in `world/sky.py`, darker procedural textures, and updated tests in `tests/test_herrans_castle_world.py` (plus the cross-map tables in `test_sky.py`, `test_arena.py`). No new item, enemy or model types.

**Tech Stack:** Python 3.11+, raylib (`pyray`), pytest, ruff, uv.

**Spec:** `docs/superpowers/specs/2026-11-22-herran-redesign-design.md`

## Global Constraints

- Never reformat a `.map` file; each grid character is one 2 m tile; grids are whitespace-sensitive.
- All original: no names, maps or layouts copied from Dark Souls 2, Blasphemous 2 or any other game.
- No image or audio files; textures stay procedural (`render/texture_gen.py`).
- Pure packages (`world/`, `player/`, `ai/`, `save/`) import no raylib.
- Use `util.rround`, not `round`, in game math.
- Player-facing text never says "hand" for equipment slots; `[meta] name` stays "Herran's Castle" / "Herran's Spire".
- Steps of floor never rise more than 0.5 m a tile (walkable climbs).
- Always smoke with `ASHEN_VAULT_SAVE=/tmp/ashen_test_save.json`.
- Done = `uv run ruff check`, `uv run ruff format --check`, `uv run pytest --cov` green, plus smoke screenshots.

## Review Focus

- Arriving by the sky stair from Vesperholm lands on the new `start` (Vesperholm's exit `at=` must move with it) — covered by the existing stair test.
- A player who dies in the spire arena and returns finds fog at the new lair tile — `test_arena.py` lair coords updated in Task 4.
- Taking the cage lift before riding it down: both ends reachable before first ride — kept in the solvability test.
- Darkness too deep to read the corridors without Lumen in the main route (only the secret lab may need a light) — Task 3 asserts main-route `dark` <= 0.35.
- Old saves standing at coords that no longer exist in the castle — load must place them at `start` if the tile isn't walkable; Task 3 adds `test_an_old_save_on_a_solid_tile_wakes_at_the_quay` only if `World` does not already do this (check `save/` load path first; if handled, no test).

---

### Task 1: The `storm` sky

**Files:**
- Modify: `src/ashen_vault/world/sky.py` (add `SKIES["storm"]` beside `"aloft"`)
- Modify: `tests/test_sky.py:20-29`

**Interfaces:**
- Produces: sky name `storm`, used as `[meta] sky = storm` by Tasks 3 and 4.

- [ ] **Step 1: Failing test** — in `test_each_outdoor_map_names_a_sky_and_the_keep_has_none` change both Herran entries to `sky.SKIES["storm"]`; add `test_the_storm_is_dark_over_the_clouds`: `s = sky.SKIES["storm"]; assert max(s.zenith) < 0.1 and s.cloud_sea is not None and s.far_moon is None and s.stars == 0 and max(s.cloud_sea) < 0.45`.
- [ ] **Step 2: Run** `uv run pytest tests/test_sky.py -v` — FAIL (KeyError `storm`).
- [ ] **Step 3: Implement** `"storm": Sky(...)`: near-black slate zenith (~0.04,0.04,0.07), sun veiled (reuse the `veiled=` field as in `moonlit`) and dim, heavy low clouds (`cap=True`), `drift` ~0.01, dark `cloud_sea` (~0.3,0.3,0.36), no stars, no `far_moon`.
- [ ] **Step 4: Run** — still FAIL on the map test (maps not yet changed). Temporarily set `sky = storm` in both maps' `[meta]` (one-line meta edit, grids untouched); run — PASS. Update the two `meta["sky"] == "aloft"` asserts in `test_herrans_castle_world.py` to `"storm"`.
- [ ] **Step 5: Commit** `feat(sky): stormy night over Herran's castle`.

### Task 2: Darker Victorian textures

**Files:**
- Modify: `src/ashen_vault/render/texture_gen.py` (`herran_brick`, `herran_slate`, `encaustic_tile`, `lab_tile`; `herran_ashlar` kept only for trim/edges)
- Test: `tests/test_render_logic.py` (existing texture tests must stay green)

- [ ] **Step 1:** Retune `herran_brick` to sooty dark red with black mortar streaks and lancet-arch-friendly coursing; `herran_slate` near-black blue; `encaustic_tile` deep oxblood/ochre; `lab_tile` grimy green-grey with stains. Mean luminance of each ≤ 0.35 (check by eye in smoke, Task 6).
- [ ] **Step 2: Run** `uv run pytest tests/test_render_logic.py -q` — PASS.
- [ ] **Step 3: Commit** `feat(render): soot the castle's brick and tile`.

### Task 3: Rebuild `herrans_castle.map`

**Files:**
- Rewrite: `src/ashen_vault/maps/herrans_castle.map`
- Modify: `src/ashen_vault/maps/vesperholm.map:252` (only the `at=` of `ÿ`, to the new start)
- Modify: `tests/test_herrans_castle_world.py`

**Interfaces:**
- Produces: castle tiles where `J` (spire exit) and the `at=` of the spire's way back must agree (Task 4).

Layout (≤ 32 wide × 42 deep, cloud `_` border ≥ 2 tiles on every side):
- South: **Cloud Quay** at h=0 — `start`, shrine `B`, sky stair `A`, a broken balustrade gap onto `_` (keeps the plunge test), gas lamps. One 1-wide gatehouse corridor north (`p`, roofed, `dark=0.3`).
- Middle: **the Ring** at h=1, a 1–2 wide roofed passage looping round a central void of `_` (≈8×10 tiles); every 3–4 tiles an arched opening (a `b` balustrade tile) onto the void.
- Four towers off the Ring, each a 3×3 to 4×4 shell of `%` walls with a spiral of half-metre steps (reuse the α…η pattern) and 1–2 small rooms:
  - **Aviary** (SE): up to 4 m, drakes, chest `G` (bitter_root).
  - **Clock** (SW): Ring 1 m → 10 m; its top room opens onto the **High Walk**.
  - **Belvedere** (NE): top room at 10 m; locked cage lift `L` (`top=10`, `on=e`) dropping to a Ring tile at 1 m.
  - **Laboratory** (NW): ground room `l` with chest `K` (spire_key), ledger hint `À`; a `secret_wall` `W` in its floor-level back wall to **the secret lab** (`s`, `dark=0.65`, ≈4×5 tiles) holding chests `D` graft_draught, `F` sun_tincture, `E` herran_bonesaw, journal hint `Á`, vats, jars, surgery table.
- North: **High Walk** `h` (iron_grating, h=10), 1 wide, over the void from the Clock's top to the Belvedere's top and on north to a short passage `q`, `door key=spire_key` `H`, then exit `J` (keep its props; set `at=` to the spire's new start).
- Remaining hints `Â`, `Ã` go one each in the Clock and Belvedere top rooms.
- Towers on the skyline: one `herran_tower` per tower (`clock`, `belvedere`, `round`, `octagon`) on `%`, and `needle` on `&` over the spire passage. Drop the `glasshouse` and `drake_fountain`.
- `[meta]`: `sky = storm`, `ambient = 0.42 0.4 0.48`, `fog = 0.12 0.12 0.16`, `fog_range = 10 60`, `model_range = 40`, `indoor_range = 18`, `torch = 6 1.0 0.72 0.45`, keep `edge_top = -40`, `roofs = true`, `entity_floor = auto`.
- Enemies: ~2 `grafted_drake` over the void/High Walk, ~3 `drake_magus` in towers, ~2 `vat_spawn` (one in the secret lab).

- [ ] **Step 1: Update tests first.**
  - `test_herrans_castle_is_solvable_up_to_the_spires_door`: `assert len(secrets) == 1`; lab chests behind the wall become `{graft_draught, sun_tincture, herran_bonesaw}` and each `not in before`; keep the lift asserts (`{1.0, 10.0}`); keep the strand check.
  - `test_the_castle_climbs_in_steps_never_too_tall`: floors `{0.0, 1.0, 10.0} <= floors`; add every adjacent walkable pair on the main route differs by ≤ 0.5 m except across lifts/doors.
  - `test_the_castles_dressing_draws_and_stands_still`: map styles assert becomes `{"round", "octagon", "clock", "belvedere", "needle"} <= set(styles)` (unchanged) — no glasshouse required in the map.
  - New `test_the_castle_is_small_and_dark`: `m.width <= 34 and m.depth <= 44`; `float(m.meta["ambient"].split()[0]) <= 0.5`; every reachable walkable tile with a ceiling has `dark` ≤ 0.35 except `lab_tile` tiles behind the secret wall, which have `dark >= 0.6`.
  - New `test_the_secret_lab_is_one_room`: the tiles reachable only once `W` opens form one connected region containing all three secret chests and one journal hint.
  - `test_a_landed_drake_rends...`: replace `(27, 57+2)`, `(28, 59)`, `(27, 52)` with three open Ring tiles of the new map (pick from the grid; any walkable h=1 tiles 1–7 apart).
- [ ] **Step 2: Run** `uv run pytest tests/test_herrans_castle_world.py -v` — FAIL (old map).
- [ ] **Step 3: Write the map** per the layout above (sketch it first in `tools/level_planner` or as ASCII; paste the grid into the map). Set Vesperholm's `ÿ` `at=` to the new `start`.
- [ ] **Step 4: Run** the castle tests, then `uv run pytest tests/test_seating.py tests/test_prop_bake.py tests/test_render_logic.py tests/test_vesperholm_world.py -q` — PASS (fix entity placements the seating/bake tests flag).
- [ ] **Step 5: Commit** `feat(maps): rebuild Herran's Castle as a ring of towers`.

### Task 4: Rebuild `herran_spire.map`

**Files:**
- Rewrite: `src/ashen_vault/maps/herran_spire.map`
- Modify: `tests/test_herrans_castle_world.py` (spire tests), `tests/test_arena.py:34`

Layout (≤ 24×28): base hall `start` with exit `X` back to the castle (its `at=` beside the castle's `J`), a 1-wide dim spiral to the **hatchery** (vats, ~6 m, `dark=0.4`), on to the **study** at 11 m (shrine, chest `C`, hint `À`, operating table, shelf), `door boss=herran_dead` `D`, and the **observatory** at 11 m, open to the sky (`ceil` none), parapet of wall tiles round it (never chasm), `observatory_dome`, `telescope`, `herran`. `sky = storm`, same darkness meta as the castle.

- [ ] **Step 1: Tests first** — in `test_herrans_spire_climbs...` add `assert m.width <= 24 and m.depth <= 28`; keep the rest. In `test_arena.py` set the Herran lair coordinate to the planned observatory tile.
- [ ] **Step 2: Run** `uv run pytest tests/test_herrans_castle_world.py tests/test_arena.py -v` — FAIL.
- [ ] **Step 3: Write the map**; set the castle's `J` `at=` to the spire's `start` and the spire's `X` `at=` beside `J`.
- [ ] **Step 4: Run** the same tests plus `tests/test_great_gate.py tests/test_seating.py tests/test_prop_bake.py tests/test_render_logic.py -q` — PASS.
- [ ] **Step 5: Commit** `feat(maps): a tighter, darker Herran's Spire`.

### Task 5: Docs

**Files:**
- Modify: `docs/dev/maps.md` (the `herrans_castle` / `herran_spire` paragraph, ~lines 105–126), `docs/dev/smoke-starts.md` (Herran entries), map header comments.

- [ ] **Step 1:** Rewrite the paragraph for the Quay → Ring → four towers → High Walk → spire, one secret lab, `storm` sky; update smoke starts to new tiles (quay, each tower top, secret lab, spire study, arena door).
- [ ] **Step 2: Commit** `docs: describe the rebuilt castle and spire`.

### Task 6: Verify

- [ ] `uv run ruff check` and `uv run ruff format --check` — clean.
- [ ] `uv run pytest --cov` — all pass, coverage ≥ `fail_under`.
- [ ] Smoke each start from `smoke-starts.md`, e.g. `ASHEN_VAULT_SAVE=/tmp/ashen_test_save.json uv run ashen-vault --map herrans_castle --at <quay> --smoke 120 --shot /tmp/opencode/quay.png`, plus the secret lab with `--flags` none and the spire arena with `--map herran_spire`. View each shot: corridors readable by lamp light, secret lab clearly darker, towers on the skyline, sky dark.
