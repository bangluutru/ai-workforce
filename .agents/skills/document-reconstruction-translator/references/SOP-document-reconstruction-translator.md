---
name: W2-dich-giu-dinh-dang
display-name: Dịch Giữ Định Dạng
description: Quy trình SOP 7 giai đoạn chuẩn hóa Dịch Giữ Định Dạng tài liệu PDF đa trang bảo toàn 100% đồ họa, biểu đồ đa phần tử, con dấu trong suốt, bố cục 1:1, cơ chế ánh xạ kép chống dịch sót và thẩm định thuật ngữ chuyên ngành theo Luật R6.
trigger: Dịch giữ định dạng, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh, dịch tài liệu có con dấu và biểu đồ
---

# Workflow W2: Dịch Giữ Định Dạng (Retain-PDF SOP v2.0)

> **Mục tiêu:** Hệ thống hóa toàn diện quy trình xử lý tài liệu PDF phức tạp (kỷ yếu khoa học 2 cột, biểu đồ kiểm soát chất lượng đa phần tử, con dấu pháp nhân, chứng nhận khung hoa văn mạ vàng) để bảo đảm khi gặp bất kỳ văn bản tương tự nào, quy trình xử lý sẽ thực hiện chính xác 100% như tài liệu mẫu chuẩn:
> 1. Bảo toàn 100% tài nguyên đồ họa và bố cục hình học tỷ lệ 1:1 so với bản gốc.
> 2. Dịch đầy đủ 100% nội dung (Zero Translation Omission) qua Cơ chế Ánh xạ Kép (Dual-Level Mapping).
> 3. Chuẩn xác 100% thuật ngữ chuyên ngành hẹp thông qua Bước Đánh giá Chuyên ngành Bắt buộc.
> **Căn cứ pháp lý & kỹ thuật:** Luật R0 (Git-Sync Mandatory), Luật R2 (Code Quality), Luật R3 §8 (Zero-Residual Source Text Quality Gate), Luật R4 (Skill Standard v1.2), Luật R6 (Retain-PDF Standard).

---

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi thành phẩm xuất bản (`.pdf`, `.docx`) PHẢI được lưu tại `<output_dir>` do người dùng chỉ định hoặc **Mặc định: `~/Downloads/AIWF_Output/`**.
> - Thư mục trung gian xử lý phải nằm tại `_process/<tên_tài_liệu>/` (đã gitignore). Tuyệt đối KHÔNG xuất file kết quả vào thư mục gốc repository.

---

## OUTPUT (Khóa trước)
1. **Tệp PDF dịch hoàn chỉnh:** Nằm tại `<output_dir>/[Ten_Tai_Lieu]_dich_giu_dinh_dang.pdf` với tỷ lệ trang chính xác 1:1 ($N_{\text{dịch}} == N_{\text{gốc}}$).
2. **Đồ họa bảo toàn 100%:** Toàn bộ biểu đồ đa phần tử, sơ đồ quy trình, logo, con dấu đỏ trong suốt (SMask Alpha) và khung hoa văn sắc nét (300 DPI).
3. **Cổng kiểm toán đối chiếu toàn vẹn 3 lớp (Tri-Layer Quality Gate) đạt 100% PASS:**
   - **Lớp 1 (Parity Audit):** Tỷ lệ trang 1:1, đủ 100% hình ảnh/biểu đồ/con dấu, đủ bảng biểu, số dòng trong ngân sách.
   - **Lớp 2 (Zero Residual Audit):** 0 khối sót ký tự nguồn CJK / ngoại ngữ gốc (Rule R3 §8).
   - **Lớp 3 (Zero Omission & Domain Audit):** 100% khối văn bản có bản dịch hoàn chỉnh (0 placeholder `.`), 100% thuật ngữ khớp Ma trận Chuyên ngành.

---

## INPUT (Truy ngược)
1. **Từ Người dùng:**
   - File PDF tài liệu nguồn (`<file_goc>`).
   - Ngôn ngữ dịch đích (`vi`, `en`, `ja` - mặc định: `vi`).
   - Thư mục lưu kết quả (`<output_dir>` - mặc định: `~/Downloads/AIWF_Output/`).
2. **Từ Hệ thống AIWF:**
   - Bộ công cụ trích xuất đồ họa: `scripts/pdf_asset_extractor.py`.
   - Bộ công cụ dàn trang Typst Smart Reflow: `.agents/skills/dich-giu-dinh-dang/scripts/typst_overlay.py`.
   - Bộ công cụ kiểm toán đối chiếu hình học: `scripts/verify_layout_parity.py`.
   - Bộ công cụ kiểm toán lưu giữ định dạng & quét ký tự nguồn: `scripts/verify_retention.py`.
   - Tiêu chuẩn bảo toàn định dạng: `.agents/rules/R6-document-layout-preservation.md`.

