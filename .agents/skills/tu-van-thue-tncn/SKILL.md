---
name: tu-van-thue-tncn
display-name: Tư Vấn Thuế TNCN
description: CỔNG TƯ VẤN THUẾ THU NHẬP CÁ NHÂN (TNCN) TƯƠNG TÁC 2 CHIỀU VIỆT NAM — KỲ TÍNH THUẾ 2026 (LUẬT 109/2025/QH15, NQ 110/2025/UBTVQH15, NĐ 253/2026/NĐ-CP, TT 87/2026/TT-BTC, NĐ 141/2026/NĐ-CP, LUẬT BHXH 2024). Tiếp nhận câu hỏi và tình huống thực tế của người dùng, chủ động phỏng vấn thu thập các thông số còn thiếu trên 5 trục tọa độ (lương Gross/Net, bảo hiểm, người phụ thuộc, hóa đơn y tế/giáo dục, chứng từ khấu trừ 10%, điều kiện BĐS, BHXH 1 lần). Tra cứu Nguồn Sự Thật Duy Nhất (SSOT), chạy động cơ tính toán Python chính xác không sai số và xuất bản báo cáo cá nhân hóa kèm bảng tính Excel 100% Live Formulas. Kích hoạt khi user đề cập 'thuế TNCN', 'tính thuế thu nhập cá nhân', 'quyết toán thuế', 'giảm trừ gia cảnh', 'eTax Mobile', 'người phụ thuộc', 'thuế freelancer', 'thuế vãng lai 10%', 'BHXH 1 lần', 'trợ cấp thất nghiệp', 'quy đổi lương gross net'. KHÔNG dùng cho thuế TNDN, thuế GTGT doanh nghiệp, thuế xuất nhập khẩu (chuyển sang tu-van-phap-luat hoặc kế toán doanh nghiệp), KHÔNG dùng cho soạn thảo văn phòng thuần túy (chuyển sang xu-ly-van-phong).
trigger: Tư vấn thuế TNCN, quyết toán thuế TNCN, tính thuế thu nhập cá nhân, tra cứu thuế TNCN, eTax Mobile, giảm trừ gia cảnh, BHXH 1 lần, thuế freelancer, thuế bất động sản, quy đổi lương gross net
argument-hint: [câu_hỏi_hoặc_tình_huống_thuế_tncn]
allowed-tools: [ask_question, run_command, view_file, write_to_file, grep_search]
effort: high
interaction-mode: interactive
needs_file: false
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
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/`** |
| `<research_dir>` | `<output_dir>/tax_consulting_[chủ_đề]/` |
| `<process_dir>` | `_process/tax_[chủ_đề]_[timestamp]/` (được bảo vệ bởi `.gitignore`) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Cho phép người dùng chọn hoặc chỉ định thư mục sẽ lưu file đầu ra.
> - TUYỆT ĐỐI KHÔNG tạo thư mục kết quả hoặc file báo cáo/bảng tính trực tiếp trong thư mục gốc của repository AIWF để tránh làm phình to kho Git.
> - Toàn bộ các file nhật ký phase (`tax_phase_{N+1}.md`), báo cáo tư vấn (`tax_report_[chủ_đề].md`) và bảng tính Excel (`Bang_Tinh_Thue_TNCN_[chủ_đề].xlsx`) PHẢI được lưu trong `<research_dir>` (tức `<output_dir>/tax_consulting_[chủ_đề]/`) và tạo bản sao bảng tính tại `<output_dir>/Bang_Tinh_Thue_TNCN_2026.xlsx`.

---

## 2. Bước 0: Giao Thức Kịch Bản Trắc Nghiệm Tương Tác Tự Động (Interactive Questionnaire Wizard Protocol)

> Thay vì bắt người dùng phải đọc nhiều chữ và tự gõ dài dòng trong chat, hệ thống vận hành theo cơ chế **Kịch bản Trắc nghiệm Tương tác Tự động (Questionnaire Wizard)** chuẩn bị sẵn trong tệp `resources/questionnaire_tree.json` kết hợp công cụ hộp thoại bản địa `ask_question`.

### Quy trình điều hướng kịch bản 4 bước:

#### BƯỚC 0.1: KÍCH HOẠT CÂU HỎI GỐC (ROOT TOPIC SELECTION)
Khi người dùng kích hoạt skill (gõ *"Tư vấn thuế TNCN"*, *"Quyết toán thuế"*, hoặc câu hỏi chung chung):
1. Agent lập tức gọi công cụ `ask_question` với nội dung từ trường `root_question` trong `resources/questionnaire_tree.json`.
2. Hộp thoại tương tác (Interactive Modal) xuất hiện ngay trên giao diện với 6 chuyên đề lựa chọn:
   - *1. Quyết toán thuế TNCN cuối năm & eTax Mobile*
   - *2. Tiền lương Gross <-> Net & Giảm trừ gia cảnh*
   - *3. Thuế chuyển nhượng Bất động sản (2%) & Miễn thuế*
   - *4. Tư vấn rút BHXH một lần theo Luật BHXH 2024 & Lương hưu*
   - *5. Thuế Freelancer, Hộ kinh doanh & Khấu trừ 10%*
   - *6. Đăng ký người phụ thuộc & Mã số thuế*

#### BƯỚC 0.2: CHUYỂN TIẾP TUẦN TỰ THEO NHÁNH KỊCH BẢN (ZERO-LATENCY BRANCH TRANSITION)
Khi người dùng chọn một chuyên đề:
1. Agent tra cứu ngay danh sách câu hỏi của nhánh tương ứng trong `resources/questionnaire_tree.json`.
2. Gọi tuần tự `ask_question` cho từng câu hỏi trong nhánh.
3. **TUYỆT ĐỐI KHÔNG DỪNG LẠI SUY LUẬN TỰ DO:** Sau khi người dùng submit câu trả lời cho câu hỏi trước, Agent **chuyển ngay sang câu hỏi tiếp theo** trong danh sách kịch bản chuẩn bị sẵn mà không chờ mô hình suy nghĩ hoặc phân tích giữa chừng.
4. **HỖ TRỢ NHẬP SỐ TIỀN CỤ THỂ:** Người dùng có thể click chọn nhanh các mốc định sẵn HOẶC nhập số tiền/giá trị chính xác vào ô viết tự do (Write-in input) tích hợp sẵn trong hộp thoại UI `ask_question`.

#### BƯỚC 0.3: CÂU HỎI CUỐI CÙNG — GHI CHÚ THÊM CỦA NGƯỜI DÙNG (FINAL NOTES)
Câu hỏi cuối cùng của mọi nhánh kịch bản luôn là:
`"Bạn có ghi chú hoặc yêu cầu đặc biệt nào thêm cho hồ sơ này không?"`
- Tùy chọn 1: `(Khuyến nghị) Không có ghi chú thêm, tiến hành tra cứu và lập báo cáo ngay`
- Tùy chọn 2: `Tôi có ghi chú cụ thể (vui lòng điền vào ô bên dưới)` -> Người dùng có thể điền các mong muốn cá nhân hóa.

#### BƯỚC 0.4: BÀN GIAO CHO ĐỘNG CƠ TỰ CHỦ (AUTONOMOUS FULL-RUN HANDOFF)
Ngay sau khi nhận câu trả lời cho câu hỏi cuối cùng:
1. Toàn bộ các thông số khảo sát được chuyển sang `scripts/interactive_wizard.py` hoặc ánh xạ trực tiếp thành các cờ tham số cho `tax_calculator.py` và `export_tax_sheet.py`.
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
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --net <số_tiền_net> --dependents <số_npt> --json
   ```
