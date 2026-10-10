# Phase 7 - Regression & Compatibility

Nhãn: OBSERVED = đã chạy lệnh và đọc kết quả.

## 1. Kết quả

| Kiểm tra | Kết quả | Nhãn |
|---|---|---|
| Toàn bộ `tests/` trên nhánh (cdb658e) | 437 passed, 2 skipped, **2 failed, 4 errors** (309s) | OBSERVED |
| Cùng 6 test lỗi trên baseline `9e4ccb4` (worktree từ tag) | **Cùng 2 failed + 4 errors** → lỗi có sẵn, không do nâng cấp | OBSERVED |
| Nguyên nhân 6 lỗi | Thiếu module `skill_quality.document_reconstruction_translator`, thiếu fixture `D04_complex_layout_ja.pdf` (thuộc mảng dịch tài liệu, không liên quan Creative Studio) | OBSERVED |
| `tests/creative` | 158 passed trước Phase 6 + 3 test mới Phase 6 pass | OBSERVED |
| `scripts/check_shared_reuse.py` | exit 0 | OBSERVED |
| `scripts/audit_skill.py video-studio` | 100/100, STRUCTURE_VALIDATED | OBSERVED |
| `compileall` creative + video-studio/scripts | OK ở 3 bản | OBSERVED |
| `video_pipeline.py --help` (Video Studio v1) | exit 0 ở 3 bản | OBSERVED |
| `node --check extension/extension.js` | OK | OBSERVED (chỉ kiểm cú pháp) |

## 2. Storyboard v2.0 cũ (không có `audio`, không có `transitions`)

Cùng một storyboard cũ, 2 cảnh x 3s, render ở 3 môi trường:

| Môi trường | Validator | Render | Thời lượng | Streams | Renderer |
|---|---|---|---|---|---|
| Nhánh, cây chính | (True, []) | success | 6.00s | video + audio | hyperframes x2 |
| Nhánh, **clone sạch** (không có sandbox HyperFrames) | (True, []) | success | 6.00s | video + audio | canvas x2 (fallback) |
| Baseline `9e4ccb4` | (True, []) | success | 6.00s | video + audio | canvas x2 |

Kết luận: tương thích ngược giữ nguyên (thời lượng, độ phân giải, có track audio im lặng như v2.0). Khác biệt duy nhất: nhánh mới thêm **một cảnh báo thông tin** khi storyboard không khai báo `audio` ("xuất track im lặng... thêm audio.mode"). Không đổi kết quả render. Baseline không có cảnh báo này.

## 3. Phát hiện R0 (có sẵn từ trước, không do 2.1)

Clone sạch dùng Canvas thay vì HyperFrames vì sandbox `_process/hyperframes_sandbox` bị gitignore và `scripts/auto-setup.sh` **không có bước cài HyperFrames** (grep rỗng). Baseline cũng vậy. Hệ quả: trên máy mới, `git pull` + auto-setup chỉ cho video Canvas chất lượng thấp hơn, không phải HyperFrames. Chưa sửa vì sửa setup script vượt phạm vi đã thống nhất; đề xuất xử lý riêng (ghi vào Phase 8, cần bạn quyết).

## 4. Chưa kiểm chứng

- Windows/Linux: NOT VERIFIED (chỉ chạy macOS).
- Extension/dashboard chạy thực tế trong IDE: NOT VERIFIED (chỉ kiểm cú pháp `extension.js`).
- 6 test lỗi có sẵn chưa được sửa (ngoài phạm vi).
- Chạy cùng lúc với tải nặng có thể khiến HyperFrames hết 120s và rơi về Canvas (đã gặp một lần ở Phase 2).

## 5. Gate 7

PASS: không phát hiện regression do nâng cấp (so sánh trực tiếp với baseline). Rủi ro mở: R0 gap HyperFrames (có sẵn), 6 test lỗi có sẵn.

Dọn dẹp: worktree baseline và clone tạm đã xóa; cây làm việc sạch.
