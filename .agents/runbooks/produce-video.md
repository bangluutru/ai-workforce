---
runbook_id: produce-video
display_name: Sản Xuất Video Truyền Thông (Produce Video Media)
description: Dây chuyền sản xuất video đa phương tiện chất lượng cao khép kín, từ thẩm định dữ kiện chính phủ, biên tập kịch bản sạch pháp lý R5, kết xuất đồ họa chuyển động Creative Studio 2.1, đến kiểm định Visual QA 2.0 và Creative Scorecard.
trigger: "Sản xuất video, làm video truyền thông, produce video, dựng video ngắn TikTok Reels, tạo video infographic"
roster:
  - research-synthesist
  - legal-compliance-reviewer
  - brand-guardian
  - evidence-collector
  - project-shepherd
skills_used:
  - chotto-newsroom
  - viet-bai
  - video-studio
required_inputs:
  - Chủ đề, từ khóa, văn bản chính sách hoặc kịch bản thô
  - Định dạng khung hình (9:16 cho TikTok/Reels/Shorts hoặc 16:9 YouTube)
  - Brand Profile (mặc định: chottoday hoặc doanh nghiệp chỉ định)
final_deliverables:
  - File video hoàn chỉnh MP4 (Full HD 1080p, audio ducking, phụ đề karaoke)
  - Hồ sơ dữ kiện gốc fact_pack.md
  - Bản thảo bài viết và kịch bản video .docx / .md
  - Báo cáo Visual QA 2.0 (contact sheet, ffprobe technical report)
  - Hồ sơ bằng chứng evidence_pack.json
---

# 🎬 RUNBOOK: SẢN XUẤT VIDEO TRUYỀN THÔNG (PRODUCE VIDEO MEDIA)

> **Mô hình:** Sequential Role-Based Pipeline with Creative QA & Evidence Gates  
> **Thành phẩm lưu tại:** `<output_dir>/video_<chu_de>_<timestamp>/` (mặc định: `~/Downloads/AIWF_Output/`)

---

## 👥 ĐỘI HÌNH VAI TRÒ (ROSTER)
- **Research & Evidence Synthesist:** Săn tin, thẩm định nguồn chính phủ (`.go.jp`, `.gov.vn`), lập Fact Pack có tọa độ trích dẫn.
- **Legal & Regulatory Reviewer:** Kiểm duyệt kịch bản, chạy `claim_guard.py` đảm bảo không over-claim (Rule R5).
- **Brand Guardian:** Thẩm định Brand Motion Profile, an toàn lề safe zones, màu sắc thương hiệu, typography.
- **Evidence Collector:** Thu thập contact sheet, trích xuất dữ liệu ffprobe, tính mã băm SHA256 cho video MP4.
- **Project Shepherd:** Điều phối 5 chặng sản xuất, kiểm soát các chốt phê duyệt kịch bản và chất lượng render.

---

## ⚙️ CÁC CHẶNG THỰC THI (EXECUTION PHASES)

### 📌 Chặng 1: Săn Tin & Lập Fact Pack (Fact Pack Creation)
- **Vai trò chịu trách nhiệm:** `research-synthesist` (Huy động skill: `chotto-newsroom`)
- **Hành động:**
  1. Tra cứu thông báo, văn bản chính sách mới từ nguồn chính phủ uy tín qua `search_web`.
  2. Xác minh chéo tối thiểu 2 nguồn độc lập; loại bỏ trích dẫn vòng tròn.
  3. Lập `<process_dir>/fact_pack.md` trả lời 5 câu hỏi cốt lõi: Bản chất, Lộ trình, Đối tượng, Quyền lợi/Nghĩa vụ, Lời khuyên.
- **Handoff Contract:** File `fact_pack.md` kèm bảng tọa độ URL và số hiệu văn bản.
- **Evidence Gate:** Trạng thái `OBSERVED`.

---

