---
name: xu-ly-van-phong
display-name: Xử Lý Văn Phòng
description: >-
  Soạn thảo, chỉnh sửa, chuyển đổi và tái tạo văn bản hành chính theo chuẩn thể thức Nghị định 30/2020/NĐ-CP hoặc chuẩn thẩm mỹ doanh nghiệp (Word .docx, PowerPoint .pptx, Excel .xlsx mẫu, PDF).
  USE WHEN: Người dùng cần soạn thảo công văn, quyết định, hợp đồng, tờ trình, quy chế hành chính, hoặc định dạng chuyển đổi tài liệu văn phòng.
  DO NOT USE WHEN: Cần lập mô hình báo cáo tài chính - kế toán chuyên sâu có công thức động Live Formulas (dùng 'bao-cao-kt'), thiết kế ấn phẩm in ấn tiếp thị đồ họa cao cấp như Leaflet/Brochure (dùng 'thiet-ke' — kể cả slide dạng ấn phẩm xuất PDF), hoặc dịch thuật văn bản đa ngôn ngữ (dùng 'ejv-translate').
trigger: Xử lý văn phòng, soạn công văn, tạo file word, làm file PowerPoint pptx theo template, chuyển đổi văn bản, chuẩn NĐ 30
category: docs
needs_file: false
file_filter: office
---

# Xử lý Văn phòng 2.0 (Bi-directional Pipeline - Gemini 3.8 Multi-Agent)

Skill xử lý toàn diện file văn phòng (DOCX, XLSX, PPTX, PDF). Hệ thống hoạt động theo **Kiến trúc Song song 2 Chiều (Extractor & Generator)**: bóc tách Dữ liệu/Giao diện từ file cũ và vẽ lại hoàn toàn bằng Code.

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Skill này chạy hoàn toàn bằng khả năng tích hợp sẵn của Antigravity IDE (Gemini 3.8).
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài hoặc yêu cầu API key.
> - Toàn bộ năng lực tư duy, thiết kế bố cục và chuyển đổi cấu trúc là của chính Agent (LLM nội bộ).
> - Kịch bản Node.js/Python chỉ đóng vai trò Generator/Extractor nhị phân.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) theo quy trình đến khi tạo thành phẩm.

---

## 1. Nguyên lý Hoạt động Cốt lõi (2 Chiều)

Mọi tài liệu đi qua hệ thống đều phân tách rõ Tầng Dữ liệu (Content) và Tầng Hiển thị (UI/Theme). Không sửa trực tiếp trên file xấu — bóc tách Data rồi sinh file mới.

### Chiều Đọc & Bóc tách (The Extractor) — Python

1. **Content:** Tệp người dùng → `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out <process_dir>/ingest --json` (từ gốc repo) → đọc `source.md` + `manifest.json` (mã `3`: đọc ảnh `ocr_pages/`; `2`: hỏi người dùng theo `manifest.message`; `4`: cài theo `manifest.message`). Công thức Excel gốc: `openpyxl` (`data_only=False`).
2. **Brand Kit (UI):** Chạy `scripts/extractor/extract_brand.py` (DOC/ODT/RTF/XLS/ODS/PPT/ODP tự chuyển OOXML bằng LibreOffice) — đọc `theme1.xml`, xuất `brand_kit.json` theo **schema chuẩn duy nhất** (khóa màu `dk1, lt1, dk2, lt2, accent1..accent6` — xem `resources/extractor_docs.md`).
3. **Assets:** Trích ảnh/logo từ `media/` ra `assets/`. Bóc Data từ biểu đồ/sơ đồ (không copy hình chết).

### Chiều Ghi & Tái tạo (The Generator) — Node.js

1. **Global Styles:** Nạp `brand_kit.json` vào Document Styles / Header Styles / Slide Master.
2. **Tái tạo Assets:** Nhúng ảnh từ `assets/` (kiểm tra tồn tại trước). Vẽ lại sơ đồ/biểu đồ dạng "sống".
3. **Đổ Content:** Đưa dữ liệu thô vào khung đã cấu hình Brand DNA và xuất bản vào `<output_dir>`.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file đầu ra trước khi xuất bản file:

