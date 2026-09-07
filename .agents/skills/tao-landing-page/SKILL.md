---
name: tao-landing-page
display-name: Tạo Landing Page
description: Chuyển đổi thiết kế từ Google Stitch hoặc Figma thành Landing Page React + Vite + TypeScript + Tailwind CSS production-ready, tích hợp bắt buộc với Landing Hub theo Integration Contract v1.0, hỗ trợ kiểm định chất lượng tự động qua App Auditor. KHÔNG dùng cho việc thiết kế ấn phẩm đồ họa in ấn tĩnh như Brochure hay Leaflet (chuyển sang [thiet-ke]), và KHÔNG dùng cho việc chỉ viết bài văn bản tiếp thị đa kênh (chuyển sang [viet-bai]).
trigger: Tạo landing page, Design to Landing, Chuyển thiết kế sang landing page, Stitch sang landing page, Figma sang landing page, làm landing page
argument-hint: [url_stitch_hoac_figma] [project_id]
allowed-tools: [run_command, view_file, write_to_file, replace_file_content, browser_subagent]
effort: high
interaction-mode: direct
context: fork
needs_file: false
file_filter: code
---

# KỸ NĂNG: TẠO LANDING PAGE (DESIGN-TO-LANDING ENGINE)
## Tiêu Chuẩn Kiến Trúc 5 Lớp Chuẩn Gemini 3.8 Multi-Agent & Rule R4

```
   [ Google Stitch / Figma / Screenshot Fallback ]
                         │
                         ▼
             ┌───────────────────────┐
             │   1. Input Router     │
             └───────────┬───────────┘
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
┌──────────────┐                   ┌──────────────┐
│ Stitch MCP   │                   │ Figma MCP    │
└──────┬───────┘                   └──────┬───────┘
       └─────────────────┬─────────────────┘
                         ▼
             ┌───────────────────────┐
             │ 2. Design Interpreter │
             │  (Normalized DESIGN)  │
             └───────────┬───────────┘
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
┌──────────────┐                   ┌──────────────┐
│ Form Classify│                   │ Arc Detector │
│(Lead/Ord/Cus)│                   │(Hero/Ben/CTA)│
└──────┬───────┘                   └──────┬───────┘
       └─────────────────┬─────────────────┘
                         ▼
             ┌───────────────────────┐
             │  3. Landing Builder   │
             │ (React+Vite+TS+TW)    │
             └───────────┬───────────┘
                         ▼
             ┌───────────────────────┐
             │ 4. Hub Integrator     │
             │ (Contract v1.0 SDK)   │
             └───────────┬───────────┘
                         ▼
             ┌───────────────────────┐
             │ 5. QA & App Auditor   │
             │ (Visual & Functional) │
             └───────────────────────┘
```

---

<goal>
Chuyển đổi thiết kế landing page từ Google Stitch (dự án / màn hình) hoặc Figma (URL / frame) thành mã nguồn ứng dụng web React + Vite + TypeScript + Tailwind CSS production-ready, đáp ứng đầy đủ responsive 3 viewports (375px, 768px, 1440px), tích hợp chuẩn xác với Landing Hub (theo Landing Hub Integration Contract v1.0 tại /Users/tranhaibang/.gemini/antigravity-ide/scratch/landing-hub) và vượt qua các vòng kiểm định chất lượng tự động của App Auditor.
</goal>

---

<context>
## BỐI CẢNH KIẾN TRÚC & NGUYÊN TẮC VẬN HÀNH

1. **ZERO EXTERNAL API & KHÔNG YÊU CẦU API KEY**:
   - Toàn bộ năng lực phân tích cấu trúc thị giác, tổng hợp mã nguồn, phân loại form và sinh component thuộc về mô hình LLM nội bộ tích hợp trong Antigravity IDE (Gemini 3.8).
   - Tuyệt đối không gọi REST API bên ngoài (OpenAI API, Claude API, Gemini API qua key riêng) và không yêu cầu người dùng cấu hình API key để vận hành kỹ năng.
   - Các script Python chỉ phục vụ trích xuất dữ liệu, kiểm tra môi trường, xác thực cú pháp và giao tiếp API với Landing Hub.

2. **AUTONOMOUS FULL-RUN PROTOCOL (TỰ CHẠY LIÊN TỤC)**:
   - Kỹ năng tự động thực hiện xuyên suốt toàn bộ chu trình PDCA Cascade ([P]lan -> [D]o -> [C]heck -> [A]ct) từ khi nhận diện đầu vào đến khi tạo dự án, đăng ký Landing Hub, kiểm thử responsive và chạy QA runner.
   - Không tự dừng giữa chừng để xin phép hoặc hỏi những câu thừa thãi nếu quy trình đang diễn ra đúng kế hoạch.
   - Chỉ dừng lại khi thiếu thông tin kinh doanh không thể tự suy luận an toàn hoặc gặp lỗi ngoại lệ không thể phục hồi.

