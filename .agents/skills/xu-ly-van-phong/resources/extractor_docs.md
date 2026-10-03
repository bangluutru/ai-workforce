# Tài liệu Hướng dẫn: Chiều Đọc & Bóc tách (The Extractor)

Hướng dẫn bóc tách Dữ liệu (Content) và Giao diện (Brand Kit) từ một file Office mẫu.

---

## 1. Nguyên lý Bóc tách XML (Unpack XML)

Mọi file `.docx`, `.xlsx`, `.pptx` bản chất là một file nén zip. Thay vì chỉ dùng `python-docx` (chỉ đọc được chữ), Agent giải nén file để vào tầng đáy OOXML lấy cấu trúc chuẩn xác nhất.

```bash
# Unpack file để xem XML thô
python scripts/extractor/office/unpack.py input.docx unpacked/

# Pack lại sau khi sửa (giữ nguyên format gốc, chỉ thay nội dung)
python scripts/extractor/office/pack.py unpacked/ output.docx

# Validate file sau khi pack
python scripts/extractor/office/validate.py output.docx
```

---

## 2. Bóc tách Brand Kit (UI/Theme)

Dùng script có sẵn — KHÔNG tự viết lại:

```bash
python3 scripts/extractor/extract_brand.py file_mau.docx --out standards/brand_kits/ten_doanh_nghiep
```

Nhận `.docx/.pptx/.xlsx`; `.doc/.odt/.rtf` (→ DOCX), `.xls/.ods` (→ XLSX), `.ppt/.odp` (→ PPTX) được tự chuyển bằng LibreOffice trước khi bóc (thiếu LibreOffice → mã `4` kèm lệnh cài). PDF/ảnh không có brand kit → mã `2`.

Script tự động: đếm màu và font thực sự được dùng, bổ sung từ `theme1.xml`, trích toàn bộ ảnh từ `media/` vào `assets/`, lưu `brand_kit.json` (chi tiết cách chọn màu và mã thoát ở cuối mục 2).

### Schema chuẩn của `brand_kit.json` (DUY NHẤT — mọi script phải theo)

```json
{
  "company_name": "TenDoanhNghiep",
  "colors": {
    "dk1": "000000",
    "lt1": "FFFFFF",
    "dk2": "333333",
    "lt2": "F8F9FA",
    "accent1": "C22620",
    "accent2": "D4AF37",
    "accent3": "2E75B6",
    "accent4": "548235",
    "accent5": "BF8F00",
    "accent6": "2F5597"
  },
  "fonts": { "heading": "Inter", "body": "Inter" },
  "assets": { "logo": "assets/logo.png" }
}
```

### Ý nghĩa từng khóa màu (theo chuẩn OOXML)

| Khóa | Vai trò | Dùng cho |
|---|---|---|
| `dk1` | Text chính | Chữ body trên nền sáng |
| `lt1` | Nền chính | Background trang/slide |
| `dk2` | Text phụ | Chữ phụ, caption, subtitle |
| `lt2` | Nền phụ nhạt | Callout box, zebra row, header nhạt |
| `accent1` | Màu chủ đạo brand | Heading 1, header bảng, nút chính |
| `accent2` | Màu nhấn phụ | Heading 2, đường viền, điểm nhấn |
| `accent3`–`accent6` | Màu bổ trợ | Series biểu đồ, traffic light |

**Lưu ý:** `assets.logo` có thể vắng mặt (file mẫu không có ảnh). Generator phải kiểm tra tồn tại trước khi nhúng.

**Cách script chọn màu (đã tự động hóa, không cần grep tay):**
1. Đếm màu THỰC SỰ dùng trong nội dung: `a:srgbClr` (slide, shape, chart), `w:color` / `w:shd` trong `document.xml` và các style Word ĐƯỢC THAM CHIẾU, `<color rgb>` trong Excel. Màu bão hòa dùng nhiều nhất → `accent1`, kế tiếp → `accent2`...; xám tối → `dk1`/`dk2`; nền nhạt → `lt2`.
2. `theme1.xml` chỉ lấp chỗ trống. Theme mặc định của Office (accent 4472C4, 4F81BD, 156082...) không bao giờ được coi là màu brand.
3. Mỗi màu có ghi nguồn trong khóa `_sources` của `brand_kit.json`; script in bảng màu kèm nguồn ra màn hình.

**Mã thoát:** `0` = có màu brand thật; `3` = file chỉ có theme mặc định hoặc không có màu nhấn (KHÔNG dùng kit này: hỏi người dùng mã màu/logo hoặc đề xuất preset); `2` = lỗi file/không phải tệp Office; `4` = thiếu LibreOffice. `format_docx.py --brand-kit` và `template_docx.js` từ chối kit thiếu màu bắt buộc.

Sau khi bóc: mở file mẫu (render PNG) và so màu bằng mắt với bảng màu script in ra trước khi generate.

---

## 3. Bóc tách Tài nguyên Vật lý (Assets)

- **Hình ảnh:** `extract_brand.py` tự trích toàn bộ ảnh từ `word/media/` hoặc `ppt/media/` vào `assets/`. Sau khi chạy, Agent xem thư mục `assets/` và tự nhận diện file nào là logo, cập nhật lại `assets.logo` trong JSON nếu script chọn sai.
- **Sơ đồ/Biểu đồ:** Không copy XML chết. Cào Data thô (con số, chữ) trong sơ đồ và ghi nhận loại biểu đồ (Bar, Pie, Phân cấp). Đưa Data này sang Chiều Ghi để dùng Node.js vẽ lại.

---

## 4. Bóc tách Content (Text, Bảng, Số liệu)

Mọi tệp người dùng (DOCX/DOC/ODT/RTF, XLSX/XLS/ODS/CSV, PPTX/PPT/ODP, PDF, EPUB, HTML, ảnh) → chạy bộ chuyển đổi dùng chung **từ gốc repo**, không đọc thẳng tệp nhị phân:

```bash
.venv/bin/python scripts/doc_ingest.py "<tệp>" --out <process_dir>/ingest --json
```

Đọc `<process_dir>/ingest/source.md` (bảng `|...|`; PDF `<!-- page N -->`; PPTX `## Slide N`; XLSX `## Sheet i: tên` + bảng công thức) và `manifest.json`. Mã thoát: `0` đủ | `3` có trang scan → đọc ảnh `ocr_pages/*.png` bằng thị giác (nháp OCR chưa kiểm chứng) | `2` hỏi người dùng theo `manifest.message` (mật khẩu/hỏng) | `4` cài theo `manifest.message` (`bash scripts/auto-setup.sh`).

| Cần lấy | Công cụ |
|---|---|
| Text thô toàn văn (mọi định dạng) | `doc_ingest.py` như trên → `source.md` |
| Cấu trúc chính xác (style, run) | Unpack XML rồi đọc `document.xml` |
| Số liệu + công thức Excel | `openpyxl` với `data_only=False` để giữ công thức |
| Bảng trong PDF digital | `pdfplumber` |
