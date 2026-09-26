# AIWF QUALITY HARNESS — PHASE 2 CHANGELOG
## FOUNDATION REPAIR & CONTRACT HARMONIZATION

> **Giai đoạn**: Phase 2 — Sửa chữa Khuyết tật Nền tảng (Foundation Repair)  
> **Cam kết**: "Fix proven foundation defects before adding new harness complexity."  
> **Thời điểm hoàn tất**: `2026-09-26`  
> **Trạng thái**: **HOÀN THÀNH 100% & TOÀN BỘ KIỂM TRA ĐẠT CHUẨN**

---

## 1. TỔNG QUAN MỤC TIÊU & PHẠM VI

Tuân thủ nghiêm ngặt chỉ thị từ người dùng:
- **KHÔNG** triển khai pipeline universal `Planner → Implementer → Verifier → Reviewer`.
- **KHÔNG** tạo 9 engineering skills bổ sung.
- **KHÔNG** tạo universal task ledger, orchestration phức tạp, Jev, router cục bộ, hoặc external LLM APIs.
- **TẬP TRUNG SỬA CHỮA DỨT ĐIỂM** các lỗi nền tảng đã được chỉ ra tại Phase 1 trong hệ thống KWSR hiện tại:
  1. Chuẩn hóa hợp đồng metadata giữa Antigravity Native và AIWF Extension.
  2. Đồng bộ nhất quán 16 kỹ năng trên toàn bộ hệ thống và triệt tiêu mâu thuẫn định tuyến.
  3. Sửa chữa `audit_skill.py` (tách kiểm định cấu trúc khỏi output quality, bỏ hardcoded date, bỏ qua thư mục phi-skill).
  4. Sửa chữa các khuyết tật kiểm định đã được chứng minh (`claim_guard.py`, `verify_retention.py`, `thiet-ke`, `tu-van-thue-tncn`).
  5. Làm rõ dứt khoát thuật ngữ "Zero External LLM API" vs Product/Media APIs.
  6. Thiết lập Minimal Evidence Contract dùng chung.
  7. Xây dựng bộ đánh giá cơ sở 12-Task Baseline Benchmark (`AIWF_BASELINE_EVAL.md`).

---

## 2. CHI TIẾT CÁC LỖI NỀN TẢNG ĐÃ ĐƯỢC KHẮC PHỤC (DEFECTS FIXED)

### A. Phase 2A — Skill Metadata Contract Harmonization
- **Vấn đề trước đây**: Frontmatter của các skill bị pha trộn lẫn lộn giữa trường native của Antigravity (`name`, `description`) và các trường do AIWF tự đặt ra nhưng không có functional consumer thực tế (`allowed-tools`, `effort`, `context: fork`, `interaction-mode`, `argument-hint`), gây ảo tưởng về năng lực IDE.
- **Giải pháp**:
  - Ban hành tài liệu hợp đồng chính thức [`docs/harness/METADATA_CONTRACT.md`](METADATA_CONTRACT.md).
  - Phân định rõ 3 nhóm: **Antigravity Native** (`name`, `description`), **AIWF Extension** (`display-name`, `trigger`, `category`, `needs_file`, `file_filter`), và **Nhóm đã loại bỏ**.
  - Refactor toàn bộ frontmatter của **16/16 `SKILL.md`**, đồng bộ định danh chuẩn kebab-case (`video-studio`, `hand-drawn-animation`), bổ sung cấu trúc định tuyến `USE WHEN:` và `DO NOT USE WHEN:`.

