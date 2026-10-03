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

# 🎬 AIWF Video Studio & Automated Pipeline (v2)

## 1. Mô tả
Video Studio là hệ thống sáng tạo và biên tập video đa năng trong AIWF:
1. **Automated One-Click Pipeline:** Tự động chuyển hoá ý tưởng thành video hoàn chỉnh (kịch bản $\rightarrow$ thuyết minh TTS $\rightarrow$ video stock $\rightarrow$ nhạc nền BGM ducking $\rightarrow$ phụ đề karaoke $\rightarrow$ MP4).
2. **Web Studio Editor (localhost:8800):** Giao diện web trực quan chuyên nghiệp với biểu tượng Lucide SVG, Waveform sóng âm, phát hiện nhịp beat bằng `librosa`, và multi-track timeline.

---

## 2. Năng lực (v2 — đã kiểm chứng bằng render thật)

| Khâu | Cách làm | Ghi chú |
|---|---|---|
| Kịch bản | **Agent viết** `script.json` theo `references/script-guide.md` | Pipeline từ chối chạy thiếu `--script` (mẫu cố định chỉ để thử máy: `--allow-template`) |
| Giọng đọc | VieNeu-TTS 48 kHz offline (tiếng Việt), Kokoro offline (en/ja); Whisper nghe lại từng câu, đọc lại câu sai | Dùng chung `_shared/media/dub_engine.py` + `tts.py` (R7), có cache theo câu |
| Hình | `media` của người dùng → Pexels/Pixabay (key trong `.env`) → ảnh CC từ Wikimedia Commons/Openverse (không cần key) + Ken Burns | YouTube chỉ khi `--allow-youtube` (giấy phép không xác minh được) |
| Nhạc | Thư viện CC BY 4.0 (Kevin MacLeod) theo mood, hạ còn 25% khi có lời, −16 LUFS | Ghi công tự động vào `<tên>_credits.txt` |
| Phụ đề | Ngắt câu + ASS dùng chung `_shared/media/ass_generator.py` (Be Vietnam Pro trong `_shared/fonts`, hộp bo góc), tiêu đề + caption cảnh; `|` để agent chỉ định chỗ ngắt | 9:16 tự dùng preset TikTok, đẩy phụ đề lên |
| Bằng chứng | `<tên>_review.jpg` (1 khung/cảnh), `<tên>_credits.txt`, `<tên>_report.json` | Agent PHẢI mở ảnh duyệt |

---

## 3. Quy trình (SOP Autonomous Full-Run)

<instructions>

**B0 — Tiếp nhận (Intake):** mục đích (quảng cáo/giải thích/du lịch/mạng xã hội), thời lượng, nền tảng → tỷ lệ
(YouTube 16:9, TikTok/Reels/Shorts 9:16), ngôn ngữ, giọng, tư liệu người dùng có sẵn (logo, ảnh sản phẩm). Chỉ hỏi khi
thiếu thông tin đổi kết quả (ví dụ tên thương hiệu, giá); còn lại tự quyết và ghi trong kịch bản.

**B1 — Viết kịch bản:** đọc `references/script-guide.md` + `references/example-script.json`, viết
`_process/video_<tên>/script.json`. Tự kiểm theo checklist cuối guide.

**B2 — Render:**
```bash
python3 .agents/skills/video-studio/scripts/video_pipeline.py --topic "<tên>" --script _process/video_<tên>/script.json \
  --output ~/Downloads/AIWF_Output/<tên>/<tên>.mp4 [--aspect 9:16] [--mood corporate] [--voice "Minh Quân Pro"]
```
(~2 phút cho video 30 s lần đầu; render lại dùng cache giọng/clip/shot không đổi.)

**B3 — Duyệt (bắt buộc, lặp tối đa 3 vòng):** MỞ `<tên>_review.jpg` và `<tên>_report.json`:
- Hình sai ngữ cảnh, ảnh ghép/có chữ lạ, cảnh "nền màu (thiếu hình)" → sửa `visuals` (query cụ thể hơn / media).
- `voice_check` có câu đọc sai → viết lại cụm khó đọc trong `narration`.
- Phụ đề ngắt xấu → thêm `|`. Tiêu đề/caption che chủ thể → đổi caption hoặc bỏ.
- `warnings` không rỗng → xử lý từng mục. Sửa xong chạy lại B2.

