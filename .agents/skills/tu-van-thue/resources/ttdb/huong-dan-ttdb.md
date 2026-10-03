# Hướng dẫn thuế tiêu thụ đặc biệt

> Lệnh: `scripts/tax_cli.py ttdb --item <khóa> --price N [--quantity Q] [--factor hybrid|sinh_hoc]`. Chạy `ttdb --list` hoặc bỏ `--item` để xem các khóa. Tham số: `standards/ttdb.json` (49 mục, đọc từ ảnh trang gốc Công báo, PRIMARY_VERIFIED).

## Căn cứ

| Nội dung | Văn bản |
|---|---|
| Biểu thuế, giá tính thuế, thời điểm xác định | Luật 66/2025/QH15 Điều 6, 7, 8 |
| Xe chạy pin: mốc tăng thuế suất là 01/01/2031 | Luật 09/2026/QH16 Điều 4 (thay mốc 01/03/2027 trong Luật 66) |
| Hướng dẫn chi tiết | NĐ 360/2025/NĐ-CP |

## Công thức

Thuế TTĐB = giá tính thuế x thuế suất. Giá tính thuế là giá chưa có thuế TTĐB, thuế bảo vệ môi trường và GTGT (Điều 6 khoản 1). Nếu chỉ biết giá đã gồm TTĐB, dùng `--price-includes-ttdb` (suy ra: giá / (1 + thuế suất)).

Thuế suất tăng dần theo năm đối với rượu, bia, nước giải khát có đường: engine chọn theo ngày `--on`. Ngày trước hiệu lực của biểu thuế sẽ báo lỗi.

## Hạn chế

- Thuốc lá: thuế suất 75% cùng mức thuế tuyệt đối từ 01/01/2027. Engine trả cả hai thành phần và gắn cờ cần xác minh cách kết hợp theo văn bản hướng dẫn.
- Chưa xử lý khấu trừ TTĐB nguyên liệu, hoàn thuế, giá tính thuế đặc thù (gôn, casino, xổ số, hàng bán trả góp).
