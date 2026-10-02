# MẪU BỐ CỤC DASHBOARD QUẢN TRỊ TÀI CHÍNH (KPI DASHBOARD TEMPLATE)

Tài liệu này mô tả bố cục mà `scripts/build_excel_dashboard.py` tự dựng. Mọi giá trị trên thẻ KPI là công thức tham chiếu sheet P&L; không gõ số vào thẻ.

---

## 1. PHÂN BỔ KHÔNG GIAN BẢNG TÍNH (GRID LAYOUT)

```
+-------------------------------------------------------------------------------------+
| B2:I4  Tên công ty / Tiêu đề báo cáo / Kỳ + đơn vị tính                              |
+---------------------+---------------------+---------------------+-------------------+
| B6:C8 DOANH THU     | D6:E8 LỢI NHUẬN GỘP | F6:G8 LỢI NHUẬN     | H6:I8 TIỀN CUỐI KỲ |
| THUẦN (10)          | (20)                | SAU THUẾ (60)       | (chỉ khi có cash)  |
| ='P&L'!C<dòng 10>   | ='P&L'!C<dòng 20>   | ='P&L'!C<dòng 60>   | số nhập            |
| Tăng trưởng (CT)    | Biên gộp (CT)       | Biên ròng (CT)      |                    |
+---------------------+---------------------+---------------------+-------------------+
| B11:E..  Bảng theo kỳ (chỉ khi có quarterly) + dòng Cộng + dòng "Chênh lệch với P&L" |
| Biểu đồ cột: doanh thu thuần, giá vốn, chi phí hoạt động theo kỳ                    |
+-------------------------------------------------------------------------------------+
CT = công thức sống. <dòng xx> do script tính theo bản đồ mã số, không cố định.
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
