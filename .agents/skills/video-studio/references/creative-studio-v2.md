# Sổ Tay Vận Hành AIWF Creative Studio 2.0

> **Tài liệu tham chiếu chuẩn mực cho kỹ năng `video-studio` và workflow `W1-phong-media`.**  
> Bản đặc tả toàn diện về Kịch bản phân cảnh Storyboard v2.0, Hồ sơ nhận diện thương hiệu Brand Motion Profiles, Danh mục 10 Motion Presets và Hệ thống kiểm toán thị giác Visual QA 2.0.

---

## 1. TỔNG QUAN KIẾN TRÚC CREATIVE STUDIO 2.0

Creative Studio 2.0 là bản nâng cấp toàn diện cho năng lực sản xuất video của AI Workforce, bổ sung lớp đồ họa chuyển động (Motion Graphics), kiểu chữ động (Kinetic Typography), biểu đồ dữ liệu tương tác (Infographics) và thẻ tính năng sản phẩm (Product Spotlight & Feature Cards), song song và hoàn toàn tương thích ngược với pipeline stock footage truyền thống.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI AGENT / NGƯỜI DÙNG                          │
│                                   │                                    │
│       ┌───────────────────────────┴───────────────────────────┐        │
│       ▼ (Truyền thống - v1)                                   ▼ (Nâng cao - v2) │
│  script.json (Narration + Stock)                 storyboard.json (Phân cảnh v2)│
│       │                                                       │        │
│       ▼                                                       ▼        │
│  video_pipeline.py                                storyboard_renderer.py       │
│       │                                                       │        │
│       │                                   ┌───────────────────┴────┐   │
│       │                                   ▼                        ▼   │
│       │                         HyperFrames Engine       Canvas 2D Fallback   │
│       │                           (GPU Metal/WebGL)         (FFmpeg Direct)   │
│       │                                   └─────────┬──────────────┘   │
│       │                                             ▼                  │
│       └───────────────────────┬─────────────────────┘                  │
│                               ▼                                        │
│                 Âm thanh: VieNeu-TTS / Kokoro                          │
│                 Nhạc nền: BGM Ducking -16 LUFS                         │
│                 Phụ đề: ASS Karaoke (Be Vietnam Pro)                   │
│                               │                                        │
│                               ▼                                        │
│                 Hệ thống kiểm toán Visual QA 2.0                       │
│             (Technical Report + Contact Sheet 12 Khung)                │
│                               │                                        │
│                               ▼                                        │
│              Thành phẩm: <output_dir>/<project>.mp4                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CẤU HÌNH CỜ TÍNH NĂNG (OPT-IN SAFETY FLAG)

Để đảm bảo an toàn tuyệt đối và tính tương thích ngược, toàn bộ hệ thống đồ họa chuyển động được quản lý bởi cờ tính năng tại `.agents/skills/video-studio/config/creative_studio_v2.json`:

```json
{
  "creative_studio_v2": {
    "enabled": false,
    "motion_renderer": "disabled",
    "visual_qa_v2": false,
    "audio_driven_timeline": false,
    "motion_presets": false,
    "legacy_fallback": true
  }
}
```

* **Chế độ Mặc định (`enabled: false`):** Mọi tác vụ video thông thường chạy qua pipeline v1 đã được kiểm chứng an toàn.
* **Chế độ Nâng cao (`enabled: true`):** Cho phép agent kích hoạt Storyboard v2.0, tự động gọi `creative.storyboard_renderer` và kích hoạt Visual QA 2.0.

---

## 3. HỢP ĐỒNG KỊCH BẢN PHÂN CẢNH STORYBOARD V2.0

