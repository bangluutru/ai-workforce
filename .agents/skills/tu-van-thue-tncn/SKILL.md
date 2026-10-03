---
name: tu-van-thue-tncn
display-name: Tư Vấn Thuế TNCN
description: >-
  Cổng tư vấn và tính toán thuế thu nhập cá nhân (TNCN) Việt Nam theo luật thuế hiện hành; hỗ trợ quy đổi lương Gross - Net, quyết toán năm, giảm trừ gia cảnh, hoàn thuế eTax Mobile, thuế bất động sản, BHXH 1 lần, xuất file Excel 100% công thức động Live Formulas.
  USE WHEN: Người dùng cần tính thuế TNCN, quyết toán thuế, tối ưu giảm trừ gia cảnh, quy đổi Gross-Net hoặc lập bảng tính thuế cá nhân.
  DO NOT USE WHEN: Thuế TNDN, thuế GTGT doanh nghiệp hoặc kế toán công ty (dùng 'bao-cao-kt' hoặc 'tu-van-phap-luat'), hoặc soạn thảo văn bản hành chính (dùng 'xu-ly-van-phong').
trigger: Tư vấn thuế TNCN, tính thuế thu nhập cá nhân, quyết toán thuế, giảm trừ gia cảnh, lương gross net, eTax Mobile
category: legal_finance
needs_file: false
file_filter: doc
---

# Cổng Tư Vấn Thuế Thu Nhập Cá Nhân (TNCN) — Interactive Portal & Live Engine (Gemini 3.8 Multi-Agent)

> Tiếp nhận câu hỏi & Phỏng vấn thu thập dữ liệu (5 Trục Tọa độ) → Đối soát SOT Pháp quy 2026 → Động cơ Tính toán Không sai số (Python Engine) → Báo cáo Cá nhân hóa & Bảng tính Excel Live Formulas.

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Skill này chạy hoàn toàn bằng khả năng tích hợp sẵn của Antigravity IDE (Gemini 3.8) kết hợp các atomic scripts nội bộ.
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI, Gemini API bên ngoài) hoặc yêu cầu API key để vận hành.
> - Toàn bộ năng lực lập luận, đối chiếu văn bản và tư vấn là của chính Agent (LLM nội bộ).
> - **CƠ CHẾ TƯƠNG TÁC 2 CHIỀU:** Khi người dùng cung cấp thiếu dữ kiện trọng yếu, Agent **BẮT BUỘC DỪNG LẠI** để phỏng vấn thu thập thông tin bằng khung câu hỏi điền nhanh trong chat. Khi đã có đủ dữ liệu, Agent tự động chạy một mạch (Autonomous Full-Run) đến khi xuất bản xong file và bàn giao kết quả.

---

## 1. Triết lý Vận hành Cốt lõi (Reasoning Engine)

1. **Cổng tư vấn tương tác (Interactive Intake First):** Không tự động sinh báo cáo mẫu giả định khi chưa biết rõ câu hỏi và số liệu của người dùng. Luôn phỏng vấn thu thập dữ liệu chính xác trên 5 trục tọa độ trước khi tính toán.
2. **Pháp lý thuế 2026 là Nguồn Sự Thật Duy Nhất (SSOT):** Mọi con số, thuế suất, định mức giảm trừ phải truy nguyên chính xác về văn bản quy phạm pháp luật (Luật 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC, NĐ 141/2026/NĐ-CP, Luật BHXH 2024).
3. **Cấm tính nhẩm và cấm bịa số liệu (Zero-Hallucination):** Tuyệt đối cấm tính nhẩm biểu thuế lũy tiến bằng LLM. Bắt buộc chạy script `scripts/tax_calculator.py` để đảm bảo độ chính xác 100% về số học cho cả Gross sang Net, Net sang Gross, Quyết toán năm, BĐS và BHXH.
4. **Tiêu chuẩn Dữ liệu sống (Live Formulas):** Bảng tính Excel xuất cho người dùng phải sử dụng 100% công thức Excel động (`SUM`, `MIN`, `MAX`, `IF`). Cấm ghi số chết vào ô kết quả.
5. **Cơ chế Sổ cái làm việc vật lý N+1:** Mọi bước phân tích, đối chiếu đều được lưu vết minh bạch tại thư mục nghiên cứu.
6. **Cảnh báo và Disclaimer:** Kỹ năng hỗ trợ tính toán, đối soát và tư vấn nghiệp vụ thuế; không thay thế kết luận thanh kiểm tra chính thức từ Cơ quan Thuế.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định thư mục lưu trữ đầu ra trước khi khởi tạo tiến trình tư vấn:

