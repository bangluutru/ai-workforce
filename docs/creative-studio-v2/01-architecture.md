# AIWF CREATIVE STUDIO 2.0 — KIẾN TRÚC MỤC TIÊU & THIẾT KẾ KỸ THUẬT

> **Mã tài liệu:** `docs/creative-studio-v2/01-architecture.md`  
> **Giai đoạn:** Phase 0 — Target Architecture Design  
> **Phiên bản kiến trúc:** v2.0-draft  
> **Chiến lược:** Incremental, Reversible, Evidence-Driven, Shared-Engine First (R7)

---

## 1. SƠ ĐỒ LUỒNG VẬN HÀNH TỔNG THỂ (TARGET PIPELINE)

```
                       Creative Request (Yêu cầu sáng tạo)
                                      │
                                      ▼
                        Creative Brief (Bản tóm tắt)
                                      │
                                      ▼
                   Storyboard Planner (Lập kịch bản phân cảnh)
                                      │
                                      ▼
                 Scene Specification (Đặc tả từng cảnh v2.0)
                                      │
                                      ▼
                    Motion Director (Điều phối chuyển động)
                                      │
                                      ▼
                     Render Router (Bộ định tuyến kết xuất)
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
                 ▼                                         ▼
   Existing Video Pipeline (v1)              Motion Renderer (v2 - Sandbox)
   (Stock footage + Ken Burns + ffmpeg)      (HyperFrames / Canvas Adapter)
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      │
                                      ▼
                         Audio Integration (Lõi âm thanh R7)
                         • VieNeu-TTS (vi) / Kokoro (en/ja)
                         • Whisper round-trip verification (CER)
                         • BGM ducking (-16 LUFS, fade 150/350ms)
                         • ASS karaoke / subtitles
                                      │
                                      ▼
                            Final Render (Xuất MP4)
                                      │
                                      ▼
                     Visual QA 2.0 (Kiểm định thị giác)
                     • Frame Sampler (Start, Mid, End, Transitions)
                     • Technical QA (ffprobe, duration, loudness)
                     • Visual QA (dark-lines, boil/dead-shot, text-overflow)
                     • Contact Sheet Generator (review/contact_sheet.jpg)
                                      │
                                      ▼
                         Review / Auto-Repair Loop
                                      │
                                      ▼
                       Delivery (Gói bàn giao sạch)
                       Mặc định: ~/Downloads/AIWF_Output/
```

---

## 2. NGUYÊN TẮC BẢO TOÀN PIPELINE CŨ & CƠ CHẾ DỰ PHÒNG (FALLBACK)

1. **Bảo toàn 100% Video Studio v1:**
   - Script `video-studio/scripts/video_pipeline.py` tiếp tục hoạt động độc lập, không bị thay đổi logic cốt lõi.
   - Các kịch bản dạng `video_script.json` truyền thống tiếp tục được render bình thường mà không cần sửa đổi.
2. **Bảo toàn 100% Hand-Drawn Animation:**
   - Giữ nguyên các kịch bản vẽ tay Canvas 2D (`render.mjs`, `qa.mjs`, `verify.mjs`).
3. **Cơ chế Fallback thông minh (Graceful Fallback):**
   - Nếu bộ kết xuất đồ họa động mới gặp lỗi (thiếu phụ thuộc, lỗi render, timeout):
     - Ghi nhận chi tiết nhật ký lỗi chẩn đoán (`_process/render_error.log`).
     - Tuyệt đối không xóa hoặc ghi đè lên thành phẩm hợp lệ đã có trước đó.
     - Kích hoạt pipeline truyền thống khi và chỉ khi nội dung kịch bản tương thích (có thể minh họa bằng ảnh/stock footage tương đương).
     - Báo cáo rõ ràng cho người dùng về việc đã kích hoạt chế độ fallback, lý do và sự khác biệt về hình ảnh.

---

## 3. CẤU HÌNH CỜ TÍNH NĂNG (FEATURE FLAGS)