File kịch bản phân cảnh `storyboard.json` là định dạng trung tâm biểu diễn video đa cảnh:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "schema_version": "2.0",
  "project_id": "chottoday_news_intro",
  "title": "ChottoDay Newsroom Intro",
  "purpose": "social_intro",
  "language": "vi",
  "fps": 30,
  "resolution": {
    "width": 1080,
    "height": 1080
  },
  "aspect_ratio": "1:1",
  "target_duration_seconds": 12.0,
  "brand_profile": "chottoday",
  "scenes": [
    {
      "id": "s01",
      "type": "motion_graphics",
      "duration_seconds": 3.0,
      "visual_goal": "Tiêu đề mở đầu thương hiệu ChottoDay",
      "motion": {
        "preset": "06_logo_reveal",
        "intensity": "moderate",
        "easing": "ease-out"
      },
      "props": {
        "tag": "CHOTTODAY.COM",
        "brand_name": "ChottoDay",
        "tagline": "Kênh Thông Tin & Chính Sách Nhật Bản"
      },
      "narration": "Chào mừng bạn đến với ChottoDay, cổng thông tin chính sách Nhật Bản dành riêng cho người Việt."
    },
    {
      "id": "s02",
      "type": "motion_graphics",
      "duration_seconds": 4.5,
      "visual_goal": "Thống kê cộng đồng và dữ liệu kiều bào",
      "motion": {
        "preset": "05_number_counter",
        "intensity": "energetic"
      },
      "props": {
        "tag": "CỘNG ĐỒNG NGƯỜI VIỆT TẠI NHẬT",
        "number_value": 600000,
        "number_prefix": "+",
        "number_suffix": "",
        "unit": "Kiều Bào",
        "description": "Cộng đồng người Việt Nam đang học tập, làm việc và sinh sống phát triển vững mạnh khắp 47 tỉnh thành Nhật Bản."
      },
      "narration": "Với hơn sáu trăm nghìn kiều bào, chúng tôi đồng hành cùng bạn trên mọi hành trình."
    },
    {
      "id": "s03",
      "type": "motion_graphics",
      "duration_seconds": 4.5,
      "visual_goal": "Kêu gọi theo dõi và truy cập website",
      "motion": {
        "preset": "10_cta_reveal",
        "intensity": "moderate"
      },
      "props": {
        "badge": "CHÍNH THỐNG & KỊP THỜI",
        "title": "Theo Dõi ChottoDay Ngay Hôm Nay",
        "subtitle": "Cập nhật chính sách visa, thuế Nenkin và đời sống Nhật Bản chuẩn xác nhất.",
        "cta_button": "Truy Cập ChottoDay.com"
      },
      "narration": "Truy cập ngay ChottoDay chấm com để không bỏ lỡ những quyền lợi chính sách quan trọng nhất."
    }
  ]
}
```

---

## 4. HỒ SƠ NHẬN DIỆN THƯƠNG HIỆU (BRAND MOTION PROFILES)

Hồ sơ thương hiệu xác định bảng màu, kiểu chữ, cường độ chuyển động và vùng an toàn (Safe Area):

| Profile ID | Tên Thương Hiệu | Màu Sắc Chủ Đạo (Primary / Accent / BG) | Kiểu Chữ | Đặc Trưng Chuyển Động |
|---|---|---|---|---|
| `chottoday` | ChottoDay Newsroom | `#0A2540` / `#FF6B35` / `#FAFAFA` | Be Vietnam Pro + Noto Sans JP | Chuyên nghiệp, nhịp độ tin tức rõ ràng, dứt khoát |
| `balancera` | Balancera Premium Health | `#1B4332` / `#D4AF37` / `#0D1F18` | Playfair / Spectral + Montserrat | Sang trọng, thư thái, easing mượt mà cao cấp |
| `tech_dark` | Tech Innovation | `#3B82F6` / `#10B981` / `#0B0F19` | Inter / JetBrains Mono | Hiện đại, sắc nét, công nghệ cao |
| `corporate` | Doanh nghiệp Hiện đại | `#1E3A8A` / `#3B82F6` / `#FFFFFF` | Be Vietnam Pro / Roboto | Chuẩn mực, tin cậy, bố cục cân đối |
| `default` | AIWF Neutral Standard | `#14213D` / `#FCA311` / `#FFFFFF` | Be Vietnam Pro | Trung tính, đa dụng cho mọi tình huống |

---

## 5. DANH MỤC 10 MOTION PRESETS CHUẨN MỰC

Toàn bộ presets được lưu tại `.agents/skills/_shared/creative/presets/`, hỗ trợ đa tỷ lệ khung hình (`1:1`, `16:9`, `9:16`):

### 1. `01_fade_in` — Mờ Dần & Nâng Khung (Soft Elegant Fade)
- **Mục đích:** Khởi đầu phân cảnh trang nhã, giới thiệu ý niệm mới.
- **Props chính:** `tag`, `title`, `subtitle`, `accent_color`, `bg_color`.

### 2. `02_slide_reveal` — Trượt Mở Mặt Nạ (Masked Slide Reveal)
- **Mục đích:** Chuyển cảnh phân đoạn, tách lớp thông điệp.
- **Props chính:** `tag`, `title`, `subtitle`, `direction` ("left" | "right").

### 3. `03_scale_pop` — Phóng Đại Điểm Nhấn (Scale Pop Typography)
- **Mục đích:** Tuyên ngôn mạnh mẽ, từ khóa đắt giá, slogan cốt lõi.
- **Props chính:** `tag`, `title`, `subtitle`, `accent_badge`.

### 4. `04_kinetic_title` — Chữ Động Kinetic (Kinetic Typography Stagger)
- **Mục đích:** Video nhịp điệu cao, phân rã từng từ hoặc dòng chữ nối tiếp.
- **Props chính:** `tag`, `line1`, `line2`, `line3`, `accent_word`.

