# EJV Translator JSON Schema Specification

Mỗi tài liệu dịch theo chuẩn EJV Translator được cấu trúc dưới dạng một mảng JSON các block phần tử:

```json
[
  {
    "type": "h1 | h2 | h3 | p | ul | ol | table | blockquote | hr | caption",
    "vn": "...",
    "en": "...",
    "ja": "..."
  }
]
```

## Chi tiết các loại Block

### 1. Headings (`h1`, `h2`, `h3`)
- `h1`: Tiêu đề chính, tên chương, tên văn bản (IN HOA, căn giữa khi xuất DOCX).
- `h2`: Tiêu đề mục lớn (Mục 1, Phần I, Chương II).
- `h3`: Tiêu đề tiểu mục (1.1, a, b).

```json
{
  "type": "h1",
  "vn": "TÓM TẮT NGHỊ ĐỊNH SỐ 37/2026/NĐ-CP",
  "en": "SUMMARY OF DECREE NO. 37/2026/ND-CP",
  "ja": "政令第37/2026/NĐ-CP号の概要"
}
```

### 2. Paragraph (`p`)
Đoạn văn thông thường.

```json
{
  "type": "p",
  "vn": "Nghị định này quy định chi tiết về quản lý thiết bị y tế và thuốc thử IVD.",
  "en": "This Decree provides detailed regulations on the management of medical devices and IVD reagents.",
  "ja": "本政令は、医療機器および体外診断用医薬品（IVD試薬）の管理に関する詳細を定めています。"
}
```

### 3. Lists (`ul`, `ol`)
- `ul`: Danh sách không thứ tự (Bullet points) — các trường `vn`, `en`, `ja` là mảng chuỗi.
- `ol`: Danh sách có thứ tự (Numbered steps) — các trường `vn`, `en`, `ja` là mảng chuỗi.

```json
{
  "type": "ul",
  "vn": ["Điều kiện nhập khẩu", "Hồ sơ đăng ký lưu hành", "Quy trình kiểm nghiệm"],
  "en": ["Import conditions", "Marketing authorization dossier", "Testing procedure"],
  "ja": ["輸入条件", "流通登録申請書類", "試験・検査手順"]
}
```

### 4. Table (`table`)
Bảng dữ liệu gồm `headers` và `rows`:

```json
{
  "type": "table",
  "headers": {
    "vn": ["Điều/khoản", "Tiêu đề", "Nội dung áp dụng"],
    "en": ["Article/Clause", "Title", "Applicable Content"],
    "ja": ["条・項", "規定タイトル", "適用内容"]
  },
  "rows": {
    "vn": [
      ["Điều 2, khoản 1", "Đối tượng áp dụng", "Tổ chức, cá nhân sản xuất kinh doanh IVD"]
    ],
    "en": [
      ["Article 2, Clause 1", "Scope of Application", "Organizations and individuals manufacturing/trading IVD"]
    ],
    "ja": [
      ["第2条第1項", "適用対象", "IVD試薬を製造・販売する組織および個人"]
    ]
  }
}
```

### 5. Blockquote (`blockquote`) & Caption (`caption`)
- `blockquote`: Trích dẫn, lưu ý, hộp cảnh báo.
- `caption`: Chú thích bảng hoặc hình ảnh.
- `hr`: Đường phân cách ngang trang (không cần thuộc tính ngôn ngữ).
