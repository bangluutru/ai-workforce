# ĐẶC TẢ THIẾT KẾ CHUẨN HÓA (DESIGN SPECIFICATION)

> **Tên dự án:** {{PROJECT_NAME}}  
> **Trang đích:** {{LANDING_PAGE_TITLE}} (ID: `{{LANDING_PAGE_ID}}`)  
> **Nguồn thiết kế:** {{SOURCE_ADAPTER}} (`{{SOURCE_URL_OR_ID}}`)  
> **Thời điểm xuất:** {{TIMESTAMP}}  
> **Phân loại Form:** {{FORM_TYPE}} (ID: `{{FORM_ID}}`)

---

## 1. Hệ thống Nhận diện Thị giác (Visual Identity & Tokens)

### 1.1. Bảng màu (Color Palette)
- **Primary:** `{{COLOR_PRIMARY}}` (Màu thương hiệu chủ đạo, nút CTA)
- **Secondary:** `{{COLOR_SECONDARY}}` (Màu phụ trợ, tag, badge)
- **Background:** `{{COLOR_BACKGROUND}}` (Nền chính)
- **Surface / Card:** `{{COLOR_SURFACE}}` (Nền thẻ sản phẩm, container)
- **Text:** `{{COLOR_TEXT}}` (Màu chữ chính)
- **Muted Text:** `{{COLOR_MUTED}}` (Màu chữ phụ, ghi chú)
- **Accent / Alert:** `{{COLOR_ACCENT}}` (Giá giảm, điểm nhấn, thông báo lỗi)

### 1.2. Kiểu chữ (Typography)
- **Font Family:** `{{FONT_FAMILY}}` (Google Fonts: Inter / Outfit / Plus Jakarta Sans)
- **H1 (Hero Heading):** `{{TYPO_H1}}`
- **H2 (Section Heading):** `{{TYPO_H2}}`
- **Body Text:** `{{TYPO_BODY}}`

### 1.3. Khoảng cách & Bo góc (Spacing & Radius)
- **Container Max-Width:** `1280px`
- **Section Padding Y:** `py-16 md:py-24`
- **Border Radius:** `{{BORDER_RADIUS}}` (mặc định: `rounded-2xl`)
- **Box Shadow:** `shadow-xl shadow-black/5`

---

## 2. Cấu trúc Các Phần (Section Hierarchy)

{{#EACH SECTIONS}}
### Section: {{SECTION_ID}} (Role: `{{SECTION_ROLE}}`)
- **Tiêu đề:** {{SECTION_TITLE}}
- **Bố cục:** {{SECTION_LAYOUT}}
- **Nội dung chính:**
  {{SECTION_CONTENT}}
- **Tương tác:** {{SECTION_INTERACTION}}
{{/EACH}}

---

## 3. Đặc tả Form Thu thập Thông tin & Đơn hàng

- **Form ID:** `{{FORM_ID}}`
- **Form Type:** `{{FORM_TYPE}}`
- **Target Endpoint:** `{{TARGET_ENDPOINT}}`
- **Danh sách Trường dữ liệu:**
{{#EACH FORM_FIELDS}}
  - `{{FIELD_KEY}}` ({{FIELD_LABEL}}): type=`{{FIELD_TYPE}}`, required=`{{IS_REQUIRED}}`
{{/EACH}}

---

## 4. Dự định Hành vi Co dãn (Responsive Intent)
- **Mobile (375px):** 1 cột dọc, thanh điều hướng rút gọn, nút CTA cố định dưới chân màn hình.
- **Tablet (768px):** Lưới 2 cột cho danh sách tính năng và đánh giá.
- **Desktop (1440px):** Đầy đủ các cột đối xứng, hiệu ứng hover mượt mà.
