---
name: video-studio
display-name: Studio Video
description: >-
  Biên tập và sản xuất video tự động từ kịch bản hoặc ý tưởng; hỗ trợ tìm kiếm stock media (Pexels/Pixabay), ghép audio thuyết minh, nhạc nền BGM ducking và phụ đề karaoke xuất file MP4.
  USE WHEN: Người dùng muốn sản xuất video hoàn chỉnh đa phương tiện từ kịch bản hoặc ý tưởng.
  DO NOT USE WHEN: Chỉ cần tạo/dịch phụ đề cho video có sẵn (dùng 'phu-de'), chỉ cần lồng tiếng/thuyết minh audio đơn lẻ (dùng 'long-tieng'), hoặc tạo hoạt hình vẽ tay 2D (dùng 'hand-drawn-animation').
trigger: Studio Video, biên tập video tự động, làm video từ kịch bản, dựng video
category: content
needs_file: false
file_filter: any
---

# 🎬 AIWF Video Studio & Automated Pipeline

## 1. Mô tả
Video Studio là hệ thống sáng tạo và biên tập video đa năng trong AIWF:
1. **Automated One-Click Pipeline:** Tự động chuyển hoá ý tưởng thành video hoàn chỉnh (kịch bản $\rightarrow$ thuyết minh TTS $\rightarrow$ video stock $\rightarrow$ nhạc nền BGM ducking $\rightarrow$ phụ đề karaoke $\rightarrow$ MP4).
2. **Web Studio Editor (localhost:8800):** Giao diện web trực quan chuyên nghiệp với biểu tượng Lucide SVG, Waveform sóng âm, phát hiện nhịp beat bằng `librosa`, và multi-track timeline.

---

## 2. Các Tính Năng Nổi Bật

### 💎 Phân cấp chất lượng: Free vs Premium Tier
- **Mặc định (`--tier free`):** 100% miễn phí, tận dụng API Pexels (1080p Full HD), Pixabay API, Edge-TTS Neural, và kho nhạc CC bản quyền sạch.
- **Tùy chọn (`--tier premium`):** Kích hoạt profile phòng thu cao cấp: ưu tiên footage 4K UHD nguyên bản từ Pexels/Pixabay, kết nối các API stock trả phí (nếu có key trong `.env`), và giọng đọc chuẩn studio.

### 🗣️ Ưu tiên ngôn ngữ (Language Priority)
- **Tiếng Việt Ưu tiên 1 (`--lang vi`):** Thuyết minh tiếng Việt chuẩn truyền cảm, phụ đề tiếng Việt cỡ lớn nổi bật (karaoke chữ chạy vàng gold), kèm dòng phụ đề tiếng Nhật sắc nét phía dưới.
- **Tiếng Nhật Ưu tiên 2 (`--lang ja`):** Thuyết minh tiếng Nhật (Nanami Neural), phụ đề tiếng Nhật kèm dòng dịch tiếng Việt.

### 🎧 Auto-Ducking BGM (Sidechain Compression)
- Tự động tìm kiếm nhạc nền phù hợp với tâm trạng kịch bản (`traditional`, `peaceful`, `energetic`, `emotional`, `urban`).
- Tích hợp bộ lọc `sidechaincompress` của FFmpeg: BGM tự động hạ âm lượng êm ái khi người thuyết minh cất tiếng nói và dâng nhẹ lại khi dứt câu.

### 🎨 Phụ đề Karaoke Song ngữ mượt mà
- Engine render PIL kết hợp font Hiragino Sans GB CJK & Arial Unicode, triệt tiêu hoàn toàn lỗi font hoặc thiếu glyph tiếng Nhật / tiếng Việt.
- Hiệu ứng chữ chạy karaoke từng ký tự (character-by-character highlight).

---

## 3. Hướng Dẫn Sử Dụng

### Cách 1: Tạo Video Tự Động 1-Click (CLI Pipeline)

