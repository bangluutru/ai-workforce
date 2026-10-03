---
name: tu-van-thue
display-name: Tư Vấn Thuế
description: >-
  Cổng tư vấn và tính toán thuế Việt Nam cho cá nhân, hộ kinh doanh và doanh nghiệp: thuế TNCN (quyết toán, Gross-Net, giảm trừ gia cảnh, eTax Mobile, bất động sản, BHXH một lần), thuế TNDN, GTGT, TTĐB, thuế hộ kinh doanh, hóa đơn điện tử, quản lý thuế (tiền chậm nộp, hoàn thuế, khai thuế) và xuất Excel 100% công thức động Live Formulas. Mọi tham số thuế truy nguyên về văn bản quy phạm kèm trạng thái kiểm chứng.
  USE WHEN: Người dùng cần tính hoặc tư vấn thuế (TNCN, TNDN, GTGT, TTĐB, hộ kinh doanh), hóa đơn điện tử, tiền chậm nộp, hoàn thuế, kê khai, hoặc lập bảng tính thuế.
  DO NOT USE WHEN: Lập báo cáo tài chính hoặc sổ kế toán (dùng 'bao-cao-kt'), tư vấn pháp lý tổng quát hoặc tranh chấp, hình sự thuế (dùng 'tu-van-phap-luat'), thuế và pháp luật Nhật Bản (dùng 'tu-van-phap-luat-nhat-ban'), soạn văn bản hành chính (dùng 'xu-ly-van-phong'). Chuyển giá, thuế tối thiểu toàn cầu chỉ ở mức hướng dẫn, không tính số.
trigger: Tư vấn thuế, thuế TNDN, thuế GTGT, thuế hộ kinh doanh, hóa đơn điện tử, tiền chậm nộp, Tư vấn thuế TNCN, quyết toán thuế, giảm trừ gia cảnh, lương gross net, eTax Mobile
category: legal_finance
needs_file: false
file_filter: doc
---

# Tư Vấn Thuế Việt Nam (Router + Live Engine)

> Nhận câu hỏi, xác định loại thuế và ngày phát sinh nghĩa vụ, đối soát tham số có nguồn, tính bằng script Python, xuất báo cáo và Excel Live Formulas.

<goal>
Trả lời đúng câu hỏi thuế của người dùng bằng con số tính từ script, có căn cứ pháp lý truy nguyên được, kèm disclaimer. Không tư vấn trốn thuế; chỉ nêu phương án tối ưu hợp pháp.
</goal>

<constraints>
- Zero External API: lập luận do Agent đảm nhiệm. Script chỉ xử lý dữ liệu, không gọi LLM, không cần API key.
- Cấm tính nhẩm thuế bằng LLM. Mọi con số lấy từ `scripts/` (xem mục CLI).
- Confidence Flagging và Evidence Verifier: cấm bịa tham số, mọi số phải có bằng chứng trích dẫn nguyên văn kèm tọa độ Điều/Khoản. Tham số trong `standards/*.json` có trường `verification_status`. Trạng thái `CORROBORATED` phải kèm cờ `[CẦN XÁC MINH]` trong báo cáo. Trạng thái `SECONDARY_ONLY` hoặc `UNVERIFIED` không được dùng để tính.
- Output vào `<output_dir>` (mặc định `~/Downloads/AIWF_Output/`), thư mục tạm `_process/` đã gitignore. Không ghi file kết quả vào repo.
- Excel dùng 100% công thức sống; báo cáo quét `scripts/claim_guard.py` đạt 0 vi phạm (Luật R5); không em-dash, không Oxford comma, không dấu hai chấm cuối heading.
- Autonomous Full-Run: tự chạy đến khi xong. Chỉ dừng hỏi khi thiếu dữ kiện quyết định số thuế (dùng `ask_question`, chỉ hỏi phần còn thiếu).
</constraints>

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):** `<output_dir>` mặc định `~/Downloads/AIWF_Output/` hoặc nơi người dùng chỉ định. `<research_dir>` = `<output_dir>/tax_consulting_[chủ_đề]/`, `<process_dir>` = `_process/tax_[chủ_đề]_[timestamp]/`. TUYỆT ĐỐI KHÔNG tạo báo cáo hoặc bảng tính trong thư mục gốc repo.

## 1. Định tuyến module

Xác định (a) loại thuế, (b) **ngày phát sinh nghĩa vụ hoặc kỳ tính thuế** (luật đổi hiệu lực 2025-2026, chọn văn bản theo ngày), (c) đối tượng nộp thuế.

| Câu hỏi thuộc về | Đọc tiếp | Lệnh tính |
|---|---|---|
| Thuế TNCN: lương, quyết toán, Gross-Net, giảm trừ, freelancer, BĐS, BHXH một lần, chứng khoán phái sinh | `resources/tncn/quy-trinh-tncn.md` | `tax_calculator.py` |
| Thuế GTGT (khấu trừ, trực tiếp, giảm 8%) | `resources/gtgt/huong-dan-gtgt.md` | `tax_cli.py gtgt`, `gtgt-direct` |
| Thuế TNDN (thuế suất theo doanh thu, miễn dưới 1 tỷ, kết chuyển lỗ) | `resources/tndn/huong-dan-tndn.md` | `tax_cli.py tndn` |
| Hộ kinh doanh, cá nhân kinh doanh (GTGT + TNCN) | `resources/hkd/huong-dan-hkd.md` | `tax_cli.py hkd` |
| Hóa đơn điện tử | `resources/hoa-don/huong-dan-hoa-don.md` | `tax_cli.py hoa-don` |
| Quản lý thuế: tiền chậm nộp, hạn nộp, gia hạn 2026 | `resources/core/deadline-tracker.md`, `resources/advanced/huong-dan-nang-cao.md` | `tax_cli.py cham-nop` |
| Thuế tiêu thụ đặc biệt | `resources/ttdb/huong-dan-ttdb.md` | `tax_cli.py ttdb` |
| Nhà thầu nước ngoài (phần TNDN) | `resources/nha-thau/huong-dan-nha-thau.md` | `tax_cli.py nha-thau` |
| Xuất nhập khẩu, đất, tài nguyên, môi trường | `resources/xnk/`, `resources/dat-tai-nguyen-moi-truong/` | Chỉ hướng dẫn, không tính |
| Chuyển giá, thuế tối thiểu toàn cầu, ưu đãi dự án | `resources/advanced/huong-dan-nang-cao.md` | Chỉ định hướng |

