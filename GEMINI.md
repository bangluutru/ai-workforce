# AI WORKFORCE — Hướng dẫn vận hành cho AI Agent

> File này được nạp TỰ ĐỘNG khi mở thư mục `ai-workforce` làm workspace trong Antigravity IDE (hoặc Cursor/VS Code có AI agent).
> Agent PHẢI đọc file này TRƯỚC KHI thực hiện bất kỳ yêu cầu nào.

---

## 🔴 NGUYÊN TẮC TỐI CAO — R0: MỌI THAY ĐỔI PHẢI ĐỒNG BỘ ĐƯỢC QUA GIT

> **BẤT DI BẤT DỊCH.** Trước MỌI thay đổi cho AIWF, Agent PHẢI tự hỏi:
> 1. Thay đổi này nằm trong workspace hay ngoài?
> 2. Sau `git pull` trên máy khác, thay đổi có tự kích hoạt không?
> 3. File nào cần `git add/commit`?
>
> **Nếu không đồng bộ được → DỪNG LẠI, sửa trước khi tiếp tục.**
> Chi tiết: `.agents/rules/R0-git-sync-mandatory.md`

---

## ⚡ LỆNH KÍCH HOẠT NHANH TỪ NGƯỜI DÙNG

Khi người dùng nhắn bất kỳ câu nào sau đây:
- *"Cài đặt môi trường từ README"*
- *"Đồng bộ quy tắc từ README.md"*
- *"Khởi tạo môi trường AIWF"*
- *"Kiểm định skill [tên]"* hoặc *"Audit skill [tên]"*
- *"Chuẩn hóa workspace Antigravity"* hoặc *"Dọn dẹp phân mảnh scratch"* (kích hoạt workflow `W2-chuan-hoa-workspace-ag` chạy `python3 scripts/standardize_workspace.py`)
- Hoặc mở phiên làm việc mới trên máy mới

👉 **Agent PHẢI tự động thực hiện ngay 4 bước sau mà không cần hỏi lại:**
1. **Đọc `README.md` và `.agents/rules/*.md`** để nạp toàn bộ luật và quy trình (bao gồm Luật R4 về chuẩn kỹ năng).
2. **Kiểm tra và tự động cài đặt toàn bộ Python & Sync dependencies**:
   ```bash
   python3 -c "import docx; import fitz; import pdfplumber; import notebooklm" 2>/dev/null || pip3 install -r requirements.txt
   playwright install chromium 2>/dev/null || python3 -m playwright install chromium 2>/dev/null || true
   bash scripts/auto-setup.sh --quiet 2>/dev/null || true
   ```
3. **Quét danh mục skills** trong `.agents/skills/`, kiểm tra chứng chỉ kiểm định Rule R4 (`python3 scripts/audit_skill.py --scan-new`) và nạp kho tri thức `.agents/knowledge/` để sẵn sàng nhận lệnh.
4. **Báo cáo tóm tắt trạng thái sẵn sàng cho người dùng:**
   - *"✅ AI Workforce đã thiết lập môi trường và đồng bộ toàn bộ 18 skills, 8 bộ quy tắc an toàn (R0-R7), thư viện engine dùng chung `_shared/` cùng kho tri thức SSOT sẵn sàng 100% (không cần API key bên ngoài)."*
   - Hướng dẫn phần đăng nhập Google Notebook (nếu người dùng muốn sync dữ liệu trực tiếp): *"💡 Dữ liệu tri thức đã có sẵn offline. Nếu bạn muốn kết nối trực tiếp với Google NotebookLM để kéo thêm tài liệu mới từ tài khoản của mình, hãy mở Terminal và gõ: `notebooklm login` (trình duyệt sẽ mở ra để bạn đăng nhập 1 lần duy nhất)."*

---

## ⚠️ NGUYÊN TẮC BẮT BUỘC — ZERO EXTERNAL LLM API