```bash
# Kích hoạt môi trường
source .venv-tts/bin/activate

# Tạo video mặc định (Free Tier, Tiếng Việt ưu tiên 1, Nhật ưu tiên 2)
python3 .agents/skills/video-studio/scripts/video_pipeline.py \
  --topic "Cuộc sống tươi đẹp ở Nhật Bản" \
  --tier free \
  --lang vi

# Hoặc kích hoạt chế độ Premium 4K UHD Studio:
python3 .agents/skills/video-studio/scripts/video_pipeline.py \
  --topic "Cuộc sống tươi đẹp ở Nhật Bản" \
  --tier premium \
  --lang vi \
  --output ~/Downloads/beautiful_japan_v2/Beautiful_Japan_Premium.mp4
```

### Cách 2: Giao diện Web Studio (localhost:8800)

```bash
python3 .agents/skills/video-studio/scripts/video_studio_server.py --port 8800
```
Mở trình duyệt tại: `http://localhost:8800`

---

## 4. Cấu Trúc Script & API Keys

```
.agents/skills/video-studio/
├── SKILL.md                          # Hướng dẫn chi tiết
├── config/
│   └── mood_keywords.json            # Mapping tâm trạng -> từ khóa BGM
├── templates/
│   └── .env.example                  # File mẫu cấu hình API keys
└── scripts/
    ├── stock_fetcher.py              # Bộ tìm kiếm & tải stock (Pexels, Pixabay, YouTube fallback)
    ├── audio_mixer.py                # Engine trộn âm thanh, ducking & chuẩn hóa
    ├── scene_builder.py              # Đo đạc timeline TTS, scale clip, render karaoke
    ├── video_pipeline.py             # Pipeline tự động 1-click
    ├── beat_detector.py              # Phân tích nhịp nhạc BPM bằng librosa
    └── video_studio_server.py        # Web UI server
```

### Cấu hình `.env`
Sao chép file mẫu rồi điền API keys của bạn (đăng ký miễn phí):
```bash
cp .agents/skills/video-studio/templates/.env.example .env
# Mở .env và điền keys theo hướng dẫn trong file mẫu
# Pexels: https://www.pexels.com/api/  |  Pixabay: https://pixabay.com/api/docs/
```

---

## 5. Quy Chuẩn Vận Hành & Bảo Vệ Codebase

### Path Resolution & Anti-Repo Bloat
| Placeholder | Quy ước đường dẫn |
|---|---|
| `<output_dir>` | Nơi người dùng chỉ định hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | `_process/video_[timestamp]/` (được bảo vệ bởi `.gitignore`) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> Video MP4, âm thanh và tệp ảnh stock trung gian TUYỆT ĐỐI KHÔNG lưu vào thư mục gốc repository. Toàn bộ xuất bản lưu vào `<output_dir>`.

### Quy Định Về API & Zero External LLM API
- **LLM Reasoning:** 100% sử dụng năng lực suy luận của mô hình Antigravity IDE (Gemini 3.8/Claude) để viết kịch bản, phân cảnh và căn chỉnh thời lượng. Tuyệt đối không gọi external LLM API.
- **Media Service APIs:** Pexels và Pixabay là các Data/Media Service API tùy chọn phục vụ việc kéo video/ảnh stock miễn phí về máy cục bộ. Nếu không có API keys, hệ thống tự động fallback sử dụng asset cục bộ hoặc màu nền đồ họa.

---

## 6. Quy Trình Vận Hành & Quality Gate

### Bước 1: Tiếp Nhận Phân Cảnh (Intake)
- Tiếp nhận văn bản kịch bản hoặc chủ đề video từ người dùng.
- Phân tích thời lượng dự kiến, phong cách hình ảnh (mood) và tỷ lệ khung hình (16:9 ngang hoặc 9:16 dọc TikTok/Shorts).

