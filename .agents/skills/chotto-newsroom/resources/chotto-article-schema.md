# QUY CHUẨN CẤU TRÚC BÀI VIẾT CHOTTODAY (ARTICLE SCHEMA)

> Tài liệu tóm tắt hợp đồng dữ liệu (Data Contract) của tệp bài viết JavaScript trong ChottoDay.
> Nguồn chuẩn gốc (Canonical Sources):
> - Model logic: `chottoday/src/services/content/articleModel.js`
> - Trình dựng: `chottoday/src/services/content/buildArticle.js`
> - Bộ xuất bản file: `chottoday/scripts/build/emitArticleFile.js`

---

## 1. QUY CÁCH TỆP JAVASCRIPT XUẤT BẢN

Mỗi bài viết ChottoDay được lưu trữ độc lập dưới dạng một tệp JavaScript ES Module (`.js`), đặt tên theo định dạng `[slug].js`:

```javascript
export const articleLuongToiThieu2026 = {
  slug: 'luong-toi-thieu-nhat-ban-2026',
  title: 'Tăng lương tối thiểu toàn quốc Nhật Bản năm 2026: Chi tiết từng tỉnh',
  description: 'Chính phủ Nhật Bản công bố mức tăng lương tối thiểu theo giờ mới nhất áp dụng từ tháng 10/2026. Hướng dẫn cách kiểm tra phiếu lương cho người lao động.',
  category: 'work',
  targetAudience: 'Người lao động, thực tập sinh và kỹ năng đặc định tại Nhật',
  readingTime: 4,
  lastUpdated: '2026-09-25',
  publishedDate: '2026-09-25',
  verifiedDate: '2026-09-25',
  reviewer: 'CHƯA DUYỆT',
  status: 'review',
  tags: ['lương tối thiểu', 'luật lao động', 'thực tập sinh', 'lương nhật bản'],
  searchKeywords: ['mức lương tối thiểu 2026', 'tang luong nhat ban', '最低賃金 2026'],
  seo: {
    metaTitle: 'Tăng lương tối thiểu Nhật Bản 2026: Chi tiết mức lương từng tỉnh',
    metaDescription: 'Cập nhật bảng lương tối thiểu vùng mới nhất tại Nhật Bản năm 2026. Chi tiết mức tăng tại Tokyo, Osaka, Aichi và cách kiểm tra người sử dụng lao động trả đúng luật.',
    canonicalUrl: 'https://chottoday.com/articles/luong-toi-thieu-nhat-ban-2026',
    ogType: 'article'
  },
  sources: [
    {
      title: 'Thông cáo báo chí về mức lương tối thiểu vùng năm 2026',
      url: 'https://www.mhlw.go.jp/stf/newpage_example.html',
      organization: 'Bộ Y tế, Lao động và Phúc lợi Nhật Bản (MHLW)',
      publishedDate: '2026-08-15',
      verifiedDate: '2026-09-25',
      sourceType: 'official'
    }
  ],
  sections: [
    // Danh sách các khối nội dung (chỉ dùng 12 loại hợp lệ)
  ],
  relatedArticles: [],
  toolCTA: null
};

export default articleLuongToiThieu2026;
```

---

## 2. QUY TẮC BẮT BUỘC ĐỐI VỚI BẢN THẢO TÒA SOẠN

1. **`status: 'review'` (BẮT BUỘC):**
   - Mọi bản thảo do Tòa soạn AIWF tạo ra TUYỆT ĐỐI KHÔNG ĐƯỢC đặt là `'published'`.
   - Phải giữ trạng thái `'review'` để chờ con người thẩm định.
2. **`reviewer: 'CHƯA DUYỆT'` (BẮT BUỘC):**
   - Không được gán tên người duyệt giả định hoặc tên AI.
   - Giữ nguyên chuỗi `'CHƯA DUYỆT'` làm chốt chặn bảo vệ (Hard Blocker) ngăn hệ thống CI xuất bản tự động khi chưa có biên tập viên con người ký duyệt.
3. **Quy tắc đặt tên biến Export:**
   - Biến xuất bản có dạng `article` + CamelCase của slug.
   - Ví dụ: slug `luong-toi-thieu-2026` $\rightarrow$ biến `articleLuongToiThieu2026`.
   - Tệp phải có cả `export const [tênBiến]` và `export default [tênBiến]`.
4. **Định dạng ngày tháng:**
   - Chuẩn ISO 8601: `YYYY-MM-DD`.

---

## 3. CÁC HẠNG MỤC DỮ LIỆU BẮT BUỘC (FIELD INVENTORY)

| Trường dữ liệu | Kiểu dữ liệu | Yêu cầu kiểm chuẩn |
|---|---|---|
| `slug` | string | Viết thường, nối bằng gạch ngang ngắn (kebab-case), không dấu, không ký tự đặc biệt. |
| `title` | string | Tối đa 100 ký tự. Không chứa em-dash (`—`), không có dấu hai chấm (`:`) ở cuối. |
| `description` | string | Độ dài từ 120 đến 160 ký tự. Tóm tắt nội dung cốt lõi phục vụ hiển thị thẻ xem trước. |
| `category` | string | Bắt buộc là 1 trong 9 mã danh mục hợp lệ: `life`, `doc`, `work`, `health`, `study`, `tool`, `newcomer`, `job`, `family`. |
| `targetAudience` | string | Mô tả rõ đối tượng độc giả hướng tới. |
| `readingTime` | number | Thời gian đọc ước tính bằng phút (số nguyên dương, thường từ 3 đến 7). |
| `sources` | array | Tối thiểu 1 nguồn loại `official` (.go.jp hoặc cơ quan chính thức). |
| `sections` | array | Danh sách các đối tượng section. **CHỈ SỬ DỤNG 12 LOẠI HỢP LỆ.** |
| `tags` | array | 3 - 6 thẻ từ khóa ngắn. |
| `searchKeywords` | array | Từ khóa tìm kiếm bao gồm cả biến thể tiếng Việt không dấu và Kanji/Katakana. |
| `seo` | object | Chứa `metaTitle`, `metaDescription`, `canonicalUrl`, `ogType`. |
| `relatedArticles`| array | Mảng các slug bài viết liên quan (để trống nếu chưa rõ). |
| `toolCTA` | object / null | Trỏ đến công cụ tính toán trên ChottoDay (nếu có). |