| Placeholder | Quy ước xác định đường dẫn |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<research_dir>` | `<output_dir>/tax_consulting_[chủ_đề]/` |
| `<process_dir>` | `_process/tax_[chủ_đề]_[timestamp]/` (được bảo vệ bởi `.gitignore`) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Cho phép người dùng chọn hoặc chỉ định thư mục sẽ lưu file đầu ra.
> - TUYỆT ĐỐI KHÔNG tạo thư mục kết quả hoặc file báo cáo/bảng tính trực tiếp trong thư mục gốc của repository AIWF để tránh làm phình to kho Git.
> - Toàn bộ các file nhật ký phase (`tax_phase_{N+1}.md`), báo cáo tư vấn (`tax_report_[chủ_đề].md`) và bảng tính Excel (`Bang_Tinh_Thue_TNCN_[chủ_đề].xlsx`) PHẢI được lưu trong `<research_dir>` (tức `<output_dir>/tax_consulting_[chủ_đề]/`) .

---

## 2. Bước 0: Giao Thức Kịch Bản Trắc Nghiệm Tương Tác Tự Động (Interactive Questionnaire Wizard Protocol)

> Thay vì bắt người dùng phải đọc nhiều chữ và tự gõ dài dòng trong chat, hệ thống vận hành theo cơ chế **Kịch bản Trắc nghiệm Tương tác Tự động (Questionnaire Wizard)** kết hợp công cụ hộp thoại bản địa `ask_question`.

### Quy trình điều hướng kịch bản thông minh:

#### BƯỚC 0.0: BÓC TÁCH DỮ LIỆU CÓ SẴN & PRE-FILL THÔNG MINH (SMART PRE-FILL FIRST)
> [!IMPORTANT]
> **QUY TẮC CHỐNG LÃNG PHÍ THỜI GIAN NGƯỜI DÙNG:**
> 1. **Tự động bóc tách:** Khi người dùng gửi câu hỏi, Agent PHẢI chủ động quét các thông số người dùng đã cung cấp sẵn (ví dụ: số tiền lương, số người phụ thuộc, hợp đồng, đóng BHXH, bán nhà, rút BHXH).
> 2. **Pre-fill vào hồ sơ:** Lưu trữ ngay các giá trị đã biết vào tọa độ dữ liệu.
> 3. **BỎ QUA các câu hỏi đã có đáp án:** Tuyệt đối KHÔNG hỏi lại câu hỏi mà người dùng đã nêu rõ ràng trong prompt.
> 4. **Trường hợp ĐÃ ĐỦ DỮ LIỆU TRỌNG YẾU:** Nếu người dùng đã cung cấp đủ thông tin cốt lõi để tính toán (ví dụ: mức lương và số người phụ thuộc), Agent **BỎ QUA TOÀN BỘ WIZARD**, lập tức chạy script tính toán và xuất kết quả.
> 5. **Chỉ hỏi phần còn thiếu:** Nếu thiếu dữ kiện quyết định số thuế (ví dụ: chưa rõ lương Gross hay Net, chưa rõ thời gian đóng BHXH), chỉ gọi `ask_question` đúng câu hỏi còn thiếu đó, KHÔNG restart wizard từ đầu.

#### BƯỚC 0.0b: TỆP NGƯỜI DÙNG GỬI (CHỨNG TỪ KHẤU TRỪ, PHIẾU LƯƠNG, TỜ KHAI, XÁC NHẬN BHXH)
**Đọc tệp người dùng** (PDF/ảnh/DOCX/XLSX): không đọc thẳng tệp nhị phân. Từ gốc repo chạy `.venv/bin/python scripts/doc_ingest.py "<tệp>" ["<tệp 2>" ...] --out ~/Downloads/AIWF_Output/_ingest/<tên_việc> --json` rồi đọc `source.md` + `manifest.json` (`warnings`). Mã thoát: `0` dùng `source.md` · `3` có trang scan/ảnh chụp → đọc ảnh `ocr_pages/*.png` bằng thị giác (nháp OCR trong `source.md` CHƯA kiểm chứng) · `2` hỏi người dùng đúng điều trong `manifest.message` (mật khẩu/hỏng), không đoán · `4` thiếu phụ thuộc → cài theo `manifest.message` (`bash scripts/auto-setup.sh`).
- Mọi số trên chứng từ (tổng thu nhập chịu thuế, số thuế TNCN đã khấu trừ, bảo hiểm bắt buộc, kỳ trả thu nhập, MST tổ chức trả) PHẢI đọc từ `source.md` (mã 0) hoặc từ ảnh trang trong `ocr_pages/` (mã 3). KHÔNG đoán, KHÔNG suy từ mức lương, KHÔNG chép nguyên bản nháp OCR.
- Ghi nguồn từng số vào `tax_phase_{N+1}.md` dạng `<tên tệp>, trang N, dòng/ô "<tên trường trên chứng từ>"` (Evidence Verifier) rồi mới map sang cờ của `tax_calculator.py`.
- Số chỉ có trong nháp OCR, ảnh mờ, chữ bị che → gắn `[CẦN XÁC MINH]` và đọc lại cho người dùng xác nhận trước khi tính. Nhiều nơi trả thu nhập → mỗi chứng từ một dòng, cộng có nguồn từng dòng.

#### BƯỚC 0.1: KÍCH HOẠT CÂU HỎI GỐC (KHI YÊU CẦU CHUNG CHUNG)
Chỉ khi người dùng kích hoạt chung chung (gõ *"Tư vấn thuế TNCN"*, *"Quyết toán thuế"* mà không kèm dữ liệu cụ thể):
1. Agent gọi công cụ `ask_question` với 6 chuyên đề lựa chọn từ `resources/questionnaire_tree.json`:
   - *1. Quyết toán thuế TNCN cuối năm & eTax Mobile*
   - *2. Tiền lương Gross <-> Net & Giảm trừ gia cảnh*
   - *3. Thuế chuyển nhượng Bất động sản (2%) & Miễn thuế*
   - *4. Tư vấn rút BHXH một lần theo Luật BHXH 2024 & Lương hưu*
   - *5. Thuế Freelancer, Hộ kinh doanh & Khấu trừ 10%*
   - *6. Đăng ký người phụ thuộc & Mã số thuế*

#### BƯỚC 0.2: CHUYỂN TIẾP THEO NHÁNH KỊCH BẢN (CHỈ HỎI CÂU THIẾU)
Khi chuyển tiếp:
1. Agent tra cứu danh sách câu hỏi của nhánh tương ứng.
2. Bỏ qua các câu mà dữ liệu đã được xác định ở Bước 0.0.
3. Chỉ gọi `ask_question` cho các câu còn thiếu.
4. **HỖ TRỢ NHẬP SỐ TIỀN CỤ THỂ:** Người dùng có thể click chọn nhanh các mốc định sẵn HOẶC nhập số tiền/giá trị chính xác vào ô viết tự do (Write-in input).

#### BƯỚC 0.3: CÂU HỎI CUỐI CÙNG — GHI CHÚ THÊM CỦA NGƯỜI DÙNG (FINAL NOTES)
Câu hỏi cuối cùng của mọi nhánh kịch bản luôn là:
`"Bạn có ghi chú hoặc yêu cầu đặc biệt nào thêm cho hồ sơ này không?"`
- Tùy chọn 1: `(Khuyến nghị) Không có ghi chú thêm, tiến hành tra cứu và lập báo cáo ngay`
- Tùy chọn 2: `Tôi có ghi chú cụ thể (vui lòng điền vào ô bên dưới)` -> Người dùng có thể điền các mong muốn cá nhân hóa.

#### BƯỚC 0.4: BÀN GIAO CHO ĐỘNG CƠ TỰ CHỦ (AUTONOMOUS FULL-RUN HANDOFF)
Ngay sau khi nhận câu trả lời cho câu hỏi cuối cùng:
1. Ánh xạ trực tiếp các câu trả lời thành cờ tham số của `tax_calculator.py` và `export_tax_sheet.py` (bảng ánh xạ ở mục 7). Hai thông số luôn phải xác định trước khi tính:
   - **Năm thuế (`--year`)**: quyết toán thu nhập năm 2025 (nộp hồ sơ trong năm 2026) dùng `--year 2025` (biểu 7 bậc, giảm trừ 11tr/4,4tr). Thu nhập phát sinh từ 01/01/2026 dùng `--year 2026`. Không bao giờ áp quy tắc 2026 cho quyết toán năm 2025.
   - **Vùng nơi làm việc (`--region I|II|III|IV`)**: quyết định trần đóng BHTN (20 x lương tối thiểu vùng). Lương trên ~74 triệu mà không biết vùng thì hỏi; nếu người dùng không trả lời, ghi giả định `[CẦN XÁC MINH]` trong báo cáo.
   - Không có giá trị mặc định cho số người phụ thuộc, thuế đã khấu trừ, bảo hiểm đã đóng, số năm đóng BHXH. Thiếu thì hỏi, không tự điền.
2. Agent tự động kích hoạt cơ chế **Autonomous Full-Run**, chạy liên tục một mạch qua Bước 1, Bước 2, Bước 3, Bước 4 để tra cứu SSOT, tính toán chính xác, xuất Excel Live Formulas và tạo Báo cáo tư vấn chuyên sâu mà không dừng xin phép giữa chừng.

---

## 3. Bước 1: Tra Cứu & Đối Soát Source of Truth (SOT)

Nạp dữ liệu từ thư mục `resources/` tương ứng với đúng bài toán của người dùng:

| Nhóm bài toán người dùng hỏi | Tài liệu tham chiếu trong `resources/` | Căn cứ pháp lý cốt lõi |
|---|---|---|
| Tiền lương Gross sang Net / Net sang Gross | `resources/tong-quan-thue.md`<br>`resources/vi-du-tinh-thue.md` | Luật 109/2025/QH15 (Đ.22)<br>NQ 110/2025/UBTVQH15<br>NĐ 161/2026/NĐ-CP (Lương cơ sở 2,53tr) |
| Quyết toán cuối năm & Hoàn thuế eTax Mobile | `resources/sop-quyet-toan.md`<br>`resources/deadline-tracker.md` | Luật Quản lý thuế số 38/2019/QH14<br>TT 80/2021/TT-BTC, TT 87/2026/TT-BTC |
| Freelancer, KOL, Bán hàng online, Khấu trừ 10% | `resources/freelancer-guide.md`<br>`resources/thue-khoan-guide.md` | TT 87/2026/TT-BTC (Ngưỡng 5tr)<br>NĐ 141/2026/NĐ-CP (Ngưỡng 1 tỷ) |
| Chuyển nhượng BĐS, Nhà đất duy nhất | `resources/bat-dong-san-guide.md` | Luật 109/2025/QH15<br>NĐ 253/2026/NĐ-CP (Điều 18, Điều 19) |
| BHXH rút 1 lần & Trợ cấp thất nghiệp | `resources/bhxh-rut-mot-lan-guide.md`<br>`resources/bhtn-tro-cap-guide.md` | Luật BHXH 2024 (Số 41/2024/QH15)<br>Luật Việc làm 2025 |
| Câu hỏi nghiệp vụ khác & Kiểm tra tài khoản | `resources/faq.md` | Tổng cục Thuế & Bộ Tài chính |

---

## 4. Bước 2: Động Cơ Tính Toán Không Sai Số & Sinh Excel Live Formulas

> [!IMPORTANT]
> **QUY TẮC BẮT BUỘC: CHẠY PYTHON ENGINE ĐỂ TÍNH TOÁN CHÍNH XÁC**
> Tuyệt đối không tự tính nhẩm các phép toán thuế lũy tiến phức tạp. Phải gọi script `scripts/tax_calculator.py` tương ứng với bài toán của người dùng:

1. **Bài toán 1 — Quy đổi Lương Net sang Gross:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --year <năm> --region <vùng> --net <số_tiền_net> --dependents <số_npt> --json
   ```
2. **Bài toán 2 — Tính Lương Gross sang Net:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --year <năm> --region <vùng> --gross <số_tiền_gross> --dependents <số_npt> --medical <y_tế_bình_quân_tháng> --education <học_phí_bình_quân_tháng> --pension <hưu_trí_tháng> --json
   ```
3. **Bài toán 3 — Quyết toán thuế năm (Thu nhập 2 nơi trở lên):**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --year <năm_quyết_toán> --settlement-income <tổng_thu_nhập_năm> --settlement-insurance <tổng_bh_đã_nộp> --dependents <số_npt> --settlement-tax-withheld <số_thuế_các_nơi_đã_trừ> --json
   ```
4. **Bài toán 4 — Thuế chuyển nhượng Bất động sản:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --bds-value <giá_chuyển_nhượng> [--sole-owner --ownership-days <số_ngày>] [--relative] --json
   ```
5. **Bài toán 5 — Rút BHXH một lần vs Bảo lưu lương hưu:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --bhxh-before-2014 <năm> --bhxh-from-2014 <năm> --mbqtl <lương_bình_quân> --json
   ```
6. **Bài toán 6 — Thu nhập vãng lai:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --adhoc <số_tiền> --json
   ```

**Sinh Bảng Tính Excel Live Formulas:**
Sau khi có kết quả tính toán, chạy script xuất Excel phục vụ người dùng:
```bash
python3 .agents/skills/tu-van-thue-tncn/scripts/export_tax_sheet.py --output "<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx" --year <năm> --region <vùng> --dependents <npt> [--gross <gross>] [--settlement-income <income> --settlement-insurance <bh_năm> --tax-withheld <withheld>] [--include-bhxh --bhxh-before-2014 <n> --bhxh-from-2014 <n> --mbqtl <vnđ> --months-off <tháng>]
python3 .agents/skills/tu-van-thue-tncn/scripts/verify_tax_sheet.py --xlsx "<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx"
```
- Chỉ truyền những sheet người dùng cần và có đủ số liệu: script **từ chối** (exit 1) nếu quyết toán thiếu `--settlement-insurance`/`--tax-withheld`, hoặc BHXH thiếu số năm đóng. Khi đó hỏi người dùng, không tự bịa số để vượt lỗi.
- `verify_tax_sheet.py` tính lại mọi công thức bằng LibreOffice và so với `tax_calculator.py`. Chỉ bàn giao khi in `✅ ĐẠT`; nếu `✗`, sửa đầu vào/lệnh rồi xuất lại.
- Số trong báo cáo `.md` phải lấy từ JSON của `tax_calculator.py` (cùng `--year`, `--region`, đầu vào) và trùng với Excel.

---

## 5. Bước 3: Động Cơ PDCA Cascade & Báo Cáo Tư Vấn Cá Nhân Hóa

1. **Khởi tạo Sổ cái N+1:**
   - Tạo thư mục `<research_dir>` tại `<output_dir>/tax_consulting_[chủ_đề]/`.
   - Tạo file nhật ký `tax_phase_{N+1}.md` lưu vết 5 trục tọa độ và các câu trả lời phỏng vấn của người dùng.
2. **Biên soạn Báo cáo Tư vấn Cá nhân hóa (`tax_report_[chủ_đề].md`):**
   - Áp dụng mẫu `templates/tax_report_template.md`.
   - **Tập trung giải quyết đúng câu hỏi của người dùng:** Trả lời trực tiếp số thuế, số tiền thực nhận/hoàn lại, và các bước hành động cụ thể.
   - Trích dẫn nguyên văn điều khoản pháp luật làm căn cứ chứng minh.
   - Gắn cờ cảnh báo `[CẦN XÁC MINH]` cho các yếu tố chưa có chứng từ thực tế.
   - Đưa ra 3 khuyến nghị tối ưu nghĩa vụ thuế hợp chuẩn pháp lý.

---

## 6. Bước 4: Tiêu Chuẩn Bàn Giao Sạch & Kiểm Định Chất Lượng

### 6.1 Bảng Checklist Nghiệm thu Chất lượng (Quality Gate)
- [ ] Đã hoàn thành phỏng vấn thu thập dữ kiện trước khi tính toán; năm thuế và vùng đã xác định (hoặc ghi rõ giả định).
- [ ] `verify_tax_sheet.py` in `✅ ĐẠT` cho file Excel giao người dùng (bằng chứng: dán dòng kết quả vào `tax_phase_{N+1}.md`).
- [ ] Số liệu tính toán từ `tax_calculator.py` khớp hoàn toàn với bảng thuế trong báo cáo và file Excel.
- [ ] File bảng tính Excel được xuất với 100% Live Formulas tại `<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx`.
- [ ] File báo cáo chính thức được lưu tại `<research_dir>/tax_report_[chủ_đề].md`.
- [ ] Đã khử toàn bộ dấu vết AI tiếng Việt: không dùng em-dash `—` trong văn bản chạy (thay bằng ` - `), không dùng Oxford comma `, và`, không đặt dấu `:` cuối các heading.
- [ ] Báo cáo đã được quét: `python3 scripts/claim_guard.py <research_dir>/tax_report_[chủ_đề].md` (script ở thư mục gốc repo) đạt 0 vi phạm Rule R5.

### 6.2 Giao thức Bàn giao Sạch (Clean Delivery Protocol)
Khung chat chỉ hiển thị:
1. Bản tóm tắt điều hành súc tích (3 - 5 điểm cốt lõi giải đáp trực tiếp câu hỏi của người dùng).
2. Đường dẫn truy cập clickable đến file báo cáo `.md` và file bảng tính `.xlsx`.
3. Bảng disclaimer pháp lý chuẩn mực:

```
⚠️ LƯU Ý PHÁP LÝ:
Thông tin tư vấn dựa trên quy định pháp luật thuế và bảo hiểm xã hội Việt Nam có hiệu lực năm 2026. 
Kết quả tính toán mang tính chất tham khảo đối soát, không thay thế quyết định hành chính chính thức từ Cơ quan Thuế.
Kiểm tra và tra cứu hồ sơ cá nhân tại: https://canhan.gdt.gov.vn hoặc ứng dụng eTax Mobile.
```

---

## 7. CLI CONTRACT

> Dùng CLI contract dưới đây trước. Được phép đọc mã nguồn script bất cứ khi nào cần hiểu cách tính (ví dụ để giải thích cho người dùng) hoặc khi kết quả trông bất thường.

### 1. `scripts/tax_calculator.py`
- **Mục đích:** Tính toán chính xác số liệu thuế TNCN, Gross-Net, quyết toán năm, giảm trừ gia cảnh, BĐS và BHXH 1 lần.
- **Cú pháp:** `python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py [tùy_chọn] --json`
- **Tham số chính:**
  - `--gross <số_tiền>`: Lương Gross hàng tháng (VNĐ)
  - `--net <số_tiền>`: Lương Net hàng tháng muốn quy đổi sang Gross (VNĐ)
  - `--dependents <số_lượng>`: Số người phụ thuộc
  - `--settlement-income <số_tiền>`: Tổng thu nhập chịu thuế cả năm khi quyết toán (VNĐ)
  - `--settlement-insurance <số_tiền>`: Tổng bảo hiểm bắt buộc đã nộp trong năm (VNĐ)
  - `--settlement-tax-withheld <số_tiền>`: Tổng số thuế TNCN các nơi đã tạm khấu trừ (VNĐ)
  - `--adhoc <số_tiền>`: Thu nhập vãng lai / hợp đồng dịch vụ khấu trừ 10% (VNĐ)
  - `--year 2025|2026`: Năm thuế (mặc định 2026). Quyết toán năm 2025 BẮT BUỘC `--year 2025`
  - `--region I|II|III|IV`: Vùng lương tối thiểu → trần BHTN
  - `--medical`, `--education`, `--pension`: số BÌNH QUÂN THÁNG (quyết toán tự nhân 12)
  - `--json`: Xuất kết quả dưới định dạng JSON
- **Kết quả:** Trả về JSON chứa số liệu tính toán chi tiết, thuế phải nộp, hoàn lại.
- **Mã thoát (Exit code):** 0 nếu thành công, khác 0 nếu lỗi.
- **Ví dụ mẫu:**
  ```bash
  python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --year 2025 --settlement-income 300000000 --settlement-insurance 31500000 --settlement-tax-withheld 9000000 --dependents 1 --json
  ```

### 2. `scripts/export_tax_sheet.py`
- **Mục đích:** Bảng tính Excel công thức sống theo đúng năm thuế. Sheet "Thông số" chứa định mức của năm (giảm trừ, trần bảo hiểm, biểu thuế); các sheet khác tham chiếu tới đó.
- **Sheet được tạo theo dữ liệu có thật:** `--gross` → "Lương tháng"; `--settlement-income` (+ `--settlement-insurance`, `--tax-withheld` bắt buộc) → "Quyết toán năm"; `--include-bhxh` (+ 4 tham số BHXH bắt buộc) → "BHXH một lần".
- **Tham số:** `--output` (bắt buộc), `--year`, `--region`, `--dependents` (bắt buộc khi có lương/quyết toán), `--medical/--education/--pension` (bình quân tháng), `--months` (tháng giảm trừ bản thân, mặc định 12), `--dependent-months` (tổng tháng-người phụ thuộc nếu NPT đăng ký không đủ năm).
- **Mã thoát:** 0 thành công; 1 thiếu dữ liệu (thông báo rõ cần hỏi gì).
- **Ví dụ:**
  ```bash
  python3 .agents/skills/tu-van-thue-tncn/scripts/export_tax_sheet.py --output ~/Downloads/AIWF_Output/tax_consulting_quyet_toan/Bang_Tinh_Thue_TNCN_quyet_toan.xlsx --year 2025 --dependents 1 --settlement-income 300000000 --settlement-insurance 31500000 --tax-withheld 9000000
  ```

### 3. `scripts/verify_tax_sheet.py`
- **Mục đích:** Cổng kiểm định Excel trước khi giao: tính lại công thức bằng LibreOffice, so thuế tháng, Net, thuế năm, chênh lệch và kết luận quyết toán với `tax_calculator.py`; bắt ô lỗi `#VALUE!`/`#REF!`.
- **Cú pháp:** `python3 .agents/skills/tu-van-thue-tncn/scripts/verify_tax_sheet.py --xlsx <file.xlsx>`
- **Mã thoát:** 0 = `✅ ĐẠT`; 1 = có sai lệch (không được giao file).
