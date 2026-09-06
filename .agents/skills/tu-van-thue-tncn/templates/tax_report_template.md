# BÁO CÁO TƯ VẤN THUẾ THU NHẬP CÁ NHÂN (TNCN) — KỲ TÍNH THUẾ 2026
**Số hiệu hồ sơ:** `TAX-[ID]-[YYYYMMDD]`  
**Thời điểm lập:** `[YYYY-MM-DD HH:MM]`  
**Cán bộ số tư vấn:** Antigravity AI Workforce (`tu-van-thue-tncn`)  
**Căn cứ pháp lý:** Luật 109/2025/QH15, Luật 09/2026/QH16, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC.

---

## 1. TỌA ĐỘ VỤ VIỆC & TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)

| Trục Tọa Độ | Dữ liệu ghi nhận từ Người nộp thuế (NNT) | Trạng thái xác minh |
|---|---|---|
| **ĐỐI TƯỢNG** | [Họ tên / Nhóm đối tượng: Cá nhân cư trú / KCT / Freelancer / HKD] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **HÀNH VI / NGUỒN THU** | [Tiền lương, tiền công / Hợp đồng dịch vụ vãng lai / Chuyển nhượng BĐS...] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **TÁC ĐỘNG / NGHĨA VỤ** | [Khấu trừ tại nguồn / Tự quyết toán / Hoàn thuế / Nộp thêm] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **PHẠM VI** | [1 nơi duy nhất (đã/chưa ủy quyền) / Nhiều nơi / Xuyên biên giới] | [ĐÃ XÁC MINH / CẦN XÁC MINH] |
| **THỜI ĐIỂM** | Kỳ tính thuế [Năm 2026 / Quyết toán năm 2025] | [Áp dụng Luật 109/2025 & NQ 110/2025] |

### Tóm tắt kết luận cốt lõi:
- **Tổng thu nhập ghi nhận (Gross):** `[Số tiền] VNĐ`
- **Tổng các khoản giảm trừ & bảo hiểm:** `[Số tiền] VNĐ`
- **Thu nhập tính thuế (TNTT):** `[Số tiền] VNĐ`
- **Tổng thuế TNCN nghĩa vụ trong kỳ:** `[Số tiền] VNĐ`
- **Thu nhập thực nhận (Net):** `[Số tiền] VNĐ` (Tỷ lệ thuế thực tế: `[X.XX]%`)
- **Tình trạng nghĩa vụ:** `[Ủy quyền quyết toán cho công ty / Phải tự làm thủ tục quyết toán trực tiếp / Thuộc diện hoàn thuế]`

---

## 2. BẢNG NGUỒN SỰ THẬT DUY NHẤT (SOURCE OF TRUTH - SOT)

> Trích dẫn NGUYÊN VĂN các điều khoản pháp luật làm căn cứ xác định nghĩa vụ:

| STT | Tọa độ văn bản (Số hiệu - Điều - Khoản) | Trích dẫn nguyên văn quy định | Giá trị đối soát áp dụng |
|:---:|---|---|---|
| 1 | **Luật 109/2025/QH15** — Điều 22 | *"Biểu thuế lũy tiến từng phần áp dụng đối với thu nhập tính thuế từ tiền lương, tiền công gồm 05 bậc: Bậc 1 đến 10 triệu đồng (5%), Bậc 2 từ 10 đến 30 triệu đồng (10%), Bậc 3 từ 30 đến 60 triệu đồng (20%), Bậc 4 từ 60 đến 100 triệu đồng (30%), Bậc 5 trên 100 triệu đồng (35%)."* | Phân bổ thu nhập vào 5 bậc thuế mới |
| 2 | **Nghị quyết 110/2025/UBTVQH15** | *"Mức giảm trừ gia cảnh đối với đối tượng nộp thuế là 15,5 triệu đồng/tháng (186 triệu đồng/năm); mức giảm trừ đối với mỗi người phụ thuộc là 6,2 triệu đồng/tháng."* | Giảm trừ bản thân: 15,5tr; NPT: 6,2tr/người |
| 3 | **Thông tư 87/2026/TT-BTC** | *"Các tổ chức, cá nhân trả tiền công, tiền thù lao, tiền chi khác cho cá nhân cư trú không ký hợp đồng lao động... có tổng mức trả thu nhập từ 5.000.000 đồng/lần trở lên thì phải khấu trừ thuế theo mức 10% trên thu nhập trước khi trả."* | Ngưỡng khấu trừ vãng lai: từ 5tr trở lên |
| 4 | **Nghị định 253/2026/NĐ-CP** | *"Giảm trừ chi phí y tế khám chữa bệnh thực tế tối đa 23.000.000 đồng/năm; giảm trừ chi phí giáo dục đào tạo tối đa 24.000.000 đồng/năm; hưu trí tự nguyện tối đa 3.000.000 đồng/tháng."* | Định mức giảm trừ y tế, học phí, hưu trí |

---

## 3. BẢNG TÍNH TOÁN VÀ ĐỐI SOÁT CHI TIẾT (LIVE FORMULAS AUDIT)

### 3.1 Bảng phân rã các khoản trừ lương
1. **Lương Gross thỏa thuận:** `[Gross] VNĐ`
2. **Bảo hiểm bắt buộc (NLĐ):**
   - BHXH (8% x min(Gross, 50.600.000)): `[BHXH] VNĐ`
   - BHYT (1.5% x min(Gross, 50.600.000)): `[BHYT] VNĐ`
   - BHTN (1%): `[BHTN] VNĐ`
   - *=> Tổng khấu trừ bảo hiểm:* `[Tổng BH] VNĐ`
