---
name: boc-tach-pdf
display-name: Bóc Tách PDF
description: >-
  Số hóa toàn diện file PDF scan dài thành Word (.docx) hoặc Markdown (.md) trung thực — giữ nguyên chữ (kể cả dấu tiếng Việt, chữ Nhật), bảng biểu, hình minh họa và bố cục header văn bản hành chính, có đối chiếu OCR độc lập và gắn cờ [CẦN XÁC MINH].
  USE WHEN: Người dùng cần bóc tách OCR tài liệu giấy scan, PDF scan dài sang định dạng văn bản có thể chỉnh sửa (.docx, .md, bảng ra .xlsx).
  DO NOT USE WHEN: Cần dịch thuật đa ngôn ngữ giữ nguyên định dạng PDF tỷ lệ 1:1 (dùng 'dich-giu-dinh-dang' hoặc 'ejv-translate'), hoặc soạn thảo văn bản từ đầu (dùng 'xu-ly-van-phong').
trigger: Bóc tách PDF scan, số hóa tài liệu scan, OCR PDF, chuyển file scan sang Word DOCX
category: docs
needs_file: true
file_filter: pdf
---

# Quy trình Số hóa PDF Scan Toàn diện (v4)

Mục tiêu: bản số hóa mà người kiểm tra so từng dòng với bản giấy **không tìm ra chữ sai, số sai, dòng thiếu**. Chỗ nào không chắc phải được gắn cờ, không được đoán.

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Agent tự đọc ảnh (view_file) để OCR. Không gọi REST API ngoài (Gemini API, OpenAI API...), không yêu cầu API key.
> - Python/Swift scripts chỉ làm việc cơ học: render ảnh, tiền xử lý, OCR engine cục bộ để ĐỐI CHIẾU, ghép file, xuất DOCX/XLSX.
> - Autonomous Full-Run: chạy liên tục đến khi xong, không dừng xin phép giữa chừng (trừ bước dọn dẹp xóa file).
> - **Không có "đường tắt tiết kiệm token"**: không bỏ qua trang, không bỏ bước tự kiểm, không thay bước OCR của Agent bằng OCR engine.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

| Placeholder | Giá trị |
|---|---|
| `<skill_dir>` | `<workspace>/.agents/skills/boc-tach-pdf/` |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |
| `<processing_dir>` | Mặc định `~/Downloads/AIWF_Output/_process/<tên_pdf>_processing/` (script tự tạo) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - KHÔNG tạo thư mục xử lý cạnh file PDF của người dùng, KHÔNG tạo trong repo. Chỉ dùng `--output-dir` khi người dùng chỉ định nơi khác.
> - Thành phẩm (`.docx`, `.md`, `.xlsx`, báo cáo xác minh) được sao chép vào `<output_dir>`.

Lệnh luôn dùng `python3` (máy macOS không có lệnh `python`) và `pip3`.

---

## BƯỚC 0 — Tiếp nhận (Intake) & Kiểm tra môi trường

1. Xác định: file PDF, ngôn ngữ (Việt / Nhật / Anh / trộn), định dạng đầu ra (mặc định: MD + DOCX; thêm XLSX nếu tài liệu nhiều bảng số hoặc người dùng yêu cầu), thư mục đầu ra.
2. Chạy:
   ```bash
   python3 <skill_dir>/scripts/check_deps.py
   ```
   - Thiếu core → `pip3 install PyMuPDF Pillow python-docx pypandoc-binary numpy`
   - Mục "OCR ENGINE ĐỐI CHIẾU" phải có ít nhất 1 dòng ✅ (Apple Vision trên macOS, hoặc Tesseract có `vie`+`jpn`). Nếu không có: vẫn làm được, nhưng bắt buộc tự kiểm 2 lượt (Bước 2.5).

---

## BƯỚC 1 — Render và tiền xử lý

