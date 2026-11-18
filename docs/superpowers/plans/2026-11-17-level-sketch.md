# Level Sketch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A standalone browser page, `tools/level_sketch/index.html`, for sketching Ashen Vault levels top-down
in free shapes and lines measured in metres, over an optional faint underlay of a game map, saved as
`.sketch.json` + `.svg` files in the repo.

**Architecture:** Three classic scripts loaded by one HTML page, no build step, opened from disk:
`model.js` (pure: kinds, sketch schema, geometry, undo history, SVG output, underlay paths; also
`require`-able by Node for tests), `storage.js` (localStorage autosave, File System Access save/open with a
download fallback) and the UI inline in `index.html`. A Python script turns a `.map` into underlay JSON,
reusing the planner's map parsing.

**Tech Stack:** Vanilla JS (ES2022) + inline SVG; Node's built-in test runner (`node --test`, Node 26 is
installed) for `model.js`; Python 3.11 + pytest for the underlay script.

**Spec:** `docs/superpowers/specs/2026-11-17-level-sketch-design.md`

## Global Constraints

- Everything lives in `tools/level_sketch/`; nothing under `src/` changes. No image or audio files enter the game.
- No build step, no npm dependencies. The page must work opened as `file:///…/tools/level_sketch/index.html` in
  Chrome: load scripts with plain `<script src="model.js"></script>` (ES modules are blocked on `file://`).
  Fonts may come from Google Fonts, as the planner's do; nothing else is fetched.
- 1 SVG user unit = 1 metre; x east, y south, origin at the sketch's top-left; one tile = 2 m.
- Sketch file format: `"format": "ashen-vault-sketch"`, `"version": 1`, exactly the shape in the spec's
  "The sketch file" section. Unknown fields survive a load/save round trip.
- Defaults: size `[120, 120]` m, one layer `{"id": "l1", "name": "Ground"}`, snap off, nudge 0.5 m
  (shift 2 m), undo depth at least 150, underlay opacity 30%.
- Grid: thin line every 2 m, strong every 10 m. Snap: 1 m, 2 m with Alt. Rotate with shift: 15° steps.
- Look: copy the planner's colour tokens, fonts and light/dark theme blocks (`tools/level_planner/index.html`
  lines 9–40), its three-column layout (tools left, canvas centre, properties right) and status bar.
- Python: ruff settings from `pyproject.toml` (line length 110, double quotes); `uv run ruff check`,
  `uv run ruff format --check` and `uv run pytest` must stay green.
- Commit only when Victor asks (AGENTS.md). The "Checkpoint" steps below say what would go in one commit; run
  them as `git add` + `git commit` only with his go-ahead.

## Review Focus

1. **A malformed, partial or older sketch file**: missing `layers`, an item without `kind`, an unknown kind, extra
   fields. It should load with defaults filled in, keep the extra fields and refuse only a file that isn't a sketch
   at all, with a readable message. Task 2's `normalize` tests pin this.
2. **Rotated shapes**: clicking inside a rotated rectangle's visual area selects it, and dragging a resize handle
   resizes it along its own axes, not the screen's. Task 3's `hitTest`/`resizeItem` tests pin this.
3. **Labels and notes with `<`, `&`, quotes or accents** in the SVG export, and on the canvas: they must show as
   typed and never break the file. Task 4's `toSvg` escaping test pins this.
4. **Typing in a text field**: Delete, Backspace, arrow keys, V/R/E… pressed while the label, note or a number
   field has focus must edit the field, never delete, nudge shapes or switch tools. Task 7's manual check
   pins this, and `isTypingTarget` in Task 7 is the single gate every shortcut passes through.
5. **A big underlay** (Harrowmere is 64x52 tiles, the jungle larger): panning and zooming stay smooth. Underlays
   draw as one merged `<path>` per kind, never a `<rect>` per tile. Task 9's `underlayPaths` test pins the merging.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `tools/level_sketch/map_to_underlay.py` | `.map` → underlay JSON (tile kinds per cell, landmarks in metres) |
| `tests/test_map_to_underlay.py` | pytest for it, on the real maps |
| `tools/level_sketch/model.js` | Pure logic: kinds, schema, geometry, history, SVG, underlay paths. Exposes `SketchModel` on `globalThis` and `module.exports` |
| `tools/level_sketch/model.test.js` | `node --test` tests for `model.js` |
| `tools/level_sketch/storage.js` | Autosave, save/open through the File System Access API, download/file-picker fallback. Exposes `SketchStorage` |
| `tools/level_sketch/index.html` | Page, styles, UI state, tools, panels, rendering |
| `tools/level_sketch/sketches/.gitkeep` | The folder sketches are saved into |
| `AGENTS.md` | One row in the Layout table |

---

### Task 1: Underlay script

