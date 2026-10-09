# AIWF CREATIVE STUDIO 2.0 — KẾ HOẠCH TRIỂN KHAI NÂNG CẤP CHI TIẾT

> **Mã tài liệu:** `docs/creative-studio-v2/03-implementation-plan.md`  
> **Giai đoạn:** Phase 0 — Implementation Roadmap & Execution Plan  
> **Phiên bản:** v1.0  
> **Chiến lược:** Incremental Small-Batches, Evidence-Driven, Checkpoint Gated

---

## 1. NGUYÊN TẮC THI HÀNH & KỶ LUẬT THỰC HIỆN

1. **Thực thi theo từng lô nhỏ (Small-Batch Cycles):** Mỗi giai đoạn (Phase) được chia thành các nhát cắt nhỏ, có bài kiểm thử riêng biệt và điểm kiểm tra (Checkpoint commit).
2. **Tuân thủ quy định dừng ngay (Immediate Stop Triggers):** Nếu phát hiện nguy cơ ghi đè dữ liệu người dùng, gãy pipeline cũ, hoặc HyperFrames không ổn định $\rightarrow$ Dừng lại, báo cáo theo đúng định dạng `STOP CONDITION`.
3. **Chờ sự phê duyệt của Người dùng (User Approval Gate):** Hoàn tất toàn bộ tài liệu Phase 0 $\rightarrow$ Trình bày cho Người dùng $\rightarrow$ CHỈ BẮT ĐẦU Phase 1 khi có sự chấp thuận rõ ràng từ Người dùng.

---

## 2. LỘ TRÌNH 8 GIAI ĐOẠN (PHASES 0 ĐẾN 7)

```
[Phase 0: Baseline & Safety] ──(GATE 0: USER APPROVAL)──┐
                                                        ▼
[Phase 1: Creative Contracts] ──(CP1 Checkpoint)
       │
       ▼
[Phase 2: Motion Director & Security Hardening] ──(CP2 Checkpoint)
       │
       ▼
[Phase 3: HyperFrames POC & Feasibility Gate] ──(CP3 Checkpoint)
       │
       ▼
[Phase 4: Render Adapter & 10 Motion Presets] ──(CP4 Checkpoint)
       │
       ▼
[Phase 5: Visual QA 2.0 & Defect Detection] ──(CP5 Checkpoint)
       │
       ▼
[Phase 6: Skill & Workflow Integration] ──(CP6 Checkpoint)
       │
       ▼
[Phase 7: Dual Reviews, Benchmarks & Final Release Decision] ──(CP7 Checkpoint)
```

---

## 3. CHI TIẾT CÁC GIAI ĐOẠN & THAY ĐỔI CẤP FILE (FILE-LEVEL PROPOSALS)

---

### GIAI ĐOẠN 0 — THẨM ĐỊNH CƠ SỞ & AN TOÀN (PHASE 0: BASELINE & SAFETY)
* **Trạng thái:** ĐANG HOÀN TẤT.
* **Nhiệm vụ:**
  1. Kiểm tra trạng thái Git, nhánh, commit, tag, hooks.
  2. Tạo tag phục hồi `backup/creative-studio-v2-pre-upgrade` trỏ vào `7c989ea`.
  3. Tạo nhánh phát triển `feature/creative-studio-v2`.
  4. Lưu recovery manifest ra bên ngoài repository Git.
  5. Chạy test suite cơ sở (`pytest -q`), ghi nhận các lỗi hiện hữu.
  6. Soạn thảo 5 tài liệu kỹ thuật nền tảng trong `docs/creative-studio-v2/`.
* **Cổng Gate 0:** Người dùng phê duyệt kế hoạch trước khi viết code mới.

---

