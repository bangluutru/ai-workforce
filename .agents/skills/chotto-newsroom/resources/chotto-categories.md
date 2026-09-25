# 9 DANH MỤC HỢP LỆ TRONG CHOTTODAY (CATEGORY TAXONOMY)

> Hệ thống phân loại danh mục bài viết chuẩn của ChottoDay.
> Nguồn đối chiếu: `chottoday/src/services/content/articleModel.js` (Mảng `CATEGORIES`).
> Mỗi bài viết BẮT BUỘC phải chọn duy nhất 1 trong 9 mã danh mục (`category`) dưới đây.

---

## BẢNG TRA CỨU 9 MÃ DANH MỤC

| Mã Danh Mục (`category`) | Tên Tiếng Việt | Phạm vi nội dung cốt lõi | Ví dụ chủ đề thời sự điển hình |
|:---:|---|---|---|
| **`doc`** | Thủ tục & Giấy tờ | Thẻ cư trú (Zairyu Card), thị thực, thủ tục Cục Xuất nhập cảnh, thẻ My Number, giấy chuyển khẩu (Juminhyo), đổi bằng lái xe. | - Gia hạn thẻ ngoại kiều online<br/>- Tích hợp bằng lái vào My Number<br/>- Cấp lại thẻ cư trú bị mất |
| **`work`** | Lao động & Quyền lợi | Luật lao động, tiền lương tối thiểu, bảo hiểm thất nghiệp, tai nạn lao động, giải quyết tranh chấp với công ty, nghiệp đoàn. | - Tăng lương tối thiểu toàn quốc 2026<br/>- Quy định mới về giờ làm thêm<br/>- Quyền đổi công ty của lao động Tokutei |
| **`life`** | Đời sống Nhật Bản | Nhà ở, tiền điện nước gas, phân loại rác, tài khoản ngân hàng, sim điện thoại, giao thông, an toàn phòng chống thiên tai. | - Trợ cấp giá điện mùa hè<br/>- Quy tắc bỏ rác đồ điện tử mới<br/>- Mở tài khoản ngân hàng Yucho |
| **`health`** | Sức khỏe & Bảo hiểm | Bảo hiểm y tế quốc dân (Kokumin Kenko Hoken), bảo hiểm xã hội (Shakai Hoken), khám chữa bệnh, tiêm chủng, cấp cứu 119. | - Tăng tỷ lệ đóng bảo hiểm y tế<br/>- Khám sức khỏe định kỳ miễn phí<br/>- Cách dùng ứng dụng cấp cứu đa ngữ |
| **`family`** | Gia đình & Con cái | Bảo lãnh vợ/chồng/con sang Nhật, kết hôn, sinh con, tiền trợ cấp thai sản, tiền nuôi con (Jido Teate), trường học cho trẻ em. | - Nới rộng đối tượng nhận trợ cấp Jido Teate<br/>- Thủ tục làm giấy khai sinh tại Đại sứ quán<br/>- Miễn học phí mầm non |
| **`job`** | Chuyển việc & Phỏng vấn | Tìm việc làm, viết sơ yếu lý lịch (Rirekisho), phỏng vấn tuyển dụng, xin việc kỹ sư, thủ tục chuyển việc hợp pháp. | - Cổng thông tin Hello Work hỗ trợ tiếng Việt<br/>- Danh mục ngành nghề thiếu hụt nhân lực mới<br/>- Bí quyết phỏng vấn trực tuyến |
| **`study`** | Học tập & Tiếng Nhật | Du học, trường tiếng Nhật, kỳ thi JLPT, kỳ thi EJU, học bổng MEXT, chuyển đổi từ visa du học sang visa đi làm. | - Lịch đăng ký thi JLPT tháng 12<br/>- Nới lỏng giờ làm thêm cho sinh viên tốt nghiệp<br/>- Học bổng chính phủ Nhật Bản mới |
| **`newcomer`** | Người mới sang Nhật | Cẩm nang sơ cấp trong 14 ngày đầu đến Nhật: đăng ký địa chỉ ở shiyakusho, làm sim, thẻ cư trú tại sân bay, đồ dùng thiết yếu. | - Hướng dẫn 7 việc phải làm trong tuần đầu<br/>- Danh sách đồ dùng cấm mang vào Nhật<br/>- Cách kích hoạt thẻ SIM tại sân bay |
| **`tool`** | Tiện ích & Công cụ | Bài viết hướng dẫn hoặc giới thiệu các công cụ số, bảng tính, ứng dụng tra cứu hữu ích cho cuộc sống. | - Hướng dẫn dùng công cụ tính lương thực nhận<br/>- Tra cứu mức giảm trừ gia cảnh khi gửi tiền |

---

## NGUYÊN TẮC CHỌN DANH MỤC KHI CÓ GIAO THOA (CONFLICT RESOLUTION)

1. **Ưu tiên mục đích hành động chính của độc giả:**
   - Nếu tin tức về việc sinh con và nhận trợ cấp $\rightarrow$ Chọn `family` (thay vì `health`).
   - Nếu tin tức về việc đổi visa sau khi chuyển việc $\rightarrow$ Chọn `doc` (vì thủ tục visa là chặng cuối bắt buộc).
   - Nếu tin tức về mức lương và bảo hiểm lao động $\rightarrow$ Chọn `work`.
2. **Không tự ý tạo mã danh mục mới:** Bất kỳ mã danh mục nào nằm ngoài 9 mã trên sẽ làm gãy bộ lọc và trang danh mục của ChottoDay.
