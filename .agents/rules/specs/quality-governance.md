# ĐẶC TẢ KỸ THUẬT: QUẢN TRỊ CHẤT LƯỢNG & PHẢN BIỆN CHÉO (SPEC-QG-01)
## Chuẩn Phản Biện Chéo Phân Tầng Rủi Ro Cho AI Workforce

> **Mã đặc tả:** SPEC-QG-01  
> **Quy chuẩn cha:** Rule R3 (Operational Discipline §9) & Rule R4 (Skill Standard v1.2)  
> **Engine thực thi:** `_shared/governance/evidence_gate.py` & `_shared/governance/review_router.py`

---

## 1. NGUYÊN LÝ NỀN TẢNG

1. **Không Có Phê Duyệt Ảo Tưởng (No Fantasy Approvals):**
   - Mọi tuyên bố hoàn thành hoặc đánh giá chất lượng phải được chứng minh bằng bằng chứng kỹ thuật (mã băm SHA256, exit code, log console, hoặc ảnh chụp Playwright).
   - Tuyên bố hoàn thành không kèm bằng chứng bị coi là vi phạm nghiêm trọng Rule R3 §9 (Zero Unverified Claims Ban).
2. **Phân Định Rạch Ròi Bản Chất Người Thẩm Định:**
   - `human`: Con người thực tế trải nghiệm và xác nhận (độc lập tuyệt đối).
   - `separate_agent`: Agent/subagent chạy trong phiên làm việc độc lập với ngữ cảnh riêng.
   - `automated_test`: Công cụ kiểm thử phần mềm tự động (pytest, Playwright, claim_guard, ffprobe).
   - `same_context_agent`: Cùng mô hình LLM trong cùng phiên hội thoại. **BẮT BUỘC ĐÁNH DẤU `independent: false` VÀ KẸP TRẦN ĐIỂM SỐ $\le 3.0/5.0$**.
3. **Phân Tầng Theo Cấp Độ Rủi Ro (Risk-Tiered Quality Governance):**
   - Không áp dụng cùng một quy trình nặng nề cho mọi tác vụ. Tác vụ nhỏ chạy tinh gọn; tác vụ lớn/nhạy cảm bắt buộc qua hội đồng phản biện và chốt phê duyệt con người.

---

## 2. MA TRẬN 3 PHÂN TẦNG RỦI RO (THE 3-TIER MATRIX)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: RỦI RO THẤP (LOW RISK)                                         │
│ • Định nghĩa: Sửa chính tả, cập nhật docs, chỉnh sửa vi mô < 10 dòng   │
│ • Quy trình: Minimal Change Engineer thực thi -> Linter/syntax check   │
│ • Yêu cầu phản biện chéo: KHÔNG (Tránh lãng phí token & độ trễ)        │
│ • Chốt phê duyệt người dùng: KHÔNG BẮT BUỘC                            │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: RỦI RO TRUNG BÌNH (MEDIUM RISK)                                │
│ • Định nghĩa: Thêm tính năng mới, viết bài tiếp thị, dựng video MP4    │
│ • Quy trình: Role chuyên trách thực thi -> Kiểm thử tự động (Test/QA)  │
│ • Yêu cầu phản biện chéo: BẮT BUỘC (Reality Checker HOẶC Brand Review) │
│ • Người thẩm định: automated_test + same_context_agent (flagged)       │
│ • Chốt phê duyệt người dùng: Xem trước tóm tắt bằng chứng              │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: RỦI RO CAO (HIGH RISK)                                         │
│ • Định nghĩa: Kiến trúc hệ thống, pháp lý, thuế, xuất bản production   │
│ • Quy trình: Multi-role pipeline -> Đa chốt kiểm định vật lý           │
│ • Yêu cầu phản biện chéo: BẮT BUỘC ĐA VAI TRÒ ĐỘC LẬP                  │
│ • Chốt phê duyệt người dùng: BẮT BUỘC (Gate 3 - Human Acceptance Gate) │
│ • CẤM tự ý xuất bản hoặc kết thúc khi chưa có chữ ký người dùng        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. BA CHỐT PHÊ DUYỆT CON NGƯỜI (THE 3 HITL GATES)

Mọi Team Runbook của AIWF tích hợp 3 chốt phê duyệt con người có cấu trúc:

1. **Gate 1 — Duyệt Kế Hoạch & Phạm Vi (Plan & Scope Approval):**
   - Diễn ra ngay sau Chặng Khảo sát/Kiến trúc.
   - Người dùng xem bảng đặc tả I/O và phạm vi trước khi cấp phép thực thi viết code hoặc sản xuất tài nguyên nặng.
2. **Gate 2 — Duyệt Bằng Chứng Kỹ Thuật (Technical Evidence Review):**
   - Diễn ra sau khi hoàn tất kiểm thử tự động và kiểm định thực tế.
   - Người dùng xem ảnh chụp màn hình, kết quả kiểm tra linter/an ninh, và báo cáo `claim_guard.py`.
