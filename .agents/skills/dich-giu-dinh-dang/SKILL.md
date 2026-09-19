---
name: dich-giu-dinh-dang
display-name: Dịch Giữ Định Dạng
description: Dịch thuật chuyên sâu tài liệu PDF đa trang bảo toàn 100% bố cục gốc, tỷ lệ trang 1:1, đồ họa, biểu đồ đa phần tử, con dấu pháp nhân trong suốt (SMask Alpha) và khung viền hoa văn theo chuẩn Luật R6 (Retain-PDF). Hỗ trợ tiếng Việt, tiếng Anh và tiếng Nhật. Kích hoạt khi user yêu cầu 'dịch giữ định dạng', 'dịch bảo toàn định dạng PDF', 'retain PDF', 'dịch PDF giữ nguyên bố cục và hình ảnh', 'dịch tài liệu có con dấu và biểu đồ'. KHÔNG dùng cho văn bản Word/Excel thuần túy (dùng xu-ly-van-phong) hoặc chỉ bóc tách chữ ra text (dùng boc-tach-pdf).
trigger: Dịch giữ định dạng, Dịch bảo toàn định dạng PDF, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh, dịch tài liệu có con dấu và biểu đồ
argument-hint: [pdf_file_path] [target_lang: vi|en|ja] [output_dir]
allowed-tools: [run_command, view_file, write_to_file, replace_file_content]
effort: high
context: fork
interaction-mode: direct
needs_file: true
file_filter: pdf
---

# Kỹ Năng Dịch Giữ Định Dạng (dich-giu-dinh-dang v1.0)
## Chuẩn Google Antigravity 2.0 & Tiêu Chuẩn Bảo Toàn Bố Cục Đồ Họa Luật R6 (Retain-PDF)

<goal>
Thực hiện quy trình dịch thuật tài liệu PDF phức tạp (chuyên khảo 2 cột, bảng biểu số liệu, con dấu pháp nhân đỏ, biểu đồ kiểm soát chất lượng đa phần tử, bằng khen khung hoa văn) sang tiếng Việt (hoặc tiếng Anh, tiếng Nhật) với các tiêu chí tối thượng:
1. Bảo toàn chính xác tỷ lệ trang 1:1 so với bản gốc ($N_{\text{dịch}} == N_{\text{gốc}}$).
2. Bảo toàn 100% hình ảnh, sơ đồ, biểu đồ đa phần tử sắc nét chuẩn 300 DPI.
3. Giải mã kênh Alpha mặt nạ mềm (SMask) để con dấu đỏ và chữ ký trong suốt tự nhiên, không bị lỗi bôi đen nền.
4. Tách biệt khung hoa văn mạ vàng và thiết lập vùng đệm an toàn (Safe Zone Margins) chống đè chữ lên họa tiết.
5. Vượt qua cổng kiểm định đối chiếu định dạng 1:1 (`verify_layout_parity.py`) đạt 100% PASS trước khi xuất bản ra `<output_dir>`.
</goal>

---

