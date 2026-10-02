# Chuyển đổi Tài liệu (Convert)

Pipeline chuyển đổi giữa các định dạng.

---

## MD → DOCX (Pandoc + Format)

```powershell
# Bước 1: Pandoc convert
pandoc input.md -o output.docx --markdown-headings=atx -f markdown+raw_attribute --wrap=none

# Bước 2: Post-process theo khung mặc định. BẮT BUỘC chọn chế độ màu:
python3 scripts/extractor/format/format_docx.py output.docx --mono                      # đen trắng (mặc định)
python3 scripts/extractor/format/format_docx.py output.docx --brand-kit <brand_kit.json>  # đắp màu brand
```

### Nhiều file MD (xuất bản sách)

```powershell
$files = Get-ChildItem "chapters\*.md" | Sort-Object Name
$merged = ($files | ForEach-Object { Get-Content $_ -Raw -Encoding UTF8 }) -join "`n`n"
$merged | Out-File "_merged.md" -Encoding UTF8
pandoc _merged.md -o output.docx
python3 scripts/extractor/format/format_docx.py output.docx --mono
```

**Lưu ý:** văn bản hành chính NĐ 30 KHÔNG đi đường Pandoc, dùng `scripts/generator/nd30_docx.py`. Tài liệu Track 2 cần bìa, callout, bảng màu thì ưu tiên Generator Node.js (`template_docx.js`); Pandoc + `format_docx.py --brand-kit` chỉ hợp tài liệu dạng văn bản liền mạch.

---

## PDF → DOCX

| Loại | Cách làm |
|---|---|
| PDF digital | `python scripts/extractor/convert/convert_pdf_to_docx.py input.pdf output.docx` |
| PDF scan | AI Vision phân tích → tái tạo bằng Generator. Xem `pdf.md` |

---

## DOCX → PDF

```powershell
python3 scripts/extractor/office/soffice.py --headless --convert-to pdf --outdir <thư_mục> input.docx
```

---

## Dependencies

```
pip install -r requirements.txt   # gồm python-docx, defusedxml (validate.py)
pip install pdf2docx              # chỉ khi cần PDF -> DOCX
# pandoc: macOS `brew install pandoc`, Windows `winget install pandoc`
# LibreOffice: macOS `brew install --cask libreoffice`
```
