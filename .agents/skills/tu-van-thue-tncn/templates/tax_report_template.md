# BÁO CÁO TƯ VẤN THUẾ THU NHẬP CÁ NHÂN (TNCN) - KỲ TÍNH THUẾ 2026
**Số hiệu hồ sơ:** `TAX-[CHỦ_ĐỀ]-[YYYYMMDD]`  
**Thời điểm lập:** `[YYYY-MM-DD HH:MM]`  
**Cán bộ số tư vấn:** Antigravity AI Workforce (`tu-van-thue-tncn`)  
**Căn cứ pháp lý:** Luật 109/2025/QH15, Luật 09/2026/QH16, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC, NĐ 141/2026/NĐ-CP, Luật BHXH 2024.

---

## 1. TỌA ĐỘ VỤ VIỆC VÀ TÓM TẮT ĐIỀU HÀNH

| Trục Tọa Độ | Dữ liệu ghi nhận từ Người nộp thuế (NNT) | Trạng thái xác minh |
|---|---|---|
| **ĐỐI TƯỢNG** | [Họ tên / Nhóm đối tượng: Cá nhân cư trú / Freelancer / HKD / Người bán BĐS / Người rút BHXH] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **HÀNH VI / NGUỒN THU** | [Tiền lương Gross/Net / Thù lao dịch vụ vãng lai / Chuyển nhượng BĐS / Trợ cấp BHXH] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **TÁC ĐỘNG / NGHĨA VỤ** | [Tính thuế hàng tháng / Quy đổi lương / Tự quyết toán hoàn thuế / Nộp thêm / Miễn thuế] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **PHẠM VI** | [1 nơi ủy quyền / Nhiều nơi tự quyết toán / Trong nước / Nước ngoài] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **THỜI ĐIỂM** | Kỳ tính thuế năm 2026 | [Áp dụng văn bản quy phạm pháp luật năm 2026] |

### Tóm tắt kết luận và giải pháp cốt lõi
- **Vấn đề của người dùng:** `[Tóm tắt ngắn gọn câu hỏi / tình huống của người dùng]`
- **Kết quả tính toán then chốt:**
  - *Thu nhập ghi nhận:* `[Số tiền] VNĐ`
  - *Tổng giảm trừ gia cảnh và chi phí hợp pháp:* `[Số tiền] VNĐ`
  - *Nghĩa vụ thuế TNCN thực tế:* `[Số tiền] VNĐ`
  - *Số tiền thực nhận (Net) hoặc Số thuế được hoàn lại:* `[Số tiền] VNĐ`
- **Đường lối hành động khuyến nghị:** `[Lộ trình cụ thể cần thực hiện ngay: Nộp ủy quyền trước 30/03, nộp tờ khai 02/QTT-TNCN trên eTax Mobile, làm cam kết 08/CK-TNCN, hoặc thu thập chứng từ]`

---

## 2. BẢNG NGUỒN SỰ THẬT PHÁP QUY (SOURCE OF TRUTH - SOT)

> Trích dẫn nguyên văn các điều khoản pháp luật làm căn cứ trực tiếp cho bài toán của người dùng:

| STT | Tọa độ văn bản (Số hiệu - Điều - Khoản) | Trích dẫn nguyên văn quy định | Giá trị đối soát áp dụng |
|:---:|---|---|---|
| 1 | **[Văn bản 1]** - Điều X Khoản Y | *"[Trích dẫn nguyên văn câu chữ của điều luật]"* | [Áp dụng cho trường hợp của NNT] |
| 2 | **[Văn bản 2]** - Điều X Khoản Y | *"[Trích dẫn nguyên văn câu chữ của điều luật]"* | [Định mức hoặc tỷ lệ khấu trừ áp dụng] |

---

## 3. BẢNG TÍNH TOÁN VÀ ĐỐI SOÁT CHI TIẾT

*(Lựa chọn mục 3A, 3B, 3C hoặc 3D tương ứng với bài toán của người dùng)*

### 3A. BÀI TOÁN TIỀN LƯƠNG (GROSS -> NET HOẶC NET -> GROSS)
1. **Lương Gross thỏa thuận:** `[Gross] VNĐ`
2. **Bảo hiểm bắt buộc (NLĐ đóng):**
   - BHXH (8% x min(Gross, 50.600.000)): `[BHXH] VNĐ`
   - BHYT (1,5% x min(Gross, 50.600.000)): `[BHYT] VNĐ`
   - BHTN (1% x Gross): `[BHTN] VNĐ`
   - *=> Tổng khấu trừ bảo hiểm:* `[Tổng BH] VNĐ`
3. **Các khoản giảm trừ hợp pháp:**
   - Giảm trừ bản thân NNT: `15.500.000 VNĐ` (NQ 110/2025/UBTVQH15)
   - Giảm trừ Người phụ thuộc ([Số lượng] người x 6.200.000): `[Giảm trừ NPT] VNĐ`
   - Giảm trừ chi phí Y tế / Giáo dục / Hưu trí tự nguyện: `[Chi phí] VNĐ`
   - *=> Tổng giảm trừ gia cảnh và chi phí:* `[Tổng giảm trừ] VNĐ`