<context>
Kỹ năng vận hành dựa trên 5 Trụ cột Retain-PDF của Luật R6:
1. **Trụ cột 1 — Mặt nạ mềm SMask trong suốt**: Trích xuất và giải mã mặt nạ mềm qua `pdf_asset_extractor.py`, hòa trộn kênh Alpha Compositing trên nền trắng, triệt tiêu lỗi bôi đen nền con dấu.
2. **Trụ cột 2 — Trích xuất toàn vẹn biểu đồ đa phần tử**: Bounding box bao trọn cả hàng đồ thị $\bar{X}$ và $R$, các đường giới hạn UCL/LCL và thước đo trục hoành.
3. **Trụ cột 3 — Cô lập khung viền & Lề an toàn**: Tách sạch nội dung lõi của bằng khen/chứng chỉ, thiết lập Safe Zone Margins (top $\ge 105\text{pt}$, bottom $\ge 90\text{pt}$, x $\ge 75\text{pt}$) chống đè viền hoa văn.
4. **Trụ cột 4 — Cân bằng bố cục đa cột & Ngân sách chữ**: Bù trừ độ giãn nở tiếng Việt (+25-35%), cân đối đáy 2 cột qua dãn dòng và `#colbreak()`.
5. **Trụ cột 5 — Cổng kiểm toán đối chiếu 1:1**: Bắt buộc đạt 100% PASS qua `verify_layout_parity.py` trước khi xuất bản.
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
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/`** |
| `<process_dir>` | Thư mục tạm xử lý: `<workspace>/_process/retain_pdf_[stem]/` (đã nằm trong `.gitignore`) |
| `<skill_dir>` | Thư mục kỹ năng: `<workspace>/.agents/skills/dich-giu-dinh-dang/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi file thành phẩm xuất bản (`.pdf`, `.docx`) PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/` hoặc nơi user chỉ định).
> - Toàn bộ file tạm (assets hình ảnh trích xuất, json dàn trang, preview) PHẢI lưu trong `<process_dir>`.
> - TUYỆT ĐỐI KHÔNG lưu file thành phẩm trực tiếp vào thư mục gốc của repository Git.

---

## 🏗️ Bảng Tọa độ Đầu vào & Phân luồng (Intake Coordinates)

Trước khi thực thi, Agent phân loại tọa độ đầu vào của người dùng theo 4 Trục Tọa độ:

| Trục Tọa độ | Giá trị xác định | Hành vi mặc định nếu thiếu |
|---|---|---|
| **1. File PDF Nguồn** | Đường dẫn tuyệt đối file `.pdf` | Yêu cầu người dùng cung cấp file PDF |
| **2. Ngôn ngữ Đích** | `vi` (Tiếng Việt), `en` (Tiếng Anh), `ja` (Tiếng Nhật) | `vi` (Tiếng Việt) |
| **3. Thư mục Xuất bản** | Đường dẫn thư mục lưu file kết quả | Mặc định: `~/Downloads/` |
| **4. Bố cục Tài liệu** | Chuyên khảo 2 cột, Biểu đồ đa phần tử, Bằng khen viền | Tự động quét cấu trúc qua PyMuPDF |

---

<instructions>
## QUY TRÌNH THỰC THI 6 GIAI ĐOẠN (SOP AUTONOMOUS FULL-RUN)

### GIAI ĐOẠN 1: KHÁM PHÁ & TRÍCH XUẤT ĐỒ HỌA CHUYÊN SÂU
Agent quét toàn bộ trang trong tài liệu nguồn và phân loại đối tượng đồ họa:
1. **Giải mã Mặt nạ mềm SMask (Con dấu đỏ & Chữ ký):**
   ```bash
   python3 .agents/skills/dich-giu-dinh-dang/scripts/pdf_asset_extractor.py extract-images --pdf "<pdf_path>" --output-dir "<process_dir>/assets/"
   ```
2. **Trích xuất Biểu đồ Đa phần tử (Subplot Bounding):**
   - Đối với biểu đồ kiểm soát chất lượng đa phần tử:
   ```bash
   python3 .agents/skills/dich-giu-dinh-dang/scripts/pdf_asset_extractor.py crop-box --pdf "<pdf_path>" --page <P> --bbox "<x0>,<y0>,<x1>,<y1>" --output "<process_dir>/assets/fig_<name>.png" --dpi 300
   ```
3. **Cô lập Khung viền Hoa văn (Ornate Frame Isolation):**
   - Đối với bằng khen hoặc giấy chứng nhận:
   ```bash
   python3 .agents/skills/dich-giu-dinh-dang/scripts/pdf_asset_extractor.py isolate-frame --pdf "<pdf_path>" --page <P> --inner-rect "<x0>,<y0>,<x1>,<y1>" --output "<process_dir>/assets/frame_page_<P>.png"
   ```

---

### GIAI ĐOẠN 2: DỊCH THUẬT NGỮ CẢNH & QUẢN TRỊ NGÂN SÁCH TỪ NGỮ
- Áp dụng Live Formulas kiểm soát mật độ chữ:
  $$\text{Budget Ratio} = \frac{\text{Số từ tiếng Việt}}{\text{Số từ tiếng gốc}} \in [1.20, 1.35]$$
- Nếu Budget Ratio vượt quá $1.35$, Agent tự động cô đọng mệnh đề hành chính, loại bỏ từ đệm nhưng giữ nguyên 100% thuật ngữ chuyên ngành và dữ liệu số.
- Tuyệt đối cấm viết tắt sai quy chuẩn, cấm bịa đặt số liệu.

---

### GIAI ĐOẠN 3: LẬP TRÌNH BỐ CỤC TYPST 1:1 HOẶC DÀN TRANG IN-PLACE
Agent lựa chọn một trong hai phương thức dàn trang:
- **Phương thức 1: Tự động hóa qua Typst 1:1 In-Place Engine (Khuyến nghị cho PDF phức tạp):**
  ```bash
  python3 .agents/skills/dich-giu-dinh-dang/scripts/typst_overlay.py \
      --pdf "<pdf_path>" \
      --blocks "<process_dir>/merged_ejv.json" \
      --lang vi \
      --output "<process_dir>/draft.pdf"
  ```
- **Phương thức 2: Dựng file mã nguồn Typst tùy biến (`document.typ`):**
  - Dựng file mã nguồn bố cục `document.typ` mô phỏng 1:1 cấu trúc hình học:
    - Header, Footer, số trang đối xứng.
    - Phân cột động với `#set columns(2, gutter: 14pt)`.
    - Cân bằng đáy hai cột qua `#colbreak()`.
    - Chèn biểu đồ và bảng biểu giữ nguyên tỷ lệ khung hình.
