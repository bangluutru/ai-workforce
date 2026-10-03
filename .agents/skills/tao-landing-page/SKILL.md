---
name: tao-landing-page
display-name: Tạo Landing Page
description: >-
  Tạo mã nguồn Landing Page (React + Vite + TypeScript + Tailwind) từ brief chữ, ảnh mockup, Google Stitch hoặc Figma; nội dung tách khỏi mã (content.json), màu/font theo token thương hiệu, tích hợp Landing Hub SDK, QA thật bằng build + chụp màn hình 3 khung nhìn.
  USE WHEN: Người dùng cần làm trang đích / landing page web, chuyển thiết kế hoặc brief thành trang web chạy được.
  DO NOT USE WHEN: Cần ấn phẩm in (leaflet, brochure, poster PDF - dùng 'thiet-ke'), hoặc chỉ viết nội dung chữ (dùng 'viet-bai'), hoặc chỉ kiểm định một trang có sẵn (dùng 'app-auditor').
trigger: Tạo landing page, Design to Landing, Chuyển thiết kế sang landing page, Stitch sang landing page, Figma sang landing page
category: content
needs_file: false
file_filter: doc
---

# KỸ NĂNG: TẠO LANDING PAGE

<goal>
Trang đích chạy được, đúng thương hiệu và đúng nội dung của người dùng: không câu chữ mặc định, không số liệu bịa,
màu/font lấy từ thiết kế/brief, build sạch, đã chụp và soát 375/768/1440px, form nối Landing Hub đúng hợp đồng v1.0.
</goal>

<context>
## Nguyên tắc
1. **ZERO EXTERNAL API cho suy luận:** không gọi LLM API, không yêu cầu API key. Script chỉ xử lý dữ liệu, build, kiểm thử.
   Landing Hub là API sản phẩm (được phép) - nhưng mọi thao tác GHI lên Hub cần token của người dùng và chỉ chạy sau `--dry-run`.
2. **Autonomous Full-Run** từ brief đến QA; chỉ dừng khi thiếu nguồn thiết kế/brief hoặc khi cần người dùng xác nhận đăng ký Hub thật.
3. **Môi trường:** script Playwright (`qa_runner.py`) chạy bằng **`<workspace>/.venv/bin/python`**; script khác chạy được bằng `python3`. Không dùng `npx` tải gói từ mạng.
4. **BẢO VỆ CODEBASE (Anti-Repo Bloat):** mã nguồn trang ở `<output_dir>` (mặc định `~/Downloads/AIWF_Output/landing-pages/<project_id>/`); spec, báo cáo, ảnh QA ở `_process/<project_id>/` (đã gitignore). Không tạo dự án trong repo AIWF.
5. **Landing Hub:** repo riêng ngoài AIWF (hiện tại `~/.gemini/antigravity-ide/scratch/xtools/landing-hub`, chạy `npm run server` -> `http://localhost:3001`). Tóm tắt hợp đồng: `resources/integration-contract-v1.md`, `resources/api-reference-v1.md`.
</context>

<constraints>
## ⛔ Luật cứng
1. **Không bịa nội dung:** mọi câu chữ, số liệu, giá, địa chỉ, giấy phép, đánh giá, "hơn N khách hàng", "số 1", "tiêu chuẩn Nhật"... phải có trong brief/thiết kế. Thiếu -> `[CẦN XÁC MINH: ...]` (hiển thị tô vàng trên trang). Câu chữ rủi ro phải ghi nguồn trong `claims_evidence`.
2. **Không hallucinate thiết kế:** Stitch/Figma không đọc được -> báo lỗi, không dùng dữ liệu mẫu (`--allow-mock` chỉ để test script).
3. **Không sửa component để chèn câu chữ** - chỉ sửa `landing_spec.json` rồi build lại. Component chỉ dùng class `brand-*`.
4. **Không secret trong client**, không Firestore/Google Sheets trực tiếp, không đổi tên sự kiện chuẩn; `form_submit`/`order_created`/`purchase` do máy chủ ghi.
5. **Không bàn giao khi qa_runner FAIL hoặc khi chưa mở xem ảnh chụp.** Không ghi "đã kiểm thử form" nếu E2E là "CHƯA KIỂM".
</constraints>

