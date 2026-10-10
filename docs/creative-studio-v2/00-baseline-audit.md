# AIWF CREATIVE STUDIO 2.0 — BASELINE SYSTEM AUDIT

> **Mã tài liệu:** `docs/creative-studio-v2/00-baseline-audit.md`  
> **Giai đoạn:** Phase 0 — Discovery & Baseline Audit  
> **Thời điểm thẩm định:** 2026-10-10T08:08:00+09:00  
> **Trạng thái:** Hoàn tất kiểm tra hiện trạng (OBSERVED & VERIFIED)  
> **Nguyên tắc phân định:** Phân biệt minh bạch giữa **[OBSERVED FACT]**, **[TECHNICAL INFERENCE]**, và **[PROPOSED IMPROVEMENT]**.

---

## 1. TỔNG QUAN HIỆN TRẠNG REPOSITORY (OBSERVED FACTS)

* **Repository:** `https://github.com/bangluutru/ai-workforce.git`
* **Nhánh cơ sở (Baseline Branch):** `main`
* **Commit cơ sở (Baseline Commit SHA):** `7c989ea62df9816f73ab866fbcc38b9597e52eb8`
* **Tag điểm phục hồi (Recovery Tag):** `backup/creative-studio-v2-pre-upgrade` (trỏ chính xác vào `7c989ea62df9816f73ab866fbcc38b9597e52eb8`)
* **Nhánh phát triển độc lập (Feature Branch):** `feature/creative-studio-v2`
* **Trạng thái Working Tree:** Sạch (`working tree clean`), không có thay đổi dở dang trước khi phân nhánh.
* **Git Hooks:** `core.hooksPath = scripts/hooks` (đang kích hoạt `pre-commit` kiểm soát Luật R7 và `post-merge` tự đồng bộ extension).

---

## 2. MÔI TRƯỜNG THỰC THI & CÔNG CỤ NỀN TẢNG (OBSERVED FACTS)

* **Hệ điều hành:** macOS 15+ (`Darwin Kernel 25.6.0`, kiến trúc ARM64 Apple Silicon T6000).
* **Node.js:** `v22.23.1` (sẵn sàng hỗ trợ ES Modules, Top-Level Await, Worker Threads).
* **Python Runtime:** `Python 3.14.7` (hệ thống) kèm môi trường ảo `.venv/bin/python` tích hợp đầy đủ:
  - `numpy`: `2.5.2`
  - `Pillow (PIL)`: `12.3.0`
  - `librosa`: `1.0.0` (trong `.venv`, sẵn sàng cho audio onset/beat tracking)
* **FFmpeg / FFprobe:** `v9.0.1` (Apple clang 21.0.0), tích hợp đầy đủ các bộ lọc quan trọng:
  - `ass`: `True` (render phụ đề vector nâng cao)
  - `rubberband`: `True` (co giãn thời gian âm thanh giữ nguyên cao độ/formant)
  - `drawtext`: `True`
  - `scale`: `True`
  - `pad`: `True`
* **Trình duyệt phục vụ Render/Visual QA:** Google Chrome `v130+` tại `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` và Puppeteer-core `^25` trong `hand-drawn-animation/scripts/node_modules`.

---

## 3. KẾT QUẢ KIỂM THỬ CƠ SỞ (BASELINE TEST RESULTS)

Trước khi thực hiện bất kỳ thay đổi nào, toàn bộ bộ kiểm thử hiện có đã được kích hoạt:

```bash
pytest -q
```

* **Tổng số bài test thực thi:** 289 tests
* **Kết quả đạt:** 276 passed, 7 subtests passed
* **Tạm bỏ qua (Skipped):** 2 skipped
* **Lỗi phát hiện ở trạng thái cơ sở (Existing Baseline Failures & Errors):**
  1. `tests/test_mixed_complex_corpus.py`: 4 lỗi `ModuleNotFoundError: No module named 'skill_quality.document_reconstruction_translator'` do thiếu fixture PDF và trỏ nhầm module cũ (thuộc kỹ năng dịch thuật).
  2. `tests/test_adaptive_layout.py::test_20_real_corpus_verifier_usability`: Thất bại do ném ngoại lệ `SkipTest` tự định nghĩa thay vì `pytest.skip` khi thiếu file PDF thực tế trong `_process/`.
  3. `tests/test_real_document_acceptance.py::TestRealDocumentAcceptance::test_02_real_document_acceptance_d04`: Thất bại do thiếu file PDF kiểm thử `D04_complex_layout_ja.pdf`.
* **Kiểm tra Luật R7 (`python3 scripts/check_shared_reuse.py`):** Đạt chuẩn 100% (`✅ R7: không phát hiện trùng lặp / engine viết lại / engine bị cấm`).

---

## 4. TRẢ LỜI 10 CÂU HỎI THẨM ĐỊNH BẮT BUỘC (CODEBASE AUDIT QUESTIONS)

