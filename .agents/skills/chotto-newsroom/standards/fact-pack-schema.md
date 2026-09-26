# CẤU TRÚC GÓI SỰ THẬT KIỂM CHỨNG (FACT PACK SCHEMA)

> Quy chuẩn cấu trúc hóa dữ liệu kiểm chứng sự thật (Fact Pack).
> Mọi bài viết trước khi được viết lời văn bắt buộc phải có một Fact Pack hoàn chỉnh nhằm triệt tiêu hoàn toàn ảo giác (Zero-Hallucination) và bảo đảm tính truy vết 100%.

---

## 1. CẤU TRÚC TỔNG THỂ CỦA FACT PACK

Mỗi file Fact Pack (định dạng Markdown) bao gồm 8 phần bắt buộc:

```markdown
# GÓI SỰ THẬT KIỂM CHỨNG: [MÃ SỰ KIỆN] - [TIÊU ĐỀ SỰ KIỆN]

## 1. THÔNG TIN ĐỊNH DANH SỰ KIỆN (METADATA)
- Mã sự kiện: [EVT-YYYYMMDD-XX]
- Chủ đề: [Tên chính sách / Thay đổi luật]
- Cơ quan ban hành: [Tên cơ quan tiếng Nhật và tiếng Việt]
- Ngày công bố chính thức: [YYYY-MM-DD]
- Ngày bắt đầu có hiệu lực: [YYYY-MM-DD] (khác nhau theo vùng thì ghi "xem mục 7")
- Giai đoạn pháp lý: [検討 / 諮問 / 答申 / 決定・公示 / 施行] (xem mục 5 dưới đây)
- Đối tượng thụ hưởng / chịu tác động: [Mô tả chi tiết nhóm đối tượng]
- Điểm đánh giá mức độ liên quan (Rubric Score): [xx/100]

## 2. MA TRẬN CÁC TUYÊN BỐ SỰ THẬT (KEY CLAIMS MATRIX)
[Bảng chi tiết các tuyên bố cần chứng minh trong bài viết]

## 3. DANH MỤC NGUỒN KIỂM CHỨNG (SOURCE REGISTRY)
[Danh sách URL, loại nguồn, cấp độ tin cậy]

## 4. BẰNG CHỨNG ĐỐI CHIẾU NGUYÊN VĂN (VERBATIM EVIDENCE QUOTES)
[Đoạn văn trích xuất nguyên bản từ tài liệu gốc tiếng Nhật]

## 5. CÁC ĐIỂM CHƯA RÕ RÀNG / CẦN GẮN CỜ ([CẦN XÁC MINH])
[Các khía cạnh chưa có số liệu chính thức hoặc đang chờ thông tư hướng dẫn]

## 6. MA TRẬN TÁC ĐỘNG VÀ HÀNH ĐỘNG (IMPACT & ACTION MATRIX)
[Ai bị ảnh hưởng? Cần làm thủ tục gì? Hạn chót khi nào?]

## 7. SỔ SỐ LIỆU (NUMBER LEDGER)
[Mọi con số và ngày sẽ xuất hiện trong bài: giá trị, nguồn, vị trí trong nguồn,
ô/dòng nguyên văn. Số tự tính thì ghi công thức.]

## 8. SỔ ĐIỀU LUẬT (LAW CITATIONS)
[Mọi điều luật bài nhắc tới: tên luật, số điều, link e-Gov, nguyên văn điều.]
```

---

## 2. CHI TIẾT MA TRẬN TUYÊN BỐ SỰ THẬT (KEY CLAIMS MATRIX)

Mỗi tuyên bố trong bài viết phải được phân rã thành một dòng trong bảng:

| Mã Claim | Tuyên bố sự thật (Tiếng Việt) | Mã Nguồn | Trích dẫn nguyên văn (Tiếng Nhật) | Mức tin cậy | Trạng thái thẩm định |
|:---:|---|:---:|---|:---:|:---:|
| **C01** | [Mức mới của vùng A là X đơn vị] | S01 | 「[ô/dòng nguyên văn chứa đúng con số X]」 | High | Đã xác minh |
| **C02** | [Vùng A áp dụng từ ngày D (dự kiến)] | S02 | 「[dòng nguyên văn ghi ngày D của vùng A]」 | High | Đã xác minh |
| **C03** | [Vi phạm bị phạt tới Y theo Điều N Luật Z] | S03 | 「[nguyên văn Điều N trên e-Gov]」 | High | Đã xác minh |
| **C04** | [Nội dung đang được xem xét] | S04 | 「[câu nguyên văn cho thấy mới ở giai đoạn 検討]」 | Medium | [CẦN XÁC MINH: Đang dự thảo] |

