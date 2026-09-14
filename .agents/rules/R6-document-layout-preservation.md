# LUẬT R6: TIÊU CHUẨN BẢO TOÀN BỐ CỤC & ĐỒ HỌA VĂN BẢN (RETAIN-PDF LAYOUT PRESERVATION STANDARD)

> Áp dụng bắt buộc cho mọi kỹ năng bóc tách, dịch thuật và xuất bản tài liệu PDF đa trang (`ejv-translate`, `boc-tach-pdf`, `xu-ly-van-phong`) trong AI Workforce.
> Đảm bảo khi xử lý bất kỳ văn bản chuyên khảo, công văn, kỷ yếu y khoa, tài liệu hướng dẫn hay giấy chứng nhận nào, thành phẩm dịch đầu ra PHẢI bảo toàn 100% tài nguyên đồ họa, giữ đúng tỷ lệ 1:1 và cấu trúc bố cục như tài liệu gốc.

---

## 1. 5 TRỤ CỘT KỸ THUẬT BẢO TOÀN ĐỊNH DẠNG (5 IMMUTABLE PILLARS)

### 🏛️ TRỤ CỘT 1: CHUẨN GIẢI MÃ MẶT NẠ MỀM TRONG SUỐT (SMASK TRANSPARENCY PROTOCOL)
1. **Bản chất kỹ thuật PDF**:
   - Nhiều con dấu đỏ, chữ ký điện tử hoặc logo được nhúng trong PDF dưới dạng 2 đối tượng luồng riêng biệt:
     - Đối tượng ảnh màu RGB (`xref`) nén JPEG (DCTDecode). Vùng nền xung quanh con dấu trong file JPEG này thường chứa các điểm ảnh màu đen `RGB = (0, 0, 0)`.
     - Đối tượng mặt nạ mềm (`/SMask` hoặc `smask_xref`): Luồng đơn sắc (DeviceGray) quy định kênh độ trong suốt (Alpha). Vùng giá trị bằng 0 là trong suốt, giá trị $>0$ là nét vẽ con dấu.
2. **Quy tắc cấm trích xuất thô (No Raw Extraction)**:
   - **TUYỆT ĐỐI CẤM** dùng lệnh trích xuất thô `Pixmap(doc, xref).save(...)` mà bỏ qua `smask`. Hành vi này sẽ giữ nguyên nền đen của JPEG, gây lỗi đen kịt nền con dấu/chữ ký trên trang dịch.
3. **Quy trình giải mã bắt buộc**:
   - Khi `smask_xref > 0`, bắt buộc trích xuất đồng thời `xref` và `smask_xref`.
   - Tính toán hòa trộn Alpha Compositing trên nền trắng (`white_bg * (1 - alpha) + rgb * alpha`) hoặc xuất thành ảnh PNG 4 kênh (`RGBA`) có kênh alpha chuẩn xác.

---

### 🏛️ TRỤ CỘT 2: TRÍCH XUẤT TOÀN VẸN BIỂU ĐỒ ĐA PHẦN TỬ (MULTI-PANEL SUBPLOT BOUNDING)
1. **Nhận diện biểu đồ phức hợp**:
   - Các hình vẽ khoa học, biểu đồ kiểm soát chất lượng (như $\bar{X} - R$ control chart) thường chứa nhiều đồ thị con (subplots) xếp theo ma trận (ví dụ: 3 cột $\times$ 2 hàng = 6 đồ thị con, hoặc 1 cột $\times$ 2 hàng = 2 đồ thị con).
2. **Quy tắc bao trọn biên giới tọa độ (Full Bounding Rule)**:
   - Bắt buộc quét và xác định bounding box bao trọn:
     - Toàn bộ hàng đồ thị trên ($\bar{X}$ mean chart) và hàng đồ thị dưới ($R$ range chart).
     - Toàn bộ trục tung (thang nồng độ, đơn vị $mmol/L$).
     - Toàn bộ trục hoành (thước chia số ngày theo dõi, ví dụ $1, 4, 7\dots 34$, nhãn thời gian `[経過日数]`).
     - Các đường giới hạn thống kê chuẩn: Giới hạn kiểm soát trên (UCL), Giới hạn kiểm soát dưới (LCL), đường trung bình ($\bar{\bar{X}}, \bar{R}$).
3. **Cắt bỏ phần chú thích ngôn ngữ cũ để chèn chú thích dịch**:
   - Chỉ cắt gọn phần chữ chú thích tiếng gốc (ví dụ `図4...`, `Figure 4...`) ở đáy hình để Typst/DOCX chèn chú thích tiếng Việt chuẩn mực ngay dưới hình mà không bị trùng lặp 2 thứ tiếng.

---

