'use strict';
// character-pelican.js — CHARACTER BIBLE (code): bồ nông thủy thủ + xe đạp bạc hà. Định nghĩa DUY NHẤT, dùng chung cho
// mọi shot và model sheet. Bất biến: mỏ dài ≈ 1.2 lần thân, mũ thủy thủ viền xanh, khăn đỏ, chân cam, xe bạc hà bánh 70.
// Thứ tự lớp: cánh xa → chân xa → [XE] → chân gần → thân → cổ/khăn → cánh gần → đầu (cánh không bao giờ che mặt).

const COL = { white: '#fbf7ef', shadeW: '#cfd8e6', orange: '#f29a4a', orangeD: '#d9772d', red: '#e2483f', navy: '#2d3f73',
  mint: '#7fd3bf', mintD: '#4fa894', tire: '#2b2a33', wicker: '#c99a5b', fish: '#9fb7cf' };

function pelShape(c, pts, fill, k, w = 3.6, amp = 1.2) {
  const path = curvePath(pts); c.fillStyle = fill; c.fill(path);
  c.strokeStyle = PAL.ink; c.lineWidth = w; wob(c, pts, amp, k.seed * 7 + k.boil, true, { pressure: .55 });
  return path;
}
function pelLine(c, pts, w, k, col = PAL.ink, sub = 0) {
  c.strokeStyle = col; c.lineWidth = w; wob(c, pts, 1, k.seed * 11 + sub * 3 + k.boil, false, { pressure: .45 });
}
// tapered limb outline along +x
const taper = (len, w0, w1, tip = .6) => [[0, -w0], [len * .5, -(w0 + w1) * .55], [len, -w1], [len + w1 * tip, 0], [len, w1], [len * .5, (w0 + w1) * .55], [0, w0], [-w0 * .7, 0]];

