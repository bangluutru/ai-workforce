# Thiết kế: `_shared/docx/inspect_docx.py`

Trạng thái: bước 1 đến 4 đã làm (module, `--rules`, đăng ký engine, `--pages` + gộp soffice); bước 5 (gắn vào skill) đang làm. Nguồn cảm hứng: `inspect_document` / `get_text` của WordCraft
(storytold/wordcraft, `docs/mcp.md`), đọc từ tài liệu, chưa đọc mã Rust.

## 1. Vấn đề

Hiện chỉ có `check_nd30.py` đọc cấu trúc DOCX, và nó chỉ kiểm các luật cố định của NĐ 30. Skill nào sinh DOCX
khác (`tu-van-phap-luat`, `viet-bai`, `dich-thuat`, chuẩn doanh nghiệp của `xu-ly-van-phong`) chỉ có hai cách
kiểm: render PNG rồi nhìn, hoặc không kiểm. `doc_ingest` (markitdown) làm mất định dạng nên không thay được.
Cần một bước "đọc ngược" có cấu trúc, rẻ và lặp lại được, để agent và test tự khẳng định (assert) trên đó.

Phát hiện phụ khi khảo sát (cần xử lý riêng, ngoài phạm vi file này):
- Hàm `run_font`, `run_size`, `all_paragraphs` nằm trong `check_nd30.py` nhưng sẽ cần ở nhiều nơi (R7).
- Có hai bộ tìm LibreOffice trùng chức năng: `bao-cao-kt/scripts/office_utils.py` và
  `xu-ly-van-phong/scripts/extractor/office/soffice.py`.
- `output_manager.py` chỉ chọn thư mục, không có ghi nguyên tử; theo `ENGINES.md` chưa skill nào dùng.
  `docs/harness/AIWF_HARNESS_AUDIT.md` có nhắc nó, chưa kiểm tra nội dung.

## 2. Phạm vi

Làm: đọc DOCX, xuất JSON mô tả cấu trúc, kiểm theo bộ luật khai báo (tùy chọn).
Không làm: sửa file, sinh file, thay `check_nd30`, kiểm luật miền (thuế, pháp lý), OCR.

## 3. Vị trí và gọi

- Module: `.agents/skills/_shared/docx/inspect_docx.py` (cạnh `legal_report.py`; thư mục này không phải gói
  Python nên import dạng `from inspect_docx import inspect_docx`).
- Đăng ký `engines.json` id `docx.inspect`, thêm dòng vào `ENGINES.md`, `signatures` là `def inspect_docx(`.
- CLI:

```
python3 .agents/skills/_shared/docx/inspect_docx.py FILE.docx
    [--json OUT.json]        # mặc định in tóm tắt ra stdout
    [--text]                 # in văn bản thuần theo thứ tự đọc (tương đương get_text)
    [--rules RULES.json]     # kiểm theo luật khai báo, xem mục 6
    [--pages]                # thêm số trang thật (cần LibreOffice, xem mục 7)
```

Mã thoát: `0` đạt/chỉ mô tả · `1` vi phạm luật trong `--rules` · `2` đầu vào không đọc được (không phải DOCX,
hỏng, có mật khẩu) · `4` thiếu phụ thuộc. Cùng quy ước với `doc_ingest.py` và `verify_report.py`.

## 4. Nguyên tắc lỗi (học từ SoundCraft/GridCraft)

- Lỗi là giá trị, không phải sập: phần nào đọc hỏng thì ghi vào `warnings[]` và vẫn trả phần còn lại.
- Không sửa file đầu vào. Không ghi gì ngoài `--json`.
- Thông báo lỗi nói rõ phải làm gì tiếp (vd "file có mật khẩu: hỏi người dùng", đúng tinh thần mã 2 của doc_ingest).

## 5. Lược đồ JSON (`schema: "aiwf.docx.inspect/1"`)