### 🏛️ TRỤ CỘT 3: CÔ LẬP KHUNG VIỀN HOA VĂN & LỀ AN TOÀN (ORNATE FRAME & SAFE ZONE MARGINS)
1. **Tách rời Khung viền và Nội dung lõi**:
   - Với văn bản trang trọng có khung hoa văn mạ vàng/họa tiết cổ điển (Bằng khen, Giấy chứng nhận, Chứng chỉ):
   - Tạo file khung viền nền sạch (`certificate_frame.png`) bằng cách xóa trắng (clean/whitewash) toàn bộ vùng chữ bên trong lõi, giữ nguyên vẹn 100% khung hoa văn bao quanh.
2. **Trích xuất thực thể đồ họa độc lập**:
   - Tách riêng logo màu ở đỉnh (ví dụ: Logo JSTB `top_logo.png`) ở độ phân giải cao (300 DPI).
   - Tách riêng con dấu triện đỏ vuông pháp nhân (`seal_square.png`) ở độ phân giải cao.
3. **Thiết lập vùng an toàn chống đè viền (Safe Zone Margin)**:
   - Khoảng cách lề nội dung (`margin`) bắt buộc phải cách xa chi tiết hoa văn nhô ra sâu nhất ít nhất $15 - 20\text{pt}$ (Ví dụ: `top: 105pt, bottom: 90pt, x: 75pt`).
   - CẤM sử dụng các khối hộp thẻ (cards/rectangles có viền màu hiện đại) đè lên khung hoa văn cổ điển. Sử dụng bảng căn lề kiểu Nhật trang nhã (`Tên cơ sở : ...`, `Địa chỉ : ...`).

---

### 🏛️ TRỤ CỘT 4: CÂN BẰNG BỐ CỤC ĐA CỘT & NGÂN SÁCH CHỮ (MULTI-COLUMN BALANCE & TYPOGRAPHY BUDGETING)
1. **Bù trừ độ giãn nở ngôn ngữ**:
   - Bản dịch tiếng Việt thường dài hơn tiếng Nhật hoặc tiếng Anh từ **25% đến 35%**.
   - Đối với trang kỷ yếu học thuật/báo cáo 2 cột dày đặc có chứa nhiều hình ảnh, bắt buộc áp dụng:
     - Cỡ chữ thân bài: `5.8pt - 6.2pt`.
     - Khoảng cách dãn dòng (`leading`): `0.24em - 0.26em`.
     - Cỡ chữ tài liệu tham khảo/chú thích: `5.0pt - 5.4pt`, dãn dòng `0.20em - 0.22em`.
2. **Cân đối đáy 2 cột (Column Height Harmonization)**:
   - Phải tính toán khối lượng chữ trước khi ngắt cột (`#colbreak()`).
   - Phân bổ các đoạn văn bản sao cho đáy của Cột 1 và đáy của Cột 2 kết thúc ngang hàng nhau. Tuyệt đối tránh tình trạng Cột 1 dài chạm đáy trong khi Cột 2 bị bỏ trống một khoảng trắng lớn, hoặc chữ bị tràn sang trang kế tiếp làm phá vỡ tỷ lệ trang 1:1.

---

### 🏛️ TRỤ CỘT 5: CỔNG KIỂM TOÁN ĐỐI CHIẾU ĐỊNH DẠNG 1:1 (AUTOMATED PARITY QUALITY GATE)
Trước khi bàn giao bất kỳ file dịch hoàn chỉnh nào cho người dùng, Agent BẮT BUỘC phải chạy công cụ kiểm toán đối chiếu tự động (`verify_layout_parity.py`). Báo cáo phải thỏa mãn 4 tiêu chuẩn cứng:

| Chỉ số kiểm định | Tiêu chuẩn bắt buộc |
|---|---|
| **Tỷ lệ số trang (Page Parity)** | Phải đạt chính xác **1:1** ($N_{\text{dịch}} == N_{\text{gốc}}$). Không được phát sinh thêm trang thừa hoặc thiếu trang. |
| **Bảo toàn hình ảnh (Image Fidelity)** | $100\%$ số lượng hình ảnh, biểu đồ, con dấu, sơ đồ và khung hoa văn phải xuất hiện đầy đủ trên từng trang tương ứng. |
| **Bảo toàn bảng biểu (Table Parity)** | Toàn bộ các bảng số liệu, bảng thông số kỹ thuật phải được tái tạo nguyên vẹn cấu trúc hàng - cột. |
| **Ngân sách dòng (Line Count Budget)** | Số dòng văn bản trên mỗi trang phải nằm trong khoảng mục tiêu $[Min, Max]$ tương đồng với mật độ trang gốc, sai số $\le \pm 10\%$. |

> ⚠️ **Quy tắc nghiệm thu:** Nếu kết quả kiểm toán chưa đạt **100% PASS**, Agent KHÔNG ĐƯỢC PHÉP báo cáo hoàn thành. Phải tự động điều chỉnh dãn dòng/cỡ chữ/bố cục cho đến khi đạt chuẩn hoàn hảo.
