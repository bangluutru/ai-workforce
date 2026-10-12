---
runbook_id: marketing-campaign
display_name: Chiến Dịch Nội Dung Đa Kênh (Multi-Channel Marketing Campaign)
description: Quy trình sáng tạo chiến dịch nội dung tiếp thị tích hợp, kết hợp nghiên cứu thị trường, bài viết đa kênh (Blog SEO, Facebook, PR), ấn phẩm đồ họa in ấn/digital, kiểm duyệt nghiêm ngặt Luật Quảng cáo (Rule R5).
trigger: "Chiến dịch marketing, chiến dịch nội dung, marketing campaign, kế hoạch truyền thông đa kênh"
roster:
  - research-synthesist
  - brand-guardian
  - legal-compliance-reviewer
  - reality-checker
  - project-shepherd
skills_used:
  - viet-bai
  - thiet-ke
required_inputs:
  - Brief chiến dịch, mục tiêu truyền thông, đối tượng mục tiêu (Persona)
  - Thông điệp chủ đạo (Key Message), định vị thương hiệu hoặc Brand Kit
final_deliverables:
  - Bộ bài viết đa kênh (Blog SEO, Post Facebook, Bài PR báo chí) .docx / .md
  - Bộ ấn phẩm đồ họa (Leaflet/Poster in ấn 300 DPI hoặc Banner Digital) .pdf / .png
  - Báo cáo kiểm định pháp lý claim_guard_report.json (0 vi phạm)
  - Hồ sơ bằng chứng evidence_pack.json
---

# 📢 RUNBOOK: CHIẾN DỊCH NỘI DUNG ĐA KÊNH (MARKETING CAMPAIGN)

> **Mô hình:** Sequential Role-Based Pipeline with Legal Gate & Brand Compliance  
> **Thành phẩm lưu tại:** `<output_dir>/campaign_<ten_chien_dich>_<timestamp>/` (mặc định: `~/Downloads/AIWF_Output/`)

---

## 👥 ĐỘI HÌNH VAI TRÒ (ROSTER)
- **Research & Evidence Synthesist:** Khảo sát đối thủ, thị trường, tìm kiếm dữ liệu thống kê có căn cứ chứng minh.
- **Brand Guardian:** Thiết lập Brand Guidelines cho chiến dịch: thông điệp, Tone & Voice, typography, màu sắc.
- **Legal & Regulatory Reviewer:** Chốt chặn pháp lý, quét tự động chống over-claim qua `claim_guard.py` (Rule R5).
- **Reality Checker:** Thẩm định tính thực tế của thông điệp, kiểm tra footnote chứng minh cho các tuyên bố thị phần/chất lượng.
- **Project Shepherd:** Điều phối các mốc bàn giao bài viết và ấn phẩm đồ họa, tổ chức duyệt cổng nghiệm thu.

---

## ⚙️ CÁC CHẶNG THỰC THI (EXECUTION PHASES)

### 📌 Chặng 1: Nghiên Cứu Định Vị & Thông Điệp Cốt Lõi (Research & Brand Foundation)
- **Vai trò chịu trách nhiệm:** `research-synthesist` phối hợp `brand-guardian`
- **Hành động:**
  1. Phân tích chân dung khách hàng mục tiêu, rào cản tâm lý và động lực mua hàng.
  2. Xác định thông điệp cốt lõi (Big Idea), bộ từ khóa SEO và định vị chiến dịch.
  3. Lập khung nhận diện chiến dịch: Bảng màu, typography, tone & voice, danh mục việc NÊN và KHÔNG NÊN làm.
- **Handoff Contract:** File `<process_dir>/campaign_strategy.md`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 🛑 CHỐT PHÊ DUYỆT 1: DUYỆT ĐỊNH HƯỚNG CHIẾN DỊCH (GATE 1 - STRATEGY APPROVAL)
- `project-shepherd` tóm tắt chiến lược, thông điệp cốt lõi và kế hoạch phân bổ kênh cho người dùng.
- Người dùng duyệt chiến lược trước khi triển khai sản xuất nội dung quy mô lớn.

