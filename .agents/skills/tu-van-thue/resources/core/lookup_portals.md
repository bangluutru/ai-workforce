# Cổng tra cứu văn bản và thông tin thuế

> Kiểm tra khả năng truy cập ngày 03/10/2026 từ môi trường làm việc của skill.

| Cổng | Địa chỉ | Vai trò | Truy cập |
|---|---|---|---|
| Công báo Chính phủ | https://congbao.chinhphu.vn | Nguyên văn văn bản có PDF ký số (nguồn chính của skill) | Được |
| Cổng thông tin Chính phủ, cơ sở dữ liệu văn bản | https://vanban.chinhphu.vn | Tra cứu văn bản | Được |
| Bộ Tài chính | https://mof.gov.vn | Thông tư, dự thảo, hướng dẫn | Được |
| Thư viện Pháp luật | https://thuvienphapluat.vn | Tra cứu thứ cấp, đối chiếu hiệu lực | Được (thứ cấp, không dùng làm nguồn tính) |
| Cục Thuế (gdt.gov.vn) | https://gdt.gov.vn | Hướng dẫn nghiệp vụ, biểu mẫu | Quá thời gian chờ |
| LuatVietnam | https://luatvietnam.vn | Tra cứu thứ cấp | Bị chặn 403 |

## Quy tắc dùng nguồn

1. Con số đưa vào `standards/` phải đọc từ nguyên văn (PDF Công báo) và ghi Điều, Khoản.
2. Nguồn thứ cấp chỉ để tìm văn bản, không đủ để tính (trạng thái SECONDARY_ONLY).
3. Quy trình đọc nguyên văn: lấy PDF từ trang chi tiết Công báo rồi chạy `scripts/doc_ingest.py` ở thư mục gốc workspace. Trang scan thì đọc ảnh trang.
4. Khi `gdt.gov.vn` truy cập được, dùng để đối chiếu hướng dẫn nghiệp vụ, vẫn không thay thế nguyên văn.
