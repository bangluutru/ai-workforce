# LUẬT R4: TIÊU CHUẨN KIẾN TRÚC & KIỂM ĐỊNH KỸ NĂNG (SKILL STANDARD V1.0)

> **Mã quy tắc:** R4 (Thuộc Hệ Thống Quy Tắc Vận Hành Cốt Lõi AIWF)  
> **Phiên bản:** 1.0 (Standard Specification)  
> **Phạm vi áp dụng:** Toàn bộ nhân sự số, kỹ năng (Skills) hiện có và mọi kỹ năng mới được nạp vào thư mục `.agents/skills/`  
> **Lĩnh vực bao quát:** Áp dụng trung lập (Domain-Agnostic) cho cả nhóm **Logic/Tính toán/Tuân thủ** (Pháp lý, Tài chính, Kế toán, Kiểm toán, Kho vận) và nhóm **Sáng tạo/Sản xuất/Thẩm mỹ** (Marketing, Content, Copywriting, Thiết kế văn phòng, Slide/Pitch Deck).

---

## 1. NGUYÊN LÝ NỀN TẢNG: HAI ĐỘNG CƠ TƯ DUY CỦA SKILL

Mọi kỹ năng trong AI Workforce đều phải được phân loại và thiết kế dựa trên 1 trong 2 động cơ cốt lõi:

| Động cơ | Lĩnh vực áp dụng | Bản chất vận hành | Quy chuẩn thiết kế bắt buộc |
|---|---|---|---|
| **THE REASONING ENGINE** *(Động cơ Lý tính)* | **Pháp lý, Tài chính, Kế toán, Kiểm toán, Rủi ro, Quản trị kho** | Đối chiếu Nguồn Sự Thật Duy Nhất (SSOT), tính toán số liệu chính xác, tư duy đa tầng không sai số. | • Định danh 5 Trục Tọa độ đầu vào.<br>• Sổ cái làm việc vật lý N+1 (`phase_{N+1}.md`).<br>• Chu trình **PDCA Cascade** ([P]lan $\rightarrow$ [D]o $\rightarrow$ [C]heck $\rightarrow$ [A]ct).<br>• Bảng SOT trích dẫn nguyên văn có tọa độ (Điều/Khoản/Mục).<br>• Công thức tính toán phải sống (Live Formulas). |
| **THE FACTORY ENGINE** *(Động cơ Sản xuất)* | **Marketing, Sáng tạo Nội dung, Copywriting, Soạn thảo Văn phòng, Slide Pitch Deck** | Bóc tách cấu trúc dữ liệu, tái tạo sản phẩm thẩm mỹ cao, đồng bộ nhận diện thương hiệu. | • Bảng Menu tùy chọn (Hỏi trước khi làm - RRI).<br>• Đường ray đôi (Chuẩn công quyền nghiêm ngặt vs Chuẩn doanh nghiệp hiện đại).<br>• Kiến trúc 2 Chiều: Bóc tách (Extractor) $\rightarrow$ Tái tạo (Generator).<br>• Tách rời Dữ liệu (Content) và Thẩm mỹ (Brand Kit).<br>• Bộ lọc khử triệt để dấu vết văn phong AI. |

---

## 2. KHUNG KIẾN TRÚC 5 LỚP BẮT BUỘC (THE 5-LAYER STANDARD)

Mỗi kỹ năng được nạp vào AIWF bắt buộc phải đáp ứng đầy đủ 5 tầng kiến trúc vật lý và logic:

```
┌────────────────────────────────────────────────────────────────────────┐
│ LỚP 1: METADATA & TRIGGER CONTRACT (Hợp đồng kích hoạt)                 │
│  - YAML Frontmatter: name, description (Làm gì & KHÔNG làm gì), trigger│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 2: INTAKE & ANTI-REPO BLOAT (Tọa độ & Bảo vệ Codebase)             │
│  - Hệ thống tọa độ đầu vào / Menu chọn luồng (RRI Pattern)             │
│  - Path Resolution: <output_dir> mặc định ~/Downloads/ (Cấm ghi repo)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 3: THE AUTONOMOUS ENGINE (Động cơ Thực thi Khép kín)               │
│  - Zero External API: 100% chạy bằng Agent nội bộ, cấm đòi API key     │
│  - Autonomous Full-Run: Tự động chạy đến cùng, không dừng xin phép      │
│  - Lưu vết tiến trình vật lý (Working Ledger / Checkpoints)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 4: MODULAR CODE & STORAGE (Cấu trúc Thư mục Vật lý)                │
│  - Phân tầng: resources/, standards/, scripts/, templates/, examples/ │
│  - Script Python / Node.js hợp lệ cú pháp, không lỗi runtime           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ LỚP 5: QUALITY GATE & CLEAN DELIVERY (Kiểm định & Bàn giao Sạch)       │
│  - Checklist n-điểm tự đánh giá trước khi xuất bản                     │
│  - Kiểm chứng bằng chứng (Evidence Verifier: trích dẫn nguyên văn SSOT)│
│  - Quy tắc Khử dấu vết AI (Anti-AI Footprint Cleansing)                │
│  - Giao thức Bàn giao Sạch: File thành phẩm riêng, chat chỉ tóm tắt    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2.1 VÒNG ĐỜI TÁC VỤ 3 BƯỚC SIÊU TỐC (FAST 3-STEP TASK LIFECYCLE)

Để đảm bảo tối đa **TỐC ĐỘ** và **ĐỘ CHÍNH XÁC**, mọi tác vụ do Skill thực thi đều tuân thủ vòng đời 3 bước tinh gọn:

```
[1. INTAKE]              [2. EXECUTE & VERIFY]               [3. CLEAN DELIVERY]
File đầu vào / Yêu cầu → Xử lý tại _process/              → Xuất file ra ~/Downloads/
Đối chiếu mẫu chuẩn      Đối chiếu Evidence Verifier        Chat báo link trực tiếp
                         (Chống bịa số/điều luật)           Dọn dẹp thư mục tạm
