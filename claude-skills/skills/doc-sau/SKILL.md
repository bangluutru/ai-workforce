---
name: doc-sau
description: >-
  Tóm tắt sách toàn diện và phân tích phản biện chuyên sâu (Đường ray kép: Executive Brief, tóm tắt hành trình từng chương kèm case study, kết hợp SCQA, 5W2H, phản biện… Dùng khi: Người dùng muốn tóm tắt sách, nắm bắt nhanh nội dung các chương, đọc hiểu sâu, mổ xẻ cấu trúc bài viết, phát hiện lỗi logic/ngụy… Không dùng khi: Chỉ cần bóc tách OCR tài liệu scan (dùng 'boc-tach-pdf'), dịch văn bản đơn thuần (dùng 'ejv-translate' hoặc…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/doc-sau/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Đọc Sâu (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/doc-sau/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/doc-sau/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/doc-sau/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/doc-sau/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 2-chuyen-mon (Phân tích, tư vấn, tính toán) |
| Đầu vào | Sách, bài viết, báo cáo (đã đọc được chữ) |
| Đầu ra | Báo cáo đọc sâu (Executive Summary, phản biện, kế hoạch 24h), Audiobook Brief |
| Thường nhận từ | `boc-tach-pdf` |
| Thường giao cho | `sach-noi`, `viet-bai`, `xu-ly-van-phong` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
