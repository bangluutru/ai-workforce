---
name: W1-phong-media
display-name: Phòng Media
description: "Dây chuyền sản xuất nội dung truyền thông đa phương tiện khép kín: Săn tin chính sách Nhật Bản (Chotto Newsroom) -> Biên tập bài phân tích chuyên sâu (Viết Bài Đa Kênh) -> Dựng video ngắn full HD có phụ đề & giọng đọc AI (Video Studio)."
trigger: "Phòng Media, chạy phòng media, sản xuất tin tức và video, workflow phong media"
category: workflows
needs_file: false
file_filter: any
---

# Workflow: Phòng Media (Media Production Pipeline)

> **Mục tiêu:** Tự động hóa toàn diện quy trình sản xuất nội dung đa phương tiện: từ phát hiện sự kiện thời sự/chính sách Nhật Bản, thẩm định nguồn chính phủ (.go.jp), biên tập bài phân tích chuyên sâu chuẩn báo chí đến sản xuất video MP4 hoàn chỉnh (thuyết minh AI, phụ đề karaoke, stock clip, nhạc nền ducking).

---

## 🎯 OUTPUT CUỐI CÙNG (Gói Bàn Giao Sạch)
Toàn bộ thành phẩm được lưu tại thư mục: `<output_dir>/phong_media_<chu_de>/` (mặc định: `~/Downloads/AIWF_Output/`):
1. `fact_pack.md`: Hồ sơ dữ kiện gốc kiểm chứng từ các cơ quan chính phủ Nhật Bản (`.go.jp`, ISA, MHLW, NTA...).
2. `bai_viet.md` & `bai_viet.docx`: Bài viết phân tích hoàn chỉnh, đa kênh (Website/Facebook/PR), 100% số liệu có nguồn, đạt chuẩn kiểm định Luật R5 (`claim_guard.py`).
3. `video_media.mp4`: Video full HD (khổ dọc 9:16 cho TikTok/Reels/Shorts hoặc 16:9 YouTube), giọng đọc AI tiếng Việt tự nhiên (VieNeu-TTS), phụ đề karaoke đồng bộ từng từ, lồng nhạc nền và hiệu ứng giảm âm khi có tiếng nói (Audio Ducking).

---

## 📥 INPUT (Đầu vào)
- **Tùy chọn A (Chủ đề chỉ định):** Tên chủ đề, từ khóa, hoặc đường link bài báo/thông báo do người dùng cung cấp (ví dụ: *"Quy định hoàn thuế Nenkin mới 2026"*, *"Chính sách visa Kỹ năng đặc định số 2"*...).
- **Tùy chọn B (Tự động săn tin):** Nếu người dùng không nêu chủ đề cụ thể, hệ thống tự động quét các thông báo và quy định mới nhất có hiệu lực từ các cổng thông tin chính phủ Nhật Bản (`mhlw.go.jp`, `moj.go.jp`, `nta.go.jp`...).

---

## ⚙️ PROCESS (Quy trình 3 chặng khép kín)

### 📌 Chặng 1: Săn tin & Lập Fact Pack (Skill: `chotto-newsroom`)
1. **Tìm kiếm & Thẩm định:**
   - Dùng `search_web` tra cứu các thông cáo báo chí, luật sửa đổi mới từ nguồn chính phủ Nhật (`.go.jp`, MHLW, ISA, NTA, NHK).
   - Xác minh chéo tối thiểu 2 nguồn độc lập.
2. **Lập Fact Pack đối chiếu:**
   - Tạo file `<process_dir>/fact_pack.md` trả lời 5 câu hỏi cốt lõi:
     - *1. Bản chất sự việc là gì? (Điều khoản/Luật/Quy định nào sửa đổi?)*
     - *2. Mốc thời gian & Lộ trình áp dụng khi nào?*
     - *3. Đối tượng chịu ảnh hưởng trực tiếp (Thực tập sinh, Kỹ sư, Tokutei Gino, Du học sinh)?*
     - *4. Quyền lợi hoặc nghĩa vụ mới phát sinh là gì?*
     - *5. Lời khuyên & Lưu ý hành động thực tế cho người Việt tại Nhật?*
   - Kèm bảng tọa độ trích dẫn: Số hiệu văn bản, URL gốc, cơ quan ban hành.

---

### 📌 Chặng 2: Biên tập bài viết chuyên sâu & Lọc pháp lý (Skill: `viet-bai`)
1. **Tiếp nhận & Sáng tạo nội dung:**
   - Nhận `<process_dir>/fact_pack.md` làm Nguồn Sự Thật Duy Nhất (SSOT) — tuyệt đối cấm bịa thêm số liệu ngoài Fact Pack.
   - Soạn thảo bài viết theo công thức báo chí đa kênh:
     - **Tiêu đề:** Rõ ràng, hấp dẫn, đúng bản chất, không giật tít lừa dối.
     - **Sapo / Điểm tin nhanh:** 3 gạch đầu dòng tóm tắt thông tin quan trọng nhất người đọc cần nắm.
     - **Thân bài:** Đi sâu phân tích quyền lợi, điều kiện, thủ tục hồ sơ từng bước.
     - **Lời khuyên thực tế & Cảnh báo lừa đảo:** Nhắc nhở người đọc tránh bị môi giới xấu trục lợi.