**Files:**
- Create: `tools/level_sketch/map_to_underlay.py`
- Test: `tests/test_map_to_underlay.py`

**Interfaces:**
- Consumes: `sections(text) -> dict[str, list[str]]` and `entries(lines) -> dict[str, str]` from
  `tools/level_planner/map_to_planner.py` (import it by putting that folder on `sys.path` at the top of the script).
- Produces (used by Task 9): underlay JSON
  ```json
  {"format": "ashen-vault-underlay", "version": 1, "map": "harrowmere", "name": "Harrowmere",
   "w": 64, "h": 52, "tile_m": 2,
   "codes": {"#": "wall", ".": "floor", "i": "indoor", "~": "sea", "r": "water", "L": "lava",
             "c": "chasm", "m": "mud", "t": "thorns"},
   "rows": ["####....", "..."],
   "marks": [{"kind": "gate", "x": 5.0, "y": 59.0, "label": "Cemetery gate", "note": "To ashen_cemetery"}]}
  ```
  `rows[z][x]` is a code char; `marks` positions are tile centres in metres (`x = tx*2+1`, `y = tz*2+1`).
- Python functions: `underlay_kind(spec: str) -> str` (one of the `codes` values),
  `convert(path: Path) -> dict`, `main() -> None` (`map_to_underlay.py <map file>` prints the JSON).

- [ ] **Step 1: Write the failing tests** in `tests/test_map_to_underlay.py` (load the script with
  `importlib.util.spec_from_file_location` from `tools/level_sketch/map_to_underlay.py`):

```python
@pytest.mark.parametrize(
    ("spec", "kind"),
    [
        ("wall tex=black_brick top=8 cap=slate", "wall"),
        ("wall tex=stone thin=0.5", "wall"),
        ("water tex=sea h=-1 deep", "sea"),
        ("water tex=bog h=-0.5 side=mud", "water"),
        ("floor tex=lava h=-8 side=cliff_rock chasm", "lava"),  # lava wins over chasm
        ("floor tex=lava h=-1 ceil=6 lava", "lava"),
        ("floor tex=ravine h=-5 side=cliff_rock chasm", "chasm"),
        ("floor tex=stone h=0 pit", "chasm"),
        ("floor tex=mud h=-0.2 side=mud slow=0.65", "mud"),
        ("floor tex=thorns h=0 side=mud hurt=5", "thorns"),
        ("floor tex=leaf_litter h=0 ceil=4.6", "indoor"),
        ("floor tex=jungle_floor h=0 side=bark", "floor"),
    ],
)
def test_underlay_kind(spec, kind):
    assert mod.underlay_kind(spec) == kind


@pytest.mark.parametrize("name", ["harrowmere", "verdant_hollow", "cinderhold", "cinder_keep"])
def test_convert_real_maps(name):
    out = mod.convert(MAPS / f"{name}.map")
    assert out["format"] == "ashen-vault-underlay" and out["version"] == 1 and out["tile_m"] == 2
    assert len(out["rows"]) == out["h"] and all(len(r) == out["w"] for r in out["rows"])
    assert set("".join(out["rows"])) <= set(out["codes"])
    json.dumps(out)  # serialisable


def test_cinderhold_has_lava_and_harrowmere_has_sea():
    assert "L" in "".join(mod.convert(MAPS / "cinderhold.map")["rows"])
    assert "~" in "".join(mod.convert(MAPS / "harrowmere.map")["rows"])


def test_marks_are_tile_centres_in_metres():
    out = mod.convert(MAPS / "harrowmere.map")
    start = next(m for m in out["marks"] if m["kind"] == "start")
    assert (start["x"], start["y"]) == (2 * 2 + 1, 29 * 2 + 1)  # harrowmere: start = 2 29 0
    assert any(m["kind"] == "npc" and m["label"] == "Odrin" for m in out["marks"])
    assert any(m["kind"] == "shrine" for m in out["marks"])
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_map_to_underlay.py -v`
Expected: FAIL (file not found / no module).

- [ ] **Step 3: Implement `map_to_underlay.py`**

`underlay_kind` checks in this order: `wall` → `"wall"`; `water` → `"sea"` if `deep` else `"water"`; a `lava`
token or `tex=lava` → `"lava"`; `chasm` or `pit` → `"chasm"`; `slow=` → `"mud"`; `hurt=` → `"thorns"`; `ceil=` →
`"indoor"`; else `"floor"`. An entity tile takes the kind of its `on=` tile; without one, the kind most of its
non-wall neighbours have (three passes, as `map_to_planner.convert` does), else the kind of the `[meta]`
`default` tile, else `"floor"`. Marks: `npc` (label `id` capitalised), `exit` (kind `well` / `cave` / `gate` by
`model=`, note `To <map>`), `cemetery_gate` (gate), `save_statue` (shrine), `door boss=` (boss, label the flag),
`lift` (lift), and `[meta] start` (start).

