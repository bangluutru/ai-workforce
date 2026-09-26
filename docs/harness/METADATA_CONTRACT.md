# AIWF SKILL METADATA CONTRACT
## Đặc Tả Hợp Đồng Metadata Kỹ Năng Chuẩn Hóa Cho Google Antigravity & AIWF Extension

> **Tài liệu:** `docs/harness/METADATA_CONTRACT.md`  
> **Phiên bản:** 2.0.0 (Phase 2 Foundation Repair)  
> **Áp dụng:** Toàn bộ 16 kỹ năng tại `.agents/skills/*/SKILL.md`  
> **Ngày hiệu lực:** 2026-09-26  

---

## 1. NGUYÊN TẮC THIẾT KẾ: PHÂN ĐỊNH 3 TẦNG METADATA

Trước Phase 2, repository AIWF có sự nhầm lẫn giữa metadata native của Antigravity và metadata riêng của extension hoặc các trường tùy biến không có consumer thực tế.

Hợp đồng này thiết lập phân định dứt khoát thành 3 nhóm:

```
┌────────────────────────────────────────────────────────────────────────┐
│ NHÓM 1: ANTIGRAVITY NATIVE METADATA (Bắt buộc cho Agent Runtime)       │
│ • name: Định danh duy nhất (kebab-case)                                │
│ • description: Mô tả kích hoạt (USE WHEN / DO NOT USE WHEN)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ NHÓM 2: AIWF EXTENSION METADATA (Phục vụ UI Panel & Trải nghiệm User) │
│ • display-name: Tên tiếng Việt có dấu hiển thị trên giao diện          │
│ • trigger: Câu lệnh mẫu gợi ý cho người dùng copy/paste               │
│ • category: Phân loại danh mục (content|docs|legal_finance|tech_ops)   │
│ • needs_file: Cờ khai báo cần đính kèm tệp (true|false)                │
│ • file_filter: Bộ lọc định dạng file (office|pdf|code|any)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ NHÓM 3: CÁC TRƯỜNG LOẠI BỎ KHỎI FRONTMATTER (Không có consumer thật)   │
│ ❌ allowed-tools: Antigravity không bypass quyền qua frontmatter       │
│ ❌ effort: Do User/IDE quản lý tại runtime, không qua frontmatter      │
│ ❌ context: fork: Subagent được gọi qua prompt/tools, không qua YAML    │
│ ❌ interaction-mode / argument-hint / disable-model-invocation         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CHI TIẾT CÁC TRƯỜNG HỢP CHUẨN

### 2.1. Nhóm 1: Antigravity-Native Metadata

| Trường | Kiểu dữ liệu | Bắt buộc | Quy cách & Ý nghĩa |
|---|---|---|---|
| **`name`** | String | **CÓ** | Tên định danh kỹ thuật, viết bằng chữ thường không dấu theo chuẩn `kebab-case` (ví dụ: `ejv-translate`, `video-studio`, `hand-drawn-animation`). Bắt buộc khớp chính xác với tên thư mục chứa skill. |
| **`description`** | String | **CÓ** | **Trường quan trọng nhất đối với Agent.** Mô hình Antigravity chỉ đọc duy nhất trường này để quyết định kích hoạt skill theo cơ chế *Progressive Disclosure*. Bắt buộc phải có 2 phần:<br>1. **USE WHEN**: Nêu rõ mục tiêu, loại tệp đầu vào và tình huống kích hoạt.<br>2. **DO NOT USE WHEN**: Nêu rõ ranh giới phủ định để tránh xung đột định tuyến với các skill khác. |

### 2.2. Nhóm 2: AIWF Extension Metadata

Các trường này được mã nguồn của AIWF Extension (`extension/lib/scanner.js`) đọc trực tiếp để kết xuất giao diện điều khiển (Sidebar Panel) cho người dùng:

| Trường | Kiểu dữ liệu | Bắt buộc | Quy cách & Ý nghĩa |
|---|---|---|---|
| **`display-name`** | String | **CÓ** | Tên hiển thị trên giao diện người dùng. Bắt buộc phải là **Tiếng Việt có dấu** hoặc **Tiếng Anh chuẩn chính tả** (ví dụ: `Tạo Phụ Đề`, `Studio Video`, `Tạo Hoạt Hình`, `EJV Translate`). Cấm dùng tiếng Việt không dấu. |
| **`trigger`** | String | Khuyến nghị | Câu lệnh mẫu ngắn gọn để người dùng nhấn một chạm là tự động điền vào khung chat IDE (ví dụ: `Hãy thực hiện skill video-studio theo đúng hướng dẫn trong SKILL.md`). |
| **`category`** | String | Khuyến nghị | Phân nhóm hiển thị trên sidebar panel. Chỉ chấp nhận 1 trong 4 giá trị:<br>• `content`: Kỹ năng nội dung, truyền thông, video, landing page.<br>• `docs`: Kỹ năng bóc tách, dịch thuật, soạn thảo văn bản.<br>• `legal_finance`: Kỹ năng pháp lý, thuế, kế toán.<br>• `tech_ops`: Kỹ năng kỹ thuật, kiểm định ứng dụng. |
| **`needs_file`** | Boolean | Tùy chọn | `true` nếu skill bắt buộc phải có tệp đầu vào do người dùng cung cấp (ví dụ: file PDF scan, file video, file hợp đồng). Mặc định: `false`. |
| **`file_filter`** | String | Tùy chọn | Loại tệp mở trên hộp thoại chọn file của extension: `office` (docx, xlsx, pptx), `pdf` (pdf), `code` (py, js, html, css, json), `media` (mp4, mp3, wav, srt), hoặc `any`. |

---

## 3. CÁC TRƯỜNG ĐÃ LOẠI BỎ & LÝ DO KỸ THUẬT

1. **`allowed-tools`**:
   * *Lý do:* Antigravity IDE quản lý quyền thực thi công cụ thông qua giao diện người dùng, cấu hình dự án hoặc Antigravity Lifecycle Hooks (`hooks.json` - `PreToolUse`). Việc khai báo `allowed-tools` trong frontmatter không có hiệu lực cấp quyền tự động trong phiên bản hiện hành.
   * *Giải pháp:* Chuyển thông tin về các công cụ cần thiết vào phần thân tài liệu Markdown để Agent biết nên ưu tiên dùng công cụ nào.
2. **`effort`**:
   * *Lý do:* Ngân sách tư duy (Reasoning Effort: low/medium/high) là cấu hình runtime của mô hình do người dùng chọn trên giao diện IDE (ví dụ: Gemini 3.8 Flash Thinking High). Frontmatter không thể ghi đè cấu hình này của IDE.
   * *Giải pháp:* Gỡ bỏ khỏi YAML frontmatter.
3. **`context: fork`**:
   * *Lý do:* Antigravity không tự động fork subagent chỉ dựa trên thẻ frontmatter này. Việc phân nhánh tác vụ nặng được thực hiện bằng cách hướng dẫn Agent sử dụng native tool (ví dụ: `browser_subagent`) hoặc phân tách ngữ cảnh theo quy trình.
   * *Giải pháp:* Gỡ bỏ khỏi YAML frontmatter.
4. **`interaction-mode` & `argument-hint`**:
   * *Lý do:* Không có consumer nào trong Antigravity runtime hoặc AIWF extension đọc và xử lý 2 trường này.
   * *Giải pháp:* Gỡ bỏ khỏi frontmatter.

---

## 4. MẪU YAML FRONTMATTER CHUẨN MẪU (CANONICAL TEMPLATE)

```yaml
---
name: video-studio
display-name: Studio Video
description: >-
  Biên tập và sản xuất video tự động từ kịch bản hoặc ý tưởng người dùng;
  hỗ trợ tìm kiếm stock media bản quyền (Pexels/Pixabay), ghép audio lồng tiếng,
  cân chỉnh nhạc nền (BGM ducking) và xuất video MP4.
  USE WHEN: Người dùng muốn dựng một video hoàn chỉnh từ nội dung chữ hoặc kịch bản có sẵn.
  DO NOT USE WHEN: Chỉ cần tạo/dịch phụ đề (dùng 'phu-de'), chỉ cần đọc lồng tiếng một file âm thanh đơn lẻ (dùng 'long-tieng'), hoặc tạo hoạt hình minh họa vẽ tay 2D (dùng 'hand-drawn-animation').