```bash
python3 <skill_dir>/scripts/core_pdf_to_images.py "<file.pdf>"
python3 <skill_dir>/scripts/preprocess_images.py <processing_dir> --enhance
```
- `01.input/page_NNN.png` = ảnh GỐC (không bao giờ bị ghi đè; dùng cho đối chiếu và cắt hình).
- `02.process/preprocessed/page_NNN.png` = bản đã khử nghiêng + khử nhiễu → **Agent đọc bản này**. `preprocess_report.json` ghi góc nghiêng đã sửa.
- Nếu một chỗ trên bản preprocessed trông lạ (nét mất, dấu mờ) → mở thêm bản gốc cùng vùng để so.

---

## BƯỚC 2 — OCR từng trang (Agent đọc ảnh) + tự kiểm + đối chiếu

Làm tuần tự theo trang, lưu checkpoint `02.process/page_NNN.png.md` ngay sau mỗi trang (trang đã có MD thì bỏ qua khi chạy lại). Tối đa 2 trang/lượt view; trang dày chữ hoặc có bảng: 1 trang/lượt.

### 2.1 Chọn cách nhìn trang (tiling)
Bắt buộc cắt tile khi: trang > ~35 dòng chữ, bảng ≥ 5 cột hoặc nhiều số, chữ nhỏ (chú thích, footnote), hoặc ảnh dài > 2500 px (IDE thu nhỏ ảnh làm mất dấu và số).
```bash
python3 <skill_dir>/scripts/tile_page.py <processing_dir> --page 7                    # lưới tự động
python3 <skill_dir>/scripts/tile_page.py <processing_dir> --page 7 --rows 3 --cols 1  # 3 dải ngang
python3 <skill_dir>/scripts/tile_page.py <processing_dir> --page 7 --box 0.05,0.40,0.95,0.78  # chỉ vùng bảng, phóng to
```
Đọc tile theo thứ tự r1c1 → r1c2 → r2c1...; dòng nằm ở vùng chồng lấn chỉ chép MỘT lần.

### 2.2 Quy tắc chép (TRUNG THỰC TUYỆT ĐỐI)
OCR là **chép lại**, không phải biên tập:
- Giữ nguyên từng chữ, dấu câu, gạch ngang (—, –, -), dấu hai chấm cuối tiêu đề, lỗi chính tả của bản gốc, cách viết hoa, cách đặt dấu (HOÀ/HÒA, UỶ/ỦY). **Không** "sửa cho đẹp", không áp quy tắc văn phong.
- Số liệu chép đúng từng ký tự, giữ dấu phân cách gốc (`12.450.000.000`, `3.750,5`, `１５％`).
- Chỗ không chắc (dấu mờ, số nhòe, tên riêng khó đọc): chép phương án tốt nhất kèm `[CẦN XÁC MINH: lý do]`. Hoàn toàn không đọc được: `[Không đọc được]`. Cấm đoán số.
- Không chép số trang in đơn độc ở đầu/chân trang.

**Định dạng Markdown:**
| Thấy trên trang | Viết trong MD |
|---|---|
| Tiêu đề lớn đậm căn giữa / tiêu đề mục IN HOA đậm | `## TIÊU ĐỀ` / `### I. TÊN MỤC` (không dùng `#`) |
| Chữ đậm / nghiêng / đậm nghiêng | `**...**` / `*...*` / `***...***` |
| Dòng căn giữa / căn phải | `<center>...</center>` / `<div style="text-align: right">...</div>` |
| Gạch chân thật (liền chữ) | `<u>...</u>`. Đường kẻ ngắn tách rời dưới tên cơ quan/tiêu ngữ KHÔNG phải gạch chân: bỏ qua |
| Gạch đầu dòng / đánh số | `- ...` / `1. ...` / `a) ...` (giữ nguyên ký hiệu gốc) |
| Bảng | Bảng Markdown, đủ mọi cột, ô trống để trống, ô gộp: lặp lại nội dung vào ô bị gộp và ghi `<!-- merged cell -->` sau bảng |
| Hình/biểu đồ/sơ đồ/con dấu | `[Hình minh họa: mô tả ngắn \| crop=x0,y0,x1,y1]` với toạ độ tỉ lệ 0–1 của vùng hình trên trang (đo trên ảnh). Không có `crop=` thì script dùng ảnh nhúng của trang nếu có |
| Chú thích hình | `*Hình 2.1: ...*` |

