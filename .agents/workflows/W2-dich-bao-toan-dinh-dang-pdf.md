---
name: W2-dich-bao-toan-dinh-dang-pdf
display-name: Dịch Bảo Toàn Định Dạng PDF (Retain-PDF)
description: "Quy trình dịch thuật PDF chuyên khảo 2 cột, bảng biểu số liệu, đồ thị đa phần tử, con dấu pháp nhân và khung viền hoa văn bảo toàn 100% bố cục và tỷ lệ trang 1:1 theo chuẩn Luật R6."
trigger: "Dịch bảo toàn định dạng PDF, Retain-PDF, dịch PDF giữ nguyên bố cục và hình ảnh, dịch PDF 2 cột, dịch chứng chỉ có con dấu"
action: retain_pdf_translation
---

# Workflow W2: Dịch Bảo Toàn Định Dạng PDF (Retain-PDF SOP)

> **Mục tiêu:** Vận hành quy trình dịch thuật tài liệu PDF phức tạp (chuyên khảo y khoa/khoa học 2 cột, catalogue sản phẩm, giấy chứng nhận con dấu đỏ, biểu đồ kiểm soát chất lượng) giữa **Tiếng Nhật (ja) ↔ Tiếng Việt (vi) ↔ Tiếng Anh (en)** đảm bảo:
> 1. Tỷ lệ trang 1:1 tuyệt đối ($N_{\text{dịch}} == N_{\text{gốc}}$).
> 2. Bảo toàn 100% hình ảnh, sơ đồ, biểu đồ con (subplots) sắc nét chuẩn 300 DPI.
> 3. Con dấu đỏ pháp nhân và chữ ký trong suốt tự nhiên qua giải mã kênh Alpha SMask (không đen nền).
> 4. Bảo vệ khung viền hoa văn mạ vàng và lề an toàn (Safe Zone Margins).
> 5. Cổng kiểm định chất lượng: 100% PASS qua `verify_layout_parity.py` và `verify_retention.py` (0 khối chữ nguồn sót lại).
> 6. **Zero External API:** Chạy hoàn toàn bằng AI nội bộ Antigravity IDE hoặc Ollama cục bộ.

---

## 1. NGUYÊN TẮC CỐT LÕI (5 TRỤ CỘT LUẬT R6)

1. **Trụ cột 1 — Mặt nạ mềm SMask trong suốt:**
   - Trích xuất kênh Alpha mặt nạ mềm qua `pdf_asset_extractor.py`, xóa bỏ viền đen/vết bẩn nền con dấu và chữ ký.
2. **Trụ cột 2 — Trích xuất toàn vẹn biểu đồ đa phần tử:**
   - Bounding box bao trọn cả cụm đồ thị $\bar{X}-R$, đường giới hạn UCL/LCL và các trục tọa độ.
3. **Trụ cột 3 — Cô lập khung viền & Vùng đệm an toàn:**
   - Thiết lập Safe Zone Margins (top $\ge 105\text{pt}$, bottom $\ge 90\text{pt}$, x $\ge 75\text{pt}$) chống đè chữ lên hoa văn.
4. **Trụ cột 4 — Cân bằng bố cục đa cột & Ngân sách chữ:**
   - Tự động gom cụm cột (Column Clustering) chống đọc chéo hàng; bù trừ độ giãn nở tiếng Việt (+25% đến +35%) bằng công nghệ co chữ động (Typst Binary Search Font Auto-Fit).
5. **Trụ cột 5 — Cổng kiểm toán đối chiếu 1:1:**
   - Kiểm tra đối chiếu số trang, số khối ảnh, cấu trúc bảng và quét sạch 100% ký tự nguồn trước khi xuất bản.

---

## 2. QUY TRÌNH THỰC THI TỰ ĐỘNG (6 PHA SẠCH)

