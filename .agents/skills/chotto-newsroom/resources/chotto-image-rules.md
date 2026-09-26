# QUY CHUẨN TẠO ẢNH MINH HỌA BÀI VIẾT (IMAGE GENERATION RULES)

> Hướng dẫn chi tiết về phong cách thị giác, kỹ thuật prompt và các điều cấm tuyệt đối khi tạo ảnh bìa bài viết ChottoDay bằng công cụ native `generate_image`.
> Nguồn tham chiếu: `chottoday/docs/brief-anh-minh-hoa.md` (luật cấm chữ, prompt mẫu cho từng bài cũ).
> Riêng **định dạng và tên file** theo mục 1 dưới đây (WebP, `<slug>.webp`); tài liệu repo còn ghi `.jpg` là bản cũ.

---

## 1. CÔNG CỤ VÀ THAM SỐ KỸ THUẬT (TOOL PARAMETERS)

Kỹ năng sử dụng công cụ tạo ảnh tích hợp sẵn `generate_image` của Antigravity IDE (không dùng API key bên ngoài):

* **Tỷ lệ khung hình (`AspectRatio`):** Chọn `'3:2'` (đây là tỷ lệ ngang gần nhất với chuẩn 2:1 landscape 1640×840 của ChottoDay).
* **Tên file ảnh (`ImageName`):** Đặt theo định dạng `[slug_ngan]_cover` (chữ thường, nối gạch dưới, tối đa 3 từ, ví dụ: `luong_toi_thieu_cover`).
* **Định dạng bàn giao: LUÔN WebP.** Ảnh từ `generate_image` (PNG/JPG, thường 500 KB - 1 MB) phải được chuyển sang WebP trước khi bàn giao:
  * Tên file: `<output_dir>/<slug>.webp`, **đúng bằng slug của bài**, không hậu tố `-cover`, không `.jpg`.
  * Chất lượng 80, giữ nguyên kích thước (cạnh dài 1200 - 1640 px). Mục tiêu **≤ 150 KB**; ảnh 1264×848 thực tế ra khoảng 50 KB.
  * Lệnh chuyển (Pillow có sẵn trên máy; không gọi API ngoài):
    ```bash
    python3 -c "from PIL import Image; Image.open('<ảnh gốc>').convert('RGB').save('<output_dir>/<slug>.webp', 'WEBP', quality=80, method=6)"
    ```
  * Không giữ bản PNG/JPG gốc trong `<output_dir>` để người đăng không chọn nhầm.
* **Khớp với bài:** file `.js` phải có `coverImage: '/images/featured/<slug>.webp'`. Trong Chotto Studio, người đăng chọn đúng file `<slug>.webp` ở ô "Ảnh bìa"; Studio lưu nó thành `public/images/featured/<slug>.webp`, khớp với `coverImage`.
* **Vì sao WebP:** ảnh bìa hiện ở trang chủ, trang chuyên mục và đầu bài. Bản JPG 691 KB của bài lương tối thiểu 2026 xuống còn 51 KB ở WebP mà mắt thường không phân biệt được.

---

## 2. 4 VÙNG CẤM TUYỆT ĐỐI VỀ HÌNH ẢNH (4 ABSOLUTE BANS)

> [!CAUTION]
> **TẠI SAO CẤM CHỮ VÀ MẶT NGƯỜI?**
> Các mô hình sinh ảnh AI luôn gặp lỗi nghiêm trọng khi sinh chữ Kanji, Katakana, Hiragana và dấu thanh tiếng Việt (chữ méo mó, vô nghĩa, sai chính tả). Đồng thời việc hiển thị khuôn mặt nhận diện được dễ vi phạm quyền riêng tư và bản quyền hình ảnh tại Nhật Bản.

1. ❌ **CẤM TUYỆT ĐỐI CHỮ VIẾT (NO TEXT / NO NUMBERS):**
   - Không được có chữ tiếng Nhật, tiếng Việt, tiếng Anh hay số trên ảnh.
   - Không để chữ trên màn hình máy tính, điện thoại, giấy tờ, sổ sách hay phong bì.
   - **Tránh luôn đồ vật có nhãn in nhỏ:** máy tính bỏ túi, bàn phím, điều khiển, đồng hồ số, tiền xu, tiền giấy. Prompt có ghi "no numbers" thì model vẫn vẽ phím, và nhãn trên phím ra ký tự méo. Ảnh bìa bài lương tối thiểu 2026 bị đúng lỗi này: hàng phím trên cùng là chữ vô nghĩa. Nhỏ thì khó thấy, nhưng người đọc tinh sẽ thấy.
   - **Tự kiểm trước khi bàn giao:** phóng to (crop 3-4 lần) mọi vùng có đồ vật nhỏ và nhìn kỹ. Thấy ký tự méo thì sinh lại với prompt bỏ đồ vật đó.
