---
name: document-reconstruction-translator
display-name: Dịch Tái Dựng Cấu Trúc
description: >-
  Dịch thuật tài liệu PDF chuyên sâu kết hợp tái cấu trúc thông minh (Document Reconstruction with Translation). Hiểu cấu trúc tài liệu, dịch nội dung và tái dựng tài liệu hoàn chỉnh với bố cục hợp lý nhất, giữ nguyên ý nghĩa, quan hệ cấu trúc, reflow tự nhiên, không bị ép giữ nguyên số dòng hay hộp chữ của PDF gốc.
  USE WHEN: Người dùng cần dịch file PDF và tái cấu trúc/tái dàn trang thông minh (báo cáo, kỷ yếu, tài liệu kỹ thuật có bảng, công thức, biểu đồ/diagram) yêu cầu reflow tự nhiên, typography chuẩn mực, không chấp nhận đè chữ hay shrink font cực nhỏ.
  DO NOT USE WHEN: Cần giữ nguyên 100% bố cục hình học vật lý 1:1 từng milimet, con dấu pháp nhân, bằng khen khung hoa văn giữ nguyên trang gốc (dùng 'dich-giu-dinh-dang'), hoặc dịch văn bản Word (.docx) thông thường (dùng 'ejv-translate').
trigger: Dịch tái cấu trúc, Document Reconstruction Translator, tái dàn trang tài liệu dịch, dịch PDF reflow, tái dựng cấu trúc tài liệu dịch
category: docs
needs_file: true
file_filter: pdf
---

# Kỹ Năng Dịch Tái Dựng Cấu Trúc (Document Reconstruction Translator v1.0)
## Chuẩn Kiến Trúc Tái Cấu Trúc Ngữ Nghĩa & Dàn Trang Đa Kênh

<goal>
Thực hiện quy trình dịch thuật và tái dựng tài liệu (Document Reconstruction with Translation) từ file PDF nguồn sang ngôn ngữ đích (Tiếng Việt, Tiếng Anh, Tiếng Nhật):
1. **Document Structure Analysis**: Phân tích cấu trúc tài liệu theo 3 cấp (Document -> Page -> Region/Object) và nhận diện chính xác 16 nhóm ngữ nghĩa (TEXT, HEADING, CAPTION, FOOTNOTE, TABLE, FORMULA, CHART, DIAGRAM, PHOTO, ILLUSTRATION, VECTOR_GRAPHIC, LIST, HEADER, FOOTER, PAGE_NUMBER, OTHER).
2. **Document Intermediate Representation (Document IR)**: Tách bạch tuyệt đối giữa nội dung ngữ nghĩa (content) và hình thức hiển thị (presentation). Lưu trữ quan hệ ngữ nghĩa, thứ tự đọc, liên kết caption <-> figure/table, không coi bounding box là ràng buộc tuyệt đối.
3. **Chiến lược chuyên biệt theo từng loại đối tượng**:
   - TEXT: Reflow tự nhiên, typography phân cấp, không shrink font cực nhỏ, ngắt trang tự nhiên.
   - FORMULA: Nhận diện cấu trúc, ưu tiên LaTeX / vector rendering, giữ nguyên khi confidence thấp.
   - TABLE: Khôi phục cấu trúc bảng (rows, cols, merged cells), dịch từng cell, tự do thay đổi kích thước cột/dòng, cho phép chia trang kèm lặp lại tiêu đề.
   - CHART / GRAPH: Tái tạo (redraw) qua SVG / Matplotlib nếu trích xuất được dữ liệu đáng tin cậy; bảo toàn hình ảnh gốc và dịch chú thích/nhãn nếu dữ liệu không chắc chắn.
   - DIAGRAM: Phân tích node, edge, label; tái tạo bằng SVG/Graphviz/Mermaid khi nhận diện được quan hệ; bảo toàn ảnh gốc khi phức tạp.
   - PHOTO & ILLUSTRATION: Bảo toàn nguyên vẹn 100% hình ảnh thực tế (Source Artifact), tuyệt đối không AI-regenerate.
