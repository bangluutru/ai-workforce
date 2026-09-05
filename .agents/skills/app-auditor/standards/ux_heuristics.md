# Bộ Tiêu Chuẩn Thẩm Định Trải Nghiệm Người Dùng (UX Heuristics)

App Auditor áp dụng 10 nguyên lý kinh điển của Jakob Nielsen kết hợp các tiêu chuẩn hiện đại về micro-interactions và mobile usability.

---

## 1. Mười Nguyên Lý Nielsen Norman Được Vận Dụng Trong Kiểm Thử

1. **Hiển thị trạng thái hệ thống (Visibility of System Status)**
   - Mọi hành động gửi form, tải dữ liệu, xử lý nền phải có phản hồi tức thời (< 100ms) qua spinner, thanh tiến trình hoặc skeleton loader.
   - Tuyệt đối không để màn hình đóng băng không rõ lý do.

2. **Tương đồng giữa hệ thống và thế giới thực (Match between system and the real world)**
   - Sử dụng ngôn ngữ tự nhiên, mạch lạc, tránh biệt ngữ lập trình hoặc mã lỗi kỹ thuật hiển thị thẳng cho người dùng (ví dụ: cấm hiển thị `Unhandled Promise Rejection` hay `NullPointerException`).

3. **Quyền kiểm soát và tự do của người dùng (User control and freedom)**
   - Luôn có nút "Hủy", "Quay lại" hoặc phím `Esc` để thoát khỏi modal/dialog mà không làm hỏng trạng thái trang.
   - Thao tác xóa dữ liệu quan trọng phải có bước xác nhận rõ ràng.

4. **Nhất quán và quy chuẩn (Consistency and standards)**
   - Các nút bấm cùng một cấp độ hành động phải có cùng kích thước, kiểu dáng và vị trí logic tương đương trên mọi màn hình.

5. **Ngăn ngừa lỗi (Error prevention)**
   - Vô hiệu hóa hoặc cảnh báo sớm khi người dùng nhập dữ liệu không hợp lệ trước khi bấm Submit.
   - Ngăn chặn việc gửi trùng lặp bằng cơ chế debounce hoặc loading state khóa nút bấm.

6. **Nhận diện thay vì ghi nhớ (Recognition rather than recall)**
   - Hiển thị gợi ý rõ ràng bên cạnh các trường nhập liệu phức tạp.
   - Trạng thái các bộ lọc (filter chips) đã chọn phải nhìn thấy được và có thể hủy chọn dễ dàng.

7. **Linh hoạt và hiệu quả sử dụng (Flexibility and efficiency of use)**
   - Hỗ trợ phím `Enter` để submit form, phím `Tab` để chuyển trường nhập liệu tuần tự theo thứ tự hợp lý.

8. **Thiết kế thẩm mỹ và tinh giản (Aesthetic and minimalist design)**
   - Loại bỏ các thành phần gây nhiễu thị giác không cần thiết.
   - Giữ tỷ lệ khoảng trắng cân đối, không nhồi nhét thông tin dày đặc.

9. **Giúp người dùng nhận biết và khắc phục lỗi (Help users recognize, diagnose, and recover from errors)**
   - Thông báo lỗi phải chỉ rõ vị trí bị sai và hướng dẫn cách sửa cụ thể (ví dụ: *"Vui lòng nhập mật khẩu tối thiểu 8 ký tự"* thay vì *"Lỗi dữ liệu"*).

10. **Trợ giúp và tài liệu hướng dẫn (Help and documentation)**
    - Các form phức tạp cần có tooltip giải thích ý nghĩa các thuật ngữ nghiệp vụ.

---

## 2. Tiêu Chuẩn Trải Nghiệm Di Động (Mobile Usability)

* **Vùng chạm tối thiểu (Touch Target Size):** Mọi nút bấm, link hoặc icon có thể bấm được trên màn hình mobile 390px phải có kích thước tối thiểu $44 \times 44$ pixel.
* **Quy tắc không tràn ngang (Zero Horizontal Overflow):** Toàn bộ nội dung trang web phải co giãn vừa vặn trong chiều rộng khung nhìn mobile, không làm xuất hiện thanh cuộn ngang gây lệch trải nghiệm vuốt ngón tay.
* **Khả năng hiển thị bàn phím ảo (Virtual Keyboard Resilience):** Form nhập liệu trên mobile không được để bàn phím che khuất nút Submit hoặc nội dung đang gõ.
