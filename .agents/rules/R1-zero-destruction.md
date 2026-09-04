---
trigger: always_on
description: "Luật Zero-Destruction - Bảo toàn dữ liệu qua lịch sử Git, nghiêm cấm xả rác vào workspace."
---

# LUẬT ZERO-DESTRUCTION (BẢO TOÀN DỮ LIỆU QUA GIT-NATIVE)

Đây là quy tắc cao nhất liên quan đến tệp tin hệ thống. Mọi tác nhân AI khi thao tác với file trong AI Workforce phải tuân thủ nghiêm ngặt các quy định sau:

## 1. BẢO TOÀN LỊCH SỬ BẰNG GIT (GIT-NATIVE PRESERVATION)
1. **Git là cỗ máy bảo toàn lịch sử duy nhất:** Toàn bộ mã nguồn, cấu hình và kho tri thức SSOT (`.agents/knowledge/`) được kiểm soát phiên bản qua Git.
2. Mọi tệp tin khi sửa đổi hoặc xóa bỏ đều có thể phục hồi tức thì thông qua:
   ```bash
   git checkout <commit_hash> -- <đường_dẫn_file>
   # hoặc:
   git restore <đường_dẫn_file>
   ```
3. Tuyệt đối KHÔNG tự ý xóa file mã nguồn, file cấu hình hoặc kho tri thức của hệ thống nếu chưa có sự phê duyệt từ người dùng.

## 2. NGHIÊM CẤM TẠO THÙNG RÁC CỤC BỘ (_DELETE / _ARCHIVE)
1. **Triệt tiêu thư mục rác:** KHÔNG tạo hoặc duy trì các thư mục rác cục bộ như `_Delete/` hoặc `_Archive/` trong repository.
2. Việc lưu file rác trong workspace làm phình to dung lượng git repository, vi phạm Luật R0 (Git-Sync Mandatory) và gây phân mảnh dữ liệu giữa các máy khi `git push/pull`.
3. Khi người dùng yêu cầu xóa một file trong dự án đã được Git theo dõi, tác nhân sử dụng `git rm` hoặc xóa file để Git ghi nhận thay đổi sạch sẽ.

## 3. CẬP NHẬT TRI THỨC IN-PLACE & QUẢN TRỊ DIFF
1. Khi một file chính sách, bảng giá hoặc tri thức trong `.agents/knowledge/` có bản mới, cập nhật trực tiếp vào file đó (in-place) để Git hiển thị rõ ràng từng dòng thay đổi (diff).
2. Lịch sử các phiên bản cũ được lưu giữ vĩnh viễn trong lịch sử Git commit, người dùng có thể tra cứu lại bất kỳ lúc nào qua `git log -p`.

## 4. BẢO VỆ GỐC REPOSITORY (ANTI-REPO BLOAT)
1. Mọi thành phẩm xuất bản (DOCX, XLSX, PPTX, PDF, Markdown) PHẢI được lưu vào `<output_dir>` do người dùng chỉ định hoặc mặc định `~/Downloads/`.
2. Tuyệt đối KHÔNG tạo thư mục kết quả hoặc file xuất bản trực tiếp trong thư mục gốc của repository.
