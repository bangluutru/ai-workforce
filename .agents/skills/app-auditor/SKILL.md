---
name: app-auditor
display-name: Kiểm Định Ứng Dụng
description: >-
  Kiểm định toàn diện web app / landing page đang chạy: khám phá route, quét 4 khung nhìn (tràn ngang đo theo clientWidth, nội dung bị cắt, ảnh hỏng), console/network/axe-core WCAG cho MỌI route ở desktop + mobile, người dùng khó tính (chỉ trên môi trường local), đối chiếu nội dung với brief, và bắt buộc Agent soát ảnh chụp trước khi chốt báo cáo P0-P4.
  USE WHEN: Người dùng cần kiểm thử/audit giao diện web đang chạy (localhost hoặc URL), hoặc re-test sau khi sửa bug.
  DO NOT USE WHEN: Cần tự sửa mã nguồn ứng dụng (giao cho lập trình viên), hoặc kiểm định bản dịch tài liệu PDF (dùng 'dich-thuat').
trigger: Kiểm định ứng dụng, app-auditor, test ứng dụng, audit web, QA web, kiểm thử giao diện, test app, re-test bug
category: tech_ops
needs_file: false
file_filter: any
---

# Kiểm Định Ứng Dụng (App Auditor)

<goal>
Tìm lỗi THẬT mà người dùng thật sẽ gặp (chức năng, runtime, bố cục mobile, trợ năng, nội dung sai/bịa) và chứng minh
từng lỗi bằng route + viewport + bước tái hiện + ảnh chụp. Không tuyên bố "đạt" cho hạng mục chưa kiểm.
</goal>

<context>
- Kết hợp kiểm tra tất định (Playwright + axe-core offline `resources/axe.min.js`) với **soát thị giác bắt buộc của Agent**:
  script không thấy được chữ trắng trên nền trắng, bố cục xấu, nội dung lạc đề - Agent phải nhìn ảnh.
- **ZERO EXTERNAL API:** không gọi LLM API, không yêu cầu API key. Chạy cục bộ, 1 trình duyệt.
- **Autonomous Full-Run** từ khám phá đến báo cáo; điểm dừng duy nhất là bước soát ảnh (Checkpoint) do chính Agent làm.
</context>

## 🔧 Môi trường & Path Resolution

| Ký hiệu | Giá trị |
|---|---|
| `<PY>` | **`<workspace>/.venv/bin/python`** - BẮT BUỘC (Playwright chỉ có trong `.venv`; script tự báo lỗi mã 2 nếu chạy bằng python khác) |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/app-auditor/` (báo cáo `.md`) |
| `<process_dir>` | Mặc định `_process/audit_<slug>_<thời_gian>/` (đã gitignore): ảnh chụp, JSON thô |

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):** ảnh và JSON chỉ ở `<process_dir>`, báo cáo ở `<output_dir>`. Không ghi vào thư mục gốc repo.

<constraints>
## ⛔ Luật cứng
1. **An toàn môi trường thật:** chỉ bấm nút / điền form trên localhost, 127.0.0.1, *.localhost, *.test. URL staging/production: chỉ quan sát (không click, không submit) trừ khi người dùng cho phép rõ ràng -> `--allow-prod-actions`. Kể cả khi được phép, script bỏ qua nút xóa/hủy/thanh toán/đăng xuất.
2. **Không bịa lỗi:** mỗi lỗi có route, viewport, bước tái hiện, kỳ vọng, thực tế, selector/log và **ảnh chụp**. Phát hiện thị giác không có ảnh bằng chứng bị report_generator loại.
3. **Không tuyên bố đạt cho hạng mục chưa kiểm:** báo cáo ghi `N/A - chưa kiểm: <lý do>`.
4. **Không tự sửa code** của ứng dụng (vai trò kiểm định, không phải lập trình).
5. Không em dash `—`, không Oxford comma `, và`, không dấu hai chấm cuối tiêu đề trong báo cáo tiếng Việt.
</constraints>

<instructions>
## 📋 Quy trình

### Bước 0 - Tiếp nhận (Intake)
URL mục tiêu; môi trường (local / staging / production); đây có phải landing page có brief không (nếu có: lấy file brief hoặc `landing_spec.json`); người dùng có cho phép thao tác trên môi trường thật không.

### Bước 1 - Chạy audit đầy đủ (lệnh chính)
```bash
<PY> .agents/skills/app-auditor/scripts/audit_runner.py --url "<target_url>" \
     [--brief <brief.md>] [--output-dir <output_dir>] [--process-dir <process_dir>] [--max-routes 6] [--allow-prod-actions]
