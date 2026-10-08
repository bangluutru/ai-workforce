# SỔ TAY CHUẨN HÓA VĂN BẢN PHÁT THANH TIẾNG VIỆT (SPOKEN RULES)

Tài liệu hướng dẫn quy tắc chuẩn hóa văn bản dành cho biên tập viên và mô hình giọng đọc AI (VieNeu-TTS / Kokoro) trong kỹ năng Sách Nói AI (`sach-noi`).

---

## 1. NGUYÊN TẮC VÀNG: VIẾT ĐỂ NGHE BẰNG TAI

1. **Khử hoàn toàn dấu ngoặc kép:**
   - Trong tiếng Việt viết, dấu ngoặc kép `“...”` được dùng để trích dẫn hoặc nhấn mạnh.
   - Khi nạp vào mô hình TTS tiếng Việt (VieNeu-TTS), mô hình sẽ đọc to thành *"dấu ngoặc kép [từ] đóng dấu ngoặc kép"*, gây khó chịu cho người nghe.
   - **Quy tắc:** Bộ chuẩn hóa `spoken_normalizer.py` tự động lược bỏ toàn bộ ký tự ngoặc kép nhưng giữ nguyên vẹn nội dung bên trong.
2. **Khử phụ thuộc vào thị giác:**
   - Lược bỏ hoàn toàn các câu chỉ có nghĩa trên trang giấy: *"xem hình 3 bên dưới"*, *"như trong bảng trên"*, số trang, chú thích cuối trang.
   - Bảng biểu được chuyển thành văn xuôi: *"Bảng số liệu gồm ba chỉ số chính. Thứ nhất là doanh thu, thứ hai là chi phí, và thứ ba là lợi nhuận ròng."*
   - Sơ đồ được diễn giải thành một câu tóm tắt nội dung thông điệp.
3. **Ngắt nhịp thở câu văn:**
   - Độ dài lý tưởng của một câu sách nói là từ **15 đến 25 chữ**, không vượt quá **35 chữ**.
   - Câu dài nhiều mệnh đề phụ phải được tách thành 2-3 câu đơn kết nối tự nhiên bằng liên từ: *"Vì vậy"*, *"Do đó"*, *"Đồng thời"*.
   - Không dùng ngoặc đơn: Nội dung trong ngoặc đơn phải được tách thành một câu giải nghĩa riêng.

---

## 2. BẢNG MỞ RỘNG TỪ VIẾT TẮT & THUẬT NGỮ THÔNG DỤNG

| Từ viết tắt | Dạng phát thanh chuẩn | Ghi chú |
|---|---|---|
| `TP.HCM`, `TPHCM`, `Tp.HCM` | **Thành phố Hồ Chí Minh** | Tránh đọc ngắc ngứ từng chữ |
| `PGS.TS.` | **Phó giáo sư Tiến sĩ** | Danh xưng học thuật |
| `GS.TS.` | **Giáo sư Tiến sĩ** | Danh xưng học thuật |
| `ThS.` / `TS.` / `BS.` | **Thạc sĩ** / **Tiến sĩ** / **Bác sĩ** | |
| `UBND` / `HĐND` | **Ủy ban nhân dân** / **Hội đồng nhân dân** | Cơ quan hành chính |
| `BHXH` / `BHYT` / `BHTN` | **Bảo hiểm xã hội** / **Bảo hiểm y tế** / **Bảo hiểm thất nghiệp** | An sinh xã hội |
| `TNHH` / `CP` | **Trách nhiệm hữu hạn** / **Cổ phần** | Loại hình doanh nghiệp |
| `v.v.` / `vv.` | **Vân vân** | Liệt kê |
| `vd.` / `VD.` | **Ví dụ** | |
| `tr.` | **Trang** | |

---

## 3. PHÁT ÂM THUẬT NGỮ QUỐC TẾ & CHỮ VIẾT TẮT TIẾNG ANH

| Ký hiệu | Phiên âm phát thanh tiếng Việt |
|---|---|
| `KPI` | **ca pê i** |
| `OKR` | **ô ca rờ** |
| `CEO` | **xi i ô** |
| `CFO` | **xi ép ô** |
| `CTO` | **xi ti ô** |
| `COO` | **xi ô ô** |
| `AI` | **a i** |
| `IT` | **ai ti** |
| `HR` | **hát rờ** |
| `PR` | **pê rờ** |
| `ROI` | **rờ ô i** |
| `GDP` | **giê đê pê** |
| `P&L` | **pê và en** |
| `SOP` | **ét ô pê** |
| `MVP` | **em vê pê** |
| `UI / UX` | **u i / u ích** |
| `B2B / B2C` | **bi to bi / bi to xi** |
| `4P / 7P` | **bốn Pê / bảy Pê** (Tránh đọc nhầm thành 4 phút) |

---

## 4. QUY TẮC ĐỌC SỐ, TIỀN TỆ VÀ KÝ HIỆU SỐ HỌC

1. **Số La Mã trong đề mục:**
   - `Chương I, Chương II, Chương IV, Chương IX, Chương X` $\rightarrow$ Đọc thành: *"Chương một, Chương hai, Chương bốn, Chương chín, Chương mười"*.
   - Lưu ý đặc biệt: Chỉ chuyển đổi khi đứng sau các danh từ đề mục (`Chương`, `Phần`, `Mục`, `Bài`, `Tập`), không đụng vào từ tiếng Việt bình thường (như *"Bài viết"*).
2. **Tỷ lệ phần trăm (%):**
   - `50%` $\rightarrow$ *"50 phần trăm"*.
   - `0.5%` $\rightarrow$ *"không phẩy năm phần trăm"*.
3. **Phân số thông dụng:**
   - `1/2` $\rightarrow$ *"một nửa"* hoặc *"một phần hai"*.
   - `1/3` $\rightarrow$ *"một phần ba"*.
   - `2/3` $\rightarrow$ *"hai phần ba"*.
   - `1/4` $\rightarrow$ *"một phần tư"*.
   - `3/4` $\rightarrow$ *"ba phần tư"*.
4. **Khoảng số:**
   - `2-3 ngày` $\rightarrow$ *"2 đến 3 ngày"*.
   - `10-15 triệu` $\rightarrow$ *"10 đến 15 triệu"*.
5. **Tiền tệ:**
   - `100.000đ` hoặc `100.000 VNĐ` $\rightarrow$ *"100.000 đồng"*.
   - `$50` $\rightarrow$ *"50 đô la"*.
