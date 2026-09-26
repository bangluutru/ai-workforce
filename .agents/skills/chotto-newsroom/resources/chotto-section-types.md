# 12 LOẠI KHỐI NỘI DUNG HỢP LỆ TRONG CHOTTODAY (SECTION TYPES)

> Nguồn đúng duy nhất: `chottoday/docs/huong-dan-tao-bai-viet.md` Phần 4, và bộ render
> `chottoday/src/components/article/ArticleRenderer.jsx`. Nếu repo ChottoDay có trong
> môi trường, ĐỌC hai file đó trước; chỗ nào lệch với file này thì repo đúng.

> [!CAUTION]
> **HAI CÁCH LÀM BÀI RENDER TRỐNG, KHÔNG BÁO LỖI:**
> 1. `type` ngoài 12 loại dưới đây. Bộ render kết thúc bằng `default: return null`.
> 2. **Đúng `type` nhưng sai tên trường.** Bộ render đọc `section.content` cho
>    `intro`, `paragraph`, `note`, `warning`, `quote` và `step.text` cho từng bước.
>    Viết `text:` cho đoạn văn hay `detail:` cho bước là khối hiện ra rỗng.
>    Bản cũ của skill này dạy sai đúng như vậy; đừng lặp lại.

---

## BẢNG TRA CỨU 12 LOẠI SECTION

Ví dụ dưới đây cố ý dùng nội dung giữ chỗ, **không phải số liệu thật**. Đừng chép
con số, điều luật hay tên cơ quan từ đây vào bài: mọi dữ kiện phải lấy từ Fact Pack.
(Bản cũ của file này có ví dụ "phạt 500.000 yên theo Điều 119 Luật Tiêu chuẩn Lao
động" và câu đó đã lọt nguyên vào một bài đăng thật; đúng ra là Điều 40 Luật Lương
tối thiểu.)

### 1. `intro` (đoạn mở bài)
```javascript
{ type: 'intro', content: 'Một đoạn mở: chuyện gì thay đổi, từ khi nào, ảnh hưởng tới ai.' }
```

### 2. `heading` (tiêu đề mục)
```javascript
{ type: 'heading', level: 2, text: '1. Tiêu đề mục' }   // level: 2 hoặc 3; heading dùng `text`
```

### 3. `paragraph` (đoạn văn)
```javascript
{ type: 'paragraph', content: 'Một đoạn văn thường.' }
```

### 4. `list` (danh sách)
```javascript
{ type: 'list', items: ['Ý một', 'Ý hai'] }   // mảng chuỗi
```

### 5. `steps` (các bước thủ tục)
```javascript
{
  type: 'steps',
  items: [
    { stepNumber: 1, title: 'Tên bước', text: 'Làm gì cụ thể.' },
    { stepNumber: 2, title: 'Tên bước', text: 'Làm gì cụ thể.' },
  ],
}
```

### 6. `term` (thuật ngữ tiếng Nhật, lần đầu xuất hiện)
```javascript
{ type: 'term', term: '在留カード', reading: 'Zairyu Card', meaning: 'Thẻ cư trú.' }
```

### 7. `note` (ghi chú)
```javascript
{ type: 'note', title: 'Mẹo', content: 'Nội dung ghi chú.' }
```

### 8. `warning` (cảnh báo: hạn chót, rủi ro, chế tài)
```javascript
{ type: 'warning', title: 'Lưu ý', content: 'Cảnh báo quan trọng. Điều luật nào thì trích đúng tên luật và số điều trong Fact Pack.' }
```

### 9. `example` (ví dụ tính toán)
```javascript
{
  type: 'example',
  title: 'Ví dụ: tên tình huống',
  items: [
    { label: 'Khoản A', value: '300.000 ¥' },
    { label: 'Khoản trừ', value: '−45.000 ¥', isDeduction: true },
    { label: 'Còn lại', value: '255.000 ¥', isTotal: true },
  ],
  caption: 'Số liệu minh hoạ.',
}
```
`example` dùng mảng `items` (label/value), **không** có trường `content`. Tự nhân lại
từng phép tính trước khi ghi.

### 10. `quote` (trích dẫn)
```javascript
{ type: 'quote', content: 'Trích dẫn, dịch sát nguyên văn trong Fact Pack.', author: 'Nguồn' }
```

### 11. `toolCTA` (dẫn sang công cụ)
```javascript
{
  type: 'toolCTA',
  toolId: 'japan-tax-simulator',
  title: 'Tính thử lương thực nhận',
  description: 'Một câu nói công cụ giúp gì.',
}
```
`toolId` phải là id **có thật** trong registry Toolio (`chottoday/src/services/toolRegistry/toolioSnapshot.js`).
Không chắc thì bỏ khối này; `npm run validate:tool-refs` chặn id sai.

### 12. `sources` (danh mục nguồn cuối bài)
```javascript
{
  type: 'sources',
  items: [
    { title: 'Tên trang nguồn', organization: 'Cơ quan', url: 'https://www.example.go.jp/...' },
  ],
}
```
Bộ render in `title (organization)`. **Không có trường `name`**: dùng `name` là
dòng nguồn hiện ra "• ()" không có tên (đã xảy ra trên bài thật).

---

## CÁCH TRÌNH BÀY DỮ LIỆU DẠNG BẢNG

ChottoDay chưa có `type: 'table'`. Khi cần bảng (ví dụ mức lương từng tỉnh):
- Dùng `type: 'list'`, mỗi dòng một mục: `Tỉnh: giá trị (ghi chú)`.
- Hoặc chia theo vùng bằng `heading` rồi `list` bên dưới.
