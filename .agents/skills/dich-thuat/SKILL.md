---
name: dich-thuat
display-name: Dịch Thuật
description: >-
  Dịch tài liệu PDF (VI - EN - JA) với 2 chế độ trên cùng một engine: PRESERVE giữ nguyên bố cục 1:1 (số trang, ảnh, con dấu SMask trong suốt, khung hoa văn, biểu đồ đa phần tử) và RECONSTRUCT tái dựng tài liệu bằng reflow tự nhiên (Document IR, bảng, công thức, biểu đồ, sơ đồ). Có domain review thuật ngữ, dịch 2 lượt không sót và cổng kiểm định tự động.
  USE WHEN: Người dùng cần dịch file PDF có lớp chữ mà kết quả phải là PDF: giữ nguyên bố cục gốc (chứng chỉ, công văn có dấu, bằng khen, chuyên khảo 2 cột) hoặc dàn trang lại cho dễ đọc (báo cáo, kỷ yếu, tài liệu kỹ thuật có bảng/công thức/biểu đồ).
  DO NOT USE WHEN: Dịch Word/Text/Markdown/EPUB hoặc cần bản song ngữ/tam ngữ DOCX (dùng 'ejv-translate'), PDF scan không có lớp chữ cần OCR trước (dùng 'boc-tach-pdf'), hoặc chỉ dịch phụ đề video (dùng 'phu-de').
trigger: Dịch thuật PDF, dịch giữ định dạng, Retain-PDF, dịch PDF giữ nguyên bố cục, dịch tái cấu trúc, dịch PDF reflow, tái dựng tài liệu dịch, dịch chứng chỉ có con dấu, dịch tài liệu có bảng công thức biểu đồ
category: docs
needs_file: false
file_filter: pdf
---

# Kỹ Năng Dịch Thuật PDF (dich-thuat v1.0)
## Một engine, hai chế độ: PRESERVE (1:1) và RECONSTRUCT (reflow)

> Hợp nhất từ hai skill cũ `dich-giu-dinh-dang` (→ chế độ **preserve**) và `document-reconstruction-translator`
> (→ chế độ **reconstruct**), vốn dùng chung ~20 file engine giống hệt nhau (Luật R7).

<goal>
Dịch tài liệu PDF nguồn sang `vi` / `en` / `ja`, dịch đủ 100% nội dung (0 khối chữ nguồn sót, Luật R3 §8), thuật ngữ
chuyên ngành chuẩn xác (Luật R6 trụ cột 6) và bàn giao PDF đạt cổng kiểm định của chế độ đã chọn.
</goal>

> [!CAUTION]
> **ZERO EXTERNAL API:** toàn bộ phân tích, dịch thuật và quyết định cấu trúc do chính Agent trong IDE thực hiện; scripts
> chỉ xử lý dữ liệu cục bộ (PyMuPDF, Typst). Không gọi REST API LLM, không yêu cầu API key. Skill tự chạy liên tục
> (Autonomous Full-Run) đến khi đạt cổng kiểm định, không dừng giữa chừng để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

| Placeholder | Giá trị |
|---|---|
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |
| `<process_dir>` | `<workspace>/_process/dich_thuat_[stem]/` (đã gitignore) |
| `$S` | `.agents/skills/dich-thuat/scripts` |
| `$P` | `.agents/skills/_shared/pdf` (engine PDF dùng chung — Luật R7) |

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):** PDF thành phẩm và báo cáo chỉ ghi vào `<output_dir>`; file tạm (assets, JSON,
> bản nháp, ảnh so sánh) chỉ ghi vào `<process_dir>`. Không ghi gì vào thư mục gốc repo.

---

## 🏗️ Bước 0 — Intake & chọn chế độ (Tọa độ đầu vào)

| Trục | Giá trị | Mặc định |
|---|---|---|
| File PDF nguồn | đường dẫn `.pdf` có lớp chữ | hỏi người dùng |
| Ngôn ngữ nguồn → đích | `ja` / `en` / `vi` → `vi` / `en` / `ja` | tự nhận diện → `vi` |
| Chế độ | `preserve` / `reconstruct` | theo bảng dưới |
| Thư mục xuất | đường dẫn | `~/Downloads/AIWF_Output/` |

**Bảng chọn chế độ** (người dùng nói rõ thì theo người dùng):

