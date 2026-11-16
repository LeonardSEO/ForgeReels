// node --test tests/scene_core.test.js   (run from forge-reels/; also run by tests/test_scene_core.py)
const test = require("node:test");
const assert = require("node:assert/strict");
const FR = require("../assets/scene-library/core.js");

const scene = { world: { w: 2000, h: 3000 }, camera: { start: "all" },
  components: [{ type: "phone", id: "phone", x: 100, y: 100 }, { type: "chart", id: "c", bars: [{ value: 1 }, { value: 2 }] }] };
const boxes = { phone: { x: 100, y: 100, w: 420, h: 865 }, "phone.glass": { x: 120, y: 120, w: 380, h: 820 } };
const ev = (t, action, object, dur, args) => ({ t, action, object, dur: dur == null ? FR.DUR[action] : dur, args });

test("parts lists every animatable id", () => {
  const p = FR.parts(scene);
  for (const id of ["phone", "phone.glass", "phone.grid", "c.b1", "c.b2", "c.v2"]) assert.ok(p.includes(id), id);
  assert.throws(() => FR.parts({ components: [{ type: "nope", id: "x" }] }), /unknown component/);
});

test("an object whose first event is reveal is hidden before it and fully shown after", () => {
  const evs = [ev(2, "reveal", "phone.glass")];
  assert.equal(FR.stateAt(1.9, scene, evs, boxes).obj["phone.glass"].o, 0);
  assert.equal(FR.stateAt(2 + FR.DUR.reveal, scene, evs, boxes).obj["phone.glass"].o, 1);
  assert.equal(FR.stateAt(0, scene, evs, boxes).obj["phone.screen"].o, 1);       // untouched parts stay visible
});

test("default-hidden parts stay hidden until revealed", () => {
  assert.equal(FR.stateAt(5, scene, [], boxes).obj["phone.grid"].o, 0);
  assert.equal(FR.stateAt(5, scene, [ev(1, "reveal", "phone.grid")], boxes).obj["phone.grid"].o, 1);
});

test("draw, type, grow and count start from zero and finish at their end value", () => {
  const evs = [ev(1, "draw", "phone.rows"), ev(1, "grow", "c.b1"), ev(1, "count", "c.v1", 1, { from: 0, to: 49 })];
  const before = FR.stateAt(0.5, scene, evs, boxes).obj, after = FR.stateAt(3, scene, evs, boxes).obj;
  assert.equal(before["phone.rows"].draw, 0); assert.equal(after["phone.rows"].draw, 1);
  assert.equal(before["c.b1"].grow, 0); assert.ok(Math.abs(after["c.b1"].grow - 1) < 1e-9);
  assert.equal(before["c.v1"].count, 0); assert.equal(after["c.v1"].count, 49);
});

test("state depends on t alone (seeking backwards gives the same frame)", () => {
  const evs = [ev(1, "reveal", "phone.glass"), ev(2, "pulse", "phone.glass", 0.8, { repeat: 2 })];
  const a = JSON.stringify(FR.stateAt(2.3, scene, evs, boxes));
  FR.stateAt(9, scene, evs, boxes);
  assert.equal(JSON.stringify(FR.stateAt(2.3, scene, evs, boxes)), a);
});

test("pulse is transient", () => {
  const evs = [ev(1, "pulse", "phone")];
  assert.ok(FR.stateAt(1 + FR.DUR.pulse / 2, scene, evs, boxes).obj.phone.pulse > 0.9);
  assert.equal(FR.stateAt(5, scene, evs, boxes).obj.phone.pulse, 0);
});

test("focus moves the camera onto the object and wide returns to the whole world", () => {
  const evs = [ev(1, "focus", "phone.glass"), ev(4, "wide", null)];
  const start = FR.stateAt(0, scene, evs, boxes).camera;
  const focused = FR.stateAt(1 + FR.DUR.focus, scene, evs, boxes).camera;
  const wide = FR.stateAt(4 + FR.DUR.wide, scene, evs, boxes).camera;
  assert.equal(focused.x, 310); assert.equal(focused.y, 530);
  assert.ok(focused.s > start.s);
  assert.deepEqual(wide, start);
});