### GIAI ĐOẠN 1 — HỢP ĐỒNG DỮ LIỆU SÁNG TẠO (PHASE 1: CREATIVE CONTRACTS)
* **Mục tiêu:** Xây dựng tầng định nghĩa dữ liệu phân cảnh, hồ sơ thương hiệu và bộ chuyển đổi tương thích ngược.
* **Các file tạo mới / sửa đổi:**
  1. `.agents/skills/_shared/creative/__init__.py`
  2. `.agents/skills/_shared/creative/storyboard_schema.py`:
     - Khai báo JSON Schema v2.0 cho Storyboard.
     - Hàm `validate_storyboard(data: dict) -> Tuple[bool, List[str]]`.
  3. `.agents/skills/_shared/creative/brand_profile.py`:
     - Khai báo cấu trúc Brand Motion Profile (colors, fonts, easing, safe_area).
     - Hàm `load_brand_profile(name: str) -> dict`.
  4. `.agents/skills/_shared/creative/legacy_adapter.py`:
     - Chuyển đổi từ `video_script.json` (v1) sang `storyboard_v2.json` mà không làm thay đổi ngữ nghĩa.
* **Bộ test kiểm chứng (`tests/creative/`):**
  - `test_storyboard.py`: Kiểm thử schema hợp lệ, schema thiếu trường bắt buộc, thời lượng âm, tỷ lệ khung hình không hỗ trợ, chuyển đổi từ script cũ.
* **Cổng Gate 1:** Toàn bộ test của `test_storyboard.py` đạt 100%, pipeline Video Studio cũ không bị ảnh hưởng.

---

### GIAI ĐOẠN 2 — ĐIỀU PHỐI CHUYỂN ĐỘNG & VÁ BẢO MẬT (PHASE 2: MOTION DIRECTOR & SECURITY HARDENING)
* **Mục tiêu:** Xây dựng bộ tính toán tham số chuyển động tất định và vá dứt điểm 2 lỗ hổng bảo mật đã phát hiện.
* **Các file tạo mới / sửa đổi:**
  1. `.agents/skills/_shared/creative/motion_director.py`:
     - Tính toán nội suy toạ độ, tỷ lệ, xoay, độ mờ theo hàm Easing (`linear`, `ease_in`, `ease_out`, `ease_in_out`, `cubic_bezier`).
     - Quy đổi cường độ chuyển động (`subtle`, `moderate`, `energetic`).
     - Bảo đảm tính tất định bằng hàm PRNG có seed.
  2. `.agents/skills/_shared/creative/timeline_planner.py`:
     - Lập lịch các sự kiện chuyển động (Motion Cues) đồng bộ với nhịp audio và ranh giới phân cảnh.
  3. **Vá bảo mật Issue A trong `video-studio/scripts/beat_detector.py`:**
     - Thay thế `eval(stream.get("r_frame_rate", "30/1"))` bằng hàm bóc tách phân số an toàn `Fraction(r_frame_rate)`.
     - Thay thế `tempfile.mktemp()` bằng `tempfile.NamedTemporaryFile()`.
  4. **Vá bảo mật Issue B trong `video-studio/scripts/video_studio_server.py`:**
     - Giới hạn binding vào `127.0.0.1`.
     - Thẩm định đường dẫn nghiêm ngặt trong `serve_media()`: kiểm tra path traversal (`..`), chỉ cho phép các thư mục được phê duyệt (Downloads, output_dir, workspace process).
     - Giới hạn CORS domain.
* **Bộ test kiểm chứng:**
  - `test_timeline.py`: Kiểm thử thứ tự sự kiện, chồng đè chuyển cảnh, tính tất định khi chạy lại nhiều lần.
  - `test_security.py`: Thử nghiệm payload độc hại vào `beat_detector.py` và traversal attack vào `video_studio_server.py`.
* **Cổng Gate 2:** Toàn bộ test toán học và kiểm thử bảo mật đạt 100%.

---

### GIAI ĐOẠN 3 — THỬ NGHIỆM THỰC THI HYPERFRAMES (PHASE 3: HYPERFRAMES POC)
* **Mục tiêu:** Đánh giá thực nghiệm khả năng render của HyperFrames trên môi trường sandbox tách biệt.
* **Khu vực thực thi:** `_process/hyperframes_sandbox/` (tuyệt đối không cài vào root).
* **Nhiệm vụ:**
  1. Khởi tạo dự án thử nghiệm với lockfile cố định.
  2. Chạy render 3 kịch bản kiểm chứng độc lập:
     - **POC A:** Motion Typography (10s, 1:1, 30fps).
     - **POC B:** Product Showcase (15s, 16:9, 30fps).
     - **POC C:** Data Animation (15s, 9:16, 30fps).
  3. Đo lường: Thời gian render, mức tiêu thụ RAM đỉnh, dung lượng file đầu ra, tính toàn vẹn qua `ffprobe`.
  4. Thẩm định thị giác trên từng khung hình trích xuất.