4. **Thu nhập tính thuế (TNTT):** `[TNTT] VNĐ`
5. **Thuế TNCN phân bổ theo biểu 5 bậc:** `[Tổng thuế] VNĐ`
6. **Lương thực nhận (Net):** `[Net] VNĐ` (Tỷ lệ thuế thực tế: `[X.XX]%`)

### 3B. BÀI TOÁN QUYẾT TOÁN THUẾ NĂM (THU NHẬP NHIỀU NƠI)
1. **Tổng thu nhập chịu thuế cả năm:** `[Số tiền] VNĐ`
2. **Tổng giảm trừ cả năm (Bản thân 186tr + NPT + Bảo hiểm + Y tế/Giáo dục):** `[Số tiền] VNĐ`
3. **Thu nhập tính thuế cả năm:** `[Số tiền] VNĐ`
4. **Tổng nghĩa vụ thuế TNCN thực tế cả năm:** `[Số tiền] VNĐ`
5. **Số thuế các nơi đã tạm khấu trừ trong năm:** `[Số tiền] VNĐ`
6. **Kết quả bù trừ quyết toán:**
   - *Chênh lệch:* `[Số tiền] VNĐ`
   - *Kết luận:* `[BẠN ĐƯỢC HOÀN THUẾ / BẠN PHẢI NỘP THÊM / KHÔNG PHẢI NỘP THÊM (<= 50.000đ)]`

### 3C. BÀI TOÁN THUẾ CHUYỂN NHƯỢNG BẤT ĐỘNG SẢN
1. **Giá trị chuyển nhượng:** `[Số tiền] VNĐ`
2. **Thẩm định điều kiện miễn thuế:**
   - Điều kiện 1 (Sở hữu duy nhất theo Điều 19 NĐ 253/2026/NĐ-CP năm 2026): `[ĐẠT / CHƯA ĐẠT]`
   - Điều kiện 2 (Thời gian sở hữu >= 183 ngày): `[ĐẠT: X ngày / CHƯA ĐẠT]`
   - Điều kiện 3 (Chuyển nhượng toàn bộ): `[ĐẠT / CHƯA ĐẠT]`
3. **Kết luận nghĩa vụ thuế:** `[MIỄN THUẾ 100% THEO ĐIỀU 18/19 NĐ 253/2026/NĐ-CP HOẶC NỘP THUẾ 2% = X VNĐ]`

### 3D. BÀI TOÁN RÚT BẢO HIỂM XÃ HỘI 1 LẦN
1. **Thời gian tham gia:** `[X] năm trước 2014 và [Y] năm từ 2014 trở đi`
2. **Mức bình quân tiền lương (MBQTL):** `[Số tiền] VNĐ`
3. **Số tiền nhận 1 lần:** `(1,5 x X + 2,0 x Y) x MBQTL = [Số tiền] VNĐ`
4. **Bảng so sánh đa chiều với phương án bảo lưu:**
   - Lương hưu hàng tháng ước tính: `[Số tiền] VNĐ/tháng`
   - Thẻ BHYT miễn phí thanh toán đến 95%
   - Lợi ích tài chính dài hạn vượt trội hơn phương án rút một lần

---

## 4. LỘ TRÌNH HÀNH ĐỘNG VÀ THỦ TỤC THỰC THI (SOP)

*(Hướng dẫn cụ thể các bước người dùng cần làm: Tra cứu trên eTax Mobile, hồ sơ giấy tờ cần chuẩn bị, thời hạn nộp)*

---

## 5. RỦI RO, CẢNH BÁO VÀ KHUYẾN NGHỊ TỐI ƯU HỢP PHÁP

### 5.1 Cảnh báo cờ xác minh nghiệp vụ
- `[CẦN XÁC MINH: <Nội dung người dùng cần đối soát lại thực tế>]`

### 5.2 Khuyến nghị tối ưu nghĩa vụ thuế hợp chuẩn pháp lý
1. `[Khuyến nghị 1]`
2. `[Khuyến nghị 2]`
3. `[Khuyến nghị 3]`

---

> [!WARNING]
> **DISCLAIMER PHÁP LÝ:**  
> Báo cáo tư vấn này được lập tự động dựa trên các văn bản quy phạm pháp luật thuế và bảo hiểm xã hội Việt Nam có hiệu lực trong kỳ tính thuế 2026. Báo cáo mang tính chất tham vấn chuyên môn, hỗ trợ đối soát dữ liệu và định hướng nghiệp vụ; không thay thế các quyết định hành chính, thông báo nộp thuế hoặc kết luận thanh kiểm tra chính thức từ Cơ quan Quản lý Thuế và Cơ quan Bảo hiểm Xã hội. Người nộp thuế vui lòng đối soát trực tiếp trên ứng dụng eTax Mobile hoặc cổng thông tin https://canhan.gdt.gov.vn trước khi nộp tờ khai chính thức.
