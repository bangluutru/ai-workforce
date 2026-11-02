# Character rig: một nhân vật, một định nghĩa, mọi shot

File này BẮT BUỘC đọc khi phim có nhân vật chính có tay, chân, cánh, cổ hoặc đạo cụ có khớp (xe, cửa, cần câu).
Engine: [`assets/rig.js`](../assets/rig.js). Khung mẫu: [`assets/character-hero.js`](../assets/character-hero.js),
[`assets/model-sheet.html`](../assets/model-sheet.html). Ví dụ đầy đủ:
[`examples/pelican-rig/`](../examples/pelican-rig/) (bồ nông đạp xe, 10 s, 2 rig, IK chân vào bàn đạp, cánh vỗ quanh vai).

## 0. Bệnh án: vì sao nhân vật bị "trôi"

Bản lỗi thật (bồ nông đạp xe, 20 s, qua `qa.mjs` với 0 FAIL nhưng xem thì kém):

| Triệu chứng nhìn thấy | Nguyên nhân trong code | Cách sửa |
|---|---|---|
| Cánh biến thành tờ giấy trắng che mặt | cánh vẽ bằng cách cộng độ lệch vào từng điểm polygon (kéo giãn), vẽ SAU đầu | cánh là xương có khớp vai; bộ phận cứng trong toạ độ xương; `z` cánh gần < `z` đầu |
| Chân rời bàn đạp, trôi nổi | IK có, nhưng không ai đo chân có chạm bàn đạp không; chân ngắn hơn khoảng yên→bàn đạp | `pins` foot→pedal; `qa.mjs` FAIL khi lệch quá dung sai |
| Mỏ, mắt, tỉ lệ đổi giữa các cảnh | mỗi shot gọi hàm vẽ với tham số tự đặt; seed hình dáng đổi theo thời gian | một `defineRig()`; seed hình cố định; chỉ nét viền boil (`rigBoil`) |
| Xe không nằm trên mặt dốc | độ nghiêng xe đặt tay theo shot, đường là hàm khác | đặt xe từ 2 điểm chạm bánh trên `roadY(x)`; pin bánh trước xuống đường |
| QA báo "đạt" | `markFocus` nhận khung chữ nhật cố định → `subject` luôn ~49% | `drawRig` tự đăng ký hull thật; `qa.mjs` FAIL `box-focus` |

Quy tắc gốc: **vẽ nhân vật một lần, diễn bằng pose.** Shot không bao giờ vẽ lại hình dáng nhân vật.

## 1. Khi nào dùng rig, khi nào dùng cels

| Trường hợp | Chọn |
|---|---|
| Nhân vật xuất hiện ≥ 2 shot, có chi/khớp, cần giữ giống nhau (mặc định cho phim kể chuyện) | **rig** (`rig.js`) |
| Tương tác vật lý: chân–bàn đạp, tay–cán, bánh–đường, đứng trên dốc | **rig + pins + `rigIK`** |
| Biến hình lớn, co giãn cảm xúc mạnh, phong cách pencil "vẽ lại từng tư thế" | **cels** (`cels.js`, `redrawn-animation.md`) |
| Thân dài uốn lượn (cá, rồng, rắn, khăn) | **spine + width profile** (playbook §6) — gắn vào một xương của rig nếu cần |

Kết hợp được: rig cho thân và chi; một bộ phận (mặt, bàn tay) đổi bản vẽ bằng `slot` + `pose.swap` (replacement animation).

## 2. Character bible = file `character-<ten>.js`

Một file riêng, không chứa thời gian, nạp sau `core.js` + `rig.js`. Mọi shot, mọi file phân đoạn (phim dài)
và `model-sheet.html` nạp CÙNG file này. Đầu file ghi bất biến bằng lời (tỉ lệ, màu, phụ kiện, thứ tự lớp).

```js
const HERO = defineRig({
  name: 'hero',
  bones: {                                   // +x của mỗi xương = hướng xương; at = vị trí khớp trong toạ độ xương cha
    root: {},
    body:  { parent: 'root', rest: -Math.PI / 2, len: 150 },
    thighN: { parent: 'root', at: [16, 0], rest: Math.PI / 2, len: 62 },
    shinN:  { parent: 'thighN', at: [62, 0], len: 60 },          // xương dưới treo ở ĐÚNG đầu xương trên: [len_trên, 0]
  },
  sockets: { footN: { bone: 'shinN', at: [60, 0] } },             // điểm có tên: IK, pin, gắn đạo cụ
  parts: [                                   // vẽ trong toạ độ CỤC BỘ của xương → xoay theo khớp, không kéo giãn
    { id: 'body', bone: 'body', z: 0, hull: BODY_PTS, draw: (c, k) => inkFill(c, BODY_PTS, PAL.fills[1], k) },
  ],
});
```

- **`hull`** (bắt buộc với bộ phận chính): đường bao thô trong toạ độ xương. `drawRig` dùng nó để đo cỡ nhân vật
  thật trên màn hình (`qa.mjs` cột `subject`) và để `render.mjs --crops` cắt cận nhân vật.
- **`k.seed`** cố định theo bộ phận, **`k.boil`** = `rigBoil(T)` đổi theo nhịp twos. Chỉ dùng `k.boil` cho seed của
  `wob()` (nét viền) và `hatch()`. KHÔNG đưa thời gian vào `blob()`, `curvePath()`, `ellPts()`: silhouette sẽ nhảy.
- **Tham số biểu cảm** (túi mỏ phồng, nheo mắt, khăn bay) đọc từ `k.pose.<tên>` và là hình dáng có thiết kế
  (0 → 1), không phải nhiễu.