### 1. Những hàm/module hiện có nào đã hỗ trợ các tính năng được yêu cầu?
* **Xử lý âm thanh & Video hạ tầng:**
  - `_shared/media/ffmpeg_tools.py`: Tìm nhị phân `ffmpeg`/`ffprobe`, đọc/ghi WAV float32 numpy (`decode`, `encode`), đo thời lượng chính xác qua `ffprobe` (`duration`), đo độ lớn EBU R128 (`loudness`), kiểm tra bộ lọc (`has_filter`).
  - `_shared/media/tts.py`: VieNeu-TTS v3 Turbo (48 kHz, 25 giọng tiếng Việt chuẩn, nhân bản giọng) và Kokoro ONNX (33 giọng Anh/Mỹ/Nhật), chạy 100% offline.
  - `_shared/media/dub_engine.py`: Lồng tiếng studio có Whisper nghe lại round-trip (CER), tính toán khớp thời gian (`plan_fit`), co giãn tự nhiên qua `rubberband` (`render_fit`), trộn âm thanh ducking mượt mà (fade 150/350ms, chuẩn -16 LUFS, đỉnh -1.5 dBTP).
  - `_shared/media/ass_generator.py`: Trình biên dịch phụ đề ASS/SRT nâng cao, vẽ hộp bo góc vector Bezier (`make_rounded_rect_path`), đo kích thước chữ thực tế theo file font chuẩn trong `_shared/fonts`.
  - `_shared/media/linebreak.py`: Ngắt dòng cân bằng văn bản đa ngữ (Latin & CJK).
  - `_shared/media/semantic_segmenter.py`: Phân đoạn câu/mệnh đề theo ngữ nghĩa, chống câu mồ côi, giới hạn CPS.
  - `_shared/media/spoken_normalizer.py`: Chuẩn hóa văn bản phát thanh tiếng Việt (số, từ viết tắt, ký tự điều khiển).
  - `_shared/output_manager.py`: Định tuyến đường dẫn lưu trữ `<output_dir>` mặc định `~/Downloads/AIWF_Output/` chống xả rác vào repository (Anti-Repo Bloat).
* **Phân tích hình ảnh & Kiểm định thị giác (Visual QA):**
  - `hand-drawn-animation/scripts/qa.mjs`: Thuật toán đo lường thị giác khách quan trên từng khung hình (độ sáng, tỷ lệ pixel trống, biên độ thay đổi 1 khung vs 6 khung `step`/`step6` phát hiện đứng hình `dead-shot` hoặc rung giật `boil`, đo mật độ nét vẽ).
  - `hand-drawn-animation/scripts/verify.mjs`: Kiểm định tính tất định (seek invariance) và tính bảo toàn khung hình (format preservation).

### 2. Những năng lực nào thực sự còn thiếu (Genuinely Missing)?
1. **Storyboard & Scene Specification chuẩn hóa (v2.0 Schema):** Hiện tại `video-studio` chỉ dùng `video_script.json` đơn giản (chỉ có `id`, `vi`, `jp`, `keywords`), thiếu các thuộc tính phân cảnh chuyên nghiệp: bố cục hình học (`composition`), mục tiêu thị giác (`visual_goal`), chuyển động (`motion`), hiệu ứng chuyển cảnh (`transition`), cấu hình tỷ lệ khung hình (`aspect_ratio`), ngân sách thời gian chi tiết.
2. **Motion Director & Motion Parameters:** Thiếu một tầng điều phối chuyển động chuyên nghiệp (vị trí, tỷ lệ scale, góc xoay, độ mờ opacity, timing, easing curves, phân tầng layer, cường độ chuyển động `subtle`/`moderate`/`energetic`).
3. **Motion Graphics Renderer:** Hiện tại `video-studio` chỉ ghép video stock footage hoặc pan/zoom Ken Burns trên ảnh tĩnh. Không có khả năng tạo chuyển động đồ họa (Kinetic typography, animated bar charts, number counters, logo reveals, product spotlights).
4. **Visual QA 2.0 cho file video MP4 tổng quát:** `qa.mjs` hiện chỉ kiểm tra HTML Canvas; hệ thống thiếu một bộ công cụ trích xuất và thẩm định tự động khung hình (Frame Sampling, Contact Sheet, Text Overflow, Unsafe Margins, Missing Audio, Duration Drift) áp dụng cho video MP4 bất kỳ.
5. **Timeline đồng bộ đa nguồn (Audio-driven Motion Timeline):** Chưa có cơ chế tự động khớp các mốc chuyển động (motion cues) với nhịp giọng đọc thực tế hoặc beat nhạc nền.
6. **Hồ sơ Chuyển động Thương hiệu (Brand Motion Profile):** Chưa có cấu hình nhận diện chuyển động đồng bộ (bảng màu, font chữ, easing mặc định, vùng an toàn safe area).

### 3. Những thành phần nào an toàn để mở rộng?
* **Thư viện dùng chung `_shared/creative/` (Mới):** Tạo mới hoàn toàn module hạ tầng `_shared/creative/` bao gồm:
  - `storyboard_schema.py` & `storyboard_validator.py`
  - `brand_profile.py`
  - `motion_director.py`
  - `timeline_planner.py`
  - `render_router.py`
  - `qa/` (Frame sampler, technical validator, visual inspector, report builder)
  - `presets/` (Kho hiệu ứng chuyển động dùng chung)