3. **Các khoản giảm trừ hợp pháp:**
   - Giảm trừ bản thân NNT: `15.500.000 VNĐ`
   - Giảm trừ Người phụ thuộc ([Số lượng] người x 6.200.000): `[Giảm trừ NPT] VNĐ`
   - Giảm trừ chi phí Y tế / Giáo dục / Hưu trí tự nguyện: `[Chi phí] VNĐ`
   - *=> Tổng giảm trừ gia cảnh & chi phí:* `[Tổng giảm trừ] VNĐ`
4. **Thu nhập tính thuế (TNTT):**  
   $$\text{TNTT} = \text{Gross} - \text{Tổng BH} - \text{Tổng giảm trừ} = [TNTT] \text{ VNĐ}$$

### 3.2 Bảng phân bổ thuế lũy tiến từng phần (Biểu 5 bậc)
| Bậc | Khung thu nhập tính thuế | Thuế suất | Thu nhập chịu thuế trong bậc | Thuế phải nộp |
|:---:|---|:---:|:---:|:---:|
| 1 | Đến 10 triệu đồng | 5% | `[Số tiền]` | `[Thuế B1]` |
| 2 | Trên 10 đến 30 triệu đồng | 10% | `[Số tiền]` | `[Thuế B2]` |
| 3 | Trên 30 đến 60 triệu đồng | 20% | `[Số tiền]` | `[Thuế B3]` |
| 4 | Trên 60 đến 100 triệu đồng | 30% | `[Số tiền]` | `[Thuế B4]` |
| 5 | Trên 100 triệu đồng | 35% | `[Số tiền]` | `[Thuế B5]` |
| **CỘNG** | **Tổng nghĩa vụ thuế TNCN:** | | | `[Tổng Thuế] VNĐ` |

* **Lương thực nhận (Net):** `Gross - Tổng BH - Tổng Thuế = [Net] VNĐ`

---

## 4. ĐƯỜNG LỐI HÀNH ĐỘNG & QUY TRÌNH QUYẾT TOÁN (SOP)

### Trường hợp 1: Cá nhân đủ điều kiện ủy quyền quyết toán qua tổ chức trả thu nhập
- Áp dụng khi: Chỉ có thu nhập tại 1 nơi trong năm và đang làm việc tại thời điểm ủy quyền.
- Hành động: Điền Giấy ủy quyền quyết toán thuế TNCN theo Mẫu số 08/UQ-QTT-TNCN nộp cho phòng Kế toán/Nhân sự trước ngày 30/03.

### Trường hợp 2: Cá nhân tự quyết toán trực tiếp với Cơ quan Thuế
- Phương thức thực hiện khuyến nghị: **Ứng dụng eTax Mobile** hoặc Cổng thông tin điện tử Tổng cục Thuế (`canhan.gdt.gov.vn`).
- Các bước thực hiện:
  1. Đăng nhập eTax Mobile bằng tài khoản định danh VNeID mức độ 2 hoặc mã số thuế.
  2. Vào mục **"Tiện ích"** -> Chọn **"Tra cứu thông tin quyết toán"** để kiểm tra dữ liệu các nguồn chi trả đã kê khai.
  3. Chọn **"Kê khai thuế"** -> **"Quyết toán thuế TNCN"** -> Chọn mẫu tờ khai `02/QTT-TNCN`.
  4. Hệ thống tự động điền các thông tin nguồn thu nhập và số thuế đã khấu trừ tại nguồn.
  5. Đối soát số liệu với Bảng tính toán tại Mục 3 của báo cáo này.
  6. Đính kèm chứng từ khấu trừ thuế điện tử (được cấp từ các đơn vị chi trả).
  7. Ký số / Xác thực mã OTP qua SMS và nộp tờ khai.

---

## 5. RỦI RO, CẢNH BÁO & KHUYẾN NGHỊ TỐI ƯU HỢP PHÁP

### 5.1 Cảnh báo cờ xác minh (Confidence Flagging)
- `[CẦN XÁC MINH: Kiểm tra tình trạng đăng ký MST của người phụ thuộc]`
- `[CẦN XÁC MINH: Xác nhận thu nhập của người phụ thuộc không vượt quá 3 triệu đồng/tháng]`
- `[CẦN XÁC MINH: Thu thập đầy đủ chứng từ khấu trừ thuế điện tử trước khi bấm nộp tờ khai]`

### 5.2 Khuyến nghị tối ưu nghĩa vụ thuế hợp chuẩn:
1. Đăng ký đầy đủ người phụ thuộc đủ điều kiện để tối ưu mức giảm trừ 6,2 triệu đồng/tháng.
2. Lưu trữ đầy đủ hóa đơn điện tử cho chi phí y tế điều trị nội/ngoại trú thuộc danh mục BHYT và biên lai học phí giáo dục chính quy để hưởng mức giảm trừ bổ sung mới theo NĐ 253/2026/NĐ-CP.
3. Tham gia bảo hiểm hưu trí tự nguyện để được trừ tối đa thêm 3 triệu đồng/tháng vào thu nhập chịu thuế.

---

> [!WARNING]
> **DISCLAIMER PHÁP LÝ:**  
> Báo cáo này được lập tự động dựa trên quy định pháp luật Việt Nam có hiệu lực trong kỳ tính thuế 2026 và thông tin do Người nộp thuế cung cấp. Báo cáo mang tính chất tham vấn hỗ trợ đối soát, không thay thế văn bản xác nhận chính thức từ Cơ quan Quản lý Thuế. NNT vui lòng đối soát lại số liệu thực tế trên cổng thông tin https://canhan.gdt.gov.vn trước khi thực hiện nộp tờ khai.
