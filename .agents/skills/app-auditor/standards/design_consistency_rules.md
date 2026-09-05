# Quy Chuẩn Nhất Quán Hệ Thống Thiết Kế (Design Consistency Rules)

Tài liệu hướng dẫn Agent và các script đo lường tự động phát hiện những sai lệch vô thức trong hệ thống thiết kế (Design System Inconsistency).

---

## 1. Phát Hiện Biến Thể Màu Sắc (Color Variance Detection)

1. **Nguyên tắc phân nhóm màu:**
   - Trong cùng một sản phẩm, các thành phần cùng loại (Primary Button, Link, Header Accent) phải dùng chung một biến CSS hoặc mã Hex thống nhất.
2. **Lỗi phát hiện:**
   - Bắt các trường hợp mã màu tương đồng có khoảng cách Delta-E quá nhỏ nhưng khác nhau về giá trị Hex (ví dụ: `#2563EB`, `#2462EA`, `#2764E8`).
   - Đây thường là dấu hiệu lập trình viên gõ chay mã màu thay vì tái sử dụng biến Design Token.
3. **Màu nền và viền (Background & Borders):**
   - Sự không đồng nhất giữa các thẻ Card (thẻ này dùng viền `#E2E8F0`, thẻ kia dùng `#E5E7EB` trong cùng một danh sách).

---

## 2. Thang Đo Typography & Thứ Bậc Thị Giác (Visual Hierarchy)

1. **Hệ thống Font Scale:**
   - H1: 32px đến 48px
   - H2: 24px đến 30px
   - H3: 18px đến 20px
   - Body: 14px đến 16px
   - Caption / Small: 12px đến 13px
2. **Sai phạm cần gắn cờ:**
   - Heading cấp dưới (H3) lại có kích thước font hoặc độ đậm lớn hơn Heading cấp trên (H2).
   - Sử dụng quá 3 font family khác nhau trên cùng một trang mà không có chủ đích nghệ thuật rõ ràng.

---

## 3. Hệ Lưới Khoảng Cách (Spacing Grid 4px / 8px)

1. **Chuẩn bội số 4px/8px:**
   - Khoảng cách lề trong (padding) và lề ngoài (margin) nên tuân thủ các mốc: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px.
2. **Sai phạm cần gắn cờ:**
   - Hai card cùng loại trên cùng một hàng ngang nhưng có padding không bằng nhau (ví dụ: một bên 16px, một bên 22px).
   - Nút bấm bị lệch trục căn lề dọc so với icon đi kèm.

---

## 4. Bán Kính Bo Góc & Đổ Bóng (Border Radius & Shadows)

1. **Tính nhất quán bo góc:**
   - Nếu dự án theo phong cách bo góc mềm (`rounded-lg` / 8px), cấm trộn lẫn các nút bấm góc nhọn vuông (`0px`) hoặc bo tròn hình viên thuốc (`9999px`) một cách ngẫu nhiên.
2. **Hệ thống đổ bóng:**
   - Không lạm dụng đổ bóng quá đậm gây nhiễu thị giác (Visual Noise).