| Dấu hiệu tài liệu / yêu cầu | Chế độ |
|---|---|
| Chứng chỉ, bằng khen, công văn có con dấu/chữ ký, khung hoa văn; "giữ nguyên bố cục", "giống bản gốc", cần đối chiếu từng trang | **preserve** |
| Chuyên khảo 2 cột, biểu đồ kiểm soát đa phần tử mà phải giữ đúng vị trí | **preserve** |
| Báo cáo, kỷ yếu, tài liệu kỹ thuật dài, nhiều bảng/công thức/sơ đồ; "dễ đọc", "dàn lại trang", chấp nhận đổi số trang | **reconstruct** |
| Bản dịch tiếng Việt dài hơn nhiều, preserve làm chữ quá nhỏ (< 7 pt) hoặc mất cấu trúc | chuyển **reconstruct** và báo người dùng |
| Reconstruct làm mất cấu trúc quan trọng (tiêu đề dính đoạn, bảng thành đoạn liền) | chuyển **preserve** và báo người dùng |

**Kiểm tra trước (tự động trong cả hai CLI) — exit 2 = tệp bị từ chối, đọc thông báo `⛔`:**
- Không phải PDF thật (DOCX/PPTX/ảnh đổi đuôi) → `soffice --headless --convert-to pdf` (đặt đúng đuôi gốc trước) rồi chạy lại, hoặc dùng `ejv-translate`.
- PDF có mật khẩu → hỏi bản không mật khẩu; KHÔNG đoán mật khẩu.
- PDF scan / phần lớn trang không có lớp chữ → dùng `boc-tach-pdf` để OCR trước.
- Cảnh báo `DẤU TIẾNG VIỆT BỊ VỠ` → dịch theo ảnh trang đó và báo người dùng.
- 0 khối được dịch không bao giờ là "xong": CLI thoát khác 0.

---

<instructions>
## QUY TRÌNH THỰC THI (SOP AUTONOMOUS FULL-RUN)

### GIAI ĐOẠN 1 — Trích xuất đồ họa & cấu trúc (chung)
```bash
python3 $P/pdf_asset_extractor.py --pdf "<pdf>" --extract-all --output-dir "<process_dir>/assets/"
```
Giải mã mặt nạ mềm SMask (con dấu, chữ ký trong suốt), bao trọn biểu đồ đa phần tử (Luật R6 trụ cột 1–2).

### GIAI ĐOẠN 2 — Domain review & ma trận thuật ngữ (chung, bắt buộc)
1. Xác định chuyên ngành hẹp (thận học - lọc máu, kế toán - thuế, ISO/JIS, SHTT…).
2. Lập `<process_dir>/domain_matrix.json`: thuật ngữ nguồn → bản dịch chuẩn theo quy chuẩn cơ quan quản lý.
3. Cấm dịch từng chữ (vd. `血液浄化` = "kỹ thuật lọc máu ngoài cơ thể", không phải "làm sạch máu";
   `維持透析患者` = "bệnh nhân lọc máu chu kỳ").

### GIAI ĐOẠN 3 — Dịch 2 lượt theo danh sách engine yêu cầu

**Chế độ preserve** (Typst overlay, giữ trang 1:1):
```bash
python3 $S/typst_overlay.py --pdf "<pdf>" --blocks "<process_dir>/merged_ejv.json" --lang vi --output "<process_dir>/draft.pdf"
```
- Lượt 1: `merged_ejv.json` có thể là `[]` → exit 3 + `<process_dir>/draft.pdf.missing.json` = danh sách ĐÚNG từng chuỗi nguồn
  engine cần (`{"ja": "...", "vn": ""}`).
- Agent dịch từng mục theo ma trận thuật ngữ, điền `vn` (hoặc `en`/`ja`), nối vào `merged_ejv.json` (khoá `ja` nguồn + đích).
- Lượt 2: chạy lại đúng lệnh; lặp tới exit 0 và KHÔNG còn `.missing.json`.
- Tiếng Việt dài hơn 25–35 %: engine tự co chữ theo khung, câu quá dài sẽ nhỏ chữ → dịch gọn.
- `--mode auto|flow|spatial` (mặc định `auto`) chọn cách đặt chữ trong trang; không đổi số trang.

**Chế độ reconstruct** (Document IR + reflow):
```bash
python3 $S/pipeline/document_pipeline.py --source "<pdf>" --source-lang ja --target-lang vi --process-dir "<process_dir>" --output-dir "<output_dir>"
```
- Lần 1 → exit 3 `AWAITING_AGENT_TRANSLATION`: đọc `<process_dir>/agent-translation-prompt.md` + `translation-plan.json`,
  dịch MỌI unit, ghi `<process_dir>/agent-translations.json` dạng `{"<id>": "<bản dịch>"}`, chạy lại đúng lệnh.
