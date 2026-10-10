# Phase 4 — Creative Quality Review (Creative Studio 2.1)

Branch `feature/creative-studio-2.1` · Không xây lại Visual QA 2.0; chỉ thêm lớp Creative QA bên cạnh.

## Scope
Tách hai lớp: **Technical QA** (tự động, đã có) và **Creative QA** (rubric nội bộ 6 tiêu chí, không phải chuẩn ngành). Ngăn việc ghi PASS chỉ vì code chạy.

## Changes
- `creative/qa/creative_review.py` (mới, stdlib only) + CLI:
  - Rubric: Visual hierarchy 20 · Motion quality 20 · Brand consistency 15 · Typography & readability 15 · Storytelling & pacing 15 · Audio-visual sync 15.
  - Mặc định mọi tiêu chí **NOT REVIEWED**; không có reviewer thì không được chấm.
  - Điểm bắt buộc có `evidence` + `basis` (stills/video/audio/...); thiếu thì ném `ReviewError`.
  - Reviewer `same_context_agent` ⇒ `independent=false`, kèm câu tuyên bố không độc lập, điểm kẹp ≤ 3/5.
  - Tổng /100 chỉ có khi phủ 100% tiêu chí; còn lại chỉ báo độ phủ và điểm trên phần đã đánh giá (gắn nhãn "KHÔNG phải tổng điểm").
  - Technical FAIL ⇒ `BLOCKED_BY_TECHNICAL_FAIL`, không có tổng điểm.
  - `auto_signals` (khung đầu trống, khung phẳng, LUFS...) chỉ là tín hiệu, không quy đổi điểm.
  - `write_evidence_pack`: review JSON/MD, bản sao contact sheet + technical report, renderer/audio metadata, manifest (sha256 MP4, không sao chép MP4); **từ chối ghi vào trong repo** (R1).
- Đăng ký `creative.review` trong `engines.json`/`ENGINES.md`.
- Sửa lỗi tìm được qua review (C1): 11 dòng màu chữ phụ trong 9 preset đổi từ `rgba(255,255,255,a)` cứng sang `color-mix(in srgb, var(--text-color, #FFFFFF) a%, transparent)`. Preset nền tối (mặc định trắng) giữ nguyên diện mạo; brand nền sáng giờ đọc được.

## Quy trình review (7.3 — không tuyên bố độc lập)
Pass 1 (ghi nhận, không sửa) → Fix pass → Pass 2 (review lại). Reviewer: cùng agent, cùng model, cùng ngữ cảnh ⇒ **không độc lập**.

| Issue | Mức | Pass 1 → Pass 2 |
|---|---|---|
| C1 phụ đề/chữ phụ trắng trên nền sáng, không đọc được | high | **resolved** (xem khung trước/sau cùng mốc t=3.2s, 7.0s, 10.5s) |
| C2 chữ phụ/mô tả nhỏ ở 1280x720 | medium→low | open (hiệu chỉnh nhận định pass 1: tag dùng màu accent, không nhạt) |
| C3 khung đầu trống, Visual QA vẫn PASS 100 | medium | open, chưa sửa |
| C4 fade giữa hai cảnh nặng chữ chồng tiêu đề | medium | open, mới có khuyến nghị dùng slide/wipe |
| C5 brief thử dùng chữ mẫu mặc định | low | không phải lỗi renderer |

## Kết quả scorecard (video Phase 3 `after.mp4` → `after_pass2.mp4`)
- Technical QA: **PASS** (100) cả hai. Creative QA: **PARTIAL**, độ phủ **35%**, **không có tổng /100**.
- Pass 1: Visual hierarchy 3/5, Typography 2/5. Pass 2: Visual hierarchy 3/5, Typography 3/5.
- NOT REVIEWED (65%): Motion quality, Brand consistency, Storytelling & pacing, Audio-visual sync (không xem được chuyển động liên tục, không nghe audio, không có brand guide).
- Quan sát đáng chú ý: Visual QA cho 100/100 ngay cả khi phụ đề vô hình và khung đầu trống ⇒ Technical PASS không đồng nghĩa chất lượng sáng tạo.

## Evidence (ngoài Git)
`~/Downloads/AIWF_Output/creative_2_1_phase4/pass1_review/` và `pass2_review/` (creative_review.json/.md, contact sheet, technical report, evidence_manifest.json). MP4 ở `creative_2_1_phase3/`.
Chưa tạo `renderer_meta`/`audio_qa` trong gói này (API đã hỗ trợ; sẽ nối ở Phase 6 pilot).

## Tests
`tests/creative/test_creative_review.py`: 9 test (mặc định NOT REVIEWED, thiếu bằng chứng, reviewer không độc lập + kẹp điểm, PARTIAL/COMPLETE, Technical FAIL không bị che, issue/markdown, tín hiệu khung đầu trống, evidence pack từ chối ghi vào repo, CLI).

## Remaining risks / NOT VERIFIED
- Chưa có reviewer độc lập thật; cần người xem để chấm Motion, Brand, Pacing, Sync và có tổng /100.
- `color-mix()` hoạt động trong HyperFrames/Chromium (đã thấy qua render); **chưa kiểm tra** đường Canvas fallback (không dùng HTML preset).
- Màu chữ phụ của preset nền tối khi `text_color` tùy chỉnh sẽ đổi theo màu đó (chủ đích).
- C2, C3, C4 còn mở.

## Rollback
Revert commit Phase 4; scorecard là module độc lập, không nằm trong đường render.

## Gate 4
Có Technical QA + Creative QA thật (2 pass, issue có bằng chứng, 1 lỗi sửa và xác nhận lại): **PASS về quy trình/kỹ thuật**. Điểm sáng tạo tổng: **chưa có** (35% độ phủ), cần người duyệt.
