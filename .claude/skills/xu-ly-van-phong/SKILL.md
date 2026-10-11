---
name: xu-ly-van-phong
description: >-
  Soạn thảo, chỉnh sửa, chuyển đổi và tái tạo văn bản hành chính theo chuẩn thể thức Nghị định 30/2020/NĐ-CP hoặc chuẩn thẩm mỹ doanh nghiệp (Word .docx, PowerPoint… Dùng khi: Người dùng cần soạn thảo công văn, quyết định, hợp đồng, tờ trình, quy chế hành chính, hoặc định dạng chuyển đổi tài liệu văn… Không dùng khi: Cần lập mô hình báo cáo tài chính - kế toán chuyên sâu có công thức động Live Formulas (dùng 'bao-cao-kt'), thiết kế…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/xu-ly-van-phong/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Xử Lý Văn Phòng (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/xu-ly-van-phong/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/xu-ly-van-phong/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/xu-ly-van-phong/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/xu-ly-van-phong/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 4-san-xuat (Dựng thành phẩm (tài liệu, ấn phẩm, video, âm thanh, web)) |
| Đầu vào | Yêu cầu hành chính, nội dung từ skill khác, biểu mẫu |
| Đầu ra | DOCX / XLSX / PPTX / PDF chuẩn NĐ 30/2020 |
| Thường nhận từ | `tu-van-phap-luat`, `tu-van-thue`, `doc-sau`, `bao-cao-kt`, `ejv-translate` |
| Thường giao cho | — |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
