# LUẬT R4: TIÊU CHUẨN KIẾN TRÚC & KIỂM ĐỊNH KỸ NĂNG (SKILL STANDARD V1.2)
## Chuẩn Google Antigravity 2.0 & Mô Hình Lõi Gemini 3.8 Multi-Agent

> **Mã quy tắc:** R4 (Hệ Thống Quy Tắc Vận Hành Cốt Lõi AIWF)  
> **Phiên bản:** 1.2 (Gemini 3.8 Multi-Agent Architecture)  
> **Phạm vi áp dụng:** Toàn bộ nhân sự số, kỹ năng (Skills) hiện có và mọi kỹ năng mới nạp vào `.agents/skills/`  
> **Lĩnh vực bao quát:** Áp dụng trung lập (Domain-Agnostic) cho cả nhóm **Reasoning Engine** (Pháp lý, Tài chính, Kế toán, Kiểm toán, Kho vận) và nhóm **Factory Engine** (Marketing, Content, Copywriting, Thiết kế văn phòng, Slide/Pitch Deck, UI/UX).

---

## 1. NGUYÊN LÝ NỀN TẢNG: HAI ĐỘNG CƠ TƯ DUY CỦA SKILL

Mọi kỹ năng trong AI Workforce đều phải được phân loại và thiết kế dựa trên 1 trong 2 động cơ cốt lõi:

| Động cơ | Lĩnh vực áp dụng | Bản chất vận hành | Quy chuẩn thiết kế bắt buộc |
|---|---|---|---|
| **THE REASONING ENGINE** *(Động cơ Lý tính)* | **Pháp lý, Tài chính, Kế toán, Kiểm toán, Rủi ro, Kho vận** | Đối chiếu Nguồn Sự Thật Duy Nhất (SSOT), tính toán số liệu chính xác, tư duy đa tầng không sai số. | • Định danh 5 Trục Tọa độ đầu vào.<br>• Sổ cái làm việc vật lý N+1 (`phase_{N+1}.md`).<br>• Chu trình **PDCA Cascade** ([P]lan $\rightarrow$ [D]o $\rightarrow$ [C]heck $\rightarrow$ [A]ct).<br>• Bảng SOT trích dẫn nguyên văn có tọa độ (Điều/Khoản/Mục).<br>• **Live Formulas:** 100% công thức động trong Excel.<br>• **Confidence Flagging:** Gắn cờ cảnh báo khi mờ/nghi ngờ. |
| **THE FACTORY ENGINE** *(Động cơ Sản xuất)* | **Marketing, Sáng tạo Nội dung, Copywriting, Soạn thảo Văn phòng, UI/UX** | Bóc tách cấu trúc dữ liệu, tái tạo sản phẩm thẩm mỹ cao, đồng bộ nhận diện thương hiệu. | • Bảng Menu tùy chọn (Hỏi trước khi làm - RRI).<br>• Đường ray đôi (Chuẩn công quyền nghiêm ngặt vs Chuẩn doanh nghiệp hiện đại).<br>• Kiến trúc 2 Chiều: Bóc tách (Extractor) $\rightarrow$ Tái tạo (Generator).<br>• Tách rời Dữ liệu (Content) và Thẩm mỹ (Brand Kit).<br>• Bộ lọc khử triệt để dấu vết văn phong AI tiếng Việt. |

---

## 2. KHUNG KIẾN TRÚC 5 LỚP GEMINI 3.8 (THE 5-LAYER STANDARD)

Mỗi kỹ năng được nạp vào AIWF bắt buộc phải đáp ứng đầy đủ 5 tầng kiến trúc vật lý và logic:

```
┌────────────────────────────────────────────────────────────────────────┐
│ LỚP 1: METADATA & TRIGGER CONTRACT (Hợp đồng Router Gemini 3.8)         │
│  - YAML Frontmatter: name, description (Biên độ làm & KHÔNG làm gì)    │
│  - argument-hint: Gợi ý đối số autocomplete trên UI                    │
│  - allowed-tools: Phân quyền công cụ chạy tự chủ không pop-up          │
│  - effort: Định cấu hình ngân sách tư duy Gemini 3.8 (low|medium|high) │
│  - context: fork (Cô lập subagent cho tác vụ dài/nặng)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 2: INTAKE & ANTI-REPO BLOAT (Tọa độ & Bảo vệ Codebase)             │
│  - Hệ thống tọa độ đầu vào / Menu chọn luồng (RRI Pattern)             │
│  - Path Resolution: <output_dir> mặc định ~/Downloads/ (Cấm ghi repo)  │
│  - Vùng xử lý tạm _process/ (được bảo vệ bởi .gitignore)               │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 3: THE AUTONOMOUS ENGINE (Động cơ Thực thi Khép kín)               │
│  - Zero External API: 100% LLM nội bộ Antigravity, cấm đòi API key     │
│  - Autonomous Full-Run: Tự động chạy đến cùng, không dừng xin phép     │
│  - Live Formulas: Bắt buộc dùng công thức sống trong file bảng tính    │
│  - Lưu vết tiến trình vật lý (Working Ledger / Checkpoints)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 4: MODULAR CODE & STORAGE (Cấu trúc Thư mục Vật lý)                │
│  - Phân tầng: resources/, standards/, scripts/, templates/, examples/ │
│  - Atomic Scripts: Mỗi script Python/Node.js làm duy nhất 1 việc       │
│  - Script hợp lệ cú pháp, không lỗi runtime                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 5: QUALITY GATE & CLEAN DELIVERY (Kiểm định & Bàn giao Sạch)       │
│  - Checklist n-điểm tự đánh giá trước khi xuất bản                     │
│  - Confidence Flagging: Gắn cờ [CẦN XÁC MINH] khi OCR/suy luận < 85%   │
│  - Kiểm chứng bằng chứng (Evidence Verifier: trích dẫn nguyên văn SSOT)│
│  - Quy tắc Khử dấu vết AI (Anti-AI Footprint Cleansing)                │
│  - Giao thức Bàn giao Sạch: File thành phẩm riêng, chat chỉ tóm tắt    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2.1 GIẢI PHẪU YAML FRONTMATTER CHUẨN GEMINI 3.8

Lớp siêu dữ liệu đầu file `SKILL.md` đóng vai trò là **Bộ định tuyến (Semantic Router)** của Gemini 3.8:

```yaml
---
name: ten-skill # Tên kỹ thuật: kebab-case tiếng Anh hoặc không dấu (vd: phu-de, thiet-ke)
display-name: Tên Kỹ Năng # Tên hiển thị UI: BẮT BUỘC tiếng Việt có dấu hoặc tiếng Anh đúng chính tả (vd: Tạo Phụ Đề, EJV Translate)
description: Mô tả chức năng chi tiết, bối cảnh kích hoạt, và ranh giới rõ ràng. Bắt buộc có câu phủ định: "KHÔNG dùng cho [việc X], chuyển sang [skill Y]".
trigger: Từ khóa kích hoạt nhanh từ người dùng
argument-hint: [tham_số_1] [tham_số_2]
allowed-tools: [run_command, view_file, write_to_file, replace_file_content]
effort: high # high: lập luận sâu/pháp lý/toán; medium: văn phòng/dịch; low: tra cứu nhanh
interaction-mode: direct # direct (mặc định) | review (dừng duyệt trước khi render) | interactive (Webview tương tác 2 chiều)
context: fork # Tùy chọn: ép chạy trong subagent độc lập nếu tác vụ xử lý file nặng/nhiều trang
disable-model-invocation: false # true nếu là tác vụ nguy hiểm cần user gõ lệnh / trực tiếp
needs_file: true # true nếu bắt buộc có file đầu vào
file_filter: office # office | pdf | code | any
---
```

### 2.1.1 QUY TẮC ĐỊNH DANH & TÊN HIỂN THỊ (SKILL NAMING CONVENTION)

Để đảm bảo tính thẩm mỹ, nhất quán và trải nghiệm người dùng cao cấp:
1. **Tên Định Danh Kỹ Thuật (`name` / Thư mục):** Sử dụng `kebab-case` chữ thường không dấu (ví dụ: `phu-de`, `boc-tach-pdf`, `ejv-translate`, `tu-van-phap-luat`). Đảm bảo tính tương thích 100% với Git, CLI shell, đường dẫn file system và URL.
2. **Tên Hiển Thị Giao Diện (`display-name` / Nhãn UI / Tiêu đề SKILL.md):**
   - **BẮT BUỘC PHẢI LÀ TIẾNG VIỆT CÓ DẤU HOẶC TIẾNG ANH ĐÚNG CHÍNH TẢ.**
   - Ví dụ hợp chuẩn: *"Tạo Phụ Đề"*, *"Bóc Tách PDF"*, *"Tư Vấn Pháp Luật"*, *"Xử Lý Văn Phòng"*, *"Viết Bài Đa Kênh"*, *"Thiết Kế Đồ Họa"*, *"Báo Cáo Kế Toán"*, *"EJV Translate"*.
   - ❌ **NGHIÊM CẤM** sử dụng tiếng Việt không dấu làm tên hiển thị (ví dụ: cấm dùng *"Phu De"*, *"Boc Tach"*, *"Thiet Ke"*, *"Xu Ly Van Phong"* trên giao diện).
3. **Đồng Bộ Giao Diện IDE Extension:** Khi thêm một skill mới, bắt buộc:
   - Khai báo trường `display-name` trong YAML Frontmatter của `SKILL.md`.
   - Bổ sung entry tương ứng vào `ICON_MAP` trong [`extension/lib/icons.js`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/extension/lib/icons.js) với icon, màu gradient và nhãn hiển thị tiếng Việt có dấu.

---

## 2.2 CẤU TRÚC THÂN PROMPT BẰNG THẺ XML (GEMINI 3.8 OPTIMIZATION)

Để tối đa hóa khả năng nhận thức của Gemini 3.8 và ngăn ngừa hiện tượng nhầm lẫn giữa dữ liệu thô và lệnh điều khiển, phần thân `SKILL.md` hoặc các hướng dẫn thực thi lớn nên phân định bằng các thẻ XML:
* `<goal>`: Tuyên bố mục tiêu tối thượng và kết quả đầu ra mong đợi.
* `<context>`: Ngữ cảnh nghiệp vụ, quy chuẩn pháp lý hoặc phong cách thương hiệu.
* `<instructions>`: Quy trình thực thi từng bước (SOP) tuần tự.
* `<constraints>`: Các ranh giới cấm tuyệt đối (5 Absolute Bans).
* `<working_ledger>`: Định dạng lưu vết tiến trình vật lý (`_process/` hoặc file `phase_N.md`).
* `<quality_gate>`: Tiêu chí kiểm định, checklist trước khi xuất bản và gắn cờ cảnh báo.
* `<delivery_protocol>`: Giao thức xuất file ra `<output_dir>` và phản hồi ngắn gọn trên chat.

---

## 2.3 TRIẾT LÝ CONFIDENCE FLAGGING (CHỐNG ẢO GIÁC OCR VÀ SUY LUẬN)

Đối với các kỹ năng thuộc nhóm **Reasoning Engine** (Bóc tách scan, Pháp luật, Kế toán, Kiểm toán):
1. **Tuyệt đối cấm đoán mò:** Khi ảnh scan bị mờ, vết ố che khuất ký tự, hoặc điều luật có nhiều cách giải thích mâu thuẫn:
   - **ĐỘ TIN CẬY $\ge 85\%$:** Xử lý bình thường.
   - **ĐỘ TIN CẬY $< 85\%$:** Bắt buộc gắn cờ `[CẦN XÁC MINH: <lý_do_chi_tiết>]` vào bản nháp/báo cáo.
2. **Hàng đợi kiểm chứng:** Nếu phát hiện dữ liệu nhạy cảm (số tiền, số hợp đồng, điều khoản phạt) không rõ ràng, xuất file danh sách `_process/needs_human_verification.json` để người dùng xác nhận, không âm thầm bịa đặt số liệu.

---

## 2.4 TIÊU CHUẨN DỮ LIỆU SỐNG (LIVE FORMULAS FOR SPREADSHEETS)

Đối với kỹ năng tạo hoặc sửa file bảng tính Excel (`xlsx`):
* Bắt buộc sử dụng công thức tính toán sống (`SUM`, `AVERAGE`, `COUNTIF`, `IF`, `VLOOKUP`, `XLOOKUP`, `INDEX/MATCH`...).
* **NGHIÊM CẤM TÍNH NHẨM:** Tuyệt đối cấm tác nhân tính nhẩm bằng LLM rồi gõ con số tĩnh (Hardcoded Number) vào ô kết quả tổng hoặc chỉ số tài chính. Con người khi mở file Excel phải xem được công thức toán học liên kết.

---

## 2.5 TIÊU CHUẨN INTERACTIVE SKILL PATTERN & HUMAN CHECKPOINT GATE

Đối với các kỹ năng đa phương tiện / trực quan (`phu-de`, `thiet-ke`, `boc-tach-pdf`, `bao-cao-kt`):
1. **Ba Chế độ Tương tác (Interaction Modes):**
   - `direct` *(Mặc định)*: Chạy tự chủ khép kín một mạch từ đầu đến cuối (Batch pipeline).
   - `review` *(Kiểm duyệt)*: Tạo kết quả nháp $\rightarrow$ dừng tại Quality Gate Checkpoint trên chat để người dùng xác nhận $\rightarrow$ hoàn tất.
   - `interactive` *(Tương tác 2 chiều)*: Khởi tạo **Editable Project State** (`_process/<id>/project.json`) $\rightarrow$ mở **Temporary UI** (Webview Editor Tab trong IDE) để người dùng xem trực quan, tinh chỉnh thông số và phối hợp vòng lặp AI Edit với Agent $\rightarrow$ bấm Xác nhận (Finalize) $\rightarrow$ Render & Export.
2. **Nguyên tắc Editable Project State:**
   - Single Source of Truth đặt tại `<process_dir>/project.json`.
   - Bắt buộc gắn **Stable Object IDs** cho mọi thực thể có thể chỉnh sửa (`id: string`).
   - Hỗ trợ lưu vết lịch sử Revisions/Snapshots để Undo/Redo tức thì.
3. **Phân định rõ Local Action vs Agent Action:**
   - **Local Action:** Đổi màu, đổi font, căn lề, crop, chỉnh mốc thời gian, gõ sửa trực tiếp $\rightarrow$ Client xử lý tức thời (0ms, 0 token).
   - **Agent Action:** Lệnh ngữ nghĩa ("Rút ngắn câu", "Chuyển giọng điệu", "Tái cấu trúc bố cục") $\rightarrow$ gửi Action Request về Agent $\rightarrow$ Agent trả Structured Patch cục bộ tác động đúng các Object ID được chọn, không viết lại toàn bộ dự án.

---

## 3. NĂM ĐIỀU CẤM TUYỆT ĐỐI (5 ABSOLUTE BANS)

Bất kỳ kỹ năng nào vi phạm 1 trong 5 điều cấm dưới đây đều bị đánh giá **FAIL NGHIÊM TRỌNG (Hard Stop)**:

1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY (Zero External API Violation):**
   - 100% logic suy luận thuộc về LLM nội bộ Antigravity. Cấm gọi REST API ngoài (Gemini/OpenAI API) hoặc bắt cấu hình API key trong code.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE (Anti-Repo Bloat Violation):**
   - File kết quả (`.docx`, `.xlsx`, `.pptx`, `.pdf`, `.md`) PHẢI lưu vào `<output_dir>` (mặc định: `~/Downloads/`). Cấm tự ý ghi đè file rác vào kho mã nguồn làm phình Git repo.
3. ❌ **CẤM SỐ LIỆU VÀ ĐỒ THỊ CHẾT (Dead Data Violation):**
   - Cấm gõ số chết vào ô công thức Excel; cấm chụp ảnh màn hình chèn vào làm biểu đồ chết trong slide/báo cáo.
4. ❌ **CẤM VĂN PHONG VÀ DẤU CÂU "MÙI AI" (Anti-AI Footprint Violation):**
   - Cấm gạch ngang dài `—` (dùng ` - ` hoặc liên từ nối); cấm Oxford comma `, và`; cấm dấu hai chấm cuối heading; cấm ngôn từ sáo rỗng (*"Trong kỷ nguyên số...", "Đóng vai trò then chốt..."*).
5. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP (Autonomous Full-Run Violation):**
   - Skill phải tự chạy tuần tự đến khi hoàn thành 100%. Cấm dừng giữa chừng để hỏi những câu thừa thãi (*"Tôi có nên tiếp tục không?"*).
   - *Lưu ý hợp lệ với Interactive/Review Skill:* Điểm dừng tại **Human Checkpoint Gate** (mở Webview Editor Tab hoặc chờ duyệt tại cổng Quality Gate đã định nghĩa trước) là điểm tương tác chủ đích hợp lệ, KHÔNG vi phạm quy tắc này. Sau khi người dùng xác nhận Finalize, Agent phải tự động chạy tiếp đến cùng khâu Render/Bàn giao.

---

## 4. QUY TRÌNH TỰ ĐỘNG KIỂM DUYỆT SKILL (AUTO-VETTING PROTOCOL)

* **Runtime Interceptor:** Trước khi chạy một skill chưa có trong `.agents/skills/.certified.json`, Agent bắt buộc chạy:
  ```bash
  python3 scripts/audit_skill.py <đường_dẫn_skill>
  ```
* **Điều kiện Đạt Chuẩn (Certified):**
  * Tổng điểm $\ge \mathbf{85/100}$
  * **KHÔNG vi phạm bất kỳ lỗi Hard Stop nào** tại các tầng L1, L2, L3, L4.

---

## 5. BẢNG ĐIỂM THẨM ĐỊNH SKILL CHUẨN GEMINI 3.8 (AUDIT SCORECARD - 100 ĐIỂM)

| Tầng | Tiêu chí Kiểm tra Chi tiết | Điểm | Loại lỗi nếu vi phạm |
|:---:|---|:---:|:---:|
| **L1** | **YAML Frontmatter Gemini 3.8:** Có `name`, `description` (ranh giới phủ định), `trigger`, `argument-hint`, `allowed-tools`, `effort`. | **20** | Thiếu `name`/`desc` $\rightarrow$ **FAIL**; thiếu trường nâng cao $\rightarrow$ **WARN** |
| **L2** | **Path Resolution & Anti-Bloat:** Khai báo `<output_dir>`, mặc định `~/Downloads/`, thư mục tạm `_process/`, không hardcode codebase. | **20** | Hardcode codebase $\rightarrow$ **FAIL** |
| **L3** | **Zero-API & Live Engine:** Không gọi External API, tự chạy liên tục (Autonomous), quy định Live Formulas cho bảng tính. | **20** | Gọi API ngoài $\rightarrow$ **FAIL** |
| **L4** | **Cấu trúc Thư mục & Scripts Integrity:** Có thư mục module hóa, atomic scripts, toàn bộ script Python/JS không lỗi cú pháp. | **20** | Script lỗi cú pháp $\rightarrow$ **FAIL** |
| **L5** | **Quality Gate & Confidence Flagging:** Checklist nghiệm thu, quy tắc Confidence Flagging khi mờ/nghi ngờ, khử dấu vết AI tiếng Việt, bàn giao sạch. | **20** | Thiếu checklist $\rightarrow$ **WARN** |