3. **BẢO VỆ CODEBASE (ANTI-REPO BLOAT) & PATH RESOLUTION**:
   - Mọi mã nguồn Landing Page sinh ra PHẢI được lưu vào `<output_dir>` do người dùng chỉ định hoặc mặc định tại:
     `~/Downloads/landing-pages/<project_id>/`
   - Vùng xử lý dữ liệu trung gian được lưu tại `_process/<project_id>/` (được bảo vệ bởi `.gitignore`).
   - TUYỆT ĐỐI KHÔNG tự ý xả file mã nguồn landing page vào thư mục gốc của repository AI Workforce.
</context>

---

<instructions>
## QUY TRÌNH THỰC THI CHUẨN (7 BƯỚC ĐỒNG BỘ)

### BƯỚC 0: TIẾP NHẬN TỌA ĐỘ ĐẦU VÀO (INTAKE & COORDINATES)
Xác định 5 Trục Tọa độ nghiệp vụ trước khi triển khai:
- **Trục 1 (Design Source):** URL Stitch, URL Figma hoặc file ảnh thiết kế.
- **Trục 2 (Project ID):** Mã dự án kinh doanh (`projectId`, ví dụ: `genki-fami`, `abano`).
- **Trục 3 (Landing Page ID):** Mã định danh trang (`landingPageId`, ví dụ: `genki-collagen-promo`).
- **Trục 4 (Landing Hub URL):** Địa chỉ Landing Hub API (Mặc định local: `http://localhost:3001` hoặc staging).
- **Trục 5 (Output Directory):** Đường dẫn thư mục đích (`<output_dir>`, mặc định `~/Downloads/landing-pages/<project_id>/`).

### BƯỚC 1: ĐỊNH TUYẾN ĐẦU VÀO (INPUT ROUTING)
Chạy script phân loại đầu vào:
```bash
python3 .agents/skills/tao-landing-page/scripts/input_router.py "<url_hoac_input>" --json
```
- Nếu là **Stitch URL**: Chuyển sang Stitch Adapter.
- Nếu là **Figma URL**: Chuyển sang Figma Adapter.
- Nếu là **Ảnh chụp màn hình**: Kích hoạt cờ `[CẦN XÁC MINH - FIDELITY FALLBACK]` và ghi chú rõ ràng rằng độ trung thực token có thể thấp hơn dữ liệu MCP trực tiếp.

### BƯỚC 2: TRÍCH XUẤT THIẾT KẾ (DESIGN ADAPTER EXTRACTION)
1. **Google Stitch:**
   ```bash
   python3 .agents/skills/tao-landing-page/scripts/stitch_adapter.py --project "<project_id>" --screen "<screen_id>" --json
   ```
   *Nguyên tắc Fail-Closed:* Nếu Stitch MCP chưa kết nối, dừng lại và hướng dẫn cấu hình theo `.agents/skills/tao-landing-page/resources/mcp_setup_guides.md`. Tuyệt đối KHÔNG giả vờ đã đọc được thiết kế Stitch.
2. **Figma Official:**
   ```bash
   python3 .agents/skills/tao-landing-page/scripts/figma_adapter.py --file "<file_key>" --node "<node_id>" --json
   ```
   *Nguyên tắc Chunking:* Đối với frame lớn, phân mảnh cấu trúc và lấy dữ liệu section-by-section. Nếu thiếu quyền, dừng lại và yêu cầu cung cấp Personal Access Token.

### BƯỚC 3: THÔNG DỊCH ĐẶC TẢ THIẾT KẾ TRUNG GIAN (DESIGN.MD)
Hội tụ dữ liệu từ Stitch và Figma vào một bản đặc tả trung gian duy nhất:
```bash
python3 .agents/skills/tao-landing-page/scripts/design_interpreter.py --input "_process/<project_id>/raw_design.json" --output "_process/<project_id>/DESIGN.md"
```
Bản đặc tả `DESIGN.md` chứa:
- Token màu sắc (`primary`, `secondary`, `accent`, `background`, `surface`, `text`, `muted`).
- Đo lường kiểu chữ (`fontFamily`, `h1`, `h2`, `body`), khoảng cách và bo góc (`radius`).
- Danh mục section và vai trò ngữ nghĩa (Header, Hero, Benefits, Features, Social proof, Product, Pricing, FAQ, Form, Footer).