trigger: Studio Video, biên tập video tự động, làm video từ kịch bản
category: content
needs_file: false
file_filter: any
---
```

---

## 5. BẢNG TIÊU CHUẨN 16 SKILLS HIỆN CÓ

| STT | `name` | `display-name` | `category` | `needs_file` | `file_filter` |
|:---:|---|---|:---:|:---:|:---:|
| 1 | `app-auditor` | Kiểm Định Ứng Dụng | `tech_ops` | `false` | `any` |
| 2 | `bao-cao-kt` | Báo Cáo Kế Toán | `legal_finance` | `true` | `office` |
| 3 | `boc-tach-pdf` | Bóc Tách PDF | `docs` | `true` | `pdf` |
| 4 | `chotto-newsroom` | Biên Tập Tin Chotto | `content` | `false` | `any` |
| 5 | `dich-giu-dinh-dang` | Dịch Giữ Định Dạng | `docs` | `true` | `pdf` |
| 6 | `ejv-translate` | EJV Translate | `docs` | `true` | `any` |
| 7 | `hand-drawn-animation` | Tạo Hoạt Hình | `content` | `false` | `any` |
| 8 | `long-tieng` | Lồng Tiếng Video | `content` | `true` | `media` |
| 9 | `phu-de` | Tạo Phụ Đề | `content` | `true` | `media` |
| 10 | `tao-landing-page` | Tạo Landing Page | `content` | `false` | `any` |
| 11 | `thiet-ke` | Thiết Kế Đồ Họa | `content` | `false` | `any` |
| 12 | `tu-van-phap-luat` | Tư Vấn Pháp Luật | `legal_finance` | `false` | `any` |
| 13 | `tu-van-thue-tncn` | Tư Vấn Thuế TNCN | `legal_finance` | `false` | `any` |
| 14 | `video-studio` | Studio Video | `content` | `false` | `any` |
| 15 | `viet-bai` | Viết Bài Đa Kênh | `content` | `false` | `any` |
| 16 | `xu-ly-van-phong` | Xử Lý Văn Phòng | `docs` | `true` | `office` |
