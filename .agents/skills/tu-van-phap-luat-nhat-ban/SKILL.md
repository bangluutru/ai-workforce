---
name: tu-van-phap-luat-nhat-ban
display-name: Tư Vấn Pháp Luật Nhật Bản
description: >-
  Nghiên cứu và tư vấn sơ bộ pháp luật Nhật Bản theo tình huống, với căn cứ tiếng Nhật và hiệu lực theo thời điểm; chuyên sâu xuất nhập khẩu, tra mã HS từ sản phẩm/thành phần, thuế quan, xuất xứ EPA/FTA, điều kiện lưu hành, nhãn, quảng cáo và nghĩa vụ sau bán.
  USE WHEN: Người dùng cần tư vấn pháp lý Nhật Bản (hợp đồng, doanh nghiệp, lao động, cư trú, thuế, tranh chấp, SHTT) hoặc sản phẩm có yếu tố Nhật Bản, nhập khẩu vào Nhật, tra cứu mã thuế quan HS, điều kiện lưu hành thực phẩm/mỹ phẩm/thiết bị điện, rà soát nhãn và quảng cáo tại Nhật.
  DO NOT USE WHEN: Vấn đề pháp lý thuần túy tại Việt Nam không có yếu tố Nhật Bản (dùng 'tu-van-phap-luat'), dịch thuật văn bản đơn thuần (dùng 'ejv-translate'), hoặc thuế Việt Nam (TNCN, TNDN, GTGT... dùng 'tu-van-thue').
category: legal_finance
needs_file: false
file_filter: doc
---

# Tư Vấn Pháp Luật Nhật Bản — Japanese Legal & Market Access Consultant

> Nghiên cứu tình huống & căn cứ tiếng Nhật → Rà soát vòng đời hàng hóa & pháp lý chuyên ngành → Tư vấn đường lối, mã HS, thuế quan và điều kiện lưu hành.

---

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Skill này chạy hoàn toàn bằng năng lực tích hợp sẵn của Antigravity IDE (Gemini 3.8 Multi-Agent).
> - TUYỆT ĐỐI KHÔNG gọi REST API bên ngoài (OpenAI, Gemini API, Claude API) hoặc yêu cầu API key.
> - Toàn bộ năng lực lập luận, đối chiếu văn bản và tư vấn pháp lý là của chính Agent LLM nội bộ.
> - Khi được kích hoạt, skill PHẢI tự chạy liên tục (Autonomous Full-Run) theo quy trình PDCA, không tự ý dừng giữa chừng để xin phép.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

Agent PHẢI xác định thư mục lưu trữ đầu ra trước khi khởi tạo báo cáo hoặc file kịch bản tính thuế:

