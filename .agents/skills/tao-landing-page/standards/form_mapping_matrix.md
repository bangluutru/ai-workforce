# Ma trận Phân loại Form & Ánh xạ Landing Hub Endpoint

| Loại Form | Dấu hiệu Nhận biết trong Thiết kế | Target Endpoint | Target SDK Method | Cấu trúc Payload Tối thiểu |
|---|---|---|---|---|
| **`lead`** | • Nút CTA: *"Đăng ký tư vấn"*, *"Nhận mẫu thử"*, *"Gọi lại cho tôi"*<br>• Trường thông tin: Họ tên, Số điện thoại, Email, Ghi chú nhu cầu | `POST /api/lead` | `LPHub.submitLead()` | `{ formId, name, phone, email, data: {} }` |
| **`order`** | • Nút CTA: *"Đặt hàng ngay"*, *"Mua ngay"*, *"Thanh toán COD"*<br>• Trường thông tin: Sản phẩm chọn, số lượng, họ tên người nhận, địa chỉ giao hàng, phương thức thanh toán | `POST /api/order` | `LPHub.submitOrder()` | `{ formId, customer: { name, phone, address }, items: [{ name, quantity, price }], total }` |
| **`custom`** | • Nút CTA: *"Xem kết quả chẩn đoán"*, *"Gửi khảo sát"*, *"Tính toán phác đồ"*<br>• Trường thông tin: Các câu hỏi trắc nghiệm, điểm số, lựa chọn mục tiêu sức khỏe/làm đẹp | `POST /api/custom-form` | `LPHub.submitCustomForm()` | `{ formId, data: { quizScore, answers, goals } }` |

## Quy tắc Bắt buộc:
1. Nếu form có trường số lượng + giá sản phẩm + địa chỉ -> BẮT BUỘC phân loại là `order`.
2. Nếu form chỉ có thông tin liên hệ và lời nhắn -> BẮT BUỘC phân loại là `lead`.
3. Nếu form là các bước quiz tương tác nhiều bước -> BẮT BUỘC phân loại là `custom`.
4. Không được gọi sai endpoint tương ứng với loại form đã đăng ký trong Landing Hub (vi phạm trả về HTTP 400 `INVALID_FORM_TYPE`).