1. **KHÔNG gọi REST API mô hình ngôn ngữ bên ngoài** (Gemini API, OpenAI API, Claude API, v.v.) và **KHÔNG yêu cầu API key** để phục vụ việc suy luận/tư duy của bất kỳ skill nào. Toàn bộ năng lực AI (dịch thuật, phân tích, tóm tắt, viết bài, đánh giá...) là của **chính Agent tích hợp trong IDE**.
2. **PHÂN BIỆT RÕ RÀNG VỚI PRODUCT / MEDIA APIs**:
   - *Product / Business API:* Được phép giao tiếp khi nghiệp vụ sản phẩm yêu cầu (ví dụ: Landing Hub API trong `tao-landing-page` để xuất bản landing page).
   - *Data / Media Service API:* Được phép sử dụng như tiện ích bổ trợ tải media/dữ liệu miễn phí (ví dụ: Pexels/Pixabay API trong `video-studio`).
   - Tuyệt đối không viện dẫn API bên thứ ba chỉ vì sự tiện lợi cá nhân nếu tính năng đó có thể xử lý cục bộ.
3. **Python scripts** trong `.agents/skills/*/scripts/` chỉ phục vụ xử lý dữ liệu (bóc tách, merge, validate, xuất bản file) — **KHÔNG chứa logic gọi LLM API ngoài**.
4. Khi được kích hoạt, skill **PHẢI tự chạy liên tục** cho đến khi hoàn tất 100% — **KHÔNG tự dừng giữa chừng** để xin phép.
5. **KHÔNG BỊA DỮ LIỆU**. Mọi thông tin chính sách, bảng giá, quy trình phải dựa trên `.agents/knowledge/`.

---

## 📄 Đọc tệp người dùng

**KHÔNG BAO GIỜ đọc trực tiếp tệp nhị phân** (DOC/DOCX, XLS/XLSX, PPT/PPTX, PDF, EPUB, ODT/ODS/ODP, RTF, ảnh) bằng công cụ đọc file — sẽ ra rác hoặc mất bảng/dấu. Luôn chuyển đổi trước:

```bash
.venv/bin/python scripts/doc_ingest.py "<tệp>" ["<tệp 2>" ...] --out ~/Downloads/AIWF_Output/_ingest/<tên_việc> --json
```

Rồi đọc `source.md` (nội dung: bảng dạng `|...|`, ảnh `![](media/..)`, PDF có `<!-- page N -->`, PPTX `## Slide N` + ghi chú, XLSX mỗi sheet một mục kèm bảng công thức) và `manifest.json` (`warnings`, `pages_needing_ocr`, `legacy_encoding`). Nhiều tệp → mỗi tệp một thư mục con + `index.json`. Tệp dài: đọc `source.md` theo từng đoạn/marker trang, không nạp một lần.

| Mã thoát | Ý nghĩa | Agent làm gì |
|:---:|---|---|
| 0 | Đọc đầy đủ | Dùng `source.md`; vẫn đọc `warnings` (vd: đã chuyển mã TCVN3, đã tính lại công thức). |
| 3 | Có trang scan/ảnh không có lớp chữ | Đọc ảnh trong `ocr_pages/` (bản nháp OCR trong `source.md` CHƯA kiểm chứng). Tài liệu scan dài → dùng skill **boc-tach-pdf**. |
| 2 | Không đọc được (PDF mật khẩu, EPUB DRM, Office mã hoá, tệp rỗng/hỏng) | Hỏi người dùng đúng điều ghi trong `manifest.message` (bản không mật khẩu/không DRM/tệp gốc). Không đoán mật khẩu. |
| 4 | Thiếu phụ thuộc | Làm theo `manifest.message` (vd `bash scripts/auto-setup.sh`, `brew install --cask libreoffice`). |

---

## 📦 SKILL REGISTRY — Bản đồ 18 kỹ năng chuẩn hóa

Khi user yêu cầu thực hiện một skill, Agent PHẢI:
1. Định tuyến dựa trên: **LOẠI ĐẦU VÀO + Ý ĐỊNH NGƯỜI DÙNG + KẾT QUẢ ĐẦU RA KỲ VỌNG** (không chỉ dựa vào từ khóa rời rạc).
2. **Đọc file SKILL.md** tương ứng để nắm quy trình chi tiết.
3. Thực hiện đầy đủ các bước trong SKILL.md.
4. **Khi tạo/sửa skill hoặc viết script mới:** tra `.agents/skills/_shared/ENGINES.md` trước — năng lực đã có thì GỌI LẠI, không viết lại (Luật R7).

