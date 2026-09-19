# LUẬT R6: TIÊU CHUẨN BẢO TOÀN BỐ CỤC, ĐỒ HỌA & NỘI DUNG CHUYÊN NGÀNH (RETAIN-PDF STANDARD)

> Áp dụng bắt buộc cho mọi kỹ năng bóc tách, dịch thuật và xuất bản tài liệu PDF đa trang (`dich-giu-dinh-dang`, `ejv-translate`, `boc-tach-pdf`, `xu-ly-van-phong`) trong AI Workforce.
> Đảm bảo khi xử lý bất kỳ văn bản chuyên khảo, công văn, kỷ yếu y khoa/kỹ thuật, tài liệu hướng dẫn hay giấy chứng nhận nào, thành phẩm dịch đầu ra PHẢI:
> 1. Bảo toàn 100% tài nguyên đồ họa và bố cục hình học tỷ lệ 1:1 so với tài liệu gốc.
> 2. Dịch đầy đủ 100% nội dung (Zero Translation Omission) qua cơ chế ánh xạ kép (Dual-Level Mapping).
> 3. Chuẩn xác 100% thuật ngữ chuyên ngành hẹp thông qua Bước Đánh giá Chuyên ngành bắt buộc.

---

## 🏛️ 7 TRỤ CỘT KỸ THUẬT BẢO TOÀN ĐỊNH DẠNG & NỘI DUNG (7 IMMUTABLE PILLARS)

---

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
     - Toàn bộ trục tung (thang nồng độ, đơn vị $mmol/L$, $EU/mL$, $CFU/mL$).
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
   - Tách riêng logo màu ở đỉnh (ví dụ: Logo Hiệp hội JSTB `top_logo.png`) ở độ phân giải cao (300 DPI).
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
3. **Gộp Bounding Box Đoạn Văn (Paragraph Box-Merging Protocol)**:
   - Khi văn bản gốc bị trích xuất thành từng dòng độc lập (single-line boxes có khoảng cách dọc $< 8\text{pt}$), Typst overlay BẮT BUỘC phải tự động gộp các bounding box liên tiếp của cùng một đoạn văn thành một bounding box duy nhất ($\min(y0)$ đến $\max(y1)$).
   - Khi bản dịch tiếng Việt giãn nở (+25-35%), chữ sẽ tự động xuống dòng và tự co giãn font mềm mại trong toàn bộ chiều cao của đoạn văn, **triệt tiêu hoàn toàn lỗi chồng lấn/đè dòng (text collision)**.

---

### 🏛️ TRỤ CỘT 5: CƠ CHẾ ÁNH XẠ KÉP & CHỐNG DỊCH SÓT (DUAL-LEVEL MAPPING & ZERO-OMISSION PROTOCOL)
1. **Nguyên lý Ánh xạ Kép (Dual-Level Mapping)**:
   - Engine dàn trang thông minh (`typst_overlay.py`) gom các dòng thành đoạn dựa trên khoảng cách dọc (`can_merge`).
   - Để triệt tiêu hoàn toàn nguy cơ dịch sót, từ điển dữ liệu dịch (`merged_ejv.json`) **BẮT BUỘC** phải cung cấp cặp dịch song song ở 2 cấp độ:
     - **Cấp độ Đoạn Gộp (Combined Paragraph Level)**: Toàn văn của cả đoạn hoàn chỉnh (`combined_text`). Khi khớp, toàn bộ đoạn văn được render liền mạch trong 1 bounding box bao quát, chữ tự co giãn font và ngắt dòng tự nhiên.
     - **Cấp độ Khối Đơn & Từng Dòng (Single Block & Line Level Fallback)**: Cung cấp bản dịch cho từng block đơn và từng dòng con. Nếu đoạn không gộp được do sai số tọa độ, engine rơi về cấp dòng vẫn có bản dịch trọn vẹn, không bao giờ bị bỏ trống.
