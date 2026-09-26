# GÓI THẨM ĐỊNH TÒA SOẠN CHOTTODAY (REVIEW PACKAGE)

> **Phiên làm việc:** {{DATE}}
> **Trạng thái:** ⏳ CHỜ BIÊN TẬP VIÊN DUYỆT (PENDING HUMAN REVIEW)
> **Số lượng tin tức đã quét:** {{TOTAL_SCANNED}} sự kiện
> **Số lượng bài viết đề xuất xuất bản:** {{TOTAL_PROPOSED}} bài (Điểm đánh giá $\ge 60/100$)
> **Thư mục lưu trữ thành phẩm:** `{{OUTPUT_DIR}}`

---

## 1. BẢNG TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)

| STT | Tên sự kiện / Dự thảo | Cơ quan chủ quản | Điểm Rubric | Quyết định | Tệp bản thảo tương ứng |
|:---:|---|---|:---:|:---:|---|
| 1 | {{EVENT_1_TITLE}} | {{EVENT_1_ORG}} | **{{EVENT_1_SCORE}}/100** | ✅ Đề xuất xuất bản | `{{EVENT_1_SLUG}}.js` |
| 2 | {{EVENT_2_TITLE}} | {{EVENT_2_ORG}} | **{{EVENT_2_SCORE}}/100** | ⚠️ Theo dõi thêm | *Không viết bài (Lưu hồ sơ)* |

---

## 2. CHI TIẾT BÀI VIẾT ĐỀ XUẤT {{INDEX}}: {{ARTICLE_TITLE}}

### 2.1. Thông Tin Định Danh (Metadata)
* **Tiêu đề bài viết:** `{{ARTICLE_TITLE}}`
* **Slug URL:** `{{ARTICLE_SLUG}}`
* **Danh mục (`category`):** `{{ARTICLE_CATEGORY}}`
* **Nhóm độc giả mục tiêu:** {{TARGET_AUDIENCE}}
* **Thời gian đọc ước tính:** {{READING_TIME}} phút
* **Trạng thái tệp:** `status: 'review'` | `reviewer: 'CHƯA DUYỆT'`

### 2.2. Kết Quả Chấm Điểm Liên Quan (Relevance Rubric Breakdown)
* **Tổng điểm: {{TOTAL_SCORE}}/100**
  - Trục 1 (Đối tượng tác động - max 25đ): {{SCORE_POPULATION}}đ ({{NOTE_POPULATION}})
  - Trục 2 (Tính hành động - max 25đ): {{SCORE_ACTION}}đ ({{NOTE_ACTION}})
  - Trục 3 (Mức độ khẩn cấp - max 20đ): {{SCORE_URGENCY}}đ ({{NOTE_URGENCY}})
  - Trục 4 (Mức độ ảnh hưởng - max 20đ): {{SCORE_SEVERITY}}đ ({{NOTE_SEVERITY}})
  - Trục 5 (Khoảng trống thông tin - max 10đ): {{SCORE_GAP}}đ ({{NOTE_GAP}})

### 2.3. Tóm Tắt Gói Sự Thật Kiểm Chứng (Fact Pack Summary)
* **Nguồn chính thức (Official Sources):**
  - [{{SOURCE_TITLE}}]({{SOURCE_URL}}) — Cơ quan: {{SOURCE_ORG}} (Cấp độ 1: `.go.jp`)
* **Tuyên bố cốt lõi đã xác thực (Verified Claims):**
  1. {{CLAIM_1_DESC}} — *Chứng cứ tiếng Nhật:* 「{{CLAIM_1_JP_QUOTE}}」
  2. {{CLAIM_2_DESC}} — *Chứng cứ tiếng Nhật:* 「{{CLAIM_2_JP_QUOTE}}」
* **Hạng mục cần lưu ý hoặc gắn cờ:**
  - `{{CONFIDENCE_FLAGS}}`

### 2.4. Ảnh Minh Họa Đề Xuất (Generated Image)
* **Tệp ảnh bìa:** `{{OUTPUT_DIR}}/{{ARTICLE_SLUG}}.webp` ({{IMAGE_SIZE_KB}} KB, {{IMAGE_WIDTH}}×{{IMAGE_HEIGHT}})
* **`coverImage` trong bài:** `/images/featured/{{ARTICLE_SLUG}}.webp`
* **Tỷ lệ:** 3:2 ngang (chuẩn bị crop/fit cho 2:1 header)
* **Prompt tiếng Anh đã sử dụng:**
  ```text
  {{IMAGE_PROMPT}}
  ```