Toàn bộ năng lực Creative Studio 2.0 được bảo vệ bởi cờ cấu hình và **mặc định ở trạng thái TẮT (Opt-in)**:

```json
{
  "creative_studio_v2": {
    "enabled": false,
    "motion_renderer": "disabled",
    "visual_qa_v2": false,
    "audio_driven_timeline": false,
    "motion_presets": false,
    "legacy_fallback": true
  }
}
```

* Khi `enabled: false`: Toàn bộ các lệnh gọi vào `video-studio` hoặc `W1-phong-media` đều chạy theo đường dẫn v1 an toàn tuyệt đối.
* Khi `enabled: true`: Hệ thống cho phép chọn `motion_renderer` và kích hoạt các module v2 tương ứng.

---

## 4. HỢP ĐỒNG DỮ LIỆU CỐT LÕI (CORE DATA CONTRACTS)

### 4.1 Storyboard Schema v2.0 (`storyboard_schema.py`)
Mọi kịch bản phân cảnh đồ họa chuyển động phải tuân thủ nghiêm ngặt schema JSON:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AIWFCreativeStoryboardV2",
  "type": "object",
  "required": ["schema_version", "project_id", "fps", "resolution", "scenes"],
  "properties": {
    "schema_version": { "type": "string", "enum": ["2.0"] },
    "project_id": { "type": "string", "pattern": "^[a-zA-Z0-9_-]+$" },
    "title": { "type": "string" },
    "fps": { "type": "integer", "enum": [24, 30, 60] },
    "resolution": {
      "type": "object",
      "required": ["width", "height"],
      "properties": {
        "width": { "type": "integer", "minimum": 360, "maximum": 3840 },
        "height": { "type": "integer", "minimum": 360, "maximum": 3840 }
      }
    },
    "brand_profile": { "type": "string", "default": "default" },
    "scenes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["id", "type", "duration_seconds", "visual_goal"],
        "properties": {
          "id": { "type": "string", "pattern": "^scene-[0-9]{3,}$" },
          "type": { "type": "string", "enum": ["motion_graphics", "stock_media", "photo_kenburns", "hand_drawn"] },
          "duration_seconds": { "type": "number", "minimum": 0.5, "maximum": 120.0 },
          "narration": { "type": "string" },
          "visual_goal": { "type": "string" },
          "composition": {
            "type": "object",
            "properties": {
              "layout": { "type": "string", "enum": ["centered", "split_left", "split_right", "top_bottom", "grid", "card_stack"] },
              "primary_subject": { "type": "string" },
              "background_type": { "type": "string", "enum": ["solid", "gradient", "pattern", "video", "image"] }
            }
          },
          "motion": {
            "type": "object",
            "properties": {
              "preset": { "type": "string" },
              "intensity": { "type": "string", "enum": ["subtle", "moderate", "energetic"] },
              "easing": { "type": "string", "enum": ["linear", "ease-in", "ease-out", "ease-in-out", "spring"] }
            }
          },
          "transition": {
            "type": "object",
            "properties": {
              "type": { "type": "string", "enum": ["none", "fade", "slide_left", "slide_right", "zoom", "wipe"] },
              "duration_seconds": { "type": "number", "minimum": 0.1, "maximum": 2.0 }
            }
          },
          "assets": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "path"],
              "properties": {
                "id": { "type": "string" },
                "type": { "type": "string", "enum": ["image", "video", "audio", "font", "vector"] },
                "path": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

### 4.2 Brand Motion Profile (`brand_profile.py`)
Định hình ngôn ngữ thị giác và chuyển động nhất quán cho từng thương hiệu:

```json
{
  "brand_id": "default",
  "version": 1,
  "colors": {
    "primary": "#14213D",
    "secondary": "#2EC4B6",
    "accent": "#FCA311",
    "background": "#FFFFFF",
    "surface": "#F8F9FA",
    "text": "#000000"
  },
  "typography": {
    "title_font": "Be Vietnam Pro",
    "body_font": "Be Vietnam Pro",
    "mono_font": "Roboto"
  },
  "motion": {
    "intensity": "moderate",
    "default_easing": "ease-out",
    "transition_style": "smooth",
    "stagger_delay_seconds": 0.08
  },
  "safe_area": {
    "horizontal_percent": 8,
    "vertical_percent": 8
  }
}
```

---

## 5. MOTION DIRECTOR & PHÉP TÍNH CHUYỂN ĐỘNG (MOTION SPECIFICATION)

Motion Director đóng vai trò làm cầu nối giữa ý định kịch bản và các thông số chuyển động vật lý từng khung hình:
1. **Thuộc tính chuyển động bắt buộc:**
   - `position`: Toạ độ $[x, y]$ tương đối hoặc pixel.
   - `scale`: Tỷ lệ phóng to $[sx, sy]$ từ tâm neo (`transform-origin`).
   - `rotation`: Góc xoay tính theo độ (degrees).
   - `opacity`: Độ mờ từ $0.0$ đến $1.0$.
   - `timing`: Thời điểm bắt đầu `start_time` và kết thúc `end_time`.
   - `easing`: Hàm nội suy đường cong (`linear`, `ease-in`, `ease-out`, `ease-in-out`, `cubic-bezier(x1, y1, x2, y2)`).
   - `stagger`: Độ trễ nối tiếp giữa các ký tự hoặc phần tử con.
   - `layer_order`: Thứ tự hiển thị z-index chống chồng đè sai lệch.
2. **Tính tất định (Determinism):**
   - Tuyệt đối cấm sử dụng `Math.random()` hoặc hàm ngẫu nhiên tự do không có seed trong logic tạo chuyển động.
   - Mọi yếu tố biến thiên phải được sinh ra từ hàm giả ngẫu nhiên có hạt giống tất định (`rng(seed)` hoặc `hash(k, seed)`).

---

## 6. HỆ THỐNG KIỂM ĐỊNH KÉP TRƯỚC KHI BÀN GIAO (DUAL REVIEW SYSTEM)

Tuân thủ nghiêm ngặt Luật R3 §9 và Section 18-19 của Chỉ thị:

### Góc nhìn 1 — Thẩm định Kỹ thuật (Technical Perspective)
* **File integrity & Metadata:** Dùng `ffprobe` xác minh video codec (H.264), audio codec (AAC), kích thước (1080x1080, 1920x1080, hoặc 1080x1920), số khung hình thực tế và thời lượng trong dung sai $\pm 0.5\text{s}$.
* **Loudness:** Đo chuẩn âm lượng EBU R128 qua `ffmpeg_tools.loudness()`, đảm bảo nằm trong dải $-16 \pm 1$ LUFS, đỉnh không vượt quá $-1.5$ dBTP.
* **Phát hiện lỗi kỹ thuật tự động (Automated Defect Detection):**
  - Khung hình đen/trống (`blank frames`).
  - Cảnh đứng hình không chuyển động (`dead shots`).
  - Rung giật nhiễu loạn (`frame boil`).
  - Lệch âm thanh (`audio-video duration mismatch`).
  - Thoát lề an toàn (`safe-area violations`).

### Góc nhìn 2 — Thẩm định Trải nghiệm Người dùng (User Experience Perspective)
* **Độ dễ đọc trên thiết bị di động:** Chữ tiêu đề và phụ đề rõ ràng, không bị che khuất bởi giao diện của TikTok/Reels hay viền màn hình điện thoại.
* **Nhịp thở và thị giác:** Sự chuyển động ăn khớp với giọng nói, không quá nhanh gây rối mắt hay quá chậm gây buồn ngủ.
* **Tổ chức bàn giao sạch:** File lưu tại `<output_dir>`, có `contact_sheet.jpg` tổng quan các phân cảnh, kèm file báo cáo kỹ thuật `technical_report.json` và bảng ghi công `credits.txt`. Khung chat chỉ tóm tắt ngắn gọn.