2. **Cấm tuyệt đối Placeholder (No Placeholder Ban)**:
   - **NGHIÊM CẤM** gán dấu chấm `.`, khoảng trắng rỗng, hoặc câu cắt cụt làm bản dịch cho các dòng con trong một đoạn nhiều dòng.
   - Mọi dòng con khi được trích xuất phải có nghĩa hoàn chỉnh hoặc được ghép nối chuẩn xác theo câu gốc.
3. **Bảo toàn Cấu trúc Bảng biểu & Sơ đồ (Table & Flowchart Semantic Preservation)**:
   - Trong các bảng chỉ số (Indicators), ma trận tổ chức, tiến trình thời gian (Timeline):
   - Không được để mất tiêu đề cột, không làm đảo lộn thứ tự hàng - cột.
   - Tái liên kết ngữ nghĩa giữa các dòng bị ngắt ngẫu nhiên bởi PDF trước khi dịch để đảm bảo từng chỉ tiêu (Kế hoạch trước thực hiện $\leftrightarrow$ Kết quả sau thực hiện) được dịch trọn vẹn 100%.

---

### 🏛️ TRỤ CỘT 6: BƯỚC ĐÁNH GIÁ & CHUẨN HÓA THUẬT NGỮ CHUYÊN NGÀNH (MANDATORY DOMAIN REVIEW)
1. **Quy trình Đánh giá Chuyên ngành Bắt buộc**:
   - Trước khi dựng PDF thành phẩm, Agent **PHẢI thực hiện 1 bước Đánh giá Chuyên ngành** (Domain Terminology Audit):
     - Xác định đúng phân ngành kỹ thuật sâu của tài liệu (Thận học & Lọc máu, Tim mạch can thiệp, Dược lý, Thuế & Kế toán, Sở hữu trí tuệ, Tiêu chuẩn công nghiệp JIS/ISO...).
     - Đối chiếu hệ thống thuật ngữ với Quy chuẩn/Thông tư của cơ quan quản lý chuyên ngành có thẩm quyền (Bộ Y tế, Bộ Tài chính, Bộ KH&CN...).
     - Lập bảng Ma trận Tra cứu Thuật ngữ Chuyên ngành (Domain Terminology Cross-Reference Matrix) để nạp vào từ điển dịch.
2. **Cấm Dịch máy Thô Từng Chữ (No Word-by-Word Literal Translation)**:
   - Nghiêm cấm dịch theo nghĩa đen gây sai lệch nghiêm trọng về bản chất y khoa / kỹ thuật.
   - *Ví dụ mẫu trong Thận học & Lọc máu:*
     - `血液浄化` $\rightarrow$ **Kỹ thuật Lọc máu / Lọc máu ngoài cơ thể** (CẤM: *Làm sạch máu*).
     - `血液透析 (HD)` $\rightarrow$ **Chạy thận nhân tạo / Lọc máu thận nhân tạo** (CẤM: *Thẩm tách máu*).
     - `維持透析患者` $\rightarrow$ **Bệnh nhân lọc máu chu kỳ / lọc máu duy trì** (CẤM: *Bệnh nhân duy trì thẩm tách*).
     - `腹膜透析 (PD)` $\rightarrow$ **Lọc màng bụng / Thẩm phân phúc mạc** (CẤM: *Thẩm tách màng bụng*).
     - `バスキュラーアクセス (VA)` $\rightarrow$ **Đường vào mạch máu (VA - cầu nối AVF/AVG)** (CẤM: *Truy cập mạch máu*).
     - `PTA 治療` $\rightarrow$ **Can thiệp nong mạch qua da (PTA)** (CẤM: *Điều trị PTA*).
     - `透析液清浄化ガイドライン` $\rightarrow$ **Hướng dẫn kiểm soát độ tinh khiết dịch lọc thận** (CẤM: *Hướng dẫn làm sạch dịch lọc*).
     - `生菌検査 / 生菌数測定` $\rightarrow$ **Xét nghiệm đếm số lượng vi khuẩn sống (CFU/mL)**.
     - `エンドトキシン` $\rightarrow$ **Nồng độ nội độc tố vi khuẩn (Endotoxin - EU/mL)**.
     - `プラスチックカニューラ` $\rightarrow$ **Kim luồn nhựa / Canuyn nhựa lọc máu** (CẤM: *Ống thông nhựa*).
     - `エコー下穿刺` $\rightarrow$ **Chọc dò mạch máu dưới hướng dẫn siêu âm** (CẤM: *Đâm kim dưới siêu âm*).
     - `医師主導治験` $\rightarrow$ **Thử nghiệm lâm sàng do bác sĩ/nghiên cứu viên khởi xướng**.
     - `Electronic Data Capture (EDC)` $\rightarrow$ **Hệ thống thu thập dữ liệu lâm sàng điện tử (EDC)**.

