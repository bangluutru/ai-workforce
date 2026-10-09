# AIWF CREATIVE STUDIO 2.0 — ĐÁNH GIÁ PHỤ THUỘC & TÍNH KHẢ THI CỦA BỘ RENDER

> **Mã tài liệu:** `docs/creative-studio-v2/02-dependency-review.md`  
> **Giai đoạn:** Phase 0 — Dependency Review & Feasibility Study  
> **Đối tượng thẩm định:** Ứng viên Render Đồ họa Chuyển động `hyperframes` (HeyGen) & Các giải pháp thay thế  
> **Thời điểm thẩm định:** 2026-10-10T08:08:45+09:00  
> **Chính sách Phase 0:** Tuyệt đối KHÔNG cài đặt HyperFrames vào môi trường gốc trong Phase 0.

---

## 1. TỔNG QUAN ỨNG VIÊN: HYPERFRAMES (HEYGEN)

* **Repository:** `https://github.com/heygen-com/hyperframes`
* **Trang tài liệu:** `https://hyperframes.heygen.com/`
* **Gói NPM:** `hyperframes` (Phiên bản mới nhất: `0.8.143`)
* **Giấy phép (License):** `Apache-2.0` (Giấy phép mã nguồn mở thương mại tiêu chuẩn, cho phép chỉnh sửa, tích hợp và phân phối mà không có điều khoản copyleft độc hại).
* **Mô tả chức năng:** Khung kết xuất đồ họa video dựa trên công nghệ Web chuẩn (HTML5, CSS, SVG, JavaScript/TypeScript), biên dịch bằng `esbuild`, render frame-by-frame tất định thông qua Headless Chrome (`puppeteer-core`) và đóng gói thành MP4 bằng `ffmpeg`.

---

## 2. ĐÁNH GIÁ TƯƠNG THÍCH MÔI TRƯỜNG THỰC THI (ENVIRONMENT COMPATIBILITY)

| Tiêu chuẩn kỹ thuật | Yêu cầu của HyperFrames | Hiện trạng máy thực thi (AIWF) | Kết luận tương thích |
|---|---|---|:---:|
| **Node.js** | `>= 22.0.0` | `v22.23.1` | ✅ **HOÀN TOÀN TƯƠNG THÍCH** |
| **Kiến trúc CPU** | macOS ARM64 / x86_64 | Apple Silicon ARM64 (T6000 / M-series) | ✅ **HOÀN TOÀN TƯƠNG THÍCH** (Native) |
| **Trình duyệt** | Chromium / Headless Chrome | Google Chrome `v130+` tại `/Applications/Google Chrome.app/` | ✅ **SẴN CÓ** |
| **FFmpeg** | `ffmpeg` CLI trên PATH | `v9.0.1` (Apple clang, hỗ trợ `libass`, `scale`, `pad`) | ✅ **HOÀN TOÀN TƯƠNG THÍCH** |
| **Thư viện C++ Native** | `sharp` (libvips), `esbuild` | Đã có prebuilt binaries cho `darwin-arm64` trên npm | ✅ **KHÔNG CẦN COMPILER PHỨC TẠP** |

---

## 3. PHÂN TÍCH RỦI RO & BẢO MẬT (SECURITY & RISK ASSESSMENT)

1. **Rủi ro phình to mã nguồn Git (Git Bloat Risk):**
   - HyperFrames có các phụ thuộc native như `sharp`, `puppeteer-core`, `esbuild`. Nếu cài đặt bừa bãi vào root của repository `ai-workforce`, `node_modules` sẽ làm tăng dung lượng Git nghiêm trọng, vi phạm **Luật R0** và **Luật R1**.
   - **Giải pháp kiểm soát:**
     - Tuyệt đối KHÔNG cài đặt `hyperframes` vào thư mục gốc repository.
     - Trong Phase 3 (POC), sẽ triển khai trong thư mục tạm sandbox cô lập `_process/hyperframes_sandbox/` (thư mục này đã được gitignore bảo vệ 100%).
