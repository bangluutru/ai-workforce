---
name: pdf-translate
description: DỊCH TÀI LIỆU PDF sang tiếng Việt (hoặc ngôn ngữ Latin khác) — giữ nguyên layout, công thức, bảng biểu và hình ảnh gốc.
trigger: Dịch PDF, translate PDF, dịch tài liệu, dịch file PDF sang tiếng Việt
exclusion: KHÔNG dùng cho file ảnh scan cần OCR, hoặc dịch sang ngôn ngữ CJK/RTL.
push: Dùng cho MỌI yêu cầu dịch tài liệu PDF, kể cả khi user chỉ ném file PDF và nói 'dịch giùm'.
---

# LÝ LUẬN VÀ TƯ DUY (MINDSET)
- Skill này gọi engine pdf-translate đã cài sẵn tại global config (`~/.gemini/config/skills/pdf-translate/`).
- Có 2 chế độ: **Google** (mặc định, nhanh, batch) và **Handoff** (agent dịch, chất lượng cao hơn).
- Luôn giữ nguyên file gốc — output ra thư mục riêng.
- Nếu tài liệu là ảnh scan (image-only) → báo cần OCR, KHÔNG giả vờ đã dịch.
- Kiểm tra kết quả: số trang đầu ra = số trang đầu vào, không có trang trắng hay mất chữ.

# CÁCH SỬ DỤNG
1. Đọc skill chi tiết tại: `~/.gemini/config/skills/pdf-translate/SKILL.md`
2. Chạy lệnh dịch (Google mode):
   ```bash
   "<skill-root>/.venv/bin/python" "<skill-root>/scripts/translate_pdf.py" "<input.pdf>" --output-dir "<output-dir>"
   ```
3. Với tài liệu chuyên ngành hoặc cần chất lượng cao → dùng Handoff mode (xem SKILL.md gốc).

# TÀI NGUYÊN (RESOURCES)
- Skill gốc: `~/.gemini/config/skills/pdf-translate/SKILL.md`
- Preservation rules: `~/.gemini/config/skills/pdf-translate/references/preservation-rules.md`
