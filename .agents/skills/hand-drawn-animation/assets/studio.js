'use strict';
// Optional production helpers. Load after core.js. Geometry and stroke samples are
// authored once in local space; animation deforms those samples without re-seeding.

function exposureTrack(segments = [{ at: 0, on: 2 }], fps = 24) {
  if (!Number.isInteger(fps) || fps <= 0 || !segments.length) throw new Error('Invalid exposure track');
  const keys = segments.map((s, k) => {
    const f = Math.round(s.at * fps);
    if (!Number.isFinite(s.at) || s.at < 0 || Math.abs(f - s.at * fps) > 1e-5 || k && s.at <= segments[k - 1].at || !s.hold && (!Number.isInteger(s.on) || s.on < 1)) throw new Error('Exposure keys need increasing frame-aligned times and positive on counts');
    return { ...s, f };
  });
  if (keys[0].f !== 0) throw new Error('Exposure track must start at 0');
  return t => {
    const f = Math.max(0, Math.floor(t * fps + 1e-6)); let s = keys[0];
    for (const key of keys) { if (key.f > f) break; s = key; }
    return (s.hold ? s.f : s.f + Math.floor((f - s.f) / s.on) * s.on) / fps;
  };
}
function drawingTrack(keys) {
  if (!keys.length || keys[0].at !== 0 || keys.some((k, i) => !Number.isFinite(k.at) || i && k.at <= keys[i - 1].at || k.id === undefined)) throw new Error('Drawing keys need increasing times, ids and a start at 0');
  return t => { let id = keys[0].id; for (const k of keys) { if (k.at > t) break; id = k.id; } return id; };
}
// Root is fixed. An unreachable target is clamped, never silently lengthening bones.
function solveLimb(root, target, a, b, bend = 1) {
  if (!(a > 0 && b > 0) || ![...root, ...target, a, b].every(Number.isFinite)) throw new Error('Invalid limb');
  const dx = target[0] - root[0], dy = target[1] - root[1], wanted = Math.hypot(dx, dy);
  const d = clamp(wanted, Math.abs(a - b), a + b), ux = wanted > 1e-9 ? dx / wanted : 1, uy = wanted > 1e-9 ? dy / wanted : 0;
  const along = d > 1e-9 ? (a * a - b * b + d * d) / (2 * d) : 0;
  const side = Math.sqrt(Math.max(0, a * a - along * along)) * (bend < 0 ? -1 : 1);
  const joint = [root[0] + ux * along - uy * side, root[1] + uy * along + ux * side];
  const end = [root[0] + ux * d, root[1] + uy * d];
  return { root: root.slice(), joint, end, error: Math.hypot(end[0] - target[0], end[1] - target[1]), reachable: Math.abs(wanted - d) < 1e-6 };
}
function motionPath(points, { smooth = true, closed = false } = {}) {
  if (points.length < 2 || points.some(p => p.length !== 2 || !p.every(Number.isFinite))) throw new Error('Path needs finite 2D points');
  const q = (smooth ? smoothPts(points, closed, 2, Math.PI) : points).map(p => p.slice());
  if (closed) q.push(q[0].slice());
  const lengths = [0]; for (let i = 1; i < q.length; i++) lengths.push(lengths[i - 1] + Math.hypot(q[i][0] - q[i - 1][0], q[i][1] - q[i - 1][1]));
  const length = lengths[lengths.length - 1];
  return { length, at(u) {
    const d = clamp(u, 0, 1) * length; let lo = 1, hi = q.length - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (lengths[mid] < d) lo = mid + 1; else hi = mid; }
    const a = q[lo - 1], b = q[lo], seg = lengths[lo] - lengths[lo - 1], t = seg ? (d - lengths[lo - 1]) / seg : 0;
    return { p: [lerp(a[0], b[0], t), lerp(a[1], b[1], t)], tangent: seg ? [(b[0] - a[0]) / seg, (b[1] - a[1]) / seg] : [1, 0] };
  } };
}
function morphPoints(a, b, t) {
  if (a.length !== b.length || a.length < 2) throw new Error('Morph needs corresponding points; use drawing substitution for topology changes');
  return a.map((p, i) => [lerp(p[0], b[i][0], t), lerp(p[1], b[i][1], t)]);
}
const strokeProfile = (u, keys) => {
  if (!keys?.length) return 1;
  if (u <= keys[0][0]) return keys[0][1];
  for (let k = 1; k < keys.length; k++) if (u <= keys[k][0]) { const a = keys[k - 1], b = keys[k]; return lerp(a[1], b[1], (u - a[0]) / (b[0] - a[0])); }
  return keys[keys.length - 1][1];
};
function strokeSeed(id) { let n = 2166136261; for (const c of String(id)) n = Math.imul(n ^ c.charCodeAt(0), 16777619); return n >>> 0; }
// A stable rest-space stroke. Pressure is an authored profile along arc length.
function makeStroke(points, { id = 'stroke', seed = strokeSeed(id), width = 3, pressure = [[0, .28], [.12, 1], [.7, .9], [1, .18]], close = false, rough = .2, step = 2 } = {}) {
  if (!(Number.isFinite(width) && Number.isFinite(step) && width > 0 && step > 0)) throw new Error('Stroke width and step must be positive');
  if (pressure?.some((k,i) => k.length !== 2 || !k.every(Number.isFinite) || k[0] < 0 || k[0] > 1 || k[1] < 0 || i > 0 && k[0] <= pressure[i-1][0])) throw new Error('Pressure profile needs increasing positions in 0..1 and nonnegative widths');
  const path = motionPath(points, { closed: close }), n = Math.max(close ? 12 : 2, Math.ceil(path.length / step));
  const samples = Array.from({ length: n + 1 }, (_, i) => {
    const u = i / n, { p, tangent: v } = path.at(u);
    const offset = rough * (close ? Math.sin(u * TAU * 3 + hash(1, seed) * TAU) : noise1(u * 4 + 3, seed) * Math.sin(Math.PI * u));
    return { p: [p[0] - v[1] * offset, p[1] + v[0] * offset], u, w: width * Math.max(.02, strokeProfile(u, close ? null : pressure)) };
  });
  if (close) samples[samples.length - 1] = { ...samples[0], p: samples[0].p.slice(), u: 1 };
  return { id, seed, samples, close, length: path.length, width };
}
function drawStroke(c, stroke, { color = PAL.ink, map = p => p, progress = 1, opacity = 1, material = 'ink', boil = 0 } = {}) {
  const end = clamp(progress, 0, 1); if (end <= 0) return;
  const list = [];
  for (const sample of stroke.samples) {
    if (sample.u > end) {
      const a = stroke.samples[list.length - 1]; if (a && a.u < end) { const t = (end - a.u) / (sample.u - a.u); list.push({ p: [lerp(a.p[0], sample.p[0], t), lerp(a.p[1], sample.p[1], t)], w: lerp(a.w, sample.w, t), u: end }); } break;
    }
    list.push(sample);
  }
  if (list.length < 2) return;
  const points = list.map(s => {
    // Boil is an optional small bounded redraw variant; endpoints remain pinned.
    const amp = boil ? Math.sin(s.u * Math.PI) * stroke.width * .08 : 0;
    return map([s.p[0] + amp * noise1(s.u * 5 + boil * .31, stroke.seed), s.p[1] + amp * noise1(s.u * 5 + 17 + boil * .31, stroke.seed)], s.u);
  });
  const left = [], right = [], fullClose = stroke.close && end === 1, last = points.length - 1;
  for (let i = 0; i <= last; i++) {
    const a = points[i ? i - 1 : fullClose ? last - 1 : 0], b = points[i < last ? i + 1 : fullClose ? 1 : last];
    const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1, r = list[i].w / 2;
    left.push([points[i][0] - dy / len * r, points[i][1] + dx / len * r]); right.push([points[i][0] + dy / len * r, points[i][1] - dx / len * r]);
  }
  c.save(); c.fillStyle = color; c.globalAlpha *= opacity * (material === 'pencil' ? .5 : 1);
  c.fill(polyPath([...left, ...right.reverse()]));
  if (!fullClose) for (const i of [0, last]) { c.beginPath(); c.arc(...points[i], list[i].w / 2, 0, TAU); c.fill(); }
  // Graphite deposits remain attached to the canonical stroke, including through deformation.
  if (material === 'pencil' || material === 'dry') {
    c.globalAlpha *= .5;
    for (let i = 0; i <= last; i++) {
      const a = list[i], jitter = (hash(i, stroke.seed) - .5) * a.w * 1.3;
      const p = map([a.p[0] + jitter, a.p[1] + (hash(i, stroke.seed + 1) - .5) * a.w], a.u);
      const r = .25 + hash(i, stroke.seed + 2) * .55; c.beginPath(); c.ellipse(p[0], p[1], r * 1.6, r, 0, 0, TAU); c.fill();
    }
  }
  c.restore();
}
// A deliberately designed stretched drawing, distinct from the legacy ghost trail.
function smearPose(points, direction, amount, pivot = [0, 0]) {
  const dx = Math.cos(direction), dy = Math.sin(direction), stretch = Math.max(.1, 1 + amount), side = 1 / Math.sqrt(stretch);
  return points.map(p => { const x = p[0] - pivot[0], y = p[1] - pivot[1], a = (x * dx + y * dy) * stretch, b = (-x * dy + y * dx) * side; return [pivot[0] + a * dx - b * dy, pivot[1] + a * dy + b * dx]; });
}