```

1. **Bước 1 — INTAKE (Tiếp nhận chuẩn):**
   - Nhận diện file nguồn, xác định đúng định dạng và đối chiếu template chuẩn (Read-only).
   - Xác định rõ thư mục đích `<output_dir>` (mặc định: `~/Downloads/` hoặc nơi người dùng chỉ định).
2. **Bước 2 — EXECUTE & VERIFY (Xử lý & Kiểm chứng thực tế):**
   - Mọi hoạt động bóc tách, nháp, ráp nối thực hiện trong thư mục tạm `_process/` (được bảo vệ bởi `.gitignore`).
   - Đối với nhóm Lý tính (Pháp luật, Tài chính, Báo cáo): Bắt buộc kiểm chứng trích dẫn nguyên văn (`verbatim_quote`) với nguồn SSOT thông qua công cụ `scripts/harness/evidence_verifier.py`.
   - Cấm đoán mò hoặc suy diễn ngoài phạm vi tài liệu nguồn.
3. **Bước 3 — CLEAN DELIVERY (Bàn giao sạch):**
   - Xuất bản file kết quả hoàn chỉnh vào `<output_dir>`.
   - Khung chat chỉ phản hồi tóm tắt ngắn gọn (3-5 gạch đầu dòng) và đường dẫn file có thể click mở ngay.
   - Tự động dọn dẹp các file nháp trung gian để giữ môi trường luôn sạch sẽ.

---

## 3. NĂM ĐIỀU CẤM TUYỆT ĐỐI KHI XÂY DỰNG SKILL (5 ABSOLUTE BANS)

Bất kỳ kỹ năng nào vi phạm 1 trong 5 điều cấm dưới đây đều bị đánh giá **FAIL NGHIÊM TRỌNG (Hard Stop)** và không được phép vận hành:

1. ❌ **CẤM ĐÒI HỎI EXTERNAL API KEY (Zero External API Violation):**
   - Nghiêm cấm mọi lời gọi REST API bên ngoài (Gemini API, OpenAI API, Claude API) hoặc yêu cầu người dùng cấu hình API key trong code. Toàn bộ trí tuệ nhân tạo là năng lực tích hợp sẵn của Agent trong IDE.
2. ❌ **CẤM XUẤT FILE THÀNH PHẨM VÀO CODEBASE (Anti-Repo Bloat Violation):**
   - Mọi skill khi xuất bản tài liệu (`.docx`, `.xlsx`, `.pptx`, `.pdf`, báo cáo `.md`) PHẢI cho phép người dùng chọn thư mục hoặc mặc định lưu vào `<output_dir>` (`~/Downloads/`).
   - Tuyệt đối cấm tự ý tạo thư mục kết quả hoặc ghi đè file rác vào thư mục gốc của codebase làm phình dung lượng git repo.
3. ❌ **CẤM SỐ LIỆU VÀ ĐỒ THỊ CHẾT (Dead Data Violation):**
   - Đối với file Excel: Bắt buộc dùng công thức sống (Live Formulas: `SUM`, `AVERAGE`, `VLOOKUP`...). Cấm tính nhẩm rồi gõ số chết vào ô.
   - Đối với Slide/Báo cáo: Bóc tách Data từ biểu đồ/sơ đồ và vẽ lại bằng code sống (Live charts/shapes), cấm chụp ảnh màn hình chèn vào làm ảnh chết (trừ logo thương hiệu).
4. ❌ **CẤM VĂN PHONG VÀ DẤU CÂU "MÙI AI" (Anti-AI Footprint Violation):**
   - Cấm dùng gạch ngang dài kiểu tiếng Anh: `—` (thay bằng ` - ` hoặc liên từ nối).
   - Cấm dùng dấu phẩy Oxford: `, và` (tiếng Việt chuẩn chỉ dùng `và`).
   - Cấm đặt dấu hai chấm cuối tiêu đề/heading (ví dụ: `### 1. Mục tiêu:` $\rightarrow$ sửa thành `### 1. Mục tiêu`).
   - Cấm ngôn từ sáo rỗng (nhất là trong Marketing/Content): *"Trong kỷ nguyên số...", "Đóng vai trò then chốt...", "Như chúng ta đã biết..."*.
