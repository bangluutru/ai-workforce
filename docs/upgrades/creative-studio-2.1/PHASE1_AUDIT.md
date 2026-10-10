# Phase 1 — Audit hiện trạng Creative Studio 2.0

Baseline: `9e4ccb4` (tag `pre-creative-studio-2.1`). Nhãn: OBSERVED = đã đọc mã/chạy lệnh; DERIVED = suy ra; NOT VERIFIED = chưa kiểm.

## 1. Phát hiện chính (P0)

**F1. Đường audio của `StoryboardRenderer` là "Documented Only".** (OBSERVED)

- `storyboard_renderer.py` docstring dòng 6 nói "trộn âm thanh narration + BGM".
- Mã thực tế (dòng 275-297) chỉ tạo track im lặng `anullsrc` rồi mux. Không có lệnh gọi TTS, `dub_engine`, BGM hay ducking nào trong file.
- `narration` của cảnh chỉ được đưa vào `props["subtitle"]` (dòng 162-163), tức hiển thị thành chữ, không thành tiếng.
- Kết luận: **đây là đường xử lý chưa hoàn thiện, không phải silent fallback có chủ đích.** Bằng chứng: không có nhánh điều kiện, không có cờ chọn chế độ, không có cảnh báo "video không tiếng" nào trong kết quả.

**F2. `plan_scene_timeline` và `motion_director` không có call site trong renderer.** (OBSERVED qua grep)

- `plan_scene_timeline` (nhận `audio_duration`, có logic `scene_dur = max(scene_dur, audio_duration + 0.5)`) chỉ được export trong `creative/__init__.py`; `StoryboardRenderer` không gọi.
- `motion_director` cũng chỉ được export, không được renderer gọi. Chuyển động hiện do preset HTML tự quyết.
- Hệ quả: logic đồng bộ audio-timeline **tồn tại nhưng chưa nối vào pipeline** (Implemented but Not Integrated).

**F3. Cờ `audio_driven_timeline: true` không được mã nào đọc.** (OBSERVED: chỉ xuất hiện trong `creative_studio_v2.json`)

Cờ đang bật nhưng không điều khiển gì. Dễ gây hiểu nhầm rằng tính năng đang chạy.

**F4. QA không phân biệt "im lặng chủ đích" với "đáng ra phải có tiếng".** (OBSERVED, đã đính chính sau khi đo)

- Renderer truyền `expected_spec` chỉ gồm `duration/width/height/fps`, không có `require_audio`.
- Đo thật: `loudness()` trên track `anullsrc` trả **−70.0 LUFS**, nên validator cũ phát `WARN audio_too_quiet` cho mọi video im lặng. (Bản đầu của báo cáo này ghi NOT VERIFIED; đã đo và xác nhận.)
- Vấn đề còn lại: WARN này không phân biệt được video không tiếng chủ đích với video lẽ ra phải có giọng. Không có mức FAIL cho "cần tiếng mà im lặng".

## 2. Chính sách QA khi lỗi (Phase 1 §4.3)

| Tình huống | Hành vi hiện tại (OBSERVED) | Đánh giá |
|---|---|---|
| DOM QA ném exception | `logger.warning`, bỏ qua, **không ghi vào `warnings` hay report** | Lỗi: bị nuốt, trông giống PASS. Cần trạng thái SKIPPED |
| Contact sheet lỗi | `except Exception: sheet_path = None` im lặng | Lỗi: không có dấu vết SKIPPED |
| Renderer kích hoạt fallback | Ghi `fallback_used`, `degraded`, `warnings` | Tốt |
| DOM issue mức FAIL | Chỉ thành chuỗi trong `warnings`, **không chặn render** | Cần xác định: FAIL hay WARNING? |
| FFprobe thiếu | Chưa đọc đủ `technical_validator` để kết luận | NOT VERIFIED |
| Verdict tổng | Chỉ có PASS/WARN/FAIL, **không có SKIPPED / NOT VERIFIED** | Thiếu 2 trạng thái directive yêu cầu |

