'use strict';
// rig.js — one character, defined once, posed by joint angles. Load after core.js.
// Why: a character redrawn by hand in every shot drifts (beak grows, wing becomes a sheet, feet leave the pedals).
// A rig fixes the drawing and lets only the pose change:
//   bones    a hierarchy; each bone is a local frame (origin = joint, +x along the bone). Children follow parents.
//   parts    drawings in ONE bone's local frame. They rotate with the bone and never stretch; z sets draw order.
//   sockets  named points on bones (foot, hand, wheel hub) used by IK and by contact pins.
//   pins     "this socket must touch that point" (foot↔pedal, wheel↔road). The error is logged every frame and qa.mjs FAILs it.
// Parts still draw with wob/hatch/wash/drawCel, so the look stays hand-drawn; the rig only keeps proportions and joints honest.
// Coordinates: pose.x/y/rot/scale place the character in the space of the current transform (world space after applyView).
//
//   const PELICAN = defineRig({ name, bones: { hip: {}, thigh: { parent: 'hip', at: [0, 0], len: 68, rest: 1.6 }, ... },
//                               parts: [{ id, bone, z, hull: [[x,y]...], draw(c, k) }], sockets: { foot: { bone: 'shin', at: [66, 0] } } });
//   const pose = { x, y, rot, scale, flip, angles: { neck: -.2 }, z: { wingNear: 9 }, swap: { wingL: 'wingLOpen' }, boil: rigBoil(T) };
//   rigIK(PELICAN, pose, 'thighL', 'shinL', pedalWorldXY, -1);         // sets the two angles so the shin end reaches the pedal
//   drawRig(c, PELICAN, pose, { pins: [{ socket: 'footL', to: pedalWorldXY, tol: 4 }] });

const RIG_M = {
  id: () => [1, 0, 0, 1, 0, 0],
  mul: (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3], m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]],
  tr: (x, y) => [1, 0, 0, 1, x, y],
  rot: a => [Math.cos(a), Math.sin(a), -Math.sin(a), Math.cos(a), 0, 0],
  sc: (sx, sy) => [sx, 0, 0, sy, 0, 0],
  app: (m, p) => [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]],
  inv: m => { const d = m[0] * m[3] - m[1] * m[2]; return [m[3] / d, -m[1] / d, -m[2] / d, m[0] / d, (m[2] * m[5] - m[3] * m[4]) / d, (m[1] * m[4] - m[0] * m[5]) / d]; },
};

// defineRig: validates the hierarchy once and computes a signature. qa.mjs FAILs a film whose rig of one name
// has different signatures in different frames (a second, "slightly fixed" copy of the character in some shot).
function defineRig({ name, bones, parts, sockets = {}, unit = 1 }) {
  if (!name) throw new Error('defineRig: name required');
  const order = [], seen = new Set();
  const visit = (id, path = []) => { if (seen.has(id)) return; if (path.includes(id)) throw new Error(`rig ${name}: bone cycle at ${id}`);
    const b = bones[id]; if (!b) throw new Error(`rig ${name}: unknown bone ${id}`); if (b.parent) visit(b.parent, [...path, id]); seen.add(id); order.push(id); };
  Object.keys(bones).forEach(id => visit(id));
  for (const p of parts) { if (!bones[p.bone]) throw new Error(`rig ${name}: part ${p.id} on unknown bone ${p.bone}`); if (typeof p.draw !== 'function') throw new Error(`rig ${name}: part ${p.id} has no draw()`); }
  for (const [k, s] of Object.entries(sockets)) if (!bones[s.bone]) throw new Error(`rig ${name}: socket ${k} on unknown bone ${s.bone}`);
  const r2 = v => Math.round(v * 100) / 100;
  const sigSrc = JSON.stringify([order.map(id => { const b = bones[id]; return [id, b.parent || '', (b.at || [0, 0]).map(r2), r2(b.len || 0), r2(b.rest || 0)]; }),
    // full draw source + hull: a "slightly fixed" copy (one width or length changed) gets a different signature
    parts.map(p => [p.id, p.bone, p.z ?? 0, String(p.draw), (p.hull || []).map(q => q.map(r2))]), Object.entries(sockets).map(([k, s]) => [k, s.bone, s.at.map(r2)])]);
  let h = 2166136261; for (let i = 0; i < sigSrc.length; i++) { h ^= sigSrc.charCodeAt(i); h = Math.imul(h, 16777619); }
  parts.forEach((p, i) => { p.seed = p.seed ?? (Math.abs(h + i * 7919) % 100000); });   // constant shape seed per part: same silhouette in every frame
  return { name, bones, parts, sockets, order, unit, sig: (h >>> 0).toString(16) };
}

