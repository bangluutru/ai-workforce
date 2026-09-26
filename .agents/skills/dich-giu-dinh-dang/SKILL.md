---
name: dich-giu-dinh-dang
display-name: Dịch Giữ Định Dạng
description: >-
  Dịch thuật chuyên sâu tài liệu PDF phức tạp bảo toàn 100% bố cục gốc tỷ lệ 1:1, đồ họa, biểu đồ đa phần tử, con dấu pháp nhân trong suốt (SMask Alpha), khung viền hoa văn và thuật ngữ chuyên ngành hẹp theo chuẩn Luật R6.
  USE WHEN: Người dùng cần dịch file PDF (đặc biệt văn bản chuyên khảo, y khoa, chứng chỉ, công văn có con dấu/biểu đồ) yêu cầu giữ nguyên bố cục hình học 1:1.
  DO NOT USE WHEN: Cần dịch tài liệu văn phòng Word (.docx), file text dài cần xuất bản song ngữ linh hoạt (dùng 'ejv-translate'), hoặc chỉ bóc tách OCR chữ số hóa (dùng 'boc-tach-pdf').
trigger: Dịch giữ định dạng, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh, dịch tài liệu có con dấu và biểu đồ
category: docs
needs_file: true
file_filter: pdf
---

# Kỹ Năng Dịch Giữ Định Dạng (dich-giu-dinh-dang v2.0)
## Chuẩn Google Antigravity 2.0 & 7 Trụ Cột Bảo Toàn Định Dạng & Nội Dung Chuyên Ngành (Luật R6)

<goal>
Thực hiện quy trình dịch thuật tài liệu PDF phức tạp (chuyên khảo 2 cột, bảng biểu số liệu, con dấu pháp nhân đỏ, biểu đồ kiểm soát chất lượng đa phần tử, bằng khen khung hoa văn) sang tiếng Việt (hoặc tiếng Anh, tiếng Nhật) với các tiêu chí tối thượng:
1. Bảo toàn chính xác tỷ lệ trang 1:1 so với bản gốc ($N_{\text{dịch}} == N_{\text{gốc}}$).
2. Bảo toàn 100% hình ảnh, sơ đồ, biểu đồ đa phần tử sắc nét chuẩn 300 DPI (Multi-panel Subplot Bounding bao trọn cả trục tọa độ và đường giới hạn).
3. Giải mã kênh Alpha mặt nạ mềm (SMask) để con dấu đỏ và chữ ký trong suốt tự nhiên trên nền trắng, không bị lỗi bôi đen nền.
4. Tách biệt khung hoa văn mạ vàng và thiết lập vùng đệm an toàn (Safe Zone Margins $\ge 15-20\text{pt}$) chống đè chữ lên họa tiết.
5. Triệt tiêu 100% nguy cơ dịch sót (Zero Translation Omission) qua Cơ chế Ánh xạ Kép (Dual-Level Mapping: cấp đoạn gộp và cấp dòng đơn), nghiêm cấm dấu chấm placeholder `.`.
6. Chuẩn hóa 100% thuật ngữ kỹ thuật sâu qua Bước Đánh giá Chuyên ngành Bắt buộc (Domain Terminology Audit) và lập Ma trận Tra cứu Thuật ngữ.
7. Vượt qua Cổng kiểm toán đối chiếu toàn vẹn 3 lớp (Tri-Layer Quality Gate: Bố cục 1:1, Không sót ký tự nguồn Rule R3 §8, Toàn vẹn nội dung & thuật ngữ) đạt 100% PASS trước khi xuất bản ra `<output_dir>`.
</goal>

---

