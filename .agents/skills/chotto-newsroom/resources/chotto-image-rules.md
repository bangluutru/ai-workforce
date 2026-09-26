# QUY CHUẨN TẠO ẢNH MINH HỌA BÀI VIẾT (IMAGE GENERATION RULES)

> Hướng dẫn chi tiết về phong cách thị giác, kỹ thuật prompt và các giới hạn khi tạo ảnh bìa bài viết ChottoDay bằng công cụ native `generate_image`.
> Nguồn đúng: `chottoday/docs/brief-anh-minh-hoa.md` mục "Luật bắt buộc" và `chottoday/docs/huong-dan-dang-bai.md` (đoạn "Model sinh ảnh được vẽ ảnh bìa"). Hai tài liệu đó đổi thì file này đổi theo.

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

## 2. CHỮ TRÊN ẢNH: ĐƯỢC CÓ, NHƯNG ĐÚNG TỪNG NÉT

> [!CAUTION]
> **Luật đã đổi ngày 2026-09-26.** Trước đây cấm chữ hoàn toàn, nên ảnh ra toàn bàn gỗ và sổ trắng, không kể được gì. Model mới viết chữ tốt hơn hẳn, nên ảnh **được** có chữ khi chữ giúp kể chuyện (biển 交番, phong bì 給与明細, bìa hồ sơ 賃貸借契約書).
> Nhưng model vẫn **tự bịa chữ** ở những chỗ prompt không nhắc tới. Repo ChottoDay từng phải xoá ảnh thẻ cư trú ghi `日本国民政` thay vì `日本国政府`, `RESIOENCE CARD` thay vì `RESIDENCE CARD`. Đợt ảnh 2026-09-26 bị trả một tấm vì gáy sách ghi `シンプに生さる` (đúng là シンプルに生きる) và laptop có logo Apple. Ảnh bìa bài lương tối thiểu 2026 có hàng phím máy tính mang ký tự méo. Chữ sai trên ảnh bài hướng dẫn thủ tục thì tệ hơn không có ảnh: người đọc tin vào thứ họ nhìn thấy.

1. ✅ **Chữ đọc được chỉ là chữ ghi nguyên văn trong prompt.**
   - Một hai cụm tiếng Nhật ngắn, đã kiểm chính tả, viết trong prompt đúng từng ký tự và nói rõ đặt ở đâu: `the sign reads 交番 clearly legible`.
   - Prompt phải có câu khoá: `the only legible text in the whole image is <chữ>, written exactly like that` và yêu cầu mọi giấy tờ, màn hình, bao bì, biển khác **nhoè hẳn hoặc không có chữ**.
   - Không có chữ nào giúp kể chuyện thì dùng bản không chữ (mục 4, câu khoá `No legible text anywhere`).
   - Cần chữ **dài** hay chữ **tiếng Việt có dấu** thì không dùng model sinh ảnh. Người đăng dùng `scripts/images/card.py` trong repo ChottoDay (vẽ bằng font thật, kiểm từng ký tự).
   - **Tránh đồ vật có nhãn in nhỏ** mà prompt không cần: máy tính bỏ túi, bàn phím, điều khiển, đồng hồ số, tiền xu, tiền giấy, gáy sách, bao bì. Model vẽ ký tự méo lên đó dù prompt đã cấm.
2. ❌ **Không bản sao giấy tờ chính thức:** thẻ cư trú, My Number, bằng lái, hộ chiếu, giấy nộp thuế có mẫu. Chỉ được là bìa hồ sơ hay tờ giấy có tiêu đề, phần ruột nhoè.
3. ❌ **Không con số khẳng định sự thật:** tiền lương, tiền thuế, mức phí, ngày hạn. Con số sai trên ảnh bìa làm người đọc hiểu sai bài. Số trung tính (số thứ tự chờ, số phòng) thì được.
4. ❌ **Không logo thương hiệu thật và không watermark:** ngân hàng, bưu điện, hãng điện thoại, hãng xe, logo trên laptop.
5. ❌ **Không vẽ người có thật:** người nổi tiếng, chính khách, nhân vật trong tin. Người trong ảnh là nhân vật hư cấu, nhìn bình thường, không cười kiểu mẫu ảnh.

### Tự soát trước khi bàn giao (bắt buộc)

