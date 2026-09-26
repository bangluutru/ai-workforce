# AIWF HARNESS AUDIT & TARGET ARCHITECTURE BLUEPRINT
## Báo Cáo Kiểm Định Hiện Trạng & Đề Xuất Kiến Trúc Harness Kỹ Thuật AIWF Cho Google Antigravity

> **Tài liệu:** `docs/harness/AIWF_HARNESS_AUDIT.md`  
> **Phiên bản:** 1.0.0 (Giai đoạn Audit & Kiến trúc nền tảng)  
> **Ngày lập:** 2026-09-26  
> **Trạng thái:** PHASE 1 — Audit Hoàn tất (Chờ phê duyệt trước khi chuyển sang Phase 2)  
> **Nguyên tắc phương pháp:** Zero-Inference Taxonomy (OBSERVED / DERIVED / PRIOR / ASSUMED) — Codebase-First

---

## MỤC LỤC

1. [Tổng Quan Sứ Mệnh & Nguyên Lý Cốt Lõi](#1-tổng-quan-sứ-mệnh--nguyên-lý-cốt-lõi)
2. [Hiện Trạng Kiến Trúc Repository (OBSERVED)](#2-hiện-trạng-kiến-trúc-repository-observed)
3. [Năng Lực Harness Hiện Có (Existing Harness Capabilities)](#3-năng-lực-harness-hiện-có-existing-harness-capabilities)
4. [Các Năng Lực Còn Thiếu (Missing Capabilities)](#4-các-năng-lực-còn-thiếu-missing-capabilities)
5. [Sự Trùng Lặp & Phân Mảnh Chức Năng (Duplicated Capabilities)](#5-sự-trùng-lặp--phân-mảnh-chức-năng-duplicated-capabilities)
6. [Đánh Giá Rủi Ro Hệ Thống (Risks Analysis)](#6-đánh-giá-rủi-ro-hệ-thống-risks-analysis)
7. [Phân Định Thành Phần: Giữ Nguyên — Cải Tiến — Loại Bỏ / Tinh Gọn](#7-phân-định-thành-phần)
8. [Kiến Trúc Đích Đề Xuất (Target Architecture Blueprint)](#8-kiến-trúc-đích-đề-xuất-target-architecture-blueprint)
9. [Lộ Trình Triển Khai Từng Bước (Phased Implementation Plan)](#9-lộ-trình-triển-khai-từng-bước-phased-implementation-plan)
10. [Các Vấn Đề Cần Phê Duyệt & Điểm Dừng Kỹ Thuật (Checkpoints)](#10-các-vấn-đề-cần-phê-duyệt--điểm-dừng-kỹ-thuật)

---

## 1. TỔNG QUAN SỨ MỆNH & NGUYÊN LÝ CỐT LÕI

### 1.1. Sứ mệnh
Nâng cấp **AIWF (AI Workforce)** từ một bộ kỹ năng tự động hóa nghiệp vụ (Domain Skills Catalog) thành một **Harness Kỹ thuật Phần mềm Độc lập Mô hình (Model-Independent Engineering Harness)** chạy native trên nền tảng **Google Antigravity**.

Mục tiêu **KHÔNG PHẢI** là:
* ❌ Không thay thế Antigravity native harness.
* ❌ Không xây dựng thêm một coding agent độc lập hay một wrapper cồng kềnh.
* ❌ Không xây dựng hệ thống quản lý bộ nhớ hoặc LLM router phức tạp khi chưa có nhu cầu chứng minh.

Mục tiêu **CHÍNH XÁC LÀ**:
* ✅ Bổ sung một **TẦNG CHẤT LƯỢNG & KIỂM SOÁT (Thin, Rigorous Quality & Control Layer)** mỏng nhưng nghiêm ngặt.
* ✅ Đảm bảo mọi mô hình (Gemini 3.8 Flash/Pro, Claude 3.7/Sonnet/Opus, hay các mô hình tương lai) đều tuân thủ cùng một quy trình kỹ thuật chuẩn xác.
* ✅ Chuyển đổi cơ chế đánh giá: **Mô hình được đánh giá bằng BẰNG CHỨNG XÁC THỰC (Verifiable Evidence) thay vì lời tự nhận (Self-claims).**

### 1.2. Nguyên lý số 1 (First Principle)
> **Model Intelligence và Harness Quality là hai thực thể độc lập.**
> Mô hình AI tuyệt đối không bao giờ được tin cậy chỉ vì nó tuyên bố:
> * *"Đã làm xong"* (`done`)
> * *"Đã sửa lỗi"* (`fixed`)
> * *"Mã trông có vẻ đúng"* (`looks correct`)
> * *"Các bài kiểm thử sẽ pass"* (`tests should pass`)
> * *"Thay đổi này không làm hỏng cái gì đâu"* (`this shouldn't break anything`)
>
> **Mọi trạng thái hoàn thành PHẢI được chứng minh bằng bằng chứng tất định.**

### 1.3. Vòng lặp kỹ thuật chuẩn (The Desired Engineering Loop)
```
UNDERSTAND (Hiểu rõ yêu cầu & hiện trạng)
      ↓
PLAN (Lập kế hoạch thay đổi, blast radius, acceptance criteria)
      ↓
IMPLEMENT (Thực thi đúng phạm vi, không tự phong hoàn thành)
      ↓
DETERMINISTIC VERIFY (Chạy test, build, lint, typecheck, claim guard)
      ↓
INDEPENDENT REVIEW (Soát xét diff độc lập, phát hiện regression & scope creep)
      ↓
REGRESSION CHECK (Bảo đảm tính toàn vẹn hệ thống cũ)
      ↓
FIX IF NECESSARY (Khắc phục khiếm khuyết nếu có)
      ↓
FINAL VERIFY (Tái thẩm định bằng chứng)
      ↓
DONE (Đóng gói với Evidence JSON đầy đủ)
```

---

## 2. HIỆN TRẠNG KIẾN TRÚC REPOSITORY (OBSERVED)

Khảo sát trực tiếp từ mã nguồn và cấu trúc tệp thực tế tại commit `5fcf6b7` (nhánh `main`):

### 2.1. Cấu trúc thư mục mức cao (Workspace Root)
* `GEMINI.md`: 11.4 KB. File quy tắc root, nạp tự động bởi IDE. Chứa hướng dẫn vận hành, trigger registry của 15 skills, bảng đường dẫn, troubleshooting.
* `README.md`: 18.8 KB. Tài liệu giới thiệu tổng quan, kiến trúc KWSR, hướng dẫn cài đặt.
* `CHANGELOG.md`: 13.8 KB. Lịch sử các phiên bản từ v1.0.0 đến v2.2.0.
* `manifest.json`: 335 B. Metadata dự án (version 1.0.0, extension_version 2.0.0, KWSR).
* `package.json` & `package-lock.json`: Cấu hình npm cơ bản cho công cụ VSIX.
* `requirements.txt`: 497 B. Khai báo dependencies Python (`pymupdf`, `python-docx`, `pdfplumber`, `lxml`, `markitdown`, `pypandoc`, `notebooklm-py`).
* `.vscode/`:
  * `settings.json`: Thiết lập cấu hình IDE cơ bản.
  * `tasks.json`: Tác vụ tự động chạy `auto-setup.sh` khi mở thư mục (`runOn: folderOpen`).
* `dashboard/`: Giao diện trực quan tĩnh (HTML, CSS, JS) hiển thị 16 kỹ năng và catalog tri thức NotebookLM.
* `extension/`: VS Code / Antigravity IDE Extension (`ai-workforce-panel-3.6.0.vsix`) tạo panel sidebar tương tác.
* `docs/`: Chứa `AIWF_USER_HANDBOOK.md` (Sổ tay vận hành v2.0 cho 16 skills). Chưa có thư mục `docs/harness/`.
* `scripts/`: Chứa 13 scripts tiện ích và 2 thư mục con (`harness/`, `hooks/`).
* `.agents/`: Trọng tâm cấu trúc KWSR của AIWF:
  * `.agents/rules/`: 8 tệp markdown quy tắc (`AGENTS.md`, `R0` đến `R6`, kèm thư mục con `specs/`).
  * `.agents/skills/`: 16 thư mục domain skills, 1 thư mục `_shared/` (chứa `output_manager.py`), và `.certified.json`.
  * `.agents/workflows/`: 2 quy trình công việc (`W0-so-tay-aiwf.md`, `W1-chuan-bi-tuyen-dung.md`).
  * `.agents/knowledge/`: Kho tri thức SSOT (artifacts chính sách, sản phẩm, pháp lý, `CATALOG.md`, `catalog.json`).

### 2.2. Chi tiết hệ thống quy tắc (`.agents/rules/`)
1. `AGENTS.md` (11.5 KB): Bản đồ tổ chức tổng. Khung KWSR, nguyên tắc Zero-Hallucination, Zero External API, Autonomous Full-Run, Skill Registry, Luật R4/R5/R6.
2. `R0-git-sync-mandatory.md` (3.4 KB): Luật tối cao — Mọi thay đổi phải đồng bộ được 100% qua Git, cấm phụ thuộc tài nguyên máy cục bộ.
3. `R1-zero-destruction.md` (2.5 KB): Bảo toàn lịch sử qua Git-native, cấm tạo thư mục rác (`_Delete/`, `_Archive/`), cấm ghi file xuất bản vào repo root.
4. `R2-code-quality.md` (2.9 KB): Zero-Inference Taxonomy (OBSERVED/DERIVED/PRIOR/ASSUMED), Codebase-first execution, Token Economics, 5 Điều cấm tuyệt đối (cấm placeholder, cấm nuốt lỗi, cấm sửa file chưa đọc, cấm bịa API, cấm hardcode credentials).
5. `R3-operational-discipline.md` (6.3 KB): Per-Task Verification, Autonomous Full-Run, chống suy thoái ngữ cảnh (Quy tắc 15 tin nhắn), quy trình 3 pha Explore → Plan → Execute, Subagent isolation (`context: fork`), Zero-Residual Source Text Quality Gate.
6. `R4-skill-standard-v1.md` (18.2 KB): Chuẩn kiến trúc 5 lớp Gemini 3.8, Router YAML frontmatter, Live Formulas, Confidence Flagging, quy chuẩn đặt tên, kiểm định qua `scripts/audit_skill.py`.
7. `R5-legal-claim-compliance.md` (7.2 KB): Thẩm định tính pháp lý nội dung, chống over-claim tiếp thị (Luật Quảng cáo 2012, NĐ 181, NĐ 38, TT 06/2011/TT-BYT), kiểm duyệt tự động qua `scripts/claim_guard.py`.
8. `R6-document-layout-preservation.md` (14.2 KB): Tiêu chuẩn 7 trụ cột Retain-PDF (SMask Alpha, Subplot bounding, Ornate Safe Zone, Multi-column balance, Dual-Level mapping, Domain Review, Tri-Layer Quality Gate).
9. `specs/interactive-skill-pattern.md` (8.7 KB): Đặc tả mô hình tương tác 2 chiều ISP v1.0.

### 2.3. Danh mục 16 Domain Skills hiện có
Hệ thống hiện sở hữu 16 skills phục vụ tự động hóa văn phòng, dịch thuật, pháp lý và đồ họa:
1. `app-auditor`: Kiểm định ứng dụng web (Playwright, visual sweep 4 viewports, axe-core a11y).
2. `bao-cao-kt`: Lập báo cáo tài chính/kế toán/quản trị, xuất Excel formulas sống.
3. `boc-tach-pdf`: OCR và bóc tách tài liệu PDF scan thành Word chuẩn NĐ 30.
4. `chotto-newsroom`: Biên tập tin tức Chotto Nhật Bản.
5. `dich-giu-dinh-dang`: Retain-PDF, dịch giữ nguyên bố cục hình học và hình ảnh.
6. `ejv-translate`: Dịch thuật 3 ngôn ngữ (Việt - Anh - Nhật) chuẩn y tế/pháp lý.
7. `hand-drawn-animation`: Tạo hoạt hình vẽ tay Canvas 2D (5 phong cách, pop-up 3D).
8. `long-tieng`: Lồng tiếng video (TTS Kokoro-82M offline).
9. `phu-de`: Tạo phụ đề video song ngữ, auto subtitle, hardsub ASS/SRT.
10. `tao-landing-page`: Chuyển đổi bản thiết kế Figma/Stitch thành Landing Page chuẩn responsive.
11. `thiet-ke`: Thiết kế đồ họa văn phòng, brochure, leaflet, xuất bản in ấn.
12. `tu-van-phap-luat`: Tra cứu và tư vấn pháp luật Việt Nam dựa trên SSOT.
13. `tu-van-thue-tncn`: Quyết toán và tư vấn thuế thu nhập cá nhân, eTax Mobile.
14. `video-studio`: Studio biên tập video tự động từ ý tưởng, kho stock Pexels/Pixabay, auto beat sync.
15. `viet-bai`: Sáng tạo nội dung tiếp thị, blog SEO, bài PR chuẩn Luật R5.
16. `xu-ly-van-phong`: Soạn thảo và chỉnh lý văn bản Word/Excel/PPT/PDF chuẩn thể thức NĐ 30/2020/NĐ-CP.

---

## 3. NĂNG LỰC HARNESS HIỆN CÓ (EXISTING HARNESS CAPABILITIES)

Mặc dù AIWF chưa có một harness kỹ thuật phần mềm hoàn chỉnh, repo đã có sẵn nhiều nền móng chất lượng cao (OBSERVED):

| Thành phần hiện có | Đường dẫn file | Năng lực cụ thể | Đánh giá giá trị tái sử dụng |
|---|---|---|---|
| **Evidence Verifier** | `scripts/harness/evidence_verifier.py` | Kiểm chứng trích dẫn nguyên văn (verbatim quotes) với văn bản gốc. Trả về JSON: `passes`, `confidence_score`, `verified_count`, `missing_count`. 100% Python Standard Library. | **Rất cao**: Đây chính là hạt nhân của nguyên tắc "Evidence-based Completion" cho văn bản và trích dẫn. |
| **Claim Guard Linter** | `scripts/claim_guard.py` | Quét chống over-claim pháp lý (Luật Quảng cáo, NĐ 181, NĐ 38, TT 06). Kiểm tra bằng regex, trả về vi phạm và gợi ý sửa. | **Cao**: Tái sử dụng làm một deterministic gate trong vòng lặp CI/Verification. |
| **Skill Architecture Auditor** | `scripts/audit_skill.py` | Kiểm tra 5 lớp kiến trúc của skill: L1 (Frontmatter), L2 (Discipline), L3 (Zero API), L4 (Syntax py_compile), L5 (Quality gate). Tính hash SHA-256 cấp chứng chỉ `.certified.json`. | **Rất cao**: Cần tích hợp vào pre-commit/pre-merge hook để tự động hóa kiểm định kỹ năng. |
| **PDF Retention Auditor** | `scripts/verify_retention.py` | Đối chiếu 1:1 tài liệu gốc và dịch: số trang, kích thước, ảnh/con dấu, bảng biểu, công thức hóa/toán, phát hiện chữ nguồn sót. | **Cao**: Deterministic checker chuyên biệt cho document layout fidelity. |
| **Interactive State Bridge** | `scripts/harness/interactive_bridge.py` | Quản lý state `project.json`, snapshot revision (undo/redo), local HTTP streaming server cho webview. | **Trung bình**: Dành cho Interactive Skill Pattern (ISP), giữ nguyên cho UI review. |
| **Output Path Manager** | `.agents/skills/_shared/output_manager.py` | Quản lý thư mục xuất bản: 3 tầng ưu tiên (`user_path` $\rightarrow$ `AIWF_OUTPUT_DIR` $\rightarrow$ `~/Downloads/AIWF_Output/`), bảo vệ codebase không bị phình to. | **Rất cao**: Là chuẩn quản lý output cho toàn bộ các công cụ xuất bản. |
| **App Auditor** | `.agents/skills/app-auditor/SKILL.md` | Kiểm thử web app tự động qua Playwright (Chromium headless), quét 4 viewports, console error/network failure, WCAG a11y via axe-core. | **Rất cao**: Là nền móng hoàn hảo cho **UI Verification** (Phase 5). |
| **Git Post-Merge Hook** | `scripts/hooks/post-merge`, `scripts/install-hooks.sh` | Tự động chạy `auto-setup.sh --quiet` sau mỗi lệnh `git pull` để cài đặt môi trường. | **Trung bình**: Cơ chế Git hook truyền thống, cần bổ sung Antigravity Lifecycle Hooks (`hooks.json`). |
| **Hệ thống Luật R0-R6** | `.agents/rules/` | Đã thiết lập các nguyên tắc Zero-Inference, Codebase-first, 5 Điều cấm tuyệt đối, 3-Pha (Explore-Plan-Execute), Subagent isolation. | **Rất cao**: Đây là bộ quy chuẩn ứng xử sẵn sàng cho việc phân tách các vai trò (Roles). |

---

## 4. CÁC NĂNG LỰC CÒN THIẾU (MISSING CAPABILITIES)

Đối chiếu với các yêu cầu của **Production-Grade Engineering Harness**, AIWF hiện còn thiếu các năng lực then chốt sau:

### 4.1. Thiếu Antigravity Native Lifecycle Hooks (`.agents/hooks.json`)
* **Hiện trạng**: Repo chỉ có Git hooks truyền thống (`scripts/hooks/post-merge`). Antigravity IDE hoàn toàn hỗ trợ native `hooks.json` tại root customization (`.agents/hooks.json`) với các sự kiện: `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`.
* **Hậu quả**:
  * Chưa có chốt chặn ngăn agent đọc/sửa các file nhạy cảm (`.env`, secrets, `.git/`) ở tầng công cụ (`PreToolUse` deny).
  * Chưa có cơ chế ngăn model tự ý dừng (`Stop` hook) khi chưa chạy các bước kiểm thử bắt buộc.
  * Chưa có cơ chế tự động format code hoặc syntax check nhanh ngay sau khi chỉnh sửa (`PostToolUse`).

### 4.2. Thiếu Phân Tách 4 Vai Trò Kỹ Thuật (Separation of Duties)
* **Hiện trạng**: Toàn bộ tương tác hiện tại do một tác nhân đơn lẻ (Single Monolithic Agent) đảm nhiệm. Agent vừa là người lập kế hoạch, vừa là người viết code, vừa tự chạy test, và tự tuyên bố "đã hoàn thành".
* **Hậu quả**: Vi phạm First Principle. Model thường rơi vào bẫy "Confirmation Bias" (tự tin thái quá vào code mình vừa viết), bỏ qua việc kiểm tra tác động phụ hoặc không chạy kiểm thử độc lập.
* **Cần bổ sung**: 4 vai trò cấu trúc rõ ràng:
  1. `PLANNER`: Khảo sát, phân tích dependency, blast radius, lập plan & acceptance criteria. Không được tự ý sửa file lớn.
  2. `IMPLEMENTER`: Chỉ thực thi trong phạm vi plan đã duyệt, tuân thủ rules. Không được tự tuyên bố "production-ready".
  3. `REVIEWER`: Soát xét diff độc lập (read-only), tìm lỗi logic, regression, scope creep, bảo mật.
  4. `VERIFIER`: Chạy deterministic checks (test, lint, typecheck, build, browser sweep), trả về structured JSON evidence.

### 4.3. Thiếu Bộ Kỹ Năng Kỹ Thuật Phần Mềm Cốt Lõi (Core Engineering Skills)
* **Hiện trạng**: Toàn bộ 16 skills hiện tại là **Domain/Business Skills** (kế toán, dịch thuật, video, hoạt hình, pháp lý...). AIWF chưa có bất kỳ skill chuyên dụng nào cho chu trình phát triển phần mềm (Software Engineering Lifecycle).
* **Cần bổ sung (Minimal Core Set)**:
  * `repo-understand`: Khảo sát kiến trúc, cấu trúc module, luồng dữ liệu, mapping dependency mà không làm thay đổi mã nguồn.
  * `plan-change`: Lập kế hoạch thay đổi mã nguồn, tính toán blast radius, phân loại Risk Tier (0-3), lập tiêu chí nghiệm thu.
  * `implement-change`: Thực thi phẫu thuật (surgical micro-diffs), bám sát plan, chống scope creep.
  * `debug`: Sửa lỗi theo phương pháp Root Cause Analysis, tái hiện lỗi trước khi sửa, cấm sửa mò.
  * `code-review`: Soát xét diff độc lập, đối chiếu với Rule R2 và blast radius.
  * `regression-check`: Chạy kiểm tra hồi quy toàn diện trước khi bàn giao.
  * `security-review`: Rà soát lỗ hổng bảo mật, secret leakage, injection, permissions.
  * `ui-verify`: Khởi động app, dùng browser inspect giao diện, console errors, responsive layout.
  * `release-check`: Thẩm định trạng thái repo sạch, tài liệu đầy đủ, pass 100% quality gates trước khi merge/commit.

### 4.4. Thiếu Schema Bằng Chứng Xác Thực Chuẩn Hóa (Verification Schema)
* **Hiện trạng**: Mỗi công cụ kiểm tra hiện tại trả về một định dạng riêng (`evidence_verifier.py` trả về confidence score, `claim_guard.py` in terminal, `audit_skill.py` lưu `.certified.json`). Chưa có một cấu trúc dữ liệu chuẩn mực để tích hợp tất cả thành một báo cáo nghiệm thu duy nhất.
* **Cần bổ sung**: Canonical Verification Result Schema:
  ```json
  {
    "status": "PASS | FAIL | BLOCKED",
    "risk_tier": "TIER_0 | TIER_1 | TIER_2 | TIER_3",
    "checks": [],
    "tests_run": [],
    "failures": [],
    "warnings": [],
    "changed_files": [],
    "acceptance_criteria": [],
    "remaining_risks": []
  }
  ```

### 4.5. Thiếu Cơ Chế Phân Loại Rủi Ro Theo Bậc (Risk-based Workflow Tiers)
* **Hiện trạng**: Mọi yêu cầu đang được xử lý với cùng một mức độ tải ngữ cảnh và quy trình.
* **Cần bổ sung**: Phân loại 4 cấp độ rủi ro (Tier 0 đến Tier 3):
  * **Tier 0 (Docs/Trivial)**: Thay đổi tài liệu, sửa comment $\rightarrow$ Implement $\rightarrow$ Verify.
  * **Tier 1 (Small isolated)**: Sửa 1 hàm, 1 file độc lập $\rightarrow$ Plan $\rightarrow$ Implement $\rightarrow$ Verify.
  * **Tier 2 (Multi-file feature / Refactor)**: Thay đổi nhiều file, sửa core $\rightarrow$ Plan $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Independent Review.
  * **Tier 3 (Security / Auth / Migration / Destructive)**: Động đến credentials, database, deployment $\rightarrow$ Plan $\rightarrow$ Risk Analysis $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Independent Review $\rightarrow$ Human Approval.

### 4.6. Thiếu Task Ledger (Sổ Theo Dõi Tiến Trình Nhẹ)
* **Hiện trạng**: Khi thực hiện các tác vụ dài (nhiều tệp tin, nhiều bước kiểm tra), agent dễ bị "quên" yêu cầu con ban đầu hoặc tự ý tuyên bố xong khi mới hoàn thành một phần việc (Context Rot / Step Drop).
* **Cần bổ sung**: Sổ theo dõi tiến trình gọn nhẹ (`.agents/task_ledger.json` hoặc trong `_process/ledger.json`) lưu vết: objective, scope, acceptance criteria checklist, current status, failures/risks.

### 4.7. Thiếu Đo Lường & Quan Sát Nhẹ (Lightweight Observability)
* **Hiện trạng**: Chưa có bảng ghi nhật ký đo lường về hiệu năng thực thi: tác vụ nào thường thất bại, số lần retry, công cụ nào bị lỗi, model nào hoạt động ổn định nhất.

---

## 5. SỰ TRÙNG LẶP & PHÂN MẢNH CHỨC NĂNG (DUPLICATED CAPABILITIES)

Khảo sát phát hiện một số điểm chồng chéo cần được tinh giản:

### 5.1. Trùng lặp giữa `GEMINI.md` (root) và `.agents/rules/AGENTS.md`
* **Vấn đề**: Cả 2 file này đều đang chứa:
  * Toàn bộ bảng Skill Registry 15 kỹ năng (đã lỗi thời vì hiện có 16 kỹ năng).
  * Lệnh cài đặt Python dependencies.
  * Troubleshooting guide.
* **Hậu quả**: Khi mở workspace, Antigravity nạp cả 2 file vào context window, gây lãng phí từ 5.000 đến 8.000 tokens quý giá ngay tại turn đầu tiên, vi phạm Design Principle 2 (Minimal Context) và Rule R2 (Token Economics).
* **Đề xuất**:
  * Giữ `GEMINI.md` cực kỳ tinh gọn: Chỉ chứa định danh dự án, invariants bất di bất dịch, chỉ dẫn nạp rules.
  * Đặt `AGENTS.md` tại workspace root hoặc chuẩn hóa trong `.agents/rules/` theo đúng cơ chế Antigravity native. Chuyển chi tiết cài đặt môi trường vào `skills/` hoặc `scripts/`.

### 5.2. Sự trùng lặp giữa các scripts kiểm tra rời rạc
* `scripts/verify_retention.py` và `scripts/verify_layout_parity.py`: Cả hai đều kiểm tra độ tương đồng bố cục PDF, có nhiều đoạn mã regex và đo lường khoảng cách bị lặp lại.
* Cần tích hợp các công cụ này vào một interface CLI thống nhất dưới `scripts/harness/verify.py` thay vì để các file script tản mát.

### 5.3. Bảng Registry kỹ năng thủ công bị phân mảnh ở 4 nơi
* `GEMINI.md` (15 skills)
* `.agents/rules/AGENTS.md` (15 skills)
* `docs/AIWF_USER_HANDBOOK.md` (16 skills - đã cập nhật)
* `dashboard/data.json` & `extension/` (16 skills)
* Cần một cơ chế Single Source of Truth tự động sinh từ metadata YAML frontmatter của các skills (`scripts/scan_catalog.py` hoặc CLI build).

---

## 6. ĐÁNH GIÁ RỦI RO HỆ THỐNG (RISKS ANALYSIS)

Khi nâng cấp AIWF thành Engineering Harness, có 4 rủi ro kỹ thuật chính cần quản trị:

| Rủi ro | Mức độ | Nguyên nhân tiềm ẩn | Biện pháp giảm thiểu |
|---|---|---|---|
| **1. Harness Bloat & Over-engineering** | **CAO** | Xây dựng quá nhiều tầng trung gian, bắt chước các framework nặng nề (như LangChain hay AutoGen), tạo quá nhiều tệp cấu hình thừa. | **Nguyên tắc "Native-First"**: Chỉ dùng Antigravity native primitives (`hooks.json`, `.agents/rules/`, `.agents/skills/`). Giữ harness là một thin control layer. |
| **2. False Security from Self-Verification** | **CAO** | Model tự viết test, tự chạy test của chính mình, và tự xác nhận là "PASS" (Confirmation Bias). | **Separation of Duties**: Tách biệt Implementer và Reviewer/Verifier. Chạy deterministic check từ script độc lập không do LLM kiểm soát. |
| **3. Context Window Saturation (Context Rot)** | **TRUNG BÌNH** | Tải quá nhiều tài liệu hướng dẫn, bảng biểu, log test vào prompt khiến mô hình bị suy thoái khả năng nhận thức. | **Progressive Context Loading**: Chỉ load tên và description của skill. Chi tiết chỉ nạp khi kích hoạt. Áp dụng quy tắc 15 tin nhắn và subagent isolation. |
| **4. Phá vỡ tính tương thích ngược với 16 Domain Skills** | **TRUNG BÌNH** | Việc thay đổi cấu trúc rules hoặc harness làm hỏng hoạt động của các skill nghiệp vụ hiện có (`ejv-translate`, `bao-cao-kt`...). | Giữ nguyên vẹn 100% thư mục `.agents/skills/` của 16 domain skills. Harness kỹ thuật hoạt động bổ trợ như một tầng kiểm soát (Governance Layer) bên ngoài. |

---

## 7. PHÂN ĐỊNH THÀNH PHẦN

Căn cứ vào nguyên tắc: *"Prefer deletion and consolidation over accumulation"*, các thành phần được phân định như sau:

### 7.1. Thành phần GIỮ NGUYÊN (Keep Unchanged)
1. **Toàn bộ 16 Domain Skills** trong `.agents/skills/`:
   * `app-auditor`, `bao-cao-kt`, `boc-tach-pdf`, `chotto-newsroom`, `dich-giu-dinh-dang`, `ejv-translate`, `hand-drawn-animation`, `long-tieng`, `phu-de`, `tao-landing-page`, `thiet-ke`, `tu-van-phap-luat`, `tu-van-thue-tncn`, `video-studio`, `viet-bai`, `xu-ly-van-phong`.
   * Lý do: Đã được kiểm định hoạt động tốt, phục vụ nhu cầu nghiệp vụ thực tế, không can thiệp trừ khi cần sửa lỗi nghiệp vụ.
2. **Kho tri thức SSOT** (`.agents/knowledge/`):
   * Các tệp chính sách, tiêu chuẩn, sản phẩm mẫu.
3. **Module quản lý output** (`.agents/skills/_shared/output_manager.py`):
   * Cơ chế chống phình codebase đã hoàn thiện và kiểm chứng.
4. **Interactive Runtime Helper** (`scripts/harness/interactive_bridge.py`):
   * Đang phục vụ tốt mô hình tương tác ISP v1.0.

### 7.2. Thành phần CẦN CẢI TIẾN (Improve)
1. **`GEMINI.md` & `.agents/rules/AGENTS.md`**:
   * Cắt giảm nội dung dư thừa, loại bỏ bảng registry thủ công lặp lại.
   * Chuyển đổi thành **Minimal Context AGENTS.md**: chỉ lưu Project Identity, Core Invariants, Universal Constraints, Routing Rules, Definition of Done.
2. **`scripts/harness/evidence_verifier.py`**:
   * Mở rộng để không chỉ kiểm tra verbatim quotes văn bản, mà còn xuất ra **Canonical Verification Schema JSON** bao quát cả code checks (syntax, tests, git diff, sensitive files).
3. **`scripts/audit_skill.py`**:
   * Nâng cấp để kiểm định được cả các Engineering Skills mới.
4. **Hệ thống Rules (`.agents/rules/`)**:
   * Chuẩn hóa cấu trúc theo các khía cạnh kỹ thuật: `architecture.md`, `change-scope.md`, `security.md`, `verification.md` (giữ nguyên tinh thần của R0-R6 nhưng tinh gọn hơn).

### 7.3. Thành phần CẦN LOẠI BỎ HOẶC TINH GỌN (Remove / Consolidate)
1. **Các file script kiểm tra tản mát**:
   * Tinh gọn `scripts/verify_layout_parity.py` vào cùng bộ suite với `scripts/verify_retention.py`.
2. **Loại bỏ các bảng Skill Registry viết tay**:
   * Thay thế bằng một script CLI duy nhất tự động build registry khi cần thiết, tránh sai lệch phiên bản giữa 4 file tài liệu.

---

## 8. KIẾN TRÚC ĐÍCH ĐỀ XUẤT (TARGET ARCHITECTURE BLUEPRINT)

### 8.1. Sơ đồ Luồng Vận Hành (The AIWF Engineering Loop)

```mermaid
flowchart TD
    User([Người dùng / Task Input]) --> InputRouter{Phân loại Risk Tier}
    
    subgraph TIER_ROUTING ["Phân Loại Cấp Độ Rủi Ro"]
        InputRouter -->|Tier 0: Docs/Trivial| ImplDirect[Thực thi trực tiếp]
        InputRouter -->|Tier 1: Small isolated| PlanLight[Lập kế hoạch nhanh]
        InputRouter -->|Tier 2: Multi-file / Core| PlanFull[Lập kế hoạch đầy đủ]
        InputRouter -->|Tier 3: Security / DB / Auth| PlanRisk[Kế hoạch & Phân tích rủi ro cao]
    end

    subgraph PHASE_PLAN ["PHA 1: PLANNER (Read-only)"]
        PlanLight & PlanFull & PlanRisk --> RolePlanner[Agent: PLANNER]
        RolePlanner --> TaskLedger[Tạo/Cập nhật Task Ledger]
        RolePlanner --> CritCheck[Xác lập Acceptance Criteria & Blast Radius]
    end

    CritCheck --> RoleImplementer[Agent: IMPLEMENTER]
    ImplDirect --> RoleImplementer

    subgraph PHASE_EXEC ["PHA 2: IMPLEMENTER (Surgical Edits)"]
        RoleImplementer --> PreToolHook{PreToolUse Hook}
        PreToolHook -->|Chặn .env / Sensitive / Destructive| HookDeny[BLOCK Execution]
        PreToolHook -->|Hợp lệ| ExecTool[Thực thi Edit / Run Command]
        ExecTool --> PostToolHook[PostToolUse Hook: Syntax Check / Format]
    end

    PostToolHook --> RoleVerifier[Agent: VERIFIER (Deterministic)]

    subgraph PHASE_VERIFY ["PHA 3: VERIFIER (Deterministic Checks)"]
        RoleVerifier --> DetChecks[Run Tests, Lint, Typecheck, Build]
        RoleVerifier --> ClaimChecks[Run Claim Guard / Evidence Verifier]
        RoleVerifier --> UICheck[Browser Verification if UI changed]
        DetChecks & ClaimChecks & UICheck --> VerifSchema[Xuất Canonical Verification JSON]
    end

    VerifSchema --> PassGate{Verifier Pass?}
    PassGate -->|FAIL| FixLoop[Chuyển phản hồi về Implementer sửa lỗi]
    FixLoop --> RoleImplementer

    PassGate -->|PASS| ReviewGateCheck{Cần Review độc lập? (Tier 2/3)}
    ReviewGateCheck -->|Tier 0/1: Không cần| PreStopGate
    ReviewGateCheck -->|Tier 2/3: Bắt buộc| RoleReviewer[Agent: REVIEWER (Read-only Context)]

    subgraph PHASE_REVIEW ["PHA 4: REVIEWER (Independent)"]
        RoleReviewer --> DiffAudit[Soát xét Git Diff & Scope Creep]
        RoleReviewer --> RegressCheck[Kiểm tra rủi ro hồi quy]
        DiffAudit & RegressCheck --> ReviewDecision{Reviewer Phê duyệt?}
    end

    ReviewDecision -->|REJECT| FixLoop
    ReviewDecision -->|APPROVE| HumanGateCheck{Tier 3?}

    HumanGateCheck -->|Có: Tier 3| HumanApproval[Chờ Human / User Phê Duyệt]
    HumanGateCheck -->|Không: Tier 2| PreStopGate
    HumanApproval --> PreStopGate

    subgraph PHASE_STOP ["PHA 5: COMPLETION GATE (Stop Hook)"]
        PreStopGate{Stop Hook: Đủ Evidence chưa?}
        PreStopGate -->|Thiếu Evidence / Status != PASS| ForceContinue[FORCE CONTINUE: Không cho dừng]
        ForceContinue --> FixLoop
        PreStopGate -->|Đầy đủ Bằng chứng Hợp lệ| FinalDone([HOÀN THÀNH: Trả về Báo cáo kèm Evidence])
    end
```

### 8.2. Cấu trúc thư mục mục tiêu (Target Directory Layout)

Kiến trúc tôn trọng tuyệt đối tính tương thích ngược với AIWF hiện tại, chỉ bổ sung tầng Harness chuẩn hóa:

```text
ai-workforce/
├── AGENTS.md                                # Minimal Context: Invariants, Identity, DoD, Routing
├── GEMINI.md                                # File bootstrap trỏ về AGENTS.md và load rules
├── manifest.json
├── requirements.txt
├── package.json
│
├── .agents/
│   ├── hooks.json                           # Antigravity Native Lifecycle Hooks (PreToolUse, PostToolUse, Stop)
│   ├── rules/
│   │   ├── architecture.md                  # Kiến trúc hệ thống, nguyên tắc phân tách
│   │   ├── change-scope.md                  # Quy tắc khoanh vùng thay đổi, blast radius, Tiering
│   │   ├── security.md                      # Bảo vệ bí mật, cấm truy cập .env, credentials
│   │   ├── verification.md                  # Tiêu chuẩn nghiệm thu bằng chứng (Definition of Done)
│   │   ├── R0-git-sync-mandatory.md         # (Giữ nguyên)
│   │   ├── R1-zero-destruction.md           # (Giữ nguyên)
│   │   ├── R2-code-quality.md               # (Giữ nguyên)
│   │   ├── R3-operational-discipline.md     # (Giữ nguyên)
│   │   ├── R4-skill-standard-v1.md          # (Giữ nguyên)
│   │   ├── R5-legal-claim-compliance.md     # (Giữ nguyên)
│   │   └── R6-document-layout-preservation.md # (Giữ nguyên)
│   │
│   ├── agents/                              # Cấu hình vai trò chuyên biệt (Separation of Duties)
│   │   ├── planner.md                       # Persona & Ranh giới vai trò PLANNER
│   │   ├── implementer.md                   # Persona & Ranh giới vai trò IMPLEMENTER
│   │   ├── reviewer.md                      # Persona & Ranh giới vai trò REVIEWER
│   │   └── verifier.md                      # Persona & Ranh giới vai trò VERIFIER
│   │
│   ├── skills/                              # Thư viện kỹ năng (Domain + Harness)
│   │   ├── [16 Domain Skills hiện có...]    # Giữ nguyên 100% không đổi
│   │   ├── _shared/output_manager.py        # Giữ nguyên
│   │   │
│   │   │   ── CÁC CORE ENGINEERING SKILLS BỔ SUNG ──
│   │   ├── repo-understand/SKILL.md         # Khảo sát cấu trúc codebase an toàn
│   │   ├── plan-change/SKILL.md             # Lập kế hoạch thay đổi & xác lập Tier
│   │   ├── implement-change/SKILL.md        # Thực thi sửa mã phẫu thuật
│   │   ├── debug/SKILL.md                   # Điều tra & sửa lỗi theo Root Cause
│   │   ├── code-review/SKILL.md             # Soát xét diff độc lập
│   │   ├── regression-check/SKILL.md        # Kiểm tra tính toàn vẹn hệ thống cũ
│   │   ├── security-review/SKILL.md         # Thẩm định an toàn, lộ bí mật, permissions
│   │   ├── ui-verify/SKILL.md               # Kiểm định giao diện browser native
│   │   └── release-check/SKILL.md           # Thẩm định sẵn sàng bàn giao / commit
│   │
│   ├── workflows/                           # Workflows điều phối
│   │   ├── W0-so-tay-aiwf.md
│   │   ├── W1-chuan-bi-tuyen-dung.md
│   │   └── engineering-loop.md              # Workflow điều phối chu trình kỹ thuật chuẩn
│   │
│   └── knowledge/                           # SSOT Knowledge Base (Giữ nguyên)
│
├── scripts/
│   ├── harness/                             # Bộ công cụ thực thi Harness tất định
│   │   ├── verify.py                        # Runner chạy deterministic checks & xuất Verification JSON
│   │   ├── evidence_verifier.py             # (Nâng cấp) Trích dẫn & đối chiếu nguồn
│   │   ├── interactive_bridge.py            # (Giữ nguyên)
│   │   ├── pre_tool_guard.py                # Command handler cho PreToolUse hook (chặn .env, dangerous cmd)
│   │   ├── post_tool_checker.py             # Command handler cho PostToolUse hook (syntax check)
│   │   ├── completion_gate.py               # Command handler cho Stop hook (chặn done dối)
│   │   ├── task_ledger.py                   # Quản lý file Task Ledger nhẹ
│   │   └── changed_files.py                 # Tính toán git diff & changed files an toàn
│   │
│   ├── audit_skill.py                       # (Giữ nguyên / nâng cấp nhẹ)
│   ├── claim_guard.py                       # (Giữ nguyên)
│   ├── verify_retention.py                  # (Giữ nguyên)
│   └── auto-setup.sh                        # (Giữ nguyên)
│
└── docs/
    ├── AIWF_USER_HANDBOOK.md                # (Giữ nguyên)
    └── harness/                             # Tài liệu kỹ thuật Harness
        ├── AIWF_HARNESS_AUDIT.md            # (Tệp hiện tại)
        ├── AIWF_HARNESS_ARCHITECTURE.md     # Đặc tả kiến trúc chi tiết
        └── AIWF_HARNESS_USAGE.md            # Hướng dẫn vận hành cho kỹ sư
```

### 8.3. Đặc tả 4 Vai Trò (The 4 Conceptual Roles)

| Vai trò | Quyền hạn công cụ (Permissions) | Trách nhiệm chính (Responsibilities) | Điều cấm tuyệt đối (Absolute Bans) |
|---|---|---|---|
| **PLANNER** | `view_file`, `grep_search`, `list_dir`, `search_web`, `read_url_content` | • Hiểu thấu đáo yêu cầu của người dùng.<br>• Khảo sát codebase, xác định dependency, rủi ro.<br>• Phân loại Risk Tier (0, 1, 2, 3).<br>• Lập danh sách Acceptance Criteria rõ ràng.<br>• Khởi tạo Task Ledger. | ❌ CẤM thực hiện các thay đổi lớn vào mã nguồn.<br>❌ CẤM chạy các lệnh deployment hoặc xóa dữ liệu. |
| **IMPLEMENTER** | `view_file`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (approved dev commands) | • Thực hiện sửa đổi đúng theo phạm vi plan đã duyệt.<br>• Tuân thủ nghiêm ngặt Rule R2 (Code Quality).<br>• Chạy các bài kiểm tra cục bộ phạm vi hẹp. | ❌ CẤM tự ý mở rộng phạm vi (scope creep).<br>❌ CẤM tự tuyên bố công việc đã hoàn thành hoặc "production-ready". |
| **REVIEWER** | Read-only context (`view_file`, `grep_search`, `list_dir`, `run_command` cho git diff) | • Soát xét độc lập toàn bộ git diff.<br>• Đối chiếu thay đổi với Acceptance Criteria của Planner.<br>• Phát hiện lỗi logic, tác động phụ ngoài ý muốn.<br>• Kiểm tra an toàn bảo mật và rò rỉ secret. | ❌ CẤM sửa mã trực tiếp.<br>❌ CẤM phê duyệt chỉ dựa trên lời giải thích của Implementer mà không nhìn vào diff thực tế. |
| **VERIFIER** | `run_command` (test, build, lint, typecheck, scripts), `browser_subagent` (cho UI) | • Thực thi toàn bộ các bài kiểm tra tất định.<br>• Khởi động app và dùng browser verify giao diện nếu có thay đổi UI.<br>• Thu thập log lỗi, chụp màn hình bằng chứng.<br>• Xuất ra `verification_result.json` chuẩn hóa. | ❌ CẤM dùng suy luận định tính để thay thế cho lệnh test thực tế.<br>❌ CẤM chấp nhận kết quả nếu còn test bị fail. |

### 8.4. Cơ chế Antigravity Native Hooks Strategy

Cấu hình tại `.agents/hooks.json` sử dụng chính xác schema native của Antigravity:

```json
{
  "aiwf-safety-guard": {
    "enabled": true,
    "PreToolUse": [
      {
        "matcher": "run_command|write_to_file|replace_file_content|multi_replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/harness/pre_tool_guard.py",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "write_to_file|replace_file_content|multi_replace_file_content",
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/harness/post_tool_checker.py",
            "timeout": 15
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 scripts/harness/completion_gate.py",
        "timeout": 10
      }
    ]
  }
}
```

* **`PreToolUse` (`pre_tool_guard.py`)**:
  * Kiểm tra tham số lệnh hoặc đường dẫn file từ `stdin`.
  * Nếu cố tình đọc/ghi vào `.env`, `credentials.json`, private keys $\rightarrow$ Trả về `{"decision": "deny", "reason": "Blocked access to sensitive file"}`.
  * Nếu cố tình chạy các lệnh phá hủy (`rm -rf /`, `git push --force`) $\rightarrow$ Trả về `{"decision": "deny"}`.
* **`PostToolUse` (`post_tool_checker.py`)**:
  * Kiểm tra cú pháp (syntax check) nhanh đối với file vừa được chỉnh sửa (`python -m py_compile`, `node --check`).
  * Báo lỗi ngay lập tức nếu file vừa sửa bị lỗi cú pháp, ngăn lỗi tích tụ.
* **`Stop` (`completion_gate.py`)**:
  * Đọc trạng thái từ `task_ledger.json` và `verification_result.json`.
  * Nếu agent cố dừng lại mà:
    1. Chưa chạy verification của Tier tương ứng, HOẶC
    2. Verification result có `status != "PASS"`, HOẶC
    3. Còn tiêu chí nghiệm thu chưa được tick hoàn thành.
  * $\rightarrow$ Trả về `{"decision": "continue", "reason": "Chưa hoàn tất kiểm định bằng chứng hoặc còn kiểm thử thất bại. Không được dừng lại."}`.

---

## 9. LỘ TRÌNH TRIỂN KHAI TỪNG BƯỚC (PHASED IMPLEMENTATION PLAN)

Để đảm bảo tính an toàn tuyệt đối và không làm gián đoạn hệ thống, quá trình nâng cấp được chia làm 7 giai đoạn tuần tự:

```
[Phase 1: Audit] (Hiện tại)
       ↓
[Phase 2: Foundation] (AGENTS.md tinh gọn, Rules hierarchy, DoD, Verification Schema, Task Ledger)
       ↓
[Phase 3: Core Workflow] (4 Roles: Planner, Implementer, Reviewer, Verifier & Minimal Skills)
       ↓
[Phase 4: Deterministic Quality Gates] (Antigravity Native hooks.json, PreToolUse, Stop Gate)
       ↓
[Phase 5: UI Verification] (Tích hợp browser_subagent, snapshot evidence, console inspection)
       ↓
[Phase 6: Observability] (Nhật ký metrics nhẹ: token, retry, failure points)
       ↓
[Phase 7: Evaluation & Benchmarks] (Thực nghiệm đối chứng: Baseline vs Harness)
```

---

## 10. CÁC VẤN ĐỀ CẦN PHÊ DUYỆT & ĐIỂM DỪNG KỸ THUẬT

Theo chỉ thị của người dùng:
> *"STOP after the audit and architecture proposal if any major architectural uncertainty remains. Otherwise proceed incrementally."*

### 10.1. Điểm xác nhận kiến trúc (Architectural Confirmations)
1. **Vị trí của `hooks.json`**: Cấu hình sẽ đặt tại `.agents/hooks.json` (Customization Root của workspace) để đồng bộ 100% qua Git theo Rule R0.
2. **Bảo toàn 16 Domain Skills**: Toàn bộ 16 kỹ năng hiện tại được giữ nguyên vẹn 100%, không bị xáo trộn. Tầng Harness Kỹ thuật được bổ sung dưới dạng các Core Engineering Skills song hành.
3. **Đơn giản hóa AGENTS.md**: Giữ `GEMINI.md` làm cổng đón tiếp xúc tích, nạp các rules chi tiết qua cơ chế Progressive Disclosure của Antigravity để tiết kiệm token tối đa.

---
*Báo cáo Audit đã hoàn tất và sẵn sàng cho việc xem xét, đánh giá.*
