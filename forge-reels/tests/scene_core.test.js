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

test("captions mark the spoken word as now", () => {
  const g = [[{ text: "Glass", start: 1, end: 1.4 }, { text: "first.", start: 1.5, end: 1.9 }]];
  const c = FR.captionAt(1.6, g);
  assert.deepEqual(c.words.map((w) => w.state), ["past", "now"]);
  assert.equal(FR.captionAt(5, g), null);
});