// rigBoil: the line-jitter seed, held for `hold` frames of 24 and cycling through `cycle` drawings (classic 3-drawing boil).
// Use it ONLY as the seed of wob() amplitude on contours. Never feed time into blob()/curvePath() points: that redraws the silhouette.
const rigBoil = (T, hold = 3, cycle = 3) => Math.floor(T * 24 / hold + 1e-6) % cycle;

// rigRootM: character space → current space.
function rigRootM(rig, pose) {
  const s = (pose.scale ?? 1) * rig.unit;
  return RIG_M.mul(RIG_M.mul(RIG_M.tr(pose.x ?? 0, pose.y ?? 0), RIG_M.rot(pose.rot ?? 0)), RIG_M.sc(pose.flip ? -s : s, s));
}
// poseRig: bone matrices in CHARACTER space (root excluded) for the pose.
function poseRig(rig, pose) {
  const M = {}, ang = pose.angles || {};
  for (const id of rig.order) { const b = rig.bones[id], at = b.at || [0, 0];
    const local = RIG_M.mul(RIG_M.tr(at[0], at[1]), RIG_M.rot((b.rest || 0) + (ang[id] || 0)));
    M[id] = b.parent ? RIG_M.mul(M[b.parent], local) : local; }
  return M;
}
// rigPoint: a socket (or [bone, [x,y]]) in the current space for this pose.
function rigPoint(rig, pose, socket) {
  const s = typeof socket === 'string' ? rig.sockets[socket] : { bone: socket[0], at: socket[1] }; if (!s) throw new Error(`rig ${rig.name}: unknown socket ${socket}`);
  return RIG_M.app(rigRootM(rig, pose), RIG_M.app(poseRig(rig, pose)[s.bone], s.at));
}

// rigIK: two-bone IK. Sets pose.angles[upper] and pose.angles[lower] so the end of `lower` (socket `end` or [lower.len, 0])
// reaches `target` (current space). bend = +1 / -1 picks the knee side. The lower bone must hang at [upper.len, 0] of the upper.
// Out of reach: the limb straightens toward the target, and the leftover distance shows up as a pin error, never as a stretched limb.
function rigIK(rig, pose, upper, lower, target, bend = 1, end = null) {
  pose.angles = pose.angles || {};
  const bu = rig.bones[upper], bl = rig.bones[lower];
  if (bl.parent !== upper) throw new Error(`rigIK: ${lower} must be a child of ${upper}`);
  const L1 = bu.len, endPt = end ? rig.sockets[end].at : [bl.len, 0];
  const L2 = Math.hypot(endPt[0], endPt[1]), endAng = Math.atan2(endPt[1], endPt[0]);
  if (!(L1 > 0 && L2 > 0)) throw new Error(`rigIK: ${upper}.len and ${lower}.len (or socket) must be > 0`);
  const t = RIG_M.app(RIG_M.inv(rigRootM(rig, pose)), target), M = poseRig(rig, pose);
  const parentM = bu.parent ? M[bu.parent] : RIG_M.id(), j = RIG_M.app(parentM, bu.at || [0, 0]), parentAng = Math.atan2(parentM[1], parentM[0]);
  const dx = t[0] - j[0], dy = t[1] - j[1], d = clamp(Math.hypot(dx, dy), Math.abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4);
  const a1 = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1)), a2 = Math.acos(clamp((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1));
  const upperWorld = Math.atan2(dy, dx) - bend * a1;
  pose.angles[upper] = upperWorld - parentAng - (bu.rest || 0);
  pose.angles[lower] = bend * (Math.PI - a2) - (bl.rest || 0) - endAng;
  return pose;
}