**Header văn bản hành chính (NĐ 30)**: mỗi dòng in trên giấy là MỘT dòng trong MD (không gộp), khối trái trước, khối phải sau, giữ đúng đậm/nhạt:
```markdown
UBND TỈNH NGHỆ AN
**SỞ TÀI CHÍNH**

**CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**
**Độc lập - Tự do - Hạnh phúc**

Số: 1520/STC-QLNS
V/v hướng dẫn lập dự toán năm 2026

*Nghệ An, ngày 03 tháng 9 năm 2025*

Kính gửi: Các sở, ban, ngành cấp tỉnh.
```

**Ví dụ một trang hoàn chỉnh** (có bảng, hình, chỗ nghi ngờ):
```markdown
### II. KẾT QUẢ THỰC HIỆN

Tổng kinh phí đã giải ngân là 8.215,4 triệu đồng, đạt 66% kế hoạch [CẦN XÁC MINH: chữ số "66" bị nhòe, có thể là "68"].

| STT | Nội dung | Kế hoạch | Thực hiện |
|---|---|---|---|
| 1 | Hạ tầng mạng | 4.200 | 3.100,2 |
| 2 | Số hóa hồ sơ | 3.750,5 | 2.615 |
|  | **Tổng cộng** | **7.950,5** | **5.715,2** |

[Hình minh họa: Biểu đồ cột tiến độ giải ngân theo quý | crop=0.10,0.55,0.90,0.86]
*Hình 1: Tiến độ giải ngân năm 2025*
```

### 2.3 Tự kiểm TRƯỚC KHI lưu trang (bắt buộc, ghi vắn tắt vào cuối MD dưới dạng comment)
Mở lại ảnh/tile và kiểm:
1. **Đếm dòng/đoạn**: số đoạn trong MD khớp số đoạn trên trang; không bỏ đoạn đầu/cuối trang.
2. **Bảng**: số hàng và số cột khớp ảnh; tiêu đề cột đúng thứ tự; dòng tổng có mặt.
3. **Số liệu**: liệt kê MỌI con số trong MD, đối chiếu từng số với ảnh (tile/box phóng to). Có dòng tổng thì cộng thử: lệch → xem lại từng số.
4. **Dấu tiếng Việt / chữ Nhật**: soát tên riêng, địa danh, thuật ngữ; chữ Nhật soát từng ký tự Kanji dễ nhầm (未/末, 土/士).
5. Ghi cuối file: `<!-- selfcheck: đoạn=12/12, bảng=1 (5x4 khớp), số=17 đã soát, tổng khớp -->`

### 2.4 Đối chiếu bằng OCR engine độc lập (sau khi xong tất cả trang, hoặc theo đợt)
```bash
python3 <skill_dir>/scripts/ocr_crosscheck.py <processing_dir>
```
- Apple Vision chạy 2 lượt (tiếng Việt và tiếng Nhật) rồi chọn lượt phù hợp cho từng vùng chữ; so với MD của Agent và sinh `02.process/needs_verification.json` + ảnh crop phóng to `02.process/verify/page_NNN_<id>.png` cho từng cờ:
  `number_mismatch` / `number_format` / `number_not_seen_by_engine` / `number_missing_in_agent` (số), `diacritic_mismatch` (dấu), `agent_line_unsupported` (dòng Agent viết mà engine không thấy: nguy cơ chép nhầm), `possible_omission` (dòng có trên giấy mà MD thiếu).
- **Vòng xử lý từng cờ** (bắt buộc, không bỏ qua):
  1. `view_file` ảnh crop của cờ.
  2. Nếu Agent sai → sửa `page_NNN.png.md`.
  3. Nếu Agent đúng (engine đọc sai, rất hay gặp với dấu tiếng Việt) → ghi vào `02.process/verified.json`: `{"<id>": "đã xem crop: đúng là 'tầng'"}`.
  4. Chạy lại `ocr_crosscheck.py` đến khi exit 0.
  5. Cờ vẫn không thể quyết → `ocr_crosscheck.py <processing_dir> --finalize` để chèn `[CẦN XÁC MINH: ...]` vào MD.