* **Cổng Gate 3 (Feasibility Decision):**
  - NẾU render ổn định, chất lượng hình ảnh sắc nét, tài nguyên hợp lý $\rightarrow$ Tiếp tục Phase 4.
  - NẾU thất bại hoặc thiếu ổn định $\rightarrow$ Kích hoạt phương án dự phòng (Canvas 2D Adapter), không cố chấp ép buộc.

---

### GIAI ĐOẠN 4 — BỘ KẾT XUẤT ADAPTER & KHO 10 MOTION PRESETS (PHASE 4: RENDER ADAPTER & PRESETS)
* **Mục tiêu:** Tách rời logic điều phối khỏi engine render và cung cấp 10 mẫu chuyển động chuẩn mực.
* **Các file tạo mới / sửa đổi:**
  1. `.agents/skills/_shared/creative/renderers/base.py`: Lớp trừu tượng `BaseRenderAdapter`.
  2. `.agents/skills/_shared/creative/renderers/hyperframes_adapter.py` (hoặc `canvas_adapter.py`).
  3. `.agents/skills/_shared/creative/render_router.py`: Bộ định tuyến chọn adapter dựa trên loại phân cảnh.
  4. `.agents/skills/_shared/creative/presets/`: 10 mẫu chuyển động cốt lõi:
     - `01_fade_in`
     - `02_slide_reveal`
     - `03_scale_pop`
     - `04_kinetic_title`
     - `05_number_counter`
     - `06_logo_reveal`
     - `07_product_spotlight`
     - `08_feature_card`
     - `09_bar_chart`
     - `10_cta_reveal`
  5. Cập nhật `.agents/skills/_shared/engines.json` đăng ký module mới tuân thủ **Luật R7**.
* **Bộ test kiểm chứng:**
  - `test_render_router.py`: Kiểm thử chuyển tiếp render, xử lý timeout, xử lý lỗi render an toàn không đè file cũ.
  - `test_presets.py`: Kiểm thử hợp đồng tham số của 10 presets trên cả 3 tỷ lệ khung hình (1:1, 16:9, 9:16).
* **Cổng Gate 4:** 10 presets render ra video mẫu hợp lệ.

---

### GIAI ĐOẠN 5 — HỆ THỐNG KIỂM ĐỊNH THỊ GIÁC 2.0 (PHASE 5: VISUAL QA 2.0)
* **Mục tiêu:** Xây dựng cỗ máy kiểm toán thị giác khách quan cho file video thành phẩm.
* **Các file tạo mới / sửa đổi:**
  1. `.agents/skills/_shared/creative/qa/frame_sampler.py`: Trích xuất thông minh các khung hình chính (đầu cảnh, giữa cảnh, cuối cảnh, điểm chuyển cảnh).
  2. `.agents/skills/_shared/creative/qa/technical_validator.py`: Kiểm tra codec, độ dài, độ lớn âm thanh, đồng bộ audio-video.
  3. `.agents/skills/_shared/creative/qa/visual_inspector.py`: Tái sử dụng thuật toán từ `hand-drawn-animation/scripts/qa.mjs` (độ sáng, cảnh trống, chuyển động tối thiểu, tràn lề an toàn).
  4. `.agents/skills/_shared/creative/qa/contact_sheet.py`: Ghép các khung hình trích xuất thành bức ảnh tiếp xúc tổng thể (`contact_sheet.jpg`).
  5. `.agents/skills/_shared/creative/qa/report_builder.py`: Xuất báo cáo cấu trúc `technical_report.json` và bảng khuyến nghị sửa chữa.
* **Bộ test kiểm chứng (`test_visual_qa.py`):**
  - Đưa các video cố tình tạo lỗi (video đen, video đứng hình, video mất tiếng, video lệch tỷ lệ) và kiểm chứng hệ thống phát hiện chính xác 100% lỗi.
