---
trigger: always_on
description: "Luật Kỷ Luật Vận Hành — Đảm bảo kiểm chứng thực tế và hoàn thành tự động 100%."
---

# LUẬT KỶ LUẬT VẬN HÀNH (OPERATIONAL DISCIPLINE)

---

## 1. PER-TASK VERIFICATION (KIỂM CHỨNG BẮT BUỘC)

Tuyệt đối KHÔNG BAO GIỜ đánh dấu một tác vụ là "hoàn thành" khi chưa chứng minh nó hoạt động:
- Chạy lệnh kiểm thử, kiểm tra log, xác nhận file đầu ra thực tế tồn tại và hợp lệ.
- Luôn đặt câu hỏi: *"Một kỹ sư trưởng (Staff Engineer) có phê duyệt kết quả này không?"*
- Nếu có bất kỳ lỗi nào xuất hiện $\rightarrow$ Sửa dứt điểm trước khi báo cáo hoàn thành.

---

## 2. AUTONOMOUS FULL-RUN PROTOCOL (TỰ ĐỘNG CHẠY ĐẾN CÙNG)

- Khi được kích hoạt bởi người dùng, Agent PHẢI chủ động thực hiện toàn bộ các bước trong quy trình (bóc tách $\rightarrow$ dịch/xử lý $\rightarrow$ ghép nối $\rightarrow$ kiểm tra $\rightarrow$ xuất bản).
- KHÔNG tự ý dừng lại giữa chừng để hỏi những câu thừa thãi hoặc xin phép tiếp tục nếu mọi thứ đang vận hành đúng kế hoạch.
- Chỉ dừng khi:
  1. Gặp lỗi ngoại lệ nghiêm trọng không thể tự phục hồi.
  2. Phát hiện mâu thuẫn dữ liệu cần quyết định từ con người.
  3. Đã hoàn thành 100% và tạo đầy đủ thành phẩm đầu ra.

---

## 3. REGRESSION PREVENTION (CHỐNG LỖI TỒN ĐỌNG)

Khi sửa lỗi (bug fix) hoặc cập nhật tính năng:
1. Phải chứng minh lỗi xảy ra trước khi sửa.
2. Sửa đúng nguyên nhân gốc rễ (Root Cause), không vá tạm ở phần ngọn.
3. Sau khi sửa, phải chạy lại toàn bộ quy trình kiểm tra để đảm bảo không làm gãy các tính năng cũ đang chạy tốt.