```
{
  "schema": "aiwf.docx.inspect/1",
  "file": {"path", "size", "sha256", "generator": "<app.xml Application>", "core": {title, author, created, modified}},
  "sections": [{"page_mm": [w,h], "orientation", "margins_mm": {top,bottom,left,right},
                "columns": n, "header_text", "footer_text", "has_page_number_field": bool}],
  "blocks": [                                  // theo thứ tự đọc, gồm cả đoạn trong bảng
    {"i": 0, "kind": "paragraph", "style": "Heading 1", "outline": 1,
     "align": "center", "text": "...", "list": {"numId": 3, "ilvl": 0} | null,
     "page_break_before": false, "keep_next": false,
     "runs": [{"text", "font", "size_pt", "bold", "italic", "color", "highlight"}]},
    {"i": 1, "kind": "table", "rows": r, "cols": c, "merged": n, "header_row": bool,
     "col_widths_mm": [...], "cells": [[{"text", "span", "vmerge"}]]}
  ],
  "images": [{"block": i, "name", "px": [w,h], "placed_mm": [w,h], "effective_dpi", "alt": "..." | null}],
  "fields": {"toc": bool, "page": n, "numpages": n, "other": [...]},
  "review": {"tracked_insertions": n, "tracked_deletions": n, "comments": n, "footnotes": n},
  "hyperlinks": [{"text", "target"}],
  "fonts_used": {"Times New Roman": 412, ...},          // theo số ký tự, đã phân giải kế thừa
  "findings": {
    "placeholders": [{"block", "match"}],               // {{..}}, [TODO], XXX, Lorem, ###, "[CẦN XÁC MINH]"
    "empty_paragraph_runs": [{"start": i, "count": n}], // chuỗi đoạn trống liên tiếp (dùng Enter để căn chỗ)
    "heading_gaps": [{"block", "from": 1, "to": 3}],    // nhảy cấp tiêu đề
    "em_dash": [block, ...],
    "nfd_text": [block, ...],                           // chữ tiếng Việt dạng tổ hợp (NFD), dễ vỡ dấu
    "missing_alt": [block, ...]
  },
  "stats": {"paragraphs", "words", "tables", "images"},
  "pages": null | {"count": n, "text": ["trang 1...", "..."]},   // chỉ khi --pages
  "warnings": ["..."]
}
```

Cố ý chỉ đọc, không suy diễn. Mọi "findings" là phát hiện cơ học (regex, đếm), không phải phán xét chất lượng.

## 6. Luật khai báo `--rules`

Mỗi skill tự cấp một file JSON nhỏ, vd `xu-ly-van-phong/standards/doc_enterprise.rules.json`:

```
{
  "fonts_allowed": ["Be Vietnam Pro", "Spectral"],
  "page_mm": [210, 297],
  "margins_mm": {"top": [15, 25], "bottom": [15, 25], "left": [15, 30], "right": [15, 25]},
  "no_placeholders": true,
  "max_consecutive_empty_paragraphs": 1,
  "heading_no_skip": true,
  "min_image_dpi": 150,
  "require_alt_text": false,
  "forbid": ["em_dash", "nfd_text"],
  "pages": {"max": 12}
}
```

Mỗi vi phạm in một dòng `RULE <tên>: <vị trí>: <mô tả>`, mã thoát 1. Luật không biết thì báo lỗi mã 2
(không bỏ qua lặng lẽ). `check_nd30.py` giữ nguyên vai trò luật chuyên biệt; phần kiểm lề/font chung của nó
có thể về sau chuyển sang rules, không làm ở bước đầu.

## 7. Số trang thật (`--pages`)

DOCX không lưu số trang đáng tin. Chỉ khi có `--pages`: render PDF bằng LibreOffice rồi đọc bằng PyMuPDF
(`pymupdf` đã có trong `requirements.txt` qua pdfplumber/pymupdf; LibreOffice đã cài ở máy này, tìm qua bộ tìm
hiện có). Thiếu LibreOffice: bỏ qua phần `pages`, ghi `warnings`, không đổi mã thoát trừ khi luật có `pages`
(khi đó mã 2, "không xác minh được", khác với mã 1 "xác minh và hỏng").
Điều kiện tiên quyết: gộp hai bộ tìm soffice vào `_shared/office/soffice.py` (việc riêng, theo R7).

## 8. Cách đọc (python-docx 1.2.0 đã có trong `.venv`)

- Duyệt thân tài liệu theo thứ tự XML (`doc.element.body`) để giữ thứ tự đọc giữa đoạn và bảng
  (`doc.paragraphs` rồi `doc.tables` như trong `all_paragraphs` hiện tại làm mất thứ tự).
