---
name: boc-tach-cv
description: SỐ HÓA CV PDF THÀNH DỮ LIỆU CÓ CẤU TRÚC (Hook + What).
trigger: Bóc tách CV, trích xuất CV, đọc CV ra bảng
exclusion: KHÔNG dùng cho chấm điểm hay đánh giá CV (sử dụng cham-diem-cv).
push: Dùng cho MỌI yêu cầu số hóa CV, kể cả khi user chỉ ném file PDF và nói 'xử lý giùm'.
needs_file: true
file_filter: cv
---

# LÝ LUẬN VÀ TƯ DUY (MINDSET)
- Nếu thiếu SĐT/Email → Highlight bằng từ `[THIẾU]`. Đây là 2 kênh liên lạc duy nhất, tuyệt đối KHÔNG tự đoán số.
- KHÔNG đưa ra đánh giá CV này tốt hay dở.
- Luôn xuất ra dữ liệu theo đúng định dạng được quy định tại `examples/skeleton_cv.md`.

# TÀI NGUYÊN (RESOURCES / EXAMPLES)
- Xem `examples/skeleton_cv.md` để lấy định dạng đầu ra chuẩn.