### 📌 Chặng 2: Biên Tập Kịch Bản & Kiểm Duyệt Pháp Lý (Scriptwriting & R5 Check)
- **Vai trò chịu trách nhiệm:** Skill `viet-bai` phối hợp `legal-compliance-reviewer`
- **Hành động:**
  1. Soạn thảo bài phân tích chuyên sâu đa kênh (`bai_viet.md`) dựa 100% trên `fact_pack.md`.
  2. Trích xuất kịch bản video phân cảnh 45–60 giây (`video_script.json` hoặc Storyboard v2.0 JSON).
  3. Chạy lệnh kiểm tra pháp lý tự động bắt buộc:
     ```bash
     python3 scripts/claim_guard.py --input <process_dir>/bai_viet.md --profile ads
     ```
  4. Đảm bảo Exit Code = 0 (quét sạch từ ngữ over-claim).
- **Handoff Contract:** `bai_viet.md`, `bai_viet.docx`, `video_script.json`, `claim_guard_report.json`.
- **Evidence Gate:** `TESTED`.

---

### 🛑 CHỐT PHÊ DUYỆT 1: DUYỆT KỊCH BẢN & PHÁP LÝ (GATE 1 - SCRIPT APPROVAL)
- `project-shepherd` tóm tắt thông điệp và kịch bản phân cảnh cho người dùng.
- Người dùng duyệt kịch bản trước khi tiến hành thu âm và render tốn tài nguyên.

---

### 📌 Chặng 3: Kết Xuất Video Hoàn Chỉnh (Rendering & Media Pipeline)
- **Vai trò chịu trách nhiệm:** Skill `video-studio` phối hợp engine `_shared/creative/` và `_shared/media/`
- **Hành động:**
  1. Thu âm giọng đọc AI tiếng Việt tự nhiên chuẩn studio (`VieNeu-TTS` offline).
  2. Kết xuất đồ họa chuyển động qua HyperFrames/Canvas hoặc ghép stock video có bản quyền.
  3. Sinh phụ đề ASS karaoke đồng bộ thời gian từng từ.
  4. Lồng nhạc nền với cơ chế Audio Ducking tự động hạ âm khi có lời nói.
  5. Render video hoàn chỉnh MP4 qua ffmpeg.
- **Handoff Contract:** File `video_media.mp4` tại `<output_dir>/`.
- **Evidence Gate:** `IMPLEMENTED`.

---

### 📌 Chặng 4: Kiểm Định Kép Thị Giác & Bằng Chứng (Visual QA & Creative Scorecard)
- **Vai trò chịu trách nhiệm:** `brand-guardian` và `evidence-collector`
- **Hành động:**
  1. Chạy Video QA 2.0 tự động (`creative.qa`): kiểm tra ffprobe, phát hiện màn hình đen, đứng hình, tràn lề, xuất ảnh `contact_sheet.jpg`.
  2. Chạy Creative Scorecard (`creative_review.py`): đánh giá 6 tiêu chí theo rubric nội bộ, kẹp trần same-context $\le 3.0/5$.
  3. `evidence-collector` tính mã băm SHA256 cho video MP4 và lưu toàn bộ dữ liệu vào `evidence_pack.json`.
- **Handoff Contract:** `contact_sheet.jpg`, `technical_report.json`, `creative_review.json`, `evidence_pack.json`.
- **Evidence Gate:** Trạng thái `TESTED` và `OBSERVED`.

---

### 🛑 CHỐT PHÊ DUYỆT 2: DUYỆT THÀNH PHẨM VIDEO (GATE 2 - FINAL MEDIA APPROVAL)
- `project-shepherd` gửi bản tóm tắt nghiệm thu, ảnh Contact Sheet và đường dẫn file MP4.
- Người dùng duyệt nghiệm thu thành phẩm.

---

### 📌 Chặng 5: Bàn Giao Sạch (Clean Delivery)
- Báo cáo kết quả trên khung chat với:
  - Tóm tắt 3 điểm cốt lõi của nội dung video.
  - Đường dẫn tới file MP4, bài viết DOCX và contact sheet.
  - Hướng dẫn phát hành đa nền tảng (TikTok, Reels, YouTube Shorts).
