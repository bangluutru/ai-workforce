---
name: W2-dich-giu-dinh-dang
display-name: Dịch Giữ Định Dạng
description: Quy trình SOP 6 giai đoạn chuẩn hóa Dịch Giữ Định Dạng tài liệu PDF đa trang bảo toàn 100% đồ họa, biểu đồ đa phần tử, con dấu trong suốt và bố cục 1:1 theo Luật R6.
trigger: Dịch giữ định dạng, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh, dịch tài liệu có con dấu và biểu đồ
---

# Workflow W2: Dịch Giữ Định Dạng (Retain-PDF SOP)

> **Mục tiêu:** Hệ thống hóa toàn diện quy trình xử lý tài liệu PDF phức tạp (kỷ yếu khoa học 2 cột, biểu đồ kiểm soát chất lượng đa phần tử, con dấu pháp nhân, chứng nhận khung hoa văn mạ vàng) để bảo đảm khi gặp bất kỳ văn bản tương tự nào, quy trình xử lý sẽ thực hiện chính xác 100% như tài liệu mẫu chuẩn.
> **Căn cứ pháp lý & kỹ thuật:** Luật R0 (Git-Sync Mandatory), Luật R4 (Skill Standard v1.2), Luật R6 (Retain-PDF Layout Preservation Standard).

---

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi thành phẩm xuất bản (`.pdf`, `.docx`) PHẢI được lưu tại `<output_dir>` do người dùng chỉ định hoặc **Mặc định: `~/Downloads/`**.
> - Thư mục trung gian xử lý phải nằm tại `_process/<tên_tài_liệu>/` (đã gitignore). Tuyệt đối KHÔNG xuất file kết quả vào thư mục gốc repository.

---

## OUTPUT (Khóa trước)
1. **Tệp PDF dịch hoàn chỉnh:** Nằm tại `<output_dir>/[Ten_Tai_Lieu]_preserved_[lang].pdf` với tỷ lệ trang chính xác 1:1 ($N_{\text{dịch}} == N_{\text{gốc}}$).
2. **Đồ họa bảo toàn 100%:** Toàn bộ biểu đồ đa phần tử, sơ đồ quy trình, logo, con dấu đỏ trong suốt và khung hoa văn sắc nét (300 DPI).
3. **Chứng chỉ kiểm định đối chiếu định dạng (Parity Audit):** Báo cáo từ `verify_layout_parity.py` đạt **100% PASS** trên tất cả các trang về: Số lượng ảnh, Bảng biểu và Ngân sách dòng.

---

## INPUT (Truy ngược)
1. **Từ Người dùng:**
   - File PDF tài liệu nguồn (`<file_goc>`).
   - Ngôn ngữ dịch đích (`vi`, `en`, `ja` - mặc định: `vi`).
   - Thư mục lưu kết quả (`<output_dir>` - mặc định: `~/Downloads/`).
2. **Từ Hệ thống AIWF:**
   - Bộ công cụ trích xuất đồ họa: `scripts/pdf_asset_extractor.py` (hoặc `<skill_dir>/scripts/pdf_asset_extractor.py`).
   - Bộ công cụ kiểm toán đối chiếu: `scripts/verify_layout_parity.py`.
   - Tiêu chuẩn bảo toàn định dạng: `.agents/rules/R6-document-layout-preservation.md`.

---

## PROCESS (6 GIAI ĐOẠN THỰC THI CHUẨN)

### 🚀 Giai đoạn 1: Khám phá & Trích xuất Đồ họa Chuyên sâu (Asset Extraction)
Agent quét toàn bộ trang trong tài liệu nguồn và phân loại đối tượng đồ họa:
1. **Giải mã Mặt nạ mềm SMask (Con dấu đỏ & Chữ ký):**
   - Chạy script trích xuất:
     ```bash
     python3 scripts/pdf_asset_extractor.py extract-images --pdf "<file_goc>" --output-dir "_process/<stem>/assets/"
     ```
   - Tự động phát hiện `/SMask` để hòa trộn kênh Alpha Compositing trên nền trắng, triệt tiêu hoàn toàn lỗi bôi đen nền con dấu.
2. **Trích xuất Biểu đồ Đa phần tử (Subplot Bounding):**
   - Đối với biểu đồ khoa học có nhiều đồ thị con (ví dụ: Biểu đồ kiểm soát chất lượng $\bar{X} - R$ gồm 6 đồ thị dialysate + 2 đồ thị B-solution):
     ```bash
     python3 scripts/pdf_asset_extractor.py crop-box --pdf "<file_goc>" --page <P> --bbox "<x0>,<y0>,<x1>,<y1>" --output "_process/<stem>/assets/fig_<name>.png" --dpi 300
     ```
   - **Quy tắc bắt buộc:** Bounding box phải bao trọn cả hàng đồ thị $\bar{X}$ (trên) và hàng $R$ (dưới), các vạch chia đơn vị trục tung, thang chia số ngày theo dõi trục hoành và các đường giới hạn UCL/LCL. Cắt bỏ chú thích tiếng gốc ở chân hình để chèn chú thích dịch.
3. **Cô lập Khung viền Hoa văn (Ornate Frame Isolation):**
   - Đối với trang Bằng khen / Giấy chứng nhận có viền mạ vàng hoặc họa tiết cổ điển:
     ```bash
     python3 scripts/pdf_asset_extractor.py isolate-frame --pdf "<file_goc>" --page <P> --inner-rect "<x0>,<y0>,<x1>,<y1>" --output "_process/<stem>/assets/frame_page_<P>.png"
     ```
   - Tách riêng Logo pháp nhân ở đỉnh và Con dấu vuông ở đáy thành các file PNG độc lập.

---