- **`z` = thứ tự lớp**: xa (âm) → thân (0) → đầu → gần (dương). Chi/cánh phía gần mặt phải có `z` NHỎ hơn đầu
  để không bao giờ che mặt. Đổi tạm theo shot bằng `pose.z = { wingN: 5 }`, không sửa định nghĩa.
- **Đạo cụ có khớp** (xe đạp, xe đẩy, cánh cửa) là một rig riêng. Nhân vật và đạo cụ nối với nhau bằng socket + IK + pin.
  Lớp xen kẽ: `drawRig(nhânVật, {only: p => p.z < 0})` → `drawRig(đạoCụ)` → `drawRig(nhânVật, {only: p => p.z >= 0})`.

## 3. Pose, IK và pins

```js
function drawHero(c, T) {
  const pose = { x: heroX(T), y: GROUND - 108, boil: rigBoil(T), angles: { head: Math.sin(T * 2) * .05 } };
  const foot = [heroX(T) + 20, GROUND];
  rigIK(HERO, pose, 'thighN', 'shinN', foot, 1);                    // bend = ±1 chọn phía gập gối
  drawRig(c, HERO, pose, { T, pins: [{ socket: 'footN', to: foot, tol: 3 }] });
}
```

- Vị trí nhân vật là hàm của **thời gian phim T**, không phải `tau` của shot → liên tục qua vết cắt.
- Mọi trạng thái (pose, vị trí cá đang bay, xe trên dốc) là **hàm thuần của T**: `riderState(T)`. Cần vị trí ở thời
  điểm khác (điểm cá bắt đầu nảy) thì gọi lại hàm với T đó, không lưu state.
- **Pin mọi điểm chạm nhìn thấy được**: chân–đất, chân–bàn đạp, tay–cán, bánh–đường, mông–ghế. Dung sai 3–4 đơn vị.
  `qa.mjs` vẽ dày các frame và FAIL `contact` kèm frame, scene, số px. Chi duỗi quá tầm không bị kéo dài, nên sai số
  hiện ra ở pin. Khi đó sửa thiết kế (chân dài hơn, hạ yên), không nới dung sai.
- Đặt vật có 2 điểm chạm (xe 2 bánh, ván trượt) bằng hình học: góc = `atan2` giữa hai điểm chạm trên mặt đường,
  rồi pin điểm thứ hai. Không đặt góc nghiêng bằng tay theo shot.
- Chuyển chế độ (cầm ghi đông → vỗ cánh): tính pose IK "cầm" rồi `lerp` sang pose "vỗ" theo trọng số có easing.
  Pin chỉ áp ở chế độ có chạm.

## 4. Model sheet: duyệt nhân vật TRƯỚC khi dựng shot

1. Copy `assets/model-sheet.html` vào `<process_dir>`; đổi tên file character và biến (`HERO`, `HERO_SHEET`).
2. Liệt kê 4–6 tư thế KHÓ NHẤT của phim (vỗ cánh cao nhất, đớp mồi, gắng sức, quay hướng) trong `<TEN>_SHEET`.
3. `node scripts/render.mjs <process_dir>/model-sheet.html --only 0,1 --out <process_dir>/preview`
   → frame 0 = bản vẽ, frame 1 = có xương/khớp (xanh). **MỞ CẢ HAI ẢNH** (`view_file`).
4. Kiểm: silhouette đọc được, tỉ lệ đúng bible, khớp xoay đúng chỗ (vai, hông, gối), không bộ phận nào che mặt,
   chi đủ dài cho mọi điểm chạm (đo: khoảng hông→bàn đạp xa nhất < đùi + cẳng).
5. Sửa trong `character-<ten>.js`, render lại. Chỉ dựng shot khi model sheet đạt. Lưu ảnh model sheet cuối cạnh phim.

Model sheet in mã `sig` của rig. `qa.mjs` FAIL `rig-drift` khi một rig cùng tên xuất hiện với 2 `sig` khác nhau
(có shot định nghĩa lại nhân vật).

## 5. Crop review mỗi vòng

`node scripts/render.mjs <film> --crops 12 --out <process_dir>/preview` → `<film>-crops.jpg`: 12 ảnh cận nhân vật
(theo hull thật), nhãn đỏ khi pin trượt hoặc không có vùng chủ thể. Grid toàn khung quá nhỏ để thấy cánh che mặt
hay chân rời bàn đạp; crop sheet thì thấy. Mỗi vòng review mở cả grid lẫn crop sheet.

Debug: đặt `window.__debugBones = true` trong film (chỉ khi debug) để vẽ xương và pin bằng `drawRigBones`.

## 6. API (`assets/rig.js`)

```js
defineRig({ name, bones: {id: {parent?, at?, rest?, len?}}, parts: [{id, bone, z, hull, draw(c, k), slot?, default?}], sockets: {id: {bone, at}}, unit? }) → rig
poseRig(rig, pose) → {boneId: matrix}          rigPoint(rig, pose, socketId) → [x, y] (không gian hiện tại)
rigIK(rig, pose, upperBone, lowerBone, target, bend = 1, endSocket?) → pose (ghi pose.angles)
drawRig(c, rig, pose, { pins: [{socket, to, tol}], focus = true, only: part => bool, T })
drawRigBones(c, rig, pose, pins)               rigBoil(T, hold = 3, cycle = 3)
drawModelSheet(c, rig, [{label, pose, pins?}], { cols, bones, ground, title })
// pose = { x, y, rot, scale, flip, angles: {bone: rad}, z: {part: z}, swap: {slot: partId}, hide: [partId], boil, ...tham số biểu cảm }
// k (đối số thứ 2 của draw) = { seed, boil, pose, rig, T, part }
```