* **Các file script bảo mật trong `video-studio/scripts/`:**
  - `beat_detector.py`: Sửa lỗi dùng hàm `eval()` để parse FPS.
  - `video_studio_server.py`: Giới hạn binding vào localhost, kiểm tra an toàn đường dẫn chống path traversal, hạn chế CORS.

### 4. Những giao diện (Interfaces) nào bắt buộc phải tương thích ngược 100%?
* **Kịch bản `video_script.json` cũ:** `video-studio/scripts/video_pipeline.py` vẫn phải nhận và render các file kịch bản cũ mà không bắt buộc người dùng chuyển đổi sang schema v2.0.
* **Workflow `W1-phong-media`:** Dây chuyền sản xuất tin tức và video đa phương tiện hiện tại vẫn phải chạy trơn tru với các tham số CLI hiện có.
* **Toàn bộ engine trong `_shared/media/`:** Không thay đổi chữ ký (signature) của các hàm đang được `phu-de`, `long-tieng`, `sach-noi`, `video-studio` sử dụng.
* **Skill `hand-drawn-animation`:** Hoạt động độc lập, không bị ảnh hưởng.

### 5. Những chức năng nào thuộc về `_shared/`?
* Toàn bộ các hợp đồng dữ liệu dùng chung (Storyboard schema, Brand profile schema).
* Động cơ tính toán chuyển động (Motion director, Easing math).
* Trình lập kế hoạch dòng thời gian (Timeline planner).
* Bộ định tuyến render (Render router) và lớp trừu tượng (Render adapter base).
* Bộ công cụ kiểm định thị giác tự động (Visual QA 2.0: sampler, metrics, contact sheet).
* Thư viện mẫu chuyển động dùng chung (Motion presets registry).

### 6. Những chức năng nào cần giữ riêng trong từng skill?
* Việc tìm kiếm tải stock media từ Pexels/Pixabay giữ trong `video-studio`.
* Giao diện UI Web của Video Studio giữ trong `video-studio/ui/`.
* Các shader nét vẽ nghệ thuật Canvas 2D (cels, roto, sand, paper3d) giữ trong `hand-drawn-animation`.

### 7. Những phụ thuộc nào đã được cài đặt sẵn?
* Python: `numpy`, `PIL`, `librosa` (trong `.venv`), `pytest`.
* Node.js: `puppeteer-core`, Chrome executable.
* CLI: `ffmpeg` và `ffprobe` (hỗ trợ `ass`, `rubberband`).
* Font chữ: Đầy đủ trong `_shared/fonts/`.

### 8. Những phụ thuộc nào sẽ cần cài đặt thêm?
* Bộ render đồ họa động HyperFrames (cần khảo sát tính khả thi ở Phase 3 trong môi trường sandbox cô lập, tuyệt đối không cài vào thư mục gốc của AIWF khi chưa thẩm định).

### 9. Những thay đổi nào có nguy cơ làm gãy hệ thống hiện tại (Regression Risks)?
* Nếu thay đổi cấu trúc tham số dòng lệnh của `video_pipeline.py` $\rightarrow$ gãy workflow `W1-phong-media`.
* Nếu vi phạm Luật R7 (nhân bản code hoặc engine giữa các thư mục) $\rightarrow$ bị git pre-commit hook chặn.
* Nếu đưa các file video thử nghiệm nặng vào Git repository $\rightarrow$ vi phạm Luật R0 và R1 (Anti-Repo Bloat).

### 10. Những thay đổi nào là KHÔNG CẦN THIẾT và BỊ TỪ CHỐI (Rejected Changes)?
* ❌ Viết lại toàn bộ `video_pipeline.py` từ đầu (vi phạm Section 3).
* ❌ Thay thế VieNeu-TTS / Kokoro bằng các Cloud API như OpenAI TTS / ElevenLabs (vi phạm Luật R4 và R7 về Zero-External-API).
* ❌ Viết lại engine âm thanh lồng tiếng `dub_engine.py`.
* ❌ Cài đặt toàn bộ 25 motion presets ngay từ đầu mà không kiểm thử chất lượng (Section 13 yêu cầu bắt đầu bằng 10 presets chuẩn).

---

## 5. KẾT LUẬN THẨM ĐỊNH GIAI ĐOẠN 0 (AUDIT CONCLUSION)

Hệ thống AIWF hiện tại sở hữu nền tảng âm thanh, phụ đề và ffmpeg rất vững chắc. Việc nâng cấp lên Creative Studio 2.0 là **hoàn toàn khả thi** thông qua chiến lược tiếp cận vi phẫu (surgical micro-diffs), bảo toàn 100% các pipeline hiện có, thiết lập cờ tắt/mở (`creative_studio_v2.enabled = false`) và bổ sung tầng đồ họa chuyển động `_shared/creative/` tách bạch.