## 3. Capability Matrix

| Khả năng | Phân loại | Bằng chứng |
|---|---|---|
| Render cảnh qua HyperFrames + Canvas fallback | Implemented and Tested | 116 test pass; fallback metadata có |
| 10 Motion Presets | Implemented and Tested | `tests/creative/test_presets.py` |
| Brand Profile | Implemented and Tested | `brand_profile.py`, test có |
| DOM Layout Validator | Implemented and Tested (độc lập) | Chạy trong renderer; lỗi bị nuốt (xem §2) |
| Visual QA 2.0 (ffprobe + frame + contact sheet) | Implemented and Tested | `report_builder.py` |
| Voice-over cho storyboard | **Missing** trong Creative Studio | F1 |
| BGM + ducking cho storyboard | **Missing** trong Creative Studio | F1 (nhưng engine có sẵn ở `dub_engine.mix`) |
| Đồng bộ narration ↔ độ dài cảnh | **Implemented but Not Integrated** | F2 |
| Motion Director | **Implemented but Not Integrated** | F2 |
| Beat snapping | Implemented but Not Integrated | F2 |
| Audio QA (ngoài LUFS/peak) | Missing | Không có kiểm tra narration present/ducking/cắt câu |
| Trạng thái SKIPPED/NOT VERIFIED trong QA | Missing | §2 |

## 4. Khả năng tái sử dụng cho Phase 2 (R7)

`_shared/media/dub_engine.py` đã có đủ (OBSERVED):

- `synthesize(lines, lang, voice, gender, work, ...)` → TTS + Whisper kiểm tra + cache; engine thiếu thì `RuntimeError`, không đổi engine ngầm.
- `plan_fit(lines, video_dur, max_tempo=1.25, ...)` → tính tempo/overflow.
- `mix(original, placed, out_path, video_dur, bg_volume, duck_level, ...)` → trộn BGM + ducking + loudnorm −16 LUFS.
- `video_pipeline.py` (Dual-Track v1) đã dùng đúng bộ này trong thực tế (video 81.3s/79.2s hôm nay có giọng, −16.1 LUFS), nên engine đã được chạy thật (OBSERVED qua log hôm nay).

→ **Không cần viết TTS/mixer mới.** Phase 2 chỉ là lớp keo trong `creative/` gọi `dub_engine`.

## 5. Tương thích schema (Audio Contract)

- `storyboard_schema.py`: không có `additionalProperties` (grep trống). `storyboard_validator.py` dòng 60-130 chỉ kiểm các trường biết trước. (OBSERVED một phần; dòng 130-229 của validator chưa đọc → NOT VERIFIED rằng không có chỗ nào từ chối khóa lạ.)
- Dẫn xuất: thêm khối `audio` ở cấp storyboard là không bắt buộc và nhiều khả năng tương thích ngược, nhưng **phải có test backward-compat** xác nhận (sẽ làm ở Phase 2).

## 6. Rủi ro đã nhận diện

1. Sửa renderer phải giữ nguyên hành vi mặc định cho storyboard cũ. Mặc định an toàn: **không có khối `audio` → giữ hành vi hiện tại** (track im lặng), nhưng bổ sung `warnings` và ghi `audio_mode: "silent_default"` vào report để minh bạch.
2. TTS offline VieNeu tốn vài giây/câu và cần model đã tải; test phải xử lý trường hợp engine vắng (test G).
3. Không đo được hiệu năng nếu không benchmark; sẽ không tuyên bố cải thiện tốc độ.

## 7. Gate 1

**ĐẠT.** Khoảng trống thực tế đã xác định (F1-F4, §2). Không sửa mã nguồn trong Phase 1.

Chưa audit sâu (đưa vào các phase sau, không chặn Gate 1): `render_router.py`, `hyperframes_adapter.py`, `technical_validator.py` toàn bộ, `legacy_adapter.py`, chất lượng từng preset.
