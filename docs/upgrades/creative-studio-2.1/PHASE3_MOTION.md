# Phase 3 — Motion Quality (Creative Studio 2.1)

Branch `feature/creative-studio-2.1` · Baseline tag `pre-creative-studio-2.1`

## Scope
Cải thiện chất lượng chuyển động theo hướng ít rủi ro, giữ nguyên 10 preset (ID không đổi), Storyboard v2.0, HyperFrames chính + Canvas fallback.

## Findings (OBSERVED)
| ID | Phát hiện |
|----|-----------|
| M1 | Trường `scene.transition` đã có trong schema v2.0 và được validator kiểm tra, nhưng `StoryboardRenderer` **không dùng**: mọi cảnh bị cắt thẳng bằng concat. |
| M2 | 9/10 preset dùng `duration: duration - N` cho đoạn trôi nhẹ cuối cảnh; cảnh ngắn hơn N cho thời lượng âm. |
| M3 | `motion_director` (easing/spring) chỉ được export, renderer không gọi. Preset thật dùng GSAP trực tiếp. **Không nối** (không có bằng chứng cần thiết). |
| M4 | Cắt thẳng làm khung đầu mỗi cảnh gần như trống (hoạt ảnh vào bắt đầu từ trạng thái ẩn). |

## Changes
1. `creative/transitions.py` (mới, glue trên `xfade` của ffmpeg): áp dụng `scene.transition` có sẵn (`none, fade, slide_left, slide_right, zoom, wipe`) và khối tùy chọn `transitions {default, duration, enabled}`.
   - Không khai báo = cắt thẳng như v2.0 (đường concat cũ giữ nguyên).
   - Cảnh có chuyển cảnh phía sau được dựng dài thêm đúng bằng thời lượng chuyển (đuôi chồng lấn) ⇒ mốc bắt đầu cảnh kế và tổng thời lượng **không đổi**, không lệch lời đọc/BGM.
   - Thời lượng kẹp ≤ 45% cảnh ngắn hơn; `duration_seconds ≤ 0` = không chuyển (đúng v2.0).
2. `storyboard_renderer.py`: lập kế hoạch chuyển cảnh, dựng clip dài thêm, ghép bằng filter_complex khi cần.
3. `storyboard_validator.py`: kiểm tra khối `transitions` (không siết thêm trường scene cũ).
4. 9 preset: `Math.max(0.1, duration - N)` chống thời lượng âm.
5. Đăng ký `creative.transitions` trong `engines.json`/`ENGINES.md`.

## Tests / Evidence
- `tests/creative/test_transitions.py`: 8 test (kế hoạch, kẹp, kill-switch, tương thích v2.0, offset filter, render thật, đường cắt cũ).
- Toàn bộ `tests/creative`: **149 passed**; `check_shared_reuse.py` exit 0.
- Hồi quy bắt được trong quá trình làm: validator mới từng chặn `duration_seconds: 0` mà v2.0 cho phép (2 test cũ fail) → đã sửa, không siết chặt hơn v2.0.
- A/B cùng brief (5 cảnh 1280x720, 5 preset, có giọng đọc), HyperFrames cả 10 cảnh, không fallback:
  - `before.mp4` (cắt thẳng) và `after.mp4` (fade + slide_left + wipe): **cả hai 20.000s**, có luồng audio 20.000s.
  - Khung hình giữa chuyển cảnh (4.25s, 8.25s, 12.25s) đã xem trực tiếp: fade pha trộn hai cảnh, slide trượt một nửa thẻ, wipe lộ dần cảnh số liệu. (OBSERVED)
  - Artifact: `~/Downloads/AIWF_Output/creative_2_1_phase3/{before,after}.mp4`.

## Remaining risks / NOT VERIFIED
- **NOT REVIEWED**: độ mượt và thẩm mỹ khi chạy video thật (chỉ xem 3 khung tĩnh, không xem chuyển động). Cần người xem.
- Màu nền preset trong brief mẫu là nền sáng; chưa đánh giá bảng màu.
- `zoom` (xfade `zoomin`) và `slide_right` chưa render thử thật (chỉ kiểm tra tên bộ lọc/đồ thị).
- `legacy_adapter` sinh `transition: fade 0.4` cho mọi cảnh → storyboard chuyển từ v1 qua adapter sẽ có fade (đúng với khai báo, nhưng là thay đổi hình ảnh). Adapter không được gọi ở đâu ngoài export.
- Chưa thêm preset mới; chưa chạm `motion_director`; chưa nghiên cứu `charlie947/motion-graphics-skills` (không sao chép gì).
- GSAP miễn phí cho thương mại theo kết quả tìm kiếm web (chưa đọc nguyên văn giấy phép). Đang nạp từ sandbox cục bộ hoặc CDN.

## Rollback
Bỏ khai báo `transition`/`transitions` ⇒ hành vi cũ. Hoặc `transitions.enabled=false`. Hoặc revert commit Phase 3.

## Gate 3
Kỹ thuật: PASS (tổng thời lượng bảo toàn, 149 test, R7). Thẩm mỹ: **chờ người xem**.