> [!CAUTION]
> Ví dụ cũ ở bảng này ghi C03 là "xử phạt theo Điều 119 Luật Tiêu chuẩn Lao động"
> trong khi chính câu trích dẫn cạnh đó là của 最低賃金法 (Luật Lương tối thiểu).
> Claim và nguyên văn không khớp mà vẫn "Đã xác minh", và câu sai đó đã lên một bài
> đăng thật. **Trước khi đánh dấu "Đã xác minh", đọc lại: câu tiếng Việt có nói đúng
> điều mà câu tiếng Nhật nói không (cùng luật, cùng số điều, cùng con số)?**

---

## 3. QUY TẮC PHÂN LOẠI MỨC ĐỘ TIN CẬY VÀ GẮN CỜ (CONFIDENCE FLAGGING)

Hệ thống bắt buộc tuân thủ nguyên tắc phân loại độ tin cậy theo Rule R4 & R2:

* **High ($\ge 90\%$):** Thông tin được công bố trực tiếp bằng văn bản trên trang chính thức `.go.jp` hoặc công báo chính phủ (Kanpō - 官報).
  - Có thể đưa vào bài viết dưới dạng câu khẳng định khách quan: *"Theo thông báo của..."*.
* **Medium ($70 - 89\%$):** Thông tin được đăng tải trên các cơ quan báo chí cấp quốc gia (NHK, Kyodo, Nikkei) dẫn lời quan chức chính phủ nhưng văn bản hướng dẫn chi tiết chưa phát hành.
  - Phải ghi rõ nguồn báo chí và bối cảnh: *"Theo đưa tin từ đài NHK ngày DD/MM..."*.
* **Low ($< 70\%$):** Tin đồn mạng xã hội, diễn đàn hoặc suy đoán từ các chuyên gia không có trích dẫn văn bản.
  - **TUYỆT ĐỐI CẤM** đưa vào bài viết dưới dạng sự thật.
  - Nếu vấn đề gây hoang mang dư luận cần đính chính, phải gắn cờ rõ ràng: `[CẦN XÁC MINH: Chưa có cơ sở pháp lý chính thức]`.

---

## 4. NGUYÊN TẮC TRÍCH DẪN NGUYÊN VĂN (VERBATIM QUOTE RULE)

1. Mỗi tuyên bố cốt lõi (Core Claim) trong Fact Pack BẮT BUỘC phải kèm theo một đoạn văn bản tiếng Nhật nguyên gốc trích xuất trực tiếp từ trang nguồn.
2. Trích dẫn nguyên văn phải bảo toàn cấu trúc câu, từ ngữ chuyên ngành và số liệu, không được tự ý diễn giải sai ngữ nghĩa.
3. Nếu tài liệu gốc là file PDF scan hoặc bảng biểu số liệu: Ghi chú rõ số trang, mục lục hoặc tọa độ bảng để phục vụ việc hậu kiểm (Verification Audit).

---

## 5. GIAI ĐOẠN PHÁP LÝ (LEGAL STAGE)

Cùng một con số có thể ở nhiều giai đoạn. Viết sai giai đoạn là hứa với người đọc
một điều chưa chắc xảy ra.

| Giai đoạn | Tiếng Nhật | Nghĩa | Cách viết trong bài |
|---|---|---|---|
| Xem xét | 検討 | Chính phủ đang cân nhắc | "đang được xem xét", không nêu như sự thật |
| Tham vấn | 諮問 | Bộ hỏi ý kiến hội đồng | "đang chờ hội đồng" |
| Đề xuất | 答申 | Hội đồng đã đề xuất, chưa chốt | "hội đồng đã đề xuất", "ngày dự kiến", "có thể thay đổi" |
| Quyết định / công bố | 決定・公示 | Đã chốt, chưa có hiệu lực | "đã quyết định, có hiệu lực từ ..." |
| Có hiệu lực | 施行・発効 | Đang áp dụng | viết như sự thật hiện hành |

