'use strict';
// character-hero.js — CHARACTER BIBLE dạng code: định nghĩa DUY NHẤT của nhân vật, dùng chung cho mọi shot,
// mọi file phân đoạn (phim dài) và model-sheet.html. Đổi tên thành character-<ten>.js cho nhân vật của bạn.
// Cần core.js + rig.js nạp trước. Không có thời gian trong file này: chỉ hình dáng, tỉ lệ, màu, khớp.
// Một bộ phận vẽ trong toạ độ cục bộ của xương nó (+x dọc xương). Seed hình (k.seed) cố định; chỉ nét viền boil (k.boil).

const limb = (len, w0, w1) => [[0, -w0], [len * .5, -(w0 + w1) * .55], [len, -w1], [len + w1 * .6, 0], [len, w1], [len * .5, (w0 + w1) * .55], [0, w0], [-w0 * .6, 0]];
function inkFill(c, pts, fill, k, w = 3.4) {
  const path = curvePath(pts); c.fillStyle = fill; c.fill(path);
  surface(c, path, [-200, -200, 400, 400], { seed: k.seed + 5 });
  c.strokeStyle = PAL.ink; c.lineWidth = w; wob(c, pts, 1.4, k.seed * 7 + k.boil, true, { pressure: .55 });
}
const HERO = defineRig({
  name: 'hero',
  bones: {
    root:   {},                                                  // gốc tại hông, trục y hướng xuống
    body:   { parent: 'root', rest: -Math.PI / 2, len: 150 },    // +x hướng lên theo thân
    head:   { parent: 'body', at: [150, 0], len: 90 },
    armF:   { parent: 'body', at: [118, -34], rest: Math.PI * .92, len: 64 },  // tay phía xa
    armN:   { parent: 'body', at: [118, 34], rest: Math.PI * 1.08, len: 64 },  // tay phía gần
    thighF: { parent: 'root', at: [-16, 0], rest: Math.PI / 2, len: 62 },
    shinF:  { parent: 'thighF', at: [62, 0], len: 60 },
    thighN: { parent: 'root', at: [16, 0], rest: Math.PI / 2, len: 62 },
    shinN:  { parent: 'thighN', at: [62, 0], len: 60 },
  },
  sockets: { footF: { bone: 'shinF', at: [60, 0] }, footN: { bone: 'shinN', at: [60, 0] } },
  parts: [
    // z: xa (âm) → thân (0) → đầu → gần (dương). Đổi lớp theo shot bằng pose.z, không đổi định nghĩa.
    { id: 'legF', bone: 'thighF', z: -3, hull: limb(62, 13, 11), draw: (c, k) => inkFill(c, limb(62, 13, 11), shade(PAL.fills[2] || '#7a8fa6', .15), k) },
    { id: 'shinF', bone: 'shinF', z: -3, hull: limb(60, 11, 9), draw: (c, k) => inkFill(c, limb(60, 11, 9), shade(PAL.fills[2] || '#7a8fa6', .15), k) },
    { id: 'armF', bone: 'armF', z: -2, hull: limb(64, 11, 8), draw: (c, k) => inkFill(c, limb(64, 11, 8), shade(PAL.fills[1] || '#ffcc00', .2), k, 3) },
    { id: 'body', bone: 'body', z: 0, hull: blob(80, 0, 88, 66, 11, { amp: .06 }),
      draw: (c, k) => inkFill(c, blob(80, 0, 88, 66, 11, { amp: .06 }), PAL.fills[1] || '#ffcc00', k, 4.2) },
    { id: 'head', bone: 'head', z: 1, hull: blob(40, 0, 52, 46, 23, { amp: .05 }),
      draw: (c, k) => {
        inkFill(c, blob(40, 0, 52, 46, 23, { amp: .05 }), PAL.fills[3] || '#ffe7c7', k, 4);
        const look = k.pose.look || 0;                            // mắt: lòng trắng + đồng tử + điểm sáng
        for (const ey of [-16, 16]) {
          c.fillStyle = '#fffdf8'; c.fill(curvePath(ellPts(46, ey, 13, 10)));
          c.fillStyle = PAL.ink; c.fill(curvePath(ellPts(46 + look * 3, ey + look * 4, 6, 5.5)));
          c.fillStyle = '#fff'; c.fill(curvePath(ellPts(49 + look * 3, ey + look * 4 - 2, 1.8, 1.8, 0, 12)));
        }
      } },
    { id: 'legN', bone: 'thighN', z: 2, hull: limb(62, 13, 11), draw: (c, k) => inkFill(c, limb(62, 13, 11), PAL.fills[2] || '#7a8fa6', k) },
    { id: 'shinN', bone: 'shinN', z: 2, hull: limb(60, 11, 9), draw: (c, k) => inkFill(c, limb(60, 11, 9), PAL.fills[2] || '#7a8fa6', k) },
    { id: 'armN', bone: 'armN', z: 3, hull: limb(64, 11, 8), draw: (c, k) => inkFill(c, limb(64, 11, 8), PAL.fills[1] || '#ffcc00', k, 3) },
  ],
});

// Các tư thế khó nhất để duyệt trên model sheet TRƯỚC khi dựng shot (render model-sheet.html --only 0, mở ảnh, sửa).
const HERO_SHEET = [
  { label: 'đứng nghỉ', pose: { angles: {} } },
  { label: 'bước — chân gần trước', pose: { angles: { thighN: -.5, shinN: .5, thighF: .35, shinF: .3, armN: .5, armF: -.5 } } },
  { label: 'lấy đà (anticipation)', pose: { angles: { body: .25, head: -.2, thighN: -.9, shinN: 1.4, thighF: -.7, shinF: 1.2, armN: .9, armF: .7 } } },
  { label: 'nhảy — duỗi', pose: { angles: { body: -.1, head: .15, thighN: -.2, shinN: .1, thighF: .3, shinF: .2, armN: -2.2, armF: -2.0 } } },
  { label: 'quay lưng (flip)', pose: { flip: true, angles: { armN: .3 } } },
  { label: 'ngạc nhiên', pose: { look: -1, angles: { head: .25, armN: -1.2, armF: -1.0 } } },
];
