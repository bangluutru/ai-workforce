# 12 LOẠI KHỐI NỘI DUNG HỢP LỆ TRONG CHOTTODAY (SECTION TYPES)

> [!CAUTION]
> **CẢNH BÁO QUAN TRỌNG VỀ GIAO DIỆN:**
> Hệ thống hiển thị bài viết ChottoDay (`src/components/ArticleRenderer.jsx`) **CHỈ HỖ TRỢ ĐÚNG 12 LOẠI SECTION** được liệt kê dưới đây.
> Bất kỳ loại nào khác (ví dụ: `table`, `image`, `card`, `faq`, `alert`, `accordion`, `html`) **SẼ BỊ BỎ QUA VÀ HIỂN THỊ TRỐNG TRƠN (RENDER BLANK)** trên website.

---

## BẢNG TRA CỨU CẤU TRÚC 12 LOẠI SECTION

### 1. `intro` (Đoạn mở đầu bài viết)
Dùng ở đầu bài để tóm tắt thông tin quan trọng nhất.
```javascript
{
  type: 'intro',
  text: 'Từ ngày 01/10/2026, mức lương tối thiểu tại Tokyo chính thức tăng lên 1.163 yên/giờ, tăng 50 yên so với năm trước. Đây là mức tăng cao kỷ lục áp dụng cho toàn bộ người lao động.'
}
```

### 2. `heading` (Tiêu đề mục con H2)
Không đặt dấu hai chấm (`:`) ở cuối tiêu đề.
```javascript
{
  type: 'heading',
  text: 'Chi tiết mức lương tối thiểu tại 3 đô thị lớn'
}
```

### 3. `paragraph` (Đoạn văn thân bài)
Câu văn ngắn gọn, mạch lạc.
```javascript
{
  type: 'paragraph',
  text: 'Mức lương tối thiểu áp dụng cho mọi hình thức lao động, bao gồm nhân viên chính thức (seishain), nhân viên hợp đồng, làm thêm (arubaito) và thực tập sinh kỹ năng.'
}
```

### 4. `list` (Danh sách điểm hoặc gạch đầu dòng)
```javascript
{
  type: 'list',
  ordered: false, // true nếu là danh sách có thứ tự 1, 2, 3
  items: [
    'Tokyo: 1.163 yên/giờ (tăng 50 yên)',
    'Kanagawa: 1.162 yên/giờ (tăng 50 yên)',
    'Osaka: 1.114 yên/giờ (tăng 50 yên)'
  ]
}
```

### 5. `steps` (Quy trình các bước thực hiện có thứ tự)
```javascript
{
  type: 'steps',
  items: [
    {
      title: 'Bước 1: Kiểm tra phiếu lương hàng tháng',
      detail: 'Lấy tổng lương cơ bản chia cho tổng số giờ làm việc thực tế trong tháng để ra mức lương theo giờ.'
    },
    {
      title: 'Bước 2: So sánh với mức lương tối thiểu của tỉnh',
      detail: 'Đối chiếu con số vừa tính với bảng lương tối thiểu của tỉnh nơi công ty đặt trụ sở làm việc.'
    },
    {
      title: 'Bước 3: Trao đổi với nghiệp đoàn hoặc liên hệ Cục Lao động',
      detail: 'Nếu mức lương thực nhận thấp hơn quy định, báo ngay cho nghiệp đoàn quản lý hoặc Thanh tra Tiêu chuẩn Lao động.'
    }
  ]
}
```

### 6. `term` (Hộp giải thích thuật ngữ tiếng Nhật)
```javascript
{
  type: 'term',
  term: '最低賃金 (Saitei Chingin)',
  reading: 'さいていちんぎん',
  meaning: 'Mức lương tối thiểu theo giờ theo luật định mà người sử dụng lao động bắt buộc phải trả cho người lao động.'
}
```

### 7. `note` (Hộp ghi chú thông tin bổ sung)
```javascript
{
  type: 'note',
  text: 'Các khoản phụ cấp như tiền làm thêm giờ (zangyo), tiền chuyên cần và tiền hỗ trợ đi lại (tsukin teate) không được tính vào mức lương tối thiểu.'
}
```

### 8. `warning` (Hộp cảnh báo rủi ro hoặc hạn chót)
```javascript
{
  type: 'warning',
  text: 'Doanh nghiệp trả lương thấp hơn mức tối thiểu vùng sẽ bị phạt tới 500.000 yên theo Điều 119 Luật Tiêu chuẩn Lao động Nhật Bản.'
}
```

### 9. `example` (Ví dụ tình huống minh họa cụ thể)
```javascript
{
  type: 'example',
  title: 'Ví dụ tính lương làm thêm tại Tokyo',
  content: 'Bạn làm thêm 20 giờ mỗi tuần tại một cửa hàng tiện lợi ở Tokyo. Với mức lương mới 1.163 yên/giờ, thu nhập tối thiểu một tháng (4 tuần) của bạn là: 20 giờ x 4 tuần x 1.163 yên = 93.040 yên.'
}
```

### 10. `quote` (Trích dẫn phát biểu hoặc tuyên bố chính thức)
```javascript
{
  type: 'quote',
  text: 'Việc điều chỉnh mức lương tối thiểu nhằm đảm bảo mức sống cơ bản cho người lao động trong bối cảnh giá cả hàng hóa sinh hoạt tiếp tục tăng cao.',
  author: 'Hội đồng Tiền lương Trung ương, Bộ Y tế Lao động và Phúc lợi Nhật Bản'
}
```

### 11. `toolCTA` (Kêu gọi sử dụng công cụ tính toán tương tác)
```javascript
{
  type: 'toolCTA',
  toolId: 'net-salary-calculator',
  title: 'Tính thử lương thực nhận (Take-home Pay) của bạn',
  description: 'Nhập mức lương mới để xem số tiền thực tế nhận về tài khoản sau khi trừ bảo hiểm và thuế.'
}
```

### 12. `sources` (Khối trích dẫn danh mục nguồn tham khảo cuối bài)
```javascript
{
  type: 'sources',
  items: [
    {
      name: 'Thông cáo báo chí Bộ Y tế Lao động và Phúc lợi Nhật Bản (MHLW)',
      url: 'https://www.mhlw.go.jp/stf/newpage_saiteichingin2026.html'
    },
    {
      name: 'Bảng tra cứu mức lương tối thiểu từng địa phương (Cơ quan Lao động)',
      url: 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/roudoukijun/minimumichiran/'
    }
  ]
}
```

---

## 3. CÁCH XỬ LÝ DỮ LIỆU BẢNG BIỂU (TABLE WORKAROUND)

Do ChottoDay chưa có `type: 'table'`, khi cần trình bày dữ liệu dạng bảng (ví dụ: bảng lương 47 tỉnh thành):
- Dùng `type: 'list'` với định dạng rõ ràng từng dòng: `Tỉnh: [Giá trị] (Ghi chú)`.
- Hoặc kết hợp `type: 'heading'` chia theo từng khu vực (Kanto, Kansai, Chubu, Kyushu) và bên dưới dùng `type: 'list'`.
