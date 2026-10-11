---
name: tu-van-thue
description: >-
  Cổng tư vấn và tính toán thuế Việt Nam cho cá nhân, hộ kinh doanh và doanh nghiệp: thuế TNCN (quyết toán, Gross-Net, giảm trừ gia cảnh, eTax Mobile, bất động sản, BHXH… Dùng khi: Người dùng cần tính hoặc tư vấn thuế (TNCN, TNDN, GTGT, TTĐB, hộ kinh doanh), hóa đơn điện tử, tiền chậm nộp, hoàn thuế, kê… Không dùng khi: Lập báo cáo tài chính hoặc sổ kế toán (dùng 'bao-cao-kt'), tư vấn pháp lý tổng quát hoặc tranh chấp, hình sự thuế…
---
<!-- AUTO: sinh bởi claude-skills/sync_from_antigravity.py từ .agents/skills/tu-van-thue/SKILL.md. Sửa skill gốc hoặc claude-skills/skill-map.json rồi chạy lại script, đừng sửa tay file này. -->

# Tư Vấn Thuế (bản Claude)

Skill gốc (nguồn sự thật duy nhất): `.agents/skills/tu-van-thue/SKILL.md`.

## Cách chạy

1. Đọc TOÀN BỘ `.agents/skills/tu-van-thue/SKILL.md` bằng Read rồi làm đúng từng bước trong đó. Các file con skill nhắc tới (`standards/`, `references/`, `resources/`, `templates/`, `examples/`, `scripts/`) nằm trong `.agents/skills/tu-van-thue/`.
2. Quy ước đường dẫn: `<workspace>` = gốc repo (thư mục chứa `CLAUDE.md`); `<skill_dir>` = `.agents/skills/tu-van-thue/`; `<process_dir>` = `_process/<tên_việc>/` (đã gitignore); `<output_dir>` = nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/`.
3. Chuyển công cụ Antigravity sang Claude theo bảng trong `CLAUDE.md` (mục "Đổi công cụ"): `search_web` → WebSearch, `read_url_content` → WebFetch, `view_file` → Read (đọc được ảnh), `run_command` → Bash, "Agent Antigravity / Gemini" → chính Claude, "Multi-Agent" → subagent (Agent tool).
4. Giữ nguyên mọi cổng kiểm định, linter và quy tắc R0–R7 mà skill gốc yêu cầu. Chạy script bằng `.venv/bin/python` nếu skill gốc ghi vậy.

## Hợp đồng phối hợp

| Mục | Giá trị |
|---|---|
| Tầng | 2-chuyen-mon (Phân tích, tư vấn, tính toán) |
| Đầu vào | Thu nhập, doanh thu, hóa đơn, chứng từ thuế |
| Đầu ra | Bảng tính thuế XLSX công thức sống, báo cáo tư vấn thuế |
| Thường nhận từ | `bao-cao-kt`, `boc-tach-pdf` |
| Thường giao cho | `xu-ly-van-phong` |

Khi chạy trong một chuỗi nhiều skill (xem skill `dieu-phoi`): đọc đầu ra của bước trước trong thư mục việc làm nguồn sự thật, ghi thành phẩm của mình thành file mới trong cùng thư mục, cập nhật `handoff.json`, không ghi đè thành phẩm của skill khác.
