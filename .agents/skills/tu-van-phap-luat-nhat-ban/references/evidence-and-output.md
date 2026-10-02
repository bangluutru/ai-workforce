# Chứng cứ và đầu ra

## Bảng nguồn

Mỗi căn cứ trọng yếu có ID nội bộ để kết nối với kết luận; ID không thay URL/tọa độ. Ghi tên Nhật, cơ quan, loại nguồn, số hiệu/định danh, điều/khoản/điểm/phụ lục hoặc mục/trang, phiên bản/ngày thi hành, ngày truy cập và URL trực tiếp.

Trích đoạn Nhật cần thiết và bản dịch Việt được phân biệt. Không yêu cầu số lượng trích dẫn tối thiểu, không chép toàn văn tài liệu có bản quyền. Nếu nguồn là FAQ/PDF/bản án thì dùng tọa độ phù hợp, không bịa số điều.

| ID | Loại, tên Nhật, tọa độ | Phiên bản/mốc | Trích đoạn hoặc nội dung hỗ trợ | URL và ngày truy cập | Kết luận/ngoại lệ | Trạng thái |
|---|---|---|---|---|---|---|

Quy tắc bắt buộc (được `scripts/check_evidence_table.py` kiểm): bảng có cột `ID`, cột chứa `URL` và cột `Trích đoạn`; mỗi dòng có URL https, ngày `YYYY-MM-DD`, trích đoạn không rỗng; nguồn luật e-Gov phải có trích đoạn tiếng Nhật trong 「」, có nguyên văn trong file `<research_dir>/sources/*.txt` đã lưu bằng `fetch_jp_source.py`. Mỗi câu `[XÁC ĐỊNH]` trong báo cáo ghi ID nguồn, VD `(E2)`. "Đã kiểm chứng" mà không có URL/ngày/trích đoạn là lỗi.

Trạng thái **nguồn**: đã đọc/kiểm chứng; mới có snippet; chưa đọc được; chưa xác định phiên bản. Trạng thái **hồ sơ**: đáp ứng theo chứng cứ; chưa đáp ứng; chưa xác định; không thuộc phạm vi có lý do; có căn cứ cấm cho tình huống đã xác định. Không cộng hai loại trạng thái thành một điểm “độ tin cậy” giả.

## Vụ việc pháp lý

Kết luận và giới hạn → tình tiết/giả định → câu hỏi → căn cứ → áp dụng → phương án có thật → hồ sơ, cơ quan, thời hạn và bước tiếp. Phân biệt thời hạn luật định, thời gian xử lý công bố và ước tính; phí nhà nước, phí kiểm nghiệm và báo giá dịch vụ.

Chưa đủ căn cứ vẫn có thể trả phần đã xác minh, nhưng không kết luận chắc cho phần còn thiếu. Nêu dữ kiện/nguồn nào sẽ giải quyết khoảng trống, thay vì chỉ disclaimer.

## Hồ sơ sản phẩm

Đầu ra tối thiểu theo phạm vi được hỏi: thông tin SKU/phiên bản; phân loại; mã/thuế nếu được hỏi; ma trận nghĩa vụ; hồ sơ thiếu; điểm trước vận chuyển/trước bán; bước tiếp theo. Không yêu cầu SKU nếu người dùng chỉ hỏi quy định chung.

| Công đoạn | Nghĩa vụ/căn cứ | Chủ thể | Chứng cứ hồ sơ | Mốc/hạn | Trạng thái, hành động |
|---|---|---|---|---|---|

Với HS/thuế, theo bảng ở [customs-and-tariffs.md](customs-and-tariffs.md). Với claim, xuất `câu hiện tại → vấn đề/căn cứ → câu sửa dự kiến → bằng chứng/điều kiện còn cần`; câu sửa không phải chứng nhận hợp pháp nếu chưa đối chiếu hồ sơ.

Nếu người dùng cần báo cáo, lưu report và bảng chứng cứ khi hữu ích. Không lưu số giấy tờ cá nhân/bí mật công thức vượt nhu cầu. Dùng thư mục do người dùng chỉ định hoặc quy ước workspace; không tự thêm đầu ra vào thư mục cài skill.