// ---------------- XE ĐẠP (gốc = trục giữa/BB; mặt đường dưới trục bánh 70 đơn vị) ----------------
const WHEEL_R = 70, HUB_R = [-118, -12], HUB_F = [112, -12];
function wheelDraw(c, k) {
  c.strokeStyle = PAL.ink; c.lineWidth = 1.6;
  for (let s = 0; s < 12; s++) { const a = s / 12 * TAU; pelLine(c, [[0, 0], [Math.cos(a) * 62, Math.sin(a) * 62]], 1.4, k, '#5b5866', s); }
  c.strokeStyle = COL.tire; c.lineWidth = 11; c.beginPath(); c.stroke(curvePath(ellPts(0, 0, WHEEL_R - 5, WHEEL_R - 5, 0, 36)));
  c.strokeStyle = '#d9d4cc'; c.lineWidth = 2.5; c.stroke(curvePath(ellPts(0, 0, WHEEL_R - 11, WHEEL_R - 11, 0, 36)));
  c.fillStyle = '#e8e2d6'; c.fill(curvePath(ellPts(0, 0, 8, 8, 0, 14)));
  c.strokeStyle = PAL.ink; c.lineWidth = 3; wob(c, ellPts(0, 0, WHEEL_R, WHEEL_R, 0, 40), 1, k.seed * 7 + k.boil, true, { pressure: .4 });
}
function tube(c, a, b, k, sub, w = 9) { pelLine(c, [a, b], w + 4, k, PAL.ink, sub); c.strokeStyle = COL.mint; c.lineWidth = w; c.beginPath(); c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); c.stroke(); }
const BIKE = defineRig({
  name: 'bike',
  bones: { frame: {}, wheelR: { parent: 'frame', at: HUB_R, len: WHEEL_R }, wheelF: { parent: 'frame', at: HUB_F, len: WHEEL_R }, crank: { parent: 'frame', len: 30 } },
  sockets: { hubR: { bone: 'frame', at: HUB_R }, hubF: { bone: 'frame', at: HUB_F }, pedalN: { bone: 'crank', at: [30, 0] }, pedalF: { bone: 'crank', at: [-30, 0] },
    seat: { bone: 'frame', at: [-34, -116] }, bar: { bone: 'frame', at: [70, -156] }, basket: { bone: 'frame', at: [134, -132] } },
  parts: [
    { id: 'wheelR', bone: 'wheelR', z: 0, hull: ellPts(0, 0, WHEEL_R, WHEEL_R, 0, 12), draw: wheelDraw },
    { id: 'wheelF', bone: 'wheelF', z: 0, hull: ellPts(0, 0, WHEEL_R, WHEEL_R, 0, 12), draw: wheelDraw },
    { id: 'frame', bone: 'frame', z: 1, hull: [[-118, -12], [-36, -134], [140, -150], [112, -12], [0, 0]], draw: (c, k) => {
      tube(c, HUB_R, [0, 0], k, 1, 7); tube(c, HUB_R, [-30, -112], k, 2, 7); tube(c, [0, 0], [-34, -112], k, 3);
      tube(c, [-32, -108], [84, -118], k, 4); tube(c, [0, 0], [86, -104], k, 5, 10); tube(c, [84, -122], HUB_F, k, 6, 7);
      tube(c, [84, -122], [80, -150], k, 7, 6); pelLine(c, [[80, -150], [66, -158], [52, -152]], 6, k, PAL.ink, 8);   // cổ lái + ghi đông
      pelShape(c, [[-60, -124], [-18, -128], [-8, -118], [-46, -114]], '#6b4a3a', k, 3);                                   // yên
      pelShape(c, [[104, -146], [158, -146], [152, -112], [110, -112]], COL.wicker, k, 3);                                  // giỏ
      for (let i = 0; i < 4; i++) pelLine(c, [[108 + i * 12, -144], [112 + i * 11, -114]], 1.4, k, '#8a6436', 10 + i);
      c.strokeStyle = PAL.ink; c.lineWidth = 2.4; c.beginPath(); c.stroke(curvePath(ellPts(0, 0, 22, 22, 0, 24)));        // đĩa xích
    } },
    { id: 'crank', bone: 'crank', z: 2, hull: [[-34, -6], [34, -6], [34, 6], [-34, 6]], draw: (c, k) => {
      pelLine(c, [[-30, 0], [30, 0]], 5, k, '#3d3a45');
      for (const x of [-30, 30]) pelShape(c, [[x - 13, -4], [x + 13, -4], [x + 13, 4], [x - 13, 4]], '#3d3a45', k, 2, .5);
    } },
  ],
});