- Một câu có thể bị cắt thành 2 unit liền nhau: dịch sao cho hai mảnh nối lại thành câu đúng.
- PDF chỉ được giao vào `<output_dir>` khi `validation/translation.json` đạt (`--allow-draft` chỉ để xem nháp).
- Renderer router: bảng → Typst dynamic table; công thức → Typst/LaTeX math; biểu đồ/sơ đồ → vẽ lại khi độ tin cậy ≥ 0.85,
  ngược lại giữ ảnh gốc + dịch chú thích; ảnh chụp/minh họa → giữ nguyên, không AI-regenerate.

### GIAI ĐOẠN 4 — Nhìn bằng mắt (bắt buộc, cả hai chế độ)
```bash
python3 -c "import pymupdf as f; [f.open(p)[i].get_pixmap(dpi=70).save(f'<process_dir>/cmp_{k}_{i}.png') for k,p in enumerate(['<pdf>','<ban_dich.pdf>']) for i in range(min(3, f.open(p).page_count))]"
```
Mở ảnh: còn chữ gốc? tiêu đề/danh sách/bảng đúng dạng? chữ tràn khung, đè hình, đè hoa văn?

### GIAI ĐOẠN 5 — Cổng kiểm định tự động

| Lớp | Lệnh | Preserve | Reconstruct |
|---|---|---|---|
| Bố cục 1:1 | `python3 $P/verify_layout_parity.py "<ban_dich.pdf>" --source "<pdf>"` | Bắt buộc PASS | Bỏ qua |
| Sót chữ nguồn + điểm giữ định dạng | `python3 $P/verify_retention.py --source "<pdf>" --target "<ban_dich.pdf>" --json-output "<process_dir>/retention.json"` | 0 khối sót, điểm ≥ 95 | 0 khối sót (điểm bố cục chỉ tham khảo) |
| Kiểm định dàn trang tích hợp | `document_pipeline.py` tự chạy (Content/Structure/Visual/Semantic) → `<output_dir>/validation-report.json` + `<process_dir>/validation/translation.json` | Không áp dụng | Bắt buộc đạt |
| Nội dung & thuật ngữ | Agent rà: 0 placeholder `.`, 0 câu cụt, 100 % khớp `domain_matrix.json`, số liệu/đơn vị giữ nguyên | Bắt buộc | Bắt buộc |

Chưa đạt → sửa bản dịch / đổi chế độ / chạy lại. Không bao giờ báo hoàn thành khi còn ≥ 1 khối chữ nguồn.

### GIAI ĐOẠN 6 — Xuất bản
- Preserve: `cp "<process_dir>/draft.pdf" "<output_dir>/<tên>_dich_giu_bo_cuc_<lang>.pdf"`.
- Reconstruct: pipeline đã ghi `<tên>_translated_reconstructed.pdf` + `validation-report.json`, `reconstruction-report.json`,
  `source-map.json` vào `<output_dir>`.
</instructions>

---

## 🔗 Engine dùng chung (Luật R7)

| Engine | Vị trí | Ghi chú |
|---|---|---|
| `pdf.asset_extractor` | `_shared/pdf/pdf_asset_extractor.py` | SMask, ảnh 300 DPI |
| `pdf.verify_retention` | `_shared/pdf/verify_retention.py` | Sót chữ nguồn (ja/zh/en tự nhận diện), điểm giữ định dạng |
| `pdf.verify_layout_parity` | `_shared/pdf/verify_layout_parity.py` | Đối chiếu số trang, ảnh, ngân sách dòng |
| `pdf.verify_coordinates` | `_shared/pdf/verify_coordinates.py` | Chồng chữ, cắt chữ, tràn viền (được verify_retention gọi) |
| `docio.ingest` | `_shared/doc_ingest_bridge.py` | Kiểm tra trước tệp đầu vào |

Engine dàn trang (`analyzer/`, `layout/`, `render/`, `pipeline/`, `engines/`, `ir/`, `translation/`, `validation/`,
`typst_overlay.py`) chỉ tồn tại trong skill này. Skill khác cần → promote vào `_shared/` theo Luật R7, không chép file.

---

<constraints>
## SÁU ĐIỀU CẤM TUYỆT ĐỐI
1. ❌ Đòi external API key hoặc gọi LLM API ngoài.
2. ❌ Preserve: làm lệch số trang so với bản gốc; làm đen nền con dấu; đè chữ lên khung hoa văn (Safe Zone ≥ 15–20 pt).
3. ❌ Reconstruct: co chữ thân bài < 9 pt (chú thích < 7 pt) để ép vừa hộp; AI-regenerate ảnh chụp; bịa số liệu biểu đồ/công thức.
4. ❌ Placeholder `.` hoặc bỏ sót dòng/ô bảng (ánh xạ kép: cấp đoạn gộp + cấp dòng đơn).
5. ❌ Dịch máy thô từng chữ làm sai thuật ngữ chuyên ngành.
6. ❌ Ghi thành phẩm vào repo Git.
</constraints>

