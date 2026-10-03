# Hướng dẫn thuế GTGT

> Phân loại: DERIVED từ văn bản đã đọc nguyên văn. Tham số tính toán nằm ở `standards/gtgt.json` (có nguồn, hiệu lực). Lệnh: `scripts/tax_cli.py gtgt`, `gtgt-direct`.

## Căn cứ chính

| Nội dung | Văn bản | Tọa độ |
|---|---|---|
| Thuế suất 10% (chuẩn), 5% (ưu đãi) | Luật 48/2024/QH15 | Điều 9 khoản 2, 3 |
| Phương pháp tính trực tiếp trên doanh thu: 1% phân phối, 5% dịch vụ, 3% sản xuất, 2% khác | Luật 48/2024/QH15 | Điều 12 khoản 2 điểm b |
| Giảm còn 8% từ 01/07/2025 đến 31/12/2026 | NĐ 174/2025/NĐ-CP | Điều 1 |
| Giảm 20% tỷ lệ % khi tính trực tiếp, cùng thời hạn | NĐ 174/2025/NĐ-CP | Điều 1 |
| Hướng dẫn chi tiết | NĐ 181/2025/NĐ-CP, sửa đổi bởi NĐ 359/2025 và NĐ 144/2026 | Theo từng điều |
| Hộ kinh doanh có doanh thu năm từ 1 tỷ trở xuống không chịu thuế | Luật 09/2026/QH16 Điều 2, NĐ 68/2026 sửa bởi NĐ 141/2026 | Hiệu lực 01/01/2026 |
| Hoàn thuế cho người nước ngoài mua hàng mang theo khi xuất cảnh | TT 84/2026/TT-BTC | Toàn văn |

## Cách chọn phương pháp

1. Doanh nghiệp, tổ chức có hóa đơn, chứng từ đầy đủ: phương pháp khấu trừ (`gtgt`).
2. Đối tượng thuộc diện tính trực tiếp trên doanh thu (doanh thu năm dưới ngưỡng và không đăng ký khấu trừ, cá nhân kinh doanh vàng bạc...): `gtgt-direct`. Ngưỡng và điều kiện xem `standards/gtgt.json` (`nguong_dn_phuong_phap_truc_tiep`).
3. Hộ kinh doanh: dùng module `hkd` (gộp GTGT và TNCN).

## Lưu ý nghiệp vụ

- Giảm 8% chỉ áp dụng cho nhóm hàng hóa, dịch vụ đang chịu 10%, loại trừ các nhóm theo NĐ 174/2025 Điều 1 khoản 2. Engine nhận cờ `reduction_eligible` do người dùng xác nhận từng dòng.
- Hết hiệu lực 31/12/2026: khi `--on` sau ngày này engine tự trả về 10%.
- Thuế đầu vào chưa khấu trừ hết được chuyển kỳ sau (`--carry`). Điều kiện hoàn thuế cần đối chiếu riêng (NĐ 181/2025).
- Hóa đơn: xem `resources/hoa-don/huong-dan-hoa-don.md`.

## Việc chưa làm

- Chưa tự động hóa điều kiện hoàn thuế, khấu trừ đầu vào không đủ điều kiện (thanh toán không dùng tiền mặt), hàng xuất khẩu 0%.