- Phóng to (crop 3–4 lần) **mọi vùng có chữ hoặc có thể có chữ**: biển, bìa hồ sơ, màn hình, gáy sách, cốc, bao bì, bàn phím, xe cộ.
- **Đọc lại từng ký tự** chữ đọc được, so với chữ trong prompt. Sai một nét thì sinh lại, **không** sửa chữ bằng công cụ chỉnh ảnh.
- Chữ lạ (không có trong prompt) mà đọc được thì cũng sinh lại, kể cả khi nó đúng chính tả.
- Ghi vào gói duyệt: chữ đọc được trên ảnh là gì, ở đâu. Người duyệt vẫn đọc lại một lần nữa trước khi đặt vào repo.

---

## 3. PHONG CÁCH HÌNH ẢNH CHỦ ĐẠO (EDITORIAL AESTHETICS)

* **Phong cách:** Ảnh phóng sự đời thường (photorealistic documentary), chi tiết, chân thực, đậm chất đời sống Nhật Bản hiện đại. Không phải ảnh stock, không dàn dựng quá tay.
* **Kể đúng tình huống của bài:** thường là một người Việt đang sống ở Nhật, đang ở đúng khoảnh khắc bài nói tới, biểu cảm tự nhiên. Kèm chi tiết thật của Nhật: dây điện, xe đạp dựng tường, sàn tatami, cửa kính ban công.
* **Ánh sáng & Tông màu:** Ánh sáng tự nhiên, ấm, dịu mắt. Không màu neon, không filter siêu thực, không nhìn như ảnh quảng cáo ngân hàng.
* **Ví dụ tình huống (chữ đọc được ghi trong ngoặc):**
  - **Lương / thuế:** tối ngày lương, người trẻ ngồi bàn thấp mở phong bì bảng lương (給与明細); tờ bảng lương cầm nghiêng, số nhoè.
  - **Mất thẻ cư trú:** cầm ví có ngăn thẻ trống, đi về phía đồn cảnh sát ở góc phố (交番).
  - **Thuê nhà:** ngày nhận nhà, cầm chìa khoá trong căn hộ trống, tay cầm bìa hồ sơ (賃貸借契約書).
  - **Gia đình / trẻ em:** giày trẻ em ở bậc genkan, bố mẹ phía sau. Không cần chữ.

---

## 4. CÔNG THỨC PROMPT TIẾNG ANH (PROMPT STRUCTURE)

Mọi prompt gửi vào `generate_image` viết bằng **tiếng Anh**, theo ba khối:

```text
Photorealistic documentary-style photo, wide 3:2 landscape. [Tình huống: ai, ở đâu, đang làm gì, biểu cảm, chi tiết Nhật Bản, ánh sáng].
Text rules: the only legible text in the whole image is [chữ] on [vị trí], written exactly like that. Any other paper, screen, sign or package must be blurred or have no writing. No readable numbers, no brand logos, no watermarks.
Camera: [35mm lens, f/2, eye level], natural grain, candid moment, not posed, not a stock photo.
```

Ảnh không chữ thì thay khối `Text rules` bằng:

```text
Text rules: no legible text anywhere; any paper, screen or sign must be out of focus. No numbers, no brand logos, no watermarks.
```

### Ví dụ prompt mẫu

* **Lương 30 man thực nhận bao nhiêu** (có chữ):
  ```text
  Photorealistic documentary-style photo, wide 3:2 landscape. Evening in a small, lived-in Tokyo apartment: a Vietnamese man in his late twenties, office shirt with the sleeves rolled up, sits cross-legged at a low wooden table reading his monthly payslip with a thoughtful expression. In his hand is an opened white envelope with the printed title 給与明細 clearly legible; the payslip itself is held at an angle so its figures are out of focus. On the table: a half-finished convenience-store bento, a glass of barley tea, his phone face down. Warm desk-lamp light mixed with the blue of the window at dusk.
  Text rules: the only legible text in the whole image is 給与明細 on the envelope, written exactly like that. Any other paper, screen or package must be blurred or have no writing. No readable numbers, no brand logos, no watermarks.
  Camera: 35mm lens, f/2, eye level, natural grain, candid moment, not posed, not a stock photo.
  ```
* **Đổi bằng lái xe** (không chữ):
  ```text
  Photorealistic documentary-style photo, wide 3:2 landscape. Inside a white Japanese driving-test car on a test course: a Vietnamese man in his thirties grips the steering wheel, focused and a little nervous; beside him a Japanese examiner in a light-blue work jacket holds a clipboard. Through the windshield: white lane lines, orange cones, low hedges under an overcast sky. Right-hand drive.
  Text rules: no legible text anywhere; any paper, screen or sign must be out of focus. No license cards, no numbers painted on the road, no brand logos on the car, no watermarks.
  Camera: 24mm lens from the back seat, f/2.8, natural light, candid, not a stock photo.
  ```
