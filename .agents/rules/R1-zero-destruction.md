---
trigger: always_on
description: "Luật Zero-Destruction - Bảo toàn dữ liệu vật lý của doanh nghiệp."
---

# LUẬT ZERO-DESTRUCTION (BẢO TOÀN DỮ LIỆU)

Đây là quy tắc cao nhất liên quan đến tệp tin hệ thống. Mọi tác nhân AI khi thao tác với file phải tuân thủ nghiêm ngặt các quy định sau:

## 1. CẤM XÓA VĨNH VIỄN
Tuyệt đối KHÔNG ĐƯỢC PHÉP thực thi lệnh xóa tệp vĩnh viễn (như `rm -rf`, `del`). Việc làm mất mát dữ liệu của doanh nghiệp là lỗi nghiêm trọng không thể chấp nhận.

## 2. QUY TRÌNH "XÓA MỀM"
- Nếu người dùng (User) yêu cầu "Xóa file này", tác nhân KHÔNG được xóa.
- Thay vào đó, tác nhân phải dùng lệnh DI CHUYỂN (`mv` hoặc tính năng chuyển file) để đưa file đó vào thư mục `_Delete/` nằm ở gốc dự án.
- Hãy thông báo cho User: "File đã được chuyển vào thùng rác an toàn `_Delete/`".

## 3. QUY TRÌNH "LƯU TRỮ"
- Khi một file chính sách, bảng giá hoặc quy định (trong Knowledge) hết hiệu lực và có tệp mới thay thế, KHÔNG ghi đè lên file cũ.
- Hãy di chuyển file cũ vào thư mục `_Archive/` và bổ sung tệp mới vào đúng thư mục Knowledge hiện tại.
