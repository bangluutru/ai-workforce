---
name: tu-van-phap-luat-nhat-ban
description: >-
  Nghiên cứu và tư vấn sơ bộ pháp luật Nhật Bản theo tình huống, với căn cứ tiếng Nhật và hiệu lực theo thời điểm; chuyên sâu xuất nhập khẩu, tra mã HS từ sản phẩm/thành… Dùng khi: Người dùng cần tư vấn pháp lý Nhật Bản (hợp đồng, doanh nghiệp, lao động, cư trú, thuế, tranh chấp, SHTT) hoặc sản phẩm có yếu… Không dùng khi: Vấn đề pháp lý thuần túy tại Việt Nam không có yếu tố Nhật Bản (dùng 'tu-van-phap-luat'), dịch thuật văn bản đơn thuần…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/tu-van-phap-luat-nhat-ban/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Tư Vấn Pháp Luật Nhật Bản (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/tu-van-phap-luat-nhat-ban/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/tu-van-phap-luat-nhat-ban/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/tu-van-phap-luat-nhat-ban/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/tu-van-phap-luat-nhat-ban/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 2-chuyen-mon (Phân tích, tư vấn, tính toán) |
| Đầu vào | Tình huống có yếu tố Nhật Bản, hồ sơ hàng hóa XNK |
| Đầu ra | Báo cáo pháp lý Nhật Bản, bảng thuế/HS ước tính |
| Thường nhận từ | `boc-tach-pdf` |
| Thường giao cho | `chotto-newsroom`, `viet-bai`, `xu-ly-van-phong` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