2. **Kiểm duyệt tự động Luật R5:**
   - Chạy lệnh kiểm tra tính hợp chuẩn tiếp thị & pháp lý:
     ```bash
     python3 scripts/claim_guard.py --input <process_dir>/draft_bai_viet.md
     ```
   - Đảm bảo Exit Code = 0 (không chứa từ ngữ over-claim cấm).
3. **Xuất bản:**
   - Lưu `<output_dir>/bai_viet.md` và chuyển đổi sang `<output_dir>/bai_viet.docx`.
   - Trích xuất kịch bản video rút gọn (45 - 60 giây, phân cảnh rõ ràng) lưu tại `<process_dir>/video_script.json`.

---

### 📌 Chặng 3: Sản xuất Video Đa phương tiện Hoàn chỉnh (Skill: `video-studio`)
Tùy theo tính chất tin tức, Agent lựa chọn 1 trong 2 hình thức sản xuất video:

#### Tùy Chọn 3A: Video Phóng Sự & Tin Tức Đời Sống (Stock Footage & Voiceover)
1. **Chuẩn bị kịch bản phân cảnh:**
   - File JSON `<process_dir>/video_script.json` gồm các cảnh: `id`, `narration` (lời dẫn ngắt nhịp thở), `visuals` (từ khóa tìm stock footage Pexels/Pixabay), `caption`, `mood`.
2. **Thực thi Pipeline Video Studio:**
   - Chạy lệnh render tự động khép kín:
     ```bash
     python3 .agents/skills/video-studio/scripts/video_pipeline.py \
       --script <process_dir>/video_script.json \
       --topic "<ten_chu_de>" \
       --output "<output_dir>/video_media.mp4" \
       --aspect 9:16 \
       --lang vi \
       --voice "Minh Quân Pro" \
       --no-verify-voice
     ```
   - Hệ thống tự động:
     - Thu âm giọng đọc AI tiếng Việt tự nhiên chuẩn studio (`VieNeu-TTS`).
     - Tải stock footage sắc nét từ kho media chất lượng cao.
     - Sinh phụ đề ASS karaoke đồng bộ thời gian từng từ.
     - Lồng nhạc nền nhẹ nhàng với cơ chế Audio Ducking (nhạc tự hạ 25% khi có lời thuyết minh).
     - Render video hoàn chỉnh MP4 qua ffmpeg.

#### Tùy Chọn 3B: Video Đồ Họa Chuyển Động & Infographic Chính Sách (Creative Studio 2.0)
1. **Chuẩn bị Storyboard v2.0:**
   - File JSON `<process_dir>/storyboard.json` với Brand Profile `chottoday`, gồm các phân cảnh Kinetic Typography, Number Counter (số liệu kiều bào, mức thuế, lương tối thiểu), Bar Chart so sánh và CTA Outro.
2. **Thực thi Storyboard Renderer:**
   ```python
   from creative import render_storyboard
   result = render_storyboard(
       storyboard="<process_dir>/storyboard.json",
       output_path="<output_dir>/video_media.mp4",
       run_qa=True
   )
   ```
   - Tự động kết xuất đồ họa chuyển động qua HyperFrames/Canvas, lồng tiếng thuyết minh, BGM và chạy kiểm định Visual QA 2.0 xuất `<output_dir>/video_media_contact_sheet.jpg` và `technical_report.json`.

---

## 🛡️ CỔNG KIỂM ĐỊNH KÉP BẮT BUỘC (Rule R3 §9)
- **Thẩm định Kỹ thuật:**
  - [ ] `claim_guard.py` đạt Exit Code 0 (0 vi phạm pháp lý).
  - [ ] File `bai_viet.docx` và `bai_viet.md` có đầy đủ nội dung.
  - [ ] File `video_media.mp4` tồn tại, dung lượng > 0, phát hình và tiếng chuẩn xác, phụ đề khớp lời đọc.
- **Thẩm định Trải nghiệm:**
  - [ ] Toàn bộ thành phẩm nằm gọn trong thư mục `<output_dir>/phong_media_<chu_de>/`.
  - [ ] Không xả file rác vào repository Git.

---

## 🏁 GIAO THỨC BÀN GIAO SẠCH (Clean Delivery)
- Báo cáo kết quả trên khung chat với:
  - Tóm tắt 3 điểm cốt lõi của sự kiện thời sự.
  - Đường dẫn tới từng file thành phẩm (`fact_pack.md`, `bai_viet.docx`, `video_media.mp4`).
  - Hướng dẫn nhanh cách phát hành hoặc đăng tải đa kênh.
