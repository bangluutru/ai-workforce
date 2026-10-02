# Ví dụ 2 — Landing page phần mềm (category: general, channel: web)

**Brief:** Phần mềm chấm công cho chuỗi bán lẻ 5-50 cửa hàng. Giọng thương hiệu: thẳng, thực tế. Ưu đãi: dùng thử 14 ngày.
**Bằng chứng:** Case study chuỗi Cà phê Y (12 cửa hàng): thời gian chốt công giảm từ 16 giờ còn 2 giờ/tháng (dữ liệu hệ thống của khách, tháng 3/2025, khách đã đồng ý công bố); máy chủ đặt tại Việt Nam, chứng chỉ ISO/IEC 27001 cấp năm 2024.

## TRƯỚC (bị chặn: 8 lỗi)
```text
Giải pháp chấm công hàng đầu — bảo mật tuyệt đối, không thể bị hack.
Cam kết hiệu quả 100%, không rủi ro. Hơn 500+ doanh nghiệp tin dùng.
Ông Trần B, CEO, chia sẻ: "Đây là phần mềm tốt nhất thị trường".
```
Lỗi: "hàng đầu" không nguồn, em dash, "bảo mật tuyệt đối", "không thể bị hack", "hiệu quả 100%", "không rủi ro", con số khách hàng không nguồn, phát ngôn chưa xác nhận + "tốt nhất".

## SAU (đạt: `fact_checker.py --category general` exit 0)
```text
# Chốt bảng công 12 cửa hàng trong 2 giờ thay vì 2 ngày

Phần mềm chấm công cho chuỗi bán lẻ 5-50 cửa hàng: nhân viên chấm bằng điện thoại, quản lý xem bảng công theo ngày.

## Chuỗi Cà phê Y đã làm thế nào
Trước đây kế toán mất 16 giờ mỗi tháng để gom file Excel từ 12 cửa hàng. Sau khi dùng phần mềm, việc chốt công còn 2 giờ (dữ liệu hệ thống của khách hàng, tháng 3/2025).

## Dữ liệu của bạn được bảo vệ ra sao
Dữ liệu mã hóa khi truyền và khi lưu; máy chủ đặt tại Việt Nam, đạt chứng chỉ ISO/IEC 27001 (cấp năm 2024).

## Dùng thử 14 ngày
Nhập dữ liệu mẫu hoặc dữ liệu thật của 1 cửa hàng; hết 14 ngày tự chọn có tiếp tục hay không.

"Kế toán của tôi không còn phải thức khuya cuối tháng." - Ông Trần B, Giám đốc vận hành Cà phê Y [CẦN XÁC NHẬN: ông Trần B duyệt nguyên văn]
```
Vì sao đạt: tiêu đề nêu kết quả đo được của khách hàng thật; bảo mật nêu tiêu chuẩn cụ thể thay vì "tuyệt đối"; phát ngôn gắn cờ chờ duyệt; không dùng từ so sánh nhất.