### Bước 2: Tự Chủ Thực Thi (Autonomous Full-Run)
- Tạo âm thanh thuyết minh và phụ đề.
- Tìm kiếm và tải stock video phù hợp theo từng phân cảnh.
- Trộn nhạc nền với cơ chế tự động giảm âm khi có tiếng nói (Smart Audio Ducking).

### Bước 3: Quality Gate & Giao Thức Bàn Giao Sạch
1. ✅ **Audio Ducking:** Âm lượng nhạc nền giảm xuống 15-20% khi có tiếng đọc thuyết minh, không át giọng nói.
2. ✅ **Beat Alignment:** Chuyển cảnh khớp với nhịp beat của nhạc nền.
3. ✅ **Subtitles Fidelity:** Phụ đề hiển thị rõ ràng, không bị tràn viền khung hình (an toàn lề 5%).
4. ✅ **Bảo Vệ Codebase:** Tệp video thành phẩm `.mp4` được lưu đúng vào `<output_dir>`.
5. ✅ **Clean Delivery:** Khung chat chỉ tóm tắt thời lượng video, số phân cảnh và cung cấp đường dẫn tệp MP4 để người dùng mở xem ngay.

---

## 7. CLI CONTRACT

> **Quy tắc đọc helper script:** Sử dụng CLI contract dưới đây trước tiên. Chỉ đọc mã nguồn script khi: (1) lệnh theo contract bị lỗi cần debug, (2) cần hành vi chuyên biệt chưa được document, hoặc (3) cần sửa đổi script.
> 
> **Kỷ luật Sản xuất Video (Optimization C):**
> 1. Chuẩn bị kịch bản (nếu có kịch bản tùy biến, lưu file JSON tạm trong `_process/script.json`).
> 2. Gọi script pipeline 1 lần duy nhất với các cờ tham số chính xác.
> 3. Tránh chạy đi chạy lại nhiều lệnh thử nghiệm ffmpeg nếu pipeline chính đã tự động hóa 100%.

### `scripts/video_pipeline.py`
- **Mục đích:** Biên tập và sản xuất video hoàn chỉnh tự động (TTS + Stock Footage + BGM Smart Ducking -14dB + Phụ đề Karaoke).
- **Cú pháp:** `python3 .agents/skills/video-studio/scripts/video_pipeline.py --topic <tên_chủ_đề> [tùy_chọn]`
- **Tham số chính:**
  - `--topic <chuoi>`: (Bắt buộc) Chủ đề hoặc tên video
  - `--output <path>`: Đường dẫn tệp video MP4 đầu ra (khuyến nghị: `~/Downloads/<tên>.mp4`)
  - `--script <path>`: Đường dẫn tệp kịch bản JSON tùy biến (cấu trúc gồm các scene với `vi`, `jp`, `keywords`)
  - `--mood <peaceful|traditional|energetic|emotional|urban>`: Tâm trạng nhạc nền
  - `--ducking <ratio>`: Tỷ lệ nén âm lượng nhạc nền khi có giọng đọc (mặc định: `14.0` tương ứng -14dB)
  - `--lang <vi|ja>`: Ngôn ngữ thuyết minh ưu tiên (mặc định: `vi`)
  - `--tier <free|premium>`: Chất lượng phân giải (`free` HD/FHD, `premium` 4K)
  - `--json`: Xuất kết quả tóm tắt dạng JSON máy đọc súc tích
- **Kết quả:** Tệp video thành phẩm `.mp4` tại đường dẫn `--output` hoặc `~/Downloads/`.
- **Mã thoát (Exit code):** 0 nếu thành công, khác 0 nếu lỗi.
- **Ví dụ mẫu:**
  ```bash
  python3 .agents/skills/video-studio/scripts/video_pipeline.py \
    --topic "Cà phê nguyên chất" \
    --mood energetic \
    --ducking 14.0 \
    --output ~/Downloads/ca_phe_quang_cao.mp4 \
    --json
  ```