- [ ] **Step 4: Run the tests, ruff, and try it**

Run: `uv run pytest tests/test_map_to_underlay.py -v && uv run ruff check tools tests && uv run ruff format --check tools tests`
Expected: all PASS, ruff clean.
Run: `uv run python tools/level_sketch/map_to_underlay.py src/ashen_vault/maps/cinderhold.map | head -c 300`
Expected: JSON starting `{"format": "ashen-vault-underlay", "version": 1, "map": "cinderhold"`.

- [ ] **Step 5: Checkpoint** — `tools/level_sketch/map_to_underlay.py tests/test_map_to_underlay.py`

---

### Task 2: Model — kinds and the sketch schema

**Files:**
- Create: `tools/level_sketch/model.js`, `tools/level_sketch/model.test.js`

**Interfaces:**
- Produces (all on `SketchModel`):
  - `KINDS: {id, name, group, color}[]` and `KIND: Record<id, kind>`. Groups and ids, in this order:
    Ground: `street, plaza, terrace, steps, garden, jungle_floor, bog, cave_floor, fortress_floor, ash`;
    Indoors: `house_interior, hall, dungeon_room`;
    Walls: `town_wall, cliff, stone_house, timber_house, great_wall, low_wall, hedge, fortress_wall`;
    Water and void: `sea, canal, lava, chasm`; Structures: `pier, bridge, ledge, lift_shaft`; Zone: `zone`;
    Other: `other`. Colours: the planner's `TILES` colours where it has the tile (street `#a39d90`, plaza
    `#c8b791`, terrace `#bcb4a3`, steps `#ddd4c0`, garden `#6f8b49`, jungle_floor `#4e6b34`, cave_floor `#3a342d`,
    house_interior `#caa77b`, hall `#8f84a8`, town_wall `#3c3944`, cliff `#5a554c`, stone_house `#7c7192`,
    timber_house `#7f5b3c`, great_wall `#4c3f66`, low_wall `#6d6a63`, hedge `#2f4a22`, sea `#22466b`, canal
    `#3f7aa3`, pier `#9c6b3e`); pick the rest in keeping (lava a hot orange, chasm near-black).
  - `MARKER_KINDS: {id, name, color, glyph}[]`, `MARKER: Record<id, …>`: the planner's `KINDS` (npc, shop,
    gate, well, cave, shrine, boss, enemy, chest, landmark, door, start, note) plus `lift` (glyph `⇕`).
  - `newSketch(name: string) -> Sketch`
  - `normalize(data: unknown) -> Sketch` (throws `Error("Not an Ashen Vault sketch")` when `format` is present and
    different, or `data` isn't an object)
  - `slug(name: string) -> string`
  - `newId(prefix: "l" | "s" | "m" | "t") -> string` (unique within the page session)
  - `serialize(sketch: Sketch) -> string` (`JSON.stringify(sketch, null, 2)` + `"\n"`)
- Item types: `rect`, `ellipse` (`x, y` centre, `w, h`, `rot`), `polygon`, `line` (`points: [x, y][]`, line has
  `width`, default 2), `marker` (`x, y`, `kind` a marker kind), `text` (`x, y`, `text`, `size`, default 3). Shared
  optional fields: `label`, `note`, `color` (override), `opacity` (default 1; 0.35 for `zone`), `height_m`,
  `locked`.

The file ends with `if (typeof module !== "undefined") module.exports = SketchModel; globalThis.SketchModel = SketchModel;`.

- [ ] **Step 1: Write the failing tests** (`node:test`, `node:assert/strict`, `const M = require("./model.js")`):

```js
test("newSketch has the spec's defaults", () => {
  const s = M.newSketch("Harrowmere v2");
  assert.equal(s.format, "ashen-vault-sketch"); assert.equal(s.version, 1);
  assert.equal(s.name, "harrowmere-v2"); assert.deepEqual(s.size_m, [120, 120]);
  assert.equal(s.layers.length, 1); assert.equal(s.layers[0].name, "Ground"); assert.deepEqual(s.layers[0].items, []);
});
test("slug", () => {
  assert.equal(M.slug("Cinderhold  REDO!"), "cinderhold-redo");
  assert.equal(M.slug("***"), "sketch");
  assert.equal(M.slug("a".repeat(60)).length, 40);
});
test("every kind has a colour and a known group; ids are unique", () => { /* KINDS, MARKER_KINDS */ });
test("normalize fills defaults and keeps unknown fields", () => {
  const s = M.normalize({ format: "ashen-vault-sketch", version: 1, future: 7,
    layers: [{ name: "Ground", items: [{ type: "rect", x: 1, y: 2, w: 3, h: 4, extra: "kept" }] }] });
  assert.equal(s.future, 7); assert.deepEqual(s.size_m, [120, 120]);
  const it = s.layers[0].items[0];
  assert.equal(it.extra, "kept"); assert.equal(it.kind, "other"); assert.equal(it.rot, 0); assert.ok(it.id);
  assert.ok(s.layers[0].id); assert.equal(s.layers[0].visible, true);
});
test("normalize: no layers gives one empty Ground layer", () => {
  assert.equal(M.normalize({ format: "ashen-vault-sketch" }).layers[0].name, "Ground");
});
test("normalize: unknown kind becomes other, keeping the original as kind_was", () => {
  const it = M.normalize({ layers: [{ items: [{ type: "rect", kind: "volcano", x: 0, y: 0, w: 1, h: 1 }] }] }).layers[0].items[0];
  assert.equal(it.kind, "other"); assert.equal(it.kind_was, "volcano");
});
test("normalize drops items of unknown type and points that aren't numbers", () => { /* type "blob" gone; polygon with < 3 valid points gone; line with < 2 gone */ });
test("normalize refuses what isn't a sketch", () => {
  assert.throws(() => M.normalize({ format: "ashen-vault-underlay" }), /Not an Ashen Vault sketch/);
  assert.throws(() => M.normalize("hello"), /Not an Ashen Vault sketch/);
});
test("serialize round-trips through normalize unchanged", () => { /* a sketch with every item type */ });
```

- [ ] **Step 2: Run and see them fail** — `node --test tools/level_sketch/` → FAIL (`Cannot find module`).
- [ ] **Step 3: Implement** the interfaces above in `model.js`.
- [ ] **Step 4: Run** — `node --test tools/level_sketch/` → all PASS.
- [ ] **Step 5: Checkpoint** — `tools/level_sketch/model.js tools/level_sketch/model.test.js`

---

### Task 3: Model — geometry

**Files:** Modify `tools/level_sketch/model.js`, `tools/level_sketch/model.test.js`

**Interfaces:**
- Produces (`Pt = [x, y]` in metres; every function returns a new item, never mutates):
  - `bounds(item) -> {x0, y0, x1, y1}` (axis-aligned, rotation applied; marker: ±1 m; text: an estimate of
    `0.6 * size * length` by `size`)
  - `hitTest(item, pt: Pt, tol: number) -> boolean` (rect/ellipse inside, in the item's rotated frame; polygon
    inside (even-odd) or within `tol` of an edge; line within `width/2 + tol` of a segment; marker within
    `1 + tol`; text inside its bounds)
  - `itemsInBox(items, box) -> string[]` (ids whose bounds lie wholly inside `box`)
  - `snapPoint(pt, step) -> Pt` (never returns `-0`: `assert.deepEqual` tells them apart),
    `snapAngle(deg, step) -> number`, `distance(a, b) -> number`
  - `moveItem(item, dx, dy)`, `rotateItem(item, deg)` (rect/ellipse: set `rot`; polygon/line: rotate points about
    their bounds' centre), `resizeItem(item, handle, pt, keepRatio = false)` (`handle` one of
    `n s e w ne nw se sw`; rect/ellipse only; works in the item's own frame, keeps the opposite edge or corner
    fixed, minimum size 0.5 m)
  - `insertPoint(item, afterIndex, pt)`, `removePoint(item, index)` (polygon keeps at least 3 points, line at
    least 2: otherwise the item comes back unchanged), `movePoint(item, index, pt)`
  - `nearestSegment(item, pt) -> {index, dist}` (for adding a point where you click)

- [ ] **Step 1: Write the failing tests**, including:

```js
test("hitTest honours rotation", () => {
  const r = { type: "rect", x: 10, y: 10, w: 20, h: 2, rot: 90 };
  assert.ok(M.hitTest(r, [10, 19], 0));      // inside the rotated bar
  assert.ok(!M.hitTest(r, [19, 10], 0));     // where the unrotated bar would be
});
test("resizeItem works in the item's own frame", () => {
  const r = { type: "rect", x: 0, y: 0, w: 10, h: 4, rot: 90 };
  const out = M.resizeItem(r, "e", [0, 7]);  // the east handle now points south
  assert.equal(out.w, 12); assert.equal(out.h, 4); assert.equal(out.rot, 90);
  assert.ok(Math.abs(out.x - 0) < 1e-9 && Math.abs(out.y - 1) < 1e-9);  // west edge stays at y = -5
});
test("resizeItem keeps a minimum size", () => { /* drag the e handle past the w edge → w = 0.5 */ });
test("bounds of a rotated rect", () => { /* 10x2 at rot 90 → x0..x1 width 2, y0..y1 height 10 */ });
test("line hit uses its width", () => { /* width 4: a point 1.9 m off hits, 2.5 m off misses with tol 0 */ });
test("polygon hit: inside, near an edge, outside", () => {});
test("snapPoint / snapAngle / distance", () => {
  assert.deepEqual(M.snapPoint([2.6, -0.4], 2), [2, 0]); assert.equal(M.snapAngle(22, 15), 15);
  assert.equal(M.distance([0, 0], [3, 4]), 5);
});
test("removePoint keeps polygons at 3 points and lines at 2", () => {});
test("rotateItem on a polygon rotates its points about the centre", () => {});
test("geometry functions don't mutate their input", () => {});
```

- [ ] **Step 2: Run, see them fail** — `node --test tools/level_sketch/`
- [ ] **Step 3: Implement.** Rotation convention: `rot` in degrees, clockwise on screen (y south), about `(x, y)`;
  to test a point, rotate it by `-rot` about the centre and compare with the unrotated box.
- [ ] **Step 4: Run, all pass.**
- [ ] **Step 5: Checkpoint.**

---

### Task 4: Model — history and SVG

**Files:** Modify `tools/level_sketch/model.js`, `tools/level_sketch/model.test.js`

**Interfaces:**
- Produces:
  - `class History { constructor(limit = 150); record(state: string): void; undo(current: string): string | null;
    redo(current: string): string | null; get canUndo(): boolean; get canRedo(): boolean; clear(): void }`
    (`record` takes the state *before* a change and clears the redo stack; the oldest entries drop past `limit`)
  - `escapeXml(s: string) -> string` (`& < > " '`)
  - `itemSvg(item, opts = {}) -> string` (one item's SVG markup; `opts.labels` (default true) adds its label;
    the canvas in Task 5 and the export share it)
  - `toSvg(sketch, opts = {}) -> string` (a standalone `<svg xmlns=…>` with `viewBox` in metres framing the
    sketch's size and every item, a dark backdrop, visible layers in order (hidden ones left out), labels, a
    scale bar (10 m), a legend listing each kind and marker kind used with its colour and name, and
    `<title>` = sketch name)

- [ ] **Step 1: Write the failing tests:**

```js
test("History: record, undo, redo, limit", () => {
  const h = new M.History(3);
  h.record("a"); h.record("b"); h.record("c"); h.record("d");          // "a" falls off
  assert.equal(h.undo("e"), "d"); assert.equal(h.undo("d"), "c"); assert.equal(h.undo("c"), "b");
  assert.equal(h.undo("b"), null); assert.equal(h.redo("b"), "c");
  h.record("x"); assert.equal(h.canRedo, false);
});
test("toSvg escapes labels and notes", () => {
  const s = M.newSketch("t");
  s.layers[0].items.push({ id: "s1", type: "rect", kind: "plaza", x: 5, y: 5, w: 4, h: 4, rot: 0,
    label: `Tom & "Jerry's" <inn>`, note: "café" });
  const svg = M.toSvg(s);
  assert.ok(svg.includes("Tom &amp; &quot;Jerry&apos;s&quot; &lt;inn&gt;"));
  assert.ok(!svg.includes("<inn>"));
  assert.ok(svg.startsWith("<svg") && svg.includes('xmlns="http://www.w3.org/2000/svg"'));
});
test("toSvg legend lists exactly the kinds used", () => { /* plaza + lava used → both names present, "Bog" absent */ });
test("toSvg leaves hidden layers out", () => {});
test("itemSvg draws each item type", () => { /* rect → <rect … transform="rotate(…)">, ellipse → <ellipse, polygon → <polygon, line → <polyline with stroke-width = width, marker → glyph, text → <text */ });
```

- [ ] **Step 2–4:** run (fail), implement, run (pass).
- [ ] **Step 5: Checkpoint.**

---

### Task 5: Page shell — canvas, pan/zoom, grid, rendering

**Files:**
- Create: `tools/level_sketch/index.html`, `tools/level_sketch/sketches/.gitkeep`

**Interfaces:**
- Consumes: `SketchModel` (`newSketch`, `itemSvg`, `KIND`, `MARKER`)
- Produces (page-global, used by Tasks 6–10):
  - `S` — the UI state: `{ sketch, activeLayer, selection: string[], tool, kind, markerKind, snap, view: {x, y, scale}, history, underlay, showGrid, showLabels }`
  - `render()` — redraws everything from `S` (layers group via `itemSvg`, selection overlay, status)
  - `screenToWorld(clientX, clientY) -> Pt`, `worldToScreen(pt) -> [px, py]`
  - `change(mutator: (sketch) => void)` — records history, applies the mutation, calls `render()` and
    `SketchStorage.autosave` (Task 10 fills it in; until then a no-op)
  - `findItem(id) -> {layer, item, index}`

- [ ] **Step 1: Build the page.** Head: title "Ashen Vault Level Sketch", the planner's font link, colour tokens and
  theme blocks; `<script src="model.js">`, `<script src="storage.js">` (create `storage.js` now as
  `globalThis.SketchStorage = { autosave() {} };`). Layout: header (name field, New, Open, Save, Export SVG, Undo,
  Redo, status), left panel (tools, kinds, markers: empty sections for now), centre `<svg id="canvas">`, right
  panel (properties, layers: empty for now), footer status (cursor in metres and tiles: `x 41.5 m · tile 20,
  y 12.0 m · tile 6`, zoom).
- [ ] **Step 2: View.** Pan with middle-drag or space+left-drag; wheel zooms about the cursor (clamp 2–200 px
  per metre); a Fit button and key `0` frame the sketch's size and every item. Apply the view as the `<svg>`'s
  `viewBox`, so the shapes stay in metres.
- [ ] **Step 3: Grid and scale bar.** A `<pattern>`-free grid: draw lines only for the visible area; 2 m lines
  hidden below 6 px per metre, 10 m lines always; toggle with `G`. The sketch's size as a slightly lighter
  rectangle. A scale bar bottom-left in screen space whose length is a round number of metres (1, 2, 5, 10, 20,
  50, 100) closest to 120 px.
- [ ] **Step 4: Verify in Chrome.** Temporarily seed `S.sketch` with one item of each type (remove it after).
  Run: `google-chrome-stable --headless=new --screenshot=/tmp/claude-1000/sketch-shell.png --window-size=1400,900 "file://$PWD/tools/level_sketch/index.html"`
  and read the screenshot. Expected: three panels, the dark canvas with a 10 m grid, the six seeded items, scale bar.
  Then check pan and zoom by hand in a real Chrome window (or with the claude-in-chrome tools): the grid
  stays aligned with the shapes while zooming about the cursor.
- [ ] **Step 5: Checkpoint.**

---

### Task 6: Drawing tools

**Files:** Modify `tools/level_sketch/index.html`

**Interfaces:**
- Consumes: `S`, `change`, `screenToWorld`, `SketchModel.newId / snapPoint / distance`
- Produces: `setTool(id)`; tools `rect R, ellipse E, polygon P, line L, marker M, text T, measure D`
  (Select `V` is Task 7). New items go on `S.activeLayer` with `kind = S.kind` (markers `S.markerKind`) and are
  selected after drawing; the tool stays active.

- [ ] **Step 1:** Left-panel tool grid (the planner's `.tools` style with key hints), `S` knows the active tool, the
  cursor changes per tool.
- [ ] **Step 2: Rect / ellipse:** press-drag-release draws from corner to corner (`rot` 0); shift makes it square;
  a drag under 0.25 m creates nothing. Live preview while dragging.
- [ ] **Step 3: Polygon / line:** each click adds a point with a rubber-band segment to the cursor; double-click or
  Enter finishes (polygon closes, needs 3 points, line needs 2); Escape cancels; Backspace removes the last
  point.
- [ ] **Step 4: Marker / text:** a click drops one; text opens an inline input at the point (Enter commits, Escape
  or empty cancels).
- [ ] **Step 5: Measure:** drag shows a line with `23.4 m · 11.7 tiles` beside it; nothing is kept.
- [ ] **Step 6: Snap:** `S` toggles snap (status shows `snap 1 m`); while on, every placed or dragged point goes
  through `snapPoint(pt, alt ? 2 : 1)`, and within 0.75 m of another item's vertex, to that vertex instead.
- [ ] **Step 7: Verify by hand in Chrome:** draw one of each; undo (Task 7 adds the keys; until then check that
  `S.history.canUndo` is true in the console); toggle snap and see points land on whole metres.
- [ ] **Step 8: Checkpoint.**

---

### Task 7: Selecting and editing

**Files:** Modify `tools/level_sketch/index.html`

**Interfaces:**
- Consumes: `hitTest`, `itemsInBox`, `moveItem`, `resizeItem`, `rotateItem`, `snapAngle`, `insertPoint`,
  `removePoint`, `movePoint`, `nearestSegment`, `History`
- Produces: `isTypingTarget(event) -> boolean` (true when focus is in an `input`, `textarea`, `select` or
  `[contenteditable]`); every keyboard shortcut in the page returns early when it is true. `select(ids)`,
  `deleteSelection()`.

- [ ] **Step 1: Select (V):** click picks the topmost hit on the active layer (other visible layers too unless
  dimmed; locked items are never picked by click on canvas but can be selected in the layer list, Task 8);
  shift-click toggles; dragging on empty space draws a selection box (`itemsInBox`); Escape clears.
- [ ] **Step 2: Move:** dragging a selected item moves the whole selection (snapped if snap is on); arrows nudge
  0.5 m, shift-arrows 2 m. One history record per drag, not per mouse move.
- [ ] **Step 3: Handles** for a single rect/ellipse: eight resize handles (shift keeps the ratio) and a rotate handle
  above it (shift: 15° steps). Polygon/line: a rotate handle only. Handles keep a constant size on screen.
- [ ] **Step 4: Point editing:** double-click a polygon or line to edit its points: drag a point, click a segment to add
  one (`nearestSegment`), Delete removes the selected point; Escape or a click elsewhere leaves.
- [ ] **Step 5: Keys:** Ctrl+Z / Ctrl+Shift+Z (and Ctrl+Y), Ctrl+D duplicate (offset 2 m), Delete / Backspace,
  Ctrl+C / Ctrl+V (in-page clipboard; paste offset 2 m, new ids), `[` / `]` order within the layer, Ctrl+A
  selects the active layer's items.
- [ ] **Step 6: Verify by hand in Chrome:** rotate a rect 30°, resize it from a corner (it grows along its own
  axes), move two items together, undo each step back to empty. **Review Focus 4:** type into the label field
  (Task 8) or the sketch name field: Delete, arrows and `R` edit the text and leave shapes and the tool alone.
- [ ] **Step 7: Checkpoint.**

---

### Task 8: Kinds, markers, properties and layers panels

**Files:** Modify `tools/level_sketch/index.html`

**Interfaces:**
- Consumes: `KINDS`, `MARKER_KINDS`, `change`, `select`
- Produces: `S.kind`, `S.markerKind` set from the palettes; `renderPanels()` called by `render()`.

- [ ] **Step 1: Kinds palette** (left), grouped as in `KINDS`, each a swatch + name. Clicking one sets `S.kind`;
  with a selection it also changes the selected items' kind (one history record). Markers palette likewise
  for `S.markerKind`.
- [ ] **Step 2: Properties** (right) for the selection: kind (select), label, note (textarea), colour override (colour
  input + a "reset" link), opacity (0–1 slider), line width (lines), `height_m` (number, empty = none),
  layer (select: moves the items), locked (checkbox), and position/size/rotation in metres as number inputs
  (rect/ellipse: x, y, w, h, rot; marker/text: x, y). With several selected, show only the fields they share
  and apply edits to all. Text edits record history once per focus, not per keystroke.
- [ ] **Step 3: Sketch fields** when nothing is selected: name (slugged on save), target map
  (`harrowmere, verdant_hollow, cinderhold, cinder_keep, sunken_keep, ashen_cemetery`, or blank), size in metres,
  sketch notes.
- [ ] **Step 4: Layers panel:** list with the active one highlighted; add, rename (double-click), drag or ↑/↓ to
  reorder, delete (asks first, in-page confirm, never `window.confirm`), and a three-way toggle per layer:
  visible / dimmed (25%, not clickable on the canvas) / hidden. Under each layer a collapsible list of its items
  (label or kind name) that selects on click, so locked items can still be selected.
- [ ] **Step 5: Labels** toggle (key `Shift+L`) hides canvas labels.
- [ ] **Step 6: Verify by hand in Chrome:** make an "Undercroft" layer, draw on it, dim it, check its shapes can't
  be clicked; change a shape's kind and see its colour follow; set a colour override and reset it.
- [ ] **Step 7: Checkpoint.**

---

### Task 9: Underlay

**Files:** Modify `tools/level_sketch/model.js`, `tools/level_sketch/model.test.js`, `tools/level_sketch/index.html`

**Interfaces:**
- Consumes: underlay JSON from Task 1
- Produces: `SketchModel.UNDERLAY_COLORS: Record<kindName, color>` (wall → `town_wall`'s colour, floor →
  `street`'s, indoor → `house_interior`'s, sea, water → `canal`'s, lava, chasm, mud → `bog`'s, thorns → a dark
  red), `SketchModel.underlayPaths(underlay) -> {kind, d}[]` — one path per kind present, each an SVG path
  of merged rectangles in metres (runs of equal codes along a row become one rectangle).

- [ ] **Step 1: Failing tests:**

```js
test("underlayPaths merges runs and scales to metres", () => {
  const u = { format: "ashen-vault-underlay", version: 1, w: 4, h: 2, tile_m: 2,
    codes: { "#": "wall", ".": "floor" }, rows: ["##..", ".##."], marks: [] };
  const paths = Object.fromEntries(M.underlayPaths(u).map(p => [p.kind, p.d]));
  assert.deepEqual(Object.keys(paths).sort(), ["floor", "wall"]);
  assert.equal(paths.wall, "M0 0h4v2h-4zM2 2h4v2h-4z");
  assert.equal(paths.floor, "M4 0h4v2h-4zM0 2h2v2h-2zM6 2h2v2h-2z");
});
test("underlayPaths rejects what isn't an underlay", () => { /* throws /Not an underlay/ */ });
```

- [ ] **Step 2–4:** run (fail), implement, run (pass).
- [ ] **Step 5: Page:** an Underlay button (left panel) takes a file or pasted JSON; drawn behind every layer at
  `S.underlay.opacity` (slider, default 0.3) with its marks as small faint glyphs and labels; toggle with `U`;
  never selectable, never exported in the `.sketch.json` (only `"underlay": "<map>"` is) and left out of the SVG
  export unless "include underlay" is ticked in the export dialog. A sketch whose `size_m` is still the default
  takes the underlay's `w * 2, h * 2` when one is loaded.
- [ ] **Step 6: Verify:** `uv run python tools/level_sketch/map_to_underlay.py src/ashen_vault/maps/harrowmere.map > /tmp/claude-1000/harrowmere.underlay.json`,
  load it, screenshot (headless or by hand): Harrowmere's outline, sea south, markers for Odrin and the shrines.
  Pan and zoom stay smooth (Review Focus 5).
- [ ] **Step 7: Checkpoint.**

---

### Task 10: Saving, opening and exporting

**Files:** Modify `tools/level_sketch/storage.js`, `tools/level_sketch/index.html`

**Interfaces:**
- Produces `SketchStorage`:
  - `autosave(sketch)` / `restore() -> Sketch | null` — localStorage key `ashen-sketch:autosave`, debounced 500 ms,
    every access in try/catch.
  - `canUseFolder() -> boolean` (`"showDirectoryPicker" in window`)
  - `pickFolder() -> Promise<void>` — asks for the sketches folder; remembers the handle in IndexedDB
    (`ashen-sketch` db, store `handles`) so a reload asks only for permission again
    (`handle.requestPermission({mode: "readwrite"})`).
  - `save(sketch) -> Promise<"folder" | "download">` — writes `<slug>.sketch.json` (`serialize`) and `<slug>.svg`
    (`toSvg`) to the folder; without a folder or permission, downloads both instead.
  - `list() -> Promise<string[]>` — `*.sketch.json` names in the folder (empty without one).
  - `open(name?) -> Promise<Sketch>` — from the folder by name, else a file picker (`<input type=file>`); runs
    `normalize`.
- Page: New (asks first if there are unsaved changes), Open (a list from the folder plus "Open file…"), Save
  (Ctrl+S), Export SVG (download only, with the "include underlay" tick). The status bar says where the last
  save went (`Saved to sketches/harrowmere-v2.sketch.json` or `Downloaded harrowmere-v2.sketch.json`) and shows a
  dot while there are unsaved changes. On load the page restores the autosave.

- [ ] **Step 1: Implement `storage.js`** with the interfaces above.
- [ ] **Step 2: Wire the page** (buttons, Ctrl+S, unsaved dot, `beforeunload` warning when unsaved).
- [ ] **Step 3: Verify by hand in Chrome from `file://`:** Save → pick `tools/level_sketch/sketches/` → both files
  appear (`ls tools/level_sketch/sketches/`); reload → the sketch is back (autosave) and Save asks only for
  permission; Open lists the sketch and reloads it identical; `python -m json.tool` reads the `.sketch.json`; the
  `.svg` opens in the browser on its own. If `showDirectoryPicker` is refused on `file://`, check the download
  fallback works and note it in the hand-off.
- [ ] **Step 4: Error paths:** opening a non-sketch file shows `Not an Ashen Vault sketch` in the status bar and
  keeps the current sketch; a denied folder permission falls back to download with a status message.
- [ ] **Step 5: Checkpoint.**

---

### Task 11: Docs and final checks

**Files:** Modify `AGENTS.md` (Layout table, after the `tools/level_planner/` row)

- [ ] **Step 1: Add the row:**
  `| tools/level_sketch/ | A free-form top-down sketchpad for level design (index.html, open it in Chrome; a design aid, not part of the game): shapes, lines and markers in metres on layers, over an optional underlay of a game map (map_to_underlay.py <map>), saved as <name>.sketch.json + .svg in sketches/. Tests: node --test tools/level_sketch/ |`
  (with the backticks AGENTS.md uses for paths).
- [ ] **Step 2: Run every check:**
  `uv run ruff check && uv run ruff format --check && uv run pytest --cov && node --test tools/level_sketch/`
  Expected: all green; coverage still at or above `fail_under` (the new script is outside `ashen_vault`, so it
  doesn't count either way).
- [ ] **Step 3: End-to-end by hand:** load Harrowmere's underlay, sketch a reorganised market (a rotated plaza, a
  canal line, three houses, Odrin's marker, a "Market district" zone), save, reopen, export SVG; read the
  `.sketch.json` and check every shape has its kind, label and metric geometry.
- [ ] **Step 4: Checkpoint** — the whole `tools/level_sketch/` folder, `tests/test_map_to_underlay.py`, `AGENTS.md`,
  `.gitignore`, the spec and this plan.
