# QUY CHUẨN THIẾT KẾ ĐÁP ỨNG (RIGID RESPONSIVENESS & UI/UX STANDARDS)

## 1. Ranh Giới Khung Nhìn (Viewport Boundaries)
- **Mobile (Ranh giới tối thượng):** Chiều rộng 375px. Tuyệt đối KHÔNG xuất hiện thanh cuộn ngang (`overflow-x: hidden` trên wrapper, `max-width: 100%` trên ảnh và container).
- **Tablet:** 768px – 1024px.
- **Desktop:** 1200px – 1440px.

---

## 2. Chuẩn 5 Trạng Thái Tương Tác (5 Interactive States)
Mọi thành phần nhấp chuột (Button, Card, Input) đều phải có:
1. `default`: Trạng thái hiển thị tự nhiên.
2. `hover`: Chuyển đổi mượt mà với `transition: all 0.2s ease` (đổi độ bóng, tăng nhẹ độ sáng hoặc scale 1.02).
3. `focus`: Đường viền rõ nét hỗ trợ khả năng tiếp cận (`outline: 2px solid var(--primary); outline-offset: 2px`).
4. `loading`: Hiệu ứng spinner hoặc thanh loading pulse.
5. `error`: Viền đỏ `#EF4444` và thông báo ngắn gọn dưới chân input.

---

## 3. Tiêu Chuẩn In Ấn Leaflet / Brochure
- **Khổ A4 tiêu chuẩn:** 210mm x 297mm (hoặc 297mm x 210mm cho tờ rơi ngang).
- **Vùng an toàn (Safety Margin):** Cách mép cắt tối thiểu 5mm.
- **Độ phân giải:** Vector hoặc hình ảnh đạt tối thiểu 300 DPI khi xuất file.
- **Cấu trúc gấp:**
  - Bi-fold (Gấp đôi): Trang bìa trước (Cover) $\rightarrow$ 2 trang ruột đối xứng $\rightarrow$ Trang bìa sau (Liên hệ).
  - Tri-fold (Gấp ba): Trang bìa $\rightarrow$ Trang gấp trong $\rightarrow$ 3 trang ruột liền mạch $\rightarrow$ Trang thông tin liên hệ.
