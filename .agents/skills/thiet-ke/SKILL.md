---
name: thiet-ke
display-name: Thiết Kế Đồ Họa
description: >-
  Thiết kế ấn phẩm in ấn tiếp thị: Leaflet/Brochure gấp 2/gấp 3, Poster A3, Tờ rơi, Slide 16:9; xuất PDF in ấn có bleed 3mm, TrimBox/BleedBox, dấu cắt, font tiếng Việt nhúng sẵn và preflight tự động + soát ảnh xem trước.
  USE WHEN: Người dùng cần thiết kế ấn phẩm in (brochure, tờ rơi, poster, slide) hoặc file PDF gửi nhà in.
  DO NOT USE WHEN: Cần mã nguồn trang web / landing page (dùng 'tao-landing-page'), văn bản hành chính theo NĐ 30 hoặc slide .pptx chỉnh sửa được theo template (dùng 'xu-ly-van-phong'), hoặc deck số liệu tài chính (dùng 'bao-cao-kt').
trigger: Thiết kế đồ họa, làm leaflet, tạo tờ rơi, thiết kế brochure, thiết kế poster, thiết kế slide PDF trình chiếu
category: content
needs_file: false
file_filter: doc
---

# Thiết Kế Đồ Họa - Ấn phẩm in sẵn sàng gửi nhà in

<goal>
Tạo ấn phẩm in đẹp ở mức giám đốc thiết kế VÀ đúng kỹ thuật in: PDF có trang = khổ thành phẩm + 2 x bleed,
TrimBox/BleedBox chuẩn, dấu cắt, font tiếng Việt nhúng đủ dấu, ảnh >= 300 ppi, đã soát bằng mắt từng trang.
Phạm vi: chỉ ấn phẩm in / slide. Không làm web (chuyển 'tao-landing-page').
</goal>

> [!CAUTION]
> **ZERO EXTERNAL API.** Không gọi REST API ngoài, không yêu cầu API key. Toàn bộ thẩm mỹ, bố cục, nội dung là của Agent.
> Export chặn mọi tài nguyên http(s): ảnh, font phải là file cục bộ. Skill chạy liên tục (Autonomous Full-Run) tới khi preflight đạt và đã soát ảnh.

## 🔧 Môi trường & Path Resolution

