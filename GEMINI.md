# AI WORKFORCE — Hướng dẫn vận hành cho AI Agent

> File này được nạp TỰ ĐỘNG khi mở thư mục `ai-workforce` làm workspace trong Antigravity IDE (hoặc Cursor/VS Code có AI agent).
> Agent PHẢI đọc file này TRƯỚC KHI thực hiện bất kỳ yêu cầu nào.

---

## ⚠️ NGUYÊN TẮC BẮT BUỘC — ZERO EXTERNAL API

1. **KHÔNG gọi REST API bên ngoài** (Gemini API, OpenAI API, Claude API, v.v.) và **KHÔNG yêu cầu API key** để vận hành bất kỳ skill nào.
2. **Toàn bộ năng lực AI** (dịch thuật, phân tích, tóm tắt, viết bài, đánh giá...) là của **chính Agent** (LLM tích hợp sẵn trong IDE).
3. **Python scripts** trong `.agents/skills/*/scripts/` chỉ phục vụ xử lý dữ liệu (bóc tách, merge, validate, xuất bản file) — **KHÔNG chứa logic AI hoặc lời gọi API**.
4. Khi được kích hoạt, skill **PHẢI tự chạy liên tục** cho đến khi hoàn tất 100% — **KHÔNG tự dừng giữa chừng** để xin phép.
5. **KHÔNG BỊA DỮ LIỆU**. Mọi thông tin chính sách, bảng giá, quy trình phải dựa trên `.agents/knowledge/`.

---

## 📦 SKILL REGISTRY — Bản đồ kỹ năng

Khi user yêu cầu thực hiện một skill, Agent PHẢI:
1. Tìm skill phù hợp trong bảng dưới đây dựa trên **trigger keywords**.
2. **Đọc file SKILL.md** tương ứng để nắm quy trình chi tiết.
3. Thực hiện đầy đủ các bước trong SKILL.md.

| Skill | Trigger Keywords | SKILL.md Path |
|-------|------------------|---------------|
| **ejv-translate** | Dịch tài liệu 3 ngôn ngữ, EJV Translator, dịch VN/EN/JP | `.agents/skills/ejv-translate/SKILL.md` |
| **boc-tach-pdf** | Bóc tách PDF scan, số hóa tài liệu, OCR PDF, scan ra Word | `.agents/skills/boc-tach-pdf/SKILL.md` |
| **boc-tach-cv** | Bóc tách CV, trích xuất CV, đọc CV ra bảng | `.agents/skills/boc-tach-cv/SKILL.md` |
| **cham-diem-cv** | Chấm điểm CV, đánh giá độ phù hợp CV | `.agents/skills/cham-diem-cv/SKILL.md` |
| **pdf-translate** | Dịch PDF, translate PDF, dịch tài liệu song ngữ | `.agents/skills/pdf-translate/SKILL.md` |
| **invoice** | Xử lý hóa đơn, đề nghị thanh toán, invoice | `.agents/skills/invoice/SKILL.md` |
| **phan-tich-nhan-su** | Phân tích nhân sự, báo cáo KPI, đánh giá hiệu suất | `.agents/skills/phan-tich-nhan-su/SKILL.md` |
| **quan-ly-hop-dong** | Soạn hợp đồng, rà soát hợp đồng lao động | `.agents/skills/quan-ly-hop-dong/SKILL.md` |
| **tu-van-phap-luat** | Tư vấn pháp luật, tra cứu luật, xử lý tranh chấp | `.agents/skills/tu-van-phap-luat/SKILL.md` |
| **viet-jd** | Viết JD, tạo mô tả công việc, soạn JD | `.agents/skills/viet-jd/SKILL.md` |
| **viet-chuyen-nghiep** | Viết bài chuyên nghiệp, soạn thảo văn bản | `.agents/skills/viet-chuyen-nghiep/SKILL.md` |
| **xu-ly-van-phong** | Xử lý văn phòng, tạo sửa Word Excel PPT PDF | `.agents/skills/xu-ly-van-phong/SKILL.md` |

---

## 🔧 PATH RESOLUTION — Quy ước đường dẫn

Khi SKILL.md sử dụng các placeholder như `<skill_dir>`, `<process_dir>`, agent PHẢI resolve như sau:

| Placeholder | Giá trị thực |
|-------------|-------------|
| `<workspace>` | Thư mục root của workspace hiện tại (chứa file `GEMINI.md` này) |
| `<skill_dir>` | `<workspace>/.agents/skills/<tên_skill>/` |
| `<process_dir>` | Thư mục tạm để xử lý, tạo tại nơi thuận tiện (ví dụ: `<workspace>/_process/<tên_tài_liệu>/` hoặc artifact directory) |
| `<output_dir>` | Mặc định: `~/Downloads/` hoặc nơi user chỉ định |
| `<file_goc>` | File đầu vào do user cung cấp |

### Ví dụ cụ thể:
Nếu user yêu cầu dịch file `/Users/user/Downloads/contract.pdf` bằng skill `ejv-translate`:
- `<skill_dir>` = `<workspace>/.agents/skills/ejv-translate/`
- `<process_dir>` = tạo thư mục xử lý riêng cho tài liệu
- Script: `python3 <workspace>/.agents/skills/ejv-translate/scripts/extract_text.py --input "/Users/user/Downloads/contract.pdf" --output "<process_dir>/extracted_blocks.json"`

---

## 🐍 PYTHON DEPENDENCIES — Cài đặt tự động

Trước khi chạy bất kỳ Python script nào trong `.agents/skills/*/scripts/`, Agent PHẢI kiểm tra và cài dependencies nếu chưa có:

```bash
# Kiểm tra nhanh:
python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null || pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc
```

Danh sách packages cần thiết (xem `requirements.txt`):
- `python-docx` — Tạo/đọc file DOCX
- `pymupdf` (fitz) — Đọc/render PDF
- `pdfplumber` — Trích xuất bảng biểu từ PDF
- `lxml` — Xử lý XML
- `markitdown` — Chuyển đổi Markdown
- `pypandoc` — Chuyển đổi định dạng tài liệu

---

## 📂 CẤU TRÚC WORKSPACE

```
ai-workforce/                   ← MỞ THƯ MỤC NÀY LÀM WORKSPACE
├── GEMINI.md                    ← File này (nạp tự động)
├── README.md                    ← Hướng dẫn sử dụng
├── requirements.txt             ← Python dependencies
├── setup.sh                     ← 1-Click setup cho máy mới
├── .agents/                     ← Antigravity customizations root
│   ├── rules/
│   │   ├── AGENTS.md            ← Luật tổng (Zero-Hallucination, etc.)
│   │   └── R1-zero-destruction.md
│   ├── skills/                  ← 12 nhân viên số
│   │   ├── ejv-translate/
│   │   │   ├── SKILL.md         ← Mô tả công việc + quy trình
│   │   │   ├── scripts/         ← Python scripts (chỉ xử lý I/O)
│   │   │   ├── templates/       ← Prompt templates
│   │   │   └── references/      ← Schema, translation rules
│   │   ├── boc-tach-pdf/
│   │   ├── invoice/
│   │   └── ...
│   ├── knowledge/               ← Dữ liệu thật (SSOT)
│   └── workflows/               ← Quy trình tự động
├── extension/                   ← VS Code extension (sidebar)
├── dashboard/                   ← Web UI dashboard
└── scripts/                     ← Auto-setup, git hooks
```

---

## 🆘 TROUBLESHOOTING

### "Agent yêu cầu API key"
**Nguyên nhân**: Thư mục `ai-workforce` chưa được mở làm workspace → Agent không nạp được GEMINI.md và AGENTS.md.
**Giải pháp**: Mở thư mục `ai-workforce` làm workspace trong Antigravity IDE: File → Open Folder → chọn thư mục `ai-workforce`.

### "Skill không tìm thấy"
**Nguyên nhân**: Agent chưa đọc GEMINI.md hoặc SKILL.md.
**Giải pháp**: Gõ lại yêu cầu kèm tên skill rõ ràng, ví dụ: "Thực hiện skill ejv-translate với file X".

### "Python script lỗi import"
**Nguyên nhân**: Chưa cài Python dependencies.
**Giải pháp**: Chạy `pip3 install -r requirements.txt` trong thư mục `ai-workforce`.