```
Chuỗi bên trong: `discover.py` (route, nút, form) -> `visual_sweep.py` (1440/1024/768/390, ảnh full-page, tràn ngang theo clientWidth, phần tử bị cắt, ảnh hỏng, vùng chạm) -> `deterministic_checker.py` (mọi route x desktop + mobile: console, uncaught, request thất bại, HTTP >= 400, ảnh hỏng, axe-core + mục tương phản axe không tự tính được) -> `difficult_user.py` (local: bấm liên hoàn có điền dữ liệu hợp lệ, chuỗi biên, modal, F5) -> báo cáo nháp.
Có thể chạy lẻ từng script (mỗi script có `--help`).

### Bước 2 - Soát thị giác (BẮT BUỘC - Checkpoint)
1. Mở (view_file) **từng** ảnh trong `<process_dir>/screenshots/` (danh sách in cuối lệnh Bước 1), ưu tiên `*_mobile.png` và `*_desktop_large.png`.
2. Tìm: chữ khó đọc/vô hình, chữ chồng hoặc bị cắt, khoảng trống bất thường, ảnh vỡ/méo, CTA không nổi bật, bố cục lệch, nội dung lạc đề so với brief (ví dụ form hỏi "tình trạng da" trên trang quán cà phê), các mục `[CẦN XÁC MINH]` còn trên trang.
3. Ghi mỗi phát hiện vào `<process_dir>/visual_findings.json` (mẫu `templates/visual_findings_example.json`; `screenshot` là đường dẫn ảnh thật). Không có phát hiện -> ghi `[]`.
4. Chốt báo cáo:
```bash
<PY> .agents/skills/app-auditor/scripts/report_generator.py --data <process_dir>/audit_data.json \
     --visual-findings <process_dir>/visual_findings.json [--brief <brief.md>] --output <file báo cáo ở Bước 1>
```
Báo cáo chưa qua bước này có dòng "❌ CHƯA SOÁT - báo cáo CHƯA HOÀN TẤT" và KHÔNG được bàn giao.

### Bước 3 - Phân loại & thứ tự sửa
P0 chặn luồng/crash (trần điểm 5.0) · P1 lỗi chức năng nghiêm trọng, tràn ngang mobile > 30px, gửi trùng · P2 lỗi UX/chức năng, ảnh hỏng, nội dung không có trong brief · P3 thẩm mỹ, vùng chạm nhỏ · P4 kiến nghị (chỉ khi có bằng chứng, không có mục mẫu).

### Bước 4 - Re-test sau khi sửa
```bash
<PY> .agents/skills/app-auditor/scripts/retest_runner.py --url "<url>" --type <overflow|console|debounce|a11y> --viewport <mobile|desktop_large>
```
Mã thoát 0 = VERIFIED_FIXED; 1 = lỗi còn. Debounce trên URL không phải local bị bỏ qua trừ khi có `--allow-prod-actions`.
</instructions>

<working_ledger>
`<process_dir>/`: `app_map.json`, `screenshots/*.png`, `visual_sweep.json`, `deterministic_results.json`, `difficult_user_results.json`, `audit_data.json`, `visual_findings.json`.
</working_ledger>

<quality_gate>
## ✅ Quality Gate (Checklist trước khi trả kết quả)
1. Đủ 4 khung nhìn cho mọi route đã khám phá; tràn ngang đo theo `clientWidth` (không theo `innerWidth`).
2. Console/network/axe chạy cho mọi route ở desktop + mobile.
3. Đã mở xem từng ảnh và chạy lại report_generator với `--visual-findings` (dòng "Soát thị giác" = ✅).
4. Landing page có brief: đã chạy `--brief` và Agent đã đọc mục "Đối chiếu nội dung với brief".
5. Mọi hạng mục không chạy được ghi `N/A - chưa kiểm`, không ghi "đạt".
6. **Confidence Flagging:** hành vi chưa chắc là lỗi hay ý đồ thiết kế -> gắn `[CẦN XÁC MINH: <lý do>]`; mọi lỗi kèm bằng chứng (ảnh, log, selector).
7. Không thao tác (click/submit) trên môi trường thật khi chưa có `--allow-prod-actions` từ người dùng.
</quality_gate>

<delivery_protocol>
## 🚀 Bàn giao sạch (Clean Delivery)
Khung chat chỉ gồm: điểm tổng hợp và 7 danh mục; danh sách P0/P1 kèm route + viewport + đường dẫn ảnh; thứ tự sửa khuyến nghị; các hạng mục N/A; đường dẫn báo cáo chính thức tại `<output_dir>` và thư mục ảnh tại `<process_dir>`.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

Skill này hiện **không dùng engine chung** (mã trong `scripts/` là đặc thù miền). Khi cần đọc tệp người dùng, xuất DOCX, kiểm định PDF, ffmpeg/TTS/phụ đề hoặc font: dùng engine trong `_shared/ENGINES.md`, không tự viết.
