---
name: chotto-newsroom
description: >-
  Tòa soạn tin tức hàng ngày tự động cho chottoday.com — phát hiện thay đổi chính sách, pháp luật, thủ tục hành chính, đời sống tại Nhật Bản ảnh hưởng đến cộng đồng người… Dùng khi: Người dùng cần biên tập, tổng hợp hoặc thẩm định tin tức chính sách, đời sống Nhật Bản cho cộng đồng người Việt. Không dùng khi: Viết bài tiếp thị bán hàng đa kênh chung (dùng 'viet-bai'), tư vấn pháp luật Việt Nam (dùng 'tu-van-phap-luat'), hoặc…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/chotto-newsroom/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Biên Tập Tin Chotto (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/chotto-newsroom/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/chotto-newsroom/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/chotto-newsroom/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/chotto-newsroom/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 3-noi-dung (Viết và biên tập nội dung) |
| Đầu vào | Chủ đề / link, hoặc tự săn tin nguồn .go.jp |
| Đầu ra | fact_pack.md có nguồn + bản tin chottoday.com + ảnh minh họa |
| Thường nhận từ | `tu-van-phap-luat-nhat-ban` |
| Thường giao cho | `viet-bai`, `video-studio`, `hand-drawn-animation` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