---

### 🏛️ TRỤ CỘT 7: CỔNG KIỂM TOÁN ĐỐI CHIẾU TOÀN VẸN 3 LỚP (TRI-LAYER QUALITY GATE)
Trước khi bàn giao bất kỳ file dịch hoàn chỉnh nào cho người dùng, Agent BẮT BUỘC phải chạy công cụ kiểm toán đối chiếu tự động. Báo cáo phải thỏa mãn đầy đủ 3 lớp kiểm định:

| Lớp Kiểm định | Chỉ số kiểm tra | Tiêu chuẩn bắt buộc | Phân loại |
|:---:|---|---|:---:|
| **LỚP 1** | **Tỷ lệ số trang (Page Parity)** | Phải đạt chính xác **1:1** ($N_{\text{dịch}} == N_{\text{gốc}}$). Tuyệt đối không phát sinh trang thừa hoặc thiếu trang. | 🔴 **HARD BLOCKER** |
| **LỚP 1** | **Bảo toàn hình ảnh (Image Fidelity)** | $100\%$ số lượng hình ảnh, biểu đồ, con dấu trong suốt, sơ đồ và khung hoa văn phải xuất hiện đầy đủ trên từng trang tương ứng. | 🟡 Trọng số 25% |
| **LỚP 1** | **Bảo toàn bảng biểu (Table Parity)** | Toàn bộ các bảng số liệu, bảng thông số kỹ thuật phải được tái tạo nguyên vẹn cấu trúc hàng - cột. | 🟡 Trọng số 20% |
| **LỚP 1** | **Ngân sách dòng & Lề an toàn (Line Budget & Margins)** | Số dòng văn bản trên mỗi trang phải nằm trong khoảng mục tiêu $[Min, Max]$ ($\pm 10\%$), an toàn viền in $\ge 15\text{pt}$. | 🟡 Trọng số 15% |
| **LỚP 2** | **Không sót chữ nguồn (Zero Residual Source Text)** | **Chính xác 0 khối sót (100% dịch sạch)**. Nếu còn dù chỉ 1 khối chứa chữ Hán/Kana CJK hoặc câu tiếng nguồn chưa dịch $\rightarrow$ trượt ngay (Exit code 1). | 🔴 **HARD BLOCKER** (Rule R3 §8) |
| **LỚP 3** | **Toàn vẹn nội dung & Thuật ngữ (Zero Omission & Domain Accuracy)** | **100% khối có bản dịch hoàn chỉnh**, 0 dấu chấm placeholder `.`, 0 câu ngắt cụt, 100% thuật ngữ khớp Ma trận Chuyên ngành. | 🔴 **HARD BLOCKER** |

> ⚠️ **Quy tắc nghiệm thu:** Nếu kết quả kiểm toán chưa đạt **100% PASS** ở cả 3 Lớp, Agent KHÔNG ĐƯỢC PHÉP báo cáo hoàn thành. Phải tự động điều tra nguyên nhân (bóc tách cell, paragraph merge, từ điển khớp) và xử lý triệt để cho đến khi đạt chuẩn hoàn hảo.
