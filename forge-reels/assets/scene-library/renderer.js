/* ForgeReels scene renderer: the BROWSER half of the explainer runtime. Builds the components of scene.json, measures
 * them once, and applies FR.stateAt(t) (core.js) to the DOM on every HyperFrames seek. No network, no GSAP.
 *
 *   const fr = FR.mount(stageEl, window.__FR_DATA);   // {scene, events, captions, duration}
 *   window.addEventListener("hf-seek", (e) => fr.render(e.detail.time));
 */
(function (root) {
  "use strict";
  const FR = root.FR;

  FR.THEMES = {
    light: { bg: "#f4f1ea", ink: "#14161a", "ink-soft": "#2c3038", muted: "#6b7280", card: "#ffffff", screen: "#f6f7f9",
             chrome: "#eef0f3", line: "#e3e6eb", "line-strong": "#c9ced6", edge: "rgba(20,22,26,.06)",
             shadow: "rgba(20,22,26,.28)", dot: "rgba(20,22,26,.10)", vignette: "rgba(120,100,70,.10)",
             accent: "#ff5a1f", "accent-glow": "rgba(255,90,31,.45)", accent2: "#2f6bff", marker: "rgba(255,196,0,.55)",
             "cap-bg": "rgba(16,18,24,.9)", "cap-ink": "#ffffff" },
    dark:  { bg: "#0b0d12", ink: "#f2f4f8", "ink-soft": "#d5dae3", muted: "#8b93a3", card: "#161a22", screen: "#10131a",
             chrome: "#1d222c", line: "#262c38", "line-strong": "#3a4252", edge: "rgba(255,255,255,.05)",
             shadow: "rgba(0,0,0,.6)", dot: "rgba(255,255,255,.07)", vignette: "rgba(0,0,0,.45)",
             accent: "#ff6b35", "accent-glow": "rgba(255,107,53,.5)", accent2: "#4d8bff", marker: "rgba(255,196,0,.35)",
             "cap-bg": "rgba(255,255,255,.95)", "cap-ink": "#0b0d12" },
  };

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const DOTS = '<i class="dot" style="background:#ff5f57"></i><i class="dot" style="background:#febc2e"></i><i class="dot" style="background:#28c840"></i>';
  const COLORS = ["#2f6bff", "#ff5a1f", "#17b26a", "#8b5cf6", "#f59e0b", "#06b6d4"];

  // ---------- builders: spec -> [width, height, innerHTML]; every animatable part carries data-obj="<id>.<part>"
  const B = (FR.BUILD = {});

  B.phone = (c) => {
    const w = c.w || 440, h = Math.round(w * 2.05), id = c.id, touch = c.touch || { x: 0.5, y: 0.56 };
    const items = c.items || ["Messages", "Photos", "Maps", "Music"];
    const rows = items.map((t, i) => `<div class="row"><i style="background:${COLORS[i % COLORS.length]}"></i><div style="flex:1"><b>${esc(t)}</b><s></s></div></div>`).join("");
    const nr = c.rows || 9, nc = c.cols || 5;
    // viewBox follows the screen's own aspect (~100 x 213) so a stroke is equally thick across and down
    const rowsP = Array.from({ length: nr }, (_, i) => `<path pathLength="1" d="M4 ${((i + 1) * 213) / (nr + 1)} H96"/>`).join("");
    const colsP = Array.from({ length: nc }, (_, i) => `<path pathLength="1" d="M${((i + 1) * 100) / (nc + 1)} 4 V209"/>`).join("");
    const at = `left:${touch.x * 100}%;top:${touch.y * 100}%`;
    return [w, h, `
      <div data-obj="${id}.body" class="body"></div>
      <div data-obj="${id}.screen" class="screen">
        <div class="island"></div>
        <div data-obj="${id}.ui" class="ui"><div class="status"><span>9:41</span><span>● ● ▮</span></div><h4>${esc(c.title || "Home")}</h4>${rows}</div>
        <svg data-obj="${id}.grid" class="grid" viewBox="0 0 100 213" preserveAspectRatio="none">
          <g data-obj="${id}.rows" class="rows">${rowsP}</g><g data-obj="${id}.cols" class="cols">${colsP}</g></svg>
        <div data-obj="${id}.field" class="field" style="${at}"></div>
        <div data-obj="${id}.finger" class="finger" style="${at}"></div>
        <div data-obj="${id}.glass" class="glass"></div>
        <div data-obj="${id}.notification" class="notification">${esc(c.notification || "New message")}</div>
      </div>`];
  };

  B.browser = (c) => {
    const w = c.w || 920, h = c.h || 660, id = c.id, tabs = c.tabs || ["Home"];
    const tabH = tabs.map((t, i) => `<span data-obj="${id}.tab${i + 1}" class="tab${i ? " off" : ""}">${esc(t)}</span>`).join("");
    const res = (c.results || []).map((t, i) => `<div data-obj="${id}.r${i + 1}" class="result"><i></i><div style="flex:1"><b>${esc(t)}</b><s></s></div></div>`).join("");
    const cur = c.cursor || { x: 0.7, y: 0.6 };
    return [w, h, `
      <div data-obj="${id}.window" class="window fr-card">
        <div class="bar">${DOTS}${tabH}</div>
        <div data-obj="${id}.address" class="address">🔒 <span data-text="${esc(c.url || "forgereels.dev")}">${esc(c.url || "forgereels.dev")}</span></div>
        <div data-obj="${id}.page" class="page"><div data-obj="${id}.title" class="title"><span data-text="${esc(c.title || "")}">${esc(c.title || "")}</span></div>${res}</div>
      </div>
      <svg data-obj="${id}.cursor" class="cursor" style="left:${cur.x * 100}%;top:${cur.y * 100}%" viewBox="0 0 24 24"><path d="M4 2.5 L4 20 L8.6 15.6 L11.6 22 L14.4 20.8 L11.5 14.6 L18 14.4 Z" fill="#14161a" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>`];
  };

  B.terminal = (c) => {
    const w = c.w || 900, lines = c.lines || [], id = c.id, h = c.h || 120 + lines.length * 47;
    const ls = lines.map((t, i) => {
      const cmd = t.startsWith("$ "), txt = cmd ? t.slice(2) : t, cls = cmd ? "cmd" : t.startsWith("✓") ? "ok" : "";
      return `<div data-obj="${id}.l${i + 1}" class="ln ${cls}"><span data-text="${esc(txt)}">${esc(txt)}</span></div>`;
    }).join("");
    return [w, h, `<div data-obj="${id}.window" class="window"><div class="bar">${DOTS}</div><div class="body">${ls}<span data-obj="${id}.cursor" class="cursor"></span></div></div>`];
  };

  B.nodes = (c) => {
    const w = c.w || 900, h = c.h || 700, id = c.id, nodes = c.nodes || [], at = {};
    nodes.forEach((x) => (at[x.id] = x));
    const links = (c.links || []).map(([a, b]) => {
      const p = at[a], q = at[b], mx = (p.x + q.x) / 2;
      const d = Math.abs(q.x - p.x) > Math.abs(q.y - p.y) ? `M${p.x} ${p.y} C${mx} ${p.y} ${mx} ${q.y} ${q.x} ${q.y}`
        : `M${p.x} ${p.y} C${p.x} ${(p.y + q.y) / 2} ${q.x} ${(p.y + q.y) / 2} ${q.x} ${q.y}`;
      return `<g data-obj="${id}.l_${a}_${b}"><path class="link" pathLength="1" data-flow-path d="${d}"/><circle class="packet" r="11" data-flow-dot/></g>`;
    }).join("");
    const ns = nodes.map((x, i) => `<div data-obj="${id}.n_${x.id}" class="node" style="left:${x.x}px;top:${x.y}px"><i style="background:${x.color || COLORS[i % COLORS.length]}">${esc(x.icon || x.label[0])}</i><div>${esc(x.label)}${x.sub ? `<small>${esc(x.sub)}</small>` : ""}</div></div>`).join("");
    return [w, h, `<svg width="${w}" height="${h}">${links}</svg>${ns}`];
  };

  B.chart = (c) => {
    const w = c.w || 860, h = c.h || 640, id = c.id, bars = c.bars || [], max = c.max || Math.max(...bars.map((b) => b.value), 1);
    const cols = bars.map((b, i) => `<div class="col"><div data-obj="${id}.v${i + 1}" class="val" data-count data-decimals="${b.decimals || 0}" data-prefix="${esc(b.prefix || c.prefix || "")}" data-suffix="${esc(b.suffix || c.suffix || "")}">${esc((c.prefix || "") + b.value + (c.suffix || ""))}</div><div data-obj="${id}.b${i + 1}" class="bar${b.hot ? " hot" : ""}" style="height:${(b.value / max) * 100}%"></div><div class="lab">${esc(b.label || "")}</div></div>`).join("");
    return [w, h, `<div class="fr-card" style="position:absolute;inset:0"></div><div data-obj="${id}.title" class="title" style="position:relative">${esc(c.title || "")}</div><div data-obj="${id}.axis" class="axis"></div><div class="plot">${cols}</div>`, "fr-chart"];
  };

  B.document = (c) => {
    const w = c.w || 820, h = c.h || 760, id = c.id;
    const ls = (c.lines || []).map((t, i) => `<div data-obj="${id}.l${i + 1}" class="ln"><mark>${esc(t)}</mark></div>`).join("");
    return [w, h, `<div data-obj="${id}.page" class="fr-card" style="position:absolute;inset:0"></div><div data-obj="${id}.title" class="title" style="position:relative">${esc(c.title || "")}</div><div style="position:relative">${ls}</div><div data-obj="${id}.source" class="source">↗ ${esc(c.source || "")}</div>`, "fr-document"];
  };

  B.chip = (c) => {
    const w = c.w || 760, h = c.h || 760, id = c.id, n = c.traces || 6, cs = Math.min(w, h) * 0.38;
    const cx = w / 2, cy = h / 2, x0 = cx - cs / 2, y0 = cy - cs / 2;
    const traces = Array.from({ length: n }, (_, i) => {
      const side = i % 4, k = Math.floor(i / 4) + 1, f = k / (Math.ceil(n / 4) + 1);
      const [sx, sy, ex, ey, bx, by] = side === 0 ? [x0 + cs * f, y0, x0 + cs * f, 0, x0 + cs * f - 60, 70]
        : side === 1 ? [x0 + cs, y0 + cs * f, w, y0 + cs * f, w - 70, y0 + cs * f + 60]
        : side === 2 ? [x0 + cs * (1 - f), y0 + cs, x0 + cs * (1 - f), h, x0 + cs * (1 - f) + 60, h - 70]
        : [x0, y0 + cs * (1 - f), 0, y0 + cs * (1 - f), 70, y0 + cs * (1 - f) - 60];
      const mid = side % 2 === 0 ? `L${sx} ${(sy + by) / 2} L${bx} ${by} L${ex === sx ? bx : ex} ${ey}`
        : `L${(sx + bx) / 2} ${sy} L${bx} ${by} L${ex} ${by}`;
      return `<g data-obj="${id}.t${i + 1}"><path class="trace" pathLength="1" data-flow-path d="M${sx} ${sy} ${mid}"/><circle class="packet" r="10" data-flow-dot/></g>`;
    }).join("");
    const pins = Array.from({ length: 24 }, (_, i) => {
      const side = Math.floor(i / 6), k = (i % 6 + 1) / 7, L = 14, T = 8;
      const s = side === 0 ? `left:${x0 + cs * k - T / 2}px;top:${y0 - L}px;width:${T}px;height:${L}px`
        : side === 1 ? `left:${x0 + cs}px;top:${y0 + cs * k - T / 2}px;width:${L}px;height:${T}px`
        : side === 2 ? `left:${x0 + cs * k - T / 2}px;top:${y0 + cs}px;width:${T}px;height:${L}px`
        : `left:${x0 - L}px;top:${y0 + cs * k - T / 2}px;width:${L}px;height:${T}px`;
      return `<i style="${s}"></i>`;
    }).join("");
    return [w, h, `<svg width="${w}" height="${h}">${traces}</svg><div data-obj="${id}.pins" class="pins">${pins}</div><div data-obj="${id}.chip" class="chip" style="left:${x0}px;top:${y0}px;width:${cs}px;height:${cs}px"><span data-obj="${id}.label" class="label">${esc(c.label || "CPU")}</span></div>`];
  };

  B.stack = (c) => {
    const w = c.w || 520, layers = c.layers || [], id = c.id, lh = c.lh || Math.round(w * 0.62), gap = c.gap || 150, step = c.step || 30;
    const h = lh + (layers.length - 1) * step + 200;
    const ls = layers.map((l, i) => {
      const off = (layers.length - 1 - i) * step - (layers.length - 1) * step / 2, eg = (i - (layers.length - 1) / 2) * gap;
      return `<div data-obj="${id}.L${i + 1}" class="layer" style="--off:${off + 100}px;--gap:${eg}px;background:${l.color || COLORS[i % COLORS.length]}"></div>` +
        `<div class="tag" style="--off:${off + 100 + lh * 0.3}px;--gap:${eg}px">${esc(l.label || "")}</div>`;
    }).join("");
    return [w, h, `<div style="--lh:${lh}px;position:absolute;inset:0">${ls}</div>`];
  };

  B.text = (c) => [c.w || 900, c.h || Math.round((c.size || 96) * 1.15 * (c.linesHint || 1)),
    `<div style="font-size:${c.size || 96}px;font-weight:${c.weight || 830};color:${c.color || "var(--ink)"};text-align:${c.align || "left"}"><span data-text="${esc(c.text)}">${esc(c.text)}</span></div>`, "fr-text"];

  B.counter = (c) => [c.w || 700, c.h || 300,
    `<div class="num" data-count data-decimals="${c.decimals || 0}" data-prefix="${esc(c.prefix || "")}" data-suffix="${esc(c.suffix || "")}">${esc((c.prefix || "") + c.value + (c.suffix || ""))}</div><div data-obj="${c.id}.label" class="label">${esc(c.label || "")}</div>`, "fr-counter"];

  B.callout = (c) => {
    const to = c.to || { dx: 0, dy: 160 };
    return [10, 10, `<svg data-obj="${c.id}.arrow" class="arrow" width="10" height="10"><path pathLength="1" d="M0 0 L${to.dx} ${to.dy}"/><circle cx="${to.dx}" cy="${to.dy}" r="9" fill="var(--ink)"/></svg><div data-obj="${c.id}.label" class="label">${esc(c.text)}</div>`, "fr-callout"];
  };

  B.image = (c) => [c.w || 900, c.h || 600, `<img src="${esc(c.src)}" alt="">`, "fr-image" + (c.card === false ? "" : " fr-card")];

  // ---------- mount + render
  FR.mount = function (stage, data) {
    const scene = data.scene, events = data.events || [], theme = Object.assign({}, FR.THEMES[scene.theme || "light"], scene.colors || {});
    stage.classList.add("fr-stage");
    for (const k in theme) stage.style.setProperty("--" + k, theme[k]);
    const world = document.createElement("div");
    world.className = "fr-world";
    const ww = (scene.world && scene.world.w) || 1080, wh = (scene.world && scene.world.h) || 1920;
    world.style.width = ww + "px"; world.style.height = wh + "px";
    world.innerHTML = '<div class="fr-ground"></div>';
    for (const c of scene.components || []) {
      const [w, h, html, extra] = B[c.type](c);
      const el = document.createElement("div");
      el.className = "fr-c fr-" + c.type + (extra ? " " + extra : "");
      el.dataset.obj = c.id;
      Object.assign(el.style, { left: c.x + "px", top: c.y + "px", width: w + "px", height: h + "px" });
      el.style.setProperty("--w", w + "px");
      el.innerHTML = html;
      world.appendChild(el);
    }
    stage.appendChild(world);
    const vig = document.createElement("div"); vig.className = "fr-vignette"; stage.appendChild(vig);
    const cap = document.createElement("div"); cap.className = "fr-captions"; stage.appendChild(cap);

    const els = {}, boxes = {}, flows = {};
    world.querySelectorAll("[data-obj]").forEach((e) => (els[e.dataset.obj] = e));
    function measure() {
      world.style.transform = "none";
      const wr = world.getBoundingClientRect();
      for (const id in els) {
        const r = els[id].getBoundingClientRect();
        boxes[id] = { x: r.left - wr.left, y: r.top - wr.top, w: Math.max(r.width, 1), h: Math.max(r.height, 1) };
        const p = els[id].querySelector("[data-flow-path]");
        if (p) flows[id] = { path: p, dot: els[id].querySelector("[data-flow-dot]"), len: p.getTotalLength() };
      }
    }
    measure();

    const fmt = (el, v) => el.dataset.prefix + Number(v).toLocaleString("en-US", { minimumFractionDigits: +el.dataset.decimals,
      maximumFractionDigits: +el.dataset.decimals }) + el.dataset.suffix;

    function apply(id, s) {
      const el = els[id];
      if (!el) return;
      el.style.opacity = s.o.toFixed(4);
      const sc = s.s * (1 + 0.06 * s.pulse);
      el.style.translate = s.tx || s.ty ? `${s.tx.toFixed(2)}px ${s.ty.toFixed(2)}px` : "";
      el.style.scale = sc !== 1 ? sc.toFixed(4) : "";
      el.style.filter = s.pulse > 0.001 ? `drop-shadow(0 0 ${(30 * s.pulse).toFixed(1)}px var(--accent))` : "";
      el.style.setProperty("--grow", s.grow.toFixed(4));
      el.style.setProperty("--hl", s.hl.toFixed(4));
      el.style.setProperty("--explode", s.explode.toFixed(4));
      // draw: SVG strokes trace in; anything else wipes in from the left
      const paths = el.matches("path[pathLength]") ? [el] : el.querySelectorAll("path[pathLength]");
      if (paths.length) paths.forEach((p) => { p.style.strokeDasharray = "1 1"; p.style.strokeDashoffset = (1 - s.draw).toFixed(4); });
      else el.style.clipPath = s.draw < 1 ? `inset(0 ${((1 - s.draw) * 100).toFixed(2)}% 0 0)` : "";
      el.querySelectorAll(":scope [data-text]").forEach((t) => {
        if (t.closest("[data-obj]") !== el) return;                 // a text belongs to its nearest object
        const full = t.dataset.text;
        t.textContent = s.type >= 1 ? full : full.slice(0, Math.round(full.length * s.type));
      });
      const cnt = el.matches("[data-count]") ? el : el.querySelector(":scope > [data-count]");
      if (cnt && s.count != null) cnt.textContent = fmt(cnt, s.count);
      const f = flows[id];
      if (f && f.dot) {
        if (s.flow < 0) f.dot.style.opacity = 0;
        else { const pt = f.path.getPointAtLength(s.flow * f.len); f.dot.setAttribute("cx", pt.x); f.dot.setAttribute("cy", pt.y); f.dot.style.opacity = 1; }
      }
    }

    let lastCap = "";
    function render(t) {
      const st = FR.stateAt(t, scene, events, boxes);
      world.style.transform = FR.cameraTransform(st.camera);
      for (const id in st.obj) apply(id, st.obj[id]);
      const c = FR.captionAt(t, data.captions);
      const html = c ? '<div class="pill">' + c.words.map((w) => `<span class="${w.state}">${esc(w.text)}</span>`).join("") + "</div>" : "";
      if (html !== lastCap) { cap.innerHTML = html; lastCap = html; }
      return st;
    }
    return { render, measure, boxes, els };
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
