# AIWF CREATIVE STUDIO 2.0 — QUY TRÌNH PHỤC HỒI & HOÀN NGUYÊN (ROLLBACK PROCEDURE)

> **Mã tài liệu:** `docs/creative-studio-v2/08-rollback.md`  
> **Giai đoạn:** Phase 0 — Recovery Strategy & Rollback Standard Operating Procedure  
> **Nguyên tắc cốt lõi:** BẢO TOÀN DỮ LIỆU TUYỆT ĐỐI (Rule R1 Zero-Destruction). CẤM các lệnh hủy diệt: `git reset --hard`, `git clean -fd`, `git push --force`.

---

## 1. NGUYÊN TẮC BẢO VỆ DỮ LIỆU TRONG MỌI TÌNH HUỐNG

1. **Bảo tồn nhánh gốc `main`:** Nhánh `main` tại commit cơ sở `7c989ea62df9816f73ab866fbcc38b9597e52eb8` được bảo vệ nguyên vẹn bằng tag `backup/creative-studio-v2-pre-upgrade`.
2. **Không làm mất file người dùng:** Bất kỳ file nháp, kịch bản hoặc tài liệu nào do người dùng tạo ra trong quá trình nâng cấp đều phải được giữ nguyên hoặc chuyển vào thư mục lưu trữ an toàn trước khi hoàn nguyên.
3. **Minh bạch trạng thái:** Mọi thao tác rollback phải được ghi nhận rõ ràng vào nhật ký tiến trình.

---

## 2. BỐN CẤP ĐỘ HOÀN NGUYÊN (4 ROLLBACK LEVELS)

### 🔴 CẤP ĐỘ 1 — VÔ HIỆU HÓA CỜ TÍNH NĂNG (FEATURE DISABLE)
* **Khi nào áp dụng:** Khi xuất hiện lỗi render hoặc kết quả đồ họa động không như ý muốn, nhưng mã nguồn không làm gãy hệ thống tổng thể.
* **Thao tác thực hiện:**
  1. Mở file cấu hình cờ tính năng và đổi:
     ```json
     {
       "creative_studio_v2": {
         "enabled": false
       }
     }
     ```
  2. Dừng mọi tiến trình render nền đang chạy:
     ```bash
     pkill -f "hyperframes" || true
     ```
* **Kết quả:** Hệ thống lập tức quay về sử dụng 100% pipeline truyền thống của Video Studio v1 mà không cần bất kỳ thao tác Git nào.

---

### 🟡 CẤP ĐỘ 2 — HOÀN NGUYÊN THEO GIAI ĐOẠN (PHASE ROLLBACK)
* **Khi nào áp dụng:** Khi một giai đoạn cụ thể (ví dụ Phase 3 hoặc Phase 4) gặp sự cố, và muốn quay về điểm kiểm tra (checkpoint) ổn định gần nhất trong nhánh `feature/creative-studio-v2`.
* **Thao tác thực hiện (Không dùng reset hard):**
  1. Kiểm tra lịch sử checkpoint bằng lệnh:
     ```bash
     git log --oneline -10
     ```
  2. Xác định commit SHA của checkpoint ổn định trước đó (ví dụ `CP2` hoặc `CP1`).
  3. Tạo commit hoàn nguyên không phá hủy:
     ```bash
     git revert --no-edit <commit_sha_loi>..HEAD
     ```
  4. Xác minh lại bộ kiểm thử của checkpoint trước đó.

---

### 🟠 CẤP ĐỘ 3 — TỪ BỎ HOÀN TOÀN NHÁNH NÂNG CẤP (FULL UPGRADE ABANDONMENT)
* **Khi nào áp dụng:** Khi bản nâng cấp v2.0 bị đánh giá là không khả thi hoặc người dùng yêu cầu quay trở lại trạng thái ban đầu của kho mã nguồn.
* **Thao tác thực hiện:**
  1. Đảm bảo toàn bộ tài liệu chẩn đoán hoặc dữ liệu của người dùng được sao lưu vào `_process/` hoặc thư mục tải về.
  2. Chuyển nhánh về lại `main`:
     ```bash
     git checkout main
     ```
  3. Kiểm tra xem nhánh `main` có đang khớp chính xác với tag phục hồi không:
     ```bash
     git rev-parse HEAD
     git rev-parse backup/creative-studio-v2-pre-upgrade^{commit}
     ```
     *(Cả hai mã SHA phải khớp hoàn toàn: `7c989ea62df9816f73ab866fbcc38b9597e52eb8`).*
  4. Nếu cần dọn nhánh thử nghiệm sau khi đã xác nhận an toàn:
     ```bash
     git branch -D feature/creative-studio-v2
     ```

---

### 🔵 CẤP ĐỘ 4 — PHỤC HỒI SAU KHI ĐÃ MERGE VÀO MAIN (POST-MERGE RECOVERY)
* **Khi nào áp dụng:** Nếu sau này nhánh tính năng đã được merge vào `main` nhưng phát sinh lỗi nghiêm trọng ở môi trường vận hành thực tế.
* **Thao tác thực hiện:**
  1. Tuyệt đối KHÔNG force push (`git push --force`) vào `main`.
  2. Tạo commit hoàn nguyên sạch sẽ (Revert Merge Commit):
     ```bash
     git revert -m 1 <merge_commit_sha> -m "revert: hoàn nguyên Creative Studio 2.0 về trạng thái ổn định"
     git push origin main
     ```
  3. Chạy lại script cài đặt môi trường để đồng bộ:
     ```bash
     bash scripts/auto-setup.sh
     ```

---

## 3. BÀI TEST KIỂM TRA ĐỘ TOÀN VẸN CƠ SỞ (SMOKE TEST VERIFICATION)

Sau bất kỳ thao tác hoàn nguyên nào, Agent bắt buộc phải chạy quy trình kiểm thử khói để xác nhận hệ thống hoạt động ổn định:

1. **Kiểm tra trạng thái Git:**
   ```bash
   git status --short
   ```
   *(Kết quả phải rỗng hoặc không có file bị hỏng).*
2. **Kiểm tra Luật R7:**
   ```bash
   python3 scripts/check_shared_reuse.py
   ```
   *(Kết quả: `✅ R7: không phát hiện trùng lặp`).*
3. **Kiểm tra toàn bộ Skill hiện có:**
   ```bash
   python3 scripts/audit_skill.py --scan-new
   ```
   *(Kết quả: Toàn bộ kỹ năng đã xác thực).*
4. **Kiểm tra cú pháp Python:**
   ```bash
   python3 -m py_compile .agents/skills/video-studio/scripts/*.py
   ```
