---
name: dich-thuat
description: >-
  Dịch tài liệu PDF (VI - EN - JA) với 2 chế độ trên cùng một engine: PRESERVE giữ nguyên bố cục 1:1 (số trang, ảnh, con dấu SMask trong suốt, khung hoa văn, biểu đồ đa… Dùng khi: Người dùng cần dịch file PDF có lớp chữ mà kết quả phải là PDF: giữ nguyên bố cục gốc (chứng chỉ, công văn có dấu, bằng khen… Không dùng khi: Dịch Word/Text/Markdown/EPUB hoặc cần bản song ngữ/tam ngữ DOCX (dùng 'ejv-translate'), PDF scan không có lớp chữ cần…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/dich-thuat/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Dịch Thuật (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/dich-thuat/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/dich-thuat/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/dich-thuat/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/dich-thuat/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | PDF có lớp chữ (PDF scan thì qua boc-tach-pdf trước) |
| Đầu ra | PDF dịch (preserve 1:1 hoặc reconstruct) + báo cáo kiểm định |
| Thường nhận từ | — |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
