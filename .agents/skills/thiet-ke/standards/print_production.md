# Chuẩn sản xuất ấn phẩm in (thiet-ke)

## 1. Thông số kỹ thuật bắt buộc

| Ấn phẩm | Khổ thành phẩm (trim) | Bleed | Trang PDF (trim + 2 x bleed) | Lề an toàn | Template |
|---|---|---|---|---|---|
| Tờ gấp 3 A4 (roll fold) | 297 x 210 mm | 3 mm | 303 x 216 mm | 6 mm từ mép xén và nếp gấp | `leaflet_trifold_a4.html` |
| Tờ gấp đôi A4 -> A5 | 297 x 210 mm | 3 mm | 303 x 216 mm | 6 mm | `leaflet_bifold_a4.html` |
| Poster A3 dọc | 297 x 420 mm | 3 mm | 303 x 426 mm | 10 mm | `poster_a3.html` |
| Slide 16:9 | 338.67 x 190.5 mm | 0 | 338.67 x 190.5 mm | 16 mm | `slides_16x9.html` |

- Gấp 3 kiểu cuộn: panel gấp vào trong rộng 97 mm, hai panel còn lại 100 mm (tổng 297). Mặt ngoài: [nắp gấp 97][bìa sau 100][bìa trước 100]; mặt trong: [100][100][97].
- Nền màu / ảnh chạm mép PHẢI kéo hết vào vùng bleed. Chữ, logo, QR PHẢI nằm trong lề an toàn.
- Ảnh: độ phân giải hiệu dụng >= 300 ppi ở kích thước đặt. Số pixel cần = mm / 25.4 x 300 (100 mm -> 1181 px; A3 tràn lề -> 3579 x 5031 px).
- Font: chỉ dùng font đóng gói `.agents/skills/_shared/fonts` (Be Vietnam Pro, Spectral). Font khác chưa có file cục bộ sẽ rơi về Times/Helvetica và vỡ dấu tiếng Việt; preflight sẽ chặn.
- Không dùng emoji trong ấn phẩm in (bị nhúng thành ảnh bitmap Type3). Dùng icon SVG nội tuyến.
- Màu: Chromium chỉ xuất RGB. Luôn ghi khi bàn giao: `[CẦN XÁC MINH: nhà in nhận PDF RGB hay yêu cầu CMYK]`. Tránh màu RGB quá rực (xanh neon, tím điện) vì sẽ xỉn khi chuyển CMYK.

## 2. Chuẩn thẩm mỹ (mức "giám đốc thiết kế")

1. **Một điểm nhìn chính mỗi mặt.** Bìa trước chỉ gồm: ảnh/hình chủ đạo + tên thương hiệu + 1 thông điệp. Không nhồi bảng giá lên bìa.
2. **Thang chữ rõ ràng** (tờ gấp): nhãn nhỏ 7.5pt in hoa giãn chữ -> tiêu đề 15-19pt serif đậm -> thân 9-10.5pt sans, dòng 1.5. Tối đa 2 họ chữ, 3 cỡ chữ mỗi panel.
3. **Màu:** 1 màu thương hiệu + 1 màu nhấn + nền trung tính. Chữ thân tương phản >= 4.5:1 (nên >= 7:1 khi in nhỏ). Không đặt chữ trên ảnh nếu không có lớp phủ tối/sáng.
4. **Lưới và khoảng trắng:** canh mọi khối theo cùng lề trái của panel; khoảng cách dọc theo bội số 2-2.5 mm. Khoảng trống lớn ở nửa dưới panel là lỗi bố cục: phân bổ lại (đẩy khối xuống, thêm ảnh, trích dẫn, ưu đãi) chứ không để trống.
5. **Trình tự đọc gấp 3:** bìa trước (thu hút) -> nắp gấp trong (câu chuyện/lý do) -> 3 panel trong (nội dung chính, đọc liền mạch) -> bìa sau (liên hệ, bản đồ, QR, ưu đãi).
6. **Không bịa dữ kiện.** Tên, địa chỉ, điện thoại, giá, giấy phép, chứng nhận, số liệu, đánh giá khách hàng chỉ lấy từ người dùng. Thiếu -> `[CẦN XÁC MINH: ...]` hiển thị nguyên văn trên bản nháp.

## 3. Checklist soát ảnh xem trước (bắt buộc, từng trang)

- [ ] Dấu tiếng Việt hiển thị đúng ở mọi cỡ chữ (soi kỹ chữ đậm/tiêu đề: ề, ố, ự, ẫ).
- [ ] Không chữ nào bị cắt, chạm mép xén, hoặc vắt qua nếp gấp.
- [ ] Chữ đọc rõ trên nền (đặc biệt chữ trên ảnh, chữ xám nhỏ).
- [ ] Ảnh nét, không vỡ, không méo tỉ lệ; nền tràn lề kín vùng bleed (ảnh `_full.png`).
- [ ] Không còn `[[placeholder]]`; các `[CẦN XÁC MINH]` đã được liệt kê cho người dùng.
- [ ] Bố cục cân: không panel nào trống nửa trang, không panel nào chật.
- [ ] Nội dung khớp `facts.md` (đối chiếu từng giá, giờ, địa chỉ).