**B4 — Bàn giao (Clean Delivery):** khung chat chỉ tóm tắt ngắn: thời lượng, số cảnh, tỷ lệ, giọng, nhạc, cảnh báo còn lại,
và đường dẫn tuyệt đối tới MP4 + `_credits.txt` (bắt buộc kèm khi đăng: nhạc/ảnh CC BY yêu cầu ghi công) + `_review.jpg`.
</instructions>

<quality_gate>

### Checklist trước khi bàn giao
- [ ] Kịch bản do agent viết cho đúng chủ đề (không `--allow-template`), câu đầu là hook.
- [ ] Đã mở `_review.jpg`: mọi cảnh có hình khớp lời đọc, không cảnh nền màu, không ảnh có logo/chữ của bên khác.
- [ ] `report.json`: `voice_check` rỗng, `warnings` rỗng (hoặc đã giải thích), −17…−15 LUFS.
- [ ] Không dùng YouTube trừ khi người dùng đồng ý; `_credits.txt` đi kèm video (bằng chứng giấy phép).
- [ ] File nằm trong `<output_dir>`; không file media nào trong repo.
</quality_gate>

---

## 4. Cấu Trúc Script & API Keys

```
.agents/skills/video-studio/
├── SKILL.md                          # Hướng dẫn chi tiết
├── config/
│   ├── music_library.json            # Nhạc CC BY 4.0 theo mood (không cần key)
│   └── mood_keywords.json            # (cũ) mapping tâm trạng -> từ khóa
├── references/
│   ├── script-guide.md               # BẮT BUỘC đọc: cách viết kịch bản
│   └── example-script.json           # Kịch bản mẫu 28 s đã render kiểm chứng
├── templates/
│   └── .env.example                  # File mẫu cấu hình API keys
└── scripts/
    ├── stock_fetcher.py              # Pexels/Pixabay (có key); YouTube chỉ khi --allow-youtube
    ├── open_media.py                 # Ảnh CC Wikimedia Commons/Openverse (không key) + credit
    ├── video_pipeline.py             # Pipeline v2: script.json → MP4 + review/credits/report
    ├── beat_detector.py              # Phân tích nhịp nhạc BPM bằng librosa
    └── video_studio_server.py        # Web UI server

# Engine dùng chung (KHÔNG viết lại trong skill — Luật R7, xem .agents/skills/_shared/ENGINES.md):
.agents/skills/_shared/media/
├── tts.py                            # TTS offline: VieNeu (vi) · Kokoro (en/ja)
├── dub_engine.py                     # synthesize (+Whisper kiểm tra), mix (ducking), loudness
├── ass_generator.py · linebreak.py · semantic_segmenter.py · subtitle_styles.json
└── ffmpeg_tools.py                   # ffmpeg_bin, has_filter, decode/encode, loudness
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

## 6. CLI CONTRACT

### `scripts/video_pipeline.py`
- `--topic` (bắt buộc, đặt tên file) · `--script <json>` (bắt buộc với video thật) · `--output <mp4>`
- `--aspect 16:9|9:16|1:1|4:5` · `--lang vi|en|ja` · `--voice "<VieNeu (vi) hoặc Kokoro (en/ja)>"` · `--gender female|male`
- `--mood corporate|energetic|peaceful|emotional|urban|traditional|playful|epic` · `--bgm <file>` · `--music-level 0.6`
- `--no-subtitles` · `--no-verify-voice` · `--allow-youtube` · `--allow-template` · `--json`
- Đầu ra cạnh MP4: `<tên>_review.jpg`, `<tên>_credits.txt`, `<tên>_report.json`, thư mục cache `_<tên>_work/`.
- Exit 0 = render xong (vẫn phải đọc `warnings`); ≠ 0 = lỗi, đọc stderr.

### `scripts/open_media.py`
`python3 open_media.py --query "<từ khoá tiếng Anh>" --out x.jpg` — thử nhanh một query ảnh CC trước khi đưa vào kịch bản.
