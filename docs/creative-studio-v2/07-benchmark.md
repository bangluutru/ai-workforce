# BÁO CÁO ĐO LƯỜNG HIỆU NĂNG & BENCHMARK THỰC TẾ (BENCHMARK REPORT)
## AIWF Creative Studio 2.0 — Số Liệu Đo Lường Runtime & Phân Tích Thực Nghiệm

> **Tài liệu:** `docs/creative-studio-v2/07-benchmark.md`  
> **Phiên bản:** 2.0 (Hardened & Factual Benchmark)  
> **Nguyên tắc báo cáo:** Không suy diễn, không ngụy tạo số liệu so sánh.  
> **Môi trường đo lường:** Apple Silicon Mac (Metal GPU Acceleration), 16GB RAM, macOS 15, Python 3.14, FFmpeg 7.1, Headless Chromium 133

---

## 1. PHÂN LOẠI NGUỒN SỐ LIỆU (DATA TAXONOMY)

- **[OBSERVED]**: Số liệu đo lường trực tiếp từ đồng hồ bấm giờ runtime hoặc log hệ điều hành.
- **[TESTED]**: Số liệu thu được từ việc chạy thành công bộ kịch bản kiểm thử tự động.
- **[ESTIMATED]**: Ước lượng dựa trên giả định vận hành thông thường, chưa kiểm chứng bằng thực nghiệm đối chứng trong phòng thí nghiệm.
- **[NOT VERIFIED]**: Chỉ số chưa có phương pháp đo lường độc lập lặp lại được (reproducible measurement).

---

## 2. KẾT QUẢ ĐO LƯỜNG KẾT XUẤT 3 DỰ ÁN PILOT [OBSERVED]

Dữ liệu dưới đây được đo lường trực tiếp từ lệnh thực thi kịch bản `scripts/run_pilot_projects.py` trên môi trường thực tế:

| Dự án thử nghiệm | Tỷ lệ | Độ phân giải | Số cảnh | Thời lượng | Số frame | Thời gian render thực tế [OBSERVED] | Tốc độ trung bình (FPS) [DERIVED] | Điểm Visual QA | Kết quả kiểm tra |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Pilot A: ChottoDay Bản Tin** | 1:1 | $1080 \times 1080$ | 4 cảnh | 13.0s | 390 frames | **32.19 giây** | 12.11 FPS | 95/100 (WARN: độ sáng nền đậm) | ✅ PASS |
| **Pilot B: Balancera Giới Thiệu** | 16:9 | $1920 \times 1080$ | 4 cảnh | 15.0s | 450 frames | **27.17 giây** | 16.56 FPS | 95/100 (WARN: độ sáng nền đậm) | ✅ PASS |
| **Pilot C: KPI Infographic** | 1:1 | $1080 \times 1080$ | 4 cảnh | 14.0s | 420 frames | **30.92 giây** | 13.58 FPS | 95/100 (WARN: độ sáng nền đậm) | ✅ PASS |
| **Canvas 2D Fallback Engine** | 1:1 | $1080 \times 1080$ | 1 cảnh | 3.0s | 90 frames | **1.52 giây** | 59.21 FPS | 100/100 | ✅ PASS |

### Ghi chú phân tích dữ liệu quan sát:
1. **Tốc độ GPU HyperFrames [OBSERVED]:** Tốc độ render trên GPU Metal dao động từ **12.1 đến 16.6 FPS** (khoảng 1.8 đến 2.5 giây thực tế cho 1 giây video Full HD).
2. **Tốc độ Canvas Fallback [OBSERVED]:** Khi fallback sang Canvas/FFmpeg direct, tốc độ đạt **59.2 FPS** (nhanh hơn thời gian thực gần 2 lần) nhưng chất lượng đồ họa và hiệu ứng chuyển động bị giới hạn so với HTML5/GSAP.
3. **Cảnh báo độ sáng Visual QA [OBSERVED]:** Cả 3 video pilot đều nhận cờ cảnh báo `WARN` về độ sáng trung bình (do thiết kế sử dụng tông nền màu đậm như đỏ trầm `#8B0000` hoặc xám đậm `#0D1117`). Không phát hiện lỗi nghiêm trọng nào về khung hình đen (`BLACK_FRAME`), đứng hình (`FROZEN_FRAME`) hay mất tiếng (`AUDIO_MISSING`).