---

## PROCESS (7 GIAI ĐOẠN THỰC THI CHUẨN)

### 🚀 Giai đoạn 1: Khám phá & Trích xuất Đồ họa Chuyên sâu (Asset Extraction)
Agent quét toàn bộ trang trong tài liệu nguồn và phân loại đối tượng đồ họa:
1. **Giải mã Mặt nạ mềm SMask (Con dấu đỏ & Chữ ký):**
   - Chạy script trích xuất:
     ```bash
     python3 scripts/pdf_asset_extractor.py extract-images --pdf "<file_goc>" --output-dir "_process/<stem>/assets/"
     ```
   - Tự động phát hiện `/SMask` để hòa trộn kênh Alpha Compositing trên nền trắng, triệt tiêu hoàn toàn lỗi bôi đen nền con dấu.
2. **Trích xuất Biểu đồ Đa phần tử (Subplot Bounding):**
   - Đối với biểu đồ khoa học có nhiều đồ thị con (ví dụ: Biểu đồ kiểm soát chất lượng $\bar{X} - R$ gồm nhiều đồ thị dialysate / B-solution):
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
   - Dùng PyMuPDF trích xuất các khối văn bản theo thứ tự tọa độ dọc $y_0$ tự nhiên.
   - Nhận diện các dòng liên tiếp có khoảng cách dọc $< 8\text{pt}$ để chuẩn bị dữ liệu gộp đoạn văn (Paragraph Box-Merging).
2. **Trích xuất hình học bảng biểu:**
   - Quét ma trận hàng - cột, bảo toàn liên kết ngữ nghĩa giữa các ô (Kế hoạch $\leftrightarrow$ Kết quả), tránh để sót các dòng bị ngắt ngẫu nhiên trong PDF.

---

### 🚀 Giai đoạn 3: Đánh giá Chuyên ngành & Lập Ma trận Thuật ngữ (Mandatory Domain Review)
1. **Xác định phân ngành kỹ thuật sâu**:
   - Thận học & Lọc máu ngoài cơ thể, Tim mạch can thiệp, Dược lý, Tiêu chuẩn kỹ thuật ISO/JIS, Kế toán - Thuế, Sở hữu trí tuệ...
2. **Thiết lập Ma trận Tra cứu Thuật ngữ Chuyên ngành (Domain Terminology Matrix)**:
   - Đối chiếu quy chuẩn quản lý nhà nước (Bộ Y tế, Bộ Tài chính...).
   - Lập danh mục thuật ngữ chuẩn mực nạp vào bộ dịch.
   - **Nghiêm cấm tuyệt đối dịch máy thô từng chữ (word-by-word)** làm biến dạng thuật ngữ chuyên ngành (ví dụ: `血液浄化` = "Kỹ thuật lọc máu ngoài cơ thể", cấm "Làm sạch máu"; `維持透析患者` = "Bệnh nhân lọc máu chu kỳ", cấm "Bệnh nhân duy trì thẩm tách"; `プラスチックカニューラ` = "Kim luồn nhựa / Canuyn nhựa lọc máu", cấm "Ống thông nhựa").

---

### 🚀 Giai đoạn 4: Dịch thuật Ánh xạ Kép & Quản trị Ngân sách Từ ngữ (Dual-Level Mapping)
1. **Cơ chế Ánh xạ Kép (Dual-Level Mapping)**:
   - Tạo file từ điển `merged_ejv.json` bắt buộc chứa 2 cấp độ:
     - **Cấp độ Đoạn Gộp (`combined_text`)**: Toàn văn bản dịch của đoạn văn gộp nhiều dòng liên tiếp.
     - **Cấp độ Khối Đơn & Từng Dòng (`single_block` / `line_text`)**: Bản dịch của từng block con dự phòng khi không gộp được đoạn.
   - **Tuyệt đối cấm gán placeholder dấu chấm `.`**, khoảng trắng rỗng hoặc câu cắt cụt.
2. **Quản trị Ngân sách Chữ & Bù trừ Dãn nở (+25-35%):**
   - Áp dụng Live Formulas: $\text{Budget Ratio} \in [1.20, 1.35]$.
   - Đối với trang bài báo/kỷ yếu 2 cột có hình ảnh dày đặc:
     - Đặt font size: `5.8pt - 6.2pt`.
     - Đặt dãn dòng (`leading`): `0.24em - 0.26em`.
     - Chú thích & tham khảo: `5.0pt - 5.4pt`, dãn dòng `0.20em`.

