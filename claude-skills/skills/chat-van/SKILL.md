---
name: chat-van
description: >-
  Chất vấn người dùng có hệ thống về một kế hoạch, thiết kế, tính năng hoặc ý tưởng kinh doanh TRƯỚC khi bắt tay làm: dựng cây quyết định, hỏi theo từng vòng, mỗi câu kèm… Dùng khi: Người dùng nói "chất vấn tôi", "grill me", "hỏi kỹ trước khi làm", "soi kế hoạch này", hoặc gọi thẳng skill chat-van trước một… Không dùng khi: Yêu cầu đã rõ và chỉ cần làm (gọi thẳng skill nghiệp vụ); đang giữa một quy trình tự chạy của skill khác (không chen…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/chat-van/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Chất Vấn Kế Hoạch (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/chat-van/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/chat-van/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/chat-van/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/chat-van/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 0-lam-ro (Làm rõ kế hoạch trước khi làm) |
| Đầu vào | Kế hoạch, ý tưởng, đề xuất tính năng hoặc thiết kế chưa chốt |
| Đầu ra | Biên bản quyết định .md: quyết định đã chốt có nhãn nhận thức, sự kiện đã tra, giả định mở, backlog, rủi ro |
| Thường nhận từ | — |
| Thường giao cho | `dieu-phoi`, `tao-landing-page`, `viet-bai`, `app-auditor` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
