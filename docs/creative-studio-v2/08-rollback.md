# AIWF CREATIVE STUDIO 2.0 — QUY TRÌNH PHỤC HỒI & HOÀN NGUYÊN (ROLLBACK PROCEDURE)

> **Mã tài liệu:** `docs/creative-studio-v2/08-rollback.md`  
> **Phiên bản:** 2.0 (Hậu Hợp Nhất Main — Post-Merge Hardening)  
> **Nguyên tắc cốt lõi:** BẢO TOÀN DỮ LIỆU (Rule R1 Zero-Destruction). CẤM các lệnh hủy diệt: `git reset --hard`, `git clean -fd`, `git push --force`.  
> **Điểm mốc đối chiếu gốc:** Thẻ `backup/creative-studio-v2-pre-upgrade` (Commit `7c989ea62df9816f73ab866fbcc38b9597e52eb8`).

---

## 1. NGUYÊN TẮC BẢO VỆ DỮ LIỆU HẬU HỢP NHẤT (POST-MERGE CONTEXT)

Do Creative Studio 2.0 hiện đã được hợp nhất vào nhánh `main`, trạng thái `main HEAD` không còn trùng với thẻ phục hồi trước nâng cấp. Mọi thao tác hoàn nguyên phải được thực hiện theo nguyên tắc **không phá hủy (Non-Destructive)** qua các commit `git revert` và cờ tính năng, tuyệt đối không dùng `git reset --hard` làm mất lịch sử dự án.

---

## 2. BỐN CẤP ĐỘ HOÀN NGUYÊN CHUẨN MỰC (4 ROLLBACK LEVELS)

### 🔴 CẤP ĐỘ 1 — HOÀN NGUYÊN TÍNH NĂNG QUA CỜ (FEATURE ROLLBACK)
* **Phạm vi tác động:** 0 thay đổi Git, 0 rủi ro mã nguồn.
* **Khi nào áp dụng:** Khi phát hiện lỗi trong quá trình kết xuất đồ họa chuyển động, hoặc muốn tạm thời vô hiệu hóa v2 để chạy hoàn toàn qua pipeline video stock v1.
* **Thao tác thực hiện:**
  1. Mở file cấu hình `.agents/skills/video-studio/config/creative_studio_v2.json` và chỉnh sửa:
     ```json
     {
       "creative_studio_v2": {
         "enabled": false
       }
     }
     ```
  2. Dừng các tiến trình render nền nếu đang chạy dở:
     ```bash
     pkill -f "hyperframes" || true
     ```
* **Kết quả:** Kỹ năng `video-studio` tự động bỏ qua toàn bộ luồng Storyboard v2 và sử dụng 100% pipeline Video Studio v1 truyền thống.

---

### 🟡 CẤP ĐỘ 2 — HOÀN NGUYÊN THÀNH PHẦN CỤ THỂ (COMPONENT ROLLBACK)
* **Phạm vi tác động:** Hoàn nguyên một tính năng hoặc module con cụ thể mà không làm ảnh hưởng đến các phần còn lại.
* **Khi nào áp dụng:** Khi một component riêng biệt (ví dụ: một preset cụ thể, validator hoặc adapter) phát sinh lỗi, cần hoàn nguyên về commit trước đó.
* **Thao tác thực hiện:**
  1. Xác định commit đã thay đổi module đó và kiểm tra blast radius (phụ thuộc chéo):
     ```bash
     git log --oneline -5 -- .agents/skills/_shared/creative/<module>/
     ```
  2. Tạo commit hoàn nguyên không phá hủy:
     ```bash
     git revert --no-edit <commit_hash>
     ```
  3. Chạy kiểm thử đơn vị của module để xác nhận:
     ```bash
     pytest tests/creative/ -k "<tên_module>"
     ```

---

### 🟠 CẤP ĐỘ 3 — HOÀN NGUYÊN TOÀN BỘ ĐỀ ÁN HẬU HỢP NHẤT (UPGRADE ROLLBACK)
* **Phạm vi tác động:** Đưa toàn bộ mã nguồn trên nhánh `main` trở lại trạng thái chức năng trước khi hợp nhất đề án.
* **Khi nào áp dụng:** Khi phát sinh lỗi hồi quy nghiêm trọng ảnh hưởng đến các kỹ năng khác trong workspace sau khi đã merge vào `main`.
* **Thao tác thực hiện:**
  1. Tuyệt đối KHÔNG force push hoặc reset nhánh `main`.
  2. Tạo commit hoàn nguyên merge commit sạch sẽ (Revert Merge Commit):
     ```bash
     # Hoàn nguyên commit merge 57a0a1b và commit đồng bộ chứng chỉ
     git revert -m 1 57a0a1b -m "revert: hoàn nguyên đề án Creative Studio 2.0 trên main về trạng thái ổn định"
     ```
  3. Kích hoạt đồng bộ môi trường:
     ```bash
     bash scripts/auto-setup.sh --quiet
     ```
  4. Đẩy commit hoàn nguyên lên remote an toàn:
     ```bash
     git push origin main
     ```

---

### 🔵 CẤP ĐỘ 4 — PHỤC HỒI ĐỐI CHIẾU CƠ SỞ (RECOVERY BASELINE INSPECTION)
* **Phạm vi tác động:** Tham chiếu và đối soát toàn diện với trạng thái gốc của hệ thống.
* **Khi nào áp dụng:** Khi cần so sánh, bóc tách diff hoặc trích xuất lại mã nguồn nguyên bản tại thời điểm trước khi bắt đầu nâng cấp.
* **Thao tác thực hiện:**
  1. Thẻ `backup/creative-studio-v2-pre-upgrade` đóng vai trò là **REFERENCE / RECOVERY BASELINE** bất biến.
  2. Xem diff giữa trạng thái hiện tại và baseline gốc:
     ```bash
     git diff backup/creative-studio-v2-pre-upgrade HEAD --stat
     ```
  3. Trích xuất một file hoặc thư mục cụ thể từ baseline gốc nếu cần khôi phục riêng lẻ:
     ```bash
     git checkout backup/creative-studio-v2-pre-upgrade -- <đường_dẫn_file>
     ```
  4. TUYỆT ĐỐI KHÔNG sử dụng `git reset --hard backup/creative-studio-v2-pre-upgrade` vì hành vi này sẽ phá hủy toàn bộ commit history trên nhánh `main`.

---

## 3. QUY TRÌNH KIỂM THỬ KHÓI BẮT BUỘC SAU HOÀN NGUYÊN (SMOKE TEST VERIFICATION)

Sau bất kỳ thao tác hoàn nguyên nào thuộc Cấp độ 1, 2, 3 hoặc 4, Agent BẮT BUỘC phải thực thi quy trình kiểm thử khói để chứng minh hệ thống hoạt động ổn định:

1. **Kiểm tra trạng thái Git:**
   ```bash
   git status --short
   ```
   *(Kết quả: working tree clean, không có file lỗi cú pháp hoặc merge conflict).*
2. **Kiểm tra tuân thủ tái sử dụng engine (Luật R7):**
   ```bash
   python3 scripts/check_shared_reuse.py
   ```
   *(Kết quả bắt buộc: 0 FAIL, 0 WARN).*
3. **Kiểm toán chứng chỉ kỹ năng (Luật R4):**
   ```bash
   python3 scripts/audit_skill.py --scan-new
   ```
   *(Kết quả: Toàn bộ 19 kỹ năng hợp chuẩn).*
4. **Kiểm tra bộ test suite:**
   ```bash
   pytest tests/creative/ -v
   ```
   *(Toàn bộ test cases tương ứng phải PASS).*
