// Tests for model.js. Run: node --test tools/level_sketch/
"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const M = require("./model.js");

// ---------- Kinds and schema ----------

test("newSketch has the spec's defaults", () => {
  const s = M.newSketch("Harrowmere v2");
  assert.equal(s.format, "ashen-vault-sketch");
  assert.equal(s.version, 1);
  assert.equal(s.name, "harrowmere-v2");
  assert.deepEqual(s.size_m, [120, 120]);
  assert.equal(s.layers.length, 1);
  assert.equal(s.layers[0].name, "Ground");
  assert.deepEqual(s.layers[0].items, []);
});

test("slug", () => {
  assert.equal(M.slug("Cinderhold  REDO!"), "cinderhold-redo");
  assert.equal(M.slug("***"), "sketch");
  assert.equal(M.slug("a".repeat(60)).length, 40);
});

test("every kind has a colour and a known group; ids are unique", () => {
  const groups = new Set(["Ground", "Indoors", "Walls", "Water and void", "Structures", "Zone", "Other"]);
  for (const k of M.KINDS) {
    assert.match(k.color, /^#[0-9a-f]{6}$/i, k.id);
    assert.ok(groups.has(k.group), k.id);
    assert.equal(M.KIND[k.id], k);
  }
  assert.equal(new Set(M.KINDS.map(k => k.id)).size, M.KINDS.length);
  for (const id of ["street", "lava", "chasm", "fortress_wall", "zone", "other", "lift_shaft"]) assert.ok(M.KIND[id], id);
  for (const k of M.MARKER_KINDS) {
    assert.match(k.color, /^#[0-9a-f]{6}$/i, k.id);
    assert.ok(k.glyph, k.id);
  }
  assert.equal(new Set(M.MARKER_KINDS.map(k => k.id)).size, M.MARKER_KINDS.length);
  assert.ok(M.MARKER.lift && M.MARKER.npc && M.MARKER.start);
});

test("normalize fills defaults and keeps unknown fields", () => {
  const s = M.normalize({
    format: "ashen-vault-sketch", version: 1, future: 7,
    layers: [{ name: "Ground", items: [{ type: "rect", x: 1, y: 2, w: 3, h: 4, extra: "kept" }] }],
  });
  assert.equal(s.future, 7);
  assert.deepEqual(s.size_m, [120, 120]);
  const it = s.layers[0].items[0];
  assert.equal(it.extra, "kept");
  assert.equal(it.kind, "other");
  assert.equal(it.rot, 0);
  assert.ok(it.id);
  assert.ok(s.layers[0].id);
  assert.equal(s.layers[0].visible, true);
});

test("normalize: no layers gives one empty Ground layer", () => {
  assert.equal(M.normalize({ format: "ashen-vault-sketch" }).layers[0].name, "Ground");
});

test("normalize: unknown kind becomes other, keeping the original as kind_was", () => {
  const it = M.normalize({ layers: [{ items: [{ type: "rect", kind: "volcano", x: 0, y: 0, w: 1, h: 1 }] }] })
    .layers[0].items[0];
  assert.equal(it.kind, "other");
  assert.equal(it.kind_was, "volcano");
});

test("normalize drops items of unknown type and points that aren't numbers", () => {
  const s = M.normalize({ layers: [{ items: [
    { type: "blob", x: 0, y: 0 },
    { type: "polygon", points: [[0, 0], [1, "x"], [2, 2]] },
    { type: "line", points: [[0, 0]] },
    { type: "line", points: [[0, 0], [4, 0], [null, 1]] },
    { type: "rect", x: "a", y: 0, w: 1, h: 1 },
  ] }] });
  const items = s.layers[0].items;
  assert.equal(items.length, 1);
  assert.equal(items[0].type, "line");
  assert.deepEqual(items[0].points, [[0, 0], [4, 0]]);
  assert.equal(items[0].width, 2);
});

test("normalize: unique ids, even when a file repeats one", () => {
  const s = M.normalize({ layers: [{ items: [
    { id: "s1", type: "marker", kind: "npc", x: 1, y: 1 },
    { id: "s1", type: "marker", kind: "dragon", x: 2, y: 2 },
  ] }] });
  const [a, b] = s.layers[0].items;
  assert.notEqual(a.id, b.id);
  assert.equal(b.kind, "note");
});

test("normalize refuses what isn't a sketch", () => {
  assert.throws(() => M.normalize({ format: "ashen-vault-underlay" }), /Not an Ashen Vault sketch/);
  assert.throws(() => M.normalize("hello"), /Not an Ashen Vault sketch/);
  assert.throws(() => M.normalize(null), /Not an Ashen Vault sketch/);
});

function everyItem() {
  const s = M.newSketch("every");
  s.notes = "whole level";
  s.layers[0].items.push(
    { id: "s1", type: "rect", kind: "plaza", label: "Market", note: "fountain", x: 40, y: 60, w: 24, h: 18, rot: -8, height_m: 0 },
    { id: "s2", type: "ellipse", kind: "garden", x: 10, y: 10, w: 6, h: 4, rot: 0 },
    { id: "s3", type: "polygon", kind: "hall", label: "Cathedral", points: [[50, 8], [80, 8], [82, 24], [48, 26]] },
    { id: "s4", type: "line", kind: "canal", width: 4, points: [[60, 104], [58, 80], [64, 60]] },
    { id: "m1", type: "marker", kind: "npc", label: "Odrin", x: 70, y: 50 },
    { id: "t1", type: "text", text: "upper town", x: 60, y: 30, size: 3 },
  );
  return s;
}

test("serialize round-trips through normalize unchanged", () => {
  const once = M.serialize(M.normalize(JSON.parse(M.serialize(everyItem()))));
  const twice = M.serialize(M.normalize(JSON.parse(once)));
  assert.equal(once, twice);
  assert.ok(once.endsWith("}\n"));
  const back = JSON.parse(once);
  assert.equal(back.layers[0].items.length, 6);
  assert.equal(back.layers[0].items[0].label, "Market");
});

module.exports = { everyItem };

// ---------- Geometry ----------

const near = (a, b, msg) => assert.ok(Math.abs(a - b) < 1e-9, `${msg ?? ""} ${a} != ${b}`);

test("hitTest honours rotation", () => {
  const r = { type: "rect", x: 10, y: 10, w: 20, h: 2, rot: 90 };
  assert.ok(M.hitTest(r, [10, 19], 0)); // inside the rotated bar
  assert.ok(!M.hitTest(r, [19, 10], 0)); // where the unrotated bar would be
});

test("hitTest on an ellipse, a marker and text", () => {
  const e = { type: "ellipse", x: 0, y: 0, w: 10, h: 4, rot: 0 };
  assert.ok(M.hitTest(e, [4.5, 0], 0));
  assert.ok(!M.hitTest(e, [4.5, 1.9], 0)); // inside the box, outside the ellipse
  assert.ok(M.hitTest({ type: "marker", kind: "npc", x: 5, y: 5 }, [5.8, 5], 0));
  assert.ok(!M.hitTest({ type: "marker", kind: "npc", x: 5, y: 5 }, [7, 5], 0));
  assert.ok(M.hitTest({ type: "text", text: "Market", x: 0, y: 0, size: 3 }, [1, 0], 0));
});

test("resizeItem works in the item's own frame", () => {
  const r = { type: "rect", x: 0, y: 0, w: 10, h: 4, rot: 90 };
  const out = M.resizeItem(r, "e", [0, 7]); // the east handle now points south
  assert.equal(out.w, 12);
  assert.equal(out.h, 4);
  assert.equal(out.rot, 90);
  near(out.x, 0);
  near(out.y, 1); // west edge stays at y = -5
});

test("resizeItem from a corner keeps the opposite corner; keepRatio keeps the shape", () => {
  const r = { type: "rect", x: 5, y: 5, w: 10, h: 10, rot: 0 };
  const out = M.resizeItem(r, "se", [20, 12]);
  near(out.w, 20); near(out.h, 12); near(out.x, 10); near(out.y, 6);
  const sq = M.resizeItem(r, "se", [20, 12], true);
  near(sq.w, sq.h);
});

test("resizeItem keeps a minimum size", () => {
  const r = { type: "rect", x: 0, y: 0, w: 10, h: 4, rot: 0 };
  const out = M.resizeItem(r, "e", [-20, 0]);
  assert.equal(out.w, 0.5);
  near(out.x, -5 + 0.25); // the west edge stays put
});

test("bounds of a rotated rect", () => {
  const b = M.bounds({ type: "rect", x: 0, y: 0, w: 10, h: 2, rot: 90 });
  near(b.x1 - b.x0, 2); near(b.y1 - b.y0, 10);
  const p = M.bounds({ type: "polygon", points: [[0, 0], [4, 1], [2, 5]] });
  assert.deepEqual([p.x0, p.y0, p.x1, p.y1], [0, 0, 4, 5]);
});

test("line hit uses its width", () => {
  const l = { type: "line", width: 4, points: [[0, 0], [10, 0]] };
  assert.ok(M.hitTest(l, [5, 1.9], 0));
  assert.ok(!M.hitTest(l, [5, 2.5], 0));
  assert.ok(M.hitTest(l, [5, 2.5], 1));
});

test("polygon hit: inside, near an edge, outside", () => {
  const p = { type: "polygon", points: [[0, 0], [10, 0], [10, 10], [0, 10]] };
  assert.ok(M.hitTest(p, [5, 5], 0));
  assert.ok(M.hitTest(p, [10.5, 5], 1));
  assert.ok(!M.hitTest(p, [12, 5], 1));
});

test("itemsInBox takes only what lies wholly inside", () => {
  const items = [
    { id: "a", type: "rect", x: 5, y: 5, w: 2, h: 2, rot: 0 },
    { id: "b", type: "rect", x: 9, y: 5, w: 4, h: 2, rot: 0 },
  ];
  assert.deepEqual(M.itemsInBox(items, { x0: 0, y0: 0, x1: 10, y1: 10 }), ["a"]);
});

test("snapPoint / snapAngle / distance", () => {
  assert.deepEqual(M.snapPoint([2.6, -0.4], 2), [2, 0]);
  assert.equal(M.snapAngle(22, 15), 15);
  assert.equal(M.distance([0, 0], [3, 4]), 5);
});

test("moveItem moves every kind of item", () => {
  assert.deepEqual(M.moveItem({ type: "line", points: [[0, 0], [1, 1]] }, 2, 3).points, [[2, 3], [3, 4]]);
  const r = M.moveItem({ type: "rect", x: 1, y: 1, w: 1, h: 1, rot: 0 }, 2, 3);
  assert.deepEqual([r.x, r.y], [3, 4]);
});

test("removePoint keeps polygons at 3 points and lines at 2", () => {
  const tri = { type: "polygon", points: [[0, 0], [1, 0], [0, 1]] };
  assert.equal(M.removePoint(tri, 0), tri);
  const quad = { type: "polygon", points: [[0, 0], [1, 0], [1, 1], [0, 1]] };
  assert.deepEqual(M.removePoint(quad, 1).points, [[0, 0], [1, 1], [0, 1]]);
  const seg = { type: "line", points: [[0, 0], [1, 0]] };
  assert.equal(M.removePoint(seg, 0), seg);
});

test("insertPoint, movePoint and nearestSegment", () => {
  const l = { type: "line", points: [[0, 0], [10, 0], [10, 10]] };
  assert.deepEqual(M.insertPoint(l, 0, [5, 0]).points, [[0, 0], [5, 0], [10, 0], [10, 10]]);
  assert.deepEqual(M.movePoint(l, 2, [12, 12]).points[2], [12, 12]);
  assert.equal(M.nearestSegment(l, [11, 6]).index, 1);
  near(M.nearestSegment(l, [11, 6]).dist, 1);
  // A polygon's closing edge counts too.
  const sq = { type: "polygon", points: [[0, 0], [10, 0], [10, 10], [0, 10]] };
  assert.equal(M.nearestSegment(sq, [-1, 5]).index, 3);
});

test("rotateItem on a polygon rotates its points about the centre", () => {
  const p = { type: "polygon", points: [[0, 0], [4, 0], [4, 2], [0, 2]] };
  const out = M.rotateItem(p, 90);
  const b = M.bounds(out);
  near(b.x0, 1); near(b.x1, 3); near(b.y0, -1); near(b.y1, 3);
  assert.equal(M.rotateItem({ type: "rect", x: 0, y: 0, w: 1, h: 1, rot: 10 }, 30).rot, 40);
});

test("geometry functions don't mutate their input", () => {
  const r = { type: "rect", x: 0, y: 0, w: 10, h: 4, rot: 0 };
  const p = { type: "polygon", points: [[0, 0], [4, 0], [4, 2], [0, 2]] };
  const before = JSON.stringify([r, p]);
  M.moveItem(r, 1, 1); M.resizeItem(r, "n", [0, -9]); M.rotateItem(r, 5);
  M.moveItem(p, 1, 1); M.rotateItem(p, 30); M.insertPoint(p, 0, [2, 0]); M.removePoint(p, 0); M.movePoint(p, 0, [9, 9]);
  assert.equal(JSON.stringify([r, p]), before);
});

// ---------- History and SVG ----------

test("History: record, undo, redo, limit", () => {
  const h = new M.History(3);
  h.record("a"); h.record("b"); h.record("c"); h.record("d"); // "a" falls off
  assert.equal(h.undo("e"), "d");
  assert.equal(h.undo("d"), "c");
  assert.equal(h.undo("c"), "b");
  assert.equal(h.undo("b"), null);
  assert.equal(h.redo("b"), "c");
  h.record("x");
  assert.equal(h.canRedo, false);
  assert.equal(h.canUndo, true);
  h.clear();
  assert.equal(h.canUndo, false);
  assert.equal(new M.History().limit, 150);
});

test("toSvg escapes labels and notes", () => {
  const s = M.newSketch("t");
  s.layers[0].items.push({ id: "s1", type: "rect", kind: "plaza", x: 5, y: 5, w: 4, h: 4, rot: 0,
    label: `Tom & "Jerry's" <inn>`, note: "café <b>" });
  const svg = M.toSvg(s);
  assert.ok(svg.includes("Tom &amp; &quot;Jerry&apos;s&quot; &lt;inn&gt;"));
  assert.ok(!svg.includes("<inn>"));
  assert.ok(svg.includes("café &lt;b&gt;"));
  assert.ok(svg.startsWith("<svg") && svg.includes('xmlns="http://www.w3.org/2000/svg"'));
  assert.ok(svg.includes("<title>t</title>"));
});

test("toSvg legend lists exactly the kinds used", () => {
  const s = M.newSketch("legend");
  s.layers[0].items.push(
    { id: "a", type: "rect", kind: "plaza", x: 5, y: 5, w: 4, h: 4, rot: 0 },
    { id: "b", type: "line", kind: "lava", width: 2, points: [[0, 0], [9, 9]] },
    { id: "c", type: "marker", kind: "shrine", x: 3, y: 3 },
  );
  const svg = M.toSvg(s);
  for (const name of ["Plaza / setts", "Lava", "Shrine"]) assert.ok(svg.includes(name), name);
  for (const name of ["Bog / mud", "Chasm", "Boss"]) assert.ok(!svg.includes(name), name);
});

test("toSvg leaves hidden layers out and frames items beyond the sketch's size", () => {
  const s = M.newSketch("layers");
  s.layers[0].items.push({ id: "a", type: "rect", kind: "plaza", label: "Seen", x: 5, y: 5, w: 4, h: 4, rot: 0 });
  s.layers.push({ id: "l2", name: "Hidden", visible: false, dimmed: false,
    items: [{ id: "b", type: "rect", kind: "lava", label: "Unseen", x: 5, y: 5, w: 4, h: 4, rot: 0 }] });
  s.layers[0].items.push({ id: "c", type: "marker", kind: "npc", x: 300, y: 5 });
  const svg = M.toSvg(s);
  assert.ok(svg.includes("Seen") && !svg.includes("Unseen"));
  const width = Number(svg.match(/viewBox="[-\d.]+ [-\d.]+ ([-\d.]+)/)[1]);
  assert.ok(width > 300, String(width));
});

test("itemSvg draws each item type", () => {
  const s = everyItem();
  const svgs = Object.fromEntries(s.layers[0].items.map(it => [it.type, M.itemSvg(it)]));
  assert.match(svgs.rect, /<rect[^>]*transform="rotate\(-8 40 60\)"/);
  assert.match(svgs.ellipse, /<ellipse/);
  assert.match(svgs.polygon, /<polygon[^>]*points="50,8 80,8 82,24 48,26"/);
  assert.match(svgs.line, /<polyline[^>]*stroke-width="4"/);
  assert.ok(svgs.marker.includes(">N<"));
  assert.match(svgs.text, /<text[^>]*>upper town<\/text>/);
  assert.ok(svgs.rect.includes(">Market<"));
  assert.ok(!M.itemSvg(s.layers[0].items[0], { labels: false }).includes(">Market<"));
  assert.ok(M.itemSvg(s.layers[0].items[0]).includes('data-id="s1"'));
});

test("itemSvg uses the colour override and opacity", () => {
  const svg = M.itemSvg({ id: "a", type: "rect", kind: "plaza", x: 0, y: 0, w: 1, h: 1, rot: 0, color: "#123456", opacity: 0.5 });
  assert.ok(svg.includes("#123456") && svg.includes('opacity="0.5"'));
  assert.ok(!M.itemSvg({ id: "b", type: "rect", kind: "plaza", x: 0, y: 0, w: 1, h: 1, rot: 0, color: "red\" onload=\"x" }).includes('onload="x'));
});

// ---------- Underlay ----------

test("underlayPaths merges runs and scales to metres", () => {
  const u = { format: "ashen-vault-underlay", version: 1, w: 4, h: 2, tile_m: 2,
    codes: { "#": "wall", ".": "floor" }, rows: ["##..", ".##."], marks: [] };
  const paths = Object.fromEntries(M.underlayPaths(u).map(p => [p.kind, p.d]));
  assert.deepEqual(Object.keys(paths).sort(), ["floor", "wall"]);
  assert.equal(paths.wall, "M0 0h4v2h-4zM2 2h4v2h-4z");
  assert.equal(paths.floor, "M4 0h4v2h-4zM0 2h2v2h-2zM6 2h2v2h-2z");
});

test("underlayPaths rejects what isn't an underlay", () => {
  assert.throws(() => M.underlayPaths({ format: "ashen-vault-sketch" }), /Not an underlay/);
  assert.throws(() => M.underlayPaths(null), /Not an underlay/);
  assert.throws(() => M.underlayPaths({ format: "ashen-vault-underlay", rows: "nope" }), /Not an underlay/);
});

test("every underlay kind has a colour, and underlaySvg escapes mark labels", () => {
  for (const kind of ["wall", "floor", "indoor", "sea", "water", "lava", "chasm", "mud", "thorns"]) {
    assert.match(M.UNDERLAY_COLORS[kind], /^#[0-9a-f]{6}$/i, kind);
  }
  const u = { format: "ashen-vault-underlay", version: 1, w: 1, h: 1, tile_m: 2, codes: { ".": "floor" }, rows: ["."],
    marks: [{ kind: "npc", x: 1, y: 1, label: "<Odrin>", note: "" }] };
  const svg = M.underlaySvg(u);
  assert.ok(svg.includes("&lt;Odrin&gt;") && svg.includes("<path"));
});

// ---------- Review fixes ----------

test("normalize refuses JSON that isn't a sketch even without a format field", () => {
  assert.throws(() => M.normalize({ name: "ashen-vault", version: "1.0.0" }), /Not an Ashen Vault sketch/);
  assert.throws(() => M.normalize({ w: 3, h: 2, rows: ["...", "..."], marks: [] }), /Not an Ashen Vault sketch/);
  assert.equal(M.normalize({ layers: [] }).layers.length, 1); // an old, format-less sketch still opens
});

test("a zone is hit only near its outline, so what it surrounds stays clickable", () => {
  const z = { type: "rect", kind: "zone", x: 0, y: 0, w: 20, h: 10, rot: 0 };
  assert.ok(!M.hitTest(z, [0, 0], 0.5));
  assert.ok(M.hitTest(z, [9.8, 0], 0.5));
  const ze = { type: "ellipse", kind: "zone", x: 0, y: 0, w: 20, h: 10, rot: 0 };
  assert.ok(!M.hitTest(ze, [0, 0], 0.5));
  assert.ok(M.hitTest(ze, [10, 0], 0.5));
  const zp = { type: "polygon", kind: "zone", points: [[0, 0], [10, 0], [10, 10], [0, 10]] };
  assert.ok(!M.hitTest(zp, [5, 5], 0.5));
  assert.ok(M.hitTest(zp, [0.2, 5], 0.5));
});
