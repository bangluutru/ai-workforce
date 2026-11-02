---
name: hand-drawn-animation
display-name: Tạo Hoạt Hình
description: >-
  Tạo phim hoạt hình vẽ tay chất lượng cao bằng Canvas 2D với 5 phong cách nghệ thuật (ink, riso, screen, pencil, doodle), rotoscope, sand animation, và hiệu ứng pop-up paper 3D; có câu chuyện, bố cục, diễn xuất, âm thanh; xuất HTML player và video MP4 offline.
  USE WHEN: Người dùng muốn sáng tạo hoạt hình nghệ thuật vẽ tay, phim hoạt họa 2D ngắn, hoặc hiệu ứng minh họa đồ họa động.
  DO NOT USE WHEN: Cần dựng video thực tế với stock footage người thật (dùng 'video-studio'), chỉ làm phụ đề video (dùng 'phu-de'), hoặc chỉ thuyết minh/lồng tiếng (dùng 'long-tieng').
trigger: Hoạt hình vẽ tay, hand drawn animation, canvas animation, phim hoạt hình, doodle animation
category: content
needs_file: false
file_filter: any
---

# 🎨 Hand-Drawn Animation — Phim Hoạt Hình Vẽ Tay

> **Nguồn gốc**: [alesha-pro/tools](https://github.com/alesha-pro/tools/tree/main/skills/hand-drawn-canvas-animation) — MIT License © 2026 Alexey Fateev
> **Tích hợp AIWF**: Skill #14 · Bản v2.2: nhân vật dựng bằng rig (`rig.js`: khung xương, IK, ghim điểm chạm), model sheet + crop review bắt buộc, QA bắt lỗi điểm chạm/nhân vật trôi, đường làm phim dài (phân đoạn, sổ liên tục, render theo đoạn). Bản v2.1: `starter.html`, đa phong cách, `qa.mjs`.

<goal>
Giao một phim ngắn mà người xem thấy ĐẸP: có câu chuyện (mục tiêu → trở ngại → thay đổi),
bố cục có chủ đích, nhân vật được thiết kế, nét vẽ tay thật, chất liệu đúng phong cách,
diễn xuất có anticipation/reaction, âm thanh khớp hình. Render thành công chỉ là điều kiện
cần; tiêu chuẩn là kết quả nhìn thấy trên ảnh render.
</goal>

---

## 1. Năng lực

| Thành phần | Chi tiết |
|---|---|
| Renderer | Canvas 2D thuần JavaScript, không WebGL/Blender/AI video |
| Đầu ra | HTML player (xem/scrub/có tiếng) + MP4 1080p 24 fps + WAV score |
| Phong cách | ink (`paperInk`), riso (`risoPop`/plates), screen (`screenSea`), pencil (`pencilMinimal`), doodle (`doodlePastel`) |
| Engine mở rộng | rotoscope (`roto.js`), sand (`sand.js`), pop-up paper 3D (`paper3d.js`) |
| Nhân vật nhất quán | `rig.js`: một định nghĩa nhân vật (xương + bộ phận cứng + socket), IK hai xương, ghim điểm chạm (chân–bàn đạp, bánh–đường) được QA đo; model sheet; crop sheet cận nhân vật |
| Phim dài | `long-film.html` + `seq-XX.js`: một timeline, một score, xem trước/QA từng phân đoạn (`--seq`), render theo đoạn vào cache (`--range`) rồi ghép (`--assemble`) |
| Dependencies | Node ≥ 22, Chrome, ffmpeg; `cd scripts && npm i --no-audit --no-fund` (auto-setup đã cài) |

## 2. Tài liệu phải đọc (đọc TRƯỚC khi viết code)

| Thứ tự | File | Bắt buộc? | Vì sao |
|---|---|---|---|
| 1 | `references/craft-playbook.md` | **Luôn luôn** | Bệnh án phim xấu + nguyên lý bố cục, nhân vật, diễn xuất, camera, review |
| 2 | `assets/starter.html` | **Luôn luôn** | Khung khởi tạo chuẩn (Neutral Starter Skeleton) sạch, 16:9, sẵn timeline `defineFilm`, camera `applyView`, `markFocus` và audio synth |
| 3 | `references/style.md` | **Luôn luôn** | Chuẩn 5 phong cách thị giác (doodle, pencil, screen, ink, riso) và quality gate |
| 3b | `references/character-rig.md` | **Khi có nhân vật có chi/khớp hoặc đạo cụ có khớp** (gần như mọi phim kể chuyện) | Bệnh án "nhân vật trôi", rig, IK, pin điểm chạm, model sheet, crop review. Ví dụ: `examples/pelican-rig/` |
| 3c | `references/long-form.md` | **Khi phim > 30 s hoặc > 6 shot** | Cấu trúc nhiều file, sổ liên tục, xem trước/QA/render theo phân đoạn |
| 4 | Phim mẫu theo phong cách | Chọn 1 file theo đề tài | • **Doodle / Explainer / Hài hước**: `references/doodle.md` + `examples/four-looks.html`<br>• **Pencil / Sổ tay / Sinh học**: `examples/sketchbook-bird.html` + `references/redrawn-animation.md`<br>• **Screen / Poster / Retro**: `examples/four-looks.html` (đoạn screen)<br>• **Ink / Thư pháp cổ điển**: `examples/fly-style.html`<br>• **Riso 3 bản in kẽm Á Đông**: `examples/koi-dragon.html` (case study in Riso)<br>• **Tranh cát / Pop-up 3D**: `examples/one-year.html` (`sand.js`), `examples/material-studies.html` (`paper3d.js`) |

Được phép đọc mã nguồn `assets/*.js` khi cần biết chính xác một hàm. API tóm tắt ở §7 đã
được đối chiếu với mã nguồn.

## 3. Tiếp nhận đầu vào (Intake)

Điền brief (mẫu `references/brief-template.md`) — suy luận các lựa chọn thường lệ, chỉ hỏi
khi thiếu quyết định thật sự đổi kết quả:

1. **Chủ đề + nhịp cảm xúc** (ví dụ: thử – thất bại – thử lại – thắng – biến đổi).
2. **Thời lượng**: mặc định 18–25 s (4–6 shot). > 30 s → đường phim dài (`long-form.md`). **Tỷ lệ**: mặc định 16:9, 1920 px.
3. **Look**: ink | riso | screen | pencil | doodle. Không nêu → chọn look hợp đề tài và ghi lý do.
4. **Ảnh/video tham chiếu** (nếu có) cho doodle hoặc rotoscope.
5. **Chữ trên màn hình** (tiêu đề cuối...) và ngôn ngữ.

## 4. Quy trình sản xuất (Quality Path)

<instructions>

**Thư mục làm việc:** `<process_dir>` = `<workspace>/_process/<ten_phim>/` (đã gitignore).
Film HTML nằm trong `<process_dir>` cùng bản copy `assets/*.js`. Thành phẩm cuối ở
`<output_dir>/<ten_phim>/`. Các lệnh `scripts/...` dưới đây chạy với đường dẫn
`.agents/skills/hand-drawn-animation/scripts/...` từ `<workspace>`.

**B1 — Kịch bản & beat sheet.** Viết comment BRIEF + BEAT SHEET ở đầu file film
(start · dur · khán giả chú ý gì · hành động · camera · âm thanh). Bắt buộc có: thiết lập,
trở ngại/thất bại, cao trào, kết giữ ≥ 1.5 s.

**B2 — Khởi tạo từ Neutral Starter Skeleton.**
```bash
mkdir -p <process_dir> && cp .agents/skills/hand-drawn-animation/assets/*.js <process_dir>/
cp .agents/skills/hand-drawn-animation/assets/starter.html <process_dir>/<ten_phim>.html      # phim > 30 s: assets/long-film.html
cp .agents/skills/hand-drawn-animation/assets/model-sheet.html <process_dir>/
mv <process_dir>/character-hero.js <process_dir>/character-<ten>.js   # rồi sửa <script src> trong film + model-sheet
```
Giữ cấu trúc kiến trúc chuẩn:
- **PALETTE**: Chọn look tự do (`doodlePastel`, `pencilMinimal`, `screenSea`, `paperInk`, `risoPop`).
- **WORLD & BACKDROP**: Dựng bối cảnh thế giới với ≥ 3 lớp chiều sâu (xa, trung cảnh, tiền cảnh).
- **CHARACTER & PROPS**: Thiết kế hình thể tự nhiên bằng `blob`, `curvePath`, `cels`, bắt buộc gọi `markFocus(c, outlinePts)`. Tuyệt đối không bị gò bó vào hình thể con cá hay rồng trừ khi đề tài yêu cầu.
- **CAMERA & PERFORMANCE**: Dùng `shotCam` tính toán vị trí, zoom, độ rung tay tự nhiên; áp dụng `applyView(c, cam)`.
- **AUDIO SCORE**: Tổng hợp âm thanh synthesizer theo phong cách phim (pop/acoustic vui tươi cho doodle; piano/ambient cho pencil; koto/taiko cho cổ trang Á Đông).
- **DEFINE FILM**: Khai báo timeline các cảnh và render loop qua `defineFilm`.
*(Lưu ý: `examples/koi-dragon.html` là case study nâng cao cho kỹ thuật in Riso 3 bản kẽm, chỉ tham khảo khi làm phong cách Riso Á Đông).*

**B3 — Character bible + model sheet (bắt buộc TRƯỚC khi dựng shot), rồi bối cảnh + 1 shot khó nhất.**
- Nhân vật có chi/khớp: viết `character-<ten>.js` bằng `defineRig()` (xương, bộ phận cứng trong toạ độ xương, `hull`,
  socket, thứ tự lớp `z`: xa → thân → đầu → gần; chi/cánh phía gần có `z` nhỏ hơn đầu). Một định nghĩa cho cả phim.
  Chi tiết + bệnh án: `references/character-rig.md`. Biến hình lớn / pencil vẽ lại từng tư thế: cels (`cels.js`).
  Không lắp nhân vật bằng elip/vòng tròn.
- Liệt kê 4–6 tư thế khó nhất vào `<TEN>_SHEET`, render
  `node scripts/render.mjs <process_dir>/model-sheet.html --only 0,1 --out <process_dir>/preview`
  → **MỞ CẢ HAI ẢNH** (`view_file`): silhouette, tỉ lệ, khớp xoay đúng chỗ, không gì che mặt, chi đủ dài cho mọi
  điểm chạm. Sửa đến khi đạt; giữ ảnh model sheet làm chuẩn so sánh cho mọi vòng sau.
- Trong shot: `rigIK` cho chi chạm vật, `drawRig(c, RIG, pose, {pins})` với pin cho MỌI điểm chạm nhìn thấy
  (chân–đất/bàn đạp, tay–cán, bánh–đường). `drawRig` tự đăng ký vùng chủ thể thật cho `qa.mjs`.
  Nhân vật không dùng rig: gọi `markFocus(c, outlinePts)` với ĐƯỜNG BAO THẬT đang vẽ — khung chữ nhật cố định = FAIL.
- Bối cảnh: ≥ 3 lớp chiều sâu, không lỗ giấy trơn vô tình, có contour và chất liệu.
- Render 3–5 frame full-size của shot khó nhất:
  `node scripts/render.mjs <film> --only 60,150,300 --out <process_dir>/preview`
  → **MỞ TỪNG ẢNH** (`view_file`) và sửa trước khi làm tiếp.

**B4 — Dựng đủ các shot, rồi vòng review (lặp tối thiểu 2, tối đa 5 vòng):**
1. `node scripts/render.mjs <film> --grid 24 --out <process_dir>/preview` (~10 s) → mở ảnh grid.
   `node scripts/render.mjs <film> --crops 12 --out <process_dir>/preview` → mở crop sheet (cận nhân vật, nhãn đỏ =
   điểm chạm trượt). So từng ô với model sheet: nhân vật phải giống hệt, chỉ khác tư thế.
2. `node scripts/qa.mjs <film>` → sửa MỌI `FAIL`, cân nhắc từng `WARN`.
3. Chấm **Rubric §6**, ghi ra 3 lỗi tệ nhất, sửa trong code, quay lại bước 1.
4. Dừng vòng lặp khi: không còn FAIL **và** mọi tiêu chí rubric ≥ 1 **và** tổng ≥ 16/20.
   Rubric < 16 **không phải là đạt** — tiếp tục sửa tiêu chí thấp nhất (thường là: thêm bối cảnh/vật thể
   phụ, đưa camera lại gần, vẽ lại nhân vật theo skeleton). Chỉ khi hết 5 vòng mà vẫn < 16 mới được
   render và bàn giao, kèm câu **"CHƯA ĐẠT CHUẨN: x/20"** và danh sách điểm yếu ở dòng đầu báo cáo.

**B5 — Kiểm tra chi tiết.**
- `--strip START,18` quanh hành động nhanh nhất / va chạm (hiệu ứng phải trùng frame chạm).
- `--only` frame có chữ: kiểm tra dấu tiếng Việt hiển thị đủ (Ồ, Ờ, Ữ...).

**B6 — Render MP4 một lần** (phim dài: render từng phân đoạn đã đạt bằng `--range START,END` vào cache, cuối cùng
`--assemble`; xem `long-form.md` §2) (≈ 15 s render cho mỗi 1 s phim riso 1080p; các look khác nhanh hơn):
`node scripts/render.mjs <film> --out <output_dir>/<ten_phim>` → kiểm tra bằng
`ffprobe` (thời lượng, 1920x1080, số frame, có audio) và độ lớn âm thanh (`max_volume` < −0.5 dB).

**B7 — Bàn giao sạch** (§9): copy `<process_dir>/<ten_phim>.html` + các `*.js` film dùng vào
`<output_dir>/<ten_phim>/`, chạy `qa.mjs ... --json <output_dir>/<ten_phim>/qa.json` và
`--grid 24 --out <output_dir>/<ten_phim>` để lưu bằng chứng cạnh MP4.
</instructions>

> [!IMPORTANT]
> Preview (`--grid`, `--only`, `--strip`, `qa.mjs`) rẻ (giây). **Không được tiết kiệm preview.**
> Thứ đắt là MP4 đầy đủ — chỉ render khi rubric đã đạt. Mỗi lần nhìn ảnh phải dẫn tới ít nhất
> một quyết định cụ thể (giữ hay sửa gì).

## 5. Quy tắc chất lượng cứng

<constraints>

1. **Không crossfade biến hình**: không làm vật A mờ đi trong khi vật B hiện ra. Vẽ lại một
   hình qua các giai đoạn tham số (playbook §7).
2. **Không primitive làm nhân vật**: silhouette bằng `curvePath`/`blob`/cels; mắt có lòng trắng
   + đồng tử + điểm sáng; chi là hình thuôn có cơ.
3. **Phải có nét vẽ tay**: contour bằng `wob(..., {pressure})` hoặc `drawCel`; phân cấp độ dày
   (ngoài 4–6, trong 1.5–3, texture ≤ 1.5 đơn vị logic).
4. **Phải dùng finish của look**: riso → `printPlate` nhiều plate; ink → hatch/`formHatch`;
   pencil → `drawCel` pencil/`graphite`; screen → `screenFill`; doodle → ảnh + `brush`/`wash`.
5. **Cỡ chủ thể**: nhân vật chính 15–60% chiều cao khung tùy cỡ cảnh; không shot nào < 10%
   trừ khi có chủ đích ghi trong beat sheet.
6. **Thuần hàm thời gian**: mọi giá trị = f(T); không `Math.random` (dùng `rng`, `hash`);
   hiệu ứng = f(T − t_sự_kiện). Không giữ state giữa các frame.
7. **Exposure theo hành động**: chậm → `twos(T)`; nhanh/tracking → on ones.
8. **Không trùng tên** với global của engine (`key`, `arc`, `hash`, `layer`, `plate`, `paper`,
   `section`, `glow`, `on`, `pen`, `brush`, `W`, `H`, `PAL`, ...).
9. **Không tuyệt đối hóa đường dẫn máy** trong `<script src>` của film bàn giao.
10. **Một nhân vật = một định nghĩa**: nhân vật/đạo cụ có khớp dựng bằng `defineRig()` trong `character-<ten>.js`,
    dùng chung cho mọi shot/phân đoạn; shot chỉ đổi pose. Bộ phận cứng trong toạ độ xương: cánh/tay xoay quanh khớp,
    không kéo giãn điểm. Seed hình dáng cố định; chỉ nét viền boil (`rigBoil`). Không đưa thời gian vào `blob()`/`curvePath()`.
11. **Mọi điểm chạm nhìn thấy được phải có pin** và `qa.mjs` không FAIL `contact`. Chi không với tới thì sửa thiết kế
    (chi dài hơn, hạ yên), không nới dung sai.
12. **Zero External LLM API**: toàn bộ sáng tạo do agent trong IDE thực hiện; không gọi REST API
    mô hình ngoài, không yêu cầu API key.

</constraints>

## 6. Rubric tự chấm (sau mỗi vòng grid)

<quality_gate>

Chấm 0 / 1 / 2 cho từng tiêu chí, dựa trên ẢNH đã mở (không dựa trên code). Mở grid phim của
bạn và đối chiếu các tiêu chí chất lượng (về mật độ chi tiết, cỡ nhân vật, chiều sâu bối cảnh, diễn xuất) để so sánh từng tiêu chí.

> [!WARNING]
> Model tự chấm thường **thổi phồng điểm** (bài thử: tự chấm 19/20 cho phim có nhân vật chỉ
> chiếm ~8% khung và mái nhà là một khối nâu phẳng). Quy tắc chống thổi phồng:
> - Điểm 2 chỉ được cho khi phim của bạn đạt chuẩn chất lượng thực sự ở tiêu chí đó.
> - Tiêu chí 2 (bố cục) lấy cột `subject` của `qa.mjs`: median < 15% → tối đa 1; < 12% → 0.
> - Tiêu chí 5–6 (nét, chất liệu) lấy cột `detail`: < 5% (look không phải pencil) → tối đa 1.
> - Mỗi điểm 2 phải ghi kèm bằng chứng cụ thể nhìn thấy (frame nào, chi tiết gì).

| # | Tiêu chí | 2 điểm khi... |
|---|---|---|
| 1 | Câu chuyện | Nhìn grid hiểu được mục tiêu, trở ngại, thay đổi, kết |
| 2 | Bố cục | Mỗi shot có chủ thể rõ, `subject` ≥ 20%, có điểm nhìn; không khoảng trống vô tình |
| 3 | Chiều sâu | ≥ 3 lớp (xa/giữa/gần), tương phản giá trị tách chủ thể khỏi nền |
| 4 | Thiết kế & nhất quán nhân vật | Silhouette đọc được, chi tiết có chủ đích; trên crop sheet nhân vật GIỐNG model sheet ở mọi ô (tỉ lệ, mỏ/mặt, phụ kiện), không bộ phận nào che mặt |
| 5 | Nét vẽ tay | Contour có lực nhấn và phân cấp; texture theo khối |
| 6 | Chất liệu | Nhìn ra đúng look (chấm riso & chồng màu, hatch ink, nét chì...) |
| 7 | Màu | Bảng màu hạn chế, nhất quán, có màu nhấn dẫn mắt |
| 8 | Diễn xuất | Có anticipation → action → reaction; vật lý tin được |
| 9 | Liên tục | Hướng/vị trí giữ qua vết cắt; hiệu ứng trùng thời điểm va chạm; mọi điểm chạm đúng (`contact` = 0) |
| 10 | Hoàn thiện | Không lỗi hiển thị, chữ đủ dấu, kết giữ đủ lâu, âm thanh khớp hình |

**Đạt** khi tổng ≥ 16/20 và không tiêu chí nào = 0, cộng `qa.mjs` không FAIL.
Không được tự chấm điểm cho những gì chưa nhìn thấy trên ảnh.

### Checklist trước khi bàn giao
- [ ] `qa.mjs` không FAIL; đã đọc mọi WARN và ghi lý do giữ lại (nếu có).
- [ ] Model sheet đã duyệt (ảnh lưu cạnh phim); crop sheet cuối đã mở và so với model sheet.
- [ ] Phim dài: `continuity.md` đủ dòng cho mọi phân đoạn; đã xem strip quanh mỗi vết cắt giữa phân đoạn.
- [ ] Rubric ≥ 16/20, đã mở và nhìn grid cuối + ≥ 3 frame full-size + 1 strip.
- [ ] MP4: `ffprobe` đúng thời lượng, 1920x1080, đủ frame, có audio nếu có score; không clip.
- [ ] Không lỗi console; không `Math.random`; không đường dẫn tuyệt đối trong film bàn giao.
- [ ] Output isolation: thành phẩm ở `<output_dir>`, file tạm ở `<process_dir>`, không gì trong gốc repo.
- [ ] Lưu bằng chứng kiểm định: `qa.json` (`--json`) và grid cuối cạnh thành phẩm.

</quality_gate>

## 7. API đã kiểm chứng (assets/core.js, studio.js, cels.js, materials.js)

```js
// Thời gian & chuyển động (thuần hàm)
sm(a, b, t, ease=easeIO)                 // 0..1 giữa thời điểm a và b
key(t, [[t0, v...], [t1, v..., easeFn?]], ease=easeIO) // easing riêng = phần tử cuối của key BẮT ĐẦU đoạn
keyPath(t, [[t, x, y, ...]], {ease})     // Catmull-Rom → mảng
arc([x0,y0], [x1,y1], u, lift)           // parabol nhảy
spring(t, {freq=2.4, damp=.55})          // 0 → 1 có vọt lố
settle(t, t0, {amp, freq, decay, phase}) // rung tắt dần sau t0
anticipate(a, b, t, {back, hold, e})     // lùi trước khi đi
squash(k) → [sx, sy]   breathe(t, period, phase)   drift(t, seed, {amp, freq})   twos(t)
easeIO easeOut easeIn easeOutQuint easeInOutSine easeOutBack easeOutExpo easeOutElastic
// Ngẫu nhiên ổn định
rng(seed)()   hash(k, seed) → 0..1   noise1(x, seed) → -1..1
// Camera & layer
cam(c, x, y, zoom, rot)  resetT(c)  layer(w?, h?)  blit(c, L)
camKeys(c, tau, [[t, x, y, zoom, rot?]], {ease, hand, seed}) → [x,y,z,rot] (KHÔNG gồm rung tay)
// Hình
curvePath(pts, close=true, corner=.8) → Path2D   polyPath(pts, close)   smoothPts(pts, close, step, corner)
blob(cx, cy, rx, ry, seed, {amp, rot, n}) → pts  ellPts(cx, cy, rx, ry, rot, n) → pts
// Nét & chất liệu
wob(c, pts, amp, seed, close, {pressure, smooth, corner, freq})   // nét tay; set strokeStyle/lineWidth trước
crayon(c, pts, color, width, seed, close)
hatch(c, path, [x,y,w,h], {angle, gap, len, jitter, color, alpha, width, seed, flow, curve})
dotScreen(c, path, box, {cell, color, density(number | (x,y)=>0..1), angle, jitter, seed, alpha})
surface(c, path, box, {finish, color, seed, density, angle})  grain(c, path, box, n, color, al, seed, size)
plate() → layer trắng;  printPlate(c, plateLayer, {cell, ink, angle, jitter, seed, maxCov, offset, mottling})
formHatch(c, path, box, {tone:(x,y)=>0..1, direction:(x,y)=>rad, spacing, length, width, opacity, color, seed})
screenFill(c, path, box, {color, paper, seed, wear})  pigmentWash(c, path, box, {color, opacity, granulation, edge, blend})
// Cels (nhân vật vẽ lại từng tư thế)
compileCel({strokes:[{id, points, width, opacity, pressure, close, corner}]}, {id})
inbetweenCel(rawA, rawB, u)  exposureSheet([{id, frames}], drawings, 24).at(sec) → {id, drawing}
drawCel(c, cel, {material:'pencil'|'ink', color, opacity})   motionPath(pts).at(u) → {p, tangent}
// Bối cảnh, hiệu ứng, chữ
paper(c, base, band, seed)  night(c)  section(c, y, color, seed)  flash(c, color)  glow(c, x, y, r, color, k)
speedLines(c, x, y, dir, seed, n, al, color)  dotBurst(c, x, y, R, rays, color, seed, g)
blot(c, srcLayer, cx, cy, R, seed)  iris(c, cx, cy, r, fn, outside)  handText(c, text, x, y, {size, ink, ink2, align})
mix(a, b, t)  tint(c, t)  shade(c, t)  alpha(c, a)  makePalette({...}, base)  usePalette(name|obj)
// Rig nhân vật (assets/rig.js — chi tiết: references/character-rig.md)
defineRig({name, bones:{id:{parent, at, rest, len}}, parts:[{id, bone, z, hull, draw(c, k)}], sockets:{id:{bone, at}}}) → rig
rigIK(rig, pose, upperBone, lowerBone, target, bend=±1)   drawRig(c, rig, pose, {pins:[{socket, to, tol}], only, focus, T})
rigPoint(rig, pose, socket) → [x,y]   rigBoil(T)   drawRigBones(c, rig, pose, pins)   drawModelSheet(c, rig, [{label, pose}], {bones})
// pose = {x, y, rot, scale, flip, angles:{bone: rad}, z:{part: z}, swap:{slot: id}, hide:[id], boil}; k = {seed, boil, pose, T}
// Âm thanh & phim
note(ac, master, f, t0, t, d, type, g)  noiseBurst(ac, master, t0, t, d, g, seed)  pentHz(octave, step, base)
defineFilm({palette, timeline:[{name, dur, fn(c, tau, i), twos?}], score(ac, t0, dest), format:{ar:'16:9', width:1920}, fps:24})
// Biến toàn cục: W, H (logic, cạnh ngắn = 1080), CX, CY, S, TAU, PAL
```

## 8. CLI CONTRACT

> Dùng contract trước; chỉ đọc mã nguồn script khi lệnh lỗi, cần hành vi chưa ghi, hoặc cần sửa script.

### `scripts/render.mjs`
- **Cú pháp:** `node .agents/skills/hand-drawn-animation/scripts/render.mjs <film.html> [tùy chọn]`
- `--grid N` (1–240): ảnh tổng quan N frame → `<out>/<film>-grid.jpg` (preview, vài giây)
- `--strip START,COUNT`: dải frame liên tiếp → `<out>/<film>-strip-START.jpg`
- `--only 0,24,96`: PNG full-size → `<out>/<film>-frames/NNNN.png`
- `--crops N` (1–48): N ảnh cận nhân vật chính theo vùng chủ thể thật → `<out>/<film>-crops.jpg`; nhãn đỏ = pin trượt / thiếu vùng chủ thể
- `--seq XX`: chỉ dựng phân đoạn XX của phim dài (`long-film.html`), giữ thời gian toàn phim; dùng với preview
- `--range START,END` (END không gồm): render đầy đủ các frame vào cache `<out>/<film>-cache/`, bỏ qua frame đã có (`--force` để làm lại)
- `--assemble`: khi cache đủ frame → MP4 + score; cảnh báo đoạn render từ phiên bản code cũ
- `--out <dir>` (mặc định `./out` cạnh film) · `--ar 16:9` · `--width 1920` · `--look ink|pencil|riso|screen|doodle`
- Không có cờ preview → render đầy đủ: `<film>.mp4`, `<film>-final.mp4` (có tiếng nếu có score),
  `<film>-score.wav`, `<film>-contact.jpg`, `<film>-render.json`.
- Exit code 0 = thành công; ≠ 0 kèm số frame lỗi.

### `scripts/qa.mjs`
- **Cú pháp:** `node .agents/skills/hand-drawn-animation/scripts/qa.mjs <film.html> [--samples 36] [--json qa.json]`
- Đo trên 36 frame rải đều: **cỡ nhân vật** (`subject`, từ `markFocus`), tỉ lệ nét vẽ (ridge tối
  mảnh), mật độ chi tiết (`detail`), % khung trống, chuyển động theo scene; kiểm tra tĩnh: `Math.random`, thiếu hàm nét, lạm dụng elip,
  crossfade, đường dẫn tuyệt đối, toạ độ cứng; frame ném lỗi (báo số frame + scene).
- Nhân vật: `box-focus` (FAIL, `markFocus` nhận khung cố định), `contact` (FAIL, pin trượt quá dung sai — vẽ dày theo
  `--contact-frames`, mặc định 240), `rig-drift` (FAIL, một rig hai định nghĩa), `no-rig` / `shape-boil` (WARN),
  `no-ledger` (WARN, phim > 45 s thiếu `continuity.md`). `--seq XX` để QA một phân đoạn.
- Exit code: 0 = không FAIL · 2 = có FAIL · 1 = film không chạy được.
- QA là con số, không thay cho việc NHÌN ảnh.

## 9. Bàn giao & quy chuẩn vận hành

<delivery_protocol>

- **Autonomous Execution**: khi kích hoạt, agent tự chạy liên tục brief → thiết kế → dựng →
  vòng review → render → kiểm chứng → bàn giao; không tự dừng giữa chừng để xin phép
  (trừ khi thiếu quyết định thật sự đổi kết quả ở bước Intake).
- **Clean Delivery**: khung chat chỉ báo cáo ngắn: look, số shot, thời lượng, điểm rubric và
  WARN còn lại (nếu có), đường dẫn tuyệt đối tới `<ten_phim>-final.mp4`, `<ten_phim>.html`,
  grid cuối và `qa.json` trong `<output_dir>`; hướng dẫn mở HTML để scrub/nghe.
- Báo trung thực giới hạn: ví dụ "chưa xem phát lại ở tốc độ thật" nếu không xem được video.

</delivery_protocol>

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> Thành phẩm (HTML player, MP4, WAV, grid, qa.json) PHẢI lưu vào `<output_dir>` (mặc định:
> `~/Downloads/AIWF_Output/` hoặc thư mục do người dùng chỉ định). Nháp/preview/PNG tạm ở
> `<process_dir>` (`_process/`, đã gitignore) hoặc `/tmp`. TUYỆT ĐỐI KHÔNG lưu video render
> hoặc chuỗi ảnh PNG vào thư mục gốc repository.
> Khi bàn giao HTML vào `<output_dir>`, copy kèm các `assets/*.js` mà film dùng vào cùng thư mục
> và sửa `<script src>` thành tương đối để file mở được ở máy khác.

## 10. Liên kết skill khác

| Skill | Kết hợp |
|---|---|
| **long-tieng** | Lồng tiếng/thuyết minh cho phim (score của phim là nền nhạc) |
| **phu-de** | Phụ đề song ngữ VI/JP lên MP4 |
| **video-studio** | Ghép clip hoạt hình vào video stock |

## 11. Cấu trúc thư mục

```
hand-drawn-animation/
├── SKILL.md · README.md (tài liệu upstream) · LICENSE
├── assets/      core.js · cels.js · studio.js · materials.js · roto.js · sand.js · paper3d.js · starter.html (neutral skeleton) · film-template.html (khung cũ)
│                rig.js · character-hero.js (mẫu character bible) · model-sheet.html · long-film.html + seq-01.js (phim dài)
├── references/  craft-playbook.md (bắt buộc) · character-rig.md · long-form.md · style.md · redrawn-animation.md · motion.md · studio.md
│                architecture.md · mixed-media.md · palettes.md · scenes.md · doodle.md · found-motion.md
│                sand.md · paper3d.md · brief-template.md · reference-films.md
├── scripts/     render.mjs · qa.mjs · verify.mjs · photo.mjs · roto.py · package.json
└── examples/    koi-dragon.html (case study Riso print) · koi-dragon-grid.jpg · sketchbook-bird.html (pencil) · fly-style.html · four-looks.html
                 one-year.html · material-studies.html · becoming-phoenix/ (60 s) · pelican-rig/ (rig + IK + pin, model sheet, crops)
```

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

Skill này hiện **không dùng engine chung** (mã trong `scripts/` là đặc thù miền). Khi cần đọc tệp người dùng, xuất DOCX, kiểm định PDF, ffmpeg/TTS/phụ đề hoặc font: dùng engine trong `_shared/ENGINES.md`, không tự viết.
