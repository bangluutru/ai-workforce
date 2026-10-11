---
name: ejv-translate
description: >-
  Dịch thuật tài liệu chính xác 3 ngôn ngữ (Tiếng Việt, English, 日本語) với cơ chế phân đoạn chống tràn token (Zero-Loss Chunking) cho tài liệu dài, chuẩn hóa thuật ngữ… Dùng khi: Người dùng cần dịch tài liệu văn bản dài (Word, PDF, Text) giữa 3 ngôn ngữ Việt - Anh - Nhật, cần xuất bản bản dịch song ngữ… Không dùng khi: Cần dịch PDF phức tạp yêu cầu giữ nguyên bố cục hình học 1:1, ảnh, con dấu pháp nhân hoặc tái dựng trang PDF (dùng…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/ejv-translate/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Dịch Thuật EJV (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/ejv-translate/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/ejv-translate/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/ejv-translate/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/ejv-translate/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | DOCX, TXT, MD, PDF chữ đơn giản |
| Đầu ra | DOCX song ngữ / tam ngữ Việt-Anh-Nhật, PDF in |
| Thường nhận từ | `boc-tach-pdf` |
| Thường giao cho | `xu-ly-van-phong`, `sach-noi` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