| Placeholder | Quy ước xác định đường dẫn |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** (ví dụ: đường dẫn do user cung cấp) hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Cho phép người dùng chọn/chỉ định thư mục sẽ lưu file đầu ra (Word, Excel, PowerPoint, PDF).
> - Mọi file xuất bản thành phẩm PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - TUYỆT ĐỐI KHÔNG xuất file thành phẩm trực tiếp vào thư mục gốc của codebase nếu người dùng không yêu cầu, để tránh làm phình dung lượng git repo.

---

## Bước 0: Tiếp nhận yêu cầu (Intake)

Trước khi chọn track, xác định và ghi vào `<process_dir>/intake.md` (`<process_dir>` = `_process/<ten_tai_lieu>/`, đã được .gitignore):
1. **Loại đầu ra:** văn bản hành chính NĐ 30, tài liệu doanh nghiệp (đề xuất, báo cáo, quy trình), slide, Excel, hay chỉ chuyển đổi định dạng.
2. **Nguồn nội dung:** file mẫu (cần bóc), file nội dung (MD, DOCX, PDF), hay chỉ có mô tả trong chat.
3. **Văn bản NĐ 30 cần đủ dữ kiện:** cơ quan chủ quản, cơ quan ban hành, số và ký hiệu (hoặc để trống số), địa danh, ngày, người nhận (Kính gửi), người ký (quyền hạn, chức vụ, họ tên), nơi nhận. Thiếu dữ kiện nào thì HỎI, không tự đặt tên người, số văn bản hay căn cứ pháp lý. Căn cứ không chắc số hiệu: để `...` và gắn `[CẦN XÁC MINH]`.
4. **Thư mục đầu ra** `<output_dir>`.

---

## 2. Đường ray Đôi (Dual-Track) & Agent Workflow

**TỐI QUAN TRỌNG:** Agent KHÔNG ĐƯỢC tự ý đoán luồng định dạng. Trước khi tạo file, bắt buộc hỏi người dùng chọn 1 trong 3 tùy chọn:

| Lựa chọn | Luồng Thực thi | Ứng dụng | Kỹ thuật & Rào cản |
|:---:|---|---|---|
| **[1]** | **Chuẩn Hành chính Quốc gia (NĐ 30)** | Công văn, Tờ trình, Quyết định, Thông báo, Kế hoạch, Báo cáo hành chính | **Đen/Trắng tuyệt đối.** Cấm Brand Kit. Times New Roman, lề Trái 3 cm, Phải 2 cm, Trên/Dưới 2 cm, header Quốc hiệu 2 cột. Sinh bằng `scripts/generator/nd30_docx.py` từ JSON (`standards/nd30.md`), kiểm bằng `scripts/qa/check_nd30.py`. Khung nội dung: `templates/docx-hanh-chinh-*.md` |
| **[2]** | **Chuẩn Thẩm mỹ Hiện đại (Doanh nghiệp)** | Đề xuất, Pitch Deck, Báo cáo nội bộ, Tài liệu quy trình | **Kích hoạt Brand Kit.** Dùng Node.js Generator (`docx`, `exceljs`, `pptxgenjs`). Bảng zebra, callout box, nhúng logo và màu công ty |
| **[3]** | **Trích xuất Brand & Assets (chỉ bóc tách)** | Cào file mẫu lấy format làm chuẩn về sau | Chỉ chạy Extractor: `extract_brand.py` → `brand_kit.json` + `assets/`. Báo cáo thông số bóc được |

### Nhánh đặc biệt: User chỉ đưa CONTENT (file MD, text) — không có file mẫu

Đây là tình huống thường gặp nhất. KHÔNG được nhảy thẳng vào generate. Làm theo quy trình 4 bước trong `resources/content_analysis.md` (tóm tắt):

1. **Phân tích content** → lập Kế hoạch Thiết kế (chia slide/sheet/heading, bảng nào thành chart, số nào thành callout) và trình user duyệt.
2. **Chốt Brand Kit** → đề xuất 2-3 preset từ thư viện 10 bộ (`standards/brand_kits/README.md` - phân loại sáng/tối, nóng/lạnh/trung tính, cổ điển/hiện đại), hoặc nhận màu/logo user cung cấp. **CẤM dùng `brand_kits/example/` cho tài liệu user thật.**
3. **Biên tập nội dung** theo định dạng đích (mục 3b của `content_analysis.md`).
4. **Generate + QA loop.**

### Quy trình Track 1 (NĐ 30) - bắt buộc dùng generator, không tự vẽ header

