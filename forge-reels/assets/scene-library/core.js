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
             count: 1.0, grow: 0.7, explode: 0.8, collapse: 0.6, flow: 1.2, move: 0.7, morph: 0.6 };
  FR.ACTIONS = Object.keys(FR.DUR);
  FR.CAMERA_ACTIONS = ["focus", "wide"];

  // ---------- components: their animatable parts (pure). renderer.js draws them.
  const n = (k, count) => Array.from({ length: count }, (_, i) => k + (i + 1));
  FR.COMPONENTS = {
    phone:    { parts: () => ["body", "screen", "ui", "grid", "rows", "cols", "field", "finger", "glass", "notification"],
                hidden: () => ["grid", "field", "finger", "notification"] },
    browser:  { parts: (s) => ["window", "address", "page", "title", "cursor", ...n("tab", (s.tabs || ["Home"]).length),
                               ...n("r", (s.results || []).length)], hidden: () => ["cursor"] },
    terminal: { parts: (s) => ["window", "cursor", ...n("l", (s.lines || []).length)], hidden: () => [] },
    nodes:    { parts: (s) => [...(s.nodes || []).map((x) => "n_" + x.id),
                               ...(s.links || []).map(([a, b]) => "l_" + a + "_" + b)], hidden: () => [] },
    chart:    { parts: (s) => ["title", "axis", ...n("b", (s.bars || []).length), ...n("v", (s.bars || []).length)],
                hidden: () => [] },
    document: { parts: (s) => ["page", "title", "source", ...n("l", (s.lines || []).length)], hidden: () => [] },
    chip:     { parts: (s) => ["chip", "label", "pins", ...n("t", s.traces || 6)], hidden: () => [] },
    stack:    { parts: (s) => n("L", (s.layers || []).length), hidden: () => [] },
    text:     { parts: () => [], hidden: () => [] },
    counter:  { parts: () => ["label"], hidden: () => [] },
    callout:  { parts: () => ["arrow", "label"], hidden: () => [] },
    image:    { parts: () => [], hidden: () => [] },
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
                        explode: 0, flow: -1 });

  function objectState(t, id, evs, hidden) {
    const st = BASE();
    const first = {};
    for (const e of evs) if (!(e.action in first)) first[e.action] = e;
    if (hidden.has(id) || (evs[0] && evs[0].action === "reveal")) st.o = 0;
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
        case "count": st.count = lerp(a.from || 0, a.to, q); break;
        case "highlight": st.hl = q; break;
        case "explode": st.explode = q; break;
        case "collapse": st.explode = 1 - q; break;
        case "pulse": { const k = a.repeat || 1; st.pulse = p < 1 ? Math.sin(Math.PI * ((p * k) % 1)) : 0; break; }
        case "flow": { const k = a.repeat || 1; st.flow = p < 1 ? (p * k) % 1 : -1; break; }
        case "move": st.tx += (a.dx || 0) * E.inOut(p); st.ty += (a.dy || 0) * E.inOut(p); break;
        case "morph": st.o *= 1 - q; st.s *= 1 + (a.scale == null ? 0.12 : a.scale) * q; break;
        default: break;
      }
    }
    return st;
  }

  // ---------- camera: eased moves between framings of objects
  FR.VIEW = { w: 1080, h: 1920, safe: { x: 60, y: 150, w: 960, h: 1230 } };   // area above the captions

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

  function cameraAt(t, scene, events, boxes, view) {
    const target = (id, args) => frame(id && id !== "all" ? boxes[id] : worldBox(scene), args || {}, view);
    const start = scene.camera && scene.camera.start;
    let cam = target(start && boxes[start] ? start : "all", (scene.camera && scene.camera.args) || {});
    for (const e of events) {
      if (FR.CAMERA_ACTIONS.indexOf(e.action) < 0) continue;
      if (t < e.t) break;
      const to = target(e.action === "wide" ? (e.object || "all") : e.object, e.args);
      const p = E.inOut(clamp((t - e.t) / Math.max(e.dur, 1e-6), 0, 1));
      // zoom in log space so pushes feel even; centre follows the screen-space path
      cam = { x: lerp(cam.x, to.x, p), y: lerp(cam.y, to.y, p), s: Math.exp(lerp(Math.log(cam.s), Math.log(to.s), p)) };
    }
    return cam;
  }

  FR.stateAt = function (t, scene, events, boxes, view) {
    view = view || FR.VIEW;
    const evs = events.slice().sort((a, b) => a.t - b.t);
    const by = {};
    for (const e of evs) if (FR.CAMERA_ACTIONS.indexOf(e.action) < 0) (by[e.object] = by[e.object] || []).push(e);
    const hidden = FR.hiddenAtStart(scene);
    const obj = {};
    for (const id of FR.parts(scene)) obj[id] = objectState(t, id, by[id] || [], hidden);
    return { camera: cameraAt(t, scene, evs, boxes || {}, view), obj };
  };

  // camera {x, y, s} -> CSS transform for the world layer (world point x,y lands at the safe-area centre)
  FR.cameraTransform = function (cam, view) {
    view = view || FR.VIEW;
    const cx = view.safe.x + view.safe.w / 2, cy = view.safe.y + view.safe.h / 2;
    return "translate(" + (cx - cam.x * cam.s).toFixed(2) + "px," + (cy - cam.y * cam.s).toFixed(2) + "px) scale(" +
      cam.s.toFixed(4) + ")";
  };

  // ---------- captions: the same word times as the animations
  FR.captionAt = function (t, groups) {
    for (const g of groups || []) {
      const st = g[0].start - 0.05, en = g[g.length - 1].end + 0.25;
      if (t >= st && t < en) {
        return { words: g.map((w) => ({ text: w.text, state: t < w.start ? "next" : t < w.end ? "now" : "past" })) };
      }
    }
    return null;
  };

  if (typeof module !== "undefined" && module.exports) module.exports = FR;
})(typeof globalThis !== "undefined" ? globalThis : this);
