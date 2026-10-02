---
name: viet-bai
display-name: Viết Bài Đa Kênh
description: >-
  Sáng tạo nội dung và viết bài tiếp thị đa nền tảng (Blog SEO, Website/Landing page, Facebook, Bài PR Báo chí) theo nguyên tắc Zero-Hallucination, tuân thủ pháp luật quảng cáo (Luật R5, có linter tự động) và khử dấu vết văn phong AI tiếng Việt; mọi số liệu có nguồn.
  USE WHEN: Người dùng cần viết bài blog SEO, bài đăng mạng xã hội, nội dung trang web/landing page, hoặc bài PR truyền thông.
  DO NOT USE WHEN: Cần dịch thuật văn bản đa ngôn ngữ (dùng 'ejv-translate'), biên tập tin tức thời sự Nhật Bản chuyên biệt (dùng 'chotto-newsroom'), dựng landing page có code (dùng 'tao-landing-page'), hoặc soạn thảo văn bản hành chính công quyền (dùng 'xu-ly-van-phong').
trigger: Viết bài, copywriting, viết blog SEO, bài đăng Facebook, nội dung website, bài PR
category: content
needs_file: false
file_filter: any
---

# Viết Bài Đa Kênh (v3)

Chuẩn đầu ra: bài mà biên tập viên marketing có kinh nghiệm đọc xong **không phải sửa**: đúng giọng thương hiệu, đúng người đọc, mọi con số có nguồn, không một câu vi phạm luật quảng cáo, không mùi văn máy.

> [!CAUTION]
> **NGUYÊN TẮC NỀN TẢNG: CHẠY 100% TRÊN ANTIGRAVITY (ZERO EXTERNAL API)**
> - Toàn bộ năng lực viết là của chính Agent trong IDE + công cụ tra cứu `search_web`. Không gọi REST API ngoài, không yêu cầu API key.
> - Autonomous Full-Run: chạy liên tục từ nghiên cứu đến bàn giao; chỉ hỏi lại người dùng ở Bước 1 khi thiếu thông tin bắt buộc.
> - Không có "đường tắt tiết kiệm token": BẮT BUỘC đọc các file chuẩn ở Bước 1 và chạy linter ở Bước 5 mỗi lần.

---

## 🔧 Path Resolution & Thư mục Lưu trữ Đầu ra

| Placeholder | Giá trị |
|---|---|
| `<skill_dir>` | `<workspace>/.agents/skills/viet-bai/` |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/` |
| `<process_dir>` | `<workspace>/_process/viet_bai_<chu_de>/` (đã gitignore) |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):** bài thành phẩm chỉ lưu vào `<output_dir>`; nháp và nguồn lưu trong `<process_dir>`. Không ghi file vào gốc repo.

---

## BƯỚC 1 — Tiếp nhận (Intake) & đọc chuẩn

### 1.1 Phiếu tiếp nhận (ghi vào `<process_dir>/brief.md`)
| Mục | Hỏi gì | Nếu người dùng không nói |
|---|---|---|
| Kênh | blog / web (landing) / facebook / pr | Suy từ yêu cầu; không rõ thì hỏi |
| Sản phẩm / ưu đãi | Bán gì, giá, điều kiện ưu đãi thật | **Hỏi** (không bịa ưu đãi) |
| Nhóm sản phẩm (`category`) | general / cosmetics / tpcn / drug / finance / medical_service | Suy từ sản phẩm; quyết định câu bắt buộc |
| Người đọc | Ai, đang gặp vấn đề gì, họ nói về vấn đề đó bằng lời nào | Viết giả định trong brief và ghi rõ là giả định |
| Giọng thương hiệu | 3 tính từ + 1 câu mẫu của thương hiệu (website/fanpage cũ) | Mặc định: rõ ràng, ấm, không phóng đại |
| Bằng chứng có sẵn | Số liệu, case study, chứng nhận, số phiếu công bố, phát ngôn đã duyệt | Chỉ dùng những gì tìm được ở Bước 2 |
| Mục tiêu hành động | Người đọc cần làm gì sau khi đọc | Một hành động duy nhất, cụ thể |

### 1.2 Đọc BẮT BUỘC trước khi viết
1. `<skill_dir>/standards/platform_guidelines.md`: mục ứng với kênh.
2. `<skill_dir>/standards/legal_claims_guideline.md`: danh sách cấm, câu bắt buộc theo nhóm sản phẩm, quy tắc nguồn.
3. `<skill_dir>/standards/anti_ai_footprint.md`: cụm sáo rỗng, dấu câu.
4. `<skill_dir>/examples/`: đọc ví dụ cùng kênh (bản TRƯỚC bị chặn vì sao, bản SAU đạt vì sao).
5. Template của kênh trong `<skill_dir>/templates/`.

---

## BƯỚC 2 — Tìm và khóa dữ liệu (Fact-Finding)

- Dùng `search_web` + tài liệu người dùng. Ghi `<process_dir>/facts_evidence.md`, mỗi dòng một sự thật:
  `| # | Sự thật (nguyên văn số liệu) | Nguồn (đơn vị, năm) | URL / file | Dùng ở đoạn nào |`