2. **Rủi ro an ninh mạng & Truy cập tệp cục bộ (Local File Exposure):**
   - HyperFrames khởi chạy một web server phát triển cục bộ dựa trên Hono (`@hono/node-server`).
   - Cần đảm bảo server này chỉ bind vào địa chỉ loopback nội bộ (`127.0.0.1`), không mở port ra mạng ngoài, và không cho phép đọc file hệ thống tùy tiện.
3. **Rủi ro hiệu năng & Tiêu thụ tài nguyên (Resource Consumption):**
   - Headless Chrome render từng khung hình (frame-by-frame rendering) có thể tốn bộ nhớ RAM (khoảng 500MB – 1.5GB cho độ phân giải 1080p).
   - Máy trạm macOS T6000 với 32GB+ RAM hoàn toàn đủ năng lực đáp ứng, tuy nhiên cần kiểm soát số worker song song để tránh làm nghẽn máy.

---

## 4. CHIẾN LƯỢC TRIỂN KHAI THỬ NGHIỆM GIAI ĐOẠN 3 (PHASE 3 POC ROADMAP)

Khi bước vào Phase 3 (sau khi được Người dùng phê duyệt), việc thẩm định kỹ thuật sẽ được thực thi theo 3 bài kiểm tra mẫu độc lập:

1. **POC A — Motion Typography (Chữ Động Đa Tầng):**
   - Thời lượng: 10 giây | Khổ: $1080 \times 1080$ (Vuông 1:1) | 30 FPS.
   - Thử nghiệm: Tiêu đề chuyển động Kinetic, phụ đề xuất hiện theo từ, nền gradient động, chuyển cảnh fade mượt mà.
2. **POC B — Product Showcase (Trưng Bày Sản Phẩm):**
   - Thời lượng: 15 giây | Khổ: $1920 \times 1080$ (Ngang 16:9) | 30 FPS.
   - Thử nghiệm: Hình ảnh sản phẩm nổi bật, chuyển động camera pan/zoom mượt, 3 thẻ tính năng (feature cards) bật lên tuần tự, nút kêu gọi hành động (CTA) kết thúc.
3. **POC C — Data Animation (Biểu Đồ & Dữ Liệu Sống):**
   - Thời lượng: 15 giây | Khổ: $1080 \times 1920$ (Dọc 9:16) | 30 FPS.
   - Thử nghiệm: Cột biểu đồ tăng trưởng động, bộ đếm số nhảy số từ 0 đến $100\%$, chú thích nhãn mác rõ ràng.

---

## 5. PHÂN TÍCH CÁC PHƯƠNG ÁN THAY THẾ (CONTINGENCY ALTERNATIVES)

Nếu ở Phase 3, HyperFrames không đạt các tiêu chí nghiệm thu khắt khe (lỗi render, tiêu tốn tài nguyên bất thường, không ổn định trên Apple Silicon):

| Ứng viên thay thế | Ưu điểm | Nhược điểm | Đánh giá |
|---|---|---|:---:|
| **Canvas 2D Adapter** (Mở rộng từ `hand-drawn-animation`) | Đã chạy ổn định 100% trên AIWF qua Puppeteer, 0 phụ thuộc mới | Cần viết thêm bộ thư viện hình học phẳng (vector typography) | 🟢 **Phương án dự phòng số 1 (Tối ưu nhất)** |
| **Pure FFmpeg Filtergraph Complex** | Không cần Node/Browser, render cực nhanh | Bố cục phức tạp rất khó viết kịch bản, hạn chế hiệu ứng hiện đại | 🟡 Dự phòng cho video đơn giản |
| **Remotion** | Hệ sinh thái React phong phú, cộng đồng lớn | Ràng buộc giấy phép thương mại (phải mua bản quyền doanh nghiệp) | 🔴 Không ưu tiên |
| **Motion Canvas** | Mã nguồn mở chuyên cho video kỹ thuật | Hướng đến lập trình canvas hướng đối tượng phức tạp | 🟡 Xem xét nếu cần |
