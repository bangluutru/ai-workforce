# Nhật Ký Thay Đổi (CHANGELOG) — AI Workforce

Tất cả các thay đổi đáng chú ý của dự án AI Workforce sẽ được ghi lại trong tệp này.

---

## [2.7.0] - 2026-08-29

### 🚀 Tính Năng Mới (Added)
- **Tích hợp Skill Bóc Tách PDF Scan (`boc-tach-pdf` v3):**
  - Số hóa toàn diện file PDF scan dài thành Word DOCX trung thực với chuẩn định dạng Nghị định 30/2020/NĐ-CP hoặc Văn bản dài.
  - Hỗ trợ render ảnh HD tự động phát hiện DPI gốc (cap 600), tiền xử lý 2 tầng (Pillow autocontrast + OpenCV deskew/denoise), AI Vision OCR song song checkpointing, trích xuất ảnh minh họa gốc và xuất bảng biểu sang Excel (`.xlsx`).
  - Tích hợp pipeline chuyển đổi 5 lớp chuyên sâu (Pandoc → Layout → Structure → Block → Typography).
- **Icon chuyên nghiệp cho `boc-tach-pdf`:** Thiết kế biểu tượng vector SVG máy quét OCR hiện đại kèm gradient tím (`gradient-purple`) và nhãn hiển thị `Bóc tách\nPDF`.
- **Tự động kích hoạt File Picker cho PDF Scan:** Khi click vào thẻ `Bóc tách PDF` trên sidebar của Extension, hộp thoại chọn tệp PDF sẽ tự động mở lên.

---

## [2.4.0] - 2026-08-29

### 🚀 Tính Năng Mới & Nâng Cấp (Added & Improved)
- **Tự động mở File Picker khi chọn Skill:** Khi click vào bất kỳ Skill nào có cấu hình `needs_file: true` (như *Dịch PDF*, *Bóc tách CV*, *Chấm điểm CV*, *Xử lý văn phòng*, *Phân tích nhân sự*, *Quản lý hợp đồng*), hộp thoại chọn tệp của hệ điều hành sẽ tự động mở lên với bộ lọc định dạng tương ứng (`.pdf`, `.docx`, ...).
- **Huy hiệu trực quan:** Thêm huy hiệu `📎 Chọn tệp` trên các thẻ skill cần tệp đính kèm trong giao diện Sidebar.
- **Nút Làm Mới (🔄):** Bổ sung thanh công cụ Top bar trên panel extension cho phép làm mới nhanh danh sách kỹ năng và quy trình.
- **Tích hợp Native Antigravity IDE Chat:** Ưu tiên sử dụng lệnh native `antigravity.sendPromptToAgentPanel` và `antigravity.openChatView` để điền và gửi trực tiếp prompt kèm đường dẫn tệp vào Agent Chat.

### 🐛 Sửa Lỗi (Fixed)
- **Khắc phục lỗi cài đặt extension:** Cập nhật `scripts/auto-setup.sh` tự động đóng gói `.vsix` mới nhất và cài đè (`--force`) vào Antigravity IDE, tránh tình trạng IDE bị kẹt ở phiên bản cũ.
- **Khắc phục lỗi Regex Parser với CRLF:** Sửa regex parse Frontmatter trong cả `extension.js` và `dashboard/build_dashboard.js` để nhận diện chính xác các tệp định dạng Windows `\r\n` (như `xu-ly-van-phong/SKILL.md`), đảm bảo nhận đủ 8/8 kỹ năng.
- **Dọn dẹp phiên bản cũ:** Tự động loại bỏ các thư mục cài đặt cũ trong `~/.antigravity-ide/extensions/`.

### 📚 Tri Thức Hệ Thống (Knowledge)
- Bổ sung tài liệu kỹ thuật chi tiết tại: `.agents/knowledge/ai_workforce_extension_architecture/artifacts/architecture_and_file_picker_guide.md`.