test("a camera move with ease 'out' starts at full speed (the hook moves from frame 1)", () => {
  const dt = 1 / 30;
  const zoomAt = (args, t) => FR.stateAt(t, scene, [ev(0, "focus", "phone.glass", 1.5, args)], boxes).camera.s;
  const s0 = zoomAt({}, 0);
  const firstStep = (args) => Math.log(zoomAt(args, dt) / s0);
  const lastStep = (args) => Math.log(zoomAt(args, 1.5) / zoomAt(args, 1.5 - dt));
  assert.ok(firstStep({ ease: "out" }) > 20 * firstStep({}), "ease out moves much more in frame 1 than the default");
  assert.ok(firstStep({ ease: "out" }) > lastStep({ ease: "out" }));
  assert.equal(zoomAt({ ease: "out" }, 1.5), zoomAt({}, 1.5));               // same landing framing
});

test("captions mark the spoken word as now", () => {
  const g = [[{ text: "Glass", start: 1, end: 1.4 }, { text: "first.", start: 1.5, end: 1.9 }]];
  const c = FR.captionAt(1.6, g);
  assert.deepEqual(c.words.map((w) => w.state), ["past", "now"]);
  assert.equal(FR.captionAt(5, g), null);
});

test("every component draws exactly the parts core.js says it has", () => {
  require("../assets/scene-library/renderer.js");
  const samples = {
    phone: {}, browser: { tabs: ["A", "B"], results: ["x", "y", "z"] }, terminal: { lines: ["$ ls", "ok"] },
    nodes: { nodes: [{ id: "a", label: "A", x: 0, y: 0 }, { id: "b", label: "B", x: 300, y: 0 }], links: [["a", "b"]] },
    chart: { bars: [{ value: 1 }, { value: 3 }] }, document: { lines: ["one", "two"] }, chip: { traces: 6 },
    stack: { layers: [{ label: "Glass" }, { label: "Grid" }] }, text: { text: "Hi" }, counter: { value: 9 },
    callout: { text: "Here" }, image: { src: "x.png" }, steps: { steps: ["Build", "Ship"] }, frames: { src: "s/%04d.jpg", count: 3 }, lens: {}, agent: { steps: ["a", "b"] },
  };
  assert.deepEqual(Object.keys(samples).sort(), Object.keys(FR.COMPONENTS).sort());
  for (const [type, spec] of Object.entries(samples)) {
    const c = Object.assign({ type, id: "k", x: 0, y: 0 }, spec);
    const drawn = new Set(["k", ...[...FR.BUILD[type](c)[2].matchAll(/data-obj="([^"]+)"/g)].map((m) => m[1])]);
    assert.deepEqual([...drawn].sort(), FR.parts({ components: [c] }).sort(), type);
  }
});

test("the camera can frame a group of objects (their union box)", () => {
  const b = { a: { x: 0, y: 0, w: 100, h: 100 }, b: { x: 300, y: 500, w: 100, h: 100 } };
  const sc = { world: { w: 2000, h: 3000 }, camera: { start: ["a", "b"], push: 0 }, components: [] };
  const cam = FR.stateAt(0, sc, [], b).camera;
  assert.equal(cam.x, 200); assert.equal(cam.y, 300);
  const f = FR.stateAt(5, sc, [ev(1, "focus", ["a", "b"])], b).camera;
  assert.deepEqual(f, cam);
});

test("pill captions sit below the picture area and inside the reel safe zone", () => {
  const s = FR.viewFor({ captions: "pill" }).safe;
  const css = require("fs").readFileSync(require("path").join(__dirname, "../assets/scene-library/styles.css"), "utf8");
  const top = +css.match(/\.fr-captions\.pill-style \{[^}]*top: (\d+)px/)[1];
  assert.ok(top >= s.y + s.h && top + 170 <= 1330, "pill captions top " + top);
  const head = +css.match(/\.fr-captions\.headline \{[^}]*top: (\d+)px/)[1];
  assert.ok(head >= 168 && head + 150 <= FR.viewFor({}).safe.y, "headline captions top " + head);
});

test("a value that counts up is hidden until its count starts (no floating 0.00)", () => {
  const evs = [ev(2, "count", "c.v1", 1, { from: 0, to: 0.82 })];
  assert.equal(FR.stateAt(1.9, scene, evs, boxes).obj["c.v1"].o, 0);
  assert.equal(FR.stateAt(3.5, scene, evs, boxes).obj["c.v1"].o, 1);
});

// ---------- style upgrades learned from reference reels (2026-11-15)
test("the camera keeps pushing in slowly while it holds, and stays continuous into the next move", () => {
  const sc = { world: { w: 2000, h: 3000 }, camera: { start: "all" }, components: [] };
  const evs = [ev(1, "focus", "phone", 0.5), ev(5, "wide", null, 1)];
  const landed = FR.stateAt(1.5, sc, evs, boxes).camera, later = FR.stateAt(3.5, sc, evs, boxes).camera;
  assert.ok(later.s > landed.s * 1.02 && later.s < landed.s * 1.08, `${landed.s} -> ${later.s}`);
  const justBefore = FR.stateAt(4.999, sc, evs, boxes).camera, atStart = FR.stateAt(5, sc, evs, boxes).camera;
  assert.ok(Math.abs(justBefore.s - atStart.s) < 1e-3);
  const still = { world: sc.world, camera: { start: "all", push: 0 }, components: [] };
  assert.deepEqual(FR.stateAt(3.5, still, evs, boxes).camera, FR.stateAt(1.5, still, evs, boxes).camera);
});

test("focus blurs the other components (depth of field) and wide clears it", () => {
  const sc2 = { components: [{ type: "phone", id: "phone", x: 0, y: 0 }, { type: "chip", id: "ic", x: 0, y: 1200 }] };
  const evs = [ev(1, "focus", "phone.screen", 0.5), ev(4, "wide", null, 0.5)];
  const st = FR.stateAt(2, sc2, evs, boxes).obj;
  assert.equal(st.phone.blur, 0);
  assert.ok(st.ic.blur > 4);
  assert.equal(FR.stateAt(5, sc2, evs, boxes).obj.ic.blur, 0);
  const off = Object.assign({ camera: { dof: false } }, sc2);
  assert.equal(FR.stateAt(2, off, evs, boxes).obj.ic.blur, 0);
});

test("headline captions keep the key-word flag and hide words not yet spoken", () => {
  const g = [[{ text: "the", start: 1, end: 1.2 }, { text: "glass", start: 1.3, end: 1.7, key: true }, { text: "now", start: 1.8, end: 2 }]];
  const c = FR.captionAt(1.4, g);
  assert.deepEqual(c.words.map((w) => [w.state, !!w.key]), [["past", false], ["now", true], ["next", false]]);
});

test("the view leaves room for headline captions at the top, or pill captions at the bottom", () => {
  const top = FR.viewFor({}), pill = FR.viewFor({ captions: "pill" });
  assert.ok(top.safe.y >= 440 && top.safe.y + top.safe.h <= 1330);
  assert.ok(pill.safe.y >= 168 && pill.safe.y + pill.safe.h <= 1135);
});

test("steps: one part per step", () => {
  assert.deepEqual(FR.parts({ components: [{ type: "steps", id: "rail", steps: ["Build", "Deploy", "Serve"] }] }),
    ["rail", "rail.s1", "rail.s2", "rail.s3"]);
});

test("frames: a captured image sequence plays from its word and holds its last frame", () => {
  const sc = { components: [{ type: "frames", id: "demo", src: "shots/%04d.jpg", count: 90, fps: 30 }] };
  const evs = [ev(2, "play", "demo", 3)];
  assert.equal(FR.stateAt(1, sc, evs, {}).obj.demo.play, 0);
  assert.equal(FR.stateAt(3.5, sc, evs, {}).obj.demo.play, 1.5);
  assert.equal(FR.stateAt(9, sc, evs, {}).obj.demo.play, 3);
  assert.equal(FR.frameIndex(1.5, sc.components[0]), 45);
  assert.equal(FR.frameIndex(99, sc.components[0]), 89);
});

test("lens: parts for the glass profile and the two sets of light rays", () => {
  assert.deepEqual(FR.parts({ components: [{ type: "lens", id: "lens" }] }).sort(),
    ["lens", "lens.centre", "lens.glass", "lens.label", "lens.rim"]);
});

test("frames: file names follow ffmpeg's numbering, which starts at 1 unless the scene says otherwise", () => {
  assert.equal(FR.frameSrc({ src: "seq/%04d.jpg" }, 0), "seq/0001.jpg");
  assert.equal(FR.frameSrc({ src: "seq/%04d.jpg" }, 149), "seq/0150.jpg");
  assert.equal(FR.frameSrc({ src: "seq/f_%03d.png", first: 0 }, 7), "seq/f_007.png");
});

// ---------- learned from a professional promo reel (2026-11-15)
test("strike crosses an object out on its word (negation: 'no templates')", () => {
  const evs = [ev(1, "strike", "c")];
  assert.equal(FR.stateAt(0.5, scene, evs, boxes).obj.c.strike, 0);
  assert.equal(FR.stateAt(1 + FR.DUR.strike, scene, evs, boxes).obj.c.strike, 1);
});

test("a counting number blurs while it rolls and is sharp when it lands", () => {
  const evs = [ev(1, "count", "c.v1", 1, { from: 0, to: 39213786 })];
  assert.ok(FR.stateAt(1.2, scene, evs, boxes).obj["c.v1"].roll > 0.5);
  assert.equal(FR.stateAt(2.5, scene, evs, boxes).obj["c.v1"].roll, 0);
});

test("agent: a prompt and one part per step", () => {
  assert.deepEqual(FR.parts({ components: [{ type: "agent", id: "a", steps: ["Read 3 pages", "Made voice.mp3"] }] }).sort(),
    ["a", "a.input", "a.prompt", "a.s1", "a.s2"].sort());
});

test("ambient particles are a pure function of time and seed", () => {
  const a = FR.particles(3.2, 40, 7), b = FR.particles(3.2, 40, 7), c = FR.particles(3.3, 40, 7);
  assert.equal(a.length, 40);
  assert.deepEqual(a, b);
  assert.notDeepEqual(a, c);
  assert.ok(a.every((p) => p.x >= 0 && p.x <= 1 && p.y >= 0 && p.y <= 1 && p.a >= 0 && p.a <= 1));
});

test("a counter's landed number fits its width", () => {
  require("../assets/scene-library/renderer.js");
  const [w, , html] = FR.BUILD.counter({ id: "v", value: 39213786, w: 700 });
  const size = +html.match(/font-size:(\d+)px/)[1];
  assert.ok(size * 0.6 * "39,213,786".length <= w, `font ${size}px`);
});

test("odometer: digits lock from the left; only the digits still rolling are marked", () => {
  const d = FR.odometer("4,317", "5,070");
  assert.deepEqual(d.map((x) => x.settled), [false, false, false, false, false]);
  const e = FR.odometer("5,061", "5,070");
  assert.deepEqual(e.map((x) => [x.ch, x.settled]), [["5", true], [",", true], ["0", true], ["6", false], ["1", false]]);
  assert.ok(FR.odometer("5,070", "5,070").every((x) => x.settled));
});

test("scan reveals an object behind a moving line", () => {
  const evs = [ev(1, "scan", "c")];
  assert.equal(FR.stateAt(0.5, scene, evs, boxes).obj.c.scan, 0);
  assert.equal(FR.stateAt(0.5, scene, evs, boxes).obj.c.o, 0);           // hidden until its scan
  const mid = FR.stateAt(1 + FR.DUR.scan / 2, scene, evs, boxes).obj.c;
  assert.ok(mid.scan > 0.2 && mid.scan < 0.9 && mid.o === 1);
  assert.equal(FR.stateAt(3, scene, evs, boxes).obj.c.scan, 1);
});

test("theme flips the whole stage on its word (dark <-> light marks a turn in the argument)", () => {
  const s = Object.assign({}, scene, { theme: "dark" });
  assert.equal(FR.STAGE, "stage");
  const evs = [ev(2, "theme", "stage", null, { to: "light" }), ev(6, "theme", "stage", null, { to: "dark" })];
  assert.deepEqual(FR.stateAt(1, s, evs, boxes).theme, { from: "dark", to: "dark", p: 1 });
  const mid = FR.stateAt(2 + FR.DUR.theme / 2, s, evs, boxes).theme;
  assert.ok(mid.from === "dark" && mid.to === "light" && mid.p > 0.2 && mid.p < 0.8);
  assert.deepEqual(FR.stateAt(4, s, evs, boxes).theme, { from: "dark", to: "light", p: 1 });
  assert.deepEqual(FR.stateAt(9, s, evs, boxes).theme, { from: "light", to: "dark", p: 1 });
});