4. **Renderer Router & Page Reconstruction Engine**: Dàn trang ngữ nghĩa liên tục theo luồng tài liệu (flow, column flow, section breaks, keep-with-next, widow/orphan protection) kết hợp Document Style Profile bảo toàn bản sắc thiết kế.
5. **Cổng kiểm định 4 lớp (Validation Gate)**: Content Fidelity, Structural Integrity, Visual Quality, Semantic Fidelity; xuất bản đầy đủ Review Artifacts (PDF, validation-report.json, reconstruction-report.json, source-map.json).
</goal>

---

<context>
Kỹ năng vận hành dựa trên các nguyên tắc thiết kế tối cao:
1. **Document Reconstruction thay vì PDF Overlay**: Không coi PDF là tập hợp textbox vật lý rời rạc. Bản dịch được dàn trang lại như một ấn phẩm chuyên nghiệp bằng ngôn ngữ mới, không phải PDF bị "nhét chữ đè lên".
2. **Reflow thay cho Fit-to-Box**: Khi độ dài ngôn ngữ đích giãn nở (+25-35%), mở rộng vùng chứa, đẩy nội dung phía dưới, ngắt trang tự nhiên. Font-size chỉ điều chỉnh trong biên độ chuẩn mực typography, không ép chữ vào hộp cũ.
3. **Preserve Source Photographic Artifacts**: Ảnh chụp (photos) và hình minh họa phức tạp (illustrations) được tôn trọng như tạo tác nguồn gốc, bảo toàn 100%, không tái sinh bằng mô hình AI tạo ảnh.
4. **Confidence-Aware Reconstruction**: Khi độ tin cậy tái tạo cấu trúc cao ($\ge 0.85$) -> Reconstruct; khi không chắc chắn -> Preserve original & translate caption. Tuyệt đối không tự suy đoán số liệu hay công thức.
5. **Kiến trúc Zero External LLM API**: Vận hành 100% qua mô hình Agent nội bộ IDE (Gemini 3.8) và các công cụ deterministic địa phương (PyMuPDF, Typst, LaTeX, Matplotlib/SVG), không phụ thuộc API trả phí ngoài.
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Toàn bộ việc phân tích ngữ nghĩa, dịch thuật và quyết định cấu trúc được thực hiện bởi chính Agent tích hợp trong IDE.
> - Tuyệt đối không gọi REST API ngoài, không yêu cầu API key.
> - Kỹ năng tự động chạy liên tục (Autonomous Full-Run) từ phân tích -> IR -> dịch -> dàn trang -> nghiệm thu.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/reconstruction_[stem]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/document-reconstruction-translator/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (`translated.pdf`, `validation-report.json`, `reconstruction-report.json`, `source-map.json`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (assets hình ảnh trích xuất, intermediate IR json, preview) PHẢI lưu trong `<process_dir>`.
> - TUYỆT ĐỐI KHÔNG lưu file thành phẩm trực tiếp vào thư mục gốc của repository Git.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo 4 Trục Tọa độ:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File PDF Nguồn** | Đường dẫn tuyệt đối file `.pdf` | Yêu cầu người dùng cung cấp file PDF |
| **2. Ngôn ngữ Đích** | `vi` (Tiếng Việt), `en` (Tiếng Anh), `ja` (Tiếng Nhật) | `vi` (Tiếng Việt) |
| **3. Thư mục Xuất bản** | Đường dẫn thư mục lưu file kết quả | Mặc định: `~/Downloads/AIWF_Output/` |
| **4. Chính sách Tái dựng** | Chế độ mặc định: Semantic Reflow + Selective Reconstruction | Áp dụng Reconstruction Policy chuẩn |

---

<instructions>
## QUY TRÌNH THỰC THI 7 GIAI ĐOẠN (SOP AUTONOMOUS FULL-RUN)

### GIAI ĐOẠN 1: PHÂN TÍCH CẤU TRÚC TÀI LIỆU (DOCUMENT STRUCTURE ANALYSIS)
1. Quét tài liệu PDF nguồn theo 3 cấp độ:
   - **Document level**: Kích thước trang, lề trang, lưới phân cột, bảng màu chủ đạo, font chữ nhận diện.
   - **Page level**: Vùng nội dung, header/footer, số trang, phân vùng lề.
   - **Region/Object level**: Phân loại từng khối thành 16 nhóm ngữ nghĩa (TEXT, HEADING, CAPTION, FOOTNOTE, TABLE, FORMULA, CHART, DIAGRAM, PHOTO, ILLUSTRATION, VECTOR_GRAPHIC, LIST, HEADER, FOOTER, PAGE_NUMBER, OTHER).
2. Trích xuất tài nguyên đồ họa thực tế (Photos, Artwork, Vector Stamps) và bảo toàn kênh Alpha qua `scripts/pdf_asset_extractor.py`.

---

### GIAI ĐOẠN 2: XÂY DỰNG DOCUMENT IR (INTERMEDIATE REPRESENTATION)
1. Tách biệt hoàn toàn nội dung (Content) và hình thức (Presentation) thành file `document_ir.json`:
   - Phân cấp `sections`, `headings`, `paragraphs`, `tables`, `formulas`, `figures`.
   - Lưu trữ thứ tự đọc logic (Logical Reading Order) thay vì tọa độ hình học rời rạc.
   - Thiết lập liên kết tham chiếu hai chiều giữa Caption <-> Figure, Table <-> Note, Heading <-> Body.
   - Lưu bbox hình học gốc làm giá trị tham khảo định hướng (hints), không dùng làm ràng buộc cứng.

---

### GIAI ĐOẠN 3: ĐÁNH GIÁ CHUYÊN NGÀNH & DỊCH THUẬT NGỮ NGHĨA
1. Xác định chuyên ngành sâu của tài liệu (Y sinh, Kỹ thuật cơ khí, Kinh tế - Tài chính, Pháp lý, Khoa học máy tính...).
2. Thiết lập Ma trận Tra cứu Thuật ngữ Chuyên ngành (Domain Terminology Matrix).
3. Thực hiện dịch nội dung trong Document IR:
   - Dịch toàn bộ TEXT theo đoạn mạch lạc, áp dụng thuật ngữ chuyên ngành chuẩn xác.
   - Dịch văn bản trong từng cell của TABLE, giữ nguyên cấu trúc ma trận dòng/cột.
   - Dịch nhãn và chú thích của FORMULA, CHART, DIAGRAM.
   - Giữ nguyên các thực thể bảo vệ (mã số hiệu, đơn vị đo lường, công thức số học, tên riêng quốc tế).

---

### GIAI ĐOẠN 4: ĐIỀU HƯỚNG BỘ RENDER CHUYÊN BIỆT (RENDERER ROUTER)
Duyệt qua từng thành phần trong Document IR và điều hướng đến renderer tương ứng:
- **Text & Flow Components** -> Typst Native Reflow Engine.
- **Formulas** -> LaTeX Math / Typst Math rendering.
- **Tables** -> Typst Dynamic Table (hỗ trợ tự co giãn cột, tự ngắt trang, lặp tiêu đề trang).
- **Charts** -> Redraw qua SVG/Matplotlib nếu dữ liệu trích xuất $\ge 0.85$ confidence; nếu không, sử dụng ảnh gốc kèm caption dịch.
- **Diagrams** -> Tái dựng qua SVG/Graphviz/Mermaid nếu cấu trúc rõ ràng; bảo toàn ảnh gốc kèm nhãn dịch nếu phức tạp.
- **Photos / Illustrations** -> Bảo toàn nguyên bản (Original Asset Preservation).

---

### GIAI ĐOẠN 5: TÁI DỰNG TRANG NGỮ NGHĨA (PAGE RECONSTRUCTION ENGINE)
1. Tạo file mã nguồn dàn trang (Typst Markup):
   - Áp dụng Document Style Profile (typography hierarchy, line height, margins, spacing rhythm).
   - Thiết lập luật dòng chảy: `keep-with-next` cho tiêu đề, bảo vệ widow/orphan cho đoạn văn.
   - Tự do phân trang (Natural Pagination): Không ép giữ nguyên số trang gốc nếu nội dung cần không gian để hiển thị rõ ràng và đẹp mắt.

---

### GIAI ĐOẠN 6: CỔNG KIỂM ĐỊNH TOÀN DIỆN 4 LỚP (4-LAYER VALIDATION GATE)
Agent kích hoạt chuỗi kiểm định đa chiều:
1. **Lớp 1: Content Validation**: Đối chiếu không mất đoạn, không trùng lặp, bảo toàn 100% số liệu, đơn vị và công thức.
2. **Lớp 2: Structural Validation**: Kiểm tra thứ tự đọc, cấp độ tiêu đề, liên kết caption-hình ảnh, cấu trúc bảng.
3. **Lớp 3: Visual Validation**: Kiểm tra không chồng chéo (no overlap), không cắt xén (no clipping), cỡ chữ đạt chuẩn đọc dễ dàng, lề an toàn.
4. **Lớp 4: Semantic Fidelity**: Đảm bảo toàn bộ nội dung dịch phản ánh trung thực ý nghĩa nguyên bản.
- Quét sạch 100% ký tự nguồn chưa dịch qua `scripts/verify_retention.py`.

---

### GIAI ĐOẠN 7: XUẤT BẢN THÀNH PHẨM & BỘ TÀI LIỆU DUYỆT (REVIEW ARTIFACTS)
1. Biên dịch và xuất bản các thành phẩm ra `<output_dir>`:
   - `translated.pdf`: Bản PDF dịch tái cấu trúc hoàn chỉnh.
   - `validation-report.json`: Báo cáo kết quả kiểm định 4 lớp.
   - `reconstruction-report.json`: Báo cáo chi tiết chiến lược tái dựng từng phân vùng và mức độ tin cậy.
   - `source-map.json`: Bảng ánh xạ quan hệ giữa đối tượng nguồn và đối tượng tái dựng.
2. Bàn giao kết quả sạch cho người dùng theo Clean Delivery Protocol.
</instructions>

---

<constraints>
## SÁU ĐIỀU CẤM TUYỆT ĐỐI (6 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% dịch thuật và tái dựng thực hiện bằng mô hình nội bộ và tooling cục bộ.
2. ❌ **CẤM ÉP FIT-TO-BOX GÂY HỎNG TYPOGRAPHY:** Nghiêm cấm co nhỏ font chữ xuống mức không thể đọc chỉ để ép vừa hộp chữ cũ hoặc cố giữ cùng số trang/số dòng.
3. ❌ **CẤM AI-REGENERATE ẢNH CHỤP VÀ HÌNH NGHỆ THUẬT:** Ảnh chụp (photos) và hình minh họa chuyên môn phải được giữ nguyên bản gốc.
4. ❌ **CẤM TỰ BỊA DỮ LIỆU BIỂU ĐỒ HOẶC CÔNG THỨC:** Chỉ tái vẽ biểu đồ khi trích xuất được số liệu đáng tin cậy. Khi không chắc chắn, giữ ảnh biểu đồ gốc và dịch chú thích.
5. ❌ **CẤM GÁN PLACEHOLDER HOẶC BỎ SÓT NỘI DUNG:** Toàn bộ khối văn bản và ô bảng biểu phải được chuyển ngữ đầy đủ, mạch lạc.
6. ❌ **CẤM XUẤT THÀNH PHẨM VÀO REPO GIT:** Toàn bộ file xuất bản phải lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/`).
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `assets/`: Chứa hình ảnh, biểu đồ và con dấu gốc đã bóc tách.
- `document_ir.json`: Cấu trúc trung gian phân cấp của tài liệu (Document IR).
- `style_profile.json`: Bản sắc thiết kế tài liệu (Document Style Profile).
- `reconstructed.typ`: Mã nguồn dàn trang Typst ngữ nghĩa.
- `validation-report.json`: Kết quả kiểm thử đối chiếu 4 lớp.
- `reconstruction-report.json`: Báo cáo chiến lược tái cấu trúc từng vùng.
- `source-map.json`: Ánh xạ nguồn - đích.
</working_ledger>

---

<quality_gate>
## CỔNG KIỂM TOÁN ĐỐI CHIẾU TOÀN VẸN 4 LỚP (4-LAYER QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **LỚP 1 — Toàn vẹn Nội dung (Content Integrity):**
   - Đủ 100% các đoạn văn, tiêu đề, danh sách, bảng biểu so với nguồn.
   - Giữ nguyên số liệu, đơn vị đo lường, mã định danh, công thức toán.
   - Không còn sót ký tự nguồn ngoại ngữ chưa dịch (`verify_retention.py` đạt 0 residual block).
2. ✅ **LỚP 2 — Toàn vẹn Cấu trúc (Structural Integrity):**
   - Cây tiêu đề phân cấp hợp lý (H1 -> H2 -> H3).
   - Chú thích (Caption) gắn chặt với Hình ảnh/Bảng biểu tương ứng.
   - Quan hệ node - edge trong diagram được khôi phục chính xác.
3. ✅ **LỚP 3 — Chất lượng Thị giác (Visual Quality):**
   - Typography dễ đọc: Font chữ thân bài $\ge 9.0\text{pt}$ (trừ chú thích nhỏ $\ge 7.0\text{pt}$).
   - Không có hiện tượng chồng chữ (text collision), đè lề hoặc tràn trang bất thường.
   - Ngắt trang tự nhiên, tránh tiêu đề mồ côi (keep-with-next đạt chuẩn).
4. ✅ **LỚP 4 — Độ trung thực Ngữ nghĩa (Semantic Fidelity):**
   - Thuật ngữ chuyên ngành chuẩn xác theo quy chuẩn.
   - 0 placeholder, 0 câu cụt vô nghĩa.
   - Cơ chế gắn cờ tin cậy (Confidence Flagging): Khi OCR hoặc nhận diện mờ, gắn cờ `[CẦN XÁC MINH]` kèm bằng chứng.
   - Các đối tượng phức tạp có báo cáo ghi nhận chiến lược và chỉ số tin cậy rõ ràng.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên tài liệu, ngôn ngữ nguồn/đích, số trang tái dựng (kèm tỷ lệ giãn nở nếu có).
  - Bản sắc thiết kế đã khôi phục (Style Profile: font, grid, spacing).
  - Tình trạng xử lý các đối tượng đặc biệt (Bảng biểu, Công thức, Biểu đồ/Diagram, Hình ảnh).
  - Kết quả kiểm định 4 lớp (Content, Structure, Visual, Semantics).
  - Đường dẫn tuyệt đối đến file PDF hoàn chỉnh và các file Review Artifacts trong `<output_dir>`.
- Không xả mã nguồn thô hoặc log terminal dài dòng vào khung chat.
</delivery_protocol>

---

## CLI CONTRACT

### 1. `scripts/pdf_asset_extractor.py`
- **Mục đích:** Bóc tách toàn bộ hình ảnh, đồ thị và vector kèm kênh alpha mặt nạ mềm (SMask transparency).
- **Cú pháp:** `python3 scripts/pdf_asset_extractor.py --pdf <duong_dan_pdf> --extract-all --output-dir <thu_muc_assets>`

### 2. `scripts/verify_retention.py`
- **Mục đích:** Kiểm toán quét sạch 100% ký tự nguồn ngoại ngữ chưa dịch (Zero Residual Source Text, Rule R3 §8).
- **Cú pháp:** `python3 scripts/verify_retention.py --source <file_goc.pdf> --target <file_dich.pdf> [tùy_chọn]`

### 3. `scripts/verify/mode_aware_verifier.py`
- **Mục đích:** Kiểm định thích ứng theo chế độ tái dựng (TEXT_FLOW, HYBRID, FIXED), rà soát phân trang và typography.
- **Cú pháp:** `python3 scripts/verify/mode_aware_verifier.py --source <goc.pdf> --target <dich.pdf>`
