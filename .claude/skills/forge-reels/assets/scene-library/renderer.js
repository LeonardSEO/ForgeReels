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
             "cap-bg": "rgba(16,18,24,.9)", "cap-ink": "#ffffff", "key-bg": "rgba(47,107,255,.10)" },
    dark:  { bg: "#0b0d12", ink: "#f2f4f8", "ink-soft": "#d5dae3", muted: "#8b93a3", card: "#161a22", screen: "#10131a",
             chrome: "#1d222c", line: "#262c38", "line-strong": "#3a4252", edge: "rgba(255,255,255,.05)",
             shadow: "rgba(0,0,0,.6)", dot: "rgba(255,255,255,.07)", vignette: "rgba(0,0,0,.45)",
             accent: "#ff6b35", "accent-glow": "rgba(255,107,53,.5)", accent2: "#4d8bff", marker: "rgba(255,196,0,.35)",
             "cap-bg": "rgba(255,255,255,.95)", "cap-ink": "#0b0d12", "key-bg": "rgba(77,139,255,.16)" },
  };

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const DOTS = '<i class="dot" style="background:#ff5f57"></i><i class="dot" style="background:#febc2e"></i><i class="dot" style="background:#28c840"></i>';
  const COLORS = ["#2f6bff", "#ff5a1f", "#17b26a", "#8b5cf6", "#f59e0b", "#06b6d4"];

  // ---------- builders: spec -> [width, height, innerHTML]; every animatable part carries data-obj="<id>.<part>"
  const B = (FR.BUILD = {});

  B.phone = (c) => {
    const w = c.w || 440, h = Math.round(w * 2.05), id = c.id;
    const items = c.items || ["Messages", "Photos", "Maps", "Music"];
    const rows = items.map((t, i) => `<div class="row"><i style="background:${COLORS[i % COLORS.length]}"></i><div style="flex:1"><b>${esc(t)}</b><s></s></div></div>`).join("");
    const nr = c.rows || 9, nc = c.cols || 5;
    // viewBox follows the screen's own aspect (~100 x 213) so a stroke is equally thick across and down
    const rowsP = Array.from({ length: nr }, (_, i) => `<path pathLength="1" d="M4 ${((i + 1) * 213) / (nr + 1)} H96"/>`).join("");
    const colsP = Array.from({ length: nc }, (_, i) => `<path pathLength="1" d="M${((i + 1) * 100) / (nc + 1)} 4 V209"/>`).join("");
    return [w, h, `
      <i class="btn" style="top:21%"></i><i class="btn" style="top:31%;height:9%"></i>
      <div data-obj="${id}.body" class="body"></div>
      <div data-obj="${id}.screen" class="screen">
        <div class="island"></div>
        <div data-obj="${id}.ui" class="ui"><div class="status"><span>9:41</span><span>● ● ▮</span></div><h4>${esc(c.title || "Home")}</h4>${rows}</div>
        <svg data-obj="${id}.grid" class="grid" viewBox="0 0 100 213" preserveAspectRatio="none">
          <g data-obj="${id}.rows" class="rows">${rowsP}</g><g data-obj="${id}.cols" class="cols">${colsP}</g></svg>
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
    const ns = nodes.map((x, i) => `<div data-obj="${id}.n_${x.id}" class="node" style="left:${x.x}px;top:${x.y}px${c.scale ? `;transform:translate(-50%,-50%) scale(${c.scale})` : ""}"><i style="background:${x.color || COLORS[i % COLORS.length]}">${esc(x.icon || x.label[0])}</i><div>${esc(x.label)}${x.sub ? `<small>${esc(x.sub)}</small>` : ""}</div></div>`).join("");
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

  B.text = (c) => [c.w || 900, c.h || Math.round((c.size || 96) * 1.15 * (c.linesHint || 1)),
    `<div${c.serif ? ' class="serif"' : ""} style="font-size:${c.size || 96}px;font-weight:${c.weight || (c.serif ? 500 : 830)};color:${c.color || "var(--ink)"};text-align:${c.align || "left"}"><span data-text="${esc(c.text)}">${esc(c.text)}</span></div>`, "fr-text"];

  B.counter = (c) => {
    const w = c.w || 700, final = (c.prefix || "") + Number(c.value).toLocaleString("en-US", { minimumFractionDigits: c.decimals || 0,
      maximumFractionDigits: c.decimals || 0 }) + (c.suffix || "");
    const size = Math.min(190, Math.floor(w / (final.length * 0.6)));     // the landed number always fits the width
    return [w, c.h || Math.round(size * 1.6),
    `<div class="num" style="font-size:${size}px" data-count data-decimals="${c.decimals || 0}" data-prefix="${esc(c.prefix || "")}" data-suffix="${esc(c.suffix || "")}">${esc(final)}</div><div data-obj="${c.id}.label" class="label">${esc(c.label || "")}</div>`, "fr-counter"];
  };

  B.callout = (c) => {
    const to = c.to || { dx: 0, dy: 160 };
    return [10, 10, `<svg data-obj="${c.id}.arrow" class="arrow" width="10" height="10"><path pathLength="1" d="M0 0 L${to.dx} ${to.dy}"/><circle cx="${to.dx}" cy="${to.dy}" r="9" fill="var(--ink)"/></svg><div data-obj="${c.id}.label" class="label">${esc(c.text)}</div>`, "fr-callout"];
  };

  B.steps = (c) => {
    const steps = c.steps || [], w = c.w || 920, id = c.id;
    const st = steps.map((l, i) => `<div data-obj="${id}.s${i + 1}" class="step"><i></i><span>${esc(l)}</span></div>`).join("");
    return [w, c.h || 96, `<div class="line"></div>${st}`];
  };

  // a captured image sequence (screen recording of a real product), optionally inside a phone bezel
  B.frames = (c) => {
    const w = c.w || 520, h = c.h || Math.round(w * (c.device === "phone" ? 2.05 : 16 / 9));
    const first = FR.frameSrc(c, 0);
    return [w, h, c.device === "phone"
      ? `<div class="bezel"><img data-frames src="${esc(first)}" alt=""></div>`
      : `<img data-frames src="${esc(first)}" alt="">`, c.device === "phone" ? "phone-frame" : "fr-card"];
  };

  // a coding-agent panel: the folder, a prompt typed into the input, then the steps it took, one per line
  B.agent = (c) => {
    const w = c.w || 900, id = c.id, steps = c.steps || [], h = c.h || 300 + steps.length * 50;
    const st = steps.map((t, i) => `<div data-obj="${id}.s${i + 1}" class="step">${esc(t)}</div>`).join("");
    return [w, h, `<div class="panel fr-card">
      <div class="head">▢ ${esc(c.folder || "forge-reels")}</div>
      <div data-obj="${id}.prompt" class="prompt"><span data-text="${esc(c.prompt || "")}">${esc(c.prompt || "")}</span></div>
      <div class="steps">${st}</div>
      <div data-obj="${id}.input" class="input">+ Write / for commands<span class="model">${esc(c.model || "Claude")}</span></div></div>`];
  };

  // ---------- macro kit: lit, close-up illustrations that fill the frame (light from the top left, rim light, glow)
  const glowDef = (id, sd) => `<filter id="${id}-glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="${sd || 6}" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>`;

  // skin shared by finger and hand: soft blur for shading, a fine grain so it is not plastic
  const skinDefs = (g) => `<filter id="${g}-soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="7"/></filter>
        <filter id="${g}-fine" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.6"/></filter>
        <filter id="${g}-grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="4"/><feColorMatrix values="0 0 0 0 .35  0 0 0 0 .16  0 0 0 0 .1  0 0 0 .55 -.12"/></filter>
        <linearGradient id="${g}-skin" x1="0" x2="1"><stop offset="0" stop-color="#c98d70"/><stop offset=".16" stop-color="#e7b092"/><stop offset=".42" stop-color="#f4cbb0"/><stop offset=".72" stop-color="#e0a384"/><stop offset="1" stop-color="#b87558"/></linearGradient>
        <linearGradient id="${g}-nail" x1="0" y1="0" x2=".25" y2="1"><stop offset="0" stop-color="#f6ddd4"/><stop offset=".5" stop-color="#ecc0b3"/><stop offset=".86" stop-color="#e4ad9f"/><stop offset=".9" stop-color="#f7ece6"/><stop offset="1" stop-color="#f3e4dc"/></linearGradient>
        <radialGradient id="${g}-flush" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#e6735c" stop-opacity=".42"/><stop offset="1" stop-color="#e6735c" stop-opacity="0"/></radialGradient>`;

  // a fingertip pointing down, seen from the nail side: tapered, shaded as a soft cylinder, creased at the joint,
  // nail with fold shadow, lunula and gloss; free charges inside and a contact glow arrive on their words
  B.finger = (c) => {
    const w = c.w || 420, h = Math.round(w * 1.25), id = c.id, g = id + "-f";
    const ions = Array.from({ length: 14 }, (_, i) => {
      const x = 62 + (i * 37) % 78, y = 30 + ((i * 53) % 180), pos = i % 2 === 0;
      return `<g transform="translate(${x} ${y})"><circle r="9" fill="${pos ? "var(--accent)" : "var(--accent2)"}" opacity=".92"/><path d="${pos ? "M-4.5 0H4.5M0 -4.5V4.5" : "M-4.5 0H4.5"}" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></g>`;
    }).join("");
    const body = "M38 -60 C36 30 40 86 42 118 C43 136 40 150 40 172 C40 214 68 242 100 242 C132 242 160 214 160 172 C160 150 157 136 158 118 C160 86 164 30 162 -60 Z";
    const nail = "M70 152 C70 128 130 128 130 152 L132 198 C132 224 68 224 68 198 Z";
    const crease = (y, k) => `<path d="M${48 + k} ${y} Q100 ${y + 12} ${152 - k} ${y}" stroke="#7a3a26" stroke-opacity=".34" stroke-width="1.7" fill="none"/><path d="M${48 + k} ${y + 2.4} Q100 ${y + 14.4} ${152 - k} ${y + 2.4}" stroke="#fff" stroke-opacity=".22" stroke-width="1.4" fill="none"/>`;
    return [w, h, `<svg viewBox="0 0 200 250" width="${w}" height="${h}" style="overflow:visible;transform:rotate(${c.angle || 0}deg);transform-origin:50% 96%">
      <defs>${glowDef(g, 5)}${skinDefs(g)}<clipPath id="${g}-clip"><path d="${body}"/></clipPath><clipPath id="${g}-nc"><path d="${nail}"/></clipPath></defs>
      <ellipse data-obj="${id}.glow" cx="100" cy="244" rx="44" ry="10" fill="var(--accent)" filter="url(#${g}-glow)" opacity=".6"/>
      <g data-obj="${id}.tip"><path d="${body}" fill="url(#${g}-skin)"/>
        <g clip-path="url(#${g}-clip)">
          <ellipse cx="100" cy="206" rx="64" ry="52" fill="url(#${g}-flush)"/>
          <path d="M128 -60 L172 -60 L172 250 L118 250 C150 220 150 120 128 -60 Z" fill="#5e2616" opacity=".42" filter="url(#${g}-soft)"/>
          <path d="M30 -60 H47 V190 C47 216 60 232 74 240 L30 250 Z" fill="#fff" opacity=".2" filter="url(#${g}-soft)"/>
          <path d="M52 232 Q100 262 148 232 L148 262 L52 262 Z" fill="#5e2616" opacity=".5" filter="url(#${g}-soft)"/>
          ${crease(70, 0)}${crease(84, 2)}${crease(97, 5)}
          <path d="${nail}" fill="none" stroke="#6b2f1f" stroke-opacity=".55" stroke-width="7" filter="url(#${g}-fine)"/>
          <path d="${nail}" fill="url(#${g}-nail)"/>
          <g clip-path="url(#${g}-nc)"><ellipse cx="100" cy="134" rx="24" ry="13" fill="#fff" opacity=".34"/>
            <rect x="77" y="146" width="11" height="58" rx="5" fill="#fff" opacity=".42" filter="url(#${g}-fine)"/>
            <path d="M112 150 C122 160 124 190 120 210" stroke="#b9705c" stroke-opacity=".3" stroke-width="9" fill="none" filter="url(#${g}-fine)"/></g>
          <path d="M72 150 C73 133 127 133 128 150" stroke="#fff" stroke-opacity=".5" stroke-width="1.6" fill="none"/>
          <rect x="30" y="-60" width="140" height="310" filter="url(#${g}-grain)" opacity=".5" style="mix-blend-mode:multiply"/>
          <g data-obj="${id}.ions">${ions}</g></g></g></svg>`];
  };

  // a magnified cross-section of a touchscreen: cover glass, sensor electrodes with their fringe field, display pixels,
  // and one charge meter per electrode (full -> drained near the touch)
  B.section = (c) => {
    const w = c.w || 1000, h = c.h || 760, id = c.id, g = id + "-s", n = c.n || 7, tx = (c.touch == null ? 0.5 : c.touch) * w;
    const sp = w / n, xs = Array.from({ length: n }, (_, i) => sp * (i + 0.5)), gy = 230, gb = 330, ey = 350;
    const pads = xs.map((x) => `<rect x="${x - sp * 0.32}" y="${ey}" width="${sp * 0.64}" height="16" rx="6" fill="url(#${g}-pad)"/>`).join("");
    const arcs = xs.slice(1).map((x, i) => [1, 2, 3].map((k) => `<path pathLength="1" d="M${xs[i] + 12} ${ey} C${xs[i] + 12} ${ey - 38 * k} ${x - 12} ${ey - 38 * k} ${x - 12} ${ey}"/>`).join("")).join("");
    const near = xs.filter((x) => Math.abs(x - tx) < sp * 1.6);
    const pull = near.map((x) => [0, 1].map((k) => `<path pathLength="1" d="M${x + (k ? 14 : -14)} ${ey} C${x} ${ey - 120} ${tx + (x - tx) * 0.35} ${gy - 40} ${tx + (x - tx) * 0.2 + (k ? 10 : -10)} ${gy - 70}"/>`).join("")).join("");
    const px = Array.from({ length: Math.ceil(w / 16) }, (_, i) => `<rect x="${i * 16 + 2}" y="430" width="11" height="22" rx="3" fill="${["#ff4d5e", "#3ddc84", "#4d8bff"][i % 3]}"/>`).join("");
    const bar = (x, f) => `<rect x="${x - 16}" y="${600 + 120 * (1 - f)}" width="32" height="${120 * f}" rx="8"/>`;
    const drop = (x) => 1 - 0.62 * Math.exp(-Math.pow((x - tx) / (sp * 1.05), 2));
    const tracks = xs.map((x) => `<rect x="${x - 16}" y="600" width="32" height="120" rx="8"/>`).join("");
    const mono = 'font-family="IBM Plex Mono, Menlo, monospace" font-size="24" font-weight="600" letter-spacing="2"';
    return [w, h, `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="overflow:visible">
      <defs>${glowDef(g, 5)}
        <linearGradient id="${g}-glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe6ff" stop-opacity=".30"/><stop offset=".5" stop-color="#8fb8e8" stop-opacity=".10"/><stop offset="1" stop-color="#cfe6ff" stop-opacity=".22"/></linearGradient>
        <linearGradient id="${g}-band" x1="0" y1="0" x2="1" y2="1"><stop offset=".3" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset=".62" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <linearGradient id="${g}-pad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d9f3ff"/><stop offset="1" stop-color="#3a7bd5"/></linearGradient>
        <linearGradient id="${g}-fade" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
        <radialGradient id="${g}-pool" cx=".5" cy=".42" r=".6"><stop offset="0" stop-color="#4d8bff" stop-opacity=".30"/><stop offset="1" stop-color="#4d8bff" stop-opacity="0"/></radialGradient>
        <mask id="${g}-m"><rect x="0" y="-400" width="${w}" height="${h + 400}" fill="url(#${g}-fade)"/></mask></defs>
      <ellipse cx="${w / 2}" cy="${h * 0.42}" rx="${w * 0.75}" ry="${h * 0.75}" fill="url(#${g}-pool)"/>
      <g mask="url(#${g}-m)">
        <g data-obj="${id}.glass"><rect x="0" y="${gy}" width="${w}" height="${gb - gy}" fill="url(#${g}-glass)"/><rect x="0" y="${gy}" width="${w}" height="${gb - gy}" fill="url(#${g}-band)"/>
          <path d="M0 ${gy} H${w}" stroke="#fff" stroke-opacity=".85" stroke-width="3"/><path d="M0 ${gb} H${w}" stroke="#cfe6ff" stroke-opacity=".35" stroke-width="2"/></g>
        <rect x="0" y="${ey - 8}" width="${w}" height="34" fill="#1a2742"/>
        <g data-obj="${id}.field" fill="none" stroke="#5fd4ff" stroke-width="3" stroke-opacity=".9" filter="url(#${g}-glow)">${arcs}</g>
        <g data-obj="${id}.electrodes" filter="url(#${g}-glow)">${pads}</g>
        <g data-obj="${id}.pull" fill="none" stroke="var(--accent)" stroke-width="4" stroke-linecap="round" filter="url(#${g}-glow)">${pull}</g>
        <rect x="0" y="418" width="${w}" height="46" fill="#121826"/>
        <g data-obj="${id}.pixels" filter="url(#${g}-glow)">${px}</g>
        <rect x="0" y="472" width="${w}" height="26" fill="#1f2635"/><rect x="0" y="504" width="${w}" height="14" fill="#191f2b"/></g>
      <g fill="#1a2030">${tracks}</g>
      <g data-obj="${id}.charge" fill="#5fd4ff" filter="url(#${g}-glow)">${xs.map((x) => bar(x, 1)).join("")}</g>
      <g data-obj="${id}.loss" fill="#5fd4ff" filter="url(#${g}-glow)">${xs.map((x) => bar(x, drop(x))).join("")}</g>
      <g data-obj="${id}.labels" fill="var(--muted)" ${mono}><text x="24" y="${gy - 16}">COVER GLASS</text><text x="24" y="${ey + 52}">SENSOR</text><text x="24" y="545">DISPLAY</text>
        <text x="${w - 24}" y="${h - 4}" text-anchor="end" font-size="20" opacity=".7">${esc(c.note || "not to scale")}</text></g></svg>`];
  };

  // the sensor grid in perspective: glowing rows and columns, a light at every crossing, a scan dot that walks the rows
  B.mesh = (c) => {
    const w = c.w || 1000, h = c.h || 1000, id = c.id, g = id + "-m", nr = c.rows || 8, nc = c.cols || 6;
    const ry = (i) => (h * (i + 1)) / (nr + 1), cx = (j) => (w * (j + 1)) / (nc + 1), hot = c.hot || [4, 3];
    const rows = Array.from({ length: nr }, (_, i) => `<path pathLength="1" d="M20 ${ry(i)} H${w - 20}"/>`).join("");
    const cols = Array.from({ length: nc }, (_, j) => `<path pathLength="1" d="M${cx(j)} 20 V${h - 20}"/>`).join("");
    const nodes = Array.from({ length: nr * nc }, (_, k) => `<circle cx="${cx(k % nc)}" cy="${ry(Math.floor(k / nc))}" r="9"/>`).join("");
    let walk = "";
    for (let i = 0; i < nr; i++) walk += (i ? ` L${i % 2 ? cx(nc - 1) : cx(0)} ${ry(i)}` : `M${cx(0)} ${ry(0)}`) + ` L${i % 2 ? cx(0) : cx(nc - 1)} ${ry(i)}`;
    const hx = cx(hot[1] - 1), hy = ry(hot[0] - 1);
    return [w, h, `<div class="tilt" style="transform:perspective(${c.perspective || 1500}px) rotateX(${c.tilt == null ? 48 : c.tilt}deg)">
      <svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="overflow:visible"><defs>${glowDef(g, 7)}</defs>
      <defs><linearGradient id="${g}-panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d2840"/><stop offset="1" stop-color="#121a2b"/></linearGradient></defs><rect x="0" y="0" width="${w}" height="${h}" rx="40" fill="url(#${g}-panel)" stroke="#3a4a66" stroke-width="3"/>
      <g data-obj="${id}.rows" fill="none" stroke="var(--accent2)" stroke-width="5" filter="url(#${g}-glow)">${rows}</g>
      <g data-obj="${id}.cols" fill="none" stroke="#5fd4ff" stroke-width="5" filter="url(#${g}-glow)">${cols}</g>
      <g data-obj="${id}.nodes" fill="#e9f8ff" filter="url(#${g}-glow)">${nodes}</g>
      <g data-obj="${id}.sweep"><path data-flow-path fill="none" stroke="none" d="${walk}"/><circle data-flow-dot r="20" fill="#fff" filter="url(#${g}-glow)"/></g>
      <g data-obj="${id}.hot" filter="url(#${g}-glow)"><circle cx="${hx}" cy="${hy}" r="34" fill="none" stroke="var(--accent)" stroke-width="7"/><circle cx="${hx}" cy="${hy}" r="15" fill="var(--accent)"/></g>
      </svg></div>`];
  };

  // a stack of lit layers seen from the side (a battery, a display, a chip package): explode on the id spreads them
  B.cutaway = (c) => {
    const w = c.w || 900, id = c.id, g = id + "-c", layers = c.layers || [], gap = c.gap == null ? 10 : c.gap, spread = c.spread || 70;
    let y = 0, defs = glowDef(g, 5), out = "";
    layers.forEach((l, i) => {
      const h = l.h || 90, col = l.color || COLORS[i % COLORS.length], kind = l.kind || "solid";
      defs += `<linearGradient id="${g}-${i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity="${kind === "glass" ? 0.42 : 1}"/><stop offset=".12" stop-color="${col}" stop-opacity="${kind === "glass" ? 0.14 : 0.82}"/><stop offset="1" stop-color="${col}" stop-opacity="${kind === "glass" ? 0.26 : 0.55}"/></linearGradient>`;
      const cells = kind === "pixels" ? Array.from({ length: Math.ceil(w / 16) }, (_, k) => `<rect x="${k * 16 + 2}" y="${y + h * 0.25}" width="11" height="${h * 0.5}" rx="3" fill="${["#ff4d5e", "#3ddc84", "#4d8bff"][k % 3]}"/>`).join("")
        : kind === "pads" ? Array.from({ length: l.n || 7 }, (_, k) => `<rect x="${(w / (l.n || 7)) * (k + 0.18)}" y="${y + h * 0.3}" width="${(w / (l.n || 7)) * 0.64}" height="${h * 0.4}" rx="6" fill="#d9f3ff"/>`).join("")
        : kind === "cells" ? Array.from({ length: l.n || 5 }, (_, k) => `<rect x="${(w / (l.n || 5)) * k + 8}" y="${y + 8}" width="${w / (l.n || 5) - 16}" height="${h - 16}" rx="10" fill="#fff" fill-opacity=".16"/>`).join("") : "";
      out += `<g data-obj="${id}.L${i + 1}" style="translate:0 calc(var(--explode, 0) * ${(i - (layers.length - 1) / 2) * spread}px)">
        <rect x="0" y="${y}" width="${w}" height="${h}" rx="${kind === "glass" ? 4 : 10}" fill="${kind === "pixels" || kind === "pads" ? "#111827" : `url(#${g}-${i})`}"/>
        <path d="M6 ${y + 2} H${w - 6}" stroke="#fff" stroke-opacity="${kind === "glass" ? 0.85 : 0.35}" stroke-width="3" stroke-linecap="round"/>
        ${cells ? `<g filter="url(#${g}-glow)">${cells}</g>` : ""}
        <text x="${w + 26}" y="${y + h / 2 + 9}" fill="var(--ink-soft)" font-family="IBM Plex Mono, Menlo, monospace" font-size="${c.labelSize || 28}" font-weight="600">${esc(l.label || "")}</text></g>`;
      y += h + gap;
    });
    return [w, y - gap, `<svg width="${w}" height="${y - gap}" viewBox="0 0 ${w} ${y - gap}" style="overflow:visible"><defs>${defs}</defs>${out}</svg>`];
  };

  // a hand around a phone: give it the phone's x, y and w and list it AFTER the phone. Seen from the front: four
  // fingertips come round the right edge and throw a shadow on the glass, the thumb lies along the left edge
  B.hand = (c) => {
    const w = c.w || 440, h = Math.round(w * 2.05), id = c.id, g = id + "-h";
    const tip = (y, reach, t) => {
      const x = 100 - reach, e = 108, d = `M${e} ${y - 0.6} C${e + 6} ${y} ${e + 6} ${y + t} ${e} ${y + t + 0.6} C104 ${y + t + 1} 96 ${y + t + 0.6} ${x + t * 0.55} ${y + t} C${x - 2} ${y + t - 1} ${x - 2} ${y + 1} ${x + t * 0.55} ${y} C96 ${y - 0.6} 104 ${y - 1} ${e} ${y - 0.6} Z`;
      return `<path d="${d}" fill="#000" opacity=".38" transform="translate(-4 5)" filter="url(#${g}-fine)"/>
        <path d="${d}" fill="url(#${g}-tip)"/>
        <path d="M${x + 3} ${y + 3} Q${x + 12} ${y + 1.5} ${x + 22} ${y + 3}" stroke="#fff" stroke-opacity=".5" stroke-width="2" stroke-linecap="round" fill="none" filter="url(#${g}-tiny)"/>
        <path d="M101 ${y + 2} Q99 ${y + t / 2} 101 ${y + t - 2}" stroke="#7a3a26" stroke-opacity=".4" stroke-width="1.1" fill="none"/>
        <path d="M${x + 4} ${y + t - 3} Q${x + 14} ${y + t - 1} ${x + 24} ${y + t - 3}" stroke="#5e2616" stroke-opacity=".3" stroke-width="3" fill="none" filter="url(#${g}-tiny)"/>`;
    };
    const palm = "M-36 196 C-42 150 -30 118 -12 102 L8 102 L96 150 C112 156 122 190 116 236 L108 340 L-14 340 C-24 296 -32 246 -36 196 Z";
    const thumb = "M-26 310 C-40 250 -40 176 -28 138 C-22 124 -16 118 -10 112 C-2 100 12 98 17 107 C22 116 16 127 9 138 C0 152 -4 200 10 310 Z";
    return [w, h, `<svg viewBox="0 0 100 205" width="${w}" height="${h}" style="overflow:visible">
      <defs>${skinDefs(g)}<filter id="${g}-tiny" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation=".7"/></filter>
        <linearGradient id="${g}-tip" x1="0" y1="0" x2="1" y2=".35"><stop offset="0" stop-color="#f6cfb5"/><stop offset=".5" stop-color="#e3a787"/><stop offset=".78" stop-color="#a9664a"/><stop offset="1" stop-color="#5e2f20"/></linearGradient>
        <linearGradient id="${g}-p" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#eebb9d"/><stop offset=".6" stop-color="#d79a7b"/><stop offset="1" stop-color="#9c5a42"/></linearGradient>
        <clipPath id="${g}-out"><path clip-rule="evenodd" d="M-120 -40 H230 V380 H-120 Z M16 0 H84 A16 16 0 0 1 100 16 V189 A16 16 0 0 1 84 205 H16 A16 16 0 0 1 0 189 V16 A16 16 0 0 1 16 0 Z"/></clipPath>
        <clipPath id="${g}-th"><path d="${thumb}"/></clipPath><clipPath id="${g}-pc"><path d="${palm}"/></clipPath></defs>
      <g data-obj="${id}.palm" clip-path="url(#${g}-out)">
        <path d="${palm}" fill="url(#${g}-p)"/><g clip-path="url(#${g}-pc)">
        <path d="M60 212 L130 212 L120 340 L40 340 Z" fill="#5e2616" opacity=".4" filter="url(#${g}-soft)"/>
        <path d="M2 198 H100 V218 H2 Z" fill="#000" opacity=".5" filter="url(#${g}-soft)"/>
        <path d="M-30 250 Q20 236 70 262" stroke="#7a3a26" stroke-opacity=".28" stroke-width="1.6" fill="none" filter="url(#${g}-tiny)"/>
        <path d="M-14 300 Q40 292 104 304" stroke="#7a3a26" stroke-opacity=".25" stroke-width="1.4" fill="none" filter="url(#${g}-tiny)"/>
        <rect x="-60" y="90" width="200" height="250" filter="url(#${g}-grain)" opacity=".45" style="mix-blend-mode:multiply"/></g></g>
      <g data-obj="${id}.fingers">${tip(62, 15, 21)}${tip(86, 18, 22)}${tip(111, 16, 21)}${tip(135, 11, 18)}</g>
      <g data-obj="${id}.thumb"><path d="${thumb}" fill="#000" opacity=".35" transform="translate(5 4)" filter="url(#${g}-fine)"/><path d="${thumb}" fill="url(#${g}-p)"/>
        <g clip-path="url(#${g}-th)"><path d="M-6 96 L24 96 L24 214 L-2 214 C-4 176 0 150 10 134 Z" fill="#5e2616" opacity=".32" filter="url(#${g}-fine)"/>
          <path d="M-36 214 C-40 176 -30 140 -12 114" stroke="#fff" stroke-opacity=".4" stroke-width="5" fill="none" filter="url(#${g}-fine)"/>
          <path d="M-12 140 Q-2 146 6 142" stroke="#7a3a26" stroke-opacity=".4" stroke-width="1.2" fill="none"/><path d="M-13 146 Q-3 152 5 148" stroke="#7a3a26" stroke-opacity=".3" stroke-width="1.1" fill="none"/>
          <path d="M-2 108 C2 101 12 101 14 108 C16 116 10 126 4 130 C-2 126 -5 116 -2 108 Z" fill="url(#${g}-nail)" stroke="#6b2f1f" stroke-opacity=".35" stroke-width=".8"/>
          <path d="M1 109 C4 105 9 105 11 108" stroke="#fff" stroke-opacity=".7" stroke-width="1.3" fill="none" stroke-linecap="round"/>
          <rect x="-50" y="90" width="80" height="130" filter="url(#${g}-grain)" opacity=".45" style="mix-blend-mode:multiply"/></g></g></svg>`];
  };

  // an illustration drawn for this topic: the SVG file (scene: src, parts[]) is inlined by visual_plan.py as c.svg
  B.svg = (c) => {
    let svg = String(c.svg || "<svg></svg>").replace(/<\?xml[^>]*\?>|<!DOCTYPE[^>]*>/g, "");
    for (const part of c.parts || []) svg = svg.replace(new RegExp(`\\bid="${part}"`), `data-obj="${c.id}.${part}"`);
    return [c.w || 900, c.h || 900, svg];
  };

  // ---------- live components: FR.LIVE[type](el, c, els) returns draw(t, obj), called on every frame after the states
  const L = (FR.LIVE = {});

  // hundreds of dots that hold one shape and move to another (explode on the id): agents, requests, air, charge
  B.swarm = (c) => [c.w || 900, c.h || 900, `<canvas width="${c.w || 900}" height="${c.h || 900}"></canvas><div data-obj="${c.id}.label" class="label">${esc(c.label || "")}</div>`];
  L.swarm = (el, c) => {
    const cv = el.querySelector("canvas"), g = cv.getContext("2d"), n = c.count || 300, from = c.from || "cloud", to = c.to || "grid";
    const A = FR.swarmLayout(from, n, 11), Z = FR.swarmLayout(to, n, 23), cols = c.colors || ["#5fd4ff"], r = c.r || 7;
    const wrap = (v) => ((v % 1) + 1) % 1;
    return (t, obj) => {
      const k = obj[c.id].explode;
      g.clearRect(0, 0, cv.width, cv.height);
      for (let i = 0; i < n; i++) {
        const q = FR.ease.inOut(Math.max(0, Math.min(1, k * 1.5 - 0.5 * i / n)));
        const ax = from === "stream" ? wrap(A[i][0] + t * 0.09) : A[i][0], zx = to === "stream" ? wrap(Z[i][0] + t * 0.09) : Z[i][0];
        const x = ax + (zx - ax) * q + 0.006 * Math.sin(t * 1.3 + i * 1.7), y = A[i][1] + (Z[i][1] - A[i][1]) * q + 0.006 * Math.cos(t * 1.1 + i * 2.3);
        g.globalAlpha = 0.5 + 0.5 * ((i * 37) % 10) / 10; g.fillStyle = cols[i % cols.length];
        g.beginPath(); g.arc(x * cv.width, y * cv.height, r * (0.7 + 0.6 * ((i * 13) % 7) / 7), 0, 6.2832); g.fill();
      }
      g.globalAlpha = 1;
    };
  };

  // travelling waves: grow sets a wave's height, explode flips it upside down, "sum" shows what they add up to
  B.wave = (c) => {
    const w = c.w || 900, h = c.h || 420, ws = c.waves || [{}];
    const one = (key, cls, col) => `<svg data-obj="${c.id}.${key}" class="${cls}" viewBox="0 0 ${w} ${h}" style="--c:${col}"><path d=""/></svg>`;
    return [w, h, '<div class="mid"></div>' + ws.map((x, i) => one("w" + (i + 1), "w", x.color || ["#ffb020", "#5fd4ff", "#ff5a7a"][i % 3])).join("") + one("sum", "w sum", c.sumColor || "#ffffff")];
  };
  L.wave = (el, c, els) => {
    const w = c.w || 900, h = c.h || 420, ws = c.waves || [{}], N = 96, sp = c.speed == null ? 2.4 : c.speed;
    const paths = ws.map((_, i) => els[c.id + ".w" + (i + 1)].querySelector("path")), sum = els[c.id + ".sum"].querySelector("path");
    return (t, obj) => {
      const amp = ws.map((x, i) => { const s = obj[c.id + ".w" + (i + 1)]; return (x.amp == null ? 0.3 : x.amp) * h * s.grow * (1 - 2 * s.explode); });
      const y = (i, u) => amp[i] * Math.sin(6.2832 * ((ws[i].freq || 2) * u + (ws[i].phase || 0)) - t * sp);
      const d = (f) => { let o = ""; for (let k = 0; k <= N; k++) o += (k ? "L" : "M") + ((k / N) * w).toFixed(1) + " " + (h / 2 - f(k / N)).toFixed(1); return o; };
      paths.forEach((pth, i) => pth.setAttribute("d", d((u) => y(i, u))));
      sum.setAttribute("d", d((u) => ws.reduce((a, _, i) => a + y(i, u), 0)));
    };
  };

  // a slowly turning 3D map of points in clusters (embeddings, measurements); explode on the id presses it flat
  B.space = (c) => {
    const w = c.w || 900, h = c.h || 900, id = c.id, cl = c.clusters || [];
    const gs = cl.map((k, i) => `<g data-obj="${id}.c${i + 1}" fill="${k.color || COLORS[i % COLORS.length]}">${"<circle/>".repeat(k.n || 24)}<text>${esc(k.label || "")}</text></g>`).join("");
    return [w, h, `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" style="overflow:visible"><defs>${glowDef(id + "-sp", 5)}</defs>
      <g data-obj="${id}.axes" class="axes"><path pathLength="1" d=""/><path pathLength="1" d=""/><path pathLength="1" d=""/></g>
      <g filter="url(#${id}-sp-glow)">${gs}</g>
      <g data-obj="${id}.arrow" class="arrow" filter="url(#${id}-sp-glow)"><path pathLength="1" d=""/><circle r="13"/></g></svg>`];
  };
  L.space = (el, c, els) => {
    const w = c.w || 900, h = c.h || 900, cl = c.clusters || [], R = Math.min(w, h) * 0.4, rnd = FR.rng(c.seed || 5);
    const gauss = () => Math.sqrt(-2 * Math.log(1 - rnd() * 0.999)) * Math.cos(6.2832 * rnd());
    const pts = cl.map((k) => Array.from({ length: k.n || 24 }, () => (k.at || [0, 0, 0]).map((v) => v + (k.spread || 0.16) * gauss())));
    const groups = cl.map((_, i) => els[c.id + ".c" + (i + 1)]), ax = el.querySelectorAll(".axes path");
    const ar = el.querySelector(".arrow path"), tip = el.querySelector(".arrow circle"), pair = c.arrow || [1, 2];
    return (t, obj) => {
      const yaw = (c.yaw == null ? 0.6 : c.yaw) + t * (c.spin == null ? 0.14 : c.spin), flat = 1 - obj[c.id].explode;
      const at = (q) => { const o = FR.project([q[0], q[1] * flat, q[2]], yaw, c.pitch == null ? 0.38 : c.pitch); return [w / 2 + o.x * R, h / 2 + o.y * R, o.z]; };
      groups.forEach((gEl, i) => {
        const cs = gEl.querySelectorAll("circle");
        pts[i].forEach((q, k) => { const o = at(q); cs[k].setAttribute("cx", o[0].toFixed(1)); cs[k].setAttribute("cy", o[1].toFixed(1)); cs[k].setAttribute("r", (9 - 3.5 * o[2]).toFixed(1)); });
        const o = at(cl[i].at || [0, 0, 0]), tx = gEl.querySelector("text");
        tx.setAttribute("x", o[0].toFixed(1)); tx.setAttribute("y", (o[1] - R * 0.2).toFixed(1));
      });
      [[1, 0, 0], [0, 1, 0], [0, 0, 1]].forEach((v, i) => { const a = at(v.map((x) => -x)), b = at(v); ax[i].setAttribute("d", `M${a[0].toFixed(1)} ${a[1].toFixed(1)} L${b[0].toFixed(1)} ${b[1].toFixed(1)}`); });
      if (cl[pair[0] - 1] && cl[pair[1] - 1]) {
        const a = at(cl[pair[0] - 1].at), b = at(cl[pair[1] - 1].at);
        ar.setAttribute("d", `M${a[0].toFixed(1)} ${a[1].toFixed(1)} L${b[0].toFixed(1)} ${b[1].toFixed(1)}`); tip.setAttribute("cx", b[0].toFixed(1)); tip.setAttribute("cy", b[1].toFixed(1));
      }
    };
  };

  // the world as a dot grid (equirectangular): points by lon/lat with a label, routes as arcs a packet can fly along
  const LAND = [[75, [[-120, -80], [-60, -20], [80, 110]]], [70, [[-165, -140], [-130, -80], [-55, -22], [20, 180]]],
    [65, [[-168, -65], [-52, -38], [-24, -14], [12, 180]]], [60, [[-165, -140], [-135, -95], [-78, -64], [-48, -42], [5, 165]]],
    [55, [[-130, -60], [-7, 0], [8, 140], [156, 162]]], [50, [[-126, -56], [-5, 2], [4, 140], [142, 143]]],
    [45, [[-124, -62], [-1, 135], [141, 145]]], [40, [[-124, -74], [-9, 0], [9, 17], [20, 125], [126, 129], [139, 141]]],
    [35, [[-120, -76], [-6, 10], [36, 120], [133, 140]]], [30, [[-115, -82], [-10, 33], [34, 121]]],
    [25, [[-110, -98], [-82, -80], [-15, 35], [37, 90], [98, 120]]], [20, [[-105, -97], [-90, -87], [-80, -75], [-17, 37], [40, 55], [72, 87], [93, 108]]],
    [15, [[-92, -84], [-17, 40], [43, 50], [74, 80], [98, 108], [120, 124]]], [10, [[-85, -83], [-72, -62], [-14, 50], [76, 79], [99, 106], [123, 126]]],
    [5, [[-77, -52], [-10, 47], [97, 103], [110, 118]]], [0, [[-80, -50], [9, 43], [99, 104], [109, 117], [120, 123]]],
    [-5, [[-80, -36], [12, 40], [104, 114], [120, 122], [132, 150]]], [-10, [[-78, -36], [13, 40], [142, 150]]],
    [-15, [[-76, -39], [12, 40], [47, 50], [125, 145]]], [-20, [[-70, -40], [13, 36], [44, 49], [118, 148]]],
    [-25, [[-70, -48], [15, 35], [44, 47], [114, 153]]], [-30, [[-71, -50], [17, 31], [115, 153]]],
    [-35, [[-72, -57], [19, 25], [117, 123], [136, 150]]], [-40, [[-73, -62], [145, 148], [173, 177]]],
    [-45, [[-74, -66], [168, 172]]], [-50, [[-74, -68]]], [-55, [[-70, -66]]]];
  B.map = (c) => {
    const w = c.w || 1000, h = Math.round(w * 0.5), id = c.id, at = {}, X = (lon) => ((lon + 180) / 360) * w, Y = (lat) => ((85 - lat) / 150) * h;
    (c.points || []).forEach((q) => (at[q.id] = q));
    const routes = (c.routes || []).map(([a, b]) => {
      const p = at[a], q = at[b], x1 = X(p.lon), y1 = Y(p.lat), x2 = X(q.lon), y2 = Y(q.lat), lift = Math.hypot(x2 - x1, y2 - y1) * 0.32;
      return `<g data-obj="${id}.r_${a}_${b}"><path class="route" pathLength="1" data-flow-path d="M${x1} ${y1} Q${(x1 + x2) / 2} ${(y1 + y2) / 2 - lift} ${x2} ${y2}"/><circle class="packet" r="10" data-flow-dot/></g>`;
    }).join("");
    const pts = (c.points || []).map((q) => `<g data-obj="${id}.p_${q.id}" transform="translate(${X(q.lon)} ${Y(q.lat)})"><circle class="halo" r="24"/><circle class="dot" r="9"/><text y="-34" text-anchor="middle">${esc(q.label || "")}</text></g>`).join("");
    return [w, h, `<canvas data-obj="${id}.land" width="${w}" height="${h}"></canvas><svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" style="overflow:visible"><defs>${glowDef(id + "-mp", 5)}</defs><g filter="url(#${id}-mp-glow)">${routes}${pts}</g></svg>`];
  };
  L.map = (el, c) => {
    const cv = el.querySelector("canvas"), g = cv.getContext("2d"), w = cv.width, h = cv.height, step = 2.5;
    g.fillStyle = c.land || "#6f8fc4";
    for (const [lat, runs] of LAND) for (const dl of [0, -2.5]) for (const [a, b] of runs) for (let lon = a; lon <= b; lon += step) {
      g.globalAlpha = 0.8; g.beginPath(); g.arc(((lon + 180) / 360) * w, ((85 - (lat + dl)) / 150) * h, w / 400, 0, 6.2832); g.fill();
    }
    return () => {};
  };

  // ---------- a Mac: an app window with the three window buttons, and a laptop that can show one
  const winBody = (id, c, key) => {
    const side = c.sidebar || [], lines = c.lines || [];
    const sb = side.length ? `<div class="side">${side.map((t, i) => `<div class="it${i === (c.active || 1) - 1 ? " on" : ""}">${esc(t)}</div>`).join("")}</div>` : "";
    return `<div data-obj="${id}.${key}" class="frame"><div class="bar">${DOTS}<span class="t">${esc(c.title || "")}</span></div><div class="main">${sb}<div class="body">${
      lines.map((t, i) => `<div data-obj="${id}.l${i + 1}" class="ln"><span data-text="${esc(t)}">${esc(t)}</span></div>`).join("")}</div></div></div>`;
  };
  B.window = (c) => {
    const w = c.w || 900, rows = Math.max((c.lines || []).length, (c.sidebar || []).length);
    return [w, c.h || Math.round(w * (0.105 + rows * 0.062)), winBody(c.id, c, "frame"), "fr-win"];
  };
  B.macbook = (c) => {
    const w = c.w || 940, id = c.id, app = c.title || (c.lines || []).length;
    return [w, Math.round(w * 0.665), `<div data-obj="${id}.lid" class="lid"><div data-obj="${id}.screen" class="screen">
        <div class="menubar"><b></b><span class="app">${esc(c.app || "Finder")}</span><span>File</span><span>Edit</span><span>View</span><i>${esc(c.clock || "9:41")}</i></div><div class="notch"></div>
        ${app ? `<div class="fr-win slot">${winBody(id, c, "app")}</div>` : ""}</div></div>
      <div data-obj="${id}.base" class="base"><i></i></div>`];
  };

  // ---------- numbers, data and UI
  // a chapter bar pinned to the screen (not the world): highlight on sN marks that chapter reached
  B.hud = (c) => [c.w || 900, c.h || 60, (c.steps || []).map((l, i) => `<div data-obj="${c.id}.s${i + 1}" class="st"><i></i><span>${esc(l)}</span></div>`).join("")];

  // a ring that fills (grow on "ring") around a number that counts (count on the id)
  B.gauge = (c) => {
    const w = c.w || 560, final = (c.prefix || "") + Number(c.value).toLocaleString("en-US", { minimumFractionDigits: c.decimals || 0, maximumFractionDigits: c.decimals || 0 }) + (c.suffix || "");
    return [w, w, `<svg viewBox="0 0 200 200"><circle class="track" cx="100" cy="100" r="86"/><circle data-obj="${c.id}.ring" class="ring" cx="100" cy="100" r="86" pathLength="1" style="--fill:${c.fill == null ? 0.75 : c.fill}"/></svg>
      <div class="num" style="font-size:${Math.min(w * 0.24, Math.floor((w * 0.7) / (final.length * 0.6)))}px" data-count data-decimals="${c.decimals || 0}" data-prefix="${esc(c.prefix || "")}" data-suffix="${esc(c.suffix || "")}">${esc(final)}</div>
      <div data-obj="${c.id}.label" class="label">${esc(c.label || "")}</div>`];
  };

  // a grid of cells with some of them marked (tests failed, dies on a wafer, pixels on): reveal "marked" on its word
  B.waffle = (c) => {
    const w = c.w || 800, rows = c.rows || 10, cols = c.cols || 10, id = c.id, s = w / cols, total = rows * cols;
    const order = Array.from({ length: total }, (_, i) => i).sort((a, b) => ((a * 7919 + 13) % 104729) - ((b * 7919 + 13) % 104729));
    const marked = Array.isArray(c.marked) ? c.marked.map((k) => k - 1) : order.slice(0, c.marked || 0);
    const cell = (i, cls) => `<rect class="${cls}" x="${(i % cols) * s + s * 0.1}" y="${Math.floor(i / cols) * s + s * 0.1}" width="${s * 0.8}" height="${s * 0.8}" rx="${s * 0.16}"/>`;
    return [w, rows * s + 70, `<svg viewBox="0 0 ${w} ${rows * s}" width="${w}" height="${rows * s}" style="overflow:visible"><defs>${glowDef(id + "-wf", 4)}</defs>
      <g data-obj="${id}.cells">${order.map((i) => cell(i, "cell")).join("")}</g><g data-obj="${id}.marked" filter="url(#${id}-wf-glow)">${marked.map((i) => cell(i, "on")).join("")}</g></svg>
      <div data-obj="${id}.label" class="label">${esc(c.label || "")}</div>`];
  };

  // source code; a line starting "+ " is added, "- " removed; "stamp" lands a verdict across it
  B.code = (c) => {
    const w = c.w || 900, lines = c.lines || [], id = c.id, h = c.h || 110 + lines.length * 46;
    const ls = lines.map((t, i) => {
      const cls = t.startsWith("+ ") ? "add" : t.startsWith("- ") ? "del" : "";
      return `<div data-obj="${id}.l${i + 1}" class="ln ${cls}"><b>${cls ? esc(t[0]) : i + 1}</b><span data-text="${esc(cls ? t.slice(2) : t)}">${esc(cls ? t.slice(2) : t)}</span></div>`;
    }).join("");
    return [w, h, `<div data-obj="${id}.window" class="window"><div class="bar">${DOTS}<span>${esc(c.file || "")}</span></div><div class="body">${ls}</div></div><div data-obj="${id}.stamp" class="stamp">${esc(c.stamp || "REVIEW")}</div>`];
  };

  // our own call-to-action card (no platform branding): highlight "follow" presses it, type "comment" writes the keyword
  B.social = (c) => {
    const w = c.w || 820, id = c.id, name = c.name || "ForgeReels";
    return [w, c.h || 330, `<div data-obj="${id}.card" class="card fr-card"></div>
      <div class="who"><i>${esc(name[0])}</i><div><b>${esc(name)}</b><small>${esc(c.handle || "")}</small></div><span data-obj="${id}.follow" class="follow">${esc(c.button || "Follow")}</span></div>
      <div data-obj="${id}.comment" class="comment"><span data-text="${esc(c.keyword || "")}">${esc(c.keyword || "")}</span></div>`];
  };

  // a month: reveal "mark" to ring the days that matter
  B.calendar = (c) => {
    const w = c.w || 640, id = c.id, days = c.days || 31, start = c.start || 0, s = (w - 60) / 7, rows = Math.ceil((start + days) / 7);
    const pos = (d) => [30 + ((start + d - 1) % 7) * s, 150 + Math.floor((start + d - 1) / 7) * s];
    const cells = Array.from({ length: days }, (_, k) => { const [x, y] = pos(k + 1); return `<span style="left:${x}px;top:${y}px;width:${s}px;height:${s}px;line-height:${s}px">${k + 1}</span>`; }).join("");
    const rings = (c.mark || []).map((d) => { const [x, y] = pos(d); return `<i style="left:${x + s * 0.1}px;top:${y + s * 0.1}px;width:${s * 0.8}px;height:${s * 0.8}px"></i>`; }).join("");
    return [w, 180 + rows * s, `<div data-obj="${id}.page" class="page fr-card"><div class="head">${esc(c.title || "")}</div><div class="wd">${["M", "T", "W", "T", "F", "S", "S"].map((d) => `<b style="width:${s}px">${d}</b>`).join("")}</div>${cells}</div><div data-obj="${id}.mark" class="mark">${rings}</div>`];
  };

  // a real brand logo on an app-icon tile (file fetched by scripts/logo.py; visual_plan.py inlines it as c.data)
  B.logo = (c) => {
    const w = c.w || 300, id = c.id;
    return [w, w + (c.label ? 70 : 0), `<div data-obj="${id}.tile" class="tile" style="height:${w}px;${c.tile ? `background:${c.tile}` : ""}"></div>
      <img data-obj="${id}.mark" class="mark" style="height:${w}px" src="${esc(c.data || c.src || "")}" alt="">
      <div data-obj="${id}.label" class="label">${esc(c.label || "")}</div>`];
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
    const pinned = [];
    for (const c of scene.components || []) {
      const [w, h, html, extra] = B[c.type](c);
      const el = document.createElement("div");
      el.className = "fr-c fr-" + c.type + (extra ? " " + extra : "");
      el.dataset.obj = c.id;
      Object.assign(el.style, { left: (c.x == null ? 90 : c.x) + "px", top: (c.y == null ? 176 : c.y) + "px", width: w + "px", height: h + "px" });
      el.style.setProperty("--w", w + "px");
      el.innerHTML = html;
      if (c.pinned || c.type === "hud") { el.classList.add("fr-pinned"); pinned.push(el); } else world.appendChild(el);
    }
    stage.appendChild(world);
    pinned.forEach((el) => stage.appendChild(el));           // screen space: above the world, under the captions
    // ambient particles behind everything: the frame never sits still (scene.ambient: "none" switches them off)
    const amb = scene.ambient === "none" ? null : document.createElement("canvas");
    if (amb) { amb.width = 1080; amb.height = 1920; amb.className = "fr-ambient"; stage.insertBefore(amb, world); }
    const vig = document.createElement("div"); vig.className = "fr-vignette"; stage.appendChild(vig);
    const headline = scene.captions !== "pill";
    const cap = document.createElement("div"); cap.className = "fr-captions " + (headline ? "headline" : "pill-style");
    stage.appendChild(cap);
    const view = FR.viewFor(scene);

    const els = {}, boxes = {}, flows = {};
    stage.querySelectorAll("[data-obj]").forEach((e) => (els[e.dataset.obj] = e));
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
      const fx = [];
      if (s.blur > 0.05) fx.push(`blur(${s.blur.toFixed(2)}px)`);
      if (s.pulse > 0.001) fx.push(`drop-shadow(0 0 ${(30 * s.pulse).toFixed(1)}px var(--accent))`);
      el.style.filter = fx.join(" ");
      el.style.setProperty("--grow", s.grow.toFixed(4));
      el.style.setProperty("--hl", s.hl.toFixed(4));
      el.style.setProperty("--explode", s.explode.toFixed(4));
      el.style.setProperty("--draw", s.draw.toFixed(4));
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
      if (cnt && s.count != null) {
        // odometer: digits that already show their final value are sharp, the ones still rolling are blurred
        const finalText = cnt.dataset.final || (cnt.dataset.final = cnt.textContent), now = fmt(cnt, s.count);
        cnt.innerHTML = s.roll > 0.02 ? FR.odometer(now, finalText).map((d) =>
          d.settled ? esc(d.ch) : `<span class="roll">${esc(d.ch)}</span>`).join("") : esc(now);
      }
      el.style.setProperty("--scan", s.scan.toFixed(4));
      el.classList.toggle("fr-scanning", s.scan > 0 && s.scan < 1);
      if (s.scan < 1) el.style.clipPath = `inset(0 ${((1 - s.scan) * 100).toFixed(2)}% 0 0)`;
      el.style.setProperty("--strike", s.strike.toFixed(4));
      el.classList.toggle("fr-struck", s.strike > 0);          // off again when seeking back
      const f = flows[id];
      if (f && f.dot) {
        if (s.flow < 0) f.dot.style.opacity = 0;
        else { const pt = f.path.getPointAtLength(s.flow * f.len); f.dot.setAttribute("cx", pt.x); f.dot.setAttribute("cy", pt.y); f.dot.style.opacity = 1; }
      }
    }

    const live = (scene.components || []).filter((c) => FR.LIVE[c.type]).map((c) => FR.LIVE[c.type](els[c.id], c, els));
    const seqs = (scene.components || []).filter((c) => c.type === "frames")
      .map((c) => ({ c, img: els[c.id].querySelector("[data-frames]"), shown: -1 }));

    // theme flips: every colour token is a mix of the two palettes (scene.colors overrides apply to both)
    const palette = (name) => Object.assign({}, FR.THEMES[name] || FR.THEMES.light, scene.colors || {});
    let lastTheme = "";
    function applyTheme(th) {
      const key = th.from + th.to + th.p.toFixed(3);
      if (key === lastTheme) return;
      lastTheme = key;
      const a = palette(th.from), b = palette(th.to), pc = (th.p * 100).toFixed(1);
      for (const k in b) stage.style.setProperty("--" + k, th.p >= 1 || a[k] === b[k] ? b[k] :
        `color-mix(in srgb, ${a[k] || b[k]}, ${b[k]} ${pc}%)`);
      theme.particle = b.particle || b.accent;
    }

    let lastCap = "";
    function render(t) {
      const st = FR.stateAt(t, scene, events, boxes, view);
      applyTheme(st.theme);
      if (amb) {
        const g = amb.getContext("2d"); g.clearRect(0, 0, 1080, 1920);
        g.fillStyle = theme.particle || theme.accent;
        // parallax: bigger (nearer) particles slide further against camera moves, so depth reads in every move
        const cam = st.camera, wrap = (v, m) => ((v % m) + m) % m;
        for (const q of FR.particles(t, scene.particles || 70, 7)) {
          const d = (q.r - 1) / 2.5 * 0.18;
          g.globalAlpha = q.a * 0.55; g.beginPath();
          g.arc(wrap(q.x * 1080 - cam.x * cam.s * d, 1080), wrap(q.y * 1920 - cam.y * cam.s * d, 1920), q.r, 0, 6.2832); g.fill();
        }
        g.globalAlpha = 1;
      }
      world.style.transform = FR.cameraTransform(st.camera, view);
      for (const id in st.obj) apply(id, st.obj[id]);
      for (const draw of live) draw(t, st.obj);
      const c = FR.captionAt(t, data.captions);
      // headline: words appear as they are spoken; the word that triggers an animation gets the selection box
      const html = c ? '<div class="pill">' + c.words.map((w) => `<span class="${w.state}${w.key ? " key" : ""}">${esc(w.text)}</span>`).join("") + "</div>" : "";
      if (html !== lastCap) { cap.innerHTML = html; lastCap = html; }
      // image sequences: swap to this frame's image; the returned promise lets HyperFrames wait for the decode
      const loads = [];
      for (const q of seqs) {
        const k = FR.frameIndex(st.obj[q.c.id].play, q.c);
        if (k !== q.shown) { q.shown = k; q.img.src = FR.frameSrc(q.c, k); loads.push(q.img.decode().catch(() => {})); }
      }
      st.ready = loads.length ? Promise.all(loads) : null;
      return st;
    }
    return { render, measure, boxes, els };
  };
})(typeof globalThis !== "undefined" ? globalThis : this);
