# Creative Studio 2.1 — Release Report (Phase 8)

Nhãn bằng chứng: **OBSERVED** (đã chạy/đọc trực tiếp), **TESTED** (có test tự động), **DERIVED** (suy ra), **NOT VERIFIED** (chưa kiểm chứng).

## 1. Định danh

| Mục | Giá trị |
|---|---|
| Baseline | `9e4ccb4` (tag chú thích `pre-creative-studio-2.1`) |
| Nhánh | `feature/creative-studio-2.1` |
| Đích merge | `main` (`--no-ff`, một merge commit) |
| Hợp nhất kèm | `origin/main` `e844ac5` (chỉ đồng bộ `.certified.json`) |
| Rollback | `git revert -m 1 <merge_sha>`; hoặc đặt lại về tag `pre-creative-studio-2.1` |

## 2. Thay đổi theo phase

| Phase | Nội dung | Commit |
|---|---|---|
| 0 | Baseline, xác minh rollback | `5bd808e` |
| 1 | Audit hiện trạng, capability matrix | `3f72a11` |
| 2 | Audio Contract: TTS offline + BGM ducking + audio QA; đọc chữ Anh trong lời Việt (mặc định `off`) | `e2cc85f` `9350b4b` `dc52b7b` `68418c0` |
| 3 | Chuyển cảnh giữ mốc âm thanh; chống thời lượng âm | `9aa0e49` |
| 4 | Creative Scorecard (NOT REVIEWED mặc định) | `19c3e75` |
| 5 | Nghiên cứu Remotion (không tích hợp) | `bb770b0` |
| 6 | Pilot A/B/C; sửa hf-root, preset 01, preset 06 (`logo_url`) | `cdb658e` |
| 7 | Regression + tương thích | `84a4e05` |
| — | Sửa 6 test lỗi có sẵn | `51e88f1` |
| — | Verifier dịch thuật: bỏ qua glyph điện tích ion + test_21 | `c2e32a8` |
| 8 | Cài HyperFrames từ manifest git-tracked (R0) | `47213b4` |
| 8 | Tài liệu, cờ tính năng, hạn chế đã biết | `719bbe1` |

## 3. Tái sử dụng (R7)

Gọi lại `media.dub_engine` (TTS VieNeu/Kokoro, mix, ducking, loudnorm), `ffmpeg_tools`, `creative.qa.run_visual_qa`, `render_router`. Engine mới đăng ký ở `engines.json` + `ENGINES.md`: `audio_track`, `transitions`, `creative_review`, `mixed_lang`. OBSERVED: `check_shared_reuse.py` thoát 0.

## 4. Bảo toàn Creative Studio 2.0

10 preset, Storyboard v2.0, HyperFrames chính + Canvas fallback, Visual QA 2.0, DOM Validator, Legacy v1 vẫn nguyên. TESTED (Phase 7): storyboard v2.0 cũ (không `audio`, không `transitions`) render 6,00 s giống nhau trên nhánh, clone sạch và baseline.

## 5. Kiểm chứng

| Hạng mục | Kết quả | Nhãn |
|---|---|---|
| `tests/` đầy đủ | 446 chạy, 2 skipped, 0 failed (mục 8) | TESTED |
| `check_shared_reuse.py` | exit 0 | OBSERVED |
| `audit_skill.py video-studio` | đạt chuẩn cấu trúc | OBSERVED |
| Clone sạch: `setup_hyperframes.sh` | cài ~7 s; render 8,0 s qua HyperFrames của clone | TESTED |
| Pilot A (ChottoDay 1:1, vi) | Visual QA PASS 100 | OBSERVED |
| Pilot B (Genki Fami 16:9, ja) | Visual QA WARN 92 (`mostly_empty_composition`, thiết kế tối giản) | OBSERVED |
| Pilot C (KPI 9:16, dữ liệu DEMO) | Visual QA PASS 100 | OBSERVED |
| test_20 (dịch thuật A/B/C) | chạy đủ 3 artifact, PASS | TESTED (chỉ trên máy có artifact `_process/`) |

## 6. Giới hạn (không ẩn)

* **Chất lượng sáng tạo NOT VERIFIED.** Scorecard pilot chỉ phủ 35% (PARTIAL), không có tổng /100. Chuyển động, thương hiệu, nhịp, đồng bộ và độ tự nhiên của giọng (đặc biệt tiếng Nhật ở pilot B) cần người xem và nghe. Không có tuyên bố "chất lượng thương mại".
* **Remotion: INSUFFICIENT EVIDENCE.** Không tích hợp. Điều kiện mở lại: có nhu cầu cụ thể HyperFrames không đáp ứng + prototype cô lập có benchmark.
* **P3 (trung bình):** prop rỗng rơi về chữ mặc định của preset. Giải pháp tạm: luôn truyền đủ prop. Chưa sửa mã preset.
* **Cờ `audio_driven_timeline`:** không mã nào đọc; đã ghi chú trong reference, giữ nguyên để không đổi hành vi.
* **Cần npm + mạng ở lần setup đầu** để có HyperFrames; thiếu thì Canvas fallback (chất lượng thấp hơn). HyperFrames có thể quá 120 s khi máy tải nặng và rơi về Canvas.
* **Mã pilot/dịch thuật tạm** nằm trong `_process/` (gitignored), không đồng bộ qua git.
* Pilot B/Genki Fami và ChottoDay là bản nháp cần chủ sở hữu duyệt nội dung (R5); ChottoDay chỉ có logo chữ "C" tạm.

## 7. Rollback

1. Nhanh: `git revert -m 1 <merge_sha>` rồi push (không force-push).
2. Về mốc: `git checkout pre-creative-studio-2.1` (tag giữ nguyên, không xóa).
3. Tắt riêng tính năng: bỏ khối `audio`/`transitions` khỏi storyboard (không khai báo = hành vi v2.0); `enabled: false` trong `config/creative_studio_v2.json` để về Legacy v1.

## 8. Số liệu chạy cuối

`python3 -m pytest tests` trên nhánh tại `719bbe1`: 446 test chạy, 2 skipped, 0 failed, 0 error (TESTED; tiến trình đạt 100% không có F/E). Baseline có 6 lỗi có sẵn, đã sửa ở `51e88f1`. Số skip giảm 3 → 2 vì test_20 nay chạy đủ A/B/C trên máy này.
