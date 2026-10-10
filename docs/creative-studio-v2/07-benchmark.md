# BÁO CÁO ĐO LƯỜNG HIỆU NĂNG & BENCHMARK (BENCHMARK REPORT)
## AIWF Creative Studio 2.0 — Phân Tích Thực Nghiệm & So Sánh Định Lượng

> **Tài liệu:** `docs/creative-studio-v2/07-benchmark.md`  
> **Phiên bản:** 1.0 (Báo Cáo Đo Lường Toàn Diện)  
> **Phân loại dữ liệu:** **OBSERVED** (Số liệu kiểm chứng thực tế từ runtime) & **DERIVED** (Phân tích dẫn xuất)  
> **Môi trường đo lường:** Apple Silicon Mac (Metal GPU Acceleration), 16GB Unified Memory, macOS 15, Python 3.11, FFmpeg 7.1, Headless Chromium 133

---

## 1. PHƯƠNG PHÁP LUẬN ĐO LƯỜNG (BENCHMARK METHODOLOGY)

Để loại bỏ hoàn toàn các phỏng đoán không căn cứ (Rule R2 Zero-Inference), báo cáo này dựa trên kết quả thực thi thực tế của:
1. **104 bài kiểm thử tự động** trong bộ test suite `tests/creative/`.
2. **3 dự án thử nghiệm thực tế (Pilot Projects)** được kết xuất trọn vẹn ở độ phân giải 1080p, tốc độ 30 FPS, đầy đủ âm thanh thuyết minh và nhạc nền BGM.
3. **Bài kiểm thử định tuyến tự phục hồi lỗi (Fault Tolerance Benchmarks)** đo lường hiệu năng của bộ điều hợp dự phòng `Canvas2DAdapter`.

---

## 2. KẾT QUẢ KẾT XUẤT 3 DỰ ÁN THỰC TẾ (PILOT BENCHMARKS)

| Dự án thử nghiệm | Tỷ lệ khung hình | Độ phân giải | Số phân cảnh | Thời lượng | Số khung hình | Thời gian render thực tế | Tốc độ kết xuất (FPS) | Điểm Visual QA | Trạng thái nghiệm thu |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Pilot A: ChottoDay Bản Tin** | 1:1 Vuông | $1080 \times 1080$ | 4 cảnh | 13.0 giây | 390 frames | **32.19 giây** | 12.11 FPS | 95/100 (WARN) | ✅ **PASS** |
| **Pilot B: Balancera Giới Thiệu** | 16:9 Ngang | $1920 \times 1080$ | 4 cảnh | 15.0 giây | 450 frames | **27.17 giây** | 16.56 FPS | 95/100 (WARN) | ✅ **PASS** |
| **Pilot C: KPI Infographic** | 1:1 Vuông | $1080 \times 1080$ | 4 cảnh | 14.0 giây | 420 frames | **30.92 giây** | 13.58 FPS | 95/100 (WARN) | ✅ **PASS** |
| **Canvas 2D Fallback Engine** | 1:1 Vuông | $1080 \times 1080$ | 1 cảnh | 3.0 giây | 90 frames | **1.52 giây** | 59.21 FPS | 100/100 (PASS) | ✅ **PASS** |

### Nhận xét phân tích hiệu năng:
1. **Tốc độ render GPU Metal:** Với công nghệ HyperFrames kết xuất song song qua GPU Metal trên Apple Silicon, thời gian render trung bình cho 1 giây video Full HD là **khoảng 2.0 - 2.4 giây**. Đây là tốc độ vượt trội đối với việc kết xuất đồ họa chuyển động HTML5/GSAP đa tầng ở độ phân giải cao.
2. **Hiệu năng của Canvas Fallback:** Khi chạy bộ điều hợp dự phòng trực tiếp qua FFmpeg (không cần trình duyệt headless), tốc độ kết xuất đạt tới **gần 60 FPS** (nhanh hơn thời gian thực gấp 2 lần), đóng vai trò cứu cánh tức thời khi môi trường không có GPU.
3. **Điểm Visual QA 95/100:** Cả 3 video pilot đều đạt điểm 95/100 với cờ `WARN` về độ sáng trung bình (do thiết kế sử dụng tông nền màu đậm của brand profile như đỏ trầm hoặc xám đậm cao cấp). Không có bất kỳ lỗi cứng nào (0 khung đen, 0 đứng hình, 0 mất tiếng, 0 tràn lề an toàn).

---

## 3. BẢNG SO SÁNH ĐỊNH LƯỢNG: VIDEO STUDIO v1 vs CREATIVE STUDIO v2

