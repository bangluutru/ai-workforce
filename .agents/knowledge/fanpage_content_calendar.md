# 📅 BẢNG KẾ HOẠCH NỘI DUNG FANPAGE (CONTENT CALENDAR SSOT)

> **Vai trò:** Nguồn Sự Thật Duy Nhất (SSOT) cho **Agent Team Phòng Fanpage (`W3-phong-fanpage`)**.
> Mỗi sáng lúc **08:00 AM** (hoặc khi bạn gõ lệnh chạy Phòng Fanpage), Agent Chiến lược sẽ tự động đọc dòng đầu tiên có trạng thái `PENDING` trong bảng dưới đây để sản xuất bài viết + ảnh/video, kiểm định pháp lý Luật R5 và đẩy lên Fanpage ở chế độ **Nháp / Lên lịch (Draft / Scheduled)**.
> Nếu toàn bộ danh sách đã `DONE` / `SCHEDULED`, Agent sẽ tự động nghiên cứu xu hướng mới nhất theo **Hồ sơ Thương hiệu** bên dưới.

---

## 1. HỒ SƠ THƯƠNG HIỆU & CẤU HÌNH FANPAGE MẶC ĐỊNH

| Thông số | Giá trị cấu hình | Ghi chú |
|---|---|---|
| **Tên Fanpage / Thương hiệu** | AI Workforce & Chotto Studio | Có thể sửa theo tên Fanpage thực tế của bạn |
| **Giọng văn thương hiệu (Tone)** | Thực tế, gần gũi, giàu thông tin, không sáo rỗng | Tuân thủ `anti_ai_footprint.md` |
| **Nhóm kiểm định R5 mặc định** | `general` | Đổi thành `cosmetics`, `tpcn`, `finance`... theo từng bài |
| **Chế độ đăng mặc định** | `draft` | `draft` (Lưu nháp trên Fanpage) / `schedule` (Hẹn giờ đăng) / `publish-now` |
| **Giờ hẹn đăng mặc định** | `+180` (phút sau khi tạo) | Áp dụng khi chọn chế độ `schedule` |
| **Biến môi trường kết nối API** | `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN` | Khai báo trong file `.env` ở gốc dự án (không commit token lên Git) |

---

## 2. DANH SÁCH CHỦ ĐỀ LÊN LỊCH (`CONTENT QUEUE`)

> **Hướng dẫn trạng thái:**
> - `PENDING`: Chưa thực hiện — Agent sẽ ưu tiên lấy dòng `PENDING` đầu tiên từ trên xuống.
> - `DRAFT_READY`: Đã tạo xong gói bài viết + media và đẩy lên Nháp Fanpage / lưu tại `~/Downloads/AIWF_Output/`.
> - `SCHEDULED`: Đã hẹn giờ đăng tự động trên Facebook Fanpage.
> - `PUBLISHED`: Đã đăng công khai lên Fanpage.

| ID | Ngày dự kiến | Chủ đề / Góc tiếp cận (Hook) | Nhóm R5 (`category`) | Định dạng (`media_type`) | Mục tiêu hành động (CTA) | Trạng thái |
|:---:|:---:|---|---|---|---|---|
| `FP-001` | Hôm nay | 3 sai lầm khiến dân văn phòng mất 2 giờ mỗi ngày cho báo cáo thủ công và cách tự động hóa trong 5 phút | `general` | `image` | Bình luận từ khóa "BAOCAO" hoặc nhắn tin cho Fanpage để nhận mẫu quy trình tự động hóa | `DRAFT_READY` |
| `FP-002` | Ngày mai | Những điểm mới trong thủ tục cư trú và hoàn thuế tại Nhật Bản người lao động Việt cần lưu ý năm 2026 | `general` | `image` | Lưu bài viết và chia sẻ cho bạn bè đang làm việc tại Nhật Bản | `PENDING` |
| `FP-003` | Ngày +2 | Cách đọc bảng thành phần dầu gội phủ màu tóc bạc dịu nhẹ cho da đầu nhạy cảm theo chuẩn Nhật | `cosmetics` | `video` | Nhắn tin cho Fanpage để được tư vấn dòng sản phẩm phù hợp với tình trạng tóc | `PENDING` |
| `FP-004` | Ngày +3 | Bí quyết xây dựng Đội ngũ Nhân sự Số (AI Agent Team) vận hành nội dung đa kênh không tốn chi phí API | `general` | `video` | Theo dõi Fanpage để cập nhật chuỗi hướng dẫn thực chiến về AI Workforce | `PENDING` |
