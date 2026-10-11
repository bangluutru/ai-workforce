---
name: viet-bai
description: >-
  Sáng tạo nội dung và viết bài tiếp thị đa nền tảng (Blog SEO, Website/Landing page, Facebook, Bài PR Báo chí) theo nguyên tắc Zero-Hallucination, tuân thủ pháp luật… Dùng khi: Người dùng cần viết bài blog SEO, bài đăng mạng xã hội, nội dung trang web/landing page, hoặc bài PR truyền thông. Không dùng khi: Cần dịch thuật văn bản đa ngôn ngữ (dùng 'ejv-translate'), biên tập tin tức thời sự Nhật Bản chuyên biệt (dùng…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/viet-bai/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Viết Bài Đa Kênh (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/viet-bai/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/viet-bai/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/viet-bai/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/viet-bai/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 3-noi-dung (Viết và biên tập nội dung) |
| Đầu vào | Brief tiếp thị, hoặc fact_pack.md / báo cáo từ skill khác |
| Đầu ra | Bài .md (+ .docx) theo kênh blog/web/facebook/pr + file _nguon.md |
| Thường nhận từ | `chotto-newsroom`, `doc-sau`, `tu-van-phap-luat` |
| Thường giao cho | `video-studio`, `thiet-ke`, `tao-landing-page`, `hand-drawn-animation` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
