# QUY CHUẨN CẤU TRÚC BÀI VIẾT CHOTTODAY (ARTICLE SCHEMA)

> Hợp đồng dữ liệu của tệp bài viết `.js` trong ChottoDay.
>
> **Nguồn đúng duy nhất:** `chottoday/docs/huong-dan-tao-bai-viet.md` (Phần 2 và Phần 4).
> Tài liệu đó có test canh (`scripts/test-studio.mjs` mục 12) nên luôn khớp code.
> Nếu repo ChottoDay có trong môi trường, ĐỌC nó trước khi viết; chỗ nào file này
> lệch với nó thì nó đúng, file này sai.
>
> Code tham chiếu: `src/services/content/articleModel.js` (trạng thái, loại nguồn),
> `src/studio/lib/buildArticle.js` (Studio dựng bài), `scripts/validate-content.mjs`
> (validator), `src/components/article/ArticleRenderer.jsx` (bộ render).

> [!CAUTION]
> Bản cũ của file này dùng tên trường tự đặt (`description`, `publishedDate`,
> `lastUpdated`, `sourceType`, `relatedArticles`, section `text`/`detail`). Không
> trường nào trong số đó tồn tại trong ChottoDay: Studio báo "Thiếu `excerpt`",
> còn các khối đoạn văn render ra rỗng. Chỉ dùng đúng tên trường dưới đây.

---

## 1. KHUNG FILE

```javascript
export const articleTenBien = {
  // Định danh
  id: 'slug-cua-bai',              // duy nhất toàn site, thường trùng slug
  slug: 'slug-cua-bai',            // duy nhất, chỉ [a-z0-9-]

  // Hiển thị
  title: 'Tiêu đề bài',
  excerpt: 'Một đến hai câu: bài nói gì, ảnh hưởng tới ai.',
  category: 'work',                // một trong 9 id ở mục 3
  tags: ['Nhãn 1', 'Nhãn 2'],      // 2-4 nhãn tiếng Việt

  // Thời gian, đúng YYYY-MM-DD
  publishedAt: '2026-09-26',
  updatedAt: '2026-09-26',         // không nhỏ hơn publishedAt
  readingTime: 5,                  // phút, ~200 từ/phút

  // Trạng thái: LUÔN 'review' khi skill tạo
  status: 'review',

  // Ảnh (xem mục 4)
  coverImage: '/images/featured/slug-cua-bai.webp',
  socialImage: '/images/og/og-slug-cua-bai.png',

  author: {
    name: 'Ban Biên Tập Chotto',
    role: 'Nội dung việc làm & tài chính',
  },

  // Ba khối bố cục: thiếu thì khối biến mất khỏi trang
  shortAnswer: {
    lead: 'Một câu mở, kết thúc bằng dấu hai chấm:',
    steps: ['Việc thứ nhất.', 'Việc thứ hai.', 'Việc thứ ba.'],
    note: 'Một câu lưu ý quan trọng nhất.',
  },
  keyTakeaways: ['Ý chính một.', 'Ý chính hai.', 'Ý chính ba.'],
  applicability: {
    country: 'Nhật Bản',
    effectiveFrom: '2026-10-01',
    audience: 'Ai áp dụng được.',
    notes: 'Phạm vi: toàn quốc hay từng tỉnh, ngày hiệu lực khác nhau thế nào.',
  },

  sections: [ /* xem resources/chotto-section-types.md */ ],

  sources: [
    {
      id: 'src-co-quan-01',
      organization: 'Tên cơ quan (tên tiếng Nhật)',
      title: 'Tên trang nguồn, giữ tiếng Nhật trong ngoặc',
      url: 'https://www.example.go.jp/...',   // bắt buộc https://
      accessedAt: '2026-09-26',
      type: 'official',                       // official | primary | reference
    },
  ],

  review: {
    lastVerifiedAt: '2026-09-26',
    reviewAfter: '2027-03-26',                // thường +6 tháng
    reviewer: 'CHƯA DUYỆT',                   // người duyệt tự thay tên mình
  },

  relatedArticleIds: [],                      // chỉ slug CÓ THẬT trên ChottoDay
  relatedToolIds: [],

  seo: {
    metaTitle: 'Tiêu đề SEO | Chotto',        // ≤ 60 ký tự
    metaDescription: 'Mô tả 150-160 ký tự.',
    canonical: 'https://chottoday.com/articles/slug-cua-bai',
    structuredDataType: 'Article',
  },
};

export default articleTenBien;
```

---

## 2. QUY TẮC BẮT BUỘC VỚI BẢN THẢO TÒA SOẠN

1. **`status: 'review'`** và **`review.reviewer: 'CHƯA DUYỆT'`**. Không bao giờ
   `published`, không gán tên người hay tên AI. Validator của ChottoDay từ chối
   `CHƯA DUYỆT` khi bài `published`, nên đó là chốt chặn thật.
2. **Tên biến export:** `article` + CamelCase của slug, có cả `export const` và
   `export default`.
3. **Ngày:** `YYYY-MM-DD`.
4. **Mọi con số, ngày hiệu lực, tên luật và số điều** phải có dòng tương ứng
   trong Fact Pack, kèm trích nguyên văn tiếng Nhật. Nếu chính sách có hiệu lực
   khác nhau theo tỉnh hoặc mới ở mức đề xuất (答申), ghi rõ như vậy; đừng gộp
   thành "từ ngày X trên toàn quốc".

---

## 3. CHUYÊN MỤC

`category` là một trong 9 id: `life`, `doc`, `work`, `health`, `study`, `tool`,
`newcomer`, `job`, `family`. Xem `resources/chotto-categories.md`.

---

## 4. ẢNH

| Trường | Giá trị | Ai tạo |
|---|---|---|
| `coverImage` | `/images/featured/<slug>.webp` | Skill (Bước 9), xuất file `<output_dir>/<slug>.webp` |
| `socialImage` | `/images/og/og-<slug>.png` | Người đăng chạy `card.py` trong repo. Skill **không** vẽ ảnh có chữ |

- Ảnh bìa **luôn là `.webp`**, tên file đúng bằng slug, **không** hậu tố
  `-cover` hay `-pattern`. Chotto Studio lưu ảnh chọn ở ô "Ảnh bìa" thành
  `public/images/featured/<slug>.<đuôi file>`, nên tên và đuôi khớp thì
  `coverImage` khớp.
- `-pattern.jpg` là ảnh hoạ tiết tạm do `npm run images` sinh cho bài chưa có
  ảnh. **Không** trỏ `coverImage` vào đó.
- Không tạo được ảnh đạt chuẩn thì vẫn ghi `coverImage` như trên và báo rõ trong
  Review Package là thiếu ảnh; người đăng sẽ quyết.

---

## 5. VALIDATOR CỦA CHOTTODAY CHẶN GÌ

Xem `docs/huong-dan-tao-bai-viet.md` Phần 7. Tóm tắt: `validate-content.mjs` chỉ
siết đầy đủ khi `status: 'published'` (nguồn đủ trường, `review` đủ ngày,
`reviewer` không phải giá trị giữ chỗ, SEO không rỗng). Bài `review` gần như
không bị kiểm, nên **"validate sạch" không có nghĩa là bài đủ điều kiện đăng**.
