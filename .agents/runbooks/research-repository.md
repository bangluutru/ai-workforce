---
runbook_id: research-repository
display_name: Nghiên Cứu & Đọc Sâu Dữ Liệu (Deep Research & Knowledge Synthesis)
description: Quy trình nghiên cứu đa chiều và mổ xẻ tài liệu/mã nguồn chuyên sâu bằng 10 mô hình tư duy, truy vết chứng cứ sơ cấp, đối chiếu SSOT và chuyển hóa thành kế hoạch hành động 24h.
trigger: "Nghiên cứu tài liệu, đọc sâu, phân tích chuyên sâu, research repository, tổng hợp tri thức, deep reading"
roster:
  - research-synthesist
  - systems-architect
  - technical-auditor
  - reality-checker
  - project-shepherd
skills_used:
  - doc-sau
  - chotto-newsroom
required_inputs:
  - Tài liệu đầu vào (PDF, DOCX, EPUB, URL bài viết) hoặc thư mục mã nguồn cần nghiên cứu
  - Câu hỏi nghiên cứu cốt lõi hoặc mục tiêu ra quyết định
final_deliverables:
  - Bản đồ chiến lược tìm kiếm và ma trận bằng chứng (Evidence Map)
  - Báo cáo phân tích chuyên sâu 10 mô hình tư duy (SCQA, 5W2H, Inversion, Đa ngành)
  - Bản tóm tắt điều hành (Executive Summary) và Kế hoạch Quick Win 24h
  - Hồ sơ bằng chứng evidence_pack.json
---

# 📚 RUNBOOK: NGHIÊN CỨU & ĐỌC SÂU DỮ LIỆU (RESEARCH REPOSITORY)

> **Mô hình:** Sequential Role-Based Pipeline with Evidence Synthesis & Deep Analysis  
> **Thành phẩm lưu tại:** `<output_dir>/research_<chu_de>_<timestamp>/` (mặc định: `~/Downloads/AIWF_Output/`)

---

## 👥 ĐỘI HÌNH VAI TRÒ (ROSTER)
- **Research & Evidence Synthesist:** Xây dựng chiến lược tìm kiếm, truy vết nguồn sơ cấp, bóc tách biểu đồ trích dẫn.
- **Multi-Agent Systems Architect:** Phân tích cấu trúc hệ thống, kiến trúc giải pháp và blast radius trong mã nguồn/tài liệu.
- **Technical & Security Auditor:** Kiểm tra tính toàn vẹn cú pháp, an toàn thông tin, đối chiếu với các quy tắc kỹ thuật R0–R7.
- **Reality Checker:** Thẩm định tính xác thực của mọi trích dẫn, đảm bảo 0 hallucination (Rule R3 §9).
- **Project Shepherd:** Điều phối luồng bóc tách dữ liệu, quản lý checkpoint duyệt câu hỏi nghiên cứu và báo cáo bàn giao.

---

## ⚙️ CÁC CHẶNG THỰC THI (EXECUTION PHASES)

### 📌 Chặng 1: Định Khung Nghiên Cứu & Chiến Lược Tìm Kiếm (Research Scoping)
- **Vai trò chịu trách nhiệm:** `research-synthesist`
- **Hành động:**
  1. Chuyển đổi câu hỏi mơ hồ của người dùng thành cấu trúc nghiên cứu rõ ràng: Đối tượng (Subject), Yếu tố so sánh (Intervention/Comparison), Kết quả kỳ vọng (Outcome).
  2. Xác định biên giới tìm kiếm: Các nguồn cơ sở dữ liệu sẽ tra cứu, khoảng thời gian khảo sát, tiêu chí đưa vào (inclusion) và loại trừ (exclusion).
  3. Lập file `<process_dir>/search_strategy.md`.
- **Handoff Contract:** File `search_strategy.md`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 🛑 CHỐT PHÊ DUYỆT 1: DUYỆT CÂU HỎI & BIÊN GIỚI NGHIÊN CỨU (GATE 1 - SCOPE APPROVAL)
- `project-shepherd` tóm tắt câu hỏi nghiên cứu và phạm vi khảo sát cho người dùng.
- Người dùng xác nhận phạm vi hoặc bổ sung tài liệu nội bộ cần đọc.

---