- Exit 4 (không có engine): chuyển sang 2.5.

### 2.5 Khi không có OCR engine: tự kiểm lượt 2 độc lập
Đọc lại từng trang từ đầu (tile khác lưới với lượt 1, ví dụ `--rows 4`), chép lại riêng các SỐ và TÊN RIÊNG, so với MD lượt 1; mọi chỗ khác nhau phải xem box phóng to và quyết định hoặc gắn `[CẦN XÁC MINH]`. Ghi `02.process/selfcheck.json`: `{"pages": {"1": {"numbers_checked": 17, "diffs_resolved": 2, "flags_left": 0}}}`.

### Ảnh quá kém
Thử `preprocess_images.py <processing_dir> --enhance --pages N` lại và xem bản gốc + bản preprocessed; vẫn không đọc được → `[Không đọc được]` cho vùng đó, không bịa.

---

## BƯỚC 3 — Ghép MD
```bash
python3 <skill_dir>/scripts/core_merge_md.py <processing_dir>
```
→ `02.process/MERGED.md` (có `<!-- page: N -->`). Script FAIL và liệt kê trang nếu còn trang chưa OCR (Zero-Loss).

---

## BƯỚC 4 — Xuất DOCX (mặc định làm luôn, không cần hỏi)

```bash
python3 <skill_dir>/scripts/analyze_format.py <processing_dir>
python3 <skill_dir>/scripts/extract_images.py <processing_dir>
python3 <skill_dir>/scripts/generate_reference.py <processing_dir>
python3 <skill_dir>/scripts/export_docx.py <processing_dir> [<output_dir>]
```
- `analyze_format.py` chỉ xếp `hanh_chinh_nd30` khi trang 1 có khối header (Quốc hiệu + Tiêu ngữ, hoặc "Số: 12/BC-..") và điểm ≥ 5; in ra bằng chứng. Agent nhìn trang 1 để xác nhận; sai thì sửa `doc_type` trong `02.process/format_spec.json` rồi chạy lại `generate_reference.py`.
- `extract_images.py` bỏ qua ảnh scan toàn trang; hình trong trang scan được cắt theo `crop=` ở placeholder.
- `export_docx.py`:
  - CHẶN xuất nếu chưa đối chiếu OCR hoặc còn cờ mở (dùng `--allow-unverified` chỉ khi người dùng đồng ý, và phải báo trong chat).
  - 5 layer: Pandoc (+ chèn hình, giữ ngắt dòng header, căn giữa/phải) → trang ngang/xóa số trang → dựng header NĐ 30 (chỉ khi nhận diện chắc chắn; gặp dòng lạ thì giữ nguyên) → định dạng đoạn/bảng → font (Đông Á riêng cho chữ Nhật).
  - Cuối cùng kiểm tra bảo toàn nội dung: mọi từ của MERGED.md phải có trong DOCX; có cảnh báo thì mở DOCX tìm chỗ mất.
  - Đọc `02.process/figures_report.json`: placeholder nào chưa có ảnh → thêm `crop=` và xuất lại.

### Tùy chọn: Excel (tài liệu nhiều bảng số)
```bash
python3 <skill_dir>/scripts/optional_export_xlsx.py <processing_dir>/02.process/MERGED.md --out <output_dir>/<tên>.xlsx
```
Mọi bảng → mỗi bảng 1 sheet; số kiểu Việt Nam (`4.200` = 4200, `3.750,5` = 3750,5); dòng Tổng dùng `=SUM()` sống và so với số trên giấy. Exit 3 = có tổng lệch hoặc ô nghi ngờ → mở cột "Ghi chú kiểm tra", xem lại ảnh, sửa MD và xuất lại.

### Dọn dẹp (HỎI người dùng trước vì là thao tác xóa)
*"Anh/chị kiểm tra file giúp; nếu ổn tôi xóa thư mục trung gian nhé."* Đồng ý thì:
```bash
python3 <skill_dir>/scripts/cleanup.py <processing_dir>
```