### 5. `05_number_counter` — Con Số Tăng Dần (Animated Number Counter)
- **Mục đích:** Số liệu tài chính, KPI, doanh số, số lượng người dùng.
- **Props chính:** `tag`, `number_value`, `number_prefix`, `number_suffix`, `unit`, `description`.

### 6. `06_logo_reveal` — Mở Màn Nhận Diện Logo (Brand Identity Reveal)
- **Mục đích:** Phân cảnh mở đầu hoặc kết thúc với biểu tượng thương hiệu.
- **Props chính:** `tag`, `brand_name`, `tagline`, `logo_svg` hoặc `logo_url`.

### 7. `07_product_spotlight` — Trọng Tâm Sản Phẩm (3D Floating Spotlight)
- **Mục đích:** Giới thiệu bao bì, chai lọ, hình ảnh thiết bị trung tâm với ánh sáng phản quang.
- **Props chính:** `tag`, `product_name`, `headline`, `badge`, `image_url`.

### 8. `08_feature_card` — Thẻ Tính Năng & Lợi Ích (Staggered Feature Cards)
- **Mục đích:** Trình bày 3 lợi ích cốt lõi hoặc 3 bước giải pháp.
- **Props chính:** `tag`, `headline`, `features` (mảng 3 phần tử gồm `title`, `desc`, `icon`).

### 9. `09_bar_chart` — Biểu Đồ Cột Tăng Trưởng (Animated Infographic Bars)
- **Mục đích:** So sánh dữ liệu, trực quan hóa xu hướng tăng trưởng.
- **Props chính:** `tag`, `headline`, `bars` (mảng nhãn và giá trị %).

### 10. `10_cta_reveal` — Kêu Gọi Hành Động (Call-to-Action Outro)
- **Mục đích:** Khép lại video, thúc đẩy chuyển đổi, truy cập website, tải ứng dụng.
- **Props chính:** `badge`, `title`, `subtitle`, `cta_button`, `guarantee`.

---

## 6. HỆ THỐNG KIỂM TOÁN THỊ GIÁC VISUAL QA 2.0

Mọi video đồ họa chuyển động sau khi render đều được kiểm định tự động qua `creative.qa`:

### Quy Trình Thẩm Định 2 Lớp:
1. **Lớp 1: Thẩm định Kỹ thuật (Technical Validation):**
   - Kiểm tra stream codec (`h264`), âm thanh (`aac`), sample rate (48000 Hz).
   - Kiểm tra sai số độ dài so với storyboard ($|\Delta t| \le 0.5\text{s}$).
   - Kiểm tra độ phân giải và tỷ lệ khung hình mục tiêu.
   - Đo lường mức độ lớn âm thanh EBU R128 (mục tiêu $-16 \pm 1$ LUFS).
2. **Lớp 2: Thẩm định Thị giác (Visual Inspection):**
   - Trích xuất 12 khung hình đại diện phân bổ đều theo trục thời gian.
   - Quét độ sáng: cảnh báo khi có $> 20\%$ khung hình bị đen hoàn toàn hoặc cháy sáng.
   - Quét chuyển động: phát hiện hiện tượng đứng hình (Frozen Video) nếu các khung hình giống nhau $> 98\%$.
   - Quét vùng an toàn (Safe Area Margin): cảnh báo nếu đồ thị/nội dung tràn mép ngoài viền 8%.
   - Tạo ảnh tiếp xúc tổng thể `contact_sheet.jpg` gồm lưới $4 \times 3$ kèm mốc thời gian và độ sáng.

### Đọc Báo Cáo `technical_report.json`:
- `overall_score`: Điểm số từ 0 đến 100. Đạt chuẩn khi $\ge 85/100$.
- `overall_verdict`: `PASS` (sẵn sàng xuất bản), `WARN` (có khuyến nghị điều chỉnh), `FAIL` (lỗi nghiêm trọng cần render lại).
- `recommendations`: Gợi ý sửa chữa cụ thể để agent khắc phục ngay.

---

## 7. CÁCH GỌI TỪ PYTHON VÀ CLI

```python
from creative import render_storyboard

# Kết xuất trực tiếp từ file storyboard.json
result = render_storyboard(
    storyboard="path/to/storyboard.json",
    output_path="~/Downloads/AIWF_Output/my_project/video.mp4",
    run_qa=True
)

if result.success:
    print(f"✅ Render thành công: {result.output_mp4}")
    print(f"📊 Điểm Visual QA: {result.qa_report.overall_score}/100")
    print(f"🖼️ Ảnh tiếp xúc: {result.contact_sheet}")
else:
    print(f"❌ Lỗi: {result.error_message}")
```