2. **Bài toán 2 — Tính Lương Gross sang Net:**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --gross <số_tiền_gross> --dependents <số_npt> --medical <chi_phí_y_tế> --education <chi_phí_học_phí> --pension <hưu_trí> --json
   ```
3. **Bài toán 3 — Quyết toán thuế năm (Thu nhập 2 nơi trở lên):**
   ```bash
   python3 .agents/skills/tu-van-thue-tncn/scripts/tax_calculator.py --settlement-income <tổng_thu_nhập_năm> --settlement-insurance <tổng_bh_đã_nộp> --dependents <số_npt> --settlement-tax-withheld <số_thuế_các_nơi_đã_trừ> --json
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
python3 .agents/skills/tu-van-thue-tncn/scripts/export_tax_sheet.py --output "<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx" --gross <gross> --dependents <npt> [--settlement-income <income> --tax-withheld <withheld>]
cp "<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx" "<output_dir>/Bang_Tinh_Thue_TNCN_2026.xlsx"
```

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
- [ ] Đã hoàn thành phỏng vấn thu thập dữ kiện trước khi tính toán.
- [ ] Số liệu tính toán từ `tax_calculator.py` khớp hoàn toàn với bảng thuế trong báo cáo và file Excel.
- [ ] File bảng tính Excel được xuất với 100% Live Formulas tại `<research_dir>/Bang_Tinh_Thue_TNCN_[chu_de].xlsx` và `<output_dir>/Bang_Tinh_Thue_TNCN_2026.xlsx`.
- [ ] File báo cáo chính thức được lưu tại `<research_dir>/tax_report_[chủ_đề].md`.
- [ ] Đã khử toàn bộ dấu vết AI tiếng Việt: không dùng em-dash `—` trong văn bản chạy (thay bằng ` - `), không dùng Oxford comma `, và`, không đặt dấu `:` cuối các heading.
- [ ] Báo cáo đã được quét qua `scripts/claim_guard.py` đạt 0 vi phạm Rule R5 (Legal Claim Compliance).

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
