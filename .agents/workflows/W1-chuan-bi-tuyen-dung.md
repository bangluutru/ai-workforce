---
name: W1-chuan-bi-tuyen-dung
display-name: Chuẩn Bị Tuyển Dụng
description: Chuẩn bị tuyển dụng mới từ yêu cầu Trưởng phòng để tạo folder dự án chuẩn và viết JD (Mô tả công việc) xuất ra ~/Downloads/AIWF_Output/.
---
# Workflow: Chuẩn bị Tuyển dụng (Reverse I-P-O)

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> Toàn bộ thư mục và tài liệu tuyển dụng PHẢI được tạo tại `<output_dir>` do người dùng chỉ định hoặc **Mặc định: `~/Downloads/AIWF_Output/Tuyen_Dung_{Mã TD}/`**.
> TUYỆT ĐỐI KHÔNG tạo thư mục đợt tuyển dụng trực tiếp trong thư mục gốc của repository.

## OUTPUT (Khóa trước)
- Tệp `INDEX.md` chứa metadata đợt tuyển: mã TD, vị trí, phòng ban, level.
- Tệp `JD_[Mã TD].md` và `JD_[Mã TD].docx` hoàn chỉnh chuẩn văn phòng.

## INPUT (Truy ngược)
- **Từ user:** Vị trí cần tuyển, phòng ban, số lượng, lý do tuyển, thư mục lưu kết quả (mặc định: `~/Downloads/AIWF_Output/`).
- **Từ SSOT (Knowledge):** Tham chiếu `.agents/knowledge/quan_tri_nhan_su_he_thong_luong_3p/artifacts/bang-luong-level.md` để lấy mức lương tương ứng.

## PROCESS (3 bước thực thi)
- **Bước 1: Thu thập thông số**
  - `action`: Hỏi user 4 thông số cơ bản (vị trí, phòng ban, số lượng, cấp bậc).
  - `handoff`: Bộ thông số đầy đủ.
  - `location`: Giữ trong memory.
- **Bước 2: Tạo folder dự án tại <output_dir>**
  - `action`: Tạo thư mục tại `<output_dir>/Tuyen_Dung_{Mã TD}/` và viết `INDEX.md` với mã TD sinh tự động.
  - `handoff`: Cây thư mục + `INDEX.md`.
  - `location`: `<output_dir>/Tuyen_Dung_{Mã TD}/INDEX.md`.
- **Bước 3: Soạn thảo JD**
  - `action`: Áp dụng kỹ năng `xu-ly-van-phong` (hoặc `viet-bai`), truyền thông số và tra bảng lương 3P để sinh JD hoàn chỉnh.
  - `handoff`: File JD hoàn chỉnh (Markdown và Word .docx).
  - `location`: `<output_dir>/Tuyen_Dung_{Mã TD}/JD_[Mã TD].md`.