- Phân giải font/cỡ chữ theo chuỗi: run, style đoạn, style gốc, `docDefaults`, theme. Hàm `run_font` hiện có
  dừng ở style `Normal` và bỏ qua `docDefaults` và font theme; phải bổ sung, nếu không sẽ báo sai font.
- Bảng: đọc `w:gridSpan`, `w:vMerge` trực tiếp từ XML; python-docx lặp lại ô gộp nên phải khử trùng bằng `id(cell._tc)`.
- Bản ghi sửa đổi, ghi chú cuối trang, bình luận: đếm trực tiếp trong XML (`w:ins`, `w:del`, các part `footnotes.xml`,
  `comments.xml`).
- Ảnh: kích thước đặt lấy từ `wp:extent` (EMU), px từ Pillow; dpi hiệu dụng = px / inch đặt.
- Chuẩn hóa NFC khi so khớp, đồng thời ghi nhận đoạn đang ở NFD.

## 9. Kiểm thử (`tests/test_inspect_docx.py`)

Dựng DOCX trong test bằng python-docx rồi sửa XML khi cần, thêm `tests/fixtures/doc_ingest/sample.docx` có sẵn:
1. Đoạn, bảng, ảnh, tiêu đề: thứ tự và số lượng đúng, bảng nằm đúng giữa hai đoạn.
2. Font kế thừa từ style và từ `docDefaults`: ra đúng tên font.
3. Bảng có `gridSpan`/`vMerge`: ô không bị đếm trùng.
4. Placeholder, chuỗi đoạn trống, nhảy cấp tiêu đề, em dash, NFD: mỗi loại một ca.
5. Tracked change và comment chèn tay vào XML: đếm đúng.
6. Tệp không phải zip, zip thiếu `word/document.xml`, DOCX có mật khẩu: mã thoát 2, không có traceback.
7. `--rules` đạt (0), vi phạm (1), luật lạ (2).
8. Trường hợp thiếu LibreOffice với `--pages`: có cảnh báo, không đổ vỡ (giả lập bằng `SOFFICE=/không/tồn/tại`).

## 10. Tích hợp vào skill (bước sau, sau khi module xong)

| Skill | Dùng ở đâu |
|---|---|
| xu-ly-van-phong | Chuẩn [2] (doanh nghiệp): chạy sau khi sinh, kiểm theo rules; Track soát file người dùng gửi |
| tu-van-phap-luat(-nhat-ban) | Sau `legal_report.py`: không placeholder, không đoạn trống thừa, đúng font |
| dich-thuat, ejv-translate | DOCX đầu ra: khẳng định đủ số bảng/ảnh so với nguồn (so hai file JSON) |
| viet-bai | Đầu ra DOCX: tiêu đề liền cấp, không sót placeholder |

Mỗi SKILL.md thêm đúng một bước "Bước kiểm cấu trúc" và mục `Engine dùng chung (R7)`; chưa sửa skill nào cho đến khi module có test xanh.

## 11. Rủi ro

- Đã quan sát thật: khi máy thiếu font của tài liệu (vd Cambria, font mặc định của python-docx), LibreOffice thay font và
  dấu tiếng Việt bị tách thành dòng lẻ khi trích chữ từng trang. `--pages` có cảnh báo cho trường hợp này; số trang
  cũng là số của LibreOffice, có thể lệch Word.

- Phân giải style của Word phức tạp (theme, docDefaults, style liên kết). Bản đầu có thể sai ở ca hiếm; vì vậy
  `fonts_used` ghi nguồn phân giải để dễ truy lỗi.
- Luật `--rules` dễ phình. Giữ danh sách luật nhỏ, thêm khi có skill thật sự cần.
- Chưa xác minh `agent_eval` L2 có gọi bộ kiểm DOCX nào không; đọc `scripts/eval_transcript.py` trước khi gắn vào đó.

## 12. Thứ tự làm

1. Module lõi + `--text` + JSON + test 1 đến 6 (không cần LibreOffice).
2. `--rules` + test 7.
3. Đăng ký `engines.json`/`ENGINES.md`, chạy `scripts/check_shared_reuse.py`.
4. Gộp soffice vào `_shared/office/`, rồi bật `--pages` + test 8.
5. Gắn vào từng skill, mỗi skill một commit.