Ví dụ thật: mức lương tối thiểu 2026 được MHLW công bố ngày 03/09/2026 ở giai đoạn
**答申**, hiệu lực **lần lượt từ 01/10 đến 02/12/2026 tùy tỉnh**, và MHLW ghi rõ ngày
có thể thay đổi. Bản nháp đã viết "chính thức có hiệu lực từ 01/10/2026 trên toàn bộ
47 tỉnh": sai cả giai đoạn lẫn ngày.

**Hiệu lực khác nhau theo vùng:** ghi ngày của từng vùng trong Sổ số liệu (mục 7), và
trong bài ghi ngày cạnh từng vùng, không gộp thành một ngày chung.

---

## 6. NGUỒN CHO CÁCH TÍNH VÀ THỦ TỤC

Câu nói **cách tính** (cộng khoản nào, chia cho gì) hay **thủ tục** (nộp ở đâu, cần
giấy gì) cũng là claim, và phải có nguồn chính thức như mọi con số: văn bản luật,
施行規則 (thông tư), 通達, Q&A hoặc tờ tự kiểm tra (セルフチェックシート) của bộ.

**Không viết theo "hiểu biết chung".** Bản nháp lương tối thiểu 2026 bảo "chỉ lấy
lương cơ bản, bỏ hết phụ cấp" trong khi tờ tự kiểm tra của MHLW cộng cả 役付手当,
住宅手当: người đọc làm theo sẽ tưởng mình bị trả thiếu.

---

## 7. SỔ SỐ LIỆU (NUMBER LEDGER)

Mọi con số và mọi ngày **sẽ xuất hiện trong bài** đều phải có một dòng ở đây. Phần
kiểm tra (`validate-article-draft.py --fact-pack`) đối chiếu từng số trong bài với sổ
này và **chặn** số nào không có.

```markdown
| Mã | Nội dung | Giá trị | Nguồn | Vị trí trong nguồn | Nguyên văn |
|---|---|---|---|---|---|
| N01 | Mức mới, vùng A | 1,280 | S01 | 別紙 PDF, trang 1, dòng 東京 | 東京 A 54 1,280 （1,226） 54 ±0 令和8年10月1日 |
| N02 | Mức cũ, vùng A | 1,226 | S01 | cùng dòng | (như trên) |
| N03 | Ngày hiệu lực, vùng A | 2026-10-01 | S01 | cùng dòng | 令和8年10月1日 |
```

- **Ngày ghi dạng `YYYY-MM-DD`** (đổi từ 令和 sang dương lịch: 令和 N năm = 2018 + N).
  Bài viết `01/10/2026` thì sổ phải có `2026-10-01`.
- **Số lấy từ bảng thì chép từ đúng ô của bảng**, không lấy từ đoạn tóm tắt hay bài báo.
  Ghi trang và dòng để người duyệt tìm lại trong 10 giây.
- **Số tự tính** (ví dụ thu nhập 4 tuần) ghi ở bảng riêng, có công thức:

```markdown
| Mã | Phép tính | Kết quả |
|---|---|---|
| K01 | 28 × 4 × 1,280 | 143,360 |
| K02 | (1,280 − 1,226) × 28 × 4 | 6,048 |
```

Tự tính lại từng dòng trước khi ghi. Số trong bài dùng dấu chấm (`1.280`), trong sổ
dùng dấu phẩy hay chấm đều được: phần kiểm tra bỏ dấu phân cách khi so.

---

## 8. SỔ ĐIỀU LUẬT (LAW CITATIONS)

Mọi câu "theo Điều N Luật X" trong bài phải có một dòng ở đây, **tra trên e-Gov**
(`https://laws.e-gov.go.jp/`), không lấy từ bài báo hay trí nhớ:

```markdown
| Mã | Luật | Điều | Link e-Gov | Nguyên văn |
|---|---|---|---|---|
| L01 | 最低賃金法 (Luật Lương tối thiểu) | 第40条 | https://laws.e-gov.go.jp/law/334AC0000000137 | 第四条第一項の規定に違反した者（…）は、五十万円以下の罰金に処する。 |
```

Mức phạt, thời hạn, đối tượng: đọc thẳng trong nguyên văn điều. Hai luật khác nhau
có thể cùng nói về một chuyện (Luật Tiêu chuẩn Lao động và Luật Lương tối thiểu đều có
điều xử phạt); tên luật sai là cả câu sai.
