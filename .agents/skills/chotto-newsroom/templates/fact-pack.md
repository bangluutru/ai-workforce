# GÓI SỰ THẬT KIỂM CHỨNG: {{EVENT_ID}} — {{EVENT_TITLE}}

> Tài liệu kiểm chứng sự thật và nguồn gốc dữ liệu phục vụ biên tập bài viết trên ChottoDay.
> Quy chuẩn áp dụng: `standards/fact-pack-schema.md`.

---

## 1. THÔNG TIN ĐỊNH DANH SỰ KIỆN (METADATA)

* **Mã sự kiện:** `{{EVENT_ID}}` (Định dạng: `EVT-YYYYMMDD-01`)
* **Chủ đề chính:** {{EVENT_TOPIC}}
* **Cơ quan ban hành:** {{GOV_AGENCY_JA}} ({{GOV_AGENCY_VI}})
* **Ngày công bố chính thức:** {{DATE_ANNOUNCED}}
* **Ngày bắt đầu áp dụng / có hiệu lực:** {{DATE_EFFECTIVE}} (khác nhau theo vùng thì ghi "xem mục 7")
* **Giai đoạn pháp lý:** {{LEGAL_STAGE}} (検討 / 諮問 / 答申 / 決定・公示 / 施行 — xem `standards/fact-pack-schema.md` mục 5)
* **Hạn chót thủ tục (nếu có):** {{DATE_DEADLINE}}
* **Đối tượng chịu tác động chính:** {{TARGET_POPULATION}}
* **Điểm đánh giá mức độ liên quan (Rubric Score):** {{RUBRIC_SCORE}}/100

---

## 2. MA TRẬN CÁC TUYÊN BỐ SỰ THẬT (KEY CLAIMS MATRIX)

| Mã Claim | Tuyên bố sự thật (Tiếng Việt) | Mã Nguồn | Trích dẫn nguyên văn (Tiếng Nhật) | Mức tin cậy | Trạng thái thẩm định |
|:---:|---|:---:|---|:---:|:---:|
| **C01** | {{CLAIM_01_STATEMENT}} | S01 | 「{{CLAIM_01_JP_QUOTE}}」 | {{CLAIM_01_CONFIDENCE}} | {{CLAIM_01_STATUS}} |
| **C02** | {{CLAIM_02_STATEMENT}} | S01 | 「{{CLAIM_02_JP_QUOTE}}」 | {{CLAIM_02_CONFIDENCE}} | {{CLAIM_02_STATUS}} |
| **C03** | {{CLAIM_03_STATEMENT}} | S02 | 「{{CLAIM_03_JP_QUOTE}}」 | {{CLAIM_03_CONFIDENCE}} | {{CLAIM_03_STATUS}} |

---

## 3. DANH MỤC NGUỒN THẨM ĐỊNH (SOURCE REGISTRY)

* **Nguồn S01 (Cấp độ 1 — Nguồn gốc tối cao):**
  - Tiêu đề văn bản: {{S01_TITLE}}
  - Đường dẫn chính thức: {{S01_URL}}
  - Cơ quan công bố: {{S01_ORG}}
  - Loại nguồn: `official` (.go.jp)
  - Ngày xác minh: {{S01_VERIFIED_DATE}}

* **Nguồn S02 (Cấp độ 2 hoặc 3 — Nguồn bổ trợ):**
  - Tiêu đề: {{S02_TITLE}}
  - Đường dẫn: {{S02_URL}}
  - Đơn vị phát hành: {{S02_ORG}}
  - Loại nguồn: `primary` / `reference`
  - Ngày xác minh: {{S02_VERIFIED_DATE}}

---

## 4. BẰNG CHỨNG ĐỐI CHIẾU NGUYÊN VĂN (VERBATIM EVIDENCE QUOTES)

### Đoạn trích 1 (Tương ứng Claim C01):
```text
{{S01_EXTENDED_QUOTE_01}}
```
* **Nguồn trích dẫn:** {{S01_TITLE}}, mục {{S01_SECTION_01}}.

### Đoạn trích 2 (Tương ứng Claim C02):
```text
{{S01_EXTENDED_QUOTE_02}}
```
* **Nguồn trích dẫn:** {{S01_TITLE}}, mục {{S01_SECTION_02}}.

---

## 5. CÁC HẠNG MỤC CẦN GẮN CỜ ([CẦN XÁC MINH])

* `{{FLAG_01}}`: [CẦN XÁC MINH: Nêu rõ khía cạnh chưa có số liệu hoặc đang chờ thông tư hướng dẫn từ địa phương].
* `{{FLAG_02}}`: [CẦN XÁC MINH: ...].

---

## 6. MA TRẬN TÁC ĐỘNG VÀ HÀNH ĐỘNG (IMPACT & ACTION MATRIX)

* **Ai cần hành động:** {{WHO_ACTS}}
* **Hành động cụ thể:**
  1. {{ACTION_STEP_1}}
  2. {{ACTION_STEP_2}}
  3. {{ACTION_STEP_3}}
* **Hậu quả nếu không thực hiện đúng hạn:** {{CONSEQUENCES}}

---

## 7. SỔ SỐ LIỆU (NUMBER LEDGER)

> Mọi con số và ngày sẽ có trong bài. `validate-article-draft.py` chặn số nào trong bài
> không có ở đây. Ngày ghi `YYYY-MM-DD`. Chép từ đúng ô của bảng gốc, ghi trang và dòng.

| Mã | Nội dung | Giá trị | Nguồn | Vị trí trong nguồn | Nguyên văn |
|---|---|---|---|---|---|
| N01 | {{N01_WHAT}} | {{N01_VALUE}} | S01 | {{N01_LOCATION}} | {{N01_VERBATIM}} |
| N02 | {{N02_WHAT}} | {{N02_VALUE}} | S01 | {{N02_LOCATION}} | {{N02_VERBATIM}} |

**Số tự tính** (tự nhân lại từng dòng trước khi ghi):

| Mã | Phép tính | Kết quả |
|---|---|---|
| K01 | {{K01_FORMULA}} | {{K01_RESULT}} |

---

## 8. SỔ ĐIỀU LUẬT (LAW CITATIONS)

> Mọi câu "theo Điều N Luật X" trong bài. Tra trên e-Gov, chép nguyên văn điều.

| Mã | Luật | Điều | Link e-Gov | Nguyên văn |
|---|---|---|---|---|
| L01 | {{L01_LAW}} | {{L01_ARTICLE}} | https://laws.e-gov.go.jp/law/{{L01_LAW_ID}} | {{L01_VERBATIM}} |

