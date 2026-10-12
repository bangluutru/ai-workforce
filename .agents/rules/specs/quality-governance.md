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
