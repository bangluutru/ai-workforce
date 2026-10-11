---
name: phu-de
description: >-
  Tạo, bóc tách và biên tập phụ đề video (SRT, ASS, hardsub MP4) với forced alignment từng từ, phân đoạn ngữ nghĩa CPL/CPS, dịch thuật phụ đề song ngữ và phòng dựng… Dùng khi: Người dùng cần tạo phụ đề, làm sub song ngữ, dịch phụ đề, hoặc dập phụ đề (hardsub) vào video có sẵn. Không dùng khi: Cần sản xuất video tổng thể từ kịch bản/stock media (dùng 'video-studio'), chỉ cần lồng tiếng/thuyết minh audio track…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/phu-de/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Tạo Phụ Đề (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/phu-de/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/phu-de/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/phu-de/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/phu-de/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Video / audio có sẵn |
| Đầu ra | SRT, ASS, MP4 hardsub, phụ đề song ngữ |
| Thường nhận từ | `long-tieng`, `video-studio`, `hand-drawn-animation` |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