5. ❌ **CẤM DỪNG DỞ DANG ĐỂ XIN PHÉP (Autonomous Full-Run Violation):**
   - Khi đã nhận lệnh, skill phải tự động thực thi tuần tự từ đầu đến cuối (bóc tách $\rightarrow$ xử lý/dịch $\rightarrow$ ghép nối $\rightarrow$ kiểm tra $\rightarrow$ xuất bản).
   - Cấm dừng lại giữa chừng chỉ để hỏi những câu thừa thãi: *"Tôi có nên tiếp tục không?"*.

---

## 4. QUY TRÌNH TỰ ĐỘNG KIỂM DUYỆT SKILL (AUTO-VETTING PROTOCOL)

Hệ thống duy trì cơ chế tự động bảo vệ qua 3 cấp độ:

### Cấp độ 1: Tự kiểm duyệt lúc Runtime (Agent Interceptor)
- Khi Agent được yêu cầu thực thi một skill mới hoặc một skill chưa có tên trong chứng chỉ [`.agents/skills/.certified.json`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/.agents/skills/.certified.json):
- **Agent BẮT BUỘC PHẢI tự động chạy lệnh kiểm định trước:**
  ```bash
  python3 scripts/audit_skill.py <đường_dẫn_skill>
  ```
- Nếu đạt điểm $\ge 85/100$ (không lỗi Hard Stop): Tiếp tục thực thi và cấp chứng nhận.
- Nếu không đạt chuẩn: Agent dừng lại, báo cáo chi tiết các lỗi cần khắc phục cho người dùng hoặc chủ động đề xuất bản vá phẫu thuật (Auto-Patch).

### Cấp độ 2: Kiểm duyệt tại Cổng Khởi động & Git (CLI Gatekeeper)
- Mỗi khi khởi tạo môi trường (`bash scripts/auto-setup.sh`) hoặc trước khi commit/push Git, script `audit_skill.py` sẽ tự động quét kiểm tra tính toàn vẹn của danh mục skill.
- Phát hiện thư mục lạ hoặc cấu trúc hỏng $\rightarrow$ In cảnh báo trên bảng điều khiển.

---

## 5. BẢNG ĐIỂM THẨM ĐỊNH SKILL CHUẨN (AUDIT SCORECARD - 100 ĐIỂM)

Script `scripts/audit_skill.py` sẽ chấm điểm theo thang 100 dựa trên bảng tiêu chí sau:

| Tầng | Tiêu chí Kiểm tra Chi tiết | Điểm | Loại lỗi nếu vi phạm |
|:---:|---|:---:|:---:|
| **L1** | **YAML Frontmatter Hợp lệ:** Có `name`, `description` phân định rõ ranh giới làm gì/không làm gì, có `trigger` cụ thể. | **20** | Thiếu $\rightarrow$ **FAIL** |
| **L2** | **Path Resolution & Anti-Bloat:** Khai báo `<output_dir>`, mặc định `~/Downloads/`, thư mục tạm `_process/`, không hardcode đường dẫn codebase. | **20** | Hardcode codebase $\rightarrow$ **FAIL** |
| **L3** | **Zero External API & Autonomous:** Không yêu cầu external API key, không chứa mã độc hoặc gọi API ngoài, quy trình tự chạy liên tục. | **20** | Yêu cầu API key ngoài $\rightarrow$ **FAIL** |
| **L4** | **Cấu trúc Vật lý & Script Integrity:** Có tổ chức thư mục module (`resources/`, `standards/`, `scripts/`...), toàn bộ script Python/JS không lỗi cú pháp. | **20** | Script lỗi cú pháp $\rightarrow$ **FAIL** |
| **L5** | **Quality Gate & Delivery Protocol:** Có checklist tự nghiệm thu đầu ra, quy tắc khử dấu vết AI, giao thức xuất file rời và tóm tắt chat ngắn gọn. | **20** | Thiếu checklist $\rightarrow$ **WARN** |

> 🏆 **Điều kiện Cấp Chứng Nhận (Certified Skill):**  
> - Tổng điểm $\ge \mathbf{85/100}$  
> - **KHÔNG CÓ bất kỳ lỗi Hard Stop (FAIL)** nào tại các tầng L1, L2, L3, L4.