// ===================== HAND-DRAWN ANNOTATIONS (ROUGH-NOTATION STYLE) =====================
// Deterministic progress-driven (0..1) annotations for text and focal regions.
// `box` accepts [x, y, w, h], { x, y, w, h }, or the return object of fitHandText / wrapHandText ({ box: [x, y, w, h] }).
function _normBox(box) {
  if (Array.isArray(box) && box.length >= 4) return box;
  if (box && Array.isArray(box.box)) return box.box;
  if (box && Number.isFinite(box.x)) return [box.x, box.y, box.w ?? box.width ?? 0, box.h ?? box.height ?? 0];
  throw new Error('Annotation box must be [x, y, w, h] or { box: [x, y, w, h] }');
}
// annotateHighlight: marker swipe across a text box. Each pass is ONE filled band (wobbly top/bottom edges, slanted
// nib ends), so overlapping alpha never beads into dark dots. Draw it before the text, or keep the multiply blend.
function annotateHighlight(c, box, o = {}) {
  const { progress = 1, color = PAL.accents[2] || '#f2c14e', al = .38, seed = 1, iterations = 2, padX = 8, padY = 4 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box), r = rng(seed);
  const x0 = bx - padX, x1 = bx + bw + padX, half = bh / 2 + padY, cy = by + bh / 2;
  c.save(); c.globalCompositeOperation = PAL.washBlend || 'multiply'; c.fillStyle = color;
  for (let k = 0; k < iterations; k++) {
    const passP = clamp(p * iterations - k, 0, 1); if (passP <= 0) continue;
    const xe = lerp(x0, x1, passP), dy = (k - (iterations - 1) / 2) * bh * .12 + (r() - .5) * 3, ph = r() * 50;
    const n = Math.max(2, Math.ceil((xe - x0) / 24)), slant = half * .35, top = [], bot = [];
    for (let j = 0; j <= n; j++) { const x = lerp(x0, xe, j / n), u = x / 140 + ph;
      top.push([x + slant, cy + dy - half * (.92 + .08 * noise1(u, seed + k))]);
      bot.push([x - slant, cy + dy + half * (.92 + .08 * noise1(u + 31, seed + k))]); }
    c.globalAlpha = al * (k ? .7 : 1);
    c.fill(polyPath([...top, ...bot.reverse()], true));
  }
  c.restore();
}
// annotateUnderline: organic double-pass hand-drawn underline beneath a box.
function annotateUnderline(c, box, o = {}) {
  const { progress = 1, color = PAL.accents[0] || PAL.ink, width = 3.2, seed = 1, padX = 4, offsetY = 6, iterations = 2 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box), r = rng(seed);
  const x0 = bx - padX, x1 = bx + bw + padX, y0 = by + bh + offsetY;
  for (let k = 0; k < iterations; k++) {
    const passP = clamp(p * 1.15 - k * .15, 0, 1);
    if (passP <= 0) continue;
    const dy = k * 2.2 + (r() - .5) * 1.8;
    const pts = [[x0, y0 + dy], [lerp(x0, x1, .5), y0 + dy + (r() - .5) * 3.5], [x1, y0 + dy + (r() - .5) * 2]];
    brush(c, pts, { w: width * (k ? .78 : 1), color, p: passP, seed: seed + k * 19, amp: 1.2, taper: .35, al: k ? .75 : 1 });
  }
}
// annotateBox: hand-drawn 4-stroke rectangle around a region with slight corner overshoot.
function annotateBox(c, box, o = {}) {
  const { progress = 1, color = PAL.ink, width = 2.6, seed = 1, padding = 8, overshoot = 5 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box);
  const x0 = bx - padding, y0 = by - padding, x1 = bx + bw + padding, y1 = by + bh + padding;
  const edges = [
    [[x0 - overshoot, y0], [x1 + overshoot, y0]],
    [[x1, y0 - overshoot], [x1, y1 + overshoot]],
    [[x1 + overshoot, y1], [x0 - overshoot, y1]],
    [[x0, y1 + overshoot], [x0, y0 - overshoot]],
  ];
  edges.forEach((pts, k) => {
    const segP = clamp(p * 4 - k, 0, 1);
    if (segP > 0) brush(c, pts, { w: width, color, p: segP, seed: seed + k * 23, amp: 1.3, taper: .25 });
  });
}
// annotateCircle: organic hand-drawn loop around a box with natural marker overlap.
function annotateCircle(c, box, o = {}) {
  const { progress = 1, color = PAL.accents[0] || PAL.ink, width = 3, seed = 1, padding = 12, iterations = 2 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box), r = rng(seed);
  // Size the ellipse so the padded box CORNERS lie inside it: (a/rx)^2 + (b/ry)^2 <= 1. With ry = 1.8 b this gives
  // rx ~ 1.2 a, so the loop never cuts the first/last letters or stacked diacritics; the inward spiral is capped at 3%.
  const a = bw / 2 + padding, b = bh / 2 + padding * .5, cx = bx + bw / 2, cy = by + bh / 2;
  const ry = b * 1.8, rx = a / Math.sqrt(1 - (b / ry) ** 2) * 1.04;
  const steps = Math.max(48, Math.ceil(Math.PI * (rx + ry) * 1.3 / 16)), pts = [];
  const startA = -Math.PI * .65 + (r() - .5) * .2, sweep = TAU * (1.08 + .18 * (iterations - 1));
  const ph = r() * TAU, drift = .015 + r() * .015;   // phase drawn ONCE: per-point randomness makes the loop jagged
  for (let i = 0; i <= steps; i++) {
    const u = i / steps, a = startA + u * sweep;
    // slow, smooth wobble plus a gentle spiral: the second lap lands a little inside the first, like a real pen loop
    const radScale = 1 + .02 * Math.sin(u * TAU * 1.5 + ph) - drift * u;
    pts.push([cx + Math.cos(a) * rx * radScale, cy + Math.sin(a) * ry * radScale]);
  }
  brush(c, pts, { w: width, color, p, seed, amp: 1.8, taper: .4, smooth: false });
}
// annotateBracket: left, right, or both ('left' | 'right' | 'both') hand-drawn brackets around a block.
function annotateBracket(c, box, o = {}) {
  const { progress = 1, side = 'left', color = PAL.ink, width = 2.8, seed = 1, padding = 10, hook = 12 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box);
  const y0 = by - padding, y1 = by + bh + padding;
  const sides = side === 'both' ? ['left', 'right'] : [side];
  sides.forEach((s, idx) => {
    const x = s === 'right' ? bx + bw + padding : bx - padding;
    const hx = s === 'right' ? x - hook : x + hook;
    const pts = [[hx, y0], [x, y0], [x, (y0 + y1) / 2], [x, y1], [hx, y1]];
    brush(c, pts, { w: width, color, p, seed: seed + idx * 31, amp: 1.1, taper: .2, smooth: false });
  });
}
// annotateCrossedOff: two-stroke X strike-through across a box.
function annotateCrossedOff(c, box, o = {}) {
  const { progress = 1, color = PAL.accents[0] || PAL.ink, width = 3.2, seed = 1, padding = 4 } = o;
  const p = clamp(progress, 0, 1); if (p <= 0) return;
  const [bx, by, bw, bh] = _normBox(box);
  const x0 = bx - padding, y0 = by - padding, x1 = bx + bw + padding, y1 = by + bh + padding;
  const p1 = clamp(p * 2, 0, 1), p2 = clamp(p * 2 - 1, 0, 1);
  if (p1 > 0) brush(c, [[x0, y0], [(x0 + x1) / 2, (y0 + y1) / 2], [x1, y1]], { w: width, color, p: p1, seed, amp: 1.5, taper: .3 });
  if (p2 > 0) brush(c, [[x1, y0], [(x0 + x1) / 2, (y0 + y1) / 2], [x0, y1]], { w: width, color, p: p2, seed: seed + 17, amp: 1.5, taper: .3 });
}
