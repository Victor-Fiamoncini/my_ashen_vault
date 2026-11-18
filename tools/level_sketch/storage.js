// Ashen Vault Level Sketch: keeping sketches. Exposes `SketchStorage`.
// - Autosave: the open sketch (and the underlay you loaded) in this browser's localStorage, so a closed tab
//   loses nothing. Every access is guarded: the page works without it.
// - Save / Open: straight into a folder you pick once (tools/level_sketch/sketches/) through the File System
//   Access API; its handle is kept in IndexedDB, so a reload only asks for permission again. Where the API is
//   missing or refused, Save downloads the two files and Open takes a file picker.
"use strict";
(function () {
  const M = globalThis.SketchModel;
  const KEY = "ashen-sketch:autosave";
  const UNDERLAY_KEY = "ashen-sketch:underlay";
  const DIRTY_KEY = "ashen-sketch:unsaved";
  const DB = "ashen-sketch";
  const STORE = "handles";

  const ls = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); return true; } catch { return false; } },
    remove(k) { try { localStorage.removeItem(k); } catch { /* nothing to do */ } },
  };

  let timer = null;
  let pending = null;
  // `dirty: false` when the sketch matches a file (just opened, or new and empty).
  function autosave(sketch, { dirty = true } = {}) {
    ls.set(DIRTY_KEY, dirty ? "1" : "0");
    pending = M.serialize(sketch); // taken now, written shortly
    clearTimeout(timer);
    timer = setTimeout(flush, 500);
  }
  function flush() {
    clearTimeout(timer);
    if (pending !== null) ls.set(KEY, pending);
    pending = null;
  }
  function restore() {
    try {
      const text = ls.get(KEY);
      return text ? M.normalize(JSON.parse(text)) : null;
    } catch {
      return null;
    }
  }
  // Whether the restored sketch has changes no file holds; unknown counts as yes, so nothing is dropped unasked.
  const restoredDirty = () => ls.get(DIRTY_KEY) !== "0";
  const markSaved = () => ls.set(DIRTY_KEY, "0");

  function rememberUnderlay(data) {
    if (data) ls.set(UNDERLAY_KEY, JSON.stringify(data));
    else ls.remove(UNDERLAY_KEY);
  }
  function restoreUnderlay() {
    try { return JSON.parse(ls.get(UNDERLAY_KEY) || "null"); } catch { return null; }
  }

  // ---------- IndexedDB, for the folder handle ----------
  function idb(mode, fn) {
    return new Promise((resolve, reject) => {
      let req;
      try { req = indexedDB.open(DB, 1); } catch (err) { reject(err); return; }
      req.onupgradeneeded = () => req.result.createObjectStore(STORE);
      req.onerror = () => reject(req.error);
      req.onsuccess = () => {
        const tx = req.result.transaction(STORE, mode);
        const r = fn(tx.objectStore(STORE));
        tx.oncomplete = () => resolve(r?.result);
        tx.onerror = () => reject(tx.error);
      };
    });
  }
  const idbGet = key => idb("readonly", s => s.get(key)).catch(() => null);
  const idbSet = (key, value) => idb("readwrite", s => s.put(value, key)).catch(() => null);

  // ---------- The folder ----------
  let folder = null;
  const canUseFolder = () => typeof window !== "undefined" && "showDirectoryPicker" in window;

  async function pickFolder() {
    folder = await window.showDirectoryPicker({ id: "ashen-sketches", mode: "readwrite" });
    await idbSet("folder", folder);
    return folder;
  }

  // The remembered folder if we may use it; `ask` requests permission again (needs a click behind it).
  async function folderHandle(ask) {
    if (!canUseFolder()) return null;
    if (!folder) folder = await idbGet("folder");
    if (!folder) return null;
    try {
      let p = await folder.queryPermission({ mode: "readwrite" });
      if (p !== "granted" && ask) p = await folder.requestPermission({ mode: "readwrite" });
      return p === "granted" ? folder : null;
    } catch {
      return null;
    }
  }

  async function writeFile(dir, name, text) {
    const fh = await dir.getFileHandle(name, { create: true });
    const w = await fh.createWritable();
    await w.write(text);
    await w.close();
  }

  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  // Names of sketch files this session opened or saved: writing over one of those is expected.
  const known = new Set();
  const markKnown = name => known.add(name);
  async function exists(dir, name) {
    try { await dir.getFileHandle(name); return true; } catch { return false; }
  }
  const abort = () => Object.assign(new Error("Save cancelled"), { name: "AbortError" });

  // Resolves to { where: "folder", folder, files } or { where: "download", files, reason }.
  // Rejects with an AbortError when you cancel choosing the folder, or decline to write over a sketch file
  // of the same name that this session didn't open or save (`confirmOverwrite(name)` asks).
  async function save(sketch, { confirmOverwrite = async () => true } = {}) {
    const base = M.slug(sketch.name);
    const files = [`${base}.sketch.json`, `${base}.svg`];
    const json = M.serialize(sketch);
    const svg = M.toSvg(sketch);
    let reason = "this browser can't write to a folder";
    if (canUseFolder()) {
      let dir = await folderHandle(true);
      if (!dir) {
        try {
          dir = await pickFolder();
        } catch (err) {
          if (err?.name === "AbortError") throw err;
          dir = null;
          reason = "the folder couldn't be opened";
        }
      }
      if (dir) {
        if (!known.has(files[0]) && (await exists(dir, files[0])) && !(await confirmOverwrite(files[0]))) throw abort();
        try {
          await writeFile(dir, files[0], json);
          await writeFile(dir, files[1], svg);
          flush();
          known.add(files[0]);
          markSaved();
          return { where: "folder", folder: dir.name, files };
        } catch {
          reason = "writing to the folder was refused";
        }
      }
    }
    download(files[0], json, "application/json");
    download(files[1], svg, "image/svg+xml");
    flush();
    markSaved();
    return { where: "download", files, reason };
  }

  async function list() {
    const dir = await folderHandle(false);
    if (!dir) return [];
    const names = [];
    try {
      for await (const [name, h] of dir.entries()) {
        if (h.kind === "file" && name.endsWith(".sketch.json")) names.push(name);
      }
    } catch {
      return [];
    }
    return names.sort();
  }

  async function openNamed(name) {
    const dir = await folderHandle(true);
    if (!dir) throw new Error("The sketches folder isn't available: choose it again");
    const file = await (await dir.getFileHandle(name)).getFile();
    const sketch = parse(await file.text());
    known.add(name);
    return sketch;
  }

  function parse(text) {
    let data;
    try { data = JSON.parse(text); } catch { throw new Error("Not an Ashen Vault sketch"); }
    return M.normalize(data);
  }

  function exportSvg(name, svg) {
    download(`${M.slug(name)}.svg`, svg, "image/svg+xml");
  }

  globalThis.SketchStorage = {
    autosave, flush, restore, restoredDirty, markKnown, rememberUnderlay, restoreUnderlay, canUseFolder, pickFolder, folderHandle,
    save, list, openNamed, parse, exportSvg, folderName: () => folder?.name ?? null,
  };
})();