- **Phương thức 3: Headless CLI qua BabelDOC Bridge (Khi có Ollama cục bộ):**
  ```bash
  python3 scripts/babeldoc_bridge.py \
      --input "<pdf_path>" \
      --lang-in ja --lang-out vi \
      --service ollama \
      --output-dir "<output_dir>"
  ```

---

### GIAI ĐOẠN 4: BIÊN DỊCH PDF & ĐỐI CHIẾU THỊ GIÁC
- Nếu sử dụng Phương thức 2, biên dịch Typst ra file PDF tạm:
  ```bash
  typst compile "<process_dir>/document.typ" "<process_dir>/draft.pdf"
  ```
- Kiểm tra số trang: bắt buộc $N_{\text{dịch}} == N_{\text{gốc}}$. Nếu bị tràn thêm trang, tự động hạ font-size từ 10pt xuống 9.5pt hoặc thu nhỏ gutter.

---

### GIAI ĐOẠN 5: CỔNG KIỂM TOÁN ĐỐI CHIẾU 1:1 & ZERO CJK QUALITY GATE
Chạy các công cụ kiểm toán đối chiếu:
1. **Kiểm tra hình học và ngân sách dòng (Parity Audit):**
   ```bash
   python3 .agents/skills/dich-giu-dinh-dang/scripts/verify_layout_parity.py --source "<pdf_path>" --target "<process_dir>/draft.pdf"
   ```
2. **Kiểm tra tỷ lệ lưu giữ và quét sạch 100% ký tự nguồn (Retention Audit):**
   ```bash
   python3 .agents/skills/dich-giu-dinh-dang/scripts/verify_retention.py --source "<pdf_path>" --target "<process_dir>/draft.pdf" --output "<process_dir>/retention_report.json"
   ```
- Điều kiện xuất bản: Bắt buộc đạt **100% PASS** trên toàn bộ các trang và **0 khối chữ CJK gốc sót lại**.
- Nếu có trang bị FAIL: Agent tự động tinh chỉnh dãn dòng, kiểm tra lại từ điển dịch và biên dịch lại.

