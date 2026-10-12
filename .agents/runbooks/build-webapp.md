---
runbook_id: build-webapp
display_name: Xây Dựng Ứng Dụng Web (Build Web Application)
description: Quy trình phối hợp đa vai trò tuần tự để thiết kế, lập trình, kiểm thử và bàn giao ứng dụng web tương tác chất lượng cao, chuẩn responsive 4 viewports và WCAG AA.
trigger: "Xây dựng webapp, tạo ứng dụng web, build webapp, phát triển landing page tương tác"
roster:
  - systems-architect
  - ux-reviewer
  - minimal-change-engineer
  - evidence-collector
  - reality-checker
  - project-shepherd
skills_used:
  - tao-landing-page
  - app-auditor
required_inputs:
  - Brief yêu cầu tính năng, nội dung hoặc wireframe mockup từ người dùng
  - Phong cách thiết kế, bảng màu hoặc Brand Kit (nếu có)
final_deliverables:
  - Mã nguồn hoàn chỉnh (HTML/CSS/JS hoặc React + Vite + Tailwind)
  - Báo cáo kiểm định toàn diện (Visual sweep 4 viewports, console logs, WCAG a11y)
  - Hồ sơ bằng chứng machine-readable evidence_pack.json
---

# 🚀 RUNBOOK: XÂY DỰNG ỨNG DỤNG WEB (BUILD WEBAPP)

> **Mô hình:** Sequential Role-Based Pipeline with Evidence Gates & HITL Checkpoints  
> **Thành phẩm lưu tại:** `<output_dir>/webapp_<timestamp>/` (mặc định: `~/Downloads/AIWF_Output/`)

---

## 👥 ĐỘI HÌNH VAI TRÒ (ROSTER)
- **Multi-Agent Systems Architect:** Thiết kế cấu trúc component, topology luồng dữ liệu, context budget.
- **UX & Usability Reviewer:** Thẩm định trải nghiệm người dùng, bố cục responsive 4 viewports, chuẩn WCAG 2.1 AA.
- **Minimal Change Engineer:** Triển khai mã nguồn theo kỷ luật Rule R2, diff nhỏ nhất, chống scope creep.
- **Evidence Collector:** Thu thập ảnh chụp màn hình Playwright, log console, tính mã băm SHA256 cho artifact.
- **Reality Checker:** Chặn phê duyệt ảo tưởng, trực tiếp đối chiếu webapp đang chạy với đặc tả ban đầu.
- **Project Shepherd:** Điều phối tiến độ qua các phase, kiểm soát checkpoint phê duyệt và bàn giao sạch.

---

## ⚙️ CÁC CHẶNG THỰC THI (EXECUTION PHASES)

### 📌 Chặng 1: Khảo sát Kiến trúc & Trải nghiệm (Architecture & UX Scoping)
- **Vai trò chịu trách nhiệm:** `systems-architect` phối hợp `ux-reviewer`
- **Đầu vào:** Brief người dùng, yêu cầu chức năng.
- **Hành động:**
  1. Phân tích bài toán, xác định các phân đoạn giao diện cốt lõi (Hero, Features, Interactive Widget, Pricing, Footer).
  2. Xác định cấu trúc thư mục, thư viện hỗ trợ (Vanilla HTML/CSS/JS hoặc React/Vite/Tailwind).
  3. Lập đặc tả I/O và wireframe layout: `<process_dir>/architecture_spec.md`.
- **Hợp đồng bàn giao (Handoff):** File `architecture_spec.md` với danh sách components và token thiết kế.
- **Cổng bằng chứng (Evidence Gate):** Trạng thái `IMPLEMENTED`.

---

### 🛑 CHỐT PHÊ DUYỆT 1: DUYỆT KẾ HOẠCH & PHẠM VI (GATE 1 - PLAN APPROVAL)
- `project-shepherd` tóm tắt kiến trúc và phạm vi cho người dùng.
- **Người dùng xác nhận duyệt:** Chuyển sang Chặng 2.
- **Nếu cần chỉnh sửa:** `systems-architect` cập nhật lại đặc tả.

---

### 📌 Chặng 2: Triển khai Mã nguồn Phẫu thuật Vi mô (Surgical Implementation)
- **Vai trò chịu trách nhiệm:** `minimal-change-engineer` (Huy động skill: `tao-landing-page`)
- **Đầu vào:** `architecture_spec.md` đã được phê duyệt.
- **Hành động:**
  1. Triển khai cấu trúc layout bằng HTML ngữ nghĩa hoặc React components.
  2. Xây dựng logic tương tác tại client (0 token, 0 latency).
  3. Tuân thủ nghiêm ngặt 5 Điều cấm của Rule R2: Không placeholder, không nuốt lỗi, không viết code thừa.
