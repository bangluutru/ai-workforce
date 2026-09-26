---
name: hand-drawn-animation
display-name: Tạo Hoạt Hình
description: >-
  Tạo phim hoạt hình vẽ tay bằng Canvas 2D với 5 phong cách nghệ thuật (ink, riso, screen, pencil, doodle), rotoscope, sand animation, và hiệu ứng pop-up paper 3D; xuất HTML player và video MP4 offline.
  USE WHEN: Người dùng muốn sáng tạo hoạt hình nghệ thuật vẽ tay, phim hoạt họa 2D ngắn, hoặc hiệu ứng minh họa đồ họa động.
  DO NOT USE WHEN: Cần dựng video thực tế với stock footage người thật (dùng 'video-studio'), chỉ làm phụ đề video (dùng 'phu-de'), hoặc chỉ thuyết minh/lồng tiếng (dùng 'long-tieng').
trigger: Hoạt hình vẽ tay, hand drawn animation, canvas animation, phim hoạt hình, doodle animation
category: content
needs_file: false
file_filter: any
---

# 🎨 Hand-Drawn Animation — Phim Hoạt Hình Vẽ Tay

> **Nguồn gốc**: [alesha-pro/tools](https://github.com/alesha-pro/tools/tree/main/skills/hand-drawn-canvas-animation) — MIT License © 2026 Alexey Fateev
> **Tích hợp AIWF**: Skill #14

---

## 1. Mô Tả

Skill tạo **phim hoạt hình vẽ tay** hoàn chỉnh bằng JavaScript + Canvas 2D API. Mỗi khung hình được vẽ bằng code (procedural art), sau đó render thành MP4 qua Headless Chrome + ffmpeg.

**KHÔNG cần** Blender, WebGL, hoặc AI video generation model. Toàn bộ hình ảnh được tạo bằng thuật toán vẽ nét bút trên Canvas 2D.

### Đặc điểm cốt lõi

| Đặc điểm | Chi tiết |
|-----------|----------|
| **Renderer** | Canvas 2D (thuần JavaScript) |
| **Đầu ra** | HTML player (xem trực tiếp) + MP4 offline |
| **FPS** | 24fps (chuẩn phim hoạt hình) |
| **Kỹ thuật** | Whole-pose drawings, exposure sheets, keys & breakdowns |
| **Dependencies** | Node.js, Chrome (headless), ffmpeg |

---

## 2. Các Phong Cách Hình Ảnh (5 Looks)

| Look | Palette | Mô tả |
|------|---------|--------|
| **Ink** (Mực) | `paperInk` | Nét bút lông tự tin, khối đen chủ ý, khoảng trắng |
| **Riso** (In riso) | `risoPop` | Hiệu ứng in risograph, overprint, halftone |
| **Screen** (In lụa) | `screenSea` | Hình khối phẳng đục, cạnh stencil |
| **Pencil** (Chì) | `pencilMinimal` | Nét chì mỏng, contour mở, hatching áp lực |
| **Doodle** (Nguệch ngoạc) | `doodlePastel` | Bút lông vẽ nguệch ngoạc trên ảnh thật |

## 3. Các Engine Mở Rộng

| Engine | File | Khả năng |
|--------|------|----------|
| **Found Motion** (Rotoscope) | `assets/roto.js` + `scripts/roto.py` | Vẽ lại chuyển động thật từ video |
| **Sand Animation** (Hoạt hình cát) | `assets/sand.js` | Hoạt hình cát trên đèn hắt |
| **Paper in Space** (Sách pop-up) | `assets/paper3d.js` | Sách pop-up 3D, trang lật, ánh sáng |

---

## 4. Hướng Dẫn Sử Dụng

### Bước 1: Kiểm tra dependencies

```bash
# Kiểm tra Node.js, Chrome và ffmpeg
node --version && echo "✓ Node.js" || echo "✗ Cần cài Node.js"
which ffmpeg && echo "✓ ffmpeg" || echo "✗ Cần cài: brew install ffmpeg"
```

### Bước 2: Cài đặt dependencies cho renderer

```bash
cd .agents/skills/hand-drawn-animation/scripts
npm install --no-audit --no-fund
```

### Bước 3: Tạo phim hoạt hình

Agent sẽ thực hiện quy trình sau khi được kích hoạt:

1. **Điền brief** — Xác định chủ đề, phong cách (ink/riso/pencil/screen/doodle), nhân vật, hành động
2. **Thiết kế nhân vật** — Silhouette, tỷ lệ, biểu cảm, nét vẽ đặc trưng
3. **Lập exposure sheet** — Keys, breakdowns, inbetweens, timing
4. **Hoàn thiện shot mẫu** — Render và review 1 shot trước khi làm toàn bộ
5. **Dựng phim** — Beat sheet: mở đầu, hành động chính, camera, âm thanh
6. **Xuất bản** — Render MP4 + HTML player

### Bước 4: Quy trình Render Chuẩn (Preview → Validate → Full Render)

> **Kỷ luật Render (Optimization C):**
> 1. **Kiểm tra cấu trúc:** Kiểm tra file HTML chạy không có lỗi JavaScript console.
> 2. **Spot Preview 1 khung hình:** Dùng `--only 0` để render thử khung hình đầu tiên trong 2-3s nhằm xác nhận kích thước và look.
> 3. **Render Full MP4 1 lần:** Sau khi preview đạt, thực hiện render MP4 hoàn chỉnh 1 lần duy nhất. Tuyệt đối không lặp lại grid render nhiều lần nếu không có lỗi.
> 4. **Chuẩn FPS vẽ tay:** Hoạt hình vẽ tay procedural hỗ trợ chuẩn 12fps (animating on twos) hoặc 24fps. Chuẩn 12fps giúp giảm 50% thời gian render trong khi vẫn giữ nguyên chất vẽ tay nghệ thuật.

```bash
# 1. Spot Preview nhanh frame 0 (xác nhận kích thước & look trong 2s)
node .agents/skills/hand-drawn-animation/scripts/render.mjs path/to/film.html --only 0 --out /tmp/preview

# 2. Render MP4 hoàn chỉnh 1 lần duy nhất vào thư mục xuất bản
node .agents/skills/hand-drawn-animation/scripts/render.mjs path/to/film.html --out ~/Downloads
```

---

## 4.1 CLI CONTRACT

> **Quy tắc đọc helper script:** Sử dụng CLI contract dưới đây trước tiên. Chỉ đọc mã nguồn script khi: (1) lệnh theo contract bị lỗi cần debug, (2) cần hành vi chuyên biệt chưa được document, hoặc (3) cần sửa đổi script.

### `scripts/render.mjs`
- **Mục đích:** Render film HTML Canvas 2D thành video MP4 hoặc trích xuất khung hình preview offline qua Headless Chrome + FFmpeg.
- **Cú pháp:** `node .agents/skills/hand-drawn-animation/scripts/render.mjs <film.html> [tùy_chọn]`
- **Đối số bắt buộc:** `<film.html>` (Đường dẫn tệp HTML animation)
- **Tùy chọn:**
  - `--out <dir>`: Thư mục lưu kết quả (mặc định: `./out`, khuyến nghị: `~/Downloads`)
  - `--only <frames>`: Chỉ render danh sách frame chỉ định để preview nhanh (ví dụ: `--only 0` hoặc `--only 0,24`)
  - `--grid <N>`: Xuất ảnh overview grid N khung hình (ví dụ: `--grid 12`)
  - `--strip <START,COUNT>`: Xuất dải khung hình liên tiếp
  - `--look <style>`: Override phong cách (`ink`, `riso`, `screen`, `pencil`, `doodle`)
- **Kết quả:** Tệp `<film_name>.html` và `<film_name>.mp4` tại thư mục `--out`.
- **Mã thoát (Exit code):** 0 nếu thành công, khác 0 nếu lỗi.
- **Ví dụ chuẩn:**
  ```bash
  node .agents/skills/hand-drawn-animation/scripts/render.mjs ~/Downloads/my_animation.html --out ~/Downloads
  ```

---

## 5. Tham Khảo Kỹ Thuật (References)

Agent PHẢI đọc các tài liệu tham khảo phù hợp trước khi tạo phim:

| File | Khi nào đọc |
|------|-------------|
| `references/style.md` | **Luôn luôn** — 5 looks và quality gates |
| `references/redrawn-animation.md` | Khi vẽ nhân vật hoạt hình |
| `references/motion.md` | Khi animation chuyển động hoặc camera |
| `references/architecture.md` | Khi cần hiểu core APIs và export |
| `references/studio.md` | Exposure tracks, stable strokes, IK |
| `references/doodle.md` | Khi dùng look doodle (vẽ trên ảnh) |
| `references/found-motion.md` | Khi dùng rotoscope |
| `references/sand.md` | Khi dùng sand animation |
| `references/paper3d.md` | Khi dùng pop-up paper 3D |
| `references/mixed-media.md` | Khi kết hợp nhiều phong cách |
| `references/brief-template.md` | Template để điền brief phim |
| `references/palettes.md` | Bảng màu có sẵn |
| `references/scenes.md` | Cấu trúc cảnh và bố cục |
| `references/reference-films.md` | Tham khảo phim lịch sử |

---

## 6. Cấu Trúc File

```
.agents/skills/hand-drawn-animation/
├── SKILL.md                          # Hướng dẫn chi tiết (file này)
├── LICENSE                           # MIT License (Alexey Fateev)
├── README.md                         # Tài liệu gốc từ upstream
├── assets/                           # Engine core
│   ├── core.js                       # Colour, palettes, marks, camera, timeline, player
│   ├── cels.js                       # Cel animation, exposure sheets, brushes
│   ├── studio.js                     # Exposure tracks, stable strokes, IK
│   ├── materials.js                  # Deformation, construction helpers
│   ├── roto.js                       # Rotoscope engine
│   ├── sand.js                       # Sand animation engine
│   ├── paper3d.js                    # Pop-up book engine
│   └── film-template.html            # Template runtime wiring
├── references/                       # 14 tài liệu hướng dẫn kỹ thuật
│   ├── style.md                      # 5 looks + quality gates
│   ├── redrawn-animation.md          # Character workflow
│   ├── motion.md                     # Motion principles
│   ├── architecture.md               # Core APIs & export
│   ├── studio.md                     # Exposure, strokes, IK
│   ├── doodle.md                     # Photo sourcing & masking
│   ├── found-motion.md               # Rotoscope guide
│   ├── sand.md                       # Sand animation guide
│   ├── paper3d.md                    # Pop-up paper guide
│   ├── mixed-media.md                # Multi-technique films
│   ├── brief-template.md             # Film brief template
│   ├── palettes.md                   # Colour presets
│   ├── scenes.md                     # Scene composition
│   └── reference-films.md            # Historical references
├── scripts/                          # Build & render pipeline
│   ├── render.mjs                    # Headless Chrome → PNG → ffmpeg → MP4
│   ├── verify.mjs                    # Quality verification
│   ├── photo.mjs                     # Photo processing (cho look doodle)
│   ├── roto.py                       # Python rotoscope extraction
│   ├── package.json                  # Node dependencies
│   └── package-lock.json
└── examples/                         # Film samples
    ├── sketchbook-bird.html          # Study cơ bản (6s, 9 keys, pencil/ink)
    └── becoming-phoenix/             # Phim hoàn chỉnh 60s, 5 styles
        ├── phoenix.html              # Entry point
        ├── art.js                    # Art direction
        ├── bird-drawings.js          # Character drawings
        ├── continuity.js             # Cross-scene continuity
        ├── media-scenes.js           # Scene definitions
        ├── photos.js                 # Photo assets (base64)
        ├── scene-helpers.js          # Scene utility functions
        ├── score.js                  # Synthesized music score
        ├── styles.js                 # Style configurations
        ├── README.md                 # Film documentation
        └── SOURCES.md                # Photo attribution
```

---

## 7. Liên Kết Với Các Skill Khác

Phim hoạt hình từ skill này có thể kết hợp với các skill AIWF khác:

| Skill | Cách kết hợp |
|-------|-------------|
| **long-tieng** (#12) | Lồng tiếng thuyết minh cho phim hoạt hình |
| **phu-de** (#8) | Thêm phụ đề song ngữ VI/JP |
| **video-studio** (#video-studio) | Ghép clip hoạt hình vào video stock |

**Ví dụ workflow**: Tạo phim 60s bằng `hand-drawn-animation` → xuất MP4 → `long-tieng` lồng tiếng Việt → `phu-de` thêm phụ đề Nhật.

---

## 8. Quy Chuẩn Vận Hành & Giao Thức Bàn Giao

### Tiếp nhận Đầu vào (Input Intake)
1. **Brief ý tưởng**: Chủ đề phim, thời lượng dự kiến (10s - 60s), phong cách nghệ thuật lựa chọn (`Ink`, `Riso`, `Screen`, `Pencil`, `Doodle`).
2. **Hình ảnh/Video tham chiếu (nếu có)**: Video chuyển động mẫu cho Rotoscope hoặc ảnh nền cho Doodle look.

### Nguyên Tắc Thực Thi
1. **Zero External LLM API**: Kỹ năng vận hành hoàn toàn bằng logic JavaScript Canvas 2D cục bộ và agent tích hợp sẵn, không gọi REST API ngoài, không yêu cầu API key cho việc sinh hoạt hình.
2. **Autonomous Execution**: Khi được kích hoạt, agent tự chạy liên tục: brief → thiết kế → animation → render → verify → xuất MP4, không tự dừng giữa chừng.

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> Thành phẩm HTML player và video MP4 kết xuất PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/` hoặc thư mục do người dùng chỉ định).
> TUYỆT ĐỐI KHÔNG lưu video render hoặc chuỗi ảnh tạm PNG vào thư mục gốc repository.

### Checklist Quality Gate (Tự Thẩm Định Trước Khi Bàn Giao)
- [ ] **Frame Rate & Timing**: Đảm bảo animation chạy mượt mà ở 24fps, không giật lag.
- [ ] **Style Consistency**: Đúng phong cách và bảng màu quy định trong palette đã chọn.
- [ ] **Asset Integrity**: Đường dẫn thư viện JS, Canvas context 2D được khởi tạo không lỗi console.
- [ ] **Render Verification**: Lệnh headless Chrome và ffmpeg xuất MP4 thành công, audio/visual khớp nhau và có bằng chứng file kích thước > 0.
- [ ] **Output Isolation**: File kết quả đã xuất đúng `<output_dir>`, không để sót file tạm trong repository.

### Giao thức Bàn Giao Sạch (Clean Delivery Protocol)
- Khung chat chỉ hiển thị báo cáo tóm tắt ngắn gọn: Phong cách đã vẽ, số phân cảnh, thời lượng, và đường dẫn tuyệt đối đến file MP4 / HTML player trong `<output_dir>`.
- Hướng dẫn mở HTML player để xem trực tiếp hoặc phát file MP4.
