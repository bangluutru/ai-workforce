---
name: thiet-ke
description: >-
  Thiết kế ấn phẩm in ấn tiếp thị: Leaflet/Brochure gấp 2/gấp 3, Poster A3, Tờ rơi, Slide 16:9; xuất PDF in ấn có bleed 3mm, TrimBox/BleedBox, dấu cắt, font tiếng Việt… Dùng khi: Người dùng cần thiết kế ấn phẩm in (brochure, tờ rơi, poster, slide) hoặc file PDF gửi nhà in. Không dùng khi: Cần mã nguồn trang web / landing page (dùng 'tao-landing-page'), văn bản hành chính theo NĐ 30 hoặc slide .pptx chỉnh…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/thiet-ke/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Thiết Kế Đồ Họa (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/thiet-ke/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/thiet-ke/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/thiet-ke/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/thiet-ke/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Brief ấn phẩm + nội dung đã duyệt |
| Đầu ra | PDF in ấn (bleed, 300 ppi), ảnh preview |
| Thường nhận từ | `viet-bai`, `bao-cao-kt` |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