| Placeholder | Giá trị |
|---|---|
| `<workspace>` | Thư mục gốc repo (chứa `GEMINI.md`) |
| `<PY>` | **`<workspace>/.venv/bin/python`** - BẮT BUỘC cho export/preflight (Playwright + PyMuPDF chỉ có trong `.venv`). Không dùng `python`/`python3` hệ thống. |
| `<process_dir>` | `_process/thiet_ke_<du_an>/` (đã gitignore) |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):** thành phẩm (`.pdf`, `.png`, `.html`) chỉ lưu vào `<output_dir>`; file làm việc ở `<process_dir>`. Không ghi vào thư mục gốc repo.
> Nếu `.venv` thiếu: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/python -m playwright install chromium`.

<constraints>
## ⛔ Luật cứng

1. **KHÔNG BỊA DỮ KIỆN KINH DOANH.** Tên, địa chỉ, điện thoại, email, giá, giờ mở cửa, giấy phép, số đăng ký, chứng nhận, số liệu, đánh giá khách hàng, năm thành lập, số khách hàng: chỉ lấy từ người dùng/tài liệu của họ. Thiếu -> ghi nguyên văn `[CẦN XÁC MINH: <trường>]` lên ấn phẩm và liệt kê khi bàn giao. Không thay bằng số "nghe hợp lý".
2. **Chỉ dùng template trong `templates/`** (khung bleed/nếp gấp đã đúng) và **chỉ sửa vùng `THIẾT KẾ - SỬA TỰ DO`**. Không sửa khối `KHUNG IN - KHÔNG SỬA`.
3. **Chỉ dùng font đóng gói** `Be Vietnam Pro` và `Spectral` (qua `fonts/fonts.css`). Không link Google Fonts / CDN. Không emoji (dùng SVG).
4. **Không bàn giao khi preflight FAIL** và **không bàn giao khi chưa mở xem từng ảnh xem trước**. Không có ngoại lệ "tiết kiệm token".
5. Không tuyên bố thông số chưa kiểm chứng (ví dụ "300 DPI", "CMYK", "có dấu cắt") - chỉ báo đúng số liệu preflight in ra.
</constraints>

<instructions>
## 📋 Quy trình (Intake -> Scaffold -> Thiết kế -> Export -> Preflight -> Soát ảnh -> Bàn giao)

### Bước 0 - Intake: dữ kiện và quy cách
1. Xác định loại ấn phẩm: `trifold` | `bifold` | `poster_a3` | `slides_16x9` (khác khổ: chép template gần nhất, đổi `@page`, `.sheet`, `print:trim`).
2. Gom dữ kiện từ tin nhắn/tệp người dùng vào `facts.md` (bước 1 tạo sẵn), cột "Nguồn" ghi rõ lấy từ đâu. Đọc `standards/print_production.md` và `resources/design_tokens.json` (chọn palette theo ngành).
   **Đọc tệp người dùng** (brief, catalogue, logo, bảng giá: PDF/DOCX/PPTX/XLSX/ảnh): không đọc thẳng tệp nhị phân. Từ gốc repo chạy `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<tên_việc> --json` rồi đọc `source.md` + `manifest.json` (`warnings`). Mã thoát: `0` dùng `source.md` · `3` có trang scan → đọc ảnh `ocr_pages/*.png` bằng thị giác (nháp OCR trong `source.md` CHƯA kiểm chứng) · `2` hỏi người dùng đúng điều trong `manifest.message` (mật khẩu/hỏng), không đoán · `4` thiếu phụ thuộc → cài theo `manifest.message` (`bash scripts/auto-setup.sh`). Cột "Nguồn" của `facts.md` ghi `<tên tệp>, trang N` / `Slide N`; ảnh trong `media/` chỉ dùng khi đạt >= 300 ppi ở kích thước đặt.
3. Chỉ hỏi người dùng khi thiếu thứ không thể để `[CẦN XÁC MINH]` (ví dụ: không biết sản phẩm là gì). Còn lại cứ làm, gắn cờ.

### Bước 1 - Khởi tạo từ template
```bash
python3 .agents/skills/thiet-ke/scripts/new_design.py --template trifold --out <process_dir>
```
Tạo `design.html`, `fonts/`, `images/`, `facts.md`. Mở `design.html` trên trình duyệt: đường đỏ = mép xén, xanh = nếp gấp (chỉ hiện trên màn hình).

### Bước 2 - Thiết kế
- Áp dụng chuẩn thẩm mỹ mục 2 của `standards/print_production.md` (1 điểm nhìn/bìa, thang chữ, 1 màu nhấn, lưới, không panel trống nửa trang).
- Thay mọi `[[...]]` bằng nội dung từ `facts.md`. Giữ `[CẦN XÁC MINH: ...]` cho mục chưa có.
- Ảnh đặt trong `<process_dir>/images/`, tham chiếu đường dẫn tương đối. Ảnh phải đạt >= 300 ppi ở kích thước đặt (100 mm cần >= 1181 px). Nếu có công cụ `generate_image` thì tạo ảnh đủ độ phân giải; nếu không có ảnh đạt chuẩn -> thiết kế bằng mảng màu/typography/SVG, KHÔNG phóng to ảnh nhỏ.

### Bước 3 - Xuất PDF in ấn
```bash
<PY> .agents/skills/thiet-ke/scripts/export_print_pdf.py --input <process_dir>/design.html \
     --output <output_dir>/<ten_an_pham>_print.pdf --marks
```
- Khổ thành phẩm/bleed đọc từ `<meta name="print:trim|print:bleed">` (ghi đè bằng `--trim 297x210 --bleed 3`). Slide: không dùng `--marks`.
- Script tự động quét lỗi tràn chữ (Overset Text Detection đúc kết từ DesignCraft). Thoát mã khác 0 nếu thiếu Playwright, sai kích thước hoặc phát hiện chữ tràn khung -> sửa nội dung/cỡ chữ rồi chạy lại (dùng `--allow-overset` nếu muốn xuất nháp xem xét).

### Bước 4 - Preflight kỹ thuật
```bash
<PY> .agents/skills/thiet-ke/scripts/preflight.py --pdf <output_dir>/<ten_an_pham>_print.pdf \
     --trim 297x210 --bleed 3 --render-dir <process_dir>/preview
```
Kiểm tra TrimBox/BleedBox, font nhúng + không font dự phòng (Times/Helvetica = vỡ dấu), glyph Type3/emoji, ảnh >= 300 ppi, placeholder còn sót, chữ ngoài vùng an toàn/bị cắt; render `page-NN_trimmed.png` và `page-NN_full.png`. Mã thoát 1 = FAIL -> quay lại Bước 2.

### Bước 5 - Soát ảnh xem trước (BẮT BUỘC, mỗi vòng)
1. Mở (view_file) **từng** `page-NN_trimmed.png` và `page-NN_full.png` trong `<process_dir>/preview/`.
2. Chấm theo checklist mục 3 `standards/print_production.md`; ghi kết quả vào `<process_dir>/review.md` (mỗi trang: đạt/lỗi + mô tả lỗi cụ thể).
3. Có lỗi -> sửa `design.html` -> lặp Bước 3-5 (tối đa 3 vòng; vẫn lỗi thì bàn giao kèm danh sách lỗi còn lại, không che giấu).
</instructions>

<quality_gate>
## ✅ Quality Gate (Checklist trước khi bàn giao)
1. `export_print_pdf.py` thoát 0 (0 lỗi tràn chữ Overset Text); MediaBox/TrimBox/BleedBox in ra đúng khổ + bleed.
2. `preflight.py` thoát 0 (không FAIL). Mọi WARN đã được xử lý hoặc nêu cho người dùng.
3. `review.md` có nhận xét cho TỪNG trang, lập từ việc đã mở ảnh xem trước (bằng chứng: đường dẫn PNG).
4. **Confidence Flagging:** mọi dữ kiện thiếu nguồn = `[CẦN XÁC MINH: ...]`; hệ màu RGB được ghi chú cho nhà in.
5. Không em dash `—`, không Oxford comma `, và`, không dấu hai chấm cuối tiêu đề trong nội dung ấn phẩm.
6. Thành phẩm nằm trong `<output_dir>`, không có file nào ghi vào repo ngoài `_process/`.
</quality_gate>

<delivery_protocol>
## 📦 Bàn giao (Clean Delivery)
Khung chat chỉ gồm: đường dẫn PDF + thư mục ảnh xem trước; thông số thực đo (trang, TrimBox, BleedBox, font, ppi thấp nhất) lấy từ output preflight; bảng màu & font đã dùng; danh sách `[CẦN XÁC MINH]` cần người dùng bổ sung; lưu ý RGB/CMYK cho nhà in.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `scripts/doc_ingest.py` | Đọc tệp người dùng (PDF/DOCX/XLSX/PPTX/ảnh…) thành `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` |
| `_shared/fonts/` | Bộ font in ấn Be Vietnam Pro + Spectral + `fonts.css` | `new_design.py` chép sang thư mục thiết kế; `print_common.py` (FONTS_DIR) |
| `_shared/html/dtp_layout.css` | Token CSS DTP (Baseline Grid, Micro-typography, Overset Ready) | `new_design.py` chép sang `css/dtp_layout.css`, template nhúng qua link |
| `_shared/standards/layout_principles.md` | Chuẩn mực dàn trang DTP đúc kết từ DesignCraft | Tham chiếu tiêu chuẩn căn lề, tỷ lệ chữ và nhịp dọc |
| `scripts/claim_guard.py` | Quét over-claim theo Luật R5 trước khi bàn giao | `python3 scripts/claim_guard.py --input <file> [--profile ads]` |
