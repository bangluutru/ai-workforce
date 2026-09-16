# 🤖 AI Workforce (AIWF)

> **Lực lượng Lao động AI — Company in a Folder**
>
> Hệ thống tác nhân số vận hành trên nền tảng [Antigravity IDE](https://antigravity.dev) (và tương thích hoàn toàn với VS Code, Cursor), giúp tự động hóa toàn diện quy trình doanh nghiệp bằng AI tích hợp sẵn — **100% Native, Zero External API, Zero Setup Hassle**.

👉 **[Xem ngay: Cẩm nang Sử dụng Thực chiến AIWF (AIWF User Handbook)](docs/AIWF_USER_HANDBOOK.md)** *(Hướng dẫn sử dụng chi tiết 4 kỹ năng, mẹo prompt, giao diện Extension và cách đồng bộ NotebookLM)*

---

## ⚡ Cài đặt & Khởi tạo môi trường tự động (Dành cho người không chuyên kỹ thuật)

Khi bạn clone hoặc pull repo này về bất kỳ máy nào, bạn không cần phải gõ lệnh cài đặt phức tạp. Bạn chỉ cần mở Antigravity IDE và gửi **1 câu lệnh duy nhất** vào khung chat:

> 💬 **Câu lệnh mẫu cho Agent:**
> *"Hãy đọc `README.md` và cài đặt môi trường cho tôi."*
>
> *(Hoặc ngắn gọn: **"Khởi tạo môi trường AIWF"** hoặc **"Đồng bộ quy tắc từ README.md"**)*

Khi nhận câu lệnh trên, Antigravity Agent sẽ **tự động thực hiện toàn bộ**:
1. 📦 Cài đặt đầy đủ các thư viện xử lý tài liệu & bóc tách PDF (`python-docx`, `pymupdf`, `pdfplumber`, `pypandoc`...).
2. 🔄 Cài đặt công cụ đồng bộ Google Gemini Notebook (`notebooklm-py` & trình duyệt Playwright).
3. 🔌 Tự động cài đặt Extension Sidebar và cấu hình Git Hooks tự cập nhật.
4. 🧠 Nạp toàn bộ 4 skills trong `.agents/skills/` và hệ thống 4 tầng quy tắc an toàn.
5. ✅ Báo cáo trạng thái hoàn tất và sẵn sàng 100% để bạn sử dụng ngay!

---

## 📑 Mục lục

- [Cài đặt & Khởi tạo môi trường tự động (Non-Tech)](#-cài-đặt--khởi-tạo-môi-trường-tự-động-dành-cho-người-không-chuyên-kỹ-thuật)
- [Bước Bắt Buộc: Mở đúng Workspace](#-bước-bắt-buộc--mở-đúng-thư-mục-workspace)
- [Đồng bộ Tri thức từ Google Gemini Notebook](#-đồng-bộ-tri-thức-từ-google-gemini-notebook-notebooklm)
- [Các cách cài đặt khác (Dành cho Developer)](#-các-cách-cài-đặt-khác-dành-cho-developer)
- [Danh mục 4 Nhân sự số (Skills)](#-danh-mục-4-nhân-sự-số-skills)
- [Bộ Tứ Quy Tắc Vận Hành (Rules)](#-bộ-tứ-quy-tắc-vận-hành-rules)
- [Kiến trúc KWSR](#-kiến-trúc-kwsr)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Sử dụng hàng ngày](#-sử-dụng-hàng-ngày)
- [Troubleshooting](#-troubleshooting)

---

## ⚠️ Bước Bắt Buộc — Mở đúng thư mục workspace

> **Đây là điều kiện TIÊN QUYẾT để AIWF hoạt động đúng trên mọi máy tính:**

Sau khi clone hoặc pull repo về máy:
1. Mở Antigravity IDE (hoặc VS Code / Cursor).
2. Chọn **File $\rightarrow$ Open Folder** (hoặc `Cmd+O` / `Ctrl+O`).
3. Chọn **chính xác thư mục `ai-workforce`**.

❌ **KHÔNG** mở thư mục cha (ví dụ mở cả ổ đĩa hoặc mở `Documents/`) rồi bấm vào thư mục con.  
❌ **KHÔNG** mở file đơn lẻ.  
✅ **PHẢI** mở thư mục `ai-workforce` làm **Root Workspace** để Antigravity tự động phát hiện và nạp cấu hình từ `GEMINI.md` và `.agents/`.

---

## 🔄 Đồng bộ Tri thức từ Google Gemini Notebook (NotebookLM)

Hệ thống AI Workforce kết nối trực tiếp với **Google Gemini Notebook** để làm Nguồn Sự Thật Duy Nhất (Single Source of Truth - SSOT):

### 1. Sử dụng tri thức có sẵn (Không cần đăng nhập)
* Toàn bộ tài liệu, sổ tay, chính sách đã được bóc tách sẵn vào thư mục `.agents/knowledge/`.
* Khi bạn pull repo về máy mới, **Agent có thể đọc và sử dụng ngay lập tức** mà bạn không cần đăng nhập bất cứ tài khoản nào.

### 2. Tự đồng bộ thêm tài liệu mới từ Google Notebook của bạn (Tự đăng nhập 1 lần)
Nếu bạn muốn kết nối với tài khoản Google của mình để kéo thêm tài liệu mới nhất từ trên [notebook.google.com](https://notebook.google.com):
* **Bước 1 (Người dùng tự làm 1 lần duy nhất):** Mở Terminal trên IDE và gõ:
  ```bash
  notebooklm login
  ```
  *(Một cửa sổ trình duyệt sẽ tự động mở ra $\rightarrow$ bạn đăng nhập tài khoản Google của mình $\rightarrow$ sau khi đăng nhập xong trình duyệt sẽ tự đóng và lưu phiên an toàn trên máy).*
* **Bước 2:** Sau khi đăng nhập xong, bạn có thể đồng bộ bất cứ lúc nào bằng lệnh:
  ```bash
  python3 scripts/sync_notebook.py
  ```
  *(Hoặc chỉ cần nhắn Agent: **"Đồng bộ ghi chú từ Gemini Notebook"**).*

---

## 🚀 Các cách cài đặt khác (Dành cho Developer)

### Cách 1: 1-Click Setup bằng Script
```bash
# macOS / Linux:
./setup.sh

# Windows:
setup.bat
```

### Cách 2: Tự động chạy ngầm khi mở thư mục trong IDE
Thư mục đã tích hợp sẵn `.vscode/tasks.json` (`runOn: folderOpen`). Khi bạn mở thư mục `ai-workforce` trong IDE, tác vụ cài đặt ngầm sẽ tự động chạy.

### Cách 3: Đồng bộ tự động sau mỗi lần `git pull`
Nhờ Git Hook `scripts/hooks/post-merge`, mỗi khi bạn gõ:
```bash
git pull origin main
```
Hệ thống sẽ tự động cập nhật extension và rebuild dashboard ngay lập tức.

---

## 📦 Danh mục 13 Nhân sự số (Skills)

Toàn bộ 13 skills đã được đóng gói độc lập, không phụ thuộc môi trường bên ngoài:

| STT | Tên Skill | Chức năng chính | Câu lệnh kích hoạt (Trigger mẫu) |
|:---:|---|---|---|
| 1 | **ejv-translate** | Dịch thuật tài liệu 3 ngôn ngữ (VN - EN - JP) chuẩn hành chính, bảo toàn bố cục in ấn DOCX/PDF | *"Dịch tài liệu 3 ngôn ngữ file này"*, *"EJV Translator"* |
| 2 | **boc-tach-pdf** | Số hóa PDF scan dài thành Word DOCX trung thực, giữ font, lùi dòng, bảng biểu | *"Bóc tách file PDF scan này ra Word"*, *"OCR PDF"* |
| 3 | **tu-van-phap-luat** | Tra cứu điều khoản, đối chiếu quy định và tư vấn giải pháp pháp lý Việt Nam | *"Tư vấn pháp luật về việc này"*, *"Tra cứu luật"* |
| 4 | **xu-ly-van-phong** | Chuyển đổi và tạo lập văn bản Word, Excel, PowerPoint, PDF chuẩn Nghị định 30 | *"Xử lý văn phòng"*, *"Soạn công văn chuẩn NĐ 30"* |
| 5 | **viet-bai** | Sáng tạo nội dung đa nền tảng (Blog SEO, Web Landing Page, Facebook, PR) với tra cứu Internet SSOT | *"Viết bài"*, *"Copywriting"*, *"Viết blog SEO"*, *"Soạn bài Facebook"* |
| 6 | **thiet-ke** | Thiết kế Leaflet/Brochure A4 gấp 2-3, đồ họa responsive và xuất PDF in ấn cao cấp | *"Thiết kế leaflet"*, *"Thiết kế brochure"* |
| 7 | **bao-cao-kt** | Phân tích số liệu, dashboard kinh doanh với 100% Live Formulas, xuất Excel, GSheet, Slides | *"Báo cáo KT"*, *"Báo cáo tài chính"*, *"Dashboard kinh doanh"*, *"Xuất slides báo cáo"* |
| 8 | **phu-de** | Tạo và dịch phụ đề video tự động, xuất file SRT/ASS, gắn hardsub bằng FFmpeg và whisper | *"Tạo phụ đề"*, *"Làm phụ đề video"*, *"Dịch phụ đề"*, *"Xuất phụ đề srt ass"* |
| 9 | **app-auditor** | Kiểm định toàn diện ứng dụng web: App Map, Visual sweep 4 viewports, lỗi console/network, axe-core WCAG A/AA, difficult user mode | *"Kiểm định ứng dụng"*, *"App auditor"*, *"Test ứng dụng"*, *"Audit web"*, *"QA web"* |
| 10 | **tu-van-thue-tncn** | Tư vấn thuế TNCN 2026, biểu 5 bậc, giảm trừ gia cảnh, y tế, giáo dục, hưu trí, eTax Mobile, xuất Excel Live Formulas | *"Tư vấn thuế TNCN"*, *"Tính thuế thu nhập cá nhân"*, *"Quyết toán thuế TNCN"*, *"Giảm trừ gia cảnh"* |
| 11 | **tao-landing-page** | Chuyển đổi thiết kế Google Stitch / Figma thành Landing Page React+Vite+TS+Tailwind production-ready, tích hợp Landing Hub v1.0 | *"Tạo landing page"*, *"Design to Landing"*, *"Stitch sang landing page"*, *"Figma sang landing page"* |
| 12 | **long-tieng** | Lồng tiếng và thuyết minh video tự động thông minh, đồng bộ mốc thời gian, Smart Audio Ducking, 5 sao VI/JA/EN | *"Lồng tiếng video"*, *"Thuyết minh video"*, *"Video dubbing"*, *"Voiceover clip"* |
| 13 | **dich-giu-dinh-dang** | Dịch giữ định dạng PDF chuyên khảo, bảo toàn 100% hình ảnh, đồ thị đa phần tử, con dấu trong suốt và bố cục 1:1 theo Luật R6 | *"Dịch giữ định dạng"*, *"Dịch bảo toàn định dạng PDF"*, *"Retain-PDF"* |

---

## 🛡️ Hệ Thống 5 Bộ Quy Tắc Vận Hành (Rules)

Hệ thống vận hành theo 5 bộ quy tắc nền tảng đặt tại `.agents/rules/`:

0. **R0 — Git Sync Mandatory (`R0-git-sync-mandatory.md`)**:
   - **🔴 NGUYÊN TẮC TỐI CAO:** Mọi thay đổi PHẢI đồng bộ được qua Git. Nếu `git pull` trên máy mới không tái tạo được 100% hệ thống thì thay đổi đó SAI.

1. **R1 — Zero-Destruction (`R1-zero-destruction.md`)**:
   - **Bảo toàn lịch sử qua Git**: Mọi thay đổi và tệp tin đều được kiểm soát phiên bản bằng Git commit, có thể phục hồi bất kỳ lúc nào qua `git checkout` / `git restore`.
   - **Triệt tiêu rác trong workspace**: Nghiêm cấm tạo các thư mục rác cục bộ `_Delete/` và `_Archive/`.
   - **Anti-Repo Bloat**: Mọi thành phẩm xuất bản phải lưu vào `<output_dir>` (mặc định: `~/Downloads/`), không xả rác vào root repository.

2. **R2 — Code Quality (`R2-code-quality.md`)**:
   - **Zero-Inference Taxonomy**: Phân định rõ OBSERVED, DERIVED, PRIOR, ASSUMED.
   - **Codebase-first**: Luôn đọc file thực tế và kiểm tra blast radius trước khi sửa.
   - **5 Absolute Bans**: Cấm code placeholder, cấm nuốt lỗi, cấm sửa file chưa đọc, cấm bịa API, cấm hardcode secret.

3. **R3 — Operational Discipline (`R3-operational-discipline.md`)**:
   - **Per-Task Verification**: Bắt buộc kiểm chứng kết quả chạy thực tế trước khi báo hoàn thành.
   - **Autonomous Full-Run**: Tự động chạy liên tục từ bước đầu đến bước cuối mà không dừng xin phép giữa chừng.
   - **Gemini 3.8 Context Engineering**: Quy tắc 15 tin nhắn (Rolling Summary), quy trình 3 pha Explore-Plan-Execute, phân tách Subagent với `context: fork`.

4. **R4 — Skill Standard v1.2 (`R4-skill-standard-v1.md`)**:
   - Tiêu chuẩn 5 lớp kiến trúc nhân sự số (Metadata Contract, Intake & Anti-Bloat, Zero-API & Live Engine, Modular Code, Quality Gate & Clean Handover).
   - Tự động kiểm duyệt qua script `scripts/audit_skill.py`. Toàn bộ 7 skills đạt chứng chỉ 100/100 tuyệt đối.

---

## 🏗️ Kiến trúc KWSR

AIWF được quy hoạch theo nguyên tắc **"Company in a Folder"**:

```
┌─────────────────────────────────────────────────┐
│              AI Workforce (KWSR)                │
├──────────┬──────────┬──────────┬────────────────┤
│ [K]      │ [W]      │ [S]     │ [R]            │
│ Knowledge│ Workflow  │ Skill   │ Rule           │
│          │          │         │                │
│ Nguồn    │ Sổ tay   │ "JD"   │ Rào chắn       │
│ sự thật  │ vận hành │ của AI  │ an toàn        │
│ (SSOT)   │ (I-P-O)  │ agents  │                │
└──────────┴──────────┴──────────┴────────────────┘
```

---

## 📂 Cấu trúc thư mục

```
ai-workforce/                         ← ROOT WORKSPACE (Mở thư mục này)
│
├── GEMINI.md                         ← 🤖 Hướng dẫn nạp tự động cho Antigravity
├── README.md                         ← 📖 Tài liệu hướng dẫn & quy trình đồng bộ
├── requirements.txt                  ← 🐍 Danh mục Python dependencies
├── setup.sh / setup.bat              ← ⚡ Script cài đặt 1-click
│
├── .agents/                          ← 🧠 TRUNG TÂM TRI THỨC & NHÂN SỰ
│   ├── rules/                        ← [R] Luật lệ vận hành
│   │   ├── AGENTS.md                 ← Bản đồ tổ chức tổng
│   │   ├── R0-git-sync-mandatory.md  ← Nguyên tắc tối cao đồng bộ Git
│   │   ├── R1-zero-destruction.md    ← Bảo toàn dữ liệu vật lý
│   │   ├── R2-code-quality.md        ← Quy chuẩn chất lượng mã nguồn
│   │   ├── R3-operational-discipline.md ← Kỷ luật thực thi & Gemini 3.8
│   │   └── R4-skill-standard-v1.md   ← Chuẩn 5 lớp & Audit 100đ
│   │
│   ├── skills/                       ← [S] 13 Nhân sự số chuyên trách
│   │   ├── ejv-translate/            ← Dịch thuật 3 ngôn ngữ VN/EN/JP
│   │   ├── boc-tach-pdf/             ← Số hóa PDF scan sang DOCX
│   │   ├── tu-van-phap-luat/         ← Tư vấn pháp luật Việt Nam
│   │   ├── xu-ly-van-phong/          ← Văn bản Word/Excel/PPT/PDF chuẩn NĐ 30
│   │   ├── viet-bai/                 ← Copywriting đa nền tảng & tra cứu Internet SSOT
│   │   ├── thiet-ke/                 ← Thiết kế Landing Page & Leaflet/Brochure PDF
│   │   ├── bao-cao-kt/               ← Dashboard tài chính Live Formulas, Excel/Slides
│   │   ├── phu-de/                   ← Tạo phụ đề, dịch phụ đề SRT/ASS & hardsub video
│   │   ├── app-auditor/              ← Kiểm định toàn diện web/app đa khung nhìn & QA khó tính
│   │   ├── tu-van-thue-tncn/         ← Tư vấn thuế TNCN 2026 & bảng tính Excel Live Formulas
│   │   ├── tao-landing-page/         ← Thiết kế Landing Page React/Tailwind chuẩn Stitch/Figma
│   │   ├── long-tieng/               ← Lồng tiếng video tự động & Smart Audio Ducking
│   │   └── dich-giu-dinh-dang/       ← Dịch giữ định dạng PDF bảo toàn 1:1 theo Luật R6
│   │
│   ├── knowledge/                    ← [K] Nguồn sự thật duy nhất (SSOT)
│   └── workflows/                    ← [W] Quy trình mẫu
│
├── dashboard/                        ← 🖥️ Web Dashboard (giao diện trực quan)
├── extension/                        ← 🔌 IDE Extension Sidebar
└── scripts/                          ← 🔧 Auto-Setup & Git Hooks
```

---

## 💼 Sử dụng hàng ngày

### 1. Kích hoạt bằng câu lệnh tự nhiên
Bạn chỉ cần mở chat và nhắn trực tiếp:
- *"Thực hiện skill ejv-translate với file /path/to/file.pdf"*
- *"Bóc tách tài liệu scan này sang Word"*
- *"Lập đề nghị thanh toán từ thư mục hóa đơn này"*

### 2. Kích hoạt qua Sidebar Extension
Bấm vào biểu tượng **AI Workforce** ở thanh bên trái IDE $\rightarrow$ Click vào skill muốn dùng $\rightarrow$ Lệnh kích hoạt sẽ tự động điền vào khung chat.

### 3. Kích hoạt qua Web Dashboard
Mở tệp `dashboard/index.html` trên trình duyệt $\rightarrow$ Chọn skill $\rightarrow$ Sao chép mẫu lệnh và dán vào chat.

---

## 🆘 Troubleshooting

### ❓ "Agent yêu cầu API key của Gemini/OpenAI khi chạy skill"
- **Nguyên nhân**: Bạn chưa mở đúng thư mục `ai-workforce` làm workspace, khiến Agent không nạp được `GEMINI.md` và `.agents/`.
- **Cách xử lý**: Đóng cửa sổ hiện tại $\rightarrow$ Chọn **File $\rightarrow$ Open Folder** $\rightarrow$ Trỏ vào đúng thư mục `ai-workforce`. Sau đó nhắn: *"Đồng bộ quy tắc từ README.md"*.

### ❓ "Lỗi `ModuleNotFoundError: No module named 'fitz'` hoặc `'docx'`"
- **Nguyên nhân**: Môi trường Python trên máy mới chưa cài thư viện.
- **Cách xử lý**: Chạy lệnh cài đặt:
  ```bash
  pip3 install -r requirements.txt
  ```
  Hoặc chạy lại `./setup.sh`.

### ❓ "Extension Sidebar không hiện danh sách skills"
- **Cách xử lý**: Nhấn biểu tượng 🔄 (Refresh) trên góc panel của Sidebar, hoặc nhấn `Cmd+Shift+P` (macOS) / `Ctrl+Shift+P` (Windows) $\rightarrow$ Chọn **"Developer: Reload Window"**.

---

## 📄 Bản quyền & Giấy phép
Tài liệu và hệ thống tác nhân số AI Workforce — Phát triển nội bộ, lưu hành và sử dụng đồng bộ trên toàn bộ thiết bị.
