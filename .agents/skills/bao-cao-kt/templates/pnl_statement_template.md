# MẪU BÁO CÁO KẾT QUẢ KINH DOANH (P&L) - THAM CHIẾU

> Bảng này chỉ để ĐỌC HIỂU cấu trúc. File Excel thật do `scripts/build_excel_dashboard.py` sinh từ `data.json`;
> công thức được tạo tự động theo vị trí dòng thực tế (mã nào không có số liệu thì dòng đó bị bỏ và công thức tự bỏ số hạng).
> Không tự viết công thức theo số dòng cố định như bản cũ.

## Mẫu B02-DN (regime TT200, TT99)

| Mã | Chỉ tiêu | Loại | Công thức |
|:--:|---|---|---|
| 01 | Doanh thu bán hàng và cung cấp dịch vụ | Nhập | |
| 02 | Các khoản giảm trừ doanh thu | Nhập | |
| 10 | Doanh thu thuần | Tính | 01 - 02 |
| 11 | Giá vốn hàng bán | Nhập | |
| 20 | Lợi nhuận gộp | Tính | 10 - 11 |
| GM | Biên lợi nhuận gộp | Tính | 20 / 10 |
| 21 | Doanh thu hoạt động tài chính | Nhập | |
| 22 | Chi phí tài chính | Nhập | |
| 23 | Trong đó chi phí lãi vay | Nhập (không cộng) | |
| 25 | Chi phí bán hàng | Nhập | |
| 26 | Chi phí quản lý doanh nghiệp | Nhập | |
| 30 | Lợi nhuận thuần từ HĐKD | Tính | 20 + (21 - 22) - (25 + 26) |
| 31 | Thu nhập khác | Nhập | |
| 32 | Chi phí khác | Nhập | |
| 40 | Lợi nhuận khác | Tính | 31 - 32 |
| 50 | Tổng lợi nhuận kế toán trước thuế | Tính | 30 + 40 |
| 51 | Chi phí thuế TNDN hiện hành | Nhập số thực tế, hoặc ước tính | ROUND(MAX(0, 50 x ô thuế suất), 0) |
| 52 | Chi phí thuế TNDN hoãn lại | Nhập | |
| 60 | Lợi nhuận sau thuế TNDN | Tính | 50 - 51 - 52 (kẻ đôi dưới) |
| NM | Biên lợi nhuận ròng | Tính | 60 / 10 |

## Mẫu B02-DNN (regime TT133)

Giống trên nhưng thay 25, 26 bằng **24 Chi phí quản lý kinh doanh**; 30 = 20 + 21 - 22 - 24; không có 52; 60 = 50 - 51.

Mỗi dòng có thêm cột Chênh lệch `=C-D` và Tăng trưởng `=IF(D=0,"",(C-D)/ABS(D))`. Dòng biên lợi nhuận hiển thị chênh lệch theo điểm phần trăm.
