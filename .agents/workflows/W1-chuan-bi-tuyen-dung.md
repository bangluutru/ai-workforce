---
name: W1-chuan-bi-tuyen-dung
description: Chuẩn bị tuyển dụng mới từ yêu cầu Trưởng phòng để tạo folder dự án chuẩn và viết JD (Mô tả công việc).
---
# Workflow: Chuẩn bị Tuyển dụng (Reverse I-P-O)

## OUTPUT (Khóa trước)
- Tệp `INDEX.md` chứa metadata đợt tuyển: mã TD, vị trí, phòng ban, level.
- Tệp `JD_[Mã TD].md` hoàn chỉnh.

## INPUT (Truy ngược)
- **Từ user:** Vị trí cần tuyển, phòng ban, số lượng, lý do tuyển.
- **Từ SSOT (Knowledge):** Tham chiếu `.agents/knowledge/quan_tri_nhan_su_he_thong_luong_3p/artifacts/bang-luong-level.md` để lấy mức lương tương ứng.

## PROCESS (3 bước thực thi)
- **Bước 1: Thu thập thông số**
  - `action`: Hỏi user 4 thông số cơ bản.
  - `handoff`: Bộ thông số đầy đủ.
  - `location`: Giữ trong memory.
- **Bước 2: Tạo folder dự án**
  - `action`: Tạo thư mục theo cấu trúc và viết `INDEX.md` với mã TD sinh tự động.
  - `handoff`: Cây thư mục + `INDEX.md`.
  - `location`: `Tuyen_Dung_{Mã TD}/INDEX.md`.
- **Bước 3: Viết JD**
  - `action`: Gọi Skill viết JD truyền thông số và tra bảng lương để sinh JD.
  - `handoff`: File JD hoàn chỉnh có chứa phần lương.
  - `location`: `Tuyen_Dung_{Mã TD}/JD_[Mã TD].md`.
