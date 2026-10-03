# Hướng dẫn thuế thu nhập doanh nghiệp

> Lệnh: `scripts/tax_cli.py tndn`. Tham số: `standards/tndn.json`.

## Căn cứ chính

| Nội dung | Văn bản | Tọa độ |
|---|---|---|
| Thuế suất 20% chuẩn, 17% (doanh thu năm trên 3 tỷ đến 50 tỷ), 15% (không quá 3 tỷ) | Luật 67/2025/QH15 | Điều 10 |
| Miễn thuế khi tổng doanh thu năm không quá 1 tỷ đồng | NĐ 320/2025/NĐ-CP khoản 15 Điều 4 (bổ sung bởi NĐ 141/2026 Điều 2); Luật 09/2026/QH16 Điều 3 | Hiệu lực 01/01/2026 |
| Hướng dẫn chi tiết | NĐ 320/2025/NĐ-CP, TT 20/2026/TT-BTC | Theo từng điều |
| Kê khai doanh nghiệp tổng doanh thu không quá 3 tỷ khi không xác định được chi phí: 0,3% phân phối; 1,2% sản xuất, vận tải; 1,5% dịch vụ; 4% cho thuê tài sản, đại lý | NĐ 320/2025/NĐ-CP Điều 12 khoản 4 | Chưa đưa vào engine |

## Công thức engine

Thu nhập chịu thuế = doanh thu + thu nhập khác - chi phí được trừ + chi phí không được trừ cộng lại - thu nhập miễn thuế.
Thu nhập tính thuế = thu nhập chịu thuế - lỗ kết chuyển. Thuế = thu nhập tính thuế x thuế suất.
Thuế suất chọn theo tổng doanh thu kỳ liền kề trước (`--prior-revenue`). Bỏ trống thì engine dùng doanh thu kỳ này và gắn cờ `[CẦN XÁC MINH]`.

## Điều kiện cần hỏi người dùng

1. Doanh nghiệp có phải công ty con hoặc có quan hệ liên kết không (ảnh hưởng miễn thuế dưới 1 tỷ).
2. Số lỗ được kết chuyển còn trong thời hạn luật định.
3. Có ưu đãi thuế theo dự án hay không (ngoài phạm vi tính tự động).

## Ngoài phạm vi tính tự động

Ưu đãi theo dự án, chuyển giá, thuế tối thiểu toàn cầu: xem `resources/advanced/huong-dan-nang-cao.md`.
