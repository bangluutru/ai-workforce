---
name: hand-drawn-animation
description: >-
  Tạo phim hoạt hình vẽ tay chất lượng cao bằng Canvas 2D với 5 phong cách nghệ thuật (ink, riso, screen, pencil, doodle), rotoscope, sand animation, và hiệu ứng pop-up… Dùng khi: Người dùng muốn sáng tạo hoạt hình nghệ thuật vẽ tay, phim hoạt họa 2D ngắn, hoặc hiệu ứng minh họa đồ họa động. Không dùng khi: Cần dựng video thực tế với stock footage người thật (dùng 'video-studio'), chỉ làm phụ đề video (dùng 'phu-de'), hoặc…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/hand-drawn-animation/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Tạo Hoạt Hình (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/hand-drawn-animation/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/hand-drawn-animation/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/hand-drawn-animation/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/hand-drawn-animation/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Ý tưởng / kịch bản hình ảnh |
| Đầu ra | Hoạt hình HTML Canvas, MP4 |
| Thường nhận từ | `viet-bai`, `chotto-newsroom` |
| Thường giao cho | `long-tieng`, `phu-de` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