// rigLog: what qa.mjs reads after each frame. Reset by the QA/render tools before drawing a frame.
// Capped so playback and full renders (which never reset it) do not grow it without limit.
function rigLog(entry) { const log = (window.__rig = window.__rig || []); if (log.length > 512) log.splice(0, log.length - 256); log.push(entry); }

// drawRig: draws every visible part in z order and registers the real on-screen hull for qa.mjs (subject size).
//   opts.pins   [{ socket, to: [x,y] current space, tol = 3 }]  logged as contact errors (in output px)
//   opts.focus  false for extras/crowd (only the protagonist should feed markFocus)
//   opts.only   (part) => bool, to draw a subset (e.g. far-side parts behind a prop)
function drawRig(c, rig, pose, opts = {}) {
  const { pins = [], focus = true, only = null, T = 0 } = opts;
  const root = rigRootM(rig, pose), M = poseRig(rig, pose), zOver = pose.z || {}, swap = pose.swap || {};
  const visible = rig.parts.filter(p => (!p.slot || (swap[p.slot] ? swap[p.slot] === p.id : p.default)) && !(pose.hide || []).includes(p.id) && (!only || only(p)));
  visible.sort((a, b) => (zOver[a.id] ?? a.z ?? 0) - (zOver[b.id] ?? b.z ?? 0));
  const base = c.getTransform(), toPx = (m, q) => { const w = RIG_M.app(m, q); return [base.a * w[0] + base.c * w[1] + base.e, base.b * w[0] + base.d * w[1] + base.f]; };
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const p of visible) {
    const m = RIG_M.mul(root, M[p.bone]);
    c.save(); c.transform(m[0], m[1], m[2], m[3], m[4], m[5]);
    try { p.draw(c, { seed: p.seed, boil: pose.boil ?? 0, pose, rig, T, part: p }); } finally { c.restore(); }
    for (const q of p.hull || []) { const [X, Y] = toPx(m, q); x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y); }
  }
  if (focus && x1 > x0) {
    const cw = c.canvas.width, ch = c.canvas.height, b = [Math.max(0, x0), Math.max(0, y0), Math.min(cw, x1), Math.min(ch, y1)], f = window.__focus;
    if (b[2] > b[0] && b[3] > b[1]) window.__focus = f ? [Math.min(f[0], b[0]), Math.min(f[1], b[1]), Math.max(f[2], b[2]), Math.max(f[3], b[3])] : b;
    window.__focusSrc = 'rig';
  }
  const px = Math.hypot(base.a, base.b) || 1, contacts = pins.map(pin => {
    const s = rig.sockets[pin.socket]; if (!s) throw new Error(`rig ${rig.name}: unknown socket ${pin.socket}`);
    const at = RIG_M.app(RIG_M.mul(root, M[s.bone]), s.at); return { socket: pin.socket, err: +(Math.hypot(at[0] - pin.to[0], at[1] - pin.to[1]) * px).toFixed(2), tol: (pin.tol ?? 3) * px };
  });
  if (!only && !visible.some(p => p.hull && p.hull.length >= 3)) throw new Error(`rig ${rig.name}: parts need hull points (bone-local outline) so the subject can be measured`);
  rigLog({ name: rig.name, sig: rig.sig, focus, contacts, parts: visible.map(p => p.id) });
  return { root, M };
}