### 🚀 Giai đoạn 2: Trích xuất Cấu trúc Nội dung & Bảng biểu
1. **Trích xuất cấu trúc văn bản:**
   - Dùng `extract_text.py` trích xuất các khối văn bản theo thứ tự tọa độ dọc $y_0$ tự nhiên.
   - Quét và loại bỏ sạch watermark in mờ (diagonal tracking watermark).
2. **Trích xuất hình học bảng biểu:**
   - Dùng `table_extractor.py` quét ma trận hàng - cột, tách riêng văn bản nằm trong ô bảng để tránh trùng lặp.

---

### 🚀 Giai đoạn 3: Dịch Ngữ cảnh Sâu & Chuẩn hóa Ngân sách Chữ
1. **Dịch thuật chính xác (Zero External API):**
   - Agent trực tiếp dịch toàn bộ nội dung sang ngôn ngữ đích theo văn phong hành chính/khoa học chuẩn mực.
   - Giữ nguyên 100% số liệu đo lường, công thức hóa học ($Na^+, K^+, Ca^{2+}, Cl^-, HCO_3^-$), đơn vị tính ($mmol/L, mS/cm, pH$).
2. **Tính toán Ngân sách Chữ & Bù trừ Dãn nở (+25-35%):**
   - Văn bản tiếng Việt dài hơn 25-35% so với tiếng Nhật gốc.
   - Đối với trang bài báo/kỷ yếu 2 cột có hình ảnh dày đặc:
     - Đặt font size: `5.8pt - 6.2pt`.
     - Đặt dãn dòng (`leading`): `0.24em - 0.26em`.
     - Chú thích & tham khảo: `5.0pt - 5.4pt`, dãn dòng `0.20em`.

---

### 🚀 Giai đoạn 4: Dựng Bố cục Đa tầng (Typst Layout Synthesis)
Agent sử dụng công cụ Typst để dựng cấu trúc trang theo đúng từng loại hình tài liệu:
1. **Trang Nghiên cứu 2 Cột (Two-Column Journal):**
   - Thiết lập cấu trúc `#columns(2, gutter: 12pt)`.
   - Chèn các biểu đồ đa phần tử đúng vị trí (chiếm 1 cột hoặc trải ngang 2 cột `#place` / khối toàn trang).
   - Sử dụng lệnh `#colbreak()` chủ động trước đoạn kết luận/thảo luận cuối để đáy Cột 1 và đáy Cột 2 cân bằng ngang hàng nhau.
2. **Trang Giấy chứng nhận Khung hoa văn (Ornate Certificate):**
   - Đặt file `frame_page_<P>.png` làm hình nền trang (`background: image(...)`).
   - Thiết lập **Safe Zone Margins** an toàn tuyệt đối: `top: 105pt, bottom: 90pt, x: 75pt`.
   - Đặt Logo JSTB ở đỉnh trang (`width: 32pt`).
   - Trình bày nội dung chứng nhận dạng bảng căn lề Nhật trang nhã (`Tên cơ sở : ...`, `Địa chỉ : ...`).
   - Đặt con dấu đỏ ở góc phải dưới cạnh ngày cấp và chữ ký Chủ tịch, đảm bảo cách xa khung hoa văn tối thiểu 20pt.
3. **Trang Bảng biểu Kỹ thuật Phức hợp (Multi-table Pages):**
   - Sử dụng `#table(columns: ..., stroke: 0.5pt + luma(120))` giữ nguyên vẹn cấu trúc gộp ô (colspan/rowspan).

---

### 🚀 Giai đoạn 5: Biên dịch PDF & Đóng gói Thành phẩm
1. Biên dịch từng trang Typst thành PDF vector chất lượng cao:
   ```bash
   typst compile _process/<stem>/page_<P>.typ _process/<stem>/page_<P>.pdf
   ```
2. Hợp nhất các trang thành tài liệu duy nhất lưu tại `<output_dir>`:
   ```bash
   python3 _process/<stem>/build_complete_preserved_pdf.py
   ```

---

### 🚀 Giai đoạn 6: Cổng Kiểm toán Đối chiếu Định dạng 1:1 (Quality Gate)
Trước khi bàn giao kết quả cho người dùng, Agent BẮT BUỘC phải kích hoạt công cụ kiểm toán đối chiếu tự động:
```bash
python3 scripts/verify_layout_parity.py "<output_dir>/[Ten_Tai_Lieu]_preserved_[lang].pdf"
```

**Tiêu chí Nghiệm thu Tuyệt đối:**
- ✅ **100% PASS Số trang:** Tỷ lệ chính xác 1:1 so với bản gốc ($N_{\text{target}} == N_{\text{source}}$).
- ✅ **100% PASS Tài nguyên Đồ họa:** Toàn bộ biểu đồ, con dấu, logo và khung viền hiển thị đầy đủ, sắc nét, không bị mất hoặc biến dạng.
- ✅ **100% PASS Ngân sách Dòng:** Mật độ dòng trên mỗi trang đạt chuẩn, không có trang nào bị tràn chữ hay thiếu hụt quá 10%.
- ✅ **Nền Con dấu Chuẩn:** Con dấu đỏ nổi bật trên nền trắng sạch sẽ, không có viền đen hay hộp đen bao quanh.
- ✅ **Không Đè Viền:** Toàn bộ chữ và con dấu nằm gọn trong vùng an toàn, cách khung hoa văn tối thiểu 15-20pt.

> ⚠️ Nếu có bất kỳ trang nào bị **FAIL**, Agent PHẢI tự động quay lại Giai đoạn 4 để tinh chỉnh kích thước chữ, khoảng cách dãn dòng hoặc lề an toàn cho đến khi đạt **100% PASS** trước khi bàn giao!
