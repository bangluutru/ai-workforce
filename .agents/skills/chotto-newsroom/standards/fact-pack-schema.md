# CẤU TRÚC GÓI SỰ THẬT KIỂM CHỨNG (FACT PACK SCHEMA)

> Quy chuẩn cấu trúc hóa dữ liệu kiểm chứng sự thật (Fact Pack).
> Mọi bài viết trước khi được viết lời văn bắt buộc phải có một Fact Pack hoàn chỉnh nhằm triệt tiêu hoàn toàn ảo giác (Zero-Hallucination) và bảo đảm tính truy vết 100%.

---

## 1. CẤU TRÚC TỔNG THỂ CỦA FACT PACK

Mỗi file Fact Pack (định dạng Markdown) bao gồm 6 phần bắt buộc:

```markdown
# GÓI SỰ THẬT KIỂM CHỨNG: [MÃ SỰ KIỆN] - [TIÊU ĐỀ SỰ KIỆN]

## 1. THÔNG TIN ĐỊNH DANH SỰ KIỆN (METADATA)
- Mã sự kiện: [EVT-YYYYMMDD-XX]
- Chủ đề: [Tên chính sách / Thay đổi luật]
- Cơ quan ban hành: [Tên cơ quan tiếng Nhật và tiếng Việt]
- Ngày công bố chính thức: [YYYY-MM-DD]
- Ngày bắt đầu có hiệu lực: [YYYY-MM-DD]
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
```

---

## 2. CHI TIẾT MA TRẬN TUYÊN BỐ SỰ THẬT (KEY CLAIMS MATRIX)

Mỗi tuyên bố trong bài viết phải được phân rã thành một dòng trong bảng:

| Mã Claim | Tuyên bố sự thật (Tiếng Việt) | Mã Nguồn | Trích dẫn nguyên văn (Tiếng Nhật) | Mức tin cậy | Trạng thái thẩm định |
|:---:|---|:---:|---|:---:|:---:|
| **C01** | Lương tối thiểu vùng Tokyo tăng lên 1.163 yên/giờ | S01 | 「東京都の最低賃金を1,163円に引き上げる」 | High (100%) | Đã xác minh |
| **C02** | Thời điểm áp dụng chính thức từ ngày 01/10/2026 | S01 | 「発効日は令和8年10月1日とする」 | High (100%) | Đã xác minh |
| **C03** | Doanh nghiệp không tuân thủ sẽ bị xử phạt theo Điều 119 Luật Tiêu chuẩn Lao động | S02 | 「最低賃金法第4条の規定に違反した者は…罰金に処する」 | High (95%) | Đã xác minh |
| **C04** | Trợ cấp phụ thuộc có thể thay đổi cách tính từ đầu năm sau | S03 | 「見直しの検討を進めている段階」 | Medium (75%) | [CẦN XÁC MINH: Đang dự thảo] |

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
