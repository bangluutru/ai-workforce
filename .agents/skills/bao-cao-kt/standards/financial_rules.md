# TIÊU CHUẨN TÍNH TOÁN TÀI CHÍNH & BÁO CÁO KẾ TOÁN (FINANCIAL RULES)

> **Mục tiêu:** Đảm bảo 100% tính chính xác, nhất quán và tuân thủ các chuẩn mực kế toán Việt Nam (VAS / Thông tư 200 / Thông tư 133) và báo cáo quản trị hiện đại (Management Accounting).

---

## 1. NGUYÊN TẮC CÂN ĐỐI KẾ TOÁN BẮT BUỘC

### 1.1. Bảng Cân đối Kế toán (Balance Sheet) - tham chiếu nghiệp vụ, CHƯA có script dựng tự động
$$\text{Tổng Tài sản (100 + 200)} = \text{Tổng Nguồn vốn (300 + 400)}$$
- **Tài sản ngắn hạn (100) + Tài sản dài hạn (200)**
- **Nợ phải trả (300) + Vốn chủ sở hữu (400)**
- **Sai số cho phép:** $0$ (tuyệt đối không chấp nhận chênh lệch, dù chỉ 1 đồng). Nếu có chênh lệch, PHẢI gắn cờ `[CẦN XÁC MINH: LỆCH BẢNG CÂN ĐỐI]` kèm số tiền chênh lệch.

### 1.2. Báo cáo Kết quả Hoạt động Kinh doanh (P&L)
1. **Doanh thu thuần (Mã 10)** $= \text{Doanh thu bán hàng và CCDV (01)} - \text{Các khoản giảm trừ (02)}$
2. **Lợi nhuận gộp (Mã 20)** $= \text{Doanh thu thuần (10)} - \text{Giá vốn hàng bán (11)}$
3. **Lợi nhuận thuần từ HĐKD (Mã 30)** $= \text{Lợi nhuận gộp (20)} + (\text{Doanh thu TC (21)} - \text{Chi phí TC (22)}) - \text{Chi phí BH (25)} - \text{Chi phí QLDN (26)}$
4. **Lợi nhuận trước thuế EBT (Mã 50)** $= \text{Lợi nhuận thuần (30)} + \text{Lợi nhuận khác (40)}$
5. **Lợi nhuận sau thuế NPAT (Mã 60)** $= \text{EBT (50)} - \text{Chi phí thuế TNDN (51 + 52)}$ (TT133: 60 = 50 - 51; chi phí hoạt động là mã 24 thay cho 25 + 26)
6. **Thuế TNDN (Mã 51)** không mặc định 20%: dùng số tờ khai, hoặc ước tính theo thuế suất Luật 67/2025/QH15 (20% / 17% / 15%) kèm cờ `[CẦN XÁC MINH]` (xem SKILL.md mục 3).

---

## 2. NGUYÊN TẮC "LIVE FORMULAS" 100% (CẤM HARDCODE)

- **TUYỆT ĐỐI CẤM:** Tính nhẩm bên ngoài rồi gõ kết quả số chết vào ô Excel.
- **BẮT BUỘC:** Mọi ô tính toán tổng cộng, tỷ lệ, chênh lệch, tăng trưởng PHẢI dùng công thức Excel chuẩn:
  - Tính tổng: `=SUM(C5:C20)` hoặc `=SUMIFS(D:D, A:A, "Doanh thu")`
  - Tăng trưởng MoM/YoY: `=(C6-B6)/B6` hoặc `=IF(B6=0, 0, (C6-B6)/B6)`
  - Tỷ suất lợi nhuận gộp (Gross Margin): `=C20/C10`
  - Tỷ suất lợi nhuận ròng (Net Margin): `=C60/C10`
  - Tìm kiếm & Tham chiếu: `=VLOOKUP(...)`, `=XLOOKUP(...)`, `=INDEX(..., MATCH(...))`

---

## 3. QUY CHUẨN ĐỊNH DẠNG SỐ VÀ TIỀN TỆ (FORMATTING)