3. **Gate 3 — Nghiệm Thu Cuối & Xuất Bản (Final Acceptance & Publish):**
   - Chốt chặn cuối cùng trước khi chuyển giao thành phẩm sạch ra `<output_dir>` và phát hành ra môi trường bên ngoài.
   - Bắt buộc ghi nhận tên người duyệt (`approver`), thời gian (`timestamp`) và ghi chú vào `evidence_pack.json`.

---

## 4. RANH GIỚI TIN CẬY (TRUST BOUNDARY) VÀ GIỚI HẠN HIỆN TẠI

> Nguyên tắc: **dữ liệu do caller kiểm soát không bao giờ là bằng chứng tin cậy.**

- Đối số hàm, JSON, Evidence Pack, metadata agent (`trusted_attestation`, `verified=True`, `source`, `subagent_id`, `execution_context`, `independent`, `exit_code=`, nội dung log) chỉ là **CLAIM**. Chúng được lưu để audit nhưng không xác lập "verified".
- `evidence_gate.py` / `review_router.py` tách 3 lớp: claim (khai báo) → bằng chứng thực thi (tệp tồn tại, đúng cấu trúc, còn khớp SHA-256) → kết quả xác minh tin cậy (chỉ từ verifier ngoài ranh giới dữ liệu, đăng ký trong tiến trình; không nạp được từ JSON).
- `evidence_ref` là tệp cục bộ được phép làm bằng chứng hỗ trợ; nội dung không được suy diễn PASS. Chuỗi như `exit_code=0` bị từ chối. URL ngoài chỉ là tham chiếu.
- Tier 1: không yêu cầu verifier. Tier 2: cần automated test được runner tin cậy xác minh. Tier 3: thêm thẩm định độc lập được xác minh + phê duyệt con người được xác thực. Thiếu verifier → `UNVERIFIED_INDEPENDENT_CLAIM` / `APPROVAL_CLAIMED` và Tier 2/3 **fail-closed**.
- Automated test đã xác minh **không bao giờ** thay thế yêu cầu thẩm định độc lập (agent/human) hay phê duyệt con người.

**Giới hạn hiện tại (OBSERVED):** AIWF **chưa** cài verifier tin cậy nào cho (1) phê duyệt con người, (2) thực thi subagent độc lập. Hai cơ chế này vẫn **chưa được triển khai** nên Tier 3 vẫn bị chặn. `overall_status` của Evidence Pack phản ánh trạng thái bằng chứng khai báo, không phải mức bảo đảm; quyết định phát hành do `review_router.audit_review_compliance` đưa ra.

### 4.1 Local Execute-to-Verify (`trusted_runner.py`, opt-in)

- Bật bằng `review_router.py --check-pack ... --verify-by-execution`. Mặc định vẫn fail-closed. Chỉ đăng ký verifier cho `automated_test`; **không** xác minh phê duyệt con người hay thẩm định độc lập.
- Runner tự chạy profile trong allowlist `_shared/governance/trusted_commands.json` (đúng 2 profile: `governance-tests`, `shared-reuse`; executable cố định = interpreter của runner, đối số cố định, cwd trong repo, timeout; không shell, không biến môi trường tùy ý). Step chỉ được nêu `verification_method = "trusted_command:<id>"`; mọi trường khác do caller cung cấp bị bỏ qua. Runner chạy lại tại thời điểm quyết định, bắt exit code thật, gắn với profile + git revision + dấu vân tay cây làm việc (cây đổi trong lúc chạy → FAIL). Log/`record.json` chỉ để audit, không bao giờ được đọc làm bằng chứng tin cậy. Evidence file vẫn phải còn khớp SHA-256.
- Tier 2 đạt yêu cầu automated test **chỉ khi** runner thực sự chạy profile và exit 0. Điều này chỉ chứng minh lần chạy test đó, **không** chứng minh repo an toàn để deploy.
- `trusted_commands.json` là file chính sách **Tier 3**. `scripts/check_policy_files.py` (nối vào `scripts/hooks/pre-commit`) chặn mọi thay đổi staged (fail closed, không có cờ/biến môi trường/token bypass).
- **Giới hạn trung thực:** (a) chưa có cơ chế ủy quyền bên ngoài cưỡng chế được; thay đổi chính sách vẫn bị chặn và chờ review thủ công. (b) Hook KHÔNG phải ranh giới bảo mật (`--no-verify` hoặc sửa hook vô hiệu hóa nó). (c) Runner chạy bằng quyền người dùng nên không chống được agent bị chiếm quyền sửa runner/allowlist; kiểm soát thật duy nhất là review git bên ngoài. (d) CI độc lập (Option C) được hoãn.
