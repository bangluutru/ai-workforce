# Design Taste Protocol — Quy tắc Thiết kế UI/UX

> **Khi nào đọc file này**: Chỉ khi task liên quan đến giao diện, UI, UX, layout, styling.
> Không cần đọc cho backend-only hoặc logic-only tasks.

---

## 1. VISUAL HIERARCHY (Thứ tự ưu tiên thị giác)

**TRƯỚC KHI code UI**, liệt kê các phần tử theo thứ tự quan trọng giảm dần:

```
#1 (Quan trọng nhất — đập vào mắt đầu tiên): [element]
#2: [element]
#3: [element]
...
```

**Squint Test**: Thu nhỏ/làm mờ giao diện — mục #1 có nổi bật vượt trội không?

---

## 2. DESIGN TOKENS (Chốt trước khi code)

```
Accent Color:     [1 màu chính]
Neutral Scale:    [hệ màu trung tính]
Font Primary:     [1 font chính]
Font Secondary:   [1 font phụ, nếu cần]
Spacing Scale:    [4px, 8px, 12px, 16px, 24px, 32px, 48px]
Border Radius:    [scale nhất quán]
```

**Quy tắc**: Tối đa 2 font families. Tối đa 1 accent color + 1 secondary.

---

## 3. SLOP CATALOG (Danh sách CẤM)

Các pattern "trung bình cộng" tạo giao diện rẻ tiền — NGHIÊM CẤM:

| ❌ Cấm | ✅ Thay bằng |
|--------|-------------|
| Gradient tím-xanh sặc sỡ vô nghĩa | Gradient tinh tế 2 sắc gần nhau hoặc solid color |
| Glassmorphism bẩn (blur + opacity quá mức) | Glass effect nhẹ với backdrop-filter có kiểm soát |
| Shadow đè shadow (3+ layers) | 1 shadow chính xác với đúng elevation |
| Emoji làm icon trong sản phẩm chuyên nghiệp | Icon library nhất quán (Lucide, Phosphor, Heroicons) |
| Text xám (#999) trên nền trắng (#fff) | Contrast ratio ≥ 4.5:1 (WCAG AA) |
| Border 1px solid mọi nơi | Border có chủ đích, chỉ ở ranh giới semantic |

---

## 4. STATE COMPLETENESS (Đầy đủ trạng thái)

Mọi interactive element PHẢI có đủ:

```
[ ] Default state
[ ] Hover state
[ ] Focus state (keyboard navigation)
[ ] Active/Pressed state
[ ] Disabled state
[ ] Loading state (nếu async)
[ ] Error state
[ ] Empty state (không có dữ liệu)
```

---

## 5. RESPONSIVE & OVERFLOW

- **Breakpoints bắt buộc**: Mobile (375px), Tablet (768px), Desktop (1280px+)
- **Text overflow**: Ép buộc `text-overflow: ellipsis` hoặc `word-break` cho dữ liệu dài
- **Touch target**: Tối thiểu 44×44px trên mobile
- **Numeric columns**: Right-aligned trong bảng
- **Stress test**: Thử với chuỗi tên 100+ ký tự, danh sách rỗng, ảnh bị thiếu

---

## 6. SUBTRACTION PASS (Bước cuối trước khi giao)

Rà soát 1 lượt cuối — xóa bỏ mọi trang trí KHÔNG mang giá trị thông tin:

```
Hỏi cho từng element:
"Nếu bỏ [border/shadow/animation/gradient] này đi, 
 user có mất thông tin gì không?"

Nếu KHÔNG → XÓA.
```