| STT | Skill (`name`) | Tên hiển thị | Phân định định tuyến cốt lõi | SKILL.md Path |
|:---:|----------------|--------------|------------------------------|---------------|
| 1 | **ejv-translate** | EJV Translate | Dịch văn bản dài (Word, Text, Markdown, PDF chữ đơn giản) 3 ngôn ngữ Việt - Anh - Nhật, xuất bản song ngữ/tam ngữ DOCX/PDF. Đầu vào/đầu ra là PDF cần giữ bố cục → `dich-thuat`. | `.agents/skills/ejv-translate/SKILL.md` |
| 2 | **dich-thuat** | Dịch Thuật | Dịch tài liệu PDF với 2 chế độ: **preserve** (giữ 1:1 bố cục, số trang, ảnh, con dấu SMask, khung hoa văn — chứng chỉ, hợp đồng, PDF 2 cột) và **reconstruct** (tái dựng reflow tự nhiên, bảng/công thức/diagram, không ép giữ trang/dòng — báo cáo kỹ thuật, học thuật). | `.agents/skills/dich-thuat/SKILL.md` |
| 3 | **boc-tach-pdf** | Bóc Tách PDF | Bóc tách OCR tài liệu PDF scan dài thành Word (.docx) hoặc Markdown (.md) trung thực giữ font, lề, ảnh gốc. | `.agents/skills/boc-tach-pdf/SKILL.md` |
| 4 | **xu-ly-van-phong** | Xử Lý Văn Phòng | Soạn thảo, chỉnh sửa, chuyển đổi văn bản hành chính theo chuẩn thể thức NĐ 30/2020/NĐ-CP (Word, PDF, PPT, Excel biểu mẫu). | `.agents/skills/xu-ly-van-phong/SKILL.md` |
| 5 | **bao-cao-kt** | Báo Cáo Kế Toán | Lập báo cáo tài chính/kế toán VAS/TT200/TT133, dashboard số liệu kinh doanh với **100% công thức động Live Formulas** trong Excel. | `.agents/skills/bao-cao-kt/SKILL.md` |
| 6 | **tu-van-phap-luat** | Tư Vấn Pháp Luật | Tra cứu và tư vấn đường lối giải quyết vấn đề pháp lý Việt Nam, trích dẫn nguyên văn văn bản quy phạm pháp luật theo PDCA Cascade. | `.agents/skills/tu-van-phap-luat/SKILL.md` |
| 7 | **tu-van-thue-tncn** | Tư Vấn Thuế TNCN | Quyết toán thuế TNCN, tính thuế thu nhập cá nhân, quy đổi Gross-Net, giảm trừ gia cảnh, eTax Mobile, xuất Excel Live Formulas. | `.agents/skills/tu-van-thue-tncn/SKILL.md` |
| 8 | **viet-bai** | Viết Bài Đa Kênh | Sáng tạo nội dung chữ tiếp thị đa nền tảng (Blog SEO, Website, Facebook, PR) tuân thủ nghiêm ngặt Luật Quảng cáo (Luật R5). | `.agents/skills/viet-bai/SKILL.md` |
| 9 | **chotto-newsroom** | Biên Tập Tin Chotto | Tòa soạn tin tức hàng ngày chottoday.com: tra cứu nguồn chính phủ Nhật (.go.jp), lập Fact Pack, xuất bản tin tức chính sách cho người Việt tại Nhật. | `.agents/skills/chotto-newsroom/SKILL.md` |
| 10 | **thiet-ke** | Thiết Kế Đồ Họa | Thiết kế ấn phẩm in ấn tiếp thị (Leaflet, Brochure gấp 2/3, Poster, Tờ rơi, slide dạng ấn phẩm xuất PDF) chuẩn xén lề bleed và PDF in ấn. Không lập trình web; slide `.pptx` chỉnh sửa được → `xu-ly-van-phong`. | `.agents/skills/thiet-ke/SKILL.md` |
| 11 | **tao-landing-page** | Tạo Landing Page | Chuyển đổi bản thiết kế Figma/Stitch/mockup thành mã nguồn trang đích (React + Vite + Tailwind hoặc HTML/CSS), tích hợp Landing Hub. | `.agents/skills/tao-landing-page/SKILL.md` |
| 12 | **app-auditor** | Kiểm Định Ứng Dụng | Kiểm định toàn diện web app/landing page đang chạy: Playwright crawler, visual sweep 4 viewports, lỗi console/network, WCAG a11y. | `.agents/skills/app-auditor/SKILL.md` |
| 13 | **video-studio** | Studio Video | Sản xuất video đa phương tiện hoàn chỉnh từ kịch bản: stock media (Pexels/Pixabay), audio thuyết minh, BGM ducking, karaoke sub, xuất MP4. | `.agents/skills/video-studio/SKILL.md` |
| 14 | **phu-de** | Tạo Phụ Đề | Chuyên tạo, bóc tách và biên tập phụ đề video (SRT, ASS, hardsub MP4) với forced alignment từng từ và dịch phụ đề song ngữ. | `.agents/skills/phu-de/SKILL.md` |
| 15 | **long-tieng** | Lồng Tiếng Video | Chuyên thuyết minh, lồng tiếng video tự động qua TTS offline đa ngôn ngữ/vùng miền, đồng bộ khẩu hình và timeline phụ đề. | `.agents/skills/long-tieng/SKILL.md` |
| 16 | **hand-drawn-animation** | Tạo Hoạt Hình | Tạo hoạt hình vẽ tay Canvas 2D (5 phong cách: ink, riso, screen, pencil, doodle), rotoscope, sand animation, xuất HTML/MP4 offline. | `.agents/skills/hand-drawn-animation/SKILL.md` |
| 17 | **doc-sau** | Đọc Sâu | Phân tích chuyên sâu bài viết, tài liệu, sách, báo cáo nghiên cứu bằng 10+ mô hình tư duy (SCQA, 5W2H, phản biện, đảo ngược, đa ngành, đệ nhất, hệ thống, 6 nón); kích hoạt tri thức và Quick Win 24h. | `.agents/skills/doc-sau/SKILL.md` |
| 18 | **tu-van-phap-luat-nhat-ban** | Tư Vấn Pháp Luật Nhật Bản | Nghiên cứu và tư vấn pháp luật Nhật Bản theo tình huống, căn cứ tiếng Nhật, tra cứu mã HS hải quan Nhật, thuế quan, EPA/FTA, điều kiện lưu hành hàng hóa (thực phẩm, mỹ phẩm, điện tử), nhãn, quảng cáo và nghĩa vụ sau bán. | `.agents/skills/tu-van-phap-luat-nhat-ban/SKILL.md` |