<context>
Kỹ năng vận hành dựa trên **7 Trụ Cột Kỹ Thuật Bất Di Bất Dịch** của Luật R6:
1. **Trụ cột 1 — Mặt nạ mềm SMask trong suốt (SMask Transparency Protocol)**: Trích xuất và giải mã mặt nạ mềm qua `pdf_asset_extractor.py`, hòa trộn kênh Alpha Compositing trên nền trắng, triệt tiêu lỗi bôi đen nền con dấu/chữ ký.
2. **Trụ cột 2 — Trích xuất toàn vẹn biểu đồ đa phần tử (Multi-panel Subplot Bounding)**: Bounding box bao trọn cả hàng đồ thị $\bar{X}$ và $R$, các đường giới hạn UCL/LCL, trục tung đơn vị và thước đo trục hoành.
3. **Trụ cột 3 — Cô lập khung viền & Lề an toàn (Ornate Frame & Safe Zone Margins)**: Tách sạch nội dung lõi của bằng khen/chứng chỉ, thiết lập Safe Zone Margins (top $\ge 105\text{pt}$, bottom $\ge 90\text{pt}$, x $\ge 75\text{pt}$) chống đè viền hoa văn.
4. **Trụ cột 4 — Cân bằng bố cục đa cột & Ngân sách chữ (Multi-column Balance & Typography Budgeting)**: Bù trừ độ giãn nở tiếng Việt (+25-35%), cân đối đáy 2 cột qua dãn dòng và `#colbreak()`, tự động gộp bounding box đoạn văn để triệt tiêu đè dòng.
5. **Trụ cột 5 — Cơ chế Ánh xạ Kép & Chống dịch sót (Dual-Level Mapping & Zero-Omission Protocol)**: Ánh xạ đồng thời ở Cấp độ Đoạn Gộp (`combined_text`) và Cấp độ Khối Đơn/Từng Dòng (`single_block` / `line_text`). Cấm tuyệt đối gán dấu chấm placeholder `.`.
6. **Trụ cột 6 — Bước Đánh giá & Chuẩn hóa Thuật ngữ Chuyên ngành (Mandatory Domain Review)**: Khảo sát phân ngành sâu, lập Ma trận Tra cứu Thuật ngữ Chuyên ngành, nghiêm cấm dịch máy thô từng chữ (word-by-word).
7. **Trụ cột 7 — Cổng Kiểm toán Đối chiếu Toàn vẹn 3 Lớp (Tri-Layer Quality Gate)**: Khóa chặn cứng 3 lớp (Lớp 1: Bố cục hình học 1:1; Lớp 2: Quét sạch 100% ký tự nguồn Rule R3 §8; Lớp 3: Toàn vẹn nội dung, 0 placeholder, 100% khớp thuật ngữ).
</context>

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Kỹ năng này vận hành hoàn toàn bằng khả năng nội bộ của Antigravity IDE (Gemini 3.8) kết hợp các thư viện xử lý tài liệu cục bộ (`pymupdf`, `pdfplumber`, `pypandoc`, Typst).
> - TUYỆT ĐỐI KHÔNG gọi REST API trả phí bên ngoài.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) từ bước bóc tách, dịch thuật, định dạng đến khi nghiệm thu 1:1, không tự dừng dở dang để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file trước khi thực hiện quy trình:

