---
name: long-tieng
description: >-
  Lồng tiếng và thuyết minh video tự động chuẩn phòng thu chất lượng cao, tích hợp TTS offline đa vùng miền và đa ngôn ngữ (Việt - Anh - Nhật), đồng bộ khẩu hình và… Dùng khi: Người dùng cần tạo bản thuyết minh âm thanh, lồng tiếng video từ file kịch bản hoặc file phụ đề có sẵn. Không dùng khi: Cần dựng toàn bộ video từ ý tưởng/kho stock (dùng 'video-studio'), chỉ cần tạo/dịch phụ đề chữ (dùng 'phu-de'), hoặc…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/long-tieng/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Lồng Tiếng Video (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/long-tieng/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/long-tieng/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/long-tieng/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/long-tieng/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Video có sẵn + kịch bản thuyết minh |
| Đầu ra | Video MP4 đã lồng tiếng, audio track |
| Thường nhận từ | `hand-drawn-animation`, `video-studio` |
| Thường giao cho | `phu-de` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