| Placeholder | Quy ước xác định đường dẫn |
|---|---|
| `<output_dir>` | **Nơi người dùng chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<research_dir>` | `<output_dir>/legal_jp_[chủ_đề]/` |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Cho phép người dùng chọn/chỉ định thư mục sẽ lưu file đầu ra.
> - TUYỆT ĐỐI KHÔNG tạo thư mục kết quả hoặc lưu file nghiên cứu trực tiếp trong thư mục gốc codebase AIWF để tránh làm phình to repo Git.
> - Toàn bộ báo cáo tư vấn pháp lý Nhật Bản (`legal_report_jp_[chủ_đề].md`), kịch bản tính thuế JSON và thư mục nguồn `sources/` PHẢI được xuất ra `<research_dir>` (tức `<output_dir>/legal_jp_[chủ_đề]/`).

---

## 1. Chọn việc và tài liệu định tuyến

Đọc file được liên kết bằng công cụ đọc file của môi trường. Các đường dẫn dưới đây tương đối với thư mục skill; không phụ thuộc thư mục làm việc của người dùng. Chỉ tải tài liệu cần cho câu hỏi hiện tại.

| Yêu cầu | Đọc |
|---|---|
| Nghiên cứu hiệu lực, xung đột, nguồn Nhật/bản dịch | [legal-research.md](references/legal-research.md) |
| Pháp luật chung: hợp đồng, gia đình, doanh nghiệp, lao động, cư trú, thuế, tố tụng, SHTT, dữ liệu, đất đai | [general-law-routing.md](references/general-law-routing.md) |
| HS, mã thuế quan Nhật, thành phần, thuế nhập khẩu, trị giá, xuất xứ, EPA/FTA, thủ tục hải quan | [customs-and-tariffs.md](references/customs-and-tariffs.md) |
| Xuất khẩu hàng hóa/công nghệ từ Nhật, hạn chế thương mại | [export-controls.md](references/export-controls.md) |
| Phân loại và điều kiện nhập/lưu hành sản phẩm | [product-market-access.md](references/product-market-access.md) + module sản phẩm dưới đây |
| Rà nhãn, claim, quảng cáo, trang bán online | [labeling-advertising-sales.md](references/labeling-advertising-sales.md) + module sản phẩm |
| Sự cố, thu hồi, trách nhiệm sau bán | [post-market.md](references/post-market.md) + module sản phẩm |
| Bảng căn cứ, báo cáo hồ sơ, ma trận nghĩa vụ | [evidence-and-output.md](references/evidence-and-output.md) |
| Cần tìm cơ quan/điểm tra cứu chính thức | [source-map.md](references/source-map.md) |

Module sản phẩm chuyên ngành:
- Thực phẩm, thực phẩm có claim sức khỏe, bao bì tiếp xúc thực phẩm: [food-and-health-claims.md](references/products/food-and-health-claims.md).
- Mỹ phẩm, quasi-drugs: [cosmetics-and-quasi-drugs.md](references/products/cosmetics-and-quasi-drugs.md).
- Thuốc, thiết bị y tế, IVD: [drugs-and-medical-devices.md](references/products/drugs-and-medical-devices.md).
- Điện, pin, vô tuyến, hàng tiêu dùng: [electrical-radio-consumer.md](references/products/electrical-radio-consumer.md).
- Hóa chất, vật liệu: [chemicals-materials.md](references/products/chemicals-materials.md).
- Động/thực vật, rượu, thuốc lá và hàng đặc thù: [animal-plant-special-goods.md](references/products/animal-plant-special-goods.md).

*Lưu ý:* Một hồ sơ có thể cần nhiều module. Ví dụ máy dùng điện có Bluetooth và claim trị liệu cần xem cả điện/vô tuyến và PMD nếu đặc tính liên quan.

---

## 2. Bước 0 — Intake & Tiếp nhận Dữ kiện (5 Trục Tọa độ)

Trước khi tra cứu, Agent PHẢI định danh tọa độ pháp lý:

| Trục | Câu hỏi định vị | Ví dụ |
|---|---|---|
| **ĐỐI TƯỢNG** | Ai? Cái gì? (chủ thể, sản phẩm, hàng hóa) | Cá nhân người nước ngoài; Doanh nghiệp Nhật; Mỹ phẩm serum; Hạt tiêu đen |
| **HÀNH VI** | Làm gì? (giao dịch, hành vi pháp lý) | Nhập khẩu thương mại; Bán trên Rakuten; Ký hợp đồng lao động; Chấm dứt hợp đồng |
| **TÁC ĐỘNG** | Hệ quả mong muốn hoặc rủi ro cần phòng tránh? | Thông quan suôn sẻ; Miễn thuế EPA; Giấy phép 製造販売業; Tránh vi phạm quảng cáo |
| **PHẠM VI** | Không gian, vai trò trong chuỗi hàng hóa? | Nhập từ VN sang Tokyo; D2C hay B2B; Nhà nhập khẩu (輸入者) hay Ủy thác (委託) |
| **THỜI ĐIỂM** | Khi nào? ★ Trục quyết định văn bản áp dụng | Ngày nhập khẩu dự kiến; Mốc sự kiện phát sinh tranh chấp; Ngày hợp đồng có hiệu lực |

Với hàng hóa, bổ sung: hướng nhập/xuất, nước sản xuất/xuất xứ, mục đích thương mại/cá nhân/mẫu, thông số/thành phần/hàm lượng %, công dụng/claim, kênh bán và ngày vận chuyển dự kiến. Khi phân tích trị giá hoặc số thuế, tiếp nhận thêm giá CIF, cước vận chuyển, bảo hiểm và điều kiện giao hàng.

**Đọc tệp người dùng** (hợp đồng, 通知書, 見積書/インボイス, 成分表: PDF/DOCX/XLSX/ảnh): không đọc thẳng tệp nhị phân. Từ gốc repo chạy `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<tên_việc> --json` rồi đọc `source.md` + `manifest.json` (`warnings`). Mã thoát: `0` dùng `source.md` · `3` có trang scan → đọc ảnh `ocr_pages/*.png` bằng thị giác (nháp OCR trong `source.md` CHƯA kiểm chứng) · `2` hỏi người dùng đúng điều trong `manifest.message` (mật khẩu/hỏng), không đoán · `4` thiếu phụ thuộc → cài theo `manifest.message` (`bash scripts/auto-setup.sh`). Dữ kiện lấy từ tệp ghi nguồn `<tên tệp>, trang N`; trích tiếng Nhật nguyên văn chỉ từ lớp chữ hoặc ảnh trang đã đọc, không từ nháp OCR. Nguồn web/e-Gov vẫn lưu bằng `scripts/fetch_jp_source.py`.

---

## 3. Nghiên cứu và Kiểm chứng Nguồn (PDCA Cycle)

1. **[P - Plan]** Đặt câu hỏi pháp lý cốt lõi và các khoảng trống dữ kiện ảnh hưởng kết luận.
2. **[D - Do]** Tra cứu nguồn chính thức, ưu tiên tiếng Nhật:
   - e-Gov 法令検索 (`laws.e-gov.go.jp`) cho văn bản quy phạm pháp luật (Luật `法律`, Lệnh `政令`, Thông tư `省令`).
   - Japan Customs (`customs.go.jp`) cho biểu thuế quan, văn bản hướng dẫn và phán quyết phân loại trước (`事前教示`).
   - MHLW (`mhlw.go.jp`), METI (`meti.go.jp`), CAA (`caa.go.jp`) cho quy chuẩn chuyên ngành, nhãn và quảng cáo.
   - Courts in Japan (`courts.go.jp`) cho án lệ và phán quyết tòa án.
   - Lưu mỗi nguồn được trích vào `<research_dir>/sources/` bằng `scripts/fetch_jp_source.py` (luật e-Gov được lưu theo từng 第N条). Tệp nguồn người dùng gửi (通知/PDF/DOCX...): `--file "<tệp>"` thay cho `--url` (đọc qua doc_ingest, cùng bố cục file; exit `2` mật khẩu/hỏng → hỏi bản khác, `5` scan → không lưu nháp OCR làm nguồn, ảnh trang ở `<research_dir>/_ingest/<name>/ocr_pages/`). Nguồn bị chặn (403) hoặc PDF ảnh: ghi "chưa đọc được" trong Bảng nguồn và dùng `[GIẢ ĐỊNH / CHƯA XÁC MINH]`, không viện dẫn như đã đọc.
3. **[C - Check]** Kiểm tra loại nguồn, phạm vi, điều/phụ lục, sửa đổi, ngày thi hành và chuyển tiếp tại mốc thời điểm của người dùng. Không đồng nhất ngày ban hành, ngày cập nhật web và ngày có hiệu lực.
4. **[A - Act / Synthesize]** Gắn kết luận trọng yếu với căn cứ và dữ kiện; phân biệt điều luật, hướng dẫn hành chính và suy luận áp dụng.

---

## 4. Hai Luồng Xử Lý Chính

### Luồng A — Vụ việc pháp lý chung
`Tình tiết sự việc → Vấn đề pháp lý cốt lõi → Quy định/án lệ liên quan → Áp dụng vào dữ kiện → Phương án xử lý thực tế → Thủ tục, thẩm quyền và mốc thời gian tiếp theo.`
- Đánh dấu thời hạn khẩn cấp (thời hiệu khởi kiện, thời hạn khiếu nại, thời hạn gia hạn visa).
- Không tự ép đưa ra 2 phương án giả tạo nếu quy định pháp luật chỉ quy định một trình tự cụ thể.

### Luồng B — Vòng đời hàng hóa & sản phẩm
`Phân loại chuyên ngành (Regulatory Classification) → Phân loại thuế quan (HS Code) → Cấm/hạn chế/kiểm dịch (Điều 70 Luật Hải quan) → Chủ thể chịu trách nhiệm pháp lý tại Nhật → Thuế nhập khẩu & EPA/FTA → Quy tắc xuất xứ → Điều kiện trước bán (Giấy phép/Thông báo) → Nhãn & Quảng cáo → Quản lý sau bán & Thu hồi.`

Luồng xác định thuế quan BẮT BUỘC (không có đường tắt, kể cả câu hỏi ngắn trong chat):
1. **Ứng viên mã:** từ đặc tính/thành phần → chạy `tariff_lookup.py --code <HS6> --list` để xem các dòng 9 số thật của HS6 đó. Không viết mã 9 số nào không có trong danh sách này.
2. **Tra dòng theo ngày nhập:** với mỗi mã 9 số sẽ nêu trong câu trả lời, chạy
   `python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/tariff_lookup.py --code <dddd.dd-ddd> --origin "<nước xuất xứ>" --date <YYYY-MM-DD> --compact`
   (`--compact` chỉ in cột MFN và cột hiệp định của nước xuất xứ; bỏ `--compact` khi cần so mọi hiệp định)
   và **dán nguyên khối đầu ra** (từ `<!-- TARIFF_LOOKUP v1 -->` tới `<!-- /TARIFF_LOOKUP -->`) vào báo cáo hoặc câu trả lời chat. Mọi thuế suất trong bài lấy từ khối này, không lấy từ trí nhớ, bài báo hay JETRO.
3. **Đọc ô đúng quy ước:** ô trống ở cột hiệp định (kể cả dòng cha) = **không có ưu đãi**, áp MFN; KHÔNG được viết thành 0%. "Free" mới là 0%. Mức `yen/kg` là thuế theo lượng. Mỗi hiệp định (VJEPA = cột Viet Nam, AJCEP = cột ASEAN, CPTPP, RCEP = cột ASEAN/Australia/New Zealand(RCEP)) đọc riêng, không gộp "EPA 0%".
4. **Quy tắc xuất xứ (PSR):** với mỗi hiệp định định dùng, mở [Japan Customs: Rules of Origin](https://www.customs.go.jp/roo/english/index.htm), ghi tiêu chí PSR của đúng HS6 theo phiên bản HS của hiệp định, nguyên liệu không xuất xứ (BOM), chứng từ (C/O do cơ quan cấp hay tự chứng nhận). Chưa đọc được PSR thì ghi `[GIẢ ĐỊNH / CHƯA XÁC MINH]`, không viết "đáp ứng 100%".
5. **Tính tiền:** `estimate_import_taxes.py` (hỗ trợ % và yen/kg, hỗn hợp), ghi `rate_source` là URL biểu thuế.
6. **Điểm cần 事前教示** khi phân loại còn hai ứng viên.

Với thực phẩm: chạy tự kiểm nhãn ở [food-and-health-claims.md](references/products/food-and-health-claims.md) mục "Tự kiểm nhãn": 名称, 原材料名/添加物, 内容量, 賞味期限/消費期限, 保存方法, **原産国名**, 輸入者, **栄養成分表示**, アレルゲン.

---

## 5. Công cụ Hỗ Trợ Tự Động

Mọi lệnh chạy từ **thư mục workspace AIWF** (thư mục chứa `GEMINI.md`). Ký hiệu `$S` = `.agents/skills/tu-van-phap-luat-nhat-ban/scripts`.

| Việc | Lệnh | Bắt buộc khi |
|---|---|---|
| Tra dòng biểu thuế theo ngày | `python3 $S/tariff_lookup.py --code 2101.11-210 --origin "Viet Nam" --date 2026-10-15` (`--list` để xem các dòng 9 số của HS6) | Mọi câu trả lời có mã HS hoặc thuế suất |
| Lưu nguồn chính thức để đối chiếu trích dẫn | `python3 $S/fetch_jp_source.py --url https://laws.e-gov.go.jp/law/<LawID> --out-dir <research_dir>/sources --name <tên>` | Mọi điều luật/thông báo được trích |
| Tính kịch bản thuế | `python3 $S/estimate_import_taxes.py --input <research_dir>/scenario.json` | Khi nêu số tiền thuế |
| Cổng kiểm Bảng nguồn + thuế suất + nhãn | `python3 $S/check_evidence_table.py --report <research_dir>/legal_report_jp_<chủ_đề>.md --sources-dir <research_dir>/sources` | Trước khi xuất DOCX; phải PASS (exit 0) |
| Xuất DOCX | `python3 .agents/skills/_shared/docx/legal_report.py --input <research_dir>/legal_report_jp_<chủ_đề>.md` | Hồ sơ chuyên sâu |
| Kiểm cấu trúc DOCX đã xuất | `python3 .agents/skills/_shared/docx/inspect_docx.py <research_dir>/legal_report_jp_<chủ_đề>.docx --rules .agents/skills/_shared/docx/rules/legal_report_jp.rules.json` | Sau khi xuất DOCX; phải `✅ RULES PASS` (exit 0) |

`estimate_import_taxes.py`: thuế theo tỷ lệ (`duty_rate_percent`), theo lượng (`duty_specific_jpy_per_unit` + `quantity` + `quantity_unit`), hoặc kết hợp (`duty_method`: `compound_sum` | `greater_of` | `lesser_of`). Script không tra HS, không làm tròn pháp lý, không tính hạn ngạch hay thuế điều chỉnh đường; chi tiết ở [customs-and-tariffs.md](references/customs-and-tariffs.md).

Xuất DOCX dùng engine chung `_shared/docx/legal_report.py` (Luật R7 — không chép file này vào skill).

---

## 6. Tiêu Chuẩn Kiểm Thẩm (Quality Gate) & Giao Thức Bàn Giao

### <quality_gate>
Trước khi xuất bản hoặc trả lời kết quả tư vấn, Agent PHẢI tự thẩm định qua 5 cổng kiểm soát:
1. **Phạm vi & Thời điểm**: Đúng bối cảnh Nhật Bản, đúng mốc thời gian sự kiện/nhập khẩu, đúng phiên bản luật có hiệu lực.
2. **Căn cứ Pháp lý & Evidence Verifier**: Mọi phát biểu pháp lý trọng yếu phải trích dẫn NGUYÊN VĂN tiếng Nhật kèm tọa độ chính xác:
   - Tên văn bản chuẩn (VD: `医薬品、医療機器等の品質、有効性及び安全性の確保等に関する法律`, `関税定率法`).
   - Tọa độ điều khoản: Điều `第○条`, Khoản `第○項`, Điểm `第○号`, Phụ lục `別表`, Điều khoản chuyển tiếp `附則`.
3. **Confidence Flagging**: Phân định rạch ròi 3 cấp độ chắc chắn, và mỗi dòng `[XÁC ĐỊNH]` phải dẫn ID trong Bảng nguồn, VD `(E1)`:
   - `[XÁC ĐỊNH]`: Đã đối chiếu điều luật hoặc thông báo chính thức có hiệu lực, có URL + ngày truy cập + trích đoạn trong Bảng nguồn. **Thuế suất** chỉ được `[XÁC ĐỊNH]` khi dẫn nguồn biểu thuế có ngày (`customs.go.jp/english/tariff/YYYY_MM_DD`), ghi đúng ô của khối `TARIFF_LOOKUP` đã dán trong báo cáo.
   - `[SUY LUẬN ÁP DỤNG]`: Phân tích áp dụng điều luật vào tình huống cụ thể của người dùng.
   - `[GIẢ ĐỊNH / CHƯA XÁC MINH]`: Dữ kiện chưa đủ hoặc cần làm thủ tục xác nhận với cơ quan chức năng (như 事前教示 Hải quan), hoặc nguồn chưa đọc được (403, PDF ảnh).
   - Ô trống ở cột hiệp định = không có ưu đãi. Viết "0%/Free/miễn thuế" cho hiệp định mà khối tra cứu ghi trống là lỗi nghiêm trọng.
4. **Phân biệt Khái niệm Pháp lý**:
   - Không đồng nhất nhập khẩu với được phép bán ra thị trường.
   - Không dịch chung `届出` (thông báo), `許可` (giấy phép), `承認` (chấp thuận), `認証` (chứng nhận), `登録` (đăng ký).
   - Không suy diễn chứng nhận nước ngoài (FDA, CE, GMP VN) thay thế tự động nghĩa vụ theo luật Nhật Bản.
5. **Tuân thủ Luật R5**: Không cam kết chắc chắn 100% kết quả tố tụng hoặc thông quan. Nêu rõ giới hạn tư vấn sơ bộ và khuyến nghị tham vấn luật sư Nhật Bản (弁護士) hoặc đại lý hải quan (通関士) cho hồ sơ thực tế.
6. **Evidence Verifier bằng script**: `check_evidence_table.py --sources-dir` trả PASS (exit 0). Nó kiểm Bảng nguồn (ID, URL, ngày, trích đoạn; luật e-Gov phải có trích đoạn tiếng Nhật có nguyên văn trong file nguồn đã lưu), mã 9 số đều có khối TARIFF_LOOKUP, câu "hiệp định X 0%" khớp biểu thuế, nhãn thực phẩm đủ trường, không lẫn chữ Trung. FAIL thì sửa báo cáo rồi chạy lại; không xuất DOCX khi chưa PASS.
7. **Nhất quán số liệu nội bộ**: con số dùng ở hai mục (VD vốn ¥30M ở mục visa và thuế đăng ký 0.7% × vốn ở mục chi phí) phải tính từ cùng giả định; tính lại trước khi chốt.
</quality_gate>

### <delivery_protocol>
- **Đối với câu hỏi ngắn/sơ bộ**: Trình bày trực tiếp trong chat, nêu rõ kết luận cốt lõi, căn cứ điều luật Nhật, cảnh báo rủi ro và các bước tiếp theo.
- **Đối với hồ sơ chuyên sâu/hàng hóa phức tạp**:
  1. Lưu nguồn vào `<research_dir>/sources/` bằng `fetch_jp_source.py`; xuất báo cáo vào `<research_dir>/legal_report_jp_[chủ_đề].md` kèm Bảng nguồn và các khối TARIFF_LOOKUP.
  2. Chạy cổng kiểm, phải PASS:
     ```bash
     python3 .agents/skills/tu-van-phap-luat-nhat-ban/scripts/check_evidence_table.py --report <research_dir>/legal_report_jp_[chủ_đề].md --sources-dir <research_dir>/sources
     ```
  3. Chuyển sang Word (.docx):
     ```bash
     python3 .agents/skills/_shared/docx/legal_report.py --input <research_dir>/legal_report_jp_[chủ_đề].md
     ```
     Kiểm cấu trúc file Word (font, A4, lề, placeholder, cấp tiêu đề, số trang); phải in `✅ RULES PASS`:
     ```bash
     python3 .agents/skills/_shared/docx/inspect_docx.py <research_dir>/legal_report_jp_[chủ_đề].docx --rules .agents/skills/_shared/docx/rules/legal_report_jp.rules.json
     ```
  4. Khung chat chỉ tóm tắt ngắn gọn: Kết luận chính, mức độ chắc chắn, 3-5 hành động cấp bách và link trỏ đến cả 2 file báo cáo (.md và .docx) trong thư mục người dùng.
</delivery_protocol>

---

## 🧩 Engine dùng chung (Luật R7)

> Năng lực dưới đây đã có trong `.agents/skills/_shared/` hoặc `scripts/` — **gọi lại, KHÔNG viết lại** trong skill. Cần năng lực mới: tra [`_shared/ENGINES.md`](../_shared/ENGINES.md) trước; thiếu thì mở rộng/đăng ký ở `_shared`, rồi chạy `python3 scripts/check_shared_reuse.py`.

| Engine / công cụ | Dùng cho | Cách gọi |
|---|---|---|
| `scripts/doc_ingest.py` | Đọc tệp người dùng (PDF/DOCX/XLSX/PPTX/ảnh…) thành `source.md` + `manifest.json` | `.venv/bin/python scripts/doc_ingest.py "<tệp>" --out ~/Downloads/AIWF_Output/_ingest/<việc> --json` |
| `doc_ingest_bridge` | Gọi doc_ingest từ Python: `run_ingest`, `explain`, `ocr_page_paths`, `strip_md_inline` | import trong `scripts/fetch_jp_source.py` |
| `docx.legal_report` | Báo cáo Markdown → DOCX pháp lý (font CJK) | `python3 .agents/skills/_shared/docx/legal_report.py --input <report.md>` |
| `docx.inspect` | Đọc ngược DOCX thành JSON, kiểm theo luật khai báo | `python3 .agents/skills/_shared/docx/inspect_docx.py <file.docx> --rules .agents/skills/_shared/docx/rules/legal_report_jp.rules.json` |