* **Kiểm tra 4 Vùng cấm:** ✅ Không chữ (đã phóng to soi cả nhãn nhỏ trên đồ vật), ✅ Không biển hiệu, ✅ Không logo, ✅ Không mặt người nhận diện được.

### 2.5. Báo Cáo Kiểm Định Kỹ Thuật (Quality Gate Audit)
* **Cú pháp ChottoDay Schema:** ✅ PASS (100% hợp lệ 12 loại section, đúng 9 danh mục)
* **Khử dấu vết AI:**
  - Số ký tự gạch ngang dài em-dash (`—`): **0**
  - Số dấu phẩy Oxford (`, và`): **0**
  - Dấu hai chấm cuối heading: **0**
* **Tuân thủ Luật R5 (Chống over-claim):** ✅ Đạt chuẩn (0 từ ngữ cấm)
* **Cổng đối chiếu Fact Pack:** ✅ Mọi số, ngày, điều luật trong bài có trong Fact Pack

---

### 2.6. Bảng đối chiếu nhanh cho người duyệt

> Mỗi dòng là một con số, ngày hoặc điều luật có trong bài. Mở link, tới đúng vị trí,
> so với cột "Trong bài". Đây là việc cổng tự động không làm thay được: nó chỉ biết số
> trong bài có trong Fact Pack, không biết Fact Pack chép đúng nguồn.

| Trong bài | Giá trị | Nguồn (link) | Vị trí trong nguồn | Đã so |
|---|---|---|---|:---:|
| {{CHECK_1_WHERE_IN_ARTICLE}} | {{CHECK_1_VALUE}} | {{CHECK_1_URL}} | {{CHECK_1_LOCATION}} | ☐ |
| {{CHECK_2_WHERE_IN_ARTICLE}} | {{CHECK_2_VALUE}} | {{CHECK_2_URL}} | {{CHECK_2_LOCATION}} | ☐ |

* **Giai đoạn pháp lý:** {{LEGAL_STAGE}}. Bài có viết đúng giai đoạn không (đề xuất / dự kiến / đã có hiệu lực)?
* **Cách tính / thủ tục trong bài** lấy từ: {{PROCEDURE_SOURCE}}

---

## 3. HƯỚNG DẪN THAO TÁC CHO BIÊN TẬP VIÊN DUYỆT BÀI

Để đưa bài viết vào hệ thống sản xuất của ChottoDay, biên tập viên thực hiện các bước sau:

1. **Xem xét nội dung bản thảo:**
   - Mở tệp bản thảo tại: `{{OUTPUT_DIR}}/{{ARTICLE_SLUG}}.js`
   - Đọc đối chiếu với tài liệu gốc tiếng Nhật trong Fact Pack: `{{OUTPUT_DIR}}/fact-pack-{{ARTICLE_SLUG}}.md`
2. **Nhập vào ChottoDay qua Chotto Studio** (không chép tay vào `src/content/articles/`):
   - Trong repo ChottoDay: `npm run dev`, mở `localhost:5173/studio`.
   - Dán nội dung `{{ARTICLE_SLUG}}.js`.
   - Ở ô **"Ảnh bìa"**, chọn `{{OUTPUT_DIR}}/{{ARTICLE_SLUG}}.webp`. Studio lưu thành `public/images/featured/{{ARTICLE_SLUG}}.webp`, khớp `coverImage`. Quên bước này thì bài trỏ tới ảnh không có.
   - Bấm ghi. Studio ghi file bài, thêm hai dòng vào `articlesList.js` và vẽ thẻ OG bằng `card.py`.
3. **Ký duyệt xuất bản (chỉ sau khi đã mở từng link nguồn và đối chiếu từng con số):**
   - Đổi `status: 'review'` thành `status: 'published'`.
   - Đổi `review.reviewer: 'CHƯA DUYỆT'` thành tên hoặc bút danh của bạn.
4. **Chạy kiểm thử xác thực trong kho ChottoDay:**
   ```bash
   npm run validate
   npm test
   ```
