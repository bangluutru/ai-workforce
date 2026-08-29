---
name: pdf-translate
description: DỊCH TÀI LIỆU PDF sang tiếng Việt, tiếng Anh, tiếng Nhật, tiếng Trung, tiếng Hàn và các ngôn ngữ khác chuẩn Unicode — giữ nguyên layout, công thức, bảng biểu và hình ảnh gốc.
trigger: Dịch PDF, translate PDF, dịch tài liệu, dịch file PDF sang tiếng Việt
exclusion: KHÔNG dùng cho file ảnh scan cần OCR.
push: Dùng cho MỌI yêu cầu dịch tài liệu PDF, kể cả khi user chỉ ném file PDF và nói 'dịch giùm'.
needs_file: true
file_filter: pdf
---

# LÝ LUẬN VÀ TƯ DUY (MINDSET)
- Skill này gọi engine pdf-translate đã cài sẵn tại global config (`~/.gemini/config/skills/pdf-translate/`).
- **Tự động nhận diện ngôn ngữ nguồn** (`--source-language auto` là mặc định).
- **Tùy chọn ngôn ngữ đích:** Tiếng Việt (`vi` - mặc định), Tiếng Anh (`en`), Tiếng Nhật (`ja`), Tiếng Trung (`zh-cn`/`zh-tw`), Tiếng Hàn (`ko`), Tiếng Pháp (`fr`), Tiếng Đức (`de`), Tiếng Tây Ban Nha (`es`), v.v. qua tham số `--target-language <mã>`.
- Luôn giữ nguyên file gốc — output ra file riêng kèm hậu tố ngôn ngữ (vd: `-vi.pdf`, `-ja.pdf`, `-en.pdf`).

# CHẾ ĐỘ DỊCH (DUAL-MODE)

## Mode 1: Google Translate (MẶC ĐỊNH — Khuyến nghị)
- **Engine**: `google` (mặc định, không cần chỉ định)
- **Cách hoạt động**: Dịch real-time qua Google Translate Web endpoint (`translate.google.com/m`) — web scraping, **hoàn toàn MIỄN PHÍ**, không cần API key.
- **Tốc độ**: ~1 trang/giây (78 trang ≈ 43 giây)
- **Chất lượng layout**: ★★★★★ — Segment được dịch đúng lúc PDF engine tách text, 100% segment match, không bị lỗi fragment.
- **Cơ chế chống nghẽn**: Exponential Backoff Retry (lên đến 8 lần, backoff max 60s).
- **Khi nào dùng**: Mọi trường hợp thông thường. Ưu tiên mode này.

## Mode 2: Antigravity Native — Handoff Coordinator (EXPERIMENTAL ⚠️)
- **Engine**: `handoff`
- **Cách hoạt động**: Tách tất cả segment từ PDF → Antigravity agent dịch theo batch → Ghép lại thành PDF.
- **Tốc độ**: Chậm hơn đáng kể (phải chạy 2 pass qua PDF engine + batch management).
- **Chất lượng layout**: ★★★☆☆ — CÓ VẤN ĐỀ: Segment extraction pass và rendering pass tách text ở ranh giới khác nhau → dictionary lookup miss → text bị giữ nguyên tiếng gốc hoặc hiển thị thành fragments vô nghĩa. ĐẶC BIỆT nặng ở các trang phụ lục/bảng biểu phức tạp.
- **Khi nào dùng**: CHỈ khi Google Translate bị chặn hoặc cần kiểm soát chất lượng dịch từng segment thủ công.

> ⚠️ **CẢNH BÁO**: Handoff Mode có lỗi kiến trúc cốt lõi với segment boundary mismatch. KHÔNG khuyến nghị dùng cho tài liệu có bảng biểu hoặc phụ lục phức tạp.

# CÁCH SỬ DỤNG

## 1. Google Translate Mode (Mặc định — Khuyến nghị)
```bash
"<skill-root>/.venv/bin/python" "<skill-root>/scripts/translate_pdf.py" \
  "<input.pdf>" --output-dir "<output-dir>" --target-language <lang>
```
**Ví dụ:**
```bash
"~/.gemini/config/skills/pdf-translate/.venv/bin/python" \
  "~/.gemini/config/skills/pdf-translate/scripts/translate_pdf.py" \
  "/path/to/document.pdf" --output-dir "/path/to/output" --target-language ja
```

## 2. Handoff Coordinator Mode (Experimental ⚠️)
```bash
# Bước 1: Khởi tạo điều phối và tách batch tự động
"<skill-root>/.venv/bin/python" "<skill-root>/scripts/handoff_coordinator.py" \
  init "<input.pdf>" "<work_dir>" <target_lang> <batch_size>

# Bước 2: Antigravity điều phối dịch lần lượt các batch pending trong work_dir

# Bước 3: Ghép nối và biên dịch thành file PDF hoàn chỉnh
"<skill-root>/.venv/bin/python" "<skill-root>/scripts/handoff_coordinator.py" \
  rebuild "<input.pdf>" "<work_dir>" "<output_dir>" <target_lang>
```

# TÀI NGUYÊN (RESOURCES)
- Skill gốc: `~/.gemini/config/skills/pdf-translate/SKILL.md`
- Preservation rules: `~/.gemini/config/skills/pdf-translate/references/preservation-rules.md`