| Loại dữ liệu | Định dạng Excel chuẩn (NumberFormat) | Ví dụ hiển thị |
|--------------|--------------------------------------|----------------|
| **Tiền VND** | `#,##0 "₫"` hoặc `#,##0`             | `1,500,000,000 ₫` |
| **Tiền USD** | `$#,##0.00`                          | `$65,240.50`   |
| **Tỷ lệ %**  | `0.0%` hoặc `0.00%`                  | `24.5%`        |
| **Số lượng** | `#,##0`                              | `1,250`        |
| **Số âm**    | `(#,##0);[Red](#,##0);"-"`           | `(50,000,000)` màu đỏ |
| **Số 0**     | Hiển thị dạng dấu gạch ngang `"-"`   | `-`            |

---

## 4. QUY CHUẨN KẺ VIỀN & MÀU SẮC KẾ TOÁN (STYLING)

1. **Header:** 
   - Nền xanh navy đậm (`#1E3A8A` hoặc `#0F172A`), chữ trắng bold, font `Aptos` hoặc `Calibri` 11pt, căn giữa.
2. **Dòng dữ liệu con:**
   - Không viền hoặc viền ngang mảnh chấm đứt (`hair` / `dotted`).
3. **Dòng Subtotal (Tổng mục con):**
   - In đậm, viền trên kẻ đơn mảnh (`thin`).
4. **Dòng Grand Total (Tổng cộng cuối cùng / Lợi nhuận sau thuế):**
   - In đậm, viền trên kẻ đơn (`thin`), viền dưới **kẻ đôi (`double bottom border`)** — dấu hiệu chuẩn mực kết thúc báo cáo tài chính.
5. **Căn lề:**
   - Cột Tên chỉ tiêu / Khoản mục: Căn trái (`Left`), thụt đầu dòng (indent) theo cấp bậc tài khoản.
   - Cột Mã số / Thuyết minh: Căn giữa (`Center`).
   - Cột Số tiền / Tỷ lệ: Căn phải (`Right`).

---

## 5. NGUYÊN TẮC KẾ TOÁN QUẢN TRỊ THEO THÔNG TƯ 53/2006/TT-BTC & CHUẨN CMA

### 5.1. Khung pháp lý Thông tư 53/2006/TT-BTC
Hệ thống báo cáo kế toán quản trị trong doanh nghiệp phải tuân thủ 3 yêu cầu cốt lõi:
1. **Phù hợp với yêu cầu quản lý nội bộ:** Thiết kế linh hoạt theo nhu cầu cụ thể của từng cấp quản lý (HĐQT, Ban Giám đốc, Trưởng bộ phận), tần suất (ngày, tuần, tháng, quý, năm) và phạm vi đơn vị (toàn công ty, chi nhánh, dòng sản phẩm, kênh phân phối).
2. **Đầy đủ và so sánh được:** Phản ánh trung thực, khách quan cả thông tin tài chính và phi tài chính. Bố cục dễ hiểu, có thể đối chiếu giữa thực tế với kế hoạch, với kỳ trước hoặc với các đơn vị cùng ngành.
3. **Phù hợp với kế hoạch, dự toán và báo cáo tài chính:** Các chỉ tiêu trong báo cáo quản trị phải có tính tương thích và liên kết chặt chẽ với hệ thống chỉ tiêu của dự toán ngân sách và báo cáo tài chính chính thức.

### 5.2. Quy tắc kiểm tra và xác nhận nhu cầu so sánh đối chiếu (Comparison Check Gate)
- **Khảo sát dữ liệu nguồn:** Khi tiếp nhận số liệu đầu vào, Agent kiểm tra xem tài liệu có sẵn số liệu so sánh đối chiếu hay không (kỳ trước `prev` hoặc ngân sách kế hoạch `budget`).
- **BẮT BUỘC HỎI NGƯỜI DÙNG KHI CHỈ CÓ 1 KỲ:** Nếu dữ liệu nguồn chỉ có 1 kỳ thực tế duy nhất, Agent **bắt buộc dừng lại hỏi người dùng**:
  > *"Dữ liệu hiện tại chỉ có số liệu thực tế kỳ [Tên kỳ]. Bạn có muốn so sánh đối chiếu với (1) Kỳ trước (năm trước / quý trước) hoặc (2) Kế hoạch ngân sách (Budget) không?*
  > *- Nếu CÓ: Bạn vui lòng bổ sung file báo cáo kỳ trước / file kế hoạch ngân sách hoặc nhập nhanh chỉ tiêu mục tiêu.*
  > *- Nếu KHÔNG: Tôi sẽ tiến hành lập báo cáo cho 1 kỳ thực tế duy nhất."*
