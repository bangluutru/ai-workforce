---
name: thiet-ke
description: Thiết kế giao diện Landing Page, Leaflet/Brochure (tờ rơi in ấn gấp 2/gấp 3), Poster và Mockup đồ họa chuyên nghiệp. Hỗ trợ 2 phương thức sáng tạo: (1) Thiết kế dựa trên dữ liệu/nội dung có sẵn của người dùng, hoặc (2) Sáng tạo trọn gói từ số 0 (Zero-to-One). Tích hợp triết lý Design Director (lấy cảm hứng từ ui-ux-pro-max), quy chuẩn phối màu WCAG AA, typography chuẩn mực, tính phản hồi tuyệt đối (Rigid Responsiveness không tràn ngang 375px mobile) và đủ 5 trạng thái tương tác (hover, focus, loading, empty, error). Kích hoạt khi user yêu cầu 'thiết kế', 'làm landing page', 'thiết kế leaflet', 'làm tờ rơi', 'tạo brochure', 'thiết kế poster', 'làm giao diện web', 'thiết kế ui ux'. KHÔNG dùng cho soạn thảo văn bản hành chính nhà nước chuẩn NĐ 30 đen trắng (dùng xu-ly-van-phong) hay dịch thuật (dùng ejv-translate).
trigger: Thiết kế, thiết kế landing page, làm leaflet, tạo tờ rơi, thiết kế brochure, thiết kế UI/UX
argument-hint: [loại_thiết_kế: landing_page|leaflet|poster] [chủ_đề_hoặc_file_nguồn]
allowed-tools: [run_command, view_file, write_to_file, replace_file_content, generate_image]
effort: high
context: fork
needs_file: false
---

# Thiết Kế 2.0 — Landing Page, Leaflet & UI/UX Studio
## Tiêu Chuẩn Giám Đốc Thiết Kế (Design Director) & Sáng Tạo Đồ Họa Cao Cấp (Gemini 3.8 Multi-Agent)

Kỹ năng đảm nhiệm toàn diện việc tạo dựng giao diện số (Landing Page / Web App) và ấn phẩm in ấn tiếp thị (Leaflet / Brochure / Tờ rơi), kết hợp bảng phối màu đạt chuẩn tương phản WCAG AA, typography hiện đại và triết lý micro-animations mượt mà.

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Skill này chạy hoàn toàn bằng khả năng tích hợp sẵn của Antigravity IDE (Gemini 3.8) và công cụ đồ họa nội bộ (`generate_image`).
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài hoặc yêu cầu API key.
> - Toàn bộ tư duy thẩm mỹ, phối màu, cấu trúc DOM/CSS và layout in ấn là của chính Agent.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) từ bản phác thảo đến thành phẩm cuối cùng.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định đường dẫn lưu file đầu ra trước khi xuất bản:

| Placeholder | Quy ước xác định đường dẫn |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** (ví dụ: đường dẫn do user cung cấp) hoặc **Mặc định: `~/Downloads/`** |
| `<process_dir>` | Thư mục tạm xử lý, ưu tiên đặt tại `_process/thiet_ke_[du_an]/` (đã gitignore) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Cho phép người dùng chọn/chỉ định thư mục sẽ lưu file thiết kế (`.html`, `.svg`, `.pdf`, `.png`).
> - Mọi file xuất bản thành phẩm PHẢI được lưu vào `<output_dir>` (mặc định: `~/Downloads/` hoặc nơi user chỉ định).
> - TUYỆT ĐỐI KHÔNG lưu file thiết kế thành phẩm trực tiếp vào thư mục gốc của codebase nếu người dùng không yêu cầu, để tránh làm tăng dung lượng kho lưu trữ Git.

---

## 🎯 Khi Nào Kích Hoạt Kỹ Năng Này?

Kỹ năng phục vụ 2 nhánh thiết kế chuyên biệt:
1. **Track 1 — Landing Page & Web Interface:**
   - Tạo trang đích chuyển đổi cao, website giới thiệu sản phẩm/dịch vụ, portfolio hoặc form đăng ký.
   - Sử dụng **HTML5 + Vanilla CSS hiện đại** (Glassmorphism, mảng màu hài hòa, micro-interactions, responsive 100% từ 375px đến 1440px).
   - Đảm bảo đủ **5 trạng thái tương tác** của mọi nút bấm và thẻ: `hover`, `focus`, `loading`, `empty`, `error`.