---

### GIAI ĐOẠN 6: XUẤT BẢN & BÀN GIAO THÀNH PHẨM
- Sao chép file PDF đạt chuẩn sang thư mục xuất bản:
  ```bash
  cp "<process_dir>/draft.pdf" "<output_dir>/<tên_file>_dich_giu_dinh_dang.pdf"
  ```
- Báo cáo kết quả ngắn gọn và cung cấp đường dẫn tệp tin cho người dùng.
</instructions>

---

<constraints>
## NĂM ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS)
1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY:** 100% dịch thuật và định dạng thực hiện bằng mô hình nội bộ và Typst cục bộ.
2. ❌ **CẤM LÀM TRÀN SỐ TRANG:** Số trang bản dịch bắt buộc phải khớp 1:1 với bản gốc.
3. ❌ **CẤM LÀM ĐEN NỀN CON DẤU:** Bắt buộc áp dụng SMask Alpha Compositing trên nền trắng.
4. ❌ **CẤM ĐÈ CHỮ LÊN KHUNG HOA VĂN:** Bắt buộc tuân thủ khoảng cách an toàn (Safe Zone Margins).
5. ❌ **CẤM XUẤT FILE VÀO CODEBASE:** File PDF thành phẩm bắt buộc xuất ra `<output_dir>` (`~/Downloads/`).
</constraints>

---

<working_ledger>
## ĐỊNH DẠNG LƯU VẾT TIẾN TRÌNH VẬT LÝ
Toàn bộ tiến trình làm việc được lưu vết trong thư mục `<process_dir>`:
- `assets/`: Chứa toàn bộ hình ảnh, biểu đồ và con dấu trong suốt đã bóc tách.
- `document.typ`: File mã nguồn định dạng Typst.
- `parity_rules.json`: Bộ quy tắc kiểm toán ngân sách dòng và đồ họa.
- `parity_report.json`: Báo cáo đối chiếu 1:1 thực tế giữa bản dịch và bản gốc.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
Trước khi bàn giao kết quả cho người dùng, Agent kiểm tra:
1. ✅ **Tỷ lệ trang 1:1:** $N_{\text{dịch}} == N_{\text{gốc}}$ không thừa thiếu trang nào.
2. ✅ **Đồ họa nguyên vẹn:** Toàn bộ biểu đồ đa phần tử, sơ đồ, logo sắc nét 300 DPI.
3. ✅ **Con dấu trong suốt:** Con dấu đỏ và chữ ký không có viền đen hoặc vệt bẩn nền.
4. ✅ **Khung viền an toàn:** Nội dung văn bản nằm gọn trong khung hoa văn.
5. ✅ **Kiểm toán Parity:** Đạt 100% PASS qua `verify_layout_parity.py`.
6. ✅ **Tự động gắn cờ nghi ngờ (Confidence Flagging):** Khi OCR hoặc nhận diện văn bản mờ, tự động gắn cờ `[CẦN XÁC MINH]` để xin ý kiến con người.
7. ✅ **Khử dấu vết AI:** Cấm em dash `—`, cấm Oxford comma `, và`, văn phong hành chính dịch chuẩn tự nhiên.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Khung chat chỉ hiển thị bản tóm tắt ngắn gọn:
  - Tên tài liệu, số trang (1:1), ngôn ngữ dịch.
  - Tình trạng bảo toàn đồ họa (con dấu trong suốt, biểu đồ đa phần tử, khung viền).
  - Kết quả kiểm toán đối chiếu định dạng (Parity Audit: 100% PASS).
  - Đường dẫn tuyệt đối đến file PDF hoàn chỉnh trong `<output_dir>`.
- Không xả mã lệnh thô hoặc danh sách sóng âm vào khung chat.
</delivery_protocol>
