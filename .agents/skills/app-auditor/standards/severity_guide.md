# Tiêu Chuẩn Phân Loại Mức Độ Nghiêm Trọng (Severity Guide)

Quy định chuẩn phân loại lỗi (Defects) và khuyến nghị (Recommendations) của App Auditor. Mọi vấn đề phát hiện được bắt buộc phải gán một mức độ nghiêm trọng chính xác kèm theo đường dẫn bằng chứng tái hiện.

---

## 1. Bảng Phân Cấp Mức Độ Nghiêm Trọng

| Mức độ | Định danh | Định nghĩa chi tiết | Ví dụ thực tế |
|---|---|---|---|
| **P0** | **Blocker** | Lỗi làm sập toàn bộ ứng dụng hoặc luồng nghiệp vụ cốt lõi không thể sử dụng. Người dùng không có cách nào vượt qua (no workaround). | • Trang trắng (white screen) hoặc crash runtime.<br>• Nút Submit thanh toán / đăng ký không phản hồi.<br>• Vòng lặp redirect vô tận. |
| **P1** | **Serious** | Chức năng quan trọng hoạt động sai hoặc có nguy cơ mất mát / sai lệch dữ liệu. Có thể có workaround nhưng rất khó chịu. | • Lưu form thành công nhưng F5 reload mất sạch dữ liệu.<br>• API trả về HTTP 500 khi lọc sản phẩm.<br>• Cho phép gửi trùng lặp đơn hàng khi double-click. |
| **P2** | **UX / Functional Problem** | Lỗi ảnh hưởng đáng kể đến trải nghiệm hoặc luồng phụ bị lỗi. Người dùng thông thường vẫn có thể hoàn tất tác vụ. | • Modal bị tràn ra ngoài màn hình mobile 390px không bấm được nút Đóng.<br>• Input form thiếu nhãn trợ năng (Accessible Label).<br>• Xung đột giữa bộ lọc category và ô tìm kiếm keyword. |
| **P3** | **Cosmetic / Consistency** | Khiếm khuyết về mặt thị giác, tính nhất quán hệ thống thiết kế hoặc lỗi hiển thị nhỏ không chặn thao tác. | • Sử dụng 3 mã màu xanh dương khác nhau (#2563EB, #2462EA, #2764E8) cho cùng 1 loại primary button.<br>• Khoảng cách padding giữa 2 card cùng cấp không đồng đều.<br>• Lỗi ngắt dòng chữ cụt (orphan text) trên tablet. |
| **P4** | **Improvement** | Đề xuất tối ưu hóa trải nghiệm hoặc nâng cao độ tiện dụng. Đây KHÔNG phải là lỗi phần mềm (Defect). | • Gợi ý tự động focus vào ô tìm kiếm khi mở trang.<br>• Gợi ý thêm skeleton loading thay vì spinner tròn đơn điệu.<br>• Bổ sung phím tắt Escape để đóng nhanh dialog. |

---

## 2. Nguyên Tắc Phân Biệt Giữa Lỗi (Defect) và Kiến Nghị (Recommendation)

1. **Defect (Lỗi thực tế):** Phải chứng minh được hành vi thực tế (Actual Behavior) vi phạm yêu cầu kỹ thuật, gây hỏng hóc chức năng, vi phạm chuẩn WCAG hoặc phá vỡ tính nguyên vẹn của giao diện.
2. **Recommendation (Kiến nghị):** Các quan điểm thẩm mỹ mang tính tương đối của AI. Không được hạ điểm chất lượng của sản phẩm dựa trên sở thích cá nhân nếu ứng dụng không vi phạm quy chuẩn thiết kế đã công bố.
3. Bắt buộc gắn cờ `[DEFECT]` hoặc `[RECOMMENDATION]` trong báo cáo thẩm định chi tiết.
