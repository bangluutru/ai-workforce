---
name: Tạo Video
description: "AIWF Video Studio — Hệ thống biên tập và tự động tạo video hoàn chỉnh từ ý tưởng. Hỗ trợ Pexels/Pixabay API, Free/Premium tier, auto beat sync, BGM ducking, và phụ đề karaoke song ngữ."
context: main
trigger_keywords:
  - video studio
  - biên tập video
  - chỉnh sửa video
  - tạo video tự động
  - video pipeline
  - beat sync
  - video editor
  - tạo video từ ý tưởng
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

## 5. Quy Chuẩn Vận Hành
1. **Rule R0 & R1:** Mọi script và template được lưu trong workspace để đồng bộ Git. Video và media thành phẩm lưu vào `~/Downloads/`, tuyệt đối không gây bloat repo.
2. **Rule R2:** API keys luôn đọc qua `.env`, tuyệt đối không hardcode credentials trong mã nguồn.
3. **Rule R3:** Pipeline tự động hoàn thành từ A-Z mà không ngắt quãng hỏi người dùng.