* **Cổng Gate 5:** Bộ QA bắt trọn các lỗi kỹ thuật định sẵn mà không phát sinh cảnh báo giả (false positives) phi lý.

---

### GIAI ĐOẠN 6 — TÍCH HỢP SKILL & WORKFLOW (PHASE 6: WORKFLOW INTEGRATION)
* **Mục tiêu:** Kết nối năng lực đồ họa chuyển động vào `video-studio`, `hand-drawn-animation` và workflow `W1-phong-media`.
* **Các file tạo mới / sửa đổi:**
  1. `.agents/skills/video-studio/SKILL.md`: Cập nhật tài liệu kỹ năng, hướng dẫn sử dụng kịch bản phân cảnh v2.0 và cờ tính năng.
  2. `.agents/skills/video-studio/references/creative-studio-v2.md`: Sổ tay hướng dẫn chi tiết cách viết storyboard.
  3. `.agents/workflows/W1-phong-media.md`: Bổ sung tùy chọn sản xuất video đồ họa chuyển động bên cạnh stock footage truyền thống.
  4. Cập nhật `scripts/audit_skill.py` và `scripts/check_shared_reuse.py` để bảo đảm toàn bộ skill đạt chứng chỉ Rule R4 ($\ge 85/100$) và 0 vi phạm Rule R7.
* **Cổng Gate 6:** Chạy thử nghiệm thành công 3 dự án thực tế:
  - Dự án A: Video giới thiệu ChottoDay (1:1, 60s, tiếng Việt).
  - Dự án B: Video sản phẩm Balancera (16:9, 30s, tiếng Nhật).
  - Dự án C: Video Infographic số liệu (9:16, 30s, tiếng Việt).

---

### GIAI ĐOẠN 7 — NGHIỆM THU KÉP, BENCHMARK & QUYẾT ĐỊNH PHÁT HÀNH (PHASE 7: FINAL ACCEPTANCE)
* **Nhiệm vụ:**
  1. Lập báo cáo thẩm định kỹ thuật (`05-technical-review.md`).
  2. Lập báo cáo trải nghiệm người dùng (`06-ux-review.md`).
  3. Đo lường bảng so sánh hiệu năng trước và sau nâng cấp (`07-benchmark.md`).
  4. Diễn tập quy trình phục hồi hoàn nguyên (`08-rollback.md`).
  5. Lập báo cáo tổng kết (`09-release-report.md`).
* **Trạng thái phát hành đề xuất:** Giữ nguyên `creative_studio_v2.enabled = false` (Opt-in) cho đến khi người dùng quyết định bật chính thức.

---

## 4. CHIẾN LƯỢC ĐIỂM KIỂM TRA (CHECKPOINT STRATEGY)

| Checkpoint | Thời điểm | Điều kiện kích hoạt commit | Ghi chú an toàn |
|:---:|---|---|---|
| **CP0** | Hoàn tất Phase 0 | 5 tài liệu cơ sở hoàn chỉnh, baseline tag đã tạo | Không chứa code thay đổi |
| **CP1** | Hoàn tất Phase 1 | `test_storyboard.py` đạt 100% | Chỉ chứa schemas & adapters |
| **CP2** | Hoàn tất Phase 2 | Vá lỗi bảo mật `beat_detector` & `server`, test timeline pass | Không đổi giao diện ngoài |
| **CP3** | Hoàn tất Phase 3 | 3 video POC render thành công trong sandbox | File video lưu ngoài git |
| **CP4** | Hoàn tất Phase 4 | Adapter và 10 presets pass kiểm thử | Đăng ký `engines.json` |
| **CP5** | Hoàn tất Phase 5 | Visual QA phát hiện đúng các video lỗi | Tái sử dụng thuật toán QA |
| **CP6** | Hoàn tất Phase 6 | 3 dự án thử nghiệm thực tế render đạt chuẩn | Audit skill $\ge 85/100$ |
| **CP7** | Nghiệm thu cuối | Technical & UX reviews hoàn tất | Sẵn sàng chờ lệnh kích hoạt |
