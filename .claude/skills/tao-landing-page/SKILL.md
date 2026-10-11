---
name: tao-landing-page
description: >-
  Tạo mã nguồn Landing Page (React + Vite + TypeScript + Tailwind) từ brief chữ, ảnh mockup, Google Stitch hoặc Figma; nội dung tách khỏi mã (content.json), màu/font theo… Dùng khi: Người dùng cần làm trang đích / landing page web, chuyển thiết kế hoặc brief thành trang web chạy được. Không dùng khi: Cần ấn phẩm in (leaflet, brochure, poster PDF - dùng 'thiet-ke'), hoặc chỉ viết nội dung chữ (dùng 'viet-bai'), hoặc…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/tao-landing-page/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Tạo Landing Page (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/tao-landing-page/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/tao-landing-page/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/tao-landing-page/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/tao-landing-page/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Figma / Stitch / mockup + nội dung |
| Đầu ra | Mã nguồn React+Vite+Tailwind hoặc HTML/CSS, tích hợp Landing Hub |
| Thường nhận từ | `viet-bai` |
| Thường giao cho | `app-auditor` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