// ---------------- BỒ NÔNG (gốc = xương chậu, đặt tại yên) ----------------
// cánh: bản rộng, đầu cánh 3 lông chính dạng vỏ sò (không phải răng lược)
const featherWing = (len, w) => [[0, -w * .5], [len * .6, -w * .66], [len + 6, -w * .5], [len + 30, -w * .28], [len + 14, -w * .08], [len + 32, w * .06], [len + 12, w * .22], [len + 24, w * .42], [len * .7, w * .6], [len * .3, w * .62], [0, w * .45]];
const PEL_BODY = [[-34, 4], [-20, -40], [30, -58], [92, -46], [132, -18], [134, 22], [96, 58], [30, 66], [-18, 48]];
const PELICAN = defineRig({
  name: 'pelican',
  bones: {
    pelvis: {},
    body: { parent: 'pelvis', rest: -1.0, len: 128 },
    neck: { parent: 'body', at: [122, 6], rest: -.62, len: 66 },
    head: { parent: 'neck', at: [66, 0], rest: 1.62, len: 34 },
    tail: { parent: 'body', at: [-24, 8], rest: Math.PI + .35, len: 40 },
    thighF: { parent: 'pelvis', at: [-6, 6], rest: 1.1, len: 74 }, shinF: { parent: 'thighF', at: [74, 0], len: 78 },
    thighN: { parent: 'pelvis', at: [8, 10], rest: 1.1, len: 74 }, shinN: { parent: 'thighN', at: [74, 0], len: 78 },
    wingFU: { parent: 'body', at: [96, -12], rest: 1.9, len: 66 }, wingFL: { parent: 'wingFU', at: [66, 0], len: 62 },
    wingNU: { parent: 'body', at: [100, 4], rest: 1.9, len: 66 }, wingNL: { parent: 'wingNU', at: [66, 0], len: 62 },
  },
  sockets: { footF: { bone: 'shinF', at: [78, 0] }, footN: { bone: 'shinN', at: [78, 0] }, handF: { bone: 'wingFL', at: [62, 0] }, handN: { bone: 'wingNL', at: [62, 0] },
    pouch: { bone: 'head', at: [70, 26] } },
  parts: [
    { id: 'wingFU', bone: 'wingFU', z: -6, hull: taper(66, 20, 16), draw: (c, k) => pelShape(c, taper(66, 20, 16), COL.shadeW, k, 3) },
    { id: 'wingFL', bone: 'wingFL', z: -6, hull: featherWing(62, 40), draw: (c, k) => pelShape(c, featherWing(62, 40), COL.shadeW, k, 3) },
    { id: 'thighF', bone: 'thighF', z: -5, hull: taper(74, 20, 10), draw: (c, k) => pelShape(c, taper(74, 20, 10), COL.shadeW, k, 3) },
    { id: 'shinF', bone: 'shinF', z: -5, hull: taper(78, 6, 5), draw: (c, k) => { pelShape(c, taper(78, 6, 5), COL.orangeD, k, 2.4); pelShape(c, [[70, -4], [98, -14], [100, 10], [72, 6]], COL.orangeD, k, 2.4); } },
    { id: 'tail', bone: 'tail', z: -1, hull: [[0, -16], [44, -24], [50, 0], [44, 22], [0, 16]], draw: (c, k) => pelShape(c, [[0, -16], [44, -24], [36, -6], [50, 0], [36, 8], [44, 22], [0, 16]], COL.white, k, 3) },
    { id: 'thighN', bone: 'thighN', z: 1, hull: taper(74, 22, 11), draw: (c, k) => pelShape(c, taper(74, 22, 11), COL.white, k, 3.4) },
    { id: 'shinN', bone: 'shinN', z: 1, hull: taper(78, 6.5, 5), draw: (c, k) => { pelShape(c, taper(78, 6.5, 5), COL.orange, k, 2.6); pelShape(c, [[70, -5], [100, -16], [102, 11], [72, 7]], COL.orange, k, 2.6); } },
    { id: 'body', bone: 'body', z: 2, hull: PEL_BODY, draw: (c, k) => {
      const p = pelShape(c, PEL_BODY, COL.white, k, 4.4);
      c.save(); c.clip(p); c.fillStyle = COL.shadeW; c.fill(curvePath([[-40, 20], [40, 30], [120, 10], [140, 70], [-40, 80]]));
      hatch(c, p, [-40, -60, 180, 130], { angle: .6, gap: 9, color: PAL.ink, alpha: .18, width: 1.2, seed: k.seed + k.boil }); c.restore();
      pelLine(c, [[60, -30], [80, -10], [72, 18]], 2, k, PAL.ink, 1);                                           // vai
    } },
    { id: 'neck', bone: 'neck', z: 3, hull: taper(66, 22, 17), draw: (c, k) => {
      pelShape(c, taper(70, 22, 17), COL.white, k, 3.6);
      const wv = k.pose.wind || 0, ph = k.pose.windPh || 0;                                                     // khăn đỏ + đuôi khăn bay theo gió (tham số pose, không phải seed)
      pelShape(c, [[2, -26], [24, -24], [26, 24], [4, 28]], COL.red, k, 3);
      const tail = [0, 1, 2, 3].map(i => [8 - i * 18 * (.4 + wv), 26 + i * 10 + Math.sin(ph + i * 1.3) * 8 * wv]);
      pelShape(c, [...tail, ...tail.slice().reverse().map(([x, y], i) => [x - 4, y + 12 - i * 2])], COL.red, k, 2.6);
    } },
    { id: 'wingNU', bone: 'wingNU', z: 3.5, hull: taper(66, 22, 17), draw: (c, k) => pelShape(c, taper(66, 22, 17), COL.white, k, 3.4) },
    { id: 'wingNL', bone: 'wingNL', z: 3.5, hull: featherWing(62, 42), draw: (c, k) => {
      const p = pelShape(c, featherWing(62, 42), COL.white, k, 3.4);
      c.save(); c.clip(p); hatch(c, p, [0, -30, 90, 60], { angle: -.4, gap: 8, color: '#7d93b5', alpha: .35, width: 1.1, seed: k.seed }); c.restore();
    } },
    { id: 'head', bone: 'head', z: 4, hull: [[-30, -40], [30, -36], [150, 2], [140, 30], [20, 34], [-28, 20]], draw: (c, k) => {
      const pouch = k.pose.pouch || 0, open = k.pose.mouth || 0;
      // túi mỏ (dưới) → mỏ trên → đầu → mắt → mũ
      pelShape(c, [[14, 10], [70, 18 + pouch * 34 + open * 10], [136, 14 + open * 8], [146, 10 + open * 6], [120, 8], [20, 4]], COL.orange, k, 3.2);
      if (pouch > .5) pelLine(c, [[56, 22 + pouch * 20], [62, 30 + pouch * 22], [74, 26 + pouch * 20]], 2, k, COL.orangeD, 2);
      pelShape(c, [[10, -14], [80, -10], [146, -2], [154, 8], [140, 10], [80, 4], [12, 6]], '#f6b25a', k, 3.2);
      pelShape(c, [[-30, -6], [-26, -32], [2, -40], [26, -28], [30, 6], [10, 20], [-20, 18]], COL.white, k, 3.8);
      const sq = k.pose.squint || 0;
      c.fillStyle = '#fffdf8'; c.fill(curvePath(ellPts(8, -12, 9, 8 * (1 - sq * .6))));
      if (sq < .8) { c.fillStyle = PAL.ink; c.fill(curvePath(ellPts(11, -12, 4.5, 4.5 * (1 - sq * .6)))); c.fillStyle = '#fff'; c.fill(curvePath(ellPts(12.5, -14, 1.4, 1.4, 0, 10))); }
      pelLine(c, [[-2, -22 - sq * 3], [10, -24], [20, -20 + sq * 4]], 2.2, k, PAL.ink, 3);                       // lông mày
      pelShape(c, [[-30, -30], [-26, -48], [18, -52], [26, -34]], COL.white, k, 3);                             // mũ thủy thủ
      pelShape(c, [[-32, -30], [28, -34], [28, -26], [-32, -22]], COL.navy, k, 2.4);
      c.fillStyle = COL.red; c.fill(curvePath(ellPts(-4, -54, 6, 5)));
    } },
  ],
});

// tư thế chuẩn để duyệt model sheet (không có thời gian trong file này)
const PEL_SHEET_POSES = [
  { label: 'ngồi — cánh giữ ghi đông', pose: { angles: {} } },
  { label: 'vỗ cánh lên', pose: { angles: { wingNU: -3.1, wingNL: .5, wingFU: -2.9, wingFL: .45 }, wind: 1 } },
  { label: 'vỗ cánh ngang', pose: { angles: { wingNU: -1.9, wingNL: .1, wingFU: -1.7, wingFL: .1 }, wind: 1 } },
  { label: 'đớp cá — túi phồng', pose: { pouch: 1, mouth: .2, angles: { head: -.2, neck: .15 } } },
  { label: 'gắng sức leo dốc', pose: { squint: 1, angles: { body: .35, neck: .35, head: -.3 } } },
  { label: 'mãn nguyện — dang cánh', pose: { angles: { body: -.12, neck: -.12, head: -.1, wingNU: -2.5, wingNL: .3, wingFU: -2.3, wingFL: .3 }, wind: .4 } },
];