- Nếu người dùng xác nhận **KHÔNG** -> Lập báo cáo cho 1 kỳ duy nhất (bỏ qua các cột/chỉ số chênh lệch, tăng trưởng, phương sai).
- Nếu người dùng xác nhận **CÓ** -> Cho phép người dùng bổ sung file / dữ liệu so sánh trước khi thực hiện các bước tiếp theo.

### 5.3. Chuẩn mực Phân tích Phương sai Ngân sách (Variance Analysis: Actual vs. Budget - CMA)
Khi có dữ liệu ngân sách kế hoạch (`budget`), kỹ năng tự động kích hoạt module phân tích phương sai quản trị:
1. **Phương sai tuyệt đối:**
   $$\text{Variance} = \text{Actual (Thực tế)} - \text{Budget (Kế hoạch)}$$
2. **Tỷ lệ hoàn thành kế hoạch:**
   $$\% \text{Achieved} = \frac{\text{Actual}}{\text{Budget}}$$
3. **Phân loại Phương sai Thuận lợi (Favorable) vs Bất lợi (Unfavorable):**
   - **Nhóm Doanh thu & Lợi nhuận (Mã 01, 10, 20, 30, 50, 60):**
     * $\text{Actual} \ge \text{Budget}$: **Thuận lợi (Favorable - Xanh)** $\rightarrow$ Vượt chỉ tiêu kinh doanh.
     * $\text{Actual} < \text{Budget}$: **Bất lợi (Unfavorable - Đỏ/Vàng)** $\rightarrow$ Hụt chỉ tiêu, cần mổ xẻ nguyên nhân (giá bán, sản lượng hay chiết khấu).
   - **Nhóm Giá vốn & Chi phí hoạt động (Mã 11, OPEX 25, 26, 24):**
     * $\text{Actual} \le \text{Budget}$: **Thuận lợi (Favorable - Xanh)** $\rightarrow$ Tiết kiệm chi phí so với ngân sách được duyệt.
     * $\text{Actual} > \text{Budget}$: **Bất lợi (Unfavorable - Đỏ)** $\rightarrow$ Vượt chi ngân sách (Cost Overrun).
4. **Ngưỡng Cảnh báo Rủi ro Quản trị (CMA Threshold):**
   - Nếu Chi phí vượt ngân sách $\ge 10\%$ HOẶC Doanh thu hụt ngân sách $\ge 10\%$, Agent bắt buộc gắn cờ `[CẢNH BÁO PHƯƠNG SAI NGÂN SÁCH]` trong phân tích và slide thuyết trình.

### 5.4. Định hướng Đề xuất Phương án Quản trị (CMA Actionable Prescriptions)
Báo cáo Kế toán Quản trị không chỉ dừng lại ở việc liệt kê số liệu thụ động, mà phải đóng vai trò là cố vấn tài chính chiến lược:
- **Cấu trúc khuyến nghị 3 tầng bắt buộc:**
  1. **Fact (Hiện trạng số liệu):** Chỉ rõ chỉ số nào đang lệch mục tiêu (kèm con số tuyệt đối và tỷ lệ %).
  2. **Root Cause (Nguyên nhân bản chất):** Phân tích nguyên nhân sâu xa (do chính sách bán hàng dồn cuối tháng, giá nguyên liệu tăng, công nợ đại lý nới lỏng hay chi phí marketing sàn tăng vọt).
  3. **Actionable Prescription (Giải pháp hành động):** Đưa ra lộ trình xử lý cụ thể theo khung thời gian 30 - 60 - 90 ngày (ví dụ: điều chỉnh chiết khấu thanh toán sớm 2/10 net 30, xả hàng tồn kho chậm luân chuyển, áp dụng hạn mức tín dụng động).