---

## Bài Học Thực Chiến (đọc trước khi debug)

1. **Apple Vision dùng mã `vi-VT` cho tiếng Việt**, không phải `vi-VN` (mã sai bị bỏ qua âm thầm → mất dấu). Không đọc được Việt + Nhật trong cùng một lượt: lượt vi làm mất chữ Nhật, lượt ja làm rơi dấu tiếng Việt. `mac_ocr.swift` chạy 2 lượt; `ocr_crosscheck.py` chọn theo từng vùng.
2. **OCR engine chỉ để đối chiếu.** Trên trang nghiêng, engine trộn thứ tự dòng và làm phẳng bảng; không bao giờ dùng output engine làm MD thay cho Agent. `mac_ocr.swift` không ghi vào `page_NNN.png.md`.
3. **PDF scan = mỗi trang là một ảnh nhúng toàn trang.** Đó không phải hình minh họa; hình thật phải cắt bằng `crop=`.
4. **Biến thể đặt dấu (UỶ/ỦY, HOÀ/HÒA)**: so khớp dùng dạng bỏ dấu (`analyze_format.py`, `02_structure.py`). Agent vẫn chép đúng cách đặt dấu trên giấy.
5. **Header NĐ 30 bị Pandoc gộp dòng**: `00_pandoc.py` giữ ngắt dòng cứng trong vùng header trang 1; Layer 2 đọc theo dòng và giữ đậm/nhạt từ MD.
6. **Số trang in trên giấy**: Agent không chép; `01_layout.py` xóa thêm số đứng ngay sau marker trang.
7. **Ký tự `\n` literal trong python-docx**: xuống dòng mềm dùng `p.add_run("\n")`, không phải `"\\n"`.
8. **LibreOffice/WPS hiển thị bảng hỏng** nếu reference.docx thiếu style của Pandoc: `generate_reference.py` luôn xuất phát từ reference mặc định của Pandoc.

---

## 5. Quality Gate & Giao thức Bàn giao Sạch

### Checklist Kiểm tra Chất lượng (Quality Gate)
1. ✅ Zero-Loss: 100% trang có MD (`core_merge_md.py` không FAIL); mỗi trang có dòng `<!-- selfcheck: ... -->`.
2. ✅ Đối chiếu OCR: `needs_verification.json` status `clean` hoặc `marked` (hoặc `selfcheck.json` khi không có engine). Mọi cờ đã xem crop.
3. ✅ Confidence Flagging: chỗ không chắc mang `[CẦN XÁC MINH: ...]`; đếm số cờ còn lại để báo người dùng.
4. ✅ Trung thực: không sửa chữ/dấu câu của bản gốc (không áp quy tắc văn phong lên bản OCR).
5. ✅ Bảng: số hàng/cột khớp ảnh; dòng tổng khớp phép cộng (hoặc đã gắn cờ). Excel dùng công thức sống `=SUM()`.
6. ✅ Hình minh họa: `figures_report.json` không còn placeholder chưa có ảnh (hoặc đã báo lý do).
7. ✅ DOCX: kiểm tra bảo toàn nội dung đạt 100%; đã mở/render xem trang 1 (header) và một trang có bảng.
8. ✅ Thành phẩm nằm trong `<output_dir>` (mặc định `~/Downloads/AIWF_Output/`), không có gì trong repo hay cạnh file gốc của người dùng.

### Giao thức Bàn giao Sạch
Khung chat chỉ báo: số trang, engine đối chiếu đã dùng, số cờ đã xử lý / số `[CẦN XÁC MINH]` còn lại (kèm trang), và link trỏ đến file `.docx` / `.md` / `.xlsx` trong `<output_dir>`.

---

## Tác giả

**Nguyễn Duy Tùng**
Tư vấn xây dựng Song sinh số Doanh nghiệp (EDT) & Lực lượng Lao động AI (AI Workforce)
Liên hệ: 0904.004.920
