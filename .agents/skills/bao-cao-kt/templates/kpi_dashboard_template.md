# MẪU BỐ CỤC DASHBOARD QUẢN TRỊ TÀI CHÍNH (KPI DASHBOARD TEMPLATE)

Tài liệu này hướng dẫn cách tổ chức không gian bảng tính khi xuất bản file Excel & Google Sheets Dashboard.

---

## 1. PHÂN BỔ KHÔNG GIAN BẢNG TÍNH (GRID LAYOUT)

```
+-----------------------------------------------------------------------------------------+
| [A1:H2] TIÊU ĐỀ: BÁO CÁO TÀI CHÍNH & QUẢN TRỊ DOANH NGHIỆP - KỲ ... (Theme Navy Blue)     |
+-----------------------------------------------------------------------------------------+
| [B4:C5] CARD 1:          | [D4:E5] CARD 2:          | [F4:G5] CARD 3:                   |
| TỔNG DOANH THU           | LỢI NHUẬN GỘP (GM)       | LỢI NHUẬN RÒNG (NPAT)             |
| 12,450,000,000 ₫         | 4,980,000,000 ₫ (40.0%)  | 1,867,500,000 ₫ (15.0%)           |
| ▲ +18.5% so với cùng kỳ  | ▲ +14.2% so với cùng kỳ  | ▲ +22.0% so với cùng kỳ           |
+--------------------------+--------------------------+-----------------------------------+
| [B7:E18] BIỂU ĐỒ DOANH THU & CHI PHÍ THEO THÁNG     | [F7:H18] BIỂU ĐỒ CƠ CẤU CHI PHÍ    |
| (Combo Chart Cột & Đường)                           | (Donut Chart Tỷ trọng OPEX)       |
+-----------------------------------------------------+-----------------------------------+
| [B20:H35] BẢNG TÓM TẮT CHỈ SỐ HOẠT ĐỘNG (SUMMARY TABLE CÓ LIVE FORMULAS)                 |
+-----------------------------------------------------------------------------------------+
```

---

## 2. QUY ƯỚC CONDITIONAL FORMATTING (TÔ MÀU CÓ ĐIỀU KIỆN)
- **Tăng trưởng dương (> 0%):** Chữ xanh lá cây đậm `#15803D`, nền xanh lá nhạt `#DCFCE7`.
- **Tăng trưởng âm (< 0%):** Chữ đỏ đậm `#B91C1C`, nền đỏ nhạt `#FEE2E2`.
- **Biên lợi nhuận đạt mục tiêu (>= Target):** Icon tick xanh hoặc highlight nhẹ.

---

## 3. TƯƠNG THÍCH GOOGLE SHEETS
- File `.xlsx` được tạo bằng `openpyxl` không dùng các tính năng riêng biệt chỉ có ở Excel 365 offline (như dynamic array `#SPILL` chưa hỗ trợ đầy đủ trên Google Sheets).
- Dùng các hàm phổ biến toàn cầu: `SUM`, `AVERAGE`, `IF`, `MAX`, `MIN`, `VLOOKUP`, `SUMIFS`, `COUNTIFS` để khi người dùng Import vào Google Sheets sẽ tự động hiển thị 100% không lỗi `#NAME?` hay `#REF!`.