---

## 🛡️ HỆ THỐNG QUY TẮC AN TOÀN (RULES)

| Rule File | Mục đích |
|-----------|----------|
| `.agents/rules/AGENTS.md` | Bản đồ tổ chức tổng, nguyên tắc KWSR, Zero-Hallucination |
| **`.agents/rules/R0-git-sync-mandatory.md`** | **🔴 NGUYÊN TẮC TỐI CAO: Mọi thay đổi PHẢI đồng bộ được qua Git** |
| `.agents/rules/R1-zero-destruction.md` | Bảo toàn dữ liệu qua lịch sử Git, nghiêm cấm xả rác vào workspace |
| `.agents/rules/R2-code-quality.md` | Zero-Inference Taxonomy, Codebase-first, Token Economics, 5 Absolute Bans |
| `.agents/rules/R3-operational-discipline.md` | Per-Task Verification, Autonomous Full-Run, Context Engineering (Quy tắc 15 tin nhắn, 3 Pha Explore-Plan-Execute, Subagent fork) |
| **`.agents/rules/R4-skill-standard-v1.md`** | **Tiêu chuẩn Kiến trúc & Tự kiểm duyệt Kỹ năng v1.2 (Gemini 3.8 Multi-Agent, Frontmatter Router, Live Formulas, Confidence Flagging)** |
| **`.agents/rules/R5-legal-claim-compliance.md`** | **Kiểm soát tính pháp lý nội dung, chống over-claim tiếp thị (Luật Quảng cáo 2012, NĐ 181, NĐ 38, TT 06/2011/TT-BYT)** |
| **`.agents/rules/R6-document-layout-preservation.md`** | **Tiêu chuẩn Bảo toàn Bố cục, Đồ họa & Thuật ngữ Chuyên ngành (7 Trụ cột RetainPDF: SMask Transparency, Subplot Bounding, Ornate Safe Zones, Multi-column Balance, Dual-Level Mapping, Domain Review, Tri-Layer Quality Gate)** |
| **`.agents/rules/R7-shared-engine-reuse.md`** | **🧩 Tái sử dụng engine dùng chung: tra `_shared/ENGINES.md` trước khi viết code; cấm chép file/engine giữa skill; cấm edge-tts (dùng VieNeu/Kokoro); cưỡng chế bằng `scripts/check_shared_reuse.py`** |

