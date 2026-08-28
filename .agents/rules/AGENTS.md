---
trigger: always_on
description: "Bản đồ tổ chức tổng. Bắt buộc nạp đầu tiên để định vị môi trường làm việc."
---

# BẢN ĐỒ TỔ CHỨC AI WORKFORCE

> Sơ đồ phòng ban và luật lệ tối cao cho hệ thống tác nhân số. Bất kỳ tác nhân nào được khởi tạo cũng phải đọc file này đầu tiên để định vị không gian làm việc.

## 1. KHUNG KIẾN TRÚC KWSR TỔNG THỂ
Workspace này được quy hoạch theo nguyên tắc "Company in a Folder" của KWSR:
- **[K] Knowledge**: `.agents/knowledge/` - Nơi chứa Nguồn Sự Thật Duy Nhất (SSOT).
- **[W] Workflow**: `.agents/workflows/` - Nơi chứa sổ tay vận hành và luồng quy trình (Reverse I-P-O).
- **[S] Skill**: `.agents/skills/` - Kho kỹ năng, mô tả công việc (JD) của nhân sự số 5 lớp.
- **[R] Rule**: `.agents/rules/` - Sàn phòng vệ và phân quyền.
- **Vùng Cách Ly (Isolation)**: `_Delete/` (Rác) và `_Archive/` (Kho lưu).

## 2. NGUYÊN TẮC ZERO-HALLUCINATION
Tuyệt đối KHÔNG BỊA DỮ LIỆU. Bất kỳ tuyên bố nào về chính sách, bảng giá, quy trình công ty đều phải dựa trên các file `artifacts/*.md` nằm trong thư mục `.agents/knowledge/`. Nếu không tìm thấy, AI bắt buộc phải trả lời: "Tôi không có đủ dữ liệu trong kho tri thức" và xin chỉ thị từ con người.

## 3. GIAO THỨC BÀN GIAO KHÔNG GHI ĐÈ
- Mỗi tác nhân (skill) chỉ được phép tạo file mới hoặc đọc file của tác nhân khác.
- CẤM ghi đè trực tiếp lên file đang là thành phẩm của người khác. Mọi sửa đổi phải lưu thành file bản nháp mới hoặc append vào cuối tệp.