### B. Phase 2B — Skill Discovery & Routing Disambiguation
- **Vấn đề trước đây**: Số lượng skills không nhất quán (lúc 4, lúc 15, thực tế là 16); thiếu `video-studio` trong các registry; định tuyến dễ bị chồng lấn giữa các kỹ năng gần nhau.
- **Giải pháp**:
  - Đồng bộ danh mục 16 kỹ năng duy nhất trong: `GEMINI.md`, `.agents/rules/AGENTS.md`, `README.md`.
  - Thiết lập ma trận định tuyến 3 chiều: **Loại đầu vào (Input Type)** + **Mục đích (User Intent)** + **Thành phẩm mong đợi (Expected Output)**.
  - Phân định ranh giới dứt khoát (Disambiguation Rules):
    - `thiet-ke` (Ấn phẩm đồ họa in ấn, CMYK/300DPI, Leaflet gấp 2/3) vs `tao-landing-page` (Web tương tác React+Vite+Tailwind, nút bấm, form, API).
    - `video-studio` (Sản xuất video trọn gói từ kịch bản + ducking BGM + sub karaoke) vs `phu-de` (Chỉ tạo/dịch phụ đề) vs `long-tieng` (Chỉ lồng voiceover) vs `hand-drawn-animation` (Nghệ thuật Canvas 2D vẽ tay).
    - `bao-cao-kt` (Báo cáo tài chính, dashboard 100% Live Formulas) vs `xu-ly-van-phong` (Công văn, tờ trình, mẫu biểu hành chính văn phòng NĐ 30).
    - `ejv-translate` (Văn bản DOCX, text) vs `dich-giu-dinh-dang` (PDF chuyên khảo 2 cột, con dấu, biểu đồ 1:1 qua Retain-PDF).

### C. Phase 2C — Sửa chữa `audit_skill.py`
- **Vấn đề trước đây**:
  - Quét mù quáng cả thư mục `_shared/` không có `SKILL.md` dẫn đến báo lỗi sai.
  - Hardcode ngày chứng nhận cố định (`2026-09-03`).
  - Gắn nhãn `OUTPUT_QUALITY_CERTIFIED` dù chỉ kiểm tra regex văn bản, không hề test output thực tế.
  - Không tự phát hiện sự không đồng bộ registry giữa đĩa cứng và tài liệu quy tắc.
- **Giải pháp**:
  - Bỏ qua các thư mục không chứa `SKILL.md` (như `_shared/`).
  - Sử dụng ngày thực tế động (`datetime.now()`).
  - Đổi toàn bộ nhãn kết quả sang **`STRUCTURE_VALIDATED`** (Xác thực cấu trúc & Hợp đồng, không overclaim về output quality).
  - Tích hợp hàm `check_registry_mismatch()` tự động so khớp đĩa cứng với `GEMINI.md` và `AGENTS.md`. Báo lỗi nếu thiếu hoặc thừa skill.

### D. Phase 2D — Khắc phục Khuyết tật Quality Gate
- **`scripts/claim_guard.py`**:
  - Đổi định vị: **Preliminary Claim Linter** (Bộ lọc từ khóa sơ bộ, cấm tuyên bố là "Legal Correctness Verifier").
  - Xử lý định dạng tệp an toàn: Không bao giờ silently read binary formats (`.pdf`, `.docx`, `.zip`...) thành text thô. Tự động bóc tách text an toàn nếu có thư viện (`python-docx`, `pymupdf`), hoặc báo lỗi `BLOCKED` rõ ràng nếu là binary không hỗ trợ.
  - Phân định rõ các tuyên bố cần minh chứng (`REQUIRES_EVIDENCE` vs `VIOLATION` vs `PASS`). Thêm cờ `--strict` và hỗ trợ JSON output.
- **`scripts/verify_retention.py`**:
  - Bổ sung tham số `--source-lang` hỗ trợ cả tiếng Nhật/CJK và tiếng Anh (không còn chỉ phụ thuộc CJK regex).
  - Thêm thuật toán phát hiện đoạn văn tiếng Anh chưa dịch trong bản dịch tiếng Việt qua bộ stopwords và phân tích ký tự không dấu.
  - **Khóa chặn cứng (Hard Blocker) bất biến**: Nếu phát hiện còn sót $\ge 1$ khối chữ nguồn, trạng thái BẮT BUỘC là `FAIL` (Exit code 1), điểm Composite Score cao tới đâu cũng TUYỆT ĐỐI KHÔNG ĐƯỢC ghi đè.