---

### 🚀 Giai đoạn 5: Dựng Bố cục In-Place qua Typst Smart Reflow Engine v4.0
Agent kích hoạt engine dàn trang:
```bash
python3 .agents/skills/dich-giu-dinh-dang/scripts/typst_overlay.py \
    --pdf "<file_goc>" \
    --blocks "_process/<stem>/merged_ejv.json" \
    --lang vi \
    --output "_process/<stem>/draft.pdf"
```
- **Tự động Gộp Bounding Box Đoạn Văn**: Gộp các dòng liên tiếp thành một box duy nhất ($\min(y0)$ đến $\max(y1)$).
- **Tự co giãn font mềm mại**: Bản dịch tiếng Việt tự động ngắt dòng và co giãn trong phạm vi box gộp, triệt tiêu hoàn toàn lỗi đè dòng.
- **Xóa trắng nền chữ gốc**: Whitewash chính xác lớp chữ cũ và render lớp chữ dịch vector sắc nét.

---

### 🚀 Giai đoạn 6: Biên dịch PDF & Cổng Kiểm toán Đối chiếu Toàn vẹn 3 Lớp (Tri-Layer Quality Gate)
Trước khi bàn giao kết quả cho người dùng, Agent BẮT BUỘC phải chạy chuỗi công cụ kiểm toán đối chiếu:

1. **Lớp 1: Kiểm toán Đối chiếu Định dạng Hình học 1:1 (Parity Audit):**
   ```bash
   python3 scripts/verify_layout_parity.py --source "<file_goc>" --target "_process/<stem>/draft.pdf"
   ```
   - ✅ Tỷ lệ số trang đạt chính xác 1:1 ($N_{\text{target}} == N_{\text{source}}$).
   - ✅ Toàn bộ biểu đồ, con dấu trong suốt, logo và khung viền hiển thị đầy đủ, sắc nét 300 DPI.
   - ✅ Mật độ dòng trên mỗi trang đạt chuẩn trong ngân sách mục tiêu ($\pm 10\%$).

2. **Lớp 2: Kiểm toán Quét sạch Ký tự Nguồn (Zero Residual Source Text Audit - Rule R3 §8):**
   ```bash
   python3 scripts/verify_retention.py --source "<file_goc>" --target "_process/<stem>/draft.pdf"
   ```
   - ✅ Đạt điểm lưu giữ định dạng $\ge 95\%$ (Hạng A+).
   - ✅ **Khóa chặn cứng (Hard Blocker):** Chính xác **0 khối chữ nguồn CJK** / câu tiếng gốc còn sót lại.

3. **Lớp 3: Kiểm toán Toàn vẹn Bản dịch & Khớp Thuật ngữ Chuyên ngành (Zero Omission & Domain Audit):**
   - ✅ 100% khối có bản dịch hoàn chỉnh, 0 dấu chấm placeholder `.`.
   - ✅ 100% thuật ngữ kỹ thuật khớp Ma trận Chuyên ngành Giai đoạn 3.

> ⚠️ Nếu có bất kỳ tiêu chí nào chưa đạt **100% PASS**, Agent PHẢI tự động quay lại Giai đoạn 4 hoặc 5 để xử lý dứt điểm trước khi bàn giao!

---

### 🚀 Giai đoạn 7: Xuất bản & Bàn giao Thành phẩm
1. Sao chép file PDF đạt chuẩn sang thư mục xuất bản:
   ```bash
   cp "_process/<stem>/draft.pdf" "<output_dir>/<tên_file>_dich_giu_dinh_dang.pdf"
   ```
2. Báo cáo kết quả theo Giao thức Bàn giao Sạch (Clean Delivery Protocol):
   - Tên tài liệu, số trang (1:1), ngôn ngữ dịch.
   - Chuyên ngành kỹ thuật sâu đã thẩm định và áp dụng chuẩn thuật ngữ.
   - Tình trạng bảo toàn đồ họa (con dấu trong suốt, biểu đồ đa phần tử, khung viền).
   - Kết quả kiểm toán 3 lớp: Parity Audit (100% PASS), Zero Residual CJK (0 khối sót), Zero Omission (100% hoàn chỉnh).
   - Đường dẫn tuyệt đối đến file PDF hoàn chỉnh trong `<output_dir>`.