2. ❌ **CẤM BIỂN HIỆU & BẢNG CHỈ DẪN (NO SIGNAGE):**
   - Không có biển tên ga tàu, biển tên cơ quan chính phủ, bảng thông báo ngoài phố.
3. ❌ **CẤM LOGO & WATERMARK:**
   - Không có logo ngân hàng, logo bưu điện, biểu tượng thương mại của các công ty.
4. ❌ **CẤM KHUÔN MẶT NHẬN DIỆN ĐƯỢC (NO IDENTIFIABLE FACES):**
   - Chỉ dùng góc chụp từ sau lưng (back view), góc qua vai (over-the-shoulder), góc chụp từ trên cao (flat lay) hoặc cận cảnh bàn tay đang thao tác (hands close-up).

---

## 3. PHONG CÁCH HÌNH ẢNH CHỦ ĐẠO (EDITORIAL AESTHETICS)

* **Phong cách:** Chụp ảnh đời thực (Photorealistic Editorial Photography), tự nhiên, mộc mạc, đậm chất đời sống Nhật Bản hiện đại.
* **Ánh sáng & Tông màu:** Ánh sáng ban ngày tự nhiên (Natural daylight), ấm áp, dịu mắt (Muted warm tones), không dùng màu neon lòe loẹt hay filter siêu thực.
* **Tư duy ẩn dụ hình ảnh (Metaphorical Representation):**
  - **Chủ đề lương / thuế:** Bàn làm việc gỗ sạch sẽ, sổ tay mở trang trắng, cây bút, phong bì trắng trơn, cốc trà nóng dưới nắng sáng. (Không dùng máy tính bỏ túi, xem vùng cấm 1.)
  - **Chủ đề thẻ cư trú / My Number:** Bàn tay đang cầm một chiếc bao đựng thẻ bằng da thanh lịch (bên trong thẻ màu trơn không có chữ), đặt trên bàn gỗ.
  - **Chủ đề chuyển việc / phỏng vấn:** Cặp tài liệu da công sở đặt cạnh cửa sổ kính nhìn ra quang cảnh Tokyo buổi sớm.
  - **Chủ đề gia đình / trẻ em:** Đôi giày trẻ em nhỏ nhắn đặt ngay ngắn ở bậc cửa vào nhà (Genkan) kiểu Nhật Bản.

---

## 4. CÔNG THỨC PROMPT TIẾNG ANH BẮT BUỘC (MANDATORY PROMPT SUFFIX)

Mọi prompt gửi vào `generate_image` BẮT BUỘC phải viết bằng **tiếng Anh** và nối thêm đoạn hậu tố tiêu chuẩn (Suffix) dưới đây:

```text
[Mô tả bối cảnh và đồ vật ẩn dụ cụ thể]. No text, no lettering, no signage, no documents with visible writing, no numbers, no logos, no watermarks. Photorealistic, natural daylight, muted warm tones, shallow depth of field, cinematic Japanese editorial photography.
```

### Ví dụ Prompt Mẫu Chuẩn:
* **Bài viết về Tăng lương tối thiểu:**
  ```text
  A clean wooden office desk in Tokyo with a pen, an open notebook with completely blank white pages, a plain unmarked white envelope, and a ceramic cup of green tea in gentle morning window sunlight. No text, no lettering, no signage, no documents with visible writing, no numbers, no logos, no watermarks. Photorealistic, natural daylight, muted warm tones, shallow depth of field, cinematic Japanese editorial photography.
  ```
* **Bài viết về Thủ tục gia hạn thẻ cư trú:**
  ```text
  Close-up shot of hands holding a premium leather document holder and a blank translucent card with no text, on a warm minimalist wooden counter. No text, no lettering, no signage, no documents with visible writing, no numbers, no logos, no watermarks. Photorealistic, natural daylight, muted warm tones, shallow depth of field, cinematic Japanese editorial photography.
  ```
