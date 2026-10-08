# Craft playbook — làm phim như một đạo diễn, không như một bản demo kỹ thuật

File này BẮT BUỘC đọc trước khi viết film. Nó tóm tắt những thói quen tạo ra khác
biệt giữa một phim "đẹp như Opus" và một phim "đúng API nhưng xấu". Khung sườn
trung lập: [`assets/starter.html`](../assets/starter.html). Ví dụ đối chiếu chuyên sâu
cho kỹ thuật in Riso: [`examples/koi-dragon.html`](../examples/koi-dragon.html) (22 s,
riso + ink, cùng đề tài "cá chép hóa rồng" với một bản lỗi đã gặp).

## 0. Bệnh án: vì sao phim bị xấu

Bản lỗi thật (cá chép hóa rồng, 16 s) có đủ 4 cảnh, có nhạc, render thành công,
nhưng xem thì kém. Nguyên nhân đo được:

| Triệu chứng nhìn thấy | Nguyên nhân trong code | Cách sửa |
|---|---|---|
| Nhân vật nhỏ xíu giữa khung trống (≈3% chiều cao) | không chọn camera/cỡ cảnh, vẽ ở toạ độ cố định | §2 bố cục: nhân vật chiếm 20–60% chiều cao khung; mỗi shot là 1 camera trong cùng 1 thế giới |
| 60–99% khung là giấy trơn | không có bối cảnh, không có lớp chiều sâu | §3 dựng bối cảnh: ≥3 lớp chiều sâu, khối sáng/tối lớn |
| "Riso" nhưng không thấy chất riso | chỉ `fillStyle` + `globalAlpha`, không gọi `printPlate`/`dotScreen`/`wob` | §4 chất liệu: dùng đúng finish của engine |
| Không có nét vẽ tay | không có contour (không `wob`, không `drawCel`) | §5 nét: mọi hình chính có contour có lực nhấn |
| Cá = elip + chấm tròn; rồng = chuỗi elip | lắp hình từ primitive | §6 thiết kế nhân vật: silhouette bằng `curvePath`, spine + profile, hoặc cels |
| "Biến hình" = cá mờ dần, rồng hiện dần | crossfade bằng `globalAlpha` | §7 biến hình: VẼ LẠI một cơ thể qua các giai đoạn, che chỗ khó bằng hiệu ứng có thiết kế |
| Chuyển động trôi đều, không có diễn xuất | `y = H*0.65 - tau*20`, sin vô hạn | §8 diễn xuất: anticipation → action → reaction → settle; thất bại trước khi thành công |
| Không biết phim xấu | chỉ render 1 frame rồi render MP4, không bao giờ NHÌN | §10 vòng review: grid → QA → nhìn → sửa, nhiều vòng |

Quy tắc gốc: **code chạy được ≠ phim đẹp.** Mỗi quyết định thị giác phải có lý do
và phải được kiểm tra bằng mắt trên ảnh render.

## 1. Câu chuyện trước, pixel sau

Viết beat sheet ở đầu file film (xem mẫu trong `assets/starter.html` hoặc `examples/koi-dragon.html`). Mỗi beat có: thời điểm,
độ dài, *khán giả chú ý vào gì*, hành động, camera, âm thanh.

- Một phim ngắn 15–25 s cần một **mục tiêu**, một **trở ngại** và một **thay đổi**.
  "Cá bơi → nhảy → thành rồng" là danh sách sự kiện; "cá thử, THẤT BẠI, gom sức,
  thử lại, thành công, biến đổi" là câu chuyện. Thất bại trước thành công là
  công cụ rẻ nhất để tạo cảm xúc.
- 4–6 shot là đủ. Mỗi shot ≥ 1.5 s để đọc kịp; khoảnh khắc chính (biến hình,
  cao trào) được nhiều thời gian nhất.
