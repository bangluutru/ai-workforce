# TIÊU CHUẨN TÍNH TOÁN TÀI CHÍNH & BÁO CÁO KẾ TOÁN (FINANCIAL RULES)

> **Mục tiêu:** Đảm bảo 100% tính chính xác, nhất quán và tuân thủ các chuẩn mực kế toán Việt Nam (VAS / Thông tư 200 / Thông tư 133) và báo cáo quản trị hiện đại (Management Accounting).

---

## 1. NGUYÊN TẮC CÂN ĐỐI KẾ TOÁN BẮT BUỘC

### 1.1. Bảng Cân đối Kế toán (Balance Sheet)
$$\text{Tổng Tài sản (100 + 200)} = \text{Tổng Nguồn vốn (300 + 400)}$$
- **Tài sản ngắn hạn (100) + Tài sản dài hạn (200)**
- **Nợ phải trả (300) + Vốn chủ sở hữu (400)**
- **Sai số cho phép:** $0$ (tuyệt đối không chấp nhận chênh lệch, dù chỉ 1 đồng). Nếu có chênh lệch, PHẢI gắn cờ `[CẦN XÁC MINH: LỆCH BẢNG CÂN ĐỐI]` kèm số tiền chênh lệch.

### 1.2. Báo cáo Kết quả Hoạt động Kinh doanh (P&L)
1. **Doanh thu thuần (Mã 10)** $= \text{Doanh thu bán hàng và CCDV (01)} - \text{Các khoản giảm trừ (02)}$
2. **Lợi nhuận gộp (Mã 20)** $= \text{Doanh thu thuần (10)} - \text{Giá vốn hàng bán (11)}$
3. **Lợi nhuận thuần từ HĐKD (Mã 30)** $= \text{Lợi nhuận gộp (20)} + (\text{Doanh thu TC (21)} - \text{Chi phí TC (22)}) - \text{Chi phí BH (25)} - \text{Chi phí QLDN (26)}$
4. **Lợi nhuận trước thuế EBT (Mã 50)** $= \text{Lợi nhuận thuần (30)} + \text{Lợi nhuận khác (40)}$
5. **Lợi nhuận sau thuế NPAT (Mã 60)** $= \text{EBT (50)} - \text{Chi phí thuế TNDN (51 + 52)}$

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