- Chỉ đưa vào bài những con số có trong bảng này. Nguồn độc lập > nguồn của hãng > "báo cáo nội bộ" (không dùng cho tuyên bố so sánh).
- Không tìm được nguồn: bỏ con số, hoặc ghi `[CẦN XÁC MINH: chưa có thống kê công bố chính thức]`.
- Phát ngôn người thật: chỉ dùng nguyên văn khách hàng cung cấp; nháp thì gắn `[CẦN XÁC NHẬN: <người> duyệt nguyên văn]`.

---

## BƯỚC 3 — Dàn ý

Ghi `<process_dir>/outline.md`: 1 câu thông điệp chính → các khối theo template kênh → mỗi khối ghi sự thật (# trong facts_evidence) sẽ dùng. Khối nào không có sự thật hỗ trợ thì viết bằng tình huống/cách làm, không bằng tuyên bố.

---

## BƯỚC 4 — Viết bản nháp `<process_dir>/draft.md`

- Mở bài bằng tình huống thật hoặc con số có nguồn (xem `examples/`). Không mở bằng câu chung chung.
- Lợi ích trước tính năng; mỗi lợi ích một bằng chứng.
- Con số/so sánh nào cũng có nguồn **cùng dòng**: `(Theo <đơn vị>, <năm>)`.
- Câu ngắn (≤ 30 từ), đoạn 2-4 câu, động từ mạnh; viết như người thật trong ngành nói với khách.
- Kết bài: một lời mời hành động cụ thể; thêm câu bắt buộc của nhóm sản phẩm (xem legal guideline mục 2).

---

## BƯỚC 5 — Quality Gate tự động (lặp đến khi exit 0)

```bash
python3 .agents/skills/viet-bai/scripts/fact_checker.py --input "<process_dir>/draft.md" --category <category> --channel <kênh>
```
- Script gọi `scripts/claim_guard.py --profile ads` (luật R5) và kiểm văn phong: em dash, dấu phẩy liệt kê, tiêu đề có `:`, cụm sáo rỗng, placeholder chưa điền, phát ngôn chưa xác nhận, thiếu câu bắt buộc.
- Exit 1 → sửa từng dòng được báo (dùng cột "Viết thay bằng" trong `legal_claims_guideline.md`) rồi chạy lại. Exit 2 → lỗi chạy, KHÔNG được coi là đạt; báo người dùng.
- Không "lách" linter bằng cách đổi chính tả hay thêm ký tự; sửa nội dung tuyên bố.
- Sau khi exit 0, Agent tự chấm thêm theo bảng dưới; mục nào < 4/5 thì sửa:

| Tiêu chí | 5/5 nghĩa là |
|---|---|
| Đúng người đọc | Dùng đúng vấn đề và từ ngữ của người đọc trong brief |
| Đúng giọng thương hiệu | Đọc to nghe như 3 tính từ trong brief |
| Bằng chứng | Mọi tuyên bố có số/case/nguồn; không câu "sáo" |
| Hành động | Người đọc biết rõ làm gì tiếp theo |
| Chuẩn kênh | Đúng độ dài, cấu trúc, định dạng của kênh |

---

## BƯỚC 6 — Bàn giao

Lưu `<output_dir>/<Ten_Bai_Viet>.md` (thêm `.docx`/`.html` nếu người dùng yêu cầu) và `<output_dir>/<Ten_Bai_Viet>_nguon.md` (bảng facts_evidence).

---

## 5. Quality Gate & Giao Thức Bàn Giao Sạch

### Checklist Kiểm Tra Chất Lượng (Quality Gate)
1. ✅ `fact_checker.py` exit 0 với đúng `--category` (đã bao gồm Luật R5 / claim_guard hồ sơ ads).
2. ✅ Evidence Verifier: mọi con số, xếp hạng, so sánh có trong `facts_evidence.md` và có nguồn cùng dòng trong bài.
3. ✅ Confidence Flagging: chỗ chưa có số liệu chính thức mang `[CẦN XÁC MINH: ...]`; phát ngôn chưa duyệt mang `[CẦN XÁC NHẬN: ...]`, và được liệt kê khi bàn giao.
4. ✅ Có câu bắt buộc của nhóm sản phẩm (mỹ phẩm, TPBVSK, thuốc, tài chính).
5. ✅ Tự chấm 5 tiêu chí ≥ 4/5.
6. ✅ File thành phẩm trong `<output_dir>` (mặc định `~/Downloads/AIWF_Output/`).

### Giao thức Bàn giao Sạch
Khung chat chỉ báo: kênh, số từ, thông điệp chính, kết quả linter (exit 0), danh sách cờ `[CẦN XÁC MINH]` / `[CẦN XÁC NHẬN]` còn lại để người dùng xử lý, và đường dẫn file có thể click mở.

### Kiểm thử bộ lọc (khi sửa script/chuẩn)
```bash
python3 .agents/skills/viet-bai/tests/run_tests.py
```
Phải bắt đủ mọi vi phạm trong `tests/bad.md`, để `tests/clean.md` và các bản "SAU" trong `examples/` đạt, và template không chứa câu vi phạm.
