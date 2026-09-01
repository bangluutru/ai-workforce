# 🤖 AI Workforce (AIWF)

> **Lực lượng Lao động AI — Company in a Folder**
>
> Hệ thống tác nhân số vận hành trên nền tảng [Antigravity IDE](https://antigravity.dev) (và tương thích hoàn toàn với VS Code, Cursor), giúp tự động hóa toàn diện quy trình doanh nghiệp bằng AI tích hợp sẵn — **100% Native, Zero External API, Zero Setup Hassle**.

---

## ⚡ Kích hoạt & Đồng bộ Quy tắc qua Antigravity

Khi bạn clone hoặc pull repo này về bất kỳ máy nào và mở thư mục `ai-workforce` trong Antigravity IDE, bạn chỉ cần gửi **1 câu lệnh duy nhất** vào khung chat:

> 💬 **Câu lệnh mẫu cho Agent:**
> *"Hãy đọc `README.md` và `GEMINI.md` để nạp toàn bộ quy tắc, cấu hình và danh mục 13 skills của AI Workforce. Sau đó kiểm tra môi trường xem đã sẵn sàng hoạt động chưa."*
>
> *(Hoặc ngắn gọn: **"Đồng bộ quy tắc từ README.md"**)*

Khi nhận câu lệnh trên, Antigravity Agent sẽ tự động:
1. Nạp toàn bộ 13 skills trong `.agents/skills/`.
2. Nạp hệ thống 4 tầng quy tắc an toàn (`AGENTS.md`, `R1`, `R2`, `R3`).
3. Tự động kiểm tra và cài đặt các thư viện Python cần thiết (`python-docx`, `pymupdf`, `pdfplumber`...).
4. Xác nhận hệ thống sẵn sàng 100% để bạn sử dụng ngay.

---

## 📋 Mục lục

- [Kích hoạt & Đồng bộ Quy tắc](#-kích-hoạt--đồng-bộ-quy-tắc-qua-antigravity)
- [Bước Bắt Buộc: Mở đúng Workspace](#-bước-bắt-buộc--mở-đúng-thư-mục-workspace)
- [Cài đặt trên máy mới](#-cài-đặt-trên-máy-mới)
- [Danh mục 13 Nhân sự số (Skills)](#-danh-mục-13-nhân-sự-số-skills)
- [Bộ Tứ Quy Tắc Vận Hành (Rules)](#-bộ-tứ-quy-tắc-vận-hành-rules)
- [Kiến trúc KWSR](#-kiến-trúc-kwsr)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Sử dụng hàng ngày](#-sử-dụng-hàng-ngày)
- [Auto-Setup & Git Hooks](#-auto-setup--git-hooks)
- [Extension & Dashboard](#-extension--dashboard)
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

## 🚀 Cài đặt trên máy mới

### Yêu cầu tối thiểu
- **Antigravity IDE** (khuyên dùng) hoặc VS Code / Cursor.
- **Git** đã cài đặt.
- **Python 3.9+** (để chạy các script bóc tách/xuất bản tài liệu).
- **Node.js 18+** (tùy chọn, chỉ cần khi build dashboard/extension).

### Cách 1: 1-Click Setup (Khuyên dùng)
Chạy script cài đặt nhanh:
```bash
# macOS / Linux:
./setup.sh

# Windows:
setup.bat
```

Script sẽ tự động:
1. Nhận diện IDE và cài đặt Extension Sidebar mới nhất (`ai-workforce-panel-*.vsix`).
2. Cài đặt các extension hỗ trợ xem PDF / Word / Excel (`cweijan.vscode-office`).
3. Cài đặt đầy đủ Python dependencies vào hệ thống (`python-docx`, `pymupdf`, `pdfplumber`, `lxml`, `markitdown`, `pypandoc`).
4. Kích hoạt Git Hook `post-merge` (để mọi lần sau khi gõ `git pull`, hệ thống tự cập nhật ngầm).
5. Rebuild Web Dashboard (`dashboard/data.json`).

### Cách 2: Tự động chạy khi mở thư mục trong IDE
Thư mục đã được tích hợp sẵn `.vscode/tasks.json` (`runOn: folderOpen`). Khi bạn mở thư mục `ai-workforce` trong IDE, tác vụ cài đặt ngầm sẽ tự động kích hoạt.

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
| 3 | **boc-tach-cv** | Trích xuất toàn bộ thông tin CV ứng viên thành bảng dữ liệu có cấu trúc | *"Bóc tách CV này"*, *"Đọc CV ra bảng"* |
| 4 | **cham-diem-cv** | Đánh giá, chấm điểm và xếp hạng CV ứng viên theo tiêu chuẩn tuyển dụng | *"Chấm điểm CV này"*, *"Đánh giá độ phù hợp CV"* |
| 5 | **pdf-translate** | Dịch nhanh tài liệu PDF song ngữ bảo toàn định dạng gốc | *"Dịch file PDF này"*, *"Translate PDF"* |
| 6 | **invoice** | Bóc tách hóa đơn điện tử XML/PDF và lập Bảng Đề Nghị Thanh Toán Excel | *"Xử lý thư mục hóa đơn này"*, *"Lập đề nghị thanh toán"* |
| 7 | **phan-tich-nhan-su** | Phân tích cơ cấu nhân sự, đánh giá hiệu suất và báo cáo KPI | *"Phân tích dữ liệu nhân sự"*, *"Báo cáo đánh giá KPI"* |
| 8 | **quan-ly-hop-dong** | Soạn thảo và rà soát hợp đồng lao động chuẩn Bộ luật Lao động | *"Soạn hợp đồng lao động"*, *"Rà soát hợp đồng này"* |
| 9 | **tu-van-phap-luat** | Tra cứu điều khoản, đối chiếu quy định và tư vấn giải pháp pháp lý Việt Nam | *"Tư vấn pháp luật về việc này"*, *"Tra cứu luật"* |
| 10 | **viet-jd** | Soạn thảo bản mô tả công việc (Job Description) 5 khối chuẩn quốc tế | *"Viết JD vị trí Kế toán trưởng"*, *"Tạo bản mô tả công việc"* |
| 11 | **viet-chuyen-nghiep** | Viết bài truyền thông, chuyên gia, biên tập nội dung đa văn phong | *"Viết bài chuyên nghiệp về chủ đề X"*, *"Biên tập bài viết"* |
| 12 | **xu-ly-van-phong** | Chuyển đổi và tạo lập văn bản Word, Excel, PowerPoint, PDF chuẩn Nghị định 30 | *"Xử lý văn phòng"*, *"Soạn công văn chuẩn NĐ 30"* |
| 13 | **ai-coder-rules** | Kỷ luật lập trình 3-Gate (Think - Do - Verify), chống ảo giác, kiểm thử thực tế | *"Code tính năng mới"*, *"Fix bug"*, *"Refactor"* |

---

## 🛡️ Bộ Tứ Quy Tắc Vận Hành (Rules)

Hệ thống vận hành theo 4 bộ quy tắc nền tảng đặt tại `.agents/rules/`:

1. **R0 — Zero External API (Tự chủ 100%)**:
   - Mọi tác vụ AI chạy hoàn toàn bằng LLM tích hợp sẵn trong Antigravity IDE.
   - Tuyệt đối KHÔNG yêu cầu API key hoặc gọi REST API trả phí bên ngoài.
   - Python scripts chỉ phục vụ xử lý file I/O, bóc tách và xuất bản.

2. **R1 — Zero-Destruction (`R1-zero-destruction.md`)**:
   - Cấm lệnh xóa vĩnh viễn (`rm -rf`, `del`).
   - Xóa mềm: Di chuyển file cần xóa vào `_Delete/`.
   - Lưu trữ: Di chuyển file cũ hết hiệu lực vào `_Archive/`.

3. **R2 — Code Quality (`R2-code-quality.md`)**:
   - **Zero-Inference Taxonomy**: Phân định rõ OBSERVED, DERIVED, PRIOR, ASSUMED.
   - **Codebase-first**: Luôn đọc file thực tế và kiểm tra blast radius trước khi sửa.
   - **5 Absolute Bans**: Cấm code placeholder, cấm nuốt lỗi, cấm sửa file chưa đọc, cấm bịa API, cấm hardcode secret.

4. **R3 — Operational Discipline (`R3-operational-discipline.md`)**:
   - **Per-Task Verification**: Bắt buộc kiểm chứng kết quả chạy thực tế trước khi báo hoàn thành.
   - **Autonomous Full-Run**: Tự động chạy liên tục từ bước đầu đến bước cuối mà không dừng xin phép giữa chừng.
   - **Regression Prevention**: Sửa dứt điểm nguyên nhân gốc và kiểm tra toàn diện sau khi sửa.

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
│   │   ├── R1-zero-destruction.md    ← Bảo toàn dữ liệu vật lý
│   │   ├── R2-code-quality.md        ← Quy chuẩn chất lượng mã nguồn
│   │   └── R3-operational-discipline.md ← Kỷ luật thực thi
│   │
│   ├── skills/                       ← [S] 13 Nhân sự số chuyên trách
│   │   ├── ejv-translate/            ← Dịch thuật 3 ngôn ngữ VN/EN/JP
│   │   ├── boc-tach-pdf/             ← Số hóa PDF scan sang DOCX
│   │   ├── invoice/                  ← Xử lý hóa đơn XML/PDF sang Excel
│   │   ├── ai-coder-rules/           ← Kỷ luật lập trình 3-Gate
│   │   └── ... (các skills khác)
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