```bash
# 1. Viết nội dung vào JSON theo standards/nd30.md (mẫu: examples/nd30-cong-van.json, examples/nd30-quyet-dinh.json)
# 2. Sinh DOCX
python3 .agents/skills/xu-ly-van-phong/scripts/generator/nd30_docx.py -i <process_dir>/vanban.json -o <output_dir>/<Ten van ban>.docx
# 3. Kiểm thể thức + render PNG
python3 .agents/skills/xu-ly-van-phong/scripts/qa/check_nd30.py <output_dir>/<Ten van ban>.docx --render-dir <process_dir>/review
```
- Generator báo `❌ LỖI DỮ LIỆU` (thiếu trường, ký hiệu sai dạng, công văn ghi tên loại trong ký hiệu...) → sửa JSON, chạy lại.
- Checker `FAIL` → sửa JSON / lựa chọn, chạy lại đến khi `✅ NĐ30 CHECK PASS`.
- Mỗi `WARN` (tên cơ quan / địa danh cũ trước sắp xếp 2025, năm trong ký hiệu) phải được sửa hoặc xác nhận với người dùng.
- MỞ TỪNG ẢNH PNG trong `<process_dir>/review/` và soát: header 2 cột thẳng hàng, đường kẻ dưới tên cơ quan / tiêu ngữ / trích yếu, chữ ký không bị tách trang.
- Văn bản NĐ 30 do người dùng gửi lên để soát lỗi: chạy thẳng `check_nd30.py` trên file đó và báo cáo từng lỗi.

Ngoài các track trên, nghiệp vụ PDF (cắt/ghép/trích/convert) làm theo `resources/pdf.md` và `resources/convert.md` — xử lý cục bộ, không upload cloud.

---

## 3. Kiến trúc Vật lý của Skill

### Tầng 1: Tài liệu Hướng dẫn (`resources/`)

| File | Nội dung |
|---|---|
| `extractor_docs.md` | Bóc Brand Kit & Data bằng Python/XML Unpack. **Chứa schema chuẩn brand_kit.json** |
| `generator_docs.md` | Sinh file bằng Node.js từ Brand Kit. QA loop bắt buộc |
| `content_analysis.md` | **Content Analyzer** — quy tắc phân tích MD/text thô và map sang DOCX/XLSX/PPTX khi không có file mẫu |
| `xlsx.md` | Nguyên tắc Excel: Live Formula, Zero Error, column width chuẩn |
| `pptx.md` | Nguyên tắc slide: yếu tố thị giác, cỡ chữ, layout, QA visual |
| `pdf.md` | PDF digital vs scan, cắt/ghép/trích, PDF→DOCX |
| `convert.md` | Pipeline MD→DOCX (Pandoc), PDF→DOCX, DOCX→PDF |

### Tầng 2: Tiêu chuẩn (`standards/`)

- `nd30.md`: (Track 1) Bộ luật cứng cho văn bản nhà nước.
- `brand_kits/`: (Track 2) Thư mục "sống" — mỗi doanh nghiệp 1 folder con gồm `brand_kit.json` + `assets/`. Có sẵn **10 preset** phân loại theo tông màu (xem `brand_kits/README.md`) và `example/` (chỉ dùng test script).
- `dynamic_structure/`: 11 file quy chuẩn bố cục (page-setup, typography, heading, table, cover, header-footer, caption, list, special-blocks, xlsx-structure, pptx-structure) — nhận tham số màu/font từ Brand Kit.

### Tầng 3: Kịch bản Thực thi (`scripts/`)

- `generator/nd30_docx.py`: Sinh văn bản hành chính NĐ 30 (công văn, quyết định, tờ trình, thông báo, báo cáo, kế hoạch...) từ JSON. Track 1 BẮT BUỘC dùng script này.
- `qa/check_nd30.py`: Kiểm thể thức NĐ 30 cho mọi DOCX (lề, font, Quốc hiệu, Tiêu ngữ, số ký hiệu, ngày tháng, căn cứ, Điều, Nơi nhận, `./.`, tách trang chữ ký) + cảnh báo tên cơ quan / địa danh cũ. `--render-dir` xuất PNG để soát.
- `extractor/extract_brand.py`: Bóc Brand Kit từ màu và font thực sự dùng trong file mẫu (theme chỉ để lấp chỗ trống). Thoát mã 3 nếu file chỉ có theme mặc định Office.
- `extractor/office/`: Toolkit XML - unpack, pack, clone_text, validate (cần `defusedxml`), soffice (tự tìm LibreOffice trong PATH, `/Applications/LibreOffice.app`, Program Files hoặc biến `SOFFICE`).
- `extractor/convert/` + `extractor/format/`: Convert MD/PDF→DOCX; `format_docx.py --mono` (đen trắng) hoặc `--brand-kit <json>` áp khung mặc định cho file Pandoc.
- `generator/template_docx.js` (đã cài sẵn khung quy tắc 9), `generator/template_xlsx.js`, `generator/template_pptx.js`: 3 khung Node.js sinh file từ `brand_kit.json`, cú pháp `node <script> <brand_kit.json> <output>`. Copy vào `<process_dir>` rồi thay phần CONTENT.