---

### 📌 Chặng 2: Sản Xuất Nội Dung Chữ Đa Kênh (Multi-Format Copywriting)
- **Vai trò chịu trách nhiệm:** Skill `viet-bai` (Người viết: Content Creator)
- **Hành động:**
  1. Soạn thảo bài viết Blog SEO chuẩn cấu trúc heading, meta title, meta description.
  2. Soạn thảo chuỗi bài đăng mạng xã hội (Facebook, LinkedIn) tương ứng với từng giai đoạn phễu nhận thức.
  3. Soạn thảo bài PR báo chí trang trọng, giàu dữ kiện khách quan.
  4. Khử sạch toàn bộ dấu vết văn phong AI tiếng Việt (cấm em dash `—`, cấm Oxford comma, cấm từ ngữ sáo rỗng).
- **Handoff Contract:** Thư mục bài viết `<process_dir>/content_drafts/`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 📌 Chặng 3: Thiết Kế Ấn Phẩm Đồ Họa Truyền Thông (Visual Design Assets)
- **Vai trò chịu trách nhiệm:** Skill `thiet-ke` (Người vẽ: Visual Designer)
- **Hành động:**
  1. Thiết kế ấn phẩm in ấn (Leaflet gấp 2/3 hoặc Poster A4/A3) chuẩn xén lề bleed $\ge 3\text{mm}$, safe margin $\ge 15\text{pt}$.
  2. Thiết kế banner digital đa kích thước hiển thị (Facebook Cover, Feed square 1:1, Story 9:16).
  3. Xuất bản PDF in ấn CMYK/300 DPI và file ảnh PNG sắc nét.
- **Handoff Contract:** Thư mục ấn phẩm `<process_dir>/visual_assets/`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 📌 Chặng 4: Kiểm Duyệt Pháp Lý & Thẩm Định Thực Tế (Legal R5 & Reality Gate)
- **Vai trò chịu trách nhiệm:** `legal-compliance-reviewer` và `reality-checker`
- **Hành động:**
  1. `legal-compliance-reviewer` chạy lệnh kiểm tra over-claim trên toàn bộ bài viết:
     ```bash
     python3 scripts/claim_guard.py --input <process_dir>/content_drafts/ --profile ads
     ```
  2. Đảm bảo Exit Code = 0. Triệt tiêu mọi từ ngữ cấm: "số một", "duy nhất", "an toàn tuyệt đối", "đặc trị".
  3. `reality-checker` đối chiếu các con số (doanh số, số lượng người dùng) với nguồn trích dẫn ghi chú dưới chân trang.
  4. Thu thập toàn bộ bằng chứng, tính mã băm SHA256 và lập `evidence_pack.json`.
- **Handoff Contract:** `claim_guard_report.json`, `evidence_pack.json`.
- **Evidence Gate:** `TESTED` và `OBSERVED`.

---

### 🛑 CHỐT PHÊ DUYỆT 2: DUYỆT TRỌN BỘ CHIẾN DỊCH (GATE 2 - CAMPAIGN SIGN-OFF)
- `project-shepherd` trình gói ấn phẩm và bài viết đã qua kiểm duyệt pháp lý cho người dùng.
- Người dùng duyệt phát hành.

---

### 📌 Chặng 5: Đóng Gói Chiến Dịch Sạch Sẽ (Clean Campaign Package)
- Lưu toàn bộ tài liệu vào `<output_dir>/campaign_<ten_chien_dich>_<timestamp>/`:
  - Thư mục `articles/`: Các file .docx và .md hoàn chỉnh.
  - Thư mục `designs/`: Các file PDF in ấn và ảnh banner.
  - File `compliance_report.json` và `evidence_pack.json`.
- Tóm tắt trên chat các điểm nhấn chiến dịch và lịch trình đăng tải khuyến nghị.