2. **Track 2 — Leaflet / Brochure / Tờ Rơi In Ấn:**
   - Thiết kế tờ rơi khổ A4/A5 gấp đôi (Bi-fold: 4 mặt) hoặc gấp ba (Tri-fold: 6 mặt).
   - Sử dụng file HTML Print Layout hoặc SVG vector sắc nét (300 DPI ready), có thể xuất sang PDF in ấn.
   - Tự động phối hợp công cụ `generate_image` để tạo ảnh minh họa/banner sản phẩm độc quyền nếu người dùng không có sẵn ảnh.

---

## 🏗️ Hai Phương Thức Sáng Tạo Đầu Vào (Intake Mode)

```
[LỰA CHỌN ĐẦU VÀO CỦA NGƯỜI DÙNG]
       │
       ├──► (A) ĐÃ CÓ NỘI DUNG/FILE MẪU
       │    └─► Bóc tách thông số, bảng biểu, ảnh → Tái tạo cấu trúc thị giác phân cấp (Visual Hierarchy).
       │
       └──► (B) SÁNG TẠO TỪ SỐ 0 (ZERO-TO-ONE)
            └─► Tra cứu tokens màu sắc (resources/design_tokens.json) → Brainstorm layout → Thiết kế hoàn chỉnh.
```

---

## 📋 Hướng Dẫn Thực Hiện Chi Tiết

### 📌 Bước 1: Tiếp Nhận Phân Tích & Xác Định Token Thiết Kế (Intake)
* Đọc `resources/design_tokens.json` để chọn bộ màu và phông chữ phù hợp với ngành nghề (SaaS, Y tế, Giáo dục, F&B, Bất động sản, Thời trang...).
* Xác định loại sản phẩm: `landing_page` hoặc `leaflet`.

### 📌 Bước 2: Tạo Dựng Giao Diện Hoặc Bản In
* Đối với **Landing Page**:
  - Dựa trên mẫu `templates/landing_page_starter.html`.
  - Viết Vanilla CSS tinh xảo với CSS Variables, hiệu ứng chuyển động mượt mà (smooth transitions), không có thanh cuộn ngang trên màn hình 375px.
* Đối với **Leaflet / Brochure**:
  - Dựa trên mẫu `templates/leaflet_bifold_a4.html` hoặc `templates/leaflet_trifold_a4.html`.
  - Phân chia các trang gấp (Flap/Panel) rõ ràng theo trình tự đọc tự nhiên của khách hàng.
  - Nếu cần ảnh sản phẩm hoặc minh họa: gọi `generate_image` để tạo ảnh và nhúng trực tiếp.

### 📌 Bước 3: Xuất Bản Thành Phẩm
* Đối với Landing Page: Xuất file `<output_dir>/index.html` và file style đính kèm.
* Đối với Leaflet in ấn: Chạy script chuyển đổi sang PDF:
  ```bash
  python .agents/skills/thiet-ke/scripts/export_leaflet_pdf.py --input "<process_dir>/leaflet.html" --output "<output_dir>/leaflet_print_ready.pdf"
  ```

---

## 5. Quality Gate & Giao Thức Bàn Giao Sạch

### Checklist Kiểm Tra Chất Lượng (Quality Gate):
1. ✅ **Rigid Responsiveness:** Giao diện web không có thanh cuộn ngang (horizontal overflow) trên khung nhìn di động 375px.
2. ✅ **Interactive Component States:** Mọi nút bấm hoặc thẻ tương tác đều có đầy đủ style cho `hover`, `focus`, `active`.
3. ✅ **Tương Phản Màu Sắc (WCAG AA):** Tỷ lệ tương phản chữ trên nền đạt tối thiểu 4.5:1.
4. ✅ **Confidence Flagging:** Đối với các thông số kích thước in ấn hoặc bố cục chưa có quy chuẩn chính xác từ nhà in (độ tin cậy < 85%), ghi rõ `[CẦN XÁC MINH: Khổ in xén lề 3mm]`.
5. ✅ **Khử Dấu Vết AI Tiếng Việt (Anti-AI Footprint):**
   - 0 em dash `—` (thay bằng ` - `).
   - 0 Oxford comma `, và`.
   - 0 dấu hai chấm cuối tiêu đề.
6. ✅ Toàn bộ file thành phẩm (`.html`, `.pdf`, `.svg`, `.png`) được lưu vào `<output_dir>` (mặc định: `~/Downloads/`).
7. ✅ **Evidence Verifier & Zero-Loss:** Đối chiếu nội dung đầu vào, đảm bảo không bỏ sót thông tin liên hệ, bảng giá hoặc tính năng quan trọng.
8. ✅ **Giao thức Bàn giao Sạch:** Khung chat chỉ tóm tắt thông số thiết kế (bảng màu, font chữ, các section chính) và đường dẫn file kết quả có thể mở xem ngay.

