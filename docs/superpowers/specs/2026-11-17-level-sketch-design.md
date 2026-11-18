# Level Sketch: design

A free-form, top-down sketchpad for designing Ashen Vault's levels in shapes and lines, off the tile grid.

## Intent

Victor wants to reorganize Harrowmere and draw new layouts for the Verdant Hollow and the Cinderhold.
The existing planner (`tools/level_planner/index.html`) paints on the 2 m tile grid, which is too
concrete for that stage of design: the aim is to think in rough shapes ("the market is about here, this
big, the canal runs down this way"), at any angle, still to scale.

A sketch is a picture, not a map. Once one is done, Victor and an agent read it together and write a
plan/review for building it into the real game (`.map` files, props, models) by hand. So the tool's job
ends at saving each sketch in a form an agent can read precisely: shapes in metres, their kinds, labels
and notes, plus an image.

Picked from three visual styles (painted regions, bubbles and links, shapes and lines): **shapes and
lines**.

## Goals

- Draw rectangles, polygons and ellipses freely: any size, any angle; move, rotate, resize, recolour,
  label and annotate them.
- Draw lines and polylines with a width: walls, roads, rivers, canals, bridges.
- Place icon markers for what a level holds: NPC, shop, gate/exit, well/descent, cave mouth, shrine,
  boss, enemy, chest/item, landmark, door, lift, player start, note (the planner's kinds plus `lift`).
- Keep everything to scale in metres: a ruler readout, an optional faint grid (2 m tile, 10 m major),
  a scale bar, and a measure tool for distances.
- Underlay a current game map, faint, behind the sketch, so Harrowmere can be redrawn over what exists.
- Save sketches as files in the repo: `<name>.sketch.json` (exact data) and `<name>.svg` (image).
- Several layers per sketch (e.g. the keep's Undercroft / ground / Gallery, the jungle's Root Caverns
  under the bog), each shown, hidden or dimmed.

## Non-goals

- Turning a sketch into tiles or a `.map` file. That is the later plan/review step, done by hand.
- Grid painting (the planner already does it; it stays as is).
- Importing levels drawn in the old planner: Victor doesn't need them ("we can delete them"). The
  underlay comes from the game's own `.map` files instead.
- Shipping with the game, multi-user editing, mobile/touch support.
- 3D, heights as geometry. A shape may carry a height in its notes or a `height_m` field, nothing more.

## Anti-goals

- Feeling like grid painting again: snapping is off by default, nothing forces tile alignment.
- A fiddly UI that slows sketching: drawing a shape is one drag, editing its kind or label is one click.
- Sketches only an eye can read: every shape must survive the export with its kind, label, note and
  metric geometry intact.

## Constraints

- A standalone page in `tools/level_sketch/`, like the planner: plain HTML + JS + SVG in one file,
  no build step, no dependencies, opens from disk (`file://`) in Chrome. Not part of the game package.
- AGENTS.md's rule that the game ships no image files is untouched: the tool and its sketches live
  under `tools/`, not in the game.
- Python helpers follow the repo's ruff settings (line length 110, double quotes) and get a pytest
  test.
- The player's real save and game files are never touched.

## Approaches

1. **Grow the existing planner** with a vector layer beside the tile grid. Reuses its level list,
   saving, undo, markers and map import, but makes one 867-line page juggle two ways of drawing, and
   the grid is what felt too concrete.
2. **A new page, `tools/level_sketch/`, built only for shapes** (picked). It borrows the planner's marker
   kinds, palette and look, but drops the grid painting. Costs some copied code and needs its own map
   underlay.
3. **Excalidraw or tldraw** with an icon library and a "1 square = 10 m" convention. Nothing to build,
   but metres are only a convention, it knows nothing about the game, and it isn't the tool asked for.

Victor chose 2 ("go" on the recommendation).

## Design

### Canvas and view

- One SVG canvas whose user units are metres (1 unit = 1 m). Pan with middle-drag or space+drag,
  zoom with the wheel around the cursor, a Fit button.
- A sketch has a size in metres (default 120 x 120; Harrowmere's grid is about 64 x 52 tiles, so
  128 x 104 m) and a dark backdrop. Shapes may sit outside it; Fit frames everything.
- The faint grid: thin lines every 2 m, stronger every 10 m, toggleable, fading out when zoomed far.
- A scale bar in a corner and the cursor's position in metres in the status bar.

### Tools

| Tool | Key | Does |
| --- | --- | --- |
| Select | V | click / shift-click / box-select; drag to move; handles to resize and rotate (shift: 15 degree steps) |
| Rectangle | R | drag a box |
| Ellipse | E | drag a box |
| Polygon | P | click points, double-click or Enter to close |
| Line | L | click points, double-click or Enter to finish; has a width |
| Marker | M | click to drop the current marker kind |
| Text | T | click to place a free label |
| Measure | D | drag: shows the distance in metres (and in 2 m tiles), leaves nothing behind |

- Snap (toggle, key S, off by default): to 1 m, or 2 m with Alt. Points also snap to other shapes'
  points when close.
- Edit points of a polygon or line by double-clicking it; drag a point, click a segment to add one,
  Delete removes the selected point.
- Ctrl+Z / Ctrl+Shift+Z undo and redo (at least 150 steps), Ctrl+D duplicate, Delete, Ctrl+C / Ctrl+V,
  `[` / `]` send backward / bring forward, arrow keys nudge 0.5 m (shift: 2 m).

### Kinds and palette

Every shape and line has a **kind**, which sets its default colour and tells the later plan what it
means. One palette, grouped, covering the three maps (colours borrowed from the planner where it has
them):

- Ground: street/cobble, plaza/setts, terrace, steps, garden/grass, jungle floor, bog/mud, cave floor,
  fortress floor, ash/slag
- Indoors: house interior, hall/nave, dungeon room
- Walls: town wall, cliff/rock, stone house, timber house, cathedral/great wall, low wall, hedge/vines,
  fortress wall
- Water and void: sea (deep), canal/river (shallow), lava, chasm
- Structures: pier/boards, bridge, ledge/plank, lift shaft
- Zone: a translucent outline-only area for "this is the market district" style grouping
- Other: free colour

A shape's colour can be overridden; its kind stays. Kinds are a list in the page's code so new ones are
one line.

### Properties panel

For the selection: kind, label (shown on the canvas, toggleable), note (multi-line, not drawn),
colour override, opacity, line width (lines), `height_m` (optional number: a floor height or a wall's
height, for the plan), layer, locked (can't be moved by accident). Size, position and rotation are
shown in metres and editable as numbers.

### Layers

- A sketch has named layers (default one, "Ground"). Add, rename, reorder, delete (with its shapes,
  asking first).
- Each layer: visible / hidden / dimmed (drawn at 25% and not selectable while another is active).
- Drawing goes onto the active layer.

### Underlay

- `tools/level_sketch/map_to_underlay.py <map>` reads a game `.map` and prints JSON: the grid size,
  each tile's broad kind (using the sketch's kinds: wall, water, lava, chasm, floor...) and the
  positions of exits, shrines, NPCs and bosses. It reuses `tools/level_planner/map_to_planner.py`'s
  parsing (import it, extend its mapping for the jungle's and Cinderhold's legends rather than copy it).
- The page's Underlay button loads that JSON (file picker or paste) and draws it behind every layer as
  coloured 2 m cells at adjustable opacity (default 30%), locked, never exported as shapes. The sketch
  remembers which map it used.

### Saving and files

- Autosave the open sketch to `localStorage` on every change (try/catch; the page works without it),
  so a closed tab loses nothing.
- **Save to the repo:** the Save button uses the File System Access API (Chrome): the first time you
  pick the folder `tools/level_sketch/sketches/`; after that Save writes `<name>.sketch.json` and
  `<name>.svg` straight into it. Open lists that folder's sketches. Where the API is missing (or
  `file://` refuses it), Save downloads the two files and Open takes a file picker.
- Sketch names are slugs (`harrowmere-v2`, `cinderhold-redo`).

### The sketch file (`*.sketch.json`, version 1)

```json
{
  "format": "ashen-vault-sketch",
  "version": 1,
  "name": "harrowmere-v2",
  "target_map": "harrowmere",
  "size_m": [128, 104],
  "underlay": "harrowmere",
  "notes": "free text about the whole level",
  "layers": [
    {
      "id": "l1", "name": "Ground", "visible": true,
      "items": [
        {"id": "s1", "type": "rect", "kind": "plaza", "label": "Market", "note": "fountain in the middle",
         "x": 40, "y": 60, "w": 24, "h": 18, "rot": -8, "height_m": 0},
        {"id": "s2", "type": "polygon", "kind": "hall", "label": "Cathedral", "points": [[50,8],[80,8],[82,24],[48,26]]},
        {"id": "s3", "type": "line", "kind": "canal", "label": "Canal", "width": 4, "points": [[60,104],[58,80],[64,60]]},
        {"id": "m1", "type": "marker", "kind": "npc", "label": "Odrin", "note": "by the Silent Bell", "x": 70, "y": 50},
        {"id": "t1", "type": "text", "text": "upper town", "x": 60, "y": 30, "size": 3}
      ]
    }
  ]
}
```

- Coordinates in metres, x east, y south (as on screen), origin at the sketch's top-left. `x, y` of a
  rect or ellipse is its centre; `rot` in degrees about the centre. One tile = 2 m, so tile = floor(m / 2).
- Unknown fields are kept on load, so a later version can add things without losing data.
- The SVG export draws the same thing with labels and a legend of the kinds used, readable on its own.

### Look

Matches the planner: dark UI, the same fonts and colour tokens, panels left (tools, kinds, markers) and
right (properties, layers), status bar at the bottom. Works at laptop width; phone width is not a
goal.

## Left to the builder

- Internal code structure, event handling, how undo snapshots are taken.
- Exact colours for kinds the planner doesn't have (lava, chasm, bog, fortress), in keeping with it.
- Marker icon glyphs (the planner's letters are fine).
- How the extended legend mapping in `map_to_planner.py` classifies each jungle and Cinderhold tile,
  as long as lava, chasm, water and walls come out right.

## Calls made by Claude (not discussed)

- Default size 120 x 120 m; snap off by default; 0.5 m nudge.
- Layers, `height_m`, locked shapes, the Zone kind and the measure tool were added for multi-level
  maps and for judging distances; none was asked for.
- Sketches live in `tools/level_sketch/sketches/` (not `docs/`, which holds only the logo and README
  images), committed with the tool.
- Saving through the File System Access API with a download fallback.
- `.superpowers/` (the brainstorming mockups) goes into `.gitignore`.