// drawRigBones: debug overlay for review crops — bones as lines, sockets as dots, pins as circles (red = over tolerance).
function drawRigBones(c, rig, pose, pins = []) {
  const root = rigRootM(rig, pose), M = poseRig(rig, pose); c.save(); c.lineWidth = 2 / (Math.hypot(c.getTransform().a, c.getTransform().b) || 1);
  for (const id of rig.order) { const b = rig.bones[id], m = RIG_M.mul(root, M[id]), a = RIG_M.app(m, [0, 0]), e = RIG_M.app(m, [b.len || 8, 0]);
    c.strokeStyle = '#1e90ff'; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(e[0], e[1]); c.stroke(); c.fillStyle = '#1e90ff'; c.fillRect(a[0] - 3, a[1] - 3, 6, 6); }
  for (const pin of pins) { const p = rigPoint(rig, pose, pin.socket), bad = Math.hypot(p[0] - pin.to[0], p[1] - pin.to[1]) > (pin.tol ?? 3);
    c.strokeStyle = bad ? '#e0201b' : '#18a558'; c.beginPath(); c.arc(pin.to[0], pin.to[1], 9, 0, TAU); c.stroke(); c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(pin.to[0], pin.to[1]); c.stroke(); }
  c.restore();
}

// drawModelSheet: the character in its key poses, side by side, same scale, on a neutral page with a height ruler.
// Render it (render.mjs --only 0) and LOOK before any shot is built: this is where proportions and draw order get fixed.
//   poses = [{ label, pose, pins? }]  (pose.x/y are ignored: each pose is centered in its cell; pose.scale is kept relative)
function drawModelSheet(c, rig, poses, { cols = Math.min(poses.length, 3), title = rig.name, bones = false, ground = true } = {}) {
  resetT(c); c.fillStyle = '#f6f1e7'; c.fillRect(0, 0, W, H);
  const rows = Math.ceil(poses.length / cols), top = 70, cw = W / cols, chh = (H - top) / rows;
  c.fillStyle = '#2a2622'; c.font = '600 30px system-ui, sans-serif'; c.fillText(`${title} — model sheet (${rig.sig})`, 24, 44);
  // measure every pose once, then use ONE scale for all cells so proportions compare honestly
  const boxes = poses.map(({ pose }) => { const p = { ...pose, x: 0, y: 0, rot: pose.rot || 0 }, root = rigRootM(rig, p), M = poseRig(rig, p); let a = [Infinity, Infinity, -Infinity, -Infinity];
    for (const part of rig.parts) for (const q of part.hull || []) { const v = RIG_M.app(RIG_M.mul(root, M[part.bone]), q); a = [Math.min(a[0], v[0]), Math.min(a[1], v[1]), Math.max(a[2], v[0]), Math.max(a[3], v[1])]; } return a; });
  const k = Math.min(...boxes.map(b => Math.min((cw * .82) / (b[2] - b[0] || 1), (chh * .78) / (b[3] - b[1] || 1))));
  poses.forEach(({ label, pose, pins = [] }, i) => {
    const b = boxes[i], cx = (i % cols) * cw + cw / 2, cy = top + Math.floor(i / cols) * chh + chh * .47;
    c.strokeStyle = '#d8cfbf'; c.lineWidth = 1; c.strokeRect((i % cols) * cw + 8, top + Math.floor(i / cols) * chh + 4, cw - 16, chh - 8);
    c.save(); c.translate(cx - (b[0] + b[2]) / 2 * k, cy - (b[1] + b[3]) / 2 * k); c.scale(k, k);
    if (ground) { c.strokeStyle = '#c9bca6'; c.lineWidth = 2 / k; c.setLineDash([8 / k, 6 / k]); c.beginPath(); c.moveTo(b[0] - 40, b[3]); c.lineTo(b[2] + 40, b[3]); c.stroke(); c.setLineDash([]); }
    drawRig(c, rig, { ...pose, x: 0, y: 0 }, { pins, focus: false });
    if (bones) drawRigBones(c, rig, { ...pose, x: 0, y: 0 }, pins);
    c.restore();
    c.fillStyle = '#2a2622'; c.font = '22px system-ui, sans-serif'; c.textAlign = 'center'; c.fillText(label, cx, top + Math.floor(i / cols) * chh + chh - 18); c.textAlign = 'left';
  });
}
