# Ví dụ 1 — Bài Facebook mỹ phẩm (category: cosmetics, channel: facebook)

**Brief:** Dầu gội phủ bạc thảo dược, khách hàng 45-60 tuổi, giọng thương hiệu: ấm áp, mộc mạc, không phóng đại.
**Bằng chứng có trong `facts_evidence.md`:** Phiếu công bố mỹ phẩm số 123456/25/CBMP-QLD; thử nghiệm 30 người của Viện Kiểm nghiệm X năm 2025: 26/30 người thấy tóc bạc được phủ màu sau 3 lần gội; giá 289.000 đồng/chai 300 ml.

## TRƯỚC (bản nháp bị linter chặn: 9 lỗi)
```text
🔥 THUỐC PHỦ BẠC SỐ 1 VIỆT NAM — ĐEN TÓC VĨNH VIỄN!
Trong kỷ nguyên số, mái tóc đóng vai trò then chốt trong hình ảnh của bạn.
Sản phẩm 100% thiên nhiên, an toàn tuyệt đối cho mọi loại da, không tác dụng phụ.
Trị dứt điểm tóc bạc chỉ sau 1 lần gội, được bác sĩ khuyên dùng!
```
Lỗi: "thuốc phủ bạc", "số 1" không nguồn, em dash, "vĩnh viễn", 2 cụm sáo rỗng, "100% thiên nhiên", "an toàn tuyệt đối", "mọi loại da", "không tác dụng phụ", "trị dứt điểm", "bác sĩ khuyên dùng".

## SAU (đạt: `fact_checker.py --category cosmetics` exit 0)
```text
Sáng nào chú Hòa cũng mất 10 phút soi gương nhổ tóc bạc.

Dầu gội phủ bạc thảo dược giúp phủ màu tóc bạc ngay trong lúc gội, không cần ra tiệm nhuộm.
Trong thử nghiệm trên 30 người, 26 người thấy tóc bạc được phủ màu sau 3 lần gội (Theo Viện Kiểm nghiệm X, 2025).

Cách dùng cho người mới:
1. Làm ướt tóc, xoa dầu gội từ chân tóc.
2. Ủ 10 phút rồi xả sạch.
3. Gội 2-3 lần mỗi tuần để màu đều.

Màu phủ có thể khác nhau tùy chất tóc; nên thử trên một lọn tóc nhỏ trước.
Giá 289.000 đồng/chai 300 ml. Phiếu công bố mỹ phẩm số 123456/25/CBMP-QLD.

👇 Cô chú đang phủ bạc bằng cách nào? Chia sẻ để mọi người cùng tham khảo nhé.

Sản phẩm mỹ phẩm, không phải là thuốc và không có tác dụng thay thế thuốc chữa bệnh.
```
Vì sao đạt: mở bằng tình huống thật; mọi con số có nguồn cùng dòng; dùng "phủ màu" thay "trị"; nói rõ giới hạn kết quả; có câu bắt buộc của nhóm mỹ phẩm.