- **Hợp đồng bàn giao:** Mã nguồn hoàn chỉnh trong thư mục dự án hoặc `<output_dir>/webapp_src/`.
- **Cổng bằng chứng:** `IMPLEMENTED`.

---

### 📌 Chặng 3: Kiểm thử Tự động & Thu thập Bằng chứng (Automated Test & Evidence)
- **Vai trò chịu trách nhiệm:** `evidence-collector` (Huy động skill: `app-auditor`)
- **Đầu vào:** Webapp đang khởi chạy trên localhost hoặc file HTML tĩnh.
- **Hành động:**
  1. Chạy Playwright crawler quét toàn trang.
  2. Chụp ảnh màn hình trên 4 viewports tiêu chuẩn: Desktop (1920x1080), Laptop (1366x768), Tablet (768x1024), Mobile (375x667).
  3. Kiểm tra console logs và network requests: đảm bảo 0 uncaught exception, 0 lỗi 404/500 tài nguyên.
  4. Thu thập toàn bộ bằng chứng, tính toán mã băm SHA256 và ghi vào `evidence_pack.json`.
- **Hợp đồng bàn giao:** Thư mục ảnh `screenshots/`, `test_results.json`, `evidence_pack.json`.
- **Cổng bằng chứng:** Trạng thái `TESTED` và `OBSERVED`.

---

### 📌 Chặng 4: Thẩm định Thực tế & Phản biện Khách quan (Reality Check & UX Audit)
- **Vai trò chịu trách nhiệm:** `reality-checker` và `ux-reviewer`
- **Đầu vào:** Bằng chứng thực tế từ Chặng 3.
- **Hành động:**
  1. `ux-reviewer` kiểm tra: Có tràn chữ (overflow) trên mobile không? Có nút nào nhỏ hơn 44x44px không? Độ tương phản chữ/nền có đạt chuẩn WCAG AA không?
  2. `reality-checker` đối chiếu: Mọi tính năng cam kết ở Chặng 1 có thực sự hoạt động hay chỉ là giao diện giả lập?
  3. Xuất báo cáo `reality_check_report.md` với kết luận: `VERIFIED` hoặc `NEEDS_WORK`.
- **Nếu `NEEDS_WORK`:** Chuyển danh sách lỗi cụ thể cho `minimal-change-engineer` sửa dứt điểm, rồi lặp lại Chặng 3.

---

### 🛑 CHỐT PHÊ DUYỆT 2: DUYỆT BẰNG CHỨNG KỸ THUẬT (GATE 2 - EVIDENCE REVIEW)
- `project-shepherd` trình bày bản tóm tắt bằng chứng kiểm định (Exit code, 0 lỗi console, ảnh 4 viewports).
- Người dùng duyệt nghiệm thu kỹ thuật.

---

### 📌 Chặng 5: Đóng gói & Bàn Giao Sạch (Clean Delivery)
- **Vai trò chịu trách nhiệm:** `project-shepherd`
- **Đầu vào:** Toàn bộ thành phẩm và `evidence_pack.json` đã đạt chuẩn.
- **Hành động:**
  1. Di chuyển gói thành phẩm sạch ra `<output_dir>/webapp_<timestamp>/`.
  2. Đảm bảo kho mã nguồn Git hoàn toàn sạch rác.
  3. Cập nhật trạng thái `evidence_pack.json` thành `VERIFIED` (sau khi con người phê duyệt).
  4. Thông báo trên chat: tóm tắt 3 điểm nghiệm thu, đường dẫn mở file `index.html` và báo cáo audit.

---

## 🛡️ HÀNH VI KHI GẶP LỖI & HOÀN NGUYÊN (FAILURE & ROLLBACK)
- Nếu Chặng 2 gây lỗi không thể sửa trong 2 vòng lặp: `minimal-change-engineer` dùng `git checkout` hoặc `git restore` hoàn nguyên về commit gần nhất.
- Nếu Chặng 3 phát hiện lỗi crash runtime: Dừng tiến trình, không chuyển sang Chặng 4, báo cáo trực tiếp nguyên nhân gốc rễ (Root Cause) cho kỹ sư xử lý.