- Có mở (thiết lập thế giới) và có kết (tư thế cuối giữ ≥ 1.5 s, tiêu đề nếu cần).

## 2. Bố cục và camera

- **Một thế giới, nhiều camera.** Dựng bối cảnh một lần trong toạ độ thế giới;
  mỗi shot chỉ là `shotCam(tau, keys)` khác nhau. Liên tục (vị trí, hướng) tự động đúng.
- **Cỡ nhân vật:** wide shot 15–25% chiều cao khung, medium 30–50%, close-up 60%+.
  Không có shot nào mà nhân vật chính < 10% chiều cao, trừ khi nó đang được
  giới thiệu như một chấm nhỏ có chủ đích.
- **Điểm nhìn:** đặt chủ thể ở 1/3 hoặc chính giữa *có chủ đích* (đối xứng cho
  khoảnh khắc trang trọng: rồng trước mặt trời). Dùng đường dẫn mắt (thác nước
  dọc dẫn mắt lên mặt trời).
- **Tương phản giá trị:** chủ thể sáng trên nền tối hoặc ngược lại. Cá kem/đỏ
  trên vách đá xanh tím đậm; rồng vàng trên trời kem với mặt trời cam phía sau.
- **Camera có động cơ:** push-in khi bắt đầu chú ý, tilt theo cú nhảy, pull-back
  để lộ quy mô sau cao trào. Rung tay (`hand`) 2–4 px; rung mạnh chỉ ở va chạm.
- **Áp cùng một camera** cho canvas chính và mọi plate/layer (`applyView`).
  Lưu ý: `camKeys()` trả về toạ độ KHÔNG gồm rung tay → khi có plate, tự tính
  camera (xem `shotCam` trong ví dụ) rồi `cam()` cho tất cả.
- Cắt cảnh đúng hành động (cut on action): hướng chuyển động giữ nguyên qua vết cắt.

## 3. Bối cảnh có chiều sâu

- ≥ 3 lớp: xa (núi nhạt, parallax 0.5), giữa (vách đá, thác — nơi diễn ra hành
  động), gần (cành lá đỏ ở góc khung, parallax > 1). Lớp gần chỉ cần một vật
  thể đóng khung là đủ tạo chiều sâu.
- Lớp xa nhạt và ít tương phản, lớp gần đậm. Không để lỗ giấy trơn vô tình phía
  sau vật thể (kiểm tra mọi góc camera).
- Vật trang trí có thiết kế nhận ra được (mây cuộn kiểu Á Đông, thông dáng
  bonsai, lá phong 5 thùy) thay vì blob xám.
- Chi tiết động của bối cảnh (nước chảy, gợn sóng, bọt) chạy *on twos* và là
  hàm thuần của thời gian, có id ổn định (`hash(k, seed)`), không `Math.random`.

## 4. Chất liệu: dùng đúng engine

| Look | Bắt buộc dùng | Đặc trưng phải nhìn thấy |
|---|---|---|
| riso | `printPlate` với 2–4 plate (vàng/đỏ/xanh...), multiply | chấm halftone, màu chồng màu (vàng+xanh = lục), giấy lộ ra |
| ink | `wob` có `pressure`, `hatch`/`formHatch` theo khối | nét đậm nhạt, khối đen chủ ý, hatch ở vùng tối |
| pencil | `cels.js` `drawCel(..., {material:'pencil'})`, `graphite` | nét mảnh hở, nhiều lượt nhẹ, giấy trống nhiều (tối giản là chủ ý) |
| screen | `screenFill`, khối phẳng đục, cạnh stencil | khối màu đặc, ít chấm |
| doodle | ảnh thật + `brush`/`pen`/`wash` | nét vẽ tương tác với cạnh thật của vật |

Plate riso: vẽ *độ phủ* (xám = phủ một phần, trắng = knock-out) cho từng mực,
in mực tối nhất cuối cùng. Vật ở trước phải knock-out mực của vật phía sau trên
các plate khác (núi che mặt trời → núi vẽ trắng trên plate vàng/đỏ).