### Tầng 4: Templates & Examples

- `templates/docx-hanh-chinh-*.md`: 9 mẫu khung nội dung văn bản NĐ 30 (công văn, quyết định, tờ trình...) + 1 mẫu đề xuất.
- `examples/`: file tham chiếu, mở xem để "nhìn thấy" đích đến trước khi tạo file mới. Track 2: `docx-mau-khung-chuan` (đen trắng), `docx-mau-de-xuat-brand` (bìa/callout/bảng màu), `pptx-mau-brand` (5 layout slide), `xlsx-mau-tracking` (live formula). Track 1 NĐ 30: `docx-cong-van-mau.docx` và `docx-quyet-dinh-mau.docx`, sinh bằng `nd30_docx.py` từ `nd30-cong-van.json` và `nd30-quyet-dinh.json` (đã qua `check_nd30.py`, dùng cơ cấu hành chính sau sắp xếp 2025, căn cứ chưa rõ số hiệu để `...`).

---

## Nguyên tắc Tuân thủ Tuyệt đối

1. **HỎI TRƯỚC KHI VẼ:** Luôn dùng Bảng 3 Lựa chọn hỏi User trước khi tạo file.
2. **TRACK 1 CẤM MÀU SẮC & PHẢI DÙNG GENERATOR:** User chọn [1] → nghiêm cấm màu, callout, font nghệ thuật. Sinh file bằng `nd30_docx.py`, kiểm bằng `check_nd30.py`; không tự viết script vẽ header/chữ ký và không đi đường Pandoc. Không trộn format NĐ 30 với format doanh nghiệp.
3. **TRACK 2 PHẢI DÙNG NODE.JS:** User chọn [2] → dùng `docx`/`exceljs`/`pptxgenjs`. Không dùng `python-docx` để sinh file mới. Riêng trường hợp "giữ nguyên format file mẫu, chỉ thay nội dung" → dùng Unpack/Pack XML.
4. **MỘT SCHEMA DUY NHẤT:** Mọi script đọc/ghi `brand_kit.json` phải theo schema trong `extractor_docs.md`. Cấm hardcode mã màu.
5. **SƠ ĐỒ PHẢI SỐNG:** Cấm copy SmartArt/Chart cũ bằng ảnh (trừ logo). Bóc Data và vẽ lại bằng code.
6. **EXCEL PHẢI SỐNG:** Mọi ô tính toán dùng Live Formula, không hardcode kết quả.
7. **QA TRƯỚC KHI GIAO:** Convert sang PDF/ảnh (`check_nd30.py --render-dir` cho Track 1; `soffice.py` + `pdftoppm` cho Track 2, xem `generator_docs.md` mục 5) và MỞ ẢNH soi bằng mắt ít nhất 1 vòng Generate → Inspect → Fix. Mọi tổ hợp text/nền đạt contrast WCAG.
8. **CONTENT-ONLY PHẢI QUA PHÂN TÍCH:** User chỉ đưa MD/text → bắt buộc chạy quy trình 4 bước của `content_analysis.md` (phân tích → chốt brand → biên tập → generate). Cấm dùng `brand_kits/example/` cho tài liệu thật, cấm nhồi 100% văn xuôi vào Excel/Slide.
9. **DOCX PHẢI THEO KHUNG MẶC ĐỊNH CHUNG:** Body justify + first-line indent 1.25cm + spacing 3pt/3pt + line atLeast 1.3 lần cỡ chữ; phân cấp bằng ký tự đầu dòng với left indent 0, đề mục cấp cao nhô trái 1.0cm (chi tiết trong `dynamic_structure/docx-page-setup.md`). Bullet dấu gạch `-`, không dùng `•`. Bảng full khổ nội dung, cột fit theo content, chữ trong bảng nhỏ hơn body 1-2pt. Nội dung phải qua biên tập, không copy nguyên văn MD. **Khung này áp dụng cho MỌI track; Brand Kit (Track 2) chỉ đắp lớp màu lên khung** gồm màu bảng biểu, màu chữ heading, highlight, callout box và thiết kế bìa, không được thay đổi thông số khung. Ngoại lệ duy nhất: Track 1 lùi đầu dòng 1,27 cm vì NĐ 30 chỉ cho phép 1 cm hoặc 1,27 cm (đã cài trong `nd30_docx.py`).
10. **KHỬ DẤU VẾT AI TRONG DẤU CÂU:** Cấm em dash `—` (thay ` - ` hoặc từ nối), cấm dấu hai chấm trong tiêu đề, cấm Oxford comma `, và`. Áp dụng cho mọi text do Agent biên tập trong DOCX/PPTX/XLSX, bảng quy tắc chi tiết trong `content_analysis.md` mục 3b. Sau generate phải đếm kiểm tra: `—` và `:` trong heading đều phải bằng 0. **Ngoại lệ NĐ 30:** nhãn cố định của thể thức giữ nguyên dấu câu (`Số:`, `V/v`, `Kính gửi:`, `QUYẾT ĐỊNH:`, `Nơi nhận:`, `Lưu: VT`, `Điều 1.`, `;`/`.` cuối căn cứ và nơi nhận, `./.`).
11. **XUẤT FILE ĐẦU RA RA NGOÀI CODEBASE:** Mọi file xuất bản thành phẩm (DOCX, XLSX, PPTX, PDF) phải được lưu vào `<output_dir>` do người dùng chọn (mặc định: `~/Downloads/AIWF_Output/`), không được ghi trực tiếp vào thư mục gốc codebase để tránh làm tăng dung lượng repo git.
12. **GIAO THỨC BÀN GIAO SẠCH:** Khung chat chỉ chứa tóm tắt ngắn gọn và link trỏ đến file thành phẩm hoàn chỉnh đã tạo tại `<output_dir>`.
13. **Confidence Flagging (chống ảo giác số liệu và căn cứ pháp lý):** Đối với các dữ liệu số liệu tài chính hoặc bảng biểu trích xuất từ file gốc mờ nhạt (độ tin cậy < 85%), bắt buộc gắn cờ `[CẦN XÁC MINH]` vào ô chú thích hoặc cell tương ứng, tuyệt đối cấm tự ý bịa số. Áp dụng tương tự cho số hiệu căn cứ pháp lý, số văn bản, tên cơ quan, tên người ký trong văn bản NĐ 30: không chắc thì để `...` và gắn cờ, không tự đặt.
14. **Quality Gate - Checklist trước khi hoàn tất:**
    - ✅ Track 1: `check_nd30.py` in `✅ NĐ30 CHECK PASS`; mọi `WARN` đã sửa hoặc đã xác nhận với người dùng.
    - ✅ Đã MỞ XEM ảnh PNG render của từng trang/slide (không chỉ chạy lệnh convert).
    - ✅ 100% công thức tính toán bảng tính là Live Formulas (`SUM`, `AVERAGE`...), không gõ số chết.
    - ✅ Khử sạch dấu vết AI trong câu chữ biên tập: 0 em dash `—`, 0 dấu hai chấm trong tiêu đề (trừ nhãn cố định NĐ 30).
    - ✅ Brand kit: `extract_brand.py` thoát mã 0 hoặc dùng preset/màu người dùng đưa; không dùng kit thoát mã 3.
    - ✅ Thành phẩm xuất bản đã lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/`).

---

## Tác giả

**Nguyễn Duy Tùng**
Tư vấn xây dựng Song sinh số Doanh nghiệp (EDT) & Lực lượng Lao động AI (AI Workforce)
Liên hệ: 0904.004.920

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `scripts/doc_ingest.py` | Đọc tệp người dùng (PDF/DOCX/XLSX/PPTX/ảnh…) thành `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` |
| `doc_ingest_bridge` | Gọi doc_ingest từ Python: `load_doc_ingest`, `pdf_preflight` | import trong `scripts/extractor/extract_brand.py, scripts/extractor/convert/convert_pdf_to_docx.py` |