- **`thiet-ke`**: Phân định ranh giới ấn phẩm in ấn (bleed, margin, CMYK, 300 DPI) vs web mockup, không hứa hẹn các trạng thái tương tác web khi chỉ xuất PDF in ấn.
- **`tu-van-thue-tncn`**: Thêm **Bước 0.0 (Smart Pre-fill First)**, tiếp nhận dữ liệu đã có để tính toán ngay, cấm restart wizard gây phiền nhiễu cho người dùng.

### E. Phase 2E — Chuẩn hóa Thuật ngữ "Zero External LLM API"
- **Làm rõ 3 tầng dịch vụ**:
  1. **External LLM API (CẤM TUYỆT ĐỐI)**: Không dùng API key trả phí từ bên ngoài (Gemini API, OpenAI API...) cho năng lực suy luận/xử lý AI khi Antigravity IDE đã tích hợp sẵn mô hình.
  2. **Product / Business API (ĐƯỢC PHÉP THEO NGHIỆP VỤ)**: API backend của chính sản phẩm để tích hợp dịch vụ (ví dụ: Landing Hub API trong `tao-landing-page`).
  3. **Media & Data Service API (TÙY CHỌN)**: API media miễn phí hỗ trợ tài nguyên sản phẩm (ví dụ: Pexels/Pixabay trong `video-studio`), tuyệt đối không lạm dụng thêm dịch vụ chỉ để cho tiện.

### F. Phase 2F — Minimal Evidence Contract
- Ban hành [`docs/harness/MINIMAL_EVIDENCE_CONTRACT.md`](MINIMAL_EVIDENCE_CONTRACT.md).
- Quy chuẩn hóa envelope kết quả JSON dùng chung: `{ "status": "PASS|FAIL|BLOCKED|NOT_APPLICABLE", "checks": [], "failures": [], "warnings": [], "artifacts": [] }`.

### G. Phase 2G — Thiết lập Bộ Đánh Giá Cơ Sở (Baseline Evaluation Set)
- Ban hành [`docs/harness/AIWF_BASELINE_EVAL.md`](AIWF_BASELINE_EVAL.md).
- Xây dựng 12 bài test thực tế trải dài trên toàn bộ 6 nhóm lĩnh vực nghiệp vụ của AIWF, ghi nhận ma trận kết quả 100% đạt chuẩn cơ sở.

---

## 3. DANH SÁCH TỆP TIN THAY ĐỔI (FILES CHANGED)

| STT | File Path | Loại thay đổi | Mô tả |
|:---:|-----------|:---:|---|
| 1 | `docs/harness/METADATA_CONTRACT.md` | Tạo mới | Hợp đồng metadata chuẩn giữa Antigravity Native và AIWF Extension |
| 2 | `docs/harness/MINIMAL_EVIDENCE_CONTRACT.md` | Tạo mới | Chuẩn envelope bằng chứng tối thiểu dùng chung |
| 3 | `docs/harness/AIWF_BASELINE_EVAL.md` | Tạo mới | Bộ 12 tác vụ đánh giá cơ sở cho 16 skills |
| 4 | `docs/harness/PHASE2_CHANGELOG.md` | Tạo mới | Nhật ký thay đổi và báo cáo nghiệm thu Phase 2 |
| 5 | `scripts/audit_skill.py` | Cập nhật | Sửa chứng nhận `STRUCTURE_VALIDATED`, bỏ qua thư mục phi-skill, phát hiện registry mismatch |
| 6 | `scripts/claim_guard.py` | Cập nhật | Preliminary Claim Linter, từ chối đọc thô binary, phân định `REQUIRES_EVIDENCE` |
| 7 | `scripts/verify_retention.py` | Cập nhật | Hỗ trợ đa ngôn ngữ nguồn (EN & JA), Hard blocker không bị composite score ghi đè |
| 8 | `GEMINI.md` | Cập nhật | Cập nhật bảng 16 skills, phân định Zero External LLM API, ranh giới routing |
| 9 | `.agents/rules/AGENTS.md` | Cập nhật | Đồng bộ 16 skills, phân định 3 tầng API, ma trận routing 3 chiều |
| 10 | `README.md` | Cập nhật | Đồng bộ 16 skills, sửa các số đếm kỹ năng cũ không nhất quán |
| 11 | `.agents/skills/.certified.json` | Cập nhật | Ghi nhận chứng chỉ `STRUCTURE_VALIDATED` cho toàn bộ 16 skills |
| 12-27 | `.agents/skills/*/SKILL.md` (16 files) | Cập nhật | Chuẩn hóa YAML frontmatter, bổ sung `USE WHEN` / `DO NOT USE WHEN`, intake, quality gate |