Câu hỏi đa thuế (ví dụ hộ kinh doanh cần cả GTGT, TNCN, hóa đơn): chạy từng lệnh, gộp kết quả. Wizard chọn loại thuế: nhánh `tax_type_routing` trong `resources/questionnaire_tree.json`. Tra cứu nguyên văn: `resources/core/lookup_portals.md`, chỉ mục `resources/legal_index.json`, kiểm độ mới `scripts/check_legal_freshness.py`.

## 2. Quy trình chung và tiếp nhận đầu vào (Intake)

1. **Pre-fill:** quét dữ liệu người dùng đã nêu; không hỏi lại cái đã có. Đủ dữ liệu thì bỏ qua wizard.
2. **Tệp đầu vào** (chứng từ, tờ khai, hóa đơn): không đọc nhị phân trực tiếp. Chạy `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json`, đọc `source.md` + `manifest.json`. Số chỉ có trong nháp OCR gắn `[CẦN XÁC MINH]`.
3. **Chọn bộ tham số** theo ngày: `standards/*.json`. Ghi rõ văn bản, điều khoản, trạng thái kiểm chứng vào báo cáo.
4. **Tính** bằng CLI (mục 3), lấy JSON.
5. **Báo cáo** theo `templates/tax_report_template.md`; **Excel** TNCN bằng `export_tax_sheet.py` rồi `verify_tax_sheet.py`; các module khác bằng `export_tax_module.py` rồi `verify_tax_module.py` (chỉ giao khi `✅ ĐẠT`). Sheet "Thông số" ghi văn bản căn cứ và trạng thái kiểm chứng; báo cáo phải nêu các cờ `[CẦN XÁC MINH]` do script trả về.
6. **Bàn giao sạch:** chat chỉ có tóm tắt 3-5 ý, link file, disclaimer.

## 3. CLI Contract

| Script | Mục đích | Ghi chú |
|---|---|---|
| `scripts/tax_calculator.py` | TNCN: Gross-Net, quyết toán, BĐS, BHXH, vãng lai | Tương thích ngược; xem `resources/tncn/quy-trinh-tncn.md` mục 7 |
| `scripts/tax_cli.py` | `hkd`, `tndn`, `gtgt`, `gtgt-direct`, `cham-nop`, `hoa-don`, `ttdb`, `nha-thau`, `params` | `--json`, `--on YYYY-MM-DD`; mã 0 đạt, 1 lỗi tham số hoặc đầu vào, 2 lỗi không mong đợi |
| `scripts/export_tax_sheet.py`, `verify_tax_sheet.py` | Excel TNCN Live Formulas và kiểm tra | Mã 0 = ĐẠT |
| `scripts/export_tax_module.py`, `verify_tax_module.py` | Excel Live Formulas cho tndn, hkd, gtgt, ttdb, nha-thau, cham-nop | Tính lại bằng LibreOffice, so với engine |
| `scripts/check_legal_freshness.py` | Kiểm độ mới chỉ mục văn bản, tham số sắp hết hiệu lực | Ngoại tuyến |

Lệnh ví dụ: `python3 .agents/skills/tu-van-thue/scripts/tax_cli.py hkd --activity phan_phoi=2e9 --json` và `python3 .agents/skills/tu-van-thue/scripts/tax_calculator.py --gross 30000000 --dependents 1 --json`

## 4. Quality Gate

- [ ] Đã xác định loại thuế, ngày phát sinh, đối tượng nộp thuế (hoặc ghi giả định).
- [ ] Mọi tham số dùng có `verification_status` hợp lệ; `CORROBORATED` có cờ `[CẦN XÁC MINH]`.
- [ ] Số trong báo cáo khớp JSON của script và file Excel; `verify_tax_sheet.py` đạt.
- [ ] Báo cáo qua `claim_guard.py` đạt, không dùng từ over-claim ("tối ưu thuế tuyệt đối", "chắc chắn không bị phạt").
- [ ] Có disclaimer bên dưới.

<delivery_protocol>
```
⚠️ LƯU Ý PHÁP LÝ:
Thông tin tư vấn dựa trên quy định pháp luật thuế Việt Nam tại thời điểm tra cứu và mang tính tham khảo, đối soát sơ bộ.
Không thay thế kết luận hoặc quyết định chính thức của cơ quan thuế. Vui lòng đối chiếu văn bản gốc và hỏi cơ quan thuế khi cần.
```
</delivery_protocol>

## 🧩 Engine dùng chung (Luật R7)

> Gọi lại, KHÔNG viết lại. Tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước khi thêm code.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `scripts/doc_ingest.py` | Đọc tệp người dùng thành `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` |
| `scripts/claim_guard.py` | Quét over-claim Luật R5 | `python3 scripts/claim_guard.py --input <file>` |