### BƯỚC 4: PHÂN LOẠI FORM (FORM CLASSIFICATION)
Xác định bắt buộc loại form:
```bash
python3 .agents/skills/tao-landing-page/scripts/form_classifier.py --json-input "_process/<project_id>/form_data.json" --cta "<cta_text>"
```
- `lead`: Thu thập liên hệ, nhận tư vấn -> `/api/lead` (`LPHub.submitLead()`).
- `order`: Chọn sản phẩm, số lượng, giao COD -> `/api/order` (`LPHub.submitOrder()`).
- `custom`: Quiz, trắc nghiệm, khảo sát -> `/api/custom-form` (`LPHub.submitCustomForm()`).
*Tuyệt đối cấm tạo backend riêng hoặc lưu Google Sheets tự chế.*

### BƯỚC 5: ĐĂNG KÝ THỰC THỂ LANDING HUB (HUB INTEGRATION)
Kiểm tra và đăng ký an toàn trên Landing Hub Ingestion / Admin API:
```bash
python3 .agents/skills/tao-landing-page/scripts/hub_integrator.py \
  --api-url "http://localhost:3001" \
  --project-id "<project_id>" \
  --lp-id "<landing_page_id>" \
  --form-id "<form_id>" \
  --form-type "<lead|order|custom>"
```
Lưu cấu hình trả về để nhúng vào mã nguồn client:
`{ projectId, landingPageId, formId, formType, apiUrl }`.

### BƯỚC 6: SINH MÃ NGUỒN LANDING PAGE (LANDING BUILDER)
Khởi tạo cấu trúc dự án React + Vite + TypeScript + Tailwind CSS:
```bash
python3 .agents/skills/tao-landing-page/scripts/landing_builder.py \
  --design-json "_process/<project_id>/raw_design.json" \
  --hub-config-json "_process/<project_id>/hub_config.json" \
  --target-dir "<output_dir>"
```
- Module hóa các component: `Header.tsx`, `Hero.tsx`, `Benefits.tsx`, `OrderForm.tsx`/`LeadForm.tsx`, `Footer.tsx`.
- Tích hợp `src/lib/lphub.ts` với `LPHub.init()`, `LPHub.track()`.
- Xử lý trạng thái nút bấm: `disabled` khi submitting, hiện spinner, báo lỗi có nút bấm thử lại (retry), màn hình cảm ơn (thank-you state).
- **Tuân thủ Chuẩn Modern Web Guidance (Google Platform Standard):**
  Bắt buộc tra cứu và áp dụng best-practices từ `modern-web-guidance` (`npx -y modern-web-guidance@latest search "<query>"`):
  * *Native UI & Animations:* Sử dụng thẻ `<dialog>` native cho modal và Popover API cho tooltip/popover; tận dụng CSS Anchor Positioning thay vì cài thư viện ngoài (như `floating-ui`, `popper.js`). Tận dụng View Transitions API cho hiệu ứng chuyển đổi mượt mà.
  * *Tối ưu Core Web Vitals & LCP:* Bổ sung thuộc tính `fetchpriority="high"` cho hình ảnh Hero (LCP candidate), gắn `loading="lazy"` cho ảnh phụ, áp dụng `content-visibility: auto` cho các khối nội dung dài phía dưới fold.
  * *Form & Validation thân thiện:* Sử dụng CSS `:user-valid` / `:user-invalid` để hiển thị lỗi validation chỉ sau khi người dùng đã tương tác (tránh báo lỗi giật cục khi vừa tải trang); dùng `field-sizing: content` cho dynamic textarea.
  * *Zero External Bloat:* Tuyệt đối KHÔNG cài đặt các thư viện JavaScript thừa thãi cho các tính năng nền tảng web hiện đại đã hỗ trợ native.

### BƯỚC 7: KIỂM ĐỊNH CHẤT LƯỢNG (QA RUNNER & APP AUDITOR)
Chạy bộ kiểm thử tự động:
```bash
python3 .agents/skills/tao-landing-page/scripts/qa_runner.py \
  --project-dir "<output_dir>" \
  --hub-api-url "http://localhost:3001" \
  --project-id "<project_id>" \
  --lp-id "<landing_page_id>" \
  --form-id "<form_id>" \
  --form-type "<form_type>"
```
- Kiểm tra TypeScript (`tsc --noEmit`) và Build (`vite build`).
- Kiểm tra 3 viewports: Mobile 375px, Tablet 768px, Desktop 1440px.
- Thực hiện kiểm thử gửi form E2E: Xác thực nhận HTTP 201 lần đầu và HTTP 200 `idempotentReplay: true` khi gửi lại.
- Gọi tiếp kỹ năng kiểm định `app-auditor` để quét rà soát toàn bộ Accessibility WCAG A/AA và lỗi giao diện nếu có.
</instructions>

---

