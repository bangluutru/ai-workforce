---
name: app-auditor
description: >-
  Kiểm định toàn diện web app / landing page đang chạy: khám phá route, quét 4 khung nhìn (tràn ngang đo theo clientWidth, nội dung bị cắt, ảnh hỏng)… Dùng khi: Người dùng cần kiểm thử/audit giao diện web đang chạy (localhost hoặc URL), hoặc re-test sau khi sửa bug. Không dùng khi: Cần tự sửa mã nguồn ứng dụng (giao cho lập trình viên), hoặc kiểm định bản dịch tài liệu PDF (dùng 'dich-thuat').
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/app-auditor/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Kiểm Định Ứng Dụng (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/app-auditor/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/app-auditor/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/app-auditor/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/app-auditor/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 5-kiem-dinh (Kiểm thử thành phẩm) |
| Đầu vào | URL / localhost web app đang chạy |
| Đầu ra | Báo cáo lỗi P0-P4 có ảnh chụp bằng chứng |
| Thường nhận từ | `tao-landing-page` |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