### PHA 1: TIẾP NHẬN & PHÂN TÍCH HÌNH HỌC TÀI LIỆU
1. **Xác định đường dẫn:**
   - File gốc: `<file_goc>` (.pdf)
   - Thư mục tạm: `<workspace>/_process/retain_[stem]/`
   - Thư mục xuất bản: `<output_dir>` (mặc định: `~/Downloads/`)
2. **Quét cấu trúc và trích xuất tài sản:**
   ```bash
   python3 .agents/skills/ejv-translate/scripts/pdf_asset_extractor.py extract-images \
       --pdf "<file_goc>" \
       --output-dir "<process_dir>/assets/"
   ```

### PHA 2: BÓC TÁCH KHỐI NGỮ NGHĨA & BẢO VỆ CÔNG THỨC
1. **Bóc tách văn bản nhận diện đa cột (Column-aware):**
   ```bash
   python3 .agents/skills/ejv-translate/scripts/extract_text.py \
       --input "<file_goc>" \
       --output "<process_dir>/blocks_source.json"
   ```
   *Lưu ý: Script tự động bảo vệ công thức toán/hóa ($Na^+$, $K^+$, $\bar{X}$, $\pm 1.5$) bằng mã đại diện `<formula_N>`.*

### PHA 3: DỊCH THUẬT NỘI BỘ (ZERO EXTERNAL API)
- **Phương thức 1 (Mặc định - IDE Agent):**
  - Tác nhân Antigravity trong IDE đọc trực tiếp các khối văn bản từ `blocks_source.json`.
  - Dịch sang ngôn ngữ đích (`vi`, `en`, hoặc `ja`), giữ nguyên vẹn mã `<formula_N>`, các nhãn số và ký hiệu đơn vị.
  - Ghi vào `<process_dir>/merged_ejv.json`.
- **Phương thức 2 (Headless qua Ollama cục bộ):**
  ```bash
  python3 scripts/babeldoc_bridge.py \
      --input "<file_goc>" \
      --lang-in ja \
      --lang-out vi \
      --service ollama \
      --output-dir "<output_dir>"
  ```

### PHA 4: ĐỊNH TRÌNH BỐ CỤC TYPST 1:1
- Thực thi dàn trang Typst Binary Search Auto-Fit:
  ```bash
  python3 .agents/skills/ejv-translate/scripts/typst_overlay.py \
      --pdf "<file_goc>" \
      --blocks "<process_dir>/merged_ejv.json" \
      --lang vi \
      --output "<process_dir>/draft_translated.pdf"
  ```

### PHA 5: CỔNG KIỂM ĐỊNH CHẤT LƯỢNG (QUALITY GATE)
1. **Kiểm tra tỷ lệ trang và đồ họa 1:1:**
   ```bash
   python3 .agents/skills/ejv-translate/scripts/verify_layout_parity.py \
       --source "<file_goc>" \
       --target "<process_dir>/draft_translated.pdf"
   ```
2. **Kiểm tra sạch chữ nguồn (Zero Residual CJK Blocker):**
   ```bash
   python3 .agents/skills/ejv-translate/scripts/verify_retention.py \
       --source "<file_goc>" \
       --target "<process_dir>/draft_translated.pdf" \
       --output "<process_dir>/retention_audit.json"
   ```
   *Điều kiện vượt qua: Bắt buộc đạt điểm Retention $\ge 90\%$ và phát hiện **0 khối chữ gốc sót lại**.*

### PHA 6: BÀN GIAO THÀNH PHẨM (ANTI-REPO BLOAT)
- Sao chép file PDF nghiệm thu sang `<output_dir>`:
  ```bash
  cp "<process_dir>/draft_translated.pdf" "<output_dir>/<stem>_translated_<lang>.pdf"
  ```
- Dọn dẹp các file cache tạm thời trong `_process/` nếu cần.
- Báo cáo kết quả và cung cấp đường dẫn tệp tin cho người dùng.
