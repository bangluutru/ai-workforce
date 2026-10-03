# Hướng dẫn thuế nhà thầu nước ngoài

> Lệnh: `scripts/tax_cli.py nha-thau --item <khóa> --revenue N [--gross-up]`. Tham số: `standards/fct.json`.

## Phạm vi đã đọc nguyên văn

| Nội dung | Văn bản | Tọa độ |
|---|---|---|
| Tỷ lệ TNDN trên doanh thu tính thuế (dịch vụ 5%, quản lý nhà hàng khách sạn casino 10%, hàng hóa 1%, không tách được hàng hóa và dịch vụ 2%, bản quyền 10%, thuê máy bay tàu biển 2%, thuê máy móc phương tiện 5%, lãi vay 5%, chứng khoán và tái bảo hiểm 0,1%, phái sinh 2%, chuyển nhượng vốn 2%, xây dựng vận tải khác 2%) | NĐ 320/2025/NĐ-CP | Điều 12 khoản 3 |
| Công thức, gộp thuế vào giá (doanh thu thực nhận chia (1 - tỷ lệ)) | TT 20/2026/TT-BTC | Điều 7 |

## Chưa có nguyên văn

- Thuế GTGT của nhà thầu nước ngoài: TT 89/2026 không có trên Công báo (chỉ có QĐ 2551 đính chính). Engine không tính phần này, chỉ cảnh báo.
- Hiệp định tránh đánh thuế hai lần, điều kiện miễn thuế: cần đối chiếu từng hiệp định.

## Cần hỏi người dùng

Loại hợp đồng, có tách được giá trị hàng hóa và dịch vụ không, bên Việt Nam nộp thuế hộ (gross-up) hay không, quốc gia của nhà thầu.