| Placeholder | Quy ước xác định đường dẫn thực tế |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/retain_pdf_[stem]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/dich-giu-dinh-dang/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (`.pdf`, `.docx`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (assets hình ảnh trích xuất, json dàn trang, preview) PHẢI lưu trong `<process_dir>`.
> - TUYỆT ĐỐI KHÔNG lưu file thành phẩm trực tiếp vào thư mục gốc của repository Git.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo 4 Trục Tọa độ:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File PDF Nguồn** | Đường dẫn tuyệt đối file `.pdf` | Yêu cầu người dùng cung cấp file PDF |
| **2. Ngôn ngữ Đích** | `vi` (Tiếng Việt), `en` (Tiếng Anh), `ja` (Tiếng Nhật) | `vi` (Tiếng Việt) |
| **3. Thư mục Xuất bản** | Đường dẫn thư mục lưu file kết quả | Mặc định: `~/Downloads/AIWF_Output/` |
| **4. Bố cục Tài liệu** | Chuyên khảo 2 cột, Biểu đồ đa phần tử, Bằng khen viền | Tự động quét cấu trúc qua PyMuPDF |

---

<instructions>
## QUY TRÌNH THỰC THI 7 GIAI ĐOẠN (SOP AUTONOMOUS FULL-RUN)

### GIAI ĐOẠN 1: KHÁM PHÁ & TRÍCH XUẤT ĐỒ HỌA CHUYÊN SÂU
Agent quét toàn bộ trang trong tài liệu nguồn và phân loại đối tượng đồ họa:
1. **Bóc tách toàn bộ hình ảnh & Giải mã Mặt nạ mềm SMask (Con dấu đỏ & Chữ ký):**
   ```bash
   python3 scripts/pdf_asset_extractor.py --pdf "<pdf_path>" --extract-all --output-dir "<process_dir>/assets/"
   ```
2. **Trích xuất theo từng trang:**
   ```bash
   python3 scripts/pdf_asset_extractor.py --pdf "<pdf_path>" --page <P> --output-dir "<process_dir>/assets/"
   ```

---

### GIAI ĐOẠN 2: TRÍCH XUẤT CẤU TRÚC VĂN BẢN & ĐOẠN LIÊN TIẾP
1. Trích xuất toàn bộ khối văn bản với tọa độ hình học chính xác qua PyMuPDF.
2. Tự động nhận diện cấu trúc phân cột (1 cột, 2 cột), bảng biểu (ma trận dòng-cột), tiêu đề, danh mục và chú thích.
3. Gom nhóm các dòng liên tiếp có khoảng cách dọc $< 8\text{pt}$ để chuẩn bị dữ liệu cho cơ chế gộp đoạn văn (Paragraph Box-Merging).

---

### GIAI ĐOẠN 3: ĐÁNH GIÁ CHUYÊN NGÀNH & LẬP MA TRẬN THUẬT NGỮ (MANDATORY DOMAIN REVIEW)
1. **Xác định chuyên ngành sâu**: Nhận diện lĩnh vực chuyên biệt của tài liệu (Thận học & Lọc máu, Tim mạch can thiệp, Dược lý lâm sàng, Kế toán - Thuế, Sở hữu trí tuệ, Tiêu chuẩn kỹ thuật ISO/JIS...).
2. **Thiết lập Ma trận Tra cứu Thuật ngữ Chuyên ngành (Domain Terminology Matrix)**:
   - Đối chiếu quy chuẩn quản lý nhà nước (Bộ Y tế, Bộ Tài chính, Bộ KH&CN...).
   - Lập danh mục từ khóa kỹ thuật cốt lõi và định nghĩa dịch thuật chuẩn tắc.
   - **Cấm tuyệt đối dịch máy thô từng chữ (word-by-word)** làm biến dạng thuật ngữ y tế / kỹ thuật (ví dụ: cấm dịch `血液浄化` là "làm sạch máu", phải dịch là "kỹ thuật lọc máu ngoài cơ thể"; cấm dịch `維持透析患者` là "bệnh nhân duy trì thẩm tách", phải dịch là "bệnh nhân lọc máu chu kỳ").

---

### GIAI ĐOẠN 4: DỊCH THUẬT ÁNH XẠ KÉP & QUẢN TRỊ NGÂN SÁCH TỪ NGỮ (DUAL-LEVEL MAPPING)
1. **Cơ chế Ánh xạ Kép (Dual-Level Mapping)**:
   - Tạo từ điển dịch `merged_ejv.json` bắt buộc chứa 2 cấp độ ánh xạ song song:
     - **Cấp độ Đoạn Gộp (`combined_text`)**: Chứa bản dịch hoàn chỉnh của cả đoạn văn đa dòng.
     - **Cấp độ Khối Đơn & Từng Dòng (`single_block` / `line_text`)**: Chứa bản dịch của từng khối và dòng con nhằm dự phòng fallback khi sai số tọa độ.
   - **NGHIÊM CẤM** gán placeholder dấu chấm `.`, khoảng trắng rỗng hoặc cắt cụt câu.
2. **Quản trị Ngân sách Từ ngữ (Typography Budgeting)**:
   - Áp dụng Live Formulas kiểm soát mật độ chữ:
     $$\text{Budget Ratio} = \frac{\text{Số từ tiếng Việt}}{\text{Số từ tiếng gốc}} \in [1.20, 1.35]$$
   - Tinh chỉnh cỡ chữ ($5.8\text{pt} - 6.2\text{pt}$ cho kỷ yếu 2 cột) và dãn dòng ($0.24\text{em} - 0.26\text{em}$) để đảm bảo bản dịch nằm gọn trong trang mà không tràn sang trang mới.

---

### GIAI ĐOẠN 5: LẬP TRÌNH BỐ CỤC TYPST 1:1 IN-PLACE ENGINE
Agent sử dụng Typst Smart Reflow Engine v4.0:
```bash
python3 .agents/skills/dich-giu-dinh-dang/scripts/typst_overlay.py \
    --pdf "<pdf_path>" \
    --blocks "<process_dir>/merged_ejv.json" \
    --lang vi \
    --output "<process_dir>/draft.pdf"
```
- Tự động gộp Bounding Box đoạn văn ($\min(y0)$ đến $\max(y1)$).
- Tự động cân đối tỷ lệ font theo chiều cao khối gộp, triệt tiêu hiện tượng đè chữ.
- Xóa trắng chính xác lớp chữ gốc và phủ lớp chữ dịch vector siêu nét.

---

### GIAI ĐOẠN 6: BIÊN DỊCH PDF & CỔNG KIỂM TOÁN ĐỐI CHIẾU TOÀN VẸN 3 LỚP (TRI-LAYER QUALITY GATE)
Agent kích hoạt chuỗi công cụ kiểm toán tự động:
1. **Lớp 1: Kiểm toán Đối chiếu Định dạng Hình học 1:1 (Parity Audit):**
   ```bash
   python3 scripts/verify_layout_parity.py --source "<pdf_path>" --target "<process_dir>/draft.pdf"
   ```
   - Bắt buộc: Tỷ lệ trang 1:1, đủ 100% hình ảnh/biểu đồ/con dấu, đủ bảng biểu, số dòng trong ngân sách.
2. **Lớp 2: Kiểm toán Quét sạch Ký tự Nguồn (Zero Residual Source Text Audit - Rule R3 §8):**
   ```bash
   python3 scripts/verify_retention.py --source "<pdf_path>" --target "<process_dir>/draft.pdf" --output "<process_dir>/retention_report.json"
   ```
   - Bắt buộc: 0 khối sót ký tự nguồn CJK / tiếng gốc. Khóa chặn cứng (Hard Blocker) nếu còn sót $\ge 1$ khối.
3. **Lớp 3: Kiểm toán Toàn vẹn Bản dịch & Khớp Thuật ngữ Chuyên ngành (Zero Omission & Domain Audit):**
   - Rà soát 100% khối văn bản: 0 dấu chấm placeholder `.`, 0 câu ngắt cụt, 100% thuật ngữ kỹ thuật khớp Ma trận Chuyên ngành Giai đoạn 3.

> ⚠️ **Điều kiện xuất bản:** Bắt buộc đạt **100% PASS** trên cả 3 Lớp kiểm định. Nếu chưa đạt, Agent tự động sửa lỗi và biên dịch lại.

---

### GIAI ĐOẠN 7: XUẤT BẢN & BÀN GIAO THÀNH PHẨM
- Sao chép file PDF đạt chuẩn sang thư mục xuất bản:
  ```bash
  cp "<process_dir>/draft.pdf" "<output_dir>/<tên_file>_dich_giu_dinh_dang.pdf"
  ```
- Báo cáo kết quả theo Giao thức Bàn giao Sạch (Clean Delivery Protocol).
</instructions>

---

<constraints>
## SÁU ĐIỀU CẤM TUYỆT ĐỐI (6 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% dịch thuật và định dạng thực hiện bằng mô hình nội bộ và Typst cục bộ.
2. ❌ **CẤM LÀM TRÀN SỐ TRANG:** Số trang bản dịch bắt buộc phải khớp 1:1 với bản gốc ($N_{\text{target}} == N_{\text{source}}$).
3. ❌ **CẤM LÀM ĐEN NỀN CON DẤU & ĐÈ CHỮ LÊN KHUNG HOA VĂN:** Bắt buộc áp dụng SMask Alpha Compositing và tuân thủ khoảng cách an toàn Safe Zone Margins $\ge 15-20\text{pt}$.
4. ❌ **CẤM GÁN PLACEHOLDER DẤU CHẤM `.` HOẶC BỎ SÓT DÒNG DỊCH:** Cung cấp đầy đủ bản dịch ở cả Cấp độ Đoạn Gộp và Cấp độ Khối Đơn/Dòng Con (Dual-Level Mapping).
5. ❌ **CẤM DỊCH MÁY THÔ TỪNG CHỮ (WORD-BY-WORD):** Nghiêm cấm dịch theo nghĩa đen làm sai lệch bản chất y khoa / kỹ thuật chuyên ngành sâu.
6. ❌ **CẤM XUẤT FILE VÀO CODEBASE:** File PDF thành phẩm bắt buộc xuất ra `<output_dir>` (mặc định: `~/Downloads/AIWF_Output/`).
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `assets/`: Chứa toàn bộ hình ảnh, biểu đồ và con dấu trong suốt đã bóc tách.
- `merged_ejv.json`: Từ điển ánh xạ kép (Combined Text + Single Line mappings).
- `domain_matrix.json`: Ma trận tra cứu thuật ngữ chuyên ngành đã chuẩn hóa.
- `parity_report.json`: Báo cáo đối chiếu định dạng hình học 1:1.
- `retention_report.json`: Báo cáo đối chiếu ký tự nguồn và điểm lưu giữ định dạng.
</working_ledger>

---

<quality_gate>
## CỔNG KIỂM TOÁN ĐỐI CHIẾU TOÀN VẸN 3 LỚP (TRI-LAYER QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **LỚP 1 — Bố cục hình học 1:1:**
   - Tỷ lệ trang 1:1 ($N_{\text{dịch}} == N_{\text{gốc}}$).
   - Đồ họa nguyên vẹn 100%, sắc nét 300 DPI.
   - Con dấu trong suốt tự nhiên, không viền đen.
   - Khung viền an toàn, không bị chữ đè lên hoa văn.
   - Điểm Parity Audit đạt 100% PASS.
2. ✅ **LỚP 2 — Sạch 100% ký tự nguồn (Rule R3 §8):**
   - Điểm kiểm toán `verify_retention.py` $\ge 95\%$ (Hạng A+).
   - **Chính xác 0 khối chữ nguồn CJK / ngoại ngữ gốc còn sót lại**.
3. ✅ **LỚP 3 — Toàn vẹn nội dung & Chuẩn hóa chuyên ngành:**
   - Đạt 100% độ phủ bản dịch (Zero Translation Omission).
   - 0 dấu chấm placeholder `.`, 0 dòng cắt cụt vô nghĩa.
   - 100% thuật ngữ chuyên ngành chuẩn xác theo Ma trận Chuyên ngành.
   - Khử sạch dấu vết AI (không dùng em dash `—`, không dùng Oxford comma `, và`).
   - Tự động gắn cờ nghi ngờ (Confidence Flagging): Khi OCR hoặc nhận diện văn bản mờ, tự động gắn cờ `[CẦN XÁC MINH]` để xin ý kiến con người.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên tài liệu, số trang (1:1), ngôn ngữ dịch.
  - Chuyên ngành kỹ thuật sâu đã thẩm định và áp dụng chuẩn thuật ngữ.
  - Tình trạng bảo toàn đồ họa (con dấu trong suốt, biểu đồ đa phần tử, khung viền).
  - Kết quả kiểm toán 3 lớp: Parity Audit (100% PASS), Zero Residual CJK (0 khối sót), Zero Omission (100% hoàn chỉnh).
  - Đường dẫn tuyệt đối đến file PDF hoàn chỉnh trong `<output_dir>`.
- Không xả mã lệnh thô hoặc danh sách sóng âm vào khung chat.
</delivery_protocol>

---

## CLI CONTRACT

> **Quy tắc đọc helper script:** Sử dụng CLI contract dưới đây trước tiên. Chỉ đọc mã nguồn script khi: (1) lệnh theo contract bị lỗi cần debug, (2) cần hành vi chuyên biệt chưa được document, hoặc (3) cần sửa đổi script.

### 1. `scripts/pdf_asset_extractor.py`
- **Mục đích:** Bóc tách toàn bộ hình ảnh, đồ thị đa phần tử và con dấu pháp nhân kèm giải mã kênh alpha mặt nạ mềm (SMask transparency, Rule R6).
- **Cú pháp:** `python3 scripts/pdf_asset_extractor.py --pdf <duong_dan_pdf> --extract-all --output-dir <thu_muc_assets>`
- **Tham số:**
  - `--pdf <path>`: (Bắt buộc) Đường dẫn file PDF nguồn
  - `--extract-all`: Trích xuất toàn bộ hình ảnh/con dấu qua tất cả các trang
  - `--output-dir <path>`: Thư mục lưu assets bóc tách
- **Mã thoát (Exit code):** 0 nếu thành công, khác 0 nếu lỗi.
- **Ví dụ mẫu:**
  ```bash
  python3 scripts/pdf_asset_extractor.py --pdf "input.pdf" --extract-all --output-dir "_process/assets/"
  ```

### 2. `scripts/verify_retention.py`
- **Mục đích:** Kiểm toán đối chiếu định dạng 1:1, bảo toàn hình ảnh/con dấu và quét sạch 100% ký tự nguồn (Zero Residual Source Text, Rule R3 §8).
- **Cú pháp:** `python3 scripts/verify_retention.py --source <file_goc.pdf> --target <file_dich.pdf> [tùy_chọn]`
- **Tham số:**
  - `--source, -s <path>`: (Bắt buộc) Đường dẫn file PDF gốc
  - `--target, -t <path>`: (Bắt buộc) Đường dẫn file PDF bản dịch
  - `--json, -j <path>`: Đường dẫn file `merged_ejv.json` (tùy chọn)
  - `--min-score <score>`: Ngưỡng điểm tối thiểu (mặc định: 85.0)
- **Mã thoát (Exit code):** 0 nếu Đạt chuẩn (PASS), 1 nếu có lỗi hoặc còn sót chữ nguồn (FAIL).
- **Ví dụ mẫu:**
  ```bash
  python3 scripts/verify_retention.py --source "goc.pdf" --target "dich.pdf"
  ```


