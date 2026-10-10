# Phase 6 - Three End-to-End Pilots

Nhãn: OBSERVED (đã đo/xem trực tiếp) · NOT REVIEWED (không thể xem/nghe) · NOT VERIFIED.

## 1. Kết quả

| Pilot | Thông số | Render | Visual QA | Audio (OBSERVED) | Creative review |
|---|---|---|---|---|---|
| A ChottoDay | 1:1 1080x1080, 30s, vi, 4 cảnh | HyperFrames cả 4 cảnh, 0 fallback | PASS 100 | có audio, mean -23.7 dB, peak -1.5 dB | PARTIAL, coverage 35% |
| B Genki Fami (Balancera) | 16:9 1920x1080, 30s, ja, 4 cảnh | HyperFrames cả 4 cảnh | **WARN 92** (mostly_empty_composition) | có audio, mean -23.0 dB, peak -3.1 dB | PARTIAL, coverage 35% |
| C KPI infographic | 9:16 1080x1920, 20s, vi, 3 cảnh | HyperFrames cả 3 cảnh | PASS 100 | có audio, mean -22.7 dB, peak -3.0 dB | PARTIAL, coverage 35% |

Thời lượng file đúng 30.0 / 30.0 / 20.0s (ffprobe). Không BGM theo yêu cầu (mode `narration`). Không có điểm tổng /100 cho bất kỳ pilot nào: motion, brand, pacing, sync là NOT REVIEWED.

Evidence: `~/Downloads/AIWF_Output/creative_2_1_pilots/` (`pilot_{A,B,C}.mp4`, `*_qa/`, `*_review/`). MP4 không nằm trong git.

Asset: logo Genki Fami lấy từ thư mục người dùng chỉ định (`[GF]_Color_Logo_VN1.png`), thu nhỏ còn 1400px và nhúng data URI, không copy vào repo. ChottoDay không có logo nên dùng chữ "C" (placeholder, ghi rõ). Nội dung B chỉ là giá trị thương hiệu chung, **không có công bố y tế/công dụng** (R5); là bản nháp cần chủ sở hữu duyệt. Số liệu pilot C là dữ liệu mô phỏng, gắn nhãn "DỮ LIỆU MÔ PHỎNG (DEMO)" ở các cảnh số liệu.

## 2. Lỗi thật phát hiện nhờ pilot (và xử lý)

| ID | Mô tả | Xử lý |
|---|---|---|
| P1 (high) | Presets 01, 06, 07, 10 căn giữa bằng `body`, nhưng registry bọc nội dung trong `hf-root` dạng block nên nội dung dồn lên góc trên-trái, logo bị cắt mép trên. Có thể chính là nguyên nhân "bố cục dồn nửa trên" (C3/Phase 4) | `registry.py`: `hf-root` thêm `display:flex` + căn giữa. Kiểm chứng bằng khung trước/sau và render lại cả 3 pilot. **Resolved** |
| P2 (high) | Tiêu đề preset 01 dùng gradient trắng cứng, mất chữ trên nền sáng (Genki Fami) | `01_fade_in.html` dùng `--text-color`. **Resolved** |
| P3 (medium) | Prop rỗng rơi về chữ mặc định của preset (`aiworkforce.vn`, "Creative Studio 2.0" lộ ra video) | **Open**: pilot né bằng giá trị tường minh; cần sửa preset hoặc validator cảnh báo |
| Tính năng | Preset 06 chưa hỗ trợ logo ảnh | Thêm prop tùy chọn `logo_url`, `hide_brand_name` (cộng thêm, mặc định không đổi) |

Lỗi mở khác: B1 tagline lặp trong logo (low), C5 nhãn DEMO nhỏ trên 9:16 (low), C2 chữ phụ nhỏ (low), C4 fade chồng chữ (khuyến nghị dùng slide/wipe; pilot dùng `slide_left`).

## 3. Cảnh báo giữ nguyên

- B: Visual QA WARN 92 do thiết kế tối giản nền trắng bị heuristic coi là "đa số khung đơn điệu". Đây là lựa chọn thẩm mỹ chủ ý, nhưng WARN vẫn được ghi nhận.
- Kiểm tra bằng khung tĩnh. NOT REVIEWED: chuyển động, độ tự nhiên giọng, tiếng Nhật (phát âm Kokoro), đồng bộ hình-tiếng, nhịp.
- Hiển thị tiếng Nhật chỉ xác nhận ở khung tĩnh (chữ đúng, không tofu).
- Giọng tiếng Nhật chưa nghe; `mixed_english` giữ `off`.

## 4. Gate 6

Process PASS: 3 MP4 thật, có audio đo được, evidence pack, lỗi thật được báo và sửa tận gốc. Creative: **PARTIAL**, chưa có điểm /100. Cần người xem/nghe để chấm 4 tiêu chí còn lại.

Rollback: revert commit Phase 6 (3 file preset/registry + test + doc).
