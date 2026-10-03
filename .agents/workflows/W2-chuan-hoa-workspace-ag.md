---
name: W2-chuan-hoa-workspace-ag
display-name: Chuẩn Hoá Workspace
description: Chuẩn hóa môi trường Antigravity, hợp nhất phân mảnh dự án giữa antigravity/scratch và antigravity-ide/scratch theo kiến trúc Symlink SSOT, dọn dẹp ổ đĩa an toàn.
---
# Workflow: Chuẩn hóa Workspace Antigravity & Symlink SSOT

> [!IMPORTANT]
> **LUẬT ZERO-DESTRUCTION (R1) & CODEBASE-FIRST (R2):**
> Tuyệt đối không xóa bất kỳ thư mục dự án nào khi chưa tạo bản sao lưu an toàn (`scratch_backup_<timestamp>`).
> Mọi thay đổi tuân thủ kiến trúc Single Source of Truth (SSOT).

---

## 🎯 OUTPUT (Kết quả đạt được)
1. **Kiến trúc Symlink SSOT chuẩn hóa:**
   - Thư mục vật lý duy nhất lưu trữ dự án: `~/.gemini/antigravity-ide/scratch/`
   - Đường dẫn symlink: `~/.gemini/antigravity/scratch -> ~/.gemini/antigravity-ide/scratch`
   - Symlink skills: `~/.gemini/antigravity/skills -> ~/.gemini/config/skills` (nếu có)
2. **Không mất mát mã nguồn:** Toàn bộ dự án độc nhất được gộp về IDE Scratch, dự án trùng lặp giữ bản mới nhất, dữ liệu cũ được lưu tại `~/.gemini/antigravity/scratch_backup_<timestamp>`.
3. **Giải phóng dung lượng ổ đĩa:** Dọn sạch cache Chromium (`antigravity-browser-profile`), file tạm `tmp/`, `.DS_Store`, `__pycache__` (tiết kiệm 5 - 20+ GB).

---

## 📥 INPUT
- Thư mục môi trường người dùng trên macOS: `~/.gemini/`
- Công cụ tự động hóa: `scripts/standardize_workspace.py`

---

## ⚙️ PROCESS (Quy trình 3 bước thực thi)

### Bước 1: Khảo sát hiện trạng (Audit & Dry-run)
Agent chạy công cụ khảo sát:
```bash
python3 scripts/standardize_workspace.py
```
- Phân tích trạng thái symlink.
- Liệt kê danh sách dự án trùng lặp, dự án độc nhất.
- Báo cáo dung lượng rác có thể giải phóng.

### Bước 2: Kiểm tra an toàn Git (Safety Preflight)
- Đối với các dự án trùng lặp có thay đổi dở dang (uncommitted/unpushed), Agent cảnh báo hoặc hỗ trợ commit/push lên GitHub trước khi hợp nhất.

### Bước 3: Thực thi Chuẩn hóa & Dọn dẹp
Agent chạy lệnh thực thi:
```bash
python3 scripts/standardize_workspace.py --execute
```
Công cụ tự động:
1. Tạo backup `~/.gemini/antigravity/scratch_backup_<timestamp>`.
2. Đồng bộ các dự án còn thiếu sang `~/.gemini/antigravity-ide/scratch/`.
3. Tạo Symbolic Link `~/.gemini/antigravity/scratch -> ~/.gemini/antigravity-ide/scratch`.
4. Tạo Symbolic Link cho skills nếu cấu hình toàn cục tồn tại.
5. Dọn dẹp rác hệ thống và in bảng nghiệm thu hoàn tất.

---

## ✅ VERIFICATION MATRIX (Nghiệm thu)
- [ ] Lệnh `ls -ld ~/.gemini/antigravity/scratch` hiển thị liên kết mũi tên `-> .../antigravity-ide/scratch`.
- [ ] Tạo thử 1 file test qua `~/.gemini/antigravity/scratch`, kiểm tra xuất hiện tức thì trong `~/.gemini/antigravity-ide/scratch`.
- [ ] Trạng thái các dự án hoạt động bình thường, không mất dữ liệu.