### 📌 Chặng 2: Bóc Tách & Nạp Dữ Liệu Khách Quan (Data Ingestion & Extraction)
- **Vai trò chịu trách nhiệm:** Skill `doc-sau` phối hợp engine `doc_ingest_bridge`
- **Hành động:**
  1. Đọc tệp người dùng thông qua `scripts/doc_ingest.py` (DOCX, PDF, XLSX, PPTX, EPUB) $\rightarrow$ sinh `source.md` và `manifest.json`.
  2. Tuyệt đối không đọc trực tiếp file nhị phân để tránh mất cấu trúc bảng biểu hoặc lỗi font.
  3. Phân đoạn dữ liệu thành các khối thông tin logic (logical chunks) theo ngữ cảnh.
- **Handoff Contract:** Thư mục dữ liệu đã bóc tách `<process_dir>/_ingest/`.
- **Evidence Gate:** `OBSERVED`.

---

### 📌 Chặng 3: Phân Tích Chuyên Sâu Đa Mô Hình (Multi-Model Deep Reading)
- **Vai trò chịu trách nhiệm:** Skill `doc-sau`
- **Hành động:**
  1. Mổ xẻ cấu trúc lập luận theo mô hình SCQA (Tình huống $\rightarrow$ Xung đột $\rightarrow$ Câu hỏi $\rightarrow$ Trọng tâm giải quyết).
  2. Bóc tách bản chất sự việc bằng mô hình 5W2H (What, Why, Who, When, Where, How, How much).
  3. Phân tích rủi ro tiềm ẩn và các điểm gãy đổ qua Tư duy Đảo ngược (Inversion Thinking).
  4. Liên kết các nguyên lý từ các ngành khoa học khác (Tư duy Đa ngành - Mental Models).
  5. Đúc kết hành động thực tiễn: Kế hoạch hành động 24h (Quick Win) và Lộ trình 30 ngày.
- **Handoff Contract:** Bản thảo báo cáo `<process_dir>/draft_deep_reading_report.md`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 📌 Chặng 4: Kiểm Chứng Bằng Chứng & Thẩm Định Thực Tế (Evidence Audit & Reality Gate)
- **Vai trò chịu trách nhiệm:** `reality-checker` và `technical-auditor`
- **Hành động:**
  1. `reality-checker` rà soát từng tuyên bố và số liệu trong báo cáo: Có trích dẫn nguyên văn từ `source.md` không? Có hiện tượng suy diễn vô căn cứ (hallucination) không?
  2. Gắn cờ `[CẦN XÁC MINH]` cho các điểm dữ liệu mờ hoặc có độ tin cậy $< 85\%$ (Confidence Flagging - Rule R4 §2.3).
  3. `technical-auditor` kiểm tra tính toàn vẹn cú pháp của các bảng số liệu và sơ đồ.
  4. Thu thập toàn bộ bằng chứng, tính mã băm SHA256 và lập `evidence_pack.json`.
- **Handoff Contract:** `evidence_pack.json`, `audit_notes.md`.
- **Evidence Gate:** `TESTED` và `OBSERVED`.

---

### 🛑 CHỐT PHÊ DUYỆT 2: DUYỆT BÁO CÁO NGHIÊN CỨU (GATE 2 - REPORT ACCEPTANCE)
- `project-shepherd` gửi bản Tóm tắt Điều hành (Executive Summary) và thông báo các cờ cảnh báo (nếu có).
- Người dùng duyệt báo cáo.

---

### 📌 Chặng 5: Xuất Bản Báo Cáo Chuyên Nghiệp (Clean Publishing)
- Chuyển đổi báo cáo thành các định dạng thành phẩm chuyên nghiệp lưu tại `<output_dir>/research_<chu_de>_<timestamp>/`:
  - File Markdown báo cáo đầy đủ: `bao_cao_nghien_cuu_chuyen_sau.md`.
  - File Word báo cáo theo mẫu doanh nghiệp chuẩn mực (qua `_shared/docx/legal_report.py`): `bao_cao_nghien_cuu.docx`.
  - File hồ sơ bằng chứng: `evidence_pack.json`.
- Tóm tắt trên chat: 3 phát hiện bất ngờ nhất, 3 rủi ro cốt lõi và 3 hành động cần làm ngay trong 24 giờ tới.