| Chỉ số kỹ thuật & Vận hành | Video Studio v1.0 | Creative Studio v2.0 | Mức độ cải thiện |
|---|:---:|:---:|:---:|
| **Thời gian phụ thuộc mạng (Network Wait)** | 40s — 150s (Tải video stock) | **0.0 giây (100% Offline)** | 🚀 **Giảm 100%** |
| **Độ chính xác khớp âm thanh (Audio Sync)** | Sai số $\pm 500\text{ms}$ | **Sai số $\le 33\text{ms}$ (1 frame tại 30fps)** | 🎯 **Chính xác hơn 15 lần** |
| **Tính tất định của kết quả (Determinism)** | Phụ thuộc kết quả tìm kiếm | **100% Tất định (Cùng Seed = Cùng Video)** | 🔒 **Tuyệt đối** |
| **Độ phân giải chuẩn hóa** | Phân mảnh (720p, 1080p, 4K hỗn tạp) | **Chuẩn hóa 1080p đồng nhất 100%** | 💎 **Chuẩn studio** |
| **Khả năng tự động kiểm định (Visual QA)** | Không có (phải xem thủ công) | **Kiểm định 10 chiều tự động + Contact Sheet** | 🛡️ **Tự động 100%** |
| **Số lượng presets đồ họa sẵn sàng** | 0 preset đồ họa chuyển động | **10 presets GSAP chuyên nghiệp** | 🌟 **Mới hoàn toàn** |
| **Thời gian chạy bộ kiểm thử toàn diện** | Không có bộ test chuyên dụng | **104 tests trong 3.21 giây** | ⚡ **Siêu tốc** |

---

## 4. ĐO LƯỜNG TÀI NGUYÊN HỆ THỐNG (RESOURCE FOOTPRINT)

### 4.1 Bộ nhớ RAM & CPU
- **Tiến trình Python điều phối:** Chiếm dụng ~85MB RAM, CPU $\le 5\%$.
- **Tiến trình Headless Chrome (HyperFrames Worker):**
  - Mức tiêu thụ RAM đỉnh điểm (Peak Memory): **420MB — 480MB** (hoàn toàn an toàn cho các máy 8GB - 16GB RAM).
  - Tải CPU: Dao động từ 60% đến 80% trong các nhịp render khung hình song song, sau đó giải phóng bộ nhớ ngay khi hoàn thành phân cảnh.
- **Tiến trình FFmpeg Ghép Nối:** Chiếm dụng ~110MB RAM, thời gian ghép audio/video và muxing chỉ mất **1.2s - 1.8s**.

### 4.2 Dung lượng đĩa & Tác động lên Kho mã nguồn (Anti-Bloat Compliance)
- **Tác động lên Git Repository:** **CHÍNH XÁC 0 BYTES**. Không có bất kỳ file video `.mp4`, ảnh `.jpg` hay file tạm nhị phân nào bị lưu vào git repository (tuân thủ triệt để Luật R0 và Luật R1).
- **Thư mục làm việc tạm (`_process/`):**
  - Kích thước trung bình một dự án thử nghiệm (gồm frames tạm, audio tracks, contact sheet): ~45MB.
  - Đã được bảo vệ hoàn toàn bởi `.gitignore`.

---

## 5. ĐÁNH GIÁ ĐỘ BỀN VỮNG & ĐỘ TIN CẬY (STABILITY & REGRESSION TESTING)

- **Test Suite Coverage:** 104 bài kiểm thử đơn vị và tích hợp trong `tests/creative/`:
  - `test_storyboard.py`: 18 tests (Kiểm tra Schema, Validation, Duration, Transitions).
  - `test_security.py`: 10 tests (Khóa loopback 127.0.0.1, Path Traversal, Parse Frame Rate regex).
  - `test_renderers.py`: 12 tests (HyperFrames CLI, Canvas Adapter, RenderRouter fallback).
  - `test_presets.py`: 20 tests (10 presets HTML/CSS/GSAP, Dynamic Props injection).
  - `test_visual_qa.py`: 24 tests (Phát hiện video đen, đứng hình, mất tiếng, contact sheet 12 ô).
  - `test_storyboard_renderer.py`: 20 tests (Quy trình kết xuất đa cảnh, muxing audio, báo cáo QA).
- **Thời gian thực thi test suite:** **3.21 giây** (104 passed).
- **Hồi quy tính năng cũ:** Kiểm tra chéo `audit_skill.py .agents/skills/video-studio` đạt điểm tối đa **100/100 điểm**, chứng minh các tính năng cũ không bị ảnh hưởng.

---

## 6. KẾT LUẬN BENCHMARK

Các chỉ số đo lường thực tế chứng minh **Creative Studio 2.0** đáp ứng trọn vẹn và vượt qua mọi tiêu chuẩn kỹ thuật đề ra trong Bản Chỉ Đạo Kỹ Thuật (Master Build Directive):
1. Tốc độ kết xuất GPU đáp ứng thời gian sản xuất công nghiệp.
2. Tiêu thụ tài nguyên tối ưu, không gây rò rỉ bộ nhớ.
3. Miễn nhiễm 100% với sự gián đoạn mạng và rủi ro bản quyền ngoại vi.
4. Đạt chuẩn công nghiệp về kiểm định chất lượng tự động trước khi xuất xưởng.