---

## 🔧 PATH RESOLUTION — Quy ước đường dẫn

Khi SKILL.md sử dụng các placeholder như `<skill_dir>`, `<process_dir>`, agent PHẢI resolve như sau:

| Placeholder | Giá trị thực |
|-------------|-------------|
| `<workspace>` | Thư mục root của workspace hiện tại (chứa file `GEMINI.md` này) |
| `<skill_dir>` | `<workspace>/.agents/skills/<tên_skill>/` |
| `<process_dir>` | Thư mục tạm để xử lý (ví dụ: `<workspace>/_process/<tên_tài_liệu>/` - đã được gitignore, hoặc artifact directory) |
| `<output_dir>` | **Nơi user chỉ định** hoặc **Mặc định: `~/Downloads/AIWF_Output/`** |
| `<file_goc>` | File đầu vào do user cung cấp |

> [!IMPORTANT]
> **QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat):**
> - Mọi skill khi xuất bản thành phẩm PHẢI cho phép người dùng chọn thư mục lưu hoặc mặc định lưu vào `<output_dir>` (`~/Downloads/AIWF_Output/` hoặc nơi user chỉ định).
> - TUYỆT ĐỐI KHÔNG tự ý lưu file kết quả / thư mục nghiên cứu vào thư mục gốc của codebase để tránh làm phình dung lượng git repository.

---

## 🐍 PYTHON DEPENDENCIES — Cài đặt tự động

Trước khi chạy bất kỳ Python script nào trong `.agents/skills/*/scripts/` hoặc `scripts/sync_notebook.py`, Agent PHẢI kiểm tra và cài dependencies nếu chưa có:

```bash
python3 -c "import docx; import fitz; import pdfplumber; import notebooklm" 2>/dev/null || pip3 install -r requirements.txt
```

Danh sách packages cần thiết (xem [`requirements.txt`](file:///Users/tranhaibang/.gemini/antigravity-ide/scratch/ai-workforce/requirements.txt)):
- `python-docx` — Tạo/đọc file DOCX
- `pymupdf` (fitz) — Đọc/render PDF
- `pdfplumber` — Trích xuất bảng biểu từ PDF
- `lxml` — Xử lý XML
- `markitdown` — Chuyển đổi Markdown
- `pypandoc` — Chuyển đổi định dạng tài liệu
- `notebooklm-py[browser]` — Đồng bộ tri thức từ Google Gemini Notebook (NotebookLM)

---

## 🆘 TROUBLESHOOTING

### "Agent yêu cầu API key"
**Nguyên nhân**: Thư mục `ai-workforce` chưa được mở làm workspace $\rightarrow$ Agent không nạp được GEMINI.md và AGENTS.md.
**Giải pháp**: Mở thư mục `ai-workforce` làm workspace trong Antigravity IDE: **File $\rightarrow$ Open Folder $\rightarrow$ chọn thư mục `ai-workforce`**.

### "Skill không tìm thấy"
**Nguyên nhân**: Agent chưa đọc GEMINI.md hoặc SKILL.md.
**Giải pháp**: Gõ câu lệnh: *"Đồng bộ quy tắc từ README.md"* hoặc gõ yêu cầu kèm tên skill rõ ràng.

### "Python script lỗi import"
**Nguyên nhân**: Chưa cài Python dependencies.
**Giải pháp**: Chạy `pip3 install -r requirements.txt` trong thư mục `ai-workforce`.