<instructions>
## QUY TRÌNH

### Bước 0 - Intake (Tọa độ đầu vào)
Xác định: nguồn (brief chữ | ảnh mockup | Stitch | Figma), `project_id`, `landingPageId`, `formId`, loại form (lead/order/custom), `<output_dir>`.
```bash
python3 .agents/skills/tao-landing-page/scripts/input_router.py "<brief | url | đường dẫn ảnh | tệp brief>" --json
```
**Đọc tệp người dùng:** brief là tệp (PDF/PPTX/DOCX/HTML/DOC/ODT/RTF/EPUB/MD/TXT) → router tự chạy `scripts/doc_ingest.py` (thư mục `~/Downloads/AIWF_Output/_ingest/landing_<tên tệp>`) và trả `text_brief` + `brief_md`: đọc `source.md` đó, không đọc thẳng tệp gốc. Mã thoát: `0` dùng `source.md` · `3` có trang scan → đọc ảnh `ocr_pages` bằng thị giác (nháp OCR CHƯA kiểm chứng; trang là mockup → xử lý như fallback_image) · `2` (`unreadable`) hỏi người dùng đúng điều trong `message` (mật khẩu/DRM/hỏng/sai đường dẫn), không đoán · `4` (`missing_dependency`) cài theo `message` (`bash scripts/auto-setup.sh`). Ảnh mockup vẫn là `fallback_image`.

### Bước 1 - Lập `landing_spec.json` (nguồn sự thật duy nhất của trang)
Mẫu đầy đủ: `templates/landing_spec_example.json` (quán cà phê từ brief chữ). Lưu tại `_process/<project_id>/landing_spec.json`.
- **text_brief:** chép nguyên văn câu chữ từ brief; tự chọn bảng màu hợp ngành/brief (ghi lý do vào `source.palette_reason`); font chỉ `Be Vietnam Pro` / `Spectral`.
- **fallback_image (ảnh mockup):** đo màu bằng mắt từ ảnh, gắn `source.flag = "[CẦN XÁC MINH - FIDELITY FALLBACK]"`.
- **Stitch:** `python3 .agents/skills/tao-landing-page/scripts/stitch_adapter.py --project "<id số>" --json` (lỗi -> dừng, hướng dẫn `resources/mcp_setup_guides.md`).
- **Figma:** dùng công cụ Figma MCP trong IDE (get_design_context) rồi tự ghi spec; `figma_adapter.py --check-only` để kiểm tra quyền.
- Loại section hỗ trợ: `cards`, `pricelist`, `faq`, `text`; form: trường lấy đúng theo brief (`key,label,type,required,options`). Form `order` bắt buộc `product.unitPrice` do người dùng cung cấp.

Kiểm tra spec (tương phản màu WCAG, trường thiếu, câu chữ rủi ro):
```bash
python3 .agents/skills/tao-landing-page/scripts/landing_builder.py --spec _process/<project_id>/landing_spec.json --validate-only
```
`DESIGN.md` (tùy chọn, để người dùng duyệt): `design_interpreter.py --input <spec> --output _process/<project_id>/DESIGN.md`.

### Bước 2 - Landing Hub (dry-run trước)
```bash
python3 .agents/skills/tao-landing-page/scripts/hub_integrator.py --project-id <id> --lp-id <lp> --form-id <form> \
  --form-type lead --lp-url <url thật> --allowed-domain <domain thật> --fields-json '<fields>' --dry-run
```
Hub local đang chạy và người dùng đồng ý -> chạy lại không `--dry-run`, token qua `LPHUB_ADMIN_TOKEN`, thêm `--output _process/<project_id>/hub_config.json`.
Chưa có Hub -> tự ghi `hub_config.json` `{ "config": { projectId, landingPageId, formId, formType } }` và ghi chú "chưa đăng ký Hub".