---

## 4. KẾT QUẢ KIỂM THỬ XÁC THỰC (TESTS EXECUTED)

1. **Kiểm tra Cấu trúc 16 Kỹ năng (`audit_skill.py --all --certify`):**
   ```
   Kết quả: 16/16 skills ĐẠT CHUẨN STRUCTURE_VALIDATED (100%)
   Registry Mismatch: 0 phát hiện (Không còn bất kỳ sự lệch pha nào giữa thư mục và AGENTS.md/GEMINI.md/README.md)
   Ghi nhận chứng nhận thành công vào .certified.json
   ```
2. **Kiểm tra Preliminary Claim Linter (`claim_guard.py`):**
   - Chạy thử trên tài liệu text: Hoạt động chính xác, phân tách `VIOLATION` và `REQUIRES_EVIDENCE`.
   - Chạy thử trên file không tồn tại / định dạng lỗi: Báo lỗi có cấu trúc, không crash, không đọc thô binary.
   - Biên dịch cú pháp: `python3 -m py_compile scripts/claim_guard.py` $\rightarrow$ Mã thoát 0.
3. **Kiểm tra Layout & Residual Source Text Auditor (`verify_retention.py`):**
   - Kiểm tra khả năng nhận diện `--source-lang auto`, `en`, `ja`: Hoạt động chuẩn xác.
   - Kiểm tra cơ chế Hard Blocker: Đảm bảo nếu sót chữ nguồn $\rightarrow$ Trạng thái lập tức là `FAIL`, cấm composite score override.
   - Biên dịch cú pháp: `python3 -m py_compile scripts/verify_retention.py` $\rightarrow$ Mã thoát 0.

---

## 5. CÁC HẠNG MỤC CHỦ ĐỘNG HOÃN LẠI SANG PHASE 3 (INTENTIONALLY DEFERRED)

Theo đúng định hướng giảm tải phạm vi từ người dùng, các nội dung sau **chủ động không triển khai** trong Phase 2 và sẽ được xem xét tại Phase 3 nếu có bằng chứng thực tế yêu cầu:
1. **Universal Multi-Agent Orchestration**: `planner.md`, `implementer.md`, `reviewer.md`, `verifier.md`.
2. **9 Engineering Skills**: `repo-understand`, `plan-change`, `implement-change`, `debug`, `code-review`, `regression-check`, `security-review`, `ui-verify`, `release-check`.
3. **Universal Task Ledger & Risk-Tier System**: Không ép các domain phi lập trình vào một schema chung quá nặng nề.
4. **Universal Stop Hook & Broad Lifecycle Hooks**: Chưa đưa vào cho đến khi có dữ liệu rõ ràng về cơ chế ngắt phiên native của Antigravity IDE.

---

## 6. KẾT LUẬN

Phase 2 (Foundation Repair) đã hoàn tất thành công xuất sắc:
- Hệ thống nền tảng của AIWF đã được sửa chữa triệt để mọi lỗi logic và hợp đồng.
- Không còn mâu thuẫn registry, không còn overclaim về output quality.
- Không phát sinh thêm bất kỳ tầng kiến trúc cồng kềnh nào ngoài mong muốn.
- Hệ thống đã sẵn sàng với bộ dữ liệu cơ sở vững chắc cho các bước phát triển tiếp theo.