<working_ledger>
## LƯU VẾT TIẾN TRÌNH (`<process_dir>`)
`assets/`, `domain_matrix.json`, `merged_ejv.json` (preserve) hoặc `translation-plan.json` + `agent-translations.json` +
`document-ir.json` (reconstruct), `draft.pdf`, `cmp_*.png`, `retention.json`.
</working_ledger>

<quality_gate>
## CHECKLIST QUALITY GATE
1. ✅ Đã chọn chế độ theo bảng Bước 0 và ghi lý do trong báo cáo.
2. ✅ `domain_matrix.json` đã lập; 100 % thuật ngữ trong bản dịch khớp ma trận.
3. ✅ `verify_retention.py`: **0 khối chữ nguồn sót** (Luật R3 §8).
4. ✅ Preserve: `verify_layout_parity.py` PASS, số trang 1:1, con dấu trong suốt, điểm retention ≥ 95.
5. ✅ Reconstruct: `validation/translation.json` và `validation-report.json` đạt, chữ thân bài ≥ 9 pt.
6. ✅ Đã mở ảnh so sánh trang gốc/trang dịch (Giai đoạn 4).
7. ✅ Đoạn mờ / độ tin cậy thấp có cờ `[CẦN XÁC MINH: <lý do>]`, kèm bằng chứng (ảnh trang).
8. ✅ Khử dấu vết AI trong tiếng Việt: không em dash `—`, không Oxford comma `, và`.
</quality_gate>

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (Clean Delivery)
Khung chat chỉ tóm tắt: tên tài liệu, ngôn ngữ, chế độ + lý do, số trang (gốc → dịch), chuyên ngành đã thẩm định,
kết quả các lớp kiểm định (0 khối sót, parity/mode verifier), các điểm `[CẦN XÁC MINH]`, và link tuyệt đối tới PDF +
báo cáo trong `<output_dir>`. Không dán log terminal dài.
</delivery_protocol>

---

## CLI CONTRACT
> Dùng contract này trước; chỉ đọc mã nguồn khi lệnh lỗi cần debug hoặc cần sửa script.

| Script | Cú pháp | Exit |
|---|---|---|
| `$S/typst_overlay.py` | `--pdf <pdf> --blocks <merged_ejv.json> --lang vi\|en\|ja --output <pdf> [--mode auto\|flow\|spatial] [--allow-missing] [--skip-preflight]` | 0 xong · 2 từ chối tệp · 3 còn chuỗi cần dịch (`.missing.json`) |
| `$S/pipeline/document_pipeline.py` | `--source <pdf> --source-lang ja --target-lang vi --process-dir <dir> --output-dir <dir> [--allow-draft] [--skip-preflight]` | 0 xong · 1 kiểm định chưa đạt · 2 từ chối tệp · 3 chờ agent dịch |
| `$P/pdf_asset_extractor.py` | `--pdf <pdf> (--extract-all \| --page N) --output-dir <dir>` | 0 / ≠0 |
| `$P/verify_retention.py` | `--source <pdf> --target <pdf> [--source-lang auto\|ja\|en\|zh] [--json-output f] [--output report.md] [--min-score 85]` | 0 PASS · 1 FAIL / còn sót chữ nguồn |
| `$P/verify_layout_parity.py` | `<ban_dich.pdf> --source <pdf>` | 0 PASS · 1 FAIL |

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `doc_ingest_bridge` | Gọi doc_ingest từ Python: `pdf_preflight` (lớp chữ, dấu tiếng Việt) | import trong `scripts/pipeline/document_pipeline.py, scripts/typst_overlay.py` |
| `pdf.asset_extractor` | Trích ảnh giữ SMask, con dấu, khung hoa văn | `python3 .agents/skills/_shared/pdf/pdf_asset_extractor.py` |
| `pdf.verify_retention` | Cổng dịch sót ký tự nguồn (R3 §8) | `python3 .agents/skills/_shared/pdf/verify_retention.py` |
| `pdf.verify_layout_parity` | So khớp bố cục bản dịch ↔ bản gốc | `python3 .agents/skills/_shared/pdf/verify_layout_parity.py` |
| `pdf.verify_coordinates` | Chồng chữ, tràn lề, va chạm khung | `python3 .agents/skills/_shared/pdf/verify_coordinates.py` |
