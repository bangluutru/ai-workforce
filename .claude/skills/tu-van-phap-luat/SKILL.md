---
name: tu-van-phap-luat
description: >-
  Tra cứu, đối chiếu và tư vấn đường lối giải quyết vấn đề pháp lý Việt Nam theo chu trình PDCA Cascade; truy nguyên văn bản quy phạm pháp luật (Luật, Nghị định, Thông… Dùng khi: Người dùng cần tra cứu luật, tư vấn tranh chấp, khiếu nại, hợp đồng, thành lập doanh nghiệp hoặc xử lý tình huống pháp lý. Không dùng khi: Cần tính toán hoặc tư vấn thuế cụ thể: TNCN, TNDN, GTGT, hộ kinh doanh, hóa đơn (dùng 'tu-van-thue'), hoặc viết bài…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/tu-van-phap-luat/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Pháp Luật Việt Nam (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/tu-van-phap-luat/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/tu-van-phap-luat/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/tu-van-phap-luat/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/tu-van-phap-luat/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 2-chuyen-mon (Phân tích, tư vấn, tính toán) |
| Đầu vào | Tình huống pháp lý Việt Nam, văn bản luật |
| Đầu ra | Báo cáo / thư tư vấn có trích dẫn nguyên văn |
| Thường nhận từ | `boc-tach-pdf` |
| Thường giao cho | `xu-ly-van-phong`, `viet-bai` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