### Bước 3 - Sinh dự án
```bash
python3 .agents/skills/tao-landing-page/scripts/landing_builder.py --spec _process/<project_id>/landing_spec.json \
  --hub-config-json _process/<project_id>/hub_config.json --target-dir <output_dir>
cd <output_dir> && npm install
```
Builder chép template tĩnh, ghi `src/content.json`, `src/theme.css`, font/ảnh tự host, `.env.qa`. Production: tạo `.env.production` với `VITE_LPHUB_URL=https://...` (xem `.env.production.example`); `npm run build` sẽ dừng nếu URL rỗng/localhost.

### Bước 4 - QA thật + soát ảnh (Checkpoint bắt buộc)
```bash
.venv/bin/python .agents/skills/tao-landing-page/scripts/qa_runner.py --project-dir <output_dir> \
  --report-dir _process/<project_id>/qa [--hub-api-url http://localhost:3001 --project-id .. --lp-id .. --form-id .. --form-type ..]
```
1. Mã thoát 1 -> sửa spec/template -> build lại -> chạy lại.
2. **Mở (view_file) từng ảnh** trong `_process/<project_id>/qa/screenshots/` và điền mục "Nhận xét thị giác" trong `qa_report.md` theo `standards/quality_gates_checklist.md` mục B. Lỗi thẩm mỹ/nội dung -> sửa và lặp (tối đa 3 vòng).
3. Gửi form E2E chỉ chạy với Hub localhost (hoặc `--allow-test-data` khi người dùng cho phép ghi bản ghi "QA TEST").
4. Sau khi deploy thật: chạy skill `app-auditor` trên URL công khai.
</instructions>

<working_ledger>
`_process/<project_id>/`: `landing_spec.json`, `build_report.json`, `hub_config.json`, `qa/qa_report.md|json`, `qa/screenshots/*.png`.
</working_ledger>

<quality_gate>
## CHECKLIST TRƯỚC KHI BÀN GIAO
- [ ] `build_report.json` status OK; mọi `[CẦN XÁC MINH]` đã liệt kê cho người dùng (**Confidence Flagging**).
- [ ] `qa_runner.py` thoát 0 (bằng chứng: `qa_report.json`).
- [ ] Đã mở xem 3 ảnh chụp và ghi nhận xét vào `qa_report.md`.
- [ ] Trạng thái gửi form E2E báo đúng sự thật (ĐẠT / CHƯA KIỂM + lý do).
- [ ] Không em dash `—`, không Oxford comma `, và` trong nội dung tiếng Việt.
- [ ] Mã nguồn nằm ở `<output_dir>`, không có file trong repo AIWF ngoài `_process/`.
</quality_gate>

<delivery_protocol>
## BÀN GIAO SẠCH (Clean Delivery)
Khung chat chỉ gồm: đường dẫn dự án + 3 ảnh chụp; `projectId/landingPageId/formId` và trạng thái đăng ký Hub; kết quả QA (số FAIL/WARN, E2E ĐẠT hoặc CHƯA KIỂM); danh sách `[CẦN XÁC MINH]`; lệnh chạy thử `cd <output_dir> && npm install && npm run dev`.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `scripts/doc_ingest.py` | Đọc tệp người dùng (PDF/DOCX/XLSX/PPTX/ảnh…) thành `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` |
| `doc_ingest_bridge` | Gọi doc_ingest từ Python: `run_ingest`, `explain`, `ocr_page_paths`, `default_ingest_dir` | import trong `scripts/input_router.py` |
| `_shared/fonts/` | Font OFL tự host cho landing (chép vào `public/fonts`) | `landing_builder.py` (SHARED_FONTS) |