<constraints>
## 5 ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS)
1. ❌ **CẤM ghi trực tiếp vào Firestore / Database phía Client:** Mọi hành vi gửi lead, đặt hàng, tracking bắt buộc phải qua Landing Hub Ingestion endpoints hoặc SDK `LPHub`.
2. ❌ **CẤM Hardcode Secret / Test Tokens:** Không để lộ token quản trị, API keys hay chuỗi xác thực trong client bundle.
3. ❌ **CẤM Hallucinate dữ liệu thiết kế:** Nếu Stitch MCP hoặc Figma MCP không khả dụng, phải báo lỗi minh bạch và dừng lại; không tự bịa rằng đã đọc được design tree.
4. ❌ **CẤM đổi tên Standard Events:** Bắt buộc tuân thủ đúng tên sự kiện chuẩn (`page_view`, `cta_click`, `form_view`, `form_start`, `form_submit`, `order_created`, `purchase`). Tuyệt đối không tự gộp `order_created` thành `purchase`.
5. ❌ **CẤM Xả Rác Codebase:** Không tạo thư mục mã nguồn landing page ngay tại thư mục gốc repository AI Workforce.
</constraints>

---

<working_ledger>
## SỔ CÁI TIẾN TRÌNH VẬT LÝ (CHECKPOINT & PDCA CASCADE)
Mọi tác vụ thực thi được ghi nhận tuần tự vào `_process/<project_id>/landing_ledger.md`:
- `[P]lan`: Đã nhận diện adapter, phân tích cây phân cấp mục tiêu.
- `[D]o`: Đã bóc tách DESIGN.md, sinh mã nguồn component React và nhúng SDK.
- `[C]heck`: Đã chạy QA Runner, kiểm thử gửi form đến Hub, kiểm tra 3 viewports.
- `[A]ct`: Tối ưu hóa các điểm lệch giao diện, hoàn tất đóng gói và bàn giao.
</working_ledger>

---

<quality_gate>
## CHECKLIST TỰ THẨM ĐỊNH TRƯỚC KHI BÀN GIAO (QUALITY GATES)
Trước khi bàn giao thành phẩm cho người dùng, Agent phải xác nhận:
- [ ] 1. Phân cấp thực thể `projectId` -> `landingPageId` -> `formId` đã khớp và tồn tại trong Landing Hub.
- [ ] 2. Loại form khớp với phương thức gửi (`lead` -> `submitLead`, `order` -> `submitOrder`, `custom` -> `submitCustomForm`).
- [ ] 3. SDK `LPHub.init()` được cấu hình chính xác, tự động gửi `page_view`.
- [ ] 4. Nút bấm CTA chính gắn sự kiện `cta_click` với metadata rõ ràng.
- [ ] 5. Đã kiểm thử gửi form thực nghiệm: Lần 1 trả về 201, lần 2 replay trả về 200 `idempotentReplay: true`.
- [ ] 6. Không có kết nối cơ sở dữ liệu nội bộ trực tiếp hoặc Google Sheets bắc cầu.
- [ ] 7. Giao diện đáp ứng mượt mà trên cả 3 kích thước màn hình (375px, 768px, 1440px), không bị tràn viền ngang.
- [ ] 8. Mã nguồn không có lỗi TypeScript, biên dịch Vite thành công.
- [ ] 9. Áp dụng quy tắc Khử dấu vết AI (Anti-AI Footprint Cleansing): Không lạm dụng dấu gạch ngang dài (em dash), không dùng dấu phẩy Oxford kiểu máy móc trong văn phong tiếng Việt.
- [ ] 10. Gắn cờ `[CẦN XÁC MINH]` đối với các trường thông tin hoặc hình ảnh lấy từ fallback không chính thức.
- [ ] 11. Tuân thủ chuẩn Modern Web Platform (Google Standard): Tận dụng native `<dialog>`, Popover API, CSS Anchor Positioning, `fetchpriority`, `:user-invalid`, không bị bloat thư viện JavaScript thừa thãi cho các tính năng trình duyệt đã hỗ trợ.
</quality_gate>

---

<delivery_protocol>
## GIAO THỨC BÀN GIAO SẠCH (CLEAN DELIVERY PROTOCOL)
- Toàn bộ mã nguồn hoàn chỉnh được lưu tại `<output_dir>` (ví dụ: `~/Downloads/landing-pages/<project_id>/`).
- Bản đặc tả trung gian được lưu tại `_process/<project_id>/DESIGN.md`.
- Báo cáo kết quả kiểm thử được lưu tại `_process/<project_id>/test_report.md`.
- Khung chat chỉ trình bày tóm tắt ngắn gọn:
  * Trạng thái hoàn thành và đường dẫn thư mục mã nguồn.
  * Thông tin phân cấp Landing Hub (`projectId`, `landingPageId`, `formId`).
  * Kết quả kiểm định QA & App Auditor.
  * Hướng dẫn 1 lệnh để chạy thử: `cd <output_dir> && npm install && npm run dev`.
</delivery_protocol>