## 5. Nét (line) — thứ làm phim "vẽ tay"

- Một hàm cọ duy nhất cho cả phim (ví dụ `lineK` = `wob` + `pressure`), để nét
  đồng nhất.
- Phân cấp độ dày: contour ngoài 4–6 px (logic 1080), chi tiết trong 1.5–3 px,
  texture 1–1.5 px với alpha thấp. Cạnh bóng tối dày hơn cạnh sáng.
- Contour hai nửa (lưng / bụng) vẽ thành 2 nét hở có thon đầu, không phải
  `stroke()` một polygon kín đều đặn.
- Kỹ thuật **stroke-then-fill** cho hình hợp (mây nhiều bướu): hoặc tính đường
  bao rồi vẽ một nét, không để các đường tròn chồng nhau lộ ra.

## 6. Thiết kế nhân vật

Chọn một trong ba cách, đừng lắp elip:

1. **Cels (mặc định cho nhân vật có chân tay, biểu cảm):** các tư thế key vẽ trọn
   bằng stroke có id → `compileCel`, `inbetweenCel`, `exposureSheet`
   (xem `sketchbook-bird.html`, `redrawn-animation.md`).
2. **Spine + width profile (sinh vật thân dài: cá, rắn, rồng, sâu, khăn, dải lụa):**
   một đường xương sống tính từ đầu (`heading`, `bend`, sóng `amp/wave/phase`),
   bề rộng theo `profile(u)`, mọi bộ phận gắn tại phân số `u` của xương sống
   (`pt(u, v)`: v = −1 lưng, +1 bụng). Hoa văn (vảy, mảng màu) định nghĩa trong
   toạ độ (u, v) nên uốn theo thân và không "trôi".
3. **Hình vẽ tay theo khung cục bộ:** đầu rồng, sừng, lá — điểm do người vẽ đặt
   trong hệ toạ độ cục bộ, `curvePath` để làm mềm, giữ góc nhọn bằng `corner`.

Checklist thiết kế: silhouette nhận ra được khi tô đen; 1 màu chủ đạo + 1 màu
nhấn; mắt có lòng trắng + đồng tử + điểm sáng; tay/chân là hình thuôn có cơ
(không phải hộp chữ nhật); sừng/vây là hình có bề rộng (không phải nét que).

## 7. Biến hình (transformation)

- **Một cơ thể, tham số thay đổi:** `g.len` (dài ra), `g.head` (đầu mới mọc
  trong đầu cũ), `g.legs` (vây → chân), `g.mane` (vây lưng → gai + bờm),
  `g.color`. Mỗi tham số có khoảng thời gian riêng, gối lên nhau → biến đổi theo
  giai đoạn, đọc được từng bước.
- Mỗi giai đoạn có một "nhịp" thị giác + âm thanh (vòng sáng, chuông).
- Che chỗ khó bằng hiệu ứng có thiết kế (1–2 frame flash, vòng mực, tia sáng),
  không bằng `globalAlpha` crossfade toàn bộ.
- Kết thúc bằng một hành động khẳng định danh tính mới (rồng gầm: há miệng,
  rung camera, gong).

## 8. Diễn xuất và thời gian

- Mỗi hành động: **anticipation** (co lại, lấy đà, 0.3–0.7 s) → **action**
  (nhanh, `easeOut`/`easeOutQuint` để "bật") → **follow-through/settle**.
- Vật lý: rơi tăng tốc (`easeIn`), bật lên giảm tốc (`easeOut`), bay theo
  parabol (`arc`). Va chạm có phản ứng (bắn nước tại đúng frame chạm mặt nước).
- **Exposure theo hành động:** đoạn chậm *on twos* (`twos(T)`) cho cảm giác vẽ
  tay; đoạn nhanh/tracking *on ones* để không giật khi camera bám theo.