---

## 3. BẢNG SO SÁNH ĐỐI CHỨNG GIỮA CÁC PHIÊN BẢN (DE-BIASED COMPARISON)

> ⚠️ **Lưu ý kỷ luật báo cáo:** Bảng dưới đây phân tách rạch ròi giữa số liệu đo đạc thực tế và các ước lượng định tính. Mọi so sánh chưa qua đo lường đối chứng phòng thí nghiệm đều được đánh dấu `[ESTIMATED]` hoặc `[NOT VERIFIED]`.

| Tiêu chí so sánh | Video Studio v1.0 | Creative Studio v2.0 | Cơ sở bằng chứng |
|---|---|---|:---:|
| **Phụ thuộc tài nguyên mạng khi render** | Cần kết nối internet để tải video stock | 0 request mạng trong quá trình render (100% offline) | [OBSERVED] Đã kiểm chứng qua biến `DO_NOT_TRACK=1` và ngắt mạng cục bộ |
| **Thời gian chờ tải tài nguyên mạng** | Dao động tùy băng thông mạng (ước tính 30s — 120s) | 0.0 giây chờ tải tài nguyên | [ESTIMATED] Thời gian mạng của v1 chỉ là ước lượng, không phải hằng số đo lường |
| **Tính tất định của thuật toán chuyển động** | Phụ thuộc ngẫu nhiên vào kết quả tìm kiếm stock | PRNG Seed đảm bảo thông số chuyển động toán học nhất quán | [TESTED] đối với thuật toán PRNG; [NOT VERIFIED] đối với rasterization trên các GPU khác nhau |
| **Độ chính xác cắt khung hình** | Cắt video theo timestamp phụ đề của ffmpeg | Khung hình được xuất ở tần số cố định 30 FPS (khoảng 33.3ms/frame) | [DERIVED] Tính toán dựa trên thông số khung hình cố định; [NOT VERIFIED] cho độ trễ âm thanh thực tế |
| **Phạm vi kiểm định tự động** | Không có bộ kiểm tra thị giác tự động | Kiểm tra 5 class thị giác (đen, đứng hình, âm thanh, lề an toàn) + 5 class DOM layout | [TESTED] Kiểm tra đúng các class lỗi định sẵn, KHÔNG phát hiện mọi lỗi thị giác |
| **Số lượng presets đồ họa chuyển động** | 0 preset chuyển động | 10 presets HTML/CSS/GSAP | [OBSERVED] 10 file templates đã được tạo và test |
| **Thời gian chạy bộ test suite tự động** | Chưa có bộ test chuyên dụng | 116 bài kiểm thử chạy trong ~3.4 giây | [OBSERVED] Đo lường từ lệnh `pytest tests/creative/` |

---

## 4. ĐO LƯỜNG TÀI NGUYÊN HỆ THỐNG [OBSERVED]

- **Bộ nhớ RAM của tiến trình Headless Chrome:** Mức tiêu thụ RAM đỉnh điểm (Peak RSS) ghi nhận được là **420MB — 480MB** trong quá trình capture khung hình.
- **Tải CPU trung bình:** Dao động từ **60% đến 80%** trong thời gian render song song, sau đó giải phóng hoàn toàn khi hoàn tất.
- **Tiến trình FFmpeg:** Ghép nối clip và multiplexing âm thanh hoàn thành trong **1.2s đến 1.8s**.
- **Tác động lên kho mã nguồn Git:** **0 bytes** file nhị phân phát sinh trong repository (toàn bộ dữ liệu tạm nằm trong `_process/` được gitignore).

---

## 5. KẾT LUẬN BENCHMARK [SELF-REVIEWED]

1. Các số liệu đo lường runtime khẳng định hệ thống có khả năng kết xuất đồ họa chuyển động trên máy Apple Silicon với tốc độ thực tế từ 12 đến 16 FPS.
2. Bộ điều hợp dự phòng Canvas 2D hoàn thành nhiệm vụ cứu cánh với tốc độ cao (~60 FPS) khi môi trường không có GPU.
3. Không duy trì bất kỳ tuyên bố phóng đại nào (như "chính xác hơn 15 lần", "tuyệt đối 100%", hay "chuẩn công nghiệp") khi chưa có đủ dữ liệu kiểm nghiệm đối chứng độc lập.
