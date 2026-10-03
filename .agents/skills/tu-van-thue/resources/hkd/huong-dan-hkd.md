# Hướng dẫn thuế hộ kinh doanh và cá nhân kinh doanh

> Lệnh: `scripts/tax_cli.py hkd`. Tham số: `standards/hkd.json`. Hiệu lực từ 01/01/2026.

## Căn cứ chính

| Nội dung | Văn bản | Tọa độ |
|---|---|---|
| Ngưỡng doanh thu năm từ 1 tỷ trở xuống không phải nộp GTGT, TNCN | NĐ 68/2026/NĐ-CP sửa đổi bởi NĐ 141/2026/NĐ-CP; Luật 09/2026/QH16 Điều 1, 2 | NĐ 141 Điều 3 (hiệu lực 01/01/2026) |
| TNCN theo lợi nhuận: 15% đến 3 tỷ, 17% từ 3 đến 50 tỷ, 20% trên 50 tỷ | Luật 109/2025/QH15 | Điều 7 |
| TNCN theo doanh thu: 0,5% phân phối; 2% dịch vụ; 5% cho thuê tài sản, đại lý; 1,5% sản xuất; 5% nội dung số; 1% khác; 5% cho thuê bất động sản | Luật 109/2025/QH15 | Điều 7 khoản 3, 4 |
| GTGT trực tiếp trên doanh thu | Luật 48/2024/QH15 | Điều 12 khoản 2 điểm b |
| Hóa đơn điện tử | NĐ 68/2026 khoản 5 Điều 8 sửa bởi NĐ 141/2026 | Xem module hóa đơn |
| Kế toán hộ kinh doanh | TT 152/2025/TT-BTC | Toàn văn |
| Đăng ký, thay đổi, tạm ngừng | TT 18/2026/TT-BTC | Toàn văn |

## Cách engine tính

1. Doanh thu năm không quá ngưỡng 1 tỷ: GTGT và TNCN bằng 0.
2. Trên ngưỡng: GTGT = doanh thu x tỷ lệ GTGT theo nhóm ngành. TNCN theo doanh thu = (doanh thu - ngưỡng) x tỷ lệ, hoặc theo lợi nhuận khi người dùng nhập `--expenses`.
3. Phương pháp doanh thu áp dụng đến ngưỡng `nguong_pp_doanh_thu` (3 tỷ); trên ngưỡng này dùng phương pháp lợi nhuận.
4. Cờ `--vat-reduction` áp giảm 20% tỷ lệ GTGT theo NĐ 174/2025 trong thời hạn hiệu lực.

## Cần hỏi người dùng

Nhóm ngành chính, doanh thu từng nhóm, có chi phí chứng từ đầy đủ không, địa điểm kinh doanh, đã đăng ký hóa đơn điện tử chưa.