- Hiệu ứng (bắn nước, bụi, tia) là hàm thuần của `thời gian kể từ sự kiện`, có
  danh sách sự kiện `[t0, x, y, size]` → seek được, render lại được.
- Kiểm tra khớp thời điểm: hiệu ứng va chạm phải trùng frame nhân vật chạm
  (dùng `--strip` quanh frame đó).

## 9. Âm thanh

- Âm thanh cắt theo hình: mỗi cú taiko/gong rơi đúng một hành động nhìn thấy.
- Lớp nền (nước, gió) thay đổi âm lượng theo shot; motif giai điệu ngắn
  (ngũ cung cho đề tài Á Đông) mở đầu và trở lại hoàn chỉnh ở kết.
- Master qua `DynamicsCompressor` và gain ≈ 0.6 để không clip (kiểm tra
  `max_volume` < −0.5 dB bằng ffmpeg volumedetect).

## 10. Vòng review (bắt buộc, nhiều vòng)

1. `node scripts/render.mjs film.html --grid 24 --out <process_dir>/preview` → MỞ ẢNH
   (`view_file`) và nhìn thật.
2. `node scripts/qa.mjs film.html` → sửa mọi FAIL; đọc WARN.
3. Chấm rubric (SKILL.md §6). Viết ra 3 lỗi tệ nhất, sửa, render lại grid.
4. `--only` 3–5 frame full-size ở các khoảnh khắc chính → nhìn chi tiết: chữ
   (dấu tiếng Việt!), nét, mép, lỗ giấy trơn.
5. `--strip START,18` quanh hành động nhanh nhất / va chạm → kiểm tra spacing,
   hiệu ứng trùng thời điểm.
6. Chỉ khi rubric đạt mới render MP4 đầy đủ (một lần).

**Không tin điểm tự chấm.** Một bài thử với model nhỏ tự chấm 19/20 cho phim có
con mèo chiếm ~8% khung trên một mái nhà phẳng không chi tiết. Dùng số đo của
`qa.mjs` (`subject`, `detail`) và so sánh trực tiếp với `examples/koi-dragon-grid.jpg`.

Dấu hiệu của một vòng review thật: mỗi vòng có ít nhất một thay đổi thị giác
cụ thể (không phải chỉ đổi số cho "an toàn").

## 11. Bẫy kỹ thuật đã gặp

- Sửa code bằng `sed`/regex có thể chèn `//` giữa dòng và **comment mất phần
  còn lại** → biến `undefined`, lỗi ở frame xa. `qa.mjs` render rải khắp phim nên
  bắt được; luôn chạy lại QA sau khi sửa hàng loạt.
- Chữ tiếng Việt: font Nhật/Trung (Hiragino Mincho...) có thể THIẾU dấu (Ồ → Ô).
  Dùng font có đủ dấu ("Times New Roman", "Noto Serif", "Be Vietnam Pro" nếu có)
  và kiểm tra frame full-size.
- Tên hàm/hằng trùng với `core.js` (`key`, `arc`, `hash`, `layer`, `plate`, `paper`,
  `section`, `glow`, `flash`, `on`, `pen`, `brush`, `W`, `H`, `PAL`...) làm trang không
  bao giờ `__ready`. Đặt tên riêng (ví dụ `lineK`, `shotCam`, `COL`).
- `layer()` tạo ở file scope tự đổi kích thước theo format; tạo layer mới mỗi
  frame gây rò bộ nhớ → tái sử dụng (xem `PLATES`).
- Hiệu năng: 3 plate riso full-frame ≈ 0.5 s/frame ở 1920 px → 22 s phim ≈ 5 phút
  render. Preview grid vẫn chỉ ~10 s. Đừng tiết kiệm preview.
- MP4 halftone rất nặng (≈ 3.5 MB/s ở crf 18) — bình thường với chất liệu chấm.
