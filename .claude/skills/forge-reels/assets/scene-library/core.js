/* ForgeReels scene core: the PURE half of the explainer runtime (no DOM; runs in the browser and in Node).
 *
 *   FR.parts(scene)                         -> every object id the scene can animate ("phone", "phone.glass", ...)
 *   FR.stateAt(t, scene, events, boxes)     -> { camera: {x, y, s}, obj: { id: {o, s, tx, ty, draw, type, ...} } }
 *   FR.captionAt(t, groups)                 -> { words: [{text, state: "past"|"now"|"next"}] } or null
 *
 * Everything is a function of t alone: HyperFrames seeks frames in any order.
 * events: [{t, dur, action, object, args}] from scripts/pipeline/visual_plan.py (t = the spoken word's start).
 * boxes:  { id: {x, y, w, h} } in world px, measured once by renderer.js (tests pass them by hand).
 */
(function (root) {
  "use strict";
  const FR = root.FR || (root.FR = {});

  // ---------- easing + helpers
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const E = {
    linear: (p) => p,
    out: (p) => 1 - Math.pow(1 - p, 3),
    inOut: (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2),
    back: (p) => 1 + 2.2 * Math.pow(p - 1, 3) + 1.2 * Math.pow(p - 1, 2),
  };
  FR.ease = E;

  // default action lengths (s); "type" scales with the text length in visual_plan.py
  FR.DUR = { reveal: 0.5, hide: 0.35, focus: 0.9, wide: 1.0, draw: 0.8, type: 0.9, pulse: 0.7, highlight: 0.45,
             count: 1.0, grow: 0.7, explode: 0.8, collapse: 0.6, flow: 1.2, move: 0.7, morph: 0.6, play: 4.0, strike: 0.4, scan: 0.6, theme: 0.45 };
  FR.ACTIONS = Object.keys(FR.DUR);
  FR.CAMERA_ACTIONS = ["focus", "wide"];
  FR.STAGE = "stage";             // the whole frame: object of "theme" (dark <-> light on a turn word)

  // ---------- components: their animatable parts (pure). renderer.js draws them.
  const n = (k, count) => Array.from({ length: count }, (_, i) => k + (i + 1));
  FR.COMPONENTS = {
    phone:    { parts: () => ["body", "screen", "ui", "grid", "rows", "cols", "glass", "notification"],
                hidden: () => ["grid", "notification"] },
    browser:  { parts: (s) => ["window", "address", "page", "title", "cursor", ...n("tab", (s.tabs || ["Home"]).length),
                               ...n("r", (s.results || []).length)], hidden: () => ["cursor"] },
    terminal: { parts: (s) => ["window", "cursor", ...n("l", (s.lines || []).length)], hidden: () => [] },
    nodes:    { parts: (s) => [...(s.nodes || []).map((x) => "n_" + x.id),
                               ...(s.links || []).map(([a, b]) => "l_" + a + "_" + b)], hidden: () => [] },
    chart:    { parts: (s) => ["title", "axis", ...n("b", (s.bars || []).length), ...n("v", (s.bars || []).length)],
                hidden: () => [] },
    document: { parts: (s) => ["page", "title", "source", ...n("l", (s.lines || []).length)], hidden: () => [] },
    chip:     { parts: (s) => ["chip", "label", "pins", ...n("t", s.traces || 6)], hidden: () => [] },
    text:     { parts: () => [], hidden: () => [] },
    counter:  { parts: () => ["label"], hidden: () => [] },
    callout:  { parts: () => ["arrow", "label"], hidden: () => [] },
    steps:    { parts: (s) => n("s", (s.steps || []).length), hidden: () => [] },
    frames:   { parts: () => [], hidden: () => [] },
    agent:    { parts: (s) => ["prompt", "input", ...n("s", (s.steps || []).length)], hidden: (s) => n("s", (s.steps || []).length) },
    image:    { parts: () => [], hidden: () => [] },
    // macro kit (renderer.js): lit close-ups that fill the frame
    finger:   { parts: () => ["tip", "print", "ions", "glow"], hidden: () => ["ions", "glow"] },
    section:  { parts: () => ["glass", "field", "electrodes", "pull", "pixels", "charge", "loss", "labels"], hidden: () => ["pull", "loss"] },
    mesh:     { parts: () => ["rows", "cols", "nodes", "sweep", "hot"], hidden: () => ["hot"] },
    cutaway:  { parts: (s) => n("L", (s.layers || []).length), hidden: () => [] },
    hand:     { parts: () => ["palm", "fingers", "thumb"], hidden: () => [] },
    // drawn per topic: an SVG file whose <g id="part"> groups are the parts listed in scene.json
    svg:      { parts: (s) => s.parts || [], hidden: () => [] },
    // live components (renderer.js FR.LIVE redraws them every frame from t and their state)
    swarm:    { parts: () => ["label"], hidden: () => [] },
    wave:     { parts: (s) => [...n("w", (s.waves || [{}]).length), "sum"], hidden: () => ["sum"] },
    space:    { parts: (s) => ["axes", ...n("c", (s.clusters || []).length), "arrow"], hidden: () => ["arrow"] },
    map:      { parts: (s) => ["land", ...(s.points || []).map((x) => "p_" + x.id),
                               ...(s.routes || []).map(([a, b]) => "r_" + a + "_" + b)], hidden: () => [] },
    // numbers, data and UI
    hud:      { parts: (s) => n("s", (s.steps || []).length), hidden: () => [] },
    gauge:    { parts: () => ["ring", "label"], hidden: () => [] },
    waffle:   { parts: () => ["cells", "marked", "label"], hidden: () => ["marked"] },
    code:     { parts: (s) => ["window", ...n("l", (s.lines || []).length), "stamp"], hidden: () => ["stamp"] },
    social:   { parts: () => ["card", "follow", "comment"], hidden: () => [] },
    calendar: { parts: () => ["page", "mark"], hidden: () => ["mark"] },
    logo:     { parts: () => ["tile", "mark", "label"], hidden: () => [] },   // a fetched brand logo (scripts/logo.py)
  };

  // frames component: which image of the sequence shows after `play` seconds of playback
  FR.frameIndex = (play, c) => Math.min((c.count || 1) - 1, Math.floor(play * (c.fps || 30) + 1e-6));
  // file of frame k (0-based): "%04d" in src, numbered from c.first (default 1, as ffmpeg writes image sequences)
  FR.frameSrc = (c, k) => c.src.replace(/%0(\d)d/, (_, d) => String(k + (c.first == null ? 1 : c.first)).padStart(+d, "0"));

  // ambient particles: n points drifting up through the frame, a pure function of t and seed (frames render in any order)
  FR.particles = function (t, count, seed) {
    let s = (seed || 1) >>> 0;
    const rnd = () => { s = (s + 0x6D2B79F5) >>> 0; let x = s; x = Math.imul(x ^ (x >>> 15), x | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };   // mulberry32
    return Array.from({ length: count }, () => {
      const x0 = rnd(), y0 = rnd(), speed = 0.006 + rnd() * 0.02, sway = rnd() * 6.28, size = rnd();
      const y = (((y0 - t * speed) % 1) + 1) % 1;
      return { x: clamp(x0 + 0.015 * Math.sin(t * 0.6 + sway), 0, 1), y, r: 1 + size * 2.5,
               a: clamp(0.25 + 0.55 * size * (0.6 + 0.4 * Math.sin(t * 1.3 + sway)), 0, 1) };
    });
  };

  // seeded random numbers (mulberry32): the same picture on every frame and every machine
  FR.rng = function (seed) {
    let s = (seed || 1) >>> 0;
    return () => { s = (s + 0x6D2B79F5) >>> 0; let x = s; x = Math.imul(x ^ (x >>> 15), x | 1);
      x ^= x + Math.imul(x ^ (x >>> 7), x | 61); return ((x ^ (x >>> 14)) >>> 0) / 4294967296; };
  };
  // swarm: where n dots sit (0..1) in a named shape; the renderer blends two shapes by the swarm's `explode`
  FR.SWARM_SHAPES = ["cloud", "grid", "ring", "stream", "clusters", "column"];
  FR.swarmLayout = function (name, count, seed) {
    const r = FR.rng(seed || 7), cols = Math.ceil(Math.sqrt(count)), rows = Math.ceil(count / cols);
    const gauss = () => Math.sqrt(-2 * Math.log(1 - r() * 0.999)) * Math.cos(6.2832 * r());
    const centres = [[0.27, 0.3], [0.72, 0.38], [0.45, 0.74]];
    return Array.from({ length: count }, (_, i) => {
      let x, y;
      if (name === "grid") { x = 0.08 + 0.84 * ((i % cols) + 0.5) / cols; y = 0.08 + 0.84 * (Math.floor(i / cols) + 0.5) / rows; }
      else if (name === "ring") { const a = 6.2832 * i / count, q = 0.36 + 0.05 * r(); x = 0.5 + q * Math.cos(a); y = 0.5 + q * Math.sin(a); }
      else if (name === "stream") { x = r(); y = 0.5 + 0.13 * gauss(); }
      else if (name === "clusters") { const k = centres[i % 3]; x = k[0] + 0.07 * gauss(); y = k[1] + 0.07 * gauss(); }
      else if (name === "column") { x = 0.5 + 0.05 * gauss(); y = 0.06 + 0.88 * r(); }
      else { x = 0.5 + 0.15 * gauss(); y = 0.5 + 0.15 * gauss(); }
      return [clamp(x, 0.01, 0.99), clamp(y, 0.01, 0.99)];
    });
  };
  // space: a 3D point (each axis -1..1) turned by yaw around the vertical axis, tilted by pitch -> x, y in -1..1 and depth z
  FR.project = function (pt, yaw, pitch) {
    const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    const x = pt[0] * cy + pt[2] * sy, z = -pt[0] * sy + pt[2] * cy;
    const y = pt[1] * cp - z * sp, z2 = pt[1] * sp + z * cp, k = 1 / (1 + 0.22 * z2);
    return { x: x * k, y: -y * k, z: z2 };
  };

  // odometer: which characters of a rolling number already show their final digit (they lock from the left)
  FR.odometer = function (cur, fin) {
    cur = String(cur).padStart(fin.length, " ");
    let locked = true;
    return Array.from(cur).map((ch, i) => { locked = locked && ch === fin[i]; return { ch, settled: locked }; });
  };

  FR.parts = function (scene) {
    const out = [];
    for (const c of scene.components || []) {
      const def = FR.COMPONENTS[c.type];
      if (!def) throw new Error("unknown component type '" + c.type + "' (" + c.id + ")");
      out.push(c.id, ...def.parts(c).map((p) => c.id + "." + p));
    }
    return out;
  };

  FR.hiddenAtStart = function (scene) {
    const out = new Set();
    for (const c of scene.components || []) {
      if (c.hidden === true) out.add(c.id);
      for (const p of FR.COMPONENTS[c.type].hidden(c).concat(Array.isArray(c.hidden) ? c.hidden : [])) out.add(c.id + "." + p);
    }
    return out;
  };

  // ---------- per-object state at t
  const BASE = () => ({ o: 1, s: 1, tx: 0, ty: 0, draw: 1, type: 1, pulse: 0, hl: 0, count: null, grow: 1,
                        explode: 0, flow: -1, blur: 0, play: 0, strike: 0, roll: 0, scan: 1 });

  function objectState(t, id, evs, hidden) {
    const st = BASE();
    const first = {};
    for (const e of evs) if (!(e.action in first)) first[e.action] = e;
    // hidden until its first event: a reveal, or a value that counts up (no "0.00" floating before its moment)
    if (hidden.has(id) || (evs[0] && ["reveal", "count", "scan"].indexOf(evs[0].action) >= 0)) st.o = 0;
    if (first.scan) st.scan = 0;
    if (first.draw) st.draw = 0;
    if (first.type) st.type = 0;
    if (first.grow) st.grow = 0;
    if (first.count) st.count = (first.count.args && first.count.args.from) || 0;
    for (const e of evs) {
      if (t < e.t) break;
      const p = clamp((t - e.t) / Math.max(e.dur, 1e-6), 0, 1);
      const q = E.out(p);
      const a = e.args || {};
      switch (e.action) {
        case "reveal": st.o = q; st.s = lerp(0.94, 1, q); st.ty = lerp(28, 0, q); break;
        case "hide": st.o *= 1 - q; break;
        case "draw": st.draw = q; break;
        case "type": st.type = p; break;
        case "grow": st.grow = E.back(p); break;
        case "count": st.count = lerp(a.from || 0, a.to, q); st.o = Math.max(st.o, clamp(p * 4, 0, 1));
          st.roll = p < 1 ? 1 - q : 0; break;                       // digits blur while they roll
        case "strike": st.strike = q; break;
        case "scan": st.scan = E.inOut(p); st.o = 1; break;       // a bright line sweeps across and leaves the object behind
        case "highlight": st.hl = q; break;
        case "explode": st.explode = q; break;
        case "collapse": st.explode = 1 - q; break;
        case "pulse": { const k = a.repeat || 1; st.pulse = p < 1 ? Math.sin(Math.PI * ((p * k) % 1)) : 0; break; }
        case "flow": { const k = a.repeat || 1; st.flow = p < 1 ? (p * k) % 1 : -1; break; }
        case "move": st.tx += (a.dx || 0) * E.inOut(p); st.ty += (a.dy || 0) * E.inOut(p); break;
        case "morph": st.o *= 1 - q; st.s *= 1 + (a.scale == null ? 0.12 : a.scale) * q; break;
        case "play": st.play = Math.round(clamp(t - e.t, 0, e.dur) * 1000) / 1000; break;
        default: break;
      }
    }
    return st;
  }

  // ---------- camera: eased moves between framings of objects
  // Everything a viewer must see stays inside the 168-1330 px reel safe zone (references/platform-specs.md).
  // Default "headline" captions sit at the top (270-420 px), pictures below them (450-1300 px); "pill" captions sit
  // at the bottom (1135-1310 px), pictures above them (200-1080 px).
  const VIEW_TOP = { w: 1080, h: 1920, safe: { x: 80, y: 450, w: 920, h: 850 } };
  const VIEW_PILL = { w: 1080, h: 1920, safe: { x: 80, y: 200, w: 920, h: 880 } };
  FR.VIEW = VIEW_TOP;
  FR.viewFor = (scene) => (scene && scene.captions === "pill" ? VIEW_PILL : VIEW_TOP);

  function frame(box, args, view) {
    const pad = args.pad == null ? 60 : args.pad;
    const sw = view.safe.w - 2 * pad, sh = view.safe.h - 2 * pad;
    const s = clamp(Math.min(sw / box.w, sh / box.h) * (args.zoom || 1), args.min || 0.25, args.max || 3);
    return { x: box.x + box.w / 2, y: box.y + box.h / 2, s };
  }

  function worldBox(scene) {
    const w = (scene.world && scene.world.w) || 1080, h = (scene.world && scene.world.h) || 1920;
    return { x: 0, y: 0, w, h };
  }

  // a camera target: "all", one object id, or a list of ids (framed by their union box)
  function boxOf(id, scene, boxes) {
    if (!id || id === "all") return worldBox(scene);
    const ids = Array.isArray(id) ? id : [id];
    const bs = ids.map((k) => boxes[k]).filter(Boolean);
    if (!bs.length) return worldBox(scene);
    const x0 = Math.min(...bs.map((b) => b.x)), y0 = Math.min(...bs.map((b) => b.y));
    const x1 = Math.max(...bs.map((b) => b.x + b.w)), y1 = Math.max(...bs.map((b) => b.y + b.h));
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }

  function cameraAt(t, scene, events, boxes, view) {
    const target = (id, args) => frame(boxOf(id, scene, boxes), args || {}, view);
    // while the camera holds it keeps pushing in slowly (default 1.5% a second, at most 4 s): the frame never sits still
    const push = scene.camera && scene.camera.push != null ? scene.camera.push : 0.015;
    const drift = (c, hold) => ({ x: c.x, y: c.y, s: c.s * (1 + push * clamp(hold, 0, 4)) });
    let cam = target(scene.camera && scene.camera.start, (scene.camera && scene.camera.args) || {});
    let lastEnd = 0, moving = false;
    for (const e of events) {
      if (FR.CAMERA_ACTIONS.indexOf(e.action) < 0) continue;
      if (t < e.t) break;
      const from = moving ? cam : drift(cam, e.t - lastEnd);
      const to = target(e.action === "wide" ? (e.object || "all") : e.object, e.args);
      const raw = clamp((t - e.t) / Math.max(e.dur, 1e-6), 0, 1), p = (E[e.args && e.args.ease] || E.inOut)(raw);
      // zoom in log space so pushes feel even; centre follows the screen-space path
      cam = { x: lerp(from.x, to.x, p), y: lerp(from.y, to.y, p), s: Math.exp(lerp(Math.log(from.s), Math.log(to.s), p)) };
      moving = raw < 1;
      if (!moving) lastEnd = e.t + e.dur;
    }
    return moving ? cam : drift(cam, t - lastEnd);
  }

  // depth of field: while the camera is on a target, every other component goes soft and dims a little
  function sharpSet(e) {
    if (!e || e.action !== "focus") return null;
    return Array.isArray(e.object) ? e.object : [e.object];
  }
  function blurAt(t, scene, camEvents) {
    const out = {};
    if (scene.camera && scene.camera.dof === false) return out;
    const started = camEvents.filter((e) => e.t <= t);
    const cur = started[started.length - 1];
    if (!cur) return out;
    const prev = started[started.length - 2];
    const p = E.inOut(clamp((t - cur.t) / Math.max(cur.dur, 1e-6), 0, 1));
    const amount = (set, id) => (!set || set.some((x) => x === id || x.indexOf(id + ".") === 0 || id.indexOf(x + ".") === 0) ? 0 : 1);
    const a = sharpSet(prev), b = sharpSet(cur);
    for (const c of scene.components || []) out[c.id] = lerp(amount(a, c.id), amount(b, c.id), p);
    return out;
  }

  // theme at t: the last flip that started, as {from, to, p} (renderer mixes the two palettes by p)
  FR.themeAt = function (t, scene, evs) {
    let cur = scene.theme || "light", out = { from: cur, to: cur, p: 1 };
    for (const e of evs) {
      if (e.action !== "theme" || t < e.t) continue;
      const to = (e.args && e.args.to) || (cur === "dark" ? "light" : "dark");
      out = { from: cur, to, p: E.inOut(clamp((t - e.t) / Math.max(e.dur, 1e-6), 0, 1)) };
      cur = to;
    }
    return out;
  };

  FR.stateAt = function (t, scene, events, boxes, view) {
    view = view || FR.viewFor(scene);
    const evs = events.slice().sort((a, b) => a.t - b.t);
    const by = {};
    for (const e of evs) if (FR.CAMERA_ACTIONS.indexOf(e.action) < 0) (by[e.object] = by[e.object] || []).push(e);
    const hidden = FR.hiddenAtStart(scene);
    const obj = {};
    for (const id of FR.parts(scene)) obj[id] = objectState(t, id, by[id] || [], hidden);
    const soft = blurAt(t, scene, evs.filter((e) => FR.CAMERA_ACTIONS.indexOf(e.action) >= 0));
    for (const id in soft) if (obj[id] && soft[id] > 0) { obj[id].blur = 9 * soft[id]; obj[id].o *= 1 - 0.5 * soft[id]; }
    return { camera: cameraAt(t, scene, evs, boxes || {}, view), obj, theme: FR.themeAt(t, scene, evs) };
  };

  // camera {x, y, s} -> CSS transform for the world layer (world point x,y lands at the safe-area centre)
  FR.cameraTransform = function (cam, view) {
    view = view || FR.VIEW;   // renderer passes FR.viewFor(scene)
    const cx = view.safe.x + view.safe.w / 2, cy = view.safe.y + view.safe.h / 2;
    return "translate(" + (cx - cam.x * cam.s).toFixed(2) + "px," + (cy - cam.y * cam.s).toFixed(2) + "px) scale(" +
      cam.s.toFixed(4) + ")";
  };

  // ---------- captions: the same word times as the animations
  FR.captionAt = function (t, groups) {
    for (const g of groups || []) {
      const st = g[0].start - 0.05, en = g[g.length - 1].end + 0.25;
      if (t >= st && t < en) {
        return { words: g.map((w) => ({ text: w.text, key: !!w.key,
                                        state: t < w.start ? "next" : t < w.end ? "now" : "past" })) };
      }
    }
    return null;
  };

  if (typeof module !== "undefined" && module.exports) module.exports = FR;
})(typeof globalThis !== "undefined" ? globalThis : this);
