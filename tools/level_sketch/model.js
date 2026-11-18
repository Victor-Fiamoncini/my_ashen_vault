// Ashen Vault Level Sketch: the pure model. No DOM here, so Node can test it (node --test tools/level_sketch/).
// Loaded by index.html as a classic script (ES modules are blocked on file://); exposes `SketchModel`.
// Units are metres: x east, y south, origin at the sketch's top-left. One game tile is 2 m.
"use strict";
(function () {
  const FORMAT = "ashen-vault-sketch";
  const VERSION = 1;
  const DEFAULT_SIZE = [120, 120];

  // ---------- Kinds ----------
  // [id, name, group, colour]. A shape's kind says what it stands for in the game; it also sets its colour.
  const KINDS = [
    ["street", "Street / cobble", "Ground", "#a39d90"],
    ["plaza", "Plaza / setts", "Ground", "#c8b791"],
    ["terrace", "Raised terrace", "Ground", "#bcb4a3"],
    ["steps", "Steps", "Ground", "#ddd4c0"],
    ["garden", "Grass / garden", "Ground", "#6f8b49"],
    ["jungle_floor", "Jungle floor", "Ground", "#4e6b34"],
    ["bog", "Bog / mud", "Ground", "#5c5236"],
    ["cave_floor", "Cave floor", "Ground", "#3a342d"],
    ["fortress_floor", "Fortress floor", "Ground", "#6a625c"],
    ["ash", "Ash / slag", "Ground", "#55504c"],
    ["house_interior", "House interior", "Indoors", "#caa77b"],
    ["hall", "Hall / nave", "Indoors", "#8f84a8"],
    ["dungeon_room", "Dungeon room", "Indoors", "#7b7366"],
    ["town_wall", "Town wall", "Walls", "#3c3944"],
    ["cliff", "Cliff / rock", "Walls", "#5a554c"],
    ["stone_house", "Stone house", "Walls", "#7c7192"],
    ["timber_house", "Timber house", "Walls", "#7f5b3c"],
    ["great_wall", "Cathedral / great wall", "Walls", "#4c3f66"],
    ["low_wall", "Low wall / plinth", "Walls", "#6d6a63"],
    ["hedge", "Hedge / vines", "Walls", "#2f4a22"],
    ["fortress_wall", "Fortress wall", "Walls", "#2b2626"],
    ["sea", "Sea (deep)", "Water and void", "#22466b"],
    ["canal", "Canal / river", "Water and void", "#3f7aa3"],
    ["lava", "Lava", "Water and void", "#e0561b"],
    ["chasm", "Chasm", "Water and void", "#0b0a0e"],
    ["pier", "Pier / boards", "Structures", "#9c6b3e"],
    ["bridge", "Bridge", "Structures", "#8a7660"],
    ["ledge", "Ledge / plank", "Structures", "#a88c5f"],
    ["lift_shaft", "Lift shaft", "Structures", "#4f6f7a"],
    ["zone", "Zone (area)", "Zone", "#b9a6e8"],
    ["other", "Other", "Other", "#9a95ad"],
  ].map(([id, name, group, color]) => ({ id, name, group, color }));
  const KIND = Object.fromEntries(KINDS.map(k => [k.id, k]));

  // [id, name, colour, glyph]: the planner's marker kinds, plus lifts.
  const MARKER_KINDS = [
    ["npc", "NPC", "#3f8fd6", "N"],
    ["shop", "Shop", "#d6a33f", "$"],
    ["gate", "Gate / exit", "#c25b3a", "G"],
    ["well", "Well / descent", "#2f9f8f", "W"],
    ["cave", "Cave mouth", "#6f8b49", "C"],
    ["shrine", "Shrine", "#e0c070", "S"],
    ["boss", "Boss", "#b8323d", "B"],
    ["enemy", "Enemy", "#8a3b56", "E"],
    ["chest", "Chest / item", "#b07a2f", "I"],
    ["landmark", "Landmark", "#8e6fd0", "L"],
    ["door", "Door", "#8c8478", "D"],
    ["lift", "Lift", "#4f9fb5", "⇕"],
    ["start", "Player start", "#ffffff", "P"],
    ["note", "Note", "#5f6b7a", "?"],
  ].map(([id, name, color, glyph]) => ({ id, name, color, glyph }));
  const MARKER = Object.fromEntries(MARKER_KINDS.map(k => [k.id, k]));

  const TYPES = new Set(["rect", "ellipse", "polygon", "line", "marker", "text"]);

  // ---------- Schema ----------
  let counter = 0;
  function newId(prefix) {
    counter += 1;
    return `${prefix}${Date.now().toString(36)}${counter.toString(36)}${Math.random().toString(36).slice(2, 5)}`;
  }

  function slug(name) {
    const s = String(name ?? "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40)
      .replace(/-+$/, "");
    return s || "sketch";
  }

  function newLayer(name) {
    return { id: newId("l"), name, visible: true, dimmed: false, items: [] };
  }

  function newSketch(name) {
    const layer = newLayer("Ground");
    layer.id = "l1";
    return {
      format: FORMAT, version: VERSION, name: slug(name), target_map: "", size_m: [...DEFAULT_SIZE],
      underlay: "", notes: "", layers: [layer],
    };
  }

  const num = v => typeof v === "number" && Number.isFinite(v);
  const numOr = (v, dflt) => (num(v) ? v : dflt);
  const str = (v, dflt = "") => (typeof v === "string" ? v : dflt);

  function cleanPoints(points) {
    if (!Array.isArray(points)) return [];
    return points.filter(p => Array.isArray(p) && num(p[0]) && num(p[1])).map(p => [p[0], p[1]]);
  }

  // One item made sound, or null when it can't be. Unknown fields are kept.
  function cleanItem(raw, ids) {
    if (!raw || typeof raw !== "object" || !TYPES.has(raw.type)) return null;
    const it = { ...raw };
    if (typeof it.id !== "string" || !it.id || ids.has(it.id)) it.id = newId(it.type === "marker" ? "m" : it.type === "text" ? "t" : "s");
    ids.add(it.id);
    const known = it.type === "marker" ? MARKER : KIND;
    const fallback = it.type === "marker" ? "note" : "other";
    if (it.type !== "text") {
      if (it.kind !== undefined && !known[it.kind]) it.kind_was = String(it.kind);
      if (!known[it.kind]) it.kind = fallback;
    }
    for (const f of ["label", "note"]) if (f in it) it[f] = str(it[f]);
    if (it.type === "rect" || it.type === "ellipse") {
      if (![it.x, it.y, it.w, it.h].every(num)) return null;
      it.w = Math.abs(it.w);
      it.h = Math.abs(it.h);
      it.rot = numOr(it.rot, 0);
    } else if (it.type === "polygon" || it.type === "line") {
      it.points = cleanPoints(it.points);
      if (it.points.length < (it.type === "polygon" ? 3 : 2)) return null;
      if (it.type === "line") it.width = numOr(it.width, 2) > 0 ? numOr(it.width, 2) : 2;
    } else {
      if (!num(it.x) || !num(it.y)) return null;
      if (it.type === "text") {
        it.text = str(it.text);
        it.size = numOr(it.size, 3) > 0 ? numOr(it.size, 3) : 3;
      }
    }
    if ("opacity" in it) it.opacity = Math.min(1, Math.max(0, numOr(it.opacity, 1)));
    if ("height_m" in it && !num(it.height_m)) delete it.height_m;
    if ("locked" in it) it.locked = !!it.locked;
    return it;
  }

  function normalize(data) {
    // A sketch says so, or (an early one without `format`) at least carries layers.
    const looksLike = data && typeof data === "object" && !Array.isArray(data) &&
      (data.format === FORMAT || (!("format" in data) && Array.isArray(data.layers)));
    if (!looksLike) {
      throw new Error("Not an Ashen Vault sketch");
    }
    const s = { ...data, format: FORMAT, version: VERSION };
    s.name = slug(s.name ?? "sketch");
    s.target_map = str(s.target_map);
    s.underlay = str(s.underlay);
    s.notes = str(s.notes);
    const size = Array.isArray(s.size_m) ? s.size_m : [];
    s.size_m = [0, 1].map(i => (num(size[i]) && size[i] > 0 ? size[i] : DEFAULT_SIZE[i]));
    const ids = new Set();
    const layerIds = new Set();
    const layers = Array.isArray(s.layers) ? s.layers : [];
    s.layers = layers.filter(l => l && typeof l === "object").map((raw, i) => {
      const l = { ...raw };
      if (typeof l.id !== "string" || !l.id || layerIds.has(l.id)) l.id = newId("l");
      layerIds.add(l.id);
      l.name = str(l.name, `Layer ${i + 1}`) || `Layer ${i + 1}`;
      l.visible = l.visible !== false;
      l.dimmed = !!l.dimmed;
      l.items = (Array.isArray(l.items) ? l.items : []).map(it => cleanItem(it, ids)).filter(Boolean);
      return l;
    });
    if (!s.layers.length) s.layers = [{ ...newLayer("Ground"), id: "l1" }];
    return s;
  }

  function serialize(sketch) {
    return JSON.stringify(sketch, null, 2) + "\n";
  }

  // ---------- Geometry ----------
  // `rot` is in degrees, clockwise on screen (y runs south), about an item's centre: the same as SVG's rotate().
  const MIN_SIZE = 0.5;
  const MARKER_R = 1.5;
  const rad = deg => (deg * Math.PI) / 180;
  const zero = v => (v === 0 ? 0 : v); // never -0

  function turn([x, y], deg) {
    const c = Math.cos(rad(deg));
    const s = Math.sin(rad(deg));
    return [x * c - y * s, x * s + y * c];
  }
  const toLocal = (it, [px, py]) => turn([px - it.x, py - it.y], -(it.rot || 0));
  const toWorld = (it, p) => {
    const [x, y] = turn(p, it.rot || 0);
    return [it.x + x, it.y + y];
  };

  function textBox(it) {
    const w = 0.6 * it.size * Math.max(1, String(it.text ?? "").length);
    return { x0: it.x - w / 2, y0: it.y - it.size / 2, x1: it.x + w / 2, y1: it.y + it.size / 2 };
  }

  function pointsBounds(points) {
    const xs = points.map(p => p[0]);
    const ys = points.map(p => p[1]);
    return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
  }

  function corners(it) {
    const w = it.w / 2;
    const h = it.h / 2;
    return [[-w, -h], [w, -h], [w, h], [-w, h]].map(p => toWorld(it, p));
  }

  function bounds(it) {
    switch (it.type) {
      case "rect":
        return pointsBounds(corners(it));
      case "ellipse": {
        const a = rad(it.rot || 0);
        const rx = it.w / 2;
        const ry = it.h / 2;
        const hx = Math.hypot(rx * Math.cos(a), ry * Math.sin(a));
        const hy = Math.hypot(rx * Math.sin(a), ry * Math.cos(a));
        return { x0: it.x - hx, y0: it.y - hy, x1: it.x + hx, y1: it.y + hy };
      }
      case "polygon":
        return pointsBounds(it.points);
      case "line": {
        const b = pointsBounds(it.points);
        const r = (it.width || 0) / 2;
        return { x0: b.x0 - r, y0: b.y0 - r, x1: b.x1 + r, y1: b.y1 + r };
      }
      case "marker":
        return { x0: it.x - MARKER_R, y0: it.y - MARKER_R, x1: it.x + MARKER_R, y1: it.y + MARKER_R };
      default:
        return textBox(it);
    }
  }

  function segDist([px, py], [ax, ay], [bx, by]) {
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy;
    const t = len2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2)) : 0;
    return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
  }

  function segments(it) {
    const pts = it.points;
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) out.push([pts[i], pts[i + 1]]);
    if (it.type === "polygon") out.push([pts[pts.length - 1], pts[0]]);
    return out;
  }

  function inside(points, [px, py]) {
    let hit = false;
    for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
      const [xi, yi] = points[i];
      const [xj, yj] = points[j];
      if (yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) hit = !hit;
    }
    return hit;
  }

  // A zone is a see-through outline: only its edge takes clicks, so the shapes it surrounds stay clickable.
  function zoneEdgeHit(it, pt, tol) {
    if (it.type === "polygon") return segments(it).some(([a, b]) => segDist(pt, a, b) <= tol);
    const [x, y] = toLocal(it, pt);
    const rx = it.w / 2;
    const ry = it.h / 2;
    if (it.type === "rect") {
      const dx = Math.abs(x) - rx;
      const dy = Math.abs(y) - ry;
      return dx <= tol && dy <= tol && (dx >= -tol || dy >= -tol);
    }
    const r = Math.hypot(x / rx, y / ry);
    return Math.abs(r - 1) * Math.min(rx, ry) <= tol;
  }

  function hitTest(it, pt, tol = 0) {
    if (it.kind === "zone" && (it.type === "rect" || it.type === "ellipse" || it.type === "polygon")) {
      return zoneEdgeHit(it, pt, tol);
    }
    switch (it.type) {
      case "rect": {
        const [x, y] = toLocal(it, pt);
        return Math.abs(x) <= it.w / 2 + tol && Math.abs(y) <= it.h / 2 + tol;
      }
      case "ellipse": {
        const [x, y] = toLocal(it, pt);
        const rx = it.w / 2 + tol;
        const ry = it.h / 2 + tol;
        return (x * x) / (rx * rx) + (y * y) / (ry * ry) <= 1;
      }
      case "polygon":
        return inside(it.points, pt) || segments(it).some(([a, b]) => segDist(pt, a, b) <= tol);
      case "line":
        return segments(it).some(([a, b]) => segDist(pt, a, b) <= (it.width || 0) / 2 + tol);
      case "marker":
        return Math.hypot(pt[0] - it.x, pt[1] - it.y) <= MARKER_R + tol;
      default: {
        const b = textBox(it);
        return pt[0] >= b.x0 - tol && pt[0] <= b.x1 + tol && pt[1] >= b.y0 - tol && pt[1] <= b.y1 + tol;
      }
    }
  }

  function itemsInBox(items, box) {
    return items.filter(it => {
      const b = bounds(it);
      return b.x0 >= box.x0 && b.y0 >= box.y0 && b.x1 <= box.x1 && b.y1 <= box.y1;
    }).map(it => it.id);
  }

  const snapPoint = ([x, y], step) => [zero(Math.round(x / step) * step), zero(Math.round(y / step) * step)];
  const snapAngle = (deg, step) => zero(Math.round(deg / step) * step);
  const distance = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);
  const hasPoints = it => it.type === "polygon" || it.type === "line";

  function moveItem(it, dx, dy) {
    if (hasPoints(it)) return { ...it, points: it.points.map(([x, y]) => [x + dx, y + dy]) };
    return { ...it, x: it.x + dx, y: it.y + dy };
  }

  function center(it) {
    if (!hasPoints(it)) return [it.x, it.y];
    const b = pointsBounds(it.points);
    return [(b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2];
  }

  function rotateItem(it, deg) {
    if (hasPoints(it)) {
      const [cx, cy] = center(it);
      return { ...it, points: it.points.map(([x, y]) => {
        const [rx, ry] = turn([x - cx, y - cy], deg);
        return [cx + rx, cy + ry];
      }) };
    }
    if (it.type === "rect" || it.type === "ellipse") return { ...it, rot: ((it.rot || 0) + deg) % 360 };
    return { ...it };
  }

  // Drag one of a rect's or ellipse's eight handles (n s e w ne nw se sw) to `pt`: the opposite edge or corner
  // stays where it is, in the item's own (rotated) frame.
  function resizeItem(it, handle, pt, keepRatio = false) {
    if (it.type !== "rect" && it.type !== "ellipse") return { ...it };
    const [px, py] = toLocal(it, pt);
    let left = -it.w / 2;
    let right = it.w / 2;
    let top = -it.h / 2;
    let bottom = it.h / 2;
    const e = handle.includes("e");
    const w = handle.includes("w");
    const s = handle.includes("s");
    const n = handle.includes("n");
    if (e) right = Math.max(px, left + MIN_SIZE);
    if (w) left = Math.min(px, right - MIN_SIZE);
    if (s) bottom = Math.max(py, top + MIN_SIZE);
    if (n) top = Math.min(py, bottom - MIN_SIZE);
    if (keepRatio && (e || w) && (n || s) && it.w > 0 && it.h > 0) {
      const scale = Math.max((right - left) / it.w, (bottom - top) / it.h);
      if (e) right = left + it.w * scale;
      else left = right - it.w * scale;
      if (s) bottom = top + it.h * scale;
      else top = bottom - it.h * scale;
    }
    const [x, y] = toWorld(it, [(left + right) / 2, (top + bottom) / 2]);
    return { ...it, x, y, w: right - left, h: bottom - top };
  }

  function minPoints(it) {
    return it.type === "polygon" ? 3 : 2;
  }

  function insertPoint(it, afterIndex, pt) {
    const points = it.points.map(p => [...p]);
    points.splice(afterIndex + 1, 0, [pt[0], pt[1]]);
    return { ...it, points };
  }

  function removePoint(it, index) {
    if (it.points.length <= minPoints(it)) return it;
    return { ...it, points: it.points.filter((_, i) => i !== index).map(p => [...p]) };
  }

  function movePoint(it, index, pt) {
    return { ...it, points: it.points.map((p, i) => (i === index ? [pt[0], pt[1]] : [...p])) };
  }

  function nearestSegment(it, pt) {
    let best = { index: -1, dist: Infinity };
    segments(it).forEach(([a, b], index) => {
      const dist = segDist(pt, a, b);
      if (dist < best.dist) best = { index, dist };
    });
    return best;
  }

  // ---------- History ----------
  // Snapshots as strings. `record` takes the state before a change; undo/redo trade the current state for one.
  class History {
    constructor(limit = 150) {
      this.limit = limit;
      this.past = [];
      this.future = [];
    }
    record(state) {
      this.past.push(state);
      if (this.past.length > this.limit) this.past.shift();
      this.future = [];
    }
    undo(current) {
      if (!this.past.length) return null;
      this.future.push(current);
      return this.past.pop();
    }
    redo(current) {
      if (!this.future.length) return null;
      this.past.push(current);
      return this.future.pop();
    }
    get canUndo() {
      return this.past.length > 0;
    }
    get canRedo() {
      return this.future.length > 0;
    }
    clear() {
      this.past = [];
      this.future = [];
    }
  }

  // ---------- SVG ----------
  const XML = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" };
  const escapeXml = s => String(s ?? "").replace(/[&<>"']/g, c => XML[c]);
  const fmt = n => String(zero(Math.round(n * 1000) / 1000));
  const LABEL_SIZE = 2;
  const INK = "#f0ece4";
  const OUTLINE = "#16151b";

  function colorOf(it) {
    if (typeof it.color === "string" && /^#[0-9a-f]{3,8}$/i.test(it.color)) return it.color;
    return it.type === "marker" ? (MARKER[it.kind] ?? MARKER.note).color : (KIND[it.kind] ?? KIND.other).color;
  }

  function darker(hex) {
    const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(hex);
    if (!m) return OUTLINE;
    return "#" + m.slice(1, 4).map(h => Math.round(parseInt(h, 16) * 0.55).toString(16).padStart(2, "0")).join("");
  }

  function label(text, x, y, size = LABEL_SIZE) {
    return `<text class="label" x="${fmt(x)}" y="${fmt(y)}" font-size="${fmt(size)}" text-anchor="middle" ` +
      `dominant-baseline="central" fill="${INK}" stroke="${OUTLINE}" stroke-width="${fmt(size / 6)}" ` +
      `paint-order="stroke" font-family="Inter, system-ui, sans-serif">${escapeXml(text)}</text>`;
  }

  function shapeSvg(it, color) {
    const edge = darker(color);
    const zone = it.kind === "zone";
    const fill = zone ? `fill="${color}" fill-opacity="0.18" stroke="${color}" stroke-dasharray="1.5 1"` : `fill="${color}" stroke="${edge}"`;
    const rot = it.rot ? ` transform="rotate(${fmt(it.rot)} ${fmt(it.x)} ${fmt(it.y)})"` : "";
    switch (it.type) {
      case "rect":
        return `<rect x="${fmt(it.x - it.w / 2)}" y="${fmt(it.y - it.h / 2)}" width="${fmt(it.w)}" height="${fmt(it.h)}" ` +
          `${fill} stroke-width="0.3"${rot}/>`;
      case "ellipse":
        return `<ellipse cx="${fmt(it.x)}" cy="${fmt(it.y)}" rx="${fmt(it.w / 2)}" ry="${fmt(it.h / 2)}" ${fill} stroke-width="0.3"${rot}/>`;
      case "polygon":
        return `<polygon points="${it.points.map(p => `${fmt(p[0])},${fmt(p[1])}`).join(" ")}" ${fill} stroke-width="0.3" stroke-linejoin="round"/>`;
      case "line":
        return `<polyline points="${it.points.map(p => `${fmt(p[0])},${fmt(p[1])}`).join(" ")}" fill="none" stroke="${color}" ` +
          `stroke-width="${fmt(it.width)}" stroke-linecap="round" stroke-linejoin="round"${zone ? ' stroke-opacity="0.4"' : ""}/>`;
      case "marker": {
        const glyph = (MARKER[it.kind] ?? MARKER.note).glyph;
        return `<circle cx="${fmt(it.x)}" cy="${fmt(it.y)}" r="${MARKER_R}" fill="${color}" stroke="${OUTLINE}" stroke-width="0.3"/>` +
          `<text x="${fmt(it.x)}" y="${fmt(it.y)}" font-size="1.9" font-weight="700" text-anchor="middle" dominant-baseline="central" ` +
          `fill="${OUTLINE}" font-family="Inter, system-ui, sans-serif">${escapeXml(glyph)}</text>`;
      }
      default:
        return `<text x="${fmt(it.x)}" y="${fmt(it.y)}" font-size="${fmt(it.size)}" text-anchor="middle" dominant-baseline="central" ` +
          `fill="${typeof it.color === "string" ? color : INK}" font-family="Alegreya Sans SC, Inter, sans-serif" ` +
          `font-weight="700">${escapeXml(it.text)}</text>`;
    }
  }

  function itemSvg(it, opts = {}) {
    const color = colorOf(it);
    const opacity = it.opacity ?? 1;
    let out = `<g data-id="${escapeXml(it.id)}"${opacity !== 1 ? ` opacity="${fmt(opacity)}"` : ""}>`;
    if (it.note) out += `<title>${escapeXml(it.label ? `${it.label}: ${it.note}` : it.note)}</title>`;
    out += shapeSvg(it, color);
    if (opts.labels !== false && it.label && it.type !== "text") {
      const [cx, cy] = center(it);
      out += it.type === "marker" ? label(it.label, cx, cy + MARKER_R + 1.4, 1.6) : label(it.label, cx, cy);
    }
    return out + "</g>";
  }

  function frameOf(sketch, items) {
    let x0 = 0;
    let y0 = 0;
    let x1 = sketch.size_m[0];
    let y1 = sketch.size_m[1];
    for (const it of items) {
      const b = bounds(it);
      x0 = Math.min(x0, b.x0);
      y0 = Math.min(y0, b.y0);
      x1 = Math.max(x1, b.x1);
      y1 = Math.max(y1, b.y1);
    }
    return { x0, y0, x1, y1 };
  }

  function toSvg(sketch, opts = {}) {
    const layers = sketch.layers.filter(l => l.visible !== false);
    const items = layers.flatMap(l => l.items);
    const pad = 4;
    const f = frameOf(sketch, items);
    const kinds = KINDS.filter(k => items.some(it => it.type !== "marker" && it.type !== "text" && it.kind === k.id));
    const marks = MARKER_KINDS.filter(k => items.some(it => it.type === "marker" && it.kind === k.id));
    const legend = [...kinds.map(k => [k.color, k.name, false]), ...marks.map(k => [k.color, k.name, true])];
    const row = 3;
    const cols = Math.max(1, Math.floor((f.x1 - f.x0) / 30));
    const legendH = legend.length ? Math.ceil(legend.length / cols) * row + row : 0;
    const vx = f.x0 - pad;
    const vy = f.y0 - pad;
    const vw = f.x1 - f.x0 + pad * 2;
    const vh = f.y1 - f.y0 + pad * 2 + 6 + legendH;
    const out = [
      `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${fmt(vx)} ${fmt(vy)} ${fmt(vw)} ${fmt(vh)}" ` +
        `width="${fmt(vw * 8)}" height="${fmt(vh * 8)}">`,
      `<title>${escapeXml(sketch.name)}</title>`,
      sketch.notes ? `<desc>${escapeXml(sketch.notes)}</desc>` : "",
      `<rect x="${fmt(vx)}" y="${fmt(vy)}" width="${fmt(vw)}" height="${fmt(vh)}" fill="#16151b"/>`,
      `<rect x="0" y="0" width="${fmt(sketch.size_m[0])}" height="${fmt(sketch.size_m[1])}" fill="#1e1c25"/>`,
    ];
    if (opts.underlayPaths) out.push(opts.underlayPaths);
    for (const l of layers) {
      out.push(`<g data-layer="${escapeXml(l.id)}"${l.dimmed ? ' opacity="0.25"' : ""}>`);
      for (const it of l.items) out.push(itemSvg(it, opts));
      out.push("</g>");
    }
    // Scale bar: 10 m.
    const sy = f.y1 + pad + 1;
    out.push(`<g><rect x="${fmt(f.x0)}" y="${fmt(sy)}" width="10" height="0.6" fill="${INK}"/>` +
      label("10 m", f.x0 + 5, sy + 2.2, 1.6) + "</g>");
    // Legend.
    const ly = sy + 6;
    legend.forEach(([color, name, isMarker], i) => {
      const x = f.x0 + (i % cols) * 30;
      const y = ly + Math.floor(i / cols) * row;
      out.push(isMarker
        ? `<circle cx="${fmt(x + 1)}" cy="${fmt(y)}" r="1" fill="${color}"/>`
        : `<rect x="${fmt(x)}" y="${fmt(y - 1)}" width="2" height="2" fill="${color}"/>`);
      out.push(`<text x="${fmt(x + 3)}" y="${fmt(y)}" font-size="1.6" dominant-baseline="central" fill="${INK}" ` +
        `font-family="Inter, system-ui, sans-serif">${escapeXml(name)}</text>`);
    });
    out.push("</svg>");
    return out.filter(Boolean).join("\n") + "\n";
  }

  // ---------- Underlay ----------
  // A game map from map_to_underlay.py, drawn faintly behind the sketch: one merged path per kind of tile.
  const UNDERLAY_COLORS = {
    wall: KIND.town_wall.color, floor: KIND.street.color, indoor: KIND.house_interior.color, sea: KIND.sea.color,
    water: KIND.canal.color, lava: KIND.lava.color, chasm: "#050407", mud: KIND.bog.color, thorns: "#6b2a2a",
  };

  function checkUnderlay(u) {
    if (!u || typeof u !== "object" || u.format !== "ashen-vault-underlay" || !Array.isArray(u.rows) ||
        !u.codes || typeof u.codes !== "object") {
      throw new Error("Not an underlay (make one with map_to_underlay.py)");
    }
  }

  function underlayPaths(u) {
    checkUnderlay(u);
    const t = num(u.tile_m) && u.tile_m > 0 ? u.tile_m : 2;
    const parts = {};
    u.rows.forEach((row, z) => {
      const line = String(row);
      for (let x = 0; x < line.length;) {
        let end = x + 1;
        while (end < line.length && line[end] === line[x]) end++;
        const kind = u.codes[line[x]];
        if (kind) (parts[kind] ??= []).push(`M${fmt(x * t)} ${fmt(z * t)}h${fmt((end - x) * t)}v${fmt(t)}h-${fmt((end - x) * t)}z`);
        x = end;
      }
    });
    return Object.entries(parts).map(([kind, d]) => ({ kind, d: d.join("") }));
  }

  function underlaySvg(u) {
    const out = underlayPaths(u).map(p => `<path d="${p.d}" fill="${UNDERLAY_COLORS[p.kind] ?? KIND.other.color}"/>`);
    for (const m of Array.isArray(u.marks) ? u.marks : []) {
      if (!num(m.x) || !num(m.y)) continue;
      const k = MARKER[m.kind] ?? MARKER.note;
      out.push(`<circle cx="${fmt(m.x)}" cy="${fmt(m.y)}" r="1" fill="${k.color}"/>`);
      if (m.label) out.push(label(m.label, m.x, m.y + 2.2, 1.4));
    }
    return out.join("");
  }

  const SketchModel = {
    FORMAT, VERSION, DEFAULT_SIZE, KINDS, KIND, MARKER_KINDS, MARKER, TYPES, MIN_SIZE, MARKER_R,
    newId, slug, newLayer, newSketch, normalize, serialize,
    bounds, corners, center, hitTest, itemsInBox, snapPoint, snapAngle, distance, moveItem, rotateItem,
    resizeItem, insertPoint, removePoint, movePoint, nearestSegment, toLocal, toWorld,
    History, escapeXml, colorOf, itemSvg, toSvg, frameOf, fmt, UNDERLAY_COLORS, underlayPaths, underlaySvg,
  };
  if (typeof module !== "undefined") module.exports = SketchModel;
  globalThis.SketchModel = SketchModel;
})();
