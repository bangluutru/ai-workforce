---
name: Tạo Hoạt Hình
description: >-
  Tạo phim hoạt hình vẽ tay bằng Canvas 2D — 5 phong cách (ink, riso, screen,
  pencil, doodle), rotoscope, sand animation, pop-up paper 3D. Xuất HTML player
  + MP4 offline. Dựa trên alesha-pro/tools (MIT License).
context: fork
trigger_keywords:
  - hoạt hình vẽ tay
  - hand drawn animation
  - canvas animation
  - phim hoạt hình
  - rotoscope
  - sand animation
  - animated short film
  - doodle animation
  - vẽ hoạt hình
  - ink animation
  - riso animation
  - pencil animation
  - pop-up paper
  - phim ngắn hoạt hình
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

### Bước 4: Render thành MP4

```bash
# Render phim từ file HTML
node .agents/skills/hand-drawn-animation/scripts/render.mjs \
  --input path/to/your-film.html \
  --output ~/Downloads/my-animation.mp4

# Kiểm tra chất lượng
node .agents/skills/hand-drawn-animation/scripts/verify.mjs \
  --input path/to/your-film.html
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

## 8. Quy Chuẩn Vận Hành

1. **Rule R0 & R1:** Mọi engine, script và reference được lưu trong workspace để đồng bộ Git. Video/MP4 thành phẩm xuất vào `~/Downloads/`, tuyệt đối không gây bloat repo.
2. **Rule R2:** Không hardcode credentials. File ảnh dùng cho look doodle lấy từ nguồn CC0/Public Domain.
3. **Rule R3:** Khi được kích hoạt, agent tự chạy liên tục: brief → thiết kế → animation → render → verify → xuất MP4.
4. **Context: fork** — Skill này sử dụng subagent riêng (`context: fork`) vì workflow tốn context nặng (thiết kế nhân vật + animation + render).
