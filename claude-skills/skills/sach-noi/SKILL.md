---
name: sach-noi
description: >-
  Sản xuất sách nói chất lượng cao (.m4b có mục lục chương và thư mục MP3 ID3 tags) từ file EPUB, Word (DOCX), PDF, Markdown hoặc tóm tắt từ 'doc-sau'. Dùng khi: Người dùng muốn chuyển sách, ebook, tài liệu, giáo trình, bài viết hoặc báo cáo tóm tắt thành sách nói để nghe trên điện thoại… Không dùng khi: Chỉ cần bóc tách OCR tài liệu scan đơn thuần (dùng 'boc-tach-pdf'), phân tích phản biện triết học chuyên sâu (dùng…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/sach-noi/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Sách Nói AI (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/sach-noi/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/sach-noi/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/sach-noi/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/sach-noi/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | EPUB, DOCX, PDF chữ, MD, hoặc Audiobook Brief từ doc-sau |
| Đầu ra | File .m4b có mục lục chương + thư mục MP3 + kịch bản đọc DOCX |
| Thường nhận từ | `doc-sau`, `boc-tach-pdf`, `ejv-translate` |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
